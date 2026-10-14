import unittest
import backend.character_generator as cg
import backend.mechanics as mechanics
import backend.persona_engine as persona_engine


class TestGenderAndTutorialCrucible(unittest.TestCase):
    def test_gender_selection_and_pronouns(self):
        self.assertEqual(mechanics.normalize_gender("Male"), "Male")
        self.assertEqual(mechanics.normalize_gender("female"), "Female")
        self.assertEqual(mechanics.normalize_gender("F"), "Female")
        self.assertEqual(mechanics.normalize_gender(None), "Male")

        female_char = cg.generate_starting_character(
            name="Asuna",
            point_alloc={"STR": 2, "DEX": 6, "CON": 4, "INT": 4, "WIS": 2, "CHA": 2},
            background_key="student_athlete",
            race_key="human",
            class_key="spellblade",
            relic_key="polaroid_camera",
            gender="Female",
        )
        self.assertEqual(female_char["gender"], "Female")
        prof_f = mechanics.get_physical_profile(female_char)
        self.assertEqual(prof_f["gender"], "Female")
        self.assertEqual(prof_f["pronouns"], "she/her")
        self.assertIn("Female (she/her)", prof_f["summary"])

        male_char = cg.generate_starting_character(
            name="Kirito",
            point_alloc={"STR": 4, "DEX": 6, "CON": 4, "INT": 4, "WIS": 2, "CHA": 0},
            background_key="esports_prodigy",
            race_key="human",
            class_key="spellblade",
            relic_key="smartphone",
            gender="Male",
        )
        self.assertEqual(male_char["gender"], "Male")
        prof_m = mechanics.get_physical_profile(male_char)
        self.assertEqual(prof_m["gender"], "Male")
        self.assertEqual(prof_m["pronouns"], "he/him")
        self.assertIn("Male (he/him)", prof_m["summary"])

        # Visual manifest & character visual profile include gender
        vis_prof = mechanics.build_character_visual_profile(female_char)
        self.assertIn("Female", vis_prof)
        manifest = mechanics.build_scene_visual_manifest(female_char)
        self.assertIn("Female (she/her)", manifest)

    def test_three_stage_tutorial_to_level_3_and_washington_nj_teleport(self):
        player = cg.generate_starting_character(
            name="Valeria",
            point_alloc={"STR": 4, "DEX": 4, "CON": 4, "INT": 4, "WIS": 2, "CHA": 2},
            background_key="medical_first_responder",
            race_key="elf",
            class_key="spellblade",
            relic_key="tuning_fork",
            gender="Female",
            start_tutorial=True,
        )
        self.assertEqual(player["level"], 1)
        self.assertTrue(mechanics.is_tutorial_active(player))
        self.assertEqual(player["tutorial"]["stage"], 1)
        self.assertIn("Cardinal Calibration Crucible", player["location"])

        welcome = cg.build_system_initialization_welcome_message(player)
        self.assertIn("Female (she/her)", welcome)
        self.assertIn("BASE MECHANICS BRIEFING", welcome)
        self.assertIn("STAGE 1 OF 3", welcome)
        self.assertIn("Washington Borough, NJ", welcome)

        master_state = mechanics.build_tutorial_master_state(player, stage=1)
        self.assertIn("npc_cardinal_arbiter", [e["id"] for e in master_state["entities"]])

        # Stage 1: Base Mechanics & Orientation -> Stage 2
        res1 = mechanics.advance_tutorial_stage(
            player,
            player_action="Inspect my HUD, check my physical build modifiers, and resonate with my Personal Relic.",
            master_state=master_state,
        )
        self.assertEqual(res1["completed_stage"], 1)
        self.assertEqual(res1["new_stage"], 2)
        self.assertFalse(res1["graduated"])
        inv_names_1 = [it["name"] if isinstance(it, dict) else str(it) for it in player["inventory"]]
        self.assertIn("Minor Aether-Salve Vial", inv_names_1)
        self.assertIn("Calibration Whetstone Kit", inv_names_1)
        self.assertIn("tutorial_clockwork_sentinel", [e["id"] for e in master_state["entities"]])

        # Stage 2: Martial Combat & Looting -> Level 2 & Unlocks Astral Bolt -> Stage 3
        res2 = mechanics.advance_tutorial_stage(
            player,
            player_action="Strike the Clockwork Calibration Sentinel and loot its core!",
            master_state=master_state,
        )
        self.assertEqual(res2["completed_stage"], 2)
        self.assertEqual(res2["new_stage"], 3)
        self.assertEqual(player["level"], 2)
        self.assertTrue(any("Astral Bolt" in s for s in player["spells"]))
        inv_names_2 = [it["name"] if isinstance(it, dict) else str(it) for it in player["inventory"]]
        self.assertIn("Sentinel Brass Armguards", inv_names_2)
        self.assertIn("Clockwork Reflex Servo", inv_names_2)
        self.assertIn("Inscribed Spell Slate: Astral Bolt", inv_names_2)
        self.assertIn("tutorial_crucible_warden", [e["id"] for e in master_state["entities"]])

        # Stage 3: Spellcasting & Active Powers -> Level 3 & Teleports to Washington, NJ Safe-Zone with all loot
        res3 = mechanics.advance_tutorial_stage(
            player,
            player_action="Cast Astral Bolt and unleash my class technique on the Aether-Forged Crucible Warden!",
            master_state=master_state,
        )
        self.assertEqual(res3["completed_stage"], 3)
        self.assertTrue(res3["graduated"])
        self.assertTrue(res3["teleported"])
        self.assertFalse(mechanics.is_tutorial_active(player))
        self.assertTrue(player["tutorial"]["completed"])
        self.assertEqual(player["level"], 3)
        self.assertEqual(player["location"], "Sector 1 Safe-Zone: Washington Borough, NJ")
        self.assertEqual(master_state["environment"]["location"], "Sector 1 Safe-Zone: Washington Borough, NJ")
        self.assertTrue(master_state["environment"]["safe_zone"])

        # Verify all 8 tutorial loot items remain in player's inventory upon arrival in Washington, NJ
        expected_loot = [
            "Minor Aether-Salve Vial",
            "Calibration Whetstone Kit",
            "Sentinel Brass Armguards",
            "Clockwork Reflex Servo",
            "Inscribed Spell Slate: Astral Bolt",
            "Crucible Vanguard Signet",
            "Condensed Aether-Core",
            "Greater Crimson Draught",
        ]
        inv_names_final = [it["name"] if isinstance(it, dict) else str(it) for it in player["inventory"]]
        for item_name in expected_loot:
            self.assertIn(item_name, inv_names_final)
            self.assertIn(item_name, player["tutorial"]["acquired_loot"])

    def test_fast_forward_complete_all_tutorial(self):
        player = cg.generate_starting_character(
            name="Garrick",
            point_alloc={"STR": 6, "DEX": 2, "CON": 6, "INT": 2, "WIS": 2, "CHA": 2},
            background_key="industrial_line_worker",
            race_key="dwarf",
            class_key="forge_knight",
            relic_key="zippo_lighter",
            gender="Male",
            start_tutorial=True,
        )
        master_state = mechanics.build_tutorial_master_state(player, stage=1)
        res = mechanics.advance_tutorial_stage(
            player,
            player_action="Skip tutorial",
            master_state=master_state,
            complete_all=True,
        )
        self.assertTrue(res["graduated"])
        self.assertTrue(res["teleported"])
        self.assertEqual(player["level"], 3)
        self.assertEqual(player["location"], "Sector 1 Safe-Zone: Washington Borough, NJ")
        self.assertGreaterEqual(len(res["loot_gained"]), 8)

    def test_tutorial_subagent_personas_load_without_api(self):
        player = cg.generate_starting_character(name="TestHero", gender="Female")
        visible_room = {"environment": {"location": player["location"]}, "entities_in_room": []}
        for eid in ("npc_cardinal_arbiter", "tutorial_clockwork_sentinel", "tutorial_crucible_warden"):
            out = persona_engine.get_subagent_action(
                api_key="",
                entity_id=eid,
                visible_room=visible_room,
                player_action="Ready weapon",
                player_state=player,
            )
            self.assertEqual(out["actor_id"], eid)
            self.assertTrue(out["actor_name"])


if __name__ == "__main__":
    unittest.main()
