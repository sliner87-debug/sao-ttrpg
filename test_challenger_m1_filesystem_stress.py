"""
test_challenger_m1_filesystem_stress.py
======================================
Adversarial Verification Suite for Milestone 1: Zero-Byte & Filesystem Stress.
Authored by: Milestone 1 Challenger 2 (teamwork_preview_challenger_m1_2).

Verification Targets:
1. Zero-byte file protection under serialization failures (circular refs, unpicklable objects, I/O errors).
2. Concurrent file writes and reads on Windows under high thread contention (WinError 32 / Errno 13 retry backoff).
3. Transient file locking resilience (antivirus / file indexing contention simulation).
4. Disk mirroring functions schema validation (mirror_character_to_disk, mirror_party_to_disk, mirror_master_state_to_disk).
5. Universal save_game and load_game adapter round-trip fidelity.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from typing import Any, Dict, List, Optional
from unittest.mock import patch

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import backend.database.adapters as adapters
from backend.database.adapters import (
    DEFAULT_INDENT,
    MAX_RETRIES,
    INITIAL_DELAY,
    BACKOFF_FACTOR,
    MAX_DELAY,
    atomic_write_json,
    atomic_read_json,
    mirror_character_to_disk,
    mirror_party_to_disk,
    mirror_master_state_to_disk,
    mirror_world_state_to_disk,
    mirror_staging_ground_to_disk,
    save_game,
    load_game,
    load_world,
    sanitize_character_slug,
)


def compute_file_sha256(file_path: str) -> str:
    """Computes SHA256 hex digest of file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class ExplodingObject:
    """Adversarial object whose stringification or pickling raises an exception."""
    def __init__(self, message: str = "Exploding object triggered!"):
        self.message = message

    def __str__(self) -> str:
        raise TypeError(self.message)

    def __repr__(self) -> str:
        raise TypeError(self.message)


class TestZeroByteAndSerializationFailures(unittest.TestCase):
    """Stress tests verifying that atomic_write_json NEVER creates 0-byte files or corrupts existing files."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="sao_challenger_m1_")
        self.target_file = os.path.join(self.test_dir, "test_save.json")
        self.initial_data = {
            "player": {
                "name": "Glenny",
                "race": "Troll-Kreen Hybrid",
                "class": "Gorgon Barbarian",
                "level": 4,
                "hp": 160,
                "max_hp": 160,
                "col": 2500,
                "equipped": {
                    "main_hand": "Dragonbone Greatclub",
                    "off_hand": "[2H Grip: Dragonbone Greatclub]",
                    "lower_main_hand": "Spiked Buckler",
                    "lower_off_hand": "Empty",
                },
            },
            "messages": [{"role": "system", "content": "You awaken in the Crucible."}],
            "last_saved": time.time(),
        }
        atomic_write_json(self.target_file, self.initial_data)
        self.initial_size = os.path.getsize(self.target_file)
        self.initial_sha256 = compute_file_sha256(self.target_file)
        self.assertGreater(self.initial_size, 0, "Target file must initially be non-zero bytes")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_circular_reference_dict_leaves_destination_file_unmodified(self):
        """Inject circular reference dict into atomic_write_json. Must fail without truncating destination."""
        circular_dict: Dict[str, Any] = {"key": "value"}
        circular_dict["cycle"] = circular_dict

        with self.assertRaises(ValueError) as ctx:
            atomic_write_json(self.target_file, circular_dict)

        self.assertIn("Circular reference detected", str(ctx.exception))
        self.assertTrue(os.path.exists(self.target_file))
        self.assertEqual(
            os.path.getsize(self.target_file),
            self.initial_size,
            "Target file size must be completely preserved",
        )
        self.assertEqual(
            compute_file_sha256(self.target_file),
            self.initial_sha256,
            "Target file SHA256 hash must be identical",
        )
        reloaded = atomic_read_json(self.target_file)
        self.assertEqual(reloaded["player"]["name"], "Glenny")

    def test_circular_reference_list_leaves_destination_file_unmodified(self):
        """Inject circular reference list into atomic_write_json. Must fail without truncating destination."""
        circular_list: List[Any] = [1, 2, 3]
        circular_list.append(circular_list)

        with self.assertRaises(ValueError) as ctx:
            atomic_write_json(self.target_file, circular_list)

        self.assertIn("Circular reference detected", str(ctx.exception))
        self.assertTrue(os.path.exists(self.target_file))
        self.assertEqual(os.path.getsize(self.target_file), self.initial_size)
        self.assertEqual(compute_file_sha256(self.target_file), self.initial_sha256)

    def test_exploding_unpicklable_object_leaves_destination_file_unmodified(self):
        """Inject object whose stringifier raises TypeError. Pre-serialization must abort before touching disk."""
        bad_payload = {
            "player": {"name": "ExplodingHero"},
            "bad_field": ExplodingObject("Simulated un-serializable/unpicklable state"),
        }

        with self.assertRaises(TypeError) as ctx:
            atomic_write_json(self.target_file, bad_payload)

        self.assertIn("Simulated un-serializable/unpicklable state", str(ctx.exception))
        self.assertTrue(os.path.exists(self.target_file))
        self.assertEqual(os.path.getsize(self.target_file), self.initial_size)
        self.assertEqual(compute_file_sha256(self.target_file), self.initial_sha256)

    def test_nonexistent_file_does_not_create_zero_byte_ghost_on_serialization_failure(self):
        """When destination does not exist, serialization error must NOT create a 0-byte orphan file."""
        ghost_path = os.path.join(self.test_dir, "ghost_save.json")
        self.assertFalse(os.path.exists(ghost_path))

        circular_dict: Dict[str, Any] = {"status": "ghost"}
        circular_dict["self"] = circular_dict

        with self.assertRaises(ValueError):
            atomic_write_json(ghost_path, circular_dict)

        self.assertFalse(
            os.path.exists(ghost_path),
            "A 0-byte or corrupted file must NOT be created when serialization fails",
        )

        # Also check for leftover temporary files
        tmp_files = [f for f in os.listdir(self.test_dir) if f.startswith(".ghost_save.json")]
        self.assertEqual(len(tmp_files), 0, "No orphaned temporary files should remain")

    def test_io_failure_during_tempfile_write_leaves_destination_intact(self):
        """Simulate an I/O crash during fsync. Destination must be preserved and temp file cleaned up."""
        with patch("os.fsync", side_effect=OSError("Simulated low-level disk I/O failure (ENOSPC/EIO)")):
            with self.assertRaises(OSError) as ctx:
                atomic_write_json(self.target_file, {"new_state": "should_fail"})

            self.assertIn("Simulated low-level disk I/O failure", str(ctx.exception))

        # Target file must still be completely intact
        self.assertTrue(os.path.exists(self.target_file))
        self.assertEqual(os.path.getsize(self.target_file), self.initial_size)
        self.assertEqual(compute_file_sha256(self.target_file), self.initial_sha256)

        # No temp files should be lingering
        tmp_files = [f for f in os.listdir(self.test_dir) if f.endswith(".tmp")]
        self.assertEqual(len(tmp_files), 0, "Temporary files must be cleaned up in finally block")

    def test_none_file_path_raises_value_error(self):
        """Calling atomic_write_json with None file_path must cleanly raise ValueError."""
        with self.assertRaises(ValueError):
            atomic_write_json(None, {"data": 123})


class TestWindowsConcurrencyAndLockContention(unittest.TestCase):
    """Stress tests hammering atomic_write_json and atomic_read_json across threads to verify retry backoff."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="sao_concurrency_stress_")
        self.shared_file = os.path.join(self.test_dir, "shared_state.json")
        atomic_write_json(self.shared_file, {"version": 0, "writer_id": "init", "payload": "initial"})

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_concurrent_hammer_writes_and_reads(self):
        """
        Hammer shared_state.json with 8 writers and 8 readers concurrently (16 threads total).
        Verify zero WinError 32 or Errno 13 unhandled exceptions, zero 0-byte reads, and 100% valid JSON.
        """
        num_writers = 8
        num_readers = 8
        writes_per_thread = 25
        reads_per_thread = 40

        errors: List[Exception] = []
        zero_byte_reads = 0
        successful_reads = 0
        successful_writes = 0
        lock = threading.Lock()

        stop_event = threading.Event()

        def writer_task(wid: int):
            nonlocal successful_writes
            for i in range(writes_per_thread):
                if stop_event.is_set():
                    break
                payload = {
                    "version": (wid * 1000) + i,
                    "writer_id": f"writer_{wid}",
                    "iteration": i,
                    "timestamp": time.time(),
                    "data": f"Stress payload data from writer {wid} step {i}",
                }
                try:
                    atomic_write_json(self.shared_file, payload)
                    with lock:
                        successful_writes += 1
                except Exception as exc:
                    with lock:
                        errors.append(exc)
                time.sleep(0.005)

        def reader_task(rid: int):
            nonlocal zero_byte_reads, successful_reads
            for _ in range(reads_per_thread):
                if stop_event.is_set():
                    break
                try:
                    data = atomic_read_json(self.shared_file)
                    if data is None:
                        # atomic_read_json returns default (None) if file not readable
                        with lock:
                            zero_byte_reads += 1
                    else:
                        # Verify integrity
                        if not isinstance(data, dict) or "version" not in data:
                            with lock:
                                errors.append(ValueError(f"Corrupt read data: {data}"))
                        else:
                            with lock:
                                successful_reads += 1
                except Exception as exc:
                    with lock:
                        errors.append(exc)
                time.sleep(0.003)

        threads: List[threading.Thread] = []
        for w in range(num_writers):
            t = threading.Thread(target=writer_task, args=(w,))
            threads.append(t)
        for r in range(num_readers):
            t = threading.Thread(target=reader_task, args=(r,))
            threads.append(t)

        # Launch all threads simultaneously
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30.0)

        # Ensure all threads completed
        alive_threads = [t for t in threads if t.is_alive()]
        if alive_threads:
            stop_event.set()
            for t in alive_threads:
                t.join(timeout=5.0)

        self.assertEqual(
            len(alive_threads),
            0,
            f"Some threads deadlocked or timed out: {alive_threads}",
        )
        self.assertEqual(
            len(errors),
            0,
            f"Encountered concurrency errors during hammer test: {errors}",
        )
        self.assertEqual(
            zero_byte_reads,
            0,
            "Observed 0-byte or unreadable file reads during concurrent operations",
        )
        self.assertGreaterEqual(
            successful_writes,
            num_writers * writes_per_thread * 0.9,
            "Writes did not reach expected threshold",
        )
        self.assertGreaterEqual(
            successful_reads,
            num_readers * reads_per_thread * 0.9,
            "Reads did not reach expected threshold",
        )

        # Final check on file integrity
        final_data = atomic_read_json(self.shared_file)
        self.assertIsInstance(final_data, dict)
        self.assertIn("version", final_data)
        self.assertGreater(os.path.getsize(self.shared_file), 0)

    def test_transient_exclusive_read_lock_resilience(self):
        """
        Simulate transient Windows file locks (like Windows Defender or Search Indexer)
        by holding an open file descriptor in a background thread for 30ms bursts while
        calling atomic_write_json. The retry backoff must overcome WinError 32.
        """
        lock_file = os.path.join(self.test_dir, "locked_target.json")
        atomic_write_json(lock_file, {"round": 0, "status": "active"})

        contention_errors: List[Exception] = []
        stop_locking = threading.Event()

        def locker_thread_worker():
            while not stop_locking.is_set():
                try:
                    # Open file on Windows without sharing or holding it open
                    with open(lock_file, "r", encoding="utf-8") as f:
                        _ = f.read()
                        time.sleep(0.03)  # Hold handle for 30ms
                except OSError:
                    pass
                time.sleep(0.01)

        locker = threading.Thread(target=locker_thread_worker)
        locker.start()

        try:
            for round_idx in range(1, 15):
                try:
                    atomic_write_json(
                        lock_file,
                        {"round": round_idx, "timestamp": time.time(), "msg": "survived_lock"},
                        max_retries=10,
                        initial_delay=0.03,
                        backoff_factor=1.5,
                        max_delay=0.4,
                    )
                except Exception as exc:
                    contention_errors.append(exc)
                time.sleep(0.02)
        finally:
            stop_locking.set()
            locker.join(timeout=5.0)

        self.assertEqual(
            len(contention_errors),
            0,
            f"atomic_write_json failed under simulated Windows file locking: {contention_errors}",
        )
        final_read = atomic_read_json(lock_file)
        self.assertEqual(final_read["msg"], "survived_lock")

    def test_concurrent_nested_directory_auto_creation(self):
        """Multiple threads concurrently writing to a new deep directory must not race on os.makedirs."""
        deep_dir = os.path.join(self.test_dir, "deeply", "nested", "saves", "dir")
        self.assertFalse(os.path.exists(deep_dir))

        errors: List[Exception] = []

        def worker(wid: int):
            fpath = os.path.join(deep_dir, f"worker_{wid}.json")
            try:
                atomic_write_json(fpath, {"worker": wid, "success": True})
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)

        self.assertEqual(len(errors), 0, f"Concurrent directory creation produced errors: {errors}")
        for i in range(10):
            fpath = os.path.join(deep_dir, f"worker_{i}.json")
            self.assertTrue(os.path.exists(fpath))
            data = atomic_read_json(fpath)
            self.assertEqual(data["worker"], i)


class TestDiskMirroringFunctionsAndSchemaCompliance(unittest.TestCase):
    """Stress tests validating disk mirroring functions, schema compliance, and slug sanitization."""

    def setUp(self):
        self.test_base_dir = tempfile.mkdtemp(prefix="sao_mirror_test_")
        self.player_state = {
            "name": "Glenny the Undying",
            "gender": "Non-binary",
            "level": 4,
            "race": "Troll-Kreen Hybrid",
            "class": "Gorgon Barbarian",
            "hp": 160,
            "max_hp": 160,
            "col": 5400,
            "location": "Sector 1 Safe-Zone: Washington Borough, NJ",
            "equipped": {
                "head": "Iron Circlet",
                "chest": "Beast Carapace Harness",
                "main_hand": "Dragonbone Greatclub",
                "off_hand": "[2H Grip: Dragonbone Greatclub]",
                "lower_main_hand": "Spiked Buckler",
                "lower_off_hand": "Empty",
                "accessory": "Crucible Vanguard Signet",
            },
            "stats": {"STR": 20, "DEX": 12, "CON": 18, "INT": 8, "WIS": 12, "CHA": 8},
            "grafts": {
                "torso": "basalt_carapace_plating",
                "lower_left_arm": "golem_hydraulic_arm",
            },
            "active_debuffs": [],
        }
        self.messages = [
            {"role": "system", "content": "Crucible initialized."},
            {"role": "user", "content": "I ready my greatclub and shield."},
        ]

    def tearDown(self):
        if os.path.exists(self.test_base_dir):
            shutil.rmtree(self.test_base_dir, ignore_errors=True)

    def test_mirror_character_to_disk_creates_valid_files_and_schema(self):
        """Verify saves/<slug>/save_game.json, profile.json, and root save_game.json match schema."""
        save_path = mirror_character_to_disk(
            self.player_state,
            messages=self.messages,
            base_dir=self.test_base_dir,
            mirror_to_root=True,
        )

        slug = "Glenny_the_Undying"
        char_dir = os.path.join(self.test_base_dir, "saves", slug)
        expected_save = os.path.join(char_dir, "save_game.json")
        expected_profile = os.path.join(char_dir, "profile.json")
        expected_root = os.path.join(self.test_base_dir, "save_game.json")

        self.assertEqual(save_path, expected_save)
        self.assertTrue(os.path.exists(expected_save))
        self.assertTrue(os.path.exists(expected_profile))
        self.assertTrue(os.path.exists(expected_root))

        # 1. Validate character save file schema
        save_data = atomic_read_json(expected_save)
        self.assertIn("player", save_data)
        self.assertIn("messages", save_data)
        self.assertIn("last_saved", save_data)
        self.assertEqual(save_data["player"]["name"], "Glenny the Undying")
        self.assertEqual(
            save_data["player"]["equipped"]["off_hand"],
            "[2H Grip: Dragonbone Greatclub]",
        )
        self.assertEqual(len(save_data["messages"]), 2)

        # 2. Validate profile.json manifest schema
        profile_data = atomic_read_json(expected_profile)
        for req_field in [
            "name", "slug", "gender", "level", "race", "class",
            "hp", "hp_cur", "hp_max", "col", "location", "equipped",
            "turns_logged", "unique_url", "last_saved",
        ]:
            self.assertIn(req_field, profile_data, f"profile.json missing required field: {req_field}")
        self.assertEqual(profile_data["name"], "Glenny the Undying")
        self.assertEqual(profile_data["slug"], slug)
        self.assertEqual(profile_data["level"], 4)
        self.assertEqual(profile_data["turns_logged"], 2)

        # 3. Validate root save_game.json
        root_data = atomic_read_json(expected_root)
        self.assertEqual(root_data["player"]["name"], "Glenny the Undying")

    def test_mirror_character_slug_sanitization_edge_cases(self):
        """Verify that unusual character names are safely sanitized for filesystem directories."""
        test_cases = [
            ("Kirito / Asuna <3", "Kirito__Asuna_3"),
            ("   Spaces   Everywhere   ", "Spaces___Everywhere"),
            ("Special!@#$%^&*()_+={}|[]\\;:'\",.<>?/Chars", "Special_Chars"),
            ("", "Survivor"),
            (None, "Survivor"),
            ("   ", "Survivor"),
            ("日本語Anomaly", "Anomaly"),
        ]

        for input_name, expected_slug in test_cases:
            slug = sanitize_character_slug(input_name)
            self.assertEqual(slug, expected_slug, f"Failed for input: {input_name}")

            # Verify directory creation with sanitized slug succeeds without OS error
            state = dict(self.player_state)
            state["name"] = input_name
            save_file = mirror_character_to_disk(
                state, base_dir=self.test_base_dir, mirror_to_root=False
            )
            self.assertTrue(os.path.exists(save_file))
            self.assertTrue(os.path.getsize(save_file) > 0)

    def test_mirror_character_purges_master_state_player(self):
        """Verify extra_meta containing master_state with 'player' has 'player' stripped to prevent circular loops."""
        meta = {
            "master_state": {
                "player": {"circular_risk": True},
                "gm_secret": "Crucible Core Active",
            }
        }
        mirror_character_to_disk(
            self.player_state,
            extra_meta=meta,
            base_dir=self.test_base_dir,
            mirror_to_root=False,
        )
        save_path = os.path.join(self.test_base_dir, "saves", "Glenny_the_Undying", "save_game.json")
        saved_data = atomic_read_json(save_path)
        self.assertIn("master_state", saved_data)
        self.assertNotIn(
            "player",
            saved_data["master_state"],
            "master_state.player must be purged to prevent circular state leaks",
        )
        self.assertEqual(saved_data["master_state"]["gm_secret"], "Crucible Core Active")

    def test_mirror_party_to_disk_handles_both_list_and_dict(self):
        """Verify mirror_party_to_disk correctly writes companion sheets for both list and dict inputs."""
        companions_list = [
            {"id": "companion_ren", "name": "Ren Sasaki", "hp": 45, "max_hp": 45, "role": "Vanguard Scout"},
            {"id": "companion_titus", "name": "Titus Sterling", "hp": 110, "max_hp": 110, "weight_lbs": 1200},
        ]

        # 1. List input with slug and root mirroring
        mirror_party_to_disk(
            companions_list,
            slug="Glenny_the_Undying",
            base_dir=self.test_base_dir,
            mirror_to_root=True,
        )

        root_ren = os.path.join(self.test_base_dir, "Party", "companion_ren.json")
        root_titus = os.path.join(self.test_base_dir, "Party", "companion_titus.json")
        root_ent_ren = os.path.join(self.test_base_dir, "Entities", "companion_ren.json")
        slug_ren = os.path.join(self.test_base_dir, "saves", "Glenny_the_Undying", "Party", "companion_ren.json")
        slug_titus = os.path.join(self.test_base_dir, "saves", "Glenny_the_Undying", "Party", "companion_titus.json")
        slug_ent_ren = os.path.join(self.test_base_dir, "saves", "Glenny_the_Undying", "Entities", "companion_ren.json")

        for p in [root_ren, root_titus, root_ent_ren, slug_ren, slug_titus, slug_ent_ren]:
            self.assertTrue(os.path.exists(p), f"Expected companion file missing: {p}")
            data = atomic_read_json(p)
            self.assertIn("name", data)

        # 2. Dict input
        companions_dict = {
            "ren": {"id": "companion_ren", "name": "Ren Sasaki", "hp": 50, "max_hp": 50},
        }
        mirror_party_to_disk(
            companions_dict,
            slug="Glenny_the_Undying",
            base_dir=self.test_base_dir,
            mirror_to_root=False,
        )
        ren_updated = atomic_read_json(slug_ren)
        self.assertEqual(ren_updated["hp"], 50)

    def test_mirror_master_state_to_disk_purges_player_and_creates_dir(self):
        """Verify mirror_master_state_to_disk creates .game_state dir and strips 'player' key."""
        m_state = {
            "player": {"name": "ShouldNotBeHere"},
            "world_seed": 9999,
            "anomaly_bleed_pct": 42.5,
        }
        mirror_master_state_to_disk(m_state, base_dir=self.test_base_dir)

        m_file = os.path.join(self.test_base_dir, ".game_state", "secret_master_state.json")
        self.assertTrue(os.path.exists(m_file))
        saved = atomic_read_json(m_file)
        self.assertNotIn("player", saved)
        self.assertEqual(saved["world_seed"], 9999)
        self.assertEqual(saved["anomaly_bleed_pct"], 42.5)

    def test_mirror_world_state_and_staging_ground_to_disk(self):
        """Verify world_state.json and Staging_Ground JSONs are created properly."""
        w_state = {"sector": 1, "world_status": "CRUCIBLE: ACTIVE", "global_news": ["Floor 1 unsealed."]}
        mirror_world_state_to_disk(w_state, base_dir=self.test_base_dir)
        w_file = os.path.join(self.test_base_dir, "world_state.json")
        self.assertTrue(os.path.exists(w_file))
        self.assertEqual(atomic_read_json(w_file)["world_status"], "CRUCIBLE: ACTIVE")

        vr = {"room_id": "nexus_vault", "name": "The Nexus Vault", "entities": []}
        aq = [{"actor": "companion_ren", "action": "stealth_recon"}]
        mirror_staging_ground_to_disk(visible_room=vr, action_queue=aq, base_dir=self.test_base_dir)

        vr_file = os.path.join(self.test_base_dir, "Staging_Ground", "visible_room.json")
        aq_file = os.path.join(self.test_base_dir, "Staging_Ground", "action_queue.json")
        self.assertTrue(os.path.exists(vr_file))
        self.assertTrue(os.path.exists(aq_file))
        self.assertEqual(atomic_read_json(vr_file)["room_id"], "nexus_vault")
        self.assertEqual(len(atomic_read_json(aq_file)), 1)

    def test_universal_save_game_and_load_game_adapter_round_trip(self):
        """Verify save_game adapter executes atomic disk mirroring and load_game recovers identical state."""
        save_path = save_game(
            self.player_state,
            messages=self.messages,
            session_id="test_challenger_session",
            base_dir=self.test_base_dir,
        )
        self.assertTrue(os.path.exists(save_path))

        loaded = load_game(save_path, base_dir=self.test_base_dir)
        self.assertEqual(loaded["player"]["name"], "Glenny the Undying")
        self.assertEqual(
            loaded["player"]["equipped"]["main_hand"],
            "Dragonbone Greatclub",
        )
        self.assertEqual(len(loaded["messages"]), 2)

        # Verify chat backup was also created
        chat_backup = os.path.join(self.test_base_dir, "chat_history_backup.json")
        self.assertTrue(os.path.exists(chat_backup))
        self.assertEqual(len(atomic_read_json(chat_backup)), 2)


if __name__ == "__main__":
    unittest.main()
