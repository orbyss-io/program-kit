## Architecture context

<!-- program-kit:story-delivery-v1 -->

Name the domain owner, affected boundaries, contracts and important quality requirements.
Reference confirmed intake and relevant architectural decisions when present. Clarify material
product ambiguity; unchanged intake does not need another approval because tooling changed.
The roadmap is a user-owned planning aid, not a prerequisite ledger for specification work.
One roadmap epic may have several specifications. For new feature intake, record the parent
`Specification roadmap entry`, independent `Specification feature ID`, exact `Confirmed intake brief`
path and its `Confirmed intake SHA256`. Reuse the preserved feature seed and supplied boundary
rationale, rules and examples; resolve consequential gaps without restarting whole-product discovery.
Legacy specifications retain their existing entry-only identity and confirmed brief.

Describe the User-visible vertical outcome and Explicit non-goals in the normal specification.

Preserve the core template's prioritized user stories, independent tests, Given/When/Then acceptance
scenarios and measurable success criteria. Include applicable failure and boundary cases, assumptions
and dependencies. Explicitly request automated behavioral tests under the constitution's risk-based
policy. Describe observable outcomes and quality constraints here; leave technology choices and
test frameworks to the plan. Intake answers inform this specification, not a second requirements set.

Each story has one coherent actor intent and useful observable outcome, explicit non-goals and an
independent runnable walkthrough through its supported interface and connected effects. Include
necessary authorization, ownership, persistence and recovery behavior. Split oversized stories by
useful journeys before tasks, never technical layers. Preserve real provider/security/authority gates.
Estimate time to human review including preparation/integration/verification; disclose rationale and
effort for larger stories. The two-hour target is a sizing aid, never an automatic rejection.
