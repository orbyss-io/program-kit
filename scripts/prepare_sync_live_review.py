"""Create a reproducible, credential-free live-test review packet. Never starts a worker."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENARIO = ROOT / "tests/live/scenarios/repository-sync/v1"


def inventory(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Live fixture cannot contain symbolic links: {path}")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    if not result:
        raise ValueError(f"Empty live fixture: {root}")
    return result


def prepare(scenario: Path = SCENARIO) -> dict:
    cases = json.loads((scenario / "cases.json").read_text(encoding="utf-8"))
    seed = (scenario / cases["inputs"]["consumerSeed"]).resolve()
    scenario_root = scenario.parents[1].resolve()
    if not seed.is_relative_to(scenario_root):
        raise ValueError("Consumer seed must stay inside the live scenario directory")
    request = (scenario / cases["inputs"]["request"]).resolve()
    if not request.is_relative_to(scenario.resolve()) or not request.is_file():
        raise ValueError("Feature request must exist inside its fixture")
    inventories = {"exercise": inventory(scenario), "consumerSeed": inventory(seed)}
    digest = hashlib.sha256(json.dumps(inventories, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "schemaVersion": "1.0", "status": "prepared-not-authorized", "fixtureDigest": digest,
        "inventories": inventories, "cases": cases["cases"], "metrics": cases["metrics"],
        "unboundRequirements": ["baselineCandidateReceipt", "candidateCandidateReceipt", "sealedCheckpoints",
                                "modelAndReasoningEffort", "humanFeatureConfirmation", "functionalAcceptanceEvidence"],
        "stageRunner": "scripts/Test-LiveRepositorySync.ps1",
        "paidSessionsStarted": 0, "authorizationIssued": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    packet = prepare()
    output = args.output.resolve()
    if output.is_relative_to((ROOT / "tests/live/scenarios").resolve()):
        raise ValueError("Write generated review packets outside source fixtures")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Prepared live review {packet['fixtureDigest']}: {output}; no authorization issued or worker started.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
