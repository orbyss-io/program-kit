# Equipment lending architecture

## Authority and outcome

The ratified constitution 1.0.0, confirmed intake and approved decision register govern
this local fictional .NET/React trial. [bootstrap-baseline](decisions/bootstrap-baseline.md)
records adopted choices. The canonical map, explicit acceptance scope and generated views
record current architecture authority; approval of a design does not prove implementation.
[reservation-runtime-acceptance](decisions/reservation-runtime-acceptance.md) proposes the
omitted persistence/delivery scope and supersedes historical closure bookkeeping upon approval.
The four existing prerequisite receipts retain their exact source/design bindings and limits.

The operator reserves one of two cameras, explicitly acknowledges confirmation or cancels.
Confirmed and Cancelled are terminal; cancellation releases capacity once, confirmation adds
no hold. Each successful transition owns durable notification intent. Identical retries return
the original identities and outcome; conflicting content, denials and illegal transitions cause
no new stock or notification effect. Real restart preserves state and pending work.

## Context, modules and dependencies

[founding-boundary](decisions/founding-boundary.md) defines one Reservation Management context.
Reservation policy/lifecycle is Core; notification fulfilment and future reporting are Supporting;
runtime, Forms and storage mechanisms are Generic. The canonical subdomains and J01-J08 views
remain unchanged. An adapter or page is not another business context. Separate inventory,
delivery or reporting needs new ownership/model evidence; reporting remains unscaffolded.

| Owner | Planned placement | Compile-time boundary |
|---|---|---|
| rm01 | src/Reservations/Reservations.csproj | Framework-free domain contracts and time/effect ports |
| reservation-api | src/Reservations.Api/Reservations.Api.csproj | Reservations plus admitted Foundation HTTP mechanisms |
| reservation-persistence | src/ReservationStorage/ReservationStorage.csproj | Reservations; private EF/Npgsql implementation |
| lifecycle-delivery | src/LifecycleDelivery/LifecycleDelivery.csproj | Reservations durable-work and effect contracts |
| reservation-forms | tools/ReservationForms/ReservationForms.csproj; web/package.json | Public Forms producer/renderer and consumer V1 mapping |
| runtime-composition | src/LendingRuntime/LendingRuntime.csproj | Selects API, storage, delivery and page implementations |

building-block-selection.json binds managed dependencies to these planned owners. Missing files
are not a scaffold request. Core references no ORM, HTTP, serializer, DI or implementation.
API and delivery adapters use RM01-owned capabilities rather than referencing the storage
implementation. Runtime arrows do not imply compile-time references. Operations own their
request, handler, response and tests; IWebShellFeature registers thin endpoints. Prefer cohesive
admission/query/work contracts over generic repositories. Keep time and effects injectable.

Shell lending-local selects reservation-http, reservation-storage, lifecycle-delivery and
reservation-page features; operation routes are not shells. No shared-kernel/store or
cross-context Core exception is selected. New edges require reviewed ownership and enforcement;
tests/Architecture rejects forbidden references and verifies capability replacement.

## Contracts and durable execution

RM01 owns reserve-v1, confirm-v1, cancel-v1, reservation-query-v1, admission, delivery-work and
lifecycle-event-v1. Reservations.Api owns wire DTOs; Reservations owns semantic outcomes/events;
ReservationStorage owns private schema/migrations. No other context reads its tables.
acceptance/http-contract.json and acceptance/browser-contract.json fix observable contracts.
Exact limits, payload/version/order, replay comparison and retry constants await feature intake.

[founding-durability](decisions/founding-durability.md) specifies atomic operation-ledger,
state/capacity and outbox admission. Its trial protocol locks the camera row consistently, uses
unique/nonnegative constraints, resolves original outcomes before re-evaluating retries and
reconciles ambiguous commits by stable key. Delivery claims ordered work per reservation with
durable leases, retry ownership and fenced completion. Stable event IDs and recipient
deduplication prevent repeated observed effects despite repeated sends. Recovery never replays
stock changes. Preserve the ADR's alternatives and the real-provider evidence limits.

This is the Integration Events/outbox boundary. Program Kit declares no managed durable-delivery
capability here; the consumer owns it. In-process DomainEvents awaits an actual subscriber and
cannot replace durable ownership. Migrations run during reviewed setup; host startup checks
schema compatibility. Fixture controls and observations stay outside public product contracts.

## Forms, browser and release

[founding-form-delivery](decisions/founding-form-delivery.md) and the reviewed selection bind
api_baseline, forms_immutable_release, openapi_export, json_profiles and hosted_pages.
Use Forms 0.2 public create/review/approve/publish at build time, trusted immutable admission
and the supported React renderer. The consumer owns form meaning and V1 mapping; there is no
deployed management service. Foundation owns explicit JSON profiles, named response policies,
one header writer and host mechanisms. Public typed bootstrap contains no private data/secrets.

Run the unchanged digest-pinned published Orbyss.Foundation.Host image. The consumer releases
artifacts/application-bundle.zip: shells.json, hostsettings.json, nuplane.settings.json, optional
packages and a version/source/hash-bound descriptor. The packager projects the single Nuplane
object into staged host settings; conflicting duplicates fail. Runtime loading configuration is
distinct from build feeds. Mount individual settings/package paths, preserving /app binaries.
No consumer host DLL, Dockerfile, derived image or image build/push pipeline. Application and
host versions are independent; detailed obligations remain in founding delivery/compatibility ADRs.

## UI, trust and verification

ui-experience-v1 governs Equipment lending branding, tokens, contextual navigation, comfortable
density, native CSS, system scheme, reduced motion and page metadata. The local utility is
nonindexed; analytics/discovery are disabled, training is disallowed, llms/Markdown opt-in.
Icons retain licensing/accessibility obligations. QA01-QA15 and quality-system.md own verification.

Secure profile, threat model and security evidence are none-v1. Trusted operator, local isolation
and fictional data bound the trial; deployment owns the unauthenticated-access risk. Verify
fixture-only controls, secret-free public artifacts and tamper rejection. Reassess for real
users/data/recipients/deployment or identity; future authentication owns permission gates/claims,
consumer code resource/state/effect decisions. No security certification is claimed.

The current slice-rm01 combines J01-J07 across browser, Forms, V1 operations, policy, persistence,
delivery and recipient outcome. Decomposition changes require separate review. J08 upgrade needs
independently admitted released inputs and preserves V1, consumer edits, identity and durable data.
Bootstrap scratch proofs establish mechanisms; delivery must prove the actual reservation feature,
including denial, replay, concurrency, restart and recovery. Preserve failure/token/cache/unknown
accounting. [specification-roadmap.md](specification-roadmap.md) alone owns entry lifecycle status.
