from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# Support the existing importlib-based installed callers as well as direct CLI execution.
_scripts_path = str(Path(__file__).resolve().parent)
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)
from decision_status import has_decision_status as _has_decision_status
from windows_workflow_path import write_bytes as _write_bytes


CONSTITUTION = Path(".specify/memory/constitution.md")
ROADMAP = Path("docs/architecture/specification-roadmap.md")
ARCHITECTURE = Path("docs/architecture/architecture.md")
ARCHITECTURE_MAP = Path("docs/architecture/architecture-map.json")
WORKSPACE_DSL = Path("docs/architecture/workspace.dsl")
DECISIONS = Path("docs/architecture/decisions")
BOOTSTRAP_INTAKE = Path("docs/architecture/bootstrap-intake.json")
PROJECT_INTENT = Path("docs/architecture/project-intent.md")
BOOTSTRAP_DECISIONS = Path("docs/architecture/bootstrap-decisions.json")
CONFIGURATION = Path(
    ".specify/extensions/program-kit-governance/program-kit-governance-config.yml"
)
LOCAL_CONFIGURATION = Path(
    ".specify/extensions/program-kit-governance/program-kit-governance-config.local.yml"
)
EXTENSION_MANIFEST = Path(".specify/extensions/program-kit-governance/extension.yml")
BUILDING_BLOCK_EXTENSION_MANIFEST = Path(".specify/extensions/program-kit-building-blocks/extension.yml")
DOTNET_EXTENSION_MANIFEST = Path(".specify/extensions/program-kit-dotnet/extension.yml")
PRESET_MANIFEST = Path(".specify/presets/program-kit-governance-preset/preset.yml")
PRESET_REGISTRY = Path(".specify/presets/.registry")
BUNDLE_RECORDS = Path(".specify/bundle-records.json")
STATUSES = {"Candidate", "Blocked", "Ready", "Active", "Delivered", "Superseded"}
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


class GovernanceStateError(ValueError):
    pass


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
        top_scalar = re.fullmatch(r"([A-Za-z][A-Za-z0-9_-]*):[ \t]+(.+)", line)
        nested = re.fullmatch(r"  ([A-Za-z][A-Za-z0-9_-]*):\s*(.+)", line)
        if top:
            current = {}
            result[top.group(1)] = current
        elif top_scalar:
            result[top_scalar.group(1)] = _parse_scalar(top_scalar.group(2))
            current = None
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
    global CONSTITUTION, ROADMAP, DECISIONS
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
    return (
        "Inspect the installed toolkit components and preserve authored work. A 0.x consumer needs deliberate "
        "preview re-onboarding; no automatic authority conversion is supported. For an existing preview, "
        "extract both the current and target release, inspect the owned replacement plan, then apply only "
        "the explicitly requested replacement:\n"
        "python <target-release>/scripts/upgrade_program_kit.py --target . "
        "--release-root <target-release> --previous-release-root <current-release> --plan"
    )


def validate_installation() -> dict[str, str]:
    versions = {
        "extension": manifest_version(
            project_path(EXTENSION_MANIFEST), "Program Kit Governance extension"
        ),
        "building-block extension": manifest_version(
            project_path(BUILDING_BLOCK_EXTENSION_MANIFEST), "Program Kit building-block extension"
        ),
        "dotnet extension": manifest_version(
            project_path(DOTNET_EXTENSION_MANIFEST), "Program Kit .NET extension"
        ),
        "preset": manifest_version(
            project_path(PRESET_MANIFEST), "Program Kit Governance preset"
        ),
    }

    preset_registry_path = project_path(PRESET_REGISTRY)
    if not preset_registry_path.is_file():
        raise GovernanceStateError(
            f"Preset registry is missing: {preset_registry_path}\n"
            f"Repair the installation sequentially:\n{repair_commands()}"
        )
    preset_registry = read_json(preset_registry_path).get("presets")
    preset_entry = (
        preset_registry.get("program-kit-governance-preset")
        if isinstance(preset_registry, dict)
        else None
    )
    preset_registry_version = preset_entry.get("version") if isinstance(preset_entry, dict) else None
    if not isinstance(preset_registry_version, str):
        raise GovernanceStateError(
            f"Program Kit Governance preset is absent from the preset registry: {preset_registry_path}\n"
            f"Repair the installation sequentially:\n{repair_commands()}"
        )
    versions["preset registry"] = preset_registry_version

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
    building_block_extension = next(
        (
            component
            for component in components or []
            if isinstance(component, dict)
            and component.get("kind") == "extensions"
            and component.get("id") == "program-kit-building-blocks"
        ),
        None,
    )
    if not isinstance(building_block_extension, dict) or not isinstance(building_block_extension.get("version"), str):
        raise GovernanceStateError(
            "Program Kit building blocks are absent from the Program Kit bundle record.\n"
            f"Repair the installation, in this order:\n{repair_commands()}"
        )
    versions["bundle building-block extension record"] = building_block_extension["version"]
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

    preset_record = next(
        (
            component
            for component in components or []
            if isinstance(component, dict)
            and component.get("kind") == "presets"
            and component.get("id") == "program-kit-governance-preset"
        ),
        None,
    )
    if not isinstance(preset_record, dict) or not isinstance(preset_record.get("version"), str):
        raise GovernanceStateError(
            "Program Kit Governance preset is absent from the Program Kit bundle record.\n"
            f"Repair the installation sequentially:\n{repair_commands()}"
        )
    versions["bundle preset record"] = preset_record["version"]

    if len(set(versions.values())) != 1:
        details = ", ".join(f"{name}={version}" for name, version in versions.items())
        raise GovernanceStateError(
            f"Program Kit installation is version-incoherent ({details}). A bundle operation may "
            "have advanced its record without every installed component. Repair the selected installation before toolkit mutation, "
            "sync, or another component mutation independently. Repair the installation sequentially:\n"
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
    write_text(path, json.dumps(value, indent=2) + "\n")


def write_text(path: Path, value: str) -> None:
    _write_bytes(path, value.encode('utf-8'))


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GovernanceStateError(f"Invalid governance state file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GovernanceStateError(f"Governance state file must be an object: {path}")
    return value


def validate_setup_configuration() -> dict:
    """Inspect only selected setup input; each engineering owner validates its actual operation."""
    value = read_json(project_path(BOOTSTRAP_DECISIONS))
    profiles = value.get('selected_profiles', [])
    if not isinstance(profiles, list) or not all(isinstance(item, str) and item.strip() for item in profiles) or len(profiles) != len(set(profiles)):
        raise GovernanceStateError('selected_profiles must contain distinct nonempty profile names')
    toolchain = value.get('toolchain')
    if toolchain is not None:
        if not isinstance(toolchain, dict) or not isinstance(toolchain.get('pins'), dict):
            raise GovernanceStateError('Selected toolchain needs its explicit pins object')
        if not all(isinstance(key, str) and isinstance(pin, str) and pin.strip() for key, pin in toolchain['pins'].items()):
            raise GovernanceStateError('Toolchain pins must be nonempty strings')
        if toolchain.get('source') == 'override' and not str(toolchain.get('override_reason', '')).strip():
            raise GovernanceStateError('Toolchain overrides need their substantive rationale')
    return value


def validate_constitution_draft() -> None:
    text = project_path(CONSTITUTION).read_text(encoding='utf-8')
    if not text.strip() or not re.search(r'^#\s+\S', text, re.MULTILINE):
        raise GovernanceStateError('Constitution needs a readable title and substantive principles')
    if re.search(r'\[(?:PROJECT_NAME|PRINCIPLE_[^]]*|GOVERNANCE_[^]]*)\]', text):
        raise GovernanceStateError('Replace constitution template placeholders before review')
    body = [line.strip() for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith(('#', '**'))]
    if not body:
        raise GovernanceStateError('Constitution needs authored principles, not only headings/status metadata')


def validate_ratification() -> dict:
    """Inspect readable ratification only when a caller specifically needs that decision."""
    validate_constitution_draft()
    text = project_path(CONSTITUTION).read_text(encoding='utf-8')
    if not re.search(r'^\*\*Status\*\*:\s*Ratified\s*$', text, re.MULTILINE):
        raise GovernanceStateError('Constitution does not record explicit human ratification; review it with the human')
    return {'status': 'Ratified', 'constitution': {'path': CONSTITUTION.as_posix()},
            'evidence_limit': 'Authored human decision; no hash receipt or independent consent proof'}


def accepted_adr(adr_id: str) -> bool:
    decisions = project_path(DECISIONS)
    if not decisions.is_dir():
        return False
    normalized = adr_id.lower()
    for path in decisions.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if normalized in (path.stem + "\n" + text[:500]).lower() and _has_decision_status(
            text, "Accepted"
        ):
            return True
    return False


def roadmap_required_adr_ids(value: str, record_id: str) -> list[str]:
    if value.lower() in {"none", "n/a", "not applicable"}:
        return []
    identifiers = re.findall(r"`([A-Za-z0-9][A-Za-z0-9._-]{1,127})`", value)
    remainder = re.sub(r"`[A-Za-z0-9][A-Za-z0-9._-]{1,127}`", " ", value)
    bare = re.findall(r"\bADR-[A-Z0-9-]+\b", remainder, re.IGNORECASE)
    identifiers.extend(bare)
    remainder = re.sub(r"\bADR-[A-Z0-9-]+\b", " ", remainder, flags=re.IGNORECASE)
    remainder = re.sub(r"(?i)\band\b|[,;]", " ", remainder)
    if remainder.strip() or not identifiers:
        raise GovernanceStateError(
            f"Roadmap record {record_id} Required Accepted ADRs must be None or contain "
            "only exact ADR identifiers (use backticks for non-ADR-* identifiers)"
        )
    return list(dict.fromkeys(identifiers))


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
        if fields.get('Type') == 'Epic':
            missing = {'Completion criteria', 'Feature seeds', 'Intent'} - fields.keys()
            if missing:
                raise GovernanceStateError(f"Epic {match.group(1)} is missing: {', '.join(sorted(missing))}")
            if fields['Intent'] not in {'Intended', 'Exploratory'}:
                raise GovernanceStateError(f"Epic {match.group(1)} has invalid Intent")
            if fields['Intent'] == 'Exploratory' and status in {'Ready', 'Active', 'Delivered'}:
                raise GovernanceStateError(f"Exploratory epic {match.group(1)} cannot claim delivery commitment/status {status}")
        elif 'Type' in fields:
            raise GovernanceStateError(f"Roadmap record {match.group(1)} has unsupported Type: {fields['Type']}")
        records.append({"id": match.group(1), "title": match.group(2), **fields})
    if len({r['id'] for r in records}) != len(records):
        raise GovernanceStateError('Roadmap entry IDs must be unique')
    return records


def epic_feature_ids(record: dict) -> list[str]:
    """Exact IDs, rather than prose matches or shared journey inference."""
    value = record.get('Feature seeds', 'None')
    if value == 'None':
        return []
    identities = [part.strip().strip('`') for part in value.split(',')]
    if any(not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', identity) for identity in identities) or len(set(identities)) != len(identities):
        raise GovernanceStateError(f"{record['id']} Feature seeds must be comma-separated exact candidate IDs or None")
    return identities


def validate_roadmap(require_ready: bool = False, *, verify_delivery: bool = False) -> list[dict[str, str]]:
    records = roadmap_records(project_path(ROADMAP))
    if require_ready and not any(record.get('Status') == 'Ready' for record in records):
        raise GovernanceStateError('The requested structured roadmap has no Ready record')
    return records


def readiness_authority(run_id: str = '') -> dict:
    from product_intake import inspect
    return inspect()


def render_readiness(run_id: str = '') -> dict:
    """Optional content overview; no lifecycle or eligibility report is persisted."""
    result = readiness_authority()
    print(json.dumps(result, ensure_ascii=False))
    return result


def evaluate_readiness() -> dict:
    return readiness_authority()


def main() -> int:
    parser = argparse.ArgumentParser(description='Optional focused Program Kit content and installation checks')
    parser.add_argument('command')
    parser.add_argument('--require-ready', action='store_true')
    parser.add_argument('--require-roadmap', action='store_true')
    args, extra = parser.parse_known_args()
    try:
        configure_paths()
        if args.command == 'validate-installation':
            versions = validate_installation()
            print('Program Kit installation is version-coherent: ' + next(iter(versions.values())))
        elif args.command == 'validate-constitution-draft':
            validate_constitution_draft()
        elif args.command == 'validate':
            validate_ratification()
            if args.require_roadmap:
                validate_roadmap(args.require_ready)
        elif args.command == 'validate-roadmap':
            validate_roadmap(args.require_ready)
        elif args.command == 'validate-setup-configuration':
            validate_setup_configuration()
        elif args.command in {'render-readiness', 'evaluate-readiness'}:
            print(json.dumps(readiness_authority()))
        else:
            print('This authoring receipt/workflow operation is retired. Use product-intake, native speckit.constitution and readable human decisions. Existing historical files are not converted.', file=sys.stderr)
            return 2
        if extra:
            raise GovernanceStateError('Unrecognized arguments for this focused check: ' + ' '.join(extra))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print('Governance check failed: ' + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
