from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "extensions/program-kit-dotnet/templates/dotnet/files/eng/Invoke-RepositoryVerification.ps1"
)
RESTORE_SOURCE = SOURCE.with_name("Restore.ps1")


def run(shell: str, script: Path, environment: dict[str, str], *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            shell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-Mode",
            "CI",
            *arguments,
        ],
        capture_output=True,
        text=True,
        env=environment,
    )


def main() -> int:
    shell = (
        (shutil.which("powershell") if os.name == "nt" else None)
        or shutil.which("pwsh")
        or shutil.which("powershell")
    )
    if shell is None:
        raise AssertionError("PowerShell is required to validate the repository verification hook")
    source_text = SOURCE.read_text(encoding="utf-8")
    if "Invoke-Expression" in source_text or "ConsumerVerificationPath" in source_text:
        raise AssertionError("consumer verification must use the fixed literal eng/verify.ps1 path")

    with tempfile.TemporaryDirectory(prefix="program-kit-verification-hook-") as value:
        repository = Path(value) / "consumer"
        managed = repository / "eng"
        managed.mkdir(parents=True)
        wrapper = managed / SOURCE.name
        shutil.copyfile(SOURCE, wrapper)
        shutil.copyfile(RESTORE_SOURCE, managed / RESTORE_SOURCE.name)
        shutil.copyfile(
            ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/NuGet.config",
            repository / "NuGet.config",
        )
        marker = repository / "verification.marker"
        environment = os.environ.copy()
        environment["PROGRAMKIT_TEST_VERIFICATION_MARKER"] = str(marker)
        (managed / "Build.ps1").write_text(
            "param([switch]$SkipReleaseBundle, [switch]$LockedMode, [switch]$VerifyArchitecture)\n"
            "if (-not $VerifyArchitecture) { throw 'Fallback must own fresh architecture verification' }\n"
            "Set-Content -LiteralPath $env:PROGRAMKIT_TEST_VERIFICATION_MARKER -Value 'fallback'\n",
            encoding="utf-8",
        )

        # This unit fixture isolates wrapper/environment routing. Actual compiled
        # architecture failures are exercised by validate_architecture_recipe and
        # validate_standalone_engineering, not by its fake dotnet command.
        (managed / 'repository_architecture.py').write_text(
            "import os,sys\nfrom pathlib import Path\n"
            "root=Path(sys.argv[sys.argv.index('--repository')+1]).resolve()\n"
            "assert Path(os.environ['NUGET_PACKAGES']).resolve()==root/'artifacts/cache/nuget/packages'\n"
            "(root/'architecture.marker').write_text('checked')\n",encoding='utf-8')
        absent = run(shell, wrapper, environment)
        if absent.returncode != 0 or marker.read_text(encoding="utf-8").strip() != "fallback":
            raise AssertionError(f"absent consumer hook did not use managed fallback: {absent.stdout}{absent.stderr}")

        consumer = repository / "eng/verify.ps1"
        consumer.parent.mkdir(parents=True, exist_ok=True)
        consumer.write_text(
            "Set-Content -LiteralPath $env:PROGRAMKIT_TEST_VERIFICATION_MARKER -Value 'consumer'\n",
            encoding="utf-8",
        )
        marker.unlink()
        present = run(shell, wrapper, environment)
        if present.returncode != 0 or marker.read_text(encoding="utf-8").strip() != "consumer":
            raise AssertionError(f"consumer verification did not replace the fallback: {present.stdout}{present.stderr}")

        consumer.write_text("exit 23\n", encoding="utf-8")
        failed = run(shell, wrapper, environment)
        if failed.returncode == 0:
            raise AssertionError("consumer verification failure did not fail the managed entry point")

        consumer.unlink()
        consumer.mkdir()
        unsafe = run(shell, wrapper, environment)
        if unsafe.returncode == 0 or "regular repository file" not in (unsafe.stdout + unsafe.stderr):
            raise AssertionError("non-file consumer verification path was accepted")

        # Scoped execution must select the native runner without invoking either
        # acceptance path, forward filters literally and preserve its failure.
        (managed / 'repository_verification.py').write_text(
            "import json,os,sys\nfrom pathlib import Path\n"
            "Path(os.environ['PROGRAMKIT_TEST_VERIFICATION_MARKER']).write_text(json.dumps(sys.argv[1:]))\n"
            "sys.exit(int(os.environ.get('PROGRAMKIT_TEST_EXIT','0')))\n", encoding='utf-8')
        scoped = run(shell, wrapper, environment, '-Scope', 'Focused', '-Projects',
                     'tests/Notes.Tests/Notes.Tests.csproj', '-TestArguments', '--filter-uid=one', '-Plan')
        if scoped.returncode or '--test-argument=--filter-uid=one' not in marker.read_text():
            raise AssertionError('Scoped selection/filter forwarding failed: ' + scoped.stdout + scoped.stderr)
        environment['PROGRAMKIT_TEST_EXIT'] = '9'
        failed = run(shell, wrapper, environment, '-Scope', 'Affected', '-ChangedFrom', 'initial-commit')
        if failed.returncode == 0 or 'No full-suite fallback' not in failed.stdout + failed.stderr:
            raise AssertionError('Scoped native failure did not propagate without acceptance fallback')
        for arguments in (('-Projects', 'tests/Notes.Tests/Notes.Tests.csproj'), ('-Plan',)):
            narrowed = run(shell, wrapper, environment, *arguments)
            if narrowed.returncode == 0 or 'Acceptance cannot be narrowed' not in narrowed.stdout + narrowed.stderr:
                raise AssertionError('Acceptance accepted a scoped parameter')

        adapter = managed / 'verify-scoped.ps1'
        adapter.write_text('param($Scope,$Projects,$TestArguments,$ChangedPaths,$ChangedFrom,$FeatureDirectory,$Configuration,[switch]$Restore,[switch]$Plan)\n'
                           "if ($Scope -ne 'Affected' -or $ChangedFrom -ne 'initial-commit') { throw 'Wrong scoped arguments' }\n"
                           "Set-Content -LiteralPath $env:PROGRAMKIT_TEST_VERIFICATION_MARKER -Value 'scoped-adapter'\n", encoding='utf-8')
        delegated = run(shell, wrapper, environment, '-Scope', 'Affected', '-ChangedFrom', 'initial-commit')
        if delegated.returncode or marker.read_text().strip() != 'scoped-adapter':
            raise AssertionError('Fixed scoped consumer adapter did not receive the scope')
        adapter.write_text('exit 23\n', encoding='utf-8')
        if run(shell, wrapper, environment, '-Scope', 'Affected', '-ChangedFrom', 'initial-commit').returncode == 0:
            raise AssertionError('Scoped adapter failure was accepted')

    print("Managed acceptance and scoped routing, filter forwarding, failure propagation and path safety passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
