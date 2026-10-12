import json
import os
from google import genai
from google.genai import types

def get_client(api_key):
    return genai.Client(api_key=api_key)

def load_cardinal_rules(rules_path="H:/Antigravity/SAO Sandbox v2/backend/System_Core/cardinal_rules.md"):
    if os.path.exists(rules_path):
        with open(rules_path, "r", encoding="utf-8") as f:
            return f.read()
    return "You are the Cardinal System Encounter Director."

def generate_visible_room(player_state, world_state, staging_dir="H:/Antigravity/SAO Sandbox v2/backend/Staging_Ground"):
    """
    Extracts the visible elements of the current location and saves to Staging_Ground/visible_room.json
    This serves as a sanitized state for subagents (actors).
    """
    current_location = player_state.get('location', 'Unknown')
    
    visible_entities = []
    room_desc = "Unknown area."
    
    for loc in world_state.get('map_locations', []):
        if loc['name'] == current_location:
            # Sanitize secrets out of the visible room
            visible_entities = loc.get('entities', [])
            room_desc = loc.get('description', f"You are in {current_location}.")
            break
            
    visible_state = {
        "location_name": current_location,
        "description": room_desc,
        "player_summary": {
            "name": player_state.get('name', 'Player'),
            "hp": player_state.get('hp', 100),
            "max_hp": player_state.get('max_hp', 100),
            "equipment": player_state.get('equip', {})
        },
        "visible_entities": visible_entities
    }
    
    os.makedirs(staging_dir, exist_ok=True)
    out_path = os.path.join(staging_dir, "visible_room.json")
    with open(out_path, 'w', encoding="utf-8") as f:
        json.dump(visible_state, f, indent=4)
        
    return visible_state

def resolve_turn(api_key, user_input, queued_actions, chat_history, player_state, world_state, map_state, rules_path=None):
    """
    Resolves the turn taking into account the player's action and all queued actor actions.
    """
    client = get_client(api_key)
    
    cardinal_rules_text = load_cardinal_rules(rules_path) if rules_path else load_cardinal_rules()
    
    current_location = player_state.get('location', 'Unknown')
    entities_in_room = []
    secrets_in_room = []
    for loc in world_state.get('map_locations', []):
        if loc['name'] == current_location:
            entities_in_room = loc.get('entities', [])
            secrets_in_room = loc.get('secrets', [])
            break
            
    system_instruction = f"""{cardinal_rules_text}
    
    CURRENT STATE:
    Player: {player_state.get('name')} (HP: {player_state.get('hp')}/{player_state.get('max_hp')})
    Location: {current_location}
    GPS Coordinates: X: {map_state.get('player_x', 50)}, Y: {map_state.get('player_y', 50)}
    Entities present: {json.dumps(entities_in_room)}
    Hidden Secrets: {json.dumps(secrets_in_room)}
    
    QUEUED ACTIONS FROM ACTORS:
    {json.dumps(queued_actions, indent=2)}
    
    YOUR ROLE:
    1. Narrate the outcome of the player's action AND weave in the Queued Actions from Actors natively.
    2. Resolve combat and skill checks logically based on the queued actions and player input.
    3. Do NOT puppet the player.
    4. Reveal hidden secrets if investigated.
    
    Format your response EXACTLY as a JSON object with keys:
    - "narrative": The markdown formatted story/dialogue.
    - "combat_logs": A list of strings showing the exact dice math and damage for the turn.
    - "state_updates": A JSON object containing updates to the player's HUD, health, inventory, skills, and map location.
    """
    
    contents = []
    for msg in chat_history[-6:]:
        role = "user" if msg["role"] == "user" else "model"
        text = msg.get("ai_prompt", msg.get("content", ""))
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))
        
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_input)]))
    
    try:
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.7
            )
        )
        return json.loads(response.text)
    except Exception as e:
        return {"narrative": f"**System Error:** {str(e)}", "state_updates": {}}
