"""
map_engine.py
Cardinal Omniscience Multi-Layer Geospatial Atlas Engine (SAO Sandbox V2)
Authoritative Deep-GIS Engine integrating 44 USGS Topographic, LiDAR 3DEP,
Satellite Ortho, Subterranean Bathymetry, and Vertical Cross-Section map plates.
Centered on Washington Borough, NJ (07882) [40.7584° N, 74.9793° W].
"""

import os
import math
import json
import hashlib
from typing import Dict, List, Tuple, Optional, Any
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAPS_DIR = os.path.join(BASE_DIR, "assets", "maps")
MAP_STATE_FILE = os.path.join(BASE_DIR, "map_state.json")
CURRENT_MAP_FILE = os.path.join(BASE_DIR, "current_map.jpg")
GLOBAL_MAP_FILE = os.path.join(BASE_DIR, "current_global_map.jpg")
CURRENT_TACTICAL_MAP_FILE = os.path.join(BASE_DIR, "current_tactical_map.jpg")

# -----------------------------------------------------------------------------
# 1. SECTOR & LAYER REGISTRY
# -----------------------------------------------------------------------------

SECTORS: Dict[str, Dict[str, Any]] = {
    "sector0_core": {
        "id": "sector0_core",
        "name": "Sector 0: Washington Municipal Core",
        "prefix": "Sector0_Washington_Core",
        "radius_miles": 5.0,
        "center_gps": (40.7584, -74.9793),
        "elevation_asl_ft": 460,
        "bounds_lat_lon": {
            "north": 40.8309,
            "south": 40.6859,
            "east": -74.8837,
            "west": -75.0749
        },
        "description": "5-mile ultra-dense municipal grid around Washington Borough safe-zone."
    },
    "sector1_primary": {
        "id": "sector1_primary",
        "name": "Sector 1: Primary 25-Mile Core",
        "prefix": "Sector1_Primary",
        "radius_miles": 25.0,
        "center_gps": (40.7584, -74.9793),
        "elevation_asl_ft": 460,
        "bounds_lat_lon": {
            "north": 41.1209,
            "south": 40.3959,
            "east": -74.5013,
            "west": -75.4573
        },
        "description": "Warren, Hunterdon, Morris, Sussex, and Northampton regional corridor."
    },
    "sector2_west_nw": {
        "id": "sector2_west_nw",
        "name": "Sector 2: West & NW Poconos / Anthracite",
        "prefix": "Sector2_WestNW",
        "radius_miles": 100.0,
        "center_gps": (41.0500, -75.5000),
        "elevation_asl_ft": 1200,
        "bounds_lat_lon": {
            "north": 41.8000,
            "south": 40.3000,
            "east": -74.5000,
            "west": -76.5000
        },
        "description": "Lehigh River Gorge, Poconos, Scranton, Wilkes-Barre, and PA Anthracite Coal Belt."
    },
    "sector3_north_east": {
        "id": "sector3_north_east",
        "name": "Sector 3: North & East NYC / Hudson / Catskills",
        "prefix": "Sector3_NorthEast",
        "radius_miles": 100.0,
        "center_gps": (41.1000, -74.2000),
        "elevation_asl_ft": 200,
        "bounds_lat_lon": {
            "north": 42.1000,
            "south": 40.4000,
            "east": -73.2000,
            "west": -75.2000
        },
        "description": "Northern NJ, NYC 5 Boroughs, Hudson Fjord, West Point, Catskills, and deep aqueducts."
    },
    "sector4_south_sw": {
        "id": "sector4_south_sw",
        "name": "Sector 4: South & SW Pine Barrens / Philly",
        "prefix": "Sector4_SouthSW",
        "radius_miles": 100.0,
        "center_gps": (40.2000, -75.1000),
        "elevation_asl_ft": 100,
        "bounds_lat_lon": {
            "north": 40.8000,
            "south": 39.2000,
            "east": -74.0000,
            "west": -76.2000
        },
        "description": "Central/South NJ, Pine Barrens aquifer, Greater Philadelphia, and Cornwall iron mining belt."
    },
    "master_100mi": {
        "id": "master_100mi",
        "name": "Master 100-Mile Regional Overview",
        "prefix": "Master_100Mile",
        "radius_miles": 100.0,
        "center_gps": (40.7584, -74.9793),
        "elevation_asl_ft": 460,
        "bounds_lat_lon": {
            "north": 42.2084,
            "south": 39.3084,
            "east": -73.0793,
            "west": -76.8793
        },
        "description": "Macro 100-mile tri-state overview across NY, NJ, and PA."
    },
    "sector_ring_20_50mi_master": {
        "id": "sector_ring_20_50mi_master",
        "name": "Intermediate Ring: 20–50 Mile Master Belt",
        "prefix": "Sector_Ring_20_50Mi_Master",
        "radius_miles": 50.0,
        "inner_radius_miles": 20.0,
        "center_gps": (40.7584, -74.9793),
        "elevation_asl_ft": 460,
        "bounds_lat_lon": {
            "north": 41.4834,
            "south": 40.0334,
            "east": -74.0200,
            "west": -75.9386
        },
        "description": "Macro 20-to-50-mile annular buffer ring (~6,597 sq mi) surrounding Washington Borough."
    },
    "sector_ring_20_50mi_nw": {
        "id": "sector_ring_20_50mi_nw",
        "name": "Ring-NW: Poconos, Jim Thorpe & Lehigh Gorge (20–50 Mi)",
        "prefix": "Sector_Ring_20_50Mi_NW",
        "radius_miles": 50.0,
        "inner_radius_miles": 20.0,
        "center_gps": (41.0500, -75.4500),
        "elevation_asl_ft": 1100,
        "bounds_lat_lon": {
            "north": 41.4834,
            "south": 40.6500,
            "east": -74.9000,
            "west": -75.9386
        },
        "description": "Northwest quadrant: Delaware Water Gap, Poconos, Jim Thorpe (Mauch Chunk), and Lehigh Gorge."
    },
    "sector_ring_20_50mi_ne": {
        "id": "sector_ring_20_50mi_ne",
        "name": "Ring-NE: Kittatinny, Sterling Hill & Picatinny (20–50 Mi)",
        "prefix": "Sector_Ring_20_50Mi_NE",
        "radius_miles": 50.0,
        "inner_radius_miles": 20.0,
        "center_gps": (41.0500, -74.5000),
        "elevation_asl_ft": 900,
        "bounds_lat_lon": {
            "north": 41.4834,
            "south": 40.6500,
            "east": -74.0200,
            "west": -75.0500
        },
        "description": "Northeast quadrant: High Point (1,803 ft), Sterling Hill (-2,675 ft), Mt. Hope (-2,694 ft), Picatinny Arsenal."
    },
    "sector_ring_20_50mi_sw": {
        "id": "sector_ring_20_50mi_sw",
        "name": "Ring-SW: Bethlehem Steel, Allentown & Doylestown (20–50 Mi)",
        "prefix": "Sector_Ring_20_50Mi_SW",
        "radius_miles": 50.0,
        "inner_radius_miles": 20.0,
        "center_gps": (40.4500, -75.4500),
        "elevation_asl_ft": 350,
        "bounds_lat_lon": {
            "north": 40.8500,
            "south": 40.0334,
            "east": -74.9000,
            "west": -75.9386
        },
        "description": "Southwest quadrant: Bethlehem Steel blast furnaces, Allentown, Doylestown concrete castles, Valley Forge."
    },
    "sector_ring_20_50mi_se": {
        "id": "sector_ring_20_50mi_se",
        "name": "Ring-SE: Sourlands, Princeton Tokamak & Lakehurst (20–50 Mi)",
        "prefix": "Sector_Ring_20_50Mi_SE",
        "radius_miles": 50.0,
        "inner_radius_miles": 20.0,
        "center_gps": (40.4500, -74.5000),
        "elevation_asl_ft": 200,
        "bounds_lat_lon": {
            "north": 40.8500,
            "south": 40.0334,
            "east": -74.0200,
            "west": -75.0500
        },
        "description": "Southeast quadrant: Sourland Mountain, Princeton PPPL fusion tokamak, Trenton, and Lakehurst Hangar No. 1."
    },
    "global_raid": {
        "id": "global_raid",
        "name": "Planetary Patchwork Earth (Global Raids)",
        "prefix": "Global_Raid",
        "radius_miles": 12000.0,
        "center_gps": (0.0, 0.0),
        "elevation_asl_ft": 0,
        "bounds_lat_lon": {
            "north": 90.0,
            "south": -90.0,
            "east": 180.0,
            "west": -180.0
        },
        "description": "The 6 planetary 1–50 floor raid monoliths and leyline corridors."
    }
}

LAYERS: Dict[str, Dict[str, Any]] = {
    "usgs_topo": {
        "id": "usgs_topo",
        "label": "🗺️ Surface Topography (USGS Topo)",
        "description": "USGS topographic elevation contours, surface highways, and township boundaries.",
        "icon": "🗺️"
    },
    "satellite_ortho": {
        "id": "satellite_ortho",
        "label": "🛰️ Aerial Satellite Ortho",
        "description": "High-resolution aerial orthophotography, infrastructure footprints, and highway cuts.",
        "icon": "🛰️"
    },
    "lidar_hillshade": {
        "id": "lidar_hillshade",
        "label": "⛰️ Elevation & Shaded Relief (LiDAR 3DEP)",
        "description": "Bare-earth laser radar penetrating canopy to reveal buried rail grades and collapsed adits.",
        "icon": "⛰️"
    },
    "bathymetry_underground": {
        "id": "bathymetry_underground",
        "label": "🌊 Subterranean & Bathymetry",
        "description": "Deep mine shafts down to -2,700 ft, submerged towns, drowned dams, and water tunnels.",
        "icon": "🌊"
    },
    "vertical_cross_section": {
        "id": "vertical_cross_section",
        "label": "📐 Vertical Elevation Cross-Section",
        "description": "Architectural vertical elevation profile from mountain summits to deep subterranean bedrock.",
        "icon": "📐"
    }
}

GRID_SIZE = 100
PIXELS_PER_GRID = 768 / GRID_SIZE

# -----------------------------------------------------------------------------
# 2. BACKWARD COMPATIBLE MOCK NODES & SECRETS (FOR LEGACY TEST COMPATIBILITY)
# -----------------------------------------------------------------------------

NODES = {
    "Washington_Borough": {"x": 50, "y": 50, "color": "blue", "label": "Washington Safe-Zone"},
    "Route_31_Chokepoint": {"x": 50, "y": 35, "color": "red", "label": "Route 31 Blockade"},
    "Oxford_Mines": {"x": 53, "y": 48, "color": "purple", "label": "Oxford Mine Vaults"}
}

CONNECTIONS = [
    ("Washington_Borough", "Route_31_Chokepoint"),
    ("Route_31_Chokepoint", "Oxford_Mines")
]

SECRETS = {
    "Smugglers_Cache": {
        "x": 52, "y": 48, "color": "gold", "label": "Smuggler's Drop",
        "skill": "Cartography I", "layer": "usgs_topo"
    },
    "Aether_Well": {
        "x": 45, "y": 30, "color": "magenta", "label": "Aether-Well",
        "skill": "Aether-Mapping", "layer": "bathymetry_underground"
    },
    "Old_Subway": {
        "x": 55, "y": 40, "color": "darkgray", "label": "Collapsed Subway",
        "skill": "Cartography II", "layer": "lidar_hillshade"
    },
    "Abandoned_Warren_Railroad": {
        "x": 54, "y": 52, "color": "cyan", "label": "Warren RR Cut (1856)",
        "skill": "Cartography I", "layer": "lidar_hillshade"
    },
    "Oxford_Deep_Stopes": {
        "x": 53, "y": 47, "color": "crimson", "label": "Oxford Washington Shaft (-2700 ft)",
        "skill": "Cartography II", "layer": "bathymetry_underground"
    },
    "ATT_Netcong_EMP_Bunker": {
        "x": 68, "y": 32, "color": "yellow", "label": "AT&T Roxbury Vault",
        "skill": "Aether-Mapping", "layer": "bathymetry_underground"
    },
    "Sterling_Hill_Rainbow_Caverns": {
        "x": 55, "y": 28, "color": "magenta", "label": "Sterling Hill UV Tunnels (-2675 ft)",
        "skill": "Cartography III", "layer": "bathymetry_underground"
    },
    "Mt_Hope_Leonard_Vein": {
        "x": 62, "y": 36, "color": "purple", "label": "Mt. Hope Leonard Shaft (-2694 ft)",
        "skill": "Cartography II", "layer": "bathymetry_underground"
    },
    "Lausanne_7_Mile_Discharge": {
        "x": 26, "y": 32, "color": "cyan", "label": "Lausanne Drainage Adit (7.5 Mi)",
        "skill": "Cartography II", "layer": "bathymetry_underground"
    },
    "Friedensville_President_Engine": {
        "x": 42, "y": 48, "color": "purple", "label": "Friedensville 'The President' Sump (-1260 ft)",
        "skill": "Cartography II", "layer": "bathymetry_underground"
    },
    "Princeton_PPPL_Tokamak_Cryo": {
        "x": 62, "y": 66, "color": "magenta", "label": "Princeton Tokamak Plasma Trench",
        "skill": "Aether-Mapping", "layer": "usgs_topo"
    },
    "Mauch_Chunk_Gravity_Switchback": {
        "x": 24, "y": 35, "color": "gold", "label": "Mauch Chunk Gravity Grade (1827)",
        "skill": "Cartography I", "layer": "lidar_hillshade"
    },
    "Doylestown_Concrete_Vaults": {
        "x": 48, "y": 62, "color": "darkgray", "label": "Fonthill Concrete Crypts",
        "skill": "Cartography I", "layer": "lidar_hillshade"
    },
    "Lake_Hopatcong_Sunken_Boiler": {
        "x": 60, "y": 32, "color": "cyan", "label": "Lake Hopatcong 1750 Forge Dam",
        "skill": "Cartography I", "layer": "bathymetry_underground"
    }
}

HIDDEN_CONNECTIONS = [
    ("Washington_Borough", "Smugglers_Cache", "Cartography I"),
    ("Route_31_Chokepoint", "Aether_Well", "Aether-Mapping"),
]

GLOBAL_RAID_MAP_NODES = {
    "grand_canyon_monolith": {"px": 145, "py": 310, "label": "Grand Canyon (50F)", "floors": 50},
    "pohatcong_spire": {"px": 245, "py": 285, "label": "Pohatcong Spire (10F)", "floors": 10},
    "delaware_abyss": {"px": 230, "py": 255, "label": "Delaware Gap (16F)", "floors": 16},
    "black_forest_citadel": {"px": 415, "py": 245, "label": "Black Forest (24F)", "floors": 24},
    "vatican_catacombs": {"px": 430, "py": 300, "label": "Rome Catacombs (36F)", "floors": 36},
    "tokyo_override": {"px": 665, "py": 305, "label": "Tokyo Override (30F)", "floors": 30},
}

GLOBAL_LEYLINE_LINKS = [
    ("pohatcong_spire", "delaware_abyss"),
    ("delaware_abyss", "black_forest_citadel"),
    ("black_forest_citadel", "tokyo_override"),
    ("tokyo_override", "vatican_catacombs"),
    ("vatican_catacombs", "grand_canyon_monolith"),
]

# -----------------------------------------------------------------------------
# 3. COORDINATE PROJECTION & DEPTH TELEMETRY MATHEMATICS
# -----------------------------------------------------------------------------

def gps_to_grid(lat: float, lon: float, sector_id: str = "sector1_primary") -> Tuple[float, float]:
    """
    Projects WGS84 GPS (latitude, longitude) to local sector grid coordinates (0 to 100).
    Origin (50, 50) corresponds to the sector's center GPS.
    """
    sector = SECTORS.get(sector_id, SECTORS["sector1_primary"])
    bounds = sector.get("bounds_lat_lon")
    if not bounds:
        return 50.0, 50.0

    north, south = bounds["north"], bounds["south"]
    east, west = bounds["east"], bounds["west"]

    # Linear interpolation within sector bounding box
    if north == south or east == west:
        return 50.0, 50.0

    gx = ((lon - west) / (east - west)) * 100.0
    # Y is inverted (North is top = 0, South is bottom = 100)
    gy = ((north - lat) / (north - south)) * 100.0

    # Clamp to [0, 100]
    gx = max(0.0, min(100.0, gx))
    gy = max(0.0, min(100.0, gy))
    return gx, gy

def grid_to_gps(gx: float, gy: float, sector_id: str = "sector1_primary") -> Tuple[float, float]:
    """
    Inverse projection: maps sector grid coordinates (0 to 100) back to WGS84 (lat, lon).
    """
    sector = SECTORS.get(sector_id, SECTORS["sector1_primary"])
    bounds = sector.get("bounds_lat_lon")
    if not bounds:
        return sector.get("center_gps", (40.7584, -74.9793))

    north, south = bounds["north"], bounds["south"]
    east, west = bounds["east"], bounds["west"]

    lon = west + (gx / 100.0) * (east - west)
    lat = north - (gy / 100.0) * (north - south)
    return lat, lon

def calculate_depth_telemetry(collar_asl_ft: float, bottom_asl_ft: float, phreatic_table_asl: float = 400.0) -> Dict[str, Any]:
    """
    Computes subterranean overburden, water table inundation status, and hydrostatic pressure PSI.
    Hydrostatic water gradient: 0.433 PSI per vertical foot of freshwater.
    """
    depth_ft = max(0.0, collar_asl_ft - bottom_asl_ft)
    submerged = bottom_asl_ft < phreatic_table_asl
    water_head_ft = max(0.0, phreatic_table_asl - bottom_asl_ft)
    psi = round(water_head_ft * 0.433, 2)

    return {
        "collar_asl_ft": collar_asl_ft,
        "bottom_asl_ft": bottom_asl_ft,
        "depth_ft": int(depth_ft),
        "overburden_ft": int(depth_ft),
        "submerged": submerged,
        "water_head_ft": int(water_head_ft),
        "hydrostatic_psi": psi,
        "environment_state": "Flooded / Sump" if submerged else "Dry Bedrock Cavity",
        "travel_minutes": 0
    }

# -----------------------------------------------------------------------------
# 4. WORLD ATLAS ZONE REGISTRATION
# -----------------------------------------------------------------------------

def get_sector_zones(sector_id: str) -> List[Dict[str, Any]]:
    """
    Extracts and maps zones from backend.world_atlas onto the requested sector.
    """
    try:
        from backend.world_atlas import WORLD_ATLAS_ZONES
    except ImportError:
        # Fallback to legacy mock nodes
        return [
            {"id": k, "name": v["label"], "category": "safe_zone", "coords": {"x": v["x"], "y": v["y"]}, "color": v["color"]}
            for k, v in NODES.items()
        ]

    sector = SECTORS.get(sector_id, SECTORS["sector1_primary"])
    s_radius = sector["radius_miles"]
    s_center_lat, s_center_lon = sector["center_gps"]

    matched_zones = []
    for z_id, z in WORLD_ATLAS_ZONES.items():
        # Check radial distance from sector center
        dist = z.get("distance_miles", 0.0)
        quad = z.get("quadrant", "")

        include = False
        if sector_id == "sector0_core" and dist <= 5.0:
            include = True
        elif sector_id == "sector1_primary" and ("Inner Core" in quad or dist <= 25.0):
            include = True
        elif sector_id == "sector_ring_20_50mi_master" and (18.0 <= dist <= 52.0):
            include = True
        elif sector_id == "sector_ring_20_50mi_nw" and (18.0 <= dist <= 52.0 or "West" in quad) and (260 <= z.get("bearing_deg", 0) <= 360 or 0 <= z.get("bearing_deg", 0) <= 20):
            include = True
        elif sector_id == "sector_ring_20_50mi_ne" and (18.0 <= dist <= 52.0 or "North" in quad) and (0 <= z.get("bearing_deg", 0) <= 100):
            include = True
        elif sector_id == "sector_ring_20_50mi_sw" and (18.0 <= dist <= 52.0 or "South" in quad) and (180 <= z.get("bearing_deg", 0) <= 270):
            include = True
        elif sector_id == "sector_ring_20_50mi_se" and (18.0 <= dist <= 52.0 or "East" in quad) and (80 <= z.get("bearing_deg", 0) <= 190):
            include = True
        elif sector_id == "sector2_west_nw" and ("West" in quad or "Northwest" in quad):
            include = True
        elif sector_id == "sector3_north_east" and ("North" in quad or "East" in quad):
            include = True
        elif sector_id == "sector4_south_sw" and ("South" in quad or "Southwest" in quad):
            include = True
        elif sector_id == "master_100mi":
            include = True

        if include:
            z_copy = dict(z)
            # Compute sector grid coordinates
            if "real_coords" in z:
                lat, lon = z["real_coords"]["lat"], z["real_coords"]["lon"]
                gx, gy = gps_to_grid(lat, lon, sector_id)
            else:
                # Use mapped relative coords
                gx = z.get("coords", {}).get("x", 50)
                gy = z.get("coords", {}).get("y", 50)
            z_copy["sector_gx"] = gx
            z_copy["sector_gy"] = gy
            matched_zones.append(z_copy)

    return matched_zones

def get_available_layers(sector_id: str) -> List[str]:
    """Returns available layers for a given sector."""
    if sector_id == "global_raid":
        return ["usgs_topo"]
    if sector_id == "master_100mi":
        return ["usgs_topo", "lidar_hillshade", "satellite_ortho"]
    return list(LAYERS.keys())

# -----------------------------------------------------------------------------
# 5. CARTOGRAPHY SKILL GATING
# -----------------------------------------------------------------------------

def has_cartography_skill(req_skill: Optional[str], p_skills: Any) -> bool:
    """Checks if player meets Cartography or exploration skill requirements across V1 list or V2 1-1000 dict."""
    if req_skill is None:
        return True
    if not p_skills:
        return False
    req_lower = req_skill.lower().strip()

    # Direct string match (backwards compatibility)
    skill_keys = list(p_skills.keys()) if isinstance(p_skills, dict) else [str(s) for s in p_skills]
    if any(req_lower in s.lower() or "omniscience (dev)" in s.lower() for s in skill_keys):
        return True

    # V2 1-1000 Cartography mastery threshold check
    if isinstance(p_skills, dict):
        cart_mastery = 0
        for s_name, s_val in p_skills.items():
            if any(k in s_name.lower() for k in ("cartograph", "aether-map", "navigat", "survey")):
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

# -----------------------------------------------------------------------------
# 6. MAP STATE PERSISTENCE (ATOMIC & COMPATIBLE)
# -----------------------------------------------------------------------------

def load_map_state() -> Dict[str, Any]:
    if os.path.exists(MAP_STATE_FILE):
        try:
            with open(MAP_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Default map state centered at Washington Borough (50, 50)
    return {
        "player_x": 50,
        "player_y": 50,
        "active_sector": "sector1_primary",
        "active_layer": "usgs_topo",
        "elevation_asl": 460,
        "explored_tiles": [[50, 50], [50, 49], [51, 50], [49, 50], [50, 51]],
        "explored_sectors": {"sector1_primary": [[50, 50], [50, 49], [51, 50], [49, 50], [50, 51]]},
        "macro_mode": False
    }

def save_map_state(state: Dict[str, Any]) -> None:
    try:
        tmp_file = MAP_STATE_FILE + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)
        os.replace(tmp_file, MAP_STATE_FILE)
    except Exception as e:
        print(f"Error saving map state: {e}")

# -----------------------------------------------------------------------------
# 7. MULTI-LAYER, MULTI-SECTOR TACTICAL COMPOSITE RENDERER
# -----------------------------------------------------------------------------

_OVERLAY_CACHE_HASH: Optional[str] = None

def _resolve_base_layer_image(sector_id: str, layer_id: str) -> Optional[Image.Image]:
    """
    Loads the base map image from optimized/ or raw/ storage.
    If not available, generates a procedural tactical grid.
    """
    # 1. Try optimized version
    opt_path = os.path.join(MAPS_DIR, "optimized", sector_id, f"{layer_id}.jpg")
    if os.path.exists(opt_path):
        try:
            return Image.open(opt_path).convert("RGBA")
        except Exception:
            pass

    # 2. Try raw plate
    sector = SECTORS.get(sector_id, {})
    prefix = sector.get("prefix", "")
    suffix_map = {
        "usgs_topo": "01_USGS_Topo_HiRes.png" if sector_id != "master_100mi" else "01_USGS_Topo_Overview.png",
        "satellite_ortho": "02_Satellite_Ortho_HiRes.png" if sector_id != "master_100mi" else "03_Satellite_Hybrid_Overview.png",
        "lidar_hillshade": "03_LiDAR_3DEP_Hillshade.png" if sector_id != "master_100mi" else "02_LiDAR_3DEP_Shaded_Relief_Overview.png",
        "bathymetry_underground": "04_Underground_and_Bathymetry_Map.png",
        "vertical_cross_section": "05_Vertical_Cross_Section.png"
    }
    raw_filename = f"{prefix}_{suffix_map.get(layer_id, '01_USGS_Topo_HiRes.png')}"
    raw_path = os.path.join(MAPS_DIR, "raw", raw_filename)
    if os.path.exists(raw_path):
        try:
            with Image.open(raw_path) as raw_img:
                return raw_img.convert("RGBA").resize((768, 768), Image.Resampling.LANCZOS)
        except Exception:
            pass

    # 3. Legacy base_map.jpg fallback
    legacy_base = os.path.join(BASE_DIR, "base_map.jpg")
    if os.path.exists(legacy_base):
        try:
            return Image.open(legacy_base).convert("RGBA").resize((768, 768))
        except Exception:
            pass

    # 4. Procedural Tactical Fallback
    bg_color = (15, 23, 42, 255)
    if layer_id == "lidar_hillshade":
        bg_color = (35, 45, 60, 255)
    elif layer_id == "bathymetry_underground":
        bg_color = (8, 25, 45, 255)
    elif layer_id == "vertical_cross_section":
        bg_color = (20, 20, 30, 255)

    base = Image.new("RGBA", (768, 768), bg_color)
    draw = ImageDraw.Draw(base)
    # Tactical grid lines
    grid_col = (50, 75, 105, 100)
    for g in range(0, 768, int(PIXELS_PER_GRID * 5)):
        draw.line([(g, 0), (g, 768)], fill=grid_col, width=1)
        draw.line([(0, g), (768, g)], fill=grid_col, width=1)
    return base


def render_sector_layer(
    sector_id: str = "sector1_primary",
    layer_id: str = "usgs_topo",
    player_state: Optional[Dict[str, Any]] = None,
    character_id: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Renders the tactical map composite for the specified sector and layer.
    Returns: (output_image_path, telemetry_dict)
    """
    global _OVERLAY_CACHE_HASH

    if sector_id == "global_raid":
        return generate_global_atlas_overlay(player_state), {
            "mode": "global_raid",
            "travel_minutes": 0,
            "player_gps": (0.0, 0.0),
            "bottom_asl_ft": 0,
            "overburden_ft": 0,
            "hydrostatic_psi": 0.0,
            "environment_state": "Planetary Surface"
        }

    state = load_map_state()
    p_skills = (player_state or {}).get("skills", [])
    player_x = state.get("player_x", 50)
    player_y = state.get("player_y", 50)
    p_loc = (player_state or {}).get("location", "Sector 1 Safe-Zone: Washington Borough, NJ")

    # Determine elevation and depth telemetry
    collar_asl = 460
    bottom_asl = 460
    if "sterling" in p_loc.lower() or "ogdensburg" in p_loc.lower():
        collar_asl = 720
        bottom_asl = -1955 # Sterling Hill 2,675 ft deep
    elif "mount hope" in p_loc.lower() or "leonard" in p_loc.lower():
        collar_asl = 900
        bottom_asl = -1794 # Mt. Hope 2,694 ft deep
    elif "friedensville" in p_loc.lower():
        collar_asl = 420
        bottom_asl = -840 # Friedensville 1,260 ft deep
    elif "lausanne" in p_loc.lower():
        collar_asl = 950
        bottom_asl = 500 # Lausanne Tunnel 450 ft overburden
    elif "high point" in p_loc.lower():
        collar_asl = 1803
        bottom_asl = 1803
    elif "camelback" in p_loc.lower() or "pocono" in p_loc.lower():
        collar_asl = 2133
        bottom_asl = 2133
    elif "mine" in p_loc.lower() or "shaft" in p_loc.lower() or "oxford" in p_loc.lower():
        collar_asl = 600
        bottom_asl = -2100 # Oxford 2,700 ft deep
    elif "merrill" in p_loc.lower():
        collar_asl = 750
        bottom_asl = 525 # Merrill Creek 225 ft deep
    elif "siphon" in p_loc.lower() or "aqueduct" in p_loc.lower():
        collar_asl = 400
        bottom_asl = -1114 # Hudson Siphon
    elif "slide" in p_loc.lower() or "mountain" in p_loc.lower():
        collar_asl = 1500
        bottom_asl = 1500

    telemetry = calculate_depth_telemetry(collar_asl, bottom_asl)
    telemetry.update({
        "sector_id": sector_id,
        "layer_id": layer_id,
        "sector_name": SECTORS.get(sector_id, {}).get("name", sector_id),
        "layer_label": LAYERS.get(layer_id, {}).get("label", layer_id),
        "player_grid": (player_x, player_y),
        "player_gps": grid_to_gps(player_x, player_y, sector_id),
        "travel_minutes": 0
    })

    # Cache signature check
    sig_payload = {
        "sector": sector_id,
        "layer": layer_id,
        "px": player_x,
        "py": player_y,
        "skills": str(p_skills),
        "loc": p_loc,
        "explored": state.get("explored_sectors", {}).get(sector_id, state.get("explored_tiles", []))
    }
    sig_hash = hashlib.md5(json.dumps(sig_payload, sort_keys=True, default=str).encode()).hexdigest()

    out_file = CURRENT_TACTICAL_MAP_FILE
    if _OVERLAY_CACHE_HASH == sig_hash and os.path.exists(out_file):
        return out_file, telemetry

    base_img = _resolve_base_layer_image(sector_id, layer_id)
    if not base_img:
        return CURRENT_MAP_FILE, telemetry

    w, h = base_img.size
    px_scale_x = w / 100.0
    px_scale_y = h / 100.0

    # SPECIAL HANDLING FOR VERTICAL CROSS-SECTION
    if layer_id == "vertical_cross_section":
        draw = ImageDraw.Draw(base_img)
        # Draw player elevation indicator horizontal reticle across cross-section
        # Map elevation: +2000 ft (top 15%) down to -3000 ft (bottom 85%)
        elev_pct = (2000 - bottom_asl) / 5000.0
        marker_y = int(h * 0.15 + elev_pct * (h * 0.70))
        marker_y = max(10, min(h - 20, marker_y))

        # Cyan laser elevation line
        draw.line([(0, marker_y), (w, marker_y)], fill=(0, 255, 255, 220), width=2)
        # Reticle triangle
        marker_x = int(w * 0.45)
        draw.polygon([(marker_x, marker_y - 8), (marker_x + 12, marker_y), (marker_x, marker_y + 8)], fill="cyan", outline="white")
        draw.rectangle([marker_x + 18, marker_y - 14, marker_x + 240, marker_y + 14], fill=(10, 15, 25, 210), outline=(0, 255, 255))
        draw.text((marker_x + 24, marker_y - 8), f"PLAYER: {bottom_asl} ft ASL | {telemetry['depth_ft']} ft Depth", fill="white")

        # Telemetry watermark box
        draw.rectangle([15, 15, 340, 75], fill=(5, 10, 20, 220), outline=(0, 200, 255), width=2)
        draw.text((25, 22), "VERTICAL DATUM: NAVD88 ELEVATION SLICE", fill=(0, 230, 255))
        draw.text((25, 40), f"Overburden Depth: {telemetry['depth_ft']} ft | PSI: {telemetry['hydrostatic_psi']}", fill="white")
        draw.text((25, 56), f"Environment: {telemetry['environment_state']}", fill=(255, 200, 80))

        rgb_img = base_img.convert("RGB")
        rgb_img.save(out_file, "JPEG", quality=90)
        rgb_img.save(CURRENT_MAP_FILE, "JPEG", quality=90)
        _OVERLAY_CACHE_HASH = sig_hash
        return out_file, telemetry

    # SPATIAL LAYERS: FOG OF WAR & REVEALS
    fog = Image.new("RGBA", (w, h), (0, 0, 0, 195))
    mask = Image.new("L", (w, h), 195)
    mask_draw = ImageDraw.Draw(mask)

    # Explored tiles
    sector_explored = state.get("explored_sectors", {}).get(sector_id, state.get("explored_tiles", []))
    for coords in sector_explored:
        gx, gy = coords[0], coords[1]
        px, py = gx * px_scale_x, gy * px_scale_y
        radius = px_scale_x * 4.0
        mask_draw.ellipse([px - radius, py - radius, px + radius, py + radius], fill=0)

    # Reveal Zones
    sector_zones = get_sector_zones(sector_id)
    for z in sector_zones:
        gx = z.get("sector_gx", 50)
        gy = z.get("sector_gy", 50)
        px, py = gx * px_scale_x, gy * px_scale_y
        reveal_r = px_scale_x * 5.0 if z.get("is_safe_zone") else px_scale_x * 3.5
        mask_draw.ellipse([px - reveal_r, py - reveal_r, px + reveal_r, py + reveal_r], fill=0)

    # Reveal Secrets gated by Cartography / Aether-Mapping
    unlocked_secrets = {}
    for s_key, s_data in SECRETS.items():
        s_layer = s_data.get("layer", "usgs_topo")
        # Secrets visible on this layer or Topo
        if s_layer == layer_id or s_layer == "usgs_topo" or layer_id == "usgs_topo":
            if has_cartography_skill(s_data.get("skill"), p_skills):
                unlocked_secrets[s_key] = s_data
                px, py = s_data["x"] * px_scale_x, s_data["y"] * px_scale_y
                mask_draw.ellipse([px - px_scale_x * 2.5, py - px_scale_y * 2.5, px + px_scale_x * 2.5, py + px_scale_y * 2.5], fill=0)

    fog.putalpha(mask)
    map_img = Image.alpha_composite(base_img, fog)
    draw = ImageDraw.Draw(map_img)

    # Draw Transit Connections in Sector
    if sector_id in ("sector0_core", "sector1_primary"):
        for n1, n2 in CONNECTIONS:
            if n1 in NODES and n2 in NODES:
                x1, y1 = NODES[n1]["x"] * px_scale_x, NODES[n1]["y"] * px_scale_y
                x2, y2 = NODES[n2]["x"] * px_scale_x, NODES[n2]["y"] * px_scale_y
                draw.line([x1, y1, x2, y2], fill=(220, 60, 60, 160), width=3)

    # Draw Sector Zone Nodes
    for z in sector_zones:
        gx = z.get("sector_gx", 50)
        gy = z.get("sector_gy", 50)
        px, py = gx * px_scale_x, gy * px_scale_y
        cat = z.get("category", "wilderness")
        name = z.get("name", "Zone")

        if cat == "safe_zone" or z.get("is_safe_zone"):
            node_col = (30, 200, 255) # Cyan/Blue Safe Zone
            draw.ellipse([px - 7, py - 7, px + 7, py + 7], fill=node_col, outline="white", width=2)
            draw.text((px + 10, py - 9), name, fill="white")
        elif cat == "mine":
            node_col = (180, 80, 240) # Purple Mine
            draw.rectangle([px - 6, py - 6, px + 6, py + 6], fill=node_col, outline="white", width=2)
            draw.text((px + 10, py - 9), name, fill=(210, 160, 255))
        elif cat == "dungeon":
            node_col = (255, 60, 80) # Crimson Dungeon
            draw.polygon([(px, py - 8), (px + 7, py + 6), (px - 7, py + 6)], fill=node_col, outline="white")
            draw.text((px + 10, py - 9), name, fill=(255, 120, 120))
        else:
            node_col = (240, 170, 40) # Amber Landmark
            draw.ellipse([px - 5, py - 5, px + 5, py + 5], fill=node_col, outline="black", width=1)
            draw.text((px + 8, py - 7), name, fill=(250, 210, 100))

    # Draw Secrets (Diamonds)
    for s_key, s_data in unlocked_secrets.items():
        px, py = s_data["x"] * px_scale_x, s_data["y"] * px_scale_y
        col = s_data.get("color", "gold")
        draw.polygon([(px, py - 7), (px + 7, py), (px, py + 7), (px - 7, py)], fill=col, outline="white", width=1)
        draw.text((px + 9, py - 8), s_data["label"], fill=col)

    # Draw Player Position (Cyan Triangle)
    ppx = player_x * px_scale_x
    ppy = player_y * px_scale_y
    draw.polygon([(ppx, ppy - 12), (ppx - 9, ppy + 9), (ppx + 9, ppy + 9)], fill="cyan", outline="black")
    draw.ellipse([ppx - 14, ppy - 14, ppx + 14, ppy + 14], outline=(0, 255, 255, 180), width=2)

    # Draw Tactical HUD Header & Legend
    try:
        legend_w = 260
        legend_h = 105
        draw.rectangle([10, 10, 10 + legend_w, 10 + legend_h], fill=(10, 15, 25, 210), outline=(0, 200, 255), width=2)
        draw.text((18, 16), f"TACTICAL RADAR // {SECTORS.get(sector_id, {}).get('name', 'SECTOR')}", fill=(0, 230, 255))
        draw.text((18, 34), f"Layer: {LAYERS.get(layer_id, {}).get('label', layer_id)}", fill="white")
        draw.text((18, 52), f"Grid: ({player_x:.1f}, {player_y:.1f}) | ASL: {collar_asl} ft", fill=(200, 220, 240))
        draw.text((18, 70), "Blue: Safe | Purple: Mine | Red: Dungeon | Gold: Secret", fill=(170, 190, 210))
        draw.text((18, 88), "Cyan Chevron: Player Unit Vector", fill=(0, 255, 255))
    except Exception:
        pass

    rgb_img = map_img.convert("RGB")
    try:
        rgb_img.save(out_file, "JPEG", quality=90)
        # Update legacy CURRENT_MAP_FILE as well
        rgb_img.save(CURRENT_MAP_FILE, "JPEG", quality=90)
        _OVERLAY_CACHE_HASH = sig_hash
    finally:
        rgb_img.close()
        map_img.close()
        fog.close()
        mask.close()
        base_img.close()

    return out_file, telemetry

# -----------------------------------------------------------------------------
# 8. LEGACY COMPATIBILITY WRAPPERS
# -----------------------------------------------------------------------------

def generate_overlay(player_skills: Any = None) -> Optional[str]:
    """Legacy backward-compatible facade for Sector 1 tactical overlay."""
    p_state = {"skills": player_skills or []}
    out_path, _ = render_sector_layer("sector1_primary", "usgs_topo", player_state=p_state)
    return out_path

def generate_global_atlas_overlay(player_state: Optional[Dict[str, Any]] = None) -> str:
    """Renders the Global Patchwork Earth Atlas (768x440 tactical projection)."""
    raids_data = (player_state or {}).get("planetary_raids", {}) if isinstance(player_state, dict) else {}
    width, height = 768, 440
    img = Image.new("RGB", (width, height), (12, 18, 32))
    try:
        draw = ImageDraw.Draw(img)
        for gx in range(0, width, 64):
            draw.line([(gx, 0), (gx, height)], fill=(25, 38, 62), width=1)
        for gy in range(0, height, 55):
            draw.line([(0, gy), (width, gy)], fill=(25, 38, 62), width=1)

        draw.polygon([(70, 180), (290, 170), (275, 355), (120, 360)], fill=(22, 42, 58), outline=(45, 90, 120))
        draw.polygon([(365, 175), (505, 175), (495, 335), (375, 330)], fill=(22, 42, 58), outline=(45, 90, 120))
        draw.polygon([(545, 185), (715, 195), (695, 365), (560, 350)], fill=(22, 42, 58), outline=(45, 90, 120))

        active_raid = raids_data.get("active_raid_id", "pohatcong_spire")
        raid_nodes = raids_data.get("raid_nodes", {})

        for r1, r2 in GLOBAL_LEYLINE_LINKS:
            n1, n2 = GLOBAL_RAID_MAP_NODES[r1], GLOBAL_RAID_MAP_NODES[r2]
            unsealed = raid_nodes.get(r2, {}).get("gate_unsealed", False)
            line_col = (0, 220, 255) if unsealed else (95, 70, 95)
            draw.line([(n1["px"], n1["py"]), (n2["px"], n2["py"])], fill=line_col, width=3 if unsealed else 1)

        for r_id, coord in GLOBAL_RAID_MAP_NODES.items():
            px, py = coord["px"], coord["py"]
            live = raid_nodes.get(r_id, {})
            is_stabilized = live.get("is_stabilized", False)
            is_unsealed = live.get("gate_unsealed", r_id == "pohatcong_spire")
            cur_f = live.get("current_floor", 1)
            tot_f = coord["floors"]

            if is_stabilized:
                node_col = (40, 225, 130)
            elif is_unsealed:
                node_col = (255, 165, 40)
            else:
                node_col = (140, 60, 75)

            draw.ellipse([px - 9, py - 9, px + 9, py + 9], fill=node_col, outline="white", width=2)
            if r_id == active_raid:
                draw.ellipse([px - 15, py - 15, px + 15, py + 15], outline=(0, 255, 255), width=2)
            draw.text((px - 45, py + 12), f"{coord['label']} [F{cur_f}/{tot_f}]", fill="white")

        draw.rectangle([10, 10, 425, 58], fill=(8, 12, 22), outline=(0, 200, 255))
        draw.text((18, 16), "PLANETARY PATCHWORK OVERLAY // GLOBAL RAID ATLAS", fill=(0, 230, 255))
        draw.text((18, 34), "Green: Stabilized (0% Bleed) | Orange: Gate Open | Red: Overland Only", fill=(200, 215, 230))

        img.save(GLOBAL_MAP_FILE)
    finally:
        img.close()
    return GLOBAL_MAP_FILE

if __name__ == "__main__":
    generate_overlay()
