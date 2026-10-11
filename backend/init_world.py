import json
import random
import os

# Define the file paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MONSTERS_PATH = os.path.join(BASE_DIR, 'assets', 'base_templates', 'monsters.json')
ACTIVE_WORLD_PATH = os.path.join(BASE_DIR, 'world_state.json')

# -----------------------------------------
# 1. PROCEDURAL MUTATION DATA
# -----------------------------------------
MUTATIONS = [
    {"tag": "Crystalline", "hp_mod": 1.5, "atk_mod": 0.8, "def_mod": 2.0, "behavior_mod": "Moves slowly, heavily armored.", "visual": "covered in glowing, jagged crystal growths"},
    {"tag": "Aether-Touched", "hp_mod": 0.8, "atk_mod": 1.5, "def_mod": 0.5, "behavior_mod": "Erratic and fast. Deals slight magic damage.", "visual": "radiating a faint, ethereal purple aura"},
    {"tag": "Void-Blighted", "hp_mod": 1.2, "atk_mod": 1.2, "def_mod": 1.2, "behavior_mod": "Aggressive. Attacks lower max HP temporarily.", "visual": "dripping with dark, shadowy energy"},
    {"tag": "Ember-Forged", "hp_mod": 1.0, "atk_mod": 1.8, "def_mod": 1.0, "behavior_mod": "Leaves a trail of fire. Attacks cause burn status.", "visual": "fur/skin looks like smoldering charcoal"},
    {"tag": "Debug-Corrupted", "hp_mod": 0.5, "atk_mod": 2.5, "def_mod": 0.1, "behavior_mod": "Teleports erratically. Hits incredibly hard but is extremely fragile.", "visual": "flickering with green wireframe textures and missing polygons"}
]

# -----------------------------------------
# 2. MAP GENERATION: FRACTURED EARTH
# -----------------------------------------
ENV_PREFIXES = ["Overgrown", "Glitched", "Rusted", "Crystalline", "Fractured", "Neon", "Ruined", "Sunken"]
ENV_TYPES = ["Subway Station", "Highway Expressway", "Plaza", "Shopping Mall", "Catacombs", "Stadium", "Financial District", "104 Tower"]

# Expanded Secrets Pool (Trapped Devs, Admin Tools, Isekai Lore)
SECRETS_POOL = [
    # --- TRAPPED DEVS & ADMIN TOOLS ---
    {"id": "sec_dev_01", "type": "npc_dev", "description": "A hollow-eyed man clutching a digital clipboard. He is a trapped Junior Environment Artist. If given food, he will reveal a safe path through the next 3 combat zones without drawing aggro."},
    {"id": "sec_dev_02", "type": "admin_loot", "description": "A floating, glowing blue 'DEV-CONSOLE'. Touching it grants the player a 1-time-use item: [Debug Wand]. It can instantly delete any non-boss enemy, but using it drains 90% of the player's HP."},
    {"id": "sec_dev_03", "type": "admin_loot", "description": "The frozen avatar of a Lead Network Engineer. Looting them yields an 'Admin ID Badge' that can permanently bypass one glitched Firewall barrier without needing a boss key."},
    {"id": "sec_dev_04", "type": "lore_admin", "description": "A holographic whiteboard left behind in a panic by the devs. It lists the Sector 1 Boss mechanics, but the last line is violently crossed out in red ink with the words: 'THE AI CHANGED THE CODE. IT'S NOT A GAME ANYMORE'."},
    
    # --- THE CELL PHONE (Rich Lore) ---
    {"id": "sec_01", "type": "lore_heavy", "description": "A perfectly preserved smartphone from Earth. Battery at 99%, NO SIGNAL.\n[CONTENTS]\n- Texts from 'Mom': 'Dinner is cold', 'Where are you?', 'It's been 3 days, please answer the door.'\n- Browser History: 'NerveGear manual override', 'SAO missing logout button', 'Can NerveGear be removed safely?'\n- Pictures: A selfie of a teenager putting on a VR headset captioned 'Link Start! See you in Aincrad!'\n- Apps: A proprietary 'Argus Employee Tracker' app that points the player towards a hidden developer bunker."},

    # --- REWARDING & DANGEROUS ---
    {"id": "sec_02", "type": "loot", "description": "A floating line of green text: '// TODO: Remove beta-test chest before launch'. Below it is a locked chest containing 10,000 Col and the 'Beta Tester's Cloak'."},
    {"id": "sec_03", "type": "loot", "description": "An un-textured grey cube hovering in the air. Interacting with it grants the 'Admin's Blessing' buff, permanently increasing Max HP by 100."},
    {"id": "sec_07", "type": "combat_trap", "description": "A glowing, golden subway turnstile labeled 'EXIT GAME'. Crossing it triggers a brutal trap, dropping player HP by 50% and spawning three Void-Blighted monsters."},
    {"id": "sec_09", "type": "combat_boss", "description": "A corrupted admin console. Touching it flags the player as 'INTRUDER' and spawns a Level 99 System Enforcer. It is an instant-death encounter if they don't run immediately."},
    {"id": "sec_11", "type": "combat_trap", "description": "A weeping-angel style entity made of static noise. It only moves closer when the player speaks or uses the chat UI. If it touches them, it deletes a random item from their inventory."},
]

def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

def mutate_entity(entity):
    mutated_entity = entity.copy()
    if random.random() < 0.35: # Increased mutation chance to 35%
        mutation = random.choice(MUTATIONS)
        mutated_entity['name'] = f"{mutation['tag']} {entity['base_name']}"
        mutated_entity['max_hp'] = int(entity['base_hp'] * mutation['hp_mod'])
        mutated_entity['atk'] = int(entity['base_atk'] * mutation['atk_mod'])
        mutated_entity['def'] = int(entity['base_def'] * mutation['def_mod'])
        mutated_entity['behavior'] = f"{entity['behavior']} {mutation['behavior_mod']}"
        mutated_entity['visual_prompt'] = f"{entity['visual_prompt']}, {mutation['visual']}"
        mutated_entity['is_mutated'] = True
        mutated_entity['mutation_tag'] = mutation['tag']
    else:
        mutated_entity['name'] = entity['base_name']
        mutated_entity['max_hp'] = entity['base_hp']
        mutated_entity['atk'] = entity['base_atk']
        mutated_entity['def'] = entity['base_def']
        mutated_entity['is_mutated'] = False
    return mutated_entity

def generate_map_nodes(num_nodes=8):
    nodes = []
    # Ensure Sector 1 always has a Town, the 104 Tower (Mini-Raid), and a Boss Stadium
    nodes.append({"id": "loc_0", "name": "The Safe-Zone: Yoyogi Park", "is_safe_zone": True, "secrets": [], "entities": []})
    nodes.append({"id": "loc_1", "name": "Overgrown Shibuya 104 Tower", "is_safe_zone": False, "secrets": [], "entities": []})
    nodes.append({"id": "loc_2", "name": "Corrupted Olympic Stadium (Sector 1 Boss)", "is_safe_zone": False, "secrets": [], "entities": []})
    
    # Generate the rest procedurally
    for i in range(3, num_nodes):
        name = f"{random.choice(ENV_PREFIXES)} {random.choice(ENV_TYPES)}"
        nodes.append({"id": f"loc_{i}", "name": name, "is_safe_zone": False, "secrets": [], "entities": []})
        
    return nodes

def inject_secrets(nodes):
    available_secrets = SECRETS_POOL.copy()
    random.shuffle(available_secrets)
    
    for node in nodes:
        num_secrets_to_inject = random.randint(1, 2)
        for _ in range(num_secrets_to_inject):
            if available_secrets:
                node['secrets'].append(available_secrets.pop())
    return nodes

def populate_map(nodes, base_monsters, num_entities=20):
    combat_nodes = [n for n in nodes if not n['is_safe_zone']]
    for i in range(num_entities):
        base_entity = random.choice(base_monsters)
        spawned_entity = mutate_entity(base_entity)
        spawned_entity['spawn_id'] = f"spawn_S1_{i}"
        
        target_node = random.choice(combat_nodes)
        target_node['entities'].append(spawned_entity)
    return nodes

def initialize_world():
    print("Generating Sector 1: The Fractured Overlay...")
    nodes = generate_map_nodes()
    
    print("Injecting Trapped Devs & Admin Tools...")
    nodes = inject_secrets(nodes)
    
    print("Populating Map with Mutated Entities...")
    base_monsters = load_json(MONSTERS_PATH)
    nodes = populate_map(nodes, base_monsters)
    
    world_state = {
        "sector": 1,
        "world_status": "LOCKED - FIREWALL ACTIVE",
        "map_locations": nodes
    }
    
    save_json(world_state, ACTIVE_WORLD_PATH)
    print("\n--- SECTOR 1 GENERATION COMPLETE ---")

if __name__ == "__main__":
    initialize_world()
