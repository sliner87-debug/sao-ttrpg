import unittest
from backend import character_generator as cg, mechanics

class TestMonstrousRaces(unittest.TestCase):
    def test_total_race_count(self):
        self.assertGreaterEqual(len(cg.RACIAL_LINEAGES), 70)

    def test_explicitly_requested_monsters(self):
        # 1. Troll
        self.assertIn("troll_fleshwarped", cg.RACIAL_LINEAGES)
        troll = cg.RACIAL_LINEAGES["troll_fleshwarped"]
        self.assertEqual(troll["stat_mods"]["STR"], 4)
        self.assertEqual(troll["stat_mods"]["CON"], 4)
        self.assertTrue(any("Regeneration" in a for a in troll["racial_abilities"]))
        self.assertTrue(any("Rending Talons" in a for a in troll["racial_abilities"]))
        self.assertTrue(any("Fire Vulnerability" in a for a in troll["racial_abilities"]))

        # 2. Illithid
        self.assertIn("illithid_mind_flayer", cg.RACIAL_LINEAGES)
        illithid = cg.RACIAL_LINEAGES["illithid_mind_flayer"]
        self.assertEqual(illithid["stat_mods"]["INT"], 4)
        self.assertTrue(any("Mind Blast" in a for a in illithid["racial_abilities"]))
        self.assertTrue(any("Tentacle Grapple" in a for a in illithid["racial_abilities"]))
        self.assertTrue(any("Telepathic Net" in a for a in illithid["racial_abilities"]))

        # 3. Orc
        self.assertIn("mountain_orc_blood", cg.RACIAL_LINEAGES)
        orc = cg.RACIAL_LINEAGES["mountain_orc_blood"]
        self.assertEqual(orc["stat_mods"]["STR"], 4)
        self.assertTrue(any("Aggressive Rush" in a for a in orc["racial_abilities"]))
        self.assertTrue(any("Relentless Juggernaut" in a for a in orc["racial_abilities"]))

        # 4. Goblin
        self.assertIn("goblin_pyromaniac", cg.RACIAL_LINEAGES)
        goblin = cg.RACIAL_LINEAGES["goblin_pyromaniac"]
        self.assertEqual(goblin["stat_mods"]["DEX"], 4)
        self.assertTrue(any("Nimble Escape" in a for a in goblin["racial_abilities"]))
        self.assertTrue(any("Fury of the Small" in a for a in goblin["racial_abilities"]))

        # 5. Kobold
        self.assertIn("kobold_dragon_herald", cg.RACIAL_LINEAGES)
        kobold = cg.RACIAL_LINEAGES["kobold_dragon_herald"]
        self.assertEqual(kobold["stat_mods"]["DEX"], 3)
        self.assertEqual(kobold["stat_mods"]["CHA"], 3)
        self.assertTrue(any("Draconic Roar" in a for a in kobold["racial_abilities"]))
        self.assertTrue(any("Pack Hunter Telemetry" in a for a in kobold["racial_abilities"]))

    def test_additional_monstrous_lineages(self):
        monsters = [
            "bugbear_shadow_stalker",
            "gnoll_hyena_ravager",
            "minotaur_labyrinth_breaker",
            "half_ogre_crusher",
            "medusa_gorgon_scion",
            "gargoyle_lithic_sentinel",
            "troglodyte_stench_stalker",
            "doppelganger_morph",
            "hag_born_caliban",
            "grung_tree_frog",
            "were_kin_shifter",
            "centaur_plains_vanguard",
            "thrikreen_mantis",
            "satyr_fey_reveler",
            "sahuagin_blood_frenzy",
            "grimlock_blindsight",
            "rust_monster_kin",
            "derro_deep_savant",
            "harpy_siren_reaver",
            "rakshasa_tiger_lord"
        ]
        for m in monsters:
            self.assertIn(m, cg.RACIAL_LINEAGES, f"Missing monster race {m}")
            race_obj = cg.RACIAL_LINEAGES[m]
            self.assertIn("name", race_obj)
            self.assertIn("genre", race_obj)
            self.assertIn("desc", race_obj)
            self.assertIn("stat_mods", race_obj)
            self.assertIn("racial_abilities", race_obj)
            self.assertGreaterEqual(len(race_obj["racial_abilities"]), 3)

    def test_character_generation_with_monstrous_races(self):
        test_races = ["troll_fleshwarped", "illithid_mind_flayer", "mountain_orc_blood", "goblin_pyromaniac", "kobold_dragon_herald"]
        for r_key in test_races:
            avatar = cg.generate_starting_character(
                name=f"Test_{r_key}",
                point_alloc={"STR": 4, "DEX": 2, "CON": 4, "INT": 0, "WIS": 0, "CHA": 0},
                background_key="software_engineer",
                race_key=r_key,
                class_key="warrior",
                relic_key="brass_zippo"
            )
            self.assertEqual(avatar["race"], cg.RACIAL_LINEAGES[r_key]["name"])
            self.assertGreater(avatar["hp"], 0)
            self.assertGreaterEqual(len(avatar["racial_abilities"]), 3)
            # Check derived stats have race modifiers added
            expected_str = 10 + 4 + cg.RACIAL_LINEAGES[r_key]["stat_mods"].get("STR", 0)
            self.assertEqual(avatar["stats"]["STR"], expected_str)

if __name__ == "__main__":
    unittest.main()
