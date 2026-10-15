"""
test_challenger_m5_2_adversarial_mechanics.py
=============================================
Milestone 5 Challenger 2 Adversarial Stress & Data Fuzzing Suite.
Targeting:
- 10 Generations of Character Succession & Monument of Life Etchings
- Corpse Cache multi-floor stacking, recovery lifecycles & claim idempotency
- Fuzzing malformed, corrupted, empty, or truncated JSON payloads across models.py, repositories.py, migrator.py
- Extreme debuff stacking (-50 AC, DR overrides) and AC/DR sanity recalculation
- Extreme strain capacity overflows (Bio-Tolerance pool depletion & metabolic rejection)
- Dynamic removal of grafted limbs with equipped items attached
- Fused skills relearning cycle (relearn_base_skill from archived_base_skills)
- Rapid multi-session character switching fuzzing (100 rapid switches across 10 sessions)

Authored by: Milestone 5 Challenger 2 (teamwork_preview_challenger_m5_2)
"""

from __future__ import annotations

import copy
import json
import os
import random
import shutil
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if not os.path.exists(os.path.join(PROJECT_ROOT, "backend")):
    PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import delete, func, inspect, select, text
from sqlalchemy.orm import Session

import backend.character_generator as cg
import backend.database as db
from backend.database.adapters import (
    activate_character_session,
    atomic_read_json,
    atomic_write_json,
    load_world,
    mirror_character_to_disk,
    save_game,
)
from backend.database.engine import (
    create_sao_engine,
    db_transaction,
    get_engine,
    init_db,
)
from backend.database.migrator import (
    _safe_load_json,
    migrate_all_disk_saves_to_db,
    migrate_character_file,
    migrate_master_state_file,
    migrate_party_directory,
    migrate_world_state_file,
)
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
from backend.database.repositories import (
    CharacterRepository,
    CorpseCacheRepository,
    MasterStateRepository,
    PartyRepository,
    StagingRepository,
    WorldRepository,
    _ensure_campaign_session,
)
import backend.mechanics as mechanics


class TestChallengerM52AdversarialMechanics(unittest.TestCase):
    """Milestone 5 Challenger 2 Empirical Adversarial Stress & Fuzzing Harness."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="sao_m5_2_stress_")
        cls.db_path = os.path.join(cls.temp_dir, "challenger_m5_2.db")
        cls.db_url = f"sqlite:///{cls.db_path}"
        cls.engine = create_sao_engine(cls.db_url)
        init_db(engine=cls.engine)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.engine.dispose()
        except Exception:
            pass
        if os.path.exists(cls.temp_dir):
            try:
                shutil.rmtree(cls.temp_dir, ignore_errors=True)
            except Exception:
                pass

    def setUp(self):
        pass

    # =========================================================================
    # Test 1: 10 Generations of Character Succession & Monument of Life Etchings
    # =========================================================================
    def test_01_ten_generations_character_succession_and_monument_etchings(self):
        """
        Adversarial test: Simulates 10 sequential generations of character deaths,
        enshrining 10 distinct epitaphs on the Monument of Life, generating 10
        corpse caches across multiple raid floors, and verifying full recovery by
        Generation 11 successor.
        """
        session_id = "sess_10_gen_succession"

        # Initialize base progenitor
        player = {
            "name": "Glenny Progenitor",
            "slug": "glenny_progenitor",
            "level": 10,
            "hp": 325,
            "max_hp": 325,
            "col": 20000,
            "xp": 5000,
            "class": "Chimera Berserker",
            "race": "Troll-Kreen Hybrid",
            "location": "Pohatcong Spire — Floor 1",
            "inventory": [
                {"name": f"Relic Item Gen 1", "rarity": "Rare", "slot": "inventory", "col_value": 500},
                {"name": "Health Potion", "rarity": "Common", "slot": "consumable", "qty": 5},
            ],
            "equipped": {
                "main_hand": "Muramasa Katana",
                "off_hand": "[2H Grip: Muramasa Katana]",
                "lower_main_hand": "Heirloom Hatchet",
                "lower_off_hand": "Riot Shield",
                "chest": "Reinforced Carapace Armor",
            },
        }

        death_sys = mechanics.ensure_death_and_legacy_system(player)
        self.assertEqual(len(death_sys["monument_of_life"]), 0)
        self.assertEqual(len(death_sys["corpse_caches"]), 0)

        expected_epitaphs = []
        expected_cache_ids = []

        # Run 10 generations of succession
        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            for gen in range(1, 11):
                # Set dynamic raid floor for death
                death_floor = (gen % 5) + 1  # Floors 1 through 5
                death_sys["crisis_floor"] = death_floor
                death_sys["crisis_raid_id"] = "pohatcong_spire"
                death_sys["crisis_location"] = f"Pohatcong Spire — Floor {death_floor} Boss Chamber"

                # Give custom item per generation
                player["inventory"].append({
                    "name": f"Generation {gen} Keepsake",
                    "rarity": "Epic",
                    "slot": "inventory",
                    "gen": gen,
                })
                player["col"] = 1000 * gen

                # Trigger Rogue-Lite Legacy Reset
                current_vanguard_name = player["name"]
                successor_name = f"Glenny Dynast {gen + 1}"
                reset_res = mechanics.execute_legacy_reset(player, new_survivor_name=successor_name)

                self.assertTrue(reset_res["success"], f"Legacy reset failed at gen {gen}")
                self.assertTrue(reset_res["legacy_reset_executed"])
                self.assertEqual(player["name"], successor_name)

                epitaph = reset_res["fallen_epitaph"]
                cache = reset_res["corpse_cache"]
                expected_epitaphs.append(epitaph)
                expected_cache_ids.append(cache["cache_id"])

                # Persist character and synchronize corpse caches to DB
                CharacterRepository.save_character(db_sess, player, session_id=session_id)
                CorpseCacheRepository.sync_player_caches(db_sess, session_id, player)

        # Verification in Database:
        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            char_rec = CharacterRepository.get_character_by_slug(db_sess, "glenny_dynast_11", session_id=session_id)
            if not char_rec:
                char_rec = CharacterRepository.get_character_by_slug(db_sess, "glenny_progenitor", session_id=session_id)
            self.assertIsNotNone(char_rec, "Successor character record must exist in DB")

            hydrated_player = CharacterRepository.load_character(db_sess, char_rec.slug, session_id=session_id)
            h_death_sys = hydrated_player.get("death_system", {})

            # 1. Monument of Life has all 10 fallen vanguards etched
            monument = h_death_sys.get("monument_of_life", [])
            self.assertEqual(len(monument), 10, f"Monument of Life must have 10 etched epitaphs, found {len(monument)}")
            for idx, entry in enumerate(monument):
                self.assertEqual(entry["generation"], idx + 1)
                self.assertEqual(entry["status"], "KIA — Polygon Shatter")
                self.assertIn("Floor", entry["death_location"])

            # 2. Corpse Caches table has 10 unrecovered caches
            db_caches = CorpseCacheRepository.get_all_caches(db_sess, session_id, include_recovered=False)
            self.assertEqual(len(db_caches), 10, f"Must have 10 unrecovered CorpseCacheRecords in DB, found {len(db_caches)}")

            # 3. Successor 11 recovers all 10 corpse caches in sequence
            total_col_claimed = 0
            for c_id in expected_cache_ids:
                claim_res = CorpseCacheRepository.claim_cache(db_sess, c_id, session_id=session_id)
                self.assertIsNotNone(claim_res, f"Claim result for {c_id} must not be None")
                self.assertTrue(claim_res["success"], f"Failed to claim corpse cache {c_id}")
                total_col_claimed += claim_res["col"]

                # Idempotency check: claiming already claimed cache must return recovered=True, success=False
                second_claim = CorpseCacheRepository.claim_cache(db_sess, c_id, session_id=session_id)
                self.assertFalse(second_claim["success"], "Second claim must be rejected")
                self.assertTrue(second_claim["recovered"], "Second claim must acknowledge recovered status")
                self.assertEqual(second_claim["col"], 0, "No duplicate Col awarded on second claim")

            # 4. After recovering all 10, unrecovered count is 0, recovered count is 10
            active_caches = CorpseCacheRepository.get_all_caches(db_sess, session_id, include_recovered=False)
            self.assertEqual(len(active_caches), 0, "All caches must now be marked recovered")
            all_caches = CorpseCacheRepository.get_all_caches(db_sess, session_id, include_recovered=True)
            self.assertEqual(len(all_caches), 10, "All 10 caches must still exist in table as recovered")

    # =========================================================================
    # Test 2: Malformed, Corrupted, Empty, and Truncated JSON Payload Fuzzing
    # =========================================================================
    def test_02_malformed_and_truncated_json_payload_resilience(self):
        """
        Adversarial test: Injects malformed, truncated, null, and corrupt JSON into:
        1. CharacterRecord (raw_data_json, stats_json)
        2. EquippedSlotRecord (item_data_json)
        3. AnatomicalGraftRecord (graft_data_json)
        4. ActiveDebuffRecord (debuff_data_json)
        5. SkillMasteryRecord / ArchivedSkillRecord (skill_data_json)
        6. PartyCompanionRecord (companion_data_json, equipped_json, stats_json, skills_json)
        7. MasterGameStateRecord (state_json)
        8. CorpseCacheRecord (inventory_json, gear_json)
        9. Migrator _safe_load_json and migrate_* functions.
        Verifies 100% crash immunity with safe defaults.
        """
        fuzz_payloads = [
            "",
            "   ",
            "{",
            '{"unclosed_key": ',
            '{"truncated_val": "hello',
            "null",
            "12345",
            "[1, 2, 3]",
            "<xml>Not JSON</xml>",
            "\x00\x01\x02\xff",  # Binary garbage
            '{"valid": true, "nested": {"corrupted": [}}',
        ]

        session_id = "sess_fuzz_json"

        # 1. Test Model Deserialization under Malformed Payloads
        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            _ensure_campaign_session(db_sess, session_id)

            for idx, malformed in enumerate(fuzz_payloads):
                char = CharacterRecord(
                    session_id=session_id,
                    slug=f"fuzz_char_{idx}",
                    name=f"Fuzz Char {idx}",
                    raw_data_json=malformed,
                    stats_json=malformed,
                )
                db_sess.add(char)
                db_sess.flush()

                # to_player_dict must NEVER crash
                p_dict = char.to_player_dict()
                self.assertIsInstance(p_dict, dict)
                self.assertEqual(p_dict["name"], f"Fuzz Char {idx}")

                # Child records with malformed payloads attached via relationships
                slot = EquippedSlotRecord(
                    slot_key="main_hand",
                    item_name="Fuzz Blade",
                    item_data_json=malformed,
                )
                graft = AnatomicalGraftRecord(
                    slot_key="spine",
                    graft_name="Fuzz Neural Shunt",
                    unit_strain=1,
                    bio_strain=10,
                    graft_data_json=malformed,
                )
                debuff = ActiveDebuffRecord(
                    debuff_id=f"fuzz_debuff_{idx}",
                    name="Fuzz Rot",
                    ac_penalty=1,
                    debuff_data_json=malformed,
                )
                skill = SkillMasteryRecord(
                    skill_name="Fuzz Slash",
                    mastery_level=50,
                    skill_data_json=malformed,
                )
                arch = ArchivedSkillRecord(
                    skill_name="Fuzz Base",
                    mastery_level=20,
                    skill_data_json=malformed,
                )
                char.equipped_slots.append(slot)
                char.anatomical_grafts.append(graft)
                char.active_debuffs.append(debuff)
                char.skill_masteries.append(skill)
                char.archived_skills.append(arch)
                db_sess.flush()

                # Verify to_dict on all child rows
                self.assertIsInstance(slot.to_dict(), dict)
                self.assertIsInstance(graft.to_dict(), dict)
                self.assertIsInstance(debuff.to_dict(), dict)
                self.assertIsInstance(skill.to_dict(), dict)
                self.assertIsInstance(arch.to_dict(), dict)

                # Reconstruct full character dict with all corrupt child records attached
                full_reconstructed = char.to_player_dict()
                self.assertIsInstance(full_reconstructed, dict)
                self.assertIn("main_hand", full_reconstructed.get("equipped", {}))

                # Companion Record Fuzzing
                comp = PartyCompanionRecord(
                    session_id=session_id,
                    companion_slug=f"fuzz_comp_{idx}",
                    name=f"Companion {idx}",
                    companion_data_json=malformed,
                    equipped_json=malformed,
                    stats_json=malformed,
                    skills_json=malformed,
                )
                db_sess.add(comp)
                db_sess.flush()
                c_dict = comp.to_companion_dict()
                self.assertIsInstance(c_dict, dict)
                self.assertEqual(c_dict["name"], f"Companion {idx}")

                # MasterGameState Record Fuzzing
                mgs = MasterGameStateRecord(
                    session_id=f"{session_id}_mgs_{idx}",
                    campaign_name="FuzzCampaign",
                    turn_number=idx + 1,
                    state_json=malformed,
                )
                _ensure_campaign_session(db_sess, f"{session_id}_mgs_{idx}")
                db_sess.add(mgs)
                db_sess.flush()
                self.assertIsInstance(mgs.to_dict(), dict)
                self.assertIsInstance(mgs.get_visible_room(), dict)
                self.assertIsInstance(mgs.get_action_queue(), list)

                # CorpseCache Record Fuzzing
                cache = CorpseCacheRecord(
                    session_id=session_id,
                    cache_id=f"fuzz_cache_{idx}",
                    fallen_name="Corrupt Fallen",
                    floor_number=idx + 1,
                    inventory_json=malformed,
                    gear_json=malformed,
                )
                db_sess.add(cache)
                db_sess.flush()
                cache_dict = cache.to_cache_dict()
                self.assertIsInstance(cache_dict, dict)
                # Verify keys exist and no exception occurred during deserialization
                self.assertIn("inventory", cache_dict)
                self.assertIn("equipped", cache_dict)
                # Note: to_cache_dict() returns raw parsed JSON (can be scalar if scalar JSON passed)
                self.assertTrue(cache_dict["inventory"] is None or isinstance(cache_dict["inventory"], (list, int, str, dict)))

        # 2. Test Migrator Resilience under Malformed Disk Files
        fuzz_file_dir = os.path.join(self.temp_dir, "fuzz_files")
        os.makedirs(fuzz_file_dir, exist_ok=True)

        for idx, payload in enumerate(fuzz_payloads):
            fpath = os.path.join(fuzz_file_dir, f"corrupt_{idx}.json")
            with open(fpath, "w", encoding="utf-8", errors="ignore") as f:
                f.write(payload)

            # _safe_load_json must safely return None or valid collection without exception
            loaded = _safe_load_json(fpath)
            self.assertTrue(loaded is None or isinstance(loaded, (dict, list)))

            # File migrators must handle corrupt files gracefully returning None
            self.assertIsNone(migrate_master_state_file(fpath, session_id="fuzz_mig", engine=self.engine))
            self.assertIsNone(migrate_world_state_file(fpath, session_id="fuzz_mig", engine=self.engine))
            self.assertIsNone(migrate_character_file(fpath, session_id="fuzz_mig", engine=self.engine))

        # Test directory with all corrupt files
        party_comps = migrate_party_directory(fuzz_file_dir, session_id="fuzz_mig", engine=self.engine)
        self.assertEqual(len(party_comps), 0)

    # =========================================================================
    # Test 3: Fuzzing Equipped Slots, Grafts, and Master State Payloads
    # =========================================================================
    def test_03_fuzzing_equipped_slots_grafts_and_master_state(self):
        """
        Adversarial test: Passes boundary, anomalous, and unusual data structures into
        CharacterRepository.save_character(), PartyRepository.save_party(), and
        MasterStateRepository.save_master_state().
        """
        session_id = "sess_fuzz_structures"

        fuzz_character = {
            "name": "Anomalous Entity",
            "slug": "anomalous_entity",
            "level": "5",  # String level
            "hp": "150",
            "max_hp": "150",
            "col": "9999",
            "equipped": {
                "main_hand": "Muramasa",
                "off_hand": "[2H Grip: Muramasa]",
                "empty_slot": "",
                "none_string": "None",
                "null_slot": None,
                "numeric_item": 12345,
                "weird_case_slot": "Shield Of Light",
            },
            "grafts": {
                "head": {"name": "Ocular Cyberware", "unit_strain": "1", "bio_strain": "10"},
                "spine": {"name": "Neural Web", "strain": 2},
                "tail": "Scorpion Tail Stinger",  # String instead of dict
                "lower_left_arm": {"name": "Hydraulic Arm", "unit_strain": 0, "bio_strain": 0},
            },
            "skills": {
                "One-Handed Sword": {"mastery": "150", "tier": "Journeyman"},
                "Heavy Armor": 75,  # Integer mastery directly
                "Weird Skill": None,
                "[Fusion] Plasma Burst": {"mastery": 500, "is_fusion": True},
            },
            "archived_base_skills": {
                "Firebolt": {"previous_mastery": "100", "fused_into": "[Fusion] Plasma Burst", "was_spell": 1},
                "Lightning Arc": "Consumed in fusion",  # String format
            },
            "active_debuffs": [
                {"name": "Foundry Shred", "ac_penalty": "-4", "dr_override": "0", "turns_remaining": "3"},
                {"name": "Malformed Debuff", "ac_penalty": None, "dr_override": None},
            ],
        }

        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            rec = CharacterRepository.save_character(db_sess, fuzz_character, session_id=session_id)
            self.assertIsNotNone(rec.id)

            # Verify that normalized DB records pruned empty/None slots
            db_slots = {s.slot_key: s.item_name for s in rec.equipped_slots}
            self.assertIn("main_hand", db_slots)
            self.assertIn("off_hand", db_slots)
            self.assertNotIn("empty_slot", db_slots, "Normalized DB slot table must prune empty strings")
            self.assertNotIn("none_string", db_slots, "Normalized DB slot table must prune 'None' strings")
            self.assertNotIn("null_slot", db_slots, "Normalized DB slot table must prune null slots")

            # Verify normalized skill mastery column is numeric
            skill_map = {sm.skill_name: sm for sm in rec.skill_masteries}
            self.assertEqual(skill_map["One-Handed Sword"].mastery_level, 150)
            self.assertEqual(skill_map["Heavy Armor"].mastery_level, 75)

        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            hydrated = CharacterRepository.load_character(db_sess, "anomalous_entity", session_id=session_id)
            self.assertIsNotNone(hydrated)

            # Check equipped normalization
            eq = hydrated.get("equipped", {})
            self.assertIn("main_hand", eq)
            self.assertIn("off_hand", eq)
            self.assertEqual(eq["off_hand"], "[2H Grip: Muramasa]")

            # Check graft normalization
            grafts = hydrated.get("grafts", {})
            self.assertIn("head", grafts)
            self.assertIn("spine", grafts)
            self.assertIn("tail", grafts)
            self.assertEqual(grafts["tail"]["name"], "Scorpion Tail Stinger")

            # Check skills normalization (numeric conversion)
            skills = hydrated.get("skills", {})
            self.assertEqual(int(skills["One-Handed Sword"]["mastery"]), 150)
            self.assertEqual(int(skills["Heavy Armor"]["mastery"]), 75)
            self.assertTrue(skills["[Fusion] Plasma Burst"]["is_fusion"])

            # Check archived skills
            arch = hydrated.get("archived_base_skills", {})
            self.assertIn("Firebolt", arch)
            self.assertIn("Lightning Arc", arch)

            # Check debuffs
            debuffs = hydrated.get("active_debuffs", [])
            self.assertEqual(len(debuffs), 2)

    # =========================================================================
    # Test 4: Extreme Debuff Stacking (-50 AC, DR Override 0 and Negative DR)
    # =========================================================================
    def test_04_extreme_debuff_stacking_and_ac_dr_sanity_recalculation(self):
        """
        Adversarial test: Stacks 10 high-magnitude debuffs (-50 total AC shred,
        DR override 0 and negative DR override).
        Verifies:
        1. AC is clamped strictly to the 5.0 floor (never drops below AC 5).
        2. DR override 0 completely zeros out damage reduction.
        3. Recalculate entity combat stats survives extreme values.
        4. When debuffs expire/prune, character accurately recovers baseline AC 16 / DR 3.
        """
        session_id = "sess_debuff_stacking"

        player = {
            "name": "Glenny Ironclad",
            "slug": "glenny_ironclad",
            "base_ac": 16,
            "ac": 16,
            "base_dr": 3,
            "dr": 3,
            "active_debuffs": [
                # 5x Acid Corrosion (-4 AC each = -20 AC)
                {"debuff_id": f"acid_shred_{i}", "name": f"Acid Shred {i}", "ac_penalty": -4, "turns_remaining": 3}
                for i in range(5)
            ] + [
                # 5x Slag Cracker (-6 AC each = -30 AC, with Corrosive Slag-Shatter DR 0 override)
                {"debuff_id": f"slag_crack_{i}", "name": f"Slag Cracker {i}", "ac_penalty": -6, "dr_override": 0, "turns_remaining": 2}
                for i in range(5)
            ],
        }

        # 1. Total AC penalty is -50!
        # Base AC 16 - 50 = -34. Clamped to 5.
        mechanics.recalculate_entity_combat_stats(player)
        self.assertEqual(player["ac"], 5, f"Extreme AC penalty must be clamped at floor 5, got {player['ac']}")
        self.assertEqual(player["dr"], 0, f"DR must be overridden to 0 by Slag-Shatter, got {player['dr']}")

        # 2. Persist to Relational DB
        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            CharacterRepository.save_character(db_sess, player, session_id=session_id)

        # 3. Reload from DB in fresh transaction and verify hydration recalculation
        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            reloaded = CharacterRepository.load_character(db_sess, "glenny_ironclad", session_id=session_id)
            self.assertEqual(reloaded["ac"], 5, f"Hydrated AC must remain clamped at floor 5, got {reloaded['ac']}")
            self.assertEqual(reloaded["dr"], 0, f"Hydrated DR must remain 0, got {reloaded['dr']}")
            self.assertEqual(len(reloaded["active_debuffs"]), 10)

        # 4. Now test negative DR override (e.g. Vulnerability Curse DR -5)
        player["active_debuffs"].append({
            "debuff_id": "vulnerability_curse",
            "name": "Vulnerability Curse",
            "ac_penalty": 0,
            "dr_override": -5,
            "turns_remaining": 1,
        })
        mechanics.recalculate_entity_combat_stats(player)
        self.assertEqual(player["dr"], -5, "Negative DR override should be supported for damage amplification")

        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            CharacterRepository.save_character(db_sess, player, session_id=session_id)

        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            reloaded2 = CharacterRepository.load_character(db_sess, "glenny_ironclad", session_id=session_id)
            self.assertEqual(reloaded2["dr"], -5)

        # 5. Expire all debuffs -> Full Recovery to Base AC 16 and Base DR 3
        player["active_debuffs"] = []
        mechanics.recalculate_entity_combat_stats(player)
        self.assertEqual(player["ac"], 16, "AC must recover to base 16 after all debuffs expire")
        self.assertEqual(player["dr"], 3, "DR must recover to base 3 after all debuffs expire")

        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            CharacterRepository.save_character(db_sess, player, session_id=session_id)

        # Verify in a fresh transaction that debuffs are cleared and AC/DR recover fully
        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            recovered = CharacterRepository.load_character(db_sess, "glenny_ironclad", session_id=session_id)
            self.assertEqual(recovered["ac"], 16)
            self.assertEqual(recovered["dr"], 3)
            self.assertEqual(len(recovered["active_debuffs"]), 0)

    # =========================================================================
    # Test 5: Extreme Strain Capacity Overflows (Bio-Tolerance Pool & Unit Strain)
    # =========================================================================
    def test_05_extreme_strain_capacity_overflows_and_metabolic_rejection(self):
        """
        Adversarial test: Overloads a character with extreme grafts exceeding both:
        - Unit Strain Capacity (Cap 4 -> Current 12 -> Overflow 8 units)
        - Bio-Tolerance Pool (Pool 35 -> Current 120 -> Overflow 85 points)
        Verifies:
        1. Metabolic rejection telemetry triggers.
        2. HP drain calculation matches maximum penalty: max(85*2, 8*6) = 170 HP.
        3. Database persistence preserves all 8 overloaded graft records.
        4. Rehydrated character recomputes exact same strain telemetry.
        """
        session_id = "sess_strain_overflow"

        # Glenny baseline: STR 18, DEX 15, CON 16, Level 1.
        # Unit Strain Cap = 3 (CON mod) + 0 (Level // 2) + 1 (Secondary Ganglia) = 4
        # Bio-Tolerance Pool = (16 * 2) + (1 * 3) = 35
        player = {
            "name": "Glenny Overloaded",
            "slug": "glenny_overloaded",
            "level": 1,
            "stats": {"STR": 18, "DEX": 15, "CON": 16, "INT": 10, "WIS": 12, "CHA": 8},
            "race": "Troll-Kreen Hybrid",
            "grafts": {
                # 4 grafts with unit_strain=2, strain=2 (20 bio-strain)
                "head": {"name": "Reinforced Chitin Cranium", "strain": 2, "unit_strain": 2, "bio_strain": 20},
                "spine": {"name": "Synthetic Neural Backbone", "strain": 2, "unit_strain": 2, "bio_strain": 20},
                "torso": {"name": "Adamantine Rib Cage", "strain": 2, "unit_strain": 2, "bio_strain": 20},
                "left_arm": {"name": "Hydraulic Crusher Arm", "strain": 2, "unit_strain": 2, "bio_strain": 20},
                # 4 grafts with unit_strain=1, strain=1 (10 bio-strain)
                "right_arm": {"name": "Pneumatic Piston Arm", "strain": 1, "unit_strain": 1, "bio_strain": 10},
                "lower_left_arm": {"name": "Secondary Ganglia Unit", "strain": 1, "unit_strain": 1, "bio_strain": 10},
                "lower_right_arm": {"name": "Auxiliary Blade Limb", "strain": 1, "unit_strain": 1, "bio_strain": 10},
                "tail": {"name": "Bio-Mechanical Scorpion Tail", "strain": 1, "unit_strain": 1, "bio_strain": 10},
            },
        }

        # Calculate initial strain
        strain_data = mechanics.calculate_player_strain(player)
        self.assertEqual(strain_data["max_unit_strain"], 4, "Glenny max unit strain must be 4")
        self.assertEqual(strain_data["current_unit_strain"], 12, "Current unit strain must be 12")
        self.assertEqual(strain_data["max_strain"], 35, "Max bio-tolerance pool must be 35")
        self.assertEqual(strain_data["current_strain"], 120, "Current bio-strain must be 120")

        # Verify rejection status
        rejection = strain_data["rejection"]
        self.assertTrue(rejection["is_rejecting"], "System must be in Metabolic Rejection")
        self.assertEqual(rejection["unit_overflow"], 8, "Unit overflow must be 8")
        self.assertEqual(rejection["overflow"], 85, "Bio-strain overflow must be 85")
        # hp_drain = max(85 * 2, 8 * 6) = 170
        self.assertEqual(rejection["hp_drain"], 170, "HP drain must be 170 points")

        # Persist to relational DB
        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            rec = CharacterRepository.save_character(db_sess, player, session_id=session_id)
            self.assertEqual(len(rec.anatomical_grafts), 8)

        # Reload from relational DB in fresh transaction and verify 100% telemetry fidelity
        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            hydrated = CharacterRepository.load_character(db_sess, "glenny_overloaded", session_id=session_id)
            h_strain = mechanics.calculate_player_strain(hydrated)

            self.assertEqual(h_strain["max_unit_strain"], 4)
            self.assertEqual(h_strain["current_unit_strain"], 12)
            self.assertEqual(h_strain["max_strain"], 35)
            self.assertEqual(h_strain["current_strain"], 120)
            self.assertTrue(h_strain["is_overloaded"])
            self.assertEqual(h_strain["rejection"]["hp_drain"], 170)

    # =========================================================================
    # Test 6: Dynamic Removal of Grafted Limbs with Equipped Items Attached
    # =========================================================================
    def test_06_dynamic_removal_of_grafted_limbs_with_equipped_items(self):
        """
        Adversarial test:
        1. Installs lower_left_arm and lower_right_arm grafts on 2-armed character.
        2. Equips Muramasa + 2H Grip marker in upper arms, Wood-Axe and Buckler in lower arms.
        3. Base AC is 14; with Buckler in lower_off_hand AC is 16.
        4. Dynamically excises lower arms and prunes lower limb equipment.
        5. Verifies database deletes graft rows and equipped slot rows.
        6. Rehydrates and verifies AC accurately falls back to 14.
        """
        session_id = "sess_graft_excision"

        player = {
            "name": "Banki Chimera",
            "slug": "banki_chimera",
            "level": 3,
            "stats": {"STR": 16, "DEX": 14, "CON": 14, "INT": 16, "WIS": 12, "CHA": 10},
            "race": "Pure Human",
            "grafts": {
                "lower_left_arm": {"name": "Grafted Troll Arm L", "unit_strain": 1, "bio_strain": 10},
                "lower_right_arm": {"name": "Grafted Troll Arm R", "unit_strain": 1, "bio_strain": 10},
            },
            "equipped": {
                "chest": "Threadbare Scavenger Tunic",
                "main_hand": "Muramasa Katana",
                "off_hand": "[2H Grip: Muramasa Katana]",
                "lower_main_hand": "Chipped Wood-Axe",
                "lower_off_hand": "Wooden Buckler",
            },
        }

        # 4-armed with buckler in lower_off_hand -> AC 14
        ac_4armed = mechanics.calculate_ac(player)

        # 1. Save 4-armed state to DB
        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            CharacterRepository.save_character(db_sess, player, session_id=session_id)

        # Verify DB has 2 grafts and 5 equipped slots
        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            char_rec = CharacterRepository.get_character_by_slug(db_sess, "banki_chimera", session_id=session_id)
            self.assertEqual(len(char_rec.anatomical_grafts), 2)
            self.assertEqual(len(char_rec.equipped_slots), 5)

        # 2. Dynamic Excision: Remove lower limbs from grafts and prune equipped
        player["grafts"].pop("lower_left_arm")
        player["grafts"].pop("lower_right_arm")
        player["equipped"].pop("lower_main_hand")
        player["equipped"].pop("lower_off_hand")

        ac_excision = mechanics.calculate_ac(player)
        self.assertEqual(ac_4armed - ac_excision, 2, "AC must drop by 2 when buckler-bearing lower arm is removed")

        # 3. Save excised state to DB
        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            CharacterRepository.save_character(db_sess, player, session_id=session_id)

        # 4. Verify DB pruned both grafts and both lower hand slots
        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            char_rec = CharacterRepository.get_character_by_slug(db_sess, "banki_chimera", session_id=session_id)
            self.assertEqual(len(char_rec.anatomical_grafts), 0, "All graft rows must be deleted from DB")
            slot_keys = {s.slot_key for s in char_rec.equipped_slots}
            self.assertNotIn("lower_main_hand", slot_keys, "lower_main_hand must be pruned from DB")
            self.assertNotIn("lower_off_hand", slot_keys, "lower_off_hand must be pruned from DB")
            self.assertIn("main_hand", slot_keys)
            self.assertIn("off_hand", slot_keys)

            # Reload and verify AC on hydrated player
            hydrated = CharacterRepository.load_character(db_sess, "banki_chimera", session_id=session_id)
            h_ac = mechanics.calculate_ac(hydrated)
            self.assertEqual(h_ac, ac_excision)

    # =========================================================================
    # Test 7: Fused Skills Relearning Cycle (relearn_base_skill from archived)
    # =========================================================================
    def test_07_fused_skills_relearning_and_progression_cycle(self):
        """
        Adversarial test:
        1. Fuses 'Battleaxe Mastery' (500) and 'Earth Tremor Hex' (500) into '[Fusion] Seismic Cleave'.
        2. Archives foundational skills in archived_base_skills.
        3. Persists to relational DB.
        4. Relearns 'Battleaxe Mastery' at Rank 1 (Novice) via relearn_base_skill().
        5. Persists and verifies DB contains BOTH active [Fusion] skill AND active relearned base skill.
        6. Advances relearned skill from Rank 1 to 250 (Journeyman milestone threshold).
        7. Verifies 100% database persistence of relearned milestone progress.
        """
        session_id = "sess_skill_fusion_relearn"

        player = {
            "name": "Banki Warrior",
            "slug": "banki_warrior",
            "level": 5,
            "skills": {
                "[Fusion] Seismic Cleave": {
                    "mastery": 500,
                    "tier": "Adept",
                    "is_fusion": True,
                    "description": "Fusion of Battleaxe Mastery and Earth Tremor Hex.",
                }
            },
            "archived_base_skills": {
                "Battleaxe Mastery": {
                    "previous_mastery": 500,
                    "archived_reason": "Consumed in Ability Fusion into [Fusion] Seismic Cleave",
                    "fused_into": "[Fusion] Seismic Cleave",
                    "was_spell": False,
                    "description": "Mastery of heavy axes.",
                },
                "Earth Tremor Hex": {
                    "previous_mastery": 500,
                    "archived_reason": "Consumed in Ability Fusion into [Fusion] Seismic Cleave",
                    "fused_into": "[Fusion] Seismic Cleave",
                    "was_spell": True,
                    "description": "Geokinetic magical hex.",
                },
            },
        }

        # 1. Save fused state to DB
        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            CharacterRepository.save_character(db_sess, player, session_id=session_id)

        # 2. Verify DB rows
        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            char_rec = CharacterRepository.get_character_by_slug(db_sess, "banki_warrior", session_id=session_id)
            self.assertEqual(len(char_rec.skill_masteries), 1)
            self.assertEqual(char_rec.skill_masteries[0].skill_name, "[Fusion] Seismic Cleave")
            self.assertTrue(char_rec.skill_masteries[0].is_fusion)
            self.assertEqual(len(char_rec.archived_skills), 2)

        # 3. Relearn Battleaxe Mastery at Rank 1
        relearn_res = mechanics.relearn_base_skill(player, "Battleaxe Mastery", starting_mastery=1)
        self.assertTrue(relearn_res["success"])
        self.assertEqual(relearn_res["mastery"], 1)
        self.assertIn("Battleaxe Mastery", player["skills"])
        self.assertIn("[Fusion] Seismic Cleave", player["skills"])

        # 4. Save relearned state to DB
        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            CharacterRepository.save_character(db_sess, player, session_id=session_id)

        # 5. Verify DB now has 2 active skills and archived skill remains
        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            hydrated = CharacterRepository.load_character(db_sess, "banki_warrior", session_id=session_id)
            h_skills = hydrated["skills"]
            self.assertIn("[Fusion] Seismic Cleave", h_skills)
            self.assertIn("Battleaxe Mastery", h_skills)
            self.assertEqual(h_skills["Battleaxe Mastery"]["mastery"], 1)
            self.assertEqual(h_skills["Battleaxe Mastery"]["tier"], "Novice")
            self.assertEqual(len(hydrated["archived_base_skills"]), 2)

        # 6. Train Battleaxe Mastery from 1 to 250 (Journeyman milestone threshold)
        player["skills"]["Battleaxe Mastery"]["mastery"] = 250
        player["skills"]["Battleaxe Mastery"]["tier"] = "Journeyman"
        player["skills"]["Battleaxe Mastery"]["milestones_unlocked"] = [50, 100, 250]

        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            CharacterRepository.save_character(db_sess, player, session_id=session_id)

        with db_transaction(session_id=session_id, engine=self.engine) as db_sess:
            final_char = CharacterRepository.load_character(db_sess, "banki_warrior", session_id=session_id)
            bm = final_char["skills"]["Battleaxe Mastery"]
            self.assertEqual(bm["mastery"], 250)
            self.assertEqual(bm["tier"], "Journeyman")
            self.assertIn(250, bm.get("milestones_unlocked", []))

    # =========================================================================
    # Test 8: Rapid Multi-Session Character Switching Fuzzing (100 Switches, 10 Sessions)
    # =========================================================================
    def test_08_rapid_multi_session_character_switching_100_switches_across_10_sessions(self):
        """
        Adversarial stress:
        - 10 distinct player sessions (sess_rapid_0 to sess_rapid_9).
        - 5 distinct character archetypes.
        - Spawns concurrent threads executing 100 rapid interleaved activate_character_session()
          and save_game() operations.
        - Verifies:
          1. 100% completion with zero unhandled exceptions.
          2. Zero cross-session contamination (session isolation).
          3. Zero SQLite lock timeouts or concurrency crashes.
          4. Complete data integrity under rapid session switching.
        """
        num_sessions = 10
        num_switches = 100
        session_ids = [f"sess_rapid_{i}" for i in range(num_sessions)]

        character_archetypes = [
            {"slug": "glenny", "name": "Glenny", "class": "Chimera Berserker", "level": 1, "col": 100},
            {"slug": "banki", "name": "Banki", "class": "Arcane Smith", "level": 3, "col": 500},
            {"slug": "ren_subagent", "name": "Ren Subagent", "class": "Tactical Scout", "level": 2, "col": 250},
            {"slug": "mantid_stalker", "name": "Mantid Stalker", "class": "Assassin", "level": 4, "col": 800},
            {"slug": "cyborg_paladin", "name": "Cyborg Paladin", "class": "Crusader", "level": 5, "col": 1200},
        ]

        # Seed all characters in all sessions
        for s_id in session_ids:
            with db_transaction(session_id=s_id, engine=self.engine) as db_sess:
                _ensure_campaign_session(db_sess, s_id)
                for arch in character_archetypes:
                    c_data = copy.deepcopy(arch)
                    # Unique Col to identify session and archetype
                    c_data["col"] = arch["col"] + (int(s_id.split("_")[-1]) * 1000)
                    CharacterRepository.save_character(db_sess, c_data, session_id=s_id)

        errors = []
        successful_switches = 0
        lock = threading.Lock()

        def worker_task(switch_idx: int):
            nonlocal successful_switches
            target_session = random.choice(session_ids)
            target_arch = random.choice(character_archetypes)
            sess_idx = int(target_session.split("_")[-1])

            try:
                # 1. Activate character session
                active_state = activate_character_session(
                    target_arch["slug"],
                    session_id=target_session,
                    engine=self.engine,
                )
                player = active_state.get("player")
                if not player:
                    raise ValueError(f"Player {target_arch['slug']} not found in {target_session}")

                # Verify session isolation: player col must match session-specific initial Col + mutations
                base_expected_col = target_arch["col"] + (sess_idx * 1000)
                if player["col"] < base_expected_col:
                    raise AssertionError(f"Session bleed detected: expected col >= {base_expected_col}, got {player['col']} in {target_session}")

                # 2. Mutate state slightly and persist inside session
                player["col"] += 1
                with db_transaction(session_id=target_session, engine=self.engine) as db_sess:
                    CharacterRepository.save_character(db_sess, player, session_id=target_session)

                with lock:
                    successful_switches += 1
            except Exception as exc:
                with lock:
                    errors.append(f"Switch {switch_idx} ({target_session}/{target_arch['slug']}): {exc}")

        # Execute 100 rapid switches across 10 concurrent threads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker_task, i) for i in range(num_switches)]
            for f in as_completed(futures):
                pass

        self.assertEqual(len(errors), 0, f"Encountered errors during rapid session switches:\n" + "\n".join(errors[:10]))
        self.assertEqual(successful_switches, num_switches, f"Expected {num_switches} successful switches, completed {successful_switches}")

        # Final verification: verify each session has its expected distinct Col values
        for s_id in session_ids:
            sess_idx = int(s_id.split("_")[-1])
            with db_transaction(session_id=s_id, engine=self.engine) as db_sess:
                for arch in character_archetypes:
                    c = CharacterRepository.load_character(db_sess, arch["slug"], session_id=s_id)
                    self.assertIsNotNone(c)
                    base_expected_col = arch["col"] + (sess_idx * 1000)
                    self.assertGreaterEqual(c["col"], base_expected_col)


if __name__ == "__main__":
    unittest.main(verbosity=2)
