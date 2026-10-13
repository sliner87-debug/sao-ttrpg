import streamlit as st
import json
import os
import time
import importlib
import base64
import re
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
def load_world():
    if os.path.exists(WORLD_PATH):
        try:
            with open(WORLD_PATH, 'r', encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"sector": 1, "world_status": "CRUCIBLE: ACTIVE", "map_locations": [], "global_news": []}

def load_game():
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

    data = {
        "player": player_state,
        "messages": messages,
        "world_state": world_data,
        "master_state": master_state,
        "last_saved": time.time()
    }
    with open(SAVE_PATH, 'w', encoding="utf-8") as f:
        json.dump(data, f, indent=4)
        
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


def apply_companion_state_updates(hp_changes: dict):
    """Synchronizes companion damage/healing across session state and Party/*.json sheets."""
    if not hp_changes or not isinstance(hp_changes, dict):
        return
        
    for c_key in ["companion_ren", "Ren", "ren"]:
        if c_key in hp_changes:
            delta = hp_changes[c_key]
            # 1. Update session state player["companions"]["Ren"]
            if "companions" in st.session_state.player and "Ren" in st.session_state.player["companions"]:
                ren_ref = st.session_state.player["companions"]["Ren"]
                old_hp = ren_ref.get("hp", 35)
                max_hp = ren_ref.get("max_hp", 35)
                new_hp = max(0, min(max_hp, old_hp + delta))
                ren_ref["hp"] = new_hp
                if delta < 0:
                    st.toast(f"🩸 Ren took {abs(delta)} damage! (HP: {new_hp}/{max_hp})", icon="🛡️")
                elif delta > 0:
                    st.toast(f"💚 Ren recovered {delta} HP! (HP: {new_hp}/{max_hp})", icon="🩹")
                    
            # 2. Update Party/companion_ren.json on disk
            party_file = os.path.join(BASE_DIR, "Party", "companion_ren.json")
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
            break

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
        "archetype": "QA Vanguard",
        "hp": 35,
        "max_hp": 35,
        "ac": 16,
        "status": "Vigilant and operational",
        "active_grafts": [
            {"name": "Sub-Dermal Optical Scanner", "slot": "Head", "effect": "Darkvision, reveals traps"}
        ],
        "inventory": ["Monofilament Blade", "Smoke Grenades"]
    }
})

# Synchronize existing session/saved Ren data with canonical QA Vanguard sheet
if "companions" in p and "Ren" in p["companions"]:
    r_sheet = p["companions"]["Ren"]
    if r_sheet.get("archetype") != "QA Vanguard" or r_sheet.get("max_hp") != 35:
        r_sheet["archetype"] = "QA Vanguard"
        r_sheet["max_hp"] = 35
        r_sheet["hp"] = min(35, r_sheet.get("hp", 35))
        r_sheet["ac"] = 16
        r_sheet["status"] = "Vigilant and operational"
        r_sheet["active_grafts"] = [
            {"name": "Sub-Dermal Optical Scanner", "slot": "Head", "effect": "Darkvision, reveals traps"}
        ]
        r_sheet["inventory"] = ["Monofilament Blade", "Smoke Grenades"]

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
                
    with st.expander("🤖 Party Companions", expanded=True):
        companions = player.get("companions", {})
        if not companions:
            st.caption("No party companions registered.")
        else:
            for c_id, c_data in companions.items():
                c_name = c_data.get("name", c_id)
                c_hp = c_data.get("hp", 35)
                c_max_hp = c_data.get("max_hp", 35)
                c_ac = c_data.get("ac", 16)
                c_archetype = c_data.get("archetype", "Vanguard")
                c_status = c_data.get("status", "Active")
                st.markdown(f"**{c_name}** ({c_archetype}) — AC: {c_ac}")
                c_hp_pct = max(0.0, min(1.0, c_hp / max(1, c_max_hp)))
                st.progress(c_hp_pct, text=f"HP: {c_hp} / {c_max_hp}")
                st.caption(f"Status: {c_status}")
                if "active_grafts" in c_data:
                    st.markdown("**Active Grafts:**")
                    for g in c_data["active_grafts"]:
                        st.caption(f"- 🔧 {g.get('name')} [{g.get('slot')}]: {g.get('effect')}")
                if "inventory" in c_data:
                    st.markdown("**Inventory:**")
                    for itm in c_data["inventory"]:
                        st.caption(f"- 🎒 {itm}")
                st.divider()

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

# --- MAIN UI: THE CHAT WINDOW ---
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
