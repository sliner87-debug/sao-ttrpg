import unittest
import copy
from backend import mechanics

class TestHomesteadAndMythicCrafting(unittest.TestCase):
    def setUp(self):
        self.player = {
            "name": "Banki",
            "hp": 85,
            "max_hp": 85,
            "level": 3,
            "col": 10000,
            "stats": {"STR": 16, "DEX": 12, "CON": 15, "INT": 11, "WIS": 13, "CHA": 9},
            "equipped": {
                "main_hand": "Fenrir's Tusk (Gr. 5 Axe)",
                "off_hand": "Mjöllnir-Null (Gr. 5 Trench-Hammer)",
                "chest": "Black-Iron Runic Hauberk",
                "head": "Dire-Wolf Fur Mantle",
                "accessory": "Iron Syndicate Token"
            },
            "inventory": [
                {"name": "Fenrir's Tusk (Gr. 5 Axe)", "rarity": "Legendary", "qty": 1, "weight_lbs": 6.0},
                {"name": "Overlord's Gilded Core", "rarity": "Legendary", "qty": 2, "weight_lbs": 3.0},
                {"name": "Refined Aether-Alloy", "rarity": "Uncommon", "qty": 10, "weight_lbs": 1.0},
                {"name": "Carbon Line Spools", "rarity": "Common", "qty": 5, "weight_lbs": 0.5},
                {"name": "Corroded Micro-Capacitor", "rarity": "Common", "qty": 5, "weight_lbs": 0.5},
                {"name": "Mutated Frost Herb", "rarity": "Common", "qty": 2, "weight_lbs": 0.2}
            ],
            "gear_durability": {
                "main_hand": {"item": "Fenrir's Tusk (Gr. 5 Axe)", "cur": 120, "max": 120, "grade": 5},
                "off_hand": {"item": "Mjöllnir-Null (Gr. 5 Trench-Hammer)", "cur": 130, "max": 130, "grade": 5}
            },
            "feats": [],
            "spells": [],
            "active_abilities": [],
            "factions": {"iron_syndicate": 30, "vanguard_coalition": 20},
            "homestead": {
                "owned": False,
                "vault_tier": 1,
                "greenhouse_tier": 1,
                "has_master_anvil": False,
                "mounted_trophies": [],
                "vault_items": [],
                "vault_col": 0,
                "last_harvest_day": 0
            },
            "chrono": {
                "day": 1,
                "hour": 10,
                "minute": 0,
                "weather": "clear_skies",
                "active_buffs": []
            }
        }

    def test_homestead_purchase_and_upgrades(self):
        # 1. Insufficient Col check
        p_poor = copy.deepcopy(self.player)
        p_poor["col"] = 500
        res_fail = mechanics.purchase_homestead(p_poor)
        self.assertFalse(res_fail["success"])
        self.assertIn("Insufficient Col", res_fail["message"])

        # 2. Successful purchase (3,500 Col)
        p = copy.deepcopy(self.player)
        res_buy = mechanics.purchase_homestead(p)
        self.assertTrue(res_buy["success"])
        self.assertTrue(p["homestead"]["owned"])
        self.assertEqual(p["col"], 6500)

        # 3. Upgrade Vault: Tier 1 -> Tier 2 (2,000 Col)
        res_v2 = mechanics.upgrade_homestead_facility(p, "vault")
        self.assertTrue(res_v2["success"])
        self.assertEqual(p["homestead"]["vault_tier"], 2)
        self.assertEqual(p["col"], 4500)

        # Upgrade Vault: Tier 2 -> Tier 3 (5,000 Col)
        p["col"] = 5000
        res_v3 = mechanics.upgrade_homestead_facility(p, "vault")
        self.assertTrue(res_v3["success"])
        self.assertEqual(p["homestead"]["vault_tier"], 3)
        self.assertEqual(p["col"], 0)

        # Attempting beyond Tier 3 fails
        res_v4 = mechanics.upgrade_homestead_facility(p, "vault")
        self.assertFalse(res_v4["success"])

        # 4. Upgrade Greenhouse
        p["col"] = 5000
        res_g2 = mechanics.upgrade_homestead_facility(p, "greenhouse")
        self.assertTrue(res_g2["success"])
        self.assertEqual(p["homestead"]["greenhouse_tier"], 2)

        # 5. Construct Master-Anvil (3,000 Col)
        p["col"] = 5000
        res_anvil = mechanics.upgrade_homestead_facility(p, "master_anvil")
        self.assertTrue(res_anvil["success"])
        self.assertTrue(p["homestead"]["has_master_anvil"])
        self.assertEqual(p["col"], 2000)

    def test_vault_col_and_item_operations(self):
        p = copy.deepcopy(self.player)
        mechanics.purchase_homestead(p)
        
        # Col Deposit
        dep_res = mechanics.deposit_to_vault(p, "", col_amount=2000)
        self.assertTrue(dep_res["success"])
        self.assertEqual(p["homestead"]["vault_col"], 2000)
        self.assertEqual(p["col"], 4500)

        # Col Withdrawal
        wdr_res = mechanics.withdraw_from_vault(p, "", col_amount=500)
        self.assertTrue(wdr_res["success"])
        self.assertEqual(p["homestead"]["vault_col"], 1500)
        self.assertEqual(p["col"], 5000)

        # Item Deposit
        # Deposit 5x Refined Aether-Alloy
        item_dep = mechanics.deposit_to_vault(p, "Refined Aether-Alloy", qty=5)
        self.assertTrue(item_dep["success"])
        self.assertEqual(len(p["homestead"]["vault_items"]), 1)
        self.assertEqual(p["homestead"]["vault_items"][0]["qty"], 5)
        
        # Remaining in player inventory should be 5
        inv_alloy = next(it for it in p["inventory"] if "Refined Aether-Alloy" in it["name"])
        self.assertEqual(inv_alloy["qty"], 5)

        # Item Withdrawal
        item_wdr = mechanics.withdraw_from_vault(p, "Refined Aether-Alloy", qty=2)
        self.assertTrue(item_wdr["success"])
        self.assertEqual(p["homestead"]["vault_items"][0]["qty"], 3)
        self.assertEqual(inv_alloy["qty"], 7)

    def test_trophy_mounting_and_passive_buffs(self):
        p = copy.deepcopy(self.player)
        # Attempt before purchase fails
        fail_unowned = mechanics.mount_boss_trophy(p, "Overlord's Gilded Core")
        self.assertFalse(fail_unowned["success"])

        mechanics.purchase_homestead(p)

        # Mount Overlord Core
        mount_res = mechanics.mount_boss_trophy(p, "Overlord's Gilded Core")
        self.assertTrue(mount_res["success"])
        self.assertEqual(len(p["homestead"]["mounted_trophies"]), 1)
        self.assertTrue(any("[Aegis of the Spire]" in str(f) for f in p["feats"]))

        # Active trophy buffs query
        buffs = mechanics.get_active_trophy_buffs(p)
        self.assertEqual(len(buffs), 1)
        self.assertEqual(buffs[0]["buff_name"], "[Aegis of the Spire]")

        # Duplicate mount fails
        dup_res = mechanics.mount_boss_trophy(p, "Overlord's Gilded Core")
        self.assertFalse(dup_res["success"])

        # Unmount trophy
        unm_res = mechanics.unmount_boss_trophy(p, "gilded_overlord_core")
        self.assertTrue(unm_res["success"])
        self.assertEqual(len(p["homestead"]["mounted_trophies"]), 0)
        self.assertFalse(any("[Aegis of the Spire]" in str(f) for f in p["feats"]))

    def test_alchemical_greenhouse_harvesting(self):
        p = copy.deepcopy(self.player)
        mechanics.purchase_homestead(p)

        # Day 1 Harvest
        h_res = mechanics.harvest_alchemical_garden(p)
        self.assertTrue(h_res["success"])
        self.assertEqual(h_res["day"], 1)
        self.assertEqual(p["homestead"]["last_harvest_day"], 1)

        # Same Day second harvest blocked
        h_fail = mechanics.harvest_alchemical_garden(p)
        self.assertFalse(h_fail["success"])
        self.assertIn("already harvested today", h_fail["message"])

        # Advance to Day 2
        mechanics.advance_game_time(p, minutes=1440)
        self.assertEqual(p["chrono"]["day"], 2)

        # Day 2 Harvest succeeds
        h_res2 = mechanics.harvest_alchemical_garden(p)
        self.assertTrue(h_res2["success"])
        self.assertEqual(h_res2["day"], 2)

    def test_commodity_market_trading(self):
        p = copy.deepcopy(self.player)
        prices = mechanics.get_commodity_prices(p)
        self.assertIn("refined_aether_alloy", prices)
        self.assertIn("scrap_metal", prices)

        # Buy 2x Scrap Metal
        scrap_price = prices["scrap_metal"]["buy_price"]
        init_col = p["col"]
        b_res = mechanics.trade_commodity(p, "scrap_metal", action="buy", qty=2)
        self.assertTrue(b_res["success"])
        self.assertEqual(p["col"], init_col - (scrap_price * 2))
        
        # Verify item in inventory
        scrap_item = next((it for it in p["inventory"] if "Scrap Metal & Wiring" in it["name"]), None)
        self.assertIsNotNone(scrap_item)
        self.assertEqual(scrap_item["qty"], 2)

        # Sell 1x Scrap Metal
        sell_price = prices["scrap_metal"]["sell_price"]
        s_res = mechanics.trade_commodity(p, "scrap_metal", action="sell", qty=1)
        self.assertTrue(s_res["success"])
        self.assertEqual(scrap_item["qty"], 1)
        self.assertEqual(p["col"], init_col - (scrap_price * 2) + sell_price)

    def test_grade_6_mythic_forging(self):
        p = copy.deepcopy(self.player)
        mechanics.purchase_homestead(p)

        # Fails without Master-Anvil
        fail_anvil = mechanics.forge_mythic_equipment(p, "fenrirs_howl")
        self.assertFalse(fail_anvil["success"])
        self.assertIn("Master-Anvil", fail_anvil["message"])

        # Install Master-Anvil
        mechanics.upgrade_homestead_facility(p, "master_anvil")

        # Forge Fenrir's Howl (Grade 6 Mythic Axe)
        # Requirements: Fenrir's Tusk, Overlord Core, 2x Aether-Alloy, 1x Carbon Line Spools, 2000 Col
        init_col = p["col"]
        forge_res = mechanics.forge_mythic_equipment(p, "fenrirs_howl")
        self.assertTrue(forge_res["success"])
        self.assertEqual(forge_res["grade"], 6)
        self.assertEqual(p["col"], init_col - 2000)

        # Check equipped / durability
        self.assertEqual(p["equipped"]["main_hand"], "Fenrir's Howl (Grade 6 Mythic Great-Axe)")
        self.assertEqual(p["gear_durability"]["main_hand"]["cur"], 350)
        self.assertEqual(p["gear_durability"]["main_hand"]["grade"], 6)

        # Check granted technique
        self.assertTrue(any("Crystalline Frost Wave" in s for s in p["spells"]))
        self.assertTrue(mechanics.is_ability_slotted(p, "Crystalline Frost Wave"))

        # Verify materials consumed
        alloy = next(it for it in p["inventory"] if "Refined Aether-Alloy" in it["name"])
        self.assertEqual(alloy["qty"], 8) # Started with 10, consumed 2

if __name__ == "__main__":
    unittest.main()
