"""
test_challenger_m3_v2_it2_empirical.py
======================================
Milestone 3 Iteration 2 Challenger 2 Empirical Adversarial Stress Test Suite.

Adversarially challenges Milestone 3 Iteration 2 Remediations:
1. Telemetry Pillar Idempotency:
   - Call interact_tutorial_telemetry_pillar() 10 times in a row on a single character.
   - Verify that +500 XP and +50 Col are granted strictly ONCE on the first call.
   - Verify that 2nd through 10th calls grant 0 XP, 0 Col, and 0 duplicate dispensed items.
   - Verify that player["tutorial"]["loot_acquired"] does NOT duplicate entries (stays length 2).
   - Verify that inventory item quantities do not multiply upon repeated interactions.
   - Multi-character fuzzing across 5 diverse lineage/lifestyle combinations.

2. Relic Resonance & Secret Door Acoustic/Optical Bypass Restrictions:
   - Verify non-sonic relics (smartphone, zippo_lighter, multitool, first_aid_pouch,
     tactical_flashlight, dogeared_novel, pocket_watch) CANNOT trigger acoustic bypass
     (method == "relic_bypass") in solve_tutorial_puzzle().
   - Verify non-sonic relics with failing deterministic_roll strictly fail (success == False).
   - Verify only genuine sonic relics (tuning_fork, guitar_tuning_fork) achieve acoustic bypass.
   - Verify only optical (polaroid_camera) and acoustic (tuning_fork) relics bypass
     discover_tutorial_secret_door(), and all other relics fall back to the DC 13 Perception
     check, failing on low rolls (roll < 13 - wis_mod).

3. Encumbrance, Durability Wear/Repair & Level 3 Graduation Retention:
   - Encumbrance STR * 15 lbs scaling and Catwalk hazard (> 350.0 lbs threshold).
   - Durability degradation, non-negative clamp, and whetstone field maintenance (+25 cap).
   - Complete 13-room manual progression vs fast-forward progression graduation.
   - Retention of all 8 canonical loot items in inventory via ItemEntry string equality.
   - Crucible Vanguard Signet equipped in accessory slot AND present in inventory.
   - Verification that player["tutorial"]["loot_acquired"] contains all 8 items with no duplicates.
"""

import copy
import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import backend.character_generator as cg
import backend.mechanics as m


CANONICAL_8_LOOT = [
    "Minor Aether-Salve Vial",
    "Calibration Whetstone Kit",
    "Sentinel Brass Armguards",
    "Clockwork Reflex Servo",
    "Inscribed Spell Slate: Astral Bolt",
    "Crucible Vanguard Signet",
    "Condensed Aether-Core",
    "Greater Crimson Draught"
]


class TestTelemetryPillarIdempotency(unittest.TestCase):
    """Stress test telemetry pillar idempotency across repeated invocations."""

    def setUp(self):
        if "tuning_fork" not in cg.PERSONAL_RELICS and "guitar_tuning_fork" in cg.PERSONAL_RELICS:
            cg.PERSONAL_RELICS["tuning_fork"] = cg.PERSONAL_RELICS["guitar_tuning_fork"]

    def test_01_ten_consecutive_telemetry_pillar_interactions(self):
        """Verify calling interact_tutorial_telemetry_pillar() 10 times grants XP/Col once and does not duplicate loot_acquired."""
        player = cg.generate_starting_character(
            name="ValeriaTelemetry",
            point_alloc={"STR": 4, "DEX": 4, "CON": 4, "INT": 4, "WIS": 2, "CHA": 2},
            race_key="pure_human",
            class_key="fighter",
            relic_key="tuning_fork",
            start_tutorial=True
        )
        m.initialize_tutorial_mini_dungeon(player)

        initial_xp = player.get("xp", 0)
        initial_col = player.get("col", 100)

        # First interaction: initial sync
        first_res = m.interact_tutorial_telemetry_pillar(player)
        self.assertTrue(first_res["success"])
        self.assertFalse(first_res["already_synced"])
        self.assertEqual(first_res["xp_gained"], 500)
        self.assertEqual(first_res["col_gained"], 50)
        self.assertEqual(len(first_res["loot_dispensed"]), 2)
        self.assertEqual(player["xp"], initial_xp + 500)
        self.assertEqual(player["col"], initial_col + 50)

        expected_initial_loot = ["Minor Aether-Salve Vial", "Calibration Whetstone Kit"]
        tut_acquired = player.get("tutorial", {}).get("loot_acquired", [])
        self.assertEqual(tut_acquired, expected_initial_loot)
        self.assertEqual(len(tut_acquired), 2)

        # Record inventory snapshot after first sync
        vial_count_1 = sum(
            it.get("qty", 1) if isinstance(it, dict) else 1
            for it in player["inventory"]
            if (it.get("name") if isinstance(it, dict) else str(it)) == "Minor Aether-Salve Vial"
        )
        whetstone_count_1 = sum(
            it.get("qty", 1) if isinstance(it, dict) else 1
            for it in player["inventory"]
            if (it.get("name") if isinstance(it, dict) else str(it)) == "Calibration Whetstone Kit"
        )
        self.assertEqual(vial_count_1, 2)
        self.assertEqual(whetstone_count_1, 1)

        # Interactions 2 through 10: must be 100% idempotent
        for i in range(2, 11):
            res = m.interact_tutorial_telemetry_pillar(player)
            self.assertTrue(res["success"], f"Interaction #{i} failed")
            self.assertTrue(res["already_synced"], f"Interaction #{i} failed to flag already_synced")
            self.assertEqual(res["xp_gained"], 0, f"Interaction #{i} granted non-zero XP: {res['xp_gained']}")
            self.assertEqual(res["col_gained"], 0, f"Interaction #{i} granted non-zero Col: {res['col_gained']}")
            self.assertEqual(len(res["loot_dispensed"]), 0, f"Interaction #{i} dispensed duplicate items: {res['loot_dispensed']}")

            # Invariant: XP and Col must remain unchanged
            self.assertEqual(player["xp"], initial_xp + 500, f"Interaction #{i} altered player XP: {player['xp']}")
            self.assertEqual(player["col"], initial_col + 50, f"Interaction #{i} altered player Col: {player['col']}")

            # Invariant: loot_acquired must NOT grow or duplicate
            current_tut_acquired = player.get("tutorial", {}).get("loot_acquired", [])
            self.assertEqual(
                current_tut_acquired, expected_initial_loot,
                f"Interaction #{i} duplicated or modified tutorial['loot_acquired']: {current_tut_acquired}"
            )
            self.assertEqual(
                len(current_tut_acquired), 2,
                f"Interaction #{i} increased tutorial['loot_acquired'] length: {len(current_tut_acquired)}"
            )

            # Invariant: inventory item quantities must not inflate
            vial_count_i = sum(
                it.get("qty", 1) if isinstance(it, dict) else 1
                for it in player["inventory"]
                if (it.get("name") if isinstance(it, dict) else str(it)) == "Minor Aether-Salve Vial"
            )
            whetstone_count_i = sum(
                it.get("qty", 1) if isinstance(it, dict) else 1
                for it in player["inventory"]
                if (it.get("name") if isinstance(it, dict) else str(it)) == "Calibration Whetstone Kit"
            )
            self.assertEqual(vial_count_i, vial_count_1, f"Interaction #{i} multiplied Minor Aether-Salve Vial qty: {vial_count_i}")
            self.assertEqual(whetstone_count_i, whetstone_count_1, f"Interaction #{i} multiplied Calibration Whetstone Kit qty: {whetstone_count_i}")

    def test_02_multi_character_archetype_telemetry_fuzzing(self):
        """Fuzz telemetry pillar across 5 distinct fantasy lineages and lifestyles, 10 calls each."""
        test_archetypes = [
            ("MinotaurGladiator", "minotaur", "arena_gladiator", "fighter", "pocket_watch"),
            ("PixieMage", "pixie", "archive_scribe", "wizard", "smartphone"),
            ("SatyrBard", "satyr", "courtier_emissary", "bard", "zippo_lighter"),
            ("BugbearRogue", "bugbear", "dungeon_delver", "rogue", "multitool"),
            ("GlennyChimera", "spliced_apex_chimera", "blacksmith_apprentice", "barbarian", "guitar_tuning_fork"),
        ]

        for name, race, lifestyle, cls_key, relic in test_archetypes:
            char = cg.generate_starting_character(
                name=name,
                race_key=race if race in cg.RACIAL_LINEAGES else "pure_human",
                lifestyle_key=lifestyle if lifestyle in cg.PRESET_LIFESTYLES else "desk_bound",
                class_key=cls_key,
                relic_key=relic,
                start_tutorial=True
            )
            m.initialize_tutorial_mini_dungeon(char)

            init_xp = char.get("xp", 0)
            init_col = char.get("col", 100)

            for step in range(1, 11):
                res = m.interact_tutorial_telemetry_pillar(char)
                self.assertTrue(res["success"])
                if step == 1:
                    self.assertFalse(res["already_synced"])
                    self.assertEqual(res["xp_gained"], 500)
                    self.assertEqual(res["col_gained"], 50)
                else:
                    self.assertTrue(res["already_synced"])
                    self.assertEqual(res["xp_gained"], 0)
                    self.assertEqual(res["col_gained"], 0)
                    self.assertEqual(len(res["loot_dispensed"]), 0)

            self.assertEqual(char["xp"], init_xp + 500)
            self.assertEqual(char["col"], init_col + 50)
            self.assertEqual(len(char["tutorial"]["loot_acquired"]), 2)
            self.assertEqual(len(set(char["tutorial"]["loot_acquired"])), 2)


class TestRelicResonanceAcousticOpticalRestrictions(unittest.TestCase):
    """Stress test relic resonance restrictions in Harmonic Puzzle Vault and Concealed Scriptorium."""

    def setUp(self):
        if "tuning_fork" not in cg.PERSONAL_RELICS and "guitar_tuning_fork" in cg.PERSONAL_RELICS:
            cg.PERSONAL_RELICS["tuning_fork"] = cg.PERSONAL_RELICS["guitar_tuning_fork"]

    def _create_player_with_relic(self, relic_key: str, int_stat: int = 10, wis_stat: int = 10) -> dict:
        player = cg.generate_starting_character(
            name=f"RelicTest_{relic_key}",
            point_alloc={"STR": 2, "DEX": 2, "CON": 2, "INT": int_stat - 10, "WIS": wis_stat - 10, "CHA": 2},
            race_key="pure_human",
            class_key="fighter",
            relic_key=relic_key,
            start_tutorial=True
        )
        player["stats"]["INT"] = int_stat
        player["stats"]["WIS"] = wis_stat
        m.initialize_tutorial_mini_dungeon(player)
        return player

    def test_01_non_sonic_relics_cannot_trigger_acoustic_puzzle_bypass(self):
        """Verify non-sonic relics (zippo, smartphone, multitool, etc.) CANNOT trigger acoustic bypass."""
        non_sonic_relics = [
            "smartphone",
            "zippo_lighter",
            "multitool",
            "first_aid_pouch",
            "city_map",
            "pocket_watch",
            "noise_cancelling_headphones",
            "tritium_compass",
            "dogeared_novel",
            "chalk_carabiners",
            "tactical_flashlight",
            "polaroid_camera",
        ]

        for r_key in non_sonic_relics:
            player = self._create_player_with_relic(r_key, int_stat=10)
            self.assertFalse(
                m._is_harmonic_relic_held(player),
                f"Relic '{r_key}' must NOT be classified as harmonic/sonic relic."
            )

            # Test 1: use_relic=True with failing deterministic_roll (e.g. 4 vs DC 12)
            fail_res = m.solve_tutorial_puzzle(player, use_relic=True, deterministic_roll=4)
            self.assertFalse(
                fail_res["success"],
                f"Non-sonic relic '{r_key}' with failing roll falsely succeeded in puzzle: {fail_res}"
            )
            self.assertFalse(fail_res["solved"])
            self.assertFalse(fail_res["lattice_disarmed"])
            self.assertNotEqual(fail_res["method"], "relic_bypass")
            self.assertEqual(fail_res["method"], "failed_skill_check")

            # Test 2: use_relic=True with passing deterministic_roll (e.g. 16 vs DC 12)
            # Should succeed as a skill check, but NEVER as relic_bypass!
            player_pass = self._create_player_with_relic(r_key, int_stat=10)
            pass_res = m.solve_tutorial_puzzle(player_pass, use_relic=True, deterministic_roll=16)
            self.assertTrue(pass_res["success"])
            self.assertTrue(pass_res["solved"])
            self.assertEqual(
                pass_res["method"], "skill_check",
                f"Non-sonic relic '{r_key}' must resolve as 'skill_check', got '{pass_res['method']}'"
            )
            self.assertNotEqual(
                pass_res["method"], "relic_bypass",
                f"Non-sonic relic '{r_key}' falsely triggered 'relic_bypass'!"
            )

    def test_02_genuine_sonic_relic_triggers_acoustic_puzzle_bypass(self):
        """Verify tuning_fork and guitar_tuning_fork reliably trigger relic_bypass regardless of roll."""
        sonic_relics = ["tuning_fork", "guitar_tuning_fork"]

        for r_key in sonic_relics:
            player = self._create_player_with_relic(r_key, int_stat=6)  # Negative INT modifier
            self.assertTrue(
                m._is_harmonic_relic_held(player),
                f"Sonic relic '{r_key}' must be classified as harmonic."
            )

            # Even with deterministic_roll=1 (critical failure if it were a skill check)
            res = m.solve_tutorial_puzzle(player, use_relic=True, deterministic_roll=1)
            self.assertTrue(res["success"])
            self.assertTrue(res["solved"])
            self.assertTrue(res["lattice_disarmed"])
            self.assertEqual(res["method"], "relic_bypass")
            self.assertIn("440 Hz TUNING FORK", " ".join(res["logs"]))

    def test_03_secret_door_discovery_restricted_to_optical_and_acoustic(self):
        """Verify ONLY optical (polaroid_camera) and acoustic (tuning_fork) relics bypass secret door."""
        non_bypassing_relics = [
            "smartphone",
            "zippo_lighter",
            "multitool",
            "first_aid_pouch",
            "city_map",
            "pocket_watch",
            "noise_cancelling_headphones",
            "tritium_compass",
            "dogeared_novel",
            "chalk_carabiners",
            "tactical_flashlight",
        ]

        for r_key in non_bypassing_relics:
            player = self._create_player_with_relic(r_key, wis_stat=10)
            self.assertFalse(m._is_optical_relic_held(player))
            self.assertFalse(m._is_harmonic_relic_held(player))

            # Move to puzzle vault
            player["tutorial_dungeon"]["current_room"] = "phase3_puzzle_vault"
            player["tutorial_dungeon"]["current_phase"] = 3

            # Low roll (e.g. 5 vs DC 13) with use_relic=True MUST fail
            fail_res = m.discover_tutorial_secret_door(player, use_relic=True, deterministic_roll=5)
            self.assertFalse(
                fail_res["success"],
                f"Relic '{r_key}' falsely succeeded on discover_tutorial_secret_door with low roll: {fail_res}"
            )
            self.assertFalse(fail_res["discovered"])
            self.assertEqual(fail_res["method"], "failed_perception")
            self.assertIsNone(fail_res["room_unlocked"])

            # High roll (16 vs DC 13) succeeds via perception_check, NOT relic bypass
            player_high = self._create_player_with_relic(r_key, wis_stat=10)
            player_high["tutorial_dungeon"]["current_room"] = "phase3_puzzle_vault"
            player_high["tutorial_dungeon"]["current_phase"] = 3
            pass_res = m.discover_tutorial_secret_door(player_high, use_relic=True, deterministic_roll=16)
            self.assertTrue(pass_res["success"])
            self.assertTrue(pass_res["discovered"])
            self.assertEqual(pass_res["method"], "perception_check")
            self.assertNotEqual(pass_res["method"], "polaroid_camera")
            self.assertNotEqual(pass_res["method"], "tuning_fork_resonance")

    def test_04_optical_and_acoustic_relic_secret_door_bypass(self):
        """Verify Polaroid Camera and Tuning Fork succeed on secret door even on roll of 1."""
        # 1. Optical Relic: Polaroid Camera
        p_polaroid = self._create_player_with_relic("polaroid_camera", wis_stat=6)
        p_polaroid["tutorial_dungeon"]["current_room"] = "phase3_puzzle_vault"
        p_polaroid["tutorial_dungeon"]["current_phase"] = 3
        self.assertTrue(m._is_optical_relic_held(p_polaroid))

        res_pol = m.discover_tutorial_secret_door(p_polaroid, use_relic=True, deterministic_roll=1)
        self.assertTrue(res_pol["success"])
        self.assertTrue(res_pol["discovered"])
        self.assertEqual(res_pol["method"], "polaroid_camera")
        self.assertEqual(res_pol["room_unlocked"], "phase3_secret_scriptorium")

        # 2. Acoustic Relic: Tuning Fork
        p_tuning = self._create_player_with_relic("tuning_fork", wis_stat=6)
        p_tuning["tutorial_dungeon"]["current_room"] = "phase3_puzzle_vault"
        p_tuning["tutorial_dungeon"]["current_phase"] = 3
        self.assertTrue(m._is_harmonic_relic_held(p_tuning))

        res_tun = m.discover_tutorial_secret_door(p_tuning, use_relic=True, deterministic_roll=1)
        self.assertTrue(res_tun["success"])
        self.assertTrue(res_tun["discovered"])
        self.assertEqual(res_tun["method"], "tuning_fork_resonance")
        self.assertEqual(res_tun["room_unlocked"], "phase3_secret_scriptorium")


class TestEncumbranceDurabilityAndGraduationIntegrity(unittest.TestCase):
    """Stress test encumbrance calculations, durability wear/repair, and Level 3 graduation inventory retention."""

    def setUp(self):
        if "tuning_fork" not in cg.PERSONAL_RELICS and "guitar_tuning_fork" in cg.PERSONAL_RELICS:
            cg.PERSONAL_RELICS["tuning_fork"] = cg.PERSONAL_RELICS["guitar_tuning_fork"]

    def test_01_encumbrance_scaling_and_catwalk_overload(self):
        """Verify STR * 15.0 lbs carry limit scaling and catwalk load threshold (350.0 lbs)."""
        for str_val in [8, 10, 14, 18, 20]:
            player = {
                "name": f"EncTest_STR_{str_val}",
                "race": "pure_human",
                "stats": {"STR": str_val, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
                "physical": {"height_in": 70, "weight_lbs": 160, "age": 25},
                "feats": [],
                "racial_abilities": [],
                "inventory": [],
                "equipped": {}
            }
            enc = m.calculate_encumbrance(player)
            expected_max = round(str_val * 15.0, 1)
            self.assertEqual(enc["max_weight_lbs"], expected_max)

        # Test catwalk hazard
        p_light = cg.generate_starting_character("LightCatwalk", start_tutorial=True)
        p_light["stats"]["STR"] = 10
        m.initialize_tutorial_mini_dungeon(p_light)
        res_safe = m.resolve_tutorial_encumbrance_hazard(p_light, pickup_ballast=False)
        self.assertEqual(res_safe["catwalk_load"]["status"], "SAFE")

        p_heavy = cg.generate_starting_character("HeavyCatwalk", start_tutorial=True)
        p_heavy["stats"]["STR"] = 18
        m.initialize_tutorial_mini_dungeon(p_heavy)
        # Add massive weight to trigger warning
        p_heavy["inventory"].append(m.ItemEntry({"name": "Huge Boulder", "weight_lbs": 200.0, "qty": 1}))
        res_warn = m.resolve_tutorial_encumbrance_hazard(p_heavy, pickup_ballast=True)
        self.assertEqual(res_warn["catwalk_load"]["status"], "WARNING")

    def test_02_durability_wear_and_whetstone_maintenance(self):
        """Verify durability damage degradation, non-negative clamp, and whetstone repair cap."""
        player = cg.generate_starting_character("DurHero", start_tutorial=True)
        gear_dur = player.setdefault("gear_durability", {})
        gear_dur["main_hand"] = {"cur": 60, "max": 60, "state": "Pristine"}

        # Inflict 25 wear damage
        dmg_res1 = m.apply_durability_damage(player, "main_hand", 25)
        self.assertEqual(gear_dur["main_hand"]["cur"], 35)
        self.assertEqual(dmg_res1["state"], "Worn")

        # Repair with whetstone +25
        rep1 = m.repair_gear_durability(player, "main_hand", 25)
        self.assertTrue(rep1["success"])
        self.assertEqual(rep1["cur"], 60)
        self.assertEqual(rep1["state"], "Pristine")

        # Over-repair must cap at max_durability (60)
        rep2 = m.repair_gear_durability(player, "main_hand", 50)
        self.assertEqual(rep2["cur"], 60)

        # Extreme damage must not drop below 0
        dmg_res2 = m.apply_durability_damage(player, "main_hand", 100)
        self.assertEqual(gear_dur["main_hand"]["cur"], 0)
        self.assertEqual(dmg_res2["state"], "Broken")
        self.assertTrue(dmg_res2["is_broken"])

    def test_03_full_manual_progression_all_8_canonical_loot_items(self):
        """Walk full 13-room progression and verify graduation retaining all 8 canonical loot items."""
        player = cg.generate_starting_character(
            name="FullWalkthroughValeria",
            point_alloc={"STR": 4, "DEX": 4, "CON": 4, "INT": 4, "WIS": 2, "CHA": 2},
            race_key="pure_human",
            class_key="fighter",
            relic_key="tuning_fork",
            start_tutorial=True
        )
        m.initialize_tutorial_mini_dungeon(player)

        # Room 1: Telemetry Sanctum
        sync_res = m.interact_tutorial_telemetry_pillar(player)
        self.assertTrue(sync_res["success"])

        # Room 2: Gravity Chasm
        m1 = m.move_tutorial_dungeon_room(player, "phase1_gravity_chasm")
        self.assertTrue(m1["success"])
        m.resolve_tutorial_encumbrance_hazard(player, pickup_ballast=True)

        # Room 3: Rust Mist Adit
        m2 = m.move_tutorial_dungeon_room(player, "phase1_rust_mist_adit")
        self.assertTrue(m2["success"])
        m.resolve_tutorial_durability_hazard(player, wear_damage=15, repair_amount=25)

        # Room 4: Relic Sanctum
        m3 = m.move_tutorial_dungeon_room(player, "phase1_relic_sanctum")
        self.assertTrue(m3["success"])
        m.resolve_tutorial_relic_resonance(player)

        # Room 5: Proving Ground (Phase II)
        m4 = m.move_tutorial_dungeon_room(player, "phase2_proving_ground")
        self.assertTrue(m4["success"])
        m.resolve_tutorial_martial_drill(player)

        # Room 6: Parry Arena
        m5 = m.move_tutorial_dungeon_room(player, "phase2_parry_arena")
        self.assertTrue(m5["success"])
        m.resolve_tutorial_parry_and_charge(player)

        # Room 7: Coordination Annex
        m6 = m.move_tutorial_dungeon_room(player, "phase2_coordination_annex")
        self.assertTrue(m6["success"])
        m.resolve_tutorial_multi_limb_drill(player)

        # Room 8: Triage Infirmary
        m7 = m.move_tutorial_dungeon_room(player, "phase2_triage_infirmary")
        self.assertTrue(m7["success"])
        m.resolve_tutorial_status_triage(player)
        self.assertEqual(player["level"], 2)

        # Room 9: High Ascent (Phase III)
        m8 = m.move_tutorial_dungeon_room(player, "phase3_high_ascent")
        self.assertTrue(m8["success"])

        # Room 10: Puzzle Vault
        m9 = m.move_tutorial_dungeon_room(player, "phase3_puzzle_vault")
        self.assertTrue(m9["success"])
        puz_res = m.solve_tutorial_puzzle(player, dial_inputs=["Sun", "Moon", "Star"])
        self.assertTrue(puz_res["success"])

        # Secret Room 11: Concealed Scriptorium
        sec_res = m.discover_tutorial_secret_door(player, deterministic_roll=16)
        self.assertTrue(sec_res["success"])
        m_sec = m.move_tutorial_dungeon_room(player, "phase3_secret_scriptorium")
        self.assertTrue(m_sec["success"])
        m_back = m.move_tutorial_dungeon_room(player, "phase3_puzzle_vault")
        self.assertTrue(m_back["success"])

        # Room 12: Foundry Hall
        m10 = m.move_tutorial_dungeon_room(player, "phase3_foundry_hall")
        self.assertTrue(m10["success"])
        m.resolve_tutorial_foundry_battle(player)

        # Room 13: Warden Lair
        m11 = m.move_tutorial_dungeon_room(player, "phase3_warden_lair")
        self.assertTrue(m11["success"])
        boss_res = m.resolve_tutorial_warden_boss_battle(player, cast_spell="Astral Bolt")
        self.assertTrue(boss_res["success"])
        self.assertTrue(boss_res["boss_defeated"])

        # Assertions post-graduation
        self.assertEqual(player["level"], 3)
        self.assertEqual(player["location"], "Sector 1 Safe-Zone: Washington Borough, NJ")
        self.assertTrue(player["tutorial"]["completed"])
        self.assertFalse(player["tutorial"]["active"])

        # Verify all 8 canonical loot items
        inv = player["inventory"]
        for item_name in CANONICAL_8_LOOT:
            self.assertIn(
                item_name, inv,
                f"Missing canonical loot item '{item_name}' in player inventory"
            )

        # Crucible Vanguard Signet must be equipped in accessory slot AND in inventory
        self.assertEqual(player["equipped"].get("accessory"), "Crucible Vanguard Signet")
        self.assertIn("Crucible Vanguard Signet", inv)

        # Verify tutorial['loot_acquired'] has all 8 items with no duplicate entries
        loot_acq = player["tutorial"].get("loot_acquired", [])
        for item_name in CANONICAL_8_LOOT:
            self.assertIn(item_name, loot_acq)
        self.assertEqual(
            len(loot_acq), len(set(loot_acq)),
            f"tutorial['loot_acquired'] contains duplicate items: {loot_acq}"
        )

    def test_04_fast_forward_graduation_all_8_canonical_loot_items(self):
        """Fast-forward advance_tutorial_stage(complete_all=True) retains all 8 canonical loot items."""
        player = cg.generate_starting_character(
            name="FastValeria",
            point_alloc={"STR": 4, "DEX": 4, "CON": 4, "INT": 4, "WIS": 2, "CHA": 2},
            race_key="pure_human",
            class_key="wizard",
            relic_key="smartphone",
            start_tutorial=True
        )

        res = m.advance_tutorial_stage(player, complete_all=True)
        self.assertTrue(res["graduated"])
        self.assertEqual(player["level"], 3)
        self.assertEqual(player["location"], "Sector 1 Safe-Zone: Washington Borough, NJ")

        inv = player["inventory"]
        for item_name in CANONICAL_8_LOOT:
            self.assertIn(item_name, inv, f"Fast-forward missing '{item_name}' in inventory")

        self.assertEqual(player["equipped"].get("accessory"), "Crucible Vanguard Signet")
        self.assertIn("Crucible Vanguard Signet", inv)


if __name__ == "__main__":
    unittest.main()
