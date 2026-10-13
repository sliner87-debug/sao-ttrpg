"""
Test suite for SAO Sandbox V2 Integration:
Validates Hybrid Grafting (Biological + Golem), Ability Fusion Protocol,
4-Member Vanguard Companion Matrix, and Decoupled Staging Ground.
"""

import json
import os
import unittest
from unittest.mock import patch, MagicMock
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
        """Validates fusing two skills/abilities replaces them with a [Fusion] Skill and allows relearning a Base skill."""
        p = self.player
        p["skills"] = {
            "Battleaxe Mastery": {"mastery": 60, "description": "Heavy cleaving axe techniques."},
            "Earth Tremor Hex": {"mastery": 40, "description": "Seismic ground-shattering runes."}
        }
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
        self.assertEqual(fusion_res["fusion_skill_key"], "[Fusion] Tremor-Quake Cleave")
        self.assertEqual(p["xp"], start_xp + 15)

        # Verify previous two skills were consumed and replaced by [Fusion] Tremor-Quake Cleave
        self.assertNotIn("Battleaxe Mastery", p["skills"])
        self.assertNotIn("Earth Tremor Hex", p["skills"])
        self.assertIn("[Fusion] Tremor-Quake Cleave", p["skills"])
        self.assertEqual(p["skills"]["[Fusion] Tremor-Quake Cleave"]["mastery"], 80)
        
        # Verify it appears in fused_abilities list and feats
        fused_list = mechanics.get_fused_abilities(p)
        self.assertEqual(len(fused_list), 1)
        self.assertEqual(fused_list[0]["name"], "Tremor-Quake Cleave")
        self.assertTrue(any("Tremor-Quake Cleave" in f for f in p["feats"]))

        # Verify consumed base skills can be relearned while keeping the [Fusion] Skill
        relearnable = mechanics.get_relearnable_base_skills(p)
        fused_relearn_names = [r["name"] for r in relearnable if r.get("was_fused")]
        self.assertIn("Battleaxe Mastery", fused_relearn_names)
        self.assertIn("Earth Tremor Hex", fused_relearn_names)

        relearn_res = mechanics.relearn_base_skill(p, "Battleaxe Mastery", starting_mastery=1)
        self.assertTrue(relearn_res["success"])
        self.assertIn("Battleaxe Mastery", p["skills"])
        self.assertEqual(p["skills"]["Battleaxe Mastery"]["mastery"], 1)
        self.assertIn("[Fusion] Tremor-Quake Cleave", p["skills"])

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

    def test_spells_and_powers_compendium_and_mechanics(self):
        """Verifies every spell, feat, racial ability, and milestone power resolves full description and game mechanics."""
        import backend.mechanics as mechanics
        import backend.character_generator as cg
        base_dir = os.path.dirname(os.path.abspath(__file__))

        with open(os.path.join(base_dir, "save_game.json"), "r", encoding="utf-8") as f:
            player = json.load(f)["player"]

        all_sp = mechanics.get_all_player_spells_and_powers(player)
        self.assertGreaterEqual(len(all_sp), 3)
        names = [x["name"] for x in all_sp]
        self.assertIn("Major Force Missile", names)
        self.assertIn("Earth Tremor Hex", names)
        self.assertIn("Runic Inscription (Elder Futhark)", names)

        for sp in all_sp:
            self.assertTrue(len(sp.get("description", "")) > 25, f"Missing description on {sp}")
            self.assertTrue(len(sp.get("mechanics", "")) > 25, f"Missing mechanics on {sp}")
            self.assertTrue(bool(sp.get("action_type")), f"Missing action_type on {sp}")
            self.assertTrue(bool(sp.get("cost")), f"Missing cost on {sp}")

        # Verify all starting class powers and racial abilities resolve cleanly
        for c_key, c_data in cg.CLASS_PATHS.items():
            for feat_name in c_data.get("starting_feats", []):
                det = mechanics.get_spell_or_power_details(feat_name)
                self.assertTrue(len(det["description"]) > 15, f"Missing description for class feat {feat_name}")
                self.assertTrue(len(det["mechanics"]) > 15, f"Missing mechanics for class feat {feat_name}")

        for r_key, r_data in cg.RACIAL_LINEAGES.items():
            for rab in r_data.get("racial_abilities", []):
                det = mechanics.get_spell_or_power_details(rab)
                self.assertTrue(len(det["description"]) > 15, f"Missing description for racial ability {rab}")
                self.assertTrue(len(det["mechanics"]) > 15, f"Missing mechanics for racial ability {rab}")

    def test_system_initialization_welcome_message(self):
        """Verifies V2's new System Initialization welcome message meets all LitRPG criteria."""
        import backend.character_generator as cg
        test_player = {
            "name": "Caelen",
            "race": "MageTech Cyborg",
            "class": "Aether-Slinger",
            "hp": 95,
            "max_hp": 95,
            "col": 100,
            "skills": {
                "Arcane Ballistics": {"mastery": 55, "tier": "Apprentice"},
                "Software Architecture": {"mastery": 45, "tier": "Novice"}
            },
            "equipped": {
                "main_hand": "Aether-Lock Carbine",
                "off_hand": "None",
                "chest": "Reinforced Leather",
                "accessory": "Titanium Multi-Tool"
            },
            "inventory": [
                {
                    "name": "Titanium Multi-Tool",
                    "category": "Keepsake Relic",
                    "desc": "Nineteen tools in one aerospace titanium chassis.",
                    "mechanics": "Bypasses standard tool requirements for field repairs."
                }
            ]
        }

        msg = cg.build_system_initialization_welcome_message(test_player)

        # 1. System Apocalypse Tone & Geography
        self.assertIn("SYSTEM INITIALIZATION: PLANETARY INTEGRATION COMPLETE", msg)
        self.assertIn("SECTOR 01: NORTH AMERICAN CONTINENTAL ZONE // NODE 07882: WASHINGTON BOROUGH, NEW JERSEY", msg)
        self.assertIn("Route 31 and Route 57", msg)
        self.assertIn("Oxford Furnace", msg)
        self.assertIn("Pohatcong Mountain", msg)

        # 2. Biometric & Relic Ledger with exact entered Character Name
        self.assertIn("**Caelen**", msg)
        self.assertIn("MageTech Cyborg", msg)
        self.assertIn("Aether-Slinger", msg)
        self.assertIn("Titanium Multi-Tool", msg)
        self.assertIn("Arcane Ballistics", msg)

        # 3. Sardonic Architect Broadcast (DCC style)
        self.assertIn("SYSTEM ARCHITECT EVALUATION", msg)
        self.assertIn("Software", msg)
        self.assertIn("Calculated Survival Index", msg)

        # 4. Initial Scenario #001 & In-Universe Interface Directives
        self.assertIn("INITIAL SCENARIO #001: SURVIVE THE FIRST CALIBRATION WAVE", msg)
        self.assertIn("CARDINAL INTERFACE DIRECTIVES", msg)
        self.assertIn("Autonomous Battle-Companions", msg)
        self.assertIn("Cardinal Ability Fusion Chamber", msg)
        self.assertIn("Bio-Surgical Grafting & Strain Tolerance", msg)
        self.assertIn("Neural Voice Link", msg)

    @patch("google.genai.Client")
    def test_npc_player_name_dynamic_binding(self, mock_client_cls):
        """Verifies that all SubAgent persona prompts bind the exact entered player name and purge Banki."""
        import backend.persona_engine as persona_engine
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "actor_id": "companion_ren",
            "internal_thought": "Vesper needs cover on the perimeter.",
            "intended_action": "Draws carbine and watches the entrance."
        })
        mock_client.models.generate_content.return_value = mock_response

        p = {"name": "Vesper", "race": "Pure Human", "class": "Bulwark Vanguard"}
        
        # Test raw persona file
        persona_path = os.path.join(os.path.dirname(__file__), "Entities", "companion_ren.json")
        with open(persona_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        
        # Raw file should not contain hardcoded Banki
        self.assertNotIn("Banki", raw_text)

        # In run_all_room_subagents / get_subagent_action, player_name Vesper must be bound
        subagent_actions = persona_engine.run_all_room_subagents(
            api_key="mock_key_test",
            visible_room={
                "environment": {"location": "Washington Borough Safe-Zone", "environmental_effects": ["Safe-Zone Sanctuary Wards"]},
                "entities": []
            },
            active_party=["companion_ren"],
            player_action="I check my weapons.",
            player_state=p
        )
        self.assertGreaterEqual(len(subagent_actions), 1)

        # Inspect the prompt passed to Gemini: must contain 'Vesper' and zero occurrences of 'Banki'
        call_kwargs = mock_client.models.generate_content.call_args[1]
        sent_prompt = call_kwargs["contents"]
        self.assertIn("Vesper", sent_prompt)
        self.assertNotIn("Banki", sent_prompt)

    def test_washington_100_mile_atlas(self):
        """Verifies the 100-mile Washington NJ World Atlas, regional salvage yields, travel telemetry, and Cartography 1-1000 support."""
        import map_engine

        # 1. Verify all 4 categories and all 4 quadrants are populated
        self.assertGreaterEqual(len(mechanics.WORLD_ATLAS_ZONES), 55)
        for cat in ["safe_zone", "mine", "dungeon", "wilderness"]:
            cat_zones = mechanics.get_zones_by_category(category=cat)
            self.assertGreaterEqual(len(cat_zones), 10, f"Expected >= 10 zones for category {cat}")

        for quad in [
            "Inner Core (0–25 mi)",
            "North & East (25–100 mi)",
            "West & Northwest (25–100 mi)",
            "South & Southwest (25–100 mi)",
        ]:
            q_zones = mechanics.get_zones_by_category(quadrant=quad)
            self.assertGreaterEqual(len(q_zones), 10, f"Expected >= 10 zones for quadrant {quad}")

        # 2. Verify safe-zone detection across the 100-mile radius
        self.assertTrue(mechanics.is_location_safe_zone("Sector 1 Safe-Zone: Washington Borough, NJ"))
        self.assertTrue(mechanics.is_location_safe_zone("West Point Granite Bastion & Bullion Vaults"))
        self.assertTrue(mechanics.is_location_safe_zone("Jim Thorpe Gorge Bastion"))
        self.assertTrue(mechanics.is_location_safe_zone("Princeton Arcane Conclave & Nassau Sanctuary"))
        self.assertFalse(mechanics.is_location_safe_zone("Centralia Hellfire Abyssal Breach"))
        self.assertFalse(mechanics.is_location_safe_zone("Picatinny Artificer Siege Citadel"))

        # 3. Verify regional salvage yields in a specific mine (Sterling Hill & Centralia)
        p = self.player
        p["location"] = "Sterling Hill & Franklin Fluorescent Zinc Mines, NJ"
        salv_res = mechanics.salvage_materials(p, target_type="ruins", d20_roll=16)
        self.assertTrue(salv_res["success"])
        harvested_names = [it["name"] for it in salv_res["items"]]
        self.assertIn("Neon Willemite Shards", harvested_names)

        # 4. Verify travel telemetry and GM briefing formatting
        telem = mechanics.calculate_travel_telemetry("Washington Borough", "centralia_pioneer_breach", p)
        self.assertGreater(telem["distance_miles"], 70.0)
        self.assertGreater(telem["travel_minutes"], 60)
        briefing = mechanics.format_zone_gm_briefing(mechanics.resolve_zone_from_location("Centralia"))
        self.assertIn("Centralia", briefing)
        self.assertIn("IGNIS-62", briefing)

        # 5. Verify expanded regional Homestead Estates
        self.assertIn("washington_manor", mechanics.HOMESTEAD_ESTATES)
        self.assertIn("oxford_foundry_estate", mechanics.HOMESTEAD_ESTATES)
        self.assertIn("pocono_wilderness_lodge", mechanics.HOMESTEAD_ESTATES)

        # 6. Verify map_engine Oxford_Mines coordinates and V2 1-1000 Cartography skill support
        self.assertEqual(map_engine.NODES["Oxford_Mines"]["x"], 53)
        self.assertEqual(map_engine.NODES["Oxford_Mines"]["y"], 48)
        self.assertFalse(map_engine.has_cartography_skill("Cartography I", {"Cartography": {"mastery": 25}}))
        self.assertTrue(map_engine.has_cartography_skill("Cartography I", {"Cartography": {"mastery": 55}}))
        self.assertTrue(map_engine.has_cartography_skill("Cartography II", {"Cartography": {"mastery": 120}}))

    def test_multi_universe_bestiary_and_races_dispersion(self):
        """Verifies all 45 fantasy races, multi-universe bestiary entries, 58-zone dispersion, and monster grafts."""
        import backend.character_generator as cg

        # 1. Verify 45 playable & world fantasy lineages
        self.assertGreaterEqual(len(cg.RACIAL_LINEAGES), 45)
        for req_race in [
            "underdark_drow", "duergar_deep_dwarf", "svirfneblin_deep_gnome",
            "halfling_shireborn", "rock_gnome_tinker", "goliath_cragborn",
            "firbolg_forest_keeper", "tabaxi_catfolk", "kenku_tengu",
            "kitsune_nine_tails", "leshy_botanical_spirit", "githyanki_astral_raider",
            "githzerai_limbo_monk", "tortle_shellback", "aarakocra_owlin",
            "yuan_ti_vishkanya", "witcher_mutant_hound", "viera_miqote_beastkin",
            "dunmer_ashlander", "skaven_ratfolk_ysoki", "dhampir_bloodborne",
            "conrasu_aeon_shard", "anadi_weaver", "hobgoblin_legionnaire", "kobold_trapwright"
        ]:
            self.assertIn(req_race, cg.RACIAL_LINEAGES)

        # 2. Verify multi-universe Bestiary search across D&D, Pathfinder, Witcher, FF, Monster Hunter, SAO
        for universe in ["D&D", "Pathfinder", "The Witcher", "Final Fantasy", "Monster Hunter", "Sword Art Online"]:
            matches = mechanics.search_bestiary(origin_system=universe)
            self.assertGreaterEqual(len(matches), 1, f"Expected creatures for universe {universe}")

        # 3. Verify all 58 zones in WORLD_ATLAS_ZONES have resident_races and dispersed_monsters
        for z_id, z_data in mechanics.WORLD_ATLAS_ZONES.items():
            self.assertTrue(len(z_data.get("resident_races", [])) >= 2, f"Zone {z_id} missing resident_races")
            self.assertTrue(len(z_data.get("dispersed_monsters", [])) >= 1, f"Zone {z_id} missing dispersed_monsters")

        # 4. Verify installing new multi-universe monster grafts (e.g. Displacer Tentacle Mantle & Beholder Ocular)
        p = self.player
        res1 = mechanics.install_graft(p, "displacer_tentacle_mantle", "spine")
        self.assertTrue(res1["success"], res1.get("message"))
        res2 = mechanics.install_graft(p, "beholder_antimagic_ocular", "ocular")
        self.assertTrue(res2["success"], res2.get("message"))


if __name__ == "__main__":
    unittest.main()



