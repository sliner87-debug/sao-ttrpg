import os
import toml
import sys
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import llm_engine

if __name__ == '__main__':
    secrets = toml.load(os.path.join(".streamlit", "secrets.toml"))
    api_key = secrets.get("GEMINI_API_KEY")

    print("Testing llm_engine.generate_turn...")

    chat_history = [
        {"role": "user", "content": "/admin Give me an image of me equipping my new gear!"}
    ]
    player_state = {"name": "Banki", "hp": 100, "max_hp": 100, "location": "Test Area"}
    world_state = {"map_locations": []}
    map_state = {}

    turn_data = llm_engine.generate_turn(api_key, "/admin Give me an image of me equipping my new gear!", chat_history, player_state, world_state, map_state)
    print("Keys returned:", turn_data.keys())
    print("Narrative:", turn_data.get("narrative")[:100], "...")
    print("Image prompt:", turn_data.get("image_prompt"))
