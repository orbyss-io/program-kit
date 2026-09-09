from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from live.v2.authorization import consume_authorization, issue_authorization, validate_authorization
from live.v2.candidate import (
    CONTROL_ARCHIVE_KEYS,
    extract_candidate_control_archives,
    retryable_catalog_transfer,
)
from live.v2.checkpoint import materialize_checkpoint, seal_checkpoint
from live.v2.cli import (
    process_failure,
    candidate_packages,
    execution_workspace,
    supervisor_environment,
    validate_agent_launcher,
    validate_toolchain_binding,
    worker_environment,
)
from live.v2.common import LiveContractError, atomic_write_json, load_object, sha256_file, validate
from live.v2.evidence import EvidenceStore
from live.v2.redaction import StreamingRedactor
from live.v2.scenario import bind_selection, load_scenario, scenario_authority
from live.v2.supervisor import run_supervised
from live.v2.validation import validate_consumer
from live.run_bootstrap_acceptance import specify_bridge_command


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "tests/live/schemas/v2"
SCENARIO = ROOT / "tests/live/scenarios/internal-forms-workspace/v1"
CATALOG = ROOT / "extensions/program-kit-building-blocks/references/orbyss-building-blocks.json"
RESOLVER = ROOT / "extensions/program-kit-building-blocks/scripts/building_blocks.py"
RESTORE = ROOT / "extensions/program-kit-building-blocks/scripts/restore_dependencies.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def expect_contract_error(action, code: str) -> None:
    try:
        action()
    except LiveContractError as error:
        if code not in str(error):
            raise AssertionError(f"Expected {code}, received {error}") from error
        return
    raise AssertionError(f"Expected {code}")


def main() -> int:
    required = [
        ROOT / "scripts/New-LiveAcceptanceAuthorization.ps1",
        ROOT / "scripts/New-LiveBootstrapCheckpoint.ps1",
        ROOT / "scripts/Test-LiveBuildingBlockConsumer.ps1",
        ROOT / "scripts/write_release_receipt.py",
        ROOT / "docs/live-bootstrap-acceptance.md",
        *SCHEMAS.glob("*.schema.json"),
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise AssertionError(f"Live v2 components are missing: {missing}")
    issuer_text = (ROOT / "scripts/New-LiveAcceptanceAuthorization.ps1").read_text(encoding="utf-8")
    if "^codex-cli\\s+\\S+" not in issuer_text or "--launcher-version" not in issuer_text:
        raise AssertionError("Interactive authorization no longer displays and binds the actual Codex launcher version")
    scenario, expectation, expectation_path = load_scenario(SCENARIO, SCHEMAS)
    authority = scenario_authority(SCENARIO, SCHEMAS)
    if expectation["catalogSha256"] != "8017cec0be489e5a76c0a6a75a383f5785cdcfabaf358a322d18d20e3116539d":
        raise AssertionError("Internal Forms expectation lost its reviewed catalog binding")

    resolver = load_module("live_v2_building_blocks", RESOLVER)
    catalog = load_object(CATALOG)
    if resolver.catalog_resolution_sha256(catalog) != expectation["catalogSha256"]:
        raise AssertionError("Candidate expectation is stale relative to the catalog")
    restore = load_module("live_v2_restore", RESTORE)
    receipt_writer = load_module("live_v2_release_receipt", ROOT / "scripts/write_release_receipt.py")

    transient_catalog_error = (
        "Failed to save extension archive: [WinError 10054] connection reset. "
        "No changes were recorded."
    )
    if not retryable_catalog_transfer(transient_catalog_error):
        raise AssertionError("Known atomic loopback catalog reset is no longer retryable")
    if retryable_catalog_transfer("Failed to install bundle after partial changes"):
        raise AssertionError("Unsafe catalog failure became retryable")

    bridge = specify_bridge_command(ROOT, "--version")
    bridge_site_packages = Path(bridge[bridge.index("--site-packages") + 1])
    if not (bridge_site_packages / "specify_cli/__init__.py").is_file():
        raise AssertionError("Live setup did not bind the installed Specify environment")

    path_token = "1234abcd"
    workspace_path = execution_workspace(ROOT, path_token)
    packages_path = candidate_packages(ROOT, path_token)
    if workspace_path != ROOT / "artifacts/live-v2-w" / path_token:
        raise AssertionError("Windows execution workspace lost its bounded short path")
    if packages_path != ROOT / "artifacts/live-v2-p" / path_token:
        raise AssertionError("Candidate package staging lost its bounded short path")

    release_tools = {
        "dotnet": "10.0.202", "node": "v20.11.1", "npm": "10.2.4",
        "git": "git version 2.44.0.windows.1", "specify": "specify 1.0.4", "codex": "unavailable",
    }
    live_tools = {**release_tools, "codex": "codex-cli 0.150.1"}
    validate_toolchain_binding(release_tools, live_tools)
    expect_contract_error(
        lambda: validate_toolchain_binding(
            {**release_tools, "codex": "codex-cli 0.149.0"}, live_tools
        ),
        "LIVE_RELEASE_RECEIPT_TOOLCHAIN_MISMATCH",
    )
    expect_contract_error(
        lambda: validate_toolchain_binding(release_tools, {**live_tools, "codex": "unavailable"}),
        "LIVE_ACCEPTANCE_TOOL_UNUSABLE",
    )
    validate_agent_launcher({"launcherVersion": "codex-cli 0.150.1"}, "codex-cli 0.150.1")
    expect_contract_error(
        lambda: validate_agent_launcher({"launcherVersion": "codex-cli 0.149.0"}, "codex-cli 0.150.1"),
        "LIVE_AUTHORIZATION_LAUNCHER_MISMATCH",
    )

    with tempfile.TemporaryDirectory(prefix="program-kit-live-v2-") as directory:
        temp = Path(directory)
        candidate_artifacts = temp / "candidate-artifacts"
        candidate_artifacts.mkdir()
        archive_names = {
            "governance": "governance.zip", "building-blocks": "building-blocks.zip",
            "dotnet": "dotnet.zip", "preset": "preset.zip", "workflow": "workflow.zip",
            "bundle": "bundle.zip",
        }
        with zipfile.ZipFile(candidate_artifacts / archive_names["workflow"], "w") as archive:
            archive.writestr("workflow.yml", "name: test\n")
        with zipfile.ZipFile(candidate_artifacts / archive_names["bundle"], "w") as archive:
            archive.writestr("bundle.yml", "name: test\n")
        extracted_packages = temp / "candidate-packages"
        extract_candidate_control_archives(candidate_artifacts, extracted_packages, archive_names)
        if CONTROL_ARCHIVE_KEYS != ("workflow", "bundle") or {
            path.name for path in extracted_packages.iterdir()
        } != set(CONTROL_ARCHIVE_KEYS):
            raise AssertionError("Candidate setup eagerly extracted component payload archives")

        changed_scenario = temp / "changed-scenario"
        shutil.copytree(SCENARIO, changed_scenario)
        (changed_scenario / "fixture/PROJECT_REQUEST.md").write_text("changed fixture\n", encoding="utf-8")
        if scenario_authority(changed_scenario, SCHEMAS)["digest"] == authority["digest"]:
            raise AssertionError("Scenario authorization digest does not bind fixture content")
        artifacts = temp / "artifacts"
        artifacts.mkdir()
        candidate_names = {
            "program-kit-governance-9.9.9.zip", "program-kit-building-blocks-9.9.9.zip",
            "program-kit-dotnet-9.9.9.zip", "program-kit-governance-preset-9.9.9.zip",
            "program-kit-bootstrap-9.9.9.zip", "program-kit-9.9.9.zip",
            "Initialize-ProgramKit-9.9.9.cmd", "Initialize-ProgramKit-9.9.9.sh", "SHA256SUMS",
        }
        for name in candidate_names | {"program-kit-stale-1.0.0.zip"}:
            (artifacts / name).write_text(name, encoding="utf-8")
        recorded_names = {Path(record["path"]).name for record in receipt_writer.artifact_records(artifacts, "9.9.9")}
        if recorded_names != candidate_names:
            raise AssertionError(f"Release receipt did not isolate the exact current candidate: {recorded_names}")
        project = temp / "project"
        shutil.copytree(SCENARIO / scenario["fixture"], project)
        architecture_path = project / "docs/architecture/architecture-map.json"
        architecture = load_object(architecture_path)
        architecture["decisions"] = [
            {"id": decision, "status": "Accepted"} for decision in scenario["acceptedDecisionIds"]
        ]
        atomic_write_json(architecture_path, architecture)
        selection_path, selection_sha = bind_selection(SCENARIO, project, scenario)
        plan = resolver.resolve(project, selection_path, CATALOG, "0.10.0")
        lock_path = project / ".program-kit/building-blocks.lock.json"
        resolver.apply_materialization(project, lock_path, plan, catalog)
        result = validate_consumer(project, expectation)
        if result["packageCount"] != 18 or result["activationCount"] < 10:
            raise AssertionError(f"Internal Forms oracle coverage is incomplete: {result}")

        request = restore.restore_request(project, lock_path, plan, "renew")
        validate(request, load_object(SCHEMAS / "restore-request.schema.json"))
        if request["lockSha256"] != sha256_file(lock_path) or not request["commands"]:
            raise AssertionError("Restore request is not bound to the native restore plan")
        if request["repository"] != "." or any(Path(item["cwd"]).is_absolute() or any(Path(argument).is_absolute() for argument in item["args"]) for item in request["commands"]):
            raise AssertionError("Restore request leaked a machine-bound consumer path")
        denied = subprocess.run([sys.executable, str(RESTORE), "renew", "--target", str(project)], capture_output=True, text=True)
        if denied.returncode != 2 or "PKB622" not in denied.stderr:
            raise AssertionError("Credential-bearing restore no longer requires explicit approval")
        requested = subprocess.run([sys.executable, str(RESTORE), "request-renew", "--target", str(project)], capture_output=True, text=True)
        if requested.returncode != 0 or "without network access" not in requested.stdout:
            raise AssertionError(f"Read-only restore request failed: {requested}")

        store = EvidenceStore(temp / "evidence")
        store.initialize()
        checkpoint_path, checkpoint = seal_checkpoint(
            store, project, load_object(SCHEMAS / "checkpoint.schema.json"), phase="bootstrap-checkpoint",
            candidate_digest="a" * 64, scenario_digest=authority["digest"], expectation_digest=sha256_file(expectation_path),
            selection_sha256=selection_sha,
        )
        expected_web = (project / "web/package.json").read_bytes()
        (project / "web/package.json").write_text('{"mutatedAfterSeal":true}\n', encoding="utf-8")
        copied = temp / "copied"
        materialize_checkpoint(store, checkpoint_path, copied, load_object(SCHEMAS / "checkpoint.schema.json"))
        if (copied / "web/package.json").read_bytes() != expected_web:
            raise AssertionError("Checkpoint object changed when the source workspace was modified")

        authorization_path = temp / "authorization.json"
        authorization_schema = load_object(SCHEMAS / "authorization.schema.json")
        issued = issue_authorization(
            authorization_path, authorization_schema, phase="building-block-consumer",
            scenario={key: authority[key] for key in ("id", "version", "digest")},
            candidate={"releaseReceipt": "artifacts/release-receipt.json", "releaseReceiptSha256": "a" * 64},
            checkpoint={"checkpointId": checkpoint["checkpointId"], "digest": sha256_file(checkpoint_path)},
            agent_profile={"integration": "codex", "launcherVersion": "codex-cli test", "model": "test-model", "reasoningEffort": "high", "sandbox": "workspace-write", "timeoutSeconds": 60},
        )
        validated = validate_authorization(
            authorization_path, authorization_schema, phase="building-block-consumer", scenario_digest=authority["digest"],
            candidate_receipt_digest="a" * 64, checkpoint_digest=sha256_file(checkpoint_path),
        )
        consume_authorization(authorization_path, validated, temp / "consumed")
        expect_contract_error(lambda: consume_authorization(authorization_path, issued, temp / "consumed"), "LIVE_AUTHORIZATION_REPLAYED")

        redactor = StreamingRedactor(["top-secret-token"])
        first = redactor.feed(b"prefix top-sec")
        second = redactor.feed(b"ret-token suffix")
        final, summary = redactor.finish()
        redacted = first + second + final
        if b"top-secret-token" in redacted or b"[REDACTED]" not in redacted or summary.redaction_count != 1:
            raise AssertionError("Streaming redaction failed across a chunk boundary")
        crossing = StreamingRedactor(["boundary-secret"])
        output = crossing.feed((b"x" * 510) + b"boundary-")
        output += crossing.feed(b"secret tail" + (b"y" * 600))
        ending, _ = crossing.finish()
        output += ending
        if b"boundary-secret" in output or b"boundary-" in output:
            raise AssertionError("Streaming redaction split and leaked a secret at its flush boundary")

        process = run_supervised(
            [sys.executable, "-c", "import sys; print('top-secret-token'); sys.exit(130)"], cwd=temp,
            environment=os.environ.copy(), evidence_directory=temp / "process", timeout_seconds=30, secrets=["top-secret-token"],
        )
        if process.exitCode != 130 or process.operatorCancellationRecorded or not process.cleanupComplete or not process.logsDrained:
            raise AssertionError(f"Exit 130 was incorrectly classified as operator cancellation: {process}")
        if process_failure(process) != ("inconclusive", ["unclassified"]):
            raise AssertionError("Exit 130 without observed interruption was not classified as inconclusive")
        if "top-secret-token" in (temp / "process/workflow.stdout.log").read_text(encoding="utf-8"):
            raise AssertionError("Supervisor retained a raw secret")

        previous_token = os.environ.get("PROGRAM_KIT_NPM_TOKEN")
        os.environ["PROGRAM_KIT_NPM_TOKEN"] = "worker-must-not-receive-this"
        try:
            worker = worker_environment(temp, {"model": "test-model", "reasoningEffort": "high"})
            clean = supervisor_environment()
            registry = supervisor_environment("supervisor-only-token")
        finally:
            if previous_token is None:
                os.environ.pop("PROGRAM_KIT_NPM_TOKEN", None)
            else:
                os.environ["PROGRAM_KIT_NPM_TOKEN"] = previous_token
        if "PROGRAM_KIT_NPM_TOKEN" in worker or "PROGRAM_KIT_NPM_TOKEN" in clean:
            raise AssertionError("Registry credential crossed into a worker or non-registry child")
        if registry.get("PROGRAM_KIT_NPM_TOKEN") != "supervisor-only-token":
            raise AssertionError("Supervisor registry child did not receive the exact injected credential")

    legacy = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ROOT / "scripts/Test-LiveBootstrap.ps1"), "-Approved"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    if legacy.returncode == 0 or "LIVE_ACCEPTANCE_V1_RETIRED" not in (legacy.stdout + legacy.stderr):
        raise AssertionError("Legacy paid runner was not retired before launch")
    runner_text = (ROOT / "tests/live/run_bootstrap_acceptance.py").read_text(encoding="utf-8")
    supervisor_text = (ROOT / "tests/live/v2/supervisor.py").read_text(encoding="utf-8")
    if "LIVE_ACCEPTANCE_V1_RETIRED" not in runner_text:
        raise AssertionError("Legacy Python entrypoint can still claim authority")
    if "os.kill(pid, 0)" in supervisor_text or "CTRL_C_EVENT" in supervisor_text:
        raise AssertionError("Windows process liveness regressed to signalling the console group")
    if any(marker not in supervisor_text for marker in ("CreateJobObjectW", "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE", "CREATE_SUSPENDED", "NtResumeProcess")):
        raise AssertionError("Windows worker descendants are not Job Object-owned")
    aggregate = (ROOT / "scripts/Test-ProgramKit.ps1").read_text(encoding="utf-8")
    if "write_release_receipt.py" not in aggregate:
        raise AssertionError("The deterministic Release suite does not emit a machine-bound receipt")
    release = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    if "Test-Live" in release or "live.v2.cli" in release:
        raise AssertionError("A paid live phase was added to CI")

    print("Live acceptance v2 authorization, scenario, checkpoint, redaction, supervision, and restore contracts passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
