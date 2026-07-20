"""Architecture regression: no circular dependencies between app packages."""

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
EXCLUDED_DIRS = {
    ".venv",
    "venv",
    "build",
    "dist",
    "__pycache__",
    "migrations",
    ".pytest_cache",
    ".github",
    ".kilo",
    ".nox",
    "tests",
    "management",
}
APP_PACKAGES = [
    "core",
    "properties",
    "payments",
    "notification",
    "finance",
    "documents",
    "referral_and_earn",
    "smartbot",
    "shared",
    "rentsecure_be",
]


def _python_files() -> dict[str, list[Path]]:
    files: dict[str, list[Path]] = {pkg: [] for pkg in APP_PACKAGES}
    for path in REPO_ROOT.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.name.startswith("test_"):
            continue
        try:
            rel = path.relative_to(REPO_ROOT)
            top = rel.parts[0]
            if top in files:
                files[top].append(path)
        except ValueError:
            continue
    return files


def _imports_from(filepath: Path) -> set[str]:
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return set()

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and not node.level:
            top = node.module.split(".")[0]
            if top in APP_PACKAGES:
                imports.add(top)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in APP_PACKAGES:
                    imports.add(top)
    return imports


def _build_dependency_graph() -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {pkg: set() for pkg in APP_PACKAGES}
    files_by_pkg = _python_files()
    for pkg, files in files_by_pkg.items():
        for filepath in files:
            imports = _imports_from(filepath)
            imports.discard(pkg)
            graph[pkg].update(imports)
    return graph


def _find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []

    def dfs(node: str, path: list[str], visited: set[str]) -> None:
        if node in path:
            idx = path.index(node)
            cycles.append(path[idx:] + [node])
            return
        if node in visited:
            return
        visited.add(node)
        path.append(node)
        for neighbor in sorted(graph.get(node, [])):
            dfs(neighbor, path, visited)
        path.pop()
        visited.discard(node)

    for node in sorted(graph):
        dfs(node, [], set())

    return cycles


class TestCircularDeps:
    def test_no_circular_dependencies(self) -> None:
        graph = _build_dependency_graph()
        cycles = _find_cycles(graph)
        assert not cycles, f"Circular dependencies detected: {cycles}"
