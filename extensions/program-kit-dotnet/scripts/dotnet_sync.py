from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def extension_version(extension_root: Path) -> str:
    content = (extension_root / "extension.yml").read_text(encoding="utf-8")
    match = re.search(r'^\s*version:\s*"([^"]+)"\s*$', content, re.MULTILINE)
    if match is None:
        raise ValueError("Could not read the Program Kit extension version.")
    return match.group(1)


def load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object in {path}")
    return value


def selected_web_profile(target: Path, requested: str) -> str:
    """Resolve an explicit profile or derive the secure default from reviewed bootstrap evidence."""
    if requested != "auto":
        return requested

    decision_path = target / "docs" / "architecture" / "bootstrap-decisions.json"
    if decision_path.is_file():
        decisions = load_json(decision_path, {})
        web = decisions.get("web")
        if isinstance(web, dict):
            selected = web.get("secure_profile")
            approved_profiles = {
                "none-v1": "none",
                "bff-cookie-v1": "bff-cookie",
                "spa-pkce-v1": "spa-pkce",
            }
            if selected in approved_profiles:
                return approved_profiles[selected]

    evidence_paths = [
        target / "docs" / "initial-design.md",
        target / "INITIAL_DESIGN.md",
        target / "initial_design.md",
    ]
    evidence = "\n".join(
        path.read_text(encoding="utf-8").lower() for path in evidence_paths if path.is_file()
    )
    browser_markers = ("browser", "react", "single-page", "single page", "spa", "typescript")
    return "bff-cookie" if any(marker in evidence for marker in browser_markers) else "none"


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description="Synchronize the Program Kit .NET repository baseline.")
    parser.add_argument("--target", default=".", help="Consuming repository root")
    parser.add_argument("--check", action="store_true", help="Report drift without writing")
    parser.add_argument(
        "--web-profile",
        choices=("auto", "none", "bff-cookie", "spa-pkce"),
        default="auto",
        help="Secure web boundary profile; auto adopts BFF for a detected browser UI",
    )
    parser.add_argument(
        "--profile-selected",
        action="store_true",
        help="Confirms that the consuming repository accepted the .NET technology profile",
    )
    parser.add_argument(
        "--host-runtime-accepted",
        action="store_true",
        help="Confirms that the approved bootstrap baseline or a later Accepted override selects ProgramKit.Host",
    )
    parser.add_argument(
        "--preview-sources-approved",
        action="store_true",
        help="Confirms explicit approval to add the Program Kit preview packages and NuGet sources",
    )
    parser.add_argument(
        "--persistence-profile",
        choices=("none", "ef-postgresql", "ef-sqlserver", "ef-sqlite"),
        default="none",
        help="Explicit governed persistence profile; none keeps all providers inactive",
    )
    args = parser.parse_args()

    if not args.profile_selected:
        print("Refusing to scaffold: the .NET technology profile was not explicitly selected.", file=sys.stderr)
        return 3
    if not args.check and not args.host_runtime_accepted:
        print(
            "Refusing to scaffold: the Program Kit host/runtime choice is not confirmed by the approved "
            "bootstrap baseline or a later Accepted override.",
            file=sys.stderr,
        )
        return 4
    if not args.check and not args.preview_sources_approved:
        print(
            "Refusing to scaffold: adding preview packages and NuGet sources was not explicitly approved.",
            file=sys.stderr,
        )
        return 5

    extension_root = Path(__file__).resolve().parents[1]
    template_root = extension_root / "templates" / "dotnet"
    template_manifest = load_json(template_root / "managed-files.json", {})
    entries = template_manifest.get("files")
    if not isinstance(entries, list):
        raise ValueError("The .NET template manifest has no files list.")

    target = Path(args.target).resolve()
    web_profile = selected_web_profile(target, args.web_profile)
    print(f"selected web profile: {web_profile}")
    print(f"selected persistence profile: {args.persistence_profile}")
    profile_manifest_path = template_root / "web-profiles" / web_profile / "managed-files.json"
    if profile_manifest_path.is_file():
        profile_manifest = load_json(profile_manifest_path, {})
        profile_entries = profile_manifest.get("files")
        if not isinstance(profile_entries, list):
            raise ValueError(f"The {web_profile} profile manifest has no files list.")
        profile_destinations = {entry["path"] for entry in profile_entries}
        entries = [entry for entry in entries if entry["path"] not in profile_destinations]
        entries.extend(profile_entries)
    if not args.check:
        target.mkdir(parents=True, exist_ok=True)
    state_path = target / ".program-kit" / "managed.json"
    state = load_json(state_path, {"schemaVersion": 1, "files": {}})
    old_files = state.get("files")
    if not isinstance(old_files, dict):
        raise ValueError(f"Invalid managed-file state in {state_path}")

    created: list[str] = []
    updated: list[str] = []
    unchanged: list[str] = []
    conflicts: list[str] = []
    next_files: dict[str, dict[str, str]] = {}

    for entry in entries:
        relative = entry["path"]
        ownership = entry["ownership"]
        source_root = template_root / entry.get("sourceRoot", "files")
        source = source_root / entry.get("source", relative)
        destination = target / relative
        desired = source.read_bytes()
        desired_hash = sha256_bytes(desired)
        previous = old_files.get(relative)

        if not destination.exists():
            created.append(relative)
            if not args.check:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
            current_hash = desired_hash
        else:
            current = destination.read_bytes()
            current_hash = sha256_bytes(current)
            if current_hash == desired_hash:
                unchanged.append(relative)
            elif ownership == "managed" and isinstance(previous, dict) and current_hash == previous.get("installedHash"):
                updated.append(relative)
                if not args.check:
                    shutil.copyfile(source, destination)
                current_hash = desired_hash
            else:
                conflicts.append(relative)

        next_files[relative] = {
            "ownership": ownership,
            "templateHash": desired_hash,
            "installedHash": current_hash,
        }

    print(f"created: {len(created)}")
    for path in created:
        print(f"  + {path}")
    print(f"updated: {len(updated)}")
    for path in updated:
        print(f"  ~ {path}")
    print(f"unchanged: {len(unchanged)}")
    print(f"conflicts: {len(conflicts)}")
    for path in conflicts:
        print(f"  ! {path}")

    if conflicts:
        print("Resolve conflicts explicitly; no conflicted file was overwritten.", file=sys.stderr)
        return 2

    if args.check:
        return 1 if created or updated else 0

    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "programKitVersion": extension_version(extension_root),
                "webProfile": web_profile,
                "webProfileContract": f"{web_profile}-v1",
                "webThreatModel": (
                    "program-kit-web-threat-model-v1" if web_profile != "none" else "none"
                ),
                "webSecurityEvidence": (
                    "program-kit-web-security-evidence-v1" if web_profile != "none" else "none"
                ),
                "persistenceProfile": args.persistence_profile,
                "files": next_files,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
