from __future__ import annotations

import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .common import LiveContractError, atomic_write_json, canonical_sha256, file_inventory, load_object, safe_relative, sha256_file, utc_now, validate
from .evidence import EvidenceStore


def seal_checkpoint(
    store: EvidenceStore,
    project: Path,
    checkpoint_schema: dict[str, Any],
    *,
    phase: str,
    candidate_digest: str,
    scenario_digest: str,
    expectation_digest: str,
    selection_sha256: str,
    parent: str | None = None,
) -> tuple[Path, dict[str, Any]]:
    architecture = project / "docs/architecture/architecture-map.json"
    if not architecture.is_file():
        raise LiveContractError("LIVE_CHECKPOINT_ARCHITECTURE_MAP_MISSING")
    inventory = file_inventory(project)
    for record in inventory:
        stored = store.put_file(project / safe_relative(str(record["path"])))
        if stored["sha256"] != record["sha256"] or stored["size"] != record["size"]:
            raise LiveContractError("LIVE_CHECKPOINT_OBJECT_MISMATCH")
    identifier = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{phase}-{uuid.uuid4().hex[:8]}"
    manifest = {
        "schemaVersion": "2.0",
        "status": "checkpoint-created",
        "checkpointId": identifier,
        "phase": phase,
        "parent": parent,
        "candidate": candidate_digest,
        "scenario": scenario_digest,
        "expectation": expectation_digest,
        "architectureMapSha256": sha256_file(architecture),
        "selectionSha256": selection_sha256,
        "files": inventory,
        "createdAt": utc_now(),
    }
    validate(manifest, checkpoint_schema)
    destination = store.checkpoints / f"{identifier}.json"
    atomic_write_json(destination, manifest)
    return destination, manifest


def checkpoint_digest(path: Path) -> str:
    return sha256_file(path)


def materialize_checkpoint(
    store: EvidenceStore,
    manifest_path: Path,
    destination: Path,
    checkpoint_schema: dict[str, Any],
) -> dict[str, Any]:
    manifest = load_object(manifest_path)
    validate(manifest, checkpoint_schema)
    if (manifest["phase"] == "bootstrap-checkpoint") != (manifest["parent"] is None):
        raise LiveContractError("LIVE_CHECKPOINT_PARENT_CONTRACT_INVALID")
    if destination.exists():
        raise LiveContractError(f"LIVE_CHECKPOINT_DESTINATION_EXISTS: {destination}")
    destination.mkdir(parents=True)
    for record in manifest["files"]:
        relative = safe_relative(record["path"])
        source = store.objects / record["sha256"]
        if not source.is_file() or sha256_file(source) != record["sha256"]:
            raise LiveContractError(f"LIVE_CHECKPOINT_OBJECT_MISSING_OR_CORRUPT: {record['sha256']}")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        if sha256_file(target) != record["sha256"]:
            raise LiveContractError(f"LIVE_CHECKPOINT_COPY_MISMATCH: {relative}")
    if file_inventory(destination) != manifest["files"]:
        raise LiveContractError("LIVE_CHECKPOINT_INVENTORY_MISMATCH")
    if sha256_file(destination / "docs/architecture/architecture-map.json") != manifest["architectureMapSha256"]:
        raise LiveContractError("LIVE_CHECKPOINT_ARCHITECTURE_HASH_MISMATCH")
    if sha256_file(destination / "docs/architecture/building-block-selection.json") != manifest["selectionSha256"]:
        raise LiveContractError("LIVE_CHECKPOINT_SELECTION_HASH_MISMATCH")
    return manifest
