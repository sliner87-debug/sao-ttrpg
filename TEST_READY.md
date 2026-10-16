# TEST READY — Fractured Earth SAO Sandbox V2 Classic Fantasy Framework

**Published Date:** 2026-10-16T00:32:00Z  
**Author:** E2E Testing Track Test Writer (`teamwork_preview_test_writer_classic_1`)  
**Status:** **READY FOR PROGRESSIVE IMPLEMENTATION VERIFICATION**  
**Project Root:** `h:\Antigravity\SAO Sandbox v2`  
**Master E2E Test Suite:** `test_classic_fantasy_e2e.py`  
**Test Infrastructure Specification:** `TEST_INFRA.md`  

---

## 1. Executive Summary

The comprehensive, opaque-box, requirement-driven E2E test suite for the Fractured Earth SAO Sandbox V2 Classic Fantasy Overhaul (`ORIGINAL_REQUEST.md` 2026-10-16T00:04:06Z Request) has been designed, authored, and verified.

- **Total Test Cases:** 41 automated tests structured across Tiers 1–4.
- **Test Runner Reliability:** 100% clean execution under standard Python `unittest` runner with **ZERO unhandled crashes or syntax errors** (`ERRORS COUNT: 0`).
- **Baseline Parity:** 16 tests pass immediately, confirming Glenny 4-armed chimera parity, basic level progression, durability formulas, keepsake relic resonance, and stage graduation adapters.
- **Progressive Testability:** 25 tests fail with pinpoint assertion diagnostics, establishing the authoritative criteria for Milestones 1 through 4.

---

## 2. Test Execution Baseline Results

```
Command: python -m unittest test_classic_fantasy_e2e.py
Duration: 1.179 seconds
Status: FAILED (failures=25, errors=0)
Total Tests: 41
Passed: 16
Failed: 25
```

### Test Results Breakdown by Tier and Requirement

| Category | Suite Class | Total Tests | Pass | Fail | Milestone Target | Status |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Tier 1: R1 Lifestyles** | `TestTier1R1Lifestyles` | 6 | 1 | 5 | Milestone 1 | Awaiting M1 Worker |
| **Tier 1: R2 Lineages & Purge** | `TestTier1R2LineagesAndSciFiPurge` | 6 | 1 | 5 | Milestone 2 | Awaiting M2 Worker |
| **Tier 1: R3 Mini-Dungeons** | `TestTier1R3MiniDungeons` | 7 | 6 | 1 | Milestone 3 | Awaiting M3 Worker |
| **Tier 1: R4 Classic 10 Classes** | `TestTier1R4Classic10ClassesAndEvolutions` | 7 | 2 | 5 | Milestone 4 | Awaiting M4 Worker |
| **Tier 2: Boundary Cases** | `TestTier2BoundaryAndCornerCases` | 5 | 4 | 1 | Milestones 1-4 | Awaiting M2 Worker (Tiny size) |
| **Tier 3: Cross-Feature** | `TestTier3CrossFeatureCombinations` | 5 | 0 | 5 | Milestones 1-4 | Awaiting M1-M4 Integration |
| **Tier 4: Real-World Scenarios** | `TestTier4RealWorldApplicationScenarios` | 5 | 2 | 3 | Milestone 5 | Awaiting Full Integration |
| **Total** | | **41** | **16** | **25** | | **Suite Ready** |

---

## 3. Discovered Implementation Gaps & Escalations

The test suite forensically identifies the exact missing functionality across each requirement to be resolved by the respective milestone implementation agents:

### Requirement R1: Expanded Lifestyle Archetypes (Milestone 1)
1. **Catalog Expansion:** `cg.PRESET_LIFESTYLES` contains 18 presets; must be expanded to at least 24 (proposing 26) adding `woodsman`, `monastery_ascetic`, `hearth_apothecary`, `dungeon_delver`, `arena_gladiator`, `courtier_emissary`, `blacksmith_apprentice`, `archive_scribe`.
2. **Skill Bonuses & Feats:** Presets currently define only `points`. Must add `skill_bonuses` (2 thematic skills granting +10 to +20 starting mastery) and `starting_feat` (descriptive talent string).
3. **Generator Ingress:** `cg.generate_starting_character()` does not accept `lifestyle_key`. Must add `lifestyle_key: Optional[str] = None` and apply starting skill bonuses and starting feats to the player dictionary.

### Requirement R2: Pure Fantasy & Savage Species Lineages (Milestone 2)
1. **Sci-Fi Purge:** 6 modern/sci-fi races (`neuromancer_cyborg`, `mantid_insectoid`, `nanite_host`, `void_walker`, `synthetic_android`, `phrenic_human`) are exposed in character creation. Must implement `get_character_creation_lineages()` to filter them out of character creation menus while preserving them in `RACIAL_LINEAGES`.
2. **Backward Compatibility Fallbacks:** Define `LEGACY_RACE_FALLBACKS` dictionary mapping purged races to pure fantasy analogues.
3. **Fey Lineages:** Implement `pixie_fey_sprite` (Tiny size with +2 AC size mod and 0.5x carry mult, natural 40ft flight, permanent Greater Invisibility, DR 5/cold iron, Pixie Dust) and `meadow_nymph_fey` (Unearthly Grace CHA deflection AC/saves, Blinding Beauty).
4. **Savage Species Monstrous Lineages:** Verify at least 25 pure fantasy lineages including Minotaur (Natural Cunning, Gore charge, Large size), Gargoyle (Stone hide DR, flight), Centaur (Large equine build, 40ft speed, Trample), Feral Troll, and Medusa.

### Requirement R3: Hands-On Mini-Dungeon Tutorial System (Milestone 3)
1. **13-Room Graph Engine:** Implement `TUTORIAL_MINI_DUNGEON_ROOMS` defining 13 rooms across Phase I (4 rooms: Telemetry, Gravity Chasm, Rust-Mist Adit, Relic Sanctum), Phase II (4 rooms: Proving Ground, Parry & Charge Arena, Multi-Limb Annex, Triage Infirmary), and Phase III (5 rooms: High Ingress, Puzzle Vault, Secret Scriptorium, Construct Foundry, Apex Warden Lair).
2. **Mini-Dungeon Navigation:** Implement `advance_tutorial_mini_dungeon()` for room-by-room navigation and trial execution while maintaining 100% backward compatibility for `advance_tutorial_stage()`.

### Requirement R4: Full Classic 10 Base Classes & Observational Evolutions (Milestone 4)
1. **Classic 10 Roster:** Add `fighter`, `wizard`, `rogue`, `paladin`, `druid`, `bard`, `barbarian`, `monk` to `CLASS_PATHS`, `CLASS_WEAPONS`, `CLASS_FEATS_TREE`, and `ARCHETYPE_HP_GROWTH`.
2. **Class Key Normalization:** Update `normalize_class_key()` to map `warrior`/`vanguard` -> `fighter`, `mage` -> `wizard`, `thief` -> `rogue`, while retaining `engineer`, `psion`, `pathless`.
3. **Level 10 Bespoke Synthesis:** Update `generate_curated_evolutions()` to output exactly 3 bespoke options synthesized from dual-track behavioral telemetry:
   - Option 1: Discipline & Weapon Synergy
   - Option 2: Dual-Track Moral & Ethical Alignment (Good vs Evil vs Pragmatic)
   - Option 3: Unique Deed / Relic Anchor / Monstrous Lineage
4. **Level 20 & 30 Progression:** Correct `check_evolution_eligibility()` to check Level 20 (fixing legacy Level 25 check) and Level 30, offering 3 Tier 3 prestige branches and 3 Tier 4 apex legendary evolutions.
5. **Combat Resource Scaling:** Update `apply_class_evolution()` to scale combat resources (+25% Tier 2, +50% Tier 3, +100% Tier 4).

---

## 4. How to Run the Tests

```bash
# Execute master E2E test suite
python -m unittest test_classic_fantasy_e2e.py

# Verbose output
python -m unittest test_classic_fantasy_e2e.py -v

# Regression validation against existing 5 core test suites (34 tests)
python -m unittest test_tutorial_and_gender.py test_phases_10_to_13_v2.py test_podcast_fixes_1_to_9.py test_audit_all_phases.py test_v2_integration.py
```

All 5 existing core test suites continue to pass at **100% (34/34 tests, 0 failures)**.
