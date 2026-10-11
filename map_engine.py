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
    "Oxford_Mines": {"x": 40, "y": 20, "color": "purple", "label": "Oxford Mine Vaults"}
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

def load_map_state():
    if os.path.exists("map_state.json"):
        with open("map_state.json", "r") as f:
            return json.load(f)
    # Default map state
    return {
        "player_x": 50,
        "player_y": 50,
        "explored_tiles": [[50, 50], [50, 49], [51, 50], [49, 50], [50, 51]],
        "macro_mode": False
    }

def save_map_state(state):
    with open("map_state.json", "w") as f:
        json.dump(state, f)

def generate_overlay(player_skills=None):
    if player_skills is None:
        player_skills = []
        
    if not os.path.exists("base_map.jpg"):
        return None
        
    state = load_map_state()
    base_img = Image.open("base_map.jpg").convert("RGBA")
    
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
        
    # Helper to check if player has a required skill (fuzzy match to ignore AI descriptions)
    def has_skill(req_skill, p_skills):
        if req_skill is None: return True
        req_lower = req_skill.lower()
        return any(req_lower in s.lower() or "omniscience (dev)" in s.lower() for s in p_skills)

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
    for key, node in NODES.items():
        px, py = node["x"] * PIXELS_PER_GRID, node["y"] * PIXELS_PER_GRID
        color = node["color"]
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
    
    map_img = map_img.convert("RGB")
    map_img.save("current_map.jpg")
    return "current_map.jpg"

if __name__ == "__main__":
    generate_overlay()
