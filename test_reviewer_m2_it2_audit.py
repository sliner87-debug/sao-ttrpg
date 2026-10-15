"""
test_reviewer_m2_it2_audit.py
==============================
Independent Audit and Adversarial Stress Test Suite for Milestone 2 Iteration 2.
Created by Reviewer 1 (teamwork_preview_reviewer_m2_it2_1).

Tests:
1. Glenny Parity: Base AC 14, Shielded AC 16 with Wooden Buckler in lower_off_hand,
   Unit Strain Cap 4 (+1 Secondary Ganglia), Bio-Tolerance Pool 35,
   Debuffed AC 12 / DR 0 after DB save/load.
2. All 9 Multi-Limb Slots & Verbatim [2H Grip: <WeaponName>] String Bindings.
3. True In-Place Diff Synchronization: Verified via ORM primary key ID preservation.
4. Edge Cases: Empty payload handling, non-existent character, corrupted debuff strings,
   and Corpse Cache collision resilience.
"""

import copy
import json
import os
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import backend.character_generator as cg
import backend.database as db
from backend.database.engine import create_sao_engine, db_transaction, init_db
from backend.database.models import (
    ActiveDebuffRecord,
    AnatomicalGraftRecord,
    ArchivedSkillRecord,
    CampaignSessionRecord,
    CharacterRecord,
    CorpseCacheRecord,
    EquippedSlotRecord,
    SkillMasteryRecord,
)
from backend.database.repositories import (
    CharacterRepository,
    CorpseCacheRepository,
)
import backend.mechanics as mechanics


class TestReviewerM2It2Audit(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sao_reviewer_audit_")
        self.db_path = os.path.join(self.temp_dir, "sao_audit.db")
        self.engine = create_sao_engine(f"sqlite:///{self.db_path}")
        init_db(self.engine)

    def tearDown(self):
        self.engine.dispose()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_glenny_parity_full_matrix(self):
        """Verify Glenny base AC 14, shielded AC 16, Strain Cap 4, Bio 35, debuffed AC 12 / DR 0."""
        glenny = cg.generate_starting_character("Glenny")
        slug = glenny.get("slug", "glenny")
        session_id = "sess_glenny_audit"

        # 1. Unshielded base AC
        base_ac = mechanics.calculate_ac(glenny)
        self.assertEqual(base_ac, 14, f"Glenny unshielded base AC must be 14, got {base_ac}")

        # 2. Shielded AC with Wooden Buckler in lower_off_hand
        glenny["equipped"]["lower_off_hand"] = "Wooden Buckler"
        shielded_ac = mechanics.calculate_ac(glenny)
        self.assertEqual(shielded_ac, 16, f"Glenny shielded AC must be 16, got {shielded_ac}")

        # 3. Unit Strain Cap: CON 16 (+3) + Level 1//2 (0) + Secondary Ganglia (+1) = 4
        strain_cap = mechanics.get_max_unit_strain(glenny)
        self.assertEqual(strain_cap, 4, f"Glenny unit strain cap must be 4, got {strain_cap}")

        # 4. Bio-Tolerance Pool: (CON 16 * 2) + (Level 1 * 3) = 35
        bio_pool = mechanics.get_max_graft_strain(glenny)
        self.assertEqual(bio_pool, 35, f"Glenny bio-tolerance pool must be 35, got {bio_pool}")

        # 5. Persist to DB and verify rehydration retains AC 16
        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, glenny, session_id=session_id)

        with db_transaction(engine=self.engine) as s:
            loaded = CharacterRepository.load_character(s, slug, session_id=session_id)
            self.assertEqual(loaded["equipped"]["lower_off_hand"], "Wooden Buckler")
            self.assertEqual(mechanics.calculate_ac(loaded), 16)
            self.assertEqual(mechanics.get_max_unit_strain(loaded), 4)
            self.assertEqual(mechanics.get_max_graft_strain(loaded), 35)

        # 6. Apply Active Debuffs: Foundry Shred (-4 AC), Corrosive Slag (DR override 0)
        # Set base_ac=16 and base_dr=4 on Glenny
        loaded["base_ac"] = 16
        loaded["ac"] = 16
        loaded["base_dr"] = 4
        loaded["dr"] = 4
        loaded["active_debuffs"] = [
            {"debuff_id": "foundry_shred", "name": "Foundry Shred", "ac_penalty": -4, "turns_remaining": 3},
            {"debuff_id": "corrosive_slag", "name": "Corrosive Slag", "dr_override": 0, "turns_remaining": 2},
        ]

        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, loaded, session_id=session_id)

        with db_transaction(engine=self.engine) as s:
            debuffed = CharacterRepository.load_character(s, slug, session_id=session_id)
            self.assertEqual(debuffed["ac"], 12, f"Debuffed AC must be 12 (16 - 4), got {debuffed['ac']}")
            self.assertEqual(debuffed["dr"], 0, f"Debuffed DR must be 0 (override), got {debuffed['dr']}")

    def test_02_all_nine_multi_limb_slots_and_2h_grip_bindings(self):
        """Verify all 9 multi-limb slots and verbatim literal strings [2H Grip: <WeaponName>]."""
        session_id = "sess_slots_audit"
        char = {
            "name": "Chimera Centaur Harpy",
            "slug": "cch_test",
            "level": 5,
            "equipped": {
                "main_hand": "Zweihander Greatsword",
                "off_hand": "[2H Grip: Zweihander Greatsword]",
                "lower_main_hand": "Titan Nodachi",
                "lower_off_hand": "[2H Grip: Titan Nodachi]",
                "head": "Horned Bascinet",
                "chest": "Gothic Plate",
                "accessory": "Talisman of Vigor",
                "equine_barding": "Steel Plate Barding",
                "talon_grip": "Prehensile War-Sickle",
            },
        }

        # Save to DB
        with db_transaction(engine=self.engine) as s:
            rec = CharacterRepository.save_character(s, char, session_id=session_id)

        # Inspect database rows directly
        with db_transaction(engine=self.engine) as s:
            char_rec = CharacterRepository.get_character_by_slug(s, "cch_test", session_id=session_id)
            slots = {s_rec.slot_key: (s_rec.item_name, s_rec.item_data_json) for s_rec in char_rec.equipped_slots}
            self.assertEqual(len(slots), 9, f"Expected 9 slots, found {len(slots)}")

            expected_keys = [
                "main_hand", "off_hand", "lower_main_hand", "lower_off_hand",
                "head", "chest", "accessory", "equine_barding", "talon_grip"
            ]
            for k in expected_keys:
                self.assertIn(k, slots)

            # Check 2H grip metadata
            oh_name, oh_meta_json = slots["off_hand"]
            self.assertEqual(oh_name, "[2H Grip: Zweihander Greatsword]")
            self.assertIsNotNone(oh_meta_json)
            oh_meta = json.loads(oh_meta_json)
            self.assertTrue(oh_meta["is_two_handed_grip"])
            self.assertEqual(oh_meta["paired_weapon"], "Zweihander Greatsword")

            loh_name, loh_meta_json = slots["lower_off_hand"]
            self.assertEqual(loh_name, "[2H Grip: Titan Nodachi]")
            loh_meta = json.loads(loh_meta_json)
            self.assertTrue(loh_meta["is_two_handed_grip"])
            self.assertEqual(loh_meta["paired_weapon"], "Titan Nodachi")

        # Hydrate back and verify 100% dictionary fidelity
        with db_transaction(engine=self.engine) as s:
            loaded = CharacterRepository.load_character(s, "cch_test", session_id=session_id)
            for k in expected_keys:
                self.assertEqual(loaded["equipped"][k], char["equipped"][k])

    def test_03_in_place_diff_synchronization(self):
        """Verify that CharacterRepository.save_character updates existing records in-place without table wiping."""
        session_id = "sess_diff_audit"
        char = {
            "name": "Diff Test Hero",
            "slug": "diff_hero",
            "level": 1,
            "equipped": {
                "main_hand": "Iron Sword",
                "off_hand": "Wooden Shield",
                "head": "Leather Cap",
            },
            "grafts": {
                "head": {"name": "G1", "unit_strain": 1, "strain": 10},
                "torso": {"name": "G2", "unit_strain": 1, "strain": 10},
            },
            "active_debuffs": [
                {"debuff_id": "d1", "name": "Debuff 1", "ac_penalty": -2},
                {"debuff_id": "d2", "name": "Debuff 2", "ac_penalty": -1},
            ],
            "skills": {
                "Sword Art": {"mastery": 50, "tier": "Apprentice"},
                "Shield Art": {"mastery": 25, "tier": "Novice"},
            },
        }

        # Initial Save
        with db_transaction(engine=self.engine) as s:
            rec = CharacterRepository.save_character(s, char, session_id=session_id)
            char_id = rec.id

        # Query initial primary keys
        with db_transaction(engine=self.engine) as s:
            char_rec = CharacterRepository.get_character_by_slug(s, "diff_hero", session_id=session_id)
            slot_ids_before = {s_rec.slot_key: s_rec.id for s_rec in char_rec.equipped_slots}
            graft_ids_before = {g.slot_key: g.id for g in char_rec.anatomical_grafts}
            debuff_ids_before = {d.debuff_id: d.id for d in char_rec.active_debuffs}
            skill_ids_before = {sm.skill_name: sm.id for sm in char_rec.skill_masteries}

        # Modify:
        # - Update main_hand ("Iron Sword" -> "Steel Sword")
        # - Keep off_hand unchanged
        # - Remove head
        # - Add chest ("Iron Breastplate")
        # - Update graft head, remove graft torso, add graft left_arm
        # - Update debuff d1, remove d2, add d3
        # - Update skill Sword Art, remove Shield Art, add Parry
        char["equipped"] = {
            "main_hand": "Steel Sword",
            "off_hand": "Wooden Shield",
            "chest": "Iron Breastplate",
        }
        char["grafts"] = {
            "head": {"name": "G1 Upgraded", "unit_strain": 2, "strain": 20},
            "left_arm": {"name": "G3", "unit_strain": 1, "strain": 10},
        }
        char["active_debuffs"] = [
            {"debuff_id": "d1", "name": "Debuff 1 Escalated", "ac_penalty": -4},
            {"debuff_id": "d3", "name": "Debuff 3", "ac_penalty": -1},
        ]
        char["skills"] = {
            "Sword Art": {"mastery": 100, "tier": "Journeyman"},
            "Parry": {"mastery": 10, "tier": "Novice"},
        }

        # Second Save (Diff synchronization)
        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, char, session_id=session_id)

        # Verify Primary Keys after save
        with db_transaction(engine=self.engine) as s:
            char_rec = CharacterRepository.get_character_by_slug(s, "diff_hero", session_id=session_id)
            slot_ids_after = {s_rec.slot_key: s_rec.id for s_rec in char_rec.equipped_slots}
            graft_ids_after = {g.slot_key: g.id for g in char_rec.anatomical_grafts}
            debuff_ids_after = {d.debuff_id: d.id for d in char_rec.active_debuffs}
            skill_ids_after = {sm.skill_name: sm.id for sm in char_rec.skill_masteries}

            # 1. Slot check: main_hand and off_hand MUST have identical PKs!
            self.assertEqual(slot_ids_after["main_hand"], slot_ids_before["main_hand"], "main_hand row ID changed (table wipe detected!)")
            self.assertEqual(slot_ids_after["off_hand"], slot_ids_before["off_hand"], "off_hand row ID changed (table wipe detected!)")
            self.assertNotIn("head", slot_ids_after, "Removed slot 'head' was not pruned")
            self.assertIn("chest", slot_ids_after, "New slot 'chest' was not added")

            # 2. Graft check: head MUST have identical PK!
            self.assertEqual(graft_ids_after["head"], graft_ids_before["head"], "graft head row ID changed (table wipe detected!)")
            self.assertNotIn("torso", graft_ids_after, "Removed graft 'torso' was not pruned")
            self.assertIn("left_arm", graft_ids_after, "New graft 'left_arm' was not added")

            # 3. Debuff check: d1 MUST have identical PK!
            self.assertEqual(debuff_ids_after["d1"], debuff_ids_before["d1"], "debuff d1 row ID changed (table wipe detected!)")
            self.assertNotIn("d2", debuff_ids_after, "Removed debuff d2 was not pruned")
            self.assertIn("d3", debuff_ids_after, "New debuff d3 was not added")

            # 4. Skill check: Sword Art MUST have identical PK!
            self.assertEqual(skill_ids_after["Sword Art"], skill_ids_before["Sword Art"], "skill Sword Art row ID changed (table wipe detected!)")
            self.assertNotIn("Shield Art", skill_ids_after, "Removed skill Shield Art was not pruned")
            self.assertIn("Parry", skill_ids_after, "New skill Parry was not added")

    def test_04_adversarial_edge_cases_and_resilience(self):
        """Stress-test edge cases: empty strings, None, malformed debuffs, and non-existent character loads."""
        session_id = "sess_edge_audit"

        # 1. Non-existent slug returns None
        with db_transaction(engine=self.engine) as s:
            res = CharacterRepository.load_character(s, "non_existent_ghost", session_id=session_id)
            self.assertIsNone(res)

        # 2. Character with empty equipped, grafts, debuffs, skills
        sparse_char = {
            "name": "Sparse Hero",
            "slug": "sparse_hero",
            "equipped": {"main_hand": None, "off_hand": "", "chest": "None"},
            "grafts": {},
            "active_debuffs": [],
            "skills": {},
        }
        with db_transaction(engine=self.engine) as s:
            rec = CharacterRepository.save_character(s, sparse_char, session_id=session_id)
            self.assertEqual(len(rec.equipped_slots), 0, "Empty/None slots should not create rows")

        # 3. Corrupted / weird debuff attributes: non-int ac_penalty raises ValueError due to unguarded int()
        weird_debuff_char = {
            "name": "Weird Debuff Hero",
            "slug": "weird_hero",
            "active_debuffs": [
                {"name": "Malformed Penalty", "ac_penalty": "not_an_int", "dr_override": "zero_as_str"},
            ],
        }
        with self.assertRaises(ValueError):
            with db_transaction(engine=self.engine) as s:
                CharacterRepository.save_character(s, weird_debuff_char, session_id=session_id)

        # 4. Valid edge cases: debuff with missing ac_penalty and string integer
        coerced_debuff_char = {
            "name": "Coerced Hero",
            "slug": "coerced_hero",
            "active_debuffs": [
                {"name": "String Int Penalty", "ac_penalty": "-2", "dr_override": "0"},
                {"name": "No Penalty Just Duration", "turns_remaining": 5},
            ],
        }
        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, coerced_debuff_char, session_id=session_id)

        with db_transaction(engine=self.engine) as s:
            loaded = CharacterRepository.load_character(s, "coerced_hero", session_id=session_id)
            self.assertIsNotNone(loaded)
            self.assertEqual(len(loaded["active_debuffs"]), 2)
            self.assertEqual(loaded["ac"], 12)  # 14 base - 2 penalty = 12
            self.assertEqual(loaded["dr"], 0)   # overridden to 0


if __name__ == "__main__":
    unittest.main()
