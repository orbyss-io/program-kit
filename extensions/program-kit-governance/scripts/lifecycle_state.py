from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ARTIFACTS = ("spec.md", "plan.md", "tasks.md")
BLOCKING_SEVERITIES = {"HIGH", "CRITICAL"}
SCHEMA_VERSION = 1


def configure_utf8() -> None:
    """Make redirected Windows output deterministic without requiring ``python -X utf8``."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="backslashreplace")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def feature_identity(feature_dir: Path) -> str:
    value = feature_dir.name.strip()
    if not value or value in {".", ".."}:
        raise ValueError("Feature directory must have a stable name.")
    return re.sub(r"[^a-zA-Z0-9._-]", "-", value)


def artifact_hashes(feature_dir: Path, required: tuple[str, ...]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name in required:
        path = feature_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"PKL001 required lifecycle artifact is missing: {path}")
        result[name] = sha256(path)
    return result


def state_path(repository: Path, feature_dir: Path) -> Path:
    return repository / ".program-kit" / "lifecycle" / f"{feature_identity(feature_dir)}.json"


def load_state(path: Path) -> dict:
    if not path.is_file():
        return {"schemaVersion": SCHEMA_VERSION, "phases": {}}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError(f"PKL002 lifecycle state has an unsupported schema: {path}")
    if not isinstance(value.get("phases"), dict):
        raise ValueError(f"PKL003 lifecycle state phases are invalid: {path}")
    return value


def atomic_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def feature_contract_error(feature_dir: Path) -> str | None:
    validator_path = Path(__file__).with_name("artifact_ownership.py")
    spec = importlib.util.spec_from_file_location("program_kit_artifact_ownership", validator_path)
    if spec is None or spec.loader is None:
        return f"cannot load artifact ownership validator: {validator_path}"
    validator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validator)
    manifest_path = feature_dir / "artifact-ownership.json"
    try:
        manifest = validator.load_manifest(manifest_path)
        missing = sorted(
            validator.CANONICAL
            - {
                validator.normalize(str(item["path"]))
                for item in manifest["artifacts"]
                if isinstance(item, dict) and "path" in item
            }
        )
        if missing:
            raise ValueError(
                "PKA009 manifest must predeclare canonical Program Kit artifacts: "
                + ", ".join(missing)
            )
        validator.validate_governance_context(feature_dir, True)
        validator.validate_runtime_profile(feature_dir, manifest, True)
        validator.validate_npm_graph_evidence(feature_dir, manifest)
        validator.validate_tasks(feature_dir / "tasks.md", manifest, feature_dir / "plan.md")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return str(error)
    return None


def begin(repository: Path, feature_dir: Path, phase: str, resume: bool) -> int:
    required = ("spec.md",) if phase == "clarify" else ARTIFACTS
    current_hashes = artifact_hashes(feature_dir, required)
    path = state_path(repository, feature_dir)
    state = load_state(path)
    active = state.get("active")
    if isinstance(active, dict):
        same_operation = active.get("phase") == phase and active.get("inputHashes") == current_hashes
        if same_operation and resume:
            active["resumedAtUtc"] = utc_now()
            atomic_write(path, state)
            print(f"resumed {phase} lifecycle for {feature_identity(feature_dir)}")
            return 0
        code = "PKL004" if same_operation else "PKL005"
        print(
            f"{code} lifecycle execution is already active for phase '{active.get('phase')}'. "
            "Resume the matching interrupted phase explicitly; do not re-enter it.",
            file=sys.stderr,
        )
        return 4
    state["feature"] = feature_identity(feature_dir)
    state["active"] = {
        "phase": phase,
        "inputHashes": current_hashes,
        "startedAtUtc": utc_now(),
    }
    atomic_write(path, state)
    print(f"started {phase} lifecycle for {feature_identity(feature_dir)}")
    return 0


def complete_clarify(repository: Path, feature_dir: Path, outcome: str) -> int:
    path = state_path(repository, feature_dir)
    state = load_state(path)
    active = state.get("active")
    if not isinstance(active, dict) or active.get("phase") != "clarify":
        print("PKL006 no active clarification lifecycle can be completed.", file=sys.stderr)
        return 4
    hashes = artifact_hashes(feature_dir, ("spec.md",))
    state["phases"]["afterSpecifyClarification"] = {
        "completedAtUtc": utc_now(),
        "outcome": outcome,
        "artifactHashes": hashes,
    }
    state.pop("active", None)
    atomic_write(path, state)
    print(f"clarification complete ({outcome})")
    return 0


def severities(report: Path) -> list[str]:
    text = report.read_text(encoding="utf-8")
    found = {match.upper() for match in re.findall(r"\b(CRITICAL|HIGH|MEDIUM|LOW)\b", text, re.IGNORECASE)}
    order = {value: index for index, value in enumerate(("CRITICAL", "HIGH", "MEDIUM", "LOW"))}
    return sorted(found, key=order.__getitem__)


def complete_analysis(repository: Path, feature_dir: Path, report: Path) -> int:
    path = state_path(repository, feature_dir)
    state = load_state(path)
    active = state.get("active")
    if not isinstance(active, dict) or active.get("phase") != "analyze":
        print("PKL007 no active after_tasks analysis lifecycle can be completed.", file=sys.stderr)
        return 4
    if not report.is_file():
        print(f"PKL008 canonical analysis report is missing: {report}", file=sys.stderr)
        return 4
    current_hashes = artifact_hashes(feature_dir, ARTIFACTS)
    detected = severities(report)
    blockers = [value for value in detected if value in BLOCKING_SEVERITIES]
    contract_error = feature_contract_error(feature_dir)
    ready = not blockers and contract_error is None
    state["phases"]["afterTasksAnalysis"] = {
        "completedAtUtc": utc_now(),
        "artifactHashes": current_hashes,
        "report": report.resolve().relative_to(repository.resolve()).as_posix(),
        "reportSha256": sha256(report),
        "severities": detected,
        "readyForImplementation": ready,
    }
    if contract_error:
        state["phases"]["afterTasksAnalysis"]["artifactContractError"] = contract_error
    state.pop("active", None)
    atomic_write(path, state)
    if not ready:
        if contract_error:
            print(
                "PKL016 feature artifacts violate deterministic planning/ownership constraints: "
                + contract_error,
                file=sys.stderr,
            )
            return 16
        print(
            "PKL009 feature is not ready for implementation: after_tasks analysis contains "
            + ", ".join(blockers),
            file=sys.stderr,
        )
        return 9
    print("after_tasks analysis is hash-current and ready for implementation")
    return 0


def verify_before_implement(repository: Path, feature_dir: Path) -> int:
    path = state_path(repository, feature_dir)
    state = load_state(path)
    if state.get("active"):
        print("PKL010 lifecycle execution is interrupted or still active.", file=sys.stderr)
        return 10
    analysis = state.get("phases", {}).get("afterTasksAnalysis")
    if not isinstance(analysis, dict):
        print("PKL011 after_tasks analysis evidence is missing.", file=sys.stderr)
        return 11
    current_hashes = artifact_hashes(feature_dir, ARTIFACTS)
    if analysis.get("artifactHashes") != current_hashes:
        print(
            "PKL012 after_tasks analysis is stale; spec.md, plan.md, or tasks.md changed. "
            "Run speckit.analyze and the architecture check again.",
            file=sys.stderr,
        )
        return 12
    if analysis.get("readyForImplementation") is not True:
        print("PKL013 analysis evidence marks the feature not ready for implementation.", file=sys.stderr)
        return 13
    report = repository / str(analysis.get("report", ""))
    if not report.is_file() or sha256(report) != analysis.get("reportSha256"):
        print("PKL014 after_tasks analysis report is missing or changed.", file=sys.stderr)
        return 14
    contract_error = feature_contract_error(feature_dir)
    if contract_error:
        print(
            "PKL016 feature artifacts violate deterministic planning/ownership constraints: "
            + contract_error,
            file=sys.stderr,
        )
        return 16
    print("before_implement lifecycle evidence is current")
    return 0


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Maintain hash-bound Program Kit feature lifecycle evidence.")
    root.add_argument("--repository", default=".", help="Consuming repository root")
    root.add_argument("--feature-dir", required=True, help="Feature directory containing spec.md/plan.md/tasks.md")
    commands = root.add_subparsers(dest="command", required=True)
    begin_parser = commands.add_parser("begin")
    begin_parser.add_argument("phase", choices=("clarify", "analyze"))
    begin_parser.add_argument("--resume", action="store_true")
    clarify = commands.add_parser("complete-clarify")
    clarify.add_argument("--outcome", choices=("questions-answered", "no-questions"), required=True)
    analyze = commands.add_parser("complete-analysis")
    analyze.add_argument("--report", required=True)
    commands.add_parser("verify-before-implement")
    return root


def main() -> int:
    configure_utf8()
    args = parser().parse_args()
    repository = Path(args.repository).resolve()
    feature_dir = Path(args.feature_dir)
    if not feature_dir.is_absolute():
        feature_dir = (repository / feature_dir).resolve()
    try:
        feature_dir.relative_to(repository)
    except ValueError:
        print("PKL015 feature directory must stay inside the repository.", file=sys.stderr)
        return 15
    try:
        if args.command == "begin":
            return begin(repository, feature_dir, args.phase, args.resume)
        if args.command == "complete-clarify":
            return complete_clarify(repository, feature_dir, args.outcome)
        if args.command == "complete-analysis":
            report = Path(args.report)
            if not report.is_absolute():
                report = (repository / report).resolve()
            report.relative_to(repository)
            return complete_analysis(repository, feature_dir, report)
        return verify_before_implement(repository, feature_dir)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
