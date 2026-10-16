# Receiving consumer repair feedback

This is the repository maintainer's on-demand intake procedure. The consumer
reporter delivers observations; the evaluator proposes dispositions; the selected
implementation owner controls the existing execution ledger and its approvals.
No command here starts a coding agent, polls a chat, contacts consumers, executes
submitted reproductions or publishes progress.

## Select and register the receiving owner

Use a contributor checkout containing this feature and the repository-only
`program-kit-repair-evaluator` skill. Integrate the reviewed branch normally first.
The active maintenance campaign is not an implicit destination. Do not copy another
checkout's uncommitted work or add this feature to that campaign's approved scope.

The owner explicitly selects their existing JSON ledger. The `items-v1` adapter
requires an `items` array with unique string `id` values. Existing IDs such as
`U0` remain valid; retain all existing fields, history, approval and closure proof.

```text
python scripts/repair_evaluator.py --root <checkout> --owner <owner-id> register-owner --ledger docs/reviews/<existing-ledger>.json
```

This writes an immutable, local route under
`artifacts/repair-feedback/owners/<owner-id>.json`, without editing the ledger.
Owner IDs use lowercase letters, digits and hyphens. A changed destination gets
an explicitly selected new owner/route ID; old routes and deliveries remain intact.
The returned `routeSha256` binds the owner, ledger path and adapter, not mutable
implementation status. The reporter then configures that exact owner:

```text
python <installed-repair_feedback.py> --root <consumer> configure --mode contributor --checkout <checkout> --owner <owner-id>
python <installed-repair_feedback.py> --root <consumer> local --packet <sealed-packet> --ledger docs/reviews/<existing-ledger>.json
```

These choices remain ignored personal routing references. Existing preferences
without an owner need explicit reconfiguration. For an older local delivery, use
`bind-legacy --request-id <id> --revision <n> --sha256 <hash>` after the common
`--root` and `--owner` arguments. It verifies the original ledger, request and
complete packet, appends a hash-bound owner binding, and leaves original delivery
bytes intact. The consumer can then retry its same delivery and refresh references.

## Discover and inspect scoped intake

```text
python scripts/repair_evaluator.py --root <checkout> --owner <owner-id> inbox --limit 50
python scripts/repair_evaluator.py --root <checkout> --owner <owner-id> inbox --after <next-cursor> --limit 50
python scripts/repair_evaluator.py --root <checkout> --owner <owner-id> inspect --request-id <id> --revision <n> --sha256 <hash>
```

Follow `next` until null. `pending` means there is no matching owner decision; it
does not mean a defect is confirmed. Invalid/unrouted records remain visible with
no adoption claim. A bound exceeded error requires `inbox --request-id <id>` or
explicitly scoped archival of already reviewed records, never silent truncation.
The bound is 1,000 visited queue entries and 1,000 assessment/observation files;
page size is 1–100. There is no background pickup or notification requirement.

Inspection rechecks the route, delivery, original identity and the full current
contract inventory/hashes. Older contracts remain explicitly unqualified originals
with separate terminology mapping. Preserve them using:

```text
python scripts/repair_evaluator.py --root <checkout> --owner <owner-id> --preserve-original <historical-request.json>
```

A current-contract JSON without its declared report/evidence is not qualified by
using the historical preservation command.

## Import one explicitly selected public packet

```text
python scripts/repair_evaluator.py --root <checkout> --owner <owner-id> import-public --pr <evidence-pr-number> --head <exact-head-sha> --base <exact-current-base-sha> --validator <deployed-validator-sha> --issue <program-kit-issue-number>
```

This makes read-only GitHub calls and writes only the selected local intake. It
uses the trusted guardian's data inspection, downloads the full bounded packet,
checks the issue's exact request marker, verifies deployed App/rules/source identity
and rechecks the PR pins after download. Import earlier revisions first so the
supersession chain can be checked. Submitted scripts remain inert files.

An open or unaccepted PR can be triaged. `evidenceAccepted` in the import observation
is true only for a merged PR with a successful head-bound check from the deployed
App and matching validator provenance, whose merge is on main with the exact
packet bytes. A same-name result from another App cannot establish acceptance.
An accepted packet is still an observation, not an adopted repair. Later imports
append deduplicated acceptance observations without rewriting original delivery.
These include their first observation time; they are historical evidence, not a
fresh remote status service. The ordinary reporter fetches known public objects
directly when current public status is requested.

## Evaluate, then let the owner decide

Create an assessment against the shared `contract.json` object at
`assessmentSchemas["1.1"]` (version **1.1**) using the
exact `ownerRoute` returned by registration/inspection. Each request reference
retains its ID, revision, original SHA-256, contract and selected knowledge version.
Relationships may propose existing ledger IDs or new finding IDs; they do not
create those findings. Requests routed to different owners cannot be silently
grouped into one owner's assessment. Cross-owner work needs explicit routing and
separate owner dispositions.

```text
python scripts/repair_evaluator.py --root <checkout> --assessment <assessment.json>
```

Submission revalidates packet and routing before appending an immutable assessment.
Assessment version 1.0 remains readable through `assessmentSchemas["1.0"]` as
historical evidence; new submissions require 1.1. Standalone generated copies of
both schemas remain under `docs/contracts/repair-feedback/` in the contributor
repository. The 1.0 schema bytes remain unchanged. Both schemas ship inside the
shared contract, keeping the consumer bundle within Spec Kit's entry limit.
No original account is upgraded
or rewritten. An assessment's proposed disposition never changes implementation
status.

The implementation owner records the decision in a `repairFeedback` namespace
**inside the existing ledger**. This is an adapter over the existing authority,
not another status ledger. Preserve all other ledger fields. The extension is:

```json
{
  "adapterVersion": 1,
  "ownerRoute": "replace with the complete registered ownerRoute object",
  "decisions": []
}
```

Each decision contains `requestId`, `revision`, `requestSha256`, `assessmentId`,
`assessmentSha256`, `disposition`, `rationale`, `repairIds` and `facts`.
Use the assessment file's exact measured SHA-256. `disposition` is `adopt`,
`duplicate`, `defer`, `reject` or `needs-proof`. There is one current decision per
exact request revision; preserve decision history through the owner's existing
ledger/history practice. Adopt/duplicate decisions reference actual IDs in `items`.
Other dispositions may have no repair IDs. Several observations can reference the
same repair without double-counting it.

`facts` defaults to `{}`. Only record facts supported by attributable proof:

```json
{
  "implemented": {
    "value": true,
    "proof": ["<exact implementation commit and ledger source reference>"]
  }
}
```

Allowed fact names are the published lifecycle vocabulary. Facts require boolean
values and nonempty proof references. Adoption alone does not establish a defect,
implementation, validation, release or consumer confirmation. `confirmedRepair`
requires an adopt/duplicate decision with a real finding reference. The reporter
labels these as owner declarations; it does not promote them to independently
executed proof. Changed files, verification, dependencies and closure proof remain
in the owner's existing finding record. Keep public progress in authorized public
issue/PR/release records; never upload the local ledger to make status available.

## Read status and add correlation

Consumer `status --request-id <id>` matches exact revisions, routing, assessments
and decisions and returns only those records. It reads the ledger afresh and reports
retrieval and ledger modification times. Missing/changed/ambiguous inputs yield
unavailable sources and unknown lifecycle facts, never a cached previous success.
Linked GitHub objects are read separately; local-only status needs no GitHub CLI
or authentication. Released and confirmed-in-consumer outcomes remain unknown until
their own evidence is supplied.

Retrying the same `local` command with `--correlation <search.json>` appends a
content-addressed correlation observation. The original delivery, packet and
request revision stay unchanged; identical retries create no duplicate observation.

## Deployment and verification evidence

The public repository and dedicated App were provisioned on 16 October 2026.
See the [provisioning record](../reviews/repair-feedback-provisioning-result-2026-10-16.json)
and [three closed, unmerged operational scenarios](../reviews/repair-feedback-operational-test-results-2026-10-16.json).
This feature remains unreleased source. The infrastructure tests do not qualify
consumer repair behavior or a release candidate. Run the declared
`validate_repair_feedback` check and bounded Development for source changes;
exact-candidate CI owns release qualification.
