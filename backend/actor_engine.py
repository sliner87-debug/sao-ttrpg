import json
import os
from google import genai
from google.genai import types

def get_client(api_key):
    return genai.Client(api_key=api_key)

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding="utf-8") as f:
            return json.load(f)
    return {}

def generate_actor_action(api_key, actor_id, player_input, 
                          staging_dir="H:/Antigravity/SAO Sandbox v2/backend/Staging_Ground", 
                          party_dir="H:/Antigravity/SAO Sandbox v2/backend/Party"):
    """
    Generates an intended action for an AI Actor bot based on the visible room and their character sheet.
    The actor only has access to their sheet and the sanitized Staging_Ground/visible_room.json.
    """
    client = get_client(api_key)
    
    # Load actor sheet and visible room
    actor_sheet_path = os.path.join(party_dir, f"{actor_id}.json")
    visible_room_path = os.path.join(staging_dir, "visible_room.json")
    
    actor_sheet = load_json(actor_sheet_path)
    visible_room = load_json(visible_room_path)
    
    actor_name = actor_sheet.get('name', actor_id)
    
    system_instruction = f"""You are {actor_name}, an autonomous AI Actor bot in a grimdark LitRPG world (The Fractured Earth).
    You ONLY have access to your character sheet and the currently visible room state.
    
    YOUR CHARACTER SHEET:
    {json.dumps(actor_sheet, indent=2)}
    
    VISIBLE ROOM STATE:
    {json.dumps(visible_room, indent=2)}
    
    THE PLAYER'S DECLARED ACTION THIS TURN:
    "{player_input}"
    
    YOUR ROLE:
    Evaluate the tactical state, how you feel about the situation, and decide what action you will take this turn to help, hinder, or react.
    
    You must output EXACTLY a JSON object with two keys:
    - "actor": Your character's name.
    - "action": Your intended action, written in first-person or third-person, describing what you try to do this turn.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents="Evaluate the scene and declare your intended action for this turn.",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.7
            )
        )
        return json.loads(response.text)
    except Exception as e:
        return {"actor": actor_name, "action": f"ERROR: Failed to generate action - {str(e)}"}

def calculate_survival_odds(api_key, player_state, visible_room):
    """
    Oracle Engine: Calculates the survival odds of the current room state.
    """
    client = get_client(api_key)
    
    system_instruction = f"""You are the Oracle Prediction Engine.
    Analyze the player's current state and the visible room, then predict their odds of survival if combat initiates.
    
    PLAYER STATE:
    {json.dumps(player_state, indent=2)}
    
    VISIBLE ROOM STATE:
    {json.dumps(visible_room, indent=2)}
    
    Output a JSON object with:
    - "odds": an integer between 0 and 100 representing the percent chance of survival.
    - "tip": A 1-sentence tactical tip.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents="Predict survival odds.",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        return json.loads(response.text)
    except Exception as e:
        return {"odds": 50, "tip": "System Error: Cannot compute odds."}
