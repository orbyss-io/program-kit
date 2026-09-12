# Azure reconciliation and governed revision

Use `speckit.program-kit-delivery.reconcile` after Azure setup and whenever provider changes affect
planning. Installation remains disabled by default. Existing enabled Phase 2 consumers need an
explicit initial history review before this adapter admits further refinement. No upgrade infers
that previously unseen comments or intervening edits were accepted.

All commands use `python .specify/extensions/program-kit-delivery/scripts/azure_reconciliation.py
--profile <pinned-profile>`. Keep generated reports/proposals in new files. They contain business
content and native history; store them only in locations appropriate for that delivery space.
The shared coordinator retains observations, reviews, role approvals, recovery and transition
records. Platform content remains authoritative; local reports are review artifacts.

## Observe and classify

Run `sync --output <report.json>`. Optionally supply `--keys <logical-key> ...` to observe a bounded
branch, its ancestors and descendants. An unrestricted sync covers discovered Epics, adopted
lower-level items and previously known identities, including those outside the current scope.

The observation reads item content, all available update IDs and comments, including edited/deleted
comment versions. Updates use offset pagination; comments use body continuation tokens. Reads are
bounded and checked at both ends for concurrent changes. A gap, repeated page/token, version gap,
read race or unavailable endpoint yields incomplete/unknown evidence. Prior accepted observations
remain preserved and visibly stale. Positive recycle-bin evidence can confirm deletion. Absence
from a query or a failed lookup cannot establish deletion, successful delivery or permission to
create a replacement. Initial/full scans prioritize complete evidence; use bounded scopes for large
backlogs. No background monitor or webhook service is installed.

`azure-reconciliation.schema.json` defines reports and decisions. For each finding being reviewed,
provide this shape in a JSON array:

```json
[{"nativeId":82,"classification":"business","reason":"Reviewed scope change; these requirements need revision.",
  "affectedKeys":["PORTAL-82","PORTAL-82-R1"],"technicalRevisionRequired":true}]
```

Classes are `baseline`, `cosmetic`, `feedback`, `business`, `technical`, `ownership` and `retired`.
The example is illustrative, not a standing approval for Epic 82. An uncertain Epic change initially
affects its descendants. The reviewer can narrow that set with an explanation or include known
shared-dependency work; the changed work itself cannot be omitted. Unknown/unavailable evidence
cannot be classified away as readiness. Retirement preserves identity/evidence and blocks future
admission; it does not delete or close native work automatically.

Run `review-plan --report-id <id> --decisions <decisions.json> --output <review.json>`. Present the
exact review and digest to the responsible people. Record each required decision using
`review-approve --input <review> --approved-sha256 <digest> --decision-source <actual-decision>
--role <role>`, then `review-apply --review-id <id>`. Technical approval is required for every
classification. Baseline/business/ownership/retirement also require business approval. Individuals
with different roles can approve in separate sessions; one person holding both roles can approve
the same payload for each role. New changes invalidate pending approvals rather than being rebased
silently. Repeating a completed review does not rewrite its decision.

A sync never changes the accepted planning basis. Reviewed application records the current human
content and the impact decision without rewriting native fields/comments. Business and technical
changes leave explicit technical revision obligations. Related pending obligations accumulate;
a later cosmetic acknowledgement cannot erase them. Use the Azure planning command for separately
reviewed native item updates or new children. Proposals capture full history in addition to current
fields/relations, so edit-then-revert and comment-only changes invalidate stale proposed writes.

## Technical revision and artifacts

Business approval may precede technical revision. Normal intake/architecture/planning sessions
remain mandatory; no reconciliation command launches an agent, produces an accepted ADR by itself,
or implements the customer request. Provider refinement admission reports pending technical
revisions explicitly so the authorized revision session can proceed. Implementation, verified
delivery and acceptance gates remain later-phase capabilities.

After the technical review, prepare an artifact array containing `repositoryId`, immutable `commit`,
repository-relative `path` and exact-byte `sha256`. Supply a separate JSON object mapping repository
IDs to local checkout locations via `--repositories`. Locations are lookup inputs, never authority
overrides: bindings must identify the registered repository. Run `technical-plan --keys <keys>
--artifacts <artifacts.json> --repositories <locations.json> --output <proposal>`, review it, then
`technical-complete --input <proposal> --approved-sha256 <hash> --decision-source <decision>
--repositories <locations.json>`.

The verifier checks actual Git objects, ancestry, current HEAD content and working-file bytes.
Missing/fabricated artifacts cannot clear a revision obligation. A later artifact change invalidates
the accepted technical basis and needs another reviewed technical proposal. Historical evidence is
retained, while the latest accepted revision supplies the current basis. The initial adapter needs
the relevant repositories available locally for technical verification; ordinary refinement checks
can verify artifacts in the current consumer and fail explicitly for unavailable other repositories.
Remote artifact resolution and execution evidence remain later-phase work.

## Reviewed recovery

Phase 2 automatic recovery still handles an unchanged, positively identified write. If human edits
make that insufficient, run `recovery-plan --operation-id <id> --native-id <id> --reason <explanation>
--output <proposal>`. Initial native history must establish creation correlation, or the original
operation must identify that existing item. Current type, scope, hierarchy and complete history are
verified. The review contains original intent and the current human content. Record both business
and technical decisions with `recovery-approve`, then use `recovery-apply` with the same input/hash
and decision source. Human edits are retained and the exact native identity is adopted once.

The original proposal becomes superseded for remaining work, which needs a new reviewed planning
proposal. Original operation evidence is never rewritten to imply a different dispatched payload.
No-match and unknown outcomes remain blocked; these commands provide no unsafe redispatch switch.

## Profile migration and disconnection

Migration is a reviewed cutover across all active consumers of one shared profile. First commit the
candidate policy to an immutable Azure Git location; give its repository/commit/path/byte hash in a
source descriptor. Prepare `migration-plan --new-profile <profile> --profile-source <source.json>
--repositories <all-active-consumer-locations.json> --output <proposal>`. Existing policy remains
active during preparation. New mappings, scope, roles and permissions are verified, and each local
binding/history and roadmap handoff is captured. Every active consumer must be enumerated. This
initial operation keeps provider organization, project and coordinator fixed; relocating a delivery
space needs a separate handoff. Adopted work cannot silently disappear under narrower/new mappings.

For one consumer to leave, prepare `disconnect-plan --repository-id <id> --repositories <locations>
--obligations <obligations.json> --output <proposal>`. Account for every bound Requirement with
`key`, `disposition` (`transferred`, `resolved` or `retired`), `recipientRepositoryId` (null except for
transfer), and a reason. A transfer requires another registered consumer already bound to the same
Requirement. Uncertain operations must be resolved; active implementation must finish or be paused.
Future execution claims require their supported release/handoff contract. No native status is
silently closed as a consequence of disconnect.

Both transitions require `transition-approve` for business, technical and coordinator roles, using
the exact input/hash, actual decision source and repository locations. Then run `transition-apply
--transition-id <id> --repositories <locations>`. Provider registration precedes local persistence;
old snapshots and hash-chained history remain intact. Resume the same transition ID with the old
reviewed profile after interruption. A partial profile cutover blocks affected consumers until all
handoffs finish. New profile meanings require a fresh reconciliation baseline, with old approvals
retained as historical evidence.

Disconnect permits standard local governance only after verifying its actual provider evidence and
completed handoff. The current verifier still requires read access to that evidence; loss of access
does not establish a new authority. A handwritten receipt, missing files, expired credentials or
an outage cannot disable connected governance. These are cooperating-consumer controls; Azure
administrators retain control of provider history and permissions.
