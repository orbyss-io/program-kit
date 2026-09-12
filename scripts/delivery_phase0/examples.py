"""Representative, synthetic examples for every Phase 0 record variant."""
from copy import deepcopy
import json
from pathlib import Path


def build():
    revision = "a" * 40
    timestamp = "2026-09-12T12:00:00Z"
    artifact = {"repository": "checkout-api", "commit": revision, "path": "docs/payment-contract.md", "sha256": "b" * 64}
    actor = {"providerId": "developer-17", "accountableHumanId": "owner-7", "executionId": "session-23"}
    basis = {"businessRevision": "business-v3", "profileRevision": revision, "plan": artifact}

    def record(record_type, **properties):
        return {"schemaVersion": 1, "recordType": record_type, **properties}

    profile = record("profile", enabled=True, space="checkout-delivery", provider="azure", edition="azure-devops-services",
        profileRevision=revision, coordinator={"repositoryId": "delivery-ops", "branch": "coordination", "statePath": "state.json"},
        workTypes={"epic": "Epic", "feature": "Feature", "requirement": "User Story", "task": "Task"},
        fields={"acceptance": {"providerField": "Microsoft.VSTS.Common.AcceptanceCriteria", "authority": "platform", "requiredAt": "ready", "writePolicy": "conditional"},
                "technicalPlan": {"providerField": "artifact-link", "authority": "git", "requiredAt": "ready", "writePolicy": "owned"}},
        roles={"business": ["owner-7"], "technical": ["developer-17"], "acceptance": ["owner-7"], "coordinator": ["owner-7"]},
        capabilities={"conditionalClaimCommit": "unverified", "conditionalDescription": "unverified"}, tagNamespace="pk")
    work = record("work", space="checkout-delivery", logicalId="REQ-17",
        native={"provider": "azure", "id": "17", "url": "https://dev.azure.com/example/project/_workitems/edit/17"},
        kind="requirement", title="Return a stable payment result", outcome="Checkout can safely retry a payment request",
        businessOwnerId="owner-7", parentId="FEAT-2", acceptance=[{"id": "AC-1", "criterion": "Repeated payment keys return the same outcome"}],
        repositories=["checkout-api", "checkout-web"], technicalArtifacts=[artifact], priority=1, milestoneId="M-1", deliveryState="draft")
    proposal = record("proposal", space="checkout-delivery", id="proposal-4", inputFingerprint="business-v3", payloadFingerprint="change-v4",
        basis=basis, operations=["operation-4"], decision="approved", approval={"actor": actor, "role": "business",
        "payloadFingerprint": "change-v4", "inputFingerprint": "business-v3", "decidedAt": timestamp})
    footprint = record("footprint", space="checkout-delivery", workId="REQ-17", repositoryId="checkout-api",
        baseCommit=revision, headCommit=revision, plan=artifact, basis="planned", coverage="complete", observedAt=timestamp,
        writePaths=["src/payments/handler.py"], categories=["area:checkout", "contract:payment-api"],
        resources=[{"id": "payment-api", "mode": "change", "contractRevision": "v2"}],
        generatedSources={"client/payment.ts": "contracts/payment.json"}, protectedAssumptions=["Payment idempotency keys remain stable"])
    records = [record("profile", enabled=False), profile,
        record("binding", space="checkout-delivery", repositoryId="checkout-api", profileRepositoryId="delivery-config",
               profileRevision=revision, profilePath="delivery/profile.json", teamId="checkout-team", technicalArtifacts=[artifact]), work,
        record("observation", space="checkout-delivery", workId="REQ-17", observedAt=timestamp, providerRevision="23", businessFingerprint="business-v3",
               availability="present", coverage={key: "complete" for key in ("fields", "comments", "relations", "history")}, acceptedBasis=basis, readiness="ready"),
        proposal,
        record("operation", space="checkout-delivery", id="operation-4", proposalId="proposal-4", destination="azure:project",
               payloadFingerprint="change-v4", inputFingerprint="business-v3", action="create", state="outcome_unknown", actor=actor),
        record("claim", space="checkout-delivery", workId="REQ-17", generation=2, actor=actor, state="active", basis=basis,
               lastCheckpointAt=timestamp, exclusiveResources=["payment-schema-migration"]),
        record("dependency", space="checkout-delivery", id="DEP-1", predecessor="UPSTREAM-1", successor="REQ-17", blockedActivity="delivery",
               condition="Receiving integration verifies payment API v2", requiredEvidenceIds=["EVID-1"], receivingOwnerId="developer-17",
               externalReference={"provider": "github", "id": "external-repo#42", "url": "https://github.com/example/upstream/issues/42"}),
        record("evidence", space="checkout-delivery", id="EVID-1", workId="REQ-17", artifact=artifact, sourceCommit=revision,
               contractRevision="v2", acceptanceIds=["AC-1"], result="passed", producer=actor, observedAt=timestamp), footprint]
    github = deepcopy(profile)
    github.update(provider="github", edition="github.com")
    github["workTypes"] = {"epic": "label:pk-kind:epic", "feature": "type:Feature", "requirement": "label:pk-kind:requirement", "task": "type:Task"}
    github["fields"]["acceptance"].update(providerField="issue-body", writePolicy="proposal")
    github["capabilities"]["conditionalDescription"] = "unsupported"
    records.append(github)
    return records


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[2] / "docs/delivery/examples.json"
    target.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
