# .NET engineering profile

Apply these rules only when .NET is selected. Project-specific style remains an overlay; runtime correctness and
ownership rules are profile requirements.

## Async and shell-owned work

<!-- program-kit:decision-rule async-ownership -->
<!-- program-kit:knowledge-rule principle.async-representation -->
- `Task`/`Task<T>` is the default asynchronous representation. Use `ValueTask` only for a measured hot path
  whose consumers obey its single-consumption constraints.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.bounded-async-work -->
- `async void` is limited to event handlers. Do not use `.Result`, `.Wait()`, sync-over-async, unobserved work,
  unbounded producer queues, or unbounded fan-out.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.async-operation-policy -->
- Propagate cancellation and define timeout, retry, idempotency, fault, terminal-state, and observability policy.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.shell-owned-work -->
- `IHostedService` and `BackgroundService` are root-provider, process-global facilities. A CShells feature must
  register shell-owned work through `Orbyss.Foundation.Tasks`; the Generic Host does not start services registered in
  a shell provider.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.shell-task-lifetimes -->
- Startup tasks may be scoped. Background and recurring tasks are shell-singletons owned by the task manager.
  Shutdown is idempotent, cancels, awaits with a bound, drains before provider disposal, and has disposal fallback.
<!-- /program-kit:knowledge-rule -->
<!-- /program-kit:decision-rule -->
<!-- program-kit:knowledge-rule principle.async-completion -->
- Custom schedulers, `Task.Factory.StartNew`, invisible fire-and-forget, and runtime work without an owner require
  an Accepted ADR and measured evidence.
- Await asynchronous I/O directly. `Task.Run` does not improve server I/O scalability; CPU offload needs a
  bounded execution policy. Returning a task directly is valid only when disposal, `finally` and exception
  handling do not need to span its completion. Observe all child outcomes from `Task.WhenAll`, including
  cancellation. Async streams propagate enumeration cancellation and dispose their enumerators.
- Choose continuation behavior for the actual caller context; do not mechanically add or remove
  `ConfigureAwait`. Distinguish per-process Foundation scheduling from distributed work ownership.
<!-- /program-kit:knowledge-rule -->

## Synchronization and collections

<!-- program-kit:knowledge-rule principle.synchronization-contract -->
- Use `lock` or `System.Threading.Lock` for short synchronous critical sections. Never await while holding it.
- Use `SemaphoreSlim` for asynchronous mutual exclusion or bounded concurrency, with acquisition/release paired
  in `try/finally` after successful acquisition. It is not a universal lock and provides no fairness guarantee.
- Prefer concurrent collections only when their precise atomicity is understood. `ConcurrentDictionary`
  delegates can execute more than once and outside its internal locks; factories must tolerate that behavior.
- Prefer message passing or bounded channels when ownership transfer is clearer than shared mutable state.
- `Interlocked` supports individual atomic operations; compound invariants still need coordination.
  `volatile` does not make read-modify-write atomic. Document lock order and keep uncontrolled callbacks,
  external I/O and slow work outside critical sections. Singleton lifetime does not establish thread safety.
- A channel design defines capacity, full mode, cancellation, completion and failed-consumer behavior.
  Specialized locks and lock-free algorithms require a scoped investigation and measured justification.
<!-- /program-kit:knowledge-rule -->

## Resource and memory ownership

<!-- program-kit:decision-rule resource-ownership -->
<!-- program-kit:knowledge-rule principle.disposal-ownership -->
- The creator owns disposal unless ownership is explicitly transferred. DI disposes services it creates; do not
  manually dispose them or register pre-created disposable instances without an owner.
- For selected CShells 0.0.31, a disposable lifecycle initializer can be disposed before activation
  completes through the helper's transient alias. Use the verified
  [non-owning admission pattern](examples/cshells-initializer-ownership/README.md) when a resource
  must live for the generation: one DI owner, a separate non-disposable typed initializer, awaited
  failure/cancellation and native teardown. Preserve real scoped/transient lifetimes and cleanup.
  Do not alias the disposable owner under another DI service or bypass admission/security checks.
<!-- /program-kit:knowledge-rule -->
<!-- program-kit:knowledge-rule principle.async-teardown -->
- Use `IAsyncDisposable` when teardown performs asynchronous work. Constructors do not start background work.
<!-- /program-kit:knowledge-rule -->
<!-- /program-kit:decision-rule -->
<!-- program-kit:knowledge-rule principle.resource-retention -->
- Bound caches, queues, buffers, subscriptions, and retained task state. Static references, timers, event
  handlers, callbacks, threads, and outstanding work must not retain a drained shell generation.
- `Span<T>` is stack-only and synchronous; `Memory<T>` can cross async boundaries. Follow explicit buffer
  ownership and do not retain borrowed memory beyond the documented lifetime.
- Assembly unloading is cooperative. Live reload requires weak-reference/collection tests and proof that old
  generation tasks, statics, subscriptions, and load contexts become collectible.
- Check actual shell scopes for captive dependencies. Dispose cancellation registrations, timers and event
  subscriptions with their owner; test cancellation and partial startup, not only successful shutdown.
- With `ArrayPool`, `IMemoryOwner<T>` or pipelines, document each lease and return/disposal path, including
  failures; clear sensitive pooled data as required. Never use memory after return or across an invalid lease.
  Prefer `SafeHandle` for owned unmanaged handles. Pinning, forced GC, LOH optimizations and custom pooling
  are conditional measured choices, not ordinary application defaults.
<!-- /program-kit:knowledge-rule -->

## LINQ and query boundaries

<!-- program-kit:knowledge-rule principle.query-execution -->
- Preserve deferred-execution awareness and avoid multiple enumeration. Enable CA1851 where it adds signal.
- Keep `IQueryable<T>` expressions provider-translatable until the deliberate materialization boundary. Do not
  hide client evaluation, accidental full-table reads, or offset-pagination scaling costs.
- Avoid side effects in query operators. Materialize when a stable snapshot or repeated traversal is intended.
- PLINQ and parallel projection require measurement, bounded resource analysis, deterministic outcome semantics,
  and cancellation. Do not put unbounded async lambdas into synchronous LINQ operators.
- Use `Any`, counts, `First` and `Single` according to the contract, including empty/multiple outcomes.
  Specify stable ordering and pagination. Test projection, N+1 behavior and named helper translation on
  the real selected provider; an in-memory substitute cannot prove database semantics. Do not replace
  readable queries with loops without an actual correctness or measured performance reason.
<!-- /program-kit:knowledge-rule -->

## Type and construction choices

<!-- program-kit:knowledge-rule principle.construction-invariants -->
- Use classes for identity, mutability, inheritance, large values, and DI-owned services. Persistence entities are
  normally classes, not records.
- Use record classes for data-oriented value equality and immutable contracts. Record structs and structs must be
  small, immutable, value-oriented, and justified against copy/boxing costs.
- Prefer immutable/frozen collections for build-once read-many state when measurement or ownership clarity
  supports them. Do not expose mutable collection internals.
- Constructors validate arguments and establish invariants. They do not perform I/O, start work, acquire remote
  resources, call overridable members, or hide fallible asynchronous initialization; use factories for those.
- Primary constructors are a suggestion when dependencies and state remain clearer. Do not force them when they
  create hidden mutable captures or obscure invariants.
- Seal internal leaf types when there is no extension contract, but treat CA1852 as an opt-in repository policy.
- Review `default(T)`, equality/hash semantics and copying/boxing for value contracts. Records and `init`
  properties do not make referenced collections deeply immutable. Test promised substitution contracts.
  Factories clean up partially acquired resources; static initialization must not hide required startup
  validation or introduce unrecoverable initialization dependencies.
<!-- /program-kit:knowledge-rule -->

## Deferred initialization

<!-- program-kit:knowledge-rule principle.deferred-initialization -->
Use `Lazy<T>` only for genuinely deferred, reusable initialization with an explicit lifetime. Define the
factory's side effects, exception policy, thread-safety mode and disposal owner. `ExecutionAndPublication`
coordinates initialization and can cache factory exceptions; it does not make the value thread-safe.
`PublicationOnly` can run several factories: account for duplicate effects and losing disposable values.
It is not an automatic retry policy. `Lazy<Task<T>>` can retain faulted or cancelled tasks; define shared
failure and cancellation semantics instead of binding shared initialization to one caller's token.
Required initialization uses the selected Foundation startup mechanism. Do not invent a universal
AsyncLazy abstraction, hide synchronous blocking, or defer mandatory configuration validation.
<!-- /program-kit:knowledge-rule -->

## Time, configuration and I/O

<!-- program-kit:knowledge-rule principle.runtime-time-and-io -->
- Use `TimeProvider` for replaceable time, monotonic timestamps for elapsed duration, and controlled-time
  tests for deadlines. Use `PeriodicTimer` when its single-consumer semantics fit owned periodic work.
  Consume the selected replaceable default rather than unconditionally registering `TimeProvider.System`.
  Effect owners read UTC at their actual decision boundary after lock/I/O waits; explicit instants belong
  to meaningful caller inputs or pure policy evaluation. Preserve persisted timestamp precision and
  previously accepted replay semantics when correcting expiry checks. Test actual feature registration.
  When selected, carry Foundation's `IExecutionDeadline` into PostgreSQL units and capped stages; distinguish
  caller cancellation from `IsExpired`, and neither from postdispatch commit uncertainty.
- Bind feature settings with Microsoft Options (`AddOptions`, section `Bind`, `Validate`/`IValidateOptions<T>`).
  Per-property indexers/`GetValue` and custom readers are not options binding. Preserve keys, defaults
  and conversion semantics through owned mappings; justify and test any necessary custom conversion.
  Observe required options at actual shell activation: root `ValidateOnStart` alone is not CShells proof.
  Bind/validate before immutable domain/work snapshots. Core need not reference `IOptions<T>`; retries
  retain original values, never today's options. Define reload/snapshot lifetimes and test omission,
  nondefault and invalid configuration.
  Operational pagination default/maximum sizes are owner options, consumed consistently by API defaults,
  application admission and bounded query construction. Positive page size remains an input invariant.
  Do not turn accepted application/protocol ceilings or immutable migration identities into settings.
- Use a supported `HttpClient` lifetime/DNS strategy: factory-managed handlers or long-lived clients with
  a configured pooled connection lifetime. Define deadlines and cancellation; retry only replay-safe
  operations, accounting for effects and commit ambiguity. Use `IFileProvider` where it fits the resource
  boundary; it does not by itself establish path admission or tenant isolation.
<!-- /program-kit:knowledge-rule -->

## Secure runtime boundaries and observability

<!-- program-kit:knowledge-rule context.selected-web-runtime-specialization -->
Reuse the selected WEB controls and managed JSON/asset mechanisms in `secure-web-profiles.md`; these
rules specialize runtime use, not their identities or policy. Known envelopes become typed after
admission as defined in `programming-guardrails.md`.
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:knowledge-rule principle.runtime-security -->
- Specify ordinal/culture and normalization semantics for protocol identifiers; do not let machine culture
  change authorization, identity or persisted wire meaning. Bound untrusted parsing, regular expressions,
  archives and decompression; use timeouts or an appropriate non-backtracking regex where supported.
  Qualify the actual packaged runtime, including deferred decoding and native failure/fallback behavior.
  Managed-heap limits and working-set polling do not establish a hard total-process ceiling. State
  monitored overshoot, concurrent admission and cancellation/cleanup bounds; use OS containment when
  the application contract requires a hard process limit. Follow the untrusted-parser review in
  [programming guardrails](../../program-kit-governance/references/programming-guardrails.md).
  For consumer-owned normalized labels, use the supported
  [Core export and generated browser validator](label-validation.md). Keep operation order, character
  sets and length units source-backed; test normalization and digest parity instead of copying bounds
  into browser code or treating generated DTO types as runtime validation.
- Allowlist polymorphic input. Admit file paths, outbound URLs and process arguments at their trust
  boundary; use structured process argument APIs and protect against traversal/SSRF. Use platform
  cryptographic primitives and secure random APIs for security purposes, never custom cryptography.
- Preserve exception stacks and distinguish cancellation from faults. Use structured logging and, when
  meaningful, `ActivitySource`/`Meter`; bound cardinality and redact sensitive data. Test denied, malformed,
  oversized and fault paths, including logs, rather than relying on a successful request.
- Unsafe code, interop, runtime code generation, custom schedulers, distributed locks and live reload
  trigger scoped security/compatibility research. Source generation, reflection caches, trimming and AOT
  are conditional on measured needs and the selected deployment; verify that deployment before adoption.
<!-- /program-kit:knowledge-rule -->

## Method bodies and extraction

<!-- program-kit:knowledge-rule principle.method-coherence -->
Write a non-trivial method as one coherent operation. Use this sequence when the phases apply; do not add empty
sections, comments, temporary variables, or helper calls merely to make the shape visible:

1. Validate inputs, authorization, preconditions, and other trust-boundary assumptions. Prefer guard clauses so
   the valid path remains unindented. Do not repeat guarantees already established by the type system or caller's
   accepted contract.
2. Prepare the operation state. Compute derived values and acquire short-lived resources as close as practical to
   their first use. Keep simple expressions inline when a local name adds no meaning.
3. Perform the operation at one level of abstraction. Make state changes and external effects explicit, ordered,
   cancellable, and owned.
4. Validate the result and postconditions when the method establishes an invariant or crosses a trust boundary.
   Do not defensively re-check values that were just produced by a trusted, strongly typed operation.
5. Return the result on an explicit final line when there is a result. `void`, throwing, expression-bodied, and
   `Try...` methods naturally omit or adapt phases that do not apply.

Preparation or logic is complex enough to extract when it represents a nameable concept and any of these signals
is present:

- it mixes a lower-level algorithm, parsing, mapping, policy decision, I/O, or resource lifetime into a method
  that otherwise reads at a higher level;
- it introduces multiple branches, loops, exception paths, or intermediate values that must be understood
  together;
- it has an independent contract worth focused tests, is reused, or is likely to change for a different reason
  than the calling operation;
- its side effects, failure modes, cancellation, or ownership rules deserve a boundary of their own; or
- the caller cannot describe the prepared value with one precise local name without also explaining how it is
  built.

Cyclomatic complexity is a warning signal, not the definition: review a method at 10 and normally refactor before
it exceeds 15. Also refactor a low-branch method when it mixes abstraction levels or hides a resource boundary.
Conversely, do not extract a transparent expression or create a pass-through helper solely to reduce line count.
An extracted preparation helper returns the complete prepared value, preferably as an existing domain/value type;
do not use a tuple as an unnamed parameter bag when the values form a durable concept.

Order fields first, followed by constructors and the type's externally meaningful members. Put private helper
methods at the bottom of the type, in the order in which the higher-level flow first uses them. A private method is
not automatically justified: it must make the caller easier to read or own an independently meaningful contract.
<!-- /program-kit:knowledge-rule -->

## Source files and documentation

<!-- program-kit:knowledge-rule principle.source-file-context -->
Task context projects the actual selected `Orbyss.Foundation.Analyzers` pin and root
`.editorconfig` declarations. ORB1003 is the one-type-per-file rule. Write an interface,
request record, decision enum and failure record in four files, including support and
test types. The maintained [contract example](examples/contract-layout/) compiles against
the selected pin; `python tests/validate_contract_layout.py` also proves that combining
those valid types fails ORB1003. Nested configuration and suppressions still require
the actual native build; declared root settings alone establish no effective-policy pass.
<!-- /program-kit:knowledge-rule -->

<!-- program-kit:knowledge-rule principle.source-documentation -->
- A C# source file declares exactly one named type: class, record, struct, interface, enum, or delegate. Nested and
  supporting type declarations use their own files as well. Anonymous types and tuples are expressions and do not
  violate this rule. Generated code is excluded. Name the file after the declared type; partial declarations may
  span multiple correctly named files when the split has a concrete purpose.
- Give every declared type and member, including private members and enum values, an XML documentation comment.
  Use a concise `<summary>` that states purpose or contract, and add `<param>`, `<typeparam>`, `<returns>`,
  `<value>`, and `<exception>` only when applicable. Use `<inheritdoc />` when an inherited contract is unchanged.
- XML documentation is consumer-facing contract documentation. It does not contain design history, rejected
  alternatives, implementation diaries, or architectural justification. Put durable design decisions and their
  substantiation in Architecture/ADRs; use a short inline comment only for a locally non-obvious mechanism. Code
  that follows an accepted pattern should normally explain its mechanics through names and structure.
<!-- /program-kit:knowledge-rule -->

## Orbyss style overlay

<!-- program-kit:knowledge-rule principle.invocation-layout -->
- Private fields use camelCase without an underscore; enforce through EditorConfig naming rules and
  `dotnet_diagnostic.IDE1006.severity=error`. Naming-rule severity alone does not enforce a build.
- Put control-flow bodies below their conditions. A simple single-statement `if` may omit braces on
  the next indented line; complex/ambiguous bodies use braces. Enable SDK IDE2001 as an error with
  `EnforceCodeStyleInBuild=true` and `csharp_style_allow_embedded_statements_on_same_line_experimental=false`.
- Use a 120-column target. Methods and constructors with more than two parameters, and calls with more than
  two arguments, must put every parameter/argument on its own line after the opening parenthesis. Close on
  a separate line aligned with the indentation of the line containing the opening parenthesis. Apply the
  same layout whenever a shorter list is split across lines, including primary constructors.
- Never invoke a method inside an argument to another method or constructor. Prepare the result in a named
  local first, including awaited results. Prepare constructed argument values separately as well. Keep
  deferred factories/handlers in named methods or delegate variables rather than nesting their bodies
  inside a call's argument list. Preserve evaluation order, cancellation, disposal and deferred activation.
- In a method chain, put the receiver on its own line and every invocation on a following indented line,
  starting with the first invocation. Never leave the first call beside the receiver or combine calls on
  one line. A single unchained invocation may stay on the receiver's line.
- Named-argument Policy B: prefer names for ambiguous booleans, enums, null/default literals, adjacent same-typed
  primitives, and project-defined calls with four or more arguments. Keep one- and two-argument obvious calls
  positional. Public parameter renames remain a source-compatibility concern.
- Built-in formatting and analyzers remain primary. `Orbyss.Foundation.Analyzers` supplies only semantic Program Kit
  rules that the SDK cannot express; generated repositories reference it centrally with `PrivateAssets=all`.
<!-- /program-kit:knowledge-rule -->

## Enforcement classification

<!-- program-kit:knowledge-rule principle.source-enforcement -->
- Universal: next-line control-flow bodies, argument/parameter layout, prepared argument values, one invocation per chain line,
  owned/observed async work, cancellation, bounded concurrency, lifecycle-safe teardown, explicit
  resource ownership, immutable production composition, no shell-level `AddHostedService`, coherent method
  abstraction, one declared type per file, private helpers last, and purposeful XML documentation on every
  declared type and member.
- Conditional: `ValueTask`, PLINQ, structs, records, primary constructors, frozen collections, live unloading,
  and specialized synchronization.
- Recommendation: line width, contextual named arguments, and sealing internal leaves.
- Qualified Foundation `source-readability-v1` enforces argument/parameter, prepared-value, chain and
  fields-first layout through ORB1007–ORB1010 with `FoundationSourceReadability=true`. Older packages
  block supported adoption until a qualified published release/profile exists; local candidates supply
  development proof, never public pins. Mandatory Foundation diagnostics cannot be suppressed/downgraded;
  native build/preflight reject disabled analyzer/compiler execution.
  SDK IDE2001/IDE1006 enforce body layout/naming; ORB1003/ORB1004/ORB1005 enforce one type, helpers-last
  and XML presence. Check this whole category after manual edits, including nested method, constructed,
  awaited and deferred arguments; preserve actual diagnostics, not just a passing chain check.
  Semantic ownership, cancellation/cleanup, abstraction and XML purpose still need scoped source review
  and adverse checks; a green build does not waive that review. Apply these rules to owned source and
  editable examples/templates, preserving external packages, historical evidence and native generated output.
- Prohibited unless ADR: invisible work, sync-over-async, unbounded queues/fan-out, custom schedulers, runtime feed
  mutation, and live reload without drain/unload evidence.
<!-- /program-kit:knowledge-rule -->

## Primary references

The following primary sources were checked on 2026-09-13. They substantiate runtime semantics;
Program Kit's mandatory/conditional choices above are product policy. Compile examples against the
managed SDK and exact packages before claiming support. Phase obligations bind the relevant sections
and executing verifier versions; semantic review must cite changed code and actual checks, not merely
assert that this profile was read.

- [Async scenarios](https://learn.microsoft.com/dotnet/csharp/asynchronous-programming/async-scenarios),
  [Interlocked](https://learn.microsoft.com/dotnet/api/system.threading.interlocked?view=net-10.0),
  [volatile limitations](https://learn.microsoft.com/dotnet/csharp/language-reference/keywords/volatile),
  and [channels](https://learn.microsoft.com/dotnet/core/extensions/channels).
- [Lazy semantics](https://learn.microsoft.com/dotnet/api/system.lazy-1?view=net-10.0),
  [DI ownership](https://learn.microsoft.com/dotnet/core/extensions/dependency-injection/guidelines),
  [disposal](https://learn.microsoft.com/dotnet/standard/garbage-collection/implementing-dispose),
  and [memory leases](https://learn.microsoft.com/dotnet/standard/memory-and-spans/memory-t-usage-guidelines).
- [TimeProvider](https://learn.microsoft.com/dotnet/standard/datetime/timeprovider-overview),
  [options](https://learn.microsoft.com/dotnet/core/extensions/options),
  and [HttpClient lifetime](https://learn.microsoft.com/dotnet/fundamentals/networking/http/httpclient-guidelines).
- [Protocol strings](https://learn.microsoft.com/dotnet/standard/base-types/best-practices-strings),
  [regex bounds](https://learn.microsoft.com/dotnet/standard/base-types/best-practices-regex),
  and [SDK security diagnostics](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/security-warnings).

- [Microsoft C# coding conventions](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/coding-conventions)
  for coherent structure and contract-focused comments.
- [CA1502: Avoid excessive complexity](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca1502)
  for cyclomatic-complexity measurement and configurable thresholds.
- [C# XML documentation](https://learn.microsoft.com/dotnet/csharp/language-reference/xmldoc/)
  for compiler-validated API documentation.
- [.NET runtime coding style](https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/coding-style.md)
  and [project guidelines](https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/project-guidelines.md)
  for member layout and source-file organization.
