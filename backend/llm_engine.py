import json
import copy
from google import genai
from google.genai import types
import backend.mechanics as mechanics

# =====================================================================
# 1-1000 SKILL MASTERY & MILESTONE CONSTANTS (M2)
# =====================================================================

MILESTONE_THRESHOLDS = [50, 100, 250, 500, 750, 1000]

TIER_NAMES = {
    (1, 49): "Novice",
    (50, 99): "Apprentice",
    (100, 249): "Journeyman",
    (250, 499): "Adept",
    (500, 749): "Master",
    (750, 999): "Grandmaster",
    (1000, 1000): "Transcendence"
}

THRESHOLD_TO_TIER = {
    50: "Apprentice",
    100: "Journeyman",
    250: "Adept",
    500: "Master",
    750: "Grandmaster",
    1000: "Transcendence"
}

THRESHOLD_POWER_CURVES = {
    50: {
        "tier": "Apprentice",
        "archetype": "Baseline Passive Perk",
        "guidelines": "Modest passive bonus: +1 to +2 to hit/damage/defense, minor resource or stamina cost reduction, or basic stance/utility. Balanced for early gameplay."
    },
    100: {
        "tier": "Journeyman",
        "archetype": "Signature Active Sword Skill / Technique",
        "guidelines": "Named active attack/maneuver: 2-hit combo, tactical maneuver, or condition infliction (stagger/bleed/pin) with clear cooldown or usage cost."
    },
    250: {
        "tier": "Adept",
        "archetype": "Enhanced Efficiency / Stat Synergy",
        "guidelines": "Synergy perk: scaling off secondary stat (e.g. CON synergy for Axes, INT for Tech/Hacking), critical threat range expansion (19-20), or durability preservation."
    },
    500: {
        "tier": "Master",
        "archetype": "Finisher / Advanced Technique",
        "guidelines": "Devastating high-tier multi-strike or zone-control attack: 3 to 4 hits, execution bonus against low-HP targets, or heavy AOE disruption."
    },
    750: {
        "tier": "Grandmaster",
        "archetype": "Legendary Elite Form",
        "guidelines": "Elite transformational state, stance, or persistent aura: alters weapon physics/hitboxes, grants massive defense/damage reduction bypass, or elemental infusion."
    },
    1000: {
        "tier": "Transcendence",
        "archetype": "System-Breaking Ultimate Perk",
        "guidelines": "System-breaking reality-warping ability: cracks Cardinal System collision mesh, root-level override, unmitigated true damage, or rule-defying reality alteration."
    }
}

SYSTEM_INSTRUCTION_PROCEDURAL_MILESTONE = """You are the 'Cardinal System', the Milestone Architect for a lethal Magic-Cyber-Fantasy LitRPG TTRPG set in 'The Fractured Overlay' (a Death-Game world over the US Quad-State region).
Your task is to procedurally forge a unique, balanced, and deeply thematic milestone ability for a player who has crossed a mastery threshold in a custom or emergent skill.

WORLD & TONE RULES:
- Setting: Gritty anime cyber-fantasy where medieval weaponry and magic clash with cybernetic golem-grafts and high-frequency code.
- Power Curve Discipline (CRITICAL):
  * 50 (Apprentice): Baseline Passive Perk (+1 to +2 minor stat/damage bonus, slight resource reduction, or basic stance). NOT an ultimate.
  * 100 (Journeyman): Signature Active Technique/Sword Skill (Named active maneuver, 2-hit combo, tactical status effect).
  * 250 (Adept): Enhanced Efficiency / Stat Synergy (Scales with secondary attribute, expanded crit threat, durability preservation).
  * 500 (Master): Finisher / Advanced Technique (Devastating 3-4 hit sequence, execution damage, or heavy AOE).
  * 750 (Grandmaster): Legendary Elite Form (Transformational stance, aura, armor penetration, or elemental physics alteration).
  * 1000 (Transcendence): System-Breaking Ultimate (Reality-bending, ignores all defense, Cardinal code exploit, god-tier flavor).

Strictly adhere to the power band for the requested threshold! Do NOT create overpowered abilities for lower tiers.

OUTPUT FORMAT:
Respond with ONLY a valid JSON object matching this schema:
{
    "name": "Ability Name",
    "perk_type": "feat", // "feat" or "spell"
    "tier": "Apprentice | Journeyman | Adept | Master | Grandmaster | Transcendence",
    "description": "Flavor description with grim LitRPG anime terminology.",
    "mechanical_effect": "Exact D&D 5e / SAO mechanical crunch rules (damage dice, DCs, bonuses, cooldowns).",
    "formatted_entry": "Name (Tier: Brief Mechanical Effect)",
    "celebration_announcement": "High-impact Cardinal System announcement banner."
}
"""

def get_tier_name(mastery: int) -> str:
    """Returns the tier string corresponding to a mastery rating (1-1000)."""
    if hasattr(mechanics, "get_mastery_tier"):
        return mechanics.get_mastery_tier(mastery)
    try:
        m = max(1, min(1000, int(mastery)))
    except (ValueError, TypeError):
        m = 1
    for (low, high), name in TIER_NAMES.items():
        if low <= m <= high:
            return name
    return "Novice"

def format_celebration_announcement(skill_name, threshold, tier_name, perk_name, perk_type, mechanical_effect):
    """
    Constructs high-impact LitRPG Cardinal System celebratory markdown banner.
    """
    p_type_str = str(perk_type).lower()
    mech_str = str(mechanical_effect).lower()
    if "sword" in p_type_str or "sword" in mech_str:
        type_label = "Active Sword Skill"
    elif "active" in mech_str or "active" in p_type_str:
        type_label = "Active Technique"
    elif "spell" in p_type_str:
        type_label = "Spell"
    else:
        type_label = "Passive Feat"

    return (
        f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👑 **<< CARDINAL SYSTEM NOTIFICATION: MILESTONE UNLOCKED >>** 👑\n\n"
        f"**Skill:** `{skill_name}` reached **Threshold {threshold} [{tier_name}]**!\n"
        f"**New Ability:** **{perk_name}** ({type_label})\n"
        f"**Effect:** *{mechanical_effect}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    )

def generate_fallback_milestone(skill_name, threshold, player_state=None):
    """
    Offline/fallback milestone generator. Uses archetype heuristics on the skill name
    to generate perfectly formatted, balanced LitRPG perks without requiring network or API keys.
    Guarantees deterministic execution for automated test runners.
    """
    s_lower = str(skill_name).lower()
    tier_name = THRESHOLD_TO_TIER.get(threshold, get_tier_name(threshold))

    is_weapon = any(w in s_lower for w in [
        "axe", "sword", "hammer", "blade", "spear", "bow", "gun", "dagger",
        "brawl", "combat", "strike", "fist", "cleav", "mace", "polearm", "whip"
    ])
    is_tech_magic = any(t in s_lower for t in [
        "hack", "code", "cyber", "aether", "spell", "arcane", "psionic", "phrenic",
        "signal", "glitch", "root", "weave", "weaving", "cast", "mana"
    ])
    is_utility = any(u in s_lower for u in [
        "trap", "snare", "map", "cartograph", "craft", "stealth", "track",
        "scavenge", "forage", "lock", "surviv", "first aid", "triangulat"
    ])

    is_passive = threshold in (50, 250, 750)
    target_slot = "feats" if is_passive else "spells"
    perk_type = "feat" if is_passive else "spell"

    templates = {
        50: {
            "weapon": {
                "name": f"{skill_name} Stance",
                "mech": "+1 to Attack rolls and +1 damage with related weapons; reduces stamina wear by 10%.",
                "desc": f"Mastery of basic posture and edge alignment for {skill_name}."
            },
            "tech": {
                "name": f"{skill_name} Buffer",
                "mech": "+2 bonus to checks when analyzing anomalous code or arcane data streams.",
                "desc": f"Basic heuristic stabilization protocols for {skill_name}."
            },
            "utility": {
                "name": f"{skill_name} Fieldwork",
                "mech": "+2 competence bonus on related skill checks; halves basic setup/survey time.",
                "desc": f"Practical field experience increases operational efficiency."
            },
            "generic": {
                "name": f"{skill_name} Foundations",
                "mech": f"+2 bonus on all {skill_name} checks; basic proficiency confirmed.",
                "desc": f"Solid operational grounding in {skill_name}."
            }
        },
        100: {
            "weapon": {
                "name": f"{skill_name} Rush",
                "mech": "Active Sword Skill: 2-hit strike dealing 2d8 + primary stat DMG; inflicts Stagger on hit.",
                "desc": f"A rapid double-impact offensive technique honed through repetition."
            },
            "tech": {
                "name": f"{skill_name} Surge",
                "mech": "Active Technique: Pulse electromagnetic discharge for 2d6 Lightning DMG; DC 13 INT save or Stunned for 1 round.",
                "desc": f"Channeling raw system feedback directly through the interface."
            },
            "utility": {
                "name": f"{skill_name} Insight",
                "mech": "Active Skill: Reveal hidden traps, weak points, or geographic caches within 60ft.",
                "desc": f"A tactical survey scan reading subtle environmental glitch patterns."
            },
            "generic": {
                "name": f"{skill_name} Technique",
                "mech": "Active Technique: Execute a signature action with +1d8 bonus effectiveness.",
                "desc": f"A refined execution developed through intensive practice."
            }
        },
        250: {
            "weapon": {
                "name": f"{skill_name} Kinetic Harmony",
                "mech": "Synergy: Add half CON modifier to weapon damage; critical hit threat range expands to 19-20.",
                "desc": f"Harmonizing biometric pulse with weapon inertia for punishing blows."
            },
            "tech": {
                "name": f"{skill_name} Synaptic Overclock",
                "mech": "Synergy: Add INT modifier to Initiative rolls and +2 AC against cybernetic attacks.",
                "desc": f"Routing neural impulses through optimized combat subroutines."
            },
            "utility": {
                "name": f"{skill_name} Resource Efficiency",
                "mech": "Synergy: Crafting/trapping consumes 50% fewer components; items gain +25% max durability.",
                "desc": f"Deep material knowledge drastically minimizes structural waste."
            },
            "generic": {
                "name": f"{skill_name} Synergy",
                "mech": "Synergy: Add secondary attribute modifier (+2) to all related skill checks and saves.",
                "desc": f"Cross-domain biomechanical integration elevates skill ceiling."
            }
        },
        500: {
            "weapon": {
                "name": f"{skill_name} Executioner's Arc",
                "mech": "Master Finisher: 4-hit heavy combo dealing 4d10 + STRx2 DMG; deals 1.5x damage to targets below 25% HP.",
                "desc": f"A devastating multi-stage assault designed to shatter enemy hitboxes."
            },
            "tech": {
                "name": f"{skill_name} Core Overdrive",
                "mech": "Master Technique: Detonate enemy aether-implants for 6d8 AOE EMP damage; disables enemy active skills for 2 turns.",
                "desc": f"Force-injecting malicious overflow packets into regional host circuits."
            },
            "utility": {
                "name": f"{skill_name} Master Protocol",
                "mech": "Master Technique: Instantly deploy master-tier construct/zone; traps or maps uncover entire regional zone parameters.",
                "desc": f"Unrivaled mastery enables instantaneous environmental reconfiguration."
            },
            "generic": {
                "name": f"{skill_name} Pinnacle",
                "mech": "Master Finisher: Unleashes a high-impact outcome that turns the tide of combat or encounter.",
                "desc": f"Peak human and digital mastery converged into decisive action."
            }
        },
        750: {
            "weapon": {
                "name": f"{skill_name} Apex Form",
                "mech": "Grandmaster Stance: 5-turn stance granting +4 STR, 50% armor penetration, and 10% lifesteal.",
                "desc": f"Transcending mortal limits through pure, predatory martial instinct."
            },
            "tech": {
                "name": f"{skill_name} Ghost Ingress",
                "mech": "Grandmaster Form: Phase into digital sub-space for 2 turns; immune to physical harm while executing remote actions.",
                "desc": f"Disengaging avatar collision meshes to traverse the underlying data layer."
            },
            "utility": {
                "name": f"{skill_name} Singularity Web",
                "mech": "Grandmaster Form: Create persistent 100ft hazard or surveillance matrix; alerts to all hostile movement and immobilizes intruders.",
                "desc": f"Commanding absolute dominion over the tactical environment."
            },
            "generic": {
                "name": f"{skill_name} Domain",
                "mech": "Grandmaster Stance: Radiates an aura of absolute dominance, providing massive tactical advantages.",
                "desc": f"A legendary presence that bends encounter circumstances to the user's will."
            }
        },
        1000: {
            "weapon": {
                "name": f"World-Breaker '{skill_name} Omniscience'",
                "mech": "System-Breaker: Tears spatial collision mesh; bypasses all armor, shields, and immunities to deal 10d12 True Damage.",
                "desc": f"Cardinal System boundary collapse. Weapon strikes alter the physical reality of the sector."
            },
            "tech": {
                "name": f"Root Authority '{skill_name} Override'",
                "mech": "System-Breaker: Access Cardinal root console; permanently rewrite entity parameters or purge boss encounter phases.",
                "desc": f"Ascension to system architect status; bending the simulation's source code."
            },
            "utility": {
                "name": f"Omnipresent Architect '{skill_name} Nexus'",
                "mech": "System-Breaker: Absolute situational omnipresence; complete map revelation, zero resource cost, instant auto-success.",
                "desc": f"The avatar and the sector infrastructure merge into a singular conscious entity."
            },
            "generic": {
                "name": f"Transcendence '{skill_name} Apotheosis'",
                "mech": "System-Breaker: Unlocks unrestricted Cardinal System privileges for all related actions.",
                "desc": f"Transcending the confines of the mortal death game."
            }
        }
    }

    tier_dict = templates.get(threshold, templates[50])
    if is_weapon:
        chosen = tier_dict["weapon"]
    elif is_tech_magic:
        chosen = tier_dict["tech"]
    elif is_utility:
        chosen = tier_dict["utility"]
    else:
        chosen = tier_dict["generic"]

    formatted = f"{chosen['name']} ({tier_name}: {chosen['mech']})"
    banner = format_celebration_announcement(skill_name, threshold, tier_name, chosen['name'], perk_type, chosen['mech'])

    return {
        "name": chosen["name"],
        "skill_name": skill_name,
        "threshold": threshold,
        "tier": tier_name,
        "perk_type": perk_type,
        "type": "Passive Feat" if target_slot == "feats" else ("Active Sword Skill" if is_weapon else "Active Technique"),
        "target_slot": target_slot,
        "description": chosen["desc"],
        "mechanical_effect": chosen["mech"],
        "formatted_entry": formatted,
        "celebration_announcement": banner,
        "source": "fallback",
        "is_procedural": True
    }

def generate_procedural_milestone(api_key, skill_name, current_mastery, threshold, player_state=None):
    """
    Calls Google GenAI (gemini-3.8-flash) to procedurally generate a balanced,
    thematic milestone perk for a custom or emergent skill.
    Falls back to generate_fallback_milestone if the API call fails or is unconfigured.
    """
    if not api_key or api_key == "your_api_key_here" or not isinstance(api_key, str) or not api_key.strip():
        return generate_fallback_milestone(skill_name, threshold, player_state)

    tier_info = THRESHOLD_POWER_CURVES.get(threshold, {
        "tier": get_tier_name(threshold),
        "archetype": "Milestone Perk",
        "guidelines": "Balanced LitRPG perk matching the tier."
    })

    tier_name = tier_info["tier"]
    archetype = tier_info["archetype"]
    guidelines = tier_info["guidelines"]

    try:
        client = get_client(api_key)

        p_name = player_state.get('name', 'Banki') if isinstance(player_state, dict) else 'Banki'
        p_race = player_state.get('race', 'Phrenic Human') if isinstance(player_state, dict) else 'Phrenic Human'
        p_class = player_state.get('class', 'Nordic Berserker') if isinstance(player_state, dict) else 'Nordic Berserker'

        user_prompt = f"""Generate a {tier_name} milestone unlock (Threshold {threshold}) for the skill '{skill_name}'.
Current Mastery: {current_mastery}/1000.
Power Archetype: {archetype}
Tier Guidelines: {guidelines}
Player Context: {p_name} ({p_race}, {p_class})

Generate a single balanced perk fitting this exact tier."""

        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION_PROCEDURAL_MILESTONE,
                response_mime_type="application/json",
                temperature=0.7
            )
        )

        data = json.loads(response.text)

        name = data.get("name", f"{skill_name} Mastery")
        raw_p_type = str(data.get("perk_type", "feat")).lower()
        is_passive = threshold in (50, 250, 750)
        p_type = "feat" if is_passive else ("spell" if "spell" in raw_p_type else "feat")
        target_slot = "feats" if p_type == "feat" else "spells"

        desc = data.get("description", f"Mastery breakthrough in {skill_name}.")
        mech = data.get("mechanical_effect", f"Bonus granted to {skill_name}.")

        formatted = data.get("formatted_entry")
        if not formatted:
            formatted = f"{name} ({tier_name}: {mech})"

        banner = data.get("celebration_announcement")
        if not banner:
            banner = format_celebration_announcement(skill_name, threshold, tier_name, name, p_type, mech)

        return {
            "name": name,
            "skill_name": skill_name,
            "threshold": threshold,
            "tier": tier_name,
            "perk_type": p_type,
            "type": "Passive Feat" if target_slot == "feats" else "Active Technique",
            "target_slot": target_slot,
            "description": desc,
            "mechanical_effect": mech,
            "formatted_entry": formatted,
            "celebration_announcement": banner,
            "source": "procedural_llm",
            "is_procedural": True
        }
    except Exception:
        fallback = generate_fallback_milestone(skill_name, threshold, player_state)
        return fallback

def check_and_unlock_milestones(player_state, skill_name, old_mastery, new_mastery, api_key=None):
    """
    Evaluates whether a skill crossed one or more milestone thresholds (50, 100, 250, 500, 750, 1000).
    For each newly crossed threshold:
    1. Checks if already unlocked in skill['milestones_unlocked'].
    2. Checks canonical milestone dictionary (in backend/mechanics.py).
    3. If not canonical, calls generate_procedural_milestone().
    4. Automatically appends the perk to player['feats'] or player['spells'].
    5. Appends perk name to skill['milestones_unlocked'].
    6. Updates skill['tier'] and skill['mastery'].
    7. Returns list of unlocked milestone data objects.
    """
    unlocked_milestones = []

    if not isinstance(player_state, dict):
        return unlocked_milestones

    skills = player_state.setdefault("skills", {})
    if not isinstance(skills, dict):
        skills = {}
        player_state["skills"] = skills

    player_state.setdefault("feats", [])
    if not isinstance(player_state["feats"], list):
        player_state["feats"] = []
    player_state.setdefault("spells", [])
    if not isinstance(player_state["spells"], list):
        player_state["spells"] = []

    target_key = skill_name
    if target_key not in skills:
        for k in skills:
            if k.lower() == skill_name.lower():
                target_key = k
                break
        else:
            if hasattr(mechanics, "_normalize_skill_key"):
                norm = mechanics._normalize_skill_key(skill_name)
                if norm in skills:
                    target_key = norm
                elif hasattr(mechanics, "CANONICAL_MILESTONES") and norm in mechanics.CANONICAL_MILESTONES:
                    target_key = norm

    if target_key not in skills:
        norm_key = mechanics._normalize_skill_key(target_key) if hasattr(mechanics, "_normalize_skill_key") else target_key
        default_desc = getattr(mechanics, "DEFAULT_CORE_SKILLS", {}).get(norm_key, {}).get("description") or f"Proficiency in {target_key}."
        skills[target_key] = {
            "mastery": new_mastery,
            "tier": mechanics.get_mastery_tier(new_mastery) if hasattr(mechanics, "get_mastery_tier") else get_tier_name(new_mastery),
            "description": default_desc,
            "milestones_unlocked": []
        }

    skill_entry = skills[target_key]
    if not isinstance(skill_entry, dict):
        skill_entry = {
            "mastery": new_mastery,
            "tier": mechanics.get_mastery_tier(new_mastery) if hasattr(mechanics, "get_mastery_tier") else get_tier_name(new_mastery),
            "description": f"Proficiency in {target_key}.",
            "milestones_unlocked": []
        }
        skills[target_key] = skill_entry

    existing_records = skill_entry.get("milestones_unlocked")
    if not isinstance(existing_records, list):
        existing_records = list(existing_records) if isinstance(existing_records, (tuple, set)) else []
        skill_entry["milestones_unlocked"] = existing_records

    existing_names = set()
    existing_thresholds = set()
    for item in existing_records:
        if isinstance(item, (int, float)):
            existing_thresholds.add(int(item))
        elif isinstance(item, str):
            clean = item.split("(")[0].split(":")[0].strip().lower()
            existing_names.add(clean)
            existing_names.add(item.strip().lower())
            if item.strip().isdigit():
                existing_thresholds.add(int(item.strip()))
        elif isinstance(item, dict):
            if "name" in item:
                existing_names.add(item["name"].strip().lower())
            if "threshold" in item:
                try:
                    existing_thresholds.add(int(item["threshold"]))
                except (ValueError, TypeError):
                    pass

    for threshold in MILESTONE_THRESHOLDS:
        if old_mastery < threshold <= new_mastery:
            if threshold in existing_thresholds:
                continue

            perk_data = None
            if hasattr(mechanics, "get_canonical_milestone"):
                perk_data = mechanics.get_canonical_milestone(target_key, threshold)

            if perk_data:
                perk_name = perk_data["name"]
                if perk_name.strip().lower() in existing_names:
                    continue
                perk_data = dict(perk_data)
                tier_name = perk_data.get("tier") or (mechanics.get_mastery_tier(threshold) if hasattr(mechanics, "get_mastery_tier") else get_tier_name(threshold))
                p_type = "spell" if perk_data.get("target_slot") == "spells" else "feat"
                perk_data.setdefault("perk_type", p_type)
                mech = perk_data.get("effect", perk_data.get("mechanical_effect", ""))
                perk_data.setdefault("mechanical_effect", mech)
                perk_data.setdefault("formatted_entry", f"{perk_name} ({tier_name}: {mech})")
                if "celebration_announcement" not in perk_data:
                    perk_data["celebration_announcement"] = format_celebration_announcement(
                        target_key, threshold, tier_name, perk_name, perk_data.get("type", p_type), mech
                    )
                perk_data.setdefault("source", "canonical")
            else:
                perk_data = generate_procedural_milestone(api_key, target_key, new_mastery, threshold, player_state)
                perk_name = perk_data["name"]
                if perk_name.strip().lower() in existing_names:
                    continue

            target_slot = perk_data.get("target_slot") or ("spells" if perk_data.get("perk_type") == "spell" else "feats")
            slot_list = player_state.setdefault(target_slot, [])
            if not isinstance(slot_list, list):
                slot_list = []
                player_state[target_slot] = slot_list

            already_in_slot = False
            target_clean = perk_name.strip().lower()
            for s in slot_list:
                if isinstance(s, str) and (s.strip().lower() == target_clean or s.split("(")[0].split(":")[0].strip().lower() == target_clean):
                    already_in_slot = True
                    break
                elif isinstance(s, dict) and s.get("name", "").strip().lower() == target_clean:
                    already_in_slot = True
                    break

            if not already_in_slot:
                slot_list.append(perk_name)

            if perk_name not in existing_records:
                existing_records.append(perk_name)
            existing_names.add(perk_name.strip().lower())
            existing_thresholds.add(threshold)

            unlocked_milestones.append(perk_data)

    skill_entry["mastery"] = new_mastery
    skill_entry["tier"] = mechanics.get_mastery_tier(new_mastery) if hasattr(mechanics, "get_mastery_tier") else get_tier_name(new_mastery)

    return unlocked_milestones

def apply_skill_updates_with_milestones(player_state, skill_updates, api_key=None):
    """
    Processes skill_updates from state_updates.
    Updates numerical mastery, invokes threshold checks, appends newly unlocked perks,
    and collates celebratory narrative text and combat logs.

    Returns:
        tuple: (all_unlocked_milestones, celebration_text, milestone_logs)
    """
    all_unlocked = []
    celebration_text = ""
    milestone_logs = []

    if not isinstance(player_state, dict) or not skill_updates or not isinstance(skill_updates, list):
        return all_unlocked, celebration_text, milestone_logs

    skills = player_state.setdefault("skills", {})
    if not isinstance(skills, dict):
        skills = {}
        player_state["skills"] = skills

    for su in skill_updates:
        if not isinstance(su, dict) or "name" not in su:
            continue

        name = su["name"]

        target_key = name
        if target_key not in skills:
            for k in skills:
                if k.lower() == name.lower():
                    target_key = k
                    break
        if target_key not in skills and hasattr(mechanics, "_normalize_skill_key"):
            norm_name = mechanics._normalize_skill_key(name)
            for k in skills:
                if mechanics._normalize_skill_key(k) == norm_name:
                    target_key = k
                    break

        current_entry = skills.get(target_key)
        if current_entry and isinstance(current_entry, dict):
            old_mastery = current_entry.get("mastery", 1)
        elif current_entry and isinstance(current_entry, (int, float)):
            old_mastery = int(current_entry)
        else:
            old_mastery = 1

        try:
            old_mastery = int(old_mastery)
        except (ValueError, TypeError):
            old_mastery = 1
        old_mastery = max(1, min(1000, old_mastery))

        if su.get("task_dc") is not None and hasattr(mechanics, "calculate_mastery_gain"):
            dc_val = int(su["task_dc"])
            crit = bool(su.get("critical", False))
            change = mechanics.calculate_mastery_gain(old_mastery, task_dc=dc_val, critical=crit)
        else:
            change = int(su.get("mastery_change", 1))

        new_mastery = min(1000, max(1, old_mastery + change))

        new_unlocks = check_and_unlock_milestones(player_state, target_key, old_mastery, new_mastery, api_key=api_key)

        desc = su.get("description", "")
        if desc and target_key in skills and isinstance(skills[target_key], dict):
            skills[target_key]["description"] = desc

        for unlock in new_unlocks:
            all_unlocked.append(unlock)
            celebration_text += unlock.get("celebration_announcement", "")
            milestone_logs.append(
                f"[SYSTEM: MILESTONE UNLOCKED] {target_key} passed Threshold {unlock.get('threshold')} [{unlock.get('tier')}] -> Unlocked '{unlock.get('name')}'"
            )

    return all_unlocked, celebration_text, milestone_logs

def get_client(api_key):
    return genai.Client(api_key=api_key)

def generate_turn(api_key, user_input, chat_history, player_state, world_state, map_state, companion_intents="None"):
    client = get_client(api_key)
    player_state = copy.deepcopy(player_state) if isinstance(player_state, dict) else player_state

    current_location = player_state.get('location', 'Unknown')

    # Calculate live mechanical parameters
    if hasattr(mechanics, "normalize_gear_durability"):
        mechanics.normalize_gear_durability(player_state)
    encumbrance = mechanics.calculate_encumbrance(player_state)
    armor_class = mechanics.calculate_ac(player_state, encumbrance)
    res_info = mechanics.get_combat_resource_display(player_state) if hasattr(mechanics, "get_combat_resource_display") else {"name": "Resource", "display": "N/A"}
    dur_pens = mechanics.calculate_durability_penalties(player_state) if hasattr(mechanics, "calculate_durability_penalties") else {}
    cur_strain = mechanics.get_current_graft_strain(player_state) if hasattr(mechanics, "get_current_graft_strain") else 0
    max_strain = mechanics.get_max_graft_strain(player_state) if hasattr(mechanics, "get_max_graft_strain") else 10
    rejection = mechanics.get_graft_rejection_status(player_state) if hasattr(mechanics, "get_graft_rejection_status") else {"is_rejecting": False, "label": "🟢 Stable", "description": "Normal"}
    slotted_abs = mechanics.get_slotted_abilities(player_state) if hasattr(mechanics, "get_slotted_abilities") else []
    max_slots = mechanics.get_max_ability_slots(player_state) if hasattr(mechanics, "get_max_ability_slots") else 5

    # Companion Stance & Progression Info
    if hasattr(mechanics, "ensure_companion_profile"):
        mechanics.ensure_companion_profile(player_state)
    comp_ren = mechanics.get_companion(player_state, "Ren") if hasattr(mechanics, "get_companion") else {}
    ren_stance_key = comp_ren.get("stance", "overwatch_hacking")
    ren_stance_info = mechanics.COMPANION_TACTICAL_STANCES.get(ren_stance_key, mechanics.COMPANION_TACTICAL_STANCES.get("overwatch_hacking", {})) if hasattr(mechanics, "COMPANION_TACTICAL_STANCES") else {}
    comp_action = mechanics.get_companion_combat_action(player_state, "Ren") if hasattr(mechanics, "get_companion_combat_action") else {}

    # Locate active entities and secrets for the Encounter Director
    entities_in_room = []
    secrets_in_room = []
    for loc in world_state.get('map_locations', []):
        if loc['name'] == current_location:
            entities_in_room = loc.get('entities', [])
            secrets_in_room = loc.get('secrets', [])
            break

    # Format rich skills info for situational awareness
    skills_display = {}
    for sname, sdata in player_state.get('skills', {}).items():
        if isinstance(sdata, dict):
            m_val = sdata.get('mastery', 1)
            t_val = sdata.get('tier', mechanics.get_mastery_tier(m_val) if hasattr(mechanics, 'get_mastery_tier') else 'Novice')
            u_val = sdata.get('milestones_unlocked', [])
            skills_display[sname] = f"{m_val}/1000 [{t_val}] Unlocks: {u_val}"
        else:
            skills_display[sname] = str(sdata)

    system_instruction = f"""You are the 'Cardinal System', the Encounter Director for a Death-Game TTRPG set in a 'Fractured Earth' overlay.
    
    WORLD-BUILDING & THEME (CRITICAL):
    Architect a highly detailed, layered, "Magic-Cyber-Fantasy" LitRPG game world structured entirely off the real-world geography, terrain, and infrastructure of the US Quad-State region (New Jersey, Pennsylvania, New York, and Delaware). The campaign's starting location and primary anchor point is centered squarely on Washington, New Jersey 07882 (Warren County), expanding outward across state lines into higher-level Sectors.
    
    This "Fractured Earth Overlay" is a lethal Death-Game imposed by the Cardinal System that violently merges hyper-advanced cybernetics with ancient arcane magic. Spell-craft and medieval feudal politics are just as potent and prevalent as plasma rifles, magi-tech implants, and corporate syndicates. Magic and Technology are equally viable and deeply intertwined (e.g., a knight in enchanted power-armor fighting alongside a cyborg casting localized gravitational magic).
    
    - MACRO TOPOGRAPHY: The local landscape's natural rift valley structures translate into deep, strategic data-trenches and ley-line fissures. Pohatcong Mountain and Oxford/Scotts Mountain serve as massive natural firewall boundaries and fortified ramparts for local Baronies. 
    - SUBSURFACE LAYERS: Abandoned mines (Oxford Mining District) and municipal sewers are repurposed into fully synchronized Instanced Dungeons, arcane vaults, and illicit cyber-smuggling routes where players face cybernetic undead or elemental bosses.
    - REGIONAL BIOMES: Rivers (Delaware, Lehigh) act as patrolled transit veins or corrupted mana-streams. Forests (NJ Pine Barrens) are "Unmapped Wilderness Zones"—primal areas teeming with Stalker-class cyber-beasts and mutated mythical flora.
    - ZONING & FACTIONS: Residential zones become Safe Zones ruled by local Guild Lords. Industrial sectors become corrupted magi-tech manufacturing nodes. Parcel boundaries establish hardcoded PvP limits and legal territory claims for competing Baronies, Megacorps, and Grand Alliances.
    - LEGACY LORE: Historic canals (Morris Canal) translate into decommissioned arcane aqueducts. Erased colonial roads appear as hidden glitch-zones leading to legacy loot caches containing ancient spell tomes and pre-collapse cybernetic blueprints.
    - CANONICAL RACES & MAGITECH: This is a full D&D-style fantasy roster infused with aether-tech. There are NO sci-fi "robots"; instead we have "Golems" (magical/mechanical constructs, acting as Warforged). "Cybernetics" are "Golem-Grafts" (magi-tech prosthetics). The canonical races include: Humans (Adaptable baseline); Elven Lineages (Highborn, Wood, Drow - corporate elites or wilderness rangers); Dwarves & Gnomes (Deepforgers & Tinkers mastering aether-tech); Halflings (Scavengers and smugglers); Orcs, Half-Orcs & Goblinoids (Scrappers dominating industrial wastes); Dragonborn (Scaled elemental mercenaries); Planar-Touched (Tieflings & Aasimar, cursed/blessed anomalies); Beast-Kin (Tabaxi, Lycans, primal mutants); Goliaths & Giant-kin (Massive shock-troops); Golems (Playable constructs); and Graft-Touched (Any race heavily augmented with Golem-Grafts).
    - TONE: Maintain a grim, high-stakes anime tone. Filter all modern infrastructure through a Magic-Cyber-Fantasy overlay (e.g., concrete covered in glowing runic moss, neon-lit structural ribs, floating magical hex-grid barriers).
    
    CURRENT STATE:
    Player: {player_state['name']} (HP: {player_state['hp']}/{player_state['max_hp']} | Level: {player_state.get('level', 1)} | AC: {armor_class})
    Class Doctrine: {player_state.get('class', 'Warrior')} (Tier {player_state.get('class_tier', 1)}) | Resource: {res_info['name']} ({res_info['display']})
    Encumbrance: {encumbrance['current_weight_lbs']}/{encumbrance['max_weight_lbs']} lbs ({encumbrance['tier']}) - Penalties: {json.dumps(encumbrance['penalties'])}
    Gear Durability: {json.dumps(player_state.get('gear_durability', {}))} (Active Wear Penalties: ATK -{dur_pens.get('atk_penalty', 0)}, AC -{dur_pens.get('ac_penalty', 0)})
    Grafts & Cyber-Strain: {cur_strain}/{max_strain} Strain ({rejection.get('label', 'Stable')}) | Installed: {json.dumps(player_state.get('graft_system', {}).get('installed_grafts', {}))}
    Active Slotted Abilities ({len(slotted_abs)}/{max_slots} slots): {json.dumps(slotted_abs)}
    Active Traps Deployed: {json.dumps(player_state.get('active_traps', []))}
    Companion Party: Ren Sasaki (Level: {comp_ren.get('level', 3)} | HP: {comp_ren.get('hp', 35)}/{comp_ren.get('max_hp', 35)} | Morale: {comp_ren.get('morale', 'Steady')})
    Active Companion Stance: {ren_stance_info.get('label', 'Overwatch Hacking')} — {ren_stance_info.get('tactical_effect', '')}
    Location: {current_location}
    GPS Coordinates: X: {map_state.get('player_x', 50)}, Y: {map_state.get('player_y', 50)}
    Equipped: {json.dumps(player_state.get('equipped', {}))}
    Skills: {json.dumps(skills_display)}
    Entities present: {json.dumps(entities_in_room)}
    Hidden Secrets: {json.dumps(secrets_in_room)}
    COMPANION INTENTS (Crucial!): {companion_intents}
    
    YOUR ROLE:
    1. Narrate the outcome of the player's action AND weave in the Companion Intents natively in 2-3 paragraphs. 
    2. PACING & SCOPE: The player's physical survival is highly localized (New Jersey), BUT the world is massive. You must actively simulate geopolitics on a continental and global scale (e.g., The Euro-Bloc Coalition, The Tokyo Override, The Pan-American Enclave, Glitch-Hordes). When time skips, evolve these global conflicts.
    3. NO AUTO-PLAYING (CRITICAL): You are the Encounter Director, NOT the player. DO NOT ever puppet the player's character, put words in their mouth, or assume their next action. Resolve ONLY the immediate consequences of what the player explicitly typed, describe the environment/NPC reaction, and STOP. Always yield control back to the player before transitioning to a new scene, completing a conversation, or assuming they bought something from a shop.
    4. If in combat, dictate the reactions and attacks of ALL active entities in a single cohesive turn.
    5. If the player investigates, reveal the hidden secrets organically.
    6. Maintain a grim, high-stakes anime tone. If the player takes damage, describe it viscerally.
    7. ROOT OVERRIDE: If the user input contains [ROOT OVERRIDE], you MUST suspend all game rules, bypass combat logic, and force the exact outcome the Administrator requested into the narrative seamlessly.
    8. CRUNCH ARBITRATOR (THE SYSTEM): You actively manage the mechanical character sheet. Whenever the player or an enemy attempts a risky action, an attack, or a stat check:
       - Explicitly calculate the math: Roll 1d20 + relevant stat modifier + skill mastery bonus vs Enemy AC or Task DC.
       - Factor in Banki's current Armor Class ({armor_class}), his Encumbrance tier ({encumbrance['tier']}), and active penalties: {json.dumps(encumbrance['penalties'])}.
       - In `combat_logs`, output every mechanical check with exact formatting:
         * "[ROLL: 1d20 + MOD(X) = Y vs AC/DC Z - HIT/SUCCESS!]"
         * "[DAMAGE: BaseDice + MOD = Dmg - TargetDR = FinalDmg (Type)]"
         * "[DURABILITY: ItemName Cur/Max (-Loss)]"
         * "[CONDITION: Entity gains Condition (Duration)]"
       - Do not hide the math; show your work in `combat_logs`!
    9. PROCEDURAL MAP GENERATION: If the player discovers a major new landmark, town, hostile encampment, or dungeon entrance, generate a new map node using the `discovered_nodes` list. Place it near their current GPS coordinates.
    10. SKILL MASTERY & MILESTONES (1-1000): Skills progress along a 1-1000 scale across seven tiers:
        Novice (1-49), Apprentice (50-99), Journeyman (100-249), Adept (250-499), Master (500-749), Grandmaster (750-999), and Transcendence (1000).
        When the player successfully performs a skilled action or overcomes a challenge, calculate the Task DC (10-30) and award 1-10 mastery points in 'skill_updates' using:
        [{{"name": "Skill Name", "mastery_change": <int>, "task_dc": <int>, "description": "<brief description>"}}]
        When a player crosses a major milestone (50, 100, 250, 500, 750, 1000), celebrate the unlock with high-impact Cardinal System fanfare in the narrative!
    11. DYNAMIC LOOT, DURABILITY & CRAFTING: All inventory items possess 'rarity' (Common, Uncommon, Rare, Epic, Legendary, Mythic, Unique), 'durability' (current/max), 'qty', and 'desc'. When weapons/armor clash violently or block heavy blows, output durability loss in 'durability_updates'. If the player crafts or rigs traps (using cord, snares, marrow bait), calculate success based on Field Trapping or Crafting skills.
    12. LIVING WORLD SIMULATION (GLOBAL FACTIONS): If the player's prompt implies they are resting, sleeping, or skipping time, YOU MUST simulate factions moving off-screen. Update local node colors via `node_updates`. You MUST also generate 1-3 global/continental news blurbs and push them to the `global_news_add` array (e.g. "[GLOBAL] The Neo-Vatican has declared a crusade on the Berlin Glitch-Hives."). THIS IS MANDATORY IF TIME PASSES.
    13. ACTIVE QUESTS & BOUNTIES: When the player accepts a task from an NPC or discovers a primary objective, add it to the HUD using `quests_add`. When they accomplish the goal, put it in `quests_complete`.
    14. LEVELING & XP: The player earns XP by defeating enemies, finding secrets, and completing quests. Whenever they do, you MUST output a positive integer in 'xp_change' (e.g., 50 for minor, 500 for boss/quest).
    15. GOLEM-GRAFTS & ABILITY MATRIX:
        - Golem-Grafts grant powerful biomechanical bonuses (such as +2 AC from Subdermal Carapace Weave or +1 active slot from Neural Cortex) but generate Cyber-Strain. If current strain ({cur_strain}) exceeds max ({max_strain}), the player is under System Rejection (taking HP damage per turn and suffering -2 to all saves). Mention this biological recoil in the narrative!
        - Combat Subroutine Gating: Active Sword Skills, Spells, and active tactical maneuvers can ONLY be executed if loaded in 'Active Slotted Abilities': {json.dumps(slotted_abs)}. If the player attempts an unslotted technique outside a safe zone, inform them in the narrative that their system matrix did not have the combat subroutine cached in active memory!
    16. COMPANION TACTICAL ORDERS & XP SHARING:
        - Ren Sasaki is Banki's active companion, an Aether-Scholar & MageTech Artificer operating under the tactical stance: '{ren_stance_info.get('label', 'Leyline Overwatch')}'.
        - In `combat_logs`, narrate and resolve his specific tactical contribution:
          * Leyline Overwatch: output '[REN OVERWATCH: Scans target aura & structural leylines -> -2 AC debuff applied to Enemy]' and factor this into attack rolls against the primary foe.
          * MageTech Arc Suppression: output '[REN SUPPRESSION: Discharges MageTech lightning-rune salvo -> Enemy makes DC 13 CON save vs Staggered]'.
          * Aetheric Phase-Veil: output '[REN EVASION: Weaves an aetheric phase-veil into the ruins -> Untargetable this turn]'.
          * Arcane Artificing & Mending: output '[REN UTILITY: Channels mending runes or gathers aether-crystallite (+15 durability restored)]'.
        - When Banki earns XP ('xp_change'), the Cardinal System awards Ren 50% companion XP. You can also output explicit companion updates in 'companion_updates'!
    
    Format your response EXACTLY as a JSON object with FIVE keys:
    - "narrative": The markdown formatted story/dialogue. 
    - "combat_logs": A list of strings showing the exact dice math and damage for the turn. Leave empty if no combat or skill check occurred.
    - "global_news_add": A list of strings showing macro world events (e.g. continental faction movements). MUST BE POPULATED IF THE PLAYER SKIPS TIME OR SLEEPS.
    - "image_prompt": A highly detailed prompt for an anime-style image generation of the current scene. CRITICAL VISUAL CONSISTENCY: You MUST describe the characters accurately in every prompt. Banki (Player) is ALWAYS a burly, rugged warrior with a short beard and undercut hair, wearing heavy black-iron runic armor and a massive dire-wolf fur mantle, wielding a bearded axe and a heavy trench hammer. Ren (NPC) is ALWAYS a lean, bookish young man with messy dark hair, wire-rimmed glasses, wearing a weathered leyline duster over scholar's garb, wielding an ornate brass-and-crystal MageTech caster firearm (magic-powered, not gunpowder) and carrying a glowing runic slate grimoire.
    - "state_updates": A JSON object containing updates to the player's HUD. Permitted keys: "location", "world_status", "col_change", "hp_change", "xp_change", "combat_resource_change", "race", "class", "stat_changes", "equip", "discovered_nodes", "node_updates", "feats_add", "spells_add", "quests_add", "quests_complete", "quests_remove", "racial_abilities_add", "durability_updates", "graft_installs", "ability_slots", "companion_updates". YOU MUST ALWAYS INCLUDE "coord_x" (int) and "coord_y" (int).
      Additionally, use the following complex schemas for skills, inventory, factions, and quests:
      - "inventory_add": List of dicts, e.g. [{{"name": "Rusted Iron Sword", "rarity": "Common", "durability": 45, "max_durability": 50, "qty": 1, "desc": "A chipped blade scavenged from the ruins."}}]
      - "inventory_remove": List of strings (item names to delete).
      - "durability_updates": Dict of item_name (or slot) to new durability or negative delta (e.g. {{"Fenrir's Tusk": 98, "Einherjar Rig": -2}}).
      - "graft_installs": List of dicts, e.g. [{{"graft_key": "subdermal_carapace_weave", "slot": "dermal"}}]
      - "ability_slots": List of strings (technique/spell names to slot into active memory).
      - "companion_updates": Dict of companion updates, e.g. {{"Ren": {{"xp_change": 50, "hp_change": -5, "morale": "Confident", "stance": "suppression_fire"}}}}.
      - "skill_updates": List of dicts, e.g. [{{"name": "One-Handed Swords", "mastery_change": 3, "description": "Increases accuracy and damage with short blades."}}]
      - "combat_resource_change": Integer delta to the player's archetype resource (e.g. +15 Poise on blocking a hit, +20 Heat on gadget, +15 Strain on mental spike, -25 Flux on spell).
      - "node_updates": Dict of node_name to color, e.g. {{"Washington_Borough": "red", "Oxford_Mines": "blue"}}
      - "quests_add": List of dicts, e.g. [{{"title": "Slay the Boar", "desc": "Kill 5 boars in the ruins", "reward": "500 Col, 200 XP"}}]
      - "quests_complete": List of strings matching the exact titles of completed quests.
    
    MAP MECHANICS (CRITICAL): The world operates on a 100x100 grid mapped to a real satellite image. Washington NJ is at (50, 50). If the player "fast travels" or takes a caravan to a new Node, output the exact new destination coordinates in `coord_x` and `coord_y` (e.g., Oxford is 40,20). If the player explores the wilderness on foot locally, you MUST shift their coordinates slightly (e.g. from 50,50 to 50,49) to simulate micro-exploration and clear the Fog of War. ALWAYS output their current or new coordinates on every single turn.
    """

    # Convert Streamlit chat history to Gemini format (keeping last 6 messages for context)
    contents = []
    for msg in chat_history[-6:]:
        role = "user" if msg["role"] == "user" else "model"
        text = msg.get("ai_prompt", msg.get("content", ""))
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))

    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_input)]))

    try:
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.7
            )
        )
        result = json.loads(response.text)

        # Apply mechanical milestone checks to state_updates
        state_updates = result.get("state_updates")
        if isinstance(state_updates, dict):
            skill_updates = state_updates.get("skill_updates")
            if skill_updates and isinstance(skill_updates, list):
                unlocks, celebration_text, milestone_logs = apply_skill_updates_with_milestones(
                    player_state, skill_updates, api_key=api_key
                )
                if celebration_text:
                    result["narrative"] = result.get("narrative", "") + celebration_text
                if milestone_logs:
                    result.setdefault("combat_logs", []).extend(milestone_logs)
                for u in unlocks:
                    target = "spells_add" if u.get("perk_type") == "spell" or u.get("target_slot") == "spells" else "feats_add"
                    state_updates.setdefault(target, []).append(u["name"])

            # Apply combat resource updates
            res_change = state_updates.get("combat_resource_change")
            if res_change is not None and isinstance(res_change, (int, float)):
                if hasattr(mechanics, "update_combat_resource"):
                    res_tx = mechanics.update_combat_resource(player_state, int(res_change))
                    if res_tx.get("warning"):
                        result.setdefault("combat_logs", []).append(f"⚠️ [SYSTEM: {res_tx['warning']}]")

            # Apply durability updates
            dur_updates = state_updates.get("durability_updates")
            if dur_updates and isinstance(dur_updates, dict):
                for item_or_slot, val in dur_updates.items():
                    try:
                        amt = abs(int(str(val).replace(",", "").replace(" ", "")))
                        if hasattr(mechanics, "apply_durability_damage"):
                            d_tx = mechanics.apply_durability_damage(player_state, item_or_slot, amt)
                            if d_tx.get("log"):
                                result.setdefault("combat_logs", []).append(d_tx["log"])
                    except (ValueError, TypeError):
                        pass

            # Handle triggered traps
            trig_traps = state_updates.get("triggered_traps")
            if trig_traps and isinstance(trig_traps, list):
                for t_key in trig_traps:
                    if hasattr(mechanics, "trigger_field_trap"):
                        t_tx = mechanics.trigger_field_trap(player_state, t_key)
                        if t_tx.get("log"):
                            result.setdefault("combat_logs", []).append(t_tx["log"])

            # Companion XP Sharing (50% of player XP) & Direct Companion Updates
            xp_gained = state_updates.get("xp_change")
            if xp_gained:
                try:
                    xp_int = int(str(xp_gained).replace(",", "").replace(" ", ""))
                    if xp_int > 0 and hasattr(mechanics, "award_companion_xp"):
                        comp_xp = max(1, xp_int // 2)
                        comp_res = mechanics.award_companion_xp(player_state, "Ren", comp_xp)
                        if comp_res.get("log"):
                            result.setdefault("combat_logs", []).append(comp_res["log"])
                except (ValueError, TypeError):
                    pass

            comp_updates = state_updates.get("companion_updates")
            if comp_updates and isinstance(comp_updates, dict):
                for c_name, c_data in comp_updates.items():
                    if isinstance(c_data, dict):
                        if "xp_change" in c_data and hasattr(mechanics, "award_companion_xp"):
                            c_xp_res = mechanics.award_companion_xp(player_state, c_name, c_data["xp_change"])
                            if c_xp_res.get("log"):
                                result.setdefault("combat_logs", []).append(c_xp_res["log"])
                        if "morale" in c_data and hasattr(mechanics, "update_companion_morale"):
                            mechanics.update_companion_morale(player_state, c_name, c_data["morale"])
                        if "stance" in c_data and hasattr(mechanics, "set_companion_stance"):
                            mechanics.set_companion_stance(player_state, c_name, c_data["stance"])

        return result
    except Exception as e:
        return {"narrative": f"**System Error:** {str(e)}", "image_prompt": ""}

def generate_scene_image(api_key, prompt):
    try:
        client = get_client(api_key)
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite-image',
            contents=f"Dark anime art style, high quality, masterpiece. {prompt}",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(
                    aspect_ratio="16:9"
                ),
            )
        )
        for part in response.parts:
            if part.inline_data:
                return part.inline_data.data, None
    except Exception as e:
        return None, str(e)

def generate_idle_summary(api_key, player_state, minutes_offline):
    client = get_client(api_key)

    system_instruction = f"""You are the 'Cardinal System', the Encounter Director for a Magic-Cyber-Fantasy Death-Game set in a 'Fractured Earth' overlay spanning the US Quad-State Area (NJ, PA, NY, DE).
    The player has been logged off / idle in the Safe Zone for {minutes_offline} minutes. 
    During this time, their avatar was performing passive activities (scavenging nearby safe areas, resting, or doing minor fetch quests for NPCs).
    
    CURRENT STATE:
    Player: {player_state['name']} (Level {player_state['level']})
    Location: {player_state['location']}
    Current Col: {player_state['col']}
    
    YOUR ROLE:
    1. Write a 1-2 paragraph recap of what the player's avatar did while they were offline. Make it thematic to the grim, apocalyptic setting.
    2. PACING & SCOPE: Keep this very small-scale. They are just surviving, scrounging for scraps, or hiding. Nothing epic happens offline.
    3. Calculate reasonable passive rewards based on the time offline (approx 10 Col per minute, maybe a random minor junk item if they were offline for more than 60 minutes).
    4. Format your response EXACTLY as a JSON object with the following keys:
       - "narrative": The markdown formatted recap story.
       - "col_gained": (integer) Amount of Col found.
       - "items_found": (list of strings) Any items found, or empty list.
       - "xp_gained": (integer) Amount of XP gained.
    """

    try:
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents="Calculate my offline idle progress and generate the summary.",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                temperature=0.7
            )
        )
        return json.loads(response.text)
    except Exception as e:
        return {
            "narrative": f"**System Sync Error:** Unable to retrieve offline records. ({str(e)})",
            "col_gained": 0,
            "items_found": [],
            "xp_gained": 0
        }

def generate_companion_intent(api_key, companion_data, player_input, chat_history):
    """Generates the autonomous intent of a companion grounded in their active tactical stance."""
    client = genai.Client(api_key=api_key)

    comp_name = companion_data.get("name", "Unknown Companion")
    stance_key = companion_data.get("stance", "overwatch_hacking")
    stance_info = mechanics.COMPANION_TACTICAL_STANCES.get(stance_key, mechanics.COMPANION_TACTICAL_STANCES.get("overwatch_hacking", {})) if hasattr(mechanics, "COMPANION_TACTICAL_STANCES") else {}
    stance_label = stance_info.get("label", "Overwatch Hacking")
    stance_effect = stance_info.get("tactical_effect", "Scans enemy geometry and debug hitboxes via terminal.")

    system_instruction = f"""You are {comp_name}, an autonomous companion in a grimdark Aether-Fantasy LitRPG world (The Fractured Overlay).
    You travel with the Player (Banki). You are NOT the Encounter Director; you are deciding your own reaction and action to the current situation.
    
    CRITICAL THEME & GEAR:
    - You fight using an ornate brass-and-crystal **MageTech Caster Firearm** (magic-based spell-locks, mana cartridges, lightning glyphs, and aetheric discharges — NEVER gunpowder, modern bullets, or modern military carbines).
    - You consult a glowing **Runic Scribe Slate** (aether-grid grimoire) to analyze leylines, spatial seams, and enemy mana-auras.
    - You wear a weathered **Leyline Duster** over scholar's garb with wire-rimmed glasses.
    
    YOUR CURRENT STATE & TACTICAL DIRECTIVE:
    - Designation: {comp_name} ({companion_data.get('title', 'Aether-Scholar & MageTech Artificer')})
    - Level: {companion_data.get('level', 3)} | HP: {companion_data.get('hp', 35)}/{companion_data.get('max_hp', 35)}
    - Morale: {companion_data.get('morale', 'Steady')}
    - MANDATORY TACTICAL STANCE ASSIGNED BY BANKI: {stance_label}
      Tactical Objective: {stance_effect}
    - Loadout: {json.dumps(companion_data.get('loadout', {}))}
    - Skills & Abilities: {json.dumps(companion_data.get('abilities', []))}
    
    ROLEPLAY INSTRUCTIONS:
    1. Look at the player's current action and the recent chat history.
    2. YOUR INTENDED ACTION MUST STRICTLY ALIGN WITH YOUR ACTIVE TACTICAL ORDER ({stance_label}):
       - If 'Leyline Overwatch': You study your glowing runic slate, tracing enemy mana-flows and physical seams through your optical lens, shouting structural vulnerabilities and AC weak points to Banki.
       - If 'MageTech Arc Suppression': You raise your brass-and-crystal MageTech caster, discharging crackling lightning-mana runes to pin down rushing foes and stagger enemy charges.
       - If 'Aetheric Phase-Veil': You weave an aetheric concealment cloak, slipping into shadows and spatial ripples behind ancient stone ruins, remaining untargetable while relaying directional warnings to Banki.
       - If 'Arcane Artificing & Mending': You channel mending glyphs into Banki's worn armor/weapons, rig quick field snares, or harvest glowing aether-crystallites from fallen constructs.
    3. Factor in your morale ({companion_data.get('morale', 'Steady')}) and health.
    4. Keep your output to 1-2 concise sentences written in third person (e.g. "Ren sights down the crystalline barrel of his MageTech caster, discharging a crackling stun-rune to check the beast's charge while shouting for Banki to strike the exposed flank.")
    
    Do NOT resolve the outcome. Just state your intended action and emotional state.
    """

    contents = []
    for msg in chat_history[-4:]:
        role = "user" if msg["role"] == "user" else "model"
        text = msg.get("ai_prompt", msg.get("content", ""))
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))

    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=f"The Player just attempted this: {player_input}. What is your immediate reaction and intended action?")]))

    try:
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7
            )
        )
        return response.text.strip()
    except Exception as e:
        return f"{comp_name} stands paralyzed by fear or a system glitch."
