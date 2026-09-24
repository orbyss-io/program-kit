# .NET practice enforcement audit

Reviewed Program Kit candidate: cfb60cc3974c4f5458a9814fda0abf6ed39c04fe.
Investigation only; no implementation or paid execution. The original research conversation
was not retrieved, so this is an audit of retained knowledge and enforcement, not a claim
that every original research finding survived.

Follow-up: the original task and attached request were subsequently recovered. The comparison
and proposed scope, including explicitly requested but missing Lazy<T> guidance, are recorded in
`dotnet-engineering-integration-plan.md`. This supersedes the retrieval limitation above.

## Retained knowledge

`extensions/program-kit-dotnet/references/dotnet-engineering.md` covers Task versus ValueTask,
sync-over-async, observed work, cancellation, shell-owned background tasks, lock and SemaphoreSlim,
ConcurrentDictionary factory atomicity, bounded channels, resource/disposal ownership, memory,
LINQ, record/class/struct choices, constructors, and conditional performance optimizations.
Its enforcement classification distinguishes universal, conditional and recommended rules.
No Lazy<T>, LazyThreadSafetyMode or LazyInitializer guidance was found in the searched shipped
references. EF lazy-loading guidance concerns a different mechanism.

## Current application path

- bootstrap_context.py adds the engineering reference when .NET is detected.
- technology-profiles/dotnet.md calls it mandatory.
- implementation-check.md requests detected technology profiles and checks general cancellation,
  concurrency, ownership and lifecycle design. It is a preimplementation plan check.
- The new phase-obligations.json binds generic implementation-quality and dotnet-boundaries
  requirements, but neither directly includes dotnet-engineering.md. phase_obligations.py
  constructs knowledgeHashes from the direct sources of applicable obligations. Consequently
  this full runtime profile is not independently bound there; a transitive prose link is weaker.
- knowledge-inventory.json lists the engineering reference only for setup and verification.
  It is not itself the registry used to generate phase obligations.
- validate_components.py checks for selected text such as Task/Task<T> and SemaphoreSlim.
  This establishes document presence, not rejection of incorrect consumer C#.

## Deterministic coverage and drift

ProgramKit.Build.props enables SDK analyzers and warnings-as-errors and references Foundation
Analyzers 0.2.0. That is real coverage, but AnalysisLevel=latest does not establish a complete
rule-by-rule contract for all the practices above. The exact enabled SDK diagnostic set and
suppression behavior need compiler fixtures, not inference from one MSBuild setting.

The Foundation analyzer source at the locally available v0.2.0 tag declares six diagnostics:
shell AddHostedService, named arguments, one type per file, private helpers last, XML documentation
and feature identity. These do not constitute a general async/concurrency/type-choice analyzer.

An additional concrete integration mismatch exists: Program Kit's generated .editorconfig sets
PK1001 through PK1006, while Foundation v0.2.0 source declares ORB1001 through ORB1006. Thus those
explicit severity settings do not target the declared diagnostics. This does not imply every
analyzer is disabled: most inspected descriptors are enabled errors by default. Verify the
actual published package and compiler behavior before claiming the precise runtime impact.

## Proposed correction

Extend the existing engineering profile and existing obligation mechanism, rather than adding
a competing implementation guide. Give each rule family explicit applicability and proof:

- Analyzer proof for reliably detectable misuse; verify pinned diagnostic IDs, severity and
  suppression policy with valid/invalid C# fixtures. Reuse SDK/Foundation analyzers first.
- Behavioral proof for cancellation, bounded concurrency, shutdown/drain, resource release and
  factory execution where the implementation uses those mechanisms.
- Attributed review, with measurement when relevant, for ValueTask, structs, specialized locks
  and other conditional decisions. Do not turn conditional guidance into blanket bans.
- Bind applicable engineering knowledge to planning/implementation/delivery source snapshots;
  require fresh relevant evidence after source changes, with proportional exceptions.
- Recover/compare the original research before claiming completeness. Reconcile missing topics
  such as Lazy<T> into the existing reference using primary sources.

Test the enforcement chain with deliberately incorrect consumer examples, not keyword-only
document checks: sync-over-async, unobserved work, invalid ValueTask consumption, cancellation
loss, semaphore leak, unsafe repeated factory effects, and shutdown/disposal races where
applicable. Use semantic review for cases static analysis cannot soundly decide. Include safe
counterexamples so the gate does not reward unnecessary ceremony or reject legitimate designs.

Related stale knowledge found while tracing: technology-profiles/dotnet.md still describes a
consumer runnable application image in its closing paragraph. Reconcile that with the current
application-bundle authority as part of the pending knowledge corrections.
