from __future__ import annotations

import json
import copy
import hashlib
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path


PRODUCER_KIND = "Orbyss.Foundation.OpenApi.Exporter"
PLANNING_NAMES = ("spec.md", "plan.md", "tasks.md", "research.md", "quickstart.md", "data-model.md")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:-preview\.\d+)?$")
EXPORTER_KEY = "nuget:" + PRODUCER_KIND
CATALOG_RELATIVE = "extensions/program-kit-building-blocks/references/orbyss-building-blocks.json"


# The historical exporter-only catalog bridge retains its bounded authority.
# Producer-contract/planning reconciliation is shared with reviewed profile transitions.
import importlib.util
import sys

_shared_path = Path(__file__).resolve().parents[1] / 'extensions/program-kit-building-blocks/scripts/producer_reconciliation.py'
_spec = importlib.util.spec_from_file_location('program_kit_producer_reconciliation', _shared_path)
_shared = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _shared
_spec.loader.exec_module(_shared)
ReconciliationError = _shared.ReconciliationError
normalize_path = _shared.normalize_path
relative_path = _shared.relative_path
target_exporter_version = _shared.target_exporter_version
registered_contracts = _shared.registered_contracts
manifest_contract_paths = _shared.manifest_contract_paths
utc_now = _shared.utc_now
feature_identity = _shared.feature_identity
version_key = _shared.version_key
reconcile_planning_text = _shared.reconcile_planning_text
discover = _shared.discover
describe = _shared.describe
json_bytes = _shared.json_bytes
invalidated_state = _shared.invalidated_state
atomic_replace = _shared.atomic_replace
apply = _shared.apply


def catalog_transition(target: Path, release: Path, resolver, selection: dict) -> dict:
    """Admit only the reviewed exporter tool pin; retain all consumer design choices."""
    new = resolver.load_json(release / CATALOG_RELATIVE)
    new_hash = resolver.catalog_resolution_sha256(new)
    old_hash = selection.get("catalog", {}).get("resolutionSha256")
    if not isinstance(old_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", old_hash):
        raise ReconciliationError("PKU116 accepted catalog hash is malformed")
    archive = target / ".program-kit/selection-history" / f"exporter-{old_hash}-{new_hash}"
    seal = archive / 'originals.json'
    if archive.exists():
        try:
            record = resolver.load_json(seal)
            if record['fromHash'] != old_hash or record['toHash'] != new_hash:
                raise ValueError('catalog binding differs')
            for name, expected_hash in record['files'].items():
                if name not in {'catalog.json', 'selection.json', 'architecture.json', 'lock.json', 'governance-extension.yml'}:
                    raise ValueError('unknown archive entry')
                if hashlib.sha256((archive / name).read_bytes()).hexdigest() != expected_hash:
                    raise ValueError('archive hash differs: ' + name)
            if not {'catalog.json', 'selection.json', 'architecture.json', 'governance-extension.yml'} <= record['files'].keys():
                raise ValueError('archive is incomplete')
        except (OSError, KeyError, TypeError, ValueError) as error:
            raise ReconciliationError('PKU116 preserved exporter transition is incomplete or changed: ' + str(error)) from error
    installed = target / ".specify" / CATALOG_RELATIVE
    version_path = target / ".specify/extensions/program-kit-governance/extension.yml"
    old_path = installed
    old = resolver.load_json(old_path)
    if resolver.catalog_resolution_sha256(old) != old_hash:
        # An interrupted sequential installer may already have installed the new
        # catalog. Only its preserved exact old catalog can resume this transition.
        if resolver.catalog_resolution_sha256(old) != new_hash:
            raise ReconciliationError("PKU116 installed catalog cannot resume exporter reconciliation")
        old_path = archive / "catalog.json"
        version_path = archive / "governance-extension.yml"
        old = resolver.load_json(old_path)
    resolver.validate_catalog(old)
    resolver.validate_catalog(new)
    if resolver.catalog_resolution_sha256(old) != old_hash:
        raise ReconciliationError("PKU116 preserved catalog does not match accepted selection")
    before = resolver.resolution_projection(old)
    after = resolver.resolution_projection(new)
    old_version = before["packages"][EXPORTER_KEY]["version"]
    new_version = after["packages"][EXPORTER_KEY]["version"]
    if (version_key(old_version) >= version_key(new_version)
            or new_version != target_exporter_version(release)):
        raise ReconciliationError("PKU116 exporter catalog and managed tool must advance together")
    expected = copy.deepcopy(before)
    expected["resolutionRevision"] += 1
    expected["packages"][EXPORTER_KEY]["version"] = new_version
    family = expected["packages"][EXPORTER_KEY]["family"]
    expected["families"][family].setdefault("toolVersions", {})[PRODUCER_KIND] = new_version
    if after != expected:
        raise ReconciliationError("PKU116 catalog changes exceed the exporter-only transition; renew architecture acceptance")
    architecture_path = target / selection["authority"]["architectureMap"]
    relative_path(target, architecture_path)
    paths = {"selection.json": target / "docs/architecture/building-block-selection.json",
             "architecture.json": architecture_path,
             "catalog.json": old_path, "governance-extension.yml": version_path}
    version_match = re.search(r"^\s{2}version:\s*[\"']?([^\"'#\s]+)",
                              version_path.read_text(encoding="utf-8"), re.MULTILINE)
    if version_match is None:
        raise ReconciliationError("PKU116 prior exporter transition installation version is missing")
    lock = target / ".program-kit/building-blocks.lock.json"
    if lock.is_file():
        paths["lock.json"] = lock
    return {"archive": archive, "oldCatalog": old_path, "paths": paths,
            "originals": {name: path.read_bytes() for name, path in paths.items()},
            "fromVersion": old_version, "toVersion": new_version,
            "fromHash": old_hash, "toHash": new_hash, "previousInstalledVersion": version_match.group(1)}


def archive_catalog_transition(plan: dict) -> None:
    archive = plan["archive"]
    archive.mkdir(parents=True, exist_ok=True)
    for name, data in plan["originals"].items():
        path = archive / name
        if path.exists():
            if path.read_bytes() != data:
                raise ReconciliationError(f"PKU116 preserved exporter transition evidence changed: {path}")
        else:
            with path.open("xb") as handle:
                handle.write(data)
    seal = {'schemaVersion': 1, 'fromHash': plan['fromHash'], 'toHash': plan['toHash'],
            'files': {name: hashlib.sha256(data).hexdigest() for name, data in plan['originals'].items()}}
    seal_path = archive / 'originals.json'
    if seal_path.exists():
        if json.loads(seal_path.read_text(encoding='utf-8')) != seal:
            raise ReconciliationError('PKU116 preserved exporter transition seal changed')
    else:
        with tempfile.NamedTemporaryFile(dir=archive, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(json_bytes(seal))
        try:
            os.replace(temporary, seal_path)
        finally:
            temporary.unlink(missing_ok=True)


def apply_catalog_transition(target: Path, release: Path, plan: dict, resolver, version: str) -> None:
    selection_path = target / "docs/architecture/building-block-selection.json"
    original = plan["originals"]["selection.json"]
    if selection_path.read_bytes() != original:
        raise ReconciliationError("PKU116 accepted selection changed during exporter upgrade")
    if plan["paths"]["architecture.json"].read_bytes() != plan["originals"]["architecture.json"]:
        raise ReconciliationError("PKU116 architecture authority changed during exporter upgrade")
    selection = json.loads(original)
    authority = selection["authority"]
    draft = copy.deepcopy(selection)
    draft["status"] = "Draft"
    draft["revision"] += 1
    draft["catalog"] = resolver.catalog_binding(resolver.load_json(release / CATALOG_RELATIVE))
    try:
        atomic_replace({selection_path: json_bytes(draft)})
        resolver.accept_selection(target, selection_path, release / CATALOG_RELATIVE,
                                  authority["architectureMap"], authority["decisionIds"], authority["rationale"], version)
    except Exception:
        atomic_replace({selection_path: original})
        raise
    record = {"schemaVersion": 1, "reason": "program-kit-openapi-producer-pin-reconciliation",
              "fromResolutionSha256": plan["fromHash"], "toResolutionSha256": plan["toHash"],
              "fromExporterVersion": plan["fromVersion"], "toExporterVersion": plan["toVersion"],
              "historicalFiles": {name: hashlib.sha256(data).hexdigest() for name, data in plan["originals"].items()},
              "acceptedSelectionSha256": hashlib.sha256(selection_path.read_bytes()).hexdigest()}
    path = plan["archive"] / "transition.json"
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(record, indent=2) + "\n")
    resolver.preserve_dependency_profile(target, resolver.load_json(selection_path), release / CATALOG_RELATIVE)
