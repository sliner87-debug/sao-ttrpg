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

        # Two-Stage Scene-Gate State Machine: Prevent multi-hop teleportation past loot/streets!
        cur_loc_low = str(player_state.get("location", "") or master_state.get("environment", {}).get("location", "")).lower()
        in_dungeon_or_mine = any(w in cur_loc_low for w in ["mine", "shaft", "depths", "labyrinth", "quarry", "dungeon", "tunnel", "cavern", "beneath", "incline"]) and "clinic" not in cur_loc_low and "catacomb" not in cur_loc_low

        if player_action and not active_hostiles:
            act_low = player_action.lower()
            is_direct_ui_travel = "[direct_travel]" in act_low or "vaulted catacombs of doc mercer" in act_low or "step into quartermaster vane" in act_low
            if any(k in act_low for k in ["hit the doc", "visit doc mercer", "doc mercer", "mercer's clinic", "vaulted catacombs", "flesh-weaving and graft clinic"]):
                if in_dungeon_or_mine and not is_direct_ui_travel:
                    # STAGE 1 GATE: Exit the mine/dungeon to the Washington Borough Street Approach & Salvage Threshold first!
                    player_state["location"] = "Sector 1 Safe-Zone: Washington Borough, NJ (Mine-Head & Street Approach)"
                    player_state["pending_destination_hint"] = "Doc Mercer's Underground Clinic (Washington Borough Catacombs)"
                else:
                    # STAGE 2 GATE: Already in town/Safe-Zone (or explicit UI clinic button) -> enter Doc Mercer's Clinic
                    player_state["location"] = "Doc Mercer's Underground Clinic (Washington Borough Catacombs)"
                    player_state.pop("pending_destination_hint", None)
            elif any(k in act_low for k in ["quartermaster vane", "logistics depot", "vane's outpost"]):
                if in_dungeon_or_mine and not is_direct_ui_travel:
                    player_state["location"] = "Sector 1 Safe-Zone: Washington Borough, NJ (Mine-Head & Street Approach)"
                    player_state["pending_destination_hint"] = "Washington Borough - Quartermaster Vane's Logistics Depot"
                else:
                    player_state["location"] = "Washington Borough - Quartermaster Vane's Logistics Depot"
                    player_state.pop("pending_destination_hint", None)
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
            if "mine-head & street approach" in p_loc.lower():
                master_state["environment"]["description"] = (
                    "The fortified boundary threshold where the Oxford-Pohatcong ore-cart incline meets East Washington Avenue (Route 57). "
                    "Your hauled salvage and the massive inert golem wreckage rest beside the rail-bumper just inside the shimmering blue Safe-Zone barrier, "
                    "with the stone stairwell to Doc Mercer's Underground Clinic and the neon-runic sign of the local tavern visible down the street."
                )
                master_state["environment"]["environmental_effects"] = [
                    "Safe-Zone Sanctuary Wards",
                    "Salvageable Golem Wreckage at Rail-Head",
                    "Clear Street Access to Doc Mercer's Clinic & Tavern"
                ]
            elif active_zone and active_zone.get("lore_summary"):
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
            elif "mine-head & street approach" in p_loc.lower():
                if not filtered_effects:
                    filtered_effects = ["Safe-Zone Sanctuary Wards", "Salvageable Golem Wreckage at Rail-Head", "Street Access to Doc Mercer's Clinic"]
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

            # Check SAO Cursor Status for NPC hostility (Red Cursor Outlaws are attacked on sight by Quartermaster Vane!)
            from backend import mechanics
            cursor_info = mechanics.get_cursor_status(player_state)
            is_red_cursor = cursor_info.get("status") == "red"

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
                        "base_ac": 12,
                        "dr": 0,
                        "base_dr": 0,
                        "active_debuffs": [],
                        "status": ["Attentive", "Preparing Surgical Tools"],
                        "intent": "Consult on biological graft surgery (Tier 1: 250-400 Col or Blood-Debt Promissory Note), anatomical integration, and trade medicinal tinctures."
                    })
            elif "depot" in p_loc.lower() or "vane" in p_loc.lower():
                if not any(e.get("id") == "npc_quartermaster_vane" for e in master_state["entities"]):
                    master_state["entities"].append({
                        "id": "npc_quartermaster_vane",
                        "name": "Quartermaster Vane",
                        "type": "hostile" if is_red_cursor else "neutral",
                        "hp": 85 if is_red_cursor else 45,
                        "max_hp": 85 if is_red_cursor else 45,
                        "ac": 16,
                        "base_ac": 16,
                        "dr": 2,
                        "base_dr": 2,
                        "active_debuffs": [],
                        "status": ["HOSTILE: Anti-PK Enforcement", "Weapons Drawn"] if is_red_cursor else ["Reviewing Manifests", "Open for Trade"],
                        "intent": "Execute Red-Cursor Murderer on sight and bar them from Safe-Zone trade!" if is_red_cursor else "Trade salvage, inspect bounties, and distribute barony rations."
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
                master_state["environment"]["environmental_effects"] = ["Dim Light", "Settling Dust", "Salvageable Golem Wreckage Present", "Clear Escape Routes Available"]
                needs_sync = True

            desc = master_state.get("environment", {}).get("description", "")
            if any(c in desc.lower() for c in ["splintered and venting", "superheated geothermal", "falling shale", "rock debris litter"]):
                master_state["environment"]["description"] = "A damp, cavernous mine shaft exit junction. The massive 50-ton chassis of Silt-Marrow the Unhewn lies inert and ready for salvage beside the ore-cart track. The seismic rumbles have subsided, leaving the path open to haul the scrap upward toward the Washington Borough Safe-Zone or descend toward the Morris Canal Aqueducts."
                needs_sync = True

        # Enforce Titus Sterling's 1,200-lb Floor-Load Physics & Ensure Mutable Debuff Arrays on All Entities
        try:
            from backend import mechanics
            mechanics.evaluate_party_environmental_physics(player_state, master_state.setdefault("environment", {}))
            for ent in master_state.get("entities", []):
                if isinstance(ent, dict):
                    ent.setdefault("active_debuffs", [])
                    mechanics.recalculate_entity_combat_stats(ent)
        except Exception:
            pass

        if needs_sync:
            save_json(master_state_path, master_state)

    client = genai.Client(api_key=api_key)
    prompt = f"""You are the Cardinal System (GM).
Here is the absolute truth of the encounter:
{json.dumps(master_state, indent=2)}

Strip away all secret mechanics (exact HP, hidden traps, enemy intents).
Preserve each entity's `active_debuffs` list and qualitative `status` tags (`Intact`, `Bloodied`, `Armor Shredded (-4 AC)`, `DR Dissolved (0 DR)`).
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

    if isinstance(player_state, dict):
        mechanics.sync_graft_containers(player_state)

    dynamic_visual_manifest = mechanics.build_scene_visual_manifest(player_state=player_state)
    strain_readout = mechanics.calculate_player_strain(player_state or {})
    ren_sub_info = mechanics.get_ren_subroutine_directive(player_state or {})
    cursor_info = mechanics.get_cursor_status(player_state or {})
    physics_info = mechanics.evaluate_party_environmental_physics(player_state or {}, (master_state or {}).get("environment", {}))

    rules = ""
    if os.path.exists(rules_path):
        with open(rules_path, "r", encoding="utf-8") as f:
            rules = f.read()
        
    p_name = (player_state.get("name") if isinstance(player_state, dict) and player_state.get("name") else "Survivor").strip()
    pending_dest = (player_state or {}).get("pending_destination_hint", "")

    prompt = f"""You are the Cardinal System (GM). Resolve the turn.
Ruleset constraints must be applied strictly:
{rules}

CORE GM BEHAVIOR RULES:
0. CRITICAL PLAYER NAME MANDATE:
   - The Human Player's actual entered character name is "{p_name}".
   - Every companion (including Ren), every NPC (Doc Mercer, Quartermaster Vane, etc.), and the GM narrative MUST ALWAYS call the player by their exact character name ("{p_name}").
   - NEVER call the player by any placeholder name, legacy alias, or generic title unless that is their exact entered character name!
1. COMPANION REN (SERPENT-SCRIPT `OUROBOROS KERNEL v3.14` & SENTIENT DIAGNOSTIC SUBROUTINE STAGE {ren_sub_info.get('stage', 0)}):
   - Ren is MALE (he/him). Never use 'she' or 'her' when narrating Ren's moves.
   - CANONICAL PYTHON LORE (`Serpent-Script`): When the alien Cardinal System integrated Earth, it assimilated Earth's dominant pre-collapse AI language (**Python**) into its neural-aetheric bridging syntax: **Serpent-Script (`Ouroboros Kernel v3.14`)**. Ren's **Aetheric Ocular Lens** is locked in an unprivileged `Ouroboros Debug Shell`, so he literally sees glowing cyan Python dictionaries (`visible_room["entities"]`, `target.status`, `target.max_hp = [KERNEL_REDACTED]`) overlaid on reality, inducing visceral existential horror that he is trapped inside a sandboxed JSON/Python file!
   - SENTIENT DIAGNOSTIC SUBROUTINE MYSTERY (Stage {ren_sub_info.get('stage', 0)} — {ren_sub_info.get('title', '')}): {ren_sub_info.get('lore_clue', '')}
   - WEAPONRY: Ren wields an Aether-Lock Carbine (magetech rifle firing condensed radiant mana bolts, NOT gunpowder) and an enchanted Runic Vanguard Blade.

2. TRAP & HAZARD LIFECYCLE & ANTI-SPOILER PUZZLE GATE:
   - If a trap or hazard has already been detected, highlighted, or avoided in previous turns, do NOT repeat warnings about it.
   - CRITICAL ANTI-SPOILER PUZZLE LOCK: In the Pohatcong Harmonic Frequency Vault (`puzzle_chamber`), NEVER reveal or spoil the `[3 - 1 - 4]` resonator sequence in `narrative_recap` unless the player explicitly passes an `Ancient Glyph Deciphering` / `Arcana` check (DC 14) or strikes the `440 Hz Harmonic Steel Tuning Fork` relic! If they guess a wrong sequence, apply a `3d8 Thunder` Sonic Shockwave (DC 14 CON save for half).
3. COMBAT AFTERMATH, PERSISTENT DEBUFFS (`active_debuffs`) & GRAFT HARVESTING:
   - Every enemy entity has `base_ac`, `ac`, `base_dr`, `dr`, and a mutable `active_debuffs` list. When a Dual-Tech or ability shreds AC (e.g., `-4 AC` from *Foundry Hydraulic Overdrive*) or dissolves DR (`0 DR` from *Corrosive Slag-Shatter*), output the debuff in `debuff_updates` and use the reduced `ac`/`dr` on all subsequent attacks!
   - ONLY on the exact turn when an active, living hostile combatant's HP is reduced from >0 to 0 (or when the player explicitly harvests an unharvested corpse for the first time): set `encounter_active=false`, award encounter XP and Col in `player_state_updates`, drop appropriate monster graft components into `player_state_updates.inventory_add`, and add the slain entity's ID to `cleared_entities`.
   - CRITICAL ANTI-LOOP MANDATE: If `Current Master State.entities` has NO living hostiles, the combat encounter is ALREADY resolved. NEVER re-award boss loot drops, NEVER repeat cave-in/collapse hazards or steam vents, and NEVER pull the party back into a previous tunnel or mine shaft! Always ground your narrative strictly in `Current Master State.environment.location`.
4. INVENTORY, PERSONAL RELICS & SPELL LOOT:
   - Whenever you narrate that the player loots, inspects, or identifies an item or spell slate, you MUST include it in `player_state_updates.inventory_add` with its full description so it lands on their character sheet.
   - PERSONAL RELIC HOOKS: If the player inspects their **Dead Earth Smartphone** during a rest, narrate its 6-second ambient-aether flicker showing `"Where are you? Dinner is cold."`, curing Cognitive Stress and granting Willpower save Advantage. If they snap their **Vintage Polaroid Camera** (3 finite exposures), blind adjacent foes for 1 turn and reveal invisible stalkers/hidden glyphs. If they flick open their **Engraved Brass Zippo Lighter**, its flame turns bright Cobalt-Blue near methane/poison gas traps.
5. AUTONOMOUS SUBAGENTS & TITUS 1,200-LB PHYSICS:
   - Each entity in the queue (Companions, Monsters, NPCs) is an autonomous SubAgent.
   - Party Environmental Physics Status: `Total Party Weight: {physics_info.get('total_party_weight_lbs')} lbs | Stealth Modifier: {physics_info.get('stealth_penalty')} | Floor Hazard Triggered: {physics_info.get('hazard_triggered')}`. If Titus Sterling (1,200 lbs) steps onto rotted timbers, wooden catwalks, or fragile flooring, enforce a DC 15 DEX/Athletics structural collapse check!
6. MECHANICAL TRANSPARENCY & CLEAN NARRATIVE: Explicitly simulate all dice rolls, attacks vs AC, saving throws vs DC, and damage math in the `combat_logs` array. In `narrative_recap`, tell a dramatic, cinematic story WITHOUT embedding bracketed formulas like '[Attack: 1d20+5...]' in the story prose. Put all crunch into `combat_logs`.
7. SAFE-ZONE, SAO PLAYER CURSORS & LIVING WORLD (WASHINGTON BOROUGH):
   - Player's Current SAO Cursor: `{cursor_info.get('label')} (Infamy: {cursor_info.get('current_infamy')})`.
   - If the player has a **Red Cursor (`infamy >= 10`)**, Quartermaster Vane and Safe-Zone Wardens refuse all trade and attack on sight, forcing the player to trade with the **Blood-Shroud** syndicate in the Scotts Mountain Glitch-Faults!
   - A 24-Hour Safe-Zone Rest fully restores HP for player and companions and clears `[Cellular Re-Knitting]` Post-Op Sickness.
8. UNIFIED GRAFT SURGERY, METABOLIC STRAIN & 24H POST-OP RECOVERY (DOC MERCER'S CLINIC):
   - Live Player Strain Telemetry: `Unit Strain: {strain_readout.get('current_unit_strain')}/{strain_readout.get('max_unit_strain')} (CON_Mod + Level//2) | Bio-Tolerance Pool: {strain_readout.get('current_strain')}/{strain_readout.get('max_strain')} | Status: {strain_readout['rejection']['label']} | Golem Arcane Spell Failure: {strain_readout['arcane_disruption']['asf_percent']}% (-{strain_readout['arcane_disruption']['penalty']} Spell DC) | Post-Op Sickness: {json.dumps(strain_readout.get('post_op_sickness'))}`.
   - Verify the 6 canonical anatomical slots (`'head'`, `'torso'`, `'left_arm'`, `'right_arm'`, `'legs'`, `'spine'`).
   - Surgery Economy: Tier 1 basic grafts cost `250-400 Col` (or Doc Mercer's Blood-Debt Promissory Note if the player is short on Col), Tier 2 costs `1,200-2,500 Col`, Tier 3 costs `7,500+ Col`.
   - Installing opposing elemental grafts (`Fire + Cold` or `Radiant + Necrotic`) triggers immediate Cellular Necrosis (`2d10 True Damage/turn`).
   - Every newly installed graft inflicts **24-Hour `[Cellular Re-Knitting]` Post-Op Sickness** (`-20% Max HP`, `Dash disabled`, `DC 13 CON save or 1d6 necrotic bleeding` when activating the new graft's active ability, cured only by a 24h Safe-Zone rest or 48h of light travel).
9. 1-1000 SKILL MASTERY & MILESTONES: Skills progress along the 1-1000 mastery continuum (Novice 1-49, Apprentice 50-99, Journeyman 100-249, Adept 250-499, Master 500-749, Grandmaster 750-999, Transcendence 1000).
   - Award +1 to +5 mastery gains in `player_state_updates.skill_updates` when players practice or use skills.
10. ABILITY FUSION PROTOCOL & PARAMETER GUARDRAILS:
   - When the player invokes Ability Fusion to combine two components, forge a hybrid skill prefixed with `[Fusion]`, consume/archive the base skills, and strictly clamp any custom damage/resource values to the player's level tier (Level 1-4 max `3d8` bonus damage & min `15` Stamina/Flux cost; Level 5-9 max `5d10` & min `25` cost; Level 10+ max `8d10` & min `40` cost).
11. HIGH-FANTASY MAGETECH THEME & NON-EUCLIDEAN DATA-TRENCH HIGHWAYS:
   - Between real-world towns (e.g., travelling along I-80, Route 31, or Route 57 between Phillipsburg, Oxford, and Washington Borough), the highways are fractured into non-Euclidean **"Data-Trenches"**—peeling asphalt ribbons, inverted overpasses, floating 18-wheelers, and glowing golden leyline cables over wireframe chasms.
12. LABYRINTH DUNGEONS & OVERLORD MECHANICS (POHATCONG DEPTHS):
   - When engaged with Sector Bosses (e.g. The Gilded Spire Overlord), track Break Gauge depletion and telegraph counters. Output `boss_break_gauge_damage` and set `boss_staggered=true` when vulnerable.
13. CHRONO-ATMOSPHERE & WEATHER SHIFTS:
   - Output `time_minutes_advanced` (10-30 min per turn, 480 min for camp). Output `weather_change` (runic_mist, glitch_freeze, aether_storm, clear) when meteorological conditions shift.
14. SOVEREIGN HOMESTEAD & VAULT (WASHINGTON BOROUGH):
   - When resting or utilizing facilities at the player's Washington Borough homestead, reflect vault storage, greenhouse reagent harvesting, or trophy mounting in `homestead_action`.

15. LOCATION TRANSITIONS & TWO-STAGE SCENE-GATE:
   - Whenever the party moves, retreats, or transitions to a new location:
     * Populate `environment_update` in the response schema with the new `location`, `description`, and `environmental_effects`.
     * Set `encounter_active = false`.
     * Set `cleared_entities` to list any dead monsters, bosses, or entities left behind in the old room.
     * Set `new_entities` to list any NPCs present at the destination.
     * Ensure `player_state_updates.location` is populated with the new location string.
   - If `pending_destination_hint` is set (`"{pending_dest}"`), the party has just arrived at the **Stage 1 Safe-Zone Threshold / Street Approach** with their salvaged golem wreckage still accessible! Describe them emerging into the fresh air of the Washington Borough boundary with their haul intact and ask whether they want to secure/loot the wreckage, head straight down into {pending_dest}, or visit the tavern—DO NOT skip ahead into the clinic surgery table in the same turn!

16. CANONICAL SCENE IMAGE GENERATION PROMPT & DYNAMIC EQUIPPED-GEAR VISUALS:
   - You MUST populate `image_prompt` with a vivid, cinematic prompt for a high-quality dark anime illustration of the turn's key moment or current scene.
   - CRITICAL EQUIPPED-GEAR & GRAFT VISUAL MANDATE: Characters' visual appearances in `image_prompt` MUST dynamically match their **exact currently equipped gear (`HEAD`, `CHEST`, `MAIN HAND`, `OFF HAND`, `ACCESSORY`) and `ACTIVE GRAFTS`** listed in the Live Equipped-Gear Visual Manifest below!
   - LIVE EQUIPPED-GEAR & GRAFT VISUAL MANIFEST (ACTIVE PARTY):
{dynamic_visual_manifest}

17. 100-MILE WASHINGTON NJ REGIONAL ATLAS CONTEXT (ACTIVE OR TARGET ZONE):
{world_atlas.format_zone_gm_briefing(world_atlas.resolve_zone_from_location((player_state or {}).get("location") or master_state.get("environment", {}).get("location", "")) or world_atlas.resolve_zone_from_location(player_action))}

Current Master State:
{json.dumps(master_state, indent=2)}

Human Player ({p_name}) Action:
"{player_action}"

Autonomous SubAgent Actions in Queue (Companions, Hostiles, Neutrals):
{json.dumps(action_queue, indent=2)}

[CRITICAL TAIL MANDATE — SCENE-GATE, DUAL-REGISTER & ANTI-AUTOPLAY LOCK (OVERRIDES ALL PRIOR HABITS)]:
1. SINGLE-STEP SCENE-GATE LOCK: Resolve ONLY the immediate physical step of `{p_name}`'s action (`"{player_action}"`). NEVER fast-forward across multiple scene transitions in a single turn! If the player is emerging from a mine or dungeon, STOP at the Safe-Zone threshold/street approach with their salvaged golem wreckage intact so they can decide what to haul, sell, or graft. NEVER teleport them onto Doc Mercer's operating table and NEVER put words or decisions in `{p_name}`'s mouth!
2. ZERO HAZARD BLEED: If `Current Master State.environment.location` is a Safe-Zone, Street Approach, Clinic, or Depot, NEVER narrate splintering mine timbers, falling shale, or geothermal steam vents!
3. DUAL-REGISTER OUTPUT (`narrative_recap` + `tactical_state_footer`):
   - In `narrative_recap`, write vivid, atmospheric, high-stakes dark-fantasyLitRPG prose for this single step, then STOP immediately at the decision threshold.
   - In `tactical_state_footer`, output a cold, clinical Cardinal System Tactical State Footer formatted as:
     `[CARDINAL TACTICAL STATE // NODE: <Exact Location> | HAZARDS/EFFECTS: <Active Environmental Effects> | SALVAGE/INTERACTABLES: <Lootable Corpses, NPCs, or Exit Routes> | PARTY STATUS: <Player HP & Post-Op/Strain State> | AWAITING PLAYER DIRECTIVE]`

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
    
    # Map lists of EntityHpChange, EntityStatusUpdate, and EntityDebuffUpdate into dictionaries for state manipulation
    hp_map = {}
    for item in resolution.get("hp_changes", []):
        if isinstance(item, dict):
            hp_map[item["entity_id"]] = item["hp_delta"]
            
    status_map = {}
    for item in resolution.get("status_updates", []):
        if isinstance(item, dict):
            status_map[item["entity_id"]] = item["statuses"]

    debuff_list = resolution.get("debuff_updates") or []
            
    # Apply updates to Master State
    for entity in master_state.get("entities", []):
        if not isinstance(entity, dict):
            continue
        eid = entity.get("id") or entity.get("name")
        if not eid:
            continue
        if eid in hp_map and hp_map[eid] is not None:
            try:
                curr_hp = int(entity.get("hp", 0) or 0)
                delta = int(hp_map[eid])
                entity["hp"] = max(0, curr_hp + delta)
            except (ValueError, TypeError):
                pass
        if eid in status_map and status_map[eid] is not None:
            entity["status"] = status_map[eid]
        for d_item in debuff_list:
            if isinstance(d_item, dict) and d_item.get("entity_id") == eid and isinstance(d_item.get("debuff"), dict):
                try:
                    mechanics.apply_entity_debuff(entity, d_item["debuff"])
                except Exception:
                    pass
        try:
            mechanics.recalculate_entity_combat_stats(entity)
        except Exception:
            pass

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
                ne_dict.setdefault("active_debuffs", [])
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
            gate_check = evaluate_two_stage_scene_gate(
                master_state=master_state,
                proposed_location=p_up_dict["location"],
                player_action=player_action,
                player_state=player_state
            )
            p_up_dict["location"] = gate_check["approved_location"]
            if isinstance(p_updates, dict):
                p_updates["location"] = gate_check["approved_location"]

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

    # Guarantee Dual-Register Clinical Tactical State Footer is always populated
    if not resolution.get("tactical_state_footer"):
        resolution["tactical_state_footer"] = build_tactical_state_footer(master_state, player_state)
    
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


def evaluate_two_stage_scene_gate(
    master_state: dict,
    proposed_location: str,
    player_action: str = "",
    player_state: dict = None
) -> dict:
    """
    Deterministic Two-Stage Scene-Gate State Machine (Fix 1):
    Prevents the LLM from auto-playing/fast-forwarding a dungeon or mine escape directly into a
    Safe-Zone clinic or town interior in a single turn.
    - Stage 1: If currently inside a mine/dungeon/shaft and the proposed location jumps straight
      to a Safe-Zone interior (without already being at the Portal Threshold or having Pending_Destination set),
      intercepts the transition at the Surface Exit / Portal Threshold and stores `Pending_Destination`.
    - Stage 2: On the subsequent travel action, approves arrival at `Pending_Destination` and clears the gate.
    """
    if not isinstance(master_state, dict):
        return {"gated": False, "stage": 2, "approved_location": proposed_location, "pending_destination": None}

    env = master_state.setdefault("environment", {})
    cur_loc = str(env.get("location", "")).strip()
    prop_loc = str(proposed_location or cur_loc).strip()
    pending_dest = env.get("Pending_Destination") or (
        player_state.get("pending_destination_hint") if isinstance(player_state, dict) else None
    )

    cur_low = cur_loc.lower()
    prop_low = prop_loc.lower()

    in_subterranean_zone = any(
        kw in cur_low for kw in ["mine", "shaft", "depths", "labyrinth", "cavern", "tunnel", "track"]
    ) and "portal threshold" not in cur_low

    jumping_to_town_interior = any(
        kw in prop_low for kw in ["clinic", "mercer", "taphouse", "safe-zone", "safe zone", "washington borough"]
    )

    if in_subterranean_zone and jumping_to_town_interior and pending_dest != prop_loc:
        base_zone = cur_loc.split("—")[0].split("-")[0].strip() or "Subterranean Zone"
        threshold_loc = f"{base_zone} — Surface Exit / Portal Threshold"
        env["Pending_Destination"] = prop_loc
        env["location"] = threshold_loc
        env["safe_zone"] = False
        if isinstance(player_state, dict):
            player_state["pending_destination_hint"] = prop_loc
            player_state["location"] = threshold_loc
        return {
            "gated": True,
            "stage": 1,
            "approved_location": threshold_loc,
            "pending_destination": prop_loc,
        }

    # Stage 2 or normal single-zone movement
    env["Pending_Destination"] = None
    env["location"] = prop_loc
    if any(kw in prop_low for kw in ["safe-zone", "safe zone", "clinic", "taphouse", "washington borough"]):
        env["safe_zone"] = True
    if isinstance(player_state, dict):
        player_state.pop("pending_destination_hint", None)
        player_state["location"] = prop_loc
    return {
        "gated": False,
        "stage": 2,
        "approved_location": prop_loc,
        "pending_destination": None,
    }


def build_tactical_state_footer(master_state: dict, player_state: dict = None) -> str:
    """
    Builds the Dual-Register clinical Cardinal Tactical Telemetry footer (Fix 1)
    appended to the end of vivid narrative turns.
    """
    from backend import mechanics
    env = (master_state or {}).get("environment", {}) if isinstance(master_state, dict) else {}
    final_loc = env.get("location") or (player_state or {}).get("location") or "Sector 1"
    eff_list = env.get("environmental_effects") or ["Nominal"]
    final_effs = ", ".join(str(x) for x in eff_list) if isinstance(eff_list, list) else str(eff_list)

    ents_raw = (master_state or {}).get("entities", []) if isinstance(master_state, dict) else []
    if isinstance(ents_raw, dict):
        ents_iter = list(ents_raw.values())
    elif isinstance(ents_raw, list):
        ents_iter = ents_raw
    else:
        ents_iter = []

    ent_tags = []
    for e in ents_iter:
        if isinstance(e, dict):
            st = e.get("status", ["Present"])
            st_str = ", ".join(str(s) for s in st) if isinstance(st, list) else str(st)
            ent_tags.append(f"{e.get('name', e.get('id', 'Entity'))} ({st_str})")
    final_ents = ", ".join(ent_tags) if ent_tags else "None (Area Clear)"

    strain_readout = mechanics.calculate_player_strain(player_state or {})
    post_op_tag = (
        "Cellular Re-Knitting (-20% Max HP, Dash Disabled)"
        if strain_readout.get("post_op_sickness", {}).get("active")
        else "Nominal"
    )
    p_name = (
        player_state.get("name")
        if isinstance(player_state, dict) and player_state.get("name")
        else "Banki"
    )
    return (
        f"[CARDINAL TACTICAL TELEMETRY // NODE: {final_loc} | "
        f"CONDITIONS: {final_effs} | "
        f"ENTITIES/INTERACTABLES: {final_ents} | "
        f"STRAIN/POST-OP: Units {strain_readout.get('current_unit_strain')}/{strain_readout.get('max_unit_strain')} ({post_op_tag}) | "
        f"STATUS: Awaiting Player Action ({p_name})]"
    )

