# Feature grilling evidence

Run `scripts/specification_intake.py` from the installed governance extension, with the consumer as
the working directory (or pass `--repository`). Evidence lives outside the not-yet-created feature
directory. New feature evidence lives at
`.program-kit/specification-intake/features/<feature-ID>/`; the roadmap epic is a separate relationship.
Legacy v1 evidence remains at `.program-kit/specification-intake/<roadmap-ID>/` unchanged.

`begin --entry EPIC-001 --feature invoice-export --request "<current request>"` reads the selected
canonical candidate's seed and relevant architecture, then creates a feature-owned `brief.json`
only if absent. On resume, read it, compare the new request, and update affected scope/decisions.
It never overwrites answers. Use stable canonical feature and roadmap IDs, not a generated branch name.
Several features can share one epic without sharing a brief or confirmation. Source thought, boundary
rationale and unresolved questions remain in the draft's seed context. Seed fields can prefill the
brief but do not confirm it; an incomplete seed is a legitimate starting point.

Edit the brief with these fields; strings describe the actual feature, not template placeholders:

```json
{
  "schemaVersion": 2,
  "featureId": "invoice-export",
  "roadmapEntry": "EPIC-001",
  "request": "Let account owners export their invoice history",
  "problem": "Owners cannot reconcile invoices outside the application",
  "users": "Authenticated account owners",
  "outcome": "An owner downloads invoice history for their own account",
  "scope": "Export the chosen date range as CSV",
  "nonGoals": "Other accounts, scheduled exports and payment changes",
  "journeys": "Choose dates, request export, download CSV",
  "failureCases": "Reject invalid dates and unauthorized access; show empty results explicitly",
  "dependencies": "Existing accepted invoice ownership and authorization contracts",
  "acceptanceCriteria": "An authorized owner gets exactly their invoices in the chosen range; another account's invoices never appear",
  "decisions": [
    {
      "id": "Q1",
      "question": "Which accounts can be exported?",
      "answer": "Only the requesting owner's account",
      "provenance": "User answer in conversation turn 3",
      "rationale": "Matches the accounting task and existing ownership boundary",
      "dependsOn": [],
      "disposition": "answered",
      "blocking": true
    }
  ]
}
```

Record every relevant decision, assumption/default and deferred item in `decisions`. Dispositions
are `answered`, `default`, `excluded`, `deferred`, or `open`. An open decision prevents review.
Defaults need disclosed applicability and provenance. Deferred decisions require `blocking: false`,
`owner` (owner or next action) and `trigger`. An answered/default decision cannot depend on a
deferred or excluded premise. Unknown dependencies and cycles block review. `begin` deliberately
creates an incomplete draft; fill it through the interview, not guesses to satisfy the validator.

Use the existing specification, roadmap and accepted decisions as helpful context. The roadmap
is user-owned after bootstrap; its status is not an intake gate. Clarify unresolved substantive
scope choices without importing bootstrap prerequisite ledgers or asking for renewed approvals.

```text
specification_intake.py review --entry EPIC-001 --feature invoice-export
specification_intake.py confirm --entry EPIC-001 --feature invoice-export --review-sha256 <presented-hash> --confirmation-source "<user-message-reference>" --confirmation-text "<actual-user-confirmation>"
specification_intake.py check --entry EPIC-001 --feature invoice-export
specification_intake.py check-spec --spec specs/001-invoice-export/spec.md
```

`review` renders `review.md` plus `review-basis.json` from the complete brief and current governance
context. `confirm` records confirmation of that exact review in `confirmation.json`. The validator
checks evidence integrity; the calling agent is responsible for truthfully recording the user's
confirmation and judging semantic scope/acceptance quality. There is no automatic approval mode.

Confirmation binds the substantive brief and the actual presented synthesis. Preserve unchanged
confirmation when tooling, roadmap metadata or document fingerprints change. If scope changes,
review the changed answers with the user. Reference the confirmed brief from the normal spec;
no per-rule applicability or phase review document is required. Historical hash references remain
readable, but are not prerequisites for ordinary implementation.

New specs include one `Specification roadmap entry` (parent epic), one `Specification feature ID`,
the exact `Confirmed intake brief` path and its `Confirmed intake SHA256`. The resolver validates
the feature, parent and normalized reference together. Ordinary scope/context consumers follow that
reference instead of guessing a brief path from the epic. Legacy specs keep their v1 identity and
the `--entry`-only commands. Upgrading tooling never rewrites historical confirmed brief bytes.

Source commitment is disclosed separately from current commissioning. Selecting an exploratory seed
can begin a draft; the actual reviewed feature confirmation commissions the chosen scope. It does
not silently promote the source map or require roadmap-status approval. Refining child specifications
within an epic is normal elaboration; present actual changes to epic outcomes, priority or
dependencies in the same scoped review. Shared architecture changes retain architecture review.
