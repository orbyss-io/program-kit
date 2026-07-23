# Program Kit C# source quality gate

Policy ID: `pkid:policy:program-kit:csharp-source-quality-gate`
Policy version: `1.9.0`
Status: human-directed implementation constraint
Effective date: 2026-07-23
Applies to: all Program Kit-owned handwritten C# and all C# emitted by Program
Kit generators

This constraint refines implementation quality within the approved bootstrap
scope. It does not rewrite or supersede the exact approved review-set `0.3.0`
architecture and implementation-plan bytes.

The following rules are mandatory:

1. A physical C# source file declares at most one named type. When it declares
   one, the gate applies this consistently to classes, interfaces, records,
   structs, enums, and delegates, including nested declarations. Type-free
   files are reserved for imports and assembly metadata; they may not contain
   executable top-level statements.
2. Every C# file lives below a logical intent folder. Its file name matches its
   declared type, and its namespace is exactly the project root namespace plus
   its relative folder segments. Unit-test folders mirror the tested Program
   Kit domain and source-intent folders; shared test infrastructure has its own
   explicit `TestSupport` intent. Every project that imports this gate also
   compares its physical C# inventory with `Compile`: disabling default items
   or omitting a physical source fails the build. Only `bin`, `obj`, the exact
   main conformance-fixture tree, and the exact selective negative-probe
   projects are excluded.
3. Code never invokes behavior directly on a freshly constructed receiver.
   Patterns such as `new ClassA().Validate(value)` and
   `new ClassA(context).Validate()` fail the build. The same rule follows the
   receiver result through conversions, conditional access, tuple or array
   selection, switch expressions, delegate binding, unary operations, and
   awaits; syntactic wrapping does not make a fresh receiver acceptable.
4. Uncontracted internal helpers are static, including file-local helpers.
   Static helpers may retain fixed immutable values and metadata, but never a
   behavioral collaborator in static state. Stateful or replaceable behavior
   is exposed behind a narrow interface that declares actual behavior and is
   supplied through constructor injection. A relevant framework behavior
   interface, such as `IJsonTypeInfoResolver`, is a valid contract; framework
   marker interfaces such as `IDisposable` are not. A helper that implements a
   real behavior interface is an implementation, not a static-helper candidate.
   Any non-framework interface that declares callable behavior is behavioral
   regardless of its name or suffix, and a concrete implementation of that
   contract remains behavioral regardless of its own name.
   A behavioral implementation's public instance surface, including inherited
   non-framework behavior, must be represented by interfaces; an unrelated or
   static-only interface does not qualify.
   Production code constructs behavioral implementations only at an explicit
   `Composition` or `DependencyInjection` boundary. Concrete behavioral types
   are not valid constructor, field, or property dependencies. Interface
   collaborators are constructor-captured in readonly fields or get-only
   properties. Composition boundaries receive no exception for static
   behavioral state: they construct each factory or other collaborator for the
   composition being assembled and pass it through its interface. Static
   `Default` factories, registries, serializers, and equivalent singleton or
   service-locator properties fail the gate. Every source construction entry
   point must establish that
   provenance at every reachable normal exit. The proof is path-sensitive:
   conditional or early-return paths, delegated-constructor argument mapping,
   and later overwrites are all considered. Constructor control flow that the
   gate cannot safely prove, including structured exception handling, fails
   closed. Mutable field, set, init, positional-record, hidden mutable
   primary-constructor capture, and service-locator initializer injection fail
   the gate. The same provenance analysis follows collaborators nested in
   factories and collections and treats invocation as behavior use. Framework
   `Task<T>`, `ValueTask<T>`, and `TaskCompletionSource<T>` values are async
   result carriers rather than retained collaborators; this exception does not
   apply to interface return-substitutability analysis. Framework abstract
   behavior bases are accepted only when every additional public behavior
   member overrides that framework contract; test observation hooks remain
   non-public or require their own interface. This dependency rule still
   applies inside composition code and tests: those locations may construct a
   named system under test or selected implementation, but they do not gain
   permission to retain concrete behavioral collaborators.
   Behavioral interface methods, properties, and indexers return substitutable
   contracts, including when the return is nested in a generic wrapper,
   collection, array, or constrained type parameter. They do not expose a
   concrete builder, factory, registry, serializer, or other behavioral
   implementation. Immutable records, structs, and genuinely immutable value
   contracts such as descriptors and results remain valid return values.
5. `TreatWarningsAsErrors`, nullable analysis, latest-recommended analysis, and
   build-time code-style enforcement remain enabled for every owned project,
   including the gate itself. Project-level warning exclusions, rulesets,
   analyzer disabling, caller-supplied SDK-internal analyzer inputs, effective
   compiler ruleset substitution, per-source warning suppression, nullable
   disabling, and severity downgrades fail closed during restore, build, test,
   pack, publish, and generated-output verification. On .NET 10,
   Microsoft.Testing.Platform
   `dotnet test --no-build` does not execute project MSBuild targets, so it is
   not an acceptance command and must never be cited as current-source test
   evidence. Accepted test evidence runs `dotnet test` without `--no-build`,
   which performs the gated build first. Each C# invocation also emits a
   command-line receipt. Immediately before compilation and again afterward,
   it rejects compiler skipping, analyzer skipping, response files, compiler
   substitution, shared or host-compiler reuse, post-compilation hooks,
   target-framework mutation, command-line receipt removal, or
   generated-receipt redirection. Disabling shared and host compilation
   prevents a producing build from retaining stale gate code by analyzer path
   or using an unverified compiler supplied by an IDE host. After compilation,
   the gate compares the executed analyzer, source, reference,
   additional-file, and analyzer-configuration arguments with the sets it
   validated immediately before compilation, and verifies the executed
   warning, nullable, language, and exact `net10.0` inputs. The gate assembly also
   emits a compiler-generated receipt into a freshly cleared intermediate
   location; its absence proves that returning a plausible command line was
   not sufficient and fails the build. A project-local target that mutates
   compiler inputs after the ordinary validation targets therefore fails the
   same build instead of creating an ordinary time-of-check/time-of-use bypass.
   The known SDK post-compilation target hook is pinned empty. Repository-owned
   MSBuild definitions remain reviewed source inside the trust boundary; this
   receipt is not claimed as protection against a malicious build definition
   that deliberately forges and later sanitizes every in-process receipt.
   Pack and publish additionally reject design-time or compiler-skipping modes.
6. A warning may be ignored only after the human explicitly approves a
   diagnostic-specific, project-specific, source-specific, minimally scoped
   exception and its rationale. The versioned ledger binds the diagnostic,
   project, normalized source path, suppression mechanism, symbol or line
   target, human approval identity, approval date, and rationale. The analyzer
   resolves suppression attributes and their constructor parameters
   semantically, consumes the ledger as live input, rejects malformed or
   duplicate entries, and rejects stale entries that do not match compiled
   source. Attribute approvals bind the attribute target specifier, `Scope`,
   and `MessageId` as well as the symbol target. Pragma approvals bind both the
   active disable and matching active restore line, so deleting, deactivating,
   or widening the restore invalidates the approval.
   The human in the active implementation session approved one quarantined
   compiler-level compatibility exception on 2026-07-23: `CS1701` only, for the exact
   canonical `Orbyss.ProgramKit.UnitTests` and
   `Orbyss.ProgramKit.ConformanceTests` projects, while they resolve the exact
   `MSTest.Sdk` `4.3.2` closure recorded in their lock files. The compiler-level
   ledger records bind the SDK version, the exact locked package-content hashes,
   warning-producing assembly set, the .NET 10 `System.Runtime` identity, the
   absence of .NET 10 assets in that closure, the active human-session
   authority, and mandatory review on every test-toolchain change. The gate
   rejects any additional raw assembly reference before
   package resolution, including a lower-target assembly whose own `CS1701`
   would otherwise be hidden by the global suppression. It revalidates the
   compiler receipt and rejects lock mutation during compilation. Unrelated
   product dependencies may evolve without widening the quarantined test-toolchain
   closure. Changing the project,
   diagnostic, package selection, closure, assembly identity, raw-reference
   inventory, runtime identity, or .NET 10 asset availability fails closed.
   A newly created test project does not inherit this exception. The quarantine
   must be removed as soon as the selected test toolchain supplies a compatible
   .NET 10 closure; it is not general authority to build on suppressed warnings.
   Every other compiler `/nowarn` remains forbidden.
   For projects without that exact active approval, the compiler command line
   may not contain `/nowarn`, including suppressions that the pinned SDK would
   otherwise add internally. The gate narrowly prevents those legacy SDK
   branches while preserving the canonical `net10.0` compiler target and
   restores the evaluated framework identity immediately after compilation.
7. Generated C# is not accepted merely because generation succeeded. A Program
   Kit Roslyn generator emits the ownership header
   `// <auto-generated program-kit>` as its exact first line and uses the
   exact two-segment logical hint path
   `ProgramKitGenerated/<intent>/<TypeName>.cs`; a claimed Program Kit output
   with a malformed header or any other path shape fails closed. A generated
   type-free compiler-execution receipt has the single reserved intent
   `CompilerInvocation`, exact file name
   `ProgramKitCompilerInvocationReceipt.cs`, and exact marker content; that
   reservation grants no general consumer intent folder. A generated marker
   is resolved only within the project-relative path or source hint, so
   an unrelated ancestor directory named `ProgramKitGenerated` cannot
   reclassify handwritten source. Owned physical source cannot opt out of
   analysis with another `auto-generated` header, `GeneratedCode`, or
   `CompilerGenerated` claim; any generated-code claim requires the exact
   Program Kit header and logical path. A generated physical project imports the
   repository-owned generated-project gate, runs this same analyzer, and
   completes a warnings-as-errors build before its output can be treated as a
   valid Program Kit artifact. Compiler and third-party source-generator
   implementation details under `obj` remain the responsibility of their
   owning SDK or dependency and are not reclassified as Program Kit-authored
   source.

The gate intentionally does not ban all internal state classes or all public
static APIs. Those broader rules would turn naming heuristics into architecture
and were not part of the human instruction. Its central behavioral
classification includes the governed implementation roles builder,
canonicalizer, coordinator, dispatcher, executor, factory, gateway, handler,
manager, middleware, pipeline, processor, provider, publisher, registry,
repository, resolver, runner, scheduler, serializer, service, store, and
validator.
Domains may add more explicit classifications through their contracts and
architecture tests; they may not use an omitted or novel suffix to evade the
objective rules above.

The only non-compiling source specimens are the exact negative gate fixtures
under
`program-kit/tests/Orbyss.ProgramKit.ConformanceTests/Fixtures/CSharpGate`.
They are excluded from every normal compilation and are compiled individually
only to prove that the matching stable diagnostic rejects them. They are test
inputs, never accepted or generated implementation output.

Authority is the human instruction supplied in the active Codex implementation
session on 2026-07-23, including the direction to treat this as a serious
finding, correct it first, and continue all later implementation under the
gate.
