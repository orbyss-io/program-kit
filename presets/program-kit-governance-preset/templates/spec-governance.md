## Governance Traceability *(mandatory)*

- **Specification roadmap entry**: [ROADMAP ID and title]
- **Confirmed intake brief**: [Plain repository-relative path returned by specification-intake check]
- **Confirmed intake SHA256**: [Exact briefHash returned by specification-intake check]
- **User-visible vertical outcome**: [Outcome independently verified by this feature]
- **Architecture constraints**: [Ratified constitution principles, Accepted ADRs, and module boundaries that apply]
- **Owned contracts and data**: [Public contracts, lifecycle portions, and data owned by this slice]
- **Explicit non-goals**: [Behavior or technical work intentionally outside this feature]
- **Decision impact**: [None, or the ADR/design task required before implementation]
- **Authorization boundary**: [Managed endpoint permission only for a no-effect probe, or endpoint permission plus the real resource/state/effect rule]

Do not use a horizontal technical layer as the feature outcome. A new architecture, technology, or cross-module dependency decision remains a design task until its ADR is Accepted.

Generate this specification from the confirmed feature-intake brief. Preserve its scope, exclusions,
defaults and deferred items. Material changes require revisiting the affected interview decisions
and confirming the revised synthesis before planning. Missing or stale confirmation blocks the flow.
