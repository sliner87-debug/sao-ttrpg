"""
Mechanics Engine for The Fractured Overlay (SAO TTRPG)
Handles mathematical crunch, dice logic, encumbrance physics, and equipment state.
"""

import math

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
    "scrap": 1.0
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
        if "weight" in item and item["weight"] is not None:
            try:
                return round(float(item["weight"]) * qty, 1)
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
    
    max_weight = round(str_val * 15.0, 1)
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
        # Stacking slots: each entry takes 1 slot, or 1 slot per 5 units for small items
        qty = item.get("qty", 1) if isinstance(item, dict) else 1
        slots_taken = max(1, math.ceil(qty / 5)) if w < 2.0 else qty
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
    """Calculates Armor Class based on DEX, equipped armor, durability state, and encumbrance penalties."""
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
    
    # Golem-Grafts AC Bonus
    graft_ac_bonus = 0
    installed_grafts = player_state.get("graft_system", {}).get("installed_grafts", {})
    if isinstance(installed_grafts, dict) and "dermal" in installed_grafts:
        if installed_grafts["dermal"].get("key") == "subdermal_carapace_weave":
            graft_ac_bonus += 2
            
    ac_pen = dur_pens.get("ac_penalty", 0)
    return max(10, base_ac + armor_bonus + shield_bonus + graft_ac_bonus - ac_pen)



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
            "max": max_d,
            "loss": amount,
            "state": state_info["state"],
            "is_broken": state_info["is_broken"],
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
                "max": max_d,
                "loss": amount,
                "state": state_info["state"],
                "is_broken": state_info["is_broken"],
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
        items_to_add.extend(pool[:2])
    elif total_roll >= 10:
        # Standard salvage: 1 item
        items_to_add.append(pool[0])
    else:
        # Low roll: basic scrap
        items_to_add.append({"name": "Tainted Metallic Scrap", "qty": 1, "weight": 1.0})

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
            inv.append({"name": item["name"], "qty": item["qty"], "rarity": "Common", "durability": 100, "max_durability": 100, "desc": "Field salvaged component."})
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
    }
}

BODY_GRAFT_SLOTS = ["arm_left", "arm_right", "leg_left", "leg_right", "spine", "ocular", "dermal", "neural"]

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

def get_max_graft_strain(player_state):
    """
    Max Graft Capacity = (CON * 2) + (Level * 3).
    """
    stats = player_state.get("stats", {})
    con_val = stats.get("CON", 10)
    level_val = player_state.get("level", 1)
    return (con_val * 2) + (level_val * 3)

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

def install_graft(player_state, graft_key, body_slot, surgeon_fee_col=None):
    """
    Surgically installs a Golem-Graft into a designated body slot during safe-zone clinic downtime.
    """
    if graft_key not in CANONICAL_GRAFTS:
        return {"success": False, "message": f"Unknown graft key '{graft_key}'."}

    graft_def = CANONICAL_GRAFTS[graft_key]

    if body_slot not in BODY_GRAFT_SLOTS:
        return {"success": False, "message": f"Invalid body slot '{body_slot}'."}

    if body_slot not in graft_def["allowed_slots"]:
        allowed_str = ", ".join(graft_def["allowed_slots"])
        return {"success": False, "message": f"{graft_def['name']} can only be installed in: {allowed_str}."}

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
        return {"penalty": 0, "net_grafts": 0, "harmonized": 0}

    installed = player_state.get("graft_system", {}).get("installed_grafts", {})
    count = len(installed)

    if count == 0:
        return {"penalty": 0, "net_grafts": 0, "harmonized": 0}

    # Check for harmonization feats / spinal conduit
    harmonized = 0
    feats = [str(f).lower() for f in player_state.get("feats", [])]
    if any("leyline conduit" in f for f in feats):
        harmonized += 1

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
# ABILITY & SPELL SLOTTING / MATRIX MEMORY ENGINE
# =====================================================================

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
        "name": "Overwatch Hacking",
        "label": "📡 Overwatch Hacking",
        "icon": "📡",
        "short_desc": "Scans enemy geometry and debug hitboxes via terminal.",
        "tactical_effect": "Debuffs targeted enemy AC by -2 and reveals hidden vulnerabilities.",
        "combat_log_tag": "[REN OVERWATCH]",
        "stat_bonus": {"target_ac_mod": -2, "crit_threat_bonus": 1}
    },
    "suppression_fire": {
        "key": "suppression_fire",
        "name": "Suppression Fire",
        "label": "⚡ Suppression Fire",
        "icon": "⚡",
        "short_desc": "Lays down non-lethal electrical stun bursts with corporate pistol.",
        "tactical_effect": "Enemies rushing into melee must make a DC 13 CON save or become Staggered.",
        "combat_log_tag": "[REN SUPPRESSION]",
        "stat_bonus": {"disruption_dc": 13, "condition": "Staggered"}
    },
    "full_evasion": {
        "key": "full_evasion",
        "name": "Full Evasion / Hide",
        "label": "🛡️ Full Evasion / Hide",
        "icon": "🛡️",
        "short_desc": "Takes complete cover behind collision meshes and debris.",
        "tactical_effect": "Ren is immune to single-target attacks; +4 to all defensive saves.",
        "combat_log_tag": "[REN EVASION]",
        "stat_bonus": {"defense_save_bonus": 4, "untargetable": True}
    },
    "utility_rigging": {
        "key": "utility_rigging",
        "name": "Utility & Rigging",
        "label": "🔧 Utility & Rigging",
        "icon": "🔧",
        "short_desc": "Deploys field snares, repairs gear, or harvests combat scrap.",
        "tactical_effect": "Restores +15 gear durability to worn weapon/armor or scavenges +1 extra crafting part.",
        "combat_log_tag": "[REN UTILITY]",
        "stat_bonus": {"durability_patch": 15, "salvage_bonus": 1}
    }
}

COMPANION_LEVEL_PERKS = {
    2: {
        "name": "Telemetry Ping v1.0",
        "type": "Passive",
        "desc": "+1 to Banki's attack rolls against scanned targets."
    },
    3: {
        "name": "Mesh Exploitation Mastery",
        "type": "Technique",
        "desc": "Ren can hack local safe-zone dispensers and reveal hidden doors."
    },
    4: {
        "name": "Aetheric Shield Pulse",
        "type": "Reaction",
        "desc": "When Banki takes lethal damage, Ren emits a kinetic pulse granting +20 temporary HP."
    },
    5: {
        "name": "Overclocked Stun Burst",
        "type": "Active",
        "desc": "Pistol EMP charge jumps to 2 additional adjacent targets."
    },
    6: {
        "name": "Geometry Desync Hack",
        "type": "Ultimate",
        "desc": "Freezes 1 construct's collision mesh for 1 turn, completely immobilizing it."
    }
}

def get_default_ren_companion():
    """
    Returns the canonical companion profile for Ren Sasaki.
    """
    return {
        "name": "Ren Sasaki",
        "title": "Junior Environment QA / Magi-Tech Hacker",
        "level": 3,
        "xp": 450,
        "next_level_xp": 900,
        "hp": 35,
        "max_hp": 35,
        "stance": "overwatch_hacking",
        "morale": "Steady",
        "loadout": {
            "main_hand": "Corporate Stun-Pistol (Non-Lethal EMP)",
            "tool": "Cracked QA Slate / Mesh Terminal",
            "deck": "Cracked QA Slate / Mesh Terminal",
            "armor": "Threadbare Corporate Hoodie (DR 1)",
            "chest": "Threadbare Corporate Hoodie (DR 1)"
        },
        "equipped": {
            "main_hand": "Corporate Stun-Pistol (Non-Lethal EMP)",
            "tool": "Cracked QA Slate / Mesh Terminal",
            "deck": "Cracked QA Slate / Mesh Terminal",
            "armor": "Threadbare Corporate Hoodie (DR 1)",
            "chest": "Threadbare Corporate Hoodie (DR 1)"
        },
        "skills": {
            "Mesh Exploitation": {
                "mastery": 140,
                "tier": "Journeyman",
                "description": "Exploiting collision leaks and debug boundaries.",
                "milestones_unlocked": ["Logic Buffer Exploit"]
            },
            "Stun-Pistol Marksmanship": {
                "mastery": 45,
                "tier": "Novice",
                "description": "Aiming non-lethal electrical stun charges at close range.",
                "milestones_unlocked": []
            },
            "Diagnostic Triage": {
                "mastery": 60,
                "tier": "Apprentice",
                "description": "Rapid patching of bio-signatures and status ailments.",
                "milestones_unlocked": ["Patch Script v1.0"]
            }
        },
        "abilities": [
            "Overwatch Weakpoint Scan (-2 Enemy AC)",
            "Suppression Stun Burst (DC 13 CON save vs Stun)",
            "Emergency Collision Phasing (Immune 1 turn)",
            "Scavenge Optimization (+25% salvage yield)"
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
    ren.setdefault("title", "Junior Environment QA / Magi-Tech Hacker")
    ren.setdefault("level", 3)
    ren.setdefault("xp", 450)
    ren.setdefault("next_level_xp", ren.get("level", 3) * 300)
    ren.setdefault("hp", 35)
    ren.setdefault("max_hp", 35)
    ren.setdefault("stance", "overwatch_hacking")
    ren.setdefault("morale", "Steady")
    ren.setdefault("loadout", {
        "main_hand": "Corporate Stun-Pistol (Non-Lethal EMP)",
        "tool": "Cracked QA Slate / Mesh Terminal",
        "deck": "Cracked QA Slate / Mesh Terminal",
        "armor": "Threadbare Corporate Hoodie (DR 1)",
        "chest": "Threadbare Corporate Hoodie (DR 1)"
    })
    ren.setdefault("equipped", ren.get("loadout", {
        "main_hand": "Corporate Stun-Pistol (Non-Lethal EMP)",
        "tool": "Cracked QA Slate / Mesh Terminal",
        "deck": "Cracked QA Slate / Mesh Terminal",
        "armor": "Threadbare Corporate Hoodie (DR 1)",
        "chest": "Threadbare Corporate Hoodie (DR 1)"
    }))
    if isinstance(ren.get("equipped"), dict):
        ren["equipped"].setdefault("deck", ren["equipped"].get("tool", "Cracked QA Slate / Mesh Terminal"))
        ren["equipped"].setdefault("chest", ren["equipped"].get("armor", "Threadbare Corporate Hoodie (DR 1)"))
    ren.setdefault("skills", {
        "Mesh Exploitation": {"mastery": 140, "tier": "Journeyman", "description": "Exploiting collision leaks.", "milestones_unlocked": ["Logic Buffer Exploit"]},
        "Stun-Pistol Marksmanship": {"mastery": 45, "tier": "Novice", "description": "Electrical stun charges.", "milestones_unlocked": []},
        "Diagnostic Triage": {"mastery": 60, "tier": "Apprentice", "description": "Patching bio-signatures.", "milestones_unlocked": ["Patch Script v1.0"]}
    })
    ren.setdefault("abilities", [
        "Overwatch Weakpoint Scan (-2 Enemy AC)",
        "Suppression Stun Burst (DC 13 CON save vs Stun)",
        "Emergency Collision Phasing (Immune 1 turn)",
        "Scavenge Optimization (+25% salvage yield)"
    ])

    return companions

def get_companion_stances():
    """Returns available tactical stances for companions."""
    return COMPANION_TACTICAL_STANCES

def get_companion(player_state, companion_name="Ren"):
    """Safely retrieves a companion profile."""
    companions = ensure_companion_profile(player_state)
    return companions.get(companion_name, companions.get("Ren", get_default_ren_companion()))

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

    companions = ensure_companion_profile(player_state)
    comp = companions.get(companion_name)
    if not comp:
        # Check if companion_name was actually the stance
        if companion_name in COMPANION_TACTICAL_STANCES:
            comp = companions.get("Ren")
            stance_key = companion_name
        else:
            return {"success": False, "message": f"Companion '{companion_name}' not found."}

    norm_str = str(stance_key).strip().lower()
    matched_key = None
    if any(w in norm_str for w in ["overwatch", "hack", "scan"]):
        matched_key = "overwatch_hacking"
    elif any(w in norm_str for w in ["suppress", "stun", "burst", "pistol"]):
        matched_key = "suppression_fire"
    elif any(w in norm_str for w in ["evasion", "evade", "hide", "cover"]):
        matched_key = "full_evasion"
    elif any(w in norm_str for w in ["utility", "rig", "repair", "patch", "scavenge"]):
        matched_key = "utility_rigging"

    if not matched_key:
        norm_clean = norm_str.replace(" ", "_").replace("-", "_")
        for k in COMPANION_TACTICAL_STANCES:
            if k == norm_clean or norm_clean in k or k in norm_clean:
                matched_key = k
                break

    if not matched_key:
        return {"success": False, "message": f"Unknown tactical stance '{stance_key}'."}

    stance_def = COMPANION_TACTICAL_STANCES[matched_key]
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
            "target_ac_mod": -2,
            "tag": stance_info["combat_log_tag"],
            "log": f"{stance_info['combat_log_tag']} Scans enemy hitbox topology: -2 AC debuff applied to primary target."
        }
    elif stance_key == "suppression_fire":
        return {
            "stance": stance_key,
            "dc": 13,
            "condition": "Staggered",
            "tag": stance_info["combat_log_tag"],
            "log": f"{stance_info['combat_log_tag']} Fires non-lethal electrical stun burst! Target DC 13 CON save vs Staggered."
        }
    elif stance_key == "full_evasion":
        return {
            "stance": stance_key,
            "untargetable": True,
            "tag": stance_info["combat_log_tag"],
            "log": f"{stance_info['combat_log_tag']} Ren takes cover behind collision mesh; immune to targeted single-target attacks."
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
        msg = f"{stance_info['combat_log_tag']} Field patches {patch_item} (+15 durability restored)." if patched else f"{stance_info['combat_log_tag']} Scavenges +1 extra titanium scrap from combat debris."
        return {
            "stance": stance_key,
            "patched": patched,
            "tag": stance_info["combat_log_tag"],
            "log": msg
        }

    return {"stance": "unknown", "log": "[REN: Observing situation.]"}


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



