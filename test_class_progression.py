"""
Automated Verification & Diagnostic Test Suite:
Revised Base Class System, Asymmetric Combat Resources & Harmonized Dual-Gate Evolution
"""

import sys
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
    print("  THE FRACTURED OVERLAY: REVISED BASE CLASS VERIFICATION SUITE")
    print("================================================================")

    # --- TEST 1: 7 ANCHOR CLASSES + PATHLESS INTEGRITY ---
    print("\n[TEST 1] Verifying 7 Anchor Classes + Pathless Data Integrity...")
    anchors = ["warrior", "mage", "cleric", "thief", "ranger", "engineer", "psion", "pathless"]
    expected_base_hps = {
        "warrior": 120, "mage": 80, "cleric": 105, "thief": 90,
        "ranger": 95, "engineer": 100, "psion": 85, "pathless": 100
    }
    for c_k in anchors:
        assert_check(c_k in cg.CLASS_PATHS, f"Anchor Class '{c_k}' registered in CLASS_PATHS")
        c_def = cg.CLASS_PATHS[c_k]
        assert_check(c_def["base_hp"] == expected_base_hps[c_k], f"'{c_k}' base HP == {expected_base_hps[c_k]}")
        assert_check(len(c_def["starting_feats"]) == 2, f"'{c_k}' has Fixed Iconic Duo (2 starting feats)")
        assert_check("combat_resource" in c_def, f"'{c_k}' defines combat_resource")
        assert_check(len(c_def.get("native_armor", [])) >= 1, f"'{c_k}' defines native armor conditioning")
        assert_check(len(c_def.get("favored_skills", [])) >= 1, f"'{c_k}' defines favored skills (+25% affinity)")

    # --- TEST 2: CLASS FEATS TREE (Levels 1, 3, 6, 10) ---
    print("\n[TEST 2] Verifying Complete Feat Trees for All 8 Classes...")
    for c_k in anchors:
        assert_check(c_k in mechanics.CLASS_FEATS_TREE, f"'{c_k}' registered in mechanics.CLASS_FEATS_TREE")
        tree = mechanics.CLASS_FEATS_TREE[c_k]
        assert_check(len(tree["level_1"]) == 2, f"'{c_k}' has 2 Level 1 iconic feats")
        assert_check(len(tree["level_3"]) == 3, f"'{c_k}' has 3 Level 3 choices (Pick 1 of 3)")
        assert_check(len(tree["level_6"]) == 3, f"'{c_k}' has 3 Level 6 choices (Pick 1 of 3)")
        assert_check(len(tree["level_10"]) == 3, f"'{c_k}' has 3 Level 10 capstone choices")
        
        # Verify structure of feat choices
        for lvl_key in ["level_3", "level_6", "level_10"]:
            for feat in tree[lvl_key]:
                assert_check("id" in feat and feat["id"] in ["A", "B", "C"], f"'{c_k}' {lvl_key} feat has valid ID")
                assert_check("name" in feat and len(feat["name"]) > 2, f"'{c_k}' {lvl_key} feat has name: {feat.get('name')}")
                assert_check("type" in feat and feat["type"] in ["Passive", "Active", "Reaction"], f"'{c_k}' {lvl_key} feat has valid type")
                assert_check("desc" in feat and len(feat["desc"]) > 10, f"'{c_k}' {lvl_key} feat has rich description")

    # --- TEST 3: ASYMMETRIC TACTICAL COMBAT RESOURCES ---
    print("\n[TEST 3] Verifying Asymmetric Combat Resource Engines & Boundaries...")
    
    # Warrior: Poise & Threat (0 to 100)
    p_warrior = {"class": "Warrior (Frontline Anchor)", "combat_resource": {}}
    res_w = mechanics.initialize_combat_resource(p_warrior)
    assert_check(res_w["name"] == "Poise & Threat", "Warrior initialized with Poise & Threat")
    assert_check(res_w["current"] == 0 and res_w["max"] == 100, "Warrior starts at 0/100 Poise")
    
    tx_w = mechanics.update_combat_resource(p_warrior, 35)
    assert_check(tx_w["new"] == 35, "Gained 35 Poise on blocking hits")
    tx_w2 = mechanics.update_combat_resource(p_warrior, 100)
    assert_check(tx_w2["new"] == 100, "Poise clamped at max 100")
    tx_w3 = mechanics.update_combat_resource(p_warrior, -40)
    assert_check(tx_w3["new"] == 60, "Spent 40 Poise on Guard Break")

    # Mage: Aetheric Flux (starts full at 50)
    p_mage = {"class": "Mage (Aether-Weaver)", "combat_resource": {}}
    res_m = mechanics.initialize_combat_resource(p_mage)
    assert_check(res_m["name"] == "Aetheric Flux", "Mage initialized with Aetheric Flux")
    assert_check(res_m["current"] == 50 and res_m["max"] == 50, "Mage starts full at 50/50 Flux")
    tx_m = mechanics.update_combat_resource(p_mage, -25)
    assert_check(tx_m["new"] == 25, "Spent 25 Flux on Crystalline Rail-Lance")

    # Psion: Psi-Strain (Push-your-luck 0 to 100%)
    p_psion = {"class": "Psion / Phrenic", "combat_resource": {}}
    res_p = mechanics.initialize_combat_resource(p_psion)
    assert_check(res_p["type"] == "strain", "Psion uses Strain type")
    tx_p1 = mechanics.update_combat_resource(p_psion, 80)
    assert_check("WARNING" in tx_p1["warning"], "Psion receives high-strain warning at 80%")
    tx_p2 = mechanics.update_combat_resource(p_psion, 30)
    assert_check("CRITICAL" in tx_p2["warning"], "Psion receives critical overload warning at 100%")

    # Engineer: Heat & Overclock (0 to 100)
    p_eng = {"class": "Engineer / Artificer", "combat_resource": {}}
    res_e = mechanics.initialize_combat_resource(p_eng)
    assert_check(res_e["name"] == "Heat & Overclock", "Engineer uses Heat & Overclock")
    tx_e = mechanics.update_combat_resource(p_eng, 100)
    assert_check("OVERHEAT" in tx_e["warning"], "Engineer triggers overheat warning at 100% Heat")

    # HUD display formatting
    disp_w = mechanics.get_combat_resource_display(p_warrior)
    assert_check(disp_w["display"] == "60 / 100", f"Warrior HUD formatted correctly: {disp_w['display']}")
    disp_p = mechanics.get_combat_resource_display(p_psion)
    assert_check("% Strain" in disp_p["display"], f"Psion HUD formatted with Strain: {disp_p['display']}")

    # --- TEST 4: ARCHETYPE HP SCALING & LEVEL PROGRESSION ---
    print("\n[TEST 4] Verifying Archetype HP Scaling & Level Up Engine...")
    
    # Warrior Level Up: Base HP 120, CON 16 (mod +3) -> HP gain = 35 + 3 = 38
    char_warrior = {
        "name": "Thorvald", "level": 1, "hp": 150, "max_hp": 150,
        "class": "Warrior (Frontline Anchor)", "stats": {"CON": 16, "STR": 16, "DEX": 10, "INT": 10, "WIS": 10, "CHA": 10},
        "feats": ["Shield Wall Stance", "Taunting War-Cry"], "free_attribute_points": 0
    }
    lvl_tx = mechanics.apply_level_up(char_warrior, chosen_feat="Unyielding Mass")
    assert_check(char_warrior["level"] == 2, "Level incremented to 2")
    assert_check(lvl_tx["hp_gain"] == 38, f"Warrior HP gain == 38 (35 base + 3 CON mod), got {lvl_tx['hp_gain']}")
    assert_check(char_warrior["max_hp"] == 188, f"Warrior Max HP == 188, got {char_warrior['max_hp']}")
    assert_check(char_warrior["free_attribute_points"] == 2, "Awarded 2 free attribute points")
    assert_check("Unyielding Mass" in char_warrior["feats"], "Level 3 feat applied to character feats list")

    # Attribute Allocation
    mechanics.allocate_attribute_points(char_warrior, {"STR": 1, "CON": 1})
    assert_check(char_warrior["stats"]["STR"] == 17, "STR increased from 16 to 17")
    assert_check(char_warrior["stats"]["CON"] == 17, "CON increased from 16 to 17")
    assert_check(char_warrior["free_attribute_points"] == 0, "Free points decremented to 0")

    # Mage Level Up: Base growth = 20
    char_mage = {
        "name": "Astrid", "level": 1, "hp": 90, "max_hp": 90,
        "class": "Mage (Aether-Weaver)", "stats": {"CON": 12, "INT": 18, "DEX": 12, "STR": 8, "WIS": 14, "CHA": 10},
        "feats": [], "free_attribute_points": 0
    }
    lvl_mage = mechanics.apply_level_up(char_mage)
    # CON 12 -> mod 1 -> HP gain = 20 + 1 = 21
    assert_check(lvl_mage["hp_gain"] == 21, f"Mage HP gain == 21 (20 base + 1 CON mod), got {lvl_mage['hp_gain']}")
    assert_check(char_mage["max_hp"] == 111, f"Mage Max HP == 111, got {char_mage['max_hp']}")

    # --- TEST 5: HARMONIZED DUAL-GATE EVOLUTION VERIFICATION ---
    print("\n[TEST 5] Verifying Harmonized Dual-Gate Evolution Gating & Requirements...")
    
    # Candidate 1: Level 8 with Boss killed and 120 Skill -> INELIGIBLE (Level too low)
    c1 = {
        "level": 8, "class_tier": 1, "bosses_defeated": ["Sector 1 Spire Boss - Gilded Construct"],
        "skills": {"Trench Hammers": {"mastery": 120}}
    }
    gate1 = mechanics.check_evolution_eligibility(c1)
    assert_check(not gate1["eligible"], "Level 8 candidate is ineligible")
    assert_check(any("Level Requirement Unmet" in u for u in gate1["unmet_conditions"]), "Unmet level recorded")

    # Candidate 2: Level 10, Skill 150, but NO Boss killed -> INELIGIBLE (Boss unmet)
    c2 = {
        "level": 10, "class_tier": 1, "bosses_defeated": [],
        "skills": {"Trench Hammers": {"mastery": 150}}
    }
    gate2 = mechanics.check_evolution_eligibility(c2)
    assert_check(not gate2["eligible"], "Level 10 candidate without boss kill is ineligible")
    assert_check(any("Boss Not Yet Slayed" in u for u in gate2["unmet_conditions"]), "Unmet boss recorded")

    # Candidate 3: Level 10, Boss killed, but highest skill is Novice (60) -> INELIGIBLE (Mastery unmet)
    c3 = {
        "level": 10, "class_tier": 1, "bosses_defeated": ["Sector 1 Spire Boss"],
        "skills": {"Trench Hammers": {"mastery": 60}}
    }
    gate3 = mechanics.check_evolution_eligibility(c3)
    assert_check(not gate3["eligible"], "Level 10 candidate with mastery < 100 is ineligible")
    assert_check(any("Skill Mastery" in u for u in gate3["unmet_conditions"]), "Unmet skill mastery recorded")

    # Candidate 4: Level 10, Boss killed, Skill 145 (Journeyman) -> FULLY ELIGIBLE FOR TIER 2!
    c4 = {
        "level": 10, "class_tier": 1, "bosses_defeated": ["Gilded Construct Spire Boss"],
        "skills": {"Trench Hammers": {"mastery": 145}},
        "class": "Warrior (Frontline Anchor)"
    }
    gate4 = mechanics.check_evolution_eligibility(c4)
    assert_check(gate4["eligible"], "Harmonized Dual-Gate requirements satisfied for Tier 2!")
    assert_check(gate4["target_tier"] == 2, "Target tier == 2")
    assert_check(len(gate4["unmet_conditions"]) == 0, "Zero unmet conditions")

    # --- TEST 6: CURATED 3-CHOICE EVOLUTION GENERATOR & FUSED SYNERGY ENGINE ---
    print("\n[TEST 6] Generating 3 Tailored Evolutions & Applying Fused Synergy...")
    
    # Warrior with secondary Aether-Weaving skill -> Telemetry produces Spellblade Runeknight!
    p_telemetry = {
        "name": "Valdemar", "level": 10, "class_tier": 1, "class": "Warrior (Frontline Anchor)",
        "skills": {
            "Trench Hammers": {"mastery": 180},
            "Aether-Weaving": {"mastery": 110}
        },
        "equipped": {"main_hand": "Heavy Scavenged Mace", "off_hand": "Scrap-Plate Shield"},
        "feats": []
    }
    evolutions = mechanics.generate_curated_evolutions(p_telemetry)
    assert_check(len(evolutions) == 3, "Cardinal System generates exactly 3 curated choices")
    
    # Check 3 categories: Pure, Hybrid, Unique
    categories = [e["category"] for e in evolutions]
    assert_check("Pure Specialization" in categories, "Presents 1 Pure Specialization")
    assert_check("Hybrid Melded Path" in categories, "Presents 1 Hybrid Melded Path")
    assert_check("Unique Deed Path" in categories, "Presents 1 Unique Deed Path")

    # Verify telemetry detects Aether-Weaving for Warrior -> produces Spellblade
    hybrid_opt = next(e for e in evolutions if e["category"] == "Hybrid Melded Path")
    assert_check("Spellblade" in hybrid_opt["title"] or "Runeknight" in hybrid_opt["title"], 
                 f"Telemetry curated Spellblade from magic skill: {hybrid_opt['title']}")

    # Unique Deed Path for Banki's weapon loadout (Axe + Hammer) -> Nordic Berserker
    p_banki = {
        "name": "Banki", "level": 10, "class_tier": 1, "class": "Pathless (Freeform)",
        "skills": {"One-Handed Axes": {"mastery": 210}, "Trench Hammers": {"mastery": 195}},
        "equipped": {"main_hand": "Fenrir's Tusk (Axe)", "off_hand": "Mjölnir-Null (Trench-Hammer)"},
        "feats": []
    }
    banki_evos = mechanics.generate_curated_evolutions(p_banki)
    unique_opt = next(e for e in banki_evos if e["category"] == "Unique Deed Path")
    assert_check("Nordic Berserker" in unique_opt["title"], f"Banki weapon telemetry awarded: {unique_opt['title']}")

    # Apply Evolution & Verify Fused Synergy Resource Boost
    evo_result = mechanics.apply_class_evolution(p_banki, unique_opt)
    assert_check(p_banki["class"] == "Nordic Berserker of the Rift", "Character title updated to evolved class")
    assert_check(p_banki["class_tier"] == 2, "Character tier incremented to 2")
    assert_check(p_banki["combat_resource"]["max"] == 125, "Combat resource pool boosted to 125 (+25%)")
    assert_check(any("Nordic Berserker" in f for f in p_banki["feats"]), "Evolution master perk appended to feats")

    print("================================================================")
    print(f"  ALL {passed_checks}/{total_checks} CHECKS PASSED SUCCESSFULLY (100% PASS RATE)!")
    print("================================================================")

if __name__ == "__main__":
    run_tests()
