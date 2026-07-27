# Program Kit generated Console command dispatch

Status: ready for validation and human review
Canonical identity:
`pkid:design:program-kit:console-command-dispatch@1.0.0`

The canonical machine-readable design is `architecture-design.json`. This
Markdown projection is reviewer-oriented and does not replace it.

## Outcome

A generated Console host will no longer stop at parsing. When the unchanged
generated parser returns `InvokeCommand == true`, the generated composition
root will resolve one explicitly registered consumer dispatcher, run it once,
and return its integer unchanged from `Program.Main`.

Parse failures, help, and completion retain their existing behavior and return
before host composition. A successful command with no dispatcher registration
fails closed before hosted behavior starts instead of silently returning `0`.

## Generated contract

Console generation adds one host-local file:

`ProgramKitGenerated/Commands/IProgramKitConsoleCommandDispatcher.cs`

The generated contract is internal because its input is the existing internal
`GeneratedConsoleParseResult`:

```csharp
internal interface IProgramKitConsoleCommandDispatcher
{
    ValueTask<int> DispatchAsync(
        GeneratedConsoleParseResult parseResult,
        CancellationToken cancellationToken);
}
```

The exact signature is a compatibility boundary. The consumer implements this
interface in consumer-owned source compiled into the generated host assembly.
This is the same ownership style as the generated FastEndpoints dispatcher
port, without making the Program Kit generator package a runtime dependency.

The dispatcher receives:

- the canonical command string;
- canonical option names and their parsed values;
- positional arguments; and
- the configured host's application-stopping token.

The consumer owns command selection, domain services, output, cancellation and
unexpected-failure policy, and the meaning of every returned integer. Program
Kit does not clamp, translate, or reinterpret that result.

## Composition contract

The already-partial generated `Program` type declares and invokes one optional
consumer implementation:

```csharp
static partial void ConfigureProgramKitConsoleServices(
    IServiceCollection services);
```

The method is a composition-root hook, not a behavioral extension registry.
Consumer source uses it to register the generated dispatcher interface and any
ordinary services it needs. Consumer dispatcher implementations receive their
behavioral dependencies through constructor injection.

If the consumer omits the partial method, compilation still succeeds. On a
successful command parse, generated code uses required DI resolution before
host start. Missing or ambiguous registration therefore fails closed before
hosted behavior runs.

There is no reflection, assembly scanning, ambient dispatcher, static
behavioral collaborator, or runtime reference to the generator.

## Invocation lifecycle

The generated lifecycle is ordered:

1. parse process arguments;
2. for parser failure, write the diagnostic and return the parser's code;
3. for help or completion, write the information output and return its code;
4. create the selected Generic Host or WebApplication builder;
5. render existing generated configuration, telemetry, failure, security,
   health, task-runtime, and shell registrations;
6. invoke the consumer Console service-registration partial method;
7. build the host;
8. resolve the required dispatcher before starting hosted behavior;
9. start the configured host;
10. dispatch the successful parse exactly once with the application-stopping
    token;
11. attempt host stop in a `finally` path; and
12. return the dispatcher's integer unchanged.

A long-running command may remain inside `DispatchAsync` until the host
application-stopping token is signalled. This design does not add retries,
parallel dispatch, batching, or an execution queue.

Program Kit does not catch a consumer exception merely to invent an exit code.
A consumer such as JTest that declares an internal-failure code implements that
mapping inside its own dispatcher boundary.

## Parser stability

For the same Open Console input, these generated files remain exactly as they
are:

- `ProgramKitGenerated/Commands/GeneratedConsoleParser.cs`
- `ProgramKitGenerated/Commands/GeneratedConsoleParseResult.cs`

Implementation must add golden SHA-256 checks for the current fixture outputs
before changing the renderer. Any changed byte is a stop condition unless a
separate approved parser-contract change supersedes this design.

## Lock and evidence

The artifact-manifest document revision must survive parsing and become an
explicit input to host generation. The existing resolver continues to verify
the Open Console bytes against that revision before generation.

Console generation adds:

- a versioned Console dispatch lock binding the host, shell, Open Console
  document, host generator, and generated dispatcher-contract revisions; and
- deterministic evidence binding the generated interface path, registration
  method, required-resolution behavior, lifecycle order, parser and
  parse-result paths and SHA-256 digests, and exit-code pass-through policy.

Neither artifact records command arguments, option values, process output,
consumer evidence, services, exceptions, credentials, or secrets.

Identical shell, manifest, document, generator, and contract input bytes produce
identical paths and bytes. Changing the document or dispatcher contract changes
the corresponding lock/evidence digest. The generation receipt continues to
record every emitted output digest after atomic publication.

## Shell constraint

The current `dotnet-shell` v11 contract requires:

- at least one shell identity per host; and
- the base `CShells` package pinned to `0.0.28`.

This review set does not change that ABI. A plain command may select zero
feature activations and therefore needs no CShells feature package; its
consumer services are registered through the Console composition hook.

Making base CShells optional would require a separate versioned shell-contract
migration and is deliberately deferred.

## Compatibility and migration

The generated interface signature, file path, partial registration method,
startup order, exact return behavior, lock/evidence schemas, document-revision
binding, parser bytes, and base-shell constraint are versioned compatibility
surfaces.

Implementation must:

- create an explicit revision for the generated dispatcher contract;
- version any changed generation-input or lock schema;
- update serialization contexts and schema discovery;
- add migration and compatibility evidence where an existing serialized
  contract changes;
- retain old parser behavior and declared parse exit codes; and
- keep generated runtime dependency scans free of Program Kit design-time
  packages.

## Acceptance evidence

The review closes only when an isolated generated Console consumer proves:

- codes `0`, `1`, `2`, and `3` returned by its dispatcher become the exact
  process exit codes;
- the dispatcher receives canonical command, options, and arguments;
- invalid usage still returns the Open Console parser's declared code without
  resolving or starting the host;
- help and completion still return their declared codes without dispatcher
  registration;
- missing dispatcher registration fails before a hosted-service probe runs;
- constructor-injected consumer services are available to the dispatcher;
- a zero-feature-activation Console host builds and dispatches without any
  CShells feature package;
- cancellation reaches the dispatcher through the application-stopping token;
- host stop is attempted after success, cancellation, and failure;
- generated applications reference no Program Kit generator/runtime tooling;
- current parser and parse-result fixture digests are unchanged; and
- two unchanged generation runs are path- and byte-identical.

The ordinary unit, conformance, exhaustive source-gate, Observatory fixture,
locked restore, strict Release build, package inspection, and deterministic
generation gates remain required.

## Deliberately absent

- JTest command or run-evidence implementation.
- Program Kit exit-code taxonomy beyond existing transport codes.
- Exception-to-exit-code mapping.
- Parser or Open Console grammar redesign.
- Runtime discovery or service location outside the composition root.
- A new Program Kit runtime dispatcher package.
- A base-CShells-optional shell contract.
- Any release, publish, deployment, promotion, or external consumer change.
