"""
backend/database/repositories.py
================================
ACID-Compliant Relational Repositories for SAO Sandbox V2.
Encapsulates entity serialization, multi-limb equipment persistence, 2H grip bindings,
anatomical grafts (9+ slots) and metabolic strain tracking, mutable combat debuffs,
1–1000 skill mastery with Ability Fusion matrix archival, and persistent Corpse Caches.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Union
import uuid

from sqlalchemy import func, select, text, update
from sqlalchemy.orm import Session

from backend.database.adapters import sanitize_character_slug
from backend.database.engine import register_post_commit_hook
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
import backend.mechanics as mechanics

logger = logging.getLogger("backend.database.repositories")

_party_columns_verified: bool = False


def _ensure_party_companion_columns(db_session: Session) -> None:
    """Safely verifies newly introduced columns in party_companions exist on existing SQLite databases."""
    global _party_columns_verified
    if _party_columns_verified:
        return
    try:
        conn = db_session.connection()
        if conn.dialect.name == "sqlite":
            cursor = conn.execute(text("PRAGMA table_info(party_companions);"))
            existing_cols = {row[1] for row in cursor.fetchall()}
            if existing_cols:
                for col_name in ("equipped_json", "stats_json", "skills_json"):
                    if col_name not in existing_cols:
                        conn.execute(text(f"ALTER TABLE party_companions ADD COLUMN {col_name} TEXT DEFAULT '{{}}';"))
        _party_columns_verified = True
    except Exception:
        pass


def _ensure_campaign_session(db_session: Session, session_id: str) -> CampaignSessionRecord:
    """
    Atomically ensures the parent CampaignSessionRecord exists using a nested savepoint.
    Prevents foreign key constraint failures across concurrent transactions and unseeded sessions.
    """
    session_id = str(session_id or "default").strip()
    session_rec = db_session.get(CampaignSessionRecord, session_id)
    if not session_rec:
        try:
            with db_session.begin_nested():
                session_rec = CampaignSessionRecord(
                    session_id=session_id,
                    session_name=f"Session {session_id}",
                )
                db_session.add(session_rec)
                db_session.flush()
        except Exception:
            session_rec = db_session.get(CampaignSessionRecord, session_id)
    return session_rec


class CharacterRepository:
    """
    Authoritative repository managing CharacterRecord lifecycle, multi-limb loadout
    synchronization, anatomical grafts, combat debuffs, and full V2 mechanical rehydration.
    """

    @staticmethod
    def save_character(
        db_session: Session,
        character_dict: dict,
        session_id: str = "default",
        messages: Optional[list] = None,
    ) -> CharacterRecord:
        """
        Atomically persists or updates a character in the relational database.

        Args:
            db_session: Active SQLAlchemy Session within a db_transaction.
            character_dict: Character state dictionary (or full save dict containing 'player').
            session_id: Campaign session isolation identifier.
            messages: Optional chat message log to associate with session/character.

        Returns:
            CharacterRecord: The persisted authoritative character ORM record.
        """
        if not isinstance(character_dict, dict):
            raise ValueError("character_dict must be a valid dictionary")

        session_id = str(session_id or "default").strip()

        # 1. Defensively extract player state if wrapped in full save dictionary
        if "player" in character_dict and isinstance(character_dict["player"], dict) and "name" in character_dict["player"]:
            inner_player = character_dict["player"]
        else:
            inner_player = character_dict

        # 2. Resolve Character Identity & Slug
        raw_name = str(inner_player.get("name", "Survivor")).strip()
        slug = inner_player.get("slug")
        if not slug:
            slug = sanitize_character_slug(raw_name).lower()
        else:
            slug = str(slug).strip().lower()

        # 3. Ensure Campaign Session Exists (Nested Savepoint for Multi-Thread Safety)
        session_rec = _ensure_campaign_session(db_session, session_id)

        # 4. Query Existing Character Record
        existing = db_session.execute(
            select(CharacterRecord).where(
                CharacterRecord.session_id == session_id,
                func.lower(CharacterRecord.slug) == slug,
            )
        ).scalar_one_or_none()

        stats = inner_player.get("stats")
        stats_json = json.dumps(stats, ensure_ascii=False) if stats is not None else None

        # 5. Incremental Raw JSON Merge (Preserves Full Mechanical Fidelity)
        if existing:
            rec = existing
            rec.name = str(inner_player.get("name", rec.name))
            rec.level = int(inner_player.get("level", rec.level))
            rec.hp = int(inner_player.get("hp", rec.hp))
            rec.max_hp = int(inner_player.get("max_hp", rec.max_hp))
            rec.col = int(inner_player.get("col", rec.col))
            rec.xp = int(inner_player.get("xp", rec.xp))
            if "gender" in inner_player:
                rec.gender = inner_player.get("gender")
            if "race" in inner_player:
                rec.race = inner_player.get("race")
            if "class" in inner_player:
                rec.character_class = inner_player.get("class")
            if "location" in inner_player:
                rec.location = inner_player.get("location")
            if stats_json is not None:
                rec.stats_json = stats_json

            # Merge raw_data_json
            try:
                current_raw = json.loads(rec.raw_data_json) if rec.raw_data_json else {}
                if isinstance(current_raw, dict):
                    if "player" in current_raw and isinstance(current_raw["player"], dict):
                        current_raw["player"].update(inner_player)
                    else:
                        current_raw.update(inner_player)
                    rec.raw_data_json = json.dumps(current_raw, ensure_ascii=False, default=str)
                else:
                    rec.raw_data_json = json.dumps(character_dict, ensure_ascii=False, default=str)
            except Exception:
                rec.raw_data_json = json.dumps(character_dict, ensure_ascii=False, default=str)

            rec.updated_at = datetime.now(timezone.utc)
        else:
            rec = CharacterRecord(
                session_id=session_id,
                slug=slug,
                name=raw_name,
                level=int(inner_player.get("level", 1)),
                hp=int(inner_player.get("hp", 100)),
                max_hp=int(inner_player.get("max_hp", 100)),
                col=int(inner_player.get("col", 0)),
                xp=int(inner_player.get("xp", 0)),
                gender=inner_player.get("gender"),
                race=inner_player.get("race"),
                character_class=inner_player.get("class"),
                location=inner_player.get("location"),
                stats_json=stats_json or "{}",
                raw_data_json=json.dumps(character_dict, ensure_ascii=False, default=str),
            )
            try:
                with db_session.begin_nested():
                    db_session.add(rec)
                    db_session.flush()
            except Exception:
                rec = db_session.execute(
                    select(CharacterRecord).where(
                        CharacterRecord.session_id == session_id,
                        func.lower(CharacterRecord.slug) == slug,
                    )
                ).scalar_one()
                rec.name = str(inner_player.get("name", rec.name))
                rec.level = int(inner_player.get("level", rec.level))
                rec.hp = int(inner_player.get("hp", rec.hp))
                rec.max_hp = int(inner_player.get("max_hp", rec.max_hp))
                rec.col = int(inner_player.get("col", rec.col))
                rec.xp = int(inner_player.get("xp", rec.xp))
                if "gender" in inner_player:
                    rec.gender = inner_player.get("gender")
                if "race" in inner_player:
                    rec.race = inner_player.get("race")
                if "class" in inner_player:
                    rec.character_class = inner_player.get("class")
                if "location" in inner_player:
                    rec.location = inner_player.get("location")
                if stats_json is not None:
                    rec.stats_json = stats_json
                rec.updated_at = datetime.now(timezone.utc)

        # 6. Synchronize Equipped Slots (Multi-Limb & 2H Grips)
        if "equipped" in inner_player and isinstance(inner_player["equipped"], dict):
            equipped_map = inner_player["equipped"]
            existing_slots = {s.slot_key: s for s in rec.equipped_slots}
            current_keys = set()

            for s_key, s_item in equipped_map.items():
                if s_item is None or s_item == "" or s_item == "None":
                    continue
                k_str = str(s_key).strip().lower()
                v_str = str(s_item).strip()
                current_keys.add(k_str)

                # Detect and annotate 2H grip bindings
                item_meta: Optional[Dict[str, Any]] = None
                if v_str.startswith("[2H Grip:") and v_str.endswith("]"):
                    paired = v_str[len("[2H Grip:"): -1].strip()
                    item_meta = {
                        "is_two_handed_grip": True,
                        "paired_weapon": paired,
                        "primary_weapon": paired,
                    }

                meta_json = json.dumps(item_meta) if item_meta else None

                if k_str in existing_slots:
                    slot_rec = existing_slots[k_str]
                    slot_rec.item_name = v_str
                    slot_rec.item_data_json = meta_json
                else:
                    slot_rec = EquippedSlotRecord(
                        character_id=rec.id,
                        slot_key=k_str,
                        item_name=v_str,
                        item_data_json=meta_json,
                    )
                    rec.equipped_slots.append(slot_rec)

            # Prune removed slots
            for old_k, old_s in list(existing_slots.items()):
                if old_k not in current_keys:
                    db_session.delete(old_s)

        # 7. Synchronize Anatomical Grafts (9+ Slots & Unit Strain)
        grafts_source: Optional[Dict[str, Any]] = None
        if "graft_system" in inner_player and isinstance(inner_player["graft_system"], dict):
            grafts_source = dict(inner_player["graft_system"].get("installed_grafts", {}))
        elif "grafts" in inner_player and isinstance(inner_player["grafts"], dict):
            grafts_source = dict(inner_player["grafts"])

        if "grafts" in inner_player and isinstance(inner_player["grafts"], dict):
            if grafts_source is None:
                grafts_source = {}
            for s, g in inner_player["grafts"].items():
                if isinstance(g, dict) and g.get("name") and s not in grafts_source:
                    grafts_source[s] = g

        if isinstance(grafts_source, dict):
            existing_grafts = {g.slot_key: g for g in rec.anatomical_grafts}
            current_graft_slots = set()

            for g_slot, g_val in grafts_source.items():
                if not g_val:
                    continue
                slot_k = str(g_slot).strip().lower()
                if hasattr(mechanics, "SLOT_ALIASES"):
                    slot_k = mechanics.SLOT_ALIASES.get(slot_k, slot_k)
                current_graft_slots.add(slot_k)

                if isinstance(g_val, dict):
                    g_name = str(g_val.get("name") or slot_k)
                    if hasattr(mechanics, "_infer_graft_unit_strain"):
                        u_strain = mechanics._infer_graft_unit_strain(g_val)
                    else:
                        u_strain = int(g_val.get("unit_strain") or g_val.get("strain") or 1)
                    raw_bio = g_val.get("bio_strain") or g_val.get("strain")
                    if raw_bio is not None and int(raw_bio) > 3:
                        b_strain = int(raw_bio)
                    else:
                        b_strain = u_strain * 10
                    g_meta = json.dumps(g_val)
                else:
                    g_name = str(g_val)
                    u_strain = 1
                    b_strain = 10
                    g_meta = None

                if slot_k in existing_grafts:
                    g_rec = existing_grafts[slot_k]
                    g_rec.graft_name = g_name
                    g_rec.unit_strain = u_strain
                    g_rec.bio_strain = b_strain
                    g_rec.graft_data_json = g_meta
                else:
                    g_rec = AnatomicalGraftRecord(
                        character_id=rec.id,
                        slot_key=slot_k,
                        graft_name=g_name,
                        unit_strain=u_strain,
                        bio_strain=b_strain,
                        graft_data_json=g_meta,
                    )
                    rec.anatomical_grafts.append(g_rec)

            for old_k, old_g in list(existing_grafts.items()):
                if old_k not in current_graft_slots:
                    db_session.delete(old_g)

        # 8. Synchronize Active Debuffs (AC/DR Shreds)
        if "active_debuffs" in inner_player and isinstance(inner_player["active_debuffs"], list):
            existing_debuffs = {db.debuff_id: db for db in rec.active_debuffs}
            current_debuff_ids = set()

            for db_item in inner_player["active_debuffs"]:
                if isinstance(db_item, dict) and (db_item.get("name") or db_item.get("debuff_id")):
                    raw_id = str(db_item.get("debuff_id") or db_item.get("name")).lower().replace(" ", "_")
                    current_debuff_ids.add(raw_id)
                    ac_pen = int(db_item.get("ac_penalty") or 0)
                    dr_ovr = db_item.get("dr_override")
                    if dr_ovr is not None:
                        try:
                            dr_ovr = int(dr_ovr)
                        except (ValueError, TypeError):
                            dr_ovr = None
                    turns = int(db_item.get("turns_remaining") if db_item.get("turns_remaining") is not None else 3)
                    source = str(db_item.get("source") or "")

                    if raw_id in existing_debuffs:
                        db_rec = existing_debuffs[raw_id]
                        db_rec.name = str(db_item.get("name") or raw_id)
                        db_rec.ac_penalty = ac_pen
                        db_rec.dr_override = dr_ovr
                        db_rec.turns_remaining = turns
                        db_rec.source = source
                        db_rec.debuff_data_json = json.dumps(db_item)
                    else:
                        db_rec = ActiveDebuffRecord(
                            character_id=rec.id,
                            debuff_id=raw_id,
                            name=str(db_item.get("name") or raw_id),
                            ac_penalty=ac_pen,
                            dr_override=dr_ovr,
                            turns_remaining=turns,
                            source=source,
                            debuff_data_json=json.dumps(db_item),
                        )
                        rec.active_debuffs.append(db_rec)

            for old_id, old_db in list(existing_debuffs.items()):
                if old_id not in current_debuff_ids:
                    db_session.delete(old_db)

        # 9. Synchronize Active Skills (1–1000 Mastery & Fusion Matrix)
        if "skills" in inner_player and isinstance(inner_player["skills"], dict):
            existing_skills = {sm.skill_name: sm for sm in rec.skill_masteries}
            current_skills = set()

            for s_name, s_data in inner_player["skills"].items():
                if not s_name:
                    continue
                s_name_str = str(s_name).strip()
                current_skills.add(s_name_str)
                if isinstance(s_data, dict):
                    raw_m = s_data.get("mastery", 1)
                    try:
                        m_level = int(raw_m) if raw_m is not None else 1
                    except (ValueError, TypeError):
                        m_level = 1
                    m_level = max(1, min(1000, m_level))
                    tier = str(s_data.get("tier") or (mechanics.get_mastery_tier(m_level) if hasattr(mechanics, "get_mastery_tier") else "Novice"))
                    is_fusion = s_name_str.startswith("[Fusion]") or (s_data.get("is_fusion") is True)
                    meta_str = json.dumps(s_data)
                else:
                    try:
                        m_level = int(s_data) if s_data is not None else 1
                    except (ValueError, TypeError):
                        m_level = 1
                    m_level = max(1, min(1000, m_level))
                    tier = mechanics.get_mastery_tier(m_level) if hasattr(mechanics, "get_mastery_tier") else "Novice"
                    is_fusion = s_name_str.startswith("[Fusion]")
                    meta_str = json.dumps({"description": f"Proficiency in {s_name_str}."})

                if s_name_str in existing_skills:
                    sm_rec = existing_skills[s_name_str]
                    sm_rec.mastery_level = m_level
                    sm_rec.tier = tier
                    sm_rec.is_fusion = is_fusion
                    sm_rec.skill_data_json = meta_str
                else:
                    sm_rec = SkillMasteryRecord(
                        character_id=rec.id,
                        skill_name=s_name_str,
                        mastery_level=m_level,
                        is_fusion=is_fusion,
                        tier=tier,
                        skill_data_json=meta_str,
                    )
                    rec.skill_masteries.append(sm_rec)

            for old_sk_name, old_sm in list(existing_skills.items()):
                if old_sk_name not in current_skills:
                    db_session.delete(old_sm)

        # 10. Synchronize Archived Base Skills (Ability Fusion Retention)
        if "archived_base_skills" in inner_player and isinstance(inner_player["archived_base_skills"], dict):
            existing_arch = {ar.skill_name: ar for ar in rec.archived_skills}
            current_arch = set()

            for a_name, a_data in inner_player["archived_base_skills"].items():
                if not a_name:
                    continue
                a_name_str = str(a_name).strip()
                current_arch.add(a_name_str)
                if isinstance(a_data, dict):
                    raw_prev = a_data.get("previous_mastery", a_data.get("mastery", 1))
                    try:
                        prev_m = int(raw_prev) if raw_prev is not None else 1
                    except (ValueError, TypeError):
                        prev_m = 1
                    prev_m = max(1, min(1000, prev_m))
                    reason = str(a_data.get("archived_reason") or f"Consumed in Ability Fusion into {a_data.get('fused_into', '[Fusion] Skill')}")
                    fused_into = str(a_data.get("fused_into") or "")
                    was_sp = bool(a_data.get("was_spell", False))
                    meta_arch = json.dumps(a_data)
                else:
                    prev_m = 1
                    reason = "Archived foundational skill"
                    fused_into = ""
                    was_sp = False
                    meta_arch = json.dumps({"description": str(a_data)})

                if a_name_str in existing_arch:
                    ar_rec = existing_arch[a_name_str]
                    ar_rec.mastery_level = prev_m
                    ar_rec.archived_reason = reason
                    ar_rec.fused_into = fused_into
                    ar_rec.was_spell = was_sp
                    ar_rec.skill_data_json = meta_arch
                else:
                    ar_rec = ArchivedSkillRecord(
                        character_id=rec.id,
                        skill_name=a_name_str,
                        mastery_level=prev_m,
                        archived_reason=reason,
                        fused_into=fused_into,
                        was_spell=was_sp,
                        skill_data_json=meta_arch,
                    )
                    rec.archived_skills.append(ar_rec)

        # 11. Associate Chat Messages (if provided)
        if messages and isinstance(messages, list):
            for msg in messages:
                if isinstance(msg, dict) and "content" in msg:
                    role_str = str(msg.get("role", "user"))
                    content_str = str(msg.get("content", ""))
                    # Optional ChatMessage persistence
                    chat_rec = ChatMessageRecord(
                        session_id=session_id,
                        character_id=rec.id,
                        role=role_str,
                        content=content_str,
                        subagent_log=msg.get("subagent_log"),
                        image_path=msg.get("image_path"),
                    )
                    db_session.add(chat_rec)

        db_session.flush()
        return rec

    @staticmethod
    def load_character(
        db_session: Session,
        character_slug: str,
        session_id: str = "default",
    ) -> Optional[dict]:
        """
        Loads and hydrates a full player dictionary from the relational database.

        Args:
            db_session: Active SQLAlchemy Session within a db_transaction.
            character_slug: Slug or name of character to retrieve.
            session_id: Campaign session isolation identifier.

        Returns:
            dict: Hydrated player dictionary with 100% mechanical fidelity, or None if not found.
        """
        if not character_slug:
            return None

        clean_slug = str(character_slug).strip().lower()
        session_id = str(session_id or "default").strip()

        rec = db_session.execute(
            select(CharacterRecord).where(
                CharacterRecord.session_id == session_id,
                func.lower(CharacterRecord.slug) == clean_slug,
            )
        ).scalar_one_or_none()

        if not rec:
            return None

        # Reconstruct player dictionary via ORM dual-coverage method
        player_dict = rec.to_player_dict()
        player_dict["slug"] = rec.slug

        # Ensure graft containers and multi-limb equipment are synchronized
        if hasattr(mechanics, "sync_graft_containers"):
            mechanics.sync_graft_containers(player_dict)
        if hasattr(mechanics, "ensure_multi_limb_equipment"):
            mechanics.ensure_multi_limb_equipment(player_dict)

        # Recalculate effective combat stats so active debuffs (AC shred, DR override) take effect
        if hasattr(mechanics, "recalculate_entity_combat_stats"):
            mechanics.recalculate_entity_combat_stats(player_dict)

        return player_dict

    @staticmethod
    def get_character_by_slug(
        db_session: Session,
        character_slug: str,
        session_id: str = "default",
    ) -> Optional[CharacterRecord]:
        """Directly retrieves the CharacterRecord ORM entity by slug."""
        if not character_slug:
            return None
        clean_slug = str(character_slug).strip().lower()
        session_id = str(session_id or "default").strip()
        return db_session.execute(
            select(CharacterRecord).where(
                CharacterRecord.session_id == session_id,
                func.lower(CharacterRecord.slug) == clean_slug,
            )
        ).scalar_one_or_none()

    @staticmethod
    def get_character_record(
        db_session: Session,
        character_slug: str,
        session_id: str = "default",
    ) -> Optional[CharacterRecord]:
        """Alias for get_character_by_slug."""
        return CharacterRepository.get_character_by_slug(db_session, character_slug, session_id)

    @staticmethod
    def list_characters_by_session(
        db_session: Session,
        session_id: str = "default",
    ) -> List[CharacterRecord]:
        """Returns all CharacterRecord entities in a campaign session."""
        session_id = str(session_id or "default").strip()
        return list(
            db_session.execute(
                select(CharacterRecord).where(CharacterRecord.session_id == session_id)
            ).scalars().all()
        )

    @staticmethod
    def list_characters_for_session(
        db_session: Session,
        session_id: str = "default",
    ) -> List[dict]:
        """Returns summarized dictionaries of all characters in a campaign session."""
        records = CharacterRepository.list_characters_by_session(db_session, session_id)
        return [r.to_player_dict() for r in records]

    @staticmethod
    def delete_character(
        db_session: Session,
        character_slug: str,
        session_id: str = "default",
    ) -> bool:
        """Deletes a character and cascades to all child slot/graft/debuff/skill rows."""
        rec = CharacterRepository.get_character_by_slug(db_session, character_slug, session_id)
        if not rec:
            return False
        db_session.delete(rec)
        db_session.flush()
        return True


class CorpseCacheRepository:
    """
    Repository managing persistent floor corpse caches and recovery lifecycles.
    Handles cache creation on Vanguard death, floor-scoped queries, and recovery.
    """

    @staticmethod
    def create_cache(
        db_session: Session,
        session_id: str,
        floor_number: Optional[int] = None,
        col_amount: Optional[int] = None,
        inventory: Union[list, str] = None,
        gear: Union[dict, str] = None,
        fallen_name: str = "Fallen Hero",
        raid_id: Optional[str] = None,
        location: Optional[str] = None,
        cache_id: Optional[str] = None,
        floor: Optional[int] = None,
        col: Optional[int] = None,
        **kwargs,
    ) -> CorpseCacheRecord:
        """
        Creates and persists a new CorpseCacheRecord in the database.
        Accepts both floor/col and floor_number/col_amount interchangeably.
        """
        session_id = str(session_id or "default").strip()

        # Resolve floor & col interchangeably
        actual_floor = int(floor_number if floor_number is not None else (floor if floor is not None else 1))
        actual_col = max(0, int(col_amount if col_amount is not None else (col if col is not None else 0)))

        # Ensure parent campaign session exists
        _ensure_campaign_session(db_session, session_id)

        # Generate unique cache_id if none provided
        if not cache_id:
            ts = int(datetime.now(timezone.utc).timestamp())
            ms_ts = int(time.time() * 1000)
            rand_suffix = uuid.uuid4().hex[:8]
            r_str = f"_{raid_id}" if raid_id else ""
            cache_id = f"cache_{session_id}{r_str}_f{actual_floor}_{ms_ts}_{rand_suffix}"

        # Serialize JSON fields if passed as Python collections
        inv_str = inventory if isinstance(inventory, str) else json.dumps(inventory or [], ensure_ascii=False)
        gear_str = gear if isinstance(gear, str) else json.dumps(gear or {}, ensure_ascii=False)

        rec = CorpseCacheRecord(
            session_id=session_id,
            cache_id=cache_id,
            fallen_name=str(fallen_name),
            floor_number=actual_floor,
            raid_id=raid_id,
            location=location,
            col_amount=actual_col,
            inventory_json=inv_str,
            gear_json=gear_str,
            recovered=False,
        )
        db_session.add(rec)
        db_session.flush()
        return rec

    @staticmethod
    def get_caches_for_floor(
        db_session: Session,
        session_id: str,
        floor_number: Optional[int] = None,
        include_recovered: bool = False,
        floor: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all corpse caches located on a specific floor for a session.
        Accepts floor_number or floor.
        """
        session_id = str(session_id or "default").strip()
        actual_floor = int(floor_number if floor_number is not None else (floor if floor is not None else 1))

        stmt = select(CorpseCacheRecord).where(
            CorpseCacheRecord.session_id == session_id,
            CorpseCacheRecord.floor_number == actual_floor,
        )
        if not include_recovered:
            stmt = stmt.where(CorpseCacheRecord.recovered == False)

        stmt = stmt.order_by(CorpseCacheRecord.created_at.desc())
        records = db_session.execute(stmt).scalars().all()
        return [r.to_cache_dict() for r in records]

    @staticmethod
    def claim_cache(
        db_session: Session,
        cache_id: str,
        session_id: Optional[str] = "default",
    ) -> Optional[Dict[str, Any]]:
        """
        Claims/recovers a corpse cache atomically.
        Guarantees idempotency and race-freedom:
        - Evaluates initial existence and cached recovered state.
        - Executes an atomic conditional update: WHERE id == rec.id AND recovered == False.
        - Gates claim authorization strictly on result.rowcount == 1.
        Returns Optional[dict] with success status, recovered Col, inventory, and gear.
        """
        stmt = select(CorpseCacheRecord).where(CorpseCacheRecord.cache_id == cache_id)
        if session_id and session_id != "default":
            stmt = stmt.where(CorpseCacheRecord.session_id == session_id)

        rec = db_session.execute(stmt).scalar_one_or_none()
        if not rec:
            return None

        # Fast-fail if cache was already marked recovered prior to transaction
        if rec.recovered:
            return {
                "success": False,
                "recovered": True,
                "cache_id": rec.cache_id,
                "fallen_name": rec.fallen_name,
                "floor": rec.floor_number,
                "col": 0,
                "inventory": [],
                "equipped": {},
                "message": f"Corpse cache '{cache_id}' has already been recovered.",
            }

        # Atomic conditional update: atomically transition recovered from False -> True
        update_stmt = (
            update(CorpseCacheRecord)
            .where(
                CorpseCacheRecord.id == rec.id,
                CorpseCacheRecord.recovered == False,
            )
            .values(recovered=True)
        )
        result = db_session.execute(update_stmt)
        db_session.flush()

        # Concurrency gate: only the single winning transaction receives rowcount == 1
        if result.rowcount == 0:
            return {
                "success": False,
                "recovered": True,
                "cache_id": rec.cache_id,
                "fallen_name": rec.fallen_name,
                "floor": rec.floor_number,
                "col": 0,
                "inventory": [],
                "equipped": {},
                "message": f"Corpse cache '{cache_id}' has already been recovered.",
            }

        # Synchronize in-memory record state for any caller inspecting the ORM instance
        rec.recovered = True

        inv = json.loads(rec.inventory_json) if rec.inventory_json else []
        gear = json.loads(rec.gear_json) if rec.gear_json else {}

        return {
            "success": True,
            "recovered": True,
            "cache_id": rec.cache_id,
            "fallen_name": rec.fallen_name,
            "floor": rec.floor_number,
            "raid_id": rec.raid_id,
            "location": rec.location,
            "col": rec.col_amount,
            "inventory": inv,
            "equipped": gear,
            "message": f"Successfully claimed corpse cache of {rec.fallen_name} on floor {rec.floor_number}.",
        }

    @staticmethod
    def get_all_caches(
        db_session: Session,
        session_id: str,
        include_recovered: bool = False,
    ) -> List[Dict[str, Any]]:
        """Retrieves all corpse caches across all floors for a session."""
        session_id = str(session_id or "default").strip()
        stmt = select(CorpseCacheRecord).where(CorpseCacheRecord.session_id == session_id)
        if not include_recovered:
            stmt = stmt.where(CorpseCacheRecord.recovered == False)
        stmt = stmt.order_by(CorpseCacheRecord.floor_number.asc(), CorpseCacheRecord.created_at.desc())
        records = db_session.execute(stmt).scalars().all()
        return [r.to_cache_dict() for r in records]

    @staticmethod
    def sync_player_caches(
        db_session: Session,
        session_id: str,
        player_dict: dict,
    ) -> None:
        """
        Synchronizes death_system['corpse_caches'] from player dictionary into relational database.
        Ensures caches generated by mechanics.execute_legacy_reset() persist to the relational table.
        """
        session_id = str(session_id or "default").strip()
        death_sys = player_dict.get("death_system", {})
        caches = death_sys.get("corpse_caches", [])
        if not isinstance(caches, list):
            return

        for c in caches:
            if not isinstance(c, dict):
                continue
            c_id = c.get("cache_id")
            if not c_id:
                continue

            existing = db_session.execute(
                select(CorpseCacheRecord).where(
                    CorpseCacheRecord.session_id == session_id,
                    CorpseCacheRecord.cache_id == c_id,
                )
            ).scalar_one_or_none()

            if existing:
                existing.recovered = existing.recovered or bool(c.get("recovered", False))
            else:
                CorpseCacheRepository.create_cache(
                    db_session=db_session,
                    session_id=session_id,
                    floor_number=int(c.get("floor", c.get("floor_number", 1))),
                    col_amount=int(c.get("col", c.get("col_amount", 0))),
                    inventory=c.get("inventory", []),
                    gear=c.get("equipped", c.get("gear", {})),
                    fallen_name=c.get("fallen_name", "Fallen Hero"),
                    raid_id=c.get("raid_id"),
                    location=c.get("location"),
                    cache_id=c_id,
                )
        db_session.flush()


class MasterStateRepository:
    """
    Session-isolated GM Master & World State persistence (replaces secret_master_state.json).
    Guarantees thread-safe session creation and idempotent updates across concurrent transactions.
    """

    @staticmethod
    def save_master_state(
        db_session: Session,
        arg2: Union[str, dict],
        arg3: Union[str, dict, None] = None,
        session_id: Optional[str] = None,
    ) -> MasterGameStateRecord:
        """
        Persists GM master state into MasterGameStateRecord atomically.
        Polymorphic: supports both (db_session, master_dict, session_id="default")
        and (db_session, session_id, master_dict).
        """
        if isinstance(arg2, dict):
            master_state = arg2
            s_id = str(arg3 or session_id or "default").strip()
        else:
            s_id = str(arg2 or session_id or "default").strip()
            master_state = arg3 if isinstance(arg3, dict) else {}

        _ensure_campaign_session(db_session, s_id)

        clean_state = dict(master_state) if isinstance(master_state, dict) else {}
        clean_state.pop("player", None)  # Prevent embedding redundant player object

        turn_num = int(clean_state.get("turn_number", 1))
        campaign = str(clean_state.get("campaign_name", "SAO_Sandbox"))

        rec = db_session.execute(
            select(MasterGameStateRecord).where(MasterGameStateRecord.session_id == s_id)
        ).scalar_one_or_none()

        if rec:
            current_data = {}
            if rec.state_json:
                try:
                    current_data = json.loads(rec.state_json)
                except Exception:
                    current_data = {}
            # Preserve existing staging and world_state keys if not in clean_state
            for preserve_key in ("staging", "world_state", "sector", "world_status", "map_locations", "global_news"):
                if preserve_key in current_data and preserve_key not in clean_state:
                    clean_state[preserve_key] = current_data[preserve_key]

            rec.turn_number = turn_num
            rec.campaign_name = campaign
            rec.state_json = json.dumps(clean_state, ensure_ascii=False)
            rec.updated_at = datetime.now(timezone.utc)
            db_session.flush()
            return rec

        try:
            with db_session.begin_nested():
                rec = MasterGameStateRecord(
                    session_id=s_id,
                    turn_number=turn_num,
                    campaign_name=campaign,
                    state_json=json.dumps(clean_state, ensure_ascii=False),
                )
                db_session.add(rec)
                db_session.flush()
                return rec
        except Exception:
            rec = db_session.execute(
                select(MasterGameStateRecord).where(MasterGameStateRecord.session_id == s_id)
            ).scalar_one()
            rec.turn_number = turn_num
            rec.campaign_name = campaign
            rec.state_json = json.dumps(clean_state, ensure_ascii=False)
            rec.updated_at = datetime.now(timezone.utc)
            db_session.flush()
            return rec

    @staticmethod
    def load_master_state(
        db_session: Session,
        session_id: str = "default",
    ) -> dict:
        """Loads master state from MasterGameStateRecord with safe defaults."""
        s_id = str(session_id or "default").strip()
        rec = db_session.execute(
            select(MasterGameStateRecord).where(MasterGameStateRecord.session_id == s_id)
        ).scalar_one_or_none()
        if rec and rec.state_json:
            try:
                data = json.loads(rec.state_json)
                if isinstance(data, dict):
                    data["turn_number"] = rec.turn_number
                    data["campaign_name"] = rec.campaign_name
                    return data
            except Exception:
                pass
        return {
            "turn_number": 1,
            "campaign_name": "SAO_Sandbox",
            "entities": [],
            "environment": {
                "location": "Sector 1 Safe-Zone: Washington Borough, NJ",
                "description": "A fortified civilian sanctuary shielded by ancient runic barrier wards.",
                "hidden_traps": [],
                "environmental_effects": ["Safe-Zone Sanctuary Wards"],
            },
            "players": ["player", "companion_ren"],
        }

    @staticmethod
    def save_world_state(
        db_session: Session,
        arg2: Union[str, dict],
        arg3: Union[str, dict, None] = None,
        session_id: Optional[str] = None,
    ) -> MasterGameStateRecord:
        """Persists world state dictionary into MasterGameStateRecord atomically."""
        if isinstance(arg2, dict):
            world_state = arg2
            s_id = str(arg3 or session_id or "default").strip()
        else:
            s_id = str(arg2 or session_id or "default").strip()
            world_state = arg3 if isinstance(arg3, dict) else {}

        _ensure_campaign_session(db_session, s_id)

        rec = db_session.execute(
            select(MasterGameStateRecord).where(MasterGameStateRecord.session_id == s_id)
        ).scalar_one_or_none()

        curr_data = {}
        if rec and rec.state_json:
            try:
                curr_data = json.loads(rec.state_json)
            except Exception:
                curr_data = {}

        curr_data["world_state"] = world_state
        if isinstance(world_state, dict):
            for k in ("sector", "world_status", "map_locations", "global_news"):
                if k in world_state:
                    curr_data[k] = world_state[k]

        return MasterStateRepository.save_master_state(db_session, curr_data, session_id=s_id)

    @staticmethod
    def load_world_state(
        db_session: Session,
        session_id: str = "default",
    ) -> Optional[dict]:
        """Loads world state dictionary from MasterGameStateRecord."""
        s_id = str(session_id or "default").strip()
        rec = db_session.execute(
            select(MasterGameStateRecord).where(MasterGameStateRecord.session_id == s_id)
        ).scalar_one_or_none()
        if rec and rec.state_json:
            try:
                data = json.loads(rec.state_json)
                if isinstance(data, dict):
                    if "world_state" in data and isinstance(data["world_state"], dict):
                        return data["world_state"]
                    if "sector" in data:
                        return data
            except Exception:
                pass
        return None


# Backward-compatibility alias
WorldRepository = MasterStateRepository


class StagingRepository:
    """
    Session-isolated Staging Ground persistence.
    Manages visible room projection and autonomous action queues for turn resolution.
    Replaces singleton Staging_Ground/visible_room.json and Staging_Ground/action_queue.json.
    """

    @staticmethod
    def save_visible_room(
        db_session: Session,
        visible_room: dict,
        session_id: str = "default",
    ) -> MasterGameStateRecord:
        """Atomically persists visible room projection for a session."""
        s_id = str(session_id or "default").strip()
        master_dict = MasterStateRepository.load_master_state(db_session, session_id=s_id)
        staging = master_dict.setdefault("staging", {})
        staging["visible_room"] = visible_room
        rec = MasterStateRepository.save_master_state(db_session, master_dict, session_id=s_id)
        if s_id == "default":
            from backend.database.adapters import mirror_staging_ground_to_disk
            register_post_commit_hook(
                db_session,
                lambda: mirror_staging_ground_to_disk(
                    visible_room=visible_room,
                    session_id=s_id,
                ),
            )
        return rec

    @staticmethod
    def load_visible_room(
        db_session: Session,
        session_id: str = "default",
    ) -> dict:
        """Loads visible room projection for a session."""
        s_id = str(session_id or "default").strip()
        rec = db_session.execute(
            select(MasterGameStateRecord).where(MasterGameStateRecord.session_id == s_id)
        ).scalar_one_or_none()
        if rec:
            return rec.get_visible_room()
        return {
            "turn_number": 1,
            "environment": {
                "location": "Sector 1 Safe-Zone: Washington Borough, NJ",
                "description": "A fortified civilian sanctuary shielded by ancient runic barrier wards.",
                "environmental_effects": ["Safe-Zone Sanctuary Wards"],
            },
            "entities": [],
        }

    @staticmethod
    def queue_action(
        db_session: Session,
        action: dict,
        session_id: str = "default",
    ) -> List[dict]:
        """Appends an autonomous actor action to the session's action queue."""
        s_id = str(session_id or "default").strip()
        master_dict = MasterStateRepository.load_master_state(db_session, session_id=s_id)
        staging = master_dict.setdefault("staging", {})
        queue = staging.setdefault("action_queue", [])
        if not isinstance(queue, list):
            queue = []
            staging["action_queue"] = queue
        queue.append(action)
        MasterStateRepository.save_master_state(db_session, master_dict, session_id=s_id)
        if s_id == "default":
            from backend.database.adapters import mirror_staging_ground_to_disk
            register_post_commit_hook(
                db_session,
                lambda: mirror_staging_ground_to_disk(
                    action_queue=queue,
                    session_id=s_id,
                ),
            )
        return queue

    @staticmethod
    def save_action_queue(
        db_session: Session,
        actions: list,
        session_id: str = "default",
    ) -> MasterGameStateRecord:
        """Replaces the session's action queue with a new list of actions."""
        s_id = str(session_id or "default").strip()
        master_dict = MasterStateRepository.load_master_state(db_session, session_id=s_id)
        staging = master_dict.setdefault("staging", {})
        action_list = list(actions) if actions is not None else []
        staging["action_queue"] = action_list
        rec = MasterStateRepository.save_master_state(db_session, master_dict, session_id=s_id)
        if s_id == "default":
            from backend.database.adapters import mirror_staging_ground_to_disk
            register_post_commit_hook(
                db_session,
                lambda: mirror_staging_ground_to_disk(
                    action_queue=action_list,
                    session_id=s_id,
                ),
            )
        return rec

    @staticmethod
    def load_action_queue(
        db_session: Session,
        session_id: str = "default",
    ) -> List[dict]:
        """Loads the staged action queue for a session."""
        s_id = str(session_id or "default").strip()
        rec = db_session.execute(
            select(MasterGameStateRecord).where(MasterGameStateRecord.session_id == s_id)
        ).scalar_one_or_none()
        if rec:
            return rec.get_action_queue()
        return []

    @staticmethod
    def clear_action_queue(
        db_session: Session,
        session_id: str = "default",
    ) -> None:
        """Resets the session's action queue to empty after turn resolution."""
        StagingRepository.save_action_queue(db_session, [], session_id=session_id)

    @staticmethod
    def save_staging_state(
        db_session: Session,
        visible_room: Optional[dict] = None,
        action_queue: Optional[list] = None,
        session_id: str = "default",
    ) -> MasterGameStateRecord:
        """Saves visible room and/or action queue in a single transaction."""
        s_id = str(session_id or "default").strip()
        master_dict = MasterStateRepository.load_master_state(db_session, session_id=s_id)
        staging = master_dict.setdefault("staging", {})
        if visible_room is not None:
            staging["visible_room"] = visible_room
        if action_queue is not None:
            staging["action_queue"] = list(action_queue)
        rec = MasterStateRepository.save_master_state(db_session, master_dict, session_id=s_id)
        if s_id == "default":
            from backend.database.adapters import mirror_staging_ground_to_disk
            register_post_commit_hook(
                db_session,
                lambda: mirror_staging_ground_to_disk(
                    visible_room=visible_room,
                    action_queue=action_queue,
                    session_id=s_id,
                ),
            )
        return rec

    @staticmethod
    def load_staging_state(
        db_session: Session,
        session_id: str = "default",
    ) -> Dict[str, Any]:
        """Loads both visible room and action queue for a session."""
        return {
            "visible_room": StagingRepository.load_visible_room(db_session, session_id=session_id),
            "action_queue": StagingRepository.load_action_queue(db_session, session_id=session_id),
        }


class PartyRepository:
    """
    Session-isolated Party Companion persistence.
    Guarantees ACID transactions, per-session isolation, and atomic disk mirroring
    strictly for the 'default' session.
    """

    @staticmethod
    def _normalize_slug(c: dict) -> str:
        """Derives a consistent slug for a companion dictionary."""
        raw = c.get("slug") or c.get("id") or c.get("name") or "companion"
        raw_str = str(raw).strip().lower().replace(" ", "_")
        if raw_str.startswith("companion_"):
            raw_str = raw_str[10:]
        return raw_str if raw_str else "companion"

    @staticmethod
    def save_party(
        db_session: Session,
        companions: Union[list, dict],
        session_id: str = "default",
        mirror_disk: bool = True,
        character_slug: Optional[str] = None,
        base_dir: Optional[str] = None,
    ) -> List[PartyCompanionRecord]:
        """
        Synchronizes party companion records for a session in-place.
        Handles both list-of-dicts and dict-of-dicts.
        Registers an atomic post-commit hook for disk mirroring when session_id == 'default'.
        """
        session_id = str(session_id or "default").strip()
        _ensure_party_companion_columns(db_session)
        _ensure_campaign_session(db_session, session_id)

        # 1. Normalize input to list of dicts
        comp_list: List[Dict[str, Any]] = []
        if isinstance(companions, dict):
            comp_list = [v for v in companions.values() if isinstance(v, dict)]
        elif isinstance(companions, list):
            comp_list = [c for c in companions if isinstance(c, dict)]

        # 2. Fetch existing session companions
        existing = {
            r.companion_slug: r
            for r in db_session.execute(
                select(PartyCompanionRecord).where(PartyCompanionRecord.session_id == session_id)
            ).scalars().all()
        }

        current_slugs = set()
        persisted_records: List[PartyCompanionRecord] = []

        for c in comp_list:
            c_slug = PartyRepository._normalize_slug(c)
            current_slugs.add(c_slug)

            # Defensive field extraction
            name_val = str(c.get("companion_name") or c.get("name") or c_slug.capitalize())
            lvl_val = int(c.get("level", 1))
            hp_val = int(c.get("hp", 30))
            max_hp_val = int(c.get("max_hp", max(hp_val, 30)))
            ac_val = int(c.get("ac", 15))
            recruited_val = bool(c.get("recruited", True))
            active_val = bool(c.get("is_active") if "is_active" in c else c.get("active", True))

            # Specialized JSON fields
            equipped_val = json.dumps(c.get("equipped", {}), ensure_ascii=False)
            stats_val = json.dumps(c.get("stats", {}), ensure_ascii=False)
            skills_val = json.dumps(c.get("skills", {}), ensure_ascii=False)
            payload_val = json.dumps(c, ensure_ascii=False)

            if c_slug in existing:
                rec = existing[c_slug]
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
                rec.companion_data_json = payload_val
            else:
                try:
                    with db_session.begin_nested():
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
                            companion_data_json=payload_val,
                        )
                        db_session.add(rec)
                        db_session.flush()
                except Exception:
                    rec = db_session.execute(
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
                    rec.companion_data_json = payload_val

            persisted_records.append(rec)

        # 3. Prune old records no longer present in current roster
        for old_slug, old_rec in existing.items():
            if old_slug not in current_slugs:
                db_session.delete(old_rec)

        db_session.flush()

        # 4. Atomic Disk Mirroring Synchronization
        # STRICT RULE: Mirror to root Party/ and Entities/ ONLY for 'default' session!
        if mirror_disk and session_id == "default":
            from backend.database.adapters import mirror_party_to_disk
            # Register post-commit hook so disk is touched ONLY on successful DB commit
            register_post_commit_hook(
                db_session,
                lambda: mirror_party_to_disk(
                    comp_list,
                    slug=character_slug,
                    base_dir=base_dir,
                    mirror_to_root=True,
                ),
            )
        elif mirror_disk and character_slug and session_id != "default":
            from backend.database.adapters import mirror_party_to_disk
            # Custom session mirrors ONLY to character-specific save folder, NEVER root!
            register_post_commit_hook(
                db_session,
                lambda: mirror_party_to_disk(
                    comp_list,
                    slug=character_slug,
                    base_dir=base_dir,
                    mirror_to_root=False,
                ),
            )

        return persisted_records

    @staticmethod
    def load_party(
        db_session: Session,
        session_id: str = "default",
        seed_from_disk_if_empty: bool = True,
    ) -> List[dict]:
        """
        Loads party companions for a session from the relational database.
        If default session has no records yet and seed_from_disk_if_empty is True,
        automatically seeds the canonical companions from Party/*.json.
        """
        session_id = str(session_id or "default").strip()
        _ensure_party_companion_columns(db_session)
        records = db_session.execute(
            select(PartyCompanionRecord).where(PartyCompanionRecord.session_id == session_id)
        ).scalars().all()

        if not records and session_id == "default" and seed_from_disk_if_empty:
            PartyRepository.seed_default_party_from_disk(db_session, session_id=session_id)
            records = db_session.execute(
                select(PartyCompanionRecord).where(PartyCompanionRecord.session_id == session_id)
            ).scalars().all()

        comps = []
        for r in records:
            comps.append(r.to_companion_dict())
        return comps

    @staticmethod
    def seed_default_party_from_disk(
        db_session: Session,
        party_dir: Optional[str] = None,
        session_id: str = "default",
    ) -> int:
        """
        Seeds canonical companions from Party/*.json into the campaign session.
        Returns count of seeded companions.
        """
        from backend.database.adapters import get_base_dir, atomic_read_json
        base_dir = get_base_dir()
        p_dir = party_dir or os.path.join(base_dir, "Party")
        if not os.path.exists(p_dir):
            return 0

        seeded_comps = []
        for fname in sorted(os.listdir(p_dir)):
            if fname.endswith(".json"):
                fpath = os.path.join(p_dir, fname)
                data = atomic_read_json(fpath, default=None)
                if isinstance(data, dict):
                    if not data.get("id"):
                        data["id"] = fname[:-5]
                    seeded_comps.append(data)

        if seeded_comps:
            PartyRepository.save_party(
                db_session=db_session,
                companions=seeded_comps,
                session_id=session_id,
                mirror_disk=False,  # Disk files already exist
            )
        return len(seeded_comps)
