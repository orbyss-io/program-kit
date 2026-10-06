from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


SCHEMA_VERSION = "1.0"
RESOLVER_CONTRACT_VERSION = "1"
ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
BEGIN_MARKER = "<!-- Program Kit building-block references: begin -->"
END_MARKER = "<!-- Program Kit building-block references: end -->"
NPMRC_BEGIN = "# Program Kit building-block registry routing: begin"
NPMRC_END = "# Program Kit building-block registry routing: end"


@dataclass
class ResolverError(ValueError):
    code: str
    detail: str

    def __str__(self) -> str:
        return f"{self.code} {self.detail}"


def fail(code: str, detail: str) -> None:
    raise ResolverError(code, detail)


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        fail("PKB100", f"cannot load JSON from {path}: {error}")
    if not isinstance(value, dict):
        fail("PKB101", f"{path} must contain a JSON object")
    return value


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pretty_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def require_id(value: object, label: str) -> str:
    if not isinstance(value, str) or not ID.fullmatch(value):
        fail("PKB102", f"{label} must match {ID.pattern}")
    return value


def require_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        fail("PKB102", f"{label} must be a lowercase SHA-256")
    return value


def require_list(value: object, label: str) -> list:
    if not isinstance(value, list):
        fail("PKB102", f"{label} must be an array")
    return value


def require_object(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        fail("PKB102", f"{label} must be an object")
    return value


def unique(values: list[str], label: str) -> list[str]:
    if len(set(values)) != len(values):
        fail("PKB103", f"{label} contains duplicate values")
    return values


def normalize_path(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        fail("PKB300", f"{label} must be a non-empty forward-slash repository-relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or ":" in value or ".." in path.parts or path.parts in ((), (".",)):
        fail("PKB300", f"{label} must stay inside the repository: {value!r}")
    normalized = path.as_posix()
    if any(part.endswith((".", " ")) or any(char in part for char in '<>"|?*')
           or re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part)
           for part in path.parts):
        fail("PKB300", f"{label} contains an unsafe cross-platform path segment")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def repository_path(repository: Path, relative: str) -> Path:
    root = repository.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        fail("PKB300", f"managed path escapes the repository: {relative!r}")
    return candidate


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".program-kit.tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)


def resolution_projection(catalog: dict) -> dict:
    packages: dict[str, dict] = {}
    for key, package in sorted(require_object(catalog.get("packages"), "catalog.packages").items()):
        packages[key] = {
            field: copy.deepcopy(package[field])
            for field in (
                "packageId",
                "family",
                "ecosystem",
                "version",
                "source",
                "materialization",
                "requires",
                "activations",
                "supportsBuildTime",
                "configuration",
            )
            if field in package
        }
    compositions: dict[str, dict] = {}
    for key, composition in sorted(require_object(catalog.get("compositions"), "catalog.compositions").items()):
        compositions[key] = {
            field: copy.deepcopy(composition[field])
            for field in (
                "scopeKind",
                "targetSlots",
                "buildTimeSlots",
                "requirements",
                "optionGroups",
                "conflicts",
                "configuration",
            )
            if field in composition
        }
    return {
        "schemaVersion": catalog.get("schemaVersion"),
        "catalogId": catalog.get("catalogId"),
        "resolutionRevision": catalog.get("resolutionRevision"),
        "sources": copy.deepcopy(catalog.get("sources")),
        "families": {
            key: {"releaseVersion": family.get("releaseVersion"),
                  **({"toolVersions": copy.deepcopy(family["toolVersions"])} if "toolVersions" in family else {})}
            for key, family in sorted(require_object(catalog.get("families"), "catalog.families").items())
        },
        "packages": packages,
        "capabilities": copy.deepcopy(catalog.get("capabilities")),
        "compositions": compositions,
    }


def catalog_resolution_sha256(catalog: dict) -> str:
    return canonical_sha256(resolution_projection(catalog))


def composition_projection(catalog: dict) -> dict:
    value = resolution_projection(catalog)
    value.pop('resolutionRevision')
    for family in value['families'].values():
        family.pop('releaseVersion', None)
        family.pop('toolVersions', None)
    for package in value['packages'].values(): package.pop('version')
    return value


def dependency_profile_value(catalog: dict, identity: str) -> dict:
    validate_catalog(catalog)
    return {'schemaVersion': 1, 'id': identity,
            'compositionSha256': canonical_sha256(composition_projection(catalog)),
            'catalogResolutionSha256': catalog_resolution_sha256(catalog),
            'resolutionRevision': catalog['resolutionRevision'],
            'families': copy.deepcopy(resolution_projection(catalog)['families']),
            'artifacts': {key: item['version'] for key, item in sorted(catalog['packages'].items())}}


def validate_catalog(catalog: dict) -> None:
    if catalog.get("schemaVersion") != SCHEMA_VERSION:
        fail("PKB104", f"unsupported catalog schemaVersion {catalog.get('schemaVersion')!r}")
    if catalog.get("catalogId") != "orbyss-building-blocks":
        fail("PKB104", f"unsupported catalogId {catalog.get('catalogId')!r}")
    if not isinstance(catalog.get("resolutionRevision"), int) or catalog["resolutionRevision"] < 1:
        fail("PKB102", "catalog.resolutionRevision must be a positive integer")
    sources = require_object(catalog.get("sources"), "catalog.sources")
    families = require_object(catalog.get("families"), "catalog.families")
    packages = require_object(catalog.get("packages"), "catalog.packages")
    compositions = require_object(catalog.get("compositions"), "catalog.compositions")
    if not sources or not families or not packages or not compositions:
        fail("PKB102", "catalog sources, families, packages, and compositions must be non-empty")
    package_ids: dict[tuple[str, str], str] = {}
    feature_owners: dict[str, str] = {}
    for family_id, family in families.items():
        for tool_id, pin in require_object(family.get("toolVersions", {}), f"family {family_id} toolVersions").items():
            tool = next((p for p in packages.values() if p.get('packageId') == tool_id), {})
            if (tool.get("family") != family_id or tool.get("materialization", {}).get("kind") not in {"dotnet-tool", "nuget-global-analyzer", "host-image"}
                    or not isinstance(pin, str) or not re.fullmatch(r"\d+\.\d+\.\d+", pin)):
                fail("PKB105", f"family {family_id} toolVersions must name exact stable registered tools, analyzers or host images: {tool_id!r}")
    for key, package_value in sorted(packages.items()):
        package = require_object(package_value, f"catalog.packages[{key!r}]")
        ecosystem = require_id(package.get("ecosystem"), f"catalog.packages[{key!r}].ecosystem")
        package_id = package.get("packageId")
        if not isinstance(package_id, str) or not package_id:
            fail("PKB102", f"catalog package {key!r} has no packageId")
        if key != f"{ecosystem}:{package_id}":
            fail("PKB105", f"catalog package key {key!r} must equal {ecosystem}:{package_id}")
        identity = (ecosystem, package_id.casefold() if ecosystem == "nuget" else package_id)
        if identity in package_ids:
            fail("PKB105", f"catalog duplicates package identity {package_id!r}")
        package_ids[identity] = key
        if package.get("family") not in families:
            fail("PKB105", f"catalog package {key!r} names unknown family {package.get('family')!r}")
        if package.get("source") not in sources:
            fail("PKB105", f"catalog package {key!r} names unknown source {package.get('source')!r}")
        if sources[package["source"]].get("ecosystem") != ecosystem:
            fail("PKB105", f"catalog package {key!r} ecosystem differs from source {package['source']!r}")
        version = package.get("version")
        family_version = families[package["family"]].get("releaseVersion")
        if package.get("materialization", {}).get("kind") in {"dotnet-tool", "nuget-global-analyzer", "host-image"}:
            family_version = families[package["family"]].get("toolVersions", {}).get(package_id, family_version)
        if not isinstance(version, str) or version != family_version:
            fail("PKB105", f"catalog package {key!r} must exactly match family release {family_version!r}")
        materialization = require_object(package.get("materialization"), f"catalog package {key!r} materialization")
        require_id(materialization.get("kind"), f"catalog package {key!r} materialization kind")
        require_list(materialization.get("allowedTargetKinds"), f"catalog package {key!r} allowedTargetKinds")
        require_list(materialization.get("allowedRoles"), f"catalog package {key!r} allowedRoles")
        if materialization.get("kind") == "dotnet-tool":
            commands = require_list(materialization.get("commands"), f"catalog package {key!r} commands")
            if not commands or any(not isinstance(command, str) or not command for command in commands):
                fail("PKB102", f"catalog dotnet tool {key!r} must declare non-empty commands")
        if materialization.get("kind") == "host-image" and "{version}" not in str(materialization.get("tagTemplate", "")):
            fail("PKB102", f"catalog host image {key!r} must declare a version tag template")
        require_list(package.get("requires"), f"catalog package {key!r} requires")
        activations = require_list(package.get("activations", []), f"catalog package {key!r} activations")
        activation_identities: list[tuple[str, str]] = []
        for activation_value in activations:
            activation = require_object(activation_value, f"catalog package {key!r} activation")
            identity = activation.get("featureIdentity")
            if not isinstance(identity, str) or not identity.strip():
                fail("PKB102", f"catalog package {key!r} activation featureIdentity must be non-empty")
            slot = require_id(activation.get("targetSlot"), f"catalog package {key!r} activation targetSlot")
            activation_identities.append((slot, identity))
            owner = feature_owners.get(identity)
            if owner and owner != key:
                fail("PKB105", f"catalog shell feature {identity!r} is contributed by both {owner} and {key}")
            feature_owners[identity] = key
        unique(activation_identities, f"catalog package {key!r} activations")
        require_list(package.get("configuration"), f"catalog package {key!r} configuration")
    for key, package_value in sorted(packages.items()):
        for requirement in package_value["requires"]:
            required = require_object(requirement, f"catalog package {key!r} requirement")
            if required.get("package") not in packages:
                fail("PKB105", f"catalog package {key!r} requires unknown package {required.get('package')!r}")
            require_id(required.get("targetSlot"), f"catalog package {key!r} companion targetSlot")
    for composition_id, composition_value in sorted(compositions.items()):
        require_id(composition_id, "catalog composition ID")
        composition = require_object(composition_value, f"catalog composition {composition_id}")
        slots = require_object(composition.get("targetSlots"), f"catalog composition {composition_id} targetSlots")
        for slot_id, slot in slots.items():
            require_id(slot_id, f"catalog composition {composition_id} target slot")
            slot = require_object(slot, f"catalog composition {composition_id} target slot {slot_id}")
            require_id(slot.get("kind"), f"catalog composition {composition_id} target slot {slot_id} kind")
            roles = require_list(slot.get("allowedRoles"), f"catalog composition {composition_id} target slot {slot_id} roles")
            if not roles:
                fail("PKB106", f"catalog composition {composition_id} target slot {slot_id} has no allowed roles")
        validate_requirements(catalog, composition_id, composition.get("requirements"), slots)
        group_ids: list[str] = []
        for group_value in require_list(composition.get("optionGroups"), f"catalog composition {composition_id} optionGroups"):
            group = require_object(group_value, f"catalog composition {composition_id} option group")
            group_id = require_id(group.get("id"), f"catalog composition {composition_id} option group ID")
            group_ids.append(group_id)
            minimum = group.get("minimum")
            maximum = group.get("maximum")
            options = require_object(group.get("options"), f"catalog composition {composition_id} option group {group_id} options")
            if not isinstance(minimum, int) or minimum < 0 or not isinstance(maximum, int) or maximum < 1 or minimum > maximum or maximum > len(options):
                fail("PKB106", f"catalog composition {composition_id} option group {group_id} has invalid cardinality")
            for option_id, option_value in options.items():
                require_id(option_id, f"catalog composition {composition_id} option ID")
                option = require_object(option_value, f"catalog composition {composition_id} option {option_id}")
                validate_requirements(catalog, composition_id, option.get("requirements"), slots)
        unique(group_ids, f"catalog composition {composition_id} option group IDs")
        for conflict_value in require_list(composition.get("conflicts"), f"catalog composition {composition_id} conflicts"):
            conflict = require_object(conflict_value, f"catalog composition {composition_id} conflict")
            if conflict.get("composition") not in compositions:
                fail("PKB105", f"catalog composition {composition_id} conflicts with unknown composition {conflict.get('composition')!r}")


def validate_requirements(catalog: dict, composition_id: str, value: object, slots: dict) -> None:
    for requirement_value in require_list(value, f"catalog composition {composition_id} requirements"):
        requirement = require_object(requirement_value, f"catalog composition {composition_id} requirement")
        if requirement.get("package") not in catalog["packages"]:
            fail("PKB105", f"catalog composition {composition_id} requires unknown package {requirement.get('package')!r}")
        if requirement.get("targetSlot") not in slots:
            fail("PKB105", f"catalog composition {composition_id} uses unknown target slot {requirement.get('targetSlot')!r}")
        package = catalog["packages"][requirement["package"]]
        materialization = package["materialization"]
        slot = slots[requirement["targetSlot"]]
        if slot["kind"] not in materialization["allowedTargetKinds"]:
            fail("PKB106", f"catalog composition {composition_id} cannot place {requirement['package']} in slot {requirement['targetSlot']}")
        if not set(slot["allowedRoles"]) & set(materialization["allowedRoles"]):
            fail("PKB106", f"catalog composition {composition_id} slot {requirement['targetSlot']} has no valid role for {requirement['package']}")
        build_slots = catalog['compositions'][composition_id].get('buildTimeSlots', [])
        if not isinstance(build_slots, list) or any(s not in slots or slots[s]['kind'] != 'dotnet-project' for s in build_slots):
            fail('PKB106', 'Build-time slots must be declared .NET producer projects')
        if requirement['targetSlot'] in build_slots:
            if package.get('supportsBuildTime') is not True:
                fail('PKB106', f"{requirement['package']} does not declare supported public build-time use")
        else:
            validate_activation_slots(catalog, composition_id, requirement["package"], slots, set())


def validate_activation_slots(catalog: dict, composition_id: str, package_key: str, slots: dict, seen: set[str]) -> None:
    if package_key in seen:
        return
    seen.add(package_key)
    package = catalog["packages"][package_key]
    for activation in package.get("activations", []):
        slot_id = activation["targetSlot"]
        slot = slots.get(slot_id)
        if not slot or slot.get("kind") != "cshell-shell" or "composition" not in slot.get("allowedRoles", []):
            fail("PKB106", f"catalog composition {composition_id} must provide a composition CShell slot {slot_id!r} for {package_key}")
    for companion in package["requires"]:
        validate_activation_slots(catalog, composition_id, companion["package"], slots, seen)


def validate_selection(selection: dict, required_status: str = "Accepted") -> None:
    if selection.get("schemaVersion") != SCHEMA_VERSION:
        fail("PKB104", f"unsupported selection schemaVersion {selection.get('schemaVersion')!r}")
    require_id(selection.get("selectionId"), "selection.selectionId")
    if not isinstance(selection.get("revision"), int) or selection["revision"] < 1:
        fail("PKB102", "selection.revision must be a positive integer")
    if selection.get("status") != required_status:
        fail("PKB110", f"selection status must be {required_status}, found {selection.get('status')!r}")
    require_object(selection.get("catalog"), "selection.catalog")
    authority = require_object(selection.get("authority"), "selection.authority")
    normalize_path(authority.get("architectureMap"), "selection.authority.architectureMap")
    decision_ids = [require_id(value, "selection authority decision ID") for value in require_list(authority.get("decisionIds"), "selection.authority.decisionIds")]
    unique(decision_ids, "selection.authority.decisionIds")
    if not isinstance(authority.get("rationale"), str) or not authority["rationale"].strip():
        fail("PKB102", "selection.authority.rationale must be non-empty")


def verify_catalog_binding(selection: dict, catalog: dict) -> str:
    binding = selection["catalog"]
    expected = catalog_resolution_sha256(catalog)
    if binding.get("id") != catalog.get("catalogId") or binding.get("schemaVersion") != catalog.get("schemaVersion"):
        fail("PKB111", "selection catalog identity or schema does not match the installed catalog")
    if binding.get("resolutionRevision") != catalog.get("resolutionRevision"):
        fail("PKB111", "selection catalog resolutionRevision does not match the installed catalog")
    require_sha(binding.get("resolutionSha256"), "selection.catalog.resolutionSha256")
    if binding["resolutionSha256"] != expected:
        fail("PKB111", "selection catalog resolution hash is stale; architecture acceptance must be renewed")
    accepted = require_object(binding.get("familyReleases"), "selection.catalog.familyReleases")
    actual = {key: value.get("releaseVersion") for key, value in sorted(catalog["families"].items())}
    if accepted != actual:
        fail("PKB111", f"selection family releases differ from the catalog: expected {actual}, found {accepted}")
    return expected


def verify_architecture_authority(repository: Path, selection_path: Path, selection: dict) -> tuple[str, str]:
    try:
        relative_selection = selection_path.resolve().relative_to(repository.resolve()).as_posix()
    except ValueError:
        fail("PKB300", f"selection path escapes the repository: {selection_path}")
    map_relative = normalize_path(selection["authority"]["architectureMap"], "selection.authority.architectureMap")
    architecture_path = repository / map_relative
    architecture = load_json(architecture_path)
    selection_raw = raw_sha256(selection_path)
    matching = [
        item
        for item in require_list(architecture.get("documentation"), "architecture-map.documentation")
        if isinstance(item, dict) and item.get("path") == relative_selection
    ]
    if len(matching) != 1:
        fail("PKB112", f"architecture map must register exactly one documentation entry for {relative_selection}")
    registration = matching[0]
    registered = registration.get("canonicalSha256", registration.get("sha256"))
    expected = canonical_sha256(selection) if "canonicalSha256" in registration else selection_raw
    if registered != expected:
        fail("PKB112", f"architecture registration for {relative_selection} is stale")
    decisions = {
        item.get("id"): item
        for item in require_list(architecture.get("decisions"), "architecture-map.decisions")
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    selected_decisions = []
    for decision_id in selection["authority"]["decisionIds"]:
        decision = decisions.get(decision_id)
        if decision is None:
            fail("PKB113", f"selection cites unknown architecture decision {decision_id!r}")
        if decision.get("status") != "Accepted":
            fail("PKB113", f"selection decision {decision_id!r} is not Accepted")
        selected_decisions.append(decision)
    authority_projection = {
        "registration": registration,
        "decisions": sorted(selected_decisions, key=lambda item: item["id"]),
    }
    return map_relative, canonical_sha256(authority_projection)


def index_selection(selection: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    scopes: dict[str, dict] = {}
    for item in require_list(selection.get("scopes"), "selection.scopes"):
        scope = require_object(item, "selection scope")
        scope_id = require_id(scope.get("id"), "selection scope ID")
        if scope_id in scopes:
            fail("PKB103", f"duplicate selection scope {scope_id!r}")
        if scope.get("kind") not in {"repository", "application", "browser-boundary", "shell", "storage-contract", "tooling"}:
            fail("PKB102", f"selection scope {scope_id!r} has invalid kind {scope.get('kind')!r}")
        if scope.get("environment") not in {"development", "test", "production"}:
            fail("PKB102", f"selection scope {scope_id!r} has invalid environment {scope.get('environment')!r}")
        scopes[scope_id] = scope
    for scope_id, scope in scopes.items():
        parent = scope.get("parent")
        if parent is not None and parent not in scopes:
            fail("PKB200", f"selection scope {scope_id!r} names unknown parent {parent!r}")
        current = parent
        seen = {scope_id}
        while current is not None:
            if current in seen:
                fail("PKB200", f"selection scope ancestry contains a cycle at {current!r}")
            seen.add(current)
            current = scopes[current].get("parent")
    targets: dict[str, dict] = {}
    path_identities: dict[str, str] = {}
    for item in require_list(selection.get("targets"), "selection.targets"):
        target = copy.deepcopy(require_object(item, "selection target"))
        target_id = require_id(target.get("id"), "selection target ID")
        if target_id in targets:
            fail("PKB103", f"duplicate selection target {target_id!r}")
        if target.get("scope") not in scopes:
            fail("PKB300", f"selection target {target_id!r} names unknown scope {target.get('scope')!r}")
        target["path"] = normalize_path(target.get("path"), f"selection target {target_id} path")
        identity = target["path"].casefold()
        if identity in path_identities and path_identities[identity] != target_id:
            fail("PKB301", f"selection targets {path_identities[identity]!r} and {target_id!r} have colliding paths")
        if any(identity.startswith(previous + "/") or previous.startswith(identity + "/")
               for previous in path_identities):
            fail("PKB301", f"selection target {target_id!r} collides with another target's parent path")
        path_identities[identity] = target_id
        targets[target_id] = target
    return scopes, targets


def placement_kind_contracts() -> dict:
    schema = load_json(Path(__file__).resolve().parents[1] / 'references/building-block-selection.schema.json')
    return {rule['properties']['kind']['const']: rule for rule in schema['$defs']['targetKindPlacement']['oneOf']}


def validate_placements(repository: Path, selection: dict, require_all: bool = False) -> None:
    """Validate architecture declarations without creating their consumer-owned files.

    Legacy accepted selections remain readable. New bootstrap Drafts require provenance on
    every target; a declaration stays 'planned' after scaffolding as its decision-time origin.
    The map's source hashes provide freshness without duplicating ADR hashes across approval.
    """
    _, targets = index_selection(selection)
    for target in targets.values():
        if target.get("kind") == "host-image" and Path(target.get("path", "")).name != "hostsettings.json":
            fail("PKB303", "host-image must bind hostsettings.json to the published Foundation image; review legacy Dockerfile/DLL placement before synchronization. Approved selection is not rewritten automatically.")
    declared = [target for target in targets.values() if "placement" in target]
    if require_all and (not targets or len(declared) != len(targets)):
        fail("PKB306", "architecture must declare placement provenance for every target")
    if require_all and not selection.get("instances"):
        fail("PKB306", "architecture must declare composition instances and their bindings")
    if not declared:
        return
    kind_contracts = placement_kind_contracts()
    architecture = load_json(repository_path(repository, normalize_path(
        selection["authority"]["architectureMap"], "architecture map")))
    owners = {item["id"]: item for item in architecture.get("elements", [])}
    decisions = {item["id"]: item for item in architecture.get("decisions", [])}
    for target in declared:
        label = f"placement for {target['id']}"
        placement = require_object(target["placement"], label)
        if placement.get("state") not in {"observed", "planned"}:
            fail("PKB306", f"{label} must distinguish observed from planned")
        if not isinstance(placement.get("rationale"), str) or not placement["rationale"].strip():
            fail("PKB306", f"{label} needs architecture placement rationale")
        owner = owners.get(require_id(placement.get("owner"), f"{label} owner"))
        if not owner or not owner.get("ownership"):
            fail("PKB306", f"{label} needs a canonical semantic owner with ownership")
        refs = require_list(placement.get("decisionIds"), f"{label} decisionIds")
        if not refs or any(not isinstance(ref, str) for ref in refs) or len(set(refs)) != len(refs):
            fail("PKB306", f"{label} needs unique decision provenance")
        for ref in refs:
            decision = decisions.get(ref)
            if (ref not in selection["authority"]["decisionIds"]
                    or ref not in owner.get("decision_refs", []) or not decision
                    or decision.get("status") not in {"Proposed", "Accepted"}):
                fail("PKB306", f"{label} cites absent or inactive owner decision {ref!r}")
            source = repository_path(repository, normalize_path(decision.get("path"), label))
            if not source.is_file() or raw_sha256(source) != decision.get("sha256"):
                fail("PKB306", f"{label} has stale decision provenance {ref!r}")
        path = repository_path(repository, target["path"])
        current = repository.resolve()
        for segment in PurePosixPath(target["path"]).parts:
            if current.is_dir():
                matches = [entry.name for entry in current.iterdir() if entry.name.casefold() == segment.casefold()]
                if matches and matches != [segment]:
                    fail("PKB301", f"{label} changes an observed path's case identity")
            elif current.exists():
                fail("PKB300", f"{label} has a file as a parent directory")
            current = current / segment
        if any(part.casefold() in {".specify", ".program-kit", ".git", "node_modules"}
               for part in PurePosixPath(target["path"]).parts):
            fail("PKB300", f"{label} must name consumer content, not installed/internal files")
        if path.exists() and not path.is_file():
            fail("PKB300", f"{label} must name a file")
        if placement["state"] == "observed" and not path.is_file():
            fail("PKB306", f"{label} claims an observed file that is absent")
        if require_all and placement["state"] == "planned" and path.is_file():
            fail("PKB306", f"{label} must preserve the already observed file's identity and ownership")
        rule = kind_contracts.get(target.get('kind'))
        if rule is None:
            fail('PKB303', f"{label} has no supported target-kind contract")
        if not re.search(rule['properties']['path']['pattern'], target['path']):
            fail('PKB303', f"{label} path {target['path']!r} does not match {target['kind']!r}: {rule['description']}")
        for field in rule['required']:
            if field not in {'kind', 'path'}:
                require_id(target.get(field), f"{label} {field}: {rule['properties'][field]['description']}")


def binding_targets(instance: dict, slot: str, targets: dict[str, dict]) -> list[dict]:
    value = require_object(instance.get("targetBindings"), f"selection instance {instance['id']} targetBindings").get(slot)
    if value is None:
        fail("PKB302", f"selection instance {instance['id']!r} must bind target slot {slot!r}")
    ids = value if isinstance(value, list) else [value]
    result: list[dict] = []
    for target_id in ids:
        if not isinstance(target_id, str) or target_id not in targets:
            fail("PKB302", f"selection instance {instance['id']!r} binds {slot!r} to unknown target {target_id!r}")
        result.append(targets[target_id])
    return result


def scope_matches_kind(scope_id: str, kind: str, scopes: dict[str, dict]) -> str | None:
    current = scope_id
    seen: set[str] = set()
    while current and current not in seen:
        seen.add(current)
        scope = scopes[current]
        if scope["kind"] == kind:
            return current
        current = scope.get("parent")
    return None


def resolve(
    repository: Path,
    selection_path: Path,
    catalog_path: Path,
    program_kit_version: str,
    require_accepted: bool = True,
) -> dict:
    selection = load_json(selection_path)
    catalog_path = consumer_catalog(repository, selection, catalog_path)
    catalog = load_json(catalog_path)
    validate_catalog(catalog)
    validate_selection(selection, "Accepted" if require_accepted else "Draft")
    resolution_hash = verify_catalog_binding(selection, catalog)
    if require_accepted:
        architecture_path, authority_hash = verify_architecture_authority(repository, selection_path, selection)
    else:
        architecture_path = normalize_path(selection["authority"]["architectureMap"], "selection.authority.architectureMap")
        authority_hash = canonical_sha256(selection["authority"])
    scopes, targets = index_selection(selection)
    validate_placements(repository, selection)
    compositions = catalog["compositions"]
    packages = catalog["packages"]
    instances: dict[str, dict] = {}
    for item in require_list(selection.get("instances"), "selection.instances"):
        instance = copy.deepcopy(require_object(item, "selection instance"))
        instance_id = require_id(instance.get("id"), "selection instance ID")
        if instance_id in instances:
            fail("PKB103", f"duplicate selection instance {instance_id!r}")
        composition_id = instance.get("composition")
        if composition_id not in compositions:
            fail("PKB200", f"selection instance {instance_id!r} names unknown composition {composition_id!r}")
        if instance.get("scope") not in scopes:
            fail("PKB200", f"selection instance {instance_id!r} names unknown scope {instance.get('scope')!r}")
        required_scope = compositions[composition_id]["scopeKind"]
        if scope_matches_kind(instance["scope"], required_scope, scopes) is None:
            fail("PKB201", f"selection instance {instance_id!r} requires a {required_scope!r} scope")
        bindings = require_object(instance.get("targetBindings"), f"selection instance {instance_id} targetBindings")
        slots = compositions[composition_id]["targetSlots"]
        unknown_slots = sorted(set(bindings) - set(slots))
        if unknown_slots:
            fail("PKB302", f"selection instance {instance_id!r} binds unknown target slots {unknown_slots}")
        for slot_id, binding in bindings.items():
            target_ids = binding if isinstance(binding, list) else [binding]
            if not target_ids:
                fail("PKB302", f"selection instance {instance_id!r} binds target slot {slot_id!r} to no targets")
            for target_id in target_ids:
                if target_id not in targets:
                    fail("PKB302", f"selection instance {instance_id!r} binds {slot_id!r} to unknown target {target_id!r}")
                target = targets[target_id]
                slot = slots[slot_id]
                if target.get("kind") != slot["kind"] or target.get("role") not in slot["allowedRoles"]:
                    fail("PKB303", f"selection target {target_id!r} does not satisfy slot {composition_id}/{slot_id}")
                if "placement" in target and scope_matches_kind(target["scope"], required_scope, scopes) != scope_matches_kind(instance["scope"], required_scope, scopes):
                    fail("PKB303", f"selection target {target_id!r} crosses the instance's {required_scope} scope")
        instances[instance_id] = instance
    for first in instances.values():
        composition = compositions[first["composition"]]
        for conflict in composition["conflicts"]:
            first_scope = scope_matches_kind(first["scope"], conflict["scopeKind"], scopes)
            for second in instances.values():
                if second["id"] == first["id"] or second["composition"] != conflict["composition"]:
                    continue
                second_scope = scope_matches_kind(second["scope"], conflict["scopeKind"], scopes)
                if first_scope is not None and first_scope == second_scope:
                    fail("PKB202", f"selection instances {first['id']!r} and {second['id']!r} conflict in scope {first_scope!r}")

    assignments: dict[str, dict[str, dict]] = {target_id: {} for target_id in targets}
    activations: dict[tuple[str, str, str], dict] = {}
    resolved_instances: list[dict] = []
    configuration_requirements: list[dict] = []

    def assign(package_key: str, target: dict, origin: str, instance: dict, active: set[tuple[str, str, bool]], build_time: bool = False) -> None:
        package = packages[package_key]
        materialization = package["materialization"]
        if target.get("kind") not in materialization["allowedTargetKinds"]:
            fail("PKB303", f"{origin} cannot place {package_key} in target kind {target.get('kind')!r}")
        if target.get("role") not in materialization["allowedRoles"]:
            fail("PKB303", f"{origin} cannot place {package_key} in target role {target.get('role')!r}")
        environment = scopes[target["scope"]]["environment"]
        allowed_environments = materialization.get("allowedEnvironments")
        if allowed_environments and environment not in allowed_environments and not build_time:
            fail("PKB304", f"{origin} cannot place {package_key} in {environment!r} scope {target['scope']!r}")
        identity = (package_key, target["id"], build_time)
        if identity in active:
            assignments[target["id"]][package_key]["origins"].add(origin)
            return
        active.add(identity)
        existing = assignments[target["id"]].get(package_key)
        if existing is None:
            assignments[target["id"]][package_key] = {
                "packageKey": package_key,
                "packageId": package["packageId"],
                "family": package["family"],
                "ecosystem": package["ecosystem"],
                "version": package["version"],
                "source": package["source"],
                "materializationKind": materialization["kind"],
                "origins": {origin},
            }
            if materialization.get("commands"):
                assignments[target["id"]][package_key]["commands"] = sorted(materialization["commands"])
            if materialization["kind"] == "host-image":
                tag = materialization["tagTemplate"].replace("{version}", package["version"])
                assignments[target["id"]][package_key]["reference"] = f"{package['packageId']}:{tag}"
        else:
            existing["origins"].add(origin)
        for requirement in package["requires"]:
            if requirement["targetSlot"] == "same-target":
                companions = [target]
            else:
                companions = binding_targets(instance, requirement["targetSlot"], targets)
            for companion_target in companions:
                assign(requirement["package"], companion_target, f"{origin}/requires/{requirement['package']}", instance, active,
                       build_time if requirement['targetSlot'] == 'same-target' else
                       requirement['targetSlot'] in compositions[instance['composition']].get('buildTimeSlots', []))
        if build_time and package.get('supportsBuildTime') is not True:
            fail('PKB106', f'{package_key} is not a supported build-time dependency')
        for activation in ([] if build_time else package.get("activations", [])):
            for shell_target in binding_targets(instance, activation["targetSlot"], targets):
                key = (shell_target["id"], activation["featureIdentity"], package_key)
                activations[key] = {
                    "targetId": shell_target["id"],
                    "path": shell_target["path"],
                    "shell": shell_target.get("shell", "default"),
                    "featureIdentity": activation["featureIdentity"],
                    "packageKey": package_key,
                    "origin": origin,
                }

    for instance_id, instance in sorted(instances.items()):
        composition = compositions[instance["composition"]]
        selected_options = require_object(instance.get("options"), f"selection instance {instance_id} options")
        known_groups = {group["id"]: group for group in composition["optionGroups"]}
        unknown_groups = sorted(set(selected_options) - set(known_groups))
        if unknown_groups:
            fail("PKB203", f"selection instance {instance_id!r} selects unknown option groups {unknown_groups}")
        requirements = list(composition["requirements"])
        option_summary: dict[str, list[str]] = {}
        environment = scopes[instance["scope"]]["environment"]
        for group_id, group in sorted(known_groups.items()):
            choices = selected_options.get(group_id, [])
            if not isinstance(choices, list) or any(not isinstance(choice, str) for choice in choices):
                fail("PKB203", f"selection instance {instance_id!r} option group {group_id!r} must be an array of IDs")
            choices = unique(choices, f"selection instance {instance_id} option group {group_id}")
            if len(choices) < group["minimum"] or len(choices) > group["maximum"]:
                fail("PKB204", f"selection instance {instance_id!r} option group {group_id!r} requires {group['minimum']}..{group['maximum']} choices, found {len(choices)}")
            unknown = sorted(set(choices) - set(group["options"]))
            if unknown:
                fail("PKB203", f"selection instance {instance_id!r} option group {group_id!r} selects unknown options {unknown}")
            for choice in choices:
                option = group["options"][choice]
                allowed = option.get("allowedEnvironments")
                if allowed and environment not in allowed:
                    fail("PKB205", f"selection instance {instance_id!r} option {group_id}/{choice} is not allowed in {environment}")
                requirements.extend(option["requirements"])
            option_summary[group_id] = sorted(choices)
        active: set[tuple[str, str, bool]] = set()
        origin_packages: list[str] = []
        for requirement in requirements:
            origin = f"{instance_id}/{requirement['package']}"
            for target in binding_targets(instance, requirement["targetSlot"], targets):
                assign(requirement["package"], target, origin, instance, active,
                       requirement['targetSlot'] in composition.get('buildTimeSlots', []))
            origin_packages.append(requirement["package"])
        for config in composition["configuration"]:
            configuration_requirements.append({**copy.deepcopy(config), "origin": instance_id, "scope": instance["scope"]})
        resolved_instances.append(
            {
                "id": instance_id,
                "composition": instance["composition"],
                "scope": instance["scope"],
                "options": option_summary,
                "directRequirements": sorted(set(origin_packages)),
            }
        )

    locked_targets: list[dict] = []
    selected_sources: set[str] = set()
    for target_id, package_map in sorted(assignments.items(), key=lambda item: (targets[item[0]]["path"].casefold(), item[0])):
        if not package_map:
            continue
        target_packages = []
        for package_key, package in sorted(package_map.items(), key=lambda item: (item[1]["ecosystem"], item[1]["packageId"].casefold(), item[0])):
            package["origins"] = sorted(package["origins"])
            target_packages.append(package)
            selected_sources.add(package["source"])
            for config in packages[package_key]["configuration"]:
                configuration_requirements.append({**copy.deepcopy(config), "origin": package_key, "targetId": target_id})
        locked_targets.append(
            {
                "id": target_id,
                "kind": targets[target_id]["kind"],
                "path": targets[target_id]["path"],
                **({"lockRoot": targets[target_id]["lockRoot"]} if targets[target_id].get("lockRoot") else {}),
                "packages": target_packages,
            }
        )

    try:
        selection_relative = selection_path.resolve().relative_to(repository.resolve()).as_posix()
    except ValueError:
        fail("PKB300", f"selection path escapes the repository: {selection_path}")
    lock = {
        "schemaVersion": SCHEMA_VERSION,
        "producer": {
            "programKitVersion": program_kit_version,
            "resolverContractVersion": RESOLVER_CONTRACT_VERSION,
        },
        "inputs": {
            "selection": {
                "path": selection_relative,
                "revision": selection["revision"],
                "canonicalSha256": canonical_sha256(selection),
            },
            "catalog": {
                "id": catalog["catalogId"],
                "resolutionRevision": catalog["resolutionRevision"],
                "resolutionSha256": resolution_hash,
                "rawSha256": raw_sha256(catalog_path),
            },
            "architectureAuthority": {
                "path": architecture_path,
                "authoritySha256": authority_hash,
                "decisionIds": sorted(selection["authority"]["decisionIds"]),
            },
        },
        "instances": resolved_instances,
        "targets": locked_targets,
        "activations": [activations[key] for key in sorted(activations)],
        "registryRequirements": [
            {"sourceId": source_id, **copy.deepcopy(catalog["sources"][source_id])}
            for source_id in sorted(selected_sources)
        ],
        "configurationRequirements": sorted(
            configuration_requirements,
            key=lambda item: (str(item.get("scope", "")), str(item.get("targetId", "")), str(item.get("path", "")), str(item.get("origin", ""))),
        ),
        "managedOutputs": [],
    }
    verify_new_project_profile(repository, catalog, lock['activations'])
    lock["managedOutputs"] = managed_output_records(lock)
    lock["planDigest"] = canonical_sha256(lock)
    return lock


def output_record(kind: str, path: str, entries: list[dict], target_ids: list[str] | None = None) -> dict:
    record = {
        "kind": kind,
        "path": path,
        "entries": entries,
        "ownedSha256": canonical_sha256({"kind": kind, "entries": entries}),
    }
    if target_ids:
        record["targetIds"] = sorted(target_ids)
    return record


def materialized_plan(repository: Path, lock: dict) -> dict:
    """Project accepted choices onto complete, existing composition targets without scaffolding.

    Authority still comes from resolve(). A later composition cannot acquire package assignments
    or shared-shell activations merely because one of its other targets already exists.
    """
    selection = load_json(repository_path(repository, lock["inputs"]["selection"]["path"]))
    targets = {target["id"]: target for target in selection["targets"]}
    eligible: set[str] = set()
    deferred: list[str] = []
    for instance in selection["instances"]:
        bound = {target_id for binding in instance["targetBindings"].values()
                 for target_id in (binding if isinstance(binding, list) else [binding])}
        missing = [target_id for target_id in bound
                   if targets[target_id]["kind"] in {"dotnet-project", "npm-package", "dotnet-tool-manifest"}
                   and not repository_path(repository, targets[target_id]["path"]).is_file()]
        if missing:
            deferred.append(instance["id"])
        else:
            eligible.add(instance["id"])
    result = copy.deepcopy(lock)
    result.pop("planDigest", None)
    result["materializationScope"] = "existing-compositions"
    result["deferredInstances"] = sorted(deferred)
    result["instances"] = [instance for instance in result["instances"] if instance["id"] in eligible]
    selected_targets = []
    for target in result["targets"]:
        retained = []
        for package in target["packages"]:
            package["origins"] = [origin for origin in package["origins"] if origin.split("/", 1)[0] in eligible]
            if package["origins"]:
                retained.append(package)
        if retained:
            target["packages"] = retained
            selected_targets.append(target)
    result["targets"] = selected_targets
    target_packages = {target["id"]: {package["packageKey"] for package in target["packages"]} for target in selected_targets}
    source_ids = {package["source"] for target in selected_targets for package in target["packages"]}
    result["activations"] = [activation for activation in result["activations"] if activation["origin"].split("/", 1)[0] in eligible]
    result["configurationRequirements"] = [requirement for requirement in result["configurationRequirements"]
                                           if (requirement.get("origin") in target_packages.get(requirement.get("targetId"), set()) if "targetId" in requirement
                                               else requirement.get("origin") in eligible)]
    result["registryRequirements"] = [source for source in result["registryRequirements"] if source["sourceId"] in source_ids]
    result["managedOutputs"] = managed_output_records(result)
    result["planDigest"] = canonical_sha256(result)
    return result


def managed_output_records(lock: dict) -> list[dict]:
    outputs: list[dict] = []
    central: dict[str, dict] = {}
    npm_routing: dict[str, dict[str, dict]] = {}
    shell_activations: dict[str, list[dict]] = {}
    registry = {item["sourceId"]: item for item in lock["registryRequirements"]}
    host_entries: list[dict] = []
    for target in lock["targets"]:
        project_packages = [
            {"packageId": package["packageId"], "version": package["version"]}
            for package in target["packages"]
            if package["materializationKind"] == "nuget-project"
        ]
        if project_packages:
            project_packages.sort(key=lambda item: item["packageId"].casefold())
            outputs.append(output_record("nuget-project", target["path"], project_packages, [target["id"]]))
            for package in project_packages:
                existing = central.get(package["packageId"].casefold())
                if existing and existing != package:
                    fail("PKB306", f"NuGet package {package['packageId']} resolves to multiple exact versions")
                central[package["packageId"].casefold()] = package
        tools = [
            {
                "packageId": package["packageId"],
                "version": package["version"],
                "commands": package["commands"],
            }
            for package in target["packages"]
            if package["materializationKind"] == "dotnet-tool"
        ]
        if tools:
            tools.sort(key=lambda item: item["packageId"].casefold())
            outputs.append(output_record("dotnet-tool-manifest", target["path"], tools, [target["id"]]))
        npm_entries = [
            {
                "packageId": package["packageId"],
                "version": package["version"],
                "section": "devDependencies" if package["materializationKind"] == "npm-dev-dependency" else "dependencies",
                "source": package["source"],
            }
            for package in target["packages"]
            if package["materializationKind"] in {"npm-dependency", "npm-dev-dependency"}
        ]
        if npm_entries:
            npm_entries.sort(key=lambda item: (item["section"], item["packageId"]))
            outputs.append(output_record("npm-package", target["path"], npm_entries, [target["id"]]))
            npmrc_path = (PurePosixPath(target["path"]).parent / ".npmrc").as_posix()
            if npmrc_path == "./.npmrc":
                npmrc_path = ".npmrc"
            routes = npm_routing.setdefault(npmrc_path, {})
            for source_id in sorted({entry["source"] for entry in npm_entries}):
                source = registry[source_id]
                patterns = source.get("patterns", [])
                for pattern in patterns:
                    if not pattern.startswith("@") or not pattern.endswith("/*"):
                        fail("PKB305", f"npm source {source_id!r} must declare scoped patterns")
                    scope = pattern[:-2]
                    route = {"scope": scope, "registry": source["url"]}
                    authentication = source.get("authentication", {})
                    if authentication.get("required"):
                        credential = authentication.get("credentialEnvironment")
                        if not credential:
                            fail("PKB305", f"authenticated npm source {source_id!r} has no credential environment")
                        route["credentialEnvironment"] = credential
                    routes[scope] = route
        for package in target["packages"]:
            if package["materializationKind"] == "host-image":
                host_entries.append(
                    {
                        "targetId": target["id"],
                        "path": target["path"],
                        "image": package["packageId"],
                        "version": package["version"],
                        "reference": package["reference"],
                        "source": package["source"],
                    }
                )
    if central:
        entries = sorted(central.values(), key=lambda item: item["packageId"].casefold())
        outputs.append(output_record("nuget-central-pins", "eng/ProgramKit.BuildingBlocks.props", entries))
    for path, routes in npm_routing.items():
        outputs.append(output_record("npm-registry-routing", path, [routes[key] for key in sorted(routes)]))
    for activation in lock["activations"]:
        shell_parent = PurePosixPath(activation["path"]).parent
        overlay_path = (shell_parent / "eng/building-blocks.shells.json").as_posix()
        if overlay_path.startswith("./"):
            overlay_path = overlay_path[2:]
        shell_activations.setdefault(overlay_path, []).append(copy.deepcopy(activation))
    for path, entries in shell_activations.items():
        entries.sort(key=lambda item: (item["shell"], item["featureIdentity"], item["packageKey"]))
        outputs.append(output_record("cshell-activations", path, entries))
    if host_entries:
        host_entries.sort(key=lambda item: (item["path"].casefold(), item["targetId"]))
        outputs.append(output_record("host-images", ".program-kit/building-blocks.hosts.json", host_entries))
    if lock["configurationRequirements"]:
        outputs.append(
            output_record(
                "configuration-requirements",
                ".program-kit/building-blocks.configuration.json",
                copy.deepcopy(lock["configurationRequirements"]),
            )
        )
    identities: dict[str, str] = {}
    for output in outputs:
        path = normalize_path(output["path"], "managed output path")
        identity = path.casefold()
        if identity in identities:
            fail("PKB306", f"managed outputs collide at {path!r}: {identities[identity]} and {output['kind']}")
        identities[identity] = output["kind"]
    return sorted(outputs, key=lambda item: (item["path"].casefold(), item["kind"]))


def render_central_pins(entries: list[dict]) -> str:
    lines = ["<Project>", "  <ItemGroup Label=\"ProgramKit.BuildingBlocks\">"]
    lines.extend(
        f'    <PackageVersion Include="{entry["packageId"]}" Version="{entry["version"]}" />'
        for entry in entries
    )
    lines.extend(["  </ItemGroup>", "</Project>"])
    return "\n".join(lines) + "\n"


def render_project_region(entries: list[dict]) -> str:
    lines = [BEGIN_MARKER, '  <ItemGroup Label="ProgramKit.BuildingBlocks">']
    lines.extend(f'    <PackageReference Include="{entry["packageId"]}" />' for entry in entries)
    lines.extend(["  </ItemGroup>", END_MARKER])
    return "\n".join(lines)


def render_npmrc_region(entries: list[dict]) -> str:
    lines = [NPMRC_BEGIN]
    for entry in entries:
        registry = entry["registry"].rstrip("/")
        lines.append(f'{entry["scope"]}:registry={registry}')
        credential = entry.get("credentialEnvironment")
        if credential:
            authority = registry.split("://", 1)[-1]
            lines.append(f'//{authority}/:_authToken=${{{credential}}}')
    lines.append(NPMRC_END)
    return "\n".join(lines)


def render_generated_json(kind: str, entries: list[dict]) -> str:
    if kind == "cshell-activations":
        shells: dict[str, dict] = {}
        for entry in entries:
            shell = shells.setdefault(entry["shell"], {"Features": {}})
            shell["Features"].setdefault(entry["featureIdentity"], {})
        return pretty_json({"CShells": {"Shells": shells}})
    property_names = {
        "host-images": "hosts",
        "configuration-requirements": "requirements",
    }
    return pretty_json({"schemaVersion": SCHEMA_VERSION, property_names[kind]: entries})


def output_map(lock: dict) -> dict[str, dict]:
    return {output["path"]: output for output in lock.get("managedOutputs", [])}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        fail("PKB402", f"cannot read managed output {path}: {error}")


def marker_region(content: str, begin: str, end: str, path: Path) -> str | None:
    if content.count(begin) != content.count(end) or content.count(begin) > 1:
        fail("PKB402", f"managed markers are malformed in {path}")
    if begin not in content:
        return None
    start = content.index(begin)
    finish = content.index(end, start) + len(end)
    return content[start:finish].replace("\r\n", "\n")


def check_output(repository: Path, output: dict) -> None:
    path = repository_path(repository, output["path"])
    if not path.is_file():
        fail("PKB402", f"managed output is missing: {output['path']}")
    kind = output["kind"]
    entries = output["entries"]
    if output.get("ownedSha256") != canonical_sha256({"kind": kind, "entries": entries}):
        fail("PKB401", f"lock ownership hash is stale for {output['path']}")
    if kind == "nuget-central-pins":
        if read_text(path).replace("\r\n", "\n") != render_central_pins(entries):
            fail("PKB403", f"selected NuGet central pins drifted: {output['path']}")
    elif kind == "nuget-project":
        actual = marker_region(read_text(path), BEGIN_MARKER, END_MARKER, path)
        if actual != render_project_region(entries):
            fail("PKB403", f"direct NuGet references drifted: {output['path']}")
    elif kind == "npm-registry-routing":
        actual = marker_region(read_text(path), NPMRC_BEGIN, NPMRC_END, path)
        if actual != render_npmrc_region(entries):
            fail("PKB403", f"npm registry routing drifted: {output['path']}")
    elif kind == "npm-package":
        value = load_json(path)
        for entry in entries:
            section = require_object(value.get(entry["section"]), f"{output['path']} {entry['section']}")
            if section.get(entry["packageId"]) != entry["version"]:
                fail("PKB403", f"npm dependency {entry['packageId']} drifted in {output['path']}")
            opposite = "devDependencies" if entry["section"] == "dependencies" else "dependencies"
            if entry["packageId"] in value.get(opposite, {}):
                fail("PKB403", f"npm dependency {entry['packageId']} appears in both sections of {output['path']}")
    elif kind == "dotnet-tool-manifest":
        value = load_json(path)
        tools = require_object(value.get("tools"), f"{output['path']} tools")
        for entry in entries:
            actual = tools.get(entry["packageId"].lower())
            expected = {"version": entry["version"], "commands": entry["commands"]}
            if actual != expected:
                fail("PKB403", f"dotnet tool {entry['packageId']} drifted in {output['path']}")
    elif kind in {"cshell-activations", "host-images", "configuration-requirements"}:
        if read_text(path).replace("\r\n", "\n") != render_generated_json(kind, entries):
            fail("PKB403", f"generated {kind} drifted: {output['path']}")
    else:
        fail("PKB401", f"lock contains unsupported managed output kind {kind!r}")


def check_materialization(repository: Path, lock: dict) -> None:
    for output in lock.get("managedOutputs", []):
        check_output(repository, output)
    audit_unmanaged_dependencies(repository, load_json(default_catalog(Path(__file__))), lock)


def repository_files(repository: Path, pattern: str) -> list[Path]:
    ignored = {".git", ".specify", "artifacts", "node_modules", "bin", "obj"}
    return sorted(
        path
        for path in repository.rglob(pattern)
        if not any(part in ignored for part in path.relative_to(repository).parts)
    )


def audit_unmanaged_dependencies(repository: Path, catalog: dict, ownership_lock: dict | None) -> None:
    owned = output_map(ownership_lock or {})
    # The coordinator's engineering baseline and retained proof inputs have their own
    # authorities. Never infer ownership from a docs/specs directory name.
    governance = Path(__file__).resolve().parents[2] / 'program-kit-governance/scripts'
    exempt = set()
    if (governance / 'dependency_audit.py').is_file():
        sys.path.insert(0, str(governance))
        try:
            from dependency_audit import audit_exemptions
            exempt = audit_exemptions(repository, ownership_lock or {})
        except (OSError, ValueError, KeyError, TypeError) as error:
            fail('PKB405', str(error))
        finally:
            sys.path.remove(str(governance))
    nuget_ids = {
        package["packageId"].casefold()
        for package in catalog["packages"].values()
        if package["ecosystem"] == "nuget"
    }
    npm_ids = {
        package["packageId"]
        for package in catalog["packages"].values()
        if package["ecosystem"] == "npm"
    }
    findings: list[str] = []
    reference_pattern = re.compile(r'<PackageReference\s+[^>]*Include="([^"]+)"', re.IGNORECASE)
    version_pattern = re.compile(r'<PackageVersion\s+[^>]*Include="([^"]+)"', re.IGNORECASE)
    for path in repository_files(repository, "*.csproj"):
        if path.resolve() in exempt:
            continue
        relative = path.relative_to(repository).as_posix()
        content = read_text(path)
        prior = owned.get(relative)
        if prior and prior["kind"] == "nuget-project":
            content = remove_marker_region(content, BEGIN_MARKER, END_MARKER, path)
        for package_id in reference_pattern.findall(content):
            if package_id.casefold() in nuget_ids:
                findings.append(f"unmanaged NuGet reference {package_id} in {relative}")
    for path in repository_files(repository, "*.props"):
        relative = path.relative_to(repository).as_posix()
        if relative in owned and owned[relative]["kind"] == "nuget-central-pins":
            continue
        if path.resolve() in exempt:
            continue
        for package_id in version_pattern.findall(read_text(path)):
            if package_id.casefold() in nuget_ids:
                findings.append(f"unmanaged NuGet pin {package_id} in {relative}")
    for path in repository_files(repository, "package.json"):
        if path.resolve() in exempt:
            continue
        relative = path.relative_to(repository).as_posix()
        value = load_json(path)
        prior = owned.get(relative)
        previous_entries = prior["entries"] if prior and prior["kind"] == "npm-package" else []
        previous_ids = {entry["packageId"] for entry in previous_entries}
        for section_name in ("dependencies", "devDependencies", "optionalDependencies", "peerDependencies"):
            section = value.get(section_name, {})
            if not isinstance(section, dict):
                fail("PKB405", f"{relative} {section_name} must be an object")
            for package_id in section:
                if package_id in npm_ids and package_id not in previous_ids:
                    findings.append(f"unmanaged npm dependency {package_id} in {relative}")
    for path in repository_files(repository, "dotnet-tools.json"):
        if path.resolve() in exempt:
            continue
        relative = path.relative_to(repository).as_posix()
        value = load_json(path)
        tools = value.get("tools", {})
        if not isinstance(tools, dict):
            fail("PKB405", f"{relative} tools must be an object")
        prior = owned.get(relative)
        previous_ids = {
            entry["packageId"].casefold()
            for entry in prior["entries"]
        } if prior and prior["kind"] == "dotnet-tool-manifest" else set()
        for package_id in tools:
            if package_id.casefold() in nuget_ids and package_id.casefold() not in previous_ids:
                findings.append(f"unmanaged dotnet tool {package_id} in {relative}")
    if findings:
        fail("PKB405", "building-block dependencies must be selection-owned: " + "; ".join(sorted(findings)))


def remove_marker_region(content: str, begin: str, end: str, path: Path) -> str:
    region = marker_region(content, begin, end, path)
    if region is None:
        return content
    normalized = content.replace("\r\n", "\n")
    start = normalized.index(begin)
    finish = normalized.index(end, start) + len(end)
    before = normalized[:start].rstrip("\n")
    after = normalized[finish:].lstrip("\n")
    return before + ("\n" if before and after else "") + after


def add_xml_region(content: str, region: str, path: Path) -> str:
    normalized = content.replace("\r\n", "\n")
    closing = normalized.rfind("</Project>")
    if closing < 0:
        fail("PKB404", f"NuGet target is not an MSBuild project: {path}")
    before = normalized[:closing].rstrip("\n")
    after = normalized[closing:]
    return before + "\n" + region + "\n" + after


def add_text_region(content: str, region: str) -> str:
    normalized = content.replace("\r\n", "\n").rstrip("\n")
    return (normalized + "\n" if normalized else "") + region + "\n"


def reconcile_json_entries(path: Path, previous: dict | None, desired: dict | None) -> str:
    if not path.is_file():
        fail("PKB404", f"consumer-owned JSON target is missing: {path}")
    value = load_json(path)
    previous_entries = previous["entries"] if previous else []
    desired_entries = desired["entries"] if desired else []
    kind = (desired or previous)["kind"]
    if kind == "npm-package":
        for entry in previous_entries:
            section = value.get(entry["section"], {})
            if isinstance(section, dict):
                section.pop(entry["packageId"], None)
        for entry in desired_entries:
            for section_name in ("dependencies", "devDependencies"):
                section = value.get(section_name)
                if section is not None and not isinstance(section, dict):
                    fail("PKB404", f"{path} {section_name} must be an object")
                if isinstance(section, dict) and entry["packageId"] in section:
                    fail("PKB404", f"refusing to adopt manually owned npm dependency {entry['packageId']} in {path}")
            value.setdefault(entry["section"], {})[entry["packageId"]] = entry["version"]
        for section_name in ("dependencies", "devDependencies"):
            if isinstance(value.get(section_name), dict):
                value[section_name] = dict(sorted(value[section_name].items()))
    else:
        tools = value.setdefault("tools", {})
        if not isinstance(tools, dict):
            fail("PKB404", f"{path} tools must be an object")
        for entry in previous_entries:
            tools.pop(entry["packageId"].lower(), None)
        for entry in desired_entries:
            key = entry["packageId"].lower()
            if key in tools:
                fail("PKB404", f"refusing to adopt manually owned dotnet tool {entry['packageId']} in {path}")
            tools[key] = {"version": entry["version"], "commands": entry["commands"]}
        value["tools"] = dict(sorted(tools.items()))
    return pretty_json(value)


def reconcile_output(repository: Path, previous: dict | None, desired: dict | None) -> tuple[Path, str | None]:
    output = desired or previous
    assert output is not None
    path = repository_path(repository, output["path"])
    if previous and desired and previous["kind"] != desired["kind"]:
        fail("PKB404", f"managed output kind changed at {output['path']}; recover before applying")
    kind = output["kind"]
    if kind == "nuget-central-pins":
        if not previous and path.exists():
            fail("PKB404", f"refusing to overwrite unowned generated file {output['path']}")
        return path, render_central_pins(desired["entries"]) if desired else None
    if kind in {"cshell-activations", "host-images", "configuration-requirements"}:
        if not previous and path.exists():
            fail("PKB404", f"refusing to overwrite unowned generated file {output['path']}")
        return path, render_generated_json(kind, desired["entries"]) if desired else None
    if kind in {"npm-package", "dotnet-tool-manifest"}:
        return path, reconcile_json_entries(path, previous, desired)
    if not path.is_file() and kind == "nuget-project":
        fail("PKB404", f"selected .NET project does not exist: {output['path']}")
    content = read_text(path) if path.is_file() else ""
    if kind == "nuget-project":
        if not previous and marker_region(content, BEGIN_MARKER, END_MARKER, path) is not None:
            fail("PKB404", f"refusing to adopt an unowned Program Kit region in {output['path']}")
        content = remove_marker_region(content, BEGIN_MARKER, END_MARKER, path)
        if desired:
            content = add_xml_region(content, render_project_region(desired["entries"]), path)
        return path, content
    if kind == "npm-registry-routing":
        if not previous and marker_region(content, NPMRC_BEGIN, NPMRC_END, path) is not None:
            fail("PKB404", f"refusing to adopt an unowned Program Kit registry region in {output['path']}")
        content = remove_marker_region(content, NPMRC_BEGIN, NPMRC_END, path)
        if desired:
            content = add_text_region(content, render_npmrc_region(desired["entries"]))
        return path, content or None
    fail("PKB401", f"unsupported managed output kind {kind!r}")


def atomic_write_bytes(path: Path, content: bytes, suffix: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{suffix}.tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)


def transaction_root(repository: Path) -> Path:
    return repository / ".program-kit/building-block-transactions"


def recover_materialization(repository: Path) -> list[str]:
    root = transaction_root(repository)
    if not root.is_dir():
        return []
    recovered: list[str] = []
    for transaction in sorted(path for path in root.iterdir() if path.is_dir()):
        journal_path = transaction / "journal.json"
        if not journal_path.is_file():
            shutil.rmtree(transaction)
            recovered.append(transaction.name)
            continue
        journal = load_json(journal_path)
        if journal.get("status") == "committed":
            shutil.rmtree(transaction)
            recovered.append(transaction.name)
            continue
        conflicts: list[str] = []
        for action in reversed(require_list(journal.get("actions"), "transaction actions")):
            relative = normalize_path(action.get("path"), "transaction path")
            destination = repository_path(repository, relative)
            current_hash = hashlib.sha256(destination.read_bytes()).hexdigest() if destination.is_file() else None
            allowed = {value for value in (action.get("originalSha256"), action.get("desiredSha256")) if value}
            if current_hash is not None and current_hash not in allowed:
                conflicts.append(relative)
                continue
            backup = transaction / "backup" / relative
            if backup.is_file():
                atomic_write_bytes(destination, backup.read_bytes(), transaction.name)
            elif destination.is_file():
                destination.unlink()
        if conflicts:
            fail("PKB503", "recovery preserved externally changed paths: " + ", ".join(sorted(conflicts)))
        shutil.rmtree(transaction)
        recovered.append(transaction.name)
    return recovered


def commit_transaction(repository: Path, changes: list[tuple[Path, str | None]], lock_path: Path, lock: dict) -> str:
    root = transaction_root(repository)
    pending = sorted(path for path in root.iterdir() if path.is_dir()) if root.is_dir() else []
    if pending:
        fail("PKB501", "unfinished building-block transaction exists; run recover before applying")
    transaction_id = uuid.uuid4().hex
    transaction = root / transaction_id
    stage = transaction / "stage"
    backup = transaction / "backup"
    transaction.mkdir(parents=True)
    all_changes = list(changes) + [(lock_path, pretty_json(lock))]
    actions: list[dict] = []
    for path, content in all_changes:
        try:
            relative = path.resolve().relative_to(repository.resolve()).as_posix()
        except ValueError:
            fail("PKB300", f"transaction path escapes repository: {path}")
        original = path.read_bytes() if path.is_file() else None
        desired = content.encode("utf-8") if content is not None else None
        if original is not None:
            backup_path = backup / relative
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            backup_path.write_bytes(original)
        if desired is not None:
            stage_path = stage / relative
            stage_path.parent.mkdir(parents=True, exist_ok=True)
            stage_path.write_bytes(desired)
        actions.append(
            {
                "path": relative,
                "operation": "remove" if desired is None else "write",
                "originalSha256": hashlib.sha256(original).hexdigest() if original is not None else None,
                "desiredSha256": hashlib.sha256(desired).hexdigest() if desired is not None else None,
            }
        )
    journal = {"schemaVersion": 1, "transactionId": transaction_id, "status": "staged", "actions": actions}
    journal_path = transaction / "journal.json"
    atomic_write(journal_path, pretty_json(journal))
    try:
        journal["status"] = "committing"
        atomic_write(journal_path, pretty_json(journal))
        fail_after_text = os.environ.get("PROGRAMKIT_TEST_BUILDING_BLOCK_FAIL_AFTER_ACTION", "")
        fail_after = int(fail_after_text) if fail_after_text.isdigit() else None
        for index, action in enumerate(actions, 1):
            destination = repository_path(repository, action["path"])
            if action["operation"] == "remove":
                if destination.is_file():
                    destination.unlink()
            else:
                atomic_write_bytes(destination, (stage / action["path"]).read_bytes(), transaction_id)
            if fail_after == index:
                raise OSError(f"injected materialization interruption after action {index}")
        journal["status"] = "committed"
        atomic_write(journal_path, pretty_json(journal))
    except Exception:
        recover_materialization(repository)
        raise
    shutil.rmtree(transaction)
    return transaction_id


def apply_materialization(repository: Path, lock_path: Path, lock: dict, catalog: dict) -> str:
    previous_lock = load_json(lock_path) if lock_path.is_file() else None
    if previous_lock:
        check_materialization(repository, previous_lock)
    else:
        audit_unmanaged_dependencies(repository, catalog, None)
    previous_outputs = output_map(previous_lock or {})
    desired_outputs = output_map(lock)
    paths = sorted(set(previous_outputs) | set(desired_outputs), key=str.casefold)
    changes: list[tuple[Path, str | None]] = []
    for relative in paths:
        changes.append(
            reconcile_output(repository, previous_outputs.get(relative), desired_outputs.get(relative))
        )
    transaction_id = commit_transaction(repository, changes, lock_path, lock)
    check_materialization(repository, lock)
    return transaction_id


def find_program_kit_version(script: Path) -> str:
    for parent in script.resolve().parents:
        candidate = parent / "VERSION"
        if candidate.is_file():
            value = candidate.read_text(encoding="utf-8").strip()
            if value:
                return value
    return "0.12.0"


def default_catalog(script: Path) -> Path:
    return script.resolve().parents[1] / "references" / "orbyss-building-blocks.json"


def profile_registry() -> Path:
    return Path(__file__).resolve().parents[1] / 'references/dependency-profiles'


def materialize_dependency_profile(catalog: dict, selected: dict) -> dict:
    if selected.get('schemaVersion') != 1 or selected.get('compositionSha256') != canonical_sha256(composition_projection(catalog)):
        fail('PKB610', 'dependency profile requires different composition rules; review an architecture transition')
    if set(selected['artifacts']) != set(catalog['packages']) or set(selected['families']) != set(catalog['families']):
        fail('PKB610', 'dependency profile must pin the complete registered artifact set')
    result = copy.deepcopy(catalog)
    result['resolutionRevision'] = selected['resolutionRevision']
    for key, pin in selected['artifacts'].items(): result['packages'][key]['version'] = pin
    for key, pins in selected['families'].items():
        result['families'][key].pop('toolVersions', None)
        result['families'][key].update(pins)
    validate_catalog(result)
    if catalog_resolution_sha256(result) != selected['catalogResolutionSha256']:
        fail('PKB610', 'dependency profile resolution hash differs')
    return result


def validate_additive_profile_catalog(base: dict, target: dict) -> None:
    """Permit new contracts/selections without rewriting any historical rule owner."""
    validate_catalog(base)
    validate_catalog(target)
    for field in set(base) | set(target):
        if field in {'$schema', 'resolutionRevision', 'families', 'packages', 'capabilities', 'compositions'}:
            continue
        if base.get(field) != target.get(field):
            fail('PKB610', f'additive profile catalog must preserve {field!r} unchanged')
    if not set(base['families']) <= set(target['families']):
        fail('PKB610', 'additive profile catalog must preserve existing family identities')
    for key, family in base['families'].items():
        metadata = lambda value: {field: item for field, item in value.items() if field not in {'releaseVersion', 'toolVersions'}}
        if metadata(family) != metadata(target['families'][key]):
            fail('PKB610', f'additive profile catalog must preserve family {key!r} metadata')
    for field in ('capabilities', 'compositions'):
        for key, value in base[field].items():
            if target[field].get(key) != value:
                fail('PKB610', f'additive profile catalog must preserve existing {field} {key!r} unchanged')
    for key, package in base['packages'].items():
        current = target['packages'].get(key)
        if current is None:
            fail('PKB610', f'additive profile catalog cannot remove artifact {key!r}')
        metadata = lambda value: {field: item for field, item in value.items() if field not in {'version', 'requires'}}
        if metadata(package) != metadata(current):
            fail('PKB610', f'additive profile catalog must preserve artifact {key!r} metadata unchanged')
        if current['requires'][:len(package['requires'])] != package['requires']:
            fail('PKB610', f'additive profile catalog requires append-only companions for {key!r}')
        if len({canonical_sha256(item) for item in current['requires']}) != len(current['requires']):
            fail('PKB610', f'additive profile catalog duplicates companions for {key!r}')


def dependency_profile_catalog(directory: Path, entry: dict, supplied: dict) -> dict:
    """Select only an index-bound immutable catalog, from its exact base or retained target."""
    binding = entry.get('catalogSnapshot')
    if binding is None:
        return supplied  # Historical profiles retain their existing materialization contract.
    binding = require_object(binding, 'profile.catalogSnapshot')
    if set(binding) != {'path', 'sha256', 'base'}:
        fail('PKB611', 'catalog snapshot requires exact target and immutable base bindings')

    def snapshot(reference: dict, label: str) -> dict:
        reference = require_object(reference, label)
        if set(reference) != {'path', 'sha256'}:
            fail('PKB611', f'{label} requires an exact path and hash')
        path = repository_path(directory, normalize_path(reference['path'], label + '.path'))
        expected = require_sha(reference['sha256'], label + '.sha256')
        if not path.is_file() or raw_sha256(path) != expected:
            fail('PKB611', f'{label} catalog is missing or changed')
        return load_json(path)

    base = snapshot(binding['base'], 'immutable base')
    target = snapshot({key: binding[key] for key in ('path', 'sha256')}, 'selected snapshot')
    validate_additive_profile_catalog(base, target)
    actual = canonical_sha256(composition_projection(supplied))
    if actual not in {canonical_sha256(composition_projection(base)), canonical_sha256(composition_projection(target))}:
        fail('PKB610', 'profile catalog requires its exact base or target composition; review an architecture transition')
    return target


def dependency_profile_changes(old: dict, new: dict) -> dict:
    """Expose additive and semantic artifact changes in the existing consumer review."""
    before, after = resolution_projection(old)['packages'], resolution_projection(new)['packages']
    added, removed = sorted(set(after) - set(before)), sorted(set(before) - set(after))
    changed = [key for key in old['packages'] if before[key] != after.get(key)] + added
    return {'changedArtifacts': changed, 'addedArtifacts': added, 'removedArtifacts': removed}


def named_official_tool_bindings(source: dict, selected: dict) -> dict:
    """New named recipes bind selected Build/exporter bytes; historical receipts stay unchanged."""
    tools = require_object(source.get('officialTools'), 'named qualification officialTools')
    public_source = 'https://api.nuget.org/v3/index.json'
    expected = {'Orbyss.Foundation.Build', 'Orbyss.Foundation.OpenApi.Exporter'}
    if set(tools) != expected:
        fail('PKB611', 'named qualification requires exact official Build and exporter bindings')
    for identity, binding in tools.items():
        binding = require_object(binding, 'named qualification official tool')
        version = selected['artifacts'].get('nuget:' + identity)
        archive = ('https://api.nuget.org/v3-flatcontainer/' + identity.lower() + '/' + str(version).lower()
                   + '/' + identity.lower() + '.' + str(version).lower() + '.nupkg')
        if (set(binding) != {'id', 'version', 'sha256', 'source', 'nativeSource', 'archiveUrl', 'nativeProvenanceSha256'}
                or version is None or binding.get('id') != identity or binding.get('version') != version
                or binding.get('source') != public_source or binding.get('nativeSource') not in (None, public_source)
                or binding.get('archiveUrl') != archive
                or not re.fullmatch(r'[a-f0-9]{64}', str(binding.get('sha256', '')))
                or not re.fullmatch(r'[a-f0-9]{64}', str(binding.get('nativeProvenanceSha256', '')))):
            fail('PKB611', 'named qualification official tooling differs from exact selected versions or public source')
    digest = hashlib.sha256((json.dumps(tools, indent=2, sort_keys=True) + '\n').encode('utf-8')).hexdigest()
    if source.get('officialToolsSha256') != digest:
        fail('PKB611', 'named qualification official tooling proof changed')
    return tools


def qualified_dependency_profile(directory: Path, identity: str | None, catalog: dict) -> tuple[dict, dict]:
    directory = Path(directory).resolve()
    index = load_json(directory / 'index.json')
    identity = identity or index.get('default')
    entry = index['profiles'].get(identity)
    if index.get('schemaVersion') != 1 or entry is None or entry.get('status') != 'qualified':
        fail('PKB611', 'unlisted or unqualified combination requires explicit qualification before support')
    path = repository_path(directory, entry['path'])
    if raw_sha256(path) != entry['sha256']: fail('PKB611', 'qualified profile changed')
    selected = load_json(path)
    if selected['id'] != identity: fail('PKB611', 'profile identity differs')
    result = materialize_dependency_profile(dependency_profile_catalog(directory, entry, catalog), selected)
    proof = repository_path(directory, entry['evidence']['path'])
    if raw_sha256(proof) != entry['evidence']['sha256']: fail('PKB611', 'qualification evidence changed')
    receipt = load_json(proof)
    named_recipe = entry.get('qualificationRecipe')
    named_tools = None
    named_hash = receipt.get('source', {}).get('qualificationRecipeSha256')
    if (named_recipe is None) != (named_hash is None):
        fail('PKB611', 'named qualification receipt requires its matching registered recipe')
    if named_recipe is not None:
        named_recipe = require_object(named_recipe, 'profile.qualificationRecipe')
        if set(named_recipe) != {'path', 'sha256'}:
            fail('PKB611', 'named qualification recipe requires an exact path and hash')
        recipe_path = repository_path(directory, normalize_path(named_recipe['path'], 'profile.qualificationRecipe.path'))
        if not recipe_path.is_file() or raw_sha256(recipe_path) != require_sha(named_recipe['sha256'], 'profile.qualificationRecipe.sha256'):
            fail('PKB611', 'named qualification recipe changed')
        recipe = load_json(recipe_path)
        snapshot = entry.get('catalogSnapshot', {})
        if (set(recipe) != {'schemaVersion', 'id', 'profile', 'families', 'catalogSnapshot', 'nativeLock', 'executor'}
                or recipe.get('schemaVersion') != 1 or not isinstance(recipe.get('id'), str) or not ID.fullmatch(recipe['id'])
                or receipt.get('status') != 'dependency-profile-qualified' or receipt.get('schemaVersion') != 2
                or named_hash != named_recipe['sha256']
                or recipe.get('profile', {}).get('id') != identity
                or recipe.get('profile', {}).get('sha256') != entry['sha256']
                or recipe.get('families') != selected['families']
                or recipe.get('catalogSnapshot', {}).get('sha256') != snapshot.get('sha256')
                or recipe.get('catalogSnapshot', {}).get('base', {}).get('sha256') != snapshot.get('base', {}).get('sha256')
                or recipe.get('executor', {}).get('sha256') != receipt.get('source', {}).get('recipeSha256')
                or recipe.get('nativeLock', {}).get('sha256') != receipt.get('source', {}).get('lockSha256')):
            fail('PKB611', 'named qualification recipe differs from its exact profile, catalog, executor or lock evidence')
        named_tools = named_official_tool_bindings(receipt['source'], selected)
    steps = receipt.get('steps')
    if (receipt.get('catalog', {}).get('sha256') != selected['catalogResolutionSha256']
            or not isinstance(steps, list) or not steps
            or any(not isinstance(step, dict) or type(step.get('exitCode')) is not int
                   or step['exitCode'] != 0 for step in steps)):
        fail('PKB611', 'qualification receipt does not establish this exact combination')
    if receipt.get('status') == 'release-validation-passed':
        if not receipt.get('source', {}).get('clean'):
            fail('PKB611', 'qualification receipt requires clean Release source')
    elif receipt.get('status') == 'dependency-profile-qualified' and receipt.get('schemaVersion') == 2:
        required = {'locked-restore', 'consumer-build-pack', 'publisher-descriptors',
                    'public-exporter-restore', 'activation-export-matrix', 'producer-version-rejection',
                    'published-forms-browser', 'public-artifact-availability', 'published-host-runtime'}
        source = require_object(receipt.get('source'), 'qualification.source')
        scope = require_object(receipt.get('scope'), 'qualification.scope')
        allowed = sorted({activation['featureIdentity'] for package in result['packages'].values()
                          for activation in package.get('activations', [])})
        matrix = receipt.get('activationMatrix')
        if (source.get('kind') != 'generic-publisher-integration'
                or not re.fullmatch(r'[0-9a-f]{64}', str(source.get('recipeSha256', '')))
                or source['recipeSha256'] != entry.get('recipeSha256')
                or not re.fullmatch(r'[0-9a-f]{64}', str(source.get('lockSha256', '')))
                or source['lockSha256'] != entry.get('nativeLockSha256')
                or scope.get('claim') != 'publisher-metadata-and-exporter-admission'
                or scope.get('allowedActivations') != allowed or entry.get('allowedActivations') != allowed
                or any(not isinstance(step.get('id'), str) for step in steps)
                or {step['id'] for step in steps} != required or len(steps) != len(required)
                or any(not re.fullmatch(r'[0-9a-f]{64}', str(step.get('evidenceSha256', ''))) for step in steps)
                or not isinstance(matrix, list) or len(matrix) != len(allowed)
                or any(not isinstance(row, dict) or not isinstance(row.get('activation'), str)
                       or not isinstance(row.get('closure'), list)
                       or any(not isinstance(value, str) for value in row['closure'])
                       or row['closure'] != sorted(set(row['closure']))
                       or row['activation'] not in row['closure']
                       or not re.fullmatch(r'[0-9a-f]{64}', str(row.get('evidenceSha256', ''))) for row in matrix)
                or sorted(row['activation'] for row in matrix) != allowed):
            fail('PKB611', 'generic qualification requires complete publisher, browser and activation matrix evidence')
        compositions = receipt.get('compositionMatrix')
        scenario_features = {
            'minimal-web': {'Orbyss.Foundation.Web.OpenApi', 'Orbyss.Foundation.WebDefaults'},
            'spa-assurance': {'Orbyss.Foundation.Authentication.SpaPkce', 'Orbyss.Foundation.Authentication.Assurance'},
            'bff-assurance': {'Orbyss.Foundation.Authentication.BffCookie', 'Orbyss.Foundation.Authentication.Assurance'},
            'forms-localization': {'Orbyss.Forms.Web.Runtime', 'Orbyss.Forms.Web.Submissions', 'Orbyss.Localization.Web.Runtime'}}
        if (not isinstance(compositions, list) or len(compositions) != len(scenario_features)
                or any(not isinstance(row, dict) or not isinstance(row.get('composition'), str)
                       or row['composition'] not in scenario_features or not isinstance(row.get('closure'), list)
                       or any(not isinstance(value, str) for value in row['closure'])
                       or not scenario_features[row['composition']] <= set(row['closure'])
                       or not re.fullmatch(r'[0-9a-f]{64}', str(row.get('evidenceSha256', ''))) for row in compositions)
                or {row['composition'] for row in compositions} != set(scenario_features)
                or any(row['closure'] != sorted(set(row['closure']))
                       or 'ProgramKitQualificationProbe' not in row['closure']
                       or not set(row['closure']) <= set(allowed) | {'ProgramKitQualificationProbe'} for row in matrix + compositions)):
            fail('PKB611', 'generic qualification requires representative compositions with registered activation closures')
        artifacts = require_object(receipt.get('artifacts'), 'qualification.artifacts')
        for package in result['packages'].values():
            if package['ecosystem'] == 'nuget' and (package.get('activations') or named_recipe is not None
                    and package['materialization']['kind'] == 'nuget-project'):
                bound = require_object(named_tools['Orbyss.Foundation.Build'] if named_tools is not None
                                       and package['packageId'] == 'Orbyss.Foundation.Build'
                                       else artifacts.get(package['packageId']), 'qualification.artifact')
                if (bound.get('version') != package['version']
                        or not re.fullmatch(r'[0-9a-f]{64}', str(bound.get('sha256', '')))):
                    fail('PKB611', 'generic qualification artifact differs from the exact dependency profile')
        if named_tools is not None:
            for identity, binding in named_tools.items():
                artifact = require_object(artifacts.get(identity), 'qualification.officialToolArtifact')
                if artifact.get('version') != binding['version'] or artifact.get('sha256') != binding['sha256']:
                    fail('PKB611', 'named qualification official tool artifact differs from its source proof')
        browser = require_object(receipt.get('browserIntegration'), 'qualification.browserIntegration')
        browser_profile = require_object(browser.get('profile'), 'qualification.browserProfile')
        browser_stages = require_object(browser.get('stages'), 'qualification.browserStages')
        browser_packages = require_object(browser_profile.get('packages'), 'qualification.browserPackages')
        if (browser_profile.get('catalogResolutionSha256') != selected['catalogResolutionSha256']
                or not browser_packages or any(selected['artifacts'].get('npm:' + key) != pin for key, pin in browser_packages.items())
                or set(browser_stages) != {'strict-graph', 'renew', 'locked', 'bundle', 'browser'}
                or any(not re.fullmatch(r'[0-9a-f]{64}', str(value)) for value in browser_stages.values())
                or not isinstance(browser.get('engines'), list)
                or any(not isinstance(engine, str) for engine in browser['engines'])
                or not {'chromium', 'webkit'} <= set(browser['engines'])
                or next(step for step in steps if step['id'] == 'published-forms-browser')['evidenceSha256'] != canonical_sha256(browser)):
            fail('PKB611', 'generic qualification browser evidence differs from the exact dependency profile')
        available = receipt.get('availableArtifacts')
        if (not isinstance(available, list) or len(available) != len(selected['artifacts'])
                or any(not isinstance(item, dict) or not isinstance(item.get('packageKey'), str) for item in available)
                or {item['packageKey']: item.get('version') for item in available} != selected['artifacts']):
            fail('PKB611', 'generic qualification requires availability of every exact artifact')
        if next(step for step in steps if step['id'] == 'producer-version-rejection').get('observedExitCode') != 2:
            fail('PKB611', 'generic qualification must observe a rejected producer version')
        host = require_object(receipt.get('hostRuntime'), 'qualification.hostRuntime')
        host_inputs = require_object(host.get('inputs'), 'qualification.hostInputs')
        host_artifact = next(item for item in available if item['packageKey'] == 'oci:ghcr.io/orbyss-io/foundation-host')
        expected_cases = ['PublishedHost.bundle_restart', 'PublishedHost.exact_image_activation',
                          'PublishedHost.http_profiles_headers_openapi', 'Shell.actual_registration_and_replacement',
                          'Shell.compiled_boundary_positive_and_negative']
        if (host.get('satisfied') is not True or host.get('cases') != expected_cases
                or host_inputs.get('catalogResolutionSha256') != selected['catalogResolutionSha256']
                or host_inputs.get('foundationRelease') != selected['families']['foundation']['releaseVersion']
                or host_inputs.get('hostImage') != host_artifact.get('reference')
                or not re.fullmatch(r'ghcr\.io/orbyss-io/foundation-host@sha256:[0-9a-f]{64}', str(host_inputs.get('hostImage', '')))
                or not re.fullmatch(r'[0-9a-f]{64}', str(host.get('resultsSha256', '')))
                or next(step for step in steps if step['id'] == 'published-host-runtime')['evidenceSha256'] != canonical_sha256(host)):
            fail('PKB611', 'generic qualification requires exact published host compatibility evidence')
    elif receipt.get('status') == 'dependency-profile-qualified':
        required = {'locked-restore', 'consumer-build-pack-stage', 'canonical-consumer-descriptors',
                    'native-openapi-export', 'normalize-oasdiff-existing-baseline',
                    'typescript-generation-and-application-compilation', 'native-compatibility-renewal',
                    'native-engine-completion', 'affected-feature-readiness'}
        source = require_object(receipt.get('source'), 'qualification.source')
        scope = require_object(receipt.get('scope'), 'qualification.scope')
        allowed = scope.get('allowedActivations')
        steps = receipt['steps']
        if (receipt.get('schemaVersion') != 1 or source.get('kind') != 'verified-program-kit-bundle'
                or not re.fullmatch(r'[0-9a-f]{40}', str(source.get('commit', '')))
                or any(not re.fullmatch(r'[0-9a-f]{64}', str(source.get(key, '')))
                       for key in ('bundleSha256', 'releaseInputsSha256'))
                or scope.get('claim') != 'native-export-and-runtime-compatibility'
                or not isinstance(allowed, list) or not allowed
                or any(not isinstance(value, str) for value in allowed)
                or allowed != sorted(set(allowed))
                or entry.get('allowedActivations') != allowed
                or any(not isinstance(step.get('id'), str) for step in steps)
                or {step.get('id') for step in steps} != required or len(steps) != len(required)
                or any(not re.fullmatch(r'[0-9a-f]{64}', str(step.get('evidenceSha256', ''))) for step in steps)):
            fail('PKB611', 'native qualification requires complete bound evidence and exact activation scope')
        identities = {activation['featureIdentity'] for package in result['packages'].values()
                      for activation in package.get('activations', [])}
        if not set(allowed) <= identities:
            fail('PKB611', 'native qualification contains an unregistered activation')
    else:
        fail('PKB611', 'qualification receipt does not establish this exact combination')
    return result, selected


def verify_qualification_scope(entry: dict, activations: list[dict]) -> None:
    identities = {activation['featureIdentity'] for activation in activations}
    allowed = entry.get('allowedActivations')
    if (identities.intersection(entry.get('excludedActivations', []))
            or (allowed is not None and not identities <= set(allowed))):
        fail('PKB611', 'selected activation is outside the profile qualification scope; qualify a supported dependency transition')


def new_project_catalog(identity: str | None = None) -> dict:
    return qualified_dependency_profile(profile_registry(), identity, load_json(default_catalog(Path(__file__))))[0]


def verify_new_project_profile(repository: Path, catalog: dict, activations: list[dict]) -> None:
    binding = repository / '.program-kit/dependency-profile.json'
    if not binding.is_file(): return
    record = load_json(binding)
    qualification = record.get('newProjectQualification')
    if qualification is None: return  # Retained historical selections make no new qualification claim.
    directory = profile_registry()
    entry = load_json(directory / 'index.json')['profiles'].get(qualification.get('profile'))
    if entry is None or canonical_sha256(entry) != qualification.get('entrySha256'):
        fail('PKB611', 'new-project qualification scope changed; review its profile explicitly')
    qualified, _ = qualified_dependency_profile(directory, qualification['profile'], catalog)
    if catalog_resolution_sha256(qualified) != catalog_resolution_sha256(catalog):
        fail('PKB611', 'new-project profile differs from its qualified exact dependencies')
    verify_qualification_scope(entry, activations)


def draft_qualified_selection(repository: Path, selection_path: Path, catalog: dict, capabilities: list[str], identity: str | None = None) -> None:
    binding = repository / '.program-kit/dependency-profile.json'
    if binding.exists(): fail('PKB120', 'dependency profile already exists; recover its existing selection instead of creating another Draft')
    directory = profile_registry()
    managed = repository / '.program-kit/managed.json'
    engineering = load_json(managed).get('newProjectDependencyProfile') if managed.is_file() else None
    if identity is None and engineering:
        entry = load_json(directory / 'index.json')['profiles'].get(engineering.get('profile'))
        if entry is None or canonical_sha256(entry) != engineering.get('entrySha256'):
            fail('PKB611', 'scaffolded dependency qualification changed; review a profile explicitly')
        identity = engineering['profile']
    qualified, selected = qualified_dependency_profile(directory, identity, catalog)
    if engineering and identity == engineering.get('profile') and catalog_resolution_sha256(qualified) != engineering.get('catalogResolutionSha256'):
        fail('PKB611', 'scaffolded dependency profile changed')
    entry = load_json(directory / 'index.json')['profiles'][selected['id']]
    draft_selection(repository, selection_path, qualified, capabilities)
    snapshot = repository / '.program-kit/dependency-profiles' / (catalog_resolution_sha256(qualified) + '.json')
    content = pretty_json(qualified)
    try:
        if snapshot.exists() and load_json(snapshot) != qualified:
            fail('PKB111', 'immutable dependency profile snapshot changed')
        if not snapshot.exists(): atomic_write(snapshot, content)
        preserve_dependency_profile(repository, load_json(selection_path), snapshot)
        record = load_json(binding)
        record['newProjectQualification'] = {'profile': selected['id'], 'entrySha256': canonical_sha256(entry)}
        atomic_write(binding, pretty_json(record))
    except Exception:
        binding.unlink(missing_ok=True)
        selection_path.unlink(missing_ok=True)
        raise


def consumer_catalog(repository: Path, selection: dict, candidate: Path) -> Path:
    """Resolve retained exact dependencies independently from installed Program Kit."""
    record_path = repository / '.program-kit/dependency-profile.json'
    if not record_path.exists(): return candidate
    record = load_json(record_path)
    if record.get('schemaVersion') != 2 or record.get('resolutionSha256') != selection['catalog'].get('resolutionSha256'):
        fail('PKB111', 'dependency profile differs from accepted selection; review a dependency transition')
    path = repository_path(repository, record['catalogPath'])
    if raw_sha256(path) != record.get('catalogSha256'):
        fail('PKB111', 'dependency profile snapshot is missing or changed')
    if catalog_resolution_sha256(load_json(path)) != record['resolutionSha256']:
        fail('PKB111', 'dependency profile resolution binding is corrupt')
    profile = repository_path(repository, record['profilePath'])
    if raw_sha256(profile) != record['profileSha256'] or load_json(profile) != dependency_profile_value(load_json(path), record['id']):
        fail('PKB111', 'immutable exact dependency profile changed')
    return path


def preserve_dependency_profile(repository: Path, selection: dict, catalog_path: Path) -> Path:
    """Capture selected exact inputs; Draft capture grants no acceptance authority."""
    catalog = load_json(catalog_path)
    validate_catalog(catalog)
    digest = verify_catalog_binding(selection, catalog)
    relative = '.program-kit/dependency-profiles/' + digest + '.json'
    snapshot = repository_path(repository, relative)
    if snapshot.exists() and load_json(snapshot) != catalog:
        fail('PKB111', 'immutable dependency profile snapshot changed')
    if not snapshot.exists(): atomic_write_bytes(snapshot, catalog_path.read_bytes(), 'profile-capture')
    identity = 'accepted-' + digest[:16]
    profile_relative = '.program-kit/dependency-profiles/' + digest + '.profile.json'
    profile_path = repository_path(repository, profile_relative)
    profile = dependency_profile_value(catalog, identity)
    if profile_path.exists() and load_json(profile_path) != profile:
        fail('PKB111', 'immutable exact dependency profile changed')
    if not profile_path.exists(): atomic_write(profile_path, pretty_json(profile))
    binding = repository / '.program-kit/dependency-profile.json'
    previous = load_json(binding) if binding.is_file() else {}
    record = {'schemaVersion': 2, 'id': identity,
              'resolutionSha256': digest, 'catalogPath': relative,
              'catalogSha256': raw_sha256(snapshot),
              'profilePath': profile_relative, 'profileSha256': raw_sha256(profile_path),
              'familyReleases': selection['catalog']['familyReleases'],
              'authority': ('retained accepted selection; no new compatibility claim' if selection['status'] == 'Accepted'
                            else 'retained Draft dependency suggestions; no acceptance or compatibility approval')}
    if previous.get('resolutionSha256') == digest and 'newProjectQualification' in previous:
        record['newProjectQualification'] = previous['newProjectQualification']
    atomic_write(binding, pretty_json(record))
    return snapshot


def catalog_binding(catalog: dict) -> dict:
    return {
        "id": catalog["catalogId"],
        "schemaVersion": catalog["schemaVersion"],
        "resolutionRevision": catalog["resolutionRevision"],
        "resolutionSha256": catalog_resolution_sha256(catalog),
        "familyReleases": {
            name: family["releaseVersion"] for name, family in sorted(catalog["families"].items())
        },
    }


def draft_selection(repository: Path, selection_path: Path, catalog: dict, capabilities: list[str]) -> None:
    if selection_path.exists():
        fail("PKB120", f"selection already exists; refusing to overwrite consumer architecture: {selection_path}")
    known = require_object(catalog.get("capabilities"), "catalog.capabilities")
    unknown = sorted(set(capabilities) - set(known))
    if unknown:
        fail("PKB121", f"unknown capability suggestions: {unknown}")
    suggestions = [
        {
            "capability": capability,
            "compositions": sorted(unique(list(known[capability]["suggestedCompositions"]), f"capability {capability}")),
        }
        for capability in sorted(set(capabilities))
    ]
    selection = {
        "$schema": ".specify/extensions/program-kit-building-blocks/references/building-block-selection.schema.json",
        "schemaVersion": SCHEMA_VERSION,
        "selectionId": "building-block-selection",
        "revision": 1,
        "status": "Draft",
        "draftSuggestions": suggestions,
        "catalog": catalog_binding(catalog),
        "authority": {
            "architectureMap": "docs/architecture/architecture-map.json",
            "decisionIds": ["building-block-selection"],
            "rationale": "Replace this draft text with the accepted architecture rationale.",
        },
        "scopes": [],
        "targets": [],
        "instances": [],
    }
    atomic_write(selection_path, pretty_json(selection))


def registered_selection(repository: Path, selection_path: Path, selection: dict, architecture: dict) -> dict:
    """Compute the architecture registration before a recoverable promotion writes it."""
    try:
        relative = selection_path.resolve().relative_to(repository.resolve()).as_posix()
    except ValueError:
        fail('PKB300', f'selection path escapes the repository: {selection_path}')
    result = copy.deepcopy(architecture)
    documentation = require_list(result.get('documentation'), 'architecture-map.documentation')
    matching = [item for item in documentation if isinstance(item, dict) and item.get('path') == relative]
    if len(matching) > 1:
        fail('PKB123', f'architecture map contains duplicate documentation entries for {relative}')
    registration = {
        'id': selection['selectionId'], 'path': relative,
        'sha256': hashlib.sha256(pretty_json(selection).encode('utf-8')).hexdigest(),
        'canonicalSha256': canonical_sha256(selection),
        'scope': 'Accepted building-block selection and exact consumer project assignment.',
    }
    if matching: documentation[documentation.index(matching[0])] = registration
    else: documentation.append(registration)
    result['documentation'] = sorted(documentation, key=lambda item: (str(item.get('path', '')).casefold(), str(item.get('id', ''))))
    return result


def accept_selection(
    repository: Path,
    selection_path: Path,
    catalog_path: Path,
    architecture_relative: str,
    decision_ids: list[str],
    rationale: str,
    program_kit_version: str,
) -> dict:
    selection = load_json(selection_path)
    if selection.get("status") != "Draft":
        fail("PKB122", f"only a Draft selection can be accepted; found {selection.get('status')!r}")
    if catalog_resolution_sha256(load_json(catalog_path)) != selection['catalog'].get('resolutionSha256'):
        catalog_path = consumer_catalog(repository, selection, catalog_path)
    catalog = load_json(catalog_path)
    validate_catalog(catalog)
    verify_catalog_binding(selection, catalog)
    selection["status"] = "Accepted"
    selection.pop("draftSuggestions", None)
    selection["catalog"] = catalog_binding(catalog)
    selection["authority"] = {
        "architectureMap": normalize_path(architecture_relative, "architecture map path"),
        # Preserve reviewed authority bytes across promotion: proof bindings
        # exclude lifecycle status, not changes to this selected design.
        "decisionIds": unique([require_id(item, "decision ID") for item in decision_ids], "decision IDs"),
        "rationale": rationale,
    }
    validate_selection(selection)
    verify_catalog_binding(selection, catalog)
    index_selection(selection)
    architecture_path = repository_path(repository, architecture_relative)
    architecture = load_json(architecture_path)
    decisions = {
        item.get("id"): item
        for item in require_list(architecture.get("decisions"), "architecture-map.decisions")
        if isinstance(item, dict)
    }
    for decision_id in selection["authority"]["decisionIds"]:
        decision = decisions.get(decision_id)
        if decision is None or decision.get("status") != "Accepted":
            fail("PKB123", f"architecture decision {decision_id!r} must already exist with Accepted status")
    architecture = registered_selection(repository, selection_path, selection, architecture)
    selection_text = pretty_json(selection)
    originals = {selection_path: selection_path.read_bytes(), architecture_path: architecture_path.read_bytes()}
    binding_path = repository / '.program-kit/dependency-profile.json'
    original_binding = binding_path.read_bytes() if binding_path.is_file() else None
    try:
        atomic_write(selection_path, selection_text)
        atomic_write(architecture_path, pretty_json(architecture))
        preserve_dependency_profile(repository, selection, catalog_path)
        return resolve(repository, selection_path, catalog_path, program_kit_version)
    except Exception:
        for path, content in originals.items():
            temporary = path.with_name(path.name + ".program-kit.rollback")
            temporary.write_bytes(content)
            temporary.replace(path)
        if original_binding is None: binding_path.unlink(missing_ok=True)
        else: atomic_write_bytes(binding_path, original_binding, 'profile-rollback')
        raise


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description="Resolve accepted Program Kit building-block selections.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    hash_parser = subparsers.add_parser("catalog-hash", help="Print the canonical resolution-affecting catalog SHA-256.")
    hash_parser.add_argument("--catalog")
    draft_parser = subparsers.add_parser("draft", help="Create a consumer-owned Draft selection without accepting decisions.")
    draft_parser.add_argument("--target", default=".")
    draft_parser.add_argument("--selection", default="docs/architecture/building-block-selection.json")
    draft_parser.add_argument("--catalog")
    draft_parser.add_argument('--profile', help='Qualified exact dependency profile; defaults to the registry default unless --catalog is explicit.')
    draft_parser.add_argument("--capability", action="append", default=[])
    accept_parser = subparsers.add_parser("accept", help="Bind a completed Draft to already Accepted architecture decisions.")
    accept_parser.add_argument("--target", default=".")
    accept_parser.add_argument("--selection", default="docs/architecture/building-block-selection.json")
    accept_parser.add_argument("--catalog")
    accept_parser.add_argument("--architecture-map", default="docs/architecture/architecture-map.json")
    accept_parser.add_argument("--decision-id", action="append")
    accept_parser.add_argument("--rationale")
    accept_parser.add_argument("--from-draft-authority", action="store_true")
    accept_parser.add_argument("--if-present", action="store_true")
    recover_parser = subparsers.add_parser("recover", help="Roll back an unfinished building-block transaction.")
    recover_parser.add_argument("--target", default=".")
    recover_parser.add_argument("--catalog")
    for name in ("validate-draft", "validate-accepted", "plan", "check", "apply"):
        command = subparsers.add_parser(name)
        command.add_argument("--target", default=".")
        command.add_argument("--selection", default="docs/architecture/building-block-selection.json")
        command.add_argument("--catalog")
        command.add_argument("--lock", default="eng/building-blocks.lock.json")
        if name in {"plan", "check", "apply"}:
            command.add_argument("--materialized-only", action="store_true",
                                 help="Reconcile only complete existing composition targets; keep future targets deferred.")
        if name in {"validate-draft", "validate-accepted"}:
            command.add_argument("--require-placement-provenance", action="store_true")
        if name == "apply":
            command.add_argument("--plan-digest", required=True)
    args = parser.parse_args()
    script = Path(__file__)
    catalog_path = Path(args.catalog).resolve() if getattr(args, "catalog", None) else default_catalog(script)
    try:
        catalog = load_json(catalog_path)
        validate_catalog(catalog)
        if args.command == "catalog-hash":
            print(catalog_resolution_sha256(catalog))
            return 0
        repository = Path(args.target).resolve()
        if args.command == "recover":
            recovered = recover_materialization(repository)
            print("Recovered building-block transactions: " + (", ".join(recovered) if recovered else "none"))
            return 0
        selection_path = repository / args.selection
        if args.command == "draft":
            if args.profile or not args.catalog:
                draft_qualified_selection(repository, selection_path, catalog, args.capability, args.profile)
            else:
                draft_selection(repository, selection_path, catalog, args.capability)
            print(f"Created Draft building-block selection for consumer review: {selection_path}")
            return 0
        if args.command == "accept":
            if not selection_path.is_file() and args.if_present:
                print("No Draft building-block selection is present; acceptance is not applicable.")
                return 0
            draft = load_json(selection_path)
            if args.from_draft_authority:
                authority = require_object(draft.get("authority"), "draft selection authority")
                decision_ids = authority.get("decisionIds")
                rationale = authority.get("rationale")
            else:
                decision_ids = args.decision_id
                rationale = args.rationale
            if not isinstance(decision_ids, list) or not decision_ids or not isinstance(rationale, str) or not rationale.strip():
                fail("PKB122", "accept requires decision IDs and rationale, explicitly or from Draft authority")
            lock = accept_selection(
                repository,
                selection_path,
                catalog_path,
                args.architecture_map,
                decision_ids,
                rationale,
                find_program_kit_version(script),
            )
            print(f"Accepted selection; review materialization plan digest {lock['planDigest']} before apply.")
            return 0
        lock_path = repository / args.lock
        catalog_path = consumer_catalog(repository, load_json(selection_path), catalog_path)
        catalog = load_json(catalog_path)
        lock = resolve(
            repository,
            selection_path,
            catalog_path,
            find_program_kit_version(script),
            require_accepted=args.command != "validate-draft",
        )
        scoped = getattr(args, "materialized_only", False)
        if args.command in {"plan", "check", "apply"} and lock_path.is_file():
            scoped = scoped or load_json(lock_path).get("materializationScope") == "existing-compositions"
        if scoped:
            lock = materialized_plan(repository, lock)
        if args.command == "validate-draft":
            validate_placements(repository, load_json(selection_path), args.require_placement_provenance)
            print(f"Draft building-block selection is complete and resolves provisionally: {lock['planDigest']}")
            return 0
        if args.command == "validate-accepted":
            validate_placements(repository, load_json(selection_path), args.require_placement_provenance)
            print(f"Accepted building-block selection resolves with current authority: {lock['planDigest']}")
            return 0
        if args.command == "plan":
            print(pretty_json(lock), end="")
            return 0
        if args.command == "check":
            if not lock_path.is_file():
                fail("PKB400", f"generated building-block lock is missing: {lock_path}")
            actual = load_json(lock_path)
            if actual != lock:
                fail("PKB401", f"generated building-block lock is stale or manually altered: {lock_path}")
            check_materialization(repository, actual)
            audit_unmanaged_dependencies(repository, catalog, actual)
            print(f"Building-block selection and lock are current: {lock['planDigest']}")
            return 0
        if args.plan_digest != lock["planDigest"]:
            fail("PKB500", f"reviewed plan digest {args.plan_digest!r} does not match current plan {lock['planDigest']!r}")
        transaction_id = apply_materialization(repository, lock_path, lock, catalog)
        print(f"Materialized accepted building-block plan and lock in transaction {transaction_id}: {lock_path}")
        return 0
    except ResolverError as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
