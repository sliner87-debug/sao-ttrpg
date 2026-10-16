"""
=============================================================================
MILESTONE 3 ADVERSARIAL CHALLENGE TEST SUITE (PROPERTY-BASED & FUZZING HARNESS)
=============================================================================
Authored by Milestone 3 Challenger 1.

Empirical verification suite challenging:
1. Room graph topology: fuzz room traversal across all 13 rooms, verifying
   bidirectional connections and that move_tutorial_dungeon_room strictly
   rejects illegal non-adjacent jumps (including secret scriptorium leak/teleport bugs).
2. Harmonic Puzzle Vault permutations: test all valid dial permutations,
   invalid dial inputs/casing/types, Arcana check thresholds (DC 12), and
   440 Hz Tuning Fork bypass.
3. Concealed Scriptorium secret door discovery: test Perception thresholds (DC 13),
   Polaroid Camera flash true-exposure bypass, Tuning Fork resonance bypass,
   and non-applicable relic handling.
"""

import copy
import itertools
import os
import random
import string
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import backend.character_generator as cg
import backend.mechanics as p3


class TestRoomGraphTopologyAndFuzzing(unittest.TestCase):
    """Adversarial stress-testing of room graph topology, adjacency, and movement constraints."""

    def setUp(self):
        self.player = cg.generate_starting_character(
            name="ChallengerHero",
            point_alloc={"STR": 4, "DEX": 4, "CON": 4, "INT": 4, "WIS": 2, "CHA": 2},
            race_key="pure_human" if "pure_human" in cg.RACIAL_LINEAGES else "human",
            class_key="fighter",
            relic_key="tuning_fork",
            start_tutorial=True
        )
        p3.initialize_tutorial_mini_dungeon(self.player)

    def test_01_all_13_rooms_defined_and_valid_attributes(self):
        """Verify exactly 13 rooms exist with full required schema across all 3 phases."""
        rooms = p3.TUTORIAL_MINI_DUNGEON_ROOMS
        self.assertEqual(len(rooms), 13, f"Expected 13 rooms, got {len(rooms)}")

        phase_counts = {1: 0, 2: 0, 3: 0}
        required_fields = ["room_id", "phase", "phase_name", "name", "badge", "location", "description", "connections"]

        for r_id, r_data in rooms.items():
            for f in required_fields:
                self.assertIn(f, r_data, f"Room {r_id} missing required field '{f}'")
            phase = r_data["phase"]
            self.assertIn(phase, phase_counts, f"Room {r_id} has invalid phase {phase}")
            phase_counts[phase] += 1

        self.assertEqual(phase_counts[1], 4, f"Phase I must have 4 rooms, got {phase_counts[1]}")
        self.assertEqual(phase_counts[2], 4, f"Phase II must have 4 rooms, got {phase_counts[2]}")
        self.assertEqual(phase_counts[3], 5, f"Phase III must have 5 rooms, got {phase_counts[3]}")

    def test_02_all_connections_bidirectional_property(self):
        """Property: Every connection u -> v in TUTORIAL_MINI_DUNGEON_ROOMS must be bidirectional (v -> u)."""
        rooms = p3.TUTORIAL_MINI_DUNGEON_ROOMS
        asymmetric_links = []

        for u, u_data in rooms.items():
            for v in u_data.get("connections", []):
                self.assertIn(v, rooms, f"Room '{u}' points to unregistered connection '{v}'")
                v_conns = rooms[v].get("connections", [])
                if u not in v_conns:
                    asymmetric_links.append((u, v))

        self.assertEqual(asymmetric_links, [], f"Detected asymmetric room connections: {asymmetric_links}")

    def test_03_adjacent_navigation_state_updates(self):
        """Verify moving to adjacent room properly mutates current_room, current_phase, and visited_rooms."""
        res = p3.move_tutorial_dungeon_room(self.player, "phase1_gravity_chasm")
        self.assertTrue(res["success"])
        tut = self.player["tutorial_dungeon"]
        self.assertEqual(tut["current_room"], "phase1_gravity_chasm")
        self.assertEqual(tut["current_phase"], 1)
        self.assertIn("phase1_gravity_chasm", tut["visited_rooms"])
        self.assertIn("phase1_telemetry_sanctum", tut["visited_rooms"])
        self.assertIn("Gravity Chasm", self.player.get("location", ""))

    def test_04_fuzz_illegal_non_adjacent_jumps_rejected(self):
        """
        Fuzz all 156 pairs of rooms (u, v) where v is not in connections(u).
        move_tutorial_dungeon_room MUST reject non-adjacent movement.
        """
        rooms = list(p3.TUTORIAL_MINI_DUNGEON_ROOMS.keys())
        illegal_successes = []

        for start_room in rooms:
            for target_room in rooms:
                if start_room == target_room:
                    continue
                p = copy.deepcopy(self.player)
                p["tutorial_dungeon"]["current_room"] = start_room
                conns = p3.TUTORIAL_MINI_DUNGEON_ROOMS[start_room].get("connections", [])
                if target_room not in conns:
                    res = p3.move_tutorial_dungeon_room(p, target_room)
                    if res.get("success"):
                        illegal_successes.append((start_room, target_room, res.get("message")))

        self.assertEqual(
            illegal_successes, [],
            f"CRITICAL TOPOLOGY BUG: move_tutorial_dungeon_room allowed illegal non-adjacent jumps: {illegal_successes}"
        )

    def test_05_secret_scriptorium_undiscovered_access_rejected(self):
        """
        Adversarial test: Player in phase3_puzzle_vault MUST NOT be able to enter
        phase3_secret_scriptorium before discovering the secret door (secret_door_revealed is False).
        """
        p = copy.deepcopy(self.player)
        p["tutorial_dungeon"]["current_room"] = "phase3_puzzle_vault"
        p_state = p["tutorial_dungeon"]["room_states"].setdefault("phase3_puzzle_vault", {})
        p_state["secret_door_revealed"] = False

        res = p3.move_tutorial_dungeon_room(p, "phase3_secret_scriptorium")
        self.assertFalse(
            res.get("success"),
            "CRITICAL SECURITY BUG: Player walked into Concealed Scriptorium without discovering secret door!"
        )

    def test_06_secret_scriptorium_non_adjacent_jump_after_reveal_rejected(self):
        """
        Adversarial test: Once secret door is revealed, non-adjacent rooms (e.g. phase1_telemetry_sanctum)
        MUST NOT be able to jump/teleport directly into phase3_secret_scriptorium.
        """
        non_adjacent_rooms = [
            r for r in p3.TUTORIAL_MINI_DUNGEON_ROOMS
            if "phase3_secret_scriptorium" not in p3.TUTORIAL_MINI_DUNGEON_ROOMS[r].get("connections", [])
        ]

        teleport_leaks = []
        for r_id in non_adjacent_rooms:
            p = copy.deepcopy(self.player)
            p["tutorial_dungeon"]["current_room"] = r_id
            p["tutorial_dungeon"]["room_states"].setdefault("phase3_puzzle_vault", {})["secret_door_revealed"] = True
            res = p3.move_tutorial_dungeon_room(p, "phase3_secret_scriptorium")
            if res.get("success"):
                teleport_leaks.append((r_id, res.get("message")))

        self.assertEqual(
            teleport_leaks, [],
            f"CRITICAL EXPLOIT: Non-adjacent rooms allowed teleportation into Scriptorium when door revealed: {teleport_leaks}"
        )

    def test_07_phase1_to_phase2_transit_barrier(self):
        """Moving from phase1_relic_sanctum to phase2_proving_ground requires relic resonance."""
        p = copy.deepcopy(self.player)
        p["tutorial_dungeon"]["current_room"] = "phase1_relic_sanctum"
        p["tutorial_dungeon"]["transit_phase2_unlocked"] = False

        blocked = p3.move_tutorial_dungeon_room(p, "phase2_proving_ground")
        self.assertFalse(blocked["success"])
        self.assertIn("Keepsake", blocked["message"])

        # After resonance
        p["tutorial_dungeon"]["transit_phase2_unlocked"] = True
        allowed = p3.move_tutorial_dungeon_room(p, "phase2_proving_ground")
        self.assertTrue(allowed["success"])

    def test_08_phase3_lattice_barrier(self):
        """Moving from phase3_puzzle_vault to phase3_foundry_hall requires lattice disarmed."""
        p = copy.deepcopy(self.player)
        p["tutorial_dungeon"]["current_room"] = "phase3_puzzle_vault"
        p["tutorial_dungeon"]["room_states"].setdefault("phase3_puzzle_vault", {})["lattice_disarmed"] = False

        blocked = p3.move_tutorial_dungeon_room(p, "phase3_foundry_hall")
        self.assertFalse(blocked["success"])
        self.assertIn("lattice", blocked["message"].lower())

        # Disarm lattice
        p["tutorial_dungeon"]["room_states"]["phase3_puzzle_vault"]["lattice_disarmed"] = True
        allowed = p3.move_tutorial_dungeon_room(p, "phase3_foundry_hall")
        self.assertTrue(allowed["success"])

    def test_09_fuzz_invalid_and_malformed_room_ids(self):
        """Fuzz testing with random garbage, injection strings, numbers, None, empty strings."""
        fuzz_inputs = [
            None, "", "   ", 0, 42, 3.14, True, False,
            "non_existent_room", "phase4_secret", "../etc/passwd",
            "<script>alert(1)</script>", "'; DROP TABLE rooms; --",
            "phase1_telemetry_sanctum\x00extra"
        ]

        for bad_id in fuzz_inputs:
            p = copy.deepcopy(self.player)
            res = p3.move_tutorial_dungeon_room(p, bad_id)
            self.assertFalse(res.get("success"), f"Malformed target_room_id '{bad_id}' was unexpectedly accepted!")

    def test_10_random_walk_fuzzing_100_steps(self):
        """100-step random walk through valid adjacent graph edges maintaining state invariants."""
        p = copy.deepcopy(self.player)
        p["tutorial_dungeon"]["transit_phase2_unlocked"] = True
        p["tutorial_dungeon"]["transit_phase3_unlocked"] = True
        p["tutorial_dungeon"]["room_states"].setdefault("phase3_puzzle_vault", {})["lattice_disarmed"] = True
        p["tutorial_dungeon"]["room_states"]["phase3_puzzle_vault"]["secret_door_revealed"] = True
        p["tutorial_dungeon"]["room_states"].setdefault("phase3_foundry_hall", {})["construct_defeated"] = True

        for step in range(100):
            cur_id = p["tutorial_dungeon"]["current_room"]
            conns = p3.TUTORIAL_MINI_DUNGEON_ROOMS[cur_id]["connections"]
            target = random.choice(conns)
            res = p3.move_tutorial_dungeon_room(p, target)
            self.assertTrue(res["success"], f"Step {step}: failed valid move from {cur_id} to {target}")
            self.assertEqual(p["tutorial_dungeon"]["current_room"], target)
            self.assertIn(target, p["tutorial_dungeon"]["visited_rooms"])

    def test_11_unhashable_room_id_crash_vulnerability(self):
        """
        Adversarial test: Passing unhashable types (list, dict) as target_room_id crashes
        move_tutorial_dungeon_room with unhandled TypeError instead of returning {'success': False}.
        """
        p = copy.deepcopy(self.player)
        try:
            res = p3.move_tutorial_dungeon_room(p, ["malicious", "list"])
            self.assertFalse(res.get("success"))
        except TypeError as te:
            self.fail(f"CRASH VULNERABILITY: move_tutorial_dungeon_room crashed with unhandled TypeError on list target_room_id: {te}")



class TestHarmonicPuzzleVaultPermutations(unittest.TestCase):
    """Adversarial stress-testing of Harmonic Puzzle Vault 3-dial permutations and Arcana checks."""

    def setUp(self):
        self.player = cg.generate_starting_character(
            name="PuzzleSolver",
            point_alloc={"STR": 2, "DEX": 2, "CON": 2, "INT": 8, "WIS": 3, "CHA": 3},
            relic_key="vintage_zippo_lighter",
            start_tutorial=True
        )
        # Strip all items and personal relics to test pure skill check
        self.player["inventory"] = []
        self.player["personal_relic"] = ""
        p3.initialize_tutorial_mini_dungeon(self.player)

    def test_01_all_valid_dial_combinations_and_casing(self):
        """Verify all valid dial combinations with case-insensitivity and whitespace trimming."""
        valid_combos = [
            ["sun", "moon", "star"],
            ["Sun", "Moon", "Star"],
            ["SUN", "MOON", "STAR"],
            ["  Sun  ", " Moon\t", "Star "],
            ["3", "7", "12"],
            [3, 7, 12],
            ["3", "1", "4"],
            [3, 1, 4],
            ["alpha", "beta", "gamma"],
            ["ALPHA", "BETA", "GAMMA"],
            ["alpha", "omega", "aether"],
        ]

        for combo in valid_combos:
            p = copy.deepcopy(self.player)
            res = p3.solve_tutorial_puzzle(p, dial_inputs=combo)
            self.assertTrue(res["success"], f"Failed valid dial combo: {combo}")
            self.assertTrue(res["solved"])
            self.assertTrue(res["lattice_disarmed"])
            self.assertEqual(res["method"], "dial_input")
            self.assertEqual(res["xp_gained"], 100)
            self.assertEqual(res["col_gained"], 25)

    def test_02_invalid_dial_permutations_and_rejections(self):
        """Adversarial permutations: scrambled dial order must be strictly rejected."""
        scrambled_combos = [
            ["moon", "sun", "star"],
            ["star", "moon", "sun"],
            ["star", "sun", "moon"],
            ["7", "3", "12"],
            ["12", "7", "3"],
            [7, 3, 12],
            ["beta", "alpha", "gamma"],
            ["gamma", "beta", "alpha"],
            ["omega", "alpha", "aether"],
        ]

        for combo in scrambled_combos:
            p = copy.deepcopy(self.player)
            res = p3.solve_tutorial_puzzle(p, dial_inputs=combo)
            self.assertFalse(res["success"], f"Scrambled combo {combo} should have been rejected!")
            self.assertFalse(res["solved"])
            self.assertFalse(res["lattice_disarmed"])
            self.assertEqual(res["method"], "failed_input")
            self.assertEqual(res["xp_gained"], 0)

    def test_03_fuzz_malformed_and_boundary_dial_inputs(self):
        """Fuzz testing with incorrect lengths, garbage strings, and malformed structures."""
        malformed = [
            [],
            ["sun"],
            ["sun", "moon"],
            ["sun", "moon", "star", "extra"],
            ["sun", "moon", "star", "aether", "void"],
            ["fire", "water", "earth"],
            ["", "", ""],
            [None, None, None],
            ["sun", None, "star"],
            [0, 0, 0],
            ["1", "2", "3"],
            ["!@#$", "%^&*", "()_+"],
        ]

        for bad in malformed:
            p = copy.deepcopy(self.player)
            res = p3.solve_tutorial_puzzle(p, dial_inputs=bad)
            self.assertFalse(res["success"], f"Malformed dial input {bad} was unexpectedly accepted!")
            self.assertFalse(res["solved"])

    def test_04_arcana_check_threshold_dc12_boundary_tests(self):
        """Exhaustive Arcana check threshold boundary tests across various INT stats vs DC 12."""
        cases = [
            # (int_stat, mod, roll, expected_pass)
            (10, 0, 11, False),
            (10, 0, 12, True),
            (6, -2, 13, False),
            (6, -2, 14, True),
            (14, 2, 9, False),
            (14, 2, 10, True),
            (18, 4, 7, False),
            (18, 4, 8, True),
            (2, -4, 15, False),
            (2, -4, 16, True),
            (20, 5, 6, False),
            (20, 5, 7, True),
        ]

        for int_val, expected_mod, roll, expected_pass in cases:
            p = copy.deepcopy(self.player)
            p["stats"]["INT"] = int_val
            res = p3.solve_tutorial_puzzle(p, deterministic_roll=roll)
            if expected_pass:
                self.assertTrue(res["success"], f"INT {int_val} roll {roll} expected pass, got {res}")
                self.assertEqual(res["method"], "skill_check")
            else:
                self.assertFalse(res["success"], f"INT {int_val} roll {roll} expected fail, got {res}")
                self.assertEqual(res["method"], "failed_skill_check")

    def test_05_tuning_fork_bypass_personal_relic(self):
        """Verify 440 Hz Tuning Fork bypass when set in personal_relic."""
        relic_keys = ["tuning_fork", "guitar_tuning_fork", "Vintage 440 Hz Guitar Tuning Fork"]
        for rk in relic_keys:
            p = copy.deepcopy(self.player)
            p["personal_relic"] = rk
            res = p3.solve_tutorial_puzzle(p)
            self.assertTrue(res["success"], f"Relic {rk} failed to bypass puzzle")
            self.assertEqual(res["method"], "relic_bypass")
            self.assertTrue(res["lattice_disarmed"])

    def test_06_tuning_fork_bypass_inventory_item(self):
        """Verify 440 Hz Tuning Fork bypass when carried in inventory."""
        p = copy.deepcopy(self.player)
        p["inventory"].append({"name": "440 Hz Tuning Fork", "qty": 1})
        res = p3.solve_tutorial_puzzle(p)
        self.assertTrue(res["success"])
        self.assertEqual(res["method"], "relic_bypass")

    def test_07_puzzle_solution_idempotency(self):
        """Solving the puzzle a second time must return already_solved with 0 duplicate XP/Col."""
        p = copy.deepcopy(self.player)
        res1 = p3.solve_tutorial_puzzle(p, dial_inputs=["Sun", "Moon", "Star"])
        self.assertTrue(res1["success"])
        self.assertEqual(res1["xp_gained"], 100)

        res2 = p3.solve_tutorial_puzzle(p, dial_inputs=["Sun", "Moon", "Star"])
        self.assertTrue(res2["success"])
        self.assertEqual(res2["method"], "already_solved")
        self.assertEqual(res2["xp_gained"], 0)
        self.assertEqual(res2["col_gained"], 0)

    def test_08_non_sonic_relic_does_not_falsely_claim_acoustic_bypass(self):
        """
        Adversarial check: If a character has a Zippo lighter and no Tuning Fork,
        calling solve_tutorial_puzzle with use_relic=True should NOT claim 440 Hz acoustic bypass!
        """
        p = copy.deepcopy(self.player)
        p["personal_relic"] = "vintage_zippo_lighter"
        p["inventory"] = [{"name": "Vintage Zippo Lighter"}]
        # Player has NO sonic relic. If use_relic=True is passed:
        res = p3.solve_tutorial_puzzle(p, use_relic=True)
        # Check if code claims 440 Hz acoustic wave with a zippo lighter
        has_false_claim = any("440 Hz" in log for log in res.get("logs", []))
        if has_false_claim:
            self.fail(f"FLAW FOUND: Zippo lighter falsely triggered 440 Hz acoustic relic bypass: {res.get('logs')}")


class TestConcealedScriptoriumSecretDoor(unittest.TestCase):
    """Adversarial stress-testing of Concealed Scriptorium secret door discovery mechanics."""

    def setUp(self):
        self.player = cg.generate_starting_character(
            name="SecretSeeker",
            point_alloc={"STR": 2, "DEX": 2, "CON": 2, "INT": 2, "WIS": 8, "CHA": 4},
            relic_key="vintage_zippo_lighter",
            start_tutorial=True
        )
        self.player["inventory"] = []
        self.player["personal_relic"] = ""
        p3.initialize_tutorial_mini_dungeon(self.player)

    def test_01_perception_check_dc13_boundary_tests(self):
        """Exhaustive boundary tests for Perception DC 13 check across WIS stat modifiers."""
        cases = [
            # (wis_stat, mod, roll, expected_pass)
            (10, 0, 12, False),
            (10, 0, 13, True),
            (6, -2, 14, False),
            (6, -2, 15, True),
            (16, 3, 9, False),
            (16, 3, 10, True),
            (20, 5, 7, False),
            (20, 5, 8, True),
            (2, -4, 16, False),
            (2, -4, 17, True),
        ]

        for wis_val, expected_mod, roll, expected_pass in cases:
            p = copy.deepcopy(self.player)
            p["stats"]["WIS"] = wis_val
            p["tutorial_dungeon"]["room_states"]["phase3_puzzle_vault"]["secret_door_revealed"] = False
            res = p3.discover_tutorial_secret_door(p, deterministic_roll=roll)
            if expected_pass:
                self.assertTrue(res["success"], f"WIS {wis_val} roll {roll} expected pass, got {res}")
                self.assertEqual(res["method"], "perception_check")
                self.assertEqual(res["room_unlocked"], "phase3_secret_scriptorium")
            else:
                self.assertFalse(res["success"], f"WIS {wis_val} roll {roll} expected fail, got {res}")
                self.assertEqual(res["method"], "failed_perception")
                self.assertIsNone(res["room_unlocked"])

    def test_02_polaroid_camera_flash_bypass(self):
        """Verify Polaroid Camera magnesium flash exposes hidden pressure plate."""
        p = copy.deepcopy(self.player)
        p["personal_relic"] = "polaroid_camera"
        p["inventory"].append({"name": "Vintage Polaroid Land Camera", "qty": 1})

        res = p3.discover_tutorial_secret_door(p, use_relic=True)
        self.assertTrue(res["success"])
        self.assertTrue(res["discovered"])
        self.assertEqual(res["method"], "polaroid_camera")
        self.assertEqual(res["room_unlocked"], "phase3_secret_scriptorium")
        self.assertEqual(res["col_gained"], 75)
        self.assertEqual(res["xp_gained"], 100)
        self.assertIn("Tome of the Crucible Scribe", [it["name"] if isinstance(it, dict) else str(it) for it in p["inventory"]])

    def test_03_tuning_fork_resonance_bypass(self):
        """Verify 440 Hz Tuning Fork resonance detects hollow masonry cavity."""
        p = copy.deepcopy(self.player)
        p["personal_relic"] = "tuning_fork"
        p["inventory"].append({"name": "440 Hz Tuning Fork", "qty": 1})

        res = p3.discover_tutorial_secret_door(p, use_relic=True)
        self.assertTrue(res["success"])
        self.assertTrue(res["discovered"])
        self.assertEqual(res["method"], "tuning_fork_resonance")
        self.assertEqual(res["room_unlocked"], "phase3_secret_scriptorium")

    def test_04_secret_door_idempotency(self):
        """Discovering secret door a second time returns already_discovered with 0 duplicate rewards."""
        p = copy.deepcopy(self.player)
        res1 = p3.discover_tutorial_secret_door(p, deterministic_roll=15)
        self.assertTrue(res1["success"])
        self.assertEqual(res1["col_gained"], 75)

        res2 = p3.discover_tutorial_secret_door(p, deterministic_roll=15)
        self.assertTrue(res2["success"])
        self.assertEqual(res2["method"], "already_discovered")
        self.assertEqual(res2["col_gained"], 0)
        self.assertEqual(res2["xp_gained"], 0)

    def test_05_zippo_does_not_falsely_pass_perception_check(self):
        """
        Adversarial check: If a player uses a non-applicable relic (Zippo Lighter) with use_relic=True
        and fails the Perception roll (e.g. roll=1 vs DC 13), it MUST NOT pass and claim perception success!
        """
        p = copy.deepcopy(self.player)
        p["personal_relic"] = "vintage_zippo_lighter"
        p["stats"]["WIS"] = 10  # mod = 0
        res = p3.discover_tutorial_secret_door(p, use_relic=True, deterministic_roll=1)

        # Total is 1 + 0 = 1 vs DC 13. It should FAIL.
        if res.get("success") and res.get("method") == "perception_check":
            self.fail(f"FLAW FOUND: Zippo lighter with use_relic=True falsely forced perception_check pass on roll 1: {res}")


class TestMiniDungeonDrillsAndGraduationPropertyChecks(unittest.TestCase):

    """Property checks and edge case tests across Phase I/II drills, transitions, and graduation."""

    def setUp(self):
        self.player = cg.generate_starting_character(
            name="DrillHero",
            point_alloc={"STR": 4, "DEX": 4, "CON": 4, "INT": 4, "WIS": 2, "CHA": 2},
            start_tutorial=True
        )
        p3.initialize_tutorial_mini_dungeon(self.player)

    def test_01_encumbrance_str_times_15_property_fuzzing(self):
        """Property: Base carry limit strictly equals STR * 15.0 lbs across random STR allocations."""
        for str_val in range(1, 35):
            p = copy.deepcopy(self.player)
            p["stats"]["STR"] = str_val
            enc = p3.resolve_tutorial_encumbrance_hazard(p)
            expected = round(str_val * 15.0, 1)
            self.assertEqual(enc["base_carry_limit_lbs"], expected, f"STR {str_val} mismatch")

    def test_02_gear_durability_bounds(self):
        """Durability degradation and whetstone repair cap at max durability."""
        p = copy.deepcopy(self.player)
        p["gear_durability"] = {"main_hand": {"cur": 60, "max": 60, "state": "Pristine"}}
        p3.apply_durability_damage(p, "main_hand", 10)
        self.assertEqual(p["gear_durability"]["main_hand"]["cur"], 50)

        # Over-repair should cap at 60
        rep = p3.repair_gear_durability(p, "main_hand", 50)
        self.assertEqual(rep["cur"], 60)
        self.assertEqual(rep["state"], "Pristine")

    def test_03_multi_limb_arm_counts_and_combo_scaling(self):
        """2-armed characters execute dual_wield; 4-armed characters execute quad_flurry."""
        res_2arm = p3.resolve_tutorial_multi_limb_drill(self.player)
        self.assertEqual(res_2arm["drill_mode"], "dual_wield")
        self.assertEqual(res_2arm["arm_count"], 2)

        glenny = cg.generate_starting_character(name="Glenny", start_tutorial=False)
        res_4arm = p3.resolve_tutorial_multi_limb_drill(glenny)
        self.assertEqual(res_4arm["drill_mode"], "quad_flurry")
        self.assertEqual(res_4arm["arm_count"], 4)
        self.assertGreater(res_4arm["total_combo_damage"], res_2arm["total_combo_damage"])

    def test_04_phase2_to_phase3_transit_gate_missing_enforcement(self):
        """
        Adversarial test: Moving from phase2_triage_infirmary to phase3_high_ascent
        should require transit_phase3_unlocked (defeating Clockwork Sentinel).
        Currently, move_tutorial_dungeon_room lacks an obstacle gate check for this transition.
        """
        p = copy.deepcopy(self.player)
        p["tutorial_dungeon"]["current_room"] = "phase2_triage_infirmary"
        p["tutorial_dungeon"]["transit_phase3_unlocked"] = False

        res = p3.move_tutorial_dungeon_room(p, "phase3_high_ascent")
        if res.get("success"):
            self.fail("FLAW FOUND: Player skipped Phase II Clockwork Sentinel and entered Phase III without transit_phase3_unlocked!")

    def test_05_graduation_all_8_canonical_items_and_level_3(self):
        """Graduation guarantees Level 3, Washington Borough location, and all 8 canonical loot items."""
        grad = p3.graduate_tutorial_player(self.player)
        self.assertTrue(grad["graduated"])
        self.assertEqual(self.player["level"], 3)
        self.assertEqual(self.player["location"], "Sector 1 Safe-Zone: Washington Borough, NJ")
        for item in p3.TUTORIAL_CANONICAL_LOOT:
            self.assertIn(item, self.player["inventory"], f"Missing graduation loot item: {item}")


if __name__ == "__main__":
    unittest.main()

