from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path


CONSTITUTION = Path(".specify/memory/constitution.md")
RATIFICATION = Path(".specify/memory/constitution-ratification.json")
ROADMAP = Path("docs/architecture/specification-roadmap.md")
ARCHITECTURE = Path("docs/architecture/architecture.md")
TRACEABILITY = Path("docs/architecture/traceability.md")
DECISIONS = Path("docs/architecture/decisions")
ASSESSMENT = Path("docs/architecture/bootstrap-assessment.md")
DECISION_BACKLOG = Path("docs/architecture/decision-backlog.md")
TOOLING_EVALUATION = Path("docs/architecture/tooling-evaluation.md")
BOOTSTRAP_DECISIONS = Path("docs/architecture/bootstrap-decisions.json")
ASSESSMENT_REVIEW = Path("docs/architecture/reviews/assessment-review.md")
CONSTITUTION_REVIEW = Path("docs/architecture/reviews/constitution-review.md")
BOOTSTRAP_REVIEW = Path("docs/architecture/reviews/bootstrap-review.md")
ASSESSMENT_APPROVAL = Path(".specify/governance/bootstrap-assessment-approval.json")
BOOTSTRAP_APPROVAL = Path(".specify/governance/bootstrap-approval.json")
BOOTSTRAP_COMPLETION = Path(".specify/governance/bootstrap-completion.json")
READINESS_REPORT = Path("docs/architecture/readiness-report.md")
CONFIGURATION = Path(
    ".specify/extensions/program-kit-governance/program-kit-governance-config.yml"
)
LOCAL_CONFIGURATION = Path(
    ".specify/extensions/program-kit-governance/program-kit-governance-config.local.yml"
)
EXTENSION_MANIFEST = Path(".specify/extensions/program-kit-governance/extension.yml")
DOTNET_EXTENSION_MANIFEST = Path(".specify/extensions/program-kit-dotnet/extension.yml")
WORKFLOW_MANIFEST = Path(".specify/workflows/program-kit-bootstrap/workflow.yml")
WORKFLOW_REGISTRY = Path(".specify/workflows/workflow-registry.json")
BUNDLE_RECORDS = Path(".specify/bundle-records.json")
INTEGRATION_STATE = Path(".specify/integration.json")
STATUSES = {"Candidate", "Blocked", "Ready", "Active", "Delivered", "Superseded"}
ROADMAP_VIEW_START = "<!-- PROGRAM-KIT:ROADMAP-VIEW:START -->"
ROADMAP_VIEW_END = "<!-- PROGRAM-KIT:ROADMAP-VIEW:END -->"
REQUIRED_RECORD_FIELDS = {
    "User-visible outcome",
    "Scope",
    "Non-goals",
    "Required Accepted ADRs",
    "Dependencies",
    "Owned public contracts",
    "Owned lifecycle portions",
    "Owned data",
    "Quality scenarios",
    "Verification responsibility",
    "Recommended sequence",
    "Status",
}
DECISION_SOURCES = {
    "explicit-intake",
    "program-kit-default",
    "derived-default",
    "override",
}
ASSESSMENT_ARTIFACTS = (
    ASSESSMENT,
    DECISION_BACKLOG,
    TOOLING_EVALUATION,
    BOOTSTRAP_DECISIONS,
    ASSESSMENT_REVIEW,
)
class GovernanceStateError(ValueError):
    pass


def bootstrap_artifacts() -> tuple[Path, ...]:
    """Resolve configurable roadmap and decision paths at operation time."""
    return (
        Path("docs/architecture/README.md"),
        ARCHITECTURE,
        Path("docs/architecture/quality-attributes.md"),
        Path("docs/architecture/technology-radar.md"),
        TRACEABILITY,
        DECISION_BACKLOG,
        TOOLING_EVALUATION,
        Path("docs/architecture/quality-system.md"),
        ROADMAP,
        DECISIONS / "README.md",
        DECISIONS / "bootstrap-baseline.md",
        BOOTSTRAP_DECISIONS,
        BOOTSTRAP_REVIEW,
    )


def _parse_scalar(value: str) -> str | bool:
    value = value.strip()
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value


def _parse_simple_yaml(path: Path) -> dict[str, object]:
    """Read the deliberately small mapping-only configuration without PyYAML."""
    result: dict[str, object] = {}
    current: dict[str, object] | None = None
    for number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.split("#", 1)[0].rstrip()
        if not line:
            continue
        top = re.fullmatch(r"([A-Za-z][A-Za-z0-9_-]*):\s*", line)
        nested = re.fullmatch(r"  ([A-Za-z][A-Za-z0-9_-]*):\s*(.+)", line)
        if top:
            current = {}
            result[top.group(1)] = current
        elif nested and current is not None:
            current[nested.group(1)] = _parse_scalar(nested.group(2))
        else:
            raise GovernanceStateError(
                f"Invalid Program Kit configuration at {path}:{number}; use the supplied mapping-only template"
            )
    return result


def _load_configuration(path: Path) -> dict[str, object]:
    if not path.is_file():
        return {}
    try:
        import yaml  # type: ignore[import-not-found]
    except ModuleNotFoundError:
        value = _parse_simple_yaml(path)
    else:
        try:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise GovernanceStateError(f"Invalid Program Kit configuration {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GovernanceStateError(f"Program Kit configuration must be a mapping: {path}")
    return value


def _configured_relative_path(value: object, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise GovernanceStateError(f"Program Kit configuration {label} must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise GovernanceStateError(f"Program Kit configuration {label} must stay within the project")
    return path


def configure_paths() -> None:
    """Apply installed and local configuration before a CLI lifecycle operation."""
    global CONSTITUTION, RATIFICATION, ROADMAP, DECISIONS
    installed = _load_configuration(project_path(CONFIGURATION))
    local = _load_configuration(project_path(LOCAL_CONFIGURATION))

    def configured(section: str, key: str, default: Path) -> Path:
        value: object = default.as_posix()
        for document in (installed, local):
            candidate = document.get(section)
            if isinstance(candidate, dict) and key in candidate:
                value = candidate[key]
        return _configured_relative_path(value, f"{section}.{key}")

    CONSTITUTION = configured("constitution", "document", CONSTITUTION)
    RATIFICATION = configured("constitution", "ratification", RATIFICATION)
    ROADMAP = configured("architecture", "specification_roadmap", ROADMAP)
    DECISIONS = configured("architecture", "decisions", DECISIONS)


def manifest_version(path: Path, component: str) -> str:
    if not path.is_file():
        raise GovernanceStateError(f"Installed {component} manifest is missing: {path}")
    match = re.search(
        r"^\s{2}version:\s*[\"']?([^\"'#\s]+)",
        path.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    if not match:
        raise GovernanceStateError(f"Installed {component} manifest has no version: {path}")
    return match.group(1)


def repair_commands() -> str:
    integration = "auto"
    state_path = project_path(INTEGRATION_STATE)
    if state_path.is_file():
        state = read_json(state_path)
        candidate = state.get("default_integration") or state.get("integration")
        if isinstance(candidate, str) and re.fullmatch(r"[A-Za-z0-9_-]+", candidate.strip()):
            integration = candidate.strip()
    return (
        "specify workflow update program-kit-bootstrap\n"
        f"specify bundle update program-kit --integration {integration}"
    )


def validate_installation() -> dict[str, str]:
    versions = {
        "extension": manifest_version(
            project_path(EXTENSION_MANIFEST), "Program Kit Governance extension"
        ),
        "dotnet extension": manifest_version(
            project_path(DOTNET_EXTENSION_MANIFEST), "Program Kit .NET extension"
        ),
        "workflow": manifest_version(
            project_path(WORKFLOW_MANIFEST), "Program Kit Bootstrap workflow"
        ),
    }
    registry_path = project_path(WORKFLOW_REGISTRY)
    if not registry_path.is_file():
        raise GovernanceStateError(
            f"Workflow registry is missing: {registry_path}\n"
            f"Repair the installation, in this order:\n{repair_commands()}"
        )
    registry = read_json(registry_path)
    workflows = registry.get("workflows")
    entry = workflows.get("program-kit-bootstrap") if isinstance(workflows, dict) else None
    registry_version = entry.get("version") if isinstance(entry, dict) else None
    if not isinstance(registry_version, str):
        raise GovernanceStateError(
            f"Program Kit Bootstrap is absent from the workflow registry: {registry_path}\n"
            f"Repair the installation, in this order:\n{repair_commands()}"
        )
    versions["workflow registry"] = registry_version

    records_path = project_path(BUNDLE_RECORDS)
    if not records_path.is_file():
        raise GovernanceStateError(
            f"Bundle records are missing: {records_path}\n"
            f"Repair the installation, in this order:\n{repair_commands()}"
        )
    records = read_json(records_path).get("bundles")
    bundle = next(
        (
            record
            for record in records or []
            if isinstance(record, dict) and record.get("bundle_id") == "program-kit"
        ),
        None,
    )
    if not isinstance(bundle, dict) or not isinstance(bundle.get("version"), str):
        raise GovernanceStateError(
            f"Program Kit is absent from the bundle records: {records_path}\n"
            f"Repair the installation, in this order:\n{repair_commands()}"
        )
    versions["bundle record"] = bundle["version"]
    components = bundle.get("contributed_components")
    governance_extension = next(
        (
            component
            for component in components or []
            if isinstance(component, dict)
            and component.get("kind") == "extensions"
            and component.get("id") == "program-kit-governance"
        ),
        None,
    )
    if not isinstance(governance_extension, dict) or not isinstance(governance_extension.get("version"), str):
        raise GovernanceStateError(
            "Program Kit Governance is absent from the Program Kit bundle record.\n"
            f"Repair the installation, in this order:\n{repair_commands()}"
        )
    versions["bundle governance extension record"] = governance_extension["version"]
    dotnet_extension = next(
        (
            component
            for component in components or []
            if isinstance(component, dict)
            and component.get("kind") == "extensions"
            and component.get("id") == "program-kit-dotnet"
        ),
        None,
    )
    if not isinstance(dotnet_extension, dict) or not isinstance(dotnet_extension.get("version"), str):
        raise GovernanceStateError(
            "Program Kit .NET is absent from the Program Kit bundle record.\n"
            f"Repair the installation, in this order:\n{repair_commands()}"
        )
    versions["bundle .NET extension record"] = dotnet_extension["version"]

    if len(set(versions.values())) != 1:
        details = ", ".join(f"{name}={version}" for name, version in versions.items())
        raise GovernanceStateError(
            f"Program Kit installation is version-incoherent ({details}). Spec Kit 1.0.1 "
            "cannot refresh the separately installed workflow through bundle update. Do not "
            "run bootstrap between repair commands. Repair the installation, in this order:\n"
            f"{repair_commands()}"
        )
    return versions


def project_path(relative: Path) -> Path:
    root = Path.cwd().resolve()
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise GovernanceStateError(f"Governance path escaped the project: {resolved}") from exc
    return resolved


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(value, encoding="utf-8", newline="\n")
    temporary.replace(path)


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GovernanceStateError(f"Invalid governance state file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GovernanceStateError(f"Governance state file must be an object: {path}")
    return value


def constitution_metadata(path: Path, *, allow_pending: bool = False) -> tuple[str, str, str]:
    if not path.is_file():
        raise GovernanceStateError(f"Constitution is missing: {path}")
    text = path.read_text(encoding="utf-8")
    if re.search(r"TODO\s*\(", text, re.IGNORECASE):
        raise GovernanceStateError("Constitution contains a TODO and cannot be ratified")
    placeholders = sorted(set(re.findall(r"\[[A-Z][A-Z0-9_]+\]", text)))
    if placeholders:
        raise GovernanceStateError(
            "Constitution contains template placeholders: " + ", ".join(placeholders)
        )
    if not re.search(r"^## Governance\s*$", text, re.MULTILINE):
        raise GovernanceStateError("Constitution is missing the Governance section")
    governance = text.split("## Governance", 1)[1]
    for term in ("amend", "version", "compliance"):
        if term not in governance.lower():
            raise GovernanceStateError(
                f"Constitution governance does not define {term} policy"
            )
    ratified_pattern = r"(?:\d{4}-\d{2}-\d{2}|PENDING_RATIFICATION)" if allow_pending else r"\d{4}-\d{2}-\d{2}"
    match = re.search(
        r"\*\*Version\*\*:\s*([^|\s]+)\s*\|\s*"
        rf"\*\*Ratified\*\*:\s*({ratified_pattern})\s*\|\s*"
        r"\*\*Last Amended\*\*:\s*(\d{4}-\d{2}-\d{2})",
        text,
    )
    if not match:
        raise GovernanceStateError(
            "Constitution must declare Version, Ratified, and Last Amended metadata"
        )
    version, ratified, amended = match.groups()
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?", version):
        raise GovernanceStateError(f"Constitution version is not semantic: {version}")
    for label, value in (("Ratified", ratified), ("Last Amended", amended)):
        if value == "PENDING_RATIFICATION":
            continue
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise GovernanceStateError(f"{label} date is invalid: {value}") from exc
    return version, ratified, amended


def _require_files(paths: tuple[Path, ...], label: str) -> list[Path]:
    resolved = [project_path(path) for path in paths]
    missing = [path for path in resolved if not path.is_file()]
    if missing:
        details = ", ".join(str(path) for path in missing)
        raise GovernanceStateError(f"{label} is incomplete; missing required files: {details}")
    return resolved


def _artifact_hashes(paths: tuple[Path, ...]) -> dict[str, str]:
    return {path.as_posix(): sha256(project_path(path)) for path in paths}


def _review_basis(paths: tuple[Path, ...]) -> str:
    canonical = json.dumps(_artifact_hashes(paths), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_review_basis(review: Path, paths: tuple[Path, ...], label: str) -> None:
    expected = _review_basis(paths)
    text = project_path(review).read_text(encoding="utf-8")
    if f"Review basis SHA-256: `{expected}`" not in text:
        raise GovernanceStateError(
            f"{label} review packet is stale; regenerate it before approval"
        )


def _verify_artifact_hashes(record: dict, paths: tuple[Path, ...], label: str) -> None:
    expected = _artifact_hashes(paths)
    recorded = record.get("artifacts")
    if recorded != expected:
        raise GovernanceStateError(f"{label} artifacts changed after human approval")


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GovernanceStateError(f"{label} must be a non-empty string")
    return value.strip()


def validate_bootstrap_decisions() -> dict:
    path = project_path(BOOTSTRAP_DECISIONS)
    value = read_json(path)
    if value.get("schema_version") != "1.0":
        raise GovernanceStateError("Bootstrap decisions must use schema_version 1.0")
    profile = value.get("default_profile")
    if not isinstance(profile, dict):
        raise GovernanceStateError("Bootstrap decisions have no default_profile")
    profile_id = _require_string(profile.get("id"), "Bootstrap default_profile.id")
    profile_version = _require_string(
        profile.get("version"), "Bootstrap default_profile.version"
    )
    if profile_id != "program-kit-standard":
        raise GovernanceStateError(
            "Bootstrap default_profile.id must be 'program-kit-standard'"
        )
    installed_version = manifest_version(
        project_path(EXTENSION_MANIFEST), "Program Kit Governance extension"
    )
    if profile_version != installed_version:
        raise GovernanceStateError(
            "Bootstrap default-profile version does not match the installed Program Kit version: "
            f"{profile_version} != {installed_version}"
        )

    choices = value.get("choices")
    if not isinstance(choices, list) or not choices:
        raise GovernanceStateError("Bootstrap decisions must contain at least one adopted choice")
    seen: set[str] = set()
    for index, choice in enumerate(choices):
        if not isinstance(choice, dict):
            raise GovernanceStateError(f"Bootstrap choice {index + 1} must be an object")
        choice_id = _require_string(choice.get("id"), f"Bootstrap choice {index + 1}.id")
        if choice_id in seen:
            raise GovernanceStateError(f"Duplicate bootstrap choice id: {choice_id}")
        seen.add(choice_id)
        _require_string(choice.get("decision"), f"Bootstrap choice {choice_id}.decision")
        source = _require_string(choice.get("source"), f"Bootstrap choice {choice_id}.source")
        if source not in DECISION_SOURCES:
            raise GovernanceStateError(
                f"Bootstrap choice {choice_id} has invalid source {source!r}; "
                f"expected one of {sorted(DECISION_SOURCES)}"
            )
        _require_string(choice.get("rationale"), f"Bootstrap choice {choice_id}.rationale")
        _require_string(choice.get("override"), f"Bootstrap choice {choice_id}.override")

    collection_text_fields = {
        "overrides": "decision",
        "unresolved": "question",
        "deferred": "question",
        "acknowledgements": "summary",
    }
    for collection_name, text_field in collection_text_fields.items():
        collection = value.get(collection_name, [])
        if not isinstance(collection, list) or not all(isinstance(item, dict) for item in collection):
            raise GovernanceStateError(f"Bootstrap decisions {collection_name} must be a list of objects")
        collection_ids: set[str] = set()
        for index, item in enumerate(collection):
            item_id = _require_string(
                item.get("id"), f"Bootstrap {collection_name} item {index + 1}.id"
            )
            if item_id in collection_ids:
                raise GovernanceStateError(
                    f"Duplicate bootstrap {collection_name} id: {item_id}"
                )
            collection_ids.add(item_id)
            _require_string(
                item.get(text_field),
                f"Bootstrap {collection_name} item {item_id}.{text_field}",
            )
            if collection_name == "unresolved":
                _require_string(item.get("blocks"), f"Bootstrap unresolved item {item_id}.blocks")
            elif collection_name == "deferred":
                _require_string(item.get("trigger"), f"Bootstrap deferred item {item_id}.trigger")

    selected_profiles = value.get("selected_profiles")
    if not isinstance(selected_profiles, list) or not all(
        isinstance(item, str) and item for item in selected_profiles
    ):
        raise GovernanceStateError("Bootstrap decisions selected_profiles must be a list of strings")
    if len({item.lower() for item in selected_profiles}) != len(selected_profiles):
        raise GovernanceStateError("Bootstrap decisions selected_profiles contains duplicates")
    if "dotnet" in {item.lower() for item in selected_profiles}:
        dotnet = value.get("dotnet")
        if not isinstance(dotnet, dict):
            raise GovernanceStateError("A selected .NET profile requires a dotnet decision block")
        opt_out_value = dotnet.get("program_kit_host_opt_out")
        if not isinstance(opt_out_value, bool):
            raise GovernanceStateError(
                "Bootstrap dotnet.program_kit_host_opt_out must be a boolean"
            )
        opted_out = opt_out_value
        host = _require_string(dotnet.get("host_runtime"), "Bootstrap dotnet.host_runtime")
        host_source = _require_string(dotnet.get("host_source"), "Bootstrap dotnet.host_source")
        if host_source not in DECISION_SOURCES:
            raise GovernanceStateError(
                f"Bootstrap dotnet.host_source has invalid source {host_source!r}; "
                f"expected one of {sorted(DECISION_SOURCES)}"
            )
        if opted_out:
            _require_string(dotnet.get("opt_out_reason"), "Bootstrap dotnet.opt_out_reason")
            if host == "ProgramKit.Host":
                raise GovernanceStateError(
                    "A ProgramKit.Host opt-out must select an alternate host runtime"
                )
            if host_source not in {"explicit-intake", "override"}:
                raise GovernanceStateError(
                    "A ProgramKit.Host opt-out must come from explicit intake or an override"
                )
        elif host != "ProgramKit.Host":
            raise GovernanceStateError(
                "ProgramKit.Host is the automatic .NET default; select it or record an explicit opt-out"
            )
        if not opted_out:
            acknowledgements = value.get("acknowledgements", [])
            ids = {item.get("id") for item in acknowledgements if isinstance(item, dict)}
            if "program-kit-preview-dependencies" not in ids:
                raise GovernanceStateError(
                    "ProgramKit.Host selection must disclose the pinned preview packages and package sources"
                )
    return value


def _list_items(items: object, field: str, empty: str, *, limit: int = 15) -> list[str]:
    if not isinstance(items, list) or not items:
        return [f"- {empty}"]
    result: list[str] = []
    for item in items[:limit]:
        if isinstance(item, dict):
            item_id = re.sub(r"\s+", " ", str(item.get("id", "item"))).replace("`", "'")
            text = re.sub(
                r"\s+",
                " ",
                str(item.get(field, item.get("summary", item.get("question", "")))),
            ).replace("`", "'")
            result.append(f"- `{item_id}`: {text}")
    if len(items) > limit:
        result.append(
            f"- ... {len(items) - limit} more; review `{BOOTSTRAP_DECISIONS.as_posix()}`"
        )
    return result or [f"- {empty}"]


def write_review(stage: str) -> None:
    decisions = validate_bootstrap_decisions()
    if stage == "assessment":
        required = (ASSESSMENT, DECISION_BACKLOG, TOOLING_EVALUATION, BOOTSTRAP_DECISIONS)
        _require_files(required, "Assessment review")
        choices = decisions["choices"]
        explicit = [item for item in choices if item.get("source") == "explicit-intake"]
        defaults = [item for item in choices if item.get("source") in {"program-kit-default", "derived-default"}]
        lines = [
            "# Assessment review packet",
            "",
            "## Decision requested",
            "",
            "Approve the explicit intake choices and Program Kit defaults below as the provisional bootstrap baseline. Reject to keep the run paused for revision.",
            "",
            "## Files under review",
            "",
            *[f"- `{path.as_posix()}`" for path in required],
            "",
            "## Explicit intake choices",
            "",
            *_list_items(explicit, "decision", "None detected"),
            "",
            "## Program Kit and derived defaults",
            "",
            *_list_items(defaults, "decision", "None applied"),
            "",
            "## Overrides",
            "",
            *_list_items(decisions.get("overrides"), "decision", "None"),
            "",
            "## Consequential acknowledgements",
            "",
            *_list_items(decisions.get("acknowledgements"), "summary", "None"),
            "",
            "## Genuine unresolved decisions",
            "",
            *_list_items(decisions.get("unresolved"), "question", "None"),
            "",
            "## Deferred until triggered",
            "",
            *_list_items(decisions.get("deferred"), "question", "None"),
            "",
            "## After rejection",
            "",
            "Revise the files above, then regenerate and revalidate this packet before resuming:",
            "",
            "```powershell",
            "python .specify/extensions/program-kit-governance/scripts/governance_state.py write-review --stage assessment",
            "```",
            "",
            "## Automated validation",
            "",
            f"- Review basis SHA-256: `{_review_basis(required)}`",
            "- Required assessment artifacts exist.",
            "- The bootstrap decision register is structurally valid.",
            "- For .NET, `ProgramKit.Host` is selected unless an explicit intake opt-out is recorded.",
        ]
        write_text(project_path(ASSESSMENT_REVIEW), "\n".join(lines) + "\n")
        print(f"Assessment review packet written: {project_path(ASSESSMENT_REVIEW)}")
        return
    if stage == "constitution":
        validate_constitution_draft()
        constitution = project_path(CONSTITUTION)
        text = constitution.read_text(encoding="utf-8")
        headings = re.findall(r"^#{2,3}\s+(.+?)\s*$", text, re.MULTILINE)
        version, ratified, amended = constitution_metadata(constitution, allow_pending=True)
        lines = [
            "# Constitution review packet",
            "",
            "## Decision requested",
            "",
            "Ratify the complete constitution. Approval deterministically changes only its Draft status and an initial `PENDING_RATIFICATION` date before hash-binding the final content. Reject keeps the run paused for revision.",
            "",
            "## File under review",
            "",
            f"- `{CONSTITUTION.as_posix()}`",
            "",
            "## Metadata",
            "",
            f"- Version: `{version}`",
            f"- Ratification value before approval: `{ratified}`",
            f"- Last amended: `{amended}`",
            "",
            "## Principles and governed sections",
            "",
            *[f"- {heading}" for heading in headings[:30]],
            "",
            "## After rejection",
            "",
            "Revise the constitution, then regenerate and revalidate this packet before resuming:",
            "",
            "```powershell",
            "python .specify/extensions/program-kit-governance/scripts/governance_state.py write-review --stage constitution",
            "```",
            "",
            "## Automated validation",
            "",
            f"- Review basis SHA-256: `{_review_basis((CONSTITUTION, ASSESSMENT_APPROVAL))}`",
            "- Draft status is explicit.",
            "- No TODOs or template placeholders remain.",
            "- Semantic version, amendment policy, versioning policy, and compliance governance are present.",
            "- The assessment approval still matches the reviewed bootstrap decisions.",
        ]
        write_text(project_path(CONSTITUTION_REVIEW), "\n".join(lines) + "\n")
        print(f"Constitution review packet written: {project_path(CONSTITUTION_REVIEW)}")
        return
    if stage == "bootstrap":
        validate_bootstrap(False, False)
        artifacts = bootstrap_artifacts()
        rows = []
        for relative in artifacts[:-1]:
            path = project_path(relative)
            rows.append(f"- `{relative.as_posix()}` ({path.stat().st_size} bytes)")
        accepted = 0
        proposed = 0
        for path in project_path(DECISIONS).glob("*.md"):
            text = path.read_text(encoding="utf-8")
            if re.search(r"(?:^|[-*]\s*)Status:\s*Accepted\s*$", text, re.MULTILINE | re.IGNORECASE):
                accepted += 1
            elif re.search(r"(?:^|[-*]\s*)Status:\s*Proposed\s*$", text, re.MULTILINE | re.IGNORECASE):
                proposed += 1
        roadmap_statuses = re.findall(
            r"^-\s+\*\*Status\*\*:\s*(\w+)\s*$",
            project_path(ROADMAP).read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        lines = [
            "# Bootstrap review packet",
            "",
            "## Decision requested",
            "",
            "Approve the generated architecture baseline and its adoption of explicit intake choices and Program Kit defaults. Approval does not accept separately Proposed ADRs. Reject keeps the run paused for revision.",
            "",
            "## Files under review",
            "",
            *rows,
            "",
            "## Decision status",
            "",
            f"- Accepted ADRs: {accepted}",
            f"- Proposed ADRs requiring separate later decisions: {proposed}",
            f"- Roadmap statuses: {', '.join(roadmap_statuses) if roadmap_statuses else 'none'}",
            "",
            "## Exceptions and unresolved decisions",
            "",
            *_list_items(decisions.get("overrides"), "decision", "No default overrides"),
            *_list_items(decisions.get("unresolved"), "question", "No immediate unresolved decisions"),
            "",
            "## After rejection",
            "",
            "Revise the listed artifacts, then regenerate and revalidate this packet before resuming:",
            "",
            "```powershell",
            "python .specify/extensions/program-kit-governance/scripts/governance_state.py write-review --stage bootstrap",
            "```",
            "",
            "## Automated validation",
            "",
            f"- Review basis SHA-256: `{_review_basis(artifacts[:-1])}`",
            "- Constitution ratification is current and hash-valid.",
            "- Every required architecture, decision, tooling, quality, traceability, and roadmap artifact exists.",
            "- The bootstrap baseline ADR is Accepted.",
            "- ProgramKit.Host appears in the accepted baseline when .NET is selected without an opt-out.",
            "- The roadmap is structurally valid.",
        ]
        write_text(project_path(BOOTSTRAP_REVIEW), "\n".join(lines) + "\n")
        print(f"Bootstrap review packet written: {project_path(BOOTSTRAP_REVIEW)}")
        return
    raise GovernanceStateError(f"Unknown review stage: {stage}")


def validate_assessment() -> dict:
    _require_files((ASSESSMENT, DECISION_BACKLOG, TOOLING_EVALUATION, BOOTSTRAP_DECISIONS), "Assessment")
    return validate_bootstrap_decisions()


def accept_assessment(verdict: str) -> None:
    if verdict != "approve":
        raise GovernanceStateError("Assessment acceptance requires the human gate verdict 'approve'")
    validate_assessment()
    _require_files(ASSESSMENT_ARTIFACTS, "Assessment review")
    _require_review_basis(
        ASSESSMENT_REVIEW,
        (ASSESSMENT, DECISION_BACKLOG, TOOLING_EVALUATION, BOOTSTRAP_DECISIONS),
        "Assessment",
    )
    write_json(
        project_path(ASSESSMENT_APPROVAL),
        {
            "schema_version": "1.0",
            "status": "Approved",
            "gate_verdict": verdict,
            "artifacts": _artifact_hashes(ASSESSMENT_ARTIFACTS),
        },
    )
    print(f"Assessment choices and defaults are approved: {project_path(ASSESSMENT_APPROVAL)}")


def validate_assessment_approval() -> dict:
    path = project_path(ASSESSMENT_APPROVAL)
    record = read_json(path)
    if record.get("status") != "Approved" or record.get("gate_verdict") != "approve":
        raise GovernanceStateError("Bootstrap assessment has no completed human approval")
    validate_assessment()
    _require_files(ASSESSMENT_ARTIFACTS, "Assessment review")
    _verify_artifact_hashes(record, ASSESSMENT_ARTIFACTS, "Bootstrap assessment")
    return record


def validate_constitution_draft() -> None:
    validate_assessment_approval()
    marker = project_path(RATIFICATION)
    if not marker.is_file() or read_json(marker).get("status") != "Draft":
        raise GovernanceStateError("Constitution must be in Draft state for review")
    constitution = project_path(CONSTITUTION)
    constitution_metadata(constitution, allow_pending=True)
    text = constitution.read_text(encoding="utf-8")
    if not re.search(r"^\*\*Status\*\*:\s*Draft(?:\s.*)?$", text, re.MULTILINE):
        raise GovernanceStateError("Constitution review requires an explicit Draft status")


def _finalize_constitution_for_ratification(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "**Ratified**: PENDING_RATIFICATION" in text:
        text = text.replace(
            "**Ratified**: PENDING_RATIFICATION",
            f"**Ratified**: {date.today().isoformat()}",
            1,
        )
    updated, count = re.subn(
        r"^\*\*Status\*\*:\s*Draft(?:\s.*)?$",
        "**Status**: Ratified",
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise GovernanceStateError("Constitution has no unique Draft status to finalize")
    write_text(path, updated)


def begin() -> None:
    marker = project_path(RATIFICATION)
    previous = None
    if marker.is_file():
        current = read_json(marker)
        if current.get("status") == "Ratified":
            previous = current
    value = {
        "schema_version": "1.0",
        "status": "Draft",
        "constitution": {"path": CONSTITUTION.as_posix()},
        "reason": "Constitution drafting or amendment is in progress",
    }
    if previous is not None:
        value["previous_ratification"] = previous
    write_json(marker, value)
    print(f"Constitution state is Draft: {marker}")


def ratify(verdict: str) -> None:
    if verdict != "ratify":
        raise GovernanceStateError("Ratification requires the human gate verdict 'ratify'")
    constitution = project_path(CONSTITUTION)
    marker = project_path(RATIFICATION)
    if not marker.is_file() or read_json(marker).get("status") != "Draft":
        raise GovernanceStateError("Constitution must be in Draft state before ratification")
    _require_files((CONSTITUTION_REVIEW,), "Constitution review")
    _require_review_basis(
        CONSTITUTION_REVIEW,
        (CONSTITUTION, ASSESSMENT_APPROVAL),
        "Constitution",
    )
    _finalize_constitution_for_ratification(constitution)
    version, ratified, amended = constitution_metadata(constitution)
    write_json(
        marker,
        {
            "schema_version": "1.0",
            "status": "Ratified",
            "constitution": {
                "path": CONSTITUTION.as_posix(),
                "version": version,
                "sha256": sha256(constitution),
                "ratified": ratified,
                "last_amended": amended,
            },
            "gate_verdict": verdict,
            "approval_source": CONSTITUTION_REVIEW.as_posix(),
        },
    )
    print(f"Constitution {version} is ratified and hash-bound: {marker}")


def validate_ratification() -> dict:
    constitution = project_path(CONSTITUTION)
    marker = project_path(RATIFICATION)
    record = read_json(marker)
    if record.get("status") != "Ratified" or record.get("gate_verdict") != "ratify":
        raise GovernanceStateError("Constitution has no completed human ratification")
    version, ratified, amended = constitution_metadata(constitution)
    if not re.search(
        r"^\*\*Status\*\*:\s*Ratified\s*$",
        constitution.read_text(encoding="utf-8"),
        re.MULTILINE,
    ):
        raise GovernanceStateError("Constitution document status is not Ratified")
    recorded = record.get("constitution")
    if not isinstance(recorded, dict):
        raise GovernanceStateError("Ratification record has no constitution metadata")
    expected = {
        "path": CONSTITUTION.as_posix(),
        "version": version,
        "sha256": sha256(constitution),
        "ratified": ratified,
        "last_amended": amended,
    }
    if recorded != expected:
        raise GovernanceStateError(
            "Constitution content or metadata changed after ratification; ratify the new draft"
        )
    return record


def validate_bootstrap(require_approval: bool, require_ready: bool) -> None:
    assessment_approval = validate_assessment_approval()
    validate_ratification()
    artifacts = bootstrap_artifacts()
    _require_files(artifacts[:-1], "Architecture bootstrap")
    decisions = validate_bootstrap_decisions()
    baseline = project_path(DECISIONS / "bootstrap-baseline.md")
    baseline_text = baseline.read_text(encoding="utf-8")
    if not re.search(
        r"(?:^|[-*]\s*)Status:\s*Accepted\s*$",
        baseline_text,
        re.MULTILINE | re.IGNORECASE,
    ):
        raise GovernanceStateError("Bootstrap baseline decision must be Accepted")
    approved_artifacts = assessment_approval.get("artifacts")
    decision_hash = (
        approved_artifacts.get(BOOTSTRAP_DECISIONS.as_posix())
        if isinstance(approved_artifacts, dict)
        else None
    )
    if not isinstance(decision_hash, str) or decision_hash not in baseline_text:
        raise GovernanceStateError(
            "Bootstrap baseline decision must cite the exact approved decision-register hash"
        )
    profile = decisions["default_profile"]
    baseline_evidence = [profile["id"], profile["version"]]
    for collection_name in ("choices", "overrides", "acknowledgements"):
        baseline_evidence.extend(
            item["id"] for item in decisions.get(collection_name, [])
        )
    missing_evidence = [item for item in baseline_evidence if item not in baseline_text]
    if missing_evidence:
        raise GovernanceStateError(
            "Bootstrap baseline decision does not trace all approved choices: "
            + ", ".join(missing_evidence)
        )
    selected_profiles = {item.lower() for item in decisions.get("selected_profiles", [])}
    dotnet = decisions.get("dotnet")
    if "dotnet" in selected_profiles and isinstance(dotnet, dict):
        if dotnet.get("program_kit_host_opt_out") is not True:
            combined = (
                project_path(Path("docs/architecture/architecture.md")).read_text(encoding="utf-8")
                + "\n"
                + project_path(Path("docs/architecture/technology-radar.md")).read_text(encoding="utf-8")
                + "\n"
                + baseline_text
            )
            if "ProgramKit.Host" not in combined:
                raise GovernanceStateError(
                    "The accepted .NET baseline must adopt ProgramKit.Host unless intake explicitly opts out"
                )
    validate_roadmap(require_ready)
    validate_bootstrap_consistency()
    if require_approval:
        path = project_path(BOOTSTRAP_APPROVAL)
        record = read_json(path)
        if record.get("status") != "Approved" or record.get("gate_verdict") != "approve":
            raise GovernanceStateError("Architecture bootstrap has no completed human approval")
        _require_files(artifacts, "Bootstrap review")
        _verify_artifact_hashes(record, artifacts, "Architecture bootstrap")


def accept_bootstrap(verdict: str) -> None:
    if verdict != "approve":
        raise GovernanceStateError("Bootstrap acceptance requires the human gate verdict 'approve'")
    validate_bootstrap(False, False)
    artifacts = bootstrap_artifacts()
    _require_files(artifacts, "Bootstrap review")
    _require_review_basis(
        BOOTSTRAP_REVIEW,
        artifacts[:-1],
        "Bootstrap",
    )
    write_json(
        project_path(BOOTSTRAP_APPROVAL),
        {
            "schema_version": "1.0",
            "status": "Approved",
            "gate_verdict": verdict,
            "artifacts": _artifact_hashes(artifacts),
        },
    )
    print(f"Architecture bootstrap is approved: {project_path(BOOTSTRAP_APPROVAL)}")


def complete_bootstrap() -> None:
    validate_bootstrap(True, True)
    report = project_path(READINESS_REPORT)
    if not report.is_file():
        raise GovernanceStateError(f"Readiness report is missing: {report}")
    text = report.read_text(encoding="utf-8")
    if not text.startswith("**Status**: READY\n"):
        raise GovernanceStateError("Readiness report must begin with '**Status**: READY'")
    write_json(
        project_path(BOOTSTRAP_COMPLETION),
        {
            "schema_version": "1.0",
            "status": "Completed",
            "constitution_sha256": sha256(project_path(CONSTITUTION)),
            "bootstrap_approval_sha256": sha256(project_path(BOOTSTRAP_APPROVAL)),
            "readiness_report": {
                "path": READINESS_REPORT.as_posix(),
                "sha256": sha256(report),
            },
        },
    )
    print(f"Program Kit bootstrap is deterministically complete: {project_path(BOOTSTRAP_COMPLETION)}")


def validate_completion() -> None:
    """Validate the completion record against the current approved artifacts."""
    validate_bootstrap(True, True)
    report = project_path(READINESS_REPORT)
    if not report.is_file() or not report.read_text(encoding="utf-8").startswith(
        "**Status**: READY\n"
    ):
        raise GovernanceStateError("Readiness report must begin with '**Status**: READY'")
    record = read_json(project_path(BOOTSTRAP_COMPLETION))
    expected = {
        "schema_version": "1.0",
        "status": "Completed",
        "constitution_sha256": sha256(project_path(CONSTITUTION)),
        "bootstrap_approval_sha256": sha256(project_path(BOOTSTRAP_APPROVAL)),
        "readiness_report": {
            "path": READINESS_REPORT.as_posix(),
            "sha256": sha256(report),
        },
    }
    if record != expected:
        raise GovernanceStateError(
            "Bootstrap completion record does not match the current constitution, approval, and readiness report"
        )


def accepted_adr(adr_id: str) -> bool:
    decisions = project_path(DECISIONS)
    if not decisions.is_dir():
        return False
    normalized = adr_id.lower()
    for path in decisions.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if normalized in (path.stem + "\n" + text[:500]).lower() and re.search(
            r"(?:^|[-*]\s*)Status:\s*Accepted\s*$", text, re.MULTILINE | re.IGNORECASE
        ):
            return True
    return False


def roadmap_records(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise GovernanceStateError(f"Specification roadmap is missing: {path}")
    text = path.read_text(encoding="utf-8")
    if re.search(r"TODO\s*\(", text, re.IGNORECASE):
        raise GovernanceStateError("Specification roadmap contains unresolved TODOs")
    placeholders = sorted(set(re.findall(r"\[[A-Z][A-Z0-9_]+\]", text)))
    if placeholders:
        raise GovernanceStateError(
            "Specification roadmap contains template placeholders: "
            + ", ".join(placeholders)
        )
    matches = list(re.finditer(r"^###\s+([A-Z][A-Z0-9-]+):\s+(.+?)\s*$", text, re.MULTILINE))
    if not matches:
        raise GovernanceStateError("Specification roadmap contains no specification records")
    records: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end]
        fields = {
            key.strip(): value.strip()
            for key, value in re.findall(r"^-\s+\*\*(.+?)\*\*:\s*(.+?)\s*$", body, re.MULTILINE)
        }
        missing = REQUIRED_RECORD_FIELDS - fields.keys()
        if missing:
            raise GovernanceStateError(
                f"Roadmap record {match.group(1)} is missing: {', '.join(sorted(missing))}"
            )
        status = fields["Status"]
        if status not in STATUSES:
            raise GovernanceStateError(
                f"Roadmap record {match.group(1)} has invalid status: {status}"
            )
        records.append({"id": match.group(1), "title": match.group(2), **fields})
    return records


def validate_roadmap(require_ready: bool) -> list[dict[str, str]]:
    records = roadmap_records(project_path(ROADMAP))
    for record in records:
        if record["Status"] not in {"Ready", "Active"}:
            continue
        adrs = record["Required Accepted ADRs"]
        if adrs.lower() not in {"none", "n/a", "not applicable"}:
            identifiers = re.findall(r"ADR-[A-Z0-9-]+", adrs, re.IGNORECASE)
            if not identifiers:
                raise GovernanceStateError(
                    f"{record['Status']} roadmap record {record['id']} has unparseable required ADRs"
                )
            unresolved = [adr for adr in identifiers if not accepted_adr(adr)]
            if unresolved:
                raise GovernanceStateError(
                    f"{record['Status']} roadmap record {record['id']} references unresolved ADRs: "
                    + ", ".join(unresolved)
                )
    if require_ready and not any(record["Status"] == "Ready" for record in records):
        raise GovernanceStateError("Specification roadmap contains no Ready entry")
    return records


def _roadmap_view(records: list[dict[str, str]]) -> str:
    lines = [
        ROADMAP_VIEW_START,
        "## Specification roadmap view",
        "",
        (
            "> Derived navigation view only. "
            f"`{ROADMAP.as_posix()}` is the authoritative source for roadmap-entry status."
        ),
        "",
        "| Roadmap entry | Title | Authoritative status |",
        "| --- | --- | --- |",
    ]
    for record in records:
        title = record["title"].replace("|", "\\|").replace("`", "'")
        lines.append(f"| `{record['id']}` | {title} | `{record['Status']}` |")
    lines.extend([ROADMAP_VIEW_END, ""])
    return "\n".join(lines)


def _replace_roadmap_view(text: str, view: str, path: Path) -> str:
    starts = [match.start() for match in re.finditer(re.escape(ROADMAP_VIEW_START), text)]
    ends = [match.end() for match in re.finditer(re.escape(ROADMAP_VIEW_END), text)]
    if len(starts) != len(ends) or len(starts) > 1:
        raise GovernanceStateError(f"{path} has malformed Program Kit roadmap-view markers")
    if starts:
        if starts[0] >= ends[0]:
            raise GovernanceStateError(f"{path} has out-of-order Program Kit roadmap-view markers")
        before = text[: starts[0]].rstrip()
        after = text[ends[0] :].strip()
        return before + "\n\n" + view + ("\n" + after + "\n" if after else "")
    return text.rstrip() + "\n\n" + view


def synchronize_roadmap_views() -> None:
    """Refresh non-authoritative roadmap navigation in architecture documents."""
    records = validate_roadmap(False)
    _require_files((ARCHITECTURE, TRACEABILITY), "Roadmap synchronization")
    view = _roadmap_view(records)
    updates: list[tuple[Path, str]] = []
    for relative in (ARCHITECTURE, TRACEABILITY):
        path = project_path(relative)
        updates.append(
            (path, _replace_roadmap_view(path.read_text(encoding="utf-8"), view, relative))
        )
    for path, updated in updates:
        write_text(path, updated)
    print(
        "Synchronized derived roadmap views in "
        f"{ARCHITECTURE.as_posix()} and {TRACEABILITY.as_posix()}"
    )


def _without_roadmap_view(text: str, path: Path) -> tuple[str, str]:
    start = text.find(ROADMAP_VIEW_START)
    end = text.find(ROADMAP_VIEW_END)
    if start < 0 or end < 0 or end < start:
        raise GovernanceStateError(f"{path} has no valid synchronized roadmap view")
    if text.find(ROADMAP_VIEW_START, start + 1) >= 0 or text.find(ROADMAP_VIEW_END, end + 1) >= 0:
        raise GovernanceStateError(f"{path} has duplicate synchronized roadmap views")
    end += len(ROADMAP_VIEW_END)
    return text[:start] + text[end:], text[start:end] + "\n"


def validate_bootstrap_consistency() -> None:
    """Prove that roadmap authority and its two derived architecture views agree."""
    records = validate_roadmap(False)
    expected_view = _roadmap_view(records)
    stale_claims = re.compile(
        r"(?:created\s+later\s+by\s+(?:the\s+)?roadmap|no\s+roadmap\s+record\s+exists)",
        re.IGNORECASE,
    )
    for relative in (ARCHITECTURE, TRACEABILITY):
        path = project_path(relative)
        if not path.is_file():
            raise GovernanceStateError(f"Cross-artifact consistency file is missing: {path}")
        outside, actual_view = _without_roadmap_view(
            path.read_text(encoding="utf-8"), relative
        )
        if actual_view != expected_view:
            raise GovernanceStateError(
                f"{relative} roadmap view is stale; run synchronize-roadmap after roadmap generation"
            )
        if stale_claims.search(outside):
            raise GovernanceStateError(
                f"{relative} still claims the generated specification roadmap does not exist"
            )
        for number, line in enumerate(outside.splitlines(), 1):
            for record in records:
                if record["id"] not in line:
                    continue
                copied_status = re.search(
                    r"(?:\*\*Status\*\*\s*:|\bstatus\s*[:=]|\|)\s*"
                    r"(Candidate|Blocked|Ready|Active|Delivered|Superseded)\b",
                    line,
                    re.IGNORECASE,
                )
                if copied_status:
                    raise GovernanceStateError(
                        f"{relative}:{number} duplicates authoritative status for {record['id']}; "
                        f"keep status only in {ROADMAP.as_posix()} and the synchronized derived view"
                    )
    print("Architecture, roadmap, and traceability roadmap views are consistent")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Program Kit governance state")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate-installation")
    subparsers.add_parser("validate-assessment")
    assessment_parser = subparsers.add_parser("accept-assessment")
    assessment_parser.add_argument("--verdict", required=True)
    subparsers.add_parser("begin")
    subparsers.add_parser("validate-constitution-draft")
    ratify_parser = subparsers.add_parser("ratify")
    ratify_parser.add_argument("--verdict", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--require-roadmap", action="store_true")
    validate_parser.add_argument("--require-ready", action="store_true")
    roadmap_parser = subparsers.add_parser("validate-roadmap")
    roadmap_parser.add_argument("--require-ready", action="store_true")
    subparsers.add_parser("synchronize-roadmap")
    subparsers.add_parser("validate-bootstrap-consistency")
    review_parser = subparsers.add_parser("write-review")
    review_parser.add_argument(
        "--stage", required=True, choices=("assessment", "constitution", "bootstrap")
    )
    bootstrap_parser = subparsers.add_parser("validate-bootstrap")
    bootstrap_parser.add_argument("--require-approval", action="store_true")
    bootstrap_parser.add_argument("--require-ready", action="store_true")
    accept_bootstrap_parser = subparsers.add_parser("accept-bootstrap")
    accept_bootstrap_parser.add_argument("--verdict", required=True)
    subparsers.add_parser("complete-bootstrap")
    subparsers.add_parser("validate-completion")
    args = parser.parse_args()
    try:
        configure_paths()
        if args.command == "validate-installation":
            versions = validate_installation()
            print(f"Program Kit installation is version-coherent: {next(iter(versions.values()))}")
        else:
            # Installation coherence is the first invariant for every stateful or
            # validating governance operation. In particular, no Draft marker may
            # be written while the separately installed workflow is stale.
            validate_installation()
            if args.command == "begin":
                begin()
            elif args.command == "validate-assessment":
                validate_assessment()
                print("Bootstrap assessment and default decisions are valid")
            elif args.command == "accept-assessment":
                accept_assessment(args.verdict)
            elif args.command == "validate-constitution-draft":
                validate_constitution_draft()
                print("Constitution draft is ready for human review")
            elif args.command == "ratify":
                ratify(args.verdict)
            elif args.command == "validate":
                validate_ratification()
                if args.require_roadmap or args.require_ready:
                    validate_roadmap(args.require_ready)
                print("Program Kit governance state is valid")
            elif args.command == "validate-roadmap":
                validate_roadmap(args.require_ready)
                print("Specification roadmap is valid")
            elif args.command == "synchronize-roadmap":
                synchronize_roadmap_views()
            elif args.command == "validate-bootstrap-consistency":
                validate_bootstrap_consistency()
            elif args.command == "write-review":
                write_review(args.stage)
            elif args.command == "validate-bootstrap":
                validate_bootstrap(args.require_approval, args.require_ready)
                print("Architecture bootstrap artifacts are valid")
            elif args.command == "accept-bootstrap":
                accept_bootstrap(args.verdict)
            elif args.command == "complete-bootstrap":
                complete_bootstrap()
            elif args.command == "validate-completion":
                validate_completion()
    except GovernanceStateError as exc:
        print(f"governance state error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
