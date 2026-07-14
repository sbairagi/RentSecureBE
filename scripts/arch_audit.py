#!/usr/bin/env python3
"""
Architecture Dependency Audit Script for RentSecureBE.
Read-only analysis. Produces data for architecture reports.
"""

import ast
import json
import os
from collections import defaultdict
from pathlib import Path

REPO = Path("/Users/sbairagi/Desktop/MVP Project/RentSecureBE")

SKIP_DIRS = {
    "__pycache__",
    ".git",
    ".venv",
    ".nox",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".hypothesis",
    ".benchmarks",
    ".scannerwork",
    ".sonarlint",
    ".vscode",
    ".kilo",
    ".grimp_cache",
}

STDLIB_THIRD_PARTY = {
    "os",
    "sys",
    "pathlib",
    "json",
    "datetime",
    "time",
    "uuid",
    "re",
    "typing",
    "collections",
    "itertools",
    "functools",
    "math",
    "random",
    "logging",
    "argparse",
    "csv",
    "hashlib",
    "base64",
    "io",
    "contextlib",
    "dataclasses",
    "enum",
    "string",
    "textwrap",
    "warnings",
    "traceback",
    "inspect",
    "types",
    "copy",
    "pickle",
    "shelve",
    "sqlite3",
    "decimal",
    "fractions",
    "statistics",
    "numbers",
    "abc",
    "atexit",
    "signal",
    "threading",
    "multiprocessing",
    "subprocess",
    "socket",
    "select",
    "ssl",
    "http",
    "urllib",
    "email",
    "xml",
    "html",
    "webbrowser",
    "getopt",
    "fileinput",
    "filecmp",
    "tempfile",
    "zipfile",
    "tarfile",
    "gzip",
    "bz2",
    "lzma",
    "configparser",
    "netrc",
    "plistlib",
    "ast",
    "symtable",
    "symbol",
    "token",
    "keyword",
    "generator",
    "asyncio",
    "concurrent",
    "await",
    "async",
    "django",
    "rest_framework",
    "rest_framework_simplejwt",
    "celery",
    "redis",
    "pandas",
    "numpy",
    "requests",
    "httpx",
    "boto3",
    "botocore",
    "stripe",
    "paypal",
    "twilio",
    "firebase",
    "weasyprint",
    "pdfkit",
    "reportlab",
    "fpdf",
    "xlsxwriter",
    "pytest",
    "factory",
    "hypothesis",
    "locust",
    "faker",
    "mock",
    "freezegun",
    "pytest_django",
    "pytest_cov",
    "coverage",
    "mypy",
    "flake8",
    "pylint",
    "black",
    "isort",
    "ruff",
    "bandit",
    "gunicorn",
    "uvicorn",
    "daphne",
    "channels",
    "channels_redis",
    "psycopg2",
    "psycopg2_binary",
    "asyncpg",
    "mysqlclient",
    "dj_database_url",
    "python_dotenv",
    "python_decouple",
    "pillow",
    "PIL",
    "qrcode",
    "cryptography",
    "crypt",
    "pyjwt",
    "oauth2_provider",
    "allauth",
    "social_django",
    "yaml",
    "ruamel",
    "toml",
    "dotenv",
    "jinja2",
    "markupsafe",
    "kombu",
    "amqp",
    "billiard",
    "django_celery_beat",
    "django_celery_results",
    "django_filters",
    "django_extensions",
    "django_rest_framework",
    "drf_spectacular",
    "drf_yasg",
    "swagger",
    "openapi",
    "sentry_sdk",
    "rollbar",
    "loguru",
    "structlog",
    "opentelemetry",
    "prometheus_client",
    "django_prometheus",
    "whitenoise",
    "django_storages",
    "storages",
    "watchdog",
    "schedule",
    "apscheduler",
    "celery_once",
    "flower",
    "django_flower",
    "sphinx",
    "mkdocs",
    "ipython",
    "ipdb",
    "pudb",
    "wdb",
    "debugpy",
}

PROJECT_ROOT_PACKAGES = {
    "core",
    "properties",
    "smartbot",
    "finance",
    "notification",
    "documents",
    "referral_and_earn",
    "ai_assistant",
    "dashboard",
    "rentsecure_be",
    "shared",
    "management",
    "tools",
    "scripts",
    "tests",
    "conftest",
    "debug_test",
    "manage",
    "noxfile",
    "pyproject",
    "architecture",
}

LAYER_DOMAIN = "domain"
LAYER_APPLICATION = "application"
LAYER_INFRASTRUCTURE = "infrastructure"
LAYER_SHARED = "shared"
LAYER_REPOSITORY = "repository"
LAYER_SERVICES = "services"
LAYER_VIEWS = "views"
LAYER_MODELS = "models"

APP_BOUNDARIES = {
    "core": {"domain", "application", "infrastructure", "shared"},
    "properties": {"domain", "application", "infrastructure", "shared"},
    "smartbot": {"domain", "application", "infrastructure", "shared"},
    "finance": {"domain", "application", "infrastructure", "shared"},
    "notification": {"domain", "application", "infrastructure", "shared"},
    "documents": {"domain", "application", "infrastructure", "shared"},
    "referral_and_earn": {"domain", "application", "infrastructure", "shared"},
    "ai_assistant": {"domain", "application", "infrastructure", "shared"},
    "dashboard": {"domain", "application", "infrastructure", "shared"},
    "rentsecure_be": {"infrastructure", "shared"},
    "shared": {"shared"},
}


class ImportAnalyzer(ast.NodeVisitor):
    def __init__(self, filepath):
        self.filepath = filepath
        self.imports = []
        self.from_imports = []
        self.symbols = set()
        self.has_code = False

    def visit_Import(self, node):
        self.has_code = True
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        self.has_code = True
        module = node.module or ""
        for alias in node.names:
            self.from_imports.append((module, alias.name))
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.has_code = True
        self.symbols.add(node.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.has_code = True
        self.symbols.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.has_code = True
        self.symbols.add(node.name)
        self.generic_visit(node)

    def visit_Assign(self, node):
        self.has_code = True
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.symbols.add(target.id)
        self.generic_visit(node)


def get_module_name(filepath):
    rel = filepath.relative_to(REPO)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    elif parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]
    if "migrations" in parts:
        return None
    return ".".join(parts)


def is_project_module(module_name):
    if not module_name:
        return False
    top = module_name.split(".")[0]
    return top in PROJECT_ROOT_PACKAGES


def normalize_module(m):
    if m.startswith("."):
        return None
    return m


def analyze_file(filepath):
    try:
        with open(filepath, encoding="utf-8") as f:
            source = f.read()
    except Exception:
        return None

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    analyzer = ImportAnalyzer(filepath)
    analyzer.visit(tree)
    return analyzer


def get_app(filepath):
    rel = filepath.relative_to(REPO)
    parts = list(rel.parts)
    if parts[0] in PROJECT_ROOT_PACKAGES:
        return parts[0]
    return None


def collect_files():
    files = []
    for root, dirs, filenames in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in filenames:
            if f.endswith(".py"):
                p = Path(root) / f
                files.append(p)
    files.sort()
    return files


def analyze_files(files):
    file_data = {}
    module_map = {}
    for fp in files:
        data = analyze_file(fp)
        if data:
            file_data[str(fp)] = data
            mod = get_module_name(fp)
            if mod:
                module_map.setdefault(mod, []).append(str(fp))
    return file_data, module_map


def build_module_imports(file_data):
    module_imports = defaultdict(set)
    all_project_imports = defaultdict(set)

    for mod_path, data in file_data.items():
        src_mod = get_module_name(Path(mod_path))
        if not src_mod:
            continue
        imported_mods = set()
        for imp in data.imports:
            imp = normalize_module(imp)
            if imp and is_project_module(imp):
                imported_mods.add(imp)
        for mod, _name in data.from_imports:
            mod = normalize_module(mod)
            if mod and is_project_module(mod):
                imported_mods.add(mod)
            if mod and is_project_module(mod):
                imported_mods.add(mod)
        module_imports[src_mod].update(imported_mods)
        all_project_imports[src_mod].update(
            [imp for imp in data.imports if is_project_module(imp)]
        )
        for mod, _name in data.from_imports:
            mod = normalize_module(mod)
            if mod and is_project_module(mod):
                all_project_imports[src_mod].add(mod)

    return module_imports, all_project_imports


def find_cycles(module_imports):
    adj = {k: list(v) for k, v in module_imports.items()}
    cycles = []

    def dfs(node, visited, path):
        if node in visited:
            idx = path.index(node)
            cycle = path[idx:] + [node]
            normalized = tuple(sorted(set(cycle[:-1])))
            if normalized not in [tuple(sorted(c[:-1])) for c in cycles]:
                cycles.append(cycle)
            return
        visited.add(node)
        path.append(node)
        for neighbor in adj.get(node, []):
            dfs(neighbor, visited, path)
        path.pop()
        visited.discard(node)

    for node in adj:
        dfs(node, set(), [])

    seen = set()
    unique_cycles = []
    for c in cycles:
        key = tuple(sorted(c[:-1]))
        if key not in seen:
            seen.add(key)
            unique_cycles.append(c)
    return unique_cycles


def compute_cross_app(module_imports):
    cross_app = []
    for src_mod, deps in module_imports.items():
        src_app = src_mod.split(".")[0]
        for dep in deps:
            dep_app = dep.split(".")[0]
            if src_app != dep_app:
                cross_app.append((src_mod, dep_app, dep))
    return cross_app


def compute_fan_metrics(module_imports):
    fan_out = {k: len(v) for k, v in module_imports.items()}
    fan_in = defaultdict(int)
    for _k, v in module_imports.items():
        for dep in v:
            fan_in[dep] += 1
    return fan_in, fan_out


def compute_dead_modules(module_imports, module_map, file_data):
    _fan_in, _fan_out = compute_fan_metrics(module_imports)
    fan_in = _fan_in
    dead_modules = []
    all_mods = set(module_imports.keys())
    for mod in all_mods:
        if fan_in[mod] == 0:
            has_symbols = False
            for fp in module_map.get(mod, []):
                data = file_data.get(fp)
                if data and data.symbols:
                    has_symbols = True
                    break
            if not has_symbols:
                dead_modules.append(mod)
    return dead_modules


def compute_hotspots(module_imports, module_map, file_data, cross_app):
    fan_in, fan_out = compute_fan_metrics(module_imports)
    all_mods = set(module_imports.keys())
    hotspots = []
    for mod in all_mods:
        fi = fan_in.get(mod, 0)
        fo = fan_out.get(mod, 0)
        total = fi + fo
        symbols = 0
        for fp in module_map.get(mod, []):
            data = file_data.get(fp)
            if data:
                symbols += len(data.symbols)
        ca = sum(1 for src, _dst, dep in cross_app if src == mod or dep == mod)
        hotspots.append(
            {
                "module": mod,
                "fan_in": fi,
                "fan_out": fo,
                "total": total,
                "symbols": symbols,
                "cross_app": ca,
            }
        )
    hotspots.sort(
        key=lambda x: (-x["total"], -x["fan_out"], -x["fan_in"], -x["cross_app"])
    )
    return hotspots


def compute_app_stats(module_imports, module_map, file_data):
    fan_in, fan_out = compute_fan_metrics(module_imports)
    all_mods = set(module_imports.keys())
    app_stats = {}
    for mod in all_mods:
        app = mod.split(".")[0]
        app_stats.setdefault(
            app,
            {
                "modules": 0,
                "imports": 0,
                "imported_by": 0,
                "symbols": 0,
                "files": 0,
            },
        )
        app_stats[app]["modules"] += 1
        app_stats[app]["imports"] += fan_out.get(mod, 0)
        app_stats[app]["imported_by"] += fan_in.get(mod, 0)
        app_stats[app]["symbols"] += sum(
            len(file_data.get(fp, ImportAnalyzer("")).symbols)
            for fp in module_map.get(mod, [])
        )
        app_stats[app]["files"] += len(module_map.get(mod, []))
    return app_stats


def write_output(
    path,
    files,
    all_mods,
    module_imports,
    all_project_imports,
    cross_app,
    unique_cycles,
    dead_modules,
    hotspots,
    app_stats,
    fan_in,
    fan_out,
):
    total_modules = len(all_mods)
    total_imports = sum(fan_out.values())
    avg_imports = total_imports / total_modules if total_modules else 0
    avg_fan_in = sum(fan_in.values()) / total_modules if total_modules else 0
    avg_fan_out = sum(fan_out.values()) / total_modules if total_modules else 0
    most_imported = sorted(fan_in.items(), key=lambda x: -x[1])[:20]
    most_dependent = sorted(fan_out.items(), key=lambda x: -x[1])[:20]

    out = {
        "files": [str(fp) for fp in files],
        "modules": sorted(all_mods),
        "module_imports": {k: sorted(v) for k, v in module_imports.items()},
        "all_project_imports": {k: sorted(v) for k, v in all_project_imports.items()},
        "cross_app": [
            {"source": s, "dep_app": d, "dep": dep} for s, d, dep in cross_app
        ],
        "cycles": unique_cycles,
        "dead_modules": dead_modules,
        "hotspots": hotspots,
        "app_stats": app_stats,
        "fan_in": dict(fan_in),
        "fan_out": dict(fan_out),
        "metrics": {
            "total_modules": total_modules,
            "total_imports": total_imports,
            "avg_imports_per_module": avg_imports,
            "avg_fan_in": avg_fan_in,
            "avg_fan_out": avg_fan_out,
            "most_imported": most_imported,
            "most_dependent": most_dependent,
        },
    }

    with open(path, "w") as f:
        json.dump(out, f, indent=2)


def print_summary(
    total_modules, total_imports, cross_app, unique_cycles, dead_modules, hotspots
):
    print("Analysis complete. Data written to docs/architecture/audit_data.json")
    print(f"Total modules: {total_modules}")
    print(f"Total imports: {total_imports}")
    print(f"Cross-app imports: {len(cross_app)}")
    print(f"Cycles: {len(unique_cycles)}")
    print(f"Dead modules: {len(dead_modules)}")
    print("Hotspots (top 5):")
    for h in hotspots[:5]:
        print(
            f"  {h['module']}: fan_in={h['fan_in']}, "
            f"fan_out={h['fan_out']}, total={h['total']}"
        )


def main():
    files = collect_files()

    file_data, module_map = analyze_files(files)

    module_imports, all_project_imports = build_module_imports(file_data)

    unique_cycles = find_cycles(module_imports)

    cross_app = compute_cross_app(module_imports)

    dead_modules = compute_dead_modules(module_imports, module_map, file_data)

    hotspots = compute_hotspots(module_imports, module_map, file_data, cross_app)

    app_stats = compute_app_stats(module_imports, module_map, file_data)

    fan_in, fan_out = compute_fan_metrics(module_imports)
    all_mods = set(module_imports.keys())

    out_path = REPO / "docs" / "architecture" / "audit_data.json"
    write_output(
        out_path,
        files,
        all_mods,
        module_imports,
        all_project_imports,
        cross_app,
        unique_cycles,
        dead_modules,
        hotspots,
        app_stats,
        fan_in,
        fan_out,
    )

    total_modules = len(all_mods)
    total_imports = sum(fan_out.values())
    print_summary(
        total_modules, total_imports, cross_app, unique_cycles, dead_modules, hotspots
    )


if __name__ == "__main__":
    main()
