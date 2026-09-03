from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORTER = (
    ROOT
    / "src/dotnet/ProgramKit.OpenApi.Exporter/bin/Release/net10.0/ProgramKit.OpenApi.Exporter.dll"
)
PIPELINE = ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/eng/program-kit/openapi_pipeline.py"


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=180)


def write_fixture(repository: Path) -> None:
    targets = ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/eng/program-kit/ProgramKit.Build.targets"
    (repository / "WebFeature.csproj").write_text(
        f"""<Project Sdk=\"Microsoft.NET.Sdk\">
  <PropertyGroup>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <IsPackable>true</IsPackable>
    <PackageId>ProgramKit.OpenApiFixture</PackageId>
    <AssemblyName>ProgramKit.OpenApiFixture</AssemblyName>
    <Version>1.0.0</Version>
    <ProgramKitFeatureIdentity>Fixture.Web</ProgramKitFeatureIdentity>
    <ProgramKitFeatureRoutes>/orders</ProgramKitFeatureRoutes>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include=\"CShells.Abstractions\" Version=\"0.0.29-preview.147\" PrivateAssets=\"all\" />
    <PackageReference Include=\"CShells.AspNetCore.Abstractions\" Version=\"0.0.29-preview.147\" PrivateAssets=\"all\" />
    <PackageReference Include=\"Microsoft.AspNetCore.OpenApi\" Version=\"10.0.11\" PrivateAssets=\"all\" />
  </ItemGroup>
  <Import Project=\"{targets.as_posix()}\" />
</Project>
""",
        encoding="utf-8",
    )
    (repository / "FixtureWebFeature.cs").write_text(
        """using CShells.AspNetCore.Features;
using CShells.Features;
using CShells.Lifecycle;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace ProgramKit.OpenApiFixture;

[ShellFeature(name: "Fixture.Web", DisplayName = "Fixture Web")]
public sealed class FixtureWebFeature : IWebShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddOpenApi("v1");
        services.AddShellInitializer<ForbiddenInitializer>(LifecyclePhase.Start, order: 0);
    }

    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment) =>
        endpoints.MapGet("orders/{id}", (string id) => new OrderResponse(id)).WithName("GetOrder");
}

public sealed record OrderResponse(string Id);

public sealed class ForbiddenInitializer : IShellInitializer
{
    public Task InitializeAsync(CancellationToken cancellationToken)
    {
        File.WriteAllText("initializer-ran.txt", "unsafe");
        return Task.CompletedTask;
    }
}
""",
        encoding="utf-8",
    )
    shutil.copyfile(ROOT / "NuGet.config", repository / "NuGet.config")
    (repository / "hostsettings.json").write_text("{}\n", encoding="utf-8")
    (repository / "shells.json").write_text(
        json.dumps(
            {
                "CShells": {
                    "Shells": {
                        "default": {
                            "Features": {"ProgramKitTasks": {}, "Fixture.Web": {}},
                            "Configuration": {
                                "WebRouting": {"Path": "", "RoutePrefix": "api/v1"}
                            },
                        }
                    }
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (repository / "openapi-contract.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "identity": "fixture-api-v1",
                "documentName": "v1",
                "shell": "default",
                "producer": {
                    "kind": "ProgramKit.OpenApi.Exporter",
                    "version": "0.8.6-preview.1",
                },
                "features": ["Fixture.Web"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    if not EXPORTER.is_file():
        raise AssertionError("Build ProgramKit.OpenApi.Exporter in Release before this test")
    with tempfile.TemporaryDirectory(prefix="program-kit-openapi-exporter-") as value:
        repository = Path(value)
        write_fixture(repository)
        packages = repository / "packages"
        packed = run(
            [
                "dotnet",
                "pack",
                "WebFeature.csproj",
                "-c",
                "Release",
                "-o",
                str(packages),
                "--configfile",
                str(repository / "NuGet.config"),
            ],
            repository,
        )
        if packed.returncode != 0:
            raise AssertionError(f"fixture pack failed:\n{packed.stdout}{packed.stderr}")

        raw = repository / "artifacts/openapi/fixture.raw.json"
        evidence = repository / ".program-kit/evidence/openapi-export.json"
        command = [
            "dotnet",
            str(EXPORTER),
            "--repository",
            str(repository),
            "--packages",
            str(packages),
            "--shells",
            str(repository / "shells.json"),
            "--hostsettings",
            str(repository / "hostsettings.json"),
            "--contract",
            str(repository / "openapi-contract.json"),
            "--output",
            str(raw),
            "--evidence",
            str(evidence),
        ]
        exported = run(command, repository)
        if exported.returncode != 0:
            raise AssertionError(f"composed OpenAPI export failed:\n{exported.stdout}{exported.stderr}")
        document = json.loads(raw.read_text(encoding="utf-8"))
        if "/api/v1/orders/{id}" not in document.get("paths", {}):
            raise AssertionError(f"composed route is absent from OpenAPI: {document.get('paths')}")
        recorded = json.loads(evidence.read_text(encoding="utf-8"))
        if recorded.get("contractFeatures") != ["Fixture.Web"]:
            raise AssertionError(f"export evidence lost feature coverage: {recorded}")
        if recorded.get("composedFeatures") != ["Fixture.Web"]:
            raise AssertionError(f"export evidence included a host-owned feature: {recorded}")
        side_effects = recorded.get("sideEffects", {})
        if any(
            side_effects.get(name)
            for name in ("listenerStarted", "consumerHostedServicesStarted", "shellInitializersRun")
        ):
            raise AssertionError(f"exporter claims a consumer runtime side effect: {recorded}")
        if side_effects.get("pipelineMaterialized") is not True:
            raise AssertionError(f"exporter did not record API Explorer initialization: {recorded}")
        if (repository / "initializer-ran.txt").exists():
            raise AssertionError("OpenAPI export ran a shell lifecycle initializer")

        contract = json.loads((repository / "openapi-contract.json").read_text(encoding="utf-8"))
        contract["features"] = []
        (repository / "openapi-contract.json").write_text(
            json.dumps(contract, indent=2) + "\n", encoding="utf-8"
        )
        rejected = run(command, repository)
        if rejected.returncode != 2 or "feature coverage" not in rejected.stderr:
            raise AssertionError("incomplete activated-feature coverage was accepted")

        generator = repository / "tools/openapi-generator"
        application = repository / "src/web"
        generator.mkdir(parents=True)
        application.mkdir(parents=True)
        for directory in (generator, application):
            (directory / "package.json").write_text("{}\n", encoding="utf-8")
            (directory / "package-lock.json").write_text("{}\n", encoding="utf-8")
        (application / "tsconfig.json").write_text("{}\n", encoding="utf-8")
        fake_npm = repository / "fake_npm.py"
        fake_npm.write_text(
            """from pathlib import Path
import sys
if sys.argv[1:3] == ["run", "generate"]:
    target = Path.cwd() / "generated/types.ts"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("export interface Order { id: string }\\n", encoding="utf-8")
raise SystemExit(0)
""",
            encoding="utf-8",
        )
        staged_packages = repository / "artifacts/runnable-host/packages"
        staged_packages.mkdir(parents=True)
        for package in packages.glob("*.nupkg"):
            shutil.copyfile(package, staged_packages / package.name)
        managed = repository / "eng/program-kit"
        (managed / ".config").mkdir(parents=True)
        shutil.copyfile(
            ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/eng/program-kit/openapi_contracts.py",
            managed / "openapi_contracts.py",
        )
        shutil.copyfile(
            ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/eng/program-kit/.config/dotnet-tools.json",
            managed / ".config/dotnet-tools.json",
        )
        contract.update(
            {
                "features": ["Fixture.Web"],
                "packageClosure": "artifacts/runnable-host/packages",
                "rawDocument": "artifacts/openapi/fixture.pipeline.raw.json",
                "artifact": "contracts/openapi/fixture.json",
                "baseline": "contracts/openapi/fixture.baseline.json",
                "compatibility": {
                    "oasdiffVersion": "1.29.1",
                    "approval": "contracts/openapi/fixture.breaking-change.json",
                },
                "generator": {
                    "directory": "tools/openapi-generator",
                    "packageJson": "tools/openapi-generator/package.json",
                    "lockFile": "tools/openapi-generator/package-lock.json",
                    "script": "generate",
                    "generatedTypes": "tools/openapi-generator/generated/types.ts",
                },
                "application": {
                    "directory": "src/web",
                    "packageJson": "src/web/package.json",
                    "lockFile": "src/web/package-lock.json",
                    "script": "typecheck",
                    "tsconfig": "src/web/tsconfig.json",
                },
            }
        )
        (repository / "openapi-contract.json").write_text(
            json.dumps(contract, indent=2) + "\n", encoding="utf-8"
        )
        registry = repository / ".program-kit/openapi-contracts.json"
        registry.parent.mkdir(exist_ok=True)
        registry.write_text(
            json.dumps({"schemaVersion": 1, "contracts": ["openapi-contract.json"]}, indent=2)
            + "\n",
            encoding="utf-8",
        )
        pipelined = run(
            [
                sys.executable,
                str(PIPELINE),
                "--repository",
                str(repository),
                "--exporter",
                str(EXPORTER),
                "--npm-command",
                str(fake_npm),
                "--initialize-baselines",
            ],
            repository,
        )
        if pipelined.returncode != 0:
            raise AssertionError(
                f"producer-first OpenAPI pipeline failed:\n{pipelined.stdout}{pipelined.stderr}"
            )
        pipeline_evidence = json.loads(
            (repository / ".program-kit/evidence/openapi/pipeline.json").read_text(encoding="utf-8")
        )
        if pipeline_evidence.get("satisfied") is not True:
            raise AssertionError(f"pipeline did not preserve satisfied evidence: {pipeline_evidence}")
        if not (generator / "generated/types.ts").is_file():
            raise AssertionError("isolated client generation did not run")

    print("Side-effect-free composed OpenAPI producer and client pipeline validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
