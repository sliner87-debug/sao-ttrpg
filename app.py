import streamlit as st
import json
import copy
import os
import time
import importlib
import base64
import backend.llm_engine as llm_engine
importlib.reload(llm_engine)
import backend.mechanics as mechanics
importlib.reload(mechanics)
import backend.character_generator as cg
importlib.reload(cg)

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
SAVES_DIR = os.path.join(BASE_DIR, 'saves')
if not os.path.exists(SAVES_DIR):
    os.makedirs(SAVES_DIR, exist_ok=True)

# --- PROFILE & SAVE/LOAD LOGIC ---
@st.cache_data
def load_world():
    if os.path.exists(WORLD_PATH):
        with open(WORLD_PATH, 'r') as f:
            return json.load(f)
    return {"sector": 1, "world_status": "OFFLINE", "map_locations": []}

world_state = load_world()

def get_available_profiles():
    if not os.path.exists(SAVES_DIR):
        os.makedirs(SAVES_DIR, exist_ok=True)
    files = [f for f in os.listdir(SAVES_DIR) if f.endswith('.json')]
    profiles = [os.path.splitext(f)[0] for f in files]
    
    # Ensure Banki profile is seeded if not present
    if "Banki" not in profiles:
        seed_data = None
        if os.path.exists(SAVE_PATH):
            try:
                with open(SAVE_PATH, 'r') as f:
                    seed_data = json.load(f)
            except Exception:
                pass
        if not seed_data and os.path.exists(os.path.join(BASE_DIR, 'save1.json')):
            try:
                with open(os.path.join(BASE_DIR, 'save1.json'), 'r') as f:
                    seed_data = json.load(f)
            except Exception:
                pass
        if seed_data and isinstance(seed_data, dict) and "player" in seed_data:
            seed_data["player"]["name"] = "Banki"
            banki_file = os.path.join(SAVES_DIR, 'Banki.json')
            with open(banki_file, 'w') as f:
                json.dump(seed_data, f, indent=4)
            profiles.append("Banki")
    return sorted(list(set(profiles)))

def load_game():
    active_prof = st.session_state.get("active_profile")
    if active_prof:
        prof_path = os.path.join(SAVES_DIR, f"{active_prof}.json")
        if os.path.exists(prof_path):
            with open(prof_path, 'r') as f:
                return json.load(f)
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
    # Also persist to dedicated profile file slot
    p_name = player_state.get("name")
    if p_name and p_name != "TestSubject_01":
        safe_slug = "".join(c for c in p_name if c.isalnum() or c in (' ', '_', '-')).strip()
        if safe_slug:
            slot_path = os.path.join(SAVES_DIR, f"{safe_slug}.json")
            with open(slot_path, 'w') as f:
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
if p.get("name") == "TestSubject_01" and (p.get("col", 0) > 1000 or p.get("stats", {}).get("STR", 10) > 20):
    p["name"] = "Banki"

if "character_creation_mode" not in st.session_state:
    if p.get("name") == "TestSubject_01" and p.get("col", 0) == 0:
        st.session_state.character_creation_mode = True
    else:
        st.session_state.character_creation_mode = False

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

# Migrate skills using mechanics engine with robust inline fallback
if hasattr(mechanics, "migrate_player_skills"):
    try:
        mechanics.migrate_player_skills(p)
    except Exception:
        pass

if not isinstance(p.get("skills"), dict):
    # Inline fallback normalization
    raw_skills = p.get("skills", {})
    norm_skills = {}

    def _calc_tier_fallback(m):
        m = max(1, min(1000, int(m)))
        if m < 50: return "Novice"
        if m < 100: return "Apprentice"
        if m < 250: return "Journeyman"
        if m < 500: return "Adept"
        if m < 750: return "Master"
        if m < 1000: return "Grandmaster"
        return "Transcendence"

    if isinstance(raw_skills, list):
        for s in raw_skills:
            if isinstance(s, str):
                name = s.split(":")[0].strip() if ":" in s else s.strip()
                val = 1
                if ":" in s:
                    try: val = int(s.split(":")[1].strip())
                    except ValueError: val = 1
                norm_skills[name] = {
                    "mastery": max(1, min(1000, val)),
                    "tier": _calc_tier_fallback(val),
                    "description": s,
                    "milestones_unlocked": []
                }
            elif isinstance(s, dict) and "name" in s:
                val = max(1, min(1000, int(s.get("mastery", 1))))
                norm_skills[s["name"]] = {
                    "mastery": val,
                    "tier": s.get("tier", _calc_tier_fallback(val)),
                    "description": s.get("description", ""),
                    "milestones_unlocked": s.get("milestones_unlocked", [])
                }
    p["skills"] = norm_skills

p.setdefault("racial_abilities", [])
p.setdefault("equipped", {"head": "None", "chest": "None", "main_hand": "None", "off_hand": "None", "accessory": "None"})
p.setdefault("gear_durability", {
    "head": {"cur": 100, "max": 100},
    "chest": {"cur": 250, "max": 250},
    "main_hand": {"cur": 200, "max": 200},
    "off_hand": {"cur": 200, "max": 200},
    "accessory": {"cur": 50, "max": 50}
})
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
                "content": "### SYSTEM ANNOUNCEMENT\n\n**LINK START.**\n\nWelcome to Sector 1. The Logout button has been permanently removed. If your HP reaches 0, the headset will fry your brain. Good luck.",
            }
        ]

# --- CHARACTER GENERATOR & CALIBRATION INTERFACE ---
def render_sidebar_calibration_preview():
    char_name = st.session_state.get("cg_name", "Survivor")
    st.subheader(f"Avatar: {char_name}")
    
    prev_race = cg.RACIAL_LINEAGES.get(st.session_state.get("cg_race_key", "pure_human"), cg.RACIAL_LINEAGES["pure_human"])
    prev_class = cg.CLASS_PATHS.get(st.session_state.get("cg_class_key", "pathless"), cg.CLASS_PATHS["pathless"])
    prev_relic = cg.PERSONAL_RELICS.get(st.session_state.get("cg_relic_key", "smartphone"), cg.PERSONAL_RELICS["smartphone"])
    
    pt_alloc = st.session_state.get("cg_points", {"STR": 0, "DEX": 0, "CON": 0, "INT": 0, "WIS": 0, "CHA": 0})
    prev_stats = {
        s: 10 + pt_alloc.get(s, 0) + prev_race["stat_mods"].get(s, 0)
        for s in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    }
    con_m = (prev_stats["CON"] - 10) // 2
    prev_hp = 100 + (con_m * 10)
    
    class_def_w = cg.CLASS_WEAPONS.get(st.session_state.get("cg_class_key", "pathless"), cg.CLASS_WEAPONS["pathless"])
    main_w = st.session_state.get("cg_main_hand", class_def_w["main_hand"]) if st.session_state.get("cg_custom_weapons", False) else class_def_w["main_hand"]
    off_w = st.session_state.get("cg_off_hand", class_def_w["off_hand"]) if st.session_state.get("cg_custom_weapons", False) else class_def_w["off_hand"]
    
    mock_p = {
        "name": char_name,
        "level": 1,
        "hp": prev_hp,
        "max_hp": prev_hp,
        "col": 100,
        "stats": prev_stats,
        "equipped": {
            "head": "None", 
            "chest": "Threadbare Scavenger Tunic", 
            "main_hand": main_w, 
            "off_hand": off_w, 
            "accessory": prev_relic["name"] if ("Watch" in prev_relic["name"] or "Tool" in prev_relic["name"]) else "None"
        },
        "inventory": [prev_relic, {"name": main_w, "qty": 1}, {"name": "Bottled Water", "qty": 2}, {"name": "Survival Rations", "qty": 2}]
    }
    if off_w and off_w != "None":
        mock_p["inventory"].append({"name": off_w, "qty": 1})
        
    mock_enc = mechanics.calculate_encumbrance(mock_p)
    mock_ac = mechanics.calculate_ac(mock_p, mock_enc)
    
    st.progress(1.0, text=f"HP: {prev_hp} / {prev_hp}")
    st.progress(0.0, text="XP: 0 / 1000")
    st.write(f"**Level:** 1 | **AC:** {mock_ac} 🛡️ | **Col:** 100 🪙")
    
    st.divider()
    with st.expander("🧬 Live Build Preview", expanded=True):
        st.write(f"**Race:** {prev_race['name']}")
        st.write(f"**Class:** {prev_class['title']}")
        st.write(f"**Main Hand:** {main_w}")
        st.write(f"**Off Hand:** {off_w}")
        st.write(f"**Relic:** {prev_relic['name']}")
        st.write("**Derived Stats:**")
        c_s1, c_s2, c_s3 = st.columns(3)
        c_s1.write(f"STR: {prev_stats['STR']}")
        c_s2.write(f"DEX: {prev_stats['DEX']}")
        c_s3.write(f"CON: {prev_stats['CON']}")
        c_s4, c_s5, c_s6 = st.columns(3)
        c_s4.write(f"INT: {prev_stats['INT']}")
        c_s5.write(f"WIS: {prev_stats['WIS']}")
        c_s6.write(f"CHA: {prev_stats['CHA']}")
        
    with st.expander("⚖️ Carry Physics Preview", expanded=False):
        st.write(f"**Status:** {mock_enc['label']}")
        st.progress(mock_enc['weight_percent'], text=f"Weight: {mock_enc['current_weight_lbs']} / {mock_enc['max_weight_lbs']} lbs")
        st.progress(mock_enc['slots_percent'], text=f"Slots: {mock_enc['used_slots']} / {mock_enc['max_slots']} slots")
        
    with st.expander("✨ Starting Skills & Feats Preview", expanded=False):
        bg_key = st.session_state.get("cg_bg_key", "software_engineer")
        if bg_key == "custom" and st.session_state.get("cg_custom_bg_text"):
            bg_data = cg.parse_custom_background(st.session_state.get("cg_custom_bg_text"))
        else:
            bg_data = cg.PRESET_BACKGROUNDS.get(bg_key, cg.PRESET_BACKGROUNDS["software_engineer"])
            
        st.markdown("**Skills:**")
        for sname, sinfo in bg_data.get("skills", {}).items():
            st.markdown(f"- **{sname}** `[{sinfo['mastery']}/1000]` *[{sinfo['tier']}]*")
        st.markdown("**Innate Background Perk:**")
        st.caption(bg_data.get("innate_perk", "None"))
        st.markdown("**Class Starting Feats:**")
        for cf in prev_class.get("starting_feats", []):
            st.caption(f"- {cf}")
        st.markdown("**Racial Lineage Abilities:**")
        for ra in prev_race.get("racial_abilities", []):
            st.caption(f"- {ra}")


def render_character_calibration_wizard():
    if "cg_name" not in st.session_state:
        st.session_state.cg_name = "Survivor"
    if "cg_points" not in st.session_state:
        st.session_state.cg_points = {"STR": 0, "DEX": 0, "CON": 0, "INT": 0, "WIS": 0, "CHA": 0}
    if "cg_bg_key" not in st.session_state:
        st.session_state.cg_bg_key = "software_engineer"
    if "cg_custom_bg_text" not in st.session_state:
        st.session_state.cg_custom_bg_text = ""
    if "cg_race_key" not in st.session_state:
        st.session_state.cg_race_key = "pure_human"
    if "cg_class_key" not in st.session_state:
        st.session_state.cg_class_key = "pathless"
    if "cg_relic_key" not in st.session_state:
        st.session_state.cg_relic_key = "smartphone"
    if "cg_custom_weapons" not in st.session_state:
        st.session_state.cg_custom_weapons = False
    if "cg_main_hand" not in st.session_state:
        st.session_state.cg_main_hand = "Rusted Iron Sword"
    if "cg_off_hand" not in st.session_state:
        st.session_state.cg_off_hand = "None"

    # Header & Cancel Bar
    top_c1, top_c2 = st.columns([4, 1])
    with top_c1:
        st.title("🧬 Cardinal System Calibration Protocol")
        st.caption("Translate your Pre-Integration Earth identity into Post-Integration LitRPG attributes, skills, and gear.")
    with top_c2:
        if st.button("❌ Exit Calibration", use_container_width=True, key="btn_exit_calib_top"):
            st.session_state.character_creation_mode = False
            st.rerun()

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "1. 📊 Stat Calibration", 
        "2. 💼 Earth Vocation", 
        "3. 🧬 Genetic Lineage", 
        "4. ⚔️ Class Doctrine", 
        "5. 🎒 Relic & Gear"
    ])

    # --- TAB 1: STAT CALIBRATION ---
    with tab1:
        st.markdown("### 📊 Stage 1: Identity & Stat Calibration")
        st.write("The Cardinal System scans your Pre-Integration biometric residue. You begin with a baseline score of **10** across all six core attributes, and possess a calibration pool of **20 points** to distribute based on your Earth lifestyle and physical conditioning.")
        
        st.session_state.cg_name = st.text_input(
            "Avatar Callsign / Real Name:",
            value=st.session_state.cg_name,
            key="cg_name_input_field",
            placeholder="e.g. Banki, Vance, Kaito, Marcus..."
        ).strip()
        
        total_allocated = sum(st.session_state.cg_points.values())
        pts_left = 20 - total_allocated
        
        # Budget Indicator
        if pts_left > 0:
            st.info(f"⚡ Calibration Pool Remaining: **{pts_left} / 20** points available.")
        elif pts_left == 0:
            st.success("✅ Calibration Pool: Exactly **20 / 20** points allocated! Ready for confirmation.")
        else:
            st.error(f"⚠️ Calibration Pool Overdrawn: **{total_allocated} / 20** points ({abs(pts_left)} too many)! Please reduce allocated points.")

        # Quick-Lifestyle Questionnaire Presets
        with st.expander("⚡ Quick-Lifestyle Questionnaire Presets (Auto-Distribute 20 Points)", expanded=False):
            st.caption("Click any Pre-Integration Earth archetype to instantly auto-distribute your 20 calibration points:")
            q_cols1 = st.columns(4)
            if q_cols1[0].button("🛋️ Desk Bound (+Mental)", use_container_width=True, key="preset_desk"):
                st.session_state.cg_points = {"STR": 1, "DEX": 1, "CON": 2, "INT": 6, "WIS": 6, "CHA": 4}
                st.rerun()
            if q_cols1[1].button("🏃 Athletic (+Agility)", use_container_width=True, key="preset_athletic"):
                st.session_state.cg_points = {"STR": 5, "DEX": 6, "CON": 4, "INT": 1, "WIS": 2, "CHA": 2}
                st.rerun()
            if q_cols1[2].button("🔨 Heavy Labor (+STR/CON)", use_container_width=True, key="preset_labor"):
                st.session_state.cg_points = {"STR": 7, "DEX": 3, "CON": 6, "INT": 1, "WIS": 2, "CHA": 1}
                st.rerun()
            if q_cols1[3].button("🎖️ First Responder (+Combat)", use_container_width=True, key="preset_responder"):
                st.session_state.cg_points = {"STR": 5, "DEX": 5, "CON": 4, "INT": 2, "WIS": 3, "CHA": 1}
                st.rerun()

            q_cols2 = st.columns(4)
            if q_cols2[0].button("🔬 Academic (+INT)", use_container_width=True, key="preset_academic"):
                st.session_state.cg_points = {"STR": 2, "DEX": 2, "CON": 2, "INT": 7, "WIS": 5, "CHA": 2}
                st.rerun()
            if q_cols2[1].button("🏙️ Street Smart (+WIS/CHA)", use_container_width=True, key="preset_street"):
                st.session_state.cg_points = {"STR": 2, "DEX": 4, "CON": 1, "INT": 2, "WIS": 5, "CHA": 6}
                st.rerun()
            if q_cols2[2].button("🎭 Performer (+CHA)", use_container_width=True, key="preset_performer"):
                st.session_state.cg_points = {"STR": 1, "DEX": 5, "CON": 2, "INT": 3, "WIS": 2, "CHA": 7}
                st.rerun()
            if q_cols2[3].button("🌲 Survivalist (+WIS/CON)", use_container_width=True, key="preset_survivalist"):
                st.session_state.cg_points = {"STR": 2, "DEX": 3, "CON": 4, "INT": 4, "WIS": 7, "CHA": 0}
                st.rerun()

        st.divider()
        st.markdown("#### 🎛️ Point-Buy Attribute Steppers")
        st.caption("Baseline: 10 in all attributes. Allocate points to increase your starting score:")
        
        race_info = cg.RACIAL_LINEAGES.get(st.session_state.cg_race_key, cg.RACIAL_LINEAGES["pure_human"])
        race_mods = race_info["stat_mods"]
        
        stat_c1, stat_c2 = st.columns(2)
        with stat_c1:
            st.markdown("##### 🏋️ Physical Attributes")
            for stat in ["STR", "DEX", "CON"]:
                cur = st.session_state.cg_points[stat]
                rmod = race_mods.get(stat, 0)
                rmod_str = f"+{rmod}" if rmod > 0 else (str(rmod) if rmod < 0 else "0")
                final_val = 10 + cur + rmod
                val = st.number_input(
                    f"{stat} (+points above 10 | Racial: {rmod_str} → Score: {final_val})",
                    min_value=0,
                    max_value=20,
                    value=cur,
                    step=1,
                    key=f"stepper_{stat}"
                )
                st.session_state.cg_points[stat] = val
        with stat_c2:
            st.markdown("##### 🧠 Mental & Social Attributes")
            for stat in ["INT", "WIS", "CHA"]:
                cur = st.session_state.cg_points[stat]
                rmod = race_mods.get(stat, 0)
                rmod_str = f"+{rmod}" if rmod > 0 else (str(rmod) if rmod < 0 else "0")
                final_val = 10 + cur + rmod
                val = st.number_input(
                    f"{stat} (+points above 10 | Racial: {rmod_str} → Score: {final_val})",
                    min_value=0,
                    max_value=20,
                    value=cur,
                    step=1,
                    key=f"stepper_{stat}"
                )
                st.session_state.cg_points[stat] = val

    # --- TAB 2: EARTH VOCATION ---
    with tab2:
        st.markdown("### 💼 Stage 2: Earth Career-to-Skill Translation Matrix")
        st.write("Your career, trade, and personal hobbies before the integration determine your initial **1–1000 Skill Masteries** and unlock your first innate passive perk.")
        
        v_mode = st.radio(
            "Vocation Input Mode:",
            ["Preset Earth Vocations (Recommended)", "Custom Earth Life Description (Procedural Mapping)"],
            horizontal=True,
            key="vocation_mode_radio"
        )
        
        if v_mode.startswith("Preset"):
            bg_keys = list(cg.PRESET_BACKGROUNDS.keys())
            bg_titles = [cg.PRESET_BACKGROUNDS[k]["title"] for k in bg_keys]
            
            cur_bg_idx = bg_keys.index(st.session_state.cg_bg_key) if st.session_state.cg_bg_key in bg_keys else 0
            sel_bg_title = st.selectbox(
                "Choose Earth Profession:",
                options=bg_titles,
                index=cur_bg_idx,
                key="sel_preset_bg_box"
            )
            selected_bg_key = bg_keys[bg_titles.index(sel_bg_title)]
            st.session_state.cg_bg_key = selected_bg_key
            bg_obj = cg.PRESET_BACKGROUNDS[selected_bg_key]
            
            st.info(f"**Career Summary:** {bg_obj['description']}")
            
            st.markdown("##### ⚔️ Post-Integration Starting Skills (1-1000 System):")
            for sname, sdata in bg_obj["skills"].items():
                m_val = sdata["mastery"]
                tier = sdata["tier"]
                st.write(f"**{sname}** `[{m_val} / 1000]` *[{tier}]* - {sdata['description']}")
                st.progress(m_val / 1000.0)
                
            st.markdown("##### 🎖️ Innate Vocation Perk:")
            st.success(f"🔹 **{bg_obj['innate_perk']}**")
        else:
            st.session_state.cg_bg_key = "custom"
            st.markdown("##### ✍️ Custom Earth Life Description:")
            st.session_state.cg_custom_bg_text = st.text_area(
                "Describe your pre-collapse profession, trade, or daily hobbies:",
                value=st.session_state.cg_custom_bg_text,
                placeholder="e.g. I worked as an industrial high-voltage electrician, played rugby on weekends, and spent time restoring vintage motorcycles...",
                height=110,
                key="custom_bg_input_area"
            )
            
            parsed = cg.parse_custom_background(st.session_state.cg_custom_bg_text)
            st.markdown(f"##### 🧬 Cardinal System Procedural Analysis: *{parsed['title']}*")
            st.markdown("##### ⚔️ Derived Starting Skills (1-1000 System):")
            for sname, sdata in parsed["skills"].items():
                m_val = sdata["mastery"]
                tier = sdata["tier"]
                st.write(f"**{sname}** `[{m_val} / 1000]` *[{tier}]* - {sdata['description']}")
                st.progress(m_val / 1000.0)
                
            st.markdown("##### 🎖️ Derived Innate Perk:")
            st.success(f"🔹 **{parsed['innate_perk']}**")

    # --- TAB 3: GENETIC LINEAGE ---
    with tab3:
        st.markdown("### 🧬 Stage 3: Genetic Rift Mutation (Racial Lineage)")
        st.write("When the Aetheric Rift collapsed into Earth, ambient leylines permeated human biology. Survivors either resisted mutation or adapted into new physical lineages.")
        
        race_keys = list(cg.RACIAL_LINEAGES.keys())
        race_names = [cg.RACIAL_LINEAGES[k]["name"] for k in race_keys]
        cur_r_idx = race_keys.index(st.session_state.cg_race_key) if st.session_state.cg_race_key in race_keys else 0
        
        sel_race_name = st.selectbox(
            "Select Lineage / Mutation:",
            options=race_names,
            index=cur_r_idx,
            key="sel_race_box"
        )
        selected_race_key = race_keys[race_names.index(sel_race_name)]
        st.session_state.cg_race_key = selected_race_key
        race_obj = cg.RACIAL_LINEAGES[selected_race_key]
        
        st.info(f"**Lineage Lore:** {race_obj['desc']}")
        
        st.markdown("##### ⚖️ Racial Stat Modifiers:")
        m_cols = st.columns(6)
        for idx, s in enumerate(["STR", "DEX", "CON", "INT", "WIS", "CHA"]):
            m_val = race_obj["stat_mods"].get(s, 0)
            sign = f"+{m_val}" if m_val > 0 else (str(m_val) if m_val < 0 else "0")
            m_cols[idx].metric(label=s, value=sign)
            
        st.markdown("##### 🧬 Racial Abilities & Traits:")
        for ab in race_obj["racial_abilities"]:
            if "Flaw" in ab:
                st.warning(f"⚠️ {ab}")
            else:
                st.success(f"✨ {ab}")

    # --- TAB 4: CLASS DOCTRINE ---
    with tab4:
        st.markdown("### ⚔️ Stage 4: Combat Doctrine & Class Path")
        st.write("Choose your philosophical approach to surviving the death-game. Structured classes provide specialized tactical frameworks, while the Pathless walk an unconstrained anomaly path.")
        
        class_keys = list(cg.CLASS_PATHS.keys())
        class_titles = [cg.CLASS_PATHS[k]["title"] for k in class_keys]
        cur_c_idx = class_keys.index(st.session_state.cg_class_key) if st.session_state.cg_class_key in class_keys else 0
        
        sel_class_title = st.selectbox(
            "Select Combat Doctrine:",
            options=class_titles,
            index=cur_c_idx,
            key="sel_class_box"
        )
        selected_class_key = class_keys[class_titles.index(sel_class_title)]
        st.session_state.cg_class_key = selected_class_key
        class_obj = cg.CLASS_PATHS[selected_class_key]
        
        st.info(f"**Doctrine Summary:** {class_obj['description']}")
        
        st.markdown("##### 🎖️ Starting Class Feats & Techniques:")
        for cf in class_obj["starting_feats"]:
            st.success(f"🔹 **{cf}**")
            
        def_w = cg.CLASS_WEAPONS.get(selected_class_key, cg.CLASS_WEAPONS["pathless"])
        st.caption(f"Default Combat Loadout: **{def_w['main_hand']}** (Main) & **{def_w['off_hand']}** (Off) - *{def_w['desc']}*")

    # --- TAB 5: RELIC & GEAR ---
    with tab5:
        st.markdown("### 🎒 Stage 5: Earth Relic, Starting Gear & Link Start")
        st.write("Every survivor carries a haunting personal relic from old Earth, alongside scavenged survival supplies.")
        
        # Weapons Selection (Class Default with Manual Override)
        st.markdown("#### ⚔️ Starting Weapons")
        class_def_w = cg.CLASS_WEAPONS.get(st.session_state.cg_class_key, cg.CLASS_WEAPONS["pathless"])
        
        override_w = st.checkbox(
            "⚙️ Customize Starting Weapons (Manual Override)",
            value=st.session_state.cg_custom_weapons,
            key="cb_custom_weapons_tab5"
        )
        st.session_state.cg_custom_weapons = override_w
        
        if override_w:
            w_col1, w_col2 = st.columns(2)
            all_w_opts = cg.STARTER_WEAPON_OPTIONS
            
            cur_main = st.session_state.cg_main_hand if st.session_state.cg_main_hand in all_w_opts else class_def_w["main_hand"]
            cur_off = st.session_state.cg_off_hand if st.session_state.cg_off_hand in all_w_opts else class_def_w["off_hand"]
            
            st.session_state.cg_main_hand = w_col1.selectbox("Main Hand Weapon:", all_w_opts, index=all_w_opts.index(cur_main), key="sel_main_w_custom")
            st.session_state.cg_off_hand = w_col2.selectbox("Off Hand / Shield:", all_w_opts, index=all_w_opts.index(cur_off), key="sel_off_w_custom")
        else:
            st.session_state.cg_main_hand = class_def_w["main_hand"]
            st.session_state.cg_off_hand = class_def_w["off_hand"]
            st.info(f"**Assigned Weapons:** {class_def_w['main_hand']} (Main Hand) | {class_def_w['off_hand']} (Off Hand)")
            
        st.divider()
        # Personal Relic Selection
        st.markdown("#### 📱 Pre-Integration Earth Relic (Choose 1):")
        relic_keys = list(cg.PERSONAL_RELICS.keys())
        relic_names = [cg.PERSONAL_RELICS[k]["name"] for k in relic_keys]
        cur_relic_idx = relic_keys.index(st.session_state.cg_relic_key) if st.session_state.cg_relic_key in relic_keys else 0
        
        sel_relic_name = st.selectbox(
            "Choose Personal Relic:",
            options=relic_names,
            index=cur_relic_idx,
            key="sel_relic_box"
        )
        selected_relic_key = relic_keys[relic_names.index(sel_relic_name)]
        st.session_state.cg_relic_key = selected_relic_key
        relic_obj = cg.PERSONAL_RELICS[selected_relic_key]
        
        st.success(f"✨ **{relic_obj['name']}** [{relic_obj['rarity']}]")
        st.caption(f"{relic_obj['desc']}")
        
        # Starter Survival Cache Preview
        with st.expander("📦 Standard Survival Scrap Cache (Included)", expanded=False):
            st.markdown("- **Threadbare Scavenger Tunic** (Equipped Chest Armor, Durability 100/100)")
            st.markdown("- **Bottled Water x2** (Common sealed clean drinking water)")
            st.markdown("- **Survival Rations x2** (Common vacuum-sealed trail mix / nutrient paste)")
            st.markdown("- **100 Col** (Scavenged currency)")
            
        st.divider()
        
        # Live Calibration Confirmation Summary
        r_info = cg.RACIAL_LINEAGES.get(st.session_state.cg_race_key, cg.RACIAL_LINEAGES["pure_human"])
        c_info = cg.CLASS_PATHS.get(st.session_state.cg_class_key, cg.CLASS_PATHS["pathless"])
        
        final_scores = {
            s: 10 + st.session_state.cg_points.get(s, 0) + r_info["stat_mods"].get(s, 0)
            for s in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
        }
        calc_hp = 100 + ((final_scores["CON"] - 10) // 2) * 10
        
        st.markdown("### 📋 Final Calibration Review")
        rev_c1, rev_c2, rev_c3 = st.columns(3)
        rev_c1.metric("Callsign", st.session_state.cg_name)
        rev_c1.metric("Lineage", r_info["name"])
        rev_c2.metric("Doctrine", c_info["title"])
        rev_c2.metric("Starting HP", f"{calc_hp} HP")
        rev_c3.metric("Main Weapon", st.session_state.cg_main_hand)
        rev_c3.metric("Personal Relic", relic_obj["name"][:20] + "...")
        
        # Link Start Action Button
        st.write("")
        if st.button("⚡ INITIATE SYSTEM CALIBRATION // LINK START", type="primary", use_container_width=True, key="btn_link_start"):
            spent = sum(st.session_state.cg_points.values())
            if spent > 20:
                st.error(f"Cannot complete calibration: You have allocated {spent} / 20 points ({spent - 20} over limit). Please adjust in Tab 1.")
            else:
                char_name = st.session_state.cg_name.strip() if st.session_state.cg_name.strip() else "Survivor"
                
                new_avatar = cg.generate_starting_character(
                    name=char_name,
                    point_alloc=st.session_state.cg_points,
                    background_key=st.session_state.cg_bg_key,
                    race_key=st.session_state.cg_race_key,
                    class_key=st.session_state.cg_class_key,
                    relic_key=st.session_state.cg_relic_key,
                    custom_background_text=st.session_state.cg_custom_bg_text if st.session_state.cg_bg_key == "custom" else None,
                    starting_weapons={"main_hand": st.session_state.cg_main_hand, "off_hand": st.session_state.cg_off_hand}
                )
                
                opening_announcement = (
                    f"### SYSTEM ANNOUNCEMENT\n\n"
                    f"**LINK START.**\n\n"
                    f"Welcome to Sector 1, **{char_name}**.\n\n"
                    f"Biometric calibration complete:\n"
                    f"- **Lineage:** {new_avatar['race']}\n"
                    f"- **Doctrine:** {new_avatar['class']}\n"
                    f"- **Vitals:** {new_avatar['hp']}/{new_avatar['max_hp']} HP\n\n"
                    f"The Logout button has been permanently removed. If your HP reaches 0, the headset will fry your brain. Good luck."
                )
                
                st.session_state.player = new_avatar
                st.session_state.messages = [
                    {
                        "role": "system",
                        "content": opening_announcement,
                        "image_path": None
                    }
                ]
                st.session_state.active_profile = char_name
                st.session_state.character_creation_mode = False
                
                save_game(st.session_state.player, st.session_state.messages)
                st.balloons()
                st.success(f"Calibration Complete! Avatar **{char_name}** linked to the Cardinal System. Entering Sector 1 Safe-Zone...")
                time.sleep(1.0)
                st.rerun()


# --- SIDEBAR: HUD & INVENTORY ---
with st.sidebar:
    st.title("🛡️ Player HUD")
    
    # --- MULTI-CHARACTER PROFILE SLOT SELECTOR ---
    profiles = get_available_profiles()
    curr_name = st.session_state.player.get('name', 'Banki')
    default_idx = profiles.index(curr_name) if curr_name in profiles else 0
    
    st.markdown('##### 👤 Character Slot')
    sel_profile = st.selectbox(
        'Active Profile',
        options=profiles,
        index=default_idx,
        key='active_profile_select',
        label_visibility='collapsed'
    )
    if sel_profile != curr_name and not st.session_state.get('character_creation_mode', False):
        target_file = os.path.join(SAVES_DIR, f'{sel_profile}.json')
        if os.path.exists(target_file):
            with open(target_file, 'r', encoding='utf-8') as pf:
                p_data = json.load(pf)
            st.session_state.player = p_data['player']
            st.session_state.messages = p_data.get('messages', [])
            st.session_state.active_profile = sel_profile
            st.session_state.character_creation_mode = False
            save_game(st.session_state.player, st.session_state.messages)
            st.rerun()
            
    if not st.session_state.get('character_creation_mode', False):
        if st.button('🧬 New Avatar Calibration', use_container_width=True):
            st.session_state.character_creation_mode = True
            st.rerun()
    else:
        st.warning('⚡ Calibration Mode Active')
        if st.button('❌ Exit Calibration', use_container_width=True):
            st.session_state.character_creation_mode = False
            st.rerun()
            
    st.divider()
    
    if st.session_state.get('character_creation_mode', False):
        render_sidebar_calibration_preview()
    else:
        player = st.session_state.player
        st.subheader(player["name"])
    
        # Calculate live mechanics
        encumbrance = mechanics.calculate_encumbrance(player)
        armor_class = mechanics.calculate_ac(player, encumbrance)
    
        hp_percent = max(0.0, min(1.0, player["hp"] / player["max_hp"]))
        st.progress(hp_percent, text=f"HP: {player['hp']} / {player['max_hp']}")
    
        xp_max = player.get("level", 1) * 1000
        xp_current = player.get("xp", 0)
        xp_percent = max(0.0, min(1.0, xp_current / xp_max))
        st.progress(xp_percent, text=f"XP: {xp_current} / {xp_max}")
    
        st.write(f"**Level:** {player['level']} | **AC:** {armor_class} 🛡️ | **Col:** {player['col']} 🪙")
    
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
        
        with st.expander("⚖️ Encumbrance & Carry Physics", expanded=False):
            st.write(f"**Status:** {encumbrance['label']}")
            st.progress(encumbrance['weight_percent'], text=f"Weight: {encumbrance['current_weight_lbs']} / {encumbrance['max_weight_lbs']} lbs")
            st.progress(encumbrance['slots_percent'], text=f"Slots: {encumbrance['used_slots']} / {encumbrance['max_slots']} slots")
            pen = encumbrance['penalties']
            if pen['dex_mod'] != 0 or pen['disadvantage_stealth']:
                st.warning(f"⚠️ **Penalties:** DEX {pen['dex_mod']} | Speed: {pen['speed_pct']}% | Disadvantage on Stealth")
            else:
                st.success("✅ **Unburdened:** Full agility and movement speed.")
            
        with st.expander("⚔️ Equipped Gear", expanded=False):
            gear_dur = player.get("gear_durability", {})
            for slot in ["head", "chest", "main_hand", "off_hand", "accessory"]:
                item = player['equipped'].get(slot, "None")
                dur_info = ""
                if item != "None" and slot in gear_dur:
                    d = gear_dur[slot]
                    dur_info = f" `[{d['cur']}/{d['max']} dur]`"
                st.write(f"- **{slot.replace('_', ' ').title()}:** {item}{dur_info}")
        
        with st.expander("✨ Skills, Spells & Feats", expanded=False):
            # 1. Racial Traits
            if player.get('racial_abilities'):
                st.markdown("#### 🧬 Racial Traits")
                for r in player['racial_abilities']:
                    st.markdown(f"- {r}")
                st.divider()

            # 2. Weapon & Field Skills Mastery (1-1000 System)
            st.markdown("#### ⚔️ Weapon & Field Skills")
            skills = player.get('skills', {})
            if not skills:
                st.caption("No registered skills. Perform actions or combat checks to unlock skills!")
            else:
                TIER_BADGES = {
                    "Novice": ":gray[[Novice]]",
                    "Apprentice": ":green[[Apprentice]]",
                    "Journeyman": ":blue[[Journeyman]]",
                    "Adept": ":violet[[Adept]]",
                    "Master": ":orange[[Master]]",
                    "Grandmaster": ":red[[Grandmaster]]",
                    "Transcendence": ":rainbow[[Transcendence]]"
                }
                THRESHOLDS = [50, 100, 250, 500, 750, 1000]
                THRESHOLD_TIERS = {
                    50: "Apprentice",
                    100: "Journeyman",
                    250: "Adept",
                    500: "Master",
                    750: "Grandmaster",
                    1000: "Transcendence"
                }

                for s_name, s_data in skills.items():
                    if isinstance(s_data, dict):
                        mastery = max(1, min(1000, int(s_data.get('mastery', 1))))
                        tier = s_data.get('tier', 'Novice')
                        desc = s_data.get('description', '')
                        unlocked_milestones = s_data.get('milestones_unlocked', [])
                    else:
                        mastery = 1
                        tier = "Novice"
                        desc = str(s_data)
                        unlocked_milestones = []

                    badge = TIER_BADGES.get(tier, f"[{tier}]")

                    # Find next milestone threshold
                    next_thresh = next((t for t in THRESHOLDS if t > mastery), None)
                    next_tier_name = THRESHOLD_TIERS.get(next_thresh) if next_thresh else None

                    # Header with Tier Badge and exact numerical gauge
                    st.markdown(f"**{s_name}** {badge} `[{mastery} / 1000]`")

                    # Smooth Progress Bar with Next Milestone Text
                    prog_val = min(1.0, max(0.0, mastery / 1000.0))
                    if next_thresh:
                        remaining = next_thresh - mastery
                        prog_text = f"{mastery}/1000 | Next: {next_tier_name} @ {next_thresh} (+{remaining} pts)"
                    else:
                        prog_text = "1000/1000 | 👑 Maximum Mastery Transcended"
                    st.progress(prog_val, text=prog_text)

                    if desc:
                        st.caption(desc)

                    # Render Unlocked Milestone Perks Under Parent Skill
                    if unlocked_milestones:
                        st.markdown("**Unlocked Milestone Perks:**")
                        for perk in unlocked_milestones:
                            if isinstance(perk, dict):
                                p_name = perk.get("name", "Unknown Perk")
                                p_tier = perk.get("tier", "Milestone")
                                p_thresh = perk.get("threshold", "")
                                p_type = perk.get("type", perk.get("perk_type", "Perk"))
                                p_desc = perk.get("description", perk.get("desc", perk.get("effect", "")))
                                header_label = f"[{p_tier} {p_thresh}]" if p_thresh else f"[{p_tier}]"
                                st.markdown(f"  🔹 **{header_label} {p_name}** *({p_type})*")
                                if p_desc:
                                    st.caption(f"  ↳ {p_desc}")
                            else:
                                # String perk name - attempt canonical lookup for rich details
                                perk_str = str(perk)
                                p_dict = None
                                if hasattr(mechanics, "get_canonical_milestone"):
                                    for th_test in THRESHOLDS:
                                        c_p = mechanics.get_canonical_milestone(s_name, th_test)
                                        if c_p and c_p.get("name", "").lower() == perk_str.lower():
                                            p_dict = c_p
                                            break
                                if p_dict:
                                    p_tier = p_dict.get("tier", "Milestone")
                                    p_thresh = p_dict.get("threshold", "")
                                    p_type = p_dict.get("type", "Perk")
                                    p_desc = p_dict.get("effect") or p_dict.get("description", "")
                                    header_label = f"[{p_tier} {p_thresh}]" if p_thresh else f"[{p_tier}]"
                                    st.markdown(f"  🔹 **{header_label} {p_dict['name']}** *({p_type})*")
                                    if p_desc:
                                        st.caption(f"  ↳ {p_desc}")
                                else:
                                    st.markdown(f"  🔹 **[Milestone Perk]** {perk_str}")
                    else:
                        if next_thresh:
                            st.caption(f"🔒 *No milestone perks unlocked yet. Reach {next_thresh} to unlock {next_tier_name} perk.*")

                    # Preview Upcoming Locked Milestone
                    if next_thresh:
                        st.caption(f"🎯 *Target Milestone: [{next_tier_name}] at {next_thresh} Mastery*")

                    st.divider()

            # 3. Active Feats & Techniques
            feats = player.get('feats', [])
            if feats:
                st.markdown("#### 🎖️ Feats & Techniques")
                for f in feats:
                    st.markdown(f"- {f}")
                st.divider()

            # 4. Spells & Arcana
            spells = player.get('spells', [])
            if spells:
                st.markdown("#### 🔮 Spells & Arcana")
                for sp in spells:
                    st.markdown(f"- {sp}")
            
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
    st.subheader("🗺️ Sector 1 Map")
    import map_engine
    map_state = map_engine.load_map_state()
    # Pass consolidated skill and milestone tokens to map engine
    p_skills_dict = st.session_state.player.get("skills", {})
    player_skill_tokens = list(p_skills_dict.keys()) if isinstance(p_skills_dict, dict) else list(p_skills_dict)
    if isinstance(p_skills_dict, dict):
        for s_entry in p_skills_dict.values():
            if isinstance(s_entry, dict):
                for m in s_entry.get("milestones_unlocked", []):
                    if isinstance(m, dict) and "name" in m:
                        player_skill_tokens.append(m["name"])
                    elif isinstance(m, str):
                        player_skill_tokens.append(m)
    player_skill_tokens.extend(st.session_state.player.get("feats", []))
    player_skill_tokens.extend(st.session_state.player.get("spells", []))
    map_path = map_engine.generate_overlay(player_skills=player_skill_tokens)
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

        # --- SKILL MASTERY & MILESTONE TEST BENCH ---
        st.divider()
        st.write("⚔️ **Skill Mastery & Milestone Test Bench**")
        existing_skills = list(st.session_state.player.get("skills", {}).keys())
        skill_opts = ["-- Add New Skill --"] + existing_skills
        chosen_skill_opt = st.selectbox("Select Target Skill", options=skill_opts, key="dev_skill_select")

        target_skill_name = ""
        current_m_val = 1
        if chosen_skill_opt == "-- Add New Skill --":
            target_skill_name = st.text_input(
                "New Skill Name",
                placeholder="e.g. One-Handed Axes, Trench Hammers, Field Trapping, Cartography",
                key="dev_new_skill_name"
            ).strip()
            current_m_val = 1
        else:
            target_skill_name = chosen_skill_opt
            s_obj = st.session_state.player.get("skills", {}).get(target_skill_name, {})
            current_m_val = int(s_obj.get("mastery", 1)) if isinstance(s_obj, dict) else 1

        if target_skill_name:
            state_key = f"dev_mastery_val_{target_skill_name}"
            if state_key not in st.session_state:
                st.session_state[state_key] = current_m_val

            st.write("⚡ **Quick Threshold Jump Buttons:**")
            t_col1, t_col2, t_col3 = st.columns(3)
            jump_target = None
            if t_col1.button("49 (Pre-Apprentice)", key=f"btn_jump_49_{target_skill_name}"): jump_target = 49
            if t_col2.button("50 [Apprentice]", key=f"btn_jump_50_{target_skill_name}"): jump_target = 50
            if t_col3.button("99 (Pre-Journeyman)", key=f"btn_jump_99_{target_skill_name}"): jump_target = 99

            t_col4, t_col5, t_col6 = st.columns(3)
            if t_col4.button("100 [Journeyman]", key=f"btn_jump_100_{target_skill_name}"): jump_target = 100
            if t_col5.button("249 (Pre-Adept)", key=f"btn_jump_249_{target_skill_name}"): jump_target = 249
            if t_col6.button("250 [Adept]", key=f"btn_jump_250_{target_skill_name}"): jump_target = 250

            t_col7, t_col8, t_col9 = st.columns(3)
            if t_col7.button("500 [Master]", key=f"btn_jump_500_{target_skill_name}"): jump_target = 500
            if t_col8.button("750 [Grandmaster]", key=f"btn_jump_750_{target_skill_name}"): jump_target = 750
            if t_col9.button("1000 [Transcendence]", key=f"btn_jump_1000_{target_skill_name}"): jump_target = 1000

            if jump_target is not None:
                st.session_state[state_key] = jump_target
                st.rerun()

            new_m_val = st.number_input(
                f"Set Mastery for '{target_skill_name}' (1-1000)",
                min_value=1,
                max_value=1000,
                value=int(st.session_state[state_key]),
                step=1,
                key=f"dev_num_input_{target_skill_name}"
            )
            st.session_state[state_key] = new_m_val

            # Task DC Progression Simulation
            st.caption("Simulate dynamic progression based on Task DC:")
            sim_dc = st.slider("Simulated Task DC", min_value=5, max_value=30, value=15, key=f"dev_sim_dc_{target_skill_name}")
            if st.button("🎲 Simulate Action Progression", key=f"btn_sim_prog_{target_skill_name}"):
                if hasattr(mechanics, "calculate_mastery_gain"):
                    calc_gain = mechanics.calculate_mastery_gain(new_m_val, sim_dc)
                else:
                    calc_gain = max(1, min(5, (sim_dc // 5)))
                new_calc_val = min(1000, new_m_val + calc_gain)
                st.session_state[state_key] = new_calc_val
                st.toast(f"Simulated DC {sim_dc} action -> +{calc_gain} Mastery (Total: {new_calc_val})!")
                st.rerun()

            if st.button("💾 Apply Skill Override & Save", key=f"btn_apply_skill_{target_skill_name}"):
                if target_skill_name:
                    if target_skill_name not in st.session_state.player.setdefault("skills", {}):
                        st.session_state.player["skills"][target_skill_name] = {
                            "mastery": 1,
                            "tier": "Novice",
                            "description": f"Proficiency with {target_skill_name}.",
                            "milestones_unlocked": []
                        }

                    gain_diff = new_m_val - current_m_val
                    if gain_diff > 0 and hasattr(mechanics, "update_skill_mastery"):
                        mechanics.update_skill_mastery(st.session_state.player, target_skill_name, gain_diff, is_dc=False)
                    else:
                        s_dict = st.session_state.player["skills"][target_skill_name]
                        s_dict["mastery"] = new_m_val
                        if hasattr(mechanics, "get_mastery_tier"):
                            s_dict["tier"] = mechanics.get_mastery_tier(new_m_val)
                        if hasattr(mechanics, "migrate_player_skills"):
                            mechanics.migrate_player_skills(st.session_state.player)

                    save_game(st.session_state.player, st.session_state.messages)
                    st.success(f"Updated '{target_skill_name}' to Mastery {new_m_val}! Saved to database.")
                    time.sleep(0.5)
                    st.rerun()

        st.divider()
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

# --- MAIN UI: THE CHAT WINDOW OR CALIBRATION WIZARD ---
if st.session_state.get("character_creation_mode", False):
    render_character_calibration_wizard()
    st.stop()

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
        
        # 1. Multi-Agent Companion Logic
        companion_intents_str = "None"
        companions = st.session_state.player.get("companions", {})
        if companions:
            with st.spinner("Synchronizing companion sub-routines..."):
                intents = []
                for comp_name, comp_data in companions.items():
                    intent = llm_engine.generate_companion_intent(
                        api_key=api_key,
                        companion_data=comp_data,
                        player_input=ai_prompt,
                        chat_history=st.session_state.messages
                    )
                    intents.append(f"{comp_name}: {intent}")
                    st.info(f"**[{comp_name}]** {intent}")
                companion_intents_str = " | ".join(intents)
                
        with st.spinner("The Cardinal System is generating the world..."):
            
            import map_engine
            current_ms = map_engine.load_map_state()
            
            # 2. Generate Narrative Text
            turn_data = llm_engine.generate_turn(
                api_key=api_key,
                user_input=ai_prompt,
                chat_history=st.session_state.messages,
                player_state=copy.deepcopy(st.session_state.player),
                world_state=world_state,
                map_state=current_ms,
                companion_intents=companion_intents_str
            )
            
            narrative = turn_data.get("narrative", "Error parsing narrative.")
            image_prompt = turn_data.get("image_prompt", "")
            state_updates = turn_data.get("state_updates", {})
            
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
                        # Handle strings like "-426,200" or ints
                        clean_col = str(col_change).replace(",", "").replace(" ", "")
                        st.session_state.player["col"] += int(clean_col)
                    except ValueError:
                        pass
                        
                # Handle Procedural Nodes and Faction Overrides
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
                            
                            # Level up loop
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
                            
                # Handle Skill Mastery updates with Milestone Auto-Unlocker
                skill_updates = state_updates.get("skill_updates") or []
                if isinstance(skill_updates, list):
                    for su in skill_updates:
                        if isinstance(su, dict) and "name" in su:
                            name = su["name"]
                            change = int(su.get("mastery_change", 1))
                            desc = su.get("description", "")
                            task_dc = su.get("task_dc", None)

                            # Use deterministic mechanics engine if available
                            if hasattr(mechanics, "update_skill_mastery"):
                                result = mechanics.update_skill_mastery(
                                    st.session_state.player,
                                    name,
                                    gain_or_dc=change if task_dc is None else int(task_dc),
                                    is_dc=(task_dc is not None),
                                    desc=desc
                                )
                                # Trigger celebratory announcements for newly unlocked milestones
                                new_unlocks = result.get("unlocked_milestones") or result.get("new_unlocks") or []
                                for unlock in new_unlocks:
                                    if isinstance(unlock, dict):
                                        perk_title = unlock.get("name", "Unknown Perk")
                                        perk_tier = unlock.get("tier", "Milestone")
                                    else:
                                        perk_title = str(unlock)
                                        perk_tier = "Milestone"
                                    st.toast(f"🎉 MILESTONE UNLOCKED: {perk_title} ({name} [{perk_tier}])!", icon="👑")
                                    st.balloons()
                            else:
                                # Fallback local update
                                skills_dict = st.session_state.player.setdefault("skills", {})
                                if name in skills_dict:
                                    old_m = skills_dict[name].get("mastery", 1)
                                    new_m = min(1000, old_m + change)
                                    skills_dict[name]["mastery"] = new_m
                                    if desc: skills_dict[name]["description"] = desc
                                else:
                                    skills_dict[name] = {
                                        "mastery": max(1, change),
                                        "tier": "Novice",
                                        "description": desc or f"Proficiency with {name}.",
                                        "milestones_unlocked": []
                                    }
                                
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
                                    
                # Handle Active Quests & Bounties
                for q in state_updates.get("quests_add", []):
                    # To prevent identical dicts from failing simple 'not in' checks, we check titles
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
                            
                # Process Durability Updates
                dur_updates = state_updates.get("durability_updates")
                if dur_updates and isinstance(dur_updates, dict):
                    gear_dur = st.session_state.player.setdefault("gear_durability", {})
                    for target, change in dur_updates.items():
                        target_lower = str(target).lower()
                        matched_slot = None
                        for s, iname in st.session_state.player["equipped"].items():
                            if target_lower in iname.lower() or target_lower == s.lower():
                                matched_slot = s
                                break
                        if matched_slot and matched_slot in gear_dur:
                            if isinstance(change, int) and change < 0:
                                gear_dur[matched_slot]["cur"] = max(0, gear_dur[matched_slot]["cur"] + change)
                            elif isinstance(change, int):
                                gear_dur[matched_slot]["cur"] = min(gear_dur[matched_slot]["max"], change)
                        else:
                            for item in st.session_state.player.get("inventory", []):
                                if isinstance(item, dict) and target_lower in item.get("name", "").lower():
                                    if isinstance(change, int) and change < 0:
                                        item["durability"] = max(0, item.get("durability", 100) + change)
                                    elif isinstance(change, int):
                                        item["durability"] = min(item.get("max_durability", 100), change)
                                    break

            # 1.5 Handle Combat Crunch Logs
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
                
                # Prepend the logs to the narrative so it persists in the chat history
                if log_markdown:
                    narrative = log_markdown + "\n\n" + narrative
            
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
