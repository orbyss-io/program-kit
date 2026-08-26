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
  register shell-owned work through `ProgramKit.Tasks`; the Generic Host does not start services registered in
  a shell provider.
- Startup tasks may be scoped. Background and recurring tasks are shell-singletons owned by the task manager.
  Shutdown is idempotent, cancels, awaits with a bound, drains before provider disposal, and has disposal fallback.
- Custom schedulers, `Task.Factory.StartNew`, invisible fire-and-forget, and runtime work without an owner require
  an Accepted ADR and measured evidence.

## Synchronization and collections

- Use `lock` or `System.Threading.Lock` for short synchronous critical sections. Never await while holding it.
- Use `SemaphoreSlim` for asynchronous mutual exclusion or bounded concurrency, with acquisition/release paired
  in `try/finally` after successful acquisition. It is not a universal lock and provides no fairness guarantee.
- Prefer concurrent collections only when their precise atomicity is understood. `ConcurrentDictionary`
  delegates can execute more than once and outside its internal locks; factories must tolerate that behavior.
- Prefer message passing or bounded channels when ownership transfer is clearer than shared mutable state.

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

## LINQ and query boundaries

- Preserve deferred-execution awareness and avoid multiple enumeration. Enable CA1851 where it adds signal.
- Keep `IQueryable<T>` expressions provider-translatable until the deliberate materialization boundary. Do not
  hide client evaluation, accidental full-table reads, or offset-pagination scaling costs.
- Avoid side effects in query operators. Materialize when a stable snapshot or repeated traversal is intended.
- PLINQ and parallel projection require measurement, bounded resource analysis, deterministic outcome semantics,
  and cancellation. Do not put unbounded async lambdas into synchronous LINQ operators.

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

## Orbyss style overlay

- Private fields use camelCase without an underscore; enforce through EditorConfig naming rules.
- Use a 120-column target. When a call becomes multiline, place one argument per line.
- Named-argument Policy B: require names for ambiguous booleans, enums, null/default literals, adjacent same-typed
  primitives, and project-defined calls with four or more arguments. Keep one- and two-argument obvious calls
  positional. Public parameter renames remain a source-compatibility concern.
- Built-in formatting and analyzers remain primary. `ProgramKit.Analyzers` supplies only semantic Program Kit
  rules that the SDK cannot express; generated repositories reference it centrally with `PrivateAssets=all`.

## Enforcement classification

- Universal: owned/observed async work, cancellation, bounded concurrency, lifecycle-safe teardown, explicit
  resource ownership, immutable production composition, and no shell-level `AddHostedService`.
- Conditional: `ValueTask`, PLINQ, structs, records, primary constructors, frozen collections, live unloading,
  and specialized synchronization.
- Recommendation: line width, multiline layout, contextual named arguments, and sealing internal leaves.
- Prohibited unless ADR: invisible work, sync-over-async, unbounded queues/fan-out, custom schedulers, runtime feed
  mutation, and live reload without drain/unload evidence.
