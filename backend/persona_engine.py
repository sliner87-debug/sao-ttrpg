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

def get_subagent_action(api_key: str, entity_id: str, visible_room: dict) -> dict:
    """
    Prompts a specific SubAgent (Companion, NPC, or Monster) to decide their next action.
    They read ONLY their persona sheet and visible_room.json.
    """
    client = genai.Client(api_key=api_key)
    
    # 1. Load Persona
    persona_path = os.path.join(ENTITIES_DIR, f"{entity_id}.json")
    persona = load_json(persona_path)
    
    # Check if a mechanical character sheet exists in Party/
    party_path = os.path.join(PARTY_DIR, f"{entity_id}.json")
    party_sheet = load_json(party_path)

    # Fallback to Party if persona missing
    if not persona:
        persona = party_sheet

    if not persona:
        # Forge on the fly if missing
        persona = forge_entity_persona(api_key, entity_id, raw_name=entity_id, environment=visible_room.get("environment"))

    # 2. Build mechanical gear & physical status context if available
    mech_lines = []
    if party_sheet:
        hp = party_sheet.get("hp")
        max_hp = party_sheet.get("max_hp")
        ac = party_sheet.get("ac")
        if hp is not None and max_hp is not None:
            mech_lines.append(f"- Current Health: {hp}/{max_hp} HP (Armor Class: {ac})")
        grafts = party_sheet.get("active_grafts", [])
        if grafts:
            g_strs = [f"{g.get('name')} [{g.get('slot')} slot: {g.get('effect')}]" if isinstance(g, dict) else str(g) for g in grafts]
            mech_lines.append(f"- Active Grafts & Implants: {', '.join(g_strs)}")
        inv = party_sheet.get("inventory", [])
        if inv:
            mech_lines.append(f"- Tactical Inventory: {', '.join([str(i) for i in inv])}")
            
    mechanical_section = ""
    if mech_lines:
        mechanical_section = "\nYOUR CURRENT PHYSICAL STATUS & TACTICAL LOADOUT:\n" + "\n".join(mech_lines) + "\n"

    # 3. Build the persona's subjective perception prompt
    prompt = f"""You are an autonomous SubAgent in a dark fantasy death-game.
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
{mechanical_section}
WHAT YOU CAN CURRENTLY SEE (Visible Room):
{json.dumps(visible_room, indent=2)}

Decide your next action based on your instincts, physical condition, available gear, fear level, and tactical goals.
Do not break character. Speak from your internal thought and declare your action.
Output strictly matching ActorActionSchema.
"""

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

def run_all_room_subagents(api_key: str, visible_room: dict) -> list:
    """
    Iterates through all entities in the visible room (Companions, Monsters, NPCs).
    Each SubAgent decides their move autonomously.
    Writes all actions to Staging_Ground/action_queue.json and returns the list.
    """
    action_queue_path = os.path.join(STAGING_DIR, "action_queue.json")
    all_actions = []

    # 1. Companion Ren (Always present in party)
    try:
        ren_action = get_subagent_action(api_key, "companion_ren", visible_room)
        all_actions.append(ren_action)
    except Exception as e:
        print(f"[SUBAGENT ERROR] Ren action failed: {e}", flush=True)

    # 2. All visible entities (Monsters, NPCs)
    for entity in visible_room.get("entities", []):
        eid = entity.get("id")
        if not eid or eid in ["player", "companion_ren"]:
            continue
            
        # Skip dead or inert slag entities
        statuses = [s.lower() for s in entity.get("status", [])]
        if any(dead_tag in statuses for dead_tag in ["dead", "inert", "destroyed", "slag"]):
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
            sub_action = get_subagent_action(api_key, eid, visible_room)
            all_actions.append(sub_action)
        except Exception as e:
            print(f"[SUBAGENT ERROR] Action for {eid} failed: {e}", flush=True)

    # Save to Action Queue
    save_json(action_queue_path, all_actions)
    print(f"[ACTION QUEUE] Staged {len(all_actions)} autonomous SubAgent moves.", flush=True)
    return all_actions
