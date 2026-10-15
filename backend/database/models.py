"""
backend/database/models.py
SQLAlchemy 2.0 ORM Declarative Models for SAO Sandbox V2.
Provides dual coverage: normalized relational columns for fast queries/joins/indexing,
plus JSON fallback columns for 100% mechanical fidelity across all 13 phases.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    synonym,
)


class Base(DeclarativeBase):
    """Base declarative class for SAO Sandbox V2 database entities."""
    pass


class CampaignSessionRecord(Base):
    """Represents an isolated multi-player campaign session."""
    __tablename__ = "campaign_sessions"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_name: Mapped[str] = mapped_column(String(128), nullable=False, default="Default Campaign")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships to child session-isolated entities
    characters: Mapped[List[CharacterRecord]] = relationship(
        back_populates="campaign_session",
        cascade="all, delete-orphan",
    )
    party_companions: Mapped[List[PartyCompanionRecord]] = relationship(
        back_populates="campaign_session",
        cascade="all, delete-orphan",
    )
    master_game_state: Mapped[Optional[MasterGameStateRecord]] = relationship(
        back_populates="campaign_session",
        uselist=False,
        cascade="all, delete-orphan",
    )
    corpse_caches: Mapped[List[CorpseCacheRecord]] = relationship(
        back_populates="campaign_session",
        cascade="all, delete-orphan",
    )
    chat_messages: Mapped[List[ChatMessageRecord]] = relationship(
        back_populates="campaign_session",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "session_name": self.session_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CharacterRecord(Base):
    """
    Authoritative character record with dual coverage:
    - Normalized columns for common gameplay attributes (name, level, HP, col, XP, class, race)
    - Normalized child tables (equipped_slots, anatomical_grafts, active_debuffs, skill_masteries, archived_skills)
    - Fallback JSON columns (stats_json, raw_data_json) for 100% mechanical fidelity
    """
    __tablename__ = "characters"
    __table_args__ = (
        UniqueConstraint("session_id", "slug", name="uq_session_character_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("campaign_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    hp: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    max_hp: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    col: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    xp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gender: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    race: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    character_class: Mapped[Optional[str]] = mapped_column("character_class", String(128), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

    # Dual Coverage: Structured stats JSON & Full original payload fallback
    stats_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    raw_data_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    campaign_session: Mapped[CampaignSessionRecord] = relationship(back_populates="characters")
    equipped_slots: Mapped[List[EquippedSlotRecord]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )
    anatomical_grafts: Mapped[List[AnatomicalGraftRecord]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )
    active_debuffs: Mapped[List[ActiveDebuffRecord]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )
    skill_masteries: Mapped[List[SkillMasteryRecord]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )
    archived_skills: Mapped[List[ArchivedSkillRecord]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )
    chat_messages: Mapped[List[ChatMessageRecord]] = relationship(back_populates="character")

    def to_player_dict(self) -> Dict[str, Any]:
        """
        Reconstructs the full player dictionary expected by app.py and backend.mechanics.
        Merges normalized relational fields with raw_data_json fallback to guarantee
        100% mechanical fidelity with zero loss of nested systems.
        """
        base_data: Dict[str, Any] = {}
        if self.raw_data_json:
            try:
                parsed = json.loads(self.raw_data_json)
                if isinstance(parsed, dict):
                    base_data = parsed.get("player", parsed)
            except Exception:
                base_data = {}

        # Overlay normalized core columns
        base_data["name"] = self.name
        base_data["level"] = self.level
        base_data["hp"] = self.hp
        base_data["max_hp"] = self.max_hp
        base_data["col"] = self.col
        base_data["xp"] = self.xp
        if self.gender:
            base_data["gender"] = self.gender
        if self.race:
            base_data["race"] = self.race
        if self.character_class:
            base_data["class"] = self.character_class
        if self.location:
            base_data["location"] = self.location

        # Stats dictionary
        if self.stats_json:
            try:
                base_data["stats"] = json.loads(self.stats_json)
            except Exception:
                pass

        # Overlay equipped slots
        if self.equipped_slots:
            equipped_map = base_data.setdefault("equipped", {})
            for slot in self.equipped_slots:
                equipped_map[slot.slot_key] = slot.item_name

        # Overlay anatomical grafts
        if self.anatomical_grafts:
            graft_sys = base_data.setdefault("graft_system", {})
            installed_grafts = graft_sys.setdefault("installed_grafts", {})
            grafts_dict = base_data.setdefault("grafts", {})
            for graft in self.anatomical_grafts:
                g_info = {"name": graft.graft_name, "slot": graft.slot_key, "strain": graft.unit_strain}
                if graft.graft_data_json:
                    try:
                        g_info.update(json.loads(graft.graft_data_json))
                    except Exception:
                        pass
                grafts_dict[graft.slot_key] = g_info
                installed_grafts[graft.slot_key] = g_info

        # Overlay active debuffs
        if self.active_debuffs:
            debuffs_list = []
            for db in self.active_debuffs:
                db_dict = {
                    "debuff_id": db.debuff_id,
                    "name": db.name,
                    "ac_penalty": db.ac_penalty,
                    "dr_override": db.dr_override,
                    "turns_remaining": db.turns_remaining,
                    "source": db.source or "",
                }
                if db.debuff_data_json:
                    try:
                        extra = json.loads(db.debuff_data_json)
                        if isinstance(extra, dict):
                            db_dict.update(extra)
                    except Exception:
                        pass
                debuffs_list.append(db_dict)
            base_data["active_debuffs"] = debuffs_list

        # Overlay skills
        if self.skill_masteries:
            skills_dict = base_data.setdefault("skills", {})
            for sm in self.skill_masteries:
                s_info = {
                    "mastery": sm.mastery_level,
                    "tier": sm.tier or "Novice",
                    "description": "",
                    "milestones_unlocked": [],
                }
                if sm.skill_data_json:
                    try:
                        s_extra = json.loads(sm.skill_data_json)
                        if isinstance(s_extra, dict):
                            s_info.update(s_extra)
                    except Exception:
                        pass
                skills_dict[sm.skill_name] = s_info

        # Overlay archived skills
        if self.archived_skills:
            archived_dict = base_data.setdefault("archived_base_skills", {})
            for arch in self.archived_skills:
                a_info = {
                    "name": arch.skill_name,
                    "previous_mastery": arch.mastery_level,
                    "archived_reason": arch.archived_reason or "",
                    "fused_into": arch.fused_into or "",
                    "was_spell": arch.was_spell,
                }
                if arch.skill_data_json:
                    try:
                        a_extra = json.loads(arch.skill_data_json)
                        if isinstance(a_extra, dict):
                            a_info.update(a_extra)
                    except Exception:
                        pass
                archived_dict[arch.skill_name] = a_info

        return base_data


class EquippedSlotRecord(Base):
    """Normalized equipment slot row for multi-limb loadout tracking."""
    __tablename__ = "equipped_slots"
    __table_args__ = (
        UniqueConstraint("character_id", "slot_key", name="uq_character_equipped_slot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slot_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    item_name: Mapped[str] = mapped_column(String(128), nullable=False)
    item_data_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    character: Mapped[CharacterRecord] = relationship(back_populates="equipped_slots")

    def to_dict(self) -> Dict[str, Any]:
        data = {"slot_key": self.slot_key, "item_name": self.item_name}
        if self.item_data_json:
            try:
                data["item_data"] = json.loads(self.item_data_json)
            except Exception:
                data["item_data"] = {}
        return data


class AnatomicalGraftRecord(Base):
    """Normalized anatomical graft row supporting 9+ slots and metabolic strain tracking."""
    __tablename__ = "anatomical_grafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slot_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    graft_name: Mapped[str] = mapped_column(String(128), nullable=False)
    unit_strain: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    bio_strain: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    graft_data_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    character: Mapped[CharacterRecord] = relationship(back_populates="anatomical_grafts")

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "slot_key": self.slot_key,
            "graft_name": self.graft_name,
            "unit_strain": self.unit_strain,
            "bio_strain": self.bio_strain,
        }
        if self.graft_data_json:
            try:
                data["graft_data"] = json.loads(self.graft_data_json)
            except Exception:
                data["graft_data"] = {}
        return data


class ActiveDebuffRecord(Base):
    """Normalized active combat debuff row supporting AC penalties and DR overrides."""
    __tablename__ = "active_debuffs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    character_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    entity_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    debuff_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    ac_penalty: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dr_override: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    turns_remaining: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    source: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    debuff_data_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    character: Mapped[Optional[CharacterRecord]] = relationship(back_populates="active_debuffs")

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "debuff_id": self.debuff_id,
            "name": self.name,
            "ac_penalty": self.ac_penalty,
            "dr_override": self.dr_override,
            "turns_remaining": self.turns_remaining,
            "source": self.source or "",
        }
        if self.debuff_data_json:
            try:
                extra = json.loads(self.debuff_data_json)
                if isinstance(extra, dict):
                    data.update(extra)
            except Exception:
                pass
        return data


class SkillMasteryRecord(Base):
    """Normalized active skill mastery (1–1000 scale) and fusion indicator."""
    __tablename__ = "skill_masteries"
    __table_args__ = (
        UniqueConstraint("character_id", "skill_name", name="uq_character_skill_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    mastery_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_fusion: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    tier: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    skill_data_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    character: Mapped[CharacterRecord] = relationship(back_populates="skill_masteries")

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "skill_name": self.skill_name,
            "mastery_level": self.mastery_level,
            "is_fusion": self.is_fusion,
            "tier": self.tier or "Novice",
        }
        if self.skill_data_json:
            try:
                extra = json.loads(self.skill_data_json)
                if isinstance(extra, dict):
                    data.update(extra)
            except Exception:
                pass
        return data


class ArchivedSkillRecord(Base):
    """Archived foundational skills consumed during Ability Fusion, retained for relearning."""
    __tablename__ = "archived_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    character_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    mastery_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    archived_reason: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    fused_into: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    was_spell: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    skill_data_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationship
    character: Mapped[CharacterRecord] = relationship(back_populates="archived_skills")

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "skill_name": self.skill_name,
            "mastery_level": self.mastery_level,
            "archived_reason": self.archived_reason or "",
            "fused_into": self.fused_into or "",
            "was_spell": self.was_spell,
        }
        if self.skill_data_json:
            try:
                extra = json.loads(self.skill_data_json)
                if isinstance(extra, dict):
                    data.update(extra)
            except Exception:
                pass
        return data


class PartyCompanionRecord(Base):
    """Session-isolated party companion record preventing cross-player state pollution."""
    __tablename__ = "party_companions"
    __table_args__ = (
        UniqueConstraint("session_id", "companion_slug", name="uq_session_companion_slug"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("campaign_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    companion_slug: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    hp: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    max_hp: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    ac: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    recruited: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Dedicated JSON columns matching M3 specification
    equipped_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="{}")
    stats_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="{}")
    skills_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="{}")

    # Complete un-truncated mechanical payload fallback
    companion_data_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    # Synonyms for attribute parity
    companion_name = synonym("name")
    is_active = synonym("active")

    # Relationship
    campaign_session: Mapped[CampaignSessionRecord] = relationship(back_populates="party_companions")

    def to_companion_dict(self) -> Dict[str, Any]:
        """
        Reconstructs the full companion dictionary expected by app.py and backend.mechanics.
        Merges normalized columns with JSON payloads.
        """
        data: Dict[str, Any] = {}
        if self.companion_data_json:
            try:
                parsed = json.loads(self.companion_data_json)
                if isinstance(parsed, dict):
                    data = parsed
            except Exception:
                data = {}

        # Overlay normalized core columns
        data["slug"] = self.companion_slug
        data["id"] = data.get("id") or (f"companion_{self.companion_slug}" if not self.companion_slug.startswith("companion_") else self.companion_slug)
        data["name"] = self.name
        data["companion_name"] = self.name
        data["level"] = self.level
        data["hp"] = self.hp
        data["max_hp"] = self.max_hp
        data["ac"] = self.ac
        data["recruited"] = self.recruited
        data["active"] = self.active
        data["is_active"] = self.active

        # Overlay dedicated JSON sub-dictionaries if present
        if self.equipped_json:
            try:
                data["equipped"] = json.loads(self.equipped_json)
            except Exception:
                pass
        if self.stats_json:
            try:
                data["stats"] = json.loads(self.stats_json)
            except Exception:
                pass
        if self.skills_json:
            try:
                data["skills"] = json.loads(self.skills_json)
            except Exception:
                pass

        return data


class MasterGameStateRecord(Base):
    """Session-isolated GM Master & World State (replaces singleton secret_master_state.json)."""
    __tablename__ = "master_game_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("campaign_sessions.session_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    campaign_name: Mapped[str] = mapped_column(String(128), nullable=False, default="SAO_Sandbox")
    state_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship
    campaign_session: Mapped[CampaignSessionRecord] = relationship(back_populates="master_game_state")

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "campaign_name": self.campaign_name,
            "turn_number": self.turn_number,
        }
        if self.state_json:
            try:
                parsed = json.loads(self.state_json)
                if isinstance(parsed, dict):
                    data.update(parsed)
            except Exception:
                pass
        return data

    def get_visible_room(self) -> Dict[str, Any]:
        """Extracts visible room dictionary from state_json staging namespace."""
        full_dict = self.to_dict()
        staging = full_dict.get("staging")
        if isinstance(staging, dict) and "visible_room" in staging and isinstance(staging["visible_room"], dict):
            return staging["visible_room"]
        # Fallback projection from environment
        return {
            "turn_number": self.turn_number,
            "environment": full_dict.get("environment", {}),
            "entities": [
                {"id": e.get("id"), "name": e.get("name"), "type": e.get("type"), "status": e.get("status")}
                for e in full_dict.get("entities", [])
                if isinstance(e, dict)
            ],
        }

    def get_action_queue(self) -> List[Dict[str, Any]]:
        """Extracts staged action queue list from state_json staging namespace."""
        full_dict = self.to_dict()
        staging = full_dict.get("staging")
        if isinstance(staging, dict) and isinstance(staging.get("action_queue"), list):
            return staging["action_queue"]
        if isinstance(full_dict.get("action_queue"), list):
            return full_dict["action_queue"]
        return []


class CorpseCacheRecord(Base):
    """Persistent Floor Corpse Cache tracking dropped Col and inventory on Vanguard death."""
    __tablename__ = "corpse_caches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("campaign_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cache_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    fallen_name: Mapped[str] = mapped_column(String(128), nullable=False)
    floor_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raid_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    col_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inventory_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    gear_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    recovered: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship
    campaign_session: Mapped[CampaignSessionRecord] = relationship(back_populates="corpse_caches")

    def to_cache_dict(self) -> Dict[str, Any]:
        inv: List[Any] = []
        gear: Dict[str, Any] = {}
        if self.inventory_json:
            try:
                inv = json.loads(self.inventory_json)
            except Exception:
                inv = []
        if self.gear_json:
            try:
                gear = json.loads(self.gear_json)
            except Exception:
                gear = {}
        return {
            "cache_id": self.cache_id,
            "fallen_name": self.fallen_name,
            "floor": self.floor_number,
            "raid_id": self.raid_id,
            "location": self.location,
            "col": self.col_amount,
            "inventory": inv,
            "equipped": gear,
            "recovered": self.recovered,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ChatMessageRecord(Base):
    """Session-scoped narrative and tactical message log."""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("campaign_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    character_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("characters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    subagent_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # Relationships
    campaign_session: Mapped[CampaignSessionRecord] = relationship(back_populates="chat_messages")
    character: Mapped[Optional[CharacterRecord]] = relationship(back_populates="chat_messages")

    def to_message_dict(self) -> Dict[str, Any]:
        msg: Dict[str, Any] = {
            "role": self.role,
            "content": self.content,
        }
        if self.subagent_log:
            msg["subagent_log"] = self.subagent_log
        if self.image_path:
            msg["image_path"] = self.image_path
        if self.timestamp:
            msg["timestamp"] = self.timestamp.isoformat()
        return msg
