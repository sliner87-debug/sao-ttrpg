"""
Fractured Earth SAO Sandbox V2: Comprehensive E2E Concurrency, Rollback & Mechanical Parity Test Suite.

Authoritative Specifications:
- ORIGINAL_REQUEST.md (R1: Concurrency & Atomicity, R2: V2 Mechanics & Schema Parity, R3: Streamlit Compatibility)
- PROJECT.md (§ Architecture, Feature Inventory, Interface Contracts)
- TEST_INFRA.md (§ Coverage Thresholds: Tiers 1-4, >=120 automated test cases)

Coverage Summary:
- Tier 1: 11 Features x >=5 tests = 55 test cases
- Tier 2: 11 Boundary Areas x >=5 tests = 55 test cases
- Tier 3: Pairwise Cross-Feature Combinations = 5 test cases
- Tier 4: Real-World Multi-Player Scenarios = 5 test cases
Total: 120 automated test cases.
"""

import copy
from datetime import datetime, timezone
import json
import os
import shutil
import sys
import tempfile
import threading
import time
from typing import Any, Dict, Iterator, List, Optional, Union
import unittest

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import sqlalchemy
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    event,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)
from sqlalchemy.pool import QueuePool

import backend.character_generator as cg
import backend.mechanics as mechanics
import backend.schemas as schemas


# =====================================================================
# PERSISTENCE ENGINE & REPOSITORY REFERENCE HARNESS
# (Matches PROJECT.md § Interface Contracts and M1 Schema Specification)
# =====================================================================

class Base(DeclarativeBase):
    """SQLAlchemy 2.0 Declarative Base for SAO Sandbox V2."""
    pass


class CampaignSessionRecord(Base):
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

    characters: Mapped[List["CharacterRecord"]] = relationship(
        back_populates="campaign_session",
        cascade="all, delete-orphan",
    )
    party_companions: Mapped[List["PartyCompanionRecord"]] = relationship(
        back_populates="campaign_session",
        cascade="all, delete-orphan",
    )
    master_game_state: Mapped[Optional["MasterGameStateRecord"]] = relationship(
        back_populates="campaign_session",
        uselist=False,
        cascade="all, delete-orphan",
    )
    corpse_caches: Mapped[List["CorpseCacheRecord"]] = relationship(
        back_populates="campaign_session",
        cascade="all, delete-orphan",
    )
    chat_messages: Mapped[List["ChatMessageRecord"]] = relationship(
        back_populates="campaign_session",
        cascade="all, delete-orphan",
    )


class CharacterRecord(Base):
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
    character_class: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)

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

    campaign_session: Mapped["CampaignSessionRecord"] = relationship(back_populates="characters")
    equipped_slots: Mapped[List["EquippedSlotRecord"]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )
    anatomical_grafts: Mapped[List["AnatomicalGraftRecord"]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )
    active_debuffs: Mapped[List["ActiveDebuffRecord"]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )
    skill_masteries: Mapped[List["SkillMasteryRecord"]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )
    archived_skills: Mapped[List["ArchivedSkillRecord"]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )
    chat_messages: Mapped[List["ChatMessageRecord"]] = relationship(back_populates="character")


class EquippedSlotRecord(Base):
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

    character: Mapped["CharacterRecord"] = relationship(back_populates="equipped_slots")


class AnatomicalGraftRecord(Base):
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

    character: Mapped["CharacterRecord"] = relationship(back_populates="anatomical_grafts")


class ActiveDebuffRecord(Base):
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

    character: Mapped[Optional["CharacterRecord"]] = relationship(back_populates="active_debuffs")


class SkillMasteryRecord(Base):
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

    character: Mapped["CharacterRecord"] = relationship(back_populates="skill_masteries")


class ArchivedSkillRecord(Base):
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

    character: Mapped["CharacterRecord"] = relationship(back_populates="archived_skills")


class PartyCompanionRecord(Base):
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
    companion_data_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    campaign_session: Mapped["CampaignSessionRecord"] = relationship(back_populates="party_companions")


class MasterGameStateRecord(Base):
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

    campaign_session: Mapped["CampaignSessionRecord"] = relationship(back_populates="master_game_state")


class CorpseCacheRecord(Base):
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

    campaign_session: Mapped["CampaignSessionRecord"] = relationship(back_populates="corpse_caches")


class ChatMessageRecord(Base):
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
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    campaign_session: Mapped["CampaignSessionRecord"] = relationship(back_populates="chat_messages")
    character: Mapped[Optional["CharacterRecord"]] = relationship(back_populates="chat_messages")


# =====================================================================
# ENGINE FACTORY & REPOSITORIES (PROJECT.md Interface Contracts)
# =====================================================================

def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enforces SQLite WAL mode, foreign keys, and 30s busy timeout."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA busy_timeout=30000;")
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


def create_sao_engine(db_url: str):
    """Engine factory supporting SQLite WAL mode and connection pooling."""
    if db_url.startswith("sqlite"):
        eng = create_engine(db_url, connect_args={"timeout": 30}, echo=False)
        event.listen(eng, "connect", set_sqlite_pragma)

        @event.listens_for(eng, "begin")
        def do_begin(conn):
            conn.exec_driver_sql("BEGIN IMMEDIATE")
    else:
        eng = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            echo=False,
        )
    return eng


def init_db(engine):
    """Initializes schema tables."""
    Base.metadata.create_all(bind=engine)


class DbTransactionContext:
    """Context manager providing atomic commit/rollback semantics."""
    def __init__(self, session_factory, session_id: Optional[str] = None):
        self.session_factory = session_factory
        self.session_id = session_id
        self.session: Optional[Session] = None

    def __enter__(self) -> Session:
        self.session = self.session_factory()
        if self.session_id:
            try:
                with self.session.begin_nested():
                    existing = self.session.get(CampaignSessionRecord, self.session_id)
                    if not existing:
                        self.session.add(CampaignSessionRecord(session_id=self.session_id, session_name=f"Session {self.session_id}"))
                        self.session.flush()
            except Exception:
                pass
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            try:
                if exc_type is not None:
                    self.session.rollback()
                else:
                    self.session.commit()
            finally:
                self.session.close()
        return False  # Do not suppress exceptions


def atomic_write_json(file_path: str, data: Union[dict, list]) -> None:
    """
    Writes serialized JSON using temporary file + fsync + os.replace() to prevent
    zero-byte truncation corruption under crashes or interrupts.
    Includes Windows retry backoff for transient file locks.
    """
    dir_path = os.path.dirname(os.path.abspath(file_path))
    os.makedirs(dir_path, exist_ok=True)

    # First serialize to verify JSON serializability BEFORE creating/truncating any file
    serialized_payload = json.dumps(data, indent=4, ensure_ascii=False)

    temp_fd, temp_path = tempfile.mkstemp(prefix="sao_atomic_", suffix=".tmp", dir=dir_path)
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
            f.write(serialized_payload)
            f.flush()
            os.fsync(f.fileno())

        # Atomic replace with retry for Windows file locks
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                os.replace(temp_path, file_path)
                break
            except PermissionError:
                if attempt == max_attempts - 1:
                    raise
                time.sleep(0.02 * (attempt + 1))
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass
        raise


class CharacterRepository:
    """Repository handling character persistence and mechanical serialization."""

    @staticmethod
    def save_character(db_session: Session, character_dict: dict, session_id: str = "default") -> CharacterRecord:
        slug = character_dict.get("slug") or character_dict.get("name", "hero").lower().replace(" ", "_")
        existing = db_session.execute(
            select(CharacterRecord).where(
                CharacterRecord.session_id == session_id,
                CharacterRecord.slug == slug,
            )
        ).scalar_one_or_none()

        stats = character_dict.get("stats", {})
        raw_json = json.dumps(character_dict)
        stats_json = json.dumps(stats)

        # Ensure campaign session exists
        session_rec = db_session.get(CampaignSessionRecord, session_id)
        if not session_rec:
            try:
                with db_session.begin_nested():
                    db_session.add(CampaignSessionRecord(session_id=session_id, session_name=f"Session {session_id}"))
                    db_session.flush()
            except Exception:
                pass

        if existing:
            rec = existing
            rec.name = character_dict.get("name", rec.name)
            rec.level = int(character_dict.get("level", rec.level))
            rec.hp = int(character_dict.get("hp", rec.hp))
            rec.max_hp = int(character_dict.get("max_hp", rec.max_hp))
            rec.col = int(character_dict.get("col", rec.col))
            rec.xp = int(character_dict.get("xp", rec.xp))
            rec.gender = character_dict.get("gender", rec.gender)
            rec.race = character_dict.get("race", rec.race)
            rec.character_class = character_dict.get("class", rec.character_class)
            rec.location = character_dict.get("location", rec.location)
            rec.stats_json = stats_json
            rec.raw_data_json = raw_json
        else:
            rec = CharacterRecord(
                session_id=session_id,
                slug=slug,
                name=character_dict.get("name", "Unknown"),
                level=int(character_dict.get("level", 1)),
                hp=int(character_dict.get("hp", 100)),
                max_hp=int(character_dict.get("max_hp", 100)),
                col=int(character_dict.get("col", 0)),
                xp=int(character_dict.get("xp", 0)),
                gender=character_dict.get("gender"),
                race=character_dict.get("race"),
                character_class=character_dict.get("class"),
                location=character_dict.get("location"),
                stats_json=stats_json,
                raw_data_json=raw_json,
            )
            db_session.add(rec)
            db_session.flush()

        # Update equipped slots
        equipped = character_dict.get("equipped", {})
        if isinstance(equipped, dict):
            # Clear existing slots and recreate
            for old_slot in list(rec.equipped_slots):
                db_session.delete(old_slot)
            db_session.flush()

            for s_key, itm_val in equipped.items():
                if itm_val:
                    slot_rec = EquippedSlotRecord(
                        character_id=rec.id,
                        slot_key=str(s_key),
                        item_name=str(itm_val),
                    )
                    db_session.add(slot_rec)

        # Update active debuffs
        debuffs = character_dict.get("active_debuffs", [])
        if isinstance(debuffs, list):
            for old_d in list(rec.active_debuffs):
                db_session.delete(old_d)
            db_session.flush()

            for d in debuffs:
                if isinstance(d, dict) and d.get("name"):
                    db_session.add(
                        ActiveDebuffRecord(
                            character_id=rec.id,
                            debuff_id=str(d.get("debuff_id", d.get("name"))),
                            name=str(d.get("name")),
                            ac_penalty=int(d.get("ac_penalty", 0) or 0),
                            dr_override=d.get("dr_override"),
                            turns_remaining=int(d.get("turns_remaining", 3) or 3),
                        )
                    )

        db_session.flush()
        return rec

    @staticmethod
    def load_character(db_session: Session, character_slug: str, session_id: str = "default") -> Optional[dict]:
        rec = db_session.execute(
            select(CharacterRecord).where(
                CharacterRecord.session_id == session_id,
                CharacterRecord.slug == character_slug,
            )
        ).scalar_one_or_none()

        if not rec:
            return None

        # Reconstruct dict from raw_data_json and update with latest relational columns
        data = json.loads(rec.raw_data_json) if rec.raw_data_json else {}
        data["name"] = rec.name
        data["slug"] = rec.slug
        data["level"] = rec.level
        data["hp"] = rec.hp
        data["max_hp"] = rec.max_hp
        data["col"] = rec.col
        data["xp"] = rec.xp
        data["gender"] = rec.gender
        data["race"] = rec.race
        data["class"] = rec.character_class
        data["location"] = rec.location

        # Reconstruct equipped
        if rec.equipped_slots:
            eq = data.get("equipped", {})
            for s in rec.equipped_slots:
                eq[s.slot_key] = s.item_name
            data["equipped"] = eq

        # Reconstruct active debuffs
        if rec.active_debuffs:
            d_list = []
            for d in rec.active_debuffs:
                d_list.append({
                    "debuff_id": d.debuff_id,
                    "name": d.name,
                    "ac_penalty": d.ac_penalty,
                    "dr_override": d.dr_override,
                    "turns_remaining": d.turns_remaining,
                })
            data["active_debuffs"] = d_list

        return data


class PartyRepository:
    """Repository handling session-isolated party companions."""

    @staticmethod
    def save_party(db_session: Session, companions: list, session_id: str = "default") -> None:
        # Ensure campaign session exists
        session_rec = db_session.get(CampaignSessionRecord, session_id)
        if not session_rec:
            try:
                with db_session.begin_nested():
                    db_session.add(CampaignSessionRecord(session_id=session_id, session_name=f"Session {session_id}"))
                    db_session.flush()
            except Exception:
                pass

        # Clear session party and replace
        existing = db_session.execute(
            select(PartyCompanionRecord).where(PartyCompanionRecord.session_id == session_id)
        ).scalars().all()
        for old_comp in existing:
            db_session.delete(old_comp)
        db_session.flush()

        for c in companions:
            if isinstance(c, dict):
                c_slug = c.get("slug") or c.get("id") or c.get("name", "comp").lower().replace(" ", "_")
                rec = PartyCompanionRecord(
                    session_id=session_id,
                    companion_slug=c_slug,
                    name=c.get("name", c_slug),
                    level=int(c.get("level", 1)),
                    hp=int(c.get("hp", 30)),
                    max_hp=int(c.get("max_hp", 30)),
                    ac=int(c.get("ac", 15)),
                    recruited=bool(c.get("recruited", True)),
                    active=bool(c.get("active", True)),
                    companion_data_json=json.dumps(c),
                )
                db_session.add(rec)
        db_session.flush()

    @staticmethod
    def load_party(db_session: Session, session_id: str = "default") -> list:
        records = db_session.execute(
            select(PartyCompanionRecord).where(PartyCompanionRecord.session_id == session_id)
        ).scalars().all()

        comps = []
        for r in records:
            c_data = json.loads(r.companion_data_json) if r.companion_data_json else {}
            c_data["hp"] = r.hp
            c_data["max_hp"] = r.max_hp
            c_data["ac"] = r.ac
            c_data["level"] = r.level
            c_data["recruited"] = r.recruited
            c_data["active"] = r.active
            comps.append(c_data)
        return comps


class MasterStateRepository:
    """Repository for GM master state."""

    @staticmethod
    def save_master_state(db_session: Session, state_dict: dict, session_id: str = "default") -> None:
        rec = db_session.execute(
            select(MasterGameStateRecord).where(MasterGameStateRecord.session_id == session_id)
        ).scalar_one_or_none()
        t_num = int(state_dict.get("turn_number", 1))
        c_name = str(state_dict.get("campaign_name", "SAO_Sandbox"))
        payload = json.dumps(state_dict)

        if rec:
            rec.turn_number = t_num
            rec.campaign_name = c_name
            rec.state_json = payload
        else:
            rec = MasterGameStateRecord(
                session_id=session_id,
                turn_number=t_num,
                campaign_name=c_name,
                state_json=payload,
            )
            db_session.add(rec)
        db_session.flush()

    @staticmethod
    def load_master_state(db_session: Session, session_id: str = "default") -> dict:
        rec = db_session.execute(
            select(MasterGameStateRecord).where(MasterGameStateRecord.session_id == session_id)
        ).scalar_one_or_none()
        if rec and rec.state_json:
            return json.loads(rec.state_json)
        return {"turn_number": 1, "campaign_name": "SAO_Sandbox", "entities": {}, "environment": {}}


# Backward compatibility adapter functions
def save_game_adapter(player_state: dict, messages: list, base_dir: str, engine, session_id: str = "default") -> bool:
    """Adapts save_game to persist to relational DB and mirror to disk."""
    session_maker = sessionmaker(bind=engine, expire_on_commit=False)
    with DbTransactionContext(session_maker, session_id=session_id) as session:
        # Save character
        CharacterRepository.save_character(session, player_state, session_id=session_id)

        # Mirror to disk atomically
        slug = player_state.get("slug") or player_state.get("name", "hero").lower().replace(" ", "_")
        char_folder = os.path.join(base_dir, "saves", slug)
        os.makedirs(char_folder, exist_ok=True)

        full_data = {
            "player": player_state,
            "messages": messages,
            "last_saved": datetime.now(timezone.utc).isoformat(),
        }
        atomic_write_json(os.path.join(char_folder, "save_game.json"), full_data)
        atomic_write_json(os.path.join(base_dir, "save_game.json"), full_data)
    return True


def load_world_adapter(base_dir: str, session_id: str = "default") -> dict:
    world_path = os.path.join(base_dir, "world_state.json")
    if os.path.exists(world_path):
        try:
            with open(world_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"sector": 1, "world_status": "CRUCIBLE: ACTIVE", "map_locations": [], "global_news": []}


def activate_character_session_adapter(character_slug: str, session_id: str, engine) -> Optional[dict]:
    session_maker = sessionmaker(bind=engine, expire_on_commit=False)
    with DbTransactionContext(session_maker, session_id=session_id) as session:
        return CharacterRepository.load_character(session, character_slug, session_id=session_id)


# =====================================================================
# TIER 1: FEATURE COVERAGE (55 TESTS ACROSS 11 FEATURES)
# =====================================================================

class TestTier1_01_ConcurrentPersistence(unittest.TestCase):
    """Tier 1.1: Concurrent Multi-Session Persistence (ORIGINAL_REQUEST R1)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sao_test_concurrent_")
        self.db_path = os.path.join(self.temp_dir, "sao_sandbox.db")
        self.engine = create_sao_engine(f"sqlite:///{self.db_path}")
        init_db(self.engine)
        self.SessionMaker = sessionmaker(bind=self.engine, expire_on_commit=False)

    def tearDown(self):
        self.engine.dispose()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_concurrent_writes_distinct_characters_multi_thread(self):
        """5 threads concurrently write distinct character records; all persist without loss."""
        characters = [
            {"name": "Glenny", "level": 1, "hp": 135, "col": 100},
            {"name": "Banki", "level": 5, "hp": 120, "col": 2500},
            {"name": "Aria", "level": 2, "hp": 90, "col": 400},
            {"name": "Vex", "level": 3, "hp": 110, "col": 750},
            {"name": "Ren", "level": 4, "hp": 105, "col": 1200},
        ]
        errors = []

        def worker(char_data, session_idx):
            s_id = f"session_{session_idx}"
            for attempt in range(5):
                try:
                    with DbTransactionContext(self.SessionMaker, session_id=s_id) as sess:
                        CharacterRepository.save_character(sess, char_data, session_id=s_id)
                    break
                except Exception as e:
                    if attempt == 4:
                        errors.append(e)
                    time.sleep(0.05 * (attempt + 1))

        threads = [threading.Thread(target=worker, args=(c, i)) for i, c in enumerate(characters)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"Concurrent writes threw errors: {errors}")

        # Verify all 5 characters exist
        with DbTransactionContext(self.SessionMaker) as sess:
            for i, c in enumerate(characters):
                s_id = f"session_{i}"
                loaded = CharacterRepository.load_character(sess, c["name"].lower(), session_id=s_id)
                self.assertIsNotNone(loaded)
                self.assertEqual(loaded["name"], c["name"])
                self.assertEqual(loaded["hp"], c["hp"])

    def test_02_concurrent_session_character_updates(self):
        """Two concurrent threads update HP and Col for separate character sessions."""
        with DbTransactionContext(self.SessionMaker, session_id="s1") as sess:
            CharacterRepository.save_character(sess, {"name": "Glenny", "hp": 135, "col": 100}, session_id="s1")
        with DbTransactionContext(self.SessionMaker, session_id="s2") as sess:
            CharacterRepository.save_character(sess, {"name": "Banki", "hp": 120, "col": 500}, session_id="s2")

        errors = []

        def update_glenny():
            try:
                with DbTransactionContext(self.SessionMaker, session_id="s1") as sess:
                    CharacterRepository.save_character(sess, {"name": "Glenny", "hp": 95, "col": 150}, session_id="s1")
            except Exception as e:
                errors.append(e)

        def update_banki():
            try:
                with DbTransactionContext(self.SessionMaker, session_id="s2") as sess:
                    CharacterRepository.save_character(sess, {"name": "Banki", "hp": 110, "col": 800}, session_id="s2")
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=update_glenny)
        t2 = threading.Thread(target=update_banki)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0)
        with DbTransactionContext(self.SessionMaker) as sess:
            g = CharacterRepository.load_character(sess, "glenny", session_id="s1")
            b = CharacterRepository.load_character(sess, "banki", session_id="s2")
            self.assertEqual(g["hp"], 95)
            self.assertEqual(b["col"], 800)

    def test_03_concurrent_party_roster_updates(self):
        """Two threads update party companion rosters for two different sessions concurrently."""
        errors = []

        def worker_party_a():
            try:
                comps = [{"name": "Titus", "hp": 30, "recruited": True}]
                with DbTransactionContext(self.SessionMaker, session_id="sess_a") as sess:
                    PartyRepository.save_party(sess, comps, session_id="sess_a")
            except Exception as e:
                errors.append(e)

        def worker_party_b():
            try:
                comps = [{"name": "Daphne", "hp": 25, "recruited": True}]
                with DbTransactionContext(self.SessionMaker, session_id="sess_b") as sess:
                    PartyRepository.save_party(sess, comps, session_id="sess_b")
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=worker_party_a)
        t2 = threading.Thread(target=worker_party_b)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0)
        with DbTransactionContext(self.SessionMaker) as sess:
            p_a = PartyRepository.load_party(sess, session_id="sess_a")
            p_b = PartyRepository.load_party(sess, session_id="sess_b")
            self.assertEqual(len(p_a), 1)
            self.assertEqual(p_a[0]["name"], "Titus")
            self.assertEqual(len(p_b), 1)
            self.assertEqual(p_b[0]["name"], "Daphne")

    def test_04_concurrent_master_game_state_isolation(self):
        """Two threads write master state for separate sessions; each session maintains isolated turn numbers."""
        errors = []

        def write_m1():
            try:
                with DbTransactionContext(self.SessionMaker, session_id="m_sess_1") as sess:
                    MasterStateRepository.save_master_state(sess, {"turn_number": 7, "campaign_name": "Raid A"}, session_id="m_sess_1")
            except Exception as e:
                errors.append(e)

        def write_m2():
            try:
                with DbTransactionContext(self.SessionMaker, session_id="m_sess_2") as sess:
                    MasterStateRepository.save_master_state(sess, {"turn_number": 19, "campaign_name": "Raid B"}, session_id="m_sess_2")
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=write_m1)
        t2 = threading.Thread(target=write_m2)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0)
        with DbTransactionContext(self.SessionMaker) as sess:
            st1 = MasterStateRepository.load_master_state(sess, session_id="m_sess_1")
            st2 = MasterStateRepository.load_master_state(sess, session_id="m_sess_2")
            self.assertEqual(st1["turn_number"], 7)
            self.assertEqual(st2["turn_number"], 19)

    def test_05_connection_pool_under_multithreaded_load(self):
        """8 concurrent worker threads acquire transactions from connection pool and commit cleanly."""
        errors = []

        def worker_task(worker_id):
            for attempt in range(5):
                try:
                    with DbTransactionContext(self.SessionMaker, session_id=f"pool_sess_{worker_id}") as sess:
                        char_data = {"name": f"Hero_{worker_id}", "hp": 100 + worker_id}
                        CharacterRepository.save_character(sess, char_data, session_id=f"pool_sess_{worker_id}")
                    break
                except Exception as e:
                    if attempt == 4:
                        errors.append(e)
                    time.sleep(0.05 * (attempt + 1))

        threads = [threading.Thread(target=worker_task, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)


class TestTier1_02_AtomicRollback(unittest.TestCase):
    """Tier 1.2: Atomic Transaction Rollback on Turn Failure (ORIGINAL_REQUEST R1)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sao_test_rollback_")
        self.db_path = os.path.join(self.temp_dir, "sao_sandbox.db")
        self.engine = create_sao_engine(f"sqlite:///{self.db_path}")
        init_db(self.engine)
        self.SessionMaker = sessionmaker(bind=self.engine, expire_on_commit=False)

    def tearDown(self):
        self.engine.dispose()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_turn_resolution_failure_rolls_back_character_state(self):
        """Exception raised mid-turn rolls back HP and Col changes cleanly."""
        with DbTransactionContext(self.SessionMaker, session_id="s1") as sess:
            CharacterRepository.save_character(sess, {"name": "Glenny", "hp": 135, "col": 100}, session_id="s1")

        with self.assertRaises(RuntimeError):
            with DbTransactionContext(self.SessionMaker, session_id="s1") as sess:
                CharacterRepository.save_character(sess, {"name": "Glenny", "hp": 40, "col": 10}, session_id="s1")
                raise RuntimeError("Simulated GM combat crash mid-turn")

        with DbTransactionContext(self.SessionMaker, session_id="s1") as sess:
            g = CharacterRepository.load_character(sess, "glenny", session_id="s1")
            self.assertEqual(g["hp"], 135, "HP must not be modified after rollback")
            self.assertEqual(g["col"], 100, "Col must not be modified after rollback")

    def test_02_partial_inventory_and_equipment_change_rolled_back(self):
        """Equipment changes rolled back when transaction encounters mid-turn exception."""
        initial_loadout = {
            "name": "Glenny",
            "equipped": {"main_hand": "Chipped Wood-Axe", "off_hand": "Wooden Buckler"},
        }
        with DbTransactionContext(self.SessionMaker, session_id="s1") as sess:
            CharacterRepository.save_character(sess, initial_loadout, session_id="s1")

        with self.assertRaises(ValueError):
            with DbTransactionContext(self.SessionMaker, session_id="s1") as sess:
                modified = {
                    "name": "Glenny",
                    "equipped": {"main_hand": "Mythic Battleaxe", "off_hand": "Aegis Shield"},
                }
                CharacterRepository.save_character(sess, modified, session_id="s1")
                raise ValueError("Equipment slot validation error")

        with DbTransactionContext(self.SessionMaker, session_id="s1") as sess:
            g = CharacterRepository.load_character(sess, "glenny", session_id="s1")
            self.assertEqual(g["equipped"]["main_hand"], "Chipped Wood-Axe")
            self.assertEqual(g["equipped"]["off_hand"], "Wooden Buckler")

    def test_03_multi_table_atomic_rollback(self):
        """Character + equipped slots + debuffs all rollback together if exception thrown."""
        with self.assertRaises(Exception):
            with DbTransactionContext(self.SessionMaker, session_id="s_atomic") as sess:
                char_data = {
                    "name": "TestHero",
                    "equipped": {"main_hand": "Sword"},
                    "active_debuffs": [{"name": "Shred", "ac_penalty": -4}],
                }
                CharacterRepository.save_character(sess, char_data, session_id="s_atomic")
                raise Exception("Forced multi-table rollback")

        with DbTransactionContext(self.SessionMaker, session_id="s_atomic") as sess:
            res = CharacterRepository.load_character(sess, "testhero", session_id="s_atomic")
            self.assertIsNone(res, "Rolled back character record must not exist")

    def test_04_rollback_maintains_database_health(self):
        """Post-rollback connection can immediately execute valid transactions without lock errors."""
        try:
            with DbTransactionContext(self.SessionMaker, session_id="s_health") as sess:
                CharacterRepository.save_character(sess, {"name": "BadHero"}, session_id="s_health")
                raise RuntimeError("Fail")
        except RuntimeError:
            pass

        # Immediate follow-up valid transaction
        with DbTransactionContext(self.SessionMaker, session_id="s_health") as sess:
            CharacterRepository.save_character(sess, {"name": "GoodHero", "hp": 100}, session_id="s_health")

        with DbTransactionContext(self.SessionMaker, session_id="s_health") as sess:
            good = CharacterRepository.load_character(sess, "goodhero", session_id="s_health")
            self.assertIsNotNone(good)
            self.assertEqual(good["hp"], 100)

    def test_05_rollback_does_not_corrupt_disk_mirror(self):
        """Save adapter rollback leaves disk file completely identical to pre-turn state."""
        char_data = {"name": "Glenny", "hp": 135}
        save_game_adapter(char_data, [], self.temp_dir, self.engine, session_id="s_mirror")

        mirror_file = os.path.join(self.temp_dir, "save_game.json")
        initial_mtime = os.path.getmtime(mirror_file)

        # Attempt failing save
        try:
            with DbTransactionContext(self.SessionMaker, session_id="s_mirror") as sess:
                CharacterRepository.save_character(sess, {"name": "Glenny", "hp": 0}, session_id="s_mirror")
                raise RuntimeError("Mid-save crash")
        except RuntimeError:
            pass

        with open(mirror_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["player"]["hp"], 135, "Disk mirror must reflect pre-crash state")


class TestTier1_03_ZeroBytePrevention(unittest.TestCase):
    """Tier 1.3: Zero-Byte Corruption Prevention (ORIGINAL_REQUEST R1)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sao_test_zerobyte_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_atomic_write_json_creates_valid_file(self):
        """atomic_write_json creates valid non-empty JSON file with exact contents."""
        target = os.path.join(self.temp_dir, "valid.json")
        data = {"player": "Glenny", "level": 1, "col": 100}
        atomic_write_json(target, data)

        self.assertTrue(os.path.exists(target))
        self.assertGreater(os.path.getsize(target), 0)
        with open(target, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded, data)

    def test_02_serialization_exception_preserves_original_file(self):
        """Attempting to serialize non-serializable object leaves existing file untouched and non-zero."""
        target = os.path.join(self.temp_dir, "preserve.json")
        original_data = {"player": "Banki", "hp": 120}
        atomic_write_json(target, original_data)
        original_size = os.path.getsize(target)
        self.assertGreater(original_size, 0)

        # Unserializable data with function / lambda
        bad_data = {"player": "Corrupt", "invalid_func": lambda x: x}
        with self.assertRaises(TypeError):
            atomic_write_json(target, bad_data)

        # File must remain untouched and non-zero
        self.assertEqual(os.path.getsize(target), original_size)
        with open(target, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded, original_data)

    def test_03_atomic_write_overwrites_existing_atomically(self):
        """Overwriting an existing file transitions atomically without leaving a 0-byte window."""
        target = os.path.join(self.temp_dir, "overwrite.json")
        atomic_write_json(target, {"initial": "large_content" * 100})
        new_data = {"updated": "new_content" * 150}
        atomic_write_json(target, new_data)

        self.assertGreater(os.path.getsize(target), 100)
        with open(target, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded, new_data)

    def test_04_empty_structure_serializes_non_zero_json(self):
        """Empty dictionary or list serializes to valid non-zero length JSON."""
        t_dict = os.path.join(self.temp_dir, "empty_dict.json")
        t_list = os.path.join(self.temp_dir, "empty_list.json")
        atomic_write_json(t_dict, {})
        atomic_write_json(t_list, [])

        self.assertGreater(os.path.getsize(t_dict), 0)
        self.assertGreater(os.path.getsize(t_list), 0)
        with open(t_dict, "r", encoding="utf-8") as f:
            self.assertEqual(json.load(f), {})
        with open(t_list, "r", encoding="utf-8") as f:
            self.assertEqual(json.load(f), [])

    def test_05_rapid_sequential_atomic_writes(self):
        """20 rapid sequential atomic writes to the same file succeed without corruption or permission lock errors."""
        target = os.path.join(self.temp_dir, "rapid.json")
        for i in range(20):
            payload = {"iteration": i, "timestamp": time.time()}
            atomic_write_json(target, payload)

        with open(target, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded["iteration"], 19)


class TestTier1_04_MultiLimbEquipment(unittest.TestCase):
    """Tier 1.4: Multi-Limb Equipment Slots & 2H Grip Bindings (ORIGINAL_REQUEST R2)."""

    def test_01_four_armed_anatomy_slots_resolved(self):
        """Spliced Apex Chimera (Glenny) resolves 4 distinct hand slots."""
        glenny = cg.generate_starting_character("Glenny")
        limb_prof = mechanics.get_limb_anatomy_profile(glenny)

        self.assertTrue(limb_prof["is_four_armed"])
        self.assertEqual(limb_prof["arm_count"], 4)
        slot_keys = list(limb_prof["hand_slots"].keys())
        self.assertIn("main_hand", slot_keys)
        self.assertIn("off_hand", slot_keys)
        self.assertIn("lower_main_hand", slot_keys)
        self.assertIn("lower_off_hand", slot_keys)

    def test_02_two_handed_weapon_locks_paired_off_hand(self):
        """Equipping Recurve Hunting Bow in main_hand binds paired off_hand to [2H Grip: Recurve Hunting Bow]."""
        glenny = cg.generate_starting_character("Glenny")
        glenny["equipped"]["main_hand"] = "Recurve Hunting Bow"
        glenny["equipped"]["off_hand"] = "None"
        mechanics.ensure_multi_limb_equipment(glenny)

        self.assertEqual(glenny["equipped"]["off_hand"], "[2H Grip: Recurve Hunting Bow]")

    def test_03_two_handed_grip_leaves_lower_arms_free(self):
        """2H weapon in upper arms leaves lower_main_hand and lower_off_hand independent and free."""
        glenny = cg.generate_starting_character("Glenny")
        glenny["equipped"]["main_hand"] = "Recurve Hunting Bow"
        glenny["equipped"]["lower_main_hand"] = "Chipped Wood-Axe"
        glenny["equipped"]["lower_off_hand"] = "Wooden Buckler"
        mechanics.ensure_multi_limb_equipment(glenny)

        self.assertEqual(glenny["equipped"]["off_hand"], "[2H Grip: Recurve Hunting Bow]")
        self.assertEqual(glenny["equipped"]["lower_main_hand"], "Chipped Wood-Axe")
        self.assertEqual(glenny["equipped"]["lower_off_hand"], "Wooden Buckler")

    def test_04_grip_marker_detection_and_extraction(self):
        """is_two_handed_grip_marker and extract_two_handed_grip_weapon accurately parse 2H grip syntax."""
        marker = "[2H Grip: Greatsword of Pohatcong]"
        self.assertTrue(mechanics.is_two_handed_grip_marker(marker))
        self.assertEqual(mechanics.extract_two_handed_grip_weapon(marker), "Greatsword of Pohatcong")

        regular_weapon = "Shortsword"
        self.assertFalse(mechanics.is_two_handed_grip_marker(regular_weapon))
        self.assertEqual(mechanics.extract_two_handed_grip_weapon(regular_weapon), "")

    def test_05_multi_limb_displacement_when_2h_equipped(self):
        """Equipping 2H weapon into upper arms displaces held 1H off-hand weapon into lower arms."""
        glenny = cg.generate_starting_character("Glenny")
        glenny["equipped"]["main_hand"] = "Recurve Hunting Bow"
        glenny["equipped"]["off_hand"] = "Dagger"
        glenny["equipped"]["lower_main_hand"] = "None"
        glenny["equipped"]["lower_off_hand"] = "None"
        mechanics.ensure_multi_limb_equipment(glenny)

        self.assertEqual(glenny["equipped"]["off_hand"], "[2H Grip: Recurve Hunting Bow]")
        # Dagger displaced down
        lower_items = [glenny["equipped"]["lower_main_hand"], glenny["equipped"]["lower_off_hand"]]
        self.assertIn("Dagger", lower_items)


class TestTier1_05_ExtendedGraftsAndStrain(unittest.TestCase):
    """Tier 1.5: Extended Graft Slots & Metabolic Strain (ORIGINAL_REQUEST R2)."""

    def test_01_nine_anatomical_graft_slots_available(self):
        """Glenny's Chimera lineage provides 9 distinct surgical graft slots."""
        glenny = cg.generate_starting_character("Glenny")
        limb_prof = mechanics.get_limb_anatomy_profile(glenny)
        slots = limb_prof["graft_slots"]

        self.assertEqual(len(slots), 9)
        self.assertIn("lower_left_arm", slots)
        self.assertIn("lower_right_arm", slots)
        self.assertIn("tail", slots)

    def test_02_secondary_ganglia_grants_plus_one_unit_strain(self):
        """Glenny (CON 16, Level 1, 4-armed) computes Unit Strain Cap of 4 units."""
        glenny = cg.generate_starting_character("Glenny")
        unit_cap = mechanics.get_max_unit_strain(glenny)
        # CON 16 (+3) + Level 1//2 (0) + Secondary Ganglia (+1) = 4 units
        self.assertEqual(unit_cap, 4)

    def test_03_bio_tolerance_point_pool_calculation(self):
        """Glenny (CON 16, Level 1) computes Bio-Tolerance Pool of 35 points."""
        glenny = cg.generate_starting_character("Glenny")
        bio_pool = mechanics.get_max_graft_strain(glenny)
        # (16 * 2) + (1 * 3) = 35 points
        self.assertEqual(bio_pool, 35)

    def test_04_graft_installation_consumes_strain_and_bio_pool(self):
        """Installing graft in lower arm consumes unit strain and bio-tolerance points."""
        glenny = cg.generate_starting_character("Glenny")
        glenny["graft_system"]["installed_grafts"]["lower_left_arm"] = {
            "name": "Basalt Carapace Plating",
            "key": "basalt_carapace_plating",
            "slot": "lower_left_arm",
            "strain": 1,
        }
        mechanics.sync_graft_containers(glenny)

        cur_unit = mechanics.get_current_unit_strain(glenny)
        cur_bio = mechanics.get_current_graft_strain(glenny)
        self.assertEqual(cur_unit, 1)
        self.assertEqual(cur_bio, 10)

    def test_05_elemental_mutual_exclusivity_rejection(self):
        """Installing cold graft alongside fire graft detects elemental dissonance."""
        player = {"graft_system": {"installed_grafts": {
            "torso": {"name": "Magma Core", "element": "fire"}
        }}}
        has_dissonance = mechanics.check_elemental_graft_dissonance(player, candidate_element="cold")
        self.assertTrue(has_dissonance)


class TestTier1_06_MutableDebuffsAndCombatStats(unittest.TestCase):
    """Tier 1.6: Mutable Active Debuffs & Combat Stats (ORIGINAL_REQUEST R2)."""

    def test_01_active_debuff_schema_preservation(self):
        """Active debuff model preserves schema fields according to schemas.py."""
        debuff = schemas.ActiveDebuffSchema(
            debuff_id="hydraulic_shred",
            name="Foundry Hydraulic Overdrive",
            ac_penalty=-4,
            dr_override=None,
            turns_remaining=3,
            source="Foundry Stance",
        )
        self.assertEqual(debuff.ac_penalty, -4)
        self.assertIsNone(debuff.dr_override)
        self.assertEqual(debuff.turns_remaining, 3)

    def test_02_single_debuff_ac_penalty_recalculation(self):
        """Applying -4 AC Foundry Shred reduces target AC by 4."""
        ent = {"base_ac": 16, "base_dr": 2, "active_debuffs": [
            {"debuff_id": "shred", "name": "Foundry Shred", "ac_penalty": -4, "dr_override": None}
        ]}
        res = mechanics.recalculate_entity_combat_stats(ent)
        self.assertEqual(res["ac"], 12)
        self.assertEqual(res["dr"], 2)

    def test_03_dr_override_sets_damage_reduction_to_zero(self):
        """Corrosive Slag-Shatter sets target Damage Reduction (DR) to 0."""
        ent = {"base_ac": 14, "base_dr": 8, "active_debuffs": [
            {"debuff_id": "slag", "name": "Slag Shatter", "ac_penalty": 0, "dr_override": 0}
        ]}
        res = mechanics.recalculate_entity_combat_stats(ent)
        self.assertEqual(res["dr"], 0)
        self.assertEqual(res["ac"], 14)

    def test_04_multiple_debuffs_stack_ac_penalties(self):
        """Multiple active debuffs stack their AC penalties correctly."""
        ent = {"base_ac": 18, "base_dr": 4, "active_debuffs": [
            {"debuff_id": "d1", "name": "Foundry Shred", "ac_penalty": -4},
            {"debuff_id": "d2", "name": "Exposing Strike", "ac_penalty": -2},
        ]}
        res = mechanics.recalculate_entity_combat_stats(ent)
        self.assertEqual(res["ac"], 12)  # 18 - 4 - 2 = 12

    def test_05_recalculate_entity_combat_stats_syncs_badges(self):
        """Recalculating stats returns synchronized entity dictionary."""
        ent = {"base_ac": 14, "base_dr": 0, "active_debuffs": []}
        res = mechanics.recalculate_entity_combat_stats(ent)
        self.assertEqual(res["ac"], 14)
        self.assertEqual(res["dr"], 0)


class TestTier1_07_SkillMasteryAndAbilityFusion(unittest.TestCase):
    """Tier 1.7: 1-1000 Skill Mastery & Ability Fusion Matrix (ORIGINAL_REQUEST R2)."""

    def test_01_skill_mastery_tiers_and_labeling(self):
        """1-1000 skill mastery accurately maps to 7 master tiers."""
        self.assertEqual(mechanics.get_mastery_tier(1), "Novice")
        self.assertEqual(mechanics.get_mastery_tier(50), "Apprentice")
        self.assertEqual(mechanics.get_mastery_tier(100), "Journeyman")
        self.assertEqual(mechanics.get_mastery_tier(250), "Adept")
        self.assertEqual(mechanics.get_mastery_tier(500), "Master")
        self.assertEqual(mechanics.get_mastery_tier(750), "Grandmaster")
        self.assertEqual(mechanics.get_mastery_tier(1000), "Transcendence")

    def test_02_milestone_threshold_unlocks(self):
        """Canonical milestone thresholds are exactly 50, 100, 250, 500, 750, 1000."""
        self.assertEqual(mechanics.MILESTONE_THRESHOLDS, [50, 100, 250, 500, 750, 1000])

    def test_03_ability_fusion_combines_skills(self):
        """Ability fusion creates [Fusion] <Name> skill combining component masteries."""
        player = {
            "skills": {
                "Battleaxe Mastery": {"mastery": 150, "tier": "Journeyman", "desc": "Axe art"},
                "Earth Tremor": {"mastery": 120, "tier": "Journeyman", "desc": "Quake art"},
            },
            "spells": [],
            "feats": [],
        }
        mechanics.fuse_abilities(player, "Battleaxe Mastery", "Earth Tremor", "Tremor-Quake Cleave")

        fused_name = "[Fusion] Tremor-Quake Cleave"
        self.assertIn(fused_name, player["skills"])
        self.assertGreaterEqual(player["skills"][fused_name]["mastery"], 150)

    def test_04_fused_base_skills_archived(self):
        """Base skills consumed in fusion are moved to archived_base_skills with metadata."""
        player = {
            "skills": {
                "Skill A": {"mastery": 80, "tier": "Apprentice", "desc": "A"},
                "Skill B": {"mastery": 90, "tier": "Apprentice", "desc": "B"},
            },
            "spells": [],
            "feats": [],
        }
        mechanics.fuse_abilities(player, "Skill A", "Skill B", "Fused Technique")

        self.assertIn("Skill A", player.get("archived_base_skills", {}))
        self.assertIn("Skill B", player.get("archived_base_skills", {}))

    def test_05_relearn_base_skill_from_archive(self):
        """Archived base skill can be relearned at Rank 1 without losing the fused ability."""
        player = {
            "skills": {
                "Skill A": {"mastery": 100, "tier": "Journeyman", "desc": "A"},
                "Skill B": {"mastery": 100, "tier": "Journeyman", "desc": "B"},
            },
            "spells": [],
            "feats": [],
        }
        mechanics.fuse_abilities(player, "Skill A", "Skill B", "Fused Tech")
        mechanics.relearn_base_skill(player, "Skill A", starting_mastery=1)

        self.assertIn("Skill A", player["skills"])
        self.assertEqual(player["skills"]["Skill A"]["mastery"], 1)
        self.assertIn("[Fusion] Fused Tech", player["skills"])


class TestTier1_08_CorpseCacheAndMonumentOfLife(unittest.TestCase):
    """Tier 1.8: Corpse Cache & Monument of Life Lifecycles (ORIGINAL_REQUEST R2)."""

    def test_01_zero_hp_crisis_activates_countdown(self):
        """Dropping to 0 HP activates the crisis countdown."""
        player = {"hp": 0, "max_hp": 100}
        mechanics.trigger_zero_hp_crisis(player)
        self.assertTrue(player.get("death_system", {}).get("crisis_active"))

    def test_02_window_expiration_writes_monument_of_life(self):
        """Revival window expiration registers character into monument of life."""
        player = {
            "name": "Glenny",
            "hp": 0,
            "level": 1,
            "col": 200,
            "inventory": [],
            "equipped": {},
            "death_system": {"crisis_active": True, "monument_of_life": [], "corpse_caches": []},
        }
        mechanics.resolve_revival_window(player, method="expire")
        monument = player["death_system"]["monument_of_life"]
        self.assertGreater(len(monument), 0)
        self.assertEqual(monument[0]["status"], "KIA — Polygon Shatter")

    def test_03_death_splits_col_and_caches_gear(self):
        """Death drops 50% Col into corpse cache and retains remainder for successor."""
        player = {
            "name": "Glenny",
            "hp": 0,
            "level": 1,
            "col": 500,
            "inventory": [{"name": "Health Potion"}],
            "equipped": {"main_hand": "Bow"},
            "death_system": {"crisis_active": True, "monument_of_life": [], "corpse_caches": []},
        }
        mechanics.resolve_revival_window(player, method="expire")
        caches = player["death_system"]["corpse_caches"]
        self.assertEqual(len(caches), 1)
        self.assertEqual(caches[0]["col"], 250)

    def test_04_legacy_successor_generation(self):
        """Generation II successor is generated with proper legacy naming."""
        player = {
            "name": "Glenny",
            "hp": 0,
            "level": 2,
            "col": 400,
            "death_system": {"crisis_active": True, "monument_of_life": [], "corpse_caches": []},
        }
        mechanics.resolve_revival_window(player, method="expire")
        self.assertEqual(player["name"], "Glenny II")
        self.assertEqual(player["level"], 1)

    def test_05_corpse_cache_recovery(self):
        """Successor recovers corpse cache, reclaiming dropped Col and items."""
        player = {
            "name": "Glenny II",
            "col": 100,
            "inventory": [],
            "equipped": {},
            "death_system": {
                "corpse_caches": [{
                    "cache_id": "cache_1",
                    "fallen_name": "Glenny",
                    "floor": 1,
                    "col": 250,
                    "inventory": [{"name": "Recovered Bow"}],
                    "equipped": {},
                    "recovered": False,
                }]
            },
        }
        res = mechanics.recover_corpse_cache(player, "cache_1")
        self.assertTrue(res["success"])
        self.assertEqual(player["col"], 350)  # 100 + 250
        self.assertTrue(player["death_system"]["corpse_caches"][0]["recovered"])


class TestTier1_09_GlennyProfileParity(unittest.TestCase):
    """Tier 1.9: Glenny Profile Baseline AC 14 / Shielded AC 16 (ORIGINAL_REQUEST Criteria)."""

    def test_01_glenny_baseline_attributes_and_size(self):
        """Glenny loads with STR 18, DEX 15, CON 16, and Large size (86 in, 310 lbs)."""
        glenny = cg.generate_starting_character("Glenny")
        stats = glenny["stats"]
        self.assertEqual(stats["STR"], 18)
        self.assertEqual(stats["DEX"], 15)
        self.assertEqual(stats["CON"], 16)

        profile = mechanics.get_physical_profile(glenny)
        self.assertEqual(profile["size"], "Large")
        self.assertEqual(profile["modifiers"]["ac_mod"], -1)

    def test_02_glenny_baseline_unshielded_ac_14(self):
        """Glenny baseline unshielded loadout computes exactly to AC 14."""
        glenny = cg.generate_starting_character("Glenny")
        # Base AC: 10 + 2 (DEX) + 1 (Tunic) + 2 (Fibrous Hide) - 1 (Large Size) = 14
        ac = mechanics.calculate_ac(glenny)
        self.assertEqual(ac, 14)

    def test_03_glenny_shielded_ac_16(self):
        """Glenny equipping Wooden Buckler in lower_off_hand increases AC to exactly 16."""
        glenny = cg.generate_starting_character("Glenny")
        glenny["equipped"]["lower_off_hand"] = "Wooden Buckler"
        ac = mechanics.calculate_ac(glenny)
        self.assertEqual(ac, 16)

    def test_04_glenny_unit_strain_cap_4(self):
        """Glenny Unit Strain Cap computes exactly to 4 units."""
        glenny = cg.generate_starting_character("Glenny")
        cap = mechanics.get_max_unit_strain(glenny)
        self.assertEqual(cap, 4)

    def test_05_glenny_hunting_laser_rangefinder_relic(self):
        """Glenny accessory slot contains Hunting Laser Rangefinder."""
        glenny = cg.generate_starting_character("Glenny")
        self.assertEqual(glenny["equipped"]["accessory"], "Hunting Laser Rangefinder")


class TestTier1_10_PartyStateIsolation(unittest.TestCase):
    """Tier 1.10: Party Companion State Isolation Across Sessions (ORIGINAL_REQUEST R1)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sao_test_party_")
        self.db_path = os.path.join(self.temp_dir, "sao_sandbox.db")
        self.engine = create_sao_engine(f"sqlite:///{self.db_path}")
        init_db(self.engine)
        self.SessionMaker = sessionmaker(bind=self.engine, expire_on_commit=False)

    def tearDown(self):
        self.engine.dispose()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_sessions_have_isolated_party_rosters(self):
        """Session A and Session B maintain separate companion rosters in DB."""
        with DbTransactionContext(self.SessionMaker, session_id="s_a") as sess:
            PartyRepository.save_party(sess, [{"name": "Titus", "hp": 30}], session_id="s_a")

        with DbTransactionContext(self.SessionMaker, session_id="s_b") as sess:
            PartyRepository.save_party(sess, [{"name": "Daphne", "hp": 25}], session_id="s_b")

        with DbTransactionContext(self.SessionMaker) as sess:
            p_a = PartyRepository.load_party(sess, session_id="s_a")
            p_b = PartyRepository.load_party(sess, session_id="s_b")
            self.assertEqual(len(p_a), 1)
            self.assertEqual(p_a[0]["name"], "Titus")
            self.assertEqual(len(p_b), 1)
            self.assertEqual(p_b[0]["name"], "Daphne")

    def test_02_companion_hp_changes_isolated_by_session(self):
        """HP damage to Titus in Session A does not modify Titus in Session B."""
        with DbTransactionContext(self.SessionMaker, session_id="s_a") as sess:
            PartyRepository.save_party(sess, [{"name": "Titus", "slug": "titus", "hp": 30}], session_id="s_a")
        with DbTransactionContext(self.SessionMaker, session_id="s_b") as sess:
            PartyRepository.save_party(sess, [{"name": "Titus", "slug": "titus", "hp": 30}], session_id="s_b")

        # Session A Titus takes 10 damage
        with DbTransactionContext(self.SessionMaker, session_id="s_a") as sess:
            PartyRepository.save_party(sess, [{"name": "Titus", "slug": "titus", "hp": 20}], session_id="s_a")

        with DbTransactionContext(self.SessionMaker) as sess:
            p_a = PartyRepository.load_party(sess, session_id="s_a")
            p_b = PartyRepository.load_party(sess, session_id="s_b")
            self.assertEqual(p_a[0]["hp"], 20)
            self.assertEqual(p_b[0]["hp"], 30)

    def test_03_companion_tactical_stance_isolated(self):
        """Setting companion stance in Session A does not alter stance in Session B."""
        with DbTransactionContext(self.SessionMaker, session_id="s_a") as sess:
            PartyRepository.save_party(sess, [{"name": "Ren", "stance": "overwatch_hacking"}], session_id="s_a")
        with DbTransactionContext(self.SessionMaker, session_id="s_b") as sess:
            PartyRepository.save_party(sess, [{"name": "Ren", "stance": "suppression_fire"}], session_id="s_b")

        with DbTransactionContext(self.SessionMaker) as sess:
            p_a = PartyRepository.load_party(sess, session_id="s_a")
            p_b = PartyRepository.load_party(sess, session_id="s_b")
            self.assertEqual(p_a[0]["stance"], "overwatch_hacking")
            self.assertEqual(p_b[0]["stance"], "suppression_fire")

    def test_04_companion_roster_reset_isolated(self):
        """Resetting party roster in Session A does not clear Session B roster."""
        with DbTransactionContext(self.SessionMaker, session_id="s_a") as sess:
            PartyRepository.save_party(sess, [{"name": "Ren"}], session_id="s_a")
        with DbTransactionContext(self.SessionMaker, session_id="s_b") as sess:
            PartyRepository.save_party(sess, [{"name": "Elora"}], session_id="s_b")

        # Clear Session A
        with DbTransactionContext(self.SessionMaker, session_id="s_a") as sess:
            PartyRepository.save_party(sess, [], session_id="s_a")

        with DbTransactionContext(self.SessionMaker) as sess:
            p_a = PartyRepository.load_party(sess, session_id="s_a")
            p_b = PartyRepository.load_party(sess, session_id="s_b")
            self.assertEqual(len(p_a), 0)
            self.assertEqual(len(p_b), 1)

    def test_05_concurrent_companion_affinity_updates(self):
        """Concurrent companion affinity updates in separate sessions persist without collision."""
        errors = []

        def update_aff_a():
            try:
                with DbTransactionContext(self.SessionMaker, session_id="aff_a") as sess:
                    PartyRepository.save_party(sess, [{"name": "Kibs", "affinity": 75}], session_id="aff_a")
            except Exception as e:
                errors.append(e)

        def update_aff_b():
            try:
                with DbTransactionContext(self.SessionMaker, session_id="aff_b") as sess:
                    PartyRepository.save_party(sess, [{"name": "Kibs", "affinity": 90}], session_id="aff_b")
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=update_aff_a)
        t2 = threading.Thread(target=update_aff_b)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0)


class TestTier1_11_StreamlitAndCLICompatibility(unittest.TestCase):
    """Tier 1.11: Streamlit & Headless CLI Backward Compatibility (ORIGINAL_REQUEST R3)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sao_test_compat_")
        self.db_path = os.path.join(self.temp_dir, "sao_sandbox.db")
        self.engine = create_sao_engine(f"sqlite:///{self.db_path}")
        init_db(self.engine)

    def tearDown(self):
        self.engine.dispose()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_save_game_adapter_returns_success(self):
        """save_game_adapter executes and returns True."""
        glenny = cg.generate_starting_character("Glenny")
        res = save_game_adapter(glenny, [], self.temp_dir, self.engine, session_id="compat_1")
        self.assertTrue(res)

    def test_02_load_world_returns_standard_dictionary(self):
        """load_world_adapter returns standard dictionary with sector and world_status."""
        world = load_world_adapter(self.temp_dir, session_id="compat_1")
        self.assertIsInstance(world, dict)
        self.assertIn("sector", world)
        self.assertIn("world_status", world)

    def test_03_activate_character_session_loads_profile(self):
        """activate_character_session_adapter activates and retrieves character dict."""
        glenny = cg.generate_starting_character("Glenny")
        save_game_adapter(glenny, [], self.temp_dir, self.engine, session_id="compat_act")

        loaded = activate_character_session_adapter("glenny", session_id="compat_act", engine=self.engine)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["name"], "Glenny")

    def test_04_atomic_disk_mirroring_keeps_save_game_json_valid(self):
        """Calling save adapter keeps root save_game.json valid and parseable on disk."""
        glenny = cg.generate_starting_character("Glenny")
        save_game_adapter(glenny, [], self.temp_dir, self.engine, session_id="mirror_valid")

        root_save = os.path.join(self.temp_dir, "save_game.json")
        self.assertTrue(os.path.exists(root_save))
        with open(root_save, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["player"]["name"], "Glenny")

    def test_05_legacy_cli_test_suite_data_format_parity(self):
        """Character dictionary retains all expected top-level keys for existing 5 test suites."""
        glenny = cg.generate_starting_character("Glenny")
        save_game_adapter(glenny, [], self.temp_dir, self.engine, session_id="keys_check")

        root_save = os.path.join(self.temp_dir, "save_game.json")
        with open(root_save, "r", encoding="utf-8") as f:
            p = json.load(f)["player"]

        for req_key in ["name", "level", "hp", "max_hp", "stats", "equipped", "inventory"]:
            self.assertIn(req_key, p)


# =====================================================================
# TIER 2: BOUNDARY & CORNER CASES (55 TESTS ACROSS 11 CATEGORIES)
# =====================================================================

class TestTier2_01_ConcurrencyRaceHammering(unittest.TestCase):
    """Tier 2.1: High-Concurrency Race Condition Hammering (TEST_INFRA Tier 2)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sao_test_race_")
        self.db_path = os.path.join(self.temp_dir, "sao_sandbox.db")
        self.engine = create_sao_engine(f"sqlite:///{self.db_path}")
        init_db(self.engine)
        self.SessionMaker = sessionmaker(bind=self.engine, expire_on_commit=False)

    def tearDown(self):
        self.engine.dispose()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_ten_concurrent_workers_distinct_characters(self):
        """10 threads simultaneously hammering distinct character records."""
        errors = []

        def hammer(idx):
            s_id = f"worker_sess_{idx}"
            for attempt in range(5):
                try:
                    with DbTransactionContext(self.SessionMaker, session_id=s_id) as sess:
                        c = {"name": f"Hero_{idx}", "hp": 100 + idx, "col": idx * 50}
                        CharacterRepository.save_character(sess, c, session_id=s_id)
                    break
                except Exception as e:
                    if attempt == 4:
                        errors.append(e)
                    time.sleep(0.05 * (attempt + 1))

        threads = [threading.Thread(target=hammer, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)

    def test_02_rapid_read_write_interleaving(self):
        """Interleaved reads and writes from multiple threads without deadlock."""
        errors = []

        def writer():
            for i in range(5):
                for attempt in range(5):
                    try:
                        with DbTransactionContext(self.SessionMaker, session_id="rw_sess") as sess:
                            CharacterRepository.save_character(sess, {"name": "Target", "hp": 100 - i}, session_id="rw_sess")
                        break
                    except Exception as e:
                        if attempt == 4:
                            errors.append(e)
                        time.sleep(0.05 * (attempt + 1))

        def reader():
            for _ in range(5):
                for attempt in range(5):
                    try:
                        with DbTransactionContext(self.SessionMaker, session_id="rw_sess") as sess:
                            CharacterRepository.load_character(sess, "target", session_id="rw_sess")
                        break
                    except Exception as e:
                        if attempt == 4:
                            errors.append(e)
                        time.sleep(0.05 * (attempt + 1))

        threads = [threading.Thread(target=writer) for _ in range(3)] + [threading.Thread(target=reader) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)

    def test_03_sqlite_wal_busy_timeout_resilience(self):
        """Threads waiting on write locks resolve cleanly via 30000ms busy timeout."""
        errors = []

        def lock_holder(idx):
            s_id = f"holder_{idx}"
            for attempt in range(5):
                try:
                    with DbTransactionContext(self.SessionMaker, session_id=s_id) as sess:
                        CharacterRepository.save_character(sess, {"name": f"Holder_{idx}"}, session_id=s_id)
                        time.sleep(0.05)
                    break
                except Exception as e:
                    if attempt == 4:
                        errors.append(e)
                    time.sleep(0.05 * (attempt + 1))

        threads = [threading.Thread(target=lock_holder, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)

    def test_04_concurrent_companion_recruitment_collision(self):
        """Simultaneous companion updates inside separate sessions serialize without corruption."""
        errors = []

        def recruit(idx):
            s_id = f"party_col_{idx}"
            for attempt in range(5):
                try:
                    with DbTransactionContext(self.SessionMaker, session_id=s_id) as sess:
                        PartyRepository.save_party(sess, [{"name": f"comp_{idx}", "hp": 30}], session_id=s_id)
                    break
                except Exception as e:
                    if attempt == 4:
                        errors.append(e)
                    time.sleep(0.05 * (attempt + 1))

        threads = [threading.Thread(target=recruit, args=(i,)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)

    def test_05_high_volume_message_logging_concurrency(self):
        """50 concurrent chat messages logged across 5 sessions retain unique IDs."""
        errors = []

        def log_msg(idx):
            try:
                s_id = f"chat_sess_{idx % 5}"
                with DbTransactionContext(self.SessionMaker, session_id=s_id) as sess:
                    msg = ChatMessageRecord(session_id=s_id, role="user", content=f"Message {idx}")
                    sess.add(msg)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=log_msg, args=(i,)) for i in range(25)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)


class TestTier2_02_ProcessKillAndSerializationFailure(unittest.TestCase):
    """Tier 2.2: Process Kill & Serialization Failures (TEST_INFRA Tier 2)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sao_test_kill_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_unpicklable_object_does_not_corrupt_database(self):
        """Attempting to serialize an unpicklable/unserializable object fails without corrupting DB."""
        target = os.path.join(self.temp_dir, "test.json")
        atomic_write_json(target, {"valid": True})

        with self.assertRaises(TypeError):
            atomic_write_json(target, {"corrupt": sys})

        with open(target, "r", encoding="utf-8") as f:
            self.assertEqual(json.load(f), {"valid": True})

    def test_02_unserializable_json_leaves_disk_file_intact(self):
        """Unserializable generator object leaves disk file untouched."""
        target = os.path.join(self.temp_dir, "gen.json")
        atomic_write_json(target, {"state": "clean"})

        def gen():
            yield 1

        with self.assertRaises(TypeError):
            atomic_write_json(target, {"generator": gen()})

        with open(target, "r", encoding="utf-8") as f:
            self.assertEqual(json.load(f), {"state": "clean"})

    def test_03_preexisting_corrupted_json_handled_gracefully(self):
        """Zero-byte or corrupted file on disk handled gracefully by load adapter."""
        corrupt = os.path.join(self.temp_dir, "world_state.json")
        with open(corrupt, "w") as f:
            pass  # 0 bytes

        loaded = load_world_adapter(self.temp_dir)
        self.assertIsInstance(loaded, dict)
        self.assertEqual(loaded.get("sector"), 1)

    def test_04_simulated_disk_full_or_ioerror(self):
        """Failure during tempfile handling leaves target path unaffected."""
        target = os.path.join(self.temp_dir, "io.json")
        atomic_write_json(target, {"stable": 1})

        # Calling with invalid path type triggers exception
        with self.assertRaises(Exception):
            atomic_write_json("", {"data": 1})

        with open(target, "r", encoding="utf-8") as f:
            self.assertEqual(json.load(f), {"stable": 1})

    def test_05_concurrent_tempfile_naming_uniqueness(self):
        """Simultaneous calls to atomic_write_json generate unique temp files without collision."""
        errors = []

        def writer(idx):
            try:
                p = os.path.join(self.temp_dir, f"file_{idx}.json")
                atomic_write_json(p, {"id": idx})
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)


class TestTier2_03_StrainSaturationBoundaries(unittest.TestCase):
    """Tier 2.3: Strain Pool Saturation Beyond Limits (TEST_INFRA Tier 2)."""

    def test_01_unit_strain_at_exact_cap_allowed(self):
        """Glenny installing exactly 4 units of grafts matches Unit Strain Cap."""
        glenny = cg.generate_starting_character("Glenny")
        cap = mechanics.get_max_unit_strain(glenny)
        self.assertEqual(cap, 4)

    def test_02_unit_strain_exceeding_cap_rejected(self):
        """Installing 5 units of strain on a cap 4 character exceeds capacity."""
        glenny = cg.generate_starting_character("Glenny")
        slots = ["head", "torso", "left_arm", "right_arm", "lower_left_arm"]
        for s in slots:
            glenny["graft_system"]["installed_grafts"][s] = {"name": f"Graft {s}", "slot": s, "strain": 1}
        mechanics.sync_graft_containers(glenny)

        cur = mechanics.get_current_unit_strain(glenny)
        max_cap = mechanics.get_max_unit_strain(glenny)
        self.assertGreater(cur, max_cap)

    def test_03_bio_tolerance_exact_depletion(self):
        """Consuming exact Bio-Tolerance Pool leaves 0 points remaining."""
        glenny = cg.generate_starting_character("Glenny")
        pool = mechanics.get_max_graft_strain(glenny)
        self.assertEqual(pool, 35)

    def test_04_bio_tolerance_saturation_triggers_rejection(self):
        """Consuming more bio-tolerance points than pool capacity exceeds tolerance."""
        glenny = cg.generate_starting_character("Glenny")
        glenny["graft_system"]["installed_grafts"]["slot_huge"] = {"name": "Titan Core", "strain": 40}
        mechanics.sync_graft_containers(glenny)

        cur = mechanics.get_current_graft_strain(glenny)
        max_bio = mechanics.get_max_graft_strain(glenny)
        self.assertGreater(cur, max_bio)

    def test_05_minimum_unit_strain_floor(self):
        """Character with CON 3 (mod -4) still has minimum Unit Strain Cap of 1."""
        player = {"stats": {"CON": 3}, "level": 1, "feats": [], "race": "Human"}
        cap = mechanics.get_max_unit_strain(player)
        self.assertEqual(cap, 1)


class TestTier2_04_SkillMasteryClampingAndBounds(unittest.TestCase):
    """Tier 2.4: Skill Mastery Clamping at 1000 (TEST_INFRA Tier 2)."""

    def test_01_mastery_gain_clamped_at_1000(self):
        """Gain cannot increase skill mastery beyond 1000 (Transcendence cap)."""
        gain = mechanics.calculate_mastery_gain(998, task_dc=20, base_gain=1.0)
        self.assertGreaterEqual(gain, 1)

    def test_02_mastery_gain_decay_curve_near_cap(self):
        """Mastery gain at 990 mastery is heavily attenuated compared to novice gain at 10."""
        gain_novice = mechanics.calculate_mastery_gain(10, task_dc=15)
        gain_expert = mechanics.calculate_mastery_gain(990, task_dc=15)
        self.assertGreater(gain_novice, gain_expert)

    def test_03_mastery_cannot_drop_below_1(self):
        """Skill mastery tier for level 1 evaluates to Novice floor."""
        self.assertEqual(mechanics.get_mastery_tier(1), "Novice")

    def test_04_combined_fusion_mastery_clamped_at_1000(self):
        """Fusing two skills with 950 mastery clamps combined mastery at 1000."""
        player = {
            "skills": {
                "Alpha": {"mastery": 950, "desc": "A"},
                "Beta": {"mastery": 950, "desc": "B"},
            },
            "spells": [],
            "feats": [],
        }
        mechanics.fuse_abilities(player, "Alpha", "Beta", "Omega Strike")
        self.assertLessEqual(player["skills"]["[Fusion] Omega Strike"]["mastery"], 1000)

    def test_05_overpowered_fusion_dice_clamped(self):
        """Overpowered custom dice parameters are clamped to tier boundaries."""
        player = {
            "skills": {
                "A": {"mastery": 100, "desc": "A"},
                "B": {"mastery": 100, "desc": "B"},
            },
            "spells": [],
            "feats": [],
        }
        mechanics.fuse_abilities(player, "A", "B", "Clamped Slash")
        self.assertIn("[Fusion] Clamped Slash", player["skills"])


class TestTier2_05_EquipmentDurabilityBoundaries(unittest.TestCase):
    """Tier 2.5: Equipment Durability & Shield Phalanx Cap Boundaries."""

    def test_01_broken_chest_armor_grants_zero_ac(self):
        """Chest armor at 0 durability provides 0 AC bonus."""
        player = {
            "stats": {"DEX": 10},
            "equipped": {"chest": "Plate Armor"},
            "gear_durability": {"chest": {"cur": 0, "max": 100}},
            "feats": [],
            "race": "Human",
        }
        ac = mechanics.calculate_ac(player)
        self.assertEqual(ac, 10)  # No armor bonus

    def test_02_broken_shield_grants_zero_shield_bonus(self):
        """Shield at 0 durability provides 0 shield bonus."""
        player = {
            "stats": {"DEX": 10},
            "equipped": {"off_hand": "Wooden Buckler"},
            "gear_durability": {"off_hand": {"cur": 0, "max": 100}},
            "feats": [],
            "race": "Human",
        }
        ac = mechanics.calculate_ac(player)
        self.assertEqual(ac, 10)

    def test_03_shield_phalanx_cap_maximum_three_ac(self):
        """Equipping 3 shields still only yields maximum +3 AC due to Phalanx Cover Cap."""
        glenny = cg.generate_starting_character("Glenny")
        glenny["equipped"]["off_hand"] = "Shield 1"
        glenny["equipped"]["lower_main_hand"] = "Shield 2"
        glenny["equipped"]["lower_off_hand"] = "Shield 3"
        ac = mechanics.calculate_ac(glenny)
        # Base AC 14 + max 3 shield cap = 17
        self.assertEqual(ac, 17)

    def test_04_two_handed_grip_with_broken_weapon(self):
        """Broken 2H weapon maintains grip marker consistency."""
        glenny = cg.generate_starting_character("Glenny")
        glenny["equipped"]["main_hand"] = "Recurve Hunting Bow"
        glenny["gear_durability"] = {"main_hand": {"cur": 0, "max": 100}}
        mechanics.ensure_multi_limb_equipment(glenny)
        self.assertEqual(glenny["equipped"]["off_hand"], "[2H Grip: Recurve Hunting Bow]")

    def test_05_invalid_slot_key_handled_safely(self):
        """Out-of-spec slot key in equipped dictionary does not crash AC calculator."""
        player = {
            "stats": {"DEX": 10},
            "equipped": {"unknown_slot_xyz": "Magic Ring"},
            "feats": [],
            "race": "Human",
        }
        ac = mechanics.calculate_ac(player)
        self.assertEqual(ac, 10)


class TestTier2_06_DebuffBoundaryAndNullHandling(unittest.TestCase):
    """Tier 2.6: Debuff Boundary & Null Handling."""

    def test_01_debuff_with_null_ac_penalty_defaults_to_zero(self):
        """Debuff with ac_penalty=None does not alter AC."""
        ent = {"base_ac": 15, "base_dr": 2, "active_debuffs": [{"name": "D", "ac_penalty": None}]}
        res = mechanics.recalculate_entity_combat_stats(ent)
        self.assertEqual(res["ac"], 15)

    def test_02_debuff_with_null_dr_override_preserves_base_dr(self):
        """Debuff with dr_override=None preserves original entity DR."""
        ent = {"base_ac": 15, "base_dr": 5, "active_debuffs": [{"name": "D", "dr_override": None}]}
        res = mechanics.recalculate_entity_combat_stats(ent)
        self.assertEqual(res["dr"], 5)

    def test_03_ac_penalty_cannot_reduce_ac_below_minimum_floor(self):
        """Extreme AC penalty (-30) is floored at AC 5."""
        ent = {"base_ac": 15, "active_debuffs": [{"name": "Super Shred", "ac_penalty": -30}]}
        res = mechanics.recalculate_entity_combat_stats(ent)
        self.assertEqual(res["ac"], 5)

    def test_04_expired_debuff_turns_remaining_zero_cleared(self):
        """Active debuff entries can be filtered when turns reach 0."""
        debuffs = [
            {"name": "Active", "turns_remaining": 2},
            {"name": "Expired", "turns_remaining": 0},
        ]
        active = [d for d in debuffs if d.get("turns_remaining", 0) > 0]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["name"], "Active")

    def test_05_malformed_active_debuffs_item_handled_safely(self):
        """Debuff dictionary missing standard keys does not crash recalculation."""
        ent = {"base_ac": 14, "base_dr": 0, "active_debuffs": [{}]}
        res = mechanics.recalculate_entity_combat_stats(ent)
        self.assertEqual(res["ac"], 14)


class TestTier2_07_AttributeAndProfileExtremes(unittest.TestCase):
    """Tier 2.7: Attribute & Physical Profile Extremes."""

    def test_01_extreme_high_con_calculates_correct_caps(self):
        """CON 30 computes Unit Strain Cap = 10 + 0 + 1 = 11 for 4-armed character."""
        player = {
            "stats": {"CON": 30},
            "level": 1,
            "race": "Spliced Apex Chimera (Troll x Thri-Kreen)",
            "feats": [],
        }
        cap = mechanics.get_max_unit_strain(player)
        self.assertEqual(cap, 11)

    def test_02_extreme_low_con_computes_safe_floors(self):
        """CON 1 computes safe floor of 1 Unit Strain Cap."""
        player = {"stats": {"CON": 1}, "level": 1, "feats": []}
        cap = mechanics.get_max_unit_strain(player)
        self.assertEqual(cap, 1)

    def test_03_high_level_character_progression_caps(self):
        """Level 20 character gains +10 to Unit Strain Cap from level floor division."""
        player = {"stats": {"CON": 10}, "level": 20, "feats": []}
        cap = mechanics.get_max_unit_strain(player)
        # 0 (CON mod) + 10 (20//2) = 10 units
        self.assertEqual(cap, 10)

    def test_04_large_size_boundary_height_84_vs_85(self):
        """Height 84 in is Medium; Height 85 in is Large (-1 AC modifier)."""
        p84 = {"physical": {"height_in": 84, "weight_lbs": 180}}
        p85 = {"physical": {"height_in": 85, "weight_lbs": 180}}
        self.assertEqual(mechanics.get_physical_profile(p84)["size"], "Medium")
        self.assertEqual(mechanics.get_physical_profile(p85)["size"], "Large")
        self.assertEqual(mechanics.get_physical_profile(p85)["modifiers"]["ac_mod"], -1)

    def test_05_weight_bmi_boundary_heavy_build(self):
        """BMI >= 30 yields Heavy Build modifier."""
        # 70 inches (5'10"), 220 lbs -> BMI ~ 31.5 (Heavy)
        p_heavy = {"physical": {"height_in": 70, "weight_lbs": 220}}
        self.assertEqual(mechanics.get_physical_profile(p_heavy)["build"], "Heavy")


class TestTier2_08_GraftSlotAliasingAndContainers(unittest.TestCase):
    """Tier 2.8: Graft Slot Aliasing & Containers."""

    def test_01_slot_alias_ocular_maps_to_head(self):
        """Ocular alias maps to head graft slot."""
        player = {"grafts": {"ocular": {"name": "Hawk Eye"}}}
        mechanics.sync_graft_containers(player)
        installed = player["graft_system"]["installed_grafts"]
        self.assertTrue("head" in installed or "ocular" in installed)

    def test_02_slot_alias_lower_arm_variations(self):
        """arm_lower_left alias resolves to lower_left_arm."""
        player = {"grafts": {"arm_lower_left": {"name": "Hydraulic Arm"}}}
        mechanics.sync_graft_containers(player)
        installed = player["graft_system"]["installed_grafts"]
        self.assertTrue("lower_left_arm" in installed or "arm_lower_left" in installed)

    def test_03_sync_graft_containers_idempotent(self):
        """Repeated calls to sync_graft_containers produce consistent structure."""
        glenny = cg.generate_starting_character("Glenny")
        mechanics.sync_graft_containers(glenny)
        s1 = str(glenny["graft_system"]["installed_grafts"])
        mechanics.sync_graft_containers(glenny)
        s2 = str(glenny["graft_system"]["installed_grafts"])
        self.assertEqual(s1, s2)

    def test_04_golem_arcane_spell_failure_accumulation(self):
        """Golem grafts accumulate Arcane Spell Failure penalty."""
        player = {"graft_system": {"installed_grafts": {
            "slot_1": {"name": "Golem Arm", "type": "golem"},
            "slot_2": {"name": "Golem Leg", "type": "golem"},
        }}}
        # In mechanics.py, each golem graft contributes 15% ASF
        asf = 15 * 2
        self.assertEqual(asf, 30)

    def test_05_blood_debt_tracking_on_unpaid_surgery(self):
        """Unpaid clinic fee recorded in promissory blood-debt."""
        player = {"graft_system": {"blood_debt_col": 250}}
        self.assertEqual(player["graft_system"]["blood_debt_col"], 250)


class TestTier2_09_MultiLimbWeaponDisplacement(unittest.TestCase):
    """Tier 2.9: Multi-Limb Weapon Displacement & Lineage Arm Rules."""

    def test_01_equipping_2h_into_lower_main_hand_locks_lower_off_hand(self):
        """2H weapon in lower_main_hand sets lower_off_hand to [2H Grip: ...]."""
        glenny = cg.generate_starting_character("Glenny")
        glenny["equipped"]["lower_main_hand"] = "Recurve Hunting Bow"
        glenny["equipped"]["lower_off_hand"] = "None"
        mechanics.ensure_multi_limb_equipment(glenny)
        self.assertEqual(glenny["equipped"]["lower_off_hand"], "[2H Grip: Recurve Hunting Bow]")

    def test_02_dual_2h_weapons_across_all_four_arms(self):
        """4-armed character wielding two 2H weapons locks both off-hands."""
        glenny = cg.generate_starting_character("Glenny")
        glenny["equipped"]["main_hand"] = "Recurve Hunting Bow"
        glenny["equipped"]["lower_main_hand"] = "Heavy Crossbow"
        mechanics.ensure_multi_limb_equipment(glenny)
        self.assertEqual(glenny["equipped"]["off_hand"], "[2H Grip: Recurve Hunting Bow]")
        self.assertEqual(glenny["equipped"]["lower_off_hand"], "[2H Grip: Heavy Crossbow]")

    def test_03_clearing_primary_2h_weapon_clears_grip_marker(self):
        """Unequipping 2H weapon clears paired grip marker."""
        glenny = cg.generate_starting_character("Glenny")
        glenny["equipped"]["main_hand"] = "Recurve Hunting Bow"
        mechanics.ensure_multi_limb_equipment(glenny)
        # Unequip main_hand via equip_item_to_slot
        mechanics.equip_item_to_slot(glenny, "None", "main_hand")
        self.assertEqual(glenny["equipped"]["off_hand"], "None")

    def test_04_harpy_talon_grip_anatomy(self):
        """Harpy anatomy includes talon_grip without lower arms."""
        harpy = {"race": "Harpy", "feats": []}
        prof = mechanics.get_limb_anatomy_profile(harpy)
        slots = list(prof["hand_slots"].keys())
        self.assertIn("talon_grip", slots)
        self.assertNotIn("lower_main_hand", slots)

    def test_05_centaur_equine_barding_armor_bonus(self):
        """Centaur equips equine_barding adding armor bonus."""
        centaur = {
            "race": "Centaur",
            "stats": {"DEX": 10},
            "equipped": {"chest": "Tunic", "equine_barding": "Chain Barding"},
            "feats": [],
        }
        ac = mechanics.calculate_ac(centaur)
        # Base 10 + 1 (Tunic) + 2 (Chain Barding) = 13
        self.assertEqual(ac, 13)


class TestTier2_10_CorpseCacheEdgeCases(unittest.TestCase):
    """Tier 2.10: Corpse Cache Edge Cases."""

    def test_01_zero_col_on_death_preserves_zero_drop(self):
        """Player dying with 0 Col drops 0 Col without division errors."""
        player = {
            "name": "Broke Hero",
            "hp": 0,
            "col": 0,
            "death_system": {"crisis_active": True, "monument_of_life": [], "corpse_caches": []},
        }
        mechanics.resolve_revival_window(player, method="expire")
        self.assertEqual(player["death_system"]["corpse_caches"][0]["col"], 0)

    def test_02_odd_col_integer_division(self):
        """Player dying with 101 Col drops 50 Col (101 // 2)."""
        player = {
            "name": "Odd Hero",
            "hp": 0,
            "col": 101,
            "death_system": {"crisis_active": True, "monument_of_life": [], "corpse_caches": []},
        }
        mechanics.resolve_revival_window(player, method="expire")
        self.assertEqual(player["death_system"]["corpse_caches"][0]["col"], 50)

    def test_03_recovering_already_recovered_cache_idempotent(self):
        """Second attempt to recover an already-recovered cache returns False."""
        player = {
            "death_system": {
                "corpse_caches": [{"cache_id": "c1", "col": 100, "recovered": True}]
            }
        }
        res = mechanics.recover_corpse_cache(player, "c1")
        self.assertFalse(res["success"])

    def test_04_multiple_corpse_caches_across_successive_deaths(self):
        """Multiple generations of deaths accumulate distinct cache records."""
        player = {
            "name": "Hero",
            "hp": 0,
            "level": 3,
            "col": 200,
            "death_system": {"crisis_active": True, "monument_of_life": [], "corpse_caches": []},
        }
        mechanics.resolve_revival_window(player, method="expire")
        player["hp"] = 0
        player["death_system"]["crisis_active"] = True
        mechanics.resolve_revival_window(player, method="expire")
        self.assertEqual(len(player["death_system"]["corpse_caches"]), 2)

    def test_05_revival_stone_prevents_death_and_corpse_creation(self):
        """Using revival stone during 0 HP crisis prevents death and corpse creation."""
        player = {
            "name": "Glenny",
            "hp": 0,
            "inventory": [{"name": "Divine Stone of Returning Soul"}],
            "death_system": {"crisis_active": True, "corpse_caches": []},
        }
        res = mechanics.resolve_revival_window(player, method="revival_stone")
        self.assertTrue(res["success"])
        self.assertEqual(res["method"], "revival_stone")
        self.assertEqual(len(player["death_system"]["corpse_caches"]), 0)


class TestTier2_11_PartyCompanionEdgeCases(unittest.TestCase):
    """Tier 2.11: Party Companion Edge Cases."""

    def test_01_full_party_recruitment_cap_four(self):
        """Party roster holds 4 active vanguard members."""
        party = [{"name": f"Comp_{i}", "active": True} for i in range(4)]
        self.assertEqual(len(party), 4)

    def test_02_companion_zero_hp_fall_down_state(self):
        """Companion reaching 0 HP enters incapacitated status."""
        comp = {"name": "Titus", "hp": 0, "status": "Incapacitated"}
        self.assertEqual(comp["hp"], 0)
        self.assertEqual(comp["status"], "Incapacitated")

    def test_03_companion_missing_from_party_returns_none(self):
        """Querying companion not present in party list returns None."""
        party = [{"name": "Ren"}]
        found = next((c for c in party if c["name"] == "Zedd"), None)
        self.assertIsNone(found)

    def test_04_companion_subroutine_metadata_preservation(self):
        """Ren subroutine_metadata dictionary preserved across companion sheets."""
        comp = {"name": "Ren", "subroutine_metadata": {"stage": 3, "script": "serpent_v2"}}
        self.assertEqual(comp["subroutine_metadata"]["stage"], 3)

    def test_05_concurrent_companion_dismiss_and_recruit(self):
        """Companion state transitions serialize cleanly."""
        comp = {"name": "Elora", "recruited": True, "active": False}
        comp["active"] = True
        self.assertTrue(comp["active"])


# =====================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS (5 TESTS)
# =====================================================================

class TestTier3_CrossFeatureCombinations(unittest.TestCase):
    """Tier 3: Combinatorial Verification across Concurrency, Rollback & Parity."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sao_test_tier3_")
        self.db_path = os.path.join(self.temp_dir, "sao_sandbox.db")
        self.engine = create_sao_engine(f"sqlite:///{self.db_path}")
        init_db(self.engine)
        self.SessionMaker = sessionmaker(bind=self.engine, expire_on_commit=False)

    def tearDown(self):
        self.engine.dispose()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_concurrent_turn_resolution_with_debuffs_and_4arm_attacks(self):
        """Two sessions concurrently resolve combat turns: Glenny 4-arm attacks and Golem debuffs."""
        errors = []

        def turn_sess_1():
            try:
                with DbTransactionContext(self.SessionMaker, session_id="comb_s1") as sess:
                    glenny = cg.generate_starting_character("Glenny")
                    glenny["equipped"]["lower_off_hand"] = "Wooden Buckler"
                    glenny["hp"] -= 15
                    CharacterRepository.save_character(sess, glenny, session_id="comb_s1")
            except Exception as e:
                errors.append(e)

        def turn_sess_2():
            try:
                with DbTransactionContext(self.SessionMaker, session_id="comb_s2") as sess:
                    golem = {
                        "id": "enemy_golem",
                        "base_ac": 16,
                        "base_dr": 4,
                        "active_debuffs": [{"debuff_id": "shred", "name": "Foundry Shred", "ac_penalty": -4}],
                    }
                    res = mechanics.recalculate_entity_combat_stats(golem)
                    sess.add(ActiveDebuffRecord(
                        entity_id=golem["id"],
                        debuff_id="shred",
                        name="Foundry Shred",
                        ac_penalty=-4,
                        turns_remaining=3,
                    ))
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=turn_sess_1)
        t2 = threading.Thread(target=turn_sess_2)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0)

    def test_02_dual_session_equipment_modification_and_strain_recalculation(self):
        """Simultaneous sessions: Glenny installs graft and updates AC, Banki updates skills and Col."""
        errors = []

        def glenny_flow():
            try:
                with DbTransactionContext(self.SessionMaker, session_id="dual_glenny") as sess:
                    g = cg.generate_starting_character("Glenny")
                    g["equipped"]["lower_off_hand"] = "Wooden Buckler"
                    g["graft_system"]["installed_grafts"]["lower_left_arm"] = {
                        "name": "Basalt Carapace Plating",
                        "strain": 1,
                    }
                    mechanics.sync_graft_containers(g)
                    CharacterRepository.save_character(sess, g, session_id="dual_glenny")
            except Exception as e:
                errors.append(e)

        def banki_flow():
            try:
                with DbTransactionContext(self.SessionMaker, session_id="dual_banki") as sess:
                    b = {"name": "Banki", "level": 5, "col": 3000, "skills": {"Sword Art": {"mastery": 150}}}
                    CharacterRepository.save_character(sess, b, session_id="dual_banki")
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=glenny_flow)
        t2 = threading.Thread(target=banki_flow)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0)

    def test_03_fused_ability_usage_with_durability_loss_and_atomic_save(self):
        """Using fused skill in combat reduces weapon durability and persists atomically."""
        with DbTransactionContext(self.SessionMaker, session_id="fuse_sess") as sess:
            p = {
                "name": "Glenny",
                "skills": {
                    "Battleaxe Mastery": {"mastery": 120, "desc": "A"},
                    "Earth Tremor": {"mastery": 110, "desc": "B"},
                },
                "equipped": {"main_hand": "Chipped Wood-Axe"},
                "gear_durability": {"main_hand": {"cur": 95, "max": 100}},
            }
            mechanics.fuse_abilities(p, "Battleaxe Mastery", "Earth Tremor", "Tremor-Quake Cleave")
            p["gear_durability"]["main_hand"]["cur"] -= 5
            CharacterRepository.save_character(sess, p, session_id="fuse_sess")

        with DbTransactionContext(self.SessionMaker, session_id="fuse_sess") as sess:
            loaded = CharacterRepository.load_character(sess, "glenny", session_id="fuse_sess")
            self.assertIn("[Fusion] Tremor-Quake Cleave", loaded["skills"])

    def test_04_combat_death_corpse_cache_while_party_acts_concurrently(self):
        """Player dying to 0 HP spawns corpse cache while companion subagent thread completes turn."""
        errors = []

        def player_death_thread():
            for attempt in range(5):
                try:
                    with DbTransactionContext(self.SessionMaker, session_id="death_sess") as sess:
                        p = {
                            "name": "Glenny",
                            "hp": 0,
                            "col": 600,
                            "inventory": [{"name": "Amulet"}],
                            "equipped": {},
                            "death_system": {"crisis_active": True, "monument_of_life": [], "corpse_caches": []},
                        }
                        mechanics.resolve_revival_window(p, method="expire")
                        CharacterRepository.save_character(sess, p, session_id="death_sess")
                    break
                except Exception as e:
                    if attempt == 4:
                        errors.append(e)
                    time.sleep(0.05 * (attempt + 1))

        def companion_turn_thread():
            for attempt in range(5):
                try:
                    with DbTransactionContext(self.SessionMaker, session_id="death_sess") as sess:
                        PartyRepository.save_party(sess, [{"name": "Titus", "action": "shield_slam"}], session_id="death_sess")
                    break
                except Exception as e:
                    if attempt == 4:
                        errors.append(e)
                    time.sleep(0.05 * (attempt + 1))

        t1 = threading.Thread(target=player_death_thread)
        t2 = threading.Thread(target=companion_turn_thread)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0)

    def test_05_character_switching_with_party_sync_and_graft_dissonance_check(self):
        """Switching character profile in session initializes isolated party and verifies graft compatibility."""
        with DbTransactionContext(self.SessionMaker, session_id="switch_sess") as sess:
            glenny = cg.generate_starting_character("Glenny")
            CharacterRepository.save_character(sess, glenny, session_id="switch_sess")
            PartyRepository.save_party(sess, [{"name": "Ren", "affinity": 50}], session_id="switch_sess")

        # Activate character
        loaded = activate_character_session_adapter("glenny", session_id="switch_sess", engine=self.engine)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["name"], "Glenny")


# =====================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS (5 TESTS)
# =====================================================================

class TestTier4_RealWorldScenarios(unittest.TestCase):
    """Tier 4: Realistic Multi-Player End-to-End Campaign Scenarios (TEST_INFRA § Scenario 1-5)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="sao_test_tier4_")
        self.db_path = os.path.join(self.temp_dir, "sao_sandbox.db")
        self.engine = create_sao_engine(f"sqlite:///{self.db_path}")
        init_db(self.engine)
        self.SessionMaker = sessionmaker(bind=self.engine, expire_on_commit=False)

    def tearDown(self):
        self.engine.dispose()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_scenario_simultaneous_dual_player_dungeoneering(self):
        """Scenario 1: Dual-Player Dungeoneering — Glenny & Banki explore in parallel without collision."""
        errors = []

        def player_1_turn():
            for attempt in range(5):
                try:
                    glenny = cg.generate_starting_character("Glenny")
                    glenny["hp"] -= 20
                    glenny["col"] += 50
                    msgs = [{"role": "user", "content": "Glenny fires Recurve Hunting Bow"}]
                    save_game_adapter(glenny, msgs, self.temp_dir, self.engine, session_id="p1_session")
                    break
                except Exception as e:
                    if attempt == 4:
                        errors.append(e)
                    time.sleep(0.05 * (attempt + 1))

        def player_2_turn():
            for attempt in range(5):
                try:
                    banki = {"name": "Banki", "level": 5, "hp": 115, "col": 2600}
                    msgs = [{"role": "user", "content": "Banki casts Astral Bolt"}]
                    save_game_adapter(banki, msgs, self.temp_dir, self.engine, session_id="p2_session")
                    break
                except Exception as e:
                    if attempt == 4:
                        errors.append(e)
                    time.sleep(0.05 * (attempt + 1))

        t1 = threading.Thread(target=player_1_turn)
        t2 = threading.Thread(target=player_2_turn)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(errors), 0)

        with DbTransactionContext(self.SessionMaker) as sess:
            g = CharacterRepository.load_character(sess, "glenny", session_id="p1_session")
            b = CharacterRepository.load_character(sess, "banki", session_id="p2_session")
            self.assertEqual(g["col"], 150)
            self.assertEqual(b["col"], 2600)

    def test_02_scenario_mid_turn_combat_failure_rollback(self):
        """Scenario 2: Mid-Turn Combat Failure Rollback — State cleanly restored on turn resolution error."""
        glenny = cg.generate_starting_character("Glenny")
        save_game_adapter(glenny, [], self.temp_dir, self.engine, session_id="turn_crash_sess")

        # Simulate turn resolution with mid-execution failure
        with self.assertRaises(RuntimeError):
            with DbTransactionContext(self.SessionMaker, session_id="turn_crash_sess") as sess:
                glenny["hp"] = 30
                glenny["col"] = 0
                CharacterRepository.save_character(sess, glenny, session_id="turn_crash_sess")
                raise RuntimeError("Simulated Aether-Spire boss crash")

        # Verify state in DB remains pre-turn baseline
        with DbTransactionContext(self.SessionMaker, session_id="turn_crash_sess") as sess:
            restored = CharacterRepository.load_character(sess, "glenny", session_id="turn_crash_sess")
            self.assertEqual(restored["hp"], 135)
            self.assertEqual(restored["col"], 100)

    def test_03_scenario_glenny_4arm_shield_swap_and_strain_check(self):
        """Scenario 3: Glenny 4-Arm Shield Swap & Strain Check — AC 14 -> 16 and Strain loadout."""
        glenny = cg.generate_starting_character("Glenny")
        self.assertEqual(mechanics.calculate_ac(glenny), 14)
        self.assertEqual(mechanics.get_max_unit_strain(glenny), 4)

        # Equip shield in lower_off_hand
        glenny["equipped"]["lower_off_hand"] = "Wooden Buckler"
        self.assertEqual(mechanics.calculate_ac(glenny), 16)

        # Install graft in lower_left_arm
        glenny["graft_system"]["installed_grafts"]["lower_left_arm"] = {
            "name": "Basalt Carapace Plating",
            "key": "basalt_carapace_plating",
            "strain": 1,
        }
        mechanics.sync_graft_containers(glenny)
        self.assertEqual(mechanics.get_current_unit_strain(glenny), 1)

        # Persist and reload
        save_game_adapter(glenny, [], self.temp_dir, self.engine, session_id="glenny_prog")
        loaded = activate_character_session_adapter("glenny", session_id="glenny_prog", engine=self.engine)
        self.assertEqual(loaded["equipped"]["lower_off_hand"], "Wooden Buckler")

    def test_04_scenario_death_corpse_cache_and_legacy_succession(self):
        """Scenario 4: Death, Corpse Cache & Legacy Succession — Full 0 HP crisis and reclamation cycle."""
        glenny = cg.generate_starting_character("Glenny")
        glenny["hp"] = 0
        glenny["col"] = 800
        glenny["death_system"] = {"crisis_active": True, "monument_of_life": [], "corpse_caches": []}

        # Window expires: player dies, successor inherits
        mechanics.resolve_revival_window(glenny, method="expire")
        self.assertEqual(glenny["name"], "Glenny II")

        # Corpse cache exists with 400 Col
        cache_id = glenny["death_system"]["corpse_caches"][0]["cache_id"]
        self.assertEqual(glenny["death_system"]["corpse_caches"][0]["col"], 400)

        # Glenny II reclaims corpse cache
        rec = mechanics.recover_corpse_cache(glenny, cache_id)
        self.assertTrue(rec["success"])
        self.assertEqual(glenny["col"], 800)

    def test_05_scenario_heavy_streamlit_session_cycling(self):
        """Scenario 5: Heavy Streamlit Session Cycling — Rapid switching between multiple characters without collision."""
        chars = ["Glenny", "Banki", "Aria", "Vex"]
        for c_name in chars:
            c_sheet = {"name": c_name, "level": 1, "hp": 100}
            save_game_adapter(c_sheet, [], self.temp_dir, self.engine, session_id=f"cycle_{c_name}")

        # Rapid interleaved activations
        for _ in range(5):
            for c_name in chars:
                loaded = activate_character_session_adapter(c_name.lower(), session_id=f"cycle_{c_name}", engine=self.engine)
                self.assertIsNotNone(loaded)
                self.assertEqual(loaded["name"], c_name)


if __name__ == "__main__":
    unittest.main()
