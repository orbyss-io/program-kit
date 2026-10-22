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

## Operation implementation map

| Operation | Decision | Resolution | Source |
|-----------|----------|------------|--------|
| [operation-id] | ownership | [actual semantic/effect owner, public seam and first ownership-transfer edge] | plan.md#Architecture and engineering |
| [operation-id] | results | [valid result/state invariants and material failure meanings] | plan.md#Architecture and engineering |
| [operation-id] | limits | [Limits: stable-id, stable-id OR No applicable limits: specific reason] | plan.md#Architecture and engineering |

Use this existing plan table to make applicable decisions concrete before dependent source work.
One row per operation/decision; `Source` is a current repository-relative or feature-relative file,
optionally `#Exact Markdown heading`, containing its design basis. Keep each resolution at most
1600 characters; refer to the actual existing design section for detail. Do not create another receipt.
Always resolve `ownership`, `results` and `limits`. The `limits` row declares an exact comma-separated
inventory (`Limits: page-size, request-deadline`) or `No applicable limits: <specific reason>`.
For each ID add one `limit:<id>` row in this same table. Use these exact semicolon-separated
`key=value` fields: `meaning; units; owner; classification; value; basis; enforcement; validation`.
Classification is `configurable-policy`, `fixed-contract` or `engineering-safeguard`.
Configurable policy additionally requires `setting; default-basis; lifecycle; consumers`. Name the
actual configuration binding, justified default (or mandatory input), activation/reload ownership,
all consuming boundaries and configured/invalid/default/boundary checks. Pure Core receives admitted
typed policy values; it does not read configuration/I/O. Fixed contracts require their actual basis;
engineering safeguards require a locally justified risk/bound, without routine human approval.
`Source` must cite an existing authoritative spec/contract/configuration/ADR or independent design
section; the operation map or whole containing plan cannot authorize its own limit. Missing product
policy remains unresolved, rather than inventing a value or laundering it through a constant. Existing
hard-coded behavior alone establishes neither an approved business policy nor an approved default.
Do not inventory ordinary indexes/discriminants or make protocol/citation/auth invariants configurable.
Reconcile actual source and all consumers against this inventory at completion; a no-limit claim and
source authority still require semantic review. Add only applicable mechanism categories:

- `cancellation-deadline`: caller token, one composed deadline, late-result handling and terminal state.
- `cleanup-uncertainty`: ownership from first acquisition/remote identity through every subsequent await,
  partial failure and cleanup, including uncertain external outcomes.
- `transactions-replay`: transaction/commit boundaries, concurrency, retry, replay and idempotency owner.
- `admission`: untrusted input, permission/tenant admission, typed contract and stable failure meaning.
- `bounds`: parser/enumeration/paging/input/output limits and their owner.
- `concurrency`: shared-state coordination, conflicting or stale completions and observable outcome.
- `configuration-time`: replaceable clock, deadline/connection lifetimes and operational options versus
  fixed protocol identities or accepted product constraints.
- `activation-drain`: registration/activation owner, admission closure, bounded cancel/drain and disposal.

A conditional mechanism that genuinely does not apply can say `Not applicable: <specific reason>`;
that claim remains subject to review. Placeholder text, generic rule lists and merely citing an ADR
are unresolved. For example: after provider dispatch returns its operation ID, cleanup must already
cover cancellation/failure of the accounting write before polling begins. Name that edge, its owner
and uncertain-outcome handling; “propagate cancellation and dispose” does not settle it.
Routine formatting repair can retain existing ownership/results and public meaning without a new ADR
or human approval. For missing choices, investigate accessible facts first. Ask the human only for
missing product intent, consequential architecture, risk or data/spending/authority. Update actual
spec/clarifications if meaning changes, accepted architecture/ADR when required, this plan and affected
task dependencies/tests. Preserve IDs, baseline, history and settled decisions. A toolkit representation
gap needs the owning engine repair/regression and supported installation, rather than a managed-file
patch or suppression. A missing environment prerequisite needs its supported owner or capable-CI proof.
Retry scoped analysis/preparation, then obtain a fresh successful implementation preflight; only the
dependent operation is blocked while unrelated ready work and native setup remain available.

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
