from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


IDENTITY = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")


def configure_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="backslashreplace")


def activate(args: argparse.Namespace) -> int:
    path = Path(args.shells)
    value = json.loads(path.read_text(encoding="utf-8"))
    try:
        shells = value["CShells"]["Shells"]
        shell = shells[args.shell]
        features = shell["Features"]
    except (KeyError, TypeError) as error:
        raise ValueError(
            f"PKF004 shells.json does not match the CShells:Shells:<name>:Features schema for shell '{args.shell}'."
        ) from error
    if not isinstance(features, dict):
        raise ValueError(f"PKF005 Features must be an object for shell '{args.shell}'.")
    if args.feature in features:
        raise ValueError(f"PKF006 feature '{args.feature}' is already activated in shell '{args.shell}'.")
    if not IDENTITY.fullmatch(args.feature):
        raise ValueError(f"PKF007 invalid feature identity: {args.feature!r}")
    features[args.feature] = {}
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"activated feature {args.feature} in shell {args.shell}")
    return 0


def main() -> int:
    configure_utf8()
    parser = argparse.ArgumentParser(description="Update CShells activation; descriptor emission belongs to Orbyss.Foundation.Build during pack.")
    commands = parser.add_subparsers(dest="command", required=True)
    activate_parser = commands.add_parser("activate")
    activate_parser.add_argument("--shells", default="shells.json")
    activate_parser.add_argument("--shell", required=True)
    activate_parser.add_argument("--feature", required=True)
    args = parser.parse_args()
    try:
        return activate(args)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
