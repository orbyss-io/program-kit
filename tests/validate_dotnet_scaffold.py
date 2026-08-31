from __future__ import annotations

import json
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

        installed = run("--target", str(target), "--profile-selected")
        assert installed.returncode == 0, installed.stderr
        state = json.loads((target / ".program-kit/managed.json").read_text(encoding="utf-8"))
        assert state["programKitVersion"]
        assert (target / "eng/program-kit/ProgramKit.Build.props").is_file()
        assert (target / "Directory.Build.props").is_file()
        build_script = (target / "eng/program-kit/Build.ps1").read_text(encoding="utf-8")
        assert "[switch]$LockedMode" in build_script
        assert "Join-Path (Join-Path $artifacts 'packages') $version" in build_script
        bundle_builder = (target / "eng/program-kit/create_application_bundle.py").read_text(encoding="utf-8")
        assert "def is_runtime_package" in bundle_builder
        assert 'excluded_types = {"analyzer", "dotnettool", "template"}' in bundle_builder
        application_ci = (target / ".github/workflows/application-ci.yml").read_text(encoding="utf-8")
        application_release = (target / ".github/workflows/application-release.yml").read_text(encoding="utf-8")
        assert "-SkipBundle -LockedMode" in application_ci
        assert "Build.ps1 -LockedMode" in application_release

        clean = run("--target", str(target), "--profile-selected", "--check")
        assert clean.returncode == 0, clean.stderr

        managed = target / "eng/program-kit/ProgramKit.Build.props"
        managed.write_text(managed.read_text(encoding="utf-8") + "<!-- consumer edit -->\n", encoding="utf-8")
        conflicted = run("--target", str(target), "--profile-selected")
        assert conflicted.returncode == 2, conflicted.stderr
        assert "consumer edit" in managed.read_text(encoding="utf-8")

    print("Program Kit .NET scaffold lifecycle passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
