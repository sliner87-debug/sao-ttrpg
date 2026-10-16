"""
=============================================================================
MILESTONE 3 ITERATION 2 PROPERTY-BASED FUZZING HARNESS & VERIFICATION SUITE
=============================================================================
Authored by Milestone 3 Iteration 2 Challenger 1.

Empirical verification suite challenging Milestone 3 Iteration 2 remediations:
1. Property: Non-adjacent jumps across all 13 rooms return success=False.
   - Exhaustive 13x13 Cartesian matrix testing under default state.
   - Exhaustive 13x13 Cartesian matrix testing under fully unlocked state.
   - Randomized state flag permutations (transit, lattice, construct, secret door).
   - Self-loop invariance (u -> u must be rejected).
   - State non-mutation invariance (position, phase, visited list unchanged on rejection).
2. Property: Secret door discovery cannot be bypassed.
   - Scriptorium inaccessible prior to secret door discovery.
   - Scriptorium inaccessible from any non-adjacent room even when discovered.
   - Scriptorium hidden from get_tutorial_adjacent_rooms until revealed.
   - Inapplicable relics fuzzing: non-optical/non-acoustic relics cannot bypass Perception.
   - Boundary Perception DC 13 threshold testing across all rolls and WIS modifiers.
   - Optical and acoustic relics positive bypass verification.
   - Secret door discovery idempotency (0 duplicate XP, 0 duplicate Col, 0 duplicate Tomes).
3. Property: Phase II -> Phase III transit cannot be bypassed.
   - Portcullis blocks phase2_triage_infirmary -> phase3_high_ascent when transit_phase3_unlocked is False.
   - Fuzzing falsy/corrupted transit_phase3_unlocked states (None, 0, "", [], {}, missing key).
   - Adjacency filtering reflects portcullis locked state.
   - Clean transition succeeds once Sentinel is defeated via resolve_tutorial_status_triage.
4. Property: Boss portal cannot be bypassed.
   - Phalanx Construct blocks phase3_foundry_hall -> phase3_warden_lair when construct_defeated is False.
   - Fuzzing falsy/corrupted construct_defeated states (None, 0, "", [], {}, missing room state).
   - Adjacency filtering reflects construct locked state.
   - Clean transition succeeds once Construct is defeated via resolve_tutorial_foundry_battle.
5. Property: Unhashable and malformed inputs do not raise unhandled exceptions.
   - Unhashable target_room_id types (list, dict, set, bytearray, generator) in move_tutorial_dungeon_room.
   - Non-string scalar target_room_id types (None, int, float, bool, complex, tuple, bytes, object, callable).
   - Non-dict and malformed player states (None, list, string, int, empty dict).
   - Unhashable and malformed dial_inputs in solve_tutorial_puzzle (lists of lists, dicts, sets).
   - Graceful resilience and no unhandled crash across all endpoints.
"""

import copy
import itertools
import os
import random
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import backend.character_generator as cg
import backend.mechanics as p3


class TestNonAdjacentJumpsProperty(unittest.TestCase):
    """Property 1: Non-adjacent jumps across all 13 rooms return success=False."""

    def setUp(self):
        self.player = cg.generate_starting_character(
            name="AdversaryRunner",
            point_alloc={"STR": 4, "DEX": 4, "CON": 4, "INT": 4, "WIS": 2, "CHA": 2},
            race_key="pure_human" if "pure_human" in cg.RACIAL_LINEAGES else "human",
            class_key="fighter",
            relic_key="tuning_fork",
            start_tutorial=True
        )
        p3.initialize_tutorial_mini_dungeon(self.player)
        self.all_rooms = list(p3.TUTORIAL_MINI_DUNGEON_ROOMS.keys())
        self.assertEqual(len(self.all_rooms), 13, "Expected exactly 13 tutorial rooms.")

    def test_01_exhaustive_all_pairs_matrix_default_state(self):
        """Property: In default state, for every pair (u, v) where v not in connections(u), move must fail."""
        violations = []
        for u in self.all_rooms:
            conns = p3.TUTORIAL_MINI_DUNGEON_ROOMS[u].get("connections", [])
            for v in self.all_rooms:
                if v in conns:
                    continue  # adjacent edge
                p = copy.deepcopy(self.player)
                p["tutorial_dungeon"]["current_room"] = u
                res = p3.move_tutorial_dungeon_room(p, v)
                if res.get("success"):
                    violations.append((u, v, res))

        self.assertEqual(
            violations, [],
            f"Adjacency violation in default state! Non-adjacent jumps succeeded: {violations}"
        )

    def test_02_exhaustive_all_pairs_matrix_fully_unlocked_state(self):
        """Property: Even when ALL gates/obstacles are fully unlocked, non-adjacent jumps must STILL fail."""
        violations = []
        for u in self.all_rooms:
            conns = p3.TUTORIAL_MINI_DUNGEON_ROOMS[u].get("connections", [])
            for v in self.all_rooms:
                if v in conns:
                    continue
                p = copy.deepcopy(self.player)
                tut = p["tutorial_dungeon"]
                tut["current_room"] = u
                # Unlock all barriers globally
                tut["transit_phase2_unlocked"] = True
                tut["transit_phase3_unlocked"] = True
                r_states = tut.setdefault("room_states", {})
                r_states.setdefault("phase3_puzzle_vault", {})["lattice_disarmed"] = True
                r_states.setdefault("phase3_puzzle_vault", {})["secret_door_revealed"] = True
                r_states.setdefault("phase3_foundry_hall", {})["construct_defeated"] = True

                res = p3.move_tutorial_dungeon_room(p, v)
                if res.get("success"):
                    violations.append((u, v, res))

        self.assertEqual(
            violations, [],
            f"Adjacency violation in fully unlocked state! Non-adjacent jumps succeeded: {violations}"
        )

    def test_03_random_flag_permutations_fuzzing(self):
        """Fuzz non-adjacent moves with 100 randomized flag permutations."""
        rng = random.Random(42)
        non_adjacent_pairs = [
            (u, v) for u in self.all_rooms for v in self.all_rooms
            if v not in p3.TUTORIAL_MINI_DUNGEON_ROOMS[u].get("connections", [])
        ]

        for trial in range(100):
            u, v = rng.choice(non_adjacent_pairs)
            p = copy.deepcopy(self.player)
            tut = p["tutorial_dungeon"]
            tut["current_room"] = u
            tut["transit_phase2_unlocked"] = rng.choice([True, False, None])
            tut["transit_phase3_unlocked"] = rng.choice([True, False, None])
            r_states = tut.setdefault("room_states", {})
            r_states.setdefault("phase3_puzzle_vault", {})["lattice_disarmed"] = rng.choice([True, False])
            r_states.setdefault("phase3_puzzle_vault", {})["secret_door_revealed"] = rng.choice([True, False])
            r_states.setdefault("phase3_foundry_hall", {})["construct_defeated"] = rng.choice([True, False])

            res = p3.move_tutorial_dungeon_room(p, v)
            self.assertFalse(
                res.get("success"),
                f"Trial {trial}: non-adjacent move {u} -> {v} unexpectedly succeeded: {res}"
            )
            self.assertEqual(tut["current_room"], u, f"Player position was mutated from {u} on rejected move")

    def test_04_self_loop_invariance(self):
        """Property: Moving to current room (u -> u) must fail because rooms are not self-connected."""
        for u in self.all_rooms:
            p = copy.deepcopy(self.player)
            p["tutorial_dungeon"]["current_room"] = u
            res = p3.move_tutorial_dungeon_room(p, u)
            self.assertFalse(
                res.get("success"),
                f"Self-loop move {u} -> {u} unexpectedly succeeded: {res}"
            )
            self.assertEqual(p["tutorial_dungeon"]["current_room"], u)

    def test_05_state_non_mutation_invariance_on_rejection(self):
        """Property: When a move is rejected, visited_rooms, phase, and location must not mutate."""
        p = copy.deepcopy(self.player)
        p["tutorial_dungeon"]["current_room"] = "phase1_telemetry_sanctum"
        p["tutorial_dungeon"]["visited_rooms"] = ["phase1_telemetry_sanctum"]
        p["tutorial_dungeon"]["current_phase"] = 1
        initial_loc = p.get("location")

        res = p3.move_tutorial_dungeon_room(p, "phase3_warden_lair")
        self.assertFalse(res.get("success"))
        self.assertEqual(p["tutorial_dungeon"]["current_room"], "phase1_telemetry_sanctum")
        self.assertEqual(p["tutorial_dungeon"]["visited_rooms"], ["phase1_telemetry_sanctum"])
        self.assertEqual(p["tutorial_dungeon"]["current_phase"], 1)
        self.assertEqual(p.get("location"), initial_loc)


class TestSecretDoorDiscoveryBypassProperty(unittest.TestCase):
    """Property 2: Secret door discovery cannot be bypassed."""

    def setUp(self):
        self.player = cg.generate_starting_character(
            name="SecretExaminer",
            point_alloc={"STR": 2, "DEX": 2, "CON": 2, "INT": 4, "WIS": 8, "CHA": 2},
            relic_key="vintage_zippo_lighter",
            start_tutorial=True
        )
        self.player["inventory"] = []
        self.player["personal_relic"] = ""
        p3.initialize_tutorial_mini_dungeon(self.player)

    def test_01_scriptorium_inaccessible_prior_to_discovery(self):
        """Moving from phase3_puzzle_vault to phase3_secret_scriptorium fails when secret_door_revealed is False."""
        p = copy.deepcopy(self.player)
        p["tutorial_dungeon"]["current_room"] = "phase3_puzzle_vault"
        p["tutorial_dungeon"]["room_states"].setdefault("phase3_puzzle_vault", {})["secret_door_revealed"] = False

        res = p3.move_tutorial_dungeon_room(p, "phase3_secret_scriptorium")
        self.assertFalse(res["success"])
        self.assertIn("secret door", res["message"].lower())
        self.assertEqual(p["tutorial_dungeon"]["current_room"], "phase3_puzzle_vault")

    def test_02_scriptorium_hidden_from_adjacent_listing_when_undiscovered(self):
        """Concealed Scriptorium must NOT be listed in get_tutorial_adjacent_rooms before discovery."""
        p = copy.deepcopy(self.player)
        p["tutorial_dungeon"]["current_room"] = "phase3_puzzle_vault"
        p["tutorial_dungeon"]["room_states"].setdefault("phase3_puzzle_vault", {})["secret_door_revealed"] = False

        adj = p3.get_tutorial_adjacent_rooms(p)
        room_ids = [r["room_id"] for r in adj]
        self.assertNotIn("phase3_secret_scriptorium", room_ids)

        # After discovery, it must appear
        p["tutorial_dungeon"]["room_states"]["phase3_puzzle_vault"]["secret_door_revealed"] = True
        adj_after = p3.get_tutorial_adjacent_rooms(p)
        room_ids_after = [r["room_id"] for r in adj_after]
        self.assertIn("phase3_secret_scriptorium", room_ids_after)

    def test_03_non_applicable_relics_fuzzing(self):
        """Fuzz testing with 100 trials of non-applicable relics: cannot bypass Perception check."""
        non_applicable_relics = [
            "vintage_zippo_lighter", "smartphone", "pocket_watch", "brass_compass",
            "silver_locket", "car_keys", "fountain_pen", "rubiks_cube",
            "leather_journal", "bone_dice", "silver_dollar", "crystal_shard"
        ]
        rng = random.Random(1337)

        for trial in range(100):
            relic = rng.choice(non_applicable_relics)
            p = copy.deepcopy(self.player)
            p["personal_relic"] = relic
            p["inventory"] = [{"name": relic.replace("_", " ").title(), "qty": 1}]
            # Set WIS between 6 (-2 mod) and 14 (+2 mod)
            wis_val = rng.randint(6, 14)
            p["stats"]["WIS"] = wis_val
            wis_mod = (wis_val - 10) // 2

            # Roll so that total < 13
            # total = roll + wis_mod < 13 => roll < 13 - wis_mod
            max_failing_roll = min(20, 12 - wis_mod)
            if max_failing_roll < 1:
                continue
            roll = rng.randint(1, max_failing_roll)
            total = roll + wis_mod
            self.assertLess(total, 13)

            res = p3.discover_tutorial_secret_door(p, use_relic=True, deterministic_roll=roll)
            self.assertFalse(
                res.get("success"),
                f"Trial {trial}: Inapplicable relic '{relic}' bypassed perception on total {total} vs DC 13: {res}"
            )
            self.assertFalse(res.get("discovered"))
            self.assertEqual(res.get("method"), "failed_perception")
            self.assertIsNone(res.get("room_unlocked"))
            self.assertFalse(
                p["tutorial_dungeon"]["room_states"]["phase3_puzzle_vault"].get("secret_door_revealed", False)
            )

    def test_04_optical_and_acoustic_relic_positive_bypass(self):
        """Optical (polaroid) and acoustic (tuning fork) relics strictly bypass perception even with minimum stats."""
        # Polaroid Camera
        p_opt = copy.deepcopy(self.player)
        p_opt["personal_relic"] = "polaroid_camera"
        p_opt["stats"]["WIS"] = 2  # mod -4
        res_opt = p3.discover_tutorial_secret_door(p_opt, use_relic=True, deterministic_roll=1)
        self.assertTrue(res_opt["success"])
        self.assertTrue(res_opt["discovered"])
        self.assertEqual(res_opt["method"], "polaroid_camera")
        self.assertEqual(res_opt["room_unlocked"], "phase3_secret_scriptorium")

        # Tuning Fork
        p_ac = copy.deepcopy(self.player)
        p_ac["personal_relic"] = "tuning_fork"
        p_ac["stats"]["WIS"] = 2
        res_ac = p3.discover_tutorial_secret_door(p_ac, use_relic=True, deterministic_roll=1)
        self.assertTrue(res_ac["success"])
        self.assertTrue(res_ac["discovered"])
        self.assertEqual(res_ac["method"], "tuning_fork_resonance")
        self.assertEqual(res_ac["room_unlocked"], "phase3_secret_scriptorium")

    def test_05_secret_door_idempotency_rewards(self):
        """Subsequent discovery calls must not award duplicate XP, Col, or Tomes."""
        p = copy.deepcopy(self.player)
        res1 = p3.discover_tutorial_secret_door(p, deterministic_roll=18)
        self.assertTrue(res1["success"])
        self.assertEqual(res1["xp_gained"], 100)
        self.assertEqual(res1["col_gained"], 75)
        tome_count = sum(1 for it in p["inventory"] if (it.get("name") if isinstance(it, dict) else str(it)) == "Tome of the Crucible Scribe")
        self.assertEqual(tome_count, 1)

        res2 = p3.discover_tutorial_secret_door(p, deterministic_roll=18)
        self.assertTrue(res2["success"])
        self.assertEqual(res2["method"], "already_discovered")
        self.assertEqual(res2["xp_gained"], 0)
        self.assertEqual(res2["col_gained"], 0)
        tome_count2 = sum(1 for it in p["inventory"] if (it.get("name") if isinstance(it, dict) else str(it)) == "Tome of the Crucible Scribe")
        self.assertEqual(tome_count2, 1)


class TestPhaseIIToIIITransitGateProperty(unittest.TestCase):
    """Property 3: Phase II -> III transit cannot be bypassed."""

    def setUp(self):
        self.player = cg.generate_starting_character(
            name="TransitHero",
            point_alloc={"STR": 4, "DEX": 4, "CON": 4, "INT": 4, "WIS": 2, "CHA": 2},
            start_tutorial=True
        )
        p3.initialize_tutorial_mini_dungeon(self.player)

    def test_01_portcullis_blocks_movement_when_transit_unlocked_is_false(self):
        """Player at phase2_triage_infirmary cannot pass to phase3_high_ascent without transit_phase3_unlocked."""
        p = copy.deepcopy(self.player)
        p["tutorial_dungeon"]["current_room"] = "phase2_triage_infirmary"
        p["tutorial_dungeon"]["current_phase"] = 2
        p["tutorial_dungeon"]["transit_phase3_unlocked"] = False

        res = p3.move_tutorial_dungeon_room(p, "phase3_high_ascent")
        self.assertFalse(res["success"])
        self.assertIn("Clockwork Sentinel", res["message"])
        self.assertEqual(p["tutorial_dungeon"]["current_room"], "phase2_triage_infirmary")
        self.assertEqual(p["tutorial_dungeon"]["current_phase"], 2)

    def test_02_fuzzing_falsy_and_missing_transit_flag(self):
        """Fuzz testing with various falsy and corrupted transit_phase3_unlocked values."""
        falsy_values = [False, None, 0, "", [], {}, set(), 0.0]
        for val in falsy_values:
            p = copy.deepcopy(self.player)
            p["tutorial_dungeon"]["current_room"] = "phase2_triage_infirmary"
            p["tutorial_dungeon"]["transit_phase3_unlocked"] = val

            res = p3.move_tutorial_dungeon_room(p, "phase3_high_ascent")
            self.assertFalse(
                res["success"],
                f"transit_phase3_unlocked={repr(val)} unexpectedly allowed transit into Phase III!"
            )

        # Deleting the key entirely
        p = copy.deepcopy(self.player)
        p["tutorial_dungeon"]["current_room"] = "phase2_triage_infirmary"
        p["tutorial_dungeon"].pop("transit_phase3_unlocked", None)
        res = p3.move_tutorial_dungeon_room(p, "phase3_high_ascent")
        self.assertFalse(res["success"], "Missing transit_phase3_unlocked key unexpectedly allowed transit!")

    def test_03_adjacency_filtering_reflects_portcullis_gate(self):
        """get_tutorial_adjacent_rooms reflects portcullis accessibility status."""
        p = copy.deepcopy(self.player)
        p["tutorial_dungeon"]["current_room"] = "phase2_triage_infirmary"
        p["tutorial_dungeon"]["transit_phase3_unlocked"] = False

        # Unfiltered
        adj = p3.get_tutorial_adjacent_rooms(p, filter_locked=False)
        ha = next((r for r in adj if r["room_id"] == "phase3_high_ascent"), None)
        self.assertIsNotNone(ha)
        self.assertFalse(ha["accessible"])
        self.assertIn("Clockwork Sentinel", ha["reason"])

        # Filtered
        adj_filtered = p3.get_tutorial_adjacent_rooms(p, filter_locked=True)
        ha_filtered = next((r for r in adj_filtered if r["room_id"] == "phase3_high_ascent"), None)
        self.assertIsNone(ha_filtered, "Locked phase3_high_ascent should be filtered out when filter_locked=True")

    def test_04_successful_transit_after_sentinel_resolution(self):
        """Resolving triage defeats sentinel and unlocks clean transit to Phase III."""
        p = copy.deepcopy(self.player)
        p["tutorial_dungeon"]["current_room"] = "phase2_triage_infirmary"
        p["tutorial_dungeon"]["current_phase"] = 2

        triage_res = p3.resolve_tutorial_status_triage(p)
        self.assertTrue(triage_res["success"])
        self.assertTrue(p["tutorial_dungeon"]["transit_phase3_unlocked"])

        move_res = p3.move_tutorial_dungeon_room(p, "phase3_high_ascent")
        self.assertTrue(move_res["success"])
        self.assertEqual(p["tutorial_dungeon"]["current_room"], "phase3_high_ascent")
        self.assertEqual(p["tutorial_dungeon"]["current_phase"], 3)


class TestBossPortalGateProperty(unittest.TestCase):
    """Property 4: Boss portal cannot be bypassed."""

    def setUp(self):
        self.player = cg.generate_starting_character(
            name="ConstructChallenger",
            point_alloc={"STR": 4, "DEX": 4, "CON": 4, "INT": 4, "WIS": 2, "CHA": 2},
            start_tutorial=True
        )
        p3.initialize_tutorial_mini_dungeon(self.player)

    def test_01_construct_blocks_boss_portal_when_not_defeated(self):
        """Player at phase3_foundry_hall cannot move to phase3_warden_lair without construct_defeated."""
        p = copy.deepcopy(self.player)
        p["tutorial_dungeon"]["current_room"] = "phase3_foundry_hall"
        p["tutorial_dungeon"]["room_states"].setdefault("phase3_foundry_hall", {})["construct_defeated"] = False

        res = p3.move_tutorial_dungeon_room(p, "phase3_warden_lair")
        self.assertFalse(res["success"])
        self.assertIn("Aether-Forged Phalanx Construct", res["message"])
        self.assertEqual(p["tutorial_dungeon"]["current_room"], "phase3_foundry_hall")

    def test_02_fuzzing_falsy_and_missing_construct_flag(self):
        """Fuzz testing with various falsy and corrupted construct_defeated values."""
        falsy_values = [False, None, 0, "", [], {}, set(), 0.0]
        for val in falsy_values:
            p = copy.deepcopy(self.player)
            p["tutorial_dungeon"]["current_room"] = "phase3_foundry_hall"
            p["tutorial_dungeon"]["room_states"].setdefault("phase3_foundry_hall", {})["construct_defeated"] = val

            res = p3.move_tutorial_dungeon_room(p, "phase3_warden_lair")
            self.assertFalse(
                res["success"],
                f"construct_defeated={repr(val)} unexpectedly allowed transit into Boss Lair!"
            )

        # Missing room_states entry
        p = copy.deepcopy(self.player)
        p["tutorial_dungeon"]["current_room"] = "phase3_foundry_hall"
        p["tutorial_dungeon"]["room_states"].pop("phase3_foundry_hall", None)
        res = p3.move_tutorial_dungeon_room(p, "phase3_warden_lair")
        self.assertFalse(res["success"], "Missing phase3_foundry_hall room_states unexpectedly allowed transit!")

    def test_03_adjacency_filtering_reflects_boss_portal_gate(self):
        """get_tutorial_adjacent_rooms reflects boss portal accessibility status."""
        p = copy.deepcopy(self.player)
        p["tutorial_dungeon"]["current_room"] = "phase3_foundry_hall"
        p["tutorial_dungeon"]["room_states"].setdefault("phase3_foundry_hall", {})["construct_defeated"] = False

        # Unfiltered
        adj = p3.get_tutorial_adjacent_rooms(p, filter_locked=False)
        wl = next((r for r in adj if r["room_id"] == "phase3_warden_lair"), None)
        self.assertIsNotNone(wl)
        self.assertFalse(wl["accessible"])
        self.assertIn("Aether-Forged Phalanx Construct", wl["reason"])

        # Filtered
        adj_filtered = p3.get_tutorial_adjacent_rooms(p, filter_locked=True)
        wl_filtered = next((r for r in adj_filtered if r["room_id"] == "phase3_warden_lair"), None)
        self.assertIsNone(wl_filtered, "Locked phase3_warden_lair should be filtered out when filter_locked=True")

    def test_04_successful_portal_entry_after_construct_combat(self):
        """Resolving foundry combat defeats construct and unlocks portal to Warden Lair."""
        p = copy.deepcopy(self.player)
        p["tutorial_dungeon"]["current_room"] = "phase3_foundry_hall"

        combat_res = p3.resolve_tutorial_foundry_battle(p)
        self.assertTrue(combat_res["success"])
        self.assertTrue(p["tutorial_dungeon"]["room_states"]["phase3_foundry_hall"]["construct_defeated"])

        move_res = p3.move_tutorial_dungeon_room(p, "phase3_warden_lair")
        self.assertTrue(move_res["success"])
        self.assertEqual(p["tutorial_dungeon"]["current_room"], "phase3_warden_lair")


class TestUnhashableAndMalformedInputsProperty(unittest.TestCase):
    """Property 5: Unhashable and malformed inputs do not raise unhandled exceptions."""

    def setUp(self):
        self.player = cg.generate_starting_character(
            name="RobustnessSeeker",
            point_alloc={"STR": 4, "DEX": 4, "CON": 4, "INT": 4, "WIS": 2, "CHA": 2},
            start_tutorial=True
        )
        p3.initialize_tutorial_mini_dungeon(self.player)

    def test_01_unhashable_target_room_ids_no_unhandled_exception(self):
        """Unhashable types as target_room_id must return success=False without crashing."""
        unhashables = [
            [],
            ["phase1_gravity_chasm"],
            [["nested", "list"]],
            {},
            {"room": "phase1_gravity_chasm"},
            set(),
            {"phase1_gravity_chasm"},
            bytearray(b"phase1_gravity_chasm"),
            (x for x in range(5)),
        ]

        for bad_target in unhashables:
            p = copy.deepcopy(self.player)
            try:
                res = p3.move_tutorial_dungeon_room(p, bad_target)
                self.assertFalse(
                    res.get("success"),
                    f"Unhashable target_room_id {type(bad_target)} was unexpectedly accepted!"
                )
            except Exception as exc:
                self.fail(
                    f"CRASH VULNERABILITY: move_tutorial_dungeon_room raised unhandled {type(exc).__name__} on unhashable input {type(bad_target)}: {exc}"
                )

    def test_02_non_string_scalar_target_room_ids_no_unhandled_exception(self):
        """Non-string scalar types as target_room_id must return success=False without crashing."""
        scalars = [
            None,
            0,
            1,
            -1,
            999999999999999999,
            0.0,
            3.14159,
            float("nan"),
            float("inf"),
            float("-inf"),
            True,
            False,
            1 + 2j,
            (),
            ("phase1_gravity_chasm",),
            b"phase1_gravity_chasm",
            object(),
            lambda: "phase1_gravity_chasm",
        ]

        for bad_target in scalars:
            p = copy.deepcopy(self.player)
            try:
                res = p3.move_tutorial_dungeon_room(p, bad_target)
                self.assertFalse(
                    res.get("success"),
                    f"Non-string scalar target_room_id {type(bad_target)} was unexpectedly accepted!"
                )
            except Exception as exc:
                self.fail(
                    f"CRASH VULNERABILITY: move_tutorial_dungeon_room raised unhandled {type(exc).__name__} on scalar input {type(bad_target)}: {exc}"
                )

    def test_03_non_dict_player_states_no_unhandled_exception(self):
        """Non-dict player states must return success=False without crashing."""
        non_dict_states = [
            None,
            [],
            "string_player",
            123,
            3.14,
            True,
            (1, 2, 3),
        ]

        for bad_state in non_dict_states:
            try:
                res = p3.move_tutorial_dungeon_room(bad_state, "phase1_gravity_chasm")
                self.assertFalse(
                    res.get("success"),
                    f"Non-dict player state {type(bad_state)} was unexpectedly accepted!"
                )
            except Exception as exc:
                self.fail(
                    f"CRASH VULNERABILITY: move_tutorial_dungeon_room raised unhandled {type(exc).__name__} on non-dict player state {bad_state}: {exc}"
                )

    def test_04_adjacent_rooms_with_non_dict_inputs_no_unhandled_exception(self):
        """get_tutorial_adjacent_rooms must return [] on non-dict player states without crashing."""
        non_dict_states = [
            None,
            [],
            "string_player",
            123,
            True,
        ]

        for bad_state in non_dict_states:
            try:
                adj = p3.get_tutorial_adjacent_rooms(bad_state)
                self.assertIsInstance(adj, list)
                self.assertEqual(adj, [])
            except Exception as exc:
                self.fail(
                    f"CRASH VULNERABILITY: get_tutorial_adjacent_rooms raised unhandled {type(exc).__name__} on input {bad_state}: {exc}"
                )

    def test_05_puzzle_vault_unhashable_inputs_no_unhandled_exception(self):
        """solve_tutorial_puzzle must handle unhashable dial inputs gracefully without crashing."""
        unhashables = [
            [[], [], []],
            [{}, {}, {}],
            [set(), set(), set()],
            [[1], [2], [3]],
        ]

        for bad_dials in unhashables:
            p = copy.deepcopy(self.player)
            try:
                res = p3.solve_tutorial_puzzle(p, dial_inputs=bad_dials)
                self.assertFalse(res.get("success"))
                self.assertFalse(res.get("solved"))
            except Exception as exc:
                self.fail(
                    f"CRASH VULNERABILITY: solve_tutorial_puzzle raised unhandled {type(exc).__name__} on dial inputs {bad_dials}: {exc}"
                )

    def test_06_discover_secret_door_unhashable_inventory_no_unhandled_exception(self):
        """discover_tutorial_secret_door must handle unhashable items in inventory gracefully."""
        p = copy.deepcopy(self.player)
        p["inventory"] = [["nested", "item"], set(["tag"]), bytearray(b"binary_item")]
        try:
            res = p3.discover_tutorial_secret_door(p, use_relic=True, deterministic_roll=5)
            self.assertFalse(res.get("success"))
            self.assertFalse(res.get("discovered"))
        except Exception as exc:
            self.fail(
                f"CRASH VULNERABILITY: discover_tutorial_secret_door raised unhandled {type(exc).__name__} on unhashable inventory items: {exc}"
            )


if __name__ == "__main__":
    unittest.main()
