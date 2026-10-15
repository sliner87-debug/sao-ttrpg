"""
Runner script for Milestone 3 Challenger 1 test execution.
Executes:
1. test_challenger_m3_1_party_concurrency_stress.py
2. test_audit_all_phases.py
3. test_v2_integration.py
Logs full execution transcript to .agents/teamwork/teamwork_preview_challenger_m3_1/test_output.log
"""

import os
import subprocess
import sys
import time

LOG_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    ".agents", "teamwork", "teamwork_preview_challenger_m3_1", "test_output.log"
))

SUITES = [
    ("Milestone 3 Adversarial Concurrency & Stress Suite", "test_challenger_m3_1_party_concurrency_stress.py"),
    ("Core Audit All Phases Suite (Phases 1-8)", "test_audit_all_phases.py"),
    ("Core V2 Integration Suite (Phases 9-13)", "test_v2_integration.py"),
]

def main():
    print(f"Executing Challenger M3.1 Test Suites. Output will be written to {LOG_PATH}")
    start_time = time.time()
    
    with open(LOG_PATH, "w", encoding="utf-8") as log_file:
        log_file.write("======================================================================\n")
        log_file.write("SAO SANDBOX V2 — MILESTONE 3 CHALLENGER 1 EMPIRICAL TEST EXECUTION LOG\n")
        log_file.write(f"Start Time: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
        log_file.write("======================================================================\n\n")
        
        all_passed = True
        
        for name, script in SUITES:
            log_file.write(f"\n>>> RUNNING: {name} ({script})\n")
            log_file.write("-" * 70 + "\n")
            log_file.flush()
            print(f">>> Running: {name} ({script}) ...", flush=True)
            
            s_start = time.time()
            res = subprocess.run(
                [sys.executable, script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__)),
            )
            s_elapsed = time.time() - s_start
            
            log_file.write(res.stdout)
            log_file.write(f"\n[RESULT] Exit Code: {res.returncode} | Elapsed: {s_elapsed:.2f}s\n")
            log_file.flush()
            
            if res.returncode == 0:
                print(f"    PASSED ({s_elapsed:.2f}s)", flush=True)
            else:
                print(f"    FAILED (code {res.returncode}, {s_elapsed:.2f}s)", flush=True)
                all_passed = False
                
        total_elapsed = time.time() - start_time
        log_file.write("\n======================================================================\n")
        log_file.write(f"OVERALL SUMMARY: {'ALL SUITES PASSED (100%)' if all_passed else 'SOME SUITES FAILED'}\n")
        log_file.write(f"Total Execution Time: {total_elapsed:.2f}s\n")
        log_file.write("======================================================================\n")
        
    print(f"\nCompleted in {total_elapsed:.2f}s. Verdict: {'ALL PASSED' if all_passed else 'FAILURE'}")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
