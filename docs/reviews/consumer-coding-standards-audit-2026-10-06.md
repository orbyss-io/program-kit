# Consumer coding standards and architecture audit

Date: 2026-10-06. Program Kit version: 0.12.8.

De Zaaglijst has real ownership, abstraction and review problems, and Program Kit does not enforce several recorded standards strongly enough. Some of the reported examples, however, already use dependency injection or implement legitimate protocol constants. The repair should address responsibility, lifecycle and architectural ownership, while making the desired endpoint and constant conventions explicit.

This audit covers the consumer source, browser code, tests, accepted architecture, feature plan and tasks, installed guidance, current Program Kit guidance and validators, and exact Foundation 0.2.4 integration evidence. It proposes changes; it does not amend accepted decisions or coding rules.

## Scope and evidence

Program Kit HEAD was `087290b7d3fc3f6abf5b2460e94b1d3af367ec31`. Consumer HEAD was `cd11dea329416d5aeb70a1a45f620c934a2c9cee`, with existing uncommitted changes and concurrent consumer activity. Findings concern the inspected working files, not a certified clean commit or a finished feature. The source inventory contained 170 C# files, including generated EF migration code, and 28 files declaring static classes, 16 public. These counts describe the snapshot, not quality thresholds.

Three central files retained the same SHA-256 across repeated reads:

| File | SHA-256 |
| --- | --- |
| WorkbenchFeature.cs | `5ec07ecbfe3c0bad62d3250a18ff93c3c8132348d4144e6c160fe2c127dcb3bf` |
| AddFrameOperation.cs | `fb71bdcd17e2dcac29eea9240172451fdf745d60370c685d9b9e6de9f812db6e` |
| Core/CanonicalJsonWriter.cs | `6f3b94286a6f8c9d5f6451f6617b90ff3cb0435f63014c10ab0409e35f866a3b` |

Consumer files were read only. No consumer build or test run was started. Existing task-log results are historical claims, not newly reproduced acceptance. Apparent missing historical compatibility files could not be distinguished from sandbox access restrictions, so this audit makes no deletion finding about them. No live worker, Release run, publication or receipt generation was initiated.

## Findings that require correction

### One operation depends on another operation implementation

[AddFrameOperation.cs:20](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Api/Operations/AddOwnedFrame/AddFrameOperation.cs:20) calls `EvaluateOwnedWall.WallDraftWireAdmission.Type`. Frame creation depends on an evaluation slice's implementation helper to interpret frame types. The selected [vertical slicing rule:39](C:/Users/tech_/Code/program-kit/extensions/program-kit-governance/references/vertical-slicing.md:39) forbids direct access to another slice's implementation and requires an explicit owner and contract for shared behavior.

Move the shared frame-type wire vocabulary to an intentionally owned API adapter, or keep independent small mappings with parity coverage when that better preserves slice independence. Do not turn evaluation's helper into an accidental common dependency. The consumer namespace validator treats all `Api.*` types as one bucket, so it misses this edge.

### A serialization mechanism resides in pure Core

[CanonicalJsonWriter.cs:7](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Core/CanonicalJsonWriter.cs:7) exposes a mutable buffer and generic JSON operations including `Raw`, `String`, `Property`, `Array` and `Finish`. The [Core ownership rule:51](C:/Users/tech_/Code/program-kit/extensions/program-kit-governance/references/modularity-and-contracts.md:51) excludes serializers and private implementation utilities from Core. Sharing this mechanism between geometry and persistence does not make it a semantic contract.

Canonical byte ordering and hashing are legitimate application requirements. Preserve their tested meaning and place the encoding mechanism in an appropriate helper outside Core. Foundation's ordinary strict JSON reader is not automatically interchangeable with this exact canonical representation. The current checker bans selected serialization dependencies, but a manually written serializer using `System.Text.Encoding` passes that check.

### The request filter can conceal programming faults

[StrictRequestProblemFilter.cs:17](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Api/StrictRequestProblemFilter.cs:17) catches every `ArgumentException` from the entire downstream endpoint and returns an invalid-request 400. That includes unexpected exceptions from domain code, projection, or configuration; it also includes `ArgumentNullException` and `ArgumentOutOfRangeException`.

Use typed admission failures or restrict exception translation to the request-admission boundary. An unexpected application defect should reach the managed exception handler. Add a negative test that deliberately throws an unexpected argument exception downstream and verifies that it is not reported as caller input failure. This is more useful than merely checking whether an endpoint is static.

### Persistence failures lose useful diagnostics

[CreateOwnedProject.cs:68](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Projectopslag/CreateOwnedProject.cs:68), [AddOwnedFrame.cs:75](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Projectopslag/AddOwnedFrame.cs:75) and [InitialReceiptReconciliation.cs:31](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Projectopslag/InitialReceiptReconciliation.cs:31) convert provider faults, timeouts and cancellation to application outcomes without recording an application diagnostic. Meanwhile [WorkbenchFeature.cs:36](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Composition/WorkbenchFeature.cs:36) disables the entire EF logging category, including its error level.

Preventing SQL and private input exposure is correct, but suppressing the whole category and swallowing faults leaves the operator little information to distinguish availability failures, cancellation and programming problems. Add safe structured application diagnostics with correlation and a bounded outcome classification. Keep credentials, SQL and private input out of them. Preserve the deliberate distinction between definite failure and ambiguous commit.

Cancellation is currently grouped with faults in these catches. Distinguish request cancellation from an expired storage budget and from uncertain commit. Before commit, caller cancellation should retain explicit cancellation semantics unless an owned contract intentionally defines another outcome. After commit begins, cancellation cannot prove rollback. Query operations currently propagate failures while mutation operations translate them, so the API mapping also needs a consistent, deliberate policy.

### Fallible resource loading occurs in a constructor

[WorkbenchPageAdapter.cs:21](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Composition/WorkbenchPageAdapter.cs:21) opens embedded resource streams, reads HTML, copies assets and checks the resource inventory during construction. Resources are disposed and bounded, which is good, but construction also becomes a fallible initialization phase. The [engineering profile:80](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/references/dotnet-engineering.md:80) separates constructor invariants from I/O and resource acquisition.

Load and validate assets through an owned factory or activation initializer and inject the admitted immutable asset inventory. If small embedded-resource initialization is to be an allowed exception, record its narrow rationale and verify missing-resource and partial-initialization behavior. No exception was identified in the inspected plan.

### Several implementation helpers are public

[CanonicalEncoder.cs:10](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Frameregels/CanonicalEncoder.cs:10), [StrictRequestAdmission.cs:8](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Api/StrictRequestAdmission.cs:8), [WallDraftWireAdmission.cs:6](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Api/Operations/EvaluateOwnedWall/WallDraftWireAdmission.cs:6) and shared problem/outcome mapping types expose implementation details as public package surfaces. The [guardrails:48](C:/Users/tech_/Code/program-kit/extensions/program-kit-governance/references/programming-guardrails.md:48) default implementation-only helpers to `internal`.

Review the exported surface and identify intentional contracts versus helpers. Tests calling a helper do not alone justify publishing it. Because `InternalsVisibleTo` is forbidden by the selected profile, test behavior through owned public capabilities or a deliberately designed contract. Some public DTOs and feature types are necessary for runtime or metadata use; do not make every non-Core type internal mechanically.

## Foundation responsibilities and API gaps

### Trusted identity uses private provider claim names

The two strings in [StrictRequestAdmission.cs:11](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Api/StrictRequestAdmission.cs:11) are claim type identifiers. They are not the issuer URL. The exact preserved [Foundation BFF source:194](C:/Users/tech_/Code/dezaaglijst/docs/architecture/compatibility/foundation-0.2.4/publisher-source/src/Orbyss.Foundation.Authentication.BffCookie/FoundationBffCookieFeature.cs:194) copies token-validated `iss` and `sub` into their values. Actual authority is configured in [shells.json:29](C:/Users/tech_/Code/dezaaglijst/runtime/de-zaaglijst/shells.json:29).

Making these claim names configurable issuer settings would break the protocol. The problem is that Foundation 0.2.4 keeps the names private and exposes no public typed validated-identity contract. The consumer therefore duplicates a private, version-sensitive provider convention.

Isolate this dependency in a narrow identity adapter with owner-specific claim constants and exact-version tests. Prefer a public Foundation identity projection contract in a future provider change. Keep identity projection separate from JSON request reading: `StrictRequestAdmission` currently has two unrelated reasons to change.

### Problem Details is reused but adaptation is inconsistent

Foundation Problem Details is enabled in [shells.json:12](C:/Users/tech_/Code/dezaaglijst/runtime/de-zaaglijst/shells.json:12). [WorkbenchProblemMapping.cs:40](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Api/WorkbenchProblemMapping.cs:40) calls `Results.Problem`, which uses the registered `IProblemDetailsService` before its fallback serialization. This is supported by the [ASP.NET implementation](https://github.com/dotnet/aspnetcore/blob/v10.0.0/src/Http/Http.Results/src/ProblemHttpResult.cs). Consumer-specific revision conflicts and save uncertainty still require consumer-owned semantic mapping.

The [browser contract:19](C:/Users/tech_/Code/dezaaglijst/specs/002-wall-cut-list/contracts/browser-api.md:19) promises `code`, `correlationId` and `fieldErrors`; line 9 requires Dutch error text. Consumer-generated problems supply these extensions and Dutch titles, while managed authentication, antiforgery and default exception/status paths supply provider `code` and `traceId` and default titles. Those earlier middleware paths do not pass through the consumer endpoint filter.

Existing [private boundary tests:23](C:/Users/tech_/Code/dezaaglijst/tests/Contracts/PrivateBoundaryTests.cs:23) primarily assert statuses and privacy headers rather than the promised common envelope and localization. The contract should either explicitly distinguish these envelopes or provide one safe customization that covers all promised paths. Verify anonymous, forbidden, invalid identity, CSRF, malformed JSON, domain denial, storage failure and unexpected exception responses.

Foundation JSON middleware already translates `JsonProfileException`; [StrictRequestProblemFilter.cs:13](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Api/StrictRequestProblemFilter.cs:13) intercepts it first to add localization and field association. This may be a legitimate extension, but its responsibility and interaction with managed Problem Details need an explicit design and tests. Do not replace the selected parser, authentication flow or response-header owner.

Pinned provider evidence matters: Foundation web/authentication/JSON components are 0.2.4, associated with source commit `ab22740d9bc86f01d3220751182cdcfcef9104ef`. The inspected ProblemDetails and Json.AspNetCore feature sources were independently matched to their cached 0.2.4 descriptor hashes. Current sibling repository HEAD was not treated as equivalent to the pinned release.

### Endpoint organization is only partly followed

The [current .NET profile:172](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/references/technology-profiles/dotnet.md:172) already prescribes operation folders containing their mapping, actual request/response, validation and mapping types. Exact `Endpoint.cs` and `Request.cs` names and constructor-injected endpoint classes are not specified.

The consumer has operation folders, but actual route registration and metadata live in [WorkbenchEndpoints.cs:15](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Api/WorkbenchEndpoints.cs:15), `ReadOwnedProject` also contains `ListProjectsOperation`, and add-frame accesses evaluation's helper. Co-location and operation ownership need tightening. The central composer should assemble operation registrations, while each operation owns its route and endpoint-specific metadata.

Current route declarations advertise success responses without equivalent problem metadata. API contract generation and several related tasks remain unfinished, including [T040](C:/Users/tech_/Code/dezaaglijst/specs/002-wall-cut-list/tasks.md:80), so this is a present implementation gap, not evidence that completed feature acceptance certified an incomplete contract.

## Additional design and client risks

| Finding | Evidence and consequence | Assessment |
| --- | --- | --- |
| An authorization abstraction has no production caller | [OwnedWorkAuthorization.cs:7](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Core/Toegang/OwnedWorkAuthorization.cs:7) is tested, while production archive decisions appear separately in evaluation and frame creation. | No authorization bypass was established. Use one authoritative policy at the correct state/transaction boundary, or remove the redundant policy. Tests of an unused policy cannot prove production authorization. |
| Public result records permit contradictory states | [WallResult.cs:14](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Core/Frameregels/WallResult.cs:14) permits independently changing state, parts, blockages and stock status; [WallEvaluation.cs:7](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Core/Frameregels/WallEvaluation.cs:7) does not establish input/result coherence. | Current result construction is coherent and serialization checks some invariants. This is a public contract weakness for replacement implementations, not demonstrated corrupted HTTP output. Consider validated variants/factories and capability contract tests. |
| Shared protocol constants are repeated | `add-frame`, `create-project`, `strict-request` and `wall-cut-list-v1` recur across endpoints, storage digest/receipt logic, composition and client code. See [WallResultBuilder.cs:19](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Frameregels/WallResultBuilder.cs:19). | These are legitimate code-lifecycle constants, but ownership and reuse are unclear. Use cohesive owner-specific constants and generate cross-language contracts where practical. Preserve existing bytes and versions. |
| Browser success JSON is asserted rather than admitted | [http.ts:25](C:/Users/tech_/Code/dezaaglijst/web/workbench/http.ts:25) casts arbitrary JSON to generic `T`; [model.ts:4](C:/Users/tech_/Code/dezaaglijst/web/workbench/model.ts:4) duplicates known shapes and treats many closed choices as unrestricted strings. | Canonical physical output has extra validation, but project and presentation envelopes lack equivalent admission. Use generated known shapes and explicit runtime validation at the boundary; tolerate supported optional response fields. |
| Client operations lack cancellation ownership | [http.ts:6](C:/Users/tech_/Code/dezaaglijst/web/workbench/http.ts:6) has no `AbortSignal`; [app.ts:49](C:/Users/tech_/Code/dezaaglijst/web/workbench/app.ts:49) retains a global busy flag until a request settles. | Define bounded request and navigation cancellation and keep save uncertainty distinct from rollback. Do not duplicate timeout values already owned by configuration. |
| Mutation retry identity is not retained by the current UI | [app.ts:64](C:/Users/tech_/Code/dezaaglijst/web/workbench/app.ts:64) and line 72 generate IDs inside each submit action. The error path retains no request packet for receipt reconciliation or exact replay. | An uncertain successful creation followed by resubmission can become a distinct mutation. The browser contract requires retaining operation identity; later delivery tasks remain open, so this is a required upcoming correction rather than a claimed completed acceptance failure. |

## What the original examples actually establish

The `new WallDraftAdmission().Admit(...)` pair is in [WallAdmissionTests.cs:21](C:/Users/tech_/Code/dezaaglijst/tests/Domain/WallAdmissionTests.cs:21). Direct construction of a stateless subject under unit test is legitimate. Production [EvaluateWallOperation.cs:15](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Api/Operations/EvaluateOwnedWall/EvaluateWallOperation.cs:15) receives `IWallDraftAdmission`, `IWallEvaluation` and `IWallResultProjection`, registered at [WorkbenchFeature.cs:48](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Composition/WorkbenchFeature.cs:48). Add a composition test when the subject is DI wiring; making every unit test depend on the container would obscure the test's purpose.

Static Minimal API handlers also receive registered services through parameter injection. `AddFrameOperation` already uses `IOwnedProjectQuery` and `IOwnedFrameCreation`. [Microsoft's handler binding documentation](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/minimal-apis/parameter-binding?view=aspnetcore-10.0) confirms this mechanism. The recorded [guardrails:48](C:/Users/tech_/Code/program-kit/extensions/program-kit-governance/references/programming-guardrails.md:48) explicitly allow pure deterministic static transformations. Static methods do not alone prove a DIP or SOLID failure.

Runtime operations here do not construct `WorkbenchDbContext`. [WorkbenchFeature.cs:52](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Composition/WorkbenchFeature.cs:52) registers `AddDbContext`; storage providers receive the scoped context, clock and typed budgets through constructors. The production `new WorkbenchDbContext` occurs in the EF design-time factory. Its purpose differs from runtime `IDbContextFactory`.

The [persistence baseline:81](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/references/persistence-profiles.md:81) explicitly selects scoped contexts for request/unit of work and forbids concurrent use. It does not specify runtime factory requirements. [Microsoft's EF guidance](https://learn.microsoft.com/en-us/ef/core/dbcontext-configuration/) supports scoped request contexts and factories when the desired unit of work does not match the service scope or multiple independent units are needed. Factory-created contexts require caller-owned disposal. A factory convention needs to be added explicitly, with actual CShells lifetime verification; it should not inadvertently capture scoped configuration in a longer-lived factory.

## Project separation and SOLID

There is one production project and separate test/tool projects. A rule that every source folder must become a project does not exist. Wandinvoer, Frameregels, Werkdocumenten, Projectopslag and Toegang are currently capabilities inside one accepted context, not demonstrated independent bounded contexts.

Program Kit's [.NET topology:48](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/references/technology-profiles/dotnet.md:48) defaults to separate semantic Core, implementation, API and provider projects. The consumer [Accepted runtime decision:11](C:/Users/tech_/Code/dezaaglijst/docs/architecture/decisions/runtime-composition.md:11) deliberately chooses one Workbench project and semantic namespace boundaries. This is an accepted departure from the default rather than an unexplained implementation shortcut.

The rationale conflates projects/assemblies with packages, activated features and deployments. Avoiding six deployable features does not establish that Core, HTTP adaptation and PostgreSQL mechanisms should share one compilation boundary. Reconsider this exception against the intended maintainability and ownership constraints. Separate projects can share a deployment bundle, but the chosen assembly/package loading scheme must be verified against Foundation's actual loader.

| Principle | Assessment |
| --- | --- |
| SRP | Pure admission/evaluation/projection and storage ownership are useful separations. Identity plus JSON admission, broad exception classification, and encoding in Core weaken them. |
| OCP | Owned interfaces provide extension seams. A peer operation helper and private provider identity convention create brittle change points. An interface for every helper would not solve those ownership problems. |
| LSP | No broad inheritance abuse was found. Public result invariants and replacement capability contracts need stronger tests; interface implementation alone does not establish substitutability. |
| ISP | Existing semantic query/creation/evaluation capabilities are generally cohesive. A generic repository or one interface per method would erode the recorded design. |
| DIP | Production endpoints depend on owned interfaces, and storage implementation depends on EF appropriately. Domain Core should remain free of encoding mechanisms; private pure algorithms need no container dependency. |

SOLID is partly applied. Neither a static-class count nor green analyzers establish full compliance.

## Why the phases permit these outcomes

The [installed hook chain:156](C:/Users/tech_/Code/program-kit/extensions/program-kit-governance/extension.yml:156) projects knowledge before implementation and runs architecture checking afterward. Planning/tasks also receive guidance. The chain exists; its name overstates what some steps can prove.

[implementation_preflight.py:13](C:/Users/tech_/Code/program-kit/extensions/program-kit-governance/scripts/implementation_preflight.py:13) prints applicable guidance and succeeds. [phase-obligations.json:41](C:/Users/tech_/Code/program-kit/extensions/program-kit-governance/references/phase-obligations.json:41) classifies implementation quality as behavioral review with no direct semantic coverage and explicitly limits toolkit tests to routing/recipe claims. The verification path delegates to native repository checks. It cannot establish that a source review actually considered every relevant responsibility or that an unused policy is the production policy.

The generic [repository architecture verifier:30](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/templates/dotnet/files/eng/repository_architecture.py:30) assigns one role per project. Core purity depends on the project being declared Core. Its [binding loop:117](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/templates/dotnet/files/eng/repository_architecture.py:117) proves a listed implementation implements the listed capability and a registration method exists. It does not prove that method registers the service correctly, chooses the right lifetime or resolves it. An empty binding list still reports the structural binding case as successful.

A read-only synthetic call to that actual verifier accepted one provider-role assembly containing Core/domain, API and EF types with an empty binding list. This proves a structural blind spot, not an end-to-end consumer acceptance result.

The consumer improves on the template with [compiled namespace checks:28](C:/Users/tech_/Code/dezaaglijst/eng/architecture_rules.py:28) covering Core dependencies, foreign implementation/store access, API-to-Core boundaries, provider confinement and unauthorized inheritance. Therefore it is inaccurate to say the consumer has no architecture enforcement. Nevertheless, direct read-only synthetic calls to its actual `namespace_violations` function produced:

```json
{
  "cross_operation_api_helper": [],
  "manual_serializer_in_core": []
}
```

The modeled edges were AddOwnedFrame to EvaluateOwnedWall's API helper and a Core JSON writer to ordinary BCL encoding types. Both escaped enforcement for the same reasons as the inspected source. These probes used in-memory metadata and did not compile or edit consumer code.

Several expectations are also genuinely missing: exact endpoint/type naming and constructor-based endpoint convention, mandatory placement of lifecycle constants in owner-specific Constants classes, conditional runtime DbContextFactory rules, a worked Foundation Problem Details adaptation, and an explicit relationship between project separation and feature/package/deployment count.

## Proposed standards and enforcement repair

1. Define operation ownership concretely: `Operations/<Operation>/Endpoint.cs`, its real `Request.cs`, `Response.cs` where needed, and local admission/mapping types. Resolve endpoint instances per request with explicit constructor dependencies; use the existing Core capability interfaces for business behavior. The composition root assembles registrations. Do not capture scoped endpoint instances during application startup.
2. Define constants by owner. Prefer exported framework constants; keep lifecycle-bound protocol/schema/route values in cohesive owner-specific constants classes. Put environmental values in typed validated configuration and localizable presentation text in owned resources. Avoid a solution-wide Constants dependency sink. Generate cross-language contracts or verify their parity.
3. Define runtime context creation. A single sequential request unit may use an injected scoped context. Independent units, parallel operations or long-lived consumers use an appropriately scoped/configured factory with cancellation and `await using`. If this project selects factories for all storage operations, record that stricter choice explicitly. Keep a transaction on one owned context and verify actual shell lifetimes.
4. Make default physical boundaries explicit and require a concrete rationale plus effective checks for combining roles. Preserve the distinction between one deployment and multiple compilation boundaries. Test mixed-role assemblies and serialization mechanisms, rather than relying on library prefixes alone.
5. Add negative cases for cross-operation implementation references, omitted capability bindings, registration methods that register nothing or the wrong service, captive scoped dependencies, public implementation helpers and provider/transport leaks. Add real DI resolution and behavioral substitution tests where needed.
6. Make ordinary source review address changed responsibilities, dependency direction, public surface, constants/configuration, lifetimes, faults/cancellation and Foundation reuse with source references. Record dispositions in normal task or delivery output. Do not reinstate a separate hash-bound dossier lifecycle or require another human ceremony for routine coding.
7. Verify application and managed failure envelopes together. Keep domain outcome mapping consumer-owned and transport mechanisms Foundation-owned. Exercise unexpected defects, not just malformed user input.

## Proposed small consumer trial

Use a disposable private notes application with one context and a first specification: an authenticated owner can create a named note, read it, and rename it with an expected revision. A foreign owner gets an equivalent not-found response. Duplicate operation IDs with identical content replay the original acknowledgement; different content conflicts. A timeout or ambiguous commit preserves the operation identity and never invents success or rollback. No geometry, frontend framework, events, outbox or unrelated feature is needed.

Select and review the convention before trial execution: separate `Notes.Core`, owned implementation/composition, `Notes.Api` and `Notes.PostgreSql` projects; operation folders with instance endpoints; typed contracts and outcomes; owner-specific constants; actual Foundation auth/JSON/Problem Details; explicit context lifetimes. A command followed by independent receipt reconciliation can meaningfully exercise context factory ownership without adding an artificial interface per helper.

| Phase | Reviewable result |
| --- | --- |
| Bootstrap and constitution | Installed candidate, selected mechanisms, explicit architecture and coding conventions, genuine unresolved provider prerequisites. |
| Specify and clarify | Small owner-private create/read/rename behavior and success/failure acceptance scenarios. Coding conventions remain in the engineering baseline. |
| Plan | Exact dependency graph, public capability contracts, endpoint layout, service and context lifetimes, common error envelope and test design. |
| Tasks and analyze | Complete slices, tests before behavior, no technical-layer delivery plan, all applicable coding rules assigned to verification. |
| Implement | Working API and real PostgreSQL behavior with inspectable source, DI resolution, disposal/cancellation, atomicity and replay tests. |
| Review | Human review of actual code and generated contracts alongside deterministic architecture, format/analyzer, integration and negative-case results. |

The trial oracle should reject deliberately seeded bad examples for cross-slice helper access, Core serialization, a context shared concurrently, direct runtime context construction outside the selected policy, incorrect DI lifetime, swallowed programming exceptions, private-provider claim parsing outside the adapter, and inconsistent managed/application Problem Details. Valid pure deterministic statics and direct construction in focused unit tests should remain accepted unless the reviewed project convention deliberately changes those choices.

The existing lifecycle fixture catalog includes PriceCalculator and forms cases, not this notes case. A new reviewed fixture and source-quality oracle are required; selecting an unrelated fixture is not equivalent to running this test. Preserve the generated consumer so the user can review code after each meaningful phase.

For a paid learning trial before release preparation, use the existing [development trial receipt mechanism](C:/Users/tech_/Code/program-kit/tests/live/v2/trial_candidate.py) and the exact one-use phase manifests issued through [New-LiveAcceptanceAuthorization.ps1](C:/Users/tech_/Code/program-kit/scripts/New-LiveAcceptanceAuthorization.ps1). Each segment binds its reviewed candidate, model, sandbox and checkpoint and stops at real human gates. The initial investigation does not authorize automated workers or unseen phase decisions. Development trial evidence does not replace the publication Release gate.

The next useful work is to implement the targeted standards and negative-case repairs, then prepare this small fixture. A trial of unchanged guidance would reproduce permissive decisions without establishing that the desired conventions were enforced.
