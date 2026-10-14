import os
import json
from PIL import Image, ImageDraw, ImageFont

# Define the absolute boundaries of our 3x3 stitched base map (Zoom 14)
# x_center = 4811, y_center = 6185
# So X goes from 4810 to 4812, Y goes from 6184 to 6186.
# Each tile is 256x256. Map is 768x768 pixels.
# Let's map our own custom 100x100 grid onto this 768x768 pixel image.
# Grid 0,0 is top-left, 100,100 is bottom-right.
# 1 grid step = 7.68 pixels.

GRID_SIZE = 100
PIXELS_PER_GRID = 768 / GRID_SIZE

NODES = {
    "Washington_Borough": {"x": 50, "y": 50, "color": "blue", "label": "Washington Safe-Zone"},
    "Route_31_Chokepoint": {"x": 50, "y": 35, "color": "red", "label": "Route 31 Blockade"},
    "Oxford_Mines": {"x": 53, "y": 48, "color": "purple", "label": "Oxford Mine Vaults"}
}

CONNECTIONS = [
    ("Washington_Borough", "Route_31_Chokepoint"),
    ("Route_31_Chokepoint", "Oxford_Mines")
]

# --- HIDDEN SECRETS & ROUTES ---
SECRETS = {
    "Smugglers_Cache": {"x": 52, "y": 48, "color": "gold", "label": "Smuggler's Drop", "skill": "Cartography I"},
    "Aether_Well": {"x": 45, "y": 30, "color": "magenta", "label": "Aether-Well", "skill": "Aether-Mapping"},
    "Old_Subway": {"x": 55, "y": 40, "color": "darkgray", "label": "Collapsed Subway", "skill": "Cartography II"}
}

HIDDEN_CONNECTIONS = [
    ("Washington_Borough", "Smugglers_Cache", "Cartography I"),
    ("Route_31_Chokepoint", "Aether_Well", "Aether-Mapping"),
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_STATE_FILE = os.path.join(BASE_DIR, "map_state.json")
BASE_MAP_FILE = os.path.join(BASE_DIR, "base_map.jpg")
CURRENT_MAP_FILE = os.path.join(BASE_DIR, "current_map.jpg")

def load_map_state():
    if os.path.exists(MAP_STATE_FILE):
        with open(MAP_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Default map state
    return {
        "player_x": 50,
        "player_y": 50,
        "explored_tiles": [[50, 50], [50, 49], [51, 50], [49, 50], [50, 51]],
        "macro_mode": False
    }

def save_map_state(state):
    with open(MAP_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

def has_cartography_skill(req_skill, p_skills):
    """Checks if player meets Cartography or exploration skill requirements across V1 list or V2 1-1000 dict."""
    if req_skill is None:
        return True
    if not p_skills:
        return False
    req_lower = req_skill.lower().strip()

    # Check direct string match first (backwards compatibility)
    skill_keys = list(p_skills.keys()) if isinstance(p_skills, dict) else [str(s) for s in p_skills]
    if any(req_lower in s.lower() or "omniscience (dev)" in s.lower() for s in skill_keys):
        return True

    # V2 1-1000 Cartography mastery threshold check
    if isinstance(p_skills, dict):
        cart_mastery = 0
        for s_name, s_val in p_skills.items():
            if "cartograph" in s_name.lower() or "aether-map" in s_name.lower() or "navigat" in s_name.lower():
                if isinstance(s_val, dict):
                    cart_mastery = max(cart_mastery, int(s_val.get("mastery", 0)))
                elif isinstance(s_val, (int, float)):
                    cart_mastery = max(cart_mastery, int(s_val))
        if "cartography iv" in req_lower:
            return cart_mastery >= 500
        elif "cartography iii" in req_lower:
            return cart_mastery >= 250
        elif "cartography ii" in req_lower or "aether-mapping" in req_lower:
            return cart_mastery >= 100
        elif "cartography i" in req_lower or "cartography" in req_lower:
            return cart_mastery >= 50
    return False

def generate_overlay(player_skills=None):
    if player_skills is None:
        player_skills = []
        
    if not os.path.exists(BASE_MAP_FILE):
        return None
        
    state = load_map_state()
    base_img = Image.open(BASE_MAP_FILE).convert("RGBA")
    
    # 1. Fog of War Layer
    fog = Image.new("RGBA", base_img.size, (0, 0, 0, 200)) # 200 alpha for dark fog
    fog_draw = ImageDraw.Draw(fog)
    
    mask = Image.new("L", base_img.size, 200) # Start fully "fogged"
    mask_draw = ImageDraw.Draw(mask)
    
    # Reveal explored Grid Tiles
    for coords in state["explored_tiles"]:
        gx, gy = coords[0], coords[1]
        px, py = gx * PIXELS_PER_GRID, gy * PIXELS_PER_GRID
        radius = PIXELS_PER_GRID * 3
        mask_draw.ellipse([px - radius, py - radius, px + radius, py + radius], fill=0)
        
    # Reveal Nodes
    for node in NODES.values():
        px, py = node["x"] * PIXELS_PER_GRID, node["y"] * PIXELS_PER_GRID
        mask_draw.ellipse([px - 40, py - 40, px + 40, py + 40], fill=0)
        
    # Helper to check if player has a required skill (supports V1 strings and V2 1-1000 dicts)
    def has_skill(req_skill, p_skills):
        return has_cartography_skill(req_skill, p_skills)

    # Reveal Secrets (if skill check passes)
    visible_secrets = {}
    for key, sec in SECRETS.items():
        if has_skill(sec.get("skill"), player_skills):
            visible_secrets[key] = sec
            px, py = sec["x"] * PIXELS_PER_GRID, sec["y"] * PIXELS_PER_GRID
            mask_draw.ellipse([px - 25, py - 25, px + 25, py + 25], fill=0) # Smaller reveal radius
            
    # Reveal Dynamic Procedural Nodes
    dynamic_nodes = state.get("dynamic_nodes", [])
    for d_node in dynamic_nodes:
        px, py = d_node["x"] * PIXELS_PER_GRID, d_node["y"] * PIXELS_PER_GRID
        mask_draw.ellipse([px - 35, py - 35, px + 35, py + 35], fill=0)
        
    fog.putalpha(mask)
    
    # Composite Fog onto Base
    map_img = Image.alpha_composite(base_img, fog)
    draw = ImageDraw.Draw(map_img)
    
    # 2. Draw Standard Connections
    for n1, n2 in CONNECTIONS:
        node1 = NODES[n1]
        node2 = NODES[n2]
        x1, y1 = node1["x"] * PIXELS_PER_GRID, node1["y"] * PIXELS_PER_GRID
        x2, y2 = node2["x"] * PIXELS_PER_GRID, node2["y"] * PIXELS_PER_GRID
        draw.line([x1, y1, x2, y2], fill=(200, 50, 50, 150), width=4)
        
    # Draw Hidden Connections
    for n1, n2, req_skill in HIDDEN_CONNECTIONS:
        if has_skill(req_skill, player_skills):
            def get_coords(n):
                if n in NODES: return NODES[n]["x"], NODES[n]["y"]
                if n in visible_secrets: return visible_secrets[n]["x"], visible_secrets[n]["y"]
                return None, None
            x1, y1 = get_coords(n1)
            x2, y2 = get_coords(n2)
            if x1 and x2:
                px1, py1 = x1 * PIXELS_PER_GRID, y1 * PIXELS_PER_GRID
                px2, py2 = x2 * PIXELS_PER_GRID, y2 * PIXELS_PER_GRID
                draw.line([px1, py1, px2, py2], fill=(255, 215, 0, 180), width=2)

    # 3. Draw Nodes
    node_overrides = state.get("node_overrides", {})
    for key, node in NODES.items():
        px, py = node["x"] * PIXELS_PER_GRID, node["y"] * PIXELS_PER_GRID
        color = node_overrides.get(key, node["color"])
        draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill=color, outline="white", width=2)
        draw.text((px + 10, py - 10), node["label"], fill="white")
        
    # Draw Secrets
    for key, sec in visible_secrets.items():
        px, py = sec["x"] * PIXELS_PER_GRID, sec["y"] * PIXELS_PER_GRID
        color = sec["color"]
        draw.polygon([(px, py-6), (px+6, py), (px, py+6), (px-6, py)], fill=color, outline="white") # Diamond shape
        draw.text((px + 10, py - 10), sec["label"], fill=color)
        
    # Draw Procedural Dynamic Nodes
    dynamic_nodes = state.get("dynamic_nodes", [])
    for d_node in dynamic_nodes:
        px, py = d_node["x"] * PIXELS_PER_GRID, d_node["y"] * PIXELS_PER_GRID
        color = d_node.get("color", "cyan")
        label = d_node.get("label", d_node.get("name", "Unknown Node"))
        # Hexagon shape for AI-generated nodes
        draw.polygon([(px-5, py-8), (px+5, py-8), (px+8, py), (px+5, py+8), (px-5, py+8), (px-8, py)], fill=color, outline="black")
        draw.text((px + 12, py - 10), label, fill=color)
        
    # 4. Draw Player Position
    px = state["player_x"] * PIXELS_PER_GRID
    py = state["player_y"] * PIXELS_PER_GRID
    draw.polygon([(px, py - 10), (px - 8, py + 8), (px + 8, py + 8)], fill="cyan", outline="black")
    
    # 5. Draw Legend
    try:
        legend_x = 10
        legend_y = 10
        draw.rectangle([legend_x, legend_y, legend_x + 140, legend_y + 100], fill=(0, 0, 0, 180), outline="white")
        draw.text((legend_x + 10, legend_y + 5), "--- MAP LEGEND ---", fill="white")
        
        # Safe Zone (Circle)
        draw.ellipse([legend_x + 8, legend_y + 24, legend_x + 16, legend_y + 32], fill="blue", outline="white", width=2)
        draw.text((legend_x + 25, legend_y + 22), "Safe Zone / Node", fill="white")
        
        # Hidden Secret (Diamond)
        draw.polygon([(legend_x+12, legend_y+40), (legend_x+18, legend_y+46), (legend_x+12, legend_y+52), (legend_x+6, legend_y+46)], fill="gold", outline="white")
        draw.text((legend_x + 25, legend_y + 42), "Hidden Secret", fill="white")
        
        # Procedural Landmark (Hexagon)
        draw.polygon([(legend_x+8, legend_y+60), (legend_x+16, legend_y+60), (legend_x+19, legend_y+66), (legend_x+16, legend_y+72), (legend_x+8, legend_y+72), (legend_x+5, legend_y+66)], fill="purple", outline="black")
        draw.text((legend_x + 25, legend_y + 61), "Discovered Landmark", fill="white")
        
        # Player Position (Triangle)
        draw.polygon([(legend_x+12, legend_y+82), (legend_x+6, legend_y+94), (legend_x+18, legend_y+94)], fill="cyan", outline="black")
        draw.text((legend_x + 25, legend_y + 83), "Player Location", fill="white")
    except Exception as e:
        print("Legend drawing failed:", e)
    
    map_img = map_img.convert("RGB")
    map_img.save(CURRENT_MAP_FILE)
    return CURRENT_MAP_FILE

if __name__ == "__main__":
    generate_overlay()
