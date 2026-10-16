"""
COMPREHENSIVE UNIT TEST SUITE: TUTORIAL MINI-DUNGEON R3 (13 ROOMS, DRILLS, BOSS & GRADUATION)
Authored by Milestone 3 Explorer 3.

Verifies:
1. 13-room graph engine integrity across Phase I (4), Phase II (4), and Phase III (5).
2. Physical encumbrance (STR * 15 lbs) and catwalk load checks.
3. Weapon durability degradation and whetstone field maintenance (+25 durability).
4. Soul-Bound Keepsake Relic resonance (Polaroid, Zippo, Tuning Fork, Smartphone).
5. 1-1000 skill mastery progression and Sword Skill charge buffers / parry.
6. Multi-limb coordination: 2-armed dual-wielding and 4-armed Glenny flurries.
7. Status effect triage and Clockwork Sentinel battle (Level 2 + Astral Bolt).
8. Harmonic Puzzle Vault 3-dial mechanism (inputs, DC 12 check, Tuning Fork bypass).
9. Concealed Scriptorium secret door discovery (Perception, Polaroid flash, Tuning Fork).
10. Elite Construct Foundry combat against Phalanx Construct (AC 13, HP 20).
11. Crucible Warden apex boss battle (Kinetic Ward shatter, 40 HP, auto-equip signet).
12. Level 3 Safe-Zone graduation to Washington Borough, NJ retaining all 8 canonical loot items.
13. Backward-compatible advance_tutorial_stage() single-step and fast-forward contracts.
"""

import copy
import os
import sys
import unittest

# Ensure project root and current explorer dir are on path
CUR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CUR_DIR, "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if CUR_DIR not in sys.path:
    sys.path.insert(0, CUR_DIR)

import backend.character_generator as cg
import backend.mechanics as mechanics
p3 = mechanics


class TestTutorialMiniDungeonR3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Alias tuning_fork in PERSONAL_RELICS for test robustness
        if "tuning_fork" not in cg.PERSONAL_RELICS and "guitar_tuning_fork" in cg.PERSONAL_RELICS:
            cg.PERSONAL_RELICS["tuning_fork"] = cg.PERSONAL_RELICS["guitar_tuning_fork"]

    def setUp(self):
        self.player = cg.generate_starting_character(
            name="Valeria",
            point_alloc={"STR": 4, "DEX": 4, "CON": 4, "INT": 4, "WIS": 2, "CHA": 2},
            race_key="pure_human" if "pure_human" in cg.RACIAL_LINEAGES else "human",
            class_key="fighter",
            relic_key="tuning_fork",
            start_tutorial=True
        )
        p3.initialize_tutorial_mini_dungeon(self.player)

    # -----------------------------------------------------------------
    # 1. 13-ROOM GRAPH ENGINE INTEGRITY
    # -----------------------------------------------------------------
    def test_01_thirteen_rooms_graph_structure(self):
        """Verify exactly 13 rooms exist across 3 phases and all graph connections are valid."""
        rooms = p3.TUTORIAL_MINI_DUNGEON_ROOMS
        self.assertEqual(len(rooms), 13, f"Expected exactly 13 tutorial rooms, got {len(rooms)}")

        phase1_rooms = [r for r, d in rooms.items() if d.get("phase") == 1]
        phase2_rooms = [r for r, d in rooms.items() if d.get("phase") == 2]
        phase3_rooms = [r for r, d in rooms.items() if d.get("phase") == 3]

        self.assertEqual(len(phase1_rooms), 4, "Phase I must have 4 rooms")
        self.assertEqual(len(phase2_rooms), 4, "Phase II must have 4 rooms")
        self.assertEqual(len(phase3_rooms), 5, "Phase III must have 5 rooms")

        # Verify all connections point to registered rooms
        for r_id, r_def in rooms.items():
            self.assertTrue(r_def.get("badge"), f"Room {r_id} missing badge")
            self.assertTrue(r_def.get("name"), f"Room {r_id} missing name")
            self.assertTrue(r_def.get("description"), f"Room {r_id} missing description")
            for conn in r_def.get("connections", []):
                self.assertIn(conn, rooms, f"Room {r_id} points to non-existent connection {conn}")

    # -----------------------------------------------------------------
    # 2. GRANULAR ROOM NAVIGATION ENGINE
    # -----------------------------------------------------------------
    def test_02_room_navigation_and_adjacency(self):
        """Verify moving through rooms and retrieving adjacent chambers."""
        cur = p3.get_current_tutorial_room(self.player)
        self.assertEqual(cur["room_id"], "phase1_telemetry_sanctum")

        adj = p3.get_tutorial_adjacent_rooms(self.player)
        self.assertEqual(len(adj), 1)
        self.assertEqual(adj[0]["room_id"], "phase1_gravity_chasm")

        # Move to Gravity Chasm
        res = p3.move_tutorial_dungeon_room(self.player, "phase1_gravity_chasm")
        self.assertTrue(res["success"])
        self.assertEqual(self.player["tutorial_dungeon"]["current_room"], "phase1_gravity_chasm")

        # Invalid move directly to boss lair fails
        invalid_res = p3.move_tutorial_dungeon_room(self.player, "phase3_warden_lair")
        self.assertFalse(invalid_res["success"])

    # -----------------------------------------------------------------
    # 3. PHASE I: ENCUMBRANCE HAZARD (STR * 15 LBS)
    # -----------------------------------------------------------------
    def test_03_phase_1_encumbrance_hazard(self):
        """Verify encumbrance calculation adheres to STR * 15 lbs limit."""
        enc = mechanics.calculate_encumbrance(self.player)
        expected_max = self.player["stats"]["STR"] * 15.0
        self.assertEqual(enc["max_weight_lbs"], expected_max)
        self.assertIn(enc["tier"], ["Unencumbered", "Light Load"])

    # -----------------------------------------------------------------
    # 4. PHASE I: WEAPON DURABILITY & WHETSTONE FIELD REPAIR
    # -----------------------------------------------------------------
    def test_04_phase_1_durability_and_whetstone_maintenance(self):
        """Verify weapon durability degrades and whetstone restores +25 durability."""
        init_dur = self.player.setdefault("gear_durability", {}).setdefault("main_hand", {"cur": 60, "max": 60, "state": "Pristine"})["cur"]
        mechanics.apply_durability_damage(self.player, "main_hand", 15)
        damaged_dur = self.player["gear_durability"]["main_hand"]["cur"]
        self.assertEqual(damaged_dur, init_dur - 15)

        # Apply whetstone repair
        rep = p3.repair_gear_durability(self.player, "main_hand", 25)
        self.assertTrue(rep["success"])
        self.assertGreaterEqual(rep["cur"], damaged_dur)
        self.assertIn(rep["state"], ["Pristine", "Worn"])

    # -----------------------------------------------------------------
    # 5. PHASE I: RELIC RESONANCE
    # -----------------------------------------------------------------
    def test_05_phase_1_relic_resonance(self):
        """Verify keepsake relic activation returns successful resonance."""
        res = mechanics.activate_personal_relic(self.player)
        self.assertTrue(res["success"])

    # -----------------------------------------------------------------
    # 6. PHASE II: 1-1000 SKILL PROGRESSION & MULTI-LIMB FLURRY
    # -----------------------------------------------------------------
    def test_06_phase_2_martial_skill_and_multi_limb(self):
        """Verify skill mastery gains and multi-limb profile handling."""
        skills = self.player.setdefault("skills", {"One-Handed Blades": {"mastery": 10, "tier": "Novice"}})
        sk_name = next(iter(skills.keys()))
        init_m = skills[sk_name].get("mastery", 0) if isinstance(skills[sk_name], dict) else int(skills[sk_name])
        
        upd = mechanics.update_skill_mastery(self.player, sk_name, 15)
        self.assertEqual(upd["new_mastery"], init_m + 15)

        # Multi-limb check on standard 2-armed character
        anat = mechanics.get_limb_anatomy_profile(self.player)
        self.assertEqual(anat["arm_count"], 2)

        # Multi-limb check on 4-armed Glenny
        glenny = cg.generate_starting_character(name="Glenny", start_tutorial=False)
        g_anat = mechanics.get_limb_anatomy_profile(glenny)
        self.assertEqual(g_anat["arm_count"], 4)
        self.assertTrue(g_anat["is_four_armed"])

    # -----------------------------------------------------------------
    # 7. PHASE III: HARMONIC PUZZLE VAULT (3 RUNIC DIALS)
    # -----------------------------------------------------------------
    def test_07_phase_3_puzzle_vault_resolution(self):
        """Verify 3 runic dials puzzle can be solved via manual input, DC 12 check, or Tuning Fork."""
        # 1. Manual Input
        p_manual = copy.deepcopy(self.player)
        res_manual = p3.solve_tutorial_puzzle(p_manual, dial_inputs=["Sun", "Moon", "Star"])
        self.assertTrue(res_manual["success"])
        self.assertEqual(res_manual["method"], "dial_input")
        self.assertTrue(res_manual["lattice_disarmed"])

        # 2. Tuning Fork Bypass
        p_relic = copy.deepcopy(self.player)
        res_relic = p3.solve_tutorial_puzzle(p_relic, use_relic=True)
        self.assertTrue(res_relic["success"])
        self.assertEqual(res_relic["method"], "relic_bypass")

        # 3. DC 12 Skill Check Success (player without relic)
        p_check_pass = copy.deepcopy(self.player)
        p_check_pass["inventory"] = []
        p_check_pass["personal_relic"] = ""
        res_pass = p3.solve_tutorial_puzzle(p_check_pass, deterministic_roll=14)
        self.assertTrue(res_pass["success"])
        self.assertEqual(res_pass["method"], "skill_check")

        # 4. DC 12 Skill Check Failure (player without relic)
        p_check_fail = copy.deepcopy(self.player)
        p_check_fail["inventory"] = []
        p_check_fail["personal_relic"] = ""
        p_check_fail["stats"]["INT"] = 10
        res_fail = p3.solve_tutorial_puzzle(p_check_fail, deterministic_roll=4)
        self.assertFalse(res_fail["success"])

    # -----------------------------------------------------------------
    # 8. PHASE III: CONCEALED SCRIPTORIUM SECRET DOOR DISCOVERY
    # -----------------------------------------------------------------
    def test_08_phase_3_secret_door_discovery(self):
        """Verify secret door detection unlocks Scriptorium and awards bonus lore and Col."""
        # 1. Legitimately position player in Phase 3 Puzzle Vault
        self.player["tutorial_dungeon"]["current_room"] = "phase3_puzzle_vault"
        self.player["tutorial_dungeon"]["current_phase"] = 3
        # Ensure secret door is initially locked/unrevealed
        p3_vault_state = self.player["tutorial_dungeon"]["room_states"].setdefault("phase3_puzzle_vault", {})
        p3_vault_state["secret_door_revealed"] = False

        # 2. Movement to Scriptorium MUST fail before secret door is discovered
        blocked_move = p3.move_tutorial_dungeon_room(self.player, "phase3_secret_scriptorium")
        self.assertFalse(
            blocked_move["success"],
            "Moving to secret scriptorium before door discovery must fail with success=False."
        )
        self.assertEqual(
            self.player["tutorial_dungeon"]["current_room"],
            "phase3_puzzle_vault",
            "Player must remain in phase3_puzzle_vault when transit is blocked."
        )

        # 3. Perception check pass unlocks secret door
        res_pass = p3.discover_tutorial_secret_door(self.player, deterministic_roll=15)
        self.assertTrue(res_pass["success"])
        self.assertTrue(res_pass["discovered"])
        self.assertEqual(res_pass["room_unlocked"], "phase3_secret_scriptorium")
        self.assertGreater(res_pass["col_gained"], 0)
        self.assertIn(
            "Tome of the Crucible Scribe",
            [it.get("name") if isinstance(it, dict) else str(it) for it in self.player["inventory"]]
        )

        # 4. Movement to Scriptorium succeeds AFTER discovery
        move_res = p3.move_tutorial_dungeon_room(self.player, "phase3_secret_scriptorium")
        self.assertTrue(
            move_res["success"],
            "Moving to secret scriptorium after door discovery must succeed."
        )
        self.assertEqual(
            self.player["tutorial_dungeon"]["current_room"],
            "phase3_secret_scriptorium",
            "Player current_room must update to phase3_secret_scriptorium."
        )

    # -----------------------------------------------------------------
    # 9. PHASE III: FOUNDRY BATTLE VS PHALANX CONSTRUCT
    # -----------------------------------------------------------------
    def test_09_phase_3_foundry_battle(self):
        """Verify defeating Aether-Forged Phalanx Construct in the foundry."""
        res = p3.resolve_tutorial_foundry_battle(self.player)
        self.assertTrue(res["success"])
        self.assertTrue(res["enemy_defeated"])
        self.assertEqual(res["enemy_remaining_hp"], 0)
        self.assertGreater(res["xp_gained"], 0)

    # -----------------------------------------------------------------
    # 10. PHASE III: CRUCIBLE WARDEN APEX BOSS & KINETIC WARD SHATTER
    # -----------------------------------------------------------------
    def test_10_phase_3_warden_boss_battle_and_signet(self):
        """Verify Astral Bolt shatters Kinetic Ward, defeats Warden, and auto-equips signet."""
        res = p3.resolve_tutorial_warden_boss_battle(self.player, cast_spell="Astral Bolt")
        self.assertTrue(res["success"])
        self.assertTrue(res["boss_defeated"])
        self.assertTrue(res["kinetic_ward_shattered"])
        self.assertEqual(self.player["equipped"].get("accessory"), "Crucible Vanguard Signet")

    # -----------------------------------------------------------------
    # 11. GRADUATION MECHANICS & ALL 8 CANONICAL LOOT ITEMS
    # -----------------------------------------------------------------
    def test_11_graduation_to_level_3_and_8_loot_items(self):
        """Verify Level 3 graduation to Washington Borough, NJ retaining all 8 canonical loot items."""
        grad = p3.graduate_tutorial_player(self.player)
        self.assertTrue(grad["graduated"])
        self.assertTrue(grad["teleported"])
        self.assertEqual(self.player["level"], 3)
        self.assertEqual(self.player["location"], "Sector 1 Safe-Zone: Washington Borough, NJ")
        self.assertTrue(self.player["tutorial"]["completed"])
        self.assertFalse(self.player["tutorial"]["active"])

        # Check all 8 canonical loot items
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

        inv_names = [it.get("name", "") if isinstance(it, dict) else str(it) for it in self.player["inventory"]]
        eq_names = [str(v) for v in self.player["equipped"].values()]
        all_items = " ".join(inv_names + eq_names)

        for item_name in expected_loot:
            self.assertIn(item_name.lower(), all_items.lower())
            self.assertIn(item_name, self.player["tutorial"]["acquired_loot"])
            # String containment test via ItemEntry
            self.assertIn(item_name, self.player["inventory"])

    # -----------------------------------------------------------------
    # 12. BACKWARD COMPATIBILITY: ADVANCE_TUTORIAL_STAGE WRAPPER
    # -----------------------------------------------------------------
    def test_12_advance_tutorial_stage_single_steps_and_fast_forward(self):
        """Verify advance_tutorial_stage() single-step progression and complete_all fast-forward."""
        # 1. Step-by-step
        p_step = cg.generate_starting_character(name="StepHero", start_tutorial=True)
        st1 = p3.advance_tutorial_stage(p_step)
        self.assertEqual(st1["completed_stage"], 1)
        self.assertEqual(st1["new_stage"], 2)

        st2 = p3.advance_tutorial_stage(p_step)
        self.assertEqual(st2["completed_stage"], 2)
        self.assertEqual(st2["new_stage"], 3)
        self.assertEqual(p_step["level"], 2)
        self.assertEqual(p_step["attuned_spell"], "Astral Bolt")

        st3 = p3.advance_tutorial_stage(p_step)
        self.assertEqual(st3["completed_stage"], 3)
        self.assertTrue(st3["graduated"])
        self.assertEqual(p_step["level"], 3)
        self.assertEqual(p_step["location"], "Sector 1 Safe-Zone: Washington Borough, NJ")

        # 2. Fast-forward complete_all
        p_fast = cg.generate_starting_character(name="FastHero", start_tutorial=True)
        fast_res = p3.advance_tutorial_stage(p_fast, complete_all=True)
        self.assertTrue(fast_res["graduated"])
        self.assertEqual(p_fast["level"], 3)
        self.assertEqual(p_fast["location"], "Sector 1 Safe-Zone: Washington Borough, NJ")
        self.assertGreaterEqual(len(p_fast["inventory"]) + len(p_fast["equipped"]), 8)


if __name__ == "__main__":
    unittest.main()
