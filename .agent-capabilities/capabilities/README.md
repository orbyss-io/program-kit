# Capability catalog

This file is a generated, non-authoritative projection of [`INDEX.md`](INDEX.md).
Capability availability is owned only by the canonical index.

Source path: `.agent-capabilities/capabilities/INDEX.md`
Source digest: `sha256:263b00bfd766264fec0f5f72b5b40802bdd92248c9c68535063b48b7190a301e`

| Capability ID | Flow category | Status | Canonical definition | Active-provider wrapper | Notes |
| --- | --- | --- | --- | --- | --- |
| `author-and-maintain-skills` | development tooling | available | [CAPABILITY.md](author-and-maintain-skills/CAPABILITY.md) | [Codex adapter template](../provider-adapters/codex/author-and-maintain-skills/SKILL.md) | Program Kit repository capability for maintaining canonical capabilities and provider adapters; not in the distributable bundle. |
| `develop-software` | development | available | [CAPABILITY.md](develop-software/CAPABILITY.md) | [Codex adapter template](../provider-adapters/codex/develop-software/SKILL.md) | Routes a human-started request to one backed development flow without granting authority. |
| `design-software` | design | available | [CAPABILITY.md](design-software/CAPABILITY.md) | [Codex adapter template](../provider-adapters/codex/design-software/SKILL.md) | Produces a versioned design and implementation plan, then stops for human approval. |
| `implement-software-plan` | implementation | available | [CAPABILITY.md](implement-software-plan/CAPABILITY.md) | [Codex adapter template](../provider-adapters/codex/implement-software-plan/SKILL.md) | Implements an exact approved plan and stops on material architectural deviation. |
| `publish-dotnet-application-locally` | local publishing | available | [CAPABILITY.md](publish-dotnet-application-locally/CAPABILITY.md) | [Codex adapter template](../provider-adapters/codex/publish-dotnet-application-locally/SKILL.md) | Repository-only wrapper over the backed W065 local publish operation; excluded from the distributable bundle. |
| `release-software` | release | unavailable | Not created | Not registered | Reserved stable flow ID; unavailable until the Release Cycle is implemented in a later backing phase. |
| `qualify-release-candidate` | qualification | unavailable | Not created | Not registered | Reserved stable flow ID; unavailable until release qualification is implemented in a later backing phase. |
| `promote-qualified-release` | promotion | unavailable | Not created | Not registered | Reserved stable flow ID; unavailable until release promotion is implemented in a later backing phase. |
