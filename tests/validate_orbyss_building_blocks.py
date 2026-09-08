from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "extensions/program-kit-building-blocks/references/orbyss-building-blocks.json"


def package_versions(path: Path) -> dict[str, str]:
    tree = ElementTree.parse(path)
    return {
        item.attrib["Include"]: item.attrib["Version"]
        for item in tree.iter()
        if item.tag.endswith("PackageVersion")
    }


def main() -> int:
    manifest = json.loads(REFERENCE.read_text(encoding="utf-8"))
    families = manifest["families"]
    expected_repositories = {
        "foundation": "https://github.com/orbyss-io/dotnet-foundation",
        "forms": "https://github.com/orbyss-io/forms",
        "localization": "https://github.com/orbyss-io/localization",
    }
    if set(families) != set(expected_repositories):
        raise AssertionError("The executable catalog must name exactly the three independent families.")
    for family_id, repository in expected_repositories.items():
        family = families[family_id]
        if family["repository"] != repository:
            raise AssertionError(f"{family_id} repository identity drifted.")
        if not re.fullmatch(r"\d+\.\d+\.\d+", family["releaseVersion"]):
            raise AssertionError("Building-block family versions must be exact stable SemVer pins.")

    packages = manifest["packages"]
    by_family_ecosystem: dict[tuple[str, str], set[str]] = {}
    for key, package in packages.items():
        if key != f'{package["ecosystem"]}:{package["packageId"]}':
            raise AssertionError(f"Package key is not canonical: {key}")
        if package["version"] != families[package["family"]]["releaseVersion"]:
            raise AssertionError(f"Package version is not pinned to its independent family release: {key}")
        by_family_ecosystem.setdefault((package["family"], package["ecosystem"]), set()).add(package["packageId"])
    expected_counts = {
        ("foundation", "nuget"): 22,
        ("foundation", "oci"): 1,
        ("forms", "nuget"): 15,
        ("forms", "npm"): 12,
        ("localization", "nuget"): 13,
    }
    actual_counts = {key: len(value) for key, value in by_family_ecosystem.items()}
    if actual_counts != expected_counts:
        raise AssertionError(f"Building-block family inventory drifted: {actual_counts}")
    if len(manifest["compositions"]) != 16:
        raise AssertionError("The executable catalog must retain all 16 governed compositions.")

    expected_activated_packages = {
        "Orbyss.Foundation.Authentication",
        "Orbyss.Foundation.Authentication.Assurance",
        "Orbyss.Foundation.Authentication.BffCookie",
        "Orbyss.Foundation.Authentication.ClientCredentials",
        "Orbyss.Foundation.Authentication.DownstreamApi",
        "Orbyss.Foundation.Authentication.DPoP",
        "Orbyss.Foundation.Authentication.SpaPkce",
        "Orbyss.Foundation.Authentication.TokenExchange",
        "Orbyss.Foundation.DomainEvents",
        "Orbyss.Foundation.Identity.Keycloak.Admin",
        "Orbyss.Foundation.Mcp.AspNetCore",
        "Orbyss.Foundation.Tasks",
        "Orbyss.Foundation.Web.Discovery",
        "Orbyss.Foundation.Web.OpenApi",
        "Orbyss.Foundation.Web.ProblemDetails",
        "Orbyss.Foundation.WebDefaults",
        "Orbyss.Forms.JsonForms",
        "Orbyss.Forms.Localization",
        "Orbyss.Forms.Management",
        "Orbyss.Forms.Management.Mcp.AspNetCore",
        "Orbyss.Forms.Storage.FileSystem",
        "Orbyss.Forms.Storage.InMemory",
        "Orbyss.Forms.Submissions",
        "Orbyss.Forms.Submissions.Mcp.AspNetCore",
        "Orbyss.Forms.Web.Management",
        "Orbyss.Forms.Web.Runtime",
        "Orbyss.Forms.Web.Submissions",
        "Orbyss.Localization.Formats",
        "Orbyss.Localization.Management",
        "Orbyss.Localization.Management.Mcp.AspNetCore",
        "Orbyss.Localization.Runtime",
        "Orbyss.Localization.Runtime.Mcp.AspNetCore",
        "Orbyss.Localization.Storage.FileSystem",
        "Orbyss.Localization.Storage.InMemory",
        "Orbyss.Localization.Web.Management",
        "Orbyss.Localization.Web.Runtime",
    }
    activated_packages = {package["packageId"] for package in packages.values() if package.get("activations")}
    if activated_packages != expected_activated_packages:
        raise AssertionError(f"CShell activation package inventory drifted: {sorted(activated_packages)}")
    keycloak_features = {
        activation["featureIdentity"]
        for activation in packages["nuget:Orbyss.Foundation.Identity.Keycloak.Admin"]["activations"]
    }
    if len(keycloak_features) != 10:
        raise AssertionError("The Keycloak adapter must retain its ten independently activated shell features.")

    def package_closure(requirements: list[dict], found: set[str] | None = None) -> set[str]:
        found = set() if found is None else found
        for requirement in requirements:
            key = requirement["package"]
            if key not in found:
                found.add(key)
                package_closure(packages[key]["requires"], found)
        return found

    for composition_id, composition in manifest["compositions"].items():
        possible = list(composition["requirements"])
        for group in composition["optionGroups"]:
            for option in group["options"].values():
                possible.extend(option["requirements"])
        if any(packages[key].get("activations") for key in package_closure(possible)):
            shell = composition["targetSlots"].get("shell")
            if shell != {"kind": "cshell-shell", "allowedRoles": ["composition"]}:
                raise AssertionError(f"{composition_id} can select shell features but has no exact shell target slot.")

    pins = package_versions(
        ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/.program-kit/eng/ProgramKit.Packages.props"
    )
    orbyss_pins = {key: value for key, value in pins.items() if key.startswith("Orbyss.")}
    expected_analyzer = {"Orbyss.Foundation.Analyzers": families["foundation"]["releaseVersion"]}
    if orbyss_pins != expected_analyzer:
        raise AssertionError("The managed .NET baseline must pin only the repository-wide analyzer exception.")
    directory_packages = (
        ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/Directory.Packages.props"
    ).read_text(encoding="utf-8")
    if "ProgramKit.BuildingBlocks.props" not in directory_packages:
        raise AssertionError("The .NET baseline no longer imports selected-only building-block pins.")
    if any(key.startswith("ProgramKit.") for key in pins):
        raise AssertionError("Published ProgramKit.* package IDs remain in the generated baseline.")

    template = ROOT / "extensions/program-kit-dotnet/templates/dotnet/files"
    nuget = (template / "NuGet.config").read_text(encoding="utf-8")
    host = json.loads((template / "hostsettings.json").read_text(encoding="utf-8"))
    dockerfile = (template / "Dockerfile").read_text(encoding="utf-8")
    release = (template / ".github/workflows/application-release.yml").read_text(encoding="utf-8")
    if 'pattern="Orbyss.*"' not in nuget:
        raise AssertionError("NuGet source mapping does not explicitly cover Orbyss building blocks.")
    if "Foundation" not in host or "ProgramKit" in host:
        raise AssertionError("Host configuration must use the Foundation configuration root.")
    if host["Nuplane"]["Setup"]["Feeds"][0]["IncludePatterns"] != ["Orbyss.*"]:
        raise AssertionError("Runnable package discovery must be constrained to Orbyss building blocks.")
    for value in (dockerfile, release):
        if "ORBYSS_FOUNDATION_HOST_IMAGE" not in value or "PROGRAMKIT_HOST_IMAGE" in value:
            raise AssertionError("Runnable releases must consume the independently published Foundation host.")

    tracked_runtime = subprocess.run(
        ["git", "ls-files", "src", "tests/dotnet", "ProgramKit.slnx"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if tracked_runtime:
        raise AssertionError("Program Kit regained ownership of component runtime source or implementation probes.")
    forbidden_workflows = {
        "dotnet-ci.yml", "frontend-ci.yml", "publish-nuget.yml", "publish-frontend.yml", "publish-host-image.yml"
    }
    present = {path.name for path in (ROOT / ".github/workflows").glob("*.yml")}
    if present & forbidden_workflows:
        raise AssertionError(f"Program Kit regained component publication workflows: {sorted(present & forbidden_workflows)}")

    knowledge = (REFERENCE.with_suffix(".md")).read_text(encoding="utf-8")
    for required in (
        "software factory and AI consultancy",
        "independently versioned",
        "consumer owns",
        "choose-one",
        "MCP transport",
    ):
        if required not in knowledge:
            raise AssertionError(f"Building-block knowledge lost required guidance: {required}")

    capability_index = json.loads(
        (ROOT / "extensions/program-kit-governance/references/capability-index.json").read_text(encoding="utf-8")
    )
    routed = {
        item["id"]: item["reference"]
        for item in capability_index["capabilities"]
        if item["id"] in {
            "dotnet-host-runtime", "authenticated-browser-bff", "browser-spa-pkce", "forms",
            "localization", "domain-events", "openapi-contracts"
        }
    }
    if set(routed.values()) != {"references/orbyss-building-blocks.md"} or len(routed) != 7:
        raise AssertionError("Intake no longer routes relevant capabilities to building-block knowledge.")

    print("Program Kit executable building-block inventory, selected-only pin boundary, and repository split passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
