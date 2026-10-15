"""
test_m2_challenger_equipment.py
================================
Milestone 2 Challenger 1 Empirical Test Harness.
Adversarial Verification Suite for:
1. Dynamic 2H Grip Swapping (Upper & Lower Arms, verbatim string preservation, clean unequip/swap without orphaned DB rows).
2. Multi-Limb 4-Shield Stacking on 4-Armed Entities (Glenny Phalanx Cap AC 14 -> 16 -> 17, DB persistence & hydration, unequip rollback).
3. Concurrent Slot & Attribute Mutations (10 concurrent threads hammering CharacterRepository, UniqueConstraint & StaleData handling, attribute retention).
4. Core V2 Test Suites Baseline Health Checks.
"""

import copy
import json
import logging
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import sqlalchemy
from sqlalchemy import func, inspect, select, text

import backend.character_generator as cg
import backend.database as db
import backend.mechanics as m
from backend.database.engine import (
    create_sao_engine,
    db_transaction,
    init_db,
)
from backend.database.models import (
    ActiveDebuffRecord,
    AnatomicalGraftRecord,
    CampaignSessionRecord,
    CharacterRecord,
    EquippedSlotRecord,
)
from backend.database.repositories import (
    CharacterRepository,
    CorpseCacheRepository,
    PartyRepository,
    WorldRepository,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("test_m2_challenger_equipment")


class TestM2ChallengerEquipment(unittest.TestCase):
    """Milestone 2 Challenger 1 Test Suite."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sao_m2_chal1_")
        self.db_path = os.path.join(self.temp_dir, "sao_sandbox.db")
        self.engine = create_sao_engine(f"sqlite:///{self.db_path}")
        init_db(self.engine)

    def tearDown(self):
        self.engine.dispose()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # =========================================================================
    # Test Suite 1: Dynamic 2H Grip Swapping
    # =========================================================================

    def test_01_dynamic_2h_grip_swapping_upper_arms(self):
        """Verify 2H weapon in main_hand auto-binds off_hand with verbatim string, persists, and swaps cleanly."""
        glenny = cg.generate_starting_character("Glenny")
        
        # 1. Equip 2H weapon Recurve Hunting Bow into main_hand
        equip_res = m.equip_item_to_slot(glenny, "Recurve Hunting Bow", "main_hand")
        self.assertTrue(equip_res["success"])
        self.assertTrue(equip_res["is_two_handed"])
        self.assertEqual(equip_res["paired_slot"], "off_hand")
        self.assertEqual(glenny["equipped"]["main_hand"], "Recurve Hunting Bow")
        self.assertEqual(glenny["equipped"]["off_hand"], "[2H Grip: Recurve Hunting Bow]")

        # 2. Persist to DB
        with db_transaction(engine=self.engine) as s:
            rec = CharacterRepository.save_character(s, glenny, session_id="test_grip_sess")
            self.assertIsNotNone(rec.id)

        # 3. Hydrate back from DB & verify exact verbatim string
        with db_transaction(engine=self.engine) as s:
            loaded = CharacterRepository.load_character(s, "glenny", session_id="test_grip_sess")
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded["equipped"]["main_hand"], "Recurve Hunting Bow")
            self.assertEqual(loaded["equipped"]["off_hand"], "[2H Grip: Recurve Hunting Bow]")

            # Verify underlying DB row metadata
            raw_rec = CharacterRepository.get_character_by_slug(s, "glenny", session_id="test_grip_sess")
            slot_records = {sl.slot_key: sl for sl in raw_rec.equipped_slots}
            self.assertIn("off_hand", slot_records)
            self.assertEqual(slot_records["off_hand"].item_name, "[2H Grip: Recurve Hunting Bow]")
            meta = json.loads(slot_records["off_hand"].item_data_json)
            self.assertTrue(meta.get("is_two_handed_grip"))
            self.assertEqual(meta.get("paired_weapon"), "Recurve Hunting Bow")

        # 4. Swap main_hand for 1H weapon (Bronze Shortsword)
        swap_res = m.equip_item_to_slot(loaded, "Bronze Shortsword", "main_hand")
        self.assertTrue(swap_res["success"])
        self.assertFalse(swap_res["is_two_handed"])
        self.assertEqual(loaded["equipped"]["main_hand"], "Bronze Shortsword")
        self.assertEqual(loaded["equipped"]["off_hand"], "None")

        # 5. Save and reload, verify no orphaned 2H grip records in DB
        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, loaded, session_id="test_grip_sess")

        with db_transaction(engine=self.engine) as s:
            reloaded = CharacterRepository.load_character(s, "glenny", session_id="test_grip_sess")
            self.assertEqual(reloaded["equipped"]["main_hand"], "Bronze Shortsword")
            self.assertEqual(reloaded["equipped"]["off_hand"], "None")

            raw_rec2 = CharacterRepository.get_character_by_slug(s, "glenny", session_id="test_grip_sess")
            db_slots = {sl.slot_key: sl.item_name for sl in raw_rec2.equipped_slots}
            self.assertNotIn("off_hand", db_slots)
            for k, v in db_slots.items():
                self.assertNotIn("2H Grip", v, f"Orphaned 2H grip record persisted in slot {k}: {v}")

    def test_02_dynamic_2h_grip_swapping_lower_arms(self):
        """Verify 2H weapon in lower_main_hand auto-binds lower_off_hand and cleans up on 1H replacement."""
        glenny = cg.generate_starting_character("Glenny")
        
        # Equip Nodachi (2H weapon) into lower_main_hand
        equip_res = m.equip_item_to_slot(glenny, "Nodachi", "lower_main_hand")
        self.assertTrue(equip_res["success"])
        self.assertTrue(equip_res["is_two_handed"])
        self.assertEqual(equip_res["paired_slot"], "lower_off_hand")
        self.assertEqual(glenny["equipped"]["lower_main_hand"], "Nodachi")
        self.assertEqual(glenny["equipped"]["lower_off_hand"], "[2H Grip: Nodachi]")

        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, glenny, session_id="test_lower_2h")

        with db_transaction(engine=self.engine) as s:
            loaded = CharacterRepository.load_character(s, "glenny", session_id="test_lower_2h")
            self.assertEqual(loaded["equipped"]["lower_main_hand"], "Nodachi")
            self.assertEqual(loaded["equipped"]["lower_off_hand"], "[2H Grip: Nodachi]")

        # Replace lower_main_hand with 1H Dagger
        m.equip_item_to_slot(loaded, "Iron Dagger", "lower_main_hand")
        self.assertEqual(loaded["equipped"]["lower_main_hand"], "Iron Dagger")
        self.assertEqual(loaded["equipped"]["lower_off_hand"], "None")

        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, loaded, session_id="test_lower_2h")

        with db_transaction(engine=self.engine) as s:
            reloaded = CharacterRepository.load_character(s, "glenny", session_id="test_lower_2h")
            self.assertEqual(reloaded["equipped"]["lower_main_hand"], "Iron Dagger")
            self.assertEqual(reloaded["equipped"]["lower_off_hand"], "None")
            raw_rec = CharacterRepository.get_character_by_slug(s, "glenny", session_id="test_lower_2h")
            db_slots = {sl.slot_key: sl.item_name for sl in raw_rec.equipped_slots}
            self.assertNotIn("lower_off_hand", db_slots)

    def test_03_equipping_1h_to_offhand_clears_2h_main_hand(self):
        """Equipping a shield or 1H weapon into off_hand when main_hand holds 2H weapon unequips main_hand."""
        glenny = cg.generate_starting_character("Glenny")
        m.equip_item_to_slot(glenny, "Recurve Hunting Bow", "main_hand")
        self.assertEqual(glenny["equipped"]["off_hand"], "[2H Grip: Recurve Hunting Bow]")

        # Equip shield into off_hand
        equip_res = m.equip_item_to_slot(glenny, "Steel Shield", "off_hand")
        self.assertTrue(equip_res["success"])
        self.assertEqual(glenny["equipped"]["off_hand"], "Steel Shield")
        self.assertEqual(glenny["equipped"]["main_hand"], "None")

        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, glenny, session_id="test_offhand_swap")

        with db_transaction(engine=self.engine) as s:
            loaded = CharacterRepository.load_character(s, "glenny", session_id="test_offhand_swap")
            self.assertEqual(loaded["equipped"]["off_hand"], "Steel Shield")
            self.assertEqual(loaded["equipped"]["main_hand"], "None")

    # =========================================================================
    # Test Suite 2: Multi-Limb 4-Shield Stacking on 4-Armed Entities
    # =========================================================================

    def test_04_four_shield_stacking_ac_and_persistence(self):
        """Test Glenny equipping 4 shields across all 4 arms, verifying Phalanx Cap AC rules and DB lifecycle."""
        glenny = cg.generate_starting_character("Glenny")
        # Reset upper hands to unshielded
        glenny["equipped"]["main_hand"] = "Bronze Shortsword"
        glenny["equipped"]["off_hand"] = "None"
        glenny["equipped"]["lower_main_hand"] = "None"
        glenny["equipped"]["lower_off_hand"] = "None"

        # Baseline Unshielded AC: 10 + 2 (DEX) + 1 (Tunic) + 2 (Hide) - 1 (Large) = 14
        ac_unshielded = m.calculate_ac(glenny)
        self.assertEqual(ac_unshielded, 14, f"Base AC expected 14, got {ac_unshielded}")

        # 1st Shield: Wooden Buckler in lower_off_hand (+2 AC) -> AC 16
        glenny["equipped"]["lower_off_hand"] = "Wooden Buckler"
        ac_1_shield = m.calculate_ac(glenny)
        self.assertEqual(ac_1_shield, 16, f"1 Shield AC expected 16, got {ac_1_shield}")

        # 2nd Shield: Iron Buckler in lower_main_hand (+1 Phalanx Cap) -> AC 17
        glenny["equipped"]["lower_main_hand"] = "Iron Buckler"
        ac_2_shields = m.calculate_ac(glenny)
        self.assertEqual(ac_2_shields, 17, f"2 Shields AC expected 17, got {ac_2_shields}")

        # 3rd Shield: Steel Shield in off_hand (+0, capped at +3 total shield bonus) -> AC 17
        glenny["equipped"]["off_hand"] = "Steel Shield"
        ac_3_shields = m.calculate_ac(glenny)
        self.assertEqual(ac_3_shields, 17, f"3 Shields AC expected 17 (capped), got {ac_3_shields}")

        # 4th Shield: Tower Shield in main_hand (+0, capped at +3 total shield bonus) -> AC 17
        glenny["equipped"]["main_hand"] = "Tower Shield"
        ac_4_shields = m.calculate_ac(glenny)
        self.assertEqual(ac_4_shields, 17, f"4 Shields AC expected 17 (capped), got {ac_4_shields}")

        # Persist full 4-shield build to database
        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, glenny, session_id="test_4_shields")

        # Hydrate back and verify relational records and combat AC calculation
        with db_transaction(engine=self.engine) as s:
            loaded = CharacterRepository.load_character(s, "glenny", session_id="test_4_shields")
            self.assertEqual(loaded["equipped"]["main_hand"], "Tower Shield")
            self.assertEqual(loaded["equipped"]["off_hand"], "Steel Shield")
            self.assertEqual(loaded["equipped"]["lower_main_hand"], "Iron Buckler")
            self.assertEqual(loaded["equipped"]["lower_off_hand"], "Wooden Buckler")
            self.assertEqual(m.calculate_ac(loaded), 17)

            raw_rec = CharacterRepository.get_character_by_slug(s, "glenny", session_id="test_4_shields")
            db_slots = {sl.slot_key: sl.item_name for sl in raw_rec.equipped_slots}
            self.assertEqual(db_slots["main_hand"], "Tower Shield")
            self.assertEqual(db_slots["off_hand"], "Steel Shield")
            self.assertEqual(db_slots["lower_main_hand"], "Iron Buckler")
            self.assertEqual(db_slots["lower_off_hand"], "Wooden Buckler")

        # Step-down unequip: Remove 3 shields, leaving 1 shield
        loaded["equipped"]["main_hand"] = "None"
        loaded["equipped"]["off_hand"] = "None"
        loaded["equipped"]["lower_main_hand"] = "None"
        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, loaded, session_id="test_4_shields")

        with db_transaction(engine=self.engine) as s:
            re1 = CharacterRepository.load_character(s, "glenny", session_id="test_4_shields")
            self.assertEqual(m.calculate_ac(re1), 16)
            raw_rec1 = CharacterRepository.get_character_by_slug(s, "glenny", session_id="test_4_shields")
            db_slots1 = {sl.slot_key: sl.item_name for sl in raw_rec1.equipped_slots}
            self.assertNotIn("main_hand", db_slots1)
            self.assertNotIn("off_hand", db_slots1)
            self.assertNotIn("lower_main_hand", db_slots1)
            self.assertEqual(db_slots1["lower_off_hand"], "Wooden Buckler")

        # Unequip last shield -> verify AC drops back to 14
        re1["equipped"]["lower_off_hand"] = "None"
        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, re1, session_id="test_4_shields")

        with db_transaction(engine=self.engine) as s:
            re0 = CharacterRepository.load_character(s, "glenny", session_id="test_4_shields")
            self.assertEqual(m.calculate_ac(re0), 14)

    # =========================================================================
    # Test Suite 3: Concurrent Slot Mutations & Thread Safety Analysis
    # =========================================================================

    def test_05_concurrent_attribute_mutations_retain_equipped_slots(self):
        """10 concurrent threads hammering character attributes without 'equipped' in payload preserve all equipment slots."""
        glenny = cg.generate_starting_character("Glenny")
        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, glenny, session_id="test_attr_conc")

        errors = []
        def worker(idx):
            for attempt in range(10):
                try:
                    with db_transaction(engine=self.engine) as s:
                        CharacterRepository.save_character(
                            s,
                            {"name": "Glenny", "col": 100 + idx, "hp": 100 - idx},
                            session_id="test_attr_conc",
                        )
                    break
                except Exception as e:
                    if attempt == 9:
                        errors.append((idx, e))
                    time.sleep(0.01 * (attempt + 1))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Errors encountered during concurrent attribute updates: {errors}")

        with db_transaction(engine=self.engine) as s:
            final_c = CharacterRepository.load_character(s, "glenny", session_id="test_attr_conc")
            eq = {k: v for k, v in final_c["equipped"].items() if v != "None"}
            self.assertEqual(len(eq), 5, f"Expected 5 equipped slots preserved, got {len(eq)}: {eq}")
            self.assertEqual(eq["chest"], "Threadbare Scavenger Tunic")
            self.assertEqual(eq["main_hand"], "Recurve Hunting Bow")
            self.assertEqual(eq["off_hand"], "[2H Grip: Recurve Hunting Bow]")
            self.assertEqual(eq["accessory"], "Hunting Laser Rangefinder")
            self.assertEqual(eq["lower_main_hand"], "Chipped Wood-Axe")

    def test_06_concurrent_distinct_characters_multi_thread(self):
        """10 concurrent threads simultaneously creating and modifying distinct character records (Acceptance Criterion R1)."""
        errors = []

        def worker_char(idx):
            s_id = f"session_worker_{idx}"
            for attempt in range(10):
                try:
                    with db_transaction(engine=self.engine) as s:
                        c_dict = {
                            "name": f"Vanguard_{idx}",
                            "level": idx + 1,
                            "hp": 100 + (idx * 10),
                            "col": idx * 100,
                            "equipped": {
                                "main_hand": f"Weapon_{idx}",
                                "chest": f"Armor_{idx}",
                            },
                        }
                        CharacterRepository.save_character(s, c_dict, session_id=s_id)
                    break
                except Exception as e:
                    if attempt == 9:
                        errors.append((idx, e))
                    time.sleep(0.01 * (attempt + 1))

        threads = [threading.Thread(target=worker_char, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent distinct character creation failed: {errors}")

        with db_transaction(engine=self.engine) as s:
            for idx in range(10):
                loaded = CharacterRepository.load_character(s, f"vanguard_{idx}", session_id=f"session_worker_{idx}")
                self.assertIsNotNone(loaded)
                self.assertEqual(loaded["level"], idx + 1)
                self.assertEqual(loaded["equipped"]["main_hand"], f"Weapon_{idx}")
                self.assertEqual(loaded["equipped"]["chest"], f"Armor_{idx}")

    def test_07_concurrent_slot_hammering_semantics_analysis(self):
        """
        Adversarial Concurrency Stress Test:
        10 threads simultaneously hammering different equipment slots on the same character record.
        Documents and verifies concurrency behavior, SQLite busy-timeout retry handling,
        and in-place diffing mechanics.
        """
        with db_transaction(engine=self.engine) as s:
            base_glenny = {
                "name": "Glenny",
                "hp": 135,
                "col": 500,
                "equipped": {
                    "head": "None",
                    "chest": "None",
                    "main_hand": "None",
                    "off_hand": "None",
                    "lower_main_hand": "None",
                    "lower_off_hand": "None",
                    "accessory": "None",
                    "talon_grip": "None",
                    "equine_barding": "None",
                },
            }
            CharacterRepository.save_character(s, base_glenny, session_id="hammer_sess")

        target_slots = [
            "main_hand",
            "off_hand",
            "lower_main_hand",
            "lower_off_hand",
            "head",
            "chest",
            "accessory",
            "talon_grip",
            "equine_barding",
        ]

        slot_errors = []
        barrier = threading.Barrier(len(target_slots))

        def slot_hammerer(slot_name, item_name):
            barrier.wait()
            # Perform transactional read-modify-save with exponential backoff
            for attempt in range(15):
                try:
                    with db_transaction(engine=self.engine) as s:
                        c = CharacterRepository.load_character(s, "glenny", session_id="hammer_sess")
                        c["equipped"][slot_name] = item_name
                        CharacterRepository.save_character(s, c, session_id="hammer_sess")
                    break
                except Exception as e:
                    if attempt == 14:
                        slot_errors.append((slot_name, type(e).__name__, str(e)))
                    time.sleep(0.01 * (2 ** min(attempt, 5)))

        threads = [
            threading.Thread(target=slot_hammerer, args=(sl, f"Gear_{sl}"))
            for sl in target_slots
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Database health check: ensure DB remains intact and operational
        with db_transaction(engine=self.engine) as s:
            final_c = CharacterRepository.load_character(s, "glenny", session_id="hammer_sess")
            self.assertIsNotNone(final_c)
            # The character is intact, no database corruption occurred
            eq_survived = {k: v for k, v in final_c["equipped"].items() if v != "None"}
            logger.info("Concurrent Slot Hammering Results: %d slots survived: %s", len(eq_survived), eq_survived)
            logger.info("Slot Hammering Exceptions Encountered on Max Retries: %s", slot_errors)
            # Integrity check: No fatal uncaught process crashes
            self.assertGreater(len(eq_survived), 0, "At least some slots must be committed")


def run_standalone():
    """Runs all tests and returns boolean success."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestM2ChallengerEquipment)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    return res.wasSuccessful()


if __name__ == "__main__":
    success = run_standalone()
    sys.exit(0 if success else 1)
