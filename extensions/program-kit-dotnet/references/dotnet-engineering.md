# .NET engineering profile

Apply these rules only when .NET is selected. Project-specific style remains an overlay; runtime correctness and
ownership rules are profile requirements.

## Async and shell-owned work

- `Task`/`Task<T>` is the default asynchronous representation. Use `ValueTask` only for a measured hot path
  whose consumers obey its single-consumption constraints.
- `async void` is limited to event handlers. Do not use `.Result`, `.Wait()`, sync-over-async, unobserved work,
  unbounded producer queues, or unbounded fan-out.
- Propagate cancellation and define timeout, retry, idempotency, fault, terminal-state, and observability policy.
- `IHostedService` and `BackgroundService` are root-provider, process-global facilities. A CShells feature must
  register shell-owned work through `Orbyss.Foundation.Tasks`; the Generic Host does not start services registered in
  a shell provider.
- Startup tasks may be scoped. Background and recurring tasks are shell-singletons owned by the task manager.
  Shutdown is idempotent, cancels, awaits with a bound, drains before provider disposal, and has disposal fallback.
- Custom schedulers, `Task.Factory.StartNew`, invisible fire-and-forget, and runtime work without an owner require
  an Accepted ADR and measured evidence.
- Await asynchronous I/O directly. `Task.Run` does not improve server I/O scalability; CPU offload needs a
  bounded execution policy. Returning a task directly is valid only when disposal, `finally` and exception
  handling do not need to span its completion. Observe all child outcomes from `Task.WhenAll`, including
  cancellation. Async streams propagate enumeration cancellation and dispose their enumerators.
- Choose continuation behavior for the actual caller context; do not mechanically add or remove
  `ConfigureAwait`. Distinguish per-process Foundation scheduling from distributed work ownership.

## Synchronization and collections

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

## Resource and memory ownership

- The creator owns disposal unless ownership is explicitly transferred. DI disposes services it creates; do not
  manually dispose them or register pre-created disposable instances without an owner.
- Use `IAsyncDisposable` when teardown performs asynchronous work. Constructors do not start background work.
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

## LINQ and query boundaries

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

## Type and construction choices

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

## Deferred initialization

Use `Lazy<T>` only for genuinely deferred, reusable initialization with an explicit lifetime. Define the
factory's side effects, exception policy, thread-safety mode and disposal owner. `ExecutionAndPublication`
coordinates initialization and can cache factory exceptions; it does not make the value thread-safe.
`PublicationOnly` can run several factories: account for duplicate effects and losing disposable values.
It is not an automatic retry policy. `Lazy<Task<T>>` can retain faulted or cancelled tasks; define shared
failure and cancellation semantics instead of binding shared initialization to one caller's token.
Required initialization uses the selected Foundation startup mechanism. Do not invent a universal
AsyncLazy abstraction, hide synchronous blocking, or defer mandatory configuration validation.

## Time, configuration and I/O

- Use `TimeProvider` for replaceable time, monotonic timestamps for elapsed duration, and controlled-time
  tests for deadlines. Use `PeriodicTimer` when its single-consumer semantics fit owned periodic work.
- Bind typed options and validate at their actual activation boundary. Root `ValidateOnStart` alone is
  not evidence for a CShells provider. Define reload and snapshot lifetimes and test invalid configuration.
- Use a supported `HttpClient` lifetime/DNS strategy: factory-managed handlers or long-lived clients with
  a configured pooled connection lifetime. Define deadlines and cancellation; retry only replay-safe
  operations, accounting for effects and commit ambiguity. Use `IFileProvider` where it fits the resource
  boundary; it does not by itself establish path admission or tenant isolation.

## Secure runtime boundaries and observability

Reuse the selected WEB controls and managed JSON/asset mechanisms in `secure-web-profiles.md`; these
rules specialize runtime use, not their identities or policy. Known envelopes become typed after
admission as defined in `programming-guardrails.md`.

- Specify ordinal/culture and normalization semantics for protocol identifiers; do not let machine culture
  change authorization, identity or persisted wire meaning. Bound untrusted parsing, regular expressions,
  archives and decompression; use timeouts or an appropriate non-backtracking regex where supported.
- Allowlist polymorphic input. Admit file paths, outbound URLs and process arguments at their trust
  boundary; use structured process argument APIs and protect against traversal/SSRF. Use platform
  cryptographic primitives and secure random APIs for security purposes, never custom cryptography.
- Preserve exception stacks and distinguish cancellation from faults. Use structured logging and, when
  meaningful, `ActivitySource`/`Meter`; bound cardinality and redact sensitive data. Test denied, malformed,
  oversized and fault paths, including logs, rather than relying on a successful request.
- Unsafe code, interop, runtime code generation, custom schedulers, distributed locks and live reload
  trigger scoped security/compatibility research. Source generation, reflection caches, trimming and AOT
  are conditional on measured needs and the selected deployment; verify that deployment before adoption.

## Method bodies and extraction

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

## Source files and documentation

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

## Orbyss style overlay

- Private fields use camelCase without an underscore; enforce through EditorConfig naming rules.
- Use a 120-column target. When a call becomes multiline, place one argument per line.
- Named-argument Policy B: require names for ambiguous booleans, enums, null/default literals, adjacent same-typed
  primitives, and project-defined calls with four or more arguments. Keep one- and two-argument obvious calls
  positional. Public parameter renames remain a source-compatibility concern.
- Built-in formatting and analyzers remain primary. `Orbyss.Foundation.Analyzers` supplies only semantic Program Kit
  rules that the SDK cannot express; generated repositories reference it centrally with `PrivateAssets=all`.

## Enforcement classification

- Universal: owned/observed async work, cancellation, bounded concurrency, lifecycle-safe teardown, explicit
  resource ownership, immutable production composition, no shell-level `AddHostedService`, coherent method
  abstraction, one declared type per file, private helpers last, and purposeful XML documentation on every
  declared type and member.
- Conditional: `ValueTask`, PLINQ, structs, records, primary constructors, frozen collections, live unloading,
  and specialized synchronization.
- Recommendation: line width, multiline layout, contextual named arguments, and sealing internal leaves.
- Prohibited unless ADR: invisible work, sync-over-async, unbounded queues/fan-out, custom schedulers, runtime feed
  mutation, and live reload without drain/unload evidence.

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
