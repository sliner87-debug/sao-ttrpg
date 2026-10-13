"""
Test suite for Decoupled V2 GM Engine & Persona Engine:
Validates visible room generation, autonomous actor queuing, and turn resolution.
"""

import json
import os
import unittest
from unittest.mock import patch, MagicMock

import backend.gm_engine as gm_engine
import backend.persona_engine as persona_engine
from backend.schemas import VisibleRoomSchema, ActorActionSchema, TurnResolutionSchema

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class TestDecoupledPipeline(unittest.TestCase):
    def setUp(self):
        self.master_state_path = os.path.join(BASE_DIR, ".game_state", "secret_master_state.json")
        self.visible_room_path = os.path.join(BASE_DIR, "Staging_Ground", "visible_room.json")
        self.queue_path = os.path.join(BASE_DIR, "Staging_Ground", "action_queue.json")
        self.ren_sheet_path = os.path.join(BASE_DIR, "Party", "companion_ren.json")

        # Snapshot existing files to restore after tests
        self.original_master = self._read_json(self.master_state_path)
        self.original_visible = self._read_json(self.visible_room_path)
        self.original_queue = self._read_json(self.queue_path)
        self.original_ren = self._read_json(self.ren_sheet_path)

    def tearDown(self):
        # Restore original states
        if self.original_master is not None:
            self._write_json(self.master_state_path, self.original_master)
        if self.original_visible is not None:
            self._write_json(self.visible_room_path, self.original_visible)
        if self.original_queue is not None:
            self._write_json(self.queue_path, self.original_queue)
        if self.original_ren is not None:
            self._write_json(self.ren_sheet_path, self.original_ren)

    def _read_json(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def _write_json(self, path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    @patch("google.genai.Client")
    def test_generate_visible_state(self, mock_client_cls):
        """Validates that GM engine strips secret mechanics and writes visible_room.json."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_visible_data = {
            "turn_number": 1,
            "environment": {
                "location": "Oxford Mine Adits - Lower Collapse Zone",
                "description": "Splintered oak supports creak under weight. Geothermal steam hisses from fissures.",
                "environmental_effects": ["Dim Light", "Superheated Steam Venting"]
            },
            "entities": [
                {
                    "id": "enemy_01",
                    "name": "Silt-Marrow the Unhewn",
                    "type": "hostile",
                    "status": ["Critically Compromised", "Exposed Core"]
                }
            ]
        }
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_visible_data)
        mock_client.models.generate_content.return_value = mock_response

        # Test execution
        result = gm_engine.generate_visible_state("mock_api_key")

        self.assertEqual(result["turn_number"], 1)
        self.assertEqual(len(result["entities"]), 1)
        self.assertEqual(result["entities"][0]["name"], "Silt-Marrow the Unhewn")
        # Ensure exact HP and secret intents are absent
        self.assertNotIn("hp", result["entities"][0])
        self.assertNotIn("intent", result["entities"][0])

        # Verify disk write to visible_room.json
        disk_room = self._read_json(self.visible_room_path)
        self.assertIsNotNone(disk_room)
        self.assertEqual(disk_room["turn_number"], 1)

    @patch("google.genai.Client")
    def test_autonomous_actor_loop(self, mock_client_cls):
        """Validates that SubAgents generate thoughts and intended actions into action_queue.json."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_action = {
            "actor_id": "companion_ren",
            "intended_action": "Fire a focused kinetic bolt from Aether-Lock Carbine at enemy core.",
            "target": "enemy_01",
            "internal_thought": "Its chassis is cracked at the seam. One clean shot will crack the geothermal casing!"
        }
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_action)
        mock_client.models.generate_content.return_value = mock_response

        visible_room = {
            "turn_number": 1,
            "environment": {
                "location": "Oxford Mine Adits",
                "description": "Narrow mine shaft.",
                "environmental_effects": ["Dim Light"]
            },
            "entities": [
                {
                    "id": "enemy_01",
                    "name": "Silt-Marrow",
                    "type": "hostile",
                    "status": ["Exposed Core"]
                }
            ]
        }

        actions = persona_engine.run_all_room_subagents("mock_api_key", visible_room)
        self.assertGreaterEqual(len(actions), 1)
        self.assertEqual(actions[0]["actor_id"], "companion_ren")
        self.assertIn("Aether-Lock Carbine", actions[0]["intended_action"])
        self.assertIn("internal_thought", actions[0])

        # Verify staged queue on disk
        disk_queue = self._read_json(self.queue_path)
        self.assertIsNotNone(disk_queue)
        self.assertGreaterEqual(len(disk_queue), 1)

    @patch("google.genai.Client")
    def test_gm_turn_resolution_and_state_synchronization(self, mock_client_cls):
        """Validates that resolve_turn synthesizes player + AI queue, updates HP, and flushes queue."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Seed mock master state and action queue
        test_master = {
            "campaign_name": "Test_Campaign",
            "turn_number": 5,
            "environment": {
                "location": "Oxford Mine Adits",
                "description": "Mine shaft.",
                "hidden_traps": ["Tripwire"],
                "environmental_effects": []
            },
            "entities": [
                {
                    "id": "enemy_01",
                    "name": "Silt-Marrow the Unhewn",
                    "type": "hostile",
                    "hp": 20,
                    "max_hp": 45,
                    "ac": 14,
                    "status": ["Intact"]
                }
            ],
            "players": ["player", "companion_ren"]
        }
        self._write_json(self.master_state_path, test_master)

        queued_actions = [
            {
                "actor_id": "companion_ren",
                "intended_action": "Fire radiant bolt at Silt-Marrow",
                "target": "enemy_01",
                "internal_thought": "Keep it off Banki!",
                "actor_name": "Ren"
            }
        ]
        self._write_json(self.queue_path, queued_actions)

        mock_resolution = {
            "narrative_recap": "Banki slams his broadaxe down into the golem while Ren's radiant carbine punctures its seam.",
            "combat_logs": [
                "Banki Attack: 1d20+6 = 18 vs AC 14 | Hit!",
                "Banki Damage: 1d12+4 = 10 Slashing",
                "Ren Attack: 1d20+5 = 19 vs AC 14 | Hit!",
                "Ren Damage: 1d10+3 = 8 Radiant"
            ],
            "hp_changes": [
                {"entity_id": "enemy_01", "hp_delta": -18},
                {"entity_id": "companion_ren", "hp_delta": -2}
            ],
            "status_updates": [
                {"entity_id": "enemy_01", "statuses": ["Critically Compromised", "Exposed Core"]}
            ],
            "encounter_active": True,
            "global_news_add": ["Warren County Barony reinforces patrols."],
            "weather": "clear",
            "time_of_day": "day",
            "player_state_updates": {
                "xp_change": 100,
                "col_change": 25,
                "inventory_add": ["Basalt Carapace Fragment"],
                "inventory_remove": [],
                "hp_change": 0
            }
        }
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_resolution)
        mock_client.models.generate_content.return_value = mock_response

        # Execute resolution
        result = gm_engine.resolve_turn("mock_api_key", "I charge forward and strike with my broadaxe!")

        # 1. Check returned structure
        self.assertIn("narrative_recap", result)
        self.assertIn("combat_logs", result)
        self.assertIsInstance(result["hp_changes"], dict)
        self.assertEqual(result["hp_changes"]["enemy_01"], -18)
        self.assertEqual(result["hp_changes"]["companion_ren"], -2)

        # 2. Check master state updated on disk
        updated_master = self._read_json(self.master_state_path)
        self.assertEqual(updated_master["turn_number"], 6)
        enemy_entity = next(e for e in updated_master["entities"] if e["id"] == "enemy_01")
        self.assertEqual(enemy_entity["hp"], 2) # 20 - 18 = 2
        self.assertIn("Critically Compromised", enemy_entity["status"])

        # 3. Check action queue cleared on disk
        cleared_queue = self._read_json(self.queue_path)
        self.assertEqual(cleared_queue, [])

        # 4. Check companion Ren HP updated in Party/companion_ren.json
        updated_ren = self._read_json(self.ren_sheet_path)
        self.assertIsNotNone(updated_ren)
        self.assertEqual(updated_ren["hp"], max(0, min(updated_ren["max_hp"], self.original_ren.get("hp", 35) - 2)))


if __name__ == "__main__":
    unittest.main()
