"""
Generates the High-Resolution GIS Imagery Suite (USGS Topo, Satellite Orthoimagery,
USGS 3DEP LiDAR Hillshade, Subterranean/Bathymetric Overlays, and 4-Layer Vertical
Engineering Cross-Sections) for the 100-Mile Pre-Initialization Survey around
Washington Borough, NJ (07882), starting with Sector 1 (Primary 0-25 Mi) and
covering Sectors 2, 3, and 4.

Uses pure PIL (Pillow) + NumPy + urllib.request for ultra-fast, high-resolution
2200x1750 cartographic plate rendering.

Outputs directly to:
  1. E:\\My Drive\\SAO Area Survery\\Imagery\\
  2. C:\\Users\\sline\\.gemini\\antigravity\\brain\\82c75b20-5567-4dc2-aaab-bc20f20510ad\\
"""

import os
import io
import json
import math
import shutil
import urllib.request
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image, ImageDraw, ImageFont

DRIVE_ROOT = r"E:\My Drive\SAO Area Survery"
DRIVE_IMG_DIR = os.path.join(DRIVE_ROOT, "Imagery")
ARTIFACT_DIR = r"C:\Users\sline\.gemini\antigravity\brain\82c75b20-5567-4dc2-aaab-bc20f20510ad"

os.makedirs(DRIVE_IMG_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

ORIGIN_LAT = 40.7584
ORIGIN_LON = -74.9793


def get_font(size=16, bold=False):
    candidates = (
        ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/consolab.ttf"]
        if bold else
        ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/consola.ttf"]
    )
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


SECTORS = {
    "Sector1_Primary": {
        "title": "SECTOR 1 (PRIMARY CORE): WASHINGTON, NJ 0-25 MILE RADIUS",
        "subtitle": "Skylands, Kittatinny Ridge, Musconetcong/Raritan Valleys & Lehigh Confluence",
        "bbox": (-75.46, 40.42, -74.48, 41.12),
        "nodes": [
            (-74.9793, 40.7584, "WASHINGTON BOROUGH (ORIGIN)", "hub", "Elev 460 ft | Routes 31 & 57"),
            (-75.0029, 40.7798, "Van Nest Gap Tunnel", "tunnel", "3,002 ft DL&W Bore | Oxford Mtn"),
            (-74.9904, 40.8031, "Oxford Furnace & Washington Mine", "mine", "-2,700 ft (15 Levels) Magnetite"),
            (-75.0833, 40.7750, "Merrill Creek Reservoir", "water", "225 ft Deep (Deepest in NJ) + 3.2-mi Tunnel"),
            (-74.8350, 40.6130, "Round Valley Reservoir", "water", "180 ft Deep | Submerged McPherson Village"),
            (-74.9180, 40.6620, "Spruce Run Reservoir", "water", "73 ft Deep | Submerged Union Forge"),
            (-75.0260, 40.6580, "Musconetcong (Pattenburg) Tunnel", "tunnel", "4,893 ft LVRR Mountain Bore"),
            (-75.0750, 40.8580, "Manunka Chunk Twin Tunnels", "tunnel", "938 ft Twin Bores (1856/1869)"),
            (-74.7180, 40.9670, "Roseville Tunnel (Cut-Off)", "tunnel", "1,024 ft Deep Diabase/Gneiss Cut"),
            (-75.0840, 40.9460, "Paulinskill Viaduct", "sky", "1,100 ft Long x 115 ft High Concrete Arches"),
            (-75.0120, 41.0020, "Yards Creek Pumped-Storage", "sky", "700 ft Elev Drop | 453 MW Hydro Siphon"),
            (-75.1260, 40.9690, "Delaware Water Gap & Sunfish Pond", "water", "1,527 ft Mt Tammany | 1,379 ft Glacial Tarn"),
            (-74.9250, 40.9110, "Jenny Jump Observatory & Ghost Lake", "sky", "1,100 ft UACNJ Domes | Shades of Death Rd"),
            (-74.6650, 40.9350, "Lake Hopatcong", "water", "58 ft Deep | Submerged Morris Canal & Steamboats"),
            (-74.6850, 40.8920, "AT&T Long Lines Netcong Vault", "bunker", "2-Level Subterranean EMP/Nuclear Bunker"),
            (-74.6950, 40.7850, "AT&T Long Lines Chester Node", "bunker", "Hardened Cold War Coaxial Relay"),
            (-74.5650, 40.9550, "Picatinny Arsenal & Tower", "sky", "6,500 Acres | 600 Bunkers | 200-ft Tower"),
            (-74.5420, 40.9320, "Mount Hope (New Leonard Shaft)", "mine", "-2,694 ft Deepest Iron Shaft in East US"),
            (-74.5050, 40.9650, "Hibernia Mine & 1.5-Mi Tunnel", "mine", "-1,600 ft Stopes | 30,000 Bats"),
            (-74.6050, 41.0820, "Sterling Hill Zinc Mine", "mine", "-2,675 ft Depth | 35 Mi UV Fluorescent Tunnels"),
            (-75.1900, 40.6910, "Easton / Phillipsburg Confluence", "hub", "Delaware & Lehigh Rivers | 5 Bridges"),
            (-75.3670, 40.6140, "Bethlehem Steel Furnaces A-E", "sky", "240 ft Tall Blast Furnaces | Lehigh River"),
            (-75.3950, 40.5580, "Friedensville (Ueberroth) Mine", "mine", "-1,260 ft Flooded Karst Shafts"),
            (-75.1280, 40.5610, "Ringing Rocks Boulder Field", "sky", "Resonant Diabase Olivine Boulders"),
        ],
        "cross_section": {
            "title": "SECTOR 1 VERTICAL ENGINEERING PROFILE: KITTATINNY RIDGE TO MOUNT HOPE SHAFT (+1,603 ft to -2,700 ft)",
            "min_elev": -2900,
            "max_elev": 1800,
            "features": [
                ("Mt. Tammany / Catfish Tower", 1603, 0, (239, 68, 68), "1,527-1,603 ft ASL"),
                ("Yards Creek Upper Reservoir", 1450, 750, (59, 130, 246), "700 ft Penstock Drop"),
                ("Jenny Jump UACNJ Domes", 1100, 400, (168, 85, 247), "1,100 ft ASL"),
                ("Bethlehem Steel Furnaces", 601, 361, (249, 115, 22), "240 ft Tall Furnaces"),
                ("Paulinskill Viaduct (115 ft)", 515, 400, (234, 179, 8), "1,100 ft Concrete Arch"),
                ("Washington Borough Grade", 460, 400, (16, 185, 129), "460 ft ASL (Routes 31/57)"),
                ("Van Nest Gap & Pattenburg Bores", 420, 320, (245, 158, 11), "3,002 ft & 4,893 ft Tunnels"),
                ("AT&T Netcong Nuclear Bunker", 820, 720, (236, 72, 153), "2-Level EMP/Blast Vault"),
                ("Merrill Creek Reservoir", 750, 525, (6, 182, 212), "-225 ft Max Depth + Tunnel"),
                ("Round Valley Reservoir", 385, 205, (14, 165, 233), "-180 ft | McPherson Ruins"),
                ("Oxford Washington Iron Mine", 480, -2220, (220, 38, 38), "15 Levels (-2,700 ft Depth)"),
                ("Sterling Hill Zinc Mine", 600, -2075, (34, 197, 94), "35 Mi Tunnels (-2,675 ft)"),
                ("Mount Hope New Leonard Shaft", 800, -1894, (185, 28, 28), "2,694 ft Vertical Shaft"),
            ]
        }
    },
    "Sector2_WestNW": {
        "title": "SECTOR 2 (WEST & NW 25-100 MI): POCONOS, LEHIGH GORGE & PA ANTHRACITE BELT",
        "subtitle": "Allentown, Jim Thorpe, Scranton, Wilkes-Barre, Centralia & Susquehanna Valley",
        "bbox": (-76.85, 40.25, -74.65, 41.70),
        "nodes": [
            (-75.4710, 40.6010, "Allentown & PPL Building (322 ft)", "sky", "24 Stories + NS 46-Track Hump Yard"),
            (-75.9060, 40.3360, "Reading Pagoda (Mt. Penn)", "sky", "886 ft Cliffside Tower (620 ft Drop)"),
            (-75.6050, 40.7750, "Lehigh Tunnel (I-476 Twin Bores)", "tunnel", "4,380 ft NATM Bores through Blue Mtn"),
            (-75.7320, 40.8760, "Jim Thorpe & Mt. Pisgah Plane", "hub", "1,360 ft Switchback + Lehigh Gorge"),
            (-75.6380, 40.8480, "Beltzville Lake (-127 ft)", "water", "127 ft Deep | Submerged Pohopoco Village"),
            (-75.7630, 40.8850, "Lausanne Mine Drainage Tunnel", "tunnel", "7.5-Mile Subterranean Drainage River"),
            (-75.8680, 40.8480, "Nesquehoning Tunnel & No. 9 Mine", "mine", "3,800 ft Rail Bore Piercing Mammoth Vein"),
            (-75.7560, 40.9720, "Rockport Tunnel & High Locks", "tunnel", "1,196 ft Bore + Submerged 1838 Locks"),
            (-76.0090, 40.9990, "JEDDO MINE DRAINAGE TUNNEL", "tunnel", "7.8-Mile Underground River (40M Gal/Day!)"),
            (-75.9740, 40.9580, "Hazleton (1,690 ft) & Audenried", "hub", "Highest City in PA over Deep Coal Basins"),
            (-76.1290, 40.8020, "Mahanoy Tunnel (3,558 ft)", "tunnel", "1862 Bore + Steam Fan Ruins"),
            (-76.3400, 40.8040, "CENTRALIA MINE FIRE (-300 ft)", "mine", "1,000 F Burning Mammoth Vein Since 1962"),
            (-76.3740, 40.7710, "Locust Summit Breaker & Pioneer", "sky", "158-ft 11-Story Breaker + 1,800-ft Adit"),
            (-75.4410, 40.3560, "AT&T Finland Nuclear Bunker", "bunker", "2-Story Subterranean L-4/L-5 Blast Bunker"),
            (-76.9400, 40.6410, "AT&T Dalmatia Hardened Bunker", "bunker", "Autovon Subterranean Coaxial Vault"),
            (-75.4320, 41.1930, "Tobyhanna Army Depot (1,400 Acres)", "sky", "DoD C4ISR Radar & Satcom Citadel (2,130 ft)"),
            (-75.1850, 41.4600, "Lake Wallenpaupack (-60 ft)", "water", "5,700 Acres | Submerged Town of Wilsonville"),
            (-75.8820, 41.2460, "Wilkes-Barre & Huber Breaker Site", "hub", "Luzerne Bank Tower + Susquehanna Levees"),
            (-75.8230, 41.3080, "KNOX MINE DISASTER BREACH (1959)", "water", "Susquehanna Whirlpool + 30 Sunken Railcars"),
            (-75.6620, 41.4090, "Scranton, Steamtown & #190 Slope", "hub", "Crown Ave 4,747-ft Tunnel + Nay Aug Bores"),
            (-75.5230, 41.5150, "Archbald Glacial Pothole", "mine", "38-ft Sub-Glacial Bedrock Shaft over Mine"),
            (-76.0420, 41.3660, "Harveys Lake (-102 ft)", "water", "PA's Largest Natural Lake | Sunken Steamboats"),
            (-76.0080, 41.5420, "Vosburg Tunnel (3,902 ft)", "tunnel", "1886 Bore through Susquehanna Meander Neck"),
            (-75.7770, 41.6220, "Tunkhannock Viaduct (Nicholson)", "sky", "2,375 ft Long x 240 ft High Concrete Colossus"),
        ],
        "cross_section": {
            "title": "SECTOR 2 VERTICAL PROFILE: POCONO PLATEAU TO ANTHRACITE DEEP BASINS (+2,175 ft to -1,500 ft)",
            "min_elev": -1600,
            "max_elev": 2400,
            "features": [
                ("Big Boulder / Camelback Peak", 2175, 0, (239, 68, 68), "2,133-2,175 ft ASL"),
                ("Tobyhanna Army Depot Radomes", 2130, 1935, (249, 115, 22), "1,400-Acre C4ISR Complex"),
                ("Hazleton & Locust Breaker", 1848, 1690, (234, 179, 8), "1,690 ft City + 158 ft Breaker"),
                ("Tunkhannock Viaduct (240 ft)", 980, 740, (168, 85, 247), "2,375 ft Concrete Arch"),
                ("Allentown PPL Tower (322 ft)", 660, 338, (59, 130, 246), "24 Stories (322 ft)"),
                ("Lehigh & Crown Ave Tunnels", 1250, 1100, (245, 158, 11), "4,380 ft & 4,747 ft Bores"),
                ("Lake Wallenpaupack (-60 ft)", 1187, 1127, (6, 182, 212), "Submerged Wilsonville Town"),
                ("Beltzville Lake (-127 ft)", 628, 501, (14, 165, 233), "Submerged Pohopoco Village"),
                ("Jeddo & Lausanne Tunnels", 1050, 550, (16, 185, 129), "7.8-Mi & 7.5-Mi Drainage Rivers"),
                ("Centralia Burning Seams", 1463, 1100, (220, 38, 38), "1,000 F Mammoth Vein Fire"),
                ("Knox Mine River Breach", 540, 200, (37, 99, 235), "10.3B Gal + 30 Sunken Gondolas"),
                ("Deep Anthracite Synclines", 550, -1200, (153, 27, 27), "Flooded Deep Coal Workings"),
            ]
        }
    },
    "Sector3_NorthEast": {
        "title": "SECTOR 3 (NORTH & EAST 25-100 MI): NYC METROPOLIS, HUDSON FJORD & CATSKILLS",
        "subtitle": "North/East NJ, Manhattan Supertalls & Subways, West Point, Shawangunks, Catskills & Long Island",
        "bbox": (-74.60, 40.15, -72.80, 42.15),
        "nodes": [
            (-74.0134, 40.7127, "One World Trade Center (1,776 ft)", "sky", "94 Stories + Oculus & Fed Gold Vault (-80 ft)"),
            (-74.0061, 40.7165, "33 Thomas St (AT&T TITANPOINTE)", "bunker", "550 ft Windowless Nuclear Telecom Fortress"),
            (-73.9810, 40.7663, "Central Park (1,550 ft) & Steinway", "sky", "Billionaires' Row Supertalls"),
            (-73.9857, 40.7484, "Empire State Bldg & Penn Station", "sky", "1,454 ft + North/East River Tunnels (-100 ft)"),
            (-73.9772, 40.7527, "GRAND CENTRAL UNDERCITY (-180 ft)", "tunnel", "67 Tracks + LIRR Caverns + M42 + Track 61"),
            (-73.9294, 40.8552, "191st St Subway Station (-180 ft)", "tunnel", "Deepest NYC Subway Station in Bedrock"),
            (-74.0357, 40.7145, "Jersey City (99 Hudson) & Bergen Arches", "sky", "900 ft Tower + PATH (-97 ft) + Palisades Cut"),
            (-74.0142, 40.6908, "Brooklyn-Battery Tunnel (9,117 ft)", "tunnel", "Longest Underwater Vehicular Tunnel in N.A."),
            (-73.9527, 40.8517, "George Washington Bridge (604 ft)", "sky", "14 Lanes Double-Deck over Hudson Palisades"),
            (-74.0447, 40.6066, "Verrazzano-Narrows Bridge (693 ft)", "sky", "4,260-ft Span over 100-ft Deep Narrows"),
            (-73.9289, 40.7792, "Hell Gate (East River -108 ft)", "water", "1885 300,000-lb Blast + Sunken HMS Hussar"),
            (-74.1856, 40.3907, "Bell Labs & Crawford Hill Horn", "sky", "1964 Cosmic Microwave Background Discovery"),
            (-74.0006, 40.4631, "Sandy Hook Fort Hancock & Nike NY-56", "bunker", "Disappearing Guns + Underground Nuclear SAMs"),
            (-74.0592, 40.1844, "Camp Evans (Project Diana Radar)", "sky", "1946 Moon-Bounce Radar & Marconi Bunkers"),
            (-72.8767, 40.8800, "Brookhaven Lab & 2.4-Mi RHIC Ring", "tunnel", "Subterranean Heavy Ion Collider Tunnel"),
            (-74.4025, 40.8881, "Boonton Reservoir (-105 ft)", "water", "Submerged Town & Furnaces of Old Boonton"),
            (-74.2944, 41.0694, "Wanaque Reservoir (-90 ft)", "water", "2,310 Acres | Submerged Boardville Ironworks"),
            (-73.8906, 41.0706, "Mario Cuomo Tappan Zee Bridge", "sky", "3.1-Mile Cable-Stayed Span (419-ft Towers)"),
            (-73.7656, 41.0736, "Kensico Reservoir (-155 ft)", "water", "Intact 1885 Dam Standing 110 ft Underwater!"),
            (-73.8350, 41.2261, "New Croton Reservoir (-141 ft)", "water", "297-ft Masonry Dam + Submerged 1842 Dam"),
            (-73.9559, 41.3915, "WEST POINT USMA & WORLD'S END (-216 ft)", "bunker", "US Gold Depository + CSX Tunnel + 216-ft Trench"),
            (-73.9775, 41.4422, "Catskill Aqueduct Siphon (-1,114 ft!)", "tunnel", "92-Mi Aqueduct Bored 1,114 ft Below Sea Level!"),
            (-73.9800, 41.5400, "Delaware Aqueduct (85.0 Miles)", "tunnel", "Longest Continuous Tunnel on Earth (-600 ft)"),
            (-74.5442, 41.4647, "Otisville Tunnel (5,314 ft)", "tunnel", "1.0-Mile Rail Bore through Shawangunk Ridge"),
            (-74.1561, 41.7689, "Mohonk Mtn House & Sky Top (1,542 ft)", "sky", "Shawangunk Quartz Cliffs & Fault Crevices"),
            (-74.0800, 41.8510, "Rosendale Iron Mountain Nuclear Vault", "bunker", "28-Ton Blast Door in Underground Limestone"),
            (-74.2000, 41.9500, "Ashokan Reservoir (-190 ft)", "water", "122.9B Gal | 12 Submerged Catskill Villages"),
            (-74.4556, 41.8211, "Rondout Reservoir (-175 ft)", "water", "Submerged Lackawack, Montela & Eureka"),
            (-74.3859, 41.9987, "Slide Mtn (4,180 ft) & Overlook Ruins", "sky", "Highest Catskill Peak + 1928 Concrete Hotel"),
        ],
        "cross_section": {
            "title": "SECTOR 3 VERTICAL PROFILE: CATSKILL PEAKS & MANHATTAN SUPERTALLS TO DEEP AQUEDUCTS (+4,180 ft to -1,114 ft)",
            "min_elev": -1300,
            "max_elev": 4400,
            "features": [
                ("Slide Mountain (Catskills Apex)", 4180, 0, (34, 197, 94), "4,180 ft ASL"),
                ("Overlook Mtn & 1928 Ruins", 3140, 2900, (168, 85, 247), "3,140 ft Peak"),
                ("One World Trade Center", 1776, 0, (59, 130, 246), "1,776 ft Tip / 94 Stories"),
                ("Central Park & Empire State", 1550, 0, (96, 165, 250), "1,550 ft & 1,454 ft"),
                ("33 Thomas St TITANPOINTE", 550, -50, (239, 68, 68), "550 ft Nuclear Tower"),
                ("Verrazzano & GWB Towers", 693, 0, (234, 179, 8), "693 ft & 604 ft Towers"),
                ("Ashokan & Kensico Reservoirs", 590, 400, (14, 165, 233), "12 Drowned Towns & 1885 Dam"),
                ("PATH, Lincoln & Holland Tubes", 0, -115, (249, 115, 22), "-93 to -115 ft Under Hudson"),
                ("Grand Central Madison & 191st St", 50, -180, (245, 158, 11), "-180 ft in Manhattan Schist"),
                ("West Point 'World's End' Fjord", 0, -216, (6, 182, 212), "-216 ft Deep + 1778 Chain"),
                ("NYC Water Tunnels #1, #2 & #3", 0, -800, (139, 92, 246), "500 to 800 ft Deep in Bedrock"),
                ("Delaware Aqueduct (85-Mi Bore)", 0, -900, (236, 72, 153), "-600 to -900 ft Under Hudson"),
                ("Catskill Aqueduct Hudson Siphon", 0, -1114, (220, 38, 38), "1,114 ft Below Sea Level!"),
            ]
        }
    },
    "Sector4_SouthSW": {
        "title": "SECTOR 4 (SOUTH & SW 25-100 MI): PINE BARRENS, GREATER PHILADELPHIA & IRON/NUCLEAR BELT",
        "subtitle": "Princeton, Lakehurst, NJ Pine Barrens, Center City Philly Subways & Cornwall/Limerick/TMI",
        "bbox": (-76.75, 39.30, -74.05, 40.55),
        "nodes": [
            (-75.1699, 39.9550, "Comcast Tech Ctr (1,121 ft) & Liberty", "sky", "Tallest Skyscrapers in PA"),
            (-75.1635, 39.9526, "PHILLY CITY HALL & SUBWAY LABYRINTH", "tunnel", "548 ft Tower + 3-Level Subway + 3.5-Mi Concourse"),
            (-75.1581, 39.9621, "Spring Garden & Arch St Ghost Stations", "tunnel", "Sealed 1989 Station & 1915 Unfinished Subway"),
            (-75.1590, 39.9530, "Center City Commuter Tunnel (1.7 Mi)", "tunnel", "4-Track Bore Jacked Under Reading Terminal"),
            (-75.1726, 39.9683, "Eastern State Penitentiary & Tunnels", "bunker", "Subterranean 'Klondike' Cells + 97-ft 1945 Tunnel"),
            (-75.1345, 39.9529, "Ben Franklin Bridge & PATCO Subway", "sky", "1,750-ft Span + Camden/Locust St Subways"),
            (-75.1783, 39.8889, "Philly Navy Yard Ghost Fleet & Drydocks", "water", "Mothballed Warships + 1,092-ft Battleship Drydocks"),
            (-75.2050, 39.8690, "Fort Mifflin Casemates & HMS Augusta", "water", "1771 Bombproofs + Submerged Chevaux-de-Frise & Wreck"),
            (-75.3711, 39.8267, "Commodore Barry Bridge (1,644-ft Span)", "sky", "452-ft Towers | 192-ft Clearance"),
            (-74.6575, 40.3496, "Princeton Firestone 3-Level Vaults", "bunker", "70+ Miles Underground Shelving + 12 Mi Steam Tunnels"),
            (-74.6022, 40.3489, "Princeton Plasma Physics Lab (PPPL)", "sky", "100M C NSTX-U Tokamak Magnetic Fusion Reactor"),
            (-74.7675, 40.2072, "Trenton Capitol & 'Trenton Makes' Bridge", "hub", "150-mph NEC Tangent + Tidal Fall Line"),
            (-75.1200, 40.3203, "Mercer Mile Concrete Castles", "sky", "Fonthill Castle, 6-Story Mercer Museum & Tile Works"),
            (-75.1892, 40.3247, "Lake Galena (-55 ft) New Galena", "water", "Flooded 1860s Lead Mine Shafts & 1832 Covered Bridge"),
            (-75.5122, 40.1436, "Black Rock Tunnel (1837 - 1,932 ft)", "tunnel", "2nd Oldest Active Rail Tunnel in US (Phoenixville)"),
            (-75.5875, 40.2242, "Limerick Nuclear Towers (507 ft Tall)", "sky", "Twin 2,317 MW BWR Reactors & Hyperbolic Towers"),
            (-75.7336, 40.1753, "French Creek Iron Shafts (-1,400 ft)", "mine", "12 Flooded Underground Levels"),
            (-75.7192, 40.0644, "Marsh Creek Lake (-80 ft) Milford Mills", "water", "Submerged 18th-Century Village Foundations"),
            (-76.4042, 40.2678, "CORNWALL IRON MINE (-1,225 ft / 400-ft Pit)", "mine", "400-ft Flooded Open Pit + 2,985-ft Incline Shafts"),
            (-76.4383, 40.3514, "Union Canal Tunnel (1827 - 729 ft)", "tunnel", "Oldest Existing Transportation Tunnel in US"),
            (-76.7250, 40.1533, "Three Mile Island Towers (372 ft)", "sky", "4 Hyperbolic Cooling Towers on Susquehanna"),
            (-74.3164, 40.0303, "Lakehurst Hangar No. 1 (966x350x224 ft)", "sky", "Colossal Airship Cathedral + Jet Sled Tracks"),
            (-74.2064, 39.8142, "Oyster Creek Nuclear & Barnegat Light", "sky", "368-ft Stack + 165-ft 'Old Barney' Lighthouse"),
            (-74.8886, 39.6272, "Winslow Blue Hole & 17.7T-Gal Aquifer", "water", "55 F Artesian Abyss over 3,000-Sq-Mi Aquifer"),
            (-74.6479, 39.6432, "Batsto Village & Mullica 1778 Wrecks", "water", "Submerged 1778 Privateer Fleet at Chestnut Neck"),
            (-74.4126, 39.3607, "Atlantic City Skyline (Ocean 710 ft)", "sky", "57-Story Glass Tower & 41,000-Pipe Boardwalk Hall"),
        ],
        "cross_section": {
            "title": "SECTOR 4 VERTICAL PROFILE: PHILLY SKYLINE & NUCLEAR TOWERS TO CORNWALL SHAFTS (+1,121 ft to -1,225 ft)",
            "min_elev": -1400,
            "max_elev": 1350,
            "features": [
                ("Comcast Tech Center (1,121 ft)", 1160, 39, (59, 130, 246), "60 Stories (1,121 ft)"),
                ("One Liberty & Ocean Casino AC", 984, 39, (96, 165, 250), "945 ft & 710 ft"),
                ("Philly City Hall Tower (548 ft)", 587, 39, (234, 179, 8), "22-ft Thick Masonry Walls"),
                ("Limerick Nuclear Towers (507 ft)", 707, 200, (239, 68, 68), "507 ft Hyperbolic Concrete"),
                ("Lakehurst Hangar No. 1 (224 ft)", 312, 88, (168, 85, 247), "966 ft Long Airship Hangar"),
                ("Philly 3-Level Subway & Commuter Bore", 39, -35, (249, 115, 22), "BSL, MFL, PATCO & 1.7-Mi Bore"),
                ("Princeton Firestone 3-Level Vaults", 203, 155, (16, 185, 129), "70+ Miles Underground Shelves"),
                ("Delaware Chevaux-de-Frise & Augusta", 0, -45, (6, 182, 212), "45-ft Channel + 1777 Wreck"),
                ("Winslow Blue Hole & Aquifer", 100, -200, (14, 165, 233), "17.7-Trillion-Gallon Aquifer"),
                ("Cornwall Flooded Open-Pit Lake", 640, 200, (37, 99, 235), "400+ ft Deep Submerged Pit"),
                ("French Creek Inclined Shafts", 510, -390, (245, 158, 11), "1,400-ft Incline (-900 ft Vert)"),
                ("Cornwall Iron Mine Slope #4", 640, -585, (220, 38, 38), "1,225 ft Depth (-585 ft BSL)"),
            ]
        }
    }
}

MASTER_BBOX = (-76.95, 39.25, -72.75, 42.20)

CAT_RGB = {
    "hub": (16, 185, 129),     # Emerald
    "sky": (245, 158, 11),     # Gold
    "tunnel": (249, 115, 22),  # Orange
    "bunker": (239, 68, 68),   # Crimson
    "mine": (236, 72, 153),    # Magenta
    "water": (6, 182, 212),    # Cyan
}


def fetch_wms_image(service_type, bbox, width=1800, height=1350):
    xmin, ymin, xmax, ymax = bbox
    bbox_str = f"{xmin},{ymin},{xmax},{ymax}"
    headers = {"User-Agent": "SAO-Area-Survey-GIS/2.0"}

    if service_type == "topo":
        url = (
            f"https://basemap.nationalmap.gov/arcgis/rest/services/USGSTopo/MapServer/export"
            f"?bbox={bbox_str}&bboxSR=4326&imageSR=4326&size={width},{height}&format=png&f=image"
        )
    elif service_type == "satellite":
        url = (
            f"https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryTopo/MapServer/export"
            f"?bbox={bbox_str}&bboxSR=4326&imageSR=4326&size={width},{height}&format=png&f=image"
        )
    elif service_type == "lidar":
        rule = urllib.parse.quote(json.dumps({"rasterFunction": "Hillshade Elevation Tinted"}))
        url = (
            f"https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage"
            f"?bbox={bbox_str}&bboxSR=4326&imageSR=4326&size={width},{height}&format=png"
            f"&renderingRule={rule}&f=image"
        )
    elif service_type == "hydro":
        url = (
            f"https://basemap.nationalmap.gov/arcgis/rest/services/USGSHydroCached/MapServer/export"
            f"?bbox={bbox_str}&bboxSR=4326&imageSR=4326&size={width},{height}&format=png32&transparent=true&f=image"
        )
    else:
        raise ValueError(service_type)

    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = resp.read()
                return Image.open(io.BytesIO(data)).convert("RGBA")
        except Exception as e:
            print(f"[WARN] Retry {attempt+1} for {service_type}: {e}")
    return Image.new("RGBA", (width, height), (18, 24, 38, 255))


def save_dual_image(img, filename):
    drive_path = os.path.join(DRIVE_IMG_DIR, filename)
    artifact_path = os.path.join(ARTIFACT_DIR, filename)
    img.convert("RGB").save(drive_path, format="PNG", optimize=True)
    shutil.copy2(drive_path, artifact_path)
    print(f"[OK] Saved {filename} ({os.path.getsize(drive_path)//1024} KB)")


def lonlat_to_xy(lon, lat, bbox, map_x0, map_y0, map_w, map_h):
    xmin, ymin, xmax, ymax = bbox
    px = map_x0 + int(((lon - xmin) / (xmax - xmin)) * map_w)
    py = map_y0 + int(((ymax - lat) / (ymax - ymin)) * map_h)
    return px, py


def render_sector_map_plate(sector_key, sector_cfg, mode, base_img, hydro_img=None):
    W, H = 2000, 1560
    MAP_X0, MAP_Y0 = 90, 115
    MAP_W, MAP_H = 1820, 1300
    bbox = sector_cfg["bbox"]
    xmin, ymin, xmax, ymax = bbox

    canvas = Image.new("RGBA", (W, H), (11, 15, 25, 255))

    # Prepare map layer
    map_layer = base_img.resize((MAP_W, MAP_H), Image.Resampling.LANCZOS)
    if mode == "underground_bathy":
        arr = np.array(map_layer.convert("RGB"), dtype=np.float32) * 0.38
        arr[:, :, 2] = np.clip(arr[:, :, 2] * 1.45 + 22, 0, 255)
        map_layer = Image.fromarray(arr.astype(np.uint8)).convert("RGBA")
        if hydro_img is not None:
            h_resized = hydro_img.resize((MAP_W, MAP_H), Image.Resampling.LANCZOS)
            map_layer = Image.alpha_composite(map_layer, h_resized)

    canvas.paste(map_layer, (MAP_X0, MAP_Y0))
    draw = ImageDraw.Draw(canvas, "RGBA")

    # Coordinate grid & ticks
    font_title = get_font(24, bold=True)
    font_sub = get_font(16, bold=False)
    font_lbl = get_font(13, bold=True)
    font_axis = get_font(13, bold=True)

    for i in range(1, 6):
        gx = MAP_X0 + int(MAP_W * i / 6)
        gy = MAP_Y0 + int(MAP_H * i / 6)
        lon_v = xmin + (xmax - xmin) * i / 6
        lat_v = ymax - (ymax - ymin) * i / 6
        draw.line([(gx, MAP_Y0), (gx, MAP_Y0 + MAP_H)], fill=(148, 163, 184, 85), width=1)
        draw.line([(MAP_X0, gy), (MAP_X0 + MAP_W, gy)], fill=(148, 163, 184, 85), width=1)
        draw.text((gx - 28, MAP_Y0 + MAP_H + 8), f"{abs(lon_v):.2f}W", fill=(203, 213, 225, 255), font=font_axis)
        draw.text((14, gy - 8), f"{lat_v:.2f}N", fill=(203, 213, 225, 255), font=font_axis)

    # Radial rings (25 mi and 100 mi)
    cos_lat = math.cos(math.radians(ORIGIN_LAT))
    for r_mi, r_col in [(25.0, (16, 185, 129, 210)), (100.0, (56, 189, 248, 190))]:
        pts = []
        for deg in range(0, 361, 2):
            rad = math.radians(deg)
            lat_p = ORIGIN_LAT + (r_mi / 69.0) * math.sin(rad)
            lon_p = ORIGIN_LON + (r_mi / (69.0 * cos_lat)) * math.cos(rad)
            px, py = lonlat_to_xy(lon_p, lat_p, bbox, MAP_X0, MAP_Y0, MAP_W, MAP_H)
            if MAP_X0 <= px <= MAP_X0 + MAP_W and MAP_Y0 <= py <= MAP_Y0 + MAP_H:
                pts.append((px, py))
            else:
                if len(pts) > 1:
                    draw.line(pts, fill=r_col, width=3)
                pts = []
        if len(pts) > 1:
            draw.line(pts, fill=r_col, width=3)

    # Border around map
    draw.rectangle([MAP_X0, MAP_Y0, MAP_X0 + MAP_W, MAP_Y0 + MAP_H], outline=(71, 85, 105, 255), width=3)

    # Plot nodes with smart collision avoidance
    placed_boxes = []
    for idx, (lon, lat, label, cat, detail) in enumerate(sector_cfg["nodes"], 1):
        if not (xmin <= lon <= xmax and ymin <= lat <= ymax):
            continue
        px, py = lonlat_to_xy(lon, lat, bbox, MAP_X0, MAP_Y0, MAP_W, MAP_H)
        rgb = CAT_RGB.get(cat, (255, 255, 255))

        # Outer halo & marker dot
        draw.ellipse([px - 9, py - 9, px + 9, py + 9], fill=(0, 0, 0, 210), outline=rgb + (255,), width=2)
        draw.ellipse([px - 5, py - 5, px + 5, py + 5], fill=rgb + (255,))

        text_str = f"[{idx}] {label}"
        if mode == "underground_bathy" and cat in ("tunnel", "bunker", "mine", "water"):
            text_str = f"[{idx}] {label} ({detail[:34]})"

        tw = int(draw.textlength(text_str, font=font_lbl))
        th = 18

        # Candidate offsets to minimize overlap
        offsets = [(12, -22), (12, 8), (-tw - 14, -22), (-tw - 14, 8), (14, -40), (14, 24)]
        best_box = None
        for ox, oy in offsets:
            bx0 = max(MAP_X0 + 6, min(px + ox, MAP_X0 + MAP_W - tw - 14))
            by0 = max(MAP_Y0 + 6, min(py + oy, MAP_Y0 + MAP_H - th - 10))
            bx1, by1 = bx0 + tw + 10, by0 + th + 6
            overlap = False
            for obx0, oby0, obx1, oby1 in placed_boxes:
                if not (bx1 < obx0 or bx0 > obx1 or by1 < oby0 or by0 > oby1):
                    overlap = True
                    break
            if not overlap:
                best_box = (bx0, by0, bx1, by1)
                break
        if best_box is None:
            bx0 = max(MAP_X0 + 6, min(px + 12, MAP_X0 + MAP_W - tw - 14))
            by0 = max(MAP_Y0 + 6, min(py - 20 + (idx % 3) * 18, MAP_Y0 + MAP_H - th - 10))
            best_box = (bx0, by0, bx0 + tw + 10, by0 + th + 6)

        placed_boxes.append(best_box)
        bx0, by0, bx1, by1 = best_box
        draw.line([(px, py), ((bx0 + bx1) // 2, (by0 + by1) // 2)], fill=rgb + (200,), width=2)
        draw.rounded_rectangle([bx0, by0, bx1, by1], radius=4, fill=(15, 23, 42, 225), outline=rgb + (240,), width=1)
        draw.text((bx0 + 5, by0 + 2), text_str, fill=(248, 250, 252, 255), font=font_lbl)

    # Header Title Bar
    mode_titles = {
        "topo": "PLATE 01: USGS HIGH-RESOLUTION TOPOGRAPHICAL SURVEY (USGSTopo)",
        "satellite": "PLATE 02: HIGH-RESOLUTION SATELLITE & HYBRID ORTHOIMAGERY (USGSImageryTopo)",
        "lidar": "PLATE 03: USGS 3DEP LiDAR ELEVATION-TINTED SHADED RELIEF & GEOMORPHOLOGY",
        "underground_bathy": "PLATE 04: SUBTERRANEAN INFRASTRUCTURE (TUNNELS, MINES, BUNKERS) & BATHYMETRY OVERLAY",
    }
    draw.text((MAP_X0, 22), f"{sector_cfg['title']} — {mode_titles[mode]}", fill=(248, 250, 252, 255), font=font_title)
    draw.text((MAP_X0, 56), f"{sector_cfg['subtitle']} | Pre-Initialization Earth Baseline | WGS84 Datum", fill=(148, 163, 184, 255), font=font_sub)

    # Footer Legend Bar
    leg_items = [
        ("Urban Hub / Municipality", CAT_RGB["hub"]),
        ("Skyscraper / Bridge / Mountain Site", CAT_RGB["sky"]),
        ("Underground Subway / Rail / Drainage Tunnel", CAT_RGB["tunnel"]),
        ("Hardened Nuclear Bunker / Vault", CAT_RGB["bunker"]),
        ("Deep Mine Shaft / Cavern / Fire", CAT_RGB["mine"]),
        ("Bathymetry / Submerged Town / Wreck", CAT_RGB["water"]),
    ]
    lx = MAP_X0
    ly = MAP_Y0 + MAP_H + 42
    for lbl, col in leg_items:
        draw.rounded_rectangle([lx, ly, lx + 18, ly + 18], radius=3, fill=col + (255,), outline=(255, 255, 255, 220))
        draw.text((lx + 24, ly - 1), lbl, fill=(226, 232, 240, 255), font=font_lbl)
        lx += int(draw.textlength(lbl, font=font_lbl)) + 48

    suffix_map = {
        "topo": "01_USGS_Topo_HiRes.png",
        "satellite": "02_Satellite_Ortho_HiRes.png",
        "lidar": "03_LiDAR_3DEP_Hillshade.png",
        "underground_bathy": "04_Underground_and_Bathymetry_Map.png",
    }
    save_dual_image(canvas, f"{sector_key}_{suffix_map[mode]}")


def render_vertical_cross_section(sector_key, sector_cfg):
    W, H = 2000, 1200
    X0, Y0 = 130, 120
    CW, CH = 1780, 860

    cs = sector_cfg["cross_section"]
    min_e, max_e = cs["min_elev"], cs["max_elev"]
    features = cs["features"]

    canvas = Image.new("RGBA", (W, H), (11, 15, 25, 255))
    draw = ImageDraw.Draw(canvas, "RGBA")

    font_title = get_font(23, bold=True)
    font_sub = get_font(15, bold=False)
    font_lbl = get_font(12, bold=True)
    font_axis = get_font(13, bold=True)

    def elev_to_y(e):
        return Y0 + int(((max_e - e) / (max_e - min_e)) * CH)

    y_zero = elev_to_y(0)
    y_bathy = elev_to_y(-300)

    # Background vertical layer bands
    draw.rectangle([X0, Y0, X0 + CW, y_zero], fill=(30, 41, 59, 180))
    draw.rectangle([X0, y_zero, X0 + CW, y_bathy], fill=(12, 74, 110, 165))
    draw.rectangle([X0, y_bathy, X0 + CW, Y0 + CH], fill=(31, 18, 43, 195))

    # Elevation grid lines
    step = 500 if (max_e - min_e) > 3500 else 250
    for e_val in range((min_e // step) * step, max_e + 1, step):
        if e_val < min_e or e_val > max_e:
            continue
        gy = elev_to_y(e_val)
        col = (56, 189, 248, 230) if e_val == 0 else (100, 116, 139, 95)
        w = 3 if e_val == 0 else 1
        draw.line([(X0, gy), (X0 + CW, gy)], fill=col, width=w)
        draw.text((25, gy - 8), f"{e_val:+d} ft", fill=(226, 232, 240, 255), font=font_axis)

    draw.text((X0 + 14, y_zero - 22), "MEAN SEA LEVEL DATUM (0 FT ASL) / WATERLINE", fill=(56, 189, 248, 255), font=font_lbl)
    draw.text((X0 + 14, Y0 + 10), "LAYER 1 & 2: ABOVE-GROUND SKYSCRAPERS, BRIDGES, MOUNTAINS & STREET LEVEL", fill=(148, 163, 184, 220), font=font_lbl)
    draw.text((X0 + 14, y_zero + 8), "LAYER 4: BELOW-THE-WATERLINE BATHYMETRY, DROWNED VILLAGES & RIVER TUNNELS", fill=(125, 211, 252, 220), font=font_lbl)
    draw.text((X0 + 14, y_bathy + 10), "LAYER 3: DEEP BEDROCK AQUEDUCTS, NUCLEAR BUNKERS & SUBTERRANEAN MINE SHAFTS", fill=(216, 180, 254, 220), font=font_lbl)

    n = len(features)
    slot_w = CW // n
    bar_w = int(slot_w * 0.56)

    for i, (name, top_e, bot_e, rgb, spec) in enumerate(features):
        cx = X0 + int((i + 0.5) * slot_w)
        yt = elev_to_y(max(top_e, bot_e))
        yb = elev_to_y(min(top_e, bot_e))
        if abs(yb - yt) < 12:
            yb = yt + 12

        draw.rounded_rectangle(
            [cx - bar_w // 2, yt, cx + bar_w // 2, yb],
            radius=4, fill=rgb + (215,), outline=(248, 250, 252, 240), width=2
        )

        # Callout box above or inside bar
        ty = max(Y0 + 34, yt - 42) if top_e >= 0 else min(Y0 + CH - 48, yb + 8)
        tw1 = int(draw.textlength(name, font=font_lbl))
        tw2 = int(draw.textlength(spec, font=font_lbl))
        bw = max(tw1, tw2) + 12
        bx0 = max(X0 + 4, min(cx - bw // 2, X0 + CW - bw - 4))
        draw.rounded_rectangle([bx0, ty, bx0 + bw, ty + 38], radius=4, fill=(11, 15, 25, 230), outline=rgb + (255,), width=1)
        draw.text((bx0 + 6, ty + 2), name, fill=(248, 250, 252, 255), font=font_lbl)
        draw.text((bx0 + 6, ty + 19), spec, fill=rgb + (255,), font=font_lbl)

        # Bottom label index
        draw.text((cx - 45, Y0 + CH + 12 + (i % 2) * 20), f"[{i+1}] {name[:18]}", fill=(203, 213, 225, 255), font=font_lbl)

    draw.rectangle([X0, Y0, X0 + CW, Y0 + CH], outline=(100, 116, 139, 255), width=3)
    draw.text((X0, 25), cs["title"], fill=(248, 250, 252, 255), font=font_title)
    draw.text((X0, 58), "4-Layer Vertical Engineering Datum Profile (Above-Ground -> Street Level -> Below-Waterline Bathymetry -> Deep Subterranean)", fill=(148, 163, 184, 255), font=font_sub)

    save_dual_image(canvas, f"{sector_key}_05_Vertical_Cross_Section.png")


def render_master_100mile_overview():
    W, H = 2000, 1600
    MAP_X0, MAP_Y0 = 90, 115
    MAP_W, MAP_H = 1820, 1340
    bbox = MASTER_BBOX

    print("[INFO] Fetching Master 100-Mile Regional GIS rasters...")
    with ThreadPoolExecutor(max_workers=3) as ex:
        f_topo = ex.submit(fetch_wms_image, "topo", bbox, 1820, 1340)
        f_lidar = ex.submit(fetch_wms_image, "lidar", bbox, 1820, 1340)
        f_sat = ex.submit(fetch_wms_image, "satellite", bbox, 1820, 1340)
        topo_img = f_topo.result()
        lidar_img = f_lidar.result()
        sat_img = f_sat.result()

    font_title = get_font(24, bold=True)
    font_sub = get_font(16, bold=False)
    font_lbl = get_font(13, bold=True)

    configs = [
        ("Master_100Mile_01_USGS_Topo_Overview.png", topo_img, "MASTER 100-MILE RADIUS SURVEY — USGS TOPOGRAPHIC COMPOSITE (ALL 4 SECTORS)"),
        ("Master_100Mile_02_LiDAR_3DEP_Shaded_Relief_Overview.png", lidar_img, "MASTER 100-MILE RADIUS SURVEY — USGS 3DEP LiDAR SHADED RELIEF (ALL 4 SECTORS)"),
        ("Master_100Mile_03_Satellite_Hybrid_Overview.png", sat_img, "MASTER 100-MILE RADIUS SURVEY — SATELLITE & HYBRID ORTHOIMAGERY (ALL 4 SECTORS)"),
    ]

    cos_lat = math.cos(math.radians(ORIGIN_LAT))
    for fname, img, title in configs:
        canvas = Image.new("RGBA", (W, H), (11, 15, 25, 255))
        canvas.paste(img.resize((MAP_W, MAP_H), Image.Resampling.LANCZOS), (MAP_X0, MAP_Y0))
        draw = ImageDraw.Draw(canvas, "RGBA")

        # Draw 25, 50, 75, 100 mile concentric rings
        for r_mi, r_col in [
            (25.0, (16, 185, 129, 240)),
            (50.0, (56, 189, 248, 210)),
            (75.0, (168, 85, 247, 210)),
            (100.0, (239, 68, 68, 240)),
        ]:
            pts = []
            for deg in range(0, 361, 2):
                rad = math.radians(deg)
                lat_p = ORIGIN_LAT + (r_mi / 69.0) * math.sin(rad)
                lon_p = ORIGIN_LON + (r_mi / (69.0 * cos_lat)) * math.cos(rad)
                px, py = lonlat_to_xy(lon_p, lat_p, bbox, MAP_X0, MAP_Y0, MAP_W, MAP_H)
                if MAP_X0 <= px <= MAP_X0 + MAP_W and MAP_Y0 <= py <= MAP_Y0 + MAP_H:
                    pts.append((px, py))
                else:
                    if len(pts) > 1:
                        draw.line(pts, fill=r_col, width=3)
                    pts = []
            if len(pts) > 1:
                draw.line(pts, fill=r_col, width=3)
            # Ring distance label due north
            lx, ly = lonlat_to_xy(ORIGIN_LON, ORIGIN_LAT + (r_mi / 69.0), bbox, MAP_X0, MAP_Y0, MAP_W, MAP_H)
            if MAP_Y0 < ly < MAP_Y0 + MAP_H:
                draw.rounded_rectangle([lx - 42, ly - 10, lx + 42, ly + 10], radius=3, fill=(11, 15, 25, 220), outline=r_col)
                draw.text((lx - 36, ly - 8), f"{int(r_mi)} MI RING", fill=r_col, font=font_lbl)

        # Plot all nodes across all 4 sectors
        for skey, scfg in SECTORS.items():
            for lon, lat, label, cat, detail in scfg["nodes"]:
                px, py = lonlat_to_xy(lon, lat, bbox, MAP_X0, MAP_Y0, MAP_W, MAP_H)
                if MAP_X0 <= px <= MAP_X0 + MAP_W and MAP_Y0 <= py <= MAP_Y0 + MAP_H:
                    rgb = CAT_RGB.get(cat, (255, 255, 255))
                    draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill=rgb + (255,), outline=(0, 0, 0, 230), width=2)

        ox, oy = lonlat_to_xy(ORIGIN_LON, ORIGIN_LAT, bbox, MAP_X0, MAP_Y0, MAP_W, MAP_H)
        draw.ellipse([ox - 12, oy - 12, ox + 12, oy + 12], outline=(250, 204, 21, 255), width=3)
        draw.text((ox + 15, oy - 10), "WASHINGTON, NJ (SECTOR 1 ORIGIN)", fill=(250, 204, 21, 255), font=font_lbl)

        draw.rectangle([MAP_X0, MAP_Y0, MAP_X0 + MAP_W, MAP_Y0 + MAP_H], outline=(71, 85, 105, 255), width=3)
        draw.text((MAP_X0, 24), title, fill=(248, 250, 252, 255), font=font_title)
        draw.text((MAP_X0, 58), "25-Mile Primary Core (Sector 1) + 25-to-100-Mile Outer Quadrants (Sectors 2, 3 & 4) | 99 Verified Survey Nodes", fill=(148, 163, 184, 255), font=font_sub)
        save_dual_image(canvas, fname)


def main():
    for skey, scfg in SECTORS.items():
        print(f"\n=== Processing {skey}: {scfg['title']} ===")
        bbox = scfg["bbox"]
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

    render_master_100mile_overview()
    print("\n[SUCCESS] All 23 High-Resolution GIS Survey Plates Generated!")


if __name__ == "__main__":
    main()
