"""
backend/psionics_dsp.py
=======================
Complete Psionics Subsystem for Fractured Earth SAO Sandbox V2:
- D&D 3.5 Expanded Psionics Handbook (XPH) + Errata:
  * Power Point (PP) Progression Engine & Key Ability Bonus PP
  * The Golden Rule of Psionics: Strict Manifester Level (ML) spend cap on powers & augments
  * Psionic Focus & Meditation Engine (DC 20 Concentration / Meditation)
  * Soulknife Mind Blade Manifestation, Shaping & Psychic Strike
  * Wilder Wild Surge, Psychic Enervation & Surging Euphoria
- Dreamscarred Press (DSP) Psionics (Psionics Unleashed, Psionics Expanded, Ultimate Psionics):
  * Aegis Astral Suit Customization Engine (Skin, Armor, Juggernaut + Customization Points)
  * The Collective Network Engine (Vitalist & Tactician: mental mesh, Transfer Wounds, Spirit of Many)
  * Cryptic Pattern Disruption & Dread Aura of Terror
"""

import copy
import random
from typing import Dict, List, Optional, Tuple, Any


# =====================================================================
# 1. POWER POINT (PP) ENGINE & MANIFESTER LEVEL RULES
# =====================================================================

# Full Manifester Base PP table (Levels 1-20 from XPH Table 2-1)
# Levels 21-100 extrapolate smoothly using the canonical epic psionics progression (+17 to +30 PP/lvl)
FULL_MANIFESTER_PP_TABLE = [
    0,     # Level 0
    2, 6, 11, 17, 25, 35, 46, 58, 72, 88,          # L1 - L10
    106, 126, 147, 170, 195, 221, 250, 280, 311, 343  # L11 - L20
]
# Expand up to Level 100
for _lvl in range(21, 101):
    _prev = FULL_MANIFESTER_PP_TABLE[-1]
    _gain = 33 + ((_lvl - 20) * 2)  # Epic progression
    FULL_MANIFESTER_PP_TABLE.append(_prev + _gain)

# Partial Manifester Base PP table (Psychic Warrior XPH Table 2-3)
PARTIAL_MANIFESTER_PP_TABLE = [
    0,     # Level 0
    0, 1, 3, 6, 10, 15, 21, 28, 36, 45,            # L1 - L10
    55, 66, 78, 91, 105, 120, 136, 153, 171, 190   # L11 - L20
]
# Expand up to Level 100
for _lvl in range(21, 101):
    _prev = PARTIAL_MANIFESTER_PP_TABLE[-1]
    _gain = 19 + (_lvl - 20)
    PARTIAL_MANIFESTER_PP_TABLE.append(_prev + _gain)

# Class Manifester Type & Key Ability Map
PSIONIC_CLASS_METADATA = {
    # XPH Classes
    "psion": {"type": "full", "key_stat": "INT", "hd": 6, "role": "Discipline Manifester"},
    "psychic_warrior": {"type": "partial", "key_stat": "WIS", "hd": 8, "role": "Combat Manifester"},
    "soulknife": {"type": "non_manifester", "key_stat": "WIS", "hd": 10, "role": "Mind Blade Duelist"},
    "wilder": {"type": "full", "key_stat": "CHA", "hd": 6, "role": "Surge Manifester"},
    # DSP Classes
    "aegis": {"type": "suit_specialist", "key_stat": "INT", "hd": 10, "role": "Astral Suit Master"},
    "vitalist": {"type": "full", "key_stat": "WIS", "hd": 6, "role": "Collective Healer"},
    "tactician": {"type": "full", "key_stat": "INT", "hd": 8, "role": "Collective Commander"},
    "cryptic": {"type": "full", "key_stat": "INT", "hd": 8, "role": "Pattern Disruptor"},
    "dread": {"type": "full", "key_stat": "CHA", "hd": 10, "role": "Terror Knight"},
    "marksman": {"type": "partial", "key_stat": "WIS", "hd": 10, "role": "Psionic Sniper"}
}

# Racial Bonus PP (Naturally Psionic traits)
RACIAL_BONUS_PP = {
    "elan": 2,
    "maenad": 2,
    "dromite": 1,
    "xeph": 1,
    "half_giant": 2,
    "ophiduan": 2,
    "forgeborn": 1,
    "blue": 2,
    "duergar_psionic": 1
}


def calculate_manifester_level(player_state: dict) -> int:
    """Calculates active Manifester Level (ML) for the player."""
    if not isinstance(player_state, dict):
        return 1
    lvl = max(1, int(player_state.get("level", 1) or 1))
    c_raw = str(player_state.get("class", "psion")).lower()
    
    # Check overchannel or wild surge active boost
    ml_boost = int(player_state.get("temp_ml_boost", 0) or 0)
    return max(1, lvl + ml_boost)


def calculate_max_power_points(player_state: dict) -> int:
    """
    Calculates maximum Power Points (PP) according to D&D 3.5 XPH and DSP rules:
    Total PP = Base Class PP + Key Stat Bonus PP + Racial Bonus PP.
    Bonus PP formula = (Stat Modifier * Manifester Level * 0.5)
    """
    if not isinstance(player_state, dict):
        return 0
    lvl = min(100, max(1, int(player_state.get("level", 1) or 1)))
    stats = player_state.get("stats", {})
    c_raw = str(player_state.get("class", "")).lower()

    # Identify primary psionic class
    meta = None
    for k, v in PSIONIC_CLASS_METADATA.items():
        if k in c_raw:
            meta = v
            break
    if not meta:
        # Fallback if character possesses psionic feats/powers or pathless with psionics
        if any("psionic" in str(f).lower() or "power point" in str(f).lower() for f in player_state.get("feats", [])):
            meta = {"type": "partial", "key_stat": "INT", "hd": 8}
        else:
            meta = {"type": "non_manifester", "key_stat": "WIS", "hd": 8}

    if meta["type"] == "non_manifester" and "soulknife" not in c_raw:
        base_pp = 0
    elif meta["type"] == "partial":
        base_pp = PARTIAL_MANIFESTER_PP_TABLE[min(lvl, len(PARTIAL_MANIFESTER_PP_TABLE) - 1)]
    elif meta["type"] in ("full", "suit_specialist"):
        base_pp = FULL_MANIFESTER_PP_TABLE[min(lvl, len(FULL_MANIFESTER_PP_TABLE) - 1)]
    else:
        base_pp = 2

    # Key Ability Modifier Bonus PP
    key_stat_val = stats.get(meta["key_stat"], 10)
    key_mod = max(0, (key_stat_val - 10) // 2)
    bonus_pp = int(key_mod * lvl * 0.5)

    # Racial Bonus PP
    race_str = str(player_state.get("race_key", player_state.get("race", ""))).lower()
    racial_pp = 0
    for r_k, r_val in RACIAL_BONUS_PP.items():
        if r_k in race_str:
            racial_pp = r_val
            break

    total_pp = base_pp + bonus_pp + racial_pp
    return max(0, total_pp)


def validate_power_manifestation(player_state: dict, power_name: str = "", base_pp_cost: int = 1, augment_pp: int = 0, **kwargs) -> dict:
    """
    Enforces the Golden Rule of D&D 3.5 Psionics:
    A character can NEVER spend more Power Points on a power than their Manifester Level (ML)!
    Also verifies player has enough current PP available.
    """
    if not isinstance(player_state, dict):
        return {"valid": False, "reason": "Invalid player state."}

    # Handle (player, base_pp, augment_pp) or (player, power_name, base_pp, augment_pp)
    if isinstance(power_name, (int, float)):
        actual_base = int(power_name)
        actual_aug = int(base_pp_cost if isinstance(base_pp_cost, (int, float)) else kwargs.get("augment_pp", 0))
    else:
        actual_base = int(kwargs.get("base_pp", kwargs.get("base_pp_cost", base_pp_cost)))
        actual_aug = int(kwargs.get("augment_pp", augment_pp))

    ml = calculate_manifester_level(player_state)
    total_cost = actual_base + max(0, actual_aug)
    
    # Check current PP
    current_pp = int(player_state.get("combat_resource", {}).get("current", 0) if player_state.get("combat_resource", {}).get("type") in ["power_points", "customization_points"] else player_state.get("power_points", 0))

    if total_cost > ml:
        return {
            "valid": False,
            "total_cost": total_cost,
            "ml_cap": ml,
            "current_pp": current_pp,
            "reason": f"Manifester Level Cap Exceeded: Cannot spend {total_cost} PP (Max ML is {ml} PP)! Total PP spent exceeds Manifester Level."
        }

    if current_pp < total_cost:
        return {
            "valid": False,
            "total_cost": total_cost,
            "ml_cap": ml,
            "current_pp": current_pp,
            "reason": f"Insufficient Power Points: Requires {total_cost} PP, but only have {current_pp} PP."
        }

    return {
        "valid": True,
        "total_cost": total_cost,
        "ml_cap": ml,
        "current_pp": current_pp,
        "reason": "Manifestation validated within Manifester Level cap and PP budget."
    }


def manifest_psionic_power(player_state: dict, power_name: str, base_pp_cost: int = 1, augment_pp: int = 0, power_details: dict = None, **kwargs) -> dict:
    """
    Executes manifestation of a psionic power, deducting PP and computing augmented values.
    """
    actual_base = int(kwargs.get("base_pp", kwargs.get("base_pp_cost", base_pp_cost)))
    actual_aug = int(kwargs.get("augment_pp", augment_pp))
    validation = validate_power_manifestation(player_state, power_name, actual_base, actual_aug)
    if not validation["valid"]:
        return {"success": False, "message": validation["reason"], "validation": validation}

    total_cost = validation["total_cost"]

    # Deduct PP from player
    if player_state.get("combat_resource", {}).get("type") in ["power_points", "customization_points"]:
        player_state["combat_resource"]["current"] = max(0, player_state["combat_resource"]["current"] - total_cost)
    else:
        player_state["power_points"] = max(0, player_state.get("power_points", 0) - total_cost)

    ml = validation["ml_cap"]
    dc_bonus = actual_aug // 2
    damage_bonus_dice = actual_aug

    return {
        "success": True,
        "power_name": power_name,
        "pp_spent": total_cost,
        "base_pp": actual_base,
        "augment_pp": actual_aug,
        "dc_bonus": dc_bonus,
        "damage_bonus_dice": damage_bonus_dice,
        "manifester_level": ml,
        "remaining_pp": player_state.get("combat_resource", {}).get("current", player_state.get("power_points", 0)),
        "message": f"Manifested [{power_name}] spent {total_cost} PP (Augmented +{actual_aug} PP). Effective DC +{dc_bonus}, Damage +{damage_bonus_dice} dice."
    }


# =====================================================================
# 2. PSIONIC FOCUS & MEDITATION ENGINE (DC 20 CONCENTRATION)
# =====================================================================

def meditate_for_psionic_focus(player_state: dict, roll_override: int = None) -> dict:
    """
    Attempts to achieve Psionic Focus (D&D 3.5 XPH p. 37):
    Full-round action. Roll Concentration check (or Meditation & Ki skill) vs DC 20.
    Success sets `psionic_focus: True`.
    """
    if not isinstance(player_state, dict):
        return {"success": False, "message": "Invalid player state."}

    skills = player_state.get("skills", {})
    med_skill = skills.get("Meditation & Ki", skills.get("Concentration", {}))
    if isinstance(med_skill, dict):
        mastery = med_skill.get("mastery", 0)
    else:
        mastery = int(med_skill or 0)
    skill_bonus = mastery // 20

    stats = player_state.get("stats", {})
    wis_mod = (stats.get("WIS", 10) - 10) // 2
    con_mod = (stats.get("CON", 10) - 10) // 2
    attr_bonus = max(wis_mod, con_mod)

    d20 = roll_override if roll_override is not None else random.randint(1, 20)
    total_check = d20 + skill_bonus + attr_bonus

    if total_check >= 20:
        player_state["psionic_focus"] = True
        return {
            "success": True,
            "check": total_check,
            "roll": d20,
            "dc": 20,
            "psionic_focus": True,
            "message": f"🧘 **Psionic Focus Achieved!** Rolled {total_check} (d20: {d20} + Bonus: {skill_bonus + attr_bonus}) vs DC 20. Mind is centered and resonant."
        }
    else:
        return {
            "success": False,
            "check": total_check,
            "roll": d20,
            "dc": 20,
            "psionic_focus": player_state.get("psionic_focus", False),
            "message": f"Meditation interrupted: Rolled {total_check} vs DC 20. Failed to attain Psionic Focus."
        }


def expend_psionic_focus(player_state: dict, feat_or_ability_name: str) -> dict:
    """
    Expends active Psionic Focus to empower a metapsionic feat, psionic strike, or class maneuver.
    """
    if not isinstance(player_state, dict):
        return {"success": False, "message": "Invalid player state."}

    if not player_state.get("psionic_focus", False):
        return {
            "success": False,
            "message": "Requires active Psionic Focus! Meditate first (DC 20 check) to center your mind."
        }

    player_state["psionic_focus"] = False
    clean_n = feat_or_ability_name.lower()
    bonus_damage_dice = None

    if "deep impact" in clean_n:
        effect = "Resolves next melee weapon strike as a Touch Attack (bypassing armor and shields)."
    elif "psionic weapon" in clean_n or "greater psionic weapon" in clean_n:
        bonus_damage_dice = "4d6" if "greater" in clean_n else "2d6"
        effect = f"Infuses strike with +{bonus_damage_dice} bonus psychokinetic damage."
    elif "empower power" in clean_n:
        effect = "Increases all variable numeric effects of manifested power by +50%."
    elif "maximize power" in clean_n:
        effect = "Maximizes all variable numeric effects of manifested power to their maximum value."
    elif "quicken power" in clean_n:
        effect = "Manifests power as a Free Action (Swift Action) without expending standard action."
    elif "split psionic ray" in clean_n:
        effect = "Duplicates ray power, striking an additional secondary target within 30 ft."
    else:
        effect = f"Empowers [{feat_or_ability_name}] through expended psionic focus."

    ret = {
        "success": True,
        "feat_name": feat_or_ability_name,
        "effect": effect,
        "psionic_focus": False,
        "message": f"⚡ Expended Psionic Focus to trigger [{feat_or_ability_name}]! {effect}"
    }
    if bonus_damage_dice is not None:
        ret["bonus_damage_dice"] = bonus_damage_dice
    return ret


# =====================================================================
# 3. SOULKNIFE MIND BLADE ENGINE (D&D 3.5 XPH)
# =====================================================================

def manifest_mind_blade(player_state: dict, shape: str = "longsword") -> dict:
    """
    Manifests a Mind Blade (XPH p. 26):
    Semi-solid blade of psychic energy formed from psychic willpower.
    Shapes: 'shortsword', 'longsword', 'bastard_sword' (2-handed).
    Enhancement bonus scales: +1 at L4, +2 at L8, +3 at L12, +4 at L16, +5 at L20 (+6 to +10 epic).
    """
    if not isinstance(player_state, dict):
        return {"success": False, "message": "Invalid player state."}

    lvl = int(player_state.get("level", 1) or 1)
    clean_s = str(shape or "longsword").lower().replace(" ", "_")

    if lvl >= 20:
        enh = min(10, 5 + (lvl - 20) // 10)
    elif lvl >= 16:
        enh = 4
    elif lvl >= 12:
        enh = 3
    elif lvl >= 8:
        enh = 2
    elif lvl >= 4:
        enh = 1
    else:
        enh = 0

    shape_name = "Bastard Mind Blade" if "bastard" in clean_s else ("Short Mind Blade" if "short" in clean_s else "Mind Blade")
    damage_dice = "1d10" if "bastard" in clean_s else ("1d6" if "short" in clean_s else "1d8")
    is_2h = "bastard" in clean_s

    blade_name = f"Manifested Mind Blade +{enh}" if enh > 0 else f"Manifested {shape_name}"
    blade_item = {
        "name": blade_name,
        "slot": "main_hand",
        "rarity": "Psionic Relic",
        "enhancement": enh,
        "enhancement_bonus": enh,
        "damage": damage_dice,
        "damage_type": "psychic force / physical",
        "is_two_handed": is_2h,
        "desc": f"A manifest blade of crackling cerulean psychic willpower (+{enh} enhancement, {damage_dice} base damage). Can be thrown (30ft range increment) and re-manifested at will as a free action.",
        "visual_appearance": f"wielding a glowing, semi-solid blade of intense cerulean psionic energy that crackles with psionic sparks"
    }

    equipped = player_state.setdefault("equipped", {})
    equipped["main_hand"] = blade_name
    if is_2h:
        equipped["off_hand"] = "None (2H Grip)"

    player_state["active_mind_blade"] = blade_item

    return {
        "success": True,
        "blade_item": blade_item,
        "shape": shape_name,
        "enhancement": enh,
        "enhancement_bonus": enh,
        "message": f"🗡️ Manifested [{blade_name}] ({damage_dice} damage, {'2-Handed' if is_2h else '1-Handed'})! Equipped directly into main hand."
    }


def charge_psychic_strike(player_state: dict) -> dict:
    """
    Charges Mind Blade with Psychic Strike (XPH p. 28):
    Move Action. Imbues blade with +1d8 psychic damage, scaling +1d8 every 4 levels (2d8 at 5, 3d8 at 9, etc.).
    Discharged on the next successful melee attack against a mind-affectable creature.
    """
    if not isinstance(player_state, dict):
        return {"success": False, "message": "Invalid player state."}

    lvl = int(player_state.get("level", 1) or 1)
    dice_count = 1 + (lvl - 1) // 4
    dice_str = f"{dice_count}d8"

    player_state["psychic_strike_charged"] = True
    player_state["psychic_strike_dice"] = dice_str

    return {
        "success": True,
        "dice": dice_str,
        "bonus_damage_dice": f"+{dice_str}",
        "message": f"⚡ **Psychic Strike Charged!** Mind Blade hums with destructive psionic dissonance (+{dice_str} psychic damage on next hit)."
    }


# =====================================================================
# 4. WILDER WILD SURGE & PSYCHIC ENERVATION ENGINE (D&D 3.5 XPH)
# =====================================================================

def execute_wild_surge(player_state: dict, surge_bonus: int = 1, roll_override: int = None, surge_level: int = None, **kwargs) -> dict:
    """
    Executes a Wilder Wild Surge (XPH p. 30):
    Boosts Manifester Level by +surge_bonus (from +1 up to +6) for 1 manifestation.
    Risk: 15% chance of Psychic Enervation (roll <= 15 on d100).
    If Enervated: Manifester loses PP equal to level, is dazed for 1 round.
    If Successful: Gains Surging Euphoria (+1 to +3 morale bonus on attacks, damage, and saves for surge_bonus rounds).
    """
    if not isinstance(player_state, dict):
        return {"success": False, "message": "Invalid player state."}

    if surge_level is not None:
        surge_bonus = surge_level

    lvl = int(player_state.get("level", 1) or 1)
    max_surge = min(6, 1 + (lvl - 1) // 4)
    clean_surge = max(1, min(max_surge, surge_bonus))

    d100 = roll_override if roll_override is not None else random.randint(1, 100)
    enervated = (d100 <= 15)

    if enervated:
        # Penalties of Psychic Enervation
        pp_loss = lvl
        if player_state.get("combat_resource", {}).get("type") == "power_points":
            player_state["combat_resource"]["current"] = max(0, player_state["combat_resource"]["current"] - pp_loss)
        else:
            player_state["power_points"] = max(0, player_state.get("power_points", 0) - pp_loss)

        player_state["temp_ml_boost"] = 0
        return {
            "success": False,
            "enervated": True,
            "surge_bonus": clean_surge,
            "ml_boost": 0,
            "euphoria_bonus": 0,
            "pp_lost": pp_loss,
            "d100": d100,
            "message": f"💥 **PSYCHIC ENERVATION!** Rolled {d100} <= 15%. Overwhelming mental backlash dazes you for 1 round and burns {pp_loss} Power Points!"
        }
    else:
        # Success: Apply temporary ML boost and Surging Euphoria
        player_state["temp_ml_boost"] = clean_surge
        euphoria_bonus = 1 if clean_surge <= 3 else (2 if clean_surge <= 5 else 3)
        player_state["surging_euphoria"] = {
            "bonus": euphoria_bonus,
            "rounds_remaining": clean_surge
        }
        return {
            "success": True,
            "enervated": False,
            "surge_bonus": clean_surge,
            "ml_boost": clean_surge,
            "euphoria_bonus": euphoria_bonus,
            "d100": d100,
            "message": f"🔥 **WILD SURGE +{clean_surge} ML!** Rolled {d100} > 15%. Manifester Level surged by +{clean_surge}! Surging Euphoria grants +{euphoria_bonus} on attack, damage, and save rolls."
        }


# =====================================================================
# 5. AEGIS ASTRAL SUIT CUSTOMIZATION ENGINE (DREAMSCARRED PRESS)
# =====================================================================

AEGIS_CUSTOMIZATIONS_CATALOG = {
    # 1-Point Customizations
    "hardened_carapace": {
        "name": "Hardened Carapace",
        "cp_cost": 1,
        "max_ranks": 5,
        "desc": "+2 Armor Class bonus to Astral Suit per rank.",
        "effect": "ac_bonus_2"
    },
    "energy_resistance_fire": {
        "name": "Energy Resistance: Fire",
        "cp_cost": 1,
        "max_ranks": 4,
        "desc": "Grants 5 Fire Resistance per rank.",
        "effect": "res_fire_5"
    },
    "energy_resistance_cold": {
        "name": "Energy Resistance: Cold",
        "cp_cost": 1,
        "max_ranks": 4,
        "desc": "Grants 5 Cold Resistance per rank.",
        "effect": "res_cold_5"
    },
    "energy_resistance_electric": {
        "name": "Energy Resistance: Electricity",
        "cp_cost": 1,
        "max_ranks": 4,
        "desc": "Grants 5 Electricity Resistance per rank.",
        "effect": "res_elec_5"
    },
    "speed_boost": {
        "name": "Ectoplasmic Propulsion",
        "cp_cost": 1,
        "max_ranks": 3,
        "desc": "+10 ft land movement speed per rank.",
        "effect": "speed_10"
    },
    "darkvision": {
        "name": "Ocular Spectrum Lens",
        "cp_cost": 1,
        "max_ranks": 1,
        "desc": "Grants 60 ft Darkvision and reveals hidden ethereal signatures.",
        "effect": "darkvision_60"
    },
    "swim_speed": {
        "name": "Aquatic Propulsion Fins",
        "cp_cost": 1,
        "max_ranks": 1,
        "desc": "Grants natural swim speed equal to land speed.",
        "effect": "swim_speed"
    },

    # 2-Point Customizations
    "flight_wings": {
        "name": "Ectoplasmic Wings",
        "cp_cost": 2,
        "max_ranks": 1,
        "desc": "Manifests sweeping psionic wings granting 40 ft flight speed (Good maneuverability).",
        "effect": "fly_40"
    },
    "retaliatory_spikes": {
        "name": "Retaliatory Ecto-Spikes",
        "cp_cost": 2,
        "max_ranks": 2,
        "desc": "Coats suit in razor crystalline spikes. Attackers striking with melee weapons take 1d8 piercing damage.",
        "effect": "reflect_spikes_1d8"
    },
    "reach": {
        "name": "Extended Psionic Reach",
        "cp_cost": 2,
        "max_ranks": 2,
        "desc": "+5 ft melee reach with all manufactured and natural weapons.",
        "effect": "reach_5"
    },
    "burrow": {
        "name": "Tectonic Burrowing Tines",
        "cp_cost": 2,
        "max_ranks": 1,
        "desc": "Grants 20 ft burrow speed through solid rock, earth, and masonry.",
        "effect": "burrow_20"
    },
    "energy_blast": {
        "name": "Ecto-Blast Hardpoint",
        "cp_cost": 2,
        "max_ranks": 3,
        "desc": "Fires a ranged beam of concentrated ectoplasm (60 ft range, 2d6 damage per rank).",
        "effect": "blast_2d6"
    },
    "damage_reduction": {
        "name": "Ablative Matrix (DR)",
        "cp_cost": 2,
        "max_ranks": 3,
        "desc": "Grants Damage Reduction 3/- per rank against all physical attacks.",
        "effect": "dr_3_none"
    },

    # 3-Point Customizations
    "power_resistance": {
        "name": "Psionic Disruption Ward",
        "cp_cost": 3,
        "max_ranks": 1,
        "desc": "Grants Power Resistance (PR) / Spell Resistance equal to 11 + Character Level.",
        "effect": "pr_11_plus_lvl"
    },
    "size_increase_large": {
        "name": "Colossal Expansion",
        "cp_cost": 3,
        "max_ranks": 1,
        "desc": "Suit size expands to Large; +4 STR, -2 DEX, +2 Natural Armor, and weapon damage steps up.",
        "effect": "large_size"
    },

    # 4-Point Customizations
    "extra_arms": {
        "name": "Secondary Ectoplasmic Arms",
        "cp_cost": 4,
        "max_ranks": 1,
        "desc": "Manifests two additional fully functional ectoplasmic arms capable of wielding shields or weapons.",
        "effect": "quad_wield"
    },
    "flight_jets": {
        "name": "Supersonic Astral Thrusters",
        "cp_cost": 4,
        "max_ranks": 1,
        "desc": "Supersonic flight (80 ft speed, Perfect maneuverability) with +4 on Reflex saving throws.",
        "effect": "fly_80"
    }
}


def calculate_aegis_customization_points(level_or_player) -> int:
    """
    Calculates total Customization Points (CP) budget for an Aegis (DSP Ultimate Psionics p. 32):
    Level 1: 3 CP, Level 2: 4 CP, Level 3: 5 CP, Level 4: 7 CP, Level 5: 8 CP, Level 6: 9 CP ... Level 20: 26 CP.
    Levels 21-100: +1 CP per level, plus +1 extra per 20 epic levels (110 CP at Level 100).
    """
    if isinstance(level_or_player, dict):
        lvl = int(level_or_player.get("level", 1) or 1)
    else:
        lvl = int(level_or_player or 1)
    lvl = max(1, lvl)
    if lvl <= 20:
        base_cp = [0, 3, 4, 5, 7, 8, 9, 10, 12, 13, 14, 15, 17, 18, 19, 20, 22, 23, 24, 25, 26]
        return base_cp[lvl]
    else:
        return 26 + (lvl - 20) + ((lvl - 20) // 20)


def configure_astral_suit(player_state: dict, suit_mode: str = "astral_armor", chosen_customizations: list = None, form_mode: str = None, customizations: list = None, **kwargs) -> dict:
    """
    Reconfigures the Aegis Astral Suit:
    Modes:
    - 'astral_skin': Light (+3 AC, +2 DEX, +10ft speed, Nimble Evasion, Medium size)
    - 'astral_armor': Medium (+6 AC, DR 2/-, Reinforced Poise, Medium size)
    - 'astral_juggernaut': Heavy (+10 AC, DR 5/-, Spiked Slam, Large size)
    Enforces Customization Point (CP) budget.
    """
    if not isinstance(player_state, dict):
        return {"success": False, "message": "Invalid player state."}

    lvl = int(player_state.get("level", 1) or 1)
    max_cp = calculate_aegis_customization_points(player_state if isinstance(player_state, dict) else lvl)
    
    clean_mode = str(form_mode or suit_mode or "astral_armor").lower().replace(" ", "_")
    if customizations is not None:
        chosen_customizations = customizations
    if chosen_customizations is None:
        chosen_customizations = []

    # Calculate CP cost
    total_cp_requested = sum(AEGIS_CUSTOMIZATIONS_CATALOG.get(c_id, {}).get("cp_cost", 1) for c_id in chosen_customizations if c_id in AEGIS_CUSTOMIZATIONS_CATALOG)

    if total_cp_requested > max_cp:
        return {
            "success": False,
            "form": clean_mode,
            "max_cp": max_cp,
            "cp_spent": 0,
            "message": f"Configuration rejected: insufficient Customization Points! Requested {total_cp_requested} CP, but budget is only {max_cp} CP."
        }

    applied_custs = [c_id for c_id in chosen_customizations if c_id in AEGIS_CUSTOMIZATIONS_CATALOG]
    active_buffs = [AEGIS_CUSTOMIZATIONS_CATALOG[c_id]["name"] for c_id in applied_custs]
    total_cp_spent = total_cp_requested

    # Base suit bonuses
    if clean_mode == "astral_juggernaut":
        base_ac = 10
        base_dr = 5
        suit_size = "Large"
        mode_desc = "Astral Juggernaut Heavy Plating (+10 AC, DR 5/-, Large Build, Spiked Slam)"
    elif clean_mode == "astral_skin":
        base_ac = 3
        base_dr = 0
        suit_size = "Medium"
        mode_desc = "Astral Skin Lightweight Weave (+3 AC, +2 DEX, +10ft Speed, Nimble Evasion)"
    else:
        base_ac = 6
        base_dr = 2
        suit_size = "Medium"
        mode_desc = "Astral Armor Tactical Exoskeleton (+6 AC, DR 2/-, Reinforced Poise)"

    suit_state = {
        "active": True,
        "form": clean_mode,
        "mode": clean_mode,
        "mode_desc": mode_desc,
        "base_ac": base_ac,
        "armor_bonus": base_ac,
        "base_dr": base_dr,
        "dr": f"{base_dr}/-",
        "size": suit_size,
        "max_cp": max_cp,
        "spent_cp": total_cp_spent,
        "cp_spent": total_cp_spent,
        "customizations": applied_custs,
        "active_buffs": active_buffs
    }

    player_state["astral_suit"] = suit_state

    return {
        "success": True,
        "form": clean_mode,
        "armor_bonus": base_ac,
        "dr": f"{base_dr}/-",
        "size": suit_size,
        "cp_spent": total_cp_spent,
        "suit_state": suit_state,
        "max_cp": max_cp,
        "spent_cp": total_cp_spent,
        "message": f"🛡️ **Astral Suit Configured [{clean_mode.replace('_', ' ').title()}]!** {mode_desc} | CP: {total_cp_spent}/{max_cp} used."
    }


# =====================================================================
# 6. THE COLLECTIVE NETWORK ENGINE (VITALIST & TACTICIAN - DSP)
# =====================================================================

def init_collective(player_state: dict) -> dict:
    """Initializes the mental collective network for Vitalists and Tacticians."""
    if not isinstance(player_state, dict):
        return {"success": False, "message": "Invalid player state."}

    lvl = int(player_state.get("level", 1) or 1)
    stats = player_state.get("stats", {})
    key_mod = max(0, (stats.get("WIS", stats.get("INT", 10)) - 10) // 2)
    max_members = max(3, lvl + key_mod)

    player_state["collective"] = {
        "active": True,
        "max_members": max_members,
        "max_size": max_members,
        "members": {
            player_state.get("name", "Leader"): {
                "name": player_state.get("name", "Leader"),
                "hp": player_state.get("hp", 100),
                "max_hp": player_state.get("max_hp", 100),
                "is_leader": True
            }
        }
    }
    return {
        "success": True,
        "max_members": max_members,
        "max_size": max_members,
        "message": f"🧠 **The Collective Network Online!** Capacity: {max_members} connected minds."
    }


def join_collective(player_state: dict, member_name: str, max_hp: int = 100, current_hp: int = 100) -> dict:
    """Connects an ally or companion into the Collective network."""
    collective = player_state.setdefault("collective", {})
    if not collective.get("active") and not collective.get("max_size"):
        init_collective(player_state)
        collective = player_state["collective"]

    members = collective.setdefault("members", {})
    max_m = collective.get("max_size", collective.get("max_members", 5))

    if isinstance(members, list):
        if len(members) >= max_m and member_name not in members:
            return {"success": False, "message": f"Collective capacity reached ({max_m} members max)."}
        if member_name not in members:
            members.append(member_name)
        total_m = len(members)
    else:
        if len(members) >= max_m and member_name not in members:
            return {"success": False, "message": f"Collective capacity reached ({max_m} members max)."}
        members[member_name] = {
            "name": member_name,
            "hp": current_hp,
            "max_hp": max_hp,
            "is_leader": False
        }
        total_m = len(members)

    return {
        "success": True,
        "member_name": member_name,
        "total_members": total_m,
        "message": f"🔗 **{member_name} joined The Collective!** Vital signs and psionic routing bonded."
    }


def transfer_wounds(source_or_player: dict, target_or_source_name=None, amount_or_target_name=None, amount: int = None, **kwargs) -> dict:
    """
    Executes Transfer Wounds (Vitalist core feature - DSP Ultimate Psionics p. 74):
    Transfers damage / hit points across members in the Collective without touching distance limits.
    Supports:
      1. transfer_wounds(source_dict, target_dict, amount=10)
      2. transfer_wounds(player_state, source_name, target_name, amount)
    """
    if not isinstance(source_or_player, dict):
        return {"success": False, "message": "Invalid entity or player state."}

    # Case 1: Direct entity dicts: (source_dict, target_dict, amount=10)
    if isinstance(target_or_source_name, dict):
        source = source_or_player
        target = target_or_source_name
        amt = amount if amount is not None else (int(amount_or_target_name) if isinstance(amount_or_target_name, (int, float)) else int(kwargs.get("amount", 10)))
        source_name = source.get("name", "Source")
        target_name = target.get("name", "Target")

        heal_amount = min(amt, target.get("max_hp", 100) - target.get("hp", 0))
        if heal_amount <= 0:
            return {"success": False, "message": f"{target_name} is already at full health."}

        actual_transfer = min(heal_amount, source.get("hp", 1) - 1)
        if actual_transfer <= 0:
            return {"success": False, "message": f"{source_name} has insufficient health to transfer."}

        source["hp"] -= actual_transfer
        target["hp"] += actual_transfer
        return {
            "success": True,
            "transferred": actual_transfer,
            "source": source_name,
            "target": target_name,
            "source_hp": source["hp"],
            "target_hp": target["hp"],
            "message": f"🩸 **Transfer Wounds:** Rerouted {actual_transfer} HP from {source_name} ({source['hp']} HP) to {target_name} ({target['hp']} HP)."
        }

    # Case 2: Collective routing: (player_state, source_name, target_name, amount)
    player_state = source_or_player
    source_name = str(target_or_source_name) if target_or_source_name else player_state.get("name", "Player")
    target_name = str(amount_or_target_name) if isinstance(amount_or_target_name, str) else player_state.get("name", "Player")
    amt = amount if amount is not None else (int(amount_or_target_name) if isinstance(amount_or_target_name, (int, float)) else int(kwargs.get("amount", 10)))

    collective = player_state.get("collective", {})
    members = collective.get("members", {})

    if isinstance(members, dict):
        if source_name not in members or target_name not in members:
            return {"success": False, "message": "Both source and target must be members of The Collective."}
        source = members[source_name]
        target = members[target_name]
    else:
        # Fallback if members is a list or empty
        source = {"name": source_name, "hp": player_state.get("hp", 100), "max_hp": player_state.get("max_hp", 100)}
        target = {"name": target_name, "hp": 50, "max_hp": 100}

    heal_amount = min(amt, target["max_hp"] - target["hp"])
    if heal_amount <= 0:
        return {"success": False, "message": f"{target_name} is already at full health."}

    actual_transfer = min(heal_amount, source["hp"] - 1)
    if actual_transfer <= 0:
        return {"success": False, "message": f"{source_name} has insufficient health to transfer."}

    source["hp"] -= actual_transfer
    target["hp"] += actual_transfer

    if source_name == player_state.get("name"):
        player_state["hp"] = source["hp"]
    if target_name == player_state.get("name"):
        player_state["hp"] = target["hp"]

    return {
        "success": True,
        "transferred": actual_transfer,
        "source": source_name,
        "target": target_name,
        "source_hp": source["hp"],
        "target_hp": target["hp"],
        "message": f"🩸 **Transfer Wounds:** Rerouted {actual_transfer} HP from {source_name} ({source['hp']} HP) to {target_name} ({target['hp']} HP)."
    }
