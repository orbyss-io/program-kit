# Capability catalog

This file is a generated, non-authoritative projection of [`INDEX.md`](INDEX.md).
Capability availability is owned only by the canonical index.

Source path: `.agents/capabilities/INDEX.md`
Source digest: `sha256:28c64c3f8bcc446239fd5b3940d51b9e51dcef66e14094276c6e498e59f89f49`

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
