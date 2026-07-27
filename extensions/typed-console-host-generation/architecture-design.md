# Program Kit typed Console host generation

State: awaiting exact human approval of the validated canonical design and
implementation-plan digests.

The canonical design is `architecture-design.json`. This document is its
reviewer-oriented projection.

Static conformance disposition: `reuse-existing`. Program Kit-owned source uses
the existing private C# source-quality gate and exhaustive verification profile.
Generated consumer hosts additionally select the existing public
generated-source analyzer. Binding metadata, generated-tree integrity, process
behavior, capability isolation, and human authority remain dedicated
schema/digest/process/capability proof obligations rather than being
misrepresented as C# static-analysis claims.

## 1. Ownership and generated topology

Program Kit generates one complete executable `<Product>.Cli.Host` project.
That project owns `Program.cs`, exact package references, the Spectre command
tree, typed settings, request factories, host composition, validation
orchestration, help, completion, diagnostics, generation evidence, and
integrity integration.

The generated host has a one-way `ProjectReference` to one consumer-owned
project. The consumer owns request models, handler and optional validator
contracts and implementations, one Console `IShellFeature`, and ordinary
services. No consumer implementation is copied into generated output.

Open Console is moved to neutral schema and source ownership. It contains no
CLR, Spectre, CShells, project, or constructor vocabulary. The .NET binding and
projection contracts own those concerns.

## 2. Binding compiler

The .NET binding document is a compiler contract, not advisory metadata. It
identifies the consumer project, exact reference assembly and SHA-256, single
feature type, consumer validation-result type, and one operation binding for
every Open Console command.

Every CLR type is a structured descriptor containing its metadata name, generic
arguments, and reference nullability. Every constructor parameter records its
position, name, CLR type, Open Console source, and a mandatory default
disposition: either `none` or one canonical value.

Every operation supplies one explicit generated C# symbol. Symbols must be
valid and ordinally unique. Program Kit never guesses through collisions.

Handlers have the exact shape:

```csharp
ValueTask<int> HandleAsync(TRequest request, CancellationToken cancellationToken);
```

Optional validators have the exact shape:

```csharp
ValueTask<CommandValidationResult> ValidateAsync(
    TRequest request,
    CancellationToken cancellationToken);
```

Metadata is inspected offline with `System.Reflection.Metadata`. The generator
does not load the assembly, execute consumer code, resolve runtime
dependencies, or invoke MSBuild. Candidate source compiles through Roslyn
against the exact reference bytes.

## 3. Generator structure

Console generation is a small compiler pipeline:

1. Validate Open Console, binding, generation request, and projection revision.
2. Verify and inspect consumer metadata.
3. Build an immutable projection.
4. Render one deterministic file at a time.
5. Compile the isolated candidate.
6. Seal its generated output.
7. Atomically publish and verify it.

The .NET source structure is:

```text
Generation/Console/
  Binding/
  Contracts/
  Projection/
  Rendering/
  Compilation/
  Composition/
  Diagnostics/
```

Rendering uses a repository-owned code writer rather than templates. Output is
UTF-8 without BOM, LF terminated, four-space indented, invariant formatted,
ordinally ordered, and free of timestamps, absolute paths, random identifiers,
or environment-specific content.

## 4. Spectre projection

The generated project pins:

- `Spectre.Console` `0.55.0`;
- `Spectre.Console.Cli` `0.55.0`;
- `CShells` `0.0.28`.

The projection uses `CommandApp`, `ITypeRegistrar`, `AsyncCommand<TSettings>`,
`CommandArgument`, `CommandOption`, command branches, cancellation tokens, and
`IAnsiConsole`. The registrar resolves from the already-created invocation
scope and never builds a second service provider.

Command paths become an ordinal trie. Unsupported path shapes, parsing rules,
or value forms fail projection. Open Console is never narrowed merely to make a
Spectre version succeed.

Generated settings preserve presence separately from values so defaults are
applied only after successful document validation while constructing the
consumer request.

## 5. Validation and invocation

The fixed order is:

1. Spectre binding under the proven projection profile.
2. Generated deterministic document validation.
3. Consumer request construction.
4. Optional consumer validation.
5. Handler execution.

Document validation covers declared shape, logical types, occurrence bounds,
conflicts, prerequisites, and defaults. Consumer validation may inspect
environment, filesystem, time, reachability, or cross-value semantics that the
document cannot determine.

Consumer messages are rendered as escaped plain text. A failed consumer
validator uses the document's invalid-invocation code and prevents handler
execution.

## 6. Exit codes, help, and completion

Open Console owns language-neutral host exit-code roles. The .NET projection
maps parse, document-validation, and consumer-validation failures to
`invalidInvocation`; cancellation and unexpected internal failure use their
declared host roles. Handler integers pass through unchanged at the managed
entry point.

Spectre owns command binding and help under a process-level conformance matrix.
Help uses plain styling and does not compose consumer services.

Spectre.Console.Cli 0.55.0 provides no sufficient documented completion engine,
so the host generates one narrow, information-only completion protocol. It
emits static declared candidates and never parses or invokes a command.

## 7. CShells composition

The binding names exactly one public, sealed, concrete, nongeneric,
parameterless Console `IShellFeature`. Its `ConfigureServices` registers
consumer handlers, optional validators, and ordinary services.

Before creating the provider, generated composition audits service descriptors:

- exactly one scoped, unkeyed implementation-type handler per command;
- zero or one scoped, unkeyed implementation-type validator per command;
- no keyed, factory, instance, open-generic, or wrong-lifetime registration;
- no additional Console feature.

Consumer constructors may not inject `IServiceProvider`,
`IServiceScopeFactory`, `IServiceCollection`, Spectre types, or generated host
types. The provider enables build and scope validation. Information-only
invocations do not start the shell.

## 8. Generated-output integrity

All generated host roots are Program Kit-owned. An in-tree integrity manifest
lists every other generated file and its SHA-256. A sibling external anchor
seals the manifest. Build outputs are redirected outside the generated root, so
unexpected in-root files are drift.

`dotnet verify-host` is offline and reports every modified, missing, unexpected,
unsafe, or unsealed file. Exit codes follow Program Kit's frozen operation
profile: success `0`, conformance failure `1`, usage/input failure `2`, and
internal failure `3`.

The exact private build integration verifies before compilation and emits a
required intermediate attestation type. Accidentally removing the verification
target makes compilation fail. There is no runtime source-tree verification.
Publication verifies independently.

## 9. Refresh and repair

A committed consumer-owned generation request binds all exact input paths,
versions, profiles, and output locations.

`dotnet refresh-host --request <file>`:

- creates an absent host;
- touches nothing when candidate bytes are identical;
- atomically replaces a valid changed host;
- refuses drift before repair authorization;
- supports deterministic preview.

`--build-consumer` explicitly delegates consumer compilation to the approved
C# build profile. The core generator never invokes arbitrary MSBuild.

`--repair-generated-output` is an explicit human-authorized recovery. It moves
the drifted tree to a digest-addressed quarantine and regenerates only from
authoritative inputs.

## 10. Incremental maintenance

`maintain-software` owns small, human-started, architecture-compatible changes.
It shares inert completion profiles with `implement-software-plan`; it does not
duplicate build, refresh, test, publication, evidence, commit, or push
knowledge.

Every maintenance unit refreshes every affected derived artifact and records
one coherent reversible commit. Exact Program Kit upgrades require prior human
approval. Material mechanisms, schemas, security boundaries, package families,
or architectural changes route to `design-software`.

Program Kit product capabilities are always distributable inert payloads.
Explicit initialization into a selected consumer workspace is the only
activation boundary. Authoring-workspace installation and user-global writes
are forbidden and tested.

## 11. Evidence and conformance

Generation evidence records exact Program Kit, Open Console, binding,
projection, project, assembly, package, layout, and integrity revisions and
digests. The integrity manifest covers generated bytes; the external anchor
covers the manifest; implementation or maintenance receipts record why the
operation occurred.

Release-gating conformance builds and executes a real typed Console fixture. It
proves binding, parsing, help, completion, validation order, DI cardinality,
exit codes, cancellation, deterministic regeneration, tamper detection,
repair, build/publication rejection, capability packaging, authoring
non-activation, isolated consumer initialization, and coherent maintenance
history.

## 12. Security and exclusions

Documents contain structured data only, never executable C# fragments. Paths
are containment checked and reparse traversal is rejected. Consumer validator
messages and descriptions are escaped before display. Consumer runtime code is
not sandboxed.

The integrity threat model covers ordinary human or agent drift. Coordinated
hostile rewriting of the complete tree, verifier, build integration, anchor,
and repository history requires external signing and remains deferred.

The design does not publish packages, release Program Kit, deploy applications,
modify JTest, introduce hooks or watchers, or activate packaged capabilities in
the authoring workspace.
