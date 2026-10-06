# Foundation and consumer contracts implementation plan

Date: 2026-10-06. Reusable implementation tranche integrated; qualification and public-default promotion remain in progress.

Implement reusable Foundation contracts and configuration, enforce physical modular boundaries in Program Kit, and migrate the consumer to bounded result delivery. The outcome is code whose required dependencies and mechanisms are established through public contracts, registration and tests, with ordinary source review covering responsibility ownership that compilation cannot prove.

The [first audit](C:/Users/tech_/Code/program-kit/docs/reviews/consumer-coding-standards-audit-2026-10-06.md) and [second audit](C:/Users/tech_/Code/program-kit/docs/reviews/consumer-foundation-contracts-audit-2026-10-06.md) provide the diagnosis. This plan adds the user's decisions that persistence entities belong only to the provider and large results must be paged/chunked rather than admitted as enormous HTTP responses.


## Common Program Kit branch integration status (2026-10-06)

The committed Foundation-contracts tranche6ae93b5 is integrated with handoff source9cb7298
on codex/human-infrastructure-handoff. Combined targeted checks and 74/74 bounded
Development checks pass with chromium,webkit; see the execution journals and
artifacts/validation-runs/20261006T153453Z-060b3e58/journal.json. Both acceptance controls and all
validation-inventory entries are retained, and original compatibility fixture bytes
remain unchanged. This merged tranche is reviewable but remains in progress.

Remaining work: W3's publisher-owned settings scopes, Foundation Host/package and
publication qualification, selected Build pin rendering, fresh candidate/public
profile inputs and native lock/recipe/availability/Forms/Host/sealed evidence/default
promotion, then final combined validation and clean/pushed-tree checks. The concurrent
owner performs its remaining planned Program Kit edits on the same common branch
after safely switching its clean checkout. No Program Kit Release/publication or
consumer migration authority is supplied by this merge.

## Repositories and execution boundaries

| Repository | Work |
| --- | --- |
| [Program Kit](C:/Users/tech_/Code/program-kit) | Standards, structural gates, examples, exact dependency qualification and the small consumer scenario. |
| [Foundation](C:/Users/tech_/Code/Orbyss/dotnet-foundation) | Authentication, Problem Details, JSON, host transport configuration and qualified reusable collection/deadline/provider mechanisms. |
| [De Zaaglijst](C:/Users/tech_/Code/dezaaglijst) | Read-only reference and compatibility inspection. Physical project separation, Foundation adoption, persistence corrections and paged result construction/storage/API/browser delivery remain planned consumer work requiring separate write authorization. |

CShells and Nuplane are dependencies to exercise, not automatically repositories to modify. Add work there only if a reproduced integration defect prevents the intended contracts from working. Do not fork their functionality into Foundation preemptively.

The local Foundation checkout observed in analysis is older than the consumer's published 0.2.4 source. The consumer advanced during investigation; the latest observed commit is `6800ede4a4a30c2ac99a992886aa500e2fee5d64`. Recheck current source and instructions before editing each repository. Use isolated `codex/` branches/worktrees when needed and preserve existing changes. Exact upstream versions will be selected after the candidate API and package closure are verified; this plan does not invent release numbers or rewrite historical evidence.

Plan and ordinary implementation preparation do not launch paid workers or publish packages. Candidate packages can be built and installation-tested in a private local feed. Publication and any paid Spec Kit trial retain their existing explicit gates.

### Execution boundary amendment (2026-10-06)

The user explicitly restricted De Zaaglijst to read-only access after implementation was requested. Do not edit that repository, create consumer worktrees, or run builds/tests/other commands that write there. Read source and retained evidence only. C1, C2 and C3 remain required migration work but cannot be executed under this request; consumer-side BASE architecture/specification updates and CLOSE acceptance likewise require separate write authorization. Program Kit and Foundation implementation, candidate packaging and independent disposable consumer qualification remain authorized. Record proposed consumer changes and remaining gates in the separate execution journal; do not claim the overall plan complete while these required packages remain outstanding.

The user further clarified the rollout order: complete and test the reusable Foundation/Program Kit changes, then publish the qualified version under the existing publication gates, **before** migrating De Zaaglijst. C1–C3 are follow-on work to be specified and implemented through a real consumer specification after publication; they are not executable work in this implementation request. Independent disposable consumer tests and the Notes conformance fixture supply pre-publication qualification. Candidate CLOSE covers reusable implementation, configuration, package/API surfaces and migration guidance; end-to-end De Zaaglijst rollout acceptance remains part of that later consumer specification. This amendment supersedes the original suggestion to run C1 alongside the first tranche.

## Decisions carried into implementation

1. Core, runtime implementation, API and persistence responsibilities use separate compilation projects when present. Namespaces supplement those boundaries. One context, feature bundle or deployment does not waive them.
2. Core owns models, invariants, public semantic seams, pure domain policies and small stable semantic utilities. Provider-native configuration, serializers, activation and I/O remain outside it. Stable semantics evolve through explicit compatibility/version decisions.
3. Domain-named implementation projects own activatable behavior. Appropriate registration adapters implement `IShellFeature`, `IWebShellFeature` or `IMiddlewareShellFeature`; individual business classes implement semantic interfaces. Separate EF entities, configuration, contexts and migrations belong to the persistence implementation.
4. Prefer native .NET/ASP.NET mechanisms. Use `IExceptionHandler` and `AddExceptionHandler<THandler>()` for known exceptional failures and `IProblemDetailsService` for writing. Add Foundation contribution contracts where they establish reusable guarantees; do not create another global exception pipeline.
5. Lifecycle constants live in narrowly owned Constants/keys types or exported framework constants. Deployment budgets live in typed validated configuration. Domain outcome policy remains consumer-owned.
6. Known success and failure JSON is bounded. Large collections and nested result sections page independently. Internal construction, storage reads, hashing and browser rendering must also remain bounded.
7. Existing canonical bytes, hashes, receipts and saved revisions retain their meaning. Changing the delivery protocol is separate from changing canonical identity. Any changed stored representation or byte algorithm receives its own version and retained compatibility path.

## Work packages and dependencies

Each row is a reviewable change or a small group of closely related changes. Contract decisions stay in normal ADR/plan material; there is no additional approval dossier system.

| ID | Deliverable | Depends on |
| --- | --- | --- |
| BASE | Verified source bases, ownership/API decision record and regression fixtures | None |
| PK1 | Mandatory modular standards and source/planned-graph enforcement | BASE |
| F1 | Shared problem definitions/policy and native exception integration | BASE |
| F2 | Shared validated identity contract and BFF admission | BASE |
| F3 | Configured typed JSON request/response contracts and bounded writing | F1; interfaces can be drafted in parallel |
| F4 | Reusable deadline and PostgreSQL datasource/context-factory mechanisms | BASE |
| F5 | Qualified immutable value-sequence and canonical UTF-8/hash mechanics | BASE; reuse F3 bounded primitives where appropriate |
| F6 | Real shell activation, package/loader and conformance qualification | F1–F5 |
| C1 | Later consumer specification: physical project separation with preserved behavior | PK1, PK2B; separately authorized consumer specification |
| PK2A | Explicit development candidate profile, examples and compatibility recipes | F6 |
| PK2B | Published Foundation qualification and shipped-default promotion | PK2A; authorized upstream publication and public availability/closure gates |
| TRIAL | Small consumer fixture and deterministic conformance oracle | PK1, PK2A, F6 |
| C2 | Later consumer specification: adoption and persistence repairs | C1, F6, PK2B; first deterministic TRIAL checks |
| C3 | Later consumer specification: bounded evaluation/saved-result paging through storage and browser | C2, F3, F5; proposed protocol design starts at BASE |
| CLOSE | Reusable candidate acceptance and migration documentation; later consumer rollout acceptance | Candidate: PK1, F1–F6, PK2A, TRIAL; publication: PK2B; later consumer rollout: C1–C3 |

PK1, F1, F2, F4 and F5 can progress in parallel after BASE. Each shared file has one writer. F6 and consumer adoption wait for concrete APIs and candidate packages. Prepare the result protocol early so Foundation's output contracts serve a real consumer rather than an invented generic framework.

## BASE source and compatibility preparation

- [ ] Read contributor instructions and establish the authoritative Foundation branch containing the published baseline and intervening fixes; do not edit the old local checkout as though it were current.
- [ ] Record the current project/package/feature graph and proposed additive contract packages. Avoid renaming every existing Foundation Abstractions package as part of these behavior changes.
- [ ] Capture existing claim identifiers, generic error codes, profile names, canonical vectors, persisted snapshots and exact replay identities as regression fixtures. Existing validated claims and canonical bytes must not drift accidentally.
- [ ] Record the new consumer delivery protocol and evaluation lease semantics in its normal architecture/specification artifacts. The user's paging decision replaces the enormous-response assumption; required precise wire/storage changes are part of this work.

Completion: source bases and compatibility commitments are explicit, planned APIs have owners, and the first negative tests can be written against the actual baseline.

## PK1 structural and coding standards

Change [modularity guidance](C:/Users/tech_/Code/program-kit/extensions/program-kit-governance/references/modularity-and-contracts.md), [.NET profile](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/references/technology-profiles/dotnet.md), [persistence profile](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/references/persistence-profiles.md) and their governing ADR. Remove the direct ORM mapping exception for Core models. Make project/package/activation/deployment decisions distinct.

- [ ] Restore binding rules: the capability belongs to Core; its implementation belongs to a distinct permitted implementation/provider/bridge project. Composition selects behavior rather than containing the implementations it selects.
- [ ] Reject role relabeling, EF in API/composition, same-project Core/provider bindings, omitted active capabilities and namespace substitutions such as `persistenceOwnerNamespaces`.
- [ ] Add planned-manifest validation using the same rules before builds. Route it through after-plan/after-tasks and before affected implementation. Keep ordinary `eng/architecture.json`; an empty greenfield or pure-Core graph remains legitimate.
- [ ] Add operation-owned endpoint/request/response conventions, instance endpoint dependencies, owner-specific constant placement, factory-owned independent persistence units and typed Foundation adoption to the references/examples.
- [ ] Make upgrades diagnose incompatible historical graphs without overwriting ADRs, relabeling roles or silently replacing consumer configuration.
- [ ] Retain explicit review of serializers and provider configuration hidden behind ordinary BCL types. Do not claim a filename or dependency-prefix test proves semantic ownership.

Primary code targets are the maintained [repository verifier](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/templates/dotnet/files/eng/repository_architecture.py), its [rules](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/templates/dotnet/files/eng/architecture_rules.py), phase-obligation/preflight routing and `dotnet_sync.py` upgrade diagnostics. Add negative fixtures to architecture-recipe, normal-development, standalone-engineering and architecture-placement validators, updating validation inventory inputs when necessary.

Completion: the original mixed Workbench graph and its hardcoded namespace exception are rejected; valid pure Core utilities, proportional operations and empty initial repositories remain accepted. Actual registration/resolution/lifetime tests complement the structural checks.

## F1 one problem representation and native exception dispatch

Extend `Orbyss.Foundation.Web.ProblemDetails`, with framework-light definition contracts in a lean Core project if needed. Keep the existing ASP.NET writer and middleware. [Native handlers are singleton, ordered implementations registered with AddExceptionHandler](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/error-handling?view=aspnetcore-10.0#iexceptionhandler); their request-scoped dependencies must not become constructor captures.

- [ ] Add validated immutable problem definitions and bounded field diagnostics, public code/extension-name contracts, and `IProblemMapper<TFailure>` or a similarly narrow definition-provider seam for application failures.
- [ ] Invoke one DI enrichment/representation policy through the existing Problem Details integration. Authentication, antiforgery, JSON, empty-status and application mappings use it rather than rebuilding dictionaries.
- [ ] Preserve `IAuthenticationErrorWriter` as the authentication adapter and route it to the shared representation. Keep optional global exception-feature activation independent of basic auth/JSON viability.
- [ ] Register native `IExceptionHandler` implementations for precise exceptional types; leave ordinary domain denials as typed outcomes. Unknown defects retain safe 500 handling. Remove broad argument-exception-to-400 conventions.
- [ ] Choose one canonical correlation contract with a migration policy for existing fields. Deliberately preserve useful redacted diagnostics, including .NET 10's handled-exception diagnostic behavior.

Acceptance: one envelope across 400/401/403/404/405/409/413/503/500 paths; handler ordering/fallback and shell DI lifetimes work; no secrets, private body or SQL leak through responses/logs; output-started and cancellation cases are honest. Do not add `IGlobalExceptionHandler<TException>` unless later evidence demonstrates useful behavior beyond native dispatch.

## F2 validated identity projection

- [ ] Export owner-specific claim-type and authentication-code constants.
- [ ] Add an immutable validated account identity and one public reader/admission seam. Place HTTP/ClaimsPrincipal adaptation outside consumer domain Core.
- [ ] Enforce exactly one authenticated identity and one nonempty validated issuer/subject pair consistently in BFF endpoints and consumer adapters.
- [ ] Canonicalize reserved projection claims when issuing tickets and verify their preservation through subsequent claim actions. Actual authority and role/scope configuration remain configuration.

Acceptance: missing/empty/duplicate claims, reserved-name collisions, multiple identities and unauthenticated identities fail consistently; legitimate OIDC/cookie flows work; two shells cannot share identity state. Resource ownership remains application policy.

## F3 configured JSON and HTTP budgets

Extend `Orbyss.Foundation.Json` and `.Json.AspNetCore`, integrating the same contract metadata with OpenAPI and supported host transport configuration.

- [ ] Add public preset/profile keys, typed selection and declarative endpoint profile requirements. Register typed reader/result adapters and validate required metadata/resolvers at actual shell activation.
- [ ] Keep runtime byte/depth values in one typed configuration source. Requirements validate supported strictness/capacity instead of each consumer repeating exact numeric checks. Metadata export can describe contracts without starting storage or application initialization.
- [ ] Enforce actual request bytes, cancellation and strict parser behavior through the existing reader. Configure server/proxy limits independently and before body reading; shell settings cannot mutate process-global server state indiscriminately.
- [ ] Add bounded response serialization that rejects before retaining more than its allowed output, with success commitment only after safe admission. Define buffering/counting/spooling ownership and no recursive overflow when writing the error.
- [ ] Separate request-admission failures from server response-contract failures: malformed/oversized client input is 400/413; invalid/oversized server output is a safe failure before headers, never a truncated 200 or mislabeled client error.
- [ ] Reuse typed choices and common contract metadata for OpenAPI. Rich application invariants remain consumer code; avoid type-name switches repeating the same wire bounds where reusable metadata can express them.

Initial consumer defaults proposed for qualification are two MiB request JSON, one MiB successful JSON response/page, 64 KiB problem response, page size 100 and maximum requested page size 500. Define them once in configuration. Count and byte caps both apply; large nested collections are separate sections. Qualify the largest single-item representation before adopting these defaults and split its nested data if required. Do not silently reduce supported geometry to satisfy a transport limit.

Acceptance: exact-cap/cap-plus-one, worst-case Unicode, streamed requests, cancellation, invalid configuration and two-shell differences are tested. Success endpoints cannot bypass declared response budgets. Response budget failures do not allocate the whole oversized output before rejection or become request 413s.

## F4 shared deadlines and PostgreSQL composition

Create a narrowly scoped execution/deadline module and PostgreSQL integration module; none exists in the inspected Foundation baseline. Final package names follow the adopted Core/implementation rules. Do not insert them into Tasks merely because they involve time, or create a generic repository/transaction framework.

- [ ] Provide monotonic deadlines, caller/expiry cancellation, remaining-time/stage caps and deterministic resource ownership using `TimeProvider`. A deliberate factory seam may own deadline creation; retries cannot reset the outer deadline.
- [ ] Provide validated operation/connection/command/lock configuration and native wait projection. Keep owner lookup budgets and operation-specific policy in the consumer.
- [ ] Register a stable datasource per shell provider generation/database policy and a nonpooled `IDbContextFactory<TContext>` against it. Connection pooling is distinct from context pooling. Require each factory unit to run inside a tracked `IShell.BeginScope` or an equivalent owned shell lease; `await using` alone does not track datasource ownership. This includes initialization, background work and evaluation-lease cleanup. Reject creation outside that ownership boundary and dispose the datasource only after those units drain.
- [ ] Replace per-operation connection-string rewrites with stage cancellation and capped command settings. Preserve cancellation-acknowledgement policy and uncertain commit semantics; cancellation does not prove rollback.
- [ ] Offer safe extraction of SQLSTATE/constraint names and optional schema expectation mechanics. Consumers supply mappings, schema/constraints and transaction contents.

Acceptance: fake-time and actual Npgsql tests cover connection/lock/command expiry, cancellation, state reset, independent contexts, stable pool/source identity and shell unload. Test drain during an active factory unit, creation failure and ownership release after cancellation. Factory-created contexts use `await using`; a mutation and its receipt reconciliation own separate units. No provider models or native options enter application Core.

## F5 collection value semantics and canonical mechanics

`FrozenSequence<T>` combines defensive copying, null-item rejection and ordered value equality. An `IReadOnlyList<T>` alone does not guarantee snapshot ownership. [ImmutableArray's equality uses underlying array identity](https://github.com/dotnet/runtime/blob/v10.0.0/src/libraries/System.Collections.Immutable/src/System/Collections/Immutable/ImmutableArray_1.Minimal.cs), so replacing it mechanically changes containing record equality.

- [ ] Qualify BCL immutable collections against actual model equality/ownership requirements. Use them directly where sufficient.
- [ ] For the repeated structural value requirement, extract only the missing behavior into a small Foundation collection Core value, provisionally `ValueSequence<T>`, with explicit accepted dependency direction. Avoid a global Common package, another collection framework or an unnecessary DI interface around an immutable value.
- [ ] Test defensive copy, ordered equality, hash consistency, empty/null policy and contained mutable values. State that collection immutability does not deep-freeze arbitrary elements; runtime GetHashCode is not a persisted digest.
- [ ] Supply JSON converter/metadata support through the JSON adapter so the collection Core has no serializer dependency. Preserve existing wire shapes and record equality on adoption.
- [ ] Extract bounded UTF-8/escaping/counting mechanics and incremental canonical hashing where reusable. Keep Workbench's schema order, normalization and algorithm versions consumer-owned.

Acceptance: historical byte/hash/replay vectors remain identical. Incremental hashing uses exactly the same canonical byte order without a whole-result byte array. A changed algorithm requires a new version; RFC 8785 is not substituted for the consumer's fixed-order canonical-v1.

## F6 candidate package and shell qualification

Build and pack the Foundation candidates, then exercise their public APIs through an independent consumer and actual managed-host shell loading. Verify dependency/descriptor closure, contract-only assemblies, registration replacement, native handlers, profiles/budgets and distinct shell settings. Contract libraries are not activated as features merely because they are packaged. Use a local candidate feed for development and retain actual test artifacts.

Completion: tests, packaged consumption and real shell behavior agree. Foundation gains no runtime dependency on Program Kit. Release publication is a later decision.

## C1 and C2 consumer migration

- [ ] Split Workbench Core, domain implementation, API and PostgreSQL implementation projects while retaining one application bundle. Move encoding and provider options out of Core. Remove the local namespace waiver, preserve vectors and prove actual feature loading.
- [ ] Adopt verified candidate packages and implement the new public mapping/contribution seams. Remove private claim parsing, duplicate problem dictionaries, repetitive profile lookup and unbounded success serialization.
- [ ] Use the shared collection only where its qualified semantics are required. Preserve wire contracts and supported old snapshots.
- [ ] Use factory-owned independent persistence units and safe diagnostics. Classify database errors by named constraint as well as SQLSTATE; strengthen important schema expectations and head/revision sequence coherence.
- [ ] Keep justified parameterized PostgreSQL SQL for upsert, deferred constraints and triggers. Ordinary queries/updates/migration structure remain EF-owned. Preserve atomicity, ownership, replay and commit uncertainty.

Completion: independent restore/build/test/package commands work, actual shell activation passes, and regression checks show no accidental identity or retained-data change. Update the consumer's accepted architecture and affected specification through its established workflow; do not overwrite historical approvals.

## C3 bounded results from construction to browser

Paging is an end-to-end change, not a wrapper around the current aggregate.

- [ ] Replace the enormous-response assumption with small descriptors and independently paged parts, blockages, dimensions, text and spacing sections. Page centres/gaps/suppressed positions within a band; one band is not assumed to fit.
- [ ] Eliminate repeated large suppression arrays, whole-result canonical buffers, copied wire graphs and giant text alternatives. Qualify finite aggregate work/memory/storage budgets with real supported cases and stream bounded sections when counts are large.
- [ ] For unsaved evaluation, use an owner-bound immutable expiring snapshot lease with bounded store/quota/cleanup ownership. Atomically reserve quota, build bounded sections, seal coherent counts/canonical identity/page manifest, then publish its descriptor. Cancellation or storage failure cleans up partial construction and cannot expose an incomplete lease as ready. The recommended backend is the existing PostgreSQL provider for coherent follow-up requests across hosts. Saving remains the only operation creating a business revision/acknowledgement. Expiry retains the draft and gives an explicit unavailable outcome.
- [ ] Saved-result pages pin project/frame/revision/result identities for the whole traversal. Every read checks owner and parent membership; a cursor is never authorization. Build immutable section indexes/pages once; page reads do not load and parse the entire old snapshot again.
- [ ] Preserve old retained text and canonical digests. Backfill or stream legacy projections without rewriting old identity. Version new storage/protocol representations separately and test upgrade/restart.
- [ ] Specify a versioned delivery manifest/proof root with its own identity, pinned to the immutable result and section/order. Verify page contents against that authenticated manifest; a page carrying a result ID and its own digest does not prove membership in the canonical result. Preserve canonical-v1 through server streaming/hash conformance and complete incremental client verification where required. Qualify a supported incremental client hasher or explicit delivery-proof protocol; do not concatenate all pages for WebCrypto, silently remove existing verification or describe partial delivery verification as completed canonical verification.
- [ ] Render and navigate bounded browser pages with accessible text alternatives, stale-generation cancellation and coherent part identities. Do not reconstruct the giant graph in client memory.

The protocol design must settle lease expiry/quota/cleanup, cursor protection, page ordering and digest coverage before implementing routes. Use native platform cryptography/protection rather than custom cryptographic primitives. Server and browser conformance tests must prove that pages cannot mix revisions, cross owners, omit/duplicate declared content or imply complete results before required content is available. Altering a page and recomputing its page digest must still fail against the pinned manifest. Test concurrent evaluations competing for one owner's quota, interrupted construction, cleanup racing readers and expiry between page requests.

Completion: each response obeys configured count/byte limits; traversals remain consistent while the head changes; largest admitted scenarios stay bounded through calculation, hashing, storage and rendering. Failures preserve draft/retry identities. User-reviewed output agrees across drawing, text and cut list.

## PK2 qualification and the small consumer trial

PK2A adds an explicitly selected development candidate profile/evidence entry and verifies generated pins against the local candidate feed. Keep the shipped qualified public default unchanged. Local F6 package/host evidence is development qualification, not proof that packages or images are publicly available.

PK2B promotes the new public profile/default only after separately authorized Foundation publication and the actual immutable availability, restore, host-image and package/activation closure gates pass. Add new immutable evidence and update the selecting index/catalog at that point. Do not rewrite a historical qualified profile or bulk-replace catalog version strings: the catalog uses qualified profile overlays. Add a named exact-version compatibility recipe instead of changing existing Foundation version guards to accept anything. An optional development trial can use PK2A without promoting an unpublished default.

Update examples and targeted tests for public identity/problem/JSON contracts, split assemblies, context factories and bounded pages. The reusable specimen is one private Notes context with create/read/rename, expected revisions, exact replay and a paged list. Large synthetic fixture data can exercise byte bounds without introducing another business domain.

Build a deterministic independent consumer/oracle first. It must exercise candidate public packages through the host and real PostgreSQL, and reject seeded violations: merged roles, missing bindings, private claim parsing, response-profile bypass, shared concurrent context, broad programming-error-to-400 mapping and inconsistent error envelopes. Human review assesses responsibility ownership and unnecessary abstraction.

For an eventual full agent workflow trial, add explicit versioned Notes fixtures and scenario-bound oracle support. Existing v2 feature-stage code is tied to knowledge-application/lending cases; do not run Notes through that oracle or rewrite historical fixtures. Review code at bootstrap, specification, plan/tasks, setup and delivery checkpoints.

Use [development trial preparation](C:/Users/tech_/Code/program-kit/tests/live/v2/trial_candidate.py) and the existing one-use authorization chain if the user requests paid execution. Each paid phase binds its exact candidate, model and parent checkpoint; this plan starts none.

## Validation and completion

For each changed behavior, write the relevant contract/negative tests, observe the intended failure, implement and refactor with passing checks. Run relevant targeted checks per change, then the bounded Program Kit Development suite for integrated tranches. Useful existing targets include architecture recipe/placement, normal development, standalone engineering, phase obligations, dependency profiles/default profile, building blocks, public component/Core compatibility and bootstrap provider/proof-plan validators. Add meaningful behavior and negative cases rather than tests that only repeat implementation.

Foundation validation covers native handler ordering, identity admission, cross-package problems, strict JSON/size/cancellation, collection semantics, deadline/provider lifetimes and packaged shell consumption. Consumer validation covers compiled boundaries, real PostgreSQL failure/atomicity/replay behavior, retained data and actual API/browser page conformance.

Local browser validation uses Chromium/WebKit; Firefox remains in CI because of the known Windows host limitation. Complete Program Kit Release is a later publication gate, run in the user's terminal under the existing instructions after the candidate is selected for publication. Preserve valid evidence and never manufacture a new receipt for changed source.

Final acceptance requires the resulting code, effective configuration, public surfaces, generated API, migration path and validation artifacts to be reviewable. Remove obsolete duplicate helpers in the migrated scope and retain intentional compatibility adapters with an explicit purpose. The first executable tranche is BASE plus PK1 and Foundation F1/F2. Under the execution boundary amendment, C1–C3 follow publication through a separately authorized consumer specification.
