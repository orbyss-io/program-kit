# author-and-maintain-skills

## Identity and trigger

`author-and-maintain-skills` owns human-authorized Program Kit capability
authoring and lifecycle maintenance. Use it only after a human requests a
specific capability create, update, rename, split, supersession, retirement,
registration, packaging, or verification outcome.

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
- A deterministic refresh contract for ignored, full-definition
  source-contributor projections.
- Exact capability-bundle, supporting-resource, digest, and initializer updates
  for every product capability.
- Index and navigation updates in the same change.
- Verification notes, assumptions, and failure reports.

## Preconditions

- Confirm the work is human-led and authorized.
- Confirm the capability has one stable, verb-led identity and one owning concern.
- Confirm the trigger description is specific enough to avoid accidental activation.
- Classify the capability explicitly as a distributable product capability or
  a justified repository-only capability.
- Confirm the target provider wrapper format from locally documented provider requirements before writing wrapper metadata.
- Treat a missing required active-provider wrapper as a setup blocker unless the human explicitly authorizes creating that wrapper.
- Treat a stale source-contributor projection as expected while its canonical
  definition is under authorized edit. It is user/session state, not
  mergeable or releasable content.

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
- Product distribution and authoring-inert behavior, or the explicit
  repository-only rationale.

## Allowed actions

- Create or update canonical capability definitions after authorization.
- Create or update requested provider wrappers as thin loaders.
- Update capability indexes, navigation, the existing content-only capability
  bundle, exact-byte manifests, and initializer policy.
- Maintain the provider-local refresh operation, marker, and startup
  guidance that make full source projections available without consumer
  capability delivery.
- Run deterministic local checks that do not require network access unless network use was authorized.

## Prohibited actions

- Do not create capabilities speculatively.
- Do not create runtime architecture, package projects, release state, hooks, watchers, autonomous loops, MCP bindings, tool bindings, or unrequested provider wrappers.
- Do not read sibling repositories or unrelated history unless the human explicitly authorizes that source lookup.
- Do not put secrets in capability files or wrappers.
- Do not perform destructive actions unless the human explicitly requested the destructive action and the active environment permits it.
- Do not activate, initialize, or render a newly authored product capability in
  the Program Kit source authoring workspace or a user-global provider root.
- Do not refresh a source-contributor projection after it has been loaded for
  the active task unless the human explicitly requests that experiment. The
  authoring agent must continue executing its previously loaded projection
  throughout an ordinary capability change.

## Stop conditions

- Stop if authorization is unclear.
- Stop if the repository-owned source truth conflicts with the requested change.
- Stop if required provider format cannot be confirmed locally.
- Stop if verification shows wrapper drift, copied rule bodies, broken links, or ambiguous ownership that cannot be corrected in the same change.
- Stop if a product capability is not an inert exact-byte bundle payload for
  every registered provider, if its supporting resources are not digest-bound,
  or if authoring, build, pack, or fixture work activates it.

## Product capability distribution standard

Every new or updated Program Kit product capability must be complete in the
same reviewed change:

- one provider-neutral canonical definition with every required section;
- one thin inert adapter template for every registered provider;
- an `available` canonical index row only after all backing and verification
  pass;
- exact canonical, adapter, and supporting-resource bytes in the content-only
  capability bundle manifest and package;
- explicit consumer-workspace initialization, ownership-lock, collision, and
  drift verification;
- a source-authoring marker that makes initialization from the Program Kit
  authoring tree fail closed;
- rejection of filesystem roots, user-home global provider roots, and writes
  outside the selected consumer workspace; and
- tests proving authoring, build, pack, and fixture verification remain inert.

Repository-only capabilities must be labeled explicitly in the canonical
index, must not enter the product bundle, and must not be presented as
consumer-installable. Packaging and availability do not grant authority or
start the capability.

## Program Kit source-contributor projection standard

Program Kit's ignored provider-local skills beneath the active provider's
registered root are full-definition projections, not consumer initialization
output and not canonical sources. Each projection contains the registered
provider front matter followed by the complete canonical `CAPABILITY.md` body.
It must not rely on a runtime file-path reference or an installed
`program-kit` executable.

Capability authoring deliberately uses a staged lifecycle:

1. Begin and execute the authorized change under the previously accepted,
   already-loaded source projection.
2. Edit the canonical definition and its consumer distribution inputs without
   rewriting the active projection.
3. Run the focused validation for the canonical definition, consumer adapters,
   bundle bindings, and supporting resources.
4. Complete and commit the canonical capability change without committing the
   ignored local projection.
5. At the beginning of a fresh task, or when the human explicitly requests it,
   run the repository-backed refresh-if-stale operation before loading the
   capability.

This task boundary prevents a capability from changing the rules governing its
own in-progress authoring task while allowing a user to choose when to try
newly created or updated guidance. The local refresh must reject extra
capabilities and must replace missing, partial, path-only, stale, or
non-byte-equivalent projected bodies.

## Authority and safety boundaries

The human owns capability intent, registration, compatibility, provider
selection, and lifecycle decisions. Capability authoring grants no authority
to execute the resulting workflow. Secrets, network access, provider-global
writes, destructive actions, release state, and publication remain separately
controlled. Filesystem writes stay within the selected repository, and product
initialization is tested only in isolated consumer workspaces.

## Source of truth and freshness

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
5. Classify the capability as product-distributable or explicitly
   repository-only. For a product capability, bind its canonical definition
   and supporting resources into the existing content-only capability bundle.
6. Add or update inert consumer provider templates as thin adapters only. A
   registered provider template may use that provider's skill front matter for
   triggering, then use the exact canonical-path token that initialization resolves to
   `.agent-capabilities/capabilities/<capability-id>/CAPABILITY.md`.
7. Update the capability index and nearby navigation in the same change. Mark
   a product capability available only after its backing implementation and
   distribution verification pass.
8. Verify the changed canonical definition, consumer adapters, bundle
   bindings, and supporting resources while the authoring agent still follows
   its previously loaded projection. Do not refresh that active projection.
9. Verify the provider-local refresh contract, finite capability inventory,
   ignored provider root, and fresh-task-only startup guidance without
   materializing those files as committed source.
10. Verify exact bundle digests, content-only packaging, authoring-workspace and
   user-global denial, isolated consumer initialization, ownership-lock drift,
   required paths, Markdown links, consumer wrapper-to-canonical pointers,
   duplicate-rule-body absence in committed consumer wrappers, and status
   accuracy.
11. Report results: summarize implemented, scaffolded, deferred, and
   aspirational claims; include verification commands and any failures.

Keep judgment steps separate from deterministic tooling: decide ownership, authority, and boundaries before generating files; use tools only to create files and verify consistency.

## Provider wrapper mapping and drift check

Each consumer provider-adapter template and initialized wrapper must point to
exactly one canonical definition. The adapter may contain provider-required
metadata and concise loading instructions, but must not copy canonical purpose,
procedure, boundaries, or verification rules.

Program Kit provider-local source projections are the explicit exception:
they must contain the complete canonical body because provider discovery must
not depend on runtime path traversal or the unavailable consumer CLI. Their
canonical file remains the source of truth, deterministic fresh-task refresh
owns the ignored copy, and exact local comparison prevents independent edits.

Every provider root and format must come from an explicit reviewed provider
contract; folder recognition or a model brand alone is insufficient. Legacy
migration roots remain provider-contract data and are not current adapter
contracts.

Source-contributor provider contracts are independent of the consumer CLI
provider allow-list. A source-only contract may be added without claiming
consumer initialization support, but it must record an exact local root,
adapter root, and capability filename and supply reviewed front matter for the
finite source-contributor capability inventory.

For every consumer wrapper update:

- Verify the initialized wrapper path links to the exact canonical definition
  selected by the Program Kit initialization lock.
- Confirm the ownership lock preserves every other exact provider binding and
  records the current provider root.
- Compare the wrapper body with the canonical definition for copied substantial instruction text.
- Confirm the wrapper still contains only provider-specific registration and loading details.
- Confirm the index row points to both the canonical definition and the wrapper.

For every source-contributor refresh-contract update:

- Confirm its provider front matter comes from the selected registered
  provider adapter.
- Confirm the body after front matter is byte-equivalent to the complete
  canonical definition.
- Confirm it contains no path-only loading instruction or consumer capability
  delivery command in place of the definition.
- Confirm `AGENTS.md` allows refresh only at a fresh task boundary or after an
  explicit human request, before the capability is loaded.
- Confirm the selected provider root remains ignored and no provider-local
  projection is staged, committed, packaged, or treated as CI source.

## Verification and failure reporting

Report the exact checks run. If a check cannot run, state why. If a capability is only reserved, say it is unavailable and not registered. If a wrapper or index is intentionally absent, explain the human authority or backing phase still needed.

## Compatibility and versioning

Updates should preserve stable IDs when behavior remains compatible. Rename, split, supersede, or retire a capability only with explicit human authority or an approved migration need.

When renaming, splitting, superseding, or retiring:

- Update the index in the same change.
- Migrate or remove provider-adapter templates and safely reinitialize owned
  wrappers so stale registrations do not remain.
- Link from the old ID to the replacement when useful and authorized.
- State whether the old capability is unavailable, superseded, or removed.
- Verify no wrapper points to a retired or missing canonical definition.

Updating this capability requires the same review, boundaries, drift checks, and verification as updating any other capability.
