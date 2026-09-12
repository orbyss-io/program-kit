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


@dataclass(frozen=True)
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
            key: {"releaseVersion": family.get("releaseVersion")}
            for key, family in sorted(require_object(catalog.get("families"), "catalog.families").items())
        },
        "packages": packages,
        "capabilities": copy.deepcopy(catalog.get("capabilities")),
        "compositions": compositions,
    }


def catalog_resolution_sha256(catalog: dict) -> str:
    return canonical_sha256(resolution_projection(catalog))


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


def validate_placements(repository: Path, selection: dict, require_all: bool = False) -> None:
    """Validate architecture declarations without creating their consumer-owned files.

    Legacy accepted selections remain readable. New bootstrap Drafts require provenance on
    every target; a declaration stays 'planned' after scaffolding as its decision-time origin.
    The map's source hashes provide freshness without duplicating ADR hashes across approval.
    """
    _, targets = index_selection(selection)
    declared = [target for target in targets.values() if "placement" in target]
    if require_all and (not targets or len(declared) != len(targets)):
        fail("PKB306", "architecture must declare placement provenance for every target")
    if require_all and not selection.get("instances"):
        fail("PKB306", "architecture must declare composition instances and their bindings")
    if not declared:
        return
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
        name = path.name.casefold()
        valid_kind = {
            "repository": name == "directory.build.props",
            "dotnet-project": name.endswith(".csproj"),
            "npm-package": name == "package.json",
            "cshell-shell": name == "shells.json",
            "dotnet-tool-manifest": name == "dotnet-tools.json",
            "host-image": name == "dockerfile" or name.startswith("dockerfile."),
        }.get(target.get("kind"), False)
        if not valid_kind:
            fail("PKB303", f"{label} path does not match its target kind")
        if target["kind"] == "cshell-shell":
            require_id(target.get("shell"), f"{label} shell")


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
    catalog = load_json(catalog_path)
    selection = load_json(selection_path)
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

    def assign(package_key: str, target: dict, origin: str, instance: dict, active: set[tuple[str, str]]) -> None:
        package = packages[package_key]
        materialization = package["materialization"]
        if target.get("kind") not in materialization["allowedTargetKinds"]:
            fail("PKB303", f"{origin} cannot place {package_key} in target kind {target.get('kind')!r}")
        if target.get("role") not in materialization["allowedRoles"]:
            fail("PKB303", f"{origin} cannot place {package_key} in target role {target.get('role')!r}")
        environment = scopes[target["scope"]]["environment"]
        allowed_environments = materialization.get("allowedEnvironments")
        if allowed_environments and environment not in allowed_environments:
            fail("PKB304", f"{origin} cannot place {package_key} in {environment!r} scope {target['scope']!r}")
        identity = (package_key, target["id"])
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
                assign(requirement["package"], companion_target, f"{origin}/requires/{requirement['package']}", instance, active)
        for activation in package.get("activations", []):
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
        active: set[tuple[str, str]] = set()
        origin_packages: list[str] = []
        for requirement in requirements:
            origin = f"{instance_id}/{requirement['package']}"
            for target in binding_targets(instance, requirement["targetSlot"], targets):
                assign(requirement["package"], target, origin, instance, active)
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
        outputs.append(output_record("nuget-central-pins", ".program-kit/eng/ProgramKit.BuildingBlocks.props", entries))
    for path, routes in npm_routing.items():
        outputs.append(output_record("npm-registry-routing", path, [routes[key] for key in sorted(routes)]))
    for activation in lock["activations"]:
        shell_parent = PurePosixPath(activation["path"]).parent
        overlay_path = (shell_parent / ".program-kit/building-blocks.shells.json").as_posix()
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


def repository_files(repository: Path, pattern: str) -> list[Path]:
    ignored = {".git", ".specify", "artifacts", "node_modules", "bin", "obj"}
    return sorted(
        path
        for path in repository.rglob(pattern)
        if not any(part in ignored for part in path.relative_to(repository).parts)
    )


def audit_unmanaged_dependencies(repository: Path, catalog: dict, ownership_lock: dict | None) -> None:
    owned = output_map(ownership_lock or {})
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
        if relative == ".program-kit/eng/ProgramKit.Packages.props":
            continue
        for package_id in version_pattern.findall(read_text(path)):
            if package_id.casefold() in nuget_ids:
                findings.append(f"unmanaged NuGet pin {package_id} in {relative}")
    for path in repository_files(repository, "package.json"):
        relative = path.relative_to(repository).as_posix()
        value = load_json(path)
        prior = owned.get(relative)
        previous_entries = prior["entries"] if prior and prior["kind"] == "npm-package" else []
        previous_ids = {entry["packageId"] for entry in previous_entries}
        for section_name in ("dependencies", "devDependencies"):
            section = value.get(section_name, {})
            if not isinstance(section, dict):
                fail("PKB405", f"{relative} {section_name} must be an object")
            for package_id in section:
                if package_id in npm_ids and package_id not in previous_ids:
                    findings.append(f"unmanaged npm dependency {package_id} in {relative}")
    for path in repository_files(repository, "dotnet-tools.json"):
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
    audit_unmanaged_dependencies(repository, catalog, previous_lock)
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
    audit_unmanaged_dependencies(repository, catalog, lock)
    return transaction_id


def find_program_kit_version(script: Path) -> str:
    for parent in script.resolve().parents:
        candidate = parent / "VERSION"
        if candidate.is_file():
            value = candidate.read_text(encoding="utf-8").strip()
            if value:
                return value
    return "0.10.2"


def default_catalog(script: Path) -> Path:
    return script.resolve().parents[1] / "references" / "orbyss-building-blocks.json"


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
    catalog = load_json(catalog_path)
    validate_catalog(catalog)
    selection["status"] = "Accepted"
    selection.pop("draftSuggestions", None)
    selection["catalog"] = catalog_binding(catalog)
    selection["authority"] = {
        "architectureMap": normalize_path(architecture_relative, "architecture map path"),
        "decisionIds": sorted(unique([require_id(item, "decision ID") for item in decision_ids], "decision IDs")),
        "rationale": rationale.strip(),
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
    try:
        selection_relative = selection_path.resolve().relative_to(repository.resolve()).as_posix()
    except ValueError:
        fail("PKB300", f"selection path escapes the repository: {selection_path}")
    documentation = require_list(architecture.get("documentation"), "architecture-map.documentation")
    matching = [item for item in documentation if isinstance(item, dict) and item.get("path") == selection_relative]
    if len(matching) > 1:
        fail("PKB123", f"architecture map contains duplicate documentation entries for {selection_relative}")
    selection_text = pretty_json(selection)
    registration = {
        "id": selection["selectionId"],
        "path": selection_relative,
        "sha256": hashlib.sha256(selection_text.encode("utf-8")).hexdigest(),
        "canonicalSha256": canonical_sha256(selection),
        "scope": "Accepted building-block selection and exact consumer project assignment.",
    }
    if matching:
        documentation[documentation.index(matching[0])] = registration
    else:
        documentation.append(registration)
    architecture["documentation"] = sorted(documentation, key=lambda item: (str(item.get("path", "")).casefold(), str(item.get("id", ""))))
    originals = {selection_path: selection_path.read_bytes(), architecture_path: architecture_path.read_bytes()}
    try:
        atomic_write(selection_path, selection_text)
        atomic_write(architecture_path, pretty_json(architecture))
        return resolve(repository, selection_path, catalog_path, program_kit_version)
    except Exception:
        for path, content in originals.items():
            temporary = path.with_name(path.name + ".program-kit.rollback")
            temporary.write_bytes(content)
            temporary.replace(path)
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
        command.add_argument("--lock", default=".program-kit/building-blocks.lock.json")
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
        lock = resolve(
            repository,
            selection_path,
            catalog_path,
            find_program_kit_version(script),
            require_accepted=args.command != "validate-draft",
        )
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
