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
DECISIONS = Path("docs/architecture/decisions")
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


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GovernanceStateError(f"Invalid ratification record {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GovernanceStateError(f"Ratification record must be an object: {path}")
    return value


def constitution_metadata(path: Path) -> tuple[str, str, str]:
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
    match = re.search(
        r"\*\*Version\*\*:\s*([^|\s]+)\s*\|\s*"
        r"\*\*Ratified\*\*:\s*(\d{4}-\d{2}-\d{2})\s*\|\s*"
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
        try:
            date.fromisoformat(value)
        except ValueError as exc:
            raise GovernanceStateError(f"{label} date is invalid: {value}") from exc
    return version, ratified, amended


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


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Program Kit governance state")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("begin")
    ratify_parser = subparsers.add_parser("ratify")
    ratify_parser.add_argument("--verdict", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--require-roadmap", action="store_true")
    validate_parser.add_argument("--require-ready", action="store_true")
    roadmap_parser = subparsers.add_parser("validate-roadmap")
    roadmap_parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "begin":
            begin()
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
    except GovernanceStateError as exc:
        print(f"governance state error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
