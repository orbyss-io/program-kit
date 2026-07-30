# .NET Console input materialization

This guide is part of the installed Program Kit `0.1.0-alpha.2` knowledge
closure. It defines the supported consumer-owned seam between a Console design
and `program-kit dotnet generate-host console`.

## Ownership boundary

Program Kit never writes or edits the consumer integration project, its source,
or the request's supplied artifacts. The agent may author those consumer-owned
inputs under the human-started design, implementation, or maintenance
authority. The scaffold command may create one new semantic materialization
request from an explicit consumer-owned command sketch; it never overwrites or
repairs an existing consumer file.

`program-kit dotnet materialize-console-inputs` writes only:

- the selected project's ordinary `dotnet build --no-restore` outputs; and
- the explicit Program Kit-owned materialization output directory.

Never edit `shell.json`, `open-console.json`, `console-binding.json`,
`artifact-manifest.json`, `.program-kit-console-inputs.lock.json`, or any file
below `references/` after materialization. Change the consumer-owned source or
semantic request and run the materializer again.

## Supported project topology

Select one consumer-owned `net10.0` Console integration class library. It is
separate from the generated host and contains every binding-visible contract
and implementation:

- each public concrete request type;
- one public `I<Command>Handler` interface per command;
- one public sealed concrete implementation of each selected handler;
- an optional public `I<Command>Validator` interface and one public sealed
  implementation when the binding selects a validator;
- one public sealed validation-result type;
- one public sealed parameterless `CShells.Features.IShellFeature`; and
- the exact unkeyed scoped registrations.

A contracts-only project with implementations in another assembly is not
supported by this contract. Stop and route that topology to design work.

Retrieve the complete compiling project and source examples:

```text
program-kit capabilities read-resource dotnet-console-integration-project-example --workspace-root .
program-kit capabilities read-resource dotnet-console-integration-source-example --workspace-root .
```

The project example pins:

- `CShells.Abstractions` `[0.0.28]` and
  `Microsoft.Extensions.DependencyInjection.Abstractions` `[10.0.10]` for
  consumer-owned feature and registration source; and
- private exact `CShells` `[0.0.28]`,
  `Microsoft.Extensions.Hosting` `[10.0.10]`, `Spectre.Console` `[0.55.0]`,
  and `Spectre.Console.Cli` `[0.55.0]` compile-closure references so the
  materializer's finite project evaluation supplies every reference needed to
  preflight the generated Console host.

Keep all six exact references. The private compile-closure references do not
move handler or validator ownership into Program Kit, and they must not be
replaced by a hand-authored DLL list, directory scan, or ambient cache lookup.

The source example demonstrates the exact handler and validator signatures:

```csharp
ValueTask<int> HandleAsync(TRequest request, CancellationToken cancellationToken);
ValueTask<CommandValidationResult> ValidateAsync(
    TRequest request,
    CancellationToken cancellationToken);
```

`CommandValidationResult` must expose public readable `bool IsValid` and
`IReadOnlyList<string> Messages` properties. Request constructors, CLR types,
nullability, parameter order, handler types, and optional validator types must
match the binding intent exactly. Every selected handler registration must be
one unkeyed scoped service-to-implementation registration. A selected validator
may have at most one such registration. Do not register the selected
`IShellFeature`; the generated host constructs that exact feature once and
invokes `ConfigureServices`.

## Open Console contract style

Retrieve the exact product-owned rules in text or JSON:

```text
program-kit dotnet describe-console-contract --format text
program-kit dotnet describe-console-contract --format json
```

Open Console `0.1.0-alpha.2` enforces all of these rules:

1. Every command exit map is non-empty, contains success code `0`, contains
   every host-owned role, and uses each numeric code once.
2. `invalidInvocation`, `cancellation`, and `internalFailure` are distinct
   positive reservations. They never share code `0` or the help exit code.
   Even semantically similar failures receive different codes because
   automation must distinguish their lifecycle owner.
3. Every present stdin, stdout, and stderr contract has one non-null exact
   `schemaRevision`.
4. A source whose maximum occurrence exceeds one binds only as
   ``System.Collections.Immutable.ImmutableArray`1<TScalar>`` with exactly one
   scalar generic argument matching the finite logical type catalog.
5. The selected shell host's `operationBindings` are authoritative. Every
   command's explicit `requestSchemaRevisions`, `resultSchemaRevisions`, and
   `diagnosticSchemaRevisions` sets must equal the corresponding operation
   binding sets. Supersets, subsets, duplicates, and merely contained result
   schemas fail.

Schemas describe structure; the contract-style catalog explains semantics.
Neither chooses operations, authority, command meanings, CLR types, defaults,
or package policy for the human.

## Scaffold the required semantic request

Retrieve the complete executable examples and exact schemas:

```text
program-kit capabilities read-resource dotnet-console-command-sketch-example --workspace-root .
program-kit capabilities read-resource dotnet-console-input-request-example --workspace-root .
program-kit schemas read pkid:schema:program-kit:dotnet-console-command-sketch@0.1.0-alpha.1
program-kit schemas read pkid:schema:program-kit:dotnet-console-input-materialization-request@0.1.0-alpha.2
```

The command sketch is not a replacement for design. It records every semantic
value already selected by the consumer's accepted shell and Open Console
design: identities, command paths and summaries, arguments/options, operation
and schema revisions, request/handler/optional-validator CLR metadata names,
authority references, streams, exit meanings, configuration, defaults, and
the exact alpha.2 contract style.

Create one complete request without restoring, building, scanning source, or
inferring semantics:

```text
program-kit dotnet scaffold-console-request console-command-sketch.json --workspace-root . --consumer-project src/Example.ConsoleIntegration/Example.ConsoleIntegration.csproj --output console-input-request.json
```

The scaffolder reads only the exact sketch, project, and supplied artifact
paths. It derives the normalized project path, unambiguous `net10.0` target and
assembly name, exact operation-binding schema-set mirrors, canonical ordering,
and supplied artifact digests. It rejects placeholders, stale digests,
ambiguous project mechanics, unsafe/escaping paths, existing output, and
partial staging. It writes BOM-less bytes to staging, validates them through
the public schema and strict typed reader, and atomically promotes one new
file.

The resulting strict alpha.2 request contains:

- `$schema` and `version` use the exact alpha.2 materialization contract;
- `identity`, `ownerIdentity`, and `outputSetIdentity` are explicit consumer
  identities;
- `hostIdentity` selects exactly one Console host in the embedded `shell`;
- `consumerProjectPath` is one normalized forward-slash path from the supplied
  workspace root to the integration `.csproj`;
- `consumerProjectIdentity` and `consumerProjectName` identify that project;
- `targetFramework`, `configuration`, and `platform` are respectively
  `net10.0`, `Debug` or `Release`, and `AnyCPU`;
- `shell` is the complete accepted shell document;
- `openConsole` is the complete accepted Open Console document except for its
  computed shell revision;
- `binding` contains the complete CLR type and constructor mapping except for
  build-derived project/reference-assembly evidence; and
- `suppliedArtifacts` maps every explicit source artifact to one unique,
  normalized output path and exact SHA-256-bound revision.

The shell's `inputVersionMapRevision` and `inputVersionSelectionRevision` must
each occur exactly once in `suppliedArtifacts`. Each supplied digest must match
the current bytes. Program Kit computes the shell, Open Console, binding,
reference-assembly, and artifact-manifest revisions; never guess those values.

The binding maps every Open Console command operation revision to:

- a unique safe generated symbol;
- the public request metadata name;
- the public handler-interface metadata name;
- an optional public validator-interface metadata name; and
- constructor parameters in exact zero-based order, including CLR type,
  nullability, argument/option source, and canonical default disposition.

Use `program-kit commands describe dotnet.scaffold-console-request --format
text` and `program-kit commands describe
dotnet.materialize-console-inputs --format text` for the backed command
contracts. Use `program-kit diagnostics explain <PKCIM-id> --format text` for
a materialization failure. Do not inspect Program Kit assemblies or infer
undocumented enum order.

## Restore, materialize, and generate

The materializer deliberately never restores packages. Restore the exact
consumer project first under the active capability and repository package
policy:

```text
dotnet restore src/Example.ConsoleIntegration/Example.ConsoleIntegration.csproj
```

Then run the explicit build-authorized materialization:

```text
program-kit dotnet materialize-console-inputs console-input-request.json --workspace-root . --output .program-kit/console-inputs --build-consumer
```

The command:

1. rejects the Program Kit authoring workspace and unsafe paths;
2. runs one exact project build with `--no-restore`;
3. queries only that evaluated project for `TargetRefPath` and
   `ReferencePathWithRefAssemblies`;
4. validates the binding-visible types and implementations from that exact
   reference assembly;
5. hashes and content-addresses the complete evaluated compilation-reference
   closure;
6. validates every semantic document and cross-reference;
7. stages and verifies the complete output; and
8. reports `created`, `unchanged`, or `updated`.

It performs no solution scan, feed scan, package-cache scan, assembly string
search, framework-reference guessing, or consumer source mutation.

Generate the host only from the materialized closure:

```text
program-kit dotnet generate-host console --shell .program-kit/console-inputs/shell.json --host <exact-host-pkid> --artifact-manifest .program-kit/console-inputs/artifact-manifest.json --output generated/Example.Console
```

When the materialization lock is present, `generate-host` verifies every owned
materialized byte and computes the generated host's one `ProjectReference`
relative to the selected consumer integration project. It fails closed for a
stale lock, changed reference, missing project, unexpected file, version drift,
or generated output outside the same consumer workspace.

Finally verify the generated host:

```text
program-kit dotnet verify-host --root generated/Example.Console
```

If the exact request cannot be completed from accepted consumer semantics,
stop. A schema describes structure; it does not choose commands, authority,
operation identities, CLR types, defaults, or package policy for the human.
