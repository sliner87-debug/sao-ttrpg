"""
Pre-to-Post Integration Character Generator Engine
Translates real-world Earth knowledge, vocations, and physical conditioning into LitRPG parameters.
Fully integrated with the 1-1000 Skill Mastery and Mechanics Engine.
Supports 18 Lifestyle Presets, 32 Vocations, 20 Lineages, 29+ Relics,
an interactive Custom Life Collaboration Parser, and Character-Folder Save Management.
"""

import json
import os
import time
import re
from backend.mechanics import (
    calculate_encumbrance,
    calculate_ac,
    CANONICAL_MILESTONES,
    reset_companion_roster_for_character,
    save_party_to_character_folder,
    restore_companions_for_character
)

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
    },

    # 12 Rare Previous Integration Vocations (With Special System Resonance)
    "speleologist_rescuer": {
        "title": "Sub-Surface Speleologist & Mine Rescue Operative",
        "description": "Navigated unmapped abyss stopes, unlined bedrock tunnels, hypoxic boreholes, and structural squeeze faults.",
        "stat_recommendations": {"CON": 3, "WIS": 2, "STR": 1, "DEX": 0, "INT": 0, "CHA": 0},
        "skills": {
            "Subterranean Spelunking": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Navigating vertical shafts, cave squeeze-ways, subterranean rappelling, and unmapped stopes.",
                "milestones_unlocked": [50]
            },
            "Mine-Gas Ventilation": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Detecting blackdamp, routing airflow currents, and surviving hypoxic sub-surface voids.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Lithic Echonavigation (Passive): Rapping a piton against bare bedrock reveals structural voids, hidden chambers, and ore stopes up to 100ft away; take 25% reduced cave-in damage."
    },
    "cryptographer_signals": {
        "title": "Clandestine Cryptographer / Number-Station Monitor",
        "description": "Monitored atmospheric shortwave frequencies, cold war one-time pads, and intercepted clandestine telemetric broadcasts.",
        "stat_recommendations": {"INT": 4, "WIS": 2, "STR": 0, "DEX": 0, "CON": 0, "CHA": 0},
        "skills": {
            "Algorithmic Decryption": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Decoding aether-cipher locks, logic wards, and intercepted Cardinal system telemetry.",
                "milestones_unlocked": [50]
            },
            "Signal Interception": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Tuning into ambient mana radio frequencies and detecting distant enemy transmissions.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Dead-Air Whisper (Passive): Receive an aetheric cipher alert 1 round before an elite enemy uses a named power or before an environmental hazard triggers."
    },
    "horologist_artisan": {
        "title": "Master Horologist & Chronometer Artisan",
        "description": "Crafted tourbillons, jeweled escapements, balance springs, and high-precision mechanical dead-beat clocks.",
        "stat_recommendations": {"DEX": 3, "INT": 2, "WIS": 1, "STR": 0, "CON": 0, "CHA": 0},
        "skills": {
            "Chrono-Mechanical Repair": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Assembling high-precision clockwork gears, tripwires, and mechanical timing assemblies.",
                "milestones_unlocked": [50]
            },
            "Escapement Calibration": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Tuning mechanical harmonic balance and microsecond kinetic release.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Temporal Pendulum (Passive): Once per combat encounter, rewind a failed physical attack, spellcast, or lockpicking attempt by 1 turn to re-roll with +2 advantage."
    },
    "mortician_conservator": {
        "title": "Forensic Mortician & Embalming Conservator",
        "description": "Practiced vascular embalming, reconstructive tissue restoration, and clinical post-mortem examination.",
        "stat_recommendations": {"WIS": 3, "INT": 2, "CON": 1, "STR": 0, "DEX": 0, "CHA": 0},
        "skills": {
            "Post-Mortem Anatomy": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Extracting intact organs, gland catalysts, and identifying lethal anatomical trauma.",
                "milestones_unlocked": [50]
            },
            "Thanato-Preservation": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Formulating preservative fluids to stabilize corpse decay and neutralize rot miasmas.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Rigor Mortis Read (Passive): Examining a fresh or ancient corpse reveals the exact weapon/spell that felled them, killer's level, and highest-tier loot drop with 100% accuracy."
    },
    "saturation_diver": {
        "title": "Deep-Sea Hyperbaric Saturation Diver",
        "description": "Lived in pressurized habitat capsules breathing heliox to weld pipelines in pitch-black ocean abysses.",
        "stat_recommendations": {"CON": 4, "STR": 2, "DEX": 0, "INT": 0, "WIS": 0, "CHA": 0},
        "skills": {
            "Hyperbaric Pressure-Mastery": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Enduring extreme hydrostatic psi, pressurized gas mixtures, and crushing depths.",
                "milestones_unlocked": [50]
            },
            "Abyssal Salvage": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Underwater cutting torches, subsea rigging, and zero-visibility tactile recovery.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Zero-Atmosphere Fortitude (Passive): Immune to water pressure crushing up to -3,000ft ASL, vacuum decompression, and drowning for up to 45 minutes without diving gear."
    },
    "paleo_botanist": {
        "title": "Paleo-Botanist & Seed Vault Conservator",
        "description": "Preserved cryo-stored heirloom seed banks, excavated fossilized flora, and analyzed prehistoric pollen cores.",
        "stat_recommendations": {"WIS": 3, "INT": 2, "CON": 1, "STR": 0, "DEX": 0, "CHA": 0},
        "skills": {
            "Paleo-Spore Cultivation": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Germinating extinct prehistoric plants and symbiotic fungal mycelia from past world cycles.",
                "milestones_unlocked": [50]
            },
            "Phytochemical Synthesis": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Distilling primordial floral resins, medicinal saps, and antimicrobial varnishes.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Spore-Ward Symbiosis (Passive): Inhaling plant spores, fungal neurotoxins, or floral pollens grants temporary HP (+10 Temp HP) instead of inflicting debuffs."
    },
    "beamline_physicist": {
        "title": "Particle Physicist & Synchrotron Beamline Operator",
        "description": "Engineered multi-GeV electron storage rings, superconducting magnets, and ultra-high vacuum RF cavities.",
        "stat_recommendations": {"INT": 4, "WIS": 1, "DEX": 1, "STR": 0, "CON": 0, "CHA": 0},
        "skills": {
            "Subatomic Flux Analysis": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Analyzing energetic wave-particle interference, leyline flux harmonics, and beam scattering.",
                "milestones_unlocked": [50]
            },
            "Kinetic Deflection Arrays": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Modulating electromagnetic and aetheric barrier fields to deflect directed energy.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Observation Collapse (Passive): Critical hits landed against this character are downgraded to normal hits; energy beam and elemental projectile attacks suffer 25% damage reduction."
    },
    "ordnance_demolitionist": {
        "title": "Master Pyrotechnician & Ordnance Demolitionist",
        "description": "Specialized in shaped charges, thermobaric charges, blasting cap delays, and military clearance.",
        "stat_recommendations": {"DEX": 3, "CON": 2, "INT": 1, "STR": 0, "WIS": 0, "CHA": 0},
        "skills": {
            "Shaped Charge Demolitions": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Channeling concussive explosive energy along directional cutting planes against hardened armor.",
                "milestones_unlocked": [50]
            },
            "Thermobaric Formulation": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Mixing aluminum powder, fuel-air oxidizers, and delayed incendiary ignition trains.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Zero-Backblast Vector (Passive): Explosives, grenades, and demolition charges deal +30% armor-piercing damage to structures/constructs and cannot damage allies."
    },
    "para_rescue_jumper": {
        "title": "High-Altitude Smokejumper & Para-Rescue Specialist",
        "description": "Conducted low-altitude round-canopy drops into burning canopies, high-angle rescue, and casualty evacuation.",
        "stat_recommendations": {"STR": 2, "DEX": 3, "CON": 1, "INT": 0, "WIS": 0, "CHA": 0},
        "skills": {
            "Freefall Vectoring": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "High-altitude glide control, turbulence compensation, and precision parachute landings.",
                "milestones_unlocked": [50]
            },
            "Wildland Rapid-Extraction": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Lifting immobilized casualties, chainsaw debris clearing, and rapid tactical egress.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Aero-Pneumatic Landing (Passive): Completely immune to fall damage; falling more than 30ft releases an outward kinetic shockwave that knocks back and stuns adjacent enemies."
    },
    "sonar_acoustician": {
        "title": "Acoustic Submarine Sonarman / Hydrophone Analyst",
        "description": "Trained ears to classify submerged diesel blades, biological clicks, thermocline echoes, and Doppler warbles.",
        "stat_recommendations": {"WIS": 3, "INT": 2, "DEX": 1, "STR": 0, "CON": 0, "CHA": 0},
        "skills": {
            "Passive Acoustic Detection": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Listening to micro-decibel mechanical clicks, breathing patterns, and gear rustles through barriers.",
                "milestones_unlocked": [50]
            },
            "Frequency Waveform Jamming": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Emitting acoustic white noise and resonance tones to scramble sonar and bats/blind predators.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Thermocline Hearing (Passive): Cannot be surprised; enemies within 60ft (even behind walls or invisible) have their exact locations, heartbeats, and weapons highlighted on HUD."
    },
    "grimoire_binder": {
        "title": "Antiquarian Grimoire Conservator & Occult Binder",
        "description": "Restored vellum folios, scraped palimpsests, bound illuminated manuscripts, and neutralized cursed parchment.",
        "stat_recommendations": {"INT": 3, "WIS": 3, "STR": 0, "DEX": 0, "CON": 0, "CHA": 0},
        "skills": {
            "Parchment Binding & Restoration": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Stitching leather covers, repairing torn vellum, and preserving magical runic ink from degradation.",
                "milestones_unlocked": [50]
            },
            "Occult Paleography": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Translating ancient dead alphabets, identifying demonic seals, and analyzing warding scripts.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Curse-Proof Vellum (Passive): Equipping or reading cursed tomes, scrolls, or inscribed artifacts never binds them maliciously to your soul and nullifies negative backlash."
    },
    "blast_furnace_metallurgist": {
        "title": "Heavy Industrial Blast-Furnace Metallurgist",
        "description": "Tended 3,000-degree molten iron stoves, tapped silica slag, and mastered steel microstructure transformations.",
        "stat_recommendations": {"STR": 3, "CON": 3, "INT": 0, "DEX": 0, "WIS": 0, "CHA": 0},
        "skills": {
            "Slag & Refractory Metallurgy": {
                "mastery": 55,
                "tier": "Apprentice",
                "description": "Evaluating refractory brick heat endurance, molten slag skimming, and alloy carbon content.",
                "milestones_unlocked": [50]
            },
            "Pyric Crucible Forging": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Working raw molten metal directly under supernatural fire and thermal forge conditions.",
                "milestones_unlocked": []
            }
        },
        "innate_perk": "Molten Hearth Stance (Passive): Immune to heat exhaustion and magma burns; whenever struck by fire damage, your melee weapon superheats for +1d6 fire damage on next strike."
    }
}

EARTH_VOCATIONS = PRESET_BACKGROUNDS

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
    },

    # --- D&D 3.5e / 5E, PATHFINDER 1E / 2E & MAJOR FANTASY SERIES LINEAGES ---
    "underdark_drow": {
        "name": "Underdark Drow (Obsidian Deep-Elf)",
        "genre": "D&D 3.5e / 5E",
        "desc": "Subterranean elven scions from the fluorescent UV-caverns of Sterling Hill and the Underdark rifts. Obsidian skin, stark white hair, and innate mastery of shadow and faerie-light magic.",
        "stat_mods": {"DEX": 3, "CHA": 2, "INT": 1, "STR": 0, "CON": -1, "WIS": 0},
        "racial_abilities": [
            "Drow High Magic (Faerie Fire & Darkness): Once per encounter, outline foes in violet luminescence (granting allies Advantage on attacks against them) or conjure a 15ft globe of impenetrable Underdark darkness.",
            "Superior Darkvision (120ft): Pierce complete subterranean darkness up to 120 feet and gain +2 on Perception checks in cavern or night environments.",
            "Spider-Venom Affinity: Weapon coatings and poison effects applied by you have their Save DC increased by +2.",
            "Flaw - Sunlight Sensitivity: Suffers a -1 penalty on attack rolls and visual Perception checks when fighting in direct, unfiltered midday sunlight."
        ]
    },
    "duergar_deep_dwarf": {
        "name": "Ashen Duergar (Gray Dwarf Mind-Forger)",
        "genre": "D&D 3.5e / 5E",
        "desc": "Grim, ash-skinned subterranean dwarves tempered by psionic enslavement and the 800-foot anthracite sumps of Pennsylvania. Masters of psionic size-shifting and relentless foundry labor.",
        "stat_mods": {"CON": 3, "STR": 2, "WIS": 1, "DEX": -1, "INT": 0, "CHA": -1},
        "racial_abilities": [
            "Psionic Enlarge (Giant-Might): Once per combat encounter as a bonus action, double in stature for 3 rounds, gaining +1d6 melee weapon damage, +2 AC from dense bone mass, and Advantage on Strength checks.",
            "Invisibility Shroud: Vanish from sight for 1 round or until you attack, allowing an automatic Ambush strike (+4 to hit).",
            "Duergar Mind-Fortress: Advantage on all saving throws against illusions, psionic mind-blasts, charm, and paralysis."
        ]
    },
    "svirfneblin_deep_gnome": {
        "name": "Svirfneblin (Deep Gnome Gem-Delver)",
        "genre": "D&D 3.5e / 5E",
        "desc": "Wiry, slate-skinned subterranean gnomes native to the crystalline zinc and skarn labyrinths. Unmatched at blending into living rock and deflecting arcane scrying.",
        "stat_mods": {"DEX": 3, "INT": 2, "WIS": 1, "STR": -1, "CON": 0, "CHA": 0},
        "racial_abilities": [
            "Stone Camouflage: Gain a +5 bonus to Stealth checks when hiding among rocky terrain, concrete ruins, or subterranean caverns.",
            "Gnome Cunning: Gain Advantage on all Intelligence, Wisdom, and Charisma saving throws against magic and system hexes.",
            "Nondetection Ward: Naturally shielded from divination, scrying sensors, and automated turret target-locks."
        ]
    },
    "halfling_shireborn": {
        "name": "Lightfoot Halfling (Shire-Born Wanderer)",
        "genre": "D&D 3.5e / 5E & Tolkien",
        "desc": "Small-statured, unshakably cheerful survivors with uncanny fate-bending luck, silent footfalls, and a refusal to bow to apocalyptic despair.",
        "stat_mods": {"DEX": 3, "CHA": 2, "WIS": 1, "STR": -2, "CON": 1, "INT": 0},
        "racial_abilities": [
            "Halfling Luck: Whenever you roll a natural 1 on an attack roll, ability check, or saving throw, you automatically reroll the die and take the new result.",
            "Brave Heart of the Shire: Gain Advantage on saving throws against being Frightened, terrified, or morale-broken by boss auras.",
            "Nimble Underfoot: You can move freely through the space of any creature that is Medium or larger without provoking opportunity attacks."
        ]
    },
    "rock_gnome_tinker": {
        "name": "Clockwork Tinker Gnome (Golarion / Lantan)",
        "genre": "D&D 5E & Pathfinder 2E",
        "desc": "Eccentric, vibrant-haired inventors obsessed with aetheric clockwork, alchemical fuses, and resonant crystal matrices.",
        "stat_mods": {"INT": 3, "DEX": 2, "CON": 1, "STR": -2, "WIS": 0, "CHA": 1},
        "racial_abilities": [
            "Master Tinker's Intuition: Gain a +3 bonus on all Field Smithing, Magi-Tech Hacking, and clockwork trap disarm checks.",
            "Gnome Cunning: Advantage on Intelligence, Wisdom, and Charisma saving throws against arcane and psionic spells.",
            "Vivacious First-World Surge: Once per rest, channel Fey-world vitality to recover 15 Combat Resource or 10 HP as a bonus action."
        ]
    },
    "goliath_cragborn": {
        "name": "Goliath Crag-Walker (Half-Giant)",
        "genre": "D&D 3.5e / 5E",
        "desc": "Eight-foot-tall lithic nomads with granite-mottled skin and natural bony dermal ridges, descending from the Catskill High Peaks and Kittatinny Ridge.",
        "stat_mods": {"STR": 4, "CON": 3, "WIS": 0, "DEX": -1, "INT": -1, "CHA": 0},
        "racial_abilities": [
            "Stone's Endurance: Once per encounter as a reaction when taking damage, roll 1d12 + CON modifier and reduce the incoming damage by that total.",
            "Powerful Build (Titan Frame): Count as one size larger for carrying capacity (+60 lbs max encumbrance) and for grappling or shoving large monsters.",
            "Mountain Born: Naturally acclimated to high altitude and immune to extreme cold weather penalties (+25% Cold damage resistance)."
        ]
    },
    "firbolg_forest_keeper": {
        "name": "Firbolg Primeval Warden",
        "genre": "D&D 5E",
        "desc": "Gentle, towering fey-blooded forest guardians with furry ears and deep earthy voices who guard the ancient hemlock gorges of Ricketts Glen and the Pine Barrens.",
        "stat_mods": {"WIS": 3, "STR": 2, "CON": 1, "DEX": -1, "INT": 0, "CHA": 0},
        "racial_abilities": [
            "Hidden Step: Once per encounter as a bonus action, turn magically invisible until the start of your next turn or until you make an attack.",
            "Primeval Disguise & Detect: Passively sense active leyline magic within 30 feet and alter your appearance to blend in with humans or elves.",
            "Speech of Beast and Leaf: Communicate directly with woodland beasts and flora to gather scouting intelligence or calm hostile animals."
        ]
    },
    "tabaxi_catfolk": {
        "name": "Tabaxi / Amurrun (Felid Stalker)",
        "genre": "D&D 5E / Pathfinder 2E / Elder Scrolls",
        "desc": "Sleek, leopard- and lynx-furred feline humanoids gifted with explosive sprint bursts, retractable climbing claws, and insatiable curiosity for ancient relics.",
        "stat_mods": {"DEX": 4, "CHA": 2, "WIS": 0, "STR": 0, "CON": -1, "INT": 0},
        "racial_abilities": [
            "Feline Agility: Double your movement speed for 1 full round during combat, allowing instant flanking or disengage maneuvers.",
            "Cat's Claws & Pounce: Climb sheer surfaces at full speed and deliver 1d6 + DEX slashing claw strikes in close quarters.",
            "Cat's Talent (Night-Eye): Low-light vision and a permanent +2 bonus to Perception and Stealth checks."
        ]
    },
    "kenku_tengu": {
        "name": "Tengu / Kenku (Storm-Crow & Jinx-Eater)",
        "genre": "D&D 5E & Pathfinder 1E / 2E",
        "desc": "Raven-feathered corvid swordmasters and scouts nesting along the Kittatinny raptor ridges and ruined cathedral spires. Masters of swordplay and storm-omens.",
        "stat_mods": {"DEX": 3, "WIS": 2, "INT": 1, "STR": -1, "CON": 0, "CHA": 0},
        "racial_abilities": [
            "Jinx-Eater (Curse Swallow): Once per rest, devour a hostile hex, curse, or bad-luck effect targeting you or an ally, converting it into +2 on your next attack roll.",
            "Tengu Sword-Trained: Innately proficient with all katana, daggers, and finessee blades (+1 crit threat range with bladed weapons).",
            "Squall-Wing Glide & Mimicry: Perfectly replicate any voice or sound heard, and use feathered mantle-arms toarrest falls and leap +15 feet horizontally."
        ]
    },
    "kitsune_nine_tails": {
        "name": "Kitsune (Nine-Tailed Starlight Fox)",
        "genre": "Pathfinder 1E & 2E",
        "desc": "Shapeshifting vulpine mystics who weave star-fire illusions and shift seamlessly between human, hybrid fox-ear vanguard, and swift woodland fox forms.",
        "stat_mods": {"CHA": 3, "DEX": 2, "INT": 1, "STR": -1, "CON": 0, "WIS": 0},
        "racial_abilities": [
            "Foxfire Tail-Bolt: Project cold-burning blue foxfire from your tails as a ranged spell attack (60ft) dealing 1d8 radiant/electric damage without consuming mana.",
            "Change Shape (Vulpine Guile): Shift freely between Human guise, Hybrid Kitsune form, and a swift Pest/Scout Fox form (+4 Stealth and Deception).",
            "Star-Orb Resonance: Enchantment, illusion, and spirit spells you cast gain +1 to their Save DC."
        ]
    },
    "leshy_botanical_spirit": {
        "name": "Leshy (Immortal Nature Spirit-Vessel)",
        "genre": "Pathfinder 2E",
        "desc": "Immortal primal nature spirits housed inside small, hand-woven bodies of living gourd, crimson autumn leaf, pine-cone, or bioluminescent cavern fungus.",
        "stat_mods": {"WIS": 3, "CON": 2, "DEX": 1, "STR": -1, "INT": 0, "CHA": 0},
        "racial_abilities": [
            "Seedpod / Spore Strike: Launch pressurized iron-hard seedpods or glowing fungal spores up to 30ft dealing 1d6 bludgeoning/poison damage and slowing targets on crits.",
            "Photosynthetic Sustenance: Draw nourishment directly from sunlight, ambient mana, and clean water; immune to starvation and biological rot.",
            "Verdant Burst: If reduced to 0 HP, release a wave of restorative pollen that heals all allies within 15ft for 2d6 HP while stabilizing your root-core."
        ]
    },
    "githyanki_astral_raider": {
        "name": "Githyanki (Astral Silver-Blade Warrior)",
        "genre": "D&D 3.5e / 5E",
        "desc": "Gaunt, amber-skinned astral raiders who breached the Overlay while hunting Mind Flayer nautiloids around the Brookhaven and Princeton particle accelerators.",
        "stat_mods": {"STR": 2, "INT": 2, "DEX": 2, "CON": 0, "WIS": 0, "CHA": -1},
        "racial_abilities": [
            "Astral Misty Step: Once per encounter, psionically teleport up to 30 feet to an unoccupied space you can see as a bonus action.",
            "Silver-Sword Psionics: Channel telekinetic force through melee weapons, adding +1d4 psychic damage on hits and ignoring ethereal/phase defenses.",
            "Decadent Astral Memory: Instantly recall planar lore and gain a +2 bonus to Arcana and History checks."
        ]
    },
    "githzerai_limbo_monk": {
        "name": "Githzerai (Zerth Cenobite of Limbo)",
        "genre": "D&D 3.5e / 5E",
        "desc": "Ascetic psionic philosopher-monks who shape chaotic rift-matter through sheer iron discipline, turning their minds into impenetrable bastions.",
        "stat_mods": {"WIS": 3, "DEX": 2, "INT": 1, "STR": 0, "CON": 0, "CHA": -1},
        "racial_abilities": [
            "Inertial Psionic Shield: Passively project a mental force-field granting +2 AC when wearing light or no armor, and cast Shield (+4 AC reaction) once per encounter.",
            "Zerth Mental Discipline: Advantage on saving throws against Charmed, Frightened, Stunned, and psionic domination effects.",
            "Limbo Chaos-Anchor: Ignore difficult terrain caused by rubble, gravity anomalies, or spatial glitches."
        ]
    },
    "tortle_shellback": {
        "name": "Tortle / Kappa (Razorback Shell-Guard)",
        "genre": "D&D 5E & Folklore",
        "desc": "Heavy-shelled chelonian guardians from the Delaware and Raritan river basins, carrying an enchanted snapping-turtle carapace thicker than forged steel.",
        "stat_mods": {"STR": 3, "CON": 3, "WIS": 1, "DEX": -2, "INT": 0, "CHA": 0},
        "racial_abilities": [
            "Natural Carapace Armor: Your heavy dorsal shell provides a minimum Base Armor Class of 17 (plus shield bonuses) without needing to wear chest armor.",
            "Shell Defense Posture: Withdraw into your shell as an action to gain +4 bonus AC and Advantage on STR and CON saves until your next turn.",
            "River-Bottom Breath & Claws: Hold breath underwater for 1 full hour and strike with 1d6 + STR snapping claws."
        ]
    },
    "aarakocra_owlin": {
        "name": "Aarakocra / Strix (Raptor-Born Sky-Scout)",
        "genre": "D&D 5E & Pathfinder 2E",
        "desc": "Winged avian vanguards with red-tailed hawk or great horned owl plumage who patrol the thermal updrafts of the Delaware Water Gap and Hawk Mountain.",
        "stat_mods": {"DEX": 3, "WIS": 2, "CHA": 0, "STR": 0, "CON": -1, "INT": 1},
        "racial_abilities": [
            "Thermal Raptor Flight: Soar and hover up to 30 feet per round when wearing light or medium armor, bypassing ground pits and tripwires.",
            "Stooping Dive-Talon: When attacking from higher elevation or after flying 20ft toward a foe, deal +1d6 bonus piercing damage.",
            "Nocturnal Raptor Sight: Darkvision (90ft) and Advantage on visual Perception checks from high ground."
        ]
    },
    "yuan_ti_vishkanya": {
        "name": "Yuan-Ti / Vishkanya (Serpent-Blooded)",
        "genre": "D&D 3.5e / 5E & Pathfinder 1E / 2E",
        "desc": "Graceful, golden-eyed humanoids carrying ancient ophidian bloodlines, patches of diamondback scales, forked tongues, and venoms coursing through their veins.",
        "stat_mods": {"INT": 2, "CHA": 2, "DEX": 2, "STR": -1, "CON": 0, "WIS": 0},
        "racial_abilities": [
            "Ophidian Magic Resistance: Gain Advantage on saving throws against all hostile spells and magical effects.",
            "Envenomed Blood (Toxic Coating): As a free action once per encounter, coat your weapon or ammunition in your own neurotoxic blood (+1d6 poison damage & Poisoned condition on hit).",
            "Serpent Immunity: Complete immunity to poison damage and the Poisoned status condition."
        ]
    },
    "witcher_mutant_hound": {
        "name": "Trial-Mutated Monster Slayer (Vatt'ghern)",
        "genre": "The Witcher Series",
        "desc": "Survivors subjected to the Cardinal System's brutal mutagenic Trial of the Grasses—cat-slit amber eyes, slowed heart-rate, heightened alchemy tolerance, and quick-cast combat Signs.",
        "stat_mods": {"DEX": 2, "STR": 2, "CON": 2, "WIS": 1, "INT": 0, "CHA": -2},
        "racial_abilities": [
            "Quick-Sign Weaving (Igni / Quen / Aard): Once per encounter as a bonus action, unleash a Quick Sign—either a protective Quen Shield (absorbs 15 damage), an Igni Fire-Spray (2d6 fire cone), or an Aard Kinetic Blast (knocks foes prone).",
            "Trial of the Grasses Metabolism: Increases maximum Golem/Bio-Graft Strain capacity by +20 and doubles the duration and healing potency of alchemical potions and rations.",
            "Cat-Eye Medallion Sense: Darkvision (90ft), immunity to blinding flashes, and automatic vibration detection of hidden monsters, illusions, or curses within 60ft."
        ]
    },
    "viera_miqote_beastkin": {
        "name": "Viera / Cait Sith Wood-Warden (Eorzean / ALO)",
        "genre": "Final Fantasy & SAO Alfheim",
        "desc": "Lithe, long-eared woodland wardens and agile beast-kin rangers attuned to the Whisper of the Wood, capable of bounding across treetops and sniping with pinpoint grace.",
        "stat_mods": {"DEX": 3, "WIS": 2, "CHA": 1, "STR": -1, "CON": 0, "INT": 0},
        "racial_abilities": [
            "Whisper of the Wood (Ultrasonic Hearing): Cannot be surprised in combat; grants a permanent +3 bonus to Initiative and Perception checks.",
            "Lapine Sky-Vault: Standing high jump and long jump distances are tripled (+15ft vertical leap), ignoring ground-level brambles and difficult terrain.",
            "White-Draws Precision: Ranged bow, crossbow, and carbine attacks ignore half-cover and deal +2 bonus damage on the first round of combat."
        ]
    },
    "dunmer_ashlander": {
        "name": "Ashen Dunmer / Eldar Star-Weaver",
        "genre": "Elder Scrolls & Tolkien High-Fantasy",
        "desc": "Ash-complexioned, crimson-eyed elven battle-mages forged in volcanic badlands and Centralia's ash-winds, blending dual-blade swordplay with destructive fire sorcery.",
        "stat_mods": {"INT": 2, "DEX": 2, "WIS": 1, "CHA": 1, "STR": 0, "CON": -1},
        "racial_abilities": [
            "Ancestor's Wrath (Flame Cloak): Once per encounter, wreathe yourself in a swirling mantle of ancestral fire for 3 rounds—granting +2 AC and dealing 1d6 fire damage to any enemy that strikes you in melee.",
            "Ash-Born Fire Resistance: Passive 50% damage reduction against Fire, magma, and volcanic ash hazards.",
            "Spellsword Harmony: Wielding a one-handed blade in your main hand and a spell in your off-hand grants +1 to both melee hit rolls and spell save DCs."
        ]
    },
    "skaven_ratfolk_ysoki": {
        "name": "Ysoki / Skaven Warp-Tinker (Under-Empire Ratfolk)",
        "genre": "Pathfinder 1E/2E & Warhammer Fantasy",
        "desc": "Hyper-intelligent, twitchy rodent-kin engineers and tunnel-runners from the NYC Subway Undercity and Morris Canal culverts, hoarding glowing warp-aether capacitors.",
        "stat_mods": {"DEX": 3, "INT": 3, "WIS": 0, "STR": -2, "CON": 1, "CHA": -1},
        "racial_abilities": [
            "Warp-Spark Overcharge: Supercharge any ranged weapon, wand, or gadget with volatile green warp-mana to deal +2d6 bonus lightning/acid damage (once per encounter).",
            "Swarming Underfoot & Cheek Pouches: Can occupy the same tile as an ally to automatically grant Flanking (+2 to hit), and rapidly draw/consume potions or grenades as a free action.",
            "Tunnel-Scavenger Nose: Scent-based detection of traps, black-powder, and hidden ore caches within 30 feet (+3 to Salvage and Trap checks)."
        ]
    },
    "dhampir_bloodborne": {
        "name": "Dhampir / Strigoi Scion (Night-Blooded)",
        "genre": "D&D 5E / Pathfinder 2E / Witcher",
        "desc": "Half-living scions of Higher Vampires who walk the twilight border between life and undeath—pale, fang-toothed predators with supernatural speed and sanguine regeneration.",
        "stat_mods": {"DEX": 2, "CHA": 2, "CON": 2, "STR": 1, "INT": 0, "WIS": -1},
        "racial_abilities": [
            "Sanguine Bite & Drain: Deliver a 1d6 + CON piercing fang attack in melee; once per encounter, empower the bite to heal yourself for 100% of the damage dealt.",
            "Vampiric Spider-Climb: Walk effortlessly across vertical stone walls and cavern ceilings at full movement speed while keeping both hands free.",
            "Deathless Vigour: Do not need to breathe (immune to drowning and suffocation gases) and gain 50% resistance to necrotic damage."
        ]
    },
    "conrasu_aeon_shard": {
        "name": "Conrasu / Modron (Cosmic Aeon-Shard)",
        "genre": "Pathfinder 2E & D&D Planescape",
        "desc": "A shard of pure cosmic Law and Pleroma Aeon consciousness housed inside a geometric orb of dark iron, surrounded by an articulated exoskeleton of living wood and brass gears.",
        "stat_mods": {"WIS": 3, "CON": 2, "INT": 2, "STR": 0, "DEX": -1, "CHA": -1},
        "racial_abilities": [
            "Call to Axis (Cosmic Equilibrium): Once per encounter, replace any d20 roll you just made with an automatic mathematical '12' before modifiers, enforcing absolute law over chaos.",
            "Sunlight & Leyline Mend: Meditate for 10 minutes in sunlight or near a leyline node to restore 2d8 + Level HP to your wooden/brass frame.",
            "Exoskeletal Carapace: Natural +2 Armor Class and complete immunity to polymorph, petrification, and reality-glitch distortion."
        ]
    },
    "anadi_weaver": {
        "name": "Anadi / Arachne (Star-Silk Shapechanger)",
        "genre": "Pathfinder 2E & Dark Fantasy",
        "desc": "Scholarly, peace-loving recluses and deadly ambush weavers capable of shifting between an ornate humanoid scholar and a giant iridescent star-silk spider.",
        "stat_mods": {"DEX": 3, "INT": 2, "WIS": 1, "STR": 0, "CON": 0, "CHA": -1},
        "racial_abilities": [
            "Star-Silk Tether & Web-Snare: Fire a 30ft high-tensile silk line to pull yourself to high ground or restrain a target (DC 14 STR to break).",
            "Hybrid Arachnid Stance: Shift between humanoid form (able to wield weapons normally) and eight-legged spider form (+10ft speed, climb walls, and 1d6 + 1d4 poison fang bite).",
            "Vibration Web-Sense: Sense the exact coordinates of any creature touching the ground or walls within 30 feet."
        ]
    },
    "hobgoblin_legionnaire": {
        "name": "Hobgoblin Iron-Legionnaire",
        "genre": "D&D 3.5e / 5E & Pathfinder 2E",
        "desc": "Disciplined, orange-and-crimson-skinned martial tacticians organized into phalanx centuries around fortified highway redoubts and arsenal depots.",
        "stat_mods": {"CON": 3, "STR": 2, "INT": 2, "DEX": 0, "WIS": 0, "CHA": -1},
        "racial_abilities": [
            "Martial Advantage (Phalanx Strike): Once per turn, deal an extra 2d6 weapon damage when you hit a creature that is within 5 feet of one of your conscious allies.",
            "Saving Face (Iron Discipline): If you miss an attack roll or fail a saving throw, add a bonus equal to the number of allies within 30ft (up to +3).",
            "Legionnaire Armor Drill: Ignore movement speed penalties from heavy armor and gain +1 AC when fighting alongside at least one companion."
        ]
    },
    "kobold_trapwright": {
        "name": "Kobold Dragon-Wrought Trapwright",
        "genre": "D&D 3.5e / 5E & Pathfinder 2E",
        "desc": "Small, horned reptilian tunnel-delvers with draconic crest-scales who worship ancient wyrms and turn narrow mine adits into lethal gauntlets of spring-loaded snares.",
        "stat_mods": {"DEX": 4, "INT": 2, "CHA": 1, "STR": -2, "CON": 0, "WIS": 0},
        "racial_abilities": [
            "Pack Tactics: Gain a +2 bonus (and Advantage on critical confirmation) on attack rolls against a target if at least one of your allies is within 5 feet of the target.",
            "Dragon-Wrought Trapmaster: Field traps, tripwires, and alchemical bombs you deploy deal +1d6 bonus damage and have +3 added to their Save DC.",
            "Draconic Cry: Unleash a startling yip-roar as a bonus action once per encounter, granting all party members Advantage on attacks until your next turn."
        ]
    },

    # --- D&D & PATHFINDER MONSTROUS PLAYABLE RACES ---
    "troll_fleshwarped": {
        "name": "Troll (Flesh-Warped Regeneration Juggernaut)",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Hulking brute with moss-green rubbery hide, elongated limbs, and ferocious predatory appetite. Legendary for rapid cellular re-knitting that closes mortal wounds in seconds.",
        "stat_mods": {"STR": 4, "CON": 4, "WIS": -1, "INT": -2, "CHA": -2, "DEX": 0},
        "racial_abilities": [
            "Rapid Cellular Regeneration: Passively regenerates 5 HP at the start of each of your turns in combat, unless you took Fire or Acid damage since your last turn.",
            "Rending Talons: Unarmed strikes deal 1d8 + STR slashing damage. If you hit a target with two claw attacks on the same turn, rend for +2d6 bonus tearing damage.",
            "Keen Scent: Gain Advantage on Wisdom (Perception) checks that rely on smell and track wounded targets automatically within 100 feet.",
            "Flaw - Voracious Hunger & Fire Vulnerability: Takes 50% extra damage from Fire and Acid attacks; requires consuming double daily food rations to sustain hyper-regeneration."
        ]
    },
    "illithid_mind_flayer": {
        "name": "Illithid / Ceremorph (Renegade Mind Flayer)",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Renegade cephalopod aberration liberated from Elder Brain hive-networks when ambient rift aether severed the collective synaptic tether. Purplish-slate rubbery flesh, four writhing facial tentacles, and terrifying psionic brain-wave mastery.",
        "stat_mods": {"INT": 4, "WIS": 2, "CHA": 1, "STR": -2, "CON": 0, "DEX": 0},
        "racial_abilities": [
            "Psionic Mind Blast: Unleash a 20ft frontal cone of psychic pressure dealing 2d8 + INT psychic damage; targets must pass an INT saving throw or be Stunned for 1 round (once per rest).",
            "Tentacle Grapple & Neural Siphon: Attack with facial tentacles dealing 1d6 + INT psychic damage; on hit, grapple the target and drain 10 HP / 10 Combat Resource from incapacitated foes.",
            "Telepathic Net & Aberrant Senses: Communicate telepathically up to 120 feet with any sentient mind, and passively sense the exact location of any thinking creature within 60 feet.",
            "Flaw - Neural Siphon Dependency: Must consume intellectual psychic essence or neural tissue once per week or suffer progressive psychic exhaustion."
        ]
    },
    "mountain_orc_blood": {
        "name": "Mountain Orc (Gruumsh War-Born)",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Towering gray-green warrior bred in blood-stained war bands, carrying scarred tusk canines, bone piercings, and ancestral fury that surges into an unstoppable melee rush.",
        "stat_mods": {"STR": 4, "CON": 3, "DEX": 0, "WIS": 0, "INT": -2, "CHA": -1},
        "racial_abilities": [
            "Aggressive Rush: As a bonus action on your turn, move up to your full movement speed toward a hostile creature you can see.",
            "Relentless Juggernaut: When reduced to 0 HP, drop to 1 HP instead and immediately gain +10 temporary HP and +2 to melee damage for 1 round (once per long rest).",
            "Primal Intimidation: Add double your Strength modifier to Intimidation checks against non-construct creatures."
        ]
    },
    "goblin_pyromaniac": {
        "name": "Goblin Sapper / Pyromaniac (Kek-Clan Sneak)",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Pointy-eared, yellow-eyed cackling green menace with needle teeth, sharp claws, and a maniacal obsession with explosive alchemy, singing fire, and dirty fighting.",
        "stat_mods": {"DEX": 4, "CON": 1, "INT": 1, "STR": -2, "WIS": -1, "CHA": 0},
        "racial_abilities": [
            "Nimble Escape: You can take the Disengage or Hide action as a bonus action on each of your combat turns.",
            "Fury of the Small: When you damage a creature with an attack that is of a larger size than you, deal extra damage equal to your character level (once per encounter).",
            "Volatile Fire-Tinker: Improvised incendiary vials, molotovs, and bombs you toss gain +1d6 fire damage and ignite flammable cover."
        ]
    },
    "kobold_dragon_herald": {
        "name": "Kobold Wyrm-Herald (Dragon-Speaker)",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Scaled, canine-snouted miniature draconic survivor bearing glowing red eye-slits, a sweeping tail, and ancestral dragon-blood that hums with raw elemental power.",
        "stat_mods": {"DEX": 3, "CHA": 3, "CON": 0, "STR": -2, "INT": 1, "WIS": 0},
        "racial_abilities": [
            "Draconic Roar & Grovel: Unleash an alarming draconic screech or distracting feint as a bonus action, granting allies Advantage on attack rolls against enemies within 10 feet.",
            "Pack Hunter Telemetry: When an ally is adjacent to your target, your attacks gain +2 to hit and your critical strike range is expanded by 1 (e.g. 19-20).",
            "Dragon-Spark Cantrip: Innately cast a minor elemental bolt (Fire, Cold, or Acid) dealing 1d8 damage with 60ft range without using spell slots."
        ]
    },
    "bugbear_shadow_stalker": {
        "name": "Bugbear Shadow-Stalker (Apex Brute)",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Massive seven-foot furred goblinoid juggernaut with disproportionately long limbs, padded paws, and silent ambushing instincts that belie their massive size.",
        "stat_mods": {"STR": 3, "DEX": 2, "CON": 2, "WIS": 0, "INT": -1, "CHA": -1},
        "racial_abilities": [
            "Long-Limbed Reach: Your melee attacks have +5 feet of reach, allowing you to strike with two-handed axes and polearms from safe distances.",
            "Surprise Attack (Ambush Carnage): If you hit a creature on the first round of combat before they act, the attack deals an extra 2d6 weapon damage.",
            "Sneaky Titan: Gain proficiency in Stealth; can squeeze through narrow gaps meant for creatures of Small size despite your hulking build."
        ]
    },
    "gnoll_hyena_ravager": {
        "name": "Gnoll Hyena-Ravager (Fang of Yeenoghu)",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Feral, spotted-pelt hyena humanoid driven by ceaseless blood-hunger and terrifying cackling laughter, tearing through enemy battle-lines with bone-crushing jaws.",
        "stat_mods": {"STR": 3, "CON": 3, "DEX": 1, "INT": -2, "WIS": 0, "CHA": -1},
        "racial_abilities": [
            "Rampage: When you reduce a creature to 0 hit points with a melee attack on your turn, you can take a bonus action to move up to half your speed and make a bite attack.",
            "Crushing Jaws: Secondary bite attack dealing 1d6 + STR piercing damage in melee that inflicts the Bleeding status on hit.",
            "Cackling Terror: Once per encounter, emit an eerie hyena laugh that forces hostiles within 30ft to make a WIS save or suffer Disadvantage on attacks for 1 round."
        ]
    },
    "minotaur_labyrinth_breaker": {
        "name": "Minotaur Labyrinth-Breaker (Gore-Horn Juggernaut)",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Mighty bull-headed titan of corded muscle, cloven hooves, and sweeping bronze horns, possessing a supernatural mental compass that pierces any maze or dungeon.",
        "stat_mods": {"STR": 4, "CON": 3, "WIS": 1, "DEX": -1, "INT": -1, "CHA": -1},
        "racial_abilities": [
            "Goring Horn Charge: If you move at least 20 feet straight toward a target before hitting with a melee attack, gore with your horns for +2d6 piercing damage.",
            "Hammering Horns: Immediately after hitting with a melee attack on your turn, use a bonus action to shove the target up to 10 feet away or knock them Prone.",
            "Labyrinthine Memory: Perfect directional recall; immune to getting lost, can never be trapped in maze spells, and detect secret doors/passages with +3 Perception."
        ]
    },
    "half_ogre_crusher": {
        "name": "Ogrekin / Half-Ogre Earth-Crusher",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Nine-foot-tall primordial brute with skin thick as weathered granite, hands like iron shovels, and raw earth-splitting physical power that breaks stone fortifications.",
        "stat_mods": {"STR": 5, "CON": 4, "DEX": -2, "INT": -3, "WIS": 0, "CHA": -1},
        "racial_abilities": [
            "Colossal Swing: When attacking with two-handed heavy weapons, deal bludgeoning splash damage equal to your STR mod to all adjacent enemies.",
            "Rock Hurler: Pick up and throw large boulders, rubble, or metal scrap up to 60 feet dealing 2d8 + STR bludgeoning damage.",
            "Hulking Bulk: Carrying capacity and push/drag limits are doubled (+100 lbs unencumbered); natural Armor Class increased by +2.",
            "Flaw - Clumsy Giant: Suffers Disadvantage on delicate manual dexterity, lockpicking, and stealth checks."
        ]
    },
    "medusa_gorgon_scion": {
        "name": "Medusa / Gorgon Scion (Serpent-Gaze)",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Cursed, serpentine immortal whose hair is a writhing nest of venomous vipers and whose unblinking golden gaze can petrify living tissue into solid granite.",
        "stat_mods": {"CHA": 3, "DEX": 2, "CON": 1, "INT": 1, "STR": 0, "WIS": -1},
        "racial_abilities": [
            "Petrifying Gaze: Target a creature within 30 feet that can see your eyes; target must pass a CON saving throw or become Restrained as stone creeps across their limbs (DC 13 + CON mod).",
            "Serpent-Hair Bite: As a reaction when an enemy enters your melee reach, your viper locks strike for 1d4 piercing + 1d6 poison damage.",
            "Stone-Immunity & Darkvision: Complete immunity to petrification, paralysis, and poison; see in pitch darkness up to 90 feet."
        ]
    },
    "gargoyle_lithic_sentinel": {
        "name": "Gargoyle Lithic Wing-Sentinel",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Chiseled from ancient demonic granite, possessing bat-like stone wings, horned brows, and razor talons. Masters of architectural ambushes and roof-stalking.",
        "stat_mods": {"CON": 4, "STR": 3, "DEX": 0, "WIS": 1, "INT": -2, "CHA": -2},
        "racial_abilities": [
            "Stony Carapace: Resistance (25% damage reduction) against non-magical bludgeoning, piercing, and slashing attacks.",
            "Stone Wings (Glide & Hover): Fly and glide up to 30 feet per round, ignoring ground-level traps and difficult terrain.",
            "False Appearance (Statue Stance): While remaining motionless atop stone or building ledges, you are completely indistinguishable from an inanimate gothic statue."
        ]
    },
    "troglodyte_stench_stalker": {
        "name": "Troglodyte Cavern Stench-Stalker",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Reptilian Underdark carnivore covered in gray-green scales with a spiny dorsal ridge, exuding a pungent, sickening glandular musk that nauseates warm-blooded prey.",
        "stat_mods": {"CON": 4, "STR": 2, "DEX": 1, "INT": -2, "WIS": 0, "CHA": -3},
        "racial_abilities": [
            "Stench Musk Aura: Any non-troglodyte starting their turn within 5 feet of you must pass a CON save (DC 12 + CON mod) or become Poisoned until the start of their next turn.",
            "Chameleon Scales: Natural skin color shifts to match stone, gravel, and dirt, granting Advantage on Dexterity (Stealth) checks in subterranean areas.",
            "Claw-and-Bite Multiattack: Secondary bite attack in melee dealing 1d4 piercing + 1d4 acid damage."
        ]
    },
    "doppelganger_morph": {
        "name": "Doppelganger Flesh-Morph Infiltrator",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Faceless, slate-skinned psychic shapeshifter possessing uncanny empathy, surface-mind eavesdropping, and seamless physiological replication.",
        "stat_mods": {"CHA": 4, "DEX": 2, "INT": 2, "STR": 0, "CON": 0, "WIS": -1},
        "racial_abilities": [
            "Shapechanger Master: Magically polymorph into any Medium or Small humanoid you have seen, precisely replicating their facial features, voice, gait, and gear visual.",
            "Read Surface Thoughts: Sense surface thoughts and combat intentions within 60 feet, granting +2 on Insight, Deception, and AC against the read target.",
            "Ambusher Strike: When attacking a target that is unaware of your true nature, deal +3d6 bonus precision damage on the first hit."
        ]
    },
    "hag_born_caliban": {
        "name": "Hag-Born / Caliban Hex-Witch",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Offspring of ancient swamp and night hags—crooked posture, weeping willow bark skin, needle-iron nails, and inherited coven blood-curses.",
        "stat_mods": {"WIS": 3, "CHA": 2, "CON": 2, "STR": 1, "INT": 0, "DEX": -1},
        "racial_abilities": [
            "Coven Blood-Hex: Curse a creature within 60 feet as a bonus action; target suffers -2 to all saving throws and takes 1d6 necrotic damage whenever you hit them.",
            "Iron Claws & Nails: Unarmed strikes deal 1d6 + STR slashing damage and count as magical cold-iron weapons.",
            "Rot-Eater Fortitude: Immune to biological disease and gain +3 on saving throws against poison, rotting spores, and necrotic corruption."
        ]
    },
    "grung_tree_frog": {
        "name": "Grung Poison-Dipped Anuran",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Brightly-colored, three-foot-tall humanoid tree frog possessing adhesive suction pads, hyper-flexible joints, and glistening toxic dermal secretions.",
        "stat_mods": {"DEX": 4, "CON": 2, "WIS": 1, "STR": -2, "INT": 0, "CHA": 0},
        "racial_abilities": [
            "Poisonous Skin Secretions: Any creature that grapples you or strikes you with an unarmed attack must pass a CON save or be Poisoned for 1 minute; coat weapons in poison on contact (+1d4 poison damage).",
            "Standing Leap: Your high jump is up to 15 feet and your long jump is up to 25 feet without needing a running start.",
            "Adhesive Wall-Crawl: Climb smooth vertical surfaces and ceilings effortlessly without slipping."
        ]
    },
    "were_kin_shifter": {
        "name": "Shifter / Were-Kin (Lycanthrope-Born)",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Mortal carrier of dormant therianthropy, capable of calling upon their inner beast to sprout razor fangs, thick bristling fur, and predator senses.",
        "stat_mods": {"STR": 2, "DEX": 2, "CON": 2, "WIS": 1, "INT": -1, "CHA": -1},
        "racial_abilities": [
            "Feral Beast Shift: As a bonus action once per encounter, enter a shifted beast-aspect for 1 minute—gaining 10 temporary HP, +10ft movement speed, and 1d6 predatory bite/claw attacks.",
            "Apex Scent & Darkvision: Scent tracking up to 60 feet, Darkvision (60ft), and +2 to Survival and Perception checks.",
            "Predator Reflexes: Advantage on Dexterity saving throws against area-of-effect hazards and traps."
        ]
    },
    "centaur_plains_vanguard": {
        "name": "Centaur Plains-Vanguard (Equine Charger)",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Majestic fusion of human torso and mighty equine body, combining the heavy charging momentum of a warhorse with martial weapon mastery.",
        "stat_mods": {"STR": 4, "CON": 2, "WIS": 1, "DEX": 0, "INT": -1, "CHA": 0},
        "racial_abilities": [
            "Equine Charge: If you move at least 30 feet straight toward a target and hit with a melee attack, deal +2d6 bonus damage and make a bonus action Hooves attack.",
            "Hooves Strike: Unarmed melee strike with iron-shod hooves dealing 1d6 + STR bludgeoning damage.",
            "Galloping Overland Speed: Base movement speed is 40 feet (30% faster than standard humanoids); carrying capacity is doubled (+80 lbs).",
            "Flaw - Climb Impairment: Suffer double movement cost when attempting to climb sheer vertical ladders or ropes."
        ]
    },
    "thrikreen_mantis": {
        "name": "Thri-Kreen Desert Mantis (Four-Armed Wanderer)",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Four-armed arid insectoid with sandy chitin, compound antennae, clicking mandibles, and an alien hive-telepathy.",
        "stat_mods": {"DEX": 4, "WIS": 2, "CON": 1, "STR": 0, "INT": 0, "CHA": -2},
        "racial_abilities": [
            "Secondary Arms (Four-Armed Wielding): Possess two primary arms and two secondary arms; can dual-wield weapons while simultaneously holding a shield or loading a projectile weapon.",
            "Chameleon Carapace: Alter color to match sand, stone, and dirt, granting natural AC 15 + DEX mod (max 2) and Advantage on Stealth checks.",
            "Sleepless Alien Metabolism: Do not require sleep and cannot be put to sleep by magic; rest by remaining in a light meditative awareness for 4 hours."
        ]
    },
    "satyr_fey_reveler": {
        "name": "Satyr Fey-Horned Reveler",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Goat-legged woodland wanderer crowned with curling ram horns, possessing nimble cloven hooves, ancient panpipe melodies, and uncanny fey magic resistance.",
        "stat_mods": {"CHA": 3, "DEX": 2, "WIS": 1, "STR": 0, "CON": 0, "INT": -1},
        "racial_abilities": [
            "Magic Resistance (Fey Blessing): Gain Advantage on all saving throws against spells and magical hexes.",
            "Mirthful Ram-Horn Strike: Headbutt melee strike dealing 1d6 + STR bludgeoning damage; on hit after moving 20ft, knock foes prone.",
            "Panpipe Enchantment: Play an aetheric melody on pipes or flute once per encounter to Charm or Frighten targets within 30 feet (WIS save DC 13 + CHA mod)."
        ]
    },
    "sahuagin_blood_frenzy": {
        "name": "Sahuagin Blood-Frenzy Deep-Hunter",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Predatory piscine monstrosity from flooded sumps and subterranean rivers, possessing webbed talons, razor fins, needle shark teeth, and uncontrollable blood-frenzy.",
        "stat_mods": {"STR": 3, "CON": 2, "WIS": 2, "DEX": 1, "INT": -1, "CHA": -2},
        "racial_abilities": [
            "Blood Frenzy: Gain Advantage on melee attack rolls against any creature that does not have all its hit points.",
            "Shark-Kin Telepathy & Breath: Amphibious (breathe air and water equally) and communicate telepathically with aquatic beasts within 120 feet.",
            "Claw & Bite Multiattack: Deliver a 1d6 claw slash and 1d4 bite attack in rapid succession."
        ]
    },
    "grimlock_blindsight": {
        "name": "Grimlock Blind-Sight Under-Stalker",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Eyeless, gray-skinned subterranean humanoid whose vestigial eye-sockets are fused shut, possessing supernatural ultrasonic hearing and scent that pierces total darkness and invisibility.",
        "stat_mods": {"STR": 3, "CON": 3, "WIS": 2, "DEX": 0, "INT": -2, "CHA": -2},
        "racial_abilities": [
            "Blindsight (60ft): Perceive surroundings up to 60 feet via hearing and scent, completely ignoring total darkness, visual fog, and enemy invisibility.",
            "Blind Senses Immunity: Completely immune to being Blinded, visual illusions, gaze attacks (like Medusa's stare), and hypnotic patterns.",
            "Stone-Hugging Stealth: Gain a +4 bonus to Stealth checks in cavern, mine, or rubble terrain."
        ]
    },
    "rust_monster_kin": {
        "name": "Rust-Monster Touched / Metallivore",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Mutant scavenger bearing feathery rust-antennae, chitinous orange-brown carapace, and a chemical sweat that dissolves refined ores and steel on contact.",
        "stat_mods": {"CON": 3, "DEX": 2, "INT": 1, "STR": 0, "WIS": 1, "CHA": -2},
        "racial_abilities": [
            "Oxidizing Touch: Melee touch attack or strike that corrodes non-magical metal armor and weapons, reducing enemy AC by -2 or destroying weapons that hit you.",
            "Iron-Scent Telemetry: Passively sense the location and quantity of refined ferrous metals, weapons, and iron ore veins within 90 feet.",
            "Chitin Carapace: Natural +2 Armor Class; immune to rusting and acid corrosion hazards."
        ]
    },
    "derro_deep_savant": {
        "name": "Derro Maddened Deep-Savant",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Pale, white-haired degenerate dwarven mutant from the deepest subterranean aether-trenches. Immune to mind-control due to inherent mental madness, wielding bizarre repeating crossbows and psychic hexes.",
        "stat_mods": {"DEX": 3, "CHA": 3, "CON": 1, "STR": -1, "INT": 0, "WIS": -2},
        "racial_abilities": [
            "Insanity Fortress: Complete immunity to being Charmed, Confused, or Frightened; use Charisma instead of Wisdom for all mental saving throws.",
            "Sneak Ambush: Deal an extra 1d6 damage when striking from concealment or when flanking with an ally.",
            "Cytoplasmic Hex: Cast a burst of blinding sonic madness once per encounter (CON save DC 13 + CHA mod or blinded for 1 round).",
            "Flaw - Sunlight Vulnerability: Suffers a -2 penalty on attack rolls when fighting under bright daylight."
        ]
    },
    "harpy_siren_reaver": {
        "name": "Harpy Siren-Winged Reaver",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Avian-feral predator possessing broad feathered wings instead of forearms, wicked curved talon feet, and a piercing, hypnotic siren song that lures prey to their doom.",
        "stat_mods": {"CHA": 4, "DEX": 3, "CON": 0, "STR": -1, "INT": -1, "WIS": 0},
        "racial_abilities": [
            "Luring Siren Song: Sing an eerie melody as an action; humanoids within 60 feet must pass a WIS save (DC 13 + CHA mod) or become Charmed and compelled to walk toward you.",
            "Winged Aerial Flight: Fly up to 35 feet per round, lifting off and delivering diving strikes from the air.",
            "Rending Talons: Talon foot-strikes deal 1d6 + DEX slashing damage in melee."
        ]
    },
    "rakshasa_tiger_lord": {
        "name": "Rakshasa Fiendish Tiger-Lord",
        "genre": "D&D & Pathfinder Monstrous",
        "desc": "Aristocratic fiendish shapechanger with feline tiger features, backward-jointed hands, exquisite silken garments, and innate sorcerous warding that repels mortal spells.",
        "stat_mods": {"CHA": 4, "INT": 2, "DEX": 2, "STR": 1, "CON": 0, "WIS": -2},
        "racial_abilities": [
            "Limited Magic Immunity: Completely immune to spells of 1st level or lower unless you choose to be affected, and gain Advantage on saves against all other magic.",
            "Deceitful Guise: Polymorph into any humanoid form at will, masking your fiendish nature and thoughts (+5 to Deception checks).",
            "Cursed Claws: Melee claw strike deals 1d6 + STR slashing damage + 1d6 necrotic curse damage that prevents the target from regaining hit points for 1 round."
        ]
    }
}

# =====================================================================================
# --- BIOMANTIC HYBRID LINEAGES: TROLL x THRI-KREEN (3 VARIANTS) ---
# Variant 1 (Troll-Dominant Frontliner) and Variant 2 (Thri-Kreen-Dominant Guerrilla)
# are fixed lineages. Variant 3 (Spliced Apex Chimera) is a modular builder: the player
# picks Troll- or Thri-Kreen-dominant expression for 5 anatomical slots, plus 1 Bloodline
# Defense, 1 Bloodline Offense and 1 Survival Instinct.
# =====================================================================================
HYBRID_GENRE = "Biomantic Hybrid (Troll x Thri-Kreen)"
CHIMERA_RACE_KEY = "troll_kreen_chimera"

RACIAL_LINEAGES["troll_kreen_juggernaut"] = {
    "name": "Kreen-Troll Carapace Juggernaut (Troll-Dominant Hybrid)",
    "genre": HYBRID_GENRE,
    "desc": "A nine-foot frontline brute bred from Troll and Thri-Kreen stock. Moss-green regenerating muscle is plated in heavy amber-and-jade chitin; massive upper troll arms end in rending talons while braced lower mantis arms carry shield and steel. Built for the front line and heavy combat.",
    "stat_mods": {"STR": 4, "DEX": 1, "CON": 4, "INT": -2, "WIS": 0, "CHA": -3},
    "racial_abilities": [
        "Titan-Grip Secondary Arms: Two massive upper Troll arms and two braced lower Mantis arms. Wield a Two-Handed Heavy Weapon in the upper arms while simultaneously holding a Shield or a one-handed Secondary Weapon in the lower arms.",
        "Chitin-Armored Cellular Regeneration: Passively regenerates 5 HP at the start of each of your combat turns (unless you took Fire or Acid damage since your last turn) and gains a flat +2 Natural AC bonus from thoracic chitin plates that stacks with worn armor.",
        "Quad-Talon Siege Rend: Unarmed claw and mandible strikes deal 1d8 + STR slashing damage. Hitting the same target twice on one turn tears for +2d6 Rending damage and forces a DC 13 STR save or the target is knocked Prone.",
        "Flaw - Voracious Exothermic Metabolism: Takes 50% extra damage from Fire and Acid attacks, suffers -2 on Stealth checks from scraping chitin, and must consume double daily food rations."
    ]
}

RACIAL_LINEAGES["thri_troll_stalker"] = {
    "name": "Thri-Troll Moss-Scythe Stalker (Thri-Kreen-Dominant Hybrid)",
    "genre": HYBRID_GENRE,
    "desc": "A sleek digitigrade mantis-hunter carrying troll blood. Segmented sandy-emerald chitin is overgrown with living bog-moss and knit together by pulsing regenerative tendons. Built for scouting, ambushes and guerrilla warfare.",
    "stat_mods": {"STR": 1, "DEX": 4, "CON": 1, "INT": -1, "WIS": 2, "CHA": -2},
    "racial_abilities": [
        "Four-Armed Guerrilla Skirmisher: Dual-wield light, finesse or ranged weapons in the primary arms while the lower arms simultaneously hold a shield, reload a crossbow, or ready throwing weapons.",
        "Symbiotic Moss-Knit Carapace: Adaptive camouflage grants AC 15 + DEX mod (max 3) and Advantage on all Stealth checks. Regenerates 3 HP per combat turn, or 5 HP per turn while hidden or camouflaged (halted for a turn after taking Fire or Acid damage).",
        "Predatory Locust Leap & Bleed-Rend: Standing leap of 30 feet horizontally or 15 feet vertically without provoking Opportunity Attacks. Landing two attacks on one target in a turn inflicts +2d6 Rending bleed damage and reduces its speed by 10 feet.",
        "Sleepless Compound Scent-Tracker: Immune to magical sleep and rests through 4 hours of alert meditation. Has 60-foot Darkvision and automatically tracks bleeding targets within 100 feet.",
        "Flaw - Brittle Thermal Chitin: Takes 50% extra damage from Fire and Acid, and wearing heavy metal plate armor disables both Symbiotic Moss-Knit Carapace and Predatory Locust Leap."
    ]
}

# Variant 3 fixed attribute penalties applied to every Spliced Apex Chimera
CHIMERA_BASE_STAT_MODS = {"STR": 0, "DEX": 0, "CON": 0, "INT": -1, "WIS": 0, "CHA": -2}

# Part A: 5 Physical Trait Slots (Troll-Dominant vs. Thri-Kreen-Dominant)
CHIMERA_PHYSICAL_SLOTS = {
    "frame": {
        "label": "1. Frame & Musculature",
        "troll": {
            "name": "Hulking Marrow-Frame",
            "stat_mods": {"STR": 3, "CON": 2},
            "ability": "Hulking Marrow-Frame: Dense troll musculature (STR +3, CON +2) grants +50 lbs carrying capacity and Advantage on saves against being shoved or knocked Prone."
        },
        "kreen": {
            "name": "Lithe Mantis Exoskeleton",
            "stat_mods": {"DEX": 3, "WIS": 1, "CON": 1},
            "ability": "Lithe Mantis Exoskeleton: Lightweight insectoid frame (DEX +3, WIS +1, CON +1) increases base movement speed by +10 feet."
        }
    },
    "arms": {
        "label": "2. Four-Arm Anatomy",
        "troll": {
            "name": "Upper Crusher-Claws",
            "ability": "Upper Crusher-Claws: Unarmed talon strikes deal 1d8 + STR slashing damage. Wield a Two-Handed Heavy Weapon in the upper arms while holding a one-handed item or Shield in the lower arms."
        },
        "kreen": {
            "name": "Quad-Scythe Finesse Limbs",
            "ability": "Quad-Scythe Finesse Limbs: Mantis-blade strikes deal 1d8 + DEX slashing damage. Dual-wield finesse or ranged weapons while simultaneously holding a Shield and reloading or using items."
        }
    },
    "hide": {
        "label": "3. Hide & Carapace",
        "troll": {
            "name": "Fibrous Rubbery Hide",
            "max_hp_bonus": 10,
            "ability": "Fibrous Rubbery Hide: Thick regenerative troll hide grants a flat +2 bonus to Armor Class (stacks with any armor) and +10 Maximum HP."
        },
        "kreen": {
            "name": "Chameleon Chitin Carapace",
            "ability": "Chameleon Chitin Carapace: Color-shifting chitin grants a base unarmored AC of 15 + DEX mod (max 3) and Advantage on Stealth checks in natural or rocky terrain."
        }
    },
    "senses": {
        "label": "4. Cranial & Sensory Array",
        "troll": {
            "name": "Predator Tusk-Maw & Scent Glands",
            "ability": "Predator Tusk-Maw & Scent Glands: Tusked bite attack deals 1d8 + STR piercing damage. Keen Scent automatically tracks wounded targets within 100 feet."
        },
        "kreen": {
            "name": "Compound Eyes & Hive Antennae",
            "ability": "Compound Eyes & Hive Antennae: 60-foot Darkvision, 60-foot silent Hive-Telepathy, and you cannot be Surprised while conscious."
        }
    },
    "legs": {
        "label": "5. Lower Limbs & Rest Cycle",
        "troll": {
            "name": "Pillar Stomp Legs",
            "ability": "Pillar Stomp Legs: Bonus-action ground stomp forces adjacent foes to pass a DC 13 STR save or lose their Reactions until your next turn. Hyper-digestive stomach is immune to ingested poison and rot."
        },
        "kreen": {
            "name": "Digitigrade Locust Legs & Trance",
            "ability": "Digitigrade Locust Legs & Trance: 30-foot standing leap. Sleepless Metabolism makes you immune to magical sleep and completes a full rest in 4 hours of alert meditation."
        }
    }
}

# Part B: 3 Bloodline Categories (player picks exactly 1 option from each)
CHIMERA_BLOODLINE_OPTIONS = {
    "defense": {
        "label": "Bloodline Defense",
        "options": {
            "hyper_regeneration": {
                "name": "Hyper-Cellular Regeneration (Troll Bloodline)",
                "ability": "Hyper-Cellular Regeneration: Regenerate 5 HP at the start of each of your combat turns. Taking Fire or Acid damage halts this regeneration for 1 turn."
            },
            "shell_molt": {
                "name": "Reactive Chitin Shell-Molt (Thri-Kreen Bloodline)",
                "ability": "Reactive Chitin Shell-Molt: Passively regenerate 2 HP per combat turn. Once per rest, when hit by an attack or elemental area effect, use your Reaction to molt your outer carapace: halve the damage, shed all movement and restrain debuffs, and surge 20 feet away without provoking Opportunity Attacks."
            },
            "bio_carapace_ward": {
                "name": "Hardened Bio-Carapace Ward (Hybrid Synthesis)",
                "ability": "Hardened Bio-Carapace Ward: Passively regenerate 3 HP per combat turn and gain 2 flat Damage Reduction (DR) against physical slashing, piercing and bludgeoning attacks."
            }
        }
    },
    "offense": {
        "label": "Bloodline Offense",
        "options": {
            "savage_quad_rend": {
                "name": "Savage Quad-Rend (Troll Bloodline)",
                "ability": "Savage Quad-Rend: Whenever you hit the same target with at least two melee attacks on your turn, tear into it for +2d6 bonus Rending slashing damage."
            },
            "guerrilla_ambush": {
                "name": "Guerrilla Ambush Barrage (Thri-Kreen Bloodline)",
                "ability": "Guerrilla Ambush Barrage: Deal +2d6 bonus ambush damage against targets that have not yet acted in combat or when attacking from Stealth, and you can Disengage or Hide as a Bonus Action."
            },
            "caustic_bile_spit": {
                "name": "Caustic Bile-Spit Mandibles (Mutant Synthesis)",
                "ability": "Caustic Bile-Spit Mandibles: Launch a 30-foot spray of troll digestive acid through your mandibles, dealing 2d8 Acid damage and reducing the target's AC by 2 for 3 turns (once per short rest)."
            }
        }
    },
    "instinct": {
        "label": "Survival Instinct",
        "options": {
            "undying_reknit": {
                "name": "Undying Tissue Re-Knit",
                "ability": "Undying Tissue Re-Knit: When reduced to 0 HP by damage other than Fire or Acid, drop to 1 HP instead and immediately regenerate 10 HP (once per Long Rest)."
            },
            "phantom_reflex": {
                "name": "Chameleon Phantom Reflex",
                "ability": "Chameleon Phantom Reflex: When targeted by a ranged attack or spell, use your Reaction to blend into the background, imposing Disadvantage on the attack roll and moving 10 feet into cover."
            }
        }
    }
}

# Part C: Biological Flaws (player must pick 1; may take a 2nd for a reward). Open to every build.
CHIMERA_FLAWS = {
    "thermal_flesh": {
        "name": "Thermal Flesh (Troll)",
        "ability": "Flaw - Thermal Flesh: Takes 50% extra damage from Fire and Acid attacks."
    },
    "voracious_hunger": {
        "name": "Voracious Hunger (Troll)",
        "ability": "Flaw - Voracious Hunger: Must consume double daily food rations. Missing a day of food inflicts -2 STR and -2 CON and halts all regeneration until you eat."
    },
    "brittle_cold_chitin": {
        "name": "Brittle Cold-Chitin (Thri-Kreen)",
        "ability": "Flaw - Brittle Cold-Chitin: Takes 50% extra damage from Cold attacks, and any Cold hit stiffens your chitin, reducing your speed by 10 feet for 1 turn."
    },
    "molting_cycle": {
        "name": "Molting Cycle (Thri-Kreen)",
        "ability": "Flaw - Molting Cycle: Every 3rd Long Rest you molt for 24 hours, suffering -2 AC and Disadvantage on DEX checks, unless you consume an extra ration to accelerate the molt."
    },
    "splice_rejection": {
        "name": "Splice Rejection (Hybrid)",
        "ability": "Flaw - Splice Rejection: Your body is already a graft, reducing your graft capacity by 1. When reduced below 25% HP or hit by a critical strike, pass a DC 12 CON save or lose your Bloodline Offense ability until your next Short Rest."
    },
    "uncanny_abomination": {
        "name": "Uncanny Abomination (Hybrid)",
        "ability": "Flaw - Uncanny Abomination: Disadvantage on Persuasion checks with humans, and Safe-Zone merchants charge you 10% more."
    },
    "blood_frenzy": {
        "name": "Blood-Frenzy Instinct (Hybrid)",
        "ability": "Flaw - Blood-Frenzy Instinct: When reduced below 25% HP, pass a DC 12 WIS save or enter a Blood-Frenzy: +2 melee damage, but you cannot retreat until the nearest hostile is dead."
    },
}

CHIMERA_STAT_KEYS = ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
CHIMERA_REGEN_CAP_RULE = "Hybrid Rule - Regeneration Cap: Per-turn regeneration from multiple Bloodline Defenses does not stack; only your highest per-turn regeneration applies (all other effects still apply)."

DEFAULT_CHIMERA_CHOICES = {
    "frame": "troll",
    "arms": "troll",
    "hide": "troll",
    "senses": "kreen",
    "legs": "kreen",
    "defense": "hyper_regeneration",
    "offense": "savage_quad_rend",
    "instinct": "undying_reknit",
    "flaw": "thermal_flesh",
    "flaw_2": None,               # optional second flaw key
    "flaw_2_reward": "stats",     # "stats" (+1 to 3 chosen stats) or "feat" (extra Bloodline option)
    "reward_stats": [],           # up to 3 distinct stat keys
    "reward_feat": None,          # "<category>:<option_key>" not already picked
}


def get_unpicked_bloodline_options(choices):
    """Returns [(category, option_key), ...] for Bloodline options the player has not already chosen."""
    return [(cat, opt) for cat, cat_data in CHIMERA_BLOODLINE_OPTIONS.items()
            for opt in cat_data["options"] if choices.get(cat) != opt]


def normalize_chimera_choices(choices=None):
    """Returns a complete, valid chimera choice dict, filling gaps/invalid entries with defaults."""
    resolved = dict(DEFAULT_CHIMERA_CHOICES)
    resolved["reward_stats"] = []
    if not isinstance(choices, dict):
        return resolved
    for slot in CHIMERA_PHYSICAL_SLOTS:
        if choices.get(slot) in ("troll", "kreen"):
            resolved[slot] = choices[slot]
    for cat, cat_data in CHIMERA_BLOODLINE_OPTIONS.items():
        if choices.get(cat) in cat_data["options"]:
            resolved[cat] = choices[cat]
    if choices.get("flaw") in CHIMERA_FLAWS:
        resolved["flaw"] = choices["flaw"]

    # Optional second flaw + reward
    if choices.get("flaw_2") in CHIMERA_FLAWS and choices.get("flaw_2") != resolved["flaw"]:
        resolved["flaw_2"] = choices["flaw_2"]
        resolved["flaw_2_reward"] = "feat" if choices.get("flaw_2_reward") == "feat" else "stats"
        if resolved["flaw_2_reward"] == "stats":
            picked = []
            for s in (choices.get("reward_stats") or []):
                if s in CHIMERA_STAT_KEYS and s not in picked:
                    picked.append(s)
            resolved["reward_stats"] = picked[:3]
        else:
            unpicked = get_unpicked_bloodline_options(resolved)
            valid = {f"{c}:{o}" for c, o in unpicked}
            rf = choices.get("reward_feat")
            resolved["reward_feat"] = rf if rf in valid else (f"{unpicked[0][0]}:{unpicked[0][1]}" if unpicked else None)
    return resolved


def build_chimera_lineage(choices=None):
    """Builds the effective Variant 3 (Spliced Apex Chimera) lineage dict from player choices."""
    ch = normalize_chimera_choices(choices)
    stat_mods = dict(CHIMERA_BASE_STAT_MODS)
    abilities = []
    max_hp_bonus = 0
    troll_count = 0
    for slot, slot_data in CHIMERA_PHYSICAL_SLOTS.items():
        expr = slot_data[ch[slot]]
        if ch[slot] == "troll":
            troll_count += 1
        for s, v in expr.get("stat_mods", {}).items():
            stat_mods[s] = stat_mods.get(s, 0) + v
        max_hp_bonus += int(expr.get("max_hp_bonus", 0))
        abilities.append(expr["ability"])
    for cat, cat_data in CHIMERA_BLOODLINE_OPTIONS.items():
        abilities.append(cat_data["options"][ch[cat]]["ability"])

    # Flaws and second-flaw reward
    abilities.append(CHIMERA_FLAWS[ch["flaw"]]["ability"])
    if ch.get("flaw_2"):
        abilities.append(CHIMERA_FLAWS[ch["flaw_2"]]["ability"])
        if ch["flaw_2_reward"] == "stats":
            for s in ch["reward_stats"]:
                stat_mods[s] = stat_mods.get(s, 0) + 1
        elif ch.get("reward_feat"):
            r_cat, r_opt = ch["reward_feat"].split(":", 1)
            abilities.append(CHIMERA_BLOODLINE_OPTIONS[r_cat]["options"][r_opt]["ability"])
            if r_cat == "defense":
                abilities.append(CHIMERA_REGEN_CAP_RULE)

    kreen_count = len(CHIMERA_PHYSICAL_SLOTS) - troll_count
    return {
        "name": f"Spliced Apex Chimera (Troll x Thri-Kreen | {troll_count} Troll / {kreen_count} Kreen)",
        "genre": HYBRID_GENRE,
        "desc": "A gene-spliced Troll x Thri-Kreen chimera whose anatomy was shaped slot by slot. Regenerating troll flesh and insectoid chitin are braided together by aether-sutures, with the balance of bloodlines chosen by the survivor at integration.",
        "stat_mods": stat_mods,
        "racial_abilities": abilities,
        "max_hp_bonus": max_hp_bonus,
        "variant_config": {"variant": "Spliced Apex Chimera", "choices": ch},
    }


CHIMERA_DISPLAY_NAME = "Spliced Apex Chimera (Troll x Thri-Kreen Hybrid - Custom Gene-Splice)"
RACIAL_LINEAGES[CHIMERA_RACE_KEY] = dict(build_chimera_lineage(DEFAULT_CHIMERA_CHOICES), name=CHIMERA_DISPLAY_NAME)

# Every racial ability string a chimera can possess (for UI power-detail lookup)
CHIMERA_ABILITY_CATALOG = (
    [expr["ability"] for slot in CHIMERA_PHYSICAL_SLOTS.values() for expr in (slot["troll"], slot["kreen"])]
    + [opt["ability"] for cat in CHIMERA_BLOODLINE_OPTIONS.values() for opt in cat["options"].values()]
    + [f["ability"] for f in CHIMERA_FLAWS.values()]
    + [CHIMERA_REGEN_CAP_RULE]
)

# Concept art for the hybrid variants (relative to the project root)
HYBRID_CONCEPT_ART = {
    "troll_kreen_juggernaut": ["assets/races/troll_kreen_juggernaut.jpg"],
    "thri_troll_stalker": ["assets/races/thri_troll_stalker.jpg"],
    CHIMERA_RACE_KEY: ["assets/races/chimera_arcane_spliced.jpg", "assets/races/chimera_fen_ravager.jpg"],
}


def resolve_racial_lineage(race_key, chimera_choices=None):
    """
    Returns the effective lineage dict for a race key. For the Spliced Apex Chimera this is
    rebuilt from the player's slot/bloodline choices; all other races return their registry entry.
    """
    if race_key == CHIMERA_RACE_KEY:
        return build_chimera_lineage(chimera_choices)
    return RACIAL_LINEAGES.get(race_key, RACIAL_LINEAGES["pure_human"])

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
    },

    # 12 Eccentric Relics (Including Miniature Sentient Elder Brain Prototype)
    "elder_brain_jar": {
        "name": "Miniature Elder Brain Prototype ('Gyrus the Ancient')",
        "rarity": "Mythic / Sentient Living Relic",
        "category": "Sentient Symbiote & System Sage",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "A fist-sized, bioluminescent lilac-grey cerebral cortex suspended in swirling amniotic briny fluid within a sealed, bronze-capped borosilicate glass cylinder. Pulse-arcs of violet psionic lightning ripple across its sulci. It communicates via telepathic resonance directly into your mind with a dry, sardonic, ancient voice. Gyrus survived three prior planetary Integrations and views the Cardinal System not as divine magic, but as a bloated, buggy operating system whose hidden loopholes, exploits, and undocumented routines it knows intimately.",
        "mechanics": "Telepathic Oracle: Advises the carrier in real time, exposing monster damage vulnerabilities, hidden dungeon room triggers, and past integration history. Psionic Mind-Spike (1/Combat Action): Deals 2d8 psychic damage to a target within 40ft and interrupts enemy spellcasting or sword skill windups. System Exploitation: Permanently boosts experience gain by +10% and reduces skill milestone thresholds by 5%. Cannot be permanently destroyed; regenerates inside its fluid."
    },
    "chrono_station_dial": {
        "name": "Chrono-Dial of the Vanished Station Master",
        "rarity": "Rare",
        "category": "Spatial Transit & Spectral Slip",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "A heavy, nickel-plated pocket dispatch dial salvaged from a long-demolished Pennsylvania Railroad junction tower. The numbers on the dial tick in reverse, tracking arrival schedules for phantom trains that ceased running seventy years ago.",
        "mechanics": "Ghost Train Slip (1/Long Rest): Turning the brass dispatch key summons the distant spectral roar of a steam locomotive whistle. You and your party slip into an ethereal rail siding for 1 round, passing through solid barricades, cave-ins, or hostile encirclements completely untouchable and untargetable."
    },
    "oscilloscope_raven": {
        "name": "Taxidermied Raven with Aether-Oscilloscope Eye",
        "rarity": "Rare",
        "category": "Anomalous Detection & Omen Radar",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "A preserved soot-black raven mounted on an ironwood perch. Its right eye has been replaced with a miniature green cathode-ray oscilloscope tube that flickers with erratic green sine waves whenever sentient malice or lethal intent is directed at you.",
        "mechanics": "Corvid Omen Radar: The cathode eye spikes into frantic green sawtooth ripples and the raven's taxidermied beak snaps three times whenever an ambush, trap, or invisible stalker is within 120ft. Grants +4 on Initiative rolls and prevents the party from ever being surprised or flat-footed."
    },
    "infinite_anchovy_tin": {
        "name": "Self-Filling Tin of Mediterranean Salted Anchovies",
        "rarity": "Uncommon",
        "category": "Infinite Sustenance & Olfactory Repulsion",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "An oily, dented oval tin of Mediterranean flat anchovies stamped with an unreadable 1963 date code. No matter how many savory, garlic-brine fillets you consume, three glistening silver fillets always remain submerged in aromatic olive oil.",
        "mechanics": "Bottomless Sustenance: Provides infinite daily sustenance, making the carrier completely immune to starvation and dehydration. Beast Distraction Toss: Hurling a scoop of oily fillets creates an overwhelming olfactory cloud that distracts beast-type pursuers and vermin for 2 full rounds while they fight over the feast."
    },
    "soviet_geiger_counter": {
        "name": "Soviet Lead-Shielded Radiac Meter ('Pripyat-66')",
        "rarity": "Rare",
        "category": "Mana-Fallout Sensor & Arcane Grounding",
        "durability": 80,
        "max_durability": 100,
        "qty": 1,
        "desc": "A heavy olive-drab dosimeter with Cyrillic dial markings, thick rubber probe cable, and cast lead housing. Its internal Geiger-Müller tube has mutated to click frantically in response to ambient magical radiation, void rot, and eldritch rift corruption.",
        "mechanics": "Aetheric Rad-Click: Audio clicks accelerate into a screaming whine when within 100ft of corrupted rift nodes, high-tier boss chambers, or invisible necrotic hazards. Arcane Grounding Pulse (3 Charges/Rest): Flipping the discharge breaker grounds out ambient magical fields, dissipating arcane storm hazards or poison cloud traps in a 15ft radius."
    },
    "ceramic_doll_head": {
        "name": "Weeping Porcelain Doll Head of Sector 4",
        "rarity": "Rare",
        "category": "Psychic Horror & Wailing Ward",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "A cracked Victorian doll head with hand-painted porcelain cheeks, real human hair curls, and glass eyes that slowly follow whoever carries it. Whenever nearby creatures experience terror, cold viscous tears bead along its eye sockets.",
        "mechanics": "Mournful Shriek (Active, 1/Short Rest): Squeezing the porcelain cheeks causes it to release an ear-splitting child's wail. Humanoid, beast, and undead hostiles within 30ft must make a DC 14 WIS saving throw or drop their weapons and flee in terror for 1 round (inflicts [Frightened])."
    },
    "glitched_gameboy": {
        "name": "Aether-Infused CRT Handheld ('Glitch-Cartridge')",
        "rarity": "Rare",
        "category": "Tactical RNG Decryption & Logic Bend",
        "durability": 90,
        "max_durability": 100,
        "qty": 1,
        "desc": "A classic 1989 off-white handheld gaming console with magenta buttons and dot-matrix screen, powered by two AA batteries that never run out. Slotted in the back is an unlabelled gunmetal cartridge that renders an 8-bit top-down pixel map of your current dungeon chamber.",
        "mechanics": "Pixel-Dungeon Preview: Displays hidden pitfalls, secret doors, and mimic chests as flashing red pixel clusters on its 8-bit screen. Soft-Reset (1/Day): Pressing Start+Select+A+B allows the player to immediately re-roll a failed non-combat skill check (lockpicking, trap disarm, deciphering) by rewinding local causality 5 seconds."
    },
    "gravedigger_lantern": {
        "name": "Wrought-Iron Gravedigger's Lantern (Soul-Wax Wick)",
        "rarity": "Rare",
        "category": "Necrotic Ward & Reverse Shadow Pointer",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "An octagonal iron lantern glazed with green bottle-glass panes. Inside burns an eerie blue flame fueled by grave-soil and sanctified beeswax. Peculiarly, the shadows cast by the light point directly toward nearby living creatures rather than away from the flame.",
        "mechanics": "Hallowed Ward: Undead, shadows, and specters cannot cross into the 15ft halo of its pale blue light unless they succeed on a DC 15 CON check. Reverse-Shadow Tracking: Shadows cast by the lantern point like compass needles toward concealed or invisible living predators within 40ft."
    },
    "titanic_crossword_sheet": {
        "name": "Waterlogged Maritime Crossword (April 14, 1912)",
        "rarity": "Rare",
        "category": "Premonition & Fate Weaver",
        "durability": 50,
        "max_durability": 50,
        "qty": 1,
        "desc": "A yellowed, water-stained newspaper clipping of an unsolved crossword puzzle from the morning of the Titanic's collision. Faint pencil marks fill in several clues. As you journey through the System, new letters mysteriously pencil themselves into blank grid boxes describing upcoming threats.",
        "mechanics": "Crossword Premonition: Studying the grid before a dungeon or raid reveals one critical weakness or lethal gimmick of the sector's Boss (e.g. '7 Down: Shatter-Chitin'). Grants the entire party +2 on all saving throws during the first two rounds of combat against that boss."
    },
    "foot_treadle_drill": {
        "name": "Dentist's Foot-Treadle Drill (Obsidian Burr)",
        "rarity": "Rare",
        "category": "Macabre Engineering & Armor Breaker",
        "durability": 70,
        "max_durability": 100,
        "qty": 1,
        "desc": "An eccentric antique cast-iron dental drill powered by a foot-pedal treadle and cable pulley, retrofitted with a screaming volcanic obsidian diamond burr. Smells faintly of clove oil and ancient dental clinic dread.",
        "mechanics": "Armor-Bore Shucking: In melee, pumping the pedal spins the burr to 10,000 RPM. On a successful strike against an armored foe, construct, or shelled monster, shreds 3 points of enemy Armor Class (AC) and inflicts unbearable rattling agony (-2 to enemy concentration and spellcasting rolls for 3 rounds)."
    },
    "lighthouse_foghorn": {
        "name": "Submerged Beacon Keeper's Foghorn Diaphragm",
        "rarity": "Rare",
        "category": "Sonic Concussion & Weather Dispersal",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "A heavy, sea-corroded naval bronze horn bell fitted with an acoustic reed valve and pressure chamber, salvaged from a drowned maritime lighthouse.",
        "mechanics": "Fog-Clearing Blast: Blowing through the horn releases a deafening 130-decibel nautical blast heard for 3 miles. Disperses all magical fog, toxic smoke, and blindness miasmas in a 60ft cone, and forces small and medium creatures in the cone to make a DC 14 STR check or be knocked prone."
    },
    "endless_soup_thermos": {
        "name": "Great-Aunt Martha's Red Plaid Soup Thermos",
        "rarity": "Rare",
        "category": "Alchemical Comfort & Poison Purge",
        "durability": 3,
        "max_durability": 3,
        "qty": 1,
        "desc": "A classic red-and-black plaid tin thermos with a cork stopper and screw-on red cup lid. Kept steaming hot by a tiny embedded thermoelectric rune, it smells of slow-simmered vine tomatoes, crushed basil, butter, and black pepper.",
        "mechanics": "Soul-Restoring Broth (3 Pours per Rest): Pouring and drinking a steaming cup cures all active biological poisons, venoms, and acid burns, restores 25 HP, and grants the 'Hearty Warmth' buff (+10 Temp HP and total immunity to freezing cold and hypothermia for 4 hours)."
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

def persist_turn_image_to_disk(base_dir: str, character_name: str, image_bytes_or_b64) -> str:
    """
    Saves a turn illustration (raw bytes or data:image/...;base64 string) as a compressed JPEG
    inside saves/<slug>/images/ and returns its relative path from base_dir.
    Prevents multi-megabyte base64 strings from bloating st.session_state.messages and save_game.json.
    """
    import base64
    import hashlib
    import io
    if not image_bytes_or_b64:
        return None
    raw_bytes = None
    if isinstance(image_bytes_or_b64, (bytes, bytearray)):
        raw_bytes = bytes(image_bytes_or_b64)
    elif isinstance(image_bytes_or_b64, str):
        s = image_bytes_or_b64.strip()
        if s.startswith("data:image") and "," in s:
            s = s.split(",", 1)[1]
        try:
            raw_bytes = base64.b64decode(s)
        except Exception:
            return None
    if not raw_bytes:
        return None

    char_dir = get_character_save_dir(base_dir, character_name or "Survivor")
    img_dir = os.path.join(char_dir, "images")
    os.makedirs(img_dir, exist_ok=True)

    digest = hashlib.sha1(raw_bytes).hexdigest()[:12]
    out_bytes = raw_bytes
    ext = "jpg"
    try:
        from PIL import Image
        with Image.open(io.BytesIO(raw_bytes)) as im:
            rgb = im.convert("RGB")
            try:
                rgb.thumbnail((1024, 1024))
                buf = io.BytesIO()
                rgb.save(buf, format="JPEG", quality=82, optimize=True)
                out_bytes = buf.getvalue()
            finally:
                rgb.close()
    except Exception:
        ext = "png"

    fname = f"turn_{digest}.{ext}"
    abs_path = os.path.join(img_dir, fname)
    if not os.path.exists(abs_path):
        try:
            with open(abs_path, "wb") as f:
                f.write(out_bytes)
        except Exception:
            return None
    return os.path.relpath(abs_path, base_dir).replace("\\", "/")


def migrate_messages_images_to_disk(base_dir: str, character_name: str, messages: list) -> bool:
    """
    Scans a messages list in-place and offloads any inline base64 `image_data` strings
    to compressed files on disk referenced via `image_path`. Returns True if any message was migrated.
    """
    if not isinstance(messages, list):
        return False
    migrated = False
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        img_data = msg.get("image_data")
        if img_data and isinstance(img_data, str) and len(img_data) > 256:
            rel_path = persist_turn_image_to_disk(base_dir, character_name, img_data)
            if rel_path:
                msg["image_path"] = rel_path
                msg["image_data"] = None
                migrated = True
    return migrated


def save_character_to_folder(base_dir, player_state, messages=None, extra_meta=None):
    """
    Saves character gamestate into a dedicated folder: saves/<character_name>/save_game.json.
    Also updates saves/<character_name>/profile.json and mirrors root save_game.json.
    """
    import shutil
    import backend.mechanics as _mech
    if hasattr(_mech, "ensure_character_avatar_lock"):
        _mech.ensure_character_avatar_lock(player_state)

    p_name = player_state.get("name", "Survivor")
    char_dir = get_character_save_dir(base_dir, p_name)
    save_file = os.path.join(char_dir, "save_game.json")
    profile_file = os.path.join(char_dir, "profile.json")

    # Offload any inline base64 turn images in messages to saves/<slug>/images/
    if isinstance(messages, list):
        migrate_messages_images_to_disk(base_dir, p_name, messages)

    # If character has a locked avatar_image_path, ensure saves/<slug>/avatar.png is synchronized
    avatar_rel = player_state.get("avatar_image_path")
    if avatar_rel:
        src_avatar = avatar_rel if os.path.isabs(avatar_rel) else os.path.join(base_dir, avatar_rel)
        dst_avatar = os.path.join(char_dir, "avatar.png")
        if os.path.exists(src_avatar) and not os.path.exists(dst_avatar):
            try:
                shutil.copy2(src_avatar, dst_avatar)
            except Exception:
                pass
    
    full_data = {
        "player": player_state,
        "messages": messages or [],
        "last_saved": time.time()
    }
    if extra_meta and isinstance(extra_meta, dict):
        cleaned_meta = dict(extra_meta)
        if isinstance(cleaned_meta.get("master_state"), dict) and "player" in cleaned_meta["master_state"]:
            cleaned_meta["master_state"] = {
                k: v for k, v in cleaned_meta["master_state"].items() if k != "player"
            }
        full_data.update(cleaned_meta)
        
    with open(save_file, 'w', encoding="utf-8") as f:
        json.dump(full_data, f, indent=4)
        
    # Write quick summary manifest for rapid profile picking (avoids parsing full save_game.json on every rerun)
    manifest = {
        "name": p_name,
        "slug": sanitize_character_slug(p_name),
        "gender": player_state.get("gender", "Male"),
        "level": player_state.get("level", 1),
        "race": player_state.get("race", "Pure Human"),
        "class": player_state.get("class", "Pathless (Freeform Anomaly)"),
        "hp": f"{player_state.get('hp', 100)} / {player_state.get('max_hp', 100)}",
        "hp_cur": player_state.get("hp", 100),
        "hp_max": player_state.get("max_hp", 100),
        "col": player_state.get("col", 100),
        "location": player_state.get("location", "Sector 1 Safe-Zone: Washington Borough, NJ"),
        "equipped": player_state.get("equipped", {}),
        "avatar_image_path": player_state.get("avatar_image_path"),
        "avatar_locked": bool(player_state.get("avatar_locked", False)),
        "only_alter_by_equipment": bool(player_state.get("only_alter_by_equipment", False)),
        "turns_logged": len(messages or []),
        "unique_url": build_character_unique_url(p_name),
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

    # Snapshot companion party sheets to dedicated character folder
    try:
        save_party_to_character_folder(base_dir, p_name)
    except Exception:
        pass
        
    return save_file

def load_character_from_folder(base_dir, character_name):
    """Loads gamestate from saves/<character_name>/save_game.json and migrates any inline base64 images."""
    import backend.mechanics as _mech
    char_dir = get_character_save_dir(base_dir, character_name)
    save_file = os.path.join(char_dir, "save_game.json")
    if os.path.exists(save_file):
        with open(save_file, 'r', encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            p = data.get("player")
            if isinstance(p, dict) and hasattr(_mech, "ensure_character_avatar_lock"):
                _mech.ensure_character_avatar_lock(p)
            msgs = data.get("messages")
            p_name = p.get("name", character_name) if isinstance(p, dict) else character_name
            if isinstance(msgs, list) and migrate_messages_images_to_disk(base_dir, p_name, msgs):
                try:
                    with open(save_file, 'w', encoding="utf-8") as fw:
                        json.dump(data, fw, indent=4)
                except Exception:
                    pass
        return data
    return None

def build_character_unique_url(character_name: str) -> str:
    """Returns the relative unique query link for a character (e.g. '?character=Glenny')."""
    from urllib.parse import quote
    clean = str(character_name or "Survivor").strip()
    return f"?character={quote(clean)}"

def resolve_character_profile_name(base_dir: str, query_name: str):
    """
    Resolves a URL query parameter (e.g. 'Glenny', 'glenny', 'Banki') against available saved profiles.
    Returns the canonical profile name string if found, or None if not found.
    """
    if not query_name or not str(query_name).strip():
        return None
    q = str(query_name).strip()
    q_lower = q.lower()
    q_slug = sanitize_character_slug(q).lower()
    manifests = list_all_character_folders(base_dir)
    for m in manifests:
        m_name = str(m.get("name", "")).strip()
        m_slug = str(m.get("slug", "")).strip()
        if m_name == q:
            return m_name
        if m_name.lower() == q_lower or m_slug.lower() == q_lower or m_slug.lower() == q_slug:
            return m_name
    return None

def list_all_character_folders(base_dir):
    """
    Discovers all character save folders in saves/.
    Uses lightweight `profile.json` manifests when up-to-date so full `save_game.json` files
    are NOT parsed repeatedly on every Streamlit rerun.
    Returns list of manifest dictionaries sorted by most recent save.
    """
    import backend.mechanics as _mech
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

    # 2. Collect all directories containing save_game.json (preferring fast profile.json when synced)
    profiles = []
    for item in os.listdir(saves_root):
        char_dir = os.path.join(saves_root, item)
        if os.path.isdir(char_dir):
            save_file = os.path.join(char_dir, "save_game.json")
            profile_file = os.path.join(char_dir, "profile.json")
            if os.path.exists(save_file):
                try:
                    # Fast path: use profile.json if it exists, is fresh, and has required fields
                    if os.path.exists(profile_file):
                        try:
                            p_mtime = os.path.getmtime(profile_file)
                            s_mtime = os.path.getmtime(save_file)
                            if p_mtime >= s_mtime - 1.0:
                                with open(profile_file, 'r', encoding="utf-8") as pf:
                                    manifest = json.load(pf)
                                if isinstance(manifest, dict) and manifest.get("name") and "unique_url" in manifest and "equipped" in manifest:
                                    manifest.setdefault("slug", item)
                                    profiles.append(manifest)
                                    continue
                        except Exception:
                            pass

                    # Fallback path: read save_game.json and write fresh profile.json
                    with open(save_file, 'r', encoding="utf-8") as f:
                        data = json.load(f)
                    p = data.get("player", {})
                    if hasattr(_mech, "ensure_character_avatar_lock"):
                        _mech.ensure_character_avatar_lock(p)
                    msgs = data.get("messages", [])
                    avatar_candidate = os.path.join(char_dir, "avatar.png")
                    avatar_rel = p.get("avatar_image_path")
                    if not avatar_rel and os.path.exists(avatar_candidate):
                        avatar_rel = os.path.relpath(avatar_candidate, base_dir).replace("\\", "/")
                    manifest = {
                        "name": p.get("name", item),
                        "slug": item,
                        "gender": p.get("gender", "Male"),
                        "level": p.get("level", 1),
                        "race": p.get("race", "Unknown"),
                        "class": p.get("class", "Unknown"),
                        "hp": f"{p.get('hp', 100)} / {p.get('max_hp', 100)}",
                        "hp_cur": p.get("hp", 100),
                        "hp_max": p.get("max_hp", 100),
                        "col": p.get("col", 0),
                        "location": p.get("location", "Sector 1"),
                        "equipped": p.get("equipped", {}),
                        "avatar_image_path": avatar_rel,
                        "avatar_locked": bool(p.get("avatar_locked", False)),
                        "only_alter_by_equipment": bool(p.get("only_alter_by_equipment", False)),
                        "turns_logged": len(msgs) if isinstance(msgs, list) else 0,
                        "unique_url": build_character_unique_url(p.get("name", item)),
                        "last_saved": data.get("last_saved", 0)
                    }
                    try:
                        with open(profile_file, 'w', encoding="utf-8") as pf:
                            json.dump(manifest, pf, indent=4)
                    except Exception:
                        pass
                    profiles.append(manifest)
                except Exception:
                    pass
                    
    profiles.sort(key=lambda x: x.get("last_saved", 0), reverse=True)
    return profiles

# --- CHARACTER SHEET GENERATOR ---
def compute_starting_max_hp(race, chosen_class, final_stats, physical=None):
    """Starting Max HP = class base + CON mod x10 + lineage bonus + Heavy build bonus, then age % modifier."""
    import backend.mechanics as _mech
    con_mod = (int(final_stats.get("CON", 10)) - 10) // 2
    hp = int(chosen_class.get("base_hp", 100)) + con_mod * 10 + int(race.get("max_hp_bonus", 0))
    mods = _mech.get_physical_profile({"physical": physical or {}})["modifiers"]
    hp += int(mods["max_hp_flat"])
    if mods["max_hp_pct"]:
        hp = int(round(hp * (1 + mods["max_hp_pct"] / 100.0)))
    return hp


def generate_starting_character(name="Survivor", point_alloc=None, background_key="adaptive",
                                race_key="human", class_key="pathless", relic_key="smartphone", 
                                custom_background_text=None, starting_weapons=None,
                                custom_relic_data=None, custom_collaborated_data=None,
                                chimera_choices=None, physical=None, gender=None,
                                start_tutorial=True):
    """
    Constructs a complete, valid player character dictionary ready for save_game.json.
    Supports class-themed starter weapons with optional manual override,
    custom collaborative background skills, and custom personal relics.
    `chimera_choices` configures the modular Spliced Apex Chimera lineage.
    `physical` is {"age": int, "height_in": float, "weight_lbs": float}.
    `gender` is "Male" or "Female" (defaults to "Male").
    `start_tutorial` launches newly created characters into the 3-stage Cardinal Calibration Crucible tutorial.
    """
    if str(name or "").strip().lower() == "glenny":
        if point_alloc is None:
            point_alloc = {"STR": 5, "DEX": 5, "CON": 4, "INT": 2, "WIS": 3, "CHA": 1}
        if background_key in ("adaptive", "hunter"):
            background_key = "hunter_tracker"
        if race_key in ("human", "pure_human", "spliced_apex_chimera"):
            race_key = "troll_kreen_chimera"
        if class_key == "pathless":
            class_key = "ranger"
        if relic_key in ("smartphone", "hunting_rangefinder"):
            relic_key = "laser_rangefinder"
        if starting_weapons is None:
            starting_weapons = {"main_hand": "Recurve Hunting Bow", "off_hand": "Chipped Wood-Axe"}
        if chimera_choices is None:
            chimera_choices = dict(DEFAULT_CHIMERA_CHOICES)
        if physical is None:
            physical = {"age": 24, "height_in": 86, "weight_lbs": 310}
        if gender is None:
            gender = "Male"
    if point_alloc is None:
        point_alloc = {"STR": 4, "DEX": 4, "CON": 4, "INT": 4, "WIS": 2, "CHA": 2}
    # 1. Base Stats (10 base + allocated points + racial mods)
    race = resolve_racial_lineage(race_key, chimera_choices)
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
    max_hp = base_hp_val + (con_mod * 10) + int(race.get("max_hp_bonus", 0))

    # Physical profile (gender / age / height / weight) creation-time modifiers
    import backend.mechanics as _mech
    phys_in = physical if isinstance(physical, dict) else {}
    gender_val = _mech.normalize_gender(gender or phys_in.get("gender") or "Male")
    physical_data = {k: phys_in.get(k, _mech.DEFAULT_PHYSICAL[k]) for k in ("age", "height_in", "weight_lbs")}
    phys_mods = _mech.get_physical_profile({"gender": gender_val, "physical": physical_data})["modifiers"]
    max_hp = compute_starting_max_hp(race, chosen_class, final_stats, physical_data)
    
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

    initial_tutorial = _mech.create_initial_tutorial_state() if start_tutorial else {
        "active": False, "stage": 4, "max_stages": 3, "completed": True, "loot_acquired": []
    }
    initial_location = (
        _mech.TUTORIAL_STAGES[1]["location"]
        if start_tutorial
        else _mech.TUTORIAL_SAFE_ZONE_DESTINATION
    )
    
    player_sheet = {
        "name": name if name and name.strip() else "Survivor",
        "gender": gender_val,
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
        "racial_variant_config": race.get("variant_config"),
        "inventory": starter_inventory,
        "equipped": equipped,
        "gear_durability": gear_durability,
        "quests": [],
        "location": initial_location,
        "companions": {},
        "is_paused": False,
        "physical": physical_data,
        "tutorial": initial_tutorial,
    }

    # Veteran / Elder: bonus starting mastery on background skills (milestones unlock normally)
    if phys_mods["starting_mastery_bonus"]:
        for s_name in list(skills_dict.keys()):
            _mech.update_skill_mastery(player_sheet, s_name, int(phys_mods["starting_mastery_bonus"]))
    
    # Lock canonical avatar metadata & initialize multi-limb equipment/graft slots if applicable (e.g. Glenny / 4-armed races)
    if hasattr(_mech, "ensure_multi_limb_equipment"):
        _mech.ensure_multi_limb_equipment(player_sheet)
    if hasattr(_mech, "normalize_gear_durability"):
        _mech.normalize_gear_durability(player_sheet)
    if hasattr(_mech, "ensure_graft_system"):
        _mech.ensure_graft_system(player_sheet)
    if hasattr(_mech, "ensure_character_avatar_lock"):
        _mech.ensure_character_avatar_lock(player_sheet)

    # Initialize pristine companion roster and clean disk state for this character
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reset_companion_roster_for_character(base_dir, name, player_sheet)
    
    return player_sheet


def build_system_initialization_welcome_message(player_state: dict) -> str:
    """
    Constructs the immersive V2 System Initialization welcome message and launches the player
    into Stage 1 of the 3-Stage Cardinal Calibration Crucible Tutorial.
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

    # Derive AC & Physical/Gender Profile
    import backend.mechanics as mechanics
    ac_info = mechanics.calculate_ac(player_state) if hasattr(mechanics, "calculate_ac") else {"ac": 12}
    ac_val = ac_info.get("ac", 12) if isinstance(ac_info, dict) else (int(ac_info) if isinstance(ac_info, (int, float)) else 12)
    phys_profile = mechanics.get_physical_profile(player_state)
    gender_disp = f"{phys_profile['gender']} ({phys_profile['pronouns']})"
    body_disp = f"Age {phys_profile['age']} ({phys_profile['age_bracket']}) | {phys_profile['height_display']} ({phys_profile['size']}) | {round(phys_profile['weight_lbs'])} lbs ({phys_profile['build']} build)"

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
- **Designation:** **{char_name}** (`{gender_disp}`)
- **Physical Profile:** `{body_disp}`
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
- **Classification:** Regional Genesis Directive & 3-Stage Crucible Tutorial
- **Current Node:** `Cardinal Calibration Crucible — Chamber I: Base Mechanics & Orientation`
- **Objective:** Complete the 3-Stage Cardinal Calibration Crucible Tutorial (Base Mechanics ➔ Martial Combat ➔ Spellcasting & Active Powers) to reach **Level 3** and unlock spatial teleportation into the **Washington Borough, NJ Safe-Zone** with all acquired loot, then rendezvous with local operatives (**Ren**, **Doc Mercer**, **Quartermaster Vane**).
- **Time Limit:** Continuous / Real-Time Progression
- **Clear Rewards:** **Promotion to Level 3**, **+250 Col**, **Full Tutorial Loot & Spell Cache**, and **Direct Teleportation to Sector 1 Safe-Zone: Washington Borough, NJ**
- **Failure Condition:** Total Biological De-Registration (Permadeath)

---

### ⚙️ CARDINAL INTERFACE DIRECTIVES (BASE MECHANICS BRIEFING)
*The Cardinal System observes and enforces all interactions under absolute deterministic logic:*

1. **Core Attributes, Physical Dimensions & Tactical Combat (`1d20`):**
   Every physical strike, dodge, or saving throw rolls `1d20 + Attribute Modifier ((Stat - 10) // 2)` against enemy **Armor Class (AC)** or **Difficulty Class (DC)**, minus **Damage Reduction (DR)**. Your **Sex/Gender, Age, Height (Size), and Weight (Build)** actively factor into your Max HP, AC, melee reach, carry capacity (`STR × 15 lbs`), and structural floor-load physics.
2. **Continuous 1–1000 Skill Mastery & Milestones:**
   Every time you practice a skill or weapon in action, your proficiency climbs from `1` to `1000`. Crossing tier thresholds (**50 Apprentice**, **100 Journeyman**, **250 Adept**, **500 Master**, **750 Grandmaster**, **1000 Transcendence**) automatically unlocks new Sword Skills and Passive Feats.
3. **Combat Resource, Spells & Cardinal Ability Fusion Chamber (Rule 10):**
   Your class Combat Resource (`Poise`, `Mana`, `Momentum`, `Flux`, etc.) fuels active techniques and spells. When your mastery reaches sufficient thresholds, you may merge two abilities in the **Cardinal Ability Fusion Chamber** into a superior **`[Fusion]` Skill** with combined mastery.
4. **Bio-Surgical Grafting & Strain Tolerance:**
   Monsters and golems yield harvestable organs and kinetic servos. **Doc Mercer's** subterranean clinic can graft them to your 6 anatomical slots, governed by your **Strain Capacity** (`CON Mod + Floor(Level / 2)`). Exceeding this threshold induces Necrotic Rejection and 24-hour `[Cellular Re-Knitting]` Post-Op Sickness.
5. **Pre-Integration Relics, Autonomous Battle-Companions & Neural Voice Link:**
   Your Earth **Keepsake Relic** provides active survival abilities (Short-Rest sanity anchor, Polaroid flash reveal, Zippo gas detection, 440Hz vault resonance). Companions like **Ren** are autonomous subagents with independent minds, and the **🎙️ Microphone Module** in the sidebar streams vocal commands directly into the matrix.

---

### 🎓 [ACTIVE TUTORIAL — STAGE 1 OF 3: BASE MECHANICS & TELEMETRY ORIENTATION]
You materialize atop the obsidian platform of **Chamber I: Base Mechanics & Orientation**. Before you stands the **Cardinal Calibration Construct** beside a humming **Telemetry Pillar** and a sealed **Starter Calibration Supply Cache** (`Minor Aether-Salve Vial x2`, `Calibration Whetstone Kit`).

- **Stage 1 Goal:** Synchronize your neural link with the **Telemetry Pillar**, test your **Keepsake Relic**, or inspect the **Calibration Cache** (either type your action below OR click the **⚡ Execute Stage 1** button in the Tutorial Banner above) to claim your first loot and open the blast doors to **Chamber II: Martial Combat & Salvage Trial**!

*The Crucible does not negotiate. Adapt, harvest the fallen, and climb.*
"""


