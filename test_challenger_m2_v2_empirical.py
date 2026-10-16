"""
test_challenger_m2_v2_empirical.py
==================================
Milestone 2 Challenger 2 Empirical Adversarial Test Suite.

Adversarially challenges:
1. Glenny Parity & Relational Persistence:
   - 4-armed equipment configuration & multi-limb slot model (main_hand, off_hand, lower_main_hand, lower_off_hand)
   - 2H bow grip dynamic auto-binding & dual-2H weapon concurrency across upper/lower limb pairs
   - 9 anatomical graft slots (head, torso, left_arm, right_arm, lower_left_arm, lower_right_arm, legs, spine, tail)
   - Full CRUD lifecycle on AnatomicalGraftRecord under CharacterRepository
   - AC calculation: 14 base -> 16 shielded -> 17 Phalanx Cap -> 14 unshielded
   - Secondary Ganglia unit strain cap = 4

2. Legacy Race Key Conversions:
   - All 6 purged sci-fi lineages: neuromancer_cyborg, mantid_insectoid, nanite_host,
     void_walker, synthetic_android, phrenic_human
   - Fallback resolution via LEGACY_RACE_FALLBACKS into canonical pure fantasy lineages
   - generate_starting_character() stress testing under various parameter permutations
   - Full relational database persistence & hydration roundtrip for all 6 converted characters
   - Character creation catalog verification: get_character_creation_lineages() excludes 100% of sci-fi races

3. Physical Encumbrance & Carry Weight Mechanics:
   - Tiny lineages (Pixie < 30 in): size="Tiny", carry_mult=0.5, AC mod=+2, grapple mod=-8, stealth=+8
   - Medium lineages (Human 70 in): size="Medium", carry_mult=1.0, AC mod=0, reach=5ft
   - Large lineages (Minotaur, Centaur, Half-Ogre > 84 in): size="Large", carry_mult=2.0, AC mod=-1, reach=10ft, grapple=+4
   - Un-raced Large humanoids (86 in, no monstrous tag): carry_mult=1.5
   - Specific lineage bonuses: Centaur Quadruped (+80 lbs), Half-Ogre Hulking Bulk (+100 lbs)
   - Encumbrance load tiers: Unencumbered (<=50%), Light Load (50-75%), Heavy Load (75-100%, -2 DEX), Overencumbered (>100%, -5 DEX)
   - Encumbrance penalty coupling to combat AC calculation
   - Extreme boundary stress: STR 1, STR 30, STR 50, zero inventory, overcapacity loads
"""

import json
import logging
import os
import shutil
import sys
import tempfile
import unittest

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import sqlalchemy
from sqlalchemy import select, func

import backend.character_generator as cg
import backend.mechanics as m
from backend.database.engine import create_sao_engine, db_transaction, init_db
from backend.database.models import (
    CharacterRecord,
    EquippedSlotRecord,
    AnatomicalGraftRecord,
    ActiveDebuffRecord,
    SkillMasteryRecord,
)
from backend.database.repositories import CharacterRepository

logging.basicConfig(level=logging.WARNING)


class TestGlennyParityAndPersistence(unittest.TestCase):
    """Stress tests Glenny's 4-armed equipment, graft slots, AC, and DB persistence."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sao_m2_glenny_")
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.engine = create_sao_engine(f"sqlite:///{self.db_path}")
        init_db(self.engine)

    def tearDown(self):
        self.engine.dispose()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_glenny_baseline_anatomy_slots_and_strain(self):
        """Verify Glenny baseline anatomy: 4 hands, 9 graft slots, AC 14, max strain 4."""
        glenny = cg.generate_starting_character("Glenny", start_tutorial=False)
        self.assertEqual(glenny["race_key"], "troll_kreen_chimera")
        self.assertIn("Spliced Apex Chimera", glenny["race"])

        # Check equipment slots
        eq = glenny["equipped"]
        self.assertIn("main_hand", eq)
        self.assertIn("off_hand", eq)
        self.assertIn("lower_main_hand", eq)
        self.assertIn("lower_off_hand", eq)
        self.assertEqual(eq["main_hand"], "Recurve Hunting Bow")
        self.assertEqual(eq["off_hand"], "[2H Grip: Recurve Hunting Bow]")
        self.assertEqual(eq["lower_main_hand"], "Chipped Wood-Axe")
        self.assertEqual(eq["lower_off_hand"], "None")

        # Check anatomy profile
        prof = m.get_limb_anatomy_profile(glenny)
        self.assertTrue(prof["is_four_armed"])
        self.assertTrue(prof["is_tailed"])
        self.assertEqual(prof["arm_count"], 4)
        self.assertEqual(prof["secondary_ganglia_strain_bonus"], 1)

        # Verify exact 9 anatomical graft slots
        expected_graft_slots = [
            "head", "torso", "left_arm", "right_arm",
            "lower_left_arm", "lower_right_arm", "legs", "spine", "tail"
        ]
        self.assertEqual(len(prof["graft_slot_keys"]), 9)
        self.assertEqual(prof["graft_slot_keys"], expected_graft_slots)

        # Verify AC 14 base
        base_ac = m.calculate_ac(glenny)
        self.assertEqual(base_ac, 14, f"Glenny base AC must be 14, got {base_ac}")

        # Verify Max Unit Strain Cap is 4 (3 base + 1 Secondary Ganglia)
        max_strain = m.get_max_unit_strain(glenny)
        self.assertEqual(max_strain, 4, f"Glenny max unit strain must be 4, got {max_strain}")

    def test_02_glenny_shield_stacking_and_phalanx_cap_ac(self):
        """Verify Glenny AC transitions: 14 base -> 16 shielded -> 17 Phalanx Cap -> 14 unshielded."""
        glenny = cg.generate_starting_character("Glenny", start_tutorial=False)
        # Clear hands for clean testing
        glenny["equipped"]["main_hand"] = "Bronze Shortsword"
        glenny["equipped"]["off_hand"] = "None"
        glenny["equipped"]["lower_main_hand"] = "None"
        glenny["equipped"]["lower_off_hand"] = "None"

        # Baseline: AC 14
        self.assertEqual(m.calculate_ac(glenny), 14)

        # 1 Shield equipped in lower_off_hand -> AC 16
        glenny["equipped"]["lower_off_hand"] = "Wooden Buckler"
        self.assertEqual(m.calculate_ac(glenny), 16)

        # 2nd Shield equipped in lower_main_hand -> AC 17 (Phalanx Cover +1)
        glenny["equipped"]["lower_main_hand"] = "Iron Buckler"
        self.assertEqual(m.calculate_ac(glenny), 17)

        # 3rd Shield equipped in off_hand -> AC 17 (Capped at +3 max shield bonus)
        glenny["equipped"]["off_hand"] = "Steel Shield"
        self.assertEqual(m.calculate_ac(glenny), 17)

        # 4th Shield equipped in main_hand -> AC 17 (Capped)
        glenny["equipped"]["main_hand"] = "Tower Shield"
        self.assertEqual(m.calculate_ac(glenny), 17)

        # Unequip all shields
        glenny["equipped"]["main_hand"] = "None"
        glenny["equipped"]["off_hand"] = "None"
        glenny["equipped"]["lower_main_hand"] = "None"
        glenny["equipped"]["lower_off_hand"] = "None"
        self.assertEqual(m.calculate_ac(glenny), 14)

    def test_03_glenny_dual_2h_weapons_simultaneous_equipped(self):
        """Verify Glenny can hold TWO 2H weapons simultaneously across upper and lower limb pairs."""
        glenny = cg.generate_starting_character("Glenny", start_tutorial=False)

        # Upper arms: Recurve Hunting Bow + auto-bound [2H Grip: Recurve Hunting Bow]
        res1 = m.equip_item_to_slot(glenny, "Recurve Hunting Bow", "main_hand")
        self.assertTrue(res1["success"])
        self.assertTrue(res1["is_two_handed"])
        self.assertEqual(glenny["equipped"]["main_hand"], "Recurve Hunting Bow")
        self.assertEqual(glenny["equipped"]["off_hand"], "[2H Grip: Recurve Hunting Bow]")

        # Lower arms: Nodachi (2H weapon) + auto-bound [2H Grip: Nodachi]
        res2 = m.equip_item_to_slot(glenny, "Nodachi", "lower_main_hand")
        self.assertTrue(res2["success"])
        self.assertTrue(res2["is_two_handed"])
        self.assertEqual(glenny["equipped"]["lower_main_hand"], "Nodachi")
        self.assertEqual(glenny["equipped"]["lower_off_hand"], "[2H Grip: Nodachi]")

        # Persist dual-2H loadout to database
        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, glenny, session_id="dual_2h_sess")

        # Hydrate from DB & verify exact retention
        with db_transaction(engine=self.engine) as s:
            loaded = CharacterRepository.load_character(s, "glenny", session_id="dual_2h_sess")
            self.assertEqual(loaded["equipped"]["main_hand"], "Recurve Hunting Bow")
            self.assertEqual(loaded["equipped"]["off_hand"], "[2H Grip: Recurve Hunting Bow]")
            self.assertEqual(loaded["equipped"]["lower_main_hand"], "Nodachi")
            self.assertEqual(loaded["equipped"]["lower_off_hand"], "[2H Grip: Nodachi]")

        # Unequip upper bow by equipping 1H weapon into main_hand -> lower Nodachi remains intact
        m.equip_item_to_slot(loaded, "Bronze Shortsword", "main_hand")
        self.assertEqual(loaded["equipped"]["main_hand"], "Bronze Shortsword")
        self.assertEqual(loaded["equipped"]["off_hand"], "None")
        self.assertEqual(loaded["equipped"]["lower_main_hand"], "Nodachi")
        self.assertEqual(loaded["equipped"]["lower_off_hand"], "[2H Grip: Nodachi]")

        # Save and verify no orphaned grips in DB
        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, loaded, session_id="dual_2h_sess")

        with db_transaction(engine=self.engine) as s:
            raw_rec = CharacterRepository.get_character_by_slug(s, "glenny", session_id="dual_2h_sess")
            slots = {sl.slot_key: sl.item_name for sl in raw_rec.equipped_slots}
            self.assertNotIn("off_hand", slots)
            self.assertEqual(slots["main_hand"], "Bronze Shortsword")
            self.assertEqual(slots["lower_main_hand"], "Nodachi")
            self.assertEqual(slots["lower_off_hand"], "[2H Grip: Nodachi]")

    def test_04_glenny_nine_anatomical_grafts_crud_and_db_integrity(self):
        """Verify full CRUD lifecycle on all 9 anatomical graft slots under CharacterRepository."""
        glenny = cg.generate_starting_character("Glenny", start_tutorial=False)
        slots = [
            "head", "torso", "left_arm", "right_arm",
            "lower_left_arm", "lower_right_arm", "legs", "spine", "tail"
        ]

        # 1. Install 9 distinct grafts
        for slot in slots:
            glenny["graft_system"]["installed_grafts"][slot] = {
                "key": f"graft_{slot}",
                "name": f"Apex {slot.replace('_', ' ').title()} Mod",
                "slot": slot,
                "strain": 1,
                "unit_strain": 1,
                "element": "physical",
                "effect": f"+1 test stat for {slot}",
            }
        m.sync_graft_containers(glenny)

        # 2. Persist to DB
        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, glenny, session_id="graft_crud_sess")

        # 3. Direct SQL inspection of AnatomicalGraftRecord rows
        with db_transaction(engine=self.engine) as s:
            raw_rec = CharacterRepository.get_character_by_slug(s, "glenny", session_id="graft_crud_sess")
            self.assertEqual(len(raw_rec.anatomical_grafts), 9)
            db_slots = {g.slot_key: g for g in raw_rec.anatomical_grafts}
            for slot in slots:
                self.assertIn(slot, db_slots)
                self.assertEqual(db_slots[slot].graft_name, f"Apex {slot.replace('_', ' ').title()} Mod")
                self.assertEqual(db_slots[slot].unit_strain, 1)

        # 4. Hydrate via CharacterRepository.load_character
        with db_transaction(engine=self.engine) as s:
            loaded = CharacterRepository.load_character(s, "glenny", session_id="graft_crud_sess")
            self.assertIsNotNone(loaded)
            self.assertEqual(len(loaded["graft_system"]["installed_grafts"]), 9)
            for slot in slots:
                self.assertIn(slot, loaded["graft_system"]["installed_grafts"])
                self.assertEqual(loaded["graft_system"]["installed_grafts"][slot]["name"], f"Apex {slot.replace('_', ' ').title()} Mod")

        # 5. Mutate 1 graft and delete 2 grafts
        del loaded["graft_system"]["installed_grafts"]["lower_left_arm"]
        del loaded["graft_system"]["installed_grafts"]["tail"]
        loaded["grafts"]["lower_left_arm"] = None
        loaded["grafts"]["tail"] = None
        loaded["graft_system"]["installed_grafts"]["spine"]["name"] = "Overclocked Neural Spire"

        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, loaded, session_id="graft_crud_sess")

        # 6. Verify deletions and in-place updates in DB
        with db_transaction(engine=self.engine) as s:
            raw_rec2 = CharacterRepository.get_character_by_slug(s, "glenny", session_id="graft_crud_sess")
            self.assertEqual(len(raw_rec2.anatomical_grafts), 7)
            db_slots2 = {g.slot_key: g for g in raw_rec2.anatomical_grafts}
            self.assertNotIn("lower_left_arm", db_slots2)
            self.assertNotIn("tail", db_slots2)
            self.assertEqual(db_slots2["spine"].graft_name, "Overclocked Neural Spire")

            # Hydrated check
            reloaded = CharacterRepository.load_character(s, "glenny", session_id="graft_crud_sess")
            self.assertEqual(len(reloaded["graft_system"]["installed_grafts"]), 7)
            self.assertNotIn("lower_left_arm", reloaded["graft_system"]["installed_grafts"])
            self.assertNotIn("tail", reloaded["graft_system"]["installed_grafts"])
            self.assertEqual(reloaded["graft_system"]["installed_grafts"]["spine"]["name"], "Overclocked Neural Spire")


class TestLegacyRaceConversions(unittest.TestCase):
    """Stress tests the 6 purged sci-fi race conversions through character generation & database."""

    PURGED_RACES = [
        "neuromancer_cyborg",
        "mantid_insectoid",
        "nanite_host",
        "void_walker",
        "synthetic_android",
        "phrenic_human",
    ]

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sao_m2_purged_")
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.engine = create_sao_engine(f"sqlite:///{self.db_path}")
        init_db(self.engine)

    def tearDown(self):
        self.engine.dispose()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_05_purged_races_fallback_mapping_completeness(self):
        """Verify all 6 purged races exist in LEGACY_RACE_FALLBACKS and resolve to valid lineages."""
        fallbacks = getattr(cg, "LEGACY_RACE_FALLBACKS", {})
        self.assertTrue(bool(fallbacks), "LEGACY_RACE_FALLBACKS must be defined and non-empty")

        for purged in self.PURGED_RACES:
            self.assertIn(purged, fallbacks, f"Purged race '{purged}' missing from LEGACY_RACE_FALLBACKS")
            target = fallbacks[purged]
            self.assertIn(target, cg.RACIAL_LINEAGES, f"Fallback target '{target}' missing from RACIAL_LINEAGES")
            # Target must NOT be in purged list
            self.assertNotIn(target, self.PURGED_RACES, f"Fallback target '{target}' cannot be another purged race")

    def test_06_generate_starting_character_with_all_purged_races(self):
        """Verify generate_starting_character() accepts all 6 purged race keys safely and maps them."""
        for purged_key in self.PURGED_RACES:
            char = cg.generate_starting_character(
                name=f"Hero_{purged_key}",
                race_key=purged_key,
                start_tutorial=False,
            )
            self.assertIsNotNone(char)
            self.assertIn("stats", char)
            self.assertIn("hp", char)
            self.assertGreater(char["hp"], 0)

            # Check stats strictly positive
            for stat_name, stat_val in char["stats"].items():
                self.assertGreater(stat_val, 0, f"Stat {stat_name} must be > 0 for {purged_key}")

            # Check race_key is converted to pure fantasy fallback
            effective_key = cg.LEGACY_RACE_FALLBACKS[purged_key]
            self.assertEqual(char["race_key"], effective_key, f"Expected race_key {effective_key}, got {char['race_key']}")

    def test_07_purged_races_database_persistence_and_hydration(self):
        """Verify all 6 converted characters persist and hydrate identically through CharacterRepository."""
        for idx, purged_key in enumerate(self.PURGED_RACES):
            sess_id = f"purged_sess_{idx}"
            char = cg.generate_starting_character(
                name=f"Char_{purged_key}",
                race_key=purged_key,
                start_tutorial=False,
            )

            # Persist to DB
            with db_transaction(engine=self.engine) as s:
                saved = CharacterRepository.save_character(s, char, session_id=sess_id)
                self.assertIsNotNone(saved.id)

            # Hydrate from DB
            with db_transaction(engine=self.engine) as s:
                loaded = CharacterRepository.load_character(s, f"char_{purged_key}", session_id=sess_id)
                self.assertIsNotNone(loaded)
                self.assertEqual(loaded["race_key"], cg.LEGACY_RACE_FALLBACKS[purged_key])
                self.assertEqual(loaded["hp"], char["hp"])
                self.assertEqual(loaded["stats"], char["stats"])
                self.assertEqual(loaded["equipped"]["main_hand"], char["equipped"]["main_hand"])

    def test_08_character_creation_catalog_sci_fi_exclusion(self):
        """Verify get_character_creation_lineages() returns >= 25 entries and 0 sci-fi lineages."""
        creation_lineages = cg.get_character_creation_lineages()
        self.assertGreaterEqual(len(creation_lineages), 25, "Must have at least 25 pure fantasy lineages")

        for race_key, race_def in creation_lineages.items():
            self.assertNotIn(race_key, self.PURGED_RACES, f"Purged race '{race_key}' appeared in character creation!")
            genre = str(race_def.get("genre", "")).lower()
            for disallowed in cg.DISALLOWED_CREATION_GENRES:
                self.assertNotIn(
                    disallowed,
                    genre,
                    f"Lineage '{race_key}' has disallowed genre '{genre}' containing '{disallowed}'"
                )


class TestPhysicalEncumbranceAndCarryWeight(unittest.TestCase):
    """Stress tests physical encumbrance and carry weight across Tiny, Medium, and Large lineages."""

    def test_09_tiny_lineage_pixie_mechanics(self):
        """Verify Tiny lineage (Pixie): size, carry_mult 0.5, AC mod +2, grapple -8, stealth +8."""
        pixie = cg.generate_starting_character(
            name="AeroPixie",
            race_key="pixie_fey_sprite",
            start_tutorial=False
        )
        prof = m.get_physical_profile(pixie)
        self.assertEqual(prof["size"], "Tiny")
        self.assertLess(prof["height_in"], 30.0)
        self.assertEqual(prof["carry_mult"], 0.5)
        self.assertEqual(prof["ac_mod"], 2)
        self.assertEqual(prof["grapple_mod"], -8)
        self.assertEqual(prof["stealth_bonus"], 8)

        # Carry Capacity: STR * 15 * 0.5
        str_val = pixie["stats"]["STR"]
        enc = m.calculate_encumbrance(pixie)
        expected_max = round((str_val * 15.0) * 0.5, 1)
        self.assertEqual(enc["max_weight_lbs"], expected_max)

        # Encumbrance Tier progression on Pixie
        # Clean inventory
        pixie["inventory"] = []
        pixie["equipped"] = {}

        # 1. Unencumbered (<= 50%)
        pixie["inventory"] = [{"name": "Pebble", "qty": 1, "weight_lbs": expected_max * 0.4}]
        enc1 = m.calculate_encumbrance(pixie)
        self.assertEqual(enc1["tier"], "Unencumbered")
        self.assertEqual(enc1["penalties"]["dex_mod"], 0)

        # 2. Light Load (50% - 75%)
        pixie["inventory"] = [{"name": "Pebble", "qty": 1, "weight_lbs": expected_max * 0.6}]
        enc2 = m.calculate_encumbrance(pixie)
        self.assertEqual(enc2["tier"], "Light Load")
        self.assertEqual(enc2["penalties"]["dex_mod"], 0)

        # 3. Heavy Load (75% - 100%) -> -2 DEX penalty
        pixie["inventory"] = [{"name": "Pebble", "qty": 1, "weight_lbs": expected_max * 0.85}]
        enc3 = m.calculate_encumbrance(pixie)
        self.assertEqual(enc3["tier"], "Heavy Load")
        self.assertEqual(enc3["penalties"]["dex_mod"], -2)
        self.assertTrue(enc3["penalties"]["disadvantage_stealth"])

        # 4. Overencumbered (> 100%) -> -5 DEX penalty
        pixie["inventory"] = [{"name": "Pebble", "qty": 1, "weight_lbs": expected_max * 1.2}]
        enc4 = m.calculate_encumbrance(pixie)
        self.assertEqual(enc4["tier"], "Overencumbered")
        self.assertEqual(enc4["penalties"]["dex_mod"], -5)

    def test_10_medium_lineage_human_mechanics(self):
        """Verify Medium lineage (Human standard): size, carry_mult 1.0, AC mod 0, reach 5ft."""
        human = cg.generate_starting_character(
            name="Vanguard",
            race_key="human_standard",
            start_tutorial=False
        )
        prof = m.get_physical_profile(human)
        self.assertEqual(prof["size"], "Medium")
        self.assertGreaterEqual(prof["height_in"], 48.0)
        self.assertLessEqual(prof["height_in"], 84.0)
        self.assertEqual(prof["carry_mult"], 1.0)
        self.assertEqual(prof["ac_mod"], 0)
        self.assertEqual(prof["reach_ft"], 5)

        # Carry Capacity: STR * 15 * 1.0
        str_val = human["stats"]["STR"]
        enc = m.calculate_encumbrance(human)
        expected_max = round(str_val * 15.0 * 1.0, 1)
        self.assertEqual(enc["max_weight_lbs"], expected_max)

    def test_11_large_lineage_minotaur_and_centaur_mechanics(self):
        """Verify Large lineages: size, carry_mult 2.0, AC mod -1, reach 10ft, grapple +4, and racial bonuses."""
        # Minotaur (Large build, monstrous)
        minotaur = cg.generate_starting_character(
            name="Asterion",
            race_key="minotaur_labyrinth_breaker",
            start_tutorial=False
        )
        prof_m = m.get_physical_profile(minotaur)
        self.assertEqual(prof_m["size"], "Large")
        self.assertGreater(prof_m["height_in"], 84.0)
        self.assertEqual(prof_m["carry_mult"], 2.0)
        self.assertEqual(prof_m["ac_mod"], -1)
        self.assertEqual(prof_m["reach_ft"], 10)
        self.assertEqual(prof_m["grapple_mod"], 4)

        # Minotaur carry: STR * 15 * 2.0
        str_m = minotaur["stats"]["STR"]
        enc_m = m.calculate_encumbrance(minotaur)
        self.assertEqual(enc_m["max_weight_lbs"], round(str_m * 15.0 * 2.0, 1))

        # Centaur (Large quadruped with +80 lbs capacity bonus)
        centaur = cg.generate_starting_character(
            name="Chiron",
            race_key="centaur_plains_vanguard",
            start_tutorial=False
        )
        prof_c = m.get_physical_profile(centaur)
        self.assertEqual(prof_c["size"], "Large")
        self.assertEqual(prof_c["carry_mult"], 2.0)

        # Centaur carry: (STR * 15 + 80) * 2.0
        str_c = centaur["stats"]["STR"]
        enc_c = m.calculate_encumbrance(centaur)
        expected_c = round((str_c * 15.0 + 80.0) * 2.0, 1)
        self.assertEqual(enc_c["max_weight_lbs"], expected_c)

        # Half-Ogre (Large brute with +100 lbs capacity bonus)
        half_ogre = cg.generate_starting_character(
            name="Gorg",
            race_key="half_ogre_crusher",
            start_tutorial=False
        )
        str_ho = half_ogre["stats"]["STR"]
        enc_ho = m.calculate_encumbrance(half_ogre)
        expected_ho = round((str_ho * 15.0 + 100.0) * 2.0, 1)
        self.assertEqual(enc_ho["max_weight_lbs"], expected_ho)

    def test_12_unraced_large_humanoid_carry_multiplier(self):
        """Verify un-raced standard Large humanoid receives 1.5x carry multiplier."""
        tall_human = {
            "name": "TallGuy",
            "race": "Human",
            "stats": {"STR": 14, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
            "physical": {"age": 25, "height_in": 88.0, "weight_lbs": 280.0},
        }
        prof = m.get_physical_profile(tall_human)
        self.assertEqual(prof["size"], "Large")
        self.assertEqual(prof["carry_mult"], 1.5)

        enc = m.calculate_encumbrance(tall_human)
        expected_max = round((14 * 15.0) * 1.5, 1)
        self.assertEqual(enc["max_weight_lbs"], expected_max)

    def test_13_encumbrance_coupling_to_combat_ac(self):
        """Verify heavy and overencumbered loads penalize DEX and degrade AC down to minimum floor."""
        char = {
            "name": "ArmoredSoldier",
            "stats": {"STR": 10, "DEX": 16, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
            "equipped": {"chest": "Threadbare Scavenger Tunic"},
            "physical": {"age": 25, "height_in": 70.0, "weight_lbs": 180.0},
            "inventory": [],
        }
        # Baseline AC: 10 + 3 (DEX 16) + 1 (Tunic) = 14
        ac_base = m.calculate_ac(char)
        self.assertEqual(ac_base, 14)

        # Add heavy load: Max carry is 150 lbs, add 130 lbs (86.7%) -> Heavy Load (-2 DEX)
        char["inventory"] = [{"name": "Heavy Iron Anvil", "qty": 1, "weight_lbs": 130.0}]
        ac_heavy = m.calculate_ac(char)
        # DEX mod becomes 3 - 2 = 1 -> AC = 10 + 1 + 1 = 12
        self.assertEqual(ac_heavy, 12, f"Heavy load should reduce AC to 12, got {ac_heavy}")

        # Add overencumbered load: 200 lbs (133.3%) -> Overencumbered (-5 DEX)
        char["inventory"] = [{"name": "Massive Boulder", "qty": 1, "weight_lbs": 200.0}]
        ac_over = m.calculate_ac(char)
        # DEX mod becomes 3 - 5 = -2 -> AC = 10 + (-2) + 1 = 9, clamped to max(10, ...) = 10
        self.assertEqual(ac_over, 10, f"Overencumbered load should clamp AC at floor 10, got {ac_over}")

    def test_14_extreme_strength_boundary_conditions(self):
        """Stress test extreme STR boundaries (STR 1, STR 30, STR 50) across size categories."""
        for str_val in (1, 30, 50):
            tiny_char = {
                "name": "TinyTitan",
                "stats": {"STR": str_val, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
                "physical": {"age": 25, "height_in": 22.0, "weight_lbs": 15.0},
                "inventory": [],
            }
            enc_tiny = m.calculate_encumbrance(tiny_char)
            self.assertEqual(enc_tiny["max_weight_lbs"], round((str_val * 15.0) * 0.5, 1))

            large_char = {
                "name": "Giant",
                "race": "Minotaur",
                "stats": {"STR": str_val, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
                "physical": {"age": 25, "height_in": 96.0, "weight_lbs": 400.0},
                "inventory": [],
            }
            enc_large = m.calculate_encumbrance(large_char)
            self.assertEqual(enc_large["max_weight_lbs"], round((str_val * 15.0) * 2.0, 1))


def run_standalone():
    """Runs the suite and returns success boolean."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestGlennyParityAndPersistence)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestLegacyRaceConversions))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestPhysicalEncumbranceAndCarryWeight))
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    return res.wasSuccessful()


if __name__ == "__main__":
    success = run_standalone()
    sys.exit(0 if success else 1)
