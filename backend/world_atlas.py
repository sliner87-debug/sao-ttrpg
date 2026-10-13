"""
backend/world_atlas.py
Canonical 100-Mile Radius World Atlas & System-Merge Registry centered on
Washington Borough, NJ (07882) [40.7584° N, 74.9793° W | Grid (50, 50)].

Categories:
- "safe_zone": Safe Zones, Fortified Hubs & Faction Citadels
- "mine": Mines, Furnaces & Subterranean Extraction Zones
- "dungeon": Dungeons, Labyrinths & System-Merged Megastructures
- "wilderness": Wilderness Areas (Grind Zones), Folklore Anomalies & Transit Arteries

Quadrants:
- "Inner Core (0-25 mi)"
- "North & East (25-100 mi)"
- "West & Northwest (25-100 mi)"
- "South & Southwest (25-100 mi)"
"""

from typing import Dict, List, Optional, Any
import math

WORLD_ATLAS_ZONES: Dict[str, Dict[str, Any]] = {
    # =========================================================================
    # CATEGORY I: SAFE ZONES, FORTIFIED HUBS & FACTION CITADELS (19 ZONES)
    # =========================================================================
    "washington_borough": {
        "id": "washington_borough",
        "name": "Washington Borough, NJ (Sector 1 Hub)",
        "subtitle": "The Brass & Basalt Anchor Hub",
        "category": "safe_zone",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 0.0,
        "bearing_deg": 0,
        "compass_dir": "Origin",
        "coords": {"x": 50, "y": 50},
        "level_min": 1,
        "level_max": 10,
        "is_safe_zone": True,
        "controlling_faction": "The Vanguard Coalition & Washington Municipal Council",
        "real_world_lore": "Crossroads of NJ Routes 31 and 57 in Warren County between Scotts and Pohatcong Mountains; 19th-century Morris Canal (Port Colden) hub and 'Organ Capital of the World' (Cornish, Estey & Beethoven organ factories).",
        "system_merge_lore": "Encircled by a 40-foot emerald Hex-Grid Safe-Zone Barrier stabilized by giant brass acoustic resonator pipes salvaged from the Cornish & Beethoven Organ Works. Houses The Iron Spoke Taphouse, Doc Mercer's Underground Clinic, Quartermaster Vane's Depot, Meiji Dump, and Washington Manor.",
        "special_mechanics": "Safe-Zone Ward Protection (incinerates Red-Cursor outlaws for 100 True DMG); acoustic organ pipes disrupt monster pathing AI.",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Harmonic Organ-Pipe Resonance", "Calm Ambient Mana"],
        "monsters": [],
        "boss": None,
        "resources": ["Serrated Tripwire Coils", "Heavy Highway Snares", "Carbon Line Spools", "Rendered Chimera Marrow"],
        "signature_grafts": ["Golem Hydraulic Arm", "Subdermal Carapace Weave"],
        "stationed_companions": ["Ren", "Elora", "Torvald", "Kibs", "Valeria"],
        "aliases": [
            "washington borough", "washington safe-zone", "sector 1 safe-zone",
            "doc mercer", "underground clinic", "quartermaster vane", "logistics depot",
            "iron spoke", "meiji scavenger dump", "washington manor"
        ]
    },
    "belvidere_bastion": {
        "id": "belvidere_bastion",
        "name": "Belvidere, NJ",
        "subtitle": "The Pequest Judicial Bastion",
        "category": "safe_zone",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 7.1,
        "bearing_deg": 313,
        "compass_dir": "NW",
        "coords": {"x": 30, "y": 50},
        "level_min": 5,
        "level_max": 10,
        "is_safe_zone": True,
        "controlling_faction": "The Vanguard Coalition (Western Wardens)",
        "real_world_lore": "County seat of Warren County at the confluence of the Pequest and Delaware Rivers, famous for Victorian mansions around Garrett Wall Park, the Bel-Del Railroad, and water-powered river mills.",
        "system_merge_lore": "The Warren County Courthouse has been compiled into a Secondary Law-Tribunal Monolith allowing Orange-Cursor Infamy atonement. Spinning water-saw barricades at the Pequest waterfall shred swamp beasts emerging from the Great Meadows.",
        "special_mechanics": "Secondary Infamy Atonement Tribunal; Edison Substation electrical conduit recharge.",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Pequest Hydro-Saw Perimeter"],
        "monsters": ["Pequest Bog-Lurkers (Perimeter)", "Arc-Spark Scavengers"],
        "boss": None,
        "resources": ["Pequest Bog-Iron", "Corroded Micro-Capacitor", "Frayed Copper Wiring"],
        "signature_grafts": ["Volt-Spark Capacitor Node"],
        "stationed_companions": ["Zedd"],
        "aliases": ["belvidere", "pequest judicial", "edison substation"]
    },
    "clinton_red_mill": {
        "id": "clinton_red_mill",
        "name": "Clinton, NJ (Red Mill & Spruce Run)",
        "subtitle": "The Crimson Water-Wheel Arcane Refinery",
        "category": "safe_zone",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 9.1,
        "bearing_deg": 156,
        "compass_dir": "SSE",
        "coords": {"x": 58, "y": 64},
        "level_min": 7,
        "level_max": 14,
        "is_safe_zone": True,
        "controlling_faction": "The Iron Syndicate (Alchemical & Flux Guild)",
        "real_world_lore": "Iconic 1810 four-story Red Mill and 1763 Stone Mill on the South Branch of the Raritan River backed by the 200-foot limestone cliff of Mulligan Quarry and nearby 11-billion-gallon Spruce Run Reservoir.",
        "system_merge_lore": "The Red Mill's wooden waterwheel is fused with cold-iron runic gears that crush monster cores, Mulligan Quarry limestone, and aether-herbs into Aetheric Repair Flux. The 200-ft quarry cliff serves as an unscalable natural curtain wall.",
        "special_mechanics": "Gear Durability Restoration & Aetheric Repair Flux milling (-15% cost for Iron Syndicate allies).",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Raritan Water-Wheel Hum"],
        "monsters": ["Mulligan Cliff Gargoyles (Outer Rim)", "Spruce Run Reed-Stalkers"],
        "boss": None,
        "resources": ["Aetheric Repair Flux", "Limestone Smelting Flux", "Calcified Talc Powder", "Spruce Run Reed-Fibers"],
        "signature_grafts": [],
        "stationed_companions": ["Kaelen"],
        "aliases": ["clinton", "red mill", "spruce run", "mulligan quarry", "high bridge"]
    },
    "hackettstown_citadel": {
        "id": "hackettstown_citadel",
        "name": "Hackettstown, NJ",
        "subtitle": "The Musconetcong Citadel & Ambrosia Refinery",
        "category": "safe_zone",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 10.3,
        "bearing_deg": 50,
        "compass_dir": "ENE",
        "coords": {"x": 62, "y": 40},
        "level_min": 6,
        "level_max": 12,
        "is_safe_zone": True,
        "controlling_faction": "The Iron Syndicate & Centenary Arcanist Collegium",
        "real_world_lore": "Musconetcong Valley hub home to Centenary University (1867), the Mars Wrigley Confectionery Plant (M&M's factory), and the 1912 Charles O. Hayford State Fish Hatchery (160+ spring-fed ponds).",
        "system_merge_lore": "Centenary's golden dome projects anti-ballistic spell-wards over the town. The Mars plant operates as the Ambrosia Alchemical Refinery, processing monster marrow and aether-cocoa into hard-shelled Combat Stamina Dragees, while the 160 hatchery ponds breed armored Runic Brook-Wyrms.",
        "special_mechanics": "Produces non-perishable Ambrosia Stamina Dragees (+15 Temp HP & Stamina regen).",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Centenary Astrolabe Ward"],
        "monsters": ["Runic Brook-Wyrms (Hatchery Pools)", "Schooley's Ridge Prowlers"],
        "boss": None,
        "resources": ["Ambrosia Stamina Dragees", "Glazed Mana-Beans", "Luminescent Trout Roe", "Scrolls of Leyline Geometry"],
        "signature_grafts": [],
        "stationed_companions": [],
        "aliases": ["hackettstown", "centenary", "ambrosia refinery", "fish hatchery"]
    },
    "phillipsburg_easton_confluence": {
        "id": "phillipsburg_easton_confluence",
        "name": "Phillipsburg, NJ & Easton, PA",
        "subtitle": "The Twin-River Confluence Bastion",
        "category": "safe_zone",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 12.5,
        "bearing_deg": 248,
        "compass_dir": "WSW",
        "coords": {"x": 24, "y": 58},
        "level_min": 10,
        "level_max": 18,
        "is_safe_zone": True,
        "controlling_faction": "The Iron Syndicate (Phillipsburg) & Vanguard Coalition (Easton)",
        "real_world_lore": "Lenape 'Lechauwitank' (Place at the Forks) where the Lehigh River meets the Delaware River, linked by the 1895 cantilevered Northampton Street 'Free Bridge', Ingersoll-Rand pneumatic drill works, and Lafayette College on College Hill.",
        "system_merge_lore": "The 1895 cantilevered Free Bridge is an Armored Bridge-Citadel lined with merchant stalls and steam-ballistae above cyan mana-rapids. Phillipsburg's Ingersoll-Rand brick works forge Pneumatic Trench-Hammers and Golem Hydraulic Arms, while Lafayette College provides spell-sniper overwatch.",
        "special_mechanics": "Twin-state customs hub; pneumatic weapon & hydraulic graft fabrication.",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Confluence Ley-Current Roar"],
        "monsters": ["Confluence Hydra-Eels (River Below)", "Rusted Rail-Golem Locomotives"],
        "boss": None,
        "resources": ["High-Pressure Pneumatic Cylinders", "Cast-Iron Pipe Plating", "Anthracite Coal Cores"],
        "signature_grafts": ["Golem Hydraulic Arm"],
        "stationed_companions": ["Daphne", "Thorne"],
        "aliases": ["phillipsburg", "easton", "twin-river", "free bridge", "rusty flagon", "chemical works"]
    },
    "blairstown_viaduct": {
        "id": "blairstown_viaduct",
        "name": "Blairstown & Paulinskill Viaduct, NJ",
        "subtitle": "The Highland Keep & Seven-Arch Sky-Dock",
        "category": "safe_zone",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 15.5,
        "bearing_deg": 5,
        "compass_dir": "N",
        "coords": {"x": 51, "y": 28},
        "level_min": 12,
        "level_max": 20,
        "is_safe_zone": True,
        "controlling_faction": "The Vanguard Coalition (Paulinskill Rangers)",
        "real_world_lore": "Founded around the 1825 Grist Mill and hilltop Blair Academy (1848), flanked by the colossal 1910 Paulinskill Viaduct—a 1,100-foot-long, 115-foot-high reinforced concrete seven-arch railroad bridge.",
        "system_merge_lore": "Blair Academy's stone buildings form a walled Highland Ranger Keep staging raids into the Delaware Water Gap. The 115-ft-high Paulinskill Viaduct serves as The Viaduct Sky-Dock, its hollow inspection chambers strung with wind-leylines and rope-lifts safe above the valley floor.",
        "special_mechanics": "Elevated Sky-Dock safe rest above valley floor; aerial mount & grappling hook training.",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Viaduct Wind-Leyline Updraft"],
        "monsters": ["Paulinskill Valley Prowlers", "Viaduct Gargoyle Sentries"],
        "boss": None,
        "resources": ["Viaduct Wind-Capacitors", "Paulinskill Marl-Clay", "Ranger Longbow Sinew"],
        "signature_grafts": [],
        "stationed_companions": [],
        "aliases": ["blairstown", "paulinskill viaduct", "blair academy"]
    },
    "stroudsburg_bastion": {
        "id": "stroudsburg_bastion",
        "name": "Stroudsburg, PA",
        "subtitle": "The Gap-Gate Bastion",
        "category": "safe_zone",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 19.5,
        "bearing_deg": 324,
        "compass_dir": "NNW",
        "coords": {"x": 30, "y": 24},
        "level_min": 10,
        "level_max": 18,
        "is_safe_zone": True,
        "controlling_faction": "The Vanguard Coalition",
        "real_world_lore": "Founded around colonial Fort Hamilton (1756) and the 1795 Stroud Mansion at the confluence of Brodhead, McMichael, and Pocono Creeks just west of the Delaware Water Gap.",
        "system_merge_lore": "Mandatory border checkpoint and star-fortress anchored to the I-80 viaduct for parties crossing from New Jersey (Sector 1) into the Pocono & Anthracite Sectors. Giant Magi-Tech floodgates span Brodhead Creek to flush out river drakes.",
        "special_mechanics": "Sector 1-to-2 Border Customs & Raid Staging; Pocono Wilderness Lodge deed registry.",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Brodhead Floodgate Sluice"],
        "monsters": ["Water-Gap River Drakes (Outer Creek)"],
        "boss": None,
        "resources": ["Gap-Quartzite Whetstones", "Brodhead River Pearls"],
        "signature_grafts": [],
        "stationed_companions": [],
        "aliases": ["stroudsburg", "gap-gate", "fort hamilton", "pocono wilderness lodge"]
    },
    "morristown_jockey_hollow": {
        "id": "morristown_jockey_hollow",
        "name": "Morristown & Jockey Hollow, NJ",
        "subtitle": "The Eternal Winter Redoubt",
        "category": "safe_zone",
        "quadrant": "North & East (25-100 mi)",
        "distance_miles": 23.2,
        "bearing_deg": 89,
        "compass_dir": "E",
        "coords": {"x": 72, "y": 49},
        "level_min": 5,
        "level_max": 12,
        "is_safe_zone": True,
        "controlling_faction": "The Vanguard Coalition & The Green Wardens",
        "real_world_lore": "Site of the Continental Army's 1779–1780 'Hard Winter' Encampment (28 snowstorms) where 10,000 soldiers built 1,000 log huts across Jockey Hollow below Fort Nonsense and Washington's Ford Mansion HQ.",
        "system_merge_lore": "Exists under a localized Chrono-Atmospheric 'Valley Forge Frost-Ward'. The 1,000 reconstructed soldier huts are warmed by Ever-Burning Hearth Pylons, while Fort Nonsense operates as a Geodetic Signal Array tracking glitch-hordes spilling out of the Great Swamp and Newark.",
        "special_mechanics": "Consuming Continental Pemmican Rations here grants 'Hard Winter Resilience' (4h immunity to Glitch Freeze).",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Ever-Burning Hearth Warmth"],
        "monsters": ["Frost-Bitten Timber Wolves (Outer Trail)", "Mutated Mutineer Husks"],
        "boss": None,
        "resources": ["Iron-Hard Frost Oak Timber", "Ramapo Fault Quartz Shards", "Continental Pemmican Rations"],
        "signature_grafts": ["Cryo-Thermic Vascular Pump"],
        "stationed_companions": [],
        "aliases": ["morristown", "jockey hollow", "fort nonsense", "ford mansion"]
    },
    "new_hope_lambertville": {
        "id": "new_hope_lambertville",
        "name": "New Hope, PA & Lambertville, NJ",
        "subtitle": "The Twin-Bank Toll Haven & Neutral Span",
        "category": "safe_zone",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 27.0,
        "bearing_deg": 177,
        "compass_dir": "S",
        "coords": {"x": 52, "y": 76},
        "level_min": 20,
        "level_max": 45,
        "is_safe_zone": True,
        "controlling_faction": "The Iron Syndicate (Lambertville) & The Blood Shroud (New Hope)",
        "real_world_lore": "Historic Coryell's Ferry crossing linked by the 1904 six-span steel Pratt-truss bridge across the Delaware River, flanked by the D&R Canal (NJ) and Delaware Canal (PA).",
        "system_merge_lore": "The 1904 steel bridge was fused with border-tariff code into The Iron-Truss Neutral Span—a Lawless Neutral Bazaar where automated anti-PK sentry pillars do not fire so long as weapons remain sheathed. Lambertville is a Syndicate barge depot; New Hope is a gaslamp-gothic Blood Shroud smuggler market.",
        "special_mechanics": "Orange/Red Cursor players can enter New Hope safely to trade illicit grafts or scrub temporary Outlaw flags at the Ferryman's Ledger.",
        "ambient_effects": ["Neutral Span Tariff Truce", "Canal Lock Mist"],
        "monsters": ["Delaware Canal Lurkers (Outside Lock Gates)"],
        "boss": None,
        "resources": ["Smuggled Pennsylvania Pig-Iron", "Illicit Graft Vials", "Canal Barge Cables"],
        "signature_grafts": ["Basilisk Venom Gland", "Stalker Shadow-Tendon"],
        "stationed_companions": [],
        "aliases": ["new hope", "lambertville", "twin-bank", "coryell's ferry"]
    },
    "princeton_nassau_citadel": {
        "id": "princeton_nassau_citadel",
        "name": "Princeton Arcane University & Nassau Citadel, NJ",
        "subtitle": "Scholomance Sanctuary of the Arcane Conclave",
        "category": "safe_zone",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 35.0,
        "bearing_deg": 150,
        "compass_dir": "SSE",
        "coords": {"x": 65, "y": 80},
        "level_min": 25,
        "level_max": 40,
        "is_safe_zone": True,
        "controlling_faction": "The Arcane Conclave (Regional Headquarters)",
        "real_world_lore": "Anchored by 1756 Nassau Hall and Ralph Adams Cram's sprawling Collegiate Gothic stone quadrangles, gargoyles, and towers (Holder, Cleveland), underpinned by miles of subterranean steam tunnels.",
        "system_merge_lore": "Compiled by the System into a triple-layered Abjuration Ward Matrix projected from Cleveland Tower and guarded by Level 65 Runic Bronze Tiger Constructs flanking Whig and Clio Halls. Firestone Library's vaults hold the Grimoire Archive, while the steam tunnels below form the Under-Campus Ley-Conduits.",
        "special_mechanics": "McCosh Surgical Amphitheater & Firestone Archive unlock Tier 2–3 Graft Harmonization Feats (negating spellcasting penalties from grafts).",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Triple-Layered Abjuration Matrix", "High Ley-Line Density"],
        "monsters": ["Steam-Tunnel Mana Mephits (Sub-Campus Instances)"],
        "boss": None,
        "resources": ["Scrolls of Graft Harmonization", "Stockton Rune-Sandstone", "Liquid Ley-Condensate"],
        "signature_grafts": ["Aether-Resonant Ocular", "Neural Overclock Cortex", "Leyline Conduit Spine"],
        "stationed_companions": [],
        "aliases": ["princeton", "nassau citadel", "nassau hall", "arcane conclave hq", "firestone library"]
    },
    "milford_grey_towers": {
        "id": "milford_grey_towers",
        "name": "Milford & Grey Towers Chateau, PA",
        "subtitle": "The Arbiter Forest Citadel",
        "category": "safe_zone",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 40.1,
        "bearing_deg": 13,
        "compass_dir": "NNE",
        "coords": {"x": 58, "y": 14},
        "level_min": 18,
        "level_max": 26,
        "is_safe_zone": True,
        "controlling_faction": "The Green Wardens (Pocono Conclave Seat)",
        "real_world_lore": "Perched on bluffs above the upper Delaware River around Grey Towers (1886)—the ancestral Norman-style stone chateau of US Forest Service founder Gifford Pinchot—and 180-foot Raymondskill Falls.",
        "system_merge_lore": "Grey Towers is overgrown by colossal, sentient silver-barked hemlocks serving as the sovereign seat of The Green Wardens. The chateau's famous outdoor water-filled stone dining table ('The Fingerbowl') acts as a live Scrying Basin revealing Apex Boss spawns across the Poconos.",
        "special_mechanics": "Fingerbowl Scrying Basin reveals regional bosses; sells zero-spell-penalty organic Wood-Elf/Leshy grafts.",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Silver-Hemlock Canopy Ward"],
        "monsters": ["Raymondskill Mist-Stalkers (Gorge Approaches)"],
        "boss": None,
        "resources": ["Silver-Hemlock Sap", "Raymondskill Cataract Pearls", "Warden Camouflage Weave"],
        "signature_grafts": ["Bio-Lignin Bark-Weave"],
        "stationed_companions": [],
        "aliases": ["milford", "grey towers", "raymondskill falls"]
    },
    "jim_thorpe_citadel": {
        "id": "jim_thorpe_citadel",
        "name": "Jim Thorpe / Mauch Chunk, PA",
        "subtitle": "The Iron-Gorge Citadel & Switchback Tram",
        "category": "safe_zone",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 40.2,
        "bearing_deg": 282,
        "compass_dir": "WNW",
        "coords": {"x": 14, "y": 42},
        "level_min": 20,
        "level_max": 28,
        "is_safe_zone": True,
        "controlling_faction": "The Deepforge Guild & The Iron Syndicate",
        "real_world_lore": "The 'Switzerland of America' wedged into a narrow 1,000-foot gorge of the Lehigh River; home to the 1827 Mauch Chunk Switchback Gravity Railway and the 1871 Old Carbon County Jail (site of the Molly Maguire executions and the un-erasable coal-dust handprint in Cell #17).",
        "system_merge_lore": "Sheer gorge cliffs are fused with dwarven basalt buttresses and hex-shields. The 1827 Switchback Railway is an armored gravity-tramway hauling parties to Mt. Pisgah. Beneath the Safe Zone, the 1871 Old Jail's Cell #17 handprint acts as a Purgatorial Sub-Dungeon against The Gallows Four.",
        "special_mechanics": "Switchback Gravity-Tram elevation boost; Old Jail Cell #17 Purgatorial Trial.",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Pisgah Gravity-Rail Hum"],
        "monsters": ["The Gallows Four Revenants (Old Jail Instance)", "Cliff-Scale Wyverns (Outer Rim)"],
        "boss": "Warden of Cell #17 (Sub-Dungeon Boss)",
        "resources": ["Switchback Ballast Iron", "Lehigh Lock-Stone", "Anthracite Briquettes"],
        "signature_grafts": ["Gravity-Brake Tendon Coils"],
        "stationed_companions": [],
        "aliases": ["jim thorpe", "mauch chunk", "switchback railway", "old carbon county jail"]
    },
    "eckley_miners_village": {
        "id": "eckley_miners_village",
        "name": "Eckley Miners' Village, PA",
        "subtitle": "The Patch-Town Commune & Ribbonmen Safehouse",
        "category": "safe_zone",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 49.2,
        "bearing_deg": 290,
        "compass_dir": "WNW",
        "coords": {"x": 10, "y": 36},
        "level_min": 24,
        "level_max": 32,
        "is_safe_zone": True,
        "controlling_faction": "The Iron Syndicate vs. The Ribbonmen (Free Delvers Union)",
        "real_world_lore": "Isolated 1854 single-street coal 'patch town' atop Buck Mountain (Luzerne County), preserving miners' double-block plank dwellings, the Gothic Coal Operator's Mansion, Company Store, and towering Breaker.",
        "system_merge_lore": "Enclosed by a palisade of sharpened iron rail-ties and pressurized steam-pipes. The Company Store converts Col into Black-Shale Scrip and rents Miner's Bunks (+15% mining yield). Beneath the church and mule barn lies the secret Ribbonmen Safehouse for outlaw delvers.",
        "special_mechanics": "Miner's Bunk rest grants [Deep-Delver's Grit] (+15% mining yield, immunity to Coal-Lung); Ribbonmen forge Spoofed Green-Cursor Talismans.",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Pressurized Steam-Pipe Palisade"],
        "monsters": ["Culm-Bank Ash Hounds (Outer Strip-Pits)", "Company Enforcer Automatons"],
        "boss": None,
        "resources": ["Buck Mountain Peacock-Coal", "Blasting Powder Kegs", "Carbide Lamp Cores"],
        "signature_grafts": ["Pneuma-Filter Gill-Lung"],
        "stationed_companions": [],
        "aliases": ["eckley", "patch-town", "miners' village", "ribbonmen"]
    },
    "valley_forge_bastion": {
        "id": "valley_forge_bastion",
        "name": "Valley Forge Bastion, PA",
        "subtitle": "Southern Theater Command of the Vanguard Coalition",
        "category": "safe_zone",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 52.0,
        "bearing_deg": 208,
        "compass_dir": "SSW",
        "coords": {"x": 28, "y": 86},
        "level_min": 30,
        "level_max": 50,
        "is_safe_zone": True,
        "controlling_faction": "The Vanguard Coalition (Southern Theater Command)",
        "real_world_lore": "Site of the Continental Army's 1777–1778 winter encampment along the Schuylkill River, anchored by earthen Star Redoubts, Mount Joy, Mount Misery, and the monumental granite National Memorial Arch (1917).",
        "system_merge_lore": "Upgraded into Star-Metal & Basalt Redoubts linked by glowing blue trench-barriers. The National Memorial Arch functions as a Tactical Teleport Gate & Buff Spire, while spectral Baron von Steuben Drill-Constructs on the Grand Parade grounds allow zero-durability weapon training.",
        "special_mechanics": "Mustering beneath the Memorial Arch grants 'Winter Encampment Resolve' (+15% Cold Res, +10% Boss Construct DMG); zero-durability weapon mastery drills.",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Memorial Arch Resolve Aura"],
        "monsters": ["Automated Von Steuben Drill-Constructs (Sparring)", "Mount Misery Skirmishers"],
        "boss": None,
        "resources": ["Star-Metal Redoubt Plates", "Schuylkill Forge Coal", "Vanguard Field Rations"],
        "signature_grafts": ["Golem Hydraulic Arm", "Spring-Loaded Golem Greaves"],
        "stationed_companions": [],
        "aliases": ["valley forge", "memorial arch", "southern theater command"]
    },
    "scranton_steamtown_hub": {
        "id": "scranton_steamtown_hub",
        "name": "Scranton / Steamtown Iron-Rail Hub, PA",
        "subtitle": "The 90-Foot Arcane Roundhouse & Deepforge HQ",
        "category": "safe_zone",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 57.0,
        "bearing_deg": 321,
        "compass_dir": "NW",
        "coords": {"x": 16, "y": 14},
        "level_min": 25,
        "level_max": 35,
        "is_safe_zone": True,
        "controlling_faction": "The Deepforge Guild (Supreme Northern HQ)",
        "real_world_lore": "'The Electric City' in the Lackawanna Valley; home to the 1902–1937 DL&W Railroad Roundhouse and functional 90-foot Turntable (Steamtown NHS) plus the four massive 1848 stone Scranton Iron Furnace stacks along Roaring Brook.",
        "system_merge_lore": "The 90-foot Steamtown Turntable rotates three rune-plated Union Pacific 'Big Boy' 4-8-8-4 Golem-Locomotives armed with siege rail-cannons to align with subterranean delves. The four 1848 Scranton Iron Furnaces burn with perpetual blue Electric-Arc Anthracite as public Grade 5–6 Master-Anvils.",
        "special_mechanics": "Public Grade 5–6 Master-Anvil access for Deepforge allies (+25 Rep); Armored Rail-Train fast-travel dispatch.",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Electric-Arc Furnace Heat", "Roundhouse Steam Pressure"],
        "monsters": ["Rust-Hulk Boxcar Mimics (Outer Switchyard)", "Arc-Welder Kobold Saboteurs"],
        "boss": None,
        "resources": ["Electric-Tempered Boiler Plate", "DL&W High-Pressure Valve Cores", "Refined Aether-Alloy"],
        "signature_grafts": ["Locomotive Piston Forearm"],
        "stationed_companions": [],
        "aliases": ["scranton", "steamtown", "roundhouse nexus", "roaring brook furnaces"]
    },
    "west_point_fortress": {
        "id": "west_point_fortress",
        "name": "West Point Military Academy & Bullion Vaults, NY",
        "subtitle": "The Aegis of the Iron Chain & Continental Col Mint",
        "category": "safe_zone",
        "quadrant": "North & East (25-100 mi)",
        "distance_miles": 69.0,
        "bearing_deg": 50,
        "compass_dir": "NE",
        "coords": {"x": 86, "y": 16},
        "level_min": 12,
        "level_max": 24,
        "is_safe_zone": True,
        "controlling_faction": "The Vanguard Coalition (Northern Command) & Iron Syndicate Mint",
        "real_world_lore": "Perched on 1.1-billion-year-old hornblende granite cliffs above the Hudson River S-curve; fortified in 1778 with the Great Hudson River Chain, established in 1802 as USMA, and adjacent to the 1937 West Point Mint & Bullion Depository.",
        "system_merge_lore": "Protected by a Tier-4 Hard-Light Garrison Barrier powered by the Bullion Depository's gold-and-silver mana-capacitors. Across the Hudson narrows, the 1778 Great Chain has been resurrected as a house-sized magnetite Aether-Boom that clotheslines river leviathans.",
        "special_mechanics": "Continental Col Mint & Vault Insurance; 16-inch arcane coastal batteries target Red-Cursor outlaws 2 miles out.",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Bullion Capacitor Shield", "Great Chain Magnetic Hum"],
        "monsters": ["Highland Gargoyle Sentinels (Outer Cliff)", "Popolopen Abyssal Sturgeon", "Benedict's Echo Infiltrators"],
        "boss": None,
        "resources": ["'W'-Stamped Bullion Ingots", "High-Purity Silver Coil Wire", "Proterozoic Granite Slabs"],
        "signature_grafts": ["Bullion-Shielded Neural Bus", "Cadet Vanguard Exoskeletal Brace"],
        "stationed_companions": [],
        "aliases": ["west point", "usma", "bullion depository", "great chain"]
    },
    "batsto_village_oasis": {
        "id": "batsto_village_oasis",
        "name": "Batsto Village, NJ (Wharton State Forest)",
        "subtitle": "The Bog-Iron Rangers' Oasis",
        "category": "safe_zone",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 79.0,
        "bearing_deg": 167,
        "compass_dir": "SSE",
        "coords": {"x": 66, "y": 94},
        "level_min": 35,
        "level_max": 65,
        "is_safe_zone": True,
        "controlling_faction": "The Green Wardens (Bog-Iron Rangers)",
        "real_world_lore": "Founded in 1766 along the Batsto River to smelt Revolutionary War cannons and kettles from renewable local bog-iron (limonite) and blow flat glass; preserves 30+ historic buildings and the 36-room Batsto Mansion with its 80-foot watchtower.",
        "system_merge_lore": "The only true Safe Zone inside the 1.1-million-acre NJ Pine Barrens, ringed by iron-banded white cedar logs and a moat of boiling rust-red bog-water. The 80-ft Mansion Watchtower houses an Amber Beacon Crystal that locks procedural Glitch-Fog shifting within a 1.5-mile radius.",
        "special_mechanics": "Only forge capable of smelting Acidic Limonite Bog-Ore and Jersey Silica Sand into corrosion-proof Bog-Iron armaments and Aether-Glass lenses.",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Amber Beacon Anti-Glitch Stabilization"],
        "monsters": [],
        "boss": None,
        "resources": ["Smelted Bog-Iron Ingots", "Batsto Aether-Glass Lenses", "Tannin-Cured Cedar Heartwood"],
        "signature_grafts": ["Subdermal Carapace Weave", "Chimeric Beast Claws"],
        "stationed_companions": [],
        "aliases": ["batsto", "batsto village", "bog-iron rangers"]
    },
    "mohonk_sky_citadel": {
        "id": "mohonk_sky_citadel",
        "name": "New Paltz & Mohonk Mountain House, NY",
        "subtitle": "The Shawangunk Quartz Sky-Citadel",
        "category": "safe_zone",
        "quadrant": "North & East (25-100 mi)",
        "distance_miles": 81.8,
        "bearing_deg": 31,
        "compass_dir": "NNE",
        "coords": {"x": 78, "y": 8},
        "level_min": 14,
        "level_max": 22,
        "is_safe_zone": True,
        "controlling_faction": "The Arcane Conclave / Synod of the Silver Spire",
        "real_world_lore": "1869 Victorian castle resort built by the Smiley brothers directly onto a gleaming white Silurian quartz conglomerate fault block beside glacial Mohonk Lake and crowned by Sky Top Tower, with 1677 Historic Huguenot Street below.",
        "system_merge_lore": "The piezoelectric Shawangunk quartz conglomerate elevates Mohonk into a semi-levitating Arcane Sky-Citadel. Sky Top Tower projects a dome of Prismatic Quartz Light over Mohonk Lake, whose glacial waters act as a liquid Aether-Font.",
        "special_mechanics": "Bathing in Mohonk Tarn restores 100% Mana/Flux and purges up to 5 points of temporary Cyber-Strain.",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Prismatic Quartz Resonance", "Mohonk Aether-Font"],
        "monsters": ["Shawangunk Peregrine Griffons (Cliff Approaches)", "Lemon-Squeeze Crevice Stalkers"],
        "boss": None,
        "resources": ["Resonant Shawangunk White Quartz", "Mohonk Tarn Pure Aether-Water", "Lichen-Scrawled Spell Parchment"],
        "signature_grafts": ["Piezoelectric Quartz Optic Array", "Huguenot Stone-Ward Dermal Lattice"],
        "stationed_companions": [],
        "aliases": ["mohonk", "new paltz", "sky top tower", "huguenot street"]
    },
    "kingston_rondout_harbor": {
        "id": "kingston_rondout_harbor",
        "name": "Kingston & Rondout Maritime Harbor, NY",
        "subtitle": "The Ironclad Tidewater Port & D&H Ley-Lock",
        "category": "safe_zone",
        "quadrant": "North & East (25-100 mi)",
        "distance_miles": 95.4,
        "bearing_deg": 33,
        "compass_dir": "NNE",
        "coords": {"x": 84, "y": 4},
        "level_min": 15,
        "level_max": 25,
        "is_safe_zone": True,
        "controlling_faction": "The Iron Syndicate & Deepforge Maritime Directorate",
        "real_world_lore": "New York's first capital (1777) with its 1658 Dutch limestone Stockade District, and the 1828 eastern tidewater terminus of the 108-mile Delaware & Hudson (D&H) Canal on the Hudson River, guarded by the 1915 Rondout Lighthouse.",
        "system_merge_lore": "Eastern terminus of the D&H Arcane Aqueduct where ironclad paddlewheelers and Dwarven coal-barges dock beneath the Rondout Lighthouse's Golden Safe-Zone Beacon, which pacifies aquatic monsters within 1 mile.",
        "special_mechanics": "Armored Barge fast-travel down the D&H Canal to the Delaware River; sells underwater breathing grafts for flooded Ulster mines.",
        "ambient_effects": ["Safe-Zone Sanctuary Wards", "Rondout Lighthouse Pacification Beacon"],
        "monsters": ["Sunken Barge Barnacle-Hulks (Outer Mudflats)", "Esopus Tide-Serpents"],
        "boss": None,
        "resources": ["Kingston Bluestone Flagging", "D&H Anthracite Mana-Coal", "Rondout Hydraulic Mortar"],
        "signature_grafts": ["Cornell Tug-Piston Shoulder Actuator", "Amphibious Gill-Rebreather Valve"],
        "stationed_companions": [],
        "aliases": ["kingston", "rondout", "d&h canal terminus", "stockade district"]
    },

    # =========================================================================
    # CATEGORY II: MINES, FURNACES & SUBTERRANEAN EXTRACTION ZONES (17 ZONES)
    # =========================================================================
    "oxford_mines": {
        "id": "oxford_mines",
        "name": "Oxford Furnace & Washington Iron Mine, NJ",
        "subtitle": "The Hot-Blast Citadel & 15-Tier Magnetite Abyss",
        "category": "mine",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 3.5,
        "bearing_deg": 332,
        "compass_dir": "NNW",
        "coords": {"x": 53, "y": 48},
        "level_min": 4,
        "level_max": 14,
        "is_safe_zone": False,
        "controlling_faction": "The Iron Syndicate (Levels 1–4) / Contested Abyss (Levels 5–15)",
        "real_world_lore": "1741 colonial blast furnace that pioneered America's first hot-blast smelting in 1835; sits atop the Washington Mine (operated until 1964, plunging 2,700 feet across 15 subterranean levels in Precambrian magnetite gneiss) and the Ahles manganese-iron mine.",
        "system_merge_lore": "The 1741 stone furnace stack burns perpetually with a Preheated Ember-Leyline (HQ of Guildmaster Silas Bron). Levels 1–4 are worked by the Iron Syndicate, while Levels 5–15 have collapsed into the Magnetic Gneiss Abyss where raw Magnetite-Adamant veins generate heavy magnetic drag.",
        "special_mechanics": "Magnetic Anomaly Field on Deep Levels 5–15 (-2 DEX and -15% Movement Speed in metal armor unless grounded); hosts Rok's Blood-Pit Arena on the slag heaps and the Oxford Hot-Blast Foundry Estate.",
        "ambient_effects": ["Magnetic Gneiss Anomaly", "Preheated Furnace Draft", "Subterranean Darkness"],
        "monsters": ["Grafted Scavenger Scrappers (Lv 4)", "Ember-Forged Slag Hounds (Lv 6)", "Magnetite-Shell Tunnel Borers (Lv 9)"],
        "boss": "Silt-Marrow the Unhewn / Sub-Level 15 Balanced-Skip Colossus (Lv 14)",
        "resources": ["Raw Oxford Magnetite", "Refined Aether-Alloy", "Ahles Manganese-Ochre", "Scrap Iron Plate", "High-Voltage Capacitor"],
        "signature_grafts": ["Subdermal Carapace Weave", "Silt-Marrow Geothermal Core"],
        "stationed_companions": ["Rok"],
        "aliases": ["oxford mine", "oxford furnace", "oxford mining district", "washington mine", "blood-pit arena", "silt-marrow"]
    },
    "andover_waterloo_mine": {
        "id": "andover_waterloo_mine",
        "name": "Andover Iron Mine & Waterloo Village Forge, NJ",
        "subtitle": "The Continental Blood-Ore Gorge & Lock-Smithy",
        "category": "mine",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 18.0,
        "bearing_deg": 40,
        "compass_dir": "NE",
        "coords": {"x": 64, "y": 32},
        "level_min": 10,
        "level_max": 16,
        "is_safe_zone": False,
        "controlling_faction": "Waterloo Artificer Enclave (Forge) / Haunted Gorge (Mine)",
        "real_world_lore": "Opened in the 1760s and seized by the Continental Congress in 1778 to forge legendary blister-steel swords and musket barrels; features a 1,000-foot-long, 70-foot-deep open rock gorge rich in magnetite, blood-red specular hematite, and garnet, linked to the Morris Canal port of Waterloo Village.",
        "system_merge_lore": "The 1,000-ft Andover rock cut weeps crimson Specular Blood-Hematite and jagged Garnet Shards patrolled by Spectral 1778 Continental Dragoon Automata. Five miles south, Waterloo Village's Lock 3 West waterwheels drive giant trip-hammers that quench Blood-Ore in consecrated canal water.",
        "special_mechanics": "Weapons forged with Andover Specular Blood-Ore gain innate +1d6 Bleed; Waterloo Village serves as an Artificer smithy & Morris Canal Inclined Plane 4 West hub.",
        "ambient_effects": ["Crimson Hematite Seepage", "Waterloo Trip-Hammer Cadence"],
        "monsters": ["Hematite Bleed-Hounds (Lv 12)", "Garnet-Spined Rock Crawlers (Lv 14)", "1778 Loyalist Iron-Revenant (Lv 16)"],
        "boss": "Colonel Humphreys' Spectral Dragoon Automaton (Lv 16)",
        "resources": ["Andover Specular Blood-Ore", "Faceted Almandine Garnets", "Continental Blister-Steel Ingots"],
        "signature_grafts": ["Spring-Loaded Golem Greaves"],
        "stationed_companions": [],
        "aliases": ["andover mine", "waterloo village", "andover forge", "blood-ore gorge"]
    },
    "hibernia_mount_hope_mines": {
        "id": "hibernia_mount_hope_mines",
        "name": "Hibernia & Mount Hope Iron Mines, NJ",
        "subtitle": "The Half-Mile Hoist & 30,000-Bat Echolocation Vault",
        "category": "mine",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 25.0,
        "bearing_deg": 62,
        "compass_dir": "ENE",
        "coords": {"x": 74, "y": 38},
        "level_min": 15,
        "level_max": 24,
        "is_safe_zone": False,
        "controlling_faction": "The Deepforge Guild (Hoist) vs. Feral Chiropteran Swarm",
        "real_world_lore": "Mount Hope (1710–1978) is the oldest continuously operated iron mine in North America, sinking 2,694 feet deep in the New Leonard Shaft; adjacent Hibernia Mine (1722) features the 1.5-mile underground Glendon Railway tunnel and NJ's largest bat hibernaculum (30,000 bats).",
        "system_merge_lore": "Links Hibernia's 1.5-mile underground railway directly into Mount Hope's 2,694-foot vertical shaft. The upper 1,000 feet are governed by an Acoustic Telemetry Meter where heavy plate armor or gunfire wakes 30,000 Sonar-Fanged Ironwing Bats unless muffled by stealth fields.",
        "special_mechanics": "Acoustic Aggro Meter (heavy armor/loud attacks summon Ironwing Bat swarms unless muffled); 2,694-ft vertical ore-skip defense gauntlet.",
        "ambient_effects": ["Subterranean Pitch Darkness", "Ultrasonic Echolocation Ping", "High-Depth Rock Pressure"],
        "monsters": ["Ironwing Echolocation Swarm (Lv 15)", "Glendon Rail-Strigoi (Lv 18)", "Faesch Cannon-Foundry Dreadnought (Lv 21)"],
        "boss": "The Deep-Vein Magnetite Kraken at -2,694 ft (Lv 24)",
        "resources": ["Deep-Shaft Leonard Magnetite", "Sonic-Dampening Guano Resin", "Revolutionary Cold-Iron Cannon Scrap"],
        "signature_grafts": ["Sonar-Resonant Auditory Implant"],
        "stationed_companions": [],
        "aliases": ["hibernia mine", "mount hope mine", "new leonard shaft", "glendon tunnel"]
    },
    "watchung_basalt_copper_mines": {
        "id": "watchung_basalt_copper_mines",
        "name": "Watchung Basalt & Copper Mines (Chimney Rock & Feltville), NJ",
        "subtitle": "The Malachite Rift-Drifts & Basalt Quarry Bastions",
        "category": "mine",
        "quadrant": "North & East (25-100 mi)",
        "distance_miles": 25.4,
        "bearing_deg": 116,
        "compass_dir": "ESE",
        "coords": {"x": 74, "y": 58},
        "level_min": 6,
        "level_max": 12,
        "is_safe_zone": False,
        "controlling_faction": "The Iron Syndicate vs. Goblin Scrap-Artificers",
        "real_world_lore": "200-million-year-old Jurassic flood-basalt trap-rock quarries at Chimney Rock (Bridgewater) and 18th-century copper drift tunnels dug by Hessian POWs along the red-bed contact zone at Feltville.",
        "system_merge_lore": "The contact seam between red Passaic shale and dark Orange Mountain Basalt courses with glowing turquoise veins of Aether-Conductive Malachite and Native Copper. Goblin and Reborn riggers harvest hexagonal columnar basalt for carapace grafts.",
        "special_mechanics": "Primary early-mid source of Columnar Basalt (for Basalt Carapace Plating +2 AC) and Native Copper wiring; Verdigris Slimes corrode weapon durability (-3/hit).",
        "ambient_effects": ["Triassic Rift Copper Static", "Acidic Verdigris Drip"],
        "monsters": ["Watchung Basalt Crusher-Golems (Lv 8)", "Verdigris Copper-Slimes (Lv 7)", "Hessian Draugr Miners (Lv 9)"],
        "boss": "Ignis-Cuprum, The Rift-Seam Salamander (Lv 12)",
        "resources": ["Orange Mountain Columnar Basalt", "Watchung Native Copper & Malachite Ore", "Trace Rift-Silver Nuggets"],
        "signature_grafts": ["Basalt Carapace Plating", "Verdigris Capacitor Conduit"],
        "stationed_companions": [],
        "aliases": ["watchung copper", "chimney rock", "bridgewater copper", "feltville copper"]
    },
    "friedensville_zinc_mines": {
        "id": "friedensville_zinc_mines",
        "name": "Friedensville Zinc Mines & Ueberroth Pit, PA",
        "subtitle": "The Drowned Karst Sinkhole & 'The President' Steam-Titan",
        "category": "mine",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 25.5,
        "bearing_deg": 237,
        "compass_dir": "WSW",
        "coords": {"x": 22, "y": 68},
        "level_min": 16,
        "level_max": 22,
        "is_safe_zone": False,
        "controlling_faction": "Autonomous Cornish Steam-Constructs",
        "real_world_lore": "Birthplace of commercial US zinc mining (1845) in fractured Beekmantown dolomite; known as 'The Wettest Mines in North America', where in 1872 engineers built 'The President'—the largest single-cylinder Cornish rotary steam pump on Earth (twin 50-ft flywheels pumping 17,000 GPM).",
        "system_merge_lore": "A Dynamic Water-Level Dungeon: feeding Anthracite Coal Cores into the ruined 1872 stone Engine House engages the phantom twin 50-ft flywheels, draining 17,000 GPM from the flooded Ueberroth Pit to expose 600 feet of dry karst caverns glittering with Sphalerite and Smithsonite—but awakening THE PRESIDENT!",
        "special_mechanics": "Boiler Pump Puzzle drains flooded sinkhole tiers to expose high-grade zinc veins while triggering the boss encounter.",
        "ambient_effects": ["High-Pressure 300-PSI Steam Venting", "Flooded Karst Aquifer"],
        "monsters": ["Karst Aquifer Lurkers (Lv 16)", "Sphalerite Blackjack Crabs (Lv 18)", "Pressurized Steam-Valve Drones (Lv 19)"],
        "boss": "THE PRESIDENT: 1872 Cornish Pumping Colossus (Lv 22)",
        "resources": ["Saucon Blackjack Sphalerite", "Botryoidal Smithsonite Crusts", "110-Inch Cast-Iron Piston Scrap"],
        "signature_grafts": ["Hyperbaric Steam-Lung Seal"],
        "stationed_companions": [],
        "aliases": ["friedensville", "ueberroth pit", "the president steam", "saucon zinc"]
    },
    "edison_ogden_mine": {
        "id": "edison_ogden_mine",
        "name": "Thomas Edison's Ogden Mine & Concentrating Works, NJ",
        "subtitle": "The 480-Gauss Electromagnetic Foundry & Triphammer Wastes",
        "category": "mine",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 28.0,
        "bearing_deg": 45,
        "compass_dir": "NE",
        "coords": {"x": 70, "y": 24},
        "level_min": 16,
        "level_max": 22,
        "is_safe_zone": False,
        "controlling_faction": "Rogue Edison Construct Collective",
        "real_world_lore": "Atop Sparta Mountain (1,200 ft), Thomas Edison invested $2M in the 1890s around the 1765 Ogden Mine to crush 6-ton magnetite boulders with giant triphammers and drop the powder past 480 massive electromagnets to press iron briquettes.",
        "system_merge_lore": "Flickering cyan wireframes of Edison's towering mill-houses rise over the real concrete foundations. 480 Active Electromagnetic Coils hum across the mountain ridge, sweeping the battlefield with High-Gauss Polarity Pulses every 3 rounds.",
        "special_mechanics": "Every 3 combat rounds, a 480-Gauss Magnetic Pulse forces a DC 15 STR check to prevent iron/steel weapons from being wrenched away (Disarmed 1 turn) while boosting Lightning/MageTech damage by +25%.",
        "ambient_effects": ["480-Gauss Electromagnetic Pulse", "Triphammer Seismic Shock"],
        "monsters": ["Edison Steam-Shovel Behemoths (Lv 18)", "480-Gauss Magnetic Specters (Lv 17)", "Triphammer Crushing Golems (Lv 20)"],
        "boss": "The Wizard's Briquette Automaton (Lv 22)",
        "resources": ["High-Purity Magnetite Briquettes", "Edison Copper Induction Coils", "Overcharged Dynamo Cores"],
        "signature_grafts": ["Neural Overclock Cortex", "Leyline Conduit Spine"],
        "stationed_companions": [],
        "aliases": ["edison mine", "ogden mine", "sparta mountain mine", "concentrating works"]
    },
    "sterling_hill_franklin_mines": {
        "id": "sterling_hill_franklin_mines",
        "name": "Sterling Hill & Franklin Fluorescent Zinc Mines, NJ",
        "subtitle": "The Prismatic UV Underdark & Rainbow Tunnel",
        "category": "mine",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 29.0,
        "bearing_deg": 41,
        "compass_dir": "NE",
        "coords": {"x": 72, "y": 20},
        "level_min": 18,
        "level_max": 25,
        "is_safe_zone": False,
        "controlling_faction": "The Deepforge Guild vs. Prismatic Underdark Ecology",
        "real_world_lore": "Ogdensburg & Franklin, Sussex County — 'Fluorescent Mineral Capital of the World'. 35+ miles of tunnels down to 2,550 feet in 1.1-billion-year-old Franklin Marble containing 350+ mineral species and 90+ UV-fluorescent minerals (neon-green Willemite, crimson BIP Calcite, blue Hardystonite, black Franklinite).",
        "system_merge_lore": "Flooded with Ambient Shortwave Aetheric UV-Light, turning the 35 miles of stopes and the Rainbow Tunnel into a blazing kaleidoscope of neon green, crimson, indigo, and canary yellow where each mineral vein projects a Chromatic Leyline Aura.",
        "special_mechanics": "Neon-Green Willemite veins grant +20% Mana Regen & reveal stealth; Crimson BIP Calcite veins flash-explode (2d8 Radiant/Fire) when struck by missed attacks; Black Franklinite pillars silence spellcasting within 15 ft.",
        "ambient_effects": ["Shortwave Aetheric UV-Fluorescence", "Chromatic Leyline Resonance"],
        "monsters": ["Crystalline Willemite Stalkers (Lv 19)", "Crimson-Calcite Shell Tortoises (Lv 21)", "Franklinite Null-Golems (Lv 23)"],
        "boss": "The Rainbow Tunnel Prism-Wyrm (Lv 25)",
        "resources": ["Neon Willemite Shards", "Crimson BIP Calcite Cores", "Franklinite Null-Iron Ingots", "Blood-Red Zincite Crystals"],
        "signature_grafts": ["Aether-Resonant Ocular"],
        "stationed_companions": [],
        "aliases": ["sterling hill", "franklin mine", "ogdensburg", "rainbow tunnel", "fluorescent mine"]
    },
    "mercer_mile_castles": {
        "id": "mercer_mile_castles",
        "name": "The Mercer Mile Concrete Castles (Fonthill, Tile Works & Museum), PA",
        "subtitle": "The Atrium of Forty Thousand Animated Implements",
        "category": "mine",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 32.0,
        "bearing_deg": 193,
        "compass_dir": "SSW",
        "coords": {"x": 42, "y": 80},
        "level_min": 28,
        "level_max": 45,
        "is_safe_zone": False,
        "controlling_faction": "Arcane Conclave & Iron Syndicate Truce Expedition",
        "real_world_lore": "Built 1908–1916 in Doylestown, PA by eccentric archaeologist Henry Chapman Mercer out of hand-mixed poured concrete: 44-room Fonthill Castle, the Spanish-mission Moravian Pottery & Tile Works (5 beehive kilns), and the 6-story Gothic Mercer Museum suspending 40,000+ pre-industrial tools.",
        "system_merge_lore": "Scanning the Mercer Museum's 40,000 suspended tools caused a Poltergeist Item-Soul Overflow: flocks of animated whaling harpoons, broadaxes, and suspended Conestoga wagons whirl through the 6-story atrium. Fonthill is a Non-Euclidean Rune-Maze, and the Moravian Kilns fire socketable Ward-Tiles.",
        "special_mechanics": "Capturing the 5 Moravian Beehive Kilns lets players glaze and fire Socketable Moravian Ward-Tiles (+10 Elemental Res or +1 AC); salvaged Masterwork Toolkits grant +50 to +100 effective Crafting Mastery.",
        "ambient_effects": ["Poltergeist Item-Soul Whirlwind", "Moravian Kiln Glaze Heat"],
        "monsters": ["Swarm-Constructs of the Sixty Trades", "Terracotta Gargoyle Sentinels"],
        "boss": "The Suspended Whaleboat Leviathan (6th-Floor Atrium Rafters Boss)",
        "resources": ["Masterwork Pre-Industrial Toolkits", "Glazed Moravian Ward-Tiles", "Pozzolanic Rune-Concrete"],
        "signature_grafts": ["Basalt Carapace Plating"],
        "stationed_companions": [],
        "aliases": ["mercer mile", "fonthill castle", "mercer museum", "moravian tile works", "doylestown"]
    },
    "vera_cruz_jasper_quarries": {
        "id": "vera_cruz_jasper_quarries",
        "name": "Vera Cruz Prehistoric Jasper Quarries, PA",
        "subtitle": "The 10,000-Year Paleo-Leyline Pits",
        "category": "mine",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 33.2,
        "bearing_deg": 238,
        "compass_dir": "WSW",
        "coords": {"x": 18, "y": 66},
        "level_min": 14,
        "level_max": 22,
        "is_safe_zone": False,
        "controlling_faction": "The Green Wardens (Lithic Keepers)",
        "real_world_lore": "Over 100 prehistoric open-pit quarries near Emmaus, PA where Paleo-Indians and the Lenni Lenape mined caramel and blood-red microcrystalline quartz jasper for 10,000+ years, guarded by a statue of Chief Lappawinze.",
        "system_merge_lore": "The 100 mossy quarry craters glow with ochre and blood-red geomantic light from the Primal Pre-Collapse Leyline Layer. Metal firearms and unharmonized cyber-grafts suffer a -2 lithic dampening penalty here, while primal axes and blades hum with ancient resonance.",
        "special_mechanics": "Offering monster trophies at Chief Lappawinze's Altar allows knapping Vera Cruz Blood-Jasper Shards onto Axes/Blades (+1 Critical Hit threat range & 1d6 Bleed).",
        "ambient_effects": ["Primal Lithic Resonance (-2 Unharmonized Tech)", "Ochre Geomantic Glow"],
        "monsters": ["Hardyston Jasper Earth-Elementals (Lv 16)", "Flint-Fang Sabretooths (Lv 18)", "Red-Jasper Gargoyle Sentinels"],
        "boss": "Ancient Lithic Sabretooth Alpha (Lv 22)",
        "resources": ["Vera Cruz Blood-Jasper Shards", "Conchoidal Quartz Cores", "Primal Flint Runes"],
        "signature_grafts": [],
        "stationed_companions": [],
        "aliases": ["vera cruz", "jasper quarries", "emmaus jasper", "lappawinze"]
    },
    "lansford_no9_coal_mine": {
        "id": "lansford_no9_coal_mine",
        "name": "Lansford No. 9 Anthracite Coal Mine, PA",
        "subtitle": "The 60-Foot Mammoth Vein Drift & Rock-Hewn Hospital",
        "category": "mine",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 48.0,
        "bearing_deg": 276,
        "compass_dir": "WNW",
        "coords": {"x": 12, "y": 46},
        "level_min": 22,
        "level_max": 30,
        "is_safe_zone": False,
        "controlling_faction": "The Deepforge Guild (Upper Drift) vs. Duergar Claim-Jumpers (800-ft Sump)",
        "real_world_lore": "Opened in 1855 in the Panther Creek Valley and operated until 1972 as the world's oldest continuously operated deep anthracite mine; features a 1,600-ft horizontal drift into the 60-foot-thick Mammoth Coal Vein, a rock-hewn Underground Mine Hospital, mule stables, and an 800-ft vertical shaft.",
        "system_merge_lore": "The 1,600-ft underground hospital carved into solid bedrock is preserved by a flickering green System Ward where Reborn surgeon Doc Gallagher performs Back-Alley Graft Surgery at 50% off. Beyond yawns the 60-ft-high vaulted Mammoth Seam Cathedral and flooded Duergar sump levels.",
        "special_mechanics": "Mid-dungeon Rock-Hewn Apothecary Safe Room (50% discount on graft surgery); Black-Damp Gas Slimes explode if hit by fire/sparks.",
        "ambient_effects": ["Black-Damp Methane Pockets", "Mammoth Vein Echoes"],
        "monsters": ["Blind Mule-Horrors (Lv 23)", "Black-Damp Gas Slimes (Lv 24)", "Mammoth-Seam Duergar Claim-Jumpers (Lv 27)"],
        "boss": "Duergar Overseer Krag-Nine (Lv 30)",
        "resources": ["Mammoth-Vein Mirror Coal", "Petrified Mine-Timber", "LC&N Brass Dynamite Detonators"],
        "signature_grafts": ["Pneuma-Filter Gill-Lung"],
        "stationed_companions": [],
        "aliases": ["lansford", "no. 9 mine", "number 9 coal mine", "panther creek mine", "mammoth vein"]
    },
    "phoenixville_foundry_lock60": {
        "id": "phoenixville_foundry_lock60",
        "name": "Phoenixville Foundry & Schuylkill Lock 60, PA",
        "subtitle": "The Riveted Crucible & Drowned Slag-Vaults",
        "category": "mine",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 51.0,
        "bearing_deg": 213,
        "compass_dir": "SSW",
        "coords": {"x": 26, "y": 84},
        "level_min": 32,
        "level_max": 50,
        "is_safe_zone": False,
        "controlling_faction": "Contested Industrial Salvage Zone (Vanguard Siege Engineers)",
        "real_world_lore": "1882 monumental truss-roofed Foundry of the Phoenix Iron Works (1790–1987), inventor of the 1861 wrought-iron Griffen Artillery Gun and the 1862 hollow riveted 'Phoenix Column' that enabled the first skyscrapers, adjacent to Schuylkill Canal Lock 60.",
        "system_merge_lore": "Overhead gantry cranes inside the Foundry Hall endlessly rivet hollow Phoenix Columns into the limbs of 18-foot Wrought-Iron Siege Golems. Players manipulate the wooden-and-iron miter gates of Schuylkill Canal Lock 60 to drain or flood the Drowned Slag-Vaults beneath the rolling mills.",
        "special_mechanics": "Yields Hollow Phoenix-Alloy Cylinders (craft Heavy Plate AC armor at 35% reduced encumbrance weight!).",
        "ambient_effects": ["Automated Gantry Riveter Clatter", "Canal Lock Sluice Surge"],
        "monsters": ["Phoenix-Column Striders (18-ft Iron Constructs)", "Griffen Rifle Automaton Batteries", "Lock-Chamber Silt Lurkers"],
        "boss": "The Riveted Colossus of Lock 60 (Lv 50)",
        "resources": ["Hollow Phoenix-Alloy Cylinders", "Griffen Rifled Barrel Blanks", "Wrought-Iron Truss Plates"],
        "signature_grafts": ["Golem Hydraulic Arm", "Spring-Loaded Golem Greaves"],
        "stationed_companions": [],
        "aliases": ["phoenixville", "phoenix iron works", "lock 60", "riveted crucible"]
    },
    "hopewell_french_creek_mines": {
        "id": "hopewell_french_creek_mines",
        "name": "Hopewell Furnace & French Creek Skarn Mines, PA",
        "subtitle": "The Green-Byssolite Crystal Skarn & Iron Plantation",
        "category": "mine",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 56.0,
        "bearing_deg": 227,
        "compass_dir": "SW",
        "coords": {"x": 20, "y": 82},
        "level_min": 30,
        "level_max": 48,
        "is_safe_zone": False,
        "controlling_faction": "Iron Syndicate Prospectors & Vanguard Engineers",
        "real_world_lore": "1771 Hopewell Iron Plantation (22-ft waterwheel, cold-blast charcoal furnace) and the deep underground French Creek skarn mines at St. Peters, famous worldwide for octahedral pyrite ('fool's gold'), chalcopyrite copper, magnetite, and green fibrous byssolite inside calcite.",
        "system_merge_lore": "Hopewell's 22-foot waterwheel powers automated trip-hammers at the forest edge, while two miles south the French Creek Skarn Caverns open into a glittering emerald-and-gold crystal labyrinth lined with razor-sharp Byssolite Green-Glass Needles and laser-reflecting Pyrite Mirror-Clusters.",
        "special_mechanics": "Pyrite Mirror-Clusters reflect 20% of elemental/radiant spell damage; Byssolite-Calcite provides premier thermal insulation for geothermal grafts.",
        "ambient_effects": ["Prismatic Pyrite Reflection", "Charcoal Collier Smoke"],
        "monsters": ["Crystalline Pyrite Arachnids", "Ember-Forged Collier Wraiths", "Byssolite Shard-Stalkers"],
        "boss": "The Octahedral Skarn Matriarch (Lv 48)",
        "resources": ["French Creek Chalcopyrite", "Byssolite-Infused Calcite", "Octahedral Pyrite Cores", "White Oak Charcoal"],
        "signature_grafts": ["Silt-Marrow Geothermal Core"],
        "stationed_companions": [],
        "aliases": ["hopewell furnace", "french creek mine", "st. peters village", "byssolite"]
    },
    "huber_breaker_lackawanna_mine": {
        "id": "huber_breaker_lackawanna_mine",
        "name": "The Huber Breaker & Lackawanna #190 Slope Mine, PA",
        "subtitle": "The 11-Story Ghost-Cathedral of Blue Coal & 90-Degree Under-Barrow",
        "category": "mine",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 57.5,
        "bearing_deg": 303,
        "compass_dir": "WNW",
        "coords": {"x": 12, "y": 18},
        "level_min": 25,
        "level_max": 40,
        "is_safe_zone": False,
        "controlling_faction": "The Core Apostles (Huber Breaker) / Deepforge vs. Duergar (#190 Slope)",
        "real_world_lore": "The 1939 11-story Glen Alden Huber Breaker in Ashley (which processed 7,000 tons/day and dyed anthracite bright blue to brand 'Blue Coal' before its 2014 demolition) paired with Scranton's 1939 Continental #190 Slope Mine descending 300 ft via a sharp 90-degree underground haulage curve.",
        "system_merge_lore": "Compiled from historical LIDAR memory, the demolished 11-story Huber Breaker materializes at Dusk and during Leyline Storms as a flickering cyan Phantom Megastructure grinding culm and souls into True Blue-Coal. Nearby, the #190 Slope descends through a 5-floor Dwarven vs. Duergar room-and-pillar trench war.",
        "special_mechanics": "Huber Breaker phases into physical reality at Dusk/Night/Storms; True Blue-Coal restores +50% bonus Gear Durability at forges and grants +1d8 Cold/Force weapon damage; #190 Slope features 30-inch Monkey Airway flanking crawls.",
        "ambient_effects": ["Phase-Shifted Cyan Wireframe Architecture", "Deafening Shaker-Screen Vibration"],
        "monsters": ["Blue-Dye Alchemical Oozes", "Crusher-Chute Sawblade Golems", "Room-and-Pillar Stone Hulks", "Psionic Duergar Shock-Sappers"],
        "boss": "The Breaker-Lord of Ashley (11th-Floor Mechanized Lich-Crusher, Lv 40)",
        "resources": ["True Blue-Coal (Azure Anthracite)", "Dunmore Vein Coking-Gems", "Duergar Mind-Tempered Pickaxes"],
        "signature_grafts": [],
        "stationed_companions": [],
        "aliases": ["huber breaker", "blue coal", "lackawanna mine", "190 slope", "ashley breaker"]
    },
    "centralia_pioneer_breach": {
        "id": "centralia_pioneer_breach",
        "name": "Centralia Hellfire Seam & Pioneer Tunnel / Mahanoy Plane, PA",
        "subtitle": "The 1962 Subterranean Inferno, Graffiti Highway & Broad Mountain Hoist",
        "category": "mine",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 71.5,
        "bearing_deg": 273,
        "compass_dir": "W",
        "coords": {"x": 4, "y": 46},
        "level_min": 30,
        "level_max": 50,
        "is_safe_zone": False,
        "controlling_faction": "The Core Apostles vs. Vanguard FOB Alpha (Pioneer Tunnel)",
        "real_world_lore": "Since May 27, 1962, an underground coal seam fire in the Buck Mountain Vein has burned at >1,000°F beneath Centralia, PA, venting carbon monoxide and sulfur, collapsing homes, and buckling Route 61 ('Graffiti Highway'). Just 1.5 miles south sit Ashland's 1911 Pioneer Tunnel and the 1861 Mahanoy Plane (2,500-HP steam cable hoist up Broad Mountain).",
        "system_merge_lore": "A Permanent Tier-4 Hellfire & Magma-Ash Abyssal Breach. Spray-painted tags on the buckled Graffiti Highway have compiled into active Runic Glyph Traps and Buff Sigils. Plunging 300 ft down steaming sinkholes (or infiltrating via Pioneer Tunnel's deep gangways) leads into rivers of molten coal-slag and white-hot anthracite ribs.",
        "special_mechanics": "The 1,000-Degree Seam requires a DC 18 CON save every 3 turns without a Pneuma-Filter Gill-Lung or Fire-Ward (2d8 Fire + 2d8 Poison & +5 Cyber-Strain); weather locked to Crimson Ash (-50% healing). Mahanoy Plane's 2.5-inch mithril-steel barney-cable can harpoon flying wyverns.",
        "ambient_effects": ["Crimson Ash Fall (-50% Healing)", "1,000-Degree Subterranean Seam Heat", "Living Runic Graffiti Sigils"],
        "monsters": ["Ember-Forged Tiefling Hell-Delvers (Lv 38)", "1962 Ash-Wraiths (Lv 40)", "Crystalline Fumarole Golems (Lv 44)", "Runaway Barney-Car Juggernauts"],
        "boss": "IGNIS-62: The Undying Seam-Wyrm (Lv 50 3-Phase Sector Raid Boss)",
        "resources": ["Heart-of-Centralia Eternal Ember (Grade 6/7 Mythic)", "Vitrified Anthracite Glass", "Sublimated Brimstone Crystals", "Mahanoy Barney-Cable Spools"],
        "signature_grafts": ["Thermionic Anthracite Heart-Reactor", "Winch-Spool Grapple Wrist"],
        "stationed_companions": [],
        "aliases": ["centralia", "graffiti highway", "pioneer tunnel", "mahanoy plane", "ashland", "hellfire seam"]
    },
    "pine_barrens_bog_iron_furnaces": {
        "id": "pine_barrens_bog_iron_furnaces",
        "name": "Pine Barrens Bog-Iron Pits (Batsto, Martha & Weymouth Furnaces), NJ",
        "subtitle": "The 24-Hour Bacterial Limonite Beds & Haunted Blast-Kilns",
        "category": "mine",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 80.0,
        "bearing_deg": 168,
        "compass_dir": "SSE",
        "coords": {"x": 68, "y": 96},
        "level_min": 35,
        "level_max": 52,
        "is_safe_zone": False,
        "controlling_faction": "The Green Wardens (Batsto Perimeter) / Feral Ordnance Automata",
        "real_world_lore": "Along the acidic (pH 3.5–5.0), tannin-rich 'cedar water' rivers of the Pine Barrens, iron-oxidizing Leptothrix bacteria naturally precipitate spongy masses of limonite bog-iron that regenerate every 20–30 years, feeding colonial furnaces at Batsto (1766), Martha (1793), and Weymouth (1802).",
        "system_merge_lore": "The System accelerated the real-world 20-year bacterial bog-iron cycle into a 24-hour hyper-regeneration loop: tea-colored cedar streams bubble with incandescent orange Ferro-Bacteria growing jagged crusts of Living Bog-Limonite and green Aether-Slag. Martha's cellar holes open into Slag-Centipede Burrows, and Weymouth's Gothic arches house haunted 1812 mortar-golems.",
        "special_mechanics": "Regenerating Limonite Bog-Ore respawns daily and imparts innate Acid/Rust-Proof and Bleed properties to forged weapons.",
        "ambient_effects": ["Acidic Cedar-Water Corrosion", "Incandescent Ferro-Bacterial Bloom"],
        "monsters": ["Ferro-Sludge Oozes (Dissolve Armor Durability)", "Ember-Forged Bog-Turtles", "Weymouth 1812 Ordnance Automata"],
        "boss": "The Weymouth Cast-Iron Mortar Behemoth (Lv 52)",
        "resources": ["Regenerating Limonite Bog-Ore", "Vitreous Pine-Glass Slag", "Tannin-Cured Cedar Heartwood"],
        "signature_grafts": ["Subdermal Carapace Weave"],
        "stationed_companions": [],
        "aliases": ["bog-iron pits", "martha furnace", "weymouth furnace", "limonite beds"]
    },
    "tilly_foster_rosendale_mines": {
        "id": "tilly_foster_rosendale_mines",
        "name": "Tilly Foster Iron Pit & Rosendale Widow Jane Cement Mines, NY",
        "subtitle": "The 600-Foot Pseudomorph Chasm & Drowned Pillar-Cathedral",
        "category": "mine",
        "quadrant": "North & East (25-100 mi)",
        "distance_miles": 85.0,
        "bearing_deg": 44,
        "compass_dir": "NE",
        "coords": {"x": 88, "y": 10},
        "level_min": 14,
        "level_max": 23,
        "is_safe_zone": False,
        "controlling_faction": "The Deepforge Guild & Iron Syndicate Diving Teams vs. Drow Syndicates",
        "real_world_lore": "Tilly Foster (Brewster, NY) is a 600-ft-deep flooded magnetite skarn pit famous worldwide for mineral pseudomorphs (crystals replacing other crystals' shapes) that collapsed in 1895. Rosendale's Widow Jane Mine (Ulster Co., NY) is a vast flooded room-and-pillar natural hydraulic cement cavern system that built the Brooklyn Bridge and Statue of Liberty pedestal.",
        "system_merge_lore": "Tilly Foster's 600-ft flooded chasm is criss-crossed by electrified 19th-century aerial tram cables and populated by shapeshifting Pseudomorph Mimic-Golems. Widow Jane's room-and-pillar dolostone halls glow with Silurian chain-coral fossils that amplify sonic and thunder damage by +50%.",
        "special_mechanics": "Tilly Foster yields Serpentine Pseudomorph Cores (allowing an Artificer/Smith to transfer a weapon's passive trait onto a new frame); Widow Jane amplifies Sonic/Thunder by +50% but risks Pillar Integrity Collapse.",
        "ambient_effects": ["Acoustic Room-and-Pillar Reverberation (+50% Sonic)", "Submerged Hoist-Cable Tangled Depths"],
        "monsters": ["Pseudomorph Mimic-Golems (Lv 17)", "Calcified Quarry Golems (Lv 15)", "Silurian Coral Hydras (Lv 18)"],
        "boss": "The Widow in the DarkWater (Lv 20) & Old Tilly, The 1895 Landslide Behemoth (Lv 23)",
        "resources": ["Serpentine Pseudomorph Core", "Tilly Foster Bessemer Magnetite", "Rosendale Hydraulic Dolostone", "Fossilized Silurian Chain-Coral"],
        "signature_grafts": ["Pseudomorphic Adaptive Carapace", "Dolostone Load-Bearing Spine"],
        "stationed_companions": [],
        "aliases": ["tilly foster", "rosendale", "widow jane mine", "pseudomorph chasm"]
    },
    "cornwall_magnetite_maw": {
        "id": "cornwall_magnetite_maw",
        "name": "Cornwall Iron Furnace & The 500-Foot Flooded Open-Pit, PA",
        "subtitle": "The Magnetite Maw & 1742 Gothic Great-Wheel",
        "category": "mine",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 83.0,
        "bearing_deg": 246,
        "compass_dir": "WSW",
        "coords": {"x": 6, "y": 72},
        "level_min": 45,
        "level_max": 75,
        "is_safe_zone": False,
        "controlling_faction": "The Iron Syndicate Forward Extraction Expedition",
        "real_world_lore": "Cornwall Iron Furnace (1742) in Lebanon County, PA is the only intact charcoal blast furnace in the Western Hemisphere (rebuilt in Gothic Revival style in the 1850s), sitting beside the Cornwall Ore Banks—mined continuously for 231 years (1742–1973) for 106M tons of magnetite, copper, cobalt, gold, and silver, leaving a 500-ft-deep flooded open pit.",
        "system_merge_lore": "The 500-ft flooded crater is an inverted-spiral Amphitheater Mine radiating a Tier-3 Geomagnetic Anomaly. Above the pit, the intact 1742 Gothic Revival Blast Furnace roars with its 24-foot Great Wheel driven by aether-steam, smelting Lodestone-Tempered Ingots.",
        "special_mechanics": "Tier-3 Geomagnetic Anomaly imposes -15% Movement Speed on heavy metal armor toward the pit floor while boosting Lightning/Electromagnetic critical damage by +25%.",
        "ambient_effects": ["Tier-3 Geomagnetic Pull (-15% Metal Armor Speed)", "+25% Lightning Crit Resonance"],
        "monsters": ["Crystalline Lodestone Golems (Magnetic Pull Aura)", "Cobalt-Vein Wyrms"],
        "boss": "Abyssal Pit-Leviathan 'Agnes' (Lv 72 Submerged Crater Boss)",
        "resources": ["High-Grade Cornwall Magnetite", "Chalcopyrite & Native Cobalt Nodes", "Byproduct Gold & Silver Harmonization Filigree"],
        "signature_grafts": ["Leyline Conduit Spine"],
        "stationed_companions": [],
        "aliases": ["cornwall furnace", "cornwall mine", "magnetite maw", "lebanon iron pit"]
    },

    # =========================================================================
    # CATEGORY III: DUNGEONS, LABYRINTHS & MEGASTRUCTURE RIFTS (20 ZONES)
    # =========================================================================
    "pohatcong_labyrinth": {
        "id": "pohatcong_labyrinth",
        "name": "The Pohatcong Depths (Sector 1 Labyrinth)",
        "subtitle": "The Nine-Chamber Subterranean Spire Vault",
        "category": "dungeon",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 2.0,
        "bearing_deg": 205,
        "compass_dir": "SSW",
        "coords": {"x": 49, "y": 54},
        "level_min": 5,
        "level_max": 10,
        "is_safe_zone": False,
        "controlling_faction": "The Gilded Spire Overlord (Sector 1 Boss)",
        "real_world_lore": "Deep Precambrian gneiss fault caverns and abandoned iron exploratory adits beneath Pohatcong Mountain behind the waterfall of Roaring Rock Brook.",
        "system_merge_lore": "Canonical 9-room Sector 1 Labyrinth (Subsurface Ingress -> Calcified Mine Gallery -> Runic Tripwire Corridor -> Drainage Junction -> Echoing Reservoir -> Crystal Antechamber -> Harmonic Frequency Vault [3-1-4] -> Overlord's Throne Gate -> Gilded Spire Throne Room).",
        "special_mechanics": "3-Pylon Harmonic Frequency Puzzle [Sequence: 3, 1, 4]; Boss environmental counters (sever_conduit, shatter_pillar, hide_behind_slag).",
        "ambient_effects": ["Subterranean Ley-Hum", "Cyan Mana-Dart Traps"],
        "monsters": ["Glitched Excavator Drone", "Aether-Corrupted Cave Stalker", "Mire-Titan Carapace Lurker"],
        "boss": "The Gilded Spire Overlord (Lv 5/10, 300 HP, 3 Phases)",
        "resources": ["Resonator Tuning Prism", "Overlord's Gilded Core (Grade 6 Mythic)", "Titanium Wire Scrap"],
        "signature_grafts": ["Golem Hydraulic Arm"],
        "stationed_companions": ["Malakor"],
        "aliases": ["pohatcong depths", "pohatcong labyrinth", "gilded spire", "gilded overlord", "pohatcong sinkholes"]
    },
    "merrill_creek_blood_shroud": {
        "id": "merrill_creek_blood_shroud",
        "name": "Merrill Creek Reservoir & Scotts Mountain Glitch-Vaults, NJ",
        "subtitle": "The 225-Foot Abyssal Intake & Blood Shroud PK Citadel",
        "category": "dungeon",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 6.0,
        "bearing_deg": 256,
        "compass_dir": "WSW",
        "coords": {"x": 40, "y": 53},
        "level_min": 8,
        "level_max": 15,
        "is_safe_zone": False,
        "controlling_faction": "The Blood Shroud Cartel (Headquarters)",
        "real_world_lore": "Atop Scotts Mountain sits Merrill Creek Reservoir (NJ's deepest lake at 225 feet), linked to the Delaware River 3.3 miles away via a deep subterranean rock tunnel and towering concrete Intake/Outlet Depth Tower.",
        "system_merge_lore": "The Blood Shroud (Red-Cursor PK syndicate led by The Pale Whisper) hijacked the 3.3-mile subterranean rock tunnel and the 225-foot hollow concrete Intake Tower, converting it into an unmapped, anti-scrying Outlaw Under-Citadel.",
        "special_mechanics": "Red-Cursor PK ambush mechanics, monofilament tripwire corridors, and high-value outlaw bounty contracts.",
        "ambient_effects": ["Anti-Scrying Glitch Fog", "225-Foot Hydrostatic Pressure"],
        "monsters": ["Blood Shroud Red-Cursor Assassins (Lv 10–14)", "Depth-Tower Hydro-Gargoyles (Lv 12)"],
        "boss": "The Pale Whisper (Blood Shroud Cartel Leader, Lv 15)",
        "resources": ["Serrated Tripwire Coils", "Blood-Shroud Bounty Ledger", "Uncorroded Bone-Signet"],
        "signature_grafts": ["Stalker Shadow-Tendon"],
        "stationed_companions": [],
        "aliases": ["merrill creek", "scotts mountain", "glitch-vaults", "blood shroud hq"]
    },
    "round_valley_sunken_ring": {
        "id": "round_valley_sunken_ring",
        "name": "Round Valley Reservoir (Cushetunk Ring), NJ",
        "subtitle": "The Abyssal Intake & Drowned Village of McPherson",
        "category": "dungeon",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 12.5,
        "bearing_deg": 142,
        "compass_dir": "SE",
        "coords": {"x": 62, "y": 66},
        "level_min": 12,
        "level_max": 18,
        "is_safe_zone": False,
        "controlling_faction": "Unclaimed Abyssal Anomaly",
        "real_world_lore": "A 2,350-acre, 180-foot-deep reservoir holding 55 billion gallons inside a natural ring of volcanic diabase rock (Cushetunk Mountain) over the drowned 1950s farming village of McPherson; notorious as the 'Bermuda Triangle of NJ' where 25+ people vanished.",
        "system_merge_lore": "Cushetunk's volcanic diabase ring acts as a Parabolic Leyline Dish trapping displaced avatar data beneath 180 feet of water. Concrete Depth Towers act as vertical airlock elevators descending into a Hyperbaric Aether-Bubble on the lakebed where the drowned village of McPherson stands intact.",
        "special_mechanics": "Surface skiffs face Cushetunk Microburst squalls; lakebed Hyperbaric Dome allows breathing on the flooded streets of McPherson.",
        "ambient_effects": ["Cushetunk Dimensional Microbursts", "-180ft Hyperbaric Aether-Bubble"],
        "monsters": ["Submerged Pine-Forest Entanglers (Lv 12)", "Drowned Echoes of McPherson (Lv 14)", "Thermocline Frost-Serpents (Lv 16)"],
        "boss": "The Cushetunk Trench Kraken (Lv 18)",
        "resources": ["Abyssal Pressure-Glass", "Drowned Pre-Collapse Relics", "Large-Mine Submerged Magnetite"],
        "signature_grafts": ["Hyperbaric Steam-Lung Seal"],
        "stationed_companions": [],
        "aliases": ["round valley", "cushetunk", "mcpherson", "bermuda triangle of nj"]
    },
    "yards_creek_hydro_siphon": {
        "id": "yards_creek_hydro_siphon",
        "name": "Yards Creek Pumped-Storage Hydro-Siphon, NJ",
        "subtitle": "The 453-Megawatt Chrono-Reversing Turbine Rift",
        "category": "dungeon",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 17.3,
        "bearing_deg": 351,
        "compass_dir": "NNW",
        "coords": {"x": 46, "y": 26},
        "level_min": 14,
        "level_max": 20,
        "is_safe_zone": False,
        "controlling_faction": "Contested (Vanguard Engineers vs. Chrono-Constructs)",
        "real_world_lore": "Built in 1965 on Kittatinny Mountain near Blairstown; a 453-MW pumped-storage hydroelectric station linking an Upper Reservoir on the mountain crest with a Lower Reservoir 700 vertical feet below via giant steel penstock pipes and reversible Francis pump-turbines.",
        "system_merge_lore": "Directly tied to the Chrono-Atmospheric Day/Night Cycle: by Day (08:00–18:00), liquid mana roars downward through the 700-ft penstocks to supercharge the Lower Powerhouse while draining the Upper Reservoir mud-bed; at Night (21:00–06:00), the reversible turbines suck water and swimmers upward!",
        "special_mechanics": "Daytime exposes Upper Reservoir crystal beds & electrifies Lower Powerhouse; Nighttime reverses penstock gravity upward.",
        "ambient_effects": ["453-MW Hydro-Arc Static", "Chrono-Reversing Penstock Current"],
        "monsters": ["450-MW Arc-Elementals (Lv 16)", "Penstock Siphon-Wyrms (Lv 18)", "Francis Turbine Automata"],
        "boss": "The Reversible Dynamo Archon (Lv 20)",
        "resources": ["Hydro-Charged Leyline Crystals", "High-Voltage Capacitor", "Penstock Alloy Plates"],
        "signature_grafts": ["Leyline Conduit Spine"],
        "stationed_companions": [],
        "aliases": ["yards creek", "pumped-storage", "hydro-siphon"]
    },
    "lost_river_caverns": {
        "id": "lost_river_caverns",
        "name": "Lost River Caverns (Hellertown), PA",
        "subtitle": "The Unindexed Styx & Crystal Chapel",
        "category": "dungeon",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 21.8,
        "bearing_deg": 236,
        "compass_dir": "SW",
        "coords": {"x": 24, "y": 66},
        "level_min": 11,
        "level_max": 16,
        "is_safe_zone": False,
        "controlling_faction": "Non-Euclidean Karst Ecology",
        "real_world_lore": "Discovered in 1883 in Beekmantown Limestone; features five vaulted chambers (including the subterranean Crystal Chapel) through which flows 'The Lost River'—an underground stream whose source and outlet have never been found despite fluorescent dye-tracing.",
        "system_merge_lore": "Because human science never mapped where the Lost River begins or ends, Cardinal threw '// ERROR: RIVER_TERMINUS_UNDEFINED'. Rafting the underground stream carries parties into Procedural Quarantine Caverns that shift every 24 hours, anchored by the restorative Crystal Chapel safe room.",
        "special_mechanics": "Crystal Chapel mid-dungeon rest sanctuary; Unindexed Null-Water erases tracking beacons and aggro.",
        "ambient_effects": ["Null-Pointer Topology Shift", "Crystal Chapel Harmonic Chime"],
        "monsters": ["Stalactite Drop-Piercers (Lv 11)", "Blind Albino Cave-Salamanders (Lv 13)", "Unindexed Null-Water Lurkers (Lv 15)"],
        "boss": "The Five-Headed Limestone Hydra (Lv 16)",
        "resources": ["Unindexed Null-Water Vials", "Calcified Cave-Pearls", "Flowstone Chitin Shards"],
        "signature_grafts": [],
        "stationed_companions": [],
        "aliases": ["lost river caverns", "hellertown caverns", "crystal chapel", "unindexed styx"]
    },
    "bethlehem_steel_stacks": {
        "id": "bethlehem_steel_stacks",
        "name": "Bethlehem Steel Stacks, PA",
        "subtitle": "The Five Pillars of Surtr & Hoover-Mason Sky-Trestle",
        "category": "dungeon",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 22.6,
        "bearing_deg": 244,
        "compass_dir": "WSW",
        "coords": {"x": 18, "y": 65},
        "level_min": 22,
        "level_max": 30,
        "is_safe_zone": False,
        "controlling_faction": "Vulcan-Prime & Autonomous Foundry Constructs",
        "real_world_lore": "160-acre industrial colossus (1857–1995) that forged US Navy battleship armor and Manhattan's skyscrapers; dominated by five 235-foot-tall Blast Furnaces (A–E), fifteen Hot-Blast Stoves, the elevated Hoover-Mason Trestle railway, and the massive Blower House.",
        "system_merge_lore": "All five 235-foot blast furnaces roar with Abyssal Hellfire & Molten Code across a 3-Wing Industrial Raid: Wing 1 (Hoover-Mason Trestle catwalks dodging molten slag trains), Wing 2 (Blower House flywheel engines), and Wing 3 (Blast Furnace C's Bessemer Throne). Warforged companion Titus (Unit PX-09) is stationed here.",
        "special_mechanics": "Sabotaging or overriding the 8 Blower House flywheel engines reduces the Heat Aura in Blast Furnace C's boss arena by 50%.",
        "ambient_effects": ["2,800°F Blast Furnace Convection", "Runaway Scale-Car Tracks"],
        "monsters": ["Hoover-Mason Ore-Hauler Construct (Lv 22)", "Molten Slag-Slime (Lv 23)", "Blower-House Piston Gargoyle (Lv 25)", "Battleship-Plate Ironclad Knight (Lv 27)"],
        "boss": "VULCAN-PRIME, The Bessemer Colossus (Lv 30 Raid Overlord)",
        "resources": ["Bessemer Battleship-Grade Adamant Plates", "Furnace-C Cinder Core (Grade 6–7 Mythic)", "Titanium Wire Scrap"],
        "signature_grafts": ["Golem Hydraulic Arm", "Silt-Marrow Geothermal Core"],
        "stationed_companions": ["Titus"],
        "aliases": ["bethlehem steel", "steel stacks", "hoover-mason trestle", "lehigh basin node", "vulcan-prime"]
    },
    "picatinny_arsenal_citadel": {
        "id": "picatinny_arsenal_citadel",
        "name": "Picatinny Arsenal (Rockaway Gorge), NJ",
        "subtitle": "The 6,500-Acre Ordnance Exclusion Zone & 1926 Blast Craters",
        "category": "dungeon",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 24.8,
        "bearing_deg": 60,
        "compass_dir": "ENE",
        "coords": {"x": 73, "y": 36},
        "level_min": 20,
        "level_max": 30,
        "is_safe_zone": False,
        "controlling_faction": "Arsenal-Director Faesch-80 (Autonomous Defense AI)",
        "real_world_lore": "6,500-acre US Army Armament R&D Center on the site of the 1749 Middle Forge; birthplace of the universal Picatinny Rail and site of the July 10, 1926 Lake Denmark Naval Ammunition Depot catastrophe (where lightning detonated 2.4 million lbs of TNT and depth charges).",
        "system_merge_lore": "Compiled into an autonomous MageTech Siege Fortress governed by [ARSENAL-DIRECTOR: FAESCH-80]. Automated Picatinny Rail-Turrets and laser-guided mortars sweep the valley floor while the 1926 Lake Denmark craters burn under perpetual Crimson Ash and Detonation Elementals.",
        "special_mechanics": "Players must sprint from concrete Munition Igloo to Munition Igloo during timed Artillery Barrage Telegraphs; drops Universal Picatinny Rune-Rails (allowing MageTech scopes/capacitors to mount on melee axes, hammers, and bows).",
        "ambient_effects": ["Automated Mortar Target-Locks", "1926 Lake Denmark Crimson Ash"],
        "monsters": ["Picatinny Rail-Hound Construct (Lv 20)", "Armored Munition-Igloo Mimic (Lv 22)", "1926 Lake Denmark Blast-Wraith (Lv 24)", "M777 Aether-Howitzer Walker (Lv 26)"],
        "boss": "Arsenal-Director Faesch-80: The Siege Juggernaut (Lv 28)",
        "resources": ["Universal Picatinny Rune-Rails", "Depleted-Uranium Hammer Heads", "Military Black-Box Prototypes"],
        "signature_grafts": ["Ballistic Recoil-Stabilizer Arm Graft"],
        "stationed_companions": [],
        "aliases": ["picatinny", "picatinny arsenal", "lake denmark", "munition gorge"]
    },
    "bell_labs_holmdel_complex": {
        "id": "bell_labs_holmdel_complex",
        "name": "Bell Labs Murray Hill & Holmdel Horn Antenna, NJ",
        "subtitle": "The 1947 Solid-State Labyrinth & 2.7K Cosmic Microwave Observatory",
        "category": "dungeon",
        "quadrant": "North & East (25-100 mi)",
        "distance_miles": 30.7,
        "bearing_deg": 99,
        "compass_dir": "E",
        "coords": {"x": 78, "y": 56},
        "level_min": 10,
        "level_max": 21,
        "is_safe_zone": False,
        "controlling_faction": "The Arcane Conclave & MageTech Artificers vs. UNIX Daemons",
        "real_world_lore": "Twin shrines of modern physics: Murray Hill (where Bardeen, Brattain & Shockley invented the Transistor in 1947, C, UNIX, and the world's quietest Anechoic Chamber) and Holmdel/Crawford Hill (Eero Saarinen's mirror-glass megastructure and the 20-ft Aluminum Horn Antenna where Penzias & Wilson discovered the 2.7K Cosmic Microwave Background of the Big Bang in 1964 after evicting nesting pigeons).",
        "system_merge_lore": "Linked via microwave ley-beam: Wing A (Murray Hill, Lv 10–14) features UNIX Daemons that fork/duplicate every 3 turns and an Anechoic Null-Chamber imposing total Silence. Wing B (Holmdel Horn Antenna, Lv 16–21) channels raw Primordial Void-Static from outside the Cardinal Simulation, guarded by mutated Dielectric Pigeon Griffons.",
        "special_mechanics": "Anechoic Chamber mutes all verbal spells/sound; UNIX Daemons must have parent PID killed to stop forking; drops the Murray Hill Solid-State Co-Processor (+1 Active Ability Slot). Core to Ren Sasaki's personal questline!",
        "ambient_effects": ["Anechoic Total Silence Zone", "2.7-Kelvin Cosmic Microwave Static", "Saarinen Mirror-Glass Refraction"],
        "monsters": ["Germanium Point-Contact Spiders (Lv 11)", "UNIX Daemons PID-09 (Lv 13)", "Dielectric Pigeon Griffons (Lv 17)"],
        "boss": "The Shockley-Triode Sovereign (Lv 14) & Aether-Astronomer Penzias-9 (Lv 21)",
        "resources": ["1947 Point-Contact Germanium Wafer", "Anechoic Sound-Dampening Foam", "2.7-Kelvin Cosmic Static Vial", "Saarinen Mirror-Glass Prism"],
        "signature_grafts": ["Murray Hill Solid-State Co-Processor", "Holmdel Microwave Telemetry Dish"],
        "stationed_companions": [],
        "aliases": ["bell labs", "murray hill", "holmdel", "horn antenna", "crawford hill"]
    },
    "princeton_pppl_tokamak": {
        "id": "princeton_pppl_tokamak",
        "name": "Princeton Plasma Physics Laboratory (PPPL), NJ",
        "subtitle": "The Matterhorn Star-Core & 510-Million-Degree Tokamak Raid",
        "category": "dungeon",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 34.5,
        "bearing_deg": 145,
        "compass_dir": "SSE",
        "coords": {"x": 67, "y": 79},
        "level_min": 55,
        "level_max": 75,
        "is_safe_zone": False,
        "controlling_faction": "Solaris-Zero (Contested Raid Perimeter by Arcane Conclave)",
        "real_world_lore": "Founded in 1951 as Cold War Project Matterhorn by Lyman Spitzer (inventor of the Stellarator); home to the TFTR reactor (which hit 510 million °C—30x hotter than the sun's core) and the active NSTX-U Spherical Torus surrounded by copper field coils and -269°C liquid helium cryogenics.",
        "system_merge_lore": "When the Overlay struck mid-pulse, the spherical tokamak fused with an Astral Mana Singularity. Features 4 Wings: Stellarator Figure-8 gravity-inverting tunnels, -269°C Cryo-Helium Vaults, Neutral Beam Laser Hall, and the NSTX-U Spherical Torus housing a miniature captive sun.",
        "special_mechanics": "Boss alternates between Magnetic Pinch (pulls all players toward center-stack) and Deuterium-Tritium Ignition (requires venting cryo-valves before thermal gauge hits 100%).",
        "ambient_effects": ["Toroidal Magnetic Gravity Inversion", "-269°C Cryogenic Helium Leaks", "510M-Degree Plasma Radiation"],
        "monsters": ["Aether-Touched Plasma Elementals", "Superconducting Frost-Constructs", "Debug-Corrupted Tokamak Drones"],
        "boss": "SOLARIS-ZERO, The Unbound Tokamak Archon (Lv 75 Raid Boss)",
        "resources": ["Star-Core Fusion Cell", "Tungsten-Divertor Greatshield", "Superconducting Copper Coil"],
        "signature_grafts": ["Poloidal Magnetic Spine-Coil"],
        "stationed_companions": [],
        "aliases": ["pppl", "plasma physics", "tokamak", "project matterhorn", "star-core"]
    },
    "lehigh_tunnel_penns_peak": {
        "id": "lehigh_tunnel_penns_peak",
        "name": "Lehigh Tunnel Dual-Bore & Penn's Peak, PA",
        "subtitle": "The Blue Mountain Firewall Gauntlet & High-Timber Mead-Hall",
        "category": "dungeon",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 34.8,
        "bearing_deg": 274,
        "compass_dir": "W",
        "coords": {"x": 16, "y": 48},
        "level_min": 20,
        "level_max": 28,
        "is_safe_zone": False,
        "controlling_faction": "Iron Syndicate (Toll Portal) / Blood Shroud (East Bore) / Vanguard (Penn's Peak)",
        "real_world_lore": "The 4,379-foot-long dual-bore highway tunnel carrying I-476 (PA Turnpike NE Extension) straight through Blue Mountain (1957 East Tube & 1991 NATM West Tube), flanked by the 1,400-ft mountaintop timber hall of Penn's Peak overlooking Beltzville Lake.",
        "system_merge_lore": "Mandatory ground passage piercing the Blue Mountain Sector Firewall: the 1957 East Bore ('The Corpse-Tube') is a mile-long pileup rigged with Blood Shroud tripwires; the 1991 West Bore is a howling Sonic Wind-Tunnel patrolled by Turnpike Enforcer Unit 476-N. Above the exit, Penn's Peak is a Berserker/Goliath Raid Mead-Hall.",
        "special_mechanics": "Looted Turnpike E-ZPass Transponder Keys allow free fast-travel through System Toll Gates; Penn's Peak Highland Mead grants +20 Max HP & +2 STR for 2 hours.",
        "ambient_effects": ["Overpressure Ventilation Wind-Tunnel", "Dark Tunnel Tripwire Hazard"],
        "monsters": ["Blood Shroud PK Toll-Roaders", "Turnpike Toll-Plaza Golems"],
        "boss": "TURNPIKE ENFORCER UNIT 476-N (Lv 30 Sector Gatekeeper)",
        "resources": ["Turnpike E-ZPass Transponder Key", "NATM Shotcrete Plates", "Penn's Peak Highland Mead"],
        "signature_grafts": [],
        "stationed_companions": [],
        "aliases": ["lehigh tunnel", "penn's peak", "turnpike tunnel", "blue mountain tunnel"]
    },
    "tobyhanna_army_depot": {
        "id": "tobyhanna_army_depot",
        "name": "Tobyhanna Army Depot (C4ISR Citadel), PA",
        "subtitle": "The Omniscient Radome & Anechoic Null-Vaults",
        "category": "dungeon",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 38.1,
        "bearing_deg": 322,
        "compass_dir": "NW",
        "coords": {"x": 22, "y": 20},
        "level_min": 28,
        "level_max": 38,
        "is_safe_zone": False,
        "controlling_faction": "Autonomous Cardinal Defense Subroutines",
        "real_world_lore": "1,300-acre DoD C4ISR electronics, radar, avionics, and electro-optical repair installation atop the 2,000-ft Pocono plateau along Powder Smoke Ridge, housing giant radomes, counter-mortar radar arrays, and foam-pyramid Anechoic Chambers.",
        "system_merge_lore": "Tobyhanna's satellite dishes locked directly onto the Cardinal System's orbital telemetry stream, enclosing the 1,300-acre depot in an electromagnetic dome. Powder Smoke Ridge is swept every 60 seconds by a High-Energy Aether-Radar Pulse, while interior pyramid-lined Anechoic Vaults mute all sound and verbal magic.",
        "special_mechanics": "Radar Sweep tags exposed players with [TARGET LOCKED] (-4 AC & counter-mortar barrage); drops TYAD Counter-Fire Radar Spine (boosting Ren's [REN OVERWATCH] accuracy bonus from +2 to +4!).",
        "ambient_effects": ["60-Second High-Energy Radar Sweep", "Anechoic Dead-Air Silence"],
        "monsters": ["C4ISR Watch-Hounds (Lv 29)", "Debug-Corrupted Signal Wraiths (Lv 32)", "Anechoic Stalkers (Lv 34)"],
        "boss": "ARCHON-TYAD: The Omniscient Radome (Lv 38)",
        "resources": ["Military-Spec Micro-Capacitors", "Gold-Plated Waveguides", "Encrypted Argus Admin Badges", "Anechoic Baffle-Plates"],
        "signature_grafts": ["TYAD Counter-Fire Radar Spine", "Aether-Resonant Ocular", "Neural Overclock Cortex"],
        "stationed_companions": [],
        "aliases": ["tobyhanna", "tyad", "tobyhanna army depot", "powder smoke ridge", "signal-core citadel"]
    },
    "manhattan_monolith_track61": {
        "id": "manhattan_monolith_track61",
        "name": "The Manhattan Crystalline Monolith & Grand Central Track 61, NY",
        "subtitle": "Sector 0 End-Game Spire, Hudson Firewall & Subway Undercity",
        "category": "dungeon",
        "quadrant": "North & East (25-100 mi)",
        "distance_miles": 48.0,
        "bearing_deg": 90,
        "compass_dir": "E",
        "coords": {"x": 92, "y": 50},
        "level_min": 25,
        "level_max": 35,
        "is_safe_zone": False,
        "controlling_faction": "The Core Apostles & Archon-Director Vance (Blockaded by Vanguard)",
        "real_world_lore": "Midtown Manhattan skyscrapers anchored in 450-million-year-old Manhattan Schist above the 665-mile NYC Subway system and Grand Central Terminal (1913)—featuring its inverted Zodiac ceiling, FDR's secret armored Track 61 beneath the Waldorf-Astoria, the WWII M42 rotary power converter sub-basement, and the 180-ft-deep LIRR schist cavern.",
        "system_merge_lore": "Isolated behind a 1,000-ft crimson Hudson Firewall (bypassable via Boss Key, Admin Badge, or Cartography 100 PATH tunnels). Midtown skyscrapers fused into a mile-high Crystalline Data-Monolith, while Grand Central descends 180 ft into the Abyssal Undercity where spectral Redbird trains barrel down 600V third-rail loops.",
        "special_mechanics": "Grand Central's Zodiac Ceiling rotates elemental buffs across the 44 platforms; M42 Rotary Dynamo Heart graft boosts max class resource (Poise/Flux/Heat) by +50%.",
        "ambient_effects": ["Hudson Firewall Radiation", "600V Third-Rail Arc Discharge", "Zodiac Astral Matrix"],
        "monsters": ["Third-Rail Arc-Centipedes (Lv 25)", "Schist-Carapace Gargoyle Executives (Lv 27)", "The M42 Rotary Automaton (Lv 28)"],
        "boss": "The Leviathan of Track 61 ('The Iron Express', Lv 30) & Archon-Director Vance (Lv 35)",
        "resources": ["Manhattan Garniferous Schist (Grade 6 Mythic)", "600V Third-Rail Copper Busbars", "Monolith Data-Crystal Shards", "Pre-Collapse Sovereign Bearer Bonds"],
        "signature_grafts": ["M42 Rotary Dynamo Heart", "Subway Tunnel-Vision Night-Optics"],
        "stationed_companions": [],
        "aliases": ["manhattan", "nyc", "crystalline monolith", "grand central", "track 61", "subway undercity"]
    },
    "crystal_cave_indian_echo": {
        "id": "crystal_cave_indian_echo",
        "name": "Crystal Cave (Kutztown) & Indian Echo Caverns (Swatara), PA",
        "subtitle": "The Aragonite Prism-Labyrinth & The Pennsylvania Hermit's Scriptorium",
        "category": "dungeon",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 46.5,
        "bearing_deg": 250,
        "compass_dir": "WSW",
        "coords": {"x": 10, "y": 64},
        "level_min": 18,
        "level_max": 42,
        "is_safe_zone": False,
        "controlling_faction": "The Arcane Conclave (Crystal Cave) & Susquehannock Spirit-Wardens (Indian Echo)",
        "real_world_lore": "Crystal Cave (discovered 1871 near Kutztown) is PA's oldest show cave, famed for sparkling milky-white aragonite formations. Indian Echo Caverns on Swatara Creek was home for 19 years (1802–1821) to Pennsylvania Dutch mystic and philosopher Amos Wilson ('The Pennsylvania Hermit').",
        "system_merge_lore": "In Crystal Cave, every monster has the Crystalline mutation (2.0x DEF) and milky aragonite walls split any spell or MageTech caster beam into a 50% Prismatic Ricochet. Deep in Indian Echo Caverns, the immortal data-ghost of Hermit Amos Wilson tends an Ancient Grimoire Press.",
        "special_mechanics": "Prismatic Ricochet splits beams/spells to hit an extra random target for 50% DMG; solving Amos Wilson's 3 philosophical riddles awards a Scroll of Harmonization (permanently reducing one Golem-Graft's Strain by -3!).",
        "ambient_effects": ["Aragonite Prismatic Beam Ricochet", "Hermit's Scriptorium Serenity"],
        "monsters": ["Crystalline Cave Bears", "Aragonite Shrieker Bats (Sonic DMG)", "Swatara Blind Cave-Hydras"],
        "boss": "Prismatic Stalactite Golem (Lv 25) / Amos Wilson's Riddle Trial",
        "resources": ["Prismatic Aragonite Lenses", "Scroll of Harmonization (-3 Graft Strain)", "Hermit's Ink of Unbinding"],
        "signature_grafts": [],
        "stationed_companions": [],
        "aliases": ["crystal cave", "kutztown cave", "indian echo caverns", "amos wilson", "pennsylvania hermit"]
    },
    "sandy_hook_fort_hancock": {
        "id": "sandy_hook_fort_hancock",
        "name": "Sandy Hook Proving Ground (Fort Hancock & Nike Silo NY-56), NJ",
        "subtitle": "The Disappearing Gun Peninsula & Nuclear-Aether Silo",
        "category": "dungeon",
        "quadrant": "North & East (25-100 mi)",
        "distance_miles": 55.2,
        "bearing_deg": 111,
        "compass_dir": "ESE",
        "coords": {"x": 90, "y": 64},
        "level_min": 13,
        "level_max": 18,
        "is_safe_zone": False,
        "controlling_faction": "Vanguard Coastal Watch (1764 Lighthouse) vs. Automated Artillery Batteries",
        "real_world_lore": "6-mile barrier spit at the entrance to NY Harbor housing America's oldest working lighthouse (1764), the US Army Sandy Hook Proving Ground, Endicott-era concrete disappearing gun batteries (Battery Potter, Battery Gunnison, Nine-Gun Battery), and Cold War underground Nike Hercules nuclear missile silos (Site NY-56).",
        "system_merge_lore": "A 6-mile linear gauntlet where 12-inch coastal rifles rise on steam-hydraulic counterweights above concrete parapets every 3 rounds to bombard approaching parties before dropping back into total cover. Underground hydraulic elevators descend into the 3-sublevel Nike Hercules Silo Dungeon.",
        "special_mechanics": "3-Round Disappearing Gun Telegraph; Blue Horseshoe Crab Hemocyanin stabilizes Cyber-Strain.",
        "ambient_effects": ["12-Inch Disappearing Gun Bombardment", "1764 Lighthouse Safe-Beacon (Northern Tip)"],
        "monsters": ["Proving-Ground Shrapnel Golems (Lv 14)", "Holly-Thicket Horseshoe Stalkers (Lv 13)", "Endicott Steam-Loader Automatons (Lv 15)"],
        "boss": "HERCULES-W31, The Nuclear-Aether Seraph (Lv 18 Silo Elevator Boss)",
        "resources": ["Proving Ground Krupp-Armor Plate", "Blue Horseshoe Crab Hemocyanin", "Battery Potter Steam-Valve", "Nike Solid-Fuel Booster Core"],
        "signature_grafts": ["Endicott Counterweight Shoulder-Mount"],
        "stationed_companions": [],
        "aliases": ["sandy hook", "fort hancock", "battery potter", "battery gunnison", "nike silo"]
    },
    "eastern_state_penitentiary": {
        "id": "eastern_state_penitentiary",
        "name": "Eastern State Penitentiary (Philadelphia), PA",
        "subtitle": "The Panopticon Soul-Cage & Sutton's Escape Tunnel",
        "category": "dungeon",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 55.5,
        "bearing_deg": 191,
        "compass_dir": "SSW",
        "coords": {"x": 36, "y": 88},
        "level_min": 40,
        "level_max": 58,
        "is_safe_zone": False,
        "controlling_faction": "Warden Haviland's Panopticon Subroutine (Blood Shroud Covert Entrance)",
        "real_world_lore": "Opened in 1829 in Philadelphia with 30-foot neo-Gothic granite walls and John Haviland's pioneering Radial 'Wagon-Wheel' Plan (7+ vaulted stone cellblocks radiating from a Central Rotunda, each cell lit by a single 'Eye of God' skylight); held Al Capone (Cellblock 8 luxury cell) and Willie Sutton (1945 97-ft escape tunnel).",
        "system_merge_lore": "Merged with the Cardinal System's PK Detention Subroutine. A multi-faceted Panopticon Ocular Construct in the Central Rotunda sweeps a crimson searchlight down each radial cellblock in sequence. Players duck into vaulted cells, flank between spokes via Willie Sutton's 97-ft Escape Tunnel, and rest inside Al Capone's jazz-playing Cellblock 8 Outlaw Shrine.",
        "special_mechanics": "Rotunda Searchlight Sweep inflicts 'Solitary Penance' (Silenced, Rooted & opens all cell doors on the block); Hooded Penitents are blind and aggro strictly on sound/chat.",
        "ambient_effects": ["Panopticon Crimson Searchlight Sweep", "Cellblock 8 1929 Jazz Static (Safe Room)"],
        "monsters": ["Hooded Penitents (Sound-Aggro Specters)", "Iron-Gag Wardens"],
        "boss": "WARDEN HAVILAND'S PANOPTICON EYE (Lv 58 Central Rotunda Boss)",
        "resources": ["Key of the Fifteen Spokes", "Capone's Silk-Lined Trenchcoat", "Solitary Penance Chains"],
        "signature_grafts": ["Aether-Resonant Ocular (Eye of the Rotunda Variant)"],
        "stationed_companions": [],
        "aliases": ["eastern state", "penitentiary", "panopticon", "al capone cell", "willie sutton"]
    },
    "archbald_pothole_concrete_city": {
        "id": "archbald_pothole_concrete_city",
        "name": "The Archbald Pothole & Concrete City (Nanticoke), PA",
        "subtitle": "The 1,200-Foot Glacial Whirlpool Shaft & Brutalist Construct Kill-Box",
        "category": "dungeon",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 60.3,
        "bearing_deg": 315,
        "compass_dir": "NW",
        "coords": {"x": 14, "y": 10},
        "level_min": 26,
        "level_max": 36,
        "is_safe_zone": False,
        "controlling_faction": "The Unbound Foundry (Rogue Sentient Golems)",
        "real_world_lore": "Archbald Pothole was drilled 15,000 years ago by a glacial waterfall whirlpool and discovered from the bottom up in 1884 when miners blasted into the Archbald Coal Seam and 1,000 tons of rounded river cobbles roared out of the ceiling. Concrete City (1911, Nanticoke) is a ring of 22 poured cinder-concrete double houses that survived 100 sticks of dynamite in 1924.",
        "system_merge_lore": "The Archbald Pothole's false bottom is gone, plunging 1,200 ft through an anti-gravity cyclone of orbiting 5-ton glacial 'Grinder' boulders into the Northern Underdark. At Concrete City, the 22 dynamite-proof concrete husks form an urban CQB kill-box where rogue Warforged cast new bodies in the flooded central swimming pool.",
        "special_mechanics": "Archbald Grinder Vortex requires timing ledges between 5-ton boulder orbits (DC 16 Athletics); Concrete City's 1911 Blast-Proof Cinder-Crete upgrades Homestead Subsurface Vaults.",
        "ambient_effects": ["Anti-Gravity Glacial Grinder Cyclone", "Indestructible Cinder-Crete Walls"],
        "monsters": ["Glacial-Rimed Gyro-Elementals", "Cinder-Crete Gargoyles (Lv 27)", "Pool-Sludge Cement Oozes (Petrifying Encasement)"],
        "boss": "DL&W Foreman Construct-Lord (Lv 32) & Cryo-Crystalline Remorhaz (Lv 36)",
        "resources": ["15,000-Year Glacial Grinder Cores (+25% Hammer Break-Gauge)", "1911 Blast-Proof Cinder-Crete Cores", "SWAT Breaching Rams"],
        "signature_grafts": ["Monolithic Cinder-Carapace Plating (+3 AC, DR 3)"],
        "stationed_companions": [],
        "aliases": ["archbald pothole", "concrete city", "nanticoke", "grinder vortex"]
    },
    "lakehurst_airship_hangar": {
        "id": "lakehurst_airship_hangar",
        "name": "Lakehurst Naval Air Station (Hangar No. 1), NJ",
        "subtitle": "The Cathedral of the Sky-Titans & Hindenburg Phlogiston Revenant",
        "category": "dungeon",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 61.0,
        "bearing_deg": 145,
        "compass_dir": "SE",
        "coords": {"x": 76, "y": 84},
        "level_min": 50,
        "level_max": 70,
        "is_safe_zone": False,
        "controlling_faction": "Vanguard Aerial Siege Camp (Western Runway)",
        "real_world_lore": "Built in 1921 to house rigid naval airships (USS Shenandoah, Akron, Macon), Hangar No. 1 is a 966×350×224-foot steel cathedral with 1,350-ton doors riding on railroad tracks, jet steam-catapult test tracks, and the outdoor granite-and-chain monument where the 804-ft zeppelin LZ 129 Hindenburg burned on May 6, 1937.",
        "system_merge_lore": "Hangar No. 1 is so colossal it generates its own indoor thunderclouds beneath the 224-ft roof trusses where the blueprints of the USS Akron have fused with a biological storm-whale. Outside on the sandy mooring circle at 19:25 nightly, the Burning Duralumin Behemoth (LZ-129 Revenant) materializes in hydrogen flames.",
        "special_mechanics": "Cranking open the 1,350-ton hangar doors requires an 8-player STR/Engineering check or steam-catapult winch; Duralumin Airship Struts halve weapon/armor weight.",
        "ambient_effects": ["Indoor 224-Foot Rafter Thunderclouds", "19:25 Nightly Phlogiston-Hydrogen Firestorm"],
        "monsters": ["Duralumin Rigging Harpies", "Steam-Catapult Juggernauts (180 mph track charge)"],
        "boss": "LZ-129 Phlogiston Revenant (Lv 64 World Boss) & THE AKRON SKY-LEVIATHAN (Lv 70 Raid Boss)",
        "resources": ["Duralumin Airship Struts (-50% Gear Weight)", "Phlogiston Flame-Sacs", "Steam-Catapult Kinetic Piston"],
        "signature_grafts": ["Spring-Loaded Golem Greaves (Rocket-Catapult Upgrade)"],
        "stationed_companions": [],
        "aliases": ["lakehurst", "hangar no. 1", "hindenburg", "sky-leviathan", "akron"]
    },
    "philly_navy_yard_fort_mifflin": {
        "id": "philly_navy_yard_fort_mifflin",
        "name": "Philadelphia Navy Yard ('Ghost Fleet') & Fort Mifflin, PA",
        "subtitle": "The Fused Mothball Armada & 1777 Mud Island Siege Loop",
        "category": "dungeon",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 61.5,
        "bearing_deg": 190,
        "compass_dir": "SSW",
        "coords": {"x": 34, "y": 92},
        "level_min": 38,
        "level_max": 72,
        "is_safe_zone": False,
        "controlling_faction": "Iron Syndicate Salvage Fleet (Drydock #1) / Contested Armada",
        "real_world_lore": "League Island at the Delaware-Schuylkill confluence houses America's first naval shipyard (350-ton Hammerhead Crane and the Reserve Basin 'Mothball Ghost Fleet' of decommissioned carriers, cruisers, and destroyers). 1.5 miles west sits Fort Mifflin on Mud Island (endured 10,000 British shells in Nov 1777; rebuilt 1798 with bomb-proof brick casemates).",
        "system_merge_lore": "Twelve mothballed destroyers, cruisers, and a supercarrier in the Reserve Basin have physically welded together via barnacle bulkheads and anchor-chain tendons into a floating Steel Continent. Across the river channel, Fort Mifflin runs a 6-hour 1777 Chrono-Siege bombardment loop against spectral 64-gun ships-of-the-line.",
        "special_mechanics": "Harvests Pre-Atomic 'Low-Background' Battleship Steel from pre-1945 hulls (100% immune to Debug-Corruption and Arcane interference!); Fort Mifflin's Broadside Bell requires ducking into 1798 Bomb-Proof Casemates.",
        "ambient_effects": ["350-Ton Hammerhead Crane Sweep", "1777 Spectral Broadside Bombardment"],
        "monsters": ["Barnacle-Welded Deck Marines", "Depth-Charge Crab Behemoths", "Casemate 11 Screaming Wraiths"],
        "boss": "CARRIER-LEVIATHAN CV-00 'THE MOTHBALL DREADNOUGHT' (Lv 72) & HMS Augusta Phantom Man-o'-War (Lv 54)",
        "resources": ["Pre-Atomic Low-Background Battleship Steel", "35-lb Dreadnought Anchor Links", "Montresor's Star-Fort Blueprint"],
        "signature_grafts": ["Casemate Bomb-Proof Pauldrons"],
        "stationed_companions": [],
        "aliases": ["navy yard", "ghost fleet", "mothball fleet", "fort mifflin", "mud island", "league island"]
    },
    "camp_evans_sams_point": {
        "id": "camp_evans_sams_point",
        "name": "Camp Evans Radar Bunkers (NJ) & Sam's Point Ice Caves (NY)",
        "subtitle": "The 1946 Project Diana Lunar-Echo Array & Permafrost Fault Crevices",
        "category": "dungeon",
        "quadrant": "North & East (25-100 mi)",
        "distance_miles": 66.0,
        "bearing_deg": 78,
        "compass_dir": "ENE",
        "coords": {"x": 82, "y": 28},
        "level_min": 13,
        "level_max": 19,
        "is_safe_zone": False,
        "controlling_faction": "The Arcane Conclave & Green Wardens vs. Core Apostle Hackers",
        "real_world_lore": "Camp Evans (Wall Twp, NJ) is the 1914 Marconi wireless station, WWII US Army Signal Corps radar bunker complex, and site of 1946 Project Diana (first radar wave bounced off the Moon, returning in 2.5 seconds). Sam's Point (Shawangunk Ridge, NY) features deep tectonic quartz crevice caves that trap glacial ice year-round beside 187-ft Verkeerderkill Falls.",
        "system_merge_lore": "Camp Evans' Project Diana radar array remains locked onto the Moon (Cardinal's orbital backup server), triggering a 2.5-Second Lunar Echo during night battles. At Sam's Point, the narrow quartz crevices plunge to -40°F (-Glitch Freeze) with a secret boss cavern behind the frozen cascade of Verkeerderkill Falls.",
        "special_mechanics": "The 2.5-Second Lunar Echo repeats 50% of every spell, Sword Skill, or ranged attack 1 round later at the exact coordinates cast; Sam's Point requires thermal insulation (like Dire-Wolf Fur Mantle) or Trench Hammers to smash ice choke-points.",
        "ambient_effects": ["2.5-Second Lunar Radar Echo", "-40°F Permafrost Crevice Chill"],
        "monsters": ["Signal-Corps Oscilloscope Wraiths (Lv 15)", "Ionosphere Moon-Hounds (Lv 16)", "Giant Stygobromus Ice-Amphipods (Lv 14)", "Hoarfrost Quartz Wendigos (Lv 16)"],
        "boss": "Arch-Signaler Diana-1946 (Lv 19) & Rimestalker Kaelen, The Pleistocene Remnant (Lv 18)",
        "resources": ["Project Diana Vacuum Magnetron", "Unmelting Ellenville Fault Ice", "Sam's Point Wild Huckleberry Elixir"],
        "signature_grafts": ["Project Diana Doppler-Radar Eye (60-ft Blindsight)", "Pleistocene Cryo-Vent Carapace"],
        "stationed_companions": [],
        "aliases": ["camp evans", "infoage", "project diana", "sam's point", "ice caves", "verkeerderkill"]
    },
    "bannermans_castle_nuclear_glitches": {
        "id": "bannermans_castle_nuclear_glitches",
        "name": "Bannerman's Island Arsenal & The Nuclear/Collider Glitch-Citadels (Limerick, Oyster Creek, TMI & Brookhaven)",
        "subtitle": "The 1920 Munitions Loop, Cherenkov Cooling Towers & 2.4-Mile RHIC Collider",
        "category": "dungeon",
        "quadrant": "North & East (25-100 mi)",
        "distance_miles": 70.5,
        "bearing_deg": 47,
        "compass_dir": "NE",
        "coords": {"x": 88, "y": 22},
        "level_min": 14,
        "level_max": 90,
        "is_safe_zone": False,
        "controlling_faction": "Contested Anomaly / Core Apostles Quarantine",
        "real_world_lore": "Pollepel Island's 1900 Scottish castle arsenal where 200 tons of shells exploded in 1920; paired with the regional nuclear/particle megastructures: Limerick (twin 507-ft towers, 49 mi SW), Oyster Creek (1969 Mark-I BWR & warm discharge canal, 77 mi SE), Three Mile Island (4 towers & 1979 Unit 2 meltdown, 100 mi WSW), and Brookhaven National Lab's 2.4-mile RHIC gold-ion collider (109 mi E).",
        "system_merge_lore": "Bannerman's Castle is locked in the 1920 Explosion loop with a 0–100% Ordnance Volatility Meter per room. At Limerick, Oyster Creek, TMI, and Brookhaven's 2.4-mile Ouroboros Collider ring, nuclear fission and relativistic gold-ion beams caused division-by-zero errors—tearing reality into neon-green wireframe polygons, blue Cherenkov mana-fire, and 4-trillion-degree Quark-Gluon Plasma.",
        "special_mechanics": "Bannerman's Ordnance Volatility Meter detonates rooms at 100% (6d10 blast); Brookhaven's 2.4-mile RHIC tunnel fires a near-lightspeed Gold-Ion Pulse every 5 rounds (15d10 Radiant/Force unless in shielded alcoves).",
        "ambient_effects": ["Ordnance Volatility Gauge (0-100%)", "Cherenkov Wireframe Glitch-Radiation", "Relativistic Gold-Ion Ring Pulse"],
        "monsters": ["Cordite-Geist Grenadiers (Lv 15)", "Debug-Corrupted Reactor Enforcers", "Cherenkov Blue-Glow Elementals", "Quark-Gluon Plasma Anomalies"],
        "boss": "Commissar-General Bannerman's Effigy (Lv 19), Aureus-QGP (Lv 30 Brookhaven), & Unit-2 Corium Amalgam (Lv 90 TMI)",
        "resources": ["Bannerman's Unstable Aether-Cordite", "Zircaloy Cladding Rods", "Vitrified Cherenkov Shards", "Relativistic Gold-Ion Core (Grade 7 Mythic)"],
        "signature_grafts": ["Recoil-Dampening Artillery Elbow", "RHIC Superconducting Dipole Spine"],
        "stationed_companions": [],
        "aliases": ["bannerman's castle", "pollepel island", "limerick", "oyster creek", "three mile island", "brookhaven", "rhic"]
    },

    # =========================================================================
    # CATEGORY IV: WILDERNESS AREAS (GRIND ZONES), ANOMALIES & SLIPSTREAMS (21 ZONES)
    # =========================================================================
    "morris_canal_slipstreams": {
        "id": "morris_canal_slipstreams",
        "name": "Morris Canal Inclined Planes & Lock Network, NJ",
        "subtitle": "The Gravitational Aether-Slipstreams & Cradle-Rail Artery",
        "category": "wilderness",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 0.5,
        "bearing_deg": 90,
        "compass_dir": "E-W Artery",
        "coords": {"x": 51, "y": 50},
        "level_min": 3,
        "level_max": 15,
        "is_safe_zone": False,
        "controlling_faction": "The Iron Syndicate Caravan Network (Contested by Outlaws)",
        "real_world_lore": "Built 1824–1831 from Phillipsburg through Port Colden (0.5 mi east of Washington Borough), Hackettstown, and Waterloo to NY Harbor; climbed 1,674 vertical feet using 23 water-powered Scotch-turbine Inclined Planes that hauled 70-ton hinged canal boats up mountain tracks on 2-inch Roebling wire cables.",
        "system_merge_lore": "Resurrected as a glowing ribbon of Zero-Friction Liquid Aether cutting straight through Washington Borough. The 23 Inclined Planes (starting at Plane 6 West in Port Colden) act as Scotch-Turbine Gravity Slings.",
        "special_mechanics": "Repairing a Plane Tender's Cable Drum (1x Carbon Line Spool + 1x Anchors and Tension Pins) unlocks 3x overland fast-travel speed along the Route 57 corridor; players can escort or ambush Iron Syndicate cargo-cradles.",
        "ambient_effects": ["Zero-Friction Aether Slipstream (3x Speed)", "Scotch-Turbine Cable Tension"],
        "monsters": ["Canal-Prism Bog Lurkers (Lv 4)", "Deranged Plane-Tender Automata (Lv 7)", "Wire-Rope Constrictor Constructs (Lv 10)", "Blood Shroud Train-Wreckers (Lv 12)"],
        "boss": "Overseer Automaton of Plane 6 West (Lv 10)",
        "resources": ["2-Inch Roebling Wire-Rope Coils", "Scotch-Turbine Bronze Impellers", "Plane-Tender Override Keys"],
        "signature_grafts": ["Spring-Loaded Golem Greaves"],
        "stationed_companions": [],
        "aliases": ["morris canal", "inclined plane", "port colden", "port murray", "musconetcong aqueduct", "musconetcong crypts"]
    },
    "pohatcong_roaring_rock_wilds": {
        "id": "pohatcong_roaring_rock_wilds",
        "name": "Pohatcong Mountain & Roaring Rock Park, NJ",
        "subtitle": "Sector 1 Starter Wilderness & Bounty Hunting Grounds",
        "category": "wilderness",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 1.8,
        "bearing_deg": 205,
        "compass_dir": "SSW",
        "coords": {"x": 49, "y": 53},
        "level_min": 1,
        "level_max": 5,
        "is_safe_zone": False,
        "controlling_faction": "Unclaimed Starter Wilderness (Patrolled by Washington Wardens)",
        "real_world_lore": "Steep Precambrian gneiss ridge and 267-acre hemlock boulder gorge off Brass Castle Road where Roaring Rock Brook thunders below the earthen ruins of the Upper Stewartsville Reservoir.",
        "system_merge_lore": "Fiber-optic ley-roots strangle the ancient hemlocks along Roaring Rock Brook. Primary starter hunting, field-trapping, and Warren County Bounty board zone leading to the waterfall portal of The Pohatcong Depths.",
        "special_mechanics": "Canonical hunting zone for Warren County Bounties ('Rogue Timber-Goliath' & 'Alpha Razor-Hound Pack'); prime Field Trapping corridor.",
        "ambient_effects": ["Roaring Brook Mist", "Low-Tier Leyline Saturation"],
        "monsters": ["Frenzy Boars (Lv 1)", "Dire Wolves (Lv 2)", "Nepenthes Pitcher-Plants (Lv 3)", "Rogue Timber-Goliath (Lv 3 Bounty)", "Alpha Razor-Hound Pack (Lv 4 Bounty)"],
        "boss": "Alpha Razor-Hound (Lv 4 Field Boss)",
        "resources": ["Rendered Chimera Marrow", "Hardened Chitin Plates", "Mutated Sinew Cord", "Grade 2 Titanium Plating"],
        "signature_grafts": ["Chimeric Beast Claws"],
        "stationed_companions": ["Morrigan"],
        "aliases": ["roaring rock", "pohatcong mountain", "pohatcong ridge", "brass castle"]
    },
    "jenny_jump_ghost_lake": {
        "id": "jenny_jump_ghost_lake",
        "name": "Jenny Jump State Forest, Ghost Lake & Shades of Death Road, NJ",
        "subtitle": "The Perpetual Runic-Mist Corridor & Phrenic Observatory",
        "category": "wilderness",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 9.8,
        "bearing_deg": 19,
        "compass_dir": "NNE",
        "coords": {"x": 54, "y": 33},
        "level_min": 8,
        "level_max": 16,
        "is_safe_zone": False,
        "controlling_faction": "The Green Wardens (Canopy) vs. Blood Shroud Ambushers (Road)",
        "real_world_lore": "1,100-foot Precambrian gneiss ridge above the black-dirt Great Meadows (drained glacial Lake Pequest); famous for the 6.7-mile Shades of Death Road, Ghost Lake vapor columns, Lenape Fairy Hole Cave, the 1749 Moravian settlement at Hope Township, and the UACNJ summit astronomical observatories.",
        "system_merge_lore": "Shades of Death Road and Ghost Lake are permanently locked in [Runic Mist] weather (-4 Ranged ATK, +3 Stealth). During the Witching Hour (04:00–06:00), road geometry loops unless passing a DC 14 Cartography check. Fairy Hole Cave is a totem-warded safe camp, and the UACNJ summit telescopes grant Phrenic Humans +2 INT/WIS.",
        "special_mechanics": "Permanent [Runic Mist]; UACNJ Observatory grants Phrenic Humans +2 INT/WIS & +20% Psionic Shielding; houses Sariel, Garrick (Pequest Quarry), and Sister Teresa (Hope Moravian Ruins).",
        "ambient_effects": ["Permanent Runic Mist (-4 Ranged ATK, +3 Stealth)", "Witching-Hour Spatial Loop"],
        "monsters": ["Great-Meadows Miasma Swarmers (Lv 8)", "Shades-of-Death Highwayman Wraiths (Lv 11)", "Ghost-Lake Drowned Apparitions (Lv 13)", "Pleistocene Cave-Giant Construct (Lv 15)"],
        "boss": "The Phantom Coachman of Shades of Death (Lv 16)",
        "resources": ["Ectoplasmic Mist-Condensate", "Runic Lichen", "Ancient Lenape Flint-Runes", "Black-Dirt Muckland Truffles"],
        "signature_grafts": [],
        "stationed_companions": ["Sariel", "Garrick", "Teresa"],
        "aliases": ["jenny jump", "ghost lake", "shades of death", "great meadows", "hope township", "pequest", "fairy hole"]
    },
    "hacklebarney_black_river": {
        "id": "hacklebarney_black_river",
        "name": "Hacklebarney State Park & Black River Gorge, NJ",
        "subtitle": "The Iron-Root Ravine & Premier Trapping Defile",
        "category": "wilderness",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 13.3,
        "bearing_deg": 94,
        "compass_dir": "E",
        "coords": {"x": 66, "y": 52},
        "level_min": 8,
        "level_max": 14,
        "is_safe_zone": False,
        "controlling_faction": "The Green Wardens",
        "real_world_lore": "Deep glacial boulder ravine in Chester/Long Valley where the Black River drops through ancient eastern hemlocks beside 18th-century Hacklebarney magnetite cuts and Kay's Forge.",
        "system_merge_lore": "Ancient hemlocks drank directly from the flooded Hacklebarney magnetite veins during Integration, hardening their bark into Metallic Iron-Wood. The narrow boulder-choked defiles between Trout Brook and the Black River funnel monsters into natural kill-zones.",
        "special_mechanics": "Grants a natural +4 Bonus to Field Trapping & Tripwire Snare DCs; Iron-Hemlock Heartwood adds +50 Max Durability to forged axes and hammers.",
        "ambient_effects": ["Narrow Gorge Funnel (+4 Field Trapping DC)", "Iron-Canopy Shade"],
        "monsters": ["Hacklebarney Iron-Bark Treants (Lv 10)", "Elder Acid-Sap Nepenthes Clusters (Lv 9)", "Black-River Magnetite-Shell Crabs (Lv 11)"],
        "boss": "Kay's Forge Rust-Stalker (Lv 14 Elite)",
        "resources": ["Iron-Hemlock Heartwood (+50 Max Durability)", "Salted Rock-Moss", "Wild Aether-Herbs", "Hacklebarney Surface Magnetite"],
        "signature_grafts": [],
        "stationed_companions": [],
        "aliases": ["hacklebarney", "black river gorge", "long valley", "kays forge"]
    },
    "ringing_rocks_boulder_field": {
        "id": "ringing_rocks_boulder_field",
        "name": "Ringing Rocks Park (Upper Black Eddy), PA",
        "subtitle": "The Bell-Stone Ultrasonic Resonance Field",
        "category": "wilderness",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 15.7,
        "bearing_deg": 210,
        "compass_dir": "SSW",
        "coords": {"x": 38, "y": 68},
        "level_min": 10,
        "level_max": 16,
        "is_safe_zone": False,
        "controlling_faction": "Harmonic Lithic Constructs",
        "real_world_lore": "Surreal 7-acre treeless post-glacial boulder field (felsenmeer) atop Coffman Hill in Bucks County, PA where dense igneous diabase boulders locked under internal elastic stress ring like hollow cast-iron church bells and emit ultrasonic frequencies when struck with a hammer.",
        "system_merge_lore": "Amplified into a Live Acoustic Minefield: stepping onto the bare boulders in heavy metal armor or missing a melee swing strikes the stones, triggering a 20-ft Ultrasonic Bell-Shockwave (2d6 Thunder/Sonic DMG—extra hazardous for Phrenic Humans with Sensory Overload!).",
        "special_mechanics": "Wielding a Warhammer/Trench Hammer and passing a DC 15 INT/Resonance check strikes a 5-boulder harmonic chord—shattering a boulder to harvest Acoustic-Tempered Diabase Cores and Resonator Tuning Prisms!",
        "ambient_effects": ["Ultrasonic Bell-Stone Resonance (2d6 Sonic on Missed Swings)", "Zero-Cover Felsenmeer"],
        "monsters": ["Ultrasonic Diabase Skitterers (Lv 11)", "Bell-Stone Resonance Golems (Lv 14)", "High-Falls Mist Siren (Lv 15)"],
        "boss": "The Octave Lith-Archon (Lv 16)",
        "resources": ["Acoustic-Tempered Diabase Ore (+1d6 Thunder/Sonic Weapon Mod)", "Resonator Tuning Prism", "Ultrasonic Quartz Nodes"],
        "signature_grafts": ["Basalt Carapace Plating"],
        "stationed_companions": [],
        "aliases": ["ringing rocks", "upper black eddy", "bell-stone"]
    },
    "delaware_water_gap_sunfish": {
        "id": "delaware_water_gap_sunfish",
        "name": "Delaware Water Gap (Mt. Tammany, Mt. Minsi & Sunfish Pond)",
        "subtitle": "The Sector 1–2 World-Gate Chasm & Glacial Cleansing Tarn",
        "category": "wilderness",
        "quadrant": "Inner Core (0-25 mi)",
        "distance_miles": 16.5,
        "bearing_deg": 333,
        "compass_dir": "NNW",
        "coords": {"x": 32, "y": 30},
        "level_min": 14,
        "level_max": 22,
        "is_safe_zone": False,
        "controlling_faction": "Vanguard Gate-Keepers & Green Wardens",
        "real_world_lore": "The Delaware River cuts a 1,200-foot S-curve chasm through the Silurian Shawangunk Quartzite of the Kittatinny Ridge between Mt. Tammany (1,526 ft, NJ) and Mt. Minsi (1,463 ft, PA). 4 miles NE along the Appalachian Trail sits pristine glacial Sunfish Pond (1,382 ft) and the 1650s Dutch Pahaquarry Copper Mine.",
        "system_merge_lore": "Mt. Tammany and Mt. Minsi form the natural gateposts of the 1,200-ft Sector 1 Northern Firewall (unsealed by defeating the Pohatcong Overlord). On the ridge crest, the pristine glacial waters of Sunfish Pond are untouched by System corruption. Companion Nyssa Thorn-Weft guards the Water Gap wolf dens.",
        "special_mechanics": "Bathing or drinking from Sunfish Pond grants [Glacial Purity]: permanently reduces Graft Strain by -5 points (preventing System Rejection!) and cleanses all glitch/corruption debuffs.",
        "ambient_effects": ["Gorge Wind-Shear", "Sunfish Tarn Glacial Purity (-5 Graft Strain)"],
        "monsters": ["Shawangunk Quartz-Crag Gargoyles (Lv 15)", "Kittatinny Ridge Razor-Bears (Lv 17)", "Water-Gap Storm-Roc Wyverns (Lv 19)", "Pahaquarry Copper-Vein Construct (Lv 21)"],
        "boss": "Apex Storm-Roc of Mount Tammany (Lv 22)",
        "resources": ["Pure Glacial Tarn-Water", "Shawangunk White-Quartz Crystals", "Pahaquarry Green-Malachite & Native Copper"],
        "signature_grafts": [],
        "stationed_companions": ["Nyssa"],
        "aliases": ["delaware water gap", "mt. tammany", "mount tammany", "mt. minsi", "sunfish pond", "pahaquarry"]
    },
    "sourland_mountain_devils_acre": {
        "id": "sourland_mountain_devils_acre",
        "name": "Sourland Mountain Preserve & Devil's Half-Acre, NJ",
        "subtitle": "The Roaring Megalith Maze & Knitting Betty's Web",
        "category": "wilderness",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 25.0,
        "bearing_deg": 144,
        "compass_dir": "SSE",
        "coords": {"x": 60, "y": 72},
        "level_min": 22,
        "level_max": 36,
        "is_safe_zone": False,
        "controlling_faction": "Vanguard / Arcane Conclave Borderland (Blood Shroud in John Hart Cave)",
        "real_world_lore": "17-mile Jurassic diabase sill ridge featuring 'Roaring Rocks' (where mountain brooks rush invisibly beneath hollow boulder piles), 'Devil's Half-Acre', 'The Three Brothers' boulders, 'Knitting Betty's Rock', and John Hart's Revolutionary War hideout cave.",
        "system_merge_lore": "Gateway grind zone between Warren/Hunterdon and Princeton. Subterranean brooks roar through hollow Under-Boulder Echo Caverns beneath the diabase megaliths; at night, The Three Petrified Brothers awaken as linked Menhir Golems while Knitting Betty's Weaver-Spiders string invisible Aether-Silk tripwires across boulder gaps.",
        "special_mechanics": "Harvests Sourland Diabase Slabs (for Basalt Carapace Plating) and Aether-Silk Gossamer Spools (elite Field Trapping snares).",
        "ambient_effects": ["Under-Boulder Subterranean Roar", "Invisible Gossamer Tripwires"],
        "monsters": ["Crystalline Diabase Gargoyles", "Sourland Devil-Hounds", "Knitting Betty's Weaver-Spiders"],
        "boss": "The Three Petrified Brothers (Linked Menhir Golem Trio, Lv 36)",
        "resources": ["Sourland Trap-Rock (Diabase) Slabs", "Aether-Silk Gossamer Spools", "Subterranean Roaring-Spring Water"],
        "signature_grafts": ["Basalt Carapace Plating"],
        "stationed_companions": [],
        "aliases": ["sourland", "sourland mountain", "devil's half-acre", "roaring rocks", "knitting betty"]
    },
    "bushkill_promised_land": {
        "id": "bushkill_promised_land",
        "name": "Bushkill Falls & Promised Land State Park, PA",
        "subtitle": "The Eight-Bridge Gorge & Beast-Kin Proving Grounds",
        "category": "wilderness",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 25.0,
        "bearing_deg": 356,
        "compass_dir": "N",
        "coords": {"x": 42, "y": 18},
        "level_min": 12,
        "level_max": 30,
        "is_safe_zone": False,
        "controlling_faction": "The Green Wardens & Autonomous Beast-Kin / Lycan Clans",
        "real_world_lore": "Bushkill Falls ('Niagara of PA') features 8 waterfalls connected by wooden canyon bridges; Promised Land State Park sits at 1,800 ft on the glacial Pocono Plateau around Promised Land Lake and Conservation Island.",
        "system_merge_lore": "Bushkill's suspension bridges are held by Tengu Bridge-Bandits who mimic player voice callouts to lure parties onto trapped spans. At Promised Land Lake, Midnight/Witching Hour triggers [The Wild Hunt], doubling monster density and XP while guaranteeing Apex Dire-Beast spawns.",
        "special_mechanics": "Premier Field Trapping (Mastery 100–250) bridge-rigging zone; [The Wild Hunt] nocturnal 2x XP & Apex Beast event.",
        "ambient_effects": ["Canyon Waterfall Mist", "Nocturnal Wild Hunt Blood-Moon (2x XP at Night)"],
        "monsters": ["Bushkill Tengu Snipers (Voice Mimicry)", "Aether-Touched Dire Bears", "Crystalline Stag-Lords"],
        "boss": "Glacial-Lake Bog-Kraken of Conservation Island (Lv 30)",
        "resources": ["Dire-Bear Pelts", "Prime Wolf Marrow-Jars", "Tengu Feather-Charms", "Glacial Lake Bog-Iron"],
        "signature_grafts": ["Chimeric Beast Claws", "Ursine Hydraulic Tendon-Weave"],
        "stationed_companions": [],
        "aliases": ["bushkill falls", "promised land", "conservation island"]
    },
    "great_swamp_stirling_fen": {
        "id": "great_swamp_stirling_fen",
        "name": "The Great Swamp & Lord Stirling Fen, NJ",
        "subtitle": "The Miasmic Caldera of Prehistoric Lake Passaic",
        "category": "wilderness",
        "quadrant": "North & East (25-100 mi)",
        "distance_miles": 27.0,
        "bearing_deg": 97,
        "compass_dir": "E",
        "coords": {"x": 75, "y": 54},
        "level_min": 5,
        "level_max": 10,
        "is_safe_zone": False,
        "controlling_faction": "The Green Wardens (Lord Stirling Outpost)",
        "real_world_lore": "7,800-acre low-lying remnant bottom of prehistoric Glacial Lake Passaic cradled inside the Watchung basalt ridges; traversed by wooden boardwalks through peat bogs, blackwater brooks, copperhead dens, and carnivorous pitcher plants.",
        "system_merge_lore": "Blanketed in glowing green Runic Mist 70% of the time. Stepping off the elevated wooden boardwalks into the blackwater peat bogs subjects Heavy Load characters to Mire Encumbrance and peat-quicksand (DC 13 STR). Primary harvesting zone for Bioluminescent Bog-Mycelium.",
        "special_mechanics": "Boardwalk Mire Quicksand hazard; Lord Stirling Outpost teaches Mycelial Grafting and Field Trapping milestones.",
        "ambient_effects": ["Dense Runic Mist", "Peat-Quicksand Mire Encumbrance"],
        "monsters": ["Glacial Fen Nepenthes (Lv 5–7)", "Lord Stirling Copperhead Wyrms (Lv 7)", "Alligator-Snapper Behemoths (Lv 9)"],
        "boss": "The Jetport Phantom / Bog-Titan of Black Brook (Lv 11)",
        "resources": ["Bioluminescent Bog-Mycelium", "Nepenthes Acid-Sap Sacs", "Copperhead Venom Glands", "Passaic Bog-Iron Nodules"],
        "signature_grafts": ["Nepenthes Acid-Gland Splice (-2 Enemy AC on hit)"],
        "stationed_companions": [],
        "aliases": ["great swamp", "lord stirling", "basking ridge fen", "lake passaic"]
    },
    "watchung_feltville_ghost_town": {
        "id": "watchung_feltville_ghost_town",
        "name": "Watchung Reservation & Deserted Village of Feltville, NJ",
        "subtitle": "The 1845 Ghost-Mill & Nocturnal Coven Instance",
        "category": "wilderness",
        "quadrant": "North & East (25-100 mi)",
        "distance_miles": 31.5,
        "bearing_deg": 100,
        "compass_dir": "E",
        "coords": {"x": 79, "y": 55},
        "level_min": 7,
        "level_max": 13,
        "is_safe_zone": False,
        "controlling_faction": "Daytime Outlaw/Halfling Smugglers / Nighttime Glenside Coven",
        "real_world_lore": "2,142-acre preserve between the First and Second Watchung Mountains containing the Deserted Village of Feltville (founded 1845 by 'King' David Felt around his water-powered printing mill, later Glenside Park resort)—NJ's most famous haunted ghost village.",
        "system_merge_lore": "By Midday, Feltville's 10 weathered 1845 clapboard cottages serve as a tax-free Outlaw & Ghostwise Halfling smuggler market. At Midnight and Witching Hour (21:00–06:00), the church bells toll on their own, locking the village into The 1845 Mill-Curse Instance.",
        "special_mechanics": "Chrono-Engine Day/Night Shift: Daytime Black-Market Fence (no Safe-Zone taxes for Orange-Cursor players); Nighttime Witch-Wraith scroll farming.",
        "ambient_effects": ["Chrono-Phase Ghost Village", "Blue Brook Ravine Mist"],
        "monsters": ["Blue Brook Dire-Stags (Lv 8)", "King Felt's Origami-Iron Press Constructs (Lv 10)", "The Three Sisters of Glenside (Lv 12 Nocturnal Witches)"],
        "boss": "King David Felt's Printing-Press Automaton (Lv 13)",
        "resources": ["1845 Ledger-Script Grimoire Pages", "Seeley's Pond Blood-Reed", "Blue Brook Trap-Rock Shards"],
        "signature_grafts": ["Glenside Spectral Veil-Cloak Node"],
        "stationed_companions": [],
        "aliases": ["feltville", "deserted village", "watchung reservation", "glenside park"]
    },
    "high_point_stokes_obelisk": {
        "id": "high_point_stokes_obelisk",
        "name": "High Point State Park & Stokes State Forest, NJ",
        "subtitle": "The 220-Foot Tri-State Telemetry Obelisk & White Cedar Bog",
        "category": "wilderness",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 42.1,
        "bearing_deg": 23,
        "compass_dir": "NNE",
        "coords": {"x": 48, "y": 12},
        "level_min": 18,
        "level_max": 30,
        "is_safe_zone": False,
        "controlling_faction": "The Vanguard Coalition (Culvers Gap) & Arcane Conclave (High Point Spire)",
        "real_world_lore": "Kittatinny Ridge in Sussex County reaching 1,803 feet above sea level (NJ's highest peak), crowned by the 220-foot granite High Point Monument obelisk (1930) overlooking NJ, NY, and PA, alongside the Dryden Kuser high-elevation Atlantic White Cedar Swamp and Culvers Gap.",
        "system_merge_lore": "The 220-ft High Point Obelisk fires beams of gold-and-white hard-light marking the NJ/NY/PA Sector Firewalls and acts as the regional safe-zone barrier frequency relay. Companion Lyra Stargaze is stationed at the High Point Observatory Spire.",
        "special_mechanics": "Cartography Transcendence Node: ascending the 291 interior steps of the High Point Obelisk and surveying the horizon grants a +50 Cartography Mastery burst and lifts Fog of War across a 30-mile radius!",
        "ambient_effects": ["Tri-State Firewall Beacon Frequency", "High-Altitude Cedar Bog Mist"],
        "monsters": ["Culvers Gap Corrupted Goliaths (Lv 22)", "Dryden Kuser Cedar-Bog Draugr (Lv 25)", "Tillman Ravine Shadow-Stalkers (Lv 20)"],
        "boss": "THE TRI-STATE ARBITER (Lv 29 Aasimar/Clockwork Obelisk Guardian)",
        "resources": ["Shawnee Pink-Quartzite Runestones", "1,500-ft White Cedar Bog-Heart", "Tri-State Survey Matrix (+3 Cartography)"],
        "signature_grafts": [],
        "stationed_companions": ["Lyra"],
        "aliases": ["high point", "stokes state forest", "culvers gap", "sunrise mountain", "sussex overlook"]
    },
    "lehigh_gorge_glen_onoko": {
        "id": "lehigh_gorge_glen_onoko",
        "name": "Lehigh Gorge & Glen Onoko Falls, PA",
        "subtitle": "The Forbidden 900-Foot Cataract & Whitewater Mana-Trench",
        "category": "wilderness",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 42.0,
        "bearing_deg": 282,
        "compass_dir": "WNW",
        "coords": {"x": 15, "y": 40},
        "level_min": 20,
        "level_max": 28,
        "is_safe_zone": False,
        "controlling_faction": "Vanguard Outriders (Rail-Trail) / Wild Gorge",
        "real_world_lore": "30-mile-long deep-walled canyon where the Lehigh River drops 500 feet through Class III rapids beside abandoned 1830s Lehigh Canal locks and the treacherous 900-foot vertical waterfall climb of Glen Onoko Falls (Chameleon, Onoko, and Cave Falls).",
        "system_merge_lore": "Rusted 'Forbidden Trail' signs at the base of Glen Onoko flash red System warnings: [HAZARD TIER: EXTREME // GRAVITY MULTIPLIER: 1.5x]. Behind the waterfall curtain of Cave Falls lies a hidden Pre-Collapse Developer Cache and the phantom ruins of the 1884 Hotel Wahnetah.",
        "special_mechanics": "1.5x Gravity Multiplier on slick Aether-Moss ledges; hidden Developer Cache behind Cave Falls.",
        "ambient_effects": ["1.5x Gravity Ledge Hazard", "Whitewater Mana-Rapid Spray"],
        "monsters": ["Onoko Ledge-Harpy Matriarchs (Lv 23)", "Lock-Chamber Snapping Hydras (Lv 25)", "Chameleon-Falls Optical Stalkers (Lv 27)"],
        "boss": "Matriarch of Cave Falls (Lv 28)",
        "resources": ["Luminous Cascade Moss", "1838 Canal Lock-Iron", "Harpy Pinion Feathers"],
        "signature_grafts": ["Gravity-Brake Tendon Coils"],
        "stationed_companions": [],
        "aliases": ["lehigh gorge", "glen onoko", "cave falls", "hotel wahnetah"]
    },
    "hickory_run_boulder_field": {
        "id": "hickory_run_boulder_field",
        "name": "Hickory Run State Park & The Boulder Field, PA",
        "subtitle": "The 16-Acre Treeless Sea of Living Liths",
        "category": "wilderness",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 42.5,
        "bearing_deg": 298,
        "compass_dir": "WNW",
        "coords": {"x": 18, "y": 32},
        "level_min": 22,
        "level_max": 32,
        "is_safe_zone": False,
        "controlling_faction": "Unclaimed Kinetic Anomaly (Monitored by Arcane Conclave Geomancers)",
        "real_world_lore": "National Natural Landmark in Carbon County, PA: an eerie, dead-flat 16-acre (400×1,800 ft) sea of red and grey Catskill sandstone and quartz conglomerate boulders (<1° slope) with zero trees or soil for over 20,000 years, formed by Ice Age periglacial frost-wedging.",
        "system_merge_lore": "Flagged by Cardinal as a Zero-Mesh Kinetic & Gravitational Anomaly Zone. Every boulder carries a Piezoelectric Quartz Charge or is a dormant lith-golem. Sprinting across requires DC 12 Acrobatics boulder-hopping.",
        "special_mechanics": "The Sympathetic Lithic Hum: striking an enemy with a Blunt/Trench Hammer sends a shockwave through interlocking boulders for +25% bonus splash bludgeoning damage to adjacent foes—but awakens dormant boulder-golems within 30 ft!",
        "ambient_effects": ["Sympathetic Lithic Hum (+25% Blunt Splash DMG)", "Zero-Soil Boulder Hopping"],
        "monsters": ["Catskill Quartz-Lith Golems (Lv 24)", "Periglacial Frost-Crag Elementals (Lv 27)", "Lithic Basilisks & Gargoyle Packs (Lv 30)"],
        "boss": "MENHIR-ZERO: The Tectonic Colossus (Lv 34 — spawns after shattering 15 lith-golems)",
        "resources": ["Piezoelectric Catskill Quartz", "20,000-Year Frost-Wedged Core Stones", "Basilisk Petrified Glands"],
        "signature_grafts": ["Golem Hydraulic Arm", "Spring-Loaded Golem Greaves"],
        "stationed_companions": [],
        "aliases": ["hickory run", "boulder field", "sea of living liths", "menhir-zero"]
    },
    "wissahickon_valley_gorge": {
        "id": "wissahickon_valley_gorge",
        "name": "Wissahickon Valley Gorge & Hermit's Cave (Philadelphia), PA",
        "subtitle": "The Forbidden Ravine of the 1694 Apocalypse Monks & Devil's Pool",
        "category": "wilderness",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 51.0,
        "bearing_deg": 193,
        "compass_dir": "SSW",
        "coords": {"x": 35, "y": 86},
        "level_min": 35,
        "level_max": 52,
        "is_safe_zone": False,
        "controlling_faction": "The Arcane Conclave & Green Wardens (Mystic Sanctuary inside Hermit's Cave)",
        "real_world_lore": "Steep 1,800-acre garnet-mica schist gorge along Forbidden Drive in NW Philadelphia; home to the 1694 Hermit's Cave of Rosicrucian mystic/astronomer Johannes Kelpius (who awaited the Apocalypse and cast the Philosopher's Stone into the creek in 1708), bottomless Devil's Pool, and the giant steel Fingerspan Bridge.",
        "system_merge_lore": "Inside Hermit's Cave, the immortal Astral Echo of Magister Johannes Kelpius teaches Almandine Garnet cutting and high-tier transmutation. At the bottom of Devil's Pool pulses the 1708 Sunken Philosopher's Stone, glowing crimson-gold at midnight and allowing Master Alchemists to transmute Astral Gold.",
        "special_mechanics": "Hermit's Cave non-aggression alchemy sanctum; Devil's Pool midnight transmutation aura; hidden developer rope-cache beneath the giant steel Fingerspan Bridge.",
        "ambient_effects": ["1708 Philosopher's Stone Midnight Aura", "Garnet-Schist Ley-Glitter"],
        "monsters": ["Garnet-Schist Cliff Stalkers (Bleed on melee contact)", "1694 Wraith-Astronomers", "Cresheim Whirlpool Nixies"],
        "boss": "The Guardian of Devil's Pool (Lv 52)",
        "resources": ["Wissahickon Almandine Garnets", "Staurolite Fairy-Cross Crystals", "Kelpius's Alchemical Distillates", "Philosopher's Silt"],
        "signature_grafts": [],
        "stationed_companions": [],
        "aliases": ["wissahickon", "hermit's cave", "kelpius", "devil's pool", "forbidden drive", "fingerspan"]
    },
    "hawk_mountain_sanctuary": {
        "id": "hawk_mountain_sanctuary",
        "name": "Hawk Mountain Sanctuary (Kittatinny Ridge), PA",
        "subtitle": "The Continental Raptor Aerie & Thermal Updraft Sky-Highway",
        "category": "wilderness",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 53.5,
        "bearing_deg": 261,
        "compass_dir": "WSW",
        "coords": {"x": 8, "y": 56},
        "level_min": 26,
        "level_max": 36,
        "is_safe_zone": False,
        "controlling_faction": "The Aerie Watch (Tengu Sky-Monks & Green Warden Falconers)",
        "real_world_lore": "Perched at 1,521 feet on the Kittatinny Ridge spine where Rosalie Edge founded the world's first refuge for birds of prey in 1934; powerful thermal updrafts carry 18,000+ migrating raptors past the jagged Tuscarora quartzite crags of the North Lookout and River of Rocks boulder field.",
        "system_merge_lore": "Merged into the Continental Aerial Ley-Current where Giant Rocs, Storm-Griffons, and Thunderbirds ride ribbons of golden wind-mana. Enforces the hardcoded 1934 Covenant of Rosalie Edge: unprovoked attacks on juvenile sky-mounts trigger an instant 6d10 Sky-Wrath Lightning Strike.",
        "special_mechanics": "Defeating Void-Blighted Poacher-Constructs or challenging an Alpha Griffon in honorable single combat at North Lookout unlocks Aerial Mount Taming Permits and the Pneumatic Raptor-Vane Shoulder Rig.",
        "ambient_effects": ["Thermal Updraft Ley-Current (+15ft Jump)", "1934 Covenant of Rosalie Edge Edict"],
        "monsters": ["Kittatinny Storm-Griffons (Lv 28)", "Thermal-Draft Wyverns (Lv 31)", "Void-Blighted Poacher Ballista-Golems (Lv 30)"],
        "boss": "SOLARIS-WING: The Autumn Roc (Lv 38, 80-ft wingspan)",
        "resources": ["Storm-Griffon Storm-Quills", "Tuscarora Updraft Quartz", "Roc-Egg Albumen (+3 DEX & +15ft Jump Meal)"],
        "signature_grafts": ["Pneumatic Raptor-Vane Shoulder Rig (Glide & Fall Immunity)"],
        "stationed_companions": [],
        "aliases": ["hawk mountain", "raptor aerie", "north lookout", "river of rocks"]
    },
    "palisades_firewall_cliffs": {
        "id": "palisades_firewall_cliffs",
        "name": "The Hudson Palisades Sill, NJ & NY",
        "subtitle": "The 540-Foot Columnar Diabase Firewall Rampart",
        "category": "wilderness",
        "quadrant": "North & East (25-100 mi)",
        "distance_miles": 56.9,
        "bearing_deg": 77,
        "compass_dir": "ENE",
        "coords": {"x": 90, "y": 44},
        "level_min": 16,
        "level_max": 24,
        "is_safe_zone": False,
        "controlling_faction": "The Vanguard Coalition (Overwatch Towers)",
        "real_world_lore": "50-mile-long, 300-to-540-foot-tall sheer vertical wall of Early Jurassic columnar diabase (trap-rock) rising straight out of the western bank of the lower Hudson River from Jersey City/Fort Lee north to Nyack, including the Giant Stairs boulder scramble and Rockefeller Lookout.",
        "system_merge_lore": "Forms the towering western rampart directly overlooking the 1,000-foot crimson Hudson River Firewall of the Manhattan Monolith. Adventurers scramble across the Giant Stairs talus slope battling cliff-gargoyles and firewall sentries.",
        "special_mechanics": "High-elevation overwatch into Sector 0 (Manhattan); prime harvesting of hexagonal columnar diabase.",
        "ambient_effects": ["Crimson Firewall Glow", "500-Foot Cliff Updrafts"],
        "monsters": ["Columnar Trap-Rock Gargoyles (Lv 18)", "Cliffside Millionaire-Manor Revenants (Lv 20)", "Hudson Firewall Sentries (Lv 23)"],
        "boss": "The Palisades Basalt Behemoth (Lv 24)",
        "resources": ["Palisades Columnar Diabase", "Firewall Telemetry Shards"],
        "signature_grafts": ["Basalt Carapace Plating"],
        "stationed_companions": [],
        "aliases": ["palisades", "hudson palisades", "giant stairs", "fort lee cliffs"]
    },
    "harriman_bear_mountain_dunderberg": {
        "id": "harriman_bear_mountain_dunderberg",
        "name": "Harriman State Park, Bear Mountain & Doodletown, NY",
        "subtitle": "The Dunderberg Thunder-Mount, Spiral Railway & Ghost Hamlet",
        "category": "wilderness",
        "quadrant": "North & East (25-100 mi)",
        "distance_miles": 62.0,
        "bearing_deg": 53,
        "compass_dir": "NE",
        "coords": {"x": 84, "y": 20},
        "level_min": 11,
        "level_max": 18,
        "is_safe_zone": False,
        "controlling_faction": "The Green Wardens & Lycan Clans / Goblin Rail-Crews (Dunderberg)",
        "real_world_lore": "47,500+ acres of Hudson Highlands granite ridges, 31 lakes (including Hessian Lake from the 1777 battle), Bear Mountain Inn, Perkins Tower, the 18th-century mining ghost hamlet of Doodletown (and Hogencamp/Forest of Dean iron mines), and the unfinished 1890 Dunderberg Spiral Gravity Railway.",
        "system_merge_lore": "Dunderberg ('Thunder Mountain') is perpetually wreathed in Leyline Overload Storms (+25% Spell DMG), where Goblin & Duergar crews completed the 1890 Spiral Railway into a runaway gravity-cart combat track. Nearby Doodletown shifts from a daytime Kobold/Duergar trade camp into a nighttime spectral battlefield.",
        "special_mechanics": "Doodletown Day/Night Phase Shift; Hogencamp Electromagnet Palm-Coil graft recalls thrown axes/hammers as a Free Action!",
        "ambient_effects": ["Dunderberg Leyline Overload Storm (+25% Spell DMG)", "Hogencamp Magnetite Drift"],
        "monsters": ["Highland Ursine Behemoths (Lv 13)", "Hessian Lake Blood-Revenants (Lv 14)", "Dunderberg Storm-Goblins (Lv 15)", "Doodletown Timber-Viper Hydras (Lv 12)"],
        "boss": "The Donner-Berg Storm Roc (Lv 18) & Malakor, Iron-Chain Forgemaster (Forest of Dean Shaft, Lv 17)",
        "resources": ["Highland Lodestone Magnetite", "Highland Dire-Bear Marrow & Pelts", "Dunderberg Fulgurite (Lightning-Glass)"],
        "signature_grafts": ["Hogencamp Electromagnet Palm-Coil (Recalls Thrown Axes/Hammers)", "Ursine Hydraulic Tendon-Weave"],
        "stationed_companions": [],
        "aliases": ["harriman", "bear mountain", "dunderberg", "doodletown", "hessian lake", "hogencamp", "forest of dean"]
    },
    "ongs_hat_blue_hole": {
        "id": "ongs_hat_blue_hole",
        "name": "Ong's Hat Quantum Rift & The Blue Hole of Winslow, NJ",
        "subtitle": "The Incunabula Mirror-Seed Portal & Bottomless Cobalt Sinkhole",
        "category": "wilderness",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 68.0,
        "bearing_deg": 168,
        "compass_dir": "SSE",
        "coords": {"x": 64, "y": 90},
        "level_min": 45,
        "level_max": 65,
        "is_safe_zone": False,
        "controlling_faction": "Rogue Developer Remnants / Unclaimed Dimensional Anomaly",
        "real_world_lore": "Ong's Hat (Pemberton Twp) is an 18th-century Pine Barrens ghost town famous for the 1980s/90s 'Incunabula' chaos-magic/quantum-physics lore claiming renegade Princeton scientists opened a portal ('The Egg') to a parallel Earth. The Blue Hole of Winslow is a 120-ft circular pool of icy, turquoise-cobalt water in dark brown cedar woods, reputed to be a bottomless whirlpool.",
        "system_merge_lore": "Cardinal's lore-scraper ingested the Ong's Hat mythos literally: a shimmering Quantum-Egg Anomaly teleports parties into Mirror-Seed Instances where Trapped Developer Bunkers, DEV-CONSOLE terminals, and Admin ID Badges spawn at 300% normal frequency. Diving below 40 ft in the Blue Hole passes through a gravity-membrane into a subterranean crystal sea linking to Cornwall Mine Pit!",
        "special_mechanics": "300% Developer Bunker / Admin Badge spawn rate inside Ong's Hat Mirror-Seeds; one-way underwater wormhole vortex in the Blue Hole of Winslow.",
        "ambient_effects": ["Quantum Mirror-Seed Flicker", "Thermocline Gravity-Membrane"],
        "monsters": ["Incunabula Phase-Stalkers (Blink Ethereal every other round)", "Debug-Corrupted Developer Husks"],
        "boss": "The Blue Hole Undertow Kraken (Lv 58 Aquatic Ambush Boss)",
        "resources": ["The Chaos-Monk's Quantum Egg (1/Day Phase-Shift)", "Admin ID Badges", "Argus Developer Logs"],
        "signature_grafts": [],
        "stationed_companions": [],
        "aliases": ["ong's hat", "ongs hat", "blue hole", "winslow", "incunabula"]
    },
    "pine_barrens_warren_grove": {
        "id": "pine_barrens_warren_grove",
        "name": "The NJ Pine Barrens (Wharton / Byrne) & Warren Grove Gunnery Range, NJ",
        "subtitle": "The Shifting Glitch-Fey Barrens, Cinder Crucible & Entity #013",
        "category": "wilderness",
        "quadrant": "South & Southwest (25-100 mi)",
        "distance_miles": 75.0,
        "bearing_deg": 162,
        "compass_dir": "SSE",
        "coords": {"x": 70, "y": 92},
        "level_min": 30,
        "level_max": 68,
        "is_safe_zone": False,
        "controlling_faction": "The Green Wardens (Fire-Towers) vs. The Leeds Glitch-Devil",
        "real_world_lore": "1.1 million acres of sugar-sand fire-roads, pyrophytic pitch pines, stunted 4-ft Pygmy Pine Plains, and acidic cedar swamps over the 17-trillion-gallon Kirkwood-Cohansey Aquifer; home to the 1735 legend of the Jersey Devil and the 9,400-acre Warren Grove F-16 bombing range.",
        "system_merge_lore": "Cardinal's procedural generator glitched across the identical miles of sugar-sand roads, causing map nodes to shuffle every 30 minutes outside Batsto's beacon unless a party has Survival 250+ or an Aether-Resonant Ocular. At Warren Grove ('The Cinder-Crater Crucible'), automated range towers paint 20-ft red laser target circles every 3 rounds for orbital strafing runs!",
        "special_mechanics": "Fire damage in the Pines triggers Pyrophytic Awakening (spawning Ember-Forged Pine Ents); savvy vanguards kite monsters into Warren Grove's Red-Smoke Target Locks to power-level.",
        "ambient_effects": ["30-Minute Procedural Map Shuffle", "Warren Grove 3-Round Orbital Strafing Locks"],
        "monsters": ["Cedar-Water Elementals", "Carnivorous Sundew Hydras", "20mm Vulcan Turret-Crabs", "Target-Hulk Tank Mimics"],
        "boss": "THE LEEDS GLITCH-DEVIL (ENTITY #013) (Lv 68 Apex Roaming Stalker Boss)",
        "resources": ["Pure Kirkwood-Cohansey Aquifer Water", "Depleted Uranium Penetrator Cores (Ignore 20% DEF)", "Leeds Devil Wing-Membrane"],
        "signature_grafts": ["Chimeric Beast Claws"],
        "stationed_companions": [],
        "aliases": ["pine barrens", "wharton state forest", "brendan t. byrne", "warren grove", "jersey devil", "leeds devil"]
    },
    "shawangunk_gunks_ricketts_glen": {
        "id": "shawangunk_gunks_ricketts_glen",
        "name": "The Shawangunk Ridge ('The Gunks', NY) & Ricketts Glen (22 Falls, PA)",
        "subtitle": "The 1,000-Foot Piezoelectric Quartz Wall & Twenty-Two Elder Cataracts",
        "category": "wilderness",
        "quadrant": "West & Northwest (25-100 mi)",
        "distance_miles": 79.1,
        "bearing_deg": 300,
        "compass_dir": "WNW",
        "coords": {"x": 8, "y": 24},
        "level_min": 14,
        "level_max": 45,
        "is_safe_zone": False,
        "controlling_faction": "The Green Wardens (High Elder Circle) & Eladrin Courts",
        "real_world_lore": "The Gunks (Ulster Co., NY, 79.1 mi NNE) feature 300-ft sheer white Silurian quartz conglomerate cliffs (The Trapps) and sky-lakes (Minnewaska, Awosting). Ricketts Glen (Luzerne Co., PA, 79.2 mi WNW) features 22 named waterfalls (led by 94-ft Ganoga Falls) cascading through 500-to-900-year-old virgin old-growth eastern hemlocks along the Allegheny Front.",
        "system_merge_lore": "The Gunks are magnified into a 1,000-ft Vertical Escarpment Grind Zone for 3D piton-and-grapple combat where impacts spark piezoelectric ley-arcs. At Ricketts Glen, each of the 22 waterfalls acts as a Sequential Leyline Seal (+30% Water/Cold/Nature power) guarded by awakened 900-Year Hemlock Elder-Treants and Eladrin Mist-Blades.",
        "special_mechanics": "3D Vertical Cliff Combat on The Trapps; Ricketts Glen yields Heartwood of the 900-Year Hemlock (Grade 6 Mythic weapon/staff haft that self-regenerates +2 Durability per hour!).",
        "ambient_effects": ["Piezoelectric Quartz Cliff Sparks", "22-Cataract Elemental Empowerment (+30% Water/Nature)"],
        "monsters": ["Trapps Quartz-Gargoyles (Lv 15)", "Awosting Sky-Eels (Lv 16)", "900-Year Hemlock Elder-Treants (Lv 38)", "Eladrin Mist-Blades (Lv 40)"],
        "boss": "Ziz-Aetherius, Sovereign of the White Escarpment (Lv 20) & Allegheny Front Frost-Wyrm (Lv 44)",
        "resources": ["Heartwood of the 900-Year Hemlock (Self-Repairing Grade 6 Timber)", "Ganoga Pure-Mana Tear (+1 WIS)", "Flawless Trapps Piezoelectric Quartz"],
        "signature_grafts": ["Trapps Piton-Claw Grip Actuators (Permanent Climb Speed)"],
        "stationed_companions": [],
        "aliases": ["the gunks", "shawangunk", "minnewaska", "ricketts glen", "ganoga falls"]
    },
    "catskill_peaks_ashokan_overlook": {
        "id": "catskill_peaks_ashokan_overlook",
        "name": "The Catskill High Peaks, Kaaterskill Falls, Overlook Ruins & Ashokan Reservoir, NY",
        "subtitle": "The Wall of Manitou, Rattlesnake Hotel Ruins & Twelve Sunken Villages",
        "category": "wilderness",
        "quadrant": "North & East (25-100 mi)",
        "distance_miles": 92.0,
        "bearing_deg": 25,
        "compass_dir": "NNE",
        "coords": {"x": 76, "y": 2},
        "level_min": 18,
        "level_max": 25,
        "is_safe_zone": False,
        "controlling_faction": "Goliath & Firbolg Enclaves / Scaled Bloodlines (Overlook Ruins)",
        "real_world_lore": "Dissected Devonian river delta plateau rising to 4,180 ft on Slide Mountain; features two-tiered 260-ft Kaaterskill Falls, the concrete shell of the 1928 Overlook Mountain House (infested with timber rattlesnake dens), and the 12-mile Ashokan Reservoir (built 1915 by flooding 12 Catskill villages).",
        "system_merge_lore": "Above 3,500 ft, the High Peaks enter a Rip Van Winkle Slumber Zone (resting off-trail skips 24h of simulation time). The 1928 Overlook Hotel concrete shell is a Naga & Rattlesnake-Basilisk stronghold crowned by a Fire Tower that lifts Fog of War across the Northern Quadrant. During storms, the church steeples of the 12 Flooded Villages rise above the Ashokan Reservoir.",
        "special_mechanics": "Overlook Fire Tower lifts Northern Quadrant Fog of War; Ashokan Reservoir sunken villages reveal pre-1915 loot vaults during Leyline Overload Storms.",
        "ambient_effects": ["Rip Van Winkle Chrono-Slumber Mist", "Hudson River School Prismatic Light"],
        "monsters": ["Overlook Rattlesnake-Basilisks (Lv 19)", "Kaaterskill Mist-Nymphs (Lv 20)", "Catskill Goliath Crag-Wardens (Lv 21)", "Drowned Villagers of Olivebridge (Lv 19)"],
        "boss": "Nessie of the Aqueduct, 'The Ashokan Hydra' (Lv 25)",
        "resources": ["Catskill Devonian Bluestone", "Overlook Basilisk Venom & Rattle-Scales", "Slide Mountain Balsam Resin", "Ashokan Pre-1915 Sunken Relics"],
        "signature_grafts": ["Overlook Pit-Viper Thermal Optics", "Goliath Crag-Lung Bellows"],
        "stationed_companions": [],
        "aliases": ["catskills", "slide mountain", "kaaterskill falls", "overlook mountain", "ashokan reservoir"]
    }
}

# Enrich each zone entry with dispersed D&D / Pathfinder / Fantasy Series races, monsters & grafts
try:
    from backend.bestiary_compendium import enrich_world_atlas_zones
    enrich_world_atlas_zones(WORLD_ATLAS_ZONES)
except Exception:
    pass

# Enrich each zone entry with convenient normalized alias keys for UI & GM consumers
for _zid, _z in WORLD_ATLAS_ZONES.items():
    _z.setdefault("id", _zid)
    _z.setdefault("level_range", (_z.get("level_min", 1), _z.get("level_max", 10)))
    _z.setdefault("bearing", _z.get("compass_dir", "N"))
    _z.setdefault("faction", _z.get("controlling_faction", "Unclaimed"))
    _z.setdefault("real_world_name", _z.get("subtitle", _z.get("name", "")))
    _z.setdefault("lore_summary", _z.get("system_merge_lore", ""))
    _z.setdefault("environmental_hazards", _z.get("ambient_effects", []))
    _c = _z.get("coords", {"x": 50, "y": 50})
    _z.setdefault("grid_coords", (_c.get("x", 50), _c.get("y", 50)))


def resolve_zone_from_location(location_str: str, x: Optional[int] = None, y: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Resolves a location string or (x, y) coordinates to a canonical zone dictionary
    in WORLD_ATLAS_ZONES.
    """
    if location_str:
        loc_low = location_str.strip().lower()
        # 1. Direct ID or exact name match
        if loc_low in WORLD_ATLAS_ZONES:
            return WORLD_ATLAS_ZONES[loc_low]
        for z_id, z_data in WORLD_ATLAS_ZONES.items():
            if z_data["name"].lower() == loc_low:
                return z_data
        # 2. Alias substring match (prioritize longest matching alias to avoid partial ambiguity)
        best_match = None
        best_len = 0
        for z_id, z_data in WORLD_ATLAS_ZONES.items():
            if z_data["name"].lower() in loc_low and len(z_data["name"]) > best_len:
                best_match = z_data
                best_len = len(z_data["name"])
            for alias in z_data.get("aliases", []):
                a_low = alias.lower()
                if (a_low in loc_low or loc_low in a_low) and len(a_low) > best_len:
                    best_match = z_data
                    best_len = len(a_low)
        if best_match is not None:
            return best_match

    # 3. Coordinate proximity fallback if (x, y) provided
    if x is not None and y is not None:
        closest_zone = None
        min_dist = 999999.0
        for z_id, z_data in WORLD_ATLAS_ZONES.items():
            coords = z_data.get("coords", {})
            zx, zy = coords.get("x", 50), coords.get("y", 50)
            dist = math.hypot(x - zx, y - zy)
            if dist < min_dist:
                min_dist = dist
                closest_zone = z_data
        if min_dist <= 3.5:
            return closest_zone

    return None


def is_location_safe_zone(location_str: str, x: Optional[int] = None, y: Optional[int] = None) -> bool:
    """
    Determines whether a given location string or coordinate is a protected Safe-Zone Hub.
    Checks WORLD_ATLAS_ZONES first, with fallback to canonical safe-zone keywords.
    """
    loc_low = (location_str or "").lower()
    # Explicit hostile / non-safe overrides even if "washington" is in township name
    if any(h in loc_low for h in ["adit", "labyrinth", "depths", "collapse", "boss", "roaring rock", "pohatcong mountain"]):
        return False

    zone = resolve_zone_from_location(location_str, x=x, y=y)
    if zone is not None:
        return bool(zone.get("is_safe_zone", False))

    safe_keywords = [
        "safe-zone", "safe zone", "clinic", "catacomb", "depot", "sanctuary",
        "manor", "outpost", "taphouse", "tavern", "bastion", "citadel", "haven"
    ]
    return any(w in loc_low for w in safe_keywords)


def get_zones_by_category(category: Optional[str] = None, quadrant: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Returns a list of zones filtered by category ('safe_zone', 'mine', 'dungeon', 'wilderness')
    and/or quadrant, sorted by distance from Washington Borough, NJ.
    """
    norm_quad = quadrant.replace("–", "-").replace("—", "-").lower().strip() if quadrant else None
    results = []
    for z_id, z_data in WORLD_ATLAS_ZONES.items():
        if category and category.lower() != "all" and z_data.get("category") != category.lower():
            continue
        if norm_quad and norm_quad != "all":
            z_quad = z_data.get("quadrant", "").replace("–", "-").replace("—", "-").lower().strip()
            if z_quad != norm_quad and norm_quad not in z_quad:
                continue
        results.append(z_data)
    results.sort(key=lambda z: (z.get("distance_miles", 0.0), z.get("level_min", 1)))
    return results


def get_zone_salvage_yields(zone_id_or_loc: str, target_type: str = "ruins") -> List[Dict[str, Any]]:
    """
    Returns regional specialty ores, salvage materials, or botanical resources for a given zone.
    """
    zone = resolve_zone_from_location(zone_id_or_loc)
    if not zone:
        return []
    res_list = zone.get("resources", [])
    items = []
    for r_name in res_list:
        items.append({
            "name": r_name,
            "qty": 1,
            "weight": 1.5,
            "category": "Regional Atlas Resource",
            "desc": f"Regional specialty resource harvested from {zone['name']} ({zone['subtitle']}).",
            "source_zone": zone["id"]
        })
    return items


def calculate_travel_telemetry(current_loc: str, target_zone_id: str, player_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Calculates overland travel distance, travel time in minutes, hazard DC, and applies
    Cartography 1–1000 mastery milestones and Morris Canal slipstream modifiers.
    """
    target_zone = WORLD_ATLAS_ZONES.get(target_zone_id) or resolve_zone_from_location(target_zone_id)
    if not target_zone:
        return {
            "valid": False,
            "reason": f"Unknown destination zone: {target_zone_id}"
        }

    curr_zone = resolve_zone_from_location(current_loc) or WORLD_ATLAS_ZONES["washington_borough"]
    c_coords = curr_zone.get("coords", {"x": 50, "y": 50})
    t_coords = target_zone.get("coords", {"x": 50, "y": 50})

    # Calculate approximate overland distance between current zone and target zone
    if curr_zone["id"] == target_zone["id"]:
        miles = 0.5
    elif curr_zone["id"] == "washington_borough":
        miles = max(0.5, float(target_zone.get("distance_miles", 5.0)))
    elif target_zone["id"] == "washington_borough":
        miles = max(0.5, float(curr_zone.get("distance_miles", 5.0)))
    else:
        # Law of cosines using distance_miles and bearing_deg from origin
        d1 = float(curr_zone.get("distance_miles", 0.0))
        d2 = float(target_zone.get("distance_miles", 0.0))
        b1 = math.radians(float(curr_zone.get("bearing_deg", 0.0)))
        b2 = math.radians(float(target_zone.get("bearing_deg", 0.0)))
        miles = math.sqrt(max(0.25, d1 * d1 + d2 * d2 - 2 * d1 * d2 * math.cos(b2 - b1)))

    # Check Cartography mastery (1–1000 scale)
    cart_mastery = 1
    if isinstance(player_state, dict):
        skills = player_state.get("skills", {})
        c_entry = skills.get("Cartography", 1)
        if isinstance(c_entry, dict):
            cart_mastery = int(c_entry.get("mastery", 1))
        elif isinstance(c_entry, (int, float)):
            cart_mastery = int(c_entry)

    # Baseline walking speed: 3.5 mph (~17 mins per mile)
    speed_mph = 3.5
    speed_notes = []
    hazard_reduction = 0

    if cart_mastery >= 100:
        hazard_reduction += 3
        speed_notes.append("Cartography 100+ (Sub-Level Nav-Mesh Bypass: -50% Encounter Threat)")
    if cart_mastery >= 750:
        speed_mph *= 2.0
        speed_notes.append("Cartography 750+ (Macro-Territory Cartogram: 2x Travel Speed)")

    # Morris Canal corridor bonus along Route 57 E-W axis
    canal_hubs = {"washington_borough", "phillipsburg_easton_confluence", "hackettstown_citadel", "andover_waterloo_mine", "morris_canal_slipstreams"}
    if curr_zone["id"] in canal_hubs and target_zone["id"] in canal_hubs:
        speed_mph *= 1.5
        speed_notes.append("Morris Canal Gravitational Slipstream (+50% Transit Speed)")

    travel_minutes = max(10, int(round((miles / speed_mph) * 60.0)))
    base_dc = max(8, min(22, 8 + (target_zone.get("level_min", 1) // 3) - hazard_reduction))
    if target_zone.get("is_safe_zone"):
        base_dc = max(5, base_dc - 4)

    return {
        "valid": True,
        "origin_zone": curr_zone,
        "target_zone": target_zone,
        "distance_miles": round(miles, 1),
        "travel_minutes": travel_minutes,
        "travel_hours": round(travel_minutes / 60.0, 1),
        "hazard_dc": base_dc,
        "cartography_mastery": cart_mastery,
        "speed_notes": speed_notes,
        "target_coords": t_coords
    }


def format_zone_gm_briefing(zone: Optional[Dict[str, Any]]) -> str:
    """
    Formats a concise, high-signal GM context block for the active zone in the 100-mile atlas.
    """
    if not zone:
        return ""
    cat_labels = {
        "safe_zone": "SAFE-ZONE HUB / FACTION CITADEL",
        "mine": "SUBTERRANEAN MINE / FURNACE EXTRACTION ZONE",
        "dungeon": "INSTANCED DUNGEON / MEGASTRUCTURE RIFT",
        "wilderness": "WILDERNESS GRIND ZONE / WORLD ANOMALY"
    }
    cat_str = cat_labels.get(zone.get("category", ""), "REGIONAL ZONE")
    monsters_str = ", ".join(zone.get("monsters", [])) or "None (Warded Sanctuary)"
    disp_monsters_str = ", ".join(zone.get("dispersed_monsters", [])) or "None"
    races_str = ", ".join(zone.get("resident_races", [])) or "Pure Human, Deepforged Dwarf, Aether-Touched Elf"
    res_str = ", ".join(zone.get("resources", [])) or "Standard Salvage"
    grafts_str = ", ".join(zone.get("signature_grafts", [])) or "None"
    comps_str = ", ".join(zone.get("stationed_companions", [])) or "None"

    quadrant = zone.get("quadrant", "Inner Core (0-25 mi)")
    v_layers = VERTICAL_LAYERS_BY_SECTOR.get(quadrant, {})
    v_above = ", ".join(v_layers.get("above_ground", [])[:4]) or "Local Ridges & Towers"
    v_street = ", ".join(v_layers.get("street_level", [])[:4]) or "Regional Highways & Rail"
    v_sub = ", ".join(v_layers.get("subterranean", [])[:4]) or "Bedrock Tunnels & Shafts"
    v_water = ", ".join(v_layers.get("below_waterline", [])[:4]) or "River Channels & Reservoirs"

    return f"""
[ACTIVE 100-MILE ATLAS ZONE TELEMETRY]:
- Zone Designation: {zone['name']} — "{zone.get('subtitle', '')}"
- Classification: {cat_str} | Quadrant: {quadrant} ({zone.get('distance_miles', 0)} mi {zone.get('compass_dir', '')} of Washington Borough)
- Recommended Level Range: Lv. {zone.get('level_min', 1)}–{zone.get('level_max', 10)} | Safe-Zone Status: {zone.get('is_safe_zone', False)}
- Controlling Faction: {zone.get('controlling_faction', 'Unclaimed')}
- Resident Fantasy Races & Enclaves (D&D / Pathfinder / Fantasy Series): {races_str}
- Real-World Geography & History: {zone.get('real_world_lore', '')}
- Cardinal System Merge Architecture: {zone.get('system_merge_lore', '')}
- Special Zone Mechanics: {zone.get('special_mechanics', '')}
- Sector 4-Layer Vertical Engineering Context:
  * Layer 1 (Above-Ground / Skyscrapers / Mountains): {v_above}
  * Layer 2 (Street-Level Highways & Surface Rail): {v_street}
  * Layer 3 (Subterranean Tunnels / Subways / Bunkers / Mines): {v_sub}
  * Layer 4 (Below-the-Waterline Bathymetry & Submerged Ruins): {v_water}
- Local & Dispersed Monster Ecology (D&D 3.5e/5E, Pathfinder 1E/2E, Witcher, FF, Monster Hunter, SAO): {monsters_str} (Dispersed Highlights: {disp_monsters_str})
- Zone Boss / Apex Spawn: {zone.get('boss') or zone.get('apex_fantasy_spawn') or 'None'} (Apex Multi-Universe Threat: {zone.get('apex_fantasy_spawn', 'None')})
- Harvestable Regional Ores & Resources: {res_str}
- Signature Golem & Monster Grafts: {grafts_str}
- Known Companion Sightings at Node: {comps_str}
"""


# =============================================================================
# 4-LAYER VERTICAL ENGINEERING SURVEY REGISTRY BY SECTOR
# =============================================================================
VERTICAL_LAYERS_BY_SECTOR: Dict[str, Dict[str, Any]] = {
    "Inner Core (0-25 mi)": {
        "sector_code": "Sector 1 (Primary Core: 0–25 Mi)",
        "vertical_span_ft": "+1,603 ft ASL (Catfish Fire Tower) to -2,700 ft (Oxford Washington Mine)",
        "above_ground": [
            "Bethlehem Steel Blast Furnaces A–E (240 ft tall, 5 furnaces & 20 Cowper stoves)",
            "Picatinny Arsenal Armaments Test Tower (200 ft) & 6,500-Acre Gorge Complex",
            "Paulinskill Viaduct (1,100 ft long x 115 ft high hollow-spandrel concrete arches)",
            "Delaware River Viaduct (1,452 ft long x 65 ft high)",
            "Yards Creek Pumped-Storage Upper Reservoir (1,555 ft ASL, 700-ft penstock drop)",
            "UACNJ Jenny Jump Astronomical Observatory (6 domes at 1,100 ft ASL)",
            "Cornish & Beethoven 5-Story Brick Organ Factories (Washington Borough)"
        ],
        "street_level": [
            "NJ-31 & NJ-57 Crossroads (Washington Borough Broad St & Belvidere Ave)",
            "I-78 & I-80 (Delaware Water Gap S-Curve Gorge Expressways)",
            "US-22, US-46, US-206, NJ-15, NJ-24, NJ-94, PA-33, PA-611",
            "Norfolk Southern Lehigh Line (30-40 freight trains/day) & Washington Secondary",
            "NJ Transit Morristown/Boonton Line & Raritan Valley Line (High Bridge)",
            "Lackawanna Cut-Off & 3.1-Mile Pequest Fill (110 ft tall embankment)",
            "Dover & Rockaway River RR (Picatinny Military Spur) & Bel-Del Railway"
        ],
        "subterranean": [
            "Van Nest Gap (Oxford) Rail Tunnel (3,002 ft 1862 brick/gneiss bore + central air shaft, 1.6 mi N of Washington)",
            "Musconetcong / Pattenburg Twin Rail Bores (4,893 ft longest rail tunnel in NJ)",
            "Manunka Chunk Twin Bores (938 ft side-by-side tunnels) & Roseville Tunnel (1,024 ft)",
            "AT&T Long Lines Netcong Nuclear Bunker (45,000 sq ft, 2 subterranean levels, EMP-shielded)",
            "AT&T Long Lines Chester Hardened Coaxial Node & 600+ Picatinny Earth-Covered Bunkers",
            "Oxford Washington Mine (-2,700 ft depth, 15 flooded levels) & Mount Hope New Leonard Shaft (-2,694 ft)",
            "Sterling Hill Zinc Mine (-2,675 ft, 35 mi UV-fluorescent tunnels) & Hibernia 1.5-Mi Bat Tunnel"
        ],
        "below_waterline": [
            "Merrill Creek Reservoir (-225 ft deepest water in NJ + 200-ft submerged tower & 3.2-mi rock tunnel)",
            "Round Valley Reservoir (-180 ft depth + submerged 19th-century village of McPherson)",
            "Spruce Run Reservoir (-73 ft depth + submerged 1760 Union Forge ruins)",
            "Lake Hopatcong (-58 ft depth + submerged 1750/1828 dams & sunken steamboats)",
            "Delaware Water Gap (-61 ft bedrock scour hole) & Morris Canal Subterranean Scotch-Turbine Vaults"
        ]
    },
    "West & Northwest (25-100 mi)": {
        "sector_code": "Sector 2 (West & NW: 25–100 Mi)",
        "vertical_span_ft": "+2,215 ft ASL (Camelback / High Point) to -2,200 ft (Southern Anthracite Synclines)",
        "above_ground": [
            "Allentown PPL Building (322 ft / 24 stories) & Five City Center (200 ft)",
            "Reading Pagoda atop Mt. Penn (886 ft ASL cliffside overlook, 620-ft drop)",
            "11-Story Locust Summit Central Coal Breaker (158 ft tall) & Huber Breaker Site",
            "Tunkhannock (Nicholson) Viaduct (2,375 ft long x 240 ft high concrete arch bridge)",
            "Tobyhanna Army Depot (1,400-acre DoD C4ISR radar & satcom complex at 2,130 ft ASL)",
            "High Point Monument (1,803 ft peak + 220 ft obelisk) & Concrete City (1911 ghost town)"
        ],
        "street_level": [
            "I-80, I-81, I-84, I-380, I-78 & I-476 (PA Turnpike Northeast Extension)",
            "US-22, US-209, US-309, US-222, US-6, US-11, PA-61 (buckled Centralia highway)",
            "Norfolk Southern Allentown Classification Hump Yard (46 tracks, 190 acres)",
            "Norfolk Southern Enola / Harrisburg Yards & Steamtown NHS Roundhouse (Scranton)",
            "Reading Blue Mountain & Northern RR (Lehigh Gorge Mainline) & Delaware-Lackawanna RR"
        ],
        "subterranean": [
            "Laurel Line Crown Avenue Tunnel (4,747 ft interurban bore under Scranton)",
            "Lehigh Tunnel Twin Highway Bores (4,380 ft through Blue Mountain on I-476)",
            "Vosburg Tunnel (3,902 ft), Nesquehoning Tunnel (3,800 ft piercing 50-ft Mammoth Coal Vein!), Mahanoy Tunnel (3,558 ft)",
            "7.8-Mile Jeddo Mine Drainage Tunnel (41,200+ ft subterranean river beneath Hazleton, 40M+ gal/day)",
            "7.5-Mile Lausanne Drainage Tunnel, 3.06-Mile Audenried Tunnel & 1.42-Mile Butler Mine Tunnel",
            "Centralia Burning Underground Coal Seams (1,000°F–1,350°F pyrolysis down to -300 ft)",
            "Lansford No. 9, Pioneer Tunnel, Lackawanna #190 Slope (-300 ft) & AT&T Finland/Dalmatia Nuclear Bunkers"
        ],
        "below_waterline": [
            "1959 Knox Mine Disaster Riverbed Breach (Port Griffith — 10.3B gal & 30 rail cars swallowed into mine workings)",
            "Lake Wallenpaupack (-60 ft depth + submerged 19th-century town of Wilsonville & 17 mi of roads)",
            "Beltzville Lake (-127 ft depth + submerged village of Pohopoco & covered bridges)",
            "Harveys Lake (-102 ft depth + sunken steamboats *Natoma* & *A.R.iser* and underwater piers)",
            "Lehigh Gorge Submerged 1838 Stone Dams & 30-Foot High Locks"
        ]
    },
    "North & East (25-100 mi)": {
        "sector_code": "Sector 3 (North & East: 25–100 Mi)",
        "vertical_span_ft": "+4,180 ft ASL (Slide Mountain) / +1,776 ft (One WTC) to -1,114 ft BSL (Catskill Aqueduct Siphon)",
        "above_ground": [
            "One World Trade Center (1,776 ft), Central Park Tower (1,550 ft), Empire State (1,454 ft), Steinway (1,428 ft), One Vanderbilt (1,401 ft)",
            "33 Thomas Street AT&T Long Lines Building (550-ft windowless nuclear-hardened TITANPOINTE tower)",
            "99 Hudson St (900 ft, Jersey City) & Brooklyn Tower (1,066 ft)",
            "George Washington Bridge (604-ft towers, 14 lanes), Verrazzano-Narrows (693-ft towers), Brooklyn/Manhattan/Queensboro Bridges",
            "West Point USMA Granite Fortress & US Bullion Depository (~22% of US gold reserves)",
            "Sandy Hook Nike Missile Base NY-56, Bell Labs CMB Horn Antenna, Camp Evans Radar & Brookhaven Lab"
        ],
        "street_level": [
            "I-95 (NJ Turnpike / Cross Bronx), I-80, I-87 (NY Thruway), I-287, I-78, I-495 (LIE), I-278 (BQE)",
            "Garden State Parkway, Palisades Interstate Parkway & Taconic State Parkway",
            "Amtrak Northeast Corridor, NJ Transit (11 lines), MTA Metro-North & LIRR",
            "Sunnyside Yard (182 acres, Queens), Hoboken Terminal (17 tracks), Oak Island Hump Yard & Croton-Harmon Yard"
        ],
        "subterranean": [
            "NYC Subway System (472 stations, 850 track miles, reaching -180 ft in Manhattan Schist at 190th/191st St + 1904 City Hall Ghost Station)",
            "Grand Central Terminal Undercity (67 tracks on 2 levels + -180 ft Grand Central Madison LIRR caverns + -109 ft secret M42 vault + FDR's Track 61)",
            "28+ Subaqueous Hudson & East River Tubes (PATH Tubes -97 ft, Amtrak North/East River Tunnels, 63rd St Double-Deck -130 ft, Holland/Lincoln/Brooklyn-Battery Tunnels)",
            "Otisville Tunnel (5,314 ft), Edgewater (5,057 ft), Weehawken (-160 ft station), Bergen Arches & West Point CSX Tunnel (under USMA Parade Ground)",
            "Catskill Aqueduct Hudson Siphon (-1,114 ft below sea level in granite!) & 85-Mile Delaware Aqueduct (-600 to -900 ft)",
            "NYC Water Tunnels #1, #2, and #3 (-500 to -800 ft in bedrock)",
            "Federal Reserve Bank of NY Gold Vault (-80 ft, 6,331 tons gold, 90-ton cylinder lock), Rosendale Iron Mountain Nuclear Cave Vaults & Brookhaven 2.4-Mi RHIC Collider Tunnel"
        ],
        "below_waterline": [
            "Hudson River Fjord 'World's End' at West Point (-216 ft depth + submerged 1778 Great Iron Chain cribs & 200+ wrecks)",
            "Ashokan Reservoir (-190 ft depth + 12 submerged Catskill villages including Olivebridge & West Hurley)",
            "Rondout Reservoir (-175 ft, 3 drowned towns), Kensico (-155 ft, intact 1885 stone dam 110 ft underwater!) & New Croton (-141 ft, intact 1842 dam)",
            "Boonton Reservoir (-105 ft, submerged Old Boonton Ironworks) & Wanaque Reservoir (-90 ft, submerged Boardville)",
            "East River 'Hell Gate' (-108 ft blasted tidal trench & 1780 British treasure frigate HMS *Hussar* wreck)"
        ]
    },
    "South & Southwest (25-100 mi)": {
        "sector_code": "Sector 4 (South & SW: 25–100 Mi)",
        "vertical_span_ft": "+1,121 ft (Comcast Tech Center) to -1,400 ft (French Creek & Cornwall Mine Shafts)",
        "above_ground": [
            "Philadelphia Skyline: Comcast Tech Center (1,121 ft), Comcast Center (974 ft), One & Two Liberty Place (945 ft / 848 ft), BNY Mellon (792 ft)",
            "Philadelphia City Hall (548-ft world's tallest freestanding masonry building with 22-ft-thick walls)",
            "Atlantic City Ocean Casino (710 ft), Barnegat Lighthouse (165 ft) & Princeton Cleveland Tower (173 ft)",
            "Walt Whitman Bridge (2,000-ft span), Ben Franklin Bridge (1,750-ft span + PATCO rail decks) & Commodore Barry Bridge (1,644-ft cantilever)",
            "Lakehurst Hangar No. 1 (966x350x224 ft airship cathedral + 1.5-mi jet catapult tracks)",
            "Princeton PPPL Fusion Tokamak (100M °C), Limerick (507-ft) & Three Mile Island (372-ft) Nuclear Cooling Towers",
            "Doylestown's 3 'Mercer Mile' Poured-Concrete Castles (Fonthill, 6-Story Mercer Museum, Tile Works) & Eastern State Penitentiary"
        ],
        "street_level": [
            "I-95, NJ Turnpike, I-195, I-295, I-76 (Schuylkill Expressway & PA Turnpike), I-276, I-476, I-676",
            "Atlantic City Expressway, Garden State Parkway, US-1, US-30, US-130, US-202, US-206, NJ-70, NJ-72",
            "Amtrak Northeast Corridor & Keystone Corridor (110 mph Philly-Lancaster-Harrisburg)",
            "SEPTA Regional Rail (13 lines), PATCO High-Speed Line, NJ Transit River Line & Atlantic City Line",
            "Conrail Pavonia Hump Yard (Camden), Greenwich Yard (South Philly) & 30th Street Station"
        ],
        "subterranean": [
            "SEPTA Broad Street 4-Track Subway (stacked 3 levels deep beneath City Hall + sealed 1989 Spring Garden & unfinished 1915 Arch St Ghost Stations)",
            "SEPTA Market-Frankford Subway (+ twin underwater Schuylkill tubes) & Subway-Surface Trolley Tunnels",
            "PATCO Locust Street Subway (+ Franklin Square Station), 1.7-Mile Center City Commuter Tunnel & 3.5-Mile Center City Underground Pedestrian Concourse",
            "Pennsylvania Ave Subway/Tunnel (2,888-ft Callowhill Cut), Black Rock Tunnel (1,932 ft, 1837) & Union Canal Tunnel (729 ft, 1827 — oldest US tunnel)",
            "Princeton Firestone Library 3-Level Subterranean Book Vaults (70+ miles of underground shelving) & 12-Mile Campus Steam Tunnel Grid",
            "Cornwall Iron Mine (-1,225 ft vertical / 2,985 ft incline shafts) & French Creek Mine (-1,400 ft incline)",
            "Fort Mifflin 1771 Subterranean Brick Casemates & Eastern State Penitentiary's Willie Sutton 97-ft Escape Tunnel"
        ],
        "below_waterline": [
            "Delaware River 45-Ft Shipping Channel, Navy Yard Reserve Basin ('Ghost Fleet') & 1,092-ft Battleship Drydocks #2 & #3",
            "Submerged 1777 Revolutionary War *Chevaux-de-Frise* (iron-tipped river frames) & sunken 64-gun British warship HMS *Augusta* wreck",
            "Cornwall 400-Foot-Deep Flooded Open-Pit Crater Lake (submerged mining shovels, crushers & haul roads)",
            "The Blue Hole of Winslow (55°F artesian spring) & 17.7-Trillion-Gallon Kirkwood-Cohansey Subterranean Aquifer",
            "Mullica River 1778 Chestnut Neck Shipwrecks, Lake Galena (-55 ft, submerged New Galena lead mines & 1832 bridge) & Marsh Creek Lake (-75 ft, submerged Milford Mills)"
        ]
    }
}


def get_sector_vertical_layers(quadrant_or_zone_id: str) -> Dict[str, Any]:
    """
    Returns the 4-layer vertical engineering survey (Above-Ground, Street-Level,
    Subterranean, Below-the-Waterline) for a sector quadrant or zone ID.
    """
    if quadrant_or_zone_id in VERTICAL_LAYERS_BY_SECTOR:
        return VERTICAL_LAYERS_BY_SECTOR[quadrant_or_zone_id]
    zone = WORLD_ATLAS_ZONES.get(quadrant_or_zone_id) or resolve_zone_from_location(quadrant_or_zone_id)
    if zone:
        q = zone.get("quadrant", "Inner Core (0-25 mi)")
        return VERTICAL_LAYERS_BY_SECTOR.get(q, VERTICAL_LAYERS_BY_SECTOR["Inner Core (0-25 mi)"])
    return VERTICAL_LAYERS_BY_SECTOR["Inner Core (0-25 mi)"]

