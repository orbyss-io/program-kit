from __future__ import annotations

import subprocess
import tempfile
import zipfile
from pathlib import Path

import yaml


EXPECTED_HOOKS = {
    "after_specify",
    "after_plan",
    "before_implement",
    "after_implement",
}


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
            "add",
            str(extracted_extension),
            "--dev",
            cwd=project,
        )
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
        if len(steps) != 7:
            raise AssertionError(f"Installed workflow has {len(steps)} steps, expected 7")

    print("Packaged extension and workflow install test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
