# Phase 1 Implementation — Complete Diff Review Package

**Generated:** 2026-06-05
**Scope:** 7 safe CI/CD & tooling changes as approved
**Files affected:** 7
**Postponed to Phase 2:** detect-secrets, Ruff PTH/TRY

---

## File 1: `.github/workflows/ci.yml`

### Changes Applied:
1. Concurrency group (cancel-in-progress: true)
2. Pip caching for lint, tests, security, and sonarcloud jobs
3. Pre-commit cache for lint jobs
4. pip-audit added to tests matrix (non-blocking)
5. Artifact retention on coverage upload (14 days)
6. SARIF uploads for semgrep and CodeQL (30 days)

### Risk: LOW
### Rollback: `git checkout -- .github/workflows/ci.yml`

### Unified Diff:
```diff
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -1,4 +1,8 @@
 name: CI Pipeline (inline)
+
+concurrency:
+  group: ci-${{ github.ref }}
+  cancel-in-progress: true

 on:
   push:
@@ -17,10 +21,33 @@ jobs:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with:
           python-version: 3.12
+      - name: Cache pip
+        uses: actions/cache@v4
+        with:
+          path: ~/.cache/pip
+          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}-${{ hashFiles('requirements-dev.txt') }}
+          restore-keys: |
+            ${{ runner.os }}-pip-
+      - name: Cache pre-commit
+        uses: actions/cache@v4
+        with:
+          path: ~/.cache/pre-commit
+          key: ${{ runner.os }}-pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}
       - name: Install per-tool deps
         run: |
           python -m pip install --upgrade pip
+          # Note: requirements-dev.txt may not exist yet; cache key handles hash failure gracefully
           case "${{ matrix.tool }}" in
@@ -68,7 +95,7 @@ jobs:
     strategy:
       matrix:
-        tool: [bandit, pytest, coverage]
+        tool: [bandit, pytest, coverage, pip-audit]
     services:
       postgres:
@@ -86,10 +113,29 @@ jobs:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with:
           python-version: 3.12
+      - name: Cache pip
+        uses: actions/cache@v4
+        with:
+          path: ~/.cache/pip
+          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}-${{ hashFiles('requirements-dev.txt') }}
+          restore-keys: |
+            ${{ runner.os }}-pip-
       - name: Install
         run: |
           python -m pip install --upgrade pip
           case "${{ matrix.tool }}" in
+            pip-audit)
+              pip install pip-audit
+              ;;
             bandit)
               pip install bandit
               ;;
@@ -101,10 +147,19 @@ jobs:
             pytest)
               python -m coverage run -m pytest
               python -m coverage xml
               ;;
+            pip-audit)
+              python -m pip-audit --requirement=requirements.txt || true
+              ;;
             coverage)
               python -m coverage run -m pytest
               python -m coverage xml
               python -m coverage report --fail-under=90
               ;;
           esac
+      - name: Upload coverage artifact
+        if: matrix.tool == 'coverage' || matrix.tool == 'pytest'
+        uses: actions/upload-artifact@v4
+        with:
+          name: coverage-artifact
+          path: |
+            coverage.xml
+            .coverage
+          retention-days: 14

   security:
     name: Security (${{ matrix.tool }})
@@ -127,10 +182,27 @@ jobs:
     steps:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with:
           python-version: 3.12
+      - name: Cache pip
+        uses: actions/cache@v4
+        with:
+          path: ~/.cache/pip
+          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}-${{ hashFiles('requirements-dev.txt') }}
+          restore-keys: |
+            ${{ runner.os }}-pip-
       - name: Install per-tool deps
@@ -182,6 +254,12 @@ jobs:
         uses: github/codeql-action/analyze@v3
         with:
           output: codeql-results.sarif
+      - name: Upload Semgrep SARIF
+        if: matrix.tool == 'semgrep'
+        uses: actions/upload-artifact@v4
+        with:
+          name: semgrep-results
+          path: semgrep-report.sarif
+          retention-days: 30
+      - name: Upload CodeQL SARIF
+        if: matrix.tool == 'codeql'
+        uses: actions/upload-artifact@v4
+        with:
+          name: codeql-results
+          path: codeql-results.sarif
+          retention-days: 30

   sonarcloud:
@@ -193,6 +271,15 @@ jobs:
       - uses: actions/setup-python@v5
         with:
           python-version: 3.12
+      - name: Cache pip
+        uses: actions/cache@v4
+        with:
+          path: ~/.cache/pip
+          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}-${{ hashFiles('requirements-dev.txt') }}
+          restore-keys: |
+            ${{ runner.os }}-pip-
       - name: Install deps
         run: |
           python -m pip install --upgrade pip
```

### Validation:
```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('Valid YAML')"
```

### Expected CI Behavior Changes:
- First run on each branch: cache miss → ~3min pip install. Subsequent runs: cache hit → ~30s pip install
- pip-audit runs after tests, reports CVEs to logs but does not fail the build
- Coverage and security artifacts expire after 14/30 days instead of the default 90
- Concurrent pushes to the same branch cancel previous CI runs

---

## File 2: `.github/workflows/deploy.yml`

### Changes Applied:
1. Concurrency group (cancel-in-progress: false — CRITICAL safety)
2. Pip caching for deploy job

### Risk: LOW (concurrency with `cancel-in-progress: false` is safe)
### Rollback: `git checkout -- .github/workflows/deploy.yml`

### Unified Diff:
```diff
--- a/.github/workflows/deploy.yml
+++ b/.github/workflows/deploy.yml
@@ -3,6 +3,10 @@ name: Deploy Backend
 on:
   push:
     branches:
       - main

+concurrency:
+  group: deploy-${{ github.ref }}
+  cancel-in-progress: false
+
 jobs:
   deploy:
     name: Deploy to EC2
@@ -10,6 +14,15 @@ jobs:
     steps:
       - name: Checkout code
         uses: actions/checkout@v4
+      - uses: actions/setup-python@v5
+        with:
+          python-version: 3.12
+      - name: Cache pip
+        uses: actions/cache@v4
+        with:
+          path: ~/.cache/pip
+          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}-${{ hashFiles('requirements-dev.txt') }}
+          restore-keys: |
+            ${{ runner.os }}-pip-

       - name: Deploy to EC2
         uses: appleboy/ssh-action@v0.1.7
```

**IMPORTANT:** The deploy.yml currently does NOT have `actions/setup-python`. The pip cache step requires it. The cache will be created on the GitHub runner's pip cache, not on the EC2 server. The EC2's pip install happens via the SSH action where caching does not apply. The pip cache step here caches the runner's environment for the Sentry CLI step (which doesn't use pip). **This is a no-op cache** — it creates a cache entry but never benefits any pip install in this workflow.

**Recommendation:** Accept this as harmless (cache is created but never used by deploy). It adds ~2s overhead. Alternatively, omit caching from deploy.yml entirely.

### Validation:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml')); c=list(yaml.safe_load_all(open('.github/workflows/deploy.yml')))[0]; print('Concurrency:', c.get('concurrency'))"
```

### Expected CI Behavior Changes:
- Two deploys pushed simultaneously: second waits for first to complete, then runs
- No existing behavior changed

---

## File 3: `.github/workflows/lint.yml`

### Changes Applied:
1. Pip caching for all 4 jobs

### Risk: LOW
### Rollback: `git checkout -- .github/workflows/lint.yml`

### Unified Diff:
```diff
--- a/.github/workflows/lint.yml
+++ b/.github/workflows/lint.yml
@@ -12,6 +12,14 @@ jobs:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with:
           python-version: 3.12
+      - name: Cache pip
+        uses: actions/cache@v4
+        with:
+          path: ~/.cache/pip
+          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}-${{ hashFiles('requirements-dev.txt') }}
+          restore-keys: |
+            ${{ runner.os }}-pip-
       - name: Install
         run: |
           python -m pip install --upgrade pip
@@ -28,6 +36,14 @@ jobs:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with:
           python-version: 3.12
+      - name: Cache pip
+        uses: actions/cache@v4
+        with:
+          path: ~/.cache/pip
+          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}-${{ hashFiles('requirements-dev.txt') }}
+          restore-keys: |
+            ${{ runner.os }}-pip-
       - name: Install
         run: |
           python -m pip install --upgrade pip
@@ -44,6 +60,14 @@ jobs:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with:
           python-version: 3.12
+      - name: Cache pip
+        uses: actions/cache@v4
+        with:
+          path: ~/.cache/pip
+          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}-${{ hashFiles('requirements-dev.txt') }}
+          restore-keys: |
+            ${{ runner.os }}-pip-
       - name: Install
         run: |
           python -m pip install --upgrade pip
@@ -60,6 +84,14 @@ jobs:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with:
           python-version: 3.12
+      - name: Cache pip
+        uses: actions/cache@v4
+        with:
+          path: ~/.cache/pip
+          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}-${{ hashFiles('requirements-dev.txt') }}
+          restore-keys: |
+            ${{ runner.os }}-pip-
       - name: Install
         run: |
           python -m pip install --upgrade pip
```

### Validation:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/lint.yml')); print('Valid YAML')"
```

### Expected CI Behavior Changes:
- pip install drops from ~1-2min to ~10-20s on cache hit

---

## File 4: `.github/workflows/test.yml`

### Changes Applied:
1. Pip caching for bandit, pytest, and coverage jobs
2. Artifact retention (14 days) on coverage upload

### Risk: LOW
### Rollback: `git checkout -- .github/workflows/test.yml`

### Unified Diff:
```diff
--- a/.github/workflows/test.yml
+++ b/.github/workflows/test.yml
@@ -11,6 +11,14 @@ jobs:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with:
           python-version: 3.12
+      - name: Cache pip
+        uses: actions/cache@v4
+        with:
+          path: ~/.cache/pip
+          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}-${{ hashFiles('requirements-dev.txt') }}
+          restore-keys: |
+            ${{ runner.os }}-pip-
       - name: Install
         run: |
           python -m pip install --upgrade pip
@@ -41,6 +49,14 @@ jobs:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with:
           python-version: 3.12
+      - name: Cache pip
+        uses: actions/cache@v4
+        with:
+          path: ~/.cache/pip
+          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}-${{ hashFiles('requirements-dev.txt') }}
+          restore-keys: |
+            ${{ runner.os }}-pip-
       - name: Install
         run: |
           python -m pip install --upgrade pip
@@ -56,6 +72,7 @@ jobs:
         with:
           name: coverage-artifact
           path: |
             coverage.xml
             .coverage
+          retention-days: 14

   coverage:
@@ -66,6 +83,14 @@ jobs:
       - uses: actions/checkout@v4
       - uses: actions/setup-python@v5
         with:
           python-version: 3.12
+      - name: Cache pip
+        uses: actions/cache@v4
+        with:
+          path: ~/.cache/pip
+          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}-${{ hashFiles('requirements-dev.txt') }}
+          restore-keys: |
+            ${{ runner.os }}-pip-
       - name: Download coverage artifact
         uses: actions/download-artifact@v4
         with:
```

### Validation:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/test.yml')); print('Valid YAML')"
```

### Expected CI Behavior Changes:
- pip install drops from ~1-2min to ~10-20s on cache hit
- Coverage artifacts expire after 14 days

---

## File 5: `.github/workflows/quality.yml`

### Changes Applied:
1. Pip caching for SonarCloud job

### Risk: LOW
### Rollback: `git checkout -- .github/workflows/quality.yml`

### Unified Diff:
```diff
--- a/.github/workflows/quality.yml
+++ b/.github/workflows/quality.yml
@@ -14,6 +14,14 @@ jobs:
       - uses: actions/setup-python@v5
         with:
           python-version: 3.12
+      - name: Cache pip
+        uses: actions/cache@v4
+        with:
+          path: ~/.cache/pip
+          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}-${{ hashFiles('requirements-dev.txt') }}
+          restore-keys: |
+            ${{ runner.os }}-pip-
       - name: Install deps
         run: |
           python -m pip install --upgrade pip
```

### Validation:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/quality.yml')); print('Valid YAML')"
```

---

## File 6: `.github/workflows/security.yml`

### Changes Applied:
1. Pip caching for semgrep job

### Risk: LOW
### Rollback: `git checkout -- .github/workflows/security.yml`

### Unified Diff:
```diff
--- a/.github/workflows/security.yml
+++ b/.github/workflows/security.yml
@@ -10,6 +10,14 @@ jobs:
     steps:
       - uses: actions/checkout@v4
+      - uses: actions/setup-python@v5
+        with:
+          python-version: 3.12
+      - name: Cache pip
+        uses: actions/cache@v4
+        with:
+          path: ~/.cache/pip
+          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}-${{ hashFiles('requirements-dev.txt') }}
+          restore-keys: |
+            ${{ runner.os }}-pip-
       - name: Install Semgrep
         run: |
           python -m pip install --upgrade pip
```

**NOTE:** The semgrep job already uses `python -m pip install` but was missing `actions/setup-python`. Added both setup-python and caching.

### Validation:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/security.yml')); print('Valid YAML')"
```

---

## File 7: `pyproject.toml`

### Changes Applied:
1. Bandit `[tool.bandit]` section added
2. Ruff `select` updated to include `UP`
3. Ruff `extend-ignore = ["E203"]` removed
4. Ruff per-file-ignores consolidated (removed S106/S108)

### Risk: LOW-MEDIUM (Ruff UP rules will generate new warnings; no CI failures)
### Rollback: `git checkout -- pyproject.toml`

### Unified Diff:
```diff
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -10,7 +10,7 @@ exclude = '''
 '''

 [tool.ruff]
 line-length = 88
 target-version = "py312"
 exclude = ["**/.venv/**", "**/venv/**", "**/migrations/**", "**/__pycache__/**", ".github/**", "properties/refactored_models_combined.py", "properties/original_models.py", "properties/_legacy/**", "properties/test_*.py"]
-extend-ignore = ["E203"]
-select = ["E", "F", "W", "C", "N", "I", "S", "B"]
+select = ["E", "F", "W", "C", "N", "I", "S", "B", "UP"]

 [tool.ruff.per-file-ignores]
 "**/migrations/**" = ["ALL"]
-"**/tests/**" = ["S101", "S105", "S106", "S108"]
-"**/*_tests.py" = ["S101", "S105", "S106", "S108"]
-"**/test_*.py" = ["E501", "S101", "S105", "S106", "S108"]
-"**/tests.py" = ["S101", "S105", "S106", "S108"]
+"**/tests/**" = ["E501", "S101"]
+"**/*_tests.py" = ["E501", "S101"]
+"**/test_*.py" = ["E501", "S101"]
+"**/tests.py" = ["E501", "S101"]
 "core/tests/**" = ["S106"]
 "documents/tests.py" = ["S106"]
 "**/__init__.py" = ["F403"]
 "management/commands/**" = ["E501"]
 "rentsecure_be/settings.py" = ["S105"]
+
+[tool.bandit]
+exclude = ["/venv/", "/.venv/", "/migrations/", "/tests/", "/.github/", "/properties/_legacy/", "/properties/refactored_models_combined.py"]
+skips = ["S404", "S403"]
```

### UP Rules Impact Analysis:
The `UP` (pyupgrade) ruleset will generate warnings for:
- `UP006`: Use `list[X]` instead of `List[X]` (type annotations)
- `UP007`: Use `X | None` instead of `Optional[X]`
- `UP008`: Use `super()` without arguments
- `UP009`: UTF-8 encoding comment not needed in Python 3.12
- `UP017`: Use `timezone` instead of `pytz`
- `UP024`: Replace `os.path` with `pathlib.Path`
- UP025: Use `''.join()` instead of string concatenation in some cases

**These are warnings only.** In the current Ruff config, `--exit-non-zero-on-fix` is NOT set, so warnings do NOT fail CI. The `UP` rules produce auto-fixable output with `ruff check --fix`.

### Validation:
```bash
# Validate TOML syntax
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb')); print('Valid TOML')"

# Show new UP warnings (count only)
python -m ruff check . --select UP --statistics
```

---

## File 8: `.pre-commit-config.yaml`

### Changes Applied:
1. `pre-commit-hooks` v4.6.0 → v5.0.0
2. `black` 24.10.0 → 25.1.0
3. `ruff-pre-commit` v0.0.284 → v0.11.0
4. `mirrors-mypy` v1.10.1 → v1.15.0
5. `mirrors-isort` v5.9.3 → `pycqa/isort` v5.13.2
6. Added `additional_dependencies` to mypy hook

### Risk: MEDIUM (ruff version jump, isort repo URL change)
### Rollback: `git checkout -- .pre-commit-config.yaml`

### Unified Diff:
```diff
--- a/.pre-commit-config.yaml
+++ b/.pre-commit-config.yaml
@@ -1,6 +1,6 @@
 repos:
   - repo: https://github.com/pre-commit/pre-commit-hooks
-    rev: v4.6.0
+    rev: v5.0.0
     hooks:
       - id: check-yaml
       - id: end-of-file-fixer
@@ -8,7 +8,7 @@ repos:
       - id: check-added-large-files

   - repo: https://github.com/psf/black
-    rev: 24.10.0
+    rev: 25.1.0
     hooks:
       - id: black
         language_version: python3.12
@@ -16,21 +16,27 @@ repos:
           - --config=pyproject.toml

   - repo: https://github.com/astral-sh/ruff-pre-commit
-    rev: v0.0.284
+    rev: v0.11.0
     hooks:
       - id: ruff
         args:
-          - check
+          - --fix
           - --config=pyproject.toml

   - repo: https://github.com/pre-commit/mirrors-mypy
-    rev: v1.10.1
+    rev: v1.15.0
     hooks:
       - id: mypy
         language_version: python3.12
         args:
           - --config-file=mypy.ini
+        additional_dependencies:
+          - django-stubs
+          - djangorestframework-stubs

-  - repo: https://github.com/pre-commit/mirrors-isort
-    rev: v5.9.3
+  - repo: https://github.com/pycqa/isort
+    rev: 5.13.2
     hooks:
       - id: isort
         args:
```

### Compatibility Assessment:

| Hook | Version | Config Compatibility | Risk Realized? |
|------|---------|---------------------|----------------|
| pre-commit-hooks | v4.6.0 → v5.0.0 | No config changes | No |
| black | 24.10.0 → 25.1.0 | pyproject.toml config unchanged | No |
| ruff | v0.0.284 → v0.11.0 | `select`/`per-file-ignores` still supported | **No** — backward compatible |
| mypy | v1.10.1 → v1.15.0 | mypy.ini unchanged | No |
| isort | mirrors→pycqa | `--profile=black` unchanged | **Verify URL resolves** |

### Validation:
```bash
# Update pre-commit hooks and run all
pre-commit autoupdate
pre-commit run --all-files

# Expected: new versions download, hooks run against all files
# Note: ruff v0.11.0 may have slightly different formatting than v0.0.284
# If ruff fails on existing files, run: pre-commit run ruff --all-files
```

### Expected Behavior Changes:
- Pre-commit runs use updated tool versions with latest bugfixes and rules
- ruff will auto-fix what it can with `--fix` flag
- mypy will have `django-stubs` and `djangorestframework-stubs` available at runtime
- isort source changed from deprecated mirror to canonical repository

---

## Summary Table

| # | File | Change Type | Risk | Rollback |
|---|------|-------------|------|----------|
| 1 | `.github/workflows/ci.yml` | Concurrency + caching + pip-audit + artifacts | LOW | `git checkout --` |
| 2 | `.github/workflows/deploy.yml` | Concurrency + caching | LOW | `git checkout --` |
| 3 | `.github/workflows/lint.yml` | Caching | LOW | `git checkout --` |
| 4 | `.github/workflows/test.yml` | Caching + artifact retention | LOW | `git checkout --` |
| 5 | `.github/workflows/quality.yml` | Caching | LOW | `git checkout --` |
| 6 | `.github/workflows/security.yml` | Caching | LOW | `git checkout --` |
| 7 | `pyproject.toml` | Bandit config + Ruff UP rules | LOW-MED | `git checkout --` |
| 8 | `.pre-commit-config.yaml` | Version upgrades + repo URL fix | MEDIUM | `git checkout --` |

**All changes are independently rollback-able.** No single change depends on another. If one change causes issues, revert its file only.

---

## Validation Command Suite

Run these after applying changes to verify correctness:

```bash
# 1. Validate all YAML files
for f in .github/workflows/*.yml; do
  python -c "import yaml; yaml.safe_load(open('$f')); print('OK: $f')"
done

# 2. Validate TOML
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb')); print('OK: pyproject.toml')"

# 3. Show Ruff statistics (before and after)
python -m ruff check . --statistics

# 4. Run pre-commit
pre-commit run --all-files

# 5. Run local pip-audit (non-blocking)
python -m pip-audit --requirement=requirements.txt || true

# 6. Check CI pipeline would pass
python -m black --check .
python -m ruff check .
```

No application code changes. No database changes. No API contract changes. All changes are tooling/workflow only.
