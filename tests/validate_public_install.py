from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import yaml


EXTENSION_CATALOG = (
    "https://raw.githubusercontent.com/orbyss-io/program-kit/"
    "main/catalogs/extensions.json"
)
WORKFLOW_CATALOG = (
    "https://raw.githubusercontent.com/orbyss-io/program-kit/"
    "main/catalogs/workflows.json"
)
BUNDLE_CATALOG = (
    "https://raw.githubusercontent.com/orbyss-io/program-kit/"
    "main/catalogs/bundles.json"
)
EXPECTED_HOOKS = {
    "after_specify",
    "after_plan",
    "before_implement",
    "after_implement",
}


def run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="program-kit-public-test-") as directory:
        project = Path(directory)
        run(
            "specify",
            "init",
            ".",
            "--force",
            "--non-interactive",
            "--integration",
            "codex",
            "--ignore-agent-tools",
            cwd=project,
        )
        run(
            "specify",
            "extension",
            "catalog",
            "add",
            EXTENSION_CATALOG,
            "--name",
            "program-kit",
            "--install-allowed",
            cwd=project,
        )
        run(
            "specify",
            "workflow",
            "catalog",
            "add",
            WORKFLOW_CATALOG,
            "--name",
            "program-kit",
            cwd=project,
        )
        run(
            "specify",
            "bundle",
            "catalog",
            "add",
            BUNDLE_CATALOG,
            "--id",
            "program-kit",
            "--policy",
            "install-allowed",
            cwd=project,
        )

        # Spec Kit 1.0.1's bundle adapter routes workflow IDs through the
        # local-dev installer. Preinstalling the catalog workflow avoids that
        # defect while preserving the bundle's pinned workflow reference.
        run("specify", "workflow", "add", "program-kit-bootstrap", cwd=project)
        run("specify", "bundle", "install", "program-kit", cwd=project)

        extensions = yaml.safe_load(
            (project / ".specify/extensions.yml").read_text(encoding="utf-8")
        )
        hooks = set(extensions.get("hooks", {}))
        if hooks != EXPECTED_HOOKS:
            raise AssertionError(f"Installed hooks {sorted(hooks)} != {sorted(EXPECTED_HOOKS)}")
        if "program-kit-governance" not in extensions.get("installed", []):
            raise AssertionError("Program Kit Governance extension was not registered")

        workflow = yaml.safe_load(
            (
                project
                / ".specify/workflows/program-kit-bootstrap/workflow.yml"
            ).read_text(encoding="utf-8")
        )
        if len(workflow.get("steps", [])) != 7:
            raise AssertionError("Installed bootstrap workflow must contain seven steps")

    print("Live public-catalog installation test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
