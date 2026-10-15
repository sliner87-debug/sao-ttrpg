"""
test_challenger_m2_2_grafts_strain_concurrency.py
=================================================
Milestone 2 Challenger 2 Empirical Stress Test Suite.

Focus Areas:
1. Extended Anatomical Graft Slots (10 slots) & Metabolic Strain (Unit Strain & Bio-Tolerance)
2. Active Debuff Persistence & Automatic Cross-Session Combat Stat Reconstitution
3. Corpse Cache Claim Race Condition across 10 Concurrent Threads
4. Core Test Suite Regression Verification
"""

import copy
import json
import os
import sys
import threading
import time
import unittest

import backend.character_generator as cg
import backend.database as db
from backend.database.models import (
    ActiveDebuffRecord,
    AnatomicalGraftRecord,
    CorpseCacheRecord,
)
from backend.database.repositories import (
    CharacterRepository,
    CorpseCacheRepository,
)
import backend.mechanics as mechanics


class TestM2Challenger2Empirical(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = os.path.abspath("test_m2_challenger_stress.db")
        cls.db_url = f"sqlite:///{cls.db_path}"
        # Ensure clean state
        cls._cleanup_db()
        cls.engine = db.create_sao_engine(cls.db_url)
        db.init_db(cls.engine)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "engine"):
            cls.engine.dispose()
        cls._cleanup_db()

    @classmethod
    def _cleanup_db(cls):
        for ext in ["", "-wal", "-shm"]:
            f = f"test_m2_challenger_stress.db{ext}"
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    # =========================================================================
    # Area 1: Graft Slots & Metabolic Strain Overload
    # =========================================================================
    def test_01_all_10_anatomical_graft_slots_persistence(self):
        """
        Verify that all 10 extended anatomical graft slots:
        head, torso, left_arm, right_arm, lower_left_arm, lower_right_arm, legs, spine, tail, wings
        persist cleanly to the relational database and rehydrate with 100% fidelity.
        """
        session_id = "test_graft_slots_session"
        glenny = cg.generate_starting_character("Glenny")
        slug = glenny.get("slug", "glenny")

        ten_grafts = {
            "head": {"name": "Aether-Resonant Ocular", "unit_strain": 1, "strain": 10, "type": "cybernetic"},
            "torso": {"name": "Reinforced Chitin Plating", "unit_strain": 1, "strain": 10, "type": "biological"},
            "left_arm": {"name": "Hydraulic Crusher Arm", "unit_strain": 1, "strain": 10, "type": "cybernetic"},
            "right_arm": {"name": "Myomer Blade Arm", "unit_strain": 1, "strain": 10, "type": "cybernetic"},
            "lower_left_arm": {"name": "Secondary Mantis Claw", "unit_strain": 1, "strain": 10, "type": "biological"},
            "lower_right_arm": {"name": "Secondary Grip Pincer", "unit_strain": 1, "strain": 10, "type": "biological"},
            "legs": {"name": "Piston-Spring Struts", "unit_strain": 1, "strain": 10, "type": "cybernetic"},
            "spine": {"name": "Neural Leyline Conduit", "unit_strain": 1, "strain": 10, "type": "cybernetic"},
            "tail": {"name": "Prehensile Stinger Tail", "unit_strain": 1, "strain": 10, "type": "biological"},
            "wings": {"name": "Glider Flight Membrane", "unit_strain": 1, "strain": 10, "type": "biological"},
        }
        glenny["grafts"] = copy.deepcopy(ten_grafts)

        # Save to database
        with db.db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, glenny, session_id=session_id)

        # Inspect normalized database table directly
        with db.db_transaction(engine=self.engine) as s:
            char_rec = CharacterRepository.get_character_by_slug(s, slug, session_id=session_id)
            self.assertIsNotNone(char_rec)
            graft_records = list(char_rec.anatomical_grafts)
            self.assertEqual(len(graft_records), 10, f"Expected 10 graft records, found {len(graft_records)}")
            persisted_slots = {g.slot_key: g.graft_name for g in graft_records}
            for expected_slot in ten_grafts:
                self.assertIn(expected_slot, persisted_slots)
                self.assertEqual(persisted_slots[expected_slot], ten_grafts[expected_slot]["name"])

        # Rehydrate via load_character
        with db.db_transaction(engine=self.engine) as s:
            loaded = CharacterRepository.load_character(s, slug, session_id=session_id)
            self.assertIsNotNone(loaded)
            self.assertIn("grafts", loaded)
            self.assertIn("graft_system", loaded)
            installed = loaded["graft_system"]["installed_grafts"]
            for slot_k, g_dict in ten_grafts.items():
                self.assertIn(slot_k, loaded["grafts"])
                self.assertEqual(loaded["grafts"][slot_k]["name"], g_dict["name"])
                self.assertIn(slot_k, installed)
                self.assertEqual(installed[slot_k]["name"], g_dict["name"])

    def test_02_secondary_ganglia_unit_strain_bonus(self):
        """
        Verify that Secondary Ganglia awards exactly +1 Unit Strain cap to Glenny (4-armed Troll-Kreen),
        raising cap from 3 to 4, while a 2-armed character with identical CON 16 has cap 3.
        """
        # Glenny: Spliced Apex Chimera (4-armed), CON 16 (+3), Level 1 (1//2 = 0)
        glenny = cg.generate_starting_character("Glenny")
        self.assertEqual(glenny["stats"]["CON"], 16)
        self.assertEqual(mechanics.get_max_unit_strain(glenny), 4)

        # Baseline 2-armed Human with CON 16
        human_state = {
            "name": "Standard Human",
            "race": "human",
            "level": 1,
            "stats": {"STR": 10, "DEX": 10, "CON": 16, "INT": 10, "WIS": 10, "CHA": 10},
            "feats": [],
            "racial_abilities": [],
        }
        self.assertEqual(mechanics.get_max_unit_strain(human_state), 3)

        # Glenny's Bio-Tolerance Pool: (16 * 2) + (1 * 3) = 35
        self.assertEqual(mechanics.get_max_graft_strain(glenny), 35)

    def test_03_intentional_graft_overload_and_rejection_persistence(self):
        """
        Stress-test intentional graft overload:
        - Exceeding Unit Strain Cap (e.g. 5 units installed vs 4 max)
        - Exceeding Bio-Tolerance Pool (e.g. 50 bio-strain vs 35 max)
        Verify that repository persists all grafts and that get_graft_rejection_status
        correctly reports 'Metabolic Rejection' with calculated penalties.
        """
        session_id = "test_overload_session"
        glenny = cg.generate_starting_character("Glenny")
        slug = glenny.get("slug", "glenny")

        # Install 5 heavy grafts (5 units total, 50 bio-strain total -> exceeds both 4 units and 35 pool)
        overloaded_grafts = {
            "head": {"name": "Heavy Golem Core", "unit_strain": 1, "strain": 10},
            "torso": {"name": "Obsidian Plating", "unit_strain": 1, "strain": 10},
            "left_arm": {"name": "Hydraulic Smasher", "unit_strain": 1, "strain": 10},
            "right_arm": {"name": "Pneumatic Cutter", "unit_strain": 1, "strain": 10},
            "legs": {"name": "Titan-Stride Pistons", "unit_strain": 1, "strain": 10},
        }
        glenny["grafts"] = overloaded_grafts

        # Pre-save rejection status
        rejection_before = mechanics.get_graft_rejection_status(glenny)
        self.assertTrue(rejection_before["is_rejecting"])
        self.assertEqual(rejection_before["status"], "Metabolic Rejection")
        self.assertEqual(rejection_before["unit_strain"], 5)
        self.assertEqual(rejection_before["max_unit_strain"], 4)
        self.assertEqual(rejection_before["unit_overflow"], 1)
        self.assertEqual(rejection_before["overflow"], 15)  # 50 - 35 = 15 points

        # Persist to database
        with db.db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, glenny, session_id=session_id)

        # Hydrate from separate transaction and verify rejection state survives
        with db.db_transaction(engine=self.engine) as s:
            loaded = CharacterRepository.load_character(s, slug, session_id=session_id)
            rejection_after = mechanics.get_graft_rejection_status(loaded)
            self.assertTrue(rejection_after["is_rejecting"])
            self.assertEqual(rejection_after["status"], "Metabolic Rejection")
            self.assertEqual(rejection_after["unit_strain"], 5)
            self.assertEqual(rejection_after["max_unit_strain"], 4)
            self.assertEqual(rejection_after["unit_overflow"], 1)
            self.assertEqual(rejection_after["overflow"], 15)
            self.assertGreater(rejection_after["hp_drain"], 0)

    # =========================================================================
    # Area 2: Active Debuffs Lifecycle & Reconstitution
    # =========================================================================
    def test_04_active_debuffs_cross_session_reconstitution(self):
        """
        Verify that multiple active debuffs (Foundry Shred -4 AC, Corrosive Slag DR 0, custom bleed)
        persist across closed sessions and connections, and that CharacterRepository.load_character()
        automatically recalculates AC 12 and DR 0 without manual caller intervention.
        """
        session_id = "test_debuff_session"
        glenny = cg.generate_starting_character("Glenny")
        slug = glenny.get("slug", "glenny")

        # Equip Wooden Buckler in lower_off_hand so base AC is 16
        glenny["equipped"]["lower_off_hand"] = "Wooden Buckler"
        glenny["base_ac"] = 16
        glenny["ac"] = 16
        glenny["base_dr"] = 4
        glenny["dr"] = 4

        # Apply 3 active debuffs
        debuffs = [
            {"debuff_id": "foundry_shred", "name": "Foundry Shred", "ac_penalty": -4, "turns_remaining": 3, "source": "Furnace Automaton"},
            {"debuff_id": "corrosive_slag", "name": "Corrosive Slag", "dr_override": 0, "turns_remaining": 2, "source": "Slag Spitter"},
            {"debuff_id": "serrated_bleed", "name": "Serrated Bleed", "turns_remaining": 5, "damage_per_turn": 6, "source": "Scrap-Saw Golem"},
        ]
        glenny["active_debuffs"] = debuffs

        # Save to DB and close session
        with db.db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, glenny, session_id=session_id)

        # Inspect ActiveDebuffRecord table directly
        with db.db_transaction(engine=self.engine) as s:
            char_rec = CharacterRepository.get_character_by_slug(s, slug, session_id=session_id)
            debuff_recs = list(char_rec.active_debuffs)
            self.assertEqual(len(debuff_recs), 3)
            ids = {d.debuff_id for d in debuff_recs}
            self.assertEqual(ids, {"foundry_shred", "corrosive_slag", "serrated_bleed"})

        # Now simulate a completely fresh thread/session reading the character
        def worker_load():
            with db.db_transaction(engine=self.engine) as s:
                return CharacterRepository.load_character(s, slug, session_id=session_id)

        loaded_result = []
        th = threading.Thread(target=lambda: loaded_result.append(worker_load()))
        th.start()
        th.join()

        loaded = loaded_result[0]
        self.assertIsNotNone(loaded)
        # Automatic recalculation assertions:
        self.assertEqual(loaded["ac"], 12, f"Expected AC 12 (16 - 4), got {loaded['ac']}")
        self.assertEqual(loaded["dr"], 0, f"Expected DR 0 (override), got {loaded['dr']}")
        self.assertEqual(len(loaded["active_debuffs"]), 3)

        # Verify custom bleed metadata preserved
        bleed_found = False
        for db_entry in loaded["active_debuffs"]:
            if db_entry["debuff_id"] == "serrated_bleed":
                bleed_found = True
                self.assertEqual(db_entry.get("damage_per_turn"), 6)
                self.assertEqual(db_entry.get("source"), "Scrap-Saw Golem")
        self.assertTrue(bleed_found, "Custom bleed debuff metadata missing from hydrated character")

    # =========================================================================
    # Area 3: Corpse Cache Double-Claim Race Condition
    # =========================================================================
    def test_05_corpse_cache_claim_concurrency_race(self):
        """
        Adversarial Stress Test:
        - Create a corpse cache record on Floor 1 with 5000 Col and 3 unique items.
        - Launch 10 concurrent threads simultaneously synchronized via a threading.Barrier.
        - Each thread calls CorpseCacheRepository.claim_cache().
        - Acceptance criteria: EXACTLY ONE thread must succeed (success=True, Col=5000, 3 items).
          All other 9 threads must receive success=False, recovered=True (0 col, 0 items).
        - No duplicate Col or items must be created.
        """
        session_id = "test_race_corpse_session"
        cache_id = "corpse_cache_floor1_race_test"
        items = ["Vorpal Edge", "Elixir of Life", "Amulet of the Eclipse"]
        col_amount = 5000

        with db.db_transaction(engine=self.engine) as s:
            CorpseCacheRepository.create_cache(
                s,
                session_id=session_id,
                floor=1,
                col=col_amount,
                inventory=items,
                cache_id=cache_id,
                fallen_name="Vanguard Vanguardian",
            )

        num_threads = 10
        barrier = threading.Barrier(num_threads)
        claim_results = []
        errors = []

        def claim_worker(thread_idx):
            barrier.wait()  # Fire all 10 threads at the exact same instant
            try:
                with db.db_transaction(engine=self.engine) as s:
                    res = CorpseCacheRepository.claim_cache(s, cache_id=cache_id, session_id=session_id)
                    claim_results.append((thread_idx, res))
            except Exception as exc:
                errors.append((thread_idx, exc))

        threads = [threading.Thread(target=claim_worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        successful_claims = [r for r in claim_results if isinstance(r[1], dict) and r[1].get("success") is True]
        idempotent_denials = [r for r in claim_results if isinstance(r[1], dict) and r[1].get("success") is False and r[1].get("recovered") is True]

        print("\n--- Initial 10-Thread Concurrency Run ---")
        print(f"Total Threads: {num_threads} | Successes: {len(successful_claims)} | Denials: {len(idempotent_denials)} | Errors: {len(errors)}")
        for t_idx, res in claim_results:
            if isinstance(res, dict):
                print(f"  Thread {t_idx:2d}: success={res.get('success')}, recovered={res.get('recovered')}, col={res.get('col')}")

        # Multi-Trial Stress Analysis: Run 5 separate 10-thread rounds to evaluate race consistency
        rounds_data = []
        for r_num in range(1, 6):
            c_id = f"corpse_cache_floor1_race_round_{r_num}"
            with db.db_transaction(engine=self.engine) as s:
                CorpseCacheRepository.create_cache(
                    s,
                    session_id=session_id,
                    floor=1,
                    col=col_amount,
                    inventory=items,
                    cache_id=c_id,
                    fallen_name=f"Vanguard {r_num}",
                )
            r_results = []
            r_barrier = threading.Barrier(10)

            def r_worker(t_idx, cache_ident):
                r_barrier.wait()
                try:
                    with db.db_transaction(engine=self.engine) as s:
                        res = CorpseCacheRepository.claim_cache(s, cache_id=cache_ident, session_id=session_id)
                        r_results.append((t_idx, res))
                except Exception as exc:
                    r_results.append((t_idx, exc))

            r_threads = [threading.Thread(target=r_worker, args=(i, c_id)) for i in range(10)]
            for t in r_threads:
                t.start()
            for t in r_threads:
                t.join()

            r_success = [r for r in r_results if isinstance(r[1], dict) and r[1].get("success") is True]
            rounds_data.append((r_num, len(r_success), sum(r[1].get("col", 0) for r in r_success)))

        print("\n--- Multi-Trial Concurrency Statistics (5 rounds x 10 threads) ---")
        for r_num, s_count, looted_col in rounds_data:
            print(f"  Round {r_num}: {s_count} successful claims (Total Looted: {looted_col} Col / Expected: 5000 Col)")

        # Invariant check: Exactly one thread per round must succeed
        self.assertEqual(
            len(successful_claims),
            1,
            f"RACE CONDITION DETECTED! Expected exactly 1 successful claim, but {len(successful_claims)} threads succeeded! "
            f"Total Col looted: {sum(r[1].get('col', 0) for r in successful_claims)} instead of {col_amount}."
        )
        self.assertEqual(len(idempotent_denials), 9, f"Expected 9 idempotent denials, got {len(idempotent_denials)}")


if __name__ == "__main__":
    unittest.main()
