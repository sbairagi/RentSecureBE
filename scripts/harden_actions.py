#!/usr/bin/env python3
"""Security hardening script for GitHub Actions workflows."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path("/Users/sbairagi/Desktop/MVP Project/RentSecureBE")
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
ACTIONS_DIR = REPO_ROOT / ".github" / "actions"

_ACTIONS = [
    ("actions/checkout", "v4", "34e114876b0b11c390a56381ad16ebd13914f8d5"),
    ("actions/setup-python", "v5", "a26af69be951a213d495a4c3e4e4022e16d87065"),
    ("actions/cache", "v4", "0057852bfaa89a56745cba8c7296529d2fc39830"),
    ("actions/upload-artifact", "v4", "ea165f8d65b6e75b540449e92b4886f43607fa02"),
    ("actions/download-artifact", "v4", "d3f86a106a0bac45b974a628896c90dbdf5c8093"),
    ("step-security/harden-runner", "v2", "9af89fc71515a100421586dfdb3dc9c984fbf411"),
    (
        "actions/dependency-review-action",
        "v5.0.0",
        "a1d282b36b6f3519aa1f3fc636f609c47dddb294",
    ),  # noqa: E501
    (
        "aquasecurity/trivy-action",
        "v0.36.0",
        "ed142fd0673e97e23eac54620cfb913e5ce36c25",
    ),  # noqa: E501
    ("gitleaks/gitleaks-action", "v2", "ff98106e4c7b2bc287b24eaf42907196329070c7"),
    ("semgrep/semgrep-action", "v1", "713efdd345f3035192eaa63f56867b88e63e4e5d"),
    (
        "github/codeql-action/upload-sarif",
        "v4",
        "54f647b7e1bb85c95cddabcd46b0c578ec92bc1a",
    ),  # noqa: E501
    ("github/codeql-action/analyze", "v4", "54f647b7e1bb85c95cddabcd46b0c578ec92bc1a"),
    ("github/codeql-action/init", "v4", "54f647b7e1bb85c95cddabcd46b0c578ec92bc1a"),
    ("ossf/scorecard-action", "v2.0.0", "13ec8c77e8a5dae7e0a0d47bde3e3004df15d34f"),
    (
        "SonarSource/sonarcloud-github-action",
        "v5.0.0",
        "ffc3010689be73b8e5ae0c57ce35968afd7909e8",
    ),  # noqa: E501
    (
        "marocchino/sticky-pull-request-comment",
        "v2",
        "773744901bac0e8cbb5a0dc842800d45e9b2b405",
    ),  # noqa: E501
    ("appleboy/ssh-action", "v0.1.7", "d91a1af6f57cd4478ceee14d7705601dafabaa19"),
]

SHA_PIN: dict[str, str] = {
    f"{name}@{ver}": f"{name}@{sha}  # {ver}" for name, ver, sha in _ACTIONS
}

DEFAULT_PERMISSIONS = "permissions:\n  contents: read\n"

PERMISSIONS_OVERRIDE: dict[str, str | None] = {
    "ci.yml": "permissions:\n"
    "  contents: read\n"
    "  security-events: write\n"
    "  id-token: write\n"
    "  actions: read\n",
    "rollback.yml": "permissions:\n"
    "  contents: read\n"
    "  deployments: write\n"
    "  pull-requests: write\n",
    "runtime-measurement.yml": "permissions:\n"
    "  contents: read\n"
    "  actions: read\n"
    "  pull-requests: write\n",
    "ci-metrics.yml": "permissions:\n"
    "  contents: read\n"
    "  actions: read\n"
    "  pull-requests: write\n",
    "quality.yml": "permissions:\n  contents: read\n  security-events: write\n",
    "security.yml": None,
    "security-deep.yml": None,
    "architecture-guard.yml": "permissions:\n"
    "  contents: read\n"
    "  security-events: write\n"
    "  id-token: write\n",
}

CONCURRENCY_OVERRIDE: dict[str, str | None] = {
    "ci.yml": None,
    "security-deep.yml": None,
    "nightly.yml": None,
    "weekly.yml": None,
    "architecture-guard.yml": None,
    "test.yml": "concurrency:\n"
    "  group: test-${{ github.ref }}\n"
    "  cancel-in-progress: true\n",
    "security.yml": "concurrency:\n"
    "  group: security-${{ github.ref }}\n"
    "  cancel-in-progress: true\n",
    "sbom.yml": "concurrency:\n"
    "  group: sbom-${{ github.ref }}\n"
    "  cancel-in-progress: true\n",
    "deploy.yml": "concurrency:\n"
    "  group: deploy-${{ github.ref }}\n"
    "  cancel-in-progress: true\n",
    "rollback.yml": "concurrency:\n"
    "  group: rollback-${{ github.ref }}\n"
    "  cancel-in-progress: true\n",
    "runtime-measurement.yml": "concurrency:\n"
    "  group: runtime-measurement-${{ github.ref }}\n"
    "  cancel-in-progress: true\n",
    "ci-metrics.yml": "concurrency:\n"
    "  group: ci-metrics-${{ github.ref }}\n"
    "  cancel-in-progress: true\n",
    "quality.yml": "concurrency:\n"
    "  group: quality-${{ github.ref }}\n"
    "  cancel-in-progress: true\n",
    "performance.yml": None,
    "architecture.yml": "concurrency:\n"
    "  group: architecture-${{ github.ref }}\n"
    "  cancel-in-progress: true\n",
    "lint.yml": "concurrency:\n"
    "  group: lint-${{ github.ref }}\n"
    "  cancel-in-progress: true\n",
    "mutation.yml": "concurrency:\n"
    "  group: mutation-${{ github.ref }}\n"
    "  cancel-in-progress: true\n",
    "hypothesis.yml": "concurrency:\n"
    "  group: hypothesis-${{ github.ref }}\n"
    "  cancel-in-progress: true\n",
    "contract-tests.yml": "concurrency:\n"
    "  group: contract-tests-${{ github.ref }}\n"
    "  cancel-in-progress: true\n",
    "deploy-readiness.yml": "concurrency:\n"
    "  group: deploy-readiness-${{ github.ref }}\n"
    "  cancel-in-progress: true\n",
    "django-check.yml": "concurrency:\n"
    "  group: django-check-${{ github.ref }}\n"
    "  cancel-in-progress: true\n",
    "migration-rollback.yml": "concurrency:\n"
    "  group: migration-rollback-${{ github.ref }}\n"
    "  cancel-in-progress: true\n",
    "load-test.yml": None,
    "benchmark.yml": None,
}


def action_replacements(content: str) -> str:
    for old, new in SHA_PIN.items():
        content = content.replace(old, new)
    return content


def has_permissions(content: str) -> bool:
    return bool(re.search(r"^permissions:\s*\n", content, re.MULTILINE))


def has_concurrency(content: str) -> bool:
    return bool(re.search(r"^concurrency:\s*\n", content, re.MULTILINE))


def add_permissions(content: str, workflow_name: str) -> str:
    if has_permissions(content):
        return content
    permissions = PERMISSIONS_OVERRIDE.get(workflow_name, DEFAULT_PERMISSIONS)
    if permissions is None:
        return content
    match = re.search(
        r"(^name:.*)(?=\njobs:)",
        content,
        re.DOTALL,
    )
    if match:
        insert_point = match.end(1)
        return (
            content[:insert_point] + "\n" + permissions + "\n" + content[insert_point:]
        )
    return re.sub(r"(\njobs:)", "\n" + permissions + r"\1", content, count=1)


def add_concurrency(content: str, workflow_name: str) -> str:
    if has_concurrency(content):
        return content
    concurrency = CONCURRENCY_OVERRIDE.get(workflow_name)
    if concurrency is None:
        return content
    return re.sub(r"(\\njobs:)", concurrency + r"\1", content, count=1)


def process_file(path: Path, workflow_name: str) -> None:
    text = path.read_text(encoding="utf-8")
    original = text

    text = action_replacements(text)

    if path.parent.name == "workflows":
        text = add_permissions(text, workflow_name)
        text = add_concurrency(text, workflow_name)

    if text != original:
        resolved = path.resolve()
        try:
            resolved.relative_to(REPO_ROOT)
        except ValueError:
            print(f"Skipped: {path.relative_to(REPO_ROOT)} (outside repo root)")
            return
        resolved.write_text(text, encoding="utf-8")
        print(f"Updated: {path.relative_to(REPO_ROOT)}")
    else:
        print(f"Unchanged: {path.relative_to(REPO_ROOT)}")


def main() -> None:
    for workflow in sorted(WORKFLOWS_DIR.glob("*.yml")):
        process_file(workflow, workflow.name)
    for action in sorted(ACTIONS_DIR.glob("*/*.yml")):
        process_file(action, action.name)


if __name__ == "__main__":
    main()
