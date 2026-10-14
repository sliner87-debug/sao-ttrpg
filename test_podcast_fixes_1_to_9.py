"""
Comprehensive Automated Verification Suite for Podcast Audit Fixes 1–9:
- Fix 1: Dual-Register Approach (Vivid Narrative + Clinical Tactical State Footer + Two-Stage Scene-Gate + Recency-Biased Tail Mandate + UI Button Decoupling)
- Fix 2: Lore-Canonical Python ("Serpent-Script" / Ouroboros Kernel v3.14) Ocular Telemetry
- Fix 3: Titus Sterling's 1,200-lb Weight & Environmental Floor Integrity Checks
- Fix 4: Persistent Enemy Mutable Debuffs (-4 AC Foundry Hydraulic Overdrive & 0 DR Corrosive Slag-Shatter) + Real Dice Combo Rolls
- Fix 5: Non-Euclidean "Data-Trench" Highway Chasm Traversal Encounters
- Fix 6: Active Mechanical Triggers for Pre-Integration Personal Relics (Earth Smartphone, 3-Charge Polaroid, Brass Zippo, 440Hz Tuning Fork)
- Fix 7: Anti-Spoiler Puzzle Gating for Pohatcong Harmonic Frequency Vault (3-1-4 gated behind Ancient Glyph Deciphering / 440Hz Fork + 3d8 Sonic Shockwave Backlash)
- Fix 8: Ability Fusion Parameter Guardrails, Unified Dual-Metric Grafting Strain, Fire+Cold Elemental Mutual Exclusivity, Golem ASF, 24h Post-Op [Cellular Re-Knitting], 250 Col / Blood-Debt, and Red Cursor NPC Hostility
- Fix 9: Ren Sasaki's 5-Stage Sentient Diagnostic Subroutine Mystery Track (ren_diag_v2.py)
"""

import json
import os
import py_compile
import unittest

import backend.mechanics as mechanics
import backend.gm_engine as gm_engine
import backend.persona_engine as persona_engine
import backend.schemas as schemas


class TestPodcastFixes1To9(unittest.TestCase):

    def setUp(self):
        self.player = {
            "name": "Banki",
            "level": 3,
            "hp": 100,
            "max_hp": 100,
            "col": 300,
            "location": "Oxford Magnetite Mine - Shaft 4",
            "stats": {"STR": 16, "DEX": 12, "CON": 14, "INT": 12, "WIS": 10, "CHA": 10},
            "skills": {
                "One-Handed Axes": {"mastery": 120, "tier": "Journeyman", "description": "Heavy cleaving strikes."},
                "Pyromancy": {"mastery": 110, "tier": "Journeyman", "description": "Aetheric flame channeling."},
            },
            "inventory": [
                {"name": "Cracked Earth Smartphone", "type": "relic"},
                {"name": "Vintage Polaroid Camera", "type": "relic", "charges": 3},
                {"name": "Engraved Brass Zippo Lighter", "type": "relic"},
                {"name": "Harmonic Steel Tuning Fork (440 Hz)", "type": "relic"},
            ],
            "grafts": {},
            "graft_system": {"installed_grafts": []},
            "party": {
                "active_companion": "Titus",
                "companions": {
                    "Ren": {"name": "Ren", "affinity": 65, "recruited": True, "hp": 85, "max_hp": 85},
                    "Titus": {"name": "Titus", "affinity": 60, "recruited": True, "hp": 145, "max_hp": 145, "weight_lbs": 1200.0},
                    "Thorne": {"name": "Thorne", "affinity": 60, "recruited": True, "hp": 80, "max_hp": 80},
                    "Daphne": {"name": "Daphne", "affinity": 60, "recruited": True, "hp": 75, "max_hp": 75},
                },
            },
        }

    def test_00_syntax_compilation(self):
        """Ensure all modified Python files compile with zero syntax errors."""
        for rel_path in [
            "app.py",
            "backend/schemas.py",
            "backend/mechanics.py",
            "backend/gm_engine.py",
            "backend/persona_engine.py",
        ]:
            py_compile.compile(rel_path, doraise=True)

    def test_01_dual_register_scene_gate_and_tactical_footer(self):
        """Verify Fix 1: Two-Stage Scene-Gate State Machine & Clinical Tactical State Footer."""
        master_state = {
            "environment": {
                "location": "Oxford Deep Mine Cart Track",
                "safe_zone": False,
                "Pending_Destination": None,
            },
            "entities": {},
        }
        # Attempting to leap directly from Deep Mine to Doc Mercer's Clinic in Washington Safe-Zone should be intercepted by Stage 1
        gate_res = gm_engine.evaluate_two_stage_scene_gate(
            master_state=master_state,
            proposed_location="Doc Mercer's Underground Clinic (Washington Borough Safe-Zone)",
            player_action="We leap into the mine cart and ride the rails!",
        )
        self.assertTrue(gate_res["gated"])
        self.assertIn("Portal Threshold", gate_res["approved_location"])
        self.assertEqual(
            master_state["environment"]["Pending_Destination"],
            "Doc Mercer's Underground Clinic (Washington Borough Safe-Zone)",
        )

        # Stage 2: Subsequent travel action clears the gate to the Pending_Destination
        gate_res_2 = gm_engine.evaluate_two_stage_scene_gate(
            master_state=master_state,
            proposed_location="Doc Mercer's Underground Clinic (Washington Borough Safe-Zone)",
            player_action="We haul the scrap up the incline and head into town to Doc Mercer's clinic.",
        )
        self.assertFalse(gate_res_2["gated"])
        self.assertEqual(
            gate_res_2["approved_location"],
            "Doc Mercer's Underground Clinic (Washington Borough Safe-Zone)",
        )

        # Verify clinical tactical state footer builder
        footer = gm_engine.build_tactical_state_footer(master_state, self.player)
        self.assertIn("[CARDINAL TACTICAL TELEMETRY", footer)
        self.assertIn("Awaiting Player Action", footer)

    def test_02_serpent_script_and_ren_subroutine_mystery_track(self):
        """Verify Fix 2 & Fix 9: Serpent-Script (Ouroboros Kernel v3.14) and Ren's 5-Stage Diagnostic Subroutine Track."""
        directive_s0 = mechanics.get_ren_subroutine_directive(self.player)
        self.assertIn("Serpent-Script", directive_s0)
        self.assertIn("Ouroboros Kernel v3.14", directive_s0)
        self.assertIn("visible_room", directive_s0)

        # Advance through stages
        adv1 = mechanics.advance_ren_subroutine_mystery(self.player, trigger_reason="tactical_scan")
        self.assertEqual(adv1["stage"], 1)
        self.assertEqual(adv1["stage_title"], "Ocular Serpent-Script Syntax Leaks")

        # Jump via high affinity + kernel terminal discovery
        self.player["party"]["companions"]["Ren"]["affinity"] = 90
        for _ in range(4):
            adv = mechanics.advance_ren_subroutine_mystery(self.player, trigger_reason="kernel_terminal")
        self.assertEqual(adv["stage"], 5)
        self.assertIn("ren_diag_v2.py", adv["subroutine_id"])
        self.assertIn("Sentient Awakening", adv["stage_title"])

        # Verify JSON sheets contain Serpent-Script & ren_diag_v2.py
        with open("Party/companion_ren.json", "r", encoding="utf-8") as f:
            ren_sheet = json.load(f)
        self.assertEqual(ren_sheet["subroutine_metadata"]["subroutine_id"], "ren_diag_v2.py")
        self.assertIn("Ouroboros Kernel v3.14", ren_sheet["subroutine_metadata"]["kernel_language"])

    def test_03_titus_1200_lb_floor_physics(self):
        """Verify Fix 3: Titus Sterling's 1,200-lb chassis triggers environmental floor-collapse and stealth penalties."""
        self.assertEqual(mechanics.COMPANION_ROSTER["Titus"]["weight_lbs"], 1200.0)
        phys_res = mechanics.evaluate_party_environmental_physics(
            self.player,
            room_description="An old colonial farmhouse cellar with rotted timber floorboards and a creaking wooden bridge.",
        )
        self.assertTrue(phys_res["titus_present"])
        self.assertGreaterEqual(phys_res["total_party_weight_lbs"], 1200.0)
        self.assertTrue(phys_res["floor_hazard_triggered"])
        self.assertEqual(phys_res["stealth_modifier"], -6)
        self.assertTrue(any("1,200-lb" in w for w in phys_res["warnings"]))

    def test_04_dual_tech_real_dice_and_persistent_enemy_debuffs(self):
        """Verify Fix 4: Persistent active_debuffs on enemies (-4 AC Foundry Overdrive, 0 DR Corrosive Slag-Shatter) & real dice."""
        golem = {
            "entity_id": "golem_01",
            "name": "Rusted Siege Golem",
            "hp": 120,
            "max_hp": 120,
            "ac": 18,
            "dr": 6,
            "active_debuffs": [],
        }
        # 1. Execute Foundry Hydraulic Overdrive (Titus) -> -4 AC
        combo_titus = mechanics.execute_dual_tech(self.player, "Titus", target_entity=golem)
        self.assertTrue(combo_titus["success"])
        self.assertEqual(combo_titus["dual_tech_name"], "Foundry Hydraulic Overdrive")
        self.assertGreater(combo_titus["total_damage"], 0)
        self.assertEqual(golem["ac"], 14)  # 18 - 4 = 14
        self.assertEqual(golem["base_ac"], 18)

        # 2. Execute Corrosive Slag-Shatter (Thorne) -> 0 DR (dissolves armor plating)
        combo_thorne = mechanics.execute_dual_tech(self.player, "Thorne", target_entity=golem)
        self.assertTrue(combo_thorne["success"])
        self.assertEqual(combo_thorne["dual_tech_name"], "Corrosive Slag-Shatter")
        self.assertEqual(golem["dr"], 0)  # Dissolved to 0!
        self.assertGreaterEqual(len(golem["active_debuffs"]), 2)

    def test_05_non_euclidean_data_trench_traversal(self):
        """Verify Fix 5: Non-Euclidean Data-Trench highway chasm traversal mechanics."""
        trench_res = mechanics.traverse_data_trench(
            self.player,
            corridor_key="route_57_trench",
            approach="gravity_hop",
        )
        self.assertTrue(trench_res["success"])
        self.assertEqual(trench_res["corridor_name"], "Route 57 Mag-Lev Siphon & Data-Trench")
        self.assertIn("roll", trench_res)
        self.assertIn("total", trench_res)

    def test_06_personal_relics_active_triggers(self):
        """Verify Fix 6: Active mechanical hooks for Smartphone, 3-Charge Polaroid, Zippo, and 440Hz Tuning Fork."""
        # 1. Cracked Earth Smartphone during Short Rest
        phone_res = mechanics.activate_personal_relic(self.player, "Cracked Earth Smartphone", context="short_rest")
        self.assertTrue(phone_res["success"])
        self.assertIn("Dinner is cold", phone_res["message"])
        self.assertGreater(phone_res["hp_restored"], 0)

        # 2. Vintage Polaroid Camera (3 charges -> 2 charges)
        cam_res = mechanics.activate_personal_relic(self.player, "Vintage Polaroid Camera", context="inspect")
        self.assertTrue(cam_res["success"])
        self.assertEqual(cam_res["charges_remaining"], 2)

        # 3. Engraved Brass Zippo Lighter (Gas detection)
        zippo_res = mechanics.activate_personal_relic(
            self.player,
            "Engraved Brass Zippo Lighter",
            context="inspect",
            room_hazards=["Firedamp Methane Gas Pocket"],
        )
        self.assertTrue(zippo_res["success"])
        self.assertTrue(zippo_res["gas_detected"])

        # 4. Harmonic Steel Tuning Fork (440 Hz)
        fork_res = mechanics.activate_personal_relic(self.player, "Harmonic Steel Tuning Fork", context="puzzle")
        self.assertTrue(fork_res["success"])
        self.assertTrue(fork_res["auto_bypass_glyph_check"])
        self.assertTrue(self.player.get("harmonic_vault_deciphered"))

    def test_07_anti_spoiler_harmonic_vault_puzzle_and_sonic_backlash(self):
        """Verify Fix 7: Pohatcong Harmonic Vault description has no spoiler, gates 3-1-4 behind check/fork, and deals 3d8 backlash on wrong sequence."""
        puzzle_desc = mechanics.POHATCONG_LABYRINTH["rooms"]["puzzle_chamber"]["description"]
        self.assertNotIn("3 - 1 - 4", puzzle_desc)
        self.assertNotIn("3-1-4", puzzle_desc)

        # Fresh player without deciphering or tuning fork cannot brute-force 3-1-4 without a check, and wrong sequence deals 3d8 Thunder backlash
        fresh_player = {
            "name": "Tester",
            "level": 2,
            "hp": 60,
            "max_hp": 60,
            "stats": {"INT": 10},
            "skills": {},
            "inventory": [],
        }
        wrong_res = mechanics.solve_dungeon_puzzle(fresh_player, "puzzle_chamber", [1, 2, 3])
        self.assertFalse(wrong_res["solved"])
        self.assertGreater(wrong_res.get("damage_taken", 0), 0)
        self.assertLess(fresh_player["hp"], 60)

        # With Tuning Fork in inventory, [3, 1, 4] succeeds cleanly
        fresh_player["inventory"].append({"name": "Harmonic Steel Tuning Fork (440 Hz)"})
        right_res = mechanics.solve_dungeon_puzzle(fresh_player, "puzzle_chamber", [3, 1, 4])
        self.assertTrue(right_res["solved"])

    def test_08a_ability_fusion_guardrails(self):
        """Verify Fix 8A: Ability Fusion clamps overpowered custom dice (e.g., 50d100 -> 3d8 at Lv.3) and strips instant-kill exploits."""
        fuse_res = mechanics.fuse_abilities(
            self.player,
            "One-Handed Axes",
            "Pyromancy",
            custom_fused_name="Apocalypse Nuke Cleave",
            custom_desc="Deals 50d100 fire damage, costs 0 stamina, no cooldown, and causes instant death to all targets.",
        )
        self.assertTrue(fuse_res["success"])
        self.assertTrue(fuse_res["guardrail_clamped"])
        self.assertNotIn("50d100", fuse_res["description"])
        self.assertIn("3d8", fuse_res["description"])
        self.assertNotIn("instant death", fuse_res["description"].lower())

    def test_08bc_unified_grafting_strain_elemental_dissonance_and_post_op(self):
        """Verify Fix 8B/8C & #4: Unified Dual-Metric Strain, 250 Col / Blood-Debt, 24h Post-Op Sickness, Golem ASF, and Fire+Cold Elemental Mutual Exclusivity."""
        # Install Tier-1 Golem Graft (piston_knuckle_augment) -> costs 250 Col, sets 24h Post-Op Sickness, 15% ASF
        inst1 = mechanics.install_graft(self.player, "piston_knuckle_augment",at_clinic=True)
        self.assertTrue(inst1["success"])
        self.assertEqual(inst1["surgery_cost_paid"], 250)
        self.assertEqual(self.player["col"], 50)  # 300 - 250 = 50 Col
        self.assertTrue(inst1["post_op_sickness"]["active"])
        self.assertEqual(self.player["max_hp"], 80)  # -20% Max HP during 24h [Cellular Re-Knitting]
        self.assertEqual(inst1["asf_percent"], 15)

        # Both Model A (player["grafts"]) and Model B (player["graft_system"]["installed_grafts"]) are synced
        self.assertIn("right_arm", self.player["grafts"])
        self.assertEqual(len(self.player["graft_system"]["installed_grafts"]), 1)

        # Active graft ability during Post-Op Sickness triggers DC 13 CON save check
        act_res = mechanics.trigger_graft_active_ability(self.player, "Piston-Strike")
        self.assertTrue(act_res["post_op_check_required"])

        # Advance 24h Safe-Zone recovery -> cures [Cellular Re-Knitting] and restores Max HP to 100
        rec_res = mechanics.advance_post_op_recovery(self.player, hours=24, in_safe_zone=True)
        self.assertTrue(rec_res["cured"])
        self.assertEqual(self.player["max_hp"], 100)

        # Install Fire graft (ignis_core_heart) using Promissory Blood-Debt since player only has 50 Col (< 1200 Col)
        self.player["stats"]["CON"] = 18  # Raise CON so unit cap allows multiple grafts
        inst_fire = mechanics.install_graft(self.player, "ignis_core_heart", at_clinic=True, allow_blood_debt=True)
        self.assertTrue(inst_fire["success"])
        self.assertTrue(inst_fire["used_blood_debt"])
        self.assertGreater(self.player["graft_system"]["blood_debt_col"], 0)

        # Attempting to install Cold graft (cryo_vein_conduit) while Fire graft is installed triggers Elemental Mutual Exclusivity Rejection!
        inst_cold = mechanics.install_graft(self.player, "cryo_vein_conduit", at_clinic=True, allow_blood_debt=True)
        self.assertFalse(inst_cold["success"])
        self.assertTrue(inst_cold.get("elemental_rejection"))
        self.assertIn("ELEMENTAL MUTUAL EXCLUSIVITY", inst_cold["error"])

    def test_08d_red_cursor_npc_hostility(self):
        """Verify Fix 8D: Quartermaster Vane and Safe-Zone Sentries attack Red-Cursor players on sight and redirect them to the Blood-Shroud."""
        self.player["pvp_state"] = {"cursor_color": "Red", "infamy_points": 15}
        vane_react = mechanics.evaluate_npc_cursor_reaction(
            self.player,
            npc_name="Quartermaster Vane",
            npc_faction="Warren County Barony",
        )
        self.assertTrue(vane_react["hostile_on_sight"])
        self.assertTrue(vane_react["trade_refused"])
        self.assertIn("Blood-Shroud", vane_react["directive"])


if __name__ == "__main__":
    unittest.main()
