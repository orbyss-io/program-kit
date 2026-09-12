from __future__ import annotations

import secrets
import os
import shutil
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .common import LiveContractError, atomic_write_json, canonical_sha256, load_object, utc_now, validate


SESSION_LIMITS = {"bootstrap-checkpoint": 7, "building-block-consumer": 1,
                  "workflow-fresh": 8, "workflow-failure": 8, "workflow-resume": 8}
PHASES = set(SESSION_LIMITS)


def issue_authorization(
    destination: Path,
    schema: dict[str, Any],
    *,
    phase: str,
    scenario: dict[str, str],
    candidate: dict[str, str],
    agent_profile: dict[str, object],
    checkpoint: dict[str, str] | None,
    expires_minutes: int = 30,
    workflow: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if phase not in PHASES:
        raise LiveContractError(f"LIVE_AUTHORIZATION_UNKNOWN_PHASE: {phase}")
    if phase == "building-block-consumer" and checkpoint is None:
        raise LiveContractError("LIVE_AUTHORIZATION_CHECKPOINT_REQUIRED")
    if phase == "bootstrap-checkpoint" and checkpoint is not None:
        raise LiveContractError("LIVE_AUTHORIZATION_CHECKPOINT_FORBIDDEN")
    if phase.startswith('workflow-'):
        if workflow is None:
            raise LiveContractError('LIVE_AUTHORIZATION_WORKFLOW_BINDING_REQUIRED')
        if (phase == 'workflow-resume') != (checkpoint is not None):
            raise LiveContractError('LIVE_AUTHORIZATION_WORKFLOW_PARENT_MISMATCH')
    elif workflow is not None:
        raise LiveContractError('LIVE_AUTHORIZATION_WORKFLOW_BINDING_FORBIDDEN')
    now = datetime.now(timezone.utc)
    manifest: dict[str, Any] = {
        "schemaVersion": "2.0",
        "authorizationId": str(uuid.uuid4()),
        "nonce": secrets.token_hex(32),
        "phase": phase,
        "scenario": scenario,
        "candidate": candidate,
        "checkpoint": checkpoint,
        "agentProfile": agent_profile,
        "limits": {
            "maximumPaidSessions": SESSION_LIMITS[phase],
            "workerNetwork": "model-transport-only",
            "restoreNetworkOwner": "supervisor",
        },
        "issuedAt": now.isoformat(),
        "expiresAt": (now + timedelta(minutes=expires_minutes)).isoformat(),
    }
    if workflow is not None:
        manifest['workflow'] = workflow
    validate(manifest, schema)
    atomic_write_json(destination, manifest)
    return manifest


def _parse_time(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise LiveContractError(f"LIVE_AUTHORIZATION_INVALID_TIME: {label}")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as error:
        raise LiveContractError(f"LIVE_AUTHORIZATION_INVALID_TIME: {label}") from error
    if parsed.tzinfo is None:
        raise LiveContractError(f"LIVE_AUTHORIZATION_TIMEZONE_REQUIRED: {label}")
    return parsed


def validate_authorization(
    path: Path,
    schema: dict[str, Any],
    *,
    phase: str,
    scenario_digest: str,
    candidate_receipt_digest: str,
    checkpoint_digest: str | None,
) -> dict[str, Any]:
    manifest = load_object(path)
    validate(manifest, schema)
    if manifest["phase"] != phase:
        raise LiveContractError("LIVE_AUTHORIZATION_PHASE_MISMATCH")
    if manifest["scenario"]["digest"] != scenario_digest:
        raise LiveContractError("LIVE_AUTHORIZATION_SCENARIO_MISMATCH")
    if manifest["candidate"]["releaseReceiptSha256"] != candidate_receipt_digest:
        raise LiveContractError("LIVE_AUTHORIZATION_CANDIDATE_MISMATCH")
    actual_checkpoint = manifest.get("checkpoint")
    if checkpoint_digest is None:
        if actual_checkpoint is not None:
            raise LiveContractError("LIVE_AUTHORIZATION_CHECKPOINT_MISMATCH")
    elif not isinstance(actual_checkpoint, dict) or actual_checkpoint.get("digest") != checkpoint_digest:
        raise LiveContractError("LIVE_AUTHORIZATION_CHECKPOINT_MISMATCH")
    now = datetime.now(timezone.utc)
    if now < _parse_time(manifest["issuedAt"], "issuedAt") or now >= _parse_time(manifest["expiresAt"], "expiresAt"):
        raise LiveContractError("LIVE_AUTHORIZATION_EXPIRED")
    expected_sessions = SESSION_LIMITS[phase]
    if manifest["limits"]["maximumPaidSessions"] != expected_sessions:
        raise LiveContractError("LIVE_AUTHORIZATION_SESSION_LIMIT")
    return manifest


def consume_authorization(path: Path, manifest: dict[str, Any], consumed_directory: Path) -> dict[str, Any]:
    expected_digest = canonical_sha256(manifest)
    consumed_directory.mkdir(parents=True, exist_ok=True)
    consumed_manifest = consumed_directory / f"{manifest['authorizationId']}.json"
    claim = consumed_directory / f"{manifest['authorizationId']}.claim"
    if consumed_manifest.exists() or claim.exists() or not path.is_file():
        raise LiveContractError("LIVE_AUTHORIZATION_REPLAYED")
    try:
        descriptor = os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise LiveContractError("LIVE_AUTHORIZATION_REPLAYED") from error
    with os.fdopen(descriptor, "w", encoding="ascii", newline="\n") as handle:
        handle.write(expected_digest + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    current = load_object(path)
    if canonical_sha256(current) != expected_digest:
        raise LiveContractError("LIVE_AUTHORIZATION_CHANGED_BEFORE_CONSUMPTION")
    try:
        shutil.copyfile(path, consumed_manifest)
        path.unlink()
    except OSError as error:
        consumed_manifest.unlink(missing_ok=True)
        raise LiveContractError(f"LIVE_AUTHORIZATION_CONSUMPTION_FAILED: {error}") from error
    receipt = {
        "schemaVersion": "2.0",
        "authorizationId": manifest["authorizationId"],
        "authorizationSha256": expected_digest,
        "consumedAt": utc_now(),
    }
    atomic_write_json(consumed_directory / f"{manifest['authorizationId']}.consumption.json", receipt)
    return receipt
