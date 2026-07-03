#!/usr/bin/env python3
"""One Command CI Guard System for RentSecure Backend.

Usage:
    python tools/ship.py

Workflow:
    STEP 1  Auto Fix
    STEP 2  Full Local CI via Nox
    STEP 3  Generate Report
    STEP 4  Block Exit If Any Failure Exists
    STEP 5  Success Message
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def banner(title: str) -> None:
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)


def step_autofix() -> bool:
    banner("STEP 1 / 5 — AUTO FIX")
    result = subprocess.run(  # noqa: S603
        [sys.executable, "tools/autofix.py"],
        cwd=REPO_ROOT,
    )  # noqa: S603
    return result.returncode == 0


def step_full_ci() -> bool:
    banner("STEP 2 / 5 — FULL LOCAL CI")
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "nox", "-s", "ci"],
        cwd=REPO_ROOT,
    )  # noqa: S603
    return result.returncode == 0


def step_generate_report() -> None:
    banner("STEP 3 / 5 — GENERATE REPORT")
    from tools.ci_guard import run_all
    from tools.report_generator import ReportGenerator

    print("[ship] collecting gate results ...")
    results_raw = run_all()
    results = [r.__dict__ for r in results_raw]

    generator = ReportGenerator(results, repo_root=REPO_ROOT)
    out = generator.save(REPO_ROOT / "reports")
    print(f"[ship] report saved to: {out}")
    generator.print_summary()


def step_block_or_proceed(full_ci_passed: bool) -> int:
    banner("STEP 4 / 5 — GATE DECISION")
    if not full_ci_passed:
        print()
        print("  ❌ CI FAILED — push blocked.")
        print("  Fix the failures above before committing.")
        print()
        return 1
    print()
    print("  ✅ CI passed — no blockers.")
    return 0


def step_success() -> None:
    banner("STEP 5 / 5 — READY")
    print()
    print("  ✅✅✅  ALL CHECKS PASSED  ✅✅✅")
    print()
    print("  Your code is ready to commit and push.")
    print("  CI on GitHub Actions has a very high probability of passing.")
    print()


def main() -> int:
    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║                                                                  ║")
    print("║          🔒  RENTSECURE — ONE COMMAND CI GUARD  🔒          ║")
    print("║                                                                  ║")
    print("╚══════════════════════════════════════════════════════════════════╝")

    autofix_passed = step_autofix()
    if not autofix_passed:
        banner("STEP 4 / 5 — GATE DECISION")
        print()
        print("  ❌ AUTO-FIX FAILED — push blocked.")
        print("  Review the fixed files and resolve remaining issues manually.")
        return 1

    full_ci_passed = step_full_ci()

    # Always generate a fresh report in both pass and fail cases
    step_generate_report()

    exit_code = step_block_or_proceed(full_ci_passed)
    if exit_code == 0:
        step_success()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
