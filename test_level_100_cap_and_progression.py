"""
Test Suite: Level 100 Cap & Multi-Tier Progression Continuum
Validates:
1. XP progression formula across levels 1 to 100, clamping at level 100.
2. Free attribute points (+2/lvl) and archetype HP growth.
3. 10-Tier class evolution continuum (Tiers 1 to 10).
4. Tier evolution resource multipliers and matrix memory slot scaling.
"""

import unittest
import copy
from backend import mechanics
from backend import character_generator as cg


class TestLevel100Progression(unittest.TestCase):
    def setUp(self):
        self.player = {
            "name": "Glenny",
            "class": "fighter",
            "level": 1,
            "hp": 135,
            "max_hp": 135,
            "xp": 0,
            "stats": {"STR": 16, "DEX": 14, "CON": 16, "INT": 12, "WIS": 12, "CHA": 10},
            "free_attribute_points": 0,
            "bosses_defeated": [],
            "skills": {
                "One-Handed Edge": {"mastery": 50, "tier": "Apprentice"}
            },
            "feats": []
        }

    def test_max_level_constant(self):
        self.assertEqual(mechanics.MAX_PLAYER_LEVEL, 100)

    def test_xp_curve_levels_1_to_100(self):
        # Level 1 required XP
        xp_l1 = mechanics.calculate_player_next_level_xp(1)
        self.assertEqual(xp_l1, 1000)

        # Level 10 required XP
        xp_l10 = mechanics.calculate_player_next_level_xp(10)
        self.assertGreater(xp_l10, 10000)
        self.assertLess(xp_l10, 50000)

        # Level 50 required XP
        xp_l50 = mechanics.calculate_player_next_level_xp(50)
        self.assertGreater(xp_l50, 300000)

        # Level 99 required XP
        xp_l99 = mechanics.calculate_player_next_level_xp(99)
        self.assertGreater(xp_l99, 1000000)

        # Level 100 (Max Level) returns 0
        xp_l100 = mechanics.calculate_player_next_level_xp(100)
        self.assertEqual(xp_l100, 0)

    def test_level_up_to_100_cap(self):
        p = copy.deepcopy(self.player)
        
        # Level up once
        res = mechanics.apply_level_up(p)
        self.assertEqual(p["level"], 2)
        self.assertEqual(res["new_level"], 2)
        self.assertEqual(p["free_attribute_points"], 2)
        self.assertGreater(p["max_hp"], 135)

        # Set level to 99 and level up to 100
        p["level"] = 99
        res_99 = mechanics.apply_level_up(p)
        self.assertEqual(p["level"], 100)
        self.assertTrue(res_99["max_level_reached"])

        # Attempt to level up beyond 100
        res_100 = mechanics.apply_level_up(p)
        self.assertEqual(p["level"], 100)
        self.assertEqual(res_100["hp_gain"], 0)
        self.assertTrue(res_100["max_level_reached"])

    def test_tier_names_continuum(self):
        self.assertIn("Tier 1", mechanics.get_class_tier_name(1))
        self.assertIn("Tier 2", mechanics.get_class_tier_name(15))
        self.assertIn("Tier 3", mechanics.get_class_tier_name(25))
        self.assertIn("Tier 4", mechanics.get_class_tier_name(35))
        self.assertIn("Tier 5", mechanics.get_class_tier_name(45))
        self.assertIn("Tier 6", mechanics.get_class_tier_name(55))
        self.assertIn("Tier 7", mechanics.get_class_tier_name(65))
        self.assertIn("Tier 8", mechanics.get_class_tier_name(75))
        self.assertIn("Tier 9", mechanics.get_class_tier_name(85))
        self.assertIn("Tier 10", mechanics.get_class_tier_name(95))
        self.assertIn("Tier 10", mechanics.get_class_tier_name(100))

    def test_tier_evolution_eligibility(self):
        p = copy.deepcopy(self.player)
        
        # Level 1 is Tier 1
        elig = mechanics.check_evolution_eligibility(p)
        self.assertFalse(elig["eligible"])
        self.assertEqual(elig["current_tier"], 1)

        # Level 10 without boss defeated
        p["level"] = 10
        p["skills"]["One-Handed Edge"]["mastery"] = 100
        elig = mechanics.check_evolution_eligibility(p)
        self.assertFalse(elig["eligible"])
        self.assertTrue(any("Spire Boss" in c for c in elig["unmet_conditions"]))

        # Defeat boss -> eligible for Tier 2
        p["bosses_defeated"] = ["spire_boss_1"]
        elig = mechanics.check_evolution_eligibility(p)
        self.assertTrue(elig["eligible"])
        self.assertEqual(elig["target_tier"], 2)

        # Evolve to Tier 2
        ev_res = mechanics.apply_class_evolution(p, "Fighter (Ironclad Vanguard)", 2)
        self.assertTrue(ev_res["success"])
        self.assertEqual(p["class_tier"], 2)

        # Check Tier 5 (Level 40)
        p["level"] = 40
        p["bosses_defeated"].extend(["regional_boss", "planetary_boss", "rift_lord"])
        p["skills"]["One-Handed Edge"]["mastery"] = 900
        elig_t5 = mechanics.check_evolution_eligibility(p)
        self.assertTrue(elig_t5["eligible"])
        self.assertEqual(elig_t5["target_tier"], 5)

        # Evolve to Tier 5
        ev_t5 = mechanics.apply_class_evolution(p, "Dimensional Sovereign", 5)
        self.assertTrue(ev_t5["success"])
        self.assertEqual(p["class_tier"], 5)
        self.assertGreaterEqual(p["combat_resource"]["max"], 200)

        # Check Tier 10 (Level 95)
        p["level"] = 95
        p["bosses_defeated"].extend(["stellar_arbiter", "astral_architect", "primordial_ascendant", "chronos_weaver", "ouroboros_godhead"])
        p["skills"]["One-Handed Edge"]["mastery"] = 1000
        elig_t10 = mechanics.check_evolution_eligibility(p)
        self.assertTrue(elig_t10["eligible"])
        self.assertEqual(elig_t10["target_tier"], 10)


if __name__ == "__main__":
    unittest.main()
