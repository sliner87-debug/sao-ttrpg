"""
test_reviewer_m3_party_adversarial.py
=====================================
Milestone 3 Reviewer 1 Adversarial Stress Test & Verification Suite for:
- PartyRepository (save_party, load_party, seed_default_party_from_disk)
- PartyCompanionRecord (dual-coverage, to_companion_dict, synonyms)
- Multi-session isolation, rollback resilience, and disk mirroring safety
"""

import json
import os
import shutil
import sys
import tempfile
import threading
import unittest

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import select, inspect
import backend.database as db
from backend.database.models import Base, CampaignSessionRecord, PartyCompanionRecord
from backend.database.repositories import PartyRepository
from backend.database.adapters import mirror_party_to_disk, atomic_read_json


class TestMilestone3PartyAdversarial(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_party_adv.db")
        self.db_url = f"sqlite:///{self.db_path}"
        self.engine = db.create_sao_engine(self.db_url)
        db.init_db(engine=self.engine)

    def tearDown(self):
        self.engine.dispose()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_save_party_supports_list_and_dict_inputs(self):
        """Verify save_party handles both list of companion dicts and dict of companion dicts."""
        # 1. List input
        list_comps = [
            {
                "slug": "alice",
                "name": "Alice Wonderland",
                "level": 3,
                "hp": 45,
                "max_hp": 45,
                "ac": 16,
                "recruited": True,
                "active": True,
                "equipped": {"main_hand": "Rapier", "head": "Silver Ribbon"},
                "stats": {"STR": 12, "DEX": 18, "CON": 14},
                "skills": {"Fencing": 120},
            },
            {
                "id": "companion_bob",
                "name": "Bob the Builder",
                "level": 5,
                "hp": 70,
                "max_hp": 70,
                "ac": 18,
                "recruited": True,
                "active": False,
                "equipped": {"main_hand": "Warhammer", "chest": "Plate Armor"},
                "stats": {"STR": 18, "DEX": 10, "CON": 18},
                "skills": {"Hammer Mastery": 200},
            },
        ]

        with db.db_transaction(engine=self.engine, session_id="sess_list") as session:
            PartyRepository.save_party(session, list_comps, session_id="sess_list", mirror_disk=False)

        with db.db_transaction(engine=self.engine, session_id="sess_list") as session:
            loaded = PartyRepository.load_party(session, session_id="sess_list")
            self.assertEqual(len(loaded), 2)
            alice = next(c for c in loaded if c["slug"] == "alice")
            self.assertEqual(alice["name"], "Alice Wonderland")
            self.assertEqual(alice["level"], 3)
            self.assertEqual(alice["equipped"]["main_hand"], "Rapier")
            self.assertEqual(alice["stats"]["DEX"], 18)
            self.assertEqual(alice["skills"]["Fencing"], 120)
            self.assertTrue(alice["active"])
            self.assertTrue(alice["is_active"])

        # 2. Dict-of-dicts input
        dict_comps = {
            "c_alice": {
                "slug": "alice",
                "name": "Alice Wonderland Updated",
                "level": 4,
                "hp": 55,
                "max_hp": 55,
                "ac": 17,
                "recruited": True,
                "active": True,
                "equipped": {"main_hand": "Vorpal Blade"},
            },
            "c_charlie": {
                "slug": "charlie",
                "name": "Charlie Chaplin",
                "level": 2,
                "hp": 30,
                "max_hp": 30,
                "ac": 13,
                "recruited": True,
                "active": True,
            },
        }

        with db.db_transaction(engine=self.engine, session_id="sess_list") as session:
            PartyRepository.save_party(session, dict_comps, session_id="sess_list", mirror_disk=False)

        with db.db_transaction(engine=self.engine, session_id="sess_list") as session:
            loaded = PartyRepository.load_party(session, session_id="sess_list")
            self.assertEqual(len(loaded), 2)
            slugs = {c["slug"] for c in loaded}
            self.assertEqual(slugs, {"alice", "charlie"}, "Bob should have been pruned, Charlie added")
            alice = next(c for c in loaded if c["slug"] == "alice")
            self.assertEqual(alice["name"], "Alice Wonderland Updated")
            self.assertEqual(alice["level"], 4)
            self.assertEqual(alice["equipped"]["main_hand"], "Vorpal Blade")

    def test_02_in_place_diffing_preserves_primary_keys(self):
        """Verify that updating an existing companion modifies columns in-place and preserves row ID."""
        initial = [{"slug": "diana", "name": "Diana", "hp": 40}]

        with db.db_transaction(engine=self.engine, session_id="sess_diff") as session:
            PartyRepository.save_party(session, initial, session_id="sess_diff", mirror_disk=False)

        with db.db_transaction(engine=self.engine, session_id="sess_diff") as session:
            rec = session.execute(
                select(PartyCompanionRecord).where(
                    PartyCompanionRecord.session_id == "sess_diff",
                    PartyCompanionRecord.companion_slug == "diana",
                )
            ).scalar_one()
            orig_id = rec.id

        # Update diana
        updated = [{"slug": "diana", "name": "Diana Princess", "hp": 50, "level": 2}]
        with db.db_transaction(engine=self.engine, session_id="sess_diff") as session:
            PartyRepository.save_party(session, updated, session_id="sess_diff", mirror_disk=False)

        with db.db_transaction(engine=self.engine, session_id="sess_diff") as session:
            rec_after = session.execute(
                select(PartyCompanionRecord).where(
                    PartyCompanionRecord.session_id == "sess_diff",
                    PartyCompanionRecord.companion_slug == "diana",
                )
            ).scalar_one()
            self.assertEqual(rec_after.id, orig_id, "In-place diffing MUST preserve the entity primary key")
            self.assertEqual(rec_after.name, "Diana Princess")
            self.assertEqual(rec_after.hp, 50)
            self.assertEqual(rec_after.level, 2)

    def test_03_multi_session_isolation(self):
        """Verify companion states are strictly isolated across multiple sessions."""
        with db.db_transaction(engine=self.engine, session_id="session_A") as session:
            PartyRepository.save_party(
                session,
                [{"slug": "ren", "name": "Ren S1", "hp": 35, "level": 3}],
                session_id="session_A",
                mirror_disk=False,
            )

        with db.db_transaction(engine=self.engine, session_id="session_B") as session:
            PartyRepository.save_party(
                session,
                [{"slug": "ren", "name": "Ren S2", "hp": 80, "level": 8}],
                session_id="session_B",
                mirror_disk=False,
            )

        with db.db_transaction(engine=self.engine) as session:
            p_a = PartyRepository.load_party(session, session_id="session_A")
            p_b = PartyRepository.load_party(session, session_id="session_B")

            self.assertEqual(len(p_a), 1)
            self.assertEqual(len(p_b), 1)
            self.assertEqual(p_a[0]["name"], "Ren S1")
            self.assertEqual(p_a[0]["hp"], 35)
            self.assertEqual(p_a[0]["level"], 3)

            self.assertEqual(p_b[0]["name"], "Ren S2")
            self.assertEqual(p_b[0]["hp"], 80)
            self.assertEqual(p_b[0]["level"], 8)

    def test_04_transaction_rollback_and_savepoint_safety(self):
        """Verify transaction rollback completely rolls back companion modifications."""
        with db.db_transaction(engine=self.engine, session_id="sess_rb") as session:
            PartyRepository.save_party(
                session,
                [{"slug": "eve", "name": "Eve", "hp": 25}],
                session_id="sess_rb",
                mirror_disk=False,
            )

        # Attempt to modify Eve and add Frank, but fail the transaction
        with self.assertRaises(RuntimeError):
            with db.db_transaction(engine=self.engine, session_id="sess_rb") as session:
                PartyRepository.save_party(
                    session,
                    [
                        {"slug": "eve", "name": "Eve Corrupted", "hp": 999},
                        {"slug": "frank", "name": "Frank", "hp": 100},
                    ],
                    session_id="sess_rb",
                    mirror_disk=False,
                )
                raise RuntimeError("Crash before commit")

        # Verify state is intact
        with db.db_transaction(engine=self.engine, session_id="sess_rb") as session:
            loaded = PartyRepository.load_party(session, session_id="sess_rb")
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["name"], "Eve")
            self.assertEqual(loaded[0]["hp"], 25)

    def test_05_disk_mirroring_root_restriction(self):
        """Verify disk mirroring to root Party/ and Entities/ ONLY triggers for default session."""
        mock_root = os.path.join(self.temp_dir, "mock_workspace")
        os.makedirs(os.path.join(mock_root, "Party"), exist_ok=True)
        os.makedirs(os.path.join(mock_root, "Entities"), exist_ok=True)

        ren_data = [{"slug": "companion_ren", "name": "Ren", "hp": 35}]

        # 1. Custom session: root files must NOT be touched
        with db.db_transaction(engine=self.engine, session_id="custom_user_1") as session:
            PartyRepository.save_party(
                session,
                ren_data,
                session_id="custom_user_1",
                mirror_disk=True,
                character_slug="user_one",
                base_dir=mock_root,
            )

        root_ren_party = os.path.join(mock_root, "Party", "companion_ren.json")
        root_ren_ent = os.path.join(mock_root, "Entities", "companion_ren.json")
        char_ren_party = os.path.join(mock_root, "saves", "user_one", "Party", "companion_ren.json")
        char_ren_ent = os.path.join(mock_root, "saves", "user_one", "Entities", "companion_ren.json")

        self.assertFalse(os.path.exists(root_ren_party), "Custom session MUST NOT write to root Party/!")
        self.assertFalse(os.path.exists(root_ren_ent), "Custom session MUST NOT write to root Entities/!")
        self.assertTrue(os.path.exists(char_ren_party), "Custom session MUST write to saves/<slug>/Party/")
        self.assertTrue(os.path.exists(char_ren_ent), "Custom session MUST write to saves/<slug>/Entities/")

        # 2. Default session: root files MUST be mirrored
        with db.db_transaction(engine=self.engine, session_id="default") as session:
            PartyRepository.save_party(
                session,
                ren_data,
                session_id="default",
                mirror_disk=True,
                character_slug="default_hero",
                base_dir=mock_root,
            )

        self.assertTrue(os.path.exists(root_ren_party), "Default session MUST mirror to root Party/!")
        self.assertTrue(os.path.exists(root_ren_ent), "Default session MUST mirror to root Entities/!")

    def test_06_load_party_seeding_restrictions(self):
        """Verify automatic disk seeding applies ONLY to default session when empty, never to custom sessions."""
        mock_root = os.path.join(self.temp_dir, "mock_seed_root")
        p_dir = os.path.join(mock_root, "Party")
        os.makedirs(p_dir, exist_ok=True)
        with open(os.path.join(p_dir, "companion_canonical.json"), "w") as f:
            json.dump({"slug": "canonical", "name": "Canonical Companion", "hp": 40}, f)

        # Monkey-patch get_base_dir in adapters temporarily
        import backend.database.adapters as adapters
        orig_get_base_dir = adapters.get_base_dir
        adapters.get_base_dir = lambda: mock_root

        try:
            with db.db_transaction(engine=self.engine, session_id="custom_empty") as session:
                # Custom empty session should return [] and NOT seed from disk
                custom_loaded = PartyRepository.load_party(session, session_id="custom_empty", seed_from_disk_if_empty=True)
                self.assertEqual(custom_loaded, [], "Custom empty session MUST NOT seed from disk!")

            with db.db_transaction(engine=self.engine, session_id="default") as session:
                # Default empty session SHOULD seed from disk
                default_loaded = PartyRepository.load_party(session, session_id="default", seed_from_disk_if_empty=True)
                self.assertEqual(len(default_loaded), 1)
                self.assertEqual(default_loaded[0]["name"], "Canonical Companion")
        finally:
            adapters.get_base_dir = orig_get_base_dir

    def test_07_resilience_to_malformed_and_edge_case_inputs(self):
        """Verify save_party handles incomplete dicts, missing fields, and non-dict items without crashes."""
        messy_input = [
            None,
            "not_a_dict",
            12345,
            {},  # Empty dict -> gets default slug "companion"
            {"name": "Nameless Wanderer"},  # Missing slug/id -> generates slug from name
            {"id": "companion_weird_hero", "name": "Weird Name", "hp": "45"},  # String numeric HP
        ]

        with db.db_transaction(engine=self.engine, session_id="sess_edge") as session:
            recs = PartyRepository.save_party(session, messy_input, session_id="sess_edge", mirror_disk=False)
            self.assertEqual(len(recs), 3, "Only the 3 dictionary items should be processed")

        with db.db_transaction(engine=self.engine, session_id="sess_edge") as session:
            loaded = PartyRepository.load_party(session, session_id="sess_edge")
            self.assertEqual(len(loaded), 3)

        # Uncoercible non-integer field must reject with ValueError
        bad_input = [{"name": "Bad Hero", "hp": "not_an_int"}]
        with self.assertRaises(ValueError):
            with db.db_transaction(engine=self.engine, session_id="sess_bad") as session:
                PartyRepository.save_party(session, bad_input, session_id="sess_bad", mirror_disk=False)

    def test_08_concurrent_party_writes_different_sessions(self):
        """Verify concurrent threads saving parties to distinct sessions experience zero lock errors or bleed."""
        num_threads = 8
        errors = []

        def worker(idx: int):
            try:
                s_id = f"concurrent_sess_{idx}"
                comps = [
                    {
                        "slug": f"companion_{idx}_1",
                        "name": f"Comp {idx}-1",
                        "hp": 50 + idx,
                        "level": idx + 1,
                    },
                    {
                        "slug": f"companion_{idx}_2",
                        "name": f"Comp {idx}-2",
                        "hp": 60 + idx,
                        "level": idx + 2,
                    },
                ]
                with db.db_transaction(engine=self.engine, session_id=s_id) as session:
                    PartyRepository.save_party(session, comps, session_id=s_id, mirror_disk=False)

                with db.db_transaction(engine=self.engine, session_id=s_id) as session:
                    res = PartyRepository.load_party(session, session_id=s_id)
                    assert len(res) == 2, f"Thread {idx} got {len(res)} companions instead of 2"
                    # PartyRepository._normalize_slug strips 'companion_' prefix by design
                    assert all(c["slug"].startswith(f"{idx}_") for c in res), f"Thread {idx} slugs unexpected: {[c['slug'] for c in res]}"
            except Exception as e:
                errors.append((idx, str(e)))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent multi-session party errors: {errors}")


if __name__ == "__main__":
    unittest.main()
