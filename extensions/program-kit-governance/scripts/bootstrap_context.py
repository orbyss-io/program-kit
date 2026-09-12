from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


SCHEMA_VERSION = "4.0"
CONTEXT_DIRECTORY = Path(".specify/workflows/runs")
INTAKE_PATH = Path("docs/architecture/bootstrap-intake.json")
INTAKE_ARTIFACTS = (
    "docs/architecture/project-intent.md",
    "docs/architecture/architecture-map.json",
    "docs/architecture/workspace.dsl",
    INTAKE_PATH.as_posix(),
)

STAGE_ARTIFACTS: dict[str, tuple[str, ...]] = {
    "assessment": (),
    "research": (
        "docs/architecture/bootstrap-assessment.md",
        "docs/architecture/bootstrap-decisions.json",
        "docs/architecture/decision-backlog.md",
    ),
    "architecture": (
        ".specify/memory/constitution.md",
        ".specify/memory/constitution-ratification.json",
        ".specify/governance/bootstrap-assessment-approval.json",
        "docs/architecture/bootstrap-assessment.md",
        "docs/architecture/bootstrap-decisions.json",
        "docs/architecture/decision-backlog.md",
        "docs/architecture/tooling-evaluation.md",
    ),
    "tooling": (
        ".specify/memory/constitution.md",
        ".specify/memory/constitution-ratification.json",
        ".specify/governance/bootstrap-assessment-approval.json",
        "docs/architecture/bootstrap-decisions.json",
        "docs/architecture/decision-backlog.md",
        "docs/architecture/tooling-evaluation.md",
        "docs/architecture/architecture.md",
        "docs/architecture/quality-attributes.md",
        "docs/architecture/technology-radar.md",
        "docs/architecture/traceability.md",
        "docs/architecture/decisions/bootstrap-baseline.md",
    ),
    "roadmap": (
        ".specify/memory/constitution.md",
        ".specify/memory/constitution-ratification.json",
        ".specify/governance/bootstrap-assessment-approval.json",
        "docs/architecture/bootstrap-decisions.json",
        "docs/architecture/decision-backlog.md",
        "docs/architecture/tooling-evaluation.md",
        "docs/architecture/architecture.md",
        "docs/architecture/quality-attributes.md",
        "docs/architecture/quality-system.md",
        "docs/architecture/technology-radar.md",
        "docs/architecture/traceability.md",
        "docs/architecture/decisions/bootstrap-baseline.md",
    ),
    "readiness": (
        ".specify/memory/constitution.md",
        ".specify/memory/constitution-ratification.json",
        ".specify/governance/bootstrap-assessment-approval.json",
        ".specify/governance/bootstrap-approval.json",
        "docs/architecture/bootstrap-decisions.json",
        "docs/architecture/decision-backlog.md",
        "docs/architecture/tooling-evaluation.md",
        "docs/architecture/architecture.md",
        "docs/architecture/quality-attributes.md",
        "docs/architecture/quality-system.md",
        "docs/architecture/specification-roadmap.md",
        "docs/architecture/technology-radar.md",
        "docs/architecture/traceability.md",
        "docs/architecture/decisions/bootstrap-baseline.md",
    ),
}

STAGE_FULL_READS = {
    "assessment": (),
    "research": ("docs/architecture/bootstrap-decisions.json",),
    "architecture": (
        ".specify/memory/constitution.md",
        "docs/architecture/architecture-map.json",
    ),
    "tooling": (".specify/memory/constitution.md",),
    "roadmap": (".specify/memory/constitution.md",),
    "readiness": (".specify/memory/constitution.md",),
}

STAGE_FOCUS = {
    "assessment": "Project confirmed intake into a proportional decision baseline without reopening accepted choices.",
    "research": "Verify only selected technologies and capabilities; excluded surfaces are out of scope.",
    "architecture": "Define the smallest governed architecture that realizes the confirmed intake journeys.",
    "tooling": "Adopt only controls required by selected capabilities and accepted boundaries.",
    "roadmap": "Create outcome-oriented specification entries from confirmed journeys and accepted decisions.",
    "readiness": "Prove the first Ready entry has accepted authority, owned risks, and sufficient evidence.",
}

INTAKE_STAGE_FIELDS = {
    "assessment": (
        "facts", "scope", "actors", "journeys", "quality_requirements", "integrations",
        "choices", "capability_assessments", "domain_analysis", "open_items",
        "candidate_slice_signals", "routing",
    ),
    "research": (
        "quality_requirements", "choices", "capability_assessments", "open_items", "routing",
    ),
    "architecture": (
        "facts", "scope", "actors", "journeys", "quality_requirements", "integrations", "choices",
        "domain_analysis", "open_items", "candidate_slice_signals", "routing",
    ),
    "tooling": (
        "scope", "quality_requirements", "open_items", "routing",
    ),
    "roadmap": (
        "scope", "actors", "journeys", "open_items", "candidate_slice_signals",
    ),
    "readiness": (
        "actors", "journeys", "open_items", "candidate_slice_signals",
    ),
}

MAP_STAGE_FIELDS = {
    "assessment": ("constraints", "elements", "relationships", "views"),
    "research": ("constraints", "elements", "relationships", "views"),
    # Architecture edits the canonical seed, so a second lossy copy in the brief is actively
    # harmful. The seed is a required full read and this projection carries only its identity.
    "architecture": (),
    "tooling": ("decisions", "constraints", "elements", "relationships"),
    "roadmap": ("decisions", "constraints", "elements", "relationships", "views"),
    "readiness": ("decisions", "constraints", "elements", "relationships", "views"),
}

MAP_RECORD_FIELDS = {
    "sources": ("id", "path", "sha256", "format", "importer"),
    "decisions": (
        "id", "path", "sha256", "title", "date", "status", "scope", "owner", "supersedes",
    ),
    "documentation": ("id", "path", "sha256", "canonicalSha256", "scope"),
    "constraints": ("id", "statement", "status", "applies_to", "decision_refs"),
    "elements": (
        "id", "type", "name", "description", "status", "ownership", "technology",
        "parent", "decision_refs", "properties",
    ),
    "relationships": (
        "id", "source", "target", "description", "technology", "status",
        "decision_refs", "properties",
    ),
    "views": (
        "key", "type", "title", "scope", "elements", "relationships", "decision_refs",
    ),
    "extensions": ("id", "kind", "policy", "source"),
}

STAGE_RECORD_FIELDS = {
    "tooling": {
        "decisions": ("id", "title", "status", "scope"),
        "constraints": ("id", "statement", "status", "applies_to", "decision_refs"),
        "elements": ("id", "type", "name", "status", "ownership", "parent", "decision_refs"),
        "relationships": ("id", "source", "target", "status", "decision_refs"),
    },
    "roadmap": {
        "decisions": ("id", "title", "status", "scope"),
        "constraints": ("id", "statement", "status", "applies_to", "decision_refs"),
        "elements": ("id", "type", "name", "status", "ownership", "parent", "decision_refs"),
        "relationships": ("id", "source", "target", "status", "decision_refs"),
        "views": ("key", "type", "title", "scope", "elements", "relationships", "decision_refs"),
    },
    "readiness": {
        "decisions": ("id", "title", "status", "scope"),
        "constraints": ("id", "statement", "status", "applies_to", "decision_refs"),
        "elements": ("id", "type", "name", "status", "ownership", "parent", "decision_refs"),
        "relationships": ("id", "source", "target", "status", "decision_refs"),
        "views": ("key", "type", "title", "scope", "elements", "relationships", "decision_refs"),
    },
}

MAX_INDEX_HEADINGS = 24
MAX_INDEX_SIGNALS = 8
MAX_INDEX_SIGNAL_CHARS = 160
MAX_BUILDING_BLOCK_TARGETS = 128

GOVERNANCE_CONFIGS = (
    Path(".specify/extensions/program-kit-governance/program-kit-governance-config.yml"),
    Path(".specify/extensions/program-kit-governance/program-kit-governance-config.local.yml"),
)

OUTPUT_CONTRACTS = {
    "assessment": {
        "write_paths": [
            "docs/architecture/bootstrap-assessment.md",
            "docs/architecture/decision-backlog.md",
            "docs/architecture/bootstrap-decisions.json",
        ],
        "contract_references": [
            ".specify/extensions/program-kit-governance/references/bootstrap-decisions.schema.json"
        ],
    },
    "research": {
        "write_paths": [
            "docs/architecture/tooling-evaluation.md",
            "docs/architecture/bootstrap-decisions.json",
        ],
        "contract_references": [
            ".specify/extensions/program-kit-governance/references/bootstrap-decisions.schema.json"
        ],
    },
    "architecture": {
        "write_paths": [
            "docs/architecture/README.md",
            "docs/architecture/architecture.md",
            "docs/architecture/quality-attributes.md",
            "docs/architecture/technology-radar.md",
            "docs/architecture/traceability.md",
            "docs/architecture/architecture-map.json",
            "docs/architecture/building-block-selection.json",
            "docs/architecture/workspace.dsl",
            "docs/architecture/decisions/README.md",
            "docs/architecture/decisions/bootstrap-baseline.md",
        ],
        "contract_references": [
            ".specify/extensions/program-kit-governance/references/architecture-map.schema.json",
            ".specify/extensions/program-kit-building-blocks/references/building-block-selection.schema.json",
        ],
    },
    "tooling": {
        "write_paths": ["docs/architecture/quality-system.md"],
        "contract_references": [],
    },
    "roadmap": {
        "write_paths": [
            "docs/architecture/specification-roadmap.md",
            "docs/architecture/architecture.md",
            "docs/architecture/traceability.md",
        ],
        "contract_references": [],
    },
    "readiness": {
        "write_paths": ["docs/architecture/readiness-report.md"],
        "contract_references": [],
    },
}

ARTIFACT_BYTE_BUDGETS = {
    "docs/architecture/bootstrap-assessment.md": 16 * 1024,
    "docs/architecture/decision-backlog.md": 10 * 1024,
    "docs/architecture/tooling-evaluation.md": 8 * 1024,
    "docs/architecture/README.md": 4 * 1024,
    "docs/architecture/architecture.md": 10 * 1024,
    "docs/architecture/architecture-map.json": 256 * 1024,
    "docs/architecture/workspace.dsl": 256 * 1024,
    "docs/architecture/quality-attributes.md": 6 * 1024,
    "docs/architecture/technology-radar.md": 4 * 1024,
    "docs/architecture/traceability.md": 6 * 1024,
    "docs/architecture/decisions/README.md": 4 * 1024,
    "docs/architecture/decisions/bootstrap-baseline.md": 6 * 1024,
    "docs/architecture/quality-system.md": 8 * 1024,
    "docs/architecture/specification-roadmap.md": 6 * 1024,
    "docs/architecture/readiness-report.md": 4 * 1024,
}

# Generation targets deliberately leave repair headroom below the hard validator budgets.
# Workers should not discover size constraints by writing to the boundary and rewriting.
ARTIFACT_TARGET_BYTES = {
    "docs/architecture/bootstrap-assessment.md": 10 * 1024,
    "docs/architecture/decision-backlog.md": 7 * 1024,
    "docs/architecture/tooling-evaluation.md": 11 * 512,
    "docs/architecture/README.md": 3 * 1024,
    "docs/architecture/architecture.md": 8 * 1024,
    "docs/architecture/architecture-map.json": 224 * 1024,
    "docs/architecture/workspace.dsl": 224 * 1024,
    "docs/architecture/quality-attributes.md": 5 * 1024,
    "docs/architecture/technology-radar.md": 3 * 1024,
    "docs/architecture/traceability.md": 5 * 1024,
    "docs/architecture/decisions/README.md": 3 * 1024,
    "docs/architecture/decisions/bootstrap-baseline.md": 5 * 1024,
    "docs/architecture/quality-system.md": 6 * 1024,
    "docs/architecture/specification-roadmap.md": 5 * 1024,
    "docs/architecture/readiness-report.md": 3 * 1024,
}

ASSESSMENT_BASE_REFERENCES = (
    ".specify/extensions/program-kit-governance/references/default-adoption.md",
    ".specify/extensions/program-kit-governance/references/capability-index.json",
)

ASSESSMENT_OPTIONAL_REFERENCES = (
    ".specify/extensions/program-kit-governance/references/modularity-and-contracts.md",
    ".specify/extensions/program-kit-governance/references/vertical-slicing.md",
)

DOTNET_REFERENCES = (
    ".specify/extensions/program-kit-dotnet/references/dotnet-engineering.md",
    ".specify/extensions/program-kit-dotnet/references/dotnet-runtime-and-application-bundles.md",
)

SECURE_WEB_REFERENCES = (
    ".specify/extensions/program-kit-dotnet/references/secure-web-profiles.md",
    ".specify/extensions/program-kit-dotnet/references/web-security-threat-model.md",
    ".specify/extensions/program-kit-dotnet/references/web-security-evidence.json",
)

UI_EXPERIENCE_REFERENCES = (
    ".specify/extensions/program-kit-governance/references/ui-experience-v1.md",
    ".specify/extensions/program-kit-governance/references/ui-evidence-v1.json",
)

AUTHORITY_JSON = {
    "docs/architecture/bootstrap-decisions.json": "assessment_decisions",
    ".specify/governance/bootstrap-assessment-approval.json": "assessment_approval",
    ".specify/memory/constitution-ratification.json": "constitution_ratification",
    ".specify/governance/bootstrap-approval.json": "bootstrap_approval",
}

DOTNET_SDK_MANIFEST = Path(
    ".specify/extensions/program-kit-dotnet/templates/dotnet/files/global.json"
)
NODE_VERSION_MANIFEST = Path(
    ".specify/extensions/program-kit-dotnet/templates/dotnet/files/.nvmrc"
)
WEB_PACKAGE_MANIFEST = Path(
    ".specify/extensions/program-kit-dotnet/templates/dotnet/web-profiles/common/.program-kit/eng/web/package.json"
)
WEB_PACKAGE_LOCK = Path(
    ".specify/extensions/program-kit-dotnet/templates/dotnet/web-profiles/common/.program-kit/eng/web/package-lock.json"
)
TOOLCHAIN_OVERRIDE_ID = "managed-toolchain-version"
UI_PACKAGE_MANIFEST = Path(
    ".specify/extensions/program-kit-governance/templates/ui-experience/acceptance/package.json"
)
UI_PACKAGE_LOCK = UI_PACKAGE_MANIFEST.with_name("package-lock.json")

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
SIGNAL = re.compile(
    r"(^\s*[-*]\s+\*\*|^\s*\*\*[^*]+\*\*\s*:|^\s*\|.*\|\s*$|"
    r"\b(?:Accepted|Proposed|Unresolved|Deferred|Blocked|Ready|Candidate)\b|"
    r"\b(?:ADR|SPC|SPEC|QA|WEB-C|WEB-V)-?[A-Z0-9-]*\b)",
    re.IGNORECASE,
)
class ContextError(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContextError(f"Cannot read JSON object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContextError(f"Expected a JSON object in {path}")
    return value


def _source_record(project_root: Path, relative: Path) -> dict:
    path = project_root / relative
    if not path.is_file():
        raise ContextError(
            f"Selected Program Kit profile pin source is missing: {relative.as_posix()}"
        )
    return {
        "path": relative.as_posix(),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def managed_profile_pin_authority(project_root: Path, decisions: dict) -> dict:
    selected = decisions.get("selected_profiles", [])
    if not isinstance(selected, list) or not all(
        isinstance(value, str) and value.strip() for value in selected
    ):
        raise ContextError("Bootstrap selected_profiles must be a list of non-empty strings")
    profiles = {value.strip().casefold() for value in selected}
    pins: dict[str, str] = {}
    sources: list[dict] = []

    if "dotnet" in profiles:
        global_path = project_root / DOTNET_SDK_MANIFEST
        global_json = load_json(global_path)
        sdk = global_json.get("sdk")
        version = sdk.get("version") if isinstance(sdk, dict) else None
        if not isinstance(version, str) or not version.strip():
            raise ContextError(
                f"Managed .NET SDK manifest has no exact sdk.version: {DOTNET_SDK_MANIFEST.as_posix()}"
            )
        pins["dotnet-sdk"] = version.strip()
        source = _source_record(project_root, DOTNET_SDK_MANIFEST)
        source["profile"] = "dotnet"
        source["provides"] = ["dotnet-sdk"]
        source["settings"] = {
            key: sdk[key] for key in ("rollForward", "allowPrerelease") if key in sdk
        }
        sources.append(source)
        node_path = project_root / NODE_VERSION_MANIFEST
        if not node_path.is_file():
            raise ContextError(
                f"Selected Program Kit profile pin source is missing: {NODE_VERSION_MANIFEST.as_posix()}"
            )
        node_version = node_path.read_text(encoding="utf-8").strip().removeprefix("v")
        if not node_version:
            raise ContextError("Managed Node version manifest is empty")
        pins["node"] = node_version
        node_source = _source_record(project_root, NODE_VERSION_MANIFEST)
        node_source["profile"] = "dotnet"
        node_source["provides"] = ["node"]
        sources.append(node_source)

    browser_selected = bool({"typescript-web", "browser-web"} & profiles)
    if "dotnet" in profiles and browser_selected:
        package_json = load_json(project_root / WEB_PACKAGE_MANIFEST)
        dependencies = package_json.get("devDependencies")
        if not isinstance(dependencies, dict) or not dependencies:
            raise ContextError("Managed web package manifest has no devDependencies")
        required_packages = ("typescript", "@types/node", "@playwright/test")
        for package in required_packages:
            version = dependencies.get(package)
            if not isinstance(version, str) or not version.strip():
                raise ContextError(f"Managed web package manifest has no exact {package} pin")
            pins[package] = version.strip()

        lock_json = load_json(project_root / WEB_PACKAGE_LOCK)
        packages = lock_json.get("packages")
        root_package = packages.get("") if isinstance(packages, dict) else None
        locked = root_package.get("devDependencies") if isinstance(root_package, dict) else None
        if not isinstance(locked, dict):
            raise ContextError("Managed web package lock has no root devDependencies")
        mismatches = {
            package: {"manifest": dependencies[package], "lock": locked.get(package)}
            for package in required_packages
            if locked.get(package) != dependencies[package]
        }
        if mismatches:
            raise ContextError(
                f"Managed web package manifest and lock disagree: {mismatches}"
            )
        package_source = _source_record(project_root, WEB_PACKAGE_MANIFEST)
        package_source["profile"] = "dotnet-typescript-web"
        package_source["provides"] = list(required_packages)
        sources.append(package_source)
        lock_source = _source_record(project_root, WEB_PACKAGE_LOCK)
        lock_source["profile"] = "dotnet-typescript-web"
        lock_source["verifies"] = WEB_PACKAGE_MANIFEST.as_posix()
        sources.append(lock_source)

    if "ui-experience-v1" in profiles:
        package = load_json(project_root / UI_PACKAGE_MANIFEST)
        locked = load_json(project_root / UI_PACKAGE_LOCK).get("packages", {}).get("", {})
        if package.get("devDependencies") != locked.get("devDependencies") or package.get("engines") != locked.get("engines"):
            raise ContextError("UI acceptance package/lock graph mismatch")
        selected = {**package["engines"], **package["devDependencies"]}
        for name, value in selected.items():
            if name in pins and pins[name] != value:
                raise ContextError(f"UI acceptance conflicts with managed pin {name}")
            pins[name] = value
        for path in (UI_PACKAGE_MANIFEST, UI_PACKAGE_LOCK):
            record = _source_record(project_root, path)
            record["profile"] = "ui-experience-v1"
            record["provides"] = list(selected)
            sources.append(record)

    return {
        "precedence": "program-kit-managed-profile-before-local-environment-or-current-candidate",
        "selected_profiles": sorted(profiles),
        "pins": dict(sorted(pins.items())),
        "sources": sources,
        "local_environment_policy": (
            "A missing or older local tool is a remediation requirement, not a version-selection "
            "input. Recommend installing or upgrading to the Program Kit pin. Retain a different "
            "local version only through an explicitly approved managed-toolchain-version override."
        ),
    }


def validate_profile_pin_decisions(project_root: Path, run_id: str) -> dict:
    validate_intake(project_root, run_id)
    decisions = load_json(project_root / "docs/architecture/bootstrap-decisions.json")
    authority = managed_profile_pin_authority(project_root, decisions)
    expected = authority["pins"]
    toolchain = decisions.get("toolchain")
    if not expected:
        if toolchain is not None:
            raise ContextError(
                "Bootstrap toolchain authority is present although no selected managed profile supplies pins"
            )
        return authority
    if not isinstance(toolchain, dict) or set(toolchain) != {
        "source",
        "pins",
        "override_reason",
    }:
        raise ContextError(
            "Selected managed profiles require toolchain with exactly source, pins, and override_reason"
        )
    recorded = toolchain.get("pins")
    if not isinstance(recorded, dict) or set(recorded) != set(expected) or not all(
        isinstance(value, str) and value.strip() for value in recorded.values()
    ):
        raise ContextError(
            f"Bootstrap toolchain pins must contain exactly the managed keys: {sorted(expected)}"
        )
    source = toolchain.get("source")
    reason = toolchain.get("override_reason")
    if source == "program-kit-default":
        if recorded != expected:
            raise ContextError(
                "Bootstrap toolchain versions do not match the authoritative Program Kit profile pins; "
                "a local installation or researched current candidate cannot replace them"
            )
        if reason not in ("", None):
            raise ContextError("Program Kit default toolchain pins must not claim an override reason")
    elif source == "override":
        if not isinstance(reason, str) or not reason.strip():
            raise ContextError("A managed toolchain version override requires an explicit reason")
        overrides = decisions.get("overrides", [])
        override_ids = {
            item.get("id") for item in overrides if isinstance(item, dict)
        } if isinstance(overrides, list) else set()
        if TOOLCHAIN_OVERRIDE_ID not in override_ids:
            raise ContextError(
                f"A managed toolchain version override requires the approved {TOOLCHAIN_OVERRIDE_ID!r} override record"
            )
        non_dotnet_differences = {
            key: {"managed": expected[key], "recorded": recorded[key]}
            for key in expected
            if key != "dotnet-sdk" and recorded[key] != expected[key]
        }
        if non_dotnet_differences:
            raise ContextError(
                "The managed-toolchain-version override may retain a user-selected local .NET SDK "
                f"only; other managed pins remain authoritative: {non_dotnet_differences}"
            )
    else:
        raise ContextError(
            "Bootstrap toolchain source must be program-kit-default or an explicit override"
        )
    return authority


def safe_run_directory(project_root: Path, run_id: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ContextError("Workflow run ID must contain only letters, digits, '-' or '_'")
    runs_root = (project_root / CONTEXT_DIRECTORY).resolve()
    run_directory = (runs_root / run_id).resolve()
    try:
        run_directory.relative_to(runs_root)
    except ValueError as exc:
        raise ContextError("Workflow run directory escaped the project") from exc
    return run_directory


def _load_intake_module():
    path = Path(__file__).with_name("bootstrap_intake.py")
    spec = importlib.util.spec_from_file_location("program_kit_bootstrap_intake", path)
    if spec is None or spec.loader is None:
        raise ContextError(f"Cannot load bootstrap intake support from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate_intake(
    project_root: Path,
    run_id: str,
    allow_architecture_evolution: bool = False,
) -> dict:
    try:
        module = _load_intake_module()
        _, intake = module.intake_from_run(
            project_root,
            run_id,
            allow_architecture_evolution=allow_architecture_evolution,
        )
    except Exception as exc:
        if exc.__class__.__name__ != "IntakeError":
            raise
        raise ContextError(str(exc)) from exc
    return intake


def validate_architecture_alignment(project_root: Path, run_id: str) -> dict:
    """Validate the evolved architecture against immutable confirmed-intake semantics."""
    return validate_intake(
        project_root,
        run_id,
        allow_architecture_evolution=True,
    )


def intake_record(project_root: Path, run_id: str) -> dict:
    path = project_root / INTAKE_PATH
    return {
        "path": INTAKE_PATH.as_posix(),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
    }


def intake_projection(intake: dict, stage: str) -> dict:
    fields = INTAKE_STAGE_FIELDS[stage]
    return {
        "projection": "stage-summary",
        "schema_version": intake["schema_version"],
        "status": intake["status"],
        "project": intake["project"],
        **{field: intake[field] for field in fields},
    }


def _nonempty_projection(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: projected
            for key, item in value.items()
            if (projected := _nonempty_projection(item)) not in (None, "", [], {})
        }
    if isinstance(value, list):
        return [
            projected
            for item in value
            if (projected := _nonempty_projection(item)) not in (None, "", [], {})
        ]
    return value


def architecture_projection(project_root: Path, architecture_map: dict, stage: str) -> dict:
    path = project_root / "docs/architecture/architecture-map.json"
    fields = MAP_STAGE_FIELDS[stage]
    projected = {
        "projection": "stage-summary",
        "source": {
            "path": "docs/architecture/architecture-map.json",
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        },
        "schema_version": architecture_map["schema_version"],
        "model_id": architecture_map["model_id"],
        "title": architecture_map["title"],
        **{
            field: [
                {
                    key: item[key]
                    for key in STAGE_RECORD_FIELDS.get(stage, {}).get(
                        field, MAP_RECORD_FIELDS[field]
                    )
                    if key in item
                }
                for item in architecture_map[field]
            ]
            if field in MAP_RECORD_FIELDS
            else architecture_map[field]
            for field in fields
        },
    }
    return _nonempty_projection(projected)


def markdown_index(text: str) -> tuple[list[dict], list[dict]]:
    headings: list[dict] = []
    signals: list[dict] = []
    for line_number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        match = HEADING.match(line)
        if match and len(headings) < MAX_INDEX_HEADINGS:
            headings.append({"line": line_number, "level": len(match.group(1)), "title": match.group(2)})
            continue
        if line and SIGNAL.search(line) and len(signals) < MAX_INDEX_SIGNALS:
            signals.append({"line": line_number, "text": line[:MAX_INDEX_SIGNAL_CHARS]})
    return headings, signals


def artifact_record(
    project_root: Path, relative_path: str, authority_name: str | None = None
) -> tuple[dict, tuple[str, dict] | None]:
    path = project_root / relative_path
    if not path.is_file():
        raise ContextError(f"Required {relative_path} is missing")
    data = path.read_bytes()
    record: dict = {"path": relative_path, "sha256": sha256_bytes(data), "bytes": len(data)}
    authority: tuple[str, dict] | None = None
    if path.suffix.lower() == ".json":
        payload = load_json(path)
        record["kind"] = "json"
        record["keys"] = sorted(payload)
        authority_name = authority_name or AUTHORITY_JSON.get(relative_path)
        if authority_name:
            authority = authority_name, payload
    else:
        headings, signals = markdown_index(data.decode("utf-8"))
        record.update({"kind": "markdown", "headings": headings, "signals": signals})
    return record, authority


def compact_authority(name: str, payload: dict) -> dict:
    if name == "assessment_decisions":
        result = {
            key: payload[key]
            for key in (
                "schema_version", "default_profile", "selected_profiles", "dotnet", "web",
                "toolchain", "unresolved", "deferred",
            )
            if key in payload
        }
        for key, fields in {
            "choices": ("id", "decision", "source"),
            "overrides": ("id", "decision"),
            "acknowledgements": ("id", "summary"),
        }.items():
            if key in payload:
                result[key] = [
                    {field: item[field] for field in fields if field in item}
                    for item in payload[key]
                ]
        return result
    keys = (
        "schema_version", "status", "constitution", "gate_verdict", "approval_mode",
        "approval_source",
    )
    result = {key: payload[key] for key in keys if key in payload}
    if name == "assessment_approval":
        artifacts = payload.get("artifacts")
        if isinstance(artifacts, dict):
            decision_hash = artifacts.get("docs/architecture/bootstrap-decisions.json")
            if isinstance(decision_hash, str) and decision_hash:
                result["bootstrap_decisions_sha256"] = decision_hash
    return result


def replace_governance_path(relative_path: str, paths: dict[str, str]) -> str:
    exact = {
        "docs/architecture/specification-roadmap.md": paths["specification_roadmap"],
        ".specify/memory/constitution.md": paths["constitution_document"],
        ".specify/memory/constitution-ratification.json": paths["constitution_ratification"],
    }
    if relative_path in exact:
        return exact[relative_path]
    default_decisions = "docs/architecture/decisions"
    if relative_path == default_decisions or relative_path.startswith(default_decisions + "/"):
        suffix = relative_path[len(default_decisions) :]
        return paths["decisions"].rstrip("/") + suffix
    return relative_path


def decision_records(project_root: Path, decisions_path: str) -> list[dict]:
    directory = project_root / decisions_path
    if not directory.is_dir():
        return []
    result: list[dict] = []
    for path in sorted(directory.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        title = next((match.group(2) for line in text.splitlines() if (match := HEADING.match(line))), path.stem)
        status_match = re.search(r"(?im)^\s*(?:[-*]\s+)?(?:\*\*)?Status(?:\*\*)?\s*:\s*(.+?)\s*$", text)
        result.append({
            "path": path.relative_to(project_root).as_posix(),
            "sha256": sha256_file(path),
            "title": title,
            "status": status_match.group(1).strip() if status_match else "Unspecified",
        })
    return result


def governance_contract(project_root: Path) -> dict:
    values = {
        "decisions": "docs/architecture/decisions",
        "specification_roadmap": "docs/architecture/specification-roadmap.md",
        "constitution_document": ".specify/memory/constitution.md",
        "constitution_ratification": ".specify/memory/constitution-ratification.json",
    }
    sources: list[dict] = []
    key_map = {
        ("architecture", "decisions"): "decisions",
        ("architecture", "specification_roadmap"): "specification_roadmap",
        ("constitution", "document"): "constitution_document",
        ("constitution", "ratification"): "constitution_ratification",
    }
    for relative in GOVERNANCE_CONFIGS:
        path = project_root / relative
        record: dict = {"path": relative.as_posix(), "exists": path.is_file()}
        if path.is_file():
            record["sha256"] = sha256_file(path)
            section: str | None = None
            for number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                line = raw_line.split("#", 1)[0].rstrip()
                if not line:
                    continue
                top = re.fullmatch(r"([A-Za-z][A-Za-z0-9_-]*):\s*", line)
                nested = re.fullmatch(r"  ([A-Za-z][A-Za-z0-9_-]*):\s*['\"]?([^'\"]+)['\"]?\s*", line)
                if top:
                    section = top.group(1)
                elif nested and section:
                    destination = key_map.get((section, nested.group(1)))
                    if destination:
                        candidate = Path(nested.group(2).strip())
                        if candidate.is_absolute() or ".." in candidate.parts:
                            raise ContextError(
                                f"Unsafe governance path in {relative.as_posix()}:{number}"
                            )
                        values[destination] = candidate.as_posix()
        sources.append(record)
    return {"paths": values, "configuration_sources": sources}


def resolved_output_contract(stage: str, paths: dict[str, str], run_id: str = "") -> dict:
    contract = OUTPUT_CONTRACTS[stage]
    write_paths = [replace_governance_path(path, paths) for path in contract["write_paths"]]
    return {
        "write_paths": write_paths,
        "contract_references": list(contract["contract_references"]),
        "validation_commands": [
            "python .specify/extensions/program-kit-governance/scripts/bootstrap_context.py "
            f"validate-stage --stage {stage} --run-id {run_id}"
        ],
        "artifact_byte_budgets": {
            replace_governance_path(path, paths): ARTIFACT_BYTE_BUDGETS[path]
            for path in contract["write_paths"]
            if path in ARTIFACT_BYTE_BUDGETS
        },
        "artifact_target_bytes": {
            replace_governance_path(path, paths): ARTIFACT_TARGET_BYTES[path]
            for path in contract["write_paths"]
            if path in ARTIFACT_TARGET_BYTES
        },
    }


def routed_references(intake: dict, stage: str) -> tuple[str, ...]:
    if stage not in {"assessment", "research"}:
        return ()
    routing = intake["routing"]
    languages = {item.casefold() for item in routing["languages"]}
    frameworks = {item.casefold() for item in routing["frameworks"]}
    interfaces = {item.casefold() for item in routing["interfaces"]}
    capabilities = {item.casefold() for item in routing["capabilities"]}
    surfaces = {item.casefold() for item in routing["included_surfaces"]}
    result: list[str] = list(
        ASSESSMENT_BASE_REFERENCES + ASSESSMENT_OPTIONAL_REFERENCES
        if stage == "assessment"
        else ()
    )
    if stage == "assessment" and (languages or interfaces):
        result.append(
            ".specify/extensions/program-kit-governance/references/software-language.md"
        )
    if any(".net" in item for item in languages | frameworks) or "c#" in languages:
        result.extend(DOTNET_REFERENCES)
    secure_web = (
        "authenticated-browser-bff" in capabilities
        or any("bff" in item for item in interfaces | surfaces)
    )
    if secure_web:
        result.extend(SECURE_WEB_REFERENCES)
    browser_ui = any(
        marker in item
        for item in interfaces | surfaces
        for marker in ("browser", "frontend", "react", "web")
    )
    if browser_ui:
        result.extend(UI_EXPERIENCE_REFERENCES)
    return tuple(dict.fromkeys(result))


def required_routed_references(intake: dict, stage: str) -> tuple[str, ...]:
    routed = routed_references(intake, stage)
    if stage == "assessment":
        return tuple(path for path in routed if path in ASSESSMENT_BASE_REFERENCES)
    if stage == "research":
        return tuple(path for path in routed if path in UI_EXPERIENCE_REFERENCES)
    return ()


def _observed_command(command: list[str]) -> str:
    executable = shutil.which(command[0])
    if executable is None:
        return "unavailable"
    try:
        result = subprocess.run(
            [executable, *command[1:]],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    lines = ((result.stdout or "") + (result.stderr or "")).strip().splitlines()
    return lines[0] if result.returncode == 0 and lines else "unavailable"


def observed_toolchain() -> dict[str, str]:
    return {
        "dotnet": _observed_command(["dotnet", "--version"]),
        "node": _observed_command(["node", "--version"]),
        "npm": _observed_command(["npm", "--version"]),
        "python": sys.version.split()[0],
    }


def building_block_target_inventory(project_root: Path) -> dict:
    ignored = {
        ".git", ".idea", ".program-kit", ".pytest_cache", ".specify", ".venv", ".vs",
        "artifacts", "bin", "build", "coverage", "dist", "node_modules", "obj", "packages",
    }
    candidates: list[dict[str, object]] = [{
        "kind": "repository",
        "path": "Directory.Build.props",
        "exists": (project_root / "Directory.Build.props").is_file(),
        "origin": "observed" if (project_root / "Directory.Build.props").is_file() else "convention",
    }]
    kinds = {
        "package.json": "npm-package",
        "shells.json": "cshell-shell",
        "dotnet-tools.json": "dotnet-tool-manifest",
    }
    for directory, names, files in os.walk(project_root):
        names[:] = [name for name in names if name.casefold() not in ignored]
        base = Path(directory)
        for name in files:
            lowered = name.casefold()
            kind = kinds.get(lowered)
            if lowered.endswith(".csproj"):
                kind = "dotnet-project"
            elif lowered == "dockerfile" or lowered.startswith("dockerfile."):
                kind = "host-image"
            if kind is None:
                continue
            relative = (base / name).relative_to(project_root).as_posix()
            if relative == "Directory.Build.props":
                continue
            candidates.append({"kind": kind, "path": relative, "exists": True, "origin": "observed"})
    candidates.sort(key=lambda item: (str(item["kind"]), str(item["path"]).casefold()))
    truncated = len(candidates) > MAX_BUILDING_BLOCK_TARGETS
    return {
        "canonical_repository_path": "Directory.Build.props",
        "candidates": candidates[:MAX_BUILDING_BLOCK_TARGETS],
        "truncated": truncated,
        "path_rule": (
            "For a selection target value, use an exact forward-slash repository-relative file "
            "path observed in this inventory or explicitly planned by architecture in the Draft target placement declaration. "
            "The repository sentinel is a convention, not evidence of a file. The draft command's "
            "repository-root '--target .' argument is separate. A directory, absolute path, "
            "undeclared guess, or repository-wide search is invalid as a selection target."
        ),
    }


def validate_placement_handoff(inventory: dict, contracts: dict, planning: dict) -> None:
    available = {item["kind"] for item in inventory["candidates"] if item.get("exists")}
    missing = sorted({slot["kind"] for contract in contracts.values()
                      for slot in contract["target_slots"].values()} - available)
    if missing and not (planning.get("authorized") is True
                        and planning.get("owner") == "architecture"
                        and planning.get("declaration")):
        raise ContextError("Architecture placement prerequisite: no observed targets for "
                           + ", ".join(missing)
                           + "; provide the architecture-owned Draft placement planning contract before dispatch.")


def building_block_stage_contract(project_root: Path, intake: dict) -> dict | None:
    catalog_path = project_root / (
        ".specify/extensions/program-kit-building-blocks/references/orbyss-building-blocks.json"
    )
    if not catalog_path.is_file():
        return None
    catalog = load_json(catalog_path)
    capabilities = catalog.get("capabilities")
    compositions = catalog.get("compositions")
    if not isinstance(capabilities, dict) or not isinstance(compositions, dict):
        raise ContextError("Installed building-block catalog has no capability/composition contract")
    routed = intake.get("routing", {}).get("capabilities", [])
    selected = sorted({item for item in routed if item in capabilities})
    if not selected:
        return None
    composition_ids = sorted({
        composition
        for capability in selected
        for composition in capabilities[capability].get("suggestedCompositions", [])
    })
    contracts: dict[str, dict] = {}
    for composition_id in composition_ids:
        composition = compositions.get(composition_id)
        if not isinstance(composition, dict):
            raise ContextError(f"Catalog capability names unknown composition {composition_id}")
        option_groups = []
        for group in composition.get("optionGroups", []):
            option_groups.append({
                "id": group["id"],
                "minimum": group["minimum"],
                "maximum": group["maximum"],
                "options": sorted(group.get("options", {})),
            })
        contracts[composition_id] = {
            "scope_kind": composition["scopeKind"],
            "target_slots": composition["targetSlots"],
            "option_groups": option_groups,
        }
    inventory = building_block_target_inventory(project_root)
    available = {item["kind"] for item in inventory["candidates"] if item["exists"]}
    planning = {
        "owner": "architecture",
        "declaration": "docs/architecture/building-block-selection.json#/targets/*/placement",
        "authorized": True,
        "missing_observed_kinds": sorted({slot["kind"] for contract in contracts.values()
                                          for slot in contract["target_slots"].values()} - available),
        "rules": [
            "Derive physical layout from context/module ownership, deployment boundaries, repository conventions and explicit preferences. Do not ask users for filenames, target IDs or other mechanical placement details.",
            "Each target declares placement.state (observed or planned), owner (canonical element ID with ownership), decisionIds (current owner-linked founding ADRs), and rationale. Planned paths need not exist.",
            "Preserve observed paths, identities and ownership; new placements need an explicit Proposed or Accepted architecture decision. Do not copy extension templates into the observed inventory.",
            "Keep selection Draft and ADRs Proposed pending review. Do not scaffold, restore or materialize during architecture. Ask only about consequential unresolved product constraints or trade-offs.",
        ],
    }
    validate_placement_handoff(inventory, contracts, planning)
    capability_arguments = " ".join(f"--capability {item}" for item in selected)
    return {
        "capabilities": selected,
        "suggested_compositions": composition_ids,
        "draft_command": (
            "python .specify/extensions/program-kit-building-blocks/scripts/building_blocks.py "
            f"draft --target . {capability_arguments}"
        ),
        "composition_contracts": contracts,
        "target_inventory": inventory,
        "placement_planning": planning,
        "rules": [
            "Use this projection instead of running --help or searching/dumping the installed catalog.",
            "The draft command initializes suggestions only. Architecture authors exact scopes, targets with placement provenance, instances, bindings, and compatible options before validation.",
            "Managed option groups constrain research: an unsupported renderer (for example Blazor for forms_runtime) remains unresolved until architecture chooses a supported option or an explicitly reviewed custom adapter/override. Never silently substitute a renderer or change approved product semantics.",
        ],
    }


def managed_web_control_projection(project_root: Path, authorities: dict[str, dict]) -> dict | None:
    decisions = authorities.get("assessment_decisions", {})
    web = decisions.get("web") if isinstance(decisions, dict) else None
    profile = web.get("secure_profile") if isinstance(web, dict) else None
    if not isinstance(profile, str) or profile == "none-v1":
        return None
    evidence_path = project_root / (
        ".specify/extensions/program-kit-dotnet/references/web-security-evidence.json"
    )
    evidence = load_json(evidence_path)
    applicability = evidence.get("controlApplicability", {})
    control_ids = applicability.get(profile) if isinstance(applicability, dict) else None
    if not isinstance(control_ids, list):
        raise ContextError(f"Managed web evidence has no control applicability for {profile}")
    controls = {
        item.get("id"): item
        for item in evidence.get("controls", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    return {
        "profile": profile,
        "threat_model": evidence.get("threatModel"),
        "evidence_profile": evidence.get("id"),
        "controls": [
            {
                "id": control_id,
                "decision": controls[control_id]["decision"],
                "verification": controls[control_id]["verification"],
            }
            for control_id in control_ids
            if control_id in controls
        ],
    }


def stage_plan(project_root: Path, intake: dict, stage: str, authorities: dict[str, dict], run_id: str) -> dict:
    terminal = {
        "command": (
            "python .specify/extensions/program-kit-governance/scripts/bootstrap_context.py "
            f"validate-stage --stage {stage} --run-id {run_id}"
        ),
        "on_success": (
            "Stop immediately. Do not read another file, inspect a diff, measure output again, "
            "or run another command; report only artifact paths, byte counts, and validation counts."
        ),
        "on_failure": "Repair only the named diagnostic, rerun this same batch once, and stop when it passes.",
    }
    if stage == "assessment":
        return {
            "mode": "confirmed-intake-projection",
            "rules": [
                "Use the projected intake and map; do not reconstruct them from repository discovery.",
                "Read required_full_reads once; routed optional references are diagnostic sources only.",
                "Write all three assessment outputs once, then run the supplied validation batch once.",
                "The assessment batch intentionally does not require tooling-evaluation.md; research owns that later prerequisite.",
            ],
            "terminal_condition": terminal,
        }
    if stage == "research":
        questions = [
            {
                "id": item["id"],
                "question": item["question"],
                "classification": item["classification"],
            }
            for item in intake["open_items"]
            if item["classification"] == "research"
        ]
        questions.extend(
            {
                "id": item["id"],
                "question": item["need"],
                "classification": item["decision_state"],
            }
            for item in intake["capability_assessments"]
            if item["decision_state"] == "research-required"
            or item["mechanism_coverage"] in {"conflict", "insufficient-evidence"}
        )
        plan = {
            "mode": "focused-research" if questions else "baseline-verification",
            "research_questions": questions,
            "rules": [
                "Do not survey alternatives unless a listed research question requires it.",
                "For an accepted managed baseline, verify only material compatibility, support, license, or supply-chain risk.",
                "Do not repeat product overviews or re-research accepted architecture choices.",
                "Use observed_toolchain below; do not run local --version, runtime-list, repository-status, or source-tree probes.",
            ],
            "observed_toolchain": observed_toolchain(),
            "building_blocks": building_block_stage_contract(project_root, intake),
            "terminal_condition": terminal,
        }
        if not questions:
            plan["rules"].append(
                "No research question is open: use the managed pins and compact authorities without surveying optional references."
            )
        return plan
    if stage == "architecture":
        return {
            "mode": "patch-canonical-seed",
            "required_order": [
                "Read the canonical seed, constitution, and both output schemas once.",
                "Write founding ADRs and patch the existing map; do not reconstruct it from scratch.",
                "Declare observed/planned placement in the Draft, with semantic owners and decision provenance; choose only compatible managed options.",
                "Run validate-architecture-structure once before narrative documents.",
                "Write compact narrative documents, refresh their map hashes, then run the single final validation batch.",
            ],
            "modeling_invariants": [
                "Preserve every existing element parent unless an accepted decision explicitly changes containment.",
                "Every strategic module references a domain-capability element whose parent equals module.context; every domain-capability has exactly one module record.",
                "Every non-empty capability binding module references one of those strategic modules, never a container.",
                "A C4 component has a container parent. A shell or host directly owned by the software system is a container, not a component.",
                "Keep one unique dynamic view for every confirmed intake journey and preserve each seed journey view's relationship selection and order exactly.",
            ],
            "structural_validation_command": (
                "python .specify/extensions/program-kit-governance/scripts/bootstrap_context.py "
                f"validate-architecture-structure --run-id {run_id}"
            ),
            "building_blocks": building_block_stage_contract(project_root, intake),
            "managed_web_contract": managed_web_control_projection(project_root, authorities),
            "blocked_result": {
                "command": "python .specify/extensions/program-kit-governance/scripts/bootstrap_context.py "
                           f"record-architecture-blocked --run-id {run_id}",
                "required_arguments": ["--reason", "--owner", "--resolution"],
                "rule": "If a prerequisite prevents completion, record the specific reason, accountable owner and next action with this command, then report BLOCKED. Its exit 2 is intentional. Process/dispatch success is not validated architecture completion.",
            },
            "terminal_condition": terminal,
        }
    return {
        "mode": "bounded-generation",
        "rules": [
            "Use the stage projections and open one source only for a decisive omitted field.",
            "Make one write batch and run the single validation batch unless a specific diagnostic requires repair.",
        ],
        "terminal_condition": terminal,
    }


def context_path(run_directory: Path, stage: str) -> Path:
    return run_directory / "program-kit-context" / f"{stage}.json"


def evidence_path(run_directory: Path, stage: str) -> Path:
    return run_directory / "program-kit-context" / f"{stage}.evidence.json"


ARCHITECTURE_BLOCKED = Path(".specify/governance/architecture-blocked.json")


def record_architecture_blocked(project_root: Path, run_id: str, reason: str, owner: str, resolution: str) -> dict:
    if not all(isinstance(value, str) and value.strip() for value in (reason, owner, resolution)):
        raise ContextError("Blocked architecture requires reason, owner and resolution")
    brief = context_path(safe_run_directory(project_root, run_id), "architecture")
    payload = {"status": "blocked", "stage": "architecture", "run_id": run_id,
               "context_sha256": sha256_file(brief), "reason": reason,
               "owner": owner, "resolution": resolution}
    destination = project_root / ARCHITECTURE_BLOCKED
    if destination.exists():
        raise ContextError("A blocked architecture report already exists; preserve it by rebuilding that run's context before retrying")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(compact_json(payload), encoding="utf-8")
    return payload


def check_architecture_blocked(project_root: Path, run_id: str = "") -> None:
    path = project_root / ARCHITECTURE_BLOCKED
    if not path.exists():
        return
    report = load_json(path)
    if (report.get("status") != "blocked" or report.get("stage") != "architecture"
            or not all(isinstance(report.get(key), str) and report[key].strip()
                       for key in ("run_id", "context_sha256", "reason", "owner", "resolution"))):
        raise ContextError("Invalid blocked architecture report; preserve and repair its diagnostic provenance")
    if run_id and report.get("run_id") != run_id:
        raise ContextError("Blocked architecture report belongs to another run; resolve that run before proceeding")
    brief = context_path(safe_run_directory(project_root, report["run_id"]), "architecture")
    if sha256_file(brief) != report.get("context_sha256"):
        raise ContextError("Blocked architecture report has stale context provenance; rebuild its context before retrying")
    raise ContextError(f"Architecture BLOCKED: {report['reason']} Owner: {report['owner']}. "
                       f"Resolution: {report['resolution']}. Dispatch/process exit is not architecture completion.")


def validate_stage_output(project_root: Path, stage: str, run_id: str = "") -> dict:
    if stage == "architecture":
        check_architecture_blocked(project_root, run_id)
    governance_paths = governance_contract(project_root)["paths"]
    contract = resolved_output_contract(stage, governance_paths, run_id)
    artifacts: list[dict] = []
    for relative_path, budget in contract["artifact_byte_budgets"].items():
        path = project_root / relative_path
        if not path.is_file():
            raise ContextError(f"Required {stage} output is missing: {relative_path}")
        size = path.stat().st_size
        if size > budget:
            raise ContextError(
                f"{stage} output exceeds its hard byte budget: "
                f"{relative_path} is {size} bytes; maximum {budget}"
            )
        target = contract["artifact_target_bytes"][relative_path]
        artifacts.append({
            "path": relative_path,
            "bytes": size,
            "target_bytes": target,
            "budget_bytes": budget,
            "target_exceeded": size > target,
        })
    return {
        "stage": stage,
        "artifacts": artifacts,
        "target_exceeded_count": sum(item["target_exceeded"] for item in artifacts),
    }


def _run_project_validator(
    project_root: Path,
    relative_script: str,
    arguments: list[str],
    label: str,
) -> None:
    script = project_root / relative_script
    if not script.is_file():
        raise ContextError(f"{label} validator is missing: {relative_script}")
    try:
        result = subprocess.run(
            [sys.executable, str(script), *arguments],
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ContextError(f"{label} validator could not run: {exc}") from exc
    if result.returncode != 0:
        diagnostic = (result.stderr or result.stdout or "no diagnostic").strip()
        raise ContextError(f"{label} failed: {diagnostic[:4000]}")


def validate_architecture_structure(project_root: Path, run_id: str) -> dict:
    check_architecture_blocked(project_root, run_id)
    map_script = ".specify/extensions/program-kit-governance/scripts/architecture_map.py"
    selection_script = (
        ".specify/extensions/program-kit-building-blocks/scripts/building_blocks.py"
    )
    map_path = "docs/architecture/architecture-map.json"
    dsl_path = "docs/architecture/workspace.dsl"
    _run_project_validator(
        project_root,
        map_script,
        ["validate", "--map", map_path, "--project-root", ".", "--verify-sources"],
        "architecture map",
    )
    checks = ["architecture-map"]
    selection_path = project_root / "docs/architecture/building-block-selection.json"
    intake = load_json(project_root / INTAKE_PATH)
    if building_block_stage_contract(project_root, intake) is not None or selection_path.is_file():
        _run_project_validator(
            project_root,
            selection_script,
            ["validate-draft", "--target", ".", "--require-placement-provenance"],
            "building-block draft",
        )
        checks.append("building-block-draft")
    _run_project_validator(
        project_root,
        map_script,
        [
            "export", "--map", map_path, "--format", "structurizr-dsl",
            "--output", dsl_path, "--force",
        ],
        "architecture DSL export",
    )
    _run_project_validator(
        project_root,
        map_script,
        ["validate", "--map", map_path, "--project-root", ".", "--verify-sources"],
        "exported architecture map",
    )
    validate_architecture_alignment(project_root, run_id)
    checks.extend([
        "architecture-dsl-export",
        "architecture-map-after-export",
        "confirmed-intake-alignment",
    ])
    return {"checks": checks}


def validate_stage_batch(project_root: Path, run_id: str, stage: str) -> dict:
    checks: list[str] = []
    if stage == "architecture":
        checks.extend(validate_architecture_structure(project_root, run_id)["checks"])
    output = validate_stage_output(project_root, stage, run_id)
    checks.append("output-contract")
    governance_script = (
        ".specify/extensions/program-kit-governance/scripts/governance_state.py"
    )
    if stage == "research":
        validate_profile_pin_decisions(project_root, run_id)
        checks.append("managed-profile-pins")
        _run_project_validator(
            project_root, governance_script, ["validate-assessment"], "assessment governance"
        )
        checks.append("assessment-governance")
    elif stage == "architecture":
        _run_project_validator(project_root, governance_script, ["validate"], "architecture governance")
        checks.append("architecture-governance")
    elif stage == "roadmap":
        _run_project_validator(
            project_root,
            governance_script,
            ["validate-roadmap", "--require-ready"],
            "roadmap governance",
        )
        checks.append("roadmap-governance")
    elif stage == "readiness":
        _run_project_validator(
            project_root,
            governance_script,
            ["validate", "--require-roadmap", "--require-ready"],
            "readiness governance",
        )
        checks.append("readiness-governance")
    return {
        "stage": stage,
        "checks": checks,
        "check_count": len(checks),
        "artifact_count": len(output["artifacts"]),
        "target_exceeded_count": output["target_exceeded_count"],
    }


def compact_json(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"


def create_documents(project_root: Path, run_id: str, stage: str) -> tuple[Path, dict, Path, dict]:
    run_directory = safe_run_directory(project_root, run_id)
    if not (run_directory / "inputs.json").is_file():
        raise ContextError(f"Spec Kit workflow inputs are missing for run {run_id}")
    intake = validate_intake(
        project_root,
        run_id,
        allow_architecture_evolution=stage in {"tooling", "roadmap", "readiness"},
    )
    architecture_map = load_json(project_root / "docs/architecture/architecture-map.json")
    governance = governance_contract(project_root)
    governance_paths = governance["paths"]
    output_contract = resolved_output_contract(stage, governance_paths, run_id)
    contract_references = tuple(output_contract["contract_references"])
    routed = routed_references(intake, stage)
    required_routed = required_routed_references(intake, stage)
    stage_artifacts = INTAKE_ARTIFACTS + tuple(
        replace_governance_path(path, governance_paths) for path in STAGE_ARTIFACTS[stage]
    ) + routed + contract_references
    artifacts: list[dict] = []
    authorities: dict[str, dict] = {}
    authority_paths = dict(AUTHORITY_JSON)
    authority_paths[governance_paths["constitution_ratification"]] = "constitution_ratification"
    for relative_path in stage_artifacts:
        record, authority = artifact_record(
            project_root, relative_path, authority_paths.get(relative_path)
        )
        artifacts.append(record)
        if authority:
            authorities[authority[0]] = compact_authority(authority[0], authority[1])
    managed_pins = (
        managed_profile_pin_authority(
            project_root, authorities.get("assessment_decisions", {})
        )
        if stage == "research"
        else None
    )
    # Research must edit and therefore fully read the decision register. Do not also spend model
    # context on a lossy duplicate of that same authority.
    if stage == "research":
        authorities.pop("assessment_decisions", None)
    evidence = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "stage": stage,
        "artifacts": artifacts,
    }
    evidence_destination = evidence_path(run_directory, stage)
    evidence_bytes = compact_json(evidence).encode("utf-8")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "stage": stage,
        "stage_focus": STAGE_FOCUS[stage],
        "stage_plan": stage_plan(project_root, intake, stage, authorities, run_id),
        "bootstrap_intake": intake_record(project_root, run_id),
        "intake": intake_projection(intake, stage),
        "architecture_map": architecture_projection(project_root, architecture_map, stage),
        "authorities": authorities,
        "managed_profile_pins": managed_pins,
        "decisions": decision_records(project_root, governance_paths["decisions"]),
        "governance": governance,
        "output_contract": output_contract,
        "evidence_index": {
            "path": evidence_destination.relative_to(project_root).as_posix(),
            "sha256": sha256_bytes(evidence_bytes),
            "bytes": len(evidence_bytes),
        },
        "reading_policy": {
            "mode": "deny-by-default",
            "required_full_reads": [
                replace_governance_path(path, governance_paths) for path in STAGE_FULL_READS[stage]
            ] + list(required_routed) + list(contract_references),
            "allowed_sources": list(stage_artifacts),
            "rules": [
                "Read this stage brief in full.",
                "Treat intake and architecture_map as stage projections; query the canonical source only for an omitted decisive fact.",
                "Do not print or read the evidence index in full; query one artifact and heading range or JSON field at a time.",
                "Do not open an allowed source unless this brief lacks a fact required for the current output.",
                "Read every listed contract reference once before the first write; do not inspect validator implementation.",
                "Excluded intake routing surfaces are out of scope unless contradictory evidence is cited.",
                "Prefer one targeted source-read batch, one write batch, and one validation batch; expand only for a specific failure.",
                "Treat artifact_target_bytes as the generation ceiling and artifact_byte_budgets as the hard validation boundary.",
                "After writes report only paths, byte counts, status, and targeted diagnostics; never print full files or diffs.",
            ],
            "provenance": "The evidence index binds optional source sections to paths and SHA-256 values.",
        },
    }
    return context_path(run_directory, stage), payload, evidence_destination, evidence


def build_context(project_root: Path, run_id: str, stage: str) -> tuple[Path, dict]:
    destination, payload, evidence_destination, evidence = create_documents(project_root, run_id, stage)
    destination.parent.mkdir(parents=True, exist_ok=True)
    blocked = project_root / ARCHITECTURE_BLOCKED
    if stage == "architecture" and blocked.exists():
        report = load_json(blocked)
        if report.get("run_id") != run_id:
            raise ContextError("Resolve the other run's blocked architecture before rebuilding context")
        # Preserve the diagnostic as immutable attempt evidence before a deliberate retry.
        archive = destination.parent / f"architecture.blocked-{sha256_file(blocked)}.json"
        if not archive.exists():
            archive.write_bytes(blocked.read_bytes())
        blocked.unlink()
    evidence_destination.write_text(compact_json(evidence), encoding="utf-8", newline="\n")
    destination.write_text(compact_json(payload), encoding="utf-8", newline="\n")
    return destination, payload


def validate_context(project_root: Path, run_id: str, stage: str) -> tuple[Path, dict]:
    run_directory = safe_run_directory(project_root, run_id)
    destination = context_path(run_directory, stage)
    evidence_destination = evidence_path(run_directory, stage)
    actual = load_json(destination)
    actual_evidence = load_json(evidence_destination)
    _, expected, _, expected_evidence = create_documents(project_root, run_id, stage)
    if actual != expected or actual_evidence != expected_evidence:
        raise ContextError(f"Bootstrap context is stale or invalid: {destination}")
    return destination, actual


def prepare_architecture_recovery(project_root: Path, run_id: str) -> dict:
    """Preserve the failed handoff and refresh context; never edit workflow/approval state."""
    run = safe_run_directory(project_root, run_id)
    state = load_json(run / "state.json")
    if (state.get("run_id") != run_id or state.get("workflow_id") != "program-kit-bootstrap" or state.get("status") != "failed"
            or state.get("current_step_id") != "validate-architecture-output"):
        raise ContextError("Architecture recovery requires a failed bootstrap at validate-architecture-output")
    if (project_root / ".specify/governance/bootstrap-approval.json").exists():
        raise ContextError("Architecture recovery cannot revise an already approved bootstrap")
    # Validate before writing evidence or replacing context. This keeps confirmed intake and
    # approved assessment semantics authoritative, including for old persisted workflow YAML.
    create_documents(project_root, run_id, "architecture")
    preserved = [run / name for name in ("state.json", "inputs.json", "workflow.yml", "log.jsonl")]
    preserved += [context_path(run, "architecture"), evidence_path(run, "architecture")]
    paths = governance_contract(project_root)["paths"]
    preserved += [project_root / replace_governance_path(name, paths) for name in (
        *INTAKE_ARTIFACTS, *STAGE_ARTIFACTS["architecture"],
    )]
    records = []
    for source in dict.fromkeys(preserved):
        if not source.is_file():
            continue
        digest = sha256_file(source)
        backup = run / "architecture-recovery" / "sources" / digest
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            backup.write_bytes(source.read_bytes())
        elif sha256_file(backup) != digest:
            raise ContextError(f"Preserved recovery evidence has an invalid hash: {backup}")
        records.append({"path": source.relative_to(project_root).as_posix(), "sha256": digest,
                        "preserved_path": backup.relative_to(project_root).as_posix()})
    destination, payload = build_context(project_root, run_id, "architecture")
    result = {
        "run_id": run_id, "status": "ready-for-architecture-retry", "preserved": records,
        "context": result_payload(project_root, destination, payload),
        "architecture_skill_input": "$speckit-program-kit-governance-architecture "
                                    "docs/architecture/bootstrap-intake.json; bootstrap context: "
                                    + destination.relative_to(project_root).as_posix(),
        "validate_command": "python .specify/extensions/program-kit-governance/scripts/bootstrap_context.py "
                            f"validate-stage --stage architecture --run-id {run_id} --json",
        "resume_after_validation": f"specify workflow resume {run_id}",
        "boundary": "Run the installed architecture skill in a user-owned session, review its new Proposed decisions, then validate before resuming. Resume alone only retries the validator. No workflow state or approval was changed.",
    }
    manifest = run / "architecture-recovery" / (sha256_bytes(compact_json(result).encode()) + ".json")
    manifest.write_text(compact_json(result), encoding="utf-8")
    return result


def result_payload(project_root: Path, path: Path, payload: dict) -> dict:
    index = payload["evidence_index"]
    return {
        "path": path.relative_to(project_root).as_posix(),
        "sha256": sha256_file(path),
        "stage": payload["stage"],
        "bytes": path.stat().st_size,
        "evidence_path": index["path"],
        "evidence_bytes": index["bytes"],
    }


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description="Build compact Program Kit bootstrap stage handoffs.")
    parser.add_argument(
        "command",
        choices=(
            "build",
            "validate",
            "validate-output",
            "validate-intake",
            "validate-profile-pins",
            "validate-architecture-alignment",
            "validate-architecture-structure",
            "validate-stage",
            "record-architecture-blocked",
            "prepare-architecture-recovery",
        ),
    )
    parser.add_argument("--stage", choices=tuple(STAGE_ARTIFACTS))
    parser.add_argument("--run-id")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--reason")
    parser.add_argument("--owner")
    parser.add_argument("--resolution")
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    try:
        if args.command != "validate-output" and not args.run_id:
            raise ContextError(f"--run-id is required for {args.command}")
        if args.command == "prepare-architecture-recovery":
            result = prepare_architecture_recovery(project_root, args.run_id)
        elif args.command == "record-architecture-blocked":
            record_architecture_blocked(project_root, args.run_id, args.reason, args.owner, args.resolution)
            check_architecture_blocked(project_root, args.run_id)
        elif args.command == "validate-intake":
            payload = validate_intake(project_root, args.run_id)
            result = {
                "path": INTAKE_PATH.as_posix(),
                "bytes": (project_root / INTAKE_PATH).stat().st_size,
                "fact_count": len(payload["facts"]),
                "journey_count": len(payload["journeys"]),
                "capability_count": len(payload["capability_assessments"]),
                "open_item_count": len(payload["open_items"]),
            }
        elif args.command == "validate-profile-pins":
            authority = validate_profile_pin_decisions(project_root, args.run_id)
            result = {
                "selected_profiles": authority["selected_profiles"],
                "pins": authority["pins"],
                "source_count": len(authority["sources"]),
            }
        elif args.command == "validate-architecture-alignment":
            payload = validate_architecture_alignment(project_root, args.run_id)
            result = {
                "path": INTAKE_PATH.as_posix(),
                "fact_count": len(payload["facts"]),
                "journey_count": len(payload["journeys"]),
                "capability_count": len(payload["capability_assessments"]),
            }
        elif args.command == "validate-architecture-structure":
            result = validate_architecture_structure(project_root, args.run_id)
        elif args.command == "validate-stage":
            if not args.stage:
                raise ContextError("--stage is required for validate-stage")
            result = validate_stage_batch(project_root, args.run_id, args.stage)
        elif args.command == "validate-output":
            if not args.stage:
                raise ContextError("--stage is required for validate-output")
            result = validate_stage_output(project_root, args.stage, args.run_id or "")
        else:
            if not args.stage:
                raise ContextError(f"--stage is required for {args.command}")
            if args.command == "build":
                path, payload = build_context(project_root, args.run_id, args.stage)
            else:
                path, payload = validate_context(project_root, args.run_id, args.stage)
            result = result_payload(project_root, path, payload)
    except (ContextError, OSError, UnicodeError) as exc:
        print(f"Program Kit bootstrap context failed: {exc}", file=sys.stderr)
        return 2
    if args.json or args.command == "prepare-architecture-recovery":
        print(json.dumps(result))
    elif args.command == "validate-intake":
        print(f"Program Kit confirmed bootstrap intake is valid: {result['path']}")
    elif args.command == "validate-profile-pins":
        print(
            "Program Kit selected-profile pins are valid: "
            f"{len(result['pins'])} managed pin(s)"
        )
    elif args.command == "validate-architecture-alignment":
        print("Program Kit architecture remains aligned with the confirmed bootstrap intake")
    elif args.command == "validate-architecture-structure":
        print(
            "Program Kit architecture structural batch passed "
            f"({len(result['checks'])} checks)"
        )
    elif args.command == "validate-stage":
        print(
            f"Program Kit {args.stage} terminal validation batch passed "
            f"({result['check_count']} checks; {result['target_exceeded_count']} above generation target)"
        )
    elif args.command == "validate-output":
        print(
            f"Program Kit {args.stage} outputs are within hard byte budgets "
            f"({result['target_exceeded_count']} above generation target)"
        )
    else:
        print(f"Program Kit {args.stage} context is valid: {result['path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
