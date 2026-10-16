# Test Infrastructure: Fractured Earth SAO Sandbox V2 Classic Fantasy Overhaul

## 1. Test Philosophy & Design Principles
- **Opaque-Box Requirement-Driven Testing:** Test specifications are derived strictly from authoritative sources (`ORIGINAL_REQUEST.md` 2026-10-16T00:04:06Z and `PROJECT.md` § Architecture & Interface Contracts).
- **Zero-Facade Guarantee:** Tests assert genuine behavioral mechanics, formula thresholds, and structural invariants—never superficial mocking or assertions designed to pass trivially without exercising real logic.
- **Progressive Testability:** Tests execute cleanly under standard Python `unittest` runners without unhandled syntax or runtime errors. Tests for completed baseline mechanics pass immediately, while tests for pending milestone features produce clear, informative failure diagnostics that guide implementation agents.
- **Adversarial Hardening:** Incorporates extreme stat allocations, boundary encumbrance (`STR * 15 lbs` and `STR * 15 + 0.1 lbs`), item durability destruction (`Broken`), size dichotomy physics (Tiny Pixie vs Large Minotaur), and dual-track moral/ethical telemetry conflicts.

---

## 2. Test Architecture: 4-Tier Hierarchy

The master E2E test suite is located at `test_classic_fantasy_e2e.py` and structured into 4 distinct tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 1: FEATURE COVERAGE (26 Tests)                                    │
│  - R1: Expanded Lifestyle Archetypes (6 tests)                         │
│  - R2: Savage Species Lineages & Sci-Fi Purge (6 tests)                │
│  - R3: Hands-On Mini-Dungeon Tutorial System (7 tests)                 │
│  - R4: Classic 10 Base Classes & Observational Evolutions (7 tests)    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ TIER 2: BOUNDARY & CORNER CASES (5 Tests)                              │
│  - Stat boundary allocations (0-stat, 20 max, over-allocation clamp)   │
│  - Encumbrance exact boundary at STR*15 lbs and +0.1 lb threshold     │
│  - Durability broken state penalties (atk_penalty >= 4, broken flags)  │
│  - Level-up edge conditions (negative CON mod, non-zero HP gain)       │
│  - Tiny (20", 15 lbs) vs Large (96", 450 lbs) physical mechanics      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ TIER 3: CROSS-FEATURE COMBINATIONS (5 Tests)                           │
│  - Pixie (Tiny) + Woodsman (Camouflage) + Rogue in Phase I Mini-Dungeon│
│  - Minotaur (Gore) + Gladiator (Crowd Thrill) + Barbarian in Phase II   │
│  - Meadow Nymph (Unearthly Grace) + Courtier + Paladin AC deflection   │
│  - Centaur (Equine build/Trample) + Delver (Echo) + Ranger scouting    │
│  - Dual-Track Telemetry (Holy/Good vs Necrotic/Evil) evolution choices │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│ TIER 4: REAL-WORLD APPLICATION SCENARIOS (5 Tests)                     │
│  - 4.01: Full Creation -> 3-Stage Mini-Dungeons -> Level 3 Graduation   │
│  - 4.02: Fast-Forward Stage Skip -> Safe-Zone State & 8 Canonical Loot │
│  - 4.03: Level 3 to Level 10 Spire Boss Defeat & Eligibility Unlock    │
│  - 4.04: Bespoke Level 10 Evolution Synthesis & Resource Scaling (+25%)│
│  - 4.05: Multi-Tier Epic Journey: Level 20 (+50%) & Level 30 (+100%)   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Test Inventory & Mapping

| Tier | Test ID | Description | Source Requirement | Key System Under Test |
|---|---|---|---|---|
| **Tier 1** | `test_r1_01` | Lifestyle Catalog Count & Required Keys | R1 Lifestyles | `cg.PRESET_LIFESTYLES` (>=24 presets, 8 new keys) |
| **Tier 1** | `test_r1_02` | 20-Point Attribute Balance | R1 Lifestyles | `points` sum == 20 across STR, DEX, CON, INT, WIS, CHA |
| **Tier 1** | `test_r1_03` | 2 Thematic Skill Bonuses (+10 to +20) | R1 Lifestyles | `skill_bonuses` (2 entries, values in [10, 20]) |
| **Tier 1** | `test_r1_04` | Innate Starting Feat/Spell per Preset | R1 Lifestyles | `starting_feat` non-empty description |
| **Tier 1** | `test_r1_05` | Character Generator Lifestyle Application | R1 Lifestyles | `generate_starting_character(lifestyle_key=...)` |
| **Tier 1** | `test_r1_06` | Lifestyle Fallback on Missing/Unknown Key | R1 Lifestyles | Graceful default without exception |
| **Tier 1** | `test_r2_01` | Sci-Fi Races Purged from Creation Menus | R2 Savage Species | `get_character_creation_lineages()` (0 sci-fi) |
| **Tier 1** | `test_r2_02` | Legacy Race Fallback Mapping | R2 Savage Species | `cg.LEGACY_RACE_FALLBACKS` backward compatibility |
| **Tier 1** | `test_r2_03` | D&D 3.0 Pixie Lineage Mechanics | R2 Savage Species | Tiny size (+2 AC, carry 0.5x), flight, invisibility |
| **Tier 1** | `test_r2_04` | Meadow Nymph Unearthly Grace | R2 Savage Species | CHA deflection to AC and saves, Blinding Beauty |
| **Tier 1** | `test_r2_05` | Savage Species Monstrous Lineages | R2 Savage Species | >=25 pure fantasy forms (Minotaur, Gargoyle, Centaur) |
| **Tier 1** | `test_r2_06` | Glenny Chimera Multi-Limb Parity | R2 Savage Species | 4 arms, 2H bow grip, 9 grafts, AC 14/16 |
| **Tier 1** | `test_r3_01` | Mini-Dungeon 13-Room Graph Structure | R3 Mini-Dungeons | `TUTORIAL_MINI_DUNGEON_ROOMS` (Phases 1-3) |
| **Tier 1** | `test_r3_02` | Phase I Encumbrance & Durability Drills | R3 Mini-Dungeons | `calculate_encumbrance`, `apply_durability_damage` |
| **Tier 1** | `test_r3_03` | Phase I Keepsake Relic Resonance | R3 Mini-Dungeons | `activate_personal_relic` room trigger |
| **Tier 1** | `test_r3_04` | Phase II Martial Trials & Sentinel | R3 Mini-Dungeons | Skill progression, parry/charge, Level 2 advance |
| **Tier 1** | `test_r3_05` | Phase III Puzzle, Secret Door & Boss | R3 Mini-Dungeons | Runic puzzle, perception secret door, Apex Warden |
| **Tier 1** | `test_r3_06` | Safe-Zone Graduation & 8 Canonical Loot | R3 Mini-Dungeons | Level 3 graduation in Washington Borough, NJ |
| **Tier 1** | `test_r3_07` | Backward-Compatible Stage Wrapper | R3 Mini-Dungeons | `advance_tutorial_stage` preservation |
| **Tier 1** | `test_r4_01` | Classic 10 Base Classes Roster | R4 Classic Classes | `CLASS_PATHS` (10 classes with HP & resources) |
| **Tier 1** | `test_r4_02` | Class Key Normalization & Aliases | R4 Classic Classes | `normalize_class_key` (warrior->fighter, etc.) |
| **Tier 1** | `test_r4_03` | Levels 1-9 Progression & HP Growth | R4 Classic Classes | `ARCHETYPE_HP_GROWTH` + CON modifier |
| **Tier 1** | `test_r4_04` | Level 10 Evolution Gate (Spire Boss) | R4 Class Evolutions | `check_evolution_eligibility` (Level 10 + Boss) |
| **Tier 1** | `test_r4_05` | Bespoke 3-Option Evolution Synthesis | R4 Class Evolutions | Telemetry-driven synthesis (Synergy, Alignment, Deed) |
| **Tier 1** | `test_r4_06` | Level 20 & 30 Specializations | R4 Class Evolutions | Tier 3 Prestige & Tier 4 Apex Legendary |
| **Tier 1** | `test_r4_07` | Resource Scaling per Evolution Tier | R4 Class Evolutions | `apply_class_evolution` (+25% T2, +50% T3, +100% T4) |
| **Tier 2** | `test_t2_01` | Stat Boundary Allocations | Boundaries | Extreme single stat, 0 stats, over-allocation |
| **Tier 2** | `test_t2_02` | Encumbrance STR*15 Exact Limits | Boundaries | Exact capacity = Heavy Load; +0.1 lb = Overencumbered |
| **Tier 2** | `test_t2_03` | Durability Broken State Penalties | Boundaries | Durability 0 item penalty application |
| **Tier 2** | `test_t2_04` | Level-Up Edge Conditions | Boundaries | Low/negative CON mod, minimum 1 HP gain |
| **Tier 2** | `test_t2_05` | Tiny vs Large Size Mechanics | Boundaries | Pixie (+2 AC, carry 0.5x) vs Minotaur (-1 AC, carry 2.0x) |
| **Tier 3** | `test_t3_01` | Pixie + Woodsman + Rogue Phase I | Cross-Feature | Tiny encumbrance + Nature Camouflage + Daggers |
| **Tier 3** | `test_t3_02` | Minotaur + Gladiator + Barbarian Phase II | Cross-Feature | Large build Gore + Crowd Thrill + Rage resource |
| **Tier 3** | `test_t3_03` | Meadow Nymph + Courtier + Paladin | Cross-Feature | Unearthly Grace CHA deflection AC + Righteous Smite |
| **Tier 3** | `test_t3_04` | Centaur + Delver + Ranger | Cross-Feature | Equine build + Subterranean Echo + Ranged scouting |
| **Tier 3** | `test_t3_05` | Dual-Track Telemetry Synthesis | Cross-Feature | Holy/Compassionate vs Necrotic/Ruthless paths |
| **Tier 4** | `test_t4_01` | Full End-to-End Creation to Graduation | Real-World Scenario | Complete 3-stage mini-dungeon room crawl to Lv 3 |
| **Tier 4** | `test_t4_02` | Fast-Forward Stage Skip & State Sync | Real-World Scenario | Instant skip to Level 3 with persistent 8 items |
| **Tier 4** | `test_t4_03` | Level 3 -> 10 Spire Boss Defeat | Real-World Scenario | Mid-game progression & Sector 1 Spire Boss kill |
| **Tier 4** | `test_t4_04` | Bespoke Evolution Selection & Apply | Real-World Scenario | Synthesize choices, select, verify +25% resource |
| **Tier 4** | `test_t4_05` | Multi-Tier Epic Apotheosis (L20 & L30) | Real-World Scenario | Tier 2 -> Level 20 Tier 3 -> Level 30 Tier 4 Apex |

---

## 4. Test Execution Commands

Run the test suite from the repository root (`h:\Antigravity\SAO Sandbox v2`):

```bash
# Standard unittest execution
python -m unittest test_classic_fantasy_e2e.py

# Verbose execution with per-test reporting
python -m unittest test_classic_fantasy_e2e.py -v

# Standalone direct execution
python test_classic_fantasy_e2e.py

# Targeted execution by requirement tier:
python -m unittest test_classic_fantasy_e2e.TestTier1R1Lifestyles
python -m unittest test_classic_fantasy_e2e.TestTier1R2LineagesAndSciFiPurge
python -m unittest test_classic_fantasy_e2e.TestTier1R3MiniDungeons
python -m unittest test_classic_fantasy_e2e.TestTier1R4Classic10ClassesAndEvolutions
python -m unittest test_classic_fantasy_e2e.TestTier2BoundaryAndCornerCases
python -m unittest test_classic_fantasy_e2e.TestTier3CrossFeatureCombinations
python -m unittest test_classic_fantasy_e2e.TestTier4RealWorldApplicationScenarios

# Regression verification across existing core test suites:
python -m unittest test_tutorial_and_gender.py test_phases_10_to_13_v2.py test_podcast_fixes_1_to_9.py test_audit_all_phases.py test_v2_integration.py
```

---

## 5. Coverage Thresholds & Exit Criteria
- **Total Test Cases:** Exactly 41 automated test cases.
- **Milestone E2E Target:** All 41 tests compile cleanly with 0 unhandled runtime errors (`ERRORS COUNT: 0`).
- **Milestone 1 Target:** All 6 R1 Lifestyle tests (`TestTier1R1Lifestyles`) pass 100%.
- **Milestone 2 Target:** All 6 R2 Lineages & Sci-Fi Purge tests (`TestTier1R2LineagesAndSciFiPurge`) pass 100%.
- **Milestone 3 Target:** All 7 R3 Mini-Dungeon tests (`TestTier1R3MiniDungeons`) pass 100%.
- **Milestone 4 Target:** All 7 R4 Classic 10 Classes tests (`TestTier1R4Classic10ClassesAndEvolutions`) pass 100%.
- **Milestone 5 Exit Criteria:** 100% pass rate across all 41 E2E tests + 100% pass rate on all 5 existing core test suites (34 tests), with zero regressions.
