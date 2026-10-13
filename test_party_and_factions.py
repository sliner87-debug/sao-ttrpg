import unittest
import copy
import backend.mechanics as mechanics

class TestPartyAndFactionsPhase7(unittest.TestCase):
    def setUp(self):
        self.base_player = {
            "name": "Banki",
            "race": "Phrenic Human",
            "class": "Nordic Berserker",
            "level": 4,
            "hp": 135,
            "max_hp": 135,
            "col": 5000,
            "skills": {
                "One-Handed Axes": {"mastery": 120, "tier": "Journeyman"},
                "Trench Warfare": {"mastery": 80, "tier": "Apprentice"}
            },
            "feats": ["Iron Grip", "Berserk Fury"],
            "spells": [],
            "inventory": []
        }

    # =========================================================================
    # SUITE 1: 4-MEMBER RAIDING PARTY & ROSTER MANAGEMENT
    # =========================================================================
    def test_party_initialization_and_defaults(self):
        p = copy.deepcopy(self.base_player)
        comps = mechanics.ensure_party_system(p)
        
        # Verify companions exist
        self.assertIn("Ren", comps)
        self.assertIn("Elora", comps)
        self.assertIn("Torvald", comps)
        self.assertIn("Kibs", comps)

        # Ren should start recruited and active as default companion
        self.assertTrue(comps["Ren"]["recruited"])
        self.assertTrue(comps["Ren"]["active"])

        # Others start unrecruited
        self.assertFalse(comps["Elora"]["recruited"])
        self.assertFalse(comps["Torvald"]["recruited"])
        self.assertFalse(comps["Kibs"]["recruited"])

        active = mechanics.get_active_party(p)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["name"], "Ren Sasaki")

    def test_companion_recruitment_and_cap(self):
        p = copy.deepcopy(self.base_player)
        mechanics.ensure_party_system(p)

        # Recruit Elora
        res_elora = mechanics.recruit_companion(p, "Elora")
        self.assertTrue(res_elora["success"])
        self.assertTrue(res_elora["active"]) # Should auto-activate since active < 3

        # Recruit Torvald
        res_torvald = mechanics.recruit_companion(p, "Torvald")
        self.assertTrue(res_torvald["success"])
        self.assertTrue(res_torvald["active"]) # Now active = 3 (Ren, Elora, Torvald)

        active = mechanics.get_active_party(p)
        self.assertEqual(len(active), 3)

        # Recruit Kibs: should be benched because cap is 3 active companions
        res_kibs = mechanics.recruit_companion(p, "Kibs")
        self.assertTrue(res_kibs["success"])
        self.assertFalse(res_kibs["active"]) # Must go to reserve benched!

        # Total active companions is still 3 (4 total with Banki)
        active_after = mechanics.get_active_party(p)
        self.assertEqual(len(active_after), 3)
        self.assertNotIn("Kibs", [c["name"] for c in active_after])

    def test_roster_reconfiguration(self):
        p = copy.deepcopy(self.base_player)
        mechanics.ensure_party_system(p)
        mechanics.recruit_companion(p, "Elora")
        mechanics.recruit_companion(p, "Torvald")
        mechanics.recruit_companion(p, "Kibs")

        # Swap Ren and Elora for Kibs and Torvald
        res = mechanics.set_active_party_roster(p, ["Torvald", "Kibs"])
        self.assertTrue(res["success"])
        active_names = [c["name"] for c in mechanics.get_active_party(p)]
        self.assertEqual(len(active_names), 2)
        self.assertIn("Torvald Iron-Vein", active_names)
        self.assertIn("Kibs Nine-Fingers", active_names)
        self.assertNotIn("Ren Sasaki", active_names)

        # Exceeding 3 companions must fail
        fail_res = mechanics.set_active_party_roster(p, ["Ren", "Elora", "Torvald", "Kibs"])
        self.assertFalse(fail_res["success"])
        self.assertIn("cannot exceed 3", fail_res["message"].lower())

    # =========================================================================
    # SUITE 2: TACTICAL STANCES & SIMULTANEOUS COMBAT RESOLUTION
    # =========================================================================
    def test_stance_selection(self):
        p = copy.deepcopy(self.base_player)
        mechanics.ensure_party_system(p)
        mechanics.recruit_companion(p, "Elora")

        # Set Elora's stance to aether_overcharge
        res = mechanics.set_party_member_stance(p, "Elora", "aether_overcharge")
        self.assertTrue(res["success"])
        comp_elora = p["companions"]["Elora"]
        self.assertEqual(comp_elora["stance"], "aether_overcharge")

        # Invalid stance
        bad_res = mechanics.set_party_member_stance(p, "Elora", "nonexistent_stance")
        self.assertFalse(bad_res["success"])

    def test_multi_companion_combat_resolution(self):
        p = copy.deepcopy(self.base_player)
        mechanics.ensure_party_system(p)
        mechanics.recruit_companion(p, "Elora")
        mechanics.recruit_companion(p, "Torvald")

        # Configure stances
        mechanics.set_party_member_stance(p, "Ren", "suppression_fire")
        mechanics.set_party_member_stance(p, "Elora", "radiant_flurry")
        mechanics.set_party_member_stance(p, "Torvald", "aegis_bulwark")

        # Resolve party combat
        res = mechanics.resolve_party_combat_actions(p)
        self.assertEqual(len(res["actions"]), 3)
        tags = [a["tag"] for a in res["actions"]]
        self.assertIn("[REN SUPPRESSION]", tags)
        self.assertIn("[ELORA FLURRY]", tags)
        self.assertIn("[TORVALD AEGIS]", tags)

    # =========================================================================
    # SUITE 3: AFFINITY PROGRESSION & DUAL-TECH UNLOCKING
    # =========================================================================
    def test_companion_affinity_progression_and_threshold(self):
        p = copy.deepcopy(self.base_player)
        mechanics.ensure_party_system(p)

        # Ren starts at affinity 35 (Ally)
        comp_ren = p["companions"]["Ren"]
        self.assertEqual(comp_ren["affinity"], 35)
        self.assertEqual(comp_ren["affinity_tier"], "Ally")

        # Boost by 10 -> 45 (Still Ally)
        res1 = mechanics.increase_companion_affinity(p, "Ren", 10, reason="Campfire talk")
        self.assertEqual(res1["new_affinity"], 45)
        self.assertEqual(res1["tier"], "Ally")
        self.assertIsNone(res1["unlocked_combo"])

        # Boost by 5 -> 50 (Trusted Battle-Brother / Sister) -> UNLOCKS DUAL-TECH!
        res2 = mechanics.increase_companion_affinity(p, "Ren", 5, reason="Flawless dungeon sync")
        self.assertEqual(res2["new_affinity"], 50)
        self.assertEqual(res2["tier"], "Trusted Battle-Brother/Sister")
        self.assertIsNotNone(res2["unlocked_combo"])
        self.assertEqual(res2["unlocked_combo"]["name"], "Runic Axe Storm")

        # Feat should be automatically added to player sheet
        self.assertTrue(any("Dual-Tech Combo: Runic Axe Storm" in f for f in p["feats"]))

    def test_dual_tech_execution(self):
        p = copy.deepcopy(self.base_player)
        mechanics.ensure_party_system(p)

        # Before affinity 50, execute should fail (starting affinity is 35)
        fail_exec = mechanics.execute_dual_tech(p, "runic_axe_storm")
        self.assertFalse(fail_exec["success"])
        self.assertIn("Requires Affinity 50", fail_exec["message"])

        # Boost affinity to 50
        mechanics.increase_companion_affinity(p, "Ren", 15)

        # Now execute should succeed
        succ_exec = mechanics.execute_dual_tech(p, "runic_axe_storm")
        self.assertTrue(succ_exec["success"])
        self.assertIn("[DUAL-TECH: BANKI + REN -> RUNIC AXE STORM]", succ_exec["log"])
        self.assertIn("4d10+8 Slashing", succ_exec["damage"])

        # If Ren is benched, combo should fail
        p["companions"]["Ren"]["active"] = False
        benched_exec = mechanics.execute_dual_tech(p, "runic_axe_storm")
        self.assertFalse(benched_exec["success"])
        self.assertIn("must be in your active raiding party", benched_exec["message"])

    # =========================================================================
    # SUITE 4: SAO CURSOR CRIMINALITY (GREEN / ORANGE / RED)
    # =========================================================================
    def test_cursor_status_and_transitions(self):
        p = copy.deepcopy(self.base_player)

        # Starts at 0 infamy -> Green
        c_green = mechanics.get_cursor_status(p)
        self.assertEqual(c_green["status"], "green")
        self.assertTrue(c_green["safe_zone_clearance"])
        self.assertEqual(c_green["merchant_surcharge"], 0.0)

        # Add 5 infamy -> Orange (Criminal)
        res_orange = mechanics.adjust_infamy(p, 5, reason="Stole supply cache")
        self.assertTrue(res_orange["transition"])
        self.assertEqual(res_orange["new_cursor"], "orange")
        c_orange = mechanics.get_cursor_status(p)
        self.assertEqual(c_orange["status"], "orange")
        self.assertEqual(c_orange["merchant_surcharge"], 0.25)
        self.assertTrue(c_orange["safe_zone_clearance"])

        # Add 6 more infamy -> 11 total -> Red (Outlaw PK)
        res_red = mechanics.adjust_infamy(p, 6, reason="Attacked innocent player")
        self.assertTrue(res_red["transition"])
        self.assertEqual(res_red["new_cursor"], "red")
        c_red = mechanics.get_cursor_status(p)
        self.assertEqual(c_red["status"], "red")
        self.assertFalse(c_red["safe_zone_clearance"])

    def test_safe_zone_ward_enforcement(self):
        p = copy.deepcopy(self.base_player)

        # Green: allowed
        self.assertTrue(mechanics.check_safe_zone_ward_clearance(p)["allowed"])

        # Orange: allowed with surcharge
        mechanics.adjust_infamy(p, 3)
        chk_orange = mechanics.check_safe_zone_ward_clearance(p)
        self.assertTrue(chk_orange["allowed"])
        self.assertEqual(chk_orange["surcharge"], 0.25)

        # Red: denied with barrier blast
        mechanics.adjust_infamy(p, 10)
        chk_red = mechanics.check_safe_zone_ward_clearance(p)
        self.assertFalse(chk_red["allowed"])
        self.assertEqual(chk_red["damage"], 100)
        self.assertIn("BARRIER WARD DETONATION", chk_red["log"])

    def test_criminal_atonement(self):
        p = copy.deepcopy(self.base_player)
        p["col"] = 5000

        # Orange with 4 infamy -> cost is 4 * 500 = 2000 Col
        mechanics.adjust_infamy(p, 4)
        self.assertEqual(p["infamy"], 4)

        atone_res = mechanics.pay_criminal_atonement(p)
        self.assertTrue(atone_res["success"])
        self.assertEqual(atone_res["cost_paid"], 2000)
        self.assertEqual(p["col"], 3000)
        self.assertEqual(p["infamy"], 0)
        self.assertEqual(mechanics.get_cursor_status(p)["status"], "green")

        # Red player cannot buy atonement
        mechanics.adjust_infamy(p, 15)
        fail_atone = mechanics.pay_criminal_atonement(p)
        self.assertFalse(fail_atone["success"])
        self.assertIn("cannot be paid off", fail_atone["message"].lower())

    # =========================================================================
    # SUITE 5: FACTION POLITICS & GUILD ALIGNMENT
    # =========================================================================
    def test_faction_initialization_and_standings(self):
        p = copy.deepcopy(self.base_player)
        standings = mechanics.get_all_faction_standings(p)
        self.assertEqual(len(standings), 3)

        # Check default Neutral
        for st in standings:
            self.assertEqual(st["score"], 0)
            self.assertEqual(st["label"], "Neutral")

    def test_faction_reputation_tiers_and_perks(self):
        p = copy.deepcopy(self.base_player)

        # Vanguard Coalition: Friendly at 25+
        mechanics.modify_faction_rep(p, "vanguard_coalition", 30, reason="Sector 1 scouting")
        st_vc = mechanics.get_faction_standing(p, "vanguard_coalition")
        self.assertEqual(st_vc["label"], "Friendly")
        self.assertEqual(len(st_vc["perks_active"]), 1)

        # Vanguard Coalition: Honored at 50+
        mechanics.modify_faction_rep(p, "vanguard_coalition", 25, reason="Boss raid assistance")
        st_vc2 = mechanics.get_faction_standing(p, "vanguard_coalition")
        self.assertEqual(st_vc2["label"], "Honored / Revered")
        self.assertEqual(len(st_vc2["perks_active"]), 2)

        # Iron Syndicate: Hostile below 0
        mechanics.modify_faction_rep(p, "iron_syndicate", -15, reason="Robbed caravan")
        st_is = mechanics.get_faction_standing(p, "iron_syndicate")
        self.assertEqual(st_is["label"], "Hostile")

    # =========================================================================
    # SUITE 6: BACKWARDS COMPATIBILITY
    # =========================================================================
    def test_backwards_compatibility_legacy_player(self):
        # Old player structure with only Ren string or minimal dict
        legacy_p = {
            "name": "OldPlayer",
            "level": 2,
            "hp": 80,
            "max_hp": 80,
            "companions": {
                "Ren": {"name": "Ren", "level": 2, "hp": 30}
            }
        }
        comps = mechanics.ensure_party_system(legacy_p)
        self.assertIn("Ren", comps)
        self.assertIn("Elora", comps)
        self.assertIn("Torvald", comps)
        self.assertIn("Kibs", comps)

        active = mechanics.get_active_party(legacy_p)
        self.assertGreaterEqual(len(active), 1)

        cursor = mechanics.get_cursor_status(legacy_p)
        self.assertEqual(cursor["status"], "green")

    # =========================================================================
    # SUITE 7: LLM STATE UPDATES PROCESSING & XP SHARING
    # =========================================================================
    def test_llm_state_updates_processing(self):
        p = copy.deepcopy(self.base_player)
        mechanics.ensure_party_system(p)
        mechanics.recruit_companion(p, "Elora")

        # Simulate state_updates packet returned by llm_engine
        mock_state_updates = {
            "infamy_change": 5,
            "faction_rep_updates": [
                {"faction": "vanguard_coalition", "rep_change": 25, "reason": "Dungeon recon"}
            ],
            "affinity_updates": [
                {"companion": "Ren", "affinity_change": 15, "reason": "Coordinated strike"}
            ],
            "recruit_companion": "Torvald",
            "xp_change": 200
        }

        # 1. Process infamy
        mechanics.adjust_infamy(p, mock_state_updates["infamy_change"])
        self.assertEqual(p["infamy"], 5)
        self.assertEqual(mechanics.get_cursor_status(p)["status"], "orange")

        # 2. Process faction reps
        for fu in mock_state_updates["faction_rep_updates"]:
            mechanics.modify_faction_rep(p, fu["faction"], fu["rep_change"])
        self.assertEqual(mechanics.get_faction_standing(p, "vanguard_coalition")["label"], "Friendly")

        # 3. Process affinity (35 + 15 = 50 -> Unlocks Dual-Tech)
        for au in mock_state_updates["affinity_updates"]:
            mechanics.increase_companion_affinity(p, au["companion"], au["affinity_change"])
        self.assertEqual(p["companions"]["Ren"]["affinity"], 50)
        self.assertEqual(p["companions"]["Ren"]["affinity_tier"], "Trusted Battle-Brother/Sister")
        self.assertTrue(any("Runic Axe Storm" in f for f in p["feats"]))

        # 4. Process companion recruitment
        mechanics.recruit_companion(p, mock_state_updates["recruit_companion"])
        self.assertTrue(p["companions"]["Torvald"]["recruited"])
        self.assertTrue(p["companions"]["Torvald"]["active"]) # Banki + Ren, Elora, Torvald = 3 active companions

        # 5. Process active companion XP sharing (50% of 200 = 100 XP to all 3 active companions)
        comp_xp = mock_state_updates["xp_change"] // 2
        active_comps = mechanics.get_active_party(p)
        self.assertEqual(len(active_comps), 3)
        for ac in active_comps:
            old_xp = ac.get("xp", 0)
            mechanics.award_companion_xp(p, ac["name"], comp_xp)
            self.assertEqual(ac["xp"], old_xp + 100)

        # 6. Execute Dual Tech
        exec_res = mechanics.execute_dual_tech(p, "runic_axe_storm")
        self.assertTrue(exec_res["success"])

if __name__ == "__main__":
    unittest.main()

