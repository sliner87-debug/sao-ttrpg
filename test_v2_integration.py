"""
Test suite for SAO Sandbox V2 Integration:
Validates Hybrid Grafting (Biological + Golem), Ability Fusion Protocol,
4-Member Vanguard Companion Matrix, and Decoupled Staging Ground.
"""

import json
import os
import unittest
import backend.mechanics as mechanics

class TestV2Integration(unittest.TestCase):
    def setUp(self):
        self.player = {
            "name": "Banki",
            "race": "Unregistered Anomaly",
            "class": "Wyrd-Weaver / Battleaxe Vanguard",
            "level": 3,
            "hp": 95,
            "max_hp": 100,
            "col": 10000,
            "stats": {"STR": 16, "DEX": 14, "CON": 16, "INT": 14, "WIS": 12, "CHA": 10},
            "location": "Sector 1 Safe-Zone: Washington Borough, NJ",
            "skills": {
                "Battleaxe Mastery": {"mastery": 150, "description": "Proficiency with heavy axes."},
                "Arcana": {"mastery": 200, "description": "Elder runes and matrices."}
            },
            "feats": ["Runic Inscription"],
            "spells": ["Earth Tremor Hex", "Major Force Missile"],
            "equipped": {
                "head": "None", "chest": "Reinforced Leather",
                "main_hand": "Enchanted Bearded Axe", "off_hand": "None", "accessory": "None"
            },
            "inventory": []
        }
        mechanics.ensure_graft_system(self.player)
        mechanics.ensure_party_system(self.player)
        mechanics.ensure_chrono_system(self.player)
        mechanics.ensure_homestead_system(self.player)

    def test_hybrid_grafting_biological_and_golem(self):
        """Validates that players can install BOTH biological beast grafts and golem grafts."""
        p = self.player
        # 1. Install Biological Graft: Basalt Carapace Plating into Torso
        bio_res = mechanics.install_graft(p, "basalt_carapace_plating", "torso")
        self.assertTrue(bio_res["success"], bio_res.get("message"))
        self.assertEqual(bio_res["graft"]["type"], "biological")
        self.assertIn("basalt_carapace_plating", [g["key"] for g in p["graft_system"]["installed_grafts"].values()])

        # 2. Install Golem Graft: Golem Hydraulic Arm into Arm Left
        golem_res = mechanics.install_graft(p, "golem_hydraulic_arm", "arm_left")
        self.assertTrue(golem_res["success"], golem_res.get("message"))
        self.assertIn("golem_hydraulic_arm", [g["key"] for g in p["graft_system"]["installed_grafts"].values()])

        # 3. Check Spell Penalty (Biological should NOT count towards metallic spell penalty)
        p["class"] = "Aether-Slinger"
        penalty_info = mechanics.calculate_spellcasting_graft_penalty(p)
        # Only 1 tech graft (golem_hydraulic_arm), biological graft is ignored
        self.assertEqual(penalty_info["total_grafts"], 1)

    def test_ability_fusion_protocol(self):
        """Validates fusing two abilities into a unique synergistic technique."""
        p = self.player
        start_xp = p.get("xp", 0)
        fusion_res = mechanics.fuse_abilities(
            p,
            component_a_name="Battleaxe Mastery",
            component_b_name="Earth Tremor Hex",
            custom_fused_name="Tremor-Quake Cleave",
            custom_desc="Channels seismic shockwaves through axe impact, knocking foes prone."
        )
        self.assertTrue(fusion_res["success"])
        self.assertEqual(fusion_res["fused_name"], "Tremor-Quake Cleave")
        self.assertEqual(p["xp"], start_xp + 15)
        
        # Verify it appears in fused_abilities list and feats
        fused_list = mechanics.get_fused_abilities(p)
        self.assertEqual(len(fused_list), 1)
        self.assertEqual(fused_list[0]["name"], "Tremor-Quake Cleave")
        self.assertTrue(any("Tremor-Quake Cleave" in f for f in p["feats"]))

    def test_four_companion_sheets_exist(self):
        """Verifies all 4 companions exist in Party/ and Entities/ with correct attributes."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        party_dir = os.path.join(base_dir, "Party")
        entities_dir = os.path.join(base_dir, "Entities")

        expected_ids = ["companion_ren", "companion_elora", "companion_torvald", "companion_kibs"]
        for cid in expected_ids:
            p_path = os.path.join(party_dir, f"{cid}.json")
            e_path = os.path.join(entities_dir, f"{cid}.json")
            self.assertTrue(os.path.exists(p_path), f"Missing {p_path}")
            self.assertTrue(os.path.exists(e_path), f"Missing {e_path}")

            with open(p_path, "r", encoding="utf-8") as f:
                p_data = json.load(f)
            self.assertIn("name", p_data)
            self.assertIn("hp", p_data)
            self.assertIn("behavior_prompt", p_data)

            with open(e_path, "r", encoding="utf-8") as f:
                e_data = json.load(f)
            self.assertIn("backstory_interview", e_data)
            self.assertIn("personality", e_data)

    def test_ren_harmonized_persona(self):
        """Verifies Ren is characterized as a 17yo game tester with MageTech firearms."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        p_path = os.path.join(base_dir, "Party", "companion_ren.json")
        with open(p_path, "r", encoding="utf-8") as f:
            ren = json.load(f)

        self.assertIn("17", ren.get("role", "") + ren.get("behavior_prompt", ""))
        inv_names = [it.get("name") if isinstance(it, dict) else it for it in ren.get("inventory", [])]
        self.assertIn("Aether-Lock Carbine", inv_names)
        self.assertIn("not gunpowder", ren.get("behavior_prompt", "").lower())
        self.assertIn("mana bolts", ren.get("behavior_prompt", "").lower())

    def test_dynamic_equipped_gear_visuals_and_item_descriptions(self):
        """Verifies every item in save files and Party sheets is fully described and Image Generator updates dynamically with equipped gear."""
        import backend.mechanics as mechanics
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # 1. Verify all items in save_game.json and Party/*.json have full desc and visual_appearance
        with open(os.path.join(base_dir, "save_game.json"), "r", encoding="utf-8") as f:
            save_data = json.load(f)
        player = save_data["player"]
        for item in player.get("inventory", []):
            self.assertIsInstance(item, dict)
            self.assertTrue(len(item.get("desc", "")) > 15, f"Missing full desc on {item}")
            self.assertTrue(len(item.get("visual_appearance", "")) > 10, f"Missing visual_appearance on {item}")

        party_dir = os.path.join(base_dir, "Party")
        for fname in os.listdir(party_dir):
            if fname.endswith(".json"):
                with open(os.path.join(party_dir, fname), "r", encoding="utf-8") as f:
                    c_data = json.load(f)
                self.assertIn("equipped", c_data, f"Missing equipped dict in {fname}")
                for item in c_data.get("inventory", []):
                    self.assertIsInstance(item, dict, f"Un-enriched item in {fname}: {item}")
                    self.assertTrue(len(item.get("desc", "")) > 15, f"Missing desc in {fname}: {item}")
                    self.assertTrue(len(item.get("visual_appearance", "")) > 10, f"Missing visual_appearance in {fname}: {item}")

        # 2. Verify build_character_visual_profile updates dynamically when equipped gear changes
        p_copy = json.loads(json.dumps(player))
        p_copy["equipped"] = {
            "head": "None",
            "chest": "Reinforced Leather",
            "main_hand": "Enchanted Bearded Axe",
            "off_hand": "Free (Somatic Futhark Casting)",
            "accessory": "None"
        }
        vis_leather_axe = mechanics.build_character_visual_profile(p_copy, entity_id="banki")
        self.assertIn("Reinforced Leather", vis_leather_axe)
        self.assertIn("Enchanted Bearded Axe", vis_leather_axe)
        self.assertNotIn("Einherjar Overdrive Rig", vis_leather_axe)

        # Swap equipped gear to Einherjar Rig and Heavy Trench Hammer + install a Graft
        p_copy["equipped"]["chest"] = "Einherjar Overdrive Rig"
        p_copy["equipped"]["main_hand"] = "Heavy Trench Hammer"
        p_copy["grafts"]["left_arm"] = "Golem Hydraulic Arm"
        vis_rig_hammer = mechanics.build_character_visual_profile(p_copy, entity_id="banki")
        self.assertIn("Einherjar Overdrive Rig", vis_rig_hammer)
        self.assertIn("Heavy Trench Hammer", vis_rig_hammer)
        self.assertIn("Golem Hydraulic Arm", vis_rig_hammer)
        self.assertNotIn("Reinforced Leather", vis_rig_hammer)

if __name__ == "__main__":
    unittest.main()
