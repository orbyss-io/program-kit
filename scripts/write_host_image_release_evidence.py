from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Write immutable Program Kit host-image release evidence.")
    parser.add_argument("--version", required=True)
    parser.add_argument("--runtime-version", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--digest", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", args.version):
        raise ValueError("PKH001 version must be an exact stable Program Kit version")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+-preview\.[0-9]+", args.runtime_version):
        raise ValueError("PKH001 runtime version must be an exact Program Kit preview version")
    if not re.fullmatch(r"[a-f0-9]{40,64}", args.source_commit):
        raise ValueError("PKH001 source commit must be a lowercase Git object id")
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", args.digest):
        raise ValueError("PKH001 image digest must be a lowercase sha256 digest")
    repository = "ghcr.io/orbyss-io/program-kit-host"
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "programKitVersion": args.version,
                "runtimeVersion": args.runtime_version,
                "releaseTag": f"v{args.version}",
                "sourceCommit": args.source_commit,
                "hostImage": {
                    "repository": repository,
                    "tag": args.runtime_version,
                    "digest": args.digest,
                    "reference": f"{repository}@{args.digest}",
                },
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
