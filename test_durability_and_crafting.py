"""
test_durability_and_crafting.py
Comprehensive automated test suite for Phase 3 (Phase M3):
Equipment Durability Degradation, Field Crafting, Trap-Rigging, and Field Salvage.
"""

import sys
import os
import copy

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from backend import mechanics

def run_tests():
    total_checks = 0
    passed_checks = 0

    def assert_check(condition, name):
        nonlocal total_checks, passed_checks
        total_checks += 1
        if condition:
            passed_checks += 1
            print(f"  [PASS] {name}")
        else:
            print(f"  [FAIL] {name}")
            raise AssertionError(f"Check failed: {name}")

    print("=" * 65)
    print(" STARTING PHASE M3 VERIFICATION SUITE: DURABILITY & FIELD CRAFTING")
    print("=" * 65)

    # -------------------------------------------------------------
    # TEST 1: ITEM GRADES & DURABILITY NORMALIZATION
    # -------------------------------------------------------------
    print("\n[TEST 1] Verifying Item Grades & Durability Normalization...")
    assert_check(mechanics.get_item_grade("Rusted Iron Sword") == 1, "Rusted Iron Sword is Grade 1")
    assert_check(mechanics.get_item_grade("Reinforced Leather Armor") == 2, "Reinforced Leather is Grade 2")
    assert_check(mechanics.get_item_grade("Aether-Forged Spear") == 3, "Aether-Forged Spear is Grade 3")
    assert_check(mechanics.get_item_grade("Runic Masterwork Crossbow") == 4, "Runic Masterwork is Grade 4")
    assert_check(mechanics.get_item_grade("Fenrir's Tusk (Gr. 5 Axe)") == 5, "Fenrir's Tusk is Grade 5")
    assert_check(mechanics.get_item_grade("Einherjar Rig (Gr. 5 Armor)") == 5, "Einherjar Rig is Grade 5")
    assert_check(mechanics.get_item_grade("Mjölnir-Null (Gr. 5 Trench-Hammer)") == 5, "Mjölnir-Null is Grade 5")

    # Grade scaling table
    assert_check(mechanics.ITEM_GRADE_SCALING[1]["default_durability"] == 50, "Grade 1 default durability == 50")
    assert_check(mechanics.ITEM_GRADE_SCALING[2]["default_durability"] == 75, "Grade 2 default durability == 75")
    assert_check(mechanics.ITEM_GRADE_SCALING[3]["default_durability"] == 100, "Grade 3 default durability == 100")
    assert_check(mechanics.ITEM_GRADE_SCALING[4]["default_durability"] == 150, "Grade 4 default durability == 150")
    assert_check(mechanics.ITEM_GRADE_SCALING[5]["default_durability"] == 200, "Grade 5 default durability == 200")

    # Test normalization on player state
    mock_banki = {
        "name": "Banki",
        "stats": {"STR": 45, "DEX": 35, "CON": 43, "INT": 43, "WIS": 41, "CHA": 31},
        "equipped": {
            "head": "None",
            "chest": "Einherjar Rig (Gr. 5 Armor)",
            "main_hand": "Fenrir's Tusk (Gr. 5 Axe)",
            "off_hand": "Mjölnir-Null (Gr. 5 Trench-Hammer)",
            "accessory": "None"
        },
        "col": 5000,
        "skills": {
            "Field Trapping": {"mastery": 140, "tier": "Journeyman", "description": "Snares and ambush rigging.", "milestones_unlocked": []},
            "Field Smithing": {"mastery": 85, "tier": "Apprentice", "description": "Salvage and repairs.", "milestones_unlocked": []}
        },
        "inventory": [
            "Carbon Line Spools x3",
            "Serrated Tripwire Coils x6",
            "Heavy Highway Snares x12",
            "Crate of Marrow-Jars x8",
            "Anchors and Tension Pins x4",
            "Corroded Micro-Capacitor x2",
            "Frayed Copper Wiring x5"
        ]
    }

    norm_dur = mechanics.normalize_gear_durability(mock_banki)
    assert_check("chest" in norm_dur, "Chest slot registered in gear_durability")
    assert_check(norm_dur["chest"]["max"] == 250, "Einherjar Rig max durability scaled to 250")
    assert_check(norm_dur["chest"]["cur"] == 250, "Einherjar Rig cur durability initialized to 250")
    assert_check(norm_dur["chest"]["grade"] == 5, "Einherjar Rig grade == 5")
    assert_check(norm_dur["main_hand"]["max"] == 200, "Fenrir's Tusk max durability == 200")
    assert_check(norm_dur["off_hand"]["max"] == 200, "Mjölnir-Null max durability == 200")

    # -------------------------------------------------------------
    # TEST 2: DURABILITY DEGRADATION, WEAR STATES & PENALTIES
    # -------------------------------------------------------------
    print("\n[TEST 2] Verifying Durability Wear States & Combat Penalties...")
    # Pristine (>75%)
    s_pristine = mechanics.get_durability_state(190, 200)
    assert_check(s_pristine["state"] == "Pristine", "190/200 is Pristine")
    assert_check(not s_pristine["is_dulled"] and not s_pristine["is_broken"], "Pristine has no penalties")

    # Worn (25% - 74%)
    s_worn = mechanics.get_durability_state(100, 200)
    assert_check(s_worn["state"] == "Worn", "100/200 is Worn")
    assert_check(not s_worn["is_dulled"] and not s_worn["is_broken"], "Worn has no numerical penalties")

    # Dulled/Cracked (1% - 24%)
    s_dulled = mechanics.get_durability_state(30, 200)
    assert_check(s_dulled["state"] == "Dulled/Cracked", "30/200 is Dulled/Cracked")
    assert_check(s_dulled["is_dulled"] and not s_dulled["is_broken"], "Dulled flag is True")
    assert_check(s_dulled["penalty_atk"] == 2 and s_dulled["penalty_ac"] == 2, "Dulled applies 2 penalty")

    # Broken (0%)
    s_broken = mechanics.get_durability_state(0, 200)
    assert_check(s_broken["state"] == "Broken", "0/200 is Broken")
    assert_check(s_broken["is_broken"], "Broken flag is True")

    # Apply durability damage to Banki's weapon
    p1 = copy.deepcopy(mock_banki)
    res_dmg = mechanics.apply_durability_damage(p1, "main_hand", 180)
    assert_check(res_dmg["new_cur"] == 20, "Weapon took 180 damage (200 -> 20)")
    assert_check(res_dmg["is_dulled"], "Weapon crossed into Dulled state")
    assert_check(not res_dmg["is_broken"], "Weapon is not yet broken at 20 dur")

    # Verify penalties calculation
    pens = mechanics.calculate_durability_penalties(p1)
    assert_check(pens["atk_penalty"] == 2, "Dulled main_hand applies -2 attack penalty")
    assert_check(pens["ac_penalty"] == 0, "Chest is pristine so AC penalty is 0")

    # Check calculate_ac with pristine armor
    ac_pristine = mechanics.calculate_ac(p1)
    # Banki: DEX 35 (+12), Einherjar Rig (+8). Encumbrance: Light load (DEX mod +0). AC = 10 + 12 + 8 = 30.
    assert_check(ac_pristine == 30, f"Pristine AC == 30, got {ac_pristine}")

    # Break Banki's chest armor
    res_chest_break = mechanics.apply_durability_damage(p1, "chest", 300)
    assert_check(res_chest_break["new_cur"] == 0, "Chest durability clamped at 0")
    assert_check(res_chest_break["is_broken"], "Chest armor is now BROKEN")

    # Verify AC drops significantly when chest armor breaks (loses +8 bonus and gets -2 penalty)
    pens_broken = mechanics.calculate_durability_penalties(p1)
    assert_check(pens_broken["chest_broken"], "Chest marked broken in penalties dict")
    ac_broken = mechanics.calculate_ac(p1)
    # AC should be 10 + 12 (DEX) + 0 (broken armor) - 2 (penalty) = 20
    assert_check(ac_broken == 20, f"Broken armor AC dropped to 20, got {ac_broken}")

    # -------------------------------------------------------------
    # TEST 3: SAFE ZONE FORGE REPAIRS
    # -------------------------------------------------------------
    print("\n[TEST 3] Verifying Forge Repairs (The Scrap-Yard Anvil)...")
    # Repair main_hand: currently at 20/200, needs 180 repair
    old_col = p1["col"]
    rep_res = mechanics.repair_item(p1, "main_hand", col_per_point=1)
    assert_check(rep_res["success"], "Repair succeeded")
    assert_check(rep_res["repaired"] == 180, "Repaired 180 points")
    assert_check(rep_res["new_durability"] == 200, "Weapon restored to 200 max")
    assert_check(rep_res["col_cost"] == 180, "Cost was 180 Col")
    assert_check(p1["col"] == old_col - 180, f"Col deducted accurately: {p1['col']}")

    # Repair already pristine item
    rep_pristine = mechanics.repair_item(p1, "main_hand")
    assert_check(rep_pristine["success"], "Pristine repair returns success")
    assert_check(rep_pristine["repaired"] == 0, "Zero points repaired on pristine item")
    assert_check(rep_pristine["col_cost"] == 0, "Zero Col cost on pristine item")

    # Repair broken chest
    rep_chest = mechanics.repair_item(p1, "chest", col_per_point=1)
    assert_check(rep_chest["success"], "Broken chest repaired")
    assert_check(p1["gear_durability"]["chest"]["cur"] == 250, "Chest restored to 250")
    # AC should now be restored to full 30
    assert_check(mechanics.calculate_ac(p1) == 30, "AC restored to 30 after forge repair")

    # Test repair with insufficient Col (partial repair)
    p_poor = copy.deepcopy(mock_banki)
    p_poor["col"] = 25
    mechanics.apply_durability_damage(p_poor, "main_hand", 100)
    rep_poor = mechanics.repair_item(p_poor, "main_hand", col_per_point=1)
    assert_check(rep_poor["success"], "Partial repair succeeded with low Col")
    assert_check(rep_poor["repaired"] == 25, "Repaired exactly 25 points with 25 Col")
    assert_check(p_poor["col"] == 0, "Col reduced to 0")

    # -------------------------------------------------------------
    # TEST 4: FIELD TRAP CRAFTING & MATERIAL CONSUMPTION
    # -------------------------------------------------------------
    print("\n[TEST 4] Verifying Field Trap Crafting & Material Consumption...")
    p_trap = copy.deepcopy(mock_banki)

    # All 4 canonical traps registered
    assert_check("serrated_tripwire" in mechanics.CANONICAL_TRAPS, "Serrated Tripwire registered")
    assert_check("heavy_highway_snare" in mechanics.CANONICAL_TRAPS, "Heavy Highway Snare registered")
    assert_check("marrow_aggro_corridor" in mechanics.CANONICAL_TRAPS, "Marrow Aggro Corridor registered")
    assert_check("emp_shock_mine" in mechanics.CANONICAL_TRAPS, "EMP Shock-Mine registered")

    # Banki has materials for all 4 traps
    can_trip, _, _ = mechanics.can_craft_trap(p_trap, "serrated_tripwire")
    can_snare, _, _ = mechanics.can_craft_trap(p_trap, "heavy_highway_snare")
    can_marrow, _, _ = mechanics.can_craft_trap(p_trap, "marrow_aggro_corridor")
    can_emp, _, _ = mechanics.can_craft_trap(p_trap, "emp_shock_mine")

    assert_check(can_trip, "Can craft Serrated Tripwire")
    assert_check(can_snare, "Can craft Heavy Highway Snare")
    assert_check(can_marrow, "Can craft Marrow Aggro Corridor")
    assert_check(can_emp, "Can craft EMP Shock-Mine")

    # Rig Serrated Tripwire
    initial_wire = 6
    initial_pins = 4
    rig_res = mechanics.rig_field_trap(p_trap, "serrated_tripwire", d20_roll=15)
    assert_check(rig_res["success"], "Tripwire rigging successful")
    assert_check(len(p_trap.get("active_traps", [])) == 1, "Active trap added to active_traps list")
    
    # Check that materials decremented
    item_wire, _ = mechanics._find_inventory_item(p_trap["inventory"], "Serrated Tripwire Coils")
    item_pins, _ = mechanics._find_inventory_item(p_trap["inventory"], "Anchors and Tension Pins")
    assert_check("x5" in item_wire, f"Tripwire coils decremented to 5: {item_wire}")
    assert_check("x3" in item_pins, f"Tension pins decremented to 3: {item_pins}")

    # Check Stealth DC calculation: Base DC 12, roll 15 + DEX mod 12 + Field Trapping Mastery bonus 1 = 28 vs DC 12 -> Stealth DC = 10 + 12 + 1 + 16 = 39
    assert_check(rig_res["stealth_dc"] >= 20, f"High stealth DC generated: {rig_res['stealth_dc']}")

    # Check Field Trapping mastery gained
    new_trap_mastery = p_trap["skills"]["Field Trapping"]["mastery"]
    assert_check(new_trap_mastery > 140, f"Field Trapping mastery increased: {new_trap_mastery}")

    # Test missing materials handling
    p_empty = copy.deepcopy(mock_banki)
    p_empty["inventory"] = []
    can_fail, msg_fail, _ = mechanics.can_craft_trap(p_empty, "serrated_tripwire")
    assert_check(not can_fail, "Cannot craft without materials")
    assert_check("Missing materials" in msg_fail, "Informative missing materials message")

    # -------------------------------------------------------------
    # TEST 5: TRAP TRIGGERING & AMBUSH RESOLUTION
    # -------------------------------------------------------------
    print("\n[TEST 5] Verifying Trap Triggering & Ambush Status...")
    # Spring the deployed tripwire against a monster with low perception (12)
    spring_res = mechanics.trigger_field_trap(p_trap, 0, target_name="Glitch-Hound Alpha", target_passive_perception=12)
    assert_check(spring_res["triggered"], "Trap triggered successfully")
    assert_check(spring_res["ambushed"], "Surprise ambush achieved against low perception")
    assert_check(spring_res["trap"]["condition"] == "Bleed & Prone", "Inflicts Bleed & Prone condition")
    assert_check(len(p_trap["active_traps"]) == 0, "Trap consumed from active_traps")

    # -------------------------------------------------------------
    # TEST 6: FIELD SCAVENGING & SALVAGE
    # -------------------------------------------------------------
    print("\n[TEST 6] Verifying Field Salvage & Scavenging...")
    p_salv = copy.deepcopy(mock_banki)
    initial_copper, _ = mechanics._find_inventory_item(p_salv["inventory"], "Frayed Copper Wiring")
    
    # High roll salvage on construct
    salv_res = mechanics.salvage_materials(p_salv, target_type="cyber_construct", d20_roll=18)
    assert_check(salv_res["success"], "Salvage succeeded")
    assert_check(len(salv_res["items"]) >= 2, "Harvested 2 items on roll 18")

    # Verify inventory updated
    new_copper, _ = mechanics._find_inventory_item(p_salv["inventory"], "Frayed Copper Wiring")
    assert_check("x7" in new_copper, f"Copper wiring increased from x5 to x7: {new_copper}")

    # Verify Field Smithing mastery gained
    new_smith_mastery = p_salv["skills"]["Field Smithing"]["mastery"]
    assert_check(new_smith_mastery > 85, f"Field Smithing mastery increased: {new_smith_mastery}")

    # Beast salvage
    salv_beast = mechanics.salvage_materials(p_salv, target_type="mutated_chimera", d20_roll=16)
    assert_check(salv_beast["success"], "Chimera salvage succeeded")
    marrow_item, _ = mechanics._find_inventory_item(p_salv["inventory"], "Rendered Chimera Marrow")
    assert_check(marrow_item is not None, "Rendered Chimera Marrow added to inventory")

    print("\n" + "=" * 65)
    print(f" ALL {passed_checks}/{total_checks} CHECKS PASSED SUCCESSFULLY (100% PASS RATE)!")
    print("=" * 65)
    return True

if __name__ == "__main__":
    run_tests()
