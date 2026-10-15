"""
test_reviewer_adversarial.py
Adversarial Stress Test & Integrity Verification Suite for Milestone 1.
Authored by: Milestone 1 Reviewer 1 (teamwork_preview_reviewer_m1_1)
"""

import os
import sys
import tempfile
import threading
import time
import unittest
import json

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import select, inspect, text
from sqlalchemy.exc import IntegrityError
import backend.database as db
import backend.mechanics as mechanics
import backend.character_generator as cg


class TestMilestone1Adversarial(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_adv.db")
        self.db_url = f"sqlite:///{self.db_path}"
        self.engine = db.create_sao_engine(self.db_url)
        db.init_db(engine=self.engine)

    def tearDown(self):
        self.engine.dispose()
        # Clean up directory
        for f in os.listdir(self.temp_dir):
            try:
                os.remove(os.path.join(self.temp_dir, f))
            except OSError:
                pass
        try:
            os.rmdir(self.temp_dir)
        except OSError:
            pass

    def test_01_all_11_models_registered_and_table_names(self):
        """Verify all 11 declarative models map to exact expected table names."""
        expected_tables = {
            "campaign_sessions",
            "characters",
            "equipped_slots",
            "anatomical_grafts",
            "active_debuffs",
            "skill_masteries",
            "archived_skills",
            "party_companions",
            "master_game_states",
            "corpse_caches",
            "chat_messages",
        }
        inspector = inspect(self.engine)
        actual_tables = set(inspector.get_table_names())
        self.assertEqual(expected_tables, actual_tables, f"Missing or extra tables: {expected_tables ^ actual_tables}")

    def test_02_sqlite_wal_pragmas_on_every_connection(self):
        """Verify SQLite WAL PRAGMAs are strictly applied on newly acquired connections."""
        pragmas = db.get_sqlite_pragmas(self.engine)
        self.assertEqual(pragmas.get("journal_mode", "").lower(), "wal")
        self.assertEqual(pragmas.get("synchronous"), 1)
        self.assertEqual(pragmas.get("busy_timeout"), 30000)
        self.assertEqual(pragmas.get("foreign_keys"), 1)

    def test_03_foreign_key_cascades_and_set_null(self):
        """
        Adversarial test: Delete CharacterRecord and CampaignSessionRecord.
        Verify child records cascade delete, and ChatMessage.character_id sets to NULL.
        """
        with db.db_transaction(engine=self.engine) as session:
            camp = db.CampaignSessionRecord(session_id="sess_cascade", session_name="Cascade Test")
            session.add(camp)
            session.flush()

            char = db.CharacterRecord(session_id="sess_cascade", slug="hero_1", name="Hero One")
            session.add(char)
            session.flush()

            slot = db.EquippedSlotRecord(character_id=char.id, slot_key="main_hand", item_name="Iron Sword")
            graft = db.AnatomicalGraftRecord(character_id=char.id, slot_key="lower_left_arm", graft_name="Secondary Ganglia", unit_strain=1)
            debuff = db.ActiveDebuffRecord(character_id=char.id, debuff_id="acid_1", name="Acid Burn", ac_penalty=2)
            skill = db.SkillMasteryRecord(character_id=char.id, skill_name="One-Handed Sword", mastery_level=100)
            arch = db.ArchivedSkillRecord(character_id=char.id, skill_name="Slash", mastery_level=50)
            msg = db.ChatMessageRecord(session_id="sess_cascade", character_id=char.id, role="user", content="Hello world")
            comp = db.PartyCompanionRecord(session_id="sess_cascade", companion_slug="ren", name="Ren", hp=40, max_hp=40)
            mgs = db.MasterGameStateRecord(session_id="sess_cascade", turn_number=5)
            corpse = db.CorpseCacheRecord(session_id="sess_cascade", cache_id="cache_1", fallen_name="Hero Zero", floor_number=1, col_amount=500)

            session.add_all([slot, graft, debuff, skill, arch, msg, comp, mgs, corpse])

        # Verify insertion
        with db.db_transaction(engine=self.engine) as session:
            c = session.execute(select(db.CharacterRecord).where(db.CharacterRecord.slug == "hero_1")).scalar_one()
            self.assertEqual(len(c.equipped_slots), 1)
            self.assertEqual(len(c.anatomical_grafts), 1)
            self.assertEqual(len(c.active_debuffs), 1)
            self.assertEqual(len(c.skill_masteries), 1)
            self.assertEqual(len(c.archived_skills), 1)

            # Now delete the Character
            session.delete(c)

        # Verify child records were cascade-deleted
        with db.db_transaction(engine=self.engine) as session:
            slots = session.execute(select(db.EquippedSlotRecord)).scalars().all()
            self.assertEqual(len(slots), 0, "Equipped slots must be deleted when character is deleted")
            grafts = session.execute(select(db.AnatomicalGraftRecord)).scalars().all()
            self.assertEqual(len(grafts), 0, "Grafts must be deleted when character is deleted")
            debuffs = session.execute(select(db.ActiveDebuffRecord)).scalars().all()
            self.assertEqual(len(debuffs), 0, "Debuffs must be deleted when character is deleted")
            skills = session.execute(select(db.SkillMasteryRecord)).scalars().all()
            self.assertEqual(len(skills), 0, "Skills must be deleted when character is deleted")
            archived = session.execute(select(db.ArchivedSkillRecord)).scalars().all()
            self.assertEqual(len(archived), 0, "Archived skills must be deleted when character is deleted")

            # ChatMessage should NOT be deleted, but character_id should be SET NULL
            msgs = session.execute(select(db.ChatMessageRecord)).scalars().all()
            self.assertEqual(len(msgs), 1, "ChatMessageRecord should survive character deletion")
            self.assertIsNone(msgs[0].character_id, "ChatMessageRecord.character_id must be set to NULL")

            # Now delete CampaignSessionRecord
            camp = session.execute(select(db.CampaignSessionRecord).where(db.CampaignSessionRecord.session_id == "sess_cascade")).scalar_one()
            session.delete(camp)

        # Verify CampaignSession cascade deletes everything remaining
        with db.db_transaction(engine=self.engine) as session:
            self.assertEqual(len(session.execute(select(db.PartyCompanionRecord)).scalars().all()), 0)
            self.assertEqual(len(session.execute(select(db.MasterGameStateRecord)).scalars().all()), 0)
            self.assertEqual(len(session.execute(select(db.CorpseCacheRecord)).scalars().all()), 0)
            self.assertEqual(len(session.execute(select(db.ChatMessageRecord)).scalars().all()), 0)

    def test_04_unique_constraints_enforcement(self):
        """Adversarial test: Enforce unique constraints on characters, equipped slots, companions, master state."""
        with db.db_transaction(engine=self.engine) as session:
            session.add(db.CampaignSessionRecord(session_id="s1"))
            session.add(db.CampaignSessionRecord(session_id="s2"))
            # Same slug in different sessions should SUCCEED
            c1 = db.CharacterRecord(session_id="s1", slug="glenny", name="Glenny S1")
            c2 = db.CharacterRecord(session_id="s2", slug="glenny", name="Glenny S2")
            session.add_all([c1, c2])

        # Same slug in SAME session should FAIL
        with self.assertRaises(IntegrityError):
            with db.db_transaction(engine=self.engine) as session:
                dup = db.CharacterRecord(session_id="s1", slug="glenny", name="Glenny Duplicate")
                session.add(dup)

        # Same slot_key on same character should FAIL
        with db.db_transaction(engine=self.engine) as session:
            c = session.execute(select(db.CharacterRecord).where(db.CharacterRecord.session_id == "s1")).scalars().first()
            s1 = db.EquippedSlotRecord(character_id=c.id, slot_key="main_hand", item_name="Sword A")
            session.add(s1)

        with self.assertRaises(IntegrityError):
            with db.db_transaction(engine=self.engine) as session:
                c = session.execute(select(db.CharacterRecord).where(db.CharacterRecord.session_id == "s1")).scalars().first()
                s2 = db.EquippedSlotRecord(character_id=c.id, slot_key="main_hand", item_name="Sword B")
                session.add(s2)

    def test_05_db_transaction_atomicity_and_post_commit_hooks(self):
        """Test transaction rollback discards hooks and changes, while commit triggers hooks."""
        hook_ran = []

        def sample_hook():
            hook_ran.append(True)

        # 1. Rollback case
        with self.assertRaises(ValueError):
            with db.db_transaction(engine=self.engine) as session:
                session.add(db.CampaignSessionRecord(session_id="fail_session"))
                db.register_post_commit_hook(session, sample_hook)
                raise ValueError("Intentional crash")

        self.assertEqual(len(hook_ran), 0, "Post-commit hook must NOT run on rollback")

        with db.db_transaction(engine=self.engine) as session:
            sess = session.execute(select(db.CampaignSessionRecord).where(db.CampaignSessionRecord.session_id == "fail_session")).scalars().first()
            self.assertIsNone(sess, "Failed session must have been rolled back")

        # 2. Success case
        with db.db_transaction(engine=self.engine) as session:
            session.add(db.CampaignSessionRecord(session_id="success_session"))
            db.register_post_commit_hook(session, sample_hook)

        self.assertEqual(len(hook_ran), 1, "Post-commit hook must run exactly once on commit")

    def test_06_nested_transaction_savepoint_rollback(self):
        """Test savepoint semantics with session.begin_nested()."""
        with db.db_transaction(engine=self.engine) as outer_session:
            outer_session.add(db.CampaignSessionRecord(session_id="outer_ok"))

            # Inner nested transaction fails
            try:
                with db.db_transaction(session=outer_session) as inner_session:
                    inner_session.add(db.CampaignSessionRecord(session_id="inner_fail"))
                    raise RuntimeError("Inner failure")
            except RuntimeError:
                pass

            outer_session.add(db.CampaignSessionRecord(session_id="outer_ok_2"))

        with db.db_transaction(engine=self.engine) as session:
            ok1 = session.execute(select(db.CampaignSessionRecord).where(db.CampaignSessionRecord.session_id == "outer_ok")).scalars().first()
            ok2 = session.execute(select(db.CampaignSessionRecord).where(db.CampaignSessionRecord.session_id == "outer_ok_2")).scalars().first()
            failed = session.execute(select(db.CampaignSessionRecord).where(db.CampaignSessionRecord.session_id == "inner_fail")).scalars().first()

            self.assertIsNotNone(ok1)
            self.assertIsNotNone(ok2)
            self.assertIsNone(failed, "Inner savepoint failure must not persist inner entity")

    def test_07_glenny_4_arm_strain_and_ac_hydration(self):
        """Verify Glenny's 4-armed profile, strain math, and AC parity via to_player_dict()."""
        glenny_raw = cg.generate_starting_character("Glenny")
        self.assertIn("main_hand", glenny_raw["equipped"])
        self.assertIn("off_hand", glenny_raw["equipped"])
        self.assertIn("lower_main_hand", glenny_raw["equipped"])
        self.assertIn("lower_off_hand", glenny_raw["equipped"])

        with db.db_transaction(engine=self.engine) as session:
            session.add(db.CampaignSessionRecord(session_id="glenny_sess"))
            c = db.CharacterRecord(
                session_id="glenny_sess",
                slug="glenny",
                name="Glenny",
                level=1,
                hp=100,
                max_hp=100,
                col=100,
                xp=0,
                gender="Male",
                race="Construct / Aberrant",
                character_class="Pathless (Freeform Anomaly)",
                raw_data_json=json.dumps(glenny_raw),
                stats_json=json.dumps(glenny_raw["stats"]),
            )
            session.add(c)
            session.flush()

            for slot_k, item_v in glenny_raw["equipped"].items():
                session.add(db.EquippedSlotRecord(character_id=c.id, slot_key=slot_k, item_name=item_v))

            # Install Secondary Ganglia in lower_left_arm with unit_strain=1
            session.add(db.AnatomicalGraftRecord(
                character_id=c.id,
                slot_key="lower_left_arm",
                graft_name="Secondary Ganglia",
                unit_strain=1,
                bio_strain=0,
                graft_data_json=json.dumps({"key": "secondary_ganglia", "name": "Secondary Ganglia", "strain": 1}),
            ))

        with db.db_transaction(engine=self.engine) as session:
            c = session.execute(select(db.CharacterRecord).where(db.CharacterRecord.slug == "glenny")).scalar_one()
            hydrated = c.to_player_dict()

            # Verify equipped slots
            self.assertEqual(hydrated["equipped"]["lower_main_hand"], glenny_raw["equipped"]["lower_main_hand"])
            self.assertEqual(hydrated["equipped"]["lower_off_hand"], glenny_raw["equipped"]["lower_off_hand"])

            # Verify strain
            self.assertEqual(mechanics.get_max_unit_strain(hydrated), 4)
            self.assertEqual(mechanics.get_current_unit_strain(hydrated), 1)

            # Verify base AC = 14
            self.assertEqual(mechanics.calculate_ac(hydrated), 14)

            # Equip Wooden Buckler in lower_off_hand -> AC = 16
            hydrated["equipped"]["lower_off_hand"] = "Wooden Buckler"
            self.assertEqual(mechanics.calculate_ac(hydrated), 16)

    def test_08_active_debuff_ac_dr_shred_recalculation(self):
        """Verify active debuff records apply AC penalty and DR override in combat stats."""
        with db.db_transaction(engine=self.engine) as session:
            session.add(db.CampaignSessionRecord(session_id="debuff_sess"))
            c = db.CharacterRecord(
                session_id="debuff_sess",
                slug="test_warrior",
                name="Test Warrior",
                raw_data_json=json.dumps({"ac": 15, "base_ac": 15, "dr": 5, "base_dr": 5}),
            )
            session.add(c)
            session.flush()

            # Add debuff: -3 AC, DR override to 0
            session.add(db.ActiveDebuffRecord(
                character_id=c.id,
                debuff_id="acid_shred",
                name="Acid Corrosion",
                ac_penalty=-3,
                dr_override=0,
                turns_remaining=2,
            ))

        with db.db_transaction(engine=self.engine) as session:
            c = session.execute(select(db.CharacterRecord).where(db.CharacterRecord.slug == "test_warrior")).scalar_one()
            hydrated = c.to_player_dict()

            self.assertEqual(len(hydrated.get("active_debuffs", [])), 1)
            debuff = hydrated["active_debuffs"][0]
            self.assertEqual(debuff["ac_penalty"], -3)
            self.assertEqual(debuff["dr_override"], 0)

            stats = mechanics.recalculate_entity_combat_stats(hydrated)
            self.assertEqual(stats["ac"], 12)  # 15 + (-3)
            self.assertEqual(stats["dr"], 0)   # 5 overridden to 0

    def test_09_multi_threaded_concurrency_stress(self):
        """Stress-test SQLite WAL mode under 10 concurrent reader/writer threads."""
        num_threads = 10
        errors = []

        def worker(thread_idx: int):
            try:
                sess_id = f"thread_sess_{thread_idx}"
                with db.db_transaction(engine=self.engine, session_id=sess_id) as session:
                    camp = db.CampaignSessionRecord(session_id=sess_id, session_name=f"Thread {thread_idx}")
                    session.add(camp)
                    session.flush()

                    for i in range(5):
                        char = db.CharacterRecord(
                            session_id=sess_id,
                            slug=f"char_{thread_idx}_{i}",
                            name=f"Character {thread_idx}-{i}",
                            hp=100 + i,
                        )
                        session.add(char)

                # Read back
                with db.db_transaction(engine=self.engine, session_id=sess_id) as session:
                    chars = session.execute(
                        select(db.CharacterRecord).where(db.CharacterRecord.session_id == sess_id)
                    ).scalars().all()
                    assert len(chars) == 5, f"Expected 5 characters, got {len(chars)}"
            except Exception as exc:
                errors.append((thread_idx, str(exc)))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrency errors occurred: {errors}")

    def test_10_atomic_write_zero_byte_protection(self):
        """Verify atomic_write_json never truncates or corrupts existing file when input is un-serializable."""
        target_file = os.path.join(self.temp_dir, "safe_target.json")
        initial_data = {"status": "intact", "important_col": 9999}
        db.atomic_write_json(target_file, initial_data)

        # Confirm initial write
        self.assertEqual(db.atomic_read_json(target_file), initial_data)

        # Attempt to write an un-serializable object (circular reference)
        bad_data = {}
        bad_data["self"] = bad_data

        with self.assertRaises(ValueError):
            db.atomic_write_json(target_file, bad_data)

        # Confirm target file is 100% UNTOUCHED and NOT zero-byte truncated
        read_after = db.atomic_read_json(target_file)
        self.assertEqual(read_after, initial_data, "Original file corrupted or truncated during failed serialization!")
        self.assertGreater(os.path.getsize(target_file), 0, "Target file truncated to zero bytes!")


if __name__ == "__main__":
    unittest.main()
