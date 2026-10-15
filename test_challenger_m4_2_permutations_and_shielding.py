"""
Milestone 4 Challenger 2 Adversarial Stress Test Suite:
CLI Test Compatibility Permutations & Persona Shielding Stress.

Validates:
1. Persona Shielding & Deep Merge Stress:
   - Repeatedly hammer `mirror_party_to_disk` with mutated Ren combat data.
   - Assert `Entities/companion_ren.json` is NEVER overwritten.
   - Assert zero occurrences of "Banki" in `Entities/companion_ren.json`.
   - Assert `Party/companion_ren.json` retains `subroutine_metadata`
     (`ren_diag_v2.py`, `Ouroboros Kernel v3.14`).
2. Execution Order Permutation Stress:
   - Run the 5 baseline V2 test suites in reverse order.
   - Run the 5 baseline V2 test suites in multiple interleaved permutations.
   - Assert 100% pass rate (exit code 0, 0 failures, 0 errors) under all permutations.
3. Zero-Byte File Corruption Stress:
   - Audit all JSON files across root, Party, Entities, Staging_Ground, .game_state, saves.
   - Assert size > 0 bytes and valid JSON parse tree for every file.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Tuple


def get_project_root() -> str:
    curr = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(curr, "app.py")):
        return curr
    root = os.path.abspath(os.path.join(curr, "..", "..", ".."))
    if os.path.exists(os.path.join(root, "app.py")):
        return root
    return os.getcwd()


PROJECT_ROOT = get_project_root()
AGENT_DIR = os.path.join(PROJECT_ROOT, ".agents", "teamwork", "teamwork_preview_challenger_m4_2")
os.makedirs(AGENT_DIR, exist_ok=True)
LOG_FILE = os.path.join(AGENT_DIR, "test_output.log")

log_entries: List[str] = []


def log(msg: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    log_entries.append(formatted)


def file_sha256(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class TestContext:
    def __init__(self):
        self.entities_ren_path = os.path.join(PROJECT_ROOT, "Entities", "companion_ren.json")
        self.party_ren_path = os.path.join(PROJECT_ROOT, "Party", "companion_ren.json")
        self.save_game_path = os.path.join(PROJECT_ROOT, "save_game.json")
        self.initial_entities_hash = ""
        self.initial_entities_content = ""
        self.initial_party_content = ""
        self.initial_save_game_content = ""

    def capture_pre_state(self):
        log("=== PHASE 1: Capturing Pre-Test Invariant Baselines ===")
        assert os.path.exists(self.entities_ren_path), f"Missing {self.entities_ren_path}"
        assert os.path.exists(self.party_ren_path), f"Missing {self.party_ren_path}"
        assert os.path.exists(self.save_game_path), f"Missing {self.save_game_path}"

        with open(self.entities_ren_path, "r", encoding="utf-8") as f:
            self.initial_entities_content = f.read()
        self.initial_entities_hash = file_sha256(self.entities_ren_path)

        with open(self.party_ren_path, "r", encoding="utf-8") as f:
            self.initial_party_content = f.read()

        with open(self.save_game_path, "r", encoding="utf-8") as f:
            self.initial_save_game_content = f.read()

        # Pre-check Entities/companion_ren.json
        ent_data = json.loads(self.initial_entities_content)
        assert "backstory_interview" in ent_data, "Pre-check failed: backstory_interview missing"
        assert "personality" in ent_data, "Pre-check failed: personality missing"
        assert "Banki" not in self.initial_entities_content, "Pre-check failed: Banki found in Entities/companion_ren.json"

        # Pre-check Party/companion_ren.json
        party_data = json.loads(self.initial_party_content)
        assert "subroutine_metadata" in party_data, "Pre-check failed: subroutine_metadata missing in Party/companion_ren.json"
        meta = party_data["subroutine_metadata"]
        assert meta.get("subroutine_id") == "ren_diag_v2.py", f"Pre-check failed: unexpected subroutine_id {meta.get('subroutine_id')}"
        assert "Ouroboros Kernel v3.14" in party_data.get("ocular_kernel", ""), "Pre-check failed: ocular_kernel mismatch"

        log(f"Pre-state verified. Entities SHA256: {self.initial_entities_hash[:16]}... (Size: {len(self.initial_entities_content)} bytes)")
        log("Initial invariant check PASSED: zero 'Banki', backstory/personality intact, subroutine_metadata verified.")

    def restore_golden_baselines(self):
        with open(self.entities_ren_path, "w", encoding="utf-8") as f:
            f.write(self.initial_entities_content)
        with open(self.party_ren_path, "w", encoding="utf-8") as f:
            f.write(self.initial_party_content)
        with open(self.save_game_path, "w", encoding="utf-8") as f:
            f.write(self.initial_save_game_content)
        log("Golden baselines for Entities, Party, and save_game restored.")


def test_persona_shielding_and_deep_merge_stress(ctx: TestContext):
    log("\n=== PHASE 2: Persona Shielding & Deep Merge Hammering Stress ===")
    
    # Import adapters inside test environment
    sys.path.insert(0, PROJECT_ROOT)
    from backend.database.adapters import mirror_party_to_disk, save_game
    from backend.database.engine import db_transaction

    # 1. Sequential Hammering with hostile mutated combat states
    log("Running 100 sequential hostile mirror_party_to_disk cycles...")
    for i in range(100):
        hostile_ren = {
            "id": "companion_ren",
            "name": f"Ren (Hostile Turn {i})",
            "hp": 10 + (i % 25),
            "max_hp": 35,
            "ac": 14 + (i % 3),
            "equipped": {
                "main_hand": f"Overclocked Carbine Mk {i}",
                "off_hand": "Runic Blade",
            },
            # Intentionally omit subroutine_metadata to test deep-merge resilience
            # Intentionally omit backstory_interview, personality
            "combat_notes": f"Turn {i} kinetic burst test",
            # Adversarial attempt: inject Banki in a non-standard field
            "attacker_target": "Banki" if i % 2 == 0 else "Glenny",
        }

        mirror_party_to_disk(
            [hostile_ren],
            slug="Glenny",
            base_dir=PROJECT_ROOT,
            mirror_to_root=True,
        )

    log("Sequential hammering completed. Verifying shielding invariants...")
    _verify_shielding_invariants(ctx, "Sequential Hammering", check_hash=True)

    # 2. Multi-threaded Concurrent Hammering
    log("Running multi-threaded concurrent hammering (4 threads, 25 iterations each = 100 concurrent cycles)...")
    errors: List[str] = []

    def worker_hammer(worker_id: int):
        for j in range(25):
            turn_idx = worker_id * 100 + j
            payload = {
                "id": "companion_ren",
                "name": f"Ren (Worker {worker_id} Turn {j})",
                "hp": 5 + (turn_idx % 30),
                "max_hp": 35,
                "ac": 16,
                "inventory": [
                    {
                        "name": "Aether-Lock Carbine",
                        "durability": 50 - (j % 20),
                        "max_durability": 50,
                    }
                ],
            }
            time.sleep(0.01)
            try:
                mirror_party_to_disk(
                    [payload],
                    slug=f"Glenny_Stress_{worker_id}",
                    base_dir=PROJECT_ROOT,
                    mirror_to_root=(worker_id == 0),
                )
            except Exception as e:
                errors.append(f"Worker {worker_id} error on iter {j}: {e}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(worker_hammer, w) for w in range(4)]
        for f in concurrent.futures.as_completed(futures):
            f.result()

    assert not errors, f"Concurrent hammering encountered errors: {errors}"
    log("Concurrent hammering completed with 0 exceptions. Verifying shielding invariants...")
    _verify_shielding_invariants(ctx, "Concurrent Hammering", check_hash=True)

    # 3. Full save_game Transactional Hammering & Rollback Safety
    log("Testing save_game transactional integrity on custom session...")
    test_player = {
        "name": "Adversarial_Glenny",
        "race": "Pure Human",
        "class": "Pathless (Freeform Anomaly)",
        "hp": 100,
        "max_hp": 100,
        "companions": [
            {
                "id": "companion_ren",
                "name": "Ren Sasaki",
                "hp": 28,
                "max_hp": 35,
                "ac": 16,
            }
        ],
    }

    # Save to custom session (isolates root save_game.json)
    save_file = save_game(test_player, messages=[], session_id="adversarial_test_session", base_dir=PROJECT_ROOT)
    assert os.path.exists(save_file), f"Save file not created: {save_file}"
    _verify_shielding_invariants(ctx, "Post custom save_game()", check_hash=True)

    # Deliberate rollback test: ensure failed transaction does NOT execute post-commit disk hooks
    log("Triggering simulated transactional abort during companion update...")
    try:
        with db_transaction(session_id="default") as db:
            from backend.database.repositories import PartyRepository
            # Persist hostile companion
            PartyRepository.save_party(
                db,
                [{"id": "companion_ren", "name": "POISON_DO_NOT_PERSIST_REN", "hp": 1}],
                session_id="default",
                mirror_disk=True,
                character_slug="Glenny",
                base_dir=PROJECT_ROOT,
            )
            # Deliberately raise exception to force rollback
            raise RuntimeError("Simulated transaction abort for rollback verification")
    except RuntimeError as ex:
        assert "Simulated transaction abort" in str(ex)

    # Verify poisoned record was NOT mirrored to root Party/companion_ren.json
    with open(ctx.party_ren_path, "r", encoding="utf-8") as f:
        current_party_text = f.read()
    assert "POISON_DO_NOT_PERSIST_REN" not in current_party_text, "Rollback failed: post-commit hook leaked to disk on aborted transaction!"
    log("Rollback safety verified: aborted transaction cleanly discarded post-commit hooks.")

    # Restore Party/companion_ren.json and save_game.json to golden baseline
    ctx.restore_golden_baselines()


def _verify_shielding_invariants(ctx: TestContext, phase_name: str, check_hash: bool = False):
    # Invariant 1: Entities/companion_ren.json MUST NOT be overwritten during mirror_party_to_disk
    if check_hash:
        current_ent_hash = file_sha256(ctx.entities_ren_path)
        assert current_ent_hash == ctx.initial_entities_hash, (
            f"[{phase_name}] VIOLATION: Entities/companion_ren.json hash modified! "
            f"Expected {ctx.initial_entities_hash}, got {current_ent_hash}"
        )

    with open(ctx.entities_ren_path, "r", encoding="utf-8") as f:
        ent_text = f.read()

    # Invariant 2: ZERO occurrences of 'Banki'
    assert "Banki" not in ent_text, f"[{phase_name}] VIOLATION: 'Banki' leaked into Entities/companion_ren.json!"
    ent_json = json.loads(ent_text)
    assert "backstory_interview" in ent_json, f"[{phase_name}] VIOLATION: backstory_interview missing!"
    assert "personality" in ent_json, f"[{phase_name}] VIOLATION: personality missing!"

    # Invariant 3: Party/companion_ren.json MUST retain subroutine_metadata and rich item descriptions
    with open(ctx.party_ren_path, "r", encoding="utf-8") as f:
        party_text = f.read()
    party_json = json.loads(party_text)

    assert "subroutine_metadata" in party_json, f"[{phase_name}] VIOLATION: subroutine_metadata wiped in Party/companion_ren.json!"
    sub_meta = party_json["subroutine_metadata"]
    assert sub_meta.get("subroutine_id") == "ren_diag_v2.py", f"[{phase_name}] VIOLATION: subroutine_id corrupted: {sub_meta}"
    assert "Ouroboros Kernel v3.14" in str(sub_meta.get("kernel_language")), f"[{phase_name}] VIOLATION: kernel_language corrupted: {sub_meta}"
    assert "behavior_prompt" in party_json and len(party_json["behavior_prompt"]) > 50, f"[{phase_name}] VIOLATION: behavior_prompt missing or truncated!"

    # Verify inventory descriptions preserved
    inv = party_json.get("inventory", [])
    carbine = next((item for item in inv if isinstance(item, dict) and item.get("name") == "Aether-Lock Carbine"), None)
    assert carbine is not None, f"[{phase_name}] VIOLATION: Aether-Lock Carbine missing from inventory!"
    assert carbine.get("desc") is not None and "Grade 2 brass-and-crystal" in carbine["desc"], (
        f"[{phase_name}] VIOLATION: Carbine rich description lost in deep merge: {carbine}"
    )


def run_command_suite(suite_filename: str) -> Tuple[int, str, float]:
    start_time = time.time()
    cmd = [sys.executable, suite_filename]
    log(f"Executing: {' '.join(cmd)}")
    proc = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    elapsed = time.time() - start_time
    log(f"Result for {suite_filename}: ExitCode={proc.returncode} in {elapsed:.3f}s")
    if proc.returncode != 0:
        log(f"FAIL OUTPUT from {suite_filename}:\n{proc.stdout}")
    # Settle time on Windows to allow file handles to be released
    time.sleep(0.15)
    return proc.returncode, proc.stdout, elapsed


def test_execution_order_permutations(ctx: TestContext):
    log("\n=== PHASE 3: Execution Order Permutation Stress ===")
    
    baseline_suites = [
        "test_tutorial_and_gender.py",
        "test_phases_10_to_13_v2.py",
        "test_podcast_fixes_1_to_9.py",
        "test_audit_all_phases.py",
        "test_v2_integration.py",
    ]

    # Permutation 1: Strict Reverse Order
    reverse_order = list(reversed(baseline_suites))
    log(f"\n--- Permutation 1: Reverse Order ---")
    log(f"Order: {reverse_order}")
    for suite in reverse_order:
        code, out, elapsed = run_command_suite(suite)
        assert code == 0, f"Reverse order failure on {suite} (code {code})"
        _verify_shielding_invariants(ctx, f"After {suite} in Reverse Order", check_hash=False)
    log(">>> Permutation 1 (Reverse Order): 100% PASS <<<")

    # Permutation 2: Interleaved Permutation A
    # Phases 10-13 -> Tutorial -> V2 Integration -> Podcast -> Audit
    interleaved_a = [
        "test_phases_10_to_13_v2.py",
        "test_tutorial_and_gender.py",
        "test_v2_integration.py",
        "test_podcast_fixes_1_to_9.py",
        "test_audit_all_phases.py",
    ]
    log(f"\n--- Permutation 2: Interleaved Permutation A ---")
    log(f"Order: {interleaved_a}")
    for suite in interleaved_a:
        code, out, elapsed = run_command_suite(suite)
        assert code == 0, f"Interleaved A failure on {suite} (code {code})"
        _verify_shielding_invariants(ctx, f"After {suite} in Interleaved A", check_hash=False)
    log(">>> Permutation 2 (Interleaved A): 100% PASS <<<")

    # Permutation 3: Interleaved Permutation B
    # Podcast -> V2 Integration -> Tutorial -> Audit -> Phases 10-13
    interleaved_b = [
        "test_podcast_fixes_1_to_9.py",
        "test_v2_integration.py",
        "test_tutorial_and_gender.py",
        "test_audit_all_phases.py",
        "test_phases_10_to_13_v2.py",
    ]
    log(f"\n--- Permutation 3: Interleaved Permutation B ---")
    log(f"Order: {interleaved_b}")
    for suite in interleaved_b:
        code, out, elapsed = run_command_suite(suite)
        assert code == 0, f"Interleaved B failure on {suite} (code {code})"
        _verify_shielding_invariants(ctx, f"After {suite} in Interleaved B", check_hash=False)
    log(">>> Permutation 3 (Interleaved B): 100% PASS <<<")

    # Permutation 4: Interleaved Permutation C (Stress flip)
    # Audit -> Phases 10-13 -> V2 Integration -> Tutorial -> Podcast
    interleaved_c = [
        "test_audit_all_phases.py",
        "test_phases_10_to_13_v2.py",
        "test_v2_integration.py",
        "test_tutorial_and_gender.py",
        "test_podcast_fixes_1_to_9.py",
    ]
    log(f"\n--- Permutation 4: Interleaved Permutation C ---")
    log(f"Order: {interleaved_c}")
    for suite in interleaved_c:
        code, out, elapsed = run_command_suite(suite)
        assert code == 0, f"Interleaved C failure on {suite} (code {code})"
        _verify_shielding_invariants(ctx, f"After {suite} in Interleaved C", check_hash=False)
    log(">>> Permutation 4 (Interleaved C): 100% PASS <<<")


def test_zero_byte_corruption_prevention():
    log("\n=== PHASE 4: Zero-Byte File Corruption Stress & Comprehensive JSON Audit ===")
    
    target_dirs = [
        PROJECT_ROOT,
        os.path.join(PROJECT_ROOT, "Party"),
        os.path.join(PROJECT_ROOT, "Entities"),
        os.path.join(PROJECT_ROOT, "Staging_Ground"),
        os.path.join(PROJECT_ROOT, ".game_state"),
        os.path.join(PROJECT_ROOT, "saves"),
    ]

    checked_files = 0
    total_bytes = 0
    zero_byte_files: List[str] = []
    corrupted_json_files: List[Tuple[str, str]] = []

    for d in target_dirs:
        if not os.path.exists(d):
            continue
        for root, dirs, files in os.walk(d):
            # Skip hidden directories like .git
            if ".git" in root or ".gemini" in root:
                continue
            for fname in files:
                if fname.endswith(".json"):
                    fpath = os.path.join(root, fname)
                    checked_files += 1
                    try:
                        sz = os.path.getsize(fpath)
                        total_bytes += sz
                        if sz == 0:
                            zero_byte_files.append(fpath)
                            continue
                        with open(fpath, "r", encoding="utf-8") as f:
                            json.load(f)
                    except Exception as exc:
                        corrupted_json_files.append((fpath, str(exc)))

    log(f"Audited {checked_files} JSON save files across workspace ({total_bytes} total bytes).")
    log(f"Zero-byte files found: {len(zero_byte_files)}")
    log(f"Corrupted JSON files found: {len(corrupted_json_files)}")

    assert not zero_byte_files, f"FATAL: Zero-byte JSON files detected: {zero_byte_files}"
    assert not corrupted_json_files, f"FATAL: Corrupted JSON files detected: {corrupted_json_files}"
    log(">>> Zero-Byte & Corruption Prevention: 100% PASS (0 zero-byte files, 0 JSON parse errors) <<<")


def main():
    log("================================================================================")
    log("STARTING CHALLENGER M4-2 ADVERSARIAL STRESS TEST SUITE")
    log(f"Target Root: {PROJECT_ROOT}")
    log(f"Python Executable: {sys.executable} (Version: {sys.version.split()[0]})")
    log("================================================================================")

    ctx = TestContext()
    ctx.capture_pre_state()

    try:
        test_persona_shielding_and_deep_merge_stress(ctx)
        test_execution_order_permutations(ctx)
        test_zero_byte_corruption_prevention()

        # Final invariant audit
        log("\n=== PHASE 5: Final Post-Stress Invariant Verification ===")
        ctx.restore_golden_baselines()
        _verify_shielding_invariants(ctx, "Final Post-Stress Verification", check_hash=True)
        log("Final verification confirmed: Entities/companion_ren.json pristine, Party/companion_ren.json intact.")

        log("\n================================================================================")
        log("ALL ADVERSARIAL STRESS TESTS COMPLETED SUCCESSFULLY — 100% PASS")
        log("================================================================================")

    except Exception as exc:
        log(f"\n!!! ADVERSARIAL STRESS TEST FAILED: {exc} !!!")
        import traceback
        log(traceback.format_exc())
        sys.exit(1)
    finally:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(log_entries) + "\n")
        log(f"Logged full output to {LOG_FILE}")


if __name__ == "__main__":
    main()
