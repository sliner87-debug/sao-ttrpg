"""
backend/sillytavern_engine.py
===============================================================================
SillyTavern Community Feature Integration Engine for The Fractured Overlay (V2)
===============================================================================
Integrates the 6 most beloved SillyTavern community features directly into the
custom multi-subagent LitRPG web application:
  1. Keyword-Triggered World Info / Lorebook Engine (0-token dormant until triggered,
     token-budgeted, priority-sorted, compatible with SillyTavern V2 Worldbooks).
  2. SillyTavern V2 Character Card (.png tEXt 'chara' chunk & .json) Importer & Exporter
     with automatic conversion to/from autonomous SubAgent Personas & Party Sheets.
  3. Message Swiping (◀ 1/N ▶), Inline Prose Editing, State-Safe Turn Rewind,
     and Chat Timeline Branching.
  4. Author's Note / Director's Note with @Depth Injection (spliced at configurable
     chat history depth before the latest turn) & Live Prompt/Token Inspector.
  5. Narrative Style Presets (Grimdark Sensory Engine, Cardinal Balanced, Tavern RP,
     Fast Dungeon Crawler) & Multi-Backend LLM Switcher (Gemini Cloud + Local/Cloud
     OpenAI/KoboldCpp GGUF endpoints).
  6. Visual Novel (VN) Expression Detection, Regex Dialogue/Telepathy Colorization,
     and Quick-Reply (QR) Macro Bar.
"""

import base64
import copy
import html
import io
import json
import os
import re
import struct
import time
import urllib.request
import zlib
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRESETS_DIR = os.path.join(BASE_DIR, "presets")
ENTITIES_DIR = os.path.join(BASE_DIR, "Entities")
PARTY_DIR = os.path.join(BASE_DIR, "Party")
AVATARS_DIR = os.path.join(BASE_DIR, "assets", "avatars")


# ==============================================================================
# 1. NARRATIVE STYLE PRESETS & SAMPLER PROFILES
# ==============================================================================

DEFAULT_NARRATIVE_PRESETS: Dict[str, Dict[str, Any]] = {
    "grimdark_sensory": {
        "id": "grimdark_sensory",
        "name": "🩸 Grimdark Sensory Engine (SillyTavern Master)",
        "temperature": 0.85,
        "top_p": 0.95,
        "min_p": 0.06,
        "repetition_penalty": 1.12,
        "max_output_tokens": 1200,
        "style_directive": (
            "[NARRATIVE PRESET: GRIMDARK SENSORY ENGINE]\n"
            "- Write in a visceral, grounded, dark-fantasy literary style (inspired by Berserk, Dark Souls, and Grimgar).\n"
            "- Emphasize physical weight, iron, rust, cold stone, ozone, copper blood, and strained breathing.\n"
            "- BANNED CLICHÉS: Never use 'a testament to', 'shivers down their spine', 'little did they know', "
            "'a symphony of', or 'couldn't help but'.\n"
            "- Show physical consequences through action and sensory detail rather than melodramatic exposition."
        ),
        "default_authors_note": (
            "[Author's Note: Maintain gritty, tactile dark-fantasy realism. Ground every action in physical mass, "
            "terrain hazards, and companion banter. NEVER speak or decide for the player character; stop immediately "
            "at the next tactical or conversational decision point.]"
        ),
    },
    "cardinal_balanced": {
        "id": "cardinal_balanced",
        "name": "⚖️ Cardinal Balanced LitRPG (Default V2)",
        "temperature": 0.45,
        "top_p": 0.90,
        "min_p": 0.05,
        "repetition_penalty": 1.08,
        "max_output_tokens": 1024,
        "style_directive": (
            "[NARRATIVE PRESET: CARDINAL BALANCED LITRPG]\n"
            "- Balance high-stakes dark-anime Sword Art Online atmosphere with crisp tabletop tactical clarity.\n"
            "- Clearly telegraph enemy stances, environmental hazards, and companion positioning.\n"
            "- Stop cleanly after resolving the current step so the player retains full agency."
        ),
        "default_authors_note": (
            "[Author's Note: Resolve only the immediate step of the player's action. Highlight companion SubAgent "
            "contributions and yield control at any scene threshold or choice.]"
        ),
    },
    "tavern_roleplay": {
        "id": "tavern_roleplay",
        "name": "🎭 Character & Tavern Roleplay (Dialogue & Banter Focus)",
        "temperature": 0.90,
        "top_p": 0.96,
        "min_p": 0.05,
        "repetition_penalty": 1.10,
        "max_output_tokens": 1300,
        "style_directive": (
            "[NARRATIVE PRESET: CHARACTER & TAVERN ROLEPLAY]\n"
            "- Prioritize rich character voice, micro-expressions, body language, and multi-layered companion banter.\n"
            "- Contrast spoken dialogue with private telepathic or Serpent-Script neural whispers where appropriate.\n"
            "- Let NPCs and companions react emotionally to the player's tone, reputation, and appearance."
        ),
        "default_authors_note": (
            "[Author's Note: Slow down the pacing for immersive dialogue and character interaction. Give companions "
            "distinct vocal quirks and emotional reactions. End on an open line of dialogue or reaction prompt.]"
        ),
    },
    "dungeon_blitz": {
        "id": "dungeon_blitz",
        "name": "⚡ High-Speed Dungeon Crawler (Concise & Punchy)",
        "temperature": 0.35,
        "top_p": 0.85,
        "min_p": 0.05,
        "repetition_penalty": 1.05,
        "max_output_tokens": 750,
        "style_directive": (
            "[NARRATIVE PRESET: HIGH-SPEED DUNGEON CRAWLER]\n"
            "- Keep prose tight, kinetic, and fast-paced (2-3 punchy paragraphs maximum).\n"
            "- Focus on immediate combat geometry, strike impact, loot drops, and room exits."
        ),
        "default_authors_note": (
            "[Author's Note: Keep narration concise and kinetic. Focus on immediate combat impact and tactical options.]"
        ),
    },
}

DEFAULT_QUICK_REPLIES: List[Dict[str, str]] = [
    {
        "label": "🔍 Scan Room & Traps",
        "icon": "🔍",
        "prompt": "Carefully scan the room, floor integrity, and shadows for hidden traps, weakpoints, or salvageable loot.",
    },
    {
        "label": "🗣️ Consult Party",
        "icon": "🗣️",
        "prompt": "Turn to my active companions and ask for their tactical readout and honest opinion on our next move.",
    },
    {
        "label": "🛡️ Hold & Observe",
        "icon": "🛡️",
        "prompt": "Raise my guard in a defensive stance, observe the environment closely, and let my companions position themselves.",
    },
    {
        "label": "🧪 Field Triage & Loot",
        "icon": "🧪",
        "prompt": "Check our party's vitals and equipment durability, and inspect any fallen wreckage or containers nearby.",
    },
    {
        "label": "🚪 Advance Slowly",
        "icon": "🚪",
        "prompt": "Advance cautiously to the next threshold with weapons ready, stopping immediately at the doorway to survey what lies ahead.",
    },
]


def get_default_st_settings() -> Dict[str, Any]:
    """Returns default SillyTavern integration configuration stored in session_state / player settings."""
    return {
        "preset_id": "grimdark_sensory",
        "temperature": 0.85,
        "top_p": 0.95,
        "max_output_tokens": 1200,
        "backend_mode": "gemini",  # "gemini" or "openai_compat"
        "gemini_model": "gemini-3.8-flash",
        "openai_endpoint": "http://127.0.0.1:5001/v1",
        "openai_api_key": "sk-local",
        "openai_model": "local-gguf-model",
        "authors_note": DEFAULT_NARRATIVE_PRESETS["grimdark_sensory"]["default_authors_note"],
        "authors_note_depth": 1,
        "authors_note_role": "system",
        "chat_history_depth": 6,
        "worldbook_enabled": True,
        "worldbook_token_budget": 1200,
        "worldbook_scan_depth": 4,
        "active_worldbooks": ["Fractured_Reality_V2_Master_Worldbook.json"],
        "custom_worldbook_entries": [],
        "vn_sprites_enabled": True,
        "regex_coloring_enabled": True,
        "quick_replies_enabled": True,
        "custom_quick_replies": [],
        "last_prompt_inspection": {},
    }


def ensure_st_settings(player_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Ensures player_state has a normalized `st_settings` dictionary and returns it."""
    defaults = get_default_st_settings()
    if not isinstance(player_state, dict):
        return defaults
    existing = player_state.get("st_settings")
    if not isinstance(existing, dict):
        player_state["st_settings"] = copy.deepcopy(defaults)
        return player_state["st_settings"]
    for k, v in defaults.items():
        if k not in existing:
            existing[k] = copy.deepcopy(v)
    return existing


# ==============================================================================
# 2. KEYWORD-TRIGGERED WORLDBOOK / LOREBOOK ENGINE (0-TOKEN DORMANT)
# ==============================================================================

def estimate_tokens(text: str) -> int:
    """Fast heuristic token estimator (~4 chars per token, matching SillyTavern's budgeter)."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def list_available_worldbook_files(base_dir: str = BASE_DIR) -> List[str]:
    """Lists all SillyTavern Worldbook JSON files in `presets/`."""
    p_dir = os.path.join(base_dir, "presets")
    if not os.path.exists(p_dir):
        return []
    wb_files = []
    for fname in sorted(os.listdir(p_dir)):
        if not fname.lower().endswith(".json"):
            continue
        low = fname.lower()
        if any(k in low for k in ["worldbook", "lorebook", "fr_factions", "fr_mechanics", "fr_ruins"]):
            wb_files.append(fname)
    return wb_files


def load_worldbook_entries(
    worldbook_filenames: Optional[List[str]] = None,
    custom_entries: Optional[List[Dict[str, Any]]] = None,
    base_dir: str = BASE_DIR,
) -> List[Dict[str, Any]]:
    """
    Loads and normalizes entries from one or more SillyTavern V2 Worldbook JSON files
    plus any user-defined custom entries.
    """
    if worldbook_filenames is None:
        worldbook_filenames = ["Fractured_Reality_V2_Master_Worldbook.json"]

    normalized: List[Dict[str, Any]] = []
    seen_comments = set()

    for fname in worldbook_filenames:
        fpath = fname if os.path.isabs(fname) else os.path.join(base_dir, "presets", fname)
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            raw_entries = data.get("entries", {})
            if isinstance(raw_entries, dict):
                entries_iter = list(raw_entries.values())
            elif isinstance(raw_entries, list):
                entries_iter = raw_entries
            else:
                entries_iter = []

            for entry in entries_iter:
                if not isinstance(entry, dict):
                    continue
                if entry.get("disable", False) or not entry.get("enabled", True):
                    continue
                content = str(entry.get("content", "")).strip()
                if not content:
                    continue
                comment = str(entry.get("comment", entry.get("uid", "Lore Entry"))).strip()
                dedup_key = f"{comment}::{content[:60]}"
                if dedup_key in seen_comments:
                    continue
                seen_comments.add(dedup_key)

                keys = [str(k).strip() for k in (entry.get("key") or []) if str(k).strip()]
                secondary_keys = [str(k).strip() for k in (entry.get("keysecondary") or []) if str(k).strip()]
                normalized.append({
                    "uid": entry.get("uid", len(normalized)),
                    "comment": comment,
                    "keys": keys,
                    "secondary_keys": secondary_keys,
                    "selective": bool(entry.get("selective", False)),
                    "constant": bool(entry.get("constant", False)),
                    "order": int(entry.get("order", 100) or 100),
                    "position": int(entry.get("position", 0) or 0),
                    "depth": int(entry.get("depth", 4) or 4),
                    "content": content,
                    "tokens": estimate_tokens(content),
                    "source": os.path.basename(fpath),
                })
        except Exception as e:
            print(f"[WORLDBOOK] Error loading {fpath}: {e}", flush=True)

    if isinstance(custom_entries, list):
        for idx, c_ent in enumerate(custom_entries):
            if not isinstance(c_ent, dict) or not c_ent.get("enabled", True):
                continue
            content = str(c_ent.get("content", "")).strip()
            if not content:
                continue
            keys = c_ent.get("keys") or c_ent.get("key") or []
            if isinstance(keys, str):
                keys = [k.strip() for k in keys.split(",") if k.strip()]
            normalized.append({
                "uid": f"custom_{idx}",
                "comment": str(c_ent.get("comment", f"Custom Lore #{idx + 1}")),
                "keys": keys,
                "secondary_keys": [],
                "selective": False,
                "constant": bool(c_ent.get("constant", False)),
                "order": int(c_ent.get("order", 150) or 150),
                "position": 0,
                "depth": 2,
                "content": content,
                "tokens": estimate_tokens(content),
                "source": "Custom User Lorebook",
            })

    # Sort highest insertion order first (matching SillyTavern priority)
    normalized.sort(key=lambda x: x.get("order", 100), reverse=True)
    return normalized


def _keyword_matches(keyword: str, haystack_lower: str) -> bool:
    """
    Matches a SillyTavern Worldbook keyword against the scan buffer.
    Short keywords (<= 3 chars) require word boundaries to avoid false positives;
    longer phrases match case-insensitively.
    """
    kw = keyword.strip().lower()
    if not kw:
        return False
    if len(kw) <= 3:
        return bool(re.search(rf"\b{re.escape(kw)}\b", haystack_lower))
    return kw in haystack_lower


def scan_and_inject_worldbook(
    player_action: str = "",
    messages: Optional[List[Dict[str, Any]]] = None,
    player_state: Optional[Dict[str, Any]] = None,
    visible_room: Optional[Dict[str, Any]] = None,
    base_dir: str = BASE_DIR,
) -> Dict[str, Any]:
    """
    Scans recent chat messages, player action, location, and active entities against
    loaded SillyTavern Worldbooks. Enforces the configured token budget and returns:
      {
        "formatted_block": str,
        "triggered_entries": List[Dict],
        "total_tokens": int,
        "token_budget": int,
        "total_available_entries": int,
      }
    """
    st_cfg = ensure_st_settings(player_state)
    if not st_cfg.get("worldbook_enabled", True):
        return {
            "formatted_block": "",
            "triggered_entries": [],
            "total_tokens": 0,
            "token_budget": int(st_cfg.get("worldbook_token_budget", 1200)),
            "total_available_entries": 0,
        }

    budget = int(st_cfg.get("worldbook_token_budget", 1200) or 1200)
    scan_depth = int(st_cfg.get("worldbook_scan_depth", 4) or 4)
    active_wbs = st_cfg.get("active_worldbooks") or ["Fractured_Reality_V2_Master_Worldbook.json"]
    custom_entries = st_cfg.get("custom_worldbook_entries") or []

    all_entries = load_worldbook_entries(active_wbs, custom_entries, base_dir=base_dir)

    # Assemble scan buffer from recent chat history + current action + location + entities
    scan_parts: List[str] = []
    if player_action:
        scan_parts.append(str(player_action))
    if isinstance(player_state, dict):
        if player_state.get("location"):
            scan_parts.append(str(player_state["location"]))
        if player_state.get("race"):
            scan_parts.append(str(player_state["race"]))
        if player_state.get("class"):
            scan_parts.append(str(player_state["class"]))
    if isinstance(visible_room, dict):
        env = visible_room.get("environment", {})
        if isinstance(env, dict):
            scan_parts.append(str(env.get("location", "")))
            scan_parts.append(str(env.get("description", "")))
        for ent in visible_room.get("entities", []) or []:
            if isinstance(ent, dict):
                scan_parts.append(str(ent.get("name", "")))
                scan_parts.append(str(ent.get("id", "")))
    if isinstance(messages, list) and scan_depth > 0:
        for msg in messages[-scan_depth:]:
            if isinstance(msg, dict) and msg.get("content"):
                scan_parts.append(str(msg["content"])[:1500])

    haystack_lower = "\n".join(scan_parts).lower()

    triggered: List[Dict[str, Any]] = []
    used_tokens = 0

    for entry in all_entries:
        matched_key = None
        if entry.get("constant"):
            matched_key = "[Constant]"
        else:
            for k in entry.get("keys", []):
                if _keyword_matches(k, haystack_lower):
                    matched_key = k
                    break
            if matched_key and entry.get("selective") and entry.get("secondary_keys"):
                sec_ok = any(_keyword_matches(sk, haystack_lower) for sk in entry["secondary_keys"])
                if not sec_ok:
                    matched_key = None

        if not matched_key:
            continue

        entry_tokens = entry.get("tokens", estimate_tokens(entry["content"]))
        if used_tokens + entry_tokens > budget:
            continue

        used_tokens += entry_tokens
        triggered.append({
            "uid": entry["uid"],
            "comment": entry["comment"],
            "matched_key": matched_key,
            "tokens": entry_tokens,
            "order": entry["order"],
            "source": entry["source"],
            "content": entry["content"],
        })

    if not triggered:
        return {
            "formatted_block": "",
            "triggered_entries": [],
            "total_tokens": 0,
            "token_budget": budget,
            "total_available_entries": len(all_entries),
        }

    blocks = [
        f"### 📚 [SILLYTAVERN WORLD INFO / KEYWORD-TRIGGERED LOREBOOK ({len(triggered)} entries | {used_tokens}/{budget} tokens)]"
    ]
    for t in triggered:
        blocks.append(f"#### [{t['comment']}] (Triggered by: `{t['matched_key']}`)\n{t['content']}")

    return {
        "formatted_block": "\n\n".join(blocks),
        "triggered_entries": triggered,
        "total_tokens": used_tokens,
        "token_budget": budget,
        "total_available_entries": len(all_entries),
    }


# ==============================================================================
# 3. AUTHOR'S NOTE (@DEPTH INJECTION) & RECENT CHAT HISTORY FORMATTING
# ==============================================================================

def build_chat_history_with_authors_note(
    messages: Optional[List[Dict[str, Any]]],
    player_state: Optional[Dict[str, Any]] = None,
    current_action: str = "",
) -> Tuple[str, Dict[str, Any]]:
    """
    Builds a recent chat history window for the GM engine and splices the
    SillyTavern Author's Note / Director's Note at exact `@Depth N` from the bottom.
     Also returns metadata for the Prompt Inspector.
    """
    st_cfg = ensure_st_settings(player_state)
    max_turns = int(st_cfg.get("chat_history_depth", 6) or 6)
    authors_note = str(st_cfg.get("authors_note", "")).strip()
    an_depth = max(0, int(st_cfg.get("authors_note_depth", 1) or 1))
    an_role = str(st_cfg.get("authors_note_role", "system")).upper()

    preset_id = st_cfg.get("preset_id", "grimdark_sensory")
    preset = DEFAULT_NARRATIVE_PRESETS.get(preset_id, DEFAULT_NARRATIVE_PRESETS["grimdark_sensory"])
    style_directive = preset.get("style_directive", "")

    history_lines: List[str] = []
    if isinstance(messages, list) and max_turns > 0:
        # Exclude the just-appended user message if it duplicates current_action
        tail = messages[-(max_turns + 1):]
        for m in tail:
            if not isinstance(m, dict):
                continue
            role = m.get("role", "assistant")
            raw_c = str(m.get("content", "")).strip()
            if not raw_c:
                continue
            if role == "user" and current_action and raw_c == current_action.strip():
                continue
            # Trim long messages so history stays compact
            clipped = raw_c if len(raw_c) <= 900 else (raw_c[:900] + " ... [truncated]")
            speaker = "PLAYER" if role == "user" else "GM / SYSTEM"
            history_lines.append(f"[{speaker}]: {clipped}")

    # Splice Author's Note at @Depth N (counting backwards from the end of history_lines)
    if authors_note:
        an_formatted = f"[{an_role} NOTE @Depth {an_depth}]: {authors_note}"
        insert_idx = max(0, len(history_lines) - an_depth)
        history_lines.insert(insert_idx, an_formatted)

    blocks: List[str] = []
    if style_directive:
        blocks.append(style_directive)
    if history_lines:
        blocks.append(
            "### 💬 [RECENT CHAT HISTORY & @DEPTH AUTHOR'S NOTE]\n" + "\n\n".join(history_lines)
        )

    combined = "\n\n".join(blocks)
    meta = {
        "preset_id": preset_id,
        "preset_name": preset.get("name"),
        "temperature": float(st_cfg.get("temperature", preset.get("temperature", 0.7))),
        "top_p": float(st_cfg.get("top_p", preset.get("top_p", 0.95))),
        "authors_note": authors_note,
        "authors_note_depth": an_depth,
        "history_messages_included": len(history_lines),
        "tokens": estimate_tokens(combined),
    }
    return combined, meta


# ==============================================================================
# 4. SILLYTAVERN V2 CHARACTER CARD (.PNG & .JSON) IMPORTER & EXPORTER
# ==============================================================================

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def extract_chara_json_from_png_bytes(png_bytes: bytes) -> Optional[Dict[str, Any]]:
    """
    Reads a SillyTavern V2 Character Card `.png` byte stream and extracts the
    base64-encoded `chara` (or `ccv3`) JSON payload from PNG `tEXt` or `iTXt` chunks.
    """
    if not png_bytes or len(png_bytes) < 8 or png_bytes[:8] != PNG_SIGNATURE:
        return None

    offset = 8
    length = len(png_bytes)
    while offset + 8 <= length:
        chunk_len = struct.unpack(">I", png_bytes[offset:offset + 4])[0]
        chunk_type = png_bytes[offset + 4:offset + 8].decode("latin1", errors="ignore")
        chunk_data = png_bytes[offset + 8:offset + 8 + chunk_len]
        offset += 12 + chunk_len

        if chunk_type == "tEXt" and b"\x00" in chunk_data:
            keyword_bytes, text_bytes = chunk_data.split(b"\x00", 1)
            keyword = keyword_bytes.decode("latin1", errors="ignore").strip().lower()
            if keyword in ("chara", "ccv3"):
                try:
                    b64_str = text_bytes.decode("utf-8", errors="ignore").strip()
                    decoded = base64.b64decode(b64_str).decode("utf-8")
                    return json.loads(decoded)
                except Exception:
                    pass
        elif chunk_type == "iTXt" and b"\x00" in chunk_data:
            parts = chunk_data.split(b"\x00", 5)
            if len(parts) >= 6:
                keyword = parts[0].decode("latin1", errors="ignore").strip().lower()
                if keyword in ("chara", "ccv3"):
                    try:
                        b64_str = parts[-1].decode("utf-8", errors="ignore").strip()
                        decoded = base64.b64decode(b64_str).decode("utf-8")
                        return json.loads(decoded)
                    except Exception:
                        pass
        elif chunk_type == "IEND":
            break
    return None


def embed_chara_json_into_png_bytes(png_bytes: bytes, card_dict: Dict[str, Any]) -> bytes:
    """
    Embeds a `chara_card_v2` JSON dictionary into a PNG byte stream as a standard
    base64-encoded `tEXt` (`chara`) chunk immediately before `IEND`.
    If `png_bytes` is not a valid PNG, converts it via PIL first or generates a fallback PNG canvas.
    """
    valid_png = png_bytes
    if not valid_png or len(valid_png) < 8 or valid_png[:8] != PNG_SIGNATURE:
        try:
            from PIL import Image, ImageDraw
            if valid_png:
                with Image.open(io.BytesIO(valid_png)) as im:
                    buf = io.BytesIO()
                    im.convert("RGBA").save(buf, format="PNG")
                    valid_png = buf.getvalue()
            else:
                img = Image.new("RGBA", (512, 768), (18, 24, 38, 255))
                draw = ImageDraw.Draw(img)
                c_name = card_dict.get("data", {}).get("name") or card_dict.get("name", "Companion")
                draw.rectangle([20, 20, 492, 748], outline=(0, 212, 255, 255), width=3)
                draw.text((48, 360), f"CARDINAL V2 CARD\n{c_name}", fill=(255, 255, 255, 255))
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                valid_png = buf.getvalue()
        except Exception:
            # Minimal 1x1 valid PNG fallback
            valid_png = base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
            )

    json_bytes = json.dumps(card_dict, ensure_ascii=False).encode("utf-8")
    b64_payload = base64.b64encode(json_bytes)
    chunk_data = b"chara\x00" + b64_payload
    chunk_type = b"tEXt"
    crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
    text_chunk = struct.pack(">I", len(chunk_data)) + chunk_type + chunk_data + struct.pack(">I", crc)

    # Strip any old 'chara' tEXt chunk and insert the new one before IEND
    out_chunks = [PNG_SIGNATURE]
    offset = 8
    length = len(valid_png)
    inserted = False
    while offset + 8 <= length:
        c_len = struct.unpack(">I", valid_png[offset:offset + 4])[0]
        c_type = valid_png[offset + 4:offset + 8]
        c_data = valid_png[offset + 8:offset + 8 + c_len]
        c_crc = valid_png[offset + 8 + c_len:offset + 12 + c_len]
        offset += 12 + c_len

        if c_type == b"tEXt" and c_data.startswith(b"chara\x00"):
            continue
        if c_type == b"IEND" and not inserted:
            out_chunks.append(text_chunk)
            inserted = True
        out_chunks.append(struct.pack(">I", c_len) + c_type + c_data + c_crc)

    if not inserted:
        out_chunks.append(text_chunk)

    return b"".join(out_chunks)


def import_sillytavern_card_to_game(
    raw_bytes: bytes,
    filename: str = "card.png",
    player_state: Optional[Dict[str, Any]] = None,
    recruit_immediately: bool = True,
    base_dir: str = BASE_DIR,
) -> Dict[str, Any]:
    """
    Imports a SillyTavern V2 `.png` or `.json` Character Card into the website:
      1. Extracts the V2 metadata (`name`, `description`, `personality`, `scenario`,
         `first_mes`, `mes_example`, `system_prompt`, `alternate_greetings`, `tags`).
      2. Saves the `.png` avatar to `assets/avatars/<slug>_card.png` if importing a PNG.
      3. Creates/updates `Entities/companion_<slug>.json` (for isolated SubAgent perception)
         and `Party/companion_<slug>.json` (for tactical stances, HP, AC, and loadout).
      4. Registers the character in `player_state["companions"]` so they can immediately
         join the active 4-Vanguard party!
    """
    card_json: Optional[Dict[str, Any]] = None
    is_png = filename.lower().endswith(".png") or (raw_bytes[:8] == PNG_SIGNATURE)

    if is_png:
        card_json = extract_chara_json_from_png_bytes(raw_bytes)
        if not card_json:
            # Check if a matching .json file exists in presets/
            stem = os.path.splitext(os.path.basename(filename))[0]
            candidate_json = os.path.join(base_dir, "presets", f"{stem}.json")
            if os.path.exists(candidate_json):
                with open(candidate_json, "r", encoding="utf-8") as f:
                    card_json = json.load(f)
    else:
        try:
            card_json = json.loads(raw_bytes.decode("utf-8"))
        except Exception as e:
            return {"success": False, "message": f"Invalid JSON character card: {e}"}

    if not isinstance(card_json, dict):
        return {
            "success": False,
            "message": "No SillyTavern V2 'chara' metadata chunk found in this PNG image.",
        }

    data = card_json.get("data") if isinstance(card_json.get("data"), dict) else card_json
    name = str(data.get("name") or os.path.splitext(filename)[0]).strip()
    if not name:
        name = "Imported Companion"

    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "imported_companion"
    entity_id = slug if slug.startswith("companion_") else f"companion_{slug}"
    short_name = name.split()[0].strip()

    description = str(data.get("description", "")).strip()
    personality = str(data.get("personality", "Tactical, expressive, self-aware.")).strip()
    scenario = str(data.get("scenario", "")).strip()
    first_mes = str(data.get("first_mes", "")).strip()
    mes_example = str(data.get("mes_example", "")).strip()
    sys_prompt = str(data.get("system_prompt", "")).strip()
    alt_greetings = data.get("alternate_greetings") if isinstance(data.get("alternate_greetings"), list) else []
    tags = data.get("tags") if isinstance(data.get("tags"), list) else []

    # Persist PNG portrait if provided
    avatar_rel_path = None
    if is_png and len(raw_bytes) > 64:
        os.makedirs(os.path.join(base_dir, "assets", "avatars"), exist_ok=True)
        avatar_rel_path = f"assets/avatars/{slug}_st_card.png"
        with open(os.path.join(base_dir, avatar_rel_path), "wb") as img_f:
            img_f.write(raw_bytes)
    else:
        # Check if presets/ has a matching PNG
        for cand in [f"{name}.png", f"{name.replace(' ', '_')}.png", f"{short_name}.png"]:
            cand_p = os.path.join(base_dir, "presets", cand)
            if os.path.exists(cand_p):
                avatar_rel_path = f"presets/{cand}"
                break

    # Build SubAgent Persona Schema (`Entities/companion_<slug>.json`)
    behavior_parts = [
        f"You are {name}.",
        sys_prompt if sys_prompt else "",
        f"Character Description: {description[:1200]}" if description else "",
        f"Scenario Context: {scenario[:500]}" if scenario else "",
        f"Example Dialogue Style:\n{mes_example[:800]}" if mes_example else "",
    ]
    behavior_prompt = "\n".join(p for p in behavior_parts if p).strip()

    persona_payload = {
        "id": entity_id,
        "name": name,
        "species_or_type": ", ".join(str(t) for t in tags[:3]) if tags else "SillyTavern V2 Character",
        "role": "companion",
        "backstory_interview": description or scenario or f"Awakened via SillyTavern V2 Character Card ({name}).",
        "personality": personality or "Expressive, adaptive, and autonomous.",
        "quirks": [
            "Speaks in the exact voice defined by their SillyTavern V2 Character Card",
            *(tags[:3] if tags else ["Autonomous Vanguard Companion"]),
        ],
        "dreams_and_desires": scenario or "Survive the Fractured Overlay alongside the party.",
        "fears_and_dreads": "Permadeath and losing neural synchronization.",
        "tactical_style": "Adaptive V2 Persona Combat & Roleplay",
        "behavior_prompt": behavior_prompt,
        "sillytavern_v2_data": {
            "first_mes": first_mes,
            "alternate_greetings": alt_greetings,
            "mes_example": mes_example,
            "tags": tags,
            "creator_notes": str(data.get("creator_notes", "")),
        },
        "avatar": avatar_rel_path,
    }

    os.makedirs(os.path.join(base_dir, "Entities"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "Party"), exist_ok=True)
    with open(os.path.join(base_dir, "Entities", f"{entity_id}.json"), "w", encoding="utf-8") as ef:
        json.dump(persona_payload, ef, indent=4)

    # Build Party Mechanical Sheet (`Party/companion_<slug>.json`)
    party_sheet = {
        "id": entity_id,
        "name": name,
        "short_name": short_name,
        "full_name": name,
        "role": ", ".join(str(t) for t in tags[:2]) if tags else "SillyTavern V2 Vanguard",
        "class": tags[0].title() if tags else "Vanguard Specialist",
        "title": tags[0].title() if tags else "Vanguard Specialist",
        "level": 3,
        "hp": 42,
        "max_hp": 42,
        "ac": 16,
        "xp": 450,
        "next_level_xp": 900,
        "stance": "vanguard_assault",
        "morale": "Resolute",
        "affinity": 45,
        "affinity_tier": "Ally",
        "recruited": bool(recruit_immediately),
        "active": False,
        "avatar": avatar_rel_path,
        "bio": (description[:360] + "...") if len(description) > 360 else (description or personality),
        "behavior_prompt": behavior_prompt,
        "first_mes": first_mes,
        "alternate_greetings": alt_greetings,
        "equipped": {
            "main_hand": "Signature V2 Relic Weapon (1d10+3 Arcane/Physical)",
            "off_hand": "Resonance Ward Focus (+2 AC)",
            "chest": "Traveler's Aether-Weave Coat (DR 1)",
        },
        "stances": {
            "vanguard_assault": {
                "name": "Signature Assault",
                "label": "⚔️ Signature V2 Assault",
                "tag": f"[{short_name.upper()} ASSAULT]",
                "tactical_effect": f"{name} executes aggressive signature strikes (2d8+4 DMG) and flanks the primary target.",
                "desc": "Offensive signature stance.",
            },
            "tactical_support": {
                "name": "Overwatch & Banter",
                "label": "🛡️ Overwatch & Support",
                "tag": f"[{short_name.upper()} SUPPORT]",
                "tactical_effect": f"{name} covers the player's blind spot (+2 Party AC) and provides tactical reconnaissance.",
                "desc": "Defensive support stance.",
            },
        },
        "dual_tech_id": f"st_combo_{slug}",
        "dual_tech_name": f"{short_name}'s Resonance Strike",
    }

    with open(os.path.join(base_dir, "Party", f"{entity_id}.json"), "w", encoding="utf-8") as pf:
        json.dump(party_sheet, pf, indent=4)

    # Register in player_state["companions"] if provided
    if isinstance(player_state, dict):
        comps = player_state.setdefault("companions", {})
        if isinstance(comps, dict):
            # Activate if fewer than 3 active companions
            active_count = sum(
                1 for c in comps.values() if isinstance(c, dict) and c.get("active", False)
            )
            if recruit_immediately and active_count < 3:
                party_sheet["active"] = True
            comps[short_name] = party_sheet

    return {
        "success": True,
        "name": name,
        "short_name": short_name,
        "entity_id": entity_id,
        "avatar": avatar_rel_path,
        "first_mes": first_mes,
        "alternate_greetings": alt_greetings,
        "party_sheet": party_sheet,
        "message": f"Imported SillyTavern V2 Card '{name}' as autonomous SubAgent `{entity_id}`!",
    }


def export_character_to_sillytavern_v2(
    char_data: Dict[str, Any],
    is_player: bool = False,
    base_dir: str = BASE_DIR,
) -> Tuple[Dict[str, Any], bytes]:
    """
    Exports any website Player Character or SubAgent Companion into a spec-compliant
    SillyTavern `chara_card_v2` JSON dictionary AND a `.png` Character Card with
    embedded `tEXt` (`chara`) metadata!
    """
    name = str(char_data.get("name", "Survivor")).strip()
    role_or_class = str(char_data.get("class") or char_data.get("role") or "Vanguard").strip()
    race = str(char_data.get("race") or char_data.get("species_or_type") or "Human").strip()
    level = int(char_data.get("level", 1) or 1)
    hp = char_data.get("hp", 100)
    max_hp = char_data.get("max_hp", 100)

    eq = char_data.get("equipped", {})
    eq_lines = [f"- {k.title()}: {v}" for k, v in eq.items() if v and v != "None"] if isinstance(eq, dict) else []
    bio = str(char_data.get("bio") or char_data.get("backstory_interview") or char_data.get("locked_avatar_anatomy") or "").strip()
    behavior = str(char_data.get("behavior_prompt") or "").strip()

    description = (
        f"[Character: {name} | Lineage: {race} | Class: {role_or_class} | Level: {level} | Vitals: {hp}/{max_hp} HP]\n\n"
        f"### Overview & Anatomy\n{bio}\n\n"
        f"### Equipped Loadout\n" + ("\n".join(eq_lines) if eq_lines else "- Standard Survivor Gear")
    )

    first_mes = str(
        char_data.get("first_mes")
        or (
            f"*{name} adjusts their gear as the cerulean telemetry of the Cardinal System hums across the chamber.*\n\n"
            f"\"Neural link stabilized. Let's check our perimeter before the next breach wave hits.\""
        )
    )

    card_v2 = {
        "spec": "chara_card_v2",
        "spec_version": "2.0",
        "data": {
            "name": name,
            "description": description,
            "personality": str(char_data.get("personality") or f"Level {level} {race} {role_or_class}. Resolute, tactical, self-aware."),
            "scenario": str(char_data.get("location") or "Sector 1: Washington Borough, NJ — The Fractured Overlay"),
            "first_mes": first_mes,
            "mes_example": str(char_data.get("sillytavern_v2_data", {}).get("mes_example", "")),
            "creator_notes": "Exported from The Fractured Overlay V2 (Autonomous Multi-SubAgent TTRPG Website).",
            "system_prompt": behavior,
            "post_history_instructions": (
                f"[Stay strictly in character as {name} ({race} {role_or_class}). Never speak or act for {{{{user}}}}.]"
            ),
            "alternate_greetings": list(char_data.get("alternate_greetings") or []),
            "tags": ["LitRPG", "Fractured_Reality_V2", race, role_or_class, "SubAgent" if not is_player else "Player_Avatar"],
            "creator": "The Fractured Overlay V2",
            "character_version": "2.0",
            "extensions": {
                "fractured_overlay_v2": {
                    "is_player": is_player,
                    "stats": char_data.get("stats", {}),
                    "skills": char_data.get("skills", {}),
                    "equipped": eq,
                }
            },
        },
    }

    # Locate best portrait image to embed into PNG
    raw_img_bytes = None
    candidate_paths = []
    if char_data.get("avatar_image_path"):
        candidate_paths.append(char_data["avatar_image_path"])
    if char_data.get("avatar"):
        candidate_paths.append(char_data["avatar"])
    short_n = name.split()[0]
    candidate_paths.extend([
        f"presets/{name}.png",
        f"presets/{name.replace(' ', '_')}.png",
        f"presets/{short_n}.png",
        f"assets/avatars/{name.lower()}_avatar.png",
        f"assets/avatars/{short_n.lower()}_avatar.png",
    ])
    for cp in candidate_paths:
        abs_cp = cp if os.path.isabs(cp) else os.path.join(base_dir, cp)
        if os.path.exists(abs_cp):
            try:
                with open(abs_cp, "rb") as f:
                    raw_img_bytes = f.read()
                break
            except Exception:
                pass

    png_with_metadata = embed_chara_json_into_png_bytes(raw_img_bytes or b"", card_v2)
    return card_v2, png_with_metadata


# ==============================================================================
# 5. MESSAGE SWIPING (◀ 1/N ▶), INLINE EDITING, REWIND & BRANCHING
# ==============================================================================

def ensure_message_swipe_structure(msg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures an assistant message has a `swipes` list and `swipe_index` so the user
    can cycle between alternate regenerated responses (`◀ 1/N ▶`) just like SillyTavern.
    """
    if not isinstance(msg, dict):
        return msg
    swipes = msg.get("swipes")
    if not isinstance(swipes, list) or len(swipes) == 0:
        msg["swipes"] = [{
            "content": msg.get("content", ""),
            "mechanics_log": msg.get("mechanics_log", ""),
            "subagent_log": msg.get("subagent_log", ""),
            "image_path": msg.get("image_path"),
            "image_data": msg.get("image_data"),
            "timestamp": time.time(),
        }]
        msg["swipe_index"] = 0
    else:
        idx = int(msg.get("swipe_index", len(swipes) - 1) or 0)
        idx = max(0, min(len(swipes) - 1, idx))
        msg["swipe_index"] = idx
    return msg


def apply_active_swipe_to_message(msg: Dict[str, Any], new_index: int) -> Dict[str, Any]:
    """Switches the active swipe on a message and updates its top-level display fields."""
    ensure_message_swipe_structure(msg)
    swipes = msg["swipes"]
    idx = max(0, min(len(swipes) - 1, new_index))
    msg["swipe_index"] = idx
    active = swipes[idx]
    msg["content"] = active.get("content", "")
    if "mechanics_log" in active:
        msg["mechanics_log"] = active["mechanics_log"]
    if "subagent_log" in active:
        msg["subagent_log"] = active["subagent_log"]
    if active.get("image_path") is not None:
        msg["image_path"] = active.get("image_path")
    return msg


def append_new_swipe_to_message(
    msg: Dict[str, Any],
    content: str,
    mechanics_log: Optional[str] = None,
    subagent_log: Optional[str] = None,
    image_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Appends a newly generated swipe variation to `msg['swipes']` and selects it."""
    ensure_message_swipe_structure(msg)
    new_entry = {
        "content": content,
        "mechanics_log": mechanics_log if mechanics_log is not None else msg.get("mechanics_log", ""),
        "subagent_log": subagent_log if subagent_log is not None else msg.get("subagent_log", ""),
        "image_path": image_path if image_path is not None else msg.get("image_path"),
        "image_data": msg.get("image_data"),
        "timestamp": time.time(),
    }
    msg["swipes"].append(new_entry)
    return apply_active_swipe_to_message(msg, len(msg["swipes"]) - 1)


def generate_swipe_variation(
    api_key: str,
    user_action: str,
    msg: Dict[str, Any],
    player_state: Dict[str, Any],
    messages_context: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Generates a fresh SillyTavern-style Swipe (`◀ 1/N ▶`) narrative continuation for a turn
    while preserving the deterministic Python dice rolls (`mechanics_log`) and SubAgent thoughts
    (`subagent_log`) that already occurred on that turn!
    Returns (new_narrative_markdown, error_str).
    """
    st_cfg = ensure_st_settings(player_state)
    preset_id = st_cfg.get("preset_id", "grimdark_sensory")
    preset = DEFAULT_NARRATIVE_PRESETS.get(preset_id, DEFAULT_NARRATIVE_PRESETS["grimdark_sensory"])
    temp = min(1.15, float(st_cfg.get("temperature", preset.get("temperature", 0.85))) + 0.08)

    prev_swipes = [s.get("content", "")[:400] for s in (msg.get("swipes") or [])]
    mech_log = msg.get("mechanics_log", "")
    sub_log = msg.get("subagent_log", "")
    p_name = player_state.get("name", "Survivor") if isinstance(player_state, dict) else "Survivor"
    loc = player_state.get("location", "Sector 1") if isinstance(player_state, dict) else "Sector 1"

    wb_res = scan_and_inject_worldbook(
        player_action=user_action,
        messages=messages_context,
        player_state=player_state,
    )
    hist_block, _ = build_chat_history_with_authors_note(
        messages=messages_context,
        player_state=player_state,
        current_action=user_action,
    )

    swipe_prompt = f"""You are the Cardinal System Game Master generating an alternate **Swipe Variation (#{len(prev_swipes) + 1})** for the latest turn.

{preset.get('style_directive', '')}
{wb_res.get('formatted_block', '')}
{hist_block}

### CURRENT TURN CONTEXT (KEEP EXACT MECHANICAL OUTCOMES, WRITE FRESH CINEMATIC PROSE & DIALOGUE):
- **Player Character:** {p_name}
- **Current Location:** {loc}
- **Player's Action:** "{user_action}"
- **Resolved Dice Rolls & Mechanics (Must honor these exact outcomes without putting raw bracket math in prose):**
{mech_log or 'No combat rolls this turn.'}
- **Autonomous SubAgent Thoughts & Actions This Turn:**
{sub_log or 'Companions stand ready.'}

### PREVIOUS SWIPE OPENINGS (Write a noticeably fresh angle, pacing, sensory focus, and dialogue phrasing):
{json.dumps(prev_swipes, indent=2)}

### CRITICAL RULES:
1. Write ONLY the new narrative prose followed by a `---` divider and the `[CARDINAL TACTICAL TELEMETRY // ...]` footer line.
2. NEVER auto-play `{p_name}` past the immediate step of their action (`"{user_action}"`). Stop at the immediate decision point!
"""

    try:
        text_out = call_configured_llm_text(
            api_key=api_key,
            prompt=swipe_prompt,
            player_state=player_state,
            temperature_override=temp,
        )
        if text_out and text_out.strip():
            return text_out.strip(), None
        return None, "Empty response from model."
    except Exception as e:
        return None, str(e)


# ==============================================================================
# 6. MULTI-BACKEND LLM ROUTER (GEMINI CLOUD + OPENAI/KOBOLDCPP GGUF)
# ==============================================================================

def call_configured_llm_text(
    api_key: str,
    prompt: str,
    player_state: Optional[Dict[str, Any]] = None,
    temperature_override: Optional[float] = None,
) -> str:
    """
    Routes free-form text generation (such as Swipe regeneration or Character Card greetings)
    to either the configured OpenAI/KoboldCpp GGUF endpoint or Google Gemini API.
    """
    st_cfg = ensure_st_settings(player_state)
    backend_mode = st_cfg.get("backend_mode", "gemini")
    temp = float(temperature_override if temperature_override is not None else st_cfg.get("temperature", 0.85))
    top_p = float(st_cfg.get("top_p", 0.95))
    max_tokens = int(st_cfg.get("max_output_tokens", 1200) or 1200)

    if backend_mode == "openai_compat":
        endpoint = str(st_cfg.get("openai_endpoint", "http://127.0.0.1:5001/v1")).rstrip("/")
        url = f"{endpoint}/chat/completions" if not endpoint.endswith("/chat/completions") else endpoint
        oai_key = str(st_cfg.get("openai_api_key", "sk-local")).strip()
        oai_model = str(st_cfg.get("openai_model", "local-model")).strip()
        payload = {
            "model": oai_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temp,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {oai_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                return resp_data["choices"][0]["message"]["content"]
        except Exception as oai_err:
            print(f"[ST ROUTER] OpenAI/GGUF endpoint ({url}) failed ({oai_err}); falling back to Gemini.", flush=True)

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    model_name = str(st_cfg.get("gemini_model", "gemini-3.8-flash") or "gemini-3.8-flash")
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temp,
            top_p=top_p,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text


# ==============================================================================
# 7. VISUAL NOVEL (VN) EXPRESSION CLASSIFIER & REGEX QUOTE COLORING
# ==============================================================================

VN_EXPRESSIONS: Dict[str, Dict[str, str]] = {
    "dread": {
        "badge": "😨 Existential Dread",
        "border": "#00f5d4",
        "bg": "rgba(0, 245, 212, 0.10)",
    },
    "combat": {
        "badge": "😤 Combat Focus",
        "border": "#ff4d6d",
        "bg": "rgba(255, 77, 109, 0.12)",
    },
    "synaptic": {
        "badge": "🧠 Synaptic Override",
        "border": "#c77dff",
        "bg": "rgba(199, 125, 255, 0.12)",
    },
    "smug": {
        "badge": "😏 Tactical Confidence",
        "border": "#ffd166",
        "bg": "rgba(255, 209, 102, 0.12)",
    },
    "wounded": {
        "badge": "🩸 Strained / Bloodied",
        "border": "#e63946",
        "bg": "rgba(230, 57, 70, 0.15)",
    },
    "steady": {
        "badge": "🛡️ Steady Overwatch",
        "border": "#4cc9f0",
        "bg": "rgba(76, 201, 240, 0.10)",
    },
}


def classify_vn_expression(text: str, hp_ratio: float = 1.0, actor_name: str = "") -> Dict[str, str]:
    """Classifies a character's current VN expression state from their latest thought/dialogue & HP."""
    low = (text or "").lower()
    if hp_ratio < 0.45:
        return VN_EXPRESSIONS["wounded"]
    if "gyrus" in (actor_name or "").lower() or any(w in low for w in ["ulitharid", "lobe", "psionic", "palanquin", "docent"]):
        return VN_EXPRESSIONS["synaptic"]
    if any(w in low for w in ["redacted", "kernel", "terrified", "horror", "sandbox", "glitch", "trap", "careful"]):
        return VN_EXPRESSIONS["dread"]
    if any(w in low for w in ["strike", "fire", "salvo", "cleave", "shatter", "kill", "attack", "flank", "target"]):
        return VN_EXPRESSIONS["combat"]
    if any(w in low for w in ["grin", "smirk", "easy", "jackpot", "loot", "col", "haha", "nice"]):
        return VN_EXPRESSIONS["smug"]
    return VN_EXPRESSIONS["steady"]


def resolve_companion_portrait_path(comp_name: str, comp_data: Optional[Dict[str, Any]] = None, base_dir: str = BASE_DIR) -> Optional[str]:
    """Finds the best `.png` portrait path in `presets/` or `assets/avatars/` for any companion or NPC."""
    candidates: List[str] = []
    if isinstance(comp_data, dict):
        if comp_data.get("avatar"):
            candidates.append(str(comp_data["avatar"]))
        if comp_data.get("avatar_image_path"):
            candidates.append(str(comp_data["avatar_image_path"]))

    clean = (comp_name or "").strip()
    short = clean.split()[0] if clean else ""
    candidates.extend([
        f"presets/{clean}.png",
        f"presets/{clean.replace(' ', '_')}.png",
        f"presets/{short}.png",
        f"assets/avatars/{clean.lower().replace(' ', '_')}.png",
        f"assets/avatars/{short.lower()}_avatar.png",
        f"assets/avatars/{short.lower()}_st_card.png",
    ])
    # Special mappings for our preset cards
    low = clean.lower()
    if "ren" in low:
        candidates.append("presets/Ren.png")
    elif "elora" in low:
        candidates.append("presets/Elora Thorne.png")
    elif "torvald" in low:
        candidates.append("presets/Torvald Iron-Vein.png")
    elif "kibs" in low:
        candidates.append("presets/Kibs Nine-Fingers.png")
    elif "mercer" in low:
        candidates.append("presets/Doc Mercer.png")
    elif "vance" in low or "kaelen" in low:
        candidates.append("presets/Commander Kaelen Vance.png")
    elif "silas" in low:
        candidates.append("presets/Guildmaster Silas Bron.png")
    elif "silt" in low:
        candidates.append("presets/Silt-Marrow the Unhewn.png")

    for rel in candidates:
        abs_p = rel if os.path.isabs(rel) else os.path.join(base_dir, rel)
        if os.path.exists(abs_p):
            return abs_p
    return None


def format_sillytavern_prose(markdown_text: str, enable_regex_coloring: bool = True) -> str:
    """
    Applies SillyTavern-style Regex Quote & Telemetry Coloring to narrative markdown:
      - Spoken dialogue (`"..."`) -> warm golden-amber spans
      - Telepathic / Psionic links (`*[...]*` or `《...》`) -> glowing cyan/violet spans
      - Clinical `[CARDINAL TACTICAL TELEMETRY ...]` footer -> preserved cleanly
    """
    if not markdown_text or not enable_regex_coloring:
        return markdown_text

    # 1. Style Spoken Dialogue "..." first (before any HTML <span style="..."> attributes are added)
    def _color_quotes(line: str) -> str:
        if line.strip().startswith("`[CARDINAL") or line.strip().startswith("[CARDINAL"):
            return line
        return re.sub(
            r'(?<!=)"([^"\n]{2,350})"',
            r'<span style="color:#ffd166; font-weight:500;">"\1"</span>',
            line,
        )

    text = "\n".join(_color_quotes(ln) for ln in markdown_text.split("\n"))

    # 2. Style Gyrus / Docent Psionic Telepathy 《 ... 》
    text = re.sub(
        r"(《[^》\n]+》)",
        r'<span style="color:#c77dff; font-weight:600; text-shadow:0 0 8px rgba(199,125,255,0.35);">\1</span>',
        text,
    )

    # 3. Style Neural Whispers / Telepathy *[ ... ]*
    text = re.sub(
        r"\*\[([^\]\n]+)\]\*",
        r'<span style="color:#00f5d4; font-style:italic; background:rgba(0,245,212,0.08); padding:1px 6px; border-radius:4px; border-left:2px solid #00f5d4;">*[\1]*</span>',
        text,
    )

    return text
