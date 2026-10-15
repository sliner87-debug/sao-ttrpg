# Project: Fractured Earth SAO Sandbox V2 Database Persistence Migration

## Architecture
Migration from single-player raw JSON file persistence (`save_game.json`, `.game_state/secret_master_state.json`, `Party/`, `Staging_Ground/`) to an ACID-compliant, concurrent relational persistence engine powered by SQLAlchemy 2.0 with SQLite WAL mode and PostgreSQL connection pooling, coupled with an Atomic Disk-Mirroring Adapter for 100% backward compatibility with Streamlit `app.py` and existing CLI test suites.

```
+---------------------------------------------------------------------------------------+
|                                    Clients / Callers                                   |
|   Streamlit Multi-Session UI (app.py)   |   Headless CLI Tests / Automated Test Suites |
+------------------------------------+--------------------------------------------------+
                                     |
                                     v
+---------------------------------------------------------------------------------------+
|                        Backward Compatibility & Adapter Layer                         |
|   - save_game(player, msgs) adapter (74 call sites in app.py)                         |
|   - load_world(base_dir) & activate_character_session() adapter                       |
|   - Character generator & profile discovery adapters                                   |
|   - Atomic Disk-Mirroring Engine (atomic_write_json via tempfile + os.replace + fsync)|
+------------------------------------+--------------------------------------------------+
                                     |
                                     v
+---------------------------------------------------------------------------------------+
|                            Database Repository & Service Layer                        |
|   - Session & Transaction Management (db_transaction context manager)                 |
|   - CharacterRepository (V2 Entity Serialization / Deserialization)                   |
|   - PartyRepository (Session-Isolated Companion Synchronization)                      |
|   - MasterStateRepository (Isolated GM Master & World State)                          |
|   - StagingRepository (Turn Action Queue & Visible Room Resolution)                    |
+------------------------------------+--------------------------------------------------+
                                     |
                                     v
+---------------------------------------------------------------------------------------+
|                                 SQLAlchemy 2.0 Engine                                 |
|   - Engine Factory (SQLite WAL: PRAGMA journal_mode=WAL; busy_timeout=30000)          |
|   - PostgreSQL Connection Pool (QueuePool)                                            |
|   - Relational Schema:                                                                |
|       * campaign_sessions                                                             |
|       * characters                                                                    |
|       * character_equipped_slots                                                      |
|       * character_grafts                                                              |
|       * character_active_debuffs                                                      |
|       * character_skills & archived_skills                                            |
|       * party_companions                                                              |
|       * master_game_states                                                            |
|       * corpse_caches                                                                 |
|       * chat_messages                                                                 |
+------------------------------------+--------------------------------------------------+
                                     |
                                     v
+---------------------------------------------------------------------------------------+
|                                Authoritative Storage Engine                           |
|       sao_sandbox.db (SQLite WAL) / PostgreSQL Server + Atomic Mirrored JSON Files    |
+---------------------------------------------------------------------------------------+
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Relational Engine & Pool | SQLAlchemy 2.0 engine factory with SQLite WAL mode (`PRAGMA journal_mode=WAL;`, `busy_timeout=30000;`) and PostgreSQL `QueuePool` | M1 | ORIGINAL_REQUEST R1 |
| 2 | Atomic Transactions & Rollback | `db_transaction()` context manager with commit/rollback semantics for zero corruption | M1 | ORIGINAL_REQUEST R1, Acceptance Criteria |
| 3 | Zero-Byte Corruption Prevention | `atomic_write_json()` helper using `tempfile` + `os.replace` + `os.fsync` eliminating `open('w')` truncation | M1 | ORIGINAL_REQUEST R1 |
| 4 | Relational Schema Models | Declarative models for sessions, characters, slots, grafts, debuffs, skills, companions, and world state | M1 | ORIGINAL_REQUEST R1, R2 |
| 5 | Multi-Limb Equipment Persistence | Support for `main_hand`, `off_hand`, `lower_main_hand`, `lower_off_hand`, `head`, `chest`, `accessory`, `equine_barding`, `talon_grip` | M2 | ORIGINAL_REQUEST R2 |
| 6 | 2H Grip String Bindings | Preservation of literal `[2H Grip: <Weapon>]` strings in paired off-hand slots | M2 | ORIGINAL_REQUEST R2 |
| 7 | Extended Graft Slots Persistence | Support for 9+ anatomical graft slots (`head`, `torso`, `left_arm`, `right_arm`, `lower_left_arm`, `lower_right_arm`, `legs`, `spine`, `tail`) | M2 | ORIGINAL_REQUEST R2 |
| 8 | Metabolic Strain Tracking | Persistence and recalculation of Unit Strain (+1 Secondary Ganglia) and Bio-Tolerance Pool | M2 | ORIGINAL_REQUEST R2 |
| 9 | Mutable Debuffs & Combat Stats | Persistence of `active_debuffs` arrays with AC penalty and DR override recalculations (`recalculate_entity_combat_stats`) | M2 | ORIGINAL_REQUEST R2 |
| 10 | Skill Mastery & Ability Fusion | 1–1000 skill mastery, `[Fusion] <Name>` skills, and `archived_base_skills` retention for relearning | M2 | ORIGINAL_REQUEST R2 |
| 11 | Corpse Cache & Monument Lifecycles | Persistent floor corpse caches (50% Col, gear, items) and monument of life across successions | M2 | ORIGINAL_REQUEST R2 |
| 12 | Glenny Profile & AC 14/16 Parity | Exact database hydration of Glenny's Large 4-armed profile: AC 14 base / AC 16 with shield, Unit Strain Cap 4 | M2 | ORIGINAL_REQUEST Acceptance Criteria |
| 13 | Multi-Session Party State Isolation | Decouple `Party/*.json` into database records partitioned by `session_id` to prevent cross-player contamination | M3 | ORIGINAL_REQUEST R1 |
| 14 | GM Master State Isolation | Replace singleton `.game_state/secret_master_state.json` with session-scoped database state | M3 | ORIGINAL_REQUEST R1 |
| 15 | Staging Ground Queue Isolation | Replace global `Staging_Ground/action_queue.json` and `visible_room.json` with session-isolated staging records | M3 | ORIGINAL_REQUEST R1 |
| 16 | Seed Migration Utility | Script/utility to migrate existing JSON save files (`save_game.json`, `saves/`, `Campaign_Data/`) into relational DB | M3 | Survey Findings |
| 17 | Streamlit save_game() Adapter | Backward-compatible adapter for `save_game(player, msgs)` across 74 call sites in `app.py` | M4 | ORIGINAL_REQUEST R3 |
| 18 | Streamlit load_world() Adapter | Backward-compatible adapter for `load_world()` and `activate_character_session()` | M4 | ORIGINAL_REQUEST R3 |
| 19 | Atomic Disk-Mirroring for Tests | Automatic synchronization of `save_game.json` and companion JSONs on commit to maintain CLI test compatibility | M4 | ORIGINAL_REQUEST R3 |
| 20 | 100% Pass Rate on 5 V2 Test Suites | Pass `test_tutorial_and_gender.py`, `test_phases_10_to_13_v2.py`, `test_podcast_fixes_1_to_9.py`, `test_audit_all_phases.py`, `test_v2_integration.py` | M4 | ORIGINAL_REQUEST Acceptance Criteria |
| 21 | Concurrency & Rollback E2E Testing | Comprehensive automated test suite verifying simultaneous sessions, atomic rollback, and zero-byte protection | M5 / Test Track | ORIGINAL_REQUEST Acceptance Criteria |
| 22 | Adversarial Hardening (Tier 5) | White-box stress testing, race-condition fuzzing, and corrupted input resistance verification | M5 / Test Track | Project Pattern |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Testing Track | Requirement-driven test suite (Tiers 1–4: Concurrency, Rollback, Parity, Stress) + TEST_READY.md | none | DONE |
| M1 | Relational Engine & Schema | SQLAlchemy 2.0 models, SQLite WAL engine, atomic transaction manager, atomic write helper | none | DONE |
| M2 | V2 Mechanics Persistence Layer | Multi-limb slots, 2H grips, 9 grafts, strain math, debuffs, fusion matrix, Glenny AC 14/16 | M1 | DONE |
| M3 | Multi-Session Party & World State | Session-isolated party companions, GM master state, staging ground, seed migration | M1, M2 | DONE |
| M4 | Compatibility Adapters & 5 Test Suites | Streamlit save_game/load_world adapters, atomic disk mirror, 100% pass on 5 V2 suites | M2, M3 | DONE |
| M5 | Final E2E Pass & Adversarial Hardening | Pass 100% of E2E tests (Tiers 1–4) + Tier 5 Challenger adversarial hardening | M4, E2E | DONE |

## Interface Contracts
### Client / UI ↔ Persistence Layer
- `save_game(player_state: dict, messages: list, session_id: str = "default") -> bool`
  Saves character state and message history atomically to relational DB and mirrors to disk. Returns True on success.
- `load_world(base_dir: str, session_id: str = "default") -> dict`
  Loads world state, current player, and party companions for the given session.
- `activate_character_session(character_slug: str, session_id: str) -> dict`
  Switches the active character for a specific player session without polluting global files or other player sessions.

### Repository ↔ Database Engine
- `db_transaction(session_id: Optional[str] = None) -> Iterator[Session]`
  Context manager providing atomic commit/rollback semantics with thread/session isolation.
- `CharacterRepository.save_character(db_session, character_dict: dict, session_id: str) -> CharacterRecord`
- `CharacterRepository.load_character(db_session, character_slug: str, session_id: str) -> dict`
- `PartyRepository.save_party(db_session, companions: list, session_id: str) -> None`
- `PartyRepository.load_party(db_session, session_id: str) -> list`

### Disk-Mirroring Engine
- `atomic_write_json(file_path: str, data: Union[dict, list]) -> None`
  Writes serialized JSON to `tempfile.NamedTemporaryFile` in same directory, runs `flush()` and `os.fsync()`, then atomically moves via `os.replace()`.

## Code Layout
- `backend/database/` (NEW):
  * `backend/database/__init__.py`: Package root, exports public engine and repository API.
  * `backend/database/models.py`: SQLAlchemy 2.0 ORM models.
  * `backend/database/engine.py`: Engine factory, connection pool, PRAGMA setup, `db_transaction`.
  * `backend/database/repositories.py`: Character, Party, World, and Staging repositories.
  * `backend/database/adapters.py`: Backward compatibility adapters for `save_game()`, `load_world()`, `atomic_write_json`.
  * `backend/database/migrator.py`: Seed migration utility from existing JSON saves to relational DB.
- `tests/` or root test suite:
  * `test_concurrency_and_rollback.py`: E2E concurrency, atomicity, zero-byte corruption, and parity verification.
