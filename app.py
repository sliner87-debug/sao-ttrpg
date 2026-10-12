import streamlit as st
import json
import os
import time
import importlib
import base64
import backend.gm_engine as gm_engine
import backend.actor_engine as actor_engine

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="The Fractured Overlay", page_icon="🗡️", layout="wide")

# --- AUTHENTICATION CHECK ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    api_key = "your_api_key_here"

if api_key == "your_api_key_here":
    st.error("⚠️ **SYSTEM LOCK:** Please enter your Gemini API Key in `.streamlit/secrets.toml` to connect to the Cardinal System.")
    st.stop()

# --- PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORLD_PATH = os.path.join(BASE_DIR, 'world_state.json')
SAVE_PATH = os.path.join(BASE_DIR, 'save_game.json')

# --- SAVE/LOAD LOGIC ---
@st.cache_data
def load_world():
    if os.path.exists(WORLD_PATH):
        with open(WORLD_PATH, 'r') as f:
            return json.load(f)
    return {"sector": 1, "world_status": "OFFLINE", "map_locations": []}

world_state = load_world()

def load_game():
    if os.path.exists(SAVE_PATH):
        with open(SAVE_PATH, 'r') as f:
            return json.load(f)
    return None

def save_game(player_state, messages):
    data = {
        "player": player_state,
        "messages": messages,
        "last_saved": time.time()
    }
    with open(SAVE_PATH, 'w') as f:
        json.dump(data, f, indent=4)

# --- INITIALIZE SESSION STATE ---
saved_data = load_game()

if "offline_processed" not in st.session_state:
    st.session_state.offline_processed = True
if "player" not in st.session_state:
    if saved_data:
        st.session_state.player = saved_data["player"]
    else:
        st.session_state.player = {
            "name": "TestSubject_01",
            "level": 1,
            "xp": 0,
            "hp": 100,
            "max_hp": 100,
            "col": 0,
            "inventory": [
                {"name": "Iron Sword", "rarity": "Common", "durability": 45, "max_durability": 50, "qty": 1, "desc": "A basic, slightly rusted blade."},
                {"name": "Bottled Water", "rarity": "Common", "durability": 1, "max_durability": 1, "qty": 2, "desc": "Clean drinking water."}
            ],
            "location": "Sector 1 Safe-Zone: Washington Borough, NJ"
        }
        
# Migration: Ensure new database keys exist for old save files and cached sessions
p = st.session_state.player
p.setdefault("race", "Unregistered Anomaly")
p.setdefault("class", "Pathless (Freeform)")
p.setdefault("xp", 0)
p.setdefault("stats", {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10})
p.setdefault("skills", {})
p.setdefault("spells", [])
p.setdefault("feats", [])
p.setdefault("quests", [])

# Migrate old inventory (list of strings) to complex objects
new_inv = []
for item in p.get("inventory", []):
    if isinstance(item, str):
        qty = 1
        name = item
        if " x" in item:
            parts = item.rsplit(" x", 1)
            name = parts[0]
            try: qty = int(parts[1])
            except: pass
        new_inv.append({"name": name, "rarity": "Common", "durability": 100, "max_durability": 100, "qty": qty, "desc": "Legacy item."})
    else:
        new_inv.append(item)
p["inventory"] = new_inv

# Migrate old skills (list of strings) to mastery dictionaries
if isinstance(p.get("skills", {}), list):
    new_skills = {}
    for s in p["skills"]:
        if isinstance(s, str):
            name = s.split(":")[0] if ":" in s else s
            new_skills[name] = {"mastery": 1, "description": s}
    p["skills"] = new_skills

p.setdefault("racial_abilities", [])
p.setdefault("equipped", {"head": "None", "chest": "None", "main_hand": "None", "off_hand": "None", "accessory": "None"})
p.setdefault("companions", {
    "Ren": {
        "name": "Ren",
        "archetype": "Corporate Hacker / Magi-tech Support",
        "hp": 40,
        "max_hp": 40,
        "status": "Exhausted but loyal",
        "inventory": ["Cyan Digital Clipboard (Hacking Deck)", "Corporate Stun-Pistol"]
    }
})

if "messages" not in st.session_state:
    if saved_data:
        st.session_state.messages = saved_data["messages"]
    else:
        st.session_state.messages = [
            {
                "role": "system", 
                "content": "### ⚠️ SYSTEM INITIALIZATION (THE CRUCIBLE) ⚠️\n\n*Planetary inoculation complete. Ambient Aether levels rising to lethal thresholds. Initiating Phase 1: Metamorphic Stress Test.*\n*Current human genome recognized as: OBSOLETE. Dungeons and aggressive bio-fauna deployed to catalyze forced mutation. Shed your frailties, harvest the strong, and evolve. The Architects are watching.*\n\n---\n\n**[ 🛠️ SURVIVAL TUTORIAL ]**\nWelcome to the V2 Sandbox. Here is how to play:\n1. **Actions:** Type your combat maneuvers, dialogue, or exploration choices in the command box below. The System mathematically resolves all dice rolls, AC, and damage.\n2. **AI Companions:** Your party members (like Ren) are fully autonomous. They evaluate the room and queue tactical choices independently.\n3. **Live Table Companion:** If you want to run the game vocally, toggle the **🎙️ Microphone Module** in the left sidebar to stream your voice directly to the AI.\n4. **Grafting:** You can augment your body with monster parts or cybernetics, but watch your *Strain* limit. Biological atrocities are rewarded.",
                "image_path": None
            }
        ]

# --- SIDEBAR: HUD & INVENTORY ---
with st.sidebar:
    st.title("🛡️ Player HUD")
    player = st.session_state.player
    st.subheader(player["name"])
    
    hp_percent = max(0.0, min(1.0, player["hp"] / player["max_hp"]))
    st.progress(hp_percent, text=f"HP: {player['hp']} / {player['max_hp']}")
    
    xp_max = player.get("level", 1) * 1000
    xp_current = player.get("xp", 0)
    xp_percent = max(0.0, min(1.0, xp_current / xp_max))
    st.progress(xp_percent, text=f"XP: {xp_current} / {xp_max}")
    
    st.write(f"**Level:** {player['level']} | **Col:** {player['col']} 🪙")
    
    st.divider()
    

    with st.expander("🧬 Character Build", expanded=False):
        st.write(f"**Race:** {player['race']}")
        st.write(f"**Class:** {player['class']}")
        st.write("**Core Stats:**")
        cols = st.columns(3)
        cols[0].write(f"STR: {player['stats']['STR']}")
        cols[1].write(f"DEX: {player['stats']['DEX']}")
        cols[2].write(f"CON: {player['stats']['CON']}")
        cols = st.columns(3)
        cols[0].write(f"INT: {player['stats']['INT']}")
        cols[1].write(f"WIS: {player['stats']['WIS']}")
        cols[2].write(f"CHA: {player['stats']['CHA']}")
        
    with st.expander("⚔️ Equipped Gear", expanded=False):
        st.write(f"- **Head:** {player['equipped']['head']}")
        st.write(f"- **Chest:** {player['equipped']['chest']}")
        st.write(f"- **Main:** {player['equipped']['main_hand']}")
        st.write(f"- **Off:** {player['equipped']['off_hand']}")
        st.write(f"- **Acc:** {player['equipped']['accessory']}")
        
    with st.expander("✨ Skills, Spells & Feats", expanded=False):
        if player['racial_abilities']:
            st.write("**Racial Traits:**")
            for r in player['racial_abilities']: st.write(f"- {r}")
            st.divider()
            
        for s_name, s_data in player.get('skills', {}).items():
            # Fallback in case of weird data structures
            if isinstance(s_data, dict):
                mastery = s_data.get('mastery', 1)
                desc = s_data.get('description', '')
            else:
                mastery = 1
                desc = str(s_data)
                
            st.write(f"**{s_name}** ({mastery}/1000)")
            st.progress(min(1.0, mastery / 1000.0))
            st.caption(desc)
            
        for s in player.get('spells', []) + player.get('feats', []):
            st.write(f"- {s}")
            
    with st.expander("🎒 Backpack Inventory", expanded=False):
        rarity_colors = {"Common": "⚪", "Uncommon": "🟢", "Rare": "🔵", "Epic": "🟣", "Legendary": "🟠", "Mythic": "🔴", "Unique": "✨"}
        for item in player.get("inventory", []):
            if isinstance(item, dict):
                icon = rarity_colors.get(item.get("rarity", "Common"), "⚪")
                st.write(f"{icon} **{item.get('name', 'Unknown')}** (x{item.get('qty', 1)})")
                st.caption(f"Durability: {item.get('durability', 0)}/{item.get('max_durability', 0)} | {item.get('desc', '')}")
            else:
                st.write(f"- {item}")
                
    with st.expander("📜 Active Quests & Bounties", expanded=True):
        if not player.get("quests"):
            st.caption("No active directives.")
        else:
            for q in player["quests"]:
                if isinstance(q, dict):
                    title = q.get('title', q.get('name', 'Unknown Quest'))
                    desc = q.get('desc', q.get('description', ''))
                    reward = q.get('reward', '')
                    st.markdown(f"🔸 **{title}**")
                    if desc: st.caption(desc)
                    if reward: st.markdown(f"🎁 *Reward:* {reward}")
                    st.divider()
                else:
                    st.markdown(f"🔸 {q}")
                    st.divider()
                
    with st.expander("🌍 Global Threat Intelligence", expanded=False):
        global_news = world_state.get("global_news", [])
        if not global_news:
            st.caption("No global uplinks established yet...")
        else:
            for news in reversed(global_news[-15:]):
                st.info(f"📡 {news}")
        

    st.divider()
    st.subheader("🎙️ Live Table Companion")
    st.caption("Stream your mic to the AI GM.")
    if st.toggle("Activate Microphone Module", value=False):
        with st.spinner("Minting secure token..."):
            import backend.auth as auth
            token = auth.get_ephemeral_token(api_key)
            
        import streamlit.components.v1 as components
        live_companion = components.declare_component("live_companion", path=os.path.join(BASE_DIR, "frontend"))
        
        # Pass the token down to the JS component. When the user stops recording, it returns Markdown.
        markdown_out = live_companion(token=token, default=None)
        
        if markdown_out:
            # Append the transcribed markdown to the chat automatically!
            st.session_state.messages.append({"role": "system", "content": f"**[LIVE COMPANION LOG]**\n{markdown_out}"})
            st.rerun()
            
    st.divider()
    st.subheader("🗺️ Sector 1 Map")
    import map_engine
    map_state = map_engine.load_map_state()
    player_skills = st.session_state.player.get("skills", [])
    map_path = map_engine.generate_overlay(player_skills=player_skills)
    if map_path and os.path.exists(map_path):
        import base64
        import streamlit.components.v1 as components
        with open(map_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        
        # Inject native inline mouse-wheel zoom & drag panning using Panzoom.js!
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <script src="https://unpkg.com/@panzoom/panzoom@4.5.1/dist/panzoom.min.js"></script>
        <style>
          body {{ margin: 0; padding: 0; overflow: hidden; background-color: transparent; }}
          #map-container {{ width: 100%; height: 100vh; display: flex; justify-content: center; align-items: center; }}
          img {{ max-width: 100%; max-height: 100%; object-fit: contain; cursor: grab; border-radius: 8px; }}
          img:active {{ cursor: grabbing; }}
        </style>
        </head>
        <body>
          <div id="map-container">
            <img id="map" src="data:image/jpeg;base64,{encoded_string}" />
          </div>
          <script>
            const elem = document.getElementById('map')
            const panzoom = Panzoom(elem, {{
              maxScale: 6,
              minScale: 1,
              contain: 'outside',
              step: 0.3
            }})
            elem.parentElement.addEventListener('wheel', panzoom.zoomWithWheel)
          </script>
        </body>
        </html>
        """
        components.html(html_code, height=350)
        
    st.write(f"**GPS Coordinates:** X: {map_state['player_x']}, Y: {map_state['player_y']}")
    st.write(f"**Status:** {world_state['world_status']}")

    st.divider()
    with st.expander("💻 Root Dev Console"):
        st.caption("Bypass the AI and edit the database directly.")
        st.session_state.player['hp'] = st.number_input("Set HP", value=player['hp'], step=10)
        st.session_state.player['max_hp'] = st.number_input("Set Max HP", value=player['max_hp'], step=10)
        st.session_state.player['level'] = st.number_input("Set Level", value=player.get('level', 1), step=1)
        st.session_state.player['xp'] = st.number_input("Set XP", value=player.get('xp', 0), step=100)
        st.session_state.player['col'] = st.number_input("Set Col", value=player['col'], step=100)
        
        st.write("**Set Core Stats**")
        c1, c2, c3 = st.columns(3)
        st.session_state.player['stats']['STR'] = c1.number_input("STR", value=player['stats']['STR'], step=1)
        st.session_state.player['stats']['DEX'] = c2.number_input("DEX", value=player['stats']['DEX'], step=1)
        st.session_state.player['stats']['CON'] = c3.number_input("CON", value=player['stats']['CON'], step=1)
        
        c4, c5, c6 = st.columns(3)
        st.session_state.player['stats']['INT'] = c4.number_input("INT", value=player['stats']['INT'], step=1)
        st.session_state.player['stats']['WIS'] = c5.number_input("WIS", value=player['stats']['WIS'], step=1)
        st.session_state.player['stats']['CHA'] = c6.number_input("CHA", value=player['stats']['CHA'], step=1)
        
        dev_cmd = st.text_input("Execute Root Command (Optional)")
        
        if st.button("Apply Database Override"):
            if dev_cmd:
                st.session_state.pending_dev_command = dev_cmd
            save_game(st.session_state.player, st.session_state.messages)
            st.rerun()

    st.divider()
    st.subheader("⏳ Time Control")
    if player.get("is_paused", False):
        st.warning("World is currently PAUSED.")
        if st.button("▶️ Resume World"):
            st.session_state.player["is_paused"] = False
            save_game(st.session_state.player, st.session_state.messages)
            st.rerun()
    else:
        st.success("World is ACTIVE.")
        if st.button("⏸️ Pause World"):
            st.session_state.player["is_paused"] = True
            save_game(st.session_state.player, st.session_state.messages)
            st.rerun()

    st.divider()
    with st.expander("💾 Save Management"):
        st.caption("Streamlit Cloud erases local files when it sleeps. Download your save file to keep your game safe!")
        
        # Export
        save_json = json.dumps({"player": st.session_state.player, "messages": st.session_state.messages, "last_saved": time.time()}, indent=4)
        st.download_button(
            label="📥 Export Save to Device",
            data=save_json,
            file_name=f"fractured_earth_save_{int(time.time())}.json",
            mime="application/json"
        )
        
        # Import
        st.divider()
        uploaded_file = st.file_uploader("📤 Import Save from Device", type="json")
        if uploaded_file is not None:
            if st.button("Restore Save"):
                try:
                    loaded_data = json.load(uploaded_file)
                    st.session_state.player = loaded_data["player"]
                    st.session_state.messages = loaded_data["messages"]
                    if "last_saved" in loaded_data:
                        save_game(st.session_state.player, st.session_state.messages)
                    st.success("Save loaded! Refreshing...")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to load save: {e}")

# --- MAIN UI: THE CHAT WINDOW ---
st.title("🗡️ The Fractured Overlay")
st.caption("A Death-Game TTRPG powered by the Cardinal System AI.")

# Render Chat History
for msg in st.session_state.messages:
    avatar = "👾" if msg["role"] == "system" else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg.get("image_data"):
            st.image(msg["image_data"], use_container_width=True)
        elif msg.get("image_path") and os.path.exists(msg["image_path"]):
            st.image(msg["image_path"], use_container_width=True)

# User Input
chat_prompt = st.chat_input("Action... (Type /admin to force an AI outcome)")
dev_prompt = st.session_state.pop("pending_dev_command", None)

if prompt := (dev_prompt or chat_prompt):
    
    # Intercept Admin Commands
    is_admin = prompt.startswith("/admin ") or dev_prompt is not None
    if is_admin:
        command = prompt.replace("/admin ", "")
        ui_text = f"💻 **ROOT OVERRIDE EXECUTED:** {command}"
        ai_prompt = f"[ROOT OVERRIDE] {command}"
    else:
        ui_text = prompt
        ai_prompt = prompt
        
    st.session_state.messages.append({"role": "user", "content": ui_text, "ai_prompt": ai_prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(ui_text)
        
    with st.chat_message("system", avatar="👾"):
        with st.spinner("The Cardinal System is generating the world..."):
            
            import map_engine
            current_ms = map_engine.load_map_state()
            
            # --- NEW TURN LOOP (V2 ARCHITECTURE) ---
            import backend.gm_engine as gm_engine
            import backend.actor_engine as actor_engine
            
            # a. Generate the Staging Ground (Visible Room)
            gm_engine.generate_visible_state(api_key=api_key)
            
            # b. Companions Act (Read Visible Room, Write to Queue)
            ren_action = actor_engine.get_companion_action(api_key=api_key, character_id="companion_ren")
            
            ren_intent = ren_action.get("intended_action", "Ren stands ready.")
            ren_thought = ren_action.get("internal_thought", "")
            ren_log = f"\n\n**[Ren's Tactical Logic]**\n> *{ren_thought}*\n> **Action:** {ren_intent}"
            
            # c. Resolve the turn (Read Player Action + Queue, Update Master State)
            turn_data = gm_engine.resolve_turn(api_key=api_key, player_action=ai_prompt)
            
            narrative = turn_data.get("narrative_recap", "Error parsing narrative.") + ren_log
            
            # Extract player state updates into the format app.py expects
            state_updates = turn_data.get("player_state_updates", {})
            if state_updates is None:
                state_updates = {}
                
            # Add HP changes to player state updates dynamically
            hp_changes = turn_data.get("hp_changes", {})
            if "player" in hp_changes:
                state_updates["hp_change"] = hp_changes["player"]
                
            # Fallback for old variables
            image_prompt = "" 
            
            # Apply State Updates
            if state_updates and isinstance(state_updates, dict):
                loc = state_updates.get("location")
                if loc and isinstance(loc, str):
                    st.session_state.player["location"] = loc
                    
                w_status = state_updates.get("world_status")
                news_add = state_updates.get("global_news_add", [])
                if not news_add:
                    news_add = turn_data.get("global_news_add", [])
                
                if w_status or news_add:
                    if w_status and isinstance(w_status, str):
                        world_state["world_status"] = w_status
                    if news_add and isinstance(news_add, list):
                        if "global_news" not in world_state: world_state["global_news"] = []
                        world_state["global_news"].extend(news_add)
                        
                    with open("world_state.json", "w") as f:
                        json.dump(world_state, f)
                    
                col_change = state_updates.get("col_change")
                if col_change:
                    try:
                        clean_col = str(col_change).replace(",", "").replace(" ", "")
                        st.session_state.player["col"] += int(clean_col)
                    except ValueError:
                        pass
                        
                discovered_nodes = state_updates.get("discovered_nodes", [])
                node_updates = state_updates.get("node_updates", {})
                
                coord_x = state_updates.get("coord_x")
                coord_y = state_updates.get("coord_y")
                
                if coord_x is not None or coord_y is not None or discovered_nodes or node_updates:
                    ms = map_engine.load_map_state()
                    if "dynamic_nodes" not in ms: ms["dynamic_nodes"] = []
                    if "node_overrides" not in ms: ms["node_overrides"] = {}
                    
                    if coord_x is not None: ms["player_x"] = int(coord_x)
                    if coord_y is not None: ms["player_y"] = int(coord_y)
                    if [ms["player_x"], ms["player_y"]] not in ms["explored_tiles"]:
                        ms["explored_tiles"].append([ms["player_x"], ms["player_y"]])
                        
                    if discovered_nodes:
                        for n in discovered_nodes:
                            if "name" in n and "x" in n and "y" in n:
                                ms["dynamic_nodes"].append(n)
                                
                    if node_updates and isinstance(node_updates, dict):
                        for n_key, color in node_updates.items():
                            ms["node_overrides"][n_key] = color
                                
                    map_engine.save_map_state(ms)

                hp_change = state_updates.get("hp_change")
                if hp_change:
                    try:
                        clean_hp = str(hp_change).replace(",", "").replace(" ", "")
                        st.session_state.player["hp"] = max(0, min(st.session_state.player["max_hp"], st.session_state.player["hp"] + int(clean_hp)))
                    except ValueError:
                        pass
                        
                xp_change = state_updates.get("xp_change")
                if xp_change:
                    try:
                        clean_xp = int(str(xp_change).replace(",", "").replace(" ", ""))
                        if clean_xp > 0:
                            st.session_state.player["xp"] += clean_xp
                            st.toast(f"✨ Gained {clean_xp} XP!")
                            
                            while st.session_state.player["xp"] >= st.session_state.player["level"] * 1000:
                                st.session_state.player["xp"] -= st.session_state.player["level"] * 1000
                                st.session_state.player["level"] += 1
                                st.session_state.player["max_hp"] += 25
                                st.session_state.player["hp"] = st.session_state.player["max_hp"]
                                for s in st.session_state.player["stats"]:
                                    st.session_state.player["stats"][s] += 1
                                st.balloons()
                                st.success(f"🎉 **LEVEL UP!** You are now Level {st.session_state.player['level']}! Max HP and Core Stats increased!")
                    except ValueError:
                        pass
                
                inv_add = state_updates.get("inventory_add") or []
                if isinstance(inv_add, list):
                    for item in inv_add:
                        if isinstance(item, dict) and "name" in item:
                            st.session_state.player["inventory"].append(item)
                        elif isinstance(item, str):
                            st.session_state.player["inventory"].append({"name": item, "rarity": "Common", "durability": 100, "max_durability": 100, "qty": 1, "desc": ""})
                            
                inv_remove = state_updates.get("inventory_remove") or []
                if isinstance(inv_remove, list):
                    for item_to_remove in inv_remove:
                        name_to_remove = item_to_remove.get("name", "").lower() if isinstance(item_to_remove, dict) else str(item_to_remove).lower()
                        for existing_item in st.session_state.player["inventory"][:]:
                            if isinstance(existing_item, dict) and name_to_remove in existing_item.get("name", "").lower():
                                st.session_state.player["inventory"].remove(existing_item)
                                break
                            elif isinstance(existing_item, str) and name_to_remove in existing_item.lower():
                                st.session_state.player["inventory"].remove(existing_item)
                                break
                                
                if state_updates.get("race"): st.session_state.player["race"] = state_updates["race"]
                if state_updates.get("class"): st.session_state.player["class"] = state_updates["class"]
                
                stat_changes = state_updates.get("stat_changes") or {}
                if isinstance(stat_changes, dict):
                    for stat, change in stat_changes.items():
                        if stat in st.session_state.player["stats"]:
                            st.session_state.player["stats"][stat] += int(change)
                            
                equip = state_updates.get("equip") or {}
                if isinstance(equip, dict):
                    for slot, item in equip.items():
                        if slot in st.session_state.player["equipped"]:
                            st.session_state.player["equipped"][slot] = item
                            
                skill_updates = state_updates.get("skill_updates") or []
                if isinstance(skill_updates, list):
                    for su in skill_updates:
                        if isinstance(su, dict) and "name" in su:
                            name = su["name"]
                            change = int(su.get("mastery_change", 1))
                            desc = su.get("description", "")
                            
                            if name in st.session_state.player["skills"]:
                                st.session_state.player["skills"][name]["mastery"] = min(1000, st.session_state.player["skills"][name]["mastery"] + change)
                                if desc: st.session_state.player["skills"][name]["description"] = desc
                            else:
                                st.session_state.player["skills"][name] = {"mastery": max(1, change), "description": desc}
                                
                for k in ["spells_add", "feats_add", "racial_abilities_add"]:
                    adds = state_updates.get(k) or []
                    if isinstance(adds, list):
                        target_list = k.replace("_add", "")
                        for a in adds:
                            if a not in st.session_state.player[target_list]:
                                st.session_state.player[target_list].append(a)
                                
                for k in ["spells_remove", "feats_remove", "racial_abilities_remove"]:
                    removes = state_updates.get(k) or []
                    if isinstance(removes, list):
                        target_list = k.replace("_remove", "")
                        for item_to_remove in removes:
                            for existing_item in st.session_state.player[target_list][:]:
                                if str(item_to_remove).lower() in existing_item.lower():
                                    st.session_state.player[target_list].remove(existing_item)
                                    break
                                    
                for q in state_updates.get("quests_add", []):
                    new_title = q.get('title', q.get('name', str(q))) if isinstance(q, dict) else str(q)
                    exists = False
                    for active_q in st.session_state.player["quests"]:
                        active_title = active_q.get('title', active_q.get('name', str(active_q))) if isinstance(active_q, dict) else str(active_q)
                        if new_title.lower() == active_title.lower():
                            exists = True
                            break
                    if not exists:
                        st.session_state.player["quests"].append(q)
                        st.toast(f"📜 New Quest Accepted: {new_title}")
                        
                for q in state_updates.get("quests_complete", []):
                    search_title = q.get('title', q.get('name', str(q))) if isinstance(q, dict) else str(q)
                    for active_q in st.session_state.player["quests"][:]:
                        active_title = active_q.get('title', active_q.get('name', str(active_q))) if isinstance(active_q, dict) else str(active_q)
                        if search_title.lower() in active_title.lower():
                            st.session_state.player["quests"].remove(active_q)
                            st.toast(f"✅ Quest Completed: {active_title}")
                            st.balloons()
                            break
                            
                for q in state_updates.get("quests_remove", []):
                    search_title = q.get('title', q.get('name', str(q))) if isinstance(q, dict) else str(q)
                    for active_q in st.session_state.player["quests"][:]:
                        active_title = active_q.get('title', active_q.get('name', str(active_q))) if isinstance(active_q, dict) else str(active_q)
                        if search_title.lower() in active_title.lower():
                            st.session_state.player["quests"].remove(active_q)
                            break

            combat_logs = turn_data.get("combat_logs", [])
            log_markdown = ""
            if combat_logs and isinstance(combat_logs, list):
                for log in combat_logs:
                    if "CRITICAL" in log.upper() or "FAIL" in log.upper() or "MISS" in log.upper():
                        st.error(f"💥 **{log}**")
                    elif "DAMAGE" in log.upper() or "DMG" in log.upper():
                        st.warning(f"🩸 {log}")
                    elif "ROLL" in log.upper():
                        st.info(f"🎲 {log}")
                    else:
                        st.info(f"⚔️ {log}")
                    log_markdown += f"> 🎲 `{log}`\n>\n"
                
                if log_markdown:
                    narrative = log_markdown + "\n\n" + narrative
            
            st.markdown(narrative)
            
            image_data = None
            if image_prompt:
                image_bytes, img_error = llm_engine.generate_scene_image(api_key, image_prompt)
                if image_bytes:
                    b64_img = base64.b64encode(image_bytes).decode("utf-8")
                    image_data = f"data:image/png;base64,{b64_img}"
                    st.image(image_data, use_container_width=True)
                elif img_error:
                    narrative += f"\n\n*(System Note: Image Generation Failed - {img_error})*"
            
    new_msg = {
        "role": "system", 
        "content": narrative,
        "image_data": image_data
    }
    st.session_state.messages.append(new_msg)
    save_game(st.session_state.player, st.session_state.messages)
    
    st.rerun()
