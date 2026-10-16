"""
test_challenger_m3_v2_2_empirical.py
====================================
Milestone 3 Challenger 2 Empirical Adversarial Property-Based Stress Test Suite.

Adversarially challenges Milestone 3:
1. Physical Encumbrance Limits:
   - Property-based fuzzing of STR scores from 3 to 30 across multiple racial sizes and carry multipliers
     (Pixie carry_mult=0.5, Medium human carry_mult=1.0, Large minotaur carry_mult=2.0).
   - Invariant: max_weight_lbs == round(STR * 15.0 * carry_mult, 1) [for baseline lineages].
   - Boundary load transitions: Unencumbered (<=50%), Light Load (50-75%), Heavy Load (75-100%, -2 DEX), Overencumbered (>100%, -5 DEX).
   - Catwalk failure testing on overload in both resolve_tutorial_encumbrance_hazard (load > 350.0 lbs -> WARNING)
     and evaluate_party_environmental_physics fragile floor mechanics (load >= 800.0 lbs -> collapse hazard triggered).

2. Durability Wear & Whetstone Repair Cycles:
   - Property-based fuzzing of durability wear damage from 1 to 100 on equipment.
   - Non-negative invariant: current durability never drops below 0.
   - Wear state transitions and labels across all percentage thresholds:
     Pristine (>=75%), Worn (25%-74%), Dulled/Cracked (1%-24%), Broken (0%).
   - Whetstone honing cap invariant: current durability never exceeds maximum durability (cur <= max).
   - Multi-cycle wear/honing stress tests verifying stability across 50 continuous cycles.

3. Multi-Limb Combat Drills:
   - 2-armed vs 4-armed (Glenny chimera) loadout differentiation.
   - Quad-flurry limb attacks across all 4 hand slots (main_hand, off_hand, lower_main_hand, lower_off_hand).
   - Validation that 2-armed loadouts execute dual-wield drills across 2 hand slots.
   - Total combo damage invariant == sum of individual limb attack damage values.

4. Canonical Loot Integrity:
   - Manual graduation walk-through vs Fast-forward (advance_tutorial_stage complete_all=True) graduation.
   - Verification that all 8 canonical loot items are present in player inventory.
   - Verification that "Minor Aether-Salve Vial" in player["inventory"] evaluates to True via ItemEntry.__eq__.
   - Verification that "Crucible Vanguard Signet" is BOTH equipped in player["equipped"]["accessory"] AND present in player["inventory"].
   - ItemEntry dictionary subclass semantics, JSON serializability, and hash support.
"""

import copy
import json
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


class TestPhysicalEncumbranceAndCatwalkOverload(unittest.TestCase):
    """
    Challenge Dimension 1: Physical Encumbrance Limits & Catwalk Overload.
    Verifies STR 3..30 fuzzing, carry multiplier scaling, load tiers, and catwalk failure modes.
    """

    def setUp(self):
        if "tuning_fork" not in cg.PERSONAL_RELICS and "guitar_tuning_fork" in cg.PERSONAL_RELICS:
            cg.PERSONAL_RELICS["tuning_fork"] = cg.PERSONAL_RELICS["guitar_tuning_fork"]

    def test_01_fuzz_str_scores_carry_multiplier(self):
        """Fuzz STR scores from 3 to 30 verifying max_weight_lbs == round(STR * 15.0 * carry_mult, 1)."""
        # Test configurations: (race_key, height_in, expected_mult)
        test_profiles = [
            ("pure_human", 70, 1.0, "Medium Humanoid"),
            ("pixie", 24, 0.5, "Tiny Pixie"),
            ("half_ogre", 96, 2.0, "Large Savage Species"),
        ]

        for race_key, height, expected_mult, label in test_profiles:
            for str_score in range(3, 31):
                mock_player = {
                    "name": f"FuzzSTR_{race_key}_{str_score}",
                    "race": race_key,
                    "stats": {
                        "STR": str_score, "DEX": 10, "CON": 10,
                        "INT": 10, "WIS": 10, "CHA": 10
                    },
                    "physical": {
                        "height_in": height, "weight_lbs": 150, "age": 25, "gender": "Non-binary"
                    },
                    "feats": [],
                    "racial_abilities": [],
                    "inventory": [],
                    "equipped": {}
                }

                # Clear race bonus capacities if testing strictly baseline multiplier scaling
                phys = m.get_physical_profile(mock_player)
                self.assertAlmostEqual(
                    phys["modifiers"]["carry_mult"], expected_mult, places=2,
                    msg=f"{label} must have carry_mult={expected_mult}, got {phys['modifiers']['carry_mult']}"
                )

                enc = m.calculate_encumbrance(mock_player)
                # Compute expected carry limit
                bonus = 0.0
                if "half-ogre" in race_key:
                    # Half-Ogre has +100 bonus capacity in mechanics.py
                    bonus = 100.0
                expected_max = round((str_score * 15.0 + bonus) * expected_mult, 1)

                self.assertEqual(
                    enc["max_weight_lbs"], expected_max,
                    f"STR {str_score} on {label}: expected max_weight_lbs {expected_max}, got {enc['max_weight_lbs']}"
                )

                # Verify slot capacity invariant: 10 + (STR // 2)
                expected_slots = 10 + (str_score // 2)
                self.assertEqual(
                    enc["max_slots"], expected_slots,
                    f"STR {str_score} must yield {expected_slots} slots, got {enc['max_slots']}"
                )

    def test_02_pure_baseline_str_multiplier_invariant(self):
        """Directly verify pure baseline: max_weight_lbs == STR * 15.0 * carry_mult for pure human."""
        for str_val in range(3, 31):
            player = {
                "name": "StandardTest",
                "race": "pure_human",
                "stats": {"STR": str_val, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
                "physical": {"height_in": 70, "weight_lbs": 170, "age": 28},
                "feats": [],
                "racial_abilities": [],
                "inventory": [],
                "equipped": {}
            }
            enc = m.calculate_encumbrance(player)
            expected = round(str_val * 15.0 * 1.0, 1)
            self.assertEqual(enc["max_weight_lbs"], expected)

    def test_03_encumbrance_tier_transitions_and_penalties(self):
        """Stress-test exact weight boundaries for encumbrance tiers and stat penalties."""
        str_val = 14  # Max carry: 210.0 lbs
        player = {
            "name": "TierHero",
            "race": "pure_human",
            "stats": {"STR": str_val, "DEX": 14, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
            "physical": {"height_in": 70, "weight_lbs": 170, "age": 25},
            "feats": [],
            "racial_abilities": [],
            "inventory": [],
            "equipped": {}
        }
        max_w = 14 * 15.0  # 210.0 lbs

        # Case A: Exactly 50.0% -> Unencumbered
        player["inventory"] = [{"name": "Lead Bar", "weight": max_w * 0.50, "qty": 1}]
        enc_50 = m.calculate_encumbrance(player)
        self.assertEqual(enc_50["tier"], "Unencumbered")
        self.assertEqual(enc_50["penalties"]["dex_mod"], 0)
        self.assertEqual(enc_50["penalties"]["speed_pct"], 100)

        # Case B: 50.0% + 0.1 lb -> Light Load
        player["inventory"] = [{"name": "Lead Bar", "weight": round(max_w * 0.50 + 0.1, 1), "qty": 1}]
        enc_light = m.calculate_encumbrance(player)
        self.assertEqual(enc_light["tier"], "Light Load")
        self.assertEqual(enc_light["penalties"]["dex_mod"], 0)

        # Case C: Exactly 75.0% -> Light Load
        player["inventory"] = [{"name": "Lead Bar", "weight": round(max_w * 0.75, 1), "qty": 1}]
        enc_75 = m.calculate_encumbrance(player)
        self.assertEqual(enc_75["tier"], "Light Load")

        # Case D: 75.0% + 0.1 lb -> Heavy Load (-2 DEX, 85% speed, disadvantage stealth)
        player["inventory"] = [{"name": "Lead Bar", "weight": round(max_w * 0.75 + 0.1, 1), "qty": 1}]
        enc_heavy = m.calculate_encumbrance(player)
        self.assertEqual(enc_heavy["tier"], "Heavy Load")
        self.assertEqual(enc_heavy["penalties"]["dex_mod"], -2)
        self.assertEqual(enc_heavy["penalties"]["speed_pct"], 85)
        self.assertTrue(enc_heavy["penalties"]["disadvantage_stealth"])

        # Case E: Exactly 100.0% -> Heavy Load
        player["inventory"] = [{"name": "Lead Bar", "weight": max_w, "qty": 1}]
        enc_100 = m.calculate_encumbrance(player)
        self.assertEqual(enc_100["tier"], "Heavy Load")

        # Case F: 100.0% + 0.1 lb -> Overencumbered (-5 DEX, 50% speed, disadvantage stealth)
        player["inventory"] = [{"name": "Lead Bar", "weight": round(max_w + 0.1, 1), "qty": 1}]
        enc_over = m.calculate_encumbrance(player)
        self.assertEqual(enc_over["tier"], "Overencumbered")
        self.assertEqual(enc_over["penalties"]["dex_mod"], -5)
        self.assertEqual(enc_over["penalties"]["speed_pct"], 50)
        self.assertTrue(enc_over["penalties"]["disadvantage_stealth"])

    def test_04_catwalk_overload_tutorial_hazard(self):
        """Verify catwalk status toggles between SAFE and WARNING when total load exceeds 350.0 lbs."""
        player = cg.generate_starting_character("CatwalkTest", start_tutorial=True)
        m.initialize_tutorial_mini_dungeon(player)

        # 1. Normal state: total load <= 350 lbs -> SAFE
        res_safe = m.resolve_tutorial_encumbrance_hazard(player, pickup_ballast=False, test_catwalk=True)
        self.assertTrue(res_safe["success"])
        self.assertEqual(res_safe["catwalk_load"]["status"], "SAFE")
        self.assertLessEqual(res_safe["catwalk_load"]["total_weight_lbs"], 350.0)

        # 2. Overloaded state: inject heavy ballast into inventory so total load > 350.0 lbs
        player["inventory"].append({"name": "Superdense Iron Golem Slab", "weight": 250.0, "qty": 1})
        res_warn = m.resolve_tutorial_encumbrance_hazard(player, pickup_ballast=False, test_catwalk=True)
        self.assertTrue(res_warn["success"])
        self.assertEqual(res_warn["catwalk_load"]["status"], "WARNING")
        self.assertGreater(res_warn["catwalk_load"]["total_weight_lbs"], 350.0)
        self.assertIn("WARNING", res_warn["message"])

    def test_05_catwalk_fragile_floor_environmental_collapse_hazard(self):
        """Verify evaluate_party_environmental_physics triggers catwalk collapse warning upon overload."""
        env_catwalk = {
            "location": "Suspended Ballast Catwalks",
            "description": "Magnetized iron girders and suspended ballast catwalk over deep chasm.",
            "environmental_effects": []
        }

        # 1. Normal load (< 800 lbs) -> No collapse hazard
        light_player = {
            "name": "LightScout",
            "race": "pure_human",
            "stats": {"STR": 10, "DEX": 14, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10},
            "physical": {"height_in": 68, "weight_lbs": 150.0, "age": 22},
            "inventory": [],
            "equipped": {},
            "companions": {}
        }
        light_res = m.evaluate_party_environmental_physics(light_player, dict(env_catwalk))
        self.assertFalse(light_res["hazard_triggered"])

        # 2. Player own weight + gear overloaded (>= 800 lbs, e.g. Minotaur carrying heavy load)
        heavy_player = {
            "name": "HugeGoliath",
            "race": "minotaur",
            "stats": {"STR": 20, "DEX": 10, "CON": 16, "INT": 8, "WIS": 10, "CHA": 8},
            "physical": {"height_in": 96, "weight_lbs": 550.0, "age": 30},
            "inventory": [{"name": "Boulder", "weight": 300.0, "qty": 1}],
            "equipped": {},
            "companions": {}
        }
        heavy_res = m.evaluate_party_environmental_physics(heavy_player, dict(env_catwalk))
        self.assertTrue(heavy_res["hazard_triggered"])
        self.assertTrue(any("CRITICAL FLOOR LOAD WARNING" in ef for ef in heavy_res["effects"]))
        self.assertTrue(any("catwalk tolerance" in ef for ef in heavy_res["effects"]))

        # 3. Companion overload (Titus Sterling 1200-lb cast-iron chassis)
        party_player = copy.deepcopy(light_player)
        m.ensure_party_system(party_player)
        party_player["companions"]["Titus"]["recruited"] = True
        party_player["companions"]["Titus"]["active"] = True
        party_res = m.evaluate_party_environmental_physics(party_player, dict(env_catwalk))
        self.assertTrue(party_res["hazard_triggered"])
        self.assertTrue(party_res["titus_present"])
        self.assertTrue(any("Titus Sterling (1,200-lb chassis)" in ef for ef in party_res["effects"]))


class TestDurabilityWearAndWhetstoneRepairCycles(unittest.TestCase):
    """
    Challenge Dimension 2: Durability Wear & Whetstone Repair Cycles.
    Fuzzes durability damage from 1 to 100, checking wear state labels, clamping, and whetstone honing caps.
    """

    def setUp(self):
        self.player = cg.generate_starting_character("DurabilityTester", start_tutorial=True)

    def test_01_fuzz_durability_damage_1_to_100(self):
        """Fuzz durability damage from 1 to 100, verifying non-negative cur, states, and wear labels."""
        for max_d in [50, 60, 100]:
            for dmg in range(1, 101):
                self.player["gear_durability"] = {
                    "main_hand": {"cur": max_d, "max": max_d, "state": "Pristine"}
                }
                res = m.apply_durability_damage(self.player, "main_hand", amount=dmg)

                expected_cur = max(0, max_d - dmg)
                self.assertEqual(
                    res["new_cur"], expected_cur,
                    f"Max {max_d}, Damage {dmg}: expected cur {expected_cur}, got {res['new_cur']}"
                )
                self.assertGreaterEqual(res["new_cur"], 0, "Durability must never be negative")
                self.assertLessEqual(res["new_cur"], max_d, "Durability must never exceed max")

                # Verify state label invariants
                pct = expected_cur / float(max_d)
                if expected_cur == 0:
                    self.assertEqual(res["state"], "Broken")
                    self.assertTrue(res["is_broken"])
                    self.assertIn("BROKEN", res["log"])
                elif pct < 0.25:
                    self.assertEqual(res["state"], "Dulled/Cracked")
                    self.assertFalse(res["is_broken"])
                    self.assertTrue(res["is_dulled"])
                    self.assertIn("Dulled/Cracked", res["log"])
                elif pct < 0.75:
                    self.assertEqual(res["state"], "Worn")
                    self.assertFalse(res["is_broken"])
                    self.assertFalse(res["is_dulled"])
                    self.assertIn("Worn", res["log"])
                else:
                    self.assertEqual(res["state"], "Pristine")
                    self.assertFalse(res["is_broken"])
                    self.assertFalse(res["is_dulled"])
                    self.assertIn("Pristine", res["log"])

    def test_02_whetstone_honing_cap_invariant(self):
        """Verify whetstone repairs strictly cap at maximum durability without overflowing."""
        max_durability = 60
        for initial_cur in range(0, max_durability + 1, 5):
            for repair_amount in [10, 25, 50, 100]:
                self.player["gear_durability"] = {
                    "main_hand": {"cur": initial_cur, "max": max_durability, "state": "Worn"}
                }
                rep = m.repair_gear_durability(self.player, "main_hand", amount=repair_amount)

                expected_new = min(max_durability, initial_cur + repair_amount)
                expected_restored = expected_new - initial_cur

                self.assertTrue(rep["success"])
                self.assertEqual(rep["cur"], expected_new)
                self.assertEqual(rep["amount_restored"], expected_restored)
                self.assertLessEqual(rep["cur"], max_durability, "Honing must never exceed max durability!")

        # Over-cap check: pristine weapon at max durability restored by +25 restores 0
        self.player["gear_durability"]["main_hand"] = {"cur": 60, "max": 60, "state": "Pristine"}
        rep_full = m.repair_gear_durability(self.player, "main_hand", amount=25)
        self.assertEqual(rep_full["cur"], 60)
        self.assertEqual(rep_full["amount_restored"], 0)

    def test_03_continuous_wear_repair_stress_cycles(self):
        """Stress-test 50 alternating wear-damage and whetstone-repair cycles."""
        self.player["gear_durability"] = {"main_hand": {"cur": 60, "max": 60, "state": "Pristine"}}

        # Pseudo-random sequence of wear and repairs
        test_sequence = [(15, 25), (40, 25), (60, 25), (10, 25), (35, 50), (100, 25)] * 8

        for step, (wear, hone) in enumerate(test_sequence):
            cur_before = self.player["gear_durability"]["main_hand"]["cur"]
            # Apply wear
            res_wear = m.apply_durability_damage(self.player, "main_hand", amount=wear)
            after_wear = res_wear["new_cur"]
            self.assertEqual(after_wear, max(0, cur_before - wear))
            self.assertGreaterEqual(after_wear, 0)

            # Apply hone
            res_hone = m.repair_gear_durability(self.player, "main_hand", amount=hone)
            after_hone = res_hone["cur"]
            self.assertEqual(after_hone, min(60, after_wear + hone))
            self.assertLessEqual(after_hone, 60)

    def test_04_tutorial_durability_hazard_fuzzing(self):
        """Fuzz resolve_tutorial_durability_hazard() across wear damages 1..100."""
        for dmg in range(1, 101):
            self.player["gear_durability"] = {"main_hand": {"cur": 60, "max": 60, "state": "Pristine"}}
            res = m.resolve_tutorial_durability_hazard(self.player, target_slot="main_hand", wear_damage=dmg, repair_amount=25)

            self.assertTrue(res["success"])
            expected_degraded = max(0, 60 - dmg)
            expected_repaired = min(60, expected_degraded + 25)

            self.assertEqual(res["degraded_durability"], expected_degraded)
            self.assertEqual(res["repaired_durability"], expected_repaired)
            self.assertLessEqual(res["repaired_durability"], 60)
            self.assertTrue(self.player["tutorial_dungeon"]["phase_1_drills"]["durability_checked"])


class TestMultiLimbCombatDrills(unittest.TestCase):
    """
    Challenge Dimension 3: Multi-Limb Combat Drills.
    Verifies 2-armed dual-wielding vs 4-armed (Glenny chimera) quad-flurries across all 4 hand slots.
    """

    def test_01_two_armed_dual_wield_drill(self):
        """Verify 2-armed character executes dual_wield drill with exactly 2 limb attacks."""
        human = cg.generate_starting_character("StandardHuman", race_key="pure_human", start_tutorial=True)
        m.initialize_tutorial_mini_dungeon(human)

        anat = m.get_limb_anatomy_profile(human)
        self.assertEqual(anat["arm_count"], 2)
        self.assertFalse(anat["is_four_armed"])
        self.assertEqual(anat["hand_slot_keys"], ["main_hand", "off_hand"])

        drill_res = m.resolve_tutorial_multi_limb_drill(human)
        self.assertTrue(drill_res["success"])
        self.assertEqual(drill_res["drill_mode"], "dual_wield")
        self.assertFalse(drill_res["is_four_armed"])
        self.assertEqual(drill_res["arm_count"], 2)

        attacks = drill_res["limb_attacks"]
        self.assertEqual(len(attacks), 2)
        slots_attacked = [a["slot"] for a in attacks]
        self.assertEqual(slots_attacked, ["main_hand", "off_hand"])

        expected_total = sum(a["damage"] for a in attacks)
        self.assertEqual(drill_res["total_combo_damage"], expected_total)
        self.assertTrue(human["tutorial_dungeon"]["phase_2_drills"]["multi_limb_coordinated"])

    def test_02_four_armed_glenny_chimera_quad_flurry(self):
        """Verify 4-armed Glenny chimera executes quad_flurry across all 4 hand slots."""
        glenny = cg.generate_starting_character("Glenny", start_tutorial=True)
        m.initialize_tutorial_mini_dungeon(glenny)

        anat = m.get_limb_anatomy_profile(glenny)
        self.assertEqual(anat["arm_count"], 4)
        self.assertTrue(anat["is_four_armed"])
        self.assertEqual(
            set(anat["hand_slot_keys"]),
            {"main_hand", "off_hand", "lower_main_hand", "lower_off_hand"}
        )

        drill_res = m.resolve_tutorial_multi_limb_drill(glenny)
        self.assertTrue(drill_res["success"])
        self.assertEqual(drill_res["drill_mode"], "quad_flurry")
        self.assertTrue(drill_res["is_four_armed"])
        self.assertEqual(drill_res["arm_count"], 4)

        attacks = drill_res["limb_attacks"]
        self.assertEqual(len(attacks), 4, f"Expected 4 limb attacks for quad flurry, got {len(attacks)}")

        slots_attacked = [a["slot"] for a in attacks]
        expected_slots = ["main_hand", "off_hand", "lower_main_hand", "lower_off_hand"]
        self.assertEqual(
            slots_attacked, expected_slots,
            f"Quad flurry must attack across all 4 hand slots: {expected_slots}, got {slots_attacked}"
        )

        # Verify all attacks have non-empty weapon descriptions and positive damage
        for atk in attacks:
            self.assertGreater(atk["damage"], 0)
            self.assertTrue(atk["weapon"])

        expected_total = sum(a["damage"] for a in attacks)
        self.assertEqual(drill_res["total_combo_damage"], expected_total)
        self.assertTrue(glenny["tutorial_dungeon"]["phase_2_drills"]["multi_limb_coordinated"])

    def test_03_four_armed_lineage_archetypes_fuzzing(self):
        """Verify multiple 4-armed lineage variants consistently trigger quad_flurry."""
        test_races = ["troll_kreen_chimera", "thrikreen_mantis", "troll_kreen_juggernaut", "thri_troll_stalker"]
        for r_key in test_races:
            p = cg.generate_starting_character(f"FourArmed_{r_key}", race_key=r_key, start_tutorial=False)
            anat = m.get_limb_anatomy_profile(p)
            self.assertTrue(
                anat["is_four_armed"],
                f"Lineage {r_key} must evaluate to is_four_armed=True"
            )
            res = m.resolve_tutorial_multi_limb_drill(p)
            self.assertEqual(res["drill_mode"], "quad_flurry")
            self.assertEqual(len(res["limb_attacks"]), 4)
            slots = [a["slot"] for a in res["limb_attacks"]]
            self.assertEqual(slots, ["main_hand", "off_hand", "lower_main_hand", "lower_off_hand"])

    def test_04_auxiliary_servo_arm_isolation(self):
        """Verify a 2-armed character with 1 auxiliary servo-arm graft does NOT falsely claim 4-armed quad-flurry."""
        cyborg = {
            "name": "AuxArmWarrior",
            "race": "pure_human",
            "stats": {"STR": 14, "DEX": 12, "CON": 12, "INT": 10, "WIS": 10, "CHA": 10},
            "feats": [],
            "racial_abilities": [],
            "grafts": {"torso": "Auxiliary Hydraulic Servo-Arm"},
            "inventory": [],
            "equipped": {}
        }
        anat = m.get_limb_anatomy_profile(cyborg)
        self.assertTrue(anat["has_graft_extra_arm"])
        self.assertFalse(anat["is_four_armed"])
        self.assertEqual(anat["arm_count"], 3)

        res = m.resolve_tutorial_multi_limb_drill(cyborg)
        self.assertEqual(res["drill_mode"], "dual_wield")
        self.assertEqual(len(res["limb_attacks"]), 2)


class TestCanonicalLootIntegrity(unittest.TestCase):
    """
    Challenge Dimension 4: Canonical Loot Integrity & ItemEntry Membership.
    Tests manual graduation and fast-forward graduation, verifying all 8 items,
    'Minor Aether-Salve Vial' in player['inventory'] via ItemEntry, and Signet equipped + in inventory.
    """

    def setUp(self):
        if "tuning_fork" not in cg.PERSONAL_RELICS and "guitar_tuning_fork" in cg.PERSONAL_RELICS:
            cg.PERSONAL_RELICS["tuning_fork"] = cg.PERSONAL_RELICS["guitar_tuning_fork"]

    def _verify_graduation_integrity(self, player, mode_label):
        """Helper to exhaustively assert all graduation criteria and canonical loot invariants."""
        # 1. Level & Safe-Zone Location
        self.assertEqual(player["level"], 3, f"[{mode_label}] Player must graduate at Level 3, got {player.get('level')}")
        self.assertEqual(
            player["location"],
            "Sector 1 Safe-Zone: Washington Borough, NJ",
            f"[{mode_label}] Player must be at Washington Borough, NJ, got {player.get('location')}"
        )

        # 2. Tutorial completion state
        self.assertTrue(player["tutorial"]["completed"], f"[{mode_label}] tutorial.completed must be True")
        self.assertFalse(player["tutorial"]["active"], f"[{mode_label}] tutorial.active must be False")

        # 3. All 8 canonical loot items present in inventory via ItemEntry string containment
        inv = player["inventory"]
        for expected_item in CANONICAL_8_LOOT:
            # String containment test via ItemEntry.__eq__
            self.assertIn(
                expected_item, inv,
                f"[{mode_label}] Missing canonical loot '{expected_item}' in player['inventory']"
            )

        # 4. Specific mandatory assertion: 'Minor Aether-Salve Vial' in player['inventory']
        self.assertTrue(
            "Minor Aether-Salve Vial" in player["inventory"],
            f"[{mode_label}] 'Minor Aether-Salve Vial' in player['inventory'] must evaluate to True"
        )

        # 5. Specific mandatory assertion: Crucible Vanguard Signet is BOTH equipped AND in inventory
        self.assertEqual(
            player["equipped"].get("accessory"),
            "Crucible Vanguard Signet",
            f"[{mode_label}] Crucible Vanguard Signet must be equipped in player['equipped']['accessory']"
        )
        self.assertTrue(
            "Crucible Vanguard Signet" in player["inventory"],
            f"[{mode_label}] Crucible Vanguard Signet must be preserved in player['inventory']"
        )

    def test_01_manual_graduation_canonical_loot(self):
        """Walk full 13-room manual progression to Crucible Warden defeat and assert all 8 canonical loot items."""
        player = cg.generate_starting_character(
            name="ManualValeria",
            point_alloc={"STR": 4, "DEX": 4, "CON": 4, "INT": 4, "WIS": 2, "CHA": 2},
            race_key="pure_human",
            class_key="fighter",
            relic_key="tuning_fork",
            start_tutorial=True
        )
        m.initialize_tutorial_mini_dungeon(player)

        # Phase I manual drills
        m.move_tutorial_dungeon_room(player, "phase1_gravity_chasm")
        m.resolve_tutorial_encumbrance_hazard(player, pickup_ballast=True)
        m.move_tutorial_dungeon_room(player, "phase1_rust_mist_adit")
        m.resolve_tutorial_durability_hazard(player, wear_damage=15, repair_amount=25)
        m.move_tutorial_dungeon_room(player, "phase1_resonant_reliquary")
        m.resolve_tutorial_relic_resonance(player)

        # Phase II manual drills
        m.move_tutorial_dungeon_room(player, "phase2_proving_ground")
        m.resolve_tutorial_martial_drill(player)
        m.move_tutorial_dungeon_room(player, "phase2_buffer_alcove")
        m.resolve_tutorial_parry_and_charge(player)
        m.move_tutorial_dungeon_room(player, "phase2_coordination_annex")
        m.resolve_tutorial_multi_limb_drill(player)
        m.move_tutorial_dungeon_room(player, "phase2_sentinel_sanctum")
        m.resolve_tutorial_status_triage(player)

        # Phase III manual drills
        m.move_tutorial_dungeon_room(player, "phase3_puzzle_vault")
        m.solve_tutorial_puzzle(player, dial_inputs=["Sun", "Moon", "Star"])
        m.discover_tutorial_secret_door(player, deterministic_roll=16)
        m.move_tutorial_dungeon_room(player, "phase3_foundry")
        m.resolve_tutorial_foundry_battle(player)
        m.move_tutorial_dungeon_room(player, "phase3_warden_lair")
        m.resolve_tutorial_warden_boss_battle(player, cast_spell="Astral Bolt")

        # Exhaustive verification
        self._verify_graduation_integrity(player, "Manual Walkthrough")

    def test_02_fast_forward_complete_all_canonical_loot(self):
        """Fast-forward graduation via advance_tutorial_stage(complete_all=True) and assert all 8 canonical loot items."""
        player = cg.generate_starting_character(
            name="FastHero",
            point_alloc={"STR": 4, "DEX": 4, "CON": 4, "INT": 4, "WIS": 2, "CHA": 2},
            race_key="pure_human",
            class_key="wizard",
            relic_key="tuning_fork",
            start_tutorial=True
        )

        res = m.advance_tutorial_stage(player, complete_all=True)
        self.assertTrue(res["graduated"])
        self.assertEqual(res["level"], 3)

        # Exhaustive verification
        self._verify_graduation_integrity(player, "Fast-Forward complete_all=True")

    def test_03_stage_by_stage_sequential_advance(self):
        """Advance stages 1 -> 2 -> 3 one by one and verify incremental loot acquisition and final graduation."""
        player = cg.generate_starting_character("SequentialHero", start_tutorial=True)

        # Stage 1
        st1 = m.advance_tutorial_stage(player)
        self.assertEqual(st1["completed_stage"], 1)
        self.assertEqual(st1["new_stage"], 2)
        self.assertIn("Minor Aether-Salve Vial", player["inventory"])
        self.assertIn("Calibration Whetstone Kit", player["inventory"])

        # Stage 2
        st2 = m.advance_tutorial_stage(player)
        self.assertEqual(st2["completed_stage"], 2)
        self.assertEqual(st2["new_stage"], 3)
        self.assertEqual(player["level"], 2)
        self.assertIn("Sentinel Brass Armguards", player["inventory"])
        self.assertIn("Clockwork Reflex Servo", player["inventory"])
        self.assertIn("Inscribed Spell Slate: Astral Bolt", player["inventory"])
        self.assertEqual(player["attuned_spell"], "Astral Bolt")

        # Stage 3
        st3 = m.advance_tutorial_stage(player)
        self.assertEqual(st3["completed_stage"], 3)
        self.assertTrue(st3["graduated"])

        # Exhaustive verification
        self._verify_graduation_integrity(player, "Sequential Stage-by-Stage")

    def test_04_item_entry_properties_and_dictionary_parity(self):
        """Verify ItemEntry maintains 100% dictionary semantics, case-insensitive string equality, and JSON serialization."""
        raw_dict = {
            "name": "Minor Aether-Salve Vial",
            "rarity": "Common",
            "category": "Consumable",
            "qty": 2,
            "weight_lbs": 0.5,
            "desc": "Restores 35 HP."
        }
        entry = m.ItemEntry(raw_dict)

        # 1. Subclass and dict instance check
        self.assertIsInstance(entry, dict)
        self.assertIsInstance(entry, m.ItemEntry)

        # 2. String equality (exact and case-insensitive)
        self.assertEqual(entry, "Minor Aether-Salve Vial")
        self.assertEqual(entry, "minor aether-salve vial")
        self.assertEqual(entry, "MINOR AETHER-SALVE VIAL")

        # 3. Standard dict equality with another dict
        self.assertEqual(entry, raw_dict)

        # 4. Standard dict mutation and access
        entry["qty"] += 1
        self.assertEqual(entry["qty"], 3)
        self.assertEqual(entry.get("rarity"), "Common")

        # 5. Membership testing in collections
        test_inv = [entry, {"name": "Regular Dictionary Item"}]
        self.assertIn("Minor Aether-Salve Vial", test_inv)
        self.assertIn("minor aether-salve vial", test_inv)

        # 6. JSON serialization without custom encoder
        serialized = json.dumps(test_inv)
        self.assertIn("Minor Aether-Salve Vial", serialized)
        deserialized = json.loads(serialized)
        self.assertEqual(deserialized[0]["name"], "Minor Aether-Salve Vial")


if __name__ == "__main__":
    unittest.main()
