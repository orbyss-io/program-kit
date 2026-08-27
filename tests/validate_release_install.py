from __future__ import annotations

import subprocess
import tempfile
import zipfile
from pathlib import Path

import yaml


EXPECTED_HOOKS = {
    "before_specify",
    "after_specify",
    "after_plan",
    "before_implement",
    "after_implement",
}

EXPECTED_STEPS = [
    "codex-execution-preflight",
    "codex-execution-boundary",
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


def run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    extension_zip = root / "artifacts" / f"program-kit-governance-{version}.zip"
    workflow_zip = root / "artifacts" / f"program-kit-bootstrap-{version}.zip"
    if not extension_zip.is_file() or not workflow_zip.is_file():
        raise FileNotFoundError("Build release assets before running the install test")

    with tempfile.TemporaryDirectory(prefix="program-kit-release-test-") as directory:
        project = Path(directory)
        extracted_extension = project / "release-extension"
        with zipfile.ZipFile(extension_zip, "r") as archive:
            archive.extractall(extracted_extension)
        if not (extracted_extension / "extension.yml").is_file():
            raise AssertionError("Extension release ZIP must contain extension.yml at its root")
        if not (extracted_extension / "scripts/governance_state.py").is_file():
            raise AssertionError("Extension release ZIP must contain the governance-state validator")
        for path in (
            "scripts/codex_bootstrap_preflight.py",
            "references/codex-desktop-windows.md",
            "templates/codex/program-kit-bootstrap.rules",
        ):
            if not (extracted_extension / path).is_file():
                raise AssertionError(f"Extension release ZIP is missing {path}")
        for reference in ("vertical-slicing.md", "modularity-and-contracts.md"):
            if not (extracted_extension / "references" / reference).is_file():
                raise AssertionError(f"Extension release ZIP is missing {reference}")

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
        if not (project / ".agents/skills/speckit-constitution/SKILL.md").is_file():
            raise AssertionError(
                "Spec Kit 1.0.1 did not install the core speckit.constitution command"
            )
        run(
            "specify",
            "extension",
            "add",
            str(extracted_extension),
            "--dev",
            cwd=project,
        )
        bootstrap_skill = (
            project
            / ".agents/skills/speckit-program-kit-governance-bootstrap/SKILL.md"
        )
        if not bootstrap_skill.is_file():
            raise AssertionError("Codex-safe Program Kit bootstrap skill was not installed")
        if "Do not first attempt" not in bootstrap_skill.read_text(encoding="utf-8"):
            raise AssertionError("Installed bootstrap skill lost its execution-boundary guidance")
        run("specify", "workflow", "add", str(workflow_zip), "--dev", cwd=project)

        extension_config = yaml.safe_load(
            (project / ".specify/extensions.yml").read_text(encoding="utf-8")
        )
        deployed_config = (
            project
            / ".specify/extensions/program-kit-governance/program-kit-config.yml"
        )
        if not deployed_config.is_file():
            raise AssertionError("Program Kit configuration template was not scaffolded")
        hooks = set(extension_config.get("hooks", {}))
        if hooks != EXPECTED_HOOKS:
            raise AssertionError(f"Registered hooks {sorted(hooks)} != {sorted(EXPECTED_HOOKS)}")

        installed_workflow = yaml.safe_load(
            (
                project
                / ".specify/workflows/program-kit-bootstrap/workflow.yml"
            ).read_text(encoding="utf-8")
        )
        steps = installed_workflow.get("steps", [])
        step_ids = [step["id"] for step in steps]
        if step_ids != EXPECTED_STEPS:
            raise AssertionError(f"Installed workflow steps {step_ids} != {EXPECTED_STEPS}")

    print("Packaged extension and workflow install test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
