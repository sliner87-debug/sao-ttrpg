import os
import shutil
import unittest

from backend import character_generator as cg, mechanics

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ZERO = {s: 0 for s in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]}


def _p(age=25, h=70, w=185, **extra):
    d = {"physical": {"age": age, "height_in": h, "weight_lbs": w}, "stats": {"STR": 10, "DEX": 10}}
    d.update(extra)
    return d


class TestPhysicalProfile(unittest.TestCase):
    created = []

    @classmethod
    def tearDownClass(cls):
        for n in cls.created:
            shutil.rmtree(cg.get_character_save_dir(BASE_DIR, n), ignore_errors=True)

    def _make(self, name, physical, race="pure_human"):
        self.created.append(name)
        return cg.generate_starting_character(name, ZERO, "software_engineer", race, "warrior", "smartphone", physical=physical)

    def test_legacy_save_has_no_modifiers(self):
        prof = mechanics.get_physical_profile({"stats": {"STR": 10}})
        self.assertEqual((prof["size"], prof["build"], prof["age_bracket"]), ("Medium", "Average", "Prime"))
        self.assertEqual(prof["effects"], [])

    def test_size_brackets(self):
        self.assertEqual(mechanics.get_physical_profile(_p(h=47, w=60))["size"], "Small")
        self.assertEqual(mechanics.get_physical_profile(_p(h=48, w=80))["size"], "Medium")
        self.assertEqual(mechanics.get_physical_profile(_p(h=84, w=300))["size"], "Medium")
        self.assertEqual(mechanics.get_physical_profile(_p(h=85, w=300))["size"], "Large")

    def test_build_brackets(self):
        self.assertEqual(mechanics.get_physical_profile(_p(h=70, w=120))["build"], "Lean")
        self.assertEqual(mechanics.get_physical_profile(_p(h=70, w=185))["build"], "Average")
        self.assertEqual(mechanics.get_physical_profile(_p(h=70, w=240))["build"], "Heavy")

    def test_age_brackets(self):
        for age, br in ((17, "Youth"), (20, "Prime"), (39, "Prime"), (40, "Veteran"), (59, "Veteran"), (60, "Elder")):
            self.assertEqual(mechanics.get_physical_profile(_p(age=age))["age_bracket"], br)

    def test_carry_capacity_scales_with_size(self):
        med = mechanics.calculate_encumbrance(_p())["max_weight_lbs"]
        small = mechanics.calculate_encumbrance(_p(h=44, w=60))["max_weight_lbs"]
        large = mechanics.calculate_encumbrance(_p(h=96, w=400))["max_weight_lbs"]
        self.assertEqual(med, 150.0)
        self.assertEqual(small, 112.5)
        self.assertEqual(large, 225.0)

    def test_ac_size_modifier(self):
        base = {"stats": {"STR": 10, "DEX": 14}, "equipped": {"chest": "Leather Jerkin"}}
        med = mechanics.calculate_ac(dict(base, physical={"age": 25, "height_in": 70, "weight_lbs": 185}))
        small = mechanics.calculate_ac(dict(base, physical={"age": 25, "height_in": 44, "weight_lbs": 60}))
        large = mechanics.calculate_ac(dict(base, physical={"age": 25, "height_in": 96, "weight_lbs": 400}))
        self.assertEqual(small - med, 1)
        self.assertEqual(large - med, -1)

    def test_youth_mastery_bonus_accumulates(self):
        youth = _p(age=17, skills={"Perception": {"mastery": 10, "tier": "Novice", "description": "", "milestones_unlocked": []}})
        prime = _p(age=25, skills={"Perception": {"mastery": 10, "tier": "Novice", "description": "", "milestones_unlocked": []}})
        for _ in range(10):
            mechanics.update_skill_mastery(youth, "Perception", 5)
            mechanics.update_skill_mastery(prime, "Perception", 5)
        self.assertEqual(prime["skills"]["Perception"]["mastery"], 60)
        self.assertEqual(youth["skills"]["Perception"]["mastery"], 65)  # +10% of 50

    def test_creation_hp_modifiers(self):
        prime = self._make("Test_Phys_Prime", {"age": 25, "height_in": 70, "weight_lbs": 185})
        heavy = self._make("Test_Phys_Heavy", {"age": 25, "height_in": 70, "weight_lbs": 240})
        elder = self._make("Test_Phys_Elder", {"age": 65, "height_in": 70, "weight_lbs": 185})
        vet = self._make("Test_Phys_Vet", {"age": 45, "height_in": 70, "weight_lbs": 185})
        self.assertEqual(heavy["max_hp"] - prime["max_hp"], 10)
        self.assertEqual(elder["max_hp"], int(round(prime["max_hp"] * 0.90)))
        self.assertEqual(vet["max_hp"], int(round(prime["max_hp"] * 0.95)))
        self.assertEqual(heavy["physical"], {"age": 25, "height_in": 70, "weight_lbs": 240})

    def test_veteran_and_elder_starting_mastery(self):
        prime = self._make("Test_Phys_Prime2", {"age": 25, "height_in": 70, "weight_lbs": 185})
        vet = self._make("Test_Phys_Vet2", {"age": 45, "height_in": 70, "weight_lbs": 185})
        elder = self._make("Test_Phys_Elder2", {"age": 70, "height_in": 70, "weight_lbs": 185})
        bg_skills = list(cg.PRESET_BACKGROUNDS["software_engineer"]["skills"].keys())
        for s in bg_skills:
            p_m = prime["skills"][s]["mastery"]
            self.assertEqual(vet["skills"][s]["mastery"], min(1000, p_m + 15))
            self.assertEqual(elder["skills"][s]["mastery"], min(1000, p_m + 30))

    def test_preview_hp_matches_generator(self):
        phys = {"age": 62, "height_in": 70, "weight_lbs": 260}
        p = self._make("Test_Phys_Preview", phys)
        race = cg.resolve_racial_lineage("pure_human")
        self.assertEqual(cg.compute_starting_max_hp(race, cg.CLASS_PATHS["warrior"], p["stats"], phys), p["max_hp"])

    def test_floor_hazard_uses_player_body_weight(self):
        env = {"location": "Rotted timber catwalk", "description": "rotted timber walkway", "environmental_effects": []}
        light = mechanics.evaluate_party_environmental_physics(_p(h=70, w=185, party={}), dict(env))
        huge = mechanics.evaluate_party_environmental_physics(_p(h=108, w=900, party={}), dict(env))
        self.assertGreater(huge["total_party_weight_lbs"], light["total_party_weight_lbs"] + 700)
        self.assertTrue(huge["hazard_triggered"])

    def test_gm_visual_manifest_includes_body(self):
        m = mechanics.build_scene_visual_manifest(player_state=dict(_p(age=19, h=96, w=500), name="Test", equipped={}))
        self.assertIn("BODY: 19 years old", m)
        self.assertIn("Large", m)


if __name__ == "__main__":
    unittest.main()
