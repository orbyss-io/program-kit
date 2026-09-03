from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    dotnet = shutil.which("dotnet")
    if dotnet is None:
        raise RuntimeError("dotnet is required for the consumer package-source restore test")

    with tempfile.TemporaryDirectory(prefix="program-kit-consumer-restore-") as value:
        repository = Path(value)
        project = repository / "Consumer.Tests.csproj"
        project.write_text(
            """<Project Sdk=\"MSTest.Sdk/4.3.3\">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include=\"Testcontainers\" Version=\"4.14.0\" />
    <PackageReference Include=\"TngTech.ArchUnitNET\" Version=\"0.13.4\" />
  </ItemGroup>
</Project>
""",
            encoding="utf-8",
        )
        packages = repository / ".packages"
        environment = os.environ.copy()
        environment["NUGET_PACKAGES"] = str(packages)
        result = subprocess.run(
            [
                dotnet,
                "restore",
                str(project),
                "--configfile",
                str(ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/NuGet.config"),
                "--force-evaluate",
            ],
            cwd=repository,
            env=environment,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise AssertionError(
                "Consumer restore through the scaffolded source mapping failed:\n"
                + result.stdout
                + result.stderr
            )
        lock = repository / "packages.lock.json"
        if not lock.is_file():
            raise AssertionError("Consumer restore did not emit dependency lock evidence")
        lock_text = lock.read_text(encoding="utf-8")
        if not (packages / "mstest.sdk" / "4.3.3").is_dir():
            raise AssertionError("Consumer restore did not resolve MSTest.Sdk 4.3.3")
        for package in (
            "Testcontainers",
            "Docker.DotNet.Enhanced",
            "SSH.NET",
            "TngTech.ArchUnitNET",
            "CycleDetection",
            "Mono.Cecil",
        ):
            if f'\"{package}\"' not in lock_text:
                raise AssertionError(f"Consumer dependency closure is missing {package}")

    print("Consumer-owned public package graph restores through protected source routing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
