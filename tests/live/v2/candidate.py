from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from live.run_bootstrap_acceptance import prepare_local_catalog_server, safe_extract, specify_bridge_command

from .common import LiveContractError, load_object, safe_relative, sha256_file, validate
from .supervisor import ProcessResult, run_supervised


CONTROL_ARCHIVE_KEYS = ("workflow", "bundle")


def validate_release_receipt(root: Path, receipt_path: Path, schema: dict[str, Any]) -> tuple[dict[str, Any], str]:
    receipt = load_object(receipt_path)
    validate(receipt, schema)
    receipt_digest = sha256_file(receipt_path)
    for record in receipt["artifacts"]:
        relative = safe_relative(record["path"])
        artifact = root / relative
        if not artifact.is_file() or artifact.stat().st_size != record["size"] or sha256_file(artifact) != record["sha256"]:
            raise LiveContractError(f"LIVE_CANDIDATE_ARTIFACT_MISMATCH: {relative}")
    availability = root / "artifacts/building-block-public-availability.json"
    if not availability.is_file() or sha256_file(availability) != receipt["catalog"]["availabilityEvidenceSha256"]:
        raise LiveContractError("LIVE_CANDIDATE_AVAILABILITY_EVIDENCE_MISMATCH")
    catalog_result = subprocess.run(
        [sys.executable, str(root / "extensions/program-kit-building-blocks/scripts/building_blocks.py"), "catalog-hash"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if catalog_result.returncode != 0 or catalog_result.stdout.strip() != receipt["catalog"]["sha256"]:
        raise LiveContractError("LIVE_CANDIDATE_CATALOG_MISMATCH")
    return receipt, receipt_digest


def _setup_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for key in ("PROGRAM_KIT_NPM_TOKEN", "NPM_TOKEN", "NODE_AUTH_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        environment.pop(key, None)
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    return environment


def retryable_catalog_transfer(output: str) -> bool:
    return (
        re.search(r"Failed to save extension\s+archive", output) is not None
        and "No changes were recorded" in output
    )


def _run_setup(command: list[str], cwd: Path, evidence: Path, index: int) -> ProcessResult:
    for attempt in range(1, 4):
        attempt_name = f"setup-{index:02d}" if attempt == 1 else f"setup-{index:02d}-retry-{attempt}"
        attempt_evidence = evidence / attempt_name
        result = run_supervised(
            command,
            cwd=cwd,
            environment=_setup_environment(),
            evidence_directory=attempt_evidence,
            timeout_seconds=600,
        )
        if result.exitCode == 0 and result.cleanupComplete and result.logsDrained:
            return result
        output = "\n".join(
            (attempt_evidence / name).read_text(encoding="utf-8", errors="replace")
            for name in ("workflow.stdout.log", "workflow.stderr.log")
        )
        if not retryable_catalog_transfer(output) or attempt == 3:
            raise LiveContractError(
                f"LIVE_CANDIDATE_SETUP_FAILED: {command[0]} exited {result.exitCode}"
            )
    raise LiveContractError("LIVE_CANDIDATE_SETUP_RETRY_EXHAUSTED")


def extract_candidate_control_archives(
    artifacts: Path,
    packages: Path,
    names: dict[str, str],
) -> None:
    for key in CONTROL_ARCHIVE_KEYS:
        safe_extract(artifacts / names[key], packages / key)


def install_candidate_from_receipt(
    root: Path,
    project: Path,
    packages: Path,
    receipt: dict[str, Any],
    evidence: Path,
) -> list[dict[str, object]]:
    version = receipt["version"]
    artifacts = root / "artifacts"
    names = {
        "governance": f"program-kit-governance-{version}.zip",
        "building-blocks": f"program-kit-building-blocks-{version}.zip",
        "dotnet": f"program-kit-dotnet-{version}.zip",
        "preset": f"program-kit-governance-preset-{version}.zip",
        "workflow": f"program-kit-bootstrap-{version}.zip",
        "bundle": f"program-kit-{version}.zip",
    }
    listed = {Path(record["path"]).name: record for record in receipt["artifacts"]}
    for name in names.values():
        if name not in listed:
            raise LiveContractError(f"LIVE_CANDIDATE_RECEIPT_ARCHIVE_MISSING: {name}")
    extract_candidate_control_archives(artifacts, packages, names)
    receipts: list[dict[str, object]] = []
    commands = [
        ["git", "init"],
        specify_bridge_command(root, "init", ".", "--force", "--non-interactive", "--integration", "codex", "--script", "py", "--ignore-agent-tools"),
    ]
    for index, command in enumerate(commands, 1):
        receipts.append(_run_setup(command, project, evidence, index).as_dict())
    server, thread, base_url = prepare_local_catalog_server(root, artifacts, packages, evidence, version)
    catalog_commands = [
        specify_bridge_command(root, "extension", "catalog", "add", f"{base_url}/extensions.json", "--name", "program-kit-live-candidate", "--priority", "1", "--install-allowed", loopback_http_only=os.name == "nt"),
        specify_bridge_command(root, "preset", "catalog", "add", f"{base_url}/presets.json", "--name", "program-kit-live-candidate", "--priority", "1", "--install-allowed", loopback_http_only=os.name == "nt"),
        specify_bridge_command(root, "workflow", "catalog", "add", f"{base_url}/workflows.json", "--name", "program-kit-live-candidate", loopback_http_only=os.name == "nt"),
        specify_bridge_command(root, "workflow", "add", "program-kit-bootstrap", loopback_http_only=os.name == "nt"),
        specify_bridge_command(root, "bundle", "install", str(packages / "bundle/bundle.yml"), "--integration", "codex", loopback_http_only=os.name == "nt"),
    ]
    try:
        for offset, command in enumerate(catalog_commands, len(commands) + 1):
            receipts.append(_run_setup(command, project, evidence, offset).as_dict())
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)
    return receipts
