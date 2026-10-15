# E2E Test Infra: 1–1000 Skill Mastery & Milestone Auto-Unlocker System

## Test Philosophy
- **Requirement-Driven & Opaque-Box**: Exercises the skill engine, auto-unlock pipeline, save persistence, and HUD data structures according to the authoritative requirements in `ORIGINAL_REQUEST.md`.
- **Offline Reliability**: Must execute deterministically without requiring external API keys or live network connectivity (leveraging fallback procedural generators).
- **Zero-Tolerance Regression**: Validates that all modifications compile without syntax/lint errors, preserve existing save game schemas, and exit with code 0.

## Feature Inventory Mapping
| # | Feature | Requirement Source | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|---|---------|-------------------|:------:|:------:|:------:|:------:|
| 1 | 1-1000 Progression Math & Tiers | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 2 | Structured Skill Schema | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 3 | Legacy Save Migration | ORIGINAL_REQUEST §R1 | 5 | 5 | ✓ | ✓ |
| 4 | Canonical Core Perks (Axes, Hammers, Trapping, Maps) | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 5 | Hybrid / Procedural Unlock System | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 6 | Auto-Append to Feats & Spells | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 7 | Celebratory Announcements | ORIGINAL_REQUEST §R2 | 5 | 5 | ✓ | ✓ |
| 8 | Streamlit HUD Data Contract | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |
| 9 | Save/Load State Persistence | ORIGINAL_REQUEST §R3 | 5 | 5 | ✓ | ✓ |

## Test Architecture
- **Test Runner Location**: `H:\Antigravity\SAO Mockup\test_playtest_phase_m2.py`
- **Invocation Command**: `python test_playtest_phase_m2.py`
- **Pass/Fail Semantics**:
  - Exits with return code `0` on 100% pass.
  - Exits with return code `1` and detailed failure trace if any assertion fails.
  - Produces structured pass/fail matrix summarizing all test tiers.

## Tier Breakdown & Coverage Strategy

### Tier 1 — Feature Coverage (Happy Path)
- Test 1.1: Verify 7 tier classifications (Novice, Apprentice, Journeyman, Adept, Master, Grandmaster, Transcendence).
- Test 1.2: Verify dynamic gain math with standard Task DC (DC 15).
- Test 1.3: Verify structured schema normalization for skills.
- Test 1.4: Verify canonical perks retrieved for One-Handed Axes at 50, 100, 250, 500, 750, 1000.
- Test 1.5: Verify canonical perks retrieved for Trench Hammers across all thresholds.
- Test 1.6: Verify canonical perks retrieved for Field Trapping across all thresholds.
- Test 1.7: Verify canonical perks retrieved for Cartography across all thresholds.
- Test 1.8: Verify procedural fallback generation for custom/emergent skills.
- Test 1.9: Verify auto-append of unlocked perks to `player["feats"]` or `player["spells"]`.
- Test 1.10: Verify celebratory announcement banner formatting.

### Tier 2 — Boundary & Corner Cases
- Test 2.1: Boundary crossing at 49 -> 50 (Apprentice trigger).
- Test 2.2: Boundary crossing at 99 -> 100 (Journeyman trigger).
- Test 2.3: Boundary crossing at 249 -> 250 (Adept trigger).
- Test 2.4: Boundary crossing at 499 -> 500 (Master trigger).
- Test 2.5: Boundary crossing at 749 -> 750 (Grandmaster trigger).
- Test 2.6: Boundary crossing at 999 -> 1000 (Transcendence trigger).
- Test 2.7: Cap enforcement at exactly 1000 (no overflow to 1001+).
- Test 2.8: Massive single-turn gain leap (e.g. 1 -> 150) crossing multiple thresholds (50 and 100 awarded simultaneously without duplicates).
- Test 2.9: Negative or zero DC and trivial DC handling.
- Test 2.10: Critical success and failure multipliers at tier boundaries.
- Test 2.11: Empty, corrupt, or legacy skill structures in migration.

### Tier 3 — Cross-Feature Combinations & State Interactions
- Test 3.1: Hybrid system resolution (Canonical skill vs Emergent custom skill in same session).
- Test 3.2: Interaction between skill gain and inventory/encumbrance/stats.
- Test 3.3: Map engine token resolution with consolidated skills and milestone perks.
- Test 3.4: Duplicate milestone prevention (re-reaching threshold does not grant duplicate feat).
- Test 3.5: Multi-skill simultaneous progression across combat turn.

### Tier 4 — Real-World Workload Playtesting Scenarios
- Scenario 4.1: Banki's Combat Run (Nordic Berserker dual-wielding Axe & Hammer, gaining Axe & Hammer mastery over 20 combat turns, unlocking Hewing Edge, Gale Cleave, Concussive Impact, Pneumatic Back-Pick).
- Scenario 4.2: Survivalist & Cartographer Expedition (Setting traps in Washington Borough, exploring sub-level nav meshes, crossing 50/100/250 in Trapping and Cartography).
- Scenario 4.3: Custom Emergent Skill Playtest (Developing "Neural Glitch Weaving", crossing 50 and 100, verifying procedural perk generation and celebration).
- Scenario 4.4: Full Save/Load Roundtrip (Saving player state after multiple milestone unlocks, reloading from JSON, verifying 100% data integrity without data loss).
- Scenario 4.5: Dev Console State Override Simulation (Simulating dev quick-jump and database override, verifying atomic persistence).
