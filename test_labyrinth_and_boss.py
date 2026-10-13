"""
test_labyrinth_and_boss.py
Comprehensive Verification Suite for Phase 6:
- Procedural Labyrinth Engine (The Pohatcong Depths)
- Room Topology, Traps, Runic Puzzle Vault, Sanctuary Rest
- Multi-Phase Sector Boss Architecture (The Gilded Spire Overlord)
- Break Gauge, Stagger States, Telegraph Warning & Counter-Actions
- Victory Claim, Legendary Rewards, Sector 2 Teleport Gate Unsealing
"""

import sys
import copy
import backend.mechanics as mechanics

passed_checks = 0
failed_checks = 0

def check(condition, message):
    global passed_checks, failed_checks
    if condition:
        print(f"  [PASS] {message}")
        passed_checks += 1
    else:
        print(f"  [FAIL] {message}")
        failed_checks += 1

def create_test_player():
    return {
        "name": "Banki",
        "level": 3,
        "hp": 100,
        "max_hp": 100,
        "col": 2000,
        "xp": 500,
        "stats": {"STR": 16, "DEX": 14, "CON": 16, "INT": 12, "WIS": 12, "CHA": 10},
        "skills": {
            "One-Handed Axes": {"mastery": 150, "tier": "Journeyman", "milestones_unlocked": ["Cleave"]},
            "Field Trapping": {"mastery": 200, "tier": "Journeyman", "milestones_unlocked": ["Quick Snare"]},
            "Cartography": {"mastery": 120, "tier": "Journeyman", "milestones_unlocked": ["Surveyor"]}
        },
        "inventory": [],
        "equipped": {
            "main_hand": "Bearded Iron Axe",
            "off_hand": "Trench Demolition Hammer",
            "chest": "Black Iron Lamellar Rig"
        },
        "gear_durability": {
            "main_hand": {"cur": 80, "max": 100},
            "off_hand": {"cur": 70, "max": 100},
            "chest": {"cur": 65, "max": 100}
        },
        "feats": [],
        "spells": [],
        "quests": [],
        "companions": {
            "Ren": {
                "name": "Ren Sasaki",
                "level": 3,
                "hp": 35,
                "max_hp": 35,
                "xp": 450,
                "next_level_xp": 900,
                "stance": "overwatch_hacking",
                "morale": "Steady"
            }
        }
    }


def suite_1_labyrinth_topology():
    print("\n--- SUITE 1: LABYRINTH TOPOLOGY & NAVIGATION ---")
    p = create_test_player()
    
    # 1. Initialization
    d_state = mechanics.initialize_dungeon_state(p)
    check(d_state["dungeon_id"] == "pohatcong_labyrinth", "Dungeon initialized with ID 'pohatcong_labyrinth'")
    check(d_state["current_room_id"] == "entry_hall", "Initial room is 'entry_hall'")
    check(len(d_state["rooms"]) == 9, "Labyrinth contains exactly 9 rooms")
    check("entry_hall" in d_state["visited_rooms"], "Entry hall recorded in visited rooms")
    
    cur_room = mechanics.get_current_dungeon_room(p)
    check(cur_room["id"] == "entry_hall", "get_current_dungeon_room returns entry_hall")
    check(cur_room["type"] == "sanctuary", "Entry hall is a sanctuary room")
    
    # 2. Valid Navigation
    mv1 = mechanics.move_dungeon_room(p, "calcified_mine_gallery")
    check(mv1["success"] is True, "Successfully navigated from entry_hall to calcified_mine_gallery")
    check(p["dungeon_state"]["current_room_id"] == "calcified_mine_gallery", "Current room ID updated to calcified_mine_gallery")
    check("calcified_mine_gallery" in p["dungeon_state"]["visited_rooms"], "calcified_mine_gallery added to visited rooms")
    
    # 3. Invalid Navigation (Unconnected room)
    mv_invalid = mechanics.move_dungeon_room(p, "gilded_overlord_arena")
    check(mv_invalid["success"] is False, "Direct movement to unconnected boss arena is blocked")
    check(p["dungeon_state"]["current_room_id"] == "calcified_mine_gallery", "Player remained in current room")
    
    # 4. Boss Gate Locked Check
    p["dungeon_state"]["current_room_id"] = "puzzle_chamber"
    mv_gate = mechanics.move_dungeon_room(p, "overlord_throne_gate")
    check(mv_gate["success"] is False, "Movement into boss gate blocked while puzzle is unsolved")


def suite_2_traps_and_disarming():
    print("\n--- SUITE 2: TRAPPED CORRIDORS & DISARMING ---")
    p = create_test_player()
    mechanics.initialize_dungeon_state(p)
    p["dungeon_state"]["current_room_id"] = "runic_trip_corridor"
    
    cur_room = mechanics.get_current_dungeon_room(p)
    check(cur_room["type"] == "trapped_corridor", "Room type is trapped_corridor")
    check("trap" in cur_room, "Trap definition exists in corridor")
    check(cur_room["trap"]["disarmed"] is False, "Trap is initially armed")
    
    # Test disarm with high Field Trapping mastery & Ren Overwatch
    # Banki has Trapping 200 (bonus +4), DEX 14 (+2), Ren Overwatch (+3) -> total mod +9 vs DC 14
    # Run disarm:
    res = mechanics.disarm_dungeon_trap(p)
    check("roll" in res and "dc" in res, "Disarm result reports roll and dc")
    if res["success"]:
        check(cur_room["trap"]["disarmed"] is True, "Successful roll disarmed the trap")
        check(cur_room["cleared"] is True, "Room marked as cleared upon disarm")
    else:
        check(res["damage_taken"] > 0, "Failed disarm triggered damage")
        check(p["hp"] < 100, "Player HP reduced by sprung trap")
        
    # Attempting to disarm again when neutralized
    cur_room["trap"]["disarmed"] = True
    res_repeat = mechanics.disarm_dungeon_trap(p)
    check(res_repeat["success"] is False, "Repeated disarm on neutralized trap is cleanly handled")


def suite_3_puzzle_vault():
    print("\n--- SUITE 3: HARMONIC FREQUENCY VAULT (PUZZLE) ---")
    p = create_test_player()
    mechanics.initialize_dungeon_state(p)
    p["dungeon_state"]["current_room_id"] = "puzzle_chamber"
    
    cur_room = mechanics.get_current_dungeon_room(p)
    check(cur_room["type"] == "puzzle_chamber", "Room type is puzzle_chamber")
    check(cur_room["puzzle"]["solved"] is False, "Puzzle is initially unsolved")
    
    # 1. Incorrect sequence
    bad_res = mechanics.solve_dungeon_puzzle(p, sequence=[1, 2, 3])
    check(bad_res["success"] is False, "Incorrect dial sequence [1-2-3] rejected")
    check(cur_room["puzzle"]["solved"] is False, "Puzzle remains unsolved")
    
    # 2. Correct sequence [3, 1, 4]
    good_res = mechanics.solve_dungeon_puzzle(p, sequence=[3, 1, 4])
    check(good_res["success"] is True, "Correct dial sequence [3-1-4] succeeds")
    check(cur_room["puzzle"]["solved"] is True, "Puzzle state marked solved")
    check(cur_room["cleared"] is True, "Puzzle chamber marked cleared")
    
    # 3. Verify Boss Gate unsealed
    gate_room = p["dungeon_state"]["rooms"]["overlord_throne_gate"]
    check(gate_room["unlocked"] is True, "Solving puzzle unlocked overlord_throne_gate")
    
    # Now navigation to boss gate and arena is permitted
    p["dungeon_state"]["current_room_id"] = "puzzle_chamber"
    mv_gate = mechanics.move_dungeon_room(p, "overlord_throne_gate")
    check(mv_gate["success"] is True, "Player can now enter overlord_throne_gate")
    
    mv_arena = mechanics.move_dungeon_room(p, "gilded_overlord_arena")
    check(mv_arena["success"] is True, "Player can now enter gilded_overlord_arena")
    check("boss_encounter" in p, "Entering boss arena automatically initialized boss encounter")


def suite_4_sanctuary_haven():
    print("\n--- SUITE 4: SANCTUARY HAVEN & FIELD REST ---")
    p = create_test_player()
    mechanics.initialize_dungeon_state(p)
    p["dungeon_state"]["current_room_id"] = "crystal_sanctuary"
    
    # Damage player and gear
    p["hp"] = 30
    p["gear_durability"]["main_hand"]["cur"] = 40
    p["companions"]["Ren"]["morale"] = "Panicked"
    
    rest_res = mechanics.rest_in_sanctuary(p)
    check(rest_res["success"] is True, "Rest in crystal sanctuary succeeded")
    check(p["hp"] == 80, "Rest restored 50% HP (30 -> 80)")
    check(p["gear_durability"]["main_hand"]["cur"] == 50, "Gear field-repaired by +10 (40 -> 50)")
    check(p["companions"]["Ren"]["morale"] == "Confident", "Ren's morale restored to Confident")
    
    # Attempting to rest in a non-sanctuary room
    p["dungeon_state"]["current_room_id"] = "calcified_mine_gallery"
    bad_rest = mechanics.rest_in_sanctuary(p)
    check(bad_rest["success"] is False, "Rest in hostile monster den is prohibited")


def suite_5_sector_boss_phases_and_break():
    print("\n--- SUITE 5: SECTOR BOSS MULTI-PHASE & BREAK GAUGE ---")
    p = create_test_player()
    boss = mechanics.initialize_boss_encounter(p, "gilded_overlord")
    
    check(boss["max_hp"] == 300, "Boss max HP is 300")
    check(boss["current_hp"] == 300, "Boss starts at 300 HP")
    check(boss["phase"] == 1, "Boss starts in Phase 1 (Runic Bulwark)")
    check(boss["current_break"] == 100, "Boss starts with 100 Break Gauge")
    check(boss["is_staggered"] is False, "Boss is initially not staggered")
    
    # 1. Phase 1 Damage Reduction (DR 3)
    # Deal 23 damage -> 23 - 3 = 20 actual damage
    dmg1 = mechanics.apply_damage_to_boss(p, 23, is_heavy=False)
    check(dmg1["damage_dealt"] == 20, "Phase 1 DR 3 reduced 23 damage to 20")
    check(boss["current_hp"] == 280, "Boss HP updated to 280")
    check(boss["current_break"] == 90, "Normal attack chipped Break Gauge by -10 (now 90)")
    check(boss["phase"] == 1, "Still in Phase 1")
    
    # 2. Heavy hammer attack on Break Gauge
    dmg2 = mechanics.apply_damage_to_boss(p, 33, is_heavy=True, is_stagger_hit=True)
    check(dmg2["damage_dealt"] == 30, "Heavy attack dealt 30 damage (33 - 3)")
    check(boss["current_break"] == 55, "Heavy stagger attack chipped Break Gauge by -35 (90 -> 55)")
    
    # 3. Trigger Stagger (Break Gauge to 0)
    mechanics.apply_damage_to_boss(p, 20, is_heavy=True, is_stagger_hit=True) # -35 -> 20
    dmg_stagger = mechanics.apply_damage_to_boss(p, 20, is_heavy=True, is_stagger_hit=True) # -35 -> 0
    check(boss["current_break"] == 0, "Break gauge reached 0")
    check(boss["is_staggered"] is True, "Boss entered STAGGERED state")
    check(dmg_stagger["stagger_triggered"] is True, "Stagger triggered flag is True")
    
    # 4. Critical damage during stagger (DR bypassed, +50% bonus)
    # Attack with 20 damage during stagger -> 20 * 1.5 = 30 damage, DR bypassed
    hp_before = boss["current_hp"]
    dmg_crit = mechanics.apply_damage_to_boss(p, 20)
    check(dmg_crit["damage_dealt"] == 30, "Staggered boss took +50% critical damage with DR bypassed (20 -> 30)")
    check(boss["current_hp"] == hp_before - 30, "Boss HP accurately reduced by critical stagger damage")
    
    # 5. Stagger recovery
    boss_action = mechanics.get_boss_turn_action(p)
    check(boss_action["action"] == "recover", "Staggered boss spends turn recovering")
    check(boss["is_staggered"] is False, "Boss is no longer staggered")
    check(boss["current_break"] == 100, "Break Gauge reset to 100 on recovery")
    
    # 6. Phase 2 Transition (Drop HP <= 180 / 60%)
    # Boss is at 186 HP. Phase 1 DR 3 -> deal 20 (actual 17) -> HP 169 (<= 180)
    dmg_p2 = mechanics.apply_damage_to_boss(p, 20)
    check(boss["current_hp"] <= 180, f"Boss HP now {boss['current_hp']} (<= 180)")
    check(boss["phase"] == 2, "Boss transitioned to Phase 2: Aetheric Core Overload")
    check(dmg_p2["phase_transition"] is True, "Phase transition flag reported True")
    p2_info = boss["phases"][2]
    check(p2_info["ac"] == 15 and p2_info["dr"] == 1, "Phase 2 has AC 15 and DR 1")
    
    # 7. Phase 3 Transition (Drop HP <= 60 / 20%)
    # Boss is at 169 HP. Phase 2 DR 1 -> deal 120 (actual 119) -> HP 50 (<= 60)
    dmg_p3 = mechanics.apply_damage_to_boss(p, 120)
    check(boss["current_hp"] <= 60, f"Boss HP now {boss['current_hp']} (<= 60)")
    check(boss["phase"] == 3, "Boss transitioned to Phase 3: Desperation Spatial Tear")
    check(dmg_p3["phase_transition"] is True, "Phase transition flag reported True")
    p3_info = boss["phases"][3]
    check(p3_info["ac"] == 13 and p3_info["dr"] == 0, "Phase 3 has AC 13 and DR 0")


def suite_6_telegraphs_and_counters():
    print("\n--- SUITE 6: TELEGRAPH WARNINGS & COUNTER-ACTIONS ---")
    p = create_test_player()
    boss = mechanics.initialize_boss_encounter(p, "gilded_overlord")
    
    # Prime a telegraph manually
    boss["active_telegraph"] = {
        "name": "Colossal Seismic Cleave",
        "dc": 15,
        "stat": "DEX",
        "damage": "3d10+6 Force",
        "warning": "Raises titanic gilded maul high overhead!"
    }
    
    # 1. Counter via Ren's Aetheric Phase-Veil (Guaranteed avoidance)
    ren_counter = mechanics.counter_boss_telegraph(p, "ren_phase_veil")
    check(ren_counter["success"] is True, "Ren's Phase-Veil successfully countered telegraph")
    check(ren_counter["damage_avoided"] is True, "Damage completely avoided")
    check(boss["active_telegraph"] is None, "Telegraph cleared after being countered")
    
    # 2. Counter via Shield Block
    boss["active_telegraph"] = {
        "name": "Colossal Seismic Cleave",
        "dc": 10,
        "stat": "CON",
        "damage": "3d10 Force"
    }
    block_counter = mechanics.counter_boss_telegraph(p, "shield_block")
    check("damage_reduced" in block_counter, "Shield Block resulted in damage reduction")
    check(boss["active_telegraph"] is None, "Telegraph cleared after shield block")
    
    # 3. Counter via Stagger Interrupt
    boss["active_telegraph"] = {
        "name": "Aetheric Overload Cascade",
        "dc": 16,
        "stat": "DEX",
        "damage": "4d8 Lightning"
    }
    boss["current_break"] = 30
    interrupt_counter = mechanics.counter_boss_telegraph(p, "stagger_interrupt")
    check(interrupt_counter["success"] is True, "Stagger interrupt strike succeeded")
    check(boss["current_break"] == 0, "Break gauge reached 0 from interrupt")
    check(boss["is_staggered"] is True, "Boss staggered by interrupt")


def suite_7_victory_and_rewards():
    print("\n--- SUITE 7: VICTORY CLAIM, REWARDS & SECTOR 2 PORTAL ---")
    p = create_test_player()
    mechanics.initialize_dungeon_state(p)
    boss = mechanics.initialize_boss_encounter(p, "gilded_overlord")
    
    # Add Overlord directive quest
    p["quests"].append({
        "id": "bounty_gilded_overlord",
        "title": "Sector Overlord Elimination: The Gilded Spire",
        "completed": False
    })
    
    # Cannot claim victory if boss HP > 0
    bad_claim = mechanics.claim_boss_victory(p)
    check(bad_claim["success"] is False, "Cannot claim victory while boss is alive")
    
    # Reduce boss HP to 0
    boss["current_hp"] = 0
    
    old_xp = p["xp"]
    old_col = p["col"]
    old_ren_xp = p["companions"]["Ren"]["xp"] if "xp" in p["companions"]["Ren"] else 0
    
    claim_res = mechanics.claim_boss_victory(p)
    check(claim_res["success"] is True, "Boss victory claimed successfully")
    check(p["xp"] == old_xp + 2500, "Awarded 2,500 XP to Banki")
    check(p["col"] == old_col + 5000, "Awarded 5,000 Col to Banki")
    check(p["companions"]["Ren"]["xp"] == old_ren_xp + 1250, "Awarded 1,250 XP (50% share) to Ren")
    
    # Check Legendary Items
    inv_names = [i["name"] for i in p["inventory"] if isinstance(i, dict)]
    check("Overlord's Gilded Core" in inv_names, "Inventory contains 'Overlord's Gilded Core' (Legendary Grade 5)")
    check("Gilded Spire Great-Axe" in inv_names, "Inventory contains 'Gilded Spire Great-Axe' (Legendary Grade 5)")
    
    # Check Feats / Titles
    feat_strs = [str(f) for f in p["feats"]]
    check(any("Sector 1 Conqueror" in f for f in feat_strs), "Awarded 'Sector 1 Conqueror' title/feat")
    
    # Check Dungeon & Quest Completion
    check(p["dungeon_state"]["dungeon_completed"] is True, "Dungeon state marked dungeon_completed = True")
    check(p["dungeon_state"]["rooms"]["gilded_overlord_arena"]["cleared"] is True, "Boss arena room marked cleared")
    check(p["quests"][0]["completed"] is True, "Sector Overlord bounty quest marked completed")


def suite_8_backwards_compatibility():
    print("\n--- SUITE 8: BACKWARDS COMPATIBILITY & ISOLATION ---")
    legacy_player = {"name": "OldHero", "level": 1, "hp": 50, "max_hp": 50}
    
    d_init = mechanics.initialize_dungeon_state(legacy_player)
    check("dungeon_state" in legacy_player, "initialize_dungeon_state safely populates bare player")
    check(d_init["dungeon_id"] == "pohatcong_labyrinth", "Default dungeon is pohatcong_labyrinth")
    
    cur_r = mechanics.get_current_dungeon_room(legacy_player)
    check(cur_r["id"] == "entry_hall", "Bare player defaults to entry_hall")
    
    boss_init = mechanics.initialize_boss_encounter(legacy_player)
    check(boss_init["id"] == "gilded_overlord", "initialize_boss_encounter safely populates bare player")
    
    dmg_res = mechanics.apply_damage_to_boss(legacy_player, 15)
    check(dmg_res["success"] is True, "apply_damage_to_boss works on bare player")


if __name__ == "__main__":
    print("======================================================================")
    print("RUNNING PHASE 6 TEST SUITE: LABYRINTH DUNGEON & SECTOR BOSS ENGINE")
    print("======================================================================")
    
    suite_1_labyrinth_topology()
    suite_2_traps_and_disarming()
    suite_3_puzzle_vault()
    suite_4_sanctuary_haven()
    suite_5_sector_boss_phases_and_break()
    suite_6_telegraphs_and_counters()
    suite_7_victory_and_rewards()
    suite_8_backwards_compatibility()
    
    print("\n======================================================================")
    print(f"PHASE 6 TEST SUITE RESULTS: {passed_checks} PASSED / {failed_checks} FAILED")
    print("======================================================================")
    if failed_checks == 0:
        print("ALL TESTS PASSED SUCCESSFULLY! (100% Pass Rate)")
        sys.exit(0)
    else:
        print("SOME TESTS FAILED.")
        sys.exit(1)
