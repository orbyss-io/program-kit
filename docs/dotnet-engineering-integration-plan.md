# .NET engineering knowledge integration plan

Status: engineering proposal accepted by the user, 2026-09-13. The persistence recommendations in
`persistence-selection-audit-2026-09-13.md` are also accepted. The combined refactor and GitHub
issue scope were subsequently approved. Implementation and deterministic integration are recorded
in `knowledge-refactor-evidence-2026-09-13.md`; fresh paid consumer acceptance remains pending.
The issue review below preserves the decision basis. No GitHub issue state was changed.

## Evidence and completeness boundary

The original task **Research .NET profile improvements**, ID
`01a03e52-4b07-79a1-978c-1a36564f65d5`, was located and read. Its original request is retained at
`C:/Users/Joeyb/.codex/attachments/5a68e786-75e5-40c8-bfe4-f07f4b62461a/pasted-text.txt`.
Its later method-body/style request was also inspected. Historical runtime and distribution
choices are superseded where they conflict with the current published Foundation host plus
consumer configuration/Nuplane/package bundle contract.

The original request explicitly included Lazy<T>, HttpClient lifetime, Interlocked, volatile,
PeriodicTimer/TimeProvider, advanced locks, pooling, SafeHandle/GC, detailed LINQ semantics,
default(T), equality/copying/boxing, and static-constructor failure. Several have no explicit
treatment in the current engineering reference. We must reconcile the original request item
by item, rather than declaring the shortened profile complete.

GitHub read on 2026-09-13: [Program Kit #17](https://github.com/orbyss-io/program-kit/issues/17)
(typed boundaries/SOLID/testability/constants) remains open;
[Foundation #2](https://github.com/orbyss-io/dotnet-foundation/issues/2) (typed JSON) is closed.
The [coordination issue #20](https://github.com/orbyss-io/program-kit/issues/20) also remains open.
Issue closure, local implementation, published availability and consumer adoption are separate
claims. Preserve and verify the delivered Foundation mechanisms rather than implementing another
JSON/security/host layer in consumer features.

Completeness means every original requested topic, applicable issue acceptance criterion and
current normative rule has a recorded disposition and proof route. It cannot mean enumerating
every present or future .NET API or proving all security properties with static analysis.

## One owner for each kind of knowledge

Keep normative text in the existing authorities:

| Authority | Owns |
| --- | --- |
| governance/references/programming-guardrails.md | Technology-neutral typed boundaries, SOLID, dependency/testability and constant ownership |
| governance/references/software-language.md | Domain policies, transitions, effects, admissions and outcomes |
| governance/references/modularity-and-contracts.md | Core/provider boundaries, extension contracts, allowed dependencies and compatibility |
| governance/references/vertical-slicing.md | Operation ownership and complete slice delivery |
| dotnet/references/dotnet-engineering.md | C#/.NET async, synchronization, types, initialization, lifetime, queries and runtime primitives |
| dotnet/references/technology-profiles/dotnet.md | .NET applicability, project/operation placement, composition and pointers to narrower authorities |
| dotnet/references/persistence-profiles.md | EF/provider adoption, transaction/concurrency/migration and real-database evidence |
| dotnet/references/secure-web-profiles.md and web-security-evidence.json | Existing WEB controls, defaults, threat treatment and verification identities |
| building-blocks references/catalog and Foundation public contracts | Supported JSON, response policies, hosted assets, tasks and other component mechanisms |
| dotnet/references/dotnet-runtime-and-application-bundles.md | Published-host compatibility, activation, release bundle and runtime ownership |

Paths in this table are relative to `extensions/program-kit-<owner>/`.
The plan is contributor review material, not another consumer instruction source.
Strengthen an existing section where one exists. New rules get one owning section and stable
identity. Extend the existing phase-obligation metadata with rule references, applicability,
proof kind, diagnostic/check identity and source revision; generated briefs resolve that text.
Do not copy the complete rule into intake, plan, implementation and delivery instructions.
Derive or validate knowledge-inventory routing against this same mapping so it cannot advertise
coverage independently of the executing gate. Preserve existing WEB and domain identities.

## Coverage to retain and complete

| Family | Already retained | Proposed completion / consideration | Proof |
| --- | --- | --- | --- |
| Typed boundaries | Typed information after admission, pure Core, named domain outcomes | Known envelopes use DTOs/approved converters; represent valid variants; align schema/parser/runtime behavior; internal helpers; cohesive constants; bounded dynamic JSON exceptions | Analyzer where sound, schema/behavior negatives, semantic review |
| SOLID and design | SOLID/cohesion, semantic interfaces, composition-only DI, no interface-per-method default | Assess each principle against concrete responsibilities, clients, substitutions and extension points; preserve pure static transformations | Attributed design and implementation review; substitution/architecture tests where applicable |
| Async | Task default, measured ValueTask, no hidden work, cancellation | Direct Task return versus await and disposal/exception scope; I/O versus CPU; Task.Run/ThreadPool starvation; WhenAll observation; IAsyncEnumerable cancellation; continuation/context semantics | Compiler/analyzers, cancellation/fault tests, measured exceptions |
| Concurrency | lock/System.Threading.Lock, SemaphoreSlim, concurrent collections, bounded channels | Interlocked, volatile limits, lock ordering, no uncontrolled external calls under locks, mutable singleton safety, channel completion/full modes, measured advanced locks | Analyzer where sound, deterministic coordination and bounded stress tests |
| Types and construction | class/record/struct guidance, immutability, constructor invariants, primary constructors | default(T), shallow versus deep immutability, equality/hash/boxing/copying, public inheritance contracts, partial construction cleanup, static initialization failures, Lazy<T> | Review, value/contract tests, measurements when optimization motivates a choice |
| Lifetime and memory | IDisposable/IAsyncDisposable, DI ownership, bounds, Span/Memory, retention and unload | Captive dependencies and actual shell scopes, cancellation-registration lifetime, HttpClient, ArrayPool/IMemoryOwner/Pipelines, SafeHandle, pinning/LOH/GC caution | Scope/disposal tests, analyzers, targeted retention tests |
| LINQ and persistence queries | Deferred execution, multiple enumeration, IQueryable translation, projections, PLINQ | Any/Count/First/Single according to meaning, deterministic ordering, safe named helpers at query boundaries, pagination/N+1, no automatic loop rewrite | Analyzer plus real-provider queries; semantic review |
| Time, configuration and I/O | General controlled time/I/O and typed options | Explicit TimeProvider/FakeTimeProvider, PeriodicTimer and monotonic elapsed time; validated options and reload lifetime; appropriate IFileProvider; HttpClient lifetime, deadlines and retry safety | Fake-time/fault tests plus real shell/HTTP integration |
| Secure data and runtime use | Existing WEB controls, managed JSON/assets, no secrets, package/runtime boundaries | String comparison/culture/Unicode at protocol boundaries; bounded parsing/regex/archive input; allowlisted polymorphism; path/URL/process boundaries; cryptographic API use; safe logs | Existing security evidence plus targeted negative tests and applicable SDK security diagnostics |
| Observability and errors | Structured logs, correlation, metrics/traces, explicit outcomes | Cancellation versus faults, stack preservation, no swallowed failures; ActivitySource/Meter and logging mechanisms; cardinality and data disclosure limits | Fault-path assertions, emitted evidence review, security tests |
| Performance options | Conditional ValueTask/PLINQ/structs/frozen collections and no speculation | Pooling, source generation, cached reflection/delegates, Span/Memory and specialized locks only when applicable; trimming/AOT only when a selected deployment requires it | Measurements and actual deployment compatibility where selected |
| Host and component lifecycle | Foundation.Tasks, activation, drain/disposal, immutable bundle | Prove actual task registration and feature use; distinguish per-process scheduling from distributed ownership; unload tests only for live-reload scope | Published-host composition tests and owned lifecycle tests |
| Source/style | Coherent method phases, extraction, one type/file, helper ordering, XML docs, field naming, Policy B | Verify actual analyzer IDs/severities and documented limitations; retain proportional guidance and generated-code exceptions | Compiler/formatter fixtures plus review for meaning |

Unmanaged interop, unsafe code, lock-free algorithms, custom schedulers, runtime code generation,
distributed locking and live reload remain conditional specializations. Their occurrence must
trigger a scoped compatibility/security investigation; absence requires no boilerplate design.
This closes known coverage gaps without requiring every consumer to use every framework class.

## Typed objects and SOLID: required review questions

Use the existing implementation-quality obligation, enriched with concrete checks from #17:

- SRP: identify unrelated reasons to change; separate filesystem/configuration/transport from
  policy where that boundary improves ownership. A file-count threshold is not evidence.
- OCP: use supported named policies and owned extension points; do not copy Foundation behavior
  or add speculative plugin abstractions.
- LSP: implementations preserve their published preconditions, outcomes and invariants. Static
  methods alone do not establish a violation. Test replacement where a substitution is promised.
- ISP: interfaces group cohesive capabilities required by real consumers. Avoid mandatory
  one-interface-per-method decomposition.
- DIP: domain behavior depends on owned semantic capabilities; supply replaceable time,
  environment and I/O using appropriate existing abstractions. Keep private implementation
  seams private; do not move every helper interface into Core.
- Known data is typed after admission. Dynamic JSON remains valid for genuinely dynamic schemas
  or lexical/canonical processing, encapsulated and bounded. Typed DTOs alone do not prove
  authorization, validation, deep immutability or safe serialization.
- Reuse framework constants or cohesive owner-scoped values; preserve wire/version semantics.
  Pure deterministic helpers may remain static and implementation-only helpers default internal.

Require findings tied to changed code and relevant behavior; a generic "SOLID passed" checkbox
does not satisfy the review. Automated checks establish only the properties they actually test.

## Lazy<T> decision

Include a conditional section in the existing construction/lifetime guidance. Use Lazy<T> for
genuinely deferred, reusable initialization whose cost and lifecycle justify it. Required startup
validation stays explicit. Define factory exception behavior, thread-safety mode, value lifetime
and disposal. ExecutionAndPublication coordinates initialization; it does not make the produced
object thread-safe. PublicationOnly can execute multiple factories, so side effects and losing
disposable values need deliberate ownership. Do not present it as an automatic retry solution.
Lazy<Task<T>> needs an explicit shared-failure/cancellation policy: caching a faulted or cancelled
task can retain that result. Do not invent a universal AsyncLazy framework or hide sync-over-async.
Use the already selected Foundation task/startup mechanism where initialization is required.

[Microsoft Lazy<T>](https://learn.microsoft.com/en-us/dotnet/api/system.lazy-1?view=net-10.0)
supports the initialization, exception and object-safety distinctions; the adoption and lifecycle
rules above are the proposed Program Kit interpretation.

## Apply knowledge when it is needed

| Phase | Required action |
| --- | --- |
| Intake | Capture business outcomes and exceptions; inherit ordinary engineering defaults without interviewing the user about Task versus ValueTask or SOLID |
| Assessment/research | Select existing mechanisms and exact compatible versions; research only unresolved gaps or overrides |
| Architecture/closure | Assign owners, trust boundaries, extension points, data stores and lifetimes; close compatibility prerequisites at the existing gate |
| Specify | State observable behavior, concurrency/replay/failure requirements; avoid embedding an API catalog |
| Plan | Project applicable rule sections; record design/proof ownership and conditional decisions once |
| Tasks | Derive implementation and verification work from those obligations; no manually repeated checklists |
| Implementation | Present relevant sections before affected source work; run compiler/analyzer and targeted behavioral checks as code changes |
| Delivery | Bind current source, rule versions, tool configuration, review and executed proof; require all applicable blocking obligations |
| Upgrade | Use the shared coordinator; preserve consumer-owned changes, show rule/profile differences and renew affected proof; no automatic data migration or global cleanup refactor |

Trigger applicability from accepted intent and declared capabilities before source exists, and
reconcile it with source/project changes later. Source scanning alone can miss aliases or absent
required behavior. Unsupported/unclassified relevant uses must receive a review disposition.
Retain the existing implementation-quality/domain/.NET obligations; specialize their rule groups
instead of running a parallel quality pipeline. Missing evidence or a removed verifier must not
silently make an obligation inapplicable.

## Implementation sequence and acceptance

### GitHub issue scope review

The live GitHub open-issues collection was checked on 2026-09-13: exactly five open issues,
#16 through #20. The collection also contains dependency PR #8, which is not an issue and is
not part of this design review. Include all five issues in the improvement run, with the
following distinct dispositions. Existing work is retained and verified, not restarted.

| Issue | Disposition and completion evidence |
| --- | --- |
| [#16 selected mechanisms](https://github.com/orbyss-io/program-kit/issues/16) | Core scope, partly implemented already through component-adoption.md, capability_adoption.py and phase obligations. Complete intent-to-selection-to-actual-mechanism proof using real Forms/JSON/web/asset paths; fail a selected-but-bypassed mechanism and keep future management deferred. |
| [#17 typed boundaries/SOLID](https://github.com/orbyss-io/program-kit/issues/17) | Already in the accepted engineering plan. Bind every concrete issue acceptance criterion to design and implementation proof, including legitimate exceptions. |
| [#18 operation layout/thin composition](https://github.com/orbyss-io/program-kit/issues/18) | Explicit work package. Strengthen the existing Minimal API/vertical-slicing guidance and ownership checks. Plan and generate operation-owned endpoint/request/response/validation/mapping paths where needed; IWebShellFeature composes routes and registrations. Verify actual responsibility separation, multi-operation discoverability, mirrored tests, small-operation exceptions and unchanged wire/schema identity after refactoring. No mandatory mediator or extra layers. |
| [#19 API evolution](https://github.com/orbyss-io/program-kit/issues/19) | Explicit work package. Strengthen the current OpenAPI/API-contract obligation with typed DTO/parser/schema parity, old-client and stored-snapshot compatibility, strict-request/tolerant-response behavior, version/deprecation decisions and canonical identity preservation. Retain exporter/oasdiff/client generation and authority over baselines. Prove V1-to-V2 evolution in a small deterministic fixture; do not invent V2 in the lending slice. |
| [#20 coordination/consumer hold](https://github.com/orbyss-io/program-kit/issues/20) | Delivery checklist rather than another implementation layer. Track every dependency, component release, adoption proof and migration procedure. Keep the historical consumer unchanged and paused; no automatic resume follows issue closure or a release. |

Foundation/Forms issue resolutions are dependency inputs to #16/#19/#20. Verify published versions
and exact supported mechanisms in the combined consumer; do not reopen resolved producer work
unless a concrete integration defect is demonstrated. No issue is complete solely because it
appears in this plan, its package is referenced, or a prose review says it passed.

**API Evolve is identifiable.** The [Spec Kit community catalog](https://github.com/github/spec-kit/blob/main/extensions/catalog.community.json)
lists [Quratulain-bilal/spec-kit-api-evolve](https://github.com/Quratulain-bilal/spec-kit-api-evolve),
v1.0.0, MIT, as an unverified community entry. Its README and extension manifest advertise
contract detection, snapshots, classification, deprecation, versioning and five lifecycle hooks.
This corrects the earlier issue's unresolved tool identity; it does not establish compatible or
deterministic execution with the installed Spec Kit.

Evaluate it within #19 with an explicit adopt/adapt/reject decision before changing the installed
research trigger. Its after-plan snapshots, task edits, gate and release/version actions overlap
Program Kit's current baseline authority, hash-bound task analysis and release boundaries. Test
hook compatibility and actual implementation, baseline provenance, stale/missing proof, generated
contracts, semantic limits and token/reading overhead in a disposable deterministic setup. Do not
install it automatically, give it independent baseline authority, or let it tag/bump releases as
a side effect of feature execution. If it adds value, integrate through the existing coordinator
and evidence contract; otherwise retain the existing tools and record why.

[Asp.Versioning](https://github.com/dotnet/aspnet-api-versioning) is a separate runtime routing/version
negotiation candidate when multiple supported API versions require it. API Evolve, runtime version
routing, oasdiff and semantic compatibility tests solve different parts of #19. No single one
establishes the complete compatibility contract. Extra GraphQL/gRPC support is outside this .NET
HTTP trial unless a real capability requirement introduces it.

1. **Reconcile knowledge.** Produce a topic-by-topic map of the recovered original request,
   current references and issues. Every item is retained, strengthened, superseded with reason,
   conditional, or explicitly deferred. Resolve contradictions in existing text, including the
   stale consumer-image sentence. Keep product defaults distinct from ecosystem guidance.
2. **Repair the enforcement connection.** Extend current rule metadata and phase projection,
   preserve IDs, bind relevant source sections, and ensure source/knowledge changes invalidate
   affected review. One compact applicable brief replaces repeated full-document reading.
3. **Prove tool coverage.** Verify the shipped Foundation analyzer package, fix PK/ORB mismatch,
   choose SDK diagnostics per rule (including CA2012/CA2016 where appropriate), test severity,
   suppression and generated-code behavior. Use custom analyzers only for a demonstrated gap;
   analyzer runtime changes belong in Foundation with published compatibility evidence.
4. **Build meaningful positive and negative fixtures.** Include the actual #17 design failures,
   DTO/schema mismatch, invalid ValueTask usage, dropped cancellation, unsafe shared state,
   semaphore release failure, Lazy factory/fault/lifetime cases, partial startup and disposal,
   query translation/concurrency and insecure input cases. Every relevant gate must reject its
   bad fixture for the intended reason and accept legitimate static/dynamic/simple alternatives.
   Runtime race tests use controlled scheduling/barriers and bounded tests, not sleep-based luck.
5. **Integrate accepted persistence and fixture infrastructure.** Exercise selection through
   real activation, EF/provider behavior and shared upgrade sync. Add owned database service
   setup/connection/cleanup without changing the independent business oracle or Foundation image.
6. **Validate installed paths, then prepare the new paid trial.** Targeted checks and Development
   validation cover fresh installs, implementation and upgrade, including rule-version changes
   and consumer exceptions. Prepare exact fresh evidence; the user separately commences/authorizes
   intake + bootstrap + first vertical slice. An old receipt cannot cover changed shipped sources.

Do not overload the fictional lending feature with every BCL mechanism just to exercise coverage.
Small deterministic consumers cover specialized rules; the live slice tests natural combined use.
Measure tokens (cached separately), unnecessary reading/retries, missed obligations, false-positive
findings, source rework and time spent on useful versus avoidable work. More checklists are not
an improvement unless coverage and consumer efficiency improve together.

## Research basis for additional coverage

Primary sources checked 2026-09-13. Examples must be compiled against the selected SDK and packages
before rules claim a supported API; current documentation is not permission to change managed pins.

- [DI guidance](https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/guidelines):
  scope/disposal ownership, captive dependencies and service thread safety support lifetime tests.
- [Options](https://learn.microsoft.com/en-us/dotnet/core/extensions/options): typed configuration and
  validation; validate actual CShells activation rather than assuming root-host startup hooks apply.
- [TimeProvider](https://learn.microsoft.com/en-us/dotnet/standard/datetime/timeprovider-overview):
  use the framework time seam for controlled timing and tests.
- [HttpClient](https://learn.microsoft.com/en-us/dotnet/fundamentals/networking/http/httpclient-guidelines):
  use a supported lifetime/DNS strategy; factory-created clients and long-lived clients with
  configured pooled connection lifetime are alternatives, not a universal factory mandate.
- [Channels](https://learn.microsoft.com/en-us/dotnet/core/extensions/channels): bounded capacity,
  full-mode behavior and completion need explicit producer/consumer semantics.
- [Memory ownership](https://learn.microsoft.com/en-us/dotnet/standard/memory-and-spans/memory-t-usage-guidelines):
  keep owners, consumers and leases explicit when memory crosses API/async boundaries.
- [String comparisons](https://learn.microsoft.com/en-us/dotnet/standard/base-types/best-practices-strings)
  and [regex](https://learn.microsoft.com/en-us/dotnet/standard/base-types/best-practices-regex):
  explicit protocol comparison semantics and bounded handling of untrusted inputs.
- [Security diagnostics](https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/quality-rules/security-warnings):
  select rules for the actual runtime/API surface; not every listed legacy rule applies.
- [CA2012](https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/quality-rules/ca2012)
  and [CA2016](https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/quality-rules/ca2016):
  concrete examples of existing analyzers to verify before building new ones.

No instruction says every feature must use Lazy, ValueTask, records, pooling, channels, a broker
or a new abstraction. Applicability and soundness are the acceptance criteria.
