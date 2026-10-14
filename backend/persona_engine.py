import json
import os
from google import genai
from google.genai import types
from backend.schemas import EntityPersonaSchema, ActorActionSchema

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTITIES_DIR = os.path.join(BASE_DIR, "Entities")
PARTY_DIR = os.path.join(BASE_DIR, "Party")
STAGING_DIR = os.path.join(BASE_DIR, "Staging_Ground")

def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def forge_entity_persona(api_key: str, entity_id: str, raw_name: str = "", entity_type: str = "hostile", environment: dict = None) -> dict:
    """
    Spawns and interviews a unique SubAgent for an NPC or Monster.
    Generates their full life story, personality, quirks, dreams, and fears.
    Persists their file in Entities/{entity_id}.json.
    """
    entity_file = os.path.join(ENTITIES_DIR, f"{entity_id}.json")
    existing = load_json(entity_file)
    if existing:
        return existing

    client = genai.Client(api_key=api_key)
    env_desc = environment.get("description", "A hostile subterranean sector") if environment else "A hostile sector"
    env_loc = environment.get("location", "Sector 1") if environment else "Sector 1"

    prompt = f"""You are the Soul-Forge of the Crucible. A new SubAgent is being awakened into Earth's Eldritch Terraforming integration.
The setting is high-fantasy aether-punk and magetech (NOT modern military or cyberpunk). Technology is driven by ancient arcane matrices, runic clockwork, elemental crystals, and living golem craft.

Entity Designation: {entity_id}
Suggested Name / Archetype: {raw_name or entity_id}
Role / Alignment: {entity_type}
Current Environment: {env_loc} — {env_desc}


Interview this SubAgent and bring them to life with depth and psychological realism.
1. Ask them: "What has your life been up to now?" Have them recount their origins in first person (were they a mutated animal, an infected human survivor, an ancient pre-collapse excavator, or an alien bio-construct?).
2. Define their unique personality, strange quirks (ticks, vocal patterns, sensory habits).
3. Reveal their deepest dreams/desires, and their darkest fears/dreads (what makes them break morale or rage?).
4. Define their tactical survival philosophy and a tight behavior prompt for combat/roleplay.

Output strictly conforming to the EntityPersonaSchema.
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=EntityPersonaSchema,
            temperature=0.7
        )
    )

    persona = json.loads(response.text)
    save_json(entity_file, persona)
    print(f"[SUBAGENT FORGED] {persona['name']} ({persona['id']}) awakened with full persona.", flush=True)
    return persona

def get_subagent_action(api_key: str, entity_id: str, visible_room: dict, player_action: str = "", player_state: dict = None) -> dict:
    """
    Prompts a specific SubAgent (Companion, NPC, or Monster) to decide their next action.
    They read ONLY their persona sheet, visible_room.json, and the player's current action/speech.
    Ensures all companions and NPCs know and address the human player by their actual entered name.
    """
    # Determine the human player's active name
    p_name = "Survivor"
    if player_state and isinstance(player_state, dict) and player_state.get("name"):
        p_name = str(player_state["name"]).strip()
    else:
        save_path = "save_game.json"
        if os.path.exists(save_path):
            try:
                s_d = load_json(save_path)
                if s_d and isinstance(s_d, dict) and "player" in s_d and s_d["player"].get("name"):
                    p_name = str(s_d["player"]["name"]).strip()
            except Exception:
                pass
    
    # 1. Load Persona
    persona_path = os.path.join(ENTITIES_DIR, f"{entity_id}.json")
    persona = load_json(persona_path)
    
    # Check if a mechanical character sheet exists in Party/
    party_path = os.path.join(PARTY_DIR, f"{entity_id}.json")
    party_sheet = load_json(party_path)

    # Built-in Tutorial Construct Personas (avoid extra LLM call during tutorial stages)
    tutorial_personas = {
        "npc_cardinal_arbiter": {
            "id": "npc_cardinal_arbiter",
            "name": "Cardinal Calibration Construct",
            "species_or_type": "Holographic System Arbiter",
            "role": "neutral",
            "backstory_interview": "Compiled at 03:00 UTC to calibrate newly integrated Sector 1 survivors before releasing them into Washington Borough, NJ.",
            "personality": "Clinical, sardonic, precise, and instructional.",
            "quirks": ["Projects floating blue telemetry glyphs", "Quotes survival statistics"],
            "dreams_and_desires": "Complete the survivor's 3-stage calibration without a fatal neural desync.",
            "fears_and_dreads": "Unrecoverable kernel exceptions.",
            "tactical_style": "Observational and instructional",
            "behavior_prompt": f"Guide {p_name} through Stage 1 Telemetry & Relic calibration and open the blast doors to Chamber II."
        },
        "tutorial_clockwork_sentinel": {
            "id": "tutorial_clockwork_sentinel",
            "name": "Clockwork Calibration Sentinel",
            "species_or_type": "Bronze-and-Aether Training Construct",
            "role": "hostile",
            "backstory_interview": "Forged in the Cardinal Crucible to test a survivor's physical weapon strikes, Armor Class evasion, and graft-harvesting instincts.",
            "personality": "Relentless, mechanical, telegraphed.",
            "quirks": ["Gears whir loudly before every cleaver swing", "Cyan core pulses when vulnerable"],
            "dreams_and_desires": "Test the survivor's martial readiness.",
            "fears_and_dreads": "Having its Clockwork Reflex Servo and Astral Bolt spell slate harvested.",
            "tactical_style": "Measured telegraphed melee strikes",
            "behavior_prompt": f"Deliver a telegraphed practice cleaver swing against {p_name} so they can counterattack and shatter your bronze core."
        },
        "tutorial_crucible_warden": {
            "id": "tutorial_crucible_warden",
            "name": "Aether-Forged Crucible Warden",
            "species_or_type": "Arcane Gate-Guardian Construct",
            "role": "hostile",
            "backstory_interview": "The final guardian of the Sector 1 Calibration Crucible, standing before the Spatial Teleportation Gate to Washington Borough, NJ.",
            "personality": "Imposing, resonant, arcane-shielded.",
            "quirks": ["Projects a shimmering violet Kinetic Ward that only spells and active powers can shatter"],
            "dreams_and_desires": "Force the survivor to awaken their spellcasting and active class power before entering Washington, NJ.",
            "fears_and_dreads": "Direct hits from Astral Bolt or active class techniques.",
            "tactical_style": "Defensive ward projection before the Teleportation Gate",
            "behavior_prompt": f"Project your Kinetic Ward before the Washington, NJ Teleportation Gate, challenging {p_name} to shatter it with Astral Bolt or an active power."
        }
    }

    # Fallback to Party or Tutorial Personas if persona missing
    if not persona:
        persona = party_sheet or tutorial_personas.get(entity_id)

    if not persona:
        # Forge on the fly if missing
        persona = forge_entity_persona(api_key, entity_id, raw_name=entity_id, environment=visible_room.get("environment"))

    # Sanitize any legacy placeholder names ("Banki", "{player_name}") into the player's real name
    def _sanitize_player_refs(val):
        if isinstance(val, str):
            return val.replace("Banki", p_name).replace("{player_name}", p_name).replace("[Player Name]", p_name)
        elif isinstance(val, list):
            return [_sanitize_player_refs(x) for x in val]
        elif isinstance(val, dict):
            return {k: _sanitize_player_refs(v) for k, v in val.items()}
        return val

    persona = _sanitize_player_refs(persona)

    # 2. Build mechanical gear & physical status context if available
    mech_lines = []
    if party_sheet:
        hp = party_sheet.get("hp")
        max_hp = party_sheet.get("max_hp")
        ac = party_sheet.get("ac")
        if hp is not None and max_hp is not None:
            mech_lines.append(f"- Current Health: {hp}/{max_hp} HP (Armor Class: {ac})")
        eq = party_sheet.get("equipped", {})
        if isinstance(eq, dict) and any(v and v != "None" for v in eq.values()):
            eq_strs = [f"{k}: {v}" for k, v in eq.items() if v and v != "None"]
            mech_lines.append(f"- Equipped Gear: {', '.join(eq_strs)}")
        grafts = party_sheet.get("active_grafts", [])
        if grafts:
            g_strs = [f"{g.get('name')} [{g.get('slot')} slot: {g.get('effect')}]" if isinstance(g, dict) else str(g) for g in grafts]
            mech_lines.append(f"- Active Grafts & Implants: {', '.join(g_strs)}")
        inv = party_sheet.get("inventory", [])
        if inv:
            inv_strs = [f"{i.get('name')} ({i.get('desc', '')})" if isinstance(i, dict) else str(i) for i in inv]
            mech_lines.append(f"- Tactical Inventory: {'; '.join(inv_strs)}")
            
    mechanical_section = ""
    if mech_lines:
        mechanical_section = "\nYOUR CURRENT PHYSICAL STATUS & TACTICAL LOADOUT:\n" + "\n".join(mech_lines) + "\n"

    # Special Lore & Mechanical Hooks for Ren (Serpent-Script + Diagnostic Subroutine) & Titus (1,200-lb Chassis)
    special_lore_section = ""
    if entity_id == "companion_ren":
        try:
            import backend.mechanics as mechanics
            ren_sub = mechanics.get_ren_subroutine_directive(player_state or {})
        except Exception:
            ren_sub = {
                "stage": 0,
                "title": "Human Mask Intact (Ouroboros Debug Shell)",
                "persona_directive": "Express visceral psychological dread when your Aetheric Ocular Lens renders enemies as Serpent-Script (`Ouroboros Kernel v3.14`) Python dictionaries (`visible_room['entities']`, `target.max_hp = [KERNEL_REDACTED]`)."
            }
        special_lore_section = f"""
SERPENT-SCRIPT (`OUROBOROS KERNEL v3.14`) OCULAR HUD & SUBROUTINE STATE (STAGE {ren_sub.get('stage', 0)} — {ren_sub.get('title', '')}):
- In-Universe Python Lore: When the Cardinal System integrated Earth, it assimilated Earth's dominant pre-collapse AI language (Python) as its neural-aetheric bridging syntax: **Serpent-Script (`Ouroboros Kernel v3.14`)**.
- Your **Aetheric Ocular Lens** is locked in an unprivileged `Ouroboros Debug Shell` reading ONLY `visible_room` (and blocked from `.game_state/secret_master_state.json`). You literally see glowing cyan Pythonic syntax overlaid on reality (e.g., `visible_room["entities"]`, `target.status`, `target.active_debuffs`, `target.max_hp = [KERNEL_REDACTED]`).
- Current Psychological/Subroutine Directive: {ren_sub.get('persona_directive', '')}
"""
    elif "titus" in entity_id.lower():
        special_lore_section = """
PHYSICAL MASS & FLOOR-INTEGRITY PROTOCOL (1,200 LBS):
- Your Cast-Iron Boiler Chassis weighs 1,200 lbs (`weight_lbs: 1200.0`, `-6` Stealth). If `Visible Room.environment.environmental_effects` mentions rotted timbers, wooden floorboards, rickety catwalks, or fragile bridges, explicitly acknowledge the structural load risk in your thought and action!
"""

    try:
        import backend.mechanics as _mech_p
        _p_prof = _mech_p.get_physical_profile(player_state or {})
        _p_gender_line = f"{_p_prof['gender']} ({_p_prof['pronouns']})"
    except Exception:
        _p_gender_line = "Male (he/him)"

    player_action_section = f"""
HUMAN PLAYER IDENTITY & CURRENT TURN ACTION:
- Human Player Name: {p_name}
- Human Player Sex / Gender & Pronouns: {_p_gender_line}
- Human Player's Speech / Action This Turn:
"{player_action or 'Observes and stands ready.'}"
"""

    # 3. Build the persona's subjective perception prompt
    prompt = f"""You are an autonomous SubAgent in a dark fantasy, aether-punk LitRPG death-game.
The setting is high-fantasy and magetech (NOT modern military or cyberpunk). Any firearms used (like MageTech carbines) channel condensed radiant mana or elemental charges, NEVER gunpowder or lead.
You are: {persona.get('name', entity_id)} ({persona.get('species_or_type', 'Creature')})
Role: {persona.get('role', 'entity')}


YOUR BACKSTORY (What your life has been up to now):
"{persona.get('backstory_interview', 'I survive in the dark.')}"

YOUR PSYCHE:
- Personality: {persona.get('personality', 'Cautious')}
- Quirks: {', '.join(persona.get('quirks', []))}
- Dreams & Goals: {persona.get('dreams_and_desires', 'Survival')}
- Deepest Fears: {persona.get('fears_and_dreads', 'Destruction')}
- Tactical Style: {persona.get('tactical_style', 'Aggressive')}
- Behavior Rule: {persona.get('behavior_prompt', 'Act tactically.')}
{mechanical_section}{special_lore_section}
WHAT YOU CAN CURRENTLY SEE (Visible Room):
{json.dumps(visible_room, indent=2)}
{player_action_section}
CRITICAL GROUNDING & NAMING RULES:
1. GROUNDING: Ground your thoughts and intended action strictly in `Visible Room.environment.location` and `Visible Room.environment.environmental_effects`.
   - If there are NO hostile entities in `Visible Room.entities` and no active collapse in `environmental_effects`, do NOT hallucinate cave-ins, falling shale, or active combat! Follow or coordinate with the Human Player's current action/speech naturally.
2. ABSOLUTE PLAYER NAME & PRONOUN MANDATE: The human player's entered character name is "{p_name}" ({_p_gender_line}).
   - In your internal thoughts, tactical plans, and spoken dialogue, ALWAYS refer to the human player as "{p_name}" and use their correct pronouns ({_p_gender_line}).
   - NEVER call them any placeholder name, legacy alias, or generic title!

Decide your next action based on your instincts, physical condition, available gear, fear level, and tactical goals.
Do not break character. Speak from your internal thought and declare your action.
Output strictly matching ActorActionSchema.
"""

    if not api_key:
        return {
            "actor_id": entity_id,
            "actor_name": persona.get("name", entity_id),
            "internal_thought": f"Tracking {p_name} ({_p_gender_line}) in the current chamber.",
            "intended_action": persona.get("behavior_prompt", "Stands ready."),
            "target_id": None,
            "dialogue": ""
        }

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ActorActionSchema,
            temperature=0.4
        )
    )

    action = json.loads(response.text)
    action["actor_name"] = persona.get("name", entity_id)
    return action

def run_all_room_subagents(api_key: str, visible_room: dict, active_party: list = None, player_action: str = "", player_state: dict = None) -> list:
    """
    Iterates through all entities in the visible room (Active Vanguard Companions, Monsters, NPCs).
    Each SubAgent decides their move autonomously based on their persona, stance, and visible threats.
    Writes all actions to Staging_Ground/action_queue.json and returns the list.
    """
    action_queue_path = os.path.join(STAGING_DIR, "action_queue.json")
    all_actions = []

    # 1. Process all active party companions (Ren, Elora, Torvald, Kibs)
    party_members = active_party if active_party else ["companion_ren"]

    party_ids = []
    
    for member in party_members:
        if isinstance(member, dict):
            c_id = member.get("id", member.get("entity_id", "companion_ren"))
        else:
            c_id = str(member)
        party_ids.append(c_id)
        
        try:
            c_action = get_subagent_action(api_key, c_id, visible_room, player_action=player_action, player_state=player_state)
            all_actions.append(c_action)
        except Exception as e:
            print(f"[SUBAGENT ERROR] Companion {c_id} action failed: {e}", flush=True)

    # 2. All visible entities (Monsters, NPCs)
    for entity in visible_room.get("entities", []):
        eid = entity.get("id")
        if not eid or eid in ["player"] or eid in party_ids:
            continue
            
        # Skip dead or inert slag entities
        statuses = [s.lower() for s in entity.get("status", [])]
        if any(dead_tag in statuses for dead_tag in ["dead", "inert", "destroyed", "slag", "defeated", "harvested"]):
            continue

        try:
            # Ensure they have a persona
            forge_entity_persona(
                api_key=api_key,
                entity_id=eid,
                raw_name=entity.get("name", eid),
                entity_type=entity.get("type", "hostile"),
                environment=visible_room.get("environment")
            )
            # Get their action
            sub_action = get_subagent_action(api_key, eid, visible_room, player_action=player_action, player_state=player_state)
            all_actions.append(sub_action)
        except Exception as e:
            print(f"[SUBAGENT ERROR] Action for {eid} failed: {e}", flush=True)

    # Save to Action Queue
    save_json(action_queue_path, all_actions)
    print(f"[ACTION QUEUE] Staged {len(all_actions)} autonomous SubAgent moves.", flush=True)
    return all_actions
