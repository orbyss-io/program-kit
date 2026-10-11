## Architecture and engineering

<!-- program-kit:story-delivery-v1 -->

Describe the complete vertical outcome, domain owner, public contracts and allowed dependency
boundaries. Apply the relevant Program Kit knowledge before selecting implementation patterns.
Record substantive choices and applicable ADRs here; preserve existing accepted architecture.
Review actual responsibility placement against applicable canonical constraints and accepted decisions.
In `eng/architecture.json`, each project has compact `responsibilities` records: meaningful `name`,
`kind` (contract, pure-policy, pure-helper, runtime, http, persistence, composition or test), named
`effects`, and `provides` for implemented public capabilities. Every provided capability needs its
real binding. Core contracts/policies have no runtime effects. Describe the reasons here; declaration
consistency is not proof of semantic ownership. Record surfaced conflicts and their governed resolution.
Use the phase-context command's normal inline resolution procedure for retained feature-plan decisions;
review provenance refers to the actual review, not a generated claim of human approval.
Conditional optimizations require their conditions and, where relevant, measurements.

Plan actual compiler/analyzer, architecture, contract, security and behavioral tests at the
cheapest reliable level. Put architectural role/exception configuration in `eng/architecture.json`
and native dependency/composition configuration in their ordinary engineering files.
Use the selected published host and package/bundle composition when applicable.
Describe test scope: risk-selected operation verification, story regression, reverse dependencies for shared
contracts/configuration, and complete feature/domain acceptance at closure or formal handoff.
Name actual test projects/framework filters and non-source inputs that need owned test mappings.
Use existing engineering configuration and native commands; no per-feature verification dossier.
Review changed responsibilities and applicable mechanisms, not a repeated full SOLID inventory per edit.

No artifact-ownership, obligation-design/review, semantic-contract or proof-attestation dossier
is required. Keep semantic design and test intent here; execution output belongs in artifacts/.

## Story delivery and review

Confirm small runnable journeys and their independent walkthroughs/non-goals, connected effects,
success/material failure scenarios, exact enabling dependencies and estimated active effort to review.
Reconsider oversized stories before tasks; larger coherent stories disclose rationale and effort.
Record risk and verification sequence: coherent known scaffold generation first, maintained checks,
then missing consumer-specific tests; prefer meaningful test-first for critical/uncertain behavior and
reproducible bugs. Wiring can use immediate verification; refactoring uses regressions. Reuse exact
unchanged qualified proof within its actual scope; policies/customized integrations keep their checks.
Default owner/reviewer to the requesting human. Plan required human review per story, with runnable
entry point, prepared data/account, walkthrough and limitations. Earlier gates require explicit agreement.
Default pause before more product work; acceptance or an explicit checkpoint/bounded batch deferral
permits its actual scope. Deferred reviews remain due at feature acceptance. Separate engineering
completion from human usefulness/clarity/faithfulness review; do not repeat the technical suite for humans.
Use the maintained `phase-evidence.md` transitions/state on entry, resume, progression and finish,
including absent hooks and formal handoff. Record actual assignment/decision source and material basis.
Use adjustable advisory defaults of 60 active minutes per operation and 120 per story, including repairs,
excluding human waiting. Preserve effort on resume; elapsed time alone grants no authority or block.
