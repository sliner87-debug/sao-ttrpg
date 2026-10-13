"""
Test Suite for Safe-Zone Transition, Staging Ground Hazard Purging,
and Scene Image Generation in V2.
"""

import json
import os
import unittest
from unittest.mock import patch, MagicMock

import backend.gm_engine as gm_engine
import backend.persona_engine as persona_engine

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class TestSafeZoneTransitionAndImaging(unittest.TestCase):
    def setUp(self):
        self.master_state_path = os.path.join(BASE_DIR, ".game_state", "secret_master_state.json")
        self.visible_room_path = os.path.join(BASE_DIR, "Staging_Ground", "visible_room.json")
        self.queue_path = os.path.join(BASE_DIR, "Staging_Ground", "action_queue.json")
        self.ren_sheet_path = os.path.join(BASE_DIR, "Party", "companion_ren.json")

        self.original_master = self._read_json(self.master_state_path)
        self.original_visible = self._read_json(self.visible_room_path)
        self.original_queue = self._read_json(self.queue_path)
        self.original_ren = self._read_json(self.ren_sheet_path)

    def tearDown(self):
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
    def test_safe_zone_transition_purges_dungeon_hazards(self, mock_client_cls):
        """Validates that entering Doc Mercer's clinic purges mine hazards and adds Doc Mercer."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Seed master state stuck in Oxford Mine with falling timbers and dead boss
        stuck_master = {
            "campaign_name": "SAO_Sandbox",
            "turn_number": 19,
            "environment": {
                "location": "Oxford Mine Adits - Lower Collapse Zone",
                "description": "Splintered oak supports creak under immense weight. Geothermal steam hisses from floor fissures.",
                "hidden_traps": ["Tripwire at X:5 Y:5"],
                "environmental_effects": [
                    "Dim Light",
                    "Superheated Steam Venting",
                    "Compromised Timber Bracing"
                ]
            },
            "entities": [
                {
                    "id": "enemy_01",
                    "name": "Silt-Marrow the Unhewn",
                    "type": "hostile",
                    "hp": 0,
                    "max_hp": 45,
                    "ac": 14,
                    "status": ["Shattered"],
                    "intent": "Bring the ceiling down"
                }
            ],
            "players": ["player", "companion_ren"]
        }
        self._write_json(self.master_state_path, stuck_master)

        # Mock visible room generation response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "turn_number": 20,
            "environment": {
                "location": "Doc Mercer's Underground Clinic (Washington Borough Catacombs)",
                "description": "Vaulted stone catacombs with surgical dissection tables and flickering mana lamps.",
                "environmental_effects": ["Safe-Zone Sanctuary Wards", "Sterile Ether Atmosphere"]
            },
            "entities": [
                {
                    "id": "npc_doc_mercer",
                    "name": "Doc Mercer",
                    "type": "neutral",
                    "status": ["Attentive", "Preparing Surgical Tools"]
                }
            ]
        })
        mock_client.models.generate_content.return_value = mock_response

        # Player is now in Doc Mercer's clinic
        player_state = {
            "name": "Banki",
            "location": "Doc Mercer's Underground Clinic (Washington Borough Catacombs)"
        }

        # Call generate_visible_state with player_state
        visible_room = gm_engine.generate_visible_state(api_key="mock_key", player_state=player_state)

        # Verify master state on disk was synchronized
        synced_master = self._read_json(self.master_state_path)
        self.assertIn("Doc Mercer's Underground Clinic", synced_master["environment"]["location"])
        self.assertEqual(synced_master["environment"]["hidden_traps"], [])
        
        # Verify no cave-in / timber hazards remain
        for eff in synced_master["environment"]["environmental_effects"]:
            self.assertNotIn("steam", eff.lower())
            self.assertNotIn("timber", eff.lower())
            self.assertNotIn("collapse", eff.lower())

        # Verify dead hostile Silt-Marrow is removed and Doc Mercer is present
        entity_ids = [e["id"] for e in synced_master["entities"]]
        self.assertNotIn("enemy_01", entity_ids)
        self.assertIn("npc_doc_mercer", entity_ids)

    @patch("google.genai.Client")
    def test_resolve_turn_environment_and_cleared_entities_sync(self, mock_client_cls):
        """Validates that resolve_turn updates environment, clears dead entities, and exposes image_prompt."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Seed initial combat state
        initial_master = {
            "campaign_name": "SAO_Sandbox",
            "turn_number": 35,
            "environment": {
                "location": "Oxford Mine Adits - Lower Collapse Zone",
                "description": "Mine tunnel collapsing.",
                "hidden_traps": [],
                "environmental_effects": ["Falling Shale"]
            },
            "entities": [
                {
                    "id": "enemy_01",
                    "name": "Silt-Marrow",
                    "type": "hostile",
                    "hp": 0,
                    "max_hp": 45,
                    "ac": 14,
                    "status": ["Defeated"]
                }
            ],
            "players": ["player", "companion_ren"]
        }
        self._write_json(self.master_state_path, initial_master)

        mock_resolution = {
            "narrative_recap": "Banki and Ren emerge into Washington Borough and descend into Doc Mercer's clinic.",
            "combat_logs": ["Transitioning from Oxford Mine to Washington Borough Catacombs."],
            "hp_changes": [],
            "status_updates": [],
            "encounter_active": False,
            "environment_update": {
                "location": "Doc Mercer's Underground Clinic (Washington Borough Catacombs)",
                "description": "Vaulted stone catacombs with surgical dissection tables.",
                "environmental_effects": ["Safe-Zone Sanctuary Wards", "Sterile Ether Atmosphere"]
            },
            "cleared_entities": ["enemy_01"],
            "new_entities": [
                {
                    "id": "npc_doc_mercer",
                    "name": "Doc Mercer",
                    "type": "neutral",
                    "hp": 40,
                    "max_hp": 40,
                    "ac": 12,
                    "status": ["Attentive"],
                    "intent": "Consult on biological graft surgery."
                }
            ],
            "image_prompt": "Banki, a burly rugged Nordic warrior with black-iron rune armor and wolf mantle, standing in Doc Mercer's vaulted subterranean clinic while Ren holds his MageTech caster carbine.",
            "global_news_add": ["Warren County Barony declares Sector 1 safe."],
            "player_state_updates": {
                "location": "Doc Mercer's Underground Clinic (Washington Borough Catacombs)",
                "col_change": 75,
                "xp_change": 250
            }
        }
        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_resolution)
        mock_client.models.generate_content.return_value = mock_response

        # Execute resolution
        result = gm_engine.resolve_turn("mock_key", "Let's head to Doc Mercer's clinic.")

        # Check result dictionary
        self.assertEqual(result["image_prompt"], mock_resolution["image_prompt"])
        self.assertFalse(result["encounter_active"])

        # Check master state updated on disk
        updated_master = self._read_json(self.master_state_path)
        self.assertIn("Doc Mercer's Underground Clinic", updated_master["environment"]["location"])
        self.assertEqual(updated_master["turn_number"], 36)
        
        # Verify enemy_01 removed and Doc Mercer added
        entity_ids = [e["id"] for e in updated_master["entities"]]
        self.assertNotIn("enemy_01", entity_ids)
        self.assertIn("npc_doc_mercer", entity_ids)

    @patch("google.genai.Client")
    def test_generate_scene_image_prompt_and_fallback(self, mock_client_cls):
        """Validates generate_scene_image calls Gemini image model with dark anime prefix."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_inline_data = MagicMock()
        mock_inline_data.data = b"FAKE_IMAGE_DATA_PNG"
        mock_part = MagicMock()
        mock_part.inline_data = mock_inline_data

        mock_resp = MagicMock()
        mock_resp.parts = [mock_part]
        mock_client.models.generate_content.return_value = mock_resp

        prompt = "Banki swinging bearded axe against runic golem"
        img_bytes, err = gm_engine.generate_scene_image("mock_api_key", prompt)

        self.assertIsNone(err)
        self.assertEqual(img_bytes, b"FAKE_IMAGE_DATA_PNG")

        # Verify call arguments
        call_kwargs = mock_client.models.generate_content.call_args[1]
        self.assertEqual(call_kwargs["model"], "gemini-3.1-flash-lite-image")
        self.assertIn("Dark anime art style, high quality, masterpiece.", call_kwargs["contents"])
        self.assertIn(prompt, call_kwargs["contents"])

if __name__ == "__main__":
    unittest.main()
