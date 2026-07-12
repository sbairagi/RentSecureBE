#!/usr/bin/env python3
"""Generate architecture.json metadata from the RentSecureBE repository.

This is the SINGLE SOURCE OF TRUTH scanner.
All other generators must consume ONLY this file.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except Exception:
        return ""


def _load_module(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _unparse(node: ast.expr) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def _bases_names(bases: list[ast.expr]) -> list[str]:
    return [_unparse(base) for base in bases]


class AppScanner:
    def __init__(self, root: Path, app_name: str, app_dir: Path) -> None:
        self.root = root
        self.app_name = app_name
        self.app_dir = app_dir
        self.data: dict[str, Any] = {
            "name": app_name,
            "path": str(app_dir.relative_to(root)),
            "models": [],
            "views": [],
            "serializers": [],
            "urls": [],
            "services": [],
            "signals": [],
            "files": [],
        }

    def scan(self) -> dict[str, Any]:
        for py_file in sorted(self.app_dir.rglob("*.py")):
            if "__pycache__" in str(py_file) or "migrations" in str(py_file):
                continue
            rel = str(py_file.relative_to(self.root))
            self.data["files"].append({"path": rel, "sha256": _sha256(py_file)})
            tree = _load_module(py_file)
            if tree is None:
                continue
            self._scan_tree(tree, py_file)

        self.data["model_count"] = len(self.data["models"])
        self.data["view_count"] = len(self.data["views"])
        self.data["serializer_count"] = len(self.data["serializers"])
        self.data["service_count"] = len(self.data["services"])
        self.data["signal_count"] = len(self.data["signals"])
        return self.data

    def _scan_tree(self, tree: ast.Module, py_file: Path) -> None:
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                self._scan_class(node, py_file)

    def _scan_class(self, node: ast.ClassDef, py_file: Path) -> None:
        bases = _bases_names(node.bases)
        base_str = " ".join(bases)

        if (
            "models.Model" in base_str
            or any(base.endswith("Model") for base in bases)
            or "AbstractUser" in base_str
            or "AbstractBaseUser" in base_str
        ):
            self._register_model(node, py_file, bases)
        elif any(
            k in base_str for k in ["ViewSet", "APIView", "View", "GenericViewSet"]
        ):
            self._register_view(node, py_file, bases)
        elif "Serializer" in base_str or "ModelSerializer" in base_str:
            self._register_serializer(node, py_file, bases)

    def _register_model(  # noqa: C901
        self, node: ast.ClassDef, py_file: Path, bases: list[str]
    ) -> None:
        model: dict[str, Any] = {
            "name": node.name,
            "file": str(py_file.relative_to(self.root)),
            "bases": bases,
            "fields": [],
            "relationships": [],
            "meta": {},
        }
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        field_name = target.id
                        field_type = _unparse(item.value) if item.value else ""
                        field_info: dict[str, Any] = {
                            "name": field_name,
                            "raw": field_type,
                        }
                        if "ForeignKey" in field_type:
                            related = (
                                field_type.split("(")[1]
                                .split(",")[0]
                                .strip()
                                .strip("'\"")
                                if "(" in field_type
                                else ""
                            )
                            field_info["type"] = "ForeignKey"
                            field_info["related_model"] = related
                            model["relationships"].append(
                                {
                                    "type": "ForeignKey",
                                    "from": field_name,
                                    "to": related,
                                }
                            )
                        elif "OneToOneField" in field_type:
                            related = (
                                field_type.split("(")[1]
                                .split(",")[0]
                                .strip()
                                .strip("'\"")
                                if "(" in field_type
                                else ""
                            )
                            field_info["type"] = "OneToOneField"
                            field_info["related_model"] = related
                            model["relationships"].append(
                                {
                                    "type": "OneToOne",
                                    "from": field_name,
                                    "to": related,
                                }
                            )
                        elif "ManyToManyField" in field_type:
                            related = (
                                field_type.split("(")[1]
                                .split(",")[0]
                                .strip()
                                .strip("'\"")
                                if "(" in field_type
                                else ""
                            )
                            field_info["type"] = "ManyToMany"
                            field_info["related_model"] = related
                            model["relationships"].append(
                                {
                                    "type": "ManyToMany",
                                    "from": field_name,
                                    "to": related,
                                }
                            )
                        else:
                            field_info["type"] = (
                                field_type.split("(")[0].split(".")[-1]
                                if field_type
                                else "unknown"
                            )
                        model["fields"].append(field_info)
            elif isinstance(item, ast.ClassDef) and item.name == "Meta":
                for meta_item in item.body:
                    if isinstance(meta_item, ast.Assign):
                        for target in meta_item.targets:
                            if isinstance(target, ast.Name):
                                model["meta"][target.id] = (
                                    _unparse(meta_item.value) if meta_item.value else ""
                                )
        self.data["models"].append(model)

    def _register_view(
        self, node: ast.ClassDef, py_file: Path, bases: list[str]
    ) -> None:
        view: dict[str, Any] = {
            "name": node.name,
            "file": str(py_file.relative_to(self.root)),
            "bases": bases,
            "methods": [],
        }
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                view["methods"].append(item.name)
        self.data["views"].append(view)

    def _register_serializer(
        self, node: ast.ClassDef, py_file: Path, bases: list[str]
    ) -> None:
        serializer: dict[str, Any] = {
            "name": node.name,
            "file": str(py_file.relative_to(self.root)),
            "bases": bases,
            "fields": [],
        }
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == "Meta":
                        continue
                    if isinstance(target, ast.Name):
                        serializer["fields"].append(target.id)
        self.data["serializers"].append(serializer)


class URLScanner:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.urls: list[dict[str, Any]] = []

    def scan(self) -> list[dict[str, Any]]:
        for url_file in sorted(self.root.rglob("urls.py")):
            if ".venv" in str(url_file) or "__pycache__" in str(url_file):
                continue
            tree = _load_module(url_file)
            if tree is None:
                continue
            rel = str(url_file.relative_to(self.root))
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "urlpatterns":
                            self._scan_urlpatterns(node.value, rel)
                elif (
                    isinstance(node, ast.AnnAssign)
                    and isinstance(node.target, ast.Name)
                    and node.target.id == "urlpatterns"
                ):
                    if node.value is not None:
                        self._scan_urlpatterns(node.value, rel)
        return self.urls

    def _scan_urlpatterns(self, node: ast.expr, file: str) -> None:
        if isinstance(node, ast.List):
            for elt in node.elts:
                self._scan_url_call(elt, file)

    def _scan_url_call(self, node: ast.expr, file: str) -> None:
        if not isinstance(node, ast.Call):
            return
        func_name = _unparse(node.func)
        kwargs = {kw.arg: _unparse(kw.value) for kw in node.keywords}
        path_val = ""
        view_val = ""
        name_val = ""
        include_val = ""
        if node.args:
            path_val = _unparse(node.args[0]) if len(node.args) > 0 else ""
            view_val = _unparse(node.args[1]) if len(node.args) > 1 else ""
        if "path" in kwargs:
            path_val = kwargs["path"]
        if "view" in kwargs:
            view_val = kwargs["view"]
        if "name" in kwargs:
            name_val = kwargs["name"]
        if "include" in kwargs:
            include_val = kwargs["include"]
        if path_val or view_val or include_val:
            self.urls.append(
                {
                    "file": file,
                    "path": path_val.strip("\"'"),
                    "view": view_val,
                    "name": name_val.strip("\"'"),
                    "include": include_val,
                    "function": func_name,
                }
            )


class ServiceScanner:
    def __init__(self, root: Path, app_name: str, app_dir: Path) -> None:
        self.root = root
        self.app_name = app_name
        self.app_dir = app_dir
        self.services: list[dict[str, Any]] = []

    def scan(self) -> list[dict[str, Any]]:
        services_dir = self.app_dir / "services"
        if not services_dir.exists():
            return []
        for py_file in sorted(services_dir.rglob("*.py")):
            if "__pycache__" in str(py_file):
                continue
            tree = _load_module(py_file)
            if tree is None:
                continue
            rel = str(py_file.relative_to(self.root))
            functions = []
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
            if functions:
                self.services.append(
                    {
                        "file": rel,
                        "functions": functions,
                    }
                )
        return self.services


class DependencyScanner:
    def __init__(self, root: Path, apps: list[str]) -> None:
        self.root = root
        self.apps = apps
        self.dependencies: dict[str, list[str]] = {app: [] for app in apps}

    def scan(self) -> dict[str, list[str]]:  # noqa: C901
        for app in self.apps:
            app_dir = self.root / app
            if not app_dir.exists():
                continue
            for py_file in app_dir.rglob("*.py"):
                if "__pycache__" in str(py_file) or "migrations" in str(py_file):
                    continue
                tree = _load_module(py_file)
                if tree is None:
                    continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module:
                            for other_app in self.apps:
                                if other_app != app and node.module.startswith(
                                    other_app
                                ):
                                    if other_app not in self.dependencies[app]:
                                        self.dependencies[app].append(other_app)
        return self.dependencies


def scan_feature_flags(root: Path) -> list[str]:
    flags: list[str] = []
    settings_file = root / "rentsecure_be" / "settings.py"
    if not settings_file.exists():
        return flags
    tree = _load_module(settings_file)
    if tree is None:
        return flags
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.startswith("ENABLE_"):
                    flags.append(target.id)
    return sorted(flags)


def scan_installed_apps(root: Path) -> list[str]:
    apps: list[str] = []
    settings_file = root / "rentsecure_be" / "settings.py"
    if not settings_file.exists():
        return apps
    tree = _load_module(settings_file)
    if tree is None:
        return apps
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "INSTALLED_APPS":
                    if isinstance(node.value, ast.List):
                        for elt in node.value.elts:
                            app_name = _unparse(elt).strip("\"'")
                            if app_name:
                                apps.append(app_name)
    return apps


def scan_django_apps(root: Path) -> list[str]:
    apps: list[str] = []
    skip_dirs = {
        ".venv",
        "node_modules",
        ".git",
        "staticfiles",
        "media",
        "fonts",
        "tools",
        "tests",
        "docs",
        "management",
        "architecture",
        "scripts",
    }
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name in skip_dirs:
            continue
        is_django_app = (
            (entry / "apps.py").exists()
            or (entry / "urls.py").exists()
            or (entry / "views.py").exists()
            or (entry / "models.py").exists()
        )
        if is_django_app:
            apps.append(entry.name)
    return apps


def generate_architecture_metadata(root: Path, output: str) -> None:
    root = root.resolve()
    apps = scan_django_apps(root)
    installed_apps = scan_installed_apps(root)

    metadata: dict[str, Any] = {
        "generated_at": "auto",
        "root": str(root),
        "django_apps": apps,
        "installed_apps": installed_apps,
        "feature_flags": scan_feature_flags(root),
        "apps": {},
        "urls": [],
        "dependencies": {},
        "celery": {
            "broker": "redis",
            "backend": "redis",
            "beat": True,
            "tasks": [],
        },
        "infrastructure": {
            "framework": "Django",
            "api": "DRF",
            "database": "PostgreSQL",
            "cache": "Redis",
            "worker": "Celery",
            "storage": "S3",
            "deployment": "EC2",
        },
    }

    url_scanner = URLScanner(root)
    metadata["urls"] = url_scanner.scan()

    dep_scanner = DependencyScanner(root, apps)
    metadata["dependencies"] = dep_scanner.scan()

    for app_name in apps:
        app_dir = root / app_name
        if not app_dir.exists():
            continue
        app_scanner = AppScanner(root, app_name, app_dir)
        metadata["apps"][app_name] = app_scanner.scan()
        service_scanner = ServiceScanner(root, app_name, app_dir)
        metadata["apps"][app_name]["services"] = service_scanner.scan()
        metadata["apps"][app_name]["service_count"] = len(
            metadata["apps"][app_name]["services"]
        )

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metadata, indent=2))
    print(f"Generated: {output_path}")
    print(f"Apps: {len(metadata['apps'])}")
    print(f"URLs: {len(metadata['urls'])}")
    for app_name, app_data in metadata["apps"].items():
        print(
            f"  {app_name}: {app_data['model_count']} models, "
            f"{app_data['view_count']} views, "
            f"{app_data['service_count']} services"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate architecture metadata")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument("--root", type=str, default=".", help="Repository root")
    args = parser.parse_args()

    try:
        generate_architecture_metadata(Path(args.root), args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
