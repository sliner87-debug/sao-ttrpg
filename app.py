import streamlit as st
import json
import os
import time
import importlib
import base64
import backend.llm_engine as llm_engine
importlib.reload(llm_engine)

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
    st.session_state.offline_processed = False

if not st.session_state.offline_processed and saved_data and "last_saved" in saved_data:
    is_paused = saved_data["player"].get("is_paused", False)
    
    if is_paused:
        # If paused, just update last_saved so offline time isn't retroactively accumulated
        save_game(saved_data["player"], saved_data["messages"])
    else:
        time_offline = time.time() - saved_data["last_saved"]
        minutes_offline = int(time_offline / 60)
        
        # Trigger if offline for more than 1 minute (adjustable later)
        if minutes_offline >= 1:
            with st.spinner(f"Synchronizing Offline Avatar Activity ({minutes_offline} minutes)..."):
                idle_data = llm_engine.generate_idle_summary(api_key, saved_data["player"], minutes_offline)
                
                # Update Player State
                col_gained = idle_data.get("col_gained", 0)
                xp_gained = idle_data.get("xp_gained", 0)
                items = idle_data.get("items_found", [])
                
                saved_data["player"]["col"] += col_gained
                saved_data["player"]["inventory"].extend(items)
                
                # Create a System Message
                narrative = f"### 💤 Offline Synchronization Complete\n\n**Time Offline:** {minutes_offline} minutes\n\n{idle_data.get('narrative')}\n\n**Rewards:**\n- Col: +{col_gained}\n- XP: +{xp_gained}\n- Items Found: {', '.join(items) if items else 'None'}"
                
                saved_data["messages"].append({
                    "role": "system",
                    "content": narrative,
                    "image_path": None
                })
                save_game(saved_data["player"], saved_data["messages"])
            
    st.session_state.offline_processed = True

if "player" not in st.session_state:
    if saved_data:
        st.session_state.player = saved_data["player"]
    else:
        st.session_state.player = {
            "name": "TestSubject_01",
            "level": 1,
            "hp": 100,
            "max_hp": 100,
            "col": 0,
            "inventory": ["Iron Sword", "Bottled Water x2", "Mysterious USB Drive"],
            "location": "Sector 1 Safe-Zone: Washington Borough, NJ"
        }
        
    # Migration: Ensure new database keys exist for old save files
    p = st.session_state.player
    p.setdefault("race", "Unregistered Anomaly")
    p.setdefault("class", "Pathless (Freeform)")
    p.setdefault("stats", {"STR": 10, "DEX": 10, "CON": 10, "INT": 10, "WIS": 10, "CHA": 10})
    p.setdefault("skills", [])
    p.setdefault("spells", [])
    p.setdefault("feats", [])
    p.setdefault("racial_abilities", [])
    p.setdefault("equipped", {"head": "None", "chest": "None", "main_hand": "None", "off_hand": "None", "accessory": "None"})

if "messages" not in st.session_state:
    if saved_data:
        st.session_state.messages = saved_data["messages"]
    else:
        st.session_state.messages = [
            {
                "role": "system", 
                "content": "### SYSTEM ANNOUNCEMENT\n\n**LINK START.**\n\nWelcome to Sector 1. The Logout button has been permanently removed. If your HP reaches 0, the headset will fry your brain. Good luck.",
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
    
    st.write(f"**Level:** {player['level']}")
    st.write(f"**Col (Currency):** {player['col']} 🪙")
    
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
        
    with st.expander("⚔️ Equipped Gear & Abilities", expanded=False):
        st.write("**Active Loadout:**")
        st.write(f"- **Head:** {player['equipped']['head']}")
        st.write(f"- **Chest:** {player['equipped']['chest']}")
        st.write(f"- **Main:** {player['equipped']['main_hand']}")
        st.write(f"- **Off:** {player['equipped']['off_hand']}")
        st.write(f"- **Acc:** {player['equipped']['accessory']}")
        
        if player['racial_abilities']:
            st.write("**Racial Traits:**")
            for r in player['racial_abilities']: st.write(f"- {r}")
        if player['skills'] or player['spells'] or player['feats']:
            st.write("**Skills & Spells:**")
            for s in player['skills'] + player['spells'] + player['feats']: st.write(f"- {s}")
            
    with st.expander("🎒 Backpack Inventory", expanded=False):
        for item in player["inventory"]:
            st.write(f"- {item}")
        
    st.divider()
    st.subheader("🗺️ World Data")
    st.write(f"**Current Sector:** {world_state['sector']}")
    st.write(f"**Status:** {world_state['world_status']}")
    st.write(f"**Current Location:** {player['location']}")

    st.divider()
    with st.expander("💻 Root Dev Console"):
        st.caption("Bypass the AI and edit the database directly.")
        st.session_state.player['hp'] = st.number_input("Set HP", value=player['hp'], step=10)
        st.session_state.player['max_hp'] = st.number_input("Set Max HP", value=player['max_hp'], step=10)
        st.session_state.player['level'] = st.number_input("Set Level", value=player['level'], step=1)
        st.session_state.player['col'] = st.number_input("Set Col", value=player['col'], step=100)
        
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
            
            # 1. Generate Narrative Text
            turn_data = llm_engine.generate_turn(
                api_key=api_key,
                user_input=ai_prompt,
                chat_history=st.session_state.messages,
                player_state=st.session_state.player,
                world_state=world_state
            )
            
            narrative = turn_data.get("narrative", "Error parsing narrative.")
            image_prompt = turn_data.get("image_prompt", "")
            state_updates = turn_data.get("state_updates", {})
            
            # Apply State Updates
            if state_updates and isinstance(state_updates, dict):
                loc = state_updates.get("location")
                if loc and isinstance(loc, str):
                    st.session_state.player["location"] = loc
                    
                col_change = state_updates.get("col_change")
                if col_change:
                    try:
                        # Handle strings like "-426,200" or ints
                        clean_col = str(col_change).replace(",", "").replace(" ", "")
                        st.session_state.player["col"] += int(clean_col)
                    except ValueError:
                        pass
                    
                hp_change = state_updates.get("hp_change")
                if hp_change:
                    try:
                        clean_hp = str(hp_change).replace(",", "").replace(" ", "")
                        st.session_state.player["hp"] = max(0, min(st.session_state.player["max_hp"], st.session_state.player["hp"] + int(clean_hp)))
                    except ValueError:
                        pass
                
                inv_add = state_updates.get("inventory_add") or []
                if isinstance(inv_add, list):
                    for item in inv_add:
                        st.session_state.player["inventory"].append(str(item))
                        
                inv_remove = state_updates.get("inventory_remove") or []
                if isinstance(inv_remove, list):
                    for item_to_remove in inv_remove:
                        for existing_item in st.session_state.player["inventory"][:]:
                            if str(item_to_remove).lower() in existing_item.lower():
                                st.session_state.player["inventory"].remove(existing_item)
                                break
                                
                # Extended Character Sheet Crunch Updates
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
                            
                for k in ["skills_add", "spells_add", "feats_add", "racial_abilities_add"]:
                    adds = state_updates.get(k) or []
                    if isinstance(adds, list):
                        target_list = k.replace("_add", "")
                        for a in adds:
                            if a not in st.session_state.player[target_list]:
                                st.session_state.player[target_list].append(a)
            
            st.markdown(narrative)
            
            # 2. Generate Scene Image & Encode to Base64
            image_data = None
            if image_prompt:
                image_bytes, img_error = llm_engine.generate_scene_image(api_key, image_prompt)
                if image_bytes:
                    b64_img = base64.b64encode(image_bytes).decode("utf-8")
                    image_data = f"data:image/png;base64,{b64_img}"
                    st.image(image_data, use_container_width=True)
                elif img_error:
                    narrative += f"\n\n*(System Note: Image Generation Failed - {img_error})*"
            
    # Save to history & trigger Autosave
    new_msg = {
        "role": "system", 
        "content": narrative,
        "image_data": image_data
    }
    st.session_state.messages.append(new_msg)
    save_game(st.session_state.player, st.session_state.messages)
    
    st.rerun()
