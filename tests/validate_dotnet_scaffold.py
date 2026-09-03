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
        assert state["dotnetSdk"] == "10.0.202"
        assert state["dotnetSdkSource"] == "program-kit-default"
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
        disabled_openapi = subprocess.run(
            [
                sys.executable,
                str(target / "eng/program-kit/openapi_pipeline.py"),
                "--repository",
                str(target),
            ],
            capture_output=True,
            text=True,
        )
        assert disabled_openapi.returncode == 0, disabled_openapi.stderr
        assert "not configured" in disabled_openapi.stdout

        nuget_config = target / "NuGet.config"
        nuget_text = nuget_config.read_text(encoding="utf-8")
        assert '<package pattern="*" />' in nuget_text
        assert '<package pattern="CShells.*" />' in nuget_text
        assert '<package pattern="Nuplane.*" />' in nuget_text
        assert state["files"]["NuGet.config"]["ownership"] == "scaffold"

        # Repositories installed before NuGet.config became consumer-owned receive the
        # routing correction once, but only while their managed copy is unmodified.
        legacy_nuget = nuget_text.replace(
            '<package pattern="*" />',
            '<package pattern="Microsoft.*" />\n      <package pattern="System.*" />',
        ).encode("utf-8")
        nuget_config.write_bytes(legacy_nuget)
        state_path = target / ".program-kit/managed.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["files"]["NuGet.config"] = {
            "ownership": "managed",
            "installedHash": hashlib.sha256(legacy_nuget).hexdigest(),
            "templateHash": hashlib.sha256(legacy_nuget).hexdigest(),
        }
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        ownership_migrated = run("--target", str(target), *approvals)
        assert ownership_migrated.returncode == 0, ownership_migrated.stderr
        assert "  ~ NuGet.config" in ownership_migrated.stdout
        assert nuget_config.read_text(encoding="utf-8") == nuget_text
        migrated_state = json.loads(state_path.read_text(encoding="utf-8"))
        assert migrated_state["files"]["NuGet.config"]["ownership"] == "scaffold"

        consumer_nuget = nuget_text.replace(
            "  </packageSources>",
            '    <add key="Consumer Feed" value="https://packages.example.invalid/v3/index.json" />\n  </packageSources>',
        ).replace(
            "  </packageSourceMapping>",
            '    <packageSource key="Consumer Feed">\n      <package pattern="Consumer.*" />\n    </packageSource>\n  </packageSourceMapping>',
        )
        nuget_config.write_text(consumer_nuget, encoding="utf-8")
        consumer_preserved = run("--target", str(target), *approvals)
        assert consumer_preserved.returncode == 0, consumer_preserved.stderr
        assert nuget_config.read_text(encoding="utf-8") == consumer_nuget

        unsafe_nuget = consumer_nuget.replace(
            '<package pattern="Consumer.*" />', '<package pattern="*" />'
        )
        nuget_config.write_text(unsafe_nuget, encoding="utf-8")
        unsafe_rejected = run("--target", str(target), *approvals)
        assert unsafe_rejected.returncode == 2, unsafe_rejected.stderr
        assert "must use namespace-specific patterns" in unsafe_rejected.stdout
        assert nuget_config.read_text(encoding="utf-8") == unsafe_nuget
        nuget_config.write_bytes(
            (ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/NuGet.config").read_bytes()
        )

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
        spa_configuration_path = spa_target / ".program-kit/spa-pkce.json"
        spa_configuration = json.loads(spa_configuration_path.read_text(encoding="utf-8"))
        assert spa_state["files"][".program-kit/spa-pkce.json"]["ownership"] == "configuration"
        realm = json.loads((spa_target / "deploy/keycloak/program-kit-realm.json").read_text(encoding="utf-8"))
        spa_client = next(client for client in realm["clients"] if client["clientId"] == "program-kit-spa")
        assert spa_client["publicClient"] is True and "secret" not in spa_client
        assert spa_client["redirectUris"] == [
            "http://localhost:5173/auth/callback",
            "http://localhost:5173/auth/renew-callback",
        ]
        assert spa_client["postLogoutRedirectUris"] == ["http://localhost:5173/signed-out"]
        assert not any("*" in uri for uri in spa_client["redirectUris"] + spa_client["postLogoutRedirectUris"])
        compose = (spa_target / "deploy/compose.application.yml").read_text(encoding="utf-8")
        assert "ClientSecret" not in compose and "local-program-kit-secret" not in compose
        playwright = (spa_target / "eng/program-kit/web/playwright.config.ts").read_text(encoding="utf-8")
        assert "trace: 'off'" in playwright and "screenshot: 'off'" in playwright and "video: 'off'" in playwright
        verifier = subprocess.run(
            [sys.executable, str(spa_target / "eng/program-kit/verify_spa_profile.py"),
             "--repository", str(spa_target)],
            capture_output=True,
            text=True,
        )
        assert verifier.returncode == 0, verifier.stderr

        spa_configuration["applicationOrigin"] = "http://localhost:4173"
        spa_configuration["redirectUris"] = [
            "http://localhost:4173/auth/callback",
            "http://localhost:4173/auth/renew-callback",
        ]
        spa_configuration["postLogoutRedirectUris"] = ["http://localhost:4173/signed-out"]
        spa_configuration["session"]["idleMinutes"] = 20
        spa_configuration_path.write_text(json.dumps(spa_configuration, indent=2) + "\n", encoding="utf-8")
        customized = run("--target", str(spa_target), *approvals, "--web-profile", "spa-pkce")
        assert customized.returncode == 0, customized.stderr
        customized_realm = json.loads(
            (spa_target / "deploy/keycloak/program-kit-realm.json").read_text(encoding="utf-8")
        )
        customized_client = next(
            client for client in customized_realm["clients"] if client["clientId"] == "program-kit-spa"
        )
        assert customized_client["redirectUris"] == spa_configuration["redirectUris"]
        assert customized_realm["ssoSessionIdleTimeout"] == 1200
        customized_settings = json.loads((spa_target / "hostsettings.json").read_text(encoding="utf-8"))
        assert customized_settings["ProgramKit"]["Web"]["AllowedOrigins"] == ["http://localhost:4173"]
        clean_spa = run(
            "--target", str(spa_target), "--profile-selected", "--check", "--web-profile", "spa-pkce"
        )
        assert clean_spa.returncode == 0, clean_spa.stderr

        invalid_spa = target / "invalid-spa-consumer"
        invalid_spa.mkdir()
        invalid_configuration = dict(spa_configuration)
        invalid_configuration["redirectUris"] = ["http://localhost:4173/*"]
        invalid_configuration_path = invalid_spa / ".program-kit/spa-pkce.json"
        invalid_configuration_path.parent.mkdir()
        invalid_configuration_path.write_text(
            json.dumps(invalid_configuration, indent=2) + "\n", encoding="utf-8"
        )
        wildcard_rejected = run(
            "--target", str(invalid_spa), *approvals, "--web-profile", "spa-pkce"
        )
        assert wildcard_rejected.returncode != 0 and "without wildcards" in wildcard_rejected.stderr
        assert not (invalid_spa / "deploy/keycloak/program-kit-realm.json").exists()

        override_target = target / "explicit-local-sdk-override"
        override_decisions = override_target / "docs/architecture/bootstrap-decisions.json"
        override_decisions.parent.mkdir(parents=True)
        override_decisions.write_text(
            json.dumps(
                {
                    "toolchain": {
                        "source": "override",
                        "pins": {"dotnet-sdk": "9.0.100"},
                        "override_reason": "The user explicitly retained the local SDK",
                    },
                    "overrides": [
                        {
                            "id": "managed-toolchain-version",
                            "decision": "Retain .NET SDK 9.0.100",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        override_installed = run("--target", str(override_target), *approvals)
        assert override_installed.returncode == 0, override_installed.stderr
        overridden_global = json.loads(
            (override_target / "global.json").read_text(encoding="utf-8")
        )
        assert overridden_global["sdk"]["version"] == "9.0.100"
        override_state = json.loads(
            (override_target / ".program-kit/managed.json").read_text(encoding="utf-8")
        )
        assert override_state["dotnetSdk"] == "9.0.100"
        assert override_state["dotnetSdkSource"] == "override"

        invalid_override = target / "invalid-local-sdk-override"
        invalid_decisions = invalid_override / "docs/architecture/bootstrap-decisions.json"
        invalid_decisions.parent.mkdir(parents=True)
        invalid_decisions.write_text(
            json.dumps(
                {
                    "toolchain": {
                        "source": "override",
                        "pins": {"dotnet-sdk": "9.0.100"},
                        "override_reason": "",
                    },
                    "overrides": [],
                }
            ),
            encoding="utf-8",
        )
        invalid_result = run("--target", str(invalid_override), *approvals)
        assert invalid_result.returncode != 0
        assert "override is incomplete" in invalid_result.stderr

    print("Program Kit .NET scaffold lifecycle passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
