"""
Comprehensive Fast Unit Test Suite for Milestone 4 (R4):
Classic 10 Base Classes and Multi-Tier Observational Class Evolutions.

Execution Budget: < 2.0 seconds total runtime.
Covers:
1. All 10 base classes instantiate with proper stats, HP, and resources.
2. `normalize_class_key` handles all 15+ alias permutations.
3. Level 1-9 progression increments level and scales HP properly based on ARCHETYPE_HP_GROWTH.
4. Level 10 gate verifies Level >= 10 AND Sector 1 Spire Boss defeat.
5. Level 10 evolution synthesis produces exactly 3 choices covering Discipline Synergy,
   Moral/Ethical Alignment (Holy vs Necrotic/Deathknight), and Relic/Deed/Lineage anchor.
6. Level 20 gate and 3 prestige branches.
7. Level 30 gate and 3 apex legendary evolutions.
8. Resource scaling (+25% T2, +50% T3, +100% T4).
9. Backward compatibility of Glenny chimera (class_key="ranger") and Banki (class_key="warrior").
"""

import os
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


class TestClassic10BaseClassesAndEvolutionsR4(unittest.TestCase):
    """Fast, deterministic unit test suite verifying Milestone 4 R4 requirements."""

    CLASSIC_10 = [
        "fighter", "wizard", "rogue", "cleric", "ranger",
        "paladin", "druid", "bard", "barbarian", "monk"
    ]

    # -------------------------------------------------------------------------
    # 1. Base Class Instantiation, Stats, HP, and Resources
    # -------------------------------------------------------------------------

    def test_01_all_10_base_classes_in_class_paths(self):
        """Verify all 10 classic base classes exist in CLASS_PATHS with complete metadata."""
        class_paths = getattr(cg, "CLASS_PATHS", {})
        missing = [c for c in self.CLASSIC_10 if c not in class_paths]
        self.assertEqual(
            missing, [],
            f"R4 Violation: Missing Classic 10 classes in CLASS_PATHS: {missing}"
        )

        expected_resources = {
            "fighter": ("poise", 100),
            "wizard": ("flux", 50),
            "rogue": ("momentum", 5),
            "cleric": ("devotion", 100),
            "ranger": ("focus", 5),
            "paladin": ("zeal", 100),
            "druid": ("primal", 100),
            "bard": ("cadence", 100),
            "barbarian": ("rage", 100),
            "monk": ("ki", 10),
        }

        for c_key in self.CLASSIC_10:
            c_info = class_paths[c_key]
            self.assertIn("title", c_info, f"Class {c_key} missing 'title'")
            self.assertIn("base_hp", c_info, f"Class {c_key} missing 'base_hp'")
            self.assertIn("hp_per_lvl", c_info, f"Class {c_key} missing 'hp_per_lvl'")
            self.assertIn("combat_resource", c_info, f"Class {c_key} missing 'combat_resource'")
            self.assertIn("favored_skills", c_info, f"Class {c_key} missing 'favored_skills'")
            self.assertGreaterEqual(
                len(c_info["favored_skills"]), 2,
                f"Class {c_key} must have at least 2 favored skills, got {c_info['favored_skills']}"
            )
            self.assertIn("starting_feats", c_info, f"Class {c_key} missing 'starting_feats'")
            self.assertEqual(
                len(c_info["starting_feats"]), 2,
                f"Class {c_key} must have exactly 2 Iconic Duo starting feats, got {c_info['starting_feats']}"
            )

            res_info = c_info["combat_resource"]
            exp_type, exp_max = expected_resources[c_key]
            self.assertEqual(
                res_info.get("type"), exp_type,
                f"Class {c_key} resource type expected '{exp_type}', got '{res_info.get('type')}'"
            )
            self.assertEqual(
                res_info.get("max"), exp_max,
                f"Class {c_key} resource max expected {exp_max}, got {res_info.get('max')}"
            )

    def test_02_all_10_base_classes_generate_cleanly(self):
        """Verify character generator instantiates functional characters for all 10 base classes."""
        for c_key in self.CLASSIC_10:
            char = cg.generate_starting_character(
                name=f"Test_{c_key.title()}",
                class_key=c_key,
                start_tutorial=False
            )
            player = char.get("player", char)
            self.assertGreater(
                player.get("max_hp", 0), 50,
                f"Class {c_key} starting max_hp should be > 50, got {player.get('max_hp')}"
            )
            res = player.get("combat_resource", {})
            self.assertIn("name", res, f"Class {c_key} player missing combat_resource.name")
            self.assertIn("max", res, f"Class {c_key} player missing combat_resource.max")
            self.assertIn("current", res, f"Class {c_key} player missing combat_resource.current")
            self.assertIn("type", res, f"Class {c_key} player missing combat_resource.type")

    def test_03_class_weapons_for_all_10_classes(self):
        """Verify CLASS_WEAPONS provides default main_hand and off_hand for all 10 classes."""
        class_weapons = getattr(cg, "CLASS_WEAPONS", {})
        for c_key in self.CLASSIC_10:
            self.assertIn(c_key, class_weapons, f"CLASS_WEAPONS missing entry for '{c_key}'")
            w_entry = class_weapons[c_key]
            self.assertIn("main_hand", w_entry, f"CLASS_WEAPONS['{c_key}'] missing 'main_hand'")
            self.assertIn("off_hand", w_entry, f"CLASS_WEAPONS['{c_key}'] missing 'off_hand'")
            self.assertIn("desc", w_entry, f"CLASS_WEAPONS['{c_key}'] missing 'desc'")

    # -------------------------------------------------------------------------
    # 2. Class Key Normalization (15+ Permutations)
    # -------------------------------------------------------------------------

    def test_04_normalize_class_key_alias_permutations(self):
        """Verify normalize_class_key handles 15+ alias permutations and legacy classes."""
        normalize_fn = getattr(mechanics, "normalize_class_key", None)
        self.assertIsNotNone(normalize_fn, "backend.mechanics must export normalize_class_key")

        alias_cases = [
            ("warrior", "fighter"),
            ("vanguard", "fighter"),
            ("fighter", "fighter"),
            ("Heavy Vanguard", "fighter"),
            ("mage", "wizard"),
            ("aether_slinger", "wizard"),
            ("wizard", "wizard"),
            ("arcanist", "wizard"),
            ("thief", "rogue"),
            ("infiltrator", "rogue"),
            ("rogue", "rogue"),
            ("Shadow Infiltrator", "rogue"),
            ("cleric", "cleric"),
            ("templar", "cleric"),
            ("Spire Templar", "cleric"),
            ("ranger", "ranger"),
            ("wilderness_ranger", "ranger"),
            ("hunter", "ranger"),
            ("paladin", "paladin"),
            ("crusader", "paladin"),
            ("druid", "druid"),
            ("shifter", "druid"),
            ("bard", "bard"),
            ("virtuoso", "bard"),
            ("barbarian", "barbarian"),
            ("berserker", "barbarian"),
            ("monk", "monk"),
            ("ascetic", "monk"),
            ("pathless", "pathless"),
            ("", "pathless"),
            (None, "pathless"),
        ]

        for input_str, expected in alias_cases:
            resolved = normalize_fn(input_str)
            self.assertEqual(
                resolved, expected,
                f"normalize_class_key({input_str!r}) returned {resolved!r}, expected {expected!r}"
            )

        # Legacy non-breaking classes
        self.assertIn(normalize_fn("engineer"), ["engineer", "pathless"])
        self.assertIn(normalize_fn("psion"), ["psion", "pathless"])

    # -------------------------------------------------------------------------
    # 3. Level 1–9 Progression & HP Scaling
    # -------------------------------------------------------------------------

    def test_05_level_1_to_9_progression_and_hp_growth(self):
        """Verify leveling from 1 to 9 increments level cleanly and scales HP according to ARCHETYPE_HP_GROWTH."""
        hp_growth_table = getattr(mechanics, "ARCHETYPE_HP_GROWTH", {})

        test_classes = ["barbarian", "fighter", "cleric", "wizard"]
        for c_key in test_classes:
            char = cg.generate_starting_character(name=f"LvTest_{c_key}", class_key=c_key, start_tutorial=False)
            player = char.get("player", char)

            con_mod = (player.get("stats", {}).get("CON", 10) - 10) // 2
            expected_growth = hp_growth_table.get(c_key, hp_growth_table.get(mechanics.normalize_class_key(c_key), 25))

            for expected_lvl in range(2, 10):
                prev_hp = player["max_hp"]
                mechanics.apply_level_up(player)
                self.assertEqual(player["level"], expected_lvl, f"Level should be {expected_lvl}")
                actual_gain = player["max_hp"] - prev_hp
                expected_gain = expected_growth + con_mod
                self.assertEqual(
                    actual_gain, expected_gain,
                    f"Class {c_key} level {expected_lvl} HP gain {actual_gain} != expected {expected_gain}"
                )

            self.assertEqual(player["level"], 9)

    # -------------------------------------------------------------------------
    # 4. Level 10 Evolution Gate (Level >= 10 AND Sector 1 Spire Boss Defeat)
    # -------------------------------------------------------------------------

    def test_06_level_10_gate_enforcement(self):
        """Verify check_evolution_eligibility enforces Level >= 10 AND Sector 1 Spire Boss defeat."""
        char = cg.generate_starting_character(name="GateTester", class_key="fighter", start_tutorial=False)
        player = char.get("player", char)

        # Level 1 -> Not eligible
        e1 = mechanics.check_evolution_eligibility(player)
        self.assertFalse(e1.get("eligible"), "Level 1 character must not be eligible for evolution.")

        # Level 10 without boss defeat -> Not eligible
        player["level"] = 10
        player["skills"]["Trench Hammers"] = 150
        player["bosses_defeated"] = []
        player["sector_boss_defeated"] = False

        e2 = mechanics.check_evolution_eligibility(player)
        self.assertFalse(e2.get("eligible"), "Level 10 character without Spire Boss defeat must NOT be eligible.")
        reasons_text = " ".join(e2.get("reasons", [])).lower()
        self.assertTrue(
            "boss" in reasons_text or "spire" in reasons_text or "sector" in reasons_text or "overlord" in reasons_text,
            f"Expected missing boss defeat explanation in reasons: {e2.get('reasons')}"
        )

        # Defeat Spire Boss -> Eligible
        player["sector_boss_defeated"] = True
        player["bosses_defeated"] = ["The Gilded Spire Overlord (Sector 1)"]

        e3 = mechanics.check_evolution_eligibility(player)
        self.assertTrue(e3.get("eligible"), f"Level 10 character with Spire Boss defeat must be eligible. {e3}")

    # -------------------------------------------------------------------------
    # 5. Level 10 Observational Evolution Synthesis (Exactly 3 Bespoke Choices)
    # -------------------------------------------------------------------------

    def test_07_level_10_evolution_synthesis_structure_and_categories(self):
        """Verify generate_curated_evolutions returns exactly 3 choices covering Discipline, Alignment, and Anchor."""
        char = cg.generate_starting_character(name="EvoTester", class_key="fighter", start_tutorial=False)
        player = char.get("player", char)
        player["level"] = 10
        player["sector_boss_defeated"] = True
        player["bosses_defeated"] = ["The Gilded Spire Overlord (Sector 1)"]
        player["telemetry"] = {
            "weapon_masteries": {"swords": 100, "axes": 20},
            "spells_cast": {"holy_radiant": 20, "necrotic_curse": 0},
            "combat_discipline": {"holy_radiant_damage_dealt": 400, "necrotic_curse_damage_dealt": 0},
            "moral_choices": {"good_compassionate_dialogues": 5, "evil_ruthless_dialogues": 0},
            "deeds": ["spared_cultist"],
            "relics_held": ["smartphone"]
        }

        choices = mechanics.generate_curated_evolutions(player)
        self.assertEqual(
            len(choices), 3,
            f"generate_curated_evolutions must return exactly 3 choices, got {len(choices)}"
        )

        for idx, choice in enumerate(choices):
            self.assertIn("title", choice, f"Choice {idx} missing 'title'")
            self.assertIn("category", choice, f"Choice {idx} missing 'category'")
            self.assertIn("desc", choice, f"Choice {idx} missing 'desc'")
            self.assertEqual(choice.get("tier"), 2, f"Choice {idx} must be Tier 2")

        categories = [c["category"].lower() for c in choices]
        self.assertTrue(
            any("synergy" in cat or "discipline" in cat or "weapon" in cat for cat in categories),
            f"Expected Discipline & Weapon Synergy category in {categories}"
        )
        self.assertTrue(
            any("alignment" in cat or "moral" in cat or "ethical" in cat for cat in categories),
            f"Expected Moral & Ethical Alignment category in {categories}"
        )

    def test_08_dual_track_telemetry_holy_vs_necrotic_synthesis(self):
        """Verify dual-track telemetry correctly routes Holy/Good -> Templar/Protector and Necrotic/Evil -> Deathknight/Blood."""
        # Holy Character
        holy_char = cg.generate_starting_character(name="HolyHero", class_key="cleric", start_tutorial=False)
        p_holy = holy_char.get("player", holy_char)
        p_holy["level"] = 10
        p_holy["sector_boss_defeated"] = True
        p_holy["telemetry"] = {
            "weapon_masteries": {"maces": 100},
            "spells_cast": {"holy_radiant": 30},
            "combat_discipline": {"holy_radiant_damage_dealt": 1000, "necrotic_curse_damage_dealt": 0},
            "moral_choices": {"good_compassionate_dialogues": 10, "evil_ruthless_dialogues": 0},
            "deeds": ["consecrated_shrine"],
            "relics_held": []
        }
        holy_evos = mechanics.generate_curated_evolutions(p_holy)
        holy_titles = [e["title"].lower() for e in holy_evos]
        self.assertTrue(
            any("templar" in t or "protector" in t or "crusader" in t or "radiant" in t for t in holy_titles),
            f"Holy telemetry should offer Good/Holy evolution path, got {holy_titles}"
        )

        # Necrotic Character
        necro_char = cg.generate_starting_character(name="DarkHero", class_key="fighter", start_tutorial=False)
        p_necro = necro_char.get("player", necro_char)
        p_necro["level"] = 10
        p_necro["sector_boss_defeated"] = True
        p_necro["telemetry"] = {
            "weapon_masteries": {"greatswords": 100},
            "spells_cast": {"necrotic_curse": 30},
            "combat_discipline": {"holy_radiant_damage_dealt": 0, "necrotic_curse_damage_dealt": 1000},
            "moral_choices": {"good_compassionate_dialogues": 0, "evil_ruthless_dialogues": 10},
            "deeds": ["desecrated_shrine"],
            "relics_held": []
        }
        necro_evos = mechanics.generate_curated_evolutions(p_necro)
        necro_titles = [e["title"].lower() for e in necro_evos]
        self.assertTrue(
            any("deathknight" in t or "blood" in t or "shadow" in t or "dread" in t for t in necro_titles),
            f"Necrotic telemetry should offer Evil/Necrotic evolution path, got {necro_titles}"
        )

    def test_09_relic_and_monstrous_lineage_anchor(self):
        """Verify Choice 3 tailors to personal relics or monstrous lineage."""
        # Minotaur Lineage
        mino_char = cg.generate_starting_character(
            name="Taurus",
            race_key="minotaur_labyrinth_reaver",
            class_key="barbarian",
            start_tutorial=False
        )
        p_mino = mino_char.get("player", mino_char)
        p_mino["level"] = 10
        p_mino["sector_boss_defeated"] = True
        p_mino["skills"]["Two-Handed Greataxes"] = 120
        mino_evos = mechanics.generate_curated_evolutions(p_mino)
        mino_text = " ".join([e["title"] + " " + e.get("desc", "") for e in mino_evos]).lower()
        self.assertTrue(
            "minotaur" in mino_text or "bull" in mino_text or "labyrinth" in mino_text or "gore" in mino_text,
            f"Expected Minotaur racial anchor in evolution options: {mino_text}"
        )

        # Smartphone Relic Anchor
        relic_char = cg.generate_starting_character(name="TechGuy", class_key="rogue", start_tutorial=False)
        p_relic = relic_char.get("player", relic_char)
        p_relic["level"] = 10
        p_relic["sector_boss_defeated"] = True
        p_relic["relics_held"] = ["smartphone"]
        p_relic["inventory"] = [{"name": "Earth Smartphone (99% Battery, No Signal)"}]
        relic_evos = mechanics.generate_curated_evolutions(p_relic)
        relic_text = " ".join([e["title"] + " " + e.get("desc", "") for e in relic_evos]).lower()
        self.assertTrue(
            "echo" in relic_text or "smartphone" in relic_text or "terminal" in relic_text or "logic" in relic_text or "old-world" in relic_text,
            f"Expected Smartphone relic anchor in evolution options: {relic_text}"
        )

    # -------------------------------------------------------------------------
    # 6. Level 20 Gate & 3 Prestige Branches (Tier 3)
    # -------------------------------------------------------------------------

    def test_10_level_20_gate_and_prestige_branches(self):
        """Verify Level 20 eligibility triggers exactly 3 prestige branches."""
        char = cg.generate_starting_character(name="PrestigeHero", class_key="fighter", start_tutorial=False)
        player = char.get("player", char)

        # Set Tier 2 baseline
        player["level"] = 10
        player["class_tier"] = 2
        player["class"] = "Runic Spellblade"

        # Advance to Level 20 without regional boss -> not eligible
        player["level"] = 20
        player["skills"]["Heavy Swords"] = 400
        player["regional_boss_defeated"] = False
        player["bosses_defeated"] = ["The Gilded Spire Overlord (Sector 1)"]

        e_pre = mechanics.check_evolution_eligibility(player)
        self.assertFalse(e_pre.get("eligible"), "Level 20 without regional boss must NOT be eligible.")

        # Defeat Regional Boss -> eligible
        player["regional_boss_defeated"] = True
        player["bosses_defeated"].append("Regional Apex Behemoth (Sector 5)")

        e_post = mechanics.check_evolution_eligibility(player)
        self.assertTrue(e_post.get("eligible"), f"Level 20 with Regional Boss defeat must be eligible. {e_post}")

        t3_choices = mechanics.generate_curated_evolutions(player)
        self.assertEqual(len(t3_choices), 3, f"Tier 3 must offer exactly 3 prestige branches, got {len(t3_choices)}")
        for choice in t3_choices:
            self.assertEqual(choice.get("tier"), 3, f"Tier 3 choices must have tier=3: {choice}")
            self.assertIn("title", choice)
            self.assertIn("desc", choice)

    # -------------------------------------------------------------------------
    # 7. Level 30 Gate & 3 Apex Legendary Evolutions (Tier 4)
    # -------------------------------------------------------------------------

    def test_11_level_30_gate_and_apex_legendary_evolutions(self):
        """Verify Level 30 eligibility triggers exactly 3 apex legendary evolutions breaking tier limits."""
        char = cg.generate_starting_character(name="ApexHero", class_key="wizard", start_tutorial=False)
        player = char.get("player", char)

        # Set Tier 3 baseline
        player["level"] = 20
        player["class_tier"] = 3
        player["class"] = "Grand Aether-Blademaster"

        # Advance to Level 30 without planetary boss -> not eligible
        player["level"] = 30
        player["skills"]["Aether-Weaving"] = 800
        player["planetary_boss_defeated"] = False
        player["bosses_defeated"] = ["The Gilded Spire Overlord (Sector 1)", "Regional Apex Behemoth (Sector 5)"]

        e_pre = mechanics.check_evolution_eligibility(player)
        self.assertFalse(e_pre.get("eligible"), "Level 30 without planetary boss must NOT be eligible.")

        # Defeat Planetary Boss -> eligible
        player["planetary_boss_defeated"] = True
        player["bosses_defeated"].append("Planetary World-Eater Core")

        e_post = mechanics.check_evolution_eligibility(player)
        self.assertTrue(e_post.get("eligible"), f"Level 30 with Planetary Boss defeat must be eligible. {e_post}")

        t4_choices = mechanics.generate_curated_evolutions(player)
        self.assertEqual(len(t4_choices), 3, f"Tier 4 must offer exactly 3 apex choices, got {len(t4_choices)}")
        for choice in t4_choices:
            self.assertEqual(choice.get("tier"), 4, f"Tier 4 choices must have tier=4: {choice}")
            self.assertIn("title", choice)
            self.assertIn("desc", choice)

    # -------------------------------------------------------------------------
    # 8. Resource Scaling (+25% T2, +50% T3, +100% T4)
    # -------------------------------------------------------------------------

    def test_12_apply_class_evolution_resource_scaling(self):
        """Verify apply_class_evolution scales combat resources: +25% at T2, +50% at T3, +100% at T4."""
        char = cg.generate_starting_character(name="ScalingTester", class_key="fighter", start_tutorial=False)
        player = char.get("player", char)

        base_res_max = player["combat_resource"]["max"]  # 100 for fighter

        # Apply Tier 2
        t2_choice = {
            "title": "Runic Spellblade",
            "tier": 2,
            "category": "Discipline Synergy",
            "desc": "Martial arcana mastery."
        }
        mechanics.apply_class_evolution(player, t2_choice)
        self.assertEqual(player["class"], "Runic Spellblade")
        self.assertEqual(player["class_tier"], 2)
        expected_t2 = int(base_res_max * 1.25)
        self.assertEqual(
            player["combat_resource"]["max"], expected_t2,
            f"Tier 2 should scale resource by +25% ({expected_t2}), got {player['combat_resource']['max']}"
        )

        # Apply Tier 3
        t3_choice = {
            "title": "Aether-Forged Blademaster",
            "tier": 3,
            "category": "Prestige Branch",
            "desc": "Supreme runic mastery."
        }
        mechanics.apply_class_evolution(player, t3_choice)
        self.assertEqual(player["class"], "Aether-Forged Blademaster")
        self.assertEqual(player["class_tier"], 3)
        expected_t3 = int(expected_t2 * 1.50)
        self.assertEqual(
            player["combat_resource"]["max"], expected_t3,
            f"Tier 3 should scale resource by +50% ({expected_t3}), got {player['combat_resource']['max']}"
        )

        # Apply Tier 4
        t4_choice = {
            "title": "Chrono-Architect Prime",
            "tier": 4,
            "category": "Apex Apotheosis",
            "desc": "Transcends turn tick-rates."
        }
        mechanics.apply_class_evolution(player, t4_choice)
        self.assertEqual(player["class"], "Chrono-Architect Prime")
        self.assertEqual(player["class_tier"], 4)
        expected_t4 = int(expected_t3 * 2.00)
        self.assertEqual(
            player["combat_resource"]["max"], expected_t4,
            f"Tier 4 should scale resource by +100% ({expected_t4}), got {player['combat_resource']['max']}"
        )

        # Feat recording
        feats_text = " ".join(player.get("feats", []))
        self.assertIn("Chrono-Architect Prime", feats_text)

    # -------------------------------------------------------------------------
    # 9. Backward Compatibility: Glenny Chimera & Banki Vanguard
    # -------------------------------------------------------------------------

    def test_13_glenny_chimera_backward_compatibility(self):
        """Verify Glenny chimera (ranger) preserves 4 hand slots, focus resource, and AC 14/16."""
        char = cg.generate_starting_character(
            name="Glenny",
            race_key="troll_kreen_chimera",
            class_key="ranger",
            start_tutorial=False
        )
        player = char.get("player", char)

        # Multi-limb hand slots
        eq = player.get("equipped", {})
        self.assertIn("main_hand", eq)
        self.assertIn("off_hand", eq)
        self.assertIn("lower_main_hand", eq)
        self.assertIn("lower_off_hand", eq)

        # Resource is Focus & Vantage
        res = player.get("combat_resource", {})
        self.assertEqual(res.get("type"), "focus")
        self.assertEqual(res.get("max"), 5)

        # AC calculation
        ac_val = mechanics.calculate_ac(player)
        self.assertIn(ac_val, [14, 16], f"Glenny AC should be 14 or 16, got {ac_val}")

        # Normalization
        norm_class = mechanics.normalize_class_key(player.get("class", "ranger"))
        self.assertEqual(norm_class, "ranger")

    def test_14_banki_vanguard_backward_compatibility(self):
        """Verify Banki (warrior/vanguard) resolves to fighter and instantiates cleanly."""
        # Class key "warrior"
        char_warrior = cg.generate_starting_character(
            name="Banki",
            class_key="warrior",
            start_tutorial=False
        )
        p_war = char_warrior.get("player", char_warrior)
        norm_war = mechanics.normalize_class_key(p_war.get("class", "warrior"))
        self.assertEqual(norm_war, "fighter")

        # Class key "vanguard"
        char_vanguard = cg.generate_starting_character(
            name="Banki_Vanguard",
            class_key="vanguard",
            start_tutorial=False
        )
        p_van = char_vanguard.get("player", char_vanguard)
        norm_van = mechanics.normalize_class_key(p_van.get("class", "vanguard"))
        self.assertEqual(norm_van, "fighter")

        # Resource is Poise & Threat
        self.assertEqual(p_war.get("combat_resource", {}).get("type"), "poise")

    # -------------------------------------------------------------------------
    # 10. Execution Speed Benchmark (< 2.0 Seconds)
    # -------------------------------------------------------------------------

    def test_15_suite_execution_speed_benchmark(self):
        """Verify that rapid character creation and class evolution checks execute in < 2.0 seconds."""
        t0 = time.perf_counter()

        # Execute 5 fast character instantiations and progression cycles
        for i in range(5):
            c_key = self.CLASSIC_10[i % len(self.CLASSIC_10)]
            char = cg.generate_starting_character(name=f"Speed_{i}", class_key=c_key, start_tutorial=False)
            p = char.get("player", char)
            for _ in range(3):
                mechanics.apply_level_up(p)
            mechanics.normalize_class_key(c_key)

        elapsed = time.perf_counter() - t0
        self.assertLess(
            elapsed, 2.0,
            f"Execution time {elapsed:.3f}s exceeded the 2.0s performance budget."
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
