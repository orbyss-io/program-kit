from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path, PurePosixPath


OWNERSHIP = {"managed", "scaffold-once", "consumer-owned", "generated", "evidence"}
CLASSIFICATION = {"public", "internal", "confidential", "restricted", "secret"}
LIFECYCLE = {"source", "generated", "ephemeral", "retained", "replaced", "deployment"}
CONVENTIONS = {
    "program-kit": {"spec.md", "plan.md", "tasks.md", "research.md", "data-model.md", "quickstart.md"},
    "dotnet": {"*.sln", "*.slnx", "src/**/*.csproj", "tests/**/*.csproj", "Directory.Build.props", "Directory.Build.targets", "Directory.Packages.props"},
    "typescript-vite": {"vite.config.ts", "src/**/*.ts", "src/**/*.tsx", "tests/**/*.spec.ts"},
}
CANONICAL = {
    ".program-kit/evidence/runtime-closure.json",
    ".program-kit/evidence/host-image.json",
    ".program-kit/evidence/after-tasks-analysis.md",
    "docs/security/security-ledger.md",
    "tests/fixtures/program-kit/local-contract.json",
}


def configure_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")


def normalize(value: str) -> str:
    path = value.replace("\\", "/").removeprefix("./")
    if not path or path.startswith("/") or ".." in PurePosixPath(path).parts:
        raise ValueError(f"PKA001 path must be repository-relative without traversal: {value!r}")
    return path


def load_manifest(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schemaVersion") != 1:
        raise ValueError(f"PKA002 unsupported artifact ownership manifest: {path}")
    profiles = value.get("profiles")
    artifacts = value.get("artifacts")
    if not isinstance(profiles, list) or not isinstance(artifacts, list):
        raise ValueError("PKA003 manifest profiles and artifacts must be arrays.")
    seen: set[str] = set()
    for entry in artifacts:
        if not isinstance(entry, dict) or ("path" in entry) == ("pattern" in entry):
            raise ValueError("PKA004 each artifact declares exactly one path or pattern.")
        key = normalize(str(entry.get("path", entry.get("pattern"))))
        if key in seen:
            raise ValueError(f"PKA005 duplicate artifact declaration: {key}")
        seen.add(key)
        if entry.get("ownership") not in OWNERSHIP or entry.get("classification") not in CLASSIFICATION or entry.get("lifecycle") not in LIFECYCLE:
            raise ValueError(f"PKA006 invalid ownership/classification/lifecycle for {key}")
    return value


def matches(path: str, manifest: dict) -> dict | None:
    for entry in manifest["artifacts"]:
        if "path" in entry and normalize(entry["path"]) == path:
            return entry
        if "pattern" in entry and fnmatch.fnmatchcase(path, normalize(entry["pattern"])):
            return entry
    for profile in manifest["profiles"]:
        if any(fnmatch.fnmatchcase(path, pattern) for pattern in CONVENTIONS.get(profile, set())):
            return {"ownership": "consumer-owned", "profile": profile}
    return None


def task_paths(tasks: Path) -> list[tuple[int, str, str]]:
    result: list[tuple[int, str, str]] = []
    for line_number, line in enumerate(tasks.read_text(encoding="utf-8").splitlines(), 1):
        for token in re.findall(r"`([^`]+)`", line):
            if "://" in token or " " in token or token.startswith("--"):
                continue
            if "/" in token or re.search(r"\.(?:cs|csproj|json|md|py|ts|tsx|props|targets|yml|yaml)$", token):
                result.append((line_number, normalize(token), line))
    return result


def extension_point(path: str) -> str:
    if path == "eng/program-kit/Build.ps1":
        return "use consumer-owned Directory.Build.targets or a separate consumer build script"
    if path.startswith("eng/program-kit/web/"):
        return "import the managed SPA adapter from consumer-owned vite.config and configure exact origins there"
    return "use root Directory.Build.props/targets or a feature-owned adapter after the managed import"


def validate_tasks(tasks: Path, manifest: dict, plan: Path | None) -> None:
    plan_text = plan.read_text(encoding="utf-8") if plan else ""
    errors: list[str] = []
    for line_number, path, line in task_paths(tasks):
        entry = matches(path, manifest)
        if entry is None:
            delta = f"STRUCTURE-DELTA: {path}"
            if delta not in line or delta not in plan_text:
                errors.append(
                    f"PKA007 {tasks}:{line_number} unknown path '{path}'; declare it, use an accepted profile convention, "
                    "or add the same explicit STRUCTURE-DELTA to plan and tasks before completion."
                )
            continue
        if entry.get("ownership") == "managed" and re.search(r"\b(add|create|edit|modify|update|delete|write)\b", line, re.IGNORECASE):
            errors.append(f"PKA008 {tasks}:{line_number} task edits managed path '{path}'; {extension_point(path)}.")
    if errors:
        raise ValueError("\n".join(errors))


def main() -> int:
    configure_utf8()
    parser = argparse.ArgumentParser(description="Validate Program Kit artifact ownership and task paths.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--tasks")
    parser.add_argument("--plan")
    args = parser.parse_args()
    try:
        manifest = load_manifest(Path(args.manifest))
        declared = {normalize(str(item.get("path", ""))) for item in manifest["artifacts"] if "path" in item}
        missing = sorted(CANONICAL - declared)
        if missing:
            raise ValueError("PKA009 manifest must predeclare canonical Program Kit artifacts: " + ", ".join(missing))
        if args.tasks:
            validate_tasks(Path(args.tasks), manifest, Path(args.plan) if args.plan else None)
        print("artifact ownership and task paths are valid")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
