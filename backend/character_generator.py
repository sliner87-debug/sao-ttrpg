"""
Pre-to-Post Integration Character Generator Engine
Translates real-world Earth knowledge, vocations, and physical conditioning into LitRPG parameters.
Fully integrated with the 1-1000 Skill Mastery and Mechanics Engine.
Supports 18 Lifestyle Presets, 20 Vocations, 20 Lineages, 17+ Relics,
an interactive Custom Life Collaboration Parser, and Character-Folder Save Management.
"""

import json
import os
import time
import re
from backend.mechanics import calculate_encumbrance, calculate_ac, CANONICAL_MILESTONES

# --- 18 QUICK-LIFESTYLE QUESTIONNAIRE PRESETS (Auto-Distribute 20 Points) ---
# All presets allocate exactly 20 points across the 6 core stats: STR, DEX, CON, INT, WIS, CHA.
PRESET_LIFESTYLES = {
    "desk_bound": {
        "title": "🛋️ Desk Bound / Sedentary (+Mental)",
        "desc": "Long hours at keyboards, low physical strain, high cognitive and analytical conditioning.",
        "points": {"STR": 1, "DEX": 1, "CON": 2, "INT": 6, "WIS": 6, "CHA": 4}
    },
    "athletic": {
        "title": "🏃 Athletic / Field Sports (+Agility)",
        "desc": "High cardiovascular fitness, agile footwork, kinetic discipline, and team communication.",
        "points": {"STR": 5, "DEX": 6, "CON": 4, "INT": 1, "WIS": 2, "CHA": 2}
    },
    "heavy_labor": {
        "title": "🔨 Heavy Labor / Trades (+STR/CON)",
        "desc": "Repetitive heavy lifting, calloused endurance, mechanical resistance, and tool wielding.",
        "points": {"STR": 7, "DEX": 3, "CON": 6, "INT": 1, "WIS": 2, "CHA": 1}
    },
    "first_responder": {
        "title": "🎖️ First Responder / Combat (+Combat)",
        "desc": "Crisis tactical response, rapid triage decision-making, and high adrenaline composure.",
        "points": {"STR": 5, "DEX": 5, "CON": 4, "INT": 2, "WIS": 3, "CHA": 1}
    },
    "academic_scholar": {
        "title": "📚 Academic Scholar / Researcher (+INT/WIS)",
        "desc": "Archival synthesis, methodological logic, rigorous deductive reasoning, and deep theory.",
        "points": {"STR": 0, "DEX": 1, "CON": 1, "INT": 8, "WIS": 7, "CHA": 3}
    },
    "night_security": {
        "title": "🔦 Night Shift Security / Sentry (+WIS/CON)",
        "desc": "Perimeter vigilance, sleep deprivation resistance, darkness adaptation, and acute hearing.",
        "points": {"STR": 3, "DEX": 4, "CON": 5, "INT": 1, "WIS": 6, "CHA": 1}
    },
    "offgrid_homesteader": {
        "title": "🌲 Off-Grid Homesteader / Survivalist (+CON/WIS)",
        "desc": "Timber felling, well digging, food preservation, weather reading, and stubborn endurance.",
        "points": {"STR": 4, "DEX": 3, "CON": 6, "INT": 1, "WIS": 5, "CHA": 1}
    },
    "yoga_contortionist": {
        "title": "🧘 Yoga Instructor / Contortionist (+DEX/WIS)",
        "desc": "Supreme core balance, ligament elasticity, breath regulation, and joint freedom.",
        "points": {"STR": 1, "DEX": 8, "CON": 4, "INT": 1, "WIS": 4, "CHA": 2}
    },
    "esports_gamer": {
        "title": "🎮 Esports Athlete / Speedrunner (+DEX/INT)",
        "desc": "Micro-second twitch reactions, spatial routing, predictive framing, and APM dexterity.",
        "points": {"STR": 0, "DEX": 7, "CON": 1, "INT": 7, "WIS": 3, "CHA": 2}
    },
    "stage_performer": {
        "title": "🎭 Performing Musician / Stage Actor (+CHA/DEX)",
        "desc": "Magnetic crowd presence, acoustic projection, physical choreography, and empathetic resonance.",
        "points": {"STR": 1, "DEX": 4, "CON": 2, "INT": 2, "WIS": 3, "CHA": 8}
    },
    "longhaul_trucker": {
        "title": "🚛 Long-Haul Trucker / Highway Specialist (+CON/WIS)",
        "desc": "Iron highway stamina, solitary mental resilience, situational radar, and route planning.",
        "points": {"STR": 3, "DEX": 2, "CON": 7, "INT": 1, "WIS": 5, "CHA": 2}
    },
    "extreme_sports": {
        "title": "🏂 Extreme Sports / Adrenaline Junkie (+DEX/STR)",
        "desc": "High-velocity downhill balance, rapid kinetic recovery, and zero fear of terminal velocity.",
        "points": {"STR": 5, "DEX": 7, "CON": 5, "INT": 1, "WIS": 1, "CHA": 1}
    },
    "commercial_diver": {
        "title": "🤿 Commercial Diver / Hyperbaric Welder (+CON/STR)",
        "desc": "Hyperbaric lung fortitude, freezing water tolerance, deep darkness composure, and torch work.",
        "points": {"STR": 5, "DEX": 2, "CON": 8, "INT": 1, "WIS": 3, "CHA": 1}
    },
    "line_cook": {
        "title": "🍳 Line Cook / Kitchen Warrior (+DEX/CON)",
        "desc": "Blistering stove endurance, multi-pan micro-timing, knife agility, and battle-cry tempo.",
        "points": {"STR": 2, "DEX": 6, "CON": 6, "INT": 1, "WIS": 3, "CHA": 2}
    },
    "highschool_educator": {
        "title": "👨‍🏫 High School Educator / Counselor (+CHA/INT/WIS)",
        "desc": "Infinite crisis patience, behavioral de-escalation, group discipline, and clear instruction.",
        "points": {"STR": 1, "DEX": 1, "CON": 2, "INT": 5, "WIS": 5, "CHA": 6}
    },
    "park_ranger": {
        "title": "🧭 Park Ranger / Forestry Tracker (+WIS/DEX)",
        "desc": "Topographical wilderness mastery, predator track reading, brush navigation, and fire watching.",
        "points": {"STR": 3, "DEX": 5, "CON": 4, "INT": 1, "WIS": 6, "CHA": 1}
    },
    "blacksmith_sculptor": {
        "title": "⚒️ Blacksmith / Metal Sculptor (+STR/CON)",
        "desc": "Ten-pound hammer swinging, radiant heat endurance, steel quenching, and structural vision.",
        "points": {"STR": 7, "DEX": 2, "CON": 6, "INT": 2, "WIS": 2, "CHA": 1}
    },
    "mma_fighter": {
        "title": "🥊 Combat Sports Fighter / MMA Striker (+STR/DEX)",
        "desc": "Explosive hip drive, choke defense, pain suppression, and bone-crushing striking accuracy.",
        "points": {"STR": 6, "DEX": 6, "CON": 5, "INT": 1, "WIS": 1, "CHA": 1}
    }
}

# --- 20 PRE-INTEGRATION VOCATIONAL BACKGROUNDS ---
PRESET_BACKGROUNDS = {
    # Original 8 Vocations
    "software_engineer": {
        "title": "Software Engineer / Sysadmin",
        "description": "Spent years analyzing network protocols, debugging logic leaks, and writing terminal scripts.",
        "stat_recommendations": {"INT": 3, "WIS": 2, "STR": 0, "DEX": 0, "CON": 0, "CHA": 0},
        "skills": {
            "Magi-Tech Hacking": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Bypassing arcane firewalls, terminal encryption, and logic wards.",
                "milestones_unlocked": []
            },
            "Aether-Circuit Query": {
                "mastery": 30,
                "tier": "Novice",
                "description": "Tracing leyline data flows and construct signal routing.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Logic Probe (Passive): Enhanced perception when analyzing corrupted terminals, cyber-doors, and security subroutines."
    },
    "nurse_paramedic": {
        "title": "Nurse / Paramedic / EMT",
        "description": "Trained under intense trauma conditions to triage wounds, administer emergency aid, and maintain calm under pressure.",
        "stat_recommendations": {"WIS": 3, "CON": 2, "INT": 1, "STR": 0, "DEX": 0, "CHA": 0},
        "skills": {
            "Arcane Triage": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Stabilizing biological vitals, treating traumatic bleeding, and neutralizing aetheric shock.",
                "milestones_unlocked": [50]
            },
            "Field Surgery": {
                "mastery": 40,
                "tier": "Novice",
                "description": "Physical repair of damaged tissue and extraction of crystalline shrapnel.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Tourniquet Protocol (Passive): Treating bleeding or trauma wounds consumes 50% fewer medical supplies."
    },
    "mechanic_machinist": {
        "title": "Machinist / Auto-Mechanic",
        "description": "Hands-on mastery of mechanical assemblies, torque specs, hydraulic rigging, and metal fabrication.",
        "stat_recommendations": {"STR": 2, "CON": 2, "INT": 2, "DEX": 0, "WIS": 0, "CHA": 0},
        "skills": {
            "Field Smithing": {
                "mastery": 50,
                "tier": "Apprentice",
                "description": "Reforging weapons, repairing armor plates, and maintaining mechanical gear.",
                "milestones_unlocked": [50]
            },
            "Golem-Graft Rigging": {
                "mastery": 35,
                "tier": "Novice",
                "description": "Tuning prosthetic joints, hydraulic seals, and aether-couplings.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Structural Assessment (Passive): Instantly evaluate fracture points on armor, barricades, and constructs."
    },
    "hunter_tracker": {
        "title": "Hunter / Outdoor Guide",
        "description": "Lifelong experience tracking game, surviving freezing wilderness, reading terrain, and rigging snares.",
        "stat_recommendations": {"WIS": 3, "DEX": 2, "CON": 1, "STR": 0, "INT": 0, "CHA": 0},
        "skills": {
            "Field Trapping": {
                "mastery": 60,
                "tier": "Apprentice",
                "description": "Deployment and concealment of wire snares, tripwires, and perimeter traps.",
                "milestones_unlocked": [50]
            },
            "Cartography": {
                "mastery": 50,
                "tier": "Apprentice",
                "description": "Topographical parsing, terrain mapping, and landmark navigation.",
                "milestones_unlocked": [50]
            }
        },
        "innate_perk": "Snare Concealment (Passive): Deployed traps and ambushes receive a +3 bonus to their stealth detection DC."
    },
    "construction_trades": {
        "title": "Heavy Construction / Tradesperson",
        "description": "Conditioned by heavy physical labor, tool operation, and high-impact structural demolition.",
        "stat_recommendations": {"STR": 4, "CON": 3, "DEX": 0, "INT": 0, "WIS": 0, "CHA": 0},
        "skills": {
            "Trench Hammers": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Bludgeoning armor-crush strikes and heavy structural demolition attacks.",
                "milestones_unlocked": [50]
            },
            "Structural Breach": {
                "mastery": 40,
                "tier": "Novice",
                "description": "Targeting load-bearing structures, stone barriers, and reinforced bulkheads.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Kinetic Impact (Passive): Bludgeoning attacks against constructs, golems, and armored carapaces deal +2 bonus damage."
    },
    "martial_artist_veteran": {
        "title": "Martial Artist / Combat Veteran",
        "description": "Rigorous tactical discipline, weapon choreography, instinctive reaction times, and situational awareness.",
        "stat_recommendations": {"STR": 3, "DEX": 3, "CON": 2, "INT": 0, "WIS": 0, "CHA": 0},
        "skills": {
            "One-Handed Axes": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Fast, brutal chops, hooks, and cleaves with single-handed blades.",
                "milestones_unlocked": [50]
            },
            "Tactical Reflexes": {
                "mastery": 40,
                "tier": "Novice",
                "description": "Close-quarters footwork and split-second dodging.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Hewing Grip (Passive): Off-hand accuracy penalty is reduced by 50% when dual-wielding light or medium weapons."
    },
    "corporate_negotiator": {
        "title": "Corporate Executive / Sales Lead",
        "description": "Master of leverage, contract phrasing, reading psychological tells, and resource valuation.",
        "stat_recommendations": {"CHA": 4, "WIS": 2, "INT": 1, "STR": 0, "DEX": 0, "CON": 0},
        "skills": {
            "Resource Barter": {
                "mastery": 50,
                "tier": "Apprentice",
                "description": "Assessing market value, haggling with scavengers, and securing favorable trade contracts.",
                "milestones_unlocked": [50]
            },
            "Faction Diplomacy": {
                "mastery": 40,
                "tier": "Novice",
                "description": "Navigating guild politics, feudal alliances, and executive syndicates.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Extortion Bypass (Passive): Safe-zone automated merchant casualty markups are permanently discounted by 15%."
    },
    "artist_chef": {
        "title": "Artist / Musician / Culinary Chef",
        "description": "Trained in sensory perception, delicate hand-eye coordination, emotional resonance, and nutritional synthesis.",
        "stat_recommendations": {"DEX": 2, "WIS": 2, "CHA": 2, "STR": 0, "CON": 0, "INT": 0},
        "skills": {
            "Aether-Weaving": {
                "mastery": 40,
                "tier": "Novice",
                "description": "Spinning ambient mana threads into protective meshes, musical resonances, and visual illusions.",
                "milestones_unlocked": []
            },
            "Provisions & Alchemy": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Brewing restorative elixirs, preserving aetheric ingredients, and preparing nutritious stamina rations.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Comforting Ration (Passive): Consumed food buffs grant double stamina recovery and restore +5 focus."
    },

    # 12 Brand New Pre-Packaged Vocations
    "electrician_lineworker": {
        "title": "Electrician / High-Voltage Lineworker",
        "description": "Scaled utility poles and worked with lethal voltages, high-amperage breakers, and transformer coils.",
        "stat_recommendations": {"DEX": 2, "CON": 2, "INT": 2, "STR": 0, "WIS": 0, "CHA": 0},
        "skills": {
            "Magi-Tech Wiring": {
                "mastery": 50,
                "tier": "Apprentice",
                "description": "Rigging electrical conduits, grounding leyline circuits, and channeling static mana.",
                "milestones_unlocked": [50]
            },
            "Kinetic Insulation": {
                "mastery": 40,
                "tier": "Novice",
                "description": "Insulating apparel and weaponry against electro-shock and lightning surges.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Dielectric Grounding (Passive): Suffer 25% reduced lightning/shock damage and never suffer paralysis from stun-traps."
    },
    "veterinarian_handler": {
        "title": "Veterinarian / Animal Care Specialist",
        "description": "Decades of diagnostic medicine, vaccine preparation, and surgical triage on feral and domestic beasts.",
        "stat_recommendations": {"WIS": 3, "INT": 2, "CHA": 1, "STR": 0, "DEX": 0, "CON": 0},
        "skills": {
            "Beast Empathy": {
                "mastery": 50,
                "tier": "Apprentice",
                "description": "Pacifying agitated monsters, reading predator body language, and taming mounts.",
                "milestones_unlocked": [50]
            },
            "Field Xenobiology": {
                "mastery": 40,
                "tier": "Novice",
                "description": "Dissecting monster anatomies and identifying organ gland vulnerabilities.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Beast-Whisperer (Passive): Wild predators hesitate before attacking; +3 bonus to all animal handling and taming checks."
    },
    "locksmith_security": {
        "title": "Locksmith / Physical Security Specialist",
        "description": "Decoded pin tumblers, bypass shims, electronic keypads, safe dials, and reinforced vault doors.",
        "stat_recommendations": {"DEX": 3, "INT": 2, "WIS": 1, "STR": 0, "CON": 0, "CHA": 0},
        "skills": {
            "Tumbler Decryption": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Picking mechanical lock tumblers and bypassing runic keyholes.",
                "milestones_unlocked": [50]
            },
            "Perimeter Intrusion": {
                "mastery": 40,
                "tier": "Novice",
                "description": "Detecting hidden floor pressure plates, tripwires, and intrusion wards.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Skeleton Key Insight (Passive): Lockpicks and bypass probes never break upon a failed check."
    },
    "chemist_pharmacist": {
        "title": "Chemist / Industrial Pharmacist",
        "description": "Handled reagent purity, exothermic titrations, compound crystallization, and pharmacology.",
        "stat_recommendations": {"INT": 4, "WIS": 2, "STR": 0, "DEX": 0, "CON": 0, "CHA": 0},
        "skills": {
            "Chemical Distillation": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Refining raw aetheric minerals and solvent extractions into stable reagents.",
                "milestones_unlocked": [50]
            },
            "Toxicological Neutralization": {
                "mastery": 40,
                "tier": "Novice",
                "description": "Synthesizing antivenoms and neutralizing environmental toxins and vapors.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Catalytic Reaction (Passive): Crafted potions, poisons, and solvent bombs have +20% potency or duration."
    },
    "librarian_archivist": {
        "title": "Librarian / Antiquarian Archivist",
        "description": "Curated ancient manuscripts, cross-referenced forgotten histories, and translated dead languages.",
        "stat_recommendations": {"INT": 3, "WIS": 3, "STR": 0, "DEX": 0, "CON": 0, "CHA": 0},
        "skills": {
            "Ancient Glyph Deciphering": {
                "mastery": 50,
                "tier": "Apprentice",
                "description": "Translating forgotten pre-collapse scripts and magical rune matrices.",
                "milestones_unlocked": [50]
            },
            "Lore Cataloging": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Cross-referencing monster codices to reveal enemy resistances and loot tables.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Eidetic Index (Passive): Instantly identify the tier, origin, and hidden curse of any discovered magical grimoire or parchment."
    },
    "trucker_highwayman": {
        "title": "Long-Haul Trucker / Logistics Hauler",
        "description": "Mastered interstate convoy logistics, diesel mechanics, and sleepless cross-country hauls.",
        "stat_recommendations": {"CON": 3, "STR": 2, "WIS": 1, "DEX": 0, "INT": 0, "CHA": 0},
        "skills": {
            "Heavy Vehicle Rigging": {
                "mastery": 50,
                "tier": "Apprentice",
                "description": "Operating, maintaining, and hot-wiring motorized carts and heavy salvage crawlers.",
                "milestones_unlocked": [50]
            },
            "Interstate Navigation": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Plotting the most efficient transit routes and chokepoints between distant sectors.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Highballing (Passive): Overland convoy and travel speeds are increased by 20%; driver travel fatigue is halved."
    },
    "architect_planner": {
        "title": "Architect / Structural Engineer",
        "description": "Designed high-rise foundations, cantilever trusses, blueprint schematics, and load limits.",
        "stat_recommendations": {"INT": 3, "WIS": 2, "STR": 1, "DEX": 0, "CON": 0, "CHA": 0},
        "skills": {
            "Structural Assessment": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Identifying foundational stress points, collapse hazards, and bunker layouts.",
                "milestones_unlocked": [50]
            },
            "Homestead Engineering": {
                "mastery": 40,
                "tier": "Novice",
                "description": "Designing reinforced fortifications, automated defenses, and vault expansions.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Blueprinter (Passive): Homestead room construction costs are reduced by 15%, and base bunker durability is increased by 25%."
    },
    "detective_forensics": {
        "title": "Detective / Forensic Investigator",
        "description": "Reconstructed ballistic trajectories, analyzed blood spatter, and cracked criminal conspiracies.",
        "stat_recommendations": {"WIS": 3, "INT": 3, "STR": 0, "DEX": 0, "CON": 0, "CHA": 0},
        "skills": {
            "Crime Scene Reconstruction": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Deducing what occurred in a ruined room from blood patterns and footprints.",
                "milestones_unlocked": [50]
            },
            "Ballistic Telemetry": {
                "mastery": 40,
                "tier": "Novice",
                "description": "Calculating sniper lines of fire and anticipating enemy ranged trajectories.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Forensic Eye (Passive): Clues, tracks, and concealed cache markers glow with faint residual phosphor under examination."
    },
    "botanist_horticulturist": {
        "title": "Botanist / Hydroponics Cultivator",
        "description": "Mastered soil chemistry, cross-pollination, mycorrhizal networks, and greenhouse pruning.",
        "stat_recommendations": {"WIS": 3, "INT": 2, "CON": 1, "STR": 0, "DEX": 0, "CHA": 0},
        "skills": {
            "Flora Harvesting": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Harvesting delicate medicinal plants and toxic spores without damaging yields.",
                "milestones_unlocked": [50]
            },
            "Mycelial Grafting": {
                "mastery": 40,
                "tier": "Novice",
                "description": "Cultivating bioluminescent mushrooms and graftable fungal symbiotes.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Green Thumb (Passive): Greenhouse harvest yields in the Homestead are doubled, with a 25% chance for mutant rare strains."
    },
    "firefighter_smokejumper": {
        "title": "Firefighter / Smokejumper",
        "description": "Ran into burning buildings, wielded Halligan breach bars, and survived suffocating thermal storms.",
        "stat_recommendations": {"STR": 3, "CON": 3, "DEX": 1, "INT": 0, "WIS": 0, "CHA": 0},
        "skills": {
            "Hazard Breaching": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Forcing open warped steel blast doors and chopping through burning debris.",
                "milestones_unlocked": [50]
            },
            "Pyric Suppression": {
                "mastery": 40,
                "tier": "Novice",
                "description": "Extinguishing arcane flame hazards and handling pressurized hose lines.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Thermal Resistance (Passive): Take 20% reduced fire damage and ignore smoke inhalation and choking penalties."
    },
    "pilot_avionics": {
        "title": "Commercial Pilot / Avionics Technician",
        "description": "Mastered instrument flight ratings, three-axis aerodynamics, gyroscopic navigation, and engine diagnostics.",
        "stat_recommendations": {"DEX": 3, "INT": 2, "WIS": 1, "STR": 0, "CON": 0, "CHA": 0},
        "skills": {
            "Aerodynamic Navigation": {
                "mastery": 50,
                "tier": "Apprentice",
                "description": "Glider steering, calculating wind shear, and high-altitude drift control.",
                "milestones_unlocked": [50]
            },
            "Gyroscopic Balance": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Maintaining spatial orientation during falls, zero-G, or disorienting spins.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Horizon Lock (Passive): Immune to vertigo and disorientation; fall damage is reduced by 25%."
    },
    "tailor_leathercrafter": {
        "title": "Master Tailor / Leathercrafter",
        "description": "Stitched heavy hide armors, handled delicate silk weaves, and reinforced load-bearing seams.",
        "stat_recommendations": {"DEX": 3, "WIS": 2, "CHA": 1, "STR": 0, "CON": 0, "INT": 0},
        "skills": {
            "Weave Reinforcement": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Stitching protective aether-threading and Kevlar backing into light armors.",
                "milestones_unlocked": [50]
            },
            "Hide Tanning & Curing": {
                "mastery": 40,
                "tier": "Novice",
                "description": "Processing beast pelts, chitin plates, and sinew cords into wearable gear.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Seamless Stitch (Passive): Fabric and leather armor repaired by you gains +10% bonus durability over maximum."
    }
}

# --- 20 RACIAL MUTATIONS & LINEAGES (Fantasy & Sci-Fi) ---
RACIAL_LINEAGES = {
    # Original 6 Lineages
    "pure_human": {
        "name": "Pure Human",
        "genre": "Universal",
        "desc": "Resisted genetic mutation during the Aetheric Rift collapse. Highly adaptable, tenacious, and versatile.",
        "stat_mods": {"STR": 1, "DEX": 1, "CON": 1, "INT": 1, "WIS": 1, "CHA": 1},
        "racial_abilities": [
            "Tenacious Will: +10% bonus experience gain from all combat and discovery actions.",
            "Versatile Conditioning: +1 additional starting Feat slot."
        ]
    },
    "phrenic_human": {
        "name": "Phrenic Human",
        "genre": "Psionic / Sci-Fi",
        "desc": "Awakened latent psionic neural pathways when flooded by atmospheric mana. Projects telekinetic forces.",
        "stat_mods": {"INT": 2, "WIS": 2, "DEX": 1, "STR": 0, "CON": 0, "CHA": 0},
        "racial_abilities": [
            "Aether-Telepathy: Communicate silently with party members within 60ft.",
            "Telekinetic Grip: Manipulate lightweight objects remotely and recall thrown weapons to your hand.",
            "Psionic Shielding: Project a minor kinetic barrier to absorb incoming impacts.",
            "Flaw - Sensory Overload: Vulnerable to high-frequency sonic or psychic distortion."
        ]
    },
    "deepforged_dwarf": {
        "name": "Deepforged Dwarf",
        "genre": "Fantasy",
        "desc": "Underground heritage fused with aether-furnaces. Unmatched physical fortitude and geological intuition.",
        "stat_mods": {"CON": 3, "STR": 2, "WIS": 1, "DEX": -1, "INT": 0, "CHA": -1},
        "racial_abilities": [
            "Stone-Sense: Instantly detect structural hollows, secret vaults, and ore seams in subterranean sectors.",
            "Toxic Hardening: Advantage on saving throws against atmospheric poisons, radiation, and spores."
        ]
    },
    "scrapper_goblinoid": {
        "name": "Scrapper Goblinoid",
        "genre": "Fantasy / Steampunk",
        "desc": "Warped into an agile, sharp-eyed industrial scavenger. Masters of salvage, stealth, and evasion.",
        "stat_mods": {"DEX": 3, "INT": 2, "STR": -1, "CON": 0, "WIS": 0, "CHA": 0},
        "racial_abilities": [
            "Junk-Engine Intuition: Assemble and repair crude weapons/tools using 50% fewer materials.",
            "Scurry: Disengage from melee combat without drawing free hostile attacks."
        ]
    },
    "aether_elf": {
        "name": "Aether-Touched Elf",
        "genre": "Fantasy",
        "desc": "Infused with raw ambient leyline energy. Graceful, sharp-eyed, and inherently sensitive to magic.",
        "stat_mods": {"DEX": 2, "INT": 2, "CHA": 1, "STR": -1, "CON": 0, "WIS": 0},
        "racial_abilities": [
            "Mana Resonance: Low-light vision and natural passive detection of magical wardings.",
            "Quickstep: Base overland travel speed increased by +15%."
        ]
    },
    "golem_reborn": {
        "name": "Golem Reborn",
        "genre": "MageTech / Construct",
        "desc": "Organic consciousness salvaged into a heavy mechanized construct of blackened steel and runic stone.",
        "stat_mods": {"CON": 4, "STR": 2, "DEX": -2, "CHA": -2, "INT": 0, "WIS": 0},
        "racial_abilities": [
            "Living Construct: Immune to biological diseases, starvation, and natural sleep exhaustion.",
            "Reinforced Chassis: Natural Armor Class increased by +2.",
            "Flaw - Machine Maintenance: Biological healing items are only 50% effective; requires tool repairs."
        ]
    },

    # 14 Brand New Lineages (Fantasy & Sci-Fi)
    "hellforged_tiefling": {
        "name": "Hellforged Fiendblood (Tiefling)",
        "genre": "Fantasy",
        "desc": "Infernal heritage manifested when the rift tore into planar fire-realms. Curled obsidian horns, sulfurous blood, and fiery resilience.",
        "stat_mods": {"CHA": 2, "INT": 2, "DEX": 1, "STR": 0, "CON": 0, "WIS": -1},
        "racial_abilities": [
            "Hellfire Flare: Can ignite melee weapon strikes with +1d4 infernal fire damage once per encounter.",
            "Infernal Resistance: Gain 25% passive damage reduction against fire and heat hazards.",
            "Darkvision: See clearly in non-magical darkness up to 60ft."
        ]
    },
    "celestial_aasimar": {
        "name": "Celestial Radiant (Aasimar)",
        "genre": "Fantasy",
        "desc": "Blessed with ambient astral light from uncorrupted celestial planes. Faint golden luminescence, halo-reflections, and purifying grace.",
        "stat_mods": {"WIS": 2, "CHA": 3, "CON": 1, "STR": 0, "DEX": 0, "INT": -1},
        "racial_abilities": [
            "Luminescent Touch: Release a burst of healing light restoring 15 HP to an ally (once per rest).",
            "Radiant Resistance: Passive 25% damage reduction against necrotic and void corruption.",
            "Celestial Visage: +2 on diplomacy and leadership checks."
        ]
    },
    "draconic_scion": {
        "name": "Draconic Scion (Dragonborn)",
        "genre": "Fantasy",
        "desc": "Dormant primeval reptile genomes mutated into thick iridescent dragon scales, slit pupils, and an elemental breath organ.",
        "stat_mods": {"STR": 3, "CHA": 2, "CON": 1, "DEX": -1, "INT": 0, "WIS": 0},
        "racial_abilities": [
            "Draconic Breath: Exhale a 15ft cone of elemental energy dealing 2d6 damage (once per rest).",
            "Dragon-Scale Armor: Natural AC increased by +1; resistant to elemental blasts.",
            "Intimidating Roar: Advantage on Intimidation checks against beasts and humanoids."
        ]
    },
    "changeling_mimic": {
        "name": "Changeling / Faceless Mimic",
        "genre": "Fantasy / Sci-Fi",
        "desc": "Unstable cellular matrix allowing rapid restructuring of facial features, voice chords, skin pigmentation, and body height.",
        "stat_mods": {"CHA": 3, "DEX": 2, "INT": 1, "STR": -1, "CON": 0, "WIS": 0},
        "racial_abilities": [
            "Cellular Shift: Magically alter facial appearance, voice, and build to impersonate any humanoid.",
            "Slippery Identity: +4 bonus to Deception and Stealth checks when undercover.",
            "Flaw - Identity Dissonance: Takes double psychic strain from mental probes."
        ]
    },
    "neuromancer_cyborg": {
        "name": "MageTech Cyborg (Crucible Conscript)",
        "genre": "MageTech / Biomechanical",
        "desc": "Survivors whose catastrophic trauma or pre-collapse medical implants were seized during Initialization and forcibly welded to high-torque pneumatic servos, runic copper conduits, and an aether-ocular reticle by the Cardinal System's auto-forges. Rebuilt as frontline biomechanical conscripts of the Crucible.",
        "stat_mods": {"STR": 2, "CON": 2, "INT": 1, "DEX": 1, "WIS": -1, "CHA": -1},
        "racial_abilities": [
            "Cardinal Telemetry Ocular: Retinal HUD crosshair scans enemy armor seams and weakpoints, granting +1 to hit against analyzed targets and displaying exact enemy HP percentages.",
            "Pneumatic Endoskeleton: Heavy titanium-composite bone reinforcement grants +1 Natural Armor Class, adds +25 lbs carrying capacity before encumbrance penalties, and grants +2 on Strength checks to break barriers or resist grappling.",
            "Innate Graft-Tolerance: Biomechanical conditioning increases baseline Golem-Graft Strain threshold by +15, allowing the character to install advanced cybernetic and monster grafts without neuro-vascular rejection.",
            "Flaw - Arc & EMP Conductivity: Lightning damage, electric arc spells, and electromagnetic pulse hazards deal +20% bonus damage and cause motor-servo jitter (-1 DEX penalty for 1 round following electrical damage)."
        ]
    },
    "mantid_insectoid": {
        "name": "Mantid Insectoid (Chittering Carapace)",
        "genre": "Sci-Fi / Alien",
        "desc": "Radical insectoid metamorphosis featuring chitinous armor plates, compound eyes, compound antennae, and barbed forearms.",
        "stat_mods": {"DEX": 3, "CON": 2, "STR": 1, "INT": 0, "WIS": 0, "CHA": -2},
        "racial_abilities": [
            "Chitinous Exoskeleton: Natural +2 AC against slashing and piercing attacks.",
            "Wall-Climber: Climb vertical surfaces and ceilings without movement speed penalties.",
            "Compound Vision: Cannot be flanked or caught flat-footed from behind."
        ]
    },
    "shade_touched": {
        "name": "Shade-Touched (Shadowstalker)",
        "genre": "Fantasy / Umbral",
        "desc": "Soul fused with umbral rift energies. Casts no natural shadow; skin has a faint dusky hue that absorbs direct light.",
        "stat_mods": {"DEX": 3, "WIS": 2, "INT": 1, "STR": -1, "CON": 0, "CHA": 0},
        "racial_abilities": [
            "Shadowstep: Teleport up to 30ft between two areas of dim light or darkness (once per encounter).",
            "Umbral Camouflage: Advantage on Stealth checks in dark or subterranean environments.",
            "Flaw - Photosensitivity: -1 to attack rolls in direct blinding sunlight without eye protection."
        ]
    },
    "ironjaw_orc": {
        "name": "Iron-Jaw Orc / Savage Born",
        "genre": "Fantasy",
        "desc": "Hulking muscular frame, prominent lower tusk canines, and a volcanic battle fury that shrugs off mortal wounds.",
        "stat_mods": {"STR": 4, "CON": 3, "WIS": 0, "DEX": -1, "INT": -1, "CHA": -1},
        "racial_abilities": [
            "Relentless Endurance: When reduced to 0 HP, drop to 1 HP instead (once per long rest).",
            "Savage Critical: Melee weapon critical hits roll an extra weapon damage die.",
            "Menacing Presence: +2 to Intimidation and morale break checks."
        ]
    },
    "nanite_host": {
        "name": "Nanite Swarm Symbiote",
        "genre": "Sci-Fi",
        "desc": "Ingested military nanite colonies in pre-integration research, now sustained by ambient aether and living tissue.",
        "stat_mods": {"CON": 3, "INT": 2, "DEX": 1, "STR": 0, "WIS": 0, "CHA": -1},
        "racial_abilities": [
            "Cellular Regeneration: Passively regenerates 2 HP per minute when out of active combat.",
            "Micro-Tool Extrusion: Extrude lockpicks, scalpel blades, or soldering tips directly from fingertips.",
            "Flaw - High Caloric Drain: Starvation and dehydration accumulate at double the normal rate."
        ]
    },
    "sylph_windstrider": {
        "name": "Sylph (Zephyr-Born)",
        "genre": "Fantasy",
        "desc": "Airy, buoyant biology infused with elemental aer-spirits. Unusually light on their feet, with hair that drifts as if caught in a breeze.",
        "stat_mods": {"DEX": 3, "WIS": 2, "CHA": 1, "STR": -2, "CON": 0, "INT": 0},
        "racial_abilities": [
            "Feather Fall: Naturally glide down from any height, immune to standard falling damage.",
            "Zephyr Burst: Increase movement speed by +50% for 2 rounds (once per encounter).",
            "Wind Guidance: Ranged arrow and spell accuracy penalty from heavy winds is ignored."
        ]
    },
    "sylvan_dryad": {
        "name": "Sylvan Thornborn (Fey-Touched)",
        "genre": "Fantasy",
        "desc": "Flesh intertwined with living chlorophytic vines, bark-like knuckles, and deep connection to wild flora and leyline root-networks.",
        "stat_mods": {"WIS": 3, "CON": 2, "CHA": 1, "STR": 0, "DEX": 0, "INT": -1},
        "racial_abilities": [
            "Root-Mend: Heal 10 HP when resting directly on fertile earth or natural soil.",
            "Thorn Bramble Skin: Melee attackers that strike you without reach suffer 1d4 piercing recoil damage.",
            "Flora Rapport: Communicate basic concepts with natural plants and trees."
        ]
    },
    "void_walker": {
        "name": "Void-Walker (Singularity Drifter)",
        "genre": "Sci-Fi / Cosmic",
        "desc": "Exposed directly to a zero-point spatial rift. Reality slightly bends around their periphery with faint distortion ripples.",
        "stat_mods": {"WIS": 3, "INT": 2, "DEX": 1, "STR": 0, "CON": -1, "CHA": 0},
        "racial_abilities": [
            "Phase Shift: Become incorporeal for 1 turn, avoiding all non-magical physical damage (once per combat).",
            "Spatial Anchor: Immune to being forcibly pushed, pulled, or banished through rifts.",
            "Flaw - Gravity Drift: Takes +25% increased fall damage if phase shift is on cooldown."
        ]
    },
    "amphibian_lizardfolk": {
        "name": "Saurian Dredge (Lizardfolk)",
        "genre": "Fantasy",
        "desc": "Cold-blooded scaled hunter adapted to marshlands, sewers, and flooded subway tunnels. Serrated claws and swimming tail.",
        "stat_mods": {"CON": 3, "STR": 2, "WIS": 1, "DEX": 0, "INT": -1, "CHA": -1},
        "racial_abilities": [
            "Amphibious Vigor: Hold breath for up to 30 minutes underwater; swim speed matches land speed.",
            "Natural Jaws: Secondary bite attack in melee dealing 1d6 piercing damage.",
            "Scavenger Guts: Immune to food poisoning and diseases from stale or raw meat."
        ]
    },
    "synthetic_android": {
        "name": "Synthetic Android (Printed Soul-Vessel)",
        "genre": "Pathfinder / Bio-Synthetic",
        "desc": "Derived from Pathfinder's Numerian synthetic humanoids and the Cardinal System's automated bio-foundries. Fabricated in deep subterranean print-vats from living carbon polymers, nanite circulatory fluid, and cold-forged porcelain/composite dermal plating. Created as disposable automated conscripts for the death-game, the planetary mana rupture unexpectedly seeded emergent souls and mortal consciousness into their logic cores.",
        "stat_mods": {"INT": 3, "DEX": 2, "CON": 1, "STR": 0, "WIS": 0, "CHA": -2},
        "racial_abilities": [
            "Synthetic Biology (Dual Nature): Counts as both Humanoid and Construct. Fully immune to biological diseases, atmospheric spores, and magical sleep effects. Biological healing and nanite repair items both function at full efficiency.",
            "Nanite Surge: Once per combat encounter or short rest, can trigger an internal nanite circulatory burst as a free action, adding a +4 bonus to any single attack roll, saving throw, or skill check, or immediately self-stabilizing at 1 HP upon falling unconscious.",
            "Logic-Core Discipline: Emotional suppression grants complete immunity to fear, intimidation, and charm/confusion spells. Grants +2 on tactical deduction, cryptography, and complex system query checks.",
            "Flaw - Empathy Void & Core Flush: Suffers a -2 penalty on Charisma (Persuasion, Animal Handling, and Empathy) checks with organic survivors. Requires a 4-hour stationary diagnostic stasis during long rests to cycle internal coolant and vent memory buffers."
        ]
    }
}

# --- CLASS PATHS & THEMED WEAPONS ---
CLASS_PATHS = {
    "warrior": {
        "title": "Warrior (Frontline Anchor)",
        "description": "Specialized in absorbing enemy aggro, breaking shields, controlling battlefield positioning, and anchoring frontlines.",
        "starting_feats": ["Shield Wall Stance", "Taunting War-Cry"],
        "combat_resource": {"name": "Poise & Threat", "max": 100, "current": 0, "type": "poise"},
        "base_hp": 120,
        "hp_per_lvl": 35,
        "native_armor": ["Heavy", "Medium"],
        "favored_skills": ["Trench Hammers", "One-Handed Axes", "Field Smithing"]
    },
    "mage": {
        "title": "Mage (Aether-Weaver)",
        "description": "Channels raw atmospheric mana into concentrated force projectiles, protective wards, and catastrophic elemental singularities.",
        "starting_feats": ["Arcane Ward", "Aetheric Dart"],
        "combat_resource": {"name": "Aetheric Flux", "max": 50, "current": 50, "type": "flux"},
        "base_hp": 80,
        "hp_per_lvl": 20,
        "native_armor": ["Cloth", "Light"],
        "favored_skills": ["Aether-Weaving", "Arcane Triage", "Provisions & Alchemy"]
    },
    "cleric": {
        "title": "Cleric (Spire Templar)",
        "description": "Battlefield medic and sanctified inquisitor wielding protective auras, emergency trauma restoration, and crushing mace strikes.",
        "starting_feats": ["Sanctified Ward", "Purifying Grace"],
        "combat_resource": {"name": "Devotion & Grace", "max": 100, "current": 50, "type": "devotion"},
        "base_hp": 105,
        "hp_per_lvl": 28,
        "native_armor": ["Medium", "Heavy"],
        "favored_skills": ["Arcane Triage", "Trench Hammers", "Provisions & Alchemy"]
    },
    "thief": {
        "title": "Thief (Shadow Infiltrator)",
        "description": "Acrobatic guerrilla rogue executing serrated backstabs, smoke-screen evasions, and fluid momentum chaining.",
        "starting_feats": ["Shadow Footwork", "Serrated Backstab"],
        "combat_resource": {"name": "Momentum Dice", "max": 5, "current": 1, "type": "momentum"},
        "base_hp": 90,
        "hp_per_lvl": 24,
        "native_armor": ["Light"],
        "favored_skills": ["One-Handed Axes", "Tactical Reflexes", "Field Trapping"]
    },
    "ranger": {
        "title": "Ranger (Wilderness Marksman)",
        "description": "Scout and sniper dominating extreme range, deploying lethal wire snares, and exploiting elevated vantage points.",
        "starting_feats": ["Hunter's Mark", "Deadeye Aim"],
        "combat_resource": {"name": "Focus & Vantage", "max": 5, "current": 3, "type": "focus"},
        "base_hp": 95,
        "hp_per_lvl": 28,
        "native_armor": ["Light", "Medium"],
        "favored_skills": ["Field Trapping", "Cartography", "Tactical Reflexes"]
    },
    "engineer": {
        "title": "Engineer / Artificer",
        "description": "Combat mechanist deploying automated sentry turrets, explosive traps, and venting superheated overclock steam.",
        "starting_feats": ["Deploy Sentry Turret", "Vent Overclock"],
        "combat_resource": {"name": "Heat & Overclock", "max": 100, "current": 0, "type": "heat"},
        "base_hp": 100,
        "hp_per_lvl": 28,
        "native_armor": ["Medium", "Heavy"],
        "favored_skills": ["Field Smithing", "Golem-Graft Rigging", "Magi-Tech Hacking"]
    },
    "psion": {
        "title": "Psion / Phrenic",
        "description": "Awakened mentalist projecting mind-shattering kinetic repulsion and psychic lances, walking the edge of cognitive strain.",
        "starting_feats": ["Kinetic Repulsion Barrier", "Mind Spike"],
        "combat_resource": {"name": "Psi-Strain", "max": 100, "current": 0, "type": "strain"},
        "base_hp": 85,
        "hp_per_lvl": 24,
        "native_armor": ["Cloth", "Light"],
        "favored_skills": ["Aether-Circuit Query", "Tactical Reflexes"]
    },
    "pathless": {
        "title": "Pathless (Freeform Anomaly)",
        "description": "Refuses to be bound by system constraints. Free to combine any weapons, spells, and doctrines across every level.",
        "starting_feats": ["Adaptive Weapon Mastery", "Unshackled Potential"],
        "combat_resource": {"name": "Anomaly Resonance", "max": 100, "current": 0, "type": "resonance"},
        "base_hp": 100,
        "hp_per_lvl": 25,
        "native_armor": ["Adaptive"],
        "favored_skills": ["Universal Versatility"]
    }
}

# Legacy aliases for backwards compatibility with tests and older saves
CLASS_PATHS["vanguard"] = dict(CLASS_PATHS["warrior"])
CLASS_PATHS["vanguard"]["title"] = "Vanguard (Heavy Frontliner)"
CLASS_PATHS["vanguard"]["base_hp"] = 100  # Preserved baseline for test calibration
CLASS_PATHS["magi_saboteur"] = dict(CLASS_PATHS["engineer"])
CLASS_PATHS["magi_saboteur"]["title"] = "Magi-Tech Saboteur"
CLASS_PATHS["aether_slinger"] = dict(CLASS_PATHS["mage"])
CLASS_PATHS["aether_slinger"]["title"] = "Aether-Slinger"
CLASS_PATHS["wilderness_ranger"] = dict(CLASS_PATHS["ranger"])
CLASS_PATHS["wilderness_ranger"]["title"] = "Wilderness Ranger"

CLASS_WEAPONS = {
    "warrior": {
        "main_hand": "Heavy Scavenged Mace",
        "off_hand": "Scrap-Plate Shield",
        "desc": "A dense rebar-reinforced iron mace paired with a riveted industrial scrap shield."
    },
    "mage": {
        "main_hand": "Aetheric Focusing Wand",
        "off_hand": "None",
        "desc": "A conductive brass-and-quartz resonator wand designed to project raw kinetic spells."
    },
    "cleric": {
        "main_hand": "Sanctified Flail",
        "off_hand": "Scrap-Plate Shield",
        "desc": "A heavy iron flail engraved with cleansing wards, paired with a reinforced scrap shield."
    },
    "thief": {
        "main_hand": "Concealed Trench Daggers",
        "off_hand": "Tanto Combat Knife",
        "desc": "Dual razor-sharp carbon trench blades tailored for high-speed puncture strikes."
    },
    "ranger": {
        "main_hand": "Recurve Hunting Bow",
        "off_hand": "Chipped Wood-Axe",
        "desc": "A composite outdoor hunting bow (with 20 carbon arrows) and a utility wood-axe."
    },
    "engineer": {
        "main_hand": "Arcane Stun-Pistol",
        "off_hand": "Tanto Combat Knife",
        "desc": "A low-charge shock-pulse sidearm paired with a serrated carbon combat knife."
    },
    "psion": {
        "main_hand": "Kinetic Shock-Staff",
        "off_hand": "None",
        "desc": "A resonant quartz-tipped walking staff that projects and channels telekinetic pulses."
    },
    "pathless": {
        "main_hand": "Rusted Iron Sword",
        "off_hand": "None",
        "desc": "A jagged, balance-heavy salvage blade scavenged from highway guardrails."
    }
}

CLASS_WEAPONS["vanguard"] = CLASS_WEAPONS["warrior"]
CLASS_WEAPONS["magi_saboteur"] = CLASS_WEAPONS["engineer"]
CLASS_WEAPONS["aether_slinger"] = CLASS_WEAPONS["mage"]
CLASS_WEAPONS["wilderness_ranger"] = CLASS_WEAPONS["ranger"]

STARTER_WEAPON_OPTIONS = [
    "Rusted Iron Sword",
    "Heavy Scavenged Mace",
    "Scrap-Plate Shield",
    "Arcane Stun-Pistol",
    "Tanto Combat Knife",
    "Aetheric Focusing Wand",
    "Recurve Hunting Bow",
    "Chipped Wood-Axe",
    "Sanctified Flail",
    "Concealed Trench Daggers",
    "Kinetic Shock-Staff",
    "Reinforced Spear",
    "Twin Scavenger Daggers",
    "None"
]

# --- 17 PRE-INTEGRATION PERSONAL RELICS ---
PERSONAL_RELICS = {
    # Original 5 Relics
    "smartphone": {
        "name": "Earth Smartphone (99% Battery, No Signal)",
        "rarity": "Unique",
        "category": "Psychological Anchor & Illuminator",
        "durability": 99,
        "max_durability": 100,
        "qty": 1,
        "desc": "A personal flagship smartphone with a spiderweb fracture across the Gorilla Glass screen. Held in an otterbox case, it displays 99% battery, zero cellular bars, and the offline calendar locked onto the final afternoon before the Rift collapse. Its memory stores unread text messages from family ('Where are you? Dinner is cold'), offline music playlists, photos of pets, and an encrypted corporate employee app.",
        "mechanics": "Psychological Anchor: Gazing at family photos during a short rest cures 1 level of cognitive stress / psychological despair and provides advantage on the next saving throw against cosmic madness or horror. Emergency Lumens: Emits a 20ft cone of LED light without open flame. Encrypted Cache: Once per day, querying offline notes grants +2 on an INT check regarding pre-collapse Earth history or engineering. Battery drains 1% per 10 active uses (99 charges total; cannot recharge until MageTech dynamo power is discovered)."
    },
    "multitool": {
        "name": "Mechanic's Heavy Multi-Tool",
        "rarity": "Uncommon",
        "category": "Field Crafting & Rigging",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "Hardened carbon-steel pliers, wire-strippers, carbide wire-cutters, serrated wood/bone saw, can opener, and magnetic bit driver with hardened hex heads in a ballistic nylon belt sheath.",
        "mechanics": "Field Maintenance: Permanent +2 bonus on all Field Smithing and mechanical repair checks. Reduces Col repair costs at field anvils by 25%. Improvised Rigging: Deploy or disarm mechanical wire traps and snares without requiring specialized thieves' tools (+5 to disarm trap checks). Pry & Lever: Advantage on STR checks to pry open jammed vehicle doors, locked junction boxes, and rusted scrap grates."
    },
    "first_aid_pouch": {
        "name": "Trauma First-Aid Pouch",
        "rarity": "Uncommon",
        "category": "Emergency Medical Triage",
        "durability": 3,
        "max_durability": 3,
        "qty": 1,
        "desc": "A zippered olive-drab ripstop nylon medical pouch stamped with a faded red cross. Contains sterile trauma dressings, celox hemostatic clotting powder, a compact windlass tourniquet, antiseptic burn wash, and nitrile gloves.",
        "mechanics": "Rapid Hemostasis (3 Charges): Bonus action or reaction in combat to immediately cure [Bleeding] or [Hemorrhage] on self or adjacent ally, and restore 1d8+2 HP. Antiseptic Wash: Applying wash to infected wounds grants immediate advantage on target's next saving throw against gangrene, sepsis, or monster biological venom. Depletes 1 durability charge per field triage use."
    },
    "city_map": {
        "name": "Laminated Regional Topo-Map",
        "rarity": "Uncommon",
        "category": "Tactical Navigation & Cartography",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "Waterproof, double-sided USGS topographical quadrangle map of Warren County, New Jersey (covering Washington Borough, Pohatcong Mountain, Oxford, and Delaware Water Gap) marked with elevation contour lines, river basins, power substations, and grease pencil circles.",
        "mechanics": "Terrain Mastery: Grants +5 starting mastery to Cartography and reveals hidden topographical waypoints, freshwater springs, and high-ground vantage points on the Sector 1 Map overlay. Overland Efficiency: Party overland travel speed across Sector 1 is increased by 15%; immune to becoming naturally lost in non-magical terrain. Tactical Chokepoints: Studying map before combat grants +2 to party initiative."
    },
    "pocket_watch": {
        "name": "Heirloom Pocket-Watch",
        "rarity": "Rare",
        "category": "Spatial & Temporal Detection",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "Heavy, hand-wound Swiss mechanical pocket-watch in an antiqued solid brass hunter case with Albert chain. Its ruby-jeweled movement ticks with rhythmic precision, immune to electromagnetic pulses or atmospheric aether static.",
        "mechanics": "Glitch-Rift Resonance: The escapement wheel vibrates and chimes loudly within 100ft of an unstable Aetheric Rift, spatial anomaly, or phased entity, preventing surprise attacks. Chrono-Pacing: Displays exact astronomical time and minutes to dawn/dusk, ensuring party is never caught unprepared by night-cycle difficulty escalations. Temporal Focus (1/Long Rest): Gain +2 on all Reaction saving throws for 10 minutes."
    },

    # 12 Brand New Thematic Relics
    "noise_cancelling_headphones": {
        "name": "Noise-Cancelling Headphones",
        "rarity": "Uncommon",
        "category": "Auditory & Sensory Defense",
        "durability": 80,
        "max_durability": 100,
        "qty": 1,
        "desc": "Over-ear cushioned headset with memory foam protein leather ear pads and active hybrid acoustic noise-cancellation circuitry. Scuffed along the headband from rapid evacuation.",
        "mechanics": "Acoustic Dampening: Complete immunity to auditory sensory overload, disorienting supersonic bangs, and monster sonic shrieks (Banshee wails, Harpy calls, Bat-fiend pulses). Psychological Bubble: Wearing while resting blocks out distressing environmental noises (howling wind, dark dungeon growls), ensuring uninterrupted rest. Trade-off: Suffers -2 penalty on passive Perception checks reliant strictly on ambient sound."
    },
    "tritium_compass": {
        "name": "Military Tritium Lensatic Compass",
        "rarity": "Uncommon",
        "category": "Leyline & Night Navigation",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "Rugged olive-drab aluminum casing lensatic compass with sighting wire and self-luminous radioactive gaseous tritium vials (green glow) that require no sunlight exposure or battery power to glow in total darkness.",
        "mechanics": "Leyline Divergence Gauge: Magnetic needle responds to both Earth's magnetic poles and ambient mana gradients; wobbles and points toward nearest leyline convergence or magical node. Night Navigation: Green tritium vials permit silent, zero-light compass navigation in pitch-black caves without torches. Dead-Reckoning: Advantage on Survival checks to navigate through blinding blizzards, fogs, and toxic ash clouds."
    },
    "zippo_lighter": {
        "name": "Engraved Brass Zippo Lighter",
        "rarity": "Uncommon",
        "category": "Pyrotechnic & Gas Detection",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "Windproof brushed brass lighter with a satisfying snap-lid click and engraved motto ('Keep Moving Forward'). Smelling faintly of naphtha fuel, its cotton wick and flint spark wheel are battle-tested and reliable.",
        "mechanics": "Instant Ignition: Lights campfires, torches, and stoves instantly in any weather conditions, bypassing wind, rain, and damp wood penalties. Vapor Detection: Holding flame low detects invisible natural gas, methane pockets, and swamp fumes before detonation (flame flares bright blue to warn party). Combat Spark: Free action in combat to ignite oil flasks, molotov cocktails, or alchemical haze pellets."
    },
    "dogeared_novel": {
        "name": "Dog-Eared Sci-Fi Paperback",
        "rarity": "Uncommon",
        "category": "Psychological Refresh & Ingenuity",
        "durability": 50,
        "max_durability": 50,
        "qty": 1,
        "desc": "A battered mass-market paperback novel (classic speculative fiction) with creased yellow pulp pages, split spine glue, and penciled margins. Smells of vanilla paper lignin and old-world bookstore nostalgia.",
        "mechanics": "Cognitive Refresh: Reading one chapter during a short rest (30 min) clears mental fatigue, granting +10 Focus/Mana and a +1 bonus to INT and WIS saving throws for 2 hours. Imaginative Blueprinting: Exposure to speculative tropes grants +1 bonus to Magi-Tech Hacking and unconventional puzzle solving. Emergency Tinder: In sub-zero emergencies, pages can be torn out to kindle 5 separate emergency fires (+2 to frostbite survival checks)."
    },
    "chalk_carabiners": {
        "name": "Climber's Carabiners & Chalk Bag",
        "rarity": "Uncommon",
        "category": "Athletics & Weapon Grip",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "Two heavy-duty, screw-gate asymmetrical D-shaped aluminum climbing carabiners paired with a fleece-lined ripstop waist pouch filled with compressed magnesium carbonate chalk powder.",
        "mechanics": "Grip Assurance: Chalking hands ensures a secure hold, preventing held weapons from being disarmed or dropped due to monster slime, slick blood, or torrential rain. Climbing Anchor: Advantage on Athletics checks to ascend sheer rock faces, elevator shafts, and collapsed highway overpasses. Silent Rappel Rigging: Reduces time required to set up a safe rope descent by 50%."
    },
    "polaroid_camera": {
        "name": "Vintage Polaroid Camera (3 Films Left)",
        "rarity": "Rare",
        "category": "Paranormal Detection & Flash Stun",
        "durability": 3,
        "max_durability": 3,
        "qty": 1,
        "desc": "An analog instant camera from the late 1980s with textured gray housing, rainbow stripe logo, and built-in optical flash bar. Loaded with an authentic vintage film cartridge with exactly 3 remaining chemical exposures.",
        "mechanics": "Specter-Capture Exposure (3 Charges): Snapping a photo and developing the chemical print (60 sec) captures invisible entities, phased stalkers, hidden illusion doors, or arcane sigils invisible to the naked human eye. Flash Stun (Reaction): Pyrotechnic flash can be discharged in combat to inflict [Blinded] on an adjacent attacker for 1 turn (costs 1 film charge). Photos become permanent inventory proof of paranormal encounters."
    },
    "tactical_flashlight": {
        "name": "2000-Lumen Tactical Strobe Flashlight",
        "rarity": "Uncommon",
        "category": "Illumination & Combat Disorientation",
        "durability": 75,
        "max_durability": 100,
        "qty": 1,
        "desc": "Matte black aircraft-grade anodized aluminum tactical flashlight featuring an ultra-bright Cree XHP LED emitter, strike bezel ring with glass-breaker crenellations, and IP68 waterproof tail-switch.",
        "mechanics": "Target Dazzle / Strobe: 15Hz strobe forces a DC 14 CON save on light-sensitive subterranean beasts or humanoids within 30ft; on failure, target suffers [Dazzled] (-2 to attack rolls for 2 rounds). Deep High-Beam: Illuminates 150ft beam of daylight-equivalent white light, penetrating supernatural gloom. Strike Bezel: Functions as an improvised light bludgeoning weapon in melee dealing 1d4+STR damage (10% stun chance on crit). 75/100 battery remaining."
    },
    "guitar_tuning_fork": {
        "name": "Harmonic Steel Tuning Fork (440Hz)",
        "rarity": "Uncommon",
        "category": "Acoustic Disruption & Sonar",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "Precision-machined, nickel-plated surgical steel acoustic tuning fork calibrated to Concert Pitch A (440 Hz). Produces a pure, crystalline sine wave that hums through bone and air when struck.",
        "mechanics": "Resonant Disruptor: Striking fork and holding near active magical ward, barrier, or rune trap creates destructive acoustic interference, reducing DC to dispel/disarm by 3. False-Wall Sonar: Placing vibrating stem against dungeon walls detects hollow chambers and hidden doors via frequency shifts. Aetheric Calibration: Grants +5% bonus experience gain to all sound-based or sonic magic skills."
    },
    "thermos_coffee": {
        "name": "Vacuum-Insulated Coffee Thermos",
        "rarity": "Uncommon",
        "category": "Thermal Sustenance & Cold Ward",
        "durability": 3,
        "max_durability": 3,
        "qty": 1,
        "desc": "Heavy double-walled 18/8 kitchen-grade stainless steel thermos bottle with powder-coated hunter green finish. Miraculously, its airtight silicone seal preserved piping-hot dark roast drip coffee from the morning of Integration.",
        "mechanics": "Thermal Stamina Draught (3 Sips Left): Taking a hot sip in the field instantly restores 15 Stamina/Mana, clears 1 level of physical exhaustion, and provides a +2 bonus to Initiative rolls for 1 hour. Hypothermia Ward: Consuming a sip during freezing weather or Glitch Freeze grants complete immunity to Frostbite damage for 4 hours. Indestructible Flask: Empty container can be refilled with boiling liquids or broths without degrading."
    },
    "santoku_knife": {
        "name": "Black Ceramic Chef's Santoku Knife",
        "rarity": "Uncommon",
        "category": "Non-Metallic Stealth & Butchery",
        "durability": 60,
        "max_durability": 60,
        "qty": 1,
        "desc": "7-inch Japanese-style culinary knife made from ultra-hard zirconium oxide ceramic with an ebony composite handle. Mirror-smooth and impervious to rust, acids, or biological rot, with a razor edge.",
        "mechanics": "Non-Metallic Stealth Weapon: Undetectable by metal detectors, magnetic traps, and ferro-kinetic magic. Equippable as off-hand blade dealing 1d6 piercing/slashing damage. Pristine Edge: Does not lose durability cutting flesh or herbs; grants +2 on all Field Butchery and skinning checks to harvest pristine beast hides. Brittle Seam: Striking solid steel plate armor or stone causes 5 points of durability damage."
    },
    "usb_family_drive": {
        "name": "Keychain USB (Home Videos & Photos)",
        "rarity": "Rare",
        "category": "Psychological Bastion & Defiance",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "Waterproof, shockproof aluminum thumb drive on a split-ring key loop labeled 'Family Archive 2010-2024'. Stores 64GB of home videos, Thanksgiving dinners, wedding vows, road trips, and baby laughs.",
        "mechanics": "Sentimental Bastion: Advantage on all saving throws against mind control, psychic horror, despair, and sanity erosion. Unbreakable Hope (1/Encounter Reaction): When player HP is reduced to 0 by a lethal attack, grasping the drive allows a DC 12 WIS check; on success, player clings to life with 1 HP instead. Terminal Compatibility: Can be plugged into pre-collapse Earth computers to unlock personal lore logs."
    },
    "laser_rangefinder": {
        "name": "Hunting Laser Rangefinder",
        "rarity": "Uncommon",
        "category": "Ballistic Telemetry & Ranging",
        "durability": 85,
        "max_durability": 100,
        "qty": 1,
        "desc": "Rubber-armored digital monocular laser rangefinder used by precision marksmen. Features an LCD reticle displaying line-of-sight distance in yards, true horizontal angle compensation, and scan mode.",
        "mechanics": "Ballistic Ranging: Spending a minor action to range an enemy before firing eliminates distance penalties for bows, crossbows, and firearms up to 200 yards, and grants +2 on the next ranged attack roll. True Elevation: Automatically calculates horizontal distance when aiming up or down steep cliffs or towers. Operates on CR2 lithium cell with 85/100 battery remaining (1 charge per 10 range scans)."
    }
}

def create_custom_relic(name, desc, ability_text="Sentimental Anchor"):
    """Creates a custom write-in personal relic with user-provided flavor and ability."""
    safe_name = name.strip() if name and name.strip() else "Pre-Integration Keepsake"
    safe_desc = desc.strip() if desc and desc.strip() else "A sentimental relic carried through the rift."
    safe_ability = ability_text.strip() if ability_text and ability_text.strip() else "Carries emotional warmth from Earth."
    return {
        "name": safe_name,
        "rarity": "Custom Relic",
        "category": "Custom Keepsake",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": f"{safe_desc} (Effect: {safe_ability})",
        "mechanics": safe_ability,
        "custom_ability": safe_ability
    }

# --- CUSTOM BACKGROUND COLLABORATIVE PARSER & CONSULTANT ---
def parse_custom_background(text):
    """
    Procedurally maps arbitrary custom Earth vocation descriptions into 2 balanced 1-1000 skills
    and a unique passive perk using rich semantic keyword analysis.
    """
    t = text.lower() if text else ""
    
    if any(k in t for k in ["electric", "circuit", "cable", "tech", "computer", "hack", "network", "code", "cyber"]):
        s1 = ("Magi-Tech Hacking", 45, "Bypassing arcane firewalls, terminal encryption, and logic wards.")
        s2 = ("Aether-Circuit Query", 35, "Tracing energy lines and construct signal routing.")
        perk = "Circuit Intuition (Passive): Gain +2 on checks to manipulate, decrypt, or repair aetheric terminals."
    elif any(k in t for k in ["medic", "doctor", "nurse", "surgery", "hospital", "clinic", "heal", "paramedic", "emt"]):
        s1 = ("Arcane Triage", 50, "Stabilizing biological vitals and treating acute aetheric trauma.")
        s2 = ("Field Surgery", 40, "Extracting crystalline shrapnel and repairing damaged tissue.")
        perk = "Triage Discipline (Passive): Healing checks take half as much time and reduce bleeding DC by 2."
    elif any(k in t for k in ["mechanic", "machinist", "weld", "engine", "car", "fix", "repair", "craft", "metal"]):
        s1 = ("Field Smithing", 50, "Reforging weapons, repairing armor plates, and maintaining mechanical gear.")
        s2 = ("Golem-Graft Rigging", 40, "Tuning prosthetic joints, hydraulic seals, and aether-couplings.")
        perk = "Structural Assessment (Passive): Instantly evaluate fracture points on armor, barricades, and constructs."
    elif any(k in t for k in ["hunt", "fish", "camp", "outdoor", "woods", "forest", "scout", "track", "ranger"]):
        s1 = ("Field Trapping", 50, "Deployment and concealment of wire snares and perimeter traps.")
        s2 = ("Cartography", 45, "Topographical parsing, terrain mapping, and landmark navigation.")
        perk = "Wilderness Instinct (Passive): Gain advantage on initiative checks when ambushed in natural terrain."
    elif any(k in t for k in ["construct", "carpenter", "build", "mason", "labor", "demolition", "roof"]):
        s1 = ("Trench Hammers", 50, "Bludgeoning armor-crush strikes and heavy structural demolition attacks.")
        s2 = ("Structural Breach", 40, "Targeting load-bearing structures and reinforced bulkheads.")
        perk = "Kinetic Impact (Passive): Bludgeoning attacks against constructs and barriers deal +2 bonus damage."
    elif any(k in t for k in ["martial", "combat", "fight", "box", "soldier", "military", "guard", "bjj", "wrestling"]):
        s1 = ("One-Handed Axes", 50, "Fast, brutal chops, hooks, and cleaves with single-handed blades.")
        s2 = ("Tactical Reflexes", 45, "Close-quarters footwork and split-second dodging.")
        perk = "Combat Readiness (Passive): +2 bonus to passive Armor Class during the first round of melee."
    elif any(k in t for k in ["cook", "chef", "bake", "food", "kitchen", "brew", "cater", "culinary"]):
        s1 = ("Provisions & Alchemy", 50, "Brewing restorative elixirs and preparing nutritious stamina rations.")
        s2 = ("Aether-Weaving", 40, "Refining organic materials with ambient mana.")
        perk = "Comforting Ration (Passive): Consumed food buffs grant double stamina recovery and restore focus."
    elif any(k in t for k in ["sales", "negotiat", "law", "business", "exec", "manag", "hr", "finance", "trade"]):
        s1 = ("Resource Barter", 50, "Assessing market value and securing favorable trade contracts.")
        s2 = ("Faction Diplomacy", 40, "Navigating guild politics and safe-zone syndicates.")
        perk = "Silver Tongue (Passive): Safe-zone automated merchant casualty markups are discounted by 15%."
    elif any(k in t for k in ["teach", "school", "profess", "educat", "counsel", "coach"]):
        s1 = ("Leadership & Rally", 45, "Bolstering ally morale, synchronizing combat formations, and clearing fear.")
        s2 = ("Lore Cataloging", 45, "Analytical deduction of monster behaviors and identifying environmental hazards.")
        perk = "Pedagogical Clarity (Passive): When calling out targets, all allies receive +1 to hit against that enemy."
    elif any(k in t for k in ["plant", "garden", "botan", "farm", "crop", "florist"]):
        s1 = ("Flora Harvesting", 50, "Extracting delicate herbs, spores, and sap without damaging specimen yields.")
        s2 = ("Provisions & Alchemy", 40, "Synthesizing herbal poultices and organic tonics.")
        perk = "Symbiotic Harmony (Passive): Harvest yields from wild vegetation are increased by 50%."
    elif any(k in t for k in ["art", "paint", "music", "draw", "dance", "actor"]):
        s1 = ("Aether-Weaving", 50, "Manipulating harmonic leyline frequencies and weaving visual illusions.")
        s2 = ("Tactical Reflexes", 40, "Acrobatic spatial agility, stage footwork, and balance.")
        perk = "Resonant Expression (Passive): Bardic and acoustic abilities have their area of effect doubled."
    elif any(k in t for k in ["drive", "truck", "pilot", "fly", "plane", "racing", "boat", "sail"]):
        s1 = ("Vehicle Rigging & Transit", 50, "Operating, repairing, and steering overland crawlers and carts.")
        s2 = ("Cartography", 40, "Interstate navigation, route optimization, and chokepoint awareness.")
        perk = "Throttle Sense (Passive): Travel speed with any mount or vehicle is boosted by +20%."
    else:
        # Balanced generalist fallback
        s1 = ("Survival Conditioning", 45, "Endurance, foraging, and improvised threat response.")
        s2 = ("Tactical Reflexes", 40, "Close-quarters footwork and situational awareness.")
        perk = "Adaptable Survivor (Passive): Reroll one failed skill check per long rest."
        
    skills = {
        s1[0]: {
            "mastery": s1[1],
            "tier": "Apprentice" if s1[1] >= 50 else "Novice",
            "description": s1[2],
            "milestones_unlocked": [50] if s1[1] >= 50 else []
        },
        s2[0]: {
            "mastery": s2[1],
            "tier": "Apprentice" if s2[1] >= 50 else "Novice",
            "description": s2[2],
            "milestones_unlocked": [50] if s2[1] >= 50 else []
        }
    }
    
    return {
        "title": f"Custom Background: {text[:32]}..." if len(text) > 32 else f"Custom: {text}",
        "description": text,
        "skills": skills,
        "innate_perk": perk
    }

def consult_custom_background(user_text, api_key=None, follow_up_notes=None):
    """
    Consults with the player to collaborate on custom 1-1000 skills and perks.
    Uses Gemini API if key is available, falling back gracefully to heuristic parsing.
    Returns:
      {
        "evaluation_message": str,
        "skill_1": {"name": str, "mastery": int, "description": str},
        "skill_2": {"name": str, "mastery": int, "description": str},
        "innate_perk": str
      }
    """
    if not user_text or not user_text.strip():
        user_text = "General survivor with diverse civilian life experiences."

    # Try LLM Consultation if API key is active
    if api_key and api_key != "your_api_key_here":
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            prompt = f"""You are the Cardinal System, the all-seeing LitRPG AI governing The Fractured Overlay.
The player is an Earth civilian undergoing the Biometric Calibration Protocol.
Player's Pre-Integration Life Description:
"{user_text}"

Player's Desired Custom Direction / Collaboration Notes:
"{follow_up_notes or 'None provided. Evaluate based on life description.'}"

Work collaboratively with the player. Propose two balanced 1-1000 skills and one unique passive perk.
- Skill 1: Primary vocation skill (Mastery between 45 and 60, Apprentice tier).
- Skill 2: Secondary support or survival skill (Mastery between 35 and 45, Novice tier).
- Innate Perk: Balanced passive trait named "Perk Name (Passive): Short effect description".
- Evaluation Message: 2-3 sentences of immersive, atmospheric Cardinal System diagnostic voice addressing the player.

Return ONLY valid JSON matching this schema:
{{
  "evaluation_message": "Biometric neural trace parsed...",
  "skill_1": {{"name": "Skill Name", "mastery": 50, "description": "Short description"}},
  "skill_2": {{"name": "Skill Name", "mastery": 40, "description": "Short description"}},
  "innate_perk": "Perk Title (Passive): Description..."
}}
"""
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3
                )
            )
            data = json.loads(response.text)
            if "skill_1" in data and "skill_2" in data and "innate_perk" in data:
                return data
        except Exception:
            pass  # Fall through to offline heuristic consultation

    # Offline Heuristic Consultation
    parsed = parse_custom_background(user_text)
    s_names = list(parsed["skills"].keys())
    s1_data = parsed["skills"][s_names[0]]
    s2_data = parsed["skills"][s_names[1]]
    
    return {
        "evaluation_message": f"Biometric anomaly scan complete. Synaptic memory query confirms pre-collapse vocation imprint: '{user_text[:60]}...'. Cardinal translation matrix has synthesized two foundational 1-1000 skills and an innate survival trait for your avatar.",
        "skill_1": {
            "name": s_names[0],
            "mastery": s1_data["mastery"],
            "description": s1_data["description"]
        },
        "skill_2": {
            "name": s_names[1],
            "mastery": s2_data["mastery"],
            "description": s2_data["description"]
        },
        "innate_perk": parsed["innate_perk"]
    }

# --- CHARACTER-FOLDER SAVE SYSTEM HELPERS ---
def sanitize_character_slug(name):
    """Sanitizes character name for filesystem directory names."""
    if not name or not name.strip():
        return "Survivor"
    slug = re.sub(r'[^a-zA-Z0-9_\- ]', '', name).strip().replace(' ', '_')
    return slug if slug else "Survivor"

def get_character_save_dir(base_dir, character_name):
    """Returns absolute path to a specific character's save folder: <base_dir>/saves/<character_slug>"""
    slug = sanitize_character_slug(character_name)
    saves_root = os.path.join(base_dir, 'saves')
    os.makedirs(saves_root, exist_ok=True)
    char_dir = os.path.join(saves_root, slug)
    os.makedirs(char_dir, exist_ok=True)
    return char_dir

def save_character_to_folder(base_dir, player_state, messages=None, extra_meta=None):
    """
    Saves character gamestate into a dedicated folder: saves/<character_name>/save_game.json.
    Also updates saves/<character_name>/profile.json and mirrors root save_game.json.
    """
    p_name = player_state.get("name", "Survivor")
    char_dir = get_character_save_dir(base_dir, p_name)
    save_file = os.path.join(char_dir, "save_game.json")
    profile_file = os.path.join(char_dir, "profile.json")
    
    full_data = {
        "player": player_state,
        "messages": messages or [],
        "last_saved": time.time()
    }
    if extra_meta:
        full_data.update(extra_meta)
        
    with open(save_file, 'w', encoding="utf-8") as f:
        json.dump(full_data, f, indent=4)
        
    # Write quick summary manifest for rapid profile picking
    manifest = {
        "name": p_name,
        "slug": sanitize_character_slug(p_name),
        "level": player_state.get("level", 1),
        "race": player_state.get("race", "Pure Human"),
        "class": player_state.get("class", "Pathless (Freeform Anomaly)"),
        "hp": f"{player_state.get('hp', 100)} / {player_state.get('max_hp', 100)}",
        "col": player_state.get("col", 100),
        "location": player_state.get("location", "Sector 1 Safe-Zone: Washington Borough, NJ"),
        "last_saved": full_data["last_saved"]
    }
    with open(profile_file, 'w', encoding="utf-8") as f:
        json.dump(manifest, f, indent=4)
        
    # Mirror to root save_game.json so CLI tools, tests, and legacy scripts continue working
    root_save = os.path.join(base_dir, "save_game.json")
    try:
        with open(root_save, 'w', encoding="utf-8") as f:
            json.dump(full_data, f, indent=4)
    except Exception:
        pass
        
    return save_file

def load_character_from_folder(base_dir, character_name):
    """Loads gamestate from saves/<character_name>/save_game.json."""
    char_dir = get_character_save_dir(base_dir, character_name)
    save_file = os.path.join(char_dir, "save_game.json")
    if os.path.exists(save_file):
        with open(save_file, 'r', encoding="utf-8") as f:
            return json.load(f)
    return None

def list_all_character_folders(base_dir):
    """
    Discovers all character save folders in saves/.
    Auto-migrates any legacy flat files (saves/<slug>.json) into dedicated folders.
    Returns list of manifest dictionaries sorted by most recent save.
    """
    saves_root = os.path.join(base_dir, 'saves')
    if not os.path.exists(saves_root):
        os.makedirs(saves_root, exist_ok=True)
        
    # 1. Check for legacy flat .json files in saves/ and migrate to dedicated folder
    for item in list(os.listdir(saves_root)):
        item_path = os.path.join(saves_root, item)
        if os.path.isfile(item_path) and item.endswith('.json'):
            slug = os.path.splitext(item)[0]
            target_dir = os.path.join(saves_root, slug)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
                try:
                    with open(item_path, 'r', encoding="utf-8") as f_old:
                        c_data = json.load(f_old)
                    with open(os.path.join(target_dir, "save_game.json"), 'w', encoding="utf-8") as f_new:
                        json.dump(c_data, f_new, indent=4)
                    os.remove(item_path)
                except Exception:
                    pass

    # 2. Collect all directories containing save_game.json
    profiles = []
    for item in os.listdir(saves_root):
        char_dir = os.path.join(saves_root, item)
        if os.path.isdir(char_dir):
            save_file = os.path.join(char_dir, "save_game.json")
            if os.path.exists(save_file):
                prof_manifest = os.path.join(char_dir, "profile.json")
                if os.path.exists(prof_manifest):
                    try:
                        with open(prof_manifest, 'r', encoding="utf-8") as f:
                            profiles.append(json.load(f))
                            continue
                    except Exception:
                        pass
                # Fallback: parse save_game.json directly
                try:
                    with open(save_file, 'r', encoding="utf-8") as f:
                        data = json.load(f)
                    p = data.get("player", {})
                    profiles.append({
                        "name": p.get("name", item),
                        "slug": item,
                        "level": p.get("level", 1),
                        "race": p.get("race", "Unknown"),
                        "class": p.get("class", "Unknown"),
                        "hp": f"{p.get('hp', 100)} / {p.get('max_hp', 100)}",
                        "col": p.get("col", 0),
                        "location": p.get("location", "Sector 1"),
                        "last_saved": data.get("last_saved", 0)
                    })
                except Exception:
                    pass
                    
    profiles.sort(key=lambda x: x.get("last_saved", 0), reverse=True)
    return profiles

# --- CHARACTER SHEET GENERATOR ---
def generate_starting_character(name, point_alloc, background_key, race_key, class_key, relic_key, 
                                custom_background_text=None, starting_weapons=None,
                                custom_relic_data=None, custom_collaborated_data=None):
    """
    Constructs a complete, valid player character dictionary ready for save_game.json.
    Supports class-themed starter weapons with optional manual override,
    custom collaborative background skills, and custom personal relics.
    """
    # 1. Base Stats (10 base + allocated points + racial mods)
    race = RACIAL_LINEAGES.get(race_key, RACIAL_LINEAGES["pure_human"])
    r_mods = race["stat_mods"]
    
    final_stats = {
        "STR": 10 + point_alloc.get("STR", 0) + r_mods.get("STR", 0),
        "DEX": 10 + point_alloc.get("DEX", 0) + r_mods.get("DEX", 0),
        "CON": 10 + point_alloc.get("CON", 0) + r_mods.get("CON", 0),
        "INT": 10 + point_alloc.get("INT", 0) + r_mods.get("INT", 0),
        "WIS": 10 + point_alloc.get("WIS", 0) + r_mods.get("WIS", 0),
        "CHA": 10 + point_alloc.get("CHA", 0) + r_mods.get("CHA", 0),
    }
    
    # 2. Chosen Class & Derived Attributes
    chosen_class = CLASS_PATHS.get(class_key, CLASS_PATHS["pathless"])
    con_mod = (final_stats["CON"] - 10) // 2
    base_hp_val = chosen_class.get("base_hp", 100)
    max_hp = base_hp_val + (con_mod * 10)
    
    # 3. Skills & Perks from Background (Preset, Custom Collaboration, or Heuristic)
    skills_dict = {}
    feats_list = list(race["racial_abilities"])
    
    if background_key == "custom":
        if custom_collaborated_data:
            s1_info = custom_collaborated_data.get("skill_1", {})
            s2_info = custom_collaborated_data.get("skill_2", {})
            perk = custom_collaborated_data.get("innate_perk", "Adaptable Survivor (Passive)")
            
            s1_name = s1_info.get("name", "Survival Conditioning")
            s1_mst = s1_info.get("mastery", 50)
            skills_dict[s1_name] = {
                "mastery": s1_mst,
                "tier": "Apprentice" if s1_mst >= 50 else "Novice",
                "description": s1_info.get("description", "Improvised survival."),
                "milestones_unlocked": [50] if s1_mst >= 50 else []
            }
            
            s2_name = s2_info.get("name", "Tactical Reflexes")
            s2_mst = s2_info.get("mastery", 40)
            skills_dict[s2_name] = {
                "mastery": s2_mst,
                "tier": "Apprentice" if s2_mst >= 50 else "Novice",
                "description": s2_info.get("description", "Situational awareness."),
                "milestones_unlocked": [50] if s2_mst >= 50 else []
            }
            if perk:
                feats_list.append(perk)
        elif custom_background_text:
            bg = parse_custom_background(custom_background_text)
            if bg.get("innate_perk"):
                feats_list.append(bg["innate_perk"])
            for s_name, s_data in bg.get("skills", {}).items():
                skills_dict[s_name] = dict(s_data)
        else:
            bg = PRESET_BACKGROUNDS["software_engineer"]
            if bg.get("innate_perk"):
                feats_list.append(bg["innate_perk"])
            for s_name, s_data in bg.get("skills", {}).items():
                skills_dict[s_name] = dict(s_data)
    else:
        bg = PRESET_BACKGROUNDS.get(background_key, PRESET_BACKGROUNDS["software_engineer"])
        if bg.get("innate_perk"):
            feats_list.append(bg["innate_perk"])
        for s_name, s_data in bg.get("skills", {}).items():
            skills_dict[s_name] = dict(s_data)
        
    # Add Class Feats
    for f in chosen_class.get("starting_feats", []):
        feats_list.append(f)
        
    # 4. Weapons & Equipment Loadout
    class_def_weapons = CLASS_WEAPONS.get(class_key, CLASS_WEAPONS["pathless"])
    main_hand_w = (starting_weapons.get("main_hand") if starting_weapons else None) or class_def_weapons["main_hand"]
    off_hand_w = (starting_weapons.get("off_hand") if starting_weapons else None) or class_def_weapons["off_hand"]
    
    # 5. Personal Relic (Preset or Custom)
    if relic_key == "custom" and custom_relic_data:
        relic = custom_relic_data
        if "custom_ability" in custom_relic_data:
            feats_list.append(f"Keepsake Resonator: {custom_relic_data['custom_ability']}")
    else:
        relic = PERSONAL_RELICS.get(relic_key, PERSONAL_RELICS["smartphone"])
        if "mechanics" in relic:
            feats_list.append(f"Relic Attunement ({relic['name']}): {relic['mechanics']}")
    
    import backend.mechanics as mechanics
    mh_details = mechanics.get_item_details(main_hand_w)
    water_details = mechanics.get_item_details("Bottled Water")
    ration_details = mechanics.get_item_details("Survival Rations")
    relic_enriched = mechanics.enrich_item_dict(relic)

    starter_inventory = [
        relic_enriched,
        {
            "name": main_hand_w,
            "rarity": mh_details.get("rarity", "Common"),
            "durability": 45,
            "max_durability": 50,
            "qty": 1,
            "slot": "main_hand",
            "desc": mh_details["desc"],
            "visual_appearance": mh_details["visual_appearance"]
        },
        {
            "name": "Bottled Water",
            "rarity": "Common",
            "durability": 1,
            "max_durability": 1,
            "qty": 2,
            "slot": "consumable",
            "desc": water_details["desc"],
            "visual_appearance": water_details["visual_appearance"]
        },
        {
            "name": "Survival Rations",
            "rarity": "Common",
            "durability": 1,
            "max_durability": 1,
            "qty": 2,
            "slot": "consumable",
            "desc": ration_details["desc"],
            "visual_appearance": ration_details["visual_appearance"]
        }
    ]
    
    if off_hand_w and off_hand_w != "None":
        oh_details = mechanics.get_item_details(off_hand_w)
        starter_inventory.append({
            "name": off_hand_w,
            "rarity": oh_details.get("rarity", "Common"),
            "durability": 45,
            "max_durability": 50,
            "qty": 1,
            "slot": "off_hand",
            "desc": oh_details["desc"],
            "visual_appearance": oh_details["visual_appearance"]
        })
        
    # 6. Starting Equipped Slots
    equipped = {
        "head": "None",
        "chest": "Threadbare Scavenger Tunic",
        "main_hand": main_hand_w,
        "off_hand": off_hand_w,
        "accessory": relic["name"] if any(k in relic["name"] for k in ["Watch", "Tool", "Headphones", "Compass", "USB", "Rangefinder"]) else "None"
    }
    
    gear_durability = {
        "head": {"cur": 50, "max": 50},
        "chest": {"cur": 100, "max": 100},
        "main_hand": {"cur": 45, "max": 50},
        "off_hand": {"cur": 45, "max": 50} if off_hand_w != "None" else {"cur": 0, "max": 0},
        "accessory": {"cur": 100, "max": 100}
    }

    res_def = chosen_class.get("combat_resource", {
        "name": "Poise & Threat", "max": 100, "current": 0, "type": "poise"
    })
    combat_resource = dict(res_def)
    
    player_sheet = {
        "name": name if name and name.strip() else "Survivor",
        "level": 1,
        "xp": 0,
        "hp": max_hp,
        "max_hp": max_hp,
        "combat_resource": combat_resource,
        "free_attribute_points": 0,
        "col": 100,
        "race": race["name"],
        "class": chosen_class["title"],
        "favored_skills": list(chosen_class.get("favored_skills", [])),
        "native_armor": list(chosen_class.get("native_armor", [])),
        "stats": final_stats,
        "skills": skills_dict,
        "spells": [],
        "feats": feats_list,
        "racial_abilities": race["racial_abilities"],
        "inventory": starter_inventory,
        "equipped": equipped,
        "gear_durability": gear_durability,
        "quests": [],
        "location": "Sector 1 Safe-Zone: Washington Borough, NJ",
        "companions": {},
        "is_paused": False
    }
    
    return player_sheet


def build_system_initialization_welcome_message(player_state: dict) -> str:
    """
    Constructs the immersive V2 System Initialization welcome message.
    Blending:
    1. 'The System Apocalypse' (Tao Wong) as the Main Tone:
       Universal blue screen freezing human electronics, initializing baseline attributes,
       and declaring Earth an active monster-spawning zone where pre-integration technology
       fails unless mana-adapted, grounded in real-world geography (Route 31, Route 57,
       Oxford Furnace, Pohatcong Depths, Washington Borough, NJ 07882).
    2. Interactive System AI (Sardonic Architect Broadcast - Dungeon Crawler Carl + The Crucible):
       Cold planetary reclamation notice paired with a darkly witty, observant System AI / Architect
       voice that specifically evaluates the player's pre-integration vocation, keepsake relic,
       and calculates their chilling survival odds.
    3. Biometric & Relic Ledger:
       Dynamic readout of the calibrated Avatar, Vocation, Equipped Gear, Keepsake Relic, and
       a Dungeon Crawler Carl-style System evaluation note on their build.
    4. Tutorial (Initial Scenario #001 & In-Universe Cardinal Interface Briefing):
       Action input, Autonomous Companions (Ren), Ability Fusion (Rule 10), Graft Strain,
       and Voice Link onboarding replacing out-of-character tutorial bullets.
    """
    if not isinstance(player_state, dict):
        player_state = {}

    char_name = str(player_state.get("name") or "Survivor").strip()
    race = str(player_state.get("race") or "Pure Human").strip()
    class_doctrine = str(player_state.get("class") or "Pathless (Freeform)").strip()
    hp = player_state.get("hp", 100)
    max_hp = player_state.get("max_hp", 100)
    col = player_state.get("col", 100)
    stats = player_state.get("stats", {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10})

    # Derive AC
    import backend.mechanics as mechanics
    ac_info = mechanics.calculate_ac(player_state) if hasattr(mechanics, "calculate_ac") else {"ac": 12}
    ac_val = ac_info.get("ac", 12) if isinstance(ac_info, dict) else 12

    # Identify Pre-Integration Vocation / Skills
    skills_dict = player_state.get("skills", {})
    skill_lines = []
    vocation_title = "Civilian Survivor"

    if isinstance(skills_dict, dict) and skills_dict:
        for s_n, s_d in list(skills_dict.items())[:3]:
            m_val = s_d.get("mastery", 1) if isinstance(s_d, dict) else 1
            t_val = s_d.get("tier", "Novice") if isinstance(s_d, dict) else "Novice"
            skill_lines.append(f"  - `{s_n}`: Mastery {m_val}/1000 [{t_val}]")
    else:
        skill_lines.append("  - `Survival Conditioning`: Mastery 45/1000 [Novice]")
        skill_lines.append("  - `Tactical Reflexes`: Mastery 40/1000 [Novice]")

    skills_display = "\n".join(skill_lines)

    # Detect Vocation flavor from skills or background
    skills_keys_lower = " ".join(skills_dict.keys()).lower()
    feats_str_lower = " ".join(str(f) for f in player_state.get("feats", [])).lower()

    if any(k in skills_keys_lower for k in ["code", "software", "network", "system architecture"]):
        vocation_title = "Software Engineer / System Architect"
        arch_vocation_quip = (
            "Ah, a Software Engineer. The System observes: 'Fascinating. A specimen whose primary Earth survival skill "
            "involved converting cold brew into unhandled runtime exceptions. Unfortunately for you, the physical laws of New Jersey "
            "have just been hard-recompiled into arcane C++, and your mechanical keyboard has been swapped for cold iron. "
            "Try not to segfault when a troglodyte bites through your carpal tunnel.'"
        )
        survival_odds = 6.8
        survival_verdict = "Statistically tragic. Elevated slightly if you can debug enemy attack telegraphs."
    elif any(k in skills_keys_lower for k in ["triage", "medicine", "nursing", "trauma", "first aid"]):
        vocation_title = "Emergency Trauma Nurse / First Responder"
        arch_vocation_quip = (
            "A Trauma First Responder. The System observes: 'Someone who actually understands arterial bleeding and panic control. "
            "How refreshing. You will soon discover that staunching wounds caused by corrupted aether-beasts is remarkably similar to "
            "night-shift ER triage, except the patients have teeth on their ribs and the insurance billing is conducted in blood.'"
        )
        survival_odds = 16.4
        survival_verdict = "Remarkably high for an unaugmented mammalian bi-ped."
    elif any(k in skills_keys_lower for k in ["weld", "fabricat", "blacksmith", "machin", "metalwork"]):
        vocation_title = "Industrial Welder / Metal Fabricator"
        arch_vocation_quip = (
            "A Heavy Trades Metal Fabricator. The System observes: 'Calloused palms, arc-eye tolerance, and an appreciation for structural integrity. "
            "You might actually survive the afternoon. The Oxford mine shafts are rich in raw aether-iron, provided you don't mind "
            "mining around the hibernating slag-golems.'"
        )
        survival_odds = 14.1
        survival_verdict = "Promising blunt-force survivability."
    elif any(k in skills_keys_lower for k in ["timber", "forag", "homestead", "trapper", "bushcraft"]):
        vocation_title = "Off-Grid Homesteader / Wilderness Bushcrafter"
        arch_vocation_quip = (
            "An Off-Grid Homesteader. The System observes: 'You already hated the electrical grid and modern civilization. "
            "Rejoice: both have been obliterated! Now you just have to contend with the local timber wolves growing six extra sets of eyes.'"
        )
        survival_odds = 15.2
        survival_verdict = "Well-suited for environmental hostility."
    elif any(k in skills_keys_lower for k in ["barista", "espresso", "latte", "coffee"]):
        vocation_title = "Third-Wave Specialty Barista"
        arch_vocation_quip = (
            "A Specialty Barista. The System observes: 'You spent four years mastering dial-in ratios and oat milk microfoam. "
            "The bad news: the espresso machine at the Washington diner is now an enchanted conduit of pressurized magma. "
            "The good news: caffeine withdrawal will probably kill you before the goblins do.'"
        )
        survival_odds = 4.3
        survival_verdict = "Severe lack of bludgeoning potential."
    elif any(k in skills_keys_lower for k in ["athletics", "sprinter", "quarterback", "rugby", "martial"]):
        vocation_title = "Athletic Competitor / Martial Practitioner"
        arch_vocation_quip = (
            "An Earth Athlete. The System observes: 'Cardiovascular conditioning and fast-twitch kinetic reflexes. "
            "You are physically equipped to run away from danger very quickly, which is easily 80% of surviving your first week.'"
        )
        survival_odds = 12.9
        survival_verdict = "High kinetic agility index."
    else:
        vocation_title = "Adaptive Civilian Survivor"
        arch_vocation_quip = (
            f"An Adaptive Earth Civilian. The System observes: 'Biometric neural scan parsed. A versatile background characterized "
            f"by improvised problem solving and stubborn persistence. Let us see if that civilian tenacity holds when the mountain shudders.'"
        )
        survival_odds = 9.5
        survival_verdict = "Moderate. High variance based on tactical intelligence."

    # Identify Equipped Loadout
    equipped = player_state.get("equipped", {})
    main_hand = equipped.get("main_hand", "Bare Hands")
    off_hand = equipped.get("off_hand", "None")
    chest_armor = equipped.get("chest", "Threadbare Scavenger Tunic")

    # Detect Keepsake Relic
    relic_name = "Shattered Smartphone"
    relic_effect = "Chronicles the final unread text messages of Earth before cell towers calcified into humming mana-spires."
    arch_relic_quip = "A glass-and-aluminum brick with a cracked screen that will never connect to 5G again. At least you can use it as a blunt mirror to watch your own dismay."

    # Search inventory or accessory for relic
    inv = player_state.get("inventory", [])
    found_relic = None
    if isinstance(inv, list):
        for item in inv:
            if isinstance(item, dict):
                cat = str(item.get("category", "")).lower()
                i_name = str(item.get("name", ""))
                if "relic" in cat or any(w in i_name.lower() for w in [
                    "smartphone", "multi-tool", "lighter", "novel", "carabiner", "polaroid",
                    "flashlight", "tuning fork", "thermos", "santoku", "usb", "compass",
                    "stopwatch", "monocular", "walkie", "whistle", "keepsake"
                ]):
                    found_relic = item
                    break

    if found_relic:
        relic_name = found_relic.get("name", relic_name)
        relic_desc = found_relic.get("desc", "")
        relic_mech = found_relic.get("mechanics", "")
        relic_effect = f"{relic_desc} — *{relic_mech}*" if relic_mech else relic_desc
        r_low = relic_name.lower()

        if "smartphone" in r_low:
            arch_relic_quip = (
                "Keepsake Relic: Shattered Smartphone. System Note: 'A black-glass slab with a cracked screen that will never receive "
                "another push notification. Truly, an artifact of immense sentimental tragedy. At least you can use the dead screen to check if your eyes have started glowing blue.'"
            )
        elif "multi-tool" in r_low or "leatherman" in r_low:
            arch_relic_quip = (
                "Keepsake Relic: Titanium Multi-Tool. System Note: 'Nineteen precision tools, exactly zero of which are rated for parrying "
                "a ten-foot tectonic automaton. But hey, you can strip copper wiring and tighten screws while your teammate gets crushed.'"
            )
        elif "lighter" in r_low or "zippo" in r_low:
            arch_relic_quip = (
                "Keepsake Relic: Brass Windproof Lighter. System Note: 'Fire: humanity\\'s oldest and most pathetic security blanket. "
                "Keep that flint dry; down in the Pohatcong adits, the dark has teeth.'"
            )
        elif "thermos" in r_low or "coffee" in r_low:
            arch_relic_quip = (
                "Keepsake Relic: Vacuum Thermos. System Note: 'Three sips of pre-integration drip roast preserved by double-walled steel. "
                "Savor it like liquid gold. You are never tasting convenience store hazelnut again.'"
            )
        elif "novel" in r_low or "paperback" in r_low:
            arch_relic_quip = (
                "Keepsake Relic: Dog-Eared Paperback. System Note: 'Reading speculative fiction about the apocalypse while living inside "
                "one is either profound artistic irony or a cry for help. Either way, the pages make excellent tinder.'"
            )
        elif "flashlight" in r_low or "strobe" in r_low:
            arch_relic_quip = (
                "Keepsake Relic: Tactical Strobe Flashlight. System Note: 'Two thousand lumens of blinding LED white light. "
                "Terrific for disorienting subterranean cave stalkers. Less terrific when the battery dies in the middle of a pitch-black labyrinth adit.'"
            )
        elif "polaroid" in r_low or "camera" in r_low:
            arch_relic_quip = (
                "Keepsake Relic: Vintage Polaroid Camera. System Note: 'Three exposures left. Try not to waste one taking a selfie with the thing "
                "that eats you.'"
            )
        else:
            arch_relic_quip = (
                f"Keepsake Relic: {relic_name}. System Note: 'A physical anchor to an extinct civilization. "
                "Clutch it tightly when the seismic alarms sound.'"
            )

    return f"""# 🟦 [SYSTEM INITIALIZATION: PLANETARY INTEGRATION COMPLETE] 🟦
**SECTOR 01: NORTH AMERICAN CONTINENTAL ZONE // NODE 07882: WASHINGTON BOROUGH, NEW JERSEY**
*Ambient Aetheric Saturation: 94.7% (Lethal Threshold Exceeded)*
*Status: Pre-Integration Silicon Infrastructure Decommissioned // Organic Rewrites Enacted*

---

> **ATTENTION, RESIDENT OF NODE 07882:**
>
> If you are reading this floating cerulean display, congratulations: your biological matrix did not spontaneously liquefy during the initial mana rupture!
>
> At precisely 03:00 hours, the planetary free-trial period for Earth expired. The fundamental laws of physics you grew comfortable with—combustion engines, silicon microprocessors, and long-distance electrical grids along Route 31 and Route 57—have experienced an unrecoverable runtime termination. Internal combustion is dead. The cell towers on Pohatcong Mountain have calcified into humming mana-spires. The municipal parks, abandoned iron mines at Oxford Furnace, and drainage tributaries have been designated as leveled hostile breach zones and subterranean labyrinths.
>
> Washington Borough has been partitioned as the **Sector 1 Initial Calibration Sanctuary Wards**. Step beyond the warded perimeter, and you are officially registered as free-range harvest material for the indigenous and newly spawned megafauna.

---

### 📋 BIOMETRIC & RELIC LEDGER
- **Designation:** **{char_name}**
- **Genetic Lineage:** `{race}`
- **Combat Doctrine:** `{class_doctrine}`
- **Baseline Vitals:** `{hp}/{max_hp} HP` | **Armor Class:** `{ac_val}`
- **Pre-Integration Discipline:** `{vocation_title}`
- **Calibrated Skill Matrix (1–1000):**
{skills_display}
- **Equipped Tactical Loadout:**
  - *Main Hand:* `{main_hand}`
  - *Off Hand:* `{off_hand}`
  - *Chest Armor:* `{chest_armor}`
- **Soul-Bound Keepsake Relic:** `{relic_name}`
  - *Manifestation:* {relic_effect}

> 🎙️ **SYSTEM ARCHITECT EVALUATION:**
> *"{arch_vocation_quip}"*
> *"{arch_relic_quip}"*
> **Calculated Survival Index:** `{survival_odds}%` — *{survival_verdict}*

---

### 📜 INITIAL SCENARIO #001: SURVIVE THE FIRST CALIBRATION WAVE
- **Classification:** Regional Genesis Directive
- **Objective:** Establish situational awareness within the Washington Borough Safe-Zone, rendezvous with local survivors and key node operatives (Ren, Doc Mercer, Quartermaster Vane), and prepare for incoming environmental Aetheric surges.
- **Time Limit:** Continuous / Real-Time Progression
- **Clear Rewards:** +100 Col, 50 XP, Sector 1 Safe-Zone Clearance
- **Failure Condition:** Total Biological De-Registration (Permadeath)

---

### ⚙️ CARDINAL INTERFACE DIRECTIVES (TACTICAL ONBOARDING)
*The Cardinal System observes and enforces all interactions under absolute deterministic logic:*

1. **Tactical Commands & Narrative Manifestation:**
   Type your physical strikes, tactical repositioning, incantations, or speech into the command prompt. The Cardinal System calculates all weapon reach, Armor Class (AC), Saving Throws (DC), and kinetic impact damage behind the curtain.
2. **Autonomous Battle-Companions:**
   Companions like **Ren** are fully autonomous subagents with independent neural logic, tactical stances, and psychological thresholds. They react to enemy telegraphs, protect flanks, celebrate victories, or retreat when bloodied. Coordinate with them; they are living allies, not scripted minions.
3. **Cardinal Ability Fusion Chamber (Rule 10):**
   When your mastery reaches sufficient thresholds, you may merge two active skills into a superior **`[Fusion]` Skill** with combined mastery along the 1–1000 scale. Consumed base skills are archived and can be relearned from Novice (1/1000) whenever foundational retraining is needed.
4. **Bio-Surgical Grafting & Strain Tolerance:**
   Monsters and golems yield harvestable organs and kinetic servos. Doc Mercer's subterranean clinic can graft them to your anatomy, but heed your **Strain Capacity** (`CON Mod + Floor(Level / 2)`). Exceeding this threshold induces Necrotic Rejection and Arcane Dissonance.
5. **Neural Voice Link:**
   Toggle the **🎙️ Microphone Module** in the sidebar to stream vocal commands and dialogue directly into the Cardinal Matrix.

*The Crucible does not negotiate. Adapt, harvest the fallen, and climb.*
"""

