from __future__ import annotations

import subprocess
import tempfile
import zipfile
from pathlib import Path

import yaml


EXPECTED_HOOKS = {
    "before_constitution",
    "before_specify",
    "after_specify",
    "after_plan",
    "after_tasks",
    "before_implement",
    "after_implement",
}

EXPECTED_STEPS = [
    "codex-execution-preflight",
    "codex-execution-boundary",
    "intake",
    "research",
    "validate-assessment",
    "write-assessment-review",
    "review-assessment",
    "accept-assessment",
    "constitution-draft",
    "validate-constitution-draft",
    "write-constitution-review",
    "review-constitution",
    "constitution-ratify",
    "architecture",
    "tooling",
    "specification-roadmap",
    "synchronize-roadmap",
    "validate-bootstrap-consistency",
    "validate-bootstrap",
    "write-bootstrap-review",
    "review-bootstrap",
    "accept-bootstrap",
    "readiness",
    "complete-bootstrap",
    "report-completion-result",
]


def run(*args: str, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    extension_zip = root / "artifacts" / f"program-kit-governance-{version}.zip"
    dotnet_zip = root / "artifacts" / f"program-kit-dotnet-{version}.zip"
    preset_zip = root / "artifacts" / f"program-kit-governance-preset-{version}.zip"
    workflow_zip = root / "artifacts" / f"program-kit-bootstrap-{version}.zip"
    bundle_zip = root / "artifacts" / f"program-kit-{version}.zip"
    initializers = {
        suffix: root / "artifacts" / f"Initialize-ProgramKit-{version}.{suffix}"
        for suffix in ("cmd", "sh")
    }
    if not all(
        path.is_file()
        for path in (
            extension_zip,
            dotnet_zip,
            preset_zip,
            workflow_zip,
            bundle_zip,
            *initializers.values(),
        )
    ):
        raise FileNotFoundError("Build release assets before running the install test")
    for suffix, initializer in initializers.items():
        if initializer.read_bytes() != (root / f"Initialize-ProgramKit.{suffix}").read_bytes():
            raise AssertionError(
                f"Versioned {suffix} consumer initializer differs from the root template"
            )

    for release_zip in (extension_zip, dotnet_zip, preset_zip, workflow_zip, bundle_zip):
        with zipfile.ZipFile(release_zip, "r") as archive:
            forbidden_entries = []
            for name in archive.namelist():
                parts = Path(name).parts
                if (
                    name.endswith(".rules")
                    or name.endswith(".pyc")
                    or "__pycache__" in parts
                    or "bin" in parts
                    or "obj" in parts
                    or name.endswith(".nupkg")
                ):
                    forbidden_entries.append(name)
            if forbidden_entries:
                raise AssertionError(
                    f"{release_zip.name} contains generated output or approval rules: "
                    f"{forbidden_entries}"
                )

    with tempfile.TemporaryDirectory(prefix="program-kit-release-test-") as directory:
        project = Path(directory)
        extracted_extension = project / "release-extension"
        extracted_dotnet = project / "release-dotnet-extension"
        extracted_preset = project / "release-governance-preset"
        with zipfile.ZipFile(extension_zip, "r") as archive:
            archive.extractall(extracted_extension)
        if not (extracted_extension / "extension.yml").is_file():
            raise AssertionError("Extension release ZIP must contain extension.yml at its root")
        if not (extracted_extension / "scripts/governance_state.py").is_file():
            raise AssertionError("Extension release ZIP must contain the governance-state validator")
        for path in (
            "scripts/codex_bootstrap_preflight.py",
            "references/codex-desktop-windows.md",
        ):
            if not (extracted_extension / path).is_file():
                raise AssertionError(f"Extension release ZIP is missing {path}")
        packaged_rule_files = list(extracted_extension.rglob("*.rules"))
        if packaged_rule_files:
            raise AssertionError(
                f"Extension release ZIP must not contain approval rules: {packaged_rule_files}"
            )
        packaged_guidance = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (
                extracted_extension
                / "commands/speckit.program-kit-governance.bootstrap.md",
                extracted_extension / "references/codex-desktop-windows.md",
            )
        )
        for phrase in (
            "Always allow",
            "first four argument tokens",
            "program-kit-bootstrap.rules",
            "approve only this exact prefix",
        ):
            if phrase in packaged_guidance:
                raise AssertionError(
                    f"Extension release ZIP reintroduced escalation guidance: {phrase}"
                )
        for phrase in (
            "normal user-owned PowerShell or WSL",
            "Do not call a shell tool",
            "git clone --no-hardlinks --no-checkout",
        ):
            if phrase not in packaged_guidance:
                raise AssertionError(
                    f"Extension release ZIP is missing safe boundary guidance: {phrase}"
                )
        for reference in ("vertical-slicing.md", "modularity-and-contracts.md", "default-adoption.md"):
            if not (extracted_extension / "references" / reference).is_file():
                raise AssertionError(f"Extension release ZIP is missing {reference}")
        with zipfile.ZipFile(dotnet_zip, "r") as archive:
            archive.extractall(extracted_dotnet)
        if not (extracted_dotnet / "extension.yml").is_file():
            raise AssertionError(".NET extension release ZIP must contain extension.yml at its root")
        for path in (
            "scripts/dotnet_sync.py",
            "references/dotnet-engineering.md",
            "templates/dotnet/files/.editorconfig",
        ):
            if not (extracted_dotnet / path).is_file():
                raise AssertionError(f".NET extension release ZIP is missing {path}")
        with zipfile.ZipFile(preset_zip, "r") as archive:
            archive.extractall(extracted_preset)
        if not (extracted_preset / "preset.yml").is_file():
            raise AssertionError("Governance preset release ZIP must contain preset.yml at its root")
        for path in (
            "templates/spec-governance.md",
            "templates/plan-governance.md",
            "templates/tasks-governance.md",
        ):
            if not (extracted_preset / path).is_file():
                raise AssertionError(f"Governance preset release ZIP is missing {path}")

        run(
            "specify",
            "init",
            ".",
            "--force",
            "--non-interactive",
            "--integration",
            "codex",
            "--script",
            "py",
            "--ignore-agent-tools",
            cwd=project,
        )
        run(
            "specify",
            "extension",
            "add",
            str(extracted_dotnet),
            "--dev",
            cwd=project,
        )
        run(
            "specify",
            "preset",
            "add",
            "--dev",
            str(extracted_preset),
            cwd=project,
        )
        if not (project / ".agents/skills/speckit-constitution/SKILL.md").is_file():
            raise AssertionError(
                "Spec Kit 1.0.1 did not install the core speckit.constitution command"
            )
        python_resolver = project / ".specify/scripts/python/resolve_template.py"
        if not python_resolver.is_file():
            raise AssertionError("Python-flavor consumer is missing resolve_template.py")
        constitution_skill_text = (
            project / ".agents/skills/speckit-constitution/SKILL.md"
        ).read_text(encoding="utf-8")
        if ".specify/scripts/python/resolve_template.py" not in constitution_skill_text:
            raise AssertionError("Constitution skill does not reference the Python resolver")
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
        installed_skill_text = bootstrap_skill.read_text(encoding="utf-8")
        if "Stop. Do not call a shell tool" not in installed_skill_text:
            raise AssertionError("Installed bootstrap skill lost its execution-boundary guidance")
        run("specify", "workflow", "add", str(workflow_zip), "--dev", cwd=project)

        extension_config = yaml.safe_load(
            (project / ".specify/extensions.yml").read_text(encoding="utf-8")
        )
        deployed_config = (
            project
            / ".specify/extensions/program-kit-governance/program-kit-governance-config.yml"
        )
        if not deployed_config.is_file():
            raise AssertionError("Program Kit configuration template was not scaffolded")
        hooks = set(extension_config.get("hooks", {}))
        if hooks != EXPECTED_HOOKS:
            raise AssertionError(f"Registered hooks {sorted(hooks)} != {sorted(EXPECTED_HOOKS)}")
        if "program-kit-dotnet" not in extension_config.get("installed", []):
            raise AssertionError("Program Kit .NET extension was not registered")
        if not (
            project / ".agents/skills/speckit-program-kit-dotnet-sync/SKILL.md"
        ).is_file():
            raise AssertionError(".NET sync command was not installed as a namespaced skill")

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

        # Spec Kit 1.0.1 resolves third-party primitives through their catalogs
        # even when a bundle is installed from a local ZIP. The archive is
        # therefore verified for its pinned component graph here; the live
        # public-catalog test validates catalog-backed bundle installation.
        with zipfile.ZipFile(bundle_zip, "r") as archive:
            packaged_bundle = yaml.safe_load(archive.read("bundle.yml"))
        component_graph = {
            (kind, entry["id"])
            for kind, entries in packaged_bundle["provides"].items()
            for entry in entries
        }
        if component_graph != {
            ("extensions", "program-kit-governance"),
            ("extensions", "program-kit-dotnet"),
            ("presets", "program-kit-governance-preset"),
            ("workflows", "program-kit-bootstrap"),
        }:
            raise AssertionError(f"Unexpected packaged bundle component graph: {component_graph}")

    print("Packaged component and bundle install test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
