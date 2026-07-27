# Orbyss.ProgramKit.CapabilityBundle

This content-only package carries exact copies of the three distributable
Program Kit development capabilities:

- `develop-software`
- `design-software`
- `implement-software-plan`

Their inert Codex and Claude Code wrapper templates are separately listed
provider adapters. The repository-only `publish-dotnet-application-locally`
capability, the capability index, generated catalog, authoring capability, and
Release Cycle reservations are deliberately excluded.

Bundle revision `2.0.0` uses the unique `.agent-capabilities` source tree. Its
canonical definitions stay in Program Kit. They are never copied into a
human-led workspace.

Installing or copying this package does not register a capability, grant
authority, or start work. The explicit `program-kit capabilities initialize`
operation verifies these exact bytes and renders only the selected provider's
thin wrappers plus an ownership lock.
