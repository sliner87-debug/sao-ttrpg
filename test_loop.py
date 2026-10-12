from backend.gm_engine import generate_visible_state, resolve_turn
from backend.actor_engine import get_companion_action
import json

def run_test_turn():
    print("--- 1. GM Generates Visible State ---")
    generate_visible_state()
    
    print("\n--- 2. Companions View State & Queue Actions ---")
    get_companion_action("companion_ren")
    
    print("\n--- 3. Player Takes Action ---")
    player_action = "I cast Firebolt at the Runic Quarry Golem."
    print(f"Player: {player_action}")
    
    print("\n--- 4. GM Resolves Turn ---")
    resolution = resolve_turn(player_action)
    
    print("\n[RESOLUTION RESULTS]")
    print(json.dumps(resolution, indent=2))

if __name__ == "__main__":
    run_test_turn()
