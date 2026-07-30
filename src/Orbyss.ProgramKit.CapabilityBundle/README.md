# Orbyss.ProgramKit.CapabilityBundle

This internal exact-byte verification package carries copies of the six
consumer Program Kit development capabilities:

- `design-csharp-build-gate`
- `develop-software`
- `design-software`
- `implement-software-plan`
- `maintain-software`
- `publish-dotnet-application-locally`

Their inert Codex and Claude Code wrapper templates are separately listed
provider adapters. The capability index, generated catalog, contributor
authoring capability, and Release Cycle reservations are deliberately
excluded.

Bundle version `0.1.0-alpha.3` uses the unique `.agent-capabilities` source
tree. It also carries the exact consumer catalog, gate-authoring catalog and
migration, troubleshooting guidance, and inert software-change completion
profiles. Supporting resources are not provider-discoverable, independently
invokable, or authoritative.

Consumers do not install this package. The `Orbyss.ProgramKit.CommandLine`
tool embeds and verifies the same canonical closure. Installing or copying
either package does not register a capability, grant authority, or start work;
the explicit `program-kit capabilities initialize` operation is required.
Codex uses `.agents/skills/`; Claude Code uses `.claude/skills/`. Exact legacy
Codex wrappers under `.codex/skills/` are migration input only. The explicit
`capabilities uninitialize` operation removes one exact owned provider binding.
