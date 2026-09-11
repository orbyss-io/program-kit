from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .common import LiveContractError, load_object


def _resolved_packages(lock: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for target in lock.get("targets", []):
        for package in target.get("packages", []):
            result.add(f"{package['ecosystem']}:{package['packageId']}@{package['version']}")
    return result


def validate_consumer(project: Path, expectation: dict[str, Any]) -> dict[str, object]:
    selection = load_object(project / "docs/architecture/building-block-selection.json")
    lock = load_object(project / ".program-kit/building-blocks.lock.json")
    actual_compositions = {item["composition"] for item in selection.get("instances", [])}
    expected_compositions = set(expectation["compositions"])
    if actual_compositions != expected_compositions:
        raise LiveContractError(f"LIVE_VALIDATION_COMPOSITION_MISMATCH: {sorted(actual_compositions)}")
    actual_packages = _resolved_packages(lock)
    expected_packages = set(expectation["packages"])
    if actual_packages != expected_packages:
        raise LiveContractError(
            f"LIVE_VALIDATION_PACKAGE_MISMATCH: missing={sorted(expected_packages - actual_packages)} extra={sorted(actual_packages - expected_packages)}"
        )
    actual_targets = {item["path"] for item in selection.get("targets", [])}
    if actual_targets != set(expectation["targets"]):
        raise LiveContractError("LIVE_VALIDATION_TARGET_MISMATCH")
    central = (project / "Directory.Packages.props").read_text(encoding="utf-8")
    api_project = (project / "src/InternalForms.Api/InternalForms.Api.csproj").read_text(encoding="utf-8")
    if not re.search(r'<PackageVersion\s+Include="Microsoft\.OpenApi"\s+Version="2\.7\.5"\s*/>', central):
        raise LiveContractError("LIVE_VALIDATION_CONSUMER_NUGET_PIN_LOST")
    if not re.search(r'<PackageReference\s+Include="Microsoft\.OpenApi"\s*/>', api_project):
        raise LiveContractError("LIVE_VALIDATION_CONSUMER_NUGET_REFERENCE_LOST")
    package_json = load_object(project / "web/package.json")
    combined = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
    for entry in expectation["preservedDependencies"]:
        if not entry.startswith("npm:"):
            continue
        package_and_version = entry.removeprefix("npm:").rsplit("@", 1)
        if len(package_and_version) != 2 or combined.get(package_and_version[0]) != package_and_version[1]:
            raise LiveContractError(f"LIVE_VALIDATION_CONSUMER_NPM_DEPENDENCY_LOST: {entry}")
    overlay = load_object(project / ".program-kit/building-blocks.shells.json")
    shells = overlay.get("CShells", {}).get("Shells", {})
    activation_count = sum(len(value.get("Features", {})) for value in shells.values() if isinstance(value, dict))
    if activation_count < expectation["minimumActivations"]:
        raise LiveContractError(f"LIVE_VALIDATION_ACTIVATION_COUNT: {activation_count}")
    configuration = load_object(project / ".program-kit/building-blocks.configuration.json")
    requirements = configuration.get("requirements", [])
    paths = {item.get("path") for item in requirements if isinstance(item, dict)}
    if paths != set(expectation["configurationKnowledge"]):
        raise LiveContractError(f"LIVE_VALIDATION_CONFIGURATION_KNOWLEDGE_MISMATCH: {sorted(paths)}")
    if any("value" in item for item in requirements if isinstance(item, dict)):
        raise LiveContractError("LIVE_VALIDATION_CONFIGURATION_VALUE_PRESENT")
    hosts = load_object(project / ".program-kit/building-blocks.hosts.json").get("hosts", [])
    if len(hosts) != 1 or hosts[0].get("reference") != "ghcr.io/orbyss-io/foundation-host:v0.1.0":
        raise LiveContractError("LIVE_VALIDATION_HOST_REFERENCE_MISMATCH")
    return {
        "compositionCount": len(actual_compositions),
        "packageCount": len(actual_packages),
        "activationCount": activation_count,
        "configurationRequirementCount": len(requirements),
        "consumerDependenciesPreserved": True,
    }
