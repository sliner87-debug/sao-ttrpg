# Project: 1–1000 Skill Mastery & Milestone Auto-Unlocker System (The Fractured Overlay)

## Architecture
The system integrates deterministic mechanics calculation, dynamic LLM encounter generation, and an interactive Streamlit HUD sidebar to deliver a 1–1000 LitRPG skill mastery experience adhering to the SAO Cardinal System fantasy.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Streamlit Frontend (app.py)                     │
│  - Player HUD Sidebar: Mastery Gauges (X/1000), Tier Badges, Progress  │
│  - Nested Milestone Perks Display & Target Milestone Previews           │
│  - Root Dev Console Skill Test Bench & Action DC Simulator             │
│  - Autosave Persistence Lifecycle (save_game.json)                     │
└─────────────────────────────────┬──────────────────────────────────────┘
                                  │
                   State Updates  │  Reads Player State
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   Backend Mechanics (backend/mechanics.py)             │
│  - Progress Tiers: Novice (1-49), Apprentice (50), Journeyman (100),   │
│    Adept (250), Master (500), Grandmaster (750), Transcendence (1000) │
│  - Exponential Diminishing Returns Gain Math (Task DC & Current Tier)  │
│  - Canonical Milestone Dictionary (24 Perks across 4 Core Archetypes:   │
│    One-Handed Axes, Trench Hammers, Field Trapping, Cartography)       │
│  - Structured Dictionary Migration & Auto-Unlock Threshold Detection   │
└─────────────────────────────────┬──────────────────────────────────────┘
                                  │
                   Hybrid Fallback│  Emergent Skills
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                 Encounter Director (backend/llm_engine.py)             │
│  - Google GenAI (gemini-3.8-flash) Procedural Milestone Generator      │
│  - Offline Deterministic Heuristic Fallback Generator (Test-Safe)      │
│  - Power Curve Enforcement Across Tiers (Apprentice -> Transcendence)  │
│  - Cardinal System Broadcast & High-Impact Celebratory Announcements   │
└─────────────────────────────────┬──────────────────────────────────────┘
                                  │
                         Verifies │  E2E Playtesting
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│            Automated Playtest & Diagnostic Suite                       │
│                   (test_playtest_phase_m2.py)                          │
│  - Tier 1: Feature Coverage (Core mechanics, gains, thresholds)        │
│  - Tier 2: Boundary & Corner Cases (49->50, 99->100, 249->250, 1000)   │
│  - Tier 3: Cross-Feature Combinations (Hybrid canonical/procedural)     │
│  - Tier 4: Real-World Workload Playtesting (Simulated sessions & save) │
│  - Tier 5: Adversarial Hardening (Challengers & fuzzing)               │
└────────────────────────────────────────────────────────────────────────┘
```

## Code Layout
- `backend/mechanics.py`: Deterministic crunchy math (tier mappings, exponential DC gain formula, canonical perks dictionary, threshold detection, migration logic). Owned by Milestone M1.
- `backend/llm_engine.py`: GenAI procedural milestone generator, offline fallback generator, power curve constraints, celebratory Cardinal announcements, turn state integration. Owned by Milestone M2.
- `app.py`: Streamlit frontend HUD (expander layout, tier badges, progress bars, milestone perks listing, dev console test bench, turn loop integration, autosave). Owned by Milestone M3.
- `save_game.json`: Canonical persistence file for player character sheet, skills, feats, spells, and messages.
- `test_playtest_phase_m2.py`: Automated playtesting and diagnostic suite (Tiers 1-4). Owned by E2E Testing Track / M4.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | 1-1000 Progression Math & Tiers | 7-tier scale (Novice to Transcendence) with exponential diminishing returns based on Task DC and current tier | M1 | ORIGINAL_REQUEST §R1 |
| 2 | Structured Skill Schema | Canonical dict format `{"mastery": int, "tier": str, "description": str, "milestones_unlocked": list}` | M1 | ORIGINAL_REQUEST §R1 |
| 3 | Legacy Save Migration | Safe, backward-compatible migration of legacy list/dict formats in `player["skills"]` | M1 | ORIGINAL_REQUEST §R1, Acceptance Criteria |
| 4 | Canonical Core Archetype Perks | Handcrafted 24 perks across 6 thresholds for One-Handed Axes, Trench Hammers, Field Trapping, Cartography | M1 | ORIGINAL_REQUEST §R2 |
| 5 | Procedural Milestone Generator | GenAI (`gemini-3.8-flash`) generator in `llm_engine.py` for custom/emergent skills | M2 | ORIGINAL_REQUEST §R2 |
| 6 | Offline Fallback Milestone Generator | Deterministic, offline heuristic generator guaranteeing zero-failure test execution | M2 | Survey Explorer 2 |
| 7 | Power Curve Guardrails | Strict tier-based constraints (Apprentice passive, Journeyman active combo, etc.) | M2 | ORIGINAL_REQUEST §R2 |
| 8 | Auto-Unlock & Character Sheet Sync | Auto-append perks to `player["feats"]` or `player["spells"]` and `milestones_unlocked` | M2 | ORIGINAL_REQUEST §R2 |
| 9 | Cardinal Celebratory Announcements | High-impact markdown banners in narrative and combat logs upon crossing thresholds | M2 | ORIGINAL_REQUEST §R2 |
| 10 | Streamlit Sidebar Mastery Gauges | Display exact `(X / 1000)`, colored tier badges (`[Apprentice]`, etc.), and smooth progress bars | M3 | ORIGINAL_REQUEST §R3 |
| 11 | Nested Milestone Perks Display | Indented listing of unlocked perks with descriptions directly beneath parent skill in HUD | M3 | ORIGINAL_REQUEST §R3 |
| 12 | Locked Milestone Previews | Subtle indicator of next milestone threshold and required points | M3 | Survey Explorer 3 |
| 13 | Root Dev Console Test Bench | Interactive controls in dev console: skill selector, threshold jump buttons, DC simulation, database override | M3 | Survey Explorer 3 |
| 14 | Autosave State Persistence | Atomic persistence to `save_game.json` across turn actions and dev overrides | M3 | ORIGINAL_REQUEST §R3 |
| 15 | Automated Playtest & Diagnostic Suite | `test_playtest_phase_m2.py` simulating action gain, threshold crossing (50, 100, 250), perk population, save/load | M4 | ORIGINAL_REQUEST §R4 |
| 16 | Final E2E Pass & Adversarial Hardening | 100% pass of E2E suite + white-box adversarial verification and coverage hardening (Tier 5) | Final | ORIGINAL_REQUEST §R4, Project Pattern |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Skill Engine & Calculations | `backend/mechanics.py`: Tier math, exponential DC gain formula, canonical dictionary (24 perks), migration function | None | DONE |
| M2 | Hybrid Milestone Auto-Unlock & Procedural Engine | `backend/llm_engine.py`: Procedural generator, offline fallback, power curve enforcement, celebratory announcements, auto-unlock state updates | M1 | DONE |
| M3 | Streamlit HUD Upgrades & Dev Console | `app.py`: Sidebar HUD expander, tier badges, progress bars, milestone perk listings, dev console test bench, turn loop integration, autosave | M1, M2 | DONE |
| M4 | E2E Playtest Suite Infrastructure | `test_playtest_phase_m2.py`: 4-tier opaque-box automated test runner | M1, M2, M3 | DONE |
| Final | E2E Verification & Adversarial Hardening | Pass 100% of `test_playtest_phase_m2.py` (Phase 1) + Tier 5 Adversarial Hardening & Forensic Audit (Phase 2) | M4 | DONE |

## Interface Contracts

### `backend/mechanics.py`
- `get_mastery_tier(mastery: int) -> str`
- `get_tier_badge(tier: str) -> str`
- `calculate_mastery_gain(current_mastery: int, task_dc: int = 15, base_gain: float = 1.0, success: bool = True, critical: bool = False) -> int`
- `check_milestone_unlocks(skill_name: str, old_mastery: int, new_mastery: int, existing_milestones: list = None) -> list[dict]`
- `update_skill_mastery(player_state: dict, skill_name: str, gain_or_dc: int = 1, is_dc: bool = False, desc: str = "", critical: bool = False) -> dict`
- `migrate_player_skills(player_state: dict) -> dict`
- `get_canonical_milestone(skill_name: str, threshold: int) -> dict | None`
- Constants: `SKILL_TIER_THRESHOLDS`, `MILESTONE_THRESHOLDS`, `CANONICAL_MILESTONES`

### `backend/llm_engine.py`
- `generate_procedural_milestone(api_key: str, skill_name: str, current_mastery: int, threshold: int, player_state: dict = None) -> dict`
- `generate_fallback_milestone(skill_name: str, threshold: int, player_state: dict = None) -> dict`
- `check_and_unlock_milestones(player_state: dict, skill_name: str, old_mastery: int, new_mastery: int, api_key: str = None) -> list[dict]`
- `apply_skill_updates_with_milestones(player_state: dict, skill_updates: list[dict], api_key: str = None) -> tuple[list[dict], str, list[str]]`
- `format_celebration_announcement(skill_name: str, threshold: int, tier_name: str, perk_name: str, perk_type: str, mechanical_effect: str) -> str`

### `app.py`
- Consumes `mechanics.migrate_player_skills(player)` on load.
- Consumes `mechanics.update_skill_mastery` or `llm_engine.apply_skill_updates_with_milestones` on turn processing.
- Displays `player["skills"]` structured format with tier badges and nested milestone perks.
- Dev Console updates persist directly to `save_game.json` via `save_game(player, messages)`.
