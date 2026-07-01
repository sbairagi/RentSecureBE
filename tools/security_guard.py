#!/usr/bin/env python3
"""Security scanning orchestrator for RentSecure Backend.

Wraps bandit, pip-audit, semgrep, gitleaks, and trivy with graceful
handling for missing external binaries.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCATIONS = [
    "rentsecure_be",
    "ai_assistant",
    "core",
    "dashboard",
    "documents",
    "finance",
    "notification",
    "properties",
    "referral_and_earn",
    "smartbot",
    "scripts",
]


@dataclass
class SecurityResult:
    name: str
    passed: bool
    command: str
    duration: float = 0.0
    error: str | None = None
    skipped: bool = False


def _run(cmd: Sequence[str], **kwargs: Any) -> tuple[bool, str]:
    result = subprocess.run(  # noqa: S603
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, **kwargs
    )
    return result.returncode == 0, (result.stderr or result.stdout or "")


def check_bandit() -> SecurityResult:
    print("[security] bandit (SAST) ...")
    cmd = [
        sys.executable,
        "-m",
        "bandit",
        "-r",
        *LOCATIONS,
        "-x",
        "*/tests/*,*/test_*.py,*/tests.py,*/migrations/*,.venv,venv,build,dist,.github,.kilo,properties/_legacy,properties/refactored_models_combined.py,properties/original_models.py,management",
    ]
    ok, out = _run(cmd)
    return SecurityResult(
        name="bandit",
        passed=ok,
        command=" ".join(cmd),
        error=out[:500] if not ok else None,
    )


def check_pip_audit() -> SecurityResult:
    print("[security] pip-audit (dependency vulnerability) ...")
    cmd = [
        sys.executable,
        "-m",
        "pip_audit",
        "--requirement=requirements.txt",
        "--vulnerability-service=pypi",
        "--ignore-vuln",
        "PYSEC-2022-252",
    ]
    ok, out = _run(cmd)
    return SecurityResult(
        name="pip-audit",
        passed=ok,
        command=" ".join(cmd),
        error=out[:500] if not ok else None,
    )


def check_semgrep() -> SecurityResult:
    print("[security] semgrep (SAST) ...")
    if not shutil.which("semgrep"):
        return SecurityResult(
            name="semgrep",
            passed=True,
            command="semgrep ...",
            skipped=True,
        )
    cmd = [
        "semgrep",
        "scan",
        "--config=p/security-audit,p/owasp-top-ten,p/django",
        ".",
    ]
    ok, out = _run(cmd)
    return SecurityResult(
        name="semgrep",
        passed=ok,
        command=" ".join(cmd),
        error=out[:500] if not ok else None,
    )


def check_trivy() -> SecurityResult:
    print("[security] trivy (filesystem scan) ...")
    if not shutil.which("trivy"):
        return SecurityResult(
            name="trivy",
            passed=True,
            command="trivy ...",
            skipped=True,
        )
    cmd = [
        "trivy",
        "fs",
        "--severity",
        "CRITICAL,HIGH",
        "--skip-dirs",
        ".venv,venv,build,dist,node_modules,.kilo,htmlcov",
        ".",
    ]
    ok, out = _run(cmd)
    return SecurityResult(
        name="trivy",
        passed=ok,
        command=" ".join(cmd),
        error=out[:500] if not ok else None,
    )


def check_gitleaks() -> SecurityResult:
    print("[security] gitleaks (secret scanning) ...")
    if not shutil.which("gitleaks"):
        return SecurityResult(
            name="gitleaks",
            passed=True,
            command="gitleaks ...",
            skipped=True,
        )
    cmd = ["gitleaks", "detect", "--source", ".", "--report-path", "gitleaks.sarif"]
    ok, out = _run(cmd)
    return SecurityResult(
        name="gitleaks",
        passed=ok,
        command=" ".join(cmd),
        error=out[:500] if not ok else None,
    )


def run_all() -> list[SecurityResult]:
    results: list[SecurityResult] = []
    for fn in (
        check_bandit,
        check_pip_audit,
        check_semgrep,
        check_trivy,
        check_gitleaks,
    ):
        result = fn()
        results.append(result)
        status = "PASS" if result.passed else ("SKIP" if result.skipped else "FAIL")
        print(f"[security] {result.name}: {status}")
    return results


def main() -> int:
    print("=" * 80)
    print("  SECURITY GUARD — RentSecure Backend")
    print("=" * 80)
    results = run_all()
    failed = [r for r in results if not r.passed and not r.skipped]
    print()
    if failed:
        print(f"  ❌ {len(failed)} security check(s) failed.")
        for r in failed:
            print(f"     - {r.name}: {r.error[:120] if r.error else 'unknown'}")
        return 1
    print("  ✅ All security checks passed (or skipped due to missing binary).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
