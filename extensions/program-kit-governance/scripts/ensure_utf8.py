from __future__ import annotations

import argparse
import sys
from pathlib import Path


CONTENT = '''"""Program Kit UTF-8 bootstrap for Spec Kit Python entry points."""
from __future__ import annotations

import sys

for _program_kit_stream in (sys.stdout, sys.stderr):
    _program_kit_reconfigure = getattr(_program_kit_stream, "reconfigure", None)
    if callable(_program_kit_reconfigure):
        _program_kit_reconfigure(encoding="utf-8", errors="backslashreplace")
'''
MARKER = "# PROGRAM-KIT:UTF8-ENTRYPOINT"
ENTRYPOINT_BOOTSTRAP = '''# PROGRAM-KIT:UTF8-ENTRYPOINT
import sys as _program_kit_sys
for _program_kit_stream in (_program_kit_sys.stdout, _program_kit_sys.stderr):
    _program_kit_reconfigure = getattr(_program_kit_stream, "reconfigure", None)
    if callable(_program_kit_reconfigure):
        _program_kit_reconfigure(encoding="utf-8", errors="backslashreplace")

'''


def hardened(content: str) -> str:
    normalized = content.replace("\r\n", "\n")
    if MARKER in normalized:
        return normalized
    lines = normalized.splitlines(keepends=True)
    future_indexes = [index for index, line in enumerate(lines) if line.startswith("from __future__ import ")]
    insert_at = max(future_indexes) + 1 if future_indexes else 0
    lines.insert(insert_at, ENTRYPOINT_BOOTSTRAP)
    return "".join(lines)


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description="Install idempotent UTF-8 startup for Spec Kit Python scripts.")
    parser.add_argument("--target", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    destination = Path(args.target).resolve() / ".specify" / "scripts" / "python" / "sitecustomize.py"
    desired = CONTENT.replace("\r\n", "\n")
    current = destination.read_text(encoding="utf-8") if destination.is_file() else None
    entrypoints = sorted(path for path in destination.parent.glob("*.py") if path.name != destination.name)
    stale_entrypoints = [
        path for path in entrypoints if hardened(path.read_text(encoding="utf-8")) != path.read_text(encoding="utf-8").replace("\r\n", "\n")
    ]
    if current == desired and not stale_entrypoints:
        print("Spec Kit Python UTF-8 startup is current")
        return 0
    if args.check:
        print(f"PKU001 Spec Kit Python UTF-8 startup is missing or stale: {destination}", file=sys.stderr)
        return 1
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(desired, encoding="utf-8", newline="\n")
    for path in entrypoints:
        content = path.read_text(encoding="utf-8")
        path.write_text(hardened(content), encoding="utf-8", newline="\n")
    print(f"installed Spec Kit Python UTF-8 startup and hardened {len(entrypoints)} entrypoints: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
