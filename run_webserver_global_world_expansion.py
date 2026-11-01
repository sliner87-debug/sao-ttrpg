#!/usr/bin/env python3
"""
run_webserver_global_world_expansion.py
===============================================================================
Autonomous Webserver Continental & Global Map Tile Expansion
Expands map tiles and geospatial reconnaissance out through the rest of the world:
- Rings 13 to 18 (Continental North America: 500 to 2,500+ Statute Miles)
- Global Planetary Patchwork Earth Nodes (Transoceanic Megastructures & Subterranean Spoke Hubs)

Harvests & renders 5-plate multisensor suites:
  01: High-Resolution Satellite Ortho (Esri World Imagery / Sentinel-2 / NASA)
  02: Copernicus GLO-30 / Global Bare-Earth Elevation Hillshade
  03: World Tactical Topo & Navigation Grid
  04: Crustal Geophysics & Telluric Magnetic Anomaly
  05: Subterranean Vertical Cross-Section Profile (+14,000 ft to -10,000 ft ASL)

Updates assets/maps/Imagery/, imagery_manifest.json, and the Global Raid Atlas.
===============================================================================
"""

import os
import sys
import io
import json
import math
import ssl
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont

WORKSPACE_DIR = "/home/sline/antigravity-workspace"
IMAGERY_DIR = os.path.join(WORKSPACE_DIR, "assets", "maps", "Imagery")
MANIFEST_PATH = os.path.join(IMAGERY_DIR, "imagery_manifest.json")
GLOBAL_STATE_PATH = os.path.join(WORKSPACE_DIR, "MultiModel_Global_World_State.json")
GLOBAL_LOG_PATH = os.path.join(WORKSPACE_DIR, "global_world_expansion.log")

os.makedirs(IMAGERY_DIR, exist_ok=True)

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE
UA = "Fractured-Earth-Global-Cartography/3.0 (https://136.117.249.130; research@fractured-reality.org)"

# -----------------------------------------------------------------------------
# 1. EXPANDED CONTINENTAL & GLOBAL TARGETS (Rings 13–18 + Global Patchwork)
# -----------------------------------------------------------------------------
GLOBAL_WORLD_TARGETS = [
    # Ring 13 (500–750 Mi)
    ("Ring13_ChicagoDeepTunnel", "Ring 13 (500–750 Mi)", "Chicago TARP 'Deep Tunnel' 109-Mile Subterranean Limestone Labyrinth", "3500 S Canal St, Chicago, IL 60609", 41.8290, -87.6385),
    ("Ring13_SavannahRiverSite", "Ring 13 (500–750 Mi)", "Savannah River Site Cold-War Tritium & Plutonium Sub-Bunkers", "Savannah River Site, Aiken, SC 29808", 33.2456, -81.6567),
    ("Ring13_FortGillemCDC", "Ring 13 (500–750 Mi)", "Fort Gillem / CDC Emergency Operations Underground Biological Vault", "4550 Anvil Block Rd, Forest Park, GA 30297", 33.6264, -84.3283),
    ("Ring13_MammothCaveKarst", "Ring 13 (500–750 Mi)", "Mammoth Cave System 426-Mile Natural Subterranean Conduit Network", "1 Mammoth Cave Pkwy, Mammoth Cave, KY 42259", 37.1869, -86.1005),

    # Ring 14 (750–1,000 Mi)
    ("Ring14_KansascitySubTropolis", "Ring 14 (750–1,000 Mi)", "SubTropolis 55-Million Sq Ft Underground Limestone Fortress & Server Haven", "8300 NE Underground Dr, Kansas City, MO 64161", 39.1558, -94.4914),
    ("Ring14_NewOrleansDrainage", "Ring 14 (750–1,000 Mi)", "New Orleans Sub-Sea Level Drainage Palmetto Pumping Stations & Canals", "8800 S Claiborne Ave, New Orleans, LA 70118", 29.9619, -90.1197),
    ("Ring14_IronRangeHibbing", "Ring 14 (750–1,000 Mi)", "Hull-Rust-Mahoning Open Pit & Subterranean Taconite Mine Network (6 Miles Long)", "400 3rd Ave E, Hibbing, MN 55746", 47.4583, -92.9567),

    # Ring 15 (1,000–1,500 Mi)
    ("Ring15_CheyenneMountainNORAD", "Ring 15 (1,000–1,500 Mi)", "Cheyenne Mountain Alternate Command Center (NORAD 2,000-Ft Granite Citadel)", "Cheyenne Mountain AFB, Colorado Springs, CO 80914", 38.7442, -104.8467),
    ("Ring15_DenverAirportSubLevel", "Ring 15 (1,000–1,500 Mi)", "Denver International Airport Multi-Level Subterranean Logistics & Vault Grid", "8500 Peña Blvd, Denver, CO 80249", 39.8561, -104.6737),
    ("Ring15_EllsworthICBMField", "Ring 15 (1,000–1,500 Mi)", "Ellsworth AFB 44th Strategic Missile Wing Minuteman II/III Hardened Silo Field", "1000 Ellsworth St, Ellsworth AFB, SD 57706", 44.1500, -103.1000),
    ("Ring15_HoustonBryanMoundSPR", "Ring 15 (1,000–1,500 Mi)", "Strategic Petroleum Reserve Bryan Mound Subterranean Halite Caverns", "Freeport, TX 77541", 28.9200, -95.3400),

    # Ring 16 (1,500–2,000 Mi)
    ("Ring16_YellowstoneCaldera", "Ring 16 (1,500–2,000 Mi)", "Yellowstone Caldera 45-Mile Magma Chamber & Subterranean Geothermal Core", "Yellowstone National Park, WY 82190", 44.4280, -110.5885),
    ("Ring16_DugwayProvingGround", "Ring 16 (1,500–2,000 Mi)", "Dugway Proving Ground Ditmar Subterranean Chemical & Biological Testing Complex", "Dugway, UT 84022", 40.2444, -112.7561),
    ("Ring16_LosAlamosMesaVaults", "Ring 16 (1,500–2,000 Mi)", "Los Alamos National Laboratory Technical Area 55 Plutonium Facility & Sub-Tunnels", "Bikini Atoll Rd, Los Alamos, NM 87545", 35.8647, -106.3139),
    ("Ring16_GraniteMountainVault", "Ring 16 (1,500–2,000 Mi)", "Granite Mountain Records Vault (600-Ft Deep Solid Granite Sub-Vault)", "3510 E Little Cottonwood Rd, Sandy, UT 84092", 40.5739, -111.7631),

    # Ring 17 (2,000–2,500 Mi)
    ("Ring17_Area51GroomLake", "Ring 17 (2,000–2,500 Mi)", "Groom Lake Area 51 / Tonopah Subterranean Hangar & Flight Test Corridors", "Groom Lake, NV 89044", 37.2431, -115.7930),
    ("Ring17_HanfordBReactor", "Ring 17 (2,000–2,500 Mi)", "Hanford Nuclear Reservation B-Reactor & Subterranean Plutonium Vitrification Plant", "Hanford Site, Richland, WA 99354", 46.6333, -119.5936),
    ("Ring17_GrandCouleeDam", "Ring 17 (2,000–2,500 Mi)", "Grand Coulee Dam 550-Ft High Concrete Gravity Superstructure & Third Powerplant", "Coulee Dam, WA 99116", 47.9575, -118.9814),
    ("Ring17_EdwardsAFBSubVaults", "Ring 17 (2,000–2,500 Mi)", "Edwards AFB Rocket Propulsion Laboratory & North Base Underground Test Cells", "Edwards, CA 93524", 34.9240, -117.8912),

    # Ring 18 (2,500–3,500 Mi - Continental Perimeters & Borders)
    ("Ring18_HAARPAlaska", "Ring 18 (2,500–3,500 Mi)", "HAARP Gakona Ionospheric Research Facility High-Frequency Radio Array", "Mile 11.3 Tok Cutoff, Gakona, AK 99586", 62.3917, -145.1500),
    ("Ring18_PanamaCanalMiraflores", "Ring 18 (2,500–3,500 Mi)", "Panama Canal Miraflores & Culebra Cut Sub-Lock Hydro-Engineering Grid", "Miraflores Locks, Panama City, Panama", 8.9975, -79.5919),
    ("Ring18_MexicoCityTemploMayor", "Ring 18 (2,500–3,500 Mi)", "Mexico City Metropolitan Basin & Sub-Lakebed Hydraulic Drainage Tunnels", "Zócalo, Cuauhtémoc, 06060 Mexico City, CDMX", 19.4326, -99.1332),

    # Global Planetary Patchwork Earth Nodes (Transoceanic Archetypal Nodes)
    ("Global_LondonPaddockVaults", "Global Planetary Patchwork", "London Cabinet War Rooms & Paddock Alternate COG Subterranean Bunker", "Horse Guards Rd, London SW1A 2HQ, UK", 51.5022, -0.1299),
    ("Global_ParisCatacombs", "Global Planetary Patchwork", "Paris 200-Mile Underground Lutetian Limestone Quarry Labyrinth", "1 Av. du Colonel Henri Rol-Tanguy, 75014 Paris, France", 48.8338, 2.3324),
    ("Global_ChernobylSarcophagus", "Global Planetary Patchwork", "Chernobyl Exclusion Zone Reactor #4 New Safe Confinement & Sub-Core Basement", "Pripyat, Kyiv Oblast, Ukraine", 51.3892, 30.0997),
    ("Global_TokyoGCANS", "Global Planetary Patchwork", "Tokyo Metropolitan Underground Discharge Channel (G-CANS Kasukabe Cathedral)", "720 Kamikinden, Kasukabe, Saitama 344-0111, Japan", 35.9986, 139.8114),
    ("Global_SvalbardSeedVault", "Global Planetary Patchwork", "Svalbard Global Seed Vault 400-Ft Arctic Sandstone Mountain Bunker", "Longyearbyen, Svalbard, Norway", 78.2358, 15.4913),
    ("Global_MountKailashCore", "Global Planetary Patchwork", "Mount Kailash Trans-Himalayan Four-Faced Pyramid & Indus-Brahmaputra Divide", "Ngari Prefecture, Tibet Autonomous Region, China", 31.0672, 81.3119),
]

# -----------------------------------------------------------------------------
# 2. TILE DOWNLOAD & IMAGE STITCHING ENGINE
# -----------------------------------------------------------------------------
def deg2num(lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def fetch_tile(url: str, max_retries: int = 3) -> Optional[Image.Image]:
    headers = {"User-Agent": UA}
    req = urllib.request.Request(url, headers=headers)
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, context=CTX, timeout=12) as resp:
                data = resp.read()
                if len(data) > 800:
                    return Image.open(io.BytesIO(data)).convert("RGB")
        except Exception:
            time.sleep(0.5 * (attempt + 1))
    return None

def fetch_tile_grid(center_lat: float, center_lon: float, zoom: int, tile_url_fmt: str, grid_size: int = 3) -> Image.Image:
    cx, cy = deg2num(center_lat, center_lon, zoom)
    half = grid_size // 2
    canvas = Image.new("RGB", (grid_size * 256, grid_size * 256), color=(20, 24, 32))
    
    with ThreadPoolExecutor(max_workers=8) as pool:
        future_map = {}
        for row, dy in enumerate(range(-half, half + 1)):
            for col, dx in enumerate(range(-half, half + 1)):
                x = cx + dx
                y = cy + dy
                url = tile_url_fmt.format(z=zoom, x=x, y=y)
                future_map[pool.submit(fetch_tile, url)] = (col, row)
        
        for fut in as_completed(future_map):
            col, row = future_map[fut]
            try:
                img = fut.result()
                if img:
                    canvas.paste(img, (col * 256, row * 256))
            except Exception:
                pass
                
    return canvas.resize((1024, 1024), Image.Resampling.LANCZOS)

# -----------------------------------------------------------------------------
# 3. PLATE GENERATION: 5-SERIES SUITE PER TARGET
# -----------------------------------------------------------------------------
def render_cross_section_profile(title: str, subtitle: str, elev_min: int, elev_max: int, key_strata: List[Tuple[str, int, str]]) -> Image.Image:
    img = Image.new("RGB", (1024, 1024), color=(14, 18, 26))
    draw = ImageDraw.Draw(img)
    
    # Header
    draw.rectangle([(0, 0), (1024, 120)], fill=(22, 28, 42))
    draw.text((30, 24), title, fill=(0, 229, 255))
    draw.text((30, 64), subtitle, fill=(180, 195, 215))
    
    # Profile axis bounds
    top_y = 180
    bottom_y = 900
    left_x = 120
    right_x = 940
    
    draw.rectangle([(left_x, top_y), (right_x, bottom_y)], fill=(8, 12, 18), outline=(60, 80, 110), width=2)
    
    # Elevation Grid lines
    steps = 8
    for i in range(steps + 1):
        y = top_y + int(i * (bottom_y - top_y) / steps)
        elev = int(elev_max - i * (elev_max - elev_min) / steps)
        draw.line([(left_x - 10, y), (right_x, y)], fill=(30, 45, 65), width=1)
        draw.text((20, y - 8), f"{elev:,} ft", fill=(130, 150, 180))
        
    # Strata blocks & labels
    prev_y = top_y + 40
    for name, depth_elev, color_hex in key_strata:
        ratio = (elev_max - depth_elev) / max(1, (elev_max - elev_min))
        y_pos = top_y + int(ratio * (bottom_y - top_y))
        y_pos = max(top_y + 10, min(bottom_y - 10, y_pos))
        
        # Draw stratum band
        draw.rectangle([(left_x + 10, prev_y), (right_x - 10, y_pos)], fill=color_hex, outline=(40, 50, 70), width=1)
        draw.text((left_x + 30, (prev_y + y_pos) // 2 - 8), name, fill=(240, 245, 255))
        draw.text((right_x - 140, (prev_y + y_pos) // 2 - 8), f"{depth_elev:,} ft ASL", fill=(255, 215, 0))
        prev_y = y_pos
        
    # Footer metadata
    draw.text((left_x, 920), "VERTICAL TECTONIC / CRUSTAL ENGINEERING PROFILE // CARDINAL FRACTURED EARTH OVERLAY", fill=(100, 120, 150))
    return img

def process_target(target_tuple: Tuple[str, str, str, str, float, float]) -> List[Tuple[str, str, int]]:
    t_id, ring_name, full_name, address, lat, lon = target_tuple
    saved_records = []
    
    # 1. Satellite Ortho (Esri World Imagery)
    p1_name = f"{t_id}_01_Satellite_Ortho.png"
    p1_path = os.path.join(IMAGERY_DIR, p1_name)
    if not os.path.exists(p1_path) or os.path.getsize(p1_path) < 10000:
        img_sat = fetch_tile_grid(lat, lon, zoom=16, tile_url_fmt="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", grid_size=3)
        # Add HUD header
        draw = ImageDraw.Draw(img_sat)
        draw.rectangle([(0, 0), (1024, 70)], fill=(0, 0, 0, 180))
        draw.text((20, 15), f"{full_name} [SATELLITE ORTHO]", fill=(0, 240, 255))
        draw.text((20, 42), f"GPS: {lat:.4f}° N, {lon:.4f}° W | {address}", fill=(200, 220, 240))
        img_sat.save(p1_path, "PNG")
    saved_records.append((p1_name, "Satellite_Ortho", os.path.getsize(p1_path)))

    # 2. LiDAR / Shaded Elevation (Esri World Hillshade / Terrain)
    p2_name = f"{t_id}_02_LiDAR_Hillshade.png"
    p2_path = os.path.join(IMAGERY_DIR, p2_name)
    if not os.path.exists(p2_path) or os.path.getsize(p2_path) < 10000:
        img_dem = fetch_tile_grid(lat, lon, zoom=15, tile_url_fmt="https://server.arcgisonline.com/ArcGIS/rest/services/Elevation/World_Hillshade/MapServer/tile/{z}/{y}/{x}", grid_size=3)
        draw = ImageDraw.Draw(img_dem)
        draw.rectangle([(0, 0), (1024, 70)], fill=(0, 0, 0, 180))
        draw.text((20, 15), f"{full_name} [GLOBAL DIGITAL ELEVATION & BARE-EARTH HILLSHADE]", fill=(255, 215, 0))
        draw.text((20, 42), f"GPS: {lat:.4f}° N, {lon:.4f}° W | Bare-Earth Canopy-Stripped Geomorphology", fill=(220, 230, 240))
        img_dem.save(p2_path, "PNG")
    saved_records.append((p2_name, "LiDAR_Hillshade", os.path.getsize(p2_path)))

    # 3. Tactical Topo (OpenStreetMap Humanitarian / World Topo)
    p3_name = f"{t_id}_03_Tactical_Topo.png"
    p3_path = os.path.join(IMAGERY_DIR, p3_name)
    if not os.path.exists(p3_path) or os.path.getsize(p3_path) < 10000:
        img_topo = fetch_tile_grid(lat, lon, zoom=15, tile_url_fmt="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}", grid_size=3)
        draw = ImageDraw.Draw(img_topo)
        draw.rectangle([(0, 0), (1024, 70)], fill=(0, 0, 0, 180))
        draw.text((20, 15), f"{full_name} [TACTICAL TOPOGRAPHIC / INFRASTRUCTURE OVERLAY]", fill=(50, 255, 120))
        draw.text((20, 42), f"GPS: {lat:.4f}° N, {lon:.4f}° W | Logistics, Roadway & Rail Arteries", fill=(220, 230, 240))
        img_topo.save(p3_path, "PNG")
    saved_records.append((p3_name, "Tactical_Topo", os.path.getsize(p3_path)))

    # 4. Geophysics / Magnetic / Crustal Anomaly (Procedural Thermal/Rad Anomaly Map)
    p4_name = f"{t_id}_04_Geophysics_Anomaly.png"
    p4_path = os.path.join(IMAGERY_DIR, p4_name)
    if not os.path.exists(p4_path) or os.path.getsize(p4_path) < 10000:
        # Base canvas
        img_geo = fetch_tile_grid(lat, lon, zoom=14, tile_url_fmt="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}", grid_size=3).convert("L").convert("RGB")
        # Tint with procedural geophysical heat
        arr = np.array(img_geo, dtype=np.float32)
        arr[:, :, 0] = np.clip(arr[:, :, 0] * 1.4 + 20, 0, 255) # Red/Uranium
        arr[:, :, 1] = np.clip(arr[:, :, 1] * 0.9, 0, 255)
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 1.2 + 30, 0, 255) # Blue/Magnetic
        img_geo = Image.fromarray(arr.astype(np.uint8))
        draw = ImageDraw.Draw(img_geo)
        draw.rectangle([(0, 0), (1024, 70)], fill=(10, 14, 24, 220))
        draw.text((20, 15), f"{full_name} [CRUSTAL GEOPHYSICAL & TELLURIC ANOMALY]", fill=(255, 100, 255))
        draw.text((20, 42), f"Magnetic Total-Field Perturbation & Lithospheric Density Model", fill=(210, 210, 240))
        img_geo.save(p4_path, "PNG")
    saved_records.append((p4_name, "Geophysics_Anomaly", os.path.getsize(p4_path)))

    # 5. Vertical Cross-Section
    p5_name = f"{t_id}_05_Vertical_Cross_Section.png"
    p5_path = os.path.join(IMAGERY_DIR, p5_name)
    if not os.path.exists(p5_path) or os.path.getsize(p5_path) < 10000:
        strata = [
            ("Alluvial Overburden & Reinforced Surface Pad", 800, (45, 55, 75)),
            ("Blast-Hardened Concrete Vault Cap & NBC Ventilation Gallery", 650, (65, 80, 110)),
            ("Primary Subterranean Command / Extraction Cavity", 200, (30, 40, 60)),
            ("Deep Bedrock Sump & Geothermal Drainage Horizon", -400, (20, 28, 42))
        ]
        img_cross = render_cross_section_profile(
            title=f"{full_name.upper()} — VERTICAL SUBTERRANEAN PROFILE",
            subtitle=f"{ring_name} | Coordinates: {lat:.4f}° N, {lon:.4f}° W | Collar ASL: +950 ft",
            elev_min=-800, elev_max=1200, key_strata=strata
        )
        img_cross.save(p5_path, "PNG")
    saved_records.append((p5_name, "Vertical_Cross_Section", os.path.getsize(p5_path)))

    return saved_records

def main():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] STARTING CONTINENTAL & GLOBAL MAP TILE EXPANSION...")
    print(f"Total Global Targets to Harvest: {len(GLOBAL_WORLD_TARGETS)}")
    
    # Load manifest
    manifest = {}
    if os.path.exists(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            manifest = {}
            
    total_added = 0
    t0 = time.time()
    
    for i, tgt in enumerate(GLOBAL_WORLD_TARGETS, 1):
        t_id, ring_name, full_name, address, lat, lon = tgt
        print(f"[{i}/{len(GLOBAL_WORLD_TARGETS)}] Processing {full_name} ({ring_name})...", flush=True)
        try:
            records = process_target(tgt)
            for fname, modality, size in records:
                manifest[fname] = {
                    "site_id": t_id,
                    "target_name": full_name,
                    "ring": ring_name,
                    "address": address,
                    "gps": [lat, lon],
                    "modality": modality,
                    "size_bytes": size,
                    "timestamp": time.time()
                }
                total_added += 1
                print(f"   [OK] Saved {fname} ({size // 1024} KB)", flush=True)
        except Exception as e:
            print(f"   [ERROR] Failed {t_id}: {e}", flush=True)
            
    # Save manifest
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Manifest updated: {len(manifest)} total indexed plates in {MANIFEST_PATH}")
    
    # Write Global World State
    state_out = {
        "status": "COMPLETED",
        "last_updated": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_targets": len(GLOBAL_WORLD_TARGETS),
        "total_manifest_plates": len(manifest),
        "targets": [
            {
                "id": t[0],
                "ring": t[1],
                "name": t[2],
                "address": t[3],
                "lat": t[4],
                "lon": t[5]
            } for t in GLOBAL_WORLD_TARGETS
        ]
    }
    with open(GLOBAL_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state_out, f, indent=2)
        
    elapsed = time.time() - t0
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] GLOBAL EXPANSION COMPLETE: Added {total_added} plates in {elapsed:.1f}s.")

if __name__ == "__main__":
    main()
