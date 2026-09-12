"""Pure reference semantics for the Phase 0 conformance tests.

These functions propose new state. Only a successful provider conditional commit
authorizes it. They do not create a local team-delivery backend.
"""
from copy import deepcopy
import hashlib
import json
from fnmatch import fnmatchcase


class Conflict(ValueError):
    pass


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def validate_semantics(record):
    kind = record["recordType"]
    if kind == "profile" and record["enabled"]:
        editions = {"azure": "azure-devops-services", "github": "github.com"}
        if editions[record["provider"]] != record["edition"]:
            raise Conflict("Provider and edition differ")
        if any(not members for members in record["roles"].values()):
            raise Conflict("Every role needs an accountable identity")
    if kind == "proposal" and record["decision"] == "approved":
        approval = record.get("approval", {})
        if any(approval.get(key) != record[key] for key in ("payloadFingerprint", "inputFingerprint")):
            raise Conflict("Approval does not cover current proposal and inputs")
    if kind == "observation" and record["readiness"] == "ready":
        if record["availability"] != "present" or set(record["coverage"].values()) != {"complete"} or not record.get("acceptedBasis"):
            raise Conflict("Incomplete observation cannot establish readiness")
        if record["acceptedBasis"]["businessRevision"] != record["businessFingerprint"]:
            raise Conflict("Changed business basis requires reconciliation")
    if kind == "operation" and record["state"] == "applied" and not record.get("providerId"):
        raise Conflict("Applied operation requires verified provider identity")


def admit(state, work_id, actor, basis, exclusive=(), takeover=False, authorized=False):
    new = deepcopy(state)
    previous = new["claims"].get(work_id)
    if previous and previous["state"] == "active" and not (takeover and authorized):
        raise Conflict("Work already claimed; stale time does not authorize takeover")
    if takeover and not authorized:
        raise Conflict("Takeover requires owner or coordinator authority")
    for key, other in new["claims"].items():
        if key != work_id and other["state"] == "active" and set(exclusive) & set(other["exclusiveResources"]):
            raise Conflict("Exclusive resource already claimed")
    new["claims"][work_id] = {"state": "active", "generation": (previous or {}).get("generation", 0) + 1,
        "actor": actor, "basis": basis, "exclusiveResources": list(exclusive)}
    return new


def checkpoint(state, work_id, generation, execution_id, basis):
    claim = state["claims"].get(work_id, {})
    if claim.get("state") != "active" or claim.get("generation") != generation or claim.get("actor", {}).get("executionId") != execution_id:
        raise Conflict("Execution no longer holds this claim")
    if claim["basis"] != basis:
        raise Conflict("Accepted execution basis changed")


def release(state, work_id, generation, execution_id, basis):
    checkpoint(state, work_id, generation, execution_id, basis)
    new = deepcopy(state)
    new["claims"][work_id]["state"] = "released"
    return new


def dispatch(operation):
    if operation["state"] != "prepared":
        raise Conflict("Only an undispatched operation may be sent")
    return dict(operation, state="dispatched")


def recover(operation, matches, coverage_complete):
    if operation["state"] not in ("dispatched", "outcome_unknown"):
        raise Conflict("Operation is not awaiting recovery")
    verified = [item for item in matches if all(item.get(key) == operation[key]
                for key in ("id", "destination", "payloadFingerprint"))]
    if coverage_complete and len(verified) == 1 and len(matches) == 1:
        return dict(operation, state="applied", providerId=verified[0]["providerId"])
    if len(matches) > 1 or (matches and not verified):
        return dict(operation, state="conflict")
    return dict(operation, state="outcome_unknown")


def compatibility(left, right):
    if any(p["coverage"] != "complete" for p in (left, right)):
        return {"verdict": "unknown", "reasons": ["Incomplete change scope"]}
    if any(not (p["writePaths"] or p["resources"] or p["generatedSources"]) for p in (left, right)):
        return {"verdict": "unknown", "reasons": ["No declared change scope"]}
    resources = {r["id"]: r for r in left["resources"]}
    for r in right["resources"]:
        other = resources.get(r["id"])
        if other and ("exclusive" in (r["mode"], other["mode"]) or
                      ("change" in (r["mode"], other["mode"]) and r["contractRevision"] != other["contractRevision"])):
            return {"verdict": "coordinate", "reasons": ["Incompatible shared resource: " + r["id"]]}
    if left["repositoryId"] == right["repositoryId"]:
        if left["baseCommit"] != right["baseCommit"]:
            return {"verdict": "unknown", "reasons": ["Different base revisions require reassessment"]}
        paths_a = left["writePaths"] + list(left["generatedSources"].values())
        paths_b = right["writePaths"] + list(right["generatedSources"].values())
        for a in paths_a:
            for b in paths_b:
                if fnmatchcase(a, b) or fnmatchcase(b, a):
                    return {"verdict": "advisory", "reasons": [f"Possible overlapping writes: {a}, {b}"]}
                if any(c in a + b for c in "*?["):
                    return {"verdict": "unknown", "reasons": ["Unresolved glob intersection"]}
    return {"verdict": "no_known_conflict", "reasons": []}


def evidence_satisfies(dependency, evidence, source_commit, contract_revision):
    by_id = {item["id"]: item for item in evidence}
    required = dependency["requiredEvidenceIds"]
    return bool(required) and all(key in by_id and by_id[key]["result"] == "passed"
        and by_id[key]["sourceCommit"] == source_commit and by_id[key]["contractRevision"] == contract_revision
        for key in required)


def check_binding(profile, binding):
    if not profile["enabled"] or any(profile[key] != binding[key] for key in ("space", "profileRevision")):
        raise Conflict("Repository binding requires explicit compatible profile activation")


def observation_status(http_status, complete, deletion_confirmed=False):
    if http_status in (401, 403):
        return "inaccessible"
    if http_status in (404, 410):
        return "deleted" if deletion_confirmed else "unknown"
    if http_status != 200 or not complete:
        return "unknown"
    return "present"
