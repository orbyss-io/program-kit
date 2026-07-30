# Orbyss.ProgramKit.CapabilityBundle

This content-only package carries exact copies of the five distributable
Program Kit development capabilities:

- `design-csharp-build-gate`
- `develop-software`
- `design-software`
- `implement-software-plan`
- `maintain-software`

Their inert Codex and Claude Code wrapper templates are separately listed
provider adapters. The repository-only `publish-dotnet-application-locally`
capability, the capability index, generated catalog, authoring capability, and
Release Cycle reservations are deliberately excluded.

Bundle revision `4.0.0` uses the unique `.agent-capabilities` source tree. Its
canonical definitions stay in Program Kit. They are never copied into a
human-led workspace. The bundle also carries the inert, exact-byte
software-change completion profile set shared by full implementation and
incremental maintenance. Supporting profiles are not provider-discoverable,
independently invokable, or authoritative.

Installing or copying this package does not register a capability, grant
authority, or start work. The explicit `program-kit capabilities initialize`
operation verifies these exact bytes, renders only the selected provider's
thin wrappers, and preserves the complete exact set of other provider bindings
in a versioned ownership lock. Codex uses `.agents/skills/`; Claude Code uses
`.claude/skills/`. Exact legacy Codex wrappers under `.codex/skills/` are
migration input only.
