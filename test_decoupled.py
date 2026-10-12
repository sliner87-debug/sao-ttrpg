import os
from backend.gm_engine import generate_visible_room, resolve_turn
from backend.actor_engine import generate_actor_action

# Mock State for Test
player_state = {"name": "Banki", "hp": 100, "max_hp": 100, "location": "Sector 1 Sewer"}
world_state = {"map_locations": [{"name": "Sector 1 Sewer", "entities": [{"name": "Orc", "hp": 50}], "secrets": ["Hidden trapdoor"]}]}
map_state = {"player_x": 50, "player_y": 50}
chat_history = []
player_input = "I charge the Orc with my broadsword!"

# 1. GM: Generate Visible Room
print("1. Generating Visible Room...")
room_state = generate_visible_room(player_state, world_state)
print(room_state)

# 2. Actor: Ren decides what to do
print("\n2. Ren is deciding his action...")
# (Assuming GEMINI_API_KEY is in env)
api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key:
    import toml
    try:
        secrets = toml.load("H:/Antigravity/SAO Mockup/.streamlit/secrets.toml")
        api_key = secrets.get("GEMINI_API_KEY", "")
    except Exception:
        pass

ren_action = generate_actor_action(api_key, "companion_ren", player_input)
print(f"Ren's queued action: {ren_action}")

# 3. GM: Resolves turn
print("\n3. GM is resolving the turn...")
queued_actions = [ren_action]
result = resolve_turn(api_key, player_input, queued_actions, chat_history, player_state, world_state, map_state)

print("\n--- FINAL TURN RESULT ---")
print(result.get('narrative', 'NO NARRATIVE'))
print("\nCombat Logs:", result.get('combat_logs', []))
print("State Updates:", result.get('state_updates', {}))
