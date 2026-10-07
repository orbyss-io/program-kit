## Architecture and engineering

Describe the complete vertical outcome, domain owner, public contracts and allowed dependency
boundaries. Apply the relevant Program Kit knowledge before selecting implementation patterns.
Record substantive choices and applicable ADRs here; preserve existing accepted architecture.
Conditional optimizations require their conditions and, where relevant, measurements.

Plan actual compiler/analyzer, architecture, contract, security and behavioral tests at the
cheapest reliable level. Put architectural role/exception configuration in `eng/architecture.json`
and native dependency/composition configuration in their ordinary engineering files.
Use the selected published host and package/bundle composition when applicable.
Describe test scope: operation red/green/refactor, story regression, reverse dependencies for shared
contracts/configuration, and complete feature/domain acceptance at closure or formal handoff.
Name actual test projects/framework filters and non-source inputs that need owned test mappings.
Use existing engineering configuration and native commands; no per-feature verification dossier.
Review changed responsibilities and applicable mechanisms, not a repeated full SOLID inventory per edit.

No artifact-ownership, obligation-design/review, semantic-contract or proof-attestation dossier
is required. Keep semantic design and test intent here; execution output belongs in artifacts/.
