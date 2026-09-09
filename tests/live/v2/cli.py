from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from live.v2.authorization import consume_authorization, issue_authorization, validate_authorization
from live.v2.candidate import install_candidate_from_receipt, validate_release_receipt
from live.v2.checkpoint import checkpoint_digest, materialize_checkpoint, seal_checkpoint
from live.v2.common import LiveContractError, atomic_write_json, canonical_sha256, load_object, sha256_file, utc_now, validate
from live.v2.evidence import EvidenceStore
from live.v2.scenario import bind_selection, copied_fixture, load_scenario, scenario_authority
from live.v2.supervisor import ProcessResult, run_supervised
from live.v2.validation import validate_consumer


CI_KEYS = ("CI", "GITHUB_ACTIONS", "TF_BUILD", "BUILD_BUILDID")
SECRET_KEYS = ("PROGRAM_KIT_NPM_TOKEN", "NPM_TOKEN", "NODE_AUTH_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")
LIVE_TOOLCHAINS = ("dotnet", "node", "npm", "git", "specify", "codex")


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def schemas(root: Path) -> Path:
    return root / "tests/live/schemas/v2"


def default_scenario(root: Path) -> Path:
    return root / "tests/live/scenarios/internal-forms-workspace/v1"


def execution_workspace(root: Path, run_token: str) -> Path:
    return root / "artifacts/live-v2-w" / run_token


def candidate_packages(root: Path, run_token: str) -> Path:
    return root / "artifacts/live-v2-p" / run_token


def git(root: Path, *arguments: str) -> str:
    excludes = "" if os.name == "nt" else os.devnull
    result = subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", "-c", f"core.excludesFile={excludes}", "-C", str(root), *arguments],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    if result.returncode != 0:
        raise LiveContractError(f"LIVE_GIT_FAILED: {result.stderr.strip()}")
    return result.stdout.strip()


def tool_version(name: str) -> str:
    executable = shutil.which(name)
    if executable is None:
        return "unavailable"
    result = subprocess.run(
        [executable, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    lines = ((result.stdout or "") + (result.stderr or "")).strip().splitlines()
    return lines[0] if result.returncode == 0 and lines else "unavailable"


def validate_toolchain_binding(receipt_tools: dict[str, str], current_tools: dict[str, str]) -> None:
    unusable = [name for name in LIVE_TOOLCHAINS if current_tools.get(name) == "unavailable"]
    if unusable:
        raise LiveContractError(f"LIVE_ACCEPTANCE_TOOL_UNUSABLE: {unusable}")
    mismatches = {
        name: {"receipt": receipt_tools[name], "current": current_tools[name]}
        for name in LIVE_TOOLCHAINS
        if receipt_tools[name] != "unavailable" and receipt_tools[name] != current_tools[name]
    }
    if mismatches:
        raise LiveContractError(f"LIVE_RELEASE_RECEIPT_TOOLCHAIN_MISMATCH: {mismatches}")


def validate_agent_launcher(profile: dict[str, Any], current_version: str | None = None) -> None:
    actual = current_version if current_version is not None else tool_version("codex")
    if actual == "unavailable":
        raise LiveContractError("LIVE_ACCEPTANCE_TOOL_UNUSABLE: ['codex']")
    if profile.get("launcherVersion") != actual:
        raise LiveContractError(
            "LIVE_AUTHORIZATION_LAUNCHER_MISMATCH: "
            f"authorized={profile.get('launcherVersion')} current={actual}"
        )


def preflight(root: Path, receipt: dict[str, Any]) -> None:
    active_ci = [key for key in CI_KEYS if os.environ.get(key)]
    if active_ci:
        raise LiveContractError(f"LIVE_ACCEPTANCE_CI_FORBIDDEN: {', '.join(active_ci)}")
    missing = [name for name in ("git", "specify", "codex") if shutil.which(name) is None]
    if missing:
        raise LiveContractError(f"LIVE_ACCEPTANCE_TOOL_MISSING: {missing}")
    current_platform = {"system": platform.system(), "release": platform.release(), "machine": platform.machine()}
    if receipt["platform"] != current_platform:
        raise LiveContractError(f"LIVE_RELEASE_RECEIPT_PLATFORM_MISMATCH: receipt={receipt['platform']} current={current_platform}")
    current_tools = {name: tool_version(name) for name in LIVE_TOOLCHAINS}
    receipt_tools = {name: receipt["toolchains"][name] for name in current_tools}
    validate_toolchain_binding(receipt_tools, current_tools)
    if git(root, "rev-parse", "HEAD") != receipt["source"]["commit"]:
        raise LiveContractError("LIVE_RELEASE_RECEIPT_SOURCE_COMMIT_MISMATCH")
    if git(root, "rev-parse", "HEAD^{tree}") != receipt["source"]["tree"]:
        raise LiveContractError("LIVE_RELEASE_RECEIPT_SOURCE_TREE_MISMATCH")
    if git(root, "status", "--porcelain=v1"):
        raise LiveContractError("LIVE_ACCEPTANCE_SOURCE_NOT_CLEAN")


def worker_environment(project: Path, profile: dict[str, Any]) -> dict[str, str]:
    allowed = {
        "PATH", "PATHEXT", "SYSTEMROOT", "COMSPEC", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA",
        "CODEX_HOME", "SSL_CERT_FILE", "SSL_CERT_DIR", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
    }
    environment = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    for key in SECRET_KEYS:
        environment.pop(key, None)
    environment.update(
        {
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
            "PROGRAM_KIT_LIVE_ACCEPTANCE": "v2",
            "SPECKIT_INTEGRATION_CODEX_EXTRA_ARGS": (
                f"--sandbox workspace-write --model {profile['model']} "
                f"-c model_reasoning_effort=\"{profile['reasoningEffort']}\""
            ),
            "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "safe.directory",
            "GIT_CONFIG_VALUE_0": str(project.resolve()),
            "GIT_CONFIG_KEY_1": "core.excludesFile",
            "GIT_CONFIG_VALUE_1": "" if os.name == "nt" else os.devnull,
        }
    )
    return environment


def supervisor_environment(token: str | None = None) -> dict[str, str]:
    environment = os.environ.copy()
    for key in SECRET_KEYS:
        environment.pop(key, None)
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    if token is not None:
        environment["PROGRAM_KIT_NPM_TOKEN"] = token
    return environment


def process_failure(result: ProcessResult) -> tuple[str, list[str]]:
    if result.operatorCancellationRecorded:
        return "cancelled", ["operator"]
    if result.timedOut:
        return "inconclusive", ["environment"]
    if result.exitCode == 130:
        return "inconclusive", ["unclassified"]
    if not result.cleanupComplete or not result.logsDrained:
        return "failed", ["harness"]
    return "failed", ["model-conformance"]


def worker_guidance(project: Path) -> None:
    excludes = "" if os.name == "nt" else os.devnull
    atomic_write_json(project / ".program-kit-live/worker-boundary.json", {"schemaVersion": "2.0", "network": "model-transport-only", "restoreOwner": "supervisor"})
    (project / "AGENTS.md").write_text(
        "# Disposable Program Kit live worker\n\n"
        "Work only in this disposable repository. Do not start browsers, viewers, containers, Java, or development servers.\n"
        "Do not perform network restores or request credentials. Use restore_dependencies.py request-renew and let the supervisor own restore.\n"
        f"On Windows run Git as: git -c safe.directory={project.resolve().as_posix()} -c core.excludesFile= <command>.\n"
        f"On POSIX use core.excludesFile={excludes}. Never modify global Git configuration.\n",
        encoding="utf-8", newline="\n",
    )


def operation(command: list[str], project: Path, evidence: Path, name: str, environment: dict[str, str], secrets: list[str] | None = None, timeout: int = 1200) -> tuple[ProcessResult, dict[str, Any]]:
    result = run_supervised(command, cwd=project, environment=environment, evidence_directory=evidence / name, timeout_seconds=timeout, secrets=secrets)
    process_evidence = result.as_dict()
    process_evidence["stdout"]["path"] = f"{name}/{process_evidence['stdout']['path']}"
    process_evidence["stderr"]["path"] = f"{name}/{process_evidence['stderr']['path']}"
    receipt = {
        "schemaVersion": "2.0", "operation": name, "command": command, "exitCode": result.exitCode,
        "startedAt": result.startedAt, "finishedAt": result.finishedAt, "process": process_evidence,
    }
    return result, receipt


def store_logs(store: EvidenceStore, process: ProcessResult, directory: Path) -> list[dict[str, object]]:
    records = []
    for log in (process.stdout, process.stderr):
        object_record = store.put_file(directory / log.path)
        records.append({**log.__dict__, "object": object_record})
    return records


def issue(args: argparse.Namespace) -> int:
    if not args.confirmed:
        raise LiveContractError("LIVE_AUTHORIZATION_INTERACTIVE_CONFIRMATION_REQUIRED")
    root = repository_root()
    schema_root = schemas(root)
    scenario_root = Path(args.scenario).resolve() if args.scenario else default_scenario(root)
    authority = scenario_authority(scenario_root, schema_root)
    receipt_path = Path(args.release_receipt).resolve()
    receipt, receipt_digest = validate_release_receipt(root, receipt_path, load_object(schema_root / "release-receipt.schema.json"))
    preflight(root, receipt)
    checkpoint = None
    if args.checkpoint:
        checkpoint_path = Path(args.checkpoint).resolve()
        checkpoint_value = load_object(checkpoint_path)
        validate(checkpoint_value, load_object(schema_root / "checkpoint.schema.json"))
        validate_checkpoint_binding(checkpoint_value, scenario_root, authority, receipt_digest)
        checkpoint = {"checkpointId": checkpoint_value["checkpointId"], "digest": checkpoint_digest(checkpoint_path)}
    launcher_version = tool_version("codex")
    if args.launcher_version != launcher_version:
        raise LiveContractError(
            f"LIVE_AUTHORIZATION_LAUNCHER_MISMATCH: displayed={args.launcher_version} current={launcher_version}"
        )
    profile = {
        "integration": "codex", "launcherVersion": launcher_version, "model": args.model,
        "reasoningEffort": args.reasoning_effort, "sandbox": "workspace-write",
        "timeoutSeconds": args.timeout_seconds,
    }
    destination = Path(args.output).resolve()
    manifest = issue_authorization(
        destination, load_object(schema_root / "authorization.schema.json"), phase=args.phase,
        scenario={key: authority[key] for key in ("id", "version", "digest")},
        candidate={"releaseReceipt": str(receipt_path), "releaseReceiptSha256": receipt_digest},
        checkpoint=checkpoint, agent_profile=profile, expires_minutes=args.expires_minutes,
    )
    print(f"Live authorization {manifest['authorizationId']}: {destination}")
    return 0


def validate_checkpoint_binding(checkpoint: dict[str, Any], scenario_root: Path, authority: dict[str, str], receipt_digest: str) -> None:
    scenario, _, expectation_path = load_scenario(scenario_root, schemas(repository_root()))
    if checkpoint["phase"] != "bootstrap-checkpoint" or checkpoint["parent"] is not None:
        raise LiveContractError("LIVE_CHECKPOINT_PHASE_MISMATCH")
    if checkpoint["candidate"] != receipt_digest:
        raise LiveContractError("LIVE_CHECKPOINT_CANDIDATE_MISMATCH")
    if checkpoint["scenario"] != authority["digest"]:
        raise LiveContractError("LIVE_CHECKPOINT_SCENARIO_MISMATCH")
    if checkpoint["expectation"] != sha256_file(expectation_path):
        raise LiveContractError("LIVE_CHECKPOINT_EXPECTATION_MISMATCH")


def _phase_inputs(args: argparse.Namespace, phase: str) -> tuple[Path, Path, EvidenceStore, dict[str, Any], dict[str, Any], dict[str, Any], str, dict[str, Any]]:
    root = repository_root()
    schema_root = schemas(root)
    scenario_root = Path(args.scenario).resolve() if args.scenario else default_scenario(root)
    scenario, expectation, expectation_path = load_scenario(scenario_root, schema_root)
    authority = scenario_authority(scenario_root, schema_root)
    authorization_path = Path(args.authorization).resolve()
    authorization_raw = load_object(authorization_path)
    receipt_path = Path(authorization_raw["candidate"]["releaseReceipt"]).resolve()
    receipt, receipt_digest = validate_release_receipt(root, receipt_path, load_object(schema_root / "release-receipt.schema.json"))
    preflight(root, receipt)
    store = EvidenceStore(root / "artifacts/live-acceptance/v2")
    store.initialize()
    checkpoint_sha = checkpoint_digest(Path(args.checkpoint).resolve()) if getattr(args, "checkpoint", None) else None
    if getattr(args, "checkpoint", None):
        checkpoint_value = load_object(Path(args.checkpoint).resolve())
        validate(checkpoint_value, load_object(schema_root / "checkpoint.schema.json"))
        validate_checkpoint_binding(checkpoint_value, scenario_root, authority, receipt_digest)
    authorization = validate_authorization(
        authorization_path, load_object(schema_root / "authorization.schema.json"), phase=phase,
        scenario_digest=authority["digest"], candidate_receipt_digest=receipt_digest, checkpoint_digest=checkpoint_sha,
    )
    validate_agent_launcher(authorization["agentProfile"])
    return root, scenario_root, store, scenario, expectation, receipt, receipt_digest, authorization


def bootstrap(args: argparse.Namespace) -> int:
    root, scenario_root, store, scenario, expectation, receipt, receipt_digest, authorization = _phase_inputs(args, "bootstrap-checkpoint")
    run_token = uuid.uuid4().hex[:8]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-bootstrap-{run_token}"
    run_root = store.runs / run_id
    project = execution_workspace(root, run_token)
    packages = candidate_packages(root, run_token)
    shutil.copytree(copied_fixture(scenario_root, scenario), project)
    setup_receipts = install_candidate_from_receipt(root, project, packages, receipt, run_root / "setup")
    worker_guidance(project)
    workflow_definition = packages / "workflow/workflow.yml"
    paid_steps = sum(1 for line in workflow_definition.read_text(encoding="utf-8").splitlines() if line.strip() == "type: command")
    if paid_steps < 1 or paid_steps > authorization["limits"]["maximumPaidSessions"]:
        raise LiveContractError(
            f"LIVE_AUTHORIZATION_SESSION_LIMIT_EXCEEDED: workflow has {paid_steps} paid steps; "
            f"authorization permits {authorization['limits']['maximumPaidSessions']}"
        )
    consumption = consume_authorization(Path(args.authorization).resolve(), authorization, store.authorizations / "consumed")
    command = [
        shutil.which("specify") or "specify", "workflow", "run", "program-kit-bootstrap",
        "--input", "bootstrap_intake=docs/architecture/bootstrap-intake.json", "--input", "integration=codex",
        "--input", "auto_approve_and_ratify=true", "--json",
    ]
    result = run_supervised(
        command, cwd=project, environment=worker_environment(project, authorization["agentProfile"]),
        evidence_directory=run_root / "worker", timeout_seconds=authorization["agentProfile"]["timeoutSeconds"],
        secrets=[os.environ.get(key, "") for key in SECRET_KEYS],
    )
    status, causes = process_failure(result)
    checkpoint_path: Path | None = None
    try:
        if result.exitCode != 0:
            raise LiveContractError(f"LIVE_BOOTSTRAP_WORKER_EXIT: {result.exitCode}")
        validator = project / ".specify/extensions/program-kit-governance/scripts/governance_state.py"
        validation = subprocess.run([sys.executable, str(validator), "validate-bootstrap"], cwd=project, check=False)
        if validation.returncode != 0:
            raise LiveContractError("LIVE_BOOTSTRAP_DETERMINISTIC_VALIDATION_FAILED")
        _, selection_sha = bind_selection(scenario_root, project, scenario)
        plan = subprocess.run(
            [sys.executable, str(project / ".specify/extensions/program-kit-building-blocks/scripts/building_blocks.py"), "plan", "--target", str(project)],
            cwd=project, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        )
        if plan.returncode != 0:
            raise LiveContractError(f"LIVE_BOOTSTRAP_SELECTION_BINDING_FAILED: {plan.stderr.strip()}")
        checkpoint_path, _ = seal_checkpoint(
            store, project, load_object(schemas(root) / "checkpoint.schema.json"), phase="bootstrap-checkpoint",
            candidate_digest=receipt_digest, scenario_digest=scenario_authority(scenario_root, schemas(root))["digest"],
            expectation_digest=sha256_file(scenario_root / scenario["activeExpectation"]), selection_sha256=selection_sha,
        )
        status = "checkpoint-created"
        causes = []
    except LiveContractError as error:
        (run_root / "failure.txt").write_text(str(error) + "\n", encoding="utf-8")
    logs = store_logs(store, result, run_root / "worker")
    manifest = {
        "schemaVersion": "2.0", "runId": run_id, "phase": "bootstrap-checkpoint", "status": status, "causes": causes,
        "authorization": consumption, "candidate": {"releaseReceiptSha256": receipt_digest},
        "scenario": scenario_authority(scenario_root, schemas(root)), "agentProfile": authorization["agentProfile"],
        "process": result.as_dict(), "logs": logs, "receipts": setup_receipts,
        "workspace": project.relative_to(root).as_posix(),
        "checkpoint": str(checkpoint_path) if checkpoint_path else None, "startedAt": result.startedAt, "finishedAt": utc_now(),
    }
    validate(manifest, load_object(schemas(root) / "evidence-manifest.schema.json"))
    report = store.write_run_manifest(run_id, manifest)
    print(f"Live bootstrap status: {status}; report: {report}")
    return 0 if status == "checkpoint-created" else 1


def _load_restore_module(path: Path):
    spec = importlib.util.spec_from_file_location("live_restore_dependencies", path)
    if spec is None or spec.loader is None:
        raise LiveContractError("LIVE_RESTORE_MODULE_LOAD_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def building_blocks(args: argparse.Namespace) -> int:
    root, scenario_root, store, scenario, expectation, receipt, receipt_digest, authorization = _phase_inputs(args, "building-block-consumer")
    token = os.environ.get("PROGRAM_KIT_NPM_TOKEN")
    if not token:
        raise LiveContractError("LIVE_RESTORE_CREDENTIAL_MISSING")
    run_token = uuid.uuid4().hex[:8]
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-building-blocks-{run_token}"
    run_root = store.runs / run_id
    project = execution_workspace(root, run_token)
    parent_path = Path(args.checkpoint).resolve()
    parent = materialize_checkpoint(store, parent_path, project, load_object(schemas(root) / "checkpoint.schema.json"))
    worker_guidance(project)
    consumption = consume_authorization(Path(args.authorization).resolve(), authorization, store.authorizations / "consumed")
    prompt = (
        "Adopt the already Accepted building-block selection for this disposable Internal Forms Workspace. "
        "Use the shipped Program Kit building-block workflow and its canonical tools. Review the computed plan digest, "
        "apply exactly that plan, and emit a credential-free renew restore request. Do not run a network restore, request "
        "credentials, change accepted architecture, implement a product slice, or start a browser, viewer, container, Java, "
        "or development server. Finish after the renew request is present; the supervisor owns restore and validation."
    )
    profile = authorization["agentProfile"]
    command = [shutil.which("codex") or "codex", "exec", "--sandbox", "workspace-write", "--cd", str(project), "--json", "--model", profile["model"], "-c", f"model_reasoning_effort=\"{profile['reasoningEffort']}\"", prompt]
    result = run_supervised(
        command, cwd=project, environment=worker_environment(project, profile), evidence_directory=run_root / "worker",
        timeout_seconds=profile["timeoutSeconds"], secrets=[token],
    )
    receipts: list[dict[str, Any]] = []
    status, causes = process_failure(result)
    derived_checkpoint: Path | None = None
    try:
        if result.exitCode != 0:
            raise LiveContractError(f"LIVE_BUILDING_BLOCK_WORKER_EXIT: {result.exitCode}")
        tool = project / ".specify/extensions/program-kit-building-blocks/scripts/building_blocks.py"
        restore_tool = project / ".specify/extensions/program-kit-building-blocks/scripts/restore_dependencies.py"
        plan = subprocess.run([sys.executable, str(tool), "plan", "--target", str(project)], cwd=project, capture_output=True, text=True, encoding="utf-8", check=False)
        if plan.returncode != 0:
            raise LiveContractError(f"LIVE_BUILDING_BLOCK_PLAN_FAILED: {plan.stderr.strip()}")
        plan_value = json.loads(plan.stdout)
        plan_digest = plan_value["planDigest"]
        lock = load_object(project / ".program-kit/building-blocks.lock.json")
        if lock != plan_value:
            raise LiveContractError("LIVE_BUILDING_BLOCK_APPLY_NOT_OBSERVED")
        receipts.extend([
            {"schemaVersion": "2.0", "operation": "plan", "planDigest": plan_digest, "command": ["building_blocks.py", "plan"], "exitCode": 0, "startedAt": result.finishedAt, "finishedAt": utc_now(), "artifacts": []},
            {"schemaVersion": "2.0", "operation": "apply", "planDigest": plan_digest, "command": ["building_blocks.py", "apply", "--plan-digest", plan_digest], "exitCode": 0, "startedAt": result.startedAt, "finishedAt": result.finishedAt, "artifacts": []},
        ])
        request_path = project / ".program-kit/evidence/building-block-restore-request.json"
        if not request_path.is_file():
            raise LiveContractError("LIVE_RESTORE_RENEW_REQUEST_MISSING")
        restore_module = _load_restore_module(restore_tool)
        expected_request = restore_module.restore_request(project, project / ".program-kit/building-blocks.lock.json", lock, "renew")
        if load_object(request_path) != expected_request:
            raise LiveContractError("LIVE_RESTORE_RENEW_REQUEST_MISMATCH")
        receipts.append({"schemaVersion": "2.0", "operation": "restore-request-renew", "planDigest": plan_digest, "command": ["restore_dependencies.py", "request-renew"], "exitCode": 0, "startedAt": result.startedAt, "finishedAt": result.finishedAt, "artifacts": []})
        clean_environment = supervisor_environment()
        registry_environment = supervisor_environment(token)
        availability_tool = project / ".specify/extensions/program-kit-building-blocks/scripts/public_availability.py"
        catalog_path = project / ".specify/extensions/program-kit-building-blocks/references/orbyss-building-blocks.json"
        availability_path = project / ".program-kit/evidence/building-block-availability.json"
        available, availability_receipt = operation(
            [sys.executable, str(availability_tool), "--target", str(project), "--catalog", str(catalog_path), "--lock", ".program-kit/building-blocks.lock.json"],
            project, run_root, "availability", registry_environment, [token],
        )
        availability_receipt.update({
            "planDigest": plan_digest,
            "artifacts": [] if not availability_path.is_file() else [{"path": availability_path.relative_to(project).as_posix(), "sha256": sha256_file(availability_path), "size": availability_path.stat().st_size}],
        })
        receipts.append(availability_receipt)
        if available.exitCode != 0 or not availability_path.is_file():
            raise LiveContractError("LIVE_SELECTED_AVAILABILITY_FAILED")
        renew, renew_receipt = operation([sys.executable, str(restore_tool), "renew", "--target", str(project), "--approved"], project, run_root, "restore-renew", registry_environment, [token])
        renew_receipt.update({"planDigest": plan_digest, "artifacts": []})
        receipts.append(renew_receipt)
        if renew.exitCode != 0:
            raise LiveContractError("LIVE_RESTORE_RENEW_FAILED")
        locked_request = subprocess.run([sys.executable, str(restore_tool), "request-locked", "--target", str(project)], cwd=project, env=clean_environment, check=False)
        if locked_request.returncode != 0:
            raise LiveContractError("LIVE_RESTORE_LOCKED_REQUEST_FAILED")
        receipts.append({"schemaVersion": "2.0", "operation": "restore-request-locked", "planDigest": plan_digest, "command": ["restore_dependencies.py", "request-locked"], "exitCode": 0, "startedAt": utc_now(), "finishedAt": utc_now(), "artifacts": []})
        locked, locked_receipt = operation([sys.executable, str(restore_tool), "locked", "--target", str(project), "--approved"], project, run_root, "restore-locked", registry_environment, [token])
        locked_receipt.update({"planDigest": plan_digest, "artifacts": []})
        receipts.append(locked_receipt)
        if locked.exitCode != 0:
            raise LiveContractError("LIVE_RESTORE_LOCKED_FAILED")
        checks = [
            ([sys.executable, str(tool), "check", "--target", str(project)], "check"),
            (["dotnet", "build", "InternalForms.slnx", "--no-restore"], "dotnet-build"),
            (["npm", "run", "verify"], "npm-verify"),
        ]
        for command_value, name in checks:
            cwd = project / "web" if name == "npm-verify" else project
            checked, check_receipt = operation(command_value, cwd, run_root, name, clean_environment, [token])
            check_receipt.update({"planDigest": plan_digest, "artifacts": []})
            receipts.append(check_receipt)
            if checked.exitCode != 0 or not checked.cleanupComplete or not checked.logsDrained:
                raise LiveContractError(f"LIVE_INDEPENDENT_{name.upper().replace('-', '_')}_FAILED")
        validation_result = validate_consumer(project, expectation)
        derived_checkpoint, _ = seal_checkpoint(
            store, project, load_object(schemas(root) / "checkpoint.schema.json"), phase="building-block-consumer",
            candidate_digest=receipt_digest, scenario_digest=scenario_authority(scenario_root, schemas(root))["digest"],
            expectation_digest=sha256_file(scenario_root / scenario["activeExpectation"]),
            selection_sha256=sha256_file(project / "docs/architecture/building-block-selection.json"), parent=parent["checkpointId"],
        )
        status = "passed"
        causes = []
    except (LiveContractError, json.JSONDecodeError) as error:
        failure = str(error)
        if status == "failed" and causes == ["model-conformance"]:
            if "AVAILABILITY" in failure or "RESTORE_" in failure:
                causes = ["external-service"]
            elif "INDEPENDENT_" in failure or "VALIDATION_" in failure:
                causes = ["product"]
        (run_root / "failure.txt").write_text(str(error) + "\n", encoding="utf-8")
    receipt_schema = load_object(schemas(root) / "operation-receipt.schema.json")
    for receipt_value in receipts:
        validate(receipt_value, receipt_schema)
    logs = store_logs(store, result, run_root / "worker")
    manifest = {
        "schemaVersion": "2.0", "runId": run_id, "phase": "building-block-consumer", "status": status, "causes": causes,
        "authorization": consumption, "candidate": {"releaseReceiptSha256": receipt_digest},
        "scenario": scenario_authority(scenario_root, schemas(root)), "agentProfile": profile, "process": result.as_dict(),
        "logs": logs, "receipts": receipts, "oracle": validation_result if status == "passed" else {},
        "workspace": project.relative_to(root).as_posix(),
        "checkpoint": str(derived_checkpoint) if derived_checkpoint else None,
        "startedAt": result.startedAt, "finishedAt": utc_now(),
    }
    validate(manifest, load_object(schemas(root) / "evidence-manifest.schema.json"))
    report = store.write_run_manifest(run_id, manifest)
    print(f"Live building-block status: {status}; report: {report}")
    return 0 if status == "passed" else 1


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Governed Program Kit live-acceptance v2 phases.")
    commands = value.add_subparsers(dest="command", required=True)
    authorize = commands.add_parser("authorize")
    authorize.add_argument("--phase", required=True, choices=("bootstrap-checkpoint", "building-block-consumer"))
    authorize.add_argument("--release-receipt", required=True)
    authorize.add_argument("--scenario")
    authorize.add_argument("--checkpoint")
    authorize.add_argument("--model", required=True)
    authorize.add_argument("--reasoning-effort", required=True)
    authorize.add_argument("--launcher-version", required=True)
    authorize.add_argument("--timeout-seconds", type=int, default=7200)
    authorize.add_argument("--expires-minutes", type=int, default=30)
    authorize.add_argument("--output", required=True)
    authorize.add_argument("--confirmed", action="store_true")
    bootstrap_parser = commands.add_parser("bootstrap")
    bootstrap_parser.add_argument("--authorization", required=True)
    bootstrap_parser.add_argument("--scenario")
    blocks = commands.add_parser("building-block-consumer")
    blocks.add_argument("--authorization", required=True)
    blocks.add_argument("--checkpoint", required=True)
    blocks.add_argument("--scenario")
    return value


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "authorize":
            return issue(args)
        if args.command == "bootstrap":
            return bootstrap(args)
        return building_blocks(args)
    except (LiveContractError, OSError, subprocess.SubprocessError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
