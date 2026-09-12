"""Feature-scoped grilling review and confirmation; never creates a spec or branch."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import governance_state as governance
from lifecycle_state import atomic_write


FIELDS = (
    "problem", "users", "outcome", "scope", "nonGoals", "journeys",
    "failureCases", "dependencies", "acceptanceCriteria",
)
DISPOSITIONS = {"answered", "default", "excluded", "deferred", "open"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("PKS001 " + message)


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"Expected an object: {path}")
    return value


def inside(repository: Path, relative: str) -> Path:
    path = (repository / relative).resolve()
    require(path.is_relative_to(repository), "Evidence paths must stay inside the repository")
    return path


def directory(repository: Path, entry: str) -> Path:
    require(bool(re.fullmatch(r"[A-Z][A-Z0-9-]+", entry)), "Use the exact roadmap entry ID")
    return inside(repository, f".program-kit/specification-intake/{entry}")


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_brief(brief: dict, entry: str) -> None:
    require(brief.get("schemaVersion") == 1 and brief.get("roadmapEntry") == entry,
            "Brief schema or roadmap identity does not match")
    for key in ("request", *FIELDS):
        require(nonempty(brief.get(key)), f"Brief requires {key}")
    decisions = brief.get("decisions")
    require(isinstance(decisions, list) and bool(decisions), "Record the reviewed decisions and their provenance")
    ids = [item.get("id") for item in decisions if isinstance(item, dict)]
    require(len(ids) == len(decisions) and all(nonempty(i) for i in ids) and len(set(ids)) == len(ids),
            "Decision IDs must be present and unique")
    by_id = {item["id"]: item for item in decisions}
    for item in decisions:
        for key in ("question", "answer", "provenance", "rationale"):
            require(nonempty(item.get(key)), f"{item['id']} requires {key}")
        status = item.get("disposition")
        require(status in DISPOSITIONS and status != "open", f"{item['id']} is unresolved")
        require(isinstance(item.get("blocking"), bool), f"{item['id']} requires a blocking boolean")
        dependencies = item.get("dependsOn")
        require(isinstance(dependencies, list) and all(isinstance(d, str) and d in by_id for d in dependencies),
                f"{item['id']} has unknown dependencies")
        require(item['id'] not in dependencies, "A decision cannot depend on itself")
        if status == "deferred":
            require(not item["blocking"], f"{item['id']} blocks specification and cannot be deferred")
            require(nonempty(item.get("owner")) and nonempty(item.get("trigger")),
                    f"{item['id']} needs a deferral owner/next action and trigger")
        if status in {"answered", "default"}:
            require(all(by_id[d].get("disposition") in {"answered", "default"} for d in dependencies),
                    f"{item['id']} relies on an unsettled premise")
    visited, active = set(), set()

    def visit(identity: str) -> None:
        require(identity not in active, "Decision dependencies contain a cycle")
        if identity in visited:
            return
        active.add(identity)
        for parent in by_id[identity]["dependsOn"]:
            visit(parent)
        active.remove(identity)
        visited.add(identity)

    for identity in by_id:
        visit(identity)


def context(repository: Path, entry: str, *, later: bool = False) -> dict:
    # CLI establishes cwd so configurable governance paths retain their normal semantics.
    governance.configure_paths()
    governance.validate_installation()
    governance.validate_ratification()
    records = governance.validate_roadmap(False)
    selected = [record for record in records if record["id"] == entry]
    require(len(selected) == 1, "Select exactly one existing roadmap entry")
    record = selected[0]
    require(record["Status"] in ({"Ready", "Active", "Delivered"} if later else {"Ready", "Active"}),
            f"Selected roadmap entry {entry} is not Ready or Active")
    if record["Status"] == "Active" and not later:
        pointer = read(repository / ".specify/feature.json")
        feature_directory = pointer.get("feature_directory")
        require(nonempty(feature_directory), "Active intake needs the existing Spec Kit feature context")
        spec = inside(repository, feature_directory) / "spec.md"
        require(spec_entries(spec.read_text(encoding="utf-8")) == [entry],
                "An Active entry may only resume its existing specification; select a Ready entry for a new feature")
    paths = [governance.CONSTITUTION, governance.ARCHITECTURE]
    for adr in governance.roadmap_required_adr_ids(record["Required Accepted ADRs"], entry):
        matches = [p for p in governance.project_path(governance.DECISIONS).rglob("*.md")
                   if adr.lower() in (p.stem + "\n" + p.read_text(encoding="utf-8")[:500]).lower()]
        require(bool(matches), f"Required ADR {adr} is missing")
        paths.extend(p.relative_to(repository) for p in matches)
    return {
        # Lifecycle progress and unrelated roadmap entries do not invalidate feature intent.
        "roadmap": {key: value for key, value in record.items() if key != "Status"},
        "sources": {str(p).replace("\\", "/"): hashlib.sha256(inside(repository, str(p)).read_bytes()).hexdigest()
                    for p in sorted(set(paths))},
    }


def review_text(brief: dict, basis: dict) -> str:
    lines = [f"# Specification intake: {brief['roadmapEntry']}", "", "## Request", brief["request"]]
    for field in FIELDS:
        lines += ["", f"## {field}", brief[field]]
    lines += ["", "## Decisions, defaults and deferred work"]
    for item in brief["decisions"]:
        lines += ["", f"### {item['id']}: {item['question']}", item["answer"],
                  f"Disposition: {item['disposition']}; blocking: {item['blocking']}",
                  f"Provenance: {item['provenance']}", f"Rationale: {item['rationale']}",
                  "Depends on: " + (", ".join(item["dependsOn"]) or "none")]
        if item["disposition"] == "deferred":
            lines += [f"Owner / next action: {item['owner']}", f"Trigger: {item['trigger']}"]
    lines += ["", "## Review basis", f"Brief SHA256: {digest(brief)}", f"Context SHA256: {digest(basis)}", ""]
    return "\n".join(lines)


def prepare(repository: Path, entry: str, *, later: bool = False) -> tuple[Path, dict, dict, str]:
    folder = directory(repository, entry)
    brief = read(folder / "brief.json")
    validate_brief(brief, entry)
    basis = context(repository, entry, later=later)
    return folder, brief, basis, review_text(brief, basis)


def begin(repository: Path, entry: str, request: str) -> Path:
    context(repository, entry)
    path = directory(repository, entry) / "brief.json"
    if path.exists():
        require(read(path).get("roadmapEntry") == entry, "Existing interview has a different identity")
        return path  # Resume without discarding answers or replacing the original request.
    require(nonempty(request), "An initial feature request is required")
    atomic_write(path, {"schemaVersion": 1, "roadmapEntry": entry, "request": request,
                        **{field: "" for field in FIELDS}, "decisions": []})
    return path


def review(repository: Path, entry: str) -> dict:
    folder, brief, basis, text = prepare(repository, entry)
    (folder / "review.md").write_text(text, encoding="utf-8", newline="\n")
    result = {"briefHash": digest(brief), "context": basis,
              "reviewHash": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    atomic_write(folder / "review-basis.json", result)
    return result


def current_review(repository: Path, entry: str, *, later: bool = False) -> tuple[Path, dict]:
    folder, brief, basis, text = prepare(repository, entry, later=later)
    expected = {"briefHash": digest(brief), "context": basis,
                "reviewHash": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    require(read(folder / "review-basis.json") == expected, "Review is stale; reopen affected decisions and review again")
    require((folder / "review.md").read_bytes() == text.encode("utf-8"), "Review text has changed; regenerate and review again")
    return folder, expected


def confirm(repository: Path, entry: str, review_hash: str, source: str, answer: str) -> dict:
    folder, expected = current_review(repository, entry)
    require(review_hash == expected["reviewHash"], "Confirmation must name the exact presented review hash")
    require(nonempty(source) and nonempty(answer), "Record the explicit user confirmation and its conversation source")
    receipt = {"schemaVersion": 1, "roadmapEntry": entry, **expected,
               "confirmationSource": source, "confirmationText": answer,
               "confirmedAtUtc": datetime.now(timezone.utc).isoformat()}
    atomic_write(folder / "confirmation.json", receipt)
    return receipt


def check(repository: Path, entry: str, *, later: bool = False) -> dict:
    folder, expected = current_review(repository, entry, later=later)
    receipt = read(folder / "confirmation.json")
    require(receipt.get("schemaVersion") == 1 and receipt.get("roadmapEntry") == entry,
            "Confirmation belongs to another feature or unsupported schema")
    require(all(receipt.get(key) == value for key, value in expected.items()), "Confirmation is stale")
    require(all(nonempty(receipt.get(key)) for key in ("confirmationSource", "confirmationText", "confirmedAtUtc")),
            "Explicit user confirmation evidence is missing")
    return {"roadmapEntry": entry, "briefHash": expected["briefHash"],
            "brief": (folder / "brief.json").relative_to(repository).as_posix()}


def spec_entries(text: str) -> list[str]:
    return re.findall(r"^\s*- \*\*Specification roadmap entry\*\*:\s*([A-Z][A-Z0-9-]+)\b.*$", text, re.MULTILINE)


def check_spec(repository: Path, spec_path: Path) -> dict:
    require(spec_path.resolve().is_relative_to(repository), "Spec must stay inside the repository")
    text = spec_path.read_text(encoding="utf-8")
    identities = spec_entries(text)
    hashes = re.findall(r"^\s*- \*\*Confirmed intake SHA256\*\*:\s*([0-9a-f]{64})\s*$", text, re.MULTILINE)
    references = re.findall(r"^\s*- \*\*Confirmed intake brief\*\*:\s*(\S+)\s*$", text, re.MULTILINE)
    require(len(identities) == len(hashes) == len(references) == 1,
            "Spec requires one roadmap entry, confirmed intake brief and SHA256; run specification-intake")
    result = check(repository, identities[0], later=True)
    require(hashes[0] == result["briefHash"] and references[0] == result["brief"],
            "Spec intake reference differs from the current confirmed brief")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=".")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("begin", "review", "confirm", "check"):
        command = commands.add_parser(name)
        command.add_argument("--entry", required=True)
        if name == "begin":
            command.add_argument("--request", required=True)
        if name == "confirm":
            command.add_argument("--review-sha256", required=True)
            command.add_argument("--confirmation-source", required=True)
            command.add_argument("--confirmation-text", required=True)
    commands.add_parser("check-spec").add_argument("--spec", required=True)
    args = parser.parse_args()
    repository = Path(args.repository).resolve()
    previous = Path.cwd()
    try:
        os.chdir(repository)
        if args.command == "begin":
            result = str(begin(repository, args.entry, args.request))
        elif args.command == "review":
            result = review(repository, args.entry)
        elif args.command == "confirm":
            result = confirm(repository, args.entry, args.review_sha256, args.confirmation_source, args.confirmation_text)
        elif args.command == "check":
            result = check(repository, args.entry)
        else:
            result = check_spec(repository, inside(repository, args.spec))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"Specification intake blocked: {error}", file=sys.stderr)
        return 1
    finally:
        os.chdir(previous)


if __name__ == "__main__":
    raise SystemExit(main())
