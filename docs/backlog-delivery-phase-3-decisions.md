# Phase 3: reconciliation and governed revision

Status: Phase 3 complete. Both interview rounds were accepted by the user; implementation,
independent acceptance and the approved human portal reconciliation journey passed.
See [Phase 3 evidence](delivery/phase-3-evidence.md) for verification and retained limitations.
Phase 2 is complete at `a4590fd` on `codex/backlog-delivery`. Continue on that same branch and
commit/push the completed phase; no merge to main or publication is authorized here.

## Accepted decisions: round 1

1. Automatically record observations and provably mechanical provider formatting differences.
   Description, acceptance, comment, hierarchy and ownership changes receive an explicit
   classification in the reconciliation report. An agent can propose cosmetic/no-impact
   classification, but cannot silently accept changed business meaning. Batch related findings
   into one coherent human review.
2. When an Epic change has uncertain impact, provisionally mark its descendants as requiring
   impact review. Unrelated Epics remain eligible. Narrow the restriction when evidence identifies
   affected Requirements; extend across Epics/repositories only for justified shared dependencies
   or contracts. Uncertainty is visible, not inferred readiness.
3. An approved business revision can be recorded before the required technical revision finishes.
   Affected work explicitly needs intake/architecture/planning revision. Restore the relevant
   readiness only against actual reviewed Git artifacts. Platform edits never implicitly amend
   technical authority.
4. Once the implementation is ready, agree the exact test change and have the user edit/comment
   on Epic 82 in the portal. Verify observation, impact review, approved revision and preserved human
   text. Separate synthetic items cover destructive, conflicting and interrupted-write cases.
   The agreed testing approach does not yet authorize an invented edit to the human Epic.

## Verified technical constraints for subsequent rounds

- Azure work-item update IDs and revision numbers are distinct: Microsoft's example includes
  multiple relation updates at the same revision. Ingest update history separately from current
  field/relation snapshots; a revision-only cursor misses changes, including edit-then-revert.
  [Updates](https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/updates/list?view=azure-devops-rest-7.1),
  [Revisions](https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/revisions/list?view=azure-devops-rest-7.1).
- Comments have their own IDs, versions, deletion markers and body continuation token. They need
  endpoint-specific pagination, including deleted entries and available version history, rather
  than the adapter's ordinary value/header-token list reader.
  [Comments](https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/comments/get-comments?view=azure-devops-rest-7.1),
  [Versions](https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/comments-versions/list?view=azure-devops-rest-7.1).
- A missing normal item is not proof of deletion. Positive recycle-bin evidence can establish
  deletion; absent/inaccessible evidence remains unknown, especially after permanent destruction.
  [Recycle bin](https://learn.microsoft.com/en-us/rest/api/azure/devops/wit/recyclebin/get?view=azure-devops-rest-7.1).
- Current product observation is limited to latest Epic summaries. Reconciliation must revisit
  adopted lower-level work and known IDs even when they leave discovery scope. Keep observed,
  reviewed/acknowledged and approved business/technical bases distinct. A shared login identity
  does not prove agent authorship; use correlation with actual approved operations.
- Phase 2 already stops ambiguous dispatches, stale proposals and unverified profile/disconnect
  changes. Phase 3 must add reviewed recovery and authority transitions while preserving those
  guards and their historical evidence.

## Accepted decisions: round 2

5. Technical owners acknowledge cosmetic changes and assess technical impact with an explanation;
   business owners approve changed outcomes/scope/acceptance; coordinators approve authority and
   configuration changes. Mixed findings require the corresponding roles. One verified individual
   may exercise several configured roles in one review.
6. Track coverage separately for item content, comments, history and access. Missing evidence
   blocks dependent decisions, retaining the previous observation as visibly stale. Confirm
   deletion only with positive provider evidence. No automatic recreation or inferred completion.
7. Recover an interrupted write followed by human edits through a review of the original operation,
   positively identified native item and intervening changes. Preserve the native identity and
   human edits under a revised planning basis, with original operation evidence retained. No create
   replay while outcome is unknown; an empty search is not a definitive failure.
8. Shared profile migration previews every affected repository and consequence, keeps the current
   profile active during preparation, then applies a reviewed transition with explicit repository
   handoffs and retained history. Interrupted cutover blocks affected operations until resumed.
   No implicit authority upgrade.
9. Repository disconnection requires current reconciliation, resolved uncertain operations and
   explicit transfer/resolution of remaining ownership and obligations. Provider evidence and
   local history precede disabled delivery and return to standard repository governance. Outage,
   expired login or missing files never perform the handoff.

Dates remain a Phase 4 interview topic: distinguish planned start, actual start, target finish and
committed deadline. Tags, execution claims, dependency gates and parallel-work recommendations
remain Phase 4; reconciliation must preserve relevant human changes without claiming those
execution capabilities already exist.
