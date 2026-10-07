# Foundation contracts and modular architecture audit

Date: 2026-10-06. Second analysis of De Zaaglijst and Program Kit 0.12.8.

The one-project Workbench decision should have failed review against the intended modular architecture. Core responsibilities are still recorded, but permissive wording and weakened structural checks allowed a consumer-specific namespace exception to replace compilation boundaries. Foundation also lacks some reusable public contracts, while the consumer overlooks several extension points that already exist. The repair needs stronger project invariants, small typed Foundation contributions and shared conformance tests.

This supplements the [first audit](C:/Users/tech_/Code/program-kit/docs/reviews/consumer-coding-standards-audit-2026-10-06.md). Consumer HEAD at this round was `c0071b5c36b500753e3f9fd4f7d49d5b21a6902e`; concurrent work and existing inaccessible historical evidence remain separate. Foundation dependency analysis used cached exact 0.2.4 source commit `ab22740d9bc86f01d3220751182cdcfcef9104ef`. The sibling Foundation checkout is older, at `30db6759e75bc53f7cc457e19c5a9d77297b9e71`, and was not assumed to represent that release. No consumer or Foundation files, builds, databases or live workers were changed or started.

## The architecture decision should have been rejected

Program Kit's [ADR 0006](C:/Users/tech_/Code/program-kit/docs/decisions/0006-semantic-core-and-runtime-implementation-topology.md) established the semantic Core and activatable implementation topology on 2026-09-03. [Current Core guidance:43](C:/Users/tech_/Code/program-kit/extensions/program-kit-governance/references/modularity-and-contracts.md:43) still includes models, value objects, invariants, pure domain services, public capability seams and small dependency-light semantic utilities. Git blame attributes these provisions to `8393e9c924289280c300fd7a2697c699789c9cd0`; the knowledge was not deleted.

The [.NET profile:80](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/references/technology-profiles/dotnet.md:80) separates semantic Core from domain-named implementations, API adapters and provider projects. Its phrase “default solution graph” and generic proportional exceptions made that separation easier to reinterpret than intended.

The consumer [runtime ADR:13](C:/Users/tech_/Code/dezaaglijst/docs/architecture/decisions/runtime-composition.md:13) says namespaces should remain until independent packaging is demonstrated, and line 21 cites activation/compatibility complexity. That does not establish why models, HTTP adaptation and EF implementation should share one compiler boundary. One bounded context and one deployment do not require one assembly. Conversely, each semantic folder does not require its own context or deployment.

The consumer then modified its copied architecture verifier to allow:

```python
project.get('persistenceOwnerNamespaces') == ['DeZaaglijst.Workbench.Projectopslag']
```

as an alternative to a provider/test project at [repository_architecture.py:72](C:/Users/tech_/Code/dezaaglijst/eng/repository_architecture.py:72), and as an alternative to the required provider project at line 160. Consumer commit `f838306428a5e15d0e01fbd219f88a3a37a82f5f` introduced that exception on 2026-10-05. The main project is declared `composition`, so this specific declaration permits EF in the combined assembly. Namespace negative tests add useful checks, but cannot restore a waived compilation boundary.

There is also a concrete enforcement omission after Program Kit's 2026-10-05 workflow simplification, commit `6a388ab4932cbd8a4744780896d71361673d281b`. The older [binding validation:483](C:/Users/tech_/Code/program-kit/extensions/program-kit-governance/scripts/artifact_ownership.py:483) requires the capability project to be Core and the implementation project to have an allowed implementation/provider/bridge role. The maintained [engineering binding loop:117](C:/Users/tech_/Code/program-kit/extensions/program-kit-dotnet/templates/dotnet/files/eng/repository_architecture.py:117) checks compiled interface implementation and registration-method presence without carrying those role constraints forward. Both sides can therefore name the same composition project.

Restore those invariants in ordinary planning and engineering checks. A feature ADR or consumer checker customization must not waive the adopted separation merely by relabeling a project. Intentional changes to the baseline should be explicit changes to that baseline. This does not require restoring extra review dossiers or adding a new approval ceremony to ordinary coding.

## The intended Core model

| Project | Responsibilities |
| --- | --- |
| `{Domain}.Core` | Business models, values, errors, invariant-preserving construction/equality, stable pure semantic policies/utilities, public capability and contribution interfaces. |
| `{Domain}` | Replaceable domain behavior and orchestration; its activation adapter registers implementations through the applicable shell feature contract. |
| `{Domain}.Api` | Operation endpoints, wire contracts, admission and HTTP mapping; its web/middleware activation adapter integrates them with Foundation. |
| `{Domain}.PostgreSql` | EF persistence entities, mappings, contexts, migrations, queries, provider-specific SQL and implementations of Core-owned storage capabilities. |

Only activation adapters implement the appropriate `IShellFeature`, `IWebShellFeature` or `IMiddlewareShellFeature`; individual business services implement their semantic interfaces. Ordinary implementation projects reference Core rather than peer implementations. Bundle composition selects implementations into one runtime without collapsing their projects.

“Stable” means deliberately compatible, versioned evolution. Core can contain concrete value constructors and pure utilities; it is not restricted to empty interfaces and records. [UnicodeText](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Core/UnicodeText.cs) and [Micrometres](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Core/Micrometres.cs) fit this model. A mutable general JSON encoder does not.

A further Core responsibility leak is [ProjectStorageBudgets.cs:9](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Core/Projectopslag/ProjectStorageBudgets.cs:9). Its public contract includes native connection, command, row/metadata lock and identity-resolution budgets. Those belong to provider-owned validated configuration or its deliberate registration seam. Sharing the type with composition does not make these mechanisms domain semantics. BCL-only dependency checks cannot detect this ownership error.

The current generic guidance [permits ORM mapping of persistence-ignorant Core POCOs:89](C:/Users/tech_/Code/program-kit/extensions/program-kit-governance/references/modularity-and-contracts.md:89). The user's provider-only persistence entity convention is stricter and should replace that exception explicitly. De Zaaglijst already uses separate internal EF records; its failure is the combined assembly, not EF annotations on Core models.

## Foundation mechanisms and missing contracts

The proposals below name possible interfaces; they are not claims that those APIs exist today. Prefer small contracts backed by one implementation and conformance suite. An interface by itself does not prove safe identity admission, consistent errors or bounded serialization.

### Identity projection

Foundation 0.2.4 privately owns the validated issuer/subject claim names in [BffCookie source:30](C:/Users/tech_/Code/dezaaglijst/docs/architecture/compatibility/foundation-0.2.4/publisher-source/src/Orbyss.Foundation.Authentication.BffCookie/FoundationBffCookieFeature.cs:30), creates their values at line 194 and reads them in `/bff/user`. The consumer repeats those names and its own admission in [StrictRequestAdmission.cs:11](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Api/StrictRequestAdmission.cs:11).

The two implementations disagree: consumer admission requires exactly one authenticated identity and exactly one nonempty validated claim pair; `/bff/user` uses first-claim lookup across the principal. Consolidate the stronger rule in Foundation. Do not weaken consumer admission to match permissive lookup.

Add public owner-specific claim constants, an immutable validated account projection and an `IValidatedAccountIdentityReader` seam with one tested implementation. A framework-free projection value can live in an Authentication Core contract package; a ClaimsPrincipal/HTTP-facing reader belongs to the authentication adapter. Consumers only translate that validated projection into their own account identity. Their database owner mapping and resource authorization remain consumer-owned.

The issuer URL remains typed configuration. Claim names are code-lifecycle protocol constants. Test duplicate/reserved claim collisions, multiple identities, missing values and untrusted input at ticket creation and projection. No exploit is claimed from static inspection, but differing cardinality rules and appending reserved claims require explicit admission semantics.

### Problem Details

Foundation already exposes [IAuthenticationErrorWriter](C:/Users/tech_/Code/Orbyss/dotnet-foundation/src/Orbyss.Foundation.Authentication/IAuthenticationErrorWriter.cs) and registers its default through `TryAdd`. Authentication and antiforgery call it. The consumer does not implement it, so its localized problem mapper cannot affect those earlier managed errors.

Standard ASP.NET `IProblemDetailsService`, `IProblemDetailsWriter` and `ProblemDetailsOptions` also exist. [Microsoft documents these extension points](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/error-handling-api?view=aspnetcore-10.0). Current consumer `Results.Problem` already uses the registered service. A separate generic writer that merely wraps it would add little.

The genuine Foundation gap is a shared typed problem definition and contribution policy. Its ProblemDetails, authentication and JSON packages each build code/trace dictionaries and interpret failures separately, while the consumer adds correlation/field dictionaries and localized titles. The ProblemDetails feature assigns an opaque customization delegate directly rather than invoking a stable DI contribution contract.

Add a validated `ProblemDefinition` and `IProblemMapper<TFailure>` or equivalent contributor seam. Consumers map their typed failures to safe definitions; Foundation owns standardized extensions, correlation, localization enrichment and HTTP writing through the existing ASP.NET service. A small Core package can own framework-light definition/mapping contracts; the existing `Orbyss.Foundation.Web.ProblemDetails` runtime implements them. Authentication and JSON should contribute to the same representation, while retaining optional feature activation.

Publish extension-name and generic error-code constants. Select one canonical correlation contract instead of independently maintaining `traceId` and `correlationId`. Provide a DI policy contribution invoked by the existing customization delegate, including at framework-generated errors. Preserve reserved fields and fail safely for invalid or conflicting mappings.

Today, the consumer can implement `IAuthenticationErrorWriter` and compose safe `ProblemDetailsOptions` customization without a Foundation release. It must preserve the provider's existing customization behavior when composing the delegate. The future contract removes that fragile chaining requirement. Domain conflict, archive, replay and uncertain-save semantics still belong to the consumer mapper.

The conformance suite should cover auth, CSRF, JSON, empty status, business denial and unexpected exception paths. It should prove statuses, safe codes, field diagnostics, localization and correlation. Unexpected defects must retain their safe 500 handling rather than being relabeled as ordinary input failures.

### JSON profiles and configuration

Foundation already owns strict-request parsing, rejection of unknown/duplicate properties, nullable/required constructor handling, configurable byte/depth limits, and allowlisted converter/resolver registration. Exact [JsonProfile source:18](C:/Users/tech_/Code/dezaaglijst/docs/architecture/compatibility/foundation-0.2.4/publisher-source/src/Orbyss.Foundation.Json/JsonProfile.cs:18) validates profiles; line 98 counts actual stream bytes and honors cancellation.

The consumer [shell configuration:25](C:/Users/tech_/Code/dezaaglijst/runtime/de-zaaglijst/shells.json:25) selects two MiB and depth 32. [WorkbenchJsonProfileValidator.cs:11](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Composition/WorkbenchJsonProfileValidator.cs:11) repeats these values and demands exact equality; [activation tests:30](C:/Users/tech_/Code/dezaaglijst/tests/Runtime/WorkbenchActivationTests.cs:30) deliberately reject four MiB and depth 64. Thus these knobs are configured but intentionally frozen by application code. This follows the current approved contract; it is not an accidental bypass of configuration. The limitation is duplicated policy and a lack of declarative contract requirements.

Add public preset/profile keys and a small profile requirement/contribution contract. The consumer declares its known request types, strictness, supported capacity/depth range and allowed extensions once; Foundation validates actual configuration at shell activation and resolves the admitted profile. A typed request-reader seam and endpoint profile metadata would replace repetitive catalog lookup and thin static wrappers. Metadata/export composition must describe the contract without running storage or application initialization.

Keep the runtime numeric budgets in one typed configuration source. Keep non-negotiable strictness and schema promises in the contract. A deployment must not lower supported capacity or change parser semantics silently. Code-lifecycle schema identities and semantic geometry capacities remain owner-specific constants rather than arbitrary configuration.

### Response budgets and writing

Ordinary [evaluation responses:29](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Api/Operations/EvaluateOwnedWall/EvaluateWallOperation.cs:29), reads and saved acknowledgements use `Results.Ok`. Foundation Json.AspNetCore explicitly does not change global `HttpJsonOptions`; named profile settings therefore do not govern those response writes. The custom canonical encoder's bound concerns canonical result bytes, not the whole HTTP response including input and presentation fields.

Foundation offers `JsonProfile.Serialize<T>()`, but [its source:90](C:/Users/tech_/Code/dezaaglijst/docs/architecture/compatibility/foundation-0.2.4/publisher-source/src/Orbyss.Foundation.Json/JsonProfile.cs:90) allocates the full UTF-8 output before checking its byte limit. Its HTTP middleware also maps any `json_size_exceeded` exception to 413, without distinguishing oversized client input from oversized server output. Simply routing response serialization through this method would not establish allocation protection or correct error direction.

Add a Foundation profile-aware JSON result/response writer with explicit metadata and budget ownership. Enforce a finite allocation/output limit during encoding, honor cancellation and define what happens before and after headers start. Clean Problem Details on overflow require rejection before response commitment, using bounded buffering/spooling or an admitted immutable snapshot with deterministic preflight. Streaming alone cannot guarantee a replacement error after partial JSON has already been sent. Separate request and response error classifications.

The consumer [CanonicalCapacity.cs:10](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Core/CanonicalCapacity.cs:10) computes a conservative result envelope of **2,073,572,528 bytes**, approximately 1.93 GiB. The [geometry contract:11](C:/Users/tech_/Code/dezaaglijst/specs/002-wall-cut-list/contracts/geometry.md:11) explains that this intentionally overcounts combinations and does not claim maximum-size device acceptance. Foundation profiles cap at 16 MiB. This is a compatibility question that must be resolved before replacing the current response path, not proof that real responses reach 1.93 GiB.

Keep three distinct limits: versioned semantic representation capacity, configured application request/response budgets, and server/proxy transport limits. The published host also needs an explicit infrastructure configuration route for request limits; [Kestrel supports configuration and per-request body-size features](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/servers/kestrel/options?view=aspnetcore-10.0), which must be set before body reading. Shell middleware must not mutate a process-wide server limit as though it were tenant-local configuration.

### Schema and canonical encoding duplication

The new [WorkbenchSchemaTransformer.cs:19](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Api/WorkbenchSchemaTransformer.cs:19) repeats wire choices and numeric/count bounds from runtime admission using type-name and property-name switches. It implements the existing ASP.NET schema transformer interface, but that interface does not make its duplicated values agree with runtime behavior.

Use typed closed choices, owner constants and existing schema metadata where they express the contract correctly. Where richer constraints are necessary, add a Foundation contract-description/contributor seam whose descriptor drives validation and OpenAPI projection. Domain invariants still require application code and tests. Avoid a new general-purpose schema language merely to remove a few switches.

Foundation's existing canonicalizer sorts object keys according to its RFC 8785 variant. The consumer's `canonical-v1` fixes a different property order and performs product-specific set ordering. Replacing one with the other changes bytes and hashes. A reusable bounded UTF-8/escaping primitive is a plausible Foundation addition; the consumer must retain its semantic ordering/version contract, with frozen cross-language byte/hash fixtures. Existing hashes cannot be silently migrated by switching a helper.

### Other possible shared mechanisms

The consumer page adapter repeats bounded asset loading and admission, but Foundation HostedPages currently serves fixed public pages and uses `AllowAnonymous`. Its `IHostedAssetSource` is an available stream seam, not a complete private page replacement. A future private page/asset facility needs explicit authorization, metadata, antiforgery/template and resource ownership; routing private Workbench pages through the current public feature would be wrong.

PostgreSQL deadline projection, datasource/context lifetime, redacted diagnostics and schema verification are candidates for an optional provider integration package. It should supply mechanisms with typed options and consumer-owned schema expectations, not a generic repository that absorbs revision semantics. This is a proposed new capability, not an existing Foundation package.

## EF Core and PostgreSQL assessment

The present balance between EF APIs and SQL is mostly sound:

| Work | Implementation and assessment |
| --- | --- |
| Ordinary reads | Owner-filtered, no-tracking LINQ projections, selected columns and bounded ordering/paging. |
| Head compare-and-swap | `ExecuteUpdateAsync` with affected-row verification inside an explicit transaction containing the other writes. |
| Ordinary schema | EF migration-builder tables, columns, indexes and constraints. |
| PostgreSQL-specific behavior | Parameterized owner upsert, deferred cyclic initial root/revision inserts, lock settings, catalog inspection and append-only trigger SQL. |
| Migration deployment | Explicit reviewed scripts/hashes; no startup migration or EnsureCreated path. |

[Microsoft supports EF set-based updates with explicit transaction ownership](https://learn.microsoft.com/en-us/ef/core/saving/execute-insert-update-delete), [parameterized SQL alongside LINQ](https://learn.microsoft.com/en-us/ef/core/querying/sql-queries) and [reviewable migration scripts/bundles](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying). Replacing justified provider SQL with awkward EF abstractions would not improve this design.

The EF entities and configurations are internal under `Projectopslag.Persistence`, rather than exposed as Core/wire entities. Move them with contexts and migrations into the separate persistence implementation project. Public provider registration/factory seams should be intentional.

There are concrete corrections:

1. **Constraint-specific failure mapping.** [CreateOwnedProject.cs:64](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Projectopslag/CreateOwnedProject.cs:64) and [AddOwnedFrame.cs:73](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Projectopslag/AddOwnedFrame.cs:73) classify every uniqueness failure as RevisionConflict. [The design:53](C:/Users/tech_/Code/dezaaglijst/specs/002-wall-cut-list/data-model.md:53) explicitly limits that treatment to named sequence/operation races. A frame or room UUID collision needs its own outcome. Use SQLSTATE plus the expected constraint identity and add service-level negatives.
2. **Separate owned units require separate contexts.** The data model explicitly promises a fresh context for receipt reconciliation. [InitialReceiptReconciliation.cs:16](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Projectopslag/InitialReceiptReconciliation.cs:16) clears tracking and reopens the same context. This can observe a fresh READ COMMITTED result; it is not a demonstrated stale-read defect. It nevertheless diverges from the stronger design promise. `IDbContextFactory<TContext>`, cancellation and `await using` give the mutation and reconciliation independent owned lifetimes while retaining one context per atomic transaction.
3. **Readiness omits important schema invariants.** [SchemaCompatibility.cs:34](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Projectopslag/Persistence/SchemaCompatibility.cs:34) checks history, columns, one deferred FK and trigger counts. It does not establish all unique/FK definitions, owner collation or trigger events/function behavior. A changed function body or missing sequence index could escape these checks. Add declared schema expectations and targeted damage tests; no database alteration was performed for this audit.
4. **Head sequence coherence can be stronger.** [ProjectRecordConfiguration.cs:16](C:/Users/tech_/Code/dezaaglijst/src/DeZaaglijst.Workbench/Projectopslag/Persistence/ProjectRecordConfiguration.cs:16) binds the current revision without binding the duplicated head sequence to that revision's sequence. Current writes update them coherently. A deferred triple FK or equivalent explicit invariant would strengthen database protection; this is hardening rather than observed corruption.
5. **Connection/budget plumbing is repeated.** Runtime opening rewrites native connection-string timeout values per operation; different connection strings can imply different pool identities. A stable shell-owned datasource/factory with per-operation cancellation and command deadlines is clearer. Pool proliferation was not measured. Preserve actual shell disposal and commit uncertainty rather than introducing an unsafe global datasource.

Existing PostgreSQL tests exercise meaningful behavior, including ownership, replay races, atomic writes, deferred constraints, migrations and immutability. Their inspected source does not establish the missing negatives above. This round did not rerun them.

## Recommended work by owner

| Owner | First changes |
| --- | --- |
| Program Kit | Make project/role/binding separation invariant; reject consumer-specific namespace waivers; preserve pure semantic Core utilities; apply the provider-only EF entity convention; specify typed Foundation adoption and conformance checks. |
| Foundation Authentication | Public claim contract and a shared validated identity projection/admission implementation; use it internally and in consumer adapters. |
| Foundation ProblemDetails | Typed validated problem definitions/mapping contributions, public envelope constants, shared DI enrichment and cross-package conformance fixtures using ASP.NET's existing writer. |
| Foundation Json and Json.AspNetCore | Public profile keys/requirements; typed request/response integration; early finite output bounds and direction-specific failures; shared contract metadata where needed. |
| Foundation Host | Explicit host-level transport-budget configuration and supported shell endpoint integration. |
| Consumer | Implement available extension points, supply only owned semantic mappings/contracts, separate projects and provider options, correct context/failure classification and verify schema/response conformance. |

Prioritize the modularity gate and identity/problem contracts first, then JSON response/configuration integration, then optional generic asset/PostgreSQL facilities. Keep provider contracts compatible and test actual shell activation and package loading. Update Program Kit's examples, profile catalog/pins and negative tests when the public Foundation changes exist; merely adding an interface name to guidance will not remove consumer duplication.

The small consumer trial proposed in the first audit remains useful after these contracts and enforceable rules are defined. Its purpose should be to prove reusable Foundation behavior and compilation boundaries with inspectable source, not merely to show that another agent can reproduce today's permissive conventions.
