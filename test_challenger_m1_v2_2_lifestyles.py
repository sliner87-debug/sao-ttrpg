"""
test_challenger_m1_v2_2_lifestyles.py
======================================
Empirical Adversarial Challenge Suite 2 for Milestone 1:
Expanded Lifestyle Archetypes (Requirement R1).

Focus Areas:
1. Glenny Isolation & Hardening (AC 14/16, Strain Cap 4, 4-armed equipment slots, zero desk_bound pollution).
2. Backward Compatibility & Parameter Ingress (Default hero, positional argument matrix, fallback on unknown keys, SkillEntry hybrid behavior).
3. Database Persistence across ALL 26 Lifestyles (SQLAlchemy models and repositories save/load round-trips, session isolation, state mutability).
"""

import copy
import json
import os
import shutil
import sys
import tempfile
import unittest

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import backend.character_generator as cg
import backend.mechanics as mechanics
from backend.character_generator import SkillEntry, PRESET_LIFESTYLES
from backend.database.engine import db_transaction, get_engine
from backend.database.models import Base, CharacterRecord
from backend.database.repositories import CharacterRepository


class TestGlennyIsolationAndHardening(unittest.TestCase):
    """
    Stress test Glenny isolation:
    Ensure Glenny retains canonical stats, AC 14 base / 16 shielded,
    Unit Strain Cap 4, 4-armed equipment slots, and zero pollution from desk_bound.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sao_test_glenny_")
        self.db_path = os.path.join(self.temp_dir, "glenny_test.db")
        self.engine = get_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_glenny_default_generation_canonical_stats(self):
        """Calling generate_starting_character('Glenny') produces canonical attributes."""
        glenny = cg.generate_starting_character("Glenny", start_tutorial=False)

        # Canonical attributes from saves/Glenny/save_game.json:
        # STR: 10 + 5 (alloc) + 3 (troll_kreen) = 18
        # DEX: 10 + 5 (alloc) + 0 (troll_kreen) = 15
        # CON: 10 + 4 (alloc) + 2 (troll_kreen) = 16
        # INT: 10 + 2 (alloc) - 1 (troll_kreen) = 11
        # WIS: 10 + 3 (alloc) + 0 (troll_kreen) = 13
        # CHA: 10 + 1 (alloc) - 2 (troll_kreen) = 9
        expected_stats = {"STR": 18, "DEX": 15, "CON": 16, "INT": 11, "WIS": 13, "CHA": 9}
        self.assertEqual(glenny["stats"], expected_stats, f"Glenny stats mismatch: {glenny['stats']}")

    def test_02_glenny_ac_calculation_base_and_shielded(self):
        """Glenny achieves baseline unshielded AC 14 and single-shield AC 16."""
        glenny = cg.generate_starting_character("Glenny", start_tutorial=False)

        # Baseline AC: 10 + 2 (DEX +2 mod) + 1 (Tunic) + 2 (Hide) - 1 (Large build) = 14
        ac_base = mechanics.calculate_ac(glenny)
        self.assertEqual(ac_base, 14, f"Glenny baseline AC must be 14, got {ac_base}")

        # Equipping Wooden Buckler into lower_off_hand (+2 shield AC) -> 16
        glenny_shield = copy.deepcopy(glenny)
        glenny_shield["equipped"]["lower_off_hand"] = "Wooden Buckler"
        ac_shielded = mechanics.calculate_ac(glenny_shield)
        self.assertEqual(ac_shielded, 16, f"Glenny shielded AC must be 16, got {ac_shielded}")

    def test_03_glenny_unit_strain_cap_and_bio_tolerance(self):
        """Glenny computes Unit Strain Cap 4 (CON 16 mod +3, Secondary Ganglia +1) and Bio Pool 35."""
        glenny = cg.generate_starting_character("Glenny", start_tutorial=False)

        unit_strain_cap = mechanics.get_max_unit_strain(glenny)
        self.assertEqual(unit_strain_cap, 4, f"Glenny Unit Strain Cap must be 4, got {unit_strain_cap}")

        bio_tolerance_pool = mechanics.get_max_graft_strain(glenny)
        self.assertEqual(bio_tolerance_pool, 35, f"Glenny Bio-Tolerance Pool must be 35, got {bio_tolerance_pool}")

    def test_04_glenny_four_armed_slots_and_graft_anatomy(self):
        """Glenny has all 4 hand slots in equipped and all 9 graft slots in graft system."""
        glenny = cg.generate_starting_character("Glenny", start_tutorial=False)

        eq = glenny.get("equipped", {})
        self.assertIn("main_hand", eq)
        self.assertIn("off_hand", eq)
        self.assertIn("lower_main_hand", eq)
        self.assertIn("lower_off_hand", eq)
        self.assertEqual(eq["main_hand"], "Recurve Hunting Bow")
        self.assertEqual(eq["off_hand"], "[2H Grip: Recurve Hunting Bow]")
        self.assertEqual(eq["lower_main_hand"], "Chipped Wood-Axe")
        self.assertEqual(eq["lower_off_hand"], "None")

        grafts = glenny.get("grafts", {})
        expected_graft_slots = {
            "head", "torso", "left_arm", "right_arm",
            "lower_left_arm", "lower_right_arm", "legs", "spine", "tail"
        }
        self.assertTrue(expected_graft_slots.issubset(set(grafts.keys())), f"Missing graft slots: {set(grafts.keys())}")

    def test_05_glenny_zero_pollution_from_desk_bound(self):
        """Glenny has zero lifestyle pollution, no desk_bound feats, and no desk_bound skills."""
        glenny = cg.generate_starting_character("Glenny", start_tutorial=False)

        self.assertIsNone(glenny.get("lifestyle"), "Glenny lifestyle must be None")
        self.assertIsNone(glenny.get("lifestyle_key"), "Glenny lifestyle_key must be None")
        self.assertIsNone(glenny.get("lifestyle_title"), "Glenny lifestyle_title must be None")

        desk_bound_data = PRESET_LIFESTYLES.get("desk_bound", {})
        desk_feat = desk_bound_data.get("starting_feat", "Sedentary Metabolism")
        desk_skills = set(desk_bound_data.get("skill_bonuses", {}).keys())

        # No desk bound feat in player feats or spells
        all_talents = glenny.get("feats", []) + glenny.get("spells", [])
        for talent in all_talents:
            self.assertNotIn(desk_feat, talent, f"Glenny polluted with desk_bound feat: {talent}")
            self.assertNotIn("Desk-Bound", talent, f"Glenny polluted with desk-bound talent: {talent}")
            self.assertNotIn("Sedentary", talent, f"Glenny polluted with sedentary talent: {talent}")

        # Desk bound skills must NOT be present unless in hunter_tracker background
        glenny_skills = set(glenny.get("skills", {}).keys())
        for d_sk in desk_skills:
            if d_sk not in ("Field Trapping", "Cartography", "Tactical Reflexes", "Wilderness Survival"):
                self.assertNotIn(d_sk, glenny_skills, f"Glenny polluted with desk_bound skill: {d_sk}")

    def test_06_glenny_name_case_insensitivity_and_whitespace(self):
        """Name casing variations ('glenny', '  GLENNY  ') trigger identical isolation."""
        for variant in ["glenny", "GLENNY", "  Glenny  ", "  glenny\t"]:
            char = cg.generate_starting_character(variant, start_tutorial=False)
            self.assertIsNone(char.get("lifestyle"), f"Failed isolation for variant '{variant}'")
            self.assertEqual(char["stats"]["STR"], 18)
            self.assertEqual(mechanics.calculate_ac(char), 14)
            self.assertEqual(mechanics.get_max_unit_strain(char), 4)

    def test_07_glenny_explicit_lifestyle_override(self):
        """Explicitly requesting a non-default lifestyle for Glenny applies lifestyle talents."""
        glenny_woodsman = cg.generate_starting_character("Glenny", lifestyle_key="woodsman", start_tutorial=False)
        self.assertEqual(glenny_woodsman.get("lifestyle"), "woodsman")
        self.assertEqual(glenny_woodsman["stats"]["STR"], 18)  # Glenny point alloc takes precedence
        self.assertIn("Field Trapping", glenny_woodsman["skills"])
        self.assertTrue(any("Nature's Camouflage" in f for f in glenny_woodsman.get("feats", [])))


class TestBackwardCompatibilityAndParameters(unittest.TestCase):
    """
    Stress test backward compatibility across invocation styles, positional arguments,
    fallback handling, and SkillEntry hybrid behavior.
    """

    def test_01_default_hero_generation(self):
        """Default call with zero arguments generates valid default 'Survivor' hero with desk_bound lifestyle."""
        hero = cg.generate_starting_character()
        self.assertEqual(hero["name"], "Survivor")
        self.assertEqual(hero.get("lifestyle"), "desk_bound")
        self.assertIsNotNone(hero.get("lifestyle_title"))
        self.assertIn("stats", hero)
        self.assertIn("skills", hero)
        self.assertIn("feats", hero)
        self.assertGreater(hero["max_hp"], 0)

    def test_02_positional_arguments_matrix(self):
        """Verify backward compatibility across positional argument orders."""
        # 1. name only
        c1 = cg.generate_starting_character("Vanguard")
        self.assertEqual(c1["name"], "Vanguard")
        self.assertEqual(c1.get("lifestyle"), "desk_bound")

        # 2. name + custom point_alloc (overrides lifestyle point allocation)
        custom_pts = {"STR": 8, "DEX": 4, "CON": 4, "INT": 2, "WIS": 1, "CHA": 1}
        c2 = cg.generate_starting_character("Brawn", custom_pts)
        self.assertEqual(c2["stats"]["STR"], 10 + 8 + 1)  # 10 base + 8 alloc + 1 Human mod = 19
        self.assertEqual(c2.get("lifestyle"), "desk_bound")  # Still receives lifestyle talents
        self.assertIn("Algorithmic Decryption", c2["skills"])

        # 3. name + point_alloc + background_key
        c3 = cg.generate_starting_character("Scout", None, "athlete")
        self.assertEqual(c3["name"], "Scout")
        self.assertEqual(c3.get("lifestyle"), "desk_bound")

        # 4. name + point_alloc + background_key + race_key
        c4 = cg.generate_starting_character("ElfHero", None, "adaptive", "aether_elf")
        self.assertEqual(c4["race"], "Aether-Touched Elf")

        # 5. name + point_alloc + background_key + race_key + class_key
        c5 = cg.generate_starting_character("MageHero", None, "adaptive", "human", "mage")
        self.assertEqual(c5["class"], "Mage (Aether-Weaver)")

        # 6. name + point_alloc + background_key + race_key + class_key + relic_key
        c6 = cg.generate_starting_character("RelicHero", None, "adaptive", "human", "warrior", "pocket_watch")
        self.assertEqual(c6["equipped"]["accessory"], "Heirloom Pocket-Watch")

    def test_03_unknown_and_malformed_lifestyle_keys(self):
        """Generator handles unknown, empty, None, and bad-typed lifestyle keys gracefully."""
        bad_keys = ["bogus_nonexistent_archetype", "", "   ", None, 999, [], {}]
        for bad_key in bad_keys:
            char = cg.generate_starting_character("FallbackHero", lifestyle_key=bad_key, start_tutorial=False)
            self.assertIsNotNone(char)
            self.assertEqual(char["name"], "FallbackHero")
            # Default fallback points: STR:4, DEX:4, CON:4, INT:4, WIS:2, CHA:2 (+1 Human racial mod)
            self.assertEqual(char["stats"]["STR"], 15)
            self.assertEqual(char["stats"]["DEX"], 15)
            self.assertEqual(char["stats"]["CON"], 15)
            self.assertEqual(char["stats"]["INT"], 15)
            self.assertEqual(char["stats"]["WIS"], 13)
            self.assertEqual(char["stats"]["CHA"], 13)

    def test_04_skill_entry_hybrid_comparison_oracle(self):
        """SkillEntry hybrid behaves both as dictionary and as numeric comparator against int/float."""
        entry = SkillEntry({
            "mastery": 20,
            "tier": "Novice",
            "description": "Test skill.",
            "milestones_unlocked": []
        })

        # Numeric comparisons
        self.assertTrue(entry >= 20)
        self.assertTrue(entry >= 15)
        self.assertFalse(entry >= 25)
        self.assertTrue(entry > 10)
        self.assertFalse(entry > 20)
        self.assertTrue(entry <= 20)
        self.assertTrue(entry <= 50)
        self.assertFalse(entry <= 10)
        self.assertTrue(entry < 25)
        self.assertFalse(entry < 20)
        self.assertTrue(entry == 20)
        self.assertFalse(entry == 30)
        self.assertTrue(entry != 30)
        self.assertFalse(entry != 20)

        # Reflected / reverse comparisons
        self.assertTrue(15 <= entry)
        self.assertTrue(20 <= entry)
        self.assertFalse(25 <= entry)
        self.assertTrue(10 < entry)
        self.assertTrue(25 > entry)
        self.assertTrue(20 == entry)

        # Typecasting
        self.assertEqual(int(entry), 20)
        self.assertEqual(float(entry), 20.0)

        # Dictionary operations
        self.assertEqual(entry["mastery"], 20)
        self.assertEqual(entry.get("tier"), "Novice")
        entry["mastery"] += 15
        self.assertEqual(entry["mastery"], 35)
        self.assertTrue(entry >= 35)

        # JSON serialization
        serialized = json.dumps(entry)
        deserialized = json.loads(serialized)
        self.assertEqual(deserialized["mastery"], 35)
        self.assertEqual(deserialized["tier"], "Novice")


class TestDatabasePersistenceAll26Lifestyles(unittest.TestCase):
    """
    Exhaustive database persistence stress test:
    Verify serializing, persisting, and deserializing characters created with
    each of the 26 lifestyles through SQLAlchemy models and repositories.
    """

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sao_test_db_m1_")
        self.db_path = os.path.join(self.temp_dir, "lifestyle_matrix.db")
        self.engine = get_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_lifestyle_catalog_has_all_26_valid_presets(self):
        """Verify catalog contains exactly 26 presets, all strictly balanced to 20 points with 2 skills and feats."""
        self.assertEqual(len(PRESET_LIFESTYLES), 26, f"Expected 26 presets, got {len(PRESET_LIFESTYLES)}")

        required_new = [
            "woodsman", "monastery_ascetic", "hearth_apothecary", "dungeon_delver",
            "arena_gladiator", "courtier_emissary", "blacksmith_apprentice", "archive_scribe"
        ]
        for k in required_new:
            self.assertIn(k, PRESET_LIFESTYLES, f"Missing required new lifestyle preset: {k}")

        for ls_key, ls_data in PRESET_LIFESTYLES.items():
            pts = ls_data.get("points", {})
            self.assertEqual(sum(pts.values()), 20, f"Preset '{ls_key}' does not sum to 20 points: {pts}")
            sk_bonuses = ls_data.get("skill_bonuses", {})
            self.assertEqual(len(sk_bonuses), 2, f"Preset '{ls_key}' must have exactly 2 skills: {sk_bonuses}")
            for sk, b in sk_bonuses.items():
                self.assertGreaterEqual(b, 10, f"Preset '{ls_key}' skill {sk} bonus {b} < 10")
                self.assertLessEqual(b, 20, f"Preset '{ls_key}' skill {sk} bonus {b} > 20")
            self.assertTrue(ls_data.get("starting_feat"), f"Preset '{ls_key}' missing starting_feat")

    def test_02_persist_and_hydrate_all_26_lifestyles_round_trip(self):
        """
        Exhaustive relational persistence test across all 26 lifestyles:
        Generate character -> Save via CharacterRepository -> Load via CharacterRepository -> Verify parity.
        """
        for ls_key, ls_data in PRESET_LIFESTYLES.items():
            session_id = f"sess_{ls_key}"
            char_name = f"Vanguard_{ls_key}"

            # 1. Generate starting character
            char = cg.generate_starting_character(
                name=char_name,
                lifestyle_key=ls_key,
                start_tutorial=False
            )
            self.assertEqual(char["lifestyle"], ls_key)
            self.assertEqual(char["lifestyle_key"], ls_key)
            self.assertEqual(char["lifestyle_title"], ls_data["title"])

            # 2. Save character to database
            with db_transaction(engine=self.engine) as session:
                rec = CharacterRepository.save_character(session, char, session_id=session_id)
                self.assertIsNotNone(rec.id, f"Save failed for lifestyle '{ls_key}'")

            # 3. Hydrate character from database
            with db_transaction(engine=self.engine) as session:
                loaded = CharacterRepository.load_character(session, char_name.lower(), session_id=session_id)
                self.assertIsNotNone(loaded, f"Load returned None for lifestyle '{ls_key}'")

                # Verify lifestyle metadata
                self.assertEqual(loaded.get("lifestyle"), ls_key, f"Loaded lifestyle mismatch for {ls_key}")
                self.assertEqual(loaded.get("lifestyle_key"), ls_key, f"Loaded lifestyle_key mismatch for {ls_key}")
                self.assertEqual(loaded.get("lifestyle_title"), ls_data["title"], f"Loaded title mismatch for {ls_key}")

                # Verify core attributes parity
                self.assertEqual(loaded["stats"], char["stats"], f"Stats mismatch after hydration for {ls_key}")

                # Verify skills parity
                for sk_name, sk_bonus in ls_data["skill_bonuses"].items():
                    self.assertIn(sk_name, loaded["skills"], f"Skill '{sk_name}' missing after DB load for {ls_key}")
                    loaded_m = loaded["skills"][sk_name]["mastery"] if isinstance(loaded["skills"][sk_name], dict) else loaded["skills"][sk_name]
                    char_m = char["skills"][sk_name]["mastery"] if isinstance(char["skills"][sk_name], dict) else char["skills"][sk_name]
                    self.assertEqual(loaded_m, char_m, f"Skill mastery mismatch for '{sk_name}' in {ls_key}")

                # Verify starting feat/spell parity
                expected_feat = ls_data["starting_feat"]
                all_loaded_talents = loaded.get("feats", []) + loaded.get("spells", [])
                feat_present = any(expected_feat in t for t in all_loaded_talents)
                self.assertTrue(feat_present, f"Feat '{expected_feat}' not found in loaded talents for {ls_key}: {all_loaded_talents}")

                # 4. Verify update mutation survival
                loaded["hp"] = max(1, loaded["hp"] - 25)
                loaded["col"] = loaded["col"] + 500
                CharacterRepository.save_character(session, loaded, session_id=session_id)

            # 5. Reload after update mutation and verify persistence integrity
            with db_transaction(engine=self.engine) as session:
                reloaded = CharacterRepository.load_character(session, char_name.lower(), session_id=session_id)
                self.assertEqual(reloaded["col"], char["col"] + 500)
                self.assertEqual(reloaded.get("lifestyle"), ls_key)
                self.assertEqual(reloaded["stats"], char["stats"])

    def test_03_glenny_database_persistence_round_trip(self):
        """Glenny saved to DB and loaded back retains AC 14/16, Strain Cap 4, and zero desk_bound pollution."""
        glenny = cg.generate_starting_character("Glenny", start_tutorial=False)

        with db_transaction(engine=self.engine) as session:
            CharacterRepository.save_character(session, glenny, session_id="glenny_persistence_sess")

        with db_transaction(engine=self.engine) as session:
            loaded = CharacterRepository.load_character(session, "glenny", session_id="glenny_persistence_sess")
            self.assertIsNotNone(loaded)

            # Zero lifestyle pollution
            self.assertIsNone(loaded.get("lifestyle"))
            self.assertIsNone(loaded.get("lifestyle_key"))
            self.assertIsNone(loaded.get("lifestyle_title"))

            # Stats match canonical Glenny
            self.assertEqual(loaded["stats"], {"STR": 18, "DEX": 15, "CON": 16, "INT": 11, "WIS": 13, "CHA": 9})

            # AC calculation
            self.assertEqual(mechanics.calculate_ac(loaded), 14)
            loaded_shield = copy.deepcopy(loaded)
            loaded_shield["equipped"]["lower_off_hand"] = "Wooden Buckler"
            self.assertEqual(mechanics.calculate_ac(loaded_shield), 16)

            # Unit Strain Cap
            self.assertEqual(mechanics.get_max_unit_strain(loaded), 4)

            # 4-armed equipment slots
            eq = loaded["equipped"]
            self.assertEqual(eq["main_hand"], "Recurve Hunting Bow")
            self.assertEqual(eq["off_hand"], "[2H Grip: Recurve Hunting Bow]")
            self.assertEqual(eq["lower_main_hand"], "Chipped Wood-Axe")
            self.assertEqual(eq["lower_off_hand"], "None")

    def test_04_session_isolation_same_slug_distinct_lifestyles(self):
        """Two characters with the same slug created in different sessions with different lifestyles remain strictly isolated."""
        c_woodsman = cg.generate_starting_character("SameSlug", lifestyle_key="woodsman", start_tutorial=False)
        c_gladiator = cg.generate_starting_character("SameSlug", lifestyle_key="arena_gladiator", start_tutorial=False)

        with db_transaction(engine=self.engine) as s:
            CharacterRepository.save_character(s, c_woodsman, session_id="session_forest")
            CharacterRepository.save_character(s, c_gladiator, session_id="session_arena")

        with db_transaction(engine=self.engine) as s:
            loaded_forest = CharacterRepository.load_character(s, "sameslug", session_id="session_forest")
            loaded_arena = CharacterRepository.load_character(s, "sameslug", session_id="session_arena")

            self.assertEqual(loaded_forest.get("lifestyle"), "woodsman")
            self.assertEqual(loaded_arena.get("lifestyle"), "arena_gladiator")
            self.assertNotEqual(loaded_forest["stats"], loaded_arena["stats"])
            self.assertIn("Field Trapping", loaded_forest["skills"])
            self.assertIn("Trench Hammers", loaded_arena["skills"])


if __name__ == "__main__":
    unittest.main()
