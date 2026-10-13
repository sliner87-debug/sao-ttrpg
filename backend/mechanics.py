"""
Mechanics Engine for The Fractured Overlay (SAO TTRPG)
Handles mathematical crunch, dice logic, encumbrance physics, and equipment state.
"""

import math
import copy
import re
from backend.world_atlas import (
    WORLD_ATLAS_ZONES,
    resolve_zone_from_location,
    is_location_safe_zone,
    get_zones_by_category,
    get_zone_salvage_yields,
    calculate_travel_telemetry,
    format_zone_gm_briefing,
)
from backend.bestiary_compendium import (
    BESTIARY_COMPENDIUM,
    ZONE_DISPERSED_ECOLOGY,
    get_zone_dispersed_ecology,
    search_bestiary,
    roll_random_zone_encounter,
)

# --- ITEM WEIGHT HEURISTICS ---
DEFAULT_WEIGHT_MAP = {
    # Weapons
    "axe": 4.5,
    "sword": 3.5,
    "hammer": 6.0,
    "dagger": 1.0,
    "bow": 3.0,
    "pistol": 2.5,
    "rifle": 8.0,
    "spear": 5.0,
    # Armor & Apparel
    "rig": 30.0,
    "hauberk": 25.0,
    "plate": 45.0,
    "leather": 12.0,
    "chain": 28.0,
    "cloak": 3.0,
    "pelt": 5.0,
    "boots": 4.0,
    "helm": 5.0,
    "shield": 8.0,
    # Utility & Hardware
    "spool": 12.0,
    "cord": 8.0,
    "line": 6.0,
    "tripwire": 3.0,
    "snare": 5.0,
    "trap": 7.0,
    "jar": 3.5,
    "marrow": 2.5,
    "water": 1.5,
    "ration": 1.0,
    "clipboard": 2.0,
    "deck": 3.0,
    "usb": 0.1,
    "scroll": 0.5,
    "ore": 5.0,
    "scrap": 1.0,
    "anchor": 35.0
}

def get_item_weight(item):
    """Calculates total weight for a single item entry (considering quantity)."""
    if isinstance(item, str):
        name = item.lower()
        qty = 1
        if " x" in name:
            parts = name.rsplit(" x", 1)
            name = parts[0]
            try:
                qty = int(parts[1])
            except ValueError:
                pass
        base_w = 1.0
        for kw, w in DEFAULT_WEIGHT_MAP.items():
            if kw in name:
                base_w = w
                break
        return round(base_w * qty, 1)

    if isinstance(item, dict):
        qty = item.get("qty", 1)
        w_val = item.get("weight")
        if w_val is None:
            w_val = item.get("weight_lbs")
        if w_val is not None:
            try:
                return round(float(w_val) * qty, 1)
            except (ValueError, TypeError):
                pass
        
        name = item.get("name", "").lower()
        desc = item.get("desc", "").lower()
        full_text = f"{name} {desc}"
        
        base_w = 1.0
        for kw, w in DEFAULT_WEIGHT_MAP.items():
            if kw in full_text:
                base_w = w
                break
        return round(base_w * qty, 1)

    return 1.0

def calculate_encumbrance(player_state):
    """
    Calculates total carrying weight, slot capacity, encumbrance tier, and modifiers.
    Base STR * 15 = Max Carry Weight (lbs).
    10 + (STR // 2) = Max Inventory Slots.
    """
    stats = player_state.get("stats", {})
    str_val = stats.get("STR", 10)
    
    # Check for racial / feat carry capacity bonus (e.g. MageTech Cyborg Pneumatic Endoskeleton)
    bonus_capacity = 0.0
    race_str = str(player_state.get("race", "")).lower()
    feats_str = " ".join([str(f).lower() for f in player_state.get("feats", [])])
    if "cyborg" in race_str or "pneumatic endoskeleton" in feats_str:
        bonus_capacity += 25.0
        
    max_weight = round(str_val * 15.0 + bonus_capacity, 1)
    max_slots = 10 + (str_val // 2)
    
    current_weight = 0.0
    used_slots = 0
    
    # Calculate weight of equipped gear
    equipped = player_state.get("equipped", {})
    if isinstance(equipped, dict):
        for slot, item_name in equipped.items():
            if item_name and item_name != "None":
                current_weight += get_item_weight({"name": item_name, "qty": 1})
                
    # Calculate weight and slots of backpack inventory
    inventory = player_state.get("inventory", [])
    for item in inventory:
        w = get_item_weight(item)
        current_weight += w
        # Stacking slots: each entry takes 1 slot, or 1 slot per 5 units for lightweight bundled items (< 2.0 lbs per unit)
        qty = item.get("qty", 1) if isinstance(item, dict) else 1
        unit_w = (w / qty) if qty > 0 else w
        slots_taken = max(1, math.ceil(qty / 5)) if unit_w < 2.0 else qty
        used_slots += slots_taken
        
    current_weight = round(current_weight, 1)
    
    # Determine Encumbrance Tier
    weight_ratio = current_weight / max_weight if max_weight > 0 else 1.0
    
    if weight_ratio <= 0.50:
        tier = "Unencumbered"
        label = "🟢 Unencumbered"
        penalties = {"dex_mod": 0, "speed_pct": 100, "disadvantage_stealth": False}
    elif weight_ratio <= 0.75:
        tier = "Light Load"
        label = "🟢 Light Load"
        penalties = {"dex_mod": 0, "speed_pct": 100, "disadvantage_stealth": False}
    elif weight_ratio <= 1.0:
        tier = "Heavy Load"
        label = "🟠 Heavy Load"
        penalties = {"dex_mod": -2, "speed_pct": 85, "disadvantage_stealth": True}
    else:
        tier = "Overencumbered"
        label = "🔴 Overencumbered"
        penalties = {"dex_mod": -5, "speed_pct": 50, "disadvantage_stealth": True}
        
    return {
        "current_weight_lbs": current_weight,
        "max_weight_lbs": max_weight,
        "weight_percent": min(1.0, current_weight / max_weight) if max_weight > 0 else 1.0,
        "used_slots": used_slots,
        "max_slots": max_slots,
        "slots_percent": min(1.0, used_slots / max_slots) if max_slots > 0 else 1.0,
        "tier": tier,
        "label": label,
        "penalties": penalties
    }

def calculate_ac(player_state, encumbrance=None):
    """Calculates Armor Class based on DEX, equipped armor, durability state, natural armor, and encumbrance penalties."""
    if encumbrance is None:
        encumbrance = calculate_encumbrance(player_state)
        
    stats = player_state.get("stats", {})
    dex_val = stats.get("DEX", 10)
    dex_mod = (dex_val - 10) // 2
    
    # Encumbrance penalty to DEX
    dex_mod += encumbrance["penalties"]["dex_mod"]
    
    base_ac = 10 + dex_mod
    
    # Durability penalty calculations
    dur_pens = calculate_durability_penalties(player_state) if "gear_durability" in player_state else {}
    
    # Armor checks
    equipped = player_state.get("equipped", {})
    chest = equipped.get("chest", "").lower()
    
    armor_bonus = 0
    if dur_pens.get("chest_broken", False):
        armor_bonus = 0
    elif "einherjar" in chest or "plate" in chest or "gr. 5" in chest:
        armor_bonus = 8
    elif "chain" in chest or "hauberk" in chest:
        armor_bonus = 5
    elif "leather" in chest or "fur" in chest:
        armor_bonus = 3
        
    # Off-hand shield checks
    off_hand = equipped.get("off_hand", "").lower()
    shield_bonus = 0
    if "shield" in off_hand:
        shield_bonus = 0 if dur_pens.get("shield_broken", False) else 2
    
    # Natural AC from Lineage Traits
    natural_ac = 0
    race_str = str(player_state.get("race", "")).lower()
    feats_str = " ".join([str(f).lower() for f in player_state.get("feats", [])])
    if any(k in race_str for k in ["golem reborn", "mantid"]):
        natural_ac += 2
    elif any(k in race_str for k in ["cyborg", "draconic", "dragonborn"]):
        natural_ac += 1
    elif "pneumatic endoskeleton" in feats_str:
        natural_ac += 1
    elif "dragon-scale armor" in feats_str:
        natural_ac += 1
        
    # Golem & Biological Grafts AC Bonus
    graft_ac_bonus = 0
    installed_grafts = player_state.get("graft_system", {}).get("installed_grafts", {})
    if isinstance(installed_grafts, dict):
        for g_val in installed_grafts.values():
            if isinstance(g_val, dict):
                g_k = g_val.get("key", "")
                if g_k in ["subdermal_carapace_weave", "basalt_carapace_plating", "wyrm_scale_sheath"]:
                    graft_ac_bonus += 2
            
    ac_pen = dur_pens.get("ac_penalty", 0)
    return max(10, base_ac + armor_bonus + shield_bonus + natural_ac + graft_ac_bonus - ac_pen)



# =====================================================================
# 1-1000 SKILL MASTERY & CANONICAL MILESTONE ENGINE (M1)
# =====================================================================

SKILL_TIER_THRESHOLDS = [
    (1000, "Transcendence", "👑 [Transcendence]"),
    (750,  "Grandmaster",   "⚜️ [Grandmaster]"),
    (500,  "Master",        "🌟 [Master]"),
    (250,  "Adept",         "🔷 [Adept]"),
    (100,  "Journeyman",    "🔶 [Journeyman]"),
    (50,   "Apprentice",    "🟢 [Apprentice]"),
    (1,    "Novice",        "⚪ [Novice]")
]

MILESTONE_THRESHOLDS = [50, 100, 250, 500, 750, 1000]

CANONICAL_MILESTONES = {
    "One-Handed Axes": {
        50: {
            "name": "Hewing Edge",
            "type": "Passive Feat",
            "target_slot": "feats",
            "threshold": 50,
            "skill_name": "One-Handed Axes",
            "tier": "Apprentice",
            "description": "Your strikes find structural seams in armor and hide with ruthless economy of motion.",
            "effect": "+1 to Attack rolls with one-handed axes; attacks deal +2 flat slashing damage and gain 10% critical strike chance against unarmored or light targets."
        },
        100: {
            "name": "Gale Cleave",
            "type": "Active Sword Skill",
            "target_slot": "spells",
            "threshold": 100,
            "skill_name": "One-Handed Axes",
            "tier": "Journeyman",
            "description": "A 2-hit horizontal centrifugal spin that tears through enemy hitboxes with accelerated momentum.",
            "effect": "Action: 2 consecutive axe strikes at +2 to hit, dealing weapon damage + 1d8 slashing and inflicting [Hemorrhage] (3 bleed/turn for 2 turns)."
        },
        250: {
            "name": "Bearded Hook",
            "type": "Passive Feat",
            "target_slot": "feats",
            "threshold": 250,
            "skill_name": "One-Handed Axes",
            "tier": "Adept",
            "description": "Utilize the recessed beard of your axe blade to catch enemy shields, parry weapons, and manipulate hitboxes.",
            "effect": "Disarming or tripping gains Advantage. When an enemy misses in melee, retaliate with an off-balance hook that reduces target AC by -2 for 1 round."
        },
        500: {
            "name": "Executioner's Descent",
            "type": "Active Sword Skill / Finisher",
            "target_slot": "spells",
            "threshold": 500,
            "skill_name": "One-Handed Axes",
            "tier": "Master",
            "description": "A devastating overhead vertical leap-cleave focused entirely on the target's primary structural core or neck joint.",
            "effect": "Action: Leap 15 ft; deals 4d10 + STR slashing damage. Ignores 50% DR. If target is below 25% HP, triggers DC 18 CON save vs instant decapitation."
        },
        750: {
            "name": "Einherjar's Blood-Frenzy",
            "type": "Passive Feat",
            "target_slot": "feats",
            "threshold": 750,
            "skill_name": "One-Handed Axes",
            "tier": "Grandmaster",
            "description": "The spirit of the fallen Nordic vanguard infuses your neural interface; physical pain accelerates attack rate.",
            "effect": "For every 10% max HP lost, gain +1 to hit, +2 damage, and +5% attack speed. Critical hits trigger a free cleave on a nearby enemy within 5 ft."
        },
        1000: {
            "name": "Fenrir's Howling Ruin",
            "type": "Active Sword Skill / Ultimate",
            "target_slot": "spells",
            "threshold": 1000,
            "skill_name": "One-Handed Axes",
            "tier": "Transcendence",
            "description": "A reality-fracturing 5-hit phantom axe combo that shears directly into Cardinal's collision geometry, leaving spatial vacuum tears.",
            "effect": "Action: 5 strikes delivering 10d12 spatial/slashing damage. Bypasses 100% armor/invulnerability. Disables target regeneration for 1 min and creates a 15-ft vortex."
        }
    },
    "Trench Hammers": {
        50: {
            "name": "Concussive Impact",
            "type": "Passive Feat",
            "target_slot": "feats",
            "threshold": 50,
            "skill_name": "Trench Hammers",
            "tier": "Apprentice",
            "description": "Heavy blunt force vibrates through solid protection, transferring trauma directly to interior organs and chassis.",
            "effect": "Blunt attacks ignore 2 points of target AC and deal +2 bludgeoning damage. Successful hits inflict [Disoriented] (-1 on target's next roll)."
        },
        100: {
            "name": "Pneumatic Back-Pick",
            "type": "Active Sword Skill",
            "target_slot": "spells",
            "threshold": 100,
            "skill_name": "Trench Hammers",
            "tier": "Journeyman",
            "description": "Reversing swing direction, drive the diamond-hard armor-piercing raven-bill or pick into a pressurized joint.",
            "effect": "Action: Strike with rear pick at +2 to hit. Deals 2d8 + STR piercing damage, inflicts -3 permanent AC debuff, and forces DC 14 STR save vs Knockdown."
        },
        250: {
            "name": "Kinetic Rebound",
            "type": "Passive Feat",
            "target_slot": "feats",
            "threshold": 250,
            "skill_name": "Trench Hammers",
            "tier": "Adept",
            "description": "Channel massive recoil vibration of dense alloy strikes back into posture and subsequent swings.",
            "effect": "Blocking/parrying absorbs up to STR mod incoming kinetic damage. Next attack within 1 turn deals +1d6 bonus kinetic damage."
        },
        500: {
            "name": "Seismic Fracture",
            "type": "Active Sword Skill",
            "target_slot": "spells",
            "threshold": 500,
            "skill_name": "Trench Hammers",
            "tier": "Master",
            "description": "Slam the weighted head of the hammer into bedrock or pavement, propagating a directional piezoelectric seismic shockwave.",
            "effect": "Action: 20-ft cone shockwave. Entities take 4d8 bludgeoning damage and must pass DC 16 DEX save or be knocked Prone and Stunned for 1 turn. Destroys light cover."
        },
        750: {
            "name": "Colossus Breaker",
            "type": "Passive Feat",
            "target_slot": "feats",
            "threshold": 750,
            "skill_name": "Trench Hammers",
            "tier": "Grandmaster",
            "description": "Heavy blunt impacts deform high-density exo-chassis, boss-grade carapace, and golem-grafts on a molecular level.",
            "effect": "Double damage to structures, constructs, golems, and armored chitin. Crits inflict [Fractured Exoskeleton] (+50% damage from all physical sources for 2 turns)."
        },
        1000: {
            "name": "Mjölnir-Null Singularity",
            "type": "Active Sword Skill / Ultimate",
            "target_slot": "spells",
            "threshold": 1000,
            "skill_name": "Trench Hammers",
            "tier": "Transcendence",
            "description": "Overcharging the depleted-uranium core, bring the hammer down with the crushing gravitational weight of a collapsing star.",
            "effect": "Action: Deals 12d10 dense gravitational bludgeoning damage in a 30-ft radius. Shatters barriers/shields and imposes 100% Gravity Stasis for 3 turns."
        }
    },
    "Field Trapping": {
        50: {
            "name": "Hair-Trigger Rigging",
            "type": "Passive Feat",
            "target_slot": "feats",
            "threshold": 50,
            "skill_name": "Field Trapping",
            "tier": "Apprentice",
            "description": "Rapid deployment techniques allow setting mechanical snares, anchors, and tripwires in seconds.",
            "effect": "Traps deploy 50% faster (deploy tripwires/snares as Bonus Action). +2 to Trap Concealment DC (base DC 14)."
        },
        100: {
            "name": "Serrated Deadfall Snare",
            "type": "Active Technique",
            "target_slot": "spells",
            "threshold": 100,
            "skill_name": "Field Trapping",
            "tier": "Journeyman",
            "description": "Rig a spring-loaded carbon-line snare armed with micro-serrated barbs and weighted tension pins across a transit path.",
            "effect": "Action: 10-ft snare zone. First creature entering must pass DC 15 DEX save or be [Rooted] for 2 turns, taking 2d6 piercing + 3 bleed/turn."
        },
        250: {
            "name": "Pheromone Baiting & Marrow-Grafting",
            "type": "Passive Feat",
            "target_slot": "feats",
            "threshold": 250,
            "skill_name": "Field Trapping",
            "tier": "Adept",
            "description": "Imbue trap triggers with synthesized marrow mash and biological attractants to manipulate monster aggro scripts.",
            "effect": "Beasts and cyber-monsters within 60 ft must pass DC 15 WIS save or be drawn to baited kill-zones. Traps triggered by baited targets gain +100% crit damage."
        },
        500: {
            "name": "Micro-Capacitor Overload Trap",
            "type": "Active Technique",
            "target_slot": "spells",
            "threshold": 500,
            "skill_name": "Field Trapping",
            "tier": "Master",
            "description": "Splice a corroded micro-capacitor and copper wiring into a tension net, discharging high-voltage EMP lightning when tripped.",
            "effect": "Action: Detonates in 15-ft radius for 5d8 Lightning damage, paralyzing biologicals (DC 17 CON save) and disabling golems/automatons for 2 turns."
        },
        750: {
            "name": "Tactical Ambush Mastery",
            "type": "Passive Feat",
            "target_slot": "feats",
            "threshold": 750,
            "skill_name": "Field Trapping",
            "tier": "Grandmaster",
            "description": "Seamlessly integrate multiple trap lines into overlapping crossfire kill-boxes.",
            "effect": "Maintain up to 5 active trap zones simultaneously. Party gains Advantage on attack rolls against trapped enemies, with +3d6 sneak attack damage."
        },
        1000: {
            "name": "Cardinal Net: Spatial Quarantine",
            "type": "Active Technique / Ultimate",
            "target_slot": "spells",
            "threshold": 1000,
            "skill_name": "Field Trapping",
            "tier": "Transcendence",
            "description": "Project a hard-light spatial quarantine grid anchored by anchor pins, sealing an entire battlefield node from the Cardinal network.",
            "effect": "Action: 50-ft containment dome. Prevents teleportation/reinforcements. Enemies take 3d10 neural static damage/turn, lose passive buffs, and cannot evade for 1 min."
        }
    },
    "Cartography": {
        50: {
            "name": "Topographic Awareness",
            "type": "Passive Feat",
            "target_slot": "feats",
            "threshold": 50,
            "skill_name": "Cartography",
            "tier": "Apprentice",
            "description": "Your eye parses elevation gradients, contour lines, and natural choke points with effortless clarity.",
            "effect": "Passive Fog of War reveal radius on Sector 1 Map increased by +25%. Automatically detects low-tier hidden caches and elevation advantage (+1 hit from high ground)."
        },
        100: {
            "name": "Sub-Level Nav-Mesh Bypass",
            "type": "Active Technique",
            "target_slot": "spells",
            "threshold": 100,
            "skill_name": "Cartography",
            "tier": "Journeyman",
            "description": "Analyze glitching geometry to identify decommissioned maintenance ducts, old subway shafts, and unindexed paths.",
            "effect": "Action (Exploration): Reveals hidden connections and bypasses on the map. Party travel through bypasses reduces encounter threat by 50% and avoids Stalker aggro."
        },
        250: {
            "name": "Geodetic Triangulation",
            "type": "Passive Feat",
            "target_slot": "feats",
            "threshold": 250,
            "skill_name": "Cartography",
            "tier": "Adept",
            "description": "Cross-reference satellite telemetry, radio pings, and ancient colonial survey markers to locate valuable anomalies.",
            "effect": "Detects high-yield resource nodes, hidden vendor caches, and Aether-Wells within a 10-grid radius. Grants Advantage on Initiative checks in mapped sectors."
        },
        500: {
            "name": "Chorographer's Sight: Ley-Line Mapping",
            "type": "Active Technique",
            "target_slot": "spells",
            "threshold": 500,
            "skill_name": "Cartography",
            "tier": "Master",
            "description": "Project an arcane aetheric compass overlay that traces subterranean mana-currents and firewall boundaries.",
            "effect": "Action: Reveals dungeon bosses, firewall pylons, and corrupted nodes across the sector. Dispels visual illusions, spatial mirages, and false landmarks within 100 ft."
        },
        750: {
            "name": "Macro-Territory Cartogram",
            "type": "Passive Feat",
            "target_slot": "feats",
            "threshold": 750,
            "skill_name": "Cartography",
            "tier": "Grandmaster",
            "description": "Read macro-geopolitical faction shifts, troop movements, and global glitch-horde migrations before they strike.",
            "effect": "Global Threat Intelligence uplink provides advance warning (1 turn ahead) of roaming elite bosses. Travel across explored nodes consumes 0 supplies; map speed doubled."
        },
        1000: {
            "name": "Architect's Omniscient Overlay",
            "type": "Active Technique / Ultimate",
            "target_slot": "spells",
            "threshold": 1000,
            "skill_name": "Cartography",
            "tier": "Transcendence",
            "description": "Interface directly with Cardinal's root coordinate engine, rendering the entire world map in transparent wireframe.",
            "effect": "Passive & Active: Permanently lifts 100% Fog of War across all sectors. Reveals every hidden cache, backdoor, and enemy coordinate in real time. Can open Phase Portal once/rest."
        }
    }
}

DEFAULT_CORE_SKILLS = {
    "One-Handed Axes": {
        "mastery": 15,
        "tier": "Novice",
        "description": "Mastery over single-handed hatchets, bearded axes, and tactical cleavers.",
        "milestones_unlocked": []
    },
    "Trench Hammers": {
        "mastery": 15,
        "tier": "Novice",
        "description": "Proficiency with war hammers, trench clubs, and heavy blunt implements.",
        "milestones_unlocked": []
    },
    "Field Trapping": {
        "mastery": 10,
        "tier": "Novice",
        "description": "Techniques for rigging mechanical snares, tripwires, and tactical ambush zones.",
        "milestones_unlocked": []
    },
    "Cartography": {
        "mastery": 10,
        "tier": "Novice",
        "description": "Topographical parsing, hazard triangulation, and navigation of fractured sectors.",
        "milestones_unlocked": []
    }
}


def _normalize_skill_key(name: str) -> str:
    """Normalizes skill name for case-insensitive and singular/plural lookup."""
    if not isinstance(name, str):
        return ""
    s = name.strip()
    if s in CANONICAL_MILESTONES:
        return s

    s_clean = s.lower().replace("-", " ").replace("_", " ")
    s_clean = " ".join(s_clean.split())

    for key in CANONICAL_MILESTONES:
        k_clean = key.lower().replace("-", " ").replace("_", " ")
        if s_clean == k_clean:
            return key
        if s_clean.rstrip("s") == k_clean.rstrip("s"):
            return key

    # Semantic keyword mappings
    if "axe" in s_clean:
        return "One-Handed Axes"
    if "hammer" in s_clean:
        return "Trench Hammers"
    if "trap" in s_clean or "snare" in s_clean:
        return "Field Trapping"
    if "cartograph" in s_clean or "map" in s_clean:
        return "Cartography"

    return s


def get_mastery_tier(mastery: int) -> str:
    """Returns tier name corresponding to mastery level (1-1000)."""
    try:
        m = int(mastery)
    except (ValueError, TypeError):
        m = 1
    for threshold, tier_name, _ in SKILL_TIER_THRESHOLDS:
        if m >= threshold:
            return tier_name
    return "Novice"


def get_tier_badge(tier: str) -> str:
    """Returns formatted badge string with emoji for a tier name or mastery level."""
    if isinstance(tier, (int, float)):
        tier_name = get_mastery_tier(int(tier))
    elif isinstance(tier, str):
        clean = tier.strip()
        if clean.isdigit():
            tier_name = get_mastery_tier(int(clean))
        else:
            tier_name = clean
    else:
        tier_name = str(tier)

    for _, name, badge in SKILL_TIER_THRESHOLDS:
        if tier_name.lower() == name.lower():
            return badge

    return f"[{tier_name}]"


def calculate_mastery_gain(current_mastery: int, task_dc: int = 15, base_gain: float = 1.0, success: bool = True, critical: bool = False) -> int:
    """
    Calculates dynamic mastery increment with exponential diminishing returns.
    Formula: round(BaseGain * DifficultyFactor(DC, M) * TierDecay(M) * OutcomeMultiplier)
    DifficultyFactor = max(0.1, DC / (10 + 20 * (M / 1000)))
    TierDecay = exp(-M / 450) * 4.0
    """
    try:
        m_val = int(current_mastery)
    except (ValueError, TypeError):
        m_val = 1

    if m_val >= 1000:
        return 0

    m = max(1, m_val)
    dc = float(task_dc)
    base = max(0.0, float(base_gain))
    if base <= 0.0:
        return 0

    diff_factor = max(0.1, dc / (10.0 + 20.0 * (m / 1000.0)))
    tier_decay = math.exp(-m / 450.0) * 4.0

    if critical:
        outcome_mult = 1.5
    elif success:
        outcome_mult = 1.0
    else:
        outcome_mult = 0.25

    raw_gain = base * diff_factor * tier_decay * outcome_mult
    gain = round(raw_gain)

    if not success:
        gain = min(1, max(0, gain))
    else:
        if dc >= 8.0:
            gain = max(1, gain)
        gain = min(12, max(0, gain))

    gain = min(1000 - m, gain)
    gain = max(0, gain)
    return int(gain)


def get_canonical_milestone(skill_name: str, threshold: int) -> dict | None:
    """
    Retrieves canonical milestone perk dictionary for a skill and threshold.
    Supports case-insensitive and singular/plural normalized lookups.
    """
    norm_key = _normalize_skill_key(skill_name)
    if norm_key not in CANONICAL_MILESTONES:
        return None
    try:
        t_int = int(threshold)
    except (ValueError, TypeError):
        return None
    milestone = CANONICAL_MILESTONES[norm_key].get(t_int)
    if milestone is None:
        return None
    res = dict(milestone)
    res["threshold"] = t_int
    res["skill_name"] = norm_key
    res["tier"] = get_mastery_tier(t_int)
    return res


def check_milestone_unlocks(skill_name: str, old_mastery: int, new_mastery: int, existing_milestones: list = None) -> list[dict]:
    """
    Evaluates whether old_mastery -> new_mastery crossed any milestone thresholds (50, 100, 250, 500, 750, 1000).
    Filters out already unlocked milestones.
    """
    if existing_milestones is None:
        existing_milestones = []

    existing_names = set()
    for item in existing_milestones:
        if isinstance(item, dict) and "name" in item:
            existing_names.add(item["name"].strip().lower())
        elif isinstance(item, str):
            clean = item.split("(")[0].split(":")[0].strip().lower()
            existing_names.add(clean)
            existing_names.add(item.strip().lower())

    unlocked = []
    norm_name = _normalize_skill_key(skill_name)
    display_name = norm_name if norm_name in CANONICAL_MILESTONES else skill_name

    for threshold in MILESTONE_THRESHOLDS:
        if old_mastery < threshold <= new_mastery:
            perk = get_canonical_milestone(display_name, threshold)
            if perk is None:
                tier_name = get_mastery_tier(threshold)
                is_passive = threshold in (50, 250, 750)
                perk_type = "Passive Feat" if is_passive else "Active Technique"
                target_slot = "feats" if is_passive else "spells"
                perk = {
                    "name": f"{display_name}: {tier_name} Breakthrough",
                    "type": perk_type,
                    "target_slot": target_slot,
                    "threshold": threshold,
                    "skill_name": display_name,
                    "tier": tier_name,
                    "description": f"Mastery breakthrough in {display_name} at the {tier_name} tier ({threshold}).",
                    "effect": f"Grants specialized {tier_name} proficiency and bonuses to {display_name} checks.",
                    "is_procedural": True
                }

            perk_name = perk["name"]
            if perk_name.strip().lower() not in existing_names:
                unlocked.append(perk)
                existing_names.add(perk_name.strip().lower())

    return unlocked


def _is_perk_in_slot(perk_name: str, slot_list: list) -> bool:
    """Checks whether perk_name is already present in a feats or spells list."""
    if not isinstance(slot_list, list):
        return False
    target = perk_name.strip().lower()
    for item in slot_list:
        if isinstance(item, dict):
            if item.get("name", "").strip().lower() == target:
                return True
        elif isinstance(item, str):
            clean = item.split(":")[0].split("(")[0].strip().lower()
            if clean == target:
                return True
    return False


def update_skill_mastery(player_state: dict, skill_name: str, gain_or_dc: int = 1, is_dc: bool = False, desc: str = "", critical: bool = False, **kwargs) -> dict:
    """
    Updates player skill mastery, computes tiers, detects milestone threshold crossings,
    and auto-appends newly unlocked perks to player feats or spells.
    """
    if not isinstance(player_state, dict):
        return {}

    # Handle kwarg aliases
    if kwargs.get("task_dc") is not None:
        is_dc = True
        gain_or_dc = kwargs["task_dc"]
    if kwargs.get("mastery_change") is not None and not is_dc:
        gain_or_dc = kwargs["mastery_change"]
    if kwargs.get("amount") is not None and not is_dc:
        gain_or_dc = kwargs["amount"]
    if kwargs.get("description"):
        desc = kwargs["description"]
    elif kwargs.get("desc"):
        desc = kwargs["desc"]

    # Ensure structured skills container
    if "skills" not in player_state or not isinstance(player_state["skills"], dict):
        if not player_state:
            player_state["skills"] = {}
        else:
            migrated = migrate_player_skills(player_state)
            if isinstance(player_state.get("skills"), dict):
                pass
            elif isinstance(migrated, dict) and "skills" in migrated and isinstance(migrated["skills"], dict):
                player_state["skills"] = migrated["skills"]
            elif isinstance(migrated, dict):
                player_state["skills"] = migrated
            else:
                player_state["skills"] = {}

    if not isinstance(player_state.get("feats"), list):
        player_state["feats"] = []
    if not isinstance(player_state.get("spells"), list):
        player_state["spells"] = []

    skills_dict = player_state["skills"]

    # Target key resolution
    target_key = skill_name
    if target_key not in skills_dict:
        # Try case-insensitive matching
        for k in skills_dict:
            if k.lower() == skill_name.lower():
                target_key = k
                break
        else:
            # Try canonical normalization
            norm = _normalize_skill_key(skill_name)
            if norm in skills_dict:
                target_key = norm
            elif norm in CANONICAL_MILESTONES:
                target_key = norm

    # Initialize skill if not present
    if target_key not in skills_dict:
        norm_key = _normalize_skill_key(target_key)
        default_desc = DEFAULT_CORE_SKILLS.get(norm_key, {}).get("description") or f"Proficiency in {target_key}."
        skills_dict[target_key] = {
            "mastery": 1,
            "tier": "Novice",
            "description": desc or default_desc,
            "milestones_unlocked": []
        }

    skill_entry = skills_dict[target_key]
    if not isinstance(skill_entry, dict):
        if isinstance(skill_entry, (int, float)):
            try:
                mastery_val = int(skill_entry)
            except (ValueError, TypeError):
                mastery_val = 1
        elif isinstance(skill_entry, str):
            try:
                mastery_val = int(skill_entry)
            except (ValueError, TypeError):
                mastery_val = 1
        else:
            mastery_val = 1
        mastery_val = max(1, min(1000, mastery_val))
        skill_entry = {
            "mastery": mastery_val,
            "tier": get_mastery_tier(mastery_val),
            "description": desc or f"Proficiency in {target_key}.",
            "milestones_unlocked": []
        }
        skills_dict[target_key] = skill_entry

    raw_old_m = skill_entry.get("mastery", 1)
    try:
        old_mastery = int(raw_old_m) if raw_old_m is not None else 1
    except (ValueError, TypeError):
        old_mastery = 1
    old_mastery = max(1, min(1000, old_mastery))
    old_tier = skill_entry.get("tier", get_mastery_tier(old_mastery))
    raw_existing_milestones = skill_entry.get("milestones_unlocked")
    if not isinstance(raw_existing_milestones, list):
        if isinstance(raw_existing_milestones, (tuple, set)):
            existing_milestones = list(raw_existing_milestones)
        elif raw_existing_milestones is None:
            existing_milestones = []
        else:
            existing_milestones = [str(raw_existing_milestones)]
        skill_entry["milestones_unlocked"] = existing_milestones
    else:
        existing_milestones = raw_existing_milestones

    # Calculate gain delta
    if is_dc:
        delta = calculate_mastery_gain(old_mastery, task_dc=gain_or_dc, success=True, critical=critical)
    else:
        delta = int(gain_or_dc)

    new_mastery = min(1000, max(1, old_mastery + delta))
    new_tier = get_mastery_tier(new_mastery)

    skill_entry["mastery"] = new_mastery
    skill_entry["tier"] = new_tier
    if desc:
        skill_entry["description"] = desc

    # Check for unlocked milestones
    unlocked = check_milestone_unlocks(target_key, old_mastery, new_mastery, existing_milestones)
    for m in unlocked:
        perk_name = m["name"]
        if perk_name not in existing_milestones:
            existing_milestones.append(perk_name)

        target_slot = m.get("target_slot", "feats")
        if target_slot not in player_state or not isinstance(player_state[target_slot], list):
            player_state[target_slot] = []

        if not _is_perk_in_slot(perk_name, player_state[target_slot]):
            player_state[target_slot].append(perk_name)

    return {
        "skill_name": target_key,
        "old_mastery": old_mastery,
        "new_mastery": new_mastery,
        "gain": delta,
        "old_tier": old_tier,
        "new_tier": new_tier,
        "tier_changed": (old_tier != new_tier),
        "unlocked_milestones": unlocked,
        "milestones_unlocked": [m["name"] for m in unlocked],
        "milestones_triggered": unlocked,
        "skill_data": skill_entry
    }


def migrate_player_skills(player_state: dict) -> dict:
    """
    Ensures player skills conform to canonical schema:
    player["skills"][skill_name] = {
        "mastery": int,
        "tier": str,
        "description": str,
        "milestones_unlocked": list
    }
    Backfills milestone perks into player feats/spells.
    """
    if not isinstance(player_state, (dict, list)):
        return player_state

    # Determine whether player_state is character sheet or bare skills dict/list
    is_full_player = isinstance(player_state, dict) and (
        "skills" in player_state or
        any(k in player_state for k in ("name", "stats", "equipped", "hp", "inventory", "col"))
    )

    if is_full_player:
        player_state.setdefault("feats", [])
        player_state.setdefault("spells", [])
        if not isinstance(player_state["feats"], list):
            player_state["feats"] = []
        if not isinstance(player_state["spells"], list):
            player_state["spells"] = []

        raw_skills = player_state.get("skills")
    else:
        raw_skills = player_state

    new_skills = {}

    if not raw_skills or not isinstance(raw_skills, (dict, list)):
        # Seed default core skills for fresh or empty skill list, or invalid schema
        for s_name, s_def in DEFAULT_CORE_SKILLS.items():
            new_skills[s_name] = {
                "mastery": s_def["mastery"],
                "tier": s_def["tier"],
                "description": s_def["description"],
                "milestones_unlocked": list(s_def["milestones_unlocked"])
            }
    elif isinstance(raw_skills, list):
        for item in raw_skills:
            if isinstance(item, str):
                if ":" in item:
                    parts = item.split(":", 1)
                    name = parts[0].strip()
                    desc = parts[1].strip()
                else:
                    name = item.strip()
                    norm_k = _normalize_skill_key(name)
                    desc = DEFAULT_CORE_SKILLS.get(norm_k, {}).get("description") or f"Proficiency in {name}."

                norm_key = _normalize_skill_key(name)
                canonical_name = norm_key if norm_key in CANONICAL_MILESTONES else name
                new_skills[canonical_name] = {
                    "mastery": 1,
                    "tier": "Novice",
                    "description": desc,
                    "milestones_unlocked": []
                }
            elif isinstance(item, dict):
                name = item.get("name") or item.get("skill_name") or "Unknown Skill"
                norm_key = _normalize_skill_key(name)
                canonical_name = norm_key if norm_key in CANONICAL_MILESTONES else name
                raw_m = item.get("mastery", 1)
                try:
                    mastery = int(raw_m) if raw_m is not None else 1
                except (ValueError, TypeError):
                    mastery = 1
                mastery = max(1, min(1000, mastery))
                raw_ms = item.get("milestones_unlocked")
                milestones = list(raw_ms) if isinstance(raw_ms, (list, tuple, set)) else []
                new_skills[canonical_name] = {
                    "mastery": mastery,
                    "tier": get_mastery_tier(mastery),
                    "description": item.get("description") or DEFAULT_CORE_SKILLS.get(norm_key, {}).get("description") or f"Proficiency in {canonical_name}.",
                    "milestones_unlocked": milestones
                }
    elif isinstance(raw_skills, dict):
        for name, data in raw_skills.items():
            norm_key = _normalize_skill_key(name)
            canonical_name = norm_key if norm_key in CANONICAL_MILESTONES else name

            if isinstance(data, (int, float)):
                try:
                    mastery = int(data)
                except (ValueError, TypeError):
                    mastery = 1
                desc = DEFAULT_CORE_SKILLS.get(norm_key, {}).get("description") or f"Proficiency in {canonical_name}."
                milestones = []
            elif isinstance(data, dict):
                raw_m = data.get("mastery", 1)
                try:
                    mastery = int(raw_m) if raw_m is not None else 1
                except (ValueError, TypeError):
                    mastery = 1
                desc = data.get("description") or DEFAULT_CORE_SKILLS.get(norm_key, {}).get("description") or f"Proficiency in {canonical_name}."
                raw_ms = data.get("milestones_unlocked")
                milestones = list(raw_ms) if isinstance(raw_ms, (list, tuple, set)) else []
            elif isinstance(data, str):
                try:
                    mastery = int(data)
                except (ValueError, TypeError):
                    mastery = 1
                desc = DEFAULT_CORE_SKILLS.get(norm_key, {}).get("description") or f"Proficiency in {canonical_name}."
                milestones = []
            else:
                raw_m = data
                try:
                    mastery = int(raw_m) if raw_m is not None else 1
                except (ValueError, TypeError):
                    mastery = 1
                desc = f"Proficiency in {canonical_name}."
                milestones = []

            mastery = max(1, min(1000, mastery))
            new_skills[canonical_name] = {
                "mastery": mastery,
                "tier": get_mastery_tier(mastery),
                "description": desc,
                "milestones_unlocked": milestones
            }

    # Backfill milestone unlocks for any thresholds <= mastery
    for s_name, s_data in new_skills.items():
        m_level = s_data["mastery"]
        s_milestones = s_data["milestones_unlocked"]
        for threshold in MILESTONE_THRESHOLDS:
            if m_level >= threshold:
                perk = get_canonical_milestone(s_name, threshold)
                if perk:
                    perk_name = perk["name"]
                    if perk_name not in s_milestones:
                        s_milestones.append(perk_name)

                    if is_full_player:
                        target_slot = perk.get("target_slot", "feats")
                        if target_slot not in player_state or not isinstance(player_state[target_slot], list):
                            player_state[target_slot] = []
                        if not _is_perk_in_slot(perk_name, player_state[target_slot]):
                            player_state[target_slot].append(perk_name)

    if is_full_player:
        player_state["skills"] = new_skills
        return player_state
    else:
        return new_skills


# ==============================================================================
# ⚔️ PHASE B2: BASE CLASS FEATS TREE & ASYMMETRIC COMBAT RESOURCE ENGINE
# ==============================================================================

# --- TIER 1 CLASS FEATS TREES (Levels 1, 3, 6, 10) ---
CLASS_FEATS_TREE = {
    "warrior": {
        "title": "Warrior (Frontline Anchor)",
        "resource": {"name": "Poise & Threat", "max": 100, "start": 0, "type": "poise"},
        "level_1": [
            "Shield Wall Stance (Active): Enter fortified defensive stance; gain +3 AC and Advantage on CON saves, movement halved.",
            "Taunting War-Cry (Active): Spend 20 Poise to force enemies within 30ft to make a WIS save (DC 13) or focus attacks on you."
        ],
        "level_3": [
            {"id": "A", "name": "Unyielding Mass", "type": "Passive", "desc": "Max Poise increased by +25. You cannot be knocked down or moved against your will by creatures equal or smaller."},
            {"id": "B", "name": "Retaliatory Bulwark", "type": "Passive", "desc": "Successfully blocking an attack reflects 1d6 + CON mod kinetic damage back to attacker."},
            {"id": "C", "name": "Inspiring Bastion", "type": "Active", "desc": "Spend 30 Poise to rally companions within 30ft; grants +10 temporary HP for 3 turns."}
        ],
        "level_6": [
            {"id": "A", "name": "Guard Break", "type": "Active", "desc": "Spend 40 Poise on melee strike to shatter enemy defenses, reducing target AC by -3 for 2 turns."},
            {"id": "B", "name": "Bodyguard Intercept", "type": "Reaction", "desc": "When an adjacent ally is struck, instantly swap positions and absorb the hit using your Armor Class."},
            {"id": "C", "name": "Seismic Tremor", "type": "Active", "desc": "Slam weapon into ground, dealing 2d8 bludgeoning damage and knocking down enemies in 10ft."}
        ],
        "level_10": [
            {"id": "A", "name": "Unbreakable Bastion", "type": "Passive", "desc": "Gain 10% resistance to all physical damage. Max Poise increased to 125."},
            {"id": "B", "name": "Colossus Cleave", "type": "Active", "desc": "Spend 50 Poise to swing in a 180-degree arc, dealing weapon damage + 2d10 to all adjacent foes."},
            {"id": "C", "name": "Battlefield Commander", "type": "Active", "desc": "Spend 40 Poise to command all party members to strike simultaneously with Advantage."}
        ]
    },
    "mage": {
        "title": "Mage (Aether-Weaver)",
        "resource": {"name": "Aetheric Flux", "max": 50, "start": 50, "type": "flux"},
        "level_1": [
            "Arcane Ward (Active): Conjure aetheric barrier absorbing up to 25 + (5 x Lvl) damage.",
            "Aetheric Dart (Active): Fire concentrated force bolt dealing 1d8 + INT mod force damage (costs 5 Flux)."
        ],
        "level_3": [
            {"id": "A", "name": "Mana Forking", "type": "Passive", "desc": "Single-target offensive spells have a 35% chance to fork and strike a second adjacent target for half damage."},
            {"id": "B", "name": "Leyline Conduit", "type": "Passive", "desc": "Standing within 15ft of an aether conduit doubles Flux regeneration to +20 Flux/turn."},
            {"id": "C", "name": "Kinetic Repulsion Pulse", "type": "Reaction", "desc": "When an enemy enters melee reach, spend 15 Flux to trigger a shockwave pushing them back 15ft."}
        ],
        "level_6": [
            {"id": "A", "name": "Overcharge Singularity", "type": "Active", "desc": "Spend 40 Flux to unleash a localized gravity vortex dealing 3d10 force damage in 15ft radius."},
            {"id": "B", "name": "Dimensional Blink", "type": "Active", "desc": "Spend 20 Flux to instantaneously teleport up to 30ft to an unoccupied space in line of sight."},
            {"id": "C", "name": "Crystalline Rail-Lance", "type": "Active", "desc": "Spend 25 Flux to fire a crystalline beam piercing up to 3 enemies in a straight line."}
        ],
        "level_10": [
            {"id": "A", "name": "Arcane Conduit Overdrive", "type": "Passive", "desc": "Spells deal 20% increased force/elemental damage when cast at or above 30 Flux."},
            {"id": "B", "name": "Event Horizon", "type": "Active", "desc": "Spend 45 Flux to create a gravitational collapse that pulls enemies in 30ft and immobilizes them."},
            {"id": "C", "name": "Aetheric Aegis", "type": "Active", "desc": "Spend 35 Flux to grant all party members a 30 HP protective energy barrier for 3 turns."}
        ]
    },
    "cleric": {
        "title": "Cleric (Spire Templar)",
        "resource": {"name": "Devotion & Grace", "max": 100, "start": 50, "type": "devotion"},
        "level_1": [
            "Sanctified Ward (Active Stance): Project 15ft aura; allies within gain +2 to saving throws and +1 AC.",
            "Purifying Grace (Active): Spend 25 Devotion to heal ally for 2d8 + WIS mod and cleanse one bleed/poison."
        ],
        "level_3": [
            {"id": "A", "name": "Consecrated Smite", "type": "Passive", "desc": "Melee strikes generate +10 Devotion and deal +1d6 radiant damage against corrupt/undead foes."},
            {"id": "B", "name": "Martyr's Exchange", "type": "Reaction", "desc": "When an ally in 30ft takes lethal damage, spend 30 Devotion to absorb 50% onto yourself."},
            {"id": "C", "name": "Cleansing Radiance", "type": "Active", "desc": "Spend 35 Devotion to emit a pulse that blinds adjacent enemies and grants allies +15 temp HP."}
        ],
        "level_6": [
            {"id": "A", "name": "Aegis of the Spire", "type": "Active", "desc": "Spend 50 Devotion to project a golden dome for 2 turns preventing all enemy projectile entry."},
            {"id": "B", "name": "Rebuke the Corrupt", "type": "Active", "desc": "Unleash pillar of light dealing 3d8 + WIS mod radiant damage and knocking down aberrant targets."},
            {"id": "C", "name": "Divine Resurgence", "type": "Passive", "desc": "Once per day, when HP drops to 0, instantly revive at 25% HP and emit radial heal pulse."}
        ],
        "level_10": [
            {"id": "A", "name": "Wrath of the Heavens", "type": "Active", "desc": "Spend 50 Devotion to call down radiant storm dealing 4d8 radiant damage and applying Blindness."},
            {"id": "B", "name": "Hand of Salvation", "type": "Active", "desc": "Spend 45 Devotion to fully heal an ally below 25% HP and grant them Immunity to all damage for 1 turn."},
            {"id": "C", "name": "Aura of the Incorruptible", "type": "Passive", "desc": "All party members within 30ft gain +3 to all saving throws and immune to Fear and Charm."}
        ]
    },
    "thief": {
        "title": "Thief (Shadow Infiltrator)",
        "resource": {"name": "Momentum Dice", "max": 5, "start": 1, "type": "momentum"},
        "level_1": [
            "Shadow Footwork (Active Stance): Gain +2 to Dodge DC and ignore terrain movement penalties.",
            "Serrated Backstab (Active): Spend 1 Momentum to strike from stealth or flank for +2d6 precision bleed damage."
        ],
        "level_3": [
            {"id": "A", "name": "Fluid Evasion", "type": "Passive", "desc": "Whenever an enemy misses an attack against you, immediately generate +1 Momentum die."},
            {"id": "B", "name": "Pocket Blind", "type": "Active", "desc": "Spend 1 Momentum die to blind target eyes; target suffers Disadvantage on attack rolls for 2 turns."},
            {"id": "C", "name": "Opportunistic Sprint", "type": "Active", "desc": "Spend 1 Momentum die to take Dash and Disengage simultaneously as a free bonus action."}
        ],
        "level_6": [
            {"id": "A", "name": "Shadow-Vanish", "type": "Active", "desc": "Spend 2 Momentum dice to drop smoke pellet and re-enter full Stealth in plain sight."},
            {"id": "B", "name": "Severing Tendon", "type": "Active", "desc": "Spend 2 Momentum on critical strike to reduce target movement to 0 and disable reaction attacks."},
            {"id": "C", "name": "Cunning Double-Strike", "type": "Passive", "desc": "Dual-wielding off-hand strikes have a 50% chance not to consume an action when spending Momentum."}
        ],
        "level_10": [
            {"id": "A", "name": "Death Lotus", "type": "Active", "desc": "Spend 3 Momentum to teleport between up to 4 enemies in 30ft, striking each for critical damage."},
            {"id": "B", "name": "Phase Shadow", "type": "Passive", "desc": "When dropping below 30% HP, automatically vanish into shadow for 2 turns without taking damage."},
            {"id": "C", "name": "Expose Fatal Flaw", "type": "Active", "desc": "Spend 2 Momentum to analyze target; all party members deal +50% critical damage to target for 2 turns."}
        ]
    },
    "ranger": {
        "title": "Ranger (Wilderness Marksman)",
        "resource": {"name": "Focus & Vantage", "max": 5, "start": 3, "type": "focus"},
        "level_1": [
            "Hunter's Mark (Active): Mark target within 60ft as quarry; attacks deal +1d6 damage and ignore cover.",
            "Deadeye Aim (Passive): Ranged attacks ignore cover and gain +2 to hit when standing still."
        ],
        "level_3": [
            {"id": "A", "name": "Predator's Camouflage", "type": "Passive", "desc": "Advantage on Stealth in wild/ruined biomes; first shot from stealth does not break cover."},
            {"id": "B", "name": "Crippling Pin", "type": "Active", "desc": "Spend 1 Focus charge to shoot enemy servo/leg; target movement reduced to 0 for 1 turn."},
            {"id": "C", "name": "Quick-Step Disengage", "type": "Reaction", "desc": "When enemy closes to melee, spend 1 Focus to vault backward 15ft without provoking attacks of opportunity."}
        ],
        "level_6": [
            {"id": "A", "name": "Culling Shot", "type": "Active", "desc": "Spend 2 Focus charges to fire execution shot; deals triple damage against targets below 30% HP."},
            {"id": "B", "name": "Shrapnel Rain", "type": "Active", "desc": "Spend 2 Focus charges to blanket 20ft area with explosive shrapnel dealing 3d6 bleed damage."},
            {"id": "C", "name": "Wild Instincts", "type": "Passive", "desc": "You can never be surprised in combat, and automatically roll with Advantage on Initiative checks."}
        ],
        "level_10": [
            {"id": "A", "name": "Apex Predator", "type": "Passive", "desc": "Attacks against quarry expand critical threat range to 18-20 and deal x3 critical damage."},
            {"id": "B", "name": "Ballistic Barrage", "type": "Active", "desc": "Spend 3 Focus charges to fire a stream of 5 piercing arrows into a single target."},
            {"id": "C", "name": "Perimeter Lockdown", "type": "Active", "desc": "Spend 2 Focus charges to deploy a network of concealed trip-mines covering 40ft."}
        ]
    },
    "engineer": {
        "title": "Engineer / Artificer",
        "resource": {"name": "Heat & Overclock", "max": 100, "start": 0, "type": "heat"},
        "level_1": [
            "Deploy Sentry Turret (Active): Deploy kinetic/shock turret that fires 1d6 damage each turn (builds 20 Heat).",
            "Vent Overclock (Active): Vent Heat in 10ft frontal cone dealing damage equal to 50% of vented Heat."
        ],
        "level_3": [
            {"id": "A", "name": "Conductive Wiretap", "type": "Passive", "desc": "Hacking enemy terminal/construct reveals sector stats and grants +2 to hit mechanized foes."},
            {"id": "B", "name": "Heat-Sink Plating", "type": "Passive", "desc": "While Heat is above 50%, armor gains +3 AC and radiates 1d6 fire damage to melee attackers."},
            {"id": "C", "name": "Overclock Surge", "type": "Active", "desc": "Spend 40 Heat to take an additional Standard Action on your current combat turn."}
        ],
        "level_6": [
            {"id": "A", "name": "Automated Decoy Drones", "type": "Active", "desc": "Deploy 2 holographic decoy drones that draw enemy attacks away from party for 2 turns."},
            {"id": "B", "name": "EMP Shock-Discharge", "type": "Active", "desc": "Spend 50 Heat to discharge EMP burst that stuns constructs for 1 turn and disables energy weapons."},
            {"id": "C", "name": "Recursive Logic Virus", "type": "Active", "desc": "Upload corrupt logic into cybernetic/golem enemy, forcing it to attack nearest ally for 1 turn."}
        ],
        "level_10": [
            {"id": "A", "name": "Automated Siege Golem", "type": "Active", "desc": "Deploy heavy mechanized combat turret with 60 HP that taunts enemies and fires flak cannons."},
            {"id": "B", "name": "Core Melt Downcharge", "type": "Active", "desc": "Vent 100% Heat into tactical blast dealing 5d10 thermal/kinetic damage in 20ft radius."},
            {"id": "C", "name": "Nanite Patch Field", "type": "Passive", "desc": "Deploying gadgets or venting heat automatically repairs party armor and restores 10 HP."}
        ]
    },
    "psion": {
        "title": "Psion / Phrenic",
        "resource": {"name": "Psi-Strain", "max": 100, "start": 0, "type": "strain"},
        "level_1": [
            "Kinetic Repulsion Barrier (Active Stance): Deflect projectiles (+3 AC vs ranged), builds +10% Strain/turn.",
            "Mind Spike (Active): Unleash psychic jolt dealing 1d10 + INT mod damage, bypassing armor (builds +15% Strain)."
        ],
        "level_3": [
            {"id": "A", "name": "High-Strain Resonance", "type": "Passive", "desc": "While Psi-Strain is above 50%, all psychic abilities deal +25% bonus damage and +2 save DC."},
            {"id": "B", "name": "Telekinetic Toss", "type": "Active", "desc": "Hurl an enemy or heavy terrain object up to 30ft for 2d8 bludgeoning damage (builds +20% Strain)."},
            {"id": "C", "name": "Neural Dampening", "type": "Reaction", "desc": "When an ally suffers mental debuff, charm, or fear, spend 15% Strain to negate it instantly."}
        ],
        "level_6": [
            {"id": "A", "name": "Psychokinetic Implosion", "type": "Active", "desc": "Compress atmosphere in 15ft sphere, crushing for 3d10 force damage and pulling foes together (+35% Strain)."},
            {"id": "B", "name": "Neural Overwrite", "type": "Active", "desc": "Invade organic enemy motor cortex; contested WIS check to control target action for 1 turn (+40% Strain)."},
            {"id": "C", "name": "Subconscious Flush", "type": "Active", "desc": "Once per combat, instantly vent all Psi-Strain to 0%, deafening adjacent foes for 1 turn."}
        ],
        "level_10": [
            {"id": "A", "name": "Mind Over Matter", "type": "Passive", "desc": "You can use INT modifier in place of STR or DEX for attack rolls, physical saves, and AC."},
            {"id": "B", "name": "Psionic Cataclysm", "type": "Active", "desc": "Suffer 40% Strain to detonate psychic shockwave dealing 5d8 force damage and stunning foes in 25ft."},
            {"id": "C", "name": "Neural Puppet Master", "type": "Active", "desc": "Suffer 35% Strain to seize complete control of an enemy commander or elite construct for 2 full turns."}
        ]
    },
    "pathless": {
        "title": "Pathless (Freeform Anomaly)",
        "resource": {"name": "Anomaly Resonance", "max": 100, "start": 0, "type": "resonance"},
        "level_1": [
            "Adaptive Weapon Mastery (Passive): Equip and dual-wield any weapon combination without off-hand penalties.",
            "Unshackled Potential (Passive): Can choose any 1 starting ability from any of the 7 anchor classes."
        ],
        "level_3": [
            {"id": "A", "name": "Cross-Discipline Synergy", "type": "Passive", "desc": "Executing a melee attack grants +2 to hit and +1d6 damage on your next ranged or magical action."},
            {"id": "B", "name": "Adaptive Will", "type": "Passive", "desc": "Max Anomaly Resonance increased to 125. Reroll one failed saving throw per combat encounter."},
            {"id": "C", "name": "System Glitch Step", "type": "Active", "desc": "Spend 25 Resonance to phase-shift through collision for 1 turn, passing through obstacles."}
        ],
        "level_6": [
            {"id": "A", "name": "Stolen Doctrine", "type": "Passive", "desc": "Choose any 1 Level 3 or Level 6 Class Feat from any of the seven anchor classes."},
            {"id": "B", "name": "Glitched Blade Edge", "type": "Active", "desc": "Spend 40 Resonance to coat weapons in null-void data; attacks bypass physical AC for 1 turn."},
            {"id": "C", "name": "Dual-Core Overclock", "type": "Active", "desc": "Spend 50 Resonance to gain an extra Standard Action this turn."}
        ],
        "level_10": [
            {"id": "A", "name": "Sovereign Glitch", "type": "Passive", "desc": "Equip weapons and armor of any grade or category without stat prerequisites or penalties."},
            {"id": "B", "name": "Dimensional Tear", "type": "Active", "desc": "Spend 50 Resonance to slash reality, dealing 4d12 null-void damage that bypasses all defenses."},
            {"id": "C", "name": "Limitless Resonance", "type": "Passive", "desc": "Max Resonance increased to 150. Generating Resonance restores 5% of max HP per trigger."}
        ]
    }
}

# Legacy alias mappings
CLASS_FEATS_TREE["vanguard"] = CLASS_FEATS_TREE["warrior"]
CLASS_FEATS_TREE["magi_saboteur"] = CLASS_FEATS_TREE["engineer"]
CLASS_FEATS_TREE["aether_slinger"] = CLASS_FEATS_TREE["mage"]
CLASS_FEATS_TREE["wilderness_ranger"] = CLASS_FEATS_TREE["ranger"]

# --- ASYMMETRIC COMBAT RESOURCE ENGINE ---

def normalize_class_key(class_str):
    """Maps class titles or raw strings to canonical dictionary keys."""
    if not class_str or not isinstance(class_str, str):
        return "pathless"
    c_low = class_str.lower()
    if "warrior" in c_low or "vanguard" in c_low:
        return "warrior"
    if "cleric" in c_low or "templar" in c_low:
        return "cleric"
    if "thief" in c_low or "rogue" in c_low or "infiltrator" in c_low:
        return "thief"
    if "ranger" in c_low or "hunter" in c_low or "marksman" in c_low:
        return "ranger"
    if "engineer" in c_low or "artificer" in c_low or "saboteur" in c_low:
        return "engineer"
    if "psion" in c_low or "phrenic" in c_low or "mentalist" in c_low:
        return "psion"
    if "mage" in c_low or "slinger" in c_low or "arcanist" in c_low or "wizard" in c_low:
        return "mage"
    return "pathless"

def initialize_combat_resource(player):
    """
    Ensures player dictionary has a valid combat_resource sub-dictionary.
    Initializes resource according to player's class doctrine.
    """
    if "combat_resource" not in player or not isinstance(player["combat_resource"], dict) or "name" not in player["combat_resource"]:
        c_key = normalize_class_key(player.get("class", "pathless"))
        c_data = CLASS_FEATS_TREE.get(c_key, CLASS_FEATS_TREE["pathless"])
        r_info = c_data["resource"]
        player["combat_resource"] = {
            "name": r_info["name"],
            "current": r_info["start"],
            "max": r_info["max"],
            "type": r_info["type"]
        }
    return player["combat_resource"]

def update_combat_resource(player, delta):
    """
    Adjusts the player's combat resource by delta (positive or negative).
    Clamps within bounds (0 to max). For psion/strain, handles push-your-luck warning.
    Returns transaction summary dict.
    """
    res = initialize_combat_resource(player)
    old_val = res.get("current", 0)
    max_val = res.get("max", 100)
    r_type = res.get("type", "generic")
    
    new_val = max(0, min(max_val, old_val + delta))
    res["current"] = new_val
    
    warning = None
    if r_type == "strain":
        if new_val >= 100:
            warning = "CRITICAL PSYCHIC OVERLOAD! Backlash triggers self-stun and nosebleed trauma!"
        elif new_val >= 75:
            warning = "WARNING: Cognitive strain approaching dangerous threshold (75%+)."
    elif r_type == "heat":
        if new_val >= 100:
            warning = "OVERHEAT DETECTED! Chassis venting required to prevent burn damage!"
            
    return {
        "name": res["name"],
        "old": old_val,
        "new": new_val,
        "max": max_val,
        "delta": delta,
        "warning": warning
    }

def get_combat_resource_display(player):
    """Returns formatted display info for HUD rendering."""
    res = initialize_combat_resource(player)
    cur = res.get("current", 0)
    m = res.get("max", 100)
    pct = round(cur / m, 2) if m > 0 else 0.0
    r_type = res.get("type", "generic")
    
    if r_type == "strain":
        display_str = f"{cur}% / {m}% Strain"
    elif r_type in ["momentum", "focus"]:
        display_str = f"{cur} / {m} Charges"
    else:
        display_str = f"{cur} / {m}"
        
    return {
        "name": res.get("name", "Combat Resource"),
        "current": cur,
        "max": m,
        "percentage": pct,
        "type": r_type,
        "display": display_str
    }

# --- ARCHETYPE HP SCALING & LEVEL PROGRESSION ---

ARCHETYPE_HP_GROWTH = {
    "warrior": 35,
    "cleric": 28,
    "engineer": 28,
    "ranger": 28,
    "thief": 24,
    "psion": 24,
    "mage": 20,
    "pathless": 25
}

def get_archetype_hp_growth(player_class):
    """Calculates base HP growth per level for the character's class."""
    k = normalize_class_key(player_class)
    return ARCHETYPE_HP_GROWTH.get(k, 25)

def apply_level_up(player, chosen_feat=None, stat_allocations=None):
    """
    Levels up the character:
    - Increments level
    - Adds archetype HP (+ CON mod)
    - Adds 2 free attribute points (or applies allocated points)
    - Appends chosen_feat to feats if provided
    """
    player["level"] = player.get("level", 1) + 1
    con = player.get("stats", {}).get("CON", 10)
    con_mod = (con - 10) // 2
    
    hp_gain = get_archetype_hp_growth(player.get("class", "pathless")) + con_mod
    player["max_hp"] = player.get("max_hp", 100) + hp_gain
    player["hp"] = player.get("hp", 100) + hp_gain
    
    # Free attribute points
    player["free_attribute_points"] = player.get("free_attribute_points", 0) + 2
    
    if stat_allocations and isinstance(stat_allocations, dict):
        allocate_attribute_points(player, stat_allocations)
        
    if chosen_feat:
        if "feats" not in player or not isinstance(player["feats"], list):
            player["feats"] = []
        feat_entry = chosen_feat if isinstance(chosen_feat, str) else chosen_feat.get("name", str(chosen_feat))
        if feat_entry not in player["feats"]:
            player["feats"].append(feat_entry)
            
    return {
        "new_level": player["level"],
        "hp_gain": hp_gain,
        "max_hp": player["max_hp"],
        "free_points": player["free_attribute_points"]
    }

def allocate_attribute_points(player, allocations):
    """
    Spends free attribute points into STR, DEX, CON, INT, WIS, CHA.
    allocations = {"STR": 1, "CON": 1}
    """
    avail = player.get("free_attribute_points", 0)
    total_requested = sum(v for v in allocations.values() if isinstance(v, int) and v > 0)
    if total_requested > avail:
        raise ValueError(f"Cannot allocate {total_requested} points; only {avail} free points available.")
        
    stats = player.setdefault("stats", {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10})
    for s_name, pts in allocations.items():
        if pts > 0 and s_name in stats:
            stats[s_name] += pts
            
    player["free_attribute_points"] = avail - total_requested
    return stats

# --- HARMONIZED DUAL-GATE EVOLUTION ENGINE ---

def check_evolution_eligibility(player):
    """
    Evaluates whether player meets the Harmonized Dual-Gate requirements for Class Evolution:
    - Tier 2 (Level 10): Level >= 10, Sector 1 Boss defeated, at least 1 skill at Journeyman (100+).
    - Tier 3 (Level 25): Level >= 25, Regional Boss defeated, at least 1 skill at Adept/Master (350+).
    """
    lvl = player.get("level", 1)
    skills = player.get("skills", {})
    bosses = player.get("bosses_defeated", [])
    if isinstance(bosses, str):
        bosses = [bosses]
        
    # Check max skill mastery
    max_mastery = 0
    top_skill = None
    if isinstance(skills, dict):
        for s_name, s_data in skills.items():
            m = s_data.get("mastery", 0) if isinstance(s_data, dict) else (int(s_data) if isinstance(s_data, (int, float)) else 0)
            if m > max_mastery:
                max_mastery = m
                top_skill = s_name
                
    sector_boss_down = any("sector 1" in str(b).lower() or "gilded" in str(b).lower() or "spire" in str(b).lower() for b in bosses) or player.get("sector_boss_defeated", False)
    regional_boss_down = any("regional" in str(b).lower() or "sector 5" in str(b).lower() for b in bosses) or player.get("regional_boss_defeated", False)
    
    current_tier = player.get("class_tier", 1)
    
    # Tier 2 Check
    if current_tier == 1:
        reasons = []
        unmet = []
        
        if lvl >= 10:
            reasons.append(f"Level Requirement Met: Level {lvl} >= 10")
        else:
            unmet.append(f"Level Requirement Unmet: Level {lvl} / 10")
            
        if sector_boss_down:
            reasons.append("Sector 1 Spire Boss Defeated")
        else:
            unmet.append("Sector 1 Spire Boss Not Yet Slayed")
            
        if max_mastery >= 100:
            reasons.append(f"Skill Mastery Milestone Met: '{top_skill}' Mastery {max_mastery} >= 100 (Journeyman)")
        else:
            unmet.append(f"Skill Mastery Milestone Unmet: Highest Mastery {max_mastery} / 100")
            
        eligible = len(unmet) == 0
        return {
            "eligible": eligible,
            "target_tier": 2,
            "current_tier": 1,
            "reasons": reasons,
            "unmet_conditions": unmet,
            "top_skill": top_skill,
            "top_mastery": max_mastery
        }
        
    # Tier 3 Check
    elif current_tier == 2:
        reasons = []
        unmet = []
        
        if lvl >= 25:
            reasons.append(f"Level Requirement Met: Level {lvl} >= 25")
        else:
            unmet.append(f"Level Requirement Unmet: Level {lvl} / 25")
            
        if regional_boss_down:
            reasons.append("Regional Spire Boss Defeated")
        else:
            unmet.append("Regional Spire Boss Not Yet Slayed")
            
        if max_mastery >= 350:
            reasons.append(f"Skill Mastery Milestone Met: '{top_skill}' Mastery {max_mastery} >= 350")
        else:
            unmet.append(f"Skill Mastery Milestone Unmet: Highest Mastery {max_mastery} / 350")
            
        eligible = len(unmet) == 0
        return {
            "eligible": eligible,
            "target_tier": 3,
            "current_tier": 2,
            "reasons": reasons,
            "unmet_conditions": unmet,
            "top_skill": top_skill,
            "top_mastery": max_mastery
        }
        
    return {
        "eligible": False,
        "target_tier": current_tier,
        "current_tier": current_tier,
        "reasons": ["Maximum class evolution tier reached."],
        "unmet_conditions": []
    }

def generate_curated_evolutions(player):
    """
    Synthesizes player behavioral telemetry to produce the 3 Curated Evolution Options:
    1. Pure Specialization (Advancement of Anchor doctrine)
    2. Fused Hybrid Melded Path (Synergy between Anchor class and highest off-spec skill)
    3. Unique Deed / Thematic Path (Emerged from relics, titles, and unique deeds)
    """
    c_key = normalize_class_key(player.get("class", "warrior"))
    skills = player.get("skills", {})
    
    # Identify secondary skill domain
    skill_names = list(skills.keys())
    has_magic = any("aether" in s.lower() or "circuit" in s.lower() for s in skill_names)
    has_tech = any("hack" in s.lower() or "smith" in s.lower() or "rig" in s.lower() for s in skill_names)
    has_stealth = any("reflex" in s.lower() or "trap" in s.lower() or "dagger" in s.lower() for s in skill_names)
    has_healing = any("triage" in s.lower() or "provisions" in s.lower() or "surgery" in s.lower() for s in skill_names)
    has_heavy_arms = any("hammer" in s.lower() or "axe" in s.lower() for s in skill_names)
    
    # Pure Evolution
    pure_map = {
        "warrior": {"title": "Ironclad Juggernaut", "desc": "Immovable defensive fortress wielding kinetic shockwaves, reinforced poise, and armor-crush dominance."},
        "mage": {"title": "Singularity Arcanist", "desc": "Commands gravitational collapse and catastrophic raw mana rifts."},
        "cleric": {"title": "High Templar Inquisitor", "desc": "Radiant frontline judge wielding holy retribution, martyr shields, and divine storm aegis."},
        "thief": {"title": "Ghost Operative", "desc": "Phantasmal assassin mastering monomolecular strikes, shadow-teleportation, and untraceable stealth."},
        "ranger": {"title": "Phantom Sniper", "desc": "Extreme-distance sniper penetrating armor plates with anti-materiel precision."},
        "engineer": {"title": "Cyber-Mancer", "desc": "Deploys multi-turret defensive grids and overrides robotic/golem neural links."},
        "psion": {"title": "Awakened Telekineticist", "desc": "Bends physical reality and atmospheric pressure with unbridled mental telekinesis."},
        "pathless": {"title": "Sovereign Anomaly", "desc": "The ultimate unrestricted conduit, transcending system tier limits."}
    }
    pure_choice = pure_map.get(c_key, pure_map["pathless"])
    
    # Hybrid Melded Evolution
    if c_key == "warrior":
        if has_magic:
            hybrid_choice = {"title": "Spellblade Runeknight", "desc": "Fuses weapon strikes with condensed arcane flux, detonating runic charges on impact."}
        elif has_healing:
            hybrid_choice = {"title": "Paladin Crusader", "desc": "Absorbs party trauma while releasing waves of sanctified healing on heavy melee cleaves."}
        elif has_tech:
            hybrid_choice = {"title": "Siege Engineer Vanguard", "desc": "Reinforces frontline armor with motorized hydraulics, rocket-boosted hammer strikes, and field repairs."}
        else:
            hybrid_choice = {"title": "Skirmisher Duelist", "desc": "Blends heavy weapon strikes with fluid evasive footwork and lethal counter-ripostes."}
    elif c_key == "mage":
        if has_heavy_arms:
            hybrid_choice = {"title": "Battle-Mage Golem-Breaker", "desc": "Arms cloth wards with crushing melee weaponry, channeling spells directly through physical impacts."}
        elif has_stealth:
            hybrid_choice = {"title": "Arcane Trickster", "desc": "Weaves visual illusions, silent mana daggers, and phase-blink backstabs."}
        else:
            hybrid_choice = {"title": "Chrono-Weaver", "desc": "Manipulates local system tick-rates to accelerate allies and decelerate enemy attacks."}
    elif c_key == "thief":
        if has_magic:
            hybrid_choice = {"title": "Shadow-Weaver", "desc": "Infuses daggers with dark aether and walks through shadows between dimensions."}
        elif has_tech:
            hybrid_choice = {"title": "Magi-Tech Saboteur", "desc": "Infiltrates enemy perimeters with EMP flash-grenades, tripwire snares, and automated decryption."}
        else:
            hybrid_choice = {"title": "Nightstalker Assassin", "desc": "Poisons blades with synthesized neurotoxins and executes guaranteed critical bleed combos."}
    elif c_key == "ranger":
        if has_magic:
            hybrid_choice = {"title": "Aether-Archer", "desc": "Fires arrows of pure compressed light that pierce physical obstacles and illuminate weak points."}
        elif has_heavy_arms:
            hybrid_choice = {"title": "Sector Warden", "desc": "Commands perimeter combat beasts and anchors choke-points with barbed traps and heavy spears."}
        else:
            hybrid_choice = {"title": "Wilderness Survivalist", "desc": "Masters environmental poisons, natural camouflage, and relentless target tracking."}
    else:
        hybrid_choice = {"title": "Resonant Synthesist", "desc": "Seamlessly fuses contrasting combat disciplines into a personalized tactical style."}
        
    # Unique Deed / Thematic Path
    # If the player has Nordic / Berserker themes (like Banki) or Anomaly
    equipped = player.get("equipped", {})
    weapons_str = f"{equipped.get('main_hand', '')} {equipped.get('off_hand', '')}".lower()
    if "axe" in weapons_str or "hammer" in weapons_str or "fenrir" in weapons_str or "mjölnir" in weapons_str:
        unique_choice = {
            "title": "Nordic Berserker of the Rift",
            "desc": "Unleashes untamed mythical wrath, dual-wielding axes and demolition hammers to shatter the virtual overlay itself."
        }
    elif "smartphone" in str(player.get("inventory", [])):
        unique_choice = {
            "title": "Old-World Echo Agent",
            "desc": "Channels pre-integration Earth memories and corrupted terminal code to disrupt System logic."
        }
    else:
        unique_choice = {
            "title": "Glitch-Blade Sovereign",
            "desc": "Carves through reality using corrupted source code, bypassing physical Armor Class and terrain barriers."
        }
        
    return [
        {"tier": 2, "category": "Pure Specialization", **pure_choice},
        {"tier": 2, "category": "Hybrid Melded Path", **hybrid_choice},
        {"tier": 2, "category": "Unique Deed Path", **unique_choice}
    ]

def apply_class_evolution(player, evolution_choice):
    """
    Applies the chosen Tier 2 / Tier 3 Class Evolution:
    - Updates player["class"] title
    - Increments player["class_tier"]
    - Upgrades or fuses combat_resource
    - Awards celebratory evolution feat
    """
    new_title = evolution_choice.get("title", "Evolved Archetype")
    new_tier = evolution_choice.get("tier", 2)
    
    player["class"] = new_title
    player["class_tier"] = new_tier
    
    # Evolve resource pool
    res = initialize_combat_resource(player)
    res["max"] = int(res.get("max", 100) * 1.25)
    res["current"] = res["max"]
    
    # Add Evolution Master Feat
    if "feats" not in player or not isinstance(player["feats"], list):
        player["feats"] = []
        
    evo_feat = f"Class Evolution: {new_title} (Tier {new_tier}): {evolution_choice.get('desc', 'Awakened specialization.')}"
    player["feats"].append(evo_feat)
    
    return {
        "new_class": new_title,
        "new_tier": new_tier,
        "evolved_resource": res,
        "unlocked_feat": evo_feat
    }


# =====================================================================
# PHASE M3: DURABILITY DEGRADATION, FIELD CRAFTING & TRAP-RIGGING
# =====================================================================

ITEM_GRADE_SCALING = {
    1: {
        "name": "Common Scrap",
        "multiplier": 1.0,
        "default_durability": 50,
        "gem_slots": 0,
        "badge": "⚪ Grade 1 (Common Scrap)",
        "rarity": "Common"
    },
    2: {
        "name": "Reinforced",
        "multiplier": 1.25,
        "default_durability": 75,
        "gem_slots": 0,
        "badge": "🟢 Grade 2 (Reinforced)",
        "rarity": "Uncommon"
    },
    3: {
        "name": "Aether-Forged",
        "multiplier": 1.5,
        "default_durability": 100,
        "gem_slots": 1,
        "badge": "🔵 Grade 3 (Aether-Forged)",
        "rarity": "Rare"
    },
    4: {
        "name": "Runic Masterwork",
        "multiplier": 2.0,
        "default_durability": 150,
        "gem_slots": 2,
        "badge": "🟣 Grade 4 (Runic Masterwork)",
        "rarity": "Epic"
    },
    5: {
        "name": "Einherjar / Boss Tier",
        "multiplier": 2.5,
        "default_durability": 200,
        "gem_slots": 3,
        "badge": "🟠 Grade 5 (Einherjar)",
        "rarity": "Legendary"
    }
}

def get_item_grade(item):
    """Determines item grade (1-5) from item name or object."""
    if isinstance(item, dict):
        if "grade" in item:
            try:
                return max(1, min(5, int(item["grade"])))
            except (ValueError, TypeError):
                pass
        name = item.get("name", "").lower()
        desc = item.get("desc", "").lower()
        rarity = item.get("rarity", "").lower()
    elif isinstance(item, str):
        name = item.lower()
        desc = ""
        rarity = ""
    else:
        return 1

    text = f"{name} {desc} {rarity}"
    if any(k in text for k in ["gr. 5", "grade 5", "einherjar", "fenrir", "mjölnir", "boss tier", "mythic", "unique"]):
        return 5
    if any(k in text for k in ["gr. 4", "grade 4", "runic", "masterwork", "epic"]):
        return 4
    if any(k in text for k in ["gr. 3", "grade 3", "aether-forged", "aetheric", "rare"]):
        return 3
    if any(k in text for k in ["gr. 2", "grade 2", "reinforced", "uncommon"]):
        return 2
    return 1

def normalize_gear_durability(player_state):
    """
    Ensures player_state['gear_durability'] is present and synced with equipped items.
    Initializes max durability according to item grade.
    """
    if "gear_durability" not in player_state or not isinstance(player_state["gear_durability"], dict):
        player_state["gear_durability"] = {}

    gear_dur = player_state["gear_durability"]
    equipped = player_state.get("equipped", {})

    for slot in ["head", "chest", "main_hand", "off_hand", "accessory"]:
        item_val = equipped.get(slot, "None")
        if item_val and item_val != "None":
            grade = get_item_grade(item_val)
            default_max = ITEM_GRADE_SCALING[grade]["default_durability"]
            
            # Special case for heavy rigs/boss armor
            item_str = str(item_val).lower()
            if "rig" in item_str and grade >= 5:
                default_max = 250

            if slot not in gear_dur or not isinstance(gear_dur[slot], dict):
                gear_dur[slot] = {"cur": default_max, "max": default_max, "grade": grade}
            else:
                s_dict = gear_dur[slot]
                max_d = s_dict.get("max", default_max)
                cur_d = s_dict.get("cur", max_d)
                s_dict["max"] = max_d
                s_dict["cur"] = max(0, min(max_d, cur_d))
                s_dict["grade"] = grade
        else:
            if slot not in gear_dur:
                gear_dur[slot] = {"cur": 100, "max": 100, "grade": 1}

    return gear_dur

def get_durability_state(cur, max_dur):
    """
    Evaluates equipment wear state:
    - Pristine (>75%): 100% performance
    - Worn (25% - 74%): Minor visual wear
    - Dulled/Cracked (1% - 24%): -2 Attack / -2 AC penalty
    - Broken (0%): Ineffective in combat
    """
    cur = max(0, int(cur))
    max_dur = max(1, int(max_dur))
    pct = cur / max_dur

    if cur == 0:
        return {
            "state": "Broken",
            "label": "🔴 BROKEN (Ineffective)",
            "penalty_atk": 5,
            "penalty_ac": 5,
            "is_broken": True,
            "is_dulled": True,
            "pct": 0.0
        }
    elif pct < 0.25:
        return {
            "state": "Dulled/Cracked",
            "label": "🟠 Dulled/Cracked (-2)",
            "penalty_atk": 2,
            "penalty_ac": 2,
            "is_broken": False,
            "is_dulled": True,
            "pct": pct
        }
    elif pct < 0.75:
        return {
            "state": "Worn",
            "label": "🟡 Worn",
            "penalty_atk": 0,
            "penalty_ac": 0,
            "is_broken": False,
            "is_dulled": False,
            "pct": pct
        }
    else:
        return {
            "state": "Pristine",
            "label": "🟢 Pristine",
            "penalty_atk": 0,
            "penalty_ac": 0,
            "is_broken": False,
            "is_dulled": False,
            "pct": pct
        }

def calculate_durability_penalties(player_state):
    """
    Calculates total penalties applied from damaged/broken equipped gear.
    """
    gear_dur = player_state.get("gear_durability", {})
    equipped = player_state.get("equipped", {})

    atk_penalty = 0
    ac_penalty = 0
    chest_broken = False
    shield_broken = False
    broken_items = []
    dulled_items = []

    for slot in ["main_hand", "off_hand"]:
        item = equipped.get(slot, "None")
        if item != "None" and slot in gear_dur:
            d = gear_dur[slot]
            state_info = get_durability_state(d.get("cur", 0), d.get("max", 100))
            if state_info["is_broken"]:
                if "shield" in str(item).lower():
                    shield_broken = True
                else:
                    atk_penalty += 4
                broken_items.append(f"{slot} ({item})")
            elif state_info["is_dulled"]:
                if "shield" in str(item).lower():
                    ac_penalty += 1
                else:
                    atk_penalty += 2
                dulled_items.append(f"{slot} ({item})")

    # Armor slots
    for slot in ["chest", "head"]:
        item = equipped.get(slot, "None")
        if item != "None" and slot in gear_dur:
            d = gear_dur[slot]
            state_info = get_durability_state(d.get("cur", 0), d.get("max", 100))
            if state_info["is_broken"]:
                if slot == "chest":
                    chest_broken = True
                ac_penalty += 2
                broken_items.append(f"{slot} ({item})")
            elif state_info["is_dulled"]:
                ac_penalty += 2
                dulled_items.append(f"{slot} ({item})")

    return {
        "atk_penalty": atk_penalty,
        "ac_penalty": ac_penalty,
        "chest_broken": chest_broken,
        "shield_broken": shield_broken,
        "broken_items": broken_items,
        "dulled_items": dulled_items
    }

def apply_durability_damage(player_state, slot_or_name, amount=1):
    """
    Reduces durability for an equipped slot or named inventory item.
    Returns status record and combat log string.
    """
    normalize_gear_durability(player_state)
    gear_dur = player_state.get("gear_durability", {})
    equipped = player_state.get("equipped", {})

    target_slot = None
    item_name = "Unknown Item"

    # Match by slot name
    if slot_or_name in gear_dur:
        target_slot = slot_or_name
        item_name = equipped.get(target_slot, slot_or_name)
    else:
        # Match by item name across equipped slots
        query = str(slot_or_name).lower()
        for s, iname in equipped.items():
            if iname and query in iname.lower():
                target_slot = s
                item_name = iname
                break

    if target_slot and target_slot in gear_dur:
        entry = gear_dur[target_slot]
        old_cur = entry.get("cur", entry.get("max", 100))
        max_d = entry.get("max", 100)
        new_cur = max(0, old_cur - amount)
        entry["cur"] = new_cur

        state_info = get_durability_state(new_cur, max_d)
        log = f"[DURABILITY: {item_name} {new_cur}/{max_d} (-{amount}) - {state_info['label']}]"
        
        return {
            "slot": target_slot,
            "item": item_name,
            "old_cur": old_cur,
            "new_cur": new_cur,
            "current": new_cur,
            "max": max_d,
            "loss": amount,
            "state": state_info["state"],
            "is_broken": state_info["is_broken"],
            "broken": state_info["is_broken"],
            "is_dulled": state_info["is_dulled"],
            "log": log
        }

    # Fallback to backpack item search
    for item in player_state.get("inventory", []):
        if isinstance(item, dict) and str(slot_or_name).lower() in item.get("name", "").lower():
            old_cur = item.get("durability", item.get("max_durability", 100))
            max_d = item.get("max_durability", 100)
            new_cur = max(0, old_cur - amount)
            item["durability"] = new_cur
            state_info = get_durability_state(new_cur, max_d)
            log = f"[DURABILITY: {item.get('name')} {new_cur}/{max_d} (-{amount}) - {state_info['label']}]"
            return {
                "slot": "inventory",
                "item": item.get("name"),
                "old_cur": old_cur,
                "new_cur": new_cur,
                "current": new_cur,
                "max": max_d,
                "loss": amount,
                "state": state_info["state"],
                "is_broken": state_info["is_broken"],
                "broken": state_info["is_broken"],
                "is_dulled": state_info["is_dulled"],
                "log": log
            }

    return {"slot": None, "item": slot_or_name, "log": f"[DURABILITY: {slot_or_name} not found]"}

def repair_item(player_state, slot_or_name, repair_amount=None, col_per_point=1):
    """
    Repairs an equipped item or inventory item back to full (or by repair_amount).
    Deducts Col if player has sufficient funds.
    """
    normalize_gear_durability(player_state)
    gear_dur = player_state.get("gear_durability", {})
    equipped = player_state.get("equipped", {})

    target_entry = None
    item_name = str(slot_or_name)

    if slot_or_name in gear_dur:
        target_entry = gear_dur[slot_or_name]
        item_name = equipped.get(slot_or_name, slot_or_name)
    else:
        query = str(slot_or_name).lower()
        for s, iname in equipped.items():
            if iname and query in iname.lower():
                target_entry = gear_dur[s]
                item_name = iname
                break

    if not target_entry:
        for item in player_state.get("inventory", []):
            if isinstance(item, dict) and str(slot_or_name).lower() in item.get("name", "").lower():
                target_entry = item
                item_name = item.get("name")
                break

    if not target_entry:
        return {"success": False, "message": f"Item '{slot_or_name}' not found."}

    cur_key = "cur" if "cur" in target_entry else "durability"
    max_key = "max" if "max" in target_entry else "max_durability"

    cur_d = target_entry.get(cur_key, 0)
    max_d = target_entry.get(max_key, 100)
    needed = max_d - cur_d

    if needed <= 0:
        return {"success": True, "repaired": 0, "col_cost": 0, "message": f"{item_name} is already pristine ({max_d}/{max_d})."}

    actual_repair = needed if repair_amount is None else min(needed, repair_amount)
    total_cost = actual_repair * col_per_point

    player_col = player_state.get("col", 0)
    if player_col < total_cost:
        # Partial repair with whatever Col is available
        if col_per_point > 0:
            actual_repair = player_col // col_per_point
            total_cost = actual_repair * col_per_point
        if actual_repair <= 0:
            return {"success": False, "repaired": 0, "col_cost": 0, "message": f"Insufficient Col to repair {item_name} (Requires {needed * col_per_point} Col)."}

    target_entry[cur_key] = cur_d + actual_repair
    player_state["col"] = player_col - total_cost

    return {
        "success": True,
        "repaired": actual_repair,
        "new_durability": target_entry[cur_key],
        "max_durability": max_d,
        "col_cost": total_cost,
        "message": f"Repaired {item_name} (+{actual_repair} dur) to {target_entry[cur_key]}/{max_d} for {total_cost} Col."
    }

# =====================================================================
# FIELD CRAFTING, SCAVENGING & TRAP-RIGGING ENGINE
# =====================================================================

CANONICAL_TRAPS = {
    "serrated_tripwire": {
        "key": "serrated_tripwire",
        "name": "Serrated Monofilament Tripwire",
        "base_dc": 12,
        "prep_turns": 1,
        "damage_dice": "2d6",
        "condition": "Bleed & Prone",
        "description": "Ultra-sharp monofilament strung across natural choke-points. Trips target prone and inflicts 2d6 slashing damage plus Bleed.",
        "materials": {
            "Serrated Tripwire Coils": 1,
            "Anchors and Tension Pins": 1
        }
    },
    "heavy_highway_snare": {
        "key": "heavy_highway_snare",
        "name": "Heavy Highway Snare",
        "base_dc": 14,
        "prep_turns": 1,
        "damage_dice": "1d8",
        "condition": "Tethered",
        "description": "High-tension braided cable hoist. Yanks target into suspension, inflicting Tethered condition (0 movement, attacks against target have advantage).",
        "materials": {
            "Heavy Highway Snares": 1,
            "Carbon Line Spools": 1
        }
    },
    "marrow_aggro_corridor": {
        "key": "marrow_aggro_corridor",
        "name": "Rendered Marrow Scent Corridor",
        "base_dc": 13,
        "prep_turns": 2,
        "damage_dice": "None",
        "condition": "Aggro Lure & Surprise Ambush",
        "description": "Smears 500m pheromone corridor to funnel beasts directly into pre-sighted kill zones. Grants automatic Surprise Round (+5 initiative, guaranteed critical strike).",
        "materials": {
            "Crate of Marrow-Jars": 1,
            "Carbon Line Spools": 1
        }
    },
    "emp_shock_mine": {
        "key": "emp_shock_mine",
        "name": "Improvised EMP Shock-Mine",
        "base_dc": 15,
        "prep_turns": 1,
        "damage_dice": "3d8",
        "condition": "Stunned & Ionized",
        "description": "Repurposed micro-capacitor detonating on pressure. Inflicts 3d8 electrical damage in a 10ft radius; DC 14 CON save or Stunned for 1 turn.",
        "materials": {
            "Corroded Micro-Capacitor": 1,
            "Frayed Copper Wiring": 1
        }
    }
}

def _find_inventory_item(inventory, query_name):
    """Helper to locate an inventory entry matching query_name and return (item, index)."""
    q = query_name.lower().strip()
    for idx, item in enumerate(inventory):
        if isinstance(item, str):
            clean_name = item.split(" x")[0].lower().strip()
            if q in clean_name or clean_name in q:
                return item, idx
        elif isinstance(item, dict):
            name = item.get("name", "").lower().strip()
            if q in name or name in q:
                return item, idx
    return None, -1

def can_craft_trap(player_state, trap_key):
    """
    Checks if player has all required materials in inventory to craft/rig the specified trap.
    """
    if trap_key not in CANONICAL_TRAPS:
        return False, f"Unknown trap key '{trap_key}'", {}

    trap_def = CANONICAL_TRAPS[trap_key]
    required = trap_def["materials"]
    inv = player_state.get("inventory", [])
    
    missing = {}
    available = {}

    for mat_name, req_qty in required.items():
        found_item, _ = _find_inventory_item(inv, mat_name)
        if not found_item:
            missing[mat_name] = req_qty
        else:
            # Check qty
            qty = 1
            if isinstance(found_item, str) and " x" in found_item:
                try:
                    qty = int(found_item.rsplit(" x", 1)[1])
                except ValueError:
                    qty = 1
            elif isinstance(found_item, dict):
                qty = found_item.get("qty", 1)

            if qty < req_qty:
                missing[mat_name] = req_qty - qty
            else:
                available[mat_name] = qty

    if missing:
        missing_str = ", ".join([f"{k} (need {v})" for k, v in missing.items()])
        return False, f"Missing materials: {missing_str}", missing

    return True, "All materials present.", available

def consume_trap_materials(player_state, trap_key):
    """
    Deducts the required materials for a trap from the player's inventory.
    """
    can_craft, msg, _ = can_craft_trap(player_state, trap_key)
    if not can_craft:
        return False, msg

    trap_def = CANONICAL_TRAPS[trap_key]
    inv = player_state.get("inventory", [])

    for mat_name, req_qty in trap_def["materials"].items():
        found_item, idx = _find_inventory_item(inv, mat_name)
        if idx != -1:
            if isinstance(found_item, str):
                cur_qty = 1
                base_name = found_item
                if " x" in found_item:
                    parts = found_item.rsplit(" x", 1)
                    base_name = parts[0]
                    try:
                        cur_qty = int(parts[1])
                    except ValueError:
                        cur_qty = 1
                new_qty = cur_qty - req_qty
                if new_qty <= 0:
                    inv.pop(idx)
                else:
                    inv[idx] = f"{base_name} x{new_qty}"
            elif isinstance(found_item, dict):
                cur_qty = found_item.get("qty", 1)
                new_qty = cur_qty - req_qty
                if new_qty <= 0:
                    inv.pop(idx)
                else:
                    found_item["qty"] = new_qty

    return True, f"Consumed materials for {trap_def['name']}."

def rig_field_trap(player_state, trap_key, prep_time_turns=1, d20_roll=None):
    """
    Deploys a field trap:
    - Verifies and consumes materials
    - Rolls 1d20 + DEX mod + Field Trapping Mastery bonus vs Base DC
    - On success: deploys active trap with dynamic Stealth DC and damage
    - Awards Field Trapping skill mastery
    """
    if trap_key not in CANONICAL_TRAPS:
        return {"success": False, "log": f"[TRAP ERROR: Unknown trap '{trap_key}']"}

    trap_def = CANONICAL_TRAPS[trap_key]

    can_craft, msg, _ = can_craft_trap(player_state, trap_key)
    if not can_craft:
        return {"success": False, "log": f"[TRAP RIGGING FAILED: {msg}]"}

    # Consume components
    consume_trap_materials(player_state, trap_key)

    # Get Field Trapping skill mastery
    skills = player_state.get("skills", {})
    trapping_mastery = 1
    for s_name, s_data in skills.items():
        if "trapping" in s_name.lower() or "survival" in s_name.lower():
            if isinstance(s_data, dict):
                trapping_mastery = max(trapping_mastery, int(s_data.get("mastery", 1)))
            elif isinstance(s_data, (int, float)):
                trapping_mastery = max(trapping_mastery, int(s_data))

    stats = player_state.get("stats", {})
    dex_mod = (stats.get("DEX", 10) - 10) // 2
    mastery_bonus = trapping_mastery // 100

    import random
    roll = random.randint(1, 20) if d20_roll is None else int(d20_roll)
    total_check = roll + dex_mod + mastery_bonus
    base_dc = trap_def["base_dc"]

    success = (total_check >= base_dc)
    stealth_dc = 10 + dex_mod + mastery_bonus + max(0, total_check - base_dc)

    # Update Field Trapping Skill Mastery
    update_skill_mastery(
        player_state=player_state,
        skill_name="Field Trapping",
        gain_or_dc=base_dc,
        is_dc=True,
        desc="Deployment of tactical combat snare",
        critical=(roll == 20)
    )

    deployed_trap = {
        "key": trap_key,
        "name": trap_def["name"],
        "stealth_dc": stealth_dc,
        "damage_dice": trap_def["damage_dice"],
        "condition": trap_def["condition"],
        "effect": trap_def["description"],
        "deployed_turn": player_state.get("turn_count", 1)
    }

    if "active_traps" not in player_state or not isinstance(player_state["active_traps"], list):
        player_state["active_traps"] = []

    player_state["active_traps"].append(deployed_trap)

    log = (
        f"[TRAP RIGGED: {trap_def['name']} | Roll 1d20({roll}) + DEX({dex_mod}) + Mastery({mastery_bonus}) = {total_check} "
        f"vs DC {base_dc} - SUCCESS! Concealment Stealth DC: {stealth_dc}]"
    )

    return {
        "success": True,
        "trap": deployed_trap,
        "roll": roll,
        "total_check": total_check,
        "stealth_dc": stealth_dc,
        "log": log
    }

def trigger_field_trap(player_state, trap_idx_or_key, target_name="Mutated Stalker", target_passive_perception=12):
    """
    Evaluates whether an enemy triggers an active field trap.
    """
    active_traps = player_state.get("active_traps", [])
    if not active_traps:
        return {"triggered": False, "log": "[TRAP: No active traps deployed]"}

    target_trap = None
    target_idx = -1

    if isinstance(trap_idx_or_key, int) and 0 <= trap_idx_or_key < len(active_traps):
        target_trap = active_traps[trap_idx_or_key]
        target_idx = trap_idx_or_key
    else:
        for idx, t in enumerate(active_traps):
            if t.get("key") == trap_idx_or_key or t.get("name", "").lower() == str(trap_idx_or_key).lower():
                target_trap = t
                target_idx = idx
                break

    if not target_trap:
        target_trap = active_traps[0]
        target_idx = 0

    stealth_dc = target_trap.get("stealth_dc", 12)
    ambushed = (stealth_dc >= target_passive_perception)

    # Pop active trap
    active_traps.pop(target_idx)

    log = (
        f"[TRAP SPRING: {target_name} stepped into {target_trap['name']}! "
        f"Trap Stealth DC {stealth_dc} vs Target Perception {target_passive_perception} -> "
        f"{'SURPRISE AMBUSH TRIGGERED!' if ambushed else 'DETECTED AT LAST MOMENT!'} "
        f"Damage: {target_trap['damage_dice']} | Condition: {target_trap['condition']}]"
    )

    return {
        "success": True,
        "triggered": True,
        "ambushed": ambushed,
        "trap": target_trap,
        "target": target_name,
        "log": log
    }

def salvage_materials(player_state, target_type="construct", d20_roll=None):
    """
    Scavenges raw materials from fallen constructs, mutated beasts, or structural ruins.
    Scales with Field Smithing or Scavenging mastery.
    """
    SALVAGE_TABLES = {
        "construct": [
            {"name": "Frayed Copper Wiring", "qty": 2, "weight": 0.5},
            {"name": "Corroded Micro-Capacitor", "qty": 1, "weight": 0.2},
            {"name": "Titanium Wire Scrap", "qty": 1, "weight": 1.0}
        ],
        "beast": [
            {"name": "Rendered Chimera Marrow", "qty": 1, "weight": 1.5},
            {"name": "Hardened Chitin Plates", "qty": 2, "weight": 3.0},
            {"name": "Mutated Sinew Cord", "qty": 1, "weight": 0.8}
        ],
        "ruins": [
            {"name": "Carbon Line Spools", "qty": 1, "weight": 2.0},
            {"name": "Anchors and Tension Pins", "qty": 1, "weight": 1.0},
            {"name": "Scrap Iron Plate", "qty": 1, "weight": 4.0}
        ]
    }

    t_key = target_type.lower()
    table_key = "construct"
    if "beast" in t_key or "chimera" in t_key or "monster" in t_key or "wolf" in t_key or "boar" in t_key:
        table_key = "beast"
    elif "ruin" in t_key or "scrap" in t_key or "cache" in t_key:
        table_key = "ruins"

    import random
    roll = random.randint(1, 20) if d20_roll is None else int(d20_roll)
    
    # Get skill bonus
    skills = player_state.get("skills", {})
    scav_mastery = 1
    for s_name, s_data in skills.items():
        if any(w in s_name.lower() for w in ["smithing", "scaveng", "salvage", "survival"]):
            if isinstance(s_data, dict):
                scav_mastery = max(scav_mastery, int(s_data.get("mastery", 1)))
            elif isinstance(s_data, (int, float)):
                scav_mastery = max(scav_mastery, int(s_data))

    stats = player_state.get("stats", {})
    wis_mod = (stats.get("WIS", 10) - 10) // 2
    mastery_bonus = scav_mastery // 100
    total_roll = roll + wis_mod + mastery_bonus

    items_to_add = []
    pool = SALVAGE_TABLES[table_key]

    if total_roll >= 15:
        # Full salvage: 2 items
        items_to_add.extend([copy.deepcopy(x) for x in pool[:2]])
    elif total_roll >= 10:
        # Standard salvage: 1 item
        items_to_add.append(copy.deepcopy(pool[0]))
    else:
        # Low roll: basic scrap
        items_to_add.append({"name": "Tainted Metallic Scrap", "qty": 1, "weight": 1.0})

    # Regional 100-mile World Atlas specialty ore / resource yield
    active_zone = resolve_zone_from_location(player_state.get("location", "")) or resolve_zone_from_location(target_type)
    if active_zone and total_roll >= 10:
        zone_resources = active_zone.get("resources", [])
        if zone_resources:
            reg_item = zone_resources[0]
            reg_qty = 2 if (total_roll >= 15 and active_zone.get("category") == "mine") else 1
            items_to_add.append({
                "name": reg_item,
                "qty": reg_qty,
                "weight": 2.5 if active_zone.get("category") == "mine" else 1.5,
                "desc": f"Regional specialty resource extracted from {active_zone.get('name', 'the Wilds')}."
            })

    # Add to player inventory
    inv = player_state.setdefault("inventory", [])
    added_names = []
    for item in items_to_add:
        found_item, idx = _find_inventory_item(inv, item["name"])
        if idx != -1:
            if isinstance(found_item, dict):
                found_item["qty"] = found_item.get("qty", 1) + item["qty"]
            elif isinstance(found_item, str):
                cur_qty = 1
                base_name = found_item
                if " x" in found_item:
                    base_name, qstr = found_item.rsplit(" x", 1)
                    try: cur_qty = int(qstr)
                    except ValueError: cur_qty = 1
                inv[idx] = f"{base_name} x{cur_qty + item['qty']}"
        else:
            inv.append({"name": item["name"], "qty": item["qty"], "rarity": "Common", "durability": 100, "max_durability": 100, "desc": item.get("desc", "Field salvaged component.")})
        added_names.append(f"{item['name']} (x{item['qty']})")

    # Award skill mastery
    update_skill_mastery(
        player_state=player_state,
        skill_name="Field Smithing",
        gain_or_dc=12,
        is_dc=True,
        desc="Field salvage of defeated target",
        critical=(roll == 20)
    )

    log = (
        f"[SALVAGE: {target_type} | Roll 1d20({roll}) + WIS({wis_mod}) + Mastery({mastery_bonus}) = {total_roll} "
        f"-> Harvested: {', '.join(added_names)}]"
    )

    return {
        "success": True,
        "items": items_to_add,
        "roll": roll,
        "total_roll": total_roll,
        "log": log
    }


# =====================================================================
# PHASE M4: GOLEM-GRAFTS & ABILITY SLOTTING MATRIX
# =====================================================================

CANONICAL_GRAFTS = {
    "golem_hydraulic_arm": {
        "key": "golem_hydraulic_arm",
        "name": "Golem Hydraulic Arm",
        "allowed_slots": ["arm_left", "arm_right"],
        "strain": 15,
        "col_cost": 2500,
        "stat_bonuses": {"STR": 2},
        "description": "Titan-hydraulic pistons allow single-handed structural crushing and grant +2 STR checks.",
        "effect": "+2 STR, +10 unarmed bludgeoning damage"
    },
    "aether_resonant_ocular": {
        "key": "aether_resonant_ocular",
        "name": "Aether-Resonant Ocular",
        "allowed_slots": ["ocular"],
        "strain": 10,
        "col_cost": 1800,
        "stat_bonuses": {"WIS": 2},
        "description": "Crystalline runic lens revealing invisible entities, secret conduits, and ley-line currents.",
        "effect": "+2 WIS, Darkvision (120ft) & Ley-Line Sight (+3 to investigate secrets)"
    },
    "subdermal_carapace_weave": {
        "key": "subdermal_carapace_weave",
        "name": "Subdermal Carapace Weave",
        "allowed_slots": ["dermal"],
        "strain": 20,
        "col_cost": 3500,
        "stat_bonuses": {"CON": 1},
        "description": "Flexible graphene-chitin mesh woven beneath skin layers, blunting incoming ballistic and slashing impacts.",
        "effect": "+2 AC, Damage Reduction (DR 2 Physical), +1 CON"
    },
    "spring_loaded_golem_greaves": {
        "key": "spring_loaded_golem_greaves",
        "name": "Spring-Loaded Golem Greaves",
        "allowed_slots": ["leg_left", "leg_right"],
        "strain": 12,
        "col_cost": 2000,
        "stat_bonuses": {"DEX": 1},
        "description": "Pneumatic kickback joints amplifying leap distance, running velocity, and acrobatic recovery.",
        "effect": "+10ft Movement Speed, +2 to DEX saving throws, +1 DEX"
    },
    "neural_overclock_cortex": {
        "key": "neural_overclock_cortex",
        "name": "Neural Overclock Cortex",
        "allowed_slots": ["neural"],
        "strain": 18,
        "col_cost": 4000,
        "stat_bonuses": {"INT": 2},
        "description": "Liquid-crystal synaptic booster allowing multi-threaded thought processes and expanded ability memory.",
        "effect": "+2 INT, +1 Active Ability Slot in Matrix Memory"
    },
    "leyline_conduit_spine": {
        "key": "leyline_conduit_spine",
        "name": "Leyline Conduit Spine",
        "allowed_slots": ["spine"],
        "strain": 14,
        "col_cost": 3000,
        "stat_bonuses": {"WIS": 1, "INT": 1},
        "description": "Gold-threaded spinal shunt maintaining pure mana flow around metallic limbs, shielding spellcasters from graft interference.",
        "effect": "Harmonizes 2 installed grafts (negates spellcaster penalty), +15 Max Combat Resource"
    },
    # Biological & Chimera Creature Grafts (The Crucible / Doc Mercer Clinic)
    "basalt_carapace_plating": {
        "key": "basalt_carapace_plating",
        "name": "Basalt Carapace Plating",
        "type": "biological",
        "allowed_slots": ["dermal", "torso"],
        "strain": 12,
        "col_cost": 1500,
        "stat_bonuses": {"CON": 2},
        "description": "Dense calcified scales harvested from quarry behemoths, providing earth-attuned blunt resistance.",
        "effect": "+2 AC, DR 2 Physical, immune to subterranean tremors"
    },
    "silt_marrow_geothermal_core": {
        "key": "silt_marrow_geothermal_core",
        "name": "Silt-Marrow Geothermal Core",
        "type": "biological",
        "allowed_slots": ["spine", "torso", "dermal"],
        "strain": 15,
        "col_cost": 2000,
        "stat_bonuses": {"STR": 1, "CON": 1},
        "description": "An energetic beast heart ventricle pulsing with geothermal steam and volcanic vitality.",
        "effect": "Thermal venting: 1d6 fire retaliation on melee attackers, +10 Fire Resistance"
    },
    "basilisk_venom_gland": {
        "key": "basilisk_venom_gland",
        "name": "Basilisk Venom Gland",
        "type": "biological",
        "allowed_slots": ["arm_left", "arm_right", "left_arm", "right_arm"],
        "strain": 10,
        "col_cost": 1800,
        "stat_bonuses": {"DEX": 1},
        "description": "A harvested serpentine gland wired into arterial ducts to coat blades with necrotic venom.",
        "effect": "Envenomed Strikes: Weapon attacks inflict 1d8 poison damage (DC 14 CON or Poisoned)"
    },
    "wyrm_scale_sheath": {
        "key": "wyrm_scale_sheath",
        "name": "Wyrm-Scale Sheath",
        "type": "biological",
        "allowed_slots": ["dermal", "torso"],
        "strain": 14,
        "col_cost": 2800,
        "stat_bonuses": {"CON": 1, "CHA": 1},
        "description": "Iridescent draconic epidermal grafting that refracts elemental spells.",
        "effect": "+2 AC, +15 Fire/Lightning resistance, Intimidation advantage"
    },
    "stalker_shadow_tendon": {
        "key": "stalker_shadow_tendon",
        "name": "Stalker Shadow-Tendon",
        "type": "biological",
        "allowed_slots": ["leg_left", "leg_right", "legs"],
        "strain": 10,
        "col_cost": 1600,
        "stat_bonuses": {"DEX": 2},
        "description": "Elongated predatory muscle fibers woven into leg joints for silent sprint leaps.",
        "effect": "+15ft speed, +4 to Stealth checks, Silent Step perk"
    },
    "chimeric_beast_claws": {
        "key": "chimeric_beast_claws",
        "name": "Chimeric Beast Claws",
        "type": "biological",
        "allowed_slots": ["arm_left", "arm_right", "left_arm", "right_arm"],
        "strain": 8,
        "col_cost": 1200,
        "stat_bonuses": {"STR": 1},
        "description": "Razor-honed obsidian talon sheaths anchored directly into finger phalanges.",
        "effect": "1d8 Slashing Unarmed strike with Bleed (2 bleeding dmg/turn for 3 turns)"
    },
    # --- Multi-Universe Bestiary Grafts (D&D, Pathfinder, Witcher, FF, Monster Hunter, SAO) ---
    "displacer_tentacle_mantle": {
        "key": "displacer_tentacle_mantle",
        "name": "Displacer Tentacle Mantle",
        "type": "biological",
        "allowed_slots": ["spine", "torso", "dermal"],
        "strain": 14,
        "col_cost": 2600,
        "stat_bonuses": {"DEX": 2},
        "description": "Twin barbed Feywild shoulder-tentacles and light-refracting pelt nerves harvested from a D&D Displacer Beast.",
        "effect": "Displacement Blur (-2 penalty to enemy attack rolls against you) & 10ft Barbed Tentacle Whip (2d6 piercing)"
    },
    "beholder_antimagic_ocular": {
        "key": "beholder_antimagic_ocular",
        "name": "Beholder Central Anti-Magic Ocular",
        "type": "biological",
        "allowed_slots": ["ocular", "head"],
        "strain": 18,
        "col_cost": 4500,
        "stat_bonuses": {"INT": 2, "WIS": 2},
        "description": "Crystalline central lens of an Underdark Eye Tyrant wired directly into the optic chiasm.",
        "effect": "+2 INT/WIS, All-Around Vision (cannot be flanked), and 30ft Anti-Magic / Disintegration Eye-Ray (once per encounter)"
    },
    "illithid_psionic_tendrils": {
        "key": "illithid_psionic_tendrils",
        "name": "Illithid Psionic Tentacle Cortex",
        "type": "biological",
        "allowed_slots": ["neural", "head"],
        "strain": 16,
        "col_cost": 3800,
        "stat_bonuses": {"INT": 3},
        "description": "Psionic Mind Flayer ganglia grafted into the brainstem, enabling telepathic projection and psychic shockwaves.",
        "effect": "+3 INT, 120ft Telepathy, and Mind Blast (15ft cone dealing 3d8 Psychic damage + Stun DC 15 once per encounter)"
    },
    "troll_regenerative_liver": {
        "key": "troll_regenerative_liver",
        "name": "Troll Regenerative Liver",
        "type": "biological",
        "allowed_slots": ["torso", "dermal"],
        "strain": 15,
        "col_cost": 2400,
        "stat_bonuses": {"CON": 3},
        "description": "Hyper-mitotic emerald organ from a D&D/Pathfinder Troll that continuously knits torn muscle and bone.",
        "effect": "+3 CON; Regenerates +5 HP at the start of every combat round (suppressed for 1 round if hit by Fire or Acid)"
    },
    "phase_spider_spinneret": {
        "key": "phase_spider_spinneret",
        "name": "Phase Spider Ethereal Spinneret",
        "type": "biological",
        "allowed_slots": ["arm_left", "arm_right", "left_arm", "right_arm"],
        "strain": 11,
        "col_cost": 2100,
        "stat_bonuses": {"DEX": 2},
        "description": "Sub-wrist arachnid gland from an Ethereal Phase Spider that spins dimensional anchor-silk.",
        "effect": "Ethereal Jaunt (30ft bonus-action teleport once per encounter) & Phase-Web Snare (Restrains target, DC 14)"
    },
    "bulette_dorsal_carapace": {
        "key": "bulette_dorsal_carapace",
        "name": "Bulette Dorsal Carapace",
        "type": "biological",
        "allowed_slots": ["dermal", "torso"],
        "strain": 16,
        "col_cost": 3200,
        "stat_bonuses": {"CON": 2, "STR": 1},
        "description": "Layered subterranean 'Landshark' armor plates grafted across the ribcage and shoulders.",
        "effect": "+3 Natural AC, 30ft Subterranean Tremorsense, and Deadly Leap shockwave (+2d8 bludgeoning on jump attacks)"
    },
    "rust_monster_feeler_whip": {
        "key": "rust_monster_feeler_whip",
        "name": "Rust Monster Feeler Whip",
        "type": "biological",
        "allowed_slots": ["arm_left", "arm_right", "left_arm", "right_arm"],
        "strain": 9,
        "col_cost": 1650,
        "stat_bonuses": {"DEX": 1},
        "description": "Ferrous-oxidizing feathery antennae grafted along the forearm to corrode enemy plating on contact.",
        "effect": "Corrosive Touch: Melee strikes corrode enemy metal armor, permanently reducing target AC by -2 (up to -4)"
    },
    "linnorm_curse_heart": {
        "key": "linnorm_curse_heart",
        "name": "Primeval Linnorm Curse-Heart",
        "type": "biological",
        "allowed_slots": ["torso", "spine"],
        "strain": 18,
        "col_cost": 4200,
        "stat_bonuses": {"CON": 2, "STR": 2},
        "description": "First-World draconic ventricle from a Pathfinder Crag/Tarn Linnorm pulsing with primeval vitality.",
        "effect": "Freedom of Movement (immune to paralysis/grapple/slow) & Retributive Linnorm Curse (attackers take 2d6 elemental recoil)"
    },
    "leshen_ancient_heartwood": {
        "key": "leshen_ancient_heartwood",
        "name": "Leshen Ancient Heartwood",
        "type": "biological",
        "allowed_slots": ["spine", "torso"],
        "strain": 14,
        "col_cost": 2900,
        "stat_bonuses": {"WIS": 2, "CON": 1},
        "description": "Runic ironwood heart-root from a Witcher Ancient Leshen woven into the spinal column.",
        "effect": "Root-Spike Eruption (25ft line of roots dealing 3d8 piercing + Restrained) & Woodland Crow-Step"
    },
    "malboro_bad_breath_gland": {
        "key": "malboro_bad_breath_gland",
        "name": "Malboro Bad-Breath Gland",
        "type": "biological",
        "allowed_slots": ["torso", "head"],
        "strain": 13,
        "col_cost": 2700,
        "stat_bonuses": {"CON": 2},
        "description": "Fetid alchemical bile-sac from a Final Fantasy Great Malboro connected to the respiratory tract.",
        "effect": "Bad Breath (Once per encounter, exhale a 15ft Miasma Cone inflicting Poisoned, Blinded, and Confused, DC 15 CON)"
    },
    "tonberry_grudge_lantern": {
        "key": "tonberry_grudge_lantern",
        "name": "Tonberry Grudge Lantern",
        "type": "biological",
        "allowed_slots": ["ocular", "arm_left", "left_arm"],
        "strain": 12,
        "col_cost": 3100,
        "stat_bonuses": {"WIS": 2},
        "description": "Bioluminescent green soul-organ harvested from a Master Tonberry that stores karmic battle-malice.",
        "effect": "Everyone's Grudge: Adds +1d8 Karmic Psychic/True damage to melee strikes and grants +2 Critical Hit threat range"
    },
    "zinogre_fulgur_capacitor": {
        "key": "zinogre_fulgur_capacitor",
        "name": "Zinogre Fulgur-Capacitor",
        "type": "biological",
        "allowed_slots": ["spine", "dermal", "torso"],
        "strain": 15,
        "col_cost": 3400,
        "stat_bonuses": {"DEX": 2, "STR": 1},
        "description": "Symbiotic Thunderbug chitin shell from a Monster Hunter Zinogre that supercharges nerves with blue lightning.",
        "effect": "Thunderlord State: +15ft Movement Speed, Lightning Immunity, and +1d10 Lightning damage on all melee attacks"
    },
    "rathalos_flame_marrow_sac": {
        "key": "rathalos_flame_marrow_sac",
        "name": "Rathalos Flame-Marrow Sac",
        "type": "biological",
        "allowed_slots": ["torso", "spine"],
        "strain": 14,
        "col_cost": 3000,
        "stat_bonuses": {"STR": 2, "CON": 1},
        "description": "Combustible wyvern-fire organ from a Monster Hunter Rathalos ('King of the Skies').",
        "effect": "Wyvern-Fireball Breath (30ft range, 3d8 Fire in 10ft radius) & +50% Fire Resistance"
    },
    "gleam_eyes_demonic_horn": {
        "key": "gleam_eyes_demonic_horn",
        "name": "Gleam Eyes Demonic Horn",
        "type": "biological",
        "allowed_slots": ["head", "neural"],
        "strain": 17,
        "col_cost": 4400,
        "stat_bonuses": {"STR": 2, "CON": 2},
        "description": "Curved azure demon-horn harvested from the SAO Floor 74 Boss 'The Gleam Eyes'.",
        "effect": "+2 STR/CON, Intimidating Boss Aura, and Azure Demon-Flame Wave (2d10 Force/Fire ranged slash)"
    },
    "pneuma_filter_gill_lung": {
        "key": "pneuma_filter_gill_lung",
        "name": "Pneuma-Filter Gill-Lung",
        "type": "biological",
        "allowed_slots": ["torso", "dermal"],
        "strain": 10,
        "col_cost": 1750,
        "stat_bonuses": {"CON": 2},
        "description": "Amphibious Aboleth/Chuul gill-filament membrane that filters underwater oxygen and toxic coal-mine gases.",
        "effect": "Amphibious Water-Breathing & complete immunity to Centralia sulfur/carbon-monoxide and inhaled gas hazards"
    }
}

BODY_GRAFT_SLOTS = [
    "arm_left", "arm_right", "leg_left", "leg_right", "spine", "ocular", "dermal", "neural",
    "head", "torso", "left_arm", "right_arm", "legs"
]

SLOT_ALIASES = {
    "head": "neural",
    "eyes": "ocular",
    "torso": "dermal",
    "chest": "dermal",
    "left_arm": "arm_left",
    "right_arm": "arm_right",
    "legs": "leg_left"
}

HARMONIZATION_FEATS = {
    "leyline_conduits": {
        "name": "Leyline Conduits",
        "tier": 1,
        "description": "Gold-threaded conduits woven through bone negate the spellcasting interference of 1 installed Golem-Graft.",
        "effect": "Negates the -2 Arcane DC penalty for 1 installed Golem-Graft."
    },
    "aether_infused_prosthetic": {
        "name": "Aether-Infused Prosthetic",
        "tier": 2,
        "description": "Channel spells directly through metallic limbs, turning golem prosthetics into arcane focuses.",
        "effect": "+1d4 force/elemental damage to touch and ranged spells channeled through grafts."
    },
    "overclocked_matrix": {
        "name": "Overclocked Matrix",
        "tier": 3,
        "description": "Temporarily push cybernetic capacity past safe limits to cast without standard resource drain.",
        "effect": "Once per encounter, spend 10 Graft Strain to cast an active spell without consuming mana/flux."
    }
}

def ensure_graft_system(player_state):
    """Initializes or returns graft_system dict on player_state."""
    if not isinstance(player_state, dict):
        return {"installed_grafts": {}, "harmonized_grafts": []}
    graft_sys = player_state.setdefault("graft_system", {})
    if not isinstance(graft_sys, dict):
        graft_sys = {}
        player_state["graft_system"] = graft_sys
    graft_sys.setdefault("installed_grafts", {})
    graft_sys.setdefault("harmonized_grafts", [])
    return graft_sys

def get_max_graft_strain(player_state):
    """
    Max Graft Capacity = (CON * 2) + (Level * 3) + Racial/Feat Tolerance Bonus.
    """
    stats = player_state.get("stats", {})
    con_val = stats.get("CON", 10)
    level_val = player_state.get("level", 1)
    
    bonus = 0
    race_str = str(player_state.get("race", "")).lower()
    feats_str = " ".join([str(f).lower() for f in player_state.get("feats", [])])
    if "cyborg" in race_str or "innate graft-tolerance" in feats_str:
        bonus += 15
        
    return (con_val * 2) + (level_val * 3) + bonus

def get_current_graft_strain(player_state):
    """
    Calculates total strain from all currently installed golem-grafts.
    """
    grafts = player_state.get("graft_system", {}).get("installed_grafts", {})
    total_strain = 0
    if isinstance(grafts, dict):
        for slot, graft_data in grafts.items():
            if isinstance(graft_data, dict):
                total_strain += int(graft_data.get("strain", 0))
    elif isinstance(grafts, list):
        for g in grafts:
            if isinstance(g, dict):
                total_strain += int(g.get("strain", 0))
    return total_strain

def get_graft_rejection_status(player_state):
    """
    Checks if player is suffering from 'System Rejection' due to exceeding Strain capacity.
    """
    max_strain = get_max_graft_strain(player_state)
    cur_strain = get_current_graft_strain(player_state)
    overflow = max(0, cur_strain - max_strain)

    if overflow == 0:
        return {
            "status": "Stable",
            "label": "🟢 System Stable",
            "is_rejecting": False,
            "overflow": 0,
            "hp_drain": 0,
            "save_penalty": 0,
            "description": "Bio-mechanical interfaces operating within physiological tolerances."
        }
    else:
        hp_drain = overflow * 2
        save_penalty = 2
        return {
            "status": "System Rejection",
            "label": f"🔴 System Rejection (Overflow: +{overflow} Strain)",
            "is_rejecting": True,
            "overflow": overflow,
            "hp_drain": hp_drain,
            "save_penalty": save_penalty,
            "description": f"Excessive cybernetic strain is poisoning organic flesh! Suffering -{hp_drain} Max HP and -{save_penalty} to all saving throws."
        }

def calculate_player_strain(player_state):
    """
    Convenience method calculating current strain, max capacity, and rejection status.
    """
    max_strain = get_max_graft_strain(player_state)
    cur_strain = get_current_graft_strain(player_state)
    rejection = get_graft_rejection_status(player_state)
    return {
        "max_strain": max_strain,
        "current_strain": cur_strain,
        "is_overloaded": rejection["is_rejecting"],
        "rejection": rejection
    }

def install_graft(player_state, graft_key, body_slot, surgeon_fee_col=None):
    """
    Surgically installs a Golem-Graft into a designated body slot during safe-zone clinic downtime.
    """
    if graft_key not in CANONICAL_GRAFTS:
        return {"success": False, "message": f"Unknown graft key '{graft_key}'."}

    graft_def = CANONICAL_GRAFTS[graft_key]

    canonical_slot = SLOT_ALIASES.get(body_slot.lower(), body_slot.lower())
    if body_slot not in BODY_GRAFT_SLOTS and canonical_slot not in BODY_GRAFT_SLOTS:
        return {"success": False, "message": f"Invalid body slot '{body_slot}'."}

    allowed = [s.lower() for s in graft_def["allowed_slots"]]
    allowed_canonical = [SLOT_ALIASES.get(s, s) for s in allowed]
    if body_slot.lower() not in allowed and canonical_slot not in allowed and canonical_slot not in allowed_canonical:
        allowed_str = ", ".join(graft_def["allowed_slots"])
        return {"success": False, "message": f"{graft_def['name']} can only be installed in: {allowed_str}."}
    body_slot = canonical_slot

    # Ensure graft_system data container
    if "graft_system" not in player_state or not isinstance(player_state["graft_system"], dict):
        player_state["graft_system"] = {
            "installed_grafts": {},
            "current_strain": 0,
            "max_strain": get_max_graft_strain(player_state)
        }

    installed = player_state["graft_system"].setdefault("installed_grafts", {})

    if body_slot in installed and installed[body_slot]:
        existing_name = installed[body_slot].get("name", "Graft")
        return {"success": False, "message": f"Body slot '{body_slot}' is already occupied by '{existing_name}'. Extract it first."}

    # Verify Col
    cost = graft_def["col_cost"] if surgeon_fee_col is None else int(surgeon_fee_col)
    player_col = player_state.get("col", 0)
    if player_col < cost:
        return {"success": False, "message": f"Insufficient Col for surgery (Requires {cost:,} Col, has {player_col:,} Col)."}

    # Deduct Col
    player_state["col"] = player_col - cost

    # Install
    graft_record = {
        "key": graft_key,
        "name": graft_def["name"],
        "type": graft_def.get("type", "golem"),
        "slot": body_slot,
        "strain": graft_def["strain"],
        "stat_bonuses": graft_def["stat_bonuses"],
        "effect": graft_def["effect"],
        "description": graft_def["description"]
    }
    installed[body_slot] = graft_record

    # Apply permanent stat bonuses
    stats = player_state.setdefault("stats", {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10})
    for stat, bonus in graft_def["stat_bonuses"].items():
        if stat in stats:
            stats[stat] += bonus

    # Update strain tracking
    cur_strain = get_current_graft_strain(player_state)
    max_strain = get_max_graft_strain(player_state)
    player_state["graft_system"]["current_strain"] = cur_strain
    player_state["graft_system"]["max_strain"] = max_strain

    rejection = get_graft_rejection_status(player_state)

    log = (
        f"[SURGERY SUCCESS: Installed {graft_def['name']} into {body_slot.title()}! "
        f"Cost: {cost:,} Col | Strain: {cur_strain}/{max_strain} ({rejection['label']}) | "
        f"Bonuses: {graft_def['effect']}]"
    )

    return {
        "success": True,
        "graft": graft_record,
        "cost": cost,
        "current_strain": cur_strain,
        "max_strain": max_strain,
        "rejection": rejection,
        "log": log
    }

def remove_graft(player_state, body_slot, removal_fee_col=500):
    """
    Surgically extracts an installed Golem-Graft, freeing body slot and strain.
    """
    graft_sys = player_state.get("graft_system", {})
    installed = graft_sys.get("installed_grafts", {})

    if body_slot not in installed or not installed[body_slot]:
        return {"success": False, "message": f"No graft installed in slot '{body_slot}'."}

    player_col = player_state.get("col", 0)
    fee = int(removal_fee_col)
    if player_col < fee:
        return {"success": False, "message": f"Insufficient Col for surgical extraction (Requires {fee:,} Col)."}

    player_state["col"] = player_col - fee
    graft_record = installed.pop(body_slot)

    # Revert stat bonuses
    stats = player_state.setdefault("stats", {})
    for stat, bonus in graft_record.get("stat_bonuses", {}).items():
        if stat in stats:
            stats[stat] = max(1, stats[stat] - bonus)

    # Update strain tracking
    cur_strain = get_current_graft_strain(player_state)
    max_strain = get_max_graft_strain(player_state)
    graft_sys["current_strain"] = cur_strain
    graft_sys["max_strain"] = max_strain

    # Return salvage scrap to inventory
    inv = player_state.setdefault("inventory", [])
    salvage_name = f"Extracted {graft_record['name']} Core"
    inv.append({
        "name": salvage_name,
        "rarity": "Rare",
        "durability": 50,
        "max_durability": 100,
        "qty": 1,
        "desc": f"Extracted cybernetic prosthetic salvaged from {body_slot}."
    })

    log = f"[SURGERY EXTRACT: Removed {graft_record['name']} from {body_slot}. Fee: {fee:,} Col | Strain reduced to {cur_strain}/{max_strain}]"

    return {
        "success": True,
        "removed_graft": graft_record,
        "fee": fee,
        "current_strain": cur_strain,
        "max_strain": max_strain,
        "salvaged_item": salvage_name,
        "log": log
    }

def calculate_spellcasting_graft_penalty(player_state):
    """
    Calculates Arcane DC / spell attack penalty caused by installed metal/golem grafts.
    Baseline: -2 per installed graft for spellcasters (Mage, Cleric, Psion).
    Feat 'Leyline Conduits': negates penalty for 1 graft.
    Graft 'Leyline Conduit Spine': harmonizes 2 grafts.
    """
    p_class = normalize_class_key(player_state.get("class", "warrior"))
    is_caster = p_class in ["mage", "cleric", "psion", "aether_slinger"]

    if not is_caster:
        return {"penalty": 0, "total_grafts": 0, "net_grafts": 0, "harmonized": 0, "net_unharmonized": 0}

    installed = player_state.get("graft_system", {}).get("installed_grafts", {})

    # Only count metallic/golem/tech grafts for spellcaster penalty (biological grafts do not induce Arcane Spell Failure)
    count = sum(1 for g in installed.values() if isinstance(g, dict) and g.get("type") != "biological")

    if count == 0:
        return {"penalty": 0, "net_grafts": 0, "harmonized": 0}

    # Check for harmonization feats / spinal conduit
    harmonized = 0
    feats = [str(f).lower() for f in player_state.get("feats", [])]
    if any("leyline conduit" in f for f in feats) or any("bio-arcane conduit" in f for f in feats) or any("synthetic somatics" in f for f in feats):
        harmonized += 2

    # Check if Leyline Conduit Spine installed
    if "spine" in installed and installed["spine"].get("key") == "leyline_conduit_spine":
        harmonized += 2

    net_unharmonized = max(0, count - harmonized)
    penalty = net_unharmonized * 2

    return {
        "penalty": penalty,
        "total_grafts": count,
        "harmonized": harmonized,
        "net_unharmonized": net_unharmonized
    }


# =====================================================================
# ABILITY FUSION PROTOCOL (THE DUAL SYSTEM)
# =====================================================================

def fuse_abilities(player_state, component_a_name, component_b_name, custom_fused_name=None, custom_desc=None, custom_mechanics=None):
    """
    Implements V2's Ability Fusion Protocol:
    Combines two skills/abilities (component_a_name and component_b_name), removes the two
    previous base skills from active skills/spells/feats, archives them in
    `player['archived_base_skills']` so they can be relearned later if needed, and replaces
    them with a new `[Fusion] <Name>` skill in `player['skills']`, `player['feats']`, and
    `player['fused_abilities']`.
    """
    if not isinstance(player_state, dict):
        return {"success": False, "message": "Invalid player state."}
        
    fused_abilities = player_state.setdefault("fused_abilities", [])
    skills_dict = player_state.setdefault("skills", {})
    spells_list = player_state.setdefault("spells", [])
    feats_list = player_state.setdefault("feats", [])
    archived_base = player_state.setdefault("archived_base_skills", {})
    
    clean_a = str(component_a_name).strip()
    clean_b = str(component_b_name).strip()
    
    if not clean_a or not clean_b:
        return {"success": False, "message": "Ability Fusion requires two distinct components."}
        
    if clean_a.lower() == clean_b.lower():
        return {"success": False, "message": "Cannot fuse an ability with itself."}
        
    if not custom_fused_name:
        first_word = clean_a.replace("[Fusion]", "").strip().split()[0] if clean_a else "Aether"
        second_word = clean_b.replace("[Fusion]", "").strip().split()[-1] if clean_b else "Burst"
        clean_fused = f"{first_word}-{second_word} Convergence"
    else:
        raw_custom = custom_fused_name.strip()
        if raw_custom.startswith("[") and raw_custom.endswith("]") and not raw_custom.lower().startswith("[fusion]"):
            raw_custom = raw_custom[1:-1].strip()
        if raw_custom.lower().startswith("[fusion]"):
            clean_fused = raw_custom[len("[fusion]"):].strip()
        else:
            clean_fused = raw_custom
            
    fusion_skill_key = f"[Fusion] {clean_fused}"
        
    if not custom_desc:
        fused_desc = f"Synergistic fusion of [{clean_a}] and [{clean_b}]. Unleashes resonant hybrid arcane-tactical force."
    else:
        fused_desc = custom_desc.strip()

    if not custom_mechanics:
        fused_mech = (
            f"• Fusion Components: {clean_a} + {clean_b}\n"
            f"• Power Rating: Tier 3 Fused Convergence Skill\n"
            f"• Game Mechanics: Combines the primary tactical and elemental effects of [{clean_a}] and [{clean_b}] into a single Standard Action strike/cast with a +2 Synergy bonus to attack/DC and +1d8 bonus resonance damage."
        )
    else:
        fused_mech = custom_mechanics.strip()
        
    # Check if already fused
    for fa in fused_abilities:
        if isinstance(fa, dict) and fa.get("name", "").lower() == clean_fused.lower():
            return {"success": False, "message": f"Technique '{clean_fused}' has already been forged in the Matrix."}

    # Consume and archive Component A and Component B from skills, spells, and feats
    consumed_masteries = []
    consumed_from_spells = False

    for comp_name in (clean_a, clean_b):
        comp_low = comp_name.lower()
        found_skill_data = None
        matched_skill_keys = [k for k in list(skills_dict.keys()) if k.lower() == comp_low]
        for mk in matched_skill_keys:
            s_entry = skills_dict.pop(mk, None)
            if isinstance(s_entry, dict):
                m_val = int(s_entry.get("mastery", 1))
                consumed_masteries.append(m_val)
                found_skill_data = s_entry
            else:
                consumed_masteries.append(1)
                found_skill_data = {"mastery": 1, "description": str(s_entry or "")}

        # Check spells
        matched_spells = [sp for sp in list(spells_list) if str(sp).strip().lower() == comp_low or str(sp).strip("[]").lower() == comp_low]
        for msp in matched_spells:
            spells_list.remove(msp)
            consumed_from_spells = True

        # Check feats
        matched_feats = [ft for ft in list(feats_list) if str(ft).strip().lower() == comp_low or str(ft).strip("[]").lower() == comp_low]
        for mft in matched_feats:
            feats_list.remove(mft)

        # Archive the base skill so the player can relearn it later if needed
        if not comp_name.lower().startswith("[fusion]"):
            prev_arch = archived_base.get(comp_name, {})
            archived_base[comp_name] = {
                "name": comp_name,
                "previous_mastery": found_skill_data.get("mastery", prev_arch.get("previous_mastery", 1)) if isinstance(found_skill_data, dict) else 1,
                "description": (
                    found_skill_data.get("description", "")
                    if isinstance(found_skill_data, dict) and found_skill_data.get("description")
                    else prev_arch.get("description", f"Foundational base skill ({comp_name}) previously fused into {fusion_skill_key}.")
                ),
                "fused_into": fusion_skill_key,
                "was_spell": bool(matched_spells) or prev_arch.get("was_spell", False),
            }

    # Calculate combined mastery for the new [Fusion] Skill
    if len(consumed_masteries) >= 2:
        m1, m2 = consumed_masteries[0], consumed_masteries[1]
        combined_mastery = min(1000, max(m1, m2) + max(10, min(m1, m2) // 2))
    elif len(consumed_masteries) == 1:
        combined_mastery = min(1000, consumed_masteries[0] + 15)
    else:
        combined_mastery = 50

    tier_label = get_skill_tier(combined_mastery) if "get_skill_tier" in globals() else "Apprentice"
    unlocked_ms = [th for th in (50, 100, 250, 500, 750, 1000) if combined_mastery >= th]

    # Insert replacement [Fusion] skill into player_state['skills']
    skills_dict[fusion_skill_key] = {
        "mastery": combined_mastery,
        "tier": tier_label,
        "description": f"[Fused from {clean_a} + {clean_b}] {fused_desc}",
        "is_fusion": True,
        "components": [clean_a, clean_b],
        "milestones_unlocked": unlocked_ms
    }

    # Replace any slotted component references in active Matrix memory
    slotted_container = player_state.get("slotted_abilities")
    if isinstance(slotted_container, dict) and isinstance(slotted_container.get("active"), list):
        new_active = []
        replaced_slot = False
        for sl in slotted_container["active"]:
            if str(sl).strip().lower() in (clean_a.lower(), clean_b.lower()):
                if not replaced_slot and fusion_skill_key not in new_active:
                    new_active.append(fusion_skill_key)
                    replaced_slot = True
            else:
                new_active.append(sl)
        slotted_container["active"] = new_active
            
    record = {
        "name": clean_fused,
        "skill_key": fusion_skill_key,
        "components": [clean_a, clean_b],
        "description": fused_desc,
        "mechanics": fused_mech,
        "mastery": combined_mastery,
        "tier": "Fused",
        "power_rating": 3
    }
    fused_abilities.append(record)
    
    # Add [Fusion] skill to feats (and spells if a spell component was consumed)
    if fusion_skill_key not in feats_list and clean_fused not in feats_list:
        feats_list.append(fusion_skill_key)
    if consumed_from_spells and fusion_skill_key not in spells_list:
        spells_list.append(fusion_skill_key)
        
    # Award XP
    player_state["xp"] = player_state.get("xp", 0) + 15
    
    return {
        "success": True,
        "fused_name": clean_fused,
        "fusion_skill_key": fusion_skill_key,
        "consumed_components": [clean_a, clean_b],
        "combined_mastery": combined_mastery,
        "technique": record,
        "xp_awarded": 15,
        "log": f"🔮 [ABILITY FUSION SUCCESS: Combined & replaced '{clean_a}' + '{clean_b}' -> '{fusion_skill_key}' (Mastery {combined_mastery}/1000, +15 XP)!]"
    }

def get_fused_abilities(player_state):
    """Returns list of all fused abilities registered on player."""
    if not isinstance(player_state, dict):
        return []
    return player_state.get("fused_abilities", [])


def get_relearnable_base_skills(player_state):
    """
    Returns a list of Base Skills that the player can relearn.
    Includes:
      1. Base skills previously consumed by Ability Fusion (`archived_base_skills` and `fused_abilities.components`).
      2. Canonical foundational skills from `CANONICAL_MILESTONES` not currently in `player_state['skills']`.
    """
    if not isinstance(player_state, dict):
        return []

    current_skill_lows = {str(k).strip().lower() for k in player_state.get("skills", {}).keys()}
    relearnable = []
    seen = set()

    # 1. Consumed base skills from archived_base_skills
    archived = player_state.get("archived_base_skills", {})
    if isinstance(archived, dict):
        for s_name, s_info in archived.items():
            clean_n = str(s_name).strip()
            if not clean_n or clean_n.lower().startswith("[fusion]"):
                continue
            if clean_n.lower() not in current_skill_lows and clean_n.lower() not in seen:
                seen.add(clean_n.lower())
                relearnable.append({
                    "name": clean_n,
                    "description": s_info.get("description", f"Base skill previously fused into {s_info.get('fused_into', 'a [Fusion] Skill')}."),
                    "previous_mastery": s_info.get("previous_mastery", 1),
                    "fused_into": s_info.get("fused_into", ""),
                    "was_fused": True
                })

    # 2. Check components recorded inside fused_abilities (for backwards compatibility with older saves)
    for fa in player_state.get("fused_abilities", []):
        if isinstance(fa, dict):
            f_into = fa.get("skill_key") or f"[Fusion] {fa.get('name', 'Convergence')}"
            for comp in fa.get("components", []):
                clean_c = str(comp).strip()
                if not clean_c or clean_c.lower().startswith("[fusion]"):
                    continue
                if clean_c.lower() not in current_skill_lows and clean_c.lower() not in seen:
                    seen.add(clean_c.lower())
                    relearnable.append({
                        "name": clean_c,
                        "description": f"Base component skill previously fused into {f_into}.",
                        "previous_mastery": 1,
                        "fused_into": f_into,
                        "was_fused": True
                    })

    # 3. Canonical base skills from CANONICAL_MILESTONES not currently known
    for canon_skill in globals().get("CANONICAL_MILESTONES", {}).keys():
        clean_canon = str(canon_skill).strip()
        if clean_canon.lower() not in current_skill_lows and clean_canon.lower() not in seen:
            seen.add(clean_canon.lower())
            relearnable.append({
                "name": clean_canon,
                "description": f"Foundational Crucible discipline ({clean_canon}). Can be trained from Novice (1/1000).",
                "previous_mastery": 0,
                "fused_into": "",
                "was_fused": False
            })

    return relearnable


def relearn_base_skill(player_state, skill_name, starting_mastery=1):
    """
    Relearns a Base Skill (such as one previously consumed in an Ability Fusion)
    without removing the player's `[Fusion]` skill.
    Starts the relearned base skill at Novice (`starting_mastery`, default 1/1000).
    """
    if not isinstance(player_state, dict):
        return {"success": False, "message": "Invalid player state."}

    clean_name = str(skill_name or "").strip()
    if not clean_name:
        return {"success": False, "message": "Skill name is required to relearn a base skill."}

    if clean_name.lower().startswith("[fusion]"):
        return {"success": False, "message": "Only Base Skills can be relearned directly; [Fusion] skills must be forged via the Ability Fusion Protocol."}

    skills_dict = player_state.setdefault("skills", {})
    for existing_k in skills_dict.keys():
        if existing_k.lower() == clean_name.lower():
            return {"success": False, "message": f"Base skill '{existing_k}' is already active in your Skill Matrix."}

    archived = player_state.get("archived_base_skills", {})
    arch_entry = None
    if isinstance(archived, dict):
        for k, v in archived.items():
            if k.lower() == clean_name.lower():
                arch_entry = v
                break

    init_m = max(1, min(1000, int(starting_mastery)))
    tier_label = get_skill_tier(init_m) if "get_skill_tier" in globals() else "Novice"
    desc = (
        arch_entry.get("description")
        if isinstance(arch_entry, dict) and arch_entry.get("description")
        else f"Relearned foundational base skill ({clean_name}). Progresses along the 1–1000 Mastery continuum."
    )

    skills_dict[clean_name] = {
        "mastery": init_m,
        "tier": tier_label,
        "description": desc,
        "milestones_unlocked": [th for th in (50, 100, 250, 500, 750, 1000) if init_m >= th],
        "relearned": True
    }

    if isinstance(arch_entry, dict) and arch_entry.get("was_spell"):
        spells_list = player_state.setdefault("spells", [])
        if clean_name not in spells_list:
            spells_list.append(clean_name)

    return {
        "success": True,
        "skill_name": clean_name,
        "mastery": init_m,
        "tier": tier_label,
        "message": f"🔄 Relearned Base Skill '{clean_name}' at {tier_label} Mastery ({init_m}/1000)!"
    }




# =====================================================================
# ABILITY & SPELL SLOTTING / MATRIX MEMORY ENGINE
# =====================================================================

def ensure_ability_matrix(player_state):
    """Initializes or returns slotted_abilities dict on player_state."""
    if not isinstance(player_state, dict):
        return {"max_slots": 5, "active": []}
    max_slots = get_max_ability_slots(player_state)
    matrix = player_state.setdefault("slotted_abilities", {
        "max_slots": max_slots,
        "active": []
    })
    if not isinstance(matrix, dict):
        matrix = {"max_slots": max_slots, "active": []}
        player_state["slotted_abilities"] = matrix
    matrix.setdefault("max_slots", max_slots)
    matrix.setdefault("active", [])
    return matrix

def get_max_ability_slots(player_state):
    """
    Slot Caps:
    - Levels 1–10: 5 Active Slots
    - Levels 11–20: 10 Active Slots
    - +1 bonus slot if 'Neural Overclock Cortex' is installed
    """
    lvl = player_state.get("level", 1)
    base_slots = 10 if lvl >= 11 else 5

    # Check for neural graft bonus
    installed = player_state.get("graft_system", {}).get("installed_grafts", {})
    bonus_slots = 0
    if "neural" in installed and installed["neural"].get("key") == "neural_overclock_cortex":
        bonus_slots += 1

    return base_slots + bonus_slots

def get_slotted_abilities(player_state):
    """
    Retrieves current list of actively slotted spells and techniques.
    """
    matrix = player_state.get("slotted_abilities", {})
    if isinstance(matrix, dict):
        active = matrix.get("active", [])
        if isinstance(active, list):
            return active
    elif isinstance(matrix, list):
        return matrix
    return []

def get_available_abilities(player_state):
    """
    Aggregates all unlocked active abilities available to be slotted into the Matrix.
    Combines:
    - Active Sword Skills / Techniques from player['spells']
    - Active Techniques from player['feats'] (filtering out purely passive feats)
    - Racial active abilities (e.g. Telekinetic Grip, Psionic Shielding)
    """
    available = []
    seen = set()

    def add_ability(name, source="Ability"):
        clean_name = name.split("(")[0].split(":")[0].strip()
        if clean_name and clean_name.lower() not in seen:
            seen.add(clean_name.lower())
            available.append({"name": clean_name, "raw": name, "source": source})

    # Spells and active sword skills
    for s in player_state.get("spells", []):
        add_ability(str(s), source="Spell / Technique")

    # Racial abilities
    for r in player_state.get("racial_abilities", []):
        r_str = str(r)
        if "Flaw" not in r_str:
            add_ability(r_str, source="Racial Power")

    # Active Feats (filtering out purely passive perks)
    for f in player_state.get("feats", []):
        f_str = str(f)
        f_lower = f_str.lower()
        if any(w in f_lower for w in ["active", "skill", "strike", "burst", "slash", "charge", "wave", "blast", "toss", "step", "shield"]):
            if not any(w in f_lower for w in ["passive", "evolution:"]):
                add_ability(f_str, source="Feat / Maneuver")

    return available

def slot_ability(player_state, ability_name):
    """
    Slots an ability into active matrix memory.
    """
    max_slots = get_max_ability_slots(player_state)
    matrix = player_state.setdefault("slotted_abilities", {
        "max_slots": max_slots,
        "active": []
    })
    if not isinstance(matrix.get("active"), list):
        matrix["active"] = []

    matrix["max_slots"] = max_slots
    active = matrix["active"]

    clean_target = ability_name.split("(")[0].split(":")[0].strip()

    # Check if already slotted
    for item in active:
        if item.lower() == clean_target.lower():
            return {"success": False, "message": f"'{clean_target}' is already slotted in Active Memory."}

    if len(active) >= max_slots:
        return {
            "success": False,
            "message": f"Active Memory is full ({len(active)}/{max_slots} slots). Unslot an ability first."
        }

    active.append(clean_target)
    return {
        "success": True,
        "slotted_ability": clean_target,
        "used_slots": len(active),
        "max_slots": max_slots,
        "message": f"Slotted '{clean_target}' into Active Memory ({len(active)}/{max_slots})."
    }

def unslot_ability(player_state, ability_name):
    """
    Unslots an ability from active matrix memory.
    """
    matrix = player_state.setdefault("slotted_abilities", {"max_slots": get_max_ability_slots(player_state), "active": []})
    active = matrix.setdefault("active", [])

    clean_target = ability_name.split("(")[0].split(":")[0].strip().lower()
    match_idx = -1
    for idx, item in enumerate(active):
        if item.split("(")[0].split(":")[0].strip().lower() == clean_target:
            match_idx = idx
            break

    if match_idx == -1:
        return {"success": False, "message": f"'{ability_name}' is not currently slotted."}

    removed = active.pop(match_idx)
    return {
        "success": True,
        "unslotted_ability": removed,
        "used_slots": len(active),
        "max_slots": matrix.get("max_slots", 5),
        "message": f"Unslotted '{removed}' from Active Memory."
    }


def is_ability_slotted(player_state, ability_name):
    """
    Verifies if a specific ability or technique is loaded in active memory.
    """
    active = get_slotted_abilities(player_state)
    target = ability_name.split("(")[0].split(":")[0].strip().lower()
    return any(a.split("(")[0].split(":")[0].strip().lower() == target for a in active)


# =====================================================================
# 🤝 PHASE M5: AUTONOMOUS COMPANION PROGRESSION & TACTICAL ORDERS
# =====================================================================

COMPANION_TACTICAL_STANCES = {
    "overwatch_hacking": {
        "key": "overwatch_hacking",
        "name": "Leyline Overwatch",
        "label": "👁️ Leyline Overwatch",
        "icon": "👁️",
        "short_desc": "Scans enemy mana-signatures and physical seams using runic lens.",
        "tactical_effect": "Debuffs targeted enemy AC by -2 and reveals structural mana-fractures.",
        "combat_log_tag": "[REN OVERWATCH]",
        "stat_bonus": {"target_ac_mod": -2, "crit_threat_bonus": 1}
    },
    "suppression_fire": {
        "key": "suppression_fire",
        "name": "MageTech Arc Suppression",
        "label": "⚡ MageTech Arc Suppression",
        "icon": "⚡",
        "short_desc": "Fires crackling lightning-mana runes from his brass MageTech Caster firearm.",
        "tactical_effect": "Enemies rushing into melee must make a DC 13 CON save or become Staggered.",
        "combat_log_tag": "[REN SUPPRESSION]",
        "stat_bonus": {"disruption_dc": 13, "condition": "Staggered"}
    },
    "full_evasion": {
        "key": "full_evasion",
        "name": "Aetheric Phase-Veil",
        "label": "🌫️ Aetheric Phase-Veil",
        "icon": "🌫️",
        "short_desc": "Weaves spatial camouflage and takes cover behind ancient stone masonry.",
        "tactical_effect": "Ren is immune to single-target attacks; +4 to all defensive saves.",
        "combat_log_tag": "[REN EVASION]",
        "stat_bonus": {"defense_save_bonus": 4, "untargetable": True}
    },
    "utility_rigging": {
        "key": "utility_rigging",
        "name": "Arcane Artificing & Mending",
        "label": "✨ Arcane Artificing & Mending",
        "icon": "✨",
        "short_desc": "Channels mending runes into gear, sets traps, or harvests crystallite scrap.",
        "tactical_effect": "Restores +15 gear durability to worn weapon/armor or scavenges +1 extra crafting part.",
        "combat_log_tag": "[REN UTILITY]",
        "stat_bonus": {"durability_patch": 15, "salvage_bonus": 1}
    }
}

COMPANION_LEVEL_PERKS = {
    2: {
        "name": "Telemetry Ping v1.0",
        "type": "Passive",
        "desc": "+1 to Banki's attack rolls against scanned targets via mana resonance."
    },
    3: {
        "name": "Mesh Exploitation Mastery",
        "type": "Technique",
        "desc": "Ren can perceive hidden aetheric doors and safe-zone mana fountains."
    },
    4: {
        "name": "Aetheric Shield Pulse",
        "type": "Reaction",
        "desc": "When Banki takes lethal damage, Ren emits an arcane kinetic pulse granting +20 temporary HP."
    },
    5: {
        "name": "Overclocked Stun Burst",
        "type": "Active",
        "desc": "MageTech caster discharge jumps to 2 additional adjacent targets with crackling aether."
    },
    6: {
        "name": "Geometry Desync Hack",
        "type": "Ultimate",
        "desc": "Locks an enemy construct in a localized temporal stasis rune for 1 turn."
    }
}

def get_default_ren_companion():
    """
    Returns the canonical companion profile for Ren Sasaki.
    """
    return {
        "name": "Ren Sasaki",
        "title": "Aether-Scholar & MageTech Artificer",
        "level": 3,
        "xp": 450,
        "next_level_xp": 900,
        "hp": 35,
        "max_hp": 35,
        "stance": "overwatch_hacking",
        "morale": "Steady",
        "loadout": {
            "main_hand": "Aether-Etched MageTech Caster (Runic Firearm)",
            "tool": "Runic Scribe Slate (Aether-Grid Focus)",
            "deck": "Runic Scribe Slate (Aether-Grid Focus)",
            "armor": "Woven Leyline Duster (Enchanted Cloth, DR 1)",
            "chest": "Woven Leyline Duster (Enchanted Cloth, DR 1)"
        },
        "equipped": {
            "main_hand": "Aether-Etched MageTech Caster (Runic Firearm)",
            "tool": "Runic Scribe Slate (Aether-Grid Focus)",
            "deck": "Runic Scribe Slate (Aether-Grid Focus)",
            "armor": "Woven Leyline Duster (Enchanted Cloth, DR 1)",
            "chest": "Woven Leyline Duster (Enchanted Cloth, DR 1)"
        },
        "skills": {
            "Mesh Exploitation": {
                "mastery": 140,
                "tier": "Journeyman",
                "description": "Perceiving spatial seams, leylines, and architectural weaknesses.",
                "milestones_unlocked": ["Logic Buffer Exploit"]
            },
            "Stun-Pistol Marksmanship": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Discharging focused mana-bolts and lightning runes from MageTech firearm.",
                "milestones_unlocked": []
            },
            "Diagnostic Triage": {
                "mastery": 60,
                "tier": "Apprentice",
                "description": "Channelling healing runes and minor aether-salves.",
                "milestones_unlocked": ["Patch Script v1.0"]
            }
        },
        "abilities": [
            "Aura Weakpoint Scan (-2 Enemy AC)",
            "MageTech Stun-Arc Salvo (DC 13 CON save vs Stun)",
            "Aetheric Phase-Veil (Untargetable 1 turn)",
            "Aether-Scrap Extraction (+25% salvage yield)"
        ]
    }

def ensure_companion_profile(player_state):
    """
    Guarantees that player_state has a well-formed 'companions' dictionary.
    Initializes Ren Sasaki if missing or empty.
    """
    if not isinstance(player_state, dict):
        return {}

    companions = player_state.setdefault("companions", {})
    if not isinstance(companions, dict) or not companions:
        companions = {"Ren": get_default_ren_companion()}
        player_state["companions"] = companions
    elif "Ren" not in companions:
        companions["Ren"] = get_default_ren_companion()

    # Normalize Ren's fields
    ren = companions["Ren"]
    if not isinstance(ren, dict):
        ren = get_default_ren_companion()
        companions["Ren"] = ren

    ren.setdefault("name", "Ren Sasaki")
    ren.setdefault("title", "Aether-Scholar & MageTech Artificer")
    ren.setdefault("level", 3)
    ren.setdefault("xp", 450)
    ren.setdefault("next_level_xp", ren.get("level", 3) * 300)
    ren.setdefault("hp", 35)
    ren.setdefault("max_hp", 35)
    ren.setdefault("stance", "overwatch_hacking")
    ren.setdefault("morale", "Steady")
    ren.setdefault("loadout", {
        "main_hand": "Aether-Etched MageTech Caster (Runic Firearm)",
        "tool": "Runic Scribe Slate (Aether-Grid Focus)",
        "deck": "Runic Scribe Slate (Aether-Grid Focus)",
        "armor": "Woven Leyline Duster (Enchanted Cloth, DR 1)",
        "chest": "Woven Leyline Duster (Enchanted Cloth, DR 1)"
    })
    ren.setdefault("equipped", ren.get("loadout", {
        "main_hand": "Aether-Etched MageTech Caster (Runic Firearm)",
        "tool": "Runic Scribe Slate (Aether-Grid Focus)",
        "deck": "Runic Scribe Slate (Aether-Grid Focus)",
        "armor": "Woven Leyline Duster (Enchanted Cloth, DR 1)",
        "chest": "Woven Leyline Duster (Enchanted Cloth, DR 1)"
    }))
    if isinstance(ren.get("equipped"), dict):
        ren["equipped"].setdefault("deck", ren["equipped"].get("tool", "Runic Scribe Slate (Aether-Grid Focus)"))
        ren["equipped"].setdefault("chest", ren["equipped"].get("armor", "Woven Leyline Duster (Enchanted Cloth, DR 1)"))
    ren.setdefault("skills", {
        "Mesh Exploitation": {"mastery": 140, "tier": "Journeyman", "description": "Perceiving spatial seams and leylines.", "milestones_unlocked": ["Logic Buffer Exploit"]},
        "Stun-Pistol Marksmanship": {"mastery": 45, "tier": "Novice", "description": "Discharging lightning runes from MageTech firearm.", "milestones_unlocked": []},
        "Diagnostic Triage": {"mastery": 60, "tier": "Apprentice", "description": "Channelling restorative aether-salves.", "milestones_unlocked": ["Patch Script v1.0"]}
    })
    ren.setdefault("abilities", [
        "Aura Weakpoint Scan (-2 Enemy AC)",
        "MageTech Stun-Arc Salvo (DC 13 CON save vs Stun)",
        "Aetheric Phase-Veil (Untargetable 1 turn)",
        "Aether-Scrap Extraction (+25% salvage yield)"
    ])

    return companions

def get_companion_stances():
    """Returns available tactical stances for companions."""
    return COMPANION_TACTICAL_STANCES

def get_companion(player_state, companion_name="Ren"):
    """Safely retrieves a companion profile."""
    companions = ensure_companion_profile(player_state)
    comp = companions.get(companion_name)
    if not comp:
        for k, v in companions.items():
            if isinstance(v, dict) and (k.lower() == str(companion_name).lower() or str(companion_name).lower() in v.get("name", "").lower()):
                return v
    return comp or companions.get("Ren", get_default_ren_companion())

def set_companion_stance(player_state, companion_name="Ren", stance_key=None):
    """
    Sets the active tactical stance for a party companion.
    Supports either (player_state, companion_name, stance_key) or (player_state, stance_key, companion_name).
    """
    # Flexibly support swapped arguments
    if stance_key is None:
        stance_key = companion_name
        companion_name = "Ren"
    elif companion_name in COMPANION_TACTICAL_STANCES or any(k in str(companion_name).lower() for k in ["overwatch", "suppression", "evasion", "utility", "hacking"]):
        companion_name, stance_key = stance_key, companion_name

    comps = ensure_party_system(player_state)
    comp = comps.get(companion_name)
    if not comp:
        for k, v in comps.items():
            if isinstance(v, dict) and (k.lower() == str(companion_name).lower() or str(companion_name).lower() in v.get("name", "").lower()):
                comp = v
                break
    if not comp:
        # Check if companion_name was actually the stance
        if companion_name in COMPANION_TACTICAL_STANCES:
            comp = comps.get("Ren")
            stance_key = companion_name
        else:
            return {"success": False, "message": f"Companion '{companion_name}' not found."}

    # Available stances for this companion
    comp_stances = comp.get("stances", {})
    if not comp_stances and comp.get("id") == "ren_sasaki":
        comp_stances = COMPANION_TACTICAL_STANCES

    norm_str = str(stance_key).strip().lower()
    norm_clean = norm_str.replace(" ", "_").replace("-", "_")

    matched_key = None
    # 1. Exact or clean match in companion's own stances
    for k in comp_stances:
        if k.lower() == norm_clean or norm_clean in k.lower() or k.lower() in norm_clean:
            matched_key = k
            break
        label = comp_stances[k].get("name", "").lower()
        if norm_clean in label.replace(" ", "_") or norm_str in label:
            matched_key = k
            break

    # 2. Ren legacy fallback keywords if still not matched
    if not matched_key and comp.get("id") == "ren_sasaki":
        if any(w in norm_str for w in ["overwatch", "hack", "scan"]):
            matched_key = "overwatch_hacking"
        elif any(w in norm_str for w in ["suppress", "stun", "burst", "pistol"]):
            matched_key = "suppression_fire"
        elif any(w in norm_str for w in ["evasion", "evade", "hide", "cover"]):
            matched_key = "full_evasion"
        elif any(w in norm_str for w in ["utility", "rig", "repair", "patch", "scavenge"]):
            matched_key = "utility_rigging"

    if not matched_key or matched_key not in comp_stances:
        return {"success": False, "message": f"Unknown tactical stance '{stance_key}' for {comp.get('name', companion_name)}."}

    stance_def = comp_stances[matched_key]
    comp["stance"] = matched_key

    log = f"[TACTICAL DIRECTIVE: {comp['name']} transitioned to {stance_def['label']} — {stance_def['tactical_effect']}]"
    return {
        "success": True,
        "companion": comp["name"],
        "stance": matched_key,
        "stance_info": stance_def,
        "log": log,
        "message": f"Commanded {comp['name']} to assume {stance_def['name']} stance."
    }

def calculate_companion_next_level_xp(level):
    """Next level threshold formula: Level * 300."""
    return max(1, int(level)) * 300

def award_companion_xp(player_state, companion_name="Ren", xp_amount=0):
    """
    Awards XP to companion and triggers level-up progression if threshold reached.
    Supports either (player_state, companion_name, xp_amount) or (player_state, xp_amount, companion_name).
    """
    # Flexibly support swapped arguments
    if isinstance(companion_name, (int, float)) or (isinstance(companion_name, str) and companion_name.isdigit()):
        companion_name, xp_amount = (xp_amount if isinstance(xp_amount, str) else "Ren"), companion_name

    companions = ensure_companion_profile(player_state)
    comp = companions.get(companion_name)
    if not comp:
        for k, v in companions.items():
            if isinstance(v, dict) and (k.lower() == str(companion_name).lower() or str(companion_name).lower() in v.get("name", "").lower()):
                comp = v
                break
    if not comp:
        return {"success": False, "message": f"Companion '{companion_name}' not found."}

    amt = max(0, int(xp_amount))
    cur_xp = comp.get("xp", 0) + amt
    comp["xp"] = cur_xp
    cur_lvl = comp.get("level", 1)
    req_xp = comp.get("next_level_xp", calculate_companion_next_level_xp(cur_lvl))

    leveled_up = False
    new_perks = []
    hp_gains = 0

    while cur_xp >= req_xp:
        cur_lvl += 1
        leveled_up = True
        hp_gain = 8
        hp_gains += hp_gain
        comp["max_hp"] = comp.get("max_hp", 35) + hp_gain
        comp["hp"] = comp["max_hp"]
        comp["level"] = cur_lvl
        req_xp = calculate_companion_next_level_xp(cur_lvl)
        comp["next_level_xp"] = req_xp

        # Award level perk if defined
        if cur_lvl in COMPANION_LEVEL_PERKS:
            perk = COMPANION_LEVEL_PERKS[cur_lvl]
            perk_entry = f"{perk['name']} ({perk['type']}: {perk['desc']})"
            if perk_entry not in comp.get("abilities", []):
                comp.setdefault("abilities", []).append(perk_entry)
                new_perks.append(perk["name"])

        # Advance companion core skill masteries
        skills = comp.setdefault("skills", {})
        for sname, sdata in skills.items():
            if isinstance(sdata, dict):
                old_m = sdata.get("mastery", 1)
                new_m = min(1000, old_m + 25)
                sdata["mastery"] = new_m
                sdata["tier"] = get_mastery_tier(new_m)

    log = ""
    if leveled_up:
        log = (
            f"[COMPANION LEVEL UP: {comp['name']} has reached Level {cur_lvl}! "
            f"(+{hp_gains} Max HP, Now {comp['max_hp']} HP) | Unlocks: {new_perks}]"
        )

    return {
        "success": True,
        "companion": comp["name"],
        "leveled_up": leveled_up,
        "new_level": cur_lvl,
        "current_xp": comp["xp"],
        "next_level_xp": comp["next_level_xp"],
        "hp_gain": hp_gains,
        "unlocked_perks": new_perks,
        "log": log
    }

def update_companion_morale(player_state, companion_name, morale_state):
    """
    Updates companion emotional state / morale ('Panicked', 'Shaken', 'Steady', 'Confident', 'Inspired').
    """
    valid_morales = ["Panicked", "Shaken", "Steady", "Confident", "Inspired"]
    companions = ensure_companion_profile(player_state)
    comp = companions.get(companion_name)
    if not comp:
        return {"success": False, "message": "Companion not found."}

    clean_state = morale_state.strip().title()
    if clean_state not in valid_morales:
        clean_state = "Steady"

    comp["morale"] = clean_state
    return {"success": True, "companion": comp["name"], "morale": clean_state}

def get_companion_combat_action(player_state, companion_name="Ren"):
    """
    Evaluates companion's active stance and generates a deterministic mechanical combat check.
    """
    comp = get_companion(player_state, companion_name)
    stance_key = comp.get("stance", "overwatch_hacking")
    stance_info = COMPANION_TACTICAL_STANCES.get(stance_key, COMPANION_TACTICAL_STANCES["overwatch_hacking"])

    if stance_key == "overwatch_hacking":
        return {
            "stance": stance_key,
            "stance_key": stance_key,
            "target_ac_mod": -2,
            "tag": stance_info["combat_log_tag"],
            "log": f"{stance_info['combat_log_tag']} Scans enemy aura & structural leylines: -2 AC debuff applied to primary target."
        }
    elif stance_key == "suppression_fire":
        return {
            "stance": stance_key,
            "stance_key": stance_key,
            "dc": 13,
            "condition": "Staggered",
            "tag": stance_info["combat_log_tag"],
            "log": f"{stance_info['combat_log_tag']} Discharges MageTech lightning-rune salvo! Target DC 13 CON save vs Staggered."
        }
    elif stance_key == "full_evasion":
        return {
            "stance": stance_key,
            "stance_key": stance_key,
            "untargetable": True,
            "tag": stance_info["combat_log_tag"],
            "log": f"{stance_info['combat_log_tag']} Weaves an aetheric phase-veil into the ruins; immune to single-target attacks."
        }
    elif stance_key == "utility_rigging":
        # Check if Banki has worn gear
        patched = False
        patch_item = "Gear"
        dur_dict = player_state.get("gear_durability", {})
        for slot, item_data in dur_dict.items():
            if isinstance(item_data, dict):
                c_dur = item_data.get("current_durability", 100)
                m_dur = item_data.get("max_durability", 100)
                if c_dur < m_dur:
                    item_data["current_durability"] = min(m_dur, c_dur + 15)
                    patch_item = item_data.get("item", slot)
                    patched = True
                    break
        msg = f"{stance_info['combat_log_tag']} Channels mending runes into {patch_item} (+15 durability restored)." if patched else f"{stance_info['combat_log_tag']} Scavenges +1 extra aether-crystallite from combat debris."
        return {
            "stance": stance_key,
            "stance_key": stance_key,
            "patched": patched,
            "tag": stance_info["combat_log_tag"],
            "log": msg
        }

    return {"stance": "unknown", "stance_key": "unknown", "log": "[REN: Observing situation.]"}


# =====================================================================
# 🏛️ WASHINGTON BOROUGH SAFE-ZONE FACILITIES & SETTLEMENT COMMERCE
# =====================================================================

WASHINGTON_FACILITIES = {
    "iron_spoke_taphouse": {
        "id": "iron_spoke_taphouse",
        "name": "The Iron Spoke Taphouse",
        "icon": "🍺",
        "proprietor": "Torvald Iron-Vein (Deepforged Bouncer & Barkeep)",
        "description": "A fortified roadside tavern built into the stone foundations of an abandoned rail depot. Runic heat-pipes warm the heavy timber tables where mercenaries and scavengers trade rumors.",
        "services": [
            {
                "id": "stew_and_rest",
                "name": "Hearty Marrow Stew & Roasted Grain Draught",
                "cost_col": 150,
                "effect": "Restores 50 HP to Banki, cleanses fatigue, restores companion morale to 'Confident' (+10% accuracy), and grants [Well-Fed] buff."
            },
            {
                "id": "bounty_board",
                "name": "Sector 1 Regional Bounty Board",
                "cost_col": 0,
                "effect": "Inspect available local contracts and barony bounties for Warren County."
            }
        ]
    },
    "arcane_med_bay": {
        "id": "arcane_med_bay",
        "name": "The Arcane Med-Bay & Bio-Clinic",
        "icon": "🏥",
        "proprietor": "Dr. Varek Thorne (Displaced Cyber-Physician)",
        "description": "A sterile, pressurized field clinic humming with life-support conduits and diagnostic holograms. Specializes in emergency flesh repair and bio-mechanical graft integration.",
        "services": [
            {
                "id": "bio_purification",
                "name": "Full Bio-Purification & Flesh Trauma Suture",
                "cost_col": 250,
                "effect": "Completely restores HP to Max, cleanses Bleed, Poison, and Overload conditions, and stabilizes cyber-strain."
            },
            {
                "id": "cyber_surgery",
                "name": "Deepforger Artificer Surgery (Graft Installation)",
                "cost_col": 0,
                "effect": "Install or extract Golem-Grafts using clinical tools."
            }
        ]
    },
    "meiji_scavenger_dump": {
        "id": "meiji_scavenger_dump",
        "name": "The Meiji Scavenger Dump & Material Exchange",
        "icon": "🛒",
        "proprietor": "Kibs 'Nine-Fingers' (Goblinoid Scrap Broker)",
        "description": "A sprawling junkyard warehouse filled with salvaged aether-tech, chassis parts, and raw crafting commodities gathered from Highway 31 and the Oxford line.",
        "inventory": [
            {"name": "Serrated Tripwire Coils", "cost_col": 75, "qty": 5, "desc": "Pre-coiled high-tensile monofilament wire.", "type": "crafting"},
            {"name": "Heavy Highway Snares", "cost_col": 120, "qty": 4, "desc": "High-durability pneumatic limb-clamp snares.", "type": "crafting"},
            {"name": "Anchors and Tension Pins", "cost_col": 50, "qty": 8, "desc": "Steel ground spikes with locking spring-pins.", "type": "crafting"},
            {"name": "Corroded Micro-Capacitor", "cost_col": 150, "qty": 3, "desc": "High-discharge pulse capacitor salvaged from drones.", "type": "crafting"},
            {"name": "Frayed Copper Wiring", "cost_col": 40, "qty": 10, "desc": "Standard conductive copper wiring.", "type": "crafting"},
            {"name": "Rendered Chimera Marrow", "cost_col": 200, "qty": 2, "desc": "Potent scented tallow that lures predatory beasts.", "type": "bait"}
        ]
    }
}

WARREN_COUNTY_BOUNTIES = [
    {
        "id": "bounty_pohatcong_construct",
        "title": "Slay the Rogue Timber-Goliath on Pohatcong Mountain",
        "desc": "A 14-foot corrupted logging construct has gone berserk along the Pohatcong ridge trails, smashing supply wagons.",
        "target": "Rogue Timber-Goliath (Level 3 Field Construct)",
        "location": "Pohatcong Mountain Ridge",
        "reward": "1,200 Col, 450 XP, Grade 2 Titanium Plating x2"
    },
    {
        "id": "bounty_oxford_cables",
        "title": "Recover Stolen Aether-Cables from Oxford Wastes",
        "desc": "Grafted scavengers have severed the municipal power conduits leading into Oxford. Eliminate the marauder squad and secure the cables.",
        "target": "Grafted Scavenger Pack (4x Scrappers)",
        "location": "Oxford Mining District",
        "reward": "850 Col, 350 XP, High-Voltage Capacitor x1"
    },
    {
        "id": "bounty_roaring_rock_stalker",
        "title": "Cull the Glitched Razor-Hound Pack in Roaring Rock",
        "desc": "A feral pack of cyber-mutated canines has established a den near the Roaring Rock reservoir, ambushing couriers.",
        "target": "Alpha Razor-Hound + 3 Packmates",
        "location": "Roaring Rock Park",
        "reward": "1,500 Col, 500 XP, Chitin Fur Mantle x1"
    }
]

def use_taphouse_stew_and_rest(player_state):
    """
    Purchases the hearty stew & draught at The Iron Spoke Taphouse:
    Restores 50 HP, restores companion morale to 'Confident', grants 'Well-Fed'.
    Cost: 150 Col.
    """
    col = player_state.get("col", 0)
    fee = 150
    if col < fee:
        return {"success": False, "message": f"Insufficient Col for stew and rest (Requires {fee} Col, has {col} Col)."}

    player_state["col"] = col - fee
    old_hp = player_state.get("hp", 100)
    max_hp = player_state.get("max_hp", 100)
    healed_hp = min(max_hp, old_hp + 50)
    player_state["hp"] = healed_hp

    # Restore Ren's morale
    companions = ensure_companion_profile(player_state)
    if "Ren" in companions:
        companions["Ren"]["morale"] = "Confident"

    # Add Well-Fed status
    buffs = player_state.setdefault("active_buffs", [])
    if "Well-Fed" not in buffs:
        buffs.append("Well-Fed")

    log = f"[TAPHOUSE REST: Drank roasted grain draught and ate warm marrow stew. Healed to {healed_hp}/{max_hp} HP | Ren Morale: Confident | Fee: 150 Col]"
    return {
        "success": True,
        "hp_healed": healed_hp - old_hp,
        "current_hp": healed_hp,
        "max_hp": max_hp,
        "companion_morale": "Confident",
        "fee": fee,
        "log": log,
        "message": "Ate hearty marrow stew and rested by the hearth."
    }

def use_med_bay_purification(player_state):
    """
    Purchases full bio-purification and flesh suture at Dr. Thorne's Arcane Med-Bay:
    Restores HP to full, clears conditions. Cost: 250 Col.
    """
    col = player_state.get("col", 0)
    fee = 250
    if col < fee:
        return {"success": False, "message": f"Insufficient Col for clinical treatment (Requires {fee} Col, has {col} Col)."}

    player_state["col"] = col - fee
    max_hp = player_state.get("max_hp", 100)
    player_state["hp"] = max_hp

    # Clear negative status ailments
    player_state["conditions"] = []
    player_state["active_buffs"] = [b for b in player_state.get("active_buffs", []) if "Poison" not in b and "Bleed" not in b]

    log = f"[MED-BAY SUTURE: Dr. Thorne cleansed cellular trauma and stabilized vitals. HP fully restored ({max_hp}/{max_hp} HP) | Fee: 250 Col]"
    return {
        "success": True,
        "current_hp": max_hp,
        "max_hp": max_hp,
        "fee": fee,
        "log": log,
        "message": "Underwent bio-purification. Health fully restored."
    }

def buy_scavenger_material(player_state, item_name, qty=1):
    """
    Purchases raw crafting materials or bait from The Meiji Scavenger Dump.
    """
    mat_def = None
    for item in WASHINGTON_FACILITIES["meiji_scavenger_dump"]["inventory"]:
        if item["name"].lower() == item_name.lower():
            mat_def = item
            break

    if not mat_def:
        return {"success": False, "message": f"Item '{item_name}' is not in stock at the Scavenger Dump."}

    qty = max(1, int(qty))
    total_cost = mat_def["cost_col"] * qty
    col = player_state.get("col", 0)
    if col < total_cost:
        return {"success": False, "message": f"Insufficient Col to buy {qty}x {mat_def['name']} (Requires {total_cost:,} Col, has {col:,} Col)."}

    player_state["col"] = col - total_cost

    # Add to player inventory
    inv = player_state.setdefault("inventory", [])
    found = False
    for existing in inv:
        if isinstance(existing, dict) and existing.get("name", "").lower() == mat_def["name"].lower():
            existing["qty"] = existing.get("qty", 1) + qty
            found = True
            break
        elif isinstance(existing, str) and mat_def["name"].lower() in existing.lower():
            pass

    if not found:
        inv.append({
            "name": mat_def["name"],
            "rarity": "Common",
            "durability": 100,
            "max_durability": 100,
            "qty": qty,
            "desc": mat_def["desc"]
        })

    log = f"[TRADE: Purchased {qty}x {mat_def['name']} for {total_cost:,} Col from Kibs' Scavenger Dump.]"
    return {
        "success": True,
        "item": mat_def["name"],
        "qty": qty,
        "total_cost": total_cost,
        "log": log,
        "message": f"Purchased {qty}x {mat_def['name']}."
    }

def accept_bounty_directive(player_state, bounty_id):
    """
    Accepts a bounty directive from the Warren County Bounty Board and adds it to active quests.
    """
    bounty_def = None
    for b in WARREN_COUNTY_BOUNTIES:
        if b["id"] == bounty_id or b["title"].lower() == bounty_id.lower():
            bounty_def = b
            break

    if not bounty_def:
        return {"success": False, "message": f"Bounty '{bounty_id}' not found on the board."}

    quests = player_state.setdefault("quests", [])
    for q in quests:
        q_title = q.get("title", "") if isinstance(q, dict) else str(q)
        if q_title.lower() == bounty_def["title"].lower():
            return {"success": False, "message": f"Bounty '{bounty_def['title']}' is already active in your directives."}

    quests.append({
        "id": bounty_def["id"],
        "title": bounty_def["title"],
        "desc": bounty_def["desc"],
        "target": bounty_def["target"],
        "location": bounty_def["location"],
        "reward": bounty_def["reward"]
    })

    log = f"[DIRECTIVE ACCEPTED: Added '{bounty_def['title']}' to Active Quests! Reward: {bounty_def['reward']}]"
    return {
        "success": True,
        "bounty": bounty_def,
        "log": log,
        "message": f"Accepted bounty: {bounty_def['title']}"
    }


# =====================================================================
# PHASE 6: LABYRINTH DUNGEON CRAWLING & SECTOR BOSS ARCHITECTURE
# =====================================================================

POHATCONG_LABYRINTH = {
    "id": "pohatcong_labyrinth",
    "name": "The Pohatcong Depths",
    "sector": "Sector 1 (Warren County / Washington Regional Grid)",
    "description": "An ancient subterranean aether-excavation winding deep beneath Pohatcong Mountain. Guarded by automated runic defense matrixes and culminating in the sealed throne room of the Sector 1 Overlord.",
    "entry_room": "entry_hall",
    "rooms": {
        "entry_hall": {
            "id": "entry_hall",
            "name": "Subsurface Ingress & Descent",
            "type": "sanctuary",
            "badge": "🏕️ Sanctuary Gate",
            "description": "A massive arched basalt portal carved with dampening runes. Ambient leylines hum with protective frequencies, preventing hostile incursions.",
            "connections": ["calcified_mine_gallery"],
            "cleared": True,
            "can_rest": True
        },
        "calcified_mine_gallery": {
            "id": "calcified_mine_gallery",
            "name": "Calcified Mine Gallery",
            "type": "monster_den",
            "badge": "⚔️ Monster Den",
            "description": "Abandoned narrow-gauge rail tracks choked with calcified aether-stalagmites. Glitched burrower constructs and iron-jawed crawler chimeras skulk between the collapsed timber supports.",
            "connections": ["entry_hall", "runic_trip_corridor"],
            "cleared": False,
            "monsters": [
                {"name": "Glitched Excavator Drone", "hp": 40, "max_hp": 40, "ac": 13, "atk": 5, "dmg": "1d8+2 Piercing"},
                {"name": "Aether-Corrupted Cave Stalker", "hp": 48, "max_hp": 48, "ac": 14, "atk": 6, "dmg": "1d10+3 Slashing"}
            ],
            "reward_col": 350,
            "reward_xp": 250
        },
        "runic_trip_corridor": {
            "id": "runic_trip_corridor",
            "name": "Runic Tripwire Corridor",
            "type": "trapped_corridor",
            "badge": "🪤 Trapped Corridor",
            "description": "A claustrophobic corridor embedded with luminescent cyan tripwires, recessed pendulum-scythe slots, and pressure-sensitive pressure plates wired to mana-dart ports.",
            "connections": ["calcified_mine_gallery", "drainage_junction"],
            "cleared": False,
            "trap": {
                "name": "Cyan Mana-Dart & Pendulum Matrix",
                "disarm_dc": 14,
                "damage_dice": "2d10 Force",
                "disarmed": False,
                "disarm_skill": "Field Trapping or Cartography",
                "description": "Interlocking runic pressure cords primed to discharge localized force-shock waves."
            }
        },
        "drainage_junction": {
            "id": "drainage_junction",
            "name": "Subterranean Drainage Junction",
            "type": "hub",
            "badge": "🏛️ Central Hub",
            "description": "A colossal octagonal reservoir hall where mineral water cascades through massive bronze iron grates. Heavy adamant archways branch toward the reservoir, the sanctuary, and the deeper vault.",
            "connections": ["runic_trip_corridor", "echoing_reservoir", "crystal_sanctuary", "puzzle_chamber"],
            "cleared": True
        },
        "echoing_reservoir": {
            "id": "echoing_reservoir",
            "name": "Echoing Subterranean Reservoir",
            "type": "monster_den",
            "badge": "⚔️ Monster Den",
            "description": "Black reflective water ripples around sunken stone pillars. An aetheric mire-beast lurks beneath the surface, guarding an ancient runic chest.",
            "connections": ["drainage_junction"],
            "cleared": False,
            "monsters": [
                {"name": "Mire-Titan Carapace Lurker", "hp": 75, "max_hp": 75, "ac": 15, "atk": 7, "dmg": "2d8+4 Crushing"}
            ],
            "reward_col": 600,
            "reward_xp": 450,
            "loot": [
                {"name": "Resonator Tuning Prism", "rarity": "Rare", "grade": 3, "qty": 1, "desc": "A faceted prism tuned to ancient Dwarven leyline frequencies. Facilitates puzzle alignment in the vault."}
            ]
        },
        "crystal_sanctuary": {
            "id": "crystal_sanctuary",
            "name": "Crystal Antechamber (Haven)",
            "type": "sanctuary",
            "badge": "🏕️ Sanctuary Haven",
            "description": "Warm golden light radiates from a cluster of harmonic amber leylines. The air smells of ozone and clean rain; hostile entities cannot breach this threshold.",
            "connections": ["drainage_junction"],
            "cleared": True,
            "can_rest": True
        },
        "puzzle_chamber": {
            "id": "puzzle_chamber",
            "name": "Harmonic Frequency Vault",
            "type": "puzzle_chamber",
            "badge": "🧩 Runic Puzzle Chamber",
            "description": "Three monolithic Dwarven resonator pillars dominate the chamber before a towering crystalline seal. Dial runes (Alpha, Delta, Omega) must be harmonized to match the local tectonic harmonic (Frequency: 3 - 1 - 4).",
            "connections": ["drainage_junction", "overlord_throne_gate"],
            "cleared": False,
            "puzzle": {
                "name": "Tri-Resonant Leyline Alignment",
                "target_sequence": [3, 1, 4],
                "current_sequence": [0, 0, 0],
                "solved": False,
                "solve_dc": 14,
                "description": "Align the 3 Resonator Pillars to frequencies [3, 1, 4] to break the crystalline seal."
            }
        },
        "overlord_throne_gate": {
            "id": "overlord_throne_gate",
            "name": "The Gilded Overlord's Threshold",
            "type": "boss_gate",
            "badge": "🚪 Boss Gate",
            "description": "A monumental gate of blackened cold-iron reinforced with gilded filigree. Immense magical runes seal the threshold shut, vibrating with titanic aetheric pressure.",
            "connections": ["puzzle_chamber", "gilded_overlord_arena"],
            "cleared": False,
            "unlocked": False
        },
        "gilded_overlord_arena": {
            "id": "gilded_overlord_arena",
            "name": "The Gilded Spire Throne Room",
            "type": "boss_arena",
            "badge": "👑 Sector Boss Arena",
            "description": "A soaring subterranean cathedral beneath the roots of Pohatcong Mountain. Suspended above an aetheric rift floats the apex guardian of Sector 1: The Gilded Spire Overlord.",
            "connections": ["overlord_throne_gate"],
            "cleared": False,
            "boss_id": "gilded_overlord"
        }
    }
}

SECTOR_BOSSES = {
    "gilded_overlord": {
        "id": "gilded_overlord",
        "name": "The Gilded Spire Overlord",
        "title": "Sector 1 Apex Construct (Aether-Titan)",
        "max_hp": 300,
        "current_hp": 300,
        "phase": 1,
        "max_break": 100,
        "current_break": 100,
        "is_staggered": False,
        "stagger_rounds_remaining": 0,
        "active_telegraph": None,
        "phases": {
            1: {
                "name": "Phase 1: Runic Bulwark",
                "hp_range": "100% – 60% HP (300 – 180 HP)",
                "ac": 18,
                "dr": 3,
                "description": "Heavy gilded aegis active. Gilded armor plating deflects glancing attacks. Wields a colossal twin-headed maul with sweeping 180-degree cleaves.",
                "attacks": [
                    {"name": "Gilded Maul Cleave", "atk": 8, "dmg": "2d10+4 Physical", "type": "single"},
                    {"name": "Bulwark Shield Bash", "atk": 7, "dmg": "1d12+4 Force", "type": "stagger"}
                ],
                "telegraph_pool": [
                    {
                        "name": "Colossal Seismic Cleave",
                        "dc": 15,
                        "stat": "DEX",
                        "damage": "3d10+6 Force",
                        "warning": "Raises titanic gilded maul high overhead, channeling kinetic leyline pressure in a sweeping 180° frontal arc!"
                    }
                ]
            },
            2: {
                "name": "Phase 2: Aetheric Core Overload",
                "hp_range": "60% – 20% HP (180 – 60 HP)",
                "ac": 15,
                "dr": 1,
                "description": "Outer armor shatters with an explosive shockwave! The glowing blue aetheric core exposes itself, radiating lightning arcs and summoning repair-drone conduits.",
                "attacks": [
                    {"name": "Arcane Lightning Discharge", "atk": 9, "dmg": "3d8+5 Lightning", "type": "ranged"},
                    {"name": "Aether-Infused Greatsword Swipe", "atk": 8, "dmg": "2d8+5 Slashing", "type": "single"}
                ],
                "telegraph_pool": [
                    {
                        "name": "Aetheric Overload Cascade",
                        "dc": 16,
                        "stat": "DEX",
                        "damage": "4d8+8 Lightning",
                        "warning": "Core pulses with blinding cyan voltage! Ground floor grids begin crackling with lethal electrical discharge!"
                    }
                ]
            },
            3: {
                "name": "Phase 3: Desperation Spatial Tear",
                "hp_range": "20% – 0% HP (60 – 0 HP)",
                "ac": 13,
                "dr": 0,
                "description": "Enraged and disintegrating! Attack speed doubles, its collision mesh fractures into glitching red polygons, and spatial vortexes tear through the arena pulling combatants inward.",
                "attacks": [
                    {"name": "Frenzied Glitch Slash", "atk": 11, "dmg": "3d10+6 Chaos", "type": "dual"},
                    {"name": "Spatial Rift Pulse", "atk": 10, "dmg": "2d12+6 Force", "type": "gravity"}
                ],
                "telegraph_pool": [
                    {
                        "name": "Cataclysmic Spatial Collapse",
                        "dc": 17,
                        "stat": "STR",
                        "damage": "5d10+10 Chaos",
                        "warning": "Unleashes an uncontrollable gravitational singularity that fractures the arena ceiling downward!"
                    }
                ]
            }
        },
        "rewards": {
            "xp": 2500,
            "col": 5000,
            "items": [
                {
                    "name": "Overlord's Gilded Core",
                    "rarity": "Legendary",
                    "grade": 5,
                    "durability": 200,
                    "max_durability": 200,
                    "qty": 1,
                    "desc": "The pulsating apex heart of the Floor 1 Sector Boss. Used at the Deepforged Master-Anvil to forge Grade 6 Mythic armaments."
                },
                {
                    "name": "Gilded Spire Great-Axe",
                    "rarity": "Legendary",
                    "grade": 5,
                    "durability": 200,
                    "max_durability": 200,
                    "qty": 1,
                    "desc": "A colossal golden-crested battleaxe forged from aether-infused adamant. Grants +4 to Attack rolls and innate Shockwave Cleave."
                }
            ],
            "unlocked_zone": "Sector 2: The Musconetcong & Delaware Water Gap Expanse",
            "title": "Sector 1 Conqueror"
        }
    }
}


def initialize_dungeon_state(player_state, dungeon_id="pohatcong_labyrinth"):
    """
    Initializes the labyrinth dungeon state in player_state if not already present.
    """
    if "dungeon_state" not in player_state or not isinstance(player_state["dungeon_state"], dict):
        import copy
        dungeon_def = copy.deepcopy(POHATCONG_LABYRINTH)
        player_state["dungeon_state"] = {
            "dungeon_id": dungeon_id,
            "name": dungeon_def["name"],
            "current_room_id": dungeon_def["entry_room"],
            "rooms": dungeon_def["rooms"],
            "cleared_rooms": [dungeon_def["entry_room"]],
            "visited_rooms": [dungeon_def["entry_room"]],
            "dungeon_completed": False
        }
    return player_state["dungeon_state"]


def get_current_dungeon_room(player_state):
    """
    Returns the player's active dungeon room dictionary.
    """
    d_state = initialize_dungeon_state(player_state)
    cur_id = d_state.get("current_room_id", "entry_hall")
    rooms = d_state.get("rooms", {})
    return rooms.get(cur_id, POHATCONG_LABYRINTH["rooms"]["entry_hall"])


def move_dungeon_room(player_state, target_room_id):
    """
    Attempts to move the player to an adjacent dungeon room:
    - Verifies connectivity
    - Checks for locked gates or uncleared traps blocking passage
    - Updates visited and current room
    """
    d_state = initialize_dungeon_state(player_state)
    cur_room = get_current_dungeon_room(player_state)
    cur_id = cur_room["id"]

    connections = cur_room.get("connections", [])
    if target_room_id not in connections:
        return {
            "success": False,
            "message": f"Cannot reach {target_room_id} from {cur_room['name']}. No passage exists.",
            "current_room": cur_room
        }

    target_room = d_state.get("rooms", {}).get(target_room_id)
    if not target_room:
        return {
            "success": False,
            "message": f"Dungeon room {target_room_id} does not exist.",
            "current_room": cur_room
        }

    # Boss gate lock check
    if target_room.get("type") == "boss_gate" and not target_room.get("unlocked", False):
        # Check if puzzle was solved
        puzzle_room = d_state.get("rooms", {}).get("puzzle_chamber", {})
        if puzzle_room.get("puzzle", {}).get("solved", False) or puzzle_room.get("cleared", False):
            target_room["unlocked"] = True
        else:
            return {
                "success": False,
                "message": f"The monumental Boss Gate is sealed shut! The crystalline runes require solving the Harmonic Frequency Vault.",
                "current_room": cur_room
            }

    # Boss arena check
    if target_room.get("type") == "boss_arena":
        gate_room = d_state.get("rooms", {}).get("overlord_throne_gate", {})
        if not gate_room.get("unlocked", False):
            return {
                "success": False,
                "message": "The Overlord's Throne Gate must be unlocked first!",
                "current_room": cur_room
            }

    # Perform move
    d_state["current_room_id"] = target_room_id
    if target_room_id not in d_state["visited_rooms"]:
        d_state["visited_rooms"].append(target_room_id)

    log = f"[DUNGEON: Moved to '{target_room['name']}' ({target_room.get('badge', '')})]"

    # If moving into boss arena, automatically initialize boss encounter if needed
    if target_room.get("type") == "boss_arena":
        initialize_boss_encounter(player_state)

    return {
        "success": True,
        "message": f"Navigated to {target_room['name']}.",
        "new_room": target_room,
        "log": log
    }


def disarm_dungeon_trap(player_state):
    """
    Attempts to disarm the trap in the current trapped corridor using Field Trapping or Cartography.
    Ren's Leyline Overwatch stance provides a +3 tactical bonus.
    """
    cur_room = get_current_dungeon_room(player_state)
    if cur_room.get("type") != "trapped_corridor" or "trap" not in cur_room:
        return {"success": False, "message": "There are no active traps to disarm in this chamber."}

    trap = cur_room["trap"]
    if trap.get("disarmed", False):
        return {"success": False, "message": "This trap has already been neutralized."}

    dc = trap.get("disarm_dc", 14)

    # Calculate player modifier
    stats = player_state.get("stats", {})
    dex_mod = (stats.get("DEX", 10) - 10) // 2
    int_mod = (stats.get("INT", 10) - 10) // 2

    # Skill bonus from Field Trapping or Cartography
    skills = player_state.get("skills", {})
    trapping_mastery = 0
    for sk in ["Field Trapping", "Cartography", "trapping", "scavenging"]:
        if sk in skills:
            s_data = skills[sk]
            m_val = s_data.get("mastery", 1) if isinstance(s_data, dict) else int(s_data)
            trapping_mastery = max(trapping_mastery, m_val)

    # 1-1000 mastery translation to check bonus
    skill_bonus = min(8, trapping_mastery // 50)

    # Ren Tactical Stance Bonus
    ren_bonus = 0
    comp_ren = get_companion(player_state, "Ren") if "get_companion" in globals() else {}
    if comp_ren.get("stance") == "overwatch_hacking":
        ren_bonus = 3

    # Simulated deterministic roll
    import random
    roll = random.randint(1, 20)
    total = roll + dex_mod + skill_bonus + ren_bonus

    if total >= dc:
        trap["disarmed"] = True
        cur_room["cleared"] = True
        d_state = initialize_dungeon_state(player_state)
        if cur_room["id"] not in d_state["cleared_rooms"]:
            d_state["cleared_rooms"].append(cur_room["id"])

        log = f"[TRAP DISARMED: Roll {roll} + DEX({dex_mod}) + Skill({skill_bonus}) + RenOverwatch({ren_bonus}) = {total} vs DC {dc} -> SUCCESS! Disarmed {trap['name']}!]"
        return {
            "success": True,
            "disarmed": True,
            "roll": total,
            "dc": dc,
            "log": log,
            "message": f"Successfully neutralized {trap['name']}!"
        }
    else:
        # Trap sprung!
        dmg_val = random.randint(5, 15)
        player_state["hp"] = max(1, player_state.get("hp", 100) - dmg_val)
        log = f"[TRAP TRIGGERED: Roll {roll} + MODs({dex_mod + skill_bonus + ren_bonus}) = {total} vs DC {dc} -> FAILED! {trap['name']} sprung for {dmg_val} Force DMG! (HP: {player_state['hp']})]"
        return {
            "success": False,
            "disarmed": False,
            "roll": total,
            "dc": dc,
            "damage_taken": dmg_val,
            "log": log,
            "message": f"Triggered {trap['name']}! Suffered {dmg_val} Force damage."
        }


def solve_dungeon_puzzle(player_state, sequence=None):
    """
    Attempts to harmonize the three resonator pillars in the Harmonic Frequency Vault.
    Sequence should be [int, int, int] (e.g. [3, 1, 4]).
    Can also be auto-solved with an INT / Arcana check (DC 14) or Ren's Runic Scribe Slate.
    """
    cur_room = get_current_dungeon_room(player_state)
    if cur_room.get("type") != "puzzle_chamber" or "puzzle" not in cur_room:
        return {"success": False, "message": "There is no runic puzzle in this chamber."}

    puzzle = cur_room["puzzle"]
    if puzzle.get("solved", False):
        return {"success": False, "message": "The harmonic frequency is already aligned and the seal is broken."}

    target = puzzle.get("target_sequence", [3, 1, 4])

    if sequence is not None:
        puzzle["current_sequence"] = list(sequence)
        if puzzle["current_sequence"] == target:
            puzzle["solved"] = True
            cur_room["cleared"] = True
            d_state = initialize_dungeon_state(player_state)
            if cur_room["id"] not in d_state["cleared_rooms"]:
                d_state["cleared_rooms"].append(cur_room["id"])

            # Also unlock boss gate
            gate_room = d_state.get("rooms", {}).get("overlord_throne_gate", {})
            gate_room["unlocked"] = True

            log = f"[PUZZLE SOLVED: Resonators aligned to [{target[0]}-{target[1]}-{target[2]}]! The crystalline seal fractures, unlocking the Overlord's Throne Gate!]"
            return {
                "success": True,
                "solved": True,
                "log": log,
                "message": "Harmonic alignment achieved! The Boss Gate is unsealed."
            }
        else:
            return {
                "success": False,
                "solved": False,
                "message": f"Frequencies [{sequence[0]}-{sequence[1]}-{sequence[2]}] dissonant. The obelisks hum sharply in disharmony."
            }

    # Auto-solve via INT / Arcana check
    stats = player_state.get("stats", {})
    int_mod = (stats.get("INT", 10) - 10) // 2
    ren_bonus = 2  # Ren's Runic Scribe Slate assistance

    # Check for Resonator Tuning Prism from Echoing Reservoir
    inv = player_state.get("inventory", [])
    has_prism = any("Resonator Tuning Prism" in (item.get("name", "") if isinstance(item, dict) else str(item)) for item in inv)
    prism_bonus = 4 if has_prism else 0

    import random
    roll = random.randint(1, 20)
    total = roll + int_mod + ren_bonus + prism_bonus
    dc = puzzle.get("solve_dc", 14)

    if total >= dc:
        puzzle["current_sequence"] = target
        puzzle["solved"] = True
        cur_room["cleared"] = True
        d_state = initialize_dungeon_state(player_state)
        if cur_room["id"] not in d_state["cleared_rooms"]:
            d_state["cleared_rooms"].append(cur_room["id"])

        gate_room = d_state.get("rooms", {}).get("overlord_throne_gate", {})
        gate_room["unlocked"] = True

        log = f"[PUZZLE SOLVED: Intelligence check {roll} + INT({int_mod}) + RenSlate({ren_bonus}) + Prism({prism_bonus}) = {total} vs DC {dc} -> SUCCESS! Resonator aligned to 3-1-4! Gate unsealed!]"
        return {
            "success": True,
            "solved": True,
            "roll": total,
            "dc": dc,
            "log": log,
            "message": "Calculated the resonant leyline harmonics! The Overlord's Throne Gate swings open."
        }
    else:
        log = f"[PUZZLE CHECK FAILED: Roll {roll} + MODs({int_mod + ren_bonus + prism_bonus}) = {total} vs DC {dc} -> Resonator feedback discharged!]"
        return {
            "success": False,
            "solved": False,
            "roll": total,
            "dc": dc,
            "log": log,
            "message": "Failed to deduce the resonant frequency. The obelisks hum dissonantly."
        }


def rest_in_sanctuary(player_state):
    """
    Rests in a designated sanctuary room:
    - Restores 50% max HP
    - Repairs damaged equipped gear slightly (+10 durability)
    - Restores Ren's morale to 'Confident'
    """
    cur_room = get_current_dungeon_room(player_state)
    if not cur_room.get("can_rest", False) and cur_room.get("type") != "sanctuary":
        return {"success": False, "message": "Cannot rest here! The environment is hostile and unprotected."}

    max_hp = player_state.get("max_hp", 100)
    heal_amount = max(25, max_hp // 2)
    old_hp = player_state.get("hp", max_hp)
    player_state["hp"] = min(max_hp, old_hp + heal_amount)
    actual_heal = player_state["hp"] - old_hp

    # Field-repair equipped gear (+10 durability)
    gear_dur = player_state.setdefault("gear_durability", {})
    repaired_items = []
    for slot, d_info in gear_dur.items():
        if isinstance(d_info, dict) and d_info.get("cur", 100) < d_info.get("max", 100):
            d_info["cur"] = min(d_info["max"], d_info["cur"] + 10)
            repaired_items.append(slot)

    # Ren morale restoration
    if "update_companion_morale" in globals():
        update_companion_morale(player_state, "Ren", "Confident")

    log = f"[SANCTUARY REST: Recovered +{actual_heal} HP (now {player_state['hp']}/{max_hp}), field-patched gear ({len(repaired_items)} items), Ren's morale restored to Confident!]"
    return {
        "success": True,
        "healed": actual_heal,
        "current_hp": player_state["hp"],
        "repaired_slots": repaired_items,
        "log": log,
        "message": f"Rested safely in {cur_room['name']}."
    }


def initialize_boss_encounter(player_state, boss_id="gilded_overlord"):
    """
    Initializes a multi-phase sector boss encounter in player_state["boss_encounter"].
    """
    if "boss_encounter" not in player_state or not isinstance(player_state["boss_encounter"], dict) or player_state["boss_encounter"].get("id") != boss_id:
        import copy
        boss_def = copy.deepcopy(SECTOR_BOSSES.get(boss_id, SECTOR_BOSSES["gilded_overlord"]))
        player_state["boss_encounter"] = boss_def
        # Set initial telegraph
        p1 = boss_def["phases"][1]
        if p1.get("telegraph_pool"):
            player_state["boss_encounter"]["active_telegraph"] = copy.deepcopy(p1["telegraph_pool"][0])
    return player_state["boss_encounter"]


def apply_damage_to_boss(player_state, damage_amount, is_heavy=False, is_stagger_hit=False):
    """
    Applies incoming damage to the active Sector Boss:
    - Calculates Phase-based Damage Reduction (DR)
    - If boss is STAGGERED: bypasses DR, inflicts +50% critical damage
    - Reduces 100-pt Break Gauge (-10 on normal, -25 on heavy, -35 on hammer/stagger skills)
    - Triggers Stagger state when Break Gauge hits 0
    - Checks for phase transitions (100-60% -> 60-20% -> 20-0%)
    """
    boss = initialize_boss_encounter(player_state)
    if boss.get("current_hp", 0) <= 0:
        return {"success": False, "message": f"{boss['name']} has already been defeated!"}

    current_phase = boss.get("phase", 1)
    phase_info = boss["phases"].get(current_phase, boss["phases"][1])
    dr = phase_info.get("dr", 0)

    # Stagger calculations
    is_staggered = boss.get("is_staggered", False)
    if is_staggered:
        dr = 0
        damage_amount = int(damage_amount * 1.5)  # 50% critical bonus during stagger

    actual_dmg = max(1, damage_amount - dr)
    boss["current_hp"] = max(0, boss["current_hp"] - actual_dmg)

    # Break Gauge handling
    break_dmg = 25 if is_heavy else 10
    if is_stagger_hit:
        break_dmg = 35

    stagger_triggered = False
    if not is_staggered:
        boss["current_break"] = max(0, boss.get("current_break", 100) - break_dmg)
        if boss["current_break"] == 0:
            boss["is_staggered"] = True
            boss["stagger_rounds_remaining"] = 1
            stagger_triggered = True

    # Phase transition checks
    hp_pct = boss["current_hp"] / boss["max_hp"]
    new_phase = current_phase
    phase_transition = False

    if hp_pct <= 0.20 and current_phase < 3:
        new_phase = 3
        phase_transition = True
    elif hp_pct <= 0.60 and current_phase < 2:
        new_phase = 2
        phase_transition = True

    if phase_transition:
        boss["phase"] = new_phase
        new_p_info = boss["phases"][new_phase]
        # Refresh telegraph to new phase move
        if new_p_info.get("telegraph_pool"):
            import copy
            boss["active_telegraph"] = copy.deepcopy(new_p_info["telegraph_pool"][0])
        # Reset break gauge on phase transition
        boss["current_break"] = 100
        boss["is_staggered"] = False

    log_parts = []
    log_parts.append(f"[BOSS COMBAT: Dealt {damage_amount} DMG - DR({dr}) = {actual_dmg} to {boss['name']}! (HP: {boss['current_hp']}/{boss['max_hp']})]")
    if not is_staggered and not stagger_triggered:
        log_parts.append(f"[BREAK GAUGE: Chipped -{break_dmg} Break -> {boss['current_break']}/{boss['max_break']}]")

    if stagger_triggered:
        log_parts.append(f"💥 [BOSS STAGGERED: Break Gauge collapsed! {boss['name']} is STUNNED for 1 round! +50% Crit DMG & DR bypassed!]")

    if phase_transition:
        log_parts.append(f"🚨 [BOSS PHASE TRANSITION: Crossed HP threshold -> Entering {boss['phases'][new_phase]['name']}! {boss['phases'][new_phase]['description']}]")

    return {
        "success": True,
        "damage_dealt": actual_dmg,
        "boss_hp": boss["current_hp"],
        "boss_max_hp": boss["max_hp"],
        "phase": boss["phase"],
        "phase_transition": phase_transition,
        "is_staggered": boss["is_staggered"],
        "stagger_triggered": stagger_triggered,
        "current_break": boss["current_break"],
        "log": " | ".join(log_parts)
    }


def get_boss_turn_action(player_state):
    """
    Resolves the Sector Boss's turn:
    - If STAGGERED: skips turn, decrements stagger counter, resets break gauge on recovery.
    - If active telegraph exists: fires the telegraphed attack (unless countered).
    - Otherwise: picks a phase attack and primes the next telegraphed move.
    """
    boss = initialize_boss_encounter(player_state)
    if boss.get("current_hp", 0) <= 0:
        return {"action": "defeated", "log": f"[{boss['name']} lies shattered upon the aetheric floor.]"}

    # Handle Staggered state
    if boss.get("is_staggered", False):
        boss["stagger_rounds_remaining"] = max(0, boss.get("stagger_rounds_remaining", 1) - 1)
        if boss["stagger_rounds_remaining"] == 0:
            boss["is_staggered"] = False
            boss["current_break"] = boss["max_break"]  # Reset break gauge
            return {
                "action": "recover",
                "log": f"[BOSS STAGGER RECOVERY: {boss['name']} recovers balance and re-energizes its Break Shield!]"
            }
        return {
            "action": "staggered",
            "log": f"[BOSS STAGGERED: {boss['name']} is paralyzed by system recoil and cannot act this turn!]"
        }

    phase = boss.get("phase", 1)
    phase_info = boss["phases"].get(phase, boss["phases"][1])

    # If a telegraph was active, execute it!
    telegraph = boss.get("active_telegraph")
    if telegraph:
        # Clear telegraph after executing
        boss["active_telegraph"] = None
        return {
            "action": "telegraph_execute",
            "name": telegraph["name"],
            "dc": telegraph.get("dc", 15),
            "stat": telegraph.get("stat", "DEX"),
            "damage": telegraph.get("damage", "3d10 Force"),
            "log": f"[BOSS TELEGRAPH DETONATION: {boss['name']} releases {telegraph['name']}! Save DC {telegraph['dc']} {telegraph['stat']} or take {telegraph['damage']}!]"
        }

    # Standard turn: execute basic attack and prime next telegraph
    import random
    attacks = phase_info.get("attacks", [])
    atk = random.choice(attacks) if attacks else {"name": "Gilded Strike", "atk": 8, "dmg": "2d10+4 Physical"}

    # Prime next telegraph
    pool = phase_info.get("telegraph_pool", [])
    if pool:
        boss["active_telegraph"] = random.choice(pool)

    tele_msg = f" ⚠️ [BOSS TELEGRAPH WARNING: {boss['active_telegraph']['warning']}]" if boss.get("active_telegraph") else ""

    log = f"[BOSS ATTACK: {boss['name']} strikes with {atk['name']} (ATK +{atk['atk']}, {atk['dmg']})!]{tele_msg}"
    return {
        "action": "attack",
        "attack": atk,
        "primed_telegraph": boss.get("active_telegraph"),
        "log": log
    }


def counter_boss_telegraph(player_state, counter_action="dodge"):
    """
    Player counter-action against an active boss telegraph:
    - 'dodge': DEX save vs DC to take 0 damage
    - 'shield_block': CON check to reduce damage by 75%
    - 'ren_phase_veil': Ren consumes stance to phase party out of reality (Guaranteed Avoidance)
    - 'stagger_interrupt': Execute heavy weapon strike to break remaining Break Gauge
    """
    boss = initialize_boss_encounter(player_state)
    telegraph = boss.get("active_telegraph")
    if not telegraph:
        return {"success": False, "message": "There is no active boss telegraph to counter."}

    dc = telegraph.get("dc", 15)
    stats = player_state.get("stats", {})
    dex_mod = (stats.get("DEX", 10) - 10) // 2
    con_mod = (stats.get("CON", 10) - 10) // 2

    import random
    roll = random.randint(1, 20)

    if counter_action == "ren_phase_veil":
        comp_ren = get_companion(player_state, "Ren") if "get_companion" in globals() else {}
        boss["active_telegraph"] = None
        log = f"[COUNTER SUCCESS: Ren Sasaki deploys Aetheric Phase-Veil! The party blinks between dimensions, completely negating {telegraph['name']}!]"
        return {"success": True, "damage_avoided": True, "log": log, "message": "Ren's Phase-Veil neutralized the boss attack!"}

    elif counter_action == "shield_block":
        total = roll + con_mod
        boss["active_telegraph"] = None
        if total >= dc:
            log = f"[COUNTER SUCCESS: Shield Block roll {roll} + CON({con_mod}) = {total} vs DC {dc}! Absorbed 75% of {telegraph['name']}!]"
            return {"success": True, "damage_reduced": True, "reduction_pct": 0.75, "log": log, "message": "Blocked the brunt of the kinetic impact!"}
        else:
            log = f"[COUNTER PARTIAL: Shield Block roll {roll} + CON({con_mod}) = {total} vs DC {dc}. Absorbed 25% of impact.]"
            return {"success": False, "damage_reduced": True, "reduction_pct": 0.25, "log": log, "message": "Shield buckled under the force."}

    elif counter_action == "stagger_interrupt":
        # Heavy interrupt strike against break gauge
        boss["current_break"] = max(0, boss.get("current_break", 100) - 40)
        boss["active_telegraph"] = None
        if boss["current_break"] == 0:
            boss["is_staggered"] = True
            boss["stagger_rounds_remaining"] = 1
            log = f"[COUNTER CRITICAL: Interrupted telegraph with a brutal Hammer/Axe strike! Break Gauge hit 0 -> {boss['name']} is STAGGERED!]"
            return {"success": True, "interrupted": True, "staggered": True, "log": log, "message": "Interrupted the attack and shattered the boss's stance!"}
        else:
            log = f"[COUNTER HIT: Interrupted telegraph for -40 Break Gauge (now {boss['current_break']}/100)! Telegraph discharged.]"
            return {"success": True, "interrupted": False, "log": log, "message": "Chipped the boss's stance."}

    else:
        # Default: Dodge
        total = roll + dex_mod
        boss["active_telegraph"] = None
        if total >= dc:
            log = f"[COUNTER SUCCESS: Evasive Dive roll {roll} + DEX({dex_mod}) = {total} vs DC {dc} -> DODGED! Took 0 damage from {telegraph['name']}!]"
            return {"success": True, "damage_avoided": True, "log": log, "message": f"Successfully evaded {telegraph['name']}!"}
        else:
            log = f"[COUNTER FAILED: Evasive Dive roll {roll} + DEX({dex_mod}) = {total} vs DC {dc} -> Direct hit!]"
            return {"success": False, "damage_avoided": False, "log": log, "message": f"Failed to dodge {telegraph['name']}."}


def claim_boss_victory(player_state):
    """
    Claims victory rewards upon defeating the Sector 1 Overlord:
    - Verifies current_hp <= 0
    - Awards 2,500 XP and 5,000 Col
    - Awards Legendary loot (Overlord's Gilded Core, Gilded Spire Great-Axe)
    - Unseals Sector 2 Teleport Gate
    - Adds title/feat 'Sector 1 Conqueror'
    - Updates dungeon state completed = True
    """
    boss = initialize_boss_encounter(player_state)
    if boss.get("current_hp", 1) > 0:
        return {"success": False, "message": f"{boss['name']} is still standing with {boss['current_hp']} HP!"}

    rewards = boss.get("rewards", {})
    xp_reward = rewards.get("xp", 2500)
    col_reward = rewards.get("col", 5000)
    items_reward = rewards.get("items", [])
    title = rewards.get("title", "Sector 1 Conqueror")

    # Award Col
    player_state["col"] = player_state.get("col", 0) + col_reward

    # Award XP
    player_state["xp"] = player_state.get("xp", 0) + xp_reward
    award_companion_xp(player_state, "Ren", xp_reward // 2)

    # Award Loot
    inv = player_state.setdefault("inventory", [])
    import copy
    for item in items_reward:
        inv.append(copy.deepcopy(item))

    # Add Conqueror Feat/Title
    feats = player_state.setdefault("feats", [])
    feat_str = f"Title: {title} (Defeated Floor 1 Apex Titan; Floor 2 Teleport Gate unsealed)"
    if feat_str not in feats:
        feats.append(feat_str)

    # Mark dungeon as completed
    d_state = initialize_dungeon_state(player_state)
    d_state["dungeon_completed"] = True
    arena_room = d_state.get("rooms", {}).get("gilded_overlord_arena", {})
    arena_room["cleared"] = True

    # Mark quest completion if bounty exists
    quests = player_state.setdefault("quests", [])
    for q in quests:
        q_title = q.get("title", "") if isinstance(q, dict) else str(q)
        if "overlord" in q_title.lower() or "spire" in q_title.lower():
            q["completed"] = True

    log = (
        f"👑 [SECTOR BOSS SLAIN: {boss['name']} shattered into glittering crystal shards!]\n"
        f"🎁 [REWARDS: +{xp_reward} XP, +{col_reward:,} Col, Claimed 'Overlord's Gilded Core' & 'Gilded Spire Great-Axe'!]\n"
        f"🌐 [PORTAL UNSEALED: Floor Teleport Gate activated! Unlocked {rewards.get('unlocked_zone')}]"
    )

    return {
        "success": True,
        "xp_awarded": xp_reward,
        "col_awarded": col_reward,
        "items_awarded": items_reward,
        "title": title,
        "log": log,
        "message": f"Congratulations! You have cleared Sector 1 and unsealed the Teleport Gate to Sector 2."
    }


# =====================================================================
# PHASE 7: LIVING NPC ECOSYSTEM, PARTY RECRUITMENT & GUILD ALLIANCES
# =====================================================================

RECRUITABLE_COMPANIONS = {
    "Ren": {
        "id": "ren_sasaki",
        "name": "Ren Sasaki",
        "class": "Aether-Scholar & MageTech Artificer",
        "title": "Aether-Scholar & MageTech Artificer",
        "role": "Support, Aura Scanning, Lightning Stuns & Field Artificing",
        "level": 3,
        "hp": 35,
        "max_hp": 35,
        "xp": 450,
        "next_level_xp": 900,
        "stance": "overwatch_hacking",
        "morale": "Steady",
        "affinity": 35,
        "affinity_tier": "Ally",
        "recruited": True,
        "active": True,
        "recruitment_location": "Washington Borough Safe-Zone (Starting Companion / Vanguard)",
        "recruitment_requirements": {"min_level": 1, "col_cost": 0, "description": "Form a co-op pact in Sector 1."},
        "bio": "A studious 17-year-old survivor and trapped game tester who fused his engineering background with esoteric aetheric rune-matrices. Wields a custom brass-and-crystal MageTech caster firearm.",
        "loadout": {
            "main_hand": "Aether-Etched MageTech Caster (Runic Firearm)",
            "tool": "Runic Scribe Slate (Aether-Grid Focus)",
            "deck": "Runic Scribe Slate (Aether-Grid Focus)",
            "armor": "Woven Leyline Duster (Enchanted Cloth, DR 1)",
            "chest": "Woven Leyline Duster (Enchanted Cloth, DR 1)"
        },
        "equipped": {
            "main_hand": "Aether-Etched MageTech Caster (Runic Firearm)",
            "tool": "Runic Scribe Slate (Aether-Grid Focus)",
            "deck": "Runic Scribe Slate (Aether-Grid Focus)",
            "armor": "Woven Leyline Duster (Enchanted Cloth, DR 1)",
            "chest": "Woven Leyline Duster (Enchanted Cloth, DR 1)"
        },
        "skills": {
            "Mesh Exploitation": {"mastery": 190, "tier": "Journeyman", "description": "Perceiving spatial seams and leylines.", "milestones_unlocked": ["Logic Buffer Exploit"]},
            "Stun-Pistol Marksmanship": {"mastery": 95, "tier": "Apprentice", "description": "Discharging lightning runes from MageTech firearm.", "milestones_unlocked": []},
            "Diagnostic Triage": {"mastery": 110, "tier": "Journeyman", "description": "Channelling restorative aether-salves.", "milestones_unlocked": ["Patch Script v1.0"]}
        },
        "abilities": [
            "Aura Weakpoint Scan (-2 Enemy AC)",
            "MageTech Stun-Arc Salvo (DC 13 CON save vs Stun)",
            "Aether-Scrap Extraction (+25% salvage yield)"
        ],
        "stances": {
            "overwatch_hacking": {
                "name": "Leyline Overwatch",
                "label": "👁️ Leyline Overwatch",
                "tag": "[REN OVERWATCH]",
                "tactical_effect": "-2 Enemy AC debuff to primary target via weakpoint telemetry.",
                "desc": "Scans leylines and structural telemetry, debuffing target AC."
            },
            "suppression_fire": {
                "name": "MageTech Arc Suppression",
                "label": "⚡ MageTech Arc Suppression",
                "tag": "[REN SUPPRESSION]",
                "tactical_effect": "Discharges lightning-mana salvos; forces DC 13 CON save vs Staggered.",
                "desc": "Suppresses targets with crackling lightning bolts."
            },
            "full_evasion": {
                "name": "Aetheric Phase-Veil",
                "label": "🌫️ Aetheric Phase-Veil",
                "tag": "[REN EVASION]",
                "tactical_effect": "Weaves spatial distortion cloak; completely immune to single-target attacks.",
                "desc": "Blinks out of direct reality."
            },
            "utility_rigging": {
                "name": "Arcane Artificing & Mending",
                "label": "✨ Arcane Artificing & Mending",
                "tag": "[REN UTILITY]",
                "tactical_effect": "Restores +15 durability to worn equipment or scavenges bonus crystallite.",
                "desc": "Channels mending runes into ally equipment."
            }
        },
        "dual_tech_id": "runic_axe_storm"
    },
    "Elora": {
        "id": "elora_thorne",
        "name": "Elora Thorne",
        "class": "Aether-Slinger / Spellblade",
        "title": "Aether-Slinger / Spellblade",
        "role": "Ranged Burst DPS, Elemental Mana Infusion & Phase Mobility",
        "level": 3,
        "hp": 32,
        "max_hp": 32,
        "xp": 400,
        "next_level_xp": 900,
        "stance": "spellblade_flurry",
        "morale": "Steady",
        "affinity": 20,
        "affinity_tier": "Acquaintance",
        "recruited": False,
        "active": False,
        "recruitment_location": "The Iron Spoke Tavern (Washington Borough, X:50, Y:50)",
        "recruitment_requirements": {"min_level": 2, "col_cost": 100, "description": "Meet Elora at the Iron Spoke Tavern and provide 100 Col for expedition rations."},
        "bio": "A nimble spellblade who channels raw mana into rapid-firing crystal-tipped rapiers. Dr. Thorne's estranged niece, seeking a frontline raiding party in Sector 1.",
        "loadout": {
            "main_hand": "Starlight Aether-Rapier (Enchanted Steel, 1d8+3 Piercing)",
            "off_hand": "Resonating Caster Gauntlet (Focus)",
            "armor": "Silk Phase-Robes (Enchanted Cloth, DR 1, +2 DEX)",
            "chest": "Silk Phase-Robes (Enchanted Cloth, DR 1, +2 DEX)"
        },
        "equipped": {
            "main_hand": "Starlight Aether-Rapier (Enchanted Steel, 1d8+3 Piercing)",
            "off_hand": "Resonating Caster Gauntlet (Focus)",
            "armor": "Silk Phase-Robes (Enchanted Cloth, DR 1, +2 DEX)",
            "chest": "Silk Phase-Robes (Enchanted Cloth, DR 1, +2 DEX)"
        },
        "skills": {
            "Spellblade Fencing": {"mastery": 175, "tier": "Journeyman", "description": "Fluid martial strikes infused with raw mana.", "milestones_unlocked": ["Lunge & Pierce"]},
            "Aether Siphoning": {"mastery": 130, "tier": "Journeyman", "description": "Harvesting stray leyline charges to empower abilities.", "milestones_unlocked": ["Mana Flow"]},
            "Acrobatic Skirmishing": {"mastery": 140, "tier": "Journeyman", "description": "Dancing between melee and ranged kill zones.", "milestones_unlocked": ["Quickstep"]}
        },
        "abilities": [
            "Spellblade Flurry (3-Hit Piercing Combo)",
            "Aetheric Weapon Infusion (+1d8 Elemental DMG to Ally)",
            "Dimensional Blinkstep (Disengage without provoking opportunity attacks)"
        ],
        "stances": {
            "spellblade_flurry": {
                "name": "Spellblade Flurry",
                "label": "🗡️ Spellblade Flurry",
                "tag": "[ELORA FLURRY]",
                "tactical_effect": "Unleashes rapid piercing strikes dealing 2d8+4 Arcane DMG and +2 Attack bonus to party.",
                "desc": "High offensive DPS mode."
            },
            "aether_overcharge": {
                "name": "Aether Overcharge",
                "label": "🔮 Aether Overcharge",
                "tag": "[ELORA OVERCHARGE]",
                "tactical_effect": "Channels radiant mana into Banki's weapons; Banki deals +1d10 bonus Radiant/Lightning DMG.",
                "desc": "Weapon buffing stance."
            },
            "blink_skirmish": {
                "name": "Blink Skirmish",
                "label": "🌀 Blink Skirmish",
                "tag": "[ELORA BLINK]",
                "tactical_effect": "Teleports erratically across the perimeter; evades incoming attacks and roots a target (DC 14 DEX save).",
                "desc": "Evasive control stance."
            }
        },
        "dual_tech_id": "spellblade_vortex"
    },
    "Torvald": {
        "id": "torvald_ironvein",
        "name": "Torvald Iron-Vein",
        "class": "Deepforged Vanguard",
        "title": "Deepforged Vanguard",
        "role": "Heavy Tower Shield Tank, Frontline Threat Generation & Seismic Stuns",
        "level": 4,
        "hp": 55,
        "max_hp": 55,
        "xp": 750,
        "next_level_xp": 1200,
        "stance": "aegis_bulwark",
        "morale": "Steady",
        "affinity": 25,
        "affinity_tier": "Ally",
        "recruited": False,
        "active": False,
        "recruitment_location": "The Iron Spoke Tavern / Oxford Ridge Outpost (X:52, Y:48)",
        "recruitment_requirements": {"min_level": 3, "col_cost": 150, "description": "Prove your vanguard mettle in battle and pay 150 Col for deepforged gear upkeep."},
        "bio": "A veteran dwarven mercenary and barkeep of the Iron Spoke. Possesses runic cyber-plated armor and a tower shield wide as a castle gate.",
        "loadout": {
            "main_hand": "Deepforged War-Axe (Heavy Runic Iron, 1d10+4 Slashing)",
            "off_hand": "Adamant Bulwark Tower Shield (+4 AC, DR 2)",
            "armor": "Runic Plate Carapace (Heavy Armor, DR 3)",
            "chest": "Runic Plate Carapace (Heavy Armor, DR 3)"
        },
        "equipped": {
            "main_hand": "Deepforged War-Axe (Heavy Runic Iron, 1d10+4 Slashing)",
            "off_hand": "Adamant Bulwark Tower Shield (+4 AC, DR 2)",
            "armor": "Runic Plate Carapace (Heavy Armor, DR 3)",
            "chest": "Runic Plate Carapace (Heavy Armor, DR 3)"
        },
        "skills": {
            "Tower Shield Phalanx": {"mastery": 240, "tier": "Journeyman", "description": "Mastery of defensive interlocking shield stances.", "milestones_unlocked": ["Shield Wall", "Brace Impact"]},
            "Deepforged Smithing": {"mastery": 210, "tier": "Journeyman", "description": "Knowledge of runic alloys, temper lines, and repairs.", "milestones_unlocked": ["Field Tempering"]},
            "Battlefield Provocation": {"mastery": 180, "tier": "Journeyman", "description": "Commanding hostile attention through force of presence.", "milestones_unlocked": ["Roar of Challenge"]}
        },
        "abilities": [
            "Interception Ward (+4 AC to adjacent ally)",
            "Challenge of the Anvil (Forced Taunt)",
            "Seismic Tremor (Frontal Knockdown)"
        ],
        "stances": {
            "aegis_bulwark": {
                "name": "Aegis Bulwark",
                "label": "🛡️ Aegis Bulwark",
                "tag": "[TORVALD AEGIS]",
                "tactical_effect": "Locks tower shield on frontline; grants Banki +4 AC and absorbs 50% of incoming physical damage.",
                "desc": "Frontline damage interception."
            },
            "iron_taunt": {
                "name": "Iron Challenge",
                "label": "🗣️ Iron Challenge",
                "tag": "[TORVALD TAUNT]",
                "tactical_effect": "Bangs war-axe against adamant shield; forces all active foes to attack Torvald instead of allies.",
                "desc": "Aggro and threat control."
            },
            "seismic_slam": {
                "name": "Seismic Slam",
                "label": "💥 Seismic Slam",
                "tag": "[TORVALD SLAM]",
                "tactical_effect": "Slams shield into the earth for 2d10+5 Force DMG; chips target Break Gauge by -30.",
                "desc": "Heavy bludgeoning stun."
            }
        },
        "dual_tech_id": "titans_anvil_shockwave"
    },
    "Kibs": {
        "id": "kibs_ninefingers",
        "name": "Kibs Nine-Fingers",
        "class": "Scrapper Rogue / Infiltrator",
        "title": "Scrapper Rogue / Infiltrator",
        "role": "Shadow-Meld, Critical Backstabs, Poison Coatings & Trap Disarming",
        "level": 3,
        "hp": 30,
        "max_hp": 30,
        "xp": 350,
        "next_level_xp": 900,
        "stance": "shadow_meld",
        "morale": "Steady",
        "affinity": 15,
        "affinity_tier": "Acquaintance",
        "recruited": False,
        "active": False,
        "recruitment_location": "Meiji Dump Scrap Warrens (X:48, Y:54)",
        "recruitment_requirements": {"min_level": 2, "col_cost": 75, "description": "Rescue Kibs from perimeter scavengers or trade 75 Col worth of scrap parts."},
        "bio": "A crafty goblinoid scavenger operating out of the Meiji Dump. Possesses uncanny instincts for stealth, neurotoxin synthesis, and lockpicking.",
        "loadout": {
            "main_hand": "Serrated Scrap Dagger (1d6+3 Piercing + Bleed)",
            "off_hand": "Spring-Loaded Wrist Shank (1d4+3 Piercing)",
            "armor": "Cloak of Scavenged Shrouds (Light Leathers, +3 Stealth)",
            "chest": "Cloak of Scavenged Shrouds (Light Leathers, +3 Stealth)"
        },
        "equipped": {
            "main_hand": "Serrated Scrap Dagger (1d6+3 Piercing + Bleed)",
            "off_hand": "Spring-Loaded Wrist Shank (1d4+3 Piercing)",
            "armor": "Cloak of Scavenged Shrouds (Light Leathers, +3 Stealth)",
            "chest": "Cloak of Scavenged Shrouds (Light Leathers, +3 Stealth)"
        },
        "skills": {
            "Scrapper Infiltration": {"mastery": 185, "tier": "Journeyman", "description": "Unseen movement and exploitation of sightlines.", "milestones_unlocked": ["Silent Step"]},
            "Neurotoxin Synthesis": {"mastery": 140, "tier": "Journeyman", "description": "Distilling monster venom into weapon coatings.", "milestones_unlocked": ["Paralytic Blend"]},
            "Lockpick & Bypass": {"mastery": 205, "tier": "Journeyman", "description": "Circumventing tumblers and runic electronic latches.", "milestones_unlocked": ["Skeleton Keying"]}
        },
        "abilities": [
            "Shadow Strike (+3d6 Critical Bleed)",
            "Corrosive Neurotoxin Coating (-2 Enemy Saves)",
            "Scavenger's Eye (+30% bonus Col find)"
        ],
        "stances": {
            "shadow_meld": {
                "name": "Shadow Meld",
                "label": "👤 Shadow Meld",
                "tag": "[KIBS SNEAK]",
                "tactical_effect": "Melds into shadows; unleashes guaranteed sneak attack for 3d6+6 Piercing DMG + Bleed.",
                "desc": "High critical stealth DPS."
            },
            "venom_coating": {
                "name": "Venom Coating",
                "label": "🧪 Venom Coating",
                "tag": "[KIBS VENOM]",
                "tactical_effect": "Coats party weapons in neurotoxin; attacks deal +1d6 Acid damage and inflict -2 to enemy saving throws.",
                "desc": "Poison debuff support."
            },
            "lockpick_salvage": {
                "name": "Lockpick & Salvage",
                "label": "🗝️ Lockpick & Salvage",
                "tag": "[KIBS SALVAGE]",
                "tactical_effect": "Grants +4 bonus on all trap disarm and chest checks; increases party Col yield by +20%.",
                "desc": "Exploration and looting utility."
            }
        },
        "dual_tech_id": "shadow_flank_execution"
    },
    "Valeria": {
        "id": "companion_valeria",
        "name": "Valeria Vane",
        "class": "Primal Valkyrie / Aerial Skirmisher",
        "title": "Primal Valkyrie / Aerial Skirmisher",
        "role": "Aerial High-Ground Recon, Dive-Bomb Impalement & Radiant Shielding",
        "level": 4,
        "hp": 48,
        "max_hp": 48,
        "xp": 800,
        "next_level_xp": 1200,
        "stance": "aerial_divebomb",
        "morale": "Steady",
        "affinity": 25,
        "affinity_tier": "Acquaintance",
        "recruited": False,
        "active": False,
        "recruitment_location": "Warren County Barony Watchtower (Washington Borough, X:52, Y:50)",
        "recruitment_requirements": {"min_level": 3, "col_cost": 0, "faction": "Warren County Barony", "min_rep": 15, "description": "Reach Level 3 and achieve Respected standing (15+ Rep) with Warren County Barony."},
        "bio": "A phrenic human aerial skirmisher whose spine fused with aerodynamic aether-glider struts. Serves as Barony aerial perimeter commander.",
        "loadout": {
            "main_hand": "Winged Aether-Spear (1d10+4 Piercing)",
            "off_hand": "Solar Aegis Shield (+3 AC, Radiant Blind)",
            "armor": "Falcon Crest Mail (DR 2, Flight)",
            "chest": "Falcon Crest Mail (DR 2, Flight)"
        },
        "equipped": {
            "main_hand": "Winged Aether-Spear (1d10+4 Piercing)",
            "off_hand": "Solar Aegis Shield (+3 AC, Radiant Blind)",
            "armor": "Falcon Crest Mail (DR 2, Flight)",
            "chest": "Falcon Crest Mail (DR 2, Flight)"
        },
        "skills": {
            "Aerial Spear Technique": {"mastery": 260, "tier": "Adept", "description": "High-velocity vertical thrusts.", "milestones_unlocked": ["Dive-Strike Impact", "Falcon Lunge"]},
            "Aether Gliding": {"mastery": 240, "tier": "Journeyman", "description": "Mastery of thermal drafts and aetheric lift.", "milestones_unlocked": ["Thermal Glide"]},
            "Aegis Phalanx": {"mastery": 180, "tier": "Journeyman", "description": "Radiant shield positioning.", "milestones_unlocked": ["Blinding Glare"]}
        },
        "abilities": [
            "Solar Dive-Bomb (3d10 Radiant/Piercing + Knockdown)",
            "Skyward Interception (+3 AC to ground ally)",
            "Blinding Sunburst (DC 14 CON vs Blinded)"
        ],
        "stances": {
            "aerial_divebomb": {
                "name": "Aerial Dive-Bomb",
                "label": "🦅 Aerial Dive-Bomb",
                "tag": "[VALERIA DIVE]",
                "tactical_effect": "Dives from the sky dealing 2d10+4 Piercing DMG and knocking targets prone.",
                "desc": "High offensive aerial assault."
            },
            "radiant_bulwark": {
                "name": "Radiant Bulwark",
                "label": "🛡️ Radiant Bulwark",
                "tag": "[VALERIA BULWARK]",
                "tactical_effect": "Hovers above the vanguard, granting Banki +3 AC and absorbing projectile fire.",
                "desc": "Aerial defensive perimeter."
            },
            "high_overwatch": {
                "name": "High-Ground Overwatch",
                "label": "👁️ High-Ground Overwatch",
                "tag": "[VALERIA RECON]",
                "tactical_effect": "Scouts the perimeter from cloud altitude, revealing concealed enemies and granting +3 party Initiative.",
                "desc": "Aerial reconnaissance."
            }
        },
        "dual_tech_id": "valkyries_wrath"
    },
    "Morrigan": {
        "id": "companion_morrigan",
        "name": "Morrigan Black-Thorn",
        "class": "Abyssal Grave-Binder / Necrotic Hexer",
        "title": "Abyssal Grave-Binder / Necrotic Hexer",
        "role": "Necrotic Crowd Control, Soul-Siphon Drain & Bone Barricades",
        "level": 3,
        "hp": 34,
        "max_hp": 34,
        "xp": 450,
        "next_level_xp": 900,
        "stance": "soul_siphon",
        "morale": "Steady",
        "affinity": 20,
        "affinity_tier": "Acquaintance",
        "recruited": False,
        "active": False,
        "recruitment_location": "Musconetcong Crypts - Sunken Ossuary (X:45, Y:62)",
        "recruitment_requirements": {"min_level": 3, "col_cost": 0, "quest": "crypt_reanimator", "description": "Defeat the Crypt Reanimator in the Musconetcong Crypts and recover the Shattered Veil Tome."},
        "bio": "An umbral tiefling shadow-weaver who harvests digital soul-residue and deceased bio-mana from fallen monsters.",
        "loadout": {
            "main_hand": "Bone-Chime Scythe (1d8+3 Slashing + 1d6 Necrotic)",
            "off_hand": "Soul-Vessel Phylactery (Focus)",
            "armor": "Obsidian Shroud (Cloth, DR 1, +2 Spell DC)",
            "chest": "Obsidian Shroud (Cloth, DR 1, +2 Spell DC)"
        },
        "equipped": {
            "main_hand": "Bone-Chime Scythe (1d8+3 Slashing + 1d6 Necrotic)",
            "off_hand": "Soul-Vessel Phylactery (Focus)",
            "armor": "Obsidian Shroud (Cloth, DR 1, +2 Spell DC)",
            "chest": "Obsidian Shroud (Cloth, DR 1, +2 Spell DC)"
        },
        "skills": {
            "Necrotic Siphoning": {"mastery": 210, "tier": "Journeyman", "description": "Draining vitality from decaying tissue.", "milestones_unlocked": ["Soul Tap", "Life Leech"]},
            "Bone Matrix Weaving": {"mastery": 180, "tier": "Journeyman", "description": "Erecting calcified bone barriers.", "milestones_unlocked": ["Ossuary Shield"]},
            "Abyssal Hexes": {"mastery": 195, "tier": "Journeyman", "description": "Debilitating enemy metabolic functions.", "milestones_unlocked": ["Withering Curse"]}
        },
        "abilities": [
            "Soul-Siphon Lash (1d8 Necrotic DMG + restores 8 HP to lowest ally)",
            "Grave-Wall Erection (absorbs 30 incoming damage)",
            "Miasma of the Tomb (-2 Enemy Saves)"
        ],
        "stances": {
            "soul_siphon": {
                "name": "Soul-Siphon Drain",
                "label": "💀 Soul-Siphon Drain",
                "tag": "[MORRIGAN SIPHON]",
                "tactical_effect": "Drains 2d6 Necrotic DMG from target, transferring health to Banki.",
                "desc": "Lifesteal support stance."
            },
            "skeletal_wall": {
                "name": "Skeletal Wall",
                "label": "🦴 Skeletal Wall",
                "tag": "[MORRIGAN BONEWALL]",
                "tactical_effect": "Raises calcified bone palisades that intercept up to 30 damage from incoming enemy attacks.",
                "desc": "Barrier defense."
            },
            "miasma_curse": {
                "name": "Miasma Hex Aura",
                "label": "🌫️ Miasma Hex Aura",
                "tag": "[MORRIGAN MIASMA]",
                "tactical_effect": "Surrounds the enemy line in choking grave-mist; enemies suffer -2 to saving throws and lose 5 HP/turn.",
                "desc": "AOE necrotic debuff."
            }
        },
        "dual_tech_id": "grave_lord_cleave"
    },
    "Garrick": {
        "id": "companion_garrick",
        "name": "Garrick Stone-Grip",
        "class": "Seismic Brawler / Ki-Siphon Pugilist",
        "title": "Seismic Brawler / Ki-Siphon Pugilist",
        "role": "Unarmed Frontline Pressure, Kinetic Deflection & Break Gauge Stun",
        "level": 4,
        "hp": 52,
        "max_hp": 52,
        "xp": 750,
        "next_level_xp": 1200,
        "stance": "mountain_crusher",
        "morale": "Steady",
        "affinity": 25,
        "affinity_tier": "Acquaintance",
        "recruited": False,
        "active": False,
        "recruitment_location": "Pequest River Limestone Quarry (X:38, Y:42)",
        "recruitment_requirements": {"min_level": 3, "col_cost": 0, "stat_check": "STR 14 or Athletics 100", "description": "Defeat or spar with Garrick to a standstill in the Quarry fighting ring."},
        "bio": "An Earth Genasi structural ironworker whose knuckles and skin calcified into dense granite. Dominates the Pequest quarries.",
        "loadout": {
            "main_hand": "Granite-Studded Cestus (1d8+4 Bludgeoning)",
            "off_hand": "Granite-Studded Cestus (1d8+4 Bludgeoning)",
            "armor": "Iron-Thread Gi (Unarmored, DR 2)",
            "chest": "Iron-Thread Gi (Unarmored, DR 2)"
        },
        "equipped": {
            "main_hand": "Granite-Studded Cestus (1d8+4 Bludgeoning)",
            "off_hand": "Granite-Studded Cestus (1d8+4 Bludgeoning)",
            "armor": "Iron-Thread Gi (Unarmored, DR 2)",
            "chest": "Iron-Thread Gi (Unarmored, DR 2)"
        },
        "skills": {
            "Unarmed Pummeling": {"mastery": 280, "tier": "Adept", "description": "Bone-cracking pugilism.", "milestones_unlocked": ["Iron Fist", "Staggering Hook", "Haymaker"]},
            "Seismic Grounding": {"mastery": 220, "tier": "Journeyman", "description": "Rooting into tectonic bedrock.", "milestones_unlocked": ["Unyielding Stance"]},
            "Ki Kinetic Deflection": {"mastery": 190, "tier": "Journeyman", "description": "Deflecting incoming missiles with bare hands.", "milestones_unlocked": ["Missile Snatch"]}
        },
        "abilities": [
            "Tectonic Tremor Palm (2d8+5 Force + Stagger)",
            "Iron Shirt Deflection (Absorbs 15 Bludgeoning/Piercing)",
            "Earthquake Stomp (Prone all enemies in 10ft)"
        ],
        "stances": {
            "mountain_crusher": {
                "name": "Mountain-Crusher Stance",
                "label": "⛰️ Mountain-Crusher",
                "tag": "[GARRICK CRUSHER]",
                "tactical_effect": "Strikes target with 2d8+5 Bludgeoning DMG; chips boss Break Gauge by -35.",
                "desc": "High stun and break gauge pressure."
            },
            "ki_deflection": {
                "name": "Ki-Deflection Weave",
                "label": "🥋 Ki-Deflection Weave",
                "tag": "[GARRICK DEFLECT]",
                "tactical_effect": "Swats aside incoming projectiles and melee strikes, granting himself and Banki +3 AC.",
                "desc": "Martial defensive weave."
            },
            "seismic_slam": {
                "name": "Earth-Shatter Flurry",
                "label": "💥 Earth-Shatter Flurry",
                "tag": "[GARRICK FLURRY]",
                "tactical_effect": "Unleashes 3 rapid concussive palm strikes dealing 3d6+6 Force DMG and forcing DC 14 STR check vs Prone.",
                "desc": "Multi-hit knockdown flurry."
            }
        },
        "dual_tech_id": "seismic_cataclysm"
    },
    "Sariel": {
        "id": "companion_sariel",
        "name": "Sariel Swift-Wind",
        "class": "Verdant Deadeye / Beast-Stalker",
        "title": "Verdant Deadeye / Beast-Stalker",
        "role": "Extreme-Range Sniping, Crippling Arrow Volleys & Wilderness Tracking",
        "level": 3,
        "hp": 32,
        "max_hp": 32,
        "xp": 400,
        "next_level_xp": 900,
        "stance": "canopy_snipe",
        "morale": "Steady",
        "affinity": 20,
        "affinity_tier": "Acquaintance",
        "recruited": False,
        "active": False,
        "recruitment_location": "Jenny Jump Forest Canopy - Roaming Glade (X:58, Y:35)",
        "recruitment_requirements": {"min_level": 2, "col_cost": 0, "item_delivery": ["Venison Ration", "Wild Forest Herbs x2"], "description": "Track her scent through Jenny Jump Forest (Perception DC 13) and deliver forest rations."},
        "bio": "A wild wood elf ranger who nests in the 400-foot ironwood trees of Jenny Jump. Unerring sniper with living ironwood recurve bow.",
        "loadout": {
            "main_hand": "Living Ironwood Recurve Bow (1d10+4 Piercing)",
            "off_hand": "None (Two-Handed)",
            "armor": "Camouflage Ghillie-Cloak (Light, +4 Stealth)",
            "chest": "Camouflage Ghillie-Cloak (Light, +4 Stealth)"
        },
        "equipped": {
            "main_hand": "Living Ironwood Recurve Bow (1d10+4 Piercing)",
            "off_hand": "None (Two-Handed)",
            "armor": "Camouflage Ghillie-Cloak (Light, +4 Stealth)",
            "chest": "Camouflage Ghillie-Cloak (Light, +4 Stealth)"
        },
        "skills": {
            "Archery Mastery": {"mastery": 270, "tier": "Adept", "description": "Pinpoint extreme-range shooting.", "milestones_unlocked": ["Double Shot", "Ocular Piercing", "Eagle Eye"]},
            "Wilderness Stalking": {"mastery": 240, "tier": "Journeyman", "description": "Moving without disturbing leaf or twig.", "milestones_unlocked": ["Forest Ghost"]},
            "Beast Anatomy": {"mastery": 180, "tier": "Journeyman", "description": "Targeting beast tendon and heart nodes.", "milestones_unlocked": ["Cripple Tendon"]}
        },
        "abilities": [
            "Heartseeker Snipe (3d10 Piercing DMG from stealth)",
            "Barbed Hamstring Volley (Roots target for 1 turn)",
            "Wind-Guidance Aura (+2 Ranged ATK to party)"
        ],
        "stances": {
            "canopy_snipe": {
                "name": "Canopy Snipe",
                "label": "🏹 Canopy Snipe",
                "tag": "[SARIEL SNIPE]",
                "tactical_effect": "Fires from maximum concealment dealing 2d10+4 Piercing DMG, ignoring 50% enemy armor.",
                "desc": "High critical range sniping."
            },
            "suppression_volley": {
                "name": "Barbed Suppression Volley",
                "label": "🌧️ Barbed Volley",
                "tag": "[SARIEL VOLLEY]",
                "tactical_effect": "Rains barbed arrows in an arc; slows all advancing enemies and inflicts Bleed (6 DMG/turn).",
                "desc": "Area crowd control."
            },
            "stealth_ambush": {
                "name": "Woodland Camouflage",
                "label": "🌿 Woodland Camouflage",
                "tag": "[SARIEL CAMO]",
                "tactical_effect": "Melds into foliage; completely untargetable until next attack which is an automatic Critical Hit.",
                "desc": "Stealth setup."
            }
        },
        "dual_tech_id": "cyclone_arrow_storm"
    },
    "Kaelen": {
        "id": "companion_kaelen",
        "name": "Brother Kaelen",
        "class": "Sol-Templar / Radiant Apothecary",
        "title": "Sol-Templar / Radiant Apothecary",
        "role": "Frontline Healing, Radiant Flail Burst & Condition Cleansing",
        "level": 3,
        "hp": 40,
        "max_hp": 40,
        "xp": 450,
        "next_level_xp": 900,
        "stance": "radiant_bastion",
        "morale": "Steady",
        "affinity": 30,
        "affinity_tier": "Acquaintance",
        "recruited": False,
        "active": False,
        "recruitment_location": "St. Luke's Chapel Ruins (High Bridge Safe-Node, X:65, Y:55)",
        "recruitment_requirements": {"min_level": 2, "col_cost": 200, "description": "Donate 200 Col to the High Bridge hospice or restore the Sunstone Altar."},
        "bio": "An aasimar parish deacon and former EMT whose veins pulse with solar mana. Wields a heavy sunstone flail to protect the wounded.",
        "loadout": {
            "main_hand": "Radiant War-Flail (1d8+3 Bludgeoning + 1d8 Radiant)",
            "off_hand": "Sunstone Focus Censer (Holy Focus)",
            "armor": "Gilded Crusader Mail (Heavy, DR 2)",
            "chest": "Gilded Crusader Mail (Heavy, DR 2)"
        },
        "equipped": {
            "main_hand": "Radiant War-Flail (1d8+3 Bludgeoning + 1d8 Radiant)",
            "off_hand": "Sunstone Focus Censer (Holy Focus)",
            "armor": "Gilded Crusader Mail (Heavy, DR 2)",
            "chest": "Gilded Crusader Mail (Heavy, DR 2)"
        },
        "skills": {
            "Radiant Restoration": {"mastery": 250, "tier": "Adept", "description": "Channelling restorative solar fire.", "milestones_unlocked": ["Solar Mending", "Purifying Pulse"]},
            "War-Flail Discipline": {"mastery": 190, "tier": "Journeyman", "description": "Swinging spiked morningstar chains.", "milestones_unlocked": ["Shield Bypass"]},
            "Aura of Protection": {"mastery": 220, "tier": "Journeyman", "description": "Radiant protective aegis for allies.", "milestones_unlocked": ["Sanctuary Ward"]}
        },
        "abilities": [
            "Sun-Burst Heal (+25 HP to ally + cleanses poison/bleed)",
            "Solar Smite (+2d8 Radiant DMG vs Undead/Fiends)",
            "Aegis of the Brass Sun (+3 AC to adjacent allies)"
        ],
        "stances": {
            "radiant_bastion": {
                "name": "Radiant Bastion Aura",
                "label": "☀️ Radiant Bastion",
                "tag": "[KAELEN BASTION]",
                "tactical_effect": "Radiates solar protection; restores +8 HP to Banki each turn and grants +2 to all saving throws.",
                "desc": "Persistent healing aura."
            },
            "cleansing_sunburst": {
                "name": "Cleansing Sunburst",
                "label": "✨ Cleansing Sunburst",
                "tag": "[KAELEN SUNBURST]",
                "tactical_effect": "Unleashes blinding solar flash for 2d8+3 Radiant DMG; removes all debuffs from party.",
                "desc": "Damage and cleanse."
            },
            "crusader_smite": {
                "name": "Crusader Smite",
                "label": "🔨 Crusader Smite",
                "tag": "[KAELEN SMITE]",
                "tactical_effect": "Swings radiant flail dealing 1d10+4 Bludgeoning + 2d8 Radiant DMG, ignoring enemy shields.",
                "desc": "Offensive shield-breaker."
            }
        },
        "dual_tech_id": "dawn_breaker_smite"
    },
    "Zedd": {
        "id": "companion_zedd",
        "name": "Zeddicus Volt-Spark",
        "class": "Plasma-Mage / Galvanic Dynamo",
        "title": "Plasma-Mage / Galvanic Dynamo",
        "role": "Chain-Lightning AOE, Superconductor Field & Armor Splicing",
        "level": 3,
        "hp": 30,
        "max_hp": 30,
        "xp": 420,
        "next_level_xp": 900,
        "stance": "plasma_arc",
        "morale": "Steady",
        "affinity": 25,
        "affinity_tier": "Acquaintance",
        "recruited": False,
        "active": False,
        "recruitment_location": "Decommissioned Edison Substation (Belvidere Junction, X:30, Y:50)",
        "recruitment_requirements": {"min_level": 3, "col_cost": 0, "puzzle": "substation_grid", "description": "Solve the Substation Power-Grid puzzle (INT DC 13) or deliver 2 Voltaic Cores."},
        "bio": "A high-voltage lineman who survived a 500kV discharge when the Crucible hit. Fused with dorsal capacitors, he commands plasma arcs.",
        "loadout": {
            "main_hand": "Galvanic Arc Staff (1d6+3 Bludgeoning + 2d6 Lightning)",
            "off_hand": "Capacitor Battery Rig (Focus)",
            "armor": "Spark-Shield Coat (Cloth, DR 1, Lightning Immune)",
            "chest": "Spark-Shield Coat (Cloth, DR 1, Lightning Immune)"
        },
        "equipped": {
            "main_hand": "Galvanic Arc Staff (1d6+3 Bludgeoning + 2d6 Lightning)",
            "off_hand": "Capacitor Battery Rig (Focus)",
            "armor": "Spark-Shield Coat (Cloth, DR 1, Lightning Immune)",
            "chest": "Spark-Shield Coat (Cloth, DR 1, Lightning Immune)"
        },
        "skills": {
            "Galvanic Sorcery": {"mastery": 240, "tier": "Journeyman", "description": "Channelling high-voltage aetheric arcs.", "milestones_unlocked": ["Chain Lightning", "Static Overload"]},
            "Capacitor Engineering": {"mastery": 210, "tier": "Journeyman", "description": "Storing and regulating energetic voltage.", "milestones_unlocked": ["Overcharge Valve"]},
            "Dielectric Piercing": {"mastery": 180, "tier": "Journeyman", "description": "Melting metal armor with plasma heat.", "milestones_unlocked": ["Arc Weld"]}
        },
        "abilities": [
            "Ball Lightning Discharge (3d8 Lightning AOE)",
            "Static Overcharge (Weapon buff: +1d10 Shock DMG to Banki)",
            "Dielectric EMP (Stuns constructs for 1 turn)"
        ],
        "stances": {
            "plasma_arc": {
                "name": "Overcharge Plasma Arc",
                "label": "⚡ Plasma Arc",
                "tag": "[ZEDD PLASMA]",
                "tactical_effect": "Discharges chain lightning dealing 2d10+4 Shock DMG that arcs across up to 3 targets.",
                "desc": "Multi-target lightning assault."
            },
            "superconductor_field": {
                "name": "Superconductor Field",
                "label": "🌐 Superconductor Field",
                "tag": "[ZEDD FIELD]",
                "tactical_effect": "Deploys crackling electric perimeter; any enemy entering melee takes 1d8 Shock DMG and loses 10ft movement.",
                "desc": "Defensive area denial."
            },
            "capacitive_burst": {
                "name": "Static Discharge Burst",
                "label": "💥 Static Burst",
                "tag": "[ZEDD BURST]",
                "tactical_effect": "Vents all dorsal capacitors into a single concussive shockwave dealing 3d8 Force/Lightning DMG and knocking foes back 15ft.",
                "desc": "Point-blank peel."
            }
        },
        "dual_tech_id": "volt_tempest_detonation"
    },
    "Daphne": {
        "id": "companion_daphne",
        "name": "Daphne Leclair",
        "class": "Spellsinger / Skaldic Virtuoso",
        "title": "Spellsinger / Skaldic Virtuoso",
        "role": "Vocal Attack Buffs, Sonic Stuns & Skaldic Battle Anthems",
        "level": 3,
        "hp": 32,
        "max_hp": 32,
        "xp": 380,
        "next_level_xp": 900,
        "stance": "berserker_hymn",
        "morale": "Steady",
        "affinity": 25,
        "affinity_tier": "Acquaintance",
        "recruited": False,
        "active": False,
        "recruitment_location": "The Rusty Flagon Speakeasy (Easton Riverfront Node, X:22, Y:55)",
        "recruitment_requirements": {"min_level": 2, "col_cost": 350, "description": "Pay off her 350 Col tavern tab OR perform a collaborative battle ballad (CHA DC 14)."},
        "bio": "A half-elf siren-kin jazz singer whose vocal harmonies bend sound waves into sonic concussions and battle-buffs.",
        "loadout": {
            "main_hand": "Silvered Stiletto (1d4+3 Piercing)",
            "off_hand": "Resonating Aether-Lute (Focus)",
            "armor": "Velvet Performer's Doublet (+2 CHA, DR 1)",
            "chest": "Velvet Performer's Doublet (+2 CHA, DR 1)"
        },
        "equipped": {
            "main_hand": "Silvered Stiletto (1d4+3 Piercing)",
            "off_hand": "Resonating Aether-Lute (Focus)",
            "armor": "Velvet Performer's Doublet (+2 CHA, DR 1)",
            "chest": "Velvet Performer's Doublet (+2 CHA, DR 1)"
        },
        "skills": {
            "Spellsinging": {"mastery": 250, "tier": "Adept", "description": "Weaving acoustic vibrations into magic.", "milestones_unlocked": ["Sonic Boom", "Song of Valor"]},
            "Acoustic Manipulation": {"mastery": 200, "tier": "Journeyman", "description": "Bending resonance to disrupt spellcasting.", "milestones_unlocked": ["Counter-Melody"]},
            "Streetwise Performance": {"mastery": 180, "tier": "Journeyman", "description": "Extracting rumors and winning tavern crowds.", "milestones_unlocked": ["Silver Tongue"]}
        },
        "abilities": [
            "Song of Sovereign Might (+4 DMG & +2 ATK to Party)",
            "Discordant Screech (DC 14 CON vs Stun)",
            "Lullaby of the Void (Puts non-elite target to sleep)"
        ],
        "stances": {
            "berserker_hymn": {
                "name": "Hymn of the Berserker",
                "label": "🎶 Berserker Hymn",
                "tag": "[DAPHNE HYMN]",
                "tactical_effect": "Sings a thunderous battle chant; grants Banki +3 Attack rolls and +1d8 weapon damage.",
                "desc": "High offensive party buff."
            },
            "discordant_screech": {
                "name": "Discordant Screech",
                "label": "🔊 Discordant Screech",
                "tag": "[DAPHNE SCREECH]",
                "tactical_effect": "Plucks a shattering resonant chord dealing 2d6 Thunder DMG and forcing DC 14 CON check vs Disoriented.",
                "desc": "Sonic disruption."
            },
            "fleeting_shadows": {
                "name": "Song of Fleeting Shadows",
                "label": "🌫️ Fleeting Shadows",
                "tag": "[DAPHNE SHADOWS]",
                "tactical_effect": "Weaves acoustic dampening; grants all allies +4 Stealth and +2 Dodge AC.",
                "desc": "Evasive party defense."
            }
        },
        "dual_tech_id": "valkyrie_war_chorus"
    },
    "Rok": {
        "id": "companion_rok",
        "name": "Ragnarok 'Rok'",
        "class": "Juggernaut Marauder / Blood-Rager",
        "title": "Juggernaut Marauder / Blood-Rager",
        "role": "Berserk Melee Fury, High Physical DR & Twin Cleaver Slaughter",
        "level": 4,
        "hp": 58,
        "max_hp": 58,
        "xp": 850,
        "next_level_xp": 1200,
        "stance": "blood_frenzy",
        "morale": "Bloodthirsty",
        "affinity": 20,
        "affinity_tier": "Acquaintance",
        "recruited": False,
        "active": False,
        "recruitment_location": "Blood-Pit Arena (Oxford Iron Mines Slag Heaps, X:55, Y:45)",
        "recruitment_requirements": {"min_level": 3, "col_cost": 0, "duel": "slag_pit_brawl", "description": "Defeat Rok in the Slag Pit duel OR match him drink-for-drink in dwarven gut-burner ale (CON DC 15)."},
        "bio": "A half-orc bio-chimeric marauder who wields twin jagged slag-cleavers. Becomes exponentially deadlier as his health drops.",
        "loadout": {
            "main_hand": "Serrated Slag-Cleaver (1d10+4 Slashing)",
            "off_hand": "Serrated Slag-Cleaver (1d10+4 Slashing)",
            "armor": "Troll-Hide Kilt (Heavy Leathers, DR 3)",
            "chest": "Troll-Hide Kilt (Heavy Leathers, DR 3)"
        },
        "equipped": {
            "main_hand": "Serrated Slag-Cleaver (1d10+4 Slashing)",
            "off_hand": "Serrated Slag-Cleaver (1d10+4 Slashing)",
            "armor": "Troll-Hide Kilt (Heavy Leathers, DR 3)",
            "chest": "Troll-Hide Kilt (Heavy Leathers, DR 3)"
        },
        "skills": {
            "Dual-Axe Slaughter": {"mastery": 290, "tier": "Adept", "description": "Relentless twin-weapon onslaught.", "milestones_unlocked": ["Whirlwind Rake", "Decapitate", "Blood Fountain"]},
            "Pain Tolerance": {"mastery": 270, "tier": "Adept", "description": "Converting physical trauma into adrenaline.", "milestones_unlocked": ["Thick Skinned", "Berserk Vigor"]},
            "Intimidating Roar": {"mastery": 210, "tier": "Journeyman", "description": "Terrifying lesser foes with primal bellows.", "milestones_unlocked": ["Battle Shriek"]}
        },
        "abilities": [
            "Blood-Frenzy Charge (3d10+8 Slashing + Knocks Prone)",
            "Unyielding Rage (Cannot drop below 1 HP for 1 turn)",
            "Meat-Hook Cleave (Pulls enemy into melee range)"
        ],
        "stances": {
            "blood_frenzy": {
                "name": "Blood-Frenzy Rampage",
                "label": "🩸 Blood Frenzy",
                "tag": "[ROK FRENZY]",
                "tactical_effect": "Swings twin cleavers wildly dealing 2d10+6 Slashing DMG; gains +2 DMG for every 10 HP missing.",
                "desc": "Ramping berserk damage."
            },
            "unyielding_flesh": {
                "name": "Unyielding Flesh",
                "label": "🛡️ Unyielding Flesh",
                "tag": "[ROK FLESH]",
                "tactical_effect": "Tenses troll-grafted muscles; gains DR 4 against physical damage and taunts all active foes.",
                "desc": "Frontline berserk tanking."
            },
            "cleaver_whirl": {
                "name": "Whirlwind Slag-Torn",
                "label": "🌪️ Slag Whirlwind",
                "tag": "[ROK WHIRL]",
                "tactical_effect": "Spins in a tight circle dealing 2d8+4 Slashing DMG to all adjacent enemies with guaranteed Bleed.",
                "desc": "Melee AOE cleave."
            }
        },
        "dual_tech_id": "blood_twin_cleave"
    },
    "Lyra": {
        "id": "companion_lyra",
        "name": "Lyra Stargaze",
        "class": "Chronomancer / Temporal Weaver",
        "title": "Chronomancer / Temporal Weaver",
        "role": "Timeline Dilation, Haste Buffs, Slow Fields & Wound Reversal",
        "level": 4,
        "hp": 28,
        "max_hp": 28,
        "xp": 780,
        "next_level_xp": 1200,
        "stance": "temporal_haste",
        "morale": "Steady",
        "affinity": 25,
        "affinity_tier": "Acquaintance",
        "recruited": False,
        "active": False,
        "recruitment_location": "High Point Observatory Spire (Sussex Overlook, X:48, Y:12)",
        "recruitment_requirements": {"min_level": 4, "col_cost": 0, "item": "Refined Aether-Crystal", "description": "Reach Level 4 and calibrate the Astrolabe Focal Prism using an Aether-Crystal."},
        "bio": "An aether-born stargazer astrophysicist who manipulates timeline foam to speed allies, freeze foes, and rewind lethal wounds.",
        "loadout": {
            "main_hand": "Chrono-Staff of Moments (1d6+3 Bludgeoning + Time Warp)",
            "off_hand": "Hourglass Focus (Cosmic Focus)",
            "armor": "Star-Silk Robes (+2 INT, DR 1)",
            "chest": "Star-Silk Robes (+2 INT, DR 1)"
        },
        "equipped": {
            "main_hand": "Chrono-Staff of Moments (1d6+3 Bludgeoning + Time Warp)",
            "off_hand": "Hourglass Focus (Cosmic Focus)",
            "armor": "Star-Silk Robes (+2 INT, DR 1)",
            "chest": "Star-Silk Robes (+2 INT, DR 1)"
        },
        "skills": {
            "Chronomancy": {"mastery": 290, "tier": "Adept", "description": "Accelerating and decelerating causal flow.", "milestones_unlocked": ["Haste Glyphs", "Time Dilation", "Temporal Anchor"]},
            "Stargazing Telemetry": {"mastery": 240, "tier": "Journeyman", "description": "Calculating celestial alignment and odds.", "milestones_unlocked": ["Fate Reading"]},
            "Temporal Mending": {"mastery": 210, "tier": "Journeyman", "description": "Reversing physical damage into past states.", "milestones_unlocked": ["Rewind Tissue"]}
        },
        "abilities": [
            "Chrono-Stasis Bubble (Freezes target for 1 turn)",
            "Haste Surge (Grants Banki an extra standard action)",
            "Temporal Rewind (Reverses last turn's damage on ally)"
        ],
        "stances": {
            "temporal_haste": {
                "name": "Haste Surge Acceleration",
                "label": "⏳ Haste Surge",
                "tag": "[LYRA HASTE]",
                "tactical_effect": "Bends time around Banki; grants Banki +4 Initiative and an extra attack every other turn.",
                "desc": "Speed and action accelerator."
            },
            "time_dilation": {
                "name": "Time Dilation Field",
                "label": "🌀 Dilation Field",
                "tag": "[LYRA SLOW]",
                "tactical_effect": "Traps enemy frontliners in viscous time; enemies suffer -4 to AC and lose their reactions.",
                "desc": "Enemy time freeze."
            },
            "wound_echo": {
                "name": "Rewind Wound Echoes",
                "label": "⏪ Wound Rewind",
                "tag": "[LYRA REWIND]",
                "tactical_effect": "Rewinds time on the most damaged ally, restoring 20 HP from injuries sustained this combat.",
                "desc": "Temporal healing."
            }
        },
        "dual_tech_id": "temporal_shatter_strike"
    },
    "Titus": {
        "id": "companion_titus",
        "name": "Titus Sterling",
        "class": "Aegis-Automaton / Iron-Clad Sentinel",
        "title": "Aegis-Automaton / Iron-Clad Sentinel",
        "role": "Impenetrable Interception Tank, Blast Furnace Armor & Steam Concussion",
        "level": 4,
        "hp": 65,
        "max_hp": 65,
        "xp": 850,
        "next_level_xp": 1200,
        "stance": "iron_curtain",
        "morale": "Dignified",
        "affinity": 30,
        "affinity_tier": "Acquaintance",
        "recruited": False,
        "active": False,
        "recruitment_location": "Abandoned Bethlehem Steel Foundry (Lehigh Basin Node, X:18, Y:65)",
        "recruitment_requirements": {"min_level": 3, "col_cost": 0, "repair_items": ["Refined Aether-Alloy x2", "Clockwork Gyroscope"], "description": "Repair his fractured boiler core (Crafting DC 12) with alloy and clockwork parts."},
        "bio": "A sentient Victorian-era steam golem from Bethlehem Steel. Formally polite butler who absorbs up to 75% of party damage.",
        "loadout": {
            "main_hand": "Pneumatic Slag-Hammer (1d12+5 Bludgeoning)",
            "off_hand": "Steam-Buffered Kinetic Barrier (+4 AC, DR 2)",
            "armor": "Cast-Iron Boiler Chassis (Heavy Plate, DR 4)",
            "chest": "Cast-Iron Boiler Chassis (Heavy Plate, DR 4)"
        },
        "equipped": {
            "main_hand": "Pneumatic Slag-Hammer (1d12+5 Bludgeoning)",
            "off_hand": "Steam-Buffered Kinetic Barrier (+4 AC, DR 2)",
            "armor": "Cast-Iron Boiler Chassis (Heavy Plate, DR 4)",
            "chest": "Cast-Iron Boiler Chassis (Heavy Plate, DR 4)"
        },
        "skills": {
            "Sentinel Interception": {"mastery": 300, "tier": "Adept", "description": "Placing iron chassis between allies and harm.", "milestones_unlocked": ["Bodyguard Intercept", "Shield Ward", "Kinetic Absorption"]},
            "Blast Furnace Engineering": {"mastery": 250, "tier": "Adept", "description": "Regulating steam pressure and thermal vents.", "milestones_unlocked": ["Overheat Discharge"]},
            "Pneumatic Warfare": {"mastery": 220, "tier": "Journeyman", "description": "Heavy hammer strikes propelled by pistons.", "milestones_unlocked": ["Piston Slam"]}
        },
        "abilities": [
            "Iron Curtain Intercept (Absorbs 75% of damage intended for Banki)",
            "Steam Vent Blind (DC 14 CON vs Scalded/Blind)",
            "Pneumatic Crater Slam (3d10 Bludgeoning + Stun)"
        ],
        "stances": {
            "iron_curtain": {
                "name": "Iron-Curtain Interception",
                "label": "🛡️ Iron Curtain",
                "tag": "[TITUS INTERCEPT]",
                "tactical_effect": "Interposes iron frame; intercepts 75% of incoming damage to Banki, reducing it by DR 4.",
                "desc": "Ultimate damage protection."
            },
            "steam_flare": {
                "name": "Steam Exhaust Flare",
                "label": "💨 Steam Flare",
                "tag": "[TITUS STEAM]",
                "tactical_effect": "Vents boiling steam in a 15ft cone; deals 2d8 Fire DMG and inflicts -3 to enemy attack rolls.",
                "desc": "Area blindness and burn."
            },
            "concussive_smash": {
                "name": "Pneumatic Slag Slam",
                "label": "🔨 Slag Slam",
                "tag": "[TITUS SMASH]",
                "tactical_effect": "Brings slag-hammer down with 2d12+5 Bludgeoning DMG; destroys 40 points of Boss Break Gauge.",
                "desc": "Heavy bludgeoning stagger."
            }
        },
        "dual_tech_id": "foundry_forge_smash"
    },
    "Nyssa": {
        "id": "companion_nyssa",
        "name": "Nyssa Thorn-Weft",
        "class": "Primal Shapeshifter / Beast-Warden",
        "title": "Primal Shapeshifter / Beast-Warden",
        "role": "Fluid Form-Shifting (Sabre-Cat Pounce DPS / Cave-Bear Fortitude)",
        "level": 3,
        "hp": 38,
        "max_hp": 38,
        "xp": 450,
        "next_level_xp": 900,
        "stance": "cat_pounce",
        "morale": "Steady",
        "affinity": 25,
        "affinity_tier": "Acquaintance",
        "recruited": False,
        "active": False,
        "recruitment_location": "Delaware Water Gap Wolf Den (X:32, Y:30)",
        "recruitment_requirements": {"min_level": 3, "col_cost": 0, "skill_check": "Survival 120 or Animal Empathy", "description": "Tame or cure the infected Alpha Dire-Wolf pack leader alongside Nyssa."},
        "bio": "A beast-kin felis shapeshifter who flows between a deadly stealth sabre-cat and an armored, raging cave-bear.",
        "loadout": {
            "main_hand": "Obsidian Claw-Gauntlets (1d8+3 Slashing + Bleed)",
            "off_hand": "Obsidian Claw-Gauntlets (1d8+3 Slashing)",
            "armor": "Living Bramble Armor (DR 2, Thorns)",
            "chest": "Living Bramble Armor (DR 2, Thorns)"
        },
        "equipped": {
            "main_hand": "Obsidian Claw-Gauntlets (1d8+3 Slashing + Bleed)",
            "off_hand": "Obsidian Claw-Gauntlets (1d8+3 Slashing)",
            "armor": "Living Bramble Armor (DR 2, Thorns)",
            "chest": "Living Bramble Armor (DR 2, Thorns)"
        },
        "skills": {
            "Primal Shapeshifting": {"mastery": 270, "tier": "Adept", "description": "Metamorphic biology into apex predators.", "milestones_unlocked": ["Feline Quickstep", "Ursine Thickhide", "Predator Instinct"]},
            "Bramble Entanglement": {"mastery": 200, "tier": "Journeyman", "description": "Summoning thorny vines from soil.", "milestones_unlocked": ["Grasping Roots"]},
            "Predator Tracking": {"mastery": 220, "tier": "Journeyman", "description": "Scenting prey and tracking blood trails.", "milestones_unlocked": ["Blood Scent"]}
        },
        "abilities": [
            "Sabre-Cat Pounce (3d8 Slashing + Knocks Prone + Bleed)",
            "Cave-Bear Roar (Gains +25 Temporary HP + Taunts)",
            "Thorn Bramble Spikes (Entangles foes, 1d8 Piercing/turn)"
        ],
        "stances": {
            "cat_pounce": {
                "name": "Sabre-Cat Pounce",
                "label": "🐆 Sabre-Cat Pounce",
                "tag": "[NYSSA POUNCE]",
                "tactical_effect": "Pounces on vulnerable targets dealing 2d8+5 Slashing DMG and inflicting severe Bleed (8 DMG/turn).",
                "desc": "High critical burst mode."
            },
            "bear_form": {
                "name": "Bear-Form Fortitude",
                "label": "🐻 Bear Fortitude",
                "tag": "[NYSSA BEAR]",
                "tactical_effect": "Shifts into giant cave-bear; gains +20 Temp HP, DR 3, and forces hostiles to focus on her.",
                "desc": "Tanking form."
            },
            "bramble_trap": {
                "name": "Bramble Entangle",
                "label": "🌿 Bramble Entangle",
                "tag": "[NYSSA ROOTS]",
                "tactical_effect": "Summons living briars that root up to 2 enemies in place for 1 turn, preventing movement.",
                "desc": "Area crowd control."
            }
        },
        "dual_tech_id": "pack_hunt_ambush"
    },
    "Malakor": {
        "id": "companion_malakor",
        "name": "Malakor",
        "class": "Eldritch Hexblade / Void-Pact Siphon",
        "title": "Eldritch Hexblade / Void-Pact Siphon",
        "role": "Anti-Mage Execution, Resource Siphon & Shadow Teleportation",
        "level": 4,
        "hp": 42,
        "max_hp": 42,
        "xp": 800,
        "next_level_xp": 1200,
        "stance": "void_edge",
        "morale": "Steady",
        "affinity": 20,
        "affinity_tier": "Acquaintance",
        "recruited": False,
        "active": False,
        "recruitment_location": "Decommissioned Limestone Caverns (Pohatcong Sinkholes, X:42, Y:56)",
        "recruitment_requirements": {"min_level": 3, "col_cost": 0, "item": "Corrupted Void-Shard", "description": "Deliver a Corrupted Void-Shard from an Elite Abyssal mob to seal a blood-oath binding pact."},
        "bio": "A void-touched tiefling whose Greatsword 'Scourge-Drinker' drains enemy mana, active spell slots, and kinetic shielding.",
        "loadout": {
            "main_hand": "Void-Etched Greatsword (2d6+4 Slashing + Void Siphon)",
            "off_hand": "Null-Glyph Buckler (+2 AC, Spell Absorber)",
            "armor": "Shadow-Steel Hauberk (DR 2, Magic Resist)",
            "chest": "Shadow-Steel Hauberk (DR 2, Magic Resist)"
        },
        "equipped": {
            "main_hand": "Void-Etched Greatsword (2d6+4 Slashing + Void Siphon)",
            "off_hand": "Null-Glyph Buckler (+2 AC, Spell Absorber)",
            "armor": "Shadow-Steel Hauberk (DR 2, Magic Resist)",
            "chest": "Shadow-Steel Hauberk (DR 2, Magic Resist)"
        },
        "skills": {
            "Hexblade Greatsword": {"mastery": 280, "tier": "Adept", "description": "Heavy two-handed strikes imbued with void.", "milestones_unlocked": ["Void Cleave", "Severing Arc", "Soul Drinker"]},
            "Eldritch Invocation": {"mastery": 240, "tier": "Journeyman", "description": "Channelling dark patronage from beyond.", "milestones_unlocked": ["Armor of Agathys"]},
            "Anti-Magic Severing": {"mastery": 210, "tier": "Journeyman", "description": "Dispelling magical barriers and shields.", "milestones_unlocked": ["Nullify Matrix"]}
        },
        "abilities": [
            "Void-Blade Smite (3d10 Void DMG + drains 20% enemy resource)",
            "Spell-Eater Ward (Absorbs 1 spell and converts to 15 HP)",
            "Shadow Step (Teleports 30ft behind target)"
        ],
        "stances": {
            "void_edge": {
                "name": "Void-Edge Siphon",
                "label": "🌌 Void-Edge Siphon",
                "tag": "[MALAKOR VOID]",
                "tactical_effect": "Cleaves through target for 2d6+5 Void DMG, draining enemy combat resources and buffing Banki.",
                "desc": "Anti-resource damage."
            },
            "spell_eater": {
                "name": "Spell-Eater Ward",
                "label": "🔮 Spell-Eater Ward",
                "tag": "[MALAKOR WARD]",
                "tactical_effect": "Raises void buckler; absorbs all magical projectile damage directed at the party this turn.",
                "desc": "Magic damage negation."
            },
            "shadow_rend": {
                "name": "Abyssal Step Execution",
                "label": "👤 Abyssal Step",
                "tag": "[MALAKOR SHADOW]",
                "tactical_effect": "Blinks through reality into the backline, executing an unblockable strike dealing 3d8+4 Critical DMG.",
                "desc": "Backline assassin strike."
            }
        },
        "dual_tech_id": "void_abyss_cleave"
    },
    "Thorne": {
        "id": "companion_thorne",
        "name": "Dr. Alistair Thorne",
        "class": "Alchemical Saboteur / Toxicologist",
        "title": "Alchemical Saboteur / Toxicologist",
        "role": "Armor-Stripping Vitriol, Toxic Cloud Control & Adrenaline Injections",
        "level": 3,
        "hp": 30,
        "max_hp": 30,
        "xp": 450,
        "next_level_xp": 900,
        "stance": "vitriol_salvo",
        "morale": "Maniacal",
        "affinity": 25,
        "affinity_tier": "Acquaintance",
        "recruited": False,
        "active": False,
        "recruitment_location": "Abandoned Chemical Works (Phillipsburg Flats, X:26, Y:60)",
        "recruitment_requirements": {"min_level": 3, "col_cost": 0, "quest": "chemical_leak", "description": "Neutralize the chemical vat leak (Crafting/Perception DC 13) and recover his stolen journals."},
        "bio": "A manic chemical engineer and Elora's eccentric uncle. Dissolves monster armor with hyper-vitriol and juices allies with adrenaline.",
        "loadout": {
            "main_hand": "Pneumatic Acid-Siphon Cannon (1d8+3 Acid + Armor Melt)",
            "off_hand": "Bandolier of Corrosive Flasks (Alchemical Focus)",
            "armor": "Lead-Lined Hazard Apron (DR 1, Acid/Poison Immune)",
            "chest": "Lead-Lined Hazard Apron (DR 1, Acid/Poison Immune)"
        },
        "equipped": {
            "main_hand": "Pneumatic Acid-Siphon Cannon (1d8+3 Acid + Armor Melt)",
            "off_hand": "Bandolier of Corrosive Flasks (Alchemical Focus)",
            "armor": "Lead-Lined Hazard Apron (DR 1, Acid/Poison Immune)",
            "chest": "Lead-Lined Hazard Apron (DR 1, Acid/Poison Immune)"
        },
        "skills": {
            "Volatile Chemistry": {"mastery": 270, "tier": "Adept", "description": "Mixing unstable exothermic acids and gases.", "milestones_unlocked": ["Corrosive Brew", "Nitro Flask", "Thermite Compound"]},
            "Toxicology": {"mastery": 230, "tier": "Journeyman", "description": "Formulating paralytic neurotoxins.", "milestones_unlocked": ["Neuro-Darts"]},
            "Combat Bio-Stimulants": {"mastery": 210, "tier": "Journeyman", "description": "Adrenaline and stamina injections.", "milestones_unlocked": ["Adrenal Rush"]}
        },
        "abilities": [
            "Hyper-Vitriol Acid Bomb (Melt target AC by -4 permanently)",
            "Toxic Cloudkill Flask (15ft choking gas, 2d6 Poison/turn)",
            "Adrenaline Bio-Stim (+4 STR/DEX to Banki for 2 turns)"
        ],
        "stances": {
            "vitriol_salvo": {
                "name": "Corrosive Acid Salvo",
                "label": "🧪 Vitriol Salvo",
                "tag": "[THORNE ACID]",
                "tactical_effect": "Hurls bubbling acid flasks dealing 2d6+3 Acid DMG and permanently degrading target AC by -2.",
                "desc": "Armor-shredding debuff."
            },
            "toxic_smokescreen": {
                "name": "Cloudkill Smokescreen",
                "label": "🌫️ Toxic Cloudkill",
                "tag": "[THORNE SMOKE]",
                "tactical_effect": "Detonates thick chemical smoke; blinds hostiles (-3 to hit) while party gains full concealment.",
                "desc": "Obscuring defense."
            },
            "adrenal_injection": {
                "name": "Adrenaline Stim Injection",
                "label": "💉 Adrenal Stim",
                "tag": "[THORNE STIM]",
                "tactical_effect": "Injects Banki with hyper-adrenaline; Banki deals +1d10 bonus physical damage on all attacks this turn.",
                "desc": "Allied damage booster."
            }
        },
        "dual_tech_id": "corrosive_shatter_bomb"
    },
    "Teresa": {
        "id": "companion_teresa",
        "name": "Sister Teresa",
        "class": "Inquisitor / Witch-Hunter",
        "title": "Inquisitor / Witch-Hunter",
        "role": "Silver Ranged Execution, Weakness Exposure & Anti-Aberration Stake",
        "level": 3,
        "hp": 36,
        "max_hp": 36,
        "xp": 450,
        "next_level_xp": 900,
        "stance": "silver_snipe",
        "morale": "Resolute",
        "affinity": 30,
        "affinity_tier": "Acquaintance",
        "recruited": False,
        "active": False,
        "recruitment_location": "Old Moravian Mission Ruins (Hope Township, X:50, Y:30)",
        "recruitment_requirements": {"min_level": 2, "col_cost": 0, "dialogue": "truth_glyph", "description": "Pass her truth-testing glyph (WIS DC 13) or assist in exposing a cultist spy in Hope Township."},
        "bio": "A former criminal prosecutor turned Silver Flame Inquisitor. Uses silver truth-runes and heavy stake crossbows to execute heretics.",
        "loadout": {
            "main_hand": "Silver-Chambered Crossbow (1d10+3 Piercing + Silver)",
            "off_hand": "Blessed Consecrated Estoc (1d8+3 Piercing)",
            "armor": "Inquisitor's Leather Duster (+2 WIS, DR 1)",
            "chest": "Inquisitor's Leather Duster (+2 WIS, DR 1)"
        },
        "equipped": {
            "main_hand": "Silver-Chambered Crossbow (1d10+3 Piercing + Silver)",
            "off_hand": "Blessed Consecrated Estoc (1d8+3 Piercing)",
            "armor": "Inquisitor's Leather Duster (+2 WIS, DR 1)",
            "chest": "Inquisitor's Leather Duster (+2 WIS, DR 1)"
        },
        "skills": {
            "Inquisitorial Crossbow": {"mastery": 260, "tier": "Adept", "description": "Driving heavy consecrated silver stakes.", "milestones_unlocked": ["Silver Stake", "Pinning Bolt", "Judgment Volley"]},
            "Discernment of Truth": {"mastery": 240, "tier": "Journeyman", "description": "Seeing through illusions and shapeshifters.", "milestones_unlocked": ["True Sight"]},
            "Cestus & Estoc Fencing": {"mastery": 190, "tier": "Journeyman", "description": "Close-range execution maneuvers.", "milestones_unlocked": ["Parry & Riposte"]}
        },
        "abilities": [
            "Silver Stake Execution (3d10 Piercing vs Aberration/Undead)",
            "Witch-Hunter's Brand (Target cannot turn invisible or heal for 2 turns)",
            "Solemn Verdict (+3 Critical threat range to party)"
        ],
        "stances": {
            "silver_snipe": {
                "name": "Silver-Bolt Snipe",
                "label": "🏹 Silver Snipe",
                "tag": "[TERESA SNIPE]",
                "tactical_effect": "Fires a silver-tipped stake dealing 2d8+4 Piercing DMG (+2d8 vs Aberrations/Undead) and pinning target.",
                "desc": "Anti-fiend/undead sniper."
            },
            "truth_judgment": {
                "name": "True-Sight Judgment",
                "label": "⚖️ True-Sight Judgment",
                "tag": "[TERESA JUDGMENT]",
                "tactical_effect": "Paints target with silver flame; exposes physical weaknesses, increasing Banki's crit chance to 18-20.",
                "desc": "Critical threat amplifier."
            },
            "witch_hunter_brand": {
                "name": "Witch-Hunter's Brand",
                "label": "🔥 Witch Brand",
                "tag": "[TERESA BRAND]",
                "tactical_effect": "Brands target with holy fire; target loses 8 HP/turn and cannot regenerate health or phase shift.",
                "desc": "Anti-healing brand."
            }
        },
        "dual_tech_id": "inquisition_execution"
    }
}

DUAL_TECH_COMBOS = {
    "runic_axe_storm": {
        "id": "runic_axe_storm",
        "name": "Runic Axe Storm",
        "partners": ["Banki", "Ren"],
        "req_affinity": 50,
        "desc": "Banki executes a furious whirlwind cleave while Ren fires lightning runes directly into the axe head, unleashing a 360° chain-lightning cyclone.",
        "damage": "4d10+8 Slashing + 2d8 Lightning AOE",
        "effect": "Hits all surrounding enemies, deals 4d10+8 Slashing + 2d8 Lightning DMG and inflicts Stagger on secondary targets.",
        "log_tag": "[DUAL-TECH: BANKI + REN -> RUNIC AXE STORM]"
    },
    "titans_anvil_shockwave": {
        "id": "titans_anvil_shockwave",
        "name": "Titan's Anvil Shockwave",
        "partners": ["Banki", "Torvald"],
        "req_affinity": 50,
        "desc": "Torvald plants his adamant tower shield while Banki strikes the shield's runic center with his Trench Hammer, detonating a sonic kinetic shockwave.",
        "damage": "3d12+10 Force DMG",
        "effect": "Inflicts 3d12+10 Force DMG and shatters 60 Break Gauge points (guaranteed boss STAGGER).",
        "log_tag": "[DUAL-TECH: BANKI + TORVALD -> TITAN'S ANVIL SHOCKWAVE]"
    },
    "spellblade_vortex": {
        "id": "spellblade_vortex",
        "name": "Spellblade Vortex",
        "partners": ["Banki", "Elora"],
        "req_affinity": 50,
        "desc": "Banki hurls his bearded axe into Elora's dimensional spatial rift; the blade ricochets between 3 targets enveloped in cold aether-flames.",
        "damage": "3d8 Slashing + 3d8 Frost-Burn to 3 targets",
        "effect": "Cleaves through 3 enemies bypassing 50% Armor Class.",
        "log_tag": "[DUAL-TECH: BANKI + ELORA -> SPELLBLADE VORTEX]"
    },
    "shadow_flank_execution": {
        "id": "shadow_flank_execution",
        "name": "Shadow-Flank Execution",
        "partners": ["Banki", "Kibs"],
        "req_affinity": 50,
        "desc": "Kibs throws an aetheric flash-smoke bomb blinding the primary foe while Banki steps through the blind spot for a guaranteed decapitation strike.",
        "damage": "5d10+12 Critical Slashing DMG",
        "effect": "Guaranteed critical hit dealing 5d10+12 Slashing DMG and severe Bleed (10 DMG/turn).",
        "log_tag": "[DUAL-TECH: BANKI + KIBS -> SHADOW-FLANK EXECUTION]"
    },
    "valkyries_wrath": {
        "id": "valkyries_wrath",
        "name": "Valkyrie's Sky-Cleave",
        "partners": ["Banki", "Valeria"],
        "req_affinity": 50,
        "desc": "Valeria lifts Banki into an aerial trajectory before hurling him downward in a terminal-velocity dive-bomb while unleashing radiant spear salvos.",
        "damage": "4d10+10 Radiant Slashing + 2d8 Piercing AOE",
        "effect": "Inflicts 4d10+10 Radiant Slashing DMG to primary target and 2d8 Piercing to surrounding foes with guaranteed Knockdown.",
        "log_tag": "[DUAL-TECH: BANKI + VALERIA -> VALKYRIE'S SKY-CLEAVE]"
    },
    "grave_lord_cleave": {
        "id": "grave_lord_cleave",
        "name": "Grave-Lord Soul Reaver",
        "partners": ["Banki", "Morrigan"],
        "req_affinity": 50,
        "desc": "Morrigan binds the enemy's life-force in necrotic soul-chains as Banki cleaves through the tether, detonating a necrotic siphon that leeches vital essence.",
        "damage": "4d10+8 Slashing + 3d8 Necrotic DMG",
        "effect": "Deals 4d10+8 Slashing + 3d8 Necrotic DMG; heals Banki and Morrigan for 50% of necrotic damage dealt.",
        "log_tag": "[DUAL-TECH: BANKI + MORRIGAN -> GRAVE-LORD SOUL REAVER]"
    },
    "seismic_cataclysm": {
        "id": "seismic_cataclysm",
        "name": "Seismic Cataclysm",
        "partners": ["Banki", "Garrick"],
        "req_affinity": 50,
        "desc": "Garrick channels ki into a seismic earth-breaker slam while Banki drives his Trench Hammer into the fractured faultline, launching explosive tectonic debris.",
        "damage": "5d10+12 Bludgeoning Force DMG",
        "effect": "Shatters 75 Break Gauge points (guaranteed boss STUN), dealing 5d10+12 Bludgeoning Force DMG in a 20ft radius.",
        "log_tag": "[DUAL-TECH: BANKI + GARRICK -> SEISMIC CATACLYSM]"
    },
    "cyclone_arrow_storm": {
        "id": "cyclone_arrow_storm",
        "name": "Cyclone Arrow Tempest",
        "partners": ["Banki", "Sariel"],
        "req_affinity": 50,
        "desc": "Sariel fires a spiral gale-force volley pinning the targets to the earth while Banki charges through the vortex with twin-axe whirlwind cleaves.",
        "damage": "3d10+6 Slashing + 4d6 Wind-Piercing DMG",
        "effect": "Pins targets for 1 turn (Immobilized) and deals 3d10+6 Slashing + 4d6 Piercing DMG across the line.",
        "log_tag": "[DUAL-TECH: BANKI + SARIEL -> CYCLONE ARROW TEMPEST]"
    },
    "dawn_breaker_smite": {
        "id": "dawn_breaker_smite",
        "name": "Dawn-Breaker Radiant Smite",
        "partners": ["Banki", "Kaelen"],
        "req_affinity": 50,
        "desc": "Brother Kaelen invokes the Sol-Altar's zenith light, wrapping Banki's weapons in blinding solar fire as Banki delivers an overhead solar execution strike.",
        "damage": "4d10+10 Radiant/Fire DMG",
        "effect": "Deals 4d10+10 Radiant DMG (+4d10 bonus vs Undead/Corrupted), Blinds targets for 2 turns, and restores 25 HP to all allies.",
        "log_tag": "[DUAL-TECH: BANKI + KAELEN -> DAWN-BREAKER RADIANT SMITE]"
    },
    "volt_tempest_detonation": {
        "id": "volt_tempest_detonation",
        "name": "Volt-Tempest Plasma Detonation",
        "partners": ["Banki", "Zedd"],
        "req_affinity": 50,
        "desc": "Zedd hurls a high-voltage plasma sphere into the target's center-mass, which Banki violently detonates with a thunderous kinetic hammer impact.",
        "damage": "3d10+8 Bludgeoning + 4d8 Chain-Lightning DMG",
        "effect": "Detonates in a chain-lightning shockwave leaping to up to 4 nearby hostiles, inflicting Stunned on a failed DC 15 CON save.",
        "log_tag": "[DUAL-TECH: BANKI + ZEDD -> VOLT-TEMPEST PLASMA DETONATION]"
    },
    "valkyrie_war_chorus": {
        "id": "valkyrie_war_chorus",
        "name": "Valkyrie Battle Anthem",
        "partners": ["Banki", "Daphne"],
        "req_affinity": 50,
        "desc": "Daphne weaves a resounding skaldic war-chant that synchronizes heartbeats and multiplies adrenaline, propelling Banki into a hyper-accelerated strike frenzy.",
        "damage": "6d8+12 Sonic-Empowered Slashing DMG",
        "effect": "Grants Banki +2 extra attacks this turn, deals 6d8+12 Sonic Slashing DMG, and grants all party members +4 Attack and +15 Temp HP for 3 turns.",
        "log_tag": "[DUAL-TECH: BANKI + DAPHNE -> VALKYRIE BATTLE ANTHEM]"
    },
    "blood_twin_cleave": {
        "id": "blood_twin_cleave",
        "name": "Blood-Twin Berserker Cleave",
        "partners": ["Banki", "Rok"],
        "req_affinity": 50,
        "desc": "Banki and Rok roar in feral unison, executing synchronised spinning greataxe and broadaxe cleaves that tear through armor like parchment.",
        "damage": "6d12+16 Brutal Slashing DMG",
        "effect": "Bypasses 100% of enemy Damage Reduction, inflicts 6d12+16 Slashing DMG and severe Arterial Bleed (15 DMG/turn for 3 turns).",
        "log_tag": "[DUAL-TECH: BANKI + ROK -> BLOOD-TWIN BERSERKER CLEAVE]"
    },
    "temporal_shatter_strike": {
        "id": "temporal_shatter_strike",
        "name": "Temporal Stasis Shatter",
        "partners": ["Banki", "Lyra"],
        "req_affinity": 50,
        "desc": "Lyra locks the enemy within a 3-second localized time-stop capsule; Banki unleashes four devastating attacks that detonate simultaneously the instant time resumes.",
        "damage": "8d8+16 Chrono-Kinetic Force DMG",
        "effect": "Enemy is helpless during setup; deals 8d8+16 Force DMG and resets enemy initiative/turn order to the very bottom.",
        "log_tag": "[DUAL-TECH: BANKI + LYRA -> TEMPORAL STASIS SHATTER]"
    },
    "foundry_forge_smash": {
        "id": "foundry_forge_smash",
        "name": "Foundry Hydraulic Overdrive",
        "partners": ["Banki", "Titus"],
        "req_affinity": 50,
        "desc": "Titus locks the target in steam-powered pneumatic vise-clamps while Banki strikes Titus's chest-anvil, driving a superheated hydraulic piston through the target.",
        "damage": "5d10+14 Fire & Bludgeoning DMG",
        "effect": "Deals 5d10+14 Fire/Bludgeoning DMG, permanently shreds target Armor Class by -4, and leaves the foe Prone.",
        "log_tag": "[DUAL-TECH: BANKI + TITUS -> FOUNDRY HYDRAULIC OVERDRIVE]"
    },
    "pack_hunt_ambush": {
        "id": "pack_hunt_ambush",
        "name": "Apex Pack-Hunt Ambush",
        "partners": ["Banki", "Nyssa"],
        "req_affinity": 50,
        "desc": "Nyssa takes Dire-Wolf aspect to drag the target down by the throat while Banki closes the pincer from the blindside with a merciless downward execution stroke.",
        "damage": "4d10+10 Slashing + 3d8 Beast-Tear Piercing DMG",
        "effect": "Knocks target Prone, inflicts Crippled status (-50% movement speed), and deals 4d10+10 Slashing + 3d8 Piercing DMG.",
        "log_tag": "[DUAL-TECH: BANKI + NYSSA -> APEX PACK-HUNT AMBUSH]"
    },
    "void_abyss_cleave": {
        "id": "void_abyss_cleave",
        "name": "Void-Singularity Cleave",
        "partners": ["Banki", "Malakor"],
        "req_affinity": 50,
        "desc": "Malakor rips open an eldritch void anomaly that collapses space and draws all surrounding foes into a singular vortex, right into Banki's full-force whirlwind sweep.",
        "damage": "5d8 Slashing + 4d8 Void-Cold DMG (AOE)",
        "effect": "Pulls all enemies in 30ft into melee range, deals 5d8 Slashing + 4d8 Void DMG, and inflicts -3 to all enemy attack rolls for 2 turns.",
        "log_tag": "[DUAL-TECH: BANKI + MALAKOR -> VOID-SINGULARITY CLEAVE]"
    },
    "corrosive_shatter_bomb": {
        "id": "corrosive_shatter_bomb",
        "name": "Corrosive Slag Shatter",
        "partners": ["Banki", "Thorne"],
        "req_affinity": 50,
        "desc": "Dr. Thorne hurls a concentrated vial of alchemical vitriol onto the enemy's armor plate, followed instantly by Banki's concussive hammer strike that shatters the brittle slag.",
        "damage": "3d10+8 Bludgeoning + 4d6 Acid DMG",
        "effect": "Completely dissolves enemy Damage Reduction (DR reduced to 0), deals 3d10+8 Bludgeoning + 4d6 Acid DMG, and leaves a lingering acid pool.",
        "log_tag": "[DUAL-TECH: BANKI + THORNE -> CORROSIVE SLAG SHATTER]"
    },
    "inquisition_execution": {
        "id": "inquisition_execution",
        "name": "Grand Inquisitor's Execution",
        "partners": ["Banki", "Teresa"],
        "req_affinity": 50,
        "desc": "Sister Teresa pins the condemned hostile to the earth with a consecrated heavy silver stake and recites the final rite while Banki delivers a thunderous decapitation blow.",
        "damage": "6d10+15 Holy Slashing DMG",
        "effect": "Instant execution threshold against foes below 25% HP; otherwise deals 6d10+15 Holy Slashing DMG and permanently prevents resurrection or undead reanimation.",
        "log_tag": "[DUAL-TECH: BANKI + TERESA -> GRAND INQUISITOR'S EXECUTION]"
    }
}


def ensure_party_system(player_state):
    """
    Initializes the multi-companion party system in player_state:
    - Maintains 'companions' dictionary with full profiles
    - Enforces active party cap of 4 (Banki + up to 3 active companions)
    """
    import copy
    comps = player_state.setdefault("companions", {})
    if not isinstance(comps, dict):
        comps = {}
        player_state["companions"] = comps

    # Ensure all recruitable companion archetypes exist in record
    for c_name, c_def in RECRUITABLE_COMPANIONS.items():
        if c_name not in comps:
            comps[c_name] = copy.deepcopy(c_def)
        else:
            # Backfill missing keys on existing companions
            for k, v in c_def.items():
                if k not in comps[c_name]:
                    comps[c_name][k] = copy.deepcopy(v)

    # Ren is recruited and active by default
    comps["Ren"]["recruited"] = True
    if "active" not in comps["Ren"]:
        comps["Ren"]["active"] = True

    return comps


def get_active_party(player_state):
    """
    Returns the list of currently active companion dictionaries (max 3, plus Banki).
    """
    comps = ensure_party_system(player_state)
    active_list = []
    for c_name, c_data in comps.items():
        if c_data.get("recruited", False) and c_data.get("active", False):
            active_list.append(c_data)
    return active_list


def recruit_companion(player_state, companion_name, check_requirements=False):
    """
    Recruits a companion from the living world into Banki's roster.
    If check_requirements=True, verifies min_level and deducts col_cost if applicable.
    If the active party has fewer than 3 companions, automatically slots them into active duty.
    """
    comps = ensure_party_system(player_state)
    target = None
    for k in comps:
        if k.lower() == companion_name.lower():
            target = k
            break

    if not target:
        return {"success": False, "message": f"Companion '{companion_name}' not found."}

    comp = comps[target]
    if comp.get("recruited", False):
        return {"success": False, "message": f"{comp['name']} is already recruited into your vanguard."}

    if check_requirements:
        req = comp.get("recruitment_requirements", {})
        min_lvl = req.get("min_level", 1)
        player_lvl = player_state.get("level", 1)
        if player_lvl < min_lvl:
            return {
                "success": False,
                "message": f"Requirement not met: Player level {player_lvl} is below required level {min_lvl} to recruit {comp['name']}."
            }
        col_cost = req.get("col_cost", 0)
        player_col = player_state.get("col", 0)
        if col_cost > 0:
            if player_col < col_cost:
                return {
                    "success": False,
                    "message": f"Requirement not met: Insufficient Col. Requires {col_cost} Col (you have {player_col} Col)."
                }
            player_state["col"] = player_col - col_cost

    comp["recruited"] = True

    # Count active companions
    active_count = len(get_active_party(player_state))
    if active_count < 3:
        comp["active"] = True
        status_str = "added to Active Raiding Party"
    else:
        comp["active"] = False
        status_str = "added to Reserve Benched Roster"

    log = f"[PARTY RECRUIT: {comp['name']} ({comp['class']}) has joined the expedition! ({status_str})]"
    return {
        "success": True,
        "companion": comp["name"],
        "class": comp["class"],
        "active": comp["active"],
        "log": log,
        "message": f"Recruited {comp['name']} ({comp['class']})!"
    }


def set_active_party_roster(player_state, active_companion_names):
    """
    Sets the active companion roster (maximum 3 companions alongside Banki).
    Any unlisted companions are moved to Reserve / Benched.
    """
    comps = ensure_party_system(player_state)
    clean_names = [n.strip().title() for n in active_companion_names]

    if len(clean_names) > 3:
        return {"success": False, "message": "Active party cannot exceed 3 companions (4 total with Banki)."}

    # Verify all chosen companions are recruited
    for name in clean_names:
        if name in comps and not comps[name].get("recruited", False):
            return {"success": False, "message": f"Cannot activate {name}; they have not been recruited yet."}

    for c_name, c_data in comps.items():
        if c_name in clean_names and c_data.get("recruited", False):
            c_data["active"] = True
        else:
            c_data["active"] = False

    active_now = [c["name"] for c in get_active_party(player_state)]
    log = f"[PARTY ROSTER UPDATED: Active Vanguard: Banki (Leader) + {', '.join(active_now)}]"
    return {
        "success": True,
        "active_party": active_now,
        "log": log,
        "message": f"Active party configured: Banki + {', '.join(active_now)}"
    }


def set_party_member_stance(player_state, companion_name, stance_key):
    """
    Switches any companion's active tactical stance.
    """
    comps = ensure_party_system(player_state)
    target = None
    for k in comps:
        if k.lower() == companion_name.lower():
            target = k
            break

    if not target:
        return {"success": False, "message": f"Companion '{companion_name}' not found."}

    comp = comps[target]
    stances = comp.get("stances", {})
    if stance_key not in stances:
        # Check normalized / alias
        for sk in stances:
            if stance_key.lower().replace(" ", "_") in sk:
                stance_key = sk
                break
        else:
            return {"success": False, "message": f"Invalid stance '{stance_key}' for {comp['name']}."}

    comp["stance"] = stance_key
    st_info = stances[stance_key]
    log = f"[TACTICAL STANCE: {comp['name']} shifted to {st_info.get('label', stance_key)} ({st_info.get('tactical_effect', '')})]"
    return {
        "success": True,
        "companion": comp["name"],
        "stance": stance_key,
        "stance_info": st_info,
        "log": log,
        "message": f"Set {comp['name']}'s stance to {st_info.get('label', stance_key)}."
    }


def resolve_party_combat_actions(player_state):
    """
    Evaluates combat contributions from ALL active companions in a single cohesive turn.
    Returns list of action objects and concatenated combat logs.
    """
    active_comps = get_active_party(player_state)
    actions = []
    logs = []

    for comp in active_comps:
        c_name = comp["name"]
        stance_key = comp.get("stance", "default")
        stances = comp.get("stances", {})
        st_info = stances.get(stance_key, {})

        tag = st_info.get("tag", f"[{c_name.upper()}]")
        tactical_desc = st_info.get("tactical_effect", "Provides combat support.")

        log_entry = f"{tag} {tactical_desc}"
        logs.append(log_entry)

        actions.append({
            "companion": c_name,
            "stance": stance_key,
            "tag": tag,
            "log": log_entry,
            "effect": st_info
        })

    return {
        "actions": actions,
        "logs": logs,
        "combined_log": " | ".join(logs)
    }


def increase_companion_affinity(player_state, companion_name, amount, reason=""):
    """
    Increases companion affinity meter (0–100) through shared taphouse meals, dialogue, or quests.
    Updates affinity tier:
    - 0-24: Acquaintance
    - 25-49: Ally
    - 50-74: Trusted Battle-Brother / Sister
    - 75-100: Soul-Bonded Raiding Partner
    Crossing 50 unlocks the companion's signature Dual-Tech combo!
    """
    comps = ensure_party_system(player_state)
    target = None
    for k in comps:
        if k.lower() == companion_name.lower():
            target = k
            break

    if not target:
        return {"success": False, "message": f"Companion '{companion_name}' not found."}

    comp = comps[target]
    old_aff = comp.get("affinity", 0)
    new_aff = max(0, min(100, old_aff + int(amount)))
    comp["affinity"] = new_aff

    # Determine tier
    if new_aff >= 75:
        tier = "Soul-Bonded Partner"
    elif new_aff >= 50:
        tier = "Trusted Battle-Brother/Sister"
    elif new_aff >= 25:
        tier = "Ally"
    else:
        tier = "Acquaintance"

    old_tier = comp.get("affinity_tier", "Acquaintance")
    comp["affinity_tier"] = tier

    unlocked_combo = None
    if old_aff < 50 and new_aff >= 50:
        # Combo unlock!
        combo_id = comp.get("dual_tech_id")
        if combo_id and combo_id in DUAL_TECH_COMBOS:
            unlocked_combo = DUAL_TECH_COMBOS[combo_id]
            feats = player_state.setdefault("feats", [])
            f_entry = f"Dual-Tech Combo: {unlocked_combo['name']} (Banki + {comp['name']})"
            if f_entry not in feats:
                feats.append(f_entry)

    log_reason = f" ({reason})" if reason else ""
    log = f"[COMPANION AFFINITY: {comp['name']} affinity +{amount} -> {new_aff}/100 [{tier}]{log_reason}]"
    if unlocked_combo:
        log += f"\n✨ [DUAL-TECH UNLOCKED: Reached Affinity 50! Unlocked signature combo: '{unlocked_combo['name']}']"

    return {
        "success": True,
        "companion": comp["name"],
        "old_affinity": old_aff,
        "new_affinity": new_aff,
        "tier": tier,
        "unlocked_combo": unlocked_combo,
        "log": log,
        "message": f"{comp['name']}'s affinity increased to {new_aff}/100 [{tier}]!"
    }


def execute_dual_tech(player_state, combo_id_or_partner):
    """
    Executes an unlocked Dual-Tech combo attack with an active party member.
    Requires affinity >= 50 and partner in active party.
    """
    comps = ensure_party_system(player_state)
    active_names = [c["name"] for c in get_active_party(player_state)]

    combo = None
    for c_id, c_data in DUAL_TECH_COMBOS.items():
        if c_id == combo_id_or_partner or any(combo_id_or_partner.lower() in p.lower() for p in c_data["partners"]):
            combo = c_data
            break

    if not combo:
        return {"success": False, "message": f"Dual-Tech combo '{combo_id_or_partner}' not found."}

    # Find companion partner
    partner_name = [p for p in combo["partners"] if p != "Banki"][0]
    partner_comp = comps.get(partner_name)

    if not partner_comp:
        return {"success": False, "message": f"Partner '{partner_name}' is not in party."}

    if not partner_comp.get("active", False):
        return {"success": False, "message": f"{partner_comp.get('name', partner_name)} must be in your active raiding party to execute this combo."}

    if partner_comp.get("affinity", 0) < combo["req_affinity"]:
        return {"success": False, "message": f"Requires Affinity {combo['req_affinity']} with {partner_name} (Current: {partner_comp.get('affinity', 0)}/100)."}

    log = f"{combo['log_tag']} {combo['desc']} -> Dealt {combo['damage']}! {combo['effect']}"
    return {
        "success": True,
        "combo": combo["name"],
        "damage": combo["damage"],
        "effect": combo["effect"],
        "log": log,
        "message": f"Executed Dual-Tech: {combo['name']} with {partner_name}!"
    }


# =====================================================================
# THE SAO CURSOR CRIMINALITY SYSTEM (GREEN / ORANGE / RED)
# =====================================================================

CURSOR_TIERS = {
    "green": {
        "status": "green",
        "label": "🟢 Lawful (Green Cursor)",
        "badge": "🟢 Green",
        "description": "Innocent citizen and lawful adventurer. Full protection under Safe-Zone barrier matrices. Respected by merchants and regional guards.",
        "infamy_range": (0, 0),
        "merchant_surcharge": 0.0,
        "safe_zone_clearance": True
    },
    "orange": {
        "status": "orange",
        "label": "🟠 Criminal (Orange Cursor)",
        "badge": "🟠 Orange",
        "description": "Flagged for unprovoked assault, theft, or trap tampering. Safe-zone merchants impose a +25% Col surcharge. Townsfolk are guarded.",
        "infamy_range": (1, 9),
        "merchant_surcharge": 0.25,
        "safe_zone_clearance": True
    },
    "red": {
        "status": "red",
        "label": "🔴 Outlaw PK (Red Cursor)",
        "badge": "🔴 Red",
        "description": "Murderer and outlaw player-killer! Safe-Zone barrier matrices will incinerate Red players on sight. High-tier NPC Wardens actively hunt them.",
        "infamy_range": (10, 999),
        "merchant_surcharge": 1.00,
        "safe_zone_clearance": False
    }
}


def get_cursor_status(player_state):
    """
    Returns the player's active cursor criminality object (Green / Orange / Red).
    """
    infamy = max(0, int(player_state.get("infamy", 0)))
    if infamy >= 10:
        tier_data = CURSOR_TIERS["red"]
    elif infamy >= 1:
        tier_data = CURSOR_TIERS["orange"]
    else:
        tier_data = CURSOR_TIERS["green"]

    return {
        **tier_data,
        "current_infamy": infamy
    }


def adjust_infamy(player_state, delta, reason=""):
    """
    Modifies the player's infamy score and triggers cursor status transitions.
    """
    old_status = get_cursor_status(player_state)
    current_infamy = max(0, int(player_state.get("infamy", 0)))
    new_infamy = max(0, current_infamy + int(delta))
    player_state["infamy"] = new_infamy

    new_status = get_cursor_status(player_state)
    transition = old_status["status"] != new_status["status"]

    log_reason = f" ({reason})" if reason else ""
    log = f"[CURSOR INFAMY: Infamy delta {delta:+d} -> Now {new_infamy} [{new_status['badge']}]{log_reason}]"
    if transition:
        log += f"\n🚨 [CURSOR STATE TRANSITION: Player has become {new_status['label']}! {new_status['description']}]"

    return {
        "success": True,
        "old_infamy": current_infamy,
        "new_infamy": new_infamy,
        "old_cursor": old_status["status"],
        "new_cursor": new_status["status"],
        "transition": transition,
        "status_info": new_status,
        "log": log,
        "message": f"Cursor updated: {new_status['label']}"
    }


def pay_criminal_atonement(player_state):
    """
    Allows an Orange cursor player to atone for criminal acts at the Washington Council.
    Cost: 500 Col per point of Infamy.
    Resets Infamy to 0, returning cursor to Green.
    Red players cannot simply buy atonement; they must face justice or regional directives.
    """
    status = get_cursor_status(player_state)
    if status["status"] == "green":
        return {"success": False, "message": "Your cursor is already Green. You have no criminal infamy to atone for."}

    if status["status"] == "red":
        return {"success": False, "message": "Murderer (Red Cursor) status cannot be paid off with mere Col! The Safe-Zone wards reject you."}

    infamy = status["current_infamy"]
    cost = infamy * 500
    current_col = player_state.get("col", 0)

    if current_col < cost:
        return {"success": False, "message": f"Insufficient Col for criminal atonement. Required: {cost:,} Col (Have: {current_col:,} Col)."}

    player_state["col"] -= cost
    player_state["infamy"] = 0
    new_status = get_cursor_status(player_state)

    log = f"[ATONEMENT PAID: Paid {cost:,} Col in municipal reparations! Infamy reset to 0 -> Cursor restored to {new_status['label']}!]"
    return {
        "success": True,
        "cost_paid": cost,
        "remaining_col": player_state["col"],
        "new_cursor": new_status["status"],
        "log": log,
        "message": f"Atonement accepted. Your cursor is now Green."
    }


def check_safe_zone_ward_clearance(player_state):
    """
    Checks if player is allowed past Safe-Zone barrier matrices.
    Red cursor players are denied and blasted by anti-PK barrier fire.
    """
    status = get_cursor_status(player_state)
    if not status["safe_zone_clearance"]:
        log = "🚨 [BARRIER WARD DETONATION: Safe-Zone defense matrix detects RED CURSOR! Lethal anti-PK beam incinerates boundary breach!]"
        return {
            "allowed": False,
            "status": "red",
            "log": log,
            "damage": 100,
            "message": "Access Denied: Red players cannot enter safe zones!"
        }
    return {
        "allowed": True,
        "status": status["status"],
        "surcharge": status["merchant_surcharge"],
        "message": "Safe-zone clearance granted."
    }


# =====================================================================
# FACTION POLITICS & GUILD ALIGNMENT ENGINE
# =====================================================================

REGIONAL_FACTIONS = {
    "vanguard_coalition": {
        "id": "vanguard_coalition",
        "name": "The Vanguard Coalition",
        "leader": "Commander Kaelen Vance",
        "headquarters": "Washington Fortress Bastion",
        "icon": "⚔️",
        "description": "Dedicated frontline raid coalition committed to breaking the regional labyrinth bosses and ascending the regional spires.",
        "perks": {
            25: "+10% bonus damage against Dungeon and Sector Bosses; Coalition Quartermaster access.",
            50: "+15% Maximum HP and military requisition grade armor."
        }
    },
    "iron_syndicate": {
        "id": "iron_syndicate",
        "name": "The Iron Syndicate",
        "leader": "Guildmaster Silas Bron",
        "headquarters": "Oxford Forge & Smelting Vaults",
        "icon": "⚒️",
        "description": "Mercantile crafting cartel that monopolizes regional raw materials, forge leylines, and trade routes across Warren County.",
        "perks": {
            25: "15% wholesale discount on all store purchases and repair services.",
            50: "Masterwork forging blueprints and priority auction trade access."
        }
    },
    "blood_shroud": {
        "id": "blood_shroud",
        "name": "The Blood Shroud",
        "leader": "The Pale Whisper",
        "headquarters": "Scotts Mountain Glitch-Vaults",
        "icon": "🩸",
        "description": "Secretive outlaw guild operating in dark sectors (Laughing Coffin analog); orchestrates ambushes and black market trade.",
        "perks": {
            25: "Immunity to wilderness outlaw ambushes; access to illicit poison blueprints.",
            50: "Black-market teleporters and outlaw contract bounties."
        }
    }
}


def ensure_faction_system(player_state):
    """
    Initializes faction reputation standings in player_state if not present.
    """
    reps = player_state.setdefault("faction_reputation", {})
    if not isinstance(reps, dict):
        reps = {}
        player_state["faction_reputation"] = reps

    for f_id in REGIONAL_FACTIONS:
        if f_id not in reps:
            reps[f_id] = 0

    return reps


def get_faction_standing(player_state, faction_id):
    """
    Returns faction reputation score and standing label:
    - Hostile: < 0
    - Neutral: 0 - 24
    - Friendly: 25 - 49
    - Honored / Revered: 50+
    """
    reps = ensure_faction_system(player_state)
    score = reps.get(faction_id, 0)

    if score >= 50:
        label = "Honored / Revered"
        badge = "👑 Honored"
    elif score >= 25:
        label = "Friendly"
        badge = "🤝 Friendly"
    elif score >= 0:
        label = "Neutral"
        badge = "⚖️ Neutral"
    else:
        label = "Hostile"
        badge = "⚔️ Hostile"

    fac_def = REGIONAL_FACTIONS.get(faction_id, {})
    return {
        "faction_id": faction_id,
        "name": fac_def.get("name", faction_id),
        "score": score,
        "label": label,
        "badge": badge,
        "perks_active": [desc for thresh, desc in fac_def.get("perks", {}).items() if score >= thresh]
    }


def modify_faction_rep(player_state, faction_id, amount, reason=""):
    """
    Modifies reputation standing with a specific guild faction.
    """
    reps = ensure_faction_system(player_state)
    if faction_id not in REGIONAL_FACTIONS:
        # Check normalized
        for k in REGIONAL_FACTIONS:
            if faction_id.lower().replace(" ", "_") in k:
                faction_id = k
                break
        else:
            return {"success": False, "message": f"Faction '{faction_id}' not found."}

    old_score = reps.get(faction_id, 0)
    new_score = max(-100, min(100, old_score + int(amount)))
    reps[faction_id] = new_score

    fac_standing = get_faction_standing(player_state, faction_id)
    log_reason = f" ({reason})" if reason else ""
    log = f"[FACTION REP: {fac_standing['name']} reputation {amount:+d} -> Now {new_score} [{fac_standing['badge']}]{log_reason}]"

    return {
        "success": True,
        "faction": fac_standing["name"],
        "old_score": old_score,
        "new_score": new_score,
        "standing": fac_standing["label"],
        "log": log,
        "message": f"Reputation with {fac_standing['name']} is now {new_score} [{fac_standing['label']}]."
    }


def get_all_faction_standings(player_state):
    """
    Returns summary list of all faction standings for the HUD.
    """
    ensure_faction_system(player_state)
    return [get_faction_standing(player_state, f_id) for f_id in REGIONAL_FACTIONS]


# =====================================================================
# PHASE 8: CHRONO-ATMOSPHERIC ENGINE & WILDERNESS SURVIVAL ECOLOGY
# =====================================================================

CHRONO_PERIODS = {
    "dawn": {
        "key": "dawn",
        "label": "🌅 Dawn",
        "hours": (6, 8),
        "desc": "Morning light pierces the fractured data-haze. Visibility normal; creatures stirring.",
        "perception_mod": 0,
        "stealth_mod": 0
    },
    "day": {
        "key": "day",
        "label": "☀️ Midday",
        "hours": (8, 18),
        "desc": "Bright aetheric sun overhead. Optimal visibility; active regional trade routes.",
        "perception_mod": 0,
        "stealth_mod": 0
    },
    "dusk": {
        "key": "dusk",
        "label": "🌆 Dusk",
        "hours": (18, 21),
        "desc": "Sun sinks beneath Pohatcong Mountain. Lengthening shadows impose -2 to Perception checks.",
        "perception_mod": -2,
        "stealth_mod": 1
    },
    "night": {
        "key": "night",
        "label": "🌙 Midnight",
        "hours": (21, 4),
        "desc": "Pitch black wilderness. Torches or aether-lanterns required. Apex stalkers gain +2 Stealth.",
        "perception_mod": -4,
        "stealth_mod": 2
    },
    "witching_hour": {
        "key": "witching_hour",
        "label": "🌌 Witching Hour",
        "hours": (4, 6),
        "desc": "The thin hour before sunrise. Dimensional seam friction; anomalous glitched entities stir.",
        "perception_mod": -2,
        "stealth_mod": 1
    }
}

AETHER_WEATHER = {
    "clear_skies": {
        "id": "clear_skies",
        "name": "Clear Aether-Skies",
        "label": "☀️ Clear Aether-Skies",
        "icon": "☀️",
        "desc": "Temperate atmospheric conditions across Warren County. Normal movement and combat parameters.",
        "effect": "Standard baseline. Fast-travel and exploration operate at normal speed.",
        "ranged_atk_mod": 0,
        "stealth_mod": 0,
        "spell_dmg_pct": 0,
        "travel_allowed": True
    },
    "runic_mist": {
        "id": "runic_mist",
        "name": "Runic Mist",
        "label": "🌫️ Runic Mist",
        "icon": "🌫️",
        "desc": "Dense, glowing mana-vapor blankets the valley floor, distorting distances and acoustic telemetry.",
        "effect": "-4 to Ranged Attack rolls, +3 to Stealth checks. Fast travel disabled through thick fog.",
        "ranged_atk_mod": -4,
        "stealth_mod": 3,
        "spell_dmg_pct": 0,
        "travel_allowed": False
    },
    "leyline_storm": {
        "id": "leyline_storm",
        "name": "Leyline Overload Storm",
        "label": "⚡ Leyline Overload Storm",
        "icon": "⚡",
        "desc": "Violent arcane discharge cascades between mountain ridge towers. Atmospheric static crackles.",
        "effect": "+25% Spell and Arcane damage. Cyber-constructs and golems are enraged (+2 ATK).",
        "ranged_atk_mod": -2,
        "stealth_mod": -2,
        "spell_dmg_pct": 25,
        "travel_allowed": True
    },
    "crimson_ash": {
        "id": "crimson_ash",
        "name": "Crimson Ash Fall",
        "label": "🌋 Crimson Ash Fall",
        "icon": "🌋",
        "desc": "Blood-red fallout drifts from high-altitude rift fissures, signaling a roaming Apex World-Boss.",
        "effect": "Healing efficiency halved (-50% HP recovery). Wandering boss aggression quadrupled.",
        "ranged_atk_mod": -1,
        "stealth_mod": 1,
        "healing_mult": 0.5,
        "travel_allowed": True
    },
    "glitch_freeze": {
        "id": "glitch_freeze",
        "name": "Glitch-Freeze Blizzard",
        "label": "❄️ Glitch-Freeze Blizzard",
        "icon": "❄️",
        "desc": "Crystalline polygon snow and sub-zero aetheric cold. Movement halved; cold exposure hazard.",
        "effect": "Movement halved. Extreme cold damage unless insulated (Banki's Dire-Wolf Mantle protects him!).",
        "ranged_atk_mod": -2,
        "stealth_mod": -1,
        "speed_mult": 0.5,
        "cold_exposure": True,
        "travel_allowed": False
    }
}

CAMPFIRE_RECIPES = {
    "wolf_heart_stew": {
        "id": "wolf_heart_stew",
        "name": "Wolf-Heart Marrow Stew",
        "desc": "Thick, steaming marrow broth infused with wild roots that supercharges physical vigor.",
        "ingredients": {"Wolf Marrow": 1, "Wild Roots": 1},
        "buff": {
            "name": "[Wolf-Heart Vigor]",
            "desc": "+15 Maximum HP and +2 STR for 5 turns.",
            "hp_bonus": 15,
            "str_bonus": 2,
            "duration": 5
        }
    },
    "roasted_boar_ribs": {
        "id": "roasted_boar_ribs",
        "name": "Roasted Boar Ribs",
        "desc": "Crispy charred ribs seasoned with salted rock-moss, packing dense caloric fortification.",
        "ingredients": {"Raw Boar Flank": 1, "Salted Moss": 1},
        "buff": {
            "name": "[Boar's Resilience]",
            "desc": "+20 Temporary HP and +2 Physical Damage for 5 turns.",
            "temp_hp": 20,
            "phys_dmg_bonus": 2,
            "duration": 5
        }
    },
    "spiced_herb_broth": {
        "id": "spiced_herb_broth",
        "name": "Spiced Aether-Herb Broth",
        "desc": "Fragrant herbal infusion that clears mental strain and accelerates combat momentum.",
        "ingredients": {"Aether-Herb": 1, "Bottled Water": 1},
        "buff": {
            "name": "[Aetheric Focus]",
            "desc": "+20% Resource generation and cleanses fatigue.",
            "resource_regen_pct": 20,
            "cleanses_fatigue": True,
            "duration": 5
        }
    },
    "dire_scavenger_skewer": {
        "id": "dire_scavenger_skewer",
        "name": "Dire Scavenger Skewer",
        "desc": "Quick field skewer seasoned with runic lichen, heightening predatory reflex.",
        "ingredients": {"Scrap Meat": 1, "Runic Lichen": 1},
        "buff": {
            "name": "[Scavenger's Grit]",
            "desc": "+10 HP recovery and +10% Critical strike chance for 5 turns.",
            "hp_recovery": 10,
            "crit_chance_pct": 10,
            "duration": 5
        }
    }
}


def ensure_chrono_system(player_state):
    """
    Initializes chrono (day/night time of day), dynamic weather, and survival state in player_state.
    """
    chrono = player_state.setdefault("chrono", {})
    if not isinstance(chrono, dict):
        chrono = {}
        player_state["chrono"] = chrono

    chrono.setdefault("day", 1)
    chrono.setdefault("hour", 9)
    chrono.setdefault("minute", 30)
    chrono.setdefault("weather", "clear_skies")
    chrono.setdefault("active_buffs", [])

    # Keep top-level active_buffs synchronized as a separate list of buff names
    if "active_buffs" not in player_state or not isinstance(player_state["active_buffs"], list) or player_state["active_buffs"] is chrono["active_buffs"]:
        player_state["active_buffs"] = [b.get("name", str(b)) if isinstance(b, dict) else str(b) for b in chrono["active_buffs"]]

    return chrono


def get_time_period(hour):
    """
    Returns time period definition based on 24-hour integer (0-23).
    """
    h = int(hour) % 24
    if 6 <= h < 8:
        return CHRONO_PERIODS["dawn"]
    elif 8 <= h < 18:
        return CHRONO_PERIODS["day"]
    elif 18 <= h < 21:
        return CHRONO_PERIODS["dusk"]
    elif 4 <= h < 6:
        return CHRONO_PERIODS["witching_hour"]
    else:
        return CHRONO_PERIODS["night"]


def get_game_time(player_state):
    """
    Returns structured chrono object with current time, period info, and formatted string.
    """
    chrono = ensure_chrono_system(player_state)
    h = chrono.get("hour", 9)
    m = chrono.get("minute", 30)
    d = chrono.get("day", 1)
    period = get_time_period(h)

    return {
        "day": d,
        "hour": h,
        "minute": m,
        "time_str": f"Day {d}, {h:02d}:{m:02d}",
        "period": period["key"],
        "period_info": period,
        "weather": chrono.get("weather", "clear_skies"),
        "weather_info": AETHER_WEATHER.get(chrono.get("weather", "clear_skies"), AETHER_WEATHER["clear_skies"])
    }


def advance_game_time(player_state, minutes=15):
    """
    Advances game time by minutes.
    Handles rolling hour (0-23) and day increment upon crossing midnight.
    Ticks down active culinary and survival buff durations.
    """
    chrono = ensure_chrono_system(player_state)
    mins = max(1, int(minutes))

    cur_m = chrono.get("minute", 0) + mins
    add_hours = cur_m // 60
    new_m = cur_m % 60

    cur_h = chrono.get("hour", 9) + add_hours
    add_days = cur_h // 24
    new_h = cur_h % 24

    new_d = chrono.get("day", 1) + add_days

    chrono["minute"] = new_m
    chrono["hour"] = new_h
    chrono["day"] = new_d

    old_period = get_time_period((cur_h - add_hours) % 24)["key"]
    new_period_info = get_time_period(new_h)
    new_period = new_period_info["key"]

    period_transition = old_period != new_period
    day_rollover = add_days > 0

    # Tick active buffs
    buffs = chrono.get("active_buffs", [])
    remaining_buffs = []
    expired_buffs = []
    for b in buffs:
        if isinstance(b, dict):
            b["duration"] = b.get("duration", 1) - 1
            if b["duration"] > 0:
                remaining_buffs.append(b)
            else:
                expired_buffs.append(b.get("name", "Buff"))
        else:
            remaining_buffs.append(b)

    chrono["active_buffs"] = remaining_buffs
    player_state["active_buffs"] = [b.get("name", str(b)) if isinstance(b, dict) else str(b) for b in remaining_buffs]

    log = f"[CHRONO ADVANCE: +{mins} mins -> Day {new_d}, {new_h:02d}:{new_m:02d} [{new_period_info['label']}]]"
    if period_transition:
        log += f"\n🌅 [ATMOSPHERIC SHIFT: The ambient sky transitions into {new_period_info['label']}. {new_period_info['desc']}]"
    if day_rollover:
        log += f"\n📅 [NEW DAY: Dawn breaks on Day {new_d}! Safe-zone facilities restocked.]"
    for exp in expired_buffs:
        log += f"\n⌛ [BUFF EXPIRED: {exp} effect has worn off.]"

    return {
        "success": True,
        "minutes_advanced": mins,
        "day": new_d,
        "hour": new_h,
        "minute": new_m,
        "time_str": f"Day {new_d}, {new_h:02d}:{new_m:02d}",
        "period": new_period,
        "period_info": new_period_info,
        "period_transition": period_transition,
        "day_rollover": day_rollover,
        "expired_buffs": expired_buffs,
        "log": log
    }


def get_current_weather(player_state):
    """
    Returns active weather definition dictionary.
    """
    chrono = ensure_chrono_system(player_state)
    w_key = chrono.get("weather", "clear_skies")
    return AETHER_WEATHER.get(w_key, AETHER_WEATHER["clear_skies"])


def set_weather(player_state, weather_key):
    """
    Switches weather condition to target weather_key.
    """
    chrono = ensure_chrono_system(player_state)
    norm = weather_key.lower().replace(" ", "_")
    target_key = None
    for k in AETHER_WEATHER:
        if k == norm or norm in k or k in norm:
            target_key = k
            break

    if not target_key:
        return {"success": False, "message": f"Weather phenomenon '{weather_key}' not recognized."}

    chrono["weather"] = target_key
    w_def = AETHER_WEATHER[target_key]
    log = f"[AETHER WEATHER: Atmosphere shifted to {w_def['label']} — {w_def['desc']} ({w_def['effect']})]"

    return {
        "success": True,
        "weather_key": target_key,
        "weather_info": w_def,
        "log": log,
        "message": f"Weather changed to {w_def['label']}."
    }


def roll_random_weather(player_state):
    """
    Randomly selects weather condition weighted towards common conditions.
    """
    import random
    choices = [
        ("clear_skies", 45),
        ("runic_mist", 25),
        ("leyline_storm", 15),
        ("crimson_ash", 10),
        ("glitch_freeze", 5)
    ]
    total = sum(w for _, w in choices)
    r = random.randint(1, total)
    upto = 0
    selected = "clear_skies"
    for key, weight in choices:
        if upto + weight >= r:
            selected = key
            break
        upto += weight

    return set_weather(player_state, selected)


def check_frostbite_protection(player_state):
    """
    Evaluates whether Banki is insulated against extreme cold / glitch-freeze blizzards.
    Banki's Dire-Wolf Fur Mantle, heavy pelt armors, or warm garments grant insulation.
    """
    equipped = player_state.get("equipped", {})
    inventory = player_state.get("inventory", [])

    # Check equipped slots
    for slot, item in equipped.items():
        s_low = str(item).lower()
        if any(w in s_low for w in ["mantle", "fur", "pelt", "dire-wolf", "direwolf", "insulated", "thermal", "winter"]):
            return {
                "protected": True,
                "source": item,
                "message": f"Insulated against sub-zero temperatures by {item}."
            }

    # Banki's canonical dire-wolf mantle baseline
    feats = player_state.get("feats", [])
    if any("mantle" in str(f).lower() or "dire-wolf" in str(f).lower() or "berserk" in str(f).lower() for f in feats):
        return {
            "protected": True,
            "source": "Dire-Wolf Fur Mantle (Racial/Class Heritage)",
            "message": "Protected by heavy dire-wolf fur mantle."
        }

    return {
        "protected": False,
        "source": None,
        "message": "Unprotected from sub-zero glitch freeze! Suffering cold exposure."
    }


def cook_campfire_meal(player_state, recipe_id):
    """
    Prepares a culinary recipe at the wilderness campfire.
    Checks ingredient availability, deducts them from inventory,
    applies the culinary buff, and restores HP.
    """
    chrono = ensure_chrono_system(player_state)
    norm = recipe_id.lower().replace(" ", "_")
    recipe = None
    for r_k, r_data in CAMPFIRE_RECIPES.items():
        if r_k == norm or norm in r_k or norm in r_data["name"].lower():
            recipe = r_data
            break

    if not recipe:
        return {"success": False, "message": f"Campfire recipe '{recipe_id}' not found."}

    inv = player_state.setdefault("inventory", [])
    
    # Check if ingredients exist in inventory
    # For streamlined play, if ingredients are missing, can optionally buy them or verify qty
    missing = []
    inv_map = {}
    for item in inv:
        if isinstance(item, dict):
            iname = item.get("name", "").strip().lower()
            inv_map[iname] = inv_map.get(iname, 0) + item.get("qty", 1)
        elif isinstance(item, str):
            iname = item.strip().lower()
            inv_map[iname] = inv_map.get(iname, 0) + 1

    for ing_name, req_qty in recipe["ingredients"].items():
        ing_lower = ing_name.lower()
        # Look for partial match
        available_qty = sum(qty for k, qty in inv_map.items() if ing_lower in k or k in ing_lower)
        if available_qty < req_qty:
            missing.append(f"{ing_name} (Need {req_qty})")

    if missing:
        return {
            "success": False,
            "message": f"Missing required ingredients for {recipe['name']}: {', '.join(missing)}."
        }

    # Deduct ingredients
    for ing_name, req_qty in recipe["ingredients"].items():
        ing_lower = ing_name.lower()
        remaining_to_deduct = req_qty
        for item in inv[:]:
            if remaining_to_deduct <= 0:
                break
            if isinstance(item, dict):
                if ing_lower in item.get("name", "").lower() or item.get("name", "").lower() in ing_lower:
                    cur_q = item.get("qty", 1)
                    if cur_q <= remaining_to_deduct:
                        remaining_to_deduct -= cur_q
                        inv.remove(item)
                    else:
                        item["qty"] = cur_q - remaining_to_deduct
                        remaining_to_deduct = 0
            elif isinstance(item, str):
                if ing_lower in item.lower() or item.lower() in ing_lower:
                    inv.remove(item)
                    remaining_to_deduct -= 1

    # Apply culinary buff
    buff_data = dict(recipe["buff"])
    chrono.setdefault("active_buffs", []).append(buff_data)
    player_state["active_buffs"] = [b.get("name", str(b)) if isinstance(b, dict) else str(b) for b in chrono["active_buffs"]]

    # Health recovery
    hp_recovery = buff_data.get("hp_bonus", 15)
    old_hp = player_state.get("hp", 100)
    max_hp = player_state.get("max_hp", 100)
    new_hp = min(max_hp, old_hp + hp_recovery)
    player_state["hp"] = new_hp

    log = (
        f"[CAMPFIRE CULINARY: Cooked '{recipe['name']}'! "
        f"Gained {buff_data['name']} ({buff_data['desc']}) | Restored +{new_hp - old_hp} HP (Now {new_hp}/{max_hp})]"
    )

    return {
        "success": True,
        "recipe": recipe["name"],
        "buff": buff_data,
        "hp_restored": new_hp - old_hp,
        "log": log,
        "message": f"Successfully cooked {recipe['name']}! Gained {buff_data['name']}."
    }

ensure_factions_system = ensure_faction_system
check_frost_hazard = check_frostbite_protection
cook_campfire_recipe = cook_campfire_meal

def pitch_wilderness_camp(player_state, watch_companion="Ren"):
    """
    Pitches camp in the wilderness or a safe haven for an 8-hour rest.
    - Advances game time by 480 minutes (8 hours).
    - Restores 50 HP (or full HP if in safe zone).
    - Resolves watch assignment based on companion.
    """
    chrono = ensure_chrono_system(player_state)
    ensure_party_system(player_state)

    # Advance time 8 hours (480 minutes)
    time_res = advance_game_time(player_state, minutes=480)

    # Healing
    raw_loc = str(player_state.get("location", ""))
    loc_str = raw_loc.lower()
    in_safe_zone = is_location_safe_zone(raw_loc) or any(w in loc_str for w in ["borough", "safe", "haven", "taphouse", "outpost", "camp", "sanctuary"])
    old_hp = player_state.get("hp", 100)
    max_hp = player_state.get("max_hp", 100)

    if in_safe_zone:
        player_state["hp"] = max_hp
        heal_amt = max_hp - old_hp
    else:
        heal_amt = min(max_hp - old_hp, 50)
        player_state["hp"] = old_hp + heal_amt

    # Watch resolution
    watch_key = watch_companion.strip().title() if watch_companion else "None"
    comps = player_state.get("companions", {})
    comp_obj = comps.get(watch_key)
    if not comp_obj:
        for k, v in comps.items():
            if watch_key.lower() in k.lower() or watch_key.lower() in v.get("name", "").lower():
                comp_obj = v
                watch_key = k
                break

    ambush_prevented = False
    watch_log = ""
    watch_perk = ""

    if watch_key == "Ren":
        ambush_prevented = True
        watch_perk = "[Vigilant Leyline Telemetry: Party gains +2 Initiative in next encounter]"
        watch_log = "Ren monitored spatial rifts on his runic scribe slate throughout the night, spotting a pack of glitch-stalkers 200 meters out and steering them clear."
    elif watch_key == "Torvald":
        ambush_prevented = True
        watch_perk = "[Bulwark Barricade: Foes start next combat Staggered]"
        watch_log = "Torvald reinforced the camp perimeter with heavy logs and his tower shield, deflecting an early nocturnal charge without waking the camp."
    elif watch_key == "Kibs":
        ambush_prevented = True
        watch_perk = "[Perimeter Snare Web: Ambushers take 2d8 damage on contact]"
        watch_log = "Kibs strung barbed tripwires and noise-canisters through the underbrush, catching a wandering razor-hound in a snare."
    elif watch_key == "Elora":
        ambush_prevented = True
        p_name_label = player_state.get("name", "Player")
        watch_perk = f"[Warded Perimeter: {p_name_label} gains +2 AC for next combat]"
        watch_log = "Elora etched shimmering starlight wards in a ring around the campfire, alarming the party of approaching mana-beasts."
    else:
        # Solo or no companion watch
        if in_safe_zone:
            watch_log = "Safe-zone barrier matrices provided uninterrupted peaceful slumber."
        else:
            watch_log = "Unprotected rest in the wilderness. You sleep with one eye open, waking frequently to distant construct howls."

    camp_log = (
        f"[WILDERNESS CAMP: Rested for 8 Hours -> {time_res['time_str']} [{time_res['period_info']['label']}] | "
        f"Restored +{heal_amt} HP (Now {player_state['hp']}/{max_hp})]\n"
        f"🛡️ [WATCH REPORT ({watch_key}): {watch_log} {watch_perk}]"
    )

    return {
        "success": True,
        "healed_hp": heal_amt,
        "new_hp": player_state["hp"],
        "max_hp": max_hp,
        "watch_companion": watch_key,
        "watch_log": watch_log,
        "watch_perk": watch_perk,
        "time_info": time_res,
        "log": camp_log,
        "message": f"Rested for 8 hours. Time is now {time_res['time_str']}."
    }


# ==============================================================================
# 🏰 PHASE 9: SOVEREIGN HOMESTEAD, PLAYER ECONOMY & MYTHIC CRAFTING ENGINE
# ==============================================================================

HOMESTEAD_ESTATES = {
    "washington_manor": {
        "id": "washington_manor",
        "name": "The Iron-Spoke Sovereign Estate",
        "location": "Washington Borough Safe Zone (Sector 1 Ridge)",
        "purchase_cost_col": 3500,
        "description": "An expansive pre-Integration stone manor on the southern ridge of Washington Borough, fortified with ancient dwarven ward-stones, deep cellars, and an aether-well."
    },
    "oxford_foundry_estate": {
        "id": "oxford_foundry_estate",
        "name": "The Oxford Hot-Blast Foundry Estate",
        "location": "Oxford Furnace Ridge (3.5 mi NW of Washington)",
        "purchase_cost_col": 4500,
        "description": "A fortified 18th-century ironmaster's limestone manor overlooking the Oxford Furnace slag-pits, equipped with a private geothermal crucible and deep magnetite shaft access."
    },
    "pocono_wilderness_lodge": {
        "id": "pocono_wilderness_lodge",
        "name": "The Delaware Gap & Pocono Timber Lodge",
        "location": "Kittatinny Ridge / Delaware Water Gap Overlook (18 mi NW)",
        "purchase_cost_col": 5000,
        "description": "A heavy hemlock-and-bluestone cliffside bastion perched above the Delaware Water Gap wind-current, featuring a beast-kin falconry roost and alpine herb terrace."
    }
}

HOMESTEAD_TROPHIES = {
    "gilded_overlord_core": {
        "id": "gilded_overlord_core",
        "name": "Overlord's Gilded Core",
        "buff_name": "[Aegis of the Spire]",
        "desc": "+2 Armor Class and +5% Col drop rate across all encounters.",
        "ac_bonus": 2,
        "col_drop_pct": 5
    },
    "alpha_razorhound_skull": {
        "id": "alpha_razorhound_skull",
        "name": "Alpha Razor-Hound Plated Skull",
        "buff_name": "[Apex Pack-Instinct]",
        "desc": "+2 Initiative and +10% Movement speed.",
        "initiative_bonus": 2,
        "speed_pct": 10
    },
    "clockwork_golem_heart": {
        "id": "clockwork_golem_heart",
        "name": "Clockwork Golem Geared Heart",
        "buff_name": "[Clockwork Fortitude]",
        "desc": "+15 Maximum HP and +1 Damage Resistance.",
        "hp_bonus": 15,
        "dr_bonus": 1
    },
    "direwolf_alpha_pelt": {
        "id": "direwolf_alpha_pelt",
        "name": "Roaring Rock Dire-Wolf Alpha Pelt",
        "buff_name": "[Primal Ferocity]",
        "desc": "+10% Critical Strike Chance on Melee Attacks.",
        "crit_pct": 10
    }
}

GREENHOUSE_TIERS = {
    1: {"yield": {"Wild Roots": 2, "Aether-Herb": 1}, "upgrade_cost": 1000},
    2: {"yield": {"Wild Roots": 3, "Aether-Herb": 2, "Salted Moss": 2}, "upgrade_cost": 2500},
    3: {"yield": {"Wild Roots": 4, "Aether-Herb": 3, "Salted Moss": 3, "Runic Lichen": 2}, "upgrade_cost": 5000}
}

VAULT_TIERS = {
    1: {"capacity_lbs": 1000, "slots": 50, "upgrade_cost": 0},
    2: {"capacity_lbs": 2500, "slots": 100, "upgrade_cost": 2000},
    3: {"capacity_lbs": 10000, "slots": 250, "upgrade_cost": 5000}
}

COMMODITY_MARKET = {
    "refined_aether_alloy": {"name": "Refined Aether-Alloy", "base_price": 250, "category": "Ore & Ingot"},
    "scrap_metal": {"name": "Scrap Metal & Wiring", "base_price": 50, "category": "Scrap & Salvage"},
    "aether_herb": {"name": "Wild Aether-Herbs", "base_price": 75, "category": "Botanical"},
    "wolf_marrow": {"name": "Wolf Marrow", "base_price": 100, "category": "Monster Part"},
    "repair_flux": {"name": "Aetheric Repair Flux", "base_price": 120, "category": "Alchemy"}
}

MYTHIC_RECIPES = {
    "fenrirs_howl": {
        "id": "fenrirs_howl",
        "name": "Fenrir's Howl (Grade 6 Mythic Great-Axe)",
        "grade": 6,
        "slot": "main_hand",
        "durability": 350,
        "atk_bonus": 6,
        "damage_dice": "2d12",
        "active_technique": {
            "name": "Crystalline Frost Wave",
            "type": "Active Sword Skill",
            "desc": "Unleashes a 20ft cone of sub-zero frost dealing 3d8 cold damage and freezing targets for 1 turn (0 movement, -2 AC)."
        },
        "base_item_query": "Fenrir's Tusk",
        "boss_core_query": "Overlord's Gilded Core",
        "materials": {"Refined Aether-Alloy": 2, "Carbon Line Spools": 1},
        "fee_col": 2000,
        "description": "A legendary black-iron bearded greataxe infused with frozen aetheric frost and the resonance of the Gilded Overlord."
    },
    "mjolnir_prime": {
        "id": "mjolnir_prime",
        "name": "Mjölnir-Prime (Grade 6 Mythic Titan-Hammer)",
        "grade": 6,
        "slot": "off_hand",
        "durability": 350,
        "atk_bonus": 5,
        "damage_dice": "3d8",
        "active_technique": {
            "name": "Kinetic Armor Shatter",
            "type": "Active Sword Skill",
            "desc": "Shatters target defenses: -4 AC debuff and disables construct Damage Resistance for 2 turns."
        },
        "base_item_query": "Mjöllnir-Null",
        "boss_core_query": "Overlord's Gilded Core",
        "materials": {"Corroded Micro-Capacitor": 2, "Refined Aether-Alloy": 1},
        "fee_col": 2000,
        "description": "An earth-shattering trench hammer surging with overcharged magnetic kinetic conduits."
    },
    "einherjar_sovereign_aegis": {
        "id": "einherjar_sovereign_aegis",
        "name": "Einherjar Sovereign Aegis (Grade 6 Mythic Power-Rig)",
        "grade": 6,
        "slot": "chest",
        "durability": 400,
        "ac_bonus": 10,
        "dr": 3,
        "active_technique": {
            "name": "Aetheric Citadel Fortress",
            "type": "Active Stance",
            "desc": "Stance: Gain +4 AC, Advantage on CON saves, and reflect 1d10 force damage to melee attackers for 3 turns."
        },
        "base_item_query": "Einherjar Rig",
        "boss_core_query": "Overlord's Gilded Core",
        "materials": {"Refined Aether-Alloy": 3},
        "fee_col": 2500,
        "description": "Impenetrable masterwork runic plate engineered with living aether-conduits and sovereign ward lattices."
    }
}


def ensure_homestead_system(player_state):
    """
    Initializes or returns homestead container in player_state.
    """
    if not isinstance(player_state, dict):
        return {}

    homestead = player_state.setdefault("homestead", {})
    if not isinstance(homestead, dict):
        homestead = {}
        player_state["homestead"] = homestead

    homestead.setdefault("owned", False)
    homestead.setdefault("estate_id", "washington_manor")
    homestead.setdefault("vault_tier", 1)
    homestead.setdefault("greenhouse_tier", 1)
    homestead.setdefault("has_master_anvil", False)
    homestead.setdefault("mounted_trophies", [])
    homestead.setdefault("vault_items", [])
    homestead.setdefault("vault_col", 0)
    homestead.setdefault("last_harvest_day", 0)

    return homestead


def purchase_homestead(player_state, estate_id="washington_manor"):
    """
    Purchases the Washington Manor estate for player_state using Col.
    """
    homestead = ensure_homestead_system(player_state)
    if homestead.get("owned"):
        return {"success": False, "message": "You already own the Sovereign Estate in Washington Borough."}

    estate_def = HOMESTEAD_ESTATES.get(estate_id, HOMESTEAD_ESTATES["washington_manor"])
    cost = estate_def["purchase_cost_col"]
    cur_col = player_state.get("col", 0)

    if cur_col < cost:
        return {"success": False, "message": f"Insufficient Col to purchase estate (Cost: {cost:,} Col, Current: {cur_col:,} Col)."}

    player_state["col"] = cur_col - cost
    homestead["owned"] = True
    homestead["estate_id"] = estate_id
    homestead["name"] = estate_def["name"]

    log = f"[HOMESTEAD ACQUIRED: Purchased {estate_def['name']} for {cost:,} Col! Base of operations established in Washington Borough.]"
    return {
        "success": True,
        "estate": estate_def["name"],
        "cost": cost,
        "remaining_col": player_state["col"],
        "log": log,
        "message": f"Successfully purchased {estate_def['name']}!"
    }


def upgrade_homestead_facility(player_state, facility_key):
    """
    Upgrades vault, greenhouse, or master anvil in the homestead.
    """
    homestead = ensure_homestead_system(player_state)
    if not homestead.get("owned"):
        return {"success": False, "message": "You must purchase the Sovereign Estate before upgrading facilities."}

    cur_col = player_state.get("col", 0)

    if facility_key == "vault":
        cur_tier = homestead.get("vault_tier", 1)
        if cur_tier >= 3:
            return {"success": False, "message": "Subsurface Vault is already at maximum Tier 3 capacity."}
        next_tier = cur_tier + 1
        cost = VAULT_TIERS[next_tier]["upgrade_cost"]
        if cur_col < cost:
            return {"success": False, "message": f"Insufficient Col for Vault Tier {next_tier} (Requires {cost:,} Col)."}
        player_state["col"] = cur_col - cost
        homestead["vault_tier"] = next_tier
        log = f"[HOMESTEAD UPGRADE: Subsurface Vault upgraded to Tier {next_tier} ({VAULT_TIERS[next_tier]['capacity_lbs']:,} lbs capacity, {VAULT_TIERS[next_tier]['slots']} slots)!]"
        return {"success": True, "facility": "vault", "new_tier": next_tier, "cost": cost, "log": log, "message": f"Vault upgraded to Tier {next_tier}."}

    elif facility_key == "greenhouse":
        cur_tier = homestead.get("greenhouse_tier", 1)
        if cur_tier >= 3:
            return {"success": False, "message": "Alchemical Greenhouse is already at maximum Tier 3 yield."}
        next_tier = cur_tier + 1
        cost = GREENHOUSE_TIERS[next_tier]["upgrade_cost"]
        if cur_col < cost:
            return {"success": False, "message": f"Insufficient Col for Greenhouse Tier {next_tier} (Requires {cost:,} Col)."}
        player_state["col"] = cur_col - cost
        homestead["greenhouse_tier"] = next_tier
        log = f"[HOMESTEAD UPGRADE: Alchemical Greenhouse upgraded to Tier {next_tier} (Yield expanded)!]"
        return {"success": True, "facility": "greenhouse", "new_tier": next_tier, "cost": cost, "log": log, "message": f"Greenhouse upgraded to Tier {next_tier}."}

    elif facility_key == "master_anvil":
        if homestead.get("has_master_anvil"):
            return {"success": False, "message": "Deepforged Master-Anvil is already constructed."}
        cost = 3000
        if cur_col < cost:
            return {"success": False, "message": f"Insufficient Col for Deepforged Master-Anvil (Requires {cost:,} Col)."}
        player_state["col"] = cur_col - cost
        homestead["has_master_anvil"] = True
        log = "[HOMESTEAD UPGRADE: Deepforged Master-Anvil installed! Grade 6 and 7 Mythic Weapon Forging is now UNLOCKED!]"
        return {"success": True, "facility": "master_anvil", "cost": cost, "log": log, "message": "Deepforged Master-Anvil constructed!"}

    return {"success": False, "message": f"Unknown facility '{facility_key}'."}


def get_vault_capacity(player_state):
    """
    Returns max lbs and slots for the homestead vault.
    """
    homestead = ensure_homestead_system(player_state)
    tier = homestead.get("vault_tier", 1)
    tier_info = VAULT_TIERS.get(tier, VAULT_TIERS[1])
    return {
        "tier": tier,
        "max_lbs": tier_info["capacity_lbs"],
        "max_slots": tier_info["slots"]
    }


def deposit_to_vault(player_state, item_query, qty=1, col_amount=0):
    """
    Deposits item or Col from player's inventory/pouch into the homestead vault.
    """
    homestead = ensure_homestead_system(player_state)
    if not homestead.get("owned"):
        return {"success": False, "message": "You must own the Sovereign Estate to access the vault."}

    v_items = homestead.setdefault("vault_items", [])
    cap = get_vault_capacity(player_state)

    # 1. Col Deposit
    if col_amount > 0:
        cur_p_col = player_state.get("col", 0)
        if cur_p_col < col_amount:
            return {"success": False, "message": f"Insufficient Col (Have: {cur_p_col:,}, Tried: {col_amount:,})."}
        player_state["col"] = cur_p_col - col_amount
        homestead["vault_col"] = homestead.get("vault_col", 0) + col_amount
        log = f"[VAULT DEPOSIT: Stored {col_amount:,} Col in Vault (Vault Col: {homestead['vault_col']:,} | Pouch: {player_state['col']:,})]"
        return {
            "success": True,
            "deposited_col": col_amount,
            "vault_col": homestead["vault_col"],
            "player_col": player_state["col"],
            "log": log,
            "message": f"Deposited {col_amount:,} Col."
        }

    # 2. Item Deposit
    if not item_query:
        return {"success": False, "message": "No item specified for deposit."}

    inv = player_state.setdefault("inventory", [])
    found_item = None
    target_idx = -1

    for idx, it in enumerate(inv):
        iname = it.get("name", "") if isinstance(it, dict) else str(it)
        if item_query.lower() in iname.lower():
            found_item = it
            target_idx = idx
            break

    if not found_item:
        return {"success": False, "message": f"Item '{item_query}' not found in inventory."}

    # Capacity check
    if len(v_items) >= cap["max_slots"]:
        return {"success": False, "message": f"Vault is at slot capacity ({len(v_items)}/{cap['max_slots']} slots)."}

    # Handle deduction
    dep_item = None
    if isinstance(found_item, dict):
        cur_q = found_item.get("qty", 1)
        transfer_q = min(cur_q, qty)
        if cur_q <= transfer_q:
            inv.pop(target_idx)
            dep_item = copy.deepcopy(found_item)
            dep_item["qty"] = transfer_q
        else:
            found_item["qty"] = cur_q - transfer_q
            dep_item = copy.deepcopy(found_item)
            dep_item["qty"] = transfer_q
    elif isinstance(found_item, str):
        inv.pop(target_idx)
        dep_item = {"name": found_item, "qty": 1, "rarity": "Common", "desc": "Stored relic item."}

    # Add to vault (stack if exists)
    stacked = False
    for vit in v_items:
        if isinstance(vit, dict) and vit.get("name", "").lower() == dep_item.get("name", "").lower():
            vit["qty"] = vit.get("qty", 1) + dep_item.get("qty", 1)
            stacked = True
            break
    if not stacked:
        v_items.append(dep_item)

    item_disp = dep_item.get("name", item_query)
    log = f"[VAULT DEPOSIT: Stored {dep_item.get('qty', 1)}x '{item_disp}' in Secure Vault (Vault Slots: {len(v_items)}/{cap['max_slots']})]"
    return {
        "success": True,
        "item": item_disp,
        "qty": dep_item.get("qty", 1),
        "vault_slots_used": len(v_items),
        "log": log,
        "message": f"Deposited {item_disp} to vault."
    }


def withdraw_from_vault(player_state, item_query, qty=1, col_amount=0):
    """
    Withdraws item or Col from the homestead vault to player's inventory/pouch.
    """
    homestead = ensure_homestead_system(player_state)
    if not homestead.get("owned"):
        return {"success": False, "message": "You must own the Sovereign Estate to access the vault."}

    # 1. Col Withdrawal
    if col_amount > 0:
        cur_v_col = homestead.get("vault_col", 0)
        if cur_v_col < col_amount:
            return {"success": False, "message": f"Insufficient Vault Col (Have: {cur_v_col:,}, Tried: {col_amount:,})."}
        homestead["vault_col"] = cur_v_col - col_amount
        player_state["col"] = player_state.get("col", 0) + col_amount
        log = f"[VAULT WITHDRAW: Withdrew {col_amount:,} Col from Vault (Vault Col: {homestead['vault_col']:,} | Pouch: {player_state['col']:,})]"
        return {
            "success": True,
            "withdrawn_col": col_amount,
            "vault_col": homestead["vault_col"],
            "player_col": player_state["col"],
            "log": log,
            "message": f"Withdrew {col_amount:,} Col."
        }

    # 2. Item Withdrawal
    if not item_query:
        return {"success": False, "message": "No item specified for withdrawal."}

    v_items = homestead.setdefault("vault_items", [])
    found_item = None
    target_idx = -1

    for idx, it in enumerate(v_items):
        iname = it.get("name", "") if isinstance(it, dict) else str(it)
        if item_query.lower() in iname.lower():
            found_item = it
            target_idx = idx
            break

    if not found_item:
        return {"success": False, "message": f"Item '{item_query}' not found in vault."}

    inv = player_state.setdefault("inventory", [])
    with_item = None
    if isinstance(found_item, dict):
        cur_q = found_item.get("qty", 1)
        transfer_q = min(cur_q, qty)
        if cur_q <= transfer_q:
            v_items.pop(target_idx)
            with_item = copy.deepcopy(found_item)
            with_item["qty"] = transfer_q
        else:
            found_item["qty"] = cur_q - transfer_q
            with_item = copy.deepcopy(found_item)
            with_item["qty"] = transfer_q
    else:
        v_items.pop(target_idx)
        with_item = {"name": str(found_item), "qty": 1, "rarity": "Common"}

    # Add to player inventory (stack if exists)
    stacked = False
    for pit in inv:
        if isinstance(pit, dict) and pit.get("name", "").lower() == with_item.get("name", "").lower():
            pit["qty"] = pit.get("qty", 1) + with_item.get("qty", 1)
            stacked = True
            break
    if not stacked:
        inv.append(with_item)

    item_disp = with_item.get("name", item_query)
    log = f"[VAULT WITHDRAW: Withdrew {with_item.get('qty', 1)}x '{item_disp}' from Vault to personal inventory.]"
    return {
        "success": True,
        "item": item_disp,
        "qty": with_item.get("qty", 1),
        "log": log,
        "message": f"Withdrew {item_disp}."
    }


def mount_boss_trophy(player_state, trophy_query):
    """
    Mounts a boss core/trophy from player inventory to the Trophy Hall pedestal.
    Grants persistent party-wide passive perks.
    """
    homestead = ensure_homestead_system(player_state)
    if not homestead.get("owned"):
        return {"success": False, "message": "You must own the Sovereign Estate to mount trophies."}

    mounted = homestead.setdefault("mounted_trophies", [])
    if len(mounted) >= 5:
        return {"success": False, "message": "All 5 Trophy Hall pedestals are occupied."}

    # Find matching trophy definition
    norm_q = trophy_query.lower()
    t_def = None
    t_key = None
    for k, v in HOMESTEAD_TROPHIES.items():
        if k in norm_q or norm_q in k or v["name"].lower() in norm_q or norm_q in v["name"].lower():
            t_def = v
            t_key = k
            break

    if not t_def:
        return {"success": False, "message": f"Trophy '{trophy_query}' is not recognized as a mountable boss relic."}

    if t_key in [m.get("key") for m in mounted if isinstance(m, dict)]:
        return {"success": False, "message": f"{t_def['name']} is already mounted in the Trophy Hall."}

    # Check player inventory for the trophy item
    inv = player_state.setdefault("inventory", [])
    found_idx = -1
    for idx, item in enumerate(inv):
        iname = item.get("name", "") if isinstance(item, dict) else str(item)
        if t_def["name"].lower() in iname.lower() or t_key in iname.lower() or "overlord" in iname.lower() and "overlord" in t_key:
            found_idx = idx
            break

    if found_idx == -1:
        return {"success": False, "message": f"You do not possess the trophy item '{t_def['name']}' in your inventory."}

    # Consume 1 from inventory
    target_item = inv[found_idx]
    if isinstance(target_item, dict):
        if target_item.get("qty", 1) > 1:
            target_item["qty"] -= 1
        else:
            inv.pop(found_idx)
    else:
        inv.pop(found_idx)

    # Mount trophy
    trophy_record = {
        "key": t_key,
        "name": t_def["name"],
        "buff_name": t_def["buff_name"],
        "desc": t_def["desc"],
        "ac_bonus": t_def.get("ac_bonus", 0),
        "col_drop_pct": t_def.get("col_drop_pct", 0),
        "initiative_bonus": t_def.get("initiative_bonus", 0),
        "hp_bonus": t_def.get("hp_bonus", 0),
        "dr_bonus": t_def.get("dr_bonus", 0),
        "crit_pct": t_def.get("crit_pct", 0)
    }
    mounted.append(trophy_record)

    # Award feat entry
    feats = player_state.setdefault("feats", [])
    f_entry = f"{t_def['buff_name']}: {t_def['desc']}"
    if not any(t_def["buff_name"] in str(f) for f in feats):
        feats.append(f_entry)

    log = f"[TROPHY MOUNTED: {t_def['name']} mounted on Pedestal {len(mounted)}/5! Party gains {t_def['buff_name']} ({t_def['desc']})]"
    return {
        "success": True,
        "trophy": t_def["name"],
        "buff": t_def["buff_name"],
        "log": log,
        "message": f"Mounted {t_def['name']} in the Trophy Hall."
    }


def unmount_boss_trophy(player_state, trophy_key):
    """
    Removes a mounted trophy and returns it to inventory.
    """
    homestead = ensure_homestead_system(player_state)
    mounted = homestead.setdefault("mounted_trophies", [])

    match_idx = -1
    matched_trophy = None
    for idx, t in enumerate(mounted):
        if t.get("key") == trophy_key or trophy_key.lower() in t.get("name", "").lower():
            match_idx = idx
            matched_trophy = t
            break

    if match_idx == -1:
        return {"success": False, "message": f"Trophy '{trophy_key}' is not mounted."}

    mounted.pop(match_idx)
    inv = player_state.setdefault("inventory", [])
    inv.append({
        "name": matched_trophy["name"],
        "rarity": "Legendary",
        "qty": 1,
        "desc": "Unmounted boss relic."
    })

    # Remove feat
    feats = player_state.get("feats", [])
    b_name = matched_trophy.get("buff_name", "")
    player_state["feats"] = [f for f in feats if b_name not in str(f)]

    log = f"[TROPHY UNMOUNTED: Removed {matched_trophy['name']} from pedestal and returned it to inventory.]"
    return {"success": True, "trophy": matched_trophy["name"], "log": log, "message": f"Unmounted {matched_trophy['name']}."}


def get_active_trophy_buffs(player_state):
    """
    Returns list of active party-wide buffs from mounted trophies.
    """
    homestead = ensure_homestead_system(player_state)
    mounted = homestead.get("mounted_trophies", [])
    return [dict(t) for t in mounted if isinstance(t, dict)]


def harvest_alchemical_garden(player_state):
    """
    Harvests grown herbs and roots from the greenhouse once per game day.
    """
    homestead = ensure_homestead_system(player_state)
    if not homestead.get("owned"):
        return {"success": False, "message": "You must own the Sovereign Estate to harvest the greenhouse."}

    chrono = ensure_chrono_system(player_state)
    cur_day = chrono.get("day", 1)
    last_day = homestead.get("last_harvest_day", 0)

    if cur_day <= last_day:
        return {"success": False, "message": f"The greenhouse was already harvested today (Day {cur_day}). Plants require one full sunrise to bloom."}

    tier = homestead.get("greenhouse_tier", 1)
    yield_def = GREENHOUSE_TIERS.get(tier, GREENHOUSE_TIERS[1])["yield"]

    inv = player_state.setdefault("inventory", [])
    harvested_items = []

    for herb_name, herb_qty in yield_def.items():
        # Stack or append
        found = False
        for it in inv:
            if isinstance(it, dict) and it.get("name", "").lower() == herb_name.lower():
                it["qty"] = it.get("qty", 1) + herb_qty
                found = True
                break
        if not found:
            inv.append({
                "name": herb_name,
                "rarity": "Common",
                "qty": herb_qty,
                "desc": "Freshly cultivated botanical specimen harvested from the estate greenhouse."
            })
        harvested_items.append(f"{herb_qty}x {herb_name}")

    homestead["last_harvest_day"] = cur_day

    log = f"[GREENHOUSE HARVEST: Gathered {', '.join(harvested_items)} from the Tier {tier} Greenhouse on Day {cur_day}!]"
    return {
        "success": True,
        "yield": yield_def,
        "harvested": harvested_items,
        "day": cur_day,
        "log": log,
        "message": f"Harvested: {', '.join(harvested_items)}."
    }


def get_commodity_prices(player_state):
    """
    Returns current market prices for commodities based on player reputation,
    cleared trade routes, and regional market indices.
    """
    reps = player_state.get("faction_reputation", player_state.get("faction_system", {}).get("reputations", player_state.get("factions", {})))
    iron_rep = reps.get("iron_syndicate", 0) if isinstance(reps, dict) else 0

    # Iron Syndicate discount: up to 15% discount at 50+ rep
    discount_mult = 1.0
    if iron_rep >= 50:
        discount_mult = 0.85
    elif iron_rep >= 25:
        discount_mult = 0.90

    prices = {}
    for c_key, c_info in COMMODITY_MARKET.items():
        buy_p = int(c_info["base_price"] * discount_mult)
        sell_p = int(c_info["base_price"] * 0.60)
        prices[c_key] = {
            "name": c_info["name"],
            "category": c_info["category"],
            "buy_price": buy_p,
            "sell_price": sell_p
        }
    return prices


def trade_commodity(player_state, commodity_id, action="buy", qty=1):
    """
    Buys or sells commodities through the regional mercantile exchange.
    """
    prices = get_commodity_prices(player_state)
    target_c = None
    c_key = None

    for k, info in prices.items():
        if k == commodity_id or info["name"].lower() in commodity_id.lower() or commodity_id.lower() in k:
            target_c = info
            c_key = k
            break

    if not target_c:
        return {"success": False, "message": f"Commodity '{commodity_id}' not recognized."}

    inv = player_state.setdefault("inventory", [])
    cur_col = player_state.get("col", 0)

    if action == "buy":
        total_cost = target_c["buy_price"] * qty
        if cur_col < total_cost:
            return {"success": False, "message": f"Insufficient Col to purchase {qty}x {target_c['name']} (Cost: {total_cost:,} Col, Have: {cur_col:,} Col)."}

        player_state["col"] = cur_col - total_cost

        # Add to inventory
        stacked = False
        for it in inv:
            if isinstance(it, dict) and it.get("name", "").lower() == target_c["name"].lower():
                it["qty"] = it.get("qty", 1) + qty
                stacked = True
                break
        if not stacked:
            inv.append({
                "name": target_c["name"],
                "rarity": "Common",
                "qty": qty,
                "desc": f"Trade commodity: {target_c['name']}."
            })

        log = f"[COMMODITY EXCHANGE: Purchased {qty}x {target_c['name']} for {total_cost:,} Col (Balance: {player_state['col']:,} Col)]"
        return {"success": True, "action": "buy", "commodity": target_c["name"], "qty": qty, "total_col": total_cost, "log": log, "message": f"Purchased {qty}x {target_c['name']}."}

    elif action == "sell":
        # Check inventory
        found_item = None
        target_idx = -1
        for idx, it in enumerate(inv):
            iname = it.get("name", "") if isinstance(it, dict) else str(it)
            if target_c["name"].lower() in iname.lower() or c_key in iname.lower():
                found_item = it
                target_idx = idx
                break

        if not found_item:
            return {"success": False, "message": f"You do not possess '{target_c['name']}' to sell."}

        avail_q = found_item.get("qty", 1) if isinstance(found_item, dict) else 1
        if avail_q < qty:
            return {"success": False, "message": f"Insufficient quantity to sell (Have: {avail_q}, Tried: {qty})."}

        total_gain = target_c["sell_price"] * qty
        player_state["col"] = cur_col + total_gain

        # Deduct
        if isinstance(found_item, dict):
            if avail_q <= qty:
                inv.pop(target_idx)
            else:
                found_item["qty"] = avail_q - qty
        else:
            inv.pop(target_idx)

        log = f"[COMMODITY EXCHANGE: Sold {qty}x {target_c['name']} for +{total_gain:,} Col (Balance: {player_state['col']:,} Col)]"
        return {"success": True, "action": "sell", "commodity": target_c["name"], "qty": qty, "total_col": total_gain, "log": log, "message": f"Sold {qty}x {target_c['name']}."}

    return {"success": False, "message": f"Invalid trade action '{action}'."}


def forge_mythic_equipment(player_state, recipe_key):
    """
    Fuses a Grade 5 base weapon with a Sector Boss Core and rare catalysts
    at the Deepforged Master-Anvil to create a Grade 6 Mythic armament.
    Auto-slots/learns the weapon's unique Sword Skill.
    """
    homestead = ensure_homestead_system(player_state)
    if not homestead.get("owned") or not homestead.get("has_master_anvil"):
        return {"success": False, "message": "Mythic forging requires an owned Sovereign Estate with a Deepforged Master-Anvil installed."}

    norm = recipe_key.lower().replace(" ", "_")
    recipe = None
    for r_k, r_v in MYTHIC_RECIPES.items():
        if r_k == norm or norm in r_k or norm in r_v["name"].lower():
            recipe = r_v
            break

    if not recipe:
        return {"success": False, "message": f"Mythic recipe '{recipe_key}' not found."}

    cur_col = player_state.get("col", 0)
    fee = recipe.get("fee_col", 2000)
    if cur_col < fee:
        return {"success": False, "message": f"Insufficient Col for master-forge ignition (Requires {fee:,} Col, Have {cur_col:,} Col)."}

    inv = player_state.setdefault("inventory", [])
    equipped = player_state.setdefault("equipped", {})

    # 1. Check Base Item (in equipped or inventory)
    base_q = recipe["base_item_query"].lower()
    base_location = None
    base_slot = None
    base_inv_idx = -1

    for slot, item in equipped.items():
        if base_q in str(item).lower():
            base_location = "equipped"
            base_slot = slot
            break

    if not base_location:
        for idx, item in enumerate(inv):
            iname = item.get("name", "") if isinstance(item, dict) else str(item)
            if base_q in iname.lower():
                base_location = "inventory"
                base_inv_idx = idx
                break

    if not base_location:
        return {"success": False, "message": f"Missing required base item matching '{recipe['base_item_query']}'."}

    # 2. Check Boss Core (in inventory or vault)
    core_q = recipe["boss_core_query"].lower()
    core_idx = -1
    for idx, item in enumerate(inv):
        iname = item.get("name", "") if isinstance(item, dict) else str(item)
        if core_q in iname.lower() or "overlord" in iname.lower() and "core" in iname.lower():
            core_idx = idx
            break

    if core_idx == -1:
        return {"success": False, "message": f"Missing required Boss Core '{recipe['boss_core_query']}' in inventory."}

    # 3. Check Materials
    inv_map = {}
    for item in inv:
        if isinstance(item, dict):
            iname = item.get("name", "").strip().lower()
            inv_map[iname] = inv_map.get(iname, 0) + item.get("qty", 1)
        elif isinstance(item, str):
            iname = item.strip().lower()
            inv_map[iname] = inv_map.get(iname, 0) + 1

    missing = []
    for mat_name, req_q in recipe["materials"].items():
        m_low = mat_name.lower()
        have_q = sum(qty for k, qty in inv_map.items() if m_low in k or k in m_low)
        if have_q < req_q:
            missing.append(f"{mat_name} (Need {req_q})")

    if missing:
        return {"success": False, "message": f"Missing required forging materials: {', '.join(missing)}."}

    # 4. Deduct Fee
    player_state["col"] = cur_col - fee

    # 5. Consume Boss Core
    core_item = inv[core_idx]
    if isinstance(core_item, dict) and core_item.get("qty", 1) > 1:
        core_item["qty"] -= 1
    else:
        inv.pop(core_idx)

    # 6. Consume Materials
    for mat_name, req_q in recipe["materials"].items():
        m_low = mat_name.lower()
        remaining_to_deduct = req_q
        for item in inv[:]:
            if remaining_to_deduct <= 0:
                break
            if isinstance(item, dict):
                iname = item.get("name", "").lower()
                if m_low in iname or iname in m_low:
                    cur_q = item.get("qty", 1)
                    if cur_q <= remaining_to_deduct:
                        remaining_to_deduct -= cur_q
                        inv.remove(item)
                    else:
                        item["qty"] = cur_q - remaining_to_deduct
                        remaining_to_deduct = 0
            elif isinstance(item, str):
                if m_low in item.lower() or item.lower() in m_low:
                    inv.remove(item)
                    remaining_to_deduct -= 1

    # 7. Consume / Upgrade Base Item
    target_slot = recipe["slot"]
    new_gear_name = recipe["name"]

    if base_location == "equipped":
        equipped[base_slot] = new_gear_name
    else:
        # Replace in inventory
        inv.pop(base_inv_idx)
        inv.append({
            "name": new_gear_name,
            "rarity": "Mythic",
            "durability": recipe["durability"],
            "max_durability": recipe["durability"],
            "qty": 1,
            "desc": recipe["description"]
        })

    # Update gear durability tracking
    gear_dur = player_state.setdefault("gear_durability", {})
    gear_dur[target_slot] = {
        "item": new_gear_name,
        "cur": recipe["durability"],
        "max": recipe["durability"],
        "grade": 6
    }

    # 8. Learn and Slot Active Technique
    tech = recipe["active_technique"]
    spells = player_state.setdefault("spells", [])
    tech_full_name = f"{tech['name']} ({tech['type']})"
    if not any(tech["name"].lower() in str(s).lower() for s in spells):
        spells.append(tech_full_name)

    slot_ability(player_state, tech["name"])

    log = (
        f"[DEEPFORGED MASTER-FORGE: Ignited runic anvil with {fee:,} Col! "
        f"Forged '{new_gear_name}'! Durability: {recipe['durability']}/{recipe['durability']} (Grade 6 Mythic) | "
        f"Mastered Unique Technique: '{tech['name']}' ({tech['desc']})]"
    )

    return {
        "success": True,
        "mythic_item": new_gear_name,
        "grade": 6,
        "slot": target_slot,
        "active_technique": tech,
        "durability": recipe["durability"],
        "fee": fee,
        "log": log,
        "message": f"Successfully forged {new_gear_name}!"
    }


# =====================================================================
# INTEGRATION CONVENIENCE ALIASES (FOR CROSS-PHASE & V2 COUPLING)
# =====================================================================

def get_game_time_info(player_state):
    """Convenience alias for time info with period details."""
    t_data = get_game_time(player_state)
    hour = t_data.get("hour", 6)
    period = get_time_period(hour)
    p_key = period.get("key", "day") if isinstance(period, dict) else str(period)
    p_info = CHRONO_PERIODS.get(p_key, {"label": p_key.capitalize(), "desc": "Standard light conditions."})
    t_data["period_info"] = p_info
    return t_data

def get_all_companions(player_state):
    """Returns dictionary of all known companions for Vanguard recruitment."""
    return RECRUITABLE_COMPANIONS

def get_dungeon_room(player_state, room_id=None):
    """Convenience alias to retrieve dungeon room data."""
    return get_current_dungeon_room(player_state)

def get_overlord_status(player_state):
    """Convenience alias for Sector Overlord status."""
    return player_state.get("boss_encounter", SECTOR_BOSSES.get("gilded_overlord", {}))

ensure_factions_system = ensure_faction_system

def extract_turn_components(msg: dict) -> tuple:
    """
    Returns (cleaned_narrative, mechanics_log, subagent_log) from a message dictionary.
    Supports structured messages, section headers (🎲 / 🧠), blockquotes, and inline rolls.
    """
    content = msg.get("content", "") or ""
    mechanics_log = msg.get("mechanics_log", "") or ""
    subagent_log = msg.get("subagent_log", "") or ""
    
    # 1. Extract SubAgent thoughts if not already isolated
    if not subagent_log and content:
        subagent_pattern = re.compile(
            r'(?:^|\r?\n)+(?:(?:🧠|\U0001f9e0)\s*)?(?:\*\*\[.*?SubAgent Mind\]\*\*|\*\*\[Ren\'s Tactical Logic\]\*\*|SubAgent Thoughts & Planned Actions:[\s\S]*)',
            re.IGNORECASE
        )
        m = subagent_pattern.search(content)
        if m:
            subagent_log = content[m.start():].strip()
            content = content[:m.start()].strip()

    # 2. Extract Dice Rolls / Mechanics if not already isolated
    if not mechanics_log and content:
        section_pattern = re.compile(
            r'(?:^|\r?\n)+(?:(?:🎲|\U0001f3b2)\s*)?Dice Rolls & Game Mechanics:[\s\S]*?(?=(?:^|\r?\n)+(?:🧠|\U0001f9e0|\*\*\[)|$)',
            re.IGNORECASE
        )
        m = section_pattern.search(content)
        if m:
            mechanics_log = m.group(0).strip()
            content = (content[:m.start()] + "\n" + content[m.end():]).strip()
        else:
            mechanics_items = []
            
            # Check for prepended blockquote rolls like: > 🎲 `...`
            clean_lines = []
            for line in content.split("\n"):
                line_str = line.strip()
                if line_str.startswith("> 🎲") or (line_str.startswith(">") and "🎲" in line_str):
                    cleaned = line_str.replace("> 🎲", "").replace(">", "").strip(" `*")
                    if cleaned:
                        mechanics_items.append(f"* 🎲 `{cleaned}`")
                elif line_str == ">":
                    continue
                else:
                    clean_lines.append(line)
            content = "\n".join(clean_lines).strip()
            
            # Check for bracketed rolls/checks: [Attack: 1d20+5 = 17 vs AC 14 | Hit!]
            bracket_pattern = re.compile(r'\s*\[([^\]]*(?:d20|d4|d6|d8|d10|d12|\bAC\b|\bDC\b|\bHit\b|\bFail\b|\bSave\b|\bRoll\b|\bdamage\b)[^\]]*)\]', re.IGNORECASE)
            found_brackets = bracket_pattern.findall(content)
            if found_brackets:
                content = bracket_pattern.sub('', content).strip()
                for b in found_brackets:
                    clean_b = b.strip()
                    if clean_b:
                        mechanics_items.append(f"* 🎲 `{clean_b}`")
                        
            if mechanics_items:
                mechanics_log = "\n".join(mechanics_items)
                
    return content, mechanics_log, subagent_log


# =====================================================================
# PHASE M10: MASTER ITEM VISUAL & LORE COMPENDIUM + DYNAMIC APPEARANCE ENGINE
# =====================================================================

BASE_CHARACTER_ANATOMY = {
    "banki": {
        "name": "Banki",
        "base_anatomy": "Burly, rugged Nordic warrior with a broad-shouldered muscular build, weathered skin, short dark full beard, piercing intense eyes, and dark undercut hair."
    },
    "companion_ren": {
        "name": "Ren",
        "base_anatomy": "Lean, athletic 17-year-old male high school senior and systems designer with messy dark hair and sharp, expressive eyes."
    },
    "companion_elora": {
        "name": "Elora Thorne",
        "base_anatomy": "Lithe, nimble high-elven woman with silver-braided hair, pointed ears, and luminousviolet-silver eyes."
    },
    "companion_torvald": {
        "name": "Torvald Iron-Vein",
        "base_anatomy": "Stocky, battle-hardened dwarven veteran with a thick braided iron-grey beard, scarred brow, and deep amber eyes."
    },
    "companion_kibs": {
        "name": "Kibs Nine-Fingers",
        "base_anatomy": "Wiry, agile street-scrapper rogue with sharp features, a missing left ring fingertip, and darting hazel eyes."
    },
    "companion_valeria": {
        "name": "Valeria Vane",
        "base_anatomy": "Tall, striking blonde valkyrie vanguard with braided golden hair, aristocratic features, and fierce sky-blue eyes."
    },
    "companion_morrigan": {
        "name": "Morrigan Black-Thorn",
        "base_anatomy": "Pale, gothic grave-binder woman with long flowing raven-black hair and haunting emerald-glowing eyes."
    },
    "companion_garrick": {
        "name": "Garrick Stone-Grip",
        "base_anatomy": "Heavily muscled, broad-chested martial artist monk with a scarred jaw, shaved head, and glowing tectonic ki-glyphs etched across his skin."
    },
    "companion_sariel": {
        "name": "Sariel Swift-Wind",
        "base_anatomy": "Graceful wood-elf ranger with windswept auburn hair, leaf-green eyes, and keen woodland markings."
    },
    "companion_kaelen": {
        "name": "Brother Kaelen",
        "base_anatomy": "Resolute, broad-shouldered Sol-Templar cleric with a cleanly shaved head, warm golden eyes, and radiant sun-sigil brands."
    },
    "companion_zedd": {
        "name": "Zeddicus Volt-Spark",
        "base_anatomy": "Wiry, eccentric plasma-mage with wild copper-streaked spiky hair, singed eyebrows, and electric-blue eyes."
    },
    "companion_daphne": {
        "name": "Daphne Leclair",
        "base_anatomy": "Charismatic, poised skaldic duelist with curled dark hair, expressive violet eyes, and a confident half-smile."
    },
    "companion_rok": {
        "name": "Ragnarok 'Rok'",
        "base_anatomy": "Towering, colossal battle-scarred barbarian juggernaut with fiery red war-braids and glowing crimson blood-rage tattoos."
    },
    "companion_lyra": {
        "name": "Lyra Stargaze",
        "base_anatomy": "Ethereal, slender chronomancer with cascading silver-white hair and starry indigo eyes."
    },
    "companion_titus": {
        "name": "Titus Sterling",
        "base_anatomy": "Imposing 7-foot-tall articulated bronze-and-steel clockwork automaton sentinel with a glowing amber ocular visor and chest furnace."
    },
    "companion_nyssa": {
        "name": "Nyssa Thorn-Weft",
        "base_anatomy": "Feral, athletic primal druid with tangled auburn hair woven with living bramble vines and glowing amber wolf-like eyes."
    },
    "companion_malakor": {
        "name": "Malakor",
        "base_anatomy": "Slender, fiend-touched hexblade warlock with ashen skin, swept-back obsidian horns, and glowing amethyst eyes."
    },
    "companion_thorne": {
        "name": "Dr. Alistair Thorne",
        "base_anatomy": "Gaunt, sharp-featured patrician alchemist with slick silver-streaked hair and cold steel-grey eyes."
    },
    "companion_teresa": {
        "name": "Sister Teresa",
        "base_anatomy": "Austere, stern-faced inquisitor with silver-blonde hair pulled into a tight bun and piercing pale-blue eyes."
    }
}

CANONICAL_ITEM_CATALOG = {
    # --- PLAYER WEAPONS & OFF-HANDS ---
    "enchanted bearded axe": {
        "name": "Enchanted Bearded Axe",
        "slot": "main_hand",
        "rarity": "Uncommon",
        "desc": "A finely forged Nordic bearded war-axe with an ash-wood haft wrapped in cured hide; its swept black-iron blade hums with residual cyan kinetic mana (+1d6 slashing/force, thrown return resonance).",
        "visual_appearance": "wielding a heavy black-iron Nordic bearded war-axe etched with glowing cyan Elder Futhark runes along the curved cutting edge and wrapped in dark leather around the ash haft"
    },
    "free (somatic futhark casting)": {
        "name": "Free (Somatic Futhark Casting)",
        "slot": "off_hand",
        "rarity": "Unique",
        "desc": "An intentionally unencumbered off-hand stance used by Wyrd-Weavers to trace Elder Futhark rune-sigils in mid-air, channeling raw kinetic and seismic spells without somatic penalty.",
        "visual_appearance": "left hand kept open and unencumbered, fingers crackling with glowing cyan Elder Futhark holographic rune-sigils traced in mid-air"
    },
    "rusted iron sword": {
        "name": "Rusted Iron Sword",
        "slot": "main_hand",
        "rarity": "Common",
        "desc": "A jagged, balance-heavy salvage broadsword ground down from pre-collapse highway guardrail steel, wrapped at the tang with electrical tape (1d8 slashing).",
        "visual_appearance": "wielding a jagged, pitted iron salvage broadsword with a cord-wrapped hilt"
    },
    "heavy scavenged mace": {
        "name": "Heavy Scavenged Mace",
        "slot": "main_hand",
        "rarity": "Common",
        "desc": "A brutal two-handed or heavy single-handed bludgeon forged from a steel drive-shaft welded to a heavy differential gear head (1d10 bludgeoning, +2 vs construct armor).",
        "visual_appearance": "wielding a brutal heavy steel flange-mace forged from a welded industrial gear-head"
    },
    "scrap-plate shield": {
        "name": "Scrap-Plate Shield",
        "slot": "off_hand",
        "rarity": "Common",
        "desc": "A riveted heater shield hammered from layered street-sign aluminum and boilerplate steel (+2 AC, absorbs glancing kinetic blows).",
        "visual_appearance": "carrying a battered, riveted scrap-iron heater shield reinforced with bolted steel crossbars on the off-arm"
    },
    "arcane stun-pistol": {
        "name": "Arcane Stun-Pistol",
        "slot": "main_hand",
        "rarity": "Uncommon",
        "desc": "A compact brass-and-steel MageTech sidearm powered by a miniature aether-cell that fires non-lethal or high-voltage arc-bolts (1d8 lightning, DC 12 CON stun).",
        "visual_appearance": "aiming a compact brass-and-iron MageTech arc-pistol with a glowing blue mana-capacitor barrel"
    },
    "tanto combat knife": {
        "name": "Tanto Combat Knife",
        "slot": "off_hand",
        "rarity": "Common",
        "desc": "A high-carbon steel reverse-edge tanto survival blade with a matte non-reflective finish and G10 composite grip (1d6 piercing/slashing, Finesse).",
        "visual_appearance": "holding a matte-black high-carbon tanto combat knife in a reverse grip"
    },
    "aetheric focusing wand": {
        "name": "Aetheric Focusing Wand",
        "slot": "main_hand",
        "rarity": "Uncommon",
        "desc": "A slender copper-bound quartz conductor rod that stabilizes raw leyline currents into focused arcane bolts (+1 spell attack rolls, 1d8 force).",
        "visual_appearance": "channeling mana through a copper-wrapped crystalline quartz focusing wand"
    },
    "recurve hunting bow": {
        "name": "Recurve Hunting Bow",
        "slot": "main_hand",
        "rarity": "Common",
        "desc": "A laminated fiberglass-and-ash takedown recurve bow strung with high-tensile spectra cord, paired with a hip quiver of broadhead arrows (1d8 piercing, range 120ft).",
        "visual_appearance": "holding a matte composite recurve hunting bow with a hip quiver of feathered broadhead arrows"
    },
    "chipped wood-axe": {
        "name": "Chipped Wood-Axe",
        "slot": "off_hand",
        "rarity": "Common",
        "desc": "A balanced camp hatchet with a hickory handle and a notched steel wedge head suited for close-quarters hacking and timber clearing (1d6 slashing).",
        "visual_appearance": "gripping a notched hickory-handled camp hatchet"
    },
    "sanctified flail": {
        "name": "Sanctified Flail",
        "slot": "main_hand",
        "rarity": "Uncommon",
        "desc": "A heavy iron chain-flail whose spiked censer head is engraved with silvered cleansing wards that burn undead and abyssal flesh (1d8 bludgeoning + 1d4 radiant).",
        "visual_appearance": "swinging a heavy chain-flail with a glowing silver-engraved spiked censer head"
    },
    "concealed trench daggers": {
        "name": "Concealed Trench Daggers",
        "slot": "main_hand",
        "rarity": "Uncommon",
        "desc": "Twin stiletto trench blades fitted with brass knuckle-guards, balanced for rapid armor-gap punctures (2d4 piercing, Finesse, +2 stealth draw).",
        "visual_appearance": "wielding twin brass-knuckled trench stiletto daggers"
    },
    "kinetic shock-staff": {
        "name": "Kinetic Shock-Staff",
        "slot": "main_hand",
        "rarity": "Uncommon",
        "desc": "A resonant ironwood quarterstaff shod with copper induction rings and a quartz crown that discharges telekinetic shockwaves on impact (1d8 bludgeoning + 1d4 force).",
        "visual_appearance": "holding a tall ironwood quarterstaff ringed with glowing copper induction coils and a violet quartz crown"
    },
    "reinforced spear": {
        "name": "Reinforced Spear",
        "slot": "main_hand",
        "rarity": "Common",
        "desc": "A long ash-shafted boar spear reinforced with steel langets and a cross-lugged leaf blade for keeping charging beasts at bay (1d8 piercing, Reach).",
        "visual_appearance": "wielding a long steel-tipped boar spear with cross-guard lugs"
    },
    "twin scavenger daggers": {
        "name": "Twin Scavenger Daggers",
        "slot": "main_hand",
        "rarity": "Common",
        "desc": "A matched pair of leaf-bladed survival knives ground from leaf-spring steel with paracord-wrapped hilts (1d6 slashing, Finesse).",
        "visual_appearance": "wielding a matched pair of paracord-wrapped scavenger daggers"
    },
    "fenrir's tusk": {
        "name": "Fenrir's Tusk (Grade 5 Bearded Axe)",
        "slot": "main_hand",
        "rarity": "Legendary",
        "desc": "An Einherjar-tier bearded war-axe forged from meteoric black-iron and rimed with eternal rime-frost (2d8 slashing + 1d6 cold).",
        "visual_appearance": "wielding Fenrir's Tusk, a jagged meteoric black-iron bearded axe rimed with glowing ice-blue frost runes"
    },
    "fenrir's howl (grade 6 mythic great-axe)": {
        "name": "Fenrir's Howl (Grade 6 Mythic Great-Axe)",
        "slot": "main_hand",
        "rarity": "Mythic",
        "desc": "A legendary black-iron bearded greataxe infused with sub-zero aetheric frost and the gilded core resonance of the Spire Overlord (+6 ATK, 2d12 slashing/cold, Crystalline Frost Wave).",
        "visual_appearance": "wielding Fenrir's Howl, a colossal mythic black-iron greataxe radiating a swirling aura of crystalline frost and golden Overlord runes"
    },
    "mjöllnir-null": {
        "name": "Mjöllnir-Null (Grade 5 Trench Hammer)",
        "slot": "off_hand",
        "rarity": "Legendary",
        "desc": "A heavy Einherjar kinetic trench maul whose magnetized strike-face discharges construct-shattering shockwaves (2d8 bludgeoning + 1d6 lightning).",
        "visual_appearance": "wielding Mjöllnir-Null, a heavy rectangular runic trench warhammer crackling with blue magnetic lightning arcs"
    },
    "mjölnir-prime (grade 6 mythic titan-hammer)": {
        "name": "Mjölnir-Prime (Grade 6 Mythic Titan-Hammer)",
        "slot": "off_hand",
        "rarity": "Mythic",
        "desc": "An earth-shattering mythic trench hammer surging with overcharged magnetic kinetic conduits (+5 ATK, 3d8 bludgeoning/lightning, Kinetic Armor Shatter).",
        "visual_appearance": "wielding Mjölnir-Prime, a massive gold-and-iron mythic titan warhammer wreathed in blinding voltaic plasma"
    },

    # --- PLAYER & GENERAL ARMOR / HEADGEAR ---
    "threadbare scavenger tunic": {
        "name": "Threadbare Scavenger Tunic",
        "slot": "chest",
        "rarity": "Common",
        "desc": "Weathered pre-collapse canvas jacket and patched denim work-clothes reinforced at the elbows and shoulders with stitched leather scraps (+1 AC).",
        "visual_appearance": "wearing a weathered, patched dark-canvas scavenger jacket over a rugged tunic with stitched leather shoulder pads"
    },
    "reinforced leather": {
        "name": "Reinforced Leather",
        "slot": "chest",
        "rarity": "Uncommon",
        "desc": "Supple, oil-darkenedboiled cuirbouilli leather breastplate and pauldrons reinforced with blackened steel rivets, cured beast-hide straps, and a heavy fur-trimmed collar (+3 AC, full mobility).",
        "visual_appearance": "wearing rugged oil-darkened reinforced leather armor with riveted black-iron shoulder pauldrons, buckled chest straps, and a dark fur-trimmed collar"
    },
    "chainmail hauberk": {
        "name": "Chainmail Hauberk",
        "slot": "chest",
        "rarity": "Uncommon",
        "desc": "Interlocking rings of tempered high-carbon steel worn over a padded gambeson, offering reliable protection against slashing blades (+5 AC).",
        "visual_appearance": "wearing a heavy interlocking steel chainmail hauberk over a quilted dark gambeson"
    },
    "black-iron runic plate": {
        "name": "Black-Iron Runic Plate",
        "slot": "chest",
        "rarity": "Rare",
        "desc": "Heavy articulated black-iron cuirass and pauldrons etched with glowing cyan Elder Futhark ward-runes and draped with a dire-wolf fur mantle (+8 AC).",
        "visual_appearance": "clad in heavy articulated black-iron plate armor etched with glowing cyan Elder Futhark runes and a thick dire-wolf fur mantle draped over the shoulders"
    },
    "einherjar rig": {
        "name": "Einherjar Rig (Grade 5 Power-Plate)",
        "slot": "chest",
        "rarity": "Legendary",
        "desc": "Masterwork Grade 5 Aether-armored exo-cuirass powered by pressurized mana-conduits and interlocking dwarven steel plates (+8 AC, 250 durability).",
        "visual_appearance": "clad in an imposing Grade 5 Einherjar exo-plate cuirass with glowing cyan mana-conduits and heavy rune-etched pauldrons"
    },
    "einherjar sovereign aegis (grade 6 mythic power-rig)": {
        "name": "Einherjar Sovereign Aegis (Grade 6 Mythic Power-Rig)",
        "slot": "chest",
        "rarity": "Mythic",
        "desc": "Impenetrable Grade 6 mythic runic plate engineered with living aether-conduits and sovereign golden ward lattices (+10 AC, DR 3, Aetheric Citadel Fortress).",
        "visual_appearance": "clad in the radiant Einherjar Sovereign Aegis mythic full-plate armor, gleaming with black-iron, gilded Overlord trim, and blazing cyan force-wards"
    },

    # --- BOSS DROPS, GRAFT COMPONENTS & CAMPAIGN ITEMS ---
    "spell slate: earth tremor hex": {
        "name": "Spell Slate: Earth Tremor Hex",
        "slot": "accessory",
        "rarity": "Rare",
        "desc": "A scorched crystalline data-matrix and basalt runic tablet salvaged from the Runic Quarry Golem. Channeling mana into its carved seismic glyphs unleashes a localized ground-shattering shockwave (Earth Tremor Hex: 2d6 force/bludgeoning in a 15ft cone, DC 13 DEX save or knocked Prone).",
        "visual_appearance": "carrying a scorched basalt rune-slate glowing with amber seismic fracture glyphs at the belt"
    },
    "ration pack": {
        "name": "Ration Pack",
        "slot": "consumable",
        "rarity": "Common",
        "desc": "Vacuum-sealed military-grade nutrient bars, dried beef jerky, and electrolyte salt tablets. Restores 15 HP and clears mild travel fatigue when consumed during a short rest.",
        "visual_appearance": "a compact olive-drab vacuum-sealed field ration pouch"
    },
    "bottled water": {
        "name": "Bottled Water",
        "slot": "consumable",
        "rarity": "Common",
        "desc": "Clean, uncontaminated spring water sealed in a pre-Integration plastic bottle. Prevents dehydration and restores 5 Stamina/Focus.",
        "visual_appearance": "a sealed clear bottle of pure drinking water"
    },
    "survival rations": {
        "name": "Survival Rations",
        "slot": "consumable",
        "rarity": "Common",
        "desc": "High-calorie compressed oat-and-honey cakes with dried trail mix. Restores 10 HP and sustains 1 day of wilderness marching.",
        "visual_appearance": "wrapped canvas packets of compressed trail rations"
    },
    "[graft component] silt-marrow's geothermal core piston (tier 1 magetech core)": {
        "name": "[Graft Component] Silt-Marrow's Geothermal Core Piston (Tier 1 Magetech Core)",
        "slot": "spine",
        "rarity": "Rare",
        "desc": "The primary pressurized brass-and-basalt geothermal heart piston extracted from the chest cavity of Silt-Marrow the Unhewn. Pulses with superheated volcanic steam and orange leyline embers. Can be surgically grafted by Doc Mercer into the Spine or Torso (+1 STR, +1 CON, +10 Fire Resistance, and 1d6 thermal steam retaliation against melee attackers; Strain: 2).",
        "visual_appearance": "a glowing brass-and-basalt geothermal core piston venting wisps of incandescent orange steam along the spine and shoulder blades"
    },
    "[graft component] intact runic mind-matrix (tier 1 construct brain)": {
        "name": "[Graft Component] Intact Runic Mind-Matrix (Tier 1 Construct Brain)",
        "slot": "head",
        "rarity": "Rare",
        "desc": "A pristine, dodecahedral quartz-and-gold cognitive lattice harvested intact from Silt-Marrow's cranium. Hums with ancient autonomous excavation telemetry. Can be grafted into the Head/Neural slot by Doc Mercer (+2 INT, +1 Active Matrix Memory Slot, and tremor-sense within 30ft; Strain: 2).",
        "visual_appearance": "a glowing golden quartz runic mind-matrix crown-node pulsing softly at the temple"
    },
    "basalt carapace plating x2": {
        "name": "Basalt Carapace Plating x2",
        "slot": "torso",
        "rarity": "Uncommon",
        "desc": "Two dense, interlocking slabs of calcified volcanic basalt armor harvested from Silt-Marrow's outer shell, veined with dormant amber runes. Can be surgically grafted by Doc Mercer as subdermal/torso carapace plating (+2 AC, DR 2 Physical, immunity to subterranean tremor knockdowns) or forged into heavy Basalt Armor at an anvil.",
        "visual_appearance": "interlocking plates of dark volcanic basalt carapace veined with glowing amber runes across the torso and shoulders"
    },
    "basalt carapace plating": {
        "name": "Basalt Carapace Plating",
        "slot": "torso",
        "rarity": "Uncommon",
        "desc": "Dense, interlocking slabs of calcified volcanic basalt armor harvested from Silt-Marrow's outer shell, veined with dormant amber runes (+2 AC, DR 2 Physical).",
        "visual_appearance": "interlocking plates of dark volcanic basalt carapace veined with glowing amber runes across the torso and shoulders"
    },
    "runic slag scrap x3": {
        "name": "Runic Slag Scrap x3",
        "slot": "material",
        "rarity": "Common",
        "desc": "Three heavy chunks of conductive arcane iron-slag salvaged from a shattered golem frame. Rich in residual mana conductivity; used for repairing Grade 1–3 weapons, rigging shrapnel traps, or smelting at a forge.",
        "visual_appearance": "jagged chunks of metallic slag glowing faintly with residual blue rune-sparks"
    },
    "runic slag scrap": {
        "name": "Runic Slag Scrap",
        "slot": "material",
        "rarity": "Common",
        "desc": "Conductive arcane iron-slag harvested from a construct's frame. Used for field smithing repairs and smelting.",
        "visual_appearance": "jagged chunks of metallic slag glowing faintly with residual blue rune-sparks"
    },

    # --- COMPANION SIGNATURE WEAPONS, ARMOR & ITEMS (ALL 18 COMPANIONS) ---
    "aether-lock carbine": {
        "name": "Aether-Lock Carbine",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Ren's signature Grade 2 brass-and-crystal MageTech caster carbine. Channels condensed radiant mana through a rifled quartz barrel to fire piercing kinetic-light bolts (1d10 radiant/force, range 100ft, never uses gunpowder).",
        "visual_appearance": "wielding an ornate brass-and-crystal Aether-Lock MageTech caster carbine with glowing cyan mana conduits along the barrel"
    },
    "runic vanguard blade": {
        "name": "Runic Vanguard Blade",
        "slot": "off_hand",
        "rarity": "Uncommon",
        "desc": "A balanced single-edged magetech shortblade etched with defensive deflection glyphs along the fuller (1d6 slashing + +1 parry AC).",
        "visual_appearance": "carrying a sleek rune-etched Vanguard shortblade at the hip"
    },
    "alchemical haze pellets": {
        "name": "Alchemical Haze Pellets",
        "slot": "accessory",
        "rarity": "Uncommon",
        "desc": "Pressurized glass spheres filled with luminescent smoke-screen reagent that detonate on impact to obscure line-of-sight and grant party disengage.",
        "visual_appearance": "a belt bandolier of glowing alchemical smoke-haze glass spheres"
    },
    "midnight-blue leyline duster": {
        "name": "Midnight-Blue Leyline Duster",
        "slot": "chest",
        "rarity": "Uncommon",
        "desc": "A high-collared midnight-blue tailcoat duster woven with silver leyline thread over reinforced scholar's leather (+3 AC, +1 Arcane defense).",
        "visual_appearance": "wearing a high-collared midnight-blue leyline duster coat trimmed with silver runic piping over reinforced leather vest"
    },
    "aetheric ocular lens": {
        "name": "Aetheric Ocular Lens",
        "slot": "head",
        "rarity": "Rare",
        "desc": "A brass wire-rimmed monocle visor fitted with a faceted cyan mana-crystal that displays enemy hitboxes, telegraph vectors, and structural weak points.",
        "visual_appearance": "wearing wire-rimmed brass spectacles fitted with a glowing cyan Aetheric ocular lens over one eye"
    },
    "aetheric longbow": {
        "name": "Aetheric Longbow",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Elora's silver-inlaid elven longbow whose bowstring is spun from pure starlight mana (1d8 piercing + 1d4 radiant).",
        "visual_appearance": "wielding a graceful silver-inlaid elven longbow strung with a glowing starlight mana bowstring"
    },
    "twin crystal daggers": {
        "name": "Twin Crystal Daggers",
        "slot": "off_hand",
        "rarity": "Uncommon",
        "desc": "Paired prism-glass parrying daggers that refract ambient light into blinding flashes (1d6 piercing, Finesse).",
        "visual_appearance": "wearing twin translucent prism-crystal daggers sheathed at the waist"
    },
    "wind-strider shroud": {
        "name": "Wind-Strider Shroud",
        "slot": "chest",
        "rarity": "Rare",
        "desc": "Silken starlight phase-robes woven withzephyr feathers that blur the wearer's silhouette in motion (+4 AC, +10ft speed).",
        "visual_appearance": "clad in flowing silver-and-indigo silk starlight phase-robes with a wind-strider cloak"
    },
    "deepforged war-axe": {
        "name": "Deepforged War-Axe",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Torvald's heavy dwarven gromril war-axe stamped with ancestral anvil runes (1d10 slashing, ignores 2 points of target armor).",
        "visual_appearance": "wielding a heavy dwarven deepforged war-axe glowing with molten-gold forge runes"
    },
    "adamant bulwark tower shield": {
        "name": "Adamant Bulwark Tower Shield",
        "slot": "off_hand",
        "rarity": "Rare",
        "desc": "A massive castle-gate-sized tower pavise forged from adamant alloy that can anchor into the floor to provide total cover (+4 AC).",
        "visual_appearance": "carrying a massive adamant bulwark tower shield wide as a fortress gate"
    },
    "runic repair mallet": {
        "name": "Runic Repair Mallet",
        "slot": "accessory",
        "rarity": "Uncommon",
        "desc": "A master-smith's rune-etched forging hammer capable of striking out dents and restoring armor durability mid-expedition.",
        "visual_appearance": "a heavy rune-stamped smithing mallet hooked to the belt"
    },
    "deepforged runic plate armor": {
        "name": "Deepforged Runic Plate Armor",
        "slot": "chest",
        "rarity": "Rare",
        "desc": "Heavy dwarven gromril-and-steel plate armor engraved with glowing gold anvil-runes and soot-darkened forge pauldrons (+8 AC, Fire Resistance).",
        "visual_appearance": "clad in heavy dwarven Deepforged Runic Plate Armor engraved with glowing molten-gold forge runes"
    },
    "serrated scrap dagger": {
        "name": "Serrated Scrap Dagger",
        "slot": "main_hand",
        "rarity": "Uncommon",
        "desc": "Kibs's wickedly notched gut-hook dagger ground from high-speed saw steel, designed to inflict deep bleeding wounds (1d6 piercing + Bleed).",
        "visual_appearance": "wielding a wickedly serrated scrap-steel dagger"
    },
    "wrist shank": {
        "name": "Wrist Shank",
        "slot": "off_hand",
        "rarity": "Uncommon",
        "desc": "A spring-loaded stiletto blade mounted to a leather forearm bracer for instant surprise strikes (1d4 piercing).",
        "visual_appearance": "wearing a spring-loaded steel wrist-shank bracer on the forearm"
    },
    "neurotoxin vials": {
        "name": "Neurotoxin Vials",
        "slot": "accessory",
        "rarity": "Uncommon",
        "desc": "Concentrated paralytic venom distilled from tunnel-crawler glands, used to coat throwing blades.",
        "visual_appearance": "a leather chest-strap holding glowing green neurotoxin glass vials"
    },
    "skeleton lockpick set": {
        "name": "Skeleton Lockpick Set",
        "slot": "accessory",
        "rarity": "Uncommon",
        "desc": "Precision titanium tension wrenches, rakes, and runic ward-shims rolled in a oiled leather case (+3 to lockpicking and trap disarm).",
        "visual_appearance": "an oiled leather roll of precision titanium lockpicks at the hip"
    },
    "scavenged shadow-shroud leathers": {
        "name": "Scavenged Shadow-Shroud Leathers",
        "slot": "chest",
        "rarity": "Uncommon",
        "desc": "Supple soot-blackened scavenger leather armor stitched with sound-dampening rat-pelts and concealed tool pockets (+4 AC, +2 Stealth).",
        "visual_appearance": "wearing soot-blackened Scavenged Shadow-Shroud leather armor with a hooded mantle and utility pouches"
    },
    "winged aether-spear": {
        "name": "Winged Aether-Spear",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Valeria's long silver-alloyed aerial lance with sweeping wing-lugs that channel diving wind-blasts (1d10 piercing + 1d6 thunder on dive).",
        "visual_appearance": "wielding an ornate silver Winged Aether-Spear crackling with cyan wind-streams"
    },
    "solar aegis shield": {
        "name": "Solar Aegis Shield",
        "slot": "off_hand",
        "rarity": "Rare",
        "desc": "A polished sun-gold round shield emblazoned with a falcon crest that can flare with blinding solar radiance (+2 AC).",
        "visual_appearance": "carrying a gleaming sun-gold Solar Aegis shield embossed with a soaring falcon crest"
    },
    "falcon crest mail": {
        "name": "Falcon Crest Mail",
        "slot": "chest",
        "rarity": "Rare",
        "desc": "Lightweight interlocking silver-and-azure valkyrie scale mail fitted with spinal ports for aerodynamic aether-glider wings (+6 AC).",
        "visual_appearance": "clad in gleaming silver-and-azure Falcon Crest scale mail with luminous cyan aether-glider wings extending from the back"
    },
    "bone-chime scythe": {
        "name": "Bone-Chime Scythe",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Morrigan's crescent war-scythe forged from black obsidian glass and hung with carved bone spirit-chimes (1d10 necrotic/slashing).",
        "visual_appearance": "wielding a curved black-obsidian war-scythe hung with whispering bone chimes and trailing emerald soul-mist"
    },
    "soul-vessel phylactery": {
        "name": "Soul-Vessel Phylactery",
        "slot": "off_hand",
        "rarity": "Rare",
        "desc": "A wrought-iron lantern cage housing captured emerald wraith-wisps that siphon vitality from fallen foes.",
        "visual_appearance": "holding a dark wrought-iron soul-lantern glowing with captive emerald spirit-wisps"
    },
    "obsidian shroud": {
        "name": "Obsidian Shroud",
        "slot": "chest",
        "rarity": "Rare",
        "desc": "Gothic midnight-black velvet and bone-ribbed vestments that drink in ambient light (+4 AC, necrotic resistance).",
        "visual_appearance": "draped in a gothic obsidian-and-bone mantle shrouded in dark necrotic mist"
    },
    "granite-studded cestus": {
        "name": "Granite-Studded Cestus",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Garrick's heavy iron-and-basalt striking gauntlets that amplify seismic ki-punches into armor-cracking impacts (1d8 bludgeoning + tremor stagger).",
        "visual_appearance": "wearing heavy basalt-and-iron studded cestus gauntlets glowing with amber tectonic ki-runes"
    },
    "weighted linen wraps": {
        "name": "Weighted Linen Wraps",
        "slot": "off_hand",
        "rarity": "Uncommon",
        "desc": "Lead-weighted monastic forearm wraps inscribed with earth-grounding mantras (+1 AC when parrying).",
        "visual_appearance": "forearms bound in rune-inscribed monastic linen hand-wraps"
    },
    "iron-thread gi": {
        "name": "Iron-Thread Gi",
        "slot": "chest",
        "rarity": "Uncommon",
        "desc": "Sleeveless martial arts training garb woven with flexible iron-silk thread, leaving the arms and chest free to vent tectonic ki (+4 AC).",
        "visual_appearance": "wearing a sleeveless dark iron-thread martial arts gi revealing stone-grafted arms and glowing chest ki-glyphs"
    },
    "composite wind-recurve bow": {
        "name": "Composite Wind-Recurve Bow",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Sariel's masterwork horn-and-ironwood recurve bow enchanted with silent wind-guiding glyphs (1d8 piercing, ignores wind penalties).",
        "visual_appearance": "wielding an emerald-etched horn-and-ironwood recurve longbow"
    },
    "camouflage ghillie-cloak": {
        "name": "Camouflage Ghillie-Cloak",
        "slot": "chest",
        "rarity": "Uncommon",
        "desc": "Moss-green ranger leathers draped with a living autumn-leaf and lichen camouflage mantle (+4 AC, advantage on woodland stealth).",
        "visual_appearance": "clad in camouflaged moss-green ranger leathers and a living autumn-leaf ghillie cloak"
    },
    "aether-tipped broadheads": {
        "name": "Aether-Tipped Broadheads",
        "slot": "off_hand",
        "rarity": "Uncommon",
        "desc": "A quiver of thirty razor-sharp hunting arrows tipped with armor-piercing green aether-crystals.",
        "visual_appearance": "a leather back-quiver bristles with glowing green aether-tipped broadhead arrows"
    },
    "radiant war-flail": {
        "name": "Radiant War-Flail",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Brother Kaelen's heavy sun-gold warhammer-flail whose head blazes with searing golden daylight (1d8 bludgeoning + 1d6 radiant).",
        "visual_appearance": "wielding a heavy sun-gold war-flail blazing with radiant golden sunlight"
    },
    "sunstone focus censer": {
        "name": "Sunstone Focus Censer",
        "slot": "off_hand",
        "rarity": "Rare",
        "desc": "A swinging brass sanctuary censer burning consecrated solar resin that heals nearby allies and wards off shadow-fiends.",
        "visual_appearance": "holding a glowing golden sunstone sanctuary censer trailing luminous incense"
    },
    "gilded crusader mail": {
        "name": "Gilded Crusader Mail",
        "slot": "chest",
        "rarity": "Rare",
        "desc": "Polished sun-gold breastplate worn over white Templar vestments embroidered with the Sol Invictus crest (+7 AC).",
        "visual_appearance": "clad in a polished sun-gold breastplate over white hooded Sol-Templar vestments"
    },
    "galvanic arc staff": {
        "name": "Galvanic Arc Staff",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Zeddicus's copper-coiled Tesla lightning rod topped with a spinning brass induction sphere (1d10 lightning, chains to adjacent targets).",
        "visual_appearance": "wielding a copper-coiled Galvanic Arc Staff crackling with jumping blue lightning bolts"
    },
    "capacitor battery rig": {
        "name": "Capacitor Battery Rig",
        "slot": "off_hand",
        "rarity": "Rare",
        "desc": "A portable high-voltage Leyden-jar capacitor pack wired to heavy rubberized conduction gauntlets.",
        "visual_appearance": "strapped with a dorsal brass Leyden-jar capacitor rig humming with electric arcs"
    },
    "spark-shield coat": {
        "name": "Spark-Shield Coat",
        "slot": "chest",
        "rarity": "Uncommon",
        "desc": "An insulated slate-leather leyline trenchcoat lined with grounded copper Faraday mesh (+4 AC, immunity to lightning stun).",
        "visual_appearance": "wearing an insulated copper-mesh leyline trenchcoat and brass galvanic goggles"
    },
    "resonating aether-lute": {
        "name": "Resonating Aether-Lute",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Daphne's masterwork acoustic-arcane lute fitted with a reinforced mithril neck that projects sonic shockwaves and inspiring battle-hymns.",
        "visual_appearance": "strumming an ornate midnight-wood Aether-Lute glowing with vibrant violet harmonic strings"
    },
    "silvered stiletto": {
        "name": "Silvered Stiletto",
        "slot": "off_hand",
        "rarity": "Uncommon",
        "desc": "A needle-thin silvered dueling rapier concealed within the neck of the lute or drawn in the off-hand (1d6 piercing, Finesse).",
        "visual_appearance": "holding a gleaming silvered dueling stiletto"
    },
    "velvet performer's doublet": {
        "name": "Velvet Performer's Doublet",
        "slot": "chest",
        "rarity": "Uncommon",
        "desc": "A flamboyant midnight-velvet skaldic coat lined with concealed mithril chain-links and a silver-threaded scarf (+4 AC, +2 CHA checks).",
        "visual_appearance": "wearing a flamboyant midnight-velvet skaldic coat with silver brocade and a flowing silver-threaded scarf"
    },
    "twin serrated slag-cleavers": {
        "name": "Twin Serrated Slag-Cleavers",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Ragnarok 'Rok's massive dual-wielded jagged butcher-axes forged from furnace-quenched crucible iron (2d8 slashing, blood-rage cleave).",
        "visual_appearance": "hefting massive twin serrated crucible-iron slag-cleaver greataxes"
    },
    "spiked iron pauldrons": {
        "name": "Spiked Iron Pauldrons",
        "slot": "off_hand",
        "rarity": "Uncommon",
        "desc": "Heavy bone-and-iron shoulder plates spiked for brutal tackling charges (+1 AC, +1d6 ramming damage).",
        "visual_appearance": "wearing jagged spiked bone-and-iron shoulder pauldrons"
    },
    "troll-hide kilt": {
        "name": "Troll-Hide Kilt",
        "slot": "chest",
        "rarity": "Uncommon",
        "desc": "Thick, regenerating cured troll-hide war-harness and kilt that leaves the chest open to channel tribal blood-runes (+5 AC).",
        "visual_appearance": "wearing a heavy cured troll-hide war-kilt and leather harness over a bare chest covered in glowing crimson blood-runes"
    },
    "chrono-staff of moments": {
        "name": "Chrono-Staff of Moments",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Lyra's slender astral staff crowned with nested, counter-rotating golden astrolabe rings that bend localized time.",
        "visual_appearance": "holding a slender astral staff topped with spinning golden clockwork astrolabe rings"
    },
    "hourglass focus": {
        "name": "Hourglass Focus",
        "slot": "off_hand",
        "rarity": "Rare",
        "desc": "A floating crystal hourglass filled with upward-falling luminescent stardust used to rewind failed saving throws.",
        "visual_appearance": "orbited by a floating crystal hourglass trickling glowing golden stardust"
    },
    "star-silk robes": {
        "name": "Star-Silk Robes",
        "slot": "chest",
        "rarity": "Rare",
        "desc": "Deep indigo chronomancer vestments embroidered with shifting golden constellation charts (+4 AC).",
        "visual_appearance": "draped in deep indigo Star-Silk robes embroidered with glowing golden constellations"
    },
    "pneumatic slag-hammer": {
        "name": "Pneumatic Slag-Hammer",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Titus's colossal piston-driven industrial pile-driver maul that vents superheated steam on impact (2d10 bludgeoning).",
        "visual_appearance": "wielding a massive piston-driven Pneumatic Slag-Hammer venting pressurized white steam"
    },
    "steam-buffered kinetic barrier": {
        "name": "Steam-Buffered Kinetic Barrier",
        "slot": "off_hand",
        "rarity": "Rare",
        "desc": "A thick cast-iron siege pavise fitted with hydraulic shock-absorbers that nullify knockback (+3 AC).",
        "visual_appearance": "holding a thick cast-iron hydraulic tower pavise shield"
    },
    "cast-iron boiler chassis": {
        "name": "Cast-Iron Boiler Chassis",
        "slot": "chest",
        "rarity": "Rare",
        "desc": "Titus's riveted bronze-and-steel automaton armor plating housing an incandescent amber aether-furnace core (+9 AC).",
        "visual_appearance": "armored in heavy riveted bronze-and-steel boiler plating with a glowing amber chest furnace"
    },
    "obsidian claw-gauntlets": {
        "name": "Obsidian Claw-Gauntlets",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Nyssa's feral wooden-and-obsidian talon bracers that channel venomous primal life-energy (2d6 slashing/poison).",
        "visual_appearance": "wearing razor-sharp obsidian beast-claw gauntlets crackling with emerald primal energy"
    },
    "living bramble armor": {
        "name": "Living Bramble Armor",
        "slot": "chest",
        "rarity": "Rare",
        "desc": "Symbiotic ironwood bark and flowering razor-thorn vines that lash out at melee attackers (+5 AC, 1d4 piercing thorns).",
        "visual_appearance": "clad in living ironwood bark-armor interwoven with flexing green razor-thorn vines"
    },
    "fang talisman": {
        "name": "Fang Talisman",
        "slot": "off_hand",
        "rarity": "Uncommon",
        "desc": "An ancestral dire-predator fang fetish strung on sinew that amplifies wild-shape ferocity.",
        "visual_appearance": "wearing a necklace of carved dire-wolf fangs glowing with green druidic runes"
    },
    "void-etched greatsword": {
        "name": "Void-Etched Greatsword",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Malakor's two-handed translucent purple void-glass blade that slices through dimensional wards (2d6 slashing + 1d6 force/necrotic).",
        "visual_appearance": "wielding a translucent purple void-glass greatsword trailing shadowy dark-matter tendrils"
    },
    "null-glyph buckler": {
        "name": "Null-Glyph Buckler",
        "slot": "off_hand",
        "rarity": "Uncommon",
        "desc": "A floating obsidian-iron parrying disk inscribed with spell-devouring abyssal sigils (+2 AC vs spells).",
        "visual_appearance": "guarded by a floating obsidian Null-Glyph buckler on the off-arm"
    },
    "shadow-steel hauberk": {
        "name": "Shadow-Steel Hauberk",
        "slot": "chest",
        "rarity": "Rare",
        "desc": "Matte-black scale armor forged from abyssal alloy and draped in a tattered shadow-silk cloak (+6 AC).",
        "visual_appearance": "clad in matte-black Shadow-Steel scale mail beneath a tattered dark-matter warlock cloak"
    },
    "pneumatic acid-siphon cannon": {
        "name": "Pneumatic Acid-Siphon Cannon",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Dr. Thorne's brass-and-glass pressurized alchemical sprayer rifle that projects streams of armor-melting vitriol (2d6 acid, -2 target AC).",
        "visual_appearance": "aiming a brass-and-glass Pneumatic Acid-Siphon sprayer rifle filled with bubbling neon-green vitriol"
    },
    "bandolier of corrosive flasks": {
        "name": "Bandolier of Corrosive Flasks",
        "slot": "off_hand",
        "rarity": "Uncommon",
        "desc": "Lead-stoppered borosilicate volatile alchemical grenades ready for rapid lobbing (catalytic fire, acid, and cryo-mist).",
        "visual_appearance": "wearing a leather chest-bandolier packed with glowing multicolor alchemical reagent flasks"
    },
    "lead-lined hazard apron": {
        "name": "Lead-Lined Hazard Apron",
        "slot": "chest",
        "rarity": "Uncommon",
        "desc": "An acid-resistant slate-grey alchemist's lab duster and vulcanized rubber surgeon's apron (+4 AC, immunity to acid splash).",
        "visual_appearance": "wearing an acid-resistant slate-grey lab duster and heavy rubberized alchemist's hazard apron"
    },
    "silver-chambered crossbow": {
        "name": "Silver-Chambered Crossbow",
        "slot": "main_hand",
        "rarity": "Rare",
        "desc": "Sister Teresa's heavy repeating mechanical arbalest loaded with consecrated silver-tipped stakes (1d10 piercing + 1d6 radiant vs fiends/undead).",
        "visual_appearance": "wielding a heavy steel-and-walnut repeating mechanical crossbow loaded with glowing silver stakes"
    },
    "blessed consecrated estoc": {
        "name": "Blessed Consecrated Estoc",
        "slot": "off_hand",
        "rarity": "Rare",
        "desc": "A rigid, cruciform-hilted silvered thrusting sword designed to pierce monster hearts (1d8 piercing).",
        "visual_appearance": "carrying a cruciform-hilted silvered Inquisitor estoc blade"
    },
    "inquisitor's leather duster": {
        "name": "Inquisitor's Leather Duster",
        "slot": "chest",
        "rarity": "Rare",
        "desc": "An austere, high-collared charcoal-black leather witch-hunter coat pinned with silver purity seals and paired with a wide-brimmed hat (+5 AC).",
        "visual_appearance": "wearing a high-collared charcoal witch-hunter leather duster pinned with silver seals and a wide-brimmed inquisitor hat"
    },

    # --- TRAPS, SALVAGE MATERIALS & COMMODITIES ---
    "serrated tripwire coils": {
        "name": "Serrated Tripwire Coils",
        "slot": "material",
        "rarity": "Common",
        "desc": "Spools of razor-notched monofilament wire used for rigging perimeter bleed-traps.",
        "visual_appearance": "coils of glinting razor-serrated monofilament wire"
    },
    "anchors and tension pins": {
        "name": "Anchors and Tension Pins",
        "slot": "material",
        "rarity": "Common",
        "desc": "Hardened steel pitons and spring-loaded trigger pins used to anchor snares into stone or timber.",
        "visual_appearance": "steel piton anchors and spring tension pins"
    },
    "heavy highway snares": {
        "name": "Heavy Highway Snares",
        "slot": "material",
        "rarity": "Uncommon",
        "desc": "Braided steel tow-cable nooses salvaged from highway wreckers, capable of hoisting large beasts.",
        "visual_appearance": "heavy braided steel tow-cable snares"
    },
    "carbon line spools": {
        "name": "Carbon Line Spools",
        "slot": "material",
        "rarity": "Uncommon",
        "desc": "High-tensile woven carbon-fiber cordage with a 2,000-lb breaking strength.",
        "visual_appearance": "spools of matte-black high-tensile carbon fiber cord"
    },
    "crate of marrow-jars": {
        "name": "Crate of Marrow-Jars",
        "slot": "material",
        "rarity": "Uncommon",
        "desc": "Sealed mason jars of pungent, rendered monster bone-marrow pheromones used to lure apex predators into ambush corridors.",
        "visual_appearance": "glass jars filled with glowing amber monster marrow"
    },
    "corroded micro-capacitor": {
        "name": "Corroded Micro-Capacitor",
        "slot": "material",
        "rarity": "Common",
        "desc": "A salvaged magetech charge-cylinder still holding a volatile electrical potential; used for EMP shock-mines and weapon upgrades.",
        "visual_appearance": "a copper-fin micro-capacitor cylinder sparking with static"
    },
    "frayed copper wiring": {
        "name": "Frayed Copper Wiring",
        "slot": "material",
        "rarity": "Common",
        "desc": "Lengths of stripped conductive copper cabling salvaged from ruined conduits.",
        "visual_appearance": "coils of stripped conductive copper wire"
    },
    "titanium wire scrap": {
        "name": "Titanium Wire Scrap",
        "slot": "material",
        "rarity": "Uncommon",
        "desc": "Lightweight, high-tensile titanium alloy struts harvested from construct joints.",
        "visual_appearance": "gleaming silver titanium alloy struts and wire"
    },
    "rendered chimera marrow": {
        "name": "Rendered Chimera Marrow",
        "slot": "material",
        "rarity": "Uncommon",
        "desc": "Nutrient-dense, mana-infused bone marrow harvested from mutated beasts; prized for campfire cooking and bio-grafting.",
        "visual_appearance": "a sealed vial of luminescent crimson chimera marrow"
    },
    "hardened chitin plates": {
        "name": "Hardened Chitin Plates",
        "slot": "material",
        "rarity": "Uncommon",
        "desc": "Layered insectoid exoskeletal plates resilient against acid and slashing blows.",
        "visual_appearance": "iridescent dark chitin armor plates"
    },
    "mutated sinew cord": {
        "name": "Mutated Sinew Cord",
        "slot": "material",
        "rarity": "Common",
        "desc": "Elastic, high-draw monster tendon fibers ideal for bowstrings and armor lacing.",
        "visual_appearance": "braided cords of tough crimson monster sinew"
    },
    "scrap iron plate": {
        "name": "Scrap Iron Plate",
        "slot": "material",
        "rarity": "Common",
        "desc": "Heavy structural iron plating suitable for patching shields, chest armor, and fortifications.",
        "visual_appearance": "riveted slabs of heavy salvage iron plate"
    },
    "tainted metallic scrap": {
        "name": "Tainted Metallic Scrap",
        "slot": "material",
        "rarity": "Common",
        "desc": "Scorched metal fragments twisted by aetheric radiation; can be refined down at a smithy.",
        "visual_appearance": "scorched fragments of warped metallic scrap"
    },
    "refined aether-alloy": {
        "name": "Refined Aether-Alloy",
        "slot": "material",
        "rarity": "Rare",
        "desc": "Pure, high-grade dwarven-and-magetech ingot gleaming with internal blue leyline veins; required for Grade 4–6 Mythic forging.",
        "visual_appearance": "a gleaming silver-blue ingot veined with glowing leyline light"
    },
    "aetheric repair flux": {
        "name": "Aetheric Repair Flux",
        "slot": "consumable",
        "rarity": "Uncommon",
        "desc": "Alchemical welding paste that fuses micro-fractures in metal, leather, and runic crystal, restoring 50 durability to any item.",
        "visual_appearance": "a brass canister of luminescent blue welding repair paste"
    }
}


def get_item_details(item_name_or_dict, inventory: list = None) -> dict:
    """
    Resolves full item metadata (name, slot, rarity, desc, visual_appearance) for any item in the game.
    Guarantees every item has a complete lore/mechanical description (`desc`) and a vivid `visual_appearance`
    for dynamic character rendering in the Image Generator.
    """
    raw_name = ""
    existing_desc = ""
    existing_vis = ""
    existing_rarity = "Common"
    existing_slot = None

    if isinstance(item_name_or_dict, dict):
        raw_name = str(item_name_or_dict.get("name", "Unknown Item")).strip()
        existing_desc = str(item_name_or_dict.get("desc", item_name_or_dict.get("description", ""))).strip()
        existing_vis = str(item_name_or_dict.get("visual_appearance", "")).strip()
        existing_rarity = str(item_name_or_dict.get("rarity", "Common")).strip()
        existing_slot = item_name_or_dict.get("slot")
    else:
        raw_name = str(item_name_or_dict or "").strip()

    if not raw_name or raw_name.lower() == "none":
        return {
            "name": "None",
            "slot": existing_slot or "none",
            "rarity": "Common",
            "desc": "Nothing equipped in this slot.",
            "visual_appearance": "unarmored / bare"
        }

    # Check inventory if provided for custom descriptions
    if inventory and isinstance(inventory, list) and (not existing_desc or not existing_vis):
        for inv_item in inventory:
            if isinstance(inv_item, dict):
                inv_name = str(inv_item.get("name", "")).strip()
                if inv_name.lower() == raw_name.lower() or raw_name.lower() in inv_name.lower():
                    if not existing_desc and inv_item.get("desc"):
                        existing_desc = str(inv_item["desc"]).strip()
                    if not existing_vis and inv_item.get("visual_appearance"):
                        existing_vis = str(inv_item["visual_appearance"]).strip()
                    if inv_item.get("rarity"):
                        existing_rarity = str(inv_item["rarity"]).strip()
                    break

    # Normalize lookup key (normalize curly apostrophes, lowercase, strip trailing qty like ' x2')
    norm_key = raw_name.replace("’", "'").lower().strip()
    norm_no_qty = re.sub(r'\s+x\d+$', '', norm_key).strip()
    norm_no_parens = re.sub(r'\s*\([^)]*\)\s*', ' ', norm_no_qty).strip()

    # 1. Exact or normalized match in CANONICAL_ITEM_CATALOG
    for candidate in (norm_key, norm_no_qty, norm_no_parens):
        if candidate in CANONICAL_ITEM_CATALOG:
            cat_entry = copy.deepcopy(CANONICAL_ITEM_CATALOG[candidate])
            cat_entry["name"] = raw_name
            if existing_desc and len(existing_desc) > len(cat_entry.get("desc", "")):
                cat_entry["desc"] = existing_desc
            if existing_vis:
                cat_entry["visual_appearance"] = existing_vis
            return cat_entry

    # 2. Substring match in CANONICAL_ITEM_CATALOG
    for k, cat_entry in CANONICAL_ITEM_CATALOG.items():
        if k in norm_key or norm_no_qty in k:
            res = copy.deepcopy(cat_entry)
            res["name"] = raw_name
            if existing_desc and len(existing_desc) > len(res.get("desc", "")):
                res["desc"] = existing_desc
            if existing_vis:
                res["visual_appearance"] = existing_vis
            return res

    # 3. Check CANONICAL_GRAFTS
    for g_key, g_data in CANONICAL_GRAFTS.items():
        g_name_low = g_data["name"].lower()
        if g_key in norm_key or g_name_low in norm_key or norm_no_qty in g_name_low:
            desc_str = f"{g_data['description']} (Effect: {g_data['effect']} | Strain: {g_data['strain']})"
            vis_str = existing_vis or f"visibly integrated {g_data['name']} ({g_data['description'].lower().rstrip('.')})"
            return {
                "name": raw_name,
                "slot": (g_data.get("allowed_slots") or ["graft"])[0],
                "rarity": "Rare",
                "desc": existing_desc or desc_str,
                "visual_appearance": vis_str
            }

    # 4. Check MYTHIC_RECIPES & HOMESTEAD_TROPHIES
    for m_key, m_data in MYTHIC_RECIPES.items():
        if m_data["name"].lower() in norm_key or norm_no_qty in m_data["name"].lower():
            return {
                "name": raw_name,
                "slot": m_data.get("slot", "main_hand"),
                "rarity": "Mythic",
                "desc": existing_desc or f"{m_data['description']} ({m_data['active_technique']['name']}: {m_data['active_technique']['desc']})",
                "visual_appearance": existing_vis or f"equipped with the mythic {m_data['name']} ({m_data['description'].lower().rstrip('.')})"
            }
    for t_key, t_data in HOMESTEAD_TROPHIES.items():
        if t_data["name"].lower() in norm_key or norm_no_qty in t_data["name"].lower():
            return {
                "name": raw_name,
                "slot": "accessory",
                "rarity": "Legendary",
                "desc": existing_desc or f"Apex Boss Trophy: {t_data['name']}. Grants {t_data['buff_name']}: {t_data['desc']}",
                "visual_appearance": existing_vis or f"bearing the {t_data['name']} trophy emblem"
            }

    # 5. Check PERSONAL_RELICS from character_generator if importable
    try:
        import backend.character_generator as cg
        for r_key, r_data in getattr(cg, "PERSONAL_RELICS", {}).items():
            r_name_low = r_data["name"].lower()
            if r_key in norm_key or r_name_low in norm_key or norm_no_qty in r_name_low:
                return {
                    "name": raw_name,
                    "slot": "accessory",
                    "rarity": r_data.get("rarity", "Unique"),
                    "desc": existing_desc or f"{r_data['desc']} | Mechanics: {r_data.get('mechanics', '')}",
                    "visual_appearance": existing_vis or f"carrying their pre-Integration {r_data['name']} ({r_data['desc'].split('.')[0].lower()})"
                }
    except Exception:
        pass

    # 6. Intelligent Procedural Synthesizer for any emergent/custom item
    low = norm_key
    inferred_slot = existing_slot or "item"
    if any(w in low for w in ["helm", "hat", "hood", "crown", "visor", "goggles", "spectacles", "lens", "mask", "circlet"]):
        inferred_slot = "head"
        vis_default = f"wearing {raw_name} on the head"
        desc_default = f"Protective headgear ({raw_name}) forged for survival in the Fractured Overlay."
    elif any(w in low for w in ["armor", "plate", "leather", "tunic", "robe", "duster", "coat", "mail", "hauberk", "cuirass", "rig", "vest", "shroud", "mantle", "gi", "kilt", "apron"]):
        inferred_slot = "chest"
        vis_default = f"clad in {raw_name} torso armor"
        desc_default = f"Protective body armor ({raw_name}) reinforced against physical and aetheric strikes."
    elif any(w in low for w in ["shield", "buckler", "pavise", "aegis", "censer", "lantern", "phylactery", "quiver", "bandolier"]):
        inferred_slot = "off_hand"
        vis_default = f"carrying {raw_name} in the off-hand"
        desc_default = f"Tactical off-hand equipment ({raw_name}) providing defensive warding or combat utility."
    elif any(w in low for w in ["axe", "sword", "blade", "hammer", "mace", "flail", "dagger", "knife", "bow", "crossbow", "spear", "lance", "scythe", "staff", "wand", "carbine", "pistol", "cannon", "cestus", "claws", "cleaver", "lute", "estoc", "rapier"]):
        inferred_slot = "main_hand"
        vis_default = f"wielding {raw_name}"
        desc_default = f"Combat weapon ({raw_name}) balanced for lethal engagements in the Fractured Overlay."
    elif any(w in low for w in ["graft", "piston", "matrix", "carapace", "gland", "tendon", "cortex", "ocular", "spine"]):
        inferred_slot = "graft"
        vis_default = f"augmented with an integrated {raw_name}"
        desc_default = f"Bio-arcane or magetech graft component ({raw_name}) compatible with Doc Mercer's surgical table."
    else:
        vis_default = f"carrying {raw_name}"
        desc_default = f"Field-recovered item ({raw_name}) from the Fractured Overlay."

    return {
        "name": raw_name,
        "slot": inferred_slot,
        "rarity": existing_rarity or "Common",
        "desc": existing_desc if existing_desc else desc_default,
        "visual_appearance": existing_vis if existing_vis else vis_default
    }


def enrich_item_dict(item, inventory: list = None) -> dict:
    """
    Converts a string or partial item dictionary into a fully described item dictionary
    containing `name`, `rarity`, `durability`, `max_durability`, `qty`, `slot`, `desc`, and `visual_appearance`.
    """
    details = get_item_details(item, inventory=inventory)
    if isinstance(item, dict):
        enriched = copy.deepcopy(item)
        enriched.setdefault("name", details["name"])
        enriched.setdefault("rarity", details["rarity"])
        grade = get_item_grade(enriched)
        default_dur = ITEM_GRADE_SCALING.get(grade, {}).get("default_durability", 100)
        enriched.setdefault("durability", default_dur)
        enriched.setdefault("max_durability", default_dur)
        enriched.setdefault("qty", 1)
        enriched["slot"] = enriched.get("slot") or details["slot"]
        if not enriched.get("desc") or not str(enriched.get("desc")).strip():
            enriched["desc"] = details["desc"]
        if not enriched.get("visual_appearance") or not str(enriched.get("visual_appearance")).strip():
            enriched["visual_appearance"] = details["visual_appearance"]
        return enriched
    else:
        raw_str = str(item).strip()
        qty = 1
        if " x" in raw_str.lower():
            parts = re.split(r'\s+x', raw_str, flags=re.IGNORECASE)
            if len(parts) == 2 and parts[1].isdigit():
                qty = int(parts[1])
        grade = get_item_grade(raw_str)
        default_dur = ITEM_GRADE_SCALING.get(grade, {}).get("default_durability", 100)
        return {
            "name": details["name"],
            "rarity": details["rarity"],
            "durability": default_dur,
            "max_durability": default_dur,
            "qty": qty,
            "slot": details["slot"],
            "desc": details["desc"],
            "visual_appearance": details["visual_appearance"]
        }


def enrich_inventory_list(inventory: list) -> list:
    """Ensures every item in an inventory list is a fully described dict with `desc` and `visual_appearance`."""
    if not isinstance(inventory, list):
        return []
    return [enrich_item_dict(item, inventory=inventory) for item in inventory]


def build_character_visual_profile(character_state: dict, entity_id: str = "player") -> str:
    """
    Dynamically constructs a character's visual description for the Image Generator based on:
    1. Base Physical Anatomy (face, build, hair, eyes, lineage traits)
    2. Currently Equipped Gear (`head`, `chest`, `main_hand`, `off_hand`, `accessory`) + Durability Wear State
    3. Installed Magitech & Bio-Grafts (`grafts`, `graft_system`, `active_grafts`)
    """
    if not isinstance(character_state, dict):
        return ""

    name = character_state.get("name", entity_id)
    race = character_state.get("race", character_state.get("species_or_type", "Human"))
    char_class = character_state.get("class", character_state.get("role", "Survivor"))
    inv = character_state.get("inventory", [])

    # 1. Resolve Base Physical Anatomy (without hardcoded armor/weapons)
    lookup_id = entity_id.lower()
    name_low = name.lower()
    base_anat = None
    if lookup_id in BASE_CHARACTER_ANATOMY:
        base_anat = BASE_CHARACTER_ANATOMY[lookup_id]["base_anatomy"]
    elif name_low in BASE_CHARACTER_ANATOMY:
        base_anat = BASE_CHARACTER_ANATOMY[name_low]["base_anatomy"]
    else:
        for k, v in BASE_CHARACTER_ANATOMY.items():
            if v["name"].lower() in name_low or name_low in v["name"].lower():
                base_anat = v["base_anatomy"]
                break

    if not base_anat:
        base_anat = f"{race} {char_class} named {name}"

    # 2. Resolve Currently Equipped Gear per slot
    equipped = character_state.get("equipped", {})
    gear_dur = character_state.get("gear_durability", {})

    # If companion sheet lacks an explicit `equipped` dict, infer from their inventory
    if not equipped and inv:
        inferred_eq = {"head": "None", "chest": "None", "main_hand": "None", "off_hand": "None", "accessory": "None"}
        for it in inv:
            det = get_item_details(it, inventory=inv)
            s = det.get("slot", "item")
            if s in inferred_eq and inferred_eq[s] == "None":
                inferred_eq[s] = det["name"]
            elif s == "main_hand" and inferred_eq["main_hand"] != "None" and inferred_eq["off_hand"] == "None":
                inferred_eq["off_hand"] = det["name"]
        equipped = inferred_eq

    slot_descriptions = []
    for slot in ["head", "chest", "main_hand", "off_hand", "accessory"]:
        item_val = equipped.get(slot, "None") if isinstance(equipped, dict) else "None"
        slot_label = slot.replace("_", " ").upper()
        if not item_val or str(item_val).strip().lower() == "none":
            if slot == "head":
                slot_descriptions.append("HEAD: Bare-headed (no helmet; hair and face clearly visible)")
            elif slot == "chest":
                slot_descriptions.append("CHEST: Simple survivor attire (no heavy armor equipped)")
            elif slot == "main_hand":
                slot_descriptions.append("MAIN HAND: Unarmed / empty-handed")
            elif slot == "off_hand":
                slot_descriptions.append("OFF HAND: Empty / free hand")
            continue

        det = get_item_details(item_val, inventory=inv)
        vis_text = det.get("visual_appearance", det.get("desc", str(item_val)))

        # Check durability state for visual battle-wear
        wear_tag = ""
        if isinstance(gear_dur, dict) and slot in gear_dur and isinstance(gear_dur[slot], dict):
            cur_d = gear_dur[slot].get("cur", 100)
            max_d = gear_dur[slot].get("max", 100)
            d_state = get_durability_state(cur_d, max_d)
            if d_state["is_broken"]:
                wear_tag = " [VISUALLY SHATTERED / BROKEN & CRACKED]"
            elif d_state["is_dulled"]:
                wear_tag = " [HEAVILY BATTLE-SCARRED, SCORCHED & NOTCHED]"
            elif d_state["state"] == "Worn":
                wear_tag = " [WEATHERED & BATTLE-TESTED]"

        slot_descriptions.append(f"{slot_label}: {det['name']} — {vis_text}{wear_tag}")

    # 3. Resolve Active / Installed Grafts
    graft_visuals = []
    # Check player['grafts'] dict
    p_grafts = character_state.get("grafts", {})
    if isinstance(p_grafts, dict):
        for g_slot, g_val in p_grafts.items():
            if g_val:
                g_det = get_item_details(g_val, inventory=inv)
                graft_visuals.append(f"{g_slot.upper()} GRAFT: {g_det['name']} ({g_det['visual_appearance']})")

    # Check player['graft_system']['installed_grafts']
    sys_grafts = character_state.get("graft_system", {}).get("installed_grafts", {})
    if isinstance(sys_grafts, dict):
        for g_slot, g_val in sys_grafts.items():
            if g_val:
                g_det = get_item_details(g_val, inventory=inv)
                entry_str = f"{g_slot.upper()} GRAFT: {g_det['name']} ({g_det['visual_appearance']})"
                if entry_str not in graft_visuals:
                    graft_visuals.append(entry_str)

    # Check companion['active_grafts'] list
    act_grafts = character_state.get("active_grafts", [])
    if isinstance(act_grafts, list):
        for g_val in act_grafts:
            if g_val:
                g_det = get_item_details(g_val, inventory=inv)
                g_slot = g_val.get("slot", "graft") if isinstance(g_val, dict) else "graft"
                graft_visuals.append(f"{str(g_slot).upper()} GRAFT: {g_det['name']} ({g_det['visual_appearance']})")

    graft_line = f" | ACTIVE GRAFTS: {'; '.join(graft_visuals)}" if graft_visuals else " | ACTIVE GRAFTS: None installed"

    return (
        f"* {name} ({race} {char_class}):\n"
        f"  - Base Physical Appearance: {base_anat}\n"
        f"  - Equipped Gear (MUST BE DEPICTED ACCURATELY): {' | '.join(slot_descriptions)}{graft_line}"
    )


def build_scene_visual_manifest(player_state: dict = None, active_companions: list = None, base_dir: str = None) -> str:
    """
    Builds the complete multi-character Dynamic Equipped-Gear Visual Manifest for the current scene,
    combining the Player's live equipped items/grafts with all active Companions' sheets from Party/*.json.
    """
    import os
    import json
    if base_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    lines = []
    if player_state and isinstance(player_state, dict):
        lines.append(build_character_visual_profile(player_state, entity_id="banki" if player_state.get("name", "").lower() == "banki" else "player"))

    # Determine active companions
    comp_ids = []
    if active_companions:
        for c in active_companions:
            if isinstance(c, dict):
                cid = c.get("id", c.get("entity_id", f"companion_{c.get('name', 'ren').lower()}"))
            else:
                cid = str(c)
                if not cid.startswith("companion_"):
                    cid = f"companion_{cid.lower()}"
            comp_ids.append(cid)
    else:
        # Check player_state['party'] or default to companion_ren
        if player_state and isinstance(player_state, dict):
            party_data = player_state.get("party", {})
            if isinstance(party_data, dict):
                for cname, cdict in party_data.items():
                    if isinstance(cdict, dict) and cdict.get("active", False):
                        cid = cdict.get("id", f"companion_{cname.lower().split()[0]}")
                        comp_ids.append(cid)
        if not comp_ids:
            comp_ids = ["companion_ren"]

    party_dir = os.path.join(base_dir, "Party")
    for cid in comp_ids:
        p_file = os.path.join(party_dir, f"{cid}.json")
        if os.path.exists(p_file):
            try:
                with open(p_file, "r", encoding="utf-8") as f:
                    c_sheet = json.load(f)
                lines.append(build_character_visual_profile(c_sheet, entity_id=cid))
            except Exception:
                pass

    return "\n".join(lines)


# =====================================================================
# PHASE M11: CANONICAL SPELLS, POWERS & FEATS COMPENDIUM
# =====================================================================

CANONICAL_SPELLS_AND_POWERS = {
    "major force missile": {
        "name": "Major Force Missile",
        "category": "Arcane Evocation Spell (Tier 2)",
        "action_type": "Standard Action",
        "cost": "10 Aetheric Flux / Stamina",
        "range": "120 ft",
        "description": (
            "Channels raw condensed kinetic aether through somatic Elder Futhark hand-signs (Algiz-Thurisaz), "
            "condensing ambient mana into three blazing cyan force-projectiles that streak through the air with a "
            "sharp ozone crack and unerringly lock onto the target's vital signature."
        ),
        "mechanics": (
            "• Action: Standard Action (Requires free off-hand for Somatic Casting or Runic Focus)\n"
            "• Resource Cost: 10 Aetheric Flux / Stamina\n"
            "• Range & Targeting: 120 ft; launches 3 bolts that can strike a single target or split across up to 3 targets in line of sight.\n"
            "• Accuracy: Auto-hits visible targets (ignores standard partial cover and Evasion; blocked only by Total Cover or Shield wards).\n"
            "• Damage: 3d4 + 3 + INT mod Force damage (1d4 + 1 per bolt). Deals 100% unreduced damage to incorporeal spirits and heavy constructs, and inflicts 5 pts of Boss Break Gauge stagger."
        )
    },
    "earth tremor hex": {
        "name": "Earth Tremor Hex",
        "category": "Geokinetic / Runic Hex Spell (Tier 2)",
        "action_type": "Standard Action",
        "cost": "15 Aetheric Flux / Stamina",
        "range": "20-ft Radius (Self) or 30-ft Frontal Cone",
        "description": (
            "Decoded from the scorched basalt spell-slate of Silt-Marrow the Unhewn. The caster traces the "
            "subterranean fracture rune (Hagalaz-Uruz) and slams a boot or weapon haft into the floor, sending a "
            "violent seismic shockwave and erupting basalt shards tearing through the ground while binding enemies' feet in heavy gravity."
        ),
        "mechanics": (
            "• Action: Standard Action\n"
            "• Resource Cost: 15 Aetheric Flux / Stamina\n"
            "• Area of Effect: 20-ft radius centered on caster OR 30-ft frontal cone.\n"
            "• Saving Throw: DEX Save (DC = 10 + half Level + INT or WIS mod).\n"
            "• Damage: 2d8 + INT/WIS mod Bludgeoning & Seismic damage (half damage on successful save).\n"
            "• Hex Effect: Targets that fail their save are knocked [Prone] and afflicted with [Seismic Instability] (-2 AC, -10 ft movement speed, and cannot take Reactions for 2 rounds). Cracks the floor into Difficult Terrain for enemies."
        )
    },
    "runic inscription (elder futhark)": {
        "name": "Runic Inscription (Elder Futhark)",
        "category": "Wyrd-Weaver Mystic Feat & Active Power",
        "action_type": "Passive + Bonus Action (Active Etching)",
        "cost": "10 Aetheric Flux / Resonance (Active Etching)",
        "range": "Touch (Equipped Weapon, Armor, or Surface)",
        "description": (
            "Ancient Nordic Wyrd-Weaver mastery over the twenty-four primordial runes of the Elder Futhark. "
            "By tracing incandescent cyan glyphs in the air or carving them directly onto black-iron blades, "
            "leather cuirasses, and dungeon archways, you bind raw cosmic laws directly into physical matter."
        ),
        "mechanics": (
            "• Passive — Somatic Battle-Casting: You can cast somatic arcane and runic spells with one hand while wielding a weapon in your main hand, and gain +2 on all Arcana checks to decipher construct cores, spell slates, and leyline wards.\n"
            "• Active — Runic Etching (Bonus Action, lasts 10 minutes): Inscribe one glowing Elder Futhark rune onto a weapon or armor piece:\n"
            "  1. Thurisaz (Giant's Thorn): Weapon strikes deal +1d6 bonus Force/Lightning damage and bypass 2 points of enemy Armor/DR.\n"
            "  2. Algiz (Elk's Aegis): Inscribed armor grants +2 AC and 25% Resistance to Force and Necrotic damage.\n"
            "  3. Sowilo (Sun's Radiance): Weapon blazes with 30-ft daylight, dealing +1d6 Radiant damage and dispelling darkness."
        )
    },
    # --- 16 STARTING CLASS POWERS ---
    "shield wall stance": {
        "name": "Shield Wall Stance",
        "category": "Warrior Class Stance",
        "action_type": "Bonus Action (Toggle Stance)",
        "cost": "0 Poise (Generates +10 Poise when struck)",
        "range": "Self & Adjacent Allies (5 ft)",
        "description": "Plant your boots into an unyielding frontline bulwark, locking your shield or heavy weapon guard to deflect incoming barrages and protect companions behind you.",
        "mechanics": "• Action: Bonus Action to enter or exit stance.\n• Defensive Bonus: Grants +3 AC and Advantage on CON and STR saving throws against knockdown, push, or stagger.\n• Trade-off & Synergy: Movement speed is halved while active. Adjacent allies behind you gain Half Cover (+2 AC), and every attack you block generates +10 Poise."
    },
    "taunting war-cry": {
        "name": "Taunting War-Cry",
        "category": "Warrior Active Power",
        "action_type": "Bonus Action",
        "cost": "20 Poise",
        "range": "30-ft Radius",
        "description": "Unleash a thunderous, chest-rattling battlefield roar infused with kinetic threat resonance that compels nearby monsters and hostiles to abandon fragile allies and focus their fury on you.",
        "mechanics": "• Action: Bonus Action | Cost: 20 Poise\n• Saving Throw: Hostiles within 30 ft must pass a WIS Save (DC = 10 + half Level + STR or CON mod).\n• Effect: On a failed save, targets are [Taunted] for 2 rounds (forced to target you and suffer Disadvantage on attacks against any other party member)."
    },
    "arcane ward": {
        "name": "Arcane Ward",
        "category": "Mage Defensive Spell",
        "action_type": "Bonus Action or Reaction",
        "cost": "15 Aetheric Flux",
        "range": "Self (or Ally within 30 ft)",
        "description": "Weave an interlocking geometric lattice of shimmering azure mana-hexagons around the body that absorbs kinetic impacts and elemental blasts before shattering cleanly.",
        "mechanics": "• Action: Bonus Action or Reaction when targeted by an attack | Cost: 15 Aetheric Flux\n• Barrier HP: Conjures a temporary Aetheric Ward with HP equal to 25 + (5 × Character Level).\n• Effect: Absorbs all incoming damage until depleted. While the Ward holds, the caster has Advantage on Concentration checks and cannot be afflicted by Bleed."
    },
    "aetheric dart": {
        "name": "Aetheric Dart",
        "category": "Mage Offensive Spell",
        "action_type": "Standard Action",
        "cost": "5 Aetheric Flux",
        "range": "90 ft",
        "description": "Snap a condensed needle of high-velocity crystalline mana from your fingertips or resonator wand that pierces through air and armor seams.",
        "mechanics": "• Action: Standard Action | Cost: 5 Aetheric Flux\n• Attack Roll: Ranged Spell Attack (1d20 + INT mod + Mastery bonus vs Target AC).\n• Damage: Deals 1d8 + INT mod Force damage. On a Critical Hit (19–20), restores 5 Flux and pins the target's aura (-2 Evasion for 1 round)."
    },
    "sanctified ward": {
        "name": "Sanctified Ward",
        "category": "Cleric Aura Stance",
        "action_type": "Bonus Action (Aura Toggle)",
        "cost": "10 Devotion to activate",
        "range": "15-ft Radius Aura",
        "description": "Project a warm, golden halo of consecrated Spire-light across the ground that bolsters allies' resolve and turns aside lethal blows.",
        "mechanics": "• Action: Bonus Action | Area: 15-ft radius centered on you.\n• Aura Effect: You and all allies within 15 ft gain +1 AC and +2 to all Saving Throws.\n• Undead/Corrupt Ward: Aberrant and undead creatures entering the aura suffer -1 to hit."
    },
    "purifying grace": {
        "name": "Purifying Grace",
        "category": "Cleric Healing Prayer",
        "action_type": "Standard Action",
        "cost": "25 Devotion",
        "range": "30 ft",
        "description": "Channel luminous golden restoration into a wounded comrade, knitting torn muscle fibers and burning away biological venom or necrotic rot.",
        "mechanics": "• Action: Standard Action | Cost: 25 Devotion | Range: 30 ft\n• Healing: Restores 2d8 + WIS mod + Level HP to target ally.\n• Cleanse: Immediately removes one [Bleed], [Poisoned], [Burn], or [Weakened] condition."
    },
    "shadow footwork": {
        "name": "Shadow Footwork",
        "category": "Thief Mobility Stance",
        "action_type": "Bonus Action (Stance)",
        "cost": "0 Momentum",
        "range": "Self",
        "description": "Drop into a low, whisper-quiet infiltrator's cadence, gliding across rubble, tripwires, and slick blood without a sound.",
        "mechanics": "• Action: Bonus Action to enter stance.\n• Evasion & Mobility: Grants +2 to Dodge/AC against opportunity attacks, ignores Difficult Terrain movement penalties, and grants +3 to Stealth checks."
    },
    "serrated backstab": {
        "name": "Serrated Backstab",
        "category": "Thief Active Technique",
        "action_type": "Standard Action",
        "cost": "1 Momentum Die",
        "range": "Melee Reach",
        "description": "Exploit a target's blind spot or a companion's distraction to drive a serrated blade deep between armor plates and twist.",
        "mechanics": "• Action: Standard Action | Cost: 1 Momentum Die\n• Condition: Must be in Stealth or flanking the target with an active ally.\n• Damage: Weapon damage + DEX mod + 2d6 Precision Slashing damage, and inflicts [Deep Bleed] (1d4 bleed damage at the start of the target's next 2 turns)."
    },
    "hunter's mark": {
        "name": "Hunter's Mark",
        "category": "Ranger Tracking Power",
        "action_type": "Bonus Action",
        "cost": "1 Focus Charge",
        "range": "90 ft",
        "description": "Lock your predatory ocular focus onto a single quarry, highlighting its heartbeat, arterial weakpoints, and movement trail.",
        "mechanics": "• Action: Bonus Action | Cost: 1 Focus Charge | Duration: Entire encounter.\n• Effect: Your weapon attacks against the marked quarry deal +1d6 bonus Piercing damage and ignore Half/Three-Quarters Cover. You cannot lose track of the target through smoke or darkness."
    },
    "deadeye aim": {
        "name": "Deadeye Aim",
        "category": "Ranger Marksman Passive & Stance",
        "action_type": "Passive / Steady Stance",
        "cost": "Passive (0 Focus)",
        "range": "Weapon Range",
        "description": "Control your breathing and heartbeat until the world slows to a razor-sharp tunnel of ballistic certainty.",
        "mechanics": "• Passive: Ranged weapon attacks ignore partial cover penalties.\n• Steady Aim: If you did not move more than 5 ft this turn, you gain +2 to hit on ranged attacks and expand your Critical Hit range to 19–20."
    },
    "deploy sentry turret": {
        "name": "Deploy Sentry Turret",
        "category": "Engineer Artifice Power",
        "action_type": "Standard Action",
        "cost": "Builds +20 Heat",
        "range": "15 ft Placement (60 ft Turret Firing Range)",
        "description": "Slam a collapsible brass-and-steel clockwork tripod turret onto the field that unfolds with a pneumatic hiss and locks its twin aether-repeaters onto hostiles.",
        "mechanics": "• Action: Standard Action | Heat Generated: +20 Heat\n• Turret Stats: HP = 20 + (5 × Level), AC 15. Lasts for the encounter or until destroyed.\n• Autonomous Fire: At the end of each of your turns, the turret automatically fires at the nearest hostile within 60 ft for 1d6 + INT mod Piercing/Lightning damage."
    },
    "vent overclock": {
        "name": "Vent Overclock",
        "category": "Engineer Thermal Blast",
        "action_type": "Standard Action or Bonus Action",
        "cost": "Vents 100% of current Heat",
        "range": "15-ft Frontal Cone",
        "description": "Pop the emergency exhaust valves on your rig and weapon coils, unleashing a searing directional blast of superheated pressurized steam.",
        "mechanics": "• Action: Standard Action | Cost: Consumes all accumulated Heat (resets Heat to 0).\n• Damage: Deals Fire/Steam damage in a 15-ft cone equal to 50% of vented Heat (minimum 2d6 Fire damage; DEX Save DC 14 for half).\n• Secondary Effect: Obscures the cone in dense white steam for 1 round, granting Concealment (+2 AC) to allies."
    },
    "kinetic repulsion barrier": {
        "name": "Kinetic Repulsion Barrier",
        "category": "Psion Telekinetic Stance",
        "action_type": "Bonus Action",
        "cost": "+10% Psi-Strain per turn",
        "range": "Self",
        "description": "Surround yourself with a shimmering, high-density telekinetic pressure shell that bends incoming arrows, bolts, and shrapnel away from your body.",
        "mechanics": "• Action: Bonus Action | Cost: Builds +10% Psi-Strain per active turn.\n• Defense: Grants +3 AC against all ranged attacks and reduces incoming bludgeoning/slashing damage by 3.\n• Repulsion: Melee attackers striking you must pass a DC 13 STR save or be pushed back 5 ft."
    },
    "mind spike": {
        "name": "Mind Spike",
        "category": "Psion Psychic Power",
        "action_type": "Standard Action",
        "cost": "+15% Psi-Strain",
        "range": "60 ft",
        "description": "Drive an invisible, needle-sharp lance of pure phrenic dissonance directly into an enemy's cerebral cortex or cognitive matrix.",
        "mechanics": "• Action: Standard Action | Cost: Builds +15% Psi-Strain | Range: 60 ft\n• Saving Throw: INT or WIS Save (DC = 10 + half Level + INT mod), bypassing physical Armor Class completely.\n• Damage & Effect: Deals 1d10 + INT mod Psychic/Force damage and inflicts [Rattled] (-2 on the target's next attack roll or save)."
    },
    "adaptive weapon mastery": {
        "name": "Adaptive Weapon Mastery",
        "category": "Pathless Anomaly Feat",
        "action_type": "Passive",
        "cost": "Passive (No Cost)",
        "range": "Self",
        "description": "Your neural link to the Cardinal System bypasses rigid class weapon locks, allowing effortless mastery of any blade, axe, hammer, bow, or magetech firearm.",
        "mechanics": "• Passive: Equip and dual-wield any weapon combination without off-hand attack penalties.\n• Mastery Synergy: Weapon skill mastery gains are increased by +15%, and you add +1 to hit when switching weapon types mid-encounter."
    },
    "unshackled potential": {
        "name": "Unshackled Potential",
        "category": "Pathless Anomaly Power",
        "action_type": "Passive + Free Action (1/Encounter)",
        "cost": "20 Anomaly Resonance (Active Surge)",
        "range": "Self",
        "description": "As an unregistered anomaly outside the Architects' templates, you can weave martial strikes, somatic spells, and survivor ingenuity into a single unbroken flow.",
        "mechanics": "• Passive: Can learn and slot spells, sword skills, and feats from any of the 7 anchor classes without restriction.\n• Active — Anomaly Surge (Free Action, 20 Resonance): Add +1d6 bonus damage or +3 to any single attack roll, spell cast, or saving throw."
    },
    "iron grip": {
        "name": "Iron Grip",
        "category": "Vanguard Combat Feat",
        "action_type": "Passive",
        "cost": "Passive",
        "range": "Self",
        "description": "Conditioned forearm tendons and unyielding grip strength allow you to wield massive war-axes and trench hammers without recoil.",
        "mechanics": "• Passive: Immune to being disarmed. Grants +2 on STR checks to grapple, shove, or wrench weapons from enemies, and +1 damage on heavy melee swings."
    },
    "berserk fury": {
        "name": "Berserk Fury",
        "category": "Nordic Berserker Power",
        "action_type": "Bonus Action",
        "cost": "25 Poise / Stamina (1/Encounter)",
        "range": "Self",
        "description": "Ignite your blood-rage and ancestral Nordic fury, shrugging off pain as crimson-and-cyan battle-aura flares around your shoulders.",
        "mechanics": "• Action: Bonus Action | Duration: 3 rounds\n• Effect: Gain +3 bonus damage on all melee axe/hammer attacks, Resistance (25% reduction) to physical bludgeoning/slashing/piercing damage, and immunity to Fear."
    },
    "cleave": {
        "name": "Cleave",
        "category": "Axe Sword Skill",
        "action_type": "Standard Action / Trigger",
        "cost": "10 Stamina / Poise",
        "range": "Melee Reach (5 ft)",
        "description": "Carry the brutal momentum of a heavy axe swing straight through one enemy and into an adjacent foe.",
        "mechanics": "• Trigger / Action: When your melee axe strike reduces an enemy to 0 HP or scores a Critical Hit, or by spending 10 Poise/Stamina on a Standard Action swing, immediately make a secondary cleave attack against an adjacent enemy within 5 ft for 1d8 + STR slashing damage."
    },
    "berserk cleave": {
        "name": "Berserk Cleave",
        "category": "Nordic Berserker Sword Skill",
        "action_type": "Standard Action",
        "cost": "20 Poise / Stamina",
        "range": "Melee Reach (180° Frontal Arc)",
        "description": "Unleash a ferocious wide-arcing axe sweep that carves through every hostile standing in your frontal engagement zone.",
        "mechanics": "• Action: Standard Action | Cost: 20 Poise / Stamina\n• Effect: Make a melee attack against up to 3 adjacent enemies in a frontal arc, dealing full weapon damage + STR mod + 1d6 slashing damage and inflicting [Bleed] on targets that fail a DC 13 CON save."
    }
}


def get_spell_or_power_details(entry, player_state: dict = None) -> dict:
    """
    Resolves full metadata (`name`, `category`, `action_type`, `cost`, `range`, `description`, `mechanics`)
    for any Spell, Power, Sword Skill, Class Feat, Racial Ability, Vocation Perk, or Fused Technique.
    Guarantees every spell or power can be clicked and expanded in the UI to show both its
    narrative description and exact game mechanics.
    """
    if isinstance(entry, dict):
        if entry.get("tier") == "Fused" or entry.get("skill_key"):
            raw_name = str(entry.get("skill_key") or f"[Fusion] {entry.get('name', 'Convergence')}").strip()
            existing_cat = "Fused Convergence Skill (Rule 10)"
        else:
            raw_name = str(entry.get("name", entry.get("title", "Unknown Power"))).strip()
            existing_cat = str(entry.get("category", entry.get("type", "Spell / Power"))).strip()
        existing_desc = str(entry.get("description", entry.get("desc", ""))).strip()
        existing_mech = str(entry.get("mechanics", entry.get("effect", ""))).strip()
        existing_act = str(entry.get("action_type", "Standard Action")).strip()
        existing_cost = str(entry.get("cost", "20 Combat Resource / Stamina")).strip()
        existing_rng = str(entry.get("range", "Hybrid Combat Range")).strip()
        if existing_desc and existing_mech:
            return {
                "name": raw_name,
                "category": existing_cat,
                "action_type": existing_act,
                "cost": existing_cost,
                "range": existing_rng,
                "description": existing_desc,
                "mechanics": existing_mech
            }
    else:
        raw_str = str(entry or "").strip()
        # Strip surrounding brackets like "[Aether-Burst Convergence]" unless it is a "[Fusion] ..." prefix
        if raw_str.startswith("[") and raw_str.endswith("]") and not raw_str.lower().startswith("[fusion]"):
            raw_str = raw_str[1:-1].strip()
        raw_name = raw_str
        existing_desc = ""
        existing_mech = ""
        existing_cat = ""

    if not raw_name:
        return {
            "name": "Unknown Power",
            "category": "Power",
            "action_type": "Passive",
            "cost": "None",
            "range": "Self",
            "description": "An uncatalogued anomaly power.",
            "mechanics": "Consult the GM for situational resolution."
        }

    # Check if raw_name has inline "Name: Description" or "Name (Type): Mechanics"
    inline_type = ""
    inline_body = ""
    clean_lookup_name = raw_name
    if ":" in raw_name:
        head_part, body_part = raw_name.split(":", 1)
        inline_body = body_part.strip()
        if "(" in head_part and ")" in head_part:
            base_n, paren_part = head_part.split("(", 1)
            clean_lookup_name = base_n.strip()
            inline_type = paren_part.rstrip(")").strip()
        else:
            clean_lookup_name = head_part.strip()

    norm_full = raw_name.lower().strip()
    norm_clean = clean_lookup_name.lower().strip()

    # 1. Exact or normalized match in CANONICAL_SPELLS_AND_POWERS
    for cand in (norm_full, norm_clean):
        if cand in CANONICAL_SPELLS_AND_POWERS:
            return copy.deepcopy(CANONICAL_SPELLS_AND_POWERS[cand])

    # 2. Substring match in CANONICAL_SPELLS_AND_POWERS
    for k, sp_data in CANONICAL_SPELLS_AND_POWERS.items():
        if k in norm_full or norm_clean == k:
            return copy.deepcopy(sp_data)

    # 3. Search CANONICAL_MILESTONES (all 1-1000 Skill Milestone Sword Skills & Feats)
    for skill_k, tiers_dict in CANONICAL_MILESTONES.items():
        for thresh, m_data in tiers_dict.items():
            m_name = m_data["name"]
            if m_name.lower() == norm_clean or m_name.lower() in norm_full:
                is_active = "active" in m_data.get("type", "").lower() or m_data.get("target_slot") == "spells"
                return {
                    "name": m_name,
                    "category": f"{skill_k} {m_data.get('tier', '')} {m_data.get('type', 'Milestone Power')} (Mastery {thresh})".strip(),
                    "action_type": "Standard Action (Sword Skill / Technique)" if is_active else "Passive Mastery Perk",
                    "cost": "15 Stamina / Combat Resource" if is_active else "Passive (Always Active)",
                    "range": "Combat Reach / Area",
                    "description": m_data.get("description", f"{skill_k} milestone technique unlocked at {thresh} Mastery."),
                    "mechanics": f"• Unlock Source: {skill_k} Mastery {thresh} ({m_data.get('tier', 'Milestone')})\n• Game Mechanics: {m_data.get('effect', '')}"
                }

    # 4. Search CLASS_FEATS_TREE (all 8 classes x Levels 1, 3, 6, 10)
    for cls_k, cls_data in CLASS_FEATS_TREE.items():
        res_name = cls_data.get("resource", {}).get("name", "Combat Resource")
        # Check Level 1 strings
        for l1_str in cls_data.get("level_1", []):
            l1_base = l1_str.split("(")[0].split(":")[0].strip()
            if l1_base.lower() == norm_clean or l1_base.lower() in norm_full:
                mech_part = l1_str.split(":", 1)[1].strip() if ":" in l1_str else l1_str
                act_part = l1_str.split("(")[1].split(")")[0].strip() if "(" in l1_str and ")" in l1_str else "Active / Passive"
                return {
                    "name": l1_base,
                    "category": f"{cls_data.get('title', cls_k.title())} Level 1 Power",
                    "action_type": act_part,
                    "cost": f"Uses {res_name}",
                    "range": "Combat Range",
                    "description": f"Core doctrine ability of the {cls_data.get('title', cls_k.title())}, channeling {res_name} in combat.",
                    "mechanics": f"• Class Doctrine: {cls_data.get('title', cls_k.title())}\n• Action Type: {act_part}\n• Game Mechanics: {mech_part}"
                }
        # Check Level 3, 6, 10 dicts
        for lvl_key in ("level_3", "level_6", "level_10"):
            lvl_num = lvl_key.split("_")[1]
            for f_dict in cls_data.get(lvl_key, []):
                f_name = f_dict.get("name", "")
                if f_name.lower() == norm_clean or f_name.lower() in norm_full:
                    f_type = f_dict.get("type", "Active")
                    return {
                        "name": f_name,
                        "category": f"{cls_data.get('title', cls_k.title())} Level {lvl_num} {f_type} Power",
                        "action_type": f"{f_type} Action" if f_type != "Passive" else "Passive",
                        "cost": f"Uses {res_name}" if f_type != "Passive" else "Passive (Always Active)",
                        "range": "Combat Range",
                        "description": f"Advanced Tier {lvl_num} {cls_data.get('title', cls_k.title())} technique ({f_name}).",
                        "mechanics": f"• Class Tier: Level {lvl_num} {cls_data.get('title', cls_k.title())} ({f_type})\n• Game Mechanics: {f_dict.get('desc', '')}"
                    }

    # 5. Check player_state['fused_abilities'] if available
    if isinstance(player_state, dict):
        for fa in player_state.get("fused_abilities", []):
            if isinstance(fa, dict):
                fa_name = fa.get("name", "")
                fa_skill_key = fa.get("skill_key") or (fa_name if fa_name.lower().startswith("[fusion]") else f"[Fusion] {fa_name}")
                if (
                    (fa_name and (fa_name.lower() == norm_clean or fa_name.lower() in norm_full))
                    or (fa_skill_key and (fa_skill_key.lower() == norm_clean or fa_skill_key.lower() == norm_full))
                ):
                    comps = " + ".join(fa.get("components", []))
                    return {
                        "name": fa_skill_key,
                        "category": "Fused Convergence Skill (Rule 10)",
                        "action_type": "Standard Action",
                        "cost": "20 Combat Resource / Stamina",
                        "range": "Hybrid Combat Range",
                        "description": fa.get("description", f"Synergistic fusion of {comps} forged in the Cardinal Ability Fusion Chamber."),
                        "mechanics": fa.get("mechanics") or (
                            f"• Fusion Components: {comps}\n"
                            f"• Power Rating: Tier {fa.get('power_rating', 3)} Fused Technique\n"
                            f"• Game Mechanics: Combines the primary effects of [{comps}] into a single Standard Action strike/cast with a +2 Synergy bonus to hit/DC and +1d8 bonus resonance damage."
                        )
                    }

    # 6. Search RACIAL_LINEAGES & EARTH_VOCATIONS in character_generator
    try:
        import backend.character_generator as cg
        for r_key, r_data in getattr(cg, "RACIAL_LINEAGES", {}).items():
            for rab in r_data.get("racial_abilities", []):
                rab_head = rab.split(":", 1)[0].strip()
                rab_body = rab.split(":", 1)[1].strip() if ":" in rab else rab
                if rab_head.lower() == norm_clean or rab_head.lower() in norm_full:
                    is_flaw = "flaw" in rab_head.lower()
                    return {
                        "name": rab_head,
                        "category": f"{r_data['name']} Lineage {'Flaw' if is_flaw else 'Power'}",
                        "action_type": "Passive / Innate Trait" if is_flaw or "passive" in rab_body.lower() else "Innate Lineage Power",
                        "cost": "Innate / 1 per Rest (if active)",
                        "range": "Self / Lineage Range",
                        "description": f"Genetic/Aetheric lineage trait of the {r_data['name']} ({r_data.get('genre', 'Crucible')}): {r_data.get('desc', '')}",
                        "mechanics": f"• Lineage Source: {r_data['name']}\n• Game Mechanics: {rab_body}"
                    }
        for v_key, v_data in getattr(cg, "EARTH_VOCATIONS", {}).items():
            perk_str = v_data.get("innate_perk", "")
            if perk_str:
                p_head = perk_str.split("(")[0].split(":")[0].strip()
                p_body = perk_str.split(":", 1)[1].strip() if ":" in perk_str else perk_str
                if p_head.lower() == norm_clean or p_head.lower() in norm_full:
                    return {
                        "name": p_head,
                        "category": f"Pre-Integration Vocation Perk ({v_data['title']})",
                        "action_type": "Passive",
                        "cost": "Passive (Always Active)",
                        "range": "Self",
                        "description": f"Retained Earth expertise from serving as a {v_data['title']}: {v_data.get('description', '')}",
                        "mechanics": f"• Vocation Origin: {v_data['title']}\n• Game Mechanics: {p_body}"
                    }
    except Exception:
        pass

    # 7. Check if this is an item/trophy feat (like "Dire-Wolf Fur Mantle")
    if norm_clean in CANONICAL_ITEM_CATALOG:
        cat_item = CANONICAL_ITEM_CATALOG[norm_clean]
        return {
            "name": cat_item["name"],
            "category": "Relic / Mantle Passive Power",
            "action_type": "Passive (While Equipped)",
            "cost": "Passive",
            "range": "Self",
            "description": cat_item.get("visual_appearance", cat_item.get("desc", "")),
            "mechanics": f"• Equipment Perk: {cat_item.get('desc', '')}"
        }

    # 8. Intelligent Fallback Parser / Synthesizer for custom or emergent Spells & Powers
    if inline_body:
        act_str = inline_type if inline_type else ("Passive" if "passive" in inline_body.lower() else "Standard Action / Active")
        return {
            "name": clean_lookup_name,
            "category": existing_cat or ("Passive Feat" if "passive" in act_str.lower() else "Active Spell / Power"),
            "action_type": act_str,
            "cost": "Passive (No Cost)" if "passive" in act_str.lower() else "10–20 Combat Resource / Stamina",
            "range": "Self / Combat Range",
            "description": existing_desc or f"Awakened ability [{clean_lookup_name}] manifested within the Fractured Overlay.",
            "mechanics": f"• Action Type: {act_str}\n• Game Mechanics: {inline_body}"
        }

    # Keyword-driven synthesis if only a bare name was provided
    low = norm_clean
    if any(w in low for w in ["missile", "bolt", "dart", "blast", "lance", "hex", "spell", "fire", "frost", "lightning", "arcane", "aether", "rune", "runic"]):
        return {
            "name": clean_lookup_name,
            "category": "Arcane / Runic Spell",
            "action_type": "Standard Action",
            "cost": "10–15 Aetheric Flux / Mana",
            "range": "60–120 ft",
            "description": existing_desc or f"An arcane or runic spell ({clean_lookup_name}) woven from ambient leyline energy and somatic gestures.",
            "mechanics": existing_mech or (
                f"• Action: Standard Action | Cost: 10–15 Aetheric Flux\n"
                f"• Resolution: Ranged Spell Attack (1d20 + INT/WIS mod + Arcana Mastery bonus) or Saving Throw (DC = 10 + half Level + INT/WIS mod).\n"
                f"• Effect: Inflicts 2d8 + INT/WIS mod elemental/force damage or applies its thematic runic status condition."
            )
        }
    else:
        return {
            "name": clean_lookup_name,
            "category": existing_cat or "Combat Power & Feat",
            "action_type": "Active Maneuver / Passive Perk",
            "cost": "10–15 Stamina / Combat Resource (if active)",
            "range": "Melee / Tactical Range",
            "description": existing_desc or f"Specialized combat power or character feat ({clean_lookup_name}) honed through survival in the Crucible.",
            "mechanics": existing_mech or (
                f"• Activation: Grants a +2 tactical bonus on relevant combat checks or unleashes a specialized strike dealing weapon damage + 1d6 bonus damage."
            )
        }


def get_all_player_spells_and_powers(player_state: dict) -> list[dict]:
    """
    Collects, deduplicates, and enriches all Spells, Active Techniques, Feats/Powers,
    Racial Lineage Abilities, and Fused Techniques on `player_state`.
    Returns a list of enriched dicts ready to render as individual clickable & expandable
    entries in the `🔮 Spells & Powers` HUD menu.
    """
    if not isinstance(player_state, dict):
        return []

    results = []
    seen_names = set()
    slotted_list = [s.lower() for s in get_slotted_abilities(player_state)]

    def _add_entry(raw_item, source_group: str, icon: str):
        details = get_spell_or_power_details(raw_item, player_state=player_state)
        norm_n = details["name"].strip().lower()
        if not norm_n or norm_n in seen_names:
            return
        seen_names.add(norm_n)
        details["source_group"] = source_group
        details["icon"] = icon
        details["is_slotted"] = any(norm_n == s or norm_n in s or s in norm_n for s in slotted_list)
        results.append(details)

    # 1. Spells & Active Sword Skills
    for sp in player_state.get("spells", []):
        if sp:
            _add_entry(sp, "Spell / Active Technique", "🔮")

    # 2. Feats & Class Powers
    for ft in player_state.get("feats", []):
        if ft:
            _add_entry(ft, "Power / Feat", "⚡")

    # 3. Racial Lineage Powers
    for ra in player_state.get("racial_abilities", []):
        if ra:
            _add_entry(ra, "Lineage Power", "🧬")

    # 4. Fused Abilities (if any not already in feats/spells)
    for fa in player_state.get("fused_abilities", []):
        if fa:
            _add_entry(fa, "Fused Convergence", "✨")

    return results




