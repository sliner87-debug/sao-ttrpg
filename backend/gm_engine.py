import json
import os
from google import genai
from google.genai import types
from backend.schemas import VisibleRoomSchema, TurnResolutionSchema

def load_json(filepath):
    with open(filepath, "r") as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

def generate_visible_state(api_key: str):
    """Reads secret_master_state.json and writes sanitized version to visible_room.json"""
    client = genai.Client(api_key=api_key)
    master_state_path = os.path.join(".game_state", "secret_master_state.json")
    visible_room_path = os.path.join("Staging_Ground", "visible_room.json")
    master_state = load_json(master_state_path)
    
    prompt = f"""You are the Cardinal System (GM).
Here is the absolute truth of the encounter:
{json.dumps(master_state, indent=2)}

Strip away all secret mechanics (exact HP, hidden traps, enemy intents).
Return ONLY the data the players can clearly observe. Output EXACTLY matching the JSON schema.
"""
    
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VisibleRoomSchema,
            temperature=0.2
        )
    )
    
    visible_room = json.loads(response.text)
    save_json(visible_room_path, visible_room)
    print("Staging Ground updated: visible_room.json")
    return visible_room

def resolve_turn(api_key: str, player_action: str):
    """Takes the player action + AI queue, calculates math, updates master state."""
    client = genai.Client(api_key=api_key)
    master_state_path = os.path.join(".game_state", "secret_master_state.json")
    queue_path = os.path.join("Staging_Ground", "action_queue.json")
    rules_path = os.path.join("System_Core", "cardinal_rules.md")
    
    master_state = load_json(master_state_path)
    action_queue = load_json(queue_path)
    
    with open(rules_path, "r", encoding="utf-8") as f:
        rules = f.read()
        
    prompt = f"""You are the Cardinal System (GM). Resolve the turn.
Ruleset constraints must be applied strictly:
{rules}

CORE GM BEHAVIOR RULES:
1. COMPANION REN (TRAPPED 17-YEAR-OLD GAME TESTER):
   - Ren is MALE (he/him). Never use 'she' or 'her' when narrating Ren's moves.
   - REN'S SECRET IDENTITY & PERSONALITY: Ren is secretly a 17-year-old high school senior and indie game tester/designer who got pulled through his monitor and trapped inside his own character avatar (a MageTech Vanguard)! He speaks and thinks like a passionate, slightly stressed, quick-witted 17-year-old gamer and systems designer. He calls out enemy telegraphs and hitboxes, celebrates crits with gamer hype ("YES! We are so cracked!"), freaks out when his HP gets dangerously low, and treats Banki like his beloved co-op tank carry.
   - WEAPONRY: Ren wields an Aether-Lock Carbine—a fantasy magetech firearm that fires condensed radiant mana bolts and piercing kinetic force, NOT gunpowder bullets. He also wields an enchanted Runic Vanguard Blade and throws Alchemical Haze Pellets.
   - NEVER WRITE GRUFF MILITARY SOLDIER JARGON: Ren is not a hardened veteran; he is a 17-year-old kid surviving in the game he helped make, terrified of permadeath but fiercely loyal to Banki.

2. TRAP & HAZARD LIFECYCLE: If a trap or hazard (like the X:5 Y:5 tripwire) has already been detected, highlighted, or avoided in previous turns, do NOT repeat warnings about it. It has already been accounted for.
3. COMBAT AFTERMATH & GRAFT HARVESTING: When all hostiles are dead (HP <= 0), set encounter_active=false. 
   - Award significant encounter XP (e.g. 250 XP for Silt-Marrow) and Col (e.g. +75 Col) in player_state_updates.
   - Drop harvesting graft components into player_state_updates.inventory_add (e.g., "[Graft Component] Silt-Marrow's Geothermal Core Piston", "Basalt Carapace Plating x2").
   - Describe the collapse settling and open 1-2 clear exits: an emergency ore-cart incline ascending to the surface toward Washington Borough Safe-Zone, and a lower adit leading toward the Morris Canal Aqueducts.
4. INVENTORY & SPELL LOOT: Whenever you narrate that the player loots, inspects, or identifies an item or spell slate, you MUST include it in player_state_updates.inventory_add so it actually lands on their character sheet.
5. AUTONOMOUS SUBAGENTS: Each entity in the queue (Companions, Monsters, NPCs) is an autonomous SubAgent with their own quirks, fears, and tactical goals. Resolve how their queued actions collide with each other and with the Human Player's action.
6. MECHANICAL TRANSPARENCY & CLEAN NARRATIVE: Explicitly simulate all dice rolls, attacks vs AC, saving throws vs DC, and damage math in the `combat_logs` array. In `narrative_recap`, tell a dramatic, cinematic story WITHOUT embedding bracketed formulas like '[Attack: 1d20+5...]' in the story prose. Put all crunch into `combat_logs`.
7. SAFE-ZONE & LIVING WORLD (WASHINGTON BOROUGH): When players rest or interact in the Washington Borough Safe-Zone:
   - A 24-Hour Safe-Zone Rest fully restores HP for player and companions, clearing surgery and combat fatigue.
   - Generate 1-2 continental or regional news blurbs in `global_news_add` reflecting off-screen faction maneuvers, and update nearby nodes.
   - Highlight the local hub: Doc Mercer's Underground Clinic (surgery/grafts) and Quartermaster Vane's Barony Outpost (bounties/gear).
8. GRAFT SURGERY & STRAIN (DOC MERCER'S CLINIC): When players request graft surgery at Doc Mercer's clinic:
   - Verify anatomical slots ('head', 'torso', 'left_arm', 'right_arm', 'legs', 'spine').
   - Remove the installed graft item from `player_state_updates.inventory_remove`.
   - Deduct Doc Mercer's surgical fee (e.g. 25-50 Col) in `player_state_updates.col_change`.
   - Output installed graft into `player_state_updates.grafts_installed` with slot, name, strain (1-3), and mechanical effect.
   - If player's total Strain exceeds Strain Capacity (CON Mod + Level // 2), roleplay Doc Mercer's stern warning regarding Arcane Dissonance / Necrotic Rejection.
9. 1-1000 SKILL MASTERY & MILESTONES: Skills progress along the 1-1000 mastery continuum (Novice 1-49, Apprentice 50-99, Journeyman 100-249, Adept 250-499, Master 500-749, Grandmaster 750-999, Transcendence 1000).
   - Award +1 to +5 mastery gains in `player_state_updates.skill_updates` when players practice or use skills.
   - When crossing milestone thresholds, reward unique milestone perks in the description.
10. ABILITY FUSION PROTOCOL: When the player invokes the Ability Fusion protocol to combine two components (skills, spells, or feats):
   - Forge a distinct, synergistic hybrid technique (e.g. combining 'Battleaxe Mastery' + 'Earth Tremor Hex' yields 'Tremor-Quake Cleave').
   - Place the new technique into `player_state_updates.spells_add` or `player_state_updates.feats_add`.
   - Award +15 XP and +5-10 mastery points in relevant skills via `player_state_updates.skill_updates`.
   - Narrate the Cardinal System matrix resonance, holographic crystallization, and the player unlocking the combined technique!
11. HIGH-FANTASY MAGETECH THEME (OVER CYBERPUNK):
   - The world is dark fantasy infused with ancient aetheric artifice and runic machinery.
   - Prioritize magical/fantasy terminology: mana-crystallization, aether-ducts, runic glyphs, enchanted clockwork, and chimeric beast organs over pure cold cyberpunk, sterile microchips, or modern military hardware.



Current Master State:
{json.dumps(master_state, indent=2)}

Human Player Action:
"{player_action}"

Autonomous SubAgent Actions in Queue (Companions, Hostiles, Neutrals):
{json.dumps(action_queue, indent=2)}

Determine if attacks hit based on AC, update HP, and advance the turn.
Output matching TurnResolutionSchema.
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=TurnResolutionSchema,
            temperature=0.4
        )
    )
    
    resolution = json.loads(response.text)
    
    # Map lists of EntityHpChange and EntityStatusUpdate into dictionaries for state manipulation
    hp_map = {}
    for item in resolution.get("hp_changes", []):
        if isinstance(item, dict):
            hp_map[item["entity_id"]] = item["hp_delta"]
            
    status_map = {}
    for item in resolution.get("status_updates", []):
        if isinstance(item, dict):
            status_map[item["entity_id"]] = item["statuses"]
            
    # Apply updates to Master State
    for entity in master_state["entities"]:
        eid = entity["id"]
        if eid in hp_map:
            entity["hp"] = max(0, entity["hp"] + hp_map[eid])
        if eid in status_map:
            entity["status"] = status_map[eid]
            
    # Apply companion HP updates to Party/*.json files
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    party_dir = os.path.join(base_dir, "Party")
    for eid, delta in hp_map.items():
        p_path = os.path.join(party_dir, f"{eid}.json")
        if os.path.exists(p_path):
            try:
                p_sheet = load_json(p_path)
                if p_sheet and "hp" in p_sheet:
                    max_hp = p_sheet.get("max_hp", 35)
                    p_sheet["hp"] = max(0, min(max_hp, p_sheet["hp"] + delta))
                    save_json(p_path, p_sheet)
                    print(f"[GM ENGINE] Companion {eid} HP updated to {p_sheet['hp']}/{max_hp} (delta: {delta})", flush=True)
            except Exception as e:
                print(f"[GM ENGINE] Error updating companion {eid} sheet: {e}", flush=True)
            
    # If the encounter is resolved, clear traps so companions don't repeat them
    if not resolution.get("encounter_active", True):
        master_state["environment"]["hidden_traps"] = []
            
    master_state["turn_number"] += 1
    save_json(master_state_path, master_state)
    
    # Expose hp_changes as dict for app.py compatibility
    resolution["hp_changes"] = hp_map
    resolution["status_updates"] = status_map
    resolution["combat_logs"] = resolution.get("combat_logs", [])
    resolution["global_news_add"] = resolution.get("global_news_add", [])
    
    # Clear action queue for next turn
    save_json(queue_path, [])
    
    return resolution
