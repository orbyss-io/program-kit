---
description: Connect Azure team planning and apply an approved epic-to-requirement proposal.
scripts:
  py: scripts/azure.py
---

Read `.specify/extensions/program-kit-delivery/references/azure-planning.md` and the common
delivery reference. Preserve previously accepted choices. Azure planning requires an existing
human Azure CLI login and verified individual identities; never request or write a raw token.
Group-based approvals, unattended identities and implementation claims are not supported here.

For an empty platform, use the installed `scripts/azure_setup.py` to propose the exact private
Agile project and coordination repository. Present its resources and exact proposal hash for
one coherent setup decision. Apply only that approved proposal. Attach explicitly by immutable
project/repository IDs when resources already exist; never adopt by a matching name alone.

Prepare the shared profile with explicit organization, project ID, area-root IDs/paths,
descendant scope, per-type field/state mappings and individual role IDs. Run `{SCRIPT}
--profile <profile> inspect`. Resolve missing fields/rules rather than changing shared processes
or bypassing native rules. The same person may fill several roles. Keep code-repository hosting
separate from Azure backlog authority; Phase 2 resolves the shared policy through Azure Repos.

Initialize the coordination branch with the approved exact-byte profile digest. Present and
apply its exact protection plan; verify it before activation or business writes. Keep normal
conditional commits available and preserve administrator recovery. If privileges are missing,
leave prepared state and provide the exact administrator action. Never weaken the check.

Use `{SCRIPT} --profile <profile> discover --output <new-observation.json>` to find all epics in
scope, including human-created untagged items. Discovery grants no planning approval. Preserve
the native IDs, descriptions, comments and existing hierarchy. Track moved/inaccessible known
items explicitly. A human portal acceptance step must actually be performed by the user.

Refine content with the four installed templates. Author parent-first JSON entries against
`azure-planning.schema.json`: stable logical key, canonical kind, existing nativeId or null,
parent key, native fields and optional milestone records. Existing native items with empty
fields are adopted without rewriting text. A changed description must contain the full
reviewed text, including human contributions. Reference required technical artifacts in the
description; do not copy architecture authority into Azure or invent approvals/commitments.

Generate a proposal and its Markdown review with `plan --input <entries> --output <proposal>`.
Present the exact items, field changes, parent links, milestones, source revisions and hash.
Record the user's actual approval source with `approve --input <proposal> --approved-sha256
<reviewed-hash> --decision-source <conversation-reference>`, then `apply --proposal-id <id>`.
No per-item approval is needed for unchanged operations within that approved proposal. An API
permission or actor ID is not evidence that the user approved the business change.

An interrupted create stays unknown. Use `recover --operation-id <id>` and resume the same
proposal; never create a replacement because a search was empty. Changed inputs or conflicting
identities require a revised review. Completed operations remain recorded. Milestones are
business checkpoints on Epics/Features, not automatic consequences of child closure.

For repository activation, prepare the existing local-entry → Requirement bindings with the
offline delivery command and pin the committed profile bytes. Complete or explicitly pause
active local implementation first. Present `activation-plan`, approve its exact hash, then
`activate`. Bootstrap and later onboarding use this same sequence; do not rerun bootstrap.
Unbound local entries cannot pass provider-backed refinement checks. Implementation, delivery
completion and acceptance admission remain unavailable until their later phases.
