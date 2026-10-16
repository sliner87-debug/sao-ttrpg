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

    def test_pixie_dnd_3_0_abilities_and_polymorph(self):
        # 1. Lineage definition invariants
        self.assertIn("pixie_fey_sprite", cg.RACIAL_LINEAGES)
        pixie_lineage = cg.RACIAL_LINEAGES["pixie_fey_sprite"]
        self.assertEqual(pixie_lineage["flight_speed_ft"], 60)
        self.assertEqual(pixie_lineage["flight_maneuverability"], "Good")
        self.assertEqual(pixie_lineage["spell_resistance"], 15)
        self.assertEqual(pixie_lineage["size"], "Tiny")

        # 2. Character Generation with Pixie
        pixie_char = cg.generate_starting_character(
            name="Aria_Gossamer",
            point_alloc={"STR": 0, "DEX": 5, "CON": 0, "INT": 5, "WIS": 5, "CHA": 5},
            background_key="woodsman_hunter",
            race_key="pixie_fey_sprite",
            class_key="wizard",
            relic_key="brass_zippo"
        )
        self.assertIn("innate_spells", pixie_char)
        expected_spells = [
            "Polymorph Self (At Will)",
            "Permanent Greater Invisibility",
            "Pixie Dust: Sleep & Memory Loss",
            "Detect Thoughts (At Will)",
            "Lesser Confusion (At Will)",
            "Dancing Lights (At Will)",
            "Entangle (At Will)",
            "Confusion (1/Day)",
            "Dispel Magic (1/Day)",
            "Permanent Image (1/Day)"
        ]
        for sp in expected_spells:
            self.assertIn(sp, pixie_char["spells"], f"Missing {sp} in pixie spells")

        # 3. Canonical Spells & Powers metadata enrichment
        all_powers = mechanics.get_all_player_spells_and_powers(pixie_char)
        power_names = [p["name"].lower() for p in all_powers]
        for sp in ["polymorph self", "permanent greater invisibility", "pixie dust: sleep & memory loss", "detect thoughts", "dispel magic"]:
            self.assertTrue(any(sp in pn for pn in power_names), f"Missing canonical power: {sp}")
            dt = mechanics.get_spell_or_power_details(sp, player_state=pixie_char)
            self.assertNotEqual(dt["name"], "Unknown Power")
            self.assertTrue(len(dt["description"]) > 10)
            self.assertTrue(len(dt["mechanics"]) > 10)

        # 4. Pixie Dust mechanics (Sleep, Confusion, Memory Loss)
        mem_res = mechanics.apply_pixie_dust_effect({"stats": {"WIS": 10}}, dust_choice="memory_loss")
        self.assertEqual(mem_res["effect_applied"], "amnesia")
        sleep_res = mechanics.apply_pixie_dust_effect({"stats": {"WIS": 10}}, dust_choice="sleep")
        self.assertEqual(sleep_res["effect_applied"], "incapacitated")
        conf_res = mechanics.apply_pixie_dust_effect({"stats": {"WIS": 10}}, dust_choice="confusion")
        self.assertEqual(conf_res["effect_applied"], "confused")

        # 5. Polymorph Self Form Shifting & AC / Size recalculation
        base_ac = mechanics.calculate_ac(pixie_char)
        # Shift into Dire Wolf (Large, STR 25, DEX 15, Natural Armor 3)
        shift_res = mechanics.execute_pixie_polymorph(pixie_char, "dire_wolf")
        self.assertTrue(shift_res["success"])
        self.assertEqual(pixie_char.get("polymorphed_form"), "Dire Wolf")
        wolf_profile = mechanics.get_physical_profile(pixie_char)
        self.assertEqual(wolf_profile["size"], "Large")
        wolf_ac = mechanics.calculate_ac(pixie_char)
        self.assertGreaterEqual(wolf_ac, 10)

        # Shift into Giant Eagle (Large, Fly 80ft)
        eagle_res = mechanics.execute_pixie_polymorph(pixie_char, "giant_eagle")
        self.assertTrue(eagle_res["success"])
        self.assertEqual(pixie_char.get("polymorphed_form"), "Giant Eagle")

        # Revert to Pixie True Form
        revert_res = mechanics.execute_pixie_polymorph(pixie_char, "revert")
        self.assertTrue(revert_res["success"])
        self.assertTrue(revert_res.get("reverted"))
        self.assertIsNone(pixie_char.get("polymorphed_form"))
        self.assertIsNone(pixie_char.get("polymorph_data"))
        reverted_profile = mechanics.get_physical_profile(pixie_char)
        self.assertEqual(reverted_profile["size"], "Tiny")

if __name__ == "__main__":
    unittest.main()
