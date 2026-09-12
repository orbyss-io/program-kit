"""Resolve exact npm metadata through the shared package execution context."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import package_execution
from npm_graph import write_evidence


def resolve(repository: Path, package: str, version: str, toolchain: Path, evidence: Path, timeout: int) -> None:
    package_execution.routes([package])
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?", version):
        raise ValueError("PKP004 metadata requires an exact npm version, not a range or moving tag")
    proof = {"schemaVersion": 1, "package": package, "version": version, "satisfied": False}
    if evidence.is_file():
        try:
            previous = json.loads(evidence.read_text(encoding="utf-8"))
            context = package_execution.context_proof(repository, toolchain, [package])
            if (previous.get("satisfied") is True and previous.get("package") == package and previous.get("version") == version
                    and previous.get("executionContext", {}).get("contextDigest") == context["contextDigest"]
                    and previous.get("metadataSha256") == package_execution.canonical_hash(previous.get("metadata"))):
                package_execution.javascript_runtime().context(repository, toolchain)
                return
        except (OSError, ValueError):
            pass
    write_evidence(evidence, proof)
    result, context = package_execution.execute(repository, toolchain, [package], ["view", f"{package}@{version}", "--json"], repository, timeout)
    proof["executionContext"] = context
    if result.returncode != 0:
        write_evidence(evidence, proof)
        raise ValueError(f"PKP005 metadata failed ({context['failureCategory']}): {result.stderr[-2000:]}")
    metadata = json.loads(result.stdout)
    if not isinstance(metadata, dict) or metadata.get("name") != package or metadata.get("version") != version:
        raise ValueError("PKP005 registry returned metadata for a different package or version")
    proof.update(satisfied=True, metadata=metadata, metadataSha256=package_execution.canonical_hash(metadata))
    write_evidence(evidence, proof)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--package", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--toolchain-evidence", type=Path, default=Path(".program-kit/evidence/toolchain.json"))
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    args = parser.parse_args()
    repository = args.repository.resolve()
    try:
        if args.timeout_seconds < 1:
            raise ValueError("PKP004 timeout must be positive")
        resolve(repository, args.package, args.version, repository / args.toolchain_evidence,
                repository / args.evidence, args.timeout_seconds)
        print(f"PKP000 exact npm metadata recorded: {args.evidence}")
        return 0
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
