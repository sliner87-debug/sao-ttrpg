import streamlit as st
import json
import os
import time
import importlib
import base64
import re
import backend.gm_engine as gm_engine
import backend.actor_engine as actor_engine
import backend.mechanics as mechanics
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

# --- SAVE/LOAD & PROFILE LOGIC ---
def load_world():
    if os.path.exists(WORLD_PATH):
        try:
            with open(WORLD_PATH, 'r', encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"sector": 1, "world_status": "CRUCIBLE: ACTIVE", "map_locations": [], "global_news": []}

def get_available_profiles():
    # Discover all character folders in saves/ and auto-migrate legacy files
    manifests = cg.list_all_character_folders(BASE_DIR)
    profiles = [m["name"] for m in manifests if m.get("name")]
    
    # Ensure Banki profile folder is seeded if not present
    if "Banki" not in profiles:
        seed_data = None
        if os.path.exists(SAVE_PATH):
            try:
                with open(SAVE_PATH, 'r', encoding="utf-8") as f:
                    seed_data = json.load(f)
            except Exception:
                pass
        if not seed_data and os.path.exists(os.path.join(BASE_DIR, 'campaign_default_save.json')):
            try:
                with open(os.path.join(BASE_DIR, 'campaign_default_save.json'), 'r', encoding="utf-8") as f:
                    seed_data = json.load(f)
            except Exception:
                pass
        if seed_data and isinstance(seed_data, dict) and "player" in seed_data:
            seed_data["player"]["name"] = "Banki"
            cg.save_character_to_folder(BASE_DIR, seed_data["player"], seed_data.get("messages", []))
            profiles.append("Banki")
    return sorted(list(set(profiles)))

def load_game():
    active_prof = st.session_state.get("active_profile")
    if active_prof:
        char_data = cg.load_character_from_folder(BASE_DIR, active_prof)
        if char_data:
            return char_data
    if os.path.exists(SAVE_PATH):
        try:
            with open(SAVE_PATH, 'r', encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    fallback_path = os.path.join(BASE_DIR, 'campaign_default_save.json')
    if os.path.exists(fallback_path):
        try:
            with open(fallback_path, 'r', encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def save_game(player_state, messages):
    master_state_path = os.path.join(BASE_DIR, ".game_state", "secret_master_state.json")
    master_state = {}
    if os.path.exists(master_state_path):
        try:
            with open(master_state_path, "r", encoding="utf-8") as f:
                master_state = json.load(f)
        except Exception:
            pass

    world_data = st.session_state.get("world_state", load_world())

    extra_meta = {
        "world_state": world_data,
        "master_state": master_state
    }
    save_file = cg.save_character_to_folder(BASE_DIR, player_state, messages, extra_meta=extra_meta)
        
    # Persist world_state.json
    try:
        with open(WORLD_PATH, 'w', encoding="utf-8") as f:
            json.dump(world_data, f, indent=4)
    except Exception:
        pass

    # Rolling chat thread backup
    try:
        backup_path = os.path.join(BASE_DIR, "chat_history_backup.json")
        with open(backup_path, 'w', encoding="utf-8") as f:
            json.dump(messages, f, indent=4)
    except Exception:
        pass
        
    return save_file

# --- CHARACTER GENERATOR & CALIBRATION INTERFACE ---
def render_sidebar_calibration_preview():
    char_name = st.session_state.get("cg_name", "Survivor")
    st.subheader(f"Avatar: {char_name}")
    
    prev_race = cg.RACIAL_LINEAGES.get(st.session_state.get("cg_race_key", "pure_human"), cg.RACIAL_LINEAGES["pure_human"])
    prev_class = cg.CLASS_PATHS.get(st.session_state.get("cg_class_key", "pathless"), cg.CLASS_PATHS["pathless"])
    
    relic_k = st.session_state.get("cg_relic_key", "smartphone")
    if relic_k == "custom" and st.session_state.get("cg_custom_relic_data"):
        prev_relic = st.session_state.cg_custom_relic_data
    else:
        prev_relic = cg.PERSONAL_RELICS.get(relic_k, cg.PERSONAL_RELICS["smartphone"])
    
    pt_alloc = st.session_state.get("cg_points", {"STR": 0, "DEX": 0, "CON": 0, "INT": 0, "WIS": 0, "CHA": 0})
    prev_stats = {
        s: 10 + pt_alloc.get(s, 0) + prev_race["stat_mods"].get(s, 0)
        for s in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
    }
    con_m = (prev_stats["CON"] - 10) // 2
    base_hp_val = prev_class.get("base_hp", 100)
    prev_hp = base_hp_val + (con_m * 10)
    
    class_def_w = cg.CLASS_WEAPONS.get(st.session_state.get("cg_class_key", "pathless"), cg.CLASS_WEAPONS["pathless"])
    main_w = st.session_state.get("cg_main_hand", class_def_w["main_hand"]) if st.session_state.get("cg_custom_weapons", False) else class_def_w["main_hand"]
    off_w = st.session_state.get("cg_off_hand", class_def_w["off_hand"]) if st.session_state.get("cg_custom_weapons", False) else class_def_w["off_hand"]
    
    mock_p = {
        "name": char_name,
        "level": 1,
        "hp": prev_hp,
        "max_hp": prev_hp,
        "col": 100,
        "class": prev_class["title"],
        "stats": prev_stats,
        "equipped": {
            "head": "None", 
            "chest": "Threadbare Scavenger Tunic", 
            "main_hand": main_w, 
            "off_hand": off_w, 
            "accessory": prev_relic["name"] if any(k in prev_relic["name"] for k in ["Watch", "Tool", "Headphones", "Compass", "USB", "Rangefinder"]) else "None"
        },
        "inventory": [prev_relic, {"name": main_w, "qty": 1}, {"name": "Bottled Water", "qty": 2}, {"name": "Survival Rations", "qty": 2}]
    }
    if off_w and off_w != "None":
        mock_p["inventory"].append({"name": off_w, "qty": 1})
        
    mock_enc = mechanics.calculate_encumbrance(mock_p) if hasattr(mechanics, "calculate_encumbrance") else {"label": "Unencumbered", "current_weight_lbs": 10, "max_weight_lbs": 150, "weight_percent": 0.1, "used_slots": 5, "max_slots": 20, "slots_percent": 0.25}
    mock_ac = mechanics.calculate_ac(mock_p, mock_enc) if hasattr(mechanics, "calculate_ac") else 10
    
    st.progress(1.0, text=f"HP: {prev_hp} / {prev_hp}")
    st.progress(0.0, text="XP: 0 / 1000")
    if hasattr(mechanics, "get_combat_resource_display"):
        mock_res = mechanics.get_combat_resource_display(mock_p)
        st.progress(mock_res["percentage"], text=f"⚡ {mock_res['name']}: {mock_res['display']}")
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
        st.write(f"**Status:** {mock_enc.get('label', 'Unencumbered')}")
        st.progress(mock_enc.get('weight_percent', 0.1), text=f"Weight: {mock_enc.get('current_weight_lbs', 10)} / {mock_enc.get('max_weight_lbs', 150)} lbs")
        st.progress(mock_enc.get('slots_percent', 0.2), text=f"Slots: {mock_enc.get('used_slots', 4)} / {mock_enc.get('max_slots', 20)} slots")
        
    with st.expander("✨ Starting Skills & Feats Preview", expanded=False):
        bg_key = st.session_state.get("cg_bg_key", "software_engineer")
        if bg_key == "custom":
            if st.session_state.get("cg_custom_collaborated"):
                c_data = st.session_state.cg_custom_collaborated
                bg_data = {
                    "skills": {
                        c_data["skill_1"]["name"]: {"mastery": c_data["skill_1"]["mastery"], "tier": "Apprentice" if c_data["skill_1"]["mastery"] >= 50 else "Novice"},
                        c_data["skill_2"]["name"]: {"mastery": c_data["skill_2"]["mastery"], "tier": "Apprentice" if c_data["skill_2"]["mastery"] >= 50 else "Novice"}
                    },
                    "innate_perk": c_data.get("innate_perk", "")
                }
            elif st.session_state.get("cg_custom_bg_text"):
                bg_data = cg.parse_custom_background(st.session_state.get("cg_custom_bg_text"))
            else:
                bg_data = cg.PRESET_BACKGROUNDS["software_engineer"]
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
    if "cg_custom_notes" not in st.session_state:
        st.session_state.cg_custom_notes = ""
    if "cg_custom_collaborated" not in st.session_state:
        st.session_state.cg_custom_collaborated = None
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
    if "cg_custom_relic_data" not in st.session_state:
        st.session_state.cg_custom_relic_data = None

    # Header & Cancel Bar
    top_c1, top_c2 = st.columns([4, 1])
    with top_c1:
        st.title("🧬 Cardinal System Calibration Protocol (V2)")
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

        # Quick-Lifestyle Questionnaire Presets (18 Archetypes)
        with st.expander("⚡ 18 Quick-Lifestyle Questionnaire Presets (Auto-Distribute 20 Points)", expanded=False):
            st.caption("Select any Pre-Integration Earth archetype to instantly auto-distribute your 20 calibration points:")
            preset_keys = list(cg.PRESET_LIFESTYLES.keys())
            sel_p_key = st.selectbox(
                "Browse Lifestyle Archetype:",
                options=preset_keys,
                format_func=lambda k: cg.PRESET_LIFESTYLES[k]["title"],
                key="sel_lifestyle_preset"
            )
            p_data = cg.PRESET_LIFESTYLES[sel_p_key]
            st.info(f"**Archetype Summary:** {p_data['desc']}")
            p_pts = p_data["points"]
            st.caption(f"**Point Allocation:** STR +{p_pts['STR']} | DEX +{p_pts['DEX']} | CON +{p_pts['CON']} | INT +{p_pts['INT']} | WIS +{p_pts['WIS']} | CHA +{p_pts['CHA']}")
            if st.button("⚡ Apply Selected Lifestyle Preset (20 Points)", use_container_width=True, key="btn_apply_preset_main"):
                st.session_state.cg_points = dict(p_pts)
                st.rerun()

            st.markdown("---")
            st.caption("Or One-Click Popular Archetypes:")
            q_cols1 = st.columns(4)
            if q_cols1[0].button("🛋️ Desk Bound", use_container_width=True, key="preset_desk"):
                st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["desk_bound"]["points"])
                st.rerun()
            if q_cols1[1].button("🏃 Athletic", use_container_width=True, key="preset_athletic"):
                st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["athletic"]["points"])
                st.rerun()
            if q_cols1[2].button("🔨 Heavy Labor", use_container_width=True, key="preset_labor"):
                st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["heavy_labor"]["points"])
                st.rerun()
            if q_cols1[3].button("🎖️ First Responder", use_container_width=True, key="preset_responder"):
                st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["first_responder"]["points"])
                st.rerun()
                
            q_cols2 = st.columns(4)
            if q_cols2[0].button("📚 Academic Scholar", use_container_width=True, key="preset_scholar"):
                st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["academic_scholar"]["points"])
                st.rerun()
            if q_cols2[1].button("🧘 Yoga Contortionist", use_container_width=True, key="preset_yoga"):
                st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["yoga_contortionist"]["points"])
                st.rerun()
            if q_cols2[2].button("🎮 Esports Gamer", use_container_width=True, key="preset_esports"):
                st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["esports_gamer"]["points"])
                st.rerun()
            if q_cols2[3].button("🌲 Homesteader", use_container_width=True, key="preset_homesteader"):
                st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["offgrid_homesteader"]["points"])
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
            ["Preset Earth Vocations (20 Archetypes)", "✍️ Custom Earth Life (Interactive Collaboration with Cardinal)"],
            horizontal=True,
            key="vocation_mode_radio"
        )
        
        if v_mode.startswith("Preset"):
            bg_keys = list(cg.PRESET_BACKGROUNDS.keys())
            bg_titles = [cg.PRESET_BACKGROUNDS[k]["title"] for k in bg_keys]
            
            cur_bg_idx = bg_keys.index(st.session_state.cg_bg_key) if st.session_state.cg_bg_key in bg_keys else 0
            sel_bg_title = st.selectbox(
                "Choose Earth Profession (20 Options):",
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
            st.markdown("##### ✍️ Custom Earth Life Description & Collaboration:")
            st.caption("Describe your pre-collapse profession, trade, or daily hobbies. You and the Cardinal System will collaborate to synthesize the appropriate starting skills.")
            
            st.session_state.cg_custom_bg_text = st.text_area(
                "Your Pre-Integration Story / Career:",
                value=st.session_state.get("cg_custom_bg_text", ""),
                placeholder="e.g. I worked as an industrial high-voltage electrician, played rugby on weekends, and spent time restoring vintage motorcycles...",
                height=110,
                key="custom_bg_input_area"
            )
            
            col_notes = st.text_input(
                "Optional Collaboration Focus / Notes (e.g. 'Emphasize high shock resistance and hand-to-hand brawling'):",
                value=st.session_state.get("cg_custom_notes", ""),
                key="custom_notes_input"
            )
            st.session_state.cg_custom_notes = col_notes
            
            c_btn1, c_btn2 = st.columns([2, 1])
            if c_btn1.button("🤖 Consult Cardinal System on Custom Profile", use_container_width=True, key="btn_consult_cardinal"):
                with st.spinner("Cardinal System scanning pre-integration neural engrams..."):
                    collab_result = cg.consult_custom_background(
                        st.session_state.cg_custom_bg_text,
                        api_key=api_key,
                        follow_up_notes=col_notes
                    )
                    st.session_state.cg_custom_collaborated = collab_result
                    st.success("Cardinal System consultation complete!")

            if st.session_state.get("cg_custom_collaborated"):
                res = st.session_state.cg_custom_collaborated
                st.info(f"👾 **Cardinal Evaluation:** {res.get('evaluation_message', '')}")
                
                st.markdown("##### 🤝 Collaborative Refinement (Edit Your Starting Skills):")
                ref_col1, ref_col2 = st.columns(2)
                with ref_col1:
                    st.markdown("**Primary Vocation Skill**")
                    s1_name = st.text_input("Skill 1 Name:", value=res["skill_1"]["name"], key="c_s1_name")
                    s1_mst = st.slider("Skill 1 Mastery (1-1000):", min_value=30, max_value=65, value=res["skill_1"]["mastery"], key="c_s1_mst")
                    s1_desc = st.text_input("Skill 1 Description:", value=res["skill_1"]["description"], key="c_s1_desc")
                with ref_col2:
                    st.markdown("**Secondary Trait Skill**")
                    s2_name = st.text_input("Skill 2 Name:", value=res["skill_2"]["name"], key="c_s2_name")
                    s2_mst = st.slider("Skill 2 Mastery (1-1000):", min_value=25, max_value=55, value=res["skill_2"]["mastery"], key="c_s2_mst")
                    s2_desc = st.text_input("Skill 2 Description:", value=res["skill_2"]["description"], key="c_s2_desc")
                    
                perk_val = st.text_input("Innate Passive Perk:", value=res.get("innate_perk", ""), key="c_perk_val")
                
                # Keep active data synced
                st.session_state.cg_custom_collaborated["skill_1"] = {"name": s1_name, "mastery": s1_mst, "description": s1_desc}
                st.session_state.cg_custom_collaborated["skill_2"] = {"name": s2_name, "mastery": s2_mst, "description": s2_desc}
                st.session_state.cg_custom_collaborated["innate_perk"] = perk_val
            else:
                # Heuristic fallback preview
                parsed = cg.parse_custom_background(st.session_state.cg_custom_bg_text)
                st.caption("*(Click 'Consult Cardinal System' above to interactively collaborate on custom skill names and tiers)*")
                st.markdown(f"##### 🧬 Procedural Baseline Analysis: *{parsed['title']}*")
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
        st.write("When the Aetheric Rift collapsed into Earth, ambient leylines permeated human biology. Survivors either resisted mutation or adapted into new physical lineages pulling from high-fantasy and sci-fi phenotypes.")
        
        race_keys = list(cg.RACIAL_LINEAGES.keys())
        race_display_labels = [f"[{cg.RACIAL_LINEAGES[k].get('genre', 'Universal')}] {cg.RACIAL_LINEAGES[k]['name']}" for k in race_keys]
        cur_r_idx = race_keys.index(st.session_state.cg_race_key) if st.session_state.cg_race_key in race_keys else 0
        
        sel_race_label = st.selectbox(
            "Select Lineage / Mutation (20 Options):",
            options=race_display_labels,
            index=cur_r_idx,
            key="sel_race_box"
        )
        selected_race_key = race_keys[race_display_labels.index(sel_race_label)]
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
        
        canonical_keys = ["warrior", "mage", "cleric", "thief", "ranger", "engineer", "psion", "pathless"]
        class_keys = [k for k in canonical_keys if k in cg.CLASS_PATHS]
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
        
        # Display Core Stats & Scaling
        c_meta1, c_meta2, c_meta3 = st.columns(3)
        c_meta1.metric("Base HP", f"{class_obj.get('base_hp', 100)} HP", f"+{class_obj.get('hp_per_lvl', 25)}/lvl")
        c_meta2.metric("Combat Resource", class_obj.get("combat_resource", {}).get("name", "Stamina"))
        c_meta3.metric("Native Armor", ", ".join(class_obj.get("native_armor", ["Cloth"])))

        st.caption(f"**Favored Skill Affinities (+25% Mastery XP):** {', '.join(class_obj.get('favored_skills', []))}")
        
        st.markdown("##### 🎖️ Fixed Iconic Duo (Level 1 Baseline Feats):")
        for cf in class_obj["starting_feats"]:
            st.success(f"🔹 **{cf}**")
            
        def_w = cg.CLASS_WEAPONS.get(selected_class_key, cg.CLASS_WEAPONS["pathless"])
        st.caption(f"Default Combat Loadout: **{def_w['main_hand']}** (Main) & **{def_w['off_hand']}** (Off) - *{def_w['desc']}*")

    # --- TAB 5: RELIC & GEAR ---
    with tab5:
        st.markdown("### 🎒 Stage 5: Earth Relic, Starting Gear & Link Start")
        st.write("Every survivor carries a personal relic from old Earth, alongside scavenged survival supplies.")
        
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
        # Personal Relic Selection (17 Presets or Custom Write-In)
        st.markdown("#### 📱 Pre-Integration Earth Relic")
        relic_mode = st.radio(
            "Relic Selection Mode:",
            ["Choose from 17 Pre-Integration Earth Relics", "✍️ Custom Personal Keepsake (Write-In Object)"],
            horizontal=True,
            key="relic_mode_radio"
        )
        
        if relic_mode.startswith("Choose"):
            relic_keys = list(cg.PERSONAL_RELICS.keys())
            relic_names = [cg.PERSONAL_RELICS[k]["name"] for k in relic_keys]
            cur_relic_idx = relic_keys.index(st.session_state.cg_relic_key) if st.session_state.cg_relic_key in relic_keys else 0
            
            sel_relic_name = st.selectbox(
                "Choose Personal Relic (17 Options):",
                options=relic_names,
                index=cur_relic_idx,
                key="sel_relic_box"
            )
            selected_relic_key = relic_keys[relic_names.index(sel_relic_name)]
            st.session_state.cg_relic_key = selected_relic_key
            st.session_state.cg_custom_relic_data = None
            relic_obj = cg.PERSONAL_RELICS[selected_relic_key]
            
            st.success(f"✨ **{relic_obj['name']}** [{relic_obj['rarity']}]")
            st.caption(f"{relic_obj['desc']}")
        else:
            st.session_state.cg_relic_key = "custom"
            st.markdown("##### ✍️ Custom Personal Relic Write-In:")
            r_name = st.text_input(
                "Keepsake Name:",
                value=st.session_state.get("cg_custom_relic_name", "Grandpa's Pocket Bible"),
                key="in_custom_relic_name"
            )
            r_desc = st.text_area(
                "Nostalgic Memory / Visual Details:",
                value=st.session_state.get("cg_custom_relic_desc", "A dog-eared leather-bound pocket book with yellowed pages and handwritten family notes."),
                height=70,
                key="in_custom_relic_desc"
            )
            r_ability = st.text_input(
                "Thematic Survival Effect / Passive Aura:",
                value=st.session_state.get("cg_custom_relic_ability", "Grants +2 on saving throws against psychic despair, fear, and cosmic panic."),
                key="in_custom_relic_ability"
            )
            st.session_state.cg_custom_relic_name = r_name
            st.session_state.cg_custom_relic_desc = r_desc
            st.session_state.cg_custom_relic_ability = r_ability
            custom_obj = cg.create_custom_relic(r_name, r_desc, r_ability)
            st.session_state.cg_custom_relic_data = custom_obj
            relic_obj = custom_obj
            st.success(f"✨ Custom Relic: **{custom_obj['name']}** [Custom Relic] — {custom_obj['desc']}")
            
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
        calc_hp = c_info.get("base_hp", 100) + ((final_scores["CON"] - 10) // 2) * 10
        
        st.markdown("### 📋 Final Calibration Review")
        rev_c1, rev_c2, rev_c3 = st.columns(3)
        rev_c1.metric("Callsign", st.session_state.cg_name)
        rev_c1.metric("Lineage", r_info["name"])
        rev_c2.metric("Doctrine", c_info["title"])
        rev_c2.metric("Starting HP", f"{calc_hp} HP")
        rev_c3.metric("Main Weapon", st.session_state.cg_main_hand)
        rev_c3.metric("Personal Relic", relic_obj["name"][:22] + "...")
        
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
                    starting_weapons={"main_hand": st.session_state.cg_main_hand, "off_hand": st.session_state.cg_off_hand},
                    custom_relic_data=st.session_state.get("cg_custom_relic_data"),
                    custom_collaborated_data=st.session_state.get("cg_custom_collaborated")
                )
                
                opening_announcement = (
                    f"### SYSTEM ANNOUNCEMENT (V2 CRUCIBLE)\n\n"
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
                
                # Sync V2 master state on disk
                m_path = os.path.join(BASE_DIR, ".game_state", "secret_master_state.json")
                if os.path.exists(m_path):
                    try:
                        with open(m_path, 'r', encoding="utf-8") as mf:
                            m_state = json.load(mf)
                        m_state["player"] = dict(new_avatar)
                        with open(m_path, 'w', encoding="utf-8") as mf:
                            json.dump(m_state, mf, indent=4)
                    except Exception:
                        pass
                        
                save_game(st.session_state.player, st.session_state.messages)
                st.balloons()
                st.success(f"Calibration Complete! Avatar **{char_name}** linked to the Cardinal System. Saved to saves/{char_name}/. Entering Sector 1 Safe-Zone...")
                time.sleep(1.0)
                st.rerun()

def extract_turn_components(msg: dict) -> tuple:
    """
    Returns (cleaned_narrative, mechanics_log, subagent_log) from a message dictionary.
    Handles:
    1. Newly structured messages with explicit 'mechanics_log' and 'subagent_log'.
    2. Legacy messages with embedded SubAgent monologues.
    3. Legacy messages with bracketed dice rolls / DC checks / damage math or prepended > 🎲 rolls.
    """
    content = msg.get("content", "") or ""
    mechanics_log = msg.get("mechanics_log", "") or ""
    subagent_log = msg.get("subagent_log", "") or ""
    
    # 1. Extract SubAgent thoughts if not already isolated
    if not subagent_log and content:
        match = re.search(r'(?:\r?\n)+(?:\*\*\[.*?SubAgent Mind\]\*\*|\*\*\[Ren\'s Tactical Logic\]\*\*)', content)
        if match:
            split_idx = match.start()
            subagent_log = content[split_idx:].strip()
            content = content[:split_idx].strip()

    # 2. Extract Dice Rolls / Mechanics if not already isolated
    if not mechanics_log and content:
        mechanics_items = []
        
        # Check for prepended blockquote rolls like: > 🎲 `...`
        clean_lines = []
        for line in content.split("\n"):
            line_str = line.strip()
            if line_str.startswith("> 🎲") or (line_str.startswith(">") and "🎲" in line_str):
                cleaned = line_str.replace("> 🎲", "").replace(">", "").strip(" `*")
                if cleaned:
                    mechanics_items.append(f"* 🎲 `{cleaned}`")
            elif line_str == ">":
                continue
            else:
                clean_lines.append(line)
        content = "\n".join(clean_lines).strip()
        
        # Check for bracketed rolls/checks: [Attack: 1d20+5 = 17 vs AC 14 | Hit!]
        bracket_pattern = re.compile(r'\s*\[([^\]]*(?:d20|d4|d6|d8|d10|d12|\bAC\b|\bDC\b|\bHit\b|\bFail\b|\bSave\b|\bRoll\b|\bdamage\b)[^\]]*)\]', re.IGNORECASE)
        found_brackets = bracket_pattern.findall(content)
        if found_brackets:
            content = bracket_pattern.sub('', content).strip()
            for b in found_brackets:
                clean_b = b.strip()
                if clean_b:
                    mechanics_items.append(f"* 🎲 `{clean_b}`")
                    
        if mechanics_items:
            mechanics_log = "\n".join(mechanics_items)
            
    return content, mechanics_log, subagent_log

def extract_subagent_log(msg: dict) -> tuple:
    c, m, s = extract_turn_components(msg)
    return c, s

def get_strain_capacity(player_state: dict) -> int:
    con = player_state.get("stats", {}).get("CON", 10)
    con_mod = (con - 10) // 2
    level = player_state.get("level", 1)
    return max(1, con_mod + (level // 2))

def get_current_strain(player_state: dict) -> int:
    grafts = player_state.get("grafts", {})
    strain = 0
    if isinstance(grafts, dict):
        for slot, item in grafts.items():
            if item and isinstance(item, dict):
                strain += item.get("strain", 1)
            elif item and isinstance(item, str):
                strain += 1
    return strain

def get_mastery_tier_info(mastery: int) -> tuple:
    """Returns (tier_name, next_threshold)"""
    if mastery < 50:
        return "Novice", 50
    elif mastery < 100:
        return "Apprentice", 100
    elif mastery < 250:
        return "Journeyman", 250
    elif mastery < 500:
        return "Adept", 500
    elif mastery < 750:
        return "Master", 750
    elif mastery < 1000:
        return "Grandmaster", 1000
    else:
        return "Transcendence", 1000

def apply_player_state_updates(state_updates):
    if not state_updates or not isinstance(state_updates, dict):
        return
        
    hp_change = state_updates.get("hp_change")
    if hp_change:
        try:
            clean_hp = int(str(hp_change).replace(",", "").replace(" ", ""))
            st.session_state.player["hp"] = max(0, min(st.session_state.player["max_hp"], st.session_state.player["hp"] + clean_hp))
        except (ValueError, TypeError):
            pass
            
    col_change = state_updates.get("col_change")
    if col_change:
        try:
            clean_col = int(str(col_change).replace(",", "").replace(" ", ""))
            st.session_state.player["col"] = max(0, st.session_state.player["col"] + clean_col)
            if clean_col != 0:
                st.toast(f"{'+' if clean_col > 0 else ''}{clean_col} Col!", icon="💰")
        except (ValueError, TypeError):
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
        except (ValueError, TypeError):
            pass
    
    inv_add = state_updates.get("inventory_add") or []
    if isinstance(inv_add, list):
        for item in inv_add:
            if isinstance(item, dict) and "name" in item:
                st.session_state.player["inventory"].append(item)
                st.toast(f"📦 Acquired: {item['name']}!", icon="🎁")
            elif isinstance(item, str) and item.strip():
                st.session_state.player["inventory"].append({"name": item, "rarity": "Common", "durability": 100, "max_durability": 100, "qty": 1, "desc": ""})
                st.toast(f"📦 Acquired: {item}!", icon="🎁")
                
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

    for k in ["spells_add", "feats_add", "racial_abilities_add"]:
        adds = state_updates.get(k) or []
        if isinstance(adds, list):
            target_list = k.replace("_add", "")
            for a in adds:
                if a not in st.session_state.player.get(target_list, []):
                    st.session_state.player.setdefault(target_list, []).append(a)
                    st.toast(f"🔮 Learned {target_list[:-1].capitalize()}: {a}!")

    grafts_installed = state_updates.get("grafts_installed") or []
    if isinstance(grafts_installed, list):
        if "grafts" not in st.session_state.player:
            st.session_state.player["grafts"] = {}
        for g in grafts_installed:
            if isinstance(g, dict) and "slot" in g:
                slot = g["slot"].lower().replace(" ", "_")
                st.session_state.player["grafts"][slot] = g
                st.toast(f"🦾 Installed Graft ({slot.capitalize()}): {g.get('name', 'Graft')}!", icon="💉")

    grafts_update = state_updates.get("grafts_update")
    if grafts_update and isinstance(grafts_update, dict):
        if "grafts" not in st.session_state.player:
            st.session_state.player["grafts"] = {}
        for slot, g_data in grafts_update.items():
            st.session_state.player["grafts"][slot] = g_data
            g_name = g_data.get("name", str(g_data)) if isinstance(g_data, dict) else str(g_data)
            st.toast(f"🦾 Installed Graft ({slot.capitalize()}): {g_name}!", icon="💉")

    skill_updates = state_updates.get("skill_updates") or []
    if isinstance(skill_updates, list):
        for su in skill_updates:
            if isinstance(su, dict) and "name" in su:
                name = su["name"]
                change = int(su.get("mastery_change", 1))
                desc = su.get("description", "")
                if name in st.session_state.player.get("skills", {}):
                    old_m = st.session_state.player["skills"][name].get("mastery", 1)
                    new_m = min(1000, old_m + change)
                    st.session_state.player["skills"][name]["mastery"] = new_m
                    if desc:
                        st.session_state.player["skills"][name]["description"] = desc
                    st.toast(f"📈 {name} Mastery: {old_m} ➔ {new_m} (+{change})", icon="⚡")
                else:
                    st.session_state.player.setdefault("skills", {})[name] = {"mastery": max(1, change), "description": desc}
                    st.toast(f"✨ Unlocked New Skill: {name} (Mastery: {change})", icon="🌟")

    w_change = state_updates.get("weather_change")
    if w_change and hasattr(mechanics, "set_weather"):
        mechanics.set_weather(st.session_state.player, w_change)
        st.toast(f"🌪️ Weather shifted: {w_change}!", icon="🌤️")

    mins_adv = state_updates.get("time_minutes_advanced")
    if mins_adv and hasattr(mechanics, "advance_game_time"):
        try:
            m_val = int(mins_adv)
            if m_val > 0:
                t_res = mechanics.advance_game_time(st.session_state.player, minutes=m_val)
                st.toast(f"⏱️ Time advanced by {m_val}m ({t_res.get('time_str', '')})", icon="⏳")
        except (ValueError, TypeError):
            pass

    bb_dmg = state_updates.get("boss_break_gauge_damage")
    if bb_dmg and hasattr(mechanics, "damage_overlord_break_gauge"):
        try:
            b_val = int(bb_dmg)
            if b_val > 0:
                bg_res = mechanics.damage_overlord_break_gauge(st.session_state.player, b_val)
                st.toast(bg_res.get("log", f"Boss Break Gauge -{b_val}"), icon="💥")
        except (ValueError, TypeError):
            pass


def apply_companion_state_updates(hp_changes: dict):
    """Synchronizes companion damage/healing across session state and Party/*.json sheets."""
    if not hp_changes or not isinstance(hp_changes, dict):
        return
        
    companion_id_map = {
        "companion_ren": "Ren", "Ren": "Ren", "ren": "Ren",
        "companion_elora": "Elora", "Elora": "Elora", "elora": "Elora",
        "companion_torvald": "Torvald", "Torvald": "Torvald", "torvald": "Torvald",
        "companion_kibs": "Kibs", "Kibs": "Kibs", "kibs": "Kibs"
    }
    
    for c_key, delta in hp_changes.items():
        if c_key in companion_id_map:
            c_name = companion_id_map[c_key]
            # 1. Update session state player["companions"][c_name]
            if "companions" in st.session_state.player and c_name in st.session_state.player["companions"]:
                c_ref = st.session_state.player["companions"][c_name]
                old_hp = c_ref.get("hp", 35)
                max_hp = c_ref.get("max_hp", 35)
                new_hp = max(0, min(max_hp, old_hp + delta))
                c_ref["hp"] = new_hp
                if delta < 0:
                    st.toast(f"🩸 {c_name} took {abs(delta)} damage! (HP: {new_hp}/{max_hp})", icon="🛡️")
                elif delta > 0:
                    st.toast(f"💚 {c_name} recovered {delta} HP! (HP: {new_hp}/{max_hp})", icon="🩹")
                    
            # 2. Update Party/companion_*.json on disk
            party_file = os.path.join(BASE_DIR, "Party", f"companion_{c_name.lower()}.json")
            if os.path.exists(party_file):
                try:
                    with open(party_file, "r", encoding="utf-8") as f:
                        p_sheet = json.load(f)
                    p_max = p_sheet.get("max_hp", 35)
                    p_sheet["hp"] = max(0, min(p_max, p_sheet.get("hp", 35) + delta))
                    with open(party_file, "w", encoding="utf-8") as f:
                        json.dump(p_sheet, f, indent=4)
                except Exception as e:
                    print(f"[COMPANION SYNC ERROR] {e}", flush=True)

# --- INITIALIZE SESSION STATE ---
saved_data = load_game()

if "offline_processed" not in st.session_state:
    st.session_state.offline_processed = True

if "world_state" not in st.session_state:
    if saved_data and "world_state" in saved_data:
        st.session_state.world_state = saved_data["world_state"]
    else:
        st.session_state.world_state = load_world()

world_state = st.session_state.world_state

if "player" not in st.session_state:
    if saved_data:
        st.session_state.player = saved_data["player"]
        # Restore master state onto disk if saved
        if "master_state" in saved_data and saved_data["master_state"]:
            m_path = os.path.join(BASE_DIR, ".game_state", "secret_master_state.json")
            try:
                os.makedirs(os.path.dirname(m_path), exist_ok=True)
                with open(m_path, "w", encoding="utf-8") as f:
                    json.dump(saved_data["master_state"], f, indent=4)
            except Exception:
                pass
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
p.setdefault("grafts", {"head": None, "torso": None, "left_arm": None, "right_arm": None, "legs": None, "spine": None})

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
        "archetype": "MageTech Vanguard (Trapped 17yo Game Tester)",
        "role": "MageTech Vanguard (Trapped 17yo Game Tester)",
        "hp": 35,
        "max_hp": 35,
        "ac": 16,
        "status": "Vigilant and operational",
        "active_grafts": [
            {"name": "Aetheric Ocular Lens", "slot": "Head", "effect": "Darkvision, reveals arcane matrices & traps"}
        ],
        "inventory": ["Aether-Lock Carbine", "Runic Vanguard Blade", "Alchemical Haze Pellets"]
    }
})

# Synchronize existing session/saved Ren data with canonical MageTech Vanguard sheet
if "companions" in p and "Ren" in p["companions"]:
    r_sheet = p["companions"]["Ren"]
    if "MageTech" not in str(r_sheet.get("archetype", "")) or r_sheet.get("max_hp") != 35:
        r_sheet["archetype"] = "MageTech Vanguard (Trapped 17yo Game Tester)"
        r_sheet["role"] = "MageTech Vanguard (Trapped 17yo Game Tester)"
        r_sheet["max_hp"] = 35
        r_sheet["hp"] = min(35, r_sheet.get("hp", 35))
        r_sheet["ac"] = 16
        r_sheet["status"] = "Vigilant and operational"
        r_sheet["active_grafts"] = [
            {"name": "Aetheric Ocular Lens", "slot": "Head", "effect": "Darkvision, reveals arcane matrices & traps"}
        ]
        r_sheet["inventory"] = ["Aether-Lock Carbine", "Runic Vanguard Blade", "Alchemical Haze Pellets"]

# Initialize Phase 1-9 Systems
if hasattr(mechanics, "ensure_chrono_system"):
    mechanics.ensure_chrono_system(p)
if hasattr(mechanics, "ensure_factions_system"):
    mechanics.ensure_factions_system(p)
if hasattr(mechanics, "ensure_homestead_system"):
    mechanics.ensure_homestead_system(p)
if hasattr(mechanics, "ensure_graft_system"):
    mechanics.ensure_graft_system(p)
if hasattr(mechanics, "ensure_party_system"):
    mechanics.ensure_party_system(p)
if hasattr(mechanics, "ensure_ability_matrix"):
    mechanics.ensure_ability_matrix(p)

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
def render_game_hud():
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
        cursor_data = mechanics.get_cursor_status(player) if hasattr(mechanics, "get_cursor_status") else {"badge": "🟢 Green"}
        st.write(f"**Race:** {player['race']}")
        st.write(f"**Class:** {player['class']}")
        st.write(f"**SAO Status:** {cursor_data.get('badge', '🟢 Green')}")
        st.write("**Core Stats:**")
        cols = st.columns(3)
        cols[0].write(f"STR: {player['stats']['STR']}")
        cols[1].write(f"DEX: {player['stats']['DEX']}")
        cols[2].write(f"CON: {player['stats']['CON']}")
        cols = st.columns(3)
        cols[0].write(f"INT: {player['stats']['INT']}")
        cols[1].write(f"WIS: {player['stats']['WIS']}")
        cols[2].write(f"CHA: {player['stats']['CHA']}")

    encumbrance = mechanics.calculate_encumbrance(player) if hasattr(mechanics, "calculate_encumbrance") else {"label": "Unburdened", "current_weight_lbs": 10, "max_weight_lbs": 150, "weight_percent": 0.1, "used_slots": 5, "max_slots": 20, "slots_percent": 0.25, "penalties": {"dex_mod": 0, "speed_pct": 100, "disadvantage_stealth": False}}
    with st.expander("⚖️ Encumbrance & Carry Physics", expanded=False):
        st.write(f"**Status:** {encumbrance['label']}")
        st.progress(encumbrance['weight_percent'], text=f"Weight: {encumbrance['current_weight_lbs']} / {encumbrance['max_weight_lbs']} lbs")
        st.progress(encumbrance['slots_percent'], text=f"Slots: {encumbrance['used_slots']} / {encumbrance['max_slots']} slots")
        pen = encumbrance['penalties']
        if pen['dex_mod'] != 0 or pen['disadvantage_stealth']:
            st.warning(f"⚠️ **Penalties:** DEX {pen['dex_mod']} | Speed: {pen['speed_pct']}% | Disadvantage on Stealth")
        else:
            st.success("✅ **Unburdened:** Full agility and movement speed.")

    with st.expander("⚔️ Equipped Gear & Durability", expanded=False):
        gear_dur = mechanics.normalize_gear_durability(player) if hasattr(mechanics, "normalize_gear_durability") else {}
        pens = mechanics.calculate_durability_penalties(player) if hasattr(mechanics, "calculate_durability_penalties") else {"atk_penalty": 0, "ac_penalty": 0, "broken_items": []}
        if pens["atk_penalty"] > 0 or pens["ac_penalty"] > 0:
            st.warning(f"⚠️ **Wear Penalties Active:** ATK -{pens['atk_penalty']} | AC -{pens['ac_penalty']}")
        if pens["broken_items"]:
            st.error(f"🚨 **Broken Gear:** {', '.join(pens['broken_items'])} (Ineffective!)")

        for slot in ["head", "chest", "main_hand", "off_hand", "accessory"]:
            item = player['equipped'].get(slot, "None")
            slot_label = slot.replace('_', ' ').title()
            if item and item != "None":
                grade = mechanics.get_item_grade(item) if hasattr(mechanics, "get_item_grade") else 1
                grade_badge = f"Grade {grade}"
                d = gear_dur.get(slot, {"cur": 100, "max": 100})
                cur_d = d.get("cur", 100)
                max_d = d.get("max", 100)
                state_info = mechanics.get_durability_state(cur_d, max_d) if hasattr(mechanics, "get_durability_state") else {"label": f"{cur_d}/{max_d}", "pct": cur_d / max_d if max_d > 0 else 1.0, "is_broken": cur_d <= 0, "is_dulled": cur_d < max_d * 0.25}
                st.markdown(f"**{slot_label}:** {item}")
                st.caption(f"{grade_badge} | {state_info['label']}")
                pct_val = max(0.0, min(1.0, float(state_info.get("pct", cur_d / max_d if max_d > 0 else 1.0))))
                st.progress(pct_val, text=f"{cur_d} / {max_d} Durability ({int(pct_val * 100)}%)")
                if state_info.get("is_broken"):
                    st.error("🛑 BROKEN: Weapon/Armor has fractured!")
                elif state_info.get("is_dulled"):
                    st.warning("🟠 DULLED/CRACKED: Imposing -2 penalty to checks!")
                st.divider()
            else:
                st.caption(f"- **{slot_label}:** None")

        total_dur_needed = sum(max(0, d.get("max", 100) - d.get("cur", 100)) for d in gear_dur.values())
        if total_dur_needed > 0:
            st.caption(f"Maintenance Required: **{total_dur_needed} pts** of wear | Cost: **{total_dur_needed} Col**")
            if st.button("🔨 Repair All Equipped Gear", key="btn_repair_all_gear_hud", use_container_width=True):
                for slot_k in ["head", "chest", "main_hand", "off_hand", "accessory"]:
                    if slot_k in gear_dur and hasattr(mechanics, "repair_item"):
                        mechanics.repair_item(player, slot_k)
                save_game(player, st.session_state.messages)
                st.toast("🔨 All equipped gear repaired!", icon="✨")
                st.rerun()

        
    with st.expander("🦾 Magitech & Bio-Grafts", expanded=False):
        cap = get_strain_capacity(player)
        cur = get_current_strain(player)
        st.write(f"**Strain Capacity:** `{cur} / {cap}`")
        if cur > cap:
            st.error(f"⚠️ **OVER-STRAIN:** Exceeded capacity! Subject to Arcane Dissonance / Necrotic Rejection.")
            st.progress(1.0)
        else:
            st.progress(min(1.0, cur / max(1, cap)))

        st.caption("Strain limit = CON Mod + Floor(Level / 2). One graft per slot.")
        
        grafts = player.get("grafts", {})
        slots = [("head", "Head"), ("torso", "Torso"), ("left_arm", "Left Arm"), ("right_arm", "Right Arm"), ("legs", "Legs"), ("spine", "Spine / Internal")]
        for s_key, s_label in slots:
            g_val = grafts.get(s_key)
            if g_val:
                g_name = g_val.get("name", str(g_val)) if isinstance(g_val, dict) else str(g_val)
                st.write(f"- **{s_label}:** 🟢 `{g_name}`")
            else:
                st.write(f"- **{s_label}:** *Empty*")
        
    with st.expander("✨ Skills, Spells & Feats", expanded=False):
        if player['racial_abilities']:
            st.write("**Racial Traits:**")
            for r in player['racial_abilities']: st.write(f"- {r}")
            st.divider()
            
        for s_name, s_data in player.get('skills', {}).items():
            if isinstance(s_data, dict):
                mastery = s_data.get('mastery', 1)
                desc = s_data.get('description', '')
            else:
                mastery = 1
                desc = str(s_data)
                
            tier_name, next_th = get_mastery_tier_info(mastery)
            st.write(f"**{s_name}** `[{tier_name}]` ({mastery}/1000)")
            pct = min(1.0, mastery / float(next_th)) if next_th > 0 else 1.0
            st.progress(pct, text=f"{mastery}/{next_th} to next milestone")
            if desc: st.caption(desc)
            
        for s in player.get('spells', []) + player.get('feats', []):
            st.write(f"- {s}")

    with st.expander("🔮 Ability Fusion Chamber", expanded=False):
        st.caption("Combine 2 abilities to forge a new synergistic technique (Rule 10).")
        all_pool = list(player.get("skills", {}).keys()) + player.get("spells", []) + player.get("feats", [])
        if len(all_pool) >= 2:
            f_col1, f_col2 = st.columns(2)
            ab1 = f_col1.selectbox("Component A", all_pool, key="fusion_select_a")
            ab2 = f_col2.selectbox("Component B", [x for x in all_pool if x != ab1] or all_pool, key="fusion_select_b")
            if st.button("✨ Initiate Ability Fusion", use_container_width=True):
                st.session_state.pending_dev_command = f"I invoke the Cardinal System Ability Fusion protocol to combine [{ab1}] and [{ab2}] into a new synergistic technique. Calculate the logic and register the fusion."
                st.rerun()
        else:
            st.caption("Need at least 2 abilities to fuse.")
            
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
                
    active_comps = list(mechanics.get_active_party(player)) if hasattr(mechanics, "get_active_party") else []
    with st.expander(f"🛡️ Raiding Party Hub ({len(active_comps) + 1}/4 Vanguard)", expanded=True):
        st.markdown(f"**Party Leader:** 👑 **{player['name']}** `[Lv. {player.get('level', 1)} {player.get('class', 'Warrior')}]`")
        st.caption(f"Active Party: {player['name']} + {len(active_comps)}/3 Companions | 4-Vanguard Cap")

        tab_active_party, tab_benched_party, tab_recruit_pool = st.tabs([
            f"⚔️ Active ({len(active_comps)}/3)",
            f"🛋️ Reserve Roster",
            f"🤝 Recruit Candidates"
        ])

        with tab_active_party:
            if not active_comps:
                st.info("No active companions deployed in vanguard. Check Reserve or Recruit tabs!")
            else:
                for comp in active_comps:
                    c_name = comp["name"]
                    c_lvl = comp.get("level", 1)
                    c_class = comp.get("class", comp.get("archetype", "Specialist"))
                    c_hp = comp.get("hp", 35)
                    c_max_hp = comp.get("max_hp", 35)
                    c_xp = comp.get("xp", 0)
                    c_next_xp = comp.get("next_level_xp", 300)
                    c_morale = comp.get("morale", "Steady")
                    c_stance = comp.get("stance", "default")
                    c_aff = comp.get("affinity", 0)
                    c_tier = comp.get("affinity_tier", "Acquaintance")

                    st.markdown(f"#### 👤 {c_name} `[Lv. {c_lvl} {c_class}]`")
                    st.caption(f"Morale: **{c_morale}** | Affinity: `{c_aff}/100 [{c_tier}]`")
                    hp_pct = min(1.0, max(0.0, c_hp / max(1, c_max_hp)))
                    st.progress(hp_pct, text=f"HP: {c_hp} / {c_max_hp}")

                    col_aff1, col_aff2 = st.columns([2, 1])
                    with col_aff1:
                        if c_aff >= 50:
                            st.success(f"✨ **Dual-Tech Unlocked:** {comp.get('dual_tech_name', 'Combo')}!")
                        else:
                            st.caption("Reach Affinity 50 to unlock Dual-Tech combo.")
                    with col_aff2:
                        if st.button(f"Share Rations (50 Col)", key=f"btn_share_meal_{c_name}"):
                            if player.get("col", 0) >= 50:
                                player["col"] -= 50
                                aff_res = mechanics.increase_companion_affinity(player, c_name, 10, reason="Shared rations")
                                save_game(player, st.session_state.messages)
                                st.toast(aff_res["message"], icon="🍲")
                                st.rerun()
                            else:
                                st.error("Insufficient Col (50 Col).")

                    if c_aff >= 50:
                        combo_id = comp.get("dual_tech_id")
                        if st.button(f"⚡ Execute Dual-Tech: {comp.get('dual_tech_name', 'Combo')}", key=f"btn_exec_dt_{c_name}", use_container_width=True):
                            if hasattr(mechanics, "execute_dual_tech"):
                                dt_res = mechanics.execute_dual_tech(player, combo_id)
                                if dt_res["success"]:
                                    save_game(player, st.session_state.messages)
                                    st.toast(dt_res["message"], icon="⚡")
                                    st.success(dt_res["log"])
                                    st.rerun()
                                else:
                                    st.error(dt_res["message"])

                    stances = comp.get("stances", {})
                    if stances:
                        stance_keys = list(stances.keys())
                        curr_idx = stance_keys.index(c_stance) if c_stance in stance_keys else 0
                        new_st = st.selectbox(
                            f"Stance for {c_name}:",
                            options=stance_keys,
                            index=curr_idx,
                            format_func=lambda k: stances.get(k, {}).get("label", k),
                            key=f"sb_stance_{c_name}"
                        )
                        if new_st != c_stance:
                            if hasattr(mechanics, "set_party_member_stance"):
                                mechanics.set_party_member_stance(player, c_name, new_st)
                                save_game(player, st.session_state.messages)
                                st.toast(f"{c_name}'s stance set to {stances[new_st].get('label', new_st)}!", icon="🎯")
                                st.rerun()
                        st.caption(f"↳ **Effect:** {stances.get(c_stance, {}).get('tactical_effect', '')}")

                    if st.button(f"Bench {c_name} (Send to Reserve)", key=f"btn_bench_{c_name}"):
                        comp["active"] = False
                        save_game(player, st.session_state.messages)
                        st.toast(f"{c_name} moved to Reserve.", icon="🛋️")
                        st.rerun()
                    st.divider()

        with tab_benched_party:
            comps = player.get("party", {})
            benched = [c for c in comps.values() if c.get("recruited", False) and not c.get("active", False)] if isinstance(comps, dict) else [c for c in comps if c.get("recruited", False) and not c.get("active", False)]
            if not benched:
                st.caption("No companions currently in Reserve.")
            else:
                for b_comp in benched:
                    st.markdown(f"**👤 {b_comp['name']}** `[Lv. {b_comp.get('level', 1)}]`")
                    st.caption(f"HP: {b_comp.get('hp', 30)}/{b_comp.get('max_hp', 30)}")
                    if len(active_comps) < 3:
                        if st.button(f"Activate {b_comp['name']} to Vanguard", key=f"btn_activate_{b_comp['name']}"):
                            b_comp["active"] = True
                            save_game(player, st.session_state.messages)
                            st.toast(f"{b_comp['name']} activated to Vanguard!", icon="⚔️")
                            st.rerun()
                    else:
                        st.caption("⚠️ Vanguard is full (Max 3 companions).")
                    st.divider()

        with tab_recruit_pool:
            comps = player.get("party", {})
            all_known = mechanics.RECRUITABLE_COMPANIONS
            unrecruited = [c for name, c in all_known.items() if not (isinstance(comps, dict) and comps.get(name, {}).get("recruited")) and not (isinstance(comps, list) and any(x.get("name") == name and x.get("recruited") for x in comps))]
            if not unrecruited:
                st.success("All known Sector 1 companions have joined your vanguard!")
            else:
                for u_comp in unrecruited:
                    st.markdown(f"##### 👤 {u_comp['name']} — `{u_comp.get('title', u_comp.get('class', 'Warrior'))}`")
                    st.caption(f"**Class:** {u_comp.get('class', '')} | **Lineage:** {u_comp.get('race', 'Human')} | **Starting Level:** {u_comp.get('level', 1)}")
                    st.write(u_comp.get("bio", u_comp.get("background", "")))
                    if st.button(f"Recruit {u_comp['name']} into Vanguard", key=f"btn_recruit_{u_comp['name']}"):
                        rec_res = mechanics.recruit_companion(player, u_comp["name"])
                        if rec_res["success"]:
                            save_game(player, st.session_state.messages)
                            st.balloons()
                            st.toast(rec_res["message"], icon="🤝")
                            st.success(rec_res["log"])
                            st.rerun()
                        else:
                            st.error(rec_res["message"])
                    st.divider()

    # SAO Status Cursor
    cursor_data = mechanics.get_cursor_status(player) if hasattr(mechanics, "get_cursor_status") else {"status": "green", "label": "🟢 Lawful (Green)", "badge": "🟢 Green", "current_infamy": 0, "merchant_surcharge": 0.0, "safe_zone_clearance": True, "description": "Lawful citizen."}
    with st.expander(f"⚖️ SAO Status: {cursor_data['badge']}", expanded=False):
        st.markdown(f"#### {cursor_data['label']}")
        st.write(cursor_data.get("description", ""))
        col_cur1, col_cur2 = st.columns(2)
        col_cur1.metric("Infamy Rating", f"{cursor_data['current_infamy']} pts")
        col_cur2.metric("Merchant Surcharge", f"+{int(cursor_data['merchant_surcharge']*100)}%")
        if cursor_data["safe_zone_clearance"]:
            st.success("✅ **Safe-Zone Clearance Granted:** Barrier wards recognize lawful status.")
        else:
            st.error("🚨 **SAFE-ZONE WARD LOCKDOWN:** Anti-PK turrets active!")
        if cursor_data["status"] == "orange":
            inf = cursor_data["current_infamy"]
            atone_cost = inf * 500
            st.warning(f"⚠️ Pay reparations at Washington Council ({atone_cost:,} Col) to restore Green Cursor.")
            if st.button(f"Pay Municipal Atonement ({atone_cost:,} Col)", key="btn_pay_atone_sb", use_container_width=True):
                at_res = mechanics.pay_criminal_atonement(player)
                if at_res["success"]:
                    save_game(player, st.session_state.messages)
                    st.toast(at_res["message"], icon="🟢")
                    st.rerun()

    # Regional Factions
    factions_list = mechanics.get_all_faction_standings(player) if hasattr(mechanics, "get_all_faction_standings") else []
    with st.expander("🚩 Regional Factions & Guild Alliances", expanded=False):
        st.caption("Reputation standings across regional coalitions and baronies.")
        for fac in factions_list:
            f_def = mechanics.REGIONAL_FACTIONS.get(fac["faction_id"], {})
            st.markdown(f"##### {f_def.get('icon', '🚩')} {fac['name']}")
            st.caption(f"**Leader:** {f_def.get('leader', 'Unknown')} | **HQ:** {f_def.get('headquarters', 'Unknown')}")
            score = fac["score"]
            st.markdown(f"**Standing:** {fac['badge']} `({score:+d} Rep)`")
            norm_progress = min(1.0, max(0.0, (score + 100) / 200.0))
            st.progress(norm_progress, text=f"Reputation: {score}/100 [{fac['label']}]")
            st.divider()

    # Wilderness Survival & Chrono-Atmosphere
    time_info = mechanics.get_game_time_info(player) if hasattr(mechanics, "get_game_time_info") else {"time_str": "Day 1, 08:00", "period_info": {"label": "Day", "desc": "Clear light."}}
    cur_weather = mechanics.get_current_weather(player) if hasattr(mechanics, "get_current_weather") else {"icon": "☀️", "label": "Clear Skies", "desc": "Standard visibility", "effect": "No penalties"}
    with st.expander("⛺ Wilderness Survival & Chrono-Atmosphere", expanded=False):
        p_info = time_info.get("period_info", {})
        st.markdown(f"### ⏱️ {time_info.get('time_str', '08:00')}")
        st.caption(f"**Period:** {p_info.get('label', 'Day')} | **Field Effects:** {p_info.get('desc', 'Standard')}")
        st.markdown(f"#### {cur_weather.get('icon', '🌤️')} {cur_weather.get('label', 'Clear')}")
        st.caption(f"*{cur_weather.get('desc', '')}*")
        st.info(f"**Atmospheric Modifier:** {cur_weather.get('effect', 'None')}")

        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            if st.button("⏳ Wait 1h", key="btn_wait_1h_hud", use_container_width=True):
                w_res = mechanics.advance_game_time(player, minutes=60)
                save_game(player, st.session_state.messages)
                st.toast(f"Waited 1 Hour. Time is {w_res['time_str']}.", icon="⏳")
                st.rerun()
        with tc2:
            if st.button("🌅 Rest to Dawn", key="btn_rest_dawn_hud", use_container_width=True):
                w_res = mechanics.advance_game_time(player, minutes=480)
                save_game(player, st.session_state.messages)
                st.toast(f"Rested until Dawn ({w_res['time_str']}).", icon="🌅")
                st.rerun()
        with tc3:
            if st.button("🎲 Attune Sky", key="btn_sky_attune_hud", use_container_width=True):
                rw_res = mechanics.roll_random_weather(player)
                save_game(player, st.session_state.messages)
                st.toast(f"Atmospheric shift: {rw_res['weather_info']['label']}!", icon="🌪️")
                st.rerun()

        st.divider()
        tab_kitch, tab_cp = st.tabs(["🍳 Campfire Kitchen", "🏕️ Pitch Camp"])
        with tab_kitch:
            st.markdown("##### 🍲 Campfire Culinary Crafting")
            for r_key, r_data in getattr(mechanics, "CAMPFIRE_RECIPES", {}).items():
                st.markdown(f"**{r_data['name']}**")
                st.caption(f"Buff: `{r_data['buff']['name']}` ({r_data['buff']['desc']})")
                if st.button(f"Cook {r_data['name']}", key=f"btn_cook_{r_key}_hud"):
                    c_res = mechanics.cook_campfire_meal(player, r_key)
                    if c_res["success"]:
                        save_game(player, st.session_state.messages)
                        st.toast(c_res["message"], icon="🍲")
                        st.rerun()
                    else:
                        st.error(c_res["message"])
        with tab_cp:
            st.markdown("##### ⛺ 8-Hour Wilderness Rest & Perimeter Watch")
            w_choices = ["Ren", "Elora", "Torvald", "Kibs", "Solo / No Watch"]
            w_guard = st.selectbox("Assign Watch Guard", w_choices, key="sb_camp_guard_hud")
            if st.button("⛺ Pitch Camp & Rest (8 Hours)", key="btn_pitch_camp_action_hud", use_container_width=True):
                guard = None if w_guard == "Solo / No Watch" else w_guard
                camp_res = mechanics.pitch_wilderness_camp(player, watch_companion=guard)
                if camp_res["success"]:
                    save_game(player, st.session_state.messages)
                    st.toast(camp_res["message"], icon="⛺")
                    st.success(camp_res["log"])
                    st.rerun()
                else:
                    st.error(camp_res["message"])

    # Labyrinth Dungeon & Sector Overlord
    loc_str = str(player.get("location", "")).lower()
    in_dungeon = any(w in loc_str for w in ["dungeon", "depths", "labyrinth", "pohatcong", "spire", "overlord"])
    with st.expander("🏰 Labyrinth Dungeon: The Pohatcong Depths", expanded=in_dungeon):
        st.markdown("#### 🏰 Sector 1 Labyrinth: The Pohatcong Depths")
        st.caption("An 8-tier instanced subterranean megastructure.")
        d_room = mechanics.get_current_dungeon_room(player) if hasattr(mechanics, "get_current_dungeon_room") else {"name": "Labyrinth Entrance", "desc": "Ancient stone portal."}
        st.write(f"**Current Chamber:** {d_room.get('name', 'Entry')} (Tier {d_room.get('tier', 1)})")
        st.write(d_room.get("desc", ""))

        st.markdown("##### 👑 Sector Boss: The Gilded Spire Overlord")
        boss_data = mechanics.get_overlord_status(player) if hasattr(mechanics, "get_overlord_status") else {}
        b_hp = boss_data.get("hp", 450)
        b_max = boss_data.get("max_hp", 450)
        b_bg = boss_data.get("break_gauge", 100)
        b_bg_max = boss_data.get("max_break_gauge", 100)
        st.progress(min(1.0, max(0.0, b_hp / max(1, b_max))), text=f"Overlord HP: {b_hp} / {b_max}")
        st.progress(min(1.0, max(0.0, b_bg / max(1, b_bg_max))), text=f"Break Gauge: {b_bg} / {b_bg_max} ({'STAGGERED!' if boss_data.get('is_staggered') else 'Intact'})")
        if boss_data.get("is_staggered"):
            st.error("💥 **BOSS STAGGERED!** Attacks deal double critical damage!")

    # Sovereign Homestead, Vault & Mythic Forge
    mechanics.ensure_homestead_system(player) if hasattr(mechanics, "ensure_homestead_system") else None
    h_data = player.get("homestead", {})
    h_owned = h_data.get("owned", False)
    with st.expander("🏰 Sovereign Homestead, Vault & Mythic Forge", expanded=h_owned):
        if not h_owned:
            st.markdown("#### 🏰 Washington Borough Estate")
            st.caption("📍 *Washington Borough Crossroads, Sector 1 Safe Zone*")
            st.write("Fortified compound offering subsurface vault storage, botanical aether-greenhouses, a trophy hall, and deepforged master-forge space.")
            st.info("💰 **Purchase Price:** 3,500 Col | **Deed:** Requires earning in-game Col (Rule 22)")
            if player.get("col", 0) >= 3500:
                if st.button("🏰 Purchase Washington Borough Estate (3,500 Col)", key="btn_buy_homestead_hud", use_container_width=True):
                    b_res = mechanics.purchase_homestead(player)
                    if b_res["success"]:
                        save_game(player, st.session_state.messages)
                        st.balloons()
                        st.toast(b_res["message"], icon="🏰")
                        st.rerun()
            else:
                st.warning(f"🔒 Requires 3,500 Col (You have {player.get('col', 0):,} Col).")
        else:
            v_cap = mechanics.get_vault_capacity(player) if hasattr(mechanics, "get_vault_capacity") else {"max_slots": 20, "max_lbs": 500}
            st.markdown(f"### 🏰 {h_data.get('name', 'Washington Borough Manor')}")
            st.caption(f"Vault: Tier {h_data.get('vault_tier', 1)} | Greenhouse: Tier {h_data.get('greenhouse_tier', 1)} | Master Anvil: {'Active' if h_data.get('has_master_anvil') else 'Unbuilt'}")
            tv1, tv2, tv3, tv4, tv5 = st.tabs(["📦 Vault", "🏆 Trophies", "🌿 Greenhouse", "⚡ Forge", "⚖️ Market"])
            with tv1:
                v_col = h_data.get("vault_col", 0)
                st.write(f"💰 Vault Col: `{v_col:,} Col` | Stored Items: `{len(h_data.get('vault_items', []))} / {v_cap['max_slots']}`")
                dep_col = st.number_input("Deposit Col", min_value=1, max_value=max(1, player.get("col", 0)), value=min(100, max(1, player.get("col", 0))), step=50, key="num_vault_dep")
                if st.button("📥 Deposit Col to Vault", key="btn_dep_vault_col"):
                    mechanics.deposit_to_vault(player, "", col_amount=int(dep_col))
                    save_game(player, st.session_state.messages)
                    st.rerun()
            with tv2:
                mounted = h_data.get("mounted_trophies", [])
                st.write(f"🏛️ Occupied Pedestals: `{len(mounted)} / 5`")
                for tr in mounted:
                    st.success(f"🏆 {tr.get('name', 'Trophy')}: {tr.get('buff', '')}")
            with tv3:
                st.markdown("##### 🌿 Alchemical Garden Plots")
                if st.button("🌱 Harvest Daily Greenhouse Yield", key="btn_harvest_garden_hud"):
                    g_res = mechanics.harvest_alchemical_garden(player)
                    if g_res["success"]:
                        save_game(player, st.session_state.messages)
                        st.toast(g_res["message"], icon="🌿")
                        st.success(g_res["log"])
                        st.rerun()
                    else:
                        st.info(g_res["message"])
            with tv4:
                st.markdown("##### ⚡ Deepforged Master-Forge")
                if not h_data.get("has_master_anvil"):
                    st.info("Requires Master-Anvil installation.")
                    if st.button("Build Master-Anvil (1,500 Col)", key="btn_build_anvil_hud"):
                        mechanics.upgrade_homestead_facility(player, "master_anvil")
                        save_game(player, st.session_state.messages)
                        st.rerun()
                else:
                    st.success("✅ Deepforged Anvil Ready for Grade 6 Mythic Upgrading.")
            with tv5:
                st.markdown("##### ⚖️ Commodity Market")
                st.caption("Trade bulk materials (Scrap Metal, Aether Shards, Alchemical Herbs).")


    with st.expander("🌍 Global Threat Intelligence", expanded=False):
        global_news = world_state.get("global_news", [])
        if not global_news:
            st.caption("No global uplinks established yet...")
        else:
            for news in reversed(global_news[-15:]):
                st.info(f"📡 {news}")
        
    with st.expander("👾 SubAgent Entity Dossiers", expanded=False):
        st.caption("Inspect awakened SubAgents: their life stories, quirks, dreams, and secret fears.")
        entities_dir = os.path.join(BASE_DIR, "Entities")
        if os.path.exists(entities_dir):
            entity_files = [f for f in os.listdir(entities_dir) if f.endswith(".json")]
            if not entity_files:
                st.caption("No SubAgents awakened yet.")
            else:
                for ef in entity_files:
                    try:
                        with open(os.path.join(entities_dir, ef), "r", encoding="utf-8") as f:
                            ent_data = json.load(f)
                        e_name = ent_data.get("name", ef)
                        e_type = ent_data.get("species_or_type", "Entity")
                        e_role = ent_data.get("role", "entity")
                        icon = "🤖" if "companion" in ef or "ren" in ef else "👾"
                        
                        st.markdown(f"### {icon} {e_name}")
                        st.caption(f"**Classification:** {e_type} | **Role:** {e_role}")
                        
                        with st.expander("🎙️ Genesis Interview: 'What has your life been up to now?'"):
                            st.info(f"\"{ent_data.get('backstory_interview', 'No interview on record.')}\"")
                            
                        st.markdown(f"**🧠 Personality:** {ent_data.get('personality', 'Unknown')}")
                        
                        quirks = ent_data.get("quirks", [])
                        if quirks:
                            st.markdown("**🎭 Quirks & Tics:**")
                            for q in quirks:
                                st.markdown(f"- {q}")
                                
                        st.markdown(f"🌟 **Desires:** {ent_data.get('dreams_and_desires', 'Survival')}")
                        st.markdown(f"🩸 **Fears:** {ent_data.get('fears_and_dreads', 'Destruction')}")
                        st.markdown(f"⚔️ **Combat Style:** {ent_data.get('tactical_style', 'Aggressive')}")
                        st.divider()
                    except Exception:
                        pass
        else:
            st.caption("Entities directory not found.")

    st.divider()
    st.subheader("🎙️ Live Table Companion")
    st.caption("Record voice commands or GM narration.")
    mic_active = st.toggle("Activate Microphone Module", value=False, help="Enable native voice recording")
    
    if mic_active:
        voice_mode = st.radio("Voice Mode", ["GM Companion Log", "Player Action"], horizontal=True)
        audio_val = st.audio_input("🎙️ Record Voice", key="companion_mic", sample_rate=None)
        
        if audio_val is not None:
            audio_bytes = audio_val.getvalue()
            audio_hash = str(hash(audio_bytes))
            
            if audio_hash != st.session_state.get("last_processed_audio_hash"):
                try:
                    with st.spinner("Cardinal System analyzing audio..."):
                        print(f"[VOICE] Processing {len(audio_bytes)} audio bytes in mode: {voice_mode}", flush=True)
                        import backend.voice_engine as voice_engine
                        is_action = (voice_mode == "Player Action")
                        result_text = voice_engine.process_voice_input(api_key, audio_bytes, action_mode=is_action)
                        print(f"[VOICE] Transcribed result: {result_text}", flush=True)
                        
                        if is_action:
                            # Append player's spoken action
                            st.session_state.messages.append({"role": "user", "content": f"🗣️ [Voice Action] {result_text}"})
                            
                            # Execute the full V2 actor pipeline
                            import backend.gm_engine as gm_engine
                            import backend.persona_engine as persona_engine
                            
                            # 1. Staging ground
                            visible_room = gm_engine.generate_visible_state(api_key=api_key)
                            
                            # 2. All Room SubAgents Act Autonomously (Companions, Monsters, NPCs)
                            subagent_actions = persona_engine.run_all_room_subagents(api_key=api_key, visible_room=visible_room)
                            subagent_log_lines = []
                            for sa in subagent_actions:
                                actor_id = sa.get("actor_id", "")
                                actor_name = sa.get("actor_name", actor_id or "SubAgent")
                                thought = sa.get("internal_thought", "")
                                intent = sa.get("intended_action", "Stands ready.")
                                icon = "🤖" if "ren" in actor_id.lower() else "👾"
                                subagent_log_lines.append(f"**[{icon} {actor_name} — SubAgent Mind]**\n> *\"{thought}\"*\n> **Intent:** {intent}")
                            subagent_log = "\n\n".join(subagent_log_lines) if subagent_log_lines else ""
                            
                            # 3. GM resolution
                            turn_data = gm_engine.resolve_turn(api_key=api_key, player_action=result_text)
                            narrative = turn_data.get("narrative_recap", "")
                            
                            combat_logs = turn_data.get("combat_logs", [])
                            hp_changes = turn_data.get("hp_changes", {})
                            mechanics_entries = []
                            if combat_logs and isinstance(combat_logs, list):
                                for log in combat_logs:
                                    mechanics_entries.append(f"* 🎲 `{log}`")
                            if hp_changes and isinstance(hp_changes, dict):
                                for eid, delta in hp_changes.items():
                                    sign = "+" if delta > 0 else ""
                                    icon = "🩹" if delta > 0 else "🩸"
                                    clean_eid = eid.replace("companion_", "").capitalize()
                                    mechanics_entries.append(f"* {icon} **{clean_eid}:** {sign}{delta} HP")
                            mechanics_log = "\n".join(mechanics_entries) if mechanics_entries else ""
                            
                            state_updates = turn_data.get("player_state_updates", {})
                            if state_updates is None:
                                state_updates = {}
                            if "player" in hp_changes:
                                state_updates["hp_change"] = hp_changes["player"]
                                
                            apply_player_state_updates(state_updates)
                            apply_companion_state_updates(hp_changes)
                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": narrative,
                                "mechanics_log": mechanics_log,
                                "subagent_log": subagent_log
                            })
                        else:
                            st.session_state.messages.append({"role": "system", "content": f"**[LIVE COMPANION LOG]**\n\n{result_text}"})
                            
                    st.session_state["last_processed_audio_hash"] = audio_hash
                    save_game(st.session_state.player, st.session_state.messages)
                    st.toast("Voice command executed!", icon="🗣️")
                    st.rerun()
                except Exception as e:
                    print(f"[VOICE ERROR] {e}", flush=True)
                    st.error(f"Voice Processing Error: {e}")
            
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

    # Continental & Faction News Wire
    news_list = world_state.get("global_news", [])
    if news_list:
        with st.expander("📡 Continental News Wire", expanded=False):
            for n in reversed(news_list[-5:]):
                st.caption(f"• {n}")

    # Regional Hub & Fast Actions (Milestone 1)
    curr_loc = st.session_state.player.get("location", "")
    is_in_safe_zone = "washington" in curr_loc.lower() or (map_state.get("player_x") == 50 and map_state.get("player_y") == 50)
    
    with st.expander("🏛️ Regional Hub & Navigation", expanded=is_in_safe_zone):
        if is_in_safe_zone:
            st.success("📍 **Sanctuary: Washington Borough Safe-Zone**")
            st.caption("A fortified civilian sanctuary ruled by the Warren County Barony.")
            
            c_hub1, c_hub2 = st.columns(2)
            with c_hub1:
                if st.button("🛏️ Safe-Zone Rest (24h)", use_container_width=True, help="Full HP recovery & triggers living world simulation."):
                    st.session_state.pending_dev_command = "I take a full 24-hour long rest in the Washington Borough sanctuary to recover our wounds and hear the latest regional news."
                    st.rerun()
                if st.button("🏥 Visit Doc Mercer", use_container_width=True, help="Visit the subterranean clinic for graft consultation & surgery."):
                    st.session_state.pending_dev_command = "I head down into the ancient vaulted catacombs beneath Washington Avenue to consult with Doc Mercer at his flesh-weaving and graft clinic."
                    st.rerun()

            with c_hub2:
                if st.button("🪙 Quartermaster Vane", use_container_width=True, help="Trade supplies and review Warren County Barony bounties."):
                    st.session_state.pending_dev_command = "I report to Quartermaster Vane at the Warren County logistics depot to trade salvage and review active bounties."
                    st.rerun()
                if st.button("⛏️ Travel to Oxford Mines", use_container_width=True, help="Depart the safe zone toward Oxford Adits (X:53, Y:48)."):
                    st.session_state.pending_dev_command = "I gear up with Ren and travel southeast along the ridge toward the Oxford Mining District."
                    st.rerun()

            # Fast Surgical Action if graft candidate in inventory (Milestone 2)
            inv_items = [item.get("name", str(item)) if isinstance(item, dict) else str(item) for item in st.session_state.player.get("inventory", [])]
            graft_candidates = [i for i in inv_items if any(k in i.lower() for k in ["graft", "core", "carapace", "piston", "optic", "bio", "implant", "plate"])]
            if graft_candidates:
                st.divider()
                st.caption("💉 **Doc Mercer's Clinic: Fast Surgical Graft Installation**")
                sel_graft = st.selectbox("Select Component to Graft:", graft_candidates, key="hub_graft_candidate_select")
                sel_slot = st.selectbox("Target Anatomical Slot:", ["Spine", "Torso", "Left Arm", "Right Arm", "Legs", "Head"], key="hub_graft_slot_select")
                if st.button(f"🦾 Pay Doc Mercer (35 Col) to Install [{sel_graft}] into [{sel_slot}]", use_container_width=True):
                    st.session_state.pending_dev_command = f"I pay Doc Mercer 35 Col to surgically install [{sel_graft}] into my [{sel_slot.lower().replace(' ', '_')}]. Check my strain limit and begin the operation."
                    st.rerun()

        else:
            st.warning(f"📍 **Hostile Territory:** {curr_loc or 'Wilderness'}")
            st.caption("Active threat zone. Keep your weapon ready.")
            if st.button("🏛️ Return to Washington Safe-Zone", use_container_width=True, help="Navigate back to Washington Borough Safe-Zone (X:50, Y:50)."):
                st.session_state.pending_dev_command = "We fall back from the hazard zone and take the cleared trail back to the Washington Borough Safe-Zone."
                st.rerun()

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
    with st.expander("💾 Save & Backup Management"):
        st.caption("Streamlit Cloud erases local files when it sleeps. Download your save file or transcript to keep your game safe!")
        
        # Read current master state if available
        m_path = os.path.join(BASE_DIR, ".game_state", "secret_master_state.json")
        cur_master = {}
        if os.path.exists(m_path):
            try:
                with open(m_path, "r", encoding="utf-8") as f:
                    cur_master = json.load(f)
            except Exception:
                pass

        # 1. Full State Export (JSON)
        save_payload = {
            "player": st.session_state.player,
            "messages": st.session_state.messages,
            "world_state": st.session_state.get("world_state", {}),
            "master_state": cur_master,
            "last_saved": time.time()
        }
        try:
            save_json_str = json.dumps(save_payload, indent=4, default=str)
        except Exception:
            save_json_str = json.dumps({"error": "Failed to serialize state"}, indent=4)

        # Immediate Disk Flush
        if st.button("💾 Force Instant Save to Disk", key="btn_quick_save_disk"):
            save_game(st.session_state.player, st.session_state.messages)
            st.toast("Campaign state saved to disk!", icon="💾")
            st.success("Successfully saved `save_game.json`, `world_state.json`, and rolling chat backup.")

        st.download_button(
            label="📥 Export Full Campaign State (.json)",
            data=save_json_str,
            file_name="crucible_campaign_save.json",
            mime="application/json",
            key="btn_download_campaign_json"
        )

        with st.expander("📋 View / Copy Raw Save JSON (Clipboard Backup)"):
            st.caption("If your mobile browser or network blocks file downloads, copy this raw JSON directly to your notes.")
            st.text_area("Raw Save JSON", value=save_json_str, height=180, key="save_json_raw_area")

        # 2. Readable Transcript Backup (Markdown)
        transcript_lines = ["# 🗡️ Campaign Transcript: The Fractured Overlay\n\n"]
        for idx, m in enumerate(st.session_state.messages):
            role = m.get("role", "system")
            content, mechanics_log, subagent_log = extract_turn_components(m)
            if role == "user":
                transcript_lines.append(f"### 👤 Turn {idx}: Player Action\n{content}\n\n")
            elif role in ["assistant", "system"]:
                icon = "🤖" if role == "assistant" else "📡"
                title = "Resolution" if role == "assistant" else "System Announcement"
                entry = f"### {icon} Turn {idx}: {title}\n{content}\n"
                if mechanics_log:
                    entry += f"\n<details>\n<summary>🎲 Dice Rolls & Game Mechanics (Click to open/close)</summary>\n\n{mechanics_log}\n\n</details>\n"
                if subagent_log:
                    entry += f"\n<details>\n<summary>🧠 SubAgent Thoughts & Planned Actions (Click to open/close)</summary>\n\n{subagent_log}\n\n</details>\n"
                transcript_lines.append(entry + "\n")
        transcript_md = "".join(transcript_lines)
        
        st.download_button(
            label="📜 Download Campaign Transcript (.md)",
            data=transcript_md,
            file_name="campaign_transcript.md",
            mime="text/markdown",
            key="btn_download_campaign_transcript_md"
        )
        
        # 3. Import & Restore (File or Direct Paste)
        st.divider()
        st.markdown("**Restore Campaign**")
        uploaded_file = st.file_uploader("📤 Import Save File (.json)", type="json", key="save_file_uploader")
        if uploaded_file is not None:
            if st.button("Restore from Uploaded File", key="btn_restore_uploaded_file"):
                try:
                    loaded_data = json.load(uploaded_file)
                    st.session_state.player = loaded_data["player"]
                    st.session_state.messages = loaded_data["messages"]
                    if "world_state" in loaded_data:
                        st.session_state.world_state = loaded_data["world_state"]
                    if "master_state" in loaded_data and loaded_data["master_state"]:
                        os.makedirs(os.path.dirname(m_path), exist_ok=True)
                        with open(m_path, "w", encoding="utf-8") as f:
                            json.dump(loaded_data["master_state"], f, indent=4)
                    save_game(st.session_state.player, st.session_state.messages)
                    st.success("Save loaded successfully! Refreshing...")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to load save: {e}")

        paste_restore = st.text_area("Or Paste Raw Save JSON Here:", height=90, key="paste_restore_json_input", placeholder='{"player": ...}')
        if st.button("Restore from Pasted JSON", key="btn_restore_pasted_json"):
            if paste_restore.strip():
                try:
                    loaded_data = json.loads(paste_restore.strip())
                    st.session_state.player = loaded_data["player"]
                    st.session_state.messages = loaded_data["messages"]
                    if "world_state" in loaded_data:
                        st.session_state.world_state = loaded_data["world_state"]
                    if "master_state" in loaded_data and loaded_data["master_state"]:
                        os.makedirs(os.path.dirname(m_path), exist_ok=True)
                        with open(m_path, "w", encoding="utf-8") as f:
                            json.dump(loaded_data["master_state"], f, indent=4)
                    save_game(st.session_state.player, st.session_state.messages)
                    st.success("Save restored from text! Refreshing...")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to parse pasted save: {e}")

# --- SIDEBAR MOUNT ---
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
        p_data = cg.load_character_from_folder(BASE_DIR, sel_profile)
        if p_data:
            st.session_state.player = p_data['player']
            st.session_state.messages = p_data.get('messages', [])
            st.session_state.active_profile = sel_profile
            st.session_state.character_creation_mode = False
            # Sync to secret_master_state.json if present
            m_path = os.path.join(BASE_DIR, ".game_state", "secret_master_state.json")
            if os.path.exists(m_path):
                try:
                    with open(m_path, "r", encoding="utf-8") as f:
                        m_data = json.load(f)
                    m_data["player"] = p_data['player']
                    with open(m_path, "w", encoding="utf-8") as f:
                        json.dump(m_data, f, indent=4)
                except Exception:
                    pass
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
        render_game_hud()

# --- MAIN UI: THE CHAT WINDOW OR CALIBRATION WIZARD ---
if st.session_state.get("character_creation_mode", False):
    render_character_calibration_wizard()
    st.stop()

st.title("🗡️ The Fractured Overlay")
st.caption("A Death-Game TTRPG powered by the Cardinal System AI.")

# Render Chat History
for msg in st.session_state.messages:
    avatar = "👾" if msg.get("role") in ["assistant", "system"] else "👤"
    with st.chat_message(msg["role"], avatar=avatar):
        content, mechanics_log, subagent_log = extract_turn_components(msg)
        st.markdown(content)
        if mechanics_log:
            with st.expander("🎲 Dice Rolls & Game Mechanics (Click to open/close)", expanded=False):
                st.markdown(mechanics_log)
        if subagent_log:
            with st.expander("🧠 SubAgent Thoughts & Planned Actions (Click to open/close)", expanded=False):
                st.markdown(subagent_log)
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
            import backend.persona_engine as persona_engine
            
            # a. Generate the Staging Ground (Visible Room)
            visible_room = gm_engine.generate_visible_state(api_key=api_key)
            
            # b. All Room SubAgents Act Autonomously (Companions, Monsters, NPCs)
            subagent_actions = persona_engine.run_all_room_subagents(api_key=api_key, visible_room=visible_room)
            subagent_log_lines = []
            for sa in subagent_actions:
                actor_id = sa.get("actor_id", "")
                actor_name = sa.get("actor_name", actor_id or "SubAgent")
                thought = sa.get("internal_thought", "")
                intent = sa.get("intended_action", "Stands ready.")
                icon = "🤖" if "ren" in actor_id.lower() else "👾"
                subagent_log_lines.append(f"**[{icon} {actor_name} — SubAgent Mind]**\n> *\"{thought}\"*\n> **Intent:** {intent}")
            subagent_log = "\n\n".join(subagent_log_lines) if subagent_log_lines else ""
            
            # c. Resolve the turn (Read Player Action + SubAgent Action Queue)
            turn_data = gm_engine.resolve_turn(api_key=api_key, player_action=ai_prompt)
            
            narrative = turn_data.get("narrative_recap", "Error parsing narrative.")
            
            # Extract player state updates into the format app.py expects
            state_updates = turn_data.get("player_state_updates", {})
            if state_updates is None:
                state_updates = {}
                
            # Add HP changes to player state updates dynamically
            hp_changes = turn_data.get("hp_changes", {})
            if "player" in hp_changes:
                state_updates["hp_change"] = hp_changes["player"]
                
            # Synchronize Companion HP (e.g. Ren) across party sheet and HUD
            apply_companion_state_updates(hp_changes)
                
            # Fallback for old variables
            image_prompt = "" 
            
            # Living World Continental News Wire Updates (Milestone 1)
            news_add = turn_data.get("global_news_add", [])
            if state_updates and isinstance(state_updates, dict):
                news_add = news_add or state_updates.get("global_news_add", [])
            if news_add and isinstance(news_add, list):
                if "global_news" not in world_state: world_state["global_news"] = []
                for n in news_add:
                    if n not in world_state["global_news"]:
                        world_state["global_news"].append(n)
                try:
                    with open("world_state.json", "w", encoding="utf-8") as f:
                        json.dump(world_state, f, indent=4)
                except Exception:
                    pass

            # Apply State Updates
            if state_updates and isinstance(state_updates, dict):
                loc = state_updates.get("location")
                if loc and isinstance(loc, str):
                    st.session_state.player["location"] = loc
                    
                w_status = state_updates.get("world_status")
                if w_status and isinstance(w_status, str):
                    world_state["world_status"] = w_status
                    try:
                        with open("world_state.json", "w", encoding="utf-8") as f:
                            json.dump(world_state, f, indent=4)
                    except Exception:
                        pass

                    
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

                apply_player_state_updates(state_updates)
                                
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
            hp_changes = turn_data.get("hp_changes", {})
            mechanics_entries = []
            if combat_logs and isinstance(combat_logs, list):
                for log in combat_logs:
                    mechanics_entries.append(f"* 🎲 `{log}`")
            if hp_changes and isinstance(hp_changes, dict):
                for eid, delta in hp_changes.items():
                    sign = "+" if delta > 0 else ""
                    icon = "🩹" if delta > 0 else "🩸"
                    clean_eid = eid.replace("companion_", "").capitalize()
                    mechanics_entries.append(f"* {icon} **{clean_eid}:** {sign}{delta} HP")
            mechanics_log = "\n".join(mechanics_entries) if mechanics_entries else ""

            st.markdown(narrative)
            if mechanics_log:
                with st.expander("🎲 Dice Rolls & Game Mechanics (Click to open/close)", expanded=False):
                    st.markdown(mechanics_log)
            if subagent_log:
                with st.expander("🧠 SubAgent Thoughts & Planned Actions (Click to open/close)", expanded=False):
                    st.markdown(subagent_log)
            
            image_data = None
            
    new_msg = {
        "role": "assistant", 
        "content": narrative,
        "mechanics_log": mechanics_log,
        "subagent_log": subagent_log,
        "image_data": image_data
    }
    st.session_state.messages.append(new_msg)
    save_game(st.session_state.player, st.session_state.messages)
    
    st.rerun()
