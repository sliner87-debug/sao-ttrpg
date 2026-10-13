"""
Comprehensive Automated Playtest & Verification Suite for SAO Sandbox V2
Tests the entire game loop end-to-end:
1. Character Creation (5-Stage Wizard, 18 Lifestyles, 20 Vocations, Thematic Conscript Lineages, Relics)
2. Character-Folder Save/Load Architecture (saves/<name>/) & Master State Sync
3. Chrono & Weather System (Time progression, atmospheric shifts, frostbite checks)
4. Party Dynamics & Autonomous Companion Engine (Ren stances, affinity, dual-techs)
5. 1-1000 Skill Mastery Engine (Task DC scaling, exponential decay, milestone auto-unlocks)
6. Equipment Durability, Degradation & Field Repair
7. Golem-Graft Surgery, Biomechanical Strain & Cyborg Synergies
8. Field Trapping & Environmental Scavenging
9. Homestead Real Estate & Economic Transactions
10. Factions, Bounties & Global Threat Intelligence
11. Class Evolution (Harmonized Dual-Gate, Level/Boss/Skill thresholds, +25% pool scaling)
12. Decoupled Staging Ground & Turn Component Extraction
"""

import os
import sys
import json
import time
import shutil
import tempfile
import unittest

# Ensure working directory is V2 root
V2_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, V2_ROOT)

import backend.mechanics as mechanics
import backend.character_generator as cg
import backend.gm_engine as gm_engine


class TestV2FullPlaytest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp(prefix="sao_v2_playtest_")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_01_avatar_calibration_and_thematic_conscripts(self):
        """Test Stage 1-5 Character Calibration with MageTech Cyborg & Relic mechanics."""
        # 1. Preset Lifestyle: Off-Grid Homesteader (STR 4, DEX 3, CON 6, INT 1, WIS 5, CHA 1 = 20)
        pts = cg.PRESET_LIFESTYLES["offgrid_homesteader"]["points"]
        self.assertEqual(sum(pts.values()), 20)

        # 2. Vocation: Electrician / Lineworker
        bg_key = "electrician_lineworker"
        bg_data = cg.PRESET_BACKGROUNDS[bg_key]
        self.assertIn("Magi-Tech Wiring", bg_data["skills"])
        self.assertIn("Kinetic Insulation", bg_data["skills"])

        # 3. Lineage: MageTech Cyborg (Crucible Conscript)
        race_key = "neuromancer_cyborg"
        race_data = cg.RACIAL_LINEAGES[race_key]
        self.assertEqual(race_data["name"], "MageTech Cyborg (Crucible Conscript)")
        self.assertEqual(race_data["genre"], "MageTech / Biomechanical")
        self.assertIn("Cardinal Telemetry Ocular", race_data["racial_abilities"][0])
        self.assertIn("Pneumatic Endoskeleton", race_data["racial_abilities"][1])
        self.assertIn("Innate Graft-Tolerance", race_data["racial_abilities"][2])
        self.assertIn("Flaw - Arc & EMP Conductivity", race_data["racial_abilities"][3])

        # 4. Generate Starting Character
        char = cg.generate_starting_character(
            name="Kaelen Vex",
            point_alloc=pts,
            background_key=bg_key,
            race_key=race_key,
            class_key="warrior",
            relic_key="multitool",
            starting_weapons={"main_hand": "Heavy Scavenged Mace", "off_hand": "Scrap-Plate Shield"}
        )

        # Verify Core Stats Math: Base 10 + points + racial mods
        # STR: 10 + 4 + 2 = 16
        # DEX: 10 + 3 + 1 = 14
        # CON: 10 + 6 + 2 = 18 -> con_mod = (18 - 10)//2 = 4
        # INT: 10 + 1 + 1 = 12
        # WIS: 10 + 5 - 1 = 14
        # CHA: 10 + 1 - 1 = 10
        self.assertEqual(char["stats"]["STR"], 16)
        self.assertEqual(char["stats"]["DEX"], 14)
        self.assertEqual(char["stats"]["CON"], 18)
        self.assertEqual(char["stats"]["INT"], 12)
        self.assertEqual(char["stats"]["WIS"], 14)
        self.assertEqual(char["stats"]["CHA"], 10)

        # Base HP: Warrior (120) + (4 * 10) = 160
        self.assertEqual(char["max_hp"], 160)
        self.assertEqual(char["hp"], 160)

        # Verify Relic in inventory and Feat attunement
        inv_names = [i["name"] for i in char["inventory"]]
        self.assertIn("Mechanic's Heavy Multi-Tool", inv_names)
        self.assertTrue(any("Relic Attunement (Mechanic's Heavy Multi-Tool)" in f for f in char["feats"]))

        # Verify Starting Skills & Tiers
        self.assertIn("Magi-Tech Wiring", char["skills"])
        self.assertIn("Kinetic Insulation", char["skills"])
        self.assertEqual(char["skills"]["Magi-Tech Wiring"]["tier"], "Apprentice")
        self.assertEqual(char["skills"]["Magi-Tech Wiring"]["mastery"], 50)

        # Save to character-specific folder
        save_path = cg.save_character_to_folder(self.test_dir, char)
        self.assertTrue(os.path.exists(save_path))
        profile_path = os.path.join(os.path.dirname(save_path), "profile.json")
        self.assertTrue(os.path.exists(profile_path))

        with open(profile_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        self.assertEqual(meta["name"], "Kaelen Vex")
        self.assertEqual(meta["race"], "MageTech Cyborg (Crucible Conscript)")

    def test_02_synthetic_android_lineage_and_relic_mechanics(self):
        """Test Synthetic Android (Printed Soul-Vessel) and Custom Relic generation."""
        android_data = cg.RACIAL_LINEAGES["synthetic_android"]
        self.assertEqual(android_data["name"], "Synthetic Android (Printed Soul-Vessel)")
        self.assertEqual(android_data["genre"], "Pathfinder / Bio-Synthetic")
        self.assertEqual(android_data["stat_mods"]["INT"], 3)
        self.assertEqual(android_data["stat_mods"]["CHA"], -2)

        # Custom Relic Generation
        custom_relic = cg.create_custom_relic(
            name="Grandmother's Silver Locket",
            desc="Tarnished silver locket with a faded portrait of family on old Earth.",
            ability_text="+2 on saving throws against psychic dread and despair"
        )
        self.assertEqual(custom_relic["category"], "Custom Keepsake")
        self.assertEqual(custom_relic["mechanics"], "+2 on saving throws against psychic dread and despair")

        char = cg.generate_starting_character(
            name="Unit-7",
            point_alloc={"STR": 2, "DEX": 5, "CON": 4, "INT": 5, "WIS": 3, "CHA": 1},
            background_key="software_engineer",
            race_key="synthetic_android",
            class_key="mage",
            relic_key="custom",
            custom_relic_data=custom_relic
        )
        self.assertIn("Unit-7", char["name"])
        self.assertTrue(any("Keepsake Resonator: +2 on saving throws" in f for f in char["feats"]))
        self.assertTrue(any("Nanite Surge" in f for f in char["feats"]))

    def test_03_chrono_weather_and_campfire_system(self):
        """Simulate time advancement, weather changes, and culinary crafting."""
        player = {
            "name": "Kaelen", "level": 1, "hp": 50, "max_hp": 100,
            "inventory": [
                {"name": "Wolf Marrow", "qty": 3},
                {"name": "Wild Roots", "qty": 2},
                {"name": "Bottled Water", "qty": 2}
            ]
        }
        mechanics.ensure_chrono_system(player)
        init_time = player["chrono"]["hour"]

        # Advance 2 hours (120 minutes)
        res = mechanics.advance_game_time(player, minutes=120)
        self.assertEqual(player["chrono"]["hour"], (init_time + 2) % 24)
        self.assertIn("time_str", res)

        # Roll dynamic weather
        w_res = mechanics.roll_random_weather(player)
        self.assertIn("weather_info", w_res)
        self.assertIn("label", w_res["weather_info"])

        # Check frost hazard logic
        frost_check = mechanics.check_frost_hazard(player)
        self.assertIn("protected", frost_check)

        # Cook Campfire Stew
        stew_res = mechanics.cook_campfire_recipe(player, "wolf_heart_stew")
        self.assertTrue(stew_res["success"], stew_res.get("message"))
        self.assertGreater(player["hp"], 50)
        self.assertTrue(any("Wolf-Heart Vigor" in b["name"] for b in player["chrono"]["active_buffs"]))

    def test_04_party_stances_affinity_and_dual_techs(self):
        """Test Ren's companion sheet, stance switching, affinity growth, and combo execution."""
        player = {
            "name": "Kaelen", "col": 500, "hp": 100, "max_hp": 100,
            "companions": {}
        }
        mechanics.ensure_party_system(player)
        self.assertIn("Ren", player["companions"])
        ren = player["companions"]["Ren"]

        # Stance Switching
        s_res = mechanics.set_party_member_stance(player, "Ren", "suppression_fire")
        self.assertTrue(s_res["success"])
        self.assertEqual(ren["stance"], "suppression_fire")

        # Increase Affinity via Meal Sharing
        aff_res = mechanics.increase_companion_affinity(player, "Ren", amount=40, reason="Shared campfire feast")
        self.assertEqual(ren["affinity"], 75)
        self.assertEqual(ren["affinity_tier"], "Soul-Bonded Partner")

        # Execute Dual-Tech Combo
        dt_res = mechanics.execute_dual_tech(player, "runic_axe_storm")
        self.assertTrue(dt_res["success"], dt_res.get("message"))
        self.assertIn("DUAL-TECH", dt_res["log"])

    def test_05_skill_mastery_progression_and_milestones(self):
        """Test 1-1000 skill progression, DC decay curve, and milestone auto-unlocks."""
        player = {
            "name": "Kaelen", "level": 1, "feats": [], "spells": [],
            "skills": {
                "One-Handed Axes": {
                    "mastery": 48,
                    "tier": "Novice",
                    "description": "One-handed axe combat.",
                    "milestones_unlocked": []
                }
            }
        }

        # Mathematical Gain check: DC 15 action
        gain_low = mechanics.calculate_mastery_gain(current_mastery=48, task_dc=15)
        gain_high = mechanics.calculate_mastery_gain(current_mastery=600, task_dc=15)
        self.assertGreater(gain_low, gain_high, "Gain must experience exponential decay at higher tiers!")

        # Advance mastery from 48 across threshold 50 (Apprentice)
        res_50 = mechanics.update_skill_mastery(player, "One-Handed Axes", amount=3, is_dc=False)
        self.assertGreaterEqual(player["skills"]["One-Handed Axes"]["mastery"], 51)
        self.assertEqual(player["skills"]["One-Handed Axes"]["tier"], "Apprentice")
        self.assertEqual(len(res_50["milestones_triggered"]), 1)
        self.assertEqual(res_50["milestones_triggered"][0]["name"], "Hewing Edge")
        self.assertTrue(any("Hewing Edge" in f for f in player["feats"]))

        # Advance mastery to 100 (Journeyman Active Sword Skill)
        res_100 = mechanics.update_skill_mastery(player, "One-Handed Axes", amount=50, is_dc=False)
        self.assertGreaterEqual(player["skills"]["One-Handed Axes"]["mastery"], 101)
        self.assertEqual(player["skills"]["One-Handed Axes"]["tier"], "Journeyman")
        self.assertTrue(any("Gale Cleave" in s for s in player["spells"]))

    def test_06_durability_breakage_and_field_repair(self):
        """Test equipment wear on hit, broken penalties, and field repair."""
        player = {
            "name": "Kaelen", "col": 1000,
            "equipped": {
                "chest": "Reinforced Scrap Tunic",
                "main_hand": "Iron Battleaxe",
                "off_hand": "None", "head": "None", "accessory": "None"
            },
            "inventory": [
                {"name": "Reinforced Scrap Tunic", "durability": 50, "max_durability": 50, "qty": 1},
                {"name": "Iron Battleaxe", "durability": 60, "max_durability": 60, "qty": 1}
            ]
        }

        # Apply durability damage
        dmg_res = mechanics.apply_durability_damage(player, "chest", amount=75)
        self.assertTrue(dmg_res["broken"])
        self.assertEqual(dmg_res["current"], 0)

        # Check AC calculation with broken armor penalty
        enc = mechanics.calculate_encumbrance(player)
        ac_broken = mechanics.calculate_ac(player, enc)
        self.assertLess(ac_broken, 15)

        # Repair item in the field
        rep_res = mechanics.repair_item(player, "chest", col_per_point=1)
        self.assertTrue(rep_res["success"])
        self.assertEqual(rep_res["new_durability"], 75)
        self.assertEqual(player["col"], 1000 - 75)

    def test_07_golem_grafts_and_strain_capacity(self):
        """Test Golem-Graft installation, strain threshold, and Cyborg synergized limit."""
        player = {
            "name": "Kaelen", "level": 1, "col": 5000,
            "race": "MageTech Cyborg (Crucible Conscript)",
            "stats": {"STR": 16, "CON": 16, "INT": 12, "DEX": 14, "WIS": 15, "CHA": 10},
            "feats": ["Innate Graft-Tolerance: Baseline Golem-Graft Strain threshold is increased by +15"]
        }
        mechanics.ensure_graft_system(player)

        # Baseline strain threshold for Cyborg (CON 16 = 32 + 3 + 15 = 50 max strain)
        strain_data = mechanics.calculate_player_strain(player)
        self.assertGreaterEqual(strain_data["max_strain"], 50)

        # Install Golem Hydraulic Arm
        g_res = mechanics.install_graft(player, "golem_hydraulic_arm", "arm_left")
        self.assertTrue(g_res["success"], g_res.get("message"))
        self.assertEqual(player["graft_system"]["installed_grafts"]["arm_left"]["key"], "golem_hydraulic_arm")

        # Install Aether-Resonant Ocular
        o_res = mechanics.install_graft(player, "aether_resonant_ocular", "ocular")
        self.assertTrue(o_res["success"], o_res.get("message"))
        self.assertEqual(player["graft_system"]["installed_grafts"]["ocular"]["key"], "aether_resonant_ocular")

        # Check total strain remains within threshold
        new_strain = mechanics.calculate_player_strain(player)
        self.assertLessEqual(new_strain["current_strain"], new_strain["max_strain"])
        self.assertFalse(new_strain["is_overloaded"])

    def test_08_field_trapping_and_salvaging(self):
        """Test trap placement with natural roll, and monster salvage extraction."""
        player = {
            "name": "Kaelen",
            "inventory": [
                {"name": "Heavy Highway Snares", "qty": 1},
                {"name": "Carbon Line Spools", "qty": 1}
            ]
        }

        # Rig Heavy Highway Snare (Roll 18)
        t_res = mechanics.rig_field_trap(player, "heavy_highway_snare", d20_roll=18)
        self.assertTrue(t_res["success"], t_res.get("log"))
        self.assertEqual(t_res["trap"]["key"], "heavy_highway_snare")
        self.assertIn("snare", t_res["log"].lower())

        # Scavenge Cyber Construct
        s_res = mechanics.salvage_materials(player, "construct", d20_roll=17)
        self.assertTrue(s_res["success"])
        self.assertGreater(len(s_res["items"]), 0)
        self.assertGreater(len(player["inventory"]), 0)

    def test_09_homestead_economy_and_room_construction(self):
        """Test real estate listings, purchasing with Col, and facility upgrades."""
        player = {"name": "Kaelen", "col": 100}
        mechanics.ensure_homestead_system(player)

        # Try to purchase manor with insufficient Col
        b_fail = mechanics.purchase_homestead(player, "washington_manor")
        self.assertFalse(b_fail["success"])
        self.assertIn("Insufficient Col", b_fail["message"])

        # Give sufficient Col and purchase
        player["col"] = 15000
        b_success = mechanics.purchase_homestead(player, "washington_manor")
        self.assertTrue(b_success["success"])
        self.assertTrue(player["homestead"]["owned"])
        self.assertEqual(player["col"], 15000 - 3500)

        # Build Deepforged Master-Anvil
        player["col"] = 10000
        r_res = mechanics.upgrade_homestead_facility(player, "master_anvil")
        self.assertTrue(r_res["success"], r_res.get("message"))
        self.assertTrue(player["homestead"]["has_master_anvil"])

    def test_10_factions_bounties_and_threat_intel(self):
        """Test faction standing modifications, bounty directives, and threat intelligence."""
        player = {"name": "Kaelen", "col": 100}
        mechanics.ensure_faction_system(player)

        # Modify Reputation with Iron Syndicate
        rep_res = mechanics.modify_faction_rep(player, "iron_syndicate", 25, reason="Delivered scrap salvage")
        self.assertEqual(player["faction_reputation"]["iron_syndicate"], 25)
        self.assertEqual(rep_res["standing"], "Friendly")

        # Accept a bounty directive
        b_res = mechanics.accept_bounty_directive(player, "bounty_pohatcong_construct")
        self.assertTrue(b_res["success"])
        self.assertEqual(len(player["quests"]), 1)

    def test_11_class_evolution_harmonized_dual_gate(self):
        """Test Harmonized Dual-Gate requirements (Level + Boss + Skill) and Tier 2 Evolution."""
        player = {
            "name": "Kaelen", "class": "Warrior", "level": 10, "bosses_defeated": ["The Gilded Spire Overlord (Sector 1)"],
            "skills": {"One-Handed Axes": {"mastery": 255}},
            "feats": [], "spells": [],
            "combat_resource": {"name": "Poise", "max": 100, "current": 100, "type": "poise"}
        }

        # Check Evolution Eligibility
        evo_status = mechanics.check_evolution_eligibility(player)
        self.assertTrue(evo_status["eligible"], evo_status.get("unmet_conditions"))
        self.assertEqual(evo_status["target_tier"], 2)

        # Generate Curated Evolutions
        options = mechanics.generate_curated_evolutions(player)
        self.assertGreaterEqual(len(options), 3)

        # Apply Evolution: First curated archetype
        choice = options[0]
        res = mechanics.apply_class_evolution(player, choice)
        self.assertEqual(player["class"], choice["title"])
        self.assertEqual(player["combat_resource"]["max"], 125, "+25% resource scaling must be applied!")
        self.assertTrue(any(choice["title"] in f for f in player["feats"]))

    def test_12_decoupled_visible_room_and_subagent_logs(self):
        """Test staging ground generation and log component isolation."""
        player_state = {"name": "Kaelen", "hp": 150, "location": "Sector 1 Iron Mine"}
        world_state = {
            "map_locations": [{
                "name": "Sector 1 Iron Mine",
                "entities": [{"name": "Corrupted Drone", "hp": 40}],
                "secrets": ["Hidden aether vein"]
            }]
        }

        # 1. GM Engine generates visible room without leaking secrets
        v_room = gm_engine.generate_visible_room(player_state, world_state)
        self.assertIn("Corrupted Drone", str(v_room))
        self.assertNotIn("Hidden aether vein", str(v_room), "Secrets must not leak into visible staging ground!")

        # 2. Test turn component extraction (Mock UI turn)
        extract_turn_components = mechanics.extract_turn_components
        mock_msg = {
            "role": "assistant",
            "content": (
                "Kaelen swings his heavy mace with crushing impact!\n\n"
                "🎲 Dice Rolls & Game Mechanics:\n"
                "- Attack Roll: 1d20 (16) + 3 = 19 (HIT!)\n"
                "- Damage: 1d8 (7) + 3 = 10 bludgeoning\n\n"
                "🧠 SubAgent Thoughts & Planned Actions:\n"
                "Ren: I'll flank to the left to draw suppression fire."
            )
        }
        narrative, mechanics_log, subagent_log = extract_turn_components(mock_msg)
        self.assertIn("Kaelen swings his heavy mace", narrative)
        self.assertNotIn("Attack Roll", narrative)
        self.assertIn("Attack Roll", mechanics_log)
        self.assertIn("Ren: I'll flank to the left", subagent_log)


if __name__ == "__main__":
    unittest.main()
