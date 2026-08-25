from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


REPOSITORY = "https://raw.githubusercontent.com/orbyss-io/program-kit"
V020 = f"{REPOSITORY}/v0.2.0/catalogs"
CURRENT = f"{REPOSITORY}/main/catalogs"
EXPECTED_HOOKS = {
    "before_specify",
    "after_specify",
    "after_plan",
    "before_implement",
    "after_implement",
}
EXPECTED_STEPS = [
    "intake",
    "research",
    "review-assessment",
    "constitution-begin",
    "constitution-draft",
    "review-constitution",
    "constitution-ratify",
    "architecture",
    "tooling",
    "specification-roadmap",
    "review-bootstrap",
    "readiness",
]


def run(*args: str, cwd: Path, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        input=input_text,
        text=True,
        check=True,
        capture_output=True,
    )


def replace_catalogs(project: Path, base: str) -> None:
    specify = project / ".specify"
    (specify / "extension-catalogs.yml").write_text(
        yaml.safe_dump(
            {
                "catalogs": [
                    {
                        "name": "program-kit",
                        "url": f"{base}/extensions.json",
                        "priority": 10,
                        "install_allowed": True,
                        "description": "Program Kit upgrade regression",
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (specify / "workflow-catalogs.yml").write_text(
        yaml.safe_dump(
            {
                "catalogs": [
                    {
                        "name": "program-kit",
                        "url": f"{base}/workflows.json",
                        "priority": 1,
                        "install_allowed": True,
                        "description": "Program Kit upgrade regression",
                    }
                ]
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (specify / "bundle-catalogs.yml").write_text(
        yaml.safe_dump(
            {
                "schema_version": "1.0",
                "catalogs": [
                    {
                        "id": "program-kit",
                        "url": f"{base}/bundles.json",
                        "priority": 10,
                        "install_policy": "install-allowed",
                    }
                ],
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def manifest_version(path: Path, section: str) -> str:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return value[section]["version"]


def installed_versions(project: Path) -> dict[str, str]:
    specify = project / ".specify"
    registry = json.loads(
        (specify / "workflows/workflow-registry.json").read_text(encoding="utf-8")
    )
    records = json.loads((specify / "bundle-records.json").read_text(encoding="utf-8"))
    bundle = next(record for record in records["bundles"] if record["bundle_id"] == "program-kit")
    extension_record = next(
        component
        for component in bundle["contributed_components"]
        if component["kind"] == "extensions"
        and component["id"] == "program-kit-governance"
    )
    return {
        "extension": manifest_version(
            specify / "extensions/program-kit-governance/extension.yml", "extension"
        ),
        "workflow": manifest_version(
            specify / "workflows/program-kit-bootstrap/workflow.yml", "workflow"
        ),
        "workflow registry": registry["workflows"]["program-kit-bootstrap"]["version"],
        "bundle record": bundle["version"],
        "bundle extension record": extension_record["version"],
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="program-kit-public-upgrade-") as directory:
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
        replace_catalogs(project, V020)

        # Reproduce a genuine public v0.2.0 consumer installation, including
        # the Spec Kit 1.0.1 workflow-preinstallation workaround.
        run("specify", "workflow", "add", "program-kit-bootstrap", cwd=project)
        run("specify", "bundle", "install", "program-kit", cwd=project)
        initial = installed_versions(project)
        if set(initial.values()) != {"0.2.0"}:
            raise AssertionError(f"Expected a coherent v0.2.0 installation, got {initial}")

        replace_catalogs(project, CURRENT)

        # Capture the historical unsafe order. Bundle update refreshes the
        # extension and bundle record, but cannot refresh the separately owned
        # workflow in Spec Kit 1.0.1.
        run(
            "specify",
            "bundle",
            "update",
            "program-kit",
            "--integration",
            "codex",
            cwd=project,
            input_text="y\n",
        )
        mixed = installed_versions(project)
        if mixed["workflow"] != "0.2.0" or mixed["extension"] != "0.3.1":
            raise AssertionError(f"Regression did not reproduce the mixed installation: {mixed}")

        governance = (
            project
            / ".specify/extensions/program-kit-governance/scripts/governance_state.py"
        )
        preflight = subprocess.run(
            [sys.executable, str(governance), "validate-installation"],
            cwd=project,
            text=True,
            capture_output=True,
        )
        output = preflight.stdout + preflight.stderr
        if preflight.returncode == 0:
            raise AssertionError("Mixed-version installation unexpectedly passed preflight")
        for phrase in (
            "version-incoherent",
            "specify workflow update program-kit-bootstrap",
            "specify bundle update program-kit --integration codex",
        ):
            if phrase not in output:
                raise AssertionError(f"Preflight output is missing {phrase!r}: {output}")

        # Apply the documented repair in the mandatory order.
        run(
            "specify",
            "workflow",
            "update",
            "program-kit-bootstrap",
            cwd=project,
            input_text="y\n",
        )
        run(
            "specify",
            "bundle",
            "update",
            "program-kit",
            "--integration",
            "codex",
            cwd=project,
            input_text="y\n",
        )
        repaired = installed_versions(project)
        if set(repaired.values()) != {"0.3.1"}:
            raise AssertionError(f"Upgrade repair did not converge on v0.3.1: {repaired}")
        run(sys.executable, str(governance), "validate-installation", cwd=project)

        extensions = yaml.safe_load(
            (project / ".specify/extensions.yml").read_text(encoding="utf-8")
        )
        hooks = set(extensions.get("hooks", {}))
        if hooks != EXPECTED_HOOKS:
            raise AssertionError(f"Installed hooks {sorted(hooks)} != {sorted(EXPECTED_HOOKS)}")

        workflow = yaml.safe_load(
            (
                project / ".specify/workflows/program-kit-bootstrap/workflow.yml"
            ).read_text(encoding="utf-8")
        )
        step_ids = [step["id"] for step in workflow.get("steps", [])]
        if step_ids != EXPECTED_STEPS:
            raise AssertionError(f"Installed workflow steps {step_ids} != {EXPECTED_STEPS}")

    print("Live public-catalog v0.2.0 to v0.3.1 upgrade test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
