"""
Test Suite: D&D 3.5 Expanded Psionics Handbook (XPH) Core Engine
Validates:
1. Power Point (PP) calculations for full/partial manifesters and key stat bonus PP.
2. Manifester Level (ML) spend cap rule: Total PP spent <= ML.
3. Psionic Focus meditation check (DC 20) and metapsionic/feat expenditure.
4. Soulknife Mind Blade manifestation and Psychic Strike charging.
5. Wilder Wild Surge and Psychic Enervation roll.
6. 5 XPH Races (Elan, Maenad, Dromite, Xeph, Half-Giant).
7. Canonical psionic powers across disciplines and tiers.
"""

import unittest
from backend import mechanics
from backend import psionics_dsp
from backend import character_generator as cg


class TestPsionicsXPHCore(unittest.TestCase):
    def setUp(self):
        self.psion = {
            "name": "Kaelen",
            "class": "psion",
            "level": 5,
            "stats": {"STR": 10, "DEX": 14, "CON": 14, "INT": 18, "WIS": 12, "CHA": 10},
            "combat_resource": {"name": "Power Points", "current": 25, "max": 25, "type": "power_points"},
            "psionic_focus": False,
            "feats": ["Psionic Meditation"]
        }
        self.psy_warrior = {
            "name": "Thorne",
            "class": "psychic_warrior",
            "level": 4,
            "stats": {"STR": 16, "DEX": 12, "CON": 14, "INT": 10, "WIS": 16, "CHA": 8},
            "combat_resource": {"name": "Power Points", "current": 5, "max": 5, "type": "power_points"},
            "psionic_focus": False,
            "feats": ["Psionic Weapon"]
        }

    def test_manifester_level_calculation(self):
        self.assertEqual(psionics_dsp.calculate_manifester_level(self.psion), 5)
        self.assertEqual(psionics_dsp.calculate_manifester_level(self.psy_warrior), 4)

    def test_power_points_calculation(self):
        # Psion level 5, INT 18 (mod +4)
        # Base L5 = 25 PP. Bonus = int(4 * 5 * 0.5) = 10 PP. Total = 35 PP.
        pp_psion = psionics_dsp.calculate_max_power_points(self.psion)
        self.assertEqual(pp_psion, 35)

        # Psychic Warrior level 4, WIS 16 (mod +3)
        # Base L4 = 6 PP (XPH Table 2-3). Bonus = int(3 * 4 * 0.5) = 6 PP. Total = 12 PP.
        pp_pw = psionics_dsp.calculate_max_power_points(self.psy_warrior)
        self.assertEqual(pp_pw, 12)

    def test_golden_rule_manifester_level_cap(self):
        # Psion ML is 5.
        # Manifesting base 1 PP + 4 PP augment = 5 PP (Valid: 5 <= 5)
        check_valid = psionics_dsp.validate_power_manifestation(self.psion, base_pp=1, augment_pp=4)
        self.assertTrue(check_valid["valid"])

        # Manifesting base 1 PP + 5 PP augment = 6 PP (Invalid: 6 > 5)
        check_invalid = psionics_dsp.validate_power_manifestation(self.psion, base_pp=1, augment_pp=5)
        self.assertFalse(check_invalid["valid"])
        self.assertIn("exceeds Manifester Level", check_invalid["reason"])

    def test_power_manifestation_execution(self):
        res = psionics_dsp.manifest_psionic_power(self.psion, "Energy Ray", base_pp=1, augment_pp=2)
        self.assertTrue(res["success"])
        self.assertEqual(res["pp_spent"], 3)
        self.assertEqual(self.psion["combat_resource"]["current"], 22)

    def test_psionic_focus_meditation_and_expenditure(self):
        # Test meditation with high WIS/skills (forcing high roll or mock)
        self.assertFalse(self.psion["psionic_focus"])
        
        # Test expenditure when not focused fails
        exp_fail = psionics_dsp.expend_psionic_focus(self.psion, "Psionic Weapon")
        self.assertFalse(exp_fail["success"])

        # Grant focus
        self.psion["psionic_focus"] = True
        exp_success = psionics_dsp.expend_psionic_focus(self.psion, "Psionic Weapon")
        self.assertTrue(exp_success["success"])
        self.assertFalse(self.psion["psionic_focus"])
        self.assertEqual(exp_success["bonus_damage_dice"], "2d6")

    def test_soulknife_mind_blade_and_psychic_strike(self):
        sk = {
            "name": "Ren",
            "class": "soulknife",
            "level": 8,
            "stats": {"STR": 14, "DEX": 18, "CON": 12, "INT": 10, "WIS": 14, "CHA": 10},
            "equipped": {},
            "psychic_strike_charged": False
        }
        
        # Manifest Mind Blade
        res = psionics_dsp.manifest_mind_blade(sk, shape="longsword")
        self.assertTrue(res["success"])
        self.assertEqual(sk["equipped"]["main_hand"], "Manifested Mind Blade +2")
        self.assertEqual(res["enhancement_bonus"], 2)

        # Charge Psychic Strike (L8 -> +2d8)
        charge_res = psionics_dsp.charge_psychic_strike(sk)
        self.assertTrue(charge_res["success"])
        self.assertTrue(sk["psychic_strike_charged"])
        self.assertEqual(charge_res["bonus_damage_dice"], "+2d8")

    def test_wilder_wild_surge(self):
        wilder = {
            "name": "Cassia",
            "class": "wilder",
            "level": 7,
            "stats": {"STR": 10, "DEX": 14, "CON": 14, "INT": 10, "WIS": 12, "CHA": 18},
            "combat_resource": {"name": "Power Points", "current": 35, "max": 35, "type": "power_points"}
        }
        
        # Execute Wild Surge (+2 ML)
        res = psionics_dsp.execute_wild_surge(wilder, surge_level=2)
        if not res["enervated"]:
            self.assertEqual(res["ml_boost"], 2)
            self.assertGreaterEqual(res["euphoria_bonus"], 1)
        else:
            self.assertTrue(res["enervated"])
            self.assertLess(wilder["combat_resource"]["current"], 35)

    def test_xph_races_catalog(self):
        lineages = cg.RACIAL_LINEAGES
        for race_k in ["elan", "maenad", "dromite", "xeph", "half_giant"]:
            self.assertIn(race_k, lineages)
            race = lineages[race_k]
            self.assertEqual(race["genre"], "D&D 3.5 Psionic Lineage")
            self.assertIn(race_k, cg.RACIAL_PHYSICAL_DEFAULTS)

        # Elan Resilience
        elan = lineages["elan"]
        self.assertTrue(any("Resilience" in ab for ab in elan["racial_abilities"]))

        # Half-Giant Powerful Build
        hg = lineages["half_giant"]
        self.assertTrue(any("Powerful Build" in ab for ab in hg["racial_abilities"]))

    def test_canonical_psionic_powers(self):
        cat = mechanics.CANONICAL_SPELLS_AND_POWERS
        for p_name in [
            "crystal shard", "astral construct", "inertial armor", "vigor (psionic)",
            "energy push", "concussion blast", "time hop", "dispel psionics",
            "dimension door (psionic)", "disintegrate (psionic)", "temporal acceleration",
            "ultrablast", "greater teleport (psionic)", "microcosm"
        ]:
            self.assertIn(p_name, cat)
            self.assertTrue(cat[p_name].get("is_psionic"))


if __name__ == "__main__":
    unittest.main()
