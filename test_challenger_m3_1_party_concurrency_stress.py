"""
test_challenger_m3_1_party_concurrency_stress.py
=================================================
Milestone 3 Challenger 1 Empirical Concurrency & Stress Verification Suite.

Adversarial Stress Test Objectives:
1. Multi-Session Isolation Test across 10 concurrent threads (session_0 to session_9).
   Verifies zero cross-session data leakage, exact state preservation, and slug independence.
2. Concurrent Companion Hammering within Same Session.
   Hammers save_party and load_party concurrently; verifies in-place diffing with nested savepoints
   prevents unique slug collisions and avoids transient 0-row empty party states.
3. Concurrent New Slug Collision Handling.
   8 threads simultaneously race to insert the exact same new companion slug.
4. Disk Mirroring Isolation:
   - Custom session (session_test_999) NEVER touches root Party/*.json.
   - Default session DOES update root Party/*.json atomically.
   - Rollback aborts post-commit hooks and leaves disk mirrors untouched.
5. Roster pruning & empty list isolation across sessions.
6. Malformed / duplicate slugs in single save_party payload.
7. Live sao_sandbox.db multi-session verification.
"""

import copy
import json
import os
import random
import sys
import threading
import time
import unittest
from typing import List, Dict, Any

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import select, text
import backend.database as db
from backend.database.models import (
    CampaignSessionRecord,
    PartyCompanionRecord,
)
from backend.database.repositories import (
    PartyRepository,
)
from backend.database.adapters import (
    atomic_read_json,
    atomic_write_json,
)


class TestM3PartyConcurrencyStress(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = os.path.abspath("test_m3_challenger_stress.db")
        cls.db_url = f"sqlite:///{cls.db_path}"
        cls._cleanup_db()
        cls.stress_engine = db.create_sao_engine(cls.db_url)
        db.init_db(cls.stress_engine)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "stress_engine"):
            cls.stress_engine.dispose()
        cls._cleanup_db()

    @classmethod
    def _cleanup_db(cls):
        for ext in ["", "-wal", "-shm"]:
            f = f"{cls.db_path}{ext}"
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    # =========================================================================
    # 1. MULTI-SESSION ISOLATION TEST (10 THREADS)
    # =========================================================================
    def test_01_multi_session_companion_isolation_10_threads(self):
        """
        Spawns 10 concurrent threads representing session_0 through session_9.
        Each thread repeatedly saves and verifies a distinct companion roster with
        matching companion slugs (e.g. 'ren', 'elora', 'torvald') but session-unique stats.
        Verifies that no cross-session leakage ever occurs.
        """
        num_threads = 10
        rounds_per_thread = 15
        barrier = threading.Barrier(num_threads)
        errors: List[str] = []

        def worker_session(thread_idx: int):
            session_id = f"stress_session_{thread_idx}"
            try:
                barrier.wait(timeout=10.0)
                for r in range(rounds_per_thread):
                    # Unique attributes per session and round
                    expected_ren_hp = 100 + thread_idx * 10 + r
                    expected_ren_lvl = 10 + thread_idx
                    expected_ren_active = (thread_idx % 2 == 0)

                    expected_elora_hp = 200 + thread_idx * 10 + r
                    expected_elora_lvl = 20 + thread_idx

                    companions = [
                        {
                            "slug": "ren",
                            "name": f"Ren (Session {thread_idx})",
                            "level": expected_ren_lvl,
                            "hp": expected_ren_hp,
                            "max_hp": expected_ren_hp + 50,
                            "ac": 16,
                            "is_active": expected_ren_active,
                            "stats": {"INT": 18 + thread_idx},
                        },
                        {
                            "slug": "elora",
                            "name": f"Elora (Session {thread_idx})",
                            "level": expected_elora_lvl,
                            "hp": expected_elora_hp,
                            "max_hp": expected_elora_hp + 30,
                            "ac": 15,
                            "is_active": True,
                        },
                        {
                            "slug": f"unique_companion_{thread_idx}",
                            "name": f"Unique {thread_idx}",
                            "level": thread_idx + 1,
                            "hp": 50 + thread_idx,
                            "is_active": False,
                        },
                    ]

                    # 1. Save party
                    with db.db_transaction(engine=self.stress_engine, session_id=session_id) as sess:
                        PartyRepository.save_party(
                            db_session=sess,
                            companions=companions,
                            session_id=session_id,
                            mirror_disk=False,
                        )

                    # Jitter to maximize interleaving
                    time.sleep(random.uniform(0.001, 0.005))

                    # 2. Load party
                    with db.db_transaction(engine=self.stress_engine, session_id=session_id) as sess:
                        loaded = PartyRepository.load_party(
                            db_session=sess,
                            session_id=session_id,
                            seed_from_disk_if_empty=False,
                        )

                    # 3. Assertions
                    if len(loaded) != 3:
                        errors.append(f"[T{thread_idx} R{r}] Expected 3 companions, got {len(loaded)}")
                        continue

                    by_slug = {c["slug"]: c for c in loaded}

                    # Check Ren
                    ren = by_slug.get("ren")
                    if not ren:
                        errors.append(f"[T{thread_idx} R{r}] Missing 'ren' in session {session_id}")
                    else:
                        if ren["hp"] != expected_ren_hp:
                            errors.append(
                                f"[T{thread_idx} R{r}] Ren HP leakage! Expected {expected_ren_hp}, got {ren['hp']}"
                            )
                        if ren["level"] != expected_ren_lvl:
                            errors.append(
                                f"[T{thread_idx} R{r}] Ren level leakage! Expected {expected_ren_lvl}, got {ren['level']}"
                            )
                        if ren["is_active"] != expected_ren_active:
                            errors.append(
                                f"[T{thread_idx} R{r}] Ren active flag leakage! Expected {expected_ren_active}, got {ren['is_active']}"
                            )

                    # Check Elora
                    elora = by_slug.get("elora")
                    if not elora:
                        errors.append(f"[T{thread_idx} R{r}] Missing 'elora' in session {session_id}")
                    else:
                        if elora["hp"] != expected_elora_hp:
                            errors.append(
                                f"[T{thread_idx} R{r}] Elora HP leakage! Expected {expected_elora_hp}, got {elora['hp']}"
                            )

                    # Check unique companion
                    unique_slug = f"unique_companion_{thread_idx}"
                    if unique_slug not in by_slug:
                        errors.append(f"[T{thread_idx} R{r}] Missing {unique_slug} in session {session_id}")

                    # Check that no other thread's unique companion leaked in
                    for other_idx in range(num_threads):
                        if other_idx != thread_idx:
                            foreign_slug = f"unique_companion_{other_idx}"
                            if foreign_slug in by_slug:
                                errors.append(
                                    f"[T{thread_idx} R{r}] Cross-session leakage! Found foreign slug '{foreign_slug}'"
                                )

            except Exception as exc:
                errors.append(f"[T{thread_idx}] Unhandled exception: {exc}")

        threads = [threading.Thread(target=worker_session, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30.0)

        self.assertEqual(errors, [], f"Multi-session isolation failures: {errors}")

    # =========================================================================
    # 2. CONCURRENT COMPANION HAMMERING WITHIN SAME SESSION
    # =========================================================================
    def test_02_concurrent_companion_hammering_same_session(self):
        """
        Hammers save_party concurrently from 4 writer threads updating different companions
        in the SAME session ('hammer_unified_session').
        Simultaneously, 4 reader threads continuously query load_party().
        Verifies:
        - In-place diffing avoids transient 0-row empty party states.
        - No unhandled unique slug collisions or deadlocks occur.
        """
        session_id = "hammer_unified_session"
        initial_party = [
            {"slug": "ren", "name": "Ren", "hp": 35, "level": 3, "active": True},
            {"slug": "elora", "name": "Elora", "hp": 40, "level": 3, "active": True},
            {"slug": "torvald", "name": "Torvald", "hp": 65, "level": 4, "active": True},
            {"slug": "kibs", "name": "Kibs", "hp": 20, "level": 2, "active": True},
        ]

        with db.db_transaction(engine=self.stress_engine, session_id=session_id) as sess:
            PartyRepository.save_party(sess, initial_party, session_id=session_id, mirror_disk=False)

        stop_event = threading.Event()
        errors: List[str] = []
        zero_row_reads = []
        successful_reads = [0]
        successful_writes = [0]

        def writer_worker(target_slug: str, base_hp: int):
            try:
                for step in range(25):
                    new_hp = base_hp + step
                    # To prevent deleting other companions, the writer passes the full roster
                    # or an updated dict with its target modified
                    with db.db_transaction(engine=self.stress_engine, session_id=session_id) as sess:
                        current_roster = PartyRepository.load_party(
                            sess, session_id=session_id, seed_from_disk_if_empty=False
                        )
                        updated_roster = []
                        found = False
                        for c in current_roster:
                            c_copy = copy.deepcopy(c)
                            if c_copy["slug"] == target_slug:
                                c_copy["hp"] = new_hp
                                found = True
                            updated_roster.append(c_copy)
                        if not found:
                            updated_roster.append({"slug": target_slug, "hp": new_hp})

                        PartyRepository.save_party(
                            sess, updated_roster, session_id=session_id, mirror_disk=False
                        )
                    successful_writes[0] += 1
                    time.sleep(random.uniform(0.002, 0.008))
            except Exception as exc:
                errors.append(f"[Writer {target_slug}] Exception: {exc}")

        def reader_worker(reader_id: int):
            try:
                while not stop_event.is_set():
                    with db.db_transaction(engine=self.stress_engine, session_id=session_id) as sess:
                        loaded = PartyRepository.load_party(
                            sess, session_id=session_id, seed_from_disk_if_empty=False
                        )
                        if len(loaded) == 0:
                            zero_row_reads.append(f"Reader {reader_id} saw 0-row empty party!")
                        successful_reads[0] += 1
                    time.sleep(0.001)
            except Exception as exc:
                errors.append(f"[Reader {reader_id}] Exception: {exc}")

        writers = [
            threading.Thread(target=writer_worker, args=("ren", 35)),
            threading.Thread(target=writer_worker, args=("elora", 40)),
            threading.Thread(target=writer_worker, args=("torvald", 65)),
            threading.Thread(target=writer_worker, args=("kibs", 20)),
        ]
        readers = [threading.Thread(target=reader_worker, args=(i,)) for i in range(4)]

        for t in readers:
            t.start()
        for t in writers:
            t.start()

        for t in writers:
            t.join(timeout=30.0)

        stop_event.set()
        for t in readers:
            t.join(timeout=10.0)

        self.assertEqual(errors, [], f"Errors encountered during hammering: {errors}")
        self.assertEqual(zero_row_reads, [], f"Transient 0-row reads detected: {zero_row_reads}")
        self.assertGreater(successful_writes[0], 50, "Writers did not complete expected writes")
        self.assertGreater(successful_reads[0], 50, "Readers did not execute enough read passes")

    # =========================================================================
    # 3. CONCURRENT NEW SLUG COLLISION HANDLING
    # =========================================================================
    def test_03_concurrent_new_slug_collision_handling(self):
        """
        8 concurrent threads simultaneously race to insert the EXACT SAME new companion slug
        into the same session.
        Verifies:
        - Nested savepoint and exception handling prevents unhandled UniqueConstraint crashes.
        - Exactly 1 record persists in the database.
        """
        session_id = "slug_collision_session"
        target_slug = "adversarial_racing_slug"
        num_threads = 8
        barrier = threading.Barrier(num_threads)
        errors: List[str] = []

        def collision_racer(racer_id: int):
            try:
                barrier.wait(timeout=10.0)
                comp = {
                    "slug": target_slug,
                    "name": f"Racer {racer_id}",
                    "hp": 50 + racer_id,
                    "level": racer_id + 1,
                }
                with db.db_transaction(engine=self.stress_engine, session_id=session_id) as sess:
                    PartyRepository.save_party(
                        sess, [comp], session_id=session_id, mirror_disk=False
                    )
            except Exception as exc:
                errors.append(f"[Racer {racer_id}] Exception: {exc}")

        threads = [threading.Thread(target=collision_racer, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30.0)

        self.assertEqual(errors, [], f"Slug collision crashes: {errors}")

        # Verify only 1 record exists
        with db.db_transaction(engine=self.stress_engine, session_id=session_id) as sess:
            loaded = PartyRepository.load_party(sess, session_id=session_id, seed_from_disk_if_empty=False)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["slug"], target_slug)

    # =========================================================================
    # 4. DISK MIRRORING ISOLATION (CUSTOM SESSION VS DEFAULT SESSION)
    # =========================================================================
    def test_04_disk_mirroring_isolation_custom_session(self):
        """
        Saves party companions in a custom session ('session_test_999').
        Verifies:
        - Root Party/*.json is NEVER created or modified for custom sessions.
        - Existing root files (e.g. Party/companion_ren.json) are untouched.
        """
        session_id = "session_test_999"
        unique_slug = "ghost_companion_custom_test_999"
        root_target_path = os.path.join(PROJECT_ROOT, "Party", f"companion_{unique_slug}.json")
        ren_root_path = os.path.join(PROJECT_ROOT, "Party", "companion_ren.json")

        # Ensure ghost file does not exist before
        if os.path.exists(root_target_path):
            os.remove(root_target_path)

        # Record Ren's current mtime and data
        ren_before = atomic_read_json(ren_root_path)
        ren_before_mtime = os.path.getmtime(ren_root_path)

        custom_party = [
            {"slug": unique_slug, "name": "Ghost Companion", "hp": 999},
            {"slug": "ren", "name": "Ren Mutated", "hp": 77777, "level": 99},
        ]

        with db.db_transaction(engine=self.stress_engine, session_id=session_id) as sess:
            PartyRepository.save_party(
                sess, custom_party, session_id=session_id, mirror_disk=True
            )

        # 1. Assert ghost file was NOT created in root Party/
        self.assertFalse(
            os.path.exists(root_target_path),
            f"Cross-session leakage! Custom session created root file: {root_target_path}",
        )

        # 2. Assert Ren was NOT modified in root Party/
        ren_after = atomic_read_json(ren_root_path)
        self.assertNotEqual(
            ren_after.get("hp"),
            77777,
            "Root companion_ren.json was contaminated with custom session HP 77777!",
        )
        self.assertEqual(
            ren_after.get("hp"),
            ren_before.get("hp"),
            "Root companion_ren.json HP was altered by custom session save!",
        )

    def test_05_disk_mirroring_default_session(self):
        """
        Saves party companions in 'default' session with mirror_disk=True.
        Verifies that root Party/companion_<slug>.json IS updated, and restores it.
        """
        titus_root_path = os.path.join(PROJECT_ROOT, "Party", "companion_titus.json")
        self.assertTrue(os.path.exists(titus_root_path), "Party/companion_titus.json must exist")
        titus_backup = atomic_read_json(titus_root_path)

        try:
            test_hp = 333
            modified_titus = copy.deepcopy(titus_backup)
            modified_titus["hp"] = test_hp

            with db.db_transaction(engine=self.stress_engine, session_id="default") as sess:
                PartyRepository.save_party(
                    sess, [modified_titus], session_id="default", mirror_disk=True
                )

            # Check root file
            titus_disk = atomic_read_json(titus_root_path)
            self.assertEqual(
                titus_disk.get("hp"),
                test_hp,
                "Root companion_titus.json was not updated by default session save!",
            )
        finally:
            # Restore original disk state
            atomic_write_json(titus_root_path, titus_backup)

    def test_06_disk_mirroring_rollback_safety(self):
        """
        Tests that an aborted transaction in 'default' session does NOT execute post-commit
        disk mirroring hooks. Root file must remain unchanged.
        """
        titus_root_path = os.path.join(PROJECT_ROOT, "Party", "companion_titus.json")
        titus_before = atomic_read_json(titus_root_path)

        try:
            with self.assertRaises(RuntimeError):
                with db.db_transaction(engine=self.stress_engine, session_id="default") as sess:
                    modified = copy.deepcopy(titus_before)
                    modified["hp"] = 88888
                    PartyRepository.save_party(
                        sess, [modified], session_id="default", mirror_disk=True
                    )
                    # Force transaction failure
                    raise RuntimeError("Deliberate failure to trigger rollback")
        finally:
            titus_after = atomic_read_json(titus_root_path)
            self.assertEqual(
                titus_after.get("hp"),
                titus_before.get("hp"),
                "Rollback failed to abort post-commit disk mirror! Root file was modified.",
            )

    # =========================================================================
    # 5. ROSTER PRUNING AND EMPTY LIST ISOLATION
    # =========================================================================
    def test_07_roster_pruning_and_empty_list_isolation(self):
        """
        Verifies that pruning companions in session_A does not prune or affect session_B.
        Also verifies saving an empty list [] clears only session_A.
        """
        sess_a = "prune_session_a"
        sess_b = "prune_session_b"

        roster_a = [
            {"slug": "ren", "hp": 30},
            {"slug": "elora", "hp": 40},
        ]
        roster_b = [
            {"slug": "ren", "hp": 30},
            {"slug": "torvald", "hp": 60},
        ]

        with db.db_transaction(engine=self.stress_engine, session_id=sess_a) as sess:
            PartyRepository.save_party(sess, roster_a, session_id=sess_a, mirror_disk=False)
        with db.db_transaction(engine=self.stress_engine, session_id=sess_b) as sess:
            PartyRepository.save_party(sess, roster_b, session_id=sess_b, mirror_disk=False)

        # Prune Elora from session A
        with db.db_transaction(engine=self.stress_engine, session_id=sess_a) as sess:
            PartyRepository.save_party(sess, [{"slug": "ren", "hp": 35}], session_id=sess_a, mirror_disk=False)

        # Check session A
        with db.db_transaction(engine=self.stress_engine, session_id=sess_a) as sess:
            loaded_a = PartyRepository.load_party(sess, session_id=sess_a, seed_from_disk_if_empty=False)
            slugs_a = {c["slug"] for c in loaded_a}
            self.assertEqual(slugs_a, {"ren"})

        # Check session B: torvald must still exist!
        with db.db_transaction(engine=self.stress_engine, session_id=sess_b) as sess:
            loaded_b = PartyRepository.load_party(sess, session_id=sess_b, seed_from_disk_if_empty=False)
            slugs_b = {c["slug"] for c in loaded_b}
            self.assertEqual(slugs_b, {"ren", "torvald"})

        # Save empty list to session A
        with db.db_transaction(engine=self.stress_engine, session_id=sess_a) as sess:
            PartyRepository.save_party(sess, [], session_id=sess_a, mirror_disk=False)

        # Check session A is empty, session B still intact
        with db.db_transaction(engine=self.stress_engine, session_id=sess_a) as sess:
            loaded_a_empty = PartyRepository.load_party(sess, session_id=sess_a, seed_from_disk_if_empty=False)
            self.assertEqual(len(loaded_a_empty), 0)

        with db.db_transaction(engine=self.stress_engine, session_id=sess_b) as sess:
            loaded_b_still = PartyRepository.load_party(sess, session_id=sess_b, seed_from_disk_if_empty=False)
            self.assertEqual(len(loaded_b_still), 2)

    # =========================================================================
    # 6. DUPLICATE SLUGS IN A SINGLE PAYLOAD
    # =========================================================================
    def test_08_duplicate_slugs_in_single_payload(self):
        """
        Adversarially supplies a payload containing two entries for the SAME companion slug.
        Verifies save_party handles this gracefully without IntegrityError and keeps the latter update.
        """
        session_id = "duplicate_payload_session"
        payload = [
            {"slug": "ren", "name": "Ren Early", "hp": 20},
            {"slug": "ren", "name": "Ren Final", "hp": 45, "level": 4},
        ]

        with db.db_transaction(engine=self.stress_engine, session_id=session_id) as sess:
            PartyRepository.save_party(sess, payload, session_id=session_id, mirror_disk=False)

        with db.db_transaction(engine=self.stress_engine, session_id=session_id) as sess:
            loaded = PartyRepository.load_party(sess, session_id=session_id, seed_from_disk_if_empty=False)
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["slug"], "ren")
            self.assertEqual(loaded[0]["hp"], 45)
            self.assertEqual(loaded[0]["level"], 4)

    # =========================================================================
    # 7. LIVE PRODUCTION DB (sao_sandbox.db) VERIFICATION
    # =========================================================================
    def test_09_production_db_multi_session_verification(self):
        """
        Verifies multi-session isolation directly on the default sao_sandbox.db engine.
        Saves distinct companion states in prod_test_sess_1 and prod_test_sess_2,
        asserts total isolation, and cleans up test sessions.
        """
        sess_1 = "prod_adversarial_sess_1"
        sess_2 = "prod_adversarial_sess_2"

        comp_1 = [{"slug": "ren", "name": "Prod Ren 1", "hp": 111}]
        comp_2 = [{"slug": "ren", "name": "Prod Ren 2", "hp": 222}]

        try:
            with db.db_transaction(session_id=sess_1) as sess:
                PartyRepository.save_party(sess, comp_1, session_id=sess_1, mirror_disk=False)

            with db.db_transaction(session_id=sess_2) as sess:
                PartyRepository.save_party(sess, comp_2, session_id=sess_2, mirror_disk=False)

            with db.db_transaction(session_id=sess_1) as sess:
                loaded_1 = PartyRepository.load_party(sess, session_id=sess_1, seed_from_disk_if_empty=False)
                self.assertEqual(len(loaded_1), 1)
                self.assertEqual(loaded_1[0]["hp"], 111)

            with db.db_transaction(session_id=sess_2) as sess:
                loaded_2 = PartyRepository.load_party(sess, session_id=sess_2, seed_from_disk_if_empty=False)
                self.assertEqual(len(loaded_2), 1)
                self.assertEqual(loaded_2[0]["hp"], 222)
        finally:
            # Clean up test sessions
            with db.db_transaction() as sess:
                for s_id in [sess_1, sess_2]:
                    sess.execute(
                        text("DELETE FROM party_companions WHERE session_id = :sid"),
                        {"sid": s_id},
                    )
                    sess.execute(
                        text("DELETE FROM campaign_sessions WHERE session_id = :sid"),
                        {"sid": s_id},
                    )


if __name__ == "__main__":
    unittest.main()
