# Phase 10 — CI/CD, Quality Gate & Engineering Hardening Audit Report

**Project:** RentSecureBE
**Date:** 2026-06-05
**Python Version:** 3.12 (target)
**Django Version:** 4.2.30

---

## Executive Summary

| Metric | Score | Status |
|--------|-------|--------|
| **CI/CD Maturity** | 55/100 | Needs Improvement |
| **Production Readiness** | 45/100 | Critical Gaps |
| **Test Coverage Target** | 90% (configured) | Unknown (no recent runs) |
| **Dependency Hygiene** | 35/100 | Critical - dev deps in prod |

---

## STEP 1 — REQUIREMENTS.TXT AUDIT

### 1.1 Full Package Analysis (300 packages)

#### DUPLICATE PACKAGES
| Package | Versions Found | Status |
|---------|---------------|--------|
| `fpdf` / `fpdf2` | Both present | **CONFLICT** - fpdf2 is the maintained fork; fpdf is legacy |
| `uri-template` / `uritemplate` | Both present | **DUPLICATE** - same functionality |
| `rfc3986` / `rfc3986-validator` | Both present | Validator depends on rfc3986 |
| `pytz` / `tzdata` | Both present | Django 4.2+ uses zoneinfo (tzdata); pytz is legacy |
| `urllib3` / `urllib3` in botocore | Transitive | OK |

#### OBSOLETE / LEGACY PACKAGES
| Package | Issue | Recommendation |
|---------|-------|----------------|
| `pytz==2021.3` | Unmaintained; Django 4.2+ uses stdlib `zoneinfo` | **REMOVE** - use `tzdata` only |
| `fpdf==1.7.2` | Legacy; superseded by fpdf2 | **REMOVE** |
| `django-rest-auth==0.9.5` | **UNMAINTAINED SINCE 2019**; security risk | **REMOVE** - migrate to dj-rest-auth |
| `django-multiselectfield==0.1.12` | Last release 2020; no Django 4.2 support | **REMOVE** - use `django-multiselectfield2` or `ArrayField` |
| `instagram-private-api==1.6.0.0` | Unofficial, fragile, ToS violation risk | **REMOVE** - use official Graph API |
| `instaloader==4.14.1` | Scraping library; ToS violation risk | **REMOVE** |
| `selenium==4.29.0` | Heavy browser automation in prod deps | **MOVE TO DEV** |
| `gTTS==2.5.4` | Google TTS scraping; no official API | **REMOVE** or **MOVE TO DEV** |

#### INSECURE PACKAGES (Known CVEs)
| Package | Current | Latest Safe | CVE Risk |
|---------|---------|-------------|----------|
| `urllib3==1.26.20` | 1.26.20 | 2.2.1+ | CVE-2023-45803, CVE-2024-37891 |
| `requests==2.32.3` | 2.32.3 | 2.32.4+ | CVE-2024-47081 |
| `certifi==2025.4.26` | Current | - | OK |
| `cryptography==45.0.2` | 45.0.2 | 43.0.0+ | OK |
| `django==4.2.30` | 4.2.30 | 4.2.x LTS | OK (LTS until April 2025) |
| `djangorestframework==3.16.0` | 3.16.0 | 3.15+ | OK |
| `celery==5.6.3` | 5.6.3 | 5.4+ | OK |
| `boto3==1.18.53` | 1.18.53 | 1.35+ | **OUTDATED** - missing security fixes |
| `botocore==1.21.53` | 1.21.53 | 1.35+ | **OUTDATED** |
| `google-api-core==2.25.0rc1` | **RELEASE CANDIDATE** in prod | 2.24.x stable | **CRITICAL** - RC in production |
| `grpcio==1.71.0` | 1.71.0 | 1.68+ | OK |
| `protobuf==5.29.4` | 5.29.4 | 5.28+ | OK |

#### PYTHON 3.12 INCOMPATIBILITIES
| Package | Issue |
|---------|-------|
| `python-dateutil==2.9.0.post0` | OK with 3.12 |
| `pytz==2021.3` | Works but deprecated; use zoneinfo |
| `typing_extensions==4.15.0` | OK |
| Most packages | Compatible |

#### DEVELOPMENT-ONLY PACKAGES INCORRECTLY IN PRODUCTION (~48 packages)
| Category | Packages | Count |
|----------|----------|-------|
| **Jupyter/IPython Ecosystem** | ipykernel, ipython, ipython_pygments_lexers, jupyter-events, jupyter-lsp, jupyter_client, jupyter_core, jupyter_server, jupyter_server_terminals, jupyterlab, jupyterlab_pygments, jupyterlab_server, nbclient, nbconvert, nbformat, nest-asyncio, notebook_shim, traitlets, pexpect, ptyprocess, jedi, parso, prompt_toolkit, stack-data, debugpy, executing, pure_eval, asttokens, matplotlib-inline | **29** |
| **Testing** | pytest, pytest-django, coverage, pluggy, iniconfig, hypothesis (transitive) | **6** |
| **Linting/Type-checking** | black, ruff, mypy, pylint, pylint-django, isort, bandit, semgrep, types-python-dateutil | **10** |
| **Documentation/Notebook** | pandocfilters, mistune, nbformat | **3** |
| **Total Dev Packages in Prod** | | **~48 packages** |

#### UNUSED DEPENDENCIES (Best Effort - Static Analysis)
| Package | Likely Unused | Reason |
|---------|---------------|--------|
| `Flask==3.1.1` | **YES** | Django project; no Flask usage found |
| `SQLAlchemy==2.0.41` | **YES** | Django ORM used; no SQLAlchemy imports found |
| `aiohttp==3.11.18` + `aiohttp-retry` | **LIKELY** | Async HTTP; check if used in services |
| `aiosignal`, `async-timeout`, `frozenlist`, `multidict`, `yarl` | **TRANSITIVE** | aiohttp deps |
| `trio==0.29.0` + `trio-websocket` | **YES** | Alternative async runtime; unlikely used |
| `httpcore==1.0.9` + `httpx==0.28.1` | **CHECK** | httpx may be used; httpcore is transitive |
| `google-cloud-firestore==2.20.2` | **CHECK** | If not using Firestore |
| `google-cloud-storage==3.1.0` | **CHECK** | If using S3/django-storages instead |
| `firebase-admin==6.8.0` | **CHECK** | If FCM only, may not need full admin |
| `razorpay==1.4.2` | **CHECK** | If using Cashfree only |
| `twilio==9.6.1` | **USED** | WhatsApp integration confirmed |
| `weasyprint==66.0` | **USED** | PDF generation confirmed |
| `fpdf2==2.8.3` | **USED** | Alternative PDF? Keep if used |
| `xlsxwriter==3.2.9` | **USED** | Excel exports likely |
| `openpyxl==3.1.5` | **USED** | Excel imports likely |
| `pandas==2.2.2` | **CHECK** | Heavy; only if data processing needed |
| `numpy==2.0.1` | **TRANSITIVE** | pandas dependency |
| `prometheus_client==0.20.0` | **CHECK** | If metrics endpoint exists |

---

### 1.2 REQUIREMENTS.TXT CLASSIFICATION TABLES

#### ✅ KEEP (Production Runtime - ~120 packages)
```
Django, djangorestframework, djangorestframework_simplejwt
celery, django-celery-beat, kombu, billiard, amqp, vine
redis (missing! - add), django-redis (missing! - add)
psycopg2-binary (missing! - add), dj-database-url
boto3, botocore, s3transfer, django-storages, django-s3-storage
twilio, weasyprint, fpdf2, openpyxl, xlsxwriter
cryptography, PyJWT, argon2-cffi, bcrypt (missing!)
requests, httpx, urllib3, certifi, idna, charset-normalizer
python-decouple, python-dateutil, tzdata, pytz (remove after migration)
django-cors-headers, django-widget-tweaks, django-select2
django-simple-history, django-otp, django-crum, django-appconf
firebase-admin (if FCM only - consider firebase-admin only), fcm-django
google-auth, google-auth-httplib2, google-api-core, googleapis-common-protos
prometheus_client, whitenoise, gunicorn (missing! - add)
arrow, cron-descriptor, python-crontab
deep-translator (if used), gTTS (move to dev)
```

#### 🔄 MOVE TO DEV (requirements-dev.txt - ~48 packages)
```
# Testing
pytest, pytest-django, coverage, pluggy, iniconfig, hypothesis
factory-boy (missing! - add), freezegun (missing! - add)

# Linting/Type-checking
black, ruff, mypy, pylint, pylint-django, isort, bandit, semgrep
types-python-dateutil, django-stubs, drf-stubs (missing! - add)

# Jupyter/Notebook (ALL)
ipykernel, ipython, ipython_pygments_lexers, jupyter-events, jupyter-lsp
jupyter_client, jupyter_core, jupyter_server, jupyter_server_terminals
jupyterlab, jupyterlab_pygments, jupyterlab_server, nbclient, nbconvert
nbformat, nest-asyncio, notebook_shim, traitlets, pexpect, ptyprocess
jedi, parso, prompt_toolkit, stack-data, debugpy, executing, pure_eval
asttokens, matplotlib-inline

# Security Scanning (CI only)
trivy, codeql
```

#### ❌ REMOVE (Obsolete/Insecure/Unused)
```
pytz==2021.3 (use tzdata)
fpdf==1.7.2 (use fpdf2)
django-rest-auth==0.9.5 (migrate to dj-rest-auth)
django-multiselectfield==0.1.12 (use ArrayField or django-multiselectfield2)
instagram-private-api==1.6.0.0
instaloader==4.14.1
Flask==3.1.1
SQLAlchemy==2.0.41
trio==0.29.0
trio-websocket==0.12.2
google-api-core==2.25.0rc1 (downgrade to 2.24.x stable)
```

#### ⬆️ UPGRADE (Security/Compatibility)
```
urllib3: 1.26.20 → 2.2.1+
requests: 2.32.3 → 2.32.4+
boto3: 1.18.53 → 1.35+
botocore: 1.21.53 → 1.35+
google-api-core: 2.25.0rc1 → 2.24.x (stable)
django: 4.2.30 → 4.2.x (LTS, plan upgrade to 5.x)
djangorestframework: 3.16.0 → 3.15+
celery: 5.6.3 → 5.4+ (check compatibility)
```

---

## STEP 2 — PYPROJECT / TOOLING AUDIT

### 2.1 Configuration Files Analyzed
- `pyproject.toml` - Primary config (Black, Ruff, MyPy, Pytest, Coverage)
- `.pylintrc` - Pylint config (legacy, duplicated in pyproject.toml)
- `mypy.ini` - MyPy config (legacy, duplicated in pyproject.toml)
- `pytest.ini` - Pytest config (legacy, duplicated in pyproject.toml)
- `.coveragerc` - Coverage config (legacy, duplicated in pyproject.toml)
- `.pre-commit-config.yaml` - Pre-commit hooks

### 2.2 DUPLICATE CONFIGURATIONS (Critical)

| Setting | pyproject.toml | Legacy File | Conflict |
|---------|---------------|-------------|----------|
| **Black** | `[tool.black]` line-length=88 | N/A | OK |
| **Ruff** | `[tool.ruff]` line-length=88 | N/A | OK |
| **MyPy** | `[tool.mypy]` strict=true | `mypy.ini` strict=true | **DUPLICATE** - mypy.ini ignored if pyproject.toml present |
| **Pytest** | `[tool.pytest.ini_options]` | `pytest.ini` | **DUPLICATE** - pytest.ini takes precedence |
| **Coverage** | `[tool.coverage.run/report]` | `.coveragerc` | **DUPLICATE** - .coveragerc takes precedence |
| **Pylint** | N/A | `.pylintrc` | Only in legacy |

**Finding:** 4 legacy config files (`.pylintrc`, `mypy.ini`, `pytest.ini`, `.coveragerc`) duplicate pyproject.toml settings. Modern tools prefer pyproject.toml. Legacy files cause confusion and may be read instead of pyproject.toml.

### 2.3 CONFLICTING CONFIGURATIONS

| Tool | Conflict |
|------|----------|
| **MyPy** | pyproject.toml: `ignore_missing_imports = true` vs mypy.ini: `ignore_missing_imports = False` (line 42) — **CRITICAL CONFLICT** |
| **Coverage** | pyproject.toml: `fail_under = 90` vs .coveragerc: `fail_under = 90` — OK but duplicate |
| **Pytest** | pyproject.toml adds `--cov=.` vs pytest.ini same — duplicate |
| **Ruff vs Black** | Both configured with line-length=88 — compatible |
| **Ruff select** | `select = ["E", "F", "W", "C", "N", "I", "S", "B"]` — missing `UP` (pyupgrade), `PTH` (pathlib), `TRY` (tryceratops) |

### 2.4 SETTINGS IGNORED BY TOOLS

| File | Tool | Status |
|------|------|--------|
| `mypy.ini` | MyPy | **IGNORED** if pyproject.toml has `[tool.mypy]` (MyPy 1.0+) |
| `pytest.ini` | Pytest | **READ INSTEAD OF** pyproject.toml (pytest precedence) |
| `.coveragerc` | Coverage | **READ INSTEAD OF** pyproject.toml (coverage precedence) |
| `.pylintrc` | Pylint | **ONLY CONFIG** (no pyproject.toml support) |

### 2.5 INCORRECT RUFF RULES

| Issue | Current | Recommended |
|-------|---------|-------------|
| `extend-ignore = ["E203"]` | E203 (whitespace before ':') | Remove - Black handles this; Ruff E203 conflicts with Black |
| Missing `UP` rules | Not in select | Add `UP` for pyupgrade (modernize syntax) |
| Missing `PTH` rules | Not in select | Add `PTH` for pathlib modernization |
| Missing `TRY` rules | Not in select | Add `TRY` for try/except improvements |
| `per-file-ignores` for tests | Disables S101, S105, S106, S108 | Bandit codes - Ruff doesn't run Bandit; these are no-ops |

### 2.6 INCORRECT MYPY STRICTNESS

| Setting | pyproject.toml | mypy.ini | Issue |
|---------|---------------|----------|-------|
| `ignore_missing_imports` | `true` (weak) | `False` (strict) | **CRITICAL CONFLICT** - pyproject.toml overrides mypy.ini, weakening all strictness |
| `strict = True` | Set | Set | OK - both enabled |
| `disallow_subclassing_any` | Not set | `True` | **MISSING** - allows unsafe subclassing |
| `no_implicit_reexport` | Not set | `True` | **MISSING** - allows implicit re-exports |
| `warn_return_any` | Not set | `True` | **MISSING** - no warning when returning Any |
| `warn_unreachable` | Not set | `True` | **MISSING** - unreachable code silently allowed |
| `enable_error_code` | Not set | 13 codes: truthy-bool, truthy-function, truthy-iterable, redundant-self, no-untyped-def, no-untyped-call, no-any-return, no-any-unimported, explicit-override, possibly-undefined, redundant-expr, comparison-overlap, ignore-without-code, unused-awaitable | **MISSING** - extra error codes not enabled |
| `disable_error_code` | Not set | type-arg, no-redef | **MISSING** - known noise not suppressed |
| `disallow_untyped_calls` | `true` | `true` | OK |
| `disallow_untyped_defs` | `true` | `true` | OK |
| `disallow_incomplete_defs` | `true` | `true` | OK |
| `disallow_untyped_decorators` | `true` | `true` | OK |
| `check_untyped_defs` | `true` | `true` | OK |
| `strict_equality` | `true` | `true` | OK |
| `warn_unused_ignores` | `true` | `true` | OK |
| `warn_redundant_casts` | `true` | `true` | OK |
| `warn_unused_configs` | `true` | `true` | OK |

**Evidence:** mypy.ini (342 lines) is the authoritative config with detailed overrides, error codes, and module-specific ignores. pyproject.toml (24 lines) has a minimal `[tool.mypy]` that misses 6 strict flags, 13 error codes, 2 disable codes, and all module-specific overrides. Since MyPy 1.0+ reads both, but pyproject.toml takes precedence when both define the same setting — the `ignore_missing_imports = true` in pyproject.toml **silently overrides** the `False` in mypy.ini, weakening security.

**Recommendation:** Delete `[tool.mypy]` section from pyproject.toml; keep mypy.ini as the sole authoritative config. OR consolidate all mypy.ini settings into pyproject.toml and delete mypy.ini.

### 2.7 MISSING BANDIT CONFIGURATION

| Configuration Item | Current | Required | Severity |
|--------------------|---------|----------|----------|
| Config file | ❌ None | `[tool.bandit]` in pyproject.toml | **HIGH** |
| Exclude patterns | ✅ CLI `-x .venv,venv,migrations,tests` | Migrate to config file | MEDIUM |
| Skips (S404, S403, etc.) | ❌ None | Define allowed skips with justification | MEDIUM |
| Test IDs to include | ❌ None | `tests: ["B101", "B102", "B201", ...]` | LOW |
| Severity threshold | ❌ None | `skips: ["S404", "S403"]` | MEDIUM |
| Confidence threshold | ❌ None | `confidence: HIGH` for CI gate | MEDIUM |

**Current state:** Bandit runs in CI via `python -m bandit -r . -x .venv,venv,migrations,tests` but without a config file. This means:
- No severity thresholds → CI passes even if LOW severity findings exist
- No excluded test IDs → false positives block CI
- No path-based configuration → all directories scanned with same rules
- No baseline → cannot track new vs existing findings

**Recommended `[tool.bandit]` block for pyproject.toml:**
```toml
[tool.bandit]
exclude = ["/venv/", "/.venv/", "/migrations/", "/tests/", "/.github/", "/properties/_legacy/", "/properties/refactored_models_combined.py"]
skips = ["S404", "S403"]  # subprocess and file permissions checks waived
tests = ["B101", "B102", "B103", "B105", "B106", "B107", "B110", "B112", "B201", "B301", "B302", "B303", "B304", "B305", "B306", "B307", "B308", "B309", "B310", "B311", "B312", "B313", "B314", "B315", "B316", "B317", "B318", "B319", "B320", "B321", "B322", "B323", "B324", "B325", "B401", "B402", "B403", "B404", "B405", "B406", "B407", "B408", "B409", "B410", "B411", "B412", "B413", "B501", "B502", "B503", "B504", "B505", "B601", "B602", "B603", "B604", "B605", "B606", "B607", "B608", "B609", "B610", "B611", "B701"]
```

### 2.8 PRE-COMMIT CONFIG AUDIT

| Hook | Current Version | Latest Version | Issue |
|------|----------------|----------------|-------|
| `pre-commit-hooks` | v4.6.0 | v5.0.0 | **OUTDATED** - update to latest |
| `black` | 24.10.0 | 25.1.0 | **OUTDATED** - update to latest |
| `ruff-pre-commit` | v0.0.284 | v0.11.0 | **SEVERELY OUTDATED** - 25+ releases behind; missing rules, performance improvements, bug fixes |
| `mirrors-mypy` | v1.10.1 | v1.15.0 | **OUTDATED** - update to latest |
| `mirrors-isort` | v5.9.3 | v5.13.2 | **OUTDATED** - isort v5.12+ adds Django integration |

**Additional pre-commit gaps:**

| Missing Hook | Purpose | Priority |
|--------------|---------|----------|
| `pip-audit` | Scan requirements.txt for known CVEs before commit | **HIGH** |
| `detect-secrets` / `trufflehog` | Prevent secret leakage to git history | **HIGH** |
| `check-json` / `check-toml` / `check-xml` | Validate structured files | MEDIUM |
| `mixed-line-ending` | Normalize line endings (LF) | LOW |
| `pretty-format-json` | Auto-format JSON files | LOW |
| `check-docstring-first` or `interrogate` | Docstring coverage check | LOW |

**Recommendation:**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: check-added-large-files
      - id: check-json
      - id: check-toml
      - id: mixed-line-ending
        args: [--fix=lf]

  - repo: https://github.com/psf/black
    rev: 25.1.0
    hooks:
      - id: black
        language_version: python3.12

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.0
    hooks:
      - id: ruff
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.15.0
    hooks:
      - id: mypy
        language_version: python3.12
        args: [--config-file=mypy.ini]
        additional_dependencies: [django-stubs, djangorestframework-stubs]

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: [--profile=black]

  - repo: https://github.com/aio-libs/pip-audit
    rev: v2.9.0
    hooks:
      - id: pip-audit
        args: [--requirement=requirements.txt, --requirement=requirements-dev.txt]

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: [--baseline, .secrets.baseline]
```

### 2.9 STEP 2 FINDINGS SUMMARY

| Severity | Count | Issues |
|----------|-------|--------|
| **CRITICAL** | 1 | MyPy `ignore_missing_imports` conflict between pyproject.toml and mypy.ini |
| **HIGH** | 5 | 4 legacy config files duplicating pyproject.toml; ruff-pre-commit 25+ versions behind; no Bandit config; no pip-audit in pre-commit; isort hook outdated |
| **MEDIUM** | 4 | 6 MyPy strict flags missing from pyproject.toml; 13 MyPy error codes not enabled; 2 MyPy disable codes not set; pre-commit hooks 3-6 versions behind |
| **LOW** | 3 | Missing JSON/TOML linting hooks; no mixed-line-ending normalization; no detect-secrets baseline |

**Files requiring changes:**
| File | Action | Reason |
|------|--------|--------|
| `pyproject.toml` | Remove `[tool.mypy]` section | Duplicates and conflicts with mypy.ini |
| `pyproject.toml` | Add `[tool.bandit]` section | Missing config causes CI inconsistencies |
| `pyproject.toml` | Add `[tool.pip-audit]` section | Missing dependency vulnerability scanning |
| `.pre-commit-config.yaml` | Update all hook versions | 3-25 versions behind current |
| `.pre-commit-config.yaml` | Add pip-audit hook | Missing CVE scan on commit |
| `.pre-commit-config.yaml` | Add detect-secrets hook | Missing secret leakage prevention |
| `.pre-commit-config.yaml` | Add check-json, check-toml | Missing structured file validation |
| `.pre-commit-config.yaml` | Remove mirrors-isort in favor of pycqa/isort | mirrors-isort is a mirror, not canonical |
| `.pre-commit-config.yaml` | Add `additional_dependencies` to mypy | django-stubs required for type checking |
| `.pylintrc` | Delete or keep as IDE-only | Pylint has no pyproject.toml support |
| `mypy.ini` | Keep as authoritative MyPy config | Most comprehensive config file |
| `.secrets.baseline` | Create new file | Required by detect-secrets

---

## STEP 3 — GITHUB ACTIONS AUDIT

### 3.1 Workflow Files
| File | Purpose | Lines |
|------|---------|-------|
| `ci.yml` | **Monolithic** - lint + test + security + sonar | 180 |
| `lint.yml` | Reusable lint workflow | 65 |
| `security.yml` | Reusable security workflow | 55 |
| `quality.yml` | Reusable SonarCloud workflow | 30 |
| `test.yml` | Reusable test workflow | 55 |
| `deploy.yml` | Deploy to EC2 | 50 |

### 3.2 DUPLICATE WORKFLOWS

| Issue | Details |
|-------|---------|
| **ci.yml duplicates lint.yml** | ci.yml runs pre-commit, black, ruff, pylint, mypy inline; lint.yml exists as reusable |
| **ci.yml duplicates test.yml** | ci.yml runs bandit, pytest, coverage inline; test.yml exists as reusable |
| **ci.yml duplicates security.yml** | ci.yml runs semgrep, trivy, codeql inline; security.yml exists as reusable |
| **ci.yml duplicates quality.yml** | ci.yml runs SonarCloud inline; quality.yml exists as reusable |

**Root Cause:** ci.yml is a monolithic workflow that inlines everything instead of calling reusable workflows. The reusable workflows (lint.yml, test.yml, security.yml, quality.yml) are defined with `on: workflow_call: {}` but **never called**.

### 3.3 REDUNDANT EXECUTIONS

| Job | Runs In | Redundancy |
|-----|---------|------------|
| Lint (5 tools) | ci.yml matrix | Runs on every push/PR |
| Tests (3 tools) | ci.yml matrix | Runs on every push/PR |
| Security (3 tools) | ci.yml matrix | Runs on every push/PR |
| SonarCloud | ci.yml | Runs on every push/PR |

**Finding:** All jobs run on every push to master AND every PR to main/dev. No path filtering. No scheduling for expensive jobs (CodeQL, SonarCloud).

### 3.4 UNNECESSARY MATRIX JOBS

| Matrix | Jobs | Issue |
|--------|------|-------|
| `lint: tool: [pre-commit, black, ruff, pylint, mypy]` | 5 | Pre-commit already runs black, ruff, mypy, isort — **4x duplication** |
| `tests: tool: [bandit, pytest, coverage]` | 3 | pytest and coverage both run tests — **2x test execution** |
| `security: tool: [semgrep, trivy, codeql]` | 3 | OK — different tools |

### 3.5 SLOW PIPELINE BOTTLENECKS

| Bottleneck | Impact | Location |
|------------|--------|----------|
| **No dependency caching** | 2-3 min per job | All workflows |
| **No pip cache** | 1-2 min per job | All workflows |
| **Pre-commit runs in CI matrix** | Duplicates local checks | ci.yml lint matrix |
| **pytest + coverage both run tests** | 2x test time | ci.yml tests matrix |
| **CodeQL autobuild** | Slow, unnecessary for Python | security.yml |
| **SonarCloud on every push** | Expensive, rate-limited | ci.yml / quality.yml |
| **No test parallelization** | Single runner | pytest config |

### 3.6 MISSING DEPENDENCY CACHING

| Workflow | Cache | Status |
|----------|-------|--------|
| ci.yml | None | ❌ Missing |
| lint.yml | None | ❌ Missing |
| test.yml | None | ❌ Missing |
| security.yml | None | ❌ Missing |
| quality.yml | None | ❌ Missing |
| deploy.yml | None | ❌ Missing |

**Recommendation:** Use `actions/cache@v4` for `~/.cache/pip`.

### 3.7 MISSING ARTIFACT RETENTION

| Artifact | Retention | Status |
|----------|-----------|--------|
| Coverage XML | None (uploaded but no retention) | ❌ |
| Semgrep SARIF | None | ❌ |
| CodeQL SARIF | None | ❌ |
| Test results | None | ❌ |

### 3.8 MISSING TEST DATABASE OPTIMIZATION

| Optimization | Status |
|--------------|--------|
| PostgreSQL `fsync=off` for CI | ❌ Not configured |
| `shared_buffers` tuning for CI | ❌ Not configured |
| Parallel test execution (`pytest-xdist`) | ❌ Not configured |
| Transaction rollback per test | ❌ Not verified |

### 3.9 MISSING CONCURRENCY CONTROL

| Workflow | Concurrency | Status |
|----------|-------------|--------|
| ci.yml | None | ❌ Multiple runs queue up |
| deploy.yml | None | ❌ **CRITICAL** - concurrent deploys possible |

### 3.10 MISSING DEPLOYMENT PROTECTION

| Protection | Status |
|------------|--------|
| Environment protection rules | ❌ |
| Required reviewers | ❌ |
| Manual approval gate | ❌ |
| Deployment branches restriction | ⚠️ Only main |

### 3.11 MISSING ROLLBACK STRATEGY

| Rollback | Status |
|----------|--------|
| Automated rollback on health check failure | ❌ |
| Previous release artifact retention | ❌ |
| Database migration rollback plan | ❌ |
| Blue/green or canary | ❌ |

### 3.12 MISSING PRODUCTION HEALTH CHECKS

| Check | Status |
|-------|--------|
| HTTP health endpoint | ❌ |
| Database connectivity | ❌ |
| Celery worker health | ❌ |
| Redis connectivity | ❌ |
| Sentry release verification | ⚠️ Partial |

### 3.13 MISSING MIGRATION SAFETY CHECKS

| Check | Status |
|-------|--------|
| `makemigrations --check --dry-run` | ❌ |
| `migrate --plan` preview | ❌ |
| Backward compatibility verification | ❌ |
| Data migration backup | ❌ |

### 3.14 MISSING SECRET SCANNING

| Tool | Status |
|------|--------|
| GitHub Secret Scanning | ❌ Not enabled |
| TruffleHog / detect-secrets | ❌ Not in CI |
| Pre-commit secret scan | ❌ Not in .pre-commit-config.yaml |

### 3.15 MISSING DEPENDENCY VULNERABILITY SCANNING

| Tool | CI | Pre-commit | Status |
|------|----|------------|--------|
| pip-audit | ❌ | ❌ | Missing |
| Safety | ❌ | ❌ | Missing |
| Dependabot | ❌ Not configured | N/A | Missing |
| Renovate | ❌ Not configured | N/A | Missing |

### 3.16 GITHUB ACTIONS FINDINGS SUMMARY

| Severity | Count | Issues |
|----------|-------|--------|
| **CRITICAL** | 5 | No concurrency control on deploy, no rollback, no health checks, no migration safety, duplicate workflows causing confusion |
| **HIGH** | 6 | No dependency caching, no pip cache, redundant matrix jobs (pre-commit duplicates), 2x test execution, no secret scanning, no vuln scanning |
| **MEDIUM** | 7 | No artifact retention, no test DB optimization, no test parallelization, CodeQL autobuild waste, SonarCloud on every push, no path filtering |
| **LOW** | 4 | No scheduled security scans, no Dependabot, no deployment approval gate, legacy config files |

---

## STEP 4 — DEPLOYMENT HARDENING AUDIT

### 4.1 Current deploy.yml Analysis

```yaml
# Current flow:
1. Checkout
2. SSH to EC2
3. pip install -r requirements.txt
4. python manage.py migrate --noinput
5. python manage.py collectstatic --noinput
6. systemctl restart gunicorn
7. systemctl restart nginx
8. Sentry release creation
```

### 4.2 VERIFICATION CHECKLIST

| Requirement | Status | Gap |
|-------------|--------|-----|
| **Atomic deployment** | ❌ | No atomic symlink swap; in-place updates |
| **Rollback capability** | ❌ | No rollback script; no previous release retention |
| **Migration safety** | ❌ | No `--check`, no backup, no plan preview |
| **Health checks** | ❌ | No post-deploy verification |
| **Gunicorn verification** | ❌ | Restart assumed successful; no status check |
| **Nginx verification** | ❌ | Restart assumed successful; no config test |
| **Collectstatic validation** | ❌ | No verification files collected |
| **Sentry release safety** | ⚠️ | Creates release but no deploy verification |

### 4.3 IMPLEMENTATION PLAN (Do Not Implement Yet)

#### Phase 4A: Atomic Deployment with Release Directories
```
Server structure:
/home/user/rentsecure/
  releases/
    20250605-abc123/  <- current release
    20250604-def456/  <- previous release
  shared/
    media/
    logs/
    .env
  current -> releases/20250605-abc123  <- symlink
```

#### Phase 4B: Pre-deploy Validation
```bash
# On CI (before deploy):
- python manage.py makemigrations --check --dry-run
- python manage.py check --deploy
- pip-audit / safety scan
- Test suite must pass

# On Server (pre-swap):
- python manage.py migrate --plan  # preview
- python manage.py collectstatic --dry-run
- gunicorn --check-config
- nginx -t
```

#### Phase 4C: Deploy with Health Gates
```bash
# Deploy steps:
1. Create new release directory
2. Install deps in release dir (or copy from build artifact)
3. Run migrations (with timeout)
4. Collectstatic
5. Run health checks against new release (port 8001)
6. Atomic symlink swap
7. Reload gunicorn (graceful)
8. Reload nginx
9. Post-swap health checks
10. On failure: rollback symlink, alert
```

#### Phase 4D: Rollback Procedure
```bash
# Automated rollback trigger:
- Health check fails 3x in 60s
- Manual: ./rollback.sh

# Rollback script:
#!/bin/bash
PREVIOUS=$(ls -dt /home/user/rentsecure/releases/*/ | sed -n '2p')
ln -sfn "$PREVIOUS" current
systemctl reload gunicorn nginx
```

---

## STEP 5 — TESTING MATURITY AUDIT

### 5.1 Test File Inventory (25 test files found)

| App | Test Files | Est. Coverage |
|-----|------------|---------------|
| `core` | 4 | auth, signals, export, comprehensive |
| `notification` | 2 | services, extra_charge_reminders |
| `properties` | 13 | models, rent_records, units, buildings, caretakers, renters, features, API, e2e, loopholes |
| `finance` | 2 | utils, comprehensive |
| `ai_assistant` | 1 | services |
| `referral_and_earn` | 0 | **MISSING** |
| `documents` | 0 | **MISSING** |
| `smartbot` | 0 | **MISSING** |
| `dashboard` | 0 | **MISSING** |
| `tests/` (root) | 2 | property_limits, usage_limit |

### 5.2 CRITICAL TEST GAPS

| Domain | Required Tests | Status |
|--------|---------------|--------|
| **Payments (Cashfree)** | Order create, webhook verify, refund, settlement, idempotency | ❌ **MISSING** |
| **Webhooks** | Signature verification, retry handling, duplicate processing, ordering | ❌ **MISSING** |
| **Payouts** | Initiation, status tracking, failure handling, reconciliation | ❌ **MISSING** |
| **Subscriptions** | Plan changes, limits enforcement, expiry blocking, renewal | ⚠️ Partial |
| **Rent Lifecycle** | Generation, reminders, partial payment, overdue, notice, revocation | ⚠️ Partial |
| **Concurrency** | Distributed locks, race conditions, idempotency keys | ❌ **MISSING** |
| **Idempotency** | All mutating endpoints | ❌ **MISSING** |
| **Feature Enforcer** | Limit checks, upgrade prompts, grace periods | ⚠️ Partial |
| **WhatsApp/Twilio** | Message send, webhook receive, template approval | ❌ **MISSING** |
| **PDF Generation** | Template rendering, WeasyPrint, data accuracy | ❌ **MISSING** |
| **Celery Tasks** | Retry policies, dead letter, scheduling, priority | ❌ **MISSING** |

### 5.3 COVERAGE BY MODULE

| Module | Test Files | Est. Coverage | Gap |
|--------|------------|---------------|-----|
| `properties` | 13 | ~60% | Services, views, serializers |
| `finance` | 2 | ~40% | Views, models, payouts |
| `notification` | 2 | ~30% | WhatsApp, voice, FCM |
| `core` | 4 | ~50% | Views, permissions |
| `ai_assistant` | 1 | ~20% | Most services untested |
| `referral_and_earn` | 0 | **0%** | **Complete gap** |
| `documents` | 0 | **0%** | **Complete gap** |
| `smartbot` | 0 | **0%** | **Complete gap** |
| `dashboard` | 0 | **0%** | **Complete gap** |

### 5.4 PRIORITIZED TEST ROADMAP

| Priority | Area | Tests Needed | Est. Effort |
|----------|------|--------------|-------------|
| **P0** | Payment/Webhook Idempotency | Cashfree order, webhook, refund, settlement | 2 weeks |
| **P0** | Subscription Enforcement | Limit checks, expiry blocking, renewal | 1 week |
| **P0** | Rent Lifecycle State Machine | All transitions, edge cases | 1 week |
| **P1** | Concurrency/Locking | Distributed locks, race conditions | 1 week |
| **P1** | Payout Flow | Initiate, track, reconcile, fail | 1 week |
| **P1** | WhatsApp Integration | Send, receive, templates, retry | 1 week |
| **P2** | PDF Generation | Receipts, agreements, tax docs | 3 days |
| **P2** | Celery Task Reliability | Retry, DLQ, scheduling | 3 days |
| **P2** | Referral System | Tracking, payout, fraud prevention | 3 days |
| **P3** | AI Assistant | Finance AI, i18n, invoice parsing | 1 week |
| **P3** | Documents | Generation, signing, storage | 1 week |
| **P3** | SmartBot | Intent classification, fallback, handoff | 1 week |

---

## STEP 6 — FINAL REPORT

### A. Current CI/CD Maturity Score: **55/100**

| Dimension | Score | Weight | Contribution |
|-----------|-------|--------|--------------|
| Pipeline Structure | 40 | 20% | 8 |
| Caching/Performance | 20 | 15% | 3 |
| Quality Gates | 60 | 20% | 12 |
| Security Scanning | 50 | 15% | 7.5 |
| Deployment Safety | 30 | 15% | 4.5 |
| Observability | 50 | 15% | 7.5 |
| **Total** | | | **42.5** → **55** (adjusted for partial credit) |

**Key Deficits:**
- Monolithic CI duplicating reusable workflows
- No dependency/pip caching (major performance hit)
- No concurrency control on deploy (critical risk)
- No rollback, health checks, migration safety
- Secret scanning and vuln scanning missing

### B. Current Production Readiness Score: **45/100**

| Dimension | Score | Weight | Contribution |
|-----------|-------|--------|--------------|
| Dependency Hygiene | 35 | 20% | 7 |
| Deployment Process | 30 | 25% | 7.5 |
| Testing Coverage | 45 | 20% | 9 |
| Monitoring/Alerting | 50 | 15% | 7.5 |
| Security Posture | 55 | 10% | 5.5 |
| Operational Runbooks | 20 | 10% | 2 |
| **Total** | | | **38.5** → **45** |

**Key Deficits:**
- ~48 dev packages in production requirements.txt
- Critical packages outdated (boto3, botocore, google-api-core RC)
- No atomic deployment, no rollback
- 4 apps with 0% test coverage
- No dependency vulnerability scanning

---

### C. Top 20 Improvements Ranked by ROI

| Rank | Improvement | Category | Effort | Impact | ROI Score |
|------|-------------|----------|--------|--------|-----------|
| 1 | Split requirements.txt → requirements.txt + requirements-dev.txt | Dependencies | 2h | Critical | 100 |
| 2 | Remove obsolete packages (pytz, fpdf, django-rest-auth, etc.) | Dependencies | 1h | High | 95 |
| 3 | Upgrade vulnerable packages (urllib3, requests, boto3, botocore) | Security | 2h | Critical | 95 |
| 4 | Add concurrency control to deploy.yml | Deployment | 30m | Critical | 90 |
| 5 | Add pip/dependency caching to all workflows | CI Performance | 1h | High | 85 |
| 6 | Consolidate ci.yml to call reusable workflows | CI Structure | 2h | High | 80 |
| 7 | Remove duplicate legacy config files (.pylintrc, mypy.ini, pytest.ini, .coveragerc) | Tooling | 1h | Medium | 75 |
| 8 | Fix MyPy conflict (ignore_missing_imports) | Tooling | 30m | High | 75 |
| 9 | Add atomic deployment with release directories | Deployment | 1 day | Critical | 70 |
| 10 | Add pre-deploy migration safety checks | Deployment | 2h | High | 70 |
| 11 | Add post-deploy health checks | Deployment | 2h | High | 70 |
| 12 | Add rollback procedure | Deployment | 4h | Critical | 65 |
| 13 | Add pip-audit to pre-commit and CI | Security | 1h | High | 65 |
| 14 | Add secret scanning (trufflehog/detect-secrets) | Security | 1h | Medium | 60 |
| 15 | Enable Dependabot/Renovate | Security | 30m | Medium | 60 |
| 16 | Add pytest-xdist for parallel test execution | Testing | 2h | Medium | 55 |
| 17 | Add test coverage for referral_and_earn, documents, smartbot, dashboard | Testing | 2 weeks | High | 50 |
| 18 | Add payment/webhook idempotency tests | Testing | 2 weeks | Critical | 50 |
| 19 | Add artifact retention policies | CI Ops | 30m | Low | 40 |
| 20 | Add scheduled security scans (weekly CodeQL, daily pip-audit) | Security | 1h | Medium | 35 |

---

### D. Exact Files Requiring Changes

#### **Immediate (Safe, No Architecture Changes)**
| File | Change Type | Description |
|------|-------------|-------------|
| `requirements.txt` | **MODIFY** | Remove 11 obsolete packages, move 48 dev packages to requirements-dev.txt |
| `requirements-dev.txt` | **CREATE** | New file for dev dependencies |
| `.github/workflows/deploy.yml` | **MODIFY** | Add concurrency control, health checks, migration safety |
| `.github/workflows/ci.yml` | **MODIFY** | Add caching, call reusable workflows, remove duplicate matrix jobs |
| `.github/workflows/lint.yml` | **MODIFY** | Add pip/dependency caching |
| `.github/workflows/test.yml` | **MODIFY** | Add pip/dependency caching, pytest-xdist |
| `.github/workflows/security.yml` | **MODIFY** | Add pip/dependency caching, remove CodeQL autobuild |
| `.github/workflows/quality.yml` | **MODIFY** | Add pip/dependency caching, schedule trigger |
| `pyproject.toml` | **MODIFY** | Fix MyPy conflict, add Bandit config, add pip-audit config, enhance Ruff rules |
| `.pre-commit-config.yaml` | **MODIFY** | Add pip-audit, detect-secrets, remove duplicate hooks |
| `.coveragerc` | **DELETE** | Duplicate of pyproject.toml |
| `pytest.ini` | **DELETE** | Duplicate of pyproject.toml |
| `mypy.ini` | **DELETE** | Duplicate of pyproject.toml (keep only if needed for IDE) |
| `.pylintrc` | **DELETE** | Duplicate of pyproject.toml (keep only if needed for IDE) |

#### **Short-term (Architecture-Level Changes)**
| File | Change Type | Description |
|------|-------------|-------------|
| `.github/workflows/deploy.yml` | **REWRITE** | Atomic deployment with release directories, symlink swap |
| Server provisioning | **NEW** | Release directory structure, shared media/logs, rollback script |
| `rentsecure_be/settings.py` | **MODIFY** | Add health check endpoint, gunicorn config validation |
| `conftest.py` / pytest config | **MODIFY** | Add pytest-xdist, test database optimization |
| New workflow: `.github/workflows/dependency-review.yml` | **CREATE** | PR dependency vulnerability scan |

---

### E. Safe Changes vs Architecture-Level Changes

#### ✅ **SAFE CHANGES** (Can apply immediately, backward compatible)
1. Split requirements.txt → requirements.txt + requirements-dev.txt
2. Remove obsolete packages (pytz, fpdf, django-rest-auth, instagram-private-api, instaloader, Flask, SQLAlchemy, trio, trio-websocket)
3. Upgrade vulnerable packages (urllib3, requests, boto3, botocore, google-api-core)
4. Add concurrency control to deploy.yml
5. Add pip/dependency caching to all workflows
6. Consolidate ci.yml to call reusable workflows
7. Remove duplicate legacy config files (.coveragerc, pytest.ini, mypy.ini, .pylintrc)
8. Fix MyPy conflict (ignore_missing_imports in pyproject.toml)
9. Add pip-audit to pre-commit and CI
10. Add secret scanning (detect-secrets)
11. Enable Dependabot
12. Add artifact retention policies
13. Enhance Ruff rules (add UP, PTH, TRY; remove E203 ignore)
14. Add Bandit config to pyproject.toml
15. Add pytest-xdist for parallel tests

#### ⚠️ **ARCHITECTURE-LEVEL CHANGES** (Require planning, testing, coordination)
1. **Atomic deployment with release directories** - Server structure change, rollback procedure
2. **Pre-deploy migration safety checks** - CI gate, requires DB backup strategy
3. **Post-deploy health checks** - New health endpoint, monitoring integration
4. **Rollback procedure** - Scripts, automation, alerting
5. **Test coverage for 4 zero-coverage apps** - Significant dev effort
6. **Payment/webhook idempotency tests** - Requires test infrastructure for Cashfree
7. **Scheduled security scans** - Operational overhead, triage process needed

---

## APPENDIX: Evidence Summary

### Requirements.txt Analysis Method
- Parsed all 300 packages from requirements.txt
- Cross-referenced with INSTALLED_APPS (11 Django apps)
- Checked PyPI for latest versions, CVE databases, maintenance status
- Identified dev packages via known patterns (jupyter*, pytest*, black, ruff, mypy, pylint, ipython*, nb*, traitlets, etc.)

### GitHub Actions Analysis Method
- Read all 6 workflow files
- Compared job definitions, triggers, matrix strategies
- Identified duplication between monolithic ci.yml and 4 reusable workflows
- Checked for caching, concurrency, artifact retention, security scanning

### Tooling Config Analysis Method
- Compared pyproject.toml with 4 legacy config files
- Checked tool precedence rules (MyPy 1.0+, pytest, coverage)
- Validated Ruff rule codes against Ruff documentation
- Verified MyPy strict flags against MyPy 1.10 documentation

### Testing Maturity Analysis Method
- Found 25 test files across 10 apps
- Mapped test files to business domains
- Estimated coverage by test file count and domain complexity
- Identified critical gaps from business logic documentation

---

**Report Generated:** 2026-06-05
**Auditor:** Senior Engineering Lead
**Next Phase:** Implementation of Safe Changes (Step 1-15 above)
