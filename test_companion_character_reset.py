"""
Unit and Integration Tests for Companion Reset and Character Isolation
Verifies that companions (especially Ren Sasaki) are reset to their default 'New' state
when interacting with a newly created Player Character, and that multiple characters
maintain isolated companion progression without state bleed.
"""

import os
import json
import shutil
import tempfile
import unittest

import backend.mechanics as mechanics
import backend.character_generator as cg

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class TestCompanionCharacterReset(unittest.TestCase):
    def setUp(self):
        # Create an isolated temporary directory simulating the game root
        self.test_dir = tempfile.mkdtemp()
        self.party_dir = os.path.join(self.test_dir, "Party")
        self.entities_dir = os.path.join(self.test_dir, "Entities")
        self.saves_dir = os.path.join(self.test_dir, "saves")
        os.makedirs(self.party_dir, exist_ok=True)
        os.makedirs(self.entities_dir, exist_ok=True)
        os.makedirs(self.saves_dir, exist_ok=True)

        # Copy existing Party and Entities files as baseline fixtures
        real_party = os.path.join(BASE_DIR, "Party")
        if os.path.exists(real_party):
            for f in os.listdir(real_party):
                if f.endswith(".json"):
                    shutil.copy2(os.path.join(real_party, f), os.path.join(self.party_dir, f))

        real_entities = os.path.join(BASE_DIR, "Entities")
        if os.path.exists(real_entities):
            for f in os.listdir(real_entities):
                if f.endswith(".json"):
                    shutil.copy2(os.path.join(real_entities, f), os.path.join(self.entities_dir, f))

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_default_ren_canonical_state(self):
        """Verifies build_default_companion_ren produces pristine canonical Level 3 stats."""
        ren = mechanics.build_default_companion_ren("Alice")
        self.assertEqual(ren["name"], "Ren Sasaki")
        self.assertEqual(ren["hp"], 35)
        self.assertEqual(ren["max_hp"], 35)
        self.assertEqual(ren["ac"], 16)
        self.assertEqual(ren["affinity"], 35)
        self.assertEqual(ren["affinity_tier"], "Ally")
        self.assertTrue(ren["recruited"])
        self.assertTrue(ren["active"])
        self.assertEqual(ren["stance"], "overwatch_hacking")
        self.assertEqual(ren["subroutine_stage"], 0)
        self.assertEqual(ren["ocular_kernel"], "Serpent-Script (Ouroboros Kernel v3.14)")
        self.assertEqual(ren["subroutine_metadata"]["stage"], 0)
        self.assertEqual(ren["subroutine_metadata"]["subroutine_id"], "ren_diag_v2.py")

        # Inventory at pristine max durability
        inv_map = {item["name"]: item for item in ren["inventory"]}
        self.assertIn("Aether-Lock Carbine", inv_map)
        self.assertEqual(inv_map["Aether-Lock Carbine"]["durability"], 50)
        self.assertEqual(inv_map["Aether-Lock Carbine"]["max_durability"], 50)
        self.assertIn("Runic Vanguard Blade", inv_map)
        self.assertEqual(inv_map["Runic Vanguard Blade"]["durability"], 150)
        self.assertIn("Midnight-Blue Leyline Duster", inv_map)
        self.assertEqual(inv_map["Midnight-Blue Leyline Duster"]["durability"], 100)

        # Behavior prompt must refer to Alice and lore elements, with NO Banki
        prompt = ren["behavior_prompt"]
        self.assertIn("Alice", prompt)
        self.assertNotIn("Banki", prompt)
        self.assertIn("17-year-old", prompt)
        self.assertIn("not gunpowder", prompt.lower())
        self.assertIn("mana bolts", prompt.lower())
        self.assertIn("ren_diag_v2.py", prompt)
        self.assertIn("Serpent-Script (Ouroboros Kernel v3.14)", prompt)

    def test_default_ren_entity_persona(self):
        """Verifies build_default_companion_ren_entity formats persona with player name."""
        entity = mechanics.build_default_companion_ren_entity("David")
        self.assertEqual(entity["id"], "companion_ren")
        self.assertEqual(entity["name"], "Ren")
        self.assertIn("David", entity["backstory_interview"])
        self.assertNotIn("Banki", entity["backstory_interview"])
        self.assertIn("David", entity["personality"])
        self.assertIn("David", entity["dreams_and_desires"])
        self.assertIn("David", entity["tactical_style"])
        self.assertIn("David", entity["behavior_prompt"])
        self.assertIn("not gunpowder", entity["behavior_prompt"].lower())

    def test_reset_companion_roster_clears_dirty_state(self):
        """Verifies that dirty companion state from previous gameplay is wiped clean."""
        # 1. Dirty up the active party files
        dirty_ren_path = os.path.join(self.party_dir, "companion_ren.json")
        with open(dirty_ren_path, "r", encoding="utf-8") as f:
            dirty_ren = json.load(f)
        dirty_ren["hp"] = 12  # severely damaged
        dirty_ren["subroutine_stage"] = 4  # late-game stage
        dirty_ren["affinity"] = 85
        dirty_ren["behavior_prompt"] = "Loyal to Banki forever."
        with open(dirty_ren_path, "w", encoding="utf-8") as f:
            json.dump(dirty_ren, f, indent=4)

        # Dirty up another companion (e.g. Titus)
        dirty_titus_path = os.path.join(self.party_dir, "companion_titus.json")
        if os.path.exists(dirty_titus_path):
            with open(dirty_titus_path, "r", encoding="utf-8") as f:
                dirty_titus = json.load(f)
            dirty_titus["hp"] = 20
            dirty_titus["recruited"] = True
            dirty_titus["active"] = True
            dirty_titus["active_debuffs"] = [{"name": "Armor Melt", "ac_penalty": -4}]
            with open(dirty_titus_path, "w", encoding="utf-8") as f:
                json.dump(dirty_titus, f, indent=4)

        # 2. Reset companion roster for a new character "Kaelen"
        new_char_sheet = {"name": "Kaelen", "level": 1, "hp": 100, "max_hp": 100}
        fresh_roster = mechanics.reset_companion_roster_for_character(self.test_dir, "Kaelen", new_char_sheet)

        # 3. Verify Ren was reset on disk
        with open(dirty_ren_path, "r", encoding="utf-8") as f:
            reset_ren = json.load(f)
        self.assertEqual(reset_ren["hp"], 35)
        self.assertEqual(reset_ren["max_hp"], 35)
        self.assertEqual(reset_ren["subroutine_stage"], 0)
        self.assertIn("Kaelen", reset_ren["behavior_prompt"])
        self.assertNotIn("Banki", reset_ren["behavior_prompt"])

        # 4. Verify Ren was reset in character sheet
        self.assertEqual(new_char_sheet["ren_subroutine_stage"], 0)
        self.assertEqual(new_char_sheet["companions"]["Ren"]["hp"], 35)
        self.assertEqual(new_char_sheet["companions"]["Ren"]["affinity"], 35)
        self.assertEqual(new_char_sheet["companions"]["Ren"]["subroutine_stage"], 0)
        self.assertTrue(new_char_sheet["party"]["companions"]["Ren"]["active"])

        # 5. Verify Titus was reset to unrecruited and full health
        if os.path.exists(dirty_titus_path):
            with open(dirty_titus_path, "r", encoding="utf-8") as f:
                reset_titus = json.load(f)
            self.assertFalse(reset_titus.get("recruited", False))
            self.assertFalse(reset_titus.get("active", False))
            self.assertEqual(reset_titus.get("hp"), reset_titus.get("max_hp"))
            self.assertEqual(reset_titus.get("active_debuffs"), [])

    def test_character_generator_initializes_clean_companions(self):
        """Verifies generate_starting_character automatically initializes pristine companion state."""
        char = cg.generate_starting_character(
            name="Aria",
            point_alloc={"STR": 2, "DEX": 6, "CON": 4, "INT": 4, "WIS": 2, "CHA": 2},
            background_key="software_engineer",
            race_key="pure_human",
            class_key="pathless",
            relic_key="smartphone"
        )
        self.assertEqual(char["name"], "Aria")
        self.assertIn("companions", char)
        self.assertIn("Ren", char["companions"])
        ren = char["companions"]["Ren"]
        self.assertEqual(ren["hp"], 35)
        self.assertEqual(ren["max_hp"], 35)
        self.assertEqual(ren["affinity"], 35)
        self.assertEqual(ren["affinity_tier"], "Ally")
        self.assertEqual(ren["subroutine_stage"], 0)
        self.assertEqual(char.get("ren_subroutine_stage"), 0)
        self.assertIn("Aria", ren.get("behavior_prompt", ""))

    def test_multi_character_companion_isolation(self):
        """Verifies that switching between Character A and Character B preserves each character's companions."""
        # 1. Character A ("Alice") starts and progresses with Ren
        alice_sheet = {"name": "Alice", "level": 2, "hp": 110, "max_hp": 110}
        mechanics.reset_companion_roster_for_character(self.test_dir, "Alice", alice_sheet)

        # Alice damages Ren in combat to 20 HP, advances affinity to 65, subroutine stage to 2
        ren_party_path = os.path.join(self.party_dir, "companion_ren.json")
        with open(ren_party_path, "r", encoding="utf-8") as f:
            alice_ren = json.load(f)
        alice_ren["hp"] = 20
        alice_ren["subroutine_stage"] = 2
        with open(ren_party_path, "w", encoding="utf-8") as f:
            json.dump(alice_ren, f, indent=4)
        alice_sheet["companions"]["Ren"]["hp"] = 20
        alice_sheet["companions"]["Ren"]["affinity"] = 65
        alice_sheet["ren_subroutine_stage"] = 2

        # Save Alice's party to saves/Alice/Party/
        mechanics.save_party_to_character_folder(self.test_dir, "Alice")

        # 2. Character B ("Bob") is created
        bob_sheet = {"name": "Bob", "level": 1, "hp": 100, "max_hp": 100}
        mechanics.reset_companion_roster_for_character(self.test_dir, "Bob", bob_sheet)

        # Verify active Party/companion_ren.json is Bob's: 35 HP, Stage 0, refers to Bob
        with open(ren_party_path, "r", encoding="utf-8") as f:
            active_ren = json.load(f)
        self.assertEqual(active_ren["hp"], 35)
        self.assertEqual(active_ren["subroutine_stage"], 0)
        self.assertIn("Bob", active_ren["behavior_prompt"])
        self.assertNotIn("Alice", active_ren["behavior_prompt"])

        # Bob takes 5 damage on Ren (Ren HP = 30)
        active_ren["hp"] = 30
        with open(ren_party_path, "w", encoding="utf-8") as f:
            json.dump(active_ren, f, indent=4)
        bob_sheet["companions"]["Ren"]["hp"] = 30
        mechanics.save_party_to_character_folder(self.test_dir, "Bob")

        # 3. Switch back to Alice: restore Alice's party
        mechanics.restore_companions_for_character(self.test_dir, "Alice", alice_sheet)
        with open(ren_party_path, "r", encoding="utf-8") as f:
            restored_alice_ren = json.load(f)
        self.assertEqual(restored_alice_ren["hp"], 20)
        self.assertEqual(restored_alice_ren["subroutine_stage"], 2)
        self.assertIn("Alice", restored_alice_ren["behavior_prompt"])

        # 4. Switch back to Bob: restore Bob's party
        mechanics.restore_companions_for_character(self.test_dir, "Bob", bob_sheet)
        with open(ren_party_path, "r", encoding="utf-8") as f:
            restored_bob_ren = json.load(f)
        self.assertEqual(restored_bob_ren["hp"], 30)
        self.assertEqual(restored_bob_ren["subroutine_stage"], 0)
        self.assertIn("Bob", restored_bob_ren["behavior_prompt"])

if __name__ == "__main__":
    unittest.main()
