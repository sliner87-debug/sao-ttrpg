import unittest
import json
import os
import copy
from backend.mechanics import (
    RECRUITABLE_COMPANIONS,
    DUAL_TECH_COMBOS,
    ensure_party_system,
    get_active_party,
    recruit_companion,
    set_companion_stance,
    increase_companion_affinity,
    execute_dual_tech
)

class TestExpandedCompanionSubagents(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__)))
        self.entities_dir = os.path.join(self.base_dir, "Entities")
        self.party_dir = os.path.join(self.base_dir, "Party")
        
        self.player_state = {
            "name": "Banki",
            "level": 1,
            "col": 50,
            "hp": 42,
            "max_hp": 42,
            "companions": {},
            "feats": []
        }

    def test_all_18_companions_exist_in_mechanics(self):
        expected_names = [
            "Ren", "Elora", "Torvald", "Kibs",
            "Valeria", "Morrigan", "Garrick", "Sariel",
            "Kaelen", "Zedd", "Daphne", "Rok",
            "Lyra", "Titus", "Nyssa", "Malakor",
            "Thorne", "Teresa", "Gyrus"
        ]
        self.assertEqual(len(RECRUITABLE_COMPANIONS), 19)
        for name in expected_names:
            self.assertIn(name, RECRUITABLE_COMPANIONS, f"Missing companion {name}")
            c = RECRUITABLE_COMPANIONS[name]
            self.assertTrue(len(c.get("abilities", [])) >= 3, f"{name} should have at least 3 abilities")
            self.assertTrue(len(c.get("stances", {})) >= 3, f"{name} should have at least 3 stances")
            self.assertIn("dual_tech_id", c, f"{name} missing dual_tech_id")
            self.assertIn("recruitment_location", c, f"{name} missing recruitment_location")
            self.assertIn("recruitment_requirements", c, f"{name} missing recruitment_requirements")

    def test_all_14_subagent_personas_exist_and_validate(self):
        new_ids = [
            "companion_valeria", "companion_morrigan", "companion_garrick", "companion_sariel",
            "companion_kaelen", "companion_zedd", "companion_daphne", "companion_rok",
            "companion_lyra", "companion_titus", "companion_nyssa", "companion_malakor",
            "companion_thorne", "companion_teresa", "companion_gyrus"
        ]
        for cid in new_ids:
            filepath = os.path.join(self.entities_dir, f"{cid}.json")
            self.assertTrue(os.path.exists(filepath), f"File {filepath} does not exist")
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data.get("id"), cid)
            self.assertTrue(bool(data.get("name")))
            self.assertTrue(bool(data.get("role")))
            self.assertTrue(bool(data.get("behavior_prompt")))
            self.assertTrue(bool(data.get("personality")))
            self.assertTrue(isinstance(data.get("quirks"), list) and len(data["quirks"]) >= 2)
            self.assertTrue(bool(data.get("tactical_style")))

    def test_all_14_mechanical_party_sheets_exist_and_validate(self):
        new_ids = [
            "companion_valeria", "companion_morrigan", "companion_garrick", "companion_sariel",
            "companion_kaelen", "companion_zedd", "companion_daphne", "companion_rok",
            "companion_lyra", "companion_titus", "companion_nyssa", "companion_malakor",
            "companion_thorne", "companion_teresa", "companion_gyrus"
        ]
        for cid in new_ids:
            filepath = os.path.join(self.party_dir, f"{cid}.json")
            self.assertTrue(os.path.exists(filepath), f"File {filepath} does not exist")
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data.get("id"), cid)
            self.assertTrue(bool(data.get("name")))
            self.assertTrue(bool(data.get("role")))
            self.assertTrue(isinstance(data.get("level"), int) and data["level"] >= 1)
            self.assertTrue(isinstance(data.get("hp"), int) and data["hp"] >= 20)
            self.assertTrue(isinstance(data.get("max_hp"), int) and data["max_hp"] >= 20)
            self.assertTrue(isinstance(data.get("ac"), int) and data["ac"] >= 10)
            self.assertTrue(bool(data.get("behavior_prompt")))

    def test_dual_tech_combos_complete(self):
        self.assertEqual(len(DUAL_TECH_COMBOS), 19)
        for name, comp in RECRUITABLE_COMPANIONS.items():
            dt_id = comp["dual_tech_id"]
            self.assertIn(dt_id, DUAL_TECH_COMBOS, f"Dual tech ID {dt_id} for {name} not in DUAL_TECH_COMBOS")
            combo = DUAL_TECH_COMBOS[dt_id]
            self.assertEqual(combo["id"], dt_id)
            self.assertIn("Banki", combo["partners"])
            self.assertTrue(bool(combo.get("name")))
            self.assertTrue(bool(combo.get("damage")))
            self.assertTrue(bool(combo.get("effect")))
            self.assertTrue(bool(combo.get("log_tag")))

    def test_recruitment_logic_and_requirements(self):
        state = copy.deepcopy(self.player_state)
        ensure_party_system(state)
        
        # Ren is already recruited and active
        self.assertTrue(state["companions"]["Ren"]["recruited"])
        self.assertTrue(state["companions"]["Ren"]["active"])
        self.assertEqual(len(get_active_party(state)), 1)

        # Test requirement failure: Level too low
        # Valeria requires level 3
        state["level"] = 1
        res = recruit_companion(state, "Valeria", check_requirements=True)
        self.assertFalse(res["success"])
        self.assertIn("below required level 3", res["message"])

        # Test requirement failure: Col too low
        # Kaelen requires level 2 and 200 Col
        state["level"] = 2
        state["col"] = 50
        res = recruit_companion(state, "Kaelen", check_requirements=True)
        self.assertFalse(res["success"])
        self.assertIn("Insufficient Col", res["message"])

        # Test requirement success: Level 2 and 200 Col for Kaelen
        state["col"] = 250
        res = recruit_companion(state, "Kaelen", check_requirements=True)
        self.assertTrue(res["success"])
        self.assertEqual(state["col"], 50)  # 250 - 200 = 50 Col
        self.assertTrue(state["companions"]["Kaelen"]["recruited"])
        self.assertTrue(state["companions"]["Kaelen"]["active"])
        self.assertEqual(len(get_active_party(state)), 2)

        # Recruit 3rd companion (Valeria with check_requirements=False)
        res_v = recruit_companion(state, "Valeria", check_requirements=False)
        self.assertTrue(res_v["success"])
        self.assertTrue(state["companions"]["Valeria"]["active"])
        self.assertEqual(len(get_active_party(state)), 3)

        # Recruit 4th companion (Garrick): Max active companions is 3, so 4th goes to reserve
        res_g = recruit_companion(state, "Garrick", check_requirements=False)
        self.assertTrue(res_g["success"])
        self.assertTrue(state["companions"]["Garrick"]["recruited"])
        self.assertFalse(state["companions"]["Garrick"]["active"])
        self.assertEqual(len(get_active_party(state)), 3)

    def test_companion_stances_and_affinity(self):
        state = copy.deepcopy(self.player_state)
        ensure_party_system(state)
        recruit_companion(state, "Valeria", check_requirements=False)

        # Stance switching
        valeria_stances = state["companions"]["Valeria"]["stances"]
        self.assertIn("aerial_divebomb", valeria_stances)
        res_stance = set_companion_stance(state, "Valeria", "aerial_divebomb")
        self.assertTrue(res_stance["success"])
        self.assertEqual(state["companions"]["Valeria"]["stance"], "aerial_divebomb")

        # Affinity progression & Dual-Tech unlock
        # Valeria starts at affinity 25, req 50 for dual tech
        res_aff = increase_companion_affinity(state, "Valeria", 35)
        self.assertTrue(res_aff["success"])
        self.assertEqual(state["companions"]["Valeria"]["affinity"], 60)
        self.assertEqual(state["companions"]["Valeria"]["affinity_tier"], "Trusted Battle-Brother/Sister")

        # Verify dual tech feat unlocked
        feats = state.get("feats", [])
        has_combo_feat = any("Valkyrie's Sky-Cleave" in f for f in feats)
        self.assertTrue(has_combo_feat, f"Expected dual-tech feat in {feats}")

        # Execute dual tech
        dt_res = execute_dual_tech(state, "valkyries_wrath")
        self.assertTrue(dt_res["success"])
        self.assertIn("VALKYRIE'S SKY-CLEAVE", dt_res["log"])

    def test_gyrus_patchwork_and_1_in_10_stage_act(self):
        import backend.mechanics as mechanics
        import backend.persona_engine as persona_engine
        self.assertEqual(len(mechanics.GYRUS_DONOR_PATCHES), 7)
        self.assertEqual(len(mechanics.GYRUS_STAGE_ACT_TABLE), 7)

        state = copy.deepcopy(self.player_state)
        state["personal_relic"] = "Miniature Elder Brain Prototype ('Gyrus the Ancient')"
        self.assertTrue(mechanics.has_gyrus_present(state))

        # Simulate 9 rounds where random roll does not proc (rng_val=0.95 >= 0.20)
        for r in range(1, 10):
            res = mechanics.advance_gyrus_stage_act_counter(state, rng_val=0.95)
            self.assertFalse(res["stage_act_triggered"], f"Should not trigger on round {r} when rng_val=0.95")
            self.assertEqual(res["rounds_since_stage_act"], r)

        # On the 10th round (rounds_since == 9), even with rng_val=0.99, the 10-round pity guarantee MUST fire!
        res_10 = mechanics.advance_gyrus_stage_act_counter(state, rng_val=0.99)
        self.assertTrue(res_10["stage_act_triggered"], "10th round MUST guarantee stage-act trigger!")
        self.assertEqual(res_10["trigger_reason"], "10_round_pity_guarantee")
        self.assertEqual(res_10["rounds_since_stage_act"], 0)
        self.assertIsNotNone(res_10["stage_act"])

        # Verify persona_engine offline action includes Gyrus when relic is carried
        actions = persona_engine.run_all_room_subagents(
            api_key="",
            visible_room={"environment": {"location": "Test Vault", "environmental_effects": []}, "entities": []},
            player_action="Inspect the terminal.",
            player_state=state
        )
        actor_ids = [a.get("actor_id") for a in actions]
        self.assertIn("companion_gyrus", actor_ids)

if __name__ == "__main__":
    unittest.main()
