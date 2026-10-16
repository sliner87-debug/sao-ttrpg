"""
Milestone 4 Adversarial Challenge & Property-Based Fuzz Test Suite
Authored by Milestone 4 Challenger 1.

Verifies:
1. `normalize_class_key()`: Fuzzing 80+ class key alias variations, case variations, whitespace,
   corrupt/malformed strings, types, and compound titles, asserting no exceptions are raised
   and all aliases resolve correctly.
2. Evolution eligibility boundary testing:
   - Level 9 with boss down -> ineligible (Level unmet)
   - Level 10 with NO boss down -> ineligible (Boss unmet)
   - Level 10 with boss down but mastery < 100 -> ineligible (Mastery unmet)
   - Level 10 with boss down and mastery >= 100 -> eligible (Tier 2)
   - Level 19 with regional boss down -> ineligible for Tier 3
   - Level 20 with regional boss down and mastery >= 350 -> eligible for Tier 3
   - Level 29 with planetary boss down -> ineligible for Tier 4
   - Level 30 with planetary boss down and mastery >= 750 -> eligible for Tier 4
   - Post-Tier 4 max tier capped
3. Dual-track behavioral telemetry synthesis stress:
   - Holy damage / dialogue player -> produces Holy/Radiant evolution choice across all classes
   - Necrotic damage / dialogue player -> produces Necrotic/Deathknight/Blood/Shadow/Dread choice across all classes
   - Cold-start player with no explicit telemetry dict -> produces valid 3 choices without KeyError
   - Monstrous lineage player (Minotaur, Pixie, Satyr, Nymph, Gargoyle, Centaur, Troll, Chimera, Medusa, Ogre, Kobold, Gnoll) -> produces racial anchor option
   - Relic and deed anchors for human players
4. Resource scaling and tier transition stress (+25% T2, +50% T3, +100% T4) across all classes.
"""

import os
import sys
import unittest
import itertools

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


class TestNormalizeClassKeyFuzzing(unittest.TestCase):
    """Property-based stress testing and fuzzing for normalize_class_key()."""

    CANONICAL_10 = [
        "fighter", "wizard", "rogue", "cleric", "ranger",
        "paladin", "druid", "bard", "barbarian", "monk"
    ]

    ALIAS_TARGETS = {
        # Fighter aliases
        "warrior": "fighter",
        "vanguard": "fighter",
        # Wizard aliases
        "mage": "wizard",
        "aether_slinger": "wizard",
        "arcanist": "wizard",
        "slinger": "wizard",
        # Rogue aliases
        "thief": "rogue",
        "infiltrator": "rogue",
        "assassin": "rogue",
        # Cleric aliases
        "templar": "cleric",
        "priest": "cleric",
        # Ranger aliases
        "wilderness_ranger": "ranger",
        "hunter": "ranger",
        "marksman": "ranger",
        # Paladin aliases
        "crusader": "paladin",
        # Druid aliases
        "shifter": "druid",
        # Bard aliases
        "virtuoso": "bard",
        "skald": "bard",
        # Barbarian aliases
        "berserker": "barbarian",
        "juggernaut": "barbarian",
        # Monk aliases
        "ascetic": "monk",
        # Legacy non-breaking classes
        "engineer": "engineer",
        "artificer": "engineer",
        "magi_saboteur": "engineer",
        "psion": "psion",
        "phrenic": "psion",
        "mentalist": "psion",
        "pathless": "pathless",
    }

    def test_fuzz_all_canonical_and_aliases_with_whitespace_and_casing(self):
        """Fuzz 80+ permutations of casing and whitespace padding across all classes and aliases."""
        whitespace_paddings = [
            ("", ""),
            ("  ", "  "),
            ("\t", "\t"),
            ("\n", "\n"),
            ("\r\n ", " \r\n"),
            ("   \t", "\t   "),
        ]

        case_transforms = [
            lambda s: s.lower(),
            lambda s: s.upper(),
            lambda s: s.title(),
            lambda s: "".join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(s)),
        ]

        total_tested = 0
        all_mappings = {c: c for c in self.CANONICAL_10}
        all_mappings.update(self.ALIAS_TARGETS)

        for raw_key, expected_canonical in all_mappings.items():
            for transform in case_transforms:
                transformed = transform(raw_key)
                for pre, post in whitespace_paddings:
                    test_str = f"{pre}{transformed}{post}"
                    try:
                        resolved = mechanics.normalize_class_key(test_str)
                    except Exception as exc:
                        self.fail(f"normalize_class_key({test_str!r}) raised exception: {exc}")
                    self.assertEqual(
                        resolved, expected_canonical,
                        f"Failed resolution: normalize_class_key({test_str!r}) -> {resolved!r}, expected {expected_canonical!r}"
                    )
                    total_tested += 1

        self.assertGreaterEqual(total_tested, 50, f"Must fuzz at least 50 variations, tested {total_tested}")

    def test_corrupt_malformed_and_boundary_strings(self):
        """Verify that malformed, corrupted, empty, non-string, or boundary inputs never crash."""
        corrupt_inputs = [
            "",
            "   ",
            "\t\n\r",
            None,
            123,
            99.9,
            [],
            {},
            True,
            False,
            object(),
            "unknown_class_xyz",
            "!@#$%^&*()",
            "null",
            "undefined",
            "NaN",
            " \x00\x01\x02 ",
            "DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "⚔️🛡️🏹🧙‍♂️",
            "a" * 5000,  # Long buffer
        ]

        for bad_input in corrupt_inputs:
            try:
                resolved = mechanics.normalize_class_key(bad_input)
            except Exception as exc:
                self.fail(f"normalize_class_key({bad_input!r}) raised exception: {exc}")
            self.assertEqual(
                resolved, "pathless",
                f"normalize_class_key({bad_input!r}) should resolve to 'pathless', got {resolved!r}"
            )

    def test_compound_and_descriptive_titles_substring_matching(self):
        """Verify descriptive titles like 'Fighter (Martial Weaponmaster)' resolve to canonical keys."""
        compound_cases = [
            ("Fighter (Martial Weaponmaster)", "fighter"),
            ("Heavy Vanguard Defender", "fighter"),
            ("Spire High Templar of Light", "cleric"),
            ("Shadow Infiltrator Assassin", "rogue"),
            ("Primal Shifter of Gaea", "druid"),
            ("Aether Slinger Arcanist", "wizard"),
            ("Berserker of the North", "barbarian"),
            ("Sylvan Skald Virtuoso", "bard"),
            ("Grand Ascetic of Iron Will", "monk"),
            ("Wilderness Marksman Hunter", "ranger"),
            ("Artificer Cyber-Mancer Saboteur", "engineer"),
            ("Phrenic Telepathic Mentalist", "psion"),
        ]

        for input_title, expected_canonical in compound_cases:
            resolved = mechanics.normalize_class_key(input_title)
            self.assertEqual(
                resolved, expected_canonical,
                f"normalize_class_key({input_title!r}) returned {resolved!r}, expected {expected_canonical!r}"
            )


class TestEvolutionEligibilityBoundaryGating(unittest.TestCase):
    """Adversarially stress-tests boundary gating at Levels 10, 20, and 30."""

    def test_tier_2_boundary_matrix(self):
        """
        Matrix of Tier 2 boundaries:
        - Level 9 with boss down -> ineligible.
        - Level 10 with NO boss down -> ineligible.
        - Level 10 with boss down but mastery < 100 -> ineligible.
        - Level 10 with boss down and mastery >= 100 -> eligible.
        """
        # Case 1: Level 9 with boss down & mastery 100
        p1 = {
            "level": 9,
            "class_tier": 1,
            "sector_boss_defeated": True,
            "skills": {"Greatswords": 100}
        }
        res1 = mechanics.check_evolution_eligibility(p1)
        self.assertFalse(res1["eligible"], "Level 9 with boss down must be ineligible.")
        self.assertTrue(any("Level 9 / 10" in u for u in res1["unmet_conditions"]))
        self.assertEqual(res1["target_tier"], 2)

        # Case 2: Level 10 with NO boss down
        p2 = {
            "level": 10,
            "class_tier": 1,
            "sector_boss_defeated": False,
            "bosses_defeated": [],
            "skills": {"Greatswords": 100}
        }
        res2 = mechanics.check_evolution_eligibility(p2)
        self.assertFalse(res2["eligible"], "Level 10 with NO boss down must be ineligible.")
        self.assertTrue(any("Boss Not Yet Slayed" in u for u in res2["unmet_conditions"]))

        # Case 3: Level 10 with boss down but mastery < 100 (boundary value: 99)
        p3 = {
            "level": 10,
            "class_tier": 1,
            "sector_boss_defeated": True,
            "skills": {"Greatswords": 99}
        }
        res3 = mechanics.check_evolution_eligibility(p3)
        self.assertFalse(res3["eligible"], "Level 10 with mastery 99 must be ineligible.")
        self.assertTrue(any("Mastery 99 / 100" in u for u in res3["unmet_conditions"]))

        # Case 4: Level 10 with boss down and mastery >= 100 (exact boundary value: 100)
        p4 = {
            "level": 10,
            "class_tier": 1,
            "sector_boss_defeated": True,
            "skills": {"Greatswords": 100}
        }
        res4 = mechanics.check_evolution_eligibility(p4)
        self.assertTrue(res4["eligible"], "Level 10 with boss down and mastery 100 must be eligible.")
        self.assertEqual(res4["unmet_conditions"], [])
        self.assertEqual(res4["target_tier"], 2)

        # Case 5: Boss defeated via bosses_defeated string list
        p5 = {
            "level": 10,
            "class_tier": 1,
            "sector_boss_defeated": False,
            "bosses_defeated": ["The Gilded Spire Overlord (Sector 1)"],
            "skills": {"Greatswords": {"mastery": 150}}
        }
        res5 = mechanics.check_evolution_eligibility(p5)
        self.assertTrue(res5["eligible"], "Boss down via bosses_defeated list must be recognized.")

    def test_tier_3_boundary_matrix(self):
        """
        Matrix of Tier 3 boundaries (fixing legacy Level 25 bug -> Level 20):
        - Level 19 with regional boss down -> ineligible for Tier 3.
        - Level 20 with NO regional boss down -> ineligible for Tier 3.
        - Level 20 with regional boss down and mastery < 350 (349) -> ineligible.
        - Level 20 with regional boss down and mastery >= 350 (350) -> eligible for Tier 3.
        """
        # Case 1: Level 19 with regional boss down
        p1 = {
            "level": 19,
            "class_tier": 2,
            "regional_boss_defeated": True,
            "skills": {"Polearms": 500}
        }
        res1 = mechanics.check_evolution_eligibility(p1)
        self.assertFalse(res1["eligible"], "Level 19 must be ineligible for Tier 3.")
        self.assertTrue(any("Level 19 / 20" in u for u in res1["unmet_conditions"]))
        self.assertEqual(res1["target_tier"], 3)

        # Case 2: Level 20 with NO regional boss down
        p2 = {
            "level": 20,
            "class_tier": 2,
            "regional_boss_defeated": False,
            "bosses_defeated": ["Sector 1 Boss"],
            "skills": {"Polearms": 500}
        }
        res2 = mechanics.check_evolution_eligibility(p2)
        self.assertFalse(res2["eligible"], "Level 20 without regional boss must be ineligible.")
        self.assertTrue(any("Regional Spire Boss Not Yet Slayed" in u for u in res2["unmet_conditions"]))

        # Case 3: Level 20 with regional boss down but mastery 349
        p3 = {
            "level": 20,
            "class_tier": 2,
            "regional_boss_defeated": True,
            "skills": {"Polearms": 349}
        }
        res3 = mechanics.check_evolution_eligibility(p3)
        self.assertFalse(res3["eligible"], "Level 20 with mastery 349 must be ineligible for Tier 3.")
        self.assertTrue(any("Mastery 349 / 350" in u for u in res3["unmet_conditions"]))

        # Case 4: Level 20 with regional boss down and mastery 350 (exact boundary)
        p4 = {
            "level": 20,
            "class_tier": 2,
            "regional_boss_defeated": True,
            "skills": {"Polearms": 350}
        }
        res4 = mechanics.check_evolution_eligibility(p4)
        self.assertTrue(res4["eligible"], "Level 20 with regional boss down and mastery 350 must be eligible for Tier 3.")
        self.assertEqual(res4["target_tier"], 3)

    def test_tier_4_boundary_matrix(self):
        """
        Matrix of Tier 4 boundaries:
        - Level 29 with planetary boss down -> ineligible for Tier 4.
        - Level 30 with NO planetary boss down -> ineligible for Tier 4.
        - Level 30 with planetary boss down and mastery < 750 (749) -> ineligible.
        - Level 30 with planetary boss down and mastery >= 750 (750) -> eligible for Tier 4.
        - Level 35 already Tier 4 -> max tier capped.
        """
        # Case 1: Level 29 with planetary boss down
        p1 = {
            "level": 29,
            "class_tier": 3,
            "planetary_boss_defeated": True,
            "skills": {"Aether-Weaving": 900}
        }
        res1 = mechanics.check_evolution_eligibility(p1)
        self.assertFalse(res1["eligible"], "Level 29 must be ineligible for Tier 4.")
        self.assertTrue(any("Level 29 / 30" in u for u in res1["unmet_conditions"]))
        self.assertEqual(res1["target_tier"], 4)

        # Case 2: Level 30 with NO planetary boss down
        p2 = {
            "level": 30,
            "class_tier": 3,
            "planetary_boss_defeated": False,
            "bosses_defeated": ["Sector 1 Boss", "Regional Behemoth"],
            "skills": {"Aether-Weaving": 900}
        }
        res2 = mechanics.check_evolution_eligibility(p2)
        self.assertFalse(res2["eligible"], "Level 30 without planetary boss must be ineligible.")
        self.assertTrue(any("Planetary World-Eater Boss Not Yet Slayed" in u for u in res2["unmet_conditions"]))

        # Case 3: Level 30 with planetary boss down but mastery 749
        p3 = {
            "level": 30,
            "class_tier": 3,
            "planetary_boss_defeated": True,
            "skills": {"Aether-Weaving": 749}
        }
        res3 = mechanics.check_evolution_eligibility(p3)
        self.assertFalse(res3["eligible"], "Level 30 with mastery 749 must be ineligible for Tier 4.")
        self.assertTrue(any("Mastery 749 / 750" in u for u in res3["unmet_conditions"]))

        # Case 4: Level 30 with planetary boss down and mastery 750 (exact boundary)
        p4 = {
            "level": 30,
            "class_tier": 3,
            "planetary_boss_defeated": True,
            "skills": {"Aether-Weaving": 750}
        }
        res4 = mechanics.check_evolution_eligibility(p4)
        self.assertTrue(res4["eligible"], "Level 30 with planetary boss down and mastery 750 must be eligible for Tier 4.")
        self.assertEqual(res4["target_tier"], 4)

        # Case 5: Already Tier 4 -> max tier capped
        p5 = {
            "level": 35,
            "class_tier": 4,
            "planetary_boss_defeated": True,
            "skills": {"Aether-Weaving": 1000}
        }
        res5 = mechanics.check_evolution_eligibility(p5)
        self.assertFalse(res5["eligible"], "Tier 4 characters cannot evolve further.")
        self.assertIn("Maximum class evolution tier reached.", res5["reasons"])


class TestDualTrackTelemetrySynthesisStress(unittest.TestCase):
    """Adversarially stress-tests dual-track telemetry synthesis, cold-starts, and anchors."""

    CLASSIC_10 = [
        "fighter", "wizard", "rogue", "cleric", "ranger",
        "paladin", "druid", "bard", "barbarian", "monk"
    ]

    HOLY_KEYWORDS = [
        "radiant", "templar", "protector", "crusader", "dawn",
        "luminary", "sun", "hymn", "beacon"
    ]

    NECRO_KEYWORDS = [
        "deathknight", "blood", "shadow", "dread", "shadowmancer",
        "blight", "dirge", "desecrator"
    ]

    def test_holy_telemetry_across_all_10_classes(self):
        """Verify that Holy damage / dialogue player produces Holy/Radiant evolution choice across all 10 classes."""
        for c_key in self.CLASSIC_10:
            player = {
                "class": c_key,
                "level": 10,
                "sector_boss_defeated": True,
                "telemetry": {
                    "combat_discipline": {"holy_radiant_damage_dealt": 800},
                    "moral_choices": {"good_compassionate_dialogues": 12},
                    "spells_cast": {"holy_radiant": 25}
                }
            }
            choices = mechanics.generate_curated_evolutions(player)
            self.assertEqual(len(choices), 3, f"Expected 3 choices for {c_key}, got {len(choices)}")
            alignment_choice = choices[1]
            self.assertEqual(alignment_choice["category"], "Moral & Ethical Alignment")
            title_lower = alignment_choice["title"].lower()
            desc_lower = alignment_choice["desc"].lower()
            matched_keyword = any(k in title_lower or k in desc_lower for k in self.HOLY_KEYWORDS)
            self.assertTrue(
                matched_keyword,
                f"Class {c_key} Holy choice '{alignment_choice['title']}' missing holy/radiant keywords: {self.HOLY_KEYWORDS}"
            )

    def test_necrotic_telemetry_across_all_10_classes(self):
        """Verify that Necrotic damage / dialogue player produces Necrotic/Deathknight choice across all 10 classes."""
        for c_key in self.CLASSIC_10:
            player = {
                "class": c_key,
                "level": 10,
                "sector_boss_defeated": True,
                "telemetry": {
                    "combat_discipline": {"necrotic_curse_damage_dealt": 800},
                    "moral_choices": {"evil_ruthless_dialogues": 12},
                    "spells_cast": {"necrotic_curse": 25}
                }
            }
            choices = mechanics.generate_curated_evolutions(player)
            self.assertEqual(len(choices), 3, f"Expected 3 choices for {c_key}, got {len(choices)}")
            alignment_choice = choices[1]
            self.assertEqual(alignment_choice["category"], "Moral & Ethical Alignment")
            title_lower = alignment_choice["title"].lower()
            desc_lower = alignment_choice["desc"].lower()
            matched_keyword = any(k in title_lower or k in desc_lower for k in self.NECRO_KEYWORDS)
            self.assertTrue(
                matched_keyword,
                f"Class {c_key} Necrotic choice '{alignment_choice['title']}' missing necrotic/deathknight keywords: {self.NECRO_KEYWORDS}"
            )

    def test_cold_start_player_with_no_telemetry_dict(self):
        """Stress-test cold-start players with zero telemetry producing valid 3 choices without KeyError."""
        test_classes = self.CLASSIC_10 + ["warrior", "vanguard", "mage", "thief", "engineer", "psion", "pathless"]

        for c_key in test_classes:
            # Minimal cold-start player
            player = {"class": c_key, "level": 10}
            try:
                choices = mechanics.generate_curated_evolutions(player)
            except KeyError as ke:
                self.fail(f"generate_curated_evolutions raised KeyError for cold-start {c_key}: {ke}")
            except Exception as exc:
                self.fail(f"generate_curated_evolutions raised {type(exc).__name__} for cold-start {c_key}: {exc}")

            self.assertEqual(len(choices), 3, f"Cold-start {c_key} must produce exactly 3 choices")
            for idx, ch in enumerate(choices):
                self.assertIn("title", ch, f"Cold-start {c_key} choice {idx} missing 'title'")
                self.assertIn("desc", ch, f"Cold-start {c_key} choice {idx} missing 'desc'")
                self.assertIn("category", ch, f"Cold-start {c_key} choice {idx} missing 'category'")
                self.assertEqual(ch.get("tier"), 2, f"Cold-start {c_key} choice {idx} tier must be 2")

    def test_monstrous_lineage_racial_anchor_options(self):
        """Verify that monstrous lineage players receive their tailored racial anchor as Choice 3."""
        monstrous_lineages = [
            ("minotaur_labyrinth_reaver", "Minotaur Bull-Reaver"),
            ("dnd_pixie", "Pixie Arcane Trickster"),
            ("woodland_satyr", "Satyr Sylvan Skald"),
            ("meadow_nymph", "Meadow Nymph Grace-Binder"),
            ("gargoyle_stalker", "Gargoyle Stone-Reaver"),
            ("centaur_outrunner", "Centaur Heavy Dragoon"),
            ("feral_troll", "Feral Troll Regenerator"),
            ("troll_kreen_chimera", "Feral Troll Regenerator"),
            ("medusa_gorgon", "Gorgon Stone-Gazer"),
            ("half_ogre", "Ogre Crag-Crusher"),
            ("dragon_kobold", "Dragon-Blooded Wyrm-Scion"),
            ("hyena_gnoll", "Hyena Pack-Stalker"),
        ]

        for r_key, expected_title in monstrous_lineages:
            player = {
                "class": "fighter",
                "race_key": r_key,
                "level": 10,
                "sector_boss_defeated": True
            }
            choices = mechanics.generate_curated_evolutions(player)
            choice3 = choices[2]
            self.assertEqual(
                choice3["category"], "Unique Deed & Relic Anchor",
                f"Choice 3 category should be 'Unique Deed & Relic Anchor' for {r_key}"
            )
            self.assertEqual(
                choice3["title"], expected_title,
                f"Racial anchor mismatch for {r_key}: expected {expected_title!r}, got {choice3['title']!r}"
            )

    def test_relic_and_deed_anchors_for_standard_races(self):
        """Verify that non-monstrous characters receive relic and deed anchors in Choice 3."""
        relic_test_matrix = [
            ("smartphone", "Old-World Echo Agent"),
            ("rangefinder", "Hawkeye Ballistician"),
            ("camera", "Hawkeye Ballistician"),
            ("tuning_fork", "Aetheric Resonator Adept"),
            ("whetstone", "Relic-Bound Chrono-Warden"),
            ("compass", "Relic-Bound Chrono-Warden"),
            ("locket", "Relic-Bound Chrono-Warden"),
        ]

        for relic_name, expected_title in relic_test_matrix:
            player = {
                "class": "fighter",
                "race": "Human",
                "level": 10,
                "sector_boss_defeated": True,
                "inventory": [relic_name]
            }
            choices = mechanics.generate_curated_evolutions(player)
            choice3 = choices[2]
            self.assertEqual(
                choice3["title"], expected_title,
                f"Relic anchor mismatch for relic '{relic_name}': expected '{expected_title}', got '{choice3['title']}'"
            )

        deed_test_matrix = [
            ("spared_cultist", "Compassionate Arbiter"),
            ("desecrated_shrine", "Defiler of Sacred Altars"),
            ("consecrated_altar", "Spire Consecrator"),
            ("spire_overlord_slain", "Spire Breaker Champion"),
        ]

        for deed_name, expected_title in deed_test_matrix:
            player = {
                "class": "fighter",
                "race": "Human",
                "level": 10,
                "sector_boss_defeated": True,
                "deeds": [deed_name]
            }
            choices = mechanics.generate_curated_evolutions(player)
            choice3 = choices[2]
            self.assertEqual(
                choice3["title"], expected_title,
                f"Deed anchor mismatch for deed '{deed_name}': expected '{expected_title}', got '{choice3['title']}'"
            )


class TestResourceScalingAndApotheosisStress(unittest.TestCase):
    """Stress-tests resource pool scaling and multi-tier apotheosis transitions."""

    CLASSIC_10 = [
        "fighter", "wizard", "rogue", "cleric", "ranger",
        "paladin", "druid", "bard", "barbarian", "monk"
    ]

    def test_resource_scaling_across_all_10_classes(self):
        """Verify apply_class_evolution scales resource pools correctly (+25% T2, +50% T3, +100% T4) across all 10 classes."""
        for c_key in self.CLASSIC_10:
            char = cg.generate_starting_character(name=f"Scale_{c_key}", class_key=c_key, start_tutorial=False)
            player = char.get("player", char)
            base_max = player["combat_resource"]["max"]

            # Tier 2 Application (+25%)
            t2_choice = {
                "title": f"Evolved {c_key.title()} T2",
                "tier": 2,
                "category": "Discipline Synergy",
                "desc": "Tier 2 evolution"
            }
            mechanics.apply_class_evolution(player, t2_choice)
            expected_t2 = int(base_max * 1.25)
            self.assertEqual(
                player["combat_resource"]["max"], expected_t2,
                f"Class {c_key} T2 resource scaling mismatch: expected {expected_t2}, got {player['combat_resource']['max']}"
            )
            self.assertEqual(player["class_tier"], 2)

            # Tier 3 Application (+50%)
            t3_choice = {
                "title": f"Prestige {c_key.title()} T3",
                "tier": 3,
                "category": "Prestige Branch",
                "desc": "Tier 3 prestige"
            }
            mechanics.apply_class_evolution(player, t3_choice)
            expected_t3 = int(expected_t2 * 1.50)
            self.assertEqual(
                player["combat_resource"]["max"], expected_t3,
                f"Class {c_key} T3 resource scaling mismatch: expected {expected_t3}, got {player['combat_resource']['max']}"
            )
            self.assertEqual(player["class_tier"], 3)

            # Tier 4 Application (+100%)
            t4_choice = {
                "title": f"Apex {c_key.title()} T4",
                "tier": 4,
                "category": "Apex Apotheosis",
                "desc": "Tier 4 apex"
            }
            mechanics.apply_class_evolution(player, t4_choice)
            expected_t4 = int(expected_t3 * 2.00)
            self.assertEqual(
                player["combat_resource"]["max"], expected_t4,
                f"Class {c_key} T4 resource scaling mismatch: expected {expected_t4}, got {player['combat_resource']['max']}"
            )
            self.assertEqual(player["class_tier"], 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
