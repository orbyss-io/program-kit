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
Define Foundation resources, bindings and environment placement only in the typed
`eng/foundation-composition.json`, linked to Accepted architecture/selection identities.
Database resources belong to explicit servers and named context policies; multiple
applications can share one identity authority with separate clients/resources. Generated
settings, imports and Docker Compose are outputs. Resource composition supplies no reason
to add a `.Composition` assembly: an extra source project needs a real Accepted responsibility.
Describe test scope: risk-selected operation verification, story regression, reverse dependencies for shared
contracts/configuration, and complete feature/domain acceptance at closure or formal handoff.
Name actual test projects/framework filters and non-source inputs that need owned test mappings.
Use existing engineering configuration and native commands; no per-feature verification dossier.

Reconcile the wire contract against the selected publisher before endpoint implementation.
Foundation 0.3.3's problem writer has a closed envelope; `retryMode`/`statusPath` problem
extensions are incompatible. Record the conflict at planning/reconciliation and pause the
dependent endpoint work pending human approval. A proposal may place retry guidance in typed
operation responses/UI using retained server-issued IDs; a proposal is not contract approval.
Prove numeric DTO schemas match the selected strict request profile using real producer output
and numeric-string rejection tests. ASP.NET defaults may describe numbers as number|string.
Keep strict parsing, existing compatibility baselines and the human review gate.
Use the registered OpenAPI `.json` as the single wire-shape authority; its `.contract.json`
owns pipeline configuration and `.baseline.json` retains compatibility history. At planning,
run `python eng/openapi_capabilities.py --repository . --feature-dir <feature>` against
the proposed/current document, covering relevant errors as well as successes and native
`x-foundation-json-contracts` bindings. Missing schemas/bindings/captured capabilities are
scoped unresolved work, never an assumed pass. Planning admission is not runtime evidence.
After-plan repeats admission. Generate real OpenAPI from the earliest DTO/endpoint metadata
scaffold before business effects; the native producer pipeline checks untouched output before
baseline/client changes. Preserve existing strict annotations and review actual compatibility
changes; never strip TypeScript string unions or reset baselines to conceal a mismatch.
The supported scoped default pairs `[JsonNumberHandling(JsonNumberHandling.Strict)]` with
`[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]` on request DTOs and their
nested owned types. Qualify each actual binding. Under Foundation 0.3.3 / exporter 0.2.5 /
ASP.NET OpenAPI 10.0.12, nullable integer metadata still emits `integer|string|null` even with
class/property Strict attributes: retain the exact unresolved diagnostic and do not claim
universal numeric parity or remove nullable intent. A broader publisher integration is separate.
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
