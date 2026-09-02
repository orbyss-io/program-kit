from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FEATURE_ID = "ConsumerOrders"
PACKAGE_ID = "ProgramKit.TestFeature"


def run(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {' '.join(command)}\n{result.stdout}\n{result.stderr}"
        )


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def create_consumer_feature(repository: Path) -> None:
    repository.mkdir(parents=True)
    (repository / "ConsumerFeature.csproj").write_text(
        """<Project Sdk=\"Microsoft.NET.Sdk\">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <IsPackable>true</IsPackable>
    <PackageId>ProgramKit.TestFeature</PackageId>
    <AssemblyName>ProgramKit.TestFeature</AssemblyName>
    <Version>1.0.0</Version>
    <ProgramKitFeatureIdentity>ConsumerOrders</ProgramKitFeatureIdentity>
    <ProgramKitFeatureRoutes>/orders</ProgramKitFeatureRoutes>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include=\"CShells.Abstractions\" Version=\"0.0.29-preview.147\" PrivateAssets=\"all\" />
    <PackageReference Include=\"Microsoft.Extensions.DependencyInjection.Abstractions\" Version=\"10.0.3\" PrivateAssets=\"all\" />
  </ItemGroup>
</Project>
""",
        encoding="utf-8",
        newline="\n",
    )
    (repository / "ConsumerOrdersFeature.cs").write_text(
        """using CShells.Features;
using CShells.Lifecycle;
using Microsoft.Extensions.DependencyInjection;

namespace ProgramKit.TestFeature;

[ShellFeature(name: \"ConsumerOrders\", DisplayName = \"Consumer Orders\")]
public sealed class ConsumerOrdersFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services) =>
        services.AddShellInitializer<ConsumerOrdersInitializer>(LifecyclePhase.Start, order: 0);
}

public sealed class ConsumerOrdersInitializer : IShellInitializer
{
    public Task InitializeAsync(CancellationToken cancellationToken)
    {
        var marker = Environment.GetEnvironmentVariable("PROGRAMKIT_TEST_FEATURE_MARKER")
            ?? throw new InvalidOperationException("The feature activation marker is not configured.");
        File.WriteAllText(marker, "ConsumerOrders activated");
        return Task.CompletedTask;
    }
}
""",
        encoding="utf-8",
        newline="\n",
    )
    target = ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/eng/program-kit/ProgramKit.Build.targets"
    (repository / "Directory.Build.targets").write_text(
        f'<Project><Import Project="{target.as_posix()}" /></Project>\n',
        encoding="utf-8",
        newline="\n",
    )
    shutil.copyfile(ROOT / "NuGet.config", repository / "NuGet.config")
    (repository / "VERSION").write_text("1.0.0\n", encoding="utf-8", newline="\n")
    (repository / "shells.json").write_text(
        json.dumps(
            {
                "CShells": {
                    "Shells": {
                        "default": {
                            "Name": "default",
                            "Features": {FEATURE_ID: {}},
                            "Configuration": {"WebRouting": {"Path": ""}},
                        }
                    }
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (repository / "hostsettings.json").write_text("{}\n", encoding="utf-8", newline="\n")


def wait_for_ready(process: subprocess.Popen[str], uri: str) -> dict:
    deadline = time.monotonic() + 45
    last_error = "host did not answer"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise AssertionError(f"ProgramKit.Host exited before readiness.\n{stdout}\n{stderr}")
        try:
            with urllib.request.urlopen(uri, timeout=2) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = str(error)
            time.sleep(0.25)
    process.terminate()
    stdout, stderr = process.communicate(timeout=10)
    raise AssertionError(f"ProgramKit.Host did not become ready: {last_error}\n{stdout}\n{stderr}")


def main() -> int:
    host = ROOT / "src/dotnet/ProgramKit.Host/bin/Release/net10.0/ProgramKit.Host.dll"
    if not host.is_file():
        raise AssertionError("Build ProgramKit.Host in Release configuration before running this fixture.")

    with tempfile.TemporaryDirectory(prefix="program-kit-feature-host-", ignore_cleanup_errors=True) as value:
        repository = Path(value) / "consumer"
        packages = repository / "artifacts/packages"
        bundle = repository / "artifacts/application-bundle.zip"
        cache = repository / ".bundle-cache"
        create_consumer_feature(repository)
        run(
            [
                "dotnet",
                "pack",
                "ConsumerFeature.csproj",
                "-c",
                "Release",
                "-o",
                str(packages),
                "--configfile",
                str(repository / "NuGet.config"),
            ],
            repository,
        )
        with __import__("zipfile").ZipFile(packages / f"{PACKAGE_ID}.1.0.0.nupkg") as archive:
            metadata = json.loads(archive.read("program-kit/feature.json"))
            if metadata.get("identity") != FEATURE_ID or metadata.get("routes") != ["/orders"]:
                raise AssertionError("managed feature metadata was not embedded deterministically")

        environment = os.environ.copy()
        environment["GITHUB_SHA"] = "0" * 40
        run(
            [
                sys.executable,
                str(
                    ROOT
                    / "extensions/program-kit-dotnet/templates/dotnet/files/eng/program-kit/create_application_bundle.py"
                ),
                "--repository",
                str(repository),
                "--packages",
                str(packages),
                "--output",
                str(bundle),
            ],
            repository,
            environment,
        )

        port = free_port()
        host_environment = os.environ.copy()
        host_environment["PROGRAMKIT_BUNDLE_PATH"] = str(bundle)
        host_environment["PROGRAMKIT_BUNDLE_CACHE"] = str(cache)
        activation_marker = repository / "consumer-orders.activated"
        host_environment["PROGRAMKIT_TEST_FEATURE_MARKER"] = str(activation_marker)
        host_environment["ASPNETCORE_URLS"] = f"http://127.0.0.1:{port}"
        host_environment["DOTNET_ENVIRONMENT"] = "Production"
        host_environment["Logging__LogLevel__Default"] = "Warning"
        process = subprocess.Popen(
            ["dotnet", str(host)],
            cwd=repository,
            env=host_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            readiness = wait_for_ready(process, f"http://127.0.0.1:{port}/health/ready")
            if readiness.get("status") != "ready":
                raise AssertionError(f"host returned unexpected readiness: {readiness}")
            if not activation_marker.is_file() or activation_marker.read_text(encoding="utf-8") != "ConsumerOrders activated":
                process.terminate()
                stdout, stderr = process.communicate(timeout=10)
                raise AssertionError(
                    f"consumer feature shell was not eagerly activated: {readiness}\n{stdout}\n{stderr}"
                )
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)

    print("Consumer feature package, bundle closure, and eager ProgramKit.Host activation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
