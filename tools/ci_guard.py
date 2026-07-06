#!/usr/bin/env python3
"""CI Guard — central orchestrator for local CI validation.

Runs code quality, security, migration, and test gates programmatically.
Designed to be imported by ``ship.py`` or run standalone.
"""

from __future__ import annotations

import subprocess
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent

MANAGE_PY = "manage.py"
PYTEST_TB_SHORT = "--tb=short"  # nosonar


@dataclass
class CheckResult:
    name: str
    passed: bool
    command: str
    duration: float = 0.0
    error: str | None = None
    skipped: bool = False
    results: list[dict] = field(default_factory=list)


def _run(cmd: Sequence[str] | str, **kwargs: Any) -> tuple[bool, str, float]:
    if isinstance(cmd, str):
        cmd = cmd.split()
    start = time.time()
    result = subprocess.run(  # noqa: S603
        cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        **kwargs,
    )
    duration = time.time() - start
    output = result.stderr or result.stdout or ""
    return result.returncode == 0, output, duration


def run_lint() -> CheckResult:
    print("[ci] lint ...")
    start = time.time()
    try:
        subprocess.run(
            [sys.executable, "-m", "pre_commit", "run", "--all-files"],
            cwd=REPO_ROOT,
            check=True,
        )  # noqa: S603
    except subprocess.CalledProcessError as e:
        return CheckResult(
            name="lint",
            passed=False,
            command="pre-commit run --all-files",
            duration=time.time() - start,
            error=str(e),
        )
    return CheckResult(
        name="lint",
        passed=True,
        command="pre-commit run --all-files",
        duration=time.time() - start,
    )


def run_typing() -> CheckResult:
    print("[ci] typing (mypy) ...")
    cmd = [sys.executable, "-m", "mypy", "--config-file=mypy.ini", "."]
    ok, out, dur = _run(cmd)
    return CheckResult(
        name="typing",
        passed=ok,
        command=" ".join(cmd),
        duration=dur,
        error=out[:500] if not ok else None,
    )


def run_security() -> CheckResult:
    from tools.security_guard import run_all

    print("[ci] security ...")
    start = time.time()
    results = run_all()
    failed = [r for r in results if not r.passed and not r.skipped]
    return CheckResult(
        name="security",
        passed=len(failed) == 0,
        command="security_guard.run_all",
        duration=time.time() - start,
        error=(
            "; ".join(f"{r.name}: {(r.error or "")[:100]}" for r in failed)
            if failed
            else None
        ),
        results=[r.__dict__ for r in results],
    )


def run_tests() -> CheckResult:
    print("[ci] tests (pytest) ...")
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests",
        "ci_dashboard/tests.py",
        "-v",
        PYTEST_TB_SHORT,
    ]
    ok, out, dur = _run(cmd)
    return CheckResult(
        name="tests",
        passed=ok,
        command=" ".join(cmd),
        duration=dur,
        error=out[:500] if not ok else None,
    )


def run_coverage() -> CheckResult:
    print("[ci] coverage ...")
    cov_source = [
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
    ]
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests",
        "ci_dashboard/tests.py",
        *[f"--cov={pkg}" for pkg in cov_source],
        "--cov-report=term-missing",
        "--cov-report=xml",
        "--cov-fail-under=90",
        PYTEST_TB_SHORT,
    ]
    ok, out, dur = _run(cmd)
    return CheckResult(
        name="coverage",
        passed=ok,
        command=" ".join(cmd),
        duration=dur,
        error=out[:500] if not ok else None,
    )


def run_django_checks() -> CheckResult:
    print("[ci] django-checks ...")
    env = {
        "USE_SQLITE": "True",
        "SECRET_KEY": "ci-guard-django-2026!",
        "DEBUG": "False",
        "DJANGO_ENV": "test",
    }
    ok1, out1, d1 = _run(
        [sys.executable, MANAGE_PY, "check", "--fail-level=ERROR"], env=env
    )
    ok2, out2, d2 = _run(
        [sys.executable, MANAGE_PY, "check", "--deploy", "--fail-level=WARNING"],
        env=env,
    )
    ok = ok1 and ok2
    return CheckResult(
        name="django-checks",
        passed=ok,
        command="manage.py check + manage.py check --deploy",
        duration=d1 + d2,
        error=(out1 or out2)[:500] if not ok else None,
    )


def run_migrations() -> CheckResult:
    from tools.migration_guard import run_all

    print("[ci] migrations ...")
    start = time.time()
    results = run_all()
    failed = [r for r in results if not r.passed]
    return CheckResult(
        name="migrations",
        passed=len(failed) == 0,
        command="migration_guard.run_all",
        duration=time.time() - start,
        error=(
            "; ".join(f"{r.name}: {(r.error or "")[:100]}" for r in failed)
            if failed
            else None
        ),
        results=[r.__dict__ for r in results],
    )


def run_contracts() -> CheckResult:
    print("[ci] contracts ...")
    env = {
        "USE_SQLITE": "True",
        "SECRET_KEY": "ci-guard-contracts-2026!",
        "DEBUG": "False",
        "DJANGO_ENV": "test",
    }
    ok1, out1, d1 = _run(
        [sys.executable, MANAGE_PY, "migrate", "--run-syncdb", "--verbosity=1"],
        env=env,
    )
    ok2, out2, d2 = _run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_api_contracts.py",
            "-v",
            PYTEST_TB_SHORT,
            "--randomly-seed=last",
        ]
    )
    ok3, out3, d3 = _run([sys.executable, "scripts/check_api_contracts.py"])
    ok = ok1 and ok2 and ok3
    return CheckResult(
        name="contracts",
        passed=ok,
        command="pytest test_api_contracts.py + check_api_contracts.py",
        duration=d1 + d2 + d3,
        error=(out1 or out2 or out3)[:500] if not ok else None,
    )


def run_architecture() -> CheckResult:
    print("[ci] architecture ...")
    env = {"PYTHONPATH": str(REPO_ROOT)}
    ok1, out1, d1 = _run(
        [sys.executable, "scripts/architecture_contract.py", "--verbose"], env=env
    )
    ok2, out2, d2 = _run(["lint-imports", "--config", "import-linter.ini"])
    ok = ok1 and ok2
    return CheckResult(
        name="architecture",
        passed=ok,
        command="architecture_contract.py + lint-imports",
        duration=d1 + d2,
        error=(out1 or out2)[:500] if not ok else None,
    )


def run_hypothesis() -> CheckResult:
    print("[ci] hypothesis ...")
    env = {
        "USE_SQLITE": "True",
        "SECRET_KEY": "ci-guard-hypothesis-2026!",
        "DEBUG": "False",
        "DJANGO_ENV": "test",
        "HYPOTHESIS_MAX_EXAMPLES": "200",
    }
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_properties_hypothesis.py",
        "tests/test_core_hypothesis.py",
        "-v",
        "--hypothesis-show-statistics",
        PYTEST_TB_SHORT,
        "--randomly-seed=last",
    ]
    ok, out, dur = _run(cmd, env=env)
    return CheckResult(
        name="hypothesis",
        passed=ok,
        command=" ".join(cmd),
        duration=dur,
        error=out[:500] if not ok else None,
    )


def run_benchmark() -> CheckResult:
    print("[ci] benchmark ...")
    env = {
        "USE_SQLITE": "True",
        "SECRET_KEY": "ci-guard-bench-2026!",
        "DEBUG": "False",
        "DJANGO_ENV": "test",
    }
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_performance_benchmarks.py",
        "-v",
        "--benchmark-only",
        "--benchmark-json=benchmark-results.json",
        "--benchmark-sort=mean",
        "--benchmark-columns=min,max,mean,stddev,median,rounds",
        PYTEST_TB_SHORT,
    ]
    ok, out, dur = _run(cmd, env=env)
    return CheckResult(
        name="benchmark",
        passed=ok,
        command=" ".join(cmd),
        duration=dur,
        error=out[:500] if not ok else None,
    )


def run_mutation() -> CheckResult:
    print("[ci] mutation ...")
    env = {
        "USE_SQLITE": "True",
        "SECRET_KEY": "ci-guard-mutation-2026!",
        "DEBUG": "False",
        "DJANGO_ENV": "test",
    }
    _run(
        [sys.executable, MANAGE_PY, "migrate", "--run-syncdb", "--verbosity=1"],
        env=env,
    )
    cmd = [
        sys.executable,
        "-m",
        "mutmut",
        "run",
        "--paths-to-mutate=core/models.py,properties/models/,properties/services/,"
        "properties/utils/,finance/models.py,smartbot/services/,"
        "notification/services/,properties/feature_enforcer.py",
        "--runner=python -m pytest --no-header -q --tb=short "
        "--randomly-seed=last -x",  # nosonar
        "--worker=4",
        "--simple-output",
    ]
    ok, out, dur = _run(cmd)
    return CheckResult(
        name="mutation",
        passed=ok,
        command=" ".join(cmd),
        duration=dur,
        error=out[:500] if not ok else None,
    )


def run_deploy_readiness() -> CheckResult:
    print("[ci] deploy-readiness ...")
    env = {
        "USE_SQLITE": "True",
        "SECRET_KEY": "ci-guard-deploy-2026!",
        "DEBUG": "False",
        "DJANGO_ENV": "test",
    }
    ok1, out1, d1 = _run(
        [sys.executable, MANAGE_PY, "check", "--fail-level=ERROR"], env=env
    )
    ok2, out2, d2 = _run(
        [sys.executable, MANAGE_PY, "check", "--deploy", "--fail-level=WARNING"],
        env=env,
    )
    ok3, out3, d3 = _run(
        [sys.executable, MANAGE_PY, "migrate", "--run-syncdb", "--verbosity=2"],
        env=env,
    )
    ok4, out4, d4 = _run(
        [sys.executable, MANAGE_PY, "collectstatic", "--noinput", "--verbosity=0"],
        env=env,
    )
    ok = ok1 and ok2 and ok3 and ok4
    return CheckResult(
        name="deploy-readiness",
        passed=ok,
        command="manage.py check + deploy check + migrate + collectstatic",
        duration=d1 + d2 + d3 + d4,
        error=(out1 or out2 or out3 or out4)[:500] if not ok else None,
    )


GATES = [
    ("lint", run_lint),
    ("typing", run_typing),
    ("security", run_security),
    ("tests", run_tests),
    ("coverage", run_coverage),
    ("django-checks", run_django_checks),
    ("migrations", run_migrations),
    ("contracts", run_contracts),
    ("architecture", run_architecture),
    ("hypothesis", run_hypothesis),
    ("mutation", run_mutation),
    ("benchmark", run_benchmark),
    ("deploy-readiness", run_deploy_readiness),
]


def run_all() -> list[CheckResult]:
    results: list[CheckResult] = []
    for name, fn in GATES:
        try:
            result = fn()
        except Exception as e:
            result = CheckResult(
                name=name,
                passed=False,
                command=name,
                error=str(e),
            )
        results.append(result)
        status = "PASS" if result.passed else "FAIL"
        print(f"[ci] {result.name}: {status} ({result.duration:.2f}s)")
    return results
