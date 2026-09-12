"""Generate the reviewable Phase 0 JSON Schema, with no external dependencies."""
import json
from pathlib import Path

TEXT = {"type": "string", "minLength": 1}
REV = {"type": "string", "pattern": "^(?:[0-9a-f]{40}|[0-9a-f]{64})$"}
TIME = {"type": "string", "format": "date-time"}


def enum(*values):
    return {"enum": list(values)}


def array(value):
    return {"type": "array", "items": value, "uniqueItems": True}


def obj(properties, optional=()):
    return {"type": "object", "properties": properties,
            "required": [key for key in properties if key not in optional],
            "additionalProperties": False}


def mapping(value):
    return {"type": "object", "additionalProperties": value}


def record(kind, properties, optional=()):
    return obj({"schemaVersion": {"const": 1}, "recordType": {"const": kind}, **properties}, optional)


def build():
    artifact = obj({"repository": TEXT, "commit": REV, "path": TEXT, "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}})
    actor = obj({"providerId": TEXT, "accountableHumanId": TEXT, "executionId": TEXT})
    reference = obj({"provider": enum("azure", "github"), "id": TEXT, "url": {"type": "string", "format": "uri"}})
    basis = obj({"businessRevision": TEXT, "profileRevision": REV, "plan": artifact})
    field = obj({"providerField": TEXT, "authority": enum("platform", "git", "operational"),
                 "requiredAt": enum("intake", "ready", "optional"), "writePolicy": enum("conditional", "proposal", "owned")})
    path = {"type": "string", "minLength": 1, "pattern": "^(?!/)(?!.*:)(?!.*\\\\)(?!.*(?:^|/)\\.\\.(?:/|$)).+$"}
    defs = {
        "disabled": record("profile", {"enabled": {"const": False}}),
        "profile": record("profile", {
            "enabled": {"const": True}, "space": TEXT, "provider": enum("azure", "github"),
            "edition": enum("azure-devops-services", "github.com"), "profileRevision": REV,
            "coordinator": obj({"repositoryId": TEXT, "branch": TEXT, "statePath": path}),
            "workTypes": obj({key: TEXT for key in ("epic", "feature", "requirement", "task")}),
            "fields": mapping(field), "roles": obj({key: array(TEXT) for key in ("business", "technical", "acceptance", "coordinator")}),
            "capabilities": mapping(enum("verified", "unsupported", "unverified")),
            "tagNamespace": TEXT,
        }),
        "binding": record("binding", {"space": TEXT, "repositoryId": TEXT,
            "profileRepositoryId": TEXT, "profileRevision": REV, "profilePath": path,
            "teamId": TEXT, "technicalArtifacts": array(artifact)}),
        "work": record("work", {"space": TEXT, "logicalId": TEXT, "native": reference,
            "kind": enum("epic", "feature", "requirement", "task"), "title": TEXT,
            "outcome": TEXT, "businessOwnerId": TEXT, "parentId": TEXT,
            "acceptance": array(obj({"id": TEXT, "criterion": TEXT})),
            "repositories": array(TEXT), "technicalArtifacts": array(artifact),
            "priority": {"type": "integer", "minimum": 0}, "milestoneId": TEXT,
            "deliveryState": enum("draft", "ready", "active", "implemented", "verified", "accepted", "superseded"),
        }, ("parentId", "priority", "milestoneId")),
        "observation": record("observation", {"space": TEXT, "workId": TEXT, "observedAt": TIME,
            "providerRevision": TEXT, "businessFingerprint": TEXT,
            "availability": enum("present", "deleted", "inaccessible", "unknown"),
            "coverage": obj({key: enum("complete", "incomplete", "unknown") for key in ("fields", "comments", "relations", "history")}),
            "acceptedBasis": basis, "readiness": enum("ready", "blocked", "stale", "unknown"),
        }, ("acceptedBasis",)),
        "proposal": record("proposal", {"space": TEXT, "id": TEXT, "inputFingerprint": TEXT,
            "payloadFingerprint": TEXT, "basis": basis, "operations": array(TEXT),
            "decision": enum("proposed", "approved", "rejected", "superseded"),
            "approval": obj({"actor": actor, "role": enum("business", "technical", "acceptance"),
                             "payloadFingerprint": TEXT, "inputFingerprint": TEXT, "decidedAt": TIME}),
        }, ("approval",)),
        "operation": record("operation", {"space": TEXT, "id": TEXT, "proposalId": TEXT,
            "destination": TEXT, "payloadFingerprint": TEXT, "inputFingerprint": TEXT,
            "action": enum("create", "update", "link", "comment"),
            "state": enum("prepared", "dispatched", "outcome_unknown", "applied", "not_applied", "conflict"),
            "actor": actor, "providerId": TEXT, "expectedProviderRevision": TEXT,
        }, ("providerId", "expectedProviderRevision")),
        "claim": record("claim", {"space": TEXT, "workId": TEXT,
            "generation": {"type": "integer", "minimum": 1}, "actor": actor,
            "state": enum("active", "released"), "basis": basis,
            "lastCheckpointAt": TIME, "exclusiveResources": array(TEXT)}),
        "dependency": record("dependency", {"space": TEXT, "id": TEXT, "predecessor": TEXT,
            "successor": TEXT, "blockedActivity": enum("implementation", "integration", "delivery", "acceptance"),
            "condition": TEXT, "requiredEvidenceIds": array(TEXT), "receivingOwnerId": TEXT,
            "externalReference": reference}, ("externalReference",)),
        "evidence": record("evidence", {"space": TEXT, "id": TEXT, "workId": TEXT,
            "artifact": artifact, "sourceCommit": REV, "contractRevision": TEXT,
            "acceptanceIds": array(TEXT), "result": enum("passed", "failed", "unknown"),
            "producer": actor, "observedAt": TIME}),
        "footprint": record("footprint", {"space": TEXT, "workId": TEXT, "repositoryId": TEXT,
            "baseCommit": REV, "headCommit": REV, "plan": artifact,
            "basis": enum("planned", "observed"), "coverage": enum("complete", "incomplete", "unknown"),
            "observedAt": TIME, "writePaths": array(path), "categories": array(TEXT),
            "resources": array(obj({"id": TEXT, "mode": enum("read", "change", "exclusive"), "contractRevision": TEXT})),
            "generatedSources": mapping(path), "protectedAssumptions": array(TEXT),
        }),
    }
    return {"$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://orbyss.io/program-kit/delivery/phase0/v1",
            "title": "Program Kit delivery Phase 0 contract (experimental)",
            "oneOf": [{"$ref": "#/$defs/" + name} for name in defs], "$defs": defs}


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[2] / "docs/delivery/contracts.schema.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
