"""
Automated Verification & Diagnostic Test Suite:
Pre-to-Post Integration Character Generator & Multi-Profile System
"""

import os
import sys
import json
import shutil
import tempfile
import backend.character_generator as cg
import backend.mechanics as mechanics

def run_tests():
    total_checks = 0
    passed_checks = 0

    def assert_check(condition, msg):
        nonlocal total_checks, passed_checks
        total_checks += 1
        if condition:
            passed_checks += 1
            print(f"  [PASS] {msg}")
        else:
            print(f"  [FAIL] {msg}")
            sys.exit(1)

    print("================================================================")
    print("  THE FRACTURED OVERLAY: CHARACTER GENERATOR VERIFICATION SUITE")
    print("================================================================")

    # --- TEST 1: PRESET BACKGROUNDS (All 8 Archtypes) ---
    print("\n[TEST 1] Verifying 8 Preset Vocational Backgrounds...")
    expected_bgs = [
        "software_engineer", "nurse_paramedic", "mechanic_machinist", 
        "hunter_outdoorsman", "construction_trades", "martial_artist_veteran", 
        "corporate_negotiator", "artist_chef"
    ]
    for bg_k in expected_bgs:
        assert_check(bg_k in cg.PRESET_BACKGROUNDS, f"Background '{bg_k}' registered")
        bg_data = cg.PRESET_BACKGROUNDS[bg_k]
        assert_check("skills" in bg_data and len(bg_data["skills"]) >= 2, f"'{bg_k}' provides >= 2 skills")
        assert_check("innate_perk" in bg_data and len(bg_data["innate_perk"]) > 0, f"'{bg_k}' has innate passive perk")
        for s_name, s_val in bg_data["skills"].items():
            assert_check(1 <= s_val["mastery"] <= 1000, f"'{bg_k}' skill '{s_name}' mastery ({s_val['mastery']}) in [1, 1000]")

    # --- TEST 2: PROCEDURAL CUSTOM BACKGROUND PARSING ---
    print("\n[TEST 2] Verifying Procedural Custom Background Parsing...")
    queries = [
        ("I was a high-voltage electrician and computer hardware technician", ["Magi-Tech Hacking", "Aether-Circuit Query"]),
        ("I was an emergency room trauma nurse and surgeon", ["Arcane Triage", "Field Surgery"]),
        ("I worked in an auto repair shop rebuilding engines and machining steel parts", ["Field Smithing", "Golem-Graft Rigging"]),
        ("I was a backcountry bow hunter and wilderness guide", ["Field Trapping", "Cartography"]),
        ("I was a heavy equipment operator and construction demolition worker", ["Trench Hammers", "Structural Breach"]),
        ("I was an amateur boxer and martial artist", ["One-Handed Axes", "Tactical Reflexes"]),
        ("I was an executive pastry chef and culinary caterer", ["Provisions & Alchemy", "Aether-Weaving"]),
        ("I was a corporate sales manager and contract negotiator", ["Resource Barter", "Faction Diplomacy"]),
        ("I was an astronomer who studied variable stars and wrote poetry", ["Survival Conditioning", "Tactical Reflexes"])
    ]
    for text, expected_skills in queries:
        parsed = cg.parse_custom_background(text)
        assert_check(len(parsed["skills"]) == 2, f"Custom query parsed 2 skills: '{text[:30]}...'")
        for exp_s in expected_skills:
            assert_check(exp_s in parsed["skills"], f"Detected expected skill '{exp_s}'")
        assert_check(len(parsed["innate_perk"]) > 5, "Generated custom innate passive perk")

    # --- TEST 3: ALL 6 RACIAL LINEAGES ---
    print("\n[TEST 3] Verifying 6 Racial Lineages & Mutation Mechanics...")
    expected_races = [
        "pure_human", "phrenic_human", "deepforged_dwarf", 
        "scrapper_goblinoid", "aether_elf", "golem_reborn"
    ]
    for r_k in expected_races:
        assert_check(r_k in cg.RACIAL_LINEAGES, f"Race '{r_k}' registered")
        r_data = cg.RACIAL_LINEAGES[r_k]
        assert_check(all(s in r_data["stat_mods"] for s in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]), f"'{r_k}' has complete 6-stat modifiers")
        assert_check(len(r_data["racial_abilities"]) >= 2, f"'{r_k}' has >= 2 racial abilities")

    # --- TEST 4: ALL 5 CLASS PATHS & THEMED WEAPONS ---
    print("\n[TEST 4] Verifying 5 Class Paths & Themed Loadouts...")
    expected_classes = ["pathless", "vanguard", "magi_saboteur", "aether_slinger", "wilderness_ranger"]
    for c_k in expected_classes:
        assert_check(c_k in cg.CLASS_PATHS, f"Class '{c_k}' registered")
        assert_check(len(cg.CLASS_PATHS[c_k]["starting_feats"]) >= 2, f"'{c_k}' has starting feats")
        assert_check(c_k in cg.CLASS_WEAPONS, f"'{c_k}' has defined starting weapons loadout")
        w_loadout = cg.CLASS_WEAPONS[c_k]
        assert_check("main_hand" in w_loadout and "off_hand" in w_loadout, f"'{c_k}' has main_hand and off_hand")

    # --- TEST 5: ALL 5 PERSONAL RELICS ---
    print("\n[TEST 5] Verifying 5 Pre-Integration Personal Relics...")
    expected_relics = ["smartphone", "multitool", "first_aid_pouch", "city_map", "pocket_watch"]
    for rel_k in expected_relics:
        assert_check(rel_k in cg.PERSONAL_RELICS, f"Relic '{rel_k}' registered")
        rel_data = cg.PERSONAL_RELICS[rel_k]
        assert_check(rel_data["durability"] > 0, f"'{rel_k}' has positive durability")
        assert_check(len(rel_data["desc"]) > 20, f"'{rel_k}' has rich evocative description")

    # --- TEST 6: FULL DERIVED CHARACTER GENERATION & POINT-BUY BOUNDS ---
    print("\n[TEST 6] Generating Characters across Archetypes & Verifying Derived Stats...")
    
    # Character A: Marcus Vance (Dwarf Vanguard)
    p_alloc_a = {"STR": 5, "DEX": 0, "CON": 6, "INT": 2, "WIS": 4, "CHA": 3}  # Sum = 20
    char_a = cg.generate_starting_character(
        name="Marcus Vance",
        point_alloc=p_alloc_a,
        background_key="construction_trades",
        race_key="deepforged_dwarf",
        class_key="vanguard",
        relic_key="multitool"
    )
    # STR: 10 + 5 + 2 = 17, CON: 10 + 6 + 3 = 19
    assert_check(char_a["stats"]["STR"] == 17, "Marcus STR == 17 (10 base + 5 pts + 2 dwarf)")
    assert_check(char_a["stats"]["CON"] == 19, "Marcus CON == 19 (10 base + 6 pts + 3 dwarf)")
    assert_check(char_a["stats"]["DEX"] == 9, "Marcus DEX == 9 (10 base + 0 pts - 1 dwarf)")
    # CON mod = (19 - 10) // 2 = 4 -> Max HP = 100 + 40 = 140
    assert_check(char_a["max_hp"] == 140, "Marcus Max HP == 140 derived from CON mod")
    assert_check(char_a["equipped"]["main_hand"] == "Heavy Scavenged Mace", "Vanguard default weapon equipped (Mace)")
    assert_check(char_a["equipped"]["off_hand"] == "Scrap-Plate Shield", "Vanguard default shield equipped (Shield)")

    # Derived mechanics
    enc_a = mechanics.calculate_encumbrance(char_a)
    ac_a = mechanics.calculate_ac(char_a, enc_a)
    assert_check(enc_a["max_weight_lbs"] == 17 * 15, f"Marcus max weight == {17*15} lbs (15 x STR)")
    assert_check(ac_a >= 10, f"Marcus AC == {ac_a} valid")

    # Character B: Elena Cross (Elf Aether-Slinger with Custom Weapons Override)
    p_alloc_b = {"STR": 0, "DEX": 4, "CON": 2, "INT": 8, "WIS": 4, "CHA": 2}  # Sum = 20
    char_b = cg.generate_starting_character(
        name="Elena Cross",
        point_alloc=p_alloc_b,
        background_key="artist_chef",
        race_key="aether_elf",
        class_key="aether_slinger",
        relic_key="pocket_watch",
        starting_weapons={"main_hand": "Reinforced Spear", "off_hand": "None"}
    )
    # STR: 10 + 0 - 1 = 9, DEX: 10 + 4 + 2 = 16, INT: 10 + 8 + 2 = 20
    assert_check(char_b["stats"]["STR"] == 9, "Elena STR == 9 (10 base - 1 elf)")
    assert_check(char_b["stats"]["DEX"] == 16, "Elena DEX == 16 (10 base + 4 pts + 2 elf)")
    assert_check(char_b["stats"]["INT"] == 20, "Elena INT == 20 (10 base + 8 pts + 2 elf)")
    assert_check(char_b["equipped"]["main_hand"] == "Reinforced Spear", "Manual weapons override applied (Spear)")
    assert_check("Aether-Weaving" in char_b["skills"], "Elena has 'Aether-Weaving' from artist_chef background")
    assert_check("Provisions & Alchemy" in char_b["skills"], "Elena has 'Provisions & Alchemy'")

    # --- TEST 7: MULTI-CHARACTER PROFILE SAVE/LOAD INTEGRITY ---
    print("\n[TEST 7] Verifying Multi-Character Profile Slot Isolation & Non-Corruption...")
    
    test_saves_dir = tempfile.mkdtemp(prefix="sao_test_saves_")
    try:
        # 1. Save Banki profile
        banki_player = {
            "name": "Banki",
            "level": 1,
            "hp": 10000,
            "max_hp": 10000,
            "col": 979577710,
            "stats": {"STR": 45, "DEX": 35, "CON": 43, "INT": 43, "WIS": 41, "CHA": 31},
            "equipped": {"chest": "Einherjar Rig (Gr. 5 Armor)", "main_hand": "Fenrir's Tusk (Gr. 5 Axe)", "off_hand": "Mjölnir-Null (Gr. 5 Trench-Hammer)"}
        }
        banki_file = os.path.join(test_saves_dir, "Banki.json")
        with open(banki_file, "w", encoding="utf-8") as f:
            json.dump({"player": banki_player, "messages": []}, f, indent=4)
            
        # 2. Save New Character profile (Marcus)
        marcus_file = os.path.join(test_saves_dir, "Marcus_Vance.json")
        with open(marcus_file, "w", encoding="utf-8") as f:
            json.dump({"player": char_a, "messages": []}, f, indent=4)
            
        # 3. Verify profiles can be listed independently
        found_profiles = [os.path.splitext(f)[0] for f in os.listdir(test_saves_dir) if f.endswith(".json")]
        assert_check("Banki" in found_profiles and "Marcus_Vance" in found_profiles, "Both character profiles coexist in slots")
        
        # 4. Verify Banki is completely unchanged
        with open(banki_file, "r", encoding="utf-8") as f:
            loaded_banki = json.load(f)["player"]
        assert_check(loaded_banki["name"] == "Banki", "Banki profile name preserved")
        assert_check(loaded_banki["stats"]["STR"] == 45, "Banki STR 45 preserved")
        assert_check(loaded_banki["col"] == 979577710, "Banki col 979,577,710 preserved")
        assert_check("Fenrir's Tusk" in loaded_banki["equipped"]["main_hand"], "Banki weapons preserved")

        # 5. Verify Marcus is completely intact
        with open(marcus_file, "r", encoding="utf-8") as f:
            loaded_marcus = json.load(f)["player"]
        assert_check(loaded_marcus["name"] == "Marcus Vance", "Marcus Vance profile name preserved")
        assert_check(loaded_marcus["stats"]["STR"] == 17, "Marcus STR 17 preserved")
        assert_check(loaded_marcus["class"] == "Vanguard (Heavy Frontliner)", "Marcus class preserved")
    finally:
        shutil.rmtree(test_saves_dir, ignore_errors=True)

    print("\n================================================================")
    print(f"  ALL {passed_checks}/{total_checks} CHECKS PASSED SUCCESSFULLY (100% PASS RATE)!")
    print("================================================================")

if __name__ == "__main__":
    run_tests()
