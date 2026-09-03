from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UPDATER = ROOT / "scripts/upgrade_program_kit.py"


def run(*command: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, cwd=cwd, text=True, encoding="utf-8", errors="replace",
        capture_output=True, check=False,
    )


def require_success(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode != 0:
        raise AssertionError(f"{label} failed:\n{result.stdout}{result.stderr}")


def version(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("  version:"):
            return line.split(":", 1)[1].strip().strip('"\'')
    raise AssertionError(f"No version in {path}")


def set_manifest_version(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    marker = f'  version: "{old}"'
    if marker not in text:
        raise AssertionError(f"Could not seed old version in {path}")
    path.write_text(text.replace(marker, f'  version: "{new}"', 1), encoding="utf-8")


def main() -> int:
    expected = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    with tempfile.TemporaryDirectory(prefix="program-kit-local-upgrade-") as directory:
        project = Path(directory)
        initialized = run(
            "specify", "init", ".", "--force", "--non-interactive",
            "--integration", "codex", "--script", "py", "--ignore-agent-tools",
            cwd=project,
        )
        require_success(initialized, "Spec Kit initialization")
        primitive_commands = (
            ("specify", "workflow", "add", str(ROOT / "workflows/program-kit-bootstrap"), "--dev"),
            ("specify", "extension", "add", str(ROOT / "extensions/program-kit-governance"), "--dev", "--force"),
            ("specify", "extension", "add", str(ROOT / "extensions/program-kit-dotnet"), "--dev", "--force"),
            ("specify", "preset", "add", "--dev", str(ROOT / "presets/program-kit-governance-preset")),
        )
        for primitive in primitive_commands:
            require_success(run(*primitive, cwd=project), f"seed {' '.join(primitive[1:3])}")
        old = "0.0.0"
        manifests = (
            project / ".specify/extensions/program-kit-governance/extension.yml",
            project / ".specify/extensions/program-kit-dotnet/extension.yml",
            project / ".specify/presets/program-kit-governance-preset/preset.yml",
            project / ".specify/workflows/program-kit-bootstrap/workflow.yml",
        )
        for manifest in manifests:
            set_manifest_version(manifest, expected, old)
        workflow_registry_path = project / ".specify/workflows/workflow-registry.json"
        workflow_registry = json.loads(workflow_registry_path.read_text(encoding="utf-8"))
        workflow_registry["workflows"]["program-kit-bootstrap"]["version"] = old
        workflow_registry_path.write_text(json.dumps(workflow_registry), encoding="utf-8")
        preset_registry_path = project / ".specify/presets/.registry"
        preset_registry = json.loads(preset_registry_path.read_text(encoding="utf-8"))
        preset_registry["presets"]["program-kit-governance-preset"]["version"] = old
        preset_registry_path.write_text(json.dumps(preset_registry), encoding="utf-8")
        bundle_records = {
            "schema_version": "1.0",
            "bundles": [{
                "bundle_id": "program-kit",
                "version": old,
                "contributed_components": [
                    {"kind": "extensions", "id": "program-kit-governance", "version": old},
                    {"kind": "extensions", "id": "program-kit-dotnet", "version": old},
                    {"kind": "presets", "id": "program-kit-governance-preset", "version": old},
                ],
            }],
        }
        (project / ".specify/bundle-records.json").write_text(
            json.dumps(bundle_records), encoding="utf-8"
        )
        managed = project / ".program-kit/managed.json"
        managed.parent.mkdir(parents=True)
        managed.write_text(
            json.dumps({
                "schemaVersion": 1,
                "programKitVersion": old,
                "dotnetSdk": "10.0.202",
                "dotnetSdkSource": "program-kit-default",
                "webProfile": "none",
                "persistenceProfile": "none",
                "files": {},
            }),
            encoding="utf-8",
        )
        bootstrap_decisions = project / "docs/architecture/bootstrap-decisions.json"
        bootstrap_decisions.parent.mkdir(parents=True)
        bootstrap_decisions.write_text(
            json.dumps({
                "schema_version": "1.0",
                "default_profile": {"id": "program-kit-standard", "version": old},
                "selected_profiles": [],
                "choices": [{
                    "id": "first-slice",
                    "decision": "Keep the accepted first slice",
                    "source": "explicit-intake",
                    "rationale": "It is the approved consumer outcome",
                    "override": "Use a later accepted decision",
                }],
                "overrides": [],
                "acknowledgements": [],
                "unresolved": [],
                "deferred": [],
            }),
            encoding="utf-8",
        )
        immutable_decisions = bootstrap_decisions.read_bytes()
        command = (
            sys.executable, str(UPDATER), "--release-root", str(ROOT),
            "--target", str(project), "--integration", "codex",
        )
        installed = run(*command, cwd=project)
        require_success(installed, "local release upgrade")
        order = (
            "Resolve bundle composition record",
            "Install bootstrap workflow",
            "Install governance extension",
            "Install .NET extension",
            "Remove prior governance preset",
            "Install governance preset",
            "Resynchronize managed .NET baseline",
            "Verify managed .NET baseline convergence",
            "Validate cross-component version coherence",
            "Record accepted governed upgrade",
        )
        offsets = [installed.stdout.find(label) for label in order]
        if any(offset < 0 for offset in offsets) or offsets != sorted(offsets):
            raise AssertionError(f"Component mutations were not visibly sequential: {installed.stdout}")

        if {version(path) for path in manifests} != {expected}:
            raise AssertionError("Local release installation left mixed component manifests")
        state = json.loads(managed.read_text(encoding="utf-8"))
        if state.get("programKitVersion") != expected:
            raise AssertionError(f"Managed baseline did not advance to {expected}: {state}")
        final_records = json.loads(
            (project / ".specify/bundle-records.json").read_text(encoding="utf-8")
        )["bundles"][0]
        final_versions = {final_records["version"]} | {
            component["version"] for component in final_records["contributed_components"]
        }
        if final_versions != {expected}:
            raise AssertionError(f"Bundle record did not converge: {final_records}")
        if "Resynchronize managed .NET baseline" not in installed.stdout:
            raise AssertionError("Updater did not report managed baseline synchronization")
        if bootstrap_decisions.read_bytes() != immutable_decisions:
            raise AssertionError("Updater rewrote immutable bootstrap decisions")
        upgrade_state = json.loads(
            (project / ".specify/governance/program-kit-upgrades.json").read_text(
                encoding="utf-8"
            )
        )
        accepted = upgrade_state["upgrades"][-1]
        if (
            accepted.get("status") != "Accepted"
            or accepted.get("baseline_profile_version") != old
            or accepted.get("previous_installed_version") != old
            or accepted.get("installed_version") != expected
        ):
            raise AssertionError(f"Updater did not record governed version authority: {accepted}")

        lock = project / ".specify/program-kit-upgrade.lock"
        lock.write_text("test lock\n", encoding="utf-8")
        locked = run(*command, cwd=project)
        if locked.returncode != 2 or "PKU106" not in locked.stderr:
            raise AssertionError("Concurrent component mutation lock was not rejected")
        if not lock.is_file():
            raise AssertionError("Updater removed a lock it did not own")

    print("Sequential offline/local Program Kit upgrade and coherence validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
