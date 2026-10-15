"""
backend/database/migrator.py
============================
Authoritative Seed Migration Utility for Fractured Earth SAO Sandbox V2.
Imports all legacy disk JSON save files into ACID-compliant SQLAlchemy 2.0
relational persistence with 100% mechanical fidelity and strict idempotency.

Features:
- Migrates root save_game.json, campaign_default_save.json, and saves/<slug>/save_game.json.
- Migrates 18 companion sheets from Party/*.json and Entities/companion_*.json.
- Migrates GM master state (.game_state/secret_master_state.json) and world_state.json.
- Preserves multi-limb slots, [2H Grip] bindings, 9 graft slots, debuffs, fusion skills.
- Prevents row duplication and chat message inflation across repeated executions.
- Gracefully tolerates missing directories, missing files, and malformed JSON.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from sqlalchemy import delete, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from backend.database.adapters import (
    atomic_read_json,
    get_base_dir,
    sanitize_character_slug,
)
from backend.database.engine import (
    create_sao_engine,
    db_transaction,
    get_engine,
    init_db,
)
from backend.database.models import (
    ActiveDebuffRecord,
    AnatomicalGraftRecord,
    ArchivedSkillRecord,
    CampaignSessionRecord,
    CharacterRecord,
    ChatMessageRecord,
    CorpseCacheRecord,
    EquippedSlotRecord,
    MasterGameStateRecord,
    PartyCompanionRecord,
    SkillMasteryRecord,
)
from backend.database.repositories import (
    CharacterRepository,
    CorpseCacheRepository,
    MasterStateRepository,
    PartyRepository,
    WorldRepository,
    _ensure_campaign_session,
)
import backend.mechanics as mechanics

logger = logging.getLogger("backend.database.migrator")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


# ==============================================================================
# Helper Functions
# ==============================================================================

def _safe_load_json(file_path: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
    """Safely reads and deserializes JSON from file_path, returning None on failure."""
    if not file_path or not os.path.exists(file_path) or os.path.isdir(file_path):
        return None
    try:
        data = atomic_read_json(file_path, default=None)
        if isinstance(data, (dict, list)):
            return data
    except Exception as exc:
        logger.warning("Failed to parse JSON file '%s': %s", file_path, exc)
    return None


# ==============================================================================
# Master & World State Migration
# ==============================================================================

def migrate_master_state_file(
    state_file: str,
    session_id: str = "default",
    engine: Optional[Engine] = None,
) -> Optional[Dict[str, Any]]:
    """
    Imports GM secret master state into MasterGameStateRecord for the specified session.
    Strips 'player' key to avoid leaking player state or circular references.
    Merges state dictionary into existing state_json to preserve world_state keys.
    """
    raw_data = _safe_load_json(state_file)
    if not isinstance(raw_data, dict):
        return None

    clean_state = dict(raw_data)
    clean_state.pop("player", None)
    session_id = str(session_id or "default").strip()

    with db_transaction(session_id=session_id, engine=engine) as db:
        _ensure_campaign_session(db, session_id)
        rec = MasterStateRepository.save_master_state(db, clean_state, session_id=session_id)
        return rec.to_dict() if rec else None


def migrate_world_state_file(
    world_file: str,
    session_id: str = "default",
    engine: Optional[Engine] = None,
) -> Optional[Dict[str, Any]]:
    """
    Imports campaign world state into MasterGameStateRecord for the specified session,
    merging with any existing master state without overwriting it.
    """
    world_data = _safe_load_json(world_file)
    if not isinstance(world_data, dict):
        return None

    session_id = str(session_id or "default").strip()
    with db_transaction(session_id=session_id, engine=engine) as db:
        _ensure_campaign_session(db, session_id)
        rec = MasterStateRepository.save_world_state(db, world_data, session_id=session_id)
        return rec.to_dict() if rec else None


# ==============================================================================
# Party Companions Migration
# ==============================================================================

def migrate_party_directory(
    party_dir: str,
    session_id: str = "default",
    prune_missing: bool = False,
    engine: Optional[Engine] = None,
) -> List[Dict[str, Any]]:
    """
    Imports companion JSON sheets from party_dir into PartyCompanionRecord.
    Supports non-destructive upsert (prune_missing=False) so partial parties do not
    purge companions imported from canonical directories.
    """
    if not party_dir or not os.path.exists(party_dir) or not os.path.isdir(party_dir):
        return []

    session_id = str(session_id or "default").strip()

    # Read all companion JSON files in directory
    raw_files = [f for f in sorted(os.listdir(party_dir)) if f.endswith(".json")]
    companion_dicts: List[Dict[str, Any]] = []

    for f_name in raw_files:
        f_path = os.path.join(party_dir, f_name)
        comp_data = _safe_load_json(f_path)
        if isinstance(comp_data, dict):
            c_slug = str(
                comp_data.get("id") or comp_data.get("slug") or os.path.splitext(f_name)[0]
            ).lower().replace(" ", "_")
            comp_data["id"] = c_slug
            companion_dicts.append(comp_data)

    if not companion_dicts and not prune_missing:
        return []

    with db_transaction(session_id=session_id, engine=engine) as db:
        _ensure_campaign_session(db, session_id)

        if prune_missing:
            # Synchronize entire party strictly using PartyRepository.save_party
            PartyRepository.save_party(db, companion_dicts, session_id=session_id, mirror_disk=False)
            return PartyRepository.load_party(db, session_id=session_id)

        # Non-destructive upsert mode: update existing or insert new without pruning
        existing_map = {
            r.companion_slug: r
            for r in db.execute(
                select(PartyCompanionRecord).where(PartyCompanionRecord.session_id == session_id)
            ).scalars().all()
        }

        migrated_companions: List[Dict[str, Any]] = []

        for c in companion_dicts:
            c_slug = PartyRepository._normalize_slug(c)
            name_val = str(c.get("companion_name") or c.get("name") or c_slug.capitalize())
            lvl_val = int(c.get("level", 1))
            hp_val = int(c.get("hp", 30))
            max_hp_val = int(c.get("max_hp", max(hp_val, 30)))
            ac_val = int(c.get("ac", 15))
            recruited_val = bool(c.get("recruited", True))
            active_val = bool(c.get("is_active") if "is_active" in c else c.get("active", True))

            equipped_val = json.dumps(c.get("equipped", {}), ensure_ascii=False)
            stats_val = json.dumps(c.get("stats", {}), ensure_ascii=False)
            skills_val = json.dumps(c.get("skills", {}), ensure_ascii=False)
            payload = json.dumps(c, ensure_ascii=False)

            if c_slug in existing_map:
                rec = existing_map[c_slug]
                rec.name = name_val
                rec.level = lvl_val
                rec.hp = hp_val
                rec.max_hp = max_hp_val
                rec.ac = ac_val
                rec.recruited = recruited_val
                rec.active = active_val
                rec.equipped_json = equipped_val
                rec.stats_json = stats_val
                rec.skills_json = skills_val
                rec.companion_data_json = payload
            else:
                try:
                    with db.begin_nested():
                        rec = PartyCompanionRecord(
                            session_id=session_id,
                            companion_slug=c_slug,
                            name=name_val,
                            level=lvl_val,
                            hp=hp_val,
                            max_hp=max_hp_val,
                            ac=ac_val,
                            recruited=recruited_val,
                            active=active_val,
                            equipped_json=equipped_val,
                            stats_json=stats_val,
                            skills_json=skills_val,
                            companion_data_json=payload,
                        )
                        db.add(rec)
                        db.flush()
                except Exception:
                    rec = db.execute(
                        select(PartyCompanionRecord).where(
                            PartyCompanionRecord.session_id == session_id,
                            PartyCompanionRecord.companion_slug == c_slug,
                        )
                    ).scalar_one()
                    rec.name = name_val
                    rec.level = lvl_val
                    rec.hp = hp_val
                    rec.max_hp = max_hp_val
                    rec.ac = ac_val
                    rec.recruited = recruited_val
                    rec.active = active_val
                    rec.equipped_json = equipped_val
                    rec.stats_json = stats_val
                    rec.skills_json = skills_val
                    rec.companion_data_json = payload

            migrated_companions.append(c)

        db.flush()

    return migrated_companions


# ==============================================================================
# Character File Migration
# ==============================================================================

def migrate_character_file(
    file_path: str,
    session_id: str = "default",
    engine: Optional[Engine] = None,
    overwrite_messages: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Imports a character save file into the relational database.
    - Handles full save wrapper ({"player": ..., "messages": ...}) and flat entity dicts.
    - Idempotently updates CharacterRecord and all child mechanical tables.
    - Idempotently manages ChatMessageRecord to prevent duplicate messages across re-runs.
    - Synchronizes death_system corpse caches.
    """
    raw_data = _safe_load_json(file_path)
    if not isinstance(raw_data, dict):
        return None

    session_id = str(session_id or "default").strip()

    # Dissect player dictionary and chat messages
    if "player" in raw_data and isinstance(raw_data["player"], dict) and "name" in raw_data["player"]:
        player_state = raw_data["player"]
        messages = raw_data.get("messages", [])
    else:
        player_state = raw_data
        messages = []

    with db_transaction(session_id=session_id, engine=engine) as db:
        # 1. Save core character and normalized mechanical tables (pass messages=None to control message idempotency)
        char_rec = CharacterRepository.save_character(
            db, player_state, session_id=session_id, messages=None
        )

        # 2. Idempotent Chat Message Management
        if messages and isinstance(messages, list):
            if overwrite_messages:
                # Clear previous chat messages for this character to prevent inflation on re-migration
                db.execute(
                    delete(ChatMessageRecord).where(
                        ChatMessageRecord.session_id == session_id,
                        ChatMessageRecord.character_id == char_rec.id,
                    )
                )
                for msg in messages:
                    if isinstance(msg, dict) and "content" in msg:
                        chat_rec = ChatMessageRecord(
                            session_id=session_id,
                            character_id=char_rec.id,
                            role=str(msg.get("role", "user")),
                            content=str(msg.get("content", "")),
                            subagent_log=msg.get("subagent_log"),
                            image_path=msg.get("image_path"),
                        )
                        db.add(chat_rec)
            else:
                # Only insert if no messages currently exist for this character
                existing_cnt = db.execute(
                    select(func.count(ChatMessageRecord.id)).where(
                        ChatMessageRecord.session_id == session_id,
                        ChatMessageRecord.character_id == char_rec.id,
                    )
                ).scalar() or 0
                if existing_cnt == 0:
                    for msg in messages:
                        if isinstance(msg, dict) and "content" in msg:
                            chat_rec = ChatMessageRecord(
                                session_id=session_id,
                                character_id=char_rec.id,
                                role=str(msg.get("role", "user")),
                                content=str(msg.get("content", "")),
                                subagent_log=msg.get("subagent_log"),
                                image_path=msg.get("image_path"),
                            )
                            db.add(chat_rec)

        # 3. Synchronize Corpse Caches if present in player dictionary
        if "death_system" in player_state:
            CorpseCacheRepository.sync_player_caches(db, session_id, player_state)

        # 4. Synchronize auxiliary embedded states if present
        if "master_state" in raw_data and isinstance(raw_data["master_state"], dict):
            MasterStateRepository.save_master_state(db, raw_data["master_state"], session_id=session_id)
        if "world_state" in raw_data and isinstance(raw_data["world_state"], dict):
            MasterStateRepository.save_world_state(db, raw_data["world_state"], session_id=session_id)

        db.flush()

        # Rehydrate and return verified player dictionary
        hydrated = CharacterRepository.load_character(db, char_rec.slug, session_id=session_id)
        return hydrated


# ==============================================================================
# Comprehensive Seed Migration Orchestrator
# ==============================================================================

def migrate_all_disk_saves_to_db(
    engine: Optional[Engine] = None,
    base_dir: str = ".",
    default_session_id: str = "default",
    create_isolated_sessions: bool = True,
) -> Dict[str, Any]:
    """
    Authoritative seed migration utility importing all existing disk saves into relational DB.
    Idempotent: safe to run multiple times with zero row duplication.
    """
    start_time = time.time()
    base_dir = os.path.abspath(base_dir or get_base_dir())
    engine = engine or get_engine()

    # Ensure all tables exist in database
    init_db(engine)

    report: Dict[str, Any] = {
        "status": "success",
        "base_dir": base_dir,
        "sessions_migrated": [default_session_id],
        "characters_migrated": [],
        "party_companions_migrated": [],
        "master_states_migrated": [],
        "world_states_migrated": [],
        "corpse_caches_migrated": 0,
        "chat_messages_count": 0,
        "errors": [],
        "files_scanned": [],
    }

    # --------------------------------------------------------------------------
    # Phase 1: Migrate Canonical Master Game State & World State
    # --------------------------------------------------------------------------
    root_master_file = os.path.join(base_dir, ".game_state", "secret_master_state.json")
    if os.path.exists(root_master_file):
        report["files_scanned"].append(root_master_file)
        res = migrate_master_state_file(root_master_file, session_id=default_session_id, engine=engine)
        if res:
            report["master_states_migrated"].append(".game_state/secret_master_state.json")

    root_world_file = os.path.join(base_dir, "world_state.json")
    if os.path.exists(root_world_file):
        report["files_scanned"].append(root_world_file)
        res = migrate_world_state_file(root_world_file, session_id=default_session_id, engine=engine)
        if res:
            report["world_states_migrated"].append("world_state.json")

    # Fallback to Campaign_Data/ if root state files were missing
    camp_master_file = os.path.join(base_dir, "Campaign_Data", "secret_master_state.json")
    if not os.path.exists(root_master_file) and os.path.exists(camp_master_file):
        report["files_scanned"].append(camp_master_file)
        res = migrate_master_state_file(camp_master_file, session_id=default_session_id, engine=engine)
        if res:
            report["master_states_migrated"].append("Campaign_Data/secret_master_state.json")

    camp_world_file = os.path.join(base_dir, "Campaign_Data", "world_state.json")
    if not os.path.exists(root_world_file) and os.path.exists(camp_world_file):
        report["files_scanned"].append(camp_world_file)
        res = migrate_world_state_file(camp_world_file, session_id=default_session_id, engine=engine)
        if res:
            report["world_states_migrated"].append("Campaign_Data/world_state.json")

    # --------------------------------------------------------------------------
    # Phase 2: Migrate Canonical Party Companions (Root Party/ & Entities/)
    # --------------------------------------------------------------------------
    root_party_dir = os.path.join(base_dir, "Party")
    if os.path.exists(root_party_dir) and os.path.isdir(root_party_dir):
        report["files_scanned"].append(root_party_dir)
        comps = migrate_party_directory(
            root_party_dir, session_id=default_session_id, prune_missing=False, engine=engine
        )
        for c in comps:
            c_id = c.get("id") or c.get("name")
            if c_id not in report["party_companions_migrated"]:
                report["party_companions_migrated"].append(c_id)

    root_entities_dir = os.path.join(base_dir, "Entities")
    if os.path.exists(root_entities_dir) and os.path.isdir(root_entities_dir):
        report["files_scanned"].append(root_entities_dir)
        comps = migrate_party_directory(
            root_entities_dir, session_id=default_session_id, prune_missing=False, engine=engine
        )
        for c in comps:
            c_id = c.get("id") or c.get("name")
            if c_id not in report["party_companions_migrated"]:
                report["party_companions_migrated"].append(c_id)

    # --------------------------------------------------------------------------
    # Phase 3: Migrate Root Save Game & Campaign Default Save
    # --------------------------------------------------------------------------
    root_save_file = os.path.join(base_dir, "save_game.json")
    if os.path.exists(root_save_file):
        report["files_scanned"].append(root_save_file)
        try:
            hydrated = migrate_character_file(
                root_save_file, session_id=default_session_id, engine=engine, overwrite_messages=True
            )
            if hydrated:
                c_name = hydrated.get("name", "Banki")
                if c_name not in report["characters_migrated"]:
                    report["characters_migrated"].append(c_name)
        except Exception as exc:
            report["errors"].append(f"Error migrating {root_save_file}: {exc}")

    camp_def_file = os.path.join(base_dir, "campaign_default_save.json")
    if os.path.exists(camp_def_file):
        report["files_scanned"].append(camp_def_file)
        # Migrate into default session if root save_game.json was missing or has distinct character
        if not os.path.exists(root_save_file):
            try:
                hydrated = migrate_character_file(
                    camp_def_file, session_id=default_session_id, engine=engine, overwrite_messages=True
                )
                if hydrated:
                    c_name = hydrated.get("name", "Banki")
                    if c_name not in report["characters_migrated"]:
                        report["characters_migrated"].append(c_name)
            except Exception as exc:
                report["errors"].append(f"Error migrating {camp_def_file}: {exc}")

    # --------------------------------------------------------------------------
    # Phase 4: Migrate saves/ Directory (All Character Folders)
    # --------------------------------------------------------------------------
    saves_dir = os.path.join(base_dir, "saves")
    if os.path.exists(saves_dir) and os.path.isdir(saves_dir):
        report["files_scanned"].append(saves_dir)
        for char_folder in sorted(os.listdir(saves_dir)):
            char_path = os.path.join(saves_dir, char_folder)
            if not os.path.isdir(char_path):
                continue

            save_file = os.path.join(char_path, "save_game.json")
            if os.path.exists(save_file):
                report["files_scanned"].append(save_file)
                try:
                    # Migrate into default session so all characters are discoverable
                    hydrated = migrate_character_file(
                        save_file, session_id=default_session_id, engine=engine, overwrite_messages=True
                    )
                    if hydrated:
                        c_name = hydrated.get("name", char_folder)
                        if c_name not in report["characters_migrated"]:
                            report["characters_migrated"].append(c_name)

                    # Optionally seed an isolated session for this specific character
                    if create_isolated_sessions:
                        char_session_id = f"session_{char_folder.lower()}"
                        if char_session_id not in report["sessions_migrated"]:
                            report["sessions_migrated"].append(char_session_id)
                        migrate_character_file(
                            save_file, session_id=char_session_id, engine=engine, overwrite_messages=True
                        )

                        # Migrate character-specific party into the isolated session
                        char_party_dir = os.path.join(char_path, "Party")
                        if os.path.exists(char_party_dir):
                            migrate_party_directory(
                                char_party_dir, session_id=char_session_id, prune_missing=False, engine=engine
                            )
                except Exception as exc:
                    report["errors"].append(f"Error migrating {save_file}: {exc}")

            # Also check if character folder has a Party directory to merge into default
            char_party = os.path.join(char_path, "Party")
            if os.path.exists(char_party):
                migrate_party_directory(
                    char_party, session_id=default_session_id, prune_missing=False, engine=engine
                )

    # --------------------------------------------------------------------------
    # Phase 5: Calculate Final Database Record Totals
    # --------------------------------------------------------------------------
    with db_transaction(session_id=default_session_id, engine=engine) as db:
        report["chat_messages_count"] = db.execute(
            select(func.count(ChatMessageRecord.id))
        ).scalar() or 0
        report["corpse_caches_migrated"] = db.execute(
            select(func.count(CorpseCacheRecord.id))
        ).scalar() or 0

    report["duration_seconds"] = round(time.time() - start_time, 4)
    logger.info(
        "Seed migration completed in %s sec. Characters: %s, Companions: %s, Sessions: %s",
        report["duration_seconds"],
        len(report["characters_migrated"]),
        len(report["party_companions_migrated"]),
        len(report["sessions_migrated"]),
    )
    return report


# ==============================================================================
# Mechanical Verification Suite
# ==============================================================================

def verify_migration_fidelity(
    engine: Optional[Engine] = None,
    session_id: str = "default",
) -> Dict[str, Any]:
    """
    Performs mechanical verification against seeded database records:
    - Verifies Glenny AC 14 base / AC 16 with shield, Unit Strain Cap 4, 4-armed slots.
    - Verifies Banki Battleaxe Mastery 145, Arcana 218, level, and stats.
    - Verifies Ren HP 35, AC 16.
    - Verifies Master Game State and World State.
    """
    engine = engine or get_engine()
    audit: Dict[str, Any] = {"status": "passed", "checks": {}}

    with db_transaction(session_id=session_id, engine=engine) as db:
        # 1. Glenny Parity Check
        glenny = CharacterRepository.load_character(db, "glenny", session_id=session_id)
        if glenny:
            base_ac = mechanics.calculate_ac(glenny)
            glenny_shield = dict(glenny)
            glenny_shield["equipped"] = dict(glenny.get("equipped", {}))
            glenny_shield["equipped"]["lower_off_hand"] = "Riot Shield"
            shield_ac = mechanics.calculate_ac(glenny_shield)
            max_strain = mechanics.get_max_unit_strain(glenny)
            equipped = glenny.get("equipped", {})

            has_2h_grip = equipped.get("off_hand") == "[2H Grip: Recurve Hunting Bow]"
            has_lower_hands = "lower_main_hand" in equipped and "lower_off_hand" in equipped

            audit["checks"]["glenny_parity"] = {
                "base_ac": base_ac,
                "expected_base_ac": 14,
                "shield_ac": shield_ac,
                "expected_shield_ac": 16,
                "max_strain": max_strain,
                "expected_max_strain": 4,
                "has_2h_grip": has_2h_grip,
                "has_lower_hands": has_lower_hands,
                "pass": (base_ac == 14 and shield_ac == 16 and max_strain == 4 and has_2h_grip and has_lower_hands),
            }
        else:
            audit["checks"]["glenny_parity"] = {"pass": False, "error": "Glenny not found in session"}
            audit["status"] = "failed"

        # 2. Banki Parity Check
        banki = CharacterRepository.load_character(db, "banki", session_id=session_id)
        if banki:
            skills = banki.get("skills", {})
            b_axe = skills.get("Battleaxe Mastery", {}).get("mastery")
            arcana = skills.get("Arcana", {}).get("mastery")
            audit["checks"]["banki_parity"] = {
                "level": banki.get("level"),
                "battleaxe_mastery": b_axe,
                "arcana_mastery": arcana,
                "pass": (b_axe == 145 and arcana == 218),
            }
        else:
            audit["checks"]["banki_parity"] = {"pass": False, "error": "Banki not found in session"}
            audit["status"] = "failed"

        # 3. Companion Ren Check
        ren = None
        comps = PartyRepository.load_party(db, session_id=session_id)
        for c in comps:
            if c.get("id") in ("companion_ren", "ren") or c.get("name") in ("Ren", "Ren Sasaki"):
                ren = c
                break
        if ren:
            audit["checks"]["ren_parity"] = {
                "hp": ren.get("hp"),
                "max_hp": ren.get("max_hp"),
                "ac": ren.get("ac"),
                "pass": (ren.get("hp") == 35 and ren.get("ac") == 16),
            }
        else:
            audit["checks"]["ren_parity"] = {"pass": False, "error": "Ren not found in party"}
            audit["status"] = "failed"

        # 4. Master Game State Check
        m_state = WorldRepository.load_master_state(db, session_id=session_id)
        w_state = WorldRepository.load_world_state(db, session_id=session_id)
        audit["checks"]["world_state_parity"] = {
            "sector": w_state.get("sector") if w_state else None,
            "turn_number": m_state.get("turn_number") if m_state else None,
            "pass": bool(w_state and w_state.get("sector") == 1 and m_state and m_state.get("turn_number") == 33),
        }

    for k, v in audit["checks"].items():
        if not v.get("pass", False):
            audit["status"] = "failed"
            break

    return audit
