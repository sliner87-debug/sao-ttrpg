"""
Test Suite: Dreamscarred Press (DSP) Expanded Psionics Engine
Validates:
1. Aegis Astral Suit forms (Skin, Armor, Juggernaut) and Customization Points (CP) budget.
2. Astral Suit reconfigurations (Flight, Extra Arms, Hardened Carapace, Reach).
3. The Collective Network (initialization, member limits, party joining, and Transfer Wounds).
4. DSP Base Classes (Aegis, Vitalist, Tactician, Cryptic, Dread, Marksman) in CLASS_PATHS.
5. DSP Psionic Races (Ophiduan, Forgeborn, Blue, Duergar Psionic).
6. Backward compatibility with multi-limb grafts and monstrous chimera profiles.
"""

import unittest
from backend import mechanics
from backend import psionics_dsp
from backend import character_generator as cg


class TestPsionicsDSPExpanded(unittest.TestCase):
    def setUp(self):
        self.aegis_player = {
            "name": "Baron",
            "class": "aegis",
            "level": 6,
            "stats": {"STR": 16, "DEX": 12, "CON": 16, "INT": 16, "WIS": 10, "CHA": 8},
            "combat_resource": {"name": "Customization Points & PP", "current": 9, "max": 9, "type": "customization_points"},
            "astral_suit": {
                "form": "astral_armor",
                "customizations": ["hardened_carapace"]
            }
        }
        self.vitalist_player = {
            "name": "Dr. Sarah",
            "class": "vitalist",
            "level": 5,
            "hp": 30,
            "max_hp": 45,
            "stats": {"STR": 10, "DEX": 14, "CON": 14, "INT": 12, "WIS": 18, "CHA": 10},
            "collective": {
                "members": ["Dr. Sarah"],
                "max_size": 9
            },
            "party": {
                "Ren Sasaki": {"active": True, "hp": 40, "max_hp": 60},
                "Sister Teresa": {"active": True, "hp": 25, "max_hp": 50}
            }
        }

    def test_aegis_customization_points_budget(self):
        # Level 1: 3 CP
        self.assertEqual(psionics_dsp.calculate_aegis_customization_points({"level": 1, "class": "aegis"}), 3)
        # Level 6: 9 CP
        self.assertEqual(psionics_dsp.calculate_aegis_customization_points(self.aegis_player), 9)
        # Level 20: 26 CP
        self.assertEqual(psionics_dsp.calculate_aegis_customization_points({"level": 20, "class": "aegis"}), 26)
        # Level 100: 110 CP
        self.assertEqual(psionics_dsp.calculate_aegis_customization_points({"level": 100, "class": "aegis"}), 110)

    def test_astral_suit_configuration(self):
        # Reconfigure suit into Astral Juggernaut with flight and extra arms
        # Juggernaut + Flight (2 CP) + Extra Arms (2 CP) + Carapace (1 CP) = 5 CP <= 9 CP
        res = psionics_dsp.configure_astral_suit(
            self.aegis_player,
            form_mode="astral_juggernaut",
            customizations=["flight", "extra_arms", "hardened_carapace"]
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["form"], "astral_juggernaut")
        self.assertEqual(res["armor_bonus"], 10)
        self.assertEqual(res["dr"], "5/-")
        self.assertEqual(res["size"], "Large")
        self.assertEqual(res["cp_spent"], 5)
        self.assertIn("extra_arms", self.aegis_player["astral_suit"]["customizations"])

    def test_astral_suit_over_budget_rejected(self):
        # Level 1 has only 3 CP. Attempting 5 CP customizations must fail.
        low_aegis = {"level": 1, "class": "aegis", "astral_suit": {}}
        res = psionics_dsp.configure_astral_suit(
            low_aegis,
            form_mode="astral_armor",
            customizations=["flight", "extra_arms", "energy_resistance"]
        )
        self.assertFalse(res["success"])
        self.assertIn("insufficient Customization Points", res["message"])

    def test_collective_network_initialization_and_joining(self):
        p = {"level": 3, "stats": {"WIS": 16}, "collective": None}
        coll = psionics_dsp.init_collective(p)
        self.assertIsNotNone(coll)
        # Max size = Level (3) + WIS Mod (3) = 6
        self.assertEqual(coll["max_size"], 6)

        # Join companions
        join_res = psionics_dsp.join_collective(self.vitalist_player, "Ren Sasaki")
        self.assertTrue(join_res["success"])
        self.assertIn("Ren Sasaki", self.vitalist_player["collective"]["members"])

    def test_transfer_wounds(self):
        # Sarah is at 30/45 HP. Ren is willing to give 10 HP.
        source = {"name": "Ren Sasaki", "hp": 40, "max_hp": 60}
        target = self.vitalist_player
        
        tw_res = psionics_dsp.transfer_wounds(source, target, amount=10)
        self.assertTrue(tw_res["success"])
        self.assertEqual(source["hp"], 30)
        self.assertEqual(target["hp"], 40)

    def test_dsp_classes_catalog(self):
        for c_key in ["aegis", "vitalist", "tactician", "cryptic", "dread", "marksman"]:
            self.assertIn(c_key, cg.CLASS_PATHS)
            cls_obj = cg.CLASS_PATHS[c_key]
            self.assertIn("title", cls_obj)
            self.assertIn("starting_feats", cls_obj)
            self.assertIn(c_key, cg.CLASS_WEAPONS)
            self.assertEqual(mechanics.normalize_class_key(c_key), c_key)

    def test_dsp_races_catalog(self):
        for r_key in ["ophiduan", "forgeborn", "blue", "duergar_psionic"]:
            self.assertIn(r_key, cg.RACIAL_LINEAGES)
            race_obj = cg.RACIAL_LINEAGES[r_key]
            self.assertEqual(race_obj["genre"], "Dreamscarred Press Psionic Lineage")
            self.assertIn(r_key, cg.RACIAL_PHYSICAL_DEFAULTS)

        # Blue size Small and stealth bonus
        blue = cg.RACIAL_LINEAGES["blue"]
        self.assertEqual(blue.get("size"), "Small")

        # Ophiduan Venomous bite
        oph = cg.RACIAL_LINEAGES["ophiduan"]
        self.assertTrue(any("Venomous Bite" in ab for ab in oph["racial_abilities"]))

    def test_glenny_chimera_backward_compatibility(self):
        # Glenny's 4-armed chimera profile
        glenny = {
            "name": "Glenny",
            "class": "fighter",
            "race": "Spliced Apex Chimera",
            "race_key": cg.CHIMERA_RACE_KEY,
            "chimera_choices": {
                "base_bloodline": "troll_fleshwarped",
                "upper_limbs": "human_arms",
                "lower_limbs": "thrikreen_arms",
                "carapace": "gargoyle_stone",
                "head": "minotaur_horns"
            },
            "equipped": {
                "main_hand": "Heavy Scavenged Mace",
                "off_hand": "Scrap-Plate Shield",
                "lower_main_hand": "Tanto Combat Knife",
                "lower_off_hand": "None"
            }
        }
        res_lineage = cg.resolve_racial_lineage(glenny["race_key"], glenny["chimera_choices"])
        self.assertIsNotNone(res_lineage)
        self.assertIn("Spliced Apex Chimera", res_lineage["name"])
        self.assertEqual(glenny["equipped"]["lower_main_hand"], "Tanto Combat Knife")


if __name__ == "__main__":
    unittest.main()
