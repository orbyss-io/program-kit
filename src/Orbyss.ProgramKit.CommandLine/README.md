# Orbyss.ProgramKit.CommandLine

`program-kit` is a deterministic transport over explicitly registered Program
Kit operations. It never scans the current directory, a solution, assemblies,
or package feeds.

Install the exact `0.1.0-alpha.3` tool from the extracted Program Kit local
feed, then initialize the provider used by the current consumer session:

```powershell
dotnet tool install --global Orbyss.ProgramKit.CommandLine `
  --version 0.1.0-alpha.3 `
  --add-source <EXTRACTED_PROGRAM_KIT_HANDOFF>\feed
program-kit capabilities initialize --provider codex --workspace-root .
# or: program-kit capabilities initialize --provider claude --workspace-root .
```

No Program Kit checkout, submodule, or separate CapabilityBundle install is
required. Installation does not initialize a provider or grant capability
authority. Run `program-kit --help` or a command path followed by `--help` for
the exact finite grammar generated from the parser descriptors.

The consumer-journey additions are:

```text
program-kit capabilities initialize --provider <claude|codex> --workspace-root <dir>
program-kit capabilities catalog --workspace-root <dir> [--format text|json]
program-kit capabilities preflight <capability-id> --workspace-root <dir> [--format text|json]
program-kit capabilities read <capability-id> --workspace-root <dir>
program-kit capabilities read-resource <resource-id> --workspace-root <dir>
program-kit commands describe <command-key> [--format text|json]
program-kit schemas list [--format text|json]
program-kit schemas read <schema-id>@<version>
program-kit diagnostics explain <diagnostic-id> [--format text|json]
program-kit artifacts inspect <artifact> [--schema <exact-schema-id>] [--format text|json]
program-kit csharp-gate describe-definition [--format text|json]
program-kit csharp-gate materialize-definition <draft> --output <file>
program-kit dotnet materialize-console-inputs <request> --workspace-root <dir> --output <dir> --build-consumer
```

Every command also accepts `--diagnostics text|json`. Exit codes are `0` for
success, `1` for conformance failure, `2` for usage/input/I/O failure, and `3`
for an unexpected internal failure.

Operation adapters are registered from an explicit finite sequence. Duplicate
exact command keys fail before a dictionary can erase the conflict. Commands
without a selected operation adapter fail closed with `PKCLI004`.

The standalone composition backs exact-schema validation, model-less
canonical normalization/digest, and API/Console/Worker host generation.
The installed tool embeds the exact six-capability consumer closure: canonical
definitions, Codex/Claude trigger templates, supporting resources, registered
schema modules, and digest-bound catalogs. Initialization verifies those
package-owned bytes and transactionally renders only
`.codex/skills/<capability>/SKILL.md` or
`.claude/skills/<capability>/SKILL.md`, plus the multi-provider ownership lock
at `.program-kit/capabilities.lock.json`. The wrappers call back into
`capabilities preflight/read`; they contain no canonical procedure or source
checkout pointer.

Every read verifies exact CLI/bundle/manifest versions, resource closure,
provider registration, lock evidence, and owned wrapper bytes. A second
provider is preserved. Unowned or modified files, stale versions, incomplete
closure, and the Program Kit authoring marker fail closed. Reads never repair
state. There is no knowledge mutation or export command; resistance to a
malicious same-user edit of the installed executable itself requires an
external OS read-only installation boundary.
Host generation requires `hostDocuments[]` in the artifact manifest, binding
each selected host identity to one exact integrator-document revision. This
keeps shell and document digests independently verifiable and avoids inferred
file naming.

Before authoring a Console integration, retrieve
`dotnet-console-input-materialization-guide`,
`dotnet-console-integration-project-example`, and
`dotnet-console-integration-source-example` with `capabilities read-resource`.
The complete guide—not the request schema alone—defines the supported
consumer-owned seam and ordered workflow.

`dotnet materialize-console-inputs` accepts one explicit semantic request and
one already-restored consumer `net10.0` integration class library. That one
project contains the public request and `I<Command>Handler` contracts,
optional validator/result contract, public sealed implementations, one
parameterless `IShellFeature`, and exact unkeyed scoped registrations. A
contracts-only project split is refused. With explicit `--build-consumer`
authority, the command builds only that project with `--no-restore`, evaluates
`TargetRefPath` and `ReferencePathWithRefAssemblies`, validates the complete
seam, and transactionally materializes the digest-bound Console input closure.
It never scans a solution/feed/cache or edits consumer source.

`dotnet generate-host console` consumes only that materialized closure. It
verifies the ownership lock and every materialized byte and projects the exact
consumer integration project reference. Successful generation emits the
complete executable Spectre Console project: entry point, command tree, typed
settings, request factories, validation, service-registration audit, and exact
project/package references. Spectre is the sole command parser. Handler
integers become process exit codes unchanged; parse, validation, cancellation,
and internal failures use the document-declared host roles. Help and static
completion do not compose consumer services.

Agents may edit the consumer-owned integration source and semantic request
under human-started authority. They must never edit the Program Kit-owned
materialization directory or generated host; change consumer inputs and rerun
the backed command.

`dotnet refresh-host` reads a committed, version-exact generation request. It
creates an absent host, reports byte-identical output without touching it, and
atomically replaces only a valid generated host. Drift fails closed. The
explicit `--repair-generated-output` authority moves drift to a
digest-addressed sibling quarantine before regeneration. `--preview` reports
the deterministic disposition without changing the host.
`--build-consumer` is the only refresh mode permitted to invoke the finite
approved C# build profile, and refresh never upgrades Program Kit.

Generated hosts reference the exact private
`Orbyss.ProgramKit.GeneratedOutputIntegrity.Build` integration. It verifies the
source tree before compilation and emits a required intermediate attestation;
publication verifies source independently. There is no runtime source-tree
verification and no generated pre-parser: pinned Spectre.Console.Cli remains
the sole runtime parser and typed binder for generated .NET Console hosts.

Foreign-client generation accepts one explicit local JSON OpenAPI document and
one explicit `Microsoft.OpenApi.Kiota` package archive. The reviewed tool
manifest, package archive, entry assembly, version, language, and options must
all match exactly. The operation rejects external `$ref` values and publishes
only a complete generated C# tree containing `kiota-lock.json` and
`program-kit.client-generation.json`. It performs no package download, feed
lookup, login, or ambient tool/cache discovery.

The C# build-gate commands are finite Workbench transports. Validation,
description, and rendering are data-only. The alpha.2 materializer accepts one
UTF-8 BOM at draft ingestion, rejects duplicate properties, validates the
exact embedded schema, stable-sorts finite collections, and writes canonical
BOM-free bytes without inventing a semantic or human value. Scaffolding is
transactional. Binding reads only an explicitly ordered local asset inventory
and performs no restore, feed lookup, discovery, or assembly load.
Verification selects one pinned build, test, pack, publish, or
generated-project-verification template; neither an executable nor arbitrary
arguments can be supplied. Successful evidence is promoted atomically after
receipt, exception-use, package-isolation, performance, and cancellation
checks. These commands do not approve a gate, an empty selection, a temporary
exception, or activation.
