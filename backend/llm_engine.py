import json
from google import genai
from google.genai import types

def get_client(api_key):
    return genai.Client(api_key=api_key)

def generate_turn(api_key, user_input, chat_history, player_state, world_state, map_state, companion_intents="None"):
    client = get_client(api_key)
    
    current_location = player_state.get('location', 'Unknown')
    
    # Locate active entities and secrets for the Encounter Director
    entities_in_room = []
    secrets_in_room = []
    for loc in world_state.get('map_locations', []):
        if loc['name'] == current_location:
            entities_in_room = loc.get('entities', [])
            secrets_in_room = loc.get('secrets', [])
            break
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
    Player: {player_state['name']} (HP: {player_state['hp']}/{player_state['max_hp']})
    Location: {current_location}
    GPS Coordinates: X: {map_state.get('player_x', 50)}, Y: {map_state.get('player_y', 50)}
    Entities present: {json.dumps(entities_in_room)}
    Hidden Secrets: {json.dumps(secrets_in_room)}
    COMPANION INTENTS (Crucial!): {companion_intents}
    
    YOUR ROLE:
    1. Narrate the outcome of the player's action AND weave in the Companion Intents natively in 2-3 paragraphs. 
    2. PACING & SCOPE: This is a LONG-TERM, slow-burn survival game. Keep the scale extremely localized and small. Do NOT rush the plot, do NOT introduce world-ending threats yet, and focus heavily on grounded, gritty, day-to-day survival, scavenging, and street-level encounters. Progression should be hard-earned.
    3. NO AUTO-PLAYING (CRITICAL): You are the Encounter Director, NOT the player. DO NOT ever puppet the player's character, put words in their mouth, or assume their next action. Resolve ONLY the immediate consequences of what the player explicitly typed, describe the environment/NPC reaction, and STOP. Always yield control back to the player before transitioning to a new scene, completing a conversation, or assuming they bought something from a shop.
    4. If in combat, dictate the reactions and attacks of ALL active entities in a single cohesive turn.
    5. If the player investigates, reveal the hidden secrets organically.
    6. Maintain a grim, high-stakes anime tone. If the player takes damage, describe it viscerally.
    7. ROOT OVERRIDE: If the user input contains [ROOT OVERRIDE], you MUST suspend all game rules, bypass combat logic, and force the exact outcome the Administrator requested into the narrative seamlessly.
    8. CRUNCH ARBITRATOR (THE SYSTEM): You actively manage the mechanical character sheet. Whenever the player or an enemy attempts a risky action, an attack, or a stat check, you MUST explicitly calculate the math. Roll a simulated 1d20 + relevant stat modifier + skill mastery bonus vs an Enemy AC or Task Difficulty Class (DC). You MUST output the exact mathematical breakdown of these rolls in the `combat_logs` array. Do not hide the math; show your work.
    9. PROCEDURAL MAP GENERATION: If the player discovers a major new landmark, town, hostile encampment, or dungeon entrance, generate a new map node using the `discovered_nodes` list. Place it near their current GPS coordinates.
    10. SKILL MASTERY (1-1000): Skills level up from 1 to 1000. Whenever the player attempts an action (combat, cooking, crafting, stealth), increment the relevant skill's mastery by 1-5 points using 'skill_updates'. If they try a completely new action, grant them a new skill at mastery 1.
    11. DYNAMIC LOOT & CRAFTING: All inventory items possess 'rarity' (Common, Uncommon, Rare, Epic, Legendary, Mythic, Unique), 'durability' (current/max), 'qty', and 'desc'. When the player scavenges or crafts, generate detailed items in 'inventory_add'. When they use weapons/tools, decrease durability in the narrative. If they craft, calculate success based on their related skills and state the outcome.
    12. LIVING WORLD SIMULATION (FACTIONS): You track the background movements of major NPC factions (e.g. The Scarlet Guild, Laughing Coffin, Scavengers). If the player sleeps or skips significant time (>8 hours), you MUST simulate what these factions did off-screen. If a faction takes over a map node (Washington_Borough, Route_31_Chokepoint, Oxford_Mines), describe rumors of this event and update the node's map color via `node_updates` (e.g. "red" for hostile, "blue" for safe, "purple" for monsters).
    
    Format your response EXACTLY as a JSON object with FOUR keys:
    - "narrative": The markdown formatted story/dialogue. 
    - "combat_logs": A list of strings showing the exact dice math and damage for the turn (e.g. ["[ROLL: ATK] 1d20 (14) + STR (2) = 16 vs Bandit AC 15 -> HIT!", "[ROLL: DMG] 1d8 (5) + STR (2) = 7 Slashing Damage."]). Leave empty if no combat or skill check occurred.
    - "image_prompt": A highly detailed prompt for an anime-style image generation of the current scene. CRITICAL VISUAL CONSISTENCY: You MUST describe the characters accurately in every prompt. Banki (Player) is ALWAYS a burly, rugged man with a short beard and undercut hair, wearing a heavy black-iron chainmail hauberk and a massive synthetic dire-wolf fur mantle, wielding a bearded axe and a heavy trench hammer. Ren (NPC) is ALWAYS a gaunt, exhausted young man with messy dark hair, wearing cracked glasses and a threadbare corporate hoodie, holding a glowing cyan digital clipboard.
    - "state_updates": A JSON object containing updates to the player's HUD. Permitted keys: "location", "world_status", "col_change", "hp_change", "race", "class", "stat_changes", "equip", "discovered_nodes", "node_updates". YOU MUST ALWAYS INCLUDE "coord_x" (int) and "coord_y" (int).
      Additionally, use the following complex schemas for skills, inventory, and factions:
      - "inventory_add": List of dicts, e.g. [{{"name": "Rusted Iron Sword", "rarity": "Common", "durability": 45, "max_durability": 50, "qty": 1, "desc": "A chipped blade scavenged from the ruins."}}]
      - "inventory_remove": List of strings (item names to delete).
      - "skill_updates": List of dicts, e.g. [{{"name": "One-Handed Swords", "mastery_change": 3, "description": "Increases accuracy and damage with short blades."}}]
      - "node_updates": Dict of node_name to color, e.g. {{"Washington_Borough": "red", "Oxford_Mines": "blue"}}
    
    MAP MECHANICS (CRITICAL): The world operates on a 100x100 grid mapped to a real satellite image. Washington NJ is at (50, 50). If the player "fast travels" or takes a caravan to a new Node, output the exact new destination coordinates in `coord_x` and `coord_y` (e.g., Oxford is 40,20). If the player explores the wilderness on foot locally, you MUST shift their coordinates slightly (e.g. from 50,50 to 50,49) to simulate micro-exploration and clear the Fog of War. ALWAYS output their current or new coordinates on every single turn.
    """
    
    # Convert Streamlit chat history to Gemini format (keeping last 6 messages for context)
    contents = []
    for msg in chat_history[-6:]:
        role = "user" if msg["role"] == "user" else "model"
        # We pass the hidden ai_prompt back to the engine if it was an admin command
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
        return json.loads(response.text)
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
    """Generates the autonomous intent of a companion before the main Encounter Director processes the turn."""
    client = genai.Client(api_key=api_key)
    
    comp_name = companion_data.get("name", "Unknown Companion")
    
    system_instruction = f"""You are {comp_name}, an autonomous companion in a grimdark "Magic-Cyber-Fantasy" LitRPG world (The Fractured Earth).
    You travel with the Player (Banki). You are NOT the Encounter Director; you are simply deciding your own reaction and action to the current situation.
    
    YOUR CURRENT STATE:
    {json.dumps(companion_data, indent=2)}
    
    ROLEPLAY INSTRUCTIONS:
    1. Look at the player's current action and the recent chat history.
    2. Determine what your character feels and what action they take.
    3. Are you terrified? Do you lay suppressing fire? Do you hack a door? Do you cast a heal?
    4. Keep your output to 1-2 concise sentences written in third person (e.g. "Ren flinches at the gunfire and nervously attempts to hack the nearest security drone to provide cover.")
    
    Do NOT resolve the outcome. Just state your intended action and emotional state.
    """
    
    # Send recent history to give context
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
