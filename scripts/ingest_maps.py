"""
scripts/ingest_maps.py
Automated ingestion, validation, and web-optimization pipeline for the 44 USGS,
LiDAR 3DEP, Satellite Ortho, Bathymetry, and Vertical Cross-Section map assets
originating from Google Drive (E:\My Drive\SAO Area Survery) and NotebookLM.
"""

import os
import shutil
import json
from pathlib import Path
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_IMAGERY_DIR = Path(r"E:\My Drive\SAO Area Survery\Imagery")
FALLBACK_SOURCE_DIR = Path(r"E:\My Drive\SAO\Imagery")

TARGET_RAW_DIR = REPO_ROOT / "assets" / "maps" / "raw"
TARGET_OPT_DIR = REPO_ROOT / "assets" / "maps" / "optimized"
TARGET_META_DIR = REPO_ROOT / "assets" / "maps" / "metadata"

SECTOR_CONFIG = {
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
        "description": "5-mile high-resolution municipal grid around Washington Borough safe-zone."
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
        "description": "25-mile regional corridor covering Warren, Hunterdon, Morris, Sussex, and Northampton."
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
        "name": "20–50 Mile Annular Master Ring (All Quadrants)",
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
    }
}

LAYER_TYPES = {
    "usgs_topo": "01_USGS_Topo_HiRes.png",
    "satellite_ortho": "02_Satellite_Ortho_HiRes.png",
    "lidar_hillshade": "03_LiDAR_3DEP_Hillshade.png",
    "bathymetry_underground": "04_Underground_and_Bathymetry_Map.png",
    "vertical_cross_section": "05_Vertical_Cross_Section.png"
}

MASTER_LAYER_TYPES = {
    "usgs_topo": "01_USGS_Topo_Overview.png",
    "lidar_hillshade": "02_LiDAR_3DEP_Shaded_Relief_Overview.png",
    "satellite_ortho": "03_Satellite_Hybrid_Overview.png"
}

def resolve_source_file(filename: str) -> Path | None:
    for d in [SOURCE_IMAGERY_DIR, FALLBACK_SOURCE_DIR]:
        candidate = d / filename
        if candidate.exists():
            return candidate
    return None

def ingest_maps(optimize_size: int = 1024):
    print("=== Starting SAO V2 Map Ingestion Pipeline ===")
    TARGET_RAW_DIR.mkdir(parents=True, exist_ok=True)
    TARGET_OPT_DIR.mkdir(parents=True, exist_ok=True)
    TARGET_META_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {"sectors": {}, "total_plates": 0, "layers": list(LAYER_TYPES.keys())}
    ingested_count = 0

    for s_key, s_data in SECTOR_CONFIG.items():
        s_opt_dir = TARGET_OPT_DIR / s_key
        s_opt_dir.mkdir(parents=True, exist_ok=True)
        manifest["sectors"][s_key] = dict(s_data)
        manifest["sectors"][s_key]["layers"] = {}

        is_master = (s_key == "master_100mi")
        layer_defs = MASTER_LAYER_TYPES if is_master else LAYER_TYPES

        for l_key, suffix in layer_defs.items():
            filename = f"{s_data['prefix']}_{suffix}"
            src_file = resolve_source_file(filename)
            raw_target = TARGET_RAW_DIR / filename
            opt_target = s_opt_dir / f"{l_key}.jpg"

            if src_file and src_file.exists():
                print(f"[COPY] {filename} -> raw/")
                if not raw_target.exists() or raw_target.stat().st_size != src_file.stat().st_size:
                    shutil.copy2(src_file, raw_target)
                
                # Create web-optimized version for instant Streamlit rendering
                print(f"[OPTIMIZE] Generating {opt_target.name} ({optimize_size}x{optimize_size})...")
                try:
                    with Image.open(raw_target) as img:
                        orig_w, orig_h = img.size
                        # Convert RGBA to RGB for JPEG optimization if needed
                        if img.mode in ("RGBA", "P"):
                            rgb_img = Image.new("RGB", img.size, (15, 23, 42))
                            if img.mode == "RGBA":
                                rgb_img.paste(img, mask=img.split()[3])
                            else:
                                rgb_img.paste(img.convert("RGBA"))
                        else:
                            rgb_img = img.convert("RGB")
                        
                        # Resize maintaining aspect ratio or square fit
                        opt_img = rgb_img.resize((optimize_size, optimize_size), Image.Resampling.LANCZOS)
                        opt_img.save(opt_target, "JPEG", quality=88, optimize=True)
                        opt_img.close()
                        rgb_img.close()

                    manifest["sectors"][s_key]["layers"][l_key] = {
                        "raw_file": str(raw_target.relative_to(REPO_ROOT)),
                        "opt_file": str(opt_target.relative_to(REPO_ROOT)),
                        "original_size": [orig_w, orig_h],
                        "optimized_size": [optimize_size, optimize_size],
                        "status": "ready"
                    }
                    ingested_count += 1
                except Exception as e:
                    print(f"Error optimizing {filename}: {e}")
            else:
                print(f"[WARNING] Source file not found: {filename}")
                manifest["sectors"][s_key]["layers"][l_key] = {
                    "raw_file": None,
                    "opt_file": None,
                    "status": "missing"
                }

    manifest["total_plates"] = ingested_count
    manifest_path = TARGET_META_DIR / "sector_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"\n[SUCCESS] Ingested & Optimized {ingested_count} map plates.")
    print(f"[SAVED] Manifest at {manifest_path}")
    return manifest

if __name__ == "__main__":
    ingest_maps()
