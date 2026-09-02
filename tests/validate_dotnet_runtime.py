from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    program_version = (root / "VERSION").read_text(encoding="utf-8").strip()
    runtime_version = (root / "RUNTIME_VERSION").read_text(encoding="utf-8").strip()
    if program_version != "0.8.3":
        raise AssertionError(f"Unexpected Program Kit version: {program_version}")
    if runtime_version != "0.8.3-preview.1":
        raise AssertionError(f"Unexpected runtime artifact version: {runtime_version}")

    version_props = (root / "eng/ProgramKit.Version.props").read_text(encoding="utf-8")
    if f"<ProgramKitVersion>{runtime_version}</ProgramKitVersion>" not in version_props:
        raise AssertionError("Runtime project version does not match RUNTIME_VERSION")

    consumer_versions = (
        root
        / "extensions/program-kit-dotnet/templates/dotnet/files/eng/program-kit/ProgramKit.Packages.props"
    ).read_text(encoding="utf-8")
    for package in ("ProgramKit.Analyzers", "ProgramKit.Tasks.Abstractions", "ProgramKit.Tasks"):
        pattern = rf'Include="{re.escape(package)}" Version="{re.escape(runtime_version)}"'
        if re.search(pattern, consumer_versions) is None:
            raise AssertionError(f"Consumer template does not pin {package} to {runtime_version}")

    analyzer = (root / "src/dotnet/ProgramKit.Analyzers/ProgramKitAnalyzer.cs").read_text(encoding="utf-8")
    for rule_id in ("PK1001", "PK1002", "PK1003", "PK1004", "PK1005"):
        if rule_id not in analyzer:
            raise AssertionError(f"Program Kit analyzer does not declare {rule_id}")
    editorconfig = (
        root / "extensions/program-kit-dotnet/templates/dotnet/files/.editorconfig"
    ).read_text(encoding="utf-8")
    for rule_id in ("PK1003", "PK1004", "PK1005"):
        if f"dotnet_diagnostic.{rule_id}.severity = error" not in editorconfig:
            raise AssertionError(f"Consumer template does not enforce {rule_id}")
    engineering = (
        root / "extensions/program-kit-dotnet/references/dotnet-engineering.md"
    ).read_text(encoding="utf-8")
    for phrase in ("Validate inputs", "Prepare the operation state", "one named type", "XML documentation"):
        if phrase not in engineering:
            raise AssertionError(f".NET engineering guidance is missing: {phrase}")

    host_workflow = (root / ".github/workflows/publish-host-image.yml").read_text(encoding="utf-8")
    if "< RUNTIME_VERSION" not in host_workflow or "steps.runtime_version.outputs.value" not in host_workflow:
        raise AssertionError("Host workflow does not derive its image tag from RUNTIME_VERSION")

    global_json = (root / "global.json").read_text(encoding="utf-8")
    if '"version": "10.0.202"' not in global_json or '"rollForward": "latestPatch"' not in global_json:
        raise AssertionError("The .NET SDK feature band and patch policy are not pinned")
    dockerfile = (root / "src/dotnet/ProgramKit.Host/Dockerfile").read_text(encoding="utf-8")
    if dockerfile.count("@sha256:") < 3 or "dotnet restore ProgramKit.slnx --locked-mode" not in dockerfile:
        raise AssertionError("Host image inputs must be digest-pinned and restored in locked mode")
    if "HEALTHCHECK" in dockerfile or "PROGRAMKIT_BUNDLE" in dockerfile:
        raise AssertionError("The shallow host image must not own application health or release-bundle policy")
    host_root = root / "src/dotnet/ProgramKit.Host"
    project = ElementTree.parse(host_root / "ProgramKit.Host.csproj")
    packages = {item.attrib["Include"] for item in project.iter() if item.tag.endswith("PackageReference")}
    allowed = {"CShells.AspNetCore", "Nuplane", "Nuplane.Loading", "Nuplane.Sources.Directory"}
    if packages != allowed:
        raise AssertionError(f"ProgramKit.Host is not feature-free: {sorted(packages - allowed)}")
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in host_root.rglob("*.cs")
        if "obj" not in path.parts
    )
    for forbidden in ("Npgsql", "ApplicationBundle", "ProgramKitWeb", "MapOpenApi", "health/ready"):
        if forbidden in source:
            raise AssertionError(f"ProgramKit.Host contains application/release concern: {forbidden}")
    for required in ("AddNuplane", "AutoloadPackages", "AddCShellsAspNetCore", "MapShells"):
        if required not in source:
            raise AssertionError(f"ProgramKit.Host is missing shallow-host plumbing: {required}")
    for project in ("ProgramKit.Host", "ProgramKit.Tasks", "ProgramKit.Tasks.Abstractions", "ProgramKit.Analyzers"):
        if not (root / "src/dotnet" / project / "packages.lock.json").is_file():
            raise AssertionError(f"Missing dependency lock for {project}")

    print("Program Kit .NET runtime versions are coherent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
