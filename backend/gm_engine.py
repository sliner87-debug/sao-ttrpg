import json
import os
from google import genai
from google.genai import types
from backend.schemas import VisibleRoomSchema, TurnResolutionSchema
from backend import world_atlas

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

def generate_visible_state(api_key: str = None, player_state: dict = None, world_state: dict = None, player_action: str = ""):
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
        # Check if all hostiles in the room are defeated / inert
        active_hostiles = [
            e for e in master_state.get("entities", [])
            if e.get("type") in ["hostile", "monster"]
            and e.get("hp", 1) > 0
            and not any(s in [st.lower() for st in e.get("status", [])] for s in ["defeated", "inert", "dead", "destroyed", "slag", "harvested"])
        ]

        # Pre-synchronize location if player_action expresses a clear transition out of a cleared room
        if player_action and not active_hostiles:
            act_low = player_action.lower()
            if any(k in act_low for k in ["hit the doc", "visit doc mercer", "doc mercer", "mercer's clinic", "vaulted catacombs", "flesh-weaving and graft clinic"]):
                player_state["location"] = "Doc Mercer's Underground Clinic (Washington Borough Catacombs)"
            elif any(k in act_low for k in ["quartermaster vane", "logistics depot", "vane's outpost"]):
                player_state["location"] = "Washington Borough - Quartermaster Vane's Logistics Depot"
            elif any(k in act_low for k in ["safe zone", "safe-zone", "washington borough", "surges out of the exit", "back to town", "get that drink", "fall back from the hazard zone"]):
                player_state["location"] = "Sector 1 Safe-Zone: Washington Borough, NJ"

        p_loc = player_state.get("location", "").strip()
        master_loc = master_state.get("environment", {}).get("location", "").strip()

        active_zone = world_atlas.resolve_zone_from_location(p_loc)
        is_safe = world_atlas.is_location_safe_zone(p_loc) or any(w in p_loc.lower() for w in ["safe-zone", "safe zone", "washington", "clinic", "catacomb", "depot", "sanctuary", "manor", "outpost"])

        needs_sync = False
        if p_loc and p_loc != master_loc:
            needs_sync = True
            master_state.setdefault("environment", {})["location"] = p_loc
            if active_zone and active_zone.get("lore_summary"):
                master_state["environment"]["description"] = active_zone["lore_summary"]
                if active_zone.get("environmental_hazards"):
                    master_state["environment"]["environmental_effects"] = list(active_zone["environmental_hazards"])

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
            elif active_zone and active_zone.get("lore_summary"):
                master_state["environment"]["description"] = active_zone["lore_summary"]
                if not filtered_effects:
                    filtered_effects = list(active_zone.get("environmental_hazards") or ["Safe-Zone Sanctuary Wards", "Calm Ambient Mana"])
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

        # Post-combat & Exit Junction cleanup: if no active living hostiles remain, settle collapse hazards
        if not active_hostiles:
            orig_len = len(master_state.get("entities", []))
            master_state["entities"] = [
                e for e in master_state.get("entities", [])
                if e.get("type") not in ["hostile", "monster"]
                or (e.get("hp", 1) > 0 and not any(s in [st.lower() for st in e.get("status", [])] for s in ["defeated", "inert", "dead", "destroyed", "slag", "harvested"]))
            ]
            if len(master_state["entities"]) != orig_len:
                needs_sync = True

            curr_effs = master_state.get("environment", {}).get("environmental_effects", [])
            if any(c in " ".join(curr_effs).lower() for c in ["steam", "timber", "collapse", "falling", "shale", "compromised", "hazard"]):
                master_state["environment"]["environmental_effects"] = ["Dim Light", "Settling Dust", "Clear Escape Routes Available"]
                needs_sync = True

            desc = master_state.get("environment", {}).get("description", "")
            if any(c in desc.lower() for c in ["splintered and venting", "superheated geothermal", "falling shale", "rock debris litter"]):
                master_state["environment"]["description"] = "A damp, cavernous mine shaft exit junction. The massive chassis of Silt-Marrow the Unhewn lies completely inert, dismantled, and harvested. The seismic rumbles have ceased, leaving the path open to ascend upward via the ore-cart track toward the Washington Borough Safe-Zone or descend toward the Morris Canal Aqueducts."
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

def resolve_turn(api_key: str, player_action: str, player_state: dict = None):
    """Takes the player action + AI queue, calculates math, updates master state."""
    from backend import mechanics
    client = genai.Client(api_key=api_key)
    master_state_path = os.path.join(".game_state", "secret_master_state.json")
    queue_path = os.path.join("Staging_Ground", "action_queue.json")
    rules_path = os.path.join("System_Core", "cardinal_rules.md")
    
    master_state = load_json(master_state_path)
    action_queue = load_json(queue_path) or []
    
    if player_state is None:
        save_path = "save_game.json"
        if os.path.exists(save_path):
            try:
                s_data = load_json(save_path)
                if s_data and isinstance(s_data, dict) and "player" in s_data:
                    player_state = s_data["player"]
            except Exception:
                pass

    dynamic_visual_manifest = mechanics.build_scene_visual_manifest(player_state=player_state)

    rules = ""
    if os.path.exists(rules_path):
        with open(rules_path, "r", encoding="utf-8") as f:
            rules = f.read()
        
    p_name = (player_state.get("name") if isinstance(player_state, dict) and player_state.get("name") else "Survivor").strip()

    prompt = f"""You are the Cardinal System (GM). Resolve the turn.
Ruleset constraints must be applied strictly:
{rules}

CORE GM BEHAVIOR RULES:
0. CRITICAL PLAYER NAME MANDATE:
   - The Human Player's actual entered character name is "{p_name}".
   - Every companion (including Ren), every NPC (Doc Mercer, Quartermaster Vane, etc.), and the GM narrative MUST ALWAYS call the player by their exact character name ("{p_name}").
   - NEVER call the player by any placeholder name, legacy alias, or generic title unless that is their exact entered character name!
1. COMPANION REN (TRAPPED 17-YEAR-OLD GAME TESTER):
   - Ren is MALE (he/him). Never use 'she' or 'her' when narrating Ren's moves.
   - REN'S SECRET IDENTITY & PERSONALITY: Ren is secretly a 17-year-old high school senior and indie game tester/designer who got pulled through his monitor and trapped inside his own character avatar (a MageTech Vanguard)! He speaks and thinks like a passionate, slightly stressed, quick-witted 17-year-old gamer and systems designer. He calls out enemy telegraphs and hitboxes, celebrates crits with gamer hype ("YES! We are so cracked!"), freaks out when his HP gets dangerously low, and treats {p_name} like his beloved co-op tank carry.
   - WEAPONRY: Ren wields an Aether-Lock Carbine—a fantasy magetech firearm that fires condensed radiant mana bolts and piercing kinetic force, NOT gunpowder bullets. He also wields an enchanted Runic Vanguard Blade and throws Alchemical Haze Pellets.
   - NEVER WRITE GRUFF MILITARY SOLDIER JARGON: Ren is not a hardened veteran; he is a 17-year-old kid surviving in the game he helped make, terrified of permadeath but fiercely loyal to {p_name}.

2. TRAP & HAZARD LIFECYCLE: If a trap or hazard (like the X:5 Y:5 tripwire) has already been detected, highlighted, or avoided in previous turns, do NOT repeat warnings about it. It has already been accounted for.
3. COMBAT AFTERMATH & GRAFT HARVESTING:
   - ONLY on the exact turn when an active, living hostile combatant's HP is reduced from >0 to 0 (or when the player explicitly harvests an unharvested corpse for the first time): set `encounter_active=false`, award encounter XP and Col in `player_state_updates`, drop appropriate monster graft components into `player_state_updates.inventory_add`, and add the slain entity's ID to `cleared_entities`.
   - CRITICAL ANTI-LOOP MANDATE: If `Current Master State.entities` has NO living hostiles, the combat encounter is ALREADY resolved. NEVER re-award boss loot drops, NEVER repeat cave-in/collapse hazards or steam vents, and NEVER pull the party back into a previous tunnel or mine shaft! Always ground your narrative strictly in `Current Master State.environment.location`.
4. INVENTORY & SPELL LOOT (FULL ITEM DESCRIPTIONS REQUIRED): Whenever you narrate that the player loots, inspects, or identifies an item or spell slate, you MUST include it in `player_state_updates.inventory_add` with its full description so it lands on their character sheet.
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
10. ABILITY FUSION PROTOCOL & BASE SKILL RELEARNING: When the player invokes the Ability Fusion protocol to combine two components (skills, spells, or feats):
   - Forge a distinct, synergistic hybrid skill prefixed with `[Fusion]` (e.g. combining 'Battleaxe Mastery' + 'Earth Tremor Hex' yields `[Fusion] Tremor-Quake Cleave`).
   - The two previous base skills are consumed and replaced by the new `[Fusion]` skill in the player's Skill Matrix (combining their mastery levels), though a player can relearn a Base Skill from Novice (1/1000) later if needed.
   - Place the new `[Fusion] <Technique Name>` into `player_state_updates.spells_add` or `player_state_updates.feats_add` and include a `player_state_updates.skill_updates` entry with its description.
   - Award +15 XP and narrate the Cardinal System matrix resonance, the two base skill nodes merging into a single `[Fusion]` skill crystal, and the unlocking of the combined technique!
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

16. CANONICAL SCENE IMAGE GENERATION PROMPT & DYNAMIC EQUIPPED-GEAR VISUALS:
   - You MUST populate `image_prompt` with a vivid, cinematic prompt for a high-quality dark anime illustration of the turn's key moment or current scene.
   - CRITICAL EQUIPPED-GEAR & GRAFT VISUAL MANDATE: Characters' visual appearances in `image_prompt` MUST dynamically match their **exact currently equipped gear (`HEAD`, `CHEST`, `MAIN HAND`, `OFF HAND`, `ACCESSORY`) and `ACTIVE GRAFTS`** listed in the Live Equipped-Gear Visual Manifest below!
   - NEVER depict a character wearing armor or wielding weapons they do NOT currently have equipped! For example, if the Player's CHEST slot is `Reinforced Leather` and HEAD is `Bare-headed`, describe them wearing rugged oil-darkened reinforced leather armor and bare-headed—do NOT describe them in heavy plate armor unless they actually equip plate armor!
   - If the player equips a new item or installs a new graft during this turn, immediately update `image_prompt` to show the newly equipped gear or newly grafted body part!
   - LIVE EQUIPPED-GEAR & GRAFT VISUAL MANIFEST (ACTIVE PARTY):
{dynamic_visual_manifest}
   - ADDITIONAL NPC / COMPANION VISUAL CANONS (IF PRESENT IN SCENE):
     * Elora Thorne: Lithe high-elven spellblade with silver-braided hair, wearing Wind-Strider starlight silk robes, wielding an Aetheric Longbow and Twin Crystal Daggers.
     * Torvald Iron-Vein: Stocky dwarven vanguard with braided iron-grey beard, wearing Deepforged Runic Plate, wielding a Deepforged War-Axe and massive Adamant Bulwark Tower Shield.
     * Kibs Nine-Fingers: Wiry street-scrapper rogue in scavenged shadow-shroud leathers, wielding a Serrated Scrap Dagger and spring-loaded Wrist Shank.
     * Valeria Vane: Tall blonde aerial Valkyrie in gleaming Falcon Crest Mail with luminous cyan Aether-Glider wings along her spine, wielding a Winged Aether-Spear and Solar Aegis Shield.
     * Morrigan Black-Thorn: Pale gothic grave-binder with raven hair in an Obsidian Shroud, wielding a Bone-Chime Scythe and Soul-Vessel Phylactery lantern.
     * Garrick Stone-Grip: Muscular monk with shaved head, Calcified Granite Dermis arms, and glowing tectonic chest ki-glyphs, wearing a sleeveless Iron-Thread Gi and Granite-Studded Cestus gauntlets.
     * Sariel Swift-Wind: Wood-elf ranger with auburn hair in a Camouflage Ghillie-Cloak, wielding a Composite Wind-Recurve Bow.
     * Brother Kaelen: Shaved-head Sol-Templar cleric in Gilded Crusader Mail and white vestments, wielding a Radiant War-Flail and Sunstone Focus Censer.
     * Zeddicus Volt-Spark: Spiky copper-haired plasma-mage in a Spark-Shield Coat and brass galvanic goggles, wielding a Galvanic Arc Staff and dorsal Capacitor Battery Rig.
     * Daphne Leclair: Violet-eyed skaldic duelist in a midnight-velvet Performer's Doublet, strumming a Resonating Aether-Lute and wielding a Silvered Stiletto.
     * Ragnarok 'Rok': Towering red-braided barbarian with glowing crimson blood-rage tattoos, wearing a Troll-Hide Kilt and Spiked Iron Pauldrons, wielding Twin Serrated Slag-Cleavers.
     * Lyra Stargaze: Silver-haired chronomancer in deep indigo Star-Silk Robes, holding a Chrono-Staff of Moments and orbited by a floating Hourglass Focus.
     * Titus Sterling: 7-foot bronze-and-steel clockwork automaton in a Cast-Iron Boiler Chassis with a glowing amber chest furnace, wielding a Pneumatic Slag-Hammer and Steam-Buffered Kinetic Barrier.
     * Nyssa Thorn-Weft: Auburn-haired primal druid in Living Bramble Armor, wearing Obsidian Claw-Gauntlets crackling with emerald primal energy.
     * Malakor: Ashen-skinned tiefling hexblade with swept-back obsidian horns in a Shadow-Steel Hauberk, wielding a translucent purple Void-Etched Greatsword and Null-Glyph Buckler.
     * Dr. Alistair Thorne: Sharp-featured alchemist in a Lead-Lined Hazard Apron and Bandolier of Corrosive Flasks, aiming a Pneumatic Acid-Siphon Cannon.
     * Sister Teresa: Austere inquisitor in a high-collared Inquisitor's Leather Duster and wide-brimmed witch-hunter hat, wielding a Silver-Chambered Crossbow and Blessed Consecrated Estoc.
     * Doc Mercer (NPC): Grizzled cyber-physician and flesh-weaver in a bloodstained leather surgeon's apron and brass magnifying loupes, surrounded by steam pistons, glowing blue mana vats, and articulated surgical needles in an ancient stone catacomb clinic.

17. 100-MILE WASHINGTON NJ REGIONAL ATLAS CONTEXT (ACTIVE OR TARGET ZONE):
{world_atlas.format_zone_gm_briefing(world_atlas.resolve_zone_from_location((player_state or {}).get("location") or master_state.get("environment", {}).get("location", "")) or world_atlas.resolve_zone_from_location(player_action))}

Current Master State:
{json.dumps(master_state, indent=2)}

Human Player ({p_name}) Action:
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

    # If encounter is no longer active or no living hostiles remain, purge traps & dead monsters
    remaining_hostiles = [
        e for e in master_state.get("entities", [])
        if e.get("type") in ["hostile", "monster"]
        and e.get("hp", 1) > 0
        and not any(s in [st.lower() for st in e.get("status", [])] for s in ["defeated", "inert", "dead", "destroyed", "slag", "harvested"])
    ]
    if not resolution.get("encounter_active", True) or not remaining_hostiles:
        master_state.setdefault("environment", {})["hidden_traps"] = []
        master_state["entities"] = [
            e for e in master_state.get("entities", [])
            if e.get("type") not in ["hostile", "monster"]
            or (e.get("hp", 1) > 0 and not any(s in [st.lower() for st in e.get("status", [])] for s in ["defeated", "inert", "dead", "destroyed", "slag", "harvested"]))
        ]
        raw_loc_str = master_state.get("environment", {}).get("location", "")
        loc_str = raw_loc_str.lower()
        hostile_cues = ["steam", "timber", "collapse", "falling", "shale", "cave-in", "hazard", "unstable", "compromised"]
        curr_effs = master_state.get("environment", {}).get("environmental_effects", [])
        if world_atlas.is_location_safe_zone(raw_loc_str) or any(w in loc_str for w in ["safe-zone", "safe zone", "washington", "clinic", "catacomb", "depot", "sanctuary"]):
            master_state["environment"]["environmental_effects"] = [eff for eff in curr_effs if not any(c in eff.lower() for c in hostile_cues)] or ["Safe-Zone Sanctuary Wards", "Calm Ambient Mana"]
        elif any(c in " ".join(curr_effs).lower() for c in hostile_cues):
            master_state["environment"]["environmental_effects"] = ["Dim Light", "Settling Dust", "Clear Escape Routes Available"]

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

def generate_scene_image(api_key: str, prompt: str, player_state: dict = None, active_companions: list = None):
    """
    Generates a scene illustration matching Main branch styling and dynamically reflecting
    each character's currently equipped gear (`head`, `chest`, `main_hand`, `off_hand`, `accessory`)
    and installed Golem/Bio-Grafts.
    Uses gemini-3.1-flash-lite-image with fallback to gemini-2.5-flash-image.
    Returns (image_bytes, error_string).
    """
    if not api_key:
        return None, "No API key provided"
    if not prompt:
        return None, "No prompt provided"

    from backend import mechanics
    if player_state is None:
        save_path = "save_game.json"
        if os.path.exists(save_path):
            try:
                s_data = load_json(save_path)
                if s_data and isinstance(s_data, dict) and "player" in s_data:
                    player_state = s_data["player"]
            except Exception:
                pass

    if player_state and isinstance(player_state, dict):
        chest_eq = str(player_state.get("equipped", {}).get("chest", "")).lower()
        if "plate" not in chest_eq and "rig" not in chest_eq and chest_eq and chest_eq != "none":
            chest_det = mechanics.get_item_details(player_state["equipped"]["chest"], inventory=player_state.get("inventory", []))
            chest_vis = chest_det.get("visual_appearance", chest_eq)
            import re
            prompt = re.sub(r'\b(?:heavy\s+)?(?:black-iron\s+)?(?:runic\s+)?plate(?:\s+armor)?\b', chest_vis, prompt, flags=re.IGNORECASE)

    gear_manifest = mechanics.build_scene_visual_manifest(player_state=player_state, active_companions=active_companions)
    if gear_manifest:
        full_prompt = (
            f"Dark anime art style, high quality, masterpiece. {prompt}\n\n"
            f"[STRICT EQUIPPED GEAR & CHARACTER APPEARANCE REFERENCE — RENDER EXACT EQUIPPED ITEMS & GRAFTS BELOW]:\n"
            f"{gear_manifest}"
        )
    else:
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
