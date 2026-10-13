"""
Pre-to-Post Integration Character Generator Engine
Translates real-world Earth knowledge, vocations, and physical conditioning into LitRPG parameters.
Fully integrated with the 1-1000 Skill Mastery and Mechanics Engine.
"""

import json
from backend.mechanics import calculate_encumbrance, calculate_ac, CANONICAL_MILESTONES

# --- PRE-INTEGRATION VOCATIONAL BACKGROUNDS ---
PRESET_BACKGROUNDS = {
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
        "innate_perk": "Structural Assessment (Passive): Instantly evaluate remaining durability and weak fracture points on enemy armor and constructs."
    },
    "hunter_outdoorsman": {
        "title": "Hunter / Outdoor Guide",
        "description": "Deep knowledge of wildlife behaviors, perimeter tracking, terrain navigation, and wire snares.",
        "stat_recommendations": {"DEX": 3, "WIS": 2, "CON": 1, "STR": 0, "INT": 0, "CHA": 0},
        "skills": {
            "Field Trapping": {
                "mastery": 60,
                "tier": "Apprentice",
                "description": "Deployment and concealment of wire snares, deadfalls, and bait lines.",
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
    }
}

# --- RACIAL MUTATIONS & LINEAGES ---
RACIAL_LINEAGES = {
    "pure_human": {
        "name": "Pure Human",
        "desc": "Resisted genetic mutation during the Aetheric Rift collapse. Highly adaptable, tenacious, and versatile.",
        "stat_mods": {"STR": 1, "DEX": 1, "CON": 1, "INT": 1, "WIS": 1, "CHA": 1},
        "racial_abilities": [
            "Tenacious Will: +10% bonus experience gain from all combat and discovery actions.",
            "Versatile Conditioning: +1 additional starting Feat slot."
        ]
    },
    "phrenic_human": {
        "name": "Phrenic Human",
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
        "desc": "Underground heritage fused with aether-furnaces. Unmatched physical fortitude and geological intuition.",
        "stat_mods": {"CON": 3, "STR": 2, "WIS": 1, "DEX": -1, "INT": 0, "CHA": -1},
        "racial_abilities": [
            "Stone-Sense: Instantly detect structural hollows, secret vaults, and ore seams in subterranean sectors.",
            "Toxic Hardening: Advantage on saving throws against atmospheric poisons, radiation, and spores."
        ]
    },
    "scrapper_goblinoid": {
        "name": "Scrapper Goblinoid",
        "desc": "Warped into an agile, sharp-eyed industrial scavenger. Masters of salvage, stealth, and evasion.",
        "stat_mods": {"DEX": 3, "INT": 2, "STR": -1, "CON": 0, "WIS": 0, "CHA": 0},
        "racial_abilities": [
            "Junk-Engine Intuition: Assemble and repair crude weapons/tools using 50% fewer materials.",
            "Scurry: Disengage from melee combat without drawing free hostile attacks."
        ]
    },
    "aether_elf": {
        "name": "Aether-Touched Elf",
        "desc": "Infused with raw ambient leyline energy. Graceful, sharp-eyed, and inherently sensitive to magic.",
        "stat_mods": {"DEX": 2, "INT": 2, "CHA": 1, "STR": -1, "CON": 0, "WIS": 0},
        "racial_abilities": [
            "Mana Resonance: Low-light vision and natural passive detection of magical wardings.",
            "Quickstep: Base overland travel speed increased by +15%."
        ]
    },
    "golem_reborn": {
        "name": "Golem Reborn",
        "desc": "Organic consciousness salvaged into a heavy mechanized construct of blackened steel and runic stone.",
        "stat_mods": {"CON": 4, "STR": 2, "DEX": -2, "CHA": -2, "INT": 0, "WIS": 0},
        "racial_abilities": [
            "Living Construct: Immune to biological diseases, starvation, and natural sleep exhaustion.",
            "Reinforced Chassis: Natural Armor Class increased by +2.",
            "Flaw - Machine Maintenance: Biological healing items are only 50% effective; requires tool repairs."
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

# --- PRE-INTEGRATION PERSONAL RELICS ---
PERSONAL_RELICS = {
    "smartphone": {
        "name": "Earth Smartphone (99% Battery, No Signal)",
        "rarity": "Unique",
        "durability": 99,
        "max_durability": 100,
        "qty": 1,
        "desc": "Cracked screen showing photos of family, unread text messages from Mom ('Where are you? Dinner is cold'), and an encrypted corporate employee app."
    },
    "multitool": {
        "name": "Mechanic's Heavy Multi-Tool",
        "rarity": "Uncommon",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "Hardened carbon-steel pliers, wire-cutters, and hex-bits. Grants a passive +2 bonus to field repairs and snare rigging."
    },
    "first_aid_pouch": {
        "name": "Trauma First-Aid Pouch",
        "rarity": "Uncommon",
        "durability": 3,
        "max_durability": 3,
        "qty": 1,
        "desc": "Sterile gauze pads, clotting powder, and antiseptic spray. Can be used 3 times to immediately cure severe Bleeding."
    },
    "city_map": {
        "name": "Laminated Regional Topo-Map",
        "rarity": "Uncommon",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "Real-world topographical map of Warren County NJ. Grants +5 starting Cartography mastery and reveals nearby water sources."
    },
    "pocket_watch": {
        "name": "Heirloom Pocket-Watch",
        "rarity": "Rare",
        "durability": 100,
        "max_durability": 100,
        "qty": 1,
        "desc": "Mechanical brass pocket watch passed down through generations. Ticks rhythmically and chimes when temporal glitch-rifts open nearby."
    }
}

def parse_custom_background(text):
    """
    Procedurally maps arbitrary custom Earth vocation descriptions into 2 balanced 1-1000 skills
    and a unique passive perk.
    """
    t = text.lower() if text else ""
    
    # Keyword analysis
    if any(k in t for k in ["electric", "circuit", "cable", "tech", "computer", "hack", "network"]):
        s1 = ("Magi-Tech Hacking", 45, "Bypassing arcane firewalls and corrupted terminals.")
        s2 = ("Aether-Circuit Query", 35, "Tracing energy lines and construct signal routing.")
        perk = "Circuit Intuition (Passive): Gain +2 on checks to manipulate or decrypt aetheric terminals."
    elif any(k in t for k in ["medic", "doctor", "nurse", "surgery", "hospital", "clinic", "heal"]):
        s1 = ("Arcane Triage", 50, "Stabilizing biological vitals and treating acute aetheric trauma.")
        s2 = ("Field Surgery", 40, "Extracting crystalline shrapnel and repairing damaged tissue.")
        perk = "Triage Discipline (Passive): Healing checks take half as much time and reduce bleeding DC by 2."
    elif any(k in t for k in ["mechanic", "machinist", "weld", "engine", "car", "fix", "repair", "craft"]):
        s1 = ("Field Smithing", 50, "Reforging weapons, repairing armor plates, and maintaining mechanical gear.")
        s2 = ("Golem-Graft Rigging", 40, "Tuning prosthetic joints, hydraulic seals, and aether-couplings.")
        perk = "Structural Assessment (Passive): Instantly evaluate fracture points on armor and constructs."
    elif any(k in t for k in ["hunt", "fish", "camp", "outdoor", "woods", "forest", "scout", "track"]):
        s1 = ("Field Trapping", 50, "Deployment and concealment of wire snares and perimeter traps.")
        s2 = ("Cartography", 45, "Topographical parsing, terrain mapping, and landmark navigation.")
        perk = "Wilderness Instinct (Passive): Gain advantage on initiative checks when ambushed in natural terrain."
    elif any(k in t for k in ["construct", "carpenter", "build", "mason", "labor", "demolition"]):
        s1 = ("Trench Hammers", 50, "Bludgeoning armor-crush strikes and heavy structural demolition attacks.")
        s2 = ("Structural Breach", 40, "Targeting load-bearing structures and reinforced bulkheads.")
        perk = "Kinetic Impact (Passive): Bludgeoning attacks against constructs and barriers deal +2 bonus damage."
    elif any(k in t for k in ["martial", "combat", "fight", "box", "soldier", "military", "guard"]):
        s1 = ("One-Handed Axes", 50, "Fast, brutal chops, hooks, and cleaves with single-handed blades.")
        s2 = ("Tactical Reflexes", 45, "Close-quarters footwork and split-second dodging.")
        perk = "Combat Readiness (Passive): +2 bonus to passive Armor Class during the first round of melee."
    elif any(k in t for k in ["cook", "chef", "bake", "food", "kitchen", "brew", "cater"]):
        s1 = ("Provisions & Alchemy", 50, "Brewing restorative elixirs and preparing nutritious stamina rations.")
        s2 = ("Aether-Weaving", 40, "Refining organic materials with ambient mana.")
        perk = "Comforting Ration (Passive): Consumed food buffs grant double stamina recovery and restore focus."
    elif any(k in t for k in ["sales", "negotiat", "law", "business", "exec", "manag"]):
        s1 = ("Resource Barter", 50, "Assessing market value and securing favorable trade contracts.")
        s2 = ("Faction Diplomacy", 40, "Navigating guild politics and safe-zone syndicates.")
        perk = "Silver Tongue (Passive): Safe-zone automated merchant casualty markups are discounted by 15%."
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

def generate_starting_character(name, point_alloc, background_key, race_key, class_key, relic_key, 
                                custom_background_text=None, starting_weapons=None):
    """
    Constructs a complete, valid player character dictionary ready for save_game.json.
    Supports class-themed starter weapons with optional manual override.
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
    
    # 3. Skills & Perks from Background (Preset or Custom)
    if background_key == "custom" and custom_background_text:
        bg = parse_custom_background(custom_background_text)
    else:
        bg = PRESET_BACKGROUNDS.get(background_key, PRESET_BACKGROUNDS["software_engineer"])
        
    skills_dict = {}
    feats_list = list(race["racial_abilities"])
    
    if bg.get("innate_perk"):
        feats_list.append(bg["innate_perk"])
        
    for s_name, s_data in bg.get("skills", {}).items():
        skills_dict[s_name] = dict(s_data)
        
    # Add Class Feats
    for f in chosen_class.get("starting_feats", []):
        feats_list.append(f)
        
    # 4. Weapons & Equipment Loadout
    # Use supplied manual override, or default to class-themed loadout
    class_def_weapons = CLASS_WEAPONS.get(class_key, CLASS_WEAPONS["pathless"])
    main_hand_w = (starting_weapons.get("main_hand") if starting_weapons else None) or class_def_weapons["main_hand"]
    off_hand_w = (starting_weapons.get("off_hand") if starting_weapons else None) or class_def_weapons["off_hand"]
    
    relic = PERSONAL_RELICS.get(relic_key, PERSONAL_RELICS["smartphone"])
    
    starter_inventory = [
        relic,
        {
            "name": main_hand_w,
            "rarity": "Common",
            "durability": 45,
            "max_durability": 50,
            "qty": 1,
            "desc": f"Starting Grade 1 weapon ({main_hand_w})."
        },
        {
            "name": "Bottled Water",
            "rarity": "Common",
            "durability": 1,
            "max_durability": 1,
            "qty": 2,
            "desc": "Clean, sealed drinking water from before the collapse."
        },
        {
            "name": "Survival Rations",
            "rarity": "Common",
            "durability": 1,
            "max_durability": 1,
            "qty": 2,
            "desc": "Vacuum-sealed nutrient paste and dried trail mix."
        }
    ]
    
    if off_hand_w and off_hand_w != "None":
        starter_inventory.append({
            "name": off_hand_w,
            "rarity": "Common",
            "durability": 45,
            "max_durability": 50,
            "qty": 1,
            "desc": f"Starting Grade 1 off-hand equipment ({off_hand_w})."
        })
        
    # 5. Starting Equipped
    equipped = {
        "head": "None",
        "chest": "Threadbare Scavenger Tunic",
        "main_hand": main_hand_w,
        "off_hand": off_hand_w,
        "accessory": relic["name"] if ("Watch" in relic["name"] or "Tool" in relic["name"]) else "None"
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
