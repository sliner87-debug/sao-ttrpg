"""
backend/database
================
ACID-Compliant Relational Persistence Engine & Atomic Adapters for SAO Sandbox V2.
"""

from typing import Any

from backend.database.adapters import (
    activate_character_session,
    atomic_read_json,
    atomic_write_json,
    ensure_baseline_persistence_fidelity,
    ensure_database_initialized,
    get_base_dir,
    list_save_slots,
    load_game,
    load_world,
    mirror_character_to_disk,
    mirror_master_state_to_disk,
    mirror_party_to_disk,
    mirror_staging_ground_to_disk,
    mirror_world_state_to_disk,
    sanitize_character_slug,
    save_game,
)
from backend.database.engine import (
    check_db_health,
    create_sao_engine,
    db_transaction,
    drop_db,
    execute_post_commit_hooks,
    get_db_session,
    get_engine,
    get_scoped_session,
    get_session_factory,
    get_sqlite_pragmas,
    init_db,
    register_post_commit_hook,
    reset_engine,
)
from backend.database.models import (
    ActiveDebuffRecord,
    AnatomicalGraftRecord,
    ArchivedSkillRecord,
    Base,
    CampaignSessionRecord,
    CharacterRecord,
    ChatMessageRecord,
    CorpseCacheRecord,
    EquippedSlotRecord,
    MasterGameStateRecord,
    PartyCompanionRecord,
    SkillMasteryRecord,
)
from backend.database.migrator import (
    migrate_all_disk_saves_to_db,
    migrate_character_file,
    migrate_master_state_file,
    migrate_party_directory,
    migrate_world_state_file,
    verify_migration_fidelity,
)
from backend.database.repositories import (
    CharacterRepository,
    CorpseCacheRepository,
    MasterStateRepository,
    PartyRepository,
    StagingRepository,
    WorldRepository,
)

__all__ = [
    # Repositories
    "CharacterRepository",
    "CorpseCacheRepository",
    "WorldRepository",
    "MasterStateRepository",
    "PartyRepository",
    "StagingRepository",
    # Migration Utilities
    "migrate_all_disk_saves_to_db",
    "migrate_character_file",
    "migrate_party_directory",
    "migrate_master_state_file",
    "migrate_world_state_file",
    "verify_migration_fidelity",
    # Declarative Base & ORM Models
    "Base",
    "CampaignSessionRecord",
    "CharacterRecord",
    "EquippedSlotRecord",
    "AnatomicalGraftRecord",
    "ActiveDebuffRecord",
    "SkillMasteryRecord",
    "ArchivedSkillRecord",
    "PartyCompanionRecord",
    "MasterGameStateRecord",
    "CorpseCacheRecord",
    "ChatMessageRecord",
    # Engine & Session Management
    "get_engine",
    "create_sao_engine",
    "reset_engine",
    "get_session_factory",
    "get_scoped_session",
    "get_db_session",
    "db_transaction",
    "init_db",
    "drop_db",
    "check_db_health",
    "get_sqlite_pragmas",
    "register_post_commit_hook",
    "execute_post_commit_hooks",
    # Atomic Disk Adapters & Compatibility
    "atomic_write_json",
    "atomic_read_json",
    "mirror_character_to_disk",
    "mirror_party_to_disk",
    "mirror_master_state_to_disk",
    "mirror_world_state_to_disk",
    "mirror_staging_ground_to_disk",
    "save_game",
    "load_world",
    "load_game",
    "activate_character_session",
    "list_save_slots",
    "ensure_database_initialized",
    "ensure_baseline_persistence_fidelity",
    "get_base_dir",
    "sanitize_character_slug",
]


def __getattr__(name: str) -> Any:
    if name == "engine":
        return get_engine()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
