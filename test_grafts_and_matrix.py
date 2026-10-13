"""
test_grafts_and_matrix.py
Comprehensive automated test suite for Phase 4: Golem-Grafts & Ability Slotting Matrix.
Verifies all mechanical calculations, strain limits, rejection penalties, ability slots,
body slot constraints, and AC calculations.
"""

import sys
import copy
from backend import mechanics

def run_tests():
    total_checks = 0
    passed_checks = 0

    def assert_check(condition, test_name):
        nonlocal total_checks, passed_checks
        total_checks += 1
        if condition:
            passed_checks += 1
            print(f"  [PASS] {test_name}")
        else:
            print(f"  [FAIL] {test_name}")
            raise AssertionError(f"Check failed: {test_name}")

    print("======================================================================")
    print("RUNNING PHASE 4 TEST SUITE: GOLEM-GRAFTS & ABILITY MATRIX")
    print("======================================================================\n")

    # ------------------------------------------------------------------
    # 1. CANONICAL GRAFTS & BODY SLOTS
    # ------------------------------------------------------------------
    print("--- SECTION 1: CANONICAL GRAFTS & BODY SLOTS ---")
    canonical_keys = [
        "golem_hydraulic_arm",
        "aether_resonant_ocular",
        "subdermal_carapace_weave",
        "spring_loaded_golem_greaves",
        "neural_overclock_cortex",
        "leyline_conduit_spine"
    ]
    for k in canonical_keys:
        assert_check(k in mechanics.CANONICAL_GRAFTS, f"Canonical graft exists: {k}")
        g = mechanics.CANONICAL_GRAFTS[k]
        assert_check(g.get("strain", 0) > 0, f"Graft {k} has positive strain ({g.get('strain')})")
        assert_check("allowed_slots" in g and len(g["allowed_slots"]) > 0, f"Graft {k} has allowed slots defined")
        for slot_cand in g["allowed_slots"]:
            assert_check(slot_cand in mechanics.BODY_GRAFT_SLOTS, f"Graft {k} slot '{slot_cand}' is in BODY_GRAFT_SLOTS")
        assert_check(g.get("col_cost", 0) > 0, f"Graft {k} has positive Col cost ({g.get('col_cost')})")

    # Verify all 8 distinct body slots
    expected_slots = {"arm_left", "arm_right", "leg_left", "leg_right", "spine", "ocular", "dermal", "neural"}
    for s in mechanics.BODY_GRAFT_SLOTS:
        assert_check(s in expected_slots, f"Body slot '{s}' is recognized")

    # ------------------------------------------------------------------
    # 2. MAX STRAIN CALCULATION
    # Formula: (CON * 2) + (Level * 3)
    # ------------------------------------------------------------------
    print("\n--- SECTION 2: MAX STRAIN CALCULATION ---")
    mock_player = {
        "name": "Banki",
        "level": 1,
        "stats": {"STR": 35, "DEX": 20, "CON": 40, "INT": 15, "WIS": 15, "CHA": 10},
        "col": 5000,
        "hp": 200,
        "max_hp": 200
    }
    # CON = 40, Level = 1 -> (40 * 2) + (1 * 3) = 83
    expected_strain_lv1 = (40 * 2) + (1 * 3)
    assert_check(mechanics.get_max_graft_strain(mock_player) == expected_strain_lv1,
                 f"Max strain at Lv 1 (CON 40) is {expected_strain_lv1}")

    # Level 10, CON 40 -> (40 * 2) + (10 * 3) = 110
    mock_player["level"] = 10
    expected_strain_lv10 = (40 * 2) + (10 * 3)
    assert_check(mechanics.get_max_graft_strain(mock_player) == expected_strain_lv10,
                 f"Max strain at Lv 10 (CON 40) is {expected_strain_lv10}")

    # Low CON player: CON 10, Level 2 -> (10 * 2) + (2 * 3) = 26
    low_con_player = {"level": 2, "stats": {"CON": 10}}
    assert_check(mechanics.get_max_graft_strain(low_con_player) == 26, "Max strain for CON 10 Lv 2 is 26")

    # Fallback when stats missing
    empty_player = {}
    assert_check(mechanics.get_max_graft_strain(empty_player) == (10 * 2) + (1 * 3), "Default max strain fallback handles empty state")

    # ------------------------------------------------------------------
    # 3. GRAFT INSTALLATION & SURGICAL COL COSTS
    # ------------------------------------------------------------------
    print("\n--- SECTION 3: GRAFT INSTALLATION & SURGICAL COSTS ---")
    p1 = copy.deepcopy(mock_player)
    p1["level"] = 1
    p1["col"] = 5000

    # Install Hydraulic Arm in arm_left (cost: 2500 + 200 fee = 2700)
    res_arm = mechanics.install_graft(p1, "golem_hydraulic_arm", "arm_left", surgeon_fee_col=200)
    assert_check(res_arm["success"] is True, "Hydraulic arm installed successfully")
    assert_check(p1["col"] == 5000 - 200, f"Col deducted accurately (Remaining: {p1['col']})")
    assert_check(mechanics.get_current_graft_strain(p1) == 15, "Current strain increased to 15")

    # Try to install in wrong body slot (e.g. Ocular in arm_right)
    res_wrong_slot = mechanics.install_graft(p1, "aether_resonant_ocular", "arm_right")
    assert_check(res_wrong_slot["success"] is False, "Rejects graft install in incorrect body slot")

    # Try to install when unaffordable
    p1["col"] = 50
    res_broke = mechanics.install_graft(p1, "subdermal_carapace_weave", "dermal")
    assert_check(res_broke["success"] is False, "Rejects graft install when Col is insufficient")

    # Install Carapace Weave with sufficient Col (cost: 3500)
    p1["col"] = 6000
    res_weave = mechanics.install_graft(p1, "subdermal_carapace_weave", "dermal", surgeon_fee_col=0)
    assert_check(res_weave["success"] is True, "Subdermal carapace installed successfully")
    assert_check(mechanics.get_current_graft_strain(p1) == 15 + 20, "Strain accumulated: 15 + 20 = 35")

    # ------------------------------------------------------------------
    # 4. SYSTEM REJECTION & STRAIN OVERFLOW
    # ------------------------------------------------------------------
    print("\n--- SECTION 4: SYSTEM REJECTION & RECOIL ---")
    # p1 max strain is 83, current is 35. Should be Stable.
    rej_normal = mechanics.get_graft_rejection_status(p1)
    assert_check(rej_normal["is_rejecting"] is False, "35/83 strain is within safe capacity")
    assert_check(rej_normal["hp_drain"] == 0, "No HP drain when stable")

    # Overload a fragile character
    fragile_player = {
        "level": 1,
        "stats": {"CON": 10}, # Max strain: (10*2) + (1*3) = 23
        "col": 10000,
        "hp": 50,
        "max_hp": 50
    }
    # Install arm (15 strain)
    mechanics.install_graft(fragile_player, "golem_hydraulic_arm", "arm_left", surgeon_fee_col=0)
    # Install carapace (20 strain) -> Total 35 strain vs max 23 -> Overflow = 12
    mechanics.install_graft(fragile_player, "subdermal_carapace_weave", "dermal", surgeon_fee_col=0)
    
    rej_overflow = mechanics.get_graft_rejection_status(fragile_player)
    assert_check(rej_overflow["is_rejecting"] is True, "Overflow triggers System Rejection")
    # fragile_player CON became 11 (+1 from carapace), so max strain is (11*2)+(1*3) = 25. Strain = 35. Overflow = 10.
    assert_check(rej_overflow["overflow"] == 10, f"Overflow amount is exactly 10 (Observed: {rej_overflow['overflow']})")
    assert_check(rej_overflow["hp_drain"] == 10 * 2, f"HP drain equals overflow * 2 ({20} HP)")
    assert_check(rej_overflow["save_penalty"] == 2, "Saving throw penalty is 2")

    # ------------------------------------------------------------------
    # 5. GRAFT EXTRACTION / REMOVAL
    # ------------------------------------------------------------------
    print("\n--- SECTION 5: GRAFT EXTRACTION ---")
    rem_res = mechanics.remove_graft(fragile_player, "dermal")
    assert_check(rem_res["success"] is True, "Carapace weave removed successfully")
    assert_check(fragile_player["stats"]["CON"] == 10, "CON reverted back to 10 upon graft removal")
    assert_check(mechanics.get_current_graft_strain(fragile_player) == 15, "Strain reduced back to 15")
    assert_check("salvaged_item" in rem_res, "Surgical extraction creates salvaged core in inventory")
    rej_healed = mechanics.get_graft_rejection_status(fragile_player)
    assert_check(rej_healed["is_rejecting"] is False, "System Rejection clears once strain is within limit")

    # Remove non-existent graft
    rem_missing = mechanics.remove_graft(fragile_player, "leg_left")
    assert_check(rem_missing["success"] is False, "Gracefully handles extracting unequipped graft slot")

    # ------------------------------------------------------------------
    # 6. ARMOR CLASS INTEGRATION (SUBDERMAL CARAPACE WEAVE)
    # ------------------------------------------------------------------
    print("\n--- SECTION 6: AC INTEGRATION ---")
    p_ac_base = {
        "stats": {"DEX": 20, "CON": 40},
        "equipped": {"chest": "Black-Iron Chainmail Hauberk", "shield": "Reinforced Shield"},
        "gear_durability": {},
        "feats": []
    }
    enc = mechanics.calculate_encumbrance(p_ac_base)
    base_ac = mechanics.calculate_ac(p_ac_base, enc)

    # Now install Subdermal Carapace Weave (+2 AC)
    p_ac_grafted = copy.deepcopy(p_ac_base)
    mechanics.install_graft(p_ac_grafted, "subdermal_carapace_weave", "dermal", surgeon_fee_col=0)
    grafted_ac = mechanics.calculate_ac(p_ac_grafted, enc)
    assert_check(grafted_ac == base_ac + 2, f"Subdermal Carapace Weave grants +2 AC (Base: {base_ac} -> Grafted: {grafted_ac})")

    # ------------------------------------------------------------------
    # 7. SPELLCASTER GRAFT INTERFERENCE & HARMONIZATION FEATS
    # ------------------------------------------------------------------
    print("\n--- SECTION 7: SPELLCASTER INTERFERENCE & HARMONIZATION ---")
    mage_player = {
        "class": "Mage",
        "level": 3,
        "stats": {"INT": 30, "CON": 20},
        "feats": []
    }
    # Install 2 grafts: Arm (cybernetic) and Ocular (cybernetic)
    mechanics.install_graft(mage_player, "golem_hydraulic_arm", "arm_left", surgeon_fee_col=0)
    mechanics.install_graft(mage_player, "aether_resonant_ocular", "ocular", surgeon_fee_col=0)

    # Without harmonization, unharmonized cybernetics impose -2 DC per unharmonized graft (2 grafts = -4 DC)
    pen_unharm = mechanics.calculate_spellcasting_graft_penalty(mage_player)
    assert_check(pen_unharm["penalty"] == 4, f"Unharmonized mage suffers -4 spellcasting penalty (Observed: {pen_unharm['penalty']})")
    assert_check(pen_unharm["harmonized"] == 0, "Harmonized count is 0 without feat")

    # Add Harmonization Feat 'Leyline Conduits' (harmonizes 1 graft -> 1 unharmonized left -> -2 penalty)
    mage_player["feats"].append("Leyline Conduits")
    pen_harm1 = mechanics.calculate_spellcasting_graft_penalty(mage_player)
    assert_check(pen_harm1["penalty"] == 2, f"Spellcaster penalty drops to -2 with 'Leyline Conduits' feat (Observed: {pen_harm1['penalty']})")
    assert_check(pen_harm1["harmonized"] == 1, "Harmonized count is 1")

    # Install 'Leyline Conduit Spine' (harmonizes 2 grafts -> 1 + 2 = 3 harmonized >= 2 total -> 0 penalty)
    mechanics.install_graft(mage_player, "leyline_conduit_spine", "spine", surgeon_fee_col=0)
    pen_harm2 = mechanics.calculate_spellcasting_graft_penalty(mage_player)
    assert_check(pen_harm2["penalty"] == 0, f"Penalty drops to 0 with spinal conduit + feat (Observed: {pen_harm2['penalty']})")

    # Non-spellcaster suffers 0 penalty regardless
    warrior_player = {"class": "Warrior", "feats": []}
    mechanics.install_graft(warrior_player, "golem_hydraulic_arm", "arm_left", surgeon_fee_col=0)
    assert_check(mechanics.calculate_spellcasting_graft_penalty(warrior_player)["penalty"] == 0, "Warrior suffers 0 arcane graft penalty")

    # ------------------------------------------------------------------
    # 8. ABILITY SLOTTING MATRIX MEMORY CAPS & NEURAL OVERCLOCK
    # ------------------------------------------------------------------
    print("\n--- SECTION 8: ABILITY SLOTTING MATRIX CAPS ---")
    p_matrix = {"level": 5}
    assert_check(mechanics.get_max_ability_slots(p_matrix) == 5, "Level 5 character has base 5 active ability slots")

    p_matrix["level"] = 11
    assert_check(mechanics.get_max_ability_slots(p_matrix) == 10, "Level 11 character has base 10 active ability slots")

    # Install Neural Overclock Cortex (+1 active slot)
    mechanics.install_graft(p_matrix, "neural_overclock_cortex", "neural", surgeon_fee_col=0)
    assert_check(mechanics.get_max_ability_slots(p_matrix) == 11, "Level 11 with Neural Overclock Cortex has 11 active slots (10 + 1)")

    p_matrix["level"] = 1
    assert_check(mechanics.get_max_ability_slots(p_matrix) == 6, "Level 1 with Neural Overclock Cortex has 6 active slots (5 + 1)")

    # ------------------------------------------------------------------
    # 9. ABILITY SLOTTING, UNSLOTTING & RESTRICTIONS
    # ------------------------------------------------------------------
    print("\n--- SECTION 9: SLOTTING & UNSLOTTING MECHANICS ---")
    p_slot = {
        "level": 1,
        "spells": ["Aetheric Dart", "Arcane Ward"],
        "feats": ["Shield Wall Stance (Active)", "Unyielding Mass (Passive)"],
        "racial_abilities": ["Telekinetic Grip (Active)"]
    }
    # Max slots = 5
    assert_check(len(mechanics.get_slotted_abilities(p_slot)) == 0, "Initial slotted abilities is empty")

    # Slot 1: Aetheric Dart
    res_s1 = mechanics.slot_ability(p_slot, "Aetheric Dart")
    assert_check(res_s1["success"] is True, "Successfully slotted Aetheric Dart")
    assert_check(mechanics.is_ability_slotted(p_slot, "Aetheric Dart") is True, "is_ability_slotted confirms Aetheric Dart")

    # Slot duplicate: should reject
    res_s_dup = mechanics.slot_ability(p_slot, "Aetheric Dart")
    assert_check(res_s_dup["success"] is False, "Rejects duplicate slotting of same ability")

    # Slot 2, 3, 4, 5
    mechanics.slot_ability(p_slot, "Arcane Ward")
    mechanics.slot_ability(p_slot, "Shield Wall Stance")
    mechanics.slot_ability(p_slot, "Telekinetic Grip")
    mechanics.slot_ability(p_slot, "Cleave Strike")

    assert_check(len(mechanics.get_slotted_abilities(p_slot)) == 5, "Matrix holds exactly 5 slotted abilities")

    # Try slotting 6th when max is 5
    res_overflow = mechanics.slot_ability(p_slot, "Extra Ability")
    assert_check(res_overflow["success"] is False, "Rejects slotting when active memory is full (5/5)")

    # Unslot an ability
    res_unslot = mechanics.unslot_ability(p_slot, "Shield Wall Stance")
    assert_check(res_unslot["success"] is True, "Successfully unslotted Shield Wall Stance")
    assert_check(mechanics.is_ability_slotted(p_slot, "Shield Wall Stance") is False, "Shield Wall Stance no longer slotted")
    assert_check(len(mechanics.get_slotted_abilities(p_slot)) == 4, "Active slots count dropped to 4")

    # Unslot non-slotted ability
    res_unslot_ghost = mechanics.unslot_ability(p_slot, "Ghost Skill")
    assert_check(res_unslot_ghost["success"] is False, "Gracefully rejects unslotting unslotted ability")

    # Available abilities aggregation
    avail = mechanics.get_available_abilities(p_slot)
    avail_names = [a["name"] for a in avail]
    assert_check("Aetheric Dart" in avail_names, "Available pool includes spell 'Aetheric Dart'")
    assert_check("Telekinetic Grip" in avail_names, "Available pool includes racial power 'Telekinetic Grip'")
    assert_check("Shield Wall Stance" in avail_names, "Available pool includes active feat 'Shield Wall Stance'")
    assert_check("Unyielding Mass" not in avail_names, "Available pool excludes passive feat 'Unyielding Mass'")

    # ------------------------------------------------------------------
    # 10. BACKWARDS COMPATIBILITY WITH SAVE PROFILES
    # ------------------------------------------------------------------
    print("\n--- SECTION 10: BACKWARDS COMPATIBILITY ---")
    legacy_profile = {
        "name": "OldHero",
        "level": 4,
        "stats": {"STR": 14, "DEX": 12, "CON": 16, "INT": 10, "WIS": 10, "CHA": 10},
        "hp": 50,
        "max_hp": 50,
        "inventory": []
    }
    # No graft_system or slotted_abilities keys
    assert_check(mechanics.get_current_graft_strain(legacy_profile) == 0, "Legacy profile returns 0 graft strain")
    assert_check(mechanics.get_max_graft_strain(legacy_profile) == (16 * 2) + (4 * 3), "Legacy profile computes max strain correctly")
    assert_check(mechanics.get_graft_rejection_status(legacy_profile)["is_rejecting"] is False, "Legacy profile is not in rejection")
    assert_check(mechanics.get_max_ability_slots(legacy_profile) == 5, "Legacy profile defaults to 5 slots")
    assert_check(mechanics.get_slotted_abilities(legacy_profile) == [], "Legacy profile returns empty slotted list")

    print("\n======================================================================")
    print(f"PHASE 4 TEST SUITE COMPLETE: {passed_checks}/{total_checks} CHECKS PASSED (100%)")
    print("======================================================================")

if __name__ == "__main__":
    run_tests()
