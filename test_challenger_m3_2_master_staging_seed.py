"""
test_challenger_m3_2_master_staging_seed.py
===========================================
Milestone 3 Challenger 2 Empirical Adversarial Stress Test Suite.

Focus Areas:
1. Concurrent Staging Queue & Turn Resolution across 10 threads (Session Isolation).
2. Master State Non-Destructive Deep Merge (Preserving sector, turn_number, staging).
3. Concurrent Same-Session Staging Race Condition Stress.
4. Seed Migrator Idempotency across 3 Consecutive Runs (0 row increase, 0 duplicate chat messages).
5. Mechanical Parity Verification after 3 Consecutive Migration Runs (Glenny AC 14/16, Strain 4, Banki skills).
6. Staging Ground Disk Mirroring Session Gating.
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from typing import Any, Dict, List

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

import backend.database as db
from backend.database.engine import (
    create_sao_engine,
    db_transaction,
    get_engine,
    init_db,
)
from backend.database.migrator import (
    migrate_all_disk_saves_to_db,
    verify_migration_fidelity,
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
from backend.database.repositories import (
    CharacterRepository,
    MasterStateRepository,
    PartyRepository,
    StagingRepository,
    WorldRepository,
)
import backend.mechanics as mechanics


class TestM3Challenger2MasterStagingSeed(unittest.TestCase):
    """Adversarial stress testing suite for Milestone 3 Challenger 2."""

    @classmethod
    def setUpClass(cls):
        cls.test_db_path = os.path.abspath("test_m3_challenger_stress.db")
        cls.test_db_url = f"sqlite:///{cls.test_db_path}"
        cls._cleanup_test_db(cls.test_db_path)
        cls.engine = create_sao_engine(cls.test_db_url)
        init_db(cls.engine)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "engine"):
            cls.engine.dispose()
        cls._cleanup_test_db(cls.test_db_path)

    @classmethod
    def _cleanup_test_db(cls, db_path: str):
        for ext in ["", "-wal", "-shm"]:
            f = f"{db_path}{ext}"
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    # ==========================================================================
    # 1. Concurrent Staging Queue & Turn Resolution Across 10 Threads
    # ==========================================================================
    def test_01_concurrent_staging_10_threads_turn_resolution(self):
        """
        Spawn 10 concurrent threads resolving turns and updating staging queues
        across separate sessions. Verify zero cross-session turn interference or
        room contamination.
        """
        num_threads = 10
        turns_per_thread = 5
        barrier = threading.Barrier(num_threads)
        errors: List[Exception] = []

        def worker(thread_idx: int):
            session_id = f"stress_thread_{thread_idx}"
            try:
                # Synchronize start across all 10 threads
                barrier.wait(timeout=10.0)

                for turn in range(1, turns_per_thread + 1):
                    with db_transaction(session_id=session_id, engine=self.engine) as session:
                        # 1. Queue actions unique to this thread and turn
                        action_payload = [
                            {
                                "actor": f"actor_t{thread_idx}_turn{turn}_a1",
                                "action": f"cast_spell_t{thread_idx}",
                                "priority": turn,
                            },
                            {
                                "actor": f"actor_t{thread_idx}_turn{turn}_a2",
                                "action": "dash",
                                "priority": turn,
                            },
                        ]
                        StagingRepository.save_action_queue(session, action_payload, session_id=session_id)

                        # 2. Save visible room unique to this thread and turn
                        room_payload = {
                            "room_id": f"room_t{thread_idx}_turn{turn}",
                            "hazard": f"hazard_t{thread_idx}",
                            "environmental_effects": [f"mist_intensity_{thread_idx}"],
                            "turn": turn,
                        }
                        StagingRepository.save_visible_room(session, room_payload, session_id=session_id)

                    # 3. Read back in fresh transaction and assert session isolation
                    with db_transaction(session_id=session_id, engine=self.engine) as session:
                        loaded_room = StagingRepository.load_visible_room(session, session_id=session_id)
                        loaded_queue = StagingRepository.load_action_queue(session, session_id=session_id)

                        if loaded_room.get("room_id") != f"room_t{thread_idx}_turn{turn}":
                            raise AssertionError(
                                f"Room contamination in {session_id} turn {turn}: got {loaded_room.get('room_id')}"
                            )
                        if loaded_room.get("hazard") != f"hazard_t{thread_idx}":
                            raise AssertionError(
                                f"Hazard contamination in {session_id} turn {turn}: got {loaded_room.get('hazard')}"
                            )
                        if len(loaded_queue) != 2:
                            raise AssertionError(
                                f"Queue size mismatch in {session_id} turn {turn}: expected 2, got {len(loaded_queue)}"
                            )
                        if loaded_queue[0].get("actor") != f"actor_t{thread_idx}_turn{turn}_a1":
                            raise AssertionError(
                                f"Queue contamination in {session_id} turn {turn}: got {loaded_queue[0].get('actor')}"
                            )

                    # 4. Turn resolution: advance master state turn & clear action queue
                    with db_transaction(session_id=session_id, engine=self.engine) as session:
                        MasterStateRepository.save_master_state(
                            session,
                            {"turn_number": turn, "sector": 100 + thread_idx},
                            session_id=session_id,
                        )
                        StagingRepository.clear_action_queue(session, session_id=session_id)

                    # 5. Verify action queue is empty post-resolution
                    with db_transaction(session_id=session_id, engine=self.engine) as session:
                        post_queue = StagingRepository.load_action_queue(session, session_id=session_id)
                        if post_queue != []:
                            raise AssertionError(
                                f"Queue not cleared in {session_id} turn {turn}: {post_queue}"
                            )

            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30.0)

        # Assert zero errors during concurrent execution
        self.assertEqual(errors, [], f"Thread errors encountered: {errors}")

        # Post-concurrency full state audit across all 10 sessions
        with db_transaction(session_id="audit", engine=self.engine) as session:
            for thread_idx in range(num_threads):
                session_id = f"stress_thread_{thread_idx}"
                m_state = MasterStateRepository.load_master_state(session, session_id=session_id)
                v_room = StagingRepository.load_visible_room(session, session_id=session_id)
                a_queue = StagingRepository.load_action_queue(session, session_id=session_id)

                self.assertEqual(m_state.get("turn_number"), turns_per_thread)
                self.assertEqual(m_state.get("sector"), 100 + thread_idx)
                self.assertEqual(v_room.get("room_id"), f"room_t{thread_idx}_turn{turns_per_thread}")
                self.assertEqual(v_room.get("hazard"), f"hazard_t{thread_idx}")
                self.assertEqual(a_queue, [])

    # ==========================================================================
    # 2. Master State Non-Destructive Deep Merge
    # ==========================================================================
    def test_02_master_state_non_destructive_deep_merge(self):
        """
        Test interlaced and simultaneous updates to sector, turn_number, and staging.
        Verify that updating one subsystem does not overwrite or drop unrelated fields.
        """
        session_id = "test_deep_merge_session"

        with db_transaction(session_id=session_id, engine=self.engine) as session:
            # Step A: Initialize master state with custom fields
            init_state = {
                "turn_number": 5,
                "campaign_name": "DeepMergeCampaign",
                "custom_metadata": "unrelated_field_preserved",
                "sector": 3,
                "world_status": "Status_Normal",
            }
            MasterStateRepository.save_master_state(session, init_state, session_id=session_id)

        with db_transaction(session_id=session_id, engine=self.engine) as session:
            # Step B: Update world state (sector & news) via save_world_state
            world_patch = {
                "sector": 7,
                "world_status": "Radiation_Storm",
                "global_news": ["News_Item_1", "News_Item_2"],
            }
            MasterStateRepository.save_world_state(session, world_patch, session_id=session_id)

        # Verify after Step B
        with db_transaction(session_id=session_id, engine=self.engine) as session:
            state = MasterStateRepository.load_master_state(session, session_id=session_id)
            w_state = MasterStateRepository.load_world_state(session, session_id=session_id)
            self.assertEqual(state.get("turn_number"), 5, "turn_number should be preserved")
            self.assertEqual(state.get("campaign_name"), "DeepMergeCampaign")
            self.assertEqual(w_state.get("sector"), 7)
            self.assertEqual(w_state.get("world_status"), "Radiation_Storm")
            self.assertEqual(w_state.get("global_news"), ["News_Item_1", "News_Item_2"])

        with db_transaction(session_id=session_id, engine=self.engine) as session:
            # Step C: Save visible room via StagingRepository
            room_data = {"room_id": "bunker_vault_7", "ambient_temp": "freezing"}
            StagingRepository.save_visible_room(session, room_data, session_id=session_id)

        # Verify after Step C
        with db_transaction(session_id=session_id, engine=self.engine) as session:
            state = MasterStateRepository.load_master_state(session, session_id=session_id)
            room = StagingRepository.load_visible_room(session, session_id=session_id)
            self.assertEqual(room.get("room_id"), "bunker_vault_7")
            self.assertEqual(state.get("turn_number"), 5)
            self.assertEqual(state.get("sector"), 7)
            self.assertEqual(state.get("world_status"), "Radiation_Storm")

        with db_transaction(session_id=session_id, engine=self.engine) as session:
            # Step D: Save action queue via StagingRepository
            queue_data = [{"actor": "Banki", "action": "Parry", "target": "Mutant"}]
            StagingRepository.save_action_queue(session, queue_data, session_id=session_id)

        # Verify after Step D
        with db_transaction(session_id=session_id, engine=self.engine) as session:
            queue = StagingRepository.load_action_queue(session, session_id=session_id)
            room = StagingRepository.load_visible_room(session, session_id=session_id)
            state = MasterStateRepository.load_master_state(session, session_id=session_id)
            self.assertEqual(len(queue), 1)
            self.assertEqual(queue[0].get("actor"), "Banki")
            self.assertEqual(room.get("room_id"), "bunker_vault_7")
            self.assertEqual(state.get("sector"), 7)
            self.assertEqual(state.get("turn_number"), 5)

        with db_transaction(session_id=session_id, engine=self.engine) as session:
            # Step E: Partial master state update with ONLY turn_number increment
            # This is the critical test: does a partial dict wipe out staging or sector?
            partial_update = {"turn_number": 6}
            MasterStateRepository.save_master_state(session, partial_update, session_id=session_id)

        # Verify after Step E: All subsystems must survive
        with db_transaction(session_id=session_id, engine=self.engine) as session:
            state = MasterStateRepository.load_master_state(session, session_id=session_id)
            room = StagingRepository.load_visible_room(session, session_id=session_id)
            queue = StagingRepository.load_action_queue(session, session_id=session_id)
            w_state = MasterStateRepository.load_world_state(session, session_id=session_id)

            self.assertEqual(state.get("turn_number"), 6, "Turn number must be updated to 6")
            self.assertEqual(state.get("sector"), 7, "Sector must survive partial master state update")
            self.assertEqual(state.get("world_status"), "Radiation_Storm", "World status must survive")
            self.assertEqual(room.get("room_id"), "bunker_vault_7", "Visible room must survive")
            self.assertEqual(len(queue), 1, "Action queue must survive")
            self.assertEqual(queue[0].get("actor"), "Banki")

        # Step F: Test polymorphic calling convention: (db, sid, dict) vs (db, dict, sid)
        with db_transaction(session_id=session_id, engine=self.engine) as session:
            MasterStateRepository.save_master_state(
                session, session_id, {"turn_number": 7, "note": "reverse_sig"}
            )
        with db_transaction(session_id=session_id, engine=self.engine) as session:
            state_rev = MasterStateRepository.load_master_state(session, session_id=session_id)
            self.assertEqual(state_rev.get("turn_number"), 7)
            self.assertEqual(state_rev.get("sector"), 7)

    # ==========================================================================
    # 3. Concurrent Same-Session Staging Race Condition Stress
    # ==========================================================================
    def test_03_concurrent_same_session_staging_race(self):
        """
        Test 10 threads hammering queue_action and save_visible_room on the SAME session.
        Verify transactions commit cleanly under WAL mode without deadlock or corruption.
        """
        shared_session = "shared_concurrency_race"
        num_threads = 10
        ops_per_thread = 5
        barrier = threading.Barrier(num_threads)
        errors: List[Exception] = []

        def racer(thread_idx: int):
            try:
                barrier.wait(timeout=10.0)
                for op in range(ops_per_thread):
                    with db_transaction(session_id=shared_session, engine=self.engine) as session:
                        # Append an action
                        action = {
                            "actor": f"actor_t{thread_idx}_op{op}",
                            "action": f"attack_op{op}",
                            "timestamp": time.time(),
                        }
                        StagingRepository.queue_action(session, action, session_id=shared_session)

                    with db_transaction(session_id=shared_session, engine=self.engine) as session:
                        # Update room
                        room = {
                            "room_id": f"room_race_t{thread_idx}_op{op}",
                            "last_actor": f"t{thread_idx}",
                        }
                        StagingRepository.save_visible_room(session, room, session_id=shared_session)

            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=racer, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30.0)

        self.assertEqual(errors, [], f"Race errors encountered: {errors}")

        # Verify state integrity post-race
        with db_transaction(session_id=shared_session, engine=self.engine) as session:
            queue = StagingRepository.load_action_queue(session, session_id=shared_session)
            room = StagingRepository.load_visible_room(session, session_id=shared_session)
            self.assertIsInstance(queue, list)
            self.assertGreaterEqual(len(queue), 1)
            self.assertIn("room_race_t", room.get("room_id", ""))

    # ==========================================================================
    # 4. Seed Migrator Idempotency Across 3 Consecutive Runs
    # ==========================================================================
    def test_04_seed_migrator_idempotency_3_consecutive_runs(self):
        """
        Execute migrator.migrate_all_disk_saves_to_db() 3 consecutive times on a fresh database.
        Query all 11 tables and verify that row counts do NOT increase after the 1st run.
        Specifically verify chat_messages count remains strictly constant (0 duplicate chat messages).
        """
        mig_db_path = os.path.abspath("test_m3_migrator_idempotence.db")
        mig_db_url = f"sqlite:///{mig_db_path}"
        self._cleanup_test_db(mig_db_path)

        mig_engine = create_sao_engine(mig_db_url)
        try:
            # Table inspection helper
            def get_all_table_counts(engine) -> Dict[str, int]:
                counts = {}
                with engine.connect() as conn:
                    inspector = inspect(engine)
                    tables = sorted(inspector.get_table_names())
                    for t in tables:
                        counts[t] = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar() or 0
                return counts

            # Run 1: Initial migration
            report1 = migrate_all_disk_saves_to_db(engine=mig_engine, base_dir=".")
            self.assertEqual(report1["status"], "success")
            counts_run1 = get_all_table_counts(mig_engine)

            # Assert all 11 tables exist and are populated
            expected_tables = {
                "campaign_sessions",
                "characters",
                "equipped_slots",
                "anatomical_grafts",
                "active_debuffs",
                "skill_masteries",
                "archived_skills",
                "party_companions",
                "master_game_states",
                "corpse_caches",
                "chat_messages",
            }
            self.assertEqual(set(counts_run1.keys()), expected_tables)
            self.assertGreater(counts_run1["characters"], 0)
            self.assertGreater(counts_run1["party_companions"], 0)
            self.assertGreater(counts_run1["chat_messages"], 0)

            # Run 2: Second migration (Idempotency test 1)
            report2 = migrate_all_disk_saves_to_db(engine=mig_engine, base_dir=".")
            self.assertEqual(report2["status"], "success")
            counts_run2 = get_all_table_counts(mig_engine)

            # Check row count diffs between Run 1 and Run 2
            diffs_run2 = {
                t: counts_run2[t] - counts_run1[t]
                for t in expected_tables
                if counts_run2[t] != counts_run1[t]
            }
            self.assertEqual(
                diffs_run2,
                {},
                f"Row count increased between Run 1 and Run 2: {diffs_run2}. Full counts: {counts_run2}",
            )

            # Run 3: Third migration (Idempotency test 2)
            report3 = migrate_all_disk_saves_to_db(engine=mig_engine, base_dir=".")
            self.assertEqual(report3["status"], "success")
            counts_run3 = get_all_table_counts(mig_engine)

            # Check row count diffs between Run 1 and Run 3
            diffs_run3 = {
                t: counts_run3[t] - counts_run1[t]
                for t in expected_tables
                if counts_run3[t] != counts_run1[t]
            }
            self.assertEqual(
                diffs_run3,
                {},
                f"Row count increased between Run 1 and Run 3: {diffs_run3}. Full counts: {counts_run3}",
            )

            # Specifically verify chat_messages count remained strictly constant
            self.assertEqual(
                counts_run1["chat_messages"],
                counts_run2["chat_messages"],
                "ChatMessage count must not increase on second run",
            )
            self.assertEqual(
                counts_run1["chat_messages"],
                counts_run3["chat_messages"],
                "ChatMessage count must not increase on third run",
            )

        finally:
            mig_engine.dispose()
            self._cleanup_test_db(mig_db_path)

    # ==========================================================================
    # 5. Mechanical Parity Verification After 3 Migration Runs
    # ==========================================================================
    def test_05_seed_migrator_mechanical_parity_after_3_runs(self):
        """
        Verify that Glenny AC 14/16 & strain load, Banki skills, Ren stats, and world state
        remain 100% accurate after 3 consecutive migration runs.
        """
        mig_db_path = os.path.abspath("test_m3_migrator_parity.db")
        mig_db_url = f"sqlite:///{mig_db_path}"
        self._cleanup_test_db(mig_db_path)

        mig_engine = create_sao_engine(mig_db_url)
        try:
            # Execute 3 consecutive migrations
            for run_idx in range(1, 4):
                res = migrate_all_disk_saves_to_db(engine=mig_engine, base_dir=".")
                self.assertEqual(res["status"], "success", f"Migration run {run_idx} failed")

            # Execute official verification fidelity audit
            fidelity = verify_migration_fidelity(engine=mig_engine, session_id="default")
            self.assertEqual(
                fidelity["status"],
                "passed",
                f"Migration fidelity check failed after 3 runs: {fidelity}",
            )

            # Deep empirical inspect: Glenny
            with db_transaction(session_id="default", engine=mig_engine) as session:
                glenny = CharacterRepository.load_character(session, "glenny", session_id="default")
                self.assertIsNotNone(glenny, "Glenny must exist in default session")

                # Base AC calculation
                base_ac = mechanics.calculate_ac(glenny)
                self.assertEqual(base_ac, 14, "Glenny base AC must be 14")

                # Shield AC calculation (Riot Shield in lower_off_hand)
                glenny_shield = dict(glenny)
                glenny_shield["equipped"] = dict(glenny.get("equipped", {}))
                glenny_shield["equipped"]["lower_off_hand"] = "Riot Shield"
                shield_ac = mechanics.calculate_ac(glenny_shield)
                self.assertEqual(shield_ac, 16, "Glenny shield AC must be 16")

                # Unit strain cap: base 3 + 1 from Secondary Ganglia = 4
                max_strain = mechanics.get_max_unit_strain(glenny)
                self.assertEqual(max_strain, 4, "Glenny max unit strain must be 4")

                # Equipment limb slots
                equipped = glenny.get("equipped", {})
                self.assertEqual(
                    equipped.get("off_hand"),
                    "[2H Grip: Recurve Hunting Bow]",
                    "Glenny off_hand must be bound to 2H grip",
                )
                self.assertIn("lower_main_hand", equipped)
                self.assertIn("lower_off_hand", equipped)

                # Multi-limb Secondary Ganglia bonus (+1 Max Unit Strain Capacity)
                limb_prof = mechanics.get_limb_anatomy_profile(glenny)
                self.assertTrue(limb_prof.get("is_four_armed"), "Glenny must be four-armed")
                self.assertEqual(
                    limb_prof.get("secondary_ganglia_strain_bonus"),
                    1,
                    "Glenny must have +1 Secondary Ganglia strain bonus",
                )
                self.assertEqual(
                    limb_prof.get("extra_unit_strain_capacity"),
                    1,
                    "Glenny must have +1 extra unit strain capacity",
                )

                # Also verify installed anatomical grafts for Glenny the Undying
                glenny_undying = CharacterRepository.load_character(session, "glenny_the_undying", session_id="default")
                if glenny_undying:
                    u_grafts = glenny_undying.get("grafts", {})
                    self.assertIn("torso", u_grafts)
                    self.assertIn("lower_left_arm", u_grafts)
                    self.assertEqual(u_grafts["torso"].get("graft_name"), "basalt_carapace_plating")
                    self.assertEqual(u_grafts["lower_left_arm"].get("graft_name"), "golem_hydraulic_arm")

            # Deep empirical inspect: Banki
            with db_transaction(session_id="default", engine=mig_engine) as session:
                banki = CharacterRepository.load_character(session, "banki", session_id="default")
                self.assertIsNotNone(banki, "Banki must exist in default session")
                skills = banki.get("skills", {})
                self.assertEqual(
                    skills.get("Battleaxe Mastery", {}).get("mastery"),
                    145,
                    "Banki Battleaxe Mastery must be 145",
                )
                self.assertEqual(
                    skills.get("Arcana", {}).get("mastery"),
                    218,
                    "Banki Arcana Mastery must be 218",
                )
                self.assertEqual(banki.get("level"), 3, "Banki level must be 3")

            # Deep empirical inspect: Ren
            with db_transaction(session_id="default", engine=mig_engine) as session:
                comps = PartyRepository.load_party(session, session_id="default")
                ren = next(
                    (c for c in comps if c.get("id") in ("companion_ren", "ren") or "Ren" in c.get("name", "")),
                    None,
                )
                self.assertIsNotNone(ren, "Ren companion must exist in party")
                self.assertEqual(ren.get("hp"), 35)
                self.assertEqual(ren.get("max_hp"), 35)
                self.assertEqual(ren.get("ac"), 16)

            # Deep empirical inspect: World State
            with db_transaction(session_id="default", engine=mig_engine) as session:
                w_state = WorldRepository.load_world_state(session, session_id="default")
                m_state = WorldRepository.load_master_state(session, session_id="default")
                self.assertEqual(w_state.get("sector"), 1, "World state sector must be 1")
                self.assertEqual(m_state.get("turn_number"), 33, "Master state turn_number must be 33")

        finally:
            mig_engine.dispose()
            self._cleanup_test_db(mig_db_path)

    # ==========================================================================
    # 6. Staging Ground Disk Mirroring Session Gating
    # ==========================================================================
    def test_06_staging_ground_disk_mirroring_session_gating(self):
        """
        Verify that mirror_staging_ground_to_disk gates writes strictly to session_id == 'default'.
        Non-default sessions must NEVER alter root Staging_Ground/visible_room.json or action_queue.json.
        """
        vr_disk_path = os.path.join(PROJECT_ROOT, "Staging_Ground", "visible_room.json")
        aq_disk_path = os.path.join(PROJECT_ROOT, "Staging_Ground", "action_queue.json")

        # Snapshot existing disk content
        vr_disk_before = ""
        aq_disk_before = ""
        if os.path.exists(vr_disk_path):
            with open(vr_disk_path, "r", encoding="utf-8") as f:
                vr_disk_before = f.read()
        if os.path.exists(aq_disk_path):
            with open(aq_disk_path, "r", encoding="utf-8") as f:
                aq_disk_before = f.read()

        non_default_sid = "isolated_session_non_default"

        # Write visible room and action queue to non-default session
        with db_transaction(session_id=non_default_sid, engine=self.engine) as session:
            StagingRepository.save_visible_room(
                session,
                {"room_id": "secret_isolated_room_forbidden_on_disk"},
                session_id=non_default_sid,
            )
            StagingRepository.save_action_queue(
                session,
                [{"actor": "intruder", "action": "breach"}],
                session_id=non_default_sid,
            )

        # Verify disk files were NOT touched
        if os.path.exists(vr_disk_path):
            with open(vr_disk_path, "r", encoding="utf-8") as f:
                vr_disk_after = f.read()
            self.assertEqual(
                vr_disk_before,
                vr_disk_after,
                "Root Staging_Ground/visible_room.json was modified by non-default session!",
            )
        if os.path.exists(aq_disk_path):
            with open(aq_disk_path, "r", encoding="utf-8") as f:
                aq_disk_after = f.read()
            self.assertEqual(
                aq_disk_before,
                aq_disk_after,
                "Root Staging_Ground/action_queue.json was modified by non-default session!",
            )


if __name__ == "__main__":
    unittest.main()
