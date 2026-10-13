import json
import os
from google import genai
from google.genai import types
from backend.schemas import ActorActionSchema

def load_json(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

def get_companion_action(api_key: str, character_id: str):
    """
    Simulates the AI companion's thought process.
    Reads ONLY the visible_room.json and their own character sheet.
    """
    # 1. Load the isolated states
    client = genai.Client(api_key=api_key)
    char_sheet_path = os.path.join("Party", f"{character_id}.json")
    visible_room_path = os.path.join("Staging_Ground", "visible_room.json")
    action_queue_path = os.path.join("Staging_Ground", "action_queue.json")
    
    char_sheet = load_json(char_sheet_path)
    visible_room = load_json(visible_room_path)
    
    # 2. Construct the prompt
    prompt = f"""You are roleplaying as an AI companion in a dark fantasy, tactical TTRPG.
The setting is high-fantasy aether-punk and magetech (NOT modern military or cyberpunk). Any firearms used (like an Aether-Lock Carbine) are MageTech weapons that channel condensed radiant mana or elemental charges, NEVER gunpowder or lead.
Your character sheet is: {json.dumps(char_sheet, indent=2)}

You only know what you can see in the visible room:
{json.dumps(visible_room, indent=2)}

Decide on your next tactical action based ONLY on this information and your specific behavior_prompt.
Output your response exactly matching the requested JSON schema.
"""

    # 3. Call Gemini Flash with Structured Outputs
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ActorActionSchema,
            temperature=0.4
        )
    )
    
    # Parse the structured JSON response
    action_data = json.loads(response.text)
    
    # 4. Append to the Action Queue
    queue = load_json(action_queue_path)
    queue.append(action_data)
    save_json(action_queue_path, queue)
    
    print(f"Queued action for {character_id}: {action_data['intended_action']}")
    return action_data
