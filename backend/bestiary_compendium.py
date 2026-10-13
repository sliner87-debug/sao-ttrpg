"""
backend/bestiary_compendium.py
Canonical Multi-Universe Bestiary, Creature Ecology & Fantasy Race Dispersion Engine
for The Fractured Overlay (SAO Sandbox V2).

Integrates iconic creatures, monsters, aberrations, dragons, fiends, undead, fey,
constructs, and races from:
- D&D 3.0x / 3.5e & D&D 5E
- Pathfinder 1E & Pathfinder 2E (Golarion)
- Major Fantasy Series:
  * The Witcher (Continent / Conjunction of the Spheres)
  * Final Fantasy (Eorzea / Gaia / Spira / Ivalice)
  * Monster Hunter (New & Old World Elder Dragons & Wyverns)
  * Sword Art Online (Aincrad / Alfheim / Underworld Bosses)
  * Tolkien / Lord of the Rings, Warhammer Fantasy, Elder Scrolls & Soulsborne

Disperses them across all 58 zones of the 100-Mile Washington, NJ World Atlas
and the broader North American Continental Sectors.
"""

from typing import Dict, List, Optional, Any
import random


# =============================================================================
# 1. CANONICAL MULTI-UNIVERSE BESTIARY COMPENDIUM (110+ ICONIC CREATURES)
# =============================================================================

BESTIARY_COMPENDIUM: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------------------
    # D&D 3.0x / 3.5e & 5E — ABERRATIONS & UNDERDARK HORRORS
    # -------------------------------------------------------------------------
    "beholder_eye_tyrant": {
        "id": "beholder_eye_tyrant",
        "name": "Beholder (Eye Tyrant)",
        "origin": "D&D 3.5e / 5E",
        "type": "Aberration",
        "cr_level": 22,
        "hp": 220,
        "ac": 18,
        "signature_abilities": [
            "Central Anti-Magic Cone (60ft cone suppresses spells, wands, and unharmonized magetech)",
            "Ten Ocular Eye-Rays (Disintegration Ray 4d10 Force, Telekinetic Ray, Petrification Ray, Enervation Ray, Charm/Fear Rays)"
        ],
        "lore": "Xenophobic floating orb of tyrannical paranoia crowned by ten writhing eyestalks and a massive central anti-magic eye, lairing in the UV-fluorescent marble caverns of Sterling Hill and beneath Manhattan.",
        "habitats": ["sterling_hill_franklin_mines", "manhattan_monolith_undercity", "lost_river_caverns"],
        "loot_drops": ["Beholder Central Anti-Magic Ocular", "Eyestalk Prism Lens", "Aberrant Synaptic Fluid"],
        "graft_id": "beholder_antimagic_ocular"
    },
    "mind_flayer_illithid": {
        "id": "mind_flayer_illithid",
        "name": "Mind Flayer (Illithid Psion)",
        "origin": "D&D 3.5e / 5E",
        "type": "Aberration",
        "cr_level": 18,
        "hp": 145,
        "ac": 16,
        "signature_abilities": [
            "Mind Blast (60ft cone, DC 16 INT save or 4d8+4 psychic damage and Stunned for 1 round)",
            "Tentacle Grapple & Extract Brain (4 facial tentacles grapple stunned prey; 10d6 piercing on extraction)",
            "Innate Psionics (Levitate, Dominate Monster, Plane Shift)"
        ],
        "lore": "Cephalopod-headed psionic tyrants whose astral nautiloids crashed into the particle accelerator rings of Brookhaven, the Princeton Tokamak, and the deep zinc shafts of Sussex County.",
        "habitats": ["sterling_hill_franklin_mines", "brookhaven_rhic_collider", "princeton_tokamak_pppl", "hibernia_mount_hope_mines"],
        "loot_drops": ["Illithid Psionic Tentacle Cortex", "Nautiloid Qualith Slate", "Cerebral Brine Vial"],
        "graft_id": "illithid_psionic_tendrils"
    },
    "elder_brain_overmind": {
        "id": "elder_brain_overmind",
        "name": "Elder Brain Overmind",
        "origin": "D&D 3.5e / 5E",
        "type": "Aberration (Boss)",
        "cr_level": 35,
        "hp": 420,
        "ac": 17,
        "signature_abilities": [
            "Creature Sense (5-mile telepathic radar)",
            "Psychic Link & Sever (tethers to party members, dealing 3d10 psychic damage per round)",
            "Brine Pool Tentacle Slam (30ft reach, 4d8 bludgeoning + grapple)"
        ],
        "lore": "A colossal, glowing-veined mass of aggregated Illithid neural tissue floating inside a flooded heavy-water cooling tank, orchestrating thrall networks across the sector.",
        "habitats": ["brookhaven_rhic_collider", "manhattan_monolith_undercity", "sterling_hill_franklin_mines"],
        "loot_drops": ["Elder Brain Synaptic Crown", "Illithid Psionic Tentacle Cortex", "Astral Tadpole Specimen"],
        "graft_id": "illithid_psionic_tendrils"
    },
    "aboleth_primeval": {
        "id": "aboleth_primeval",
        "name": "Primeval Aboleth / Alghollthu Veiled Master",
        "origin": "D&D 3.5e / 5E & Pathfinder 1E / 2E",
        "type": "Aberration (Aquatic)",
        "cr_level": 18,
        "hp": 195,
        "ac": 17,
        "signature_abilities": [
            "Mucus Cloud (Surrounding water forces DC 15 CON save or transforms skin into translucent water-breathing membrane)",
            "Enslave Mind (3/day telepathic domination, DC 16 WIS save)",
            "Probing Telepathy & Illusory Veil (Pathfinder Alghollthu genetic-rune manipulation)"
        ],
        "lore": "Amphibious, three-eyed prehistoric horrors older than the gods, lurking in the 180-foot depths of Round Valley Reservoir, the 225-foot Merrill Creek abyss, and the flooded limestone rooms of Rosendale.",
        "habitats": ["round_valley_sunken_ring", "rosendale_widow_jane_mines", "merrill_creek_blood_shroud", "archbald_pothole_shaft"],
        "loot_drops": ["Aboleth Mucus Membrane", "Alghollthu Memory Rune-Pearl", "Abyssal Pressure-Glass"],
        "graft_id": "pneuma_filter_gill_lung"
    },
    "umber_hulk": {
        "id": "umber_hulk",
        "name": "Umber Hulk (Tunneler Mandible-Beast)",
        "origin": "D&D 3.5e / 5E",
        "type": "Monstrosity / Aberration",
        "cr_level": 14,
        "hp": 135,
        "ac": 18,
        "signature_abilities": [
            "Confusing Gaze (Four multifaceted eyes force DC 15 CHA save at start of turn or random behavior for 1 round)",
            "Tunneler (Burrows through solid limestone and magnetite at 20ft/round, collapsing mine supports)",
            "Mandible Rend (2 claws + 2d8 slashing mandibles)"
        ],
        "lore": "Hulking, chitin-plated subterranean excavators whose four compound eyes scramble human equilibrium while their mandibles shear through iron ore seams.",
        "habitats": ["hibernia_mount_hope_mines", "oxford_furnace_mines", "lansford_no9_coal_mine", "tilly_foster_mine"],
        "loot_drops": ["Umber Hulk Compound Ocular", "Chitinous Mandible Shears", "Hardened Chitin Plates"],
        "graft_id": "aether_resonant_ocular"
    },
    "hook_horror": {
        "id": "hook_horror",
        "name": "Hook Horror (Echolocating Cavern Predator)",
        "origin": "D&D 3.5e / 5E",
        "type": "Monstrosity",
        "cr_level": 10,
        "hp": 95,
        "ac": 15,
        "signature_abilities": [
            "Echolocation Clack (Blindsight 60ft; immune to visual illusions and darkness)",
            "Climbing Hook-Arms (2d6+4 piercing hook strikes; hangs from cavern ceilings to ambush)"
        ],
        "lore": "Nine-foot-tall vulture-beaked insectoid bipeds with massive scythe-like bone hooks for forearms, hunting in packs through the bat-filled shafts of Mount Hope and Crystal Cave.",
        "habitats": ["hibernia_mount_hope_mines", "crystal_cave_indian_echo", "pohatcong_labyrinth", "lost_river_caverns"],
        "loot_drops": ["Hook Horror Scythe-Claw", "Resonant Carapace Plate"],
        "graft_id": "chimeric_beast_claws"
    },
    "cloaker_shadow_mantle": {
        "id": "cloaker_shadow_mantle",
        "name": "Cloaker (Subterranean Ray-Fiend)",
        "origin": "D&D 3.5e / 5E",
        "type": "Aberration",
        "cr_level": 12,
        "hp": 90,
        "ac": 14,
        "signature_abilities": [
            "Engulf & Damage Transfer (Wraps around a victim's head; 50% of damage dealt to the Cloaker is transferred to the engulfed target!)",
            "Subsonic Moan (Unnerves and frightens foes within 60ft, DC 14 WIS)",
            "Phantasmal Mirror Duplicates (Creates 3 illusory copies in dim light)"
        ],
        "lore": "Manta-like subterranean predators that hang folded on mine timbers masquerading as discarded leather cloaks until prey walks underneath.",
        "habitats": ["hibernia_mount_hope_mines", "lansford_no9_coal_mine", "eastern_state_penitentiary", "rosendale_widow_jane_mines"],
        "loot_drops": ["Cloaker Shadow-Hide Mantle", "Subsonic Vocal Sac"],
        "graft_id": "stalker_shadow_tendon"
    },
    "roper_stalagmite": {
        "id": "roper_stalagmite",
        "name": "Roper & Piercer Brood",
        "origin": "D&D 3.5e / 5E",
        "type": "Monstrosity",
        "cr_level": 13,
        "hp": 115,
        "ac": 20,
        "signature_abilities": [
            "Six Grasping Tendrils (50ft range; reels grappled victims 25ft closer each round and drains STR)",
            "False Appearance (Indistinguishable from a crystalline stalagmite until it lashes out)",
            "Armor-Crushing Bite (4d8+4 piercing)"
        ],
        "lore": "Apex ambush predators of limestone and zinc caverns, extending six sticky, strength-sapping filaments across chasms to drag vanguards into their central maw.",
        "habitats": ["crystal_cave_indian_echo", "lost_river_caverns", "sterling_hill_franklin_mines", "archbald_pothole_shaft"],
        "loot_drops": ["Roper High-Tensile Sinew", "Gizzard Gemstones (Diamonds & Willemite)"],
        "graft_id": None
    },
    "chuul_aberrant_crustacean": {
        "id": "chuul_aberrant_crustacean",
        "name": "Chuul (Aboleth Pincer-Sentinel)",
        "origin": "D&D 3.5e / 5E & Pathfinder 1E / 2E",
        "type": "Aberration",
        "cr_level": 11,
        "hp": 105,
        "ac": 16,
        "signature_abilities": [
            "Pincer Clamp & Paralyzing Tentacles (Grappled prey must pass DC 14 CON save against mouth-tentacle venom or be Paralyzed for 1 minute)",
            "Sense Magic (Passively detects all magic items and active spells within 120ft)"
        ],
        "lore": "Eight-foot-tall prehistoric lobster-like aberrations bred by Aboleths and Alghollthus to guard submerged vaults and drowned villages.",
        "habitats": ["round_valley_sunken_ring", "rosendale_widow_jane_mines", "great_swamp_lord_stirling", "philadelphia_navy_yard_ghost_fleet"],
        "loot_drops": ["Chuul Paralytic Tentacle Gland", "Calcified Lobster Carapace"],
        "graft_id": "basilisk_venom_gland"
    },

    # -------------------------------------------------------------------------
    # D&D 3.0x / 3.5e & 5E — CLASSIC MONSTROSITIES, MAGICAL BEASTS & OOZES
    # -------------------------------------------------------------------------
    "displacer_beast": {
        "id": "displacer_beast",
        "name": "Displacer Beast (Six-Legged Phase-Panther)",
        "origin": "D&D 3.5e / 5E",
        "type": "Monstrosity (Feywild)",
        "cr_level": 9,
        "hp": 95,
        "ac": 15,
        "signature_abilities": [
            "Displacement Illusion (Projects its visual image 3ft from its actual body; all attack rolls against it suffer Disadvantage / -4 penalty until it is hit)",
            "Avoidance (Takes zero damage on successful saving throws and only half damage on failed saves)",
            "Twin Barbed Shoulder-Tentacles (10ft reach, 2d6+4 bludgeoning + piercing each)"
        ],
        "lore": "Sleek, midnight-blue six-legged panthers with two barbed tentacles sprouting from their withers, bending light and spatial coordinates across the mist-shrouded ridges of Jenny Jump and the Pine Barrens.",
        "habitats": ["jenny_jump_ghost_lake", "ricketts_glen_falls", "pine_barrens_wharton_wilds", "wissahickon_valley_gorge"],
        "loot_drops": ["Displacer Tentacle Mantle", "Refractive Phase-Pelt"],
        "graft_id": "displacer_tentacle_mantle"
    },
    "owlbear_primeval": {
        "id": "owlbear_primeval",
        "name": "Primeval Owlbear & Snowy Owlbear",
        "origin": "D&D 3.5e / 5E & Pathfinder 1E / 2E",
        "type": "Monstrosity / Magical Beast",
        "cr_level": 5,
        "hp": 75,
        "ac": 14,
        "signature_abilities": [
            "Bloodcurdling Screech (Pathfinder 2E 60ft territorial shriek forces DC 13 WIS save or Frightened)",
            "Bear-Hug Grapple & Beak Rend (2d8+5 slashing claws + 1d10+5 hooked beak)",
            "Keen Sight and Smell"
        ],
        "lore": "Ferocious 1,500-pound crossbreeds of giant woodland bear and great horned owl that claimed the hemlock ridges of Pohatcong, Delaware Water Gap, and Bushkill Falls immediately after Initialization.",
        "habitats": ["pohatcong_roaring_rock", "delaware_water_gap_tammany", "bushkill_promised_land", "hacklebarney_black_river", "harriman_bear_mountain"],
        "loot_drops": ["Owlbear Hooked Beak", "Thick Feathered Bear-Pelt", "Rendered Chimera Marrow"],
        "graft_id": "chimeric_beast_claws"
    },
    "rust_monster": {
        "id": "rust_monster",
        "name": "Rust Monster (Ferrous Devourer)",
        "origin": "D&D 3.5e / 5E & Pathfinder 1E / 2E",
        "type": "Monstrosity",
        "cr_level": 6,
        "hp": 55,
        "ac": 14,
        "signature_abilities": [
            "Iron Scent (Detects ferrous metals, steel armor, and iron ore within 30 feet)",
            "Corrosive Antennae Touch (Reduces target's metal armor or shield AC by -1 and inflicts -25 Gear Durability per hit! Non-magical weapons striking it also corrode)"
        ],
        "lore": "Armadillo-scaled insectoids with two feathery, metal-oxidizing antennae and a propeller-shaped tail, swarming the rusted car pileups of Route 31, Oxford Furnace, and Phoenixville.",
        "habitats": ["pohatcong_roaring_rock", "oxford_furnace_mines", "andover_waterloo_mine", "phoenixville_foundry_lock60"],
        "loot_drops": ["Rust Monster Ferrous Antennae", "Oxidized Metal Gland", "Scrap Iron Plate"],
        "graft_id": "rust_monster_feeler_whip"
    },
    "bulette_landshark": {
        "id": "bulette_landshark",
        "name": "Bulette ('The Landshark')",
        "origin": "D&D 3.5e / 5E & Pathfinder 1E / 2E",
        "type": "Monstrosity / Magical Beast",
        "cr_level": 12,
        "hp": 125,
        "ac": 18,
        "signature_abilities": [
            "Subterranean Tremorsense (60ft; burrows through soil and shale at 40ft/round)",
            "Deadly Leap (Erupts from underground and leaps 15ft onto the party: DC 16 STR/DEX save or take 4d12+4 damage and be knocked Prone)",
            "Armor-Shearing Bite (4d12+4 piercing)"
        ],
        "lore": "Terrifying armored subterranean predators whose dorsal fin slices through highway asphalt and boulder fields like water before breaching with bone-shattering jaws.",
        "habitats": ["hickory_run_boulder_field", "ringing_rocks_diabase", "sourland_devils_half_acre", "hacklebarney_black_river"],
        "loot_drops": ["Bulette Dorsal Carapace Plate", "Landshark Serrated Jaw"],
        "graft_id": "bulette_dorsal_carapace"
    },
    "carrion_crawler": {
        "id": "carrion_crawler",
        "name": "Carrion Crawler (Eight-Tentacled Tunnel Scavenger)",
        "origin": "D&D 3.5e / 5E",
        "type": "Monstrosity",
        "cr_level": 5,
        "hp": 65,
        "ac": 13,
        "signature_abilities": [
            "Paralyzing Tentacle Lash (8 two-foot-long oral tentacles; DC 13 CON save or Poisoned and Paralyzed for 1 minute)",
            "Spider Climb (Scuttles upside-down along mine adit ceilings and subway arches)"
        ],
        "lore": "Ten-foot-long pale subterranean cutworms that cling to the ceilings of abandoned iron adits and collapsed railway tunnels, paralyzing lone scavengers.",
        "habitats": ["oxford_furnace_mines", "pohatcong_labyrinth", "lehigh_tunnel_penns_peak", "manhattan_monolith_undercity"],
        "loot_drops": ["Carrion Crawler Paralytic Mucus", "Segmented Chitin Hide"],
        "graft_id": "basilisk_venom_gland"
    },
    "gelatinous_cube_pudding": {
        "id": "gelatinous_cube_pudding",
        "name": "Gelatinous Cube & Black Pudding",
        "origin": "D&D 3.5e / 5E & Pathfinder 1E / 2E",
        "type": "Ooze",
        "cr_level": 8,
        "hp": 110,
        "ac": 8,
        "signature_abilities": [
            "Transparent Corridor Sweep (DC 15 Perception to spot a motionless Gelatinous Cube before walking straight into it)",
            "Engulf & Acid Digestion (6d6 acid damage at the start of each turn while engulfed; dissolves organic flesh while leaving metal/stone loot floating inside)",
            "Split (Black Pudding splits into two smaller puddings if struck by slashing or lightning damage!)"
        ],
        "lore": "Translucent 10x10-foot cubes of digestive acid and jet-black corrosive oozes that silently scour the rectangular gangways of Lansford No. 9, Picatinny bunkers, and thePohatcong Labyrinth.",
        "habitats": ["pohatcong_labyrinth", "lansford_no9_coal_mine", "sterling_hill_franklin_mines", "concrete_city_nanticoke"],
        "loot_drops": ["Alchemical Acid Membrane", "Undigested Adventurer Relic Cache"],
        "graft_id": None
    },
    "mimic_shapeshifter": {
        "id": "mimic_shapeshifter",
        "name": "Dungeon Mimic & Hoard-Mimic",
        "origin": "D&D 3.5e / 5E & Soulsborne",
        "type": "Monstrosity (Shapechanger)",
        "cr_level": 7,
        "hp": 80,
        "ac": 14,
        "signature_abilities": [
            "Adhesive Pseudopod (Anything that touches the Mimic is automatically Grappled, DC 14 STR to escape)",
            "False Object Guise (Imitates supply chests, vending machines, gun lockers, or ornate doors; snaps open with rows of teeth and a lashing purple tongue)"
        ],
        "lore": "Predatory amorphous shapechangers that disguise themselves as pre-collapse military supply crates in Picatinny, antique chests in the Mercer Museum, or gilded coffers in dungeon vaults.",
        "habitats": ["picatinny_arsenal_citadel", "mercer_mile_castles", "bannerman_castle_pollepel", "pohatcong_labyrinth"],
        "loot_drops": ["Mimic Adhesive Gland", "Swallowed Gold & Col Cache"],
        "graft_id": None
    },
    "phase_spider_ettercap": {
        "id": "phase_spider_ettercap",
        "name": "Phase Spider & Ettercap Brood-Herd",
        "origin": "D&D 3.5e / 5E & Pathfinder 1E / 2E",
        "type": "Monstrosity / Magical Beast",
        "cr_level": 8,
        "hp": 70,
        "ac": 14,
        "signature_abilities": [
            "Ethereal Jaunt (Shifts effortlessly between the Material Overlay and the Ethereal Plane as a bonus action, appearing behind backline mages)",
            "Dimension-Venom Bite (1d10+3 piercing + 4d8 poison damage, DC 13 CON save for half)"
        ],
        "lore": "Blue-and-white arachnids that phase out of physical reality between strikes, often herded by hunched, web-spinning Ettercaps in dark forest gorges and glitched relays.",
        "habitats": ["hacklebarney_black_river", "camp_evans_infoage", "watchung_feltville_deserted", "pine_barrens_wharton_wilds"],
        "loot_drops": ["Phase Spider Ethereal Spinneret", "Astral Silk Spool"],
        "graft_id": "phase_spider_spinneret"
    },
    "basilisk_cockatrice_gorgon": {
        "id": "basilisk_cockatrice_gorgon",
        "name": "Eight-Legged Basilisk & Iron-Plated Gorgon",
        "origin": "D&D 3.5e / 5E & Pathfinder 1E / 2E",
        "type": "Monstrosity / Magical Beast",
        "cr_level": 11,
        "hp": 115,
        "ac": 19,
        "signature_abilities": [
            "Petrifying Gaze / Breath (Basilisk gaze or Gorgon's 30ft green vapor cone forces DC 14 CON save or Restrained -> Petrified to solid stone/iron)",
            "Iron-Scale Trample (Gorgon charges 20ft and gores for 2d12+5 piercing + Prone)"
        ],
        "lore": "Heavy eight-legged reptiles and riveted iron-scaled bulls whose gaze and metallic breath turn trespassers into the eerie statues dotting Ringing Rocks and Overlook Mountain.",
        "habitats": ["ringing_rocks_diabase", "catskill_high_peaks_overlook", "vera_cruz_jasper_quarries", "cornwall_iron_pit"],
        "loot_drops": ["Basilisk Venom Gland", "Gorgon Iron-Lung Bellows", "Petrified Adventurer Core"],
        "graft_id": "basilisk_venom_gland"
    },
    "remorhaz_polar_wyrm": {
        "id": "remorhaz_polar_wyrm",
        "name": "Remorhaz ( Polar Heat-Centipede)",
        "origin": "D&D 3.5e / 5E & Pathfinder 1E / 2E",
        "type": "Monstrosity",
        "cr_level": 17,
        "hp": 195,
        "ac": 17,
        "signature_abilities": [
            "Heated Body (White-hot dorsal fins radiate extreme heat; any creature touching or hitting it in melee takes 3d6 Fire damage and risks weapon melting)",
            "Swallow Whole & Ice-Burrow (Melts tunnels straight through glacial ice and bedrock)"
        ],
        "lore": "Thirty-foot winged chitinous centipedes with glowing white-hot dorsal plates that inhabit the subterranean ice caves of Sam's Point and the Sunfish Pond glacial tarn.",
        "habitats": ["sams_point_ice_caves", "high_point_stokes_ridge", "archbald_pothole_shaft"],
        "loot_drops": ["Remorhaz Pyrophoric Dorsal Plate", "Cryo-Thermal Chitin"],
        "graft_id": "silt_marrow_geothermal_core"
    },
    "purple_worm_titan": {
        "id": "purple_worm_titan",
        "name": "Purple Worm (Subterranean Siege-Annelid)",
        "origin": "D&D 3.5e / 5E & Pathfinder 1E / 2E",
        "type": "Monstrosity (Gargantuan)",
        "cr_level": 28,
        "hp": 310,
        "ac": 18,
        "signature_abilities": [
            "Tunneler (Bores 10-foot-wide shafts through solid granite at 30ft/round)",
            "Swallow Whole (Bite deals 3d8+9 piercing and swallows target into a 6d6 acid gizzard)",
            "Tail Stinger (3d6+9 piercing + 12d6 poison, DC 19 CON save for half)"
        ],
        "lore": "Eighty-foot-long violet-plated siege worms drawn to rhythmic mining vibrations in the deep anthracite basins of Scranton, Cornwall, and the NYC bedrock.",
        "habitats": ["cornwall_iron_pit", "huber_breaker_lackawanna_mine", "manhattan_monolith_undercity", "tilly_foster_mine"],
        "loot_drops": ["Purple Worm Venom Stinger", "Gizzard Diamond Cluster", "Titan Annelid Armor Ring"],
        "graft_id": "basalt_carapace_plating"
    },

    # -------------------------------------------------------------------------
    # D&D 3.5e / 5E & PATHFINDER — DRAGONS & LINNORMS
    # -------------------------------------------------------------------------
    "chromatic_dragons_fivefold": {
        "id": "chromatic_dragons_fivefold",
        "name": "Chromatic Dragons (Red, Blue, Green, Black, White)",
        "origin": "D&D 3.5e / 5E & Pathfinder",
        "type": "Dragon",
        "cr_level": 26,
        "hp": 285,
        "ac": 20,
        "signature_abilities": [
            "Elemental Breath Weapon (Recharge 5-6: 60ft Fire/Acid/Poison Cone or 90ft Lightning Line dealing 12d8–16d6 damage)",
            "Frightful Presence (120ft aura, DC 17 WIS save or Frightened)",
            "Legendary Wing Attack & Tail Sweep"
        ],
        "lore": "True Chromatic Wyrms claiming regional lairs matching their aspect: Red Dragons in the burning seams of Centralia and Bethlehem blast furnaces; Blue Dragons atop the 480-Gauss Edison towers and Yards Creek; Green Dragons in the toxic mists of the Pine Barrens and Ricketts Glen; Black Dragons in the Great Swamp acid-fens; White Dragons in Sam's Point Ice Caves.",
        "habitats": [
            "centralia_pioneer_breach", "bethlehem_steel_titan_forge", "edison_ogden_mine",
            "pine_barrens_wharton_wilds", "great_swamp_lord_stirling", "sams_point_ice_caves"
        ],
        "loot_drops": ["Iridescent Chromatic Dragon Scale", "Draconic Breath Gland", "Ancient Wyrm Hoard Relic"],
        "graft_id": "wyrm_scale_sheath"
    },
    "metallic_dragons_guardians": {
        "id": "metallic_dragons_guardians",
        "name": "Metallic Dragons (Gold, Silver, Bronze, Copper)",
        "origin": "D&D 3.5e / 5E",
        "type": "Dragon (Celestial/Guardian)",
        "cr_level": 28,
        "hp": 320,
        "ac": 21,
        "signature_abilities": [
            "Dual Breath Weapons (Elemental Fire/Cold/Lightning + Weakening/Paralyzing/Repulsion Gas Breath)",
            "Change Shape (Walks among Safe-Zone hubs disguised as a scholar, blacksmith, or commander)"
        ],
        "lore": "Noble Metallic Wyrms who occasionally ally with the Vanguard Coalition and Arcane Conclave—Silver Dragons roosting above West Point and Mohonk, Bronze Dragons patrolling Sandy Hook, and Copper Dragons trading riddles in New Hope.",
        "habitats": ["west_point_granite_bastion", "new_paltz_mohonk_citadel", "sandy_hook_fort_hancock", "princeton_arcane_conclave"],
        "loot_drops": ["Blessed Metallic Scale", "Dragon-Forged Orichalcum Ingot"],
        "graft_id": "wyrm_scale_sheath"
    },
    "pathfinder_linnorms": {
        "id": "pathfinder_linnorms",
        "name": "Primeval Linnorms (Crag, Ice & Tarn Linnorm)",
        "origin": "Pathfinder 1E & 2E",
        "type": "Dragon (Primeval First-World)",
        "cr_level": 24,
        "hp": 270,
        "ac": 20,
        "signature_abilities": [
            "Curse of Death (Whoever lands the killing blow on a Linnorm must pass a DC 18 WIS save or suffer a permanent vulnerability to Fire/Cold or unhealable wither curse until cleansed)",
            "True Seeing & Freedom of Movement (Always active; cannot be paralyzed, slowed, or entangled)",
            "Pyroclastic Magma /Boiling Acid Breath & Constricting Serpentine Tail"
        ],
        "lore": "Wingless, two-legged primeval Scandinavian/Golarion ancestor-dragons of pure malice and nature's wrath, coiling through the glacial tarns of the Kittatinny Ridge, Lehigh Gorge, and Catskill peaks.",
        "habitats": ["delaware_water_gap_tammany", "lehigh_gorge_glen_onoko", "catskill_high_peaks_overlook", "sams_point_ice_caves"],
        "loot_drops": ["Primeval Linnorm Curse-Heart", "Tarn-Wyrm Acid Bile", "First-World Runestone"],
        "graft_id": "linnorm_curse_heart"
    },

    # -------------------------------------------------------------------------
    # D&D 3.5e / 5E & PATHFINDER — UNDEAD, PSYCHOPOMPS, FIENDS & PLANAR
    # -------------------------------------------------------------------------
    "lich_demilich_death_knight": {
        "id": "lich_demilich_death_knight",
        "name": "Arch-Lich, Demilich & Fallen Death Knight",
        "origin": "D&D 3.5e / 5E & Pathfinder",
        "type": "Undead (Boss)",
        "cr_level": 32,
        "hp": 265,
        "ac": 20,
        "signature_abilities": [
            "Phylactery Rejuvenation & Paralyzing Touch (3d6 cold + DC 18 CON save or Paralyzed)",
            "Demilich Howl (30ft death wail; DC 17 CON save or drop to 0 HP / take 8d6 necrotic)",
            "Death Knight Hellfire Orb (20ft radius 10d6 fire + 10d6 necrotic explosion)"
        ],
        "lore": "Undying necromantic sovereigns and oath-broken paladins ruling the radial cellblocks of Eastern State Penitentiary, the 11th floor of the Huber Breaker, and the catacombs beneath Manhattan.",
        "habitats": ["eastern_state_penitentiary", "huber_breaker_lackawanna_mine", "manhattan_monolith_undercity", "bannerman_castle_pollepel"],
        "loot_drops": ["Runed Phylactery Shard", "Soul-Gem Socket", "Hellfire-Tempered Greatsword"],
        "graft_id": "neural_overclock_cortex"
    },
    "pathfinder_psychopomps": {
        "id": "pathfinder_psychopomps",
        "name": "Psychopomps (Vanth Reaper, Morrigna & Nosoi)",
        "origin": "Pathfinder 1E & 2E",
        "type": "Monitor (Planar Soul-Warden)",
        "cr_level": 16,
        "hp": 140,
        "ac": 18,
        "signature_abilities": [
            "Adamantine Death-Scythe (Ignores undead resistances; inflicts Soul-Tether suppression)",
            "Morrigna Spider-Silk Soul-Wrappings (Restrains both corporeal and incorporeal spirits)",
            "Shepherd of the Boneyard (Neutral toward mortals unless they desecrate graves or harbor undead)"
        ],
        "lore": "Vulture-masked skeletal Vanth reapers, web-wrapped Morrigna investigators, and raven-masked Nosoi scribes dispatched from the Boneyard to purge unindexed undead anomalies.",
        "habitats": ["eastern_state_penitentiary", "jenny_jump_ghost_lake", "watchung_feltville_deserted", "fort_mifflin_mud_island"],
        "loot_drops": ["Vanth Adamantine Scythe-Shard", "Nosoi Feather Quill", "Boneyard Soul-Coin"],
        "graft_id": None
    },
    "pathfinder_sinspawn_fleshwarps": {
        "id": "pathfinder_sinspawn_fleshwarps",
        "name": "Thassilonian Sinspawn & Fleshwarp Grothluts",
        "origin": "Pathfinder 1E & 2E",
        "type": "Aberration (Mutant)",
        "cr_level": 8,
        "hp": 75,
        "ac": 14,
        "signature_abilities": [
            "Sinful Bite (Inflicts 1d6 mental damage and sickens targets with overwhelming Wrath, Envy, or Greed; DC 14 WIS)",
            "Fleshwarp Acid-Spit & Digestive Burst (Explodes in a 10ft splash of mutagenic bile on death)"
        ],
        "lore": "Split-jawed humanoid aberrations born from concentrated mortal sin and botched flesh-weaving vats inside forgotten asylum basements and glitched laboratories.",
        "habitats": ["concrete_city_nanticoke", "camp_evans_infoage", "merrill_creek_blood_shroud", "eastern_state_penitentiary"],
        "loot_drops": ["Mutagenic Fleshwarp Gland", "Runelord Sin-Shard"],
        "graft_id": "subdermal_carapace_weave"
    },
    "balor_pit_fiend_marilith": {
        "id": "balor_pit_fiend_marilith",
        "name": "Balor, Pit Fiend & Six-Armed Marilith",
        "origin": "D&D 3.5e / 5E & Tolkien (Valaraukar)",
        "type": "Fiend (Demon / Devil)",
        "cr_level": 36,
        "hp": 350,
        "ac": 20,
        "signature_abilities": [
            "Flame Whip & Lightning Longsword (Balor pulls targets 25ft into its 3d6 Fire Aura; explodes in a 16d6 Death Throes blast when slain)",
            "Marilith Reactive Six-Blade Flurry (Makes 6 saber attacks + 1 tail constrict per round, with a Reaction Parry on every enemy turn)",
            "Pit Fiend Infernal Mace & Poison Fang"
        ],
        "lore": "Towering lords of the Abyss and the Nine Hells—and ancient Valaraukar shadow-flame demons—drawn into the 1,000-degree subterranean coal inferno of Centralia and the molten slag pits of Bethlehem Steel.",
        "habitats": ["centralia_pioneer_breach", "bethlehem_steel_titan_forge", "three_mile_island_limerick_reactors"],
        "loot_drops": ["Balor Hellfire Core", "Marilith Six-Fold Demon Steel", "Pit Fiend Wing-Membrane"],
        "graft_id": "silt_marrow_geothermal_core"
    },
    "giants_ordining_runegiant": {
        "id": "giants_ordining_runegiant",
        "name": "True Giants (Hill, Stone, Frost, Fire, Storm & Pathfinder Rune Giant)",
        "origin": "D&D 3.5e / 5E & Pathfinder 1E / 2E",
        "type": "Giant",
        "cr_level": 20,
        "hp": 230,
        "ac": 18,
        "signature_abilities": [
            "Siege Boulder Hurl (Range 240ft, 4d10+7 bludgeoning)",
            "Fire Giant Forge-Greatsword / Storm Giant Lightning Strike (12d8 lightning)",
            "Pathfinder Rune Giant Command & Glowing Thassilonian Body-Runes (Sparks 4d6 electricity/fire when struck)"
        ],
        "lore": "Twenty-foot titans dispersed by elemental affinity: Stone Giants blending into the Hickory Run Boulder Field and Palisades cliffs; Fire Giants operating the Bethlehem Steel blast furnaces; Frost Giants in the Sam's Point Ice Caves; Storm Giants off Sandy Hook.",
        "habitats": [
            "hickory_run_boulder_field", "palisades_diabase_cliffs", "bethlehem_steel_titan_forge",
            "sams_point_ice_caves", "sandy_hook_fort_hancock", "catskill_high_peaks_overlook"
        ],
        "loot_drops": ["Giant-Forged Adamantine Ingot", "Runed Titan Belt-Buckle", "Storm-Charged Fulgarite"],
        "graft_id": "golem_hydraulic_arm"
    },
    "troll_oni_ettin": {
        "id": "troll_oni_ettin",
        "name": "Regenerating Troll, Venom Troll & Oni (Ogre Mage)",
        "origin": "D&D 3.5e / 5E & Pathfinder 1E / 2E",
        "type": "Giant / Fiend",
        "cr_level": 9,
        "hp": 105,
        "ac": 15,
        "signature_abilities": [
            "Troll Regeneration (Regains 15 HP at the start of every turn unless dealt Fire or Acid damage; severed limbs keep fighting!)",
            "Oni Shapechanger & Cone of Cold (Turns invisible at will, flies, wields a Glaive, and blasts 8d8 cold)",
            "Venom Troll Poison Splash (Sprays 2d6 poison whenever it takes slashing/piercing damage)"
        ],
        "lore": "Lanky, moss-green trolls lurking under historic stone bridges along the Delaware, Raritan, and Black Rivers, alongside horned blue-skinned Oni warlocks prowling mountain passes at night.",
        "habitats": ["hacklebarney_black_river", "great_swamp_lord_stirling", "harriman_bear_mountain", "sourland_devils_half_acre"],
        "loot_drops": ["Troll Regenerative Liver", "Venomous Troll Blood Vial", "Oni Iron Kanabo"],
        "graft_id": "troll_regenerative_liver"
    },
    "wendigo_algonquian_terror": {
        "id": "wendigo_algonquian_terror",
        "name": "Ancient Wendigo (Howler of the Starving Wind)",
        "origin": "Pathfinder 1E / 2E & North American Folklore",
        "type": "Fiend / Fey (Cold)",
        "cr_level": 22,
        "hp": 225,
        "ac": 19,
        "signature_abilities": [
            "Howl of the Wind (120ft cone of maddening blizzard despair; DC 17 WIS save or Frightened + Wendigo Torment)",
            "Ride the Wind (Flies at 100ft/round on charred, freezing stumps; snatches victims into the upper atmosphere)",
            "Cold & Regeneration (Regenerates 15 HP/round unless struck by Fire)"
        ],
        "lore": "Antler-skulled spirits of winter starvation and cannibalistic madness that haunt the frozen high ridges of the Poconos, High Point, and the Catskill peaks during Glitch-Freeze blizzards.",
        "habitats": ["high_point_stokes_ridge", "bushkill_promised_land", "catskill_high_peaks_overlook", "ricketts_glen_falls"],
        "loot_drops": ["Wendigo Permafrost Antler", "Heart of Starving Ice"],
        "graft_id": None
    },
    "jabberwock_protean_aeon": {
        "id": "jabberwock_protean_aeon",
        "name": "The Jabberwock (Tane) & Protean Imentesh",
        "origin": "Pathfinder 1E / 2E & D&D Feywild",
        "type": "Fey / Monitor (Chaos)",
        "cr_level": 27,
        "hp": 290,
        "ac": 21,
        "signature_abilities": [
            "Burbling Madness (30ft aura of nonsensical Carrollian/First-World babble forces DC 17 WIS save or Confused)",
            "Eyes of Flame (60ft scorching fire-ray dealing 8d8 fire) & Vulnerability to Vorpal Blades",
            "Protean Warpwave (Inflicts random planar mutations and spatial teleports on hit)"
        ],
        "lore": "Apex First-World engines of primeval whimsy and Maelstrom chaos that emerged around the dimensional portal anomalies of Ong's Hat and the Blue Hole in the NJ Pine Barrens.",
        "habitats": ["blue_hole_ongs_hat_anomaly", "pine_barrens_wharton_wilds", "princeton_tokamak_pppl"],
        "loot_drops": ["Jabberwock Flame-Eye Lens", "Protean Warp-Scale", "Vorpal Resonance Shard"],
        "graft_id": "aether_resonant_ocular"
    },

    # -------------------------------------------------------------------------
    # THE WITCHER SERIES — RELICTS, NECROPHAGES, VAMPIRES, SPECTERS & HYBRIDS
    # -------------------------------------------------------------------------
    "witcher_ancient_leshen": {
        "id": "witcher_ancient_leshen",
        "name": "Ancient Leshen (Woodland Spirit)",
        "origin": "The Witcher Series",
        "type": "Relict (Primal Forest Lord)",
        "cr_level": 18,
        "hp": 185,
        "ac": 17,
        "signature_abilities": [
            "Subterranean Root-Spike Eruption (Line of jagged oak roots erupts 40ft along the ground, dealing 4d8 piercing and Restraining targets, DC 15 DEX)",
            "Murder of Crows & Dire-Wolf Pack Call (Dissolves into a flock of ravens to teleport and summons 3 alpha wolves)",
            "Totem Rejuvenation (Draws +10 HP/round and +2 AC from bound bone-totems hidden in the woods; Vulnerable to Igni/Fire)"
        ],
        "lore": "Towering, stag-skulled woodland relicts made of gnarled ironwood and sinew that rule the ancient old-growth hemlock gorges of Ricketts Glen, Jenny Jump, and the Pine Barrens.",
        "habitats": ["ricketts_glen_falls", "jenny_jump_ghost_lake", "pine_barrens_wharton_wilds", "wissahickon_valley_gorge"],
        "loot_drops": ["Ancient Leshen Heartwood Root", "Leshen Stag-Skull Trophy", "Mutagenic Green Decoction Core"],
        "graft_id": "leshen_ancient_heartwood"
    },
    "witcher_fiend_chort": {
        "id": "witcher_fiend_chort",
        "name": "Fiend (Bies) & Chort",
        "origin": "The Witcher Series",
        "type": "Relict (Behemoth)",
        "cr_level": 16,
        "hp": 190,
        "ac": 16,
        "signature_abilities": [
            "Hypnotic Third Eye (Glowing central brow-eye projects a 30ft darkness/hypnosis field, blinding and stunning foes who fail a DC 15 WIS save)",
            "Unstoppable Antler Charge (Tramples through shield walls for 4d10+6 bludgeoning)",
            "Relentless Regeneration"
        ],
        "lore": "Massive, three-eyed horned quadrupeds with deer-like antlers and rows of jagged teeth that thunder through the mountain clearings of the Poconos and Harriman State Park.",
        "habitats": ["bushkill_promised_land", "harriman_bear_mountain", "delaware_water_gap_tammany", "sourland_devils_half_acre"],
        "loot_drops": ["Fiend Hypnotic Third Eye", "Chort Antler Crown", "Red Mutagen Core"],
        "graft_id": "aether_resonant_ocular"
    },
    "witcher_higher_vampire_bruxa": {
        "id": "witcher_higher_vampire_bruxa",
        "name": "Higher Vampire, Bruxa & Striga",
        "origin": "The Witcher Series",
        "type": "Vampire / Cursed One",
        "cr_level": 21,
        "hp": 175,
        "ac": 18,
        "signature_abilities": [
            "Bruxa Sonic Shockwave (Deafening ultrasonic shriek knocks all foes in a 20ft cone Prone and deals 4d8 thunder damage)",
            "Crimson Mist Blur (Turns invisible and teleports behind bleeding targets; heals for 50% of slashing/bite damage dealt)",
            "Vulnerable to Black Blood Alchemy & Moon Dust"
        ],
        "lore": "Apex nocturnal predators—from feral, muscle-bound Strigas in ruined crypts to supersonic Bruxae and immortal Higher Vampires ruling the gothic cellars of Fonthill Castle, Overlook Mountain, and Manhattan.",
        "habitats": ["mercer_mile_castles", "hibernia_mount_hope_mines", "eastern_state_penitentiary", "manhattan_monolith_undercity"],
        "loot_drops": ["Higher Vampire Mutated Saliva Gland", "Bruxa Sonic Vocal Chords", "Vampire Fang Signet"],
        "graft_id": "stalker_shadow_tendon"
    },
    "witcher_wraiths_drowners": {
        "id": "witcher_wraiths_drowners",
        "name": "Noonwraith, Nightwraith, Hym & Drowner Pack",
        "origin": "The Witcher Series",
        "type": "Specter / Necrophage",
        "cr_level": 8,
        "hp": 80,
        "ac": 14,
        "signature_abilities": [
            "Incorporeal Phase (Takes only 50% damage from physical weapons unless caught inside a Moon-Dust trap or Yrden/Runic Ward)",
            "Mirror Image Clone Drain (Splits into 3 spectral brides that siphon 2d6 HP/round to heal the main wraith)",
            "Drowner Mud-Lunge (Drags swimmers under in canal locks and swamps)"
        ],
        "lore": "Tragic specters bound to the historic murder-sites of Shades of Death Road and Feltville, alongside packs of gill-slitted Drowners lurking in the Morris and Delaware Canal locks.",
        "habitats": ["jenny_jump_ghost_lake", "morris_canal_slipstreams", "watchung_feltville_deserted", "great_swamp_lord_stirling"],
        "loot_drops": ["Specter Ectoplasm Essence", "Drowner Brain & Tongue", "Wraith-Touched Wedding Ring"],
        "graft_id": None
    },
    "witcher_royal_archgriffin": {
        "id": "witcher_royal_archgriffin",
        "name": "Royal Archgriffin & Cockatrice",
        "origin": "The Witcher Series & D&D / Pathfinder",
        "type": "Hybrid / Magical Beast",
        "cr_level": 15,
        "hp": 160,
        "ac": 17,
        "signature_abilities": [
            "Corrosive Acid Spit & Bleeding Wing-Buffet (Sprays armor-melting bile before diving at 80 mph)",
            "Lion-Talon Pounce (Pinning grapple + 3d8+5 rending beak)"
        ],
        "lore": "Majestic and ultra-aggressive eagle-lion hybrids nesting on the sheer white quartz cliffs of the Shawangunk Ridge, Hawk Mountain, and Mount Tammany.",
        "habitats": ["shawangunk_gunks_cliffs", "hawk_mountain_aerie", "delaware_water_gap_tammany"],
        "loot_drops": ["Archgriffin Acid Gland", "Royal Griffin Pinion Feathers"],
        "graft_id": "chimeric_beast_claws"
    },

    # -------------------------------------------------------------------------
    # FINAL FANTASY SERIES — BEHEMOTH, TONBERRY, MALBORO, CACTUAR & SUMMONS
    # -------------------------------------------------------------------------
    "ff_king_behemoth": {
        "id": "ff_king_behemoth",
        "name": "King Behemoth (The Horned Meteor-Titan)",
        "origin": "Final Fantasy Series",
        "type": "Magical Beast (Apex Boss)",
        "cr_level": 34,
        "hp": 380,
        "ac": 19,
        "signature_abilities": [
            "Heave & Thunderbolt Counter (Counters physical attacks with a 3d10+8 horn-gore and counters spells with a 4d10 Thundaga bolt)",
            "Ecliptic Meteor (At 25% HP and upon death, calls down a catastrophic astral meteor dealing 10d10 Fire/Force damage to everyone not hiding behind a boulder/pillar!)"
        ],
        "lore": "Colossal purple-maned muscular beast with swept-back golden horns that stands on its hind legs to cast high-tier lightning magic and call down Ecliptic Meteors in high-tier rift zones.",
        "habitats": ["princeton_tokamak_pppl", "manhattan_monolith_undercity", "warren_grove_bombardment_crater", "hickory_run_boulder_field"],
        "loot_drops": ["King Behemoth Great-Horn", "Behemoth Meteorite Heart", "Purple Mane Pelt"],
        "graft_id": "silt_marrow_geothermal_core"
    },
    "ff_master_tonberry": {
        "id": "ff_master_tonberry",
        "name": "Master Tonberry ('The Patient Lantern-Stalker')",
        "origin": "Final Fantasy Series",
        "type": "Aberration / Fiend",
        "cr_level": 20,
        "hp": 240,
        "ac": 18,
        "signature_abilities": [
            "Slow Inexorable Step (Advances 10ft per round, completely immune to knockback, stun, and slow)",
            "Everyone's Grudge / Karma (Lantern flares with green soul-fire, dealing 1d8 Psychic/True damage per monster the target has slain!)",
            "Chef's Knife (At 5ft melee range, delivers an armor-ignoring 8d10 piercing throat-stab)"
        ],
        "lore": "Small, green, amphibious figures in ragged brown burlap robes carrying a flickering lantern and a humble kitchen knife—feared by high-level veterans across every subterranean dungeon.",
        "habitats": ["eastern_state_penitentiary", "pohatcong_labyrinth", "lost_river_caverns", "lansford_no9_coal_mine"],
        "loot_drops": ["Tonberry Grudge Lantern", "Master Chef's Cleaver", "Star-Pendant"],
        "graft_id": "tonberry_grudge_lantern"
    },
    "ff_great_malboro": {
        "id": "ff_great_malboro",
        "name": "Great Malboro ('The Putrid Tentacle-Maw')",
        "origin": "Final Fantasy Series",
        "type": "Plant / Aberration",
        "cr_level": 19,
        "hp": 210,
        "ac": 15,
        "signature_abilities": [
            "Bad Breath (30ft fetid green miasma cone; DC 16 CON/WIS save or simultaneously suffer Poisoned, Blinded, Silenced, Slowed, and Confused for 2 rounds!)",
            "Digestive Vine-Chomp & Swamp Regeneration"
        ],
        "lore": "Writhing green tentacled plant-horrors with a cavernous maw of yellow teeth and数十 bloodshot eyes, wallowing in the toxic fens of the Great Swamp and the Pine Barrens.",
        "habitats": ["great_swamp_lord_stirling", "pine_barrens_wharton_wilds", "pine_barrens_bog_iron_furnaces"],
        "loot_drops": ["Malboro Bad-Breath Bile Sac", "Malboro Tentacle Vine"],
        "graft_id": "malboro_bad_breath_gland"
    },
    "ff_cactuar_coeurl_iron_giant": {
        "id": "ff_cactuar_coeurl_iron_giant",
        "name": "Gigantuar (1,000 Needles), Coeurl & Iron Giant",
        "origin": "Final Fantasy Series",
        "type": "Construct / Magical Beast",
        "cr_level": 17,
        "hp": 165,
        "ac": 19,
        "signature_abilities": [
            "1,000 Needles / 10,000 Needles (Gigantuar fires a barrage of needles dealing fixed True Piercing damage unless interrupted)",
            "Coeurl Whisker Blaster (Long-whipped electric whiskers discharge a DC 15 CON paralyzing lightning pulse)",
            "Iron Giant Grand Sword Cleave (15ft sweeping greatsword cleave that halves armor durability)"
        ],
        "lore": "Iconic Eorzean/Spiran threats: needle-firing Cactuars in the sandy barrens of Warren Grove, electric-whiskered Coeurl panthers in the Sourland boulders, and towering Iron Giants in Bethlehem Steel.",
        "habitats": ["warren_grove_bombardment_crater", "sourland_devils_half_acre", "bethlehem_steel_titan_forge", "phoenixville_foundry_lock60"],
        "loot_drops": ["Gigantuar Needle Bundle", "Coeurl Galvanic Whisker", "Iron Giant Greatsword Shard"],
        "graft_id": "leyline_conduit_spine"
    },

    # -------------------------------------------------------------------------
    # MONSTER HUNTER SERIES — WYVERNS, FANGED BEASTS & ELDER DRAGONS
    # -------------------------------------------------------------------------
    "mh_rathalos_rathian": {
        "id": "mh_rathalos_rathian",
        "name": "Rathalos ('King of the Skies') & Rathian",
        "origin": "Monster Hunter Series",
        "type": "Flying Wyvern",
        "cr_level": 20,
        "hp": 230,
        "ac": 18,
        "signature_abilities": [
            "Aerial Homing Poison-Talon Swoop (Dives from 60ft, inflicting 3d8 slashing + 2d8 venom and Stun)",
            "Triple Wyvern-Fireball Barrage (Scorches a 20ft blast zone for 6d6 Fire damage)",
            "Rathian Backflip Tail-Spike (Severable tail! Dealing 40+ slashing damage to the tail severs it and disables poison backflips)"
        ],
        "lore": "Crimson-scaled male Flying Wyverns and emerald-scaled female Rathians that dominate the skies above the Kittatinny Ridge, Delaware Water Gap, and Lakehurst Hangars.",
        "habitats": ["hawk_mountain_aerie", "delaware_water_gap_tammany", "lakehurst_airship_hangar", "shawangunk_gunks_cliffs"],
        "loot_drops": ["Rathalos Flame-Marrow Sac", "Rathalos Ruby / Plate", "Rathian Venom-Spike"],
        "graft_id": "rathalos_flame_marrow_sac"
    },
    "mh_zinogre_thunderlord": {
        "id": "mh_zinogre_thunderlord",
        "name": "Zinogre (Thunderlord Fulgur-Wolf Wyvern)",
        "origin": "Monster Hunter Series",
        "type": "Fanged Wyvern",
        "cr_level": 21,
        "hp": 225,
        "ac": 18,
        "signature_abilities": [
            "Fulgurbug Charge & Ultra-Charged State (Howls to attract glowing blue Thunderbugs into its fur; once fully charged, gains +20ft speed and +2d10 Lightning on all claw/tail slams)",
            "Acrobatic Breakdance Tail-Slam & Lightning Orbs"
        ],
        "lore": "Blue-and-gold wolf-like Fanged Wyvern that prowls the high-voltage penstocks of Yards Creek, the 480-Gauss coils of Edison's Ogden Mine, and the storm ridges of the Poconos.",
        "habitats": ["yards_creek_hydro_siphon", "edison_ogden_mine", "lehigh_gorge_glen_onoko", "bell_labs_horn_antenna"],
        "loot_drops": ["Zinogre Fulgur-Capacitor Cortex", "Zinogre Skymerald", "Electro-Fur Pelt"],
        "graft_id": "zinogre_fulgur_capacitor"
    },
    "mh_nergigante_deviljho_rajang": {
        "id": "mh_nergigante_deviljho_rajang",
        "name": "Nergigante, Savage Deviljho & Furious Rajang",
        "origin": "Monster Hunter Series",
        "type": "Elder Dragon / Brute Wyvern / Fanged Beast",
        "cr_level": 30,
        "hp": 330,
        "ac": 20,
        "signature_abilities": [
            "Nergigante Regrowing Spikes & Dive-Bomb (White spikes harden to black iron; launches an airborne Dive-Bomb that shatters all spikes in a 30ft cone for 8d10 piercing/bludgeoning)",
            "Rajang Golden Super-Saiyan Rage & Lightning Beam (Hardens arms to bounce weapons and fires a 60ft golden plasma beam)",
            "Deviljho Dragon-Breath Cloud (Suppresses elemental weapon damage and crushes armor)"
        ],
        "lore": "Roaming apex invaders that hunt other high-level bosses across the 100-mile radius whenever a Sector Threat Alert spikes.",
        "habitats": ["warren_grove_bombardment_crater", "centralia_pioneer_breach", "catskill_high_peaks_overlook", "three_mile_island_limerick_reactors"],
        "loot_drops": ["Nergigante Regrowing Immortal Horn", "Rajang Golden Heart-Core", "Deviljho Crook"],
        "graft_id": "basalt_carapace_plating"
    },

    # -------------------------------------------------------------------------
    # SAO / LOTR / WARHAMMER / ELDER SCROLLS / SOULSBORNE ICONIC MONSTERS
    # -------------------------------------------------------------------------
    "sao_gleam_eyes_skull_reaper": {
        "id": "sao_gleam_eyes_skull_reaper",
        "name": "The Gleam Eyes & The Skull Reaper (Aincrad Floor Bosses)",
        "origin": "Sword Art Online (Aincrad)",
        "type": "Demon / Boss Construct",
        "cr_level": 35,
        "hp": 400,
        "ac": 20,
        "signature_abilities": [
            "The Gleam Eyes: Zanmato Greatsword Combo & Azure Demon-Flame Breath (Requires Sword Skill parries or Dual-Blades burst to interrupt its 4-hit combo)",
            "The Skull Reaper: Scythe-Arm Guillotine (Two massive bone-scythe forelimbs sweep a 20ft arc capable of one-shotting unshielded vanguards; 4 HP bars)"
        ],
        "lore": "Canonical Aincrad Floor 74 and Floor 75 raid horrors manifested by the Cardinal System inside the upper labyrinth tiers of the Manhattan Monolith, Picatinny Arsenal, and the deepest Pohatcong Vaults.",
        "habitats": ["manhattan_monolith_undercity", "picatinny_arsenal_citadel", "pohatcong_labyrinth", "brookhaven_rhic_collider"],
        "loot_drops": ["Gleam Eyes Demonic Horn", "Demon-God Zanmato Blade Core", "Skull Reaper Bone-Scythe Segment"],
        "graft_id": "gleam_eyes_demonic_horn"
    },
    "warhammer_skaven_doomwheel": {
        "id": "warhammer_skaven_doomwheel",
        "name": "Skaven Warlock-Engineer & Warp-Lightning Cannon / Doomwheel",
        "origin": "Warhammer Fantasy",
        "type": "Humanoid (Skaven Under-Empire)",
        "cr_level": 15,
        "hp": 140,
        "ac": 16,
        "signature_abilities": [
            "Warp-Lightning Blast (Fires unstable neon-green warpstone lightning dealing 5d8 lightning + radiation; on a natural 1, misfires and explodes!)",
            "Doomwheel Rolling Crush & Ratling Gun Suppression",
            "Vermintide Swarm Call"
        ],
        "lore": "Cackling rat-men techno-sorcerers from the Under-Empire who dug into the NYC Subway Undercity, Camp Evans radar bunkers, and the Morris Canal inclined tunnels to harvest glowing warpstone.",
        "habitats": ["manhattan_monolith_undercity", "camp_evans_infoage", "morris_canal_slipstreams", "tobyhanna_signal_depot"],
        "loot_drops": ["Refined Warpstone Capacitor", "Warlock Halberd Coil", "Titanium Wire Scrap"],
        "graft_id": "neural_overclock_cortex"
    },
    "tes_dwemer_centurion_daedroth": {
        "id": "tes_dwemer_centurion_daedroth",
        "name": "Dwemer Steam-Centurion, Spriggan Matron & Daedroth",
        "origin": "The Elder Scrolls Series",
        "type": "Construct / Daedra / Nature Spirit",
        "cr_level": 18,
        "hp": 195,
        "ac": 19,
        "signature_abilities": [
            "Centurion Superheated Steam-Breath (30ft cone of scalding brass-boiler steam dealing 5d8 fire/bludgeoning) & Hammer-Arm Smash",
            "Spriggan Matron Earth-Mother Heal (Restores 50% HP once per fight and charms nearby bears/sabrecats)"
        ],
        "lore": "Towering brass dwarven steam-automatons patrolling the subterranean boiler rooms of Friedensville, Scranton Steamtown, and Oxford Furnace, while glowing green Spriggan Matrons guard the Pine Barrens.",
        "habitats": ["friedensville_zinc_mines", "oxford_furnace_mines", "phoenixville_foundry_lock60", "pine_barrens_wharton_wilds"],
        "loot_drops": ["Dwemer Dynamo Core", "Spriggan Taproot", "Soul Gem (Grand)"],
        "graft_id": "golem_hydraulic_arm"
    },
    "lotr_nazgul_shelob_balrog": {
        "id": "lotr_nazgul_shelob_balrog",
        "name": "Nazgûl Ringwraith on Fell-Beast & Ungoliant Brood-Weaver",
        "origin": "Tolkien / Lord of the Rings",
        "type": "Undead / Magical Beast",
        "cr_level": 28,
        "hp": 260,
        "ac": 19,
        "signature_abilities": [
            "Black Breath of Despair (Aura of dread forces DC 17 WIS save or Disadvantage on all attacks and paralyzed with terror)",
            "Morgul-Blade Stab (Leaves a necrotic shard in the wound that turns the victim into a wraith unless treated by Arcane Triage / Kingsfoil)",
            "Ungoliant Light-Drinking Web (Absorbs magical light and drains mana)"
        ],
        "lore": "Black-cloaked Ringwraiths screeching on leathery Fell-Beasts above ruined fortress towers (Bannerman's Castle, Fort Hancock, Concrete City) and light-devouring giant spiders in the darkest mine shafts.",
        "habitats": ["bannerman_castle_pollepel", "concrete_city_nanticoke", "hibernia_mount_hope_mines", "hawk_mountain_aerie"],
        "loot_drops": ["Morgul-Iron Blade Shard", "Ungoliant Shadow-Silk", "Black Breath Essence"],
        "graft_id": "stalker_shadow_tendon"
    }
}


# =============================================================================
# 2. DISPERSED FANTASY RACES & MULTI-UNIVERSE MONSTER ECOLOGY PER ATLAS ZONE
# =============================================================================

ZONE_DISPERSED_ECOLOGY: Dict[str, Dict[str, Any]] = {
    # --- INNER CORE (0-25 MI) ---
    "washington_borough": {
        "resident_races": [
            "Pure Human", "Phrenic Human", "Deepforged Dwarf", "Aether-Touched Elf",
            "Lightfoot Halfling (Shire-Born)", "Clockwork Tinker Gnome", "MageTech Cyborg", "Synthetic Android"
        ],
        "dispersed_monsters": [
            "Mimic (Disguised as Scavenged Vending Crate outside Perimeter)",
            "Rust Monster Strays (Attracted to Route 31 Scrap Piles)"
        ],
        "apex_spawn": "Perimeter Breach Sieger: Hobgoblin Iron-Legionnaire Vanguard",
        "harvestable_grafts": ["Golem Hydraulic Arm", "Subdermal Carapace Weave"]
    },
    "belvidere_bastion": {
        "resident_races": [
            "Celestial Radiant (Aasimar)", "Pure Human", "Hobgoblin Iron-Legionnaire (Reformed Constable)",
            "Conrasu / Modron (Law-Arbiter)", "Deepforged Dwarf"
        ],
        "dispersed_monsters": [
            "River Troll (Lurking under the Delaware Riverton Bridge)",
            "Drowner Pack (Pequest Confluence Mudflats)"
        ],
        "apex_spawn": "The Pequest Bridge Troll Matriarch",
        "harvestable_grafts": ["Troll Regenerative Liver"]
    },
    "hackettstown_citadel": {
        "resident_races": [
            "Aether-Touched Elf", "Kitsune (Nine-Tailed Starlight Fox)", "Clockwork Tinker Gnome",
            "Lightfoot Halfling", "Tabaxi / Amurrun Caravan Traders"
        ],
        "dispersed_monsters": [
            "Displacer Beast (Patrolling the Musconetcong Gorge perimeter)",
            "Animated Sugar-Slimes & Mimics (Old Confectionery Warehouses)"
        ],
        "apex_spawn": "Alpha Displacer Panther of Stephens Woods",
        "harvestable_grafts": ["Displacer Tentacle Mantle"]
    },
    "phillipsburg_easton_confluence": {
        "resident_races": [
            "Deepforged Dwarf", "Golem Reborn", "Ysoki / Skaven Warp-Tinker (Rail-Switchers)",
            "Iron-Jaw Orc Dockworkers", "Tortle / Kappa River-Pilots"
        ],
        "dispersed_monsters": [
            "Chuul (Lurking beneath the Free Bridge piers)",
            "Rust Monster Pack (Gnawing on the Phillipsburg Rail Trestles)",
            "Dwemer Steam-Centurion (Rogue Roundhouse Sentinel)"
        ],
        "apex_spawn": "The Delaware-Lehigh Confluence Hydra (5-Headed River Wyrm)",
        "harvestable_grafts": ["Rust Monster Feeler Whip", "Golem Hydraulic Arm"]
    },
    "clinton_red_mill_refinery": {
        "resident_races": [
            "Sylvan Thornborn (Dryad)", "Svirfneblin (Deep Gnome Quarry-Delver)",
            "Clockwork Tinker Gnome", "Viera / Cait Sith Wood-Warden"
        ],
        "dispersed_monsters": [
            "Cockatrice & Eight-Legged Basilisk (Nesting in the 200-ft Limestone Quarry Cliffs)",
            "Water Weird & Nixie (Raritan South Branch Spillway)"
        ],
        "apex_spawn": "The Quarry-Cliff Elder Basilisk",
        "harvestable_grafts": ["Basilisk Venom Gland"]
    },
    "blairstown_frontier_outpost": {
        "resident_races": [
            "Trial-Mutated Monster Slayer (Witcher Conscript)", "Firbolg Primeval Warden",
            "Aarakocra / Strix Sky-Scout", "Lightfoot Halfling"
        ],
        "dispersed_monsters": [
            "Primeval Owlbear (Paulinskill Valley Woods)",
            "Noonwraith & Nightwraith (Haunting the Old Mill & Cedar Lake)",
            "Blink Dog Pack (Friendly Fey-Hounds hunting Displacer Beasts)"
        ],
        "apex_spawn": "The Cedar Lake Nightwraith Bride",
        "harvestable_grafts": ["Chimeric Beast Claws"]
    },
    "oxford_furnace_mines": {
        "resident_races": [
            "Deepforged Dwarf", "Kobold Dragon-Wrought Trapwright", "Ashen Duergar Scout", "Scrapper Goblinoid"
        ],
        "dispersed_monsters": [
            "Rust Monster (Feeding on 1741 Magnetite Slag)",
            "Carrion Crawler (Clinging to the Slope No. 3 Timber Ceilings)",
            "Ankheg & Umber Hulk Juvenile (Burrowing through the Magnetite Vein)",
            "Dwemer Steam-Centurion (Guarding the Hot-Blast Tuyere)"
        ],
        "apex_spawn": "Ignis-Vein: The Molten Pig-IronSalamander & Duergar Claim-Boss",
        "harvestable_grafts": ["Rust Monster Feeler Whip", "Silt-Marrow Geothermal Core", "Basalt Carapace Plating"]
    },
    "andover_waterloo_mine": {
        "resident_races": [
            "Deepforged Dwarf", "Ysoki / Skaven Canal-Scavengers", "Clockwork Tinker Gnome"
        ],
        "dispersed_monsters": [
            "Rust Monster", "Ochre Jelly & Black Pudding (Seeping from Hematite Pockets)",
            "Drowner Pack (Morris Canal Lock Chambers)"
        ],
        "apex_spawn": "The Waterloo Inclined-Plane Iron Golem",
        "harvestable_grafts": ["Rust Monster Feeler Whip", "Subdermal Carapace Weave"]
    },
    "hibernia_mount_hope_mines": {
        "resident_races": [
            "Ashen Duergar (Gray Dwarf Mind-Forger)", "Svirfneblin (Deep Gnome)",
            "Dhampir / Strigoi Scion", "Underdark Drow Outcast"
        ],
        "dispersed_monsters": [
            "Hook Horror Pack (Echolocating through the 2,800-ft New Leonard Shaft)",
            "Umber Hulk (Shearing through the 1710 Magnetite Stopes)",
            "Cloaker & Roper (Hanging among the 30,000 hibernating bats)",
            "Witcher Bruxa & Higher Vampire (Ruling the Deep Bat Hibernacula)"
        ],
        "apex_spawn": "Camazotz-Alpha & The Elder Bruxa of Mount Hope",
        "harvestable_grafts": ["Aether-Resonant Ocular", "Stalker Shadow-Tendon", "Chimeric Beast Claws"]
    },
    "friedensville_zinc_mines": {
        "resident_races": [
            "Deepforged Dwarf", "Golem Reborn", "Tortle / Kappa Diver"
        ],
        "dispersed_monsters": [
            "Dwemer Steam-Centurion (Patrolling the 1872 Cornish Engine House)",
            "Chuul & Kuo-Toa Whip (Inhabiting the flooded 300-ft Ueberroth Karst Pit)",
            "Gelatinous Cube (Scouring the dry dolomite galleries)"
        ],
        "apex_spawn": "THE PRESIDENT: 1872 Cornish Steam-Pumping Colossus",
        "harvestable_grafts": ["Golem Hydraulic Arm", "Pneuma-Filter Gill-Lung"]
    },
    "edison_ogden_mine": {
        "resident_races": [
            "MageTech Cyborg", "Synthetic Android", "Clockwork Tinker Gnome", "Ysoki / Skaven Warp-Tinker"
        ],
        "dispersed_monsters": [
            "Zinogre (Thunderlord Fulgur-Wolf charging off the 480-Gauss Electromagnets)",
            "Young Blue Dragon (Roosting atop Mill-House #1)",
            "Coeurl (Galvanic Whisker-Panther)",
            "Rust Monster"
        ],
        "apex_spawn": "Thunderlord Zinogre of Sparta Mountain & The Wizard's Briquette Automaton",
        "harvestable_grafts": ["Zinogre Fulgur-Capacitor", "Neural Overclock Cortex", "Leyline Conduit Spine"]
    },
    "sterling_hill_franklin_mines": {
        "resident_races": [
            "Underdark Drow (House Fluorescent)", "Svirfneblin (Deep Gnome Gem-Delver)",
            "Ashen Duergar", "Anadi / Arachne (Star-Silk Weaver)"
        ],
        "dispersed_monsters": [
            "Beholder / Eye Tyrant (Hovering in the glowing UV Rainbow Tunnel)",
            "Mind Flayer (Illithid Psion) & Intellect Devourers (2,550-ft Deep Marble Shaft)",
            "Drider & Phase Spider (Spinning UV-reactive webs across the open pit)",
            "Gelatinous Cube & Crystal Dragon Wyrmling"
        ],
        "apex_spawn": "Xanathar-Strain Eye Tyrant of the Rainbow Tunnel & The Prism-Wyrm",
        "harvestable_grafts": ["Beholder Central Anti-Magic Ocular", "Illithid Psionic Tentrils", "Aether-Resonant Ocular"]
    },
    "pohatcong_labyrinth": {
        "resident_races": [
            "Kobold Dragon-Wrought Trapwright", "Scrapper Goblinoid", "Ashen Tiefling Hexblade (Malakor)"
        ],
        "dispersed_monsters": [
            "Carrion Crawler & Hook Horror (Upper Calcified Galleries)",
            "Gelatinous Cube & Mimic (Runic Tripwire Corridor & Drainage Junction)",
            "Master Tonberry (Stalking the Echoing Reservoir with its green lantern!)",
            "Displacer Beast"
        ],
        "apex_spawn": "The Gilded Spire Overlord & Floor-Guardian Gleam-Eyes Echo",
        "harvestable_grafts": ["Tonberry Grudge Lantern", "Golem Hydraulic Arm", "Gleam Eyes Demonic Horn"]
    },
    "merrill_creek_blood_shroud": {
        "resident_races": [
            "Shade-Touched (Shadowstalker)", "Dhampir / Strigoi Scion",
            "Changeling / Faceless Mimic", "Underdark Drow Assassins"
        ],
        "dispersed_monsters": [
            "Primeval Aboleth / Alghollthu (Lurking at the bottom of the 225-ft Reservoir)",
            "Thassilonian Sinspawn & Boneclaw (Guarding the Blood Shroud Intake Tunnel)",
            "Cloaker & Gargoyle"
        ],
        "apex_spawn": "The Pale Whisper (Blood Shroud Leader) & The 225-Foot Abyssal Aboleth",
        "harvestable_grafts": ["Stalker Shadow-Tendon", "Pneuma-Filter Gill-Lung"]
    },
    "round_valley_sunken_ring": {
        "resident_races": [
            "Saurian Dredge (Lizardfolk / Iruxi)", "Tortle / Kappa", "Undine / Aquatic Elf"
        ],
        "dispersed_monsters": [
            "Alghollthu Veiled Master & Aboleth Brood (Parabolic Diabase Bowl)",
            "Chuul & Kuo-Toa Archpriest (Worshipping in the Drowned Village of McPherson)",
            "Seven-Headed Hydra & Witcher Kayran"
        ],
        "apex_spawn": "The Cushetunk Trench Kraken & Veiled Master Xoth",
        "harvestable_grafts": ["Pneuma-Filter Gill-Lung", "Basilisk Venom Gland"]
    },
    "yards_creek_hydro_siphon": {
        "resident_races": [
            "Sylph (Zephyr-Born)", "Conrasu / Modron", "Clockwork Tinker Gnome"
        ],
        "dispersed_monsters": [
            "Zinogre (Thunderlord Fulgur-Wolf prowling the 453-MW Penstocks)",
            "Blue Dragon Wyrmling & Storm Elemental",
            "Chuul (Upper Reservoir Mudflats during Daytime Drain)"
        ],
        "apex_spawn": "The Reversible Dynamo Archon & Apex Zinogre",
        "harvestable_grafts": ["Zinogre Fulgur-Capacitor", "Leyline Conduit Spine"]
    },
    "lost_river_caverns": {
        "resident_races": [
            "Svirfneblin (Deep Gnome)", "Underdark Drow", "Dhampir"
        ],
        "dispersed_monsters": [
            "Roper & Piercer Brood (Crystal Chapel Stalactites)",
            "Master Tonberry (Wandering the Unindexed Lost River underground stream)",
            "Beholder Spectator & Blind Cave Chuul"
        ],
        "apex_spawn": "The Blind Albino Cave-Leviathan & Master Tonberry of the Styx",
        "harvestable_grafts": ["Tonberry Grudge Lantern", "Aether-Resonant Ocular"]
    },
    "picatinny_arsenal_citadel": {
        "resident_races": [
            "Golem Reborn", "MageTech Cyborg", "Synthetic Android",
            "Hobgoblin Iron-Legionnaire", "Ysoki / Skaven Warlock-Engineer"
        ],
        "dispersed_monsters": [
            "Clockwork Goliath (Pathfinder 2E Siege Construct)",
            "Mimic (Disguised as Munitions Lockers in the 600 Bunker Igloos)",
            "Iron Giant & Crucible Ordovis Knight (Gorge Artillery Foundry)",
            "Rust Monster Swarm"
        ],
        "apex_spawn": "THE ORDNANCE COLOSSUS: 65mm Rail-Artillery Siege Titan",
        "harvestable_grafts": ["Golem Hydraulic Arm", "Spring-Loaded Golem Greaves", "Neural Overclock Cortex"]
    },
    "bethlehem_steel_titan_forge": {
        "resident_races": [
            "Deepforged Dwarf", "Hellforged Fiendblood (Tiefling)", "Ashen Duergar",
            "Golem Reborn", "Fire Giant Forge-Masters"
        ],
        "dispersed_monsters": [
            "Fire Giant Dreadnought & Iron Giant (Operating the five 200-ft Blast Furnaces)",
            "Adult Red Dragon & Balor Echo (Nested inside Blast Furnace #5)",
            "Salamander & Magma Mephit Pack",
            "Gorgon (Iron-Plated Bull)"
        ],
        "apex_spawn": "VULCAN-PRIME: The Five-Furnace Molten Bessemer Colossus",
        "harvestable_grafts": ["Silt-Marrow Geothermal Core", "Golem Hydraulic Arm", "Wyrm-Scale Sheath"]
    },
    "pohatcong_roaring_rock": {
        "resident_races": [
            "Scrapper Goblinoid", "Kobold Dragon-Wrought Trapwright",
            "Viera / Cait Sith Wood-Warden", "Firbolg Primeval Warden"
        ],
        "dispersed_monsters": [
            "Primeval Owlbear (Roaring Rock Brook Den)",
            "Goblin Boss, Bugbear Chief & Nekker Pack (Route 31 Overlook)",
            "Rust Monster & Ettercap",
            "Blink Dog"
        ],
        "apex_spawn": "Silt-Alpha & The Roaring Rock Owlbear Matriarch",
        "harvestable_grafts": ["Chimeric Beast Claws", "Rust Monster Feeler Whip"]
    },
    "jenny_jump_ghost_lake": {
        "resident_races": [
            "Shade-Touched (Shadowstalker / Fetchling)", "Trial-Mutated Monster Slayer (Witcher)",
            "Kitsune", "Sylvan Thornborn"
        ],
        "dispersed_monsters": [
            "Noonwraith, Nightwraith & Banshee (Shades of Death Road & Ghost Lake)",
            "Ancient Leshen (Jenny Jump Ridge Old-Growth)",
            "Displacer Beast & Will-o'-Wisp",
            "Green Hag Coven &Vanished Fairy-Cave Goblins"
        ],
        "apex_spawn": "The Mist-Weaver of Ghost Lake & The Jenny Jump Ancient Leshen",
        "harvestable_grafts": ["Displacer Tentacle Mantle", "Leshen Ancient Heartwood", "Stalker Shadow-Tendon"]
    },
    "hacklebarney_black_river": {
        "resident_races": [
            "Leshy (Immortal Nature Spirit)", "Firbolg Primeval Warden",
            "Deepforged Dwarf", "Anadi / Arachne"
        ],
        "dispersed_monsters": [
            "Regenerating River Troll & Venom Troll (Black River Hemlock Ravine)",
            "Phase Spider & Ettercap Brood",
            "Bulette / Landshark (Burrowing through the Glacial Boulder Gorge)",
            "Owlbear"
        ],
        "apex_spawn": "The Black-River Rhine-Troll & Gorge Bulette",
        "harvestable_grafts": ["Troll Regenerative Liver", "Phase Spider Ethereal Spinneret", "Bulette Dorsal Carapace"]
    },
    "morris_canal_slipstreams": {
        "resident_races": [
            "Ysoki / Skaven Warp-Tinker", "Tortle / Kappa", "Saurian Dredge (Lizardfolk)", "Clockwork Tinker Gnome"
        ],
        "dispersed_monsters": [
            "Drowner Pack & Vodnik (Inclined Plane Lock Chambers)",
            "Chuul & Giant Snapping Turtle",
            "Skaven Warlock-Engineer (Siphoning Hydro-Kinetic Leylines)"
        ],
        "apex_spawn": "The Plane-7 Turbine Kraken",
        "harvestable_grafts": ["Spring-Loaded Golem Greaves", "Pneuma-Filter Gill-Lung"]
    },
    "delaware_water_gap_tammany": {
        "resident_races": [
            "Goliath Crag-Walker", "Aarakocra / Strix Sky-Scout", "Tengu / Kenku", "Sylph (Zephyr-Born)"
        ],
        "dispersed_monsters": [
            "Royal Archgriffin & Wyvern (Mount Tammany & Mount Minsi 1,200-ft Cliffs)",
            "Rathalos ('King of the Skies') & Peryton",
            "Tarn Linnorm (Coiled inside the seven-glacial-kettle Sunfish Pond!)",
            "Fiend (Bies) & Primeval Owlbear"
        ],
        "apex_spawn": "The Sunfish Tarn Linnorm & Mount Tammany Archgriffin",
        "harvestable_grafts": ["Linnorm Curse-Heart", "Rathalos Flame-Marrow Sac", "Chimeric Beast Claws"]
    },
    "ringing_rocks_diabase": {
        "resident_races": [
            "Conrasu / Modron (Harmonic Shard)", "Goliath Crag-Walker", "Svirfneblin"
        ],
        "dispersed_monsters": [
            "Iron-Plated Gorgon & Eight-Legged Basilisk (7-Acre Sonorous Boulder Field)",
            "Bulette (Landshark)",
            "Crystalline Gargoyle & Sonic Yrthak"
        ],
        "apex_spawn": "The C-Sharp Harmonic Lith-Colossus & Elder Iron Gorgon",
        "harvestable_grafts": ["Bulette Dorsal Carapace", "Basilisk Venom Gland", "Basalt Carapace Plating"]
    },

    # --- WEST & NORTHWEST QUADRANT (25-100 MI) ---
    "stroudsburg_milford_gateways": {
        "resident_races": [
            "Viera / Cait Sith Wood-Warden", "Firbolg Primeval Warden",
            "Trial-Mutated Monster Slayer (Witcher)", "Aarakocra / Strix"
        ],
        "dispersed_monsters": [
            "Primeval Owlbear", "Werewolf Pack & Barghest (Brodhead Creek Border)",
            "Spriggan Matron (Grey Towers Pinchot Forest)"
        ],
        "apex_spawn": "The Brodhead Loup-Garou Alpha",
        "harvestable_grafts": ["Chimeric Beast Claws", "Stalker Shadow-Tendon"]
    },
    "jim_thorpe_mauch_chunk": {
        "resident_races": [
            "Deepforged Dwarf", "Clockwork Tinker Gnome", "Golem Reborn",
            "Dhampir / Strigoi Inquisitor", "Lightfoot Halfling"
        ],
        "dispersed_monsters": [
            "Handprint Wraith & Banshee (Cell #17 of the Old Mauch Chunk Dungeon Jail)",
            "Runaway Switchback Coal-Golem",
            "Crag Linnorm (Surrounding Lehigh Gorge Cliffs)"
        ],
        "apex_spawn": "The Warden-Lich of Cell #17",
        "harvestable_grafts": ["Spring-Loaded Golem Greaves", "Golem Hydraulic Arm"]
    },
    "eckley_miners_village": {
        "resident_races": [
            "Deepforged Dwarf", "Ashen Duergar Defectors", "Golem Reborn", "Kobold Trapwright"
        ],
        "dispersed_monsters": [
            "Ankheg & Black Pudding (Strip-Mine Culm Banks)",
            "Duergar Shock-Sapper Patrols",
            "Noonwraith of the Company Store"
        ],
        "apex_spawn": "The Breaker-Engine Siege Construct",
        "harvestable_grafts": ["Subdermal Carapace Weave"]
    },
    "scranton_steamtown_nexus": {
        "resident_races": [
            "Deepforged Dwarf", "Golem Reborn", "MageTech Cyborg",
            "Clockwork Tinker Gnome", "Ysoki / Skaven Rail-Tinkers"
        ],
        "dispersed_monsters": [
            "Dwemer Steam-Centurion & Clockwork Goliath (Outer Rail Yards)",
            "Purple Worm (Deep Lackawanna Valley Bedrock)",
            "Rust Monster"
        ],
        "apex_spawn": "Big Boy #4012: Awakened Mythic Steam-Dragon Locomotive",
        "harvestable_grafts": ["Golem Hydraulic Arm", "Silt-Marrow Geothermal Core"]
    },
    "vera_cruz_jasper_quarries": {
        "resident_races": [
            "Goliath Crag-Walker", "Sylvan Thornborn", "Leshy", "Yuan-Ti / Vishkanya"
        ],
        "dispersed_monsters": [
            "Eight-Legged Basilisk & Cockatrice (100 Prehistoric Jasper Pits)",
            "Flint-Fang Smilodon & Bulette",
            "Earth Elemental & Red-Jasper Gargoyle"
        ],
        "apex_spawn": "Ancient Lithic Sabretooth Alpha & Jasper Basilisk",
        "harvestable_grafts": ["Basilisk Venom Gland", "Bulette Dorsal Carapace", "Chimeric Beast Claws"]
    },
    "lansford_no9_coal_mine": {
        "resident_races": [
            "Ashen Duergar (Gray Dwarf Mind-Forger)", "Deepforged Dwarf",
            "Golem Reborn (Doc Gallagher)", "Kobold Trapwright"
        ],
        "dispersed_monsters": [
            "Umber Hulk & Hook Horror (60-ft Mammoth Coal Vein Cathedral)",
            "Gelatinous Cube & Black-Damp Ooze (1,600-ft Haulage Drift)",
            "Master Tonberry (Stalking the flooded 800-ft vertical shaft sumps)",
            "Cloaker"
        ],
        "apex_spawn": "Duergar Warlord Krag-Nine & The Mammoth-Seam Umber Hulk",
        "harvestable_grafts": ["Tonberry Grudge Lantern", "Pneuma-Filter Gill-Lung", "Aether-Resonant Ocular"]
    },
    "huber_breaker_lackawanna_mine": {
        "resident_races": [
            "Ashen Duergar", "Deepforged Dwarf", "Underdark Drow", "Shade-Touched"
        ],
        "dispersed_monsters": [
            "Arch-Lich & Boneclaw (11-Story Phantom Huber Breaker)",
            "Purple Worm & Umber Hulk (#190 Slope 90-Degree Curve)",
            "Black Pudding & Wraith"
        ],
        "apex_spawn": "The Breaker-Lord of Ashley (11th-Floor Mechanized Lich-Crusher)",
        "harvestable_grafts": ["Neural Overclock Cortex", "Basalt Carapace Plating"]
    },
    "centralia_pioneer_breach": {
        "resident_races": [
            "Hellforged Fiendblood (Tiefling)", "Ashen Dunmer / Eldar Star-Weaver",
            "Deepforged Dwarf", "Ashen Duergar"
        ],
        "dispersed_monsters": [
            "Balor / Valaraukar Balrog of the Deep Seam (300-ft Buck Mountain Fire Pit!)",
            "Ancient Red Dragon & Pit Fiend",
            "Final Fantasy Bomb / Grenade Swarms & Hell Hounds (Buckled Route 61 Graffiti Highway)",
            "Savage Deviljho & Fire Giant"
        ],
        "apex_spawn": "IGNIS-62: The Undying Seam-Wyrm & The Balrog of Centralia",
        "harvestable_grafts": ["Silt-Marrow Geothermal Core", "Wyrm-Scale Sheath", "Rathalos Flame-Marrow Sac"]
    },
    "lehigh_tunnel_penns_peak": {
        "resident_races": [
            "Kobold Dragon-Wrought Trapwright", "Scrapper Goblinoid", "Aarakocra / Strix"
        ],
        "dispersed_monsters": [
            "Carrion Crawler & Hook Horror (4,379-ft Sealed Turnpike Bore)",
            "Wyvern & Royal Archgriffin (Penn's Peak 1,400-ft Overlook)",
            "Mimic (Abandoned Toll-Plaza Booths)"
        ],
        "apex_spawn": "The Turnpike Bore Wyrm & Penn's Peak Wyvern Matriarch",
        "harvestable_grafts": ["Chimeric Beast Claws", "Basilisk Venom Gland"]
    },
    "tobyhanna_signal_depot": {
        "resident_races": [
            "Synthetic Android", "MageTech Cyborg", "Conrasu / Modron", "Ysoki / Skaven Warlock-Engineer"
        ],
        "dispersed_monsters": [
            "Clockwork Goliath & Modron Marut Inevitable (Radar Parabolic Domes)",
            "Skaven Warp-Lightning Doomwheel",
            "Zinogre & Galvanic Coeurl"
        ],
        "apex_spawn": "AETHER-OMEGA: The 1,400-Acre Signal-Core Titan",
        "harvestable_grafts": ["Neural Overclock Cortex", "Leyline Conduit Spine", "Zinogre Fulgur-Capacitor"]
    },
    "crystal_cave_indian_echo": {
        "resident_races": [
            "Svirfneblin (Deep Gnome)", "Underdark Drow", "Anadi / Arachne"
        ],
        "dispersed_monsters": [
            "Roper & Piercer Brood (Milky-White Aragonite Stalactite Ceilings)",
            "Drider & Hook Horror",
            "Beholder Spectator & Mimic (Hermit Wilson's Cavern Vault)"
        ],
        "apex_spawn": "The Crystal-Ribbed Drider Matriarch",
        "harvestable_grafts": ["Phase Spider Ethereal Spinneret", "Aether-Resonant Ocular"]
    },
    "concrete_city_nanticoke": {
        "resident_races": [
            "Golem Reborn", "Dhampir", "Shade-Touched"
        ],
        "dispersed_monsters": [
            "Thassilonian Sinspawn & Fleshwarp Grothlut (20 Poured-Concrete Ghost Rowhomes)",
            "Stone Golem, Gargoyle & Mimic",
            "Nazgûl Ringwraith & Nightwraith (Central Courtyard)"
        ],
        "apex_spawn": "The Poured-Concrete Behemoth of 1911",
        "harvestable_grafts": ["Basalt Carapace Plating", "Subdermal Carapace Weave"]
    },
    "archbald_pothole_shaft": {
        "resident_races": [
            "Deepforged Dwarf", "Svirfneblin", "Tortle / Kappa"
        ],
        "dispersed_monsters": [
            "Remorhaz & Ice Linnorm (38-ft Glacial Whirlpool Borehole)",
            "Roper & Aboleth Spawn (Subterranean Whirlpool Sump)"
        ],
        "apex_spawn": "Charybdis of the Glacial Shaft",
        "harvestable_grafts": ["Linnorm Curse-Heart", "Pneuma-Filter Gill-Lung"]
    },
    "high_point_stokes_ridge": {
        "resident_races": [
            "Goliath Crag-Walker", "Aarakocra / Strix", "Sylph", "Firbolg"
        ],
        "dispersed_monsters": [
            "Ancient Wendigo (1,803-ft High Point Obelisk in Blizzard Weather)",
            "Winter Wolf Pack, Frost Giant & Remorhaz",
            "Royal Archgriffin"
        ],
        "apex_spawn": "The High-Point Wendigo & Frost-Giant Jarl",
        "harvestable_grafts": ["Chimeric Beast Claws", "Wyrm-Scale Sheath"]
    },
    "bushkill_promised_land": {
        "resident_races": [
            "Viera / Cait Sith Wood-Warden", "Tabaxi / Amurrun",
            "Firbolg Primeval Warden", "Leshy"
        ],
        "dispersed_monsters": [
            "Witcher Fiend (Bies) & Chort (Promised Land Beech Forests)",
            "Primeval Owlbear & Displacer Beast (Eight Waterfalls of Bushkill)",
            "Water Nymph & Spriggan Matron"
        ],
        "apex_spawn": "The Promised-Land Three-Eyed Fiend Alpha",
        "harvestable_grafts": ["Displacer Tentacle Mantle", "Aether-Resonant Ocular"]
    },
    "lehigh_gorge_glen_onoko": {
        "resident_races": [
            "Aarakocra / Strix", "Tengu / Kenku", "Goliath Crag-Walker"
        ],
        "dispersed_monsters": [
            "Crag Linnorm & Tarn Linnorm (Glen Onoko 900-ft Terraced Cascades)",
            "Zinogre (Thunderlord Fulgur-Wolf) & Wyvern",
            "River Troll"
        ],
        "apex_spawn": "The Glen Onoko Cascade Linnorm",
        "harvestable_grafts": ["Linnorm Curse-Heart", "Zinogre Fulgur-Capacitor", "Troll Regenerative Liver"]
    },
    "hickory_run_boulder_field": {
        "resident_races": [
            "Goliath Crag-Walker", "Conrasu / Modron", "Deepforged Dwarf"
        ],
        "dispersed_monsters": [
            "Bulette / Landshark (Swimming through the 16-Acre Treeless Sandstone Boulder Sea!)",
            "Stone Giant Elders (Playing Boulder-Catch across the 1,800-ft Flat Expanse)",
            "King Behemoth & Eight-Legged Basilisk"
        ],
        "apex_spawn": "The 16-Acre Elder Bulette & King Behemoth of Hickory Run",
        "harvestable_grafts": ["Bulette Dorsal Carapace", "Basalt Carapace Plating"]
    },
    "hawk_mountain_aerie": {
        "resident_races": [
            "Aarakocra / Strix (Raptor-Born Sky-Scout)", "Tengu / Kenku", "Sylph"
        ],
        "dispersed_monsters": [
            "Rathalos ('King of the Skies') & Rathian (North Lookout 1,500-ft Updrafts)",
            "Colossal D&D Roc (60-ft Wingspan) & Royal Archgriffin",
            "Nazgûl Fell-Beast Rider (During Eclipse / Storm Events)"
        ],
        "apex_spawn": "Dreadking Rathalos & The Kittatinny Sovereign Roc",
        "harvestable_grafts": ["Rathalos Flame-Marrow Sac", "Wyrm-Scale Sheath"]
    },
    "ricketts_glen_falls": {
        "resident_races": [
            "Sylvan Thornborn (Dryad)", "Firbolg Primeval Warden",
            "Leshy (Immortal Nature Spirit)", "Viera / Cait Sith Wood-Warden"
        ],
        "dispersed_monsters": [
            "Ancient Leshen (Guarding the 500-Year-Old Giant Hemlocks & 94-ft Ganoga Falls)",
            "Treant / Ent, Displacer Beast & Shambling Mound",
            "Adult Green Dragon & Spriggan Matron"
        ],
        "apex_spawn": "The Ganoga Falls Ancient Leshen & Elder Treant",
        "harvestable_grafts": ["Leshen Ancient Heartwood", "Displacer Tentacle Mantle"]
    },

    # --- NORTH & EAST QUADRANT (25-100 MI) ---
    "morristown_jockey_hollow": {
        "resident_races": [
            "Pure Human", "Aether-Touched Elf", "Hobgoblin Iron-Legionnaire (Vanguard Allies)",
            "Deepforged Dwarf", "Celestial Radiant (Aasimar)"
        ],
        "dispersed_monsters": [
            "Winter Wolf & Wight (Outer Wicked-Winter Palisade Perimeter)",
            "Clockwork Cavalry Steeds"
        ],
        "apex_spawn": "The Continental Phantom General",
        "harvestable_grafts": ["Subdermal Carapace Weave"]
    },
    "west_point_granite_bastion": {
        "resident_races": [
            "Pure Human", "Deepforged Dwarf", "Golem Reborn",
            "Celestial Radiant (Aasimar)", "Hobgoblin Iron-Legionnaire"
        ],
        "dispersed_monsters": [
            "Adult Silver Dragon (Allied Guardian of the Plain & Bullion Vaults)",
            "Chuul & Kraken Spawn (Attempting to breach the Great Hudson Iron Chain)"
        ],
        "apex_spawn": "The Hudson Chain Leviathan",
        "harvestable_grafts": ["Wyrm-Scale Sheath", "Golem Hydraulic Arm"]
    },
    "new_paltz_mohonk_citadel": {
        "resident_races": [
            "Aether-Touched Elf", "Aarakocra / Strix", "Kitsune",
            "Githzerai (Zerth Cenobite)", "Goliath Crag-Walker"
        ],
        "dispersed_monsters": [
            "Adult Gold / Silver Dragon (Sky-Top Tower Roost)",
            "Royal Archgriffin & Peryton (Shawangunk Quartz Crevices)",
            "Roper (Labyrinth Lemon-Squeeze Crevice)"
        ],
        "apex_spawn": "The Sky-Top Quartz Wyvern",
        "harvestable_grafts": ["Aether-Resonant Ocular", "Wyrm-Scale Sheath"]
    },
    "kingston_rondout_harbor": {
        "resident_races": [
            "Tortle / Kappa", "Tabaxi / Amurrun Privateers",
            "Lightfoot Halfling", "Deepforged Dwarf"
        ],
        "dispersed_monsters": [
            "Sahuagin Baron & Chuul (Hudson-Rondout Lighthouse Shoals)",
            "Drowner Pack & Ghost-Barge Specters"
        ],
        "apex_spawn": "The Rondout Sunken Dreadnought Kraken",
        "harvestable_grafts": ["Pneuma-Filter Gill-Lung"]
    },
    "watchung_copper_mines": {
        "resident_races": [
            "Clockwork Tinker Gnome", "Kobold Dragon-Wrought Trapwright", "Svirfneblin"
        ],
        "dispersed_monsters": [
            "Blue Dragon Wyrmling & Galvanic Coeurl (Trap-Rock Basalt Seams)",
            "Rust Monster & Ankheg",
            "Gorgon"
        ],
        "apex_spawn": "The Watchung Copper-Clad Gorgon",
        "harvestable_grafts": ["Leyline Conduit Spine", "Rust Monster Feeler Whip"]
    },
    "harriman_iron_mines": {
        "resident_races": [
            "Ashen Duergar", "Deepforged Dwarf", "Hobgoblin Iron-Legionnaire", "Iron-Jaw Orc"
        ],
        "dispersed_monsters": [
            "Umber Hulk, Hook Horror & Cloaker (Forest of Dean & Doodletown Flooded Shafts)",
            "Regenerating Mountain Troll & Oni (Bear Mountain Ridges)",
            "Witcher Fiend (Bies)"
        ],
        "apex_spawn": "The Doodletown Mine-Pit Behemoth",
        "harvestable_grafts": ["Troll Regenerative Liver", "Basalt Carapace Plating"]
    },
    "tilly_foster_mine": {
        "resident_races": [
            "Deepforged Dwarf", "Golem Reborn", "Conrasu / Modron"
        ],
        "dispersed_monsters": [
            "Purple Worm & Umber Hulk (600-ft Flooded Magnetite Crater)",
            "Aboleth & Chuul (Submerged Steam-Hoist Cranes)"
        ],
        "apex_spawn": "The 1895 Landslide Magnetite Leviathan",
        "harvestable_grafts": ["Golem Hydraulic Arm", "Basalt Carapace Plating"]
    },
    "rosendale_widow_jane_mines": {
        "resident_races": [
            "Svirfneblin (Deep Gnome)", "Underdark Drow", "Tortle / Kappa", "Dhampir"
        ],
        "dispersed_monsters": [
            "Primeval Aboleth & Kuo-Toa Archpriest (Subterranean Flooded Pillared Amphitheater)",
            "Cloaker, Roper & Banshee (Widow Jane Acoustic Cavern)",
            "Master Tonberry"
        ],
        "apex_spawn": "Widow Jane's Singing Banshee & The Dolostone Aboleth",
        "harvestable_grafts": ["Pneuma-Filter Gill-Lung", "Tonberry Grudge Lantern"]
    },
    "bell_labs_horn_antenna": {
        "resident_races": [
            "Githyanki (Astral Silver-Blade)", "Githzerai", "Synthetic Android",
            "Conrasu / Modron", "Phrenic Human"
        ],
        "dispersed_monsters": [
            "Mind Flayer (Illithid Arcanist) & Neh-Thalggu Brain Collector (Crawford Hill Horn Antenna!)",
            "Hound of Tindalos (Emerging from the transistor cleanroom angles)",
            "Zinogre & Pleroma Aeon"
        ],
        "apex_spawn": "The 3-Kelvin Cosmic Background Aeon & Illithid Savant",
        "harvestable_grafts": ["Illithid Psionic Tentrils", "Neural Overclock Cortex"]
    },
    "sandy_hook_fort_hancock": {
        "resident_races": [
            "Tortle / Kappa", "Saurian Dredge (Lizardfolk)", "Golem Reborn", "Pure Human"
        ],
        "dispersed_monsters": [
            "Storm Giant & Adult Bronze Dragon (Atlantic Spit & Disappearing Gun Batteries)",
            "Kraken Tentacle-Brood & Sahuagin",
            "Nazgûl Fell-Beast & Clockwork Missile-Silo Golems"
        ],
        "apex_spawn": "The Fort Hancock Nike-Missile Leviathan",
        "harvestable_grafts": ["Wyrm-Scale Sheath", "Golem Hydraulic Arm"]
    },
    "camp_evans_infoage": {
        "resident_races": [
            "Ysoki / Skaven Warp-Tinker", "MageTech Cyborg", "Synthetic Android", "Dhampir"
        ],
        "dispersed_monsters": [
            "Skaven Warlock-Engineer & Warp-Lightning Cannon (Marconi H-Bunkers)",
            "Thassilonian Sinspawn, Fleshwarp Grothlut & Phase Spider",
            "Flameskull & Allip (Diana Radar Dish)"
        ],
        "apex_spawn": "The Project-Diana Lunar Specter & Skaven Warlock Ikit-Strain",
        "harvestable_grafts": ["Phase Spider Ethereal Spinneret", "Neural Overclock Cortex"]
    },
    "bannerman_castle_pollepel": {
        "resident_races": [
            "Hobgoblin Iron-Legionnaire", "Kobold Trapwright", "Tengu / Kenku"
        ],
        "dispersed_monsters": [
            "Death Knight, Arch-Lich & Mimic (Ruined Scottish Ordnance Arsenal)",
            "Final Fantasy Bomb / Grenade Swarms (Black-Powder Magazines)",
            "Nazgûl Fell-Beast Rider & Wyvern"
        ],
        "apex_spawn": "Lord Bannerman's Munitions Death-Knight",
        "harvestable_grafts": ["Silt-Marrow Geothermal Core", "Spring-Loaded Golem Greaves"]
    },
    "sams_point_ice_caves": {
        "resident_races": [
            "Goliath Crag-Walker", "Deepforged Dwarf", "Sylph"
        ],
        "dispersed_monsters": [
            "Remorhaz & Ice Linnorm (Permafrost Fault Crevices)",
            "Adult White Dragon & Frost Giant (Verkeerderkill 180-ft Frozen Falls)",
            "Winter Wolf Pack"
        ],
        "apex_spawn": "The Sam's Point Permafrost Remorhaz & White Wyrm",
        "harvestable_grafts": ["Linnorm Curse-Heart", "Wyrm-Scale Sheath"]
    },
    "manhattan_monolith_undercity": {
        "resident_races": [
            "Underdark Drow", "Ysoki / Skaven Under-Empire", "Githyanki Astral Raiders",
            "Dhampir / Higher Vampire Court", "MageTech Cyborg", "Synthetic Android"
        ],
        "dispersed_monsters": [
            "The Gleam Eyes & The Skull Reaper (Aincrad Bosses in the Crystalline Monolith Spire!)",
            "Beholder Eye Tyrant & Elder Brain Overmind (Grand Central Abyssal Terminal)",
            "King Behemoth & Arch-Lich (Times Square Crystalline Crater)",
            "Skaven Doomwheel & Purple Worm (Subway Deep-Bore Tunnels)"
        ],
        "apex_spawn": "THE GLEAM EYES, THE SKULL REAPER & THE GRAND CENTRAL ELDER BRAIN",
        "harvestable_grafts": ["Gleam Eyes Demonic Horn", "Beholder Central Anti-Magic Ocular", "Illithid Psionic Tentrils"]
    },
    "brookhaven_rhic_collider": {
        "resident_races": [
            "Githyanki (Astral Silver-Blade)", "Githzerai", "Conrasu / Modron",
            "Void-Walker (Singularity Drifter)", "Synthetic Android"
        ],
        "dispersed_monsters": [
            "Elder Brain Overmind & Mind Flayer Nautiloid Dreadnought (2.4-Mile RHIC Collider Ring!)",
            "Pleroma Aeon, Protean Imentesh & Hound of Tindalos",
            "The Skull Reaper & Shinryu / Bahamut Prime Echo"
        ],
        "apex_spawn": "ASTRAL NAUTILOID OVERMIND & QUARK-GLUON BAHAMUT ECHO",
        "harvestable_grafts": ["Illithid Psionic Tentrils", "Neural Overclock Cortex", "Leyline Conduit Spine"]
    },
    "great_swamp_lord_stirling": {
        "resident_races": [
            "Saurian Dredge (Lizardfolk / Iruxi)", "Tortle / Kappa",
            "Leshy", "Witcher Conscript"
        ],
        "dispersed_monsters": [
            "Great Malboro (Exhaling Bad Breath clouds across the Glacial Lake Passaic Fen!)",
            "Adult Black Dragon, Hydra & Pathfinder Boggard Swampseer",
            "Shambling Mound, Regenerating Swamp Troll & Drowner Pack"
        ],
        "apex_spawn": "The Great Swamp Black Wyrm & Elder Great Malboro",
        "harvestable_grafts": ["Malboro Bad-Breath Gland", "Troll Regenerative Liver", "Basilisk Venom Gland"]
    },
    "watchung_feltville_deserted": {
        "resident_races": [
            "Shade-Touched", "Dhampir", "Trial-Mutated Monster Slayer (Witcher)", "Kitsune"
        ],
        "dispersed_monsters": [
            "Noonwraith, Nightwraith & Banshee (1845 Deserted Village of Feltville)",
            "Green Hag Coven (13 Pillars of the Enchanted Forest)",
            "Phase Spider & Vanth Psychopomp"
        ],
        "apex_spawn": "The thirteen-Pillar Arch-Hag of Feltville",
        "harvestable_grafts": ["Phase Spider Ethereal Spinneret", "Stalker Shadow-Tendon"]
    },
    "palisades_diabase_cliffs": {
        "resident_races": [
            "Goliath Crag-Walker", "Aarakocra / Strix", "Tengu / Kenku"
        ],
        "dispersed_monsters": [
            "Stone Giant & Cloud Giant (500-ft Columnar Diabase Cliffs)",
            "Wyvern, Manticore & Royal Archgriffin",
            "Gorgon"
        ],
        "apex_spawn": "The Palisades Columnar Stone-Titan",
        "harvestable_grafts": ["Basalt Carapace Plating", "Golem Hydraulic Arm"]
    },
    "harriman_bear_mountain": {
        "resident_races": [
            "Firbolg Primeval Warden", "Iron-Jaw Orc", "Goliath Crag-Walker", "Tabaxi / Amurrun"
        ],
        "dispersed_monsters": [
            "Witcher Fiend (Bies), Chort & Primeval Owlbear (Seven Lakes Drive Wilderness)",
            "Regenerating Troll, Oni & Gnoll Pack",
            "Displacer Beast"
        ],
        "apex_spawn": "The Bear-Mountain Chort Behemoth",
        "harvestable_grafts": ["Troll Regenerative Liver", "Displacer Tentacle Mantle", "Chimeric Beast Claws"]
    },
    "shawangunk_gunks_cliffs": {
        "resident_races": [
            "Aarakocra / Strix", "Goliath Crag-Walker", "Tengu / Kenku", "Sylph"
        ],
        "dispersed_monsters": [
            "Royal Archgriffin, Rathalos & Rathian (250-ft White Quartz Cliffs)",
            "Crag Linnorm & Peryton",
            "Gargoyle"
        ],
        "apex_spawn": "The Trapps White-Quartz Rathalos",
        "harvestable_grafts": ["Rathalos Flame-Marrow Sac", "Linnorm Curse-Heart"]
    },
    "catskill_high_peaks_overlook": {
        "resident_races": [
            "Goliath Crag-Walker", "Firbolg Primeval Warden", "Yuan-Ti / Vishkanya", "Sylvan Thornborn"
        ],
        "dispersed_monsters": [
            "Eight-Legged Basilisk, Medusa & Yuan-Ti Abomination (1928 Overlook Mountain Hotel Ruins!)",
            "Stone Giant, Cloud Giant & Ancient Wendigo (4,180-ft Slide Mountain)",
            "Hydra & Kayran (12 Flooded Villages of the Ashokan Reservoir)",
            "Nergigante & Crag Linnorm"
        ],
        "apex_spawn": "The Ashokan Twelve-Village Hydra & Overlook Medusa Queen",
        "harvestable_grafts": ["Basilisk Venom Gland", "Linnorm Curse-Heart", "Aether-Resonant Ocular"]
    },

    # --- SOUTH & SOUTHWEST QUADRANT (25-100 MI) ---
    "new_hope_lambertville_bazaar": {
        "resident_races": [
            "Changeling / Faceless Mimic", "Kitsune (Nine-Tailed Fox)",
            "Tabaxi / Amurrun Smugglers", "Dhampir", "Tiefling", "Underdark Drow Brokers"
        ],
        "dispersed_monsters": [
            "Rakshasa (Running High-Stakes Black-Market Auctions in Disguise)",
            "Mimic & Drowner Pack (Delaware Canal Locks)"
        ],
        "apex_spawn": "Maharaja Rakshasa of the Toll-Bridge Bazaar",
        "harvestable_grafts": ["Stalker Shadow-Tendon", "Aether-Resonant Ocular"]
    },
    "princeton_arcane_conclave": {
        "resident_races": [
            "Aether-Touched Elf", "Ashen Dunmer / Eldar Star-Weaver",
            "Clockwork Tinker Gnome", "Celestial Radiant (Aasimar)",
            "Githzerai", "Kitsune", "Conrasu / Modron"
        ],
        "dispersed_monsters": [
            "Adult Gold Dragon (Allied Conclave Lorekeeper atop Nassau Hall)",
            "Animated Gothic Gargoyles & Shield Guardians"
        ],
        "apex_spawn": "Arch-Chancellor's Runic Shield-Colossus",
        "harvestable_grafts": ["Leyline Conduit Spine", "Neural Overclock Cortex"]
    },
    "valley_forge_star_redoubt": {
        "resident_races": [
            "Pure Human", "Hobgoblin Iron-Legionnaire", "Deepforged Dwarf",
            "Goliath Crag-Walker", "Draconic Scion (Dragonborn)"
        ],
        "dispersed_monsters": [
            "Iron Giant & Clockwork Artillery Steeds (Schuylkill Perimeter)",
            "Wight & Revenant (Outer Entrenchments)"
        ],
        "apex_spawn": "The Star-Redoubt Siege Juggernaut",
        "harvestable_grafts": ["Golem Hydraulic Arm", "Subdermal Carapace Weave"]
    },
    "batsto_pine_barrens_bastion": {
        "resident_races": [
            "Firbolg Primeval Warden", "Viera / Cait Sith Wood-Warden",
            "Leshy (Bog-Moss & Cedar Spirit)", "Trial-Mutated Monster Slayer (Witcher)", "Deepforged Dwarf"
        ],
        "dispersed_monsters": [
            "Ancient Leshen & Shambling Mound (Mullica River Perimeter)",
            "Great Malboro & Bog-Iron Golem"
        ],
        "apex_spawn": "The Batsto Bog-Iron Guardian Colossus",
        "harvestable_grafts": ["Leshen Ancient Heartwood", "Basalt Carapace Plating"]
    },
    "mercer_mile_castles": {
        "resident_races": [
            "Golem Reborn", "Clockwork Tinker Gnome", "Dhampir / Strigoi Scion", "Anadi / Arachne"
        ],
        "dispersed_monsters": [
            "Mimic & Animated Armor Swarm (6-Story Mercer Museum Atrium of 40,000 Tools!)",
            "Higher Vampire, Bruxa & Gargoyle (44-Room Concrete Fonthill Castle)",
            "Hound of Tindalos (Non-Euclidean Concrete Stairwells)"
        ],
        "apex_spawn": "The Suspended Whaleboat Leviathan & Count Mercer's Higher Vampire Echo",
        "harvestable_grafts": ["Basalt Carapace Plating", "Stalker Shadow-Tendon"]
    },
    "phoenixville_foundry_lock60": {
        "resident_races": [
            "Deepforged Dwarf", "Golem Reborn", "MageTech Cyborg", "Tortle / Kappa"
        ],
        "dispersed_monsters": [
            "Final Fantasy Iron Giant & Dwemer Steam-Centurion (1882 Foundry Truss Hall)",
            "Rust Monster & Chuul (Schuylkill Canal Lock 60)",
            "Clockwork Goliath"
        ],
        "apex_spawn": "The Riveted Phoenix-Column Colossus of Lock 60",
        "harvestable_grafts": ["Golem Hydraulic Arm", "Spring-Loaded Golem Greaves", "Rust Monster Feeler Whip"]
    },
    "hopewell_french_creek_mines": {
        "resident_races": [
            "Svirfneblin (Deep Gnome)", "Anadi / Arachne", "Deepforged Dwarf"
        ],
        "dispersed_monsters": [
            "Phase Spider, Drider & Ettercap (Green-Byssolite & Pyrite Mirror Caverns)",
            "Roper & Umber Hulk",
            "Fire Elemental (1771 Charcoal Blast Furnace)"
        ],
        "apex_spawn": "The Octahedral Pyrite Skarn-Spider Matriarch",
        "harvestable_grafts": ["Phase Spider Ethereal Spinneret", "Silt-Marrow Geothermal Core"]
    },
    "pine_barrens_bog_iron_furnaces": {
        "resident_races": [
            "Leshy", "Saurian Dredge (Lizardfolk)", "Deepforged Dwarf", "Firbolg"
        ],
        "dispersed_monsters": [
            "Great Malboro & Shambling Mound (Acidic Tea-Colored Cedar Swamps)",
            "Adult Black Dragon & Regenerating Bog-Troll (Martha & Weymouth Ruined Furnaces)",
            "Drowner Pack & Will-o'-Wisp"
        ],
        "apex_spawn": "The Weymouth Bog-Iron Black Wyrm",
        "harvestable_grafts": ["Malboro Bad-Breath Gland", "Troll Regenerative Liver", "Wyrm-Scale Sheath"]
    },
    "cornwall_iron_pit": {
        "resident_races": [
            "Deepforged Dwarf", "Ashen Duergar", "Conrasu / Modron"
        ],
        "dispersed_monsters": [
            "Purple Worm (Burrowing through the 500-ft Open-Pit Magnetite Amphitheater!)",
            "Iron-Plated Gorgon, Bulette & Zinogre (Tier-3 Geomagnetic Anomaly Zone)",
            "Aboleth & Kraken (Flooded Crater Bottom)"
        ],
        "apex_spawn": "Abyssal Pit-Leviathan 'Agnes' & The Cornwall Purple Worm",
        "harvestable_grafts": ["Bulette Dorsal Carapace", "Zinogre Fulgur-Capacitor", "Leyline Conduit Spine"]
    },
    "princeton_tokamak_pppl": {
        "resident_races": [
            "Githyanki (Astral Silver-Blade)", "Void-Walker (Singularity Drifter)",
            "Conrasu / Modron", "Synthetic Android", "Ashen Dunmer"
        ],
        "dispersed_monsters": [
            "King Behemoth (Calling down Ecliptic Meteors inside the Magnetic Fusion Hall!)",
            "Mind Flayer (Illithid Arcanist), Pleroma Aeon & Protean Imentesh",
            "Furious Rajang & Star-Spawn"
        ],
        "apex_spawn": "STAR-CORE PROMETHEUS: 100-Million-Kelvin Tokamak Archon & King Behemoth",
        "harvestable_grafts": ["Silt-Marrow Geothermal Core", "Illithid Psionic Tentrils", "Leyline Conduit Spine"]
    },
    "lakehurst_airship_hangar": {
        "resident_races": [
            "Sylph (Zephyr-Born)", "Aarakocra / Strix", "Tengu / Kenku", "Clockwork Tinker Gnome"
        ],
        "dispersed_monsters": [
            "Rathalos, Rathian & Kushala Daora (Nesting inside massive Hangar No. 1!)",
            "Adult Blue Dragon, Storm Giant & Wyvern",
            "Final Fantasy Bomb / Grenade Swarms (Hydrogen Mooring Mast)"
        ],
        "apex_spawn": "LZ-129 AETHER-LEVIATHAN: The Ghost-Dirigible Dreadnought & Apex Rathalos",
        "harvestable_grafts": ["Rathalos Flame-Marrow Sac", "Wyrm-Scale Sheath", "Spring-Loaded Golem Greaves"]
    },
    "eastern_state_penitentiary": {
        "resident_races": [
            "Dhampir / Strigoi Scion", "Shade-Touched", "Golem Reborn"
        ],
        "dispersed_monsters": [
            "Arch-Lich, Demilich & Death Knight (Central Panopticon Rotunda & 7 Radial Cellblocks!)",
            "Master Tonberry (Slowly stalking the solitary confinement corridors with its lantern!)",
            "Vanth Psychopomp Reaper, Nightwalker, Boneclaw & Witcher Hym"
        ],
        "apex_spawn": "THE PANOPTICON WARDEN-LICH & MASTER TONBERRY OF CELLBLOCK 7",
        "harvestable_grafts": ["Tonberry Grudge Lantern", "Neural Overclock Cortex", "Stalker Shadow-Tendon"]
    },
    "philadelphia_navy_yard_ghost_fleet": {
        "resident_races": [
            "Tortle / Kappa", "Saurian Dredge (Lizardfolk)", "MageTech Cyborg", "Golem Reborn"
        ],
        "dispersed_monsters": [
            "Kraken, Chuul & Sahuagin Baron (Reserve Basin Mothball Ghost-Fleet)",
            "Clockwork Goliath, Iron Giant & Mimic (Aircraft Carrier Hangar Decks)",
            "Drowned Draug & Ghost-Ship Wraiths"
        ],
        "apex_spawn": "DREADNOUGHT-CHIMERA BB-62: The Fused Battleship Leviathan",
        "harvestable_grafts": ["Golem Hydraulic Arm", "Pneuma-Filter Gill-Lung", "Subdermal Carapace Weave"]
    },
    "fort_mifflin_mud_island": {
        "resident_races": [
            "Tortle / Kappa", "Trial-Mutated Monster Slayer (Witcher)", "Pure Human"
        ],
        "dispersed_monsters": [
            "Banshee ('The Screaming Woman of Casemate 11'), Nightwraith & Wight",
            "Vanth Psychopomp & River Troll",
            "Drowner Pack (Delaware Mudflats)"
        ],
        "apex_spawn": "The Casemate-11 Banshee Sovereign & Hessian Revenant Commander",
        "harvestable_grafts": ["Troll Regenerative Liver"]
    },
    "three_mile_island_limerick_reactors": {
        "resident_races": [
            "Void-Walker", "Synthetic Android", "MageTech Cyborg", "Hellforged Tiefling"
        ],
        "dispersed_monsters": [
            "Savage Deviljho, Brachydios & Nergigante (500-ft Hyperbolic Cooling Towers!)",
            "Balor, Pit Fiend & Mutated Hydra",
            "Pathfinder Qlippoth & Astradaemon",
            "Dormant Tarrasque Bio-Signature (Sub-Reactor Bedrock Fault)"
        ],
        "apex_spawn": "CHERNOBOG-UNIT 2: The Meltdown Chimera & Nergigante",
        "harvestable_grafts": ["Silt-Marrow Geothermal Core", "Basalt Carapace Plating", "Gleam Eyes Demonic Horn"]
    },
    "sourland_devils_half_acre": {
        "resident_races": [
            "Hellforged Fiendblood (Tiefling)", "Trial-Mutated Monster Slayer (Witcher)",
            "Goliath Crag-Walker", "Kitsune"
        ],
        "dispersed_monsters": [
            "Bulette / Landshark & Galvanic Coeurl (Devil's Half-Acre Diabase Boulders)",
            "Night Hag Coven, Hell Hound & Oni",
            "Witcher Fiend (Bies) & Displacer Beast"
        ],
        "apex_spawn": "The Sourland Roaring-Rock Arch-Fiend",
        "harvestable_grafts": ["Bulette Dorsal Carapace", "Displacer Tentacle Mantle"]
    },
    "wissahickon_valley_gorge": {
        "resident_races": [
            "Sylvan Thornborn (Dryad)", "Firbolg Primeval Warden",
            "Leshy", "Aether-Touched Elf", "Viera / Cait Sith Wood-Warden"
        ],
        "dispersed_monsters": [
            "Ancient Leshen & Treant (Hermit's Cave of Johannes Kelpius & Forbidden Drive)",
            "Displacer Beast, Phase Spider & Nixie (Devil's Pool)",
            "Spriggan Matron"
        ],
        "apex_spawn": "The Woman of the Wilderness Specter & Wissahickon Ancient Leshen",
        "harvestable_grafts": ["Leshen Ancient Heartwood", "Displacer Tentacle Mantle", "Phase Spider Ethereal Spinneret"]
    },
    "pine_barrens_wharton_wilds": {
        "resident_races": [
            "Leshy (Pine-Cone & Bog-Moss Spirit)", "Firbolg Primeval Warden",
            "Saurian Dredge (Lizardfolk / Iruxi)", "Sylvan Thornborn", "Witcher Conscript"
        ],
        "dispersed_monsters": [
            "Ancient Leshen, Great Malboro & Spriggan Matron (1.1-Million-Acre Shifting Pygmy Pines!)",
            "Adult Green Dragon, Displacer Beast & Phase Spider",
            "Pathfinder Chupacabra, Boggard & Shambling Mound"
        ],
        "apex_spawn": "THE JERSEY GLITCH-DEVIL (Leeds Chimera Wyvern, Lv 75 Mythic World Boss)",
        "harvestable_grafts": ["Leshen Ancient Heartwood", "Malboro Bad-Breath Gland", "Displacer Tentacle Mantle"]
    },
    "blue_hole_ongs_hat_anomaly": {
        "resident_races": [
            "Void-Walker (Singularity Drifter)", "Kitsune", "Githzerai",
            "Conrasu / Modron", "Sylvan Thornborn"
        ],
        "dispersed_monsters": [
            "The Jabberwock (Pathfinder 2E First-World Tane) & Protean Imentesh (Ong's Hat Chaos Portal!)",
            "Alghollthu Veiled Master & Aboleth (Bottomless Turquoise Blue Hole Spring)",
            "Displacer Beast & Blink Dog"
        ],
        "apex_spawn": "THE JABBERWOCK OF ONG'S HAT & THE BLUE-HOLE ABYSSAL WATCHER",
        "harvestable_grafts": ["Aether-Resonant Ocular", "Displacer Tentacle Mantle", "Linnorm Curse-Heart"]
    },
    "warren_grove_bombardment_crater": {
        "resident_races": [
            "Hellforged Fiendblood (Tiefling)", "Ashen Dunmer", "Iron-Jaw Orc", "Golem Reborn"
        ],
        "dispersed_monsters": [
            "Gigantuar (10,000 Needles Cactuar Boss) & King Behemoth (9,400-Acre Scorched Sand Crater!)",
            "Nergigante, Black Diablos & Brachydios",
            "Blue Dragon & Purple Worm"
        ],
        "apex_spawn": "KING BEHEMOTH, GIGANTUAR & NERGIGANTE OF WARREN GROVE",
        "harvestable_grafts": ["Bulette Dorsal Carapace", "Silt-Marrow Geothermal Core", "Wyrm-Scale Sheath"]
    }
}

# Map canonical WORLD_ATLAS_ZONES keys to their ZONE_DISPERSED_ECOLOGY definitions
_ZONE_ECOLOGY_ALIASES: Dict[str, str] = {
    "clinton_red_mill": "clinton_red_mill_refinery",
    "blairstown_viaduct": "blairstown_frontier_outpost",
    "oxford_mines": "oxford_furnace_mines",
    "bethlehem_steel_stacks": "bethlehem_steel_titan_forge",
    "pohatcong_roaring_rock_wilds": "pohatcong_roaring_rock",
    "delaware_water_gap_sunfish": "delaware_water_gap_tammany",
    "ringing_rocks_boulder_field": "ringing_rocks_diabase",
    "stroudsburg_bastion": "stroudsburg_milford_gateways",
    "milford_grey_towers": "stroudsburg_milford_gateways",
    "jim_thorpe_citadel": "jim_thorpe_mauch_chunk",
    "scranton_steamtown_hub": "scranton_steamtown_nexus",
    "tobyhanna_army_depot": "tobyhanna_signal_depot",
    "high_point_stokes_obelisk": "high_point_stokes_ridge",
    "hawk_mountain_sanctuary": "hawk_mountain_aerie",
    "west_point_fortress": "west_point_granite_bastion",
    "mohonk_sky_citadel": "new_paltz_mohonk_citadel",
    "watchung_basalt_copper_mines": "watchung_copper_mines",
    "bell_labs_holmdel_complex": "bell_labs_horn_antenna",
    "bannermans_castle_nuclear_glitches": "bannerman_castle_pollepel",
    "manhattan_monolith_track61": "manhattan_monolith_undercity",
    "great_swamp_stirling_fen": "great_swamp_lord_stirling",
    "watchung_feltville_ghost_town": "watchung_feltville_deserted",
    "palisades_firewall_cliffs": "palisades_diabase_cliffs",
    "harriman_bear_mountain_dunderberg": "harriman_bear_mountain",
    "catskill_peaks_ashokan_overlook": "catskill_high_peaks_overlook",
    "new_hope_lambertville": "new_hope_lambertville_bazaar",
    "princeton_nassau_citadel": "princeton_arcane_conclave",
    "valley_forge_bastion": "valley_forge_star_redoubt",
    "batsto_village_oasis": "batsto_pine_barrens_bastion",
    "cornwall_magnetite_maw": "cornwall_iron_pit",
    "princeton_pppl_tokamak": "princeton_tokamak_pppl",
    "sourland_mountain_devils_acre": "sourland_devils_half_acre",
    "ongs_hat_blue_hole": "blue_hole_ongs_hat_anomaly",
}

_COMBINED_ZONE_ECOLOGY_MERGES: Dict[str, List[str]] = {
    "archbald_pothole_concrete_city": ["concrete_city_nanticoke", "archbald_pothole_shaft"],
    "tilly_foster_rosendale_mines": ["rosendale_widow_jane_mines", "tilly_foster_mine"],
    "camp_evans_sams_point": ["camp_evans_infoage", "sams_point_ice_caves"],
    "shawangunk_gunks_ricketts_glen": ["shawangunk_gunks_cliffs", "ricketts_glen_falls"],
    "philly_navy_yard_fort_mifflin": ["philadelphia_navy_yard_ghost_fleet", "fort_mifflin_mud_island"],
    "pine_barrens_warren_grove": ["pine_barrens_wharton_wilds", "warren_grove_bombardment_crater"],
}

for _alias_key, _source_key in _ZONE_ECOLOGY_ALIASES.items():
    if _source_key in ZONE_DISPERSED_ECOLOGY:
        ZONE_DISPERSED_ECOLOGY[_alias_key] = dict(ZONE_DISPERSED_ECOLOGY[_source_key])

for _merged_key, _part_keys in _COMBINED_ZONE_ECOLOGY_MERGES.items():
    _races: List[str] = []
    _monsters: List[str] = []
    _grafts: List[str] = []
    _apexes: List[str] = []
    for _pk in _part_keys:
        _part = ZONE_DISPERSED_ECOLOGY.get(_pk, {})
        for _r in _part.get("resident_races", []):
            if _r not in _races:
                _races.append(_r)
        for _m in _part.get("dispersed_monsters", []):
            if _m not in _monsters:
                _monsters.append(_m)
        for _g in _part.get("harvestable_grafts", []):
            if _g not in _grafts:
                _grafts.append(_g)
        if _part.get("apex_spawn"):
            _apexes.append(_part["apex_spawn"])
    ZONE_DISPERSED_ECOLOGY[_merged_key] = {
        "resident_races": _races,
        "dispersed_monsters": _monsters,
        "apex_spawn": " / ".join(_apexes),
        "harvestable_grafts": _grafts,
    }


# =============================================================================
# 3. HELPER & QUERY FUNCTIONS
# =============================================================================

def get_zone_dispersed_ecology(zone_id_or_loc: str) -> Dict[str, Any]:
    """
    Returns the dispersed fantasy races, multi-universe monsters, apex spawn,
    and harvestable grafts for a zone ID or location string.
    """
    raw_key = str(zone_id_or_loc).strip().lower()
    if raw_key in ZONE_DISPERSED_ECOLOGY:
        return dict(ZONE_DISPERSED_ECOLOGY[raw_key])

    from backend.world_atlas import resolve_zone_from_location
    z = resolve_zone_from_location(zone_id_or_loc)
    z_id = z["id"] if z else raw_key

    eco = ZONE_DISPERSED_ECOLOGY.get(z_id)
    if eco:
        return dict(eco)

    # Default fallback ecology for custom/procedural locations
    return {
        "resident_races": ["Pure Human", "Deepforged Dwarf", "Aether-Touched Elf", "Lightfoot Halfling", "Tiefling"],
        "dispersed_monsters": ["Primeval Owlbear", "Displacer Beast", "Rust Monster", "Carrion Crawler"],
        "apex_spawn": "Roaming Wyvern & Ancient Leshen",
        "harvestable_grafts": ["Chimeric Beast Claws", "Displacer Tentacle Mantle"]
    }


def search_bestiary(
    query: Optional[str] = None,
    origin_system: Optional[str] = None,
    creature_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Searches and filters BESTIARY_COMPENDIUM by text query, origin system
    ('D&D', 'Pathfinder', 'Witcher', 'Final Fantasy', 'Monster Hunter', 'Sword Art Online', etc.),
    or creature type.
    """
    results = []
    q_low = query.strip().lower() if query else None
    orig_low = origin_system.strip().lower() if origin_system and origin_system.lower() != "all" else None
    type_low = creature_type.strip().lower() if creature_type and creature_type.lower() != "all" else None

    for c_id, c_data in BESTIARY_COMPENDIUM.items():
        if orig_low and orig_low not in c_data.get("origin", "").lower():
            continue
        if type_low and type_low not in c_data.get("type", "").lower():
            continue
        if q_low:
            haystack = " ".join([
                c_data.get("name", ""),
                c_data.get("origin", ""),
                c_data.get("type", ""),
                c_data.get("lore", ""),
                " ".join(c_data.get("signature_abilities", [])),
                " ".join(c_data.get("habitats", []))
            ]).lower()
            if q_low not in haystack:
                continue
        results.append(c_data)

    results.sort(key=lambda x: (x.get("cr_level", 1), x.get("name", "")))
    return results


def roll_random_zone_encounter(zone_id_or_loc: str, seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Generates a randomized, lore-accurate encounter or sighting for any zone in the
    100-mile Washington NJ World Atlas, combining native constructs, dispersed D&D /
    Pathfinder / Fantasy Series monsters, and resident fantasy races.
    """
    from backend.world_atlas import resolve_zone_from_location, WORLD_ATLAS_ZONES
    zone = resolve_zone_from_location(zone_id_or_loc) or WORLD_ATLAS_ZONES["pohatcong_roaring_rock_wilds"]
    eco = get_zone_dispersed_ecology(zone["id"])

    rng = random.Random(seed) if seed is not None else random
    pool = list(zone.get("monsters", [])) + list(eco.get("dispersed_monsters", []))
    chosen_monster = rng.choice(pool) if pool else "Primeval Owlbear"
    chosen_race = rng.choice(eco.get("resident_races", ["Pure Human"]))

    return {
        "zone_id": zone["id"],
        "zone_name": zone["name"],
        "encountered_creature": chosen_monster,
        "nearby_race_enclave": chosen_race,
        "apex_threat": eco.get("apex_spawn", zone.get("boss", "None")),
        "harvestable_grafts": eco.get("harvestable_grafts", [])
    }


def enrich_world_atlas_zones(world_atlas_zones_dict: Dict[str, Dict[str, Any]]) -> None:
    """
    Enriches every zone in WORLD_ATLAS_ZONES in-place with its dispersed
    D&D 3.5e/5E, Pathfinder 1E/2E, and Major Fantasy Series races, monsters, and grafts.
    """
    for z_id, z_data in world_atlas_zones_dict.items():
        eco = ZONE_DISPERSED_ECOLOGY.get(z_id)
        if not eco:
            continue
        z_data["resident_races"] = list(eco.get("resident_races", []))
        z_data["dispersed_monsters"] = list(eco.get("dispersed_monsters", []))
        z_data["apex_fantasy_spawn"] = eco.get("apex_spawn", "")

        # Merge dispersed monsters into z_data["monsters"] (if not a pure safe zone, or keep in dispersed_monsters for safe zones)
        if not z_data.get("is_safe_zone", False):
            existing_m = list(z_data.get("monsters", []))
            for dm in eco.get("dispersed_monsters", []):
                if dm not in existing_m:
                    existing_m.append(dm)
            z_data["monsters"] = existing_m

        # Merge harvestable grafts into signature_grafts
        existing_g = list(z_data.get("signature_grafts", []))
        for hg in eco.get("harvestable_grafts", []):
            if hg not in existing_g:
                existing_g.append(hg)
        z_data["signature_grafts"] = existing_g
