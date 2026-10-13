import unittest
import copy
import backend.mechanics as mechanics

class TestChronoAndSurvivalPhase8(unittest.TestCase):
    def setUp(self):
        self.base_player = {
            "name": "Banki",
            "race": "Phrenic Human",
            "class": "Nordic Berserker",
            "level": 4,
            "hp": 75,
            "max_hp": 150,
            "col": 5000,
            "location": "Sector 1 Wilderness - Pine Barrens Fringe",
            "skills": {
                "One-Handed Axes": {"mastery": 150, "tier": "Journeyman"},
                "Field Trapping": {"mastery": 110, "tier": "Journeyman"}
            },
            "feats": ["Iron Grip", "Berserk Fury", "Dire-Wolf Fur Mantle"],
            "spells": [],
            "equipped": {
                "head": "None",
                "chest": "Einherjar Rig (Gr. 5 Armor)",
                "main_hand": "Fenrir's Tusk (Gr. 5 Axe)",
                "off_hand": "Mjöllnir-Null (Gr. 5 Trench-Hammer)",
                "accessory": "Dire-Wolf Fur Mantle"
            },
            "inventory": []
        }

    # =========================================================================
    # SUITE 1: 24-HOUR CHRONO ENGINE & TIME PROGRESSION
    # =========================================================================
    def test_chrono_initialization(self):
        p = copy.deepcopy(self.base_player)
        chrono = mechanics.ensure_chrono_system(p)

        self.assertIn("day", chrono)
        self.assertIn("hour", chrono)
        self.assertIn("minute", chrono)
        self.assertIn("weather", chrono)
        self.assertEqual(chrono["day"], 1)
        self.assertEqual(chrono["hour"], 9)
        self.assertEqual(chrono["minute"], 30)
        self.assertEqual(chrono["weather"], "clear_skies")

        time_data = mechanics.get_game_time(p)
        self.assertEqual(time_data["time_str"], "Day 1, 09:30")
        self.assertEqual(time_data["period"], "day")
        self.assertEqual(time_data["period_info"]["label"], "☀️ Midday")

    def test_time_advance_and_rollover(self):
        p = copy.deepcopy(self.base_player)
        mechanics.ensure_chrono_system(p)

        # Advance 45 minutes: 09:30 -> 10:15
        adv_res = mechanics.advance_game_time(p, minutes=45)
        self.assertTrue(adv_res["success"])
        self.assertEqual(adv_res["hour"], 10)
        self.assertEqual(adv_res["minute"], 15)
        self.assertEqual(adv_res["day"], 1)
        self.assertEqual(adv_res["time_str"], "Day 1, 10:15")

        # Advance 14 hours (840 minutes): 10:15 + 14h = 00:15 on Day 2
        adv_res2 = mechanics.advance_game_time(p, minutes=840)
        self.assertEqual(adv_res2["day"], 2)
        self.assertEqual(adv_res2["hour"], 0)
        self.assertEqual(adv_res2["minute"], 15)
        self.assertTrue(adv_res2["day_rollover"])
        self.assertEqual(adv_res2["period"], "night")

    def test_period_transitions(self):
        p = copy.deepcopy(self.base_player)
        mechanics.ensure_chrono_system(p)

        # Dawn: 06:00 - 08:00
        p["chrono"]["hour"] = 6
        p["chrono"]["minute"] = 0
        t_dawn = mechanics.get_game_time(p)
        self.assertEqual(t_dawn["period"], "dawn")
        self.assertIn("Dawn", t_dawn["period_info"]["label"])

        # Midday: 08:00 - 18:00
        p["chrono"]["hour"] = 12
        t_midday = mechanics.get_game_time(p)
        self.assertEqual(t_midday["period"], "day")
        self.assertIn("Midday", t_midday["period_info"]["label"])

        # Dusk: 18:00 - 21:00
        p["chrono"]["hour"] = 19
        t_dusk = mechanics.get_game_time(p)
        self.assertEqual(t_dusk["period"], "dusk")
        self.assertIn("Dusk", t_dusk["period_info"]["label"])

        # Midnight: 21:00 - 04:00
        p["chrono"]["hour"] = 23
        t_night = mechanics.get_game_time(p)
        self.assertEqual(t_night["period"], "night")
        self.assertIn("Midnight", t_night["period_info"]["label"])

        # Witching Hour: 04:00 - 06:00
        p["chrono"]["hour"] = 5
        t_witch = mechanics.get_game_time(p)
        self.assertEqual(t_witch["period"], "witching_hour")
        self.assertIn("Witching", t_witch["period_info"]["label"])

    # =========================================================================
    # SUITE 2: AETHER-WEATHER PHENOMENA & MODIFIERS
    # =========================================================================
    def test_weather_setting_and_definitions(self):
        p = copy.deepcopy(self.base_player)
        mechanics.ensure_chrono_system(p)

        # Clear Skies
        w_res = mechanics.set_weather(p, "clear_skies")
        self.assertTrue(w_res["success"])
        w_cur = mechanics.get_current_weather(p)
        self.assertEqual(w_cur["travel_allowed"], True)

        # Runic Mist (-4 Ranged ATK, +3 Stealth, Fast Travel Disabled)
        w_res = mechanics.set_weather(p, "runic_mist")
        self.assertTrue(w_res["success"])
        w_cur = mechanics.get_current_weather(p)
        self.assertEqual(w_cur["ranged_atk_mod"], -4)
        self.assertEqual(w_cur["stealth_mod"], 3)
        self.assertEqual(w_cur["travel_allowed"], False)

        # Leyline Overload Storm (+25% Spell DMG, Berserk Golems)
        w_res = mechanics.set_weather(p, "leyline_storm")
        self.assertTrue(w_res["success"])
        w_cur = mechanics.get_current_weather(p)
        self.assertEqual(w_cur["spell_dmg_pct"], 25)

        # Crimson Ash Fall (-50% Healing)
        w_res = mechanics.set_weather(p, "crimson_ash")
        self.assertTrue(w_res["success"])
        w_cur = mechanics.get_current_weather(p)
        self.assertEqual(w_cur["healing_mult"], 0.5)

        # Glitch-Freeze Blizzard (Travel Disabled, Movement Halved, Cold Exposure)
        w_res = mechanics.set_weather(p, "glitch_freeze")
        self.assertTrue(w_res["success"])
        w_cur = mechanics.get_current_weather(p)
        self.assertEqual(w_cur["travel_allowed"], False)
        self.assertEqual(w_cur["speed_mult"], 0.5)
        self.assertTrue(w_cur["cold_exposure"])

    def test_random_weather_roll(self):
        p = copy.deepcopy(self.base_player)
        mechanics.ensure_chrono_system(p)

        roll_res = mechanics.roll_random_weather(p)
        self.assertTrue(roll_res["success"])
        self.assertIn(p["chrono"]["weather"], mechanics.AETHER_WEATHER)

    # =========================================================================
    # SUITE 3: COLD INSULATION & FROSTBITE PROTECTION
    # =========================================================================
    def test_frostbite_protection_equipped_mantle(self):
        p = copy.deepcopy(self.base_player)
        p["equipped"]["accessory"] = "Dire-Wolf Fur Mantle"
        p["feats"] = [] # Clear feats to test equipment specifically

        res = mechanics.check_frostbite_protection(p)
        self.assertTrue(res["protected"])
        self.assertIn("Dire-Wolf Fur Mantle", res["source"])

    def test_frostbite_protection_feat_heritage(self):
        p = copy.deepcopy(self.base_player)
        p["equipped"]["accessory"] = "None"
        p["feats"] = ["Dire-Wolf Fur Mantle"]

        res = mechanics.check_frostbite_protection(p)
        self.assertTrue(res["protected"])
        self.assertIn("Mantle", res["source"])

    def test_frostbite_unprotected(self):
        p = copy.deepcopy(self.base_player)
        p["equipped"] = {"head": "None", "chest": "Light Cloth Tunic", "accessory": "None"}
        p["feats"] = ["Quick Reflexes"]

        res = mechanics.check_frostbite_protection(p)
        self.assertFalse(res["protected"])
        self.assertIn("Unprotected", res["message"])

    # =========================================================================
    # SUITE 4: CAMPFIRE CULINARY CRAFTING & BUFF PERSISTENCE
    # =========================================================================
    def test_cooking_missing_ingredients(self):
        p = copy.deepcopy(self.base_player)
        p["inventory"] = ["Bottled Water x1"]

        res = mechanics.cook_campfire_meal(p, "wolf_heart_stew")
        self.assertFalse(res["success"])
        self.assertIn("Missing required ingredients", res["message"])

    def test_cooking_successful_and_buff_application(self):
        p = copy.deepcopy(self.base_player)
        p["hp"] = 50
        p["max_hp"] = 150
        p["inventory"] = [
            {"name": "Wolf Marrow", "qty": 1},
            {"name": "Wild Roots", "qty": 2}
        ]

        res = mechanics.cook_campfire_meal(p, "wolf_heart_stew")
        self.assertTrue(res["success"])
        self.assertEqual(res["recipe"], "Wolf-Heart Marrow Stew")
        self.assertIn("[Wolf-Heart Vigor]", res["buff"]["name"])
        
        # Verify HP recovery (+15)
        self.assertEqual(p["hp"], 65)

        # Verify active buffs populated
        self.assertIn("[Wolf-Heart Vigor]", p["active_buffs"])
        self.assertEqual(len(p["chrono"]["active_buffs"]), 1)
        self.assertEqual(p["chrono"]["active_buffs"][0]["duration"], 5)

        # Verify inventory deducted (Wolf Marrow removed, Wild Roots reduced from 2 to 1)
        item_names = [i["name"] for i in p["inventory"]]
        self.assertNotIn("Wolf Marrow", item_names)
        roots_entry = next(i for i in p["inventory"] if i["name"] == "Wild Roots")
        self.assertEqual(roots_entry["qty"], 1)

    def test_buff_duration_countdown_and_expiration(self):
        p = copy.deepcopy(self.base_player)
        p["inventory"] = [
            {"name": "Raw Boar Flank", "qty": 1},
            {"name": "Salted Moss", "qty": 1}
        ]

        cook_res = mechanics.cook_campfire_meal(p, "roasted_boar_ribs")
        self.assertTrue(cook_res["success"])
        self.assertEqual(p["chrono"]["active_buffs"][0]["duration"], 5)

        # Advance time 4 times: duration ticks from 5 down to 1
        for _ in range(4):
            mechanics.advance_game_time(p, minutes=60)
        self.assertEqual(p["chrono"]["active_buffs"][0]["duration"], 1)
        self.assertIn("[Boar's Resilience]", p["active_buffs"])

        # 5th advance: buff expires
        adv_res = mechanics.advance_game_time(p, minutes=60)
        self.assertEqual(len(p["chrono"]["active_buffs"]), 0)
        self.assertEqual(len(p["active_buffs"]), 0)
        self.assertIn("[Boar's Resilience]", adv_res["expired_buffs"])

    # =========================================================================
    # SUITE 5: WILDERNESS CAMPING & COMPANION WATCH
    # =========================================================================
    def test_pitch_wilderness_camp_ren_watch(self):
        p = copy.deepcopy(self.base_player)
        p["hp"] = 40
        p["max_hp"] = 150
        mechanics.ensure_party_system(p)

        camp_res = mechanics.pitch_wilderness_camp(p, watch_companion="Ren")
        self.assertTrue(camp_res["success"])

        # Time should advance by 480 minutes (8 hours: 09:30 -> 17:30)
        self.assertEqual(camp_res["time_info"]["hour"], 17)
        self.assertEqual(camp_res["time_info"]["minute"], 30)

        # Field rest restores +50 HP in wilderness (40 + 50 = 90)
        self.assertEqual(p["hp"], 90)

        # Ren's watch perk
        self.assertEqual(camp_res["watch_companion"], "Ren")
        self.assertIn("Initiative", camp_res["watch_perk"])

    def test_pitch_camp_in_safe_zone_full_heal(self):
        p = copy.deepcopy(self.base_player)
        p["location"] = "Washington Borough Safe Zone - Taphouse"
        p["hp"] = 20
        p["max_hp"] = 150
        mechanics.ensure_party_system(p)

        camp_res = mechanics.pitch_wilderness_camp(p, watch_companion="Torvald")
        self.assertTrue(camp_res["success"])
        # Safe zone rest restores 100% of max HP
        self.assertEqual(p["hp"], 150)
        self.assertEqual(camp_res["healed_hp"], 130)
        self.assertIn("Staggered", camp_res["watch_perk"])

    def test_watch_perks_all_companions(self):
        p = copy.deepcopy(self.base_player)
        mechanics.ensure_party_system(p)

        # Kibs watch
        kibs_res = mechanics.pitch_wilderness_camp(p, watch_companion="Kibs")
        self.assertIn("Perimeter Snare Web", kibs_res["watch_perk"])

        # Elora watch
        elora_res = mechanics.pitch_wilderness_camp(p, watch_companion="Elora")
        self.assertIn("Warded Perimeter", elora_res["watch_perk"])

    # =========================================================================
    # SUITE 6: LLM STATE UPDATES PACKET PROCESSING
    # =========================================================================
    def test_llm_state_updates_phase8_keys(self):
        p = copy.deepcopy(self.base_player)
        p["hp"] = 50
        p["max_hp"] = 150
        p["inventory"] = [
            {"name": "Aether-Herb", "qty": 1},
            {"name": "Bottled Water", "qty": 1}
        ]
        mechanics.ensure_party_system(p)

        mock_state_updates = {
            "time_advance_minutes": 90,
            "set_weather": "runic_mist",
            "cook_recipe": "spiced_herb_broth",
            "pitch_camp": {"watch": "Ren"}
        }

        # 1. Process time advance
        t_res = mechanics.advance_game_time(p, minutes=mock_state_updates["time_advance_minutes"])
        self.assertEqual(t_res["hour"], 11)
        self.assertEqual(t_res["minute"], 0)

        # 2. Process weather shift
        w_res = mechanics.set_weather(p, mock_state_updates["set_weather"])
        self.assertEqual(p["chrono"]["weather"], "runic_mist")

        # 3. Process campfire meal
        c_res = mechanics.cook_campfire_meal(p, mock_state_updates["cook_recipe"])
        self.assertTrue(c_res["success"])
        self.assertIn("[Aetheric Focus]", p["active_buffs"])

        # 4. Process wilderness camp
        camp_res = mechanics.pitch_wilderness_camp(p, watch_companion=mock_state_updates["pitch_camp"]["watch"])
        self.assertTrue(camp_res["success"])
        self.assertEqual(camp_res["watch_companion"], "Ren")
        # 11:00 + 8 hours = 19:00 (Dusk)
        self.assertEqual(camp_res["time_info"]["hour"], 19)
        self.assertEqual(camp_res["time_info"]["period"], "dusk")

if __name__ == "__main__":
    unittest.main()
