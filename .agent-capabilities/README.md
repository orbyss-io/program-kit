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
canonical availability catalog.
