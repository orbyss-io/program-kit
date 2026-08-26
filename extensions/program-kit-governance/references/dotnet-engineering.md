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
- Built-in formatting and analyzers remain primary. `ProgramKit.Analyzers` supplies only semantic Program Kit
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

- [Microsoft C# coding conventions](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/coding-conventions)
  for coherent structure and contract-focused comments.
- [CA1502: Avoid excessive complexity](https://learn.microsoft.com/dotnet/fundamentals/code-analysis/quality-rules/ca1502)
  for cyclomatic-complexity measurement and configurable thresholds.
- [C# XML documentation](https://learn.microsoft.com/dotnet/csharp/language-reference/xmldoc/)
  for compiler-validated API documentation.
- [.NET runtime coding style](https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/coding-style.md)
  and [project guidelines](https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/project-guidelines.md)
  for member layout and source-file organization.
