from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "extensions/program-kit-dotnet/scripts/dotnet_sync.py"


def run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *arguments], capture_output=True, text=True)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="program-kit-dotnet-sync-") as value:
        target = Path(value)

        rejected = run("--target", str(target))
        assert rejected.returncode == 3, rejected.stderr
        assert not (target / "global.json").exists(), "The .NET scaffold ran without profile selection."

        runtime_unaccepted = run("--target", str(target), "--profile-selected")
        assert runtime_unaccepted.returncode == 4, runtime_unaccepted.stderr
        assert not (target / "global.json").exists(), "The .NET scaffold ran without an accepted runtime ADR."

        preview_unapproved = run(
            "--target", str(target), "--profile-selected", "--host-runtime-accepted"
        )
        assert preview_unapproved.returncode == 5, preview_unapproved.stderr
        assert not (target / "global.json").exists(), "The .NET scaffold ran without preview-source approval."

        missing_target = target / "missing"
        unchecked = run("--target", str(missing_target), "--profile-selected", "--check")
        assert unchecked.returncode == 1, unchecked.stderr
        assert not missing_target.exists(), "A read-only drift check changed the repository."

        approvals = ("--profile-selected", "--host-runtime-accepted", "--preview-sources-approved")
        installed = run("--target", str(target), *approvals)
        assert installed.returncode == 0, installed.stderr
        state = json.loads((target / ".program-kit/managed.json").read_text(encoding="utf-8"))
        assert state["programKitVersion"]
        assert (target / "eng/program-kit/ProgramKit.Build.props").is_file()
        assert (target / "Directory.Build.props").is_file()
        build_script = (target / "eng/program-kit/Build.ps1").read_text(encoding="utf-8")
        assert "[switch]$LockedMode" in build_script
        assert "Join-Path (Join-Path $artifacts 'packages') $version" in build_script
        runnable_builder = (target / "eng/program-kit/runnable_host.py").read_text(encoding="utf-8")
        assert "def is_runtime_package" in runnable_builder
        assert '"analyzer", "dotnettool", "template"' in runnable_builder
        application_ci = (target / ".github/workflows/application-ci.yml").read_text(encoding="utf-8")
        application_release = (target / ".github/workflows/application-release.yml").read_text(encoding="utf-8")
        assert "-SkipRunnableHost -LockedMode" in application_ci
        assert "Build.ps1 -LockedMode" in application_release
        assert "runnable-host.json" in application_release
        assert "containerimage.digest" in application_release

        obsolete_content = b"managed by the previous Program Kit\n"
        state_path = target / ".program-kit/managed.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        for relative in (
            ".program-kit/application-bundle.schema.json",
            "eng/program-kit/create_application_bundle.py",
        ):
            path = target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(obsolete_content)
            state["files"][relative] = {
                "ownership": "managed",
                "installedHash": hashlib.sha256(obsolete_content).hexdigest(),
                "templateHash": hashlib.sha256(obsolete_content).hexdigest(),
            }
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        upgraded = run("--target", str(target), *approvals)
        assert upgraded.returncode == 0, upgraded.stderr
        assert not (target / ".program-kit/application-bundle.schema.json").exists()
        assert not (target / "eng/program-kit/create_application_bundle.py").exists()

        clean = run("--target", str(target), "--profile-selected", "--check")
        assert clean.returncode == 0, clean.stderr

        managed = target / "eng/program-kit/ProgramKit.Build.props"
        managed.write_text(managed.read_text(encoding="utf-8") + "<!-- consumer edit -->\n", encoding="utf-8")
        conflicted = run("--target", str(target), *approvals)
        assert conflicted.returncode == 2, conflicted.stderr
        assert "consumer edit" in managed.read_text(encoding="utf-8")

        obsolete_conflict = target / "obsolete-conflict"
        installed_conflict = run("--target", str(obsolete_conflict), *approvals)
        assert installed_conflict.returncode == 0, installed_conflict.stderr
        old_path = obsolete_conflict / "eng/program-kit/create_application_bundle.py"
        old_path.parent.mkdir(parents=True, exist_ok=True)
        old_path.write_text("consumer-owned historical tool\n", encoding="utf-8")
        conflict_state_path = obsolete_conflict / ".program-kit/managed.json"
        conflict_state = json.loads(conflict_state_path.read_text(encoding="utf-8"))
        conflict_state["files"]["eng/program-kit/create_application_bundle.py"] = {
            "ownership": "managed",
            "installedHash": "0" * 64,
            "templateHash": "0" * 64,
        }
        conflict_state_path.write_text(json.dumps(conflict_state, indent=2) + "\n", encoding="utf-8")
        preserved = run("--target", str(obsolete_conflict), *approvals)
        assert preserved.returncode == 2, preserved.stderr
        assert old_path.read_text(encoding="utf-8") == "consumer-owned historical tool\n"

        browser_target = target / "browser-consumer"
        design = browser_target / "docs/initial-design.md"
        design.parent.mkdir(parents=True)
        design.write_text("# Design\n\nA React browser UI calls authenticated HTTP features.\n", encoding="utf-8")
        browser_installed = run("--target", str(browser_target), *approvals)
        assert browser_installed.returncode == 0, browser_installed.stderr
        browser_state = json.loads((browser_target / ".program-kit/managed.json").read_text(encoding="utf-8"))
        assert browser_state["webProfile"] == "bff-cookie"
        assert browser_state["webProfileContract"] == "bff-cookie-v1"
        assert browser_state["webThreatModel"] == "program-kit-web-threat-model-v1"
        assert browser_state["webSecurityEvidence"] == "program-kit-web-security-evidence-v1"
        bff_settings = json.loads((browser_target / "hostsettings.json").read_text(encoding="utf-8"))
        assert bff_settings["ProgramKit"]["Web"]["Profile"] == "BffCookie"
        assert (browser_target / "deploy/keycloak/program-kit-realm.json").is_file()
        assert (browser_target / "eng/program-kit/web/package-lock.json").is_file()
        assert (browser_target / ".program-kit/security/web-security-evidence.json").is_file()
        assert (browser_target / "docs/architecture/program-kit/web-security-threat-model.md").is_file()

        mentioned_alternative = target / "mentioned-spa-alternative"
        alternative_design = mentioned_alternative / "INITIAL_DESIGN.md"
        alternative_design.parent.mkdir(parents=True)
        alternative_design.write_text(
            "# Design\n\nA React browser UI; spa-pkce-v1 is an alternative, not the selected design.\n",
            encoding="utf-8",
        )
        alternative_installed = run("--target", str(mentioned_alternative), *approvals)
        assert alternative_installed.returncode == 0, alternative_installed.stderr
        alternative_state = json.loads(
            (mentioned_alternative / ".program-kit/managed.json").read_text(encoding="utf-8")
        )
        assert alternative_state["webProfile"] == "bff-cookie"

        spa_target = target / "explicit-spa-consumer"
        spa_installed = run("--target", str(spa_target), *approvals, "--web-profile", "spa-pkce")
        assert spa_installed.returncode == 0, spa_installed.stderr
        spa_state = json.loads((spa_target / ".program-kit/managed.json").read_text(encoding="utf-8"))
        assert spa_state["webProfile"] == "spa-pkce"
        assert spa_state["webThreatModel"] == "program-kit-web-threat-model-v1"
        assert spa_state["webSecurityEvidence"] == "program-kit-web-security-evidence-v1"
        spa_settings = json.loads((spa_target / "hostsettings.json").read_text(encoding="utf-8"))
        assert spa_settings["ProgramKit"]["Web"]["Profile"] == "SpaPkce"
        assert spa_settings["ProgramKit"]["Web"]["AllowedOrigins"] == ["http://localhost:5173"]

    print("Program Kit .NET scaffold lifecycle passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
