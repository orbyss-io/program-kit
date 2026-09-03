from __future__ import annotations

import argparse
import fnmatch
import hashlib
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
GOVERNANCE_CONTEXT = {
    "spec.md": (
        "## Governance Traceability",
        "**Specification roadmap entry**:",
        "**Architecture constraints**:",
        "**Owned contracts and data**:",
    ),
    "plan.md": (
        "## Architecture Realization",
        "**Roadmap entry and status transition**:",
        "**Vertical-slice path**:",
        "**Artifact ownership manifest**:",
    ),
    "tasks.md": (
        "## Governance Completion Evidence",
        "**Roadmap transition**:",
        "**Path and ownership protection**:",
    ),
}
EXTERNAL_HOST_REQUIREMENTS = {
    "ProgramKitFeatureIdentity": "feature identity metadata",
    "shells.json": "shell activation",
    "hostsettings.json": "external-host configuration",
    "ProgramKit.Host": "the external Program Kit host",
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


def negative_path_reference(line: str, start: int) -> bool:
    prefix = line[max(0, start - 120) : start]
    return re.search(
        r"(?:do\s+not|don't|must\s+not|never|without|instead\s+of|rather\s+than|"
        r"prohibit(?:ed)?|forbid(?:den)?|reject|absence\s+of|no\s+custom)\s+[^.;:]{0,80}$",
        prefix,
        re.IGNORECASE,
    ) is not None


def inline_paths(document: Path) -> list[tuple[int, str, str]]:
    result: list[tuple[int, str, str]] = []
    for line_number, line in enumerate(document.read_text(encoding="utf-8").splitlines(), 1):
        for match in re.finditer(r"`([^`]+)`", line):
            token = match.group(1)
            if "://" in token or " " in token or token.startswith("--"):
                continue
            if negative_path_reference(line, match.start()):
                continue
            if "/" in token or re.search(r"\.(?:cs|csproj|json|md|py|ts|tsx|props|targets|yml|yaml)$", token):
                result.append((line_number, normalize(token), line))
    return result


def task_paths(tasks: Path) -> list[tuple[int, str, str]]:
    result: list[tuple[int, str, str]] = []
    for line_number, line in enumerate(tasks.read_text(encoding="utf-8").splitlines(), 1):
        if re.match(r"^\s*-\s*\[[ xX]\]", line) is None:
            continue
        for match in re.finditer(r"`([^`]+)`", line):
            token = match.group(1)
            if "://" in token or " " in token or token.startswith("--"):
                continue
            if negative_path_reference(line, match.start()):
                continue
            if "/" in token or re.search(
                r"\.(?:cs|csproj|json|md|py|ts|tsx|props|targets|yml|yaml)$", token
            ):
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


def validate_governance_context(feature_dir: Path, include_tasks: bool) -> None:
    names = ("spec.md", "plan.md", "tasks.md") if include_tasks else ("spec.md", "plan.md")
    errors: list[str] = []
    for name in names:
        path = feature_dir / name
        if not path.is_file():
            errors.append(f"PKA010 required governed feature artifact is missing: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        missing = [marker for marker in GOVERNANCE_CONTEXT[name] if marker not in text]
        if missing:
            errors.append(
                f"PKA010 {path} is missing mandatory governance context: {', '.join(missing)}"
            )
    if errors:
        raise ValueError("\n".join(errors))


def repository_root(feature_dir: Path) -> Path:
    for candidate in (feature_dir, *feature_dir.parents):
        if (candidate / ".specify").is_dir() or (candidate / "docs/architecture/bootstrap-decisions.json").is_file():
            return candidate
    return feature_dir.parent


def external_program_kit_host_selected(feature_dir: Path, manifest: dict) -> bool:
    if "dotnet" not in {str(value).lower() for value in manifest.get("profiles", [])}:
        return False
    decisions_path = repository_root(feature_dir) / "docs/architecture/bootstrap-decisions.json"
    if not decisions_path.is_file():
        return True
    try:
        decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"PKA011 cannot inspect .NET host authority: {error}") from error
    dotnet = decisions.get("dotnet") if isinstance(decisions, dict) else None
    return not (isinstance(dotnet, dict) and dotnet.get("program_kit_host_opt_out") is True)


def is_custom_host_path(path: str) -> bool:
    normalized = normalize(path)
    lowered = normalized.lower()
    if lowered == "program.cs" or (lowered.startswith("src/") and lowered.endswith("/program.cs")):
        return True
    if not lowered.startswith("src/"):
        return False
    return any(
        segment == "host" or segment.endswith(".host")
        for segment in PurePosixPath(lowered).parts[1:]
    )


def planned_paths(feature_dir: Path, manifest: dict, include_tasks: bool) -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for entry in manifest.get("artifacts", []):
        if isinstance(entry, dict):
            value = entry.get("path", entry.get("pattern"))
            if isinstance(value, str):
                result.append(("artifact-ownership.json", normalize(value)))
    names = ["plan.md", "quickstart.md"]
    if include_tasks:
        names.append("tasks.md")
    names.extend(
        path.relative_to(feature_dir).as_posix()
        for path in sorted((feature_dir / "contracts").glob("*.md"))
        if path.is_file()
    )
    for name in names:
        path = feature_dir / name
        if path.is_file():
            references = task_paths(path) if name == "tasks.md" else inline_paths(path)
            result.extend((f"{name}:{line}", value) for line, value, _ in references)
    return result


def validate_runtime_profile(feature_dir: Path, manifest: dict, include_tasks: bool) -> None:
    if not external_program_kit_host_selected(feature_dir, manifest):
        return
    paths = planned_paths(feature_dir, manifest, include_tasks)
    custom = sorted({f"{source} -> {path}" for source, path in paths if is_custom_host_path(path)})
    if custom:
        raise ValueError(
            "PKA011 external ProgramKit.Host profile forbids a repository-owned host project or "
            "Program.cs; create packable feature projects and external-host activation/release inputs instead: "
            + "; ".join(custom)
        )
    documents = [feature_dir / "plan.md", feature_dir / "quickstart.md"]
    if include_tasks:
        documents.append(feature_dir / "tasks.md")
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in documents if path.is_file()
    )
    has_dotnet_project = any(path.lower().endswith(".csproj") for _, path in paths)
    if not has_dotnet_project:
        return
    missing = [label for marker, label in EXTERNAL_HOST_REQUIREMENTS.items() if marker not in combined]
    if not re.search(r"(?:runnable_host\.py\s+stage|package[- ]closure\s+stag)", combined, re.IGNORECASE):
        missing.append("validated package-closure staging")
    if not any(
        marker in combined
        for marker in (".program-kit/evidence/host-image.json", "runnable-host.json", "digest-pinned")
    ):
        missing.append("digest-bound external-host release evidence")
    if missing:
        raise ValueError(
            "PKA012 .NET feature planning is incomplete for the external ProgramKit.Host profile; "
            "missing " + ", ".join(missing) + "."
        )


def validate_npm_graph_evidence(feature_dir: Path, manifest: dict) -> None:
    profiles = {str(value).lower() for value in manifest.get("profiles", [])}
    if not profiles & {"typescript-vite", "typescript-web", "browser-web"}:
        return
    plan = feature_dir / "plan.md"
    if not plan.is_file():
        return
    plan_text = plan.read_text(encoding="utf-8")
    if not re.search(
        r"(?:\bnpm\b|openapi-typescript|devDependencies|dependency graph|client generator)",
        plan_text,
        re.IGNORECASE,
    ):
        return
    evidence_path = repository_root(feature_dir) / ".program-kit/evidence/npm-graph.json"
    try:
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            "PKA013 TypeScript/npm planning requires current strict peer-resolution evidence at "
            f"{evidence_path}: {error}"
        ) from error
    if not isinstance(evidence, dict) or evidence.get("satisfied") is not True:
        raise ValueError("PKA013 npm graph evidence does not record a successful strict resolution")
    package_json = Path(str(evidence.get("packageJson", "")))
    if not package_json.is_absolute():
        package_json = repository_root(feature_dir) / package_json
    try:
        package_json.resolve().relative_to(repository_root(feature_dir).resolve())
    except ValueError as error:
        raise ValueError("PKA013 npm candidate manifest must stay inside the repository") from error
    if not package_json.is_file():
        raise ValueError(f"PKA013 npm candidate manifest is missing: {package_json}")
    actual = hashlib.sha256(package_json.read_bytes()).hexdigest()
    if evidence.get("packageJsonSha256") != actual:
        raise ValueError("PKA013 npm graph evidence is stale for its candidate package manifest")


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
        feature_dir = Path(args.manifest).resolve().parent
        validate_governance_context(feature_dir, bool(args.tasks))
        validate_runtime_profile(feature_dir, manifest, bool(args.tasks))
        validate_npm_graph_evidence(feature_dir, manifest)
        if args.tasks:
            validate_tasks(Path(args.tasks), manifest, Path(args.plan) if args.plan else None)
        print("artifact ownership and task paths are valid")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
