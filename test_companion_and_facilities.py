"""
Unit & Playtesting Suite for Phase M5:
Autonomous Companion Progression & Tactical Orders (Ren Engine) & Safe Zone Facilities in Washington Borough
"""

import sys
import copy
import backend.mechanics as mechanics

def run_tests():
    total_checks = 0
    passed_checks = 0

    def check(name, condition, error_detail=""):
        nonlocal total_checks, passed_checks
        total_checks += 1
        if condition:
            passed_checks += 1
            print(f"  [PASS] {name}")
        else:
            print(f"  [FAIL] {name} - Detail: {error_detail}")

    print("======================================================================")
    print("RUNNING PHASE M5 TEST SUITE: COMPANION & SAFE ZONE FACILITIES")
    print("======================================================================")

    # ------------------------------------------------------------------
    # Test 1: Companion Default Profile & Initialization
    # ------------------------------------------------------------------
    print("\n[Suite 1: Companion Initialization & Schema Integrity]")
    default_ren = mechanics.get_default_ren_companion()
    check("Default Ren has name 'Ren Sasaki'", default_ren["name"] == "Ren Sasaki")
    check("Default Ren has Level 3", default_ren["level"] == 3)
    check("Default Ren has 35 HP & Max HP", default_ren["hp"] == 35 and default_ren["max_hp"] == 35)
    check("Default Ren has 450 XP and 900 next_level_xp", default_ren["xp"] == 450 and default_ren["next_level_xp"] == 900)
    check("Default Ren stance is 'overwatch_hacking'", default_ren["stance"] == "overwatch_hacking")
    check("Default Ren morale is 'Steady'", default_ren["morale"] == "Steady")
    check("Default Ren has core skills", "Mesh Exploitation" in default_ren["skills"] and "Diagnostic Triage" in default_ren["skills"])
    check("Default Ren has starter equipment", default_ren["equipped"]["main_hand"] != "" and default_ren["equipped"]["deck"] != "")

    # Test ensure_companion_profile on raw player dict
    raw_player = {"name": "TestSubject", "hp": 100, "col": 1000}
    comps = mechanics.ensure_companion_profile(raw_player)
    check("ensure_companion_profile populates 'companions' dict", "companions" in raw_player)
    check("Ren is populated in raw player", "Ren" in raw_player["companions"])
    check("get_companion retrieves Ren", mechanics.get_companion(raw_player, "Ren")["name"] == "Ren Sasaki")

    # Test upgrade of legacy companion profile
    legacy_player = {
        "companions": {
            "Ren": {
                "name": "Ren",
                "hp": 40,
                "status": "Exhausted"
            }
        }
    }
    upgraded = mechanics.ensure_companion_profile(legacy_player)
    ren_up = upgraded["Ren"]
    check("Legacy Ren preserves existing HP", ren_up["hp"] == 40)
    check("Legacy Ren receives level default", ren_up["level"] == 3)
    check("Legacy Ren receives stance default", ren_up["stance"] == "overwatch_hacking")
    check("Legacy Ren receives skills dict", isinstance(ren_up["skills"], dict))

    # ------------------------------------------------------------------
    # Test 2: Tactical Stances & Transitions
    # ------------------------------------------------------------------
    print("\n[Suite 2: Tactical Stances & Transitions]")
    test_player = {"name": "Banki", "col": 5000, "hp": 100, "max_hp": 100}
    mechanics.ensure_companion_profile(test_player)

    # 4 Canonical Stances
    s1 = mechanics.set_companion_stance(test_player, "suppression_fire", "Ren")
    check("Transition to suppression_fire succeeds", s1["success"] and s1["stance"] == "suppression_fire")
    check("Player state updated to suppression_fire", test_player["companions"]["Ren"]["stance"] == "suppression_fire")

    s2 = mechanics.set_companion_stance(test_player, "full_evasion", "Ren")
    check("Transition to full_evasion succeeds", s2["success"] and s2["stance"] == "full_evasion")

    s3 = mechanics.set_companion_stance(test_player, "utility_rigging", "Ren")
    check("Transition to utility_rigging succeeds", s3["success"] and s3["stance"] == "utility_rigging")

    s4 = mechanics.set_companion_stance(test_player, "overwatch_hacking", "Ren")
    check("Transition to overwatch_hacking succeeds", s4["success"] and s4["stance"] == "overwatch_hacking")

    # Normalization tests (fuzzy / display labels / aliases)
    s_norm1 = mechanics.set_companion_stance(test_player, "⚡ Suppression Fire (Stun)", "Ren")
    check("Fuzzy stance 'Suppression Fire' normalizes to suppression_fire", s_norm1["success"] and s_norm1["stance"] == "suppression_fire")

    s_norm2 = mechanics.set_companion_stance(test_player, "🛡️ Full Evasion / Cover", "Ren")
    check("Fuzzy stance 'Full Evasion' normalizes to full_evasion", s_norm2["success"] and s_norm2["stance"] == "full_evasion")

    s_norm3 = mechanics.set_companion_stance(test_player, "🔧 Utility & Field Rigging", "Ren")
    check("Fuzzy stance 'Utility Rigging' normalizes to utility_rigging", s_norm3["success"] and s_norm3["stance"] == "utility_rigging")

    s_norm4 = mechanics.set_companion_stance(test_player, "overwatch", "Ren")
    check("Alias 'overwatch' normalizes to overwatch_hacking", s_norm4["success"] and s_norm4["stance"] == "overwatch_hacking")

    s_bad = mechanics.set_companion_stance(test_player, "invalid_berserk_stance", "Ren")
    check("Invalid stance is rejected", not s_bad["success"])

    # ------------------------------------------------------------------
    # Test 3: Deterministic Companion Combat Actions
    # ------------------------------------------------------------------
    print("\n[Suite 3: Deterministic Companion Combat Actions]")
    
    # Overwatch Hacking: -2 AC debuff
    mechanics.set_companion_stance(test_player, "overwatch_hacking", "Ren")
    act_ow = mechanics.get_companion_combat_action(test_player, "Ren")
    check("Overwatch provides -2 target AC modifier", act_ow.get("target_ac_mod") == -2)
    check("Overwatch combat log contains tag", "[REN OVERWATCH]" in act_ow.get("log", ""))

    # Suppression Fire: DC 13 Stagger
    mechanics.set_companion_stance(test_player, "suppression_fire", "Ren")
    act_sup = mechanics.get_companion_combat_action(test_player, "Ren")
    check("Suppression Fire triggers DC 13 check", act_sup.get("dc") == 13 and act_sup.get("condition") == "Staggered")
    check("Suppression Fire combat log contains tag", "[REN SUPPRESSION]" in act_sup.get("log", ""))

    # Full Evasion: Untargetable
    mechanics.set_companion_stance(test_player, "full_evasion", "Ren")
    act_eva = mechanics.get_companion_combat_action(test_player, "Ren")
    check("Full Evasion flags untargetable", act_eva.get("untargetable") is True)
    check("Full Evasion combat log contains tag", "[REN EVASION]" in act_eva.get("log", ""))

    # Utility Rigging: Gear patch
    test_player["gear_durability"] = {
        "chest": {"item": "Einherjar Rig", "current_durability": 150, "max_durability": 250}
    }
    mechanics.set_companion_stance(test_player, "utility_rigging", "Ren")
    act_ut = mechanics.get_companion_combat_action(test_player, "Ren")
    check("Utility Rigging patches damaged gear", act_ut.get("patched") is True)
    check("Durability restored by +15 (now 165)", test_player["gear_durability"]["chest"]["current_durability"] == 165)
    check("Utility combat log contains tag", "[REN UTILITY]" in act_ut.get("log", ""))

    # ------------------------------------------------------------------
    # Test 4: Companion XP Progression & Level Scaling
    # ------------------------------------------------------------------
    print("\n[Suite 4: Companion XP Progression & Level Scaling]")
    comp_p = {
        "name": "Banki",
        "companions": {
            "Ren": {
                "name": "Ren Sasaki",
                "level": 1,
                "xp": 0,
                "next_level_xp": 300,
                "hp": 35,
                "max_hp": 35,
                "stance": "overwatch_hacking",
                "morale": "Steady",
                "abilities": [],
                "skills": {
                    "Mesh Exploitation": {"mastery": 20, "tier": "Novice", "description": "", "milestones_unlocked": []}
                }
            }
        }
    }
    mechanics.ensure_companion_profile(comp_p)

    # Next level formula
    check("Level 1 req XP is 300", mechanics.calculate_companion_next_level_xp(1) == 300)
    check("Level 2 req XP is 600", mechanics.calculate_companion_next_level_xp(2) == 600)
    check("Level 3 req XP is 900", mechanics.calculate_companion_next_level_xp(3) == 900)

    # Award 100 XP (no level up)
    res_xp1 = mechanics.award_companion_xp(comp_p, "Ren", 100)
    comp_ref = mechanics.get_companion(comp_p, "Ren")
    check("Award 100 XP updates current XP to 100", comp_ref["xp"] == 100)
    check("Level remains 1", comp_ref["level"] == 1 and not res_xp1["leveled_up"])

    # Swapped argument support: award_companion_xp(comp_p, 250, "Ren")
    res_xp2 = mechanics.award_companion_xp(comp_p, 250, "Ren")
    check("Crossing 300 XP (now 350) triggers level up", res_xp2["leveled_up"] and res_xp2["new_level"] == 2)
    check("Ren Max HP increased by +8 (35 -> 43)", comp_ref["max_hp"] == 43 and comp_ref["hp"] == 43)
    check("Ren next_level_xp updated to 600", comp_ref["next_level_xp"] == 600)
    check("Level 2 Perk 'Telemetry Ping v1.0' unlocked", any("Telemetry Ping v1.0" in a for a in comp_ref["abilities"]))
    check("Ren core skill Mesh Exploitation advanced", comp_ref["skills"]["Mesh Exploitation"]["mastery"] > 20)

    # Level up to Level 3 (needs 600 XP, currently 350 -> add 300 more = 650)
    res_xp3 = mechanics.award_companion_xp(comp_p, "Ren", 300)
    check("Ren reaches Level 3", comp_ref["level"] == 3)
    check("Ren Max HP increased by +8 (43 -> 51)", comp_ref["max_hp"] == 51)
    check("Level 3 Perk 'Mesh Exploitation' unlocked", any("Mesh Exploitation" in a for a in comp_ref["abilities"]))

    # Level up to Level 6 (massive XP jump)
    res_xp_big = mechanics.award_companion_xp(comp_p, "Ren", 2500)
    check("Ren advances to Level >= 6", comp_ref["level"] >= 6)
    check("Level 4 Perk 'Aetheric Shield Pulse' unlocked", any("Aetheric Shield Pulse" in a for a in comp_ref["abilities"]))
    check("Level 5 Perk 'Overclocked Stun Burst' unlocked", any("Overclocked Stun Burst" in a for a in comp_ref["abilities"]))
    check("Level 6 Perk 'Geometry Desync Hack' unlocked", any("Geometry Desync Hack" in a for a in comp_ref["abilities"]))

    # ------------------------------------------------------------------
    # Test 5: Companion Morale System
    # ------------------------------------------------------------------
    print("\n[Suite 5: Companion Morale System]")
    m_p = {"name": "Banki"}
    mechanics.ensure_companion_profile(m_p)

    m1 = mechanics.update_companion_morale(m_p, "Ren", "Confident")
    check("Update morale to Confident succeeds", m1["success"] and mechanics.get_companion(m_p, "Ren")["morale"] == "Confident")

    m2 = mechanics.update_companion_morale(m_p, "Ren", "Panicked")
    check("Update morale to Panicked succeeds", m2["success"] and mechanics.get_companion(m_p, "Ren")["morale"] == "Panicked")

    m3 = mechanics.update_companion_morale(m_p, "Ren", "invalid_state")
    check("Invalid morale falls back to Steady", m3["success"] and mechanics.get_companion(m_p, "Ren")["morale"] == "Steady")

    # ------------------------------------------------------------------
    # Test 6: Washington Borough Safe-Zone Facilities
    # ------------------------------------------------------------------
    print("\n[Suite 6: Washington Borough Safe-Zone Facilities]")
    
    # Facility Registry Checks
    check("iron_spoke_taphouse exists", "iron_spoke_taphouse" in mechanics.WASHINGTON_FACILITIES)
    check("arcane_med_bay exists", "arcane_med_bay" in mechanics.WASHINGTON_FACILITIES)
    check("meiji_scavenger_dump exists", "meiji_scavenger_dump" in mechanics.WASHINGTON_FACILITIES)
    check("WARREN_COUNTY_BOUNTIES has 3 bounties", len(mechanics.WARREN_COUNTY_BOUNTIES) == 3)

    # 1. Taphouse Stew & Rest
    fac_p = {
        "name": "Banki",
        "col": 200,
        "hp": 40,
        "max_hp": 100,
        "active_buffs": []
    }
    mechanics.ensure_companion_profile(fac_p)
    mechanics.update_companion_morale(fac_p, "Ren", "Shaken")

    # Success case (has 200 Col, fee 150)
    tap_res = mechanics.use_taphouse_stew_and_rest(fac_p)
    check("Taphouse rest succeeds", tap_res["success"])
    check("Col deducted by 150 (200 -> 50)", fac_p["col"] == 50)
    check("Player healed +50 HP (40 -> 90)", fac_p["hp"] == 90)
    check("Companion morale restored to Confident", fac_p["companions"]["Ren"]["morale"] == "Confident")
    check("Well-Fed buff granted", "Well-Fed" in fac_p["active_buffs"])

    # Fail case (insufficient Col: has 50 Col, fee 150)
    tap_fail = mechanics.use_taphouse_stew_and_rest(fac_p)
    check("Taphouse rejects insufficient Col", not tap_fail["success"])

    # 2. Med-Bay Bio-Purification
    fac_p["col"] = 300
    fac_p["hp"] = 30
    fac_p["conditions"] = ["Poisoned", "Bleeding"]
    fac_p["active_buffs"].append("Corrosive Bleed")

    med_res = mechanics.use_med_bay_purification(fac_p)
    check("Med-Bay purification succeeds", med_res["success"])
    check("Col deducted by 250 (300 -> 50)", fac_p["col"] == 50)
    check("Player HP fully restored to max (100)", fac_p["hp"] == 100)
    check("Negative conditions cleared", len(fac_p["conditions"]) == 0)
    check("Negative buffs removed", "Corrosive Bleed" not in fac_p["active_buffs"])

    # Fail case
    med_fail = mechanics.use_med_bay_purification(fac_p)
    check("Med-Bay rejects insufficient Col", not med_fail["success"])

    # 3. Scavenger Dump Trade
    fac_p["col"] = 500
    fac_p["inventory"] = []

    # Buy Serrated Tripwire Coils (75 Col each x2 = 150 Col)
    buy_res = mechanics.buy_scavenger_material(fac_p, "Serrated Tripwire Coils", qty=2)
    check("Buy material succeeds", buy_res["success"])
    check("Col deducted by 150 (500 -> 350)", fac_p["col"] == 350)
    check("Item added to inventory with qty 2", any(i.get("name") == "Serrated Tripwire Coils" and i.get("qty") == 2 for i in fac_p["inventory"]))

    # Stack existing item: buy 1 more
    buy_stack = mechanics.buy_scavenger_material(fac_p, "Serrated Tripwire Coils", qty=1)
    check("Subsequent purchase stacks qty to 3", any(i.get("name") == "Serrated Tripwire Coils" and i.get("qty") == 3 for i in fac_p["inventory"]))
    check("Col deducted by 75 (350 -> 275)", fac_p["col"] == 275)

    # Reject non-existent item
    buy_bad = mechanics.buy_scavenger_material(fac_p, "Plasma Cannon 9000", qty=1)
    check("Scavenger dump rejects unstocked item", not buy_bad["success"])

    # Reject unaffordable quantity
    buy_broke = mechanics.buy_scavenger_material(fac_p, "Heavy Highway Snares", qty=10) # 120 * 10 = 1200 > 275
    check("Scavenger dump rejects purchase exceeding available Col", not buy_broke["success"])

    # 4. Warren County Bounty Board
    fac_p["quests"] = []
    bounty_id = "bounty_pohatcong_construct"
    b_res = mechanics.accept_bounty_directive(fac_p, bounty_id)
    check("Accept bounty succeeds", b_res["success"])
    check("Bounty added to active quests", any(q.get("id") == bounty_id for q in fac_p["quests"]))

    # Duplicate acceptance prevented
    b_dup = mechanics.accept_bounty_directive(fac_p, bounty_id)
    check("Duplicate bounty directive is rejected", not b_dup["success"])
    check("Quests list still has only 1 quest", len(fac_p["quests"]) == 1)

    # Reject unknown bounty ID
    b_bad = mechanics.accept_bounty_directive(fac_p, "bounty_phantom_dragon")
    check("Non-existent bounty ID is rejected", not b_bad["success"])

    # ------------------------------------------------------------------
    # Test 7: Backwards Compatibility with Legacy Save Schema
    # ------------------------------------------------------------------
    print("\n[Suite 7: Backwards Compatibility]")
    bare_profile = {
        "name": "BarePlayer",
        "level": 1,
        "hp": 100,
        "max_hp": 100
    }
    # Operations should automatically ensure profile without crashing
    c_act = mechanics.get_companion_combat_action(bare_profile, "Ren")
    check("get_companion_combat_action initializes Ren on bare profile", "Ren" in bare_profile.get("companions", {}))
    check("get_companion_combat_action returns valid action", "log" in c_act)

    xp_tx = mechanics.award_companion_xp(bare_profile, "Ren", 50)
    check("award_companion_xp initializes Ren on bare profile", xp_tx["success"])

    morale_tx = mechanics.update_companion_morale(bare_profile, "Ren", "Inspired")
    check("update_companion_morale initializes Ren on bare profile", morale_tx["success"])

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n======================================================================")
    print(f"PHASE M5 TEST SUITE RESULTS: {passed_checks} / {total_checks} PASSED")
    print("======================================================================")
    if passed_checks == total_checks:
        print("ALL TESTS PASSED SUCCESSFULLY! (100% Pass Rate)")
        return 0
    else:
        print(f"WARNING: {total_checks - passed_checks} tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
