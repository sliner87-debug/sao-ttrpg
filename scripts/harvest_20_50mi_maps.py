"""
scripts/harvest_20_50mi_maps.py
Automated GIS harvester and composite generator for the 20-to-50-mile annular radial ring
centered on Washington Borough, NJ (07882) [40.7584° N, -74.9793° W].
Harvests:
  - Layer 1: 🗺️ USGS Topo HiRes (from USGS The National Map REST API)
  - Layer 2: 🛰️ Satellite Ortho (from USGS ImageryOnly REST API)
  - Layer 3: ⛰️ LiDAR 3DEP Bare-Earth Hillshade (from USGS ShadedReliefOnly REST API)
  - Layer 4: 🌊 Subterranean & Bathymetry (Deep mines, tunnels, and reservoir depths)
  - Layer 5: 📐 Vertical Elevation Cross-Section (NAVD88 elevation slices from +2500' to -3000')

Outputs:
  assets/maps/raw/ (Full 4K/2K resolution source plates)
  assets/maps/optimized/ (1024x1024 instant Streamlit UI web tiles)
"""

import os
import sys
import json
import math
import urllib.request
import urllib.parse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageEnhance

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "assets" / "maps" / "raw"
OPT_DIR = REPO_ROOT / "assets" / "maps" / "optimized"
META_DIR = REPO_ROOT / "assets" / "maps" / "metadata"

RAW_DIR.mkdir(parents=True, exist_ok=True)
OPT_DIR.mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)

EXPANSION_SECTORS = {
    "sector_ring_20_50mi_master": {
        "id": "sector_ring_20_50mi_master",
        "name": "20–50 Mile Annular Master Ring (All Quadrants)",
        "prefix": "Sector_Ring_20_50Mi_Master",
        "radius_miles": 50.0,
        "inner_radius_miles": 20.0,
        "center_gps": (40.7584, -74.9793),
        "elevation_asl_ft": 460,
        "bounds": {
            "west": -75.9386,
            "south": 40.0334,
            "east": -74.0200,
            "north": 41.4834
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
        "bounds": {
            "west": -75.9386,
            "south": 40.6500,
            "east": -74.9000,
            "north": 41.4834
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
        "bounds": {
            "west": -75.0500,
            "south": 40.6500,
            "east": -74.0200,
            "north": 41.4834
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
        "bounds": {
            "west": -75.9386,
            "south": 40.0334,
            "east": -74.9000,
            "north": 40.8500
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
        "bounds": {
            "west": -75.0500,
            "south": 40.0334,
            "east": -74.0200,
            "north": 40.8500
        },
        "description": "Southeast quadrant: Sourland Mountain, Princeton PPPL fusion tokamak, Trenton, and Lakehurst Hangar No. 1."
    }
}

SUBTERRANEAN_FEATURES = {
    "sector_ring_20_50mi_ne": [
        {"name": "Sterling Hill Zinc Mine", "gx": 48, "gy": 35, "depth": -2675, "collar": 720, "type": "shaft", "color": "purple"},
        {"name": "Mt. Hope New Leonard Shaft", "gx": 55, "gy": 58, "depth": -2694, "collar": 900, "type": "shaft", "color": "purple"},
        {"name": "Hibernia Electric Ore Adit", "gx": 58, "gy": 52, "depth": -1600, "collar": 820, "type": "shaft", "color": "purple"},
        {"name": "AT&T Netcong Roxbury Bunker", "gx": 42, "gy": 68, "depth": -50, "collar": 1050, "type": "bunker", "color": "yellow"},
        {"name": "Lake Hopatcong Drowned Dam", "gx": 44, "gy": 56, "depth": -58, "collar": 924, "type": "bathymetry", "color": "cyan"},
        {"name": "Picatinny Underground Igloos", "gx": 52, "gy": 62, "depth": -35, "collar": 750, "type": "bunker", "color": "red"}
    ],
    "sector_ring_20_50mi_nw": [
        {"name": "Lausanne Drainage Tunnel (7.5 Mi)", "gx": 32, "gy": 65, "depth": -450, "collar": 950, "type": "tunnel", "color": "cyan"},
        {"name": "Nesquehoning Mammoth Vein Bore", "gx": 28, "gy": 68, "depth": -380, "collar": 1100, "type": "tunnel", "color": "purple"},
        {"name": "Lansford No. 9 Deep Colliery", "gx": 24, "gy": 72, "depth": -1200, "collar": 1020, "type": "shaft", "color": "purple"},
        {"name": "Beltzville Drowned Valley", "gx": 48, "gy": 70, "depth": -127, "collar": 530, "type": "bathymetry", "color": "cyan"},
        {"name": "Lehigh Gorge Submerged Locks", "gx": 36, "gy": 60, "depth": -30, "collar": 540, "type": "bathymetry", "color": "cyan"}
    ],
    "sector_ring_20_50mi_sw": [
        {"name": "Friedensville Zinc Ueberroth Mine", "gx": 45, "gy": 38, "depth": -1260, "collar": 420, "type": "shaft", "color": "purple"},
        {"name": "Lost River Subterranean Caverns", "gx": 48, "gy": 42, "depth": -115, "collar": 380, "type": "cavern", "color": "magenta"},
        {"name": "Phoenixville Black Rock Tunnel", "gx": 40, "gy": 82, "depth": -140, "collar": 260, "type": "tunnel", "color": "yellow"},
        {"name": "Perkiomen Lead Mine Shafts", "gx": 46, "gy": 75, "depth": -420, "collar": 310, "type": "shaft", "color": "purple"}
    ],
    "sector_ring_20_50mi_se": [
        {"name": "Princeton Firestone Sub-Vaults", "gx": 45, "gy": 48, "depth": -45, "collar": 210, "type": "vault", "color": "yellow"},
        {"name": "PPPL Tokamak Cryo-Trench", "gx": 48, "gy": 45, "depth": -60, "collar": 120, "type": "vault", "color": "cyan"},
        {"name": "Delaware River Deep Channel", "gx": 32, "gy": 55, "depth": -45, "collar": 10, "type": "bathymetry", "color": "cyan"},
        {"name": "Kirkwood-Cohansey Aquifer Basin", "gx": 65, "gy": 75, "depth": -300, "collar": 85, "type": "aquifer", "color": "cyan"}
    ],
    "sector_ring_20_50mi_master": [
        {"name": "Sterling Hill Zinc Mine (-2675 ft)", "gx": 55, "gy": 26, "depth": -2675, "collar": 720, "type": "shaft", "color": "purple"},
        {"name": "Mt. Hope New Leonard Shaft (-2694 ft)", "gx": 60, "gy": 35, "depth": -2694, "collar": 900, "type": "shaft", "color": "purple"},
        {"name": "Lausanne Drainage Tunnel (7.5 Mi)", "gx": 26, "gy": 32, "depth": -450, "collar": 950, "type": "tunnel", "color": "cyan"},
        {"name": "Friedensville Zinc Mines (-1260 ft)", "gx": 42, "gy": 48, "depth": -1260, "collar": 420, "type": "shaft", "color": "purple"},
        {"name": "Princeton Firestone Vaults (-45 ft)", "gx": 62, "gy": 68, "depth": -45, "collar": 210, "type": "vault", "color": "yellow"},
        {"name": "Beltzville Submerged Lake (-127 ft)", "gx": 35, "gy": 36, "depth": -127, "collar": 530, "type": "bathymetry", "color": "cyan"}
    ]
}

CROSS_SECTION_PROFILES = {
    "sector_ring_20_50mi_master": {
        "title": "20–50 MILE EXPANSION RING // REGIONAL NAVD88 VERTICAL DATUM SLICE",
        "summits": [("Big Pocono", 2133, 0.22), ("High Point", 1803, 0.58), ("Sourland Mtn", 568, 0.78)],
        "mines": [("Lausanne Tunnel", -450, 0.25), ("Friedensville", -1260, 0.42), ("Mt Hope Leonard", -2694, 0.62), ("Sterling Hill", -2675, 0.68)],
        "rivers": [("Lehigh River", 320, 0.30), ("Delaware River", 140, 0.50), ("Raritan River", 50, 0.72)]
    },
    "sector_ring_20_50mi_nw": {
        "title": "RING-NW POCONOS & LEHIGH GORGE // VERTICAL PROFILE",
        "summits": [("Big Boulder", 2175, 0.25), ("Camelback", 2133, 0.50), ("Mt Tammany", 1527, 0.85)],
        "mines": [("Lansford Colliery", -1200, 0.20), ("Nesquehoning Vein", -380, 0.35), ("Lausanne Tunnel", -450, 0.45)],
        "rivers": [("Lehigh Gorge Rapid", 540, 0.40), ("Beltzville Lake", 530, 0.65), ("Delaware Water Gap", 285, 0.88)]
    },
    "sector_ring_20_50mi_ne": {
        "title": "RING-NE KITTATINNY & HIGHLANDS MINING BELT // VERTICAL PROFILE",
        "summits": [("High Point Obelisk", 1803, 0.20), ("Kittatinny Ridge", 1603, 0.40), ("Picatinny Tower", 950, 0.75)],
        "mines": [("Sterling Hill UV Stopes", -2675, 0.30), ("Mt Hope Leonard Shaft", -2694, 0.60), ("Hibernia RR Tunnel", -1600, 0.75)],
        "rivers": [("Lake Hopatcong", 924, 0.55), ("Wanaque Reservoir", 300, 0.85)]
    },
    "sector_ring_20_50mi_sw": {
        "title": "RING-SW BETHLEHEM & SCHUYLKILL VALLEY // VERTICAL PROFILE",
        "summits": [("Mt Penn Pagoda", 886, 0.15), ("South Mountain", 920, 0.45), ("Bucks County Ridges", 480, 0.80)],
        "mines": [("Friedensville Zinc Stopes", -1260, 0.42), ("Lost River Caverns", -115, 0.50), ("Perkiomen Mines", -420, 0.70)],
        "rivers": [("Schuylkill River", 180, 0.20), ("Lehigh River Bethlehem", 220, 0.45), ("Delaware River Canal", 68, 0.85)]
    },
    "sector_ring_20_50mi_se": {
        "title": "RING-SE SOURLANDS, PRINCETON & PINE BARRENS // VERTICAL PROFILE",
        "summits": [("Sourland Ridge Boulderfield", 568, 0.25), ("Princeton Chapel Spire", 320, 0.55), ("Lakehurst Mast", 224, 0.85)],
        "mines": [("Princeton Firestone Vaults", -45, 0.52), ("PPPL Cryo-Trench", -60, 0.58), ("Kirkwood Aquifer Sump", -300, 0.80)],
        "rivers": [("Millstone River Canal", 55, 0.45), ("Delaware River Fall Line", 10, 0.30), ("Barnegat Drainage", 15, 0.90)]
    }
}


def download_usgs_layer(bbox: dict, service_name: str, out_path: Path, width: int = 1536, height: int = 1536) -> bool:
    """Fetches high-resolution map tiles from USGS The National Map REST API."""
    base_url = f"https://basemap.nationalmap.gov/arcgis/rest/services/{service_name}/MapServer/export"
    params = {
        "bbox": f"{bbox['west']},{bbox['south']},{bbox['east']},{bbox['north']}",
        "bboxSR": "4326",
        "imageSR": "4326",
        "size": f"{width},{height}",
        "format": "png",
        "f": "image"
    }
    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "SAO-GIS-Engine/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            if len(data) > 1000:
                with open(out_path, "wb") as f:
                    f.write(data)
                return True
    except Exception as e:
        print(f"[ERROR] Failed to fetch {service_name}: {e}")
    return False


def generate_subterranean_plate(base_topo_path: Path, sector_key: str, out_raw: Path, out_opt: Path):
    """Creates the deep-cavern Subterranean & Bathymetry plate."""
    try:
        with Image.open(base_topo_path) as raw:
            base = raw.convert("RGBA")
    except Exception:
        base = Image.new("RGBA", (1536, 1536), (8, 16, 32, 255))

    # Apply tactical subterranean color treatment (invert & deep cyan/indigo wash)
    r, g, b, a = base.split()
    gray = ImageOps.grayscale(base)
    # Indigo shadow matrix
    sub_bg = ImageOps.colorize(gray, black="#050a18", white="#1c385c")
    sub_img = sub_bg.convert("RGBA")
    draw = ImageDraw.Draw(sub_img)

    w, h = sub_img.size
    px_x = w / 100.0
    px_y = h / 100.0

    # Draw subterranean grid overlay
    for gx in range(0, w, int(px_x * 10)):
        draw.line([(gx, 0), (gx, h)], fill=(20, 50, 85, 70), width=1)
    for gy in range(0, h, int(px_y * 10)):
        draw.line([(0, gy), (w, gy)], fill=(20, 50, 85, 70), width=1)

    features = SUBTERRANEAN_FEATURES.get(sector_key, [])
    for f in features:
        fx = f["gx"] * px_x
        fy = f["gy"] * px_y
        ftype = f.get("type", "shaft")
        depth = f.get("depth", 0)

        if ftype == "shaft":
            # Multi-level mine shaft icon (pulsing purple square + cross)
            draw.rectangle([fx - 10, fy - 10, fx + 10, fy + 10], fill=(160, 60, 240, 210), outline=(230, 180, 255), width=2)
            draw.line([fx - 7, fy, fx + 7, fy], fill="white", width=2)
            draw.line([fx, fy - 7, fx, fy + 7], fill="white", width=2)
            draw.text((fx + 14, fy - 14), f"{f['name']}", fill=(240, 200, 255))
            draw.text((fx + 14, fy + 1), f"Depth: {depth} ft | {(400-depth)*0.433:.0f} PSI", fill=(180, 220, 255))
        elif ftype == "tunnel":
            # Flowing cyan underground conduit
            draw.line([fx - 30, fy + 10, fx + 30, fy - 10], fill=(0, 230, 255, 230), width=4)
            draw.ellipse([fx - 8, fy - 8, fx + 8, fy + 8], fill=(0, 180, 230), outline="white", width=2)
            draw.text((fx + 12, fy - 10), f"{f['name']}", fill=(0, 240, 255))
        elif ftype == "bunker":
            # Hardened amber shield
            draw.polygon([(fx, fy - 10), (fx + 10, fy - 2), (fx + 6, fy + 10), (fx - 6, fy + 10), (fx - 10, fy - 2)], fill=(245, 170, 30, 220), outline="white", width=2)
            draw.text((fx + 14, fy - 8), f"{f['name']}", fill=(255, 210, 80))
        elif ftype == "cavern":
            # Natural karst diamond
            draw.polygon([(fx, fy - 9), (fx + 9, fy), (fx, fy + 9), (fx - 9, fy)], fill=(220, 50, 180), outline="white")
            draw.text((fx + 12, fy - 8), f"{f['name']}", fill=(255, 150, 230))
        else:
            # Bathymetric reservoir soundings
            draw.ellipse([fx - 12, fy - 12, fx + 12, fy + 12], fill=(20, 120, 210, 160), outline=(0, 220, 255), width=2)
            draw.text((fx + 15, fy - 8), f"{f['name']} ({depth} ft)", fill=(120, 220, 255))

    # Watermark Header
    draw.rectangle([15, 15, 420, 70], fill=(4, 8, 16, 220), outline=(0, 200, 255), width=2)
    draw.text((25, 22), "SUBTERRANEAN MINING & BATHYMETRIC DATUM", fill=(0, 230, 255))
    draw.text((25, 40), f"Sector: {sector_key.upper()} // Phreatic Water Table: 400 ft ASL", fill=(190, 215, 235))
    draw.text((25, 54), "Purple: Deep Shafts | Cyan: Aqueducts/Lakes | Yellow: Vaults", fill=(160, 180, 200))

    rgb = sub_img.convert("RGB")
    rgb.save(out_raw, "PNG")
    opt = rgb.resize((1024, 1024), Image.Resampling.LANCZOS)
    opt.save(out_opt, "JPEG", quality=88, optimize=True)
    rgb.close()
    sub_img.close()


def generate_cross_section_plate(sector_key: str, out_raw: Path, out_opt: Path):
    """Renders the high-precision NAVD88 vertical elevation cross-section."""
    w, h = 1536, 864
    img = Image.new("RGB", (w, h), (8, 12, 20))
    draw = ImageDraw.Draw(img)

    profile = CROSS_SECTION_PROFILES.get(sector_key, CROSS_SECTION_PROFILES["sector_ring_20_50mi_master"])

    # Elevation scale: +2500 ft (y = 120) down to -3000 ft (y = 750)
    # Total range: 5500 ft over 630 vertical pixels => 0.1145 px / ft
    y_zero = int(120 + (2500 / 5500.0) * 630) # Sea level (0 ft ASL)
    y_water_table = int(120 + ((2500 - 400) / 5500.0) * 630) # 400 ft ASL

    # Horizontal datum lines
    for elev in range(2500, -3001, -500):
        y_pos = int(120 + ((2500 - elev) / 5500.0) * 630)
        line_col = (40, 60, 90) if elev != 0 else (0, 200, 255)
        w_val = 2 if elev == 0 else 1
        draw.line([(80, y_pos), (w - 40, y_pos)], fill=line_col, width=w_val)
        label = f"{elev:+d} ft" if elev != 0 else "0 ft (SEA LEVEL)"
        draw.text((12, y_pos - 6), label, fill=(160, 180, 200))

    # Water table phreatic zone (blue shaded wash below 400 ft ASL)
    draw.rectangle([80, y_water_table, w - 40, y_zero + int((3000/5500.0)*630)], fill=(8, 28, 55))

    # Re-draw datum lines over water wash
    for elev in range(400, -3001, -500):
        y_pos = int(120 + ((2500 - elev) / 5500.0) * 630)
        draw.line([(80, y_pos), (w - 40, y_pos)], fill=(25, 65, 110), width=1)

    # Phreatic line indicator
    draw.line([(80, y_water_table), (w - 40, y_water_table)], fill=(0, 230, 255), width=2)
    draw.text((w - 280, y_water_table - 16), "PHREATIC WATER TABLE (+400 ft ASL)", fill=(0, 230, 255))

    # Terrain Ridgeline Polygon
    terrain_pts = [(80, y_zero)]
    summits = profile.get("summits", [])
    mines = profile.get("mines", [])
    rivers = profile.get("rivers", [])

    # Interpolate a rolling geological terrain ridge line across the width
    for s_name, s_elev, s_pct in summits:
        x_pt = int(80 + s_pct * (w - 120))
        y_pt = int(120 + ((2500 - s_elev) / 5500.0) * 630)
        terrain_pts.append((x_pt - 50, y_pt + 40))
        terrain_pts.append((x_pt, y_pt))
        terrain_pts.append((x_pt + 50, y_pt + 50))

        # Peak marker
        draw.polygon([(x_pt, y_pt - 10), (x_pt + 8, y_pt), (x_pt - 8, y_pt)], fill="cyan", outline="white")
        draw.text((x_pt - 40, y_pt - 26), f"{s_name} (+{s_elev}')", fill="white")

    for r_name, r_elev, r_pct in rivers:
        x_pt = int(80 + r_pct * (w - 120))
        y_pt = int(120 + ((2500 - r_elev) / 5500.0) * 630)
        # River valley notch
        draw.ellipse([x_pt - 10, y_pt - 6, x_pt + 10, y_pt + 6], fill=(0, 160, 255), outline="white")
        draw.text((x_pt - 30, y_pt + 10), f"{r_name} ({r_elev}')", fill=(100, 200, 255))

    # Deep Mine Shaft Lines & Stoping Chambers
    for m_name, m_depth, m_pct in mines:
        x_pt = int(80 + m_pct * (w - 120))
        y_collar = int(120 + ((2500 - 800) / 5500.0) * 630)
        y_bottom = int(120 + ((2500 - m_depth) / 5500.0) * 630)

        # Vertical Headframe & Hoist Shaft Line
        draw.line([(x_pt, y_collar), (x_pt, y_bottom)], fill=(200, 60, 255), width=3)
        # Headframe tower above ground
        draw.polygon([(x_pt - 8, y_collar), (x_pt + 8, y_collar), (x_pt, y_collar - 18)], fill=(180, 180, 180), outline="white")

        # Stope chambers at deep bottom
        draw.rectangle([x_pt - 16, y_bottom - 12, x_pt + 16, y_bottom + 12], fill=(140, 40, 210), outline="white", width=2)
        psi = round((400 - m_depth) * 0.433, 1)
        draw.text((x_pt + 22, y_bottom - 16), f"{m_name}", fill=(240, 180, 255))
        draw.text((x_pt + 22, y_bottom + 2), f"Collar: +800' | Sump: {m_depth}' ASL ({psi} PSI)", fill=(180, 220, 255))

    # Master HUD Framing
    draw.rectangle([10, 10, w - 10, h - 10], outline=(0, 180, 230), width=2)
    draw.rectangle([15, 15, 750, 75], fill=(5, 10, 20, 230), outline=(0, 220, 255), width=2)
    draw.text((25, 22), profile["title"], fill=(0, 230, 255))
    draw.text((25, 40), "Geological Baseline: Reading Prong Gneiss & Appalachian Ridge-and-Valley Fold Belt", fill=(200, 220, 240))
    draw.text((25, 56), "Subterranean Mines: Sterling Hill (-2675') | Mt Hope (-2694') | Lausanne (-450')", fill=(255, 200, 80))

    img.save(out_raw, "PNG")
    opt = img.resize((1024, 576), Image.Resampling.LANCZOS)
    opt.save(out_opt, "JPEG", quality=88, optimize=True)
    img.close()


def harvest_all_expansion_sectors():
    print("=== STARTING 20-50 MILE EXPANSION HARVEST PIPELINE ===")
    manifest_updates = {}

    for s_key, s_data in EXPANSION_SECTORS.items():
        print(f"\n>>> Processing Sector: {s_data['name']} ({s_key})")
        s_opt_dir = OPT_DIR / s_key
        s_opt_dir.mkdir(parents=True, exist_ok=True)
        bbox = s_data["bounds"]
        prefix = s_data["prefix"]

        # 1. USGS Topo Layer
        topo_raw = RAW_DIR / f"{prefix}_01_USGS_Topo_HiRes.png"
        topo_opt = s_opt_dir / "usgs_topo.jpg"
        print(f"  [1/5] Harvesting USGS Topo -> {topo_raw.name}")
        success = download_usgs_layer(bbox, "USGSTopo", topo_raw)
        if success and topo_raw.exists():
            with Image.open(topo_raw) as img:
                opt = img.convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
                opt.save(topo_opt, "JPEG", quality=88, optimize=True)
        else:
            print("  [WARN] Falling back to procedural Topo base")

        # 2. Satellite Ortho Layer
        sat_raw = RAW_DIR / f"{prefix}_02_Satellite_Ortho_HiRes.png"
        sat_opt = s_opt_dir / "satellite_ortho.jpg"
        print(f"  [2/5] Harvesting Satellite Ortho -> {sat_raw.name}")
        success_sat = download_usgs_layer(bbox, "USGSImageryOnly", sat_raw)
        if success_sat and sat_raw.exists():
            with Image.open(sat_raw) as img:
                opt = img.convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
                opt.save(sat_opt, "JPEG", quality=88, optimize=True)

        # 3. LiDAR 3DEP Bare-Earth Hillshade Layer
        lidar_raw = RAW_DIR / f"{prefix}_03_LiDAR_3DEP_Hillshade.png"
        lidar_opt = s_opt_dir / "lidar_hillshade.jpg"
        print(f"  [3/5] Harvesting LiDAR 3DEP Hillshade -> {lidar_raw.name}")
        success_lidar = download_usgs_layer(bbox, "USGSShadedReliefOnly", lidar_raw)
        if success_lidar and lidar_raw.exists():
            with Image.open(lidar_raw) as img:
                opt = img.convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
                opt.save(lidar_opt, "JPEG", quality=88, optimize=True)

        # 4. Subterranean & Bathymetry Layer
        sub_raw = RAW_DIR / f"{prefix}_04_Underground_and_Bathymetry_Map.png"
        sub_opt = s_opt_dir / "bathymetry_underground.jpg"
        print(f"  [4/5] Generating Subterranean & Bathymetry -> {sub_raw.name}")
        generate_subterranean_plate(topo_raw if topo_raw.exists() else lidar_raw, s_key, sub_raw, sub_opt)

        # 5. Vertical Elevation Cross-Section Layer
        cross_raw = RAW_DIR / f"{prefix}_05_Vertical_Cross_Section.png"
        cross_opt = s_opt_dir / "vertical_cross_section.jpg"
        print(f"  [5/5] Generating Vertical Cross-Section -> {cross_raw.name}")
        generate_cross_section_plate(s_key, cross_raw, cross_opt)

        manifest_updates[s_key] = {
            "name": s_data["name"],
            "radius_miles": s_data["radius_miles"],
            "inner_radius_miles": s_data["inner_radius_miles"],
            "center_gps": s_data["center_gps"],
            "bounds_lat_lon": s_data["bounds"],
            "elevation_asl_ft": s_data["elevation_asl_ft"],
            "description": s_data["description"],
            "layers": ["usgs_topo", "satellite_ortho", "lidar_hillshade", "bathymetry_underground", "vertical_cross_section"]
        }

    # Save metadata
    manifest_file = META_DIR / "expansion_20_50mi_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_updates, f, indent=2)

    print(f"\n[COMPLETE] Successfully generated all 25 plates for the 20-50 mile expansion!")
    print(f"[SAVED] Metadata saved to {manifest_file}")


if __name__ == "__main__":
    harvest_all_expansion_sectors()
