import streamlit as st
import json
import os
import sys
import time
import base64
import re

# Ensure base directory is in sys.path for clean, reliable imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import backend.schemas as schemas
import backend.gm_engine as gm_engine
import backend.actor_engine as actor_engine
import backend.mechanics as mechanics
import backend.character_generator as cg
import backend.world_atlas as world_atlas
import backend.bestiary_compendium as bestiary
import backend.persona_engine as persona_engine
import backend.database as db
import map_engine
if not hasattr(map_engine, "SECTORS"):
    import importlib
    try:
        importlib.reload(map_engine)
    except Exception as _re_err:
        print(f"[RELOAD ERROR] Failed to reload map_engine: {_re_err}", flush=True)
from backend.database.adapters import (
    activate_character_session as adapter_activate_character_session,
    atomic_read_json,
    atomic_write_json,
    ensure_database_initialized,
    get_base_dir,
    list_save_slots,
    load_world as adapter_load_world,
    sanitize_character_slug,
    save_game as adapter_save_game,
)
from backend.database.engine import db_transaction
from backend.database.repositories import (
    CharacterRepository,
    MasterStateRepository,
    PartyRepository,
    StagingRepository,
)


def _refresh_stale_backend_modules():
    """
    Streamlit re-executes app.py on every rerun/redeploy but keeps already-imported backend
    and root engine modules cached in memory. Reload modules in dependency order ONLY when one or more
    of their files actually changed on disk since they were loaded.
    """
    import importlib
    import backend as _backend_pkg

    # Ensure map_engine has current registry attributes before mtime checks
    mod_map = sys.modules.get("map_engine")
    if mod_map is not None and not hasattr(mod_map, "SECTORS"):
        try:
            importlib.reload(mod_map)
        except Exception as reload_err:
            print(f"[HOT-RELOAD] Failed to reload map_engine: {reload_err}", flush=True)

    order = ["backend.schemas", "backend.world_atlas", "backend.bestiary_compendium", "backend.mechanics",
             "backend.character_generator", "backend.persona_engine", "backend.voice_engine",
             "backend.actor_engine", "backend.auth", "backend.gm_engine", "map_engine"]
    current = {}
    for mod_name in order:
        mod = sys.modules.get(mod_name)
        path = getattr(mod, "__file__", None) if mod else None
        if path and os.path.exists(path):
            current[mod_name] = os.path.getmtime(path)
    previous = getattr(_backend_pkg, "_loaded_mtimes", None)
    if previous is None:
        _backend_pkg._loaded_mtimes = current
        return
    if previous == current:
        return
    for mod_name in order:
        if previous.get(mod_name) != current.get(mod_name):
            mod = sys.modules.get(mod_name)
            if mod is not None:
                try:
                    importlib.reload(mod)
                except Exception as reload_err:
                    print(f"[HOT-RELOAD] Failed to reload {mod_name}: {reload_err}", flush=True)
    _backend_pkg._loaded_mtimes = current


_refresh_stale_backend_modules()


# --- PAGE CONFIGURATION ---
_initial_url_char = None
try:
    _initial_url_char = st.query_params.get("character") or st.query_params.get("profile")
except Exception:
    _initial_url_char = None

st.set_page_config(
    page_title=f"{_initial_url_char} | The Fractured Overlay" if _initial_url_char else "Choose Your Character | The Fractured Overlay",
    page_icon="🗡️",
    layout="wide",
)

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

# --- INITIALIZE RELATIONAL DATABASE & AUTO-SEED IF EMPTY ---
try:
    ensure_database_initialized(BASE_DIR)
except Exception as init_err:
    print(f"[DB INIT WARNING] Relational engine deferred: {init_err}", flush=True)


def get_current_session_id() -> str:
    """
    Resolves the active campaign session ID for Streamlit and CLI environments.
    1. Checks URL query parameters ('session_id' or 'session').
    2. Checks st.session_state['session_id'].
    3. Falls back to 'default' (ensures 100% CLI test compatibility).
    """
    try:
        q_sid = st.query_params.get("session_id") or st.query_params.get("session")
        if q_sid and str(q_sid).strip():
            sid = str(q_sid).strip()
            st.session_state["session_id"] = sid
            return sid

        if hasattr(st, "session_state") and "session_id" in st.session_state:
            s_val = str(st.session_state["session_id"]).strip()
            if s_val:
                return s_val
    except Exception:
        pass

    return "default"


# --- SAVE/LOAD & PROFILE LOGIC ---
def load_world():
    sid = get_current_session_id()
    return adapter_load_world(base_dir=BASE_DIR, session_id=sid)


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

    # Ensure Glenny profile folder is seeded if not present
    if "Glenny" not in profiles:
        try:
            glenny_sheet = cg.generate_starting_character("Glenny")
            glenny_welcome = [{
                "role": "system",
                "content": cg.build_system_initialization_welcome_message(glenny_sheet),
                "image_path": None
            }]
            cg.save_character_to_folder(BASE_DIR, glenny_sheet, glenny_welcome)
            profiles.append("Glenny")
        except Exception:
            pass

    return sorted(list(set(profiles)))


def activate_character_session(profile_name: str, update_query_params: bool = True) -> bool:
    """Loads the specified character profile into session_state and syncs query params using database adapters."""
    resolved = cg.resolve_character_profile_name(BASE_DIR, profile_name) or profile_name
    clean_slug = sanitize_character_slug(resolved).lower()
    sid = get_current_session_id()
    if sid == "default":
        session_id = "default" if clean_slug in ("survivor", "banki") else f"session_{clean_slug}"
    else:
        session_id = sid

    # Clear ephemeral turn keys across switches
    for stale_key in ("pending_dev_command", "pending_fusion_components", "last_processed_audio_hash"):
        st.session_state.pop(stale_key, None)

    activated = adapter_activate_character_session(resolved, session_id=session_id, base_dir=BASE_DIR)
    if not activated or not activated.get("player"):
        return False

    st.session_state.player = activated["player"]
    st.session_state.messages = activated.get("messages", [])
    if "world_state" in activated and isinstance(activated["world_state"], dict) and activated["world_state"]:
        st.session_state.world_state = activated["world_state"]
    st.session_state.active_profile = resolved
    st.session_state.character_selected = True
    st.session_state.character_creation_mode = False

    if "master_state" in activated and activated["master_state"]:
        try:
            with db_transaction(session_id=session_id) as db_sess:
                MasterStateRepository.save_master_state(db_sess, activated["master_state"], session_id=session_id)
        except Exception:
            m_path = os.path.join(BASE_DIR, ".game_state", "secret_master_state.json")
            atomic_write_json(m_path, activated["master_state"])

    try:
        if hasattr(mechanics, "restore_companions_for_character"):
            mechanics.restore_companions_for_character(BASE_DIR, resolved, st.session_state.player)
    except Exception:
        pass

    if update_query_params:
        try:
            st.query_params["character"] = resolved
            if "mode" in st.query_params:
                del st.query_params["mode"]
        except Exception:
            pass
    return True


def load_game():
    active_prof = st.session_state.get("active_profile")
    if active_prof:
        char_data = cg.load_character_from_folder(BASE_DIR, active_prof)
        if char_data:
            return char_data
    return None


def save_game(player_state, messages, extra_meta=None, session_id=None):
    """
    Backward-compatible save_game adapter for app.py.
    Automatically scopes to active session_id without breaking any of the 71 call sites.
    """
    sid = session_id or get_current_session_id()
    if extra_meta is None:
        world_data = st.session_state.get("world_state", load_world())
        extra_meta = {"world_state": world_data}
    return adapter_save_game(
        player_state=player_state,
        messages=messages,
        extra_meta=extra_meta,
        session_id=sid,
        base_dir=BASE_DIR,
    )

# --- CHARACTER GENERATOR & CALIBRATION INTERFACE ---
def get_cg_chimera_choices():
    """Reads the Spliced Apex Chimera slot/bloodline/flaw widget state (falls back to defaults)."""
    raw = {k: st.session_state.get(f"chim_{k}") for k in cg.DEFAULT_CHIMERA_CHOICES}
    if not st.session_state.get("chim_flaw_2_enabled"):
        raw["flaw_2"] = None
    return cg.normalize_chimera_choices(raw)


def get_cg_race_obj():
    """Effective lineage for the wizard's current race selection (chimera-aware)."""
    return cg.resolve_racial_lineage(st.session_state.get("cg_race_key", "pure_human"), get_cg_chimera_choices())


def get_cg_physical():
    """Body stats entered in the wizard: {"age", "height_in", "weight_lbs"}."""
    d = mechanics.DEFAULT_PHYSICAL
    ft = st.session_state.get("cg_height_ft", d["height_in"] // 12)
    inch = st.session_state.get("cg_height_inch", d["height_in"] % 12)
    return {
        "age": int(st.session_state.get("cg_age", d["age"])),
        "height_in": int(ft) * 12 + int(inch),
        "weight_lbs": int(st.session_state.get("cg_weight", d["weight_lbs"])),
    }


def render_sidebar_calibration_preview():
    char_name = st.session_state.get("cg_name", "Survivor")
    cg_gender_val = mechanics.normalize_gender(st.session_state.get("cg_gender", "Male"))
    st.subheader(f"Avatar: {char_name} ({cg_gender_val})")
    
    prev_race = get_cg_race_obj()
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
    prev_hp = cg.compute_starting_max_hp(prev_race, prev_class, prev_stats, get_cg_physical())
    
    class_def_w = cg.CLASS_WEAPONS.get(st.session_state.get("cg_class_key", "pathless"), cg.CLASS_WEAPONS["pathless"])
    main_w = st.session_state.get("cg_main_hand", class_def_w["main_hand"]) if st.session_state.get("cg_custom_weapons", False) else class_def_w["main_hand"]
    off_w = st.session_state.get("cg_off_hand", class_def_w["off_hand"]) if st.session_state.get("cg_custom_weapons", False) else class_def_w["off_hand"]
    
    mock_p = {
        "name": char_name,
        "gender": cg_gender_val,
        "level": 1,
        "hp": prev_hp,
        "max_hp": prev_hp,
        "col": 100,
        "class": prev_class["title"],
        "stats": prev_stats,
        "physical": get_cg_physical(),
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

    if hasattr(mechanics, "get_locked_avatar_visual_directive"):
        prev_lock = mechanics.get_locked_avatar_visual_directive(mock_p, base_dir=BASE_DIR)
        if prev_lock.get("is_locked") and prev_lock.get("resolved_path"):
            st.image(prev_lock["resolved_path"], use_container_width=True)
            st.caption("🔒 **Locked Avatar:** Base appearance fixed; alters only by Equipped Gear.")
    
    st.progress(1.0, text=f"HP: {prev_hp} / {prev_hp}")
    st.progress(0.0, text="XP: 0 / 1000")
    if hasattr(mechanics, "get_combat_resource_display"):
        mock_res = mechanics.get_combat_resource_display(mock_p)
        st.progress(mock_res["percentage"], text=f"⚡ {mock_res['name']}: {mock_res['display']}")
    st.write(f"**Level:** 1 | **AC:** {mock_ac} 🛡️ | **Col:** 100 🪙")
    
    st.divider()
    with st.expander("🧬 Live Build Preview", expanded=True):
        st.write(f"**Sex / Gender:** {cg_gender_val}")
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
    if "cg_gender" not in st.session_state:
        st.session_state.cg_gender = "Male"
    if "cg_points" not in st.session_state:
        st.session_state.cg_points = {"STR": 0, "DEX": 0, "CON": 0, "INT": 0, "WIS": 0, "CHA": 0}
    if "cg_lifestyle_key" not in st.session_state:
        st.session_state.cg_lifestyle_key = "desk_bound"
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
        
        id_c1, id_c2 = st.columns([3, 2])
        with id_c1:
            st.session_state.cg_name = st.text_input(
                "Avatar Callsign / Real Name:",
                value=st.session_state.cg_name,
                key="cg_name_input_field",
                placeholder="e.g. Banki, Vance, Kaito, Marcus..."
            ).strip()
        with id_c2:
            st.radio(
                "Sex / Gender:",
                options=["Male", "Female"],
                horizontal=True,
                key="cg_gender"
            )

        # Physical profile: Age, Height, Weight
        st.markdown("#### 🧍 Physical Profile")
        d_phys = mechanics.DEFAULT_PHYSICAL
        b_c1, b_c2, b_c3, b_c4 = st.columns(4)
        b_c1.number_input("Age (years)", min_value=13, max_value=500, value=d_phys["age"], step=1, key="cg_age")
        b_c2.number_input("Height (ft)", min_value=2, max_value=12, value=d_phys["height_in"] // 12, step=1, key="cg_height_ft")
        b_c3.number_input("Height (in)", min_value=0, max_value=11, value=d_phys["height_in"] % 12, step=1, key="cg_height_inch")
        b_c4.number_input("Weight (lbs)", min_value=30, max_value=3000, value=d_phys["weight_lbs"], step=5, key="cg_weight")
        cg_profile = mechanics.get_physical_profile({"gender": st.session_state.get("cg_gender", "Male"), "physical": get_cg_physical()})
        st.info(f"**{cg_profile['summary']}**")
        if cg_profile["effects"]:
            st.caption("Body modifiers: " + " · ".join(cg_profile["effects"]))
        else:
            st.caption("Body modifiers: none (Medium size, Average build, Prime age).")
        st.caption("Size from height: Small < 4'0\" · Medium 4'0\"–7'0\" · Large > 7'0\". Build from weight vs. height. Age: Youth < 20 · Prime 20–39 · Veteran 40–59 · Elder 60+.")
        
        total_allocated = sum(st.session_state.cg_points.values())
        pts_left = 20 - total_allocated
        
        # Budget Indicator
        if pts_left > 0:
            st.info(f"⚡ Calibration Pool Remaining: **{pts_left} / 20** points available.")
        elif pts_left == 0:
            st.success("✅ Calibration Pool: Exactly **20 / 20** points allocated! Ready for confirmation.")
        else:
            st.error(f"⚠️ Calibration Pool Overdrawn: **{total_allocated} / 20** points ({abs(pts_left)} too many)! Please reduce allocated points.")

        # Quick-Lifestyle Questionnaire Presets (26 Archetypes)
        num_lifestyles = len(cg.PRESET_LIFESTYLES)
        with st.expander(f"⚡ {num_lifestyles} Quick-Lifestyle Questionnaire Presets (Auto-Distribute 20 Points)", expanded=False):
            st.caption("Select any Pre-Integration Earth or Classic Fantasy archetype to auto-distribute your 20 calibration points and grant starting skill bonuses and innate feats:")
            preset_keys = list(cg.PRESET_LIFESTYLES.keys())
            cur_ls_key = st.session_state.get("cg_lifestyle_key", "desk_bound")
            cur_p_idx = preset_keys.index(cur_ls_key) if cur_ls_key in preset_keys else 0
            sel_p_key = st.selectbox(
                "Browse Lifestyle Archetype:",
                options=preset_keys,
                index=cur_p_idx,
                format_func=lambda k: cg.PRESET_LIFESTYLES[k]["title"],
                key="sel_lifestyle_preset"
            )
            p_data = cg.PRESET_LIFESTYLES[sel_p_key]
            st.info(f"**Archetype Summary:** {p_data['desc']}")
            p_pts = p_data["points"]
            st.caption(f"**Point Allocation:** STR +{p_pts['STR']} | DEX +{p_pts['DEX']} | CON +{p_pts['CON']} | INT +{p_pts['INT']} | WIS +{p_pts['WIS']} | CHA +{p_pts['CHA']}")
            
            # Thematic 1-1000 Skill Bonuses
            p_skills = p_data.get("skill_bonuses", {})
            if p_skills:
                skills_str = " | ".join([f"**{sk}** (+{b} Mastery)" for sk, b in p_skills.items()])
                st.caption(f"**Thematic Skill Bonuses:** {skills_str}")
                
            # Innate Starting Talent / Feat / Spell
            feat_name = p_data.get("starting_feat", "")
            feat_desc = p_data.get("feat_desc", "")
            if feat_name and feat_desc:
                st.caption(f"**Innate Starting Talent:** `{feat_name}` — *{feat_desc}*")
            elif feat_name:
                st.caption(f"**Innate Starting Talent:** `{feat_name}`")
            elif "innate_ability" in p_data:
                st.caption(f"**Innate Starting Talent:** {p_data['innate_ability']}")

            if st.button("⚡ Apply Selected Lifestyle Preset (20 Points)", use_container_width=True, key="btn_apply_preset_main"):
                st.session_state.cg_points = dict(p_pts)
                st.session_state.cg_lifestyle_key = sel_p_key
                st.rerun()

            st.markdown("---")
            st.caption("Or One-Click Popular Archetypes:")
            q_cols1 = st.columns(4)
            if q_cols1[0].button("🛋️ Desk Bound", use_container_width=True, key="preset_desk"):
                st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["desk_bound"]["points"])
                st.session_state.cg_lifestyle_key = "desk_bound"
                st.rerun()
            if q_cols1[1].button("🏃 Athletic", use_container_width=True, key="preset_athletic"):
                st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["athletic"]["points"])
                st.session_state.cg_lifestyle_key = "athletic"
                st.rerun()
            if q_cols1[2].button("🔨 Heavy Labor", use_container_width=True, key="preset_labor"):
                st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["heavy_labor"]["points"])
                st.session_state.cg_lifestyle_key = "heavy_labor"
                st.rerun()
            if q_cols1[3].button("🎖️ First Responder", use_container_width=True, key="preset_responder"):
                st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["first_responder"]["points"])
                st.session_state.cg_lifestyle_key = "first_responder"
                st.rerun()
                
            q_cols2 = st.columns(4)
            if q_cols2[0].button("📚 Academic Scholar", use_container_width=True, key="preset_scholar"):
                st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["academic_scholar"]["points"])
                st.session_state.cg_lifestyle_key = "academic_scholar"
                st.rerun()
            if q_cols2[1].button("🧘 Yoga Contortionist", use_container_width=True, key="preset_yoga"):
                st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["yoga_contortionist"]["points"])
                st.session_state.cg_lifestyle_key = "yoga_contortionist"
                st.rerun()
            if q_cols2[2].button("🎮 Esports Gamer", use_container_width=True, key="preset_esports"):
                st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["esports_gamer"]["points"])
                st.session_state.cg_lifestyle_key = "esports_gamer"
                st.rerun()
            if q_cols2[3].button("🌲 Homesteader", use_container_width=True, key="preset_homesteader"):
                st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["offgrid_homesteader"]["points"])
                st.session_state.cg_lifestyle_key = "offgrid_homesteader"
                st.rerun()

            st.caption("New Classic Fantasy Archetypes:")
            q_cols3 = st.columns(4)
            if q_cols3[0].button("🪓 Woodsman", use_container_width=True, key="preset_woodsman"):
                if "woodsman" in cg.PRESET_LIFESTYLES:
                    st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["woodsman"]["points"])
                    st.session_state.cg_lifestyle_key = "woodsman"
                    st.rerun()
            if q_cols3[1].button("🧘 Ascetic", use_container_width=True, key="preset_ascetic"):
                if "monastery_ascetic" in cg.PRESET_LIFESTYLES:
                    st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["monastery_ascetic"]["points"])
                    st.session_state.cg_lifestyle_key = "monastery_ascetic"
                    st.rerun()
            if q_cols3[2].button("🌿 Apothecary", use_container_width=True, key="preset_apothecary"):
                if "hearth_apothecary" in cg.PRESET_LIFESTYLES:
                    st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["hearth_apothecary"]["points"])
                    st.session_state.cg_lifestyle_key = "hearth_apothecary"
                    st.rerun()
            if q_cols3[3].button("⛏️ Delver", use_container_width=True, key="preset_delver"):
                if "dungeon_delver" in cg.PRESET_LIFESTYLES:
                    st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["dungeon_delver"]["points"])
                    st.session_state.cg_lifestyle_key = "dungeon_delver"
                    st.rerun()

            q_cols4 = st.columns(4)
            if q_cols4[0].button("⚔️ Gladiator", use_container_width=True, key="preset_gladiator"):
                if "arena_gladiator" in cg.PRESET_LIFESTYLES:
                    st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["arena_gladiator"]["points"])
                    st.session_state.cg_lifestyle_key = "arena_gladiator"
                    st.rerun()
            if q_cols4[1].button("👑 Emissary", use_container_width=True, key="preset_emissary"):
                if "courtier_emissary" in cg.PRESET_LIFESTYLES:
                    st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["courtier_emissary"]["points"])
                    st.session_state.cg_lifestyle_key = "courtier_emissary"
                    st.rerun()
            if q_cols4[2].button("🔥 Blacksmith", use_container_width=True, key="preset_blacksmith"):
                if "blacksmith_apprentice" in cg.PRESET_LIFESTYLES:
                    st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["blacksmith_apprentice"]["points"])
                    st.session_state.cg_lifestyle_key = "blacksmith_apprentice"
                    st.rerun()
            if q_cols4[3].button("📜 Scribe", use_container_width=True, key="preset_scribe"):
                if "archive_scribe" in cg.PRESET_LIFESTYLES:
                    st.session_state.cg_points = dict(cg.PRESET_LIFESTYLES["archive_scribe"]["points"])
                    st.session_state.cg_lifestyle_key = "archive_scribe"
                    st.rerun()

        st.divider()
        st.markdown("#### 🎛️ Point-Buy Attribute Steppers")
        st.caption("Baseline: 10 in all attributes. Allocate points to increase your starting score:")
        
        race_info = get_cg_race_obj()
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
            [f"Preset Earth Vocations ({len(cg.PRESET_BACKGROUNDS)} Archetypes)", "✍️ Custom Earth Life (Interactive Collaboration with Cardinal)"],
            horizontal=True,
            key="vocation_mode_radio"
        )
        
        if v_mode.startswith("Preset"):
            bg_keys = list(cg.PRESET_BACKGROUNDS.keys())
            bg_titles = [cg.PRESET_BACKGROUNDS[k]["title"] for k in bg_keys]
            
            cur_bg_idx = bg_keys.index(st.session_state.cg_bg_key) if st.session_state.cg_bg_key in bg_keys else 0
            sel_bg_title = st.selectbox(
                f"Choose Earth Profession ({len(cg.PRESET_BACKGROUNDS)} Options):",
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
        
        creation_lineages = cg.get_character_creation_lineages() if hasattr(cg, "get_character_creation_lineages") else cg.RACIAL_LINEAGES
        race_keys = list(creation_lineages.keys())
        race_display_labels = [f"[{creation_lineages[k].get('genre', 'Universal')}] {creation_lineages[k]['name']}" for k in race_keys]
        
        # Handle backward compatibility if session previously held a purged race
        if hasattr(cg, "LEGACY_RACE_FALLBACKS") and st.session_state.cg_race_key in cg.LEGACY_RACE_FALLBACKS:
            st.session_state.cg_race_key = cg.LEGACY_RACE_FALLBACKS[st.session_state.cg_race_key]
            
        cur_r_idx = race_keys.index(st.session_state.cg_race_key) if st.session_state.cg_race_key in race_keys else 0
        
        sel_race_label = st.selectbox(
            f"Select Lineage / Monstrous Race ({len(race_keys)} Playable Forms):",
            options=race_display_labels,
            index=cur_r_idx,
            key="sel_race_box"
        )
        selected_race_key = race_keys[race_display_labels.index(sel_race_label)]
        st.session_state.cg_race_key = selected_race_key

        # Hybrid concept art
        app_root = os.path.dirname(os.path.abspath(__file__))
        art_paths = [os.path.join(app_root, p) for p in cg.HYBRID_CONCEPT_ART.get(selected_race_key, [])]
        art_paths = [p for p in art_paths if os.path.exists(p)]
        if art_paths:
            art_cols = st.columns(len(art_paths))
            for a_col, a_path in zip(art_cols, art_paths):
                a_col.image(a_path)

        # Variant 3: Spliced Apex Chimera modular builder
        if selected_race_key == cg.CHIMERA_RACE_KEY:
            st.markdown("#### 🧪 Gene-Splice Builder")
            st.caption("Part A — choose Troll-Dominant or Thri-Kreen-Dominant expression for each of the 5 anatomical slots.")
            for slot_k, slot_d in cg.CHIMERA_PHYSICAL_SLOTS.items():
                st.radio(
                    slot_d["label"],
                    options=["troll", "kreen"],
                    format_func=lambda v, sd=slot_d: f"{'🟢 Troll' if v == 'troll' else '🟡 Thri-Kreen'}: {sd[v]['name']}",
                    index=["troll", "kreen"].index(cg.DEFAULT_CHIMERA_CHOICES[slot_k]),
                    horizontal=True,
                    key=f"chim_{slot_k}"
                )
                cur_v = st.session_state.get(f"chim_{slot_k}", cg.DEFAULT_CHIMERA_CHOICES[slot_k])
                st.caption(slot_d[cur_v]["ability"].split(":", 1)[1].strip())
            st.caption("Part B — choose one option from each Bloodline category.")
            for cat_k, cat_d in cg.CHIMERA_BLOODLINE_OPTIONS.items():
                opt_keys = list(cat_d["options"].keys())
                st.selectbox(
                    cat_d["label"],
                    options=opt_keys,
                    format_func=lambda v, cd=cat_d: cd["options"][v]["name"],
                    index=opt_keys.index(cg.DEFAULT_CHIMERA_CHOICES[cat_k]),
                    key=f"chim_{cat_k}"
                )
                cur_o = st.session_state.get(f"chim_{cat_k}", cg.DEFAULT_CHIMERA_CHOICES[cat_k])
                st.caption(cat_d["options"][cur_o]["ability"].split(":", 1)[1].strip())

            st.caption("Part C — choose a Biological Flaw (required). You may take a 2nd flaw for a reward.")
            flaw_keys = list(cg.CHIMERA_FLAWS.keys())
            st.selectbox(
                "Biological Flaw",
                options=flaw_keys,
                format_func=lambda v: cg.CHIMERA_FLAWS[v]["name"],
                index=flaw_keys.index(cg.DEFAULT_CHIMERA_CHOICES["flaw"]),
                key="chim_flaw"
            )
            cur_f = st.session_state.get("chim_flaw", cg.DEFAULT_CHIMERA_CHOICES["flaw"])
            st.caption(cg.CHIMERA_FLAWS[cur_f]["ability"].split(":", 1)[1].strip())

            if st.checkbox("⚠️ Take a 2nd Flaw for a reward", key="chim_flaw_2_enabled"):
                flaw2_keys = [k for k in flaw_keys if k != cur_f]
                st.selectbox(
                    "Second Flaw",
                    options=flaw2_keys,
                    format_func=lambda v: cg.CHIMERA_FLAWS[v]["name"],
                    key="chim_flaw_2"
                )
                cur_f2 = st.session_state.get("chim_flaw_2") or flaw2_keys[0]
                if cur_f2 in cg.CHIMERA_FLAWS:
                    st.caption(cg.CHIMERA_FLAWS[cur_f2]["ability"].split(":", 1)[1].strip())
                reward = st.radio(
                    "2nd Flaw Reward",
                    options=["stats", "feat"],
                    format_func=lambda v: "+1 to 3 stats of your choice" if v == "stats" else "1 extra Bloodline option you didn't pick",
                    horizontal=True,
                    key="chim_flaw_2_reward"
                )
                if reward == "stats":
                    st.multiselect(
                        "Choose 3 different stats to raise by +1",
                        options=cg.CHIMERA_STAT_KEYS,
                        max_selections=3,
                        key="chim_reward_stats"
                    )
                    n_sel = len(st.session_state.get("chim_reward_stats") or [])
                    if n_sel < 3:
                        st.warning(f"Select {3 - n_sel} more stat(s) to claim the full reward.")
                else:
                    cur_choices = get_cg_chimera_choices()
                    feat_opts = [f"{c}:{o}" for c, o in cg.get_unpicked_bloodline_options(cur_choices)]
                    st.selectbox(
                        "Extra Bloodline option",
                        options=feat_opts,
                        format_func=lambda v: f"[{cg.CHIMERA_BLOODLINE_OPTIONS[v.split(':')[0]]['label']}] {cg.CHIMERA_BLOODLINE_OPTIONS[v.split(':')[0]]['options'][v.split(':')[1]]['name']}",
                        key="chim_reward_feat"
                    )
                    rf = st.session_state.get("chim_reward_feat")
                    if rf and rf.split(":")[0] == "defense":
                        st.caption(cg.CHIMERA_REGEN_CAP_RULE.split(":", 1)[1].strip())

        race_obj = get_cg_race_obj()
        if race_obj.get("max_hp_bonus"):
            st.success(f"🩸 Lineage Max HP Bonus: +{race_obj['max_hp_bonus']} HP")
        
        st.info(f"**Lineage Lore:** {race_obj['desc']}")
        
        st.markdown("##### ⚖️ Racial Stat Modifiers:")
        m_cols = st.columns(6)
        for idx, s in enumerate(["STR", "DEX", "CON", "INT", "WIS", "CHA"]):
            m_val = race_obj["stat_mods"].get(s, 0)
            sign = f"+{m_val}" if m_val > 0 else (str(m_val) if m_val < 0 else "0")
            m_cols[idx].metric(label=s, value=sign)
            
        st.markdown("##### 🧬 Racial Abilities & Lineage Powers:")
        for ab in race_obj["racial_abilities"]:
            ab_det = mechanics.get_spell_or_power_details(ab) if hasattr(mechanics, "get_spell_or_power_details") else {"name": ab.split(":")[0], "category": "Lineage Power", "action_type": "Innate", "cost": "Innate", "range": "Self", "description": race_obj["desc"], "mechanics": ab}
            ab_icon = "⚠️" if "Flaw" in ab else "✨"
            with st.expander(f"{ab_icon} {ab_det['name']} — [{ab_det['category']}]", expanded=False):
                st.caption(f"⏱️ **Action:** {ab_det['action_type']} | 💧 **Cost:** {ab_det['cost']} | 📏 **Range:** {ab_det['range']}")
                st.markdown(f"**📖 Description:**\n{ab_det['description']}")
                st.markdown(f"**🎲 Game Mechanics:**\n{ab_det['mechanics']}")

    # --- TAB 4: CLASS DOCTRINE ---
    with tab4:
        st.markdown("### ⚔️ Stage 4: Combat Doctrine & Class Path")
        st.write("Choose your philosophical approach to surviving the death-game. Structured classes provide specialized tactical frameworks, while the Pathless walk an unconstrained anomaly path.")
        
        # Classic 10 Base Classes + Pact & Anomaly (Warlock, Pathless) + Psionic Masters (XPH & DSP) + Artificer
        classic_10_keys = [
            "fighter", "wizard", "rogue", "cleric", "ranger",
            "paladin", "druid", "bard", "barbarian", "monk"
        ]
        pact_anomaly_keys = ["warlock", "pathless"]
        psionic_keys = [
            "psion", "psychic_warrior", "soulknife", "wilder",
            "aegis", "vitalist", "tactician", "cryptic", "dread", "marksman"
        ]
        legacy_keys = ["engineer"]
        roster_order = classic_10_keys + pact_anomaly_keys + psionic_keys + legacy_keys
        class_keys = [k for k in roster_order if k in cg.CLASS_PATHS]

        # Legacy alias map for backward compatibility
        legacy_alias_map = {
            "warrior": "fighter",
            "vanguard": "fighter",
            "mage": "wizard",
            "aether_slinger": "wizard",
            "thief": "rogue",
            "infiltrator": "rogue",
            "wilderness_ranger": "ranger",
        }
        
        # Safe index resolution handling legacy keys in session state
        raw_saved_key = st.session_state.get("cg_class_key", "fighter")
        if hasattr(mechanics, "normalize_class_key"):
            resolved_key = mechanics.normalize_class_key(raw_saved_key)
        else:
            resolved_key = legacy_alias_map.get(raw_saved_key, raw_saved_key)
            
        if resolved_key not in class_keys:
            resolved_key = legacy_alias_map.get(raw_saved_key, raw_saved_key)
            
        if resolved_key in class_keys:
            cur_c_idx = class_keys.index(resolved_key)
        elif raw_saved_key in class_keys:
            cur_c_idx = class_keys.index(raw_saved_key)
        else:
            cur_c_idx = 0

        class_titles = [cg.CLASS_PATHS[k]["title"] for k in class_keys]
        
        sel_class_title = st.selectbox(
            "Select Combat Doctrine (Classic, Pact, or Psionic):",
            options=class_titles,
            index=cur_c_idx,
            key="sel_class_box"
        )
        selected_class_key = class_keys[class_titles.index(sel_class_title)]
        st.session_state.cg_class_key = selected_class_key
        class_obj = cg.CLASS_PATHS[selected_class_key]
        
        st.info(f"**Doctrine Summary:** {class_obj['description']}")
        
        # Display Core Stats & Scaling
        c_meta1, c_meta2, c_meta3, c_meta4 = st.columns(4)
        c_meta1.metric("Base HP", f"{class_obj.get('base_hp', 100)} HP", f"+{class_obj.get('hp_per_lvl', 25)}/lvl")
        
        res_info = class_obj.get("combat_resource", {})
        res_name = res_info.get("name", "Stamina")
        res_max = res_info.get("max", 100)
        res_type = res_info.get("type", "stamina").capitalize()
        c_meta2.metric("Combat Resource", res_name, f"Max {res_max} ({res_type})")
        
        native_armors = class_obj.get("native_armor", ["Cloth"])
        c_meta3.metric("Native Armor", ", ".join(native_armors))
        
        c_meta4.metric("Starting Tier", "Tier 1 (Base)", "Levels 1–9")

        favored_skills = class_obj.get("favored_skills", [])
        st.caption(f"🎯 **Favored Skill Affinities (+25% Mastery XP):** {', '.join(favored_skills)}")
        
        st.markdown("##### 🎖️ Fixed Iconic Duo (Level 1 Baseline Powers & Feats):")
        for cf in class_obj.get("starting_feats", []):
            cf_det = mechanics.get_spell_or_power_details(cf) if hasattr(mechanics, "get_spell_or_power_details") else {
                "name": cf, "category": "Class Power", "action_type": "Active", "cost": "Resource",
                "range": "Combat", "description": "", "mechanics": cf
            }
            with st.expander(f"🔹 {cf_det['name']} — [{cf_det.get('category', 'Class Power')}]", expanded=False):
                st.caption(f"⏱️ **Action:** {cf_det.get('action_type', 'Active')} | 💧 **Cost:** {cf_det.get('cost', 'Resource')} | 📏 **Range:** {cf_det.get('range', 'Combat')}")
                if cf_det.get("description"):
                    st.markdown("**📖 Description:**\n" + str(cf_det.get("description", "")))
                if cf_det.get("mechanics"):
                    st.markdown("**🎲 Game Mechanics:**\n" + str(cf_det.get("mechanics", "")))
            
        def_w = cg.CLASS_WEAPONS.get(selected_class_key, cg.CLASS_WEAPONS.get("pathless", {
            "main_hand": "Rusted Iron Sword", "off_hand": "None", "desc": "Standard survival blade"
        }))
        st.markdown("##### ⚔️ Starter Weapon Configuration:")
        st.info(f"**Default Combat Loadout:** ⚔️ **{def_w.get('main_hand', 'None')}** (Main) & 🛡️ **{def_w.get('off_hand', 'None')}** (Off) — *{def_w.get('desc', '')}*")
        st.caption("💡 *Note: You can retain these default weapons or configure custom weapon choices from the 14-weapon survival cache in Stage 5 (Relic & Gear).*")

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
            [f"Choose from {len(cg.PERSONAL_RELICS)} Pre-Integration Earth Relics", "✍️ Custom Personal Keepsake (Write-In Object)"],
            horizontal=True,
            key="relic_mode_radio"
        )
        
        if relic_mode.startswith("Choose"):
            relic_keys = list(cg.PERSONAL_RELICS.keys())
            relic_names = [cg.PERSONAL_RELICS[k]["name"] for k in relic_keys]
            cur_relic_idx = relic_keys.index(st.session_state.cg_relic_key) if st.session_state.cg_relic_key in relic_keys else 0
            
            sel_relic_name = st.selectbox(
                f"Choose Personal Relic ({len(cg.PERSONAL_RELICS)} Options):",
                options=relic_names,
                index=cur_relic_idx,
                key="sel_relic_box"
            )
            selected_relic_key = relic_keys[relic_names.index(sel_relic_name)]
            st.session_state.cg_relic_key = selected_relic_key
            st.session_state.cg_custom_relic_data = None
            relic_obj = cg.PERSONAL_RELICS[selected_relic_key]
            
            st.success(f"✨ **{relic_obj['name']}** [{relic_obj['rarity']} • {relic_obj.get('category', 'Relic')}]")
            st.caption(f"{relic_obj['desc']}")
            if "mechanics" in relic_obj:
                st.info(f"🎲 **Game Mechanics:** {relic_obj['mechanics']}")
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
        r_info = get_cg_race_obj()
        c_info = cg.CLASS_PATHS.get(st.session_state.cg_class_key, cg.CLASS_PATHS["pathless"])
        
        final_scores = {
            s: 10 + st.session_state.cg_points.get(s, 0) + r_info["stat_mods"].get(s, 0)
            for s in ["STR", "DEX", "CON", "INT", "WIS", "CHA"]
        }
        calc_hp = cg.compute_starting_max_hp(r_info, c_info, final_scores, get_cg_physical())
        
        st.markdown("### 📋 Final Calibration Review")
        cur_ls_key = st.session_state.get("cg_lifestyle_key", "desk_bound")
        ls_obj = cg.PRESET_LIFESTYLES.get(cur_ls_key, cg.PRESET_LIFESTYLES.get("desk_bound", {}))
        ls_title = ls_obj.get("title", "Sedentary")
        ls_feat = ls_obj.get("starting_feat", "None")

        rev_c1, rev_c2, rev_c3 = st.columns(3)
        rev_c1.metric("Callsign", f"{st.session_state.cg_name} ({st.session_state.get('cg_gender', 'Male')})")
        rev_c1.metric("Lineage", r_info["name"])
        rev_c2.metric("Doctrine", c_info["title"])
        rev_c2.metric("Starting HP", f"{calc_hp} HP")
        rev_c3.metric("Main Weapon", st.session_state.cg_main_hand)
        rev_c3.metric("Personal Relic", relic_obj["name"][:22] + "...")
        st.caption(f"**Lifestyle Archetype:** {ls_title} | **Innate Talent:** `{ls_feat}`")
        
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
                    custom_collaborated_data=st.session_state.get("cg_custom_collaborated"),
                    chimera_choices=get_cg_chimera_choices(),
                    physical=get_cg_physical(),
                    gender=st.session_state.get("cg_gender", "Male"),
                    start_tutorial=True,
                    lifestyle_key=st.session_state.get("cg_lifestyle_key", "desk_bound"),
                )
                
                opening_announcement = cg.build_system_initialization_welcome_message(new_avatar)

                
                st.session_state.player = new_avatar
                st.session_state.messages = [
                    {
                        "role": "system",
                        "content": opening_announcement,
                        "image_path": None
                    }
                ]
                st.session_state.active_profile = char_name
                st.session_state.character_selected = True
                # NOTE: don't assign st.session_state['active_profile_select'] here: that sidebar widget is
                # already drawn this run (StreamlitWidgetAlreadyInstantiatedError). The sidebar syncs the
                # dropdown to `active_profile` before rendering it on the rerun below.
                st.session_state.character_creation_mode = False
                try:
                    st.query_params["character"] = char_name
                    if "mode" in st.query_params:
                        del st.query_params["mode"]
                except Exception:
                    pass
                
                # Sync V2 master state (seeded with Cardinal Calibration Crucible Stage 1)
                m_state = mechanics.build_tutorial_master_state(new_avatar, stage=1)
                sid = get_current_session_id()
                try:
                    with db_transaction(session_id=sid) as db_sess:
                        MasterStateRepository.save_master_state(db_sess, m_state, session_id=sid)
                except Exception:
                    m_path = os.path.join(BASE_DIR, ".game_state", "secret_master_state.json")
                    atomic_write_json(m_path, m_state)
                        
                save_game(st.session_state.player, st.session_state.messages)
                st.balloons()
                st.success(f"Calibration Complete! Avatar **{char_name}** linked to the Cardinal System. Launching Cardinal Calibration Crucible (Stage 1/3)...")
                time.sleep(1.0)
                st.rerun()


def render_character_select_screen():
    """
    Renders the 'Choose Your Character' loading screen when no character query parameter is active.
    Choosing a character opens a new tab with that character's unique link (?character=<Name>).
    """
    import datetime

    # Ensure default profiles (Banki, Glenny) are seeded before listing
    get_available_profiles()
    manifests = cg.list_all_character_folders(BASE_DIR)

    st.markdown(
        """
        <div style="text-align:center; padding: 1.2rem 1rem 0.8rem 1rem; border: 1px solid rgba(0, 212, 255, 0.35); border-radius: 12px; background: linear-gradient(135deg, rgba(10, 18, 32, 0.92), rgba(20, 32, 58, 0.88)); margin-bottom: 1.5rem;">
            <div style="font-size: 0.85rem; letter-spacing: 0.25em; color: #00d4ff; text-transform: uppercase; font-weight: 700;">
                CARDINAL SYSTEM // NEURAL LINK LOBBY
            </div>
            <h1 style="margin: 0.3rem 0; font-size: 2.3rem;">🗡️ Choose Your Character</h1>
            <p style="margin: 0.2rem auto 0 auto; max-width: 720px; color: #b8c7e0; font-size: 0.98rem;">
                Select a registered Survivor Profile below to launch a new tab with a unique direct link for that character's profile and story, or calibrate a new Avatar.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    total_cards = len(manifests) + 1
    num_cols = min(3, max(2, total_cards))
    cols = st.columns(num_cols, gap="large")

    for idx, m in enumerate(manifests):
        col = cols[idx % num_cols]
        prof_name = m.get("name", "Survivor")
        slug = m.get("slug", cg.sanitize_character_slug(prof_name))
        level = m.get("level", 1)
        gender = m.get("gender", "Male")
        race = m.get("race", "Unknown")
        c_class = m.get("class", "Unknown")
        hp_cur = int(m.get("hp_cur", 100))
        hp_max = max(1, int(m.get("hp_max", 100)))
        col_coins = m.get("col", 0)
        location = m.get("location", "Sector 1")
        turns_logged = m.get("turns_logged", 0)
        unique_url = m.get("unique_url") or cg.build_character_unique_url(prof_name)
        last_saved_ts = m.get("last_saved", 0)
        last_saved_str = (
            datetime.datetime.fromtimestamp(last_saved_ts).strftime("%Y-%m-%d %H:%M")
            if last_saved_ts
            else "Ready"
        )

        # Resolve portrait path if available
        char_dir = cg.get_character_save_dir(BASE_DIR, prof_name)
        eq_avatar = os.path.join(char_dir, "avatar_equipped.png")
        folder_avatar = os.path.join(char_dir, "avatar.png")
        rel_avatar = m.get("avatar_image_path")
        abs_rel_avatar = (
            rel_avatar
            if (rel_avatar and os.path.isabs(rel_avatar))
            else (os.path.join(BASE_DIR, rel_avatar) if rel_avatar else None)
        )

        portrait_path = None
        if os.path.exists(eq_avatar):
            portrait_path = eq_avatar
        elif os.path.exists(folder_avatar):
            portrait_path = folder_avatar
        elif abs_rel_avatar and os.path.exists(abs_rel_avatar):
            portrait_path = abs_rel_avatar

        with col:
            with st.container(border=True):
                if portrait_path:
                    st.image(portrait_path, use_container_width=True)
                else:
                    st.markdown(
                        f"""
                        <div style="height: 220px; border-radius: 8px; background: radial-gradient(circle at 50% 35%, rgba(0, 212, 255, 0.22), rgba(13, 19, 33, 0.95)); border: 1px solid rgba(0, 212, 255, 0.28); display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 0.75rem;">
                            <div style="font-size: 3.6rem;">🗡️</div>
                            <div style="font-size: 1.15rem; font-weight: 700; color: #e2efff; margin-top: 0.35rem;">{prof_name}</div>
                            <div style="font-size: 0.8rem; color: #7fa6d6;">CARDINAL NEURAL AVATAR</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                lock_badge = " 🔒" if m.get("avatar_locked") else ""
                st.markdown(f"### 🛡️ {prof_name}{lock_badge}")
                st.caption(f"**Level {level}** • **{gender}** • *{race}*")
                st.write(f"**Doctrine:** {c_class}")

                hp_pct = max(0.0, min(1.0, hp_cur / hp_max))
                st.progress(hp_pct, text=f"HP: {hp_cur} / {hp_max}  |  🪙 {col_coins} Col")

                eq = m.get("equipped") or {}
                mh = eq.get("main_hand", "None")
                oh = eq.get("off_hand", "None")
                st.caption(f"⚔️ **Loadout:** {mh}" + (f" & {oh}" if oh and oh != "None" else ""))
                st.caption(f"📍 **Location:** {location}")
                st.caption(f"📜 **Story Log:** {turns_logged} entries • 🕒 Saved: {last_saved_str}")
                st.markdown(f"🔗 **Unique Link:** `{unique_url}`")

                st.link_button(
                    f"⚡ Choose {prof_name} (Open in New Tab ↗)",
                    url=unique_url,
                    type="primary",
                    use_container_width=True,
                )
                if st.button(
                    f"▶️ Load {prof_name} in This Tab",
                    key=f"btn_choose_same_tab_{slug}",
                    use_container_width=True,
                ):
                    activate_character_session(prof_name, update_query_params=True)
                    st.rerun()

    # Add 'Create New Character' card in the final slot
    create_col = cols[len(manifests) % num_cols]
    with create_col:
        with st.container(border=True):
            st.markdown(
                """
                <div style="height: 220px; border-radius: 8px; background: radial-gradient(circle at 50% 35%, rgba(168, 85, 247, 0.24), rgba(13, 19, 33, 0.95)); border: 1px dashed rgba(168, 85, 247, 0.45); display: flex; flex-direction: column; align-items: center; justify-content: center; margin-bottom: 0.75rem;">
                    <div style="font-size: 3.6rem;">🧬</div>
                    <div style="font-size: 1.15rem; font-weight: 700; color: #f3e8ff; margin-top: 0.35rem;">New Survivor Calibration</div>
                    <div style="font-size: 0.8rem; color: #c084fc;">5-STAGE CARDINAL CREATION CRUCIBLE</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("### ✨ Calibrate New Avatar")
            st.caption("**Level 1 → Level 3 Tutorial Crucible** • **Custom Lineage & Relic**")
            st.write(
                "Forge a brand-new Survivor with custom Sex/Gender, Physical Build, Genetic Lineage (including Spliced Apex Chimera), Class Doctrine, and Earth Relic, then launch into the 3-stage Tutorial Crucible."
            )
            st.markdown("🔗 **Unique Link:** `?mode=create`")
            st.link_button(
                "🧬 New Character (Open in New Tab ↗)",
                url="?mode=create",
                type="primary",
                use_container_width=True,
            )
            if st.button(
                "▶️ Calibrate New Character in This Tab",
                key="btn_create_char_same_tab",
                use_container_width=True,
            ):
                st.session_state.character_creation_mode = True
                try:
                    st.query_params["mode"] = "create"
                except Exception:
                    pass
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
        match = re.search(r'(?:^|\r?\n)+(?:\*\*\[.*?SubAgent Mind\]\*\*|\*\*\[Ren\'s Tactical Logic\]\*\*)', content)
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
    if hasattr(mechanics, "get_max_unit_strain"):
        return mechanics.get_max_unit_strain(player_state)
    con = player_state.get("stats", {}).get("CON", 10)
    con_mod = (con - 10) // 2
    level = player_state.get("level", 1)
    return max(1, con_mod + (level // 2))

def get_current_strain(player_state: dict) -> int:
    if hasattr(mechanics, "get_current_unit_strain"):
        return mechanics.get_current_unit_strain(player_state)
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
            if st.session_state.player["hp"] <= 0 and hasattr(mechanics, "trigger_zero_hp_crisis"):
                c_res = mechanics.trigger_zero_hp_crisis(st.session_state.player)
                st.toast(c_res.get("message", "0 HP Crisis! 10-Second Revival Window Active!"), icon="💔")
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
                
                cur_lvl = int(st.session_state.player.get("level", 1) or 1)
                max_cap = getattr(mechanics, "MAX_PLAYER_LEVEL", 100)
                req_xp = mechanics.calculate_player_next_level_xp(cur_lvl) if hasattr(mechanics, "calculate_player_next_level_xp") else (cur_lvl * 1000)
                while req_xp > 0 and st.session_state.player["xp"] >= req_xp and cur_lvl < max_cap:
                    st.session_state.player["xp"] -= req_xp
                    lvl_res = mechanics.apply_level_up(st.session_state.player)
                    cur_lvl = int(st.session_state.player["level"])
                    st.balloons()
                    st.success(f"🎉 **LEVEL UP!** You are now Level {cur_lvl}! Max HP (+{lvl_res.get('hp_gain', 25)}) and +2 Free Attribute Points awarded!")
                    req_xp = mechanics.calculate_player_next_level_xp(cur_lvl) if hasattr(mechanics, "calculate_player_next_level_xp") else (cur_lvl * 1000)
        except (ValueError, TypeError):
            pass
    
    inv_add = state_updates.get("inventory_add") or []
    if isinstance(inv_add, list):
        for item in inv_add:
            if (isinstance(item, dict) and "name" in item) or (isinstance(item, str) and item.strip()):
                enriched_item = mechanics.enrich_item_dict(item, inventory=st.session_state.player.get("inventory", []))
                st.session_state.player["inventory"].append(enriched_item)
                st.toast(f"📦 Acquired: {enriched_item['name']}!", icon="🎁")
                
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

    # Apply equipment slot updates from schema (and ensure newly equipped items are in inventory)
    equip_map = {}
    if isinstance(state_updates.get("equip"), dict):
        equip_map.update(state_updates["equip"])
    for slot_key in ("main_hand", "off_hand", "lower_main_hand", "lower_off_hand", "head", "chest", "accessory"):
        val = state_updates.get(f"equip_{slot_key}")
        if val and isinstance(val, str) and val.strip():
            equip_map[slot_key] = val.strip()
    if equip_map:
        valid_eq_slots = set(mechanics.get_character_equipment_slots(st.session_state.player).keys()) | {
            "main_hand", "off_hand", "lower_main_hand", "lower_off_hand", "head", "chest", "accessory"
        }
        inv_list = st.session_state.player.setdefault("inventory", [])
        existing_names_low = {
            (it.get("name", "") if isinstance(it, dict) else str(it)).strip().lower()
            for it in inv_list
        }
        for slot_key, item_name in equip_map.items():
            if slot_key in valid_eq_slots and item_name:
                if (
                    item_name.strip().lower() not in ("none", "")
                    and not mechanics.is_two_handed_grip_marker(item_name)
                    and item_name.strip().lower() not in existing_names_low
                ):
                    enriched_eq = mechanics.enrich_item_dict({"name": item_name, "slot": slot_key}, inventory=inv_list)
                    inv_list.append(enriched_eq)
                    existing_names_low.add(item_name.strip().lower())
                    st.toast(f"⚔️ Equipped & Added to Inventory: {enriched_eq['name']}!", icon="🛡️")
                mechanics.equip_item_to_slot(st.session_state.player, item_name, slot_key)

    # Check if an Ability Fusion was initiated by the player this turn
    pending_fusion = st.session_state.pop("pending_fusion_components", None)
    consumed_this_turn_lows = set()
    forged_fusion_lows = set()

    if pending_fusion and isinstance(pending_fusion, (list, tuple)) and len(pending_fusion) >= 2:
        comp_a, comp_b = str(pending_fusion[0]).strip(), str(pending_fusion[1]).strip()
        consumed_this_turn_lows = {comp_a.lower(), comp_b.lower()}

        # Try to extract custom fused name & description proposed by the GM in spells_add, feats_add, or skill_updates
        custom_fused_name = None
        custom_fused_desc = None

        for k_check in ("spells_add", "feats_add"):
            for cand in (state_updates.get(k_check) or []):
                cand_str = cand.get("name", "") if isinstance(cand, dict) else str(cand)
                cand_clean = cand_str.replace("[Fusion]", "").strip(" []")
                if cand_clean and cand_clean.lower() not in consumed_this_turn_lows:
                    if ":" in cand_clean:
                        h_part, d_part = cand_clean.split(":", 1)
                        custom_fused_name = h_part.strip()
                        custom_fused_desc = d_part.strip()
                    else:
                        custom_fused_name = cand_clean
                    break
            if custom_fused_name:
                break

        for su in (state_updates.get("skill_updates") or []):
            if isinstance(su, dict) and "name" in su:
                su_name = str(su["name"]).strip()
                su_clean = su_name.replace("[Fusion]", "").strip(" []")
                if su_clean and su_clean.lower() not in consumed_this_turn_lows:
                    if not custom_fused_name:
                        custom_fused_name = su_clean
                    if su.get("description") and not custom_fused_desc:
                        custom_fused_desc = str(su["description"]).strip()

        f_res = mechanics.fuse_abilities(
            st.session_state.player,
            comp_a,
            comp_b,
            custom_fused_name=custom_fused_name,
            custom_desc=custom_fused_desc
        )
        if f_res.get("success"):
            f_key = f_res.get("fusion_skill_key", f"[Fusion] {f_res.get('fused_name', '')}")
            forged_fusion_lows = {
                f_res.get("fused_name", "").lower(),
                f_key.lower(),
                f"[{f_res.get('fused_name', '').lower()}]"
            }
            st.toast(f"🔮 Fused [{comp_a}] + [{comp_b}] ➔ {f_key}!", icon="✨")

    for k in ["spells_add", "feats_add", "racial_abilities_add"]:
        adds = state_updates.get(k) or []
        if isinstance(adds, list):
            target_list = k.replace("_add", "")
            for a in adds:
                a_str = str(a).strip()
                a_clean_low = a_str.replace("[Fusion]", "").strip(" []").split(":", 1)[0].strip().lower()
                if a_clean_low in consumed_this_turn_lows or a_clean_low in forged_fusion_lows or a_str.lower() in forged_fusion_lows:
                    continue
                if a not in st.session_state.player.get(target_list, []):
                    st.session_state.player.setdefault(target_list, []).append(a)
                    st.toast(f"🔮 Learned {target_list[:-1].capitalize()}: {a}!")

    new_graft_added = False
    grafts_installed = state_updates.get("grafts_installed") or []
    if isinstance(grafts_installed, list):
        if "grafts" not in st.session_state.player:
            st.session_state.player["grafts"] = {}
        for g in grafts_installed:
            if isinstance(g, dict) and "slot" in g:
                slot = g["slot"].lower().replace(" ", "_")
                st.session_state.player["grafts"][slot] = g
                new_graft_added = True
                st.toast(f"🦾 Installed Graft ({slot.capitalize()}): {g.get('name', 'Graft')}!", icon="💉")

    grafts_update = state_updates.get("grafts_update")
    if grafts_update and isinstance(grafts_update, dict):
        if "grafts" not in st.session_state.player:
            st.session_state.player["grafts"] = {}
        for slot, g_data in grafts_update.items():
            st.session_state.player["grafts"][slot] = g_data
            new_graft_added = True
            g_name = g_data.get("name", str(g_data)) if isinstance(g_data, dict) else str(g_data)
            st.toast(f"🦾 Installed Graft ({slot.capitalize()}): {g_name}!", icon="💉")

    if new_graft_added and hasattr(mechanics, "sync_graft_containers"):
        mechanics.sync_graft_containers(st.session_state.player)
        gs = st.session_state.player.setdefault("graft_system", {})
        if not gs.get("post_op_sickness", {}).get("active"):
            gs["post_op_sickness"] = {
                "active": True,
                "hours_remaining": 24,
                "max_hp_penalty_pct": 20,
                "dash_disabled": True,
                "active_graft_con_dc": 13,
            }
            st.toast("⚠️ [Cellular Re-Knitting] Active (24h Post-Op Recovery Required)!", icon="🩹")
        mechanics.calculate_player_strain(st.session_state.player)

    skill_updates = state_updates.get("skill_updates") or []
    if isinstance(skill_updates, list):
        for su in skill_updates:
            if isinstance(su, dict) and "name" in su:
                name = str(su["name"]).strip()
                name_clean_low = name.replace("[Fusion]", "").strip(" []").lower()
                # Do not re-add base skills in the exact turn they were consumed by Ability Fusion
                if name.lower() in consumed_this_turn_lows or name_clean_low in consumed_this_turn_lows:
                    continue
                if name.lower() in forged_fusion_lows or name_clean_low in forged_fusion_lows:
                    continue
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
                    
            # 2. Persist updated companion state via PartyRepository
            comps = st.session_state.player.get("companions", {})
            if comps:
                sid = get_current_session_id()
                p_slug = st.session_state.player.get("slug") or sanitize_character_slug(st.session_state.player.get("name", "Survivor"))
                try:
                    with db_transaction(session_id=sid) as db_sess:
                        PartyRepository.save_party(
                            db_sess, comps, session_id=sid, mirror_disk=True, character_slug=p_slug, base_dir=BASE_DIR
                        )
                except Exception as e:
                    print(f"[COMPANION SYNC ERROR] {e}", flush=True)

# --- INITIALIZE SESSION STATE & URL CHARACTER ROUTING ---
get_available_profiles()

_url_char_param = None
_url_mode_param = None
try:
    _url_char_param = st.query_params.get("character") or st.query_params.get("profile")
    _url_mode_param = st.query_params.get("mode")
except Exception:
    pass

if _url_mode_param == "create" and not st.session_state.get("character_selected"):
    st.session_state.character_creation_mode = True

if _url_char_param:
    _resolved_url_prof = cg.resolve_character_profile_name(BASE_DIR, _url_char_param)
    if _resolved_url_prof:
        if (
            st.session_state.get("active_profile") != _resolved_url_prof
            or "player" not in st.session_state
            or not st.session_state.get("character_selected")
        ):
            activate_character_session(_resolved_url_prof, update_query_params=False)

# Show the "Choose Your Character" loading screen when no character is selected and not in creation mode
if not st.session_state.get("character_selected", False) and not st.session_state.get("character_creation_mode", False):
    render_character_select_screen()
    st.stop()

saved_data = None
if (
    "player" not in st.session_state
    or "messages" not in st.session_state
    or "world_state" not in st.session_state
):
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
        if "master_state" in saved_data and saved_data["master_state"]:
            sid = get_current_session_id()
            try:
                with db_transaction(session_id=sid) as db_sess:
                    MasterStateRepository.save_master_state(db_sess, saved_data["master_state"], session_id=sid)
            except Exception:
                m_path = os.path.join(BASE_DIR, ".game_state", "secret_master_state.json")
                atomic_write_json(m_path, saved_data["master_state"])
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

# Initialize Phase 1-13 Systems
if hasattr(mechanics, "ensure_multi_limb_equipment"):
    mechanics.ensure_multi_limb_equipment(p)
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
if hasattr(mechanics, "ensure_planetary_raid_system"):
    mechanics.ensure_planetary_raid_system(p)
if hasattr(mechanics, "ensure_death_and_legacy_system"):
    mechanics.ensure_death_and_legacy_system(p)
if hasattr(mechanics, "ensure_enclave_stewardship"):
    mechanics.ensure_enclave_stewardship(p)
if hasattr(mechanics, "ensure_player_guild_system"):
    mechanics.ensure_player_guild_system(p)
if hasattr(mechanics, "ensure_character_avatar_lock"):
    mechanics.ensure_character_avatar_lock(p)

if "messages" not in st.session_state:
    if saved_data:
        st.session_state.messages = saved_data["messages"]
    else:
        st.session_state.messages = [
            {
                "role": "system", 
                "content": cg.build_system_initialization_welcome_message(st.session_state.player),
                "image_path": None
            }
        ]

# --- SIDEBAR: HUD & INVENTORY ---
def render_game_hud():
    player = st.session_state.player
    if hasattr(mechanics, "ensure_multi_limb_equipment"):
        mechanics.ensure_multi_limb_equipment(player)
    st.subheader(player["name"])

    if hasattr(mechanics, "get_locked_avatar_visual_directive"):
        lock_info = mechanics.get_locked_avatar_visual_directive(player, base_dir=BASE_DIR)
        if lock_info.get("is_locked") and lock_info.get("resolved_path"):
            char_dir = cg.get_character_save_dir(BASE_DIR, player.get("name", "Survivor"))
            eq_avatar_path = os.path.join(char_dir, "avatar_equipped.png")
            eq_sig = json.dumps(player.get("equipped", {}), sort_keys=True) + "|" + json.dumps(player.get("grafts", {}), sort_keys=True)
            display_avatar_path = lock_info["resolved_path"]
            if lock_info.get("equipment_changed") and os.path.exists(eq_avatar_path) and player.get("avatar_equipped_signature") == eq_sig:
                display_avatar_path = eq_avatar_path

            st.image(display_avatar_path, use_container_width=True)
            if not lock_info.get("equipment_changed"):
                st.caption("🔒 **Avatar Locked** — Base portrait active (Alters only by Equipped Gear)")
            else:
                st.caption(f"🔒 **Avatar Locked** — Equipment delta: `{', '.join(lock_info['changed_slots'])}`")
                if player.get("avatar_equipped_signature") != eq_sig:
                    if st.button("🔄 Update Avatar for Equipped Gear", key="btn_sync_locked_avatar_eq", use_container_width=True):
                        with st.spinner("Updating locked avatar with equipped gear..."):
                            new_bytes, err = gm_engine.generate_equipment_altered_avatar(api_key, player, base_dir=BASE_DIR)
                            if new_bytes and not err:
                                with open(eq_avatar_path, "wb") as af:
                                    af.write(new_bytes)
                                player["avatar_equipped_signature"] = eq_sig
                                save_game(player, st.session_state.messages)
                                st.toast("Updated avatar for equipped gear!", icon="🛡️")
                                st.rerun()
                            elif err:
                                st.warning(err)
    
    hp_percent = max(0.0, min(1.0, player["hp"] / max(1, player["max_hp"])))
    st.progress(hp_percent, text=f"HP: {player['hp']} / {player['max_hp']}")

    # --- PHASE 11: 0 HP 10-SECOND SHATTER CRISIS & CORPSE CACHE RECOVERY ---
    death_sys = mechanics.ensure_death_and_legacy_system(player) if hasattr(mechanics, "ensure_death_and_legacy_system") else {}
    if player.get("hp", 100) <= 0 or death_sys.get("crisis_active", False):
        st.error("💔 **0 HP MORTAL CRISIS — 10.0s SHATTER WINDOW ACTIVE!**")
        st.caption("Your polygons are fracturing! Trigger an immediate rescue or execute Legacy Reset:")
        cr_c1, cr_c2 = st.columns(2)
        with cr_c1:
            if st.button("🛡️ Companion Save", key="btn_crisis_comp_save", use_container_width=True, help="Requires active companion with Affinity >= 40"):
                res = mechanics.resolve_revival_window(player, method="companion_save")
                if res.get("success"):
                    save_game(player, st.session_state.messages)
                    st.toast(res["message"], icon="🛡️")
                    st.rerun()
                else:
                    st.warning(res.get("message", "No eligible companion."))
            if st.button("✨ Revival Stone", key="btn_crisis_stone", use_container_width=True, help="Consume Divine Stone of Returning Soul"):
                res = mechanics.resolve_revival_window(player, method="revival_stone")
                if res.get("success"):
                    save_game(player, st.session_state.messages)
                    st.toast(res["message"], icon="✨")
                    st.rerun()
                else:
                    st.warning(res.get("message", "No Revival Stone in inventory."))
        with cr_c2:
            if st.button("💎 Emergency Crystal", key="btn_crisis_crystal", use_container_width=True, help="Fails if inside Crimson Anti-Crystal room!"):
                res = mechanics.resolve_revival_window(player, method="emergency_crystal")
                if res.get("success"):
                    save_game(player, st.session_state.messages)
                    st.toast(res["message"], icon="💎")
                    st.rerun()
                else:
                    st.error(res.get("message", "Crystal jammed!"))
            if st.button("🪦 Legacy Reset", key="btn_crisis_legacy", use_container_width=True, help="Enshrine on Monument of Life & awaken Next-Gen Survivor"):
                res = mechanics.execute_legacy_reset(player)
                save_game(player, st.session_state.messages)
                st.toast(res["message"], icon="🪦")
                st.rerun()

    unrecovered_caches = [c for c in death_sys.get("corpse_caches", []) if not c.get("recovered", False)]
    if unrecovered_caches:
        latest_c = unrecovered_caches[-1]
        st.warning(f"⚱️ **Corpse Cache Active:** `{latest_c['fallen_name']}`'s gear & `{latest_c['col']} Col` rest on Floor {latest_c['floor']} ({latest_c['raid_id']}).")
        if st.button(f"⚱️ Reclaim {latest_c['fallen_name']}'s Corpse Cache", key="btn_recover_corpse_hud", use_container_width=True):
            rec_res = mechanics.recover_corpse_cache(player, latest_c["cache_id"])
            if rec_res.get("success"):
                save_game(player, st.session_state.messages)
                st.toast(rec_res["message"], icon="⚱️")
                st.rerun()

    
    cur_lvl = int(player.get("level", 1) or 1)
    max_lvl = getattr(mechanics, "MAX_PLAYER_LEVEL", 100)
    xp_max = mechanics.calculate_player_next_level_xp(cur_lvl) if hasattr(mechanics, "calculate_player_next_level_xp") else (cur_lvl * 1000)
    xp_current = player.get("xp", 0)
    if cur_lvl >= max_lvl or xp_max <= 0:
        st.progress(1.0, text=f"XP: Max Level {max_lvl} Reached! (Transcendent)")
    else:
        xp_percent = max(0.0, min(1.0, xp_current / xp_max))
        st.progress(xp_percent, text=f"XP: {xp_current} / {xp_max}")
    
    calc_ac_val = mechanics.calculate_ac(player) if hasattr(mechanics, "calculate_ac") else 10
    tier_info = mechanics.get_class_tier_name(cur_lvl) if hasattr(mechanics, "get_class_tier_name") else f"Level {cur_lvl}"
    st.write(f"**Level:** {cur_lvl}/{max_lvl} ({tier_info}) | **AC:** {calc_ac_val} 🛡️ | **Col:** {player.get('col', 0)} 🪙")
    
    st.divider()
    

    with st.expander("🧬 Character Build", expanded=False):
        cursor_data = mechanics.get_cursor_status(player) if hasattr(mechanics, "get_cursor_status") else {"badge": "🟢 Green"}
        hud_profile = mechanics.get_physical_profile(player)
        limb_prof = mechanics.get_limb_anatomy_profile(player) if hasattr(mechanics, "get_limb_anatomy_profile") else {"arm_count": 2, "hand_slots": {}, "tactical_rules": []}
        st.write(f"**Sex / Gender:** {hud_profile['gender']} ({hud_profile['pronouns']})")
        if player.get("polymorphed_form"):
            st.write(f"**Race:** {player['race']} *(Polymorphed: {player['polymorphed_form']})*")
        else:
            st.write(f"**Race:** {player['race']}")
        st.write(f"**Class:** {player['class']}")
        st.write(f"**SAO Status:** {cursor_data.get('badge', '🟢 Green')}")
        if isinstance(player.get("physical"), dict):
            st.write(f"**Body:** {hud_profile['summary']}")
        else:
            st.write("**Body:** not recorded (older save; treated as Medium / Average / Prime, no modifiers)")
        if hud_profile["effects"]:
            st.caption(" · ".join(hud_profile["effects"]))
        if limb_prof.get("arm_count", 2) > 2 or len(limb_prof.get("hand_slots", {})) > 2:
            st.markdown(f"**🦾 Multi-Limb Anatomy:** `{limb_prof['arm_count']} Functional Arms` (`{len(limb_prof.get('hand_slots', {}))} Hand Slots`)")
            for tr in limb_prof.get("tactical_rules", []):
                st.caption(f"• {tr}")
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

        char_eq_slots = mechanics.get_character_equipment_slots(player) if hasattr(mechanics, "get_character_equipment_slots") else {
            "head": "Head", "chest": "Chest / Torso Armor", "main_hand": "Main Hand", "off_hand": "Off-Hand", "accessory": "Accessory / Relic"
        }
        for slot, slot_label in char_eq_slots.items():
            item = player.get("equipped", {}).get(slot, "None")
            if item and item != "None":
                if hasattr(mechanics, "is_two_handed_grip_marker") and mechanics.is_two_handed_grip_marker(item):
                    parent_wep = mechanics.extract_two_handed_grip_weapon(item)
                    st.markdown(f"**{slot_label}:** 🔗 `{item}`")
                    st.caption(f"Two-Handed Grip paired with **{parent_wep}** (frees your other arm-pair for melee/shield/tools).")
                    st.divider()
                    continue
                grade = mechanics.get_item_grade(item) if hasattr(mechanics, "get_item_grade") else 1
                grade_badge = f"Grade {grade}"
                d = gear_dur.get(slot, {"cur": 100, "max": 100})
                cur_d = d.get("cur", 100)
                max_d = d.get("max", 100)
                state_info = mechanics.get_durability_state(cur_d, max_d) if hasattr(mechanics, "get_durability_state") else {"label": f"{cur_d}/{max_d}", "pct": cur_d / max_d if max_d > 0 else 1.0, "is_broken": cur_d <= 0, "is_dulled": cur_d < max_d * 0.25}
                item_det = mechanics.get_item_details(item, inventory=player.get("inventory", [])) if hasattr(mechanics, "get_item_details") else {"desc": "", "visual_appearance": ""}
                st.markdown(f"**{slot_label}:** {item}")
                st.caption(f"{grade_badge} | {state_info['label']}")
                if item_det.get("desc"):
                    st.caption(f"📖 *Lore & Mechanics:* {item_det['desc']}")
                if item_det.get("visual_appearance"):
                    st.caption(f"🎨 *Visual Appearance:* {item_det['visual_appearance']}")
                pct_val = max(0.0, min(1.0, float(state_info.get("pct", cur_d / max_d if max_d > 0 else 1.0))))
                st.progress(pct_val, text=f"{cur_d} / {max_d} Durability ({int(pct_val * 100)}%)")
                if state_info.get("is_broken"):
                    st.error("🛑 BROKEN: Weapon/Armor has fractured!")
                elif state_info.get("is_dulled"):
                    st.warning("🟠 DULLED/CRACKED: Imposing -2 penalty to checks!")
                if st.button(f"🔽 Unequip {slot_label}", key=f"btn_unequip_slot_{slot}", use_container_width=True):
                    mechanics.equip_item_to_slot(player, "None", slot)
                    save_game(player, st.session_state.messages)
                    st.toast(f"Unequipped {slot_label}.", icon="🔽")
                    st.rerun()
                st.divider()
            else:
                st.caption(f"- **{slot_label}:** None")

        total_dur_needed = sum(max(0, d.get("max", 100) - d.get("cur", 100)) for d in gear_dur.values())
        if total_dur_needed > 0:
            st.caption(f"Maintenance Required: **{total_dur_needed} pts** of wear | Cost: **{total_dur_needed} Col**")
            if st.button("🔨 Repair All Equipped Gear", key="btn_repair_all_gear_hud", use_container_width=True):
                for slot_k in list(char_eq_slots.keys()):
                    if slot_k in gear_dur and hasattr(mechanics, "repair_item"):
                        mechanics.repair_item(player, slot_k)
                save_game(player, st.session_state.messages)
                st.toast("🔨 All equipped gear repaired!", icon="✨")
                st.rerun()

        
    with st.expander("🦾 Magitech & Bio-Grafts", expanded=False):
        strain_info = mechanics.calculate_player_strain(player) if hasattr(mechanics, "calculate_player_strain") else {}
        cap = strain_info.get("max_unit_strain", get_strain_capacity(player))
        cur = strain_info.get("unit_strain", get_current_strain(player))
        bio_cur = strain_info.get("current_strain", 0)
        bio_max = strain_info.get("max_strain", 25)
        status_tier = strain_info.get("status_tier", "Optimal")
        asf_pct = strain_info.get("asf_percent", 0)
        spell_dc_pen = strain_info.get("spell_dc_penalty", 0)

        st.write(f"**Unit Strain:** `{cur} / {cap}` | **Bio-Tolerance Pool:** `{bio_cur} / {bio_max}` (`{status_tier}`)")
        if cur > cap or bio_cur > bio_max:
            st.error("⚠️ **OVER-STRAIN:** Exceeded physiological capacity! Subject to Metabolic Dissonance / Necrotic Rejection.")
            st.progress(1.0)
        else:
            st.progress(min(1.0, max(cur / max(1, cap), bio_cur / max(1, bio_max))))

        if asf_pct > 0:
            st.warning(f"🔮 **Golem Graft Interference:** `{asf_pct}%` Arcane Spell Failure (`-{spell_dc_pen}` Spell Save DC)")

        if strain_info.get("post_op_active"):
            hrs_rem = strain_info.get("post_op_hours_remaining", 24)
            st.warning(f"🩹 **[Cellular Re-Knitting] Active ({hrs_rem}h remaining):** `-20% Max HP`, `Dash Disabled`, `DC 13 CON Save` on active graft use.")
            if st.button("🛏️ Rest 8h in Safe-Zone (Advance Post-Op Recovery)", key="btn_advance_post_op_hud", use_container_width=True):
                rec_res = mechanics.advance_post_op_recovery(player, hours=8, in_safe_zone=True)
                save_game(player, st.session_state.messages)
                st.toast(rec_res.get("message", "Advanced recovery."), icon="🩹")
                st.rerun()

        if player.get("graft_system", {}).get("blood_debt_active"):
            debt_amt = player["graft_system"].get("blood_debt_col", 0)
            st.error(f"🩸 **Ripperdoc Promissory Blood-Debt:** `{debt_amt} Col` owed to Doc Mercer")

        limb_p = mechanics.get_limb_anatomy_profile(player) if hasattr(mechanics, "get_limb_anatomy_profile") else {}
        ganglia_note = " + 1 (Secondary Thoracic Ganglia)" if limb_p.get("extra_unit_strain_capacity", 0) > 0 else ""
        st.caption(f"Unit Cap = CON Mod + Floor(Level / 2){ganglia_note} • Bio-Pool = (CON × 2) + (Level × 3). 1 Graft per slot.")
        
        grafts = player.get("grafts", {})
        graft_slot_map = mechanics.get_character_graft_slots(player) if hasattr(mechanics, "get_character_graft_slots") else {
            "head": "Head", "torso": "Torso", "left_arm": "Left Arm", "right_arm": "Right Arm", "legs": "Legs", "spine": "Spine / Internal"
        }
        for s_key, s_label in graft_slot_map.items():
            g_val = grafts.get(s_key)
            if g_val:
                g_name = g_val.get("name", str(g_val)) if isinstance(g_val, dict) else str(g_val)
                g_elem = g_val.get("element", "none") if isinstance(g_val, dict) else "none"
                elem_badge = f" `[{g_elem.upper()}]`" if g_elem and g_elem != "none" else ""
                g_det = mechanics.get_item_details(g_val, inventory=player.get("inventory", [])) if hasattr(mechanics, "get_item_details") else {}
                st.write(f"- **{s_label}:** 🟢 `{g_name}`{elem_badge}")
                if g_det.get("desc"):
                    st.caption(f"  ↳ {g_det['desc']}")
            else:
                st.write(f"- **{s_label}:** *Empty*")

    with st.expander("📻 Pre-Integration Relics & Keepsakes", expanded=False):
        st.caption("Activate Earth relics for Short-Rest Sanity Stabilization, True-Sight Flash, Gas Detection, or 440Hz Vault Resonance.")
        inv_list = player.get("inventory", [])
        relic_keywords = ["smartphone", "polaroid", "zippo", "tuning fork", "cassette", "pocket watch", "compass", "keepsake", "relic"]
        player_relics = []
        for it in inv_list:
            it_name = it.get("name", str(it)) if isinstance(it, dict) else str(it)
            if any(rk in it_name.lower() for rk in relic_keywords) or (isinstance(it, dict) and it.get("type") == "relic"):
                player_relics.append(it_name)
        if not player_relics and player.get("relic"):
            r_obj = player["relic"]
            player_relics.append(r_obj.get("name", str(r_obj)) if isinstance(r_obj, dict) else str(r_obj))
        if player_relics:
            sel_relic = st.selectbox("Select Relic:", player_relics, key="hud_relic_select")
            sel_ctx = st.selectbox("Activation Mode:", ["short_rest", "inspect", "puzzle"], key="hud_relic_context")
            if st.button("✨ Activate Personal Relic", key="btn_activate_relic_hud", use_container_width=True):
                if hasattr(mechanics, "activate_personal_relic"):
                    r_out = mechanics.activate_personal_relic(player, sel_relic, context=sel_ctx)
                    save_game(player, st.session_state.messages)
                    st.toast(r_out.get("message", "Relic activated!"), icon="📻")
                    st.session_state.pending_dev_command = f"I use my [{sel_relic}] ({sel_ctx}): {r_out.get('message', '')}"
                    st.rerun()
        else:
            st.caption("*No Pre-Integration Relics detected in inventory.*")
        
    with st.expander("📈 Skills & Mastery (1–1000)", expanded=False):
        st.caption("Continuous 1–1000 proficiency tracking. Crossing thresholds (50, 100, 250, 500, 750, 1000) unlocks new Sword Skills and Passive Feats.")
        for s_name, s_data in player.get('skills', {}).items():
            if isinstance(s_data, dict):
                mastery = s_data.get('mastery', 1)
                desc = s_data.get('description', '')
                unlocked_ms = s_data.get('milestones_unlocked', [])
                is_fusion = s_data.get('is_fusion', False) or str(s_name).lower().startswith("[fusion]")
                comps = s_data.get('components', [])
            else:
                mastery = 1
                desc = str(s_data)
                unlocked_ms = []
                is_fusion = str(s_name).lower().startswith("[fusion]")
                comps = []
                
            tier_name, next_th = get_mastery_tier_info(mastery)
            fusion_badge = " ✨" if is_fusion else ""
            st.write(f"**{s_name}**{fusion_badge} `[{tier_name}]` ({mastery}/1000)")
            pct = min(1.0, mastery / float(next_th)) if next_th > 0 else 1.0
            st.progress(pct, text=f"{mastery}/{next_th} to next milestone")
            if comps:
                st.caption(f"🔗 *Combined from:* `{' + '.join(str(c) for c in comps)}`")
            if desc:
                st.caption(desc)
            if unlocked_ms:
                st.caption(f"🏅 *Milestones Unlocked:* {', '.join(str(m) for m in unlocked_ms)}")

        relearnable_in_skills = [
            r for r in (mechanics.get_relearnable_base_skills(player) if hasattr(mechanics, "get_relearnable_base_skills") else [])
            if r.get("was_fused")
        ]
        if relearnable_in_skills:
            st.divider()
            st.caption("🔄 **Consumed Base Skills Available to Relearn:**")
            rel_names_sm = [f"{r['name']} (fused into {r['fused_into']})" for r in relearnable_in_skills]
            sel_idx_sm = st.selectbox("Select Base Skill", range(len(relearnable_in_skills)), format_func=lambda i: rel_names_sm[i], key="relearn_skill_sm_select")
            if st.button("🔄 Relearn Selected Base Skill (Mastery 1/1000)", key="btn_relearn_sm", use_container_width=True):
                chosen_base = relearnable_in_skills[sel_idx_sm]["name"]
                r_res = mechanics.relearn_base_skill(player, chosen_base, starting_mastery=1)
                if r_res.get("success"):
                    save_game(player, st.session_state.messages)
                    st.toast(r_res.get("message", f"Relearned {chosen_base}!"), icon="🔄")
                    st.rerun()
                else:
                    st.warning(r_res.get("message", "Could not relearn skill."))

    all_spells_powers = mechanics.get_all_player_spells_and_powers(player) if hasattr(mechanics, "get_all_player_spells_and_powers") else []
    with st.expander(f"🔮 Spells & Powers ({len(all_spells_powers)})", expanded=False):
        st.caption("Click any Spell, Runic Hex, Class Power, or Lineage Ability below to expand its full Lore Description and Game Mechanics.")
        if hasattr(mechanics, "get_combat_resource_display"):
            res_disp = mechanics.get_combat_resource_display(player)
            st.progress(min(1.0, max(0.0, float(res_disp.get("percentage", 0.0)))), text=f"⚡ {res_disp['name']}: {res_disp['display']}")
        if hasattr(mechanics, "get_slotted_abilities") and hasattr(mechanics, "get_max_ability_slots"):
            slotted_now = mechanics.get_slotted_abilities(player)
            max_ab_slots = mechanics.get_max_ability_slots(player)
            st.caption(f"🧠 **Active Matrix Memory:** `{len(slotted_now)} / {max_ab_slots}` Slots Loaded")

        # Psionic Focus & Meditation Indicator
        c_k_norm = mechanics.normalize_class_key(player.get("class", "")) if hasattr(mechanics, "normalize_class_key") else str(player.get("class", "")).lower()
        is_psionic_player = (
            player.get("combat_resource", {}).get("type") in ["power_points", "customization_points"]
            or any("psionic" in str(sp.get("category", "")).lower() for sp in all_spells_powers)
            or player.get("psionic_focus") is not None
            or c_k_norm in [
                "psion", "psychic_warrior", "soulknife", "wilder", "aegis", "vitalist", "tactician", "cryptic", "dread", "marksman"
            ]
        )
        if is_psionic_player and hasattr(mechanics, "meditate_for_psionic_focus"):
            f_col_stat, f_col_btn = st.columns([1, 1])
            is_focused = bool(player.get("psionic_focus", False))
            with f_col_stat:
                focus_badge = "🌟 **ACTIVE**" if is_focused else "⭕ *Inactive*"
                st.markdown(f"🧠 **Psionic Focus:** {focus_badge}")
            with f_col_btn:
                if st.button("🧘 Meditate for Focus (DC 20)", key="btn_meditate_focus", use_container_width=True):
                    med_res = mechanics.meditate_for_psionic_focus(player)
                    save_game(player, st.session_state.messages)
                    if med_res.get("success"):
                        st.toast(med_res.get("message", "Psionic Focus achieved!"), icon="🧘")
                    else:
                        st.warning(med_res.get("message", "Meditation failed."))
                    st.rerun()

        if not all_spells_powers:
            st.info("No spells or special powers unlocked yet. Advance Skill Mastery to 100+, decipher Spell Slates, or fuse abilities!")
        else:
            for sp_idx, sp in enumerate(all_spells_powers):
                slot_badge = " 🟢 [Slotted]" if sp.get("is_slotted") else ""
                expander_label = f"{sp.get('icon', '🔮')} {sp['name']} — [{sp.get('source_group', 'Spell / Power')}]{slot_badge}"
                with st.expander(expander_label, expanded=False):
                    st.markdown(f"**Classification:** `{sp.get('category', 'Spell / Power')}`")
                    st.caption(f"⏱️ **Action:** {sp.get('action_type', 'Standard Action')} | 💧 **Cost:** {sp.get('cost', 'Standard')} | 📏 **Range:** {sp.get('range', 'Combat')}")
                    st.markdown("**📖 Description:**")
                    st.write(sp.get("description", ""))
                    st.markdown("**🎲 Game Mechanics:**")
                    st.info(sp.get("mechanics", ""))

                    if "polymorph self" in sp.get("name", "").lower() and hasattr(mechanics, "execute_pixie_polymorph"):
                        st.markdown("---")
                        st.markdown("🐾 **Pixie Polymorph Self Form Shifting (At Will):**")
                        poly_forms = list(getattr(mechanics, "PIXIE_POLYMORPH_FORMS", {}).keys())
                        poly_options = ["Pixie (True Form)"] + [mechanics.PIXIE_POLYMORPH_FORMS[k]["name"] for k in poly_forms]
                        cur_form = player.get("polymorphed_form", "Pixie (True Form)")
                        cur_idx = poly_options.index(cur_form) if cur_form in poly_options else 0
                        selected_form = st.selectbox("Select Assumed Form", poly_options, index=cur_idx, key=f"poly_select_{sp_idx}")
                        
                        p_b1, p_b2 = st.columns(2)
                        with p_b1:
                            if st.button("🔄 Shift Form", key=f"btn_shift_poly_{sp_idx}", use_container_width=True):
                                form_key = "revert" if "pixie" in selected_form.lower() else selected_form.lower().replace(" ", "_")
                                poly_res = mechanics.execute_pixie_polymorph(player, form_key)
                                save_game(player, st.session_state.messages)
                                st.toast(poly_res.get("message", "Form shifted!"), icon="🐾")
                                st.rerun()
                        with p_b2:
                            if player.get("polymorphed_form"):
                                if st.button("↩️ Revert to Pixie", key=f"btn_revert_poly_{sp_idx}", use_container_width=True):
                                    rev_res = mechanics.execute_pixie_polymorph(player, "revert")
                                    save_game(player, st.session_state.messages)
                                    st.toast(rev_res.get("message", "Reverted!"), icon="🧚")
                                    st.rerun()
                        
                        if player.get("polymorphed_form"):
                            st.success(f"🐾 **Active Form:** {player['polymorphed_form']} — {player.get('polymorph_data', {}).get('size', 'Medium')} | Stats: {player.get('polymorph_data', {}).get('stat_overrides', {})} | Natural Armor: +{player.get('polymorph_data', {}).get('natural_armor', 0)}")

                    if "pixie dust" in sp.get("name", "").lower() and hasattr(mechanics, "apply_pixie_dust_effect"):
                        st.markdown("---")
                        st.markdown("✨ **Scatter Pixie Dust (Sleep / Memory Loss / Confusion):**")
                        dust_mode = st.radio("Dust Effect Mode", ["Sleep (DC 15)", "Memory Loss (DC 15)", "Confusion (DC 15)"], horizontal=True, key=f"dust_mode_{sp_idx}")
                        if st.button("✨ Scatter Dust on Hostile", key=f"btn_dust_{sp_idx}", use_container_width=True):
                            clean_mode = "sleep" if "sleep" in dust_mode.lower() else ("memory_loss" if "memory" in dust_mode.lower() else "confusion")
                            st.session_state.pending_dev_command = f"I scatter [Pixie Dust] ({dust_mode}) in a 15-ft burst! Target must roll DC 15 Will save vs {clean_mode} or suffer full effect."
                            st.rerun()

                    if "eldritch blast" in sp.get("name", "").lower() and hasattr(mechanics, "execute_eldritch_blast"):
                        st.markdown("---")
                        st.markdown("⚡ **Eldritch Blast Modulation (D&D 3.5 Shapes & Essences):**")
                        eb_col_shape, eb_col_ess = st.columns(2)
                        
                        shapes_dict = getattr(mechanics, "WARLOCK_BLAST_SHAPES", {})
                        shape_keys = list(shapes_dict.keys())
                        shape_labels = [f"{shapes_dict[k]['name']} [{shapes_dict[k]['grade']}]" for k in shape_keys]
                        with eb_col_shape:
                            sel_shape_idx = st.selectbox("Blast Shape", range(len(shape_keys)), format_func=lambda i: shape_labels[i], key=f"eb_shape_{sp_idx}")
                            chosen_shape_key = shape_keys[sel_shape_idx] if shape_keys else "ray"
                        
                        essences_dict = getattr(mechanics, "WARLOCK_BLAST_ESSENCES", {})
                        essence_keys = list(essences_dict.keys())
                        essence_labels = [f"{essences_dict[k]['name']} [{essences_dict[k]['grade']}]" for k in essence_keys]
                        with eb_col_ess:
                            sel_ess_idx = st.selectbox("Eldritch Essence", range(len(essence_keys)), format_func=lambda i: essence_labels[i], key=f"eb_ess_{sp_idx}")
                            chosen_ess_key = essence_keys[sel_ess_idx] if essence_keys else "raw"
                        
                        eb_calc = mechanics.execute_eldritch_blast(player, shape=chosen_shape_key, essence=chosen_ess_key)
                        st.caption(f"💥 **Damage Output:** `{eb_calc['damage_dice']}` ({eb_calc['damage_type']}) | 🎯 **Range:** `{eb_calc['range_ft']} ft` | 🛡️ **Save DC:** `DC {eb_calc['save_dc']}` | ⚡ **Attack:** `{eb_calc['attack_mode']}`")
                        if eb_calc.get("con_cost", 0) > 0:
                            st.warning(f"⚠️ **Hellfire Sacrifice:** Costs {eb_calc['con_cost']} Constitution point upon invocation!")

                        if st.button("⚡ Fire Modulated Eldritch Blast", key=f"btn_fire_eb_{sp_idx}", use_container_width=True):
                            st.session_state.pending_dev_command = (
                                f"I invoke [Eldritch Blast] shaped as [{shapes_dict[chosen_shape_key]['name']}] "
                                f"and infused with [{essences_dict[chosen_ess_key]['name']}]! "
                                f"Strikes for {eb_calc['damage_dice']} {eb_calc['damage_type']} damage "
                                f"(Range: {eb_calc['range_ft']} ft, Mode: {eb_calc['attack_mode']}, DC {eb_calc['save_dc']})."
                            )
                            st.rerun()

                    # --- Psionic Power Point Augmentation Controls ---
                    is_psi_power = (
                        sp.get("is_psionic")
                        or "psionic" in sp.get("category", "").lower()
                        or sp.get("base_pp_cost", 0) > 0
                        or "power point" in str(sp.get("cost", "")).lower()
                    )
                    if is_psi_power and hasattr(mechanics, "validate_power_manifestation"):
                        st.markdown("---")
                        st.markdown("🧠 **Psionic Power Point Augmentation (D&D 3.5 ML Cap Rule):**")
                        base_cost = int(sp.get("base_pp_cost", 1) or 1)
                        ml = mechanics.calculate_manifester_level(player) if hasattr(mechanics, "calculate_manifester_level") else int(player.get("level", 1))
                        cr_info = player.get("combat_resource", {})
                        cur_pp = cr_info.get("current", 0) if cr_info.get("type") in ["power_points", "customization_points"] else 999
                        max_possible_aug = max(0, min(ml - base_cost, cur_pp - base_cost))
                        
                        aug_pp = 0
                        if max_possible_aug > 0:
                            aug_pp = st.slider(
                                "Augment Power (+PP)",
                                min_value=0,
                                max_value=max_possible_aug,
                                value=0,
                                key=f"psi_aug_slider_{sp_idx}",
                                help=f"Golden Rule of Psionics: Total PP spent ({base_cost} base + augment) cannot exceed Manifester Level ({ml})."
                            )
                        total_spend = base_cost + aug_pp
                        st.caption(f"⚡ **Total PP Cost:** `{total_spend} PP` | 🎯 **Manifester Level Cap:** `{ml} PP` | 💧 **Current Available PP:** `{cur_pp} PP`")
                        
                        if st.button(f"🧠 Manifest {sp['name']} ({total_spend} PP)", key=f"btn_manifest_psi_{sp_idx}", use_container_width=True):
                            val_check = mechanics.validate_power_manifestation(player, base_cost, aug_pp)
                            if not val_check.get("valid"):
                                st.warning(val_check.get("reason", "Manifestation invalid."))
                            else:
                                man_res = mechanics.manifest_psionic_power(player, sp["name"], base_cost, aug_pp)
                                save_game(player, st.session_state.messages)
                                st.session_state.pending_dev_command = (
                                    f"I manifest psionic power [{sp['name']}] augmented by +{aug_pp} PP "
                                    f"(Total: {total_spend} PP spent from reservoir). "
                                    f"Resolve its augmented damage, DC, and psychokinetic effects."
                                )
                                st.rerun()

                    sp_col1, sp_col2 = st.columns(2)
                    with sp_col1:
                        if sp.get("is_slotted"):
                            if st.button("🔓 Unslot from Matrix", key=f"btn_unslot_sp_{sp_idx}", use_container_width=True):
                                u_res = mechanics.unslot_ability(player, sp["name"])
                                save_game(player, st.session_state.messages)
                                st.toast(u_res.get("message", "Unslotted!"), icon="🧠")
                                st.rerun()
                        else:
                            if st.button("🧠 Slot into Matrix", key=f"btn_slot_sp_{sp_idx}", use_container_width=True):
                                s_res = mechanics.slot_ability(player, sp["name"])
                                if s_res.get("success"):
                                    save_game(player, st.session_state.messages)
                                    st.toast(s_res.get("message", "Slotted!"), icon="🧠")
                                    st.rerun()
                                else:
                                    st.warning(s_res.get("message", "Matrix memory full."))
                    with sp_col2:
                        if st.button(f"⚡ Cast / Invoke", key=f"btn_cast_sp_{sp_idx}", use_container_width=True):
                            st.session_state.pending_dev_command = f"I invoke [{sp['name']}] ({sp.get('category', 'Spell / Power')})! Resolve its game mechanics and narrative impact."
                            st.rerun()

    # --- Aegis Astral Suit Customization Workshop ---
    norm_cls = mechanics.normalize_class_key(player.get("class", "")) if hasattr(mechanics, "normalize_class_key") else str(player.get("class", "")).lower()
    if norm_cls == "aegis" or "astral_suit" in player or "aegis" in str(player.get("class", "")).lower():
        with st.expander("🛡️ Aegis Astral Suit Workshop", expanded=False):
            st.caption("Reconfigure your customizable Astral Suit using Dreamscarred Press Customization Points (CP).")
            cur_suit = player.get("astral_suit", {})
            suit_mode = cur_suit.get("form", "astral_armor")
            
            s_mode_col1, s_mode_col2 = st.columns([1, 1])
            with s_mode_col1:
                mode_choices = ["astral_skin", "astral_armor", "astral_juggernaut"]
                mode_labels = {
                    "astral_skin": "Astral Skin (Light: +2 Dex, +10ft Speed, Nimble)",
                    "astral_armor": "Astral Armor (Medium: +6 AC, DR 2/-)",
                    "astral_juggernaut": "Astral Juggernaut (Heavy: +10 AC, DR 5/-, Large Size)"
                }
                cur_m_idx = mode_choices.index(suit_mode) if suit_mode in mode_choices else 1
                new_mode = st.selectbox("Suit Form", mode_choices, index=cur_m_idx, format_func=lambda k: mode_labels.get(k, k), key="suit_form_select")
            
            with s_mode_col2:
                total_cp = mechanics.calculate_aegis_customization_points(player) if hasattr(mechanics, "calculate_aegis_customization_points") else 3
                active_custs = cur_suit.get("customizations", [])
                spent_cp = sum(mechanics.AEGIS_CUSTOMIZATIONS_CATALOG.get(c, {}).get("cost", 1) for c in active_custs) if hasattr(mechanics, "AEGIS_CUSTOMIZATIONS_CATALOG") else len(active_custs)
                st.metric("Customization Points", f"{spent_cp} / {total_cp} CP", f"{total_cp - spent_cp} Free CP")
            
            cust_catalog = getattr(mechanics, "AEGIS_CUSTOMIZATIONS_CATALOG", {})
            avail_cust_keys = list(cust_catalog.keys())
            
            selected_custs = st.multiselect(
                "Active Adaptations & Upgrades",
                options=avail_cust_keys,
                default=[c for c in active_custs if c in avail_cust_keys],
                format_func=lambda k: f"{cust_catalog[k]['name']} ({cust_catalog[k]['cost']} CP) — {cust_catalog[k]['desc']}",
                key="suit_cust_multiselect"
            )
            
            if st.button("🛠️ Reconfigure Astral Suit", key="btn_reconfigure_suit", use_container_width=True):
                cfg_res = mechanics.configure_astral_suit(player, new_mode, selected_custs)
                if cfg_res.get("success"):
                    save_game(player, st.session_state.messages)
                    st.toast(cfg_res.get("message", "Astral Suit updated!"), icon="🛡️")
                    st.rerun()
                else:
                    st.warning(cfg_res.get("message", "Configuration failed."))

    # --- The Collective Network Panel ---
    if norm_cls in ["vitalist", "tactician"] or "collective" in player or any(c in str(player.get("class", "")).lower() for c in ["vitalist", "tactician"]):
        with st.expander("🩸 The Collective Network (Mental Mesh)", expanded=False):
            st.caption("Telepathic party neural mesh for instant health redistribution and range-less buff forwarding.")
            coll = player.get("collective") or (mechanics.init_collective(player) if hasattr(mechanics, "init_collective") else {"members": [], "max_size": 5})
            members = coll.get("members", [])
            max_size = coll.get("max_size", 5)
            st.markdown(f"🕸️ **Connected Members ({len(members)} / {max_size}):** `{', '.join(members) if members else 'None'}`")
            
            # Invite active party companions
            party_dict = player.get("party", {})
            invite_candidates = [cname for cname in party_dict.keys() if cname not in members]
            if invite_candidates:
                c_inv_col1, c_inv_col2 = st.columns([2, 1])
                with c_inv_col1:
                    to_invite = st.selectbox("Invite Companion to Collective", invite_candidates, key="coll_invite_select")
                with c_inv_col2:
                    if st.button("🔗 Connect Mind", key="btn_coll_invite", use_container_width=True):
                        if hasattr(mechanics, "join_collective"):
                            inv_res = mechanics.join_collective(player, to_invite)
                            save_game(player, st.session_state.messages)
                            st.toast(inv_res.get("message", "Member joined!"), icon="🕸️")
                            st.rerun()
            
            # Transfer wounds controls
            st.markdown("---")
            st.markdown("💉 **Transfer Wounds / Rebalance Health:**")
            tw_col1, tw_col2, tw_col3 = st.columns(3)
            with tw_col1:
                tw_src = st.selectbox("Source", members or [player.get("name", "Player")], key="tw_src_sel")
            with tw_col2:
                tw_tgt = st.selectbox("Target", members or [player.get("name", "Player")], key="tw_tgt_sel")
            with tw_col3:
                tw_amt = st.number_input("HP Amount", min_value=1, max_value=100, value=10, key="tw_amt_input")
            
            if st.button("🩸 Transfer Wounds", key="btn_exec_tw", use_container_width=True):
                if hasattr(mechanics, "transfer_wounds"):
                    tw_res = mechanics.transfer_wounds(player, None, tw_amt)
                    save_game(player, st.session_state.messages)
                    st.session_state.pending_dev_command = f"I channel [Transfer Wounds] across the Collective, routing {tw_amt} HP from [{tw_src}] to [{tw_tgt}]!"
                    st.rerun()

    with st.expander("🔮 Ability Fusion Chamber", expanded=False):
        st.caption("Combine 2 skills or abilities to replace them with a unified **[Fusion] Skill** (Rule 10). Consumed Base Skills can be relearned at Novice (1/1000) if needed.")
        raw_pool = list(player.get("skills", {}).keys()) + player.get("spells", []) + player.get("feats", [])
        all_pool = []
        for item_p in raw_pool:
            s_p = str(item_p).strip()
            if s_p and s_p not in all_pool:
                all_pool.append(s_p)

        if len(all_pool) >= 2:
            f_col1, f_col2 = st.columns(2)
            ab1 = f_col1.selectbox("Component A", all_pool, key="fusion_select_a")
            ab2 = f_col2.selectbox("Component B", [x for x in all_pool if x != ab1] or all_pool, key="fusion_select_b")
            custom_f_name_input = st.text_input("Optional Custom [Fusion] Name", value="", placeholder="Leave blank for GM / Cardinal auto-naming", key="fusion_custom_name_input")
            fb_col1, fb_col2 = st.columns(2)
            with fb_col1:
                if st.button("✨ Fuse with GM Narrative", use_container_width=True):
                    st.session_state.pending_fusion_components = [ab1, ab2]
                    name_clause = f" named '[Fusion] {custom_f_name_input.strip()}'" if custom_f_name_input.strip() else ""
                    st.session_state.pending_dev_command = (
                        f"I invoke the Cardinal System Ability Fusion protocol to combine and replace [{ab1}] and [{ab2}] "
                        f"into a new synergistic [Fusion] Skill{name_clause}. Narrate the matrix convergence and register the fusion."
                    )
                    st.rerun()
            with fb_col2:
                if st.button("⚡ Instant Matrix Fuse", use_container_width=True):
                    f_res = mechanics.fuse_abilities(
                        player,
                        ab1,
                        ab2,
                        custom_fused_name=custom_f_name_input.strip() or None
                    )
                    if f_res.get("success"):
                        save_game(player, st.session_state.messages)
                        st.toast(f_res.get("log", "Fusion complete!"), icon="🔮")
                        st.rerun()
                    else:
                        st.warning(f_res.get("message", "Fusion failed."))
        else:
            st.caption("Need at least 2 skills or abilities to fuse.")

        st.divider()
        st.markdown("**🔄 Relearn Base Skill**")
        st.caption("Relearn a previously fused Base Skill (or a foundational Crucible discipline) starting at Novice (`1/1000`) while keeping your `[Fusion]` skill.")
        relearn_list = mechanics.get_relearnable_base_skills(player) if hasattr(mechanics, "get_relearnable_base_skills") else []
        if relearn_list:
            def _fmt_relearn(idx: int) -> str:
                entry = relearn_list[idx]
                if entry.get("was_fused"):
                    return f"🔄 {entry['name']} — [Previously fused into {entry.get('fused_into', '[Fusion] Skill')}]"
                return f"📘 {entry['name']} — [Foundational Base Skill]"

            sel_rel_idx = st.selectbox(
                "Base Skill to Relearn",
                range(len(relearn_list)),
                format_func=_fmt_relearn,
                key="fusion_chamber_relearn_select"
            )
            if st.button("🔄 Relearn Base Skill (1/1000)", key="btn_fusion_chamber_relearn", use_container_width=True):
                target_skill_name = relearn_list[sel_rel_idx]["name"]
                rel_res = mechanics.relearn_base_skill(player, target_skill_name, starting_mastery=1)
                if rel_res.get("success"):
                    save_game(player, st.session_state.messages)
                    st.toast(rel_res.get("message", f"Relearned {target_skill_name}!"), icon="🔄")
                    st.rerun()
                else:
                    st.warning(rel_res.get("message", "Could not relearn skill."))
        else:
            st.caption("All known base skills are currently active in your Skill Matrix.")

    with st.expander("🎒 Backpack Inventory", expanded=False):
        rarity_colors = {"Common": "⚪", "Uncommon": "🟢", "Rare": "🔵", "Epic": "🟣", "Legendary": "🟠", "Mythic": "🔴", "Unique": "✨"}
        if hasattr(mechanics, "enrich_inventory_list"):
            player["inventory"] = mechanics.enrich_inventory_list(player.get("inventory", []))
        char_eq_slots = mechanics.get_character_equipment_slots(player) if hasattr(mechanics, "get_character_equipment_slots") else {
            "head": "Head", "chest": "Chest / Torso Armor", "main_hand": "Main Hand", "off_hand": "Off-Hand", "accessory": "Accessory / Relic"
        }
        hand_slots = mechanics.get_character_hand_slots(player) if hasattr(mechanics, "get_character_hand_slots") else {
            "main_hand": "Main Hand", "off_hand": "Off-Hand"
        }
        eq_dict = player.setdefault("equipped", {})
        for idx, item in enumerate(player.get("inventory", [])):
            if isinstance(item, dict):
                icon = rarity_colors.get(item.get("rarity", "Common"), "⚪")
                i_name = item.get('name', 'Unknown')
                i_slot = item.get('slot', 'item')
                equipped_in_labels = [
                    char_eq_slots.get(sk, sk.replace("_", " ").title())
                    for sk, sv in eq_dict.items()
                    if sv == i_name
                ]
                eq_badge = f" • 🟢 *Equipped ({', '.join(equipped_in_labels)})*" if equipped_in_labels else ""
                st.write(f"{icon} **{i_name}** (x{item.get('qty', 1)}){eq_badge}")
                st.caption(f"Durability: {item.get('durability', 0)}/{item.get('max_durability', 0)} | {item.get('desc', '')}")
                if item.get("visual_appearance"):
                    st.caption(f"🎨 *Visual:* {item['visual_appearance']}")

                is_handheld = mechanics.is_handheld_equip_item(item, player.get("inventory", [])) if hasattr(mechanics, "is_handheld_equip_item") else (i_slot in ["main_hand", "off_hand"])
                is_2h = mechanics.is_two_handed_weapon(item, player.get("inventory", [])) if hasattr(mechanics, "is_two_handed_weapon") else False

                if is_handheld:
                    if is_2h:
                        pair_options = [("main_hand", "Upper Arms (2H Pair)" if "lower_main_hand" in hand_slots else "Both Hands (2H)")]
                        if "lower_main_hand" in hand_slots:
                            pair_options.append(("lower_main_hand", "Lower Arms (2H Pair)"))
                        if len(pair_options) > 1:
                            ec1, ec2 = st.columns([3, 2])
                            with ec1:
                                sel_pair = st.selectbox(
                                    "2H Arm Pair",
                                    options=[po[0] for po in pair_options],
                                    format_func=lambda k, _m=dict(pair_options): _m.get(k, k),
                                    key=f"sel_2h_pair_{idx}",
                                    label_visibility="collapsed",
                                )
                            with ec2:
                                if st.button("⚔️ Equip 2H", key=f"btn_equip_2h_{idx}", use_container_width=True):
                                    res = mechanics.equip_item_to_slot(player, i_name, sel_pair)
                                    save_game(player, st.session_state.messages)
                                    st.toast(res.get("message", f"Equipped {i_name}!"), icon="⚔️")
                                    st.rerun()
                        elif eq_dict.get("main_hand") != i_name:
                            if st.button("⚔️ Equip (2H Both Hands)", key=f"btn_equip_2h_single_{idx}"):
                                res = mechanics.equip_item_to_slot(player, i_name, "main_hand")
                                save_game(player, st.session_state.messages)
                                st.toast(res.get("message", f"Equipped {i_name}!"), icon="⚔️")
                                st.rerun()
                    else:
                        hand_keys = list(hand_slots.keys())
                        default_h_idx = 0
                        if i_slot in hand_keys:
                            default_h_idx = hand_keys.index(i_slot)
                        for hk_i, hk in enumerate(hand_keys):
                            if not eq_dict.get(hk) or eq_dict.get(hk) == "None":
                                default_h_idx = hk_i
                                break
                        ec1, ec2 = st.columns([3, 2])
                        with ec1:
                            sel_hand = st.selectbox(
                                "Hand Slot",
                                options=hand_keys,
                                index=default_h_idx,
                                format_func=lambda k, _hm=hand_slots, _eq=eq_dict: f"{_hm.get(k, k)} ({_eq.get(k, 'Empty') if _eq.get(k) not in (None, '', 'None') else 'Empty'})",
                                key=f"sel_hand_slot_{idx}",
                                label_visibility="collapsed",
                            )
                        with ec2:
                            if st.button("⚔️ Equip", key=f"btn_equip_hand_{idx}", use_container_width=True):
                                res = mechanics.equip_item_to_slot(player, i_name, sel_hand)
                                save_game(player, st.session_state.messages)
                                st.toast(res.get("message", f"Equipped {i_name}!"), icon="⚔️")
                                st.rerun()
                elif i_slot in char_eq_slots and eq_dict.get(i_slot) != i_name:
                    slot_lbl = char_eq_slots.get(i_slot, i_slot.replace('_', ' ').title())
                    if st.button(f"⚔️ Equip to {slot_lbl}", key=f"btn_equip_inv_{idx}_{i_slot}"):
                        res = mechanics.equip_item_to_slot(player, i_name, i_slot)
                        save_game(player, st.session_state.messages)
                        st.toast(res.get("message", f"Equipped {i_name} to {slot_lbl}!"), icon="⚔️")
                        st.rerun()
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
            seen_active_names = set()
            unique_active_comps = []
            for c in active_comps:
                if isinstance(c, dict):
                    cn = c.get("name", "Companion")
                    if cn not in seen_active_names:
                        seen_active_names.add(cn)
                        unique_active_comps.append(c)
            if not unique_active_comps:
                st.info("No active companions deployed in vanguard. Check Reserve or Recruit tabs!")
            else:
                for comp_idx, comp in enumerate(unique_active_comps):
                    if not isinstance(comp, dict):
                        continue
                    c_name = comp.get("name", "Companion")
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
                        if st.button(f"Share Rations (50 Col)", key=f"btn_share_meal_{c_name}_{comp_idx}"):
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
                        if st.button(f"⚡ Execute Dual-Tech: {comp.get('dual_tech_name', 'Combo')}", key=f"btn_exec_dt_{c_name}_{comp_idx}", use_container_width=True):
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
                            key=f"sb_stance_{c_name}_{comp_idx}"
                        )
                        if new_st != c_stance:
                            if hasattr(mechanics, "set_party_member_stance"):
                                mechanics.set_party_member_stance(player, c_name, new_st)
                                save_game(player, st.session_state.messages)
                                st.toast(f"{c_name}'s stance set to {stances[new_st].get('label', new_st)}!", icon="🎯")
                                st.rerun()
                        st.caption(f"↳ **Effect:** {stances.get(c_stance, {}).get('tactical_effect', '')}")

                    if st.button(f"Bench {c_name} (Send to Reserve)", key=f"btn_bench_{c_name}_{comp_idx}"):
                        comp["active"] = False
                        save_game(player, st.session_state.messages)
                        st.toast(f"{c_name} moved to Reserve.", icon="🛋️")
                        st.rerun()
                    st.divider()

        with tab_benched_party:
            comps = mechanics.ensure_party_system(player) if hasattr(mechanics, "ensure_party_system") else player.get("companions", {})
            benched = []
            if isinstance(comps, dict):
                for c in comps.values():
                    if isinstance(c, dict) and c.get("recruited", False) and not c.get("active", False):
                        benched.append(c)
            elif isinstance(comps, list):
                for c in comps:
                    if isinstance(c, dict) and c.get("recruited", False) and not c.get("active", False):
                        benched.append(c)

            if not benched:
                st.caption("No companions currently in Reserve.")
            else:
                for b_comp in benched:
                    b_name = b_comp.get("name", "Unknown")
                    st.markdown(f"**👤 {b_name}** `[Lv. {b_comp.get('level', 1)}]`")
                    st.caption(f"HP: {b_comp.get('hp', 30)}/{b_comp.get('max_hp', 30)}")
                    if len(active_comps) < 3:
                        if st.button(f"Activate {b_name} to Vanguard", key=f"btn_activate_{b_name}"):
                            b_comp["active"] = True
                            save_game(player, st.session_state.messages)
                            st.toast(f"{b_name} activated to Vanguard!", icon="⚔️")
                            st.rerun()
                    else:
                        st.caption("⚠️ Vanguard is full (Max 3 companions).")
                    st.divider()

        with tab_recruit_pool:
            comps = mechanics.ensure_party_system(player) if hasattr(mechanics, "ensure_party_system") else player.get("companions", {})
            all_known = mechanics.RECRUITABLE_COMPANIONS if hasattr(mechanics, "RECRUITABLE_COMPANIONS") else {}
            unrecruited = []
            for name, u_comp in all_known.items():
                is_recruited = False
                if isinstance(comps, dict):
                    c_entry = comps.get(name)
                    if isinstance(c_entry, dict) and c_entry.get("recruited", False):
                        is_recruited = True
                elif isinstance(comps, list):
                    for x in comps:
                        if isinstance(x, dict) and x.get("name") == name and x.get("recruited", False):
                            is_recruited = True
                            break
                if not is_recruited:
                    unrecruited.append(u_comp)

            if not unrecruited:
                st.success("All known Sector 1 companions have joined your vanguard!")
            else:
                for u_comp in unrecruited:
                    u_name = u_comp.get("name", "Unknown Companion")
                    st.markdown(f"##### 👤 {u_name} — `{u_comp.get('title', u_comp.get('class', 'Warrior'))}`")
                    st.caption(f"**Class:** {u_comp.get('class', '')} | **Lineage:** {u_comp.get('race', 'Human')} | **Starting Level:** {u_comp.get('level', 1)}")
                    st.write(u_comp.get("bio", u_comp.get("background", "")))
                    if st.button(f"Recruit {u_name} into Vanguard", key=f"btn_recruit_{u_name}"):
                        rec_res = mechanics.recruit_companion(player, u_name)
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

    # --- PHASE 10-12: PLANETARY PATCHWORK RAIDS (1-50 FLOORS), STABILIZER MERGE & INFO BROKER ---
    loc_str = str(player.get("location", "")).lower()
    in_dungeon = any(w in loc_str for w in ["dungeon", "depths", "labyrinth", "pohatcong", "spire", "overlord", "floor", "trench", "citadel", "override", "catacombs", "monolith"])
    raids_state = mechanics.ensure_planetary_raid_system(player) if hasattr(mechanics, "ensure_planetary_raid_system") else {}
    with st.expander("🗼 Planetary Patchwork Raids (1–50 Floors) & Stabilizer Hub", expanded=in_dungeon):
        raid_reg = getattr(mechanics, "GLOBAL_RAID_REGISTRY", {})
        if raid_reg:
            raid_ids = list(raid_reg.keys())
            cur_r_id = raids_state.get("active_raid_id", "pohatcong_spire")
            if cur_r_id not in raid_ids:
                cur_r_id = "pohatcong_spire"

            def _fmt_raid(rid):
                rd = raid_reg[rid]
                nd = raids_state.get("raid_nodes", {}).get(rid, {})
                st_badge = "🛡️ 0% Bleed" if nd.get("is_stabilized") else f"⚠️ {nd.get('anomaly_bleed', 0)}% Bleed"
                gate_b = "🌀 Gate Open" if nd.get("gate_unsealed") else f"🧭 Overland ({rd['overland_days']}d)"
                return f"{rd['name']} [F{nd.get('current_floor', 1)}/{rd['total_floors']} | {st_badge} | {gate_b}]"

            sel_raid_id = st.selectbox("Select Global Raid Location:", raid_ids, index=raid_ids.index(cur_r_id), format_func=_fmt_raid, key="hud_global_raid_select")
            r_status = mechanics.get_global_raid_status(player, sel_raid_id)
            live_node = r_status["live"]

            st.markdown(f"#### 🗼 {r_status['name']} (`{r_status['region']}`)")
            st.caption(f"📍 **Real-World Anchor:** {r_status['real_world_site']} | **Lv. {r_status['recommended_level'][0]}–{r_status['recommended_level'][1]}** | **Floors:** `{r_status['current_floor']} / {r_status['total_floors']}` (Mid-Boss: **F{r_status['mid_boss_floor']}**)")
            st.caption(f"🧱 **Current Stratum:** `{r_status['stratum']['name']}` — *{r_status['stratum']['hazard']}*")

            if r_status["is_stabilized"]:
                st.success("🛡️ **STABILIZER BRAKE ACTIVE:** Mid-Boss defeated! Anomaly Bleed is permanently locked at **0%**.")
            else:
                bleed_val = r_status["anomaly_bleed"]
                st.progress(min(1.0, bleed_val / 100.0), text=f"Anomaly Bleed: {bleed_val}% (Defeat F{r_status['mid_boss_floor']} Mid-Boss to lock at 0%)")

            rival_sq = live_node.get("rival_squad", {})
            if rival_sq:
                sq_st = rival_sq.get("status", "pushing")
                st.caption(f"🚩 **Frontline Ticker:** `{rival_sq.get('squad_name')}` ({rival_sq.get('commander')}) — Floor {rival_sq.get('current_floor', 1)} (`{sq_st}`)")
                if sq_st == "pinned_at_mid_boss":
                    if st.button(f"🆘 Rescue {rival_sq.get('squad_name')} at Floor {r_status['mid_boss_floor']}", key=f"btn_rescue_sq_{sel_raid_id}", use_container_width=True):
                        r_sq_res = mechanics.rescue_pinned_frontline_squad(player, sel_raid_id)
                        save_game(player, st.session_state.messages)
                        st.toast(r_sq_res["message"], icon="🆘")
                        st.rerun()

            # Travel Controls (Option 1 Leyline Gate vs Option 3 Overland Expedition)
            tr_c1, tr_c2 = st.columns(2)
            with tr_c1:
                if st.button("🌀 Leyline Gate Warp", key=f"btn_gate_warp_{sel_raid_id}", use_container_width=True, disabled=not live_node.get("gate_unsealed", False)):
                    t_res = mechanics.travel_to_global_raid(player, sel_raid_id, travel_mode="leyline_gate")
                    if t_res["success"]:
                        save_game(player, st.session_state.messages)
                        st.toast(t_res["message"], icon="🌀")
                        st.rerun()
            with tr_c2:
                if st.button(f"🧭 Overland Trek ({r_status['overland_days']}d)", key=f"btn_overland_{sel_raid_id}", use_container_width=True):
                    t_res = mechanics.travel_to_global_raid(player, sel_raid_id, travel_mode="overland")
                    if t_res["success"]:
                        save_game(player, st.session_state.messages)
                        st.toast(t_res["message"], icon="🧭")
                        st.rerun()

            st.divider()
            # Floor Delving, Anti-Crystal & Crystal Extraction
            if live_node.get("anti_crystal_active", False):
                st.error("🚨 **CRIMSON ANTI-CRYSTAL FIELD ACTIVE!** Teleport & Waypoint Crystals are JAMMED!")
                if st.button("💎 Shatter Anti-Crystal Jamming Obelisk", key=f"btn_disable_jammer_{sel_raid_id}", use_container_width=True):
                    j_res = mechanics.disable_anti_crystal_jammer(player, sel_raid_id)
                    save_game(player, st.session_state.messages)
                    st.toast(j_res["message"], icon="💎")
                    st.rerun()

            fl_c1, fl_c2, fl_c3 = st.columns(3)
            with fl_c1:
                if st.button("⬆️ Advance +1F", key=f"btn_adv_fl_{sel_raid_id}", use_container_width=True):
                    raids_state["active_raid_id"] = sel_raid_id
                    f_res = mechanics.advance_raid_floor(player, sel_raid_id)
                    save_game(player, st.session_state.messages)
                    if f_res["success"]:
                        st.toast(f_res["message"], icon="🗼")
                    else:
                        st.warning(f_res["message"])
                    st.rerun()
            with fl_c2:
                if st.button("🌀 Waypoint (F" + str(r_status["mid_boss_floor"]) + ")", key=f"btn_wp_crys_{sel_raid_id}", use_container_width=True):
                    w_res = mechanics.use_waypoint_crystal(player, sel_raid_id)
                    if w_res["success"]:
                        save_game(player, st.session_state.messages)
                        st.toast(w_res["message"], icon="🌀")
                        st.rerun()
                    else:
                        st.warning(w_res["message"])
            with fl_c3:
                if st.button("💎 Teleport Out", key=f"btn_tp_crys_{sel_raid_id}", use_container_width=True):
                    tp_res = mechanics.use_teleport_crystal(player)
                    if tp_res["success"]:
                        save_game(player, st.session_state.messages)
                        st.toast(tp_res["message"], icon="💎")
                        st.rerun()
                    else:
                        st.error(tp_res["message"])

            # Mid-Boss & Apex Boss Engagement
            mb_c1, mb_c2 = st.columns(2)
            with mb_c1:
                mb_label = "✅ Mid-Boss Cleared" if live_node.get("mid_boss_defeated") else f"⚔️ Fight F{r_status['mid_boss_floor']} Mid-Boss"
                if st.button(mb_label, key=f"btn_fight_mb_{sel_raid_id}", use_container_width=True, disabled=bool(live_node.get("mid_boss_defeated"))):
                    mb_res = mechanics.engage_raid_mid_boss(player, sel_raid_id, damage_dealt=250)
                    save_game(player, st.session_state.messages)
                    st.toast(mb_res["message"], icon="⚔️")
                    st.rerun()
            with mb_c2:
                ab_label = "👑 Raid Conquered" if live_node.get("apex_boss_defeated") else f"👑 Fight F{r_status['apex_boss_floor']} Apex Boss"
                if st.button(ab_label, key=f"btn_fight_ab_{sel_raid_id}", use_container_width=True, disabled=bool(live_node.get("apex_boss_defeated"))):
                    ab_res = mechanics.engage_raid_apex_boss(player, sel_raid_id, damage_dealt=400)
                    save_game(player, st.session_state.messages)
                    st.toast(ab_res["message"], icon="👑")
                    st.rerun()

            # Info Broker "Cipher" & Raid Strategy Briefing
            st.divider()
            st.markdown("##### 🕵️ Info Broker 'Cipher' & Pre-Boss Strategy Briefing")
            br_c1, br_c2 = st.columns(2)
            with br_c1:
                if st.button("🕵️ Floor Recon (150 Col)", key=f"btn_cipher_recon_{sel_raid_id}", use_container_width=True, disabled=bool(live_node.get("floor_recon_purchased"))):
                    b_res = mechanics.purchase_broker_intel(player, sel_raid_id, "floor_recon")
                    if b_res["success"]:
                        save_game(player, st.session_state.messages)
                        st.toast(b_res["message"], icon="🕵️")
                        st.rerun()
                    else:
                        st.warning(b_res["message"])
            with br_c2:
                if st.button("📑 Boss Dossier (250 Col)", key=f"btn_cipher_dossier_{sel_raid_id}", use_container_width=True, disabled=bool(live_node.get("boss_dossier_purchased"))):
                    b_res = mechanics.purchase_broker_intel(player, sel_raid_id, "boss_dossier")
                    if b_res["success"]:
                        save_game(player, st.session_state.messages)
                        st.toast(b_res["message"], icon="📑")
                        st.rerun()
                    else:
                        st.warning(b_res["message"])

            sq_opts = list(getattr(mechanics, "RAID_STRATEGY_SUPPORT_SQUADS", {}).keys())
            if sq_opts:
                sel_sup_sq = st.selectbox("Assign Allied Strike Team:", sq_opts, key=f"sel_strat_sq_{sel_raid_id}")
                if st.button("📋 Lock In Raid Strategy Briefing", key=f"btn_lock_strat_{sel_raid_id}", use_container_width=True):
                    st_res = mechanics.conduct_raid_strategy_briefing(player, sel_raid_id, sel_sup_sq)
                    save_game(player, st.session_state.messages)
                    st.toast(st_res["message"], icon="📋")
                    st.rerun()

            # Frontline Reputation & Unique Skill Status
            rep_info = player.get("frontline_reputation", {"la_count": 0, "beater_notoriety": 0, "title": "Frontline Clearer"})
            u_track = player.get("unique_skill_trackers", {})
            st.caption(f"🏆 **Standing:** `{rep_info.get('title', 'Frontline Clearer')}` | **LA Relics:** `{rep_info.get('la_count', 0)}` | **Unique Skill:** `{u_track.get('unlocked_unique_skill') or 'Dormant'}`")

    # Sovereign Homestead, Vault, +1 to +50 Smithing, Enclave Stewardship & Player Guilds
    if hasattr(mechanics, "ensure_homestead_system"):
        mechanics.ensure_homestead_system(player)
    h_data = player.get("homestead", {})
    h_owned = h_data.get("owned", False)
    with st.expander("🏰 Homestead, +50 Master Smith, Enclave & Guilds", expanded=h_owned):
        hm_tab1, hm_tab2, hm_tab3, hm_tab4 = st.tabs(["🔨 +50 Smith", "🏰 Estate/Vault", "🛡️ Enclave", "🚩 Guilds"])
        with hm_tab1:
            st.markdown("##### 🔨 Master Artisan Smithing (`+1` to `+50`)")
            st.caption("Enhance equipped weapons & armor up to +50. Commissioning Master Smith safeguards +11 to +50 against downgrades!")
            smith_eq_slots = mechanics.get_character_equipment_slots(player) if hasattr(mechanics, "get_character_equipment_slots") else {
                "main_hand": "Main Hand", "off_hand": "Off-Hand", "chest": "Chest", "head": "Head", "accessory": "Accessory"
            }
            enh_slot = st.selectbox(
                "Select Equipped Slot:",
                list(smith_eq_slots.keys()),
                format_func=lambda k, _sm=smith_eq_slots: f"{_sm.get(k, k)} ({player.get('equipped', {}).get(k, 'None')})",
                key="hud_smith_slot",
            )
            use_ms = st.checkbox("🛡️ Commission Master Smith Safeguard (+25% Success, Zero Downgrade)", value=True, key="hud_smith_safeguard")
            if st.button("🔨 Enhance Equipped Item (+1 Tier)", key="btn_enhance_item_hud", use_container_width=True):
                e_res = mechanics.enhance_equipment(player, slot=enh_slot, use_master_smith=use_ms, target_levels=1)
                if e_res.get("success"):
                    save_game(player, st.session_state.messages)
                    st.toast(e_res["message"], icon="🔨")
                    st.rerun()
                else:
                    st.warning(e_res.get("message", "Enhancement failed."))
        with hm_tab2:
            if not h_owned:
                st.markdown("#### 🏰 Washington Borough Estate (3,500 Col)")
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
                st.write(f"💰 Vault Col: `{h_data.get('vault_col', 0):,} Col` | Stored Items: `{len(h_data.get('vault_items', []))} / {v_cap['max_slots']}`")
                if st.button("🌱 Harvest Daily Greenhouse Yield", key="btn_harvest_garden_hud", use_container_width=True):
                    g_res = mechanics.harvest_alchemical_garden(player)
                    save_game(player, st.session_state.messages)
                    st.toast(g_res["message"], icon="🌿")
                    st.rerun()
        with hm_tab3:
            enclave = mechanics.ensure_enclave_stewardship(player) if hasattr(mechanics, "ensure_enclave_stewardship") else {}
            st.markdown(f"##### 🛡️ {enclave.get('name', 'Washington Borough Enclave')}")
            st.write(f"**Defense:** `{enclave.get('defense_rating', 40)}/100` | **Prosperity:** `{enclave.get('prosperity', 50)}/100` (`{enclave.get('citizen_morale', 'Hopeful')}`)")
            if enclave.get("outbreak_siege_active"):
                st.error("🚨 **SAFE-ZONE OUTBREAK SIEGE ACTIVE!**")
                if st.button("⚔️ Repel Outbreak Siege!", key="btn_repel_siege_hud", use_container_width=True):
                    s_res = mechanics.resolve_enclave_outbreak_siege(player)
                    save_game(player, st.session_state.messages)
                    st.toast(s_res["message"], icon="🛡️")
                    st.rerun()
            if st.button("🏛️ Invest 250 Col in Enclave Defenses", key="btn_invest_enclave_hud", use_container_width=True):
                c_res = mechanics.contribute_to_enclave_stewardship(player, 250)
                if c_res["success"]:
                    save_game(player, st.session_state.messages)
                    st.toast(c_res["message"], icon="🏛️")
                    st.rerun()
                else:
                    st.warning(c_res["message"])
        with hm_tab4:
            guild = mechanics.ensure_player_guild_system(player) if hasattr(mechanics, "ensure_player_guild_system") else {}
            if not guild.get("chartered"):
                g_name_in = st.text_input("Guild Name:", value="Knights of the Fractured Oath", key="hud_guild_name_in")
                if st.button("🚩 Charter Player Guild (500 Col)", key="btn_charter_guild_hud", use_container_width=True):
                    g_res = mechanics.charter_player_guild(player, g_name_in)
                    if g_res["success"]:
                        save_game(player, st.session_state.messages)
                        st.toast(g_res["message"], icon="🚩")
                        st.rerun()
                    else:
                        st.warning(g_res["message"])
            else:
                st.markdown(f"##### 🚩 {guild['name']}")
                st.caption(f"*\"{guild.get('motto', '')}\"* | Strike Squads: `{len(guild.get('strike_squads', []))}`")
                gc1, gc2 = st.columns(2)
                with gc1:
                    if st.button("📡 Dispatch Squads", key="btn_dispatch_sq_hud", use_container_width=True):
                        d_res = mechanics.dispatch_guild_squad(player, raid_id=raids_state.get("active_raid_id", "pohatcong_spire"))
                        save_game(player, st.session_state.messages)
                        st.toast(d_res["message"], icon="📡")
                        st.rerun()
                with gc2:
                    if st.button("💰 Collect Spoils", key="btn_collect_sq_hud", use_container_width=True):
                        col_res = mechanics.collect_guild_dispatch_rewards(player)
                        save_game(player, st.session_state.messages)
                        st.toast(col_res["message"], icon="💰")
                        st.rerun()

            st.divider()
            st.markdown("##### 🌟 Companion Personal Raid Quests")
            sel_cq = st.selectbox("Select Companion:", ["Ren", "Elora", "Torvald", "Kibs"], key="hud_comp_quest_sel")
            if st.button(f"📜 Advance {sel_cq}'s Personal Quest", key="btn_adv_comp_quest_hud", use_container_width=True):
                cq_res = mechanics.advance_companion_personal_quest(player, sel_cq)
                save_game(player, st.session_state.messages)
                st.toast(cq_res["message"], icon="🌟")
                st.rerun()



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
                            visible_room = gm_engine.generate_visible_state(api_key=api_key, player_state=st.session_state.player)
                            
                            # 2. All Room SubAgents Act Autonomously (Companions, Monsters, NPCs)
                            subagent_actions = persona_engine.run_all_room_subagents(api_key=api_key, visible_room=visible_room, player_action=result_text, player_state=st.session_state.player)
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
                            turn_data = gm_engine.resolve_turn(api_key=api_key, player_action=result_text, player_state=st.session_state.player)
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

                            # 4. Generate scene image matching Main branch styling & dynamic equipped gear
                            image_data = None
                            image_prompt = turn_data.get("image_prompt", "")
                            if image_prompt:
                                try:
                                    img_bytes, img_err = gm_engine.generate_scene_image(api_key=api_key, prompt=image_prompt, player_state=st.session_state.player)
                                    if img_bytes:
                                        b64_img = base64.b64encode(img_bytes).decode("utf-8")
                                        image_data = f"data:image/png;base64,{b64_img}"
                                except Exception as e:
                                    print(f"[VOICE IMAGE ERROR] {e}", flush=True)

                            st.session_state.messages.append({
                                "role": "assistant", 
                                "content": narrative,
                                "mechanics_log": mechanics_log,
                                "subagent_log": subagent_log,
                                "image_data": image_data
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
    st.subheader("🌐 Cardinal Omniscience Multi-Layer Geospatial Atlas")
    import map_engine
    if not hasattr(map_engine, "SECTORS"):
        import importlib
        try:
            importlib.reload(map_engine)
        except Exception as _re_err:
            print(f"[RELOAD ERROR] Failed to reload map_engine in HUD: {_re_err}", flush=True)

    map_state = map_engine.load_map_state() if hasattr(map_engine, "load_map_state") else {
        "player_x": 50, "player_y": 50, "active_sector": "sector1_primary", "active_layer": "usgs_topo"
    }

    sectors_dict = getattr(map_engine, "SECTORS", {})
    if not sectors_dict:
        sectors_dict = {
            "sector1_primary": {
                "id": "sector1_primary",
                "name": "Sector 1: Primary 25-Mile Core",
                "radius_miles": 25.0,
                "center_gps": (40.7584, -74.9793),
                "elevation_asl_ft": 460,
                "description": "Warren, Hunterdon, Morris, Sussex, and Northampton regional corridor."
            }
        }

    layers_dict = getattr(map_engine, "LAYERS", {})
    if not layers_dict:
        layers_dict = {
            "usgs_topo": {
                "id": "usgs_topo",
                "label": "🗺️ Surface Topography (USGS Topo)",
                "description": "USGS topographic elevation contours, surface highways, and township boundaries."
            }
        }

    col_sector, col_layer = st.columns([3, 2])
    with col_sector:
        sector_options = list(sectors_dict.keys())
        cur_sec = map_state.get("active_sector", "sector1_primary")
        sec_idx = sector_options.index(cur_sec) if cur_sec in sector_options else (sector_options.index("sector1_primary") if "sector1_primary" in sector_options else 0)
        selected_sector_id = st.selectbox(
            "🗺️ Sector Region:",
            options=sector_options,
            format_func=lambda s: sectors_dict.get(s, {}).get("name", s),
            index=sec_idx,
            key="hud_map_sector_select"
        )

    with col_layer:
        if hasattr(map_engine, "get_available_layers"):
            available_layers = map_engine.get_available_layers(selected_sector_id)
        else:
            available_layers = list(layers_dict.keys())
        cur_lay = map_state.get("active_layer", "usgs_topo")
        lay_idx = available_layers.index(cur_lay) if cur_lay in available_layers else 0
        selected_layer_id = st.selectbox(
            "📊 Sensor Datum Layer:",
            options=available_layers,
            format_func=lambda l: layers_dict.get(l, {}).get("label", l),
            index=lay_idx,
            key="hud_map_layer_select"
        )

    # Render Tactical Composite Map
    rendered_map_path = None
    map_telemetry = {}
    if hasattr(map_engine, "render_sector_layer"):
        try:
            rendered_map_path, map_telemetry = map_engine.render_sector_layer(
                sector_id=selected_sector_id,
                layer_id=selected_layer_id,
                player_state=st.session_state.player,
                character_id=st.session_state.get("active_character_id")
            )
        except Exception as _map_err:
            print(f"[MAP RENDER ERROR] {_map_err}", flush=True)
            map_telemetry = {}
    elif hasattr(map_engine, "generate_overlay"):
        try:
            rendered_map_path = map_engine.generate_overlay(player_skills=st.session_state.player.get("skills", []))
        except Exception as _map_err:
            print(f"[MAP OVERLAY ERROR] {_map_err}", flush=True)

    if not isinstance(map_telemetry, dict):
        map_telemetry = {}

    if rendered_map_path and os.path.exists(rendered_map_path):
        sec_name = sectors_dict.get(selected_sector_id, {}).get("name", selected_sector_id)
        lay_name = layers_dict.get(selected_layer_id, {}).get("label", selected_layer_id)
        st.image(rendered_map_path, caption=f"{sec_name} — {lay_name}", use_container_width=True)

    # Subterranean Telemetry HUD (Shown on Subterranean & Cross-Section layers)
    if selected_layer_id in ("bathymetry_underground", "vertical_cross_section") and map_telemetry:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Altitude / Depth", f"{map_telemetry.get('bottom_asl_ft', 460)} ft ASL")
        c2.metric("Overburden", f"{map_telemetry.get('overburden_ft', 0)} ft")
        c3.metric("Hydrostatic Pressure", f"{map_telemetry.get('hydrostatic_psi', 0.0)} PSI")
        c4.metric("Atmosphere", map_telemetry.get("environment_state", "Dry Bedrock"))

    gps_coords = map_telemetry.get("player_gps", (40.7584, -74.9793))
    gps_lat, gps_lon = gps_coords if isinstance(gps_coords, (tuple, list)) and len(gps_coords) >= 2 else (40.7584, -74.9793)
    st.write(f"**GPS Coordinates:** Lat: `{gps_lat:.4f}° N`, Lon: `{gps_lon:.4f}° W` | Grid: X: `{map_state.get('player_x', 50)}`, Y: `{map_state.get('player_y', 50)}`")
    st.write(f"**Status:** {world_state['world_status']}")

    # Continental & Faction News Wire
    news_list = world_state.get("global_news", [])
    if news_list:
        with st.expander("📡 Continental News Wire", expanded=False):
            for n in reversed(news_list[-5:]):
                st.caption(f"• {n}")

    # Regional Hub & Fast Actions + 100-Mile Fractured Atlas
    curr_loc = st.session_state.player.get("location", "")
    active_atlas_zone = world_atlas.resolve_zone_from_location(curr_loc, x=map_state.get("player_x"), y=map_state.get("player_y"))
    is_in_safe_zone = (
        world_atlas.is_location_safe_zone(curr_loc, x=map_state.get("player_x"), y=map_state.get("player_y"))
        or "washington" in curr_loc.lower()
        or (map_state.get("player_x") == 50 and map_state.get("player_y") == 50)
    )
    
    with st.expander("🏛️ Regional Hub & 100-Mile Atlas", expanded=is_in_safe_zone):
        if is_in_safe_zone:
            safe_title = active_atlas_zone["name"] if active_atlas_zone else "Washington Borough Safe-Zone"
            safe_desc = active_atlas_zone["lore_summary"] if active_atlas_zone else "A fortified civilian sanctuary ruled by the Warren County Barony."
            st.success(f"📍 **Sanctuary: {safe_title}**")
            st.caption(safe_desc)
            
            c_hub1, c_hub2 = st.columns(2)
            with c_hub1:
                if st.button("🛏️ Safe-Zone Rest (24h)", use_container_width=True, help="Full HP recovery, cures [Cellular Re-Knitting], & triggers living world simulation."):
                    if not active_atlas_zone:
                        st.session_state.player["location"] = "Sector 1 Safe-Zone: Washington Borough, NJ"
                    if hasattr(mechanics, "advance_post_op_recovery"):
                        mechanics.advance_post_op_recovery(st.session_state.player, hours=24, in_safe_zone=True)
                    if hasattr(mechanics, "advance_living_world_day"):
                        lw_res = mechanics.advance_living_world_day(st.session_state.player, days=1)
                        for ev in lw_res.get("news_events", []):
                            if ev not in world_state.setdefault("global_news", []):
                                world_state["global_news"].append(ev)
                    st.session_state.pending_dev_command = f"I take a full 24-hour long rest in the {safe_title} sanctuary to recover our wounds, complete any post-op cellular re-knitting, and hear the latest regional news."
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()
                if st.button("🏥 Visit Doc Mercer", use_container_width=True, help="Visit the subterranean clinic for graft consultation & surgery."):
                    st.session_state.player["location"] = "Doc Mercer's Underground Clinic (Washington Borough Catacombs)"
                    st.session_state.pending_dev_command = "I head down into the ancient vaulted catacombs beneath Washington Avenue to consult with Doc Mercer at his flesh-weaving and graft clinic."
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()

            with c_hub2:
                if st.button("🪙 Quartermaster Vane", use_container_width=True, help="Trade supplies and review Warren County Barony bounties."):
                    st.session_state.player["location"] = "Washington Borough - Quartermaster Vane's Logistics Depot"
                    st.session_state.pending_dev_command = "I report to Quartermaster Vane at the Warren County logistics depot to trade salvage and review active bounties."
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()
                if st.button("⛏️ Travel to Oxford Mines", use_container_width=True, help="Depart the safe zone toward Oxford Adits (X:53, Y:48)."):
                    st.session_state.pending_dev_command = "I gear up with Ren and travel along the ridge toward the Oxford Furnace & Deep Magnetite Mines."
                    st.rerun()

            # Fast Surgical Action if graft candidate in inventory (Milestone 2)
            inv_items = [item.get("name", str(item)) if isinstance(item, dict) else str(item) for item in st.session_state.player.get("inventory", [])]
            graft_candidates = [i for i in inv_items if any(k in i.lower() for k in ["graft", "core", "carapace", "piston", "optic", "bio", "implant", "plate"])]
            if graft_candidates:
                st.divider()
                st.caption("💉 **Doc Mercer's Clinic: Canonical Tier-1 Surgical Graft Installation (250 Col / Promissory Blood-Debt)**")
                sel_graft = st.selectbox("Select Component to Graft:", graft_candidates, key="hub_graft_candidate_select")
                mercer_graft_slots = mechanics.get_character_graft_slots(st.session_state.player) if hasattr(mechanics, "get_character_graft_slots") else {
                    "spine": "Spine / Internal", "torso": "Torso", "left_arm": "Left Arm", "right_arm": "Right Arm", "legs": "Legs", "head": "Head"
                }
                sel_slot_key = st.selectbox(
                    "Target Anatomical Slot:",
                    list(mercer_graft_slots.keys()),
                    format_func=lambda k, _gm=mercer_graft_slots: _gm.get(k, k),
                    key="hub_graft_slot_select",
                )
                sel_slot_label = mercer_graft_slots.get(sel_slot_key, sel_slot_key)
                cur_col = st.session_state.player.get("col", 0)
                btn_label = (
                    f"🦾 Pay Doc Mercer (250 Col) to Install [{sel_graft}] into [{sel_slot_label}]"
                    if cur_col >= 250
                    else f"🩸 Sign Ripperdoc Blood-Debt (250 Col Owed) to Install [{sel_graft}] into [{sel_slot_label}]"
                )
                if st.button(btn_label, use_container_width=True):
                    st.session_state.player["location"] = "Doc Mercer's Underground Clinic (Washington Borough Catacombs)"
                    payment_phrase = "pay Doc Mercer the 250 Col Tier-1 surgical fee" if cur_col >= 250 else "sign Doc Mercer's Promissory Blood-Debt Note (250 Col deferred)"
                    st.session_state.pending_dev_command = f"I {payment_phrase} to surgically install [{sel_graft}] into my [{sel_slot_key}]. Verify my strain limit, check elemental compatibility, and begin the operation (applying 24h [Cellular Re-Knitting])."
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()

        else:
            zone_label = active_atlas_zone["name"] if active_atlas_zone else (curr_loc or "Wilderness")
            lvl_badge = f" (Lv. {active_atlas_zone['level_range'][0]}–{active_atlas_zone['level_range'][1]})" if active_atlas_zone else ""
            st.warning(f"📍 **Hostile Territory:** {zone_label}{lvl_badge}")
            if active_atlas_zone:
                st.caption(f"**{active_atlas_zone.get('quadrant', 'Sector 1')}** • {active_atlas_zone.get('lore_summary', '')}")
            else:
                st.caption("Active threat zone. Keep your weapon ready.")
            if st.button("🏛️ Return to Washington Safe-Zone", use_container_width=True, help="Navigate back to Washington Borough Safe-Zone (X:50, Y:50)."):
                st.session_state.player["location"] = "Sector 1 Safe-Zone: Washington Borough, NJ"
                map_state["player_x"] = 50
                map_state["player_y"] = 50
                map_engine.save_map_state(map_state)
                st.session_state.pending_dev_command = "We fall back from the hazard zone and take the cleared trail back to the Washington Borough Safe-Zone."
                save_game(st.session_state.player, st.session_state.messages)
                st.rerun()

        st.divider()
        st.markdown("#### 🗺️ 100-Mile Fractured Atlas & Expedition Planner")
        st.caption("Survey System-Merged Safe Zones, Mines, Dungeons, and Wilderness Grind Zones within 100 miles of Washington, NJ.")

        quad_options = [
            "All Quadrants (0–100 mi)",
            "Inner Core (0–25 mi)",
            "North & East (25–100 mi)",
            "West & Northwest (25–100 mi)",
            "South & Southwest (25–100 mi)",
        ]
        cat_label_map = {
            "All Categories": None,
            "🛡️ Safe Zones & Citadels": "safe_zone",
            "⛏️ Mines & Extraction Veins": "mine",
            "🏰 Dungeons & Megastructures": "dungeon",
            "🌲 Wilderness & Anomalies": "wilderness",
        }

        f_col1, f_col2 = st.columns(2)
        with f_col1:
            sel_quad_label = st.selectbox("Quadrant:", quad_options, key="atlas_quad_filter")
        with f_col2:
            sel_cat_label = st.selectbox("Category:", list(cat_label_map.keys()), key="atlas_cat_filter")

        quad_filter = None if sel_quad_label.startswith("All") else sel_quad_label
        cat_filter = cat_label_map[sel_cat_label]
        filtered_zones = world_atlas.get_zones_by_category(category=cat_filter, quadrant=quad_filter)

        if not filtered_zones:
            st.info("No zones match the selected filters.")
        else:
            cat_icon_map = {
                "safe_zone": "🛡️",
                "mine": "⛏️",
                "dungeon": "🏰",
                "wilderness": "🌲",
            }
            zone_Display_map = {}
            for z_data in filtered_zones:
                z_id = z_data["id"]
                icon = cat_icon_map.get(z_data.get("category"), "📍")
                lv_min, lv_max = z_data.get("level_range", (1, 5))
                dist_mi = z_data.get("distance_miles", 0)
                label = f"{icon} {z_data['name']} [Lv.{lv_min}-{lv_max} | {dist_mi} mi {z_data.get('bearing', '')}]"
                zone_Display_map[label] = z_id

            sel_zone_label = st.selectbox("Select Destination Zone:", list(zone_Display_map.keys()), key="atlas_zone_select")
            target_z_id = zone_Display_map[sel_zone_label]
            target_z = world_atlas.WORLD_ATLAS_ZONES[target_z_id]
            travel_telemetry = world_atlas.calculate_travel_telemetry(curr_loc, target_z_id, st.session_state.player) if hasattr(world_atlas, "calculate_travel_telemetry") else {}
            if not isinstance(travel_telemetry, dict):
                travel_telemetry = {}
            t_dist = travel_telemetry.get("distance_miles", target_z.get("distance_miles", 0))
            t_hrs = travel_telemetry.get("travel_hours", round(t_dist / 3.0, 1))
            t_mins = travel_telemetry.get("travel_minutes", int(t_hrs * 60))

            with st.container(border=True):
                lv_min, lv_max = target_z.get("level_range", (1, 5))
                st.markdown(f"**{target_z['name']}**")
                st.caption(
                    f"🌍 **Real-World Site:** {target_z.get('real_world_name', '')} ({target_z.get('distance_miles', 0)} mi {target_z.get('bearing', '')} of Washington NJ)  \n"
                    f"⚔️ **Recommended Level:** `Lv. {lv_min}–{lv_max}` | 🏛️ **Faction:** `{target_z.get('faction', 'Unaligned')}`  \n"
                    f"🧭 **Transit Estimate:** `{t_dist} mi` (~`{t_hrs} hrs` / `{t_mins} mins`)"
                )
                st.write(target_z.get("lore_summary", ""))
                if target_z.get("resident_races"):
                    st.caption(f"🧬 **Resident Races & Enclaves:** {', '.join(target_z['resident_races'])}")
                if target_z.get("monsters") or target_z.get("dispersed_monsters"):
                    m_list = target_z.get("monsters") or target_z.get("dispersed_monsters", [])
                    boss_str = target_z.get("boss") or target_z.get("apex_fantasy_spawn") or "None"
                    st.caption(f"🐉 **Dispersed Hostiles:** {', '.join(m_list)} | 💀 **Apex Boss:** `{boss_str}`")
                if target_z.get("resources"):
                    st.caption(f"💎 **Resources & Grafts:** {', '.join(target_z['resources'])}")
                if target_z.get("signature_grafts"):
                    st.caption(f"🦾 **Harvestable Grafts:** {', '.join(target_z['signature_grafts'])}")
                if target_z.get("environmental_hazards"):
                    st.caption(f"⚠️ **Hazards:** {', '.join(target_z['environmental_hazards'])}")

                try:
                    import backend.world_atlas as wa_mod
                    v_info = wa_mod.get_sector_vertical_layers(target_z_id)
                    if v_info:
                        with st.expander(f"📐 4-Layer Pre-Initialization Engineering Survey ({v_info.get('sector_code', '')})"):
                            st.caption(f"**Vertical Datum Span:** `{v_info.get('vertical_span_ft', '')}`")
                            st.markdown("**🏙️ Layer 1 — Above-Ground Skyscrapers, Bridges & Mountain Installations:**")
                            for item in v_info.get("above_ground", [])[:4]:
                                st.caption(f"• {item}")
                            st.markdown("**🛣️ Layer 2 — Street-Level Highways & Surface Railroads:**")
                            for item in v_info.get("street_level", [])[:4]:
                                st.caption(f"• {item}")
                            st.markdown("**🚇 Layer 3 — Subterranean Tunnels, Subways, Nuclear Bunkers & Deep Mines:**")
                            for item in v_info.get("subterranean", [])[:4]:
                                st.caption(f"• {item}")
                            st.markdown("**🌊 Layer 4 — Below-the-Waterline Bathymetry & Submerged Ruins:**")
                            for item in v_info.get("below_waterline", [])[:4]:
                                st.caption(f"• {item}")
                except Exception:
                    pass

                if st.button(f"🧭 Dispatch Expedition to {target_z['name']}", key=f"btn_travel_{target_z_id}", use_container_width=True):
                    st.session_state.player["location"] = target_z["name"]
                    gx, gy = target_z.get("grid_coords", (50, 50))
                    map_state["player_x"] = gx
                    map_state["player_y"] = gy
                    if [gx, gy] not in map_state.get("explored_tiles", []):
                        map_state.setdefault("explored_tiles", []).append([gx, gy])
                    map_engine.save_map_state(map_state)
                    if t_mins > 0:
                        mechanics.advance_game_time(st.session_state.player, minutes=min(t_mins, 240))
                    st.session_state.pending_dev_command = (
                        f"We chart an expedition across the Fractured Overlay to [{target_z['name']}] "
                        f"({target_z.get('real_world_name', '')}, {target_z.get('distance_miles', 0)} miles {target_z.get('bearing', '')} of Washington Borough). "
                        f"Describe our arrival and the immediate environment."
                    )
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()

    # Multi-Universe Bestiary & Fantasy Race Compendium
    with st.expander("📖 Multi-Universe Bestiary & Race Compendium", expanded=False):
        st.caption("Browse dispersed creatures, monsters, and playable races from D&D 3.5e/5E, Pathfinder 1E/2E, The Witcher, Final Fantasy, Monster Hunter, SAO, LotR, Warhammer & Elder Scrolls.")
        b_tab1, b_tab2 = st.tabs(["🐉 Dispersed Monsters", "🧬 45 Fantasy Races"])

        with b_tab1:
            origin_opts = [
                "All",
                "D&D",
                "Pathfinder",
                "The Witcher",
                "Final Fantasy",
                "Monster Hunter",
                "Sword Art Online",
                "Tolkien",
                "Warhammer",
                "Elder Scrolls",
            ]
            sel_origin = st.selectbox("Filter by Source Universe:", origin_opts, key="bestiary_origin_filter")
            matched_creatures = bestiary.search_bestiary(origin_system=sel_origin)
            if matched_creatures:
                c_map = {f"[Lv.{c['cr_level']}] {c['name']} ({c['origin']})": c for c in matched_creatures}
                sel_c_label = st.selectbox("Select Creature Entry:", list(c_map.keys()), key="bestiary_creature_select")
                c_entry = c_map[sel_c_label]
                with st.container(border=True):
                    st.markdown(f"**{c_entry['name']}**")
                    st.caption(f"🌌 **Origin:** `{c_entry['origin']}` | 🏷️ **Type:** `{c_entry['type']}` | ⚔️ **CR/Lv:** `{c_entry['cr_level']}` | ❤️ **HP:** `{c_entry['hp']}` | 🛡️ **AC:** `{c_entry['ac']}`")
                    st.write(c_entry.get("lore", ""))
                    if c_entry.get("signature_abilities"):
                        st.markdown("**⚡ Signature Mechanics & Abilities:**")
                        for ab in c_entry["signature_abilities"]:
                            st.caption(f"• {ab}")
                    if c_entry.get("habitats"):
                        hab_names = [world_atlas.WORLD_ATLAS_ZONES[h]["name"] if h in world_atlas.WORLD_ATLAS_ZONES else h for h in c_entry["habitats"]]
                        st.caption(f"🗺️ **100-Mile Habitats:** {', '.join(hab_names)}")
                    if c_entry.get("loot_drops"):
                        st.caption(f"💎 **Harvestable Spoils & Grafts:** {', '.join(c_entry['loot_drops'])}")

        with b_tab2:
            display_lineages = cg.get_character_creation_lineages() if hasattr(cg, "get_character_creation_lineages") else cg.RACIAL_LINEAGES
            race_map = {f"{r_data['name']} [{r_data.get('genre', 'Fantasy')}]": r_data for r_data in display_lineages.values()}
            sel_r_label = st.selectbox("Inspect Lineage:", list(race_map.keys()), key="bestiary_race_select")
            r_entry = race_map[sel_r_label]
            with st.container(border=True):
                st.markdown(f"**{r_entry['name']}** (`{r_entry.get('genre', 'Fantasy')}`)")
                st.write(r_entry.get("desc", ""))
                mods_str = ", ".join([f"{k} {v:+d}" for k, v in r_entry.get("stat_mods", {}).items() if v != 0])
                st.caption(f"📊 **Attribute Modifiers:** `{mods_str or 'Balanced (+1 All)'}`")
                for rab in r_entry.get("racial_abilities", []):
                    st.caption(f"• {rab}")

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
        st.caption("Streamlit Cloud erases local files when it sleeps. Save to disk anytime or prepare a downloadable backup on demand.")

        # Immediate Disk Flush
        if st.button("💾 Force Instant Save to Disk", key="btn_quick_save_disk", use_container_width=True):
            save_game(st.session_state.player, st.session_state.messages)
            st.toast("Campaign state saved to disk!", icon="💾")
            st.success("Successfully saved `save_game.json`, `world_state.json`, and rolling chat backup.")

        prepare_export = st.checkbox(
            "📦 Prepare Download & Clipboard Backup Payloads",
            value=False,
            key="chk_prepare_save_export",
            help="Generates the downloadable .json and .md files on demand so normal turns stay fast and memory-light."
        )
        if prepare_export:
            m_path = os.path.join(BASE_DIR, ".game_state", "secret_master_state.json")
            cur_master = {}
            if os.path.exists(m_path):
                try:
                    with open(m_path, "r", encoding="utf-8") as f:
                        cur_master = json.load(f)
                    if isinstance(cur_master, dict):
                        cur_master.pop("player", None)
                except Exception:
                    pass

            light_messages = [
                {k: (None if k == "image_data" else v) for k, v in m.items()}
                if isinstance(m, dict) else m
                for m in st.session_state.messages
            ]
            save_payload = {
                "player": st.session_state.player,
                "messages": light_messages,
                "world_state": st.session_state.get("world_state", {}),
                "master_state": cur_master,
                "last_saved": time.time()
            }
            try:
                save_json_str = json.dumps(save_payload, indent=2, default=str)
            except Exception:
                save_json_str = json.dumps({"error": "Failed to serialize state"}, indent=2)

            st.download_button(
                label="📥 Export Full Campaign State (.json)",
                data=save_json_str,
                file_name=f"{ cg.sanitize_character_slug(st.session_state.player.get('name', 'campaign')) }_save.json",
                mime="application/json",
                key="btn_download_campaign_json",
                use_container_width=True,
            )

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
                key="btn_download_campaign_transcript_md",
                use_container_width=True,
            )

            with st.expander("📋 View / Copy Raw Save JSON (Clipboard Backup)"):
                st.caption("If your mobile browser or network blocks file downloads, copy this raw JSON directly to your notes.")
                st.code(save_json_str, language="json")
        
        # 3. Import & Restore (File or Direct Paste)
        st.divider()
        st.markdown("**Restore Campaign**")
        def apply_restored_save_data(loaded_data):
            player_obj = loaded_data.get("player", {})
            msgs = loaded_data.get("messages", [])

            # 1. Deduplicate repeated boss drops from the Rule 3 loop bug
            inv = player_obj.get("inventory", [])
            if isinstance(inv, list):
                deduped_inv = []
                seen_unique = set()
                unique_keys = [
                    "geothermal core piston",
                    "basalt carapace plating",
                    "intact runic mind-matrix"
                ]
                for item in inv:
                    item_str = item.get("name", str(item)) if isinstance(item, dict) else str(item)
                    low_str = item_str.strip().lower()
                    matched_uk = next((uk for uk in unique_keys if uk in low_str), None)
                    if matched_uk:
                        if matched_uk in seen_unique:
                            continue
                        seen_unique.add(matched_uk)
                    deduped_inv.append(item)
                if hasattr(mechanics, "enrich_inventory_list"):
                    deduped_inv = mechanics.enrich_inventory_list(deduped_inv)
                player_obj["inventory"] = deduped_inv

            # 2. Detect and strip the Silt-Marrow post-kill collapse loop if present in uploaded messages
            silt_kill_assistant_idx = None
            for idx, m in enumerate(msgs):
                if m.get("role") == "user" and "throw the bearded axe at the golem" in m.get("content", "").lower():
                    if idx + 1 < len(msgs) and msgs[idx + 1].get("role") in ["assistant", "system"]:
                        silt_kill_assistant_idx = idx + 1
                        break

            if silt_kill_assistant_idx is not None and len(msgs) > silt_kill_assistant_idx + 1:
                # Check if subsequent assistant messages had the repeated Piston drop bug
                subsequent_text = " ".join(m.get("content", "") + " " + m.get("mechanics_log", "") for m in msgs[silt_kill_assistant_idx + 1:])
                if "geothermal core piston" in subsequent_text.lower() or "compromised timber bracing" in subsequent_text.lower():
                    msgs = msgs[:silt_kill_assistant_idx + 1]
                    player_obj["location"] = "Oxford Mine - Exit Junction (Cleared)"
                    player_obj["hp"] = max(player_obj.get("hp", 58), 58)
                    if "companions" in player_obj and "Ren" in player_obj["companions"]:
                        player_obj["companions"]["Ren"]["hp"] = 28
                        player_obj["companions"]["Ren"]["status"] = "Active (Combat Ready - Watching Exit)"

            st.session_state.player = player_obj
            st.session_state.messages = msgs
            if "world_state" in loaded_data:
                st.session_state.world_state = loaded_data["world_state"]
            
            p_loc = st.session_state.player.get("location", "").strip()
            is_safe = any(w in p_loc.lower() for w in ["safe-zone", "safe zone", "washington", "clinic", "catacomb", "depot", "sanctuary", "manor", "outpost"])

            m_path = os.path.join(BASE_DIR, ".game_state", "secret_master_state.json")
            m_state = loaded_data.get("master_state")
            if not m_state and os.path.exists(m_path):
                try:
                    with open(m_path, "r", encoding="utf-8") as f:
                        m_state = json.load(f)
                except Exception:
                    m_state = None

            if m_state and isinstance(m_state, dict):
                m_state.pop("player", None)
                # Clean up defeated/inert hostiles
                m_state["entities"] = [
                    e for e in m_state.get("entities", [])
                    if e.get("type") not in ["hostile", "monster"]
                    or (e.get("hp", 1) > 0 and not any(s in [st.lower() for st in e.get("status", [])] for s in ["defeated", "inert", "dead", "destroyed", "slag", "harvested"]))
                ]
                
                # Check if hostiles remain
                has_hostiles = any(e.get("type") in ["hostile", "monster"] for e in m_state.get("entities", []))
                
                if is_safe:
                    m_state.setdefault("environment", {})["location"] = p_loc
                    m_state["environment"]["hidden_traps"] = []
                    curr_effs = m_state["environment"].get("environmental_effects", [])
                    hostile_cues = ["steam", "timber", "collapse", "falling", "shale", "cave-in", "hazard", "unstable", "compromised"]
                    m_state["environment"]["environmental_effects"] = [eff for eff in curr_effs if not any(c in eff.lower() for c in hostile_cues)] or ["Safe-Zone Sanctuary Wards", "Calm Ambient Mana"]
                elif not has_hostiles:
                    # Aftermath: clear collapse hazards and sync location
                    if p_loc:
                        m_state.setdefault("environment", {})["location"] = p_loc
                    m_state.setdefault("environment", {})["hidden_traps"] = []
                    curr_effs = m_state.get("environment", {}).get("environmental_effects", [])
                    if any(c in " ".join(curr_effs).lower() for c in ["steam", "timber", "collapse", "falling", "shale", "compromised", "hazard"]):
                        m_state.setdefault("environment", {})["environmental_effects"] = ["Dim Light", "Settling Dust", "Clear Escape Routes Available"]
                    desc = m_state.get("environment", {}).get("description", "")
                    if any(c in desc.lower() for c in ["splintered and venting", "superheated geothermal", "falling shale", "rock debris litter"]):
                        m_state.setdefault("environment", {})["description"] = "A damp, cavernous mine shaft exit junction. The massive chassis of Silt-Marrow the Unhewn lies completely inert, dismantled, and harvested. The seismic rumbles have ceased, leaving the path open to ascend upward via the ore-cart track toward the Washington Borough Safe-Zone or descend toward the Morris Canal Aqueducts."

                sid = get_current_session_id()
                try:
                    with db_transaction(session_id=sid) as db_sess:
                        MasterStateRepository.save_master_state(db_sess, m_state, session_id=sid)
                except Exception:
                    os.makedirs(os.path.dirname(m_path), exist_ok=True)
                    atomic_write_json(m_path, m_state)

                # Synchronize Staging_Ground
                vis_room = {
                    "turn_number": m_state.get("turn_number", 1),
                    "environment": {
                        "location": m_state.get("environment", {}).get("location", p_loc),
                        "description": m_state.get("environment", {}).get("description", ""),
                        "environmental_effects": m_state.get("environment", {}).get("environmental_effects", [])
                    },
                    "entities": [
                        {"id": e.get("id"), "name": e.get("name"), "type": e.get("type"), "status": e.get("status")}
                        for e in m_state.get("entities", [])
                    ]
                }
                try:
                    with db_transaction(session_id=sid) as db_sess:
                        StagingRepository.save_staging_state(
                            db_sess, visible_room=vis_room, action_queue=[], session_id=sid
                        )
                except Exception:
                    vr_path = os.path.join(BASE_DIR, "Staging_Ground", "visible_room.json")
                    atomic_write_json(vr_path, vis_room)
                    q_path = os.path.join(BASE_DIR, "Staging_Ground", "action_queue.json")
                    atomic_write_json(q_path, [])

            # Sync Party/companion_ren.json
            ren_data = st.session_state.player.get("companions", {}).get("Ren")
            if ren_data:
                sid = get_current_session_id()
                comps = st.session_state.player.get("companions", {})
                p_slug = st.session_state.player.get("slug") or sanitize_character_slug(st.session_state.player.get("name", "Survivor"))
                try:
                    with db_transaction(session_id=sid) as db_sess:
                        PartyRepository.save_party(
                            db_sess, comps, session_id=sid, mirror_disk=True, character_slug=p_slug, base_dir=BASE_DIR
                        )
                except Exception:
                    pass

            save_game(st.session_state.player, st.session_state.messages)

        uploaded_file = st.file_uploader("📤 Import Save File (.json)", type="json", key="save_file_uploader")
        if uploaded_file is not None:
            if st.button("Restore from Uploaded File", key="btn_restore_uploaded_file"):
                try:
                    loaded_data = json.load(uploaded_file)
                    apply_restored_save_data(loaded_data)
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
                    apply_restored_save_data(loaded_data)
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

    # Safely synchronize widget key with active character name
    if 'active_profile_select' not in st.session_state or st.session_state['active_profile_select'] not in profiles:
        st.session_state['active_profile_select'] = curr_name if curr_name in profiles else (profiles[0] if profiles else 'Banki')
    elif curr_name in profiles and st.session_state.get('active_profile') == curr_name and st.session_state['active_profile_select'] != curr_name:
        st.session_state['active_profile_select'] = curr_name

    def on_profile_dropdown_change():
        selected_prof = st.session_state.get('active_profile_select')
        if not selected_prof:
            return
        active_char_name = st.session_state.player.get('name', '')
        if selected_prof == active_char_name or st.session_state.get('character_creation_mode', False):
            return

        # 1. Atomically save current profile state prior to switching
        try:
            save_game(st.session_state.player, st.session_state.get('messages', []))
            mechanics.save_party_to_character_folder(BASE_DIR, active_char_name)
        except Exception:
            pass

        # 2. Activate target character cleanly via authoritative adapter
        activate_character_session(selected_prof, update_query_params=True)
        save_game(st.session_state.player, st.session_state.messages)

    if st.button("🏠 Choose Your Character Lobby", use_container_width=True, key="btn_return_char_select"):
        try:
            if st.session_state.get("character_selected") and "player" in st.session_state:
                save_game(st.session_state.player, st.session_state.get("messages", []))
        except Exception:
            pass
        st.session_state.character_selected = False
        st.session_state.character_creation_mode = False
        try:
            st.query_params.clear()
        except Exception:
            pass
        st.rerun()

    st.markdown('##### 👤 Character Slot')
    sel_profile = st.selectbox(
        'Active Profile',
        options=profiles,
        key='active_profile_select',
        on_change=on_profile_dropdown_change,
        label_visibility='collapsed'
    )
    st.caption(f"🔗 Unique Link: `{cg.build_character_unique_url(sel_profile)}`")

    other_profiles = [pr for pr in profiles if pr != sel_profile]
    if other_profiles:
        with st.expander("↗ Open Character in New Tab", expanded=False):
            for opr in other_profiles:
                st.link_button(
                    f"⚡ {opr} (New Tab ↗)",
                    url=cg.build_character_unique_url(opr),
                    use_container_width=True,
                )
            
    if not st.session_state.get('character_creation_mode', False):
        if st.button('🧬 New Avatar Calibration', use_container_width=True):
            st.session_state.character_creation_mode = True
            st.rerun()
    else:
        st.warning('⚡ Calibration Mode Active')
        if st.button('❌ Exit Calibration', use_container_width=True):
            st.session_state.character_creation_mode = False
            try:
                if "mode" in st.query_params:
                    del st.query_params["mode"]
            except Exception:
                pass
            st.rerun()
            
    st.divider()
    
    if st.session_state.get('character_creation_mode', False):
        render_sidebar_calibration_preview()
    else:
        render_game_hud()

def render_tutorial_crucible_banner():
    """Render an interactive Cardinal Calibration Crucible tutorial progress banner and stage controls."""
    player = st.session_state.get("player", {})
    if not hasattr(mechanics, "is_tutorial_active") or not mechanics.is_tutorial_active(player):
        return

    tut = player.get("tutorial", {})
    curr_stage = int(tut.get("stage", 1))
    tut_dungeon = mechanics.initialize_tutorial_mini_dungeon(player)
    cur_room = mechanics.get_current_tutorial_room(player)
    curr_phase = cur_room.get("phase", curr_stage)
    room_id = cur_room.get("room_id", "phase1_telemetry_sanctum")

    with st.container(border=True):
        col_hdr1, col_hdr2 = st.columns([3, 1])
        with col_hdr1:
            st.markdown(f"### 🎓 {cur_room.get('phase_name', f'Stage {curr_stage} Crucible')}")
            st.markdown(f"**Current Chamber:** `{cur_room.get('badge', 'Room')}` **{cur_room.get('name', 'Chamber')}**")
        with col_hdr2:
            st.metric("Progress", f"Phase {curr_phase} / 3", f"Level {player.get('level', 1)} → 3")

        progress_frac = max(0.0, min(1.0, (curr_phase - 1) / 3.0 + 0.1))
        st.progress(progress_frac, text=f"Tutorial Progress: Phase {curr_phase} of 3 | Current Level: {player.get('level', 1)} → Target: Level 3 & Safe-Zone Graduation")

        # Chamber Description & Active Environmental Hazards
        st.info(f"📜 **Chamber Environment:** {cur_room.get('description', '')}")
        if cur_room.get("hazards"):
            haz_labels = [h.get("name", str(h)) if isinstance(h, dict) else str(h) for h in cur_room["hazards"]]
            st.caption(f"⚠️ **Active Room Hazards:** {', '.join(haz_labels)}")

        # Adjacent Room Navigation Buttons
        adj_rooms = mechanics.get_tutorial_adjacent_rooms(player)
        if adj_rooms:
            st.markdown("**🚪 Adjacent Chambers & Passages:**")
            nav_cols = st.columns(max(1, len(adj_rooms)))
            for idx, adj in enumerate(adj_rooms):
                with nav_cols[idx]:
                    if st.button(f"➡️ Move to {adj['name']}", key=f"btn_nav_{adj['room_id']}", use_container_width=True):
                        move_res = mechanics.move_tutorial_dungeon_room(player, adj["room_id"])
                        save_game(st.session_state.player, st.session_state.messages)
                        st.rerun()

        st.divider()

        # Contextual Room Interaction Drill Buttons
        st.markdown("**⚡ Chamber Gameplay Drills & Interactive Trials:**")
        drill_c1, drill_c2 = st.columns([2, 2])
        with drill_c1:
            if room_id == "phase1_telemetry_sanctum":
                if st.button("🧭 Synchronize Telemetry Pedestal", key="drill_telemetry", use_container_width=True):
                    res = mechanics.interact_tutorial_telemetry_pillar(player)
                    st.success(res.get("message", "Telemetry synchronized!"))
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()
            elif room_id == "phase1_gravity_chasm":
                if st.button("⚖️ Test Encumbrance Hazard (STR*15 lbs)", key="drill_encumbrance", use_container_width=True):
                    res = mechanics.resolve_tutorial_encumbrance_hazard(player)
                    st.success(res.get("message", "Encumbrance evaluated!"))
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()
            elif room_id == "phase1_rust_mist_adit":
                if st.button("🧪 Brave Rust-Mist & Hone Durability (+25)", key="drill_durability", use_container_width=True):
                    res = mechanics.resolve_tutorial_durability_hazard(player)
                    st.success(res.get("message", "Durability honed!"))
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()
            elif room_id == "phase1_relic_sanctum":
                if st.button("✨ Resonate Soul-Bound Keepsake Relic", key="drill_relic", use_container_width=True):
                    res = mechanics.resolve_tutorial_relic_resonance(player)
                    st.success(res.get("message", "Relic resonated!"))
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()
            elif room_id == "phase2_proving_ground":
                if st.button("⚔️ Strike Sparring Automata (+15 Mastery)", key="drill_martial", use_container_width=True):
                    res = mechanics.resolve_tutorial_martial_drill(player)
                    st.success(res.get("message", "Martial strike landed!"))
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()
            elif room_id == "phase2_parry_arena":
                if st.button("🛡️ Charge Buffer & Execute Parry", key="drill_parry", use_container_width=True):
                    res = mechanics.resolve_tutorial_parry_and_charge(player)
                    st.success(res.get("message", "Parry and charge executed!"))
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()
            elif room_id == "phase2_coordination_annex":
                if st.button("🦾 Execute Multi-Limb Weapon Flurry", key="drill_multilimb", use_container_width=True):
                    res = mechanics.resolve_tutorial_multi_limb_drill(player)
                    st.success(res.get("message", "Multi-limb drill executed!"))
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()
            elif room_id == "phase2_triage_infirmary":
                if st.button("🩹 Triage Debuff & Slay Sentinel (➔ Lv. 2)", key="drill_sentinel", use_container_width=True):
                    res = mechanics.resolve_tutorial_status_triage(player)
                    st.success(res.get("message", "Clockwork Sentinel defeated!"))
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()
            elif room_id == "phase3_puzzle_vault":
                if st.button("🧩 Solve Runic Dials (DC 12 Arcana)", key="drill_puzzle", use_container_width=True):
                    res = mechanics.solve_tutorial_puzzle(player)
                    st.success(res.get("message", "Puzzle solved!"))
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()
            elif room_id == "phase3_foundry_hall":
                if st.button("⚔️ Engage Phalanx Construct", key="drill_foundry", use_container_width=True):
                    res = mechanics.resolve_tutorial_foundry_battle(player)
                    st.success(res.get("message", "Phalanx Construct defeated!"))
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()
            elif room_id == "phase3_warden_lair":
                if st.button("👑 Cast Astral Bolt & Slay Warden (➔ Lv. 3)", key="drill_boss", use_container_width=True):
                    res = mechanics.resolve_tutorial_warden_boss_battle(player)
                    st.balloons()
                    st.success(res.get("message", "Crucible Warden defeated! Graduated to Level 3!"))
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()
            else:
                st.write("Explore chamber to uncover hidden mechanisms.")

        with drill_c2:
            if room_id == "phase3_puzzle_vault":
                if st.button("🔍 Search for Secret Passages (DC 13)", key="drill_secret", use_container_width=True):
                    res = mechanics.discover_tutorial_secret_door(player)
                    if res.get("discovered"):
                        st.success(res.get("message"))
                    else:
                        st.warning(res.get("message"))
                    save_game(st.session_state.player, st.session_state.messages)
                    st.rerun()
            elif room_id == "phase3_secret_scriptorium":
                st.success("📜 Concealed Scriptorium Unlocked: Bonus lore codex and Col cache claimed!")
            else:
                st.caption("Room interactions trigger instant deterministic resolution.")

        st.divider()

        # Global Actions: Guided Action, Complete Phase Drill, and Fast-Forward
        stage_info = mechanics.get_tutorial_stage_info(curr_stage)
        btn_c1, btn_c2, btn_c3 = st.columns([2, 2, 1.5])
        with btn_c1:
            if st.button(
                f"🎲 Run Guided Phase {curr_phase} Action (AI + Drill)",
                type="primary",
                use_container_width=True,
                key=f"btn_tut_guided_p{curr_phase}",
            ):
                st.session_state["pending_dev_command"] = stage_info.get("suggested_action", f"Explore {cur_room.get('name')} and execute chamber trial.")
                st.rerun()
        with btn_c2:
            if st.button(
                f"✅ Complete Phase {curr_phase} Drills & Claim Loot",
                use_container_width=True,
                key=f"btn_tut_instant_p{curr_phase}",
            ):
                m_path = os.path.join(BASE_DIR, ".game_state", "secret_master_state.json")
                sid = get_current_session_id()
                m_state = None
                try:
                    with db_transaction(session_id=sid) as db_sess:
                        m_state = MasterStateRepository.load_master_state(db_sess, session_id=sid)
                except Exception:
                    m_state = atomic_read_json(m_path, default=None)
                res = mechanics.advance_tutorial_stage(
                    st.session_state.player,
                    player_action=stage_info.get("suggested_action", ""),
                    master_state=m_state,
                    complete_all=False,
                )
                if m_state is not None:
                    try:
                        with db_transaction(session_id=sid) as db_sess:
                            MasterStateRepository.save_master_state(db_sess, m_state, session_id=sid)
                    except Exception:
                        atomic_write_json(m_path, m_state)
                if res.get("teleported"):
                    try:
                        import map_engine
                        ms = map_engine.load_map_state()
                        ms["player_x"] = 50
                        ms["player_y"] = 50
                        if [50, 50] not in ms.get("explored_tiles", []):
                            ms.setdefault("explored_tiles", []).append([50, 50])
                        map_engine.save_map_state(ms)
                    except Exception:
                        pass
                st.session_state.messages.append({
                    "role": "user",
                    "content": stage_info.get("suggested_action", ""),
                    "ai_prompt": stage_info.get("suggested_action", ""),
                })
                mech_lines = [f"* 🎲 `{lg}`" for lg in res.get("combat_logs", [])]
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": res.get("summary_markdown", "Stage complete."),
                    "mechanics_log": "\n".join(mech_lines),
                    "subagent_log": "",
                    "image_data": None,
                })
                save_game(st.session_state.player, st.session_state.messages)
                if res.get("graduated"):
                    st.balloons()
                st.rerun()
        with btn_c3:
            if st.button(
                "⚡ Fast-Forward to Lvl 3 & Washington, NJ",
                use_container_width=True,
                key=f"btn_tut_skip_p{curr_phase}",
            ):
                m_path = os.path.join(BASE_DIR, ".game_state", "secret_master_state.json")
                sid = get_current_session_id()
                m_state = None
                try:
                    with db_transaction(session_id=sid) as db_sess:
                        m_state = MasterStateRepository.load_master_state(db_sess, session_id=sid)
                except Exception:
                    m_state = atomic_read_json(m_path, default=None)
                res = mechanics.advance_tutorial_stage(
                    st.session_state.player,
                    player_action="Complete full Cardinal Calibration Crucible tutorial.",
                    master_state=m_state,
                    complete_all=True,
                )
                if m_state is not None:
                    try:
                        with db_transaction(session_id=sid) as db_sess:
                            MasterStateRepository.save_master_state(db_sess, m_state, session_id=sid)
                    except Exception:
                        atomic_write_json(m_path, m_state)
                try:
                    import map_engine
                    ms = map_engine.load_map_state()
                    ms["player_x"] = 50
                    ms["player_y"] = 50
                    if [50, 50] not in ms.get("explored_tiles", []):
                        ms.setdefault("explored_tiles", []).append([50, 50])
                    map_engine.save_map_state(ms)
                except Exception:
                    pass
                mech_lines = [f"* 🎲 `{lg}`" for lg in res.get("combat_logs", [])]
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": res.get("summary_markdown", "Tutorial graduated."),
                    "mechanics_log": "\n".join(mech_lines),
                    "subagent_log": "",
                    "image_data": None,
                })
                save_game(st.session_state.player, st.session_state.messages)
                st.balloons()
                st.rerun()


# --- MAIN UI: THE CHAT WINDOW OR CALIBRATION WIZARD ---
if st.session_state.get("character_creation_mode", False):
    render_character_calibration_wizard()
    st.stop()

st.title("🗡️ The Fractured Overlay")
st.caption("A Death-Game TTRPG powered by the Cardinal System AI.")

render_tutorial_crucible_banner()

# Offload any legacy inline base64 images in session_state.messages to disk
if isinstance(st.session_state.get("messages"), list):
    cg.migrate_messages_images_to_disk(
        BASE_DIR,
        st.session_state.player.get("name", "Survivor"),
        st.session_state.messages,
    )

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
        img_rel = msg.get("image_path")
        if img_rel:
            resolved_img = img_rel if os.path.isabs(img_rel) else os.path.join(BASE_DIR, img_rel)
            if os.path.exists(resolved_img):
                st.image(resolved_img, use_container_width=True)
        elif msg.get("image_data"):
            st.image(msg["image_data"], use_container_width=True)

# User Input
chat_prompt = st.chat_input("Action... (Type /admin to force an AI outcome)")
dev_prompt = st.session_state.pop("pending_dev_command", None)

if prompt := (dev_prompt or chat_prompt):
    
    # Intercept Explicit Admin Commands (normal UI action buttons execute as regular player turns)
    is_admin = prompt.strip().lower().startswith("/admin ") or "[root override]" in prompt.lower()
    if is_admin:
        command = prompt.replace("/admin ", "").replace("[ROOT OVERRIDE]", "").strip()
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
            visible_room = gm_engine.generate_visible_state(api_key=api_key, player_state=st.session_state.player, player_action=ai_prompt)
            
            # b. All Room SubAgents Act Autonomously (Companions, Monsters, NPCs)
            subagent_actions = persona_engine.run_all_room_subagents(api_key=api_key, visible_room=visible_room, player_action=ai_prompt, player_state=st.session_state.player)
            subagent_log_lines = []
            for sa in subagent_actions:
                actor_id = sa.get("actor_id", "")
                actor_name = sa.get("actor_name", actor_id or "SubAgent")
                thought = sa.get("internal_thought", "")
                intent = sa.get("intended_action", "Stands ready.")
                icon = "🤖" if "ren" in actor_id.lower() else "👾"
                subagent_log_lines.append(f"**[{icon} {actor_name} — SubAgent Mind]**\n> *\"{thought}\"*\n> **Intent:** {intent}")
            subagent_log = "\n\n".join(subagent_log_lines) if subagent_log_lines else ""
            
            # c. Resolve the turn (Read Player Action + SubAgent Action Queue + Live Equipped Gear)
            turn_data = gm_engine.resolve_turn(api_key=api_key, player_action=ai_prompt, player_state=st.session_state.player)
            
            narrative = turn_data.get("narrative_recap", "Error parsing narrative.")
            tactical_footer = turn_data.get("tactical_state_footer", "")
            if tactical_footer and tactical_footer not in narrative:
                narrative = f"{narrative}\n\n---\n`{tactical_footer}`"
            
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
                
            # Extract image prompt from TurnResolutionSchema
            image_prompt = turn_data.get("image_prompt", "") 
            
            # Living World Continental News Wire Updates (Milestone 1)
            news_add = turn_data.get("global_news_add", [])
            if state_updates and isinstance(state_updates, dict):
                news_add = news_add or state_updates.get("global_news_add", [])
            if news_add and isinstance(news_add, list):
                if "global_news" not in world_state: world_state["global_news"] = []
                for n in news_add:
                    if n not in world_state["global_news"]:
                        world_state["global_news"].append(n)
                sid = get_current_session_id()
                try:
                    with db_transaction(session_id=sid) as db_sess:
                        MasterStateRepository.save_world_state(db_sess, world_state, session_id=sid)
                except Exception:
                    atomic_write_json(os.path.join(BASE_DIR, "world_state.json"), world_state)

            # Apply State Updates
            if state_updates and isinstance(state_updates, dict):
                loc = state_updates.get("location")
                if loc and isinstance(loc, str):
                    st.session_state.player["location"] = loc
                    
                w_status = state_updates.get("world_status")
                if w_status and isinstance(w_status, str):
                    world_state["world_status"] = w_status
                    sid = get_current_session_id()
                    try:
                        with db_transaction(session_id=sid) as db_sess:
                            MasterStateRepository.save_world_state(db_sess, world_state, session_id=sid)
                    except Exception:
                        atomic_write_json(os.path.join(BASE_DIR, "world_state.json"), world_state)

                # Note: col_change and equip_* updates are applied inside apply_player_state_updates(state_updates) below.

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
            elif st.session_state.get("pending_fusion_components"):
                apply_player_state_updates({})

            # Advance Cardinal Calibration Crucible Tutorial Stage if active
            tutorial_res = None
            if hasattr(mechanics, "is_tutorial_active") and mechanics.is_tutorial_active(st.session_state.player):
                m_path = os.path.join(BASE_DIR, ".game_state", "secret_master_state.json")
                sid = get_current_session_id()
                m_state = None
                try:
                    with db_transaction(session_id=sid) as db_sess:
                        m_state = MasterStateRepository.load_master_state(db_sess, session_id=sid)
                except Exception:
                    m_state = atomic_read_json(m_path, default=None)
                tutorial_res = mechanics.advance_tutorial_stage(
                    st.session_state.player,
                    player_action=ai_prompt,
                    master_state=m_state,
                    complete_all=False,
                )
                if m_state is not None:
                    try:
                        with db_transaction(session_id=sid) as db_sess:
                            MasterStateRepository.save_master_state(db_sess, m_state, session_id=sid)
                    except Exception:
                        atomic_write_json(m_path, m_state)
                if tutorial_res.get("teleported"):
                    try:
                        ms = map_engine.load_map_state()
                        ms["player_x"] = 50
                        ms["player_y"] = 50
                        if [50, 50] not in ms.get("explored_tiles", []):
                            ms.setdefault("explored_tiles", []).append([50, 50])
                        map_engine.save_map_state(ms)
                    except Exception:
                        pass
                if tutorial_res.get("summary_markdown"):
                    narrative = f"{narrative}\n\n---\n\n{tutorial_res['summary_markdown']}"
                if tutorial_res.get("graduated"):
                    st.balloons()

            combat_logs = list(turn_data.get("combat_logs", []) or [])
            if tutorial_res and tutorial_res.get("combat_logs"):
                for tlog in tutorial_res["combat_logs"]:
                    if tlog not in combat_logs:
                        combat_logs.append(tlog)
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
            
            # 2. Generate Scene Image matching Main Branch styling and live equipped gear / grafts
            image_path_rel = None
            if image_prompt:
                try:
                    with st.spinner("Rendering scene illustration..."):
                        image_bytes, img_error = gm_engine.generate_scene_image(api_key, image_prompt, player_state=st.session_state.player)
                        if image_bytes:
                            image_path_rel = cg.persist_turn_image_to_disk(
                                BASE_DIR,
                                st.session_state.player.get("name", "Survivor"),
                                image_bytes,
                            )
                            if image_path_rel:
                                st.image(os.path.join(BASE_DIR, image_path_rel), use_container_width=True)
                            else:
                                st.image(image_bytes, use_container_width=True)
                        elif img_error:
                            narrative += f"\n\n*(System Note: Image Generation Failed - {img_error})*"
                except Exception as e:
                    narrative += f"\n\n*(System Note: Image Generation Exception - {e})*"
            
    new_msg = {
        "role": "assistant", 
        "content": narrative,
        "mechanics_log": mechanics_log,
        "subagent_log": subagent_log,
        "image_path": image_path_rel,
        "image_data": None
    }
    st.session_state.messages.append(new_msg)
    save_game(st.session_state.player, st.session_state.messages)
    
    st.rerun()
