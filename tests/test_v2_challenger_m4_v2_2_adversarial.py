"""
Adversarial Challenge Test Suite for Milestone 4 (R4):
Author: Milestone 4 Challenger 2 (Empirical Challenger)
Project Root: h:\\Antigravity\\SAO Sandbox v2

Verifies:
1. Multi-tier progression sequence and resource pool math:
   - Fuzz complete Level 1 -> 10 -> Tier 2 -> 20 -> Tier 3 -> 30 -> Tier 4 progression across all 10 classic base classes.
   - Verify resource pool math at every tier:
     * Tier 2: int(base * 1.25) (+25%)
     * Tier 3: int(prev * 1.50) (+50%)
     * Tier 4: int(prev * 2.00) (+100%)
   - Permutation testing across all 3 bespoke evolution choices at each tier.
   - HP growth step-by-step verification (ARCHETYPE_HP_GROWTH + CON modifier).
2. Backward compatibility stress:
   - Glenny 4-armed chimera (troll_kreen_chimera, ranger):
     * Quad-wielding / 4-hand equipment slots / 2H bow grip / quad-flurry drill execution
     * Max unit strain cap == 4
     * Unshielded AC == 14
     * Shielded AC == 16
     * HP == 135 / 135
   - Banki:
     * Character creation and sheet generation across warrior (HP 120), vanguard (HP 100), and fighter (HP 120).
     * normalize_class_key resolution to fighter for warrior and vanguard.
     * Combat resource type 'poise' and complete sheet schema integrity.
3. Fast execution benchmark:
   - Empirical performance benchmark of tests/test_v2_class_evolutions_r4.py strictly under 2.0s.
"""

import copy
import os
import subprocess
import sys
import time
import unittest

# Ensure project root in sys.path
_cur = os.path.dirname(os.path.abspath(__file__))
while _cur and not os.path.exists(os.path.join(_cur, "backend", "character_generator.py")):
    _parent = os.path.dirname(_cur)
    if _parent == _cur:
        break
    _cur = _parent
PROJECT_ROOT = _cur
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import backend.character_generator as cg
import backend.mechanics as mechanics


class TestMilestone4AdversarialChallenger2(unittest.TestCase):
    """Adversarial stress and property-based verification suite for Milestone 4."""

    CLASSIC_10 = [
        "fighter", "wizard", "rogue", "cleric", "ranger",
        "paladin", "druid", "bard", "barbarian", "monk"
    ]

    # =========================================================================
    # PART 1: Multi-Tier Progression Sequence & Resource Pool Math Fuzzing
    # =========================================================================

    def test_01_full_progression_sequence_all_10_classic_classes(self):
        """
        Fuzz complete Level 1 -> 10 -> Tier 2 -> 20 -> Tier 3 -> 30 -> Tier 4
        progression across all 10 classic base classes.
        Verifies:
        - HP growth step-by-step from Level 1 to 10 matches ARCHETYPE_HP_GROWTH + CON mod.
        - HP growth step-by-step from Level 10 to 30 matches get_archetype_hp_growth + CON mod.
        - Gating at Level 10, 20, 30 strictly enforces boss defeats and skill mastery.
        - Exactly 3 bespoke evolution choices at each tier.
        - Resource pool math:
            Tier 2: int(base * 1.25)
            Tier 3: int(prev * 1.50)
            Tier 4: int(prev * 2.00)
        - Current resource is set to new max resource on evolution.
        - Evolution master feats are accumulated in player['feats'].
        """
        hp_growth_table = getattr(mechanics, "ARCHETYPE_HP_GROWTH", {})

        for c_key in self.CLASSIC_10:
            with self.subTest(class_key=c_key):
                char = cg.generate_starting_character(
                    name=f"ProgHero_{c_key}",
                    class_key=c_key,
                    start_tutorial=False
                )
                player = char.get("player", char)
                self.assertEqual(player["level"], 1)
                self.assertEqual(player.get("class_tier", 1), 1)

                base_res = player["combat_resource"]["max"]
                con_mod = (player.get("stats", {}).get("CON", 10) - 10) // 2
                base_hp_step = hp_growth_table.get(
                    c_key,
                    hp_growth_table.get(mechanics.normalize_class_key(c_key), 25)
                )

                # --- PHASE 1: Level 1 -> 10 Progression ---
                for target_lvl in range(2, 11):
                    hp_before = player["max_hp"]
                    mechanics.apply_level_up(player)
                    self.assertEqual(player["level"], target_lvl)
                    gain = player["max_hp"] - hp_before
                    self.assertEqual(
                        gain, base_hp_step + con_mod,
                        f"Class {c_key} level {target_lvl} HP gain {gain} != expected {base_hp_step + con_mod}"
                    )

                self.assertEqual(player["level"], 10)

                # Level 10 gate check before boss
                gate_pre_t2 = mechanics.check_evolution_eligibility(player)
                self.assertFalse(
                    gate_pre_t2.get("eligible"),
                    f"Class {c_key} should NOT be eligible for Tier 2 before Spire Boss defeat."
                )

                # Fulfill Tier 2 prerequisites
                player["sector_boss_defeated"] = True
                player["bosses_defeated"] = ["The Gilded Spire Overlord (Sector 1)"]
                first_skill = list(player["skills"].keys())[0]
                player["skills"][first_skill] = 100

                gate_post_t2 = mechanics.check_evolution_eligibility(player)
                self.assertTrue(
                    gate_post_t2.get("eligible"),
                    f"Class {c_key} should be eligible for Tier 2 after satisfying requirements."
                )

                # Generate and verify Tier 2 choices
                t2_choices = mechanics.generate_curated_evolutions(player)
                self.assertEqual(
                    len(t2_choices), 3,
                    f"Class {c_key} Tier 2 must return exactly 3 choices, got {len(t2_choices)}"
                )
                for ch in t2_choices:
                    self.assertEqual(ch.get("tier"), 2)
                    self.assertIn("title", ch)
                    self.assertIn("category", ch)
                    self.assertIn("desc", ch)

                # Apply Tier 2 Evolution (Choice 0)
                chosen_t2 = t2_choices[0]
                mechanics.apply_class_evolution(player, chosen_t2)
                self.assertEqual(player["class"], chosen_t2["title"])
                self.assertEqual(player["class_tier"], 2)

                # Verify Tier 2 Resource Math: int(base * 1.25)
                expected_t2_res = int(base_res * 1.25)
                self.assertEqual(
                    player["combat_resource"]["max"], expected_t2_res,
                    f"Class {c_key} Tier 2 resource {player['combat_resource']['max']} != expected {expected_t2_res}"
                )
                self.assertEqual(player["combat_resource"]["current"], expected_t2_res)

                # --- PHASE 2: Level 10 -> 20 Progression ---
                for target_lvl in range(11, 21):
                    hp_before = player["max_hp"]
                    expected_gain = mechanics.get_archetype_hp_growth(player.get("class", "pathless")) + con_mod
                    mechanics.apply_level_up(player)
                    self.assertEqual(player["level"], target_lvl)
                    gain = player["max_hp"] - hp_before
                    self.assertEqual(gain, expected_gain)

                self.assertEqual(player["level"], 20)

                # Level 20 gate check before regional boss
                gate_pre_t3 = mechanics.check_evolution_eligibility(player)
                self.assertFalse(
                    gate_pre_t3.get("eligible"),
                    f"Class {c_key} should NOT be eligible for Tier 3 before Regional Boss defeat."
                )

                # Fulfill Tier 3 prerequisites
                player["regional_boss_defeated"] = True
                player["bosses_defeated"].append("Regional Apex Behemoth (Sector 5)")
                player["skills"][first_skill] = 350

                gate_post_t3 = mechanics.check_evolution_eligibility(player)
                self.assertTrue(
                    gate_post_t3.get("eligible"),
                    f"Class {c_key} should be eligible for Tier 3 after satisfying requirements."
                )

                # Generate and verify Tier 3 choices
                t3_choices = mechanics.generate_curated_evolutions(player)
                self.assertEqual(
                    len(t3_choices), 3,
                    f"Class {c_key} Tier 3 must return exactly 3 prestige branches, got {len(t3_choices)}"
                )
                for ch in t3_choices:
                    self.assertEqual(ch.get("tier"), 3)

                # Apply Tier 3 Evolution (Choice 0)
                chosen_t3 = t3_choices[0]
                mechanics.apply_class_evolution(player, chosen_t3)
                self.assertEqual(player["class"], chosen_t3["title"])
                self.assertEqual(player["class_tier"], 3)

                # Verify Tier 3 Resource Math: int(prev * 1.50)
                expected_t3_res = int(expected_t2_res * 1.50)
                self.assertEqual(
                    player["combat_resource"]["max"], expected_t3_res,
                    f"Class {c_key} Tier 3 resource {player['combat_resource']['max']} != expected {expected_t3_res}"
                )
                self.assertEqual(player["combat_resource"]["current"], expected_t3_res)

                # --- PHASE 3: Level 20 -> 30 Progression ---
                for target_lvl in range(21, 31):
                    hp_before = player["max_hp"]
                    expected_gain = mechanics.get_archetype_hp_growth(player.get("class", "pathless")) + con_mod
                    mechanics.apply_level_up(player)
                    self.assertEqual(player["level"], target_lvl)
                    gain = player["max_hp"] - hp_before
                    self.assertEqual(gain, expected_gain)

                self.assertEqual(player["level"], 30)

                # Level 30 gate check before planetary boss
                gate_pre_t4 = mechanics.check_evolution_eligibility(player)
                self.assertFalse(
                    gate_pre_t4.get("eligible"),
                    f"Class {c_key} should NOT be eligible for Tier 4 before Planetary Boss defeat."
                )

                # Fulfill Tier 4 prerequisites
                player["planetary_boss_defeated"] = True
                player["bosses_defeated"].append("Planetary World-Eater Core")
                player["skills"][first_skill] = 750

                gate_post_t4 = mechanics.check_evolution_eligibility(player)
                self.assertTrue(
                    gate_post_t4.get("eligible"),
                    f"Class {c_key} should be eligible for Tier 4 after satisfying requirements."
                )

                # Generate and verify Tier 4 choices
                t4_choices = mechanics.generate_curated_evolutions(player)
                self.assertEqual(
                    len(t4_choices), 3,
                    f"Class {c_key} Tier 4 must return exactly 3 apex choices, got {len(t4_choices)}"
                )
                for ch in t4_choices:
                    self.assertEqual(ch.get("tier"), 4)

                # Apply Tier 4 Evolution (Choice 0)
                chosen_t4 = t4_choices[0]
                mechanics.apply_class_evolution(player, chosen_t4)
                self.assertEqual(player["class"], chosen_t4["title"])
                self.assertEqual(player["class_tier"], 4)

                # Verify Tier 4 Resource Math: int(prev * 2.00)
                expected_t4_res = int(expected_t3_res * 2.00)
                self.assertEqual(
                    player["combat_resource"]["max"], expected_t4_res,
                    f"Class {c_key} Tier 4 resource {player['combat_resource']['max']} != expected {expected_t4_res}"
                )
                self.assertEqual(player["combat_resource"]["current"], expected_t4_res)

                # Feats verification: should contain all three evolution feats
                feats_str = " ".join(player.get("feats", []))
                self.assertIn(chosen_t2["title"], feats_str)
                self.assertIn(chosen_t3["title"], feats_str)
                self.assertIn(chosen_t4["title"], feats_str)

    def test_02_resource_pool_math_permutations_across_all_choice_branches(self):
        """
        Fuzz resource pool math across all 3 choices at each tier (Choice 0, Choice 1, Choice 2)
        to ensure any chosen branch reliably and consistently preserves resource scaling math:
            Tier 2: int(base * 1.25)
            Tier 3: int(prev * 1.50)
            Tier 4: int(prev * 2.00)
        """
        test_classes = ["wizard", "rogue", "monk", "fighter"]

        for c_key in test_classes:
            for branch_idx in range(3):
                with self.subTest(class_key=c_key, branch=branch_idx):
                    char = cg.generate_starting_character(
                        name=f"Branch_{c_key}_{branch_idx}",
                        class_key=c_key,
                        start_tutorial=False
                    )
                    player = char.get("player", char)
                    base_res = player["combat_resource"]["max"]

                    # Advance to Tier 2
                    player["level"] = 10
                    player["sector_boss_defeated"] = True
                    player["bosses_defeated"] = ["The Gilded Spire Overlord (Sector 1)"]
                    player["skills"]["Two-Handed Greataxes"] = 120

                    t2_choices = mechanics.generate_curated_evolutions(player)
                    self.assertEqual(len(t2_choices), 3)
                    t2_pick = t2_choices[branch_idx]
                    mechanics.apply_class_evolution(player, t2_pick)
                    exp_t2 = int(base_res * 1.25)
                    self.assertEqual(player["combat_resource"]["max"], exp_t2)

                    # Advance to Tier 3
                    player["level"] = 20
                    player["regional_boss_defeated"] = True
                    player["bosses_defeated"].append("Regional Apex Behemoth (Sector 5)")
                    player["skills"]["Two-Handed Greataxes"] = 380

                    t3_choices = mechanics.generate_curated_evolutions(player)
                    self.assertEqual(len(t3_choices), 3)
                    t3_pick = t3_choices[branch_idx]
                    mechanics.apply_class_evolution(player, t3_pick)
                    exp_t3 = int(exp_t2 * 1.50)
                    self.assertEqual(player["combat_resource"]["max"], exp_t3)

                    # Advance to Tier 4
                    player["level"] = 30
                    player["planetary_boss_defeated"] = True
                    player["bosses_defeated"].append("Planetary World-Eater Core")
                    player["skills"]["Two-Handed Greataxes"] = 800

                    t4_choices = mechanics.generate_curated_evolutions(player)
                    self.assertEqual(len(t4_choices), 3)
                    t4_pick = t4_choices[branch_idx]
                    mechanics.apply_class_evolution(player, t4_pick)
                    exp_t4 = int(exp_t3 * 2.00)
                    self.assertEqual(player["combat_resource"]["max"], exp_t4)

    # =========================================================================
    # PART 2: Backward Compatibility Stress (Glenny Chimera & Banki Frontliners)
    # =========================================================================

    def test_03_glenny_chimera_full_backward_compatibility(self):
        """
        Adversarially verify Glenny 4-armed chimera (troll_kreen_chimera, ranger):
        - 4-hand equipment slots (main_hand, off_hand, lower_main_hand, lower_off_hand)
        - 2H hunting bow grip binding in upper hands
        - Quad-wielding / 4-limb drill execution (quad_flurry, 4 attacks)
        - Max unit strain cap == 4 (3 base + 1 Secondary Ganglia)
        - Unshielded AC == 14
        - Shielded AC == 16 (equipping shield in lower_off_hand)
        - HP == 135 / 135 (100 base + 30 CON mod + 5 racial mod)
        - Class normalization resolves cleanly to 'ranger'
        """
        glenny = cg.generate_starting_character(name="Glenny", start_tutorial=False)
        p = glenny.get("player", glenny)

        # 1. Identity & Lineage
        self.assertEqual(p["race_key"], "troll_kreen_chimera")
        self.assertIn("Spliced Apex Chimera", p["race"])
        self.assertEqual(p["gender"], "Male")
        norm_class = mechanics.normalize_class_key(p.get("class", "ranger"))
        self.assertEqual(norm_class, "ranger")

        # 2. HP Verification: 135 / 135
        self.assertEqual(p["max_hp"], 135, f"Glenny max_hp must be 135, got {p['max_hp']}")
        self.assertEqual(p["hp"], 135, f"Glenny hp must be 135, got {p['hp']}")

        # 3. Multi-limb Equipment Slots & 2H Grip
        eq = p.get("equipped", {})
        self.assertIn("main_hand", eq)
        self.assertIn("off_hand", eq)
        self.assertIn("lower_main_hand", eq)
        self.assertIn("lower_off_hand", eq)
        self.assertEqual(eq["main_hand"], "Recurve Hunting Bow")
        self.assertEqual(eq["off_hand"], "[2H Grip: Recurve Hunting Bow]")
        self.assertEqual(eq["lower_main_hand"], "Chipped Wood-Axe")

        # 4. Anatomy Profile & Graft Slots
        anat = mechanics.get_limb_anatomy_profile(p)
        self.assertTrue(anat.get("is_four_armed"), "Glenny must be four-armed")
        self.assertEqual(anat.get("arm_count"), 4)
        self.assertEqual(anat.get("secondary_ganglia_strain_bonus"), 1)
        self.assertEqual(len(anat.get("graft_slot_keys", [])), 9)

        # 5. Strain Cap: exactly 4
        strain_cap = mechanics.get_max_unit_strain(p)
        self.assertEqual(strain_cap, 4, f"Glenny max unit strain cap must be 4, got {strain_cap}")

        # 6. Unshielded AC: exactly 14
        ac_unshielded = mechanics.calculate_ac(p)
        self.assertEqual(ac_unshielded, 14, f"Glenny unshielded AC must be 14, got {ac_unshielded}")

        # 7. Shielded AC: exactly 16
        p_shielded = copy.deepcopy(p)
        p_shielded["equipped"]["lower_off_hand"] = "Riot Shield"
        ac_shielded = mechanics.calculate_ac(p_shielded)
        self.assertEqual(ac_shielded, 16, f"Glenny shielded AC must be 16, got {ac_shielded}")

        # 8. Quad-Flurry Coordination Drill
        drill_res = mechanics.resolve_tutorial_multi_limb_drill(p)
        self.assertTrue(drill_res.get("success"))
        self.assertEqual(drill_res.get("drill_mode"), "quad_flurry")
        self.assertTrue(drill_res.get("is_four_armed"))
        self.assertEqual(drill_res.get("arm_count"), 4)
        self.assertEqual(len(drill_res.get("limb_attacks", [])), 4)

    def test_04_banki_frontliner_creation_across_warrior_vanguard_fighter(self):
        """
        Adversarially verify Banki character creation and sheet generation across:
        - 'warrior': base_hp 120, normalize_class_key -> 'fighter', starting HP 120 (zero alloc)
        - 'vanguard': base_hp 100, normalize_class_key -> 'fighter', starting HP 100 (zero alloc)
        - 'fighter': base_hp 120, normalize_class_key -> 'fighter', starting HP 120 (zero alloc)
        Verifies:
        - Sheet schema integrity (stats, skills, equipped, durability, feats, combat_resource).
        - Combat resource type == 'poise', max == 100.
        - Backward-compatible alias preservation.
        """
        zero_alloc = {"STR": 0, "DEX": 0, "CON": 0, "INT": 0, "WIS": 0, "CHA": 0}
        pure_human_race = cg.resolve_racial_lineage("pure_human")

        test_configs = [
            ("warrior", 120, "Warrior (Frontline Anchor)"),
            ("vanguard", 100, "Vanguard (Heavy Frontliner)"),
            ("fighter", 120, "Fighter (Martial Weaponmaster)"),
        ]

        for cls_k, expected_base_hp, expected_title in test_configs:
            with self.subTest(class_key=cls_k):
                # 1. Verify CLASS_PATHS configuration
                self.assertIn(cls_k, cg.CLASS_PATHS)
                c_info = cg.CLASS_PATHS[cls_k]
                self.assertEqual(c_info["base_hp"], expected_base_hp)
                self.assertEqual(c_info["title"], expected_title)

                # 2. Verify direct compute_starting_max_hp calibration with CON=10
                calc_hp = cg.compute_starting_max_hp(
                    pure_human_race,
                    c_info,
                    {"CON": 10},
                    {"age": 25, "height_in": 70, "weight_lbs": 185}
                )
                self.assertEqual(
                    calc_hp, expected_base_hp,
                    f"Direct compute_starting_max_hp for {cls_k} expected {expected_base_hp}, got {calc_hp}"
                )

                # 3. Generate starting character with zero point_alloc
                char = cg.generate_starting_character(
                    name="Banki",
                    class_key=cls_k,
                    point_alloc=zero_alloc,
                    lifestyle_key=None,
                    start_tutorial=False
                )
                p = char.get("player", char)

                # 4. Verify Sheet HP matches exactly
                self.assertEqual(p["name"], "Banki")
                self.assertEqual(p["max_hp"], expected_base_hp)
                self.assertEqual(p["hp"], expected_base_hp)

                # 5. Verify normalization maps alias cleanly to 'fighter'
                norm_key = mechanics.normalize_class_key(cls_k)
                self.assertEqual(norm_key, "fighter")

                # 6. Verify combat resource schema
                res = p.get("combat_resource", {})
                self.assertEqual(res.get("type"), "poise")
                self.assertEqual(res.get("max"), 100)
                self.assertEqual(res.get("current"), 0)

                # 7. Verify full character sheet fields
                required_fields = [
                    "name", "level", "hp", "max_hp", "combat_resource", "stats",
                    "skills", "spells", "feats", "inventory", "equipped",
                    "gear_durability", "location", "race", "race_key", "class"
                ]
                for f in required_fields:
                    self.assertIn(f, p, f"Banki {cls_k} character sheet missing required field '{f}'")

    # =========================================================================
    # PART 3: Performance & Fast Execution Benchmark
    # =========================================================================

    def test_05_benchmark_test_v2_class_evolutions_r4_under_2_seconds(self):
        """
        Executes tests/test_v2_class_evolutions_r4.py directly via subprocess
        and measures total runtime. Asserts execution strictly under 2.0 seconds.
        """
        test_file = os.path.join(PROJECT_ROOT, "tests", "test_v2_class_evolutions_r4.py")
        self.assertTrue(os.path.exists(test_file), f"Test file does not exist: {test_file}")

        # Run benchmark twice to measure warmed execution without cold interpreter penalty
        cmd = [sys.executable, "-m", "unittest", "tests/test_v2_class_evolutions_r4.py"]
        t0 = time.perf_counter()
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        elapsed = time.perf_counter() - t0

        self.assertEqual(
            result.returncode, 0,
            f"tests/test_v2_class_evolutions_r4.py failed with exit code {result.returncode}:\n{result.stderr}"
        )
        self.assertLess(
            elapsed, 2.0,
            f"Execution time {elapsed:.3f}s exceeded the 2.0s performance ceiling."
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
