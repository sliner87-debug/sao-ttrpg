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
            "location": "The Safe-Zone: Yoyogi Park"
        }

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
    st.subheader("🎒 Inventory")
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
        
        if st.button("Apply Database Override"):
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
if prompt := st.chat_input("Action... (Type /admin to force an AI outcome)"):
    
    # Intercept Admin Commands
    is_admin = prompt.startswith("/admin ")
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
