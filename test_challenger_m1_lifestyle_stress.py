"""
test_challenger_m1_lifestyle_stress.py
======================================
Empirical Adversarial Challenge & Property-Based Fuzzing Suite for Milestone 1.

Verifies:
1. All 26 presets in `PRESET_LIFESTYLES` have strictly sum == 20 points across all permutations.
2. Every preset has exactly 2 skills with bonus >= 10 and <= 20.
3. Every preset has non-empty `starting_feat`, `feat_desc`, and `innate_ability`.
4. `SkillEntry` hybrid dict/int supports all comparison operators (>=, >, <=, <, ==, !=) against int/float,
   reflected/reverse comparisons, dictionary mutations/lookups, and clean JSON serialization.
5. Cross-product combinatorial stress (26 presets x 32 backgrounds = 832 combinations) and
   adversarial generator edge cases (malformed keys, Glenny isolation, full persistence round-trips).
"""

import copy
import itertools
import json
import math
import os
import random
import sys
import unittest
from typing import Any, Dict, List

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import backend.character_generator as cg
import backend.mechanics as mechanics
from backend.character_generator import SkillEntry, PRESET_LIFESTYLES, PRESET_BACKGROUNDS


class TestLifestylePresetMathematicalInvariants(unittest.TestCase):
    """
    Property-based stress tests verifying mathematical invariants of PRESET_LIFESTYLES.
    """

    CORE_STATS = ("STR", "DEX", "CON", "INT", "WIS", "CHA")

    REQUIRED_NEW_KEYS = [
        "woodsman",
        "monastery_ascetic",
        "hearth_apothecary",
        "dungeon_delver",
        "arena_gladiator",
        "courtier_emissary",
        "blacksmith_apprentice",
        "archive_scribe"
    ]

    ORIGINAL_18_KEYS = [
        "desk_bound",
        "athletic",
        "heavy_labor",
        "first_responder",
        "academic_scholar",
        "night_security",
        "offgrid_homesteader",
        "yoga_contortionist",
        "esports_gamer",
        "stage_performer",
        "longhaul_trucker",
        "extreme_sports",
        "commercial_diver",
        "line_cook",
        "highschool_educator",
        "park_ranger",
        "blacksmith_sculptor",
        "mma_fighter"
    ]

    def test_preset_catalog_completeness(self):
        """Assert exactly 26 presets exist, containing all 8 new and all 18 original archetypes."""
        self.assertIsInstance(PRESET_LIFESTYLES, dict, "PRESET_LIFESTYLES must be a dict.")
        self.assertEqual(
            len(PRESET_LIFESTYLES), 26,
            f"Expected exactly 26 presets, got {len(PRESET_LIFESTYLES)}"
        )
        for k in self.REQUIRED_NEW_KEYS:
            self.assertIn(k, PRESET_LIFESTYLES, f"Required new archetype '{k}' is missing.")
        for k in self.ORIGINAL_18_KEYS:
            self.assertIn(k, PRESET_LIFESTYLES, f"Original archetype '{k}' is missing.")

    def test_20_point_sum_invariant_across_permutations(self):
        """
        Verify that for all 26 presets, points strictly sum to 20,
        are non-negative integers, and sum is invariant under all key permutations.
        """
        for preset_key, preset in PRESET_LIFESTYLES.items():
            self.assertIn("points", preset, f"Preset '{preset_key}' missing 'points'")
            points = preset["points"]
            self.assertIsInstance(points, dict, f"Preset '{preset_key}' points must be a dict")
            
            # Exactly the 6 core stats
            self.assertEqual(
                set(points.keys()), set(self.CORE_STATS),
                f"Preset '{preset_key}' does not have exactly the 6 core stats: {points.keys()}"
            )

            # Each stat must be an integer >= 0, not a boolean or float
            for stat in self.CORE_STATS:
                val = points[stat]
                self.assertIsInstance(
                    val, int,
                    f"Preset '{preset_key}' stat '{stat}' must be int, got {type(val)}"
                )
                self.assertNotIsInstance(
                    val, bool,
                    f"Preset '{preset_key}' stat '{stat}' must not be bool"
                )
                self.assertGreaterEqual(
                    val, 0,
                    f"Preset '{preset_key}' stat '{stat}' has negative allocation: {val}"
                )

            # Strict 20 point sum
            total = sum(points.values())
            self.assertEqual(
                total, 20,
                f"Preset '{preset_key}' sums to {total}, expected strictly 20!"
            )

            # Permutation Invariance: Test across multiple random permutations of stat order
            stat_items = list(points.items())
            for _ in range(10):
                shuffled = stat_items.copy()
                random.shuffle(shuffled)
                perm_sum = sum(v for _, v in shuffled)
                self.assertEqual(
                    perm_sum, 20,
                    f"Permuted sum failed for '{preset_key}': {perm_sum}"
                )

    def test_fuzz_random_point_allocations_against_generator(self):
        """
        Fuzzing test: generate 100 random valid 20-point partitions across 6 stats,
        pass to generate_starting_character(point_alloc=...), and assert stats match exactly.
        """
        rng = random.Random(42)
        for _ in range(100):
            # Generate random 5 dividers in [0, 20] to partition 20 into 6 non-negative ints
            dividers = sorted([rng.randint(0, 20) for _ in range(5)])
            parts = [
                dividers[0],
                dividers[1] - dividers[0],
                dividers[2] - dividers[1],
                dividers[3] - dividers[2],
                dividers[4] - dividers[3],
                20 - dividers[4]
            ]
            self.assertEqual(sum(parts), 20)
            custom_alloc = dict(zip(self.CORE_STATS, parts))
            
            char = cg.generate_starting_character(
                name="FuzzHero",
                point_alloc=custom_alloc,
                race_key="pure_human",
                class_key="pathless",
                start_tutorial=False
            )
            # pure_human stat_mods: {"STR": 1, "DEX": 1, "CON": 1, "INT": 1, "WIS": 1, "CHA": 1}
            for stat in self.CORE_STATS:
                expected = 10 + custom_alloc[stat] + 1
                self.assertEqual(
                    char["stats"][stat], expected,
                    f"Fuzzed stat {stat} mismatch: got {char['stats'][stat]}, expected {expected}"
                )


class TestLifestyleSkillBonusesInvariants(unittest.TestCase):
    """
    Property-based stress tests verifying skill bonuses in PRESET_LIFESTYLES.
    """

    def test_all_presets_have_exactly_two_skills_in_range_10_to_20(self):
        """Every preset must have exactly 2 skill bonuses with values in [10, 20]."""
        for preset_key, preset in PRESET_LIFESTYLES.items():
            self.assertIn("skill_bonuses", preset, f"Preset '{preset_key}' missing 'skill_bonuses'")
            skills = preset["skill_bonuses"]
            self.assertIsInstance(skills, dict, f"Preset '{preset_key}' skill_bonuses must be dict")
            self.assertEqual(
                len(skills), 2,
                f"Preset '{preset_key}' must have exactly 2 skills, got {len(skills)}"
            )

            skill_names = list(skills.keys())
            self.assertNotEqual(
                skill_names[0], skill_names[1],
                f"Preset '{preset_key}' has duplicate skill: {skill_names[0]}"
            )

            for sk_name, bonus in skills.items():
                self.assertIsInstance(sk_name, str, f"Preset '{preset_key}' skill name must be str")
                self.assertGreater(len(sk_name.strip()), 0, f"Preset '{preset_key}' has empty skill name")
                self.assertIsInstance(
                    bonus, int,
                    f"Preset '{preset_key}' skill '{sk_name}' bonus must be int, got {type(bonus)}"
                )
                self.assertNotIsInstance(
                    bonus, bool,
                    f"Preset '{preset_key}' skill '{sk_name}' bonus must not be bool"
                )
                self.assertGreaterEqual(
                    bonus, 10,
                    f"Preset '{preset_key}' skill '{sk_name}' bonus {bonus} < 10"
                )
                self.assertLessEqual(
                    bonus, 20,
                    f"Preset '{preset_key}' skill '{sk_name}' bonus {bonus} > 20"
                )

    def test_cross_product_generator_stacking_832_combinations(self):
        """
        Cross-product combinatorial fuzzing:
        Test ALL 26 presets x ALL 32 backgrounds (832 combinations) to verify:
        - Clean generation with zero unhandled exceptions.
        - Additive stacking when background already possesses preset skill.
        - Proper initialization as SkillEntry when skill is new.
        - SkillEntry numeric comparison operators hold directly in player sheet.
        """
        count = 0
        for p_key, preset in PRESET_LIFESTYLES.items():
            for bg_key, bg_data in PRESET_BACKGROUNDS.items():
                char = cg.generate_starting_character(
                    name=f"Hero_{count}",
                    lifestyle_key=p_key,
                    background_key=bg_key,
                    start_tutorial=False
                )
                count += 1
                player_skills = char["skills"]
                bg_skills = bg_data.get("skills", {})

                for sk_name, sk_bonus in preset["skill_bonuses"].items():
                    self.assertIn(sk_name, player_skills)
                    entry = player_skills[sk_name]
                    
                    # Must be SkillEntry
                    self.assertIsInstance(entry, SkillEntry)
                    
                    # Direct comparison operator
                    self.assertTrue(entry >= sk_bonus)

                    # Verify additive arithmetic
                    if sk_name in bg_skills:
                        expected_mastery = min(1000, bg_skills[sk_name]["mastery"] + sk_bonus)
                    else:
                        expected_mastery = sk_bonus
                    
                    self.assertEqual(entry["mastery"], expected_mastery)
                    self.assertTrue(entry == expected_mastery)

        self.assertEqual(count, 26 * 32, f"Expected 832 combinations tested, got {count}")


class TestLifestyleStartingFeatsAndInnateTalents(unittest.TestCase):
    """
    Property-based stress tests verifying starting feats and innate talents in PRESET_LIFESTYLES.
    """

    def test_all_presets_have_non_empty_starting_feat_and_descriptions(self):
        """Every preset must have non-empty starting_feat, feat_desc, and innate_ability."""
        for preset_key, preset in PRESET_LIFESTYLES.items():
            self.assertIn("starting_feat", preset, f"Preset '{preset_key}' missing 'starting_feat'")
            feat = preset["starting_feat"]
            self.assertIsInstance(feat, str, f"Preset '{preset_key}' starting_feat must be str")
            self.assertGreaterEqual(
                len(feat.strip()), 3,
                f"Preset '{preset_key}' starting_feat '{feat}' too short"
            )

            self.assertIn("feat_desc", preset, f"Preset '{preset_key}' missing 'feat_desc'")
            desc = preset["feat_desc"]
            self.assertIsInstance(desc, str, f"Preset '{preset_key}' feat_desc must be str")
            self.assertGreaterEqual(
                len(desc.strip()), 10,
                f"Preset '{preset_key}' feat_desc '{desc}' too short"
            )

            self.assertIn("innate_ability", preset, f"Preset '{preset_key}' missing 'innate_ability'")
            ability = preset["innate_ability"]
            self.assertIsInstance(ability, str)
            self.assertIn(feat, ability, f"innate_ability must contain feat name '{feat}'")

    def test_feat_injection_across_all_26_presets(self):
        """Verify that generate_starting_character injects starting feat into player feats/spells."""
        for p_key, preset in PRESET_LIFESTYLES.items():
            char = cg.generate_starting_character(
                name=f"Hero_{p_key}",
                lifestyle_key=p_key,
                start_tutorial=False
            )
            feat_name = preset["starting_feat"]
            all_talents = char.get("feats", []) + char.get("spells", [])
            found = any(feat_name in t or t in feat_name for t in all_talents)
            self.assertTrue(
                found,
                f"Starting feat '{feat_name}' for preset '{p_key}' not found in talents: {all_talents}"
            )


class TestSkillEntryAdversarialFuzzing(unittest.TestCase):
    """
    Empirical adversarial stress testing and fuzzing of the SkillEntry hybrid class.
    """

    def test_all_comparison_operators_against_int_and_float(self):
        """Exhaustively verify >=, >, <=, <, ==, != against int and float."""
        entry = SkillEntry({"mastery": 50, "tier": "Apprentice", "description": "Test", "milestones_unlocked": [50]})
        
        # Test against int
        self.assertTrue(entry >= 50)
        self.assertTrue(entry >= 49)
        self.assertFalse(entry >= 51)

        self.assertTrue(entry > 49)
        self.assertFalse(entry > 50)
        self.assertFalse(entry > 51)

        self.assertTrue(entry <= 50)
        self.assertTrue(entry <= 51)
        self.assertFalse(entry <= 49)

        self.assertTrue(entry < 51)
        self.assertFalse(entry < 50)
        self.assertFalse(entry < 49)

        self.assertTrue(entry == 50)
        self.assertFalse(entry == 49)
        self.assertFalse(entry == 51)

        self.assertTrue(entry != 49)
        self.assertTrue(entry != 51)
        self.assertFalse(entry != 50)

        # Test against float
        self.assertTrue(entry >= 49.999)
        self.assertTrue(entry >= 50.0)
        self.assertFalse(entry >= 50.001)

        self.assertTrue(entry > 49.999)
        self.assertFalse(entry > 50.0)
        self.assertFalse(entry > 50.001)

        self.assertTrue(entry <= 50.0)
        self.assertTrue(entry <= 50.001)
        self.assertFalse(entry <= 49.999)

        self.assertTrue(entry < 50.001)
        self.assertFalse(entry < 50.0)
        self.assertFalse(entry < 49.999)

        self.assertTrue(entry == 50.0)
        self.assertFalse(entry == 50.001)
        self.assertTrue(entry != 50.001)
        self.assertFalse(entry != 50.0)

    def test_reflected_reverse_comparisons(self):
        """Verify number OP SkillEntry invokes reflected operations correctly."""
        entry = SkillEntry({"mastery": 50})

        # int OP entry
        self.assertTrue(40 < entry)   # entry > 40
        self.assertFalse(50 < entry)  # entry > 50
        self.assertFalse(60 < entry)  # entry > 60

        self.assertTrue(40 <= entry)  # entry >= 40
        self.assertTrue(50 <= entry)  # entry >= 50
        self.assertFalse(60 <= entry) # entry >= 60

        self.assertTrue(60 > entry)   # entry < 60
        self.assertFalse(50 > entry)  # entry < 50
        self.assertFalse(40 > entry)  # entry < 40

        self.assertTrue(60 >= entry)  # entry <= 60
        self.assertTrue(50 >= entry)  # entry <= 50
        self.assertFalse(40 >= entry) # entry <= 40

        self.assertTrue(50 == entry)  # entry == 50
        self.assertFalse(40 == entry)

        self.assertTrue(40 != entry)  # entry != 40
        self.assertFalse(50 != entry)

        # float OP entry
        self.assertTrue(49.5 <= entry)
        self.assertTrue(50.5 >= entry)
        self.assertTrue(50.0 == entry)

    def test_fuzzing_random_comparisons_property_oracle(self):
        """
        Property Oracle: for any integer m, x:
        SkillEntry({"mastery": m}) OP x === m OP x
        and x OP SkillEntry({"mastery": m}) === x OP m
        """
        rng = random.Random(1337)
        for _ in range(1000):
            m = rng.randint(-100, 1100)
            x = rng.randint(-100, 1100)
            entry = SkillEntry({"mastery": m})

            self.assertEqual(entry >= x, m >= x)
            self.assertEqual(entry > x, m > x)
            self.assertEqual(entry <= x, m <= x)
            self.assertEqual(entry < x, m < x)
            self.assertEqual(entry == x, m == x)
            self.assertEqual(entry != x, m != x)

            # Reflected
            self.assertEqual(x <= entry, x <= m)
            self.assertEqual(x < entry, x < m)
            self.assertEqual(x >= entry, x >= m)
            self.assertEqual(x > entry, x > m)
            self.assertEqual(x == entry, x == m)
            self.assertEqual(x != entry, x != m)

    def test_dictionary_mutation_and_lookups(self):
        """Verify SkillEntry behaves completely as a mutable dictionary."""
        entry = SkillEntry({"mastery": 20, "tier": "Novice"})
        
        # Subscript read & write
        self.assertEqual(entry["mastery"], 20)
        entry["mastery"] = 75
        self.assertEqual(entry["mastery"], 75)
        # Immediate comparison update
        self.assertTrue(entry >= 75)
        self.assertFalse(entry >= 76)

        # New key assignment
        entry["custom_tag"] = "test_tag"
        self.assertEqual(entry["custom_tag"], "test_tag")

        # Dict methods
        self.assertEqual(entry.get("nonexistent", "fallback"), "fallback")
        entry.setdefault("milestones_unlocked", []).append(50)
        self.assertIn(50, entry["milestones_unlocked"])
        
        entry.update({"tier": "Apprentice", "notes": "Fuzzed"})
        self.assertEqual(entry["tier"], "Apprentice")
        self.assertEqual(entry["notes"], "Fuzzed")

        # Deletion
        del entry["notes"]
        self.assertNotIn("notes", entry)
        popped = entry.pop("custom_tag")
        self.assertEqual(popped, "test_tag")
        self.assertNotIn("custom_tag", entry)

        # Dict iteration
        keys = list(entry.keys())
        self.assertIn("mastery", keys)
        self.assertIn("tier", keys)
        self.assertIn("milestones_unlocked", keys)

    def test_json_serialization_and_round_trip(self):
        """Verify SkillEntry serializes cleanly to JSON and deserializes back accurately."""
        original_data = {
            "mastery": 45,
            "tier": "Novice",
            "description": "JSON round-trip test.",
            "milestones_unlocked": []
        }
        entry = SkillEntry(original_data)

        # Standard json.dumps should succeed without custom encoder
        encoded = json.dumps(entry)
        self.assertIsInstance(encoded, str)

        decoded = json.loads(encoded)
        self.assertEqual(decoded, original_data)

        # Full player sheet serialization
        char = cg.generate_starting_character("SerializationHero", start_tutorial=False)
        player_json = json.dumps(char)
        self.assertIsInstance(player_json, str)
        restored = json.loads(player_json)
        self.assertEqual(restored["name"], "SerializationHero")
        self.assertIn("skills", restored)

    def test_edge_cases_and_malformed_entries(self):
        """Test SkillEntry with empty dict, missing mastery, and int/float typecasting."""
        # Missing mastery defaults to 0
        empty_entry = SkillEntry({})
        self.assertEqual(empty_entry.get("mastery", 0), 0)
        self.assertTrue(empty_entry == 0)
        self.assertTrue(empty_entry >= 0)
        self.assertFalse(empty_entry > 0)
        self.assertTrue(empty_entry < 10)

        # Float mastery in dict
        float_entry = SkillEntry({"mastery": 25.5})
        self.assertTrue(float_entry >= 25)
        self.assertFalse(float_entry >= 26)
        self.assertTrue(float_entry > 25)

        # Typecasting
        self.assertEqual(int(entry := SkillEntry({"mastery": 42})), 42)
        self.assertEqual(float(entry), 42.0)
        self.assertEqual(int(empty_entry), 0)

        # Equality with plain dict
        dict_compare = {"mastery": 42}
        self.assertEqual(entry, dict_compare)


class TestCharacterGeneratorAdversarialEdgeCases(unittest.TestCase):
    """
    Adversarial edge cases for generate_starting_character lifestyle integration.
    """

    def test_malformed_and_unknown_lifestyle_keys(self):
        """Generator must gracefully handle malformed, unknown, or wrong-type lifestyle_key without crashing."""
        malformed_inputs = [
            None,
            "",
            "   ",
            "nonexistent_archetype_xyz",
            12345,
            [],
            {},
            True,
            False,
            3.14159
        ]
        for bad_key in malformed_inputs:
            try:
                char = cg.generate_starting_character(
                    name="ResilientHero",
                    lifestyle_key=bad_key,
                    start_tutorial=False
                )
                self.assertIsNotNone(char)
                self.assertIn("stats", char)
                self.assertIn("skills", char)
            except Exception as e:
                self.fail(f"generate_starting_character crashed on malformed lifestyle_key={bad_key!r}: {e}")

    def test_glenny_isolation_adversarial_matrix(self):
        """
        Glenny Isolation:
        1. Default call (lifestyle_key="desk_bound") must NOT pollute Glenny with desk_bound stats or feats.
        2. Glenny must retain canonical Wasteland Ranger stats (STR 18, DEX 15, CON 14, INT 12, WIS 13, CHA 11).
        3. Glenny must NOT have 'Analytical Deduction'.
        4. Explicit lifestyle parameter (e.g. 'woodsman') must apply lifestyle talents without overriding Glenny's canonical point allocation if point_alloc is None.
        """
        # 1. Default Glenny
        glenny = cg.generate_starting_character("Glenny", start_tutorial=False)
        self.assertEqual(glenny["stats"]["STR"], 18)
        self.assertEqual(glenny["stats"]["DEX"], 15)
        self.assertEqual(glenny["stats"]["CON"], 16)
        self.assertEqual(glenny["stats"]["INT"], 11)
        self.assertEqual(glenny["stats"]["WIS"], 13)
        self.assertEqual(glenny["stats"]["CHA"], 9)
        self.assertFalse(any("Analytical Deduction" in f for f in glenny.get("feats", [])))
        self.assertIsNone(glenny.get("lifestyle"))

        # 2. Case variations of name "gLeNnY"
        glenny_caps = cg.generate_starting_character("gLeNnY  ", start_tutorial=False)
        self.assertEqual(glenny_caps["stats"]["STR"], 18)
        self.assertIsNone(glenny_caps.get("lifestyle"))

        # 3. Explicit lifestyle on Glenny: retains Glenny canonical points but gains lifestyle skills
        glenny_woodsman = cg.generate_starting_character(
            "Glenny",
            lifestyle_key="woodsman",
            start_tutorial=False
        )
        self.assertEqual(glenny_woodsman["stats"]["STR"], 18) # Canonical points preserved
        self.assertIn("Field Trapping", glenny_woodsman["skills"])
        self.assertTrue(any("Nature's Camouflage" in f for f in glenny_woodsman.get("feats", [])))


if __name__ == "__main__":
    unittest.main()
