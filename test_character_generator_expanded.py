import unittest
import os
import shutil
import tempfile
import backend.character_generator as cg

class TestCharacterGeneratorExpanded(unittest.TestCase):
    def test_all_18_lifestyle_presets_sum_to_20(self):
        self.assertEqual(len(cg.PRESET_LIFESTYLES), 18)
        for key, preset in cg.PRESET_LIFESTYLES.items():
            pts = preset["points"]
            total = sum(pts.values())
            self.assertEqual(total, 20, f"Preset {key} sums to {total}, expected 20!")
            self.assertEqual(len(pts), 6, f"Preset {key} must specify all 6 stats!")

    def test_all_32_vocational_backgrounds(self):
        self.assertGreaterEqual(len(cg.PRESET_BACKGROUNDS), 32)
        self.assertEqual(len(cg.EARTH_VOCATIONS), len(cg.PRESET_BACKGROUNDS))
        for key, bg in cg.PRESET_BACKGROUNDS.items():
            self.assertIn("title", bg)
            self.assertIn("description", bg)
            self.assertIn("skills", bg)
            self.assertEqual(len(bg["skills"]), 2, f"Vocation {key} must have exactly 2 starting skills!")
            for s_name, s_data in bg["skills"].items():
                self.assertIn("mastery", s_data)
                self.assertIn("tier", s_data)
                self.assertIn("description", s_data)
                self.assertGreaterEqual(s_data["mastery"], 20)
                self.assertLessEqual(s_data["mastery"], 100)
            self.assertIn("innate_perk", bg)
            self.assertTrue(len(bg["innate_perk"]) > 0)

    def test_all_20_racial_lineages(self):
        self.assertGreaterEqual(len(cg.RACIAL_LINEAGES), 20)
        for key, race in cg.RACIAL_LINEAGES.items():
            self.assertIn("name", race)
            self.assertIn("desc", race)
            self.assertIn("stat_mods", race)
            self.assertIn("racial_abilities", race)
            self.assertGreaterEqual(len(race["racial_abilities"]), 2)

    def test_all_29_personal_relics_and_custom_relic(self):
        self.assertGreaterEqual(len(cg.PERSONAL_RELICS), 29)
        self.assertIn("elder_brain_jar", cg.PERSONAL_RELICS)
        self.assertIn("Gyrus", cg.PERSONAL_RELICS["elder_brain_jar"]["name"])
        for key, relic in cg.PERSONAL_RELICS.items():
            self.assertIn("name", relic)
            self.assertIn("durability", relic)
            self.assertIn("desc", relic)

        # Test custom relic generator
        custom_r = cg.create_custom_relic(
            name="Grandpa's Pocket Bible",
            desc="Worn leather cover with handwritten notes.",
            ability_text="+2 saving throws against demonic panic"
        )
        self.assertEqual(custom_r["name"], "Grandpa's Pocket Bible")
        self.assertEqual(custom_r["rarity"], "Custom Relic")
        self.assertIn("custom_ability", custom_r)

    def test_activate_elder_brain_and_eccentric_relics(self):
        import backend.mechanics as mechanics
        # Test Elder Brain Prototype ('Gyrus the Ancient')
        player_gyrus = {
            "name": "Psion Test",
            "hp": 40,
            "max_hp": 80,
            "personal_relic": "Miniature Elder Brain Prototype ('Gyrus the Ancient')",
            "status_effects": ["Frightened", "Cognitive Stress"],
            "inventory": []
        }
        res_gyrus = mechanics.activate_personal_relic(player_gyrus, relic_action="auto")
        self.assertTrue(res_gyrus["success"])
        self.assertEqual(res_gyrus["effect_type"], "sentient_psionic_advisory")
        self.assertIn("Gyrus", res_gyrus["relic"])
        self.assertIn("Cardinal", res_gyrus["gyrus_dialogue"])
        self.assertNotIn("Frightened", player_gyrus["status_effects"])
        self.assertNotIn("Cognitive Stress", player_gyrus["status_effects"])

        # Test Great-Aunt Martha's Soup Thermos
        player_soup = {
            "name": "Soup Test",
            "hp": 20,
            "max_hp": 100,
            "personal_relic": "Great-Aunt Martha's Red Plaid Soup Thermos",
            "status_effects": ["Spider Venom", "Frostbite"],
            "inventory": []
        }
        res_soup = mechanics.activate_personal_relic(player_soup, relic_action="auto")
        self.assertTrue(res_soup["success"])
        self.assertEqual(player_soup["hp"], 45)
        self.assertEqual(player_soup["status_effects"], [])
        self.assertEqual(player_soup["soup_pours_remaining"], 2)

    def test_consult_custom_background(self):
        consult = cg.consult_custom_background("I was a master carpenter who built timber log cabins and brewed dark beer.")
        self.assertIn("evaluation_message", consult)
        self.assertIn("skill_1", consult)
        self.assertIn("skill_2", consult)
        self.assertIn("innate_perk", consult)
        self.assertTrue(len(consult["skill_1"]["name"]) > 0)
        self.assertTrue(len(consult["skill_2"]["name"]) > 0)

    def test_character_folder_saving_and_loading(self):
        temp_dir = tempfile.mkdtemp()
        try:
            player = cg.generate_starting_character(
                name="Aria Valkyrie",
                point_alloc={"STR": 5, "DEX": 6, "CON": 4, "INT": 1, "WIS": 2, "CHA": 2},
                background_key="electrician_lineworker",
                race_key="hellforged_tiefling",
                class_key="warrior",
                relic_key="noise_cancelling_headphones"
            )
            
            # Save character
            save_path = cg.save_character_to_folder(temp_dir, player, messages=[{"role": "user", "content": "Link Start"}])
            self.assertTrue(os.path.exists(save_path))
            
            # Check character folder
            char_folder = os.path.dirname(save_path)
            self.assertTrue(os.path.basename(char_folder) in ["Aria_Valkyrie", "Aria Valkyrie"])
            self.assertTrue(os.path.exists(os.path.join(char_folder, "profile.json")))
            
            # Load character
            loaded = cg.load_character_from_folder(temp_dir, "Aria Valkyrie")
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded["player"]["name"], "Aria Valkyrie")
            self.assertEqual(loaded["player"]["race"], "Hellforged Fiendblood (Tiefling)")
            self.assertIn("Magi-Tech Wiring", loaded["player"]["skills"])
            
            # List profiles
            profiles = cg.list_all_character_folders(temp_dir)
            self.assertEqual(len(profiles), 1)
            self.assertEqual(profiles[0]["name"], "Aria Valkyrie")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    unittest.main()
