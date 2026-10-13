"""
Generates the 5 Ultra-High-Zoom Street-Level & Subterranean Close-Up Plates
for the Immediate Primary Core around Washington Borough, NJ (07882) [0-6 Mile Radius]:
  1. Sector0_Washington_Core_01_USGS_Topo_StreetLevel.png
  2. Sector0_Washington_Core_02_Satellite_Ortho_StreetLevel.png
  3. Sector0_Washington_Core_03_LiDAR_3DEP_Hillshade_CloseUp.png
  4. Sector0_Washington_Core_04_Underground_and_Bathymetry_CloseUp.png
  5. Sector0_Washington_Core_05_Vertical_Cross_Section_CloseUp.png
"""

from concurrent.futures import ThreadPoolExecutor
from generate_sao_area_survey_imagery import (
    fetch_wms_image,
    render_sector_map_plate,
    render_vertical_cross_section,
)

WASHINGTON_CORE_CFG = {
    "title": "PRIMARY CORE STREET-LEVEL CLOSE-UP: WASHINGTON BOROUGH, NJ (0-6 MI)",
    "subtitle": "Routes 31 & 57, Port Colden, Van Nest Gap Tunnel, Oxford Mine (-2,700 ft) & Merrill Creek (-225 ft)",
    "bbox": (-75.115, 40.710, -74.895, 40.825),
    "nodes": [
        (-74.9793, 40.7584, "WASHINGTON BOROUGH (NJ-31 & NJ-57)", "hub", "460 ft ASL | Broad St & Belvidere Ave"),
        (-74.9835, 40.7610, "Cornish & Beethoven Organ Works", "sky", "Historic 5-Story Brick Factory Complex"),
        (-74.9760, 40.7555, "Washington Secondary Rail Yard", "hub", "Norfolk Southern / Old DL&W Freight Siding"),
        (-74.9530, 40.7640, "Port Colden Inclined Plane 6", "water", "Subterranean Scotch-Turbine Wheel Pit (50 ft Rise)"),
        (-75.0029, 40.7798, "Van Nest Gap (Oxford) Rail Tunnel", "tunnel", "3,002 ft Brick/Gneiss Bore + Central Air Shaft"),
        (-74.9904, 40.8031, "Oxford Furnace (1741 Stack)", "sky", "Colonial Blast Furnace & Slag Bastion"),
        (-74.9880, 40.7950, "Oxford Washington Mine Shaft", "mine", "-2,700 ft Depth (15 Flooded Levels Magnetite)"),
        (-75.0120, 40.7620, "Brass Castle & Plane 7 West", "water", "Morris Canal Lock & Inclined Plane 7 Ruins"),
        (-74.9960, 40.7420, "Roaring Rock Gorge & Boulder Rapid", "water", "Pohatcong Slope Glacial Erratics & Creek"),
        (-75.0180, 40.7280, "Pohatcong Mountain Ridge Crest", "sky", "900-1,100 ft Pre-Cambrian Gneiss Spine"),
        (-75.0833, 40.7750, "Merrill Creek Reservoir (-225 ft)", "water", "Deepest Water in NJ + 200-ft Submerged Tower"),
        (-75.0950, 40.7610, "Merrill Creek 3.2-Mi Rock Tunnel", "tunnel", "96-Inch Subterranean Bore under Scott's Mtn"),
        (-74.9220, 40.7350, "Changewater & Musconetcong Gorge", "water", "River Viaduct & Limestone Karst Springs"),
        (-74.9580, 40.7080, "Hampton Junction Rail Hub", "hub", "CRRNJ & Lehigh Valley Rail Junction"),
    ],
    "cross_section": {
        "title": "WASHINGTON BOROUGH 6-MILE CORE VERTICAL PROFILE (+1,150 ft to -2,700 ft)",
        "min_elev": -2800,
        "max_elev": 1300,
        "features": [
            ("Scott's Mtn / Montana Ridge", 1150, 450, (239, 68, 68), "1,150 ft ASL Crest"),
            ("Pohatcong Mtn Ridge", 1040, 420, (249, 115, 22), "1,040 ft Gneiss Spine"),
            ("Merrill Creek Upper Rim", 750, 525, (6, 182, 212), "-225 ft Deep Reservoir"),
            ("Cornish Organ Works Towers", 535, 460, (168, 85, 247), "75 ft Brick Factory"),
            ("Washington Borough (31/57)", 460, 420, (16, 185, 129), "460 ft ASL Street Grade"),
            ("Port Colden Turbine Chamber", 455, 405, (59, 130, 246), "50 ft Plane + Stone Vault"),
            ("Van Nest Gap Rail Tunnel", 520, 390, (245, 158, 11), "3,002 ft Bore + 130 ft Shaft"),
            ("Merrill Creek 3.2-Mi Tunnel", 525, 210, (14, 165, 233), "96-in Bore to Delaware"),
            ("Oxford Washington Mine", 480, -2220, (220, 38, 38), "15 Levels (-2,700 ft Depth)"),
        ]
    }
}


def main():
    skey = "Sector0_Washington_Core"
    scfg = WASHINGTON_CORE_CFG
    bbox = scfg["bbox"]
    print(f"=== Generating High-Zoom Street-Level Plates for {skey} ===")
    with ThreadPoolExecutor(max_workers=4) as ex:
        f_topo = ex.submit(fetch_wms_image, "topo", bbox, 1820, 1300)
        f_sat = ex.submit(fetch_wms_image, "satellite", bbox, 1820, 1300)
        f_lidar = ex.submit(fetch_wms_image, "lidar", bbox, 1820, 1300)
        f_hydro = ex.submit(fetch_wms_image, "hydro", bbox, 1820, 1300)

        topo_img = f_topo.result()
        sat_img = f_sat.result()
        lidar_img = f_lidar.result()
        hydro_img = f_hydro.result()

    render_sector_map_plate(skey, scfg, "topo", topo_img)
    render_sector_map_plate(skey, scfg, "satellite", sat_img)
    render_sector_map_plate(skey, scfg, "lidar", lidar_img)
    render_sector_map_plate(skey, scfg, "underground_bathy", lidar_img, hydro_img)
    render_vertical_cross_section(skey, scfg)
    print("[SUCCESS] All 5 High-Zoom Washington Core Street-Level Plates Generated!")


if __name__ == "__main__":
    main()
