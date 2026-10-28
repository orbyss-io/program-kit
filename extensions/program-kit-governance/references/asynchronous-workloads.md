# Replaceable asynchronous workloads

## Recognize the problem

<!-- program-kit:knowledge-rule principle.replaceable-async-workload -->
When a journey queues work, processes background jobs, or needs replaceable execution providers,
research the execution boundary before embedding the first provider in shared contracts. Separate
durable coordination, isolated execution and input/result exchange. Agree required semantics,
environment composition and failure behavior; compare credible alternatives against those needs.
Use this reference's source map for focused primary-source research. Docker in Development does
not select Production, define business completion, or justify Docker identities in Core. Read exact
selected-version facts before applying current documentation. Record decisions and unresolved
limitations in ordinary research/plan/ADR documents; no new workflow, receipt or eligibility gate.
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:knowledge-rule context.async-workload-research -->
This is Program Kit's integration reasoning, not a copy of platform manuals or a qualification of
the platforms below. Consult the relevant source only when it can answer a current design question.
Research begins in intake when consequential; deepen the selected vertical journey during planning.
A completed document or routed reference does not establish that an agent applied the reasoning.

## Three responsibilities

| Responsibility | Owns | Does not establish |
| --- | --- | --- |
| Coordination | Authoritative work state, authorization, admission, atomic dispatch intent, attempts, deadlines, reconciliation, result acceptance | A broker acknowledgement is not execution or business completion |
| Execution | Starting/observing/stopping bounded work or running a continuous worker; resource isolation | A process exit is not validated business success; a container is not automatically a security sandbox |
| Exchange | Authorized input snapshots, bounded result publication, integrity, retention and erasure | A mount, blob URL or queue payload is not the business contract |

The application owns processing meaning. A provider owns how it implements execution/exchange.
One provider may implement both capabilities, but they need separate contracts when audience,
security, consistency or replacement lifecycle differs. Avoid a generic infrastructure framework or
one interface per method. Queue consumers are a delivery/execution pattern, not an isolation tier.

## Research source map

Sources inspected 2026-10-25. Recheck the relevant platform/version, region, plan and limits when
making a deployment decision. These links are discovery inputs, not selected consumer dependencies.

| Candidate/source | Consult for | Integration consequence and unresolved proof |
| --- | --- | --- |
| [App Service/WebJobs](https://learn.microsoft.com/en-us/azure/app-service/overview-webjobs), [App Service settings](https://learn.microsoft.com/en-us/azure/app-service/configure-common) | Existing App Service hosting; continuous, scheduled or triggered background work; Always On and runtime restrictions | Shares the App Service hosting/scaling context. Assess resource contention and required per-run isolation separately. Verify the exact OS/image/plan; this is not a general Docker engine endpoint. |
| [Container Apps apps/jobs](https://learn.microsoft.com/en-us/azure/container-apps/jobs) | Continuous queue workers versus manual, scheduled or event-driven run-to-completion containers; retries, replica timeout, parallelism and stop APIs | Event scaling creates demand-based executions, not an application transaction. The worker must acquire work. App replicas, job replicas and business attempts differ. Persist authoritative history outside bounded platform history. |
| [Kubernetes Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/), [Pod termination](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination) | Cluster-owned isolated jobs, retry/backoff, deadlines, duplicate starts, termination | Jobs can start the same program twice. Preserve the application's original deadline across replacements/suspension. Termination and deletion need observed outcomes; assess node partitions, permissions and security isolation. |
| [Competing consumers](https://learn.microsoft.com/en-us/azure/architecture/patterns/competing-consumers), [Service Bus settlement](https://learn.microsoft.com/en-us/azure/service-bus-messaging/message-transfers-locks-settlement) | Continuous workers, redelivery, locks, acknowledgements and poison messages | Queue delivery does not choose per-run isolation. Lock expiry or failed settlement can redeliver completed work. Deduplicate acceptance and fence effects; do not promise exactly-once processing. |
| [Transactional outbox](https://learn.microsoft.com/en-us/azure/architecture/databases/guide/transactional-out-box-cosmos) | Durable dispatch intent recorded with application state | Apply the atomicity principle to the selected store's real transaction boundary. This Cosmos example does not qualify another database or broker. |
| [Asynchronous request/reply](https://learn.microsoft.com/en-us/azure/architecture/patterns/asynchronous-request-reply), [Valet key](https://learn.microsoft.com/en-us/azure/architecture/patterns/valet-key) | Admission/status APIs, correlated results, scoped artifact access | Keep URLs/tokens transport-private, bounded and secret. Revocation and erasure depend on actual storage/credential semantics; expiry alone is not immediate revocation. |
| [Kubernetes finished-job cleanup](https://kubernetes.io/docs/concepts/workloads/controllers/ttlafterfinished/) | Platform object/Pod retention | Job TTL is not proof that external artifacts, backups or logs were erased. |

For each applicable option, compare coordination ownership, worker trust/isolation, payload size,
duration, concurrency, cancellation strength, data locality, identity, operational cost and exit path.
State rejected options and why. Do not research every platform on every feature, or reselect an
accepted provider merely because current documentation describes a newer version.

## Semantic replacement contract

Use a domain name such as `BatchProcessing.Core`, not a solution-wide infrastructure Core.
Core publishes immutable work/input/result identities and cohesive execution/exchange capabilities.
It references no cloud SDK, Docker model, broker message, filesystem mount or provider database entity.
Provider-private storage maps an application attempt to its platform identities and reconciliation
state. Do not pass arbitrary provider dictionaries through Core as an escape hatch.

Capture exact provider identity, implementation version, semantic contract version and scope
(environment plus tenant/security boundary) for both execution and exchange when admitting work.
Resolve compatible bindings explicitly; equal contract versions alone do not establish compatible
transport, identity or security. Require an admitted pair with documented exchange interoperability.
Resolve older runs against their captured bindings, not today's defaults. An operator must drain,
migrate with explicit semantics, or retain reconciliation/cleanup support before retiring a provider.

The optional .NET example under `program-kit-dotnet/references/examples/async-workload/` illustrates
the small SDK-free contract and deterministic behavior. Its in-memory recording providers are not
Docker/cloud implementations, durable storage, production security or platform qualification.

## Explicit environment composition

Development Docker is explicit opt-in for Development. Staging, Test and Production select their
own supported bindings; no name other than Development implicitly permits development privileges.
Exclude development packages, their transitive dependencies/activations, test fixtures and Docker
engine/socket privileges from every non-Development bundle. A disabled root feature is insufficient
if another feature activates it transitively or its package remains in the deployed closure.

Compare declared roots against the actual resolved package closure, native feature activation and
deployment mounts/privileges. Reject missing, ambiguous, wrong-version, wrong-scope and incompatible
bindings before submitting work. Outages and unresolved bindings never cause automatic Docker
fallback. A configuration setting cannot grant environment isolation by itself.

The optional `provider_composition.py --input <repository-relative-json>` operation
checks a finite explicit environment closure using `provider_composition.validate_provider_composition`.
The example README describes the input. It performs no provisioning, execution or secret lookup.
Supplied observations establish only their own consistency; independently obtain exact package,
native activation and deployment privilege observations for the environment being qualified.
The existing typed composition model's global feature selection alone does not supply this proof.

For .NET retain the published digest-pinned Orbyss.Foundation.Host, CShells/Nuplane selection and
the effective profile's managed OpenAPI exporter. Providers are features/application bundles, not
replacement application hosts. Resolve the selected profile before consulting package knowledge.
Missing device tools require detection and a human-run preparation script; declared project package
restores remain ordinary agent operations. Do not install device tools or create cloud resources.

## Failure and conformance questions

| Scenario | Required design and meaningful test |
| --- | --- |
| Durable admission/dispatch | Commit work and dispatch intent atomically in the owning store. Crash after commit and before/after submission; reconcile/retry without losing intent. An in-memory fixture proves ordering only, not crash durability. |
| Ambiguous submission | Lost acknowledgement means unknown, not definitely failed. Use stable submission identity and provider lookup/deduplication; retain unknown until reconciled. Do not blindly create another execution or switch providers. |
| Duplicate delivery/starts | Deduplicate logical dispatch/result acceptance, fence current authorized attempts, and make effects idempotent where possible. Broker duplicate detection alone is insufficient. |
| Authorization and fencing | Bind tenant, work revision and attempt/generation. Reject stale or unauthorized input access, effect publication and result acceptance at the resource that performs them. A coordinator-only token check cannot fence an external side effect. |
| Original deadlines | Store absolute deadlines at admission. Retries, queue delay, restarts and provider changes do not reset them. Bound delegated grants by the same deadline. Test late delivery and clock assumptions. |
| Cancellation and stop | Record cancellation intent separately from stop requested, stop confirmed and outcome unknown. Reject late publication immediately; retain cleanup responsibility until execution and external effects are reconciled. |
| Deletion | Fence new reads/writes and late-result resurrection. Account for in-flight grants, provider storage, retained versions, logs/backups and applicable retention. Pending/unknown erasure is not completed erasure. |
| Cleanup | Keep an idempotent, retryable cleanup obligation with the original binding. Already absent may succeed; outage, missing provider or uncertain stop does not. Do not erase reconciliation identities prematurely. |
| Outage/recovery | Preserve pending and unknown state, bounded retry/backoff and original deadline. Distinguish control-plane observation failure from execution failure. Never silently fail over to Docker. |
| Provider retirement | Stop new admissions, inventory active/unknown/cleanup runs, drain or explicitly migrate, retain required versions/identity access, verify deletion and only then retire. Test an older bound run after defaults change. |

## Proof and maintenance

Workflow conformance tests exercise the application's contract with deterministic recording providers,
including negative cases. Compiled architecture tests establish SDK-free Core and dependency edges.
Composition checks establish consistency with the supplied resolved closure and configuration.
None establishes a real platform's durable dispatch, security isolation, stop/erase guarantees or
operational availability. Qualify each actual provider/version/scope combination with deployment,
identity, network/storage, outage/duplicate/partition and cleanup evidence before claiming support.
Adding a qualified provider should leave business/API/processing rules unchanged; infrastructure,
identity, configuration and qualification still change. Do not claim universal interchangeability.

When a new consumer problem exposes a reusable gap, preserve the reported observation, inspect the
actual decision path, and distinguish guidance, discoverability, tooling and runtime causes. Add the
smallest reusable decision rule/source map/example and focused regression. Link external detail,
retain selected-version facts needed by tooling, and keep consumer decisions in consumer documents.
Use existing repair intake and maintainer review; no agent polling, automatic knowledge promotion or
claim that one consumer plan correction repaired upstream. Report implemented, tested, released and
consumer-confirmed status separately.
<!-- /program-kit:knowledge-rule -->
