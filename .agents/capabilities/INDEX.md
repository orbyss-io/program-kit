# Capability index

This index is the canonical availability authority for human-session capabilities in this repository. A reserved row is not a registered capability until it has a canonical definition and an active-provider wrapper.

| Capability ID | Flow category | Status | Canonical definition | Active-provider wrapper | Notes |
| --- | --- | --- | --- | --- | --- |
| `author-and-maintain-skills` | development tooling | available | [CAPABILITY.md](author-and-maintain-skills/CAPABILITY.md) | [Codex wrapper](../../.codex/skills/author-and-maintain-skills/SKILL.md) | Initial capability for creating and maintaining canonical capabilities and provider wrappers. |
| `develop-software` | development | available | [CAPABILITY.md](develop-software/CAPABILITY.md) | [Codex wrapper](../../.codex/skills/develop-software/SKILL.md) | Routes a human-started request to one backed development flow without granting authority. |
| `design-software` | design | available | [CAPABILITY.md](design-software/CAPABILITY.md) | [Codex wrapper](../../.codex/skills/design-software/SKILL.md) | Produces a versioned design and implementation plan, then stops for human approval. |
| `implement-software-plan` | implementation | available | [CAPABILITY.md](implement-software-plan/CAPABILITY.md) | [Codex wrapper](../../.codex/skills/implement-software-plan/SKILL.md) | Implements an exact approved plan and stops on material architectural deviation. |
| `publish-dotnet-application-locally` | local publishing | available | [CAPABILITY.md](publish-dotnet-application-locally/CAPABILITY.md) | [Codex wrapper](../../.codex/skills/publish-dotnet-application-locally/SKILL.md) | Repository-only wrapper over the backed W065 local publish operation; excluded from the initial distribution bundle. |
| `release-software` | release | unavailable | Not created | Not registered | Reserved stable flow ID; unavailable until the Release Cycle is implemented in a later backing phase. |
| `qualify-release-candidate` | qualification | unavailable | Not created | Not registered | Reserved stable flow ID; unavailable until release qualification is implemented in a later backing phase. |
| `promote-qualified-release` | promotion | unavailable | Not created | Not registered | Reserved stable flow ID; unavailable until release promotion is implemented in a later backing phase. |
