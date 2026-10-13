"""
Comprehensive Cross-Phase Audit Script (Phases 1-8)
Tests integration, edge cases, state transitions, and deterministic math across all subsystems.
"""
import copy
import json
import unittest
import backend.mechanics as mechanics

class TestComprehensiveAuditPhases1to8(unittest.TestCase):
    def setUp(self):
        with open("save_game.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        self.raw_player = data["player"]
        
        # Canonical test player
        self.player = {
            "name": "Banki",
            "race": "Phrenic Human",
            "class": "Nordic Berserker",
            "class_tier": 1,
            "level": 4,
            "hp": 140,
            "max_hp": 150,
            "col": 12500,
            "stats": {"STR": 18, "DEX": 14, "CON": 16, "INT": 12, "WIS": 12, "CHA": 10},
            "location": "Washington Borough - The Iron Spoke Taphouse",
            "skills": {
                "One-Handed Axes": {"mastery": 145, "tier": "Journeyman", "description": "Proficiency with axes.", "milestones_unlocked": ["Cleave"]},
                "Trench Warfare": {"mastery": 95, "tier": "Apprentice", "description": "Fortified trench combat.", "milestones_unlocked": []},
                "Field Trapping": {"mastery": 110, "tier": "Journeyman", "description": "Trap craft and rigging.", "milestones_unlocked": []}
            },
            "feats": ["Iron Grip", "Berserk Fury", "Dire-Wolf Fur Mantle"],
            "spells": [],
            "racial_abilities": [
                "Aether-Telepathy: Communicate silently within 60ft",
                "Telekinetic Grip: Manipulate objects with mind"
            ],
            "equipped": {
                "head": "None",
                "chest": "Einherjar Rig (Gr. 5 Armor)",
                "main_hand": "Fenrir's Tusk (Gr. 5 Axe)",
                "off_hand": "Mjöllnir-Null (Gr. 5 Trench-Hammer)",
                "accessory": "Dire-Wolf Fur Mantle"
            },
            "inventory": [
                {"name": "Medical Packs", "qty": 5, "weight_lbs": 1.0, "rarity": "Uncommon"},
                {"name": "Carbon Line Spools", "qty": 3, "weight_lbs": 0.5, "rarity": "Common"},
                {"name": "Serrated Tripwire Coils", "qty": 6, "weight_lbs": 0.5, "rarity": "Common"},
                {"name": "Heavy Highway Snares", "qty": 2, "weight_lbs": 2.0, "rarity": "Uncommon"},
                {"name": "Wolf Marrow", "qty": 2, "weight_lbs": 0.5, "rarity": "Common"},
                {"name": "Wild Roots", "qty": 3, "weight_lbs": 0.2, "rarity": "Common"},
                {"name": "Raw Boar Flank", "qty": 2, "weight_lbs": 1.5, "rarity": "Common"},
                {"name": "Salted Moss", "qty": 2, "weight_lbs": 0.1, "rarity": "Common"}
            ]
        }

    # =========================================================================
    # PHASE M1 AUDIT: COMBAT MATH, AC, & ENCUMBRANCE
    # =========================================================================
    def test_phase_m1_encumbrance_and_ac(self):
        p = copy.deepcopy(self.player)
        enc = mechanics.calculate_encumbrance(p)
        self.assertIn("current_weight_lbs", enc)
        self.assertIn("max_weight_lbs", enc)
        self.assertIn("tier", enc)
        self.assertGreater(enc["max_weight_lbs"], 0)
        self.assertFalse(enc["penalties"]["disadvantage_stealth"]) # Under capacity

        # AC Calculation
        ac = mechanics.calculate_ac(p, enc)
        self.assertIsInstance(ac, int)
        self.assertGreaterEqual(ac, 10)

        # Overload test: 500 lbs leads to Overencumbered
        p["inventory"].append({"name": "Colossal Lead Anchor", "weight_lbs": 500.0, "qty": 1})
        over_enc = mechanics.calculate_encumbrance(p)
        self.assertIn(over_enc["tier"], ["Encumbered", "Heavily Encumbered", "Overloaded", "Overencumbered"])
        self.assertLess(over_enc["penalties"]["speed_pct"], 100)

    # =========================================================================
    # PHASE M2 AUDIT: 8 BASE CLASSES, 1-1000 SKILLS, MILESTONES & EVOLUTION
    # =========================================================================
    def test_phase_m2_classes_resources_and_milestones(self):
        p = copy.deepcopy(self.player)
        # 1. Asymmetric Combat Resource
        res = mechanics.initialize_combat_resource(p)
        self.assertIn("name", res)
        self.assertIn("current", res)
        self.assertIn("max", res)

        # Update resource
        tx = mechanics.update_combat_resource(p, 25)
        self.assertEqual(tx["new"], 25)

        # 2. Skill Mastery Update & Milestone Unlock
        # Trench Warfare is at 95; adding 10 hits 105 (crossing Journeyman 100 threshold)
        up_res = mechanics.update_skill_mastery(p, "Trench Warfare", gain_or_dc=10, is_dc=False)
        self.assertEqual(up_res["new_mastery"], 105)
        self.assertEqual(up_res["new_tier"], "Journeyman")
        self.assertGreaterEqual(len(up_res["unlocked_milestones"]), 1)

        # 3. Dual-Gate Evolution Check
        evo = mechanics.check_evolution_eligibility(p)
        self.assertIn("eligible", evo)
        self.assertFalse(evo["eligible"]) # Needs Level 10 and Sector 1 Boss

    # =========================================================================
    # PHASE M3 AUDIT: GEAR DURABILITY, WEAR PENALTIES, & FIELD TRAPS
    # =========================================================================
    def test_phase_m3_durability_and_field_traps(self):
        p = copy.deepcopy(self.player)
        norm_dur = mechanics.normalize_gear_durability(p)
        self.assertIn("main_hand", norm_dur)
        self.assertEqual(norm_dur["main_hand"]["max"], 200)

        # Inflict durability wear
        d_res = mechanics.apply_durability_damage(p, "main_hand", 50)
        self.assertEqual(d_res["new_cur"], 150)

        # Field Traps Check
        can_craft, msg, avail = mechanics.can_craft_trap(p, "heavy_highway_snare")
        self.assertTrue(can_craft)
        rig_res = mechanics.rig_field_trap(p, "heavy_highway_snare")
        self.assertTrue(rig_res["success"])
        self.assertEqual(len(p["active_traps"]), 1)

        # Trigger Trap
        trig_res = mechanics.trigger_field_trap(p, p["active_traps"][0]["key"])
        self.assertTrue(trig_res["success"])
        self.assertEqual(len(p["active_traps"]), 0)

    # =========================================================================
    # PHASE M4 AUDIT: BIOMECHANICAL GOLEM-GRAFTS & ABILITY MATRIX
    # =========================================================================
    def test_phase_m4_grafts_and_matrix(self):
        p = copy.deepcopy(self.player)
        g_sys = mechanics.ensure_graft_system(p)
        self.assertIn("installed_grafts", g_sys)

        # Install Graft into dermal slot
        inst_res = mechanics.install_graft(p, "subdermal_carapace_weave", "dermal", surgeon_fee_col=0)
        self.assertTrue(inst_res["success"])
        strain = mechanics.get_current_graft_strain(p)
        self.assertGreater(strain, 0)

        # Ability Matrix Slots
        m_sys = mechanics.ensure_ability_matrix(p)
        self.assertIn("active", m_sys)
        slot_res = mechanics.slot_ability(p, "Berserk Cleave")
        self.assertTrue(slot_res["success"])
        self.assertIn("Berserk Cleave", mechanics.get_slotted_abilities(p))

    # =========================================================================
    # PHASE M5 AUDIT: REN ENGINE, 4 TACTICAL STANCES, & SAFE-ZONE FACILITIES
    # =========================================================================
    def test_phase_m5_ren_and_safe_zones(self):
        p = copy.deepcopy(self.player)
        mechanics.ensure_companion_profile(p)
        ren = mechanics.get_companion(p, "Ren")
        self.assertEqual(ren["name"], "Ren Sasaki")

        # Cycle tactical stances
        for s_key in ["overwatch_hacking", "suppression_fire", "full_evasion", "utility_rigging"]:
            s_res = mechanics.set_companion_stance(p, s_key, "Ren")
            self.assertTrue(s_res["success"])
            act = mechanics.get_companion_combat_action(p, "Ren")
            self.assertEqual(act["stance_key"], s_key)

        # Safe-zone facilities interaction
        taphouse = mechanics.use_taphouse_stew_and_rest(p)
        self.assertTrue(taphouse["success"])

        clinic = mechanics.use_med_bay_purification(p)
        self.assertTrue(clinic["success"])

    # =========================================================================
    # PHASE 6 AUDIT: POHATCONG LABYRINTH & GILDED SPIRE OVERLORD
    # =========================================================================
    def test_phase_6_labyrinth_and_boss_encounter(self):
        p = copy.deepcopy(self.player)
        d_state = mechanics.initialize_dungeon_state(p)
        self.assertEqual(d_state["dungeon_id"], "pohatcong_labyrinth")

        # Current Room is entry_hall
        r = mechanics.get_current_dungeon_room(p)
        self.assertEqual(r["id"], "entry_hall")

        # Movement to calcified_mine_gallery
        mv = mechanics.move_dungeon_room(p, "calcified_mine_gallery")
        self.assertTrue(mv["success"])

        # Move to runic_trip_corridor and disarm trap
        p["dungeon_state"]["current_room_id"] = "runic_trip_corridor"
        dis = mechanics.disarm_dungeon_trap(p)
        self.assertIn("roll", dis)
        self.assertIn("dc", dis)

        # Boss Encounter
        boss = mechanics.initialize_boss_encounter(p)
        self.assertEqual(boss["phase"], 1)
        self.assertEqual(boss["current_hp"], 300)

        # Deal damage and break stance
        dmg = mechanics.apply_damage_to_boss(p, 50, is_heavy=True, is_stagger_hit=True)
        self.assertTrue(dmg["success"])
        self.assertLess(dmg["boss_hp"], 300)
        self.assertLess(dmg["current_break"], 100)

    # =========================================================================
    # PHASE 7 AUDIT: 4-MEMBER PARTY, DUAL-TECHS, SAO CURSORS, & FACTIONS
    # =========================================================================
    def test_phase_7_party_dual_tech_and_factions(self):
        p = copy.deepcopy(self.player)
        mechanics.ensure_party_system(p)

        # Recruit Elora and Torvald
        mechanics.recruit_companion(p, "Elora")
        mechanics.recruit_companion(p, "Torvald")
        party = mechanics.get_active_party(p)
        self.assertEqual(len(party), 3) # Ren, Elora, Torvald

        # Multi-companion turn actions
        actions = mechanics.resolve_party_combat_actions(p)
        self.assertEqual(len(actions), 3)

        # Companion Affinity & Dual-Tech Unlock
        aff = mechanics.increase_companion_affinity(p, "Ren", 25)
        self.assertGreaterEqual(p["companions"]["Ren"]["affinity"], 50)
        self.assertTrue(any("Runic Axe Storm" in str(f) for f in p["feats"]))

        # Execute Dual-Tech
        dt = mechanics.execute_dual_tech(p, "runic_axe_storm")
        self.assertTrue(dt["success"])

        # SAO Cursor Infamy
        inf = mechanics.adjust_infamy(p, 3)
        self.assertEqual(mechanics.get_cursor_status(p)["status"], "orange")

        # Faction Rep
        rep = mechanics.modify_faction_rep(p, "vanguard_coalition", 30)
        self.assertEqual(mechanics.get_faction_standing(p, "vanguard_coalition")["label"], "Friendly")

    # =========================================================================
    # PHASE 8 AUDIT: CHRONO ENGINE, AETHER WEATHER, COOKING & FIELD CAMP
    # =========================================================================
    def test_phase_8_chrono_weather_cooking_and_camp(self):
        p = copy.deepcopy(self.player)
        mechanics.ensure_party_system(p)
        chrono = mechanics.ensure_chrono_system(p)

        # 1. 24h Clock and Period Progression
        t_adv = mechanics.advance_game_time(p, minutes=120)
        self.assertEqual(t_adv["hour"], 11)
        self.assertEqual(t_adv["minute"], 30)
        self.assertEqual(t_adv["period"], "day")

        # 2. Weather Shifts & Modifiers
        w_res = mechanics.set_weather(p, "glitch_freeze")
        self.assertTrue(w_res["success"])
        frost = mechanics.check_frostbite_protection(p)
        self.assertTrue(frost["protected"]) # Banki's mantle

        # 3. Campfire Culinary Crafting
        c_res = mechanics.cook_campfire_meal(p, "wolf_heart_stew")
        self.assertTrue(c_res["success"])
        self.assertIn("[Wolf-Heart Vigor]", p["active_buffs"])

        # 4. 8-Hour Camping with Watch Assignment
        p["location"] = "Sector 1 Wilderness"
        p["hp"] = 50
        camp = mechanics.pitch_wilderness_camp(p, watch_companion="Torvald")
        self.assertTrue(camp["success"])
        self.assertEqual(camp["healed_hp"], 50)
        self.assertIn("Bulwark Barricade", camp["watch_perk"])
        # 11:30 + 8h = 19:30 (Dusk)
        self.assertEqual(camp["time_info"]["period"], "dusk")

    # =========================================================================
    # PHASE 9 AUDIT: SOVEREIGN HOMESTEAD, VAULT, TROPHIES & MYTHIC FORGING
    # =========================================================================
    def test_phase_9_homestead_and_mythic_crafting(self):
        p = copy.deepcopy(self.player)
        mechanics.ensure_homestead_system(p)

        # 1. Purchase Homestead
        p["col"] = 10000
        h_buy = mechanics.purchase_homestead(p)
        self.assertTrue(h_buy["success"])
        self.assertTrue(p["homestead"]["owned"])

        # 2. Vault Deposit & Withdraw
        v_dep = mechanics.deposit_to_vault(p, "", col_amount=2000)
        self.assertTrue(v_dep["success"])
        self.assertEqual(p["homestead"]["vault_col"], 2000)

        v_wdr = mechanics.withdraw_from_vault(p, "", col_amount=500)
        self.assertTrue(v_wdr["success"])
        self.assertEqual(p["homestead"]["vault_col"], 1500)

        # 3. Mount Trophy & Passive Buffs
        p["inventory"].append({"name": "Overlord's Gilded Core", "qty": 1, "rarity": "Legendary"})
        t_res = mechanics.mount_boss_trophy(p, "Overlord's Gilded Core")
        self.assertTrue(t_res["success"])
        self.assertEqual(len(mechanics.get_active_trophy_buffs(p)), 1)
        self.assertTrue(any("[Aegis of the Spire]" in str(f) for f in p["feats"]))

        # 4. Greenhouse Harvest
        p["chrono"] = {"day": 1}
        g_res = mechanics.harvest_alchemical_garden(p)
        self.assertTrue(g_res["success"])

        # 5. Commodity Market Trading
        c_res = mechanics.trade_commodity(p, "scrap_metal", action="buy", qty=2)
        self.assertTrue(c_res["success"])

        # 6. Deepforged Master-Anvil & Mythic Forging
        mechanics.upgrade_homestead_facility(p, "master_anvil")
        p["equipped"]["main_hand"] = "Fenrir's Tusk (Gr. 5 Axe)"
        p["inventory"].extend([
            {"name": "Overlord's Gilded Core", "qty": 1},
            {"name": "Refined Aether-Alloy", "qty": 5},
            {"name": "Carbon Line Spools", "qty": 3}
        ])
        p["col"] = 5000
        f_res = mechanics.forge_mythic_equipment(p, "fenrirs_howl")
        self.assertTrue(f_res["success"])
        self.assertEqual(f_res["grade"], 6)
        self.assertEqual(p["equipped"]["main_hand"], "Fenrir's Howl (Grade 6 Mythic Great-Axe)")
        self.assertTrue(mechanics.is_ability_slotted(p, "Crystalline Frost Wave"))

if __name__ == "__main__":
    unittest.main()
