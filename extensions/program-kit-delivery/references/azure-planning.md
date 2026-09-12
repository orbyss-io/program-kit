# Azure planning: setup, activation and reviewed writes

The optional module remains disabled until a repository's explicit authority handoff. Azure
planning uses the existing human Azure CLI sign-in; credentials never belong in profiles,
work items, operational commits or evidence. Individual provider identity IDs determine roles.
An authenticated actor must hold the configured role; recording an actor name or having native
write permission does not establish business approval. Approval evidence records the actual
conversation decision, exact proposal digest and verified acting identity. This is a cooperating
session protocol, not an independent cryptographic proof of a human click.

## Setup and policy

Use `python .specify/extensions/program-kit-delivery/scripts/azure_setup.py --organization <org>
propose --project-name <name> --output <proposal.json>`. To attach existing resources, explicitly
supply `--existing-project-id` and, where applicable, `--existing-repository-id` plus its name.
Review the exact resources, then apply with `--proposal`, `--journal`, `--approved-sha256` and
`--decision-source`. A new setup creates a private Agile project and coordination repository;
it never edits an organization process. The setup journal conservatively stops after an
unacknowledged create. A successful project-creation operation can be polled on resume.

The `profile --setup-journal <journal> --output <profile>` command proposes default roles for
the signed-in human, project-root area scope and per-type native mappings. Review these defaults;
one person may hold several roles. For shared projects, narrow `azure.areaRoots` to explicit
stable area IDs, current paths and include-descendants settings. Board layouts, sprints and tags
do not change discovery scope. Area moves/renames require scope review. Type discovery verifies
available fields and states; native `validateOnly` checks required/custom rules before creating
work. Do not use `bypassRules`, infer unknown custom values or modify a shared process to make a
proposal pass.

The product schema is `delivery.schema.json` with the sibling `azure-planning.schema.json`
registered as an offline resource. Older prepared profiles remain valid. Only profiles with
verified Azure settings can activate this planning adapter. Top-level field policies describe
authority; `azure.types` gives actual per-type native fields and initial states. Milestone
content is rendered into the reviewed Epic/Feature description, not a made-up native field.

All following commands use `python .specify/extensions/program-kit-delivery/scripts/azure.py
--profile <profile>`, with `--repository <consumer-root>` when needed. Run `inspect`, then
`initialize --approved-sha256 <exact-byte-profile-hash> --decision-source <approval>`.
Initialization commits the shared policy at `delivery/profile.json` alongside operational state;
it does not activate a consumer. Pin the returned repository/commit/path/byte hash in the consumer
binding, with a matching snapshot. Profile payloads do not contain their own commit hash.
The Azure adapter resolves this policy through Azure Repos in the selected project. Code
repositories can be hosted in Azure or GitHub; their primary Requirement bindings are independent.

Generate `protection-plan --output <plan>` and apply the approved exact hash with `protect`.
The exact operational branch permits normal conditional writes, explicitly denies participating
identities history rewrite/deletion and protection changes, and checks effective caller rights.
Azure's creator grants must be replaced explicitly. Unrelated ACL entries are preserved. The
guarantee covers participating actors; administrators retain the ability to restore/change access.
Do not require PRs for operational commits or treat this as application-code branch policy.
If protection cannot be established, retain prepared state and use administrator-assisted setup.

## Discovery and proposals

`discover --output <new-file>` observes all mapped epics in the area scope, regardless of tags,
and records their identities/revisions in shared observation state. Known moved or inaccessible
items remain visible as outside-scope or unknown. Work-item queries are partitioned by ID; current
items are rechecked before writes. This is checkpoint-driven observation, not a background monitor
or complete historical reconciliation service. A created-by identity alone does not prove a portal
action: human acceptance also requires the user's confirmation that they performed it.

Create a JSON array of parent-first entries:

```json
[
  {"key":"BUSINESS-EPIC","kind":"epic","nativeId":123,"parent":null,"fields":{},"milestones":[]},
  {"key":"FEATURE-A","kind":"feature","nativeId":null,"parent":"BUSINESS-EPIC",
   "fields":{"System.Title":"Status visibility","System.Description":"<p>Reviewed scope and outcome.</p>",
             "System.AssignedTo":"<verified-Azure-identity-ID>"},"milestones":[]}
]
```

Existing IDs with empty fields are adopted without rewriting their text. New items require title,
outcome and an accountable owner. The adapter resolves stable identity IDs to native account values
from the explicitly configured individual role roster; arbitrary owners and group assignment are
not part of this initial adapter. Expand the reviewed roster before assigning another participant.
It uses those native account values
when dispatching and verifies identity IDs again during recovery. Requirements need observable
acceptance content before provider-backed refinement admission. Native states represent progress;
planning cannot close work or grant implementation. Meaningful Tasks preserve the Requirement's
outcome and represent an independent contribution or receiving integration obligation.

`plan --input <entries> --output <proposal.json>` produces an immutable proposal and Markdown
review with exact fields, relationships, milestones and native revision/content bases. The
business owner reviews it once; `approve --input <proposal> --approved-sha256 <hash>
--decision-source <actual-conversation-reference>` records that exact decision. Then use
`apply --proposal-id <id>`. Technical artifacts remain authoritative in Git and can be linked in
the reviewed description. Existing local IDs remain keys in the consumer binding.

A milestone is a named checkpoint on an Epic/Feature: ID, name, owner, conditions, participating
Requirement logical IDs and optional target date. The Azure description carries its business
meaning. Operational records retain proposal provenance rather than becoming a second editable
backlog. Child closure does not accept a milestone, and a target date is not silently a commitment.

## Conditional writes and recovery

The shared operational branch stores approved proposals, operations, adopted identities and
activation registrations. Expected-head commits grant one cooperating worker permission to dispatch
an operation once. The hierarchy is a resumable sequence, never a multi-item transaction. Before
each operation, recheck the accepted basis. Azure's automatic parent revision changes are permitted
only for the exact child links this proposal applied, with business/custom fields unchanged.
Azure may expose those parent links without advancing the parent revision. Links and business
fields are checked even when the revision is unchanged. If it advances, the increase must equal
those new links; other revision changes and human link comments stop reuse.
Human changes stop affected application; they are not interpreted as accepted architecture changes.

Before create, persist dispatch and embed its operation correlation text in the initial description.
If a response or identity-record write is lost, use `recover --operation-id <id>`. Recovery searches
the project, verifies the exact marker, destination, original fields, owner identity and relations,
and records the existing identity. No match remains unknown; it never permits another create.
Duplicates or changed payload require review. Only Azure's observed whitespace insertion before
closing HTML paragraphs is normalized; text, links and other markup remain checked. Recovery hints
do not substitute for complete provider correlation observation. Preserve earlier run evidence.

## Repository handoff and limits

Prepare binding/history with the offline delivery command. Bind existing local entries to adopted
Requirements, and pin the profile bytes already committed above. Finish or explicitly pause active
local implementation before `activation-plan --output <proposal>`. Review the handoff and activate
with the exact hash and decision source. The provider registration is written first; an interrupted
local write can finish by repeating the same activation proposal. Ordinary missing/malformed
activation records remain inconsistent, never silently disabled.

Bootstrap and later onboarding use this same handoff. Activation is per repository. Refinement
checks verify current registration, immutable evidence, profile source, branch protection, mapped
Requirement content and accepted planning basis. Missing bindings, unknown operations and material
changes block admission. Existing architecture/intake gates remain mandatory. Implementation,
verified delivery, business acceptance, profile-change/disconnect workflows, complete comment/history
reconciliation and execution claims remain their later phases. No CI credentials or agent sessions
are provisioned by these commands.
