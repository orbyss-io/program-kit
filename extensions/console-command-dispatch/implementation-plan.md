# Program Kit generated Console command dispatch implementation plan

Status: ready for validation and human review
Plan identity: `pkid:plan:program-kit:console-command-dispatch@1.0.0`
Owner: `pkid:domain:program-kit:toolkit`

## Design binding

This plan implements only the exact canonical design:

`pkid:design:program-kit:console-command-dispatch@1.0.0#sha256:21afb73f5abc636f23a5fe0357d226bd04dc0697d280a18f3d2ace2ae3be6046`

Any changed dispatcher signature, parser byte, registration model, lifecycle
order, shell constraint, lock/evidence meaning, or consumer-ownership boundary
is a material architectural deviation and stops implementation for renewed
human review.

## Requirements

| ID | Required outcome |
| --- | --- |
| `PKCCD-R001` | Generate one internal host-local `IProgramKitConsoleCommandDispatcher` with the exact successful parse, cancellation, and `ValueTask<int>` contract. |
| `PKCCD-R002` | Return the dispatcher's integer unchanged from `Program.Main`; Program Kit adds no consumer exit-code mapping. |
| `PKCCD-R003` | Provide one consumer-owned partial composition hook and require DI registration on the successful-command path. |
| `PKCCD-R004` | Resolve before host start, start once, dispatch once, pass application-stopping cancellation, and stop in `finally`. |
| `PKCCD-R005` | Preserve existing parser and parse-result output bytes for unchanged Open Console input. |
| `PKCCD-R006` | Carry and validate the exact Open Console document revision through backed generation. |
| `PKCCD-R007` | Emit versioned deterministic lock and evidence that record the dispatcher seam and its exact source revisions without runtime values. |
| `PKCCD-R008` | Preserve ordinal output ordering, atomic publication, and byte-identical unchanged regeneration. |
| `PKCCD-R009` | Permit zero feature activations and no CShells feature package while retaining dotnet-shell v11's shell identity and base CShells 0.0.28 constraints. |
| `PKCCD-R010` | Keep generated runtime consumers free of Program Kit generator/tooling packages and satisfy the mandatory C# source gate. |
| `PKCCD-R011` | Prove exact process exit codes, canonical parsed values, nondispatch behavior, missing registration, lifecycle, cancellation, and constructor injection in an isolated generated consumer. |
| `PKCCD-R012` | Reconcile schemas, serialization, migrations, fixtures, package evidence, guidance, and final verification without changing JTest or claiming release authority. |

## Work units

### PKCCD-W010 — Revision, lock, and evidence contracts

Required outcomes:

1. Introduce one exact Program Kit-owned revision for the generated Console
   dispatcher contract.
2. Preserve the artifact-manifest `DocumentRevision` in
   `DotNetHostGenerationInput`; validate the canonical Open Console bytes
   against that revision before rendering.
3. Add versioned Console dispatch lock and evidence models/schemas that bind
   host, shell, document, generator, dispatcher contract, output paths,
   parser/parse-result digests, registration requirement, lifecycle, and
   pass-through policy.
4. Register new contracts in exact JSON contexts/schema modules and include
   explicit migration/compatibility evidence for every changed serialized
   Program Kit contract.
5. Add stable diagnostics for missing, mismatched, unsupported, or stale
   document/dispatch revisions. Do not add a runtime command error taxonomy.

Allowed edits:

- `schemas/dotnet/**`
- `src/Orbyss.ProgramKit.DotNet/Documentation/**`
- `src/Orbyss.ProgramKit.DotNet/Generation/**`
- `src/Orbyss.ProgramKit.DotNet/Locks/**`
- `src/Orbyss.ProgramKit.DotNet/Diagnostics/**`
- `src/Orbyss.ProgramKit.DotNet/Composition/**`
- `src/Orbyss.ProgramKit.CommandLine/Operations/DotNet/**`
- corresponding unit tests, schema tests, migrations, fixture inputs, and
  version-selection evidence

Verification:

- schema and semantic validators accept exact new instances and reject missing,
  extra, stale, and mismatched fields;
- command-line generation rejects an Open Console revision whose digest does
  not match the resolved bytes;
- serialization round trips are canonical and deterministic;
- no lock/evidence artifact contains command values, process output, secrets,
  exceptions, or consumer evidence; and
- existing API and Worker generation contracts remain compatible.

Stop conditions:

- stop if the artifact manifest ceases to own document integrity;
- stop if the shell lock is made dependent on runtime command values;
- stop if a schema change is made without an explicit revision/migration; or
- stop if document verification requires network, feed, or ambient discovery.

### PKCCD-W020 — Generated dispatch and lifecycle

Depends on: `PKCCD-W010`

Required outcomes:

1. Generate
   `ProgramKitGenerated/Commands/IProgramKitConsoleCommandDispatcher.cs` as one
   internal interface with the exact approved signature.
2. Add the optional consumer implementation point
   `ConfigureProgramKitConsoleServices(IServiceCollection)` to the existing
   generated partial `Program` composition root.
3. Preserve parse failure, help, and completion as early nondispatch returns.
4. On `InvokeCommand == true`, render existing registrations, invoke the
   consumer hook, build the host, resolve the required dispatcher before start,
   start once, dispatch once, stop in `finally`, and return the exact integer.
5. Pass `IHostApplicationLifetime.ApplicationStopping` without adding a second
   cancellation owner.
6. Emit the W010 lock/evidence projections in deterministic ordinal output
   order.

Allowed edits:

- `src/Orbyss.ProgramKit.DotNet/Generation/DotNetHostSourceRenderer.cs`
- narrowly introduced Console dispatch compiler/renderer interfaces and
  implementations under `src/Orbyss.ProgramKit.DotNet/Generation/**`
- `src/Orbyss.ProgramKit.CommandLine/Composition/**` only where constructor
  injection is required for a new renderer collaborator
- focused renderer, compiler, and generation coordinator tests

Verification:

- generated contract compiles with a consumer-owned implementation and
  constructor-injected service;
- absent registration fails before a hosted-service start probe;
- codes are not clamped, mapped, or overwritten;
- start/dispatch/stop order and exactly-once dispatch are observed;
- WebApplication-backed Console health composition and Generic Host Console
  composition both compile and follow the same dispatch semantics;
- generated sources pass the exact source gate; and
- `GeneratedConsoleParser.cs` and `GeneratedConsoleParseResult.cs` fixture
  SHA-256 values remain at their W010 baselines.

Stop conditions:

- stop if the dispatcher requires publicizing or changing the parse-result
  record;
- stop if consumer registration needs reflection, assembly scanning, static
  state, or a runtime Program Kit package;
- stop if missing registration can still return `0`; or
- stop if lifecycle behavior requires a consumer-domain policy decision.

### PKCCD-W030 — Isolated process and compatibility proof

Depends on: `PKCCD-W020`

Required outcomes:

1. Add one isolated generated Console consumer fixture with consumer-owned
   dispatcher, composition partial, ordinary constructor-injected service, and
   no Program Kit generator/tooling project or package reference.
2. Use an Open Console document declaring command outcomes `0`, `1`, `2`, and
   `3`; invoke the built executable and prove each dispatcher result is the
   exact process exit code.
3. Prove canonical command, option, and argument delivery.
4. Prove parse/usage failure and information output retain declared codes and
   do not resolve or start consumer services.
5. Add a negative generated consumer with no dispatcher registration and a
   hosted-service start probe; prove required resolution fails first and no
   silent success occurs.
6. Prove application-stopping cancellation reaches a long-running dispatcher
   and bounded stop is attempted after success, cancellation, and exception.
7. Prove a Console host with one shell identity, empty feature activations, and
   only base CShells plus consumer packages dispatches successfully.

Allowed edits:

- `tests/Orbyss.ProgramKit.ConformanceTests/Fixtures/ConsoleCommandConsumer/**`
- `tests/Orbyss.ProgramKit.ConformanceTests/DotNet/**`
- focused unit test support under
  `tests/Orbyss.ProgramKit.UnitTests/DotNet/**`
- fixture manifests and local project/package references required solely for
  the isolated proof

Verification:

- generated fixture builds under strict warnings and source gate;
- process assertions observe exact exit values `0`, `1`, `2`, and `3`;
- dependency scans reject DotNet, Workbench, CommandLine, Development,
  Planning, and other design-time Program Kit assemblies from the generated
  runtime closure;
- missing registration, duplicate registration, cancellation, exception,
  hosted-service ordering, and deterministic generation are negative-tested;
  and
- existing FastEndpoints dispatcher conformance remains green.

Stop conditions:

- stop if the fixture imports JTest code or semantics beyond generic integer
  outcome examples;
- stop if test success depends on hand-editing ProgramKitGenerated files;
- stop if a feature package is required for the plain service dispatch proof;
  or
- stop if process-exit behavior is inferred rather than observed.

### PKCCD-W040 — Fixture reconciliation and closure

Depends on: `PKCCD-W030`

Required outcomes:

1. Reconcile DotNet and CommandLine guidance, fixture manifests, evidence
   inventories, migration maps, package catalogs, and generator revision
   references with the exact implemented seam.
2. Extend Observatory generation evidence only where needed to prove new output
   determinism and document binding; do not claim its hand-composed runnable
   Console host is the dispatcher proof.
3. Run the complete locked restore, format, strict non-incremental Release
   build, mandatory source-gate self-validation, unit, ordinary conformance,
   exhaustive source-gate, Observatory fixture, deterministic generation,
   isolated consumer, pack, package-content, license, lock, and redaction
   checks.
4. Record exact commands, outcomes, source commit, and final artifact digests.
   Do not create a release, publish packages, modify JTest, or mark its work
   units complete.

Allowed edits:

- `src/Orbyss.ProgramKit.DotNet/README.md`
- `src/Orbyss.ProgramKit.CommandLine/README.md`
- `fixtures/observatory-scheduling/**` only for generated artifact/evidence
  reconciliation
- `extensions/console-command-dispatch/**` validation and implementation
  evidence
- exact repository manifests, solution/project inventory, package metadata,
  and migration/version maps required by implemented files

Verification:

- all W010-W030 focused checks pass from current source;
- unchanged Console generation is byte-identical across two clean output roots;
- parser and parse-result fixture baselines remain unchanged;
- all repository-owned test and package gates pass with zero warnings;
- clean status contains only intended review/implementation artifacts; and
- review evidence distinguishes design approval, implementation completion,
  consumer unblock availability, and release state.

Stop conditions:

- stop on any parser-byte drift, runtime generator dependency, nondeterministic
  output, warning, source-gate failure, schema/migration gap, package-content
  drift, or unredacted runtime value;
- stop if closure would require networked consumer changes, package
  publication, release qualification, or deployment; or
- stop if the implementation differs materially from the approved design or
  plan digest.

## Dependency order

```text
PKCCD-W010 → PKCCD-W020 → PKCCD-W030 → PKCCD-W040
```

No work unit may run in parallel because every later unit consumes exact
contract or evidence bytes from its predecessor.

## Deliberately deferred

- Base-CShells-optional Console hosts and a dotnet-shell v12 migration.
- JTest dispatcher implementation or JTest work-unit updates.
- Package publication, release qualification, promotion, or deployment.
- A universal command bus, handler registry, retry policy, exception mapper, or
  background dispatch runtime.

## Approval and implementation stop

This plan is not approved by its creation or validation. Implementation may
begin only after the human explicitly approves the exact canonical design and
canonical plan digests. Any subsequent byte change invalidates that approval
until the human reviews the new digests.
