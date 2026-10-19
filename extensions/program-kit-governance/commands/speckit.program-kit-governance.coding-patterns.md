---
description: Prepare or inspect a versioned coding pattern through existing coding context.
---

Read the user's problem, plain-language/code submission and requested scope. Use
`scripts/coding_patterns.py draft --repository . --submission <existing-local-file>
--id <identity> --invariant <canonical-rule-id> --output <new-draft.json>`.
Read its actual missing-proof output. Help the user edit the single draft using
the versioned contract in `scripts/coding_patterns.py:validate`; do not invent
semantic applicability or evidence from prose. The draft references supplied
source without executing it. Existing canonical rules retain their authority.

For explicit teaching/improvement, prepare one request described in
`scripts/coding_patterns.py:teach` (problem, new/refine/replace/retire intent, exact prior
version when applicable, supplied source or known gap, guidance/scaffold/check/
example and accepted-artifact changes). Run `coding_patterns.py teach --request
<local-request.json> --output <new-contribution.json>`. Review the single editable
contribution and missing proof. Empty change categories need an explanation; a
manual recipe need not invent a generator. Performance claims need actual bounded
workload/runtime/resource/correctness/adverse-case/counterexample observations.
Do not infer a universal optimization or run commands from the submitted data.

Review the draft's semantic identity, invariants, applicability/exclusions,
compatibility, examples, normal check/review owners and limits. Explicitly merge
reviewed declarations into `docs/architecture/coding-patterns.json` for private
local use, or propose a source change to shared `phase-obligations.json` through
ordinary repository review. No automatic upstream submission or publication.

Use `phase_obligations.py prepare --feature-dir <feature> --format json` for actual
selection and `coding_patterns.py inspect --feature-dir <feature>` for its pattern
view. The existing plan's `pattern-choices` block records an exact version and
contextual reason when alternatives require a choice. Use the existing native or
named toolkit verification owner explicitly; pattern commands do not dispatch checks.
After actual checks and ordinary semantic review,
`coding_patterns.py bind-evidence --feature-dir <feature> --id <local-pattern>`
appends a local binding. Inspect actual results; binding is not human approval.
Reprepare/reconcile through the existing implementation and completion routes.

Retain earlier versions, retired declarations and failed/stale evidence. A shared
lesson requires an explicit selected contribution and ordinary privacy/provenance
review. For local shared preparation, author a standalone publishable draft and
explicit file selection, then run `coding_patterns.py prepare-shared --selection
<selection.json> --output <new-local-directory>`. Review every selected byte;
this allowlist is not a secret detector. Never export the local registry/inspect
view, private review or execution history. Consumer evidence cannot transfer;
rewritten shared paths/context require fresh maintained installed proof and
ordinary source review before exact version adoption. Preparation never submits
upstream. Never dispatch agents, provider operations or submitted shell commands
as part of this command.
