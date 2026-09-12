"""Compare independently reviewed live evidence; preparation is never a passing run."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from live.v2.common import canonical_sha256, load_object, validate


METRICS = (
    "setupDiscoveryCommands", "wrongRegistryRequests", "packageResolutionAttempts",
    "repeatedUnchangedOperations", "consumerSetupHelpers", "setupFailures", "humanInterventions",
)
MATCHED_INPUTS = (
    "fixtureDigest", "architectureDigest", "componentPinsDigest", "toolchainDigest",
    "model", "reasoningEffort", "stageLimitsDigest", "cachePolicy",
)


def evidence_ref(root: Path, reference: dict) -> None:
    if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
        raise ValueError("Invalid evidence reference")
    path = (root / reference["path"]).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("Evidence must exist inside its preserved run directory")
    if hashlib.sha256(path.read_bytes()).hexdigest() != reference["sha256"]:
        raise ValueError("Evidence hash changed")


def validated_report(path: Path, cases: dict) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    case = next((case for case in cases["cases"] if case["id"] == report.get("caseId")), None)
    if case is None or report.get("status") != "passed" or report.get("execution") != "paid-live-v2":
        raise ValueError("Only completed paid live cases can establish improvement")
    bindings = report.get("bindings", {})
    for field in (*MATCHED_INPUTS, "releaseReceiptSha256", "checkpointDigest"):
        if not isinstance(bindings.get(field), str) or not bindings[field].strip():
            raise ValueError(f"Missing comparison binding: {field}")
    for field in ("authorization", "workerStdout", "workerStderr", "independentValidation"):
        evidence_ref(path.parent, report.get(field))
    for field in ('liveRunManifest', 'checkpoint'):
        evidence_ref(path.parent, report.get(field))
    run = load_object(path.parent / report['liveRunManifest']['path'])
    unsigned = dict(run)
    if unsigned.pop('manifestSha256', None) != canonical_sha256(unsigned):
        raise ValueError('Live run manifest seal is invalid')
    schemas = Path(__file__).resolve().parents[1] / 'schemas/v2'
    validate(run, load_object(schemas / 'evidence-manifest.schema.json'))
    phase = 'upgrade-consumer' if case['id'] == 'upgrade-candidate' else 'feature-delivery'
    if run['phase'] != phase or run['status'] not in {'passed','checkpoint-created'}:
        raise ValueError('A completed delivery/upgrade stage is required')
    process = run['process']
    if process.get('exitCode') != 0 or process.get('cleanupComplete') is not True or process.get('logsDrained') is not True:
        raise ValueError('Live worker execution did not complete cleanly')
    authorization = load_object(path.parent / report['authorization']['path'])
    validate(authorization, load_object(schemas / 'authorization.schema.json'))
    kind = authorization['candidate'].get('receiptKind', 'release')
    if run['candidate'].get('receiptKind', 'release') != kind:
        raise ValueError('Comparison receipt scope differs from the authorized live run')
    report['receiptKind'] = kind
    if (authorization['phase'] != phase or run['authorization']['authorizationId'] != authorization['authorizationId']
            or run['authorization']['authorizationSha256'] != canonical_sha256(authorization)
            or run['candidate']['releaseReceiptSha256'] != bindings['releaseReceiptSha256']
            or authorization['candidate']['releaseReceiptSha256'] != bindings['releaseReceiptSha256']):
        raise ValueError('Comparison does not bind the consumed live authorization and candidate')
    for key in ('model','reasoningEffort'):
        if run['agentProfile'].get(key) != bindings[key] or authorization['agentProfile'].get(key) != bindings[key]:
            raise ValueError('Comparison model profile differs from the actual live run')
    for index, field in enumerate(('workerStdout','workerStderr')):
        if len(run['logs']) <= index or run['logs'][index].get('object',{}).get('sha256') != report[field]['sha256']:
            raise ValueError('Comparison stream differs from sealed worker evidence')
    checkpoint = load_object(path.parent / report['checkpoint']['path'])
    validate(checkpoint, load_object(schemas / 'checkpoint.schema.json'))
    if report['checkpoint']['sha256'] != bindings['checkpointDigest'] or checkpoint['candidate'] != bindings['releaseReceiptSha256'] or checkpoint['phase'] != phase:
        raise ValueError('Comparison checkpoint binding differs from the live result')
    independent = load_object(path.parent / report['independentValidation']['path'])
    if independent.get('status') != 'passed' or independent.get('functionalAcceptance') is not True:
        raise ValueError('Independent functional acceptance is required, not just a stage checkpoint')
    for assertion in case["assertions"]:
        result = report.get("assertions", {}).get(assertion, {})
        if result.get("passed") is not True:
            raise ValueError(f"Independent assertion not passed: {assertion}")
        evidence_ref(path.parent, result.get("evidence"))
    for metric in METRICS:
        value = report.get("metrics", {}).get(metric, {})
        count = value.get("count")
        if count is not None and (type(count) is not int or count < 0):
            raise ValueError(f"Invalid metric count: {metric}")
        if not value.get("rationale") or not value.get("evidence"):
            raise ValueError(f"Metric lacks evidence/classification: {metric}")
        for reference in value["evidence"]:
            evidence_ref(path.parent, reference)
    return report


def compare(baseline: Path, candidate: Path, cases: dict) -> dict:
    before, after = (validated_report(path, cases) for path in (baseline, candidate))
    if before["caseId"] != "fresh-baseline" or after["caseId"] != "fresh-candidate":
        raise ValueError("Compare fresh-baseline with fresh-candidate; upgrade is a separate acceptance case")
    mismatches = [key for key in MATCHED_INPUTS if before["bindings"][key] != after["bindings"][key]]
    if before['receiptKind'] != after['receiptKind']:
        mismatches.append('receiptKind')
    if mismatches:
        raise ValueError(f"Runs are not equivalent: {', '.join(mismatches)}")
    if before["bindings"]["releaseReceiptSha256"] == after["bindings"]["releaseReceiptSha256"]:
        raise ValueError("Baseline and candidate must identify different release receipts")
    measurements = {}
    for metric in METRICS:
        old = before["metrics"][metric]["count"]
        new = after["metrics"][metric]["count"]
        measurements[metric] = {"baseline": old, "candidate": new,
                                "delta": None if old is None or new is None else new - old}
    required_zero = ("wrongRegistryRequests", "consumerSetupHelpers", "repeatedUnchangedOperations")
    complete = all(value["delta"] is not None for value in measurements.values())
    meets_efficiency_gate = complete and all(measurements[key]["candidate"] == 0 for key in required_zero)
    increased = [key for key, value in measurements.items() if value["delta"] is not None and value["delta"] > 0]
    decreased = [key for key, value in measurements.items() if value["delta"] is not None and value["delta"] < 0]
    return {
        "schemaVersion": "1.0", "receiptKind":after['receiptKind'], "measurements": measurements, "measurementsComplete": complete,
        "candidateEfficiencyGatePassed": meets_efficiency_gate,
        "observedImprovement": meets_efficiency_gate and bool(decreased) and not increased,
        "increasesRequiringReview": increased,
        "claimScope": "One matched case study; no general speed claim or upgrade acceptance implied.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--cases", type=Path, default=Path(__file__).resolve().parents[1] / "scenarios/repository-sync/v1/cases.json")
    args = parser.parse_args()
    print(json.dumps(compare(args.baseline, args.candidate, json.loads(args.cases.read_text(encoding="utf-8"))), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
