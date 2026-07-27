# author-and-maintain-skills

## Purpose

Guide a human-led agent through creating, updating, renaming, splitting, superseding, or retiring a development capability and any provider wrapper that exposes it. The canonical definition is provider-neutral and owns the rules; provider wrappers only register and load it.

## Non-goals

- Do not authorize the work that a capability describes; creating a capability only documents how to assist that work after separate human authority exists.
- Do not create hooks, autonomous loops, MCP bindings, tool bindings, startup tasks, or provider integrations unless the human requested those exact integrations.
- Do not use capabilities as Domain Semantic Engine runtime inputs.
- Do not duplicate a canonical rules body into an index or provider wrapper.

## Inputs and outputs

Inputs:

- Explicit human request, or an already authorized implementation need that requires creating or updating a capability.
- The intended owner, concern, triggers, boundaries, and provider wrappers.
- Existing canonical definitions, indexes, and wrappers in this repository.

Outputs:

- One canonical provider-neutral definition at `.agent-capabilities/capabilities/<capability-id>/CAPABILITY.md` when a capability is registered.
- Provider wrapper updates only for providers explicitly requested or already active for that capability.
- Index and navigation updates in the same change.
- Verification notes, assumptions, and failure reports.

## Preconditions

- Confirm the work is human-led and authorized.
- Confirm the capability has one stable, verb-led identity and one owning concern.
- Confirm the trigger description is specific enough to avoid accidental activation.
- Confirm the target provider wrapper format from locally documented provider requirements before writing wrapper metadata.
- Treat a missing required active-provider wrapper as a setup blocker unless the human explicitly authorizes creating that wrapper.

## Required capability content

Every proposed capability must state:

- Stable verb-led identity and owning concern.
- Trigger description.
- Purpose and non-goals.
- Inputs and outputs.
- Preconditions.
- Allowed actions, prohibited actions, and stop conditions.
- Source-of-truth and freshness rules.
- Authority, secret, network, filesystem, provider, and destructive-action boundaries.
- Ordered procedure that separates judgment from deterministic tooling.
- Verification and failure reporting.
- Compatibility and versioning expectations for updates.
- Mapping from the canonical provider-neutral definition to provider wrappers.
- Drift check proving wrappers still point to the canonical definition and do not carry a copied rules body.
- Index and navigation updates.
- Removal or migration behavior for rename, split, supersession, or retirement.

## Boundaries

Allowed actions:

- Create or update canonical capability definitions after authorization.
- Create or update requested provider wrappers as thin loaders.
- Update capability indexes and local navigation.
- Run deterministic local checks that do not require network access unless network use was authorized.

Prohibited actions:

- Do not create capabilities speculatively.
- Do not create runtime architecture, package projects, release state, hooks, watchers, autonomous loops, MCP bindings, tool bindings, or unrequested provider wrappers.
- Do not read sibling repositories or unrelated history unless the human explicitly authorizes that source lookup.
- Do not put secrets in capability files or wrappers.
- Do not perform destructive actions unless the human explicitly requested the destructive action and the active environment permits it.

Stop conditions:

- Stop if authorization is unclear.
- Stop if the repository-owned source truth conflicts with the requested change.
- Stop if required provider format cannot be confirmed locally.
- Stop if verification shows wrapper drift, copied rule bodies, broken links, or ambiguous ownership that cannot be corrected in the same change.

## Source-of-truth and freshness rules

The canonical capability definition is the source of truth for procedure and
boundaries. Program Kit's capability index owns its canonical catalog. A
consumer initialization lock owns which provider adapters were generated into
that human-led workspace. Provider adapters own only provider-specific trigger
metadata and loading instructions.

When updating a capability, read the current canonical definition, relevant index rows, and active wrappers in this repository. Do not import conventions from sibling repositories, cached workspaces, or previous implementations unless the human explicitly authorizes that source.

## Procedure

1. Establish authority: identify the human request or approved implementation need, and record any assumptions.
2. Define identity: choose one lowercase hyphenated, verb-led capability ID with one owning concern.
3. Judge fit: reject or split proposals that combine unrelated concerns, authorize work indirectly, or need unrequested integrations.
4. Draft the canonical definition with all required content sections and boundaries.
5. Add or update inert provider templates as thin adapters only. For example,
   a Codex template may use Codex skill front matter for triggering, then use
   the exact canonical-path token that initialization resolves to
   `.agent-capabilities/capabilities/<capability-id>/CAPABILITY.md`.
6. Update the capability index and nearby navigation in the same change.
7. Run deterministic verification: required paths, Markdown links, wrapper-to-canonical pointer, duplicate-rule-body scan, and status accuracy.
8. Report results: summarize implemented, scaffolded, deferred, and aspirational claims; include verification commands and any failures.

Keep judgment steps separate from deterministic tooling: decide ownership, authority, and boundaries before generating files; use tools only to create files and verify consistency.

## Provider wrapper mapping

Each provider-adapter template and initialized wrapper must point to exactly
one canonical definition. The adapter may contain provider-required metadata
and concise loading instructions, but must not copy canonical purpose,
procedure, boundaries, or verification rules.

## Drift check

For every wrapper update:

- Verify the initialized wrapper path links to the exact canonical definition
  selected by the Program Kit initialization lock.
- Compare the wrapper body with the canonical definition for copied substantial instruction text.
- Confirm the wrapper still contains only provider-specific registration and loading details.
- Confirm the index row points to both the canonical definition and the wrapper.

## Verification and failure reporting

Report the exact checks run. If a check cannot run, state why. If a capability is only reserved, say it is unavailable and not registered. If a wrapper or index is intentionally absent, explain the human authority or backing phase still needed.

## Compatibility and lifecycle changes

Updates should preserve stable IDs when behavior remains compatible. Rename, split, supersede, or retire a capability only with explicit human authority or an approved migration need.

When renaming, splitting, superseding, or retiring:

- Update the index in the same change.
- Migrate or remove provider-adapter templates and safely reinitialize owned
  wrappers so stale registrations do not remain.
- Link from the old ID to the replacement when useful and authorized.
- State whether the old capability is unavailable, superseded, or removed.
- Verify no wrapper points to a retired or missing canonical definition.

Updating this capability requires the same review, boundaries, drift checks, and verification as updating any other capability.
