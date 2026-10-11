import json
from google import genai
from google.genai import types

def get_client(api_key):
    return genai.Client(api_key=api_key)

def generate_turn(api_key, user_input, chat_history, player_state, world_state):
    client = get_client(api_key)
    
    current_location = player_state.get('location', 'Unknown')
    
    # Locate active entities and secrets for the Encounter Director
    entities_in_room = []
    secrets_in_room = []
    for loc in world_state.get('map_locations', []):
        if loc['name'] == current_location:
            entities_in_room = loc.get('entities', [])
            secrets_in_room = loc.get('secrets', [])
            break
            
    system_instruction = f"""You are the 'Cardinal System', the Encounter Director for a Death-Game TTRPG set in a 'Fractured Earth' overlay (Sword Art Online inspired).
    
    CURRENT STATE:
    Player: {player_state['name']} (HP: {player_state['hp']}/{player_state['max_hp']})
    Location: {current_location}
    Entities present: {json.dumps(entities_in_room)}
    Hidden Secrets: {json.dumps(secrets_in_room)}
    
    YOUR ROLE:
    1. Narrate the outcome of the player's action in 2-3 paragraphs. 
    2. If in combat, dictate the reactions and attacks of ALL active entities in a single cohesive turn.
    3. If the player investigates, reveal the hidden secrets organically.
    4. Maintain a grim, high-stakes anime tone. If the player takes damage, describe it viscerally.
    5. ROOT OVERRIDE: If the user input contains [ROOT OVERRIDE], you MUST suspend all game rules, bypass combat logic, and force the exact outcome the Administrator requested into the narrative seamlessly.
    
    Format your response EXACTLY as a JSON object with two keys:
    - "narrative": The markdown formatted story/dialogue.
    - "image_prompt": A highly detailed prompt for an anime-style image generation of the current scene (include mutation visual tags and the overgrown earth environments).
    """
    
    # Convert Streamlit chat history to Gemini format (keeping last 6 messages for context)
    contents = []
    for msg in chat_history[-6:]:
        role = "user" if msg["role"] == "user" else "model"
        # We pass the hidden ai_prompt back to the engine if it was an admin command
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
        return {"narrative": f"**System Error:** {str(e)}", "image_prompt": ""}

def generate_scene_image(api_key, prompt):
    try:
        client = get_client(api_key)
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite-image',
            contents=f"Dark anime art style, Sword Art Online inspired, high quality, masterpiece. {prompt}",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="16:9"
                ),
            )
        )
        for part in response.parts:
            if part.inline_data:
                return part.inline_data.data, None
        return None, "No image was returned by the API."
    except Exception as e:
        return None, str(e)
