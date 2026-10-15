"""
test_m1_challenger_concurrency.py
=================================
Empirical Adversarial Challenge Suite: Milestone 1 Concurrency, Rollback & Glenny Hydration.

Authoritative Mandate:
- Hammer `backend.database.engine.db_transaction` with 10-20 concurrent threads.
- Verify SQLite WAL mode handles simultaneous read/write transactions without database locks or deadlocks.
- Test unhandled exception injection to verify clean rollback with 0 rows or corrupted state left behind.
- Verify Glenny Large 4-armed build (AC 14/16, +1 Secondary Ganglia strain cap 4) hydrates accurately from database models.
- Output empirical metrics, timing, and pass/fail diagnostics.
"""

import copy
import json
import logging
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import sqlalchemy
from sqlalchemy import func, inspect, select, text

import backend.character_generator as cg
import backend.database as db
from backend.database.adapters import (
    atomic_read_json,
    atomic_write_json,
    mirror_character_to_disk,
)
from backend.database.engine import (
    check_db_health,
    create_sao_engine,
    db_transaction,
    drop_db,
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
import backend.mechanics as mechanics

logging.basicConfig(level=logging.WARNING)


class TestMilestone1ConcurrencyAndTransactionStress(unittest.TestCase):
    """Adversarial stress testing of db_transaction, SQLite WAL mode, and atomic rollbacks."""

    def setUp(self):
        """Create a dedicated file-backed SQLite database in a fresh temp directory for each test."""
        self.temp_dir = tempfile.mkdtemp(prefix="sao_challenger_m1_")
        self.db_path = os.path.join(self.temp_dir, "challenger_sandbox.db")
        self.db_url = f"sqlite:///{self.db_path}"
        self.engine = create_sao_engine(self.db_url)
        init_db(self.engine)

    def tearDown(self):
        """Dispose the engine and clean up temp directory."""
        if hasattr(self, "engine") and self.engine is not None:
            self.engine.dispose()
        reset_engine()
        if hasattr(self, "temp_dir") and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    # =========================================================================
    # PART 1: PRAGMA & ENGINE WAL VERIFICATION
    # =========================================================================
    def test_01_sqlite_wal_pragmas_configured_correctly(self):
        """Verify SQLite WAL mode, synchronous=NORMAL, busy_timeout=30000, and foreign_keys=ON."""
        pragmas = get_sqlite_pragmas(self.engine)
        print(f"\n[Test 1] SQLite Pragmas: {pragmas}")
        self.assertEqual(str(pragmas.get("journal_mode", "")).lower(), "wal")
        self.assertEqual(pragmas.get("synchronous"), 1)  # 1 == NORMAL
        self.assertEqual(pragmas.get("busy_timeout"), 30000)
        self.assertEqual(pragmas.get("foreign_keys"), 1)  # 1 == ON

        health = check_db_health(self.engine)
        self.assertEqual(health["status"], "healthy")
        self.assertEqual(health["dialect"], "sqlite")

    # =========================================================================
    # PART 2: CONCURRENT THREAD STRESS TESTING (10 & 20 THREADS)
    # =========================================================================
    def test_02_hammer_db_transaction_10_concurrent_threads_simultaneous_inserts(self):
        """
        Adversarial Test: 10 concurrent threads simultaneously insert distinct sessions
        and characters using db_transaction.
        Uses a threading.Barrier to force all threads to hit db_transaction at the exact same microsecond.
        """
        num_threads = 10
        barrier = threading.Barrier(num_threads)
        errors: List[Exception] = []
        thread_durations: List[float] = []

        def worker(thread_idx: int):
            try:
                session_id = f"sess_10_t{thread_idx}"
                char_slug = f"hero_10_t{thread_idx}"
                # Wait for all threads to synchronize
                barrier.wait(timeout=10.0)

                t0 = time.perf_counter()
                with db_transaction(engine=self.engine, session_id=session_id) as sess:
                    # Insert CampaignSessionRecord
                    camp = CampaignSessionRecord(session_id=session_id, session_name=f"Campaign {thread_idx}")
                    sess.add(camp)
                    sess.flush()

                    # Insert CharacterRecord
                    char = CharacterRecord(
                        session_id=session_id,
                        slug=char_slug,
                        name=f"Hero {thread_idx}",
                        level=1 + thread_idx,
                        hp=100 + (thread_idx * 10),
                        max_hp=100 + (thread_idx * 10),
                        col=50 * thread_idx,
                        race="Human",
                        character_class="Swordsman",
                        stats_json=json.dumps({"STR": 14 + thread_idx, "DEX": 12, "CON": 14}),
                        raw_data_json=json.dumps({"player": {"name": f"Hero {thread_idx}", "level": 1 + thread_idx}}),
                    )
                    sess.add(char)
                t1 = time.perf_counter()
                thread_durations.append(t1 - t0)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        t_start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30.0)
        t_total = time.perf_counter() - t_start

        print(f"\n[Test 2] 10 Concurrent Threads Hammer Results:")
        print(f"  - Total time: {t_total:.4f}s")
        print(f"  - Thread durations: min={min(thread_durations):.4f}s, max={max(thread_durations):.4f}s, avg={sum(thread_durations)/len(thread_durations):.4f}s")
        print(f"  - Errors encountered: {len(errors)}")

        self.assertEqual(len(errors), 0, f"Encountered {len(errors)} errors during 10-thread hammer: {errors}")

        # Verify all 10 sessions and characters exist in DB with exact values
        with db_transaction(engine=self.engine) as sess:
            sessions_count = sess.query(func.count(CampaignSessionRecord.session_id)).scalar()
            chars_count = sess.query(func.count(CharacterRecord.id)).scalar()
            self.assertEqual(sessions_count, num_threads)
            self.assertEqual(chars_count, num_threads)

            for i in range(num_threads):
                s_id = f"sess_10_t{i}"
                c_slug = f"hero_10_t{i}"
                c = sess.query(CharacterRecord).filter_by(session_id=s_id, slug=c_slug).first()
                self.assertIsNotNone(c)
                self.assertEqual(c.level, 1 + i)
                self.assertEqual(c.hp, 100 + (i * 10))
                self.assertEqual(c.col, 50 * i)

    def test_03_hammer_db_transaction_20_concurrent_threads_simultaneous_inserts_and_updates(self):
        """
        Adversarial Test: 20 concurrent threads simultaneously perform inserts, followed by
        subsequent updates across separate transactions using db_transaction.
        Total operations: 20 threads x 10 transaction rounds = 200 ACID transactions.
        Verifies SQLite WAL mode handles heavy concurrent writes without database lock contention.
        """
        num_threads = 20
        rounds_per_thread = 10
        barrier = threading.Barrier(num_threads)
        errors: List[Exception] = []

        def worker(thread_idx: int):
            try:
                session_id = f"sess_20_t{thread_idx}"
                char_slug = f"hero_20_t{thread_idx}"
                barrier.wait(timeout=10.0)

                # Round 0: Initial Insert
                with db_transaction(engine=self.engine, session_id=session_id) as sess:
                    camp = CampaignSessionRecord(session_id=session_id, session_name=f"Campaign 20-{thread_idx}")
                    sess.add(camp)
                    sess.flush()
                    char = CharacterRecord(
                        session_id=session_id,
                        slug=char_slug,
                        name=f"Vanguard {thread_idx}",
                        level=1,
                        hp=100,
                        max_hp=100,
                        col=0,
                        stats_json=json.dumps({"STR": 15, "CON": 14}),
                    )
                    sess.add(char)

                # Rounds 1 to rounds_per_thread - 1: Repeated Updates
                for r in range(1, rounds_per_thread):
                    with db_transaction(engine=self.engine, session_id=session_id) as sess:
                        c = sess.query(CharacterRecord).filter_by(session_id=session_id, slug=char_slug).first()
                        self.assertIsNotNone(c)
                        c.level += 1
                        c.hp += 10
                        c.max_hp += 10
                        c.col += 100

            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        t_start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=60.0)
        t_total = time.perf_counter() - t_start

        total_tx = num_threads * rounds_per_thread
        print(f"\n[Test 3] 20 Concurrent Threads x {rounds_per_thread} Rounds ({total_tx} Transactions) Results:")
        print(f"  - Total elapsed: {t_total:.4f}s")
        print(f"  - Throughput: {total_tx / t_total:.2f} tx/sec")
        print(f"  - Errors encountered: {len(errors)}")

        self.assertEqual(len(errors), 0, f"Encountered {len(errors)} errors during 20-thread stress: {errors}")

        # Verify all 20 records reached final expected values
        with db_transaction(engine=self.engine) as sess:
            sessions_count = sess.query(func.count(CampaignSessionRecord.session_id)).scalar()
            chars_count = sess.query(func.count(CharacterRecord.id)).scalar()
            self.assertEqual(sessions_count, num_threads)
            self.assertEqual(chars_count, num_threads)

            for i in range(num_threads):
                s_id = f"sess_20_t{i}"
                c_slug = f"hero_20_t{i}"
                c = sess.query(CharacterRecord).filter_by(session_id=s_id, slug=c_slug).first()
                self.assertIsNotNone(c)
                # Level should be 1 + (rounds_per_thread - 1) = 10
                self.assertEqual(c.level, rounds_per_thread)
                # HP should be 100 + (rounds_per_thread - 1) * 10 = 190
                self.assertEqual(c.hp, 100 + ((rounds_per_thread - 1) * 10))
                # Col should be 0 + (rounds_per_thread - 1) * 100 = 900
                self.assertEqual(c.col, (rounds_per_thread - 1) * 100)

    def test_04_simultaneous_concurrent_readers_and_writers_in_wal_mode(self):
        """
        Adversarial Test: 10 worker threads performing continuous WRITES while 10 worker threads
        perform continuous READS concurrently over a 3-second window.
        Verifies SQLite WAL mode enables concurrent readers and writers without lock errors.
        """
        # First seed initial data
        with db_transaction(engine=self.engine) as sess:
            for i in range(10):
                camp = CampaignSessionRecord(session_id=f"wal_seed_{i}", session_name=f"Seed {i}")
                sess.add(camp)
                sess.flush()
                char = CharacterRecord(
                    session_id=f"wal_seed_{i}",
                    slug=f"char_{i}",
                    name=f"Seed Char {i}",
                    level=1,
                    hp=100,
                    col=50,
                )
                sess.add(char)

        stop_event = threading.Event()
        write_errors: List[Exception] = []
        read_errors: List[Exception] = []
        write_ops = [0] * 10
        read_ops = [0] * 10

        def writer(idx: int):
            s_id = f"wal_seed_{idx}"
            c_slug = f"char_{idx}"
            while not stop_event.is_set():
                try:
                    with db_transaction(engine=self.engine, session_id=s_id) as sess:
                        c = sess.query(CharacterRecord).filter_by(session_id=s_id, slug=c_slug).first()
                        if c:
                            c.col += 1
                    write_ops[idx] += 1
                except Exception as exc:
                    write_errors.append(exc)
                    break
                time.sleep(0.005)

        def reader(idx: int):
            s_id = f"wal_seed_{idx}"
            c_slug = f"char_{idx}"
            while not stop_event.is_set():
                try:
                    with db_transaction(engine=self.engine) as sess:
                        c = sess.query(CharacterRecord).filter_by(session_id=s_id, slug=c_slug).first()
                        _ = c.col if c else 0
                    read_ops[idx] += 1
                except Exception as exc:
                    read_errors.append(exc)
                    break
                time.sleep(0.003)

        writer_threads = [threading.Thread(target=writer, args=(i,)) for i in range(10)]
        reader_threads = [threading.Thread(target=reader, args=(i,)) for i in range(10)]

        t_start = time.perf_counter()
        for t in writer_threads + reader_threads:
            t.start()

        # Run concurrent readers/writers for 2.5 seconds
        time.sleep(2.5)
        stop_event.set()

        for t in writer_threads + reader_threads:
            t.join(timeout=10.0)
        t_total = time.perf_counter() - t_start

        total_writes = sum(write_ops)
        total_reads = sum(read_ops)
        print(f"\n[Test 4] Concurrent Readers & Writers in WAL Mode (10 Writers + 10 Readers, 2.5s):")
        print(f"  - Completed Writes: {total_writes} ({total_writes / t_total:.2f} writes/sec)")
        print(f"  - Completed Reads:  {total_reads} ({total_reads / t_total:.2f} reads/sec)")
        print(f"  - Write Errors: {len(write_errors)}: {write_errors}")
        print(f"  - Read Errors:  {len(read_errors)}: {read_errors}")

        self.assertEqual(len(write_errors), 0, f"Encountered write errors: {write_errors}")
        self.assertEqual(len(read_errors), 0, f"Encountered read errors: {read_errors}")
        self.assertGreater(total_writes, 50)
        self.assertGreater(total_reads, 100)

    # =========================================================================
    # PART 3: UNHANDLED EXCEPTION INJECTION & ATOMIC ROLLBACK
    # =========================================================================
    def test_05_unhandled_exception_rolls_back_multi_table_inserts_cleanly(self):
        """
        Adversarial Test: An unhandled exception raised midway through a transaction
        guarantees that ALL changes are rolled back with 0 rows or corrupted state left behind.
        Also verifies that registered post-commit hooks are dropped and never executed.
        """
        hook_executed = [False]

        def post_commit_callback():
            hook_executed[0] = True

        session_id = "sess_exception_test"
        with self.assertRaises(RuntimeError) as ctx:
            with db_transaction(engine=self.engine, session_id=session_id) as sess:
                register_post_commit_hook(sess, post_commit_callback)

                # 1. Insert Campaign
                camp = CampaignSessionRecord(session_id=session_id, session_name="Doomed Campaign")
                sess.add(camp)
                sess.flush()

                # 2. Insert Character
                char = CharacterRecord(
                    session_id=session_id,
                    slug="doomed_char",
                    name="Doomed Character",
                    level=5,
                    hp=150,
                )
                sess.add(char)
                sess.flush()

                # 3. Insert Equipped Slot & Graft
                slot = EquippedSlotRecord(character_id=char.id, slot_key="main_hand", item_name="Cursed Dagger")
                graft = AnatomicalGraftRecord(character_id=char.id, slot_key="spine", graft_name="Neural Shocker")
                sess.add_all([slot, graft])
                sess.flush()

                # 4. Trigger intentional catastrophic failure
                raise RuntimeError("Simulated catastrophic crash inside db_transaction!")

        self.assertIn("Simulated catastrophic crash inside db_transaction!", str(ctx.exception))
        # Verify post-commit hook was NOT executed
        self.assertFalse(hook_executed[0], "Post-commit hook must NOT execute when transaction rolls back!")

        # Verify DB state: zero rows created across all tables
        with db_transaction(engine=self.engine) as sess:
            self.assertIsNone(sess.query(CampaignSessionRecord).filter_by(session_id=session_id).first())
            self.assertIsNone(sess.query(CharacterRecord).filter_by(slug="doomed_char").first())
            self.assertEqual(sess.query(EquippedSlotRecord).count(), 0)
            self.assertEqual(sess.query(AnatomicalGraftRecord).count(), 0)
        print("\n[Test 5] Verified clean multi-table rollback on unhandled exception: 0 rows leaked.")

    def test_06_concurrent_threads_with_injected_exceptions_isolation(self):
        """
        Adversarial Test: 10 concurrent threads where exactly 5 threads succeed and commit,
        while 5 threads encounter intentional unhandled exceptions.
        Verifies that failing threads roll back cleanly without polluting or corrupting
        the 5 successful threads.
        """
        num_threads = 10
        barrier = threading.Barrier(num_threads)
        thread_outcomes: Dict[int, str] = {}

        def worker(thread_idx: int):
            s_id = f"sess_mixed_{thread_idx}"
            c_slug = f"char_mixed_{thread_idx}"
            barrier.wait(timeout=10.0)

            should_fail = (thread_idx % 2 == 1)  # Odd threads fail (1, 3, 5, 7, 9)
            try:
                with db_transaction(engine=self.engine, session_id=s_id) as sess:
                    camp = CampaignSessionRecord(session_id=s_id, session_name=f"Camp {thread_idx}")
                    sess.add(camp)
                    sess.flush()

                    char = CharacterRecord(session_id=s_id, slug=c_slug, name=f"Char {thread_idx}", hp=100)
                    sess.add(char)
                    sess.flush()

                    if should_fail:
                        raise ValueError(f"Injected intentional failure in thread {thread_idx}")

                thread_outcomes[thread_idx] = "SUCCESS"
            except ValueError:
                thread_outcomes[thread_idx] = "ROLLED_BACK"
            except Exception as exc:
                thread_outcomes[thread_idx] = f"UNEXPECTED_ERROR: {exc}"

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30.0)

        print(f"\n[Test 6] Concurrent Mixed Outcomes: {thread_outcomes}")
        # Verify 5 succeeded, 5 rolled back
        success_count = sum(1 for v in thread_outcomes.values() if v == "SUCCESS")
        rollback_count = sum(1 for v in thread_outcomes.values() if v == "ROLLED_BACK")
        self.assertEqual(success_count, 5)
        self.assertEqual(rollback_count, 5)

        # Inspect DB state
        with db_transaction(engine=self.engine) as sess:
            sessions = sess.query(CampaignSessionRecord).all()
            characters = sess.query(CharacterRecord).all()
            self.assertEqual(len(sessions), 5)
            self.assertEqual(len(characters), 5)

            # Even threads (0, 2, 4, 6, 8) must exist; Odd threads must NOT exist
            for i in range(num_threads):
                s_id = f"sess_mixed_{i}"
                c_slug = f"char_mixed_{i}"
                c = sess.query(CharacterRecord).filter_by(session_id=s_id, slug=c_slug).first()
                if i % 2 == 0:
                    self.assertIsNotNone(c, f"Even thread {i} should be committed!")
                else:
                    self.assertIsNone(c, f"Odd thread {i} should be completely rolled back!")

    def test_07_disk_mirroring_aborts_on_transaction_rollback(self):
        """
        Adversarial Test: Verify that if a transaction rolls back, disk-mirroring hooks
        do NOT write or alter disk files, and existing save files remain completely untouched.
        """
        target_file = os.path.join(self.temp_dir, "mirrored_save.json")
        initial_payload = {"player": {"name": "SafeSurvivor", "hp": 100}}
        atomic_write_json(target_file, initial_payload)

        # Attempt transaction that modifies character and queues mirror_character_to_disk
        with self.assertRaises(RuntimeError):
            with db_transaction(engine=self.engine, session_id="mirror_sess") as sess:
                camp = CampaignSessionRecord(session_id="mirror_sess", session_name="Mirror Campaign")
                sess.add(camp)
                sess.flush()

                char = CharacterRecord(session_id="mirror_sess", slug="corrupted", name="Corrupted", hp=0)
                sess.add(char)
                sess.flush()

                # Register disk mirror hook
                register_post_commit_hook(
                    sess,
                    lambda: atomic_write_json(target_file, {"player": {"name": "Corrupted", "hp": 0}})
                )
                raise RuntimeError("Abort transaction before commit!")

        # Verify disk file is unchanged and uncorrupted
        disk_data = atomic_read_json(target_file)
        self.assertEqual(disk_data["player"]["name"], "SafeSurvivor")
        self.assertEqual(disk_data["player"]["hp"], 100)
        print("\n[Test 7] Disk mirroring verified aborted on transaction rollback; 0-byte corruption avoided.")

    def test_08_atomic_write_json_zero_byte_corruption_resilience(self):
        """
        Adversarial Test: Verify atomic_write_json never leaves a 0-byte or corrupted file
        even under non-serializable objects or crash simulation.
        """
        valid_file = os.path.join(self.temp_dir, "valid_save.json")
        atomic_write_json(valid_file, {"version": 1, "data": "solid"})

        # Try writing circular reference (un-serializable object)
        circular = {}
        circular["self"] = circular

        with self.assertRaises((ValueError, TypeError)):
            atomic_write_json(valid_file, circular)

        # Target file must still exist and be completely intact
        self.assertTrue(os.path.exists(valid_file))
        self.assertGreater(os.path.getsize(valid_file), 0)
        read_back = atomic_read_json(valid_file)
        self.assertEqual(read_back["data"], "solid")
        print("\n[Test 8] Verified atomic_write_json circular serialization crash does not truncate existing file.")

    # =========================================================================
    # PART 4: GLENNY PROFILE HYDRATION FROM DATABASE MODELS
    # =========================================================================
    def test_09_glenny_baseline_and_shielded_ac_strain_cap_parity(self):
        """
        Adversarial Verification: Glenny's Large 4-armed build (AC 14 baseline, AC 16 shielded,
        +1 Secondary Ganglia strain cap 4) hydrates accurately from the database models.
        """
        # 1. Generate canonical Glenny via character_generator
        glenny_dict = cg.generate_starting_character("Glenny")
        self.assertEqual(glenny_dict["name"], "Glenny")
        self.assertEqual(glenny_dict["stats"]["STR"], 18)
        self.assertEqual(glenny_dict["stats"]["DEX"], 15)
        self.assertEqual(glenny_dict["stats"]["CON"], 16)

        # Baseline AC before DB persistence:
        # Base AC: 10 + 2 (DEX) + 1 (Tunic) + 2 (Fibrous Hide) - 1 (Large Size) = 14
        ac_base_calc = mechanics.calculate_ac(glenny_dict)
        self.assertEqual(ac_base_calc, 14, f"Glenny baseline AC must be 14, got {ac_base_calc}")

        # Baseline Strain Cap before DB persistence:
        # CON 16 (+3) + Level 1 // 2 (0) + Secondary Ganglia (+1) = 4
        strain_cap_calc = mechanics.get_max_unit_strain(glenny_dict)
        self.assertEqual(strain_cap_calc, 4, f"Glenny strain cap must be 4, got {strain_cap_calc}")

        session_id = "glenny_campaign_session"

        # 2. Persist Glenny into Relational Database Models
        with db_transaction(engine=self.engine, session_id=session_id) as sess:
            camp = CampaignSessionRecord(session_id=session_id, session_name="Glenny Apex Campaign")
            sess.add(camp)
            sess.flush()

            char_record = CharacterRecord(
                session_id=session_id,
                slug="glenny",
                name="Glenny",
                level=1,
                hp=glenny_dict.get("hp", 135),
                max_hp=glenny_dict.get("max_hp", 135),
                col=glenny_dict.get("col", 100),
                xp=glenny_dict.get("xp", 0),
                gender=glenny_dict.get("gender", "Non-binary"),
                race=glenny_dict.get("race", "Spliced Apex Chimera"),
                character_class=glenny_dict.get("class", "Apex Predator"),
                location=glenny_dict.get("location", "Floor 1 - Town of Beginnings"),
                stats_json=json.dumps(glenny_dict.get("stats", {})),
                raw_data_json=json.dumps({"player": glenny_dict}),
            )
            sess.add(char_record)
            sess.flush()

            # Add Normalized Multi-Limb Equipped Slots
            equipped_map = glenny_dict.get("equipped", {})
            for slot_key, item_name in equipped_map.items():
                slot_rec = EquippedSlotRecord(
                    character_id=char_record.id,
                    slot_key=slot_key,
                    item_name=item_name,
                )
                sess.add(slot_rec)

            # Add Normalized Anatomical Grafts
            grafts_map = glenny_dict.get("grafts", {})
            for g_slot, g_info in grafts_map.items():
                g_name = g_info.get("name", "Unknown Graft") if isinstance(g_info, dict) else str(g_info)
                g_strain = g_info.get("strain", 1) if isinstance(g_info, dict) else 1
                graft_rec = AnatomicalGraftRecord(
                    character_id=char_record.id,
                    slot_key=g_slot,
                    graft_name=g_name,
                    unit_strain=g_strain,
                    graft_data_json=json.dumps(g_info) if isinstance(g_info, dict) else None,
                )
                sess.add(graft_rec)

        # 3. Read back Glenny in a completely fresh session from DB
        with db_transaction(engine=self.engine) as sess:
            fetched_char = sess.query(CharacterRecord).filter_by(session_id=session_id, slug="glenny").first()
            self.assertIsNotNone(fetched_char)

            # Hydrate into player dict via dual-coverage model
            hydrated = fetched_char.to_player_dict()

            print("\n[Test 9] Hydrated Glenny Model Attributes:")
            print(f"  - Name: {hydrated.get('name')}")
            print(f"  - Race: {hydrated.get('race')}")
            print(f"  - STR/DEX/CON: {hydrated['stats']['STR']}/{hydrated['stats']['DEX']}/{hydrated['stats']['CON']}")
            print(f"  - Equipped Slots: {list(hydrated.get('equipped', {}).keys())}")
            print(f"  - Off-Hand Grip: {hydrated.get('equipped', {}).get('off_hand')}")
            print(f"  - Grafts Count: {len(hydrated.get('grafts', {}))}")

            # 4. Verify 4 Hand Slots & 2H Grip String Binding
            equipped = hydrated.get("equipped", {})
            self.assertIn("main_hand", equipped)
            self.assertIn("off_hand", equipped)
            self.assertIn("lower_main_hand", equipped)
            self.assertIn("lower_off_hand", equipped)
            self.assertEqual(equipped["off_hand"], "[2H Grip: Recurve Hunting Bow]")

            # 5. Verify Hydrated Physical Profile & Size Modifier
            profile = mechanics.get_physical_profile(hydrated)
            self.assertEqual(profile["size"], "Large")
            self.assertEqual(profile["modifiers"]["ac_mod"], -1)

            # 6. Verify Hydrated Baseline Unshielded AC == 14
            hydrated_ac_unshielded = mechanics.calculate_ac(hydrated)
            self.assertEqual(hydrated_ac_unshielded, 14, f"Hydrated baseline AC must be 14, got {hydrated_ac_unshielded}")

            # 7. Verify Hydrated Unit Strain Cap == 4 (+1 Secondary Ganglia)
            hydrated_strain_cap = mechanics.get_max_unit_strain(hydrated)
            self.assertEqual(hydrated_strain_cap, 4, f"Hydrated Unit Strain Cap must be 4, got {hydrated_strain_cap}")

            # 8. Equip Wooden Buckler in lower_off_hand and verify AC == 16
            hydrated["equipped"]["lower_off_hand"] = "Wooden Buckler"
            hydrated_ac_shielded = mechanics.calculate_ac(hydrated)
            self.assertEqual(hydrated_ac_shielded, 16, f"Hydrated shielded AC must be 16, got {hydrated_ac_shielded}")

            print(f"  - Hydrated Baseline AC: {hydrated_ac_unshielded} (Expected: 14)")
            print(f"  - Hydrated Shielded AC: {hydrated_ac_shielded} (Expected: 16)")
            print(f"  - Hydrated Unit Strain Cap: {hydrated_strain_cap} (Expected: 4)")

    def test_10_update_glenny_equipped_slot_in_database_and_verify_ac_16(self):
        """
        Adversarial Test: Perform an actual database UPDATE transaction equipping
        'Wooden Buckler' in Glenny's lower_off_hand slot, re-fetch from database,
        and confirm hydrated AC recomputes to 16.
        """
        session_id = "glenny_shield_swap_sess"
        glenny_dict = cg.generate_starting_character("Glenny")

        # Initial insert
        with db_transaction(engine=self.engine, session_id=session_id) as sess:
            camp = CampaignSessionRecord(session_id=session_id, session_name="Shield Swap")
            sess.add(camp)
            sess.flush()

            char = CharacterRecord(
                session_id=session_id,
                slug="glenny",
                name="Glenny",
                level=1,
                stats_json=json.dumps(glenny_dict["stats"]),
                raw_data_json=json.dumps({"player": glenny_dict}),
            )
            sess.add(char)
            sess.flush()

            for s_key, s_item in glenny_dict["equipped"].items():
                sess.add(EquippedSlotRecord(character_id=char.id, slot_key=s_key, item_name=s_item))

        # Update transaction: equip Wooden Buckler in lower_off_hand
        with db_transaction(engine=self.engine, session_id=session_id) as sess:
            char = sess.query(CharacterRecord).filter_by(session_id=session_id, slug="glenny").first()
            self.assertIsNotNone(char)
            lower_off = sess.query(EquippedSlotRecord).filter_by(character_id=char.id, slot_key="lower_off_hand").first()
            if lower_off:
                lower_off.item_name = "Wooden Buckler"
            else:
                sess.add(EquippedSlotRecord(character_id=char.id, slot_key="lower_off_hand", item_name="Wooden Buckler"))

        # Re-fetch from fresh transaction and verify
        with db_transaction(engine=self.engine) as sess:
            char = sess.query(CharacterRecord).filter_by(session_id=session_id, slug="glenny").first()
            hydrated = char.to_player_dict()
            self.assertEqual(hydrated["equipped"]["lower_off_hand"], "Wooden Buckler")
            ac = mechanics.calculate_ac(hydrated)
            self.assertEqual(ac, 16, f"Glenny with Wooden Buckler in lower_off_hand must have AC 16, got {ac}")
            print(f"\n[Test 10] DB-Updated Glenny lower_off_hand to Wooden Buckler -> Hydrated AC: {ac} (Expected: 16)")


def run_challenger_suite():
    """Runs the suite and prints summary metrics."""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMilestone1ConcurrencyAndTransactionStress)
    runner = unittest.TextTestRunner(verbosity=2)
    start_time = time.perf_counter()
    result = runner.run(suite)
    elapsed = time.perf_counter() - start_time

    print("\n" + "=" * 70)
    print("CHALLENGER 1 EMPIRICAL VERIFICATION REPORT")
    print("=" * 70)
    print(f"Total Tests Run: {result.testsRun}")
    print(f"Failures:        {len(result.failures)}")
    print(f"Errors:          {len(result.errors)}")
    print(f"Total Runtime:   {elapsed:.2f} seconds")
    verdict = "CONFIRM" if result.wasSuccessful() else "REJECT"
    print(f"FINAL VERDICT:   {verdict}")
    print("=" * 70)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_challenger_suite()
    sys.exit(0 if success else 1)
