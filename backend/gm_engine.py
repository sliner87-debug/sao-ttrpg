import json
import os
from google import genai
from google.genai import types
from backend.schemas import VisibleRoomSchema, TurnResolutionSchema

client = genai.Client()

def load_json(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

def generate_visible_state():
    """Reads secret_master_state.json and writes sanitized version to visible_room.json"""
    master_state_path = os.path.join(".game_state", "secret_master_state.json")
    visible_room_path = os.path.join("Staging_Ground", "visible_room.json")
    master_state = load_json(master_state_path)
    
    prompt = f"""You are the Cardinal System (GM).
Here is the absolute truth of the encounter:
{json.dumps(master_state, indent=2)}

Strip away all secret mechanics (exact HP, hidden traps, enemy intents).
Return ONLY the data the players can clearly observe. Output EXACTLY matching the JSON schema.
"""
    
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VisibleRoomSchema,
            temperature=0.2
        )
    )
    
    visible_room = json.loads(response.text)
    save_json(visible_room_path, visible_room)
    print("Staging Ground updated: visible_room.json")
    return visible_room

def resolve_turn(player_action: str):
    """Takes the player action + AI queue, calculates math, updates master state."""
    master_state_path = os.path.join(".game_state", "secret_master_state.json")
    queue_path = os.path.join("Staging_Ground", "action_queue.json")
    rules_path = os.path.join("System_Core", "cardinal_rules.md")
    
    master_state = load_json(master_state_path)
    action_queue = load_json(queue_path)
    
    with open(rules_path, "r", encoding="utf-8") as f:
        rules = f.read()
        
    prompt = f"""You are the Cardinal System (GM). Resolve the turn.
Ruleset constraints must be applied strictly:
{rules}

Current Master State:
{json.dumps(master_state, indent=2)}

Human Player Action:
"{player_action}"

Companion AI Actions in Queue:
{json.dumps(action_queue, indent=2)}

Determine if attacks hit based on AC, update HP, and advance the turn.
Output the TurnResolutionSchema.
"""

    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TurnResolutionSchema,
            temperature=0.4
        )
    )
    
    resolution = json.loads(response.text)
    
    # Apply updates to Master State
    for entity in master_state["entities"]:
        eid = entity["id"]
        if eid in resolution["hp_changes"]:
            entity["hp"] += resolution["hp_changes"][eid]
        if eid in resolution["status_updates"]:
            entity["status"] = resolution["status_updates"][eid]
            
    master_state["turn_number"] += 1
    save_json(master_state_path, master_state)
    
    # Clear the queue for the next turn
    save_json(queue_path, [])
    
    print("Turn resolved and master_state updated.")
    return resolution
