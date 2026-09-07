from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "extensions/program-kit-dotnet/references/orbyss-building-blocks.json"


def package_versions(path: Path) -> dict[str, str]:
    tree = ElementTree.parse(path)
    return {
        item.attrib["Include"]: item.attrib["Version"]
        for item in tree.iter()
        if item.tag.endswith("PackageVersion")
    }


def main() -> int:
    manifest = json.loads(REFERENCE.read_text(encoding="utf-8"))
    foundation = manifest["families"]["foundation"]
    forms = manifest["families"]["forms"]

    if foundation["repository"] != "https://github.com/orbyss-io/dotnet-foundation":
        raise AssertionError("Foundation repository identity drifted.")
    if forms["repository"] != "https://github.com/orbyss-io/forms":
        raise AssertionError("Forms repository identity drifted.")
    for family in (foundation, forms):
        if not re.fullmatch(r"\d+\.\d+\.\d+", family["version"]):
            raise AssertionError("Building-block family versions must be exact stable SemVer pins.")

    foundation_packages = set(foundation["packages"])
    forms_packages = set(forms["nuget_packages"])
    npm_packages = set(forms["npm_packages"])
    if len(foundation_packages) != 22 or not all(item.startswith("Orbyss.Foundation.") for item in foundation_packages):
        raise AssertionError("Foundation must expose the exact 22-package Orbyss.Foundation family.")
    if len(forms_packages) != 27 or not all(item.startswith(("Orbyss.Forms.", "Orbyss.Localization.")) for item in forms_packages):
        raise AssertionError("Forms must expose the exact 27-package Forms/Localization NuGet family.")
    if len(npm_packages) != 12 or not all(item.startswith("@orbyss-io/forms-") for item in npm_packages):
        raise AssertionError("Forms must expose the exact 12-package npm family.")
    if set(foundation["package_roles"]) != foundation_packages:
        raise AssertionError("Every Foundation package must have selection knowledge.")
    if set(forms["nuget_package_roles"]) != forms_packages:
        raise AssertionError("Every Forms/Localization NuGet package must have selection knowledge.")
    if set(forms["npm_package_roles"]) != npm_packages:
        raise AssertionError("Every Forms frontend package must have selection knowledge.")

    known = foundation_packages | forms_packages | npm_packages
    for name, composition in manifest["compositions"].items():
        selected: list[str] = []
        for field in ("required", "optional", "optional_mcp", "choose_one_renderer", "choose_one_storage"):
            selected.extend(composition.get(field, []))
        unknown = set(selected) - known
        if unknown:
            raise AssertionError(f"{name} selects unknown building blocks: {sorted(unknown)}")
    selected_by_compositions = {
        package
        for composition in manifest["compositions"].values()
        for field in ("required", "optional", "optional_mcp", "choose_one_renderer", "choose_one_storage")
        for package in composition.get(field, [])
    }
    if selected_by_compositions != known:
        raise AssertionError(f"Composition knowledge does not cover every building block: {sorted(known - selected_by_compositions)}")

    pins = package_versions(
        ROOT / "extensions/program-kit-dotnet/templates/dotnet/files/.program-kit/eng/ProgramKit.Packages.props"
    )
    expected_pins = {
        **{item: foundation["version"] for item in foundation_packages},
        **{item: forms["version"] for item in forms_packages},
    }
    actual_orbyss = {key: value for key, value in pins.items() if key.startswith("Orbyss.")}
    if actual_orbyss != expected_pins:
        raise AssertionError("The generated .NET baseline does not exactly mirror the independently pinned manifest.")
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
    patterns = host["Nuplane"]["Setup"]["Feeds"][0]["IncludePatterns"]
    if patterns != ["Orbyss.*"]:
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
        "dotnet-ci.yml",
        "frontend-ci.yml",
        "publish-nuget.yml",
        "publish-frontend.yml",
        "publish-host-image.yml",
    }
    present = {path.name for path in (ROOT / ".github/workflows").glob("*.yml")}
    if present & forbidden_workflows:
        raise AssertionError(f"Program Kit regained component publication workflows: {sorted(present & forbidden_workflows)}")

    knowledge = (REFERENCE.with_suffix(".md")).read_text(encoding="utf-8")
    for required in (
        "software factory and AI consultancy",
        "independently versioned",
        "consumer owns",
        "Choose exactly one browser authentication profile",
        "Forms and localization MCP contributors require Foundation MCP transport",
    ):
        if required not in knowledge:
            raise AssertionError(f"Building-block knowledge lost required guidance: {required}")

    capability_index = json.loads(
        (ROOT / "extensions/program-kit-governance/references/capability-index.json").read_text(encoding="utf-8")
    )
    routed = {
        item["id"]: item["reference"]
        for item in capability_index["capabilities"]
        if item["id"] in {"dotnet-host-runtime", "authenticated-browser-bff", "browser-spa-pkce", "forms", "localization", "domain-events", "openapi-contracts"}
    }
    if set(routed.values()) != {"references/orbyss-building-blocks.md"} or len(routed) != 7:
        raise AssertionError("Intake no longer routes all relevant capabilities to Orbyss building-block knowledge.")

    print("Program Kit building-block inventory, composition knowledge, pins, and repository boundary passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
