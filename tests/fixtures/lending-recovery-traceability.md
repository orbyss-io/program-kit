# Architecture traceability

Evidence links model/ADRs to confirmed specification, plan, implementation and executed tests.
The map binds source hashes; planned checks are not delivery evidence.

| Source / meaning | Decision authority | Feature owner and executable evidence |
|---|---|---|
| e01/e07/e08: context, lifecycle, module graph | bootstrap-baseline; founding-boundary | RM01 exact brief; Reservations and operation tests; compiled forbidden-reference/replacement checks |
| e01/e02/e03/e05/e08: capacity, identity, durable work | founding-durability; reservation-runtime-acceptance | RM01 canonical comparison, payload/version/retry design; ReservationStorage/LifecycleDelivery; QA01-QA07/QA15 and real restart |
| e01/e03: V1 wire/status | founding-compatibility | Reservations.Api; QA04/QA13; structural OpenAPI and unchanged behavioural acceptance |
| e01/e02/e04: immutable Forms/browser | founding-form-delivery | ReservationForms, web and reservation-page; QA08-QA10/QA14; consumer form meaning |
| e02/e05: fixtures, migrations, bundle | bootstrap-baseline; founding-compatibility | Controlled setup; tests/Compatibility; published-host activation; QA05/QA11/QA14 |
| e01/e06: real reference upgrade | founding-compatibility | Upgrade owner; released admission, same coordinator, preserved edits/identity/data; QA16 |
| d01: defaults, source/license and pins | bootstrap-baseline | Exact register/selection and prerequisite receipts; bounded named runtime assertions |

## Slice coverage

`slice-rm01` traverses Forms/browser, reservation-api, rm01, reservation-persistence,
lifecycle-delivery and runtime-composition within Reservation Management. RM01 owns reserve,
confirm, cancel and query V1 contracts, reservation-form and event meaning, capacity/state,
operation outcomes and outbox/progress. Physical placement remains in founding-boundary.

J01 reserve, J02 acknowledge/confirm, J03 cancel/release, J04 replay/conflict, J05 real restart,
J06 notification recovery and J07 immutable form publication/use retain separate canonical
views inside the current combined slice. Valid outcomes preserve identities and intended effects.
Invalid input, denial, illegal transition, conflicting key, ambiguous commit and recipient
failure must retain their fixed visible responses and durable pending-work semantics.
acceptance/http-contract.json, acceptance/browser-contract.json and QA01-QA15 own assertions.
Operation tests stay local; tests/Compatibility owns integration checks. Delivery remains unproven.

## Dependencies and later work

bootstrap-prerequisites.json owns source/runtime/license, provider, Forms/HTTP and shell
conditions plus receipt hashes. The four closed proofs establish only their executed mechanisms.
reservation-runtime-acceptance proposes the missing implementation scope and replaces obsolete
closure bookkeeping. Its original predecessor stays immutable historical evidence. Feature
intake still confirms field limits, event format/order, retry constants and replay rules; delivery
must prove actual reservation behaviour under failure. Scope approval is not delivery proof.

J08 needs a separately authorised released reference consumer. Reporting needs its own audience
and read-model interview. Real exposure/identity/data/recipients trigger security review; an actual
internal subscriber triggers the dispatch decision without replacing durable ownership.

[specification-roadmap.md](specification-roadmap.md) alone assigns entry lifecycle status.
This document retains traceability and the generated navigation view, not another status registry.
