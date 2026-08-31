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


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize the Program Kit .NET repository baseline.")
    parser.add_argument("--target", default=".", help="Consuming repository root")
    parser.add_argument("--check", action="store_true", help="Report drift without writing")
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
        source = template_root / "files" / relative
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
