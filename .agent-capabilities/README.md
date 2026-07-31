# Program Kit agent capabilities

`.agent-capabilities/` is the only canonical source tree for Program Kit's
provider-neutral human-session capabilities and provider-adapter templates.
It is inert development content: runtime libraries and generated applications
must never load or execute it.

Canonical definitions use
`.agent-capabilities/capabilities/<capability-id>/CAPABILITY.md`. Provider
adapters live separately under `.agent-capabilities/provider-adapters/` and
contain discovery metadata plus a pointer to exactly one canonical definition.
They never copy canonical procedure or authority rules.

A human explicitly initializes an understood provider adapter into a chosen
human-led workspace root. Initialization does not copy canonical definitions,
grant authority, or start work. See
[provider-adapters/README.md](provider-adapters/README.md) for the adapter
contract and [capabilities/INDEX.md](capabilities/INDEX.md) for Program Kit's
canonical availability catalog. Consumer products choose their own
`none`, `local-optional`, or `repository-managed` posture as described in
[consumer-integration.md](consumer-integration.md); Program Kit never selects
or enforces that repository policy.

The source tree carries `authoring-workspace.json`; consumer initialization,
catalog, preflight, retrieval, and removal fail closed while that marker is
present. The marker separately records ignored provider-local projection
contracts, independently of the consumer CLI provider allow-list. Each active
provider skill contains a complete copy of its canonical definition and
requires no installed Program Kit CLI or runtime path lookup.

At the start of a fresh task, before a source capability is loaded,
`build/Sync-SourceContributorCapabilities.ps1 -Provider
<active-provider-id> -RefreshIfStale` resolves the registered provider root,
compares the local copies with current canonical content, and refreshes only
missing or stale ones. An active task never refreshes a capability it is
already executing unless the human explicitly requests that experiment.

The installed consumer CLI embeds the verified content-only capability
closure, which deliberately excludes the marker and provider-local source
projections, and rejects user-home global provider roots.

Non-discoverable supporting resources live below `supporting-resources/`.
They may hold exact shared procedure bytes referenced by canonical
capabilities, but they are not capabilities, provider adapters, triggers, or
authority grants. The initial resource is the
[software-change completion profile set](supporting-resources/completion-profiles/software-change/completion-profile-set-1.0.0.json).
