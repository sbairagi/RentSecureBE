"""Enterprise-grade Nox automation for RentSecure Backend CI pipeline.

Replicates every GitHub Actions workflow job so the entire pipeline
can be validated locally with ``nox -s ci``.
"""

from __future__ import annotations

import nox

# ---------------------------------------------------------------------------
# Shared options
# ---------------------------------------------------------------------------
PYTHON_VERSIONS = ["3.12"]
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
TEST_LOCATIONS = [
    "tests",
    "ci_dashboard/tests.py",
]
COV_SOURCE = [
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

nox.options.sessions = [
    "lint",
    "typing",
    "security",
    "tests",
    "coverage",
    "django-checks",
    "migrations",
    "contracts",
    "architecture",
    "hypothesis",
    "mutation",
    "benchmark",
    "deploy-readiness",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _install_test_deps(session: nox.Session) -> None:
    session.install("-r", "requirements.txt")


def _get_git_python_files(session: nox.Session) -> list[str]:
    """Return tracked Python files, excluding virtualenv/build dirs."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "ls-files"],  # noqa: S607
            cwd=session.invoked_from,
            capture_output=True,
            text=True,
            check=True,
        )
        return [
            f
            for f in result.stdout.splitlines()
            if f.endswith(".py")
            and not any(
                excl in f
                for excl in (
                    ".nox/",
                    ".venv/",
                    "venv/",
                    "site-packages/",
                    "build/",
                    "dist/",
                    "node_modules/",
                    "htmlcov/",
                    ".pytest_cache/",
                    "migrations/",
                    "__pycache__/",
                )
            )
        ]
    except Exception:
        return []


def _run_if_available(session: nox.Session, label: str, cmd: str) -> bool:
    """Run an external binary if it exists on PATH; return True if executed."""
    binary = cmd.split()[0]
    import shutil

    if shutil.which(binary):
        session.run(*cmd.split(), external=True)
        return True
    session.log(f"SKIP: {label} not found on PATH ({binary}).")
    return False


# ---------------------------------------------------------------------------
# Stage 1-2: Lint
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS, name="lint", tags=["quality"])  # type: ignore[misc]
def lint(session: nox.Session) -> None:
    """Run all linting checks: pre-commit, black, ruff, pylint, vulture."""
    _install_test_deps(session)
    session.install("pre-commit")
    session.run("pre-commit", "run", "--all-files")

    session.install("black", "ruff", "pylint", "pylint-django", "vulture")

    session.run(
        "python",
        "-m",
        "black",
        "--check",
        *LOCATIONS,
        env={"PYTHONPATH": str(session.invoked_from), "SKIP_DJANGO_SIGNALS": "1"},
    )
    session.run(
        "python",
        "-m",
        "ruff",
        "check",
        *LOCATIONS,
        env={"PYTHONPATH": str(session.invoked_from)},
    )
    session.run(
        "python",
        "-m",
        "pylint",
        *LOCATIONS,
        env={
            "PYTHONPATH": str(session.invoked_from),
            "SKIP_DJANGO_SIGNALS": "1",
        },
    )
    session.run(
        "python",
        "-m",
        "vulture",
        "--exclude",
        ".venv,venv,build,dist,migrations,__pycache__,.pytest_cache,.github,.kilo,"
        "properties/_legacy,properties/refactored_models_combined.py,"
        "properties/original_models.py,properties/signals,core/signals,"
        "referral_and_earn/signals",
        "--min-confidence",
        "80",
        *LOCATIONS,
    )


# ---------------------------------------------------------------------------
# Autofix
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS, name="autofix", tags=["fix"])  # type: ignore[misc]
def autofix(session: nox.Session) -> None:
    """Auto-fix code quality issues: ruff, black, isort, autoflake, migrations."""
    _install_test_deps(session)

    tracked = _get_git_python_files(session)
    targets = tracked if tracked else LOCATIONS

    session.run(
        "python",
        "-m",
        "autoflake",
        "--in-place",
        "--remove-all-unused-imports",
        "--remove-unused-variables",
        "--ignore-init-module-imports",
        *targets,
    )

    session.run("python", "-m", "ruff", "check", *targets, "--fix")
    session.run("python", "-m", "ruff", "format", *targets)
    session.run("python", "-m", "black", *targets)
    session.run("python", "-m", "isort", *targets)

    session.env["USE_SQLITE"] = "True"
    session.env["SECRET_KEY"] = "nox-autofix-migrations-2026!"  # noqa: S105
    session.env["DEBUG"] = "False"
    session.env["DJANGO_ENV"] = "test"

    try:
        session.run("python", "manage.py", "makemigrations", "--check", "--verbosity=2")
    except nox.command.CommandFailed:
        session.log("Missing migrations detected — generating them safely...")
        session.run("python", "manage.py", "makemigrations", "--verbosity=2")


# ---------------------------------------------------------------------------
# Stage 2d: Type checking
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS, name="typing", tags=["quality"])  # type: ignore[misc]
def typing(session: nox.Session) -> None:
    """Run mypy strict type checking."""
    _install_test_deps(session)
    session.install(
        "mypy", "django-stubs", "django-stubs-ext", "djangorestframework-stubs"
    )
    session.run("python", "-m", "mypy", "--config-file=mypy.ini", ".")


# ---------------------------------------------------------------------------
# Stage 6: Security scans
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS, name="security", tags=["security"])  # type: ignore[misc]
def security(session: nox.Session) -> None:
    """Run bandit, pip-audit, semgrep, gitleaks, trivy."""
    session.install("bandit", "pip-audit")

    session.run(
        "python",
        "-m",
        "bandit",
        "-r",
        *LOCATIONS,
        "-x",
        "*/tests/*,*/test_*.py,*/tests.py,*/migrations/*,.venv,venv,build,dist,.github,.kilo,properties/_legacy,properties/refactored_models_combined.py,properties/original_models.py,management",
    )

    session.run(
        "python",
        "-m",
        "pip_audit",
        "--requirement=requirements.txt",
        "--vulnerability-service=pypi",
        "--ignore-vuln",
        "PYSEC-2022-252",
    )

    _run_if_available(
        session,
        "Semgrep",
        "semgrep scan --config=p/security-audit,p/owasp-top-ten,p/django .",
    )
    _run_if_available(
        session,
        "Trivy",
        "trivy fs --severity CRITICAL,HIGH "
        "--skip-dirs .venv,venv,build,dist,node_modules,.kilo,htmlcov .",
    )
    _run_if_available(
        session, "Gitleaks", "gitleaks detect --source . --report-path gitleaks.sarif"
    )


# ---------------------------------------------------------------------------
# Stage 4a: Django system checks
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS, name="django-checks", tags=["django"])  # type: ignore[misc]
def django_checks(session: nox.Session) -> None:
    """Run Django system checks and deploy validation."""
    _install_test_deps(session)
    session.env["USE_SQLITE"] = "True"
    session.env["SECRET_KEY"] = "nox-django-checks-2026!"  # noqa: S105
    session.env["DEBUG"] = "False"
    session.env["DJANGO_ENV"] = "test"

    session.run("python", "manage.py", "check", "--verbosity=2", "--fail-level=ERROR")
    session.run(
        "python",
        "manage.py",
        "check",
        "--deploy",
        "--verbosity=2",
        "--fail-level=WARNING",
    )
    session.run("python", "manage.py", "diffsettings", "--all")


# ---------------------------------------------------------------------------
# Stage 4b: Migrations
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS, name="migrations", tags=["django"])  # type: ignore[misc]
def migrations(session: nox.Session) -> None:
    """Validate Django system checks, deploy checks, and migrations."""
    _install_test_deps(session)
    session.env["USE_SQLITE"] = "True"
    session.env["SECRET_KEY"] = "nox-migration-check-2026!"  # noqa: S105
    session.env["DEBUG"] = "False"
    session.env["DJANGO_ENV"] = "test"

    session.run("python", "manage.py", "check", "--verbosity=2", "--fail-level=ERROR")
    session.run(
        "python",
        "manage.py",
        "check",
        "--deploy",
        "--verbosity=2",
        "--fail-level=WARNING",
    )
    session.run(
        "python", "manage.py", "makemigrations", "--check", "--dry-run", "--verbosity=2"
    )

    session.run("rm", "-f", "db.sqlite3", external=True)
    session.run("python", "manage.py", "migrate", "--run-syncdb", "--verbosity=2")


# ---------------------------------------------------------------------------
# Stage 3a: Tests
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS, name="tests", tags=["testing"])  # type: ignore[misc]
def tests(session: nox.Session) -> None:
    """Run the full pytest suite."""
    _install_test_deps(session)
    session.run("python", "-m", "pytest", *TEST_LOCATIONS, "-v", "--tb=short")


# ---------------------------------------------------------------------------
# Stage 3a: Coverage
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS, name="coverage", tags=["testing"])  # type: ignore[misc]
def coverage(session: nox.Session) -> None:
    """Run pytest with enforced ≥90% coverage on business-logic packages."""
    _install_test_deps(session)
    session.run(
        "python",
        "-m",
        "pytest",
        *TEST_LOCATIONS,
        f"--cov={','.join(COV_SOURCE)}",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "--cov-fail-under=90",
        "--tb=short",
    )


# ---------------------------------------------------------------------------
# Stage 3c: API Contract tests
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS, name="contracts", tags=["testing"])  # type: ignore[misc]
def contracts(session: nox.Session) -> None:
    """Run API contract tests and schema validation."""
    _install_test_deps(session)
    session.env["USE_SQLITE"] = "True"
    session.env["SECRET_KEY"] = "nox-contract-test-2026!"  # noqa: S105
    session.env["DEBUG"] = "False"
    session.env["DJANGO_ENV"] = "test"

    session.run("python", "manage.py", "migrate", "--run-syncdb", "--verbosity=1")
    session.run(
        "python",
        "-m",
        "pytest",
        "tests/test_api_contracts.py",
        "-v",
        "--tb=short",
        "--randomly-seed=last",
    )
    session.run("python", "scripts/check_api_contracts.py")


# ---------------------------------------------------------------------------
# Stage 5: Architecture guard & import linter
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS, name="architecture", tags=["quality"])  # type: ignore[misc]
def architecture(session: nox.Session) -> None:
    """Run architecture contract validator and import-linter."""
    session.install("pyyaml", "import-linter")

    session.run("python", "scripts/architecture_contract.py", "--verbose")
    session.run("lint-imports", "--config", "import-linter.ini")


# ---------------------------------------------------------------------------
# Stage 3b: Hypothesis property tests
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS, name="hypothesis", tags=["testing"])  # type: ignore[misc]
def hypothesis(session: nox.Session) -> None:
    """Run Hypothesis property-based tests."""
    _install_test_deps(session)
    session.env["USE_SQLITE"] = "True"
    session.env["SECRET_KEY"] = "nox-hypothesis-2026!"  # noqa: S105
    session.env["DEBUG"] = "False"
    session.env["DJANGO_ENV"] = "test"
    session.env["HYPOTHESIS_MAX_EXAMPLES"] = "200"

    session.run(
        "python",
        "-m",
        "pytest",
        "tests/test_properties_hypothesis.py",
        "tests/test_core_hypothesis.py",
        "-v",
        "--hypothesis-show-statistics",
        "--tb=short",
        "--randomly-seed=last",
    )


# ---------------------------------------------------------------------------
# Stage 3d: Mutation testing (mutmut)
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS, name="mutation", tags=["testing"])  # type: ignore[misc]
def mutation(session: nox.Session) -> None:
    """Run mutmut mutation testing."""
    _install_test_deps(session)
    session.install("mutmut")
    session.env["USE_SQLITE"] = "True"
    session.env["SECRET_KEY"] = "nox-mutation-2026!"  # noqa: S105
    session.env["DEBUG"] = "False"
    session.env["DJANGO_ENV"] = "test"

    session.run("python", "manage.py", "migrate", "--run-syncdb", "--verbosity=1")

    session.run(
        "python",
        "-m",
        "mutmut",
        "run",
        "--paths-to-mutate=core/models.py,properties/models/,properties/services/,"
        "properties/utils/,finance/models.py,smartbot/services/,"
        "notification/services/,properties/feature_enforcer.py",
        "--runner=python -m pytest --no-header -q --tb=short --randomly-seed=last -x",
        "--worker=4",
        "--simple-output",
    )


# ---------------------------------------------------------------------------
# Stage 3e: Performance & benchmark
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS, name="benchmark", tags=["performance"])  # type: ignore[misc]
def benchmark(session: nox.Session) -> None:
    """Run pytest-benchmark performance regression suite."""
    _install_test_deps(session)
    session.install("pytest-benchmark")
    session.env["USE_SQLITE"] = "True"
    session.env["SECRET_KEY"] = "nox-bench-2026!"  # noqa: S105
    session.env["DEBUG"] = "False"
    session.env["DJANGO_ENV"] = "test"

    session.run(
        "python",
        "-m",
        "pytest",
        "tests/test_performance_benchmarks.py",
        "-v",
        "--benchmark-only",
        "--benchmark-json=benchmark-results.json",
        "--benchmark-sort=mean",
        "--benchmark-columns=min,max,mean,stddev,median,rounds",
        "--tb=short",
    )


# ---------------------------------------------------------------------------
# Stage 8a: Deploy readiness
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS, name="deploy-readiness", tags=["deploy"])  # type: ignore[misc]
def deploy_readiness(session: nox.Session) -> None:
    """Validate Django deploy readiness: system checks, migrations, collectstatic."""
    _install_test_deps(session)
    session.env["USE_SQLITE"] = "True"
    session.env["SECRET_KEY"] = "nox-deploy-readiness-2026!"  # noqa: S105
    session.env["DEBUG"] = "False"
    session.env["DJANGO_ENV"] = "test"

    session.run("python", "manage.py", "check", "--verbosity=2", "--fail-level=ERROR")
    session.run(
        "python",
        "manage.py",
        "check",
        "--deploy",
        "--verbosity=2",
        "--fail-level=WARNING",
    )
    session.run("rm", "-f", "db.sqlite3", external=True)
    session.run("python", "manage.py", "migrate", "--run-syncdb", "--verbosity=2")
    session.run("python", "manage.py", "collectstatic", "--noinput", "--verbosity=0")


# ---------------------------------------------------------------------------
# CI meta-session: runs EVERYTHING
# ---------------------------------------------------------------------------


@nox.session(python=PYTHON_VERSIONS, name="ci", tags=["ci"])  # type: ignore[misc]
def ci(session: nox.Session) -> None:
    """Run the complete CI pipeline locally.

    Executes every check in dependency order so that ``nox -s ci`` gives
    the same feedback as a full GitHub Actions run.
    """
    lint(session)
    typing(session)
    django_checks(session)
    migrations(session)
    tests(session)
    coverage(session)
    contracts(session)
    architecture(session)
    hypothesis(session)
    mutation(session)
    benchmark(session)
    security(session)
    deploy_readiness(session)
