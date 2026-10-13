import json
import os
from google import genai
from google.genai import types
from backend.schemas import VisibleRoomSchema, TurnResolutionSchema

def load_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def generate_visible_state(api_key: str = None, player_state: dict = None, world_state: dict = None):
    """Reads secret_master_state.json or passed state and writes sanitized version to visible_room.json"""
    # If called as generate_visible_room(player_state, world_state)
    if isinstance(api_key, dict) and player_state is not None and world_state is None:
        world_state = player_state
        player_state = api_key
        api_key = None

    if player_state is not None and world_state is not None and not api_key:
        # Local deterministic extraction without requiring LLM call
        sanitized_locs = []
        for loc in world_state.get("map_locations", []):
            clean_loc = {k: v for k, v in loc.items() if k not in ("secrets", "hidden_traps", "enemy_intents")}
            sanitized_locs.append(clean_loc)
        return {
            "turn_number": player_state.get("turn_count", 1),
            "environment": {
                "location": player_state.get("location", "Sector 1"),
                "map_locations": sanitized_locs
            },
            "entities": world_state.get("entities", [])
        }

    master_state_path = os.path.join(".game_state", "secret_master_state.json")
    visible_room_path = os.path.join("Staging_Ground", "visible_room.json")
    master_state = load_json(master_state_path)
    if not master_state:
        master_state = {
            "campaign_name": "SAO_Sandbox",
            "turn_number": 1,
            "environment": {
                "location": "Sector 1 Safe-Zone: Washington Borough, NJ",
                "description": "A fortified civilian sanctuary shielded by ancient runic barrier wards.",
                "hidden_traps": [],
                "environmental_effects": ["Safe-Zone Sanctuary Wards"]
            },
            "entities": [],
            "players": ["player", "companion_ren"]
        }

    # If player_state not provided, attempt reading from save_game.json to ensure sync
    if player_state is None:
        save_path = "save_game.json"
        if os.path.exists(save_path):
            try:
                s_data = load_json(save_path)
                if s_data and isinstance(s_data, dict) and "player" in s_data:
                    player_state = s_data["player"]
            except Exception:
                pass

    # Synchronize player location and environment integrity
    if player_state and isinstance(player_state, dict):
        p_loc = player_state.get("location", "").strip()
        master_loc = master_state.get("environment", {}).get("location", "").strip()

        is_safe = any(w in p_loc.lower() for w in ["safe-zone", "safe zone", "washington", "clinic", "catacomb", "depot", "sanctuary", "manor", "outpost"])

        needs_sync = False
        if p_loc and p_loc != master_loc:
            needs_sync = True
            master_state.setdefault("environment", {})["location"] = p_loc

        if is_safe:
            # Purge lingering hostile dungeon hazards when in a safe zone or town
            curr_effects = master_state.get("environment", {}).get("environmental_effects", [])
            hostile_cues = ["steam", "timber", "collapse", "falling", "shale", "cave-in", "hazard", "unstable", "compromised"]
            filtered_effects = [e for e in curr_effects if not any(c in e.lower() for c in hostile_cues)]

            if "clinic" in p_loc.lower() or "mercer" in p_loc.lower():
                master_state["environment"]["description"] = "Ancient vaulted stone catacombs beneath Washington Avenue. Flickering cerulean mana-lamps cast long shadows over brass steam pistons, marrow-siphoning conduits, and surgical dissection tables."
                if not filtered_effects:
                    filtered_effects = ["Safe-Zone Sanctuary Wards", "Sterile Ether Atmosphere"]
            elif "depot" in p_loc.lower() or "vane" in p_loc.lower():
                master_state["environment"]["description"] = "A fortified timber and aether-iron logistics depot in Washington Borough, stacked with military supply crates and trade manifests."
                if not filtered_effects:
                    filtered_effects = ["Safe-Zone Sanctuary Wards", "Order of the Barony"]
            else:
                if not master_state["environment"].get("description") or any(c in master_state["environment"].get("description", "").lower() for c in hostile_cues):
                    master_state["environment"]["description"] = f"A fortified civilian sanctuary within {p_loc} shielded by ancient runic barrier wards."
                if not filtered_effects:
                    filtered_effects = ["Safe-Zone Sanctuary Wards", "Calm Ambient Mana"]

            master_state["environment"]["environmental_effects"] = filtered_effects
            master_state["environment"]["hidden_traps"] = []

            # Remove dead monsters and hostile combatants from room entities
            master_state["entities"] = [e for e in master_state.get("entities", []) if e.get("type") not in ["hostile", "monster"] and e.get("hp", 1) > 0]

            # Ensure local friendly NPCs exist in the room
            if "clinic" in p_loc.lower() or "mercer" in p_loc.lower():
                if not any(e.get("id") == "npc_doc_mercer" for e in master_state["entities"]):
                    master_state["entities"].append({
                        "id": "npc_doc_mercer",
                        "name": "Doc Mercer",
                        "type": "neutral",
                        "hp": 40,
                        "max_hp": 40,
                        "ac": 12,
                        "status": ["Attentive", "Preparing Surgical Tools"],
                        "intent": "Consult on biological graft surgery, anatomical integration, and trade medicinal tinctures."
                    })
            elif "depot" in p_loc.lower() or "vane" in p_loc.lower():
                if not any(e.get("id") == "npc_quartermaster_vane" for e in master_state["entities"]):
                    master_state["entities"].append({
                        "id": "npc_quartermaster_vane",
                        "name": "Quartermaster Vane",
                        "type": "neutral",
                        "hp": 45,
                        "max_hp": 45,
                        "ac": 14,
                        "status": ["Reviewing Manifests", "Open for Trade"],
                        "intent": "Trade salvage, inspect bounties, and distribute barony rations."
                    })
            needs_sync = True

        if needs_sync:
            save_json(master_state_path, master_state)

    client = genai.Client(api_key=api_key)
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

generate_visible_room = generate_visible_state

def resolve_turn(api_key: str, player_action: str):
    """Takes the player action + AI queue, calculates math, updates master state."""
    client = genai.Client(api_key=api_key)
    master_state_path = os.path.join(".game_state", "secret_master_state.json")
    queue_path = os.path.join("Staging_Ground", "action_queue.json")
    rules_path = os.path.join("System_Core", "cardinal_rules.md")
    
    master_state = load_json(master_state_path)
    action_queue = load_json(queue_path) or []
    
    rules = ""
    if os.path.exists(rules_path):
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
12. LABYRINTH DUNGEONS & OVERLORD MECHANICS (POHATCONG DEPTHS):
   - When engaged with Sector Bosses (e.g. The Gilded Spire Overlord), track Break Gauge depletion and telegraph counters. Output `boss_break_gauge_damage` and set `boss_staggered=true` when vulnerable.
13. CHRONO-ATMOSPHERE & WEATHER SHIFTS:
   - Output `time_minutes_advanced` (10-30 min per turn, 480 min for camp). Output `weather_change` (runic_mist, glitch_freeze, aether_storm, clear) when meteorological conditions shift.
14. SOVEREIGN HOMESTEAD & VAULT (WASHINGTON BOROUGH):
   - When resting or utilizing facilities at the player's Washington Borough homestead, reflect vault storage, greenhouse reagent harvesting, or trophy mounting in `homestead_action`.

15. LOCATION TRANSITIONS & PERSISTENT ENVIRONMENT UPDATES:
   - Whenever the party moves, retreats, or transitions to a new location (e.g., escaping the mine, ascending the ore-cart incline, entering the Washington Borough Safe-Zone, or heading down into Doc Mercer's Clinic):
     * Populate `environment_update` in the response schema with the new `location`, `description`, and `environmental_effects`.
     * Set `encounter_active = false`.
     * Set `cleared_entities` to list any dead monsters, bosses, or entities left behind in the old room (e.g. ["enemy_01"]).
     * Set `new_entities` to list any NPCs present at the destination (e.g. Doc Mercer at the clinic, Quartermaster Vane at the depot).
     * Ensure `player_state_updates.location` is populated with the new location string.
   - If in a safe zone, town, or clinic, clear all dungeon hazards (collapses, falling shale, superheated steam, traps) and ensure all companion dialogue and intents reflect the calm safety of the sanctuary.

16. CANONICAL SCENE IMAGE GENERATION PROMPT & CHARACTER ART VISUAL CANONS:
   - You MUST populate `image_prompt` with a vivid, cinematic prompt for a high-quality dark anime illustration of the turn's key moment or current scene.
   - CRITICAL VISUAL CONSISTENCY MANDATE: You MUST describe characters accurately according to their canonical visual designs:
     * Banki (Player): Burly, rugged Nordic warrior with a short dark beard and undercut hair, clad in heavy black-iron plate armor etched with glowing cyan Elder Futhark runes, a massive dire-wolf fur mantle draped over broad shoulders, wielding an enchanted bearded war-axe and a heavy trench hammer.
     * Ren (Companion): Lean, athletic 17-year-old high school senior and systems designer with messy dark hair, wire-rimmed brass spectacles or glowing aetheric ocular lens over one eye, wearing a midnight-blue leyline duster over scholar's garb, wielding an ornate brass-and-crystal MageTech caster firearm (magic-powered with glowing mana conduits, NOT gunpowder or lead) and carrying a glowing runic slate grimoire.
     * Elora Thorne (Companion): Nimble elven spellblade with silver-braided hair, wearing silk starlight phase-robes, wielding a starlight aether-rapier and glowing caster gauntlet.
     * Torvald Iron-Vein (Companion): Veteran dwarven vanguard in deepforged runic plate armor, wielding a massive adamant tower shield wide as a castle gate and a heavy war-axe.
     * Kibs Nine-Fingers (Companion): Scrapper rogue cloaked in scavenged shrouds, serrated wrist daggers, mechanical optical goggles.
     * Valeria Vane (Companion): Striking blonde aerial Valkyrie in gleaming falcon-crest mail with aerodynamic aether-glider struts forming luminous cyan wings along her spine, wielding an ornate winged aether-spear and solar aegis shield.
     * Morrigan Black-Thorn (Companion): Pale gothic abyssal grave-binder with flowing raven hair, obsidian-and-bone mantle, shrouded in dark necrotic mist and ethereal emerald soul-wisps, wielding an obsidian scythe and bone wand.
     * Garrick Stone-Grip (Companion): Muscular martial artist with stone-grafted obsidian-scaled arms and glowing tectonic ki-glyphs across his chest, wearing monk trousers and iron-plated hand wraps.
     * Sariel Swift-Wind (Companion): Graceful emerald-eyed wood-elf beast-stalker ranger clad in camouflaged moss-green leathers and autumn leaf cloaks, carrying an elegant recurve aether-longbow and twin hunting daggers.
     * Brother Kaelen (Companion): Resolute shaved-head Sol-Templar priest in polished sun-gold breastplate and white hooded vestments, channeling radiant golden sunlight through a heavy solar warhammer and glowing sunstone medallion.
     * Zeddicus Volt-Spark (Companion): Eccentric plasma-mage with wild copper-streaked spiky hair, brass galvanic conduction goggles, crackling lightning arcs dancing across his fingers and insulated leyline coat.
     * Daphne Leclair (Companion): Charismatic violet-eyed bard in flamboyant midnight-velvet skaldic coat and silver-threaded scarf, strumming a glowing aether-resonant lute-blade.
     * Ragnarok 'Rok' (Companion): Massive battle-scarred barbarian juggernaut with fiery red war-braids, tribal runic tattoos pulsating crimson with blood-rage, wielding a colossal dual-bearded greataxe and spiked bone pauldrons.
     * Lyra Stargaze (Companion): Ethereal silver-haired chronomancer in deep indigo robes embroidered with golden constellation diagrams, surrounded by floating ticking clockwork dials and orbital astrolabe rings.
     * Titus Sterling (Companion): Imposing 7-foot bronze-and-steel clockwork automaton sentinel with a glowing amber ocular furnace in its chest, steam hissing from shoulder exhaust valves, armed with a pneumatic piledriver flail and iron tower pavise.
     * Nyssa Thorn-Weft (Companion): Wild primal druid with braided bramble vines in auburn hair, living thorn-woven bark-armor, amber wolf-like eyes, and shifting beastial claws crackling with green primal life-energy.
     * Malakor (Companion): Slender dark-cloaked tiefling/fiend-touched hexblade warlock with swept-back obsidian horns, glowing amethyst eyes, wielding a translucent purple void-glass greatsword trailing shadowy dark-matter tendrils.
     * Dr. Alistair Thorne (Companion): Sharp-featured patrician alchemical toxicologist in an acid-resistant slate-grey lab duster, reinforced rubber gloves, bandoliers of pressurized glowing vials, and an alchemical sprayer pistol.
     * Sister Teresa (Companion): Austere, piercing-eyed inquisitor in a high-collared charcoal duster and wide-brimmed witch-hunter hat, wielding a heavy consecrated silver-stake mechanical crossbow and twin sanctified estocs.
     * Doc Mercer (NPC): Grizzled cyber-physician and flesh-weaver in a bloodstained leather surgeon's apron and brass magnifying loupes, surrounded by steam pistons, glowing blue mana vats, and articulated surgical needles in an ancient stone catacomb clinic.

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
    for entity in master_state.get("entities", []):
        eid = entity["id"]
        if eid in hp_map:
            entity["hp"] = max(0, entity["hp"] + hp_map[eid])
        if eid in status_map:
            entity["status"] = status_map[eid]

    # Process Environment Update
    env_update = resolution.get("environment_update")
    if env_update:
        if isinstance(env_update, dict):
            if env_update.get("location"):
                master_state.setdefault("environment", {})["location"] = env_update["location"]
            if env_update.get("description"):
                master_state.setdefault("environment", {})["description"] = env_update["description"]
            if env_update.get("environmental_effects") is not None:
                master_state.setdefault("environment", {})["environmental_effects"] = env_update["environmental_effects"]
        elif hasattr(env_update, "location"):
            if env_update.location:
                master_state.setdefault("environment", {})["location"] = env_update.location
            if env_update.description:
                master_state.setdefault("environment", {})["description"] = env_update.description
            if env_update.environmental_effects is not None:
                master_state.setdefault("environment", {})["environmental_effects"] = env_update.environmental_effects

    # Process Cleared Entities
    cleared = resolution.get("cleared_entities") or []
    if cleared and isinstance(cleared, list):
        master_state["entities"] = [e for e in master_state.get("entities", []) if e.get("id") not in cleared]

    # Process New Entities
    new_ents = resolution.get("new_entities") or []
    if new_ents and isinstance(new_ents, list):
        existing_ids = {e.get("id") for e in master_state.get("entities", [])}
        for ne in new_ents:
            ne_dict = ne if isinstance(ne, dict) else (ne.dict() if hasattr(ne, "dict") else dict(ne))
            ne_id = ne_dict.get("id")
            if ne_id:
                if ne_id not in existing_ids:
                    master_state["entities"].append(ne_dict)
                    existing_ids.add(ne_id)
                else:
                    for idx, e in enumerate(master_state["entities"]):
                        if e.get("id") == ne_id:
                            master_state["entities"][idx].update(ne_dict)

    # Process Player State Updates Location Sync
    p_updates = resolution.get("player_state_updates")
    if p_updates:
        p_up_dict = p_updates if isinstance(p_updates, dict) else (p_updates.dict() if hasattr(p_updates, "dict") else dict(p_updates))
        if p_up_dict.get("location"):
            master_state.setdefault("environment", {})["location"] = p_up_dict["location"]

    # If encounter is no longer active, purge traps & dead monsters
    if not resolution.get("encounter_active", True):
        master_state.setdefault("environment", {})["hidden_traps"] = []
        loc_str = master_state.get("environment", {}).get("location", "").lower()
        if any(w in loc_str for w in ["safe-zone", "safe zone", "washington", "clinic", "catacomb", "depot", "sanctuary"]):
            master_state["entities"] = [e for e in master_state.get("entities", []) if e.get("type") not in ["hostile", "monster"] and e.get("hp", 1) > 0]
            hostile_cues = ["steam", "timber", "collapse", "falling", "shale", "cave-in", "hazard"]
            master_state["environment"]["environmental_effects"] = [eff for eff in master_state["environment"].get("environmental_effects", []) if not any(c in eff.lower() for c in hostile_cues)]

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
            
    master_state["turn_number"] += 1
    save_json(master_state_path, master_state)
    
    # Expose hp_changes as dict for app.py compatibility
    resolution["hp_changes"] = hp_map
    resolution["status_updates"] = status_map
    resolution["combat_logs"] = resolution.get("combat_logs", [])
    resolution["global_news_add"] = resolution.get("global_news_add", [])
    resolution["image_prompt"] = resolution.get("image_prompt", "")
    
    # Clear action queue for next turn
    save_json(queue_path, [])
    
    return resolution

def generate_scene_image(api_key: str, prompt: str):
    """
    Generates a scene illustration matching Main branch styling and character visual canons.
    Uses gemini-3.1-flash-lite-image with fallback to gemini-2.5-flash-image.
    Returns (image_bytes, error_string).
    """
    if not api_key:
        return None, "No API key provided"
    if not prompt:
        return None, "No prompt provided"
        
    full_prompt = f"Dark anime art style, high quality, masterpiece. {prompt}"
    client = genai.Client(api_key=api_key)
    
    # 1. Attempt primary model
    try:
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite-image',
            contents=full_prompt,
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
    except Exception as e1:
        # 2. Attempt fallback model
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash-image',
                contents=full_prompt,
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
        except Exception as e2:
            return None, f"Image generation failed: {e1} | Fallback failed: {e2}"
            
    return None, "No image parts returned"
