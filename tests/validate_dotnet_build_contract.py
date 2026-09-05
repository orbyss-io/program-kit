from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/eng/program-kit/Build.ps1"


def main() -> int:
    for path in (
        ROOT / "global.json",
        ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/global.json",
    ):
        value = json.loads(path.read_text(encoding="utf-8"))
        if value.get("test", {}).get("runner") != "Microsoft.Testing.Platform":
            raise AssertionError(f"{path} does not select Microsoft.Testing.Platform")

    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not shell:
        raise AssertionError("PowerShell is required to validate the managed Build.ps1 contract")
    with tempfile.TemporaryDirectory(prefix="program-kit-build-contract-") as value:
        repository = Path(value)
        managed = repository / "eng/program-kit"
        managed.mkdir(parents=True)
        shutil.copyfile(BUILD, managed / "Build.ps1")
        (repository / "VERSION").write_text("1.0.0\n", encoding="utf-8")
        (repository / "Consumer.slnx").write_text("<Solution />\n", encoding="utf-8")
        nuget_config = repository / "NuGet.config"
        nuget_config.write_text("<configuration />\n", encoding="utf-8")
        log = repository / "dotnet.log"
        tools = repository / "tools"
        tools.mkdir()
        if os.name == "nt":
            dotnet = tools / "dotnet.cmd"
            dotnet.write_text(
                "@echo off\r\n"
                f"echo %*^|%NUGET_PACKAGES%^|%NUGET_HTTP_CACHE_PATH%^|%NUGET_SCRATCH%^|"
                f"%NUGET_PLUGINS_CACHE_PATH%^|%DOTNET_CLI_HOME%^|%APPDATA%^|%LOCALAPPDATA%>>\"{log}\"\r\n"
                "exit /b 0\r\n",
                encoding="utf-8",
            )
        else:
            dotnet = tools / "dotnet"
            dotnet.write_text(
                "#!/bin/sh\n"
                f"printf '%s|%s|%s|%s|%s|%s|%s|%s\\n' \"$*\" \"$NUGET_PACKAGES\" "
                f"\"$NUGET_HTTP_CACHE_PATH\" \"$NUGET_SCRATCH\" \"$NUGET_PLUGINS_CACHE_PATH\" "
                f"\"$DOTNET_CLI_HOME\" \"$APPDATA\" \"$LOCALAPPDATA\" >> '{log}'\n",
                encoding="utf-8",
            )
            dotnet.chmod(0o755)
        environment = os.environ.copy()
        environment["PATH"] = str(tools) + os.pathsep + environment.get("PATH", "")
        hostile_profile = repository / "denied-roaming-profile/NuGet"
        hostile_profile.mkdir(parents=True)
        (hostile_profile / "NuGet.Config").write_text("<malformed", encoding="utf-8")
        environment["APPDATA"] = str(hostile_profile.parent)
        result = subprocess.run(
            [shell, "-NoProfile", "-File", str(managed / "Build.ps1"), "-SkipRunnableHost"],
            cwd=repository,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            raise AssertionError(f"managed Build.ps1 failed in restricted-profile fixture: {result.stdout}{result.stderr}")
        entries = log.read_text(encoding="utf-8").splitlines()
        restore = next((line for line in entries if line.startswith("restore ")), "")
        if "--configfile" not in restore or str(nuget_config) not in restore:
            raise AssertionError(f"restore did not bind the reviewed repository NuGet.config: {restore}")
        for expected in (
            repository / ".program-kit/cache/nuget/packages",
            repository / ".program-kit/cache/nuget/http",
            repository / ".program-kit/cache/nuget/scratch",
            repository / ".program-kit/cache/nuget/plugins",
            repository / ".program-kit/cache/dotnet-home",
        ):
            if str(expected) not in restore:
                raise AssertionError(f"restore did not use repository-owned NuGet cache {expected}: {restore}")
        if os.name == "nt":
            for expected in (
                repository / ".program-kit/cache/profile/roaming",
                repository / ".program-kit/cache/profile/local",
            ):
                if str(expected) not in restore:
                    raise AssertionError(f"restore did not isolate its Windows profile path {expected}: {restore}")
        test = next((line for line in entries if line.startswith("test ")), "")
        if "--solution" not in test or str(repository / "Consumer.slnx") not in test:
            raise AssertionError(f"managed Build.ps1 did not use MTP solution syntax: {test}")

    print("Restricted-profile NuGet restore and Microsoft.Testing.Platform build contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
