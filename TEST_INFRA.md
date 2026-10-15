# E2E Test Infra: Fractured Earth SAO Sandbox V2 Concurrency & Persistence

## Test Philosophy
- Opaque-box, requirement-driven testing derived from `ORIGINAL_REQUEST.md`.
- No dependency on implementation internals; interacts via client APIs (`save_game()`, `load_world()`, `activate_character_session()`, database sessions, and multi-session CLI runners).
- Methodology: Category-Partition + Boundary Value Analysis + Pairwise Combinatorial Testing + Real-World Workload Testing.

## Feature Inventory
| # | Feature | Source (Requirement) | Tier 1 | Tier 2 | Tier 3 |
|---|---------|---------------------|:------:|:------:|:------:|
| 1 | Concurrent Multi-Session Persistence | ORIGINAL_REQUEST R1 | 5 | 5 | ✓ |
| 2 | Atomic Transactions & Rollback | ORIGINAL_REQUEST R1 | 5 | 5 | ✓ |
| 3 | Zero-Byte Corruption Prevention | ORIGINAL_REQUEST R1 | 5 | 5 | ✓ |
| 4 | Multi-Limb Equipment (4 Arms, Talon, 2H Grip) | ORIGINAL_REQUEST R2 | 5 | 5 | ✓ |
| 5 | Extended Graft Slots & Metabolic Strain | ORIGINAL_REQUEST R2 | 5 | 5 | ✓ |
| 6 | Mutable Debuffs & Combat Stats (AC/DR) | ORIGINAL_REQUEST R2 | 5 | 5 | ✓ |
| 7 | Skill Mastery & Ability Fusion Matrix | ORIGINAL_REQUEST R2 | 5 | 5 | ✓ |
| 8 | Corpse Cache & Monument Lifecycles | ORIGINAL_REQUEST R2 | 5 | 5 | ✓ |
| 9 | Glenny AC 14/16 & Secondary Ganglia Parity | ORIGINAL_REQUEST Criteria | 5 | 5 | ✓ |
| 10 | Party State Isolation Across Sessions | ORIGINAL_REQUEST R1 | 5 | 5 | ✓ |
| 11 | Streamlit & CLI Backward Compatibility | ORIGINAL_REQUEST R3 | 5 | 5 | ✓ |

## Test Architecture
- Test Runner: `python -m unittest test_concurrency_and_rollback.py` and master runner script.
- All 5 existing test suites must also run and pass 100%:
  - `python test_tutorial_and_gender.py`
  - `python test_phases_10_to_13_v2.py`
  - `python test_podcast_fixes_1_to_9.py`
  - `python test_audit_all_phases.py`
  - `python test_v2_integration.py`
- Test Case Structure:
  - Tier 1: Isolated feature coverage (>=5 test cases per feature).
  - Tier 2: Boundary & Corner cases (simultaneous collision on same ID, zero-byte kill signals, max strain over-saturation, 1000 mastery cap).
  - Tier 3: Cross-feature combinations (concurrent turn combat with debuffs + 4-arm weapons + party sync).
  - Tier 4: Real-world application scenarios (Full campaign multi-player session simulation with 2 players acting concurrently, taking turns, taking damage, dying to spawn corpse cache, saving, and reloading).

## Real-World Application Scenarios (Tier 4)
| # | Scenario | Features Exercised | Complexity |
|---|----------|--------------------|------------|
| 1 | Simultaneous Dual-Player Dungeoneering | Multi-session concurrency, separate characters (Glenny & Banki), party isolation, atomic save | High |
| 2 | Mid-Turn Combat Failure Rollback | Turn resolution exception, atomic rollback, state unchanged in DB and disk | High |
| 3 | Glenny 4-Arm Shield Swap & Strain Check | Glenny loadout, AC 14 unshielded -> AC 16 with shield, Unit Strain Cap 4 | Medium |
| 4 | Death, Corpse Cache & Legacy Succession | Combat death at 0 HP, corpse cache creation, recovery by successor | High |
| 5 | Heavy Streamlit Session Cycling | Rapid switching between multiple characters without file collision or state loss | High |

## Coverage Thresholds
- Tier 1: >=55 test cases across 11 features
- Tier 2: >=55 boundary and stress cases
- Tier 3: Pairwise combinations across concurrency + mechanics
- Tier 4: >=5 realistic multi-player campaign scenarios
- Total E2E Target: >=120 automated test cases
