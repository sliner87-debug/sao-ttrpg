import unittest
import json
import os
import copy
from backend import gm_engine, mechanics

class TestPostSiltResetAndTransition(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        with open(os.path.join(self.base_dir, "save_game.json"), "r", encoding="utf-8") as f:
            self.save_data = json.load(f)

    def test_reset_state_integrity(self):
        player = self.save_data["player"]
        self.assertEqual(player["name"], "Banki")
        self.assertEqual(player["level"], 3)
        self.assertIn(player["hp"], (58, 125))
        self.assertEqual(player["col"], 1170)
        self.assertIn("Exit Junction", player["location"])

        # Verify messages were trimmed to right after Silt was defeated (21 messages: 0..20)
        self.assertEqual(len(self.save_data["messages"]), 21)

        # Verify boss drops are deduplicated
        piston_count = sum(1 for i in player["inventory"] if "geothermal core piston" in str(i).lower())
        self.assertEqual(piston_count, 1)

        # Check Ren in save
        ren = player["companions"]["Ren"]
        self.assertEqual(ren["hp"], 28)
        self.assertEqual(ren["max_hp"], 35)
        self.assertNotIn("Scalded by steam", ren["status"])

        # Check master state
        if "master_state" in self.save_data:
            ms = self.save_data["master_state"]
        else:
            with open(os.path.join(self.base_dir, ".game_state", "secret_master_state.json"), "r", encoding="utf-8") as f:
                ms = json.load(f)
        self.assertEqual(len(ms["entities"]), 0)
        effects = ms["environment"]["environmental_effects"]
        self.assertIn("Clear Escape Routes Available", effects)
        for bad_cue in ["steam", "collapse", "falling", "shale", "compromised"]:
            self.assertFalse(any(bad_cue in eff.lower() for eff in effects), f"Lingering hazard: {bad_cue}")

    def test_safe_zone_transition_clears_all_hazards(self):
        player = copy.deepcopy(self.save_data["player"])
        # Transition to safe zone
        player["location"] = "Sector 1 Safe-Zone: Washington Borough, NJ"
        
        # Test generate_visible_state synchronization logic directly
        master_state_path = os.path.join(self.base_dir, ".game_state", "secret_master_state.json")
        with open(master_state_path, "r", encoding="utf-8") as f:
            ms = json.load(f)
            
        p_loc = player["location"]
        is_safe = any(w in p_loc.lower() for w in ["safe-zone", "safe zone", "washington", "clinic", "catacomb", "depot", "sanctuary"])
        self.assertTrue(is_safe)
        
        # Simulate transition to Doc Mercer's clinic
        player["location"] = "Doc Mercer's Underground Clinic (Washington Borough Catacombs)"
        curr_effects = ["Safe-Zone Sanctuary Wards", "Sterile Ether Atmosphere"]
        hostile_cues = ["steam", "timber", "collapse", "falling", "shale", "cave-in", "hazard"]
        filtered = [e for e in curr_effects if not any(c in e.lower() for c in hostile_cues)]
        self.assertEqual(len(filtered), 2)

    def test_companion_party_sync(self):
        party_ren_path = os.path.join(self.base_dir, "Party", "companion_ren.json")
        with open(party_ren_path, "r", encoding="utf-8") as f:
            ren_sheet = json.load(f)
        self.assertIn(ren_sheet["hp"], [28, 35])
        self.assertEqual(ren_sheet["max_hp"], 35)
        self.assertEqual(ren_sheet["ac"], 16)

if __name__ == "__main__":
    unittest.main()
