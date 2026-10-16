# Repair feedback feature: separate implementation handoff

The user approved the [feature specification](repair-feedback-feature-specification-2026-10-16.md)
on 16 October 2026, including the final shared-understanding check. The approved
feature has two skills, one diagnostic contract, local development-session
delivery, and public issue/evidence delivery through a separate evidence repository.

This is a new development feature. Keep it identifiable separately from the
original maintenance repair findings and later defect addenda. This handoff does
not change their counts, rewrite their approvals, or claim this feature is built.

## Coordination and ownership

The user explicitly requires a separate implementation agent and separate branch.
Use an isolated worktree from main and create a dedicated `codex/` feature branch
(suggested name: `codex/repair-feedback`). Record the actual base commit and branch.
Do not copy the maintenance checkout's uncommitted work or change its branch.

The feature implementation session owns its execution ledger and work sequencing.
Create one feature ledger linking RF-01 through RF-13 to implementation, tests,
dependencies, and closure evidence. Do not add this feature to the maintenance
defect ledger or rewrite its plan, audit, approvals, consumer work, or repair evidence.
The reporter still must not introduce a competing execution ledger within any
session to which it submits requests.

The earlier handoff assigning this feature to **Implement maintenance repair plan**
was retracted after the user's correction. That session continues its existing
repairs independently. Treat needed changes on its branch as explicit integration
dependencies; do not assume they are already present on main or copy its working
tree. Carry these approved design documents into the feature branch.

The approved requirements are RF-01 through RF-13 in the specification. Literal
command/field names described as suggestions are implementation choices; publish
the actual questions, vocabulary, enums, schema, budgets, and compatibility rules
as maintained executable contracts before relying on them.

No source, workflow, existing ledger, or active consumer was edited by this design
handoff. Repository/branch setup, installed functionality, and qualification remain
implementation work and must be reported by their actual outcomes.

## Suggested work packages

| Package | Outcome | Requirements |
| --- | --- | --- |
| A | Versioned diagnostic question set, vocabulary, request/revision schema, evidence/assessment relationships and compatibility fixtures | RF-02, RF-03, RF-04, RF-10 |
| B | Consumer reporter command/skill, bounded export, personal preferences, submission index and local queue adapter | RF-01, RF-05, RF-06, RF-09 |
| C | Explicit GitHub setup, issue search/correlation, create/comment and recoverable delivery | RF-07, RF-08, RF-12 |
| D | Separate evidence repository source/provisioning, consumer fork/PR flow, trusted guardian and maintainer acceptance | RF-08, RF-09 |
| E | Repository-only evaluator and implementation-ledger intake/disposition integration | RF-01, RF-04, RF-06, RF-10, RF-13 |
| F | On-demand project/account history, additional evidence, freshly sourced cloud/local status | RF-04, RF-05, RF-11, RF-12 |
| G | Native installed/upgrade qualification, operating guidance, release/migration records and feature closure | RF-01, RF-03, RF-05, RF-12, RF-13 |

Start by inspecting the existing packet checker and export/native ownership
machinery. Reuse proven pieces without presenting the packet inspector as the new
diagnostic contract or promising binary/sanitization capabilities it lacks.

Prepare reviewable evidence-repository configuration and a trusted guardian before
claiming the public route works. The intended repository is
`orbyss-io/program-kit-evidence`; verify actual availability, permissions, ownership,
and rules. Keep ordinary public consumers on fork PRs without upstream Write.
Remote setup that cannot be completed must remain an explicit dependency, not a
green mock or an implied deployed service.

## Required observable acceptance

Use meaningful deterministic fixtures and recording CLI/API fakes for behavior
that would otherwise publish live test content. Do not make test issues, comments,
forks, or uploads a hidden part of a deterministic validator. Any actual remote
provisioning/delivery must have its own honest operational record.

| Scenario | Required behavior |
| --- | --- |
| Consumer diagnostics | Standard questions produce comparable output; unknown/retrospective explanations and reported versus executed results remain explicit. |
| Historical language | Preserve old request/profile identity; normalization is linked and explicit, with no invented newer answers. |
| New concept | Original wording and unclassified observation survive; existing enums are not guessed from prose. |
| Multiple consumers | Several requests/revisions map to one repair or explained related group without losing provenance or double-counting repairs. |
| First use and upgrades | Inform user when ignored personal files are created; prove ignore behavior, preserve choices, and keep preferences outside governance inputs/public evidence. |
| Local delivery | Queue survives an unavailable agent; owner retains ledger control; recording fake proves zero public mutation/fork/upload calls. |
| Local correlation unavailable | Retain request and mark search pending, with no silent public fallback or claimed successful search. |
| Public duplicate search | Search open/closed issues, refine overly broad/empty results, inspect bounded candidates and relevant comments, expose incomplete search. |
| Public destination | On public delivery, supported duplicate appends evidence; related issues retain links; uncertain match requires destination choice; reviewed payload is the one published. Local delivery records relationships without posting. |
| Useful public derivative | Minimal report/repro preserves relevant reasoning, scope and omissions; unsupported artifacts and bounds fail actionably without leaking contents. |
| Evidence submission | Correct explicit repo/fork/base, only reviewed files, linked issue and PR, stable request/revision references, no upstream consumer Write dependency. |
| Guardian boundaries | Reject path/link/case aliases, extra files, mismatched inventory/hashes, invalid contract/type/size and attempted validator/policy or prior-evidence modification. |
| Trusted guardian | A submission cannot replace its validator or counterfeit the required result by renaming a job; proof binds actual head and validator version. |
| Submitted code | Read and classify as data; never execute supplied scripts, project setup or coding-agent sessions in the guardian. |
| Partial remote mutation | Interrupted create/comment/push/PR is reconciled against actual objects/markers before retry; no duplicate side effects or false completion. |
| Prerequisites | Both Bash/PowerShell helpers distinguish missing CLI, PATH issue and unavailable/invalid authentication without exposing credentials or silently installing/logging in. |
| Account history | Authored, commented-on and broader involved issues can be found; project default and explicit account-wide discovery remain distinguishable. |
| Fresh cloud status | Change fake remote state between consecutive checks while keeping local files unchanged; second check reflects new direct reads, never persisted state or cached search. |
| Failed status retrieval | Failure after a previous success returns unavailable/partial, never the prior state as current; report retrieval times and supported source links. |
| Local status | Fresh ledger reads reflect changes immediately; cloud links are fetched separately; no public delivery merely to query status. |
| Lifecycle meanings | Closed issue, merged evidence, confirmed defect, implemented repair, validation and actual release cannot substitute for one another. |
| Release traceability | Concise what/why/context links flow through maintained versioned release/migration guidance; affected procedures and consumer actions are updated where applicable. |
| Distribution | Native command/skill generation, installed source integrity, upgrade/personal-file preservation and internal-skill packaging exclusion all hold. |

The implementation owner should add relevant validators to the maintained inventory,
run targeted checks and bounded Development, and use exact-candidate CI under the
existing policy for release qualification. This feature adds no mandatory local
Release repetition and no paid live-acceptance phase.

## Closure record

Record changed files, actual tests and their limits, external setup/rules evidence,
remaining dependencies, installed-route qualification, and release/migration links.
Distinguish implemented source from deployed public infrastructure and public
consumer availability. No feature-wide completion claim while a required delivery
route or trusted acceptance boundary remains only planned.

Update the feature session's shared ledger with disposition and closure references.
Do not retroactively mark the historical consumer repairs accepted, rerun their
work, or treat this approved feature as authority to publish a Program Kit release.
