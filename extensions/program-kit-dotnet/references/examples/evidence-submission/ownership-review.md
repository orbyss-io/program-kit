# Scoped ownership review and rejected source cases

This authored contributor review is inspectable source guidance. It does not
authenticate its author or establish human product acceptance. The runnable
fixture separately builds the actual owners, checks compiled edges/bindings and
executes the application/provider/HTTP/browser contracts. Structural checks cannot
decide every domain responsibility from a namespace, graph label or passing test.

The positive source is this exact subtree: `Core/EvidencePacket.cs` owns valid
immutable input; `Runtime/EvidenceSubmissions.cs` admits the actor and retained
identity; `Api/EvidenceEndpoint.cs` maps HTTP through `IEvidenceSubmissions`;
`PostgreSql/PostgreSqlEvidenceJournal.cs` owns persistence. API, runtime and provider
reference Core; they do not reference each other's implementations. The two
capability bindings name their actual owning feature registration methods.

| Rejected change to the actual source | Observable review finding / appropriate oracle |
| --- | --- |
| Move `EvidenceRow`, `EvidenceDbContext` and `IEvidenceJournal` into one `Workbench` project, label it provider and call that its domain boundary | Mixed Core/provider ownership. The existing architecture recipe's mixed-workbench negative rejects compiled Core types in a persistence assembly; source review also examines semantic ownership that type names cannot prove. |
| Add a runtime project reference to the API project, or reference the PostgreSQL implementation from runtime | Peer implementation coupling. The existing planned/evaluated/compiled graph owner rejects these edges; interfaces in Core remain the client boundary. |
| Add EF or ASP.NET packages/types to Core and relabel its responsibilities | Transport/provider leak. Existing package and compiled-role controls reject the contradiction; labels cannot waive it. |
| Move `AdmitOwner` and `Guid.TryParseExact` into an API-local `PrepareEvidenceHelper`, then call `IEvidenceJournal` directly from the endpoint | A business decision and provider orchestration moved into transport. Even if it compiles and returns the same response, reject it in source review: admission belongs to the runtime capability and the API client depends on `IEvidenceSubmissions`. The fixture's independent application test remains necessary. No generic lexical detector is claimed. |
| Reuse that API-local helper from a different operation, or make a generic `EvidenceUtilities` own policy, HTTP mapping and SQL | Cross-operation and mixed-responsibility helper. Trace each caller/outcome and move policy to its actual owner; graph or naming checks alone cannot establish cohesion. This is a source-review negative, not a runtime failure claim. |
| Publish a `PrepareSchema` event and assume an earlier handler completed mandatory persistence setup | An independent reaction is being used as ordered workflow admission. The current lifecycle fixture instead awaits explicit Prepare/Default admission and rejects reversed ordering. Native zero-subscriber publication succeeds, so publication alone proves no required setup. Handler order must never become that guarantee. |
| Treat successful `PublishAsync(NoteSaved)` as a durable external audit, retry protocol or committed workflow | Unsupported durability claim. The actual dispatcher is awaited in-process execution; cancellation and a fault propagate and zero subscribers succeed. Its fixture observation is explicitly nondurable. A durable design requires separate accepted architecture, not another label. |
| Change the provider table mapping, scoped registration, activation validation, owner predicate, conditional SQL or middleware placement | The seven independently compiled controls must fail their actual model/lifetime/admission/query/effect/header assertions. Inspect each invalid snapshot and its restored valid source; unrelated compile/setup failure does not count as its behavioral red. |

The native lifecycle companion keeps immutable facts in its Core project and
application publication/independent observer registrations in an activatable
runtime owner. Both observers consume only facts and abstractions. It owns no
production audit store. Mandatory database preparation stays outside its events.
The unrelated read-only query deliberately selects no event seed.

`ApplicationContractChecks` substitutes a finite in-memory journal for the real
PostgreSQL adapter through the same cohesive capability. It observes invalid and
cancelled admission before any journal call, immutable prepared observations and
acceptance of the retained identity. The separate real-provider assertions prove
SQL/JSON/query/replay behavior; the substitution cannot supply that proof. These
are scoped SOLID outcomes, not a factory/interface-per-class requirement.
