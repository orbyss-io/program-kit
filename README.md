# Orbyss Program Kit

Orbyss Program Kit is an open-source, domain-neutral toolkit for building
software from explicit, typed definitions. It provides deterministic mechanics
for contracts, validation, code generation, host composition, evidence, and
repeatable development workflows without prescribing what an application's
domain means.

The project currently targets .NET 10 and is in alpha. It can be used on its
own, as a Git submodule, through its .NET packages, or through its command-line
tooling.

## Choose your path first: consumer or contributor

Program Kit is set up two different ways. Pick the right one before running
anything:

- **Consumer** — you are building your own software *with* Program Kit (its
  packages, CLI, or as a submodule). Continue with
  [Install Program Kit CLI (consumer)](#install-program-kit-cli-consumer) below;
  you install the CLI and run
  `program-kit capabilities initialize --provider <claude|codex>`.
- **Contributor** — you are working *on* Program Kit's own source in a clone of
  this repository. Follow [CONTRIBUTING.md](CONTRIBUTING.md) instead. This is a
  source **authoring workspace** (it carries
  `.agent-capabilities/authoring-workspace.json`), so the consumer commands
  `capabilities initialize`, `capabilities read`, `capabilities catalog`, and
  `dotnet materialize-console-inputs` intentionally **fail closed** here. There
  is no consumer CLI install step; the only capability available is the
  contributor-only `author-and-maintain-skills`, wired up by hand as
  CONTRIBUTING.md describes.

**AI agents setting up this workspace:** check for
`.agent-capabilities/authoring-workspace.json`. If it exists you are in the
contributor workspace — use [CONTRIBUTING.md](CONTRIBUTING.md) and do not attempt
consumer initialization. If it is absent, this is a consumer workspace.

### Branch lifecycle for Program Kit-guided work

Both contributor and consumer repositories should enable their hosting
platform's automatic merged-head-branch deletion setting (GitHub calls it
`delete_branch_on_merge`). Program Kit treats every non-default branch as
short-lived: after its tip is proven reachable from the updated default branch,
delete the merged remote branch and its clean, inactive local branch/worktree.

Never delete a default or protected branch, an unmerged branch, a dirty branch,
or a branch attached to active work. If repository settings or permissions
cannot perform the cleanup, report the exact retained branch and its unique
commits instead of forcing deletion.

## Install Program Kit CLI (consumer)

Program Kit packages are published on
[NuGet.org](https://www.nuget.org/packages?q=Orbyss.ProgramKit).
The easiest consumer path is the
[`Orbyss.ProgramKit.CommandLine`](https://www.nuget.org/packages/Orbyss.ProgramKit.CommandLine)
.NET global tool. The coordinated `0.1.0-alpha.3` release requires the .NET 10
SDK selected by [`global.json`](global.json). A consumer does not need a
Program Kit checkout, submodule, local feed, or separate CapabilityBundle
installation.

Install the exact tool version directly from NuGet.org:

```powershell
dotnet tool install --global Orbyss.ProgramKit.CommandLine `
  --version 0.1.0-alpha.3
```

From the human-led consumer workspace root, initialize the provider that is
actually running the session:

```powershell
program-kit capabilities initialize --provider codex --workspace-root .
# Claude Code instead:
program-kit capabilities initialize --provider claude --workspace-root .
```

Tool installation alone does not initialize a provider, activate a capability,
start work, or grant authority. Initialization installs only thin trigger
wrappers and an exact ownership lock. The installed CLI retains the canonical
read-only capability knowledge and verifies it before every read.

Inspect an existing installation or replace it with the exact version—never an
ambient `latest`:

```powershell
dotnet tool list --global
dotnet tool update --global Orbyss.ProgramKit.CommandLine `
  --version 0.1.0-alpha.3
program-kit --help
program-kit capabilities catalog --workspace-root . --format text
```

The remaining `Orbyss.ProgramKit.*` packages are available from the same
NuGet.org feed for exact-version `PackageReference` use.

As a source-based alternative, download **Source code (zip)** for the matching
tag from [GitHub Releases](https://github.com/orbyss-io/program-kit/releases),
extract it, and follow
[Build an isolated local feed from source](#build-an-isolated-local-feed-from-source)
below. The release ZIP is useful for an offline or independently built local
feed; ordinary consumers can install the global tool directly from NuGet.org.

### Build an isolated local feed from source

This is a contributor/test journey, not the ordinary consumer installation
path above. From a Program Kit source checkout, create a new output directory
containing the exact coordinated package closure with:

```powershell
.\build\Invoke-PackConsumerFeed.ps1 `
  -OutputRoot C:\tmp\orbyss-program-kit-0.1.0-alpha.3
```

The script reads [`build/program-kit-release-packages.json`](build/program-kit-release-packages.json),
performs one locked restore and one Release build, then performs one bounded
parallel aggregate pack with restore and build disabled. It fails closed on
package-selection, identity, version, dependency, or content drift and
publishes nothing. On success, use the `feed` child directory as the local
NuGet source; `package-manifest.json` and `SHA256SUMS` bind the exact output.
`OutputRoot` must not already exist, so a failed or repeated invocation cannot
silently replace prior package evidence.

After the package-installed cold proof passes, create the deterministic
downloadable ZIP, outer checksum, manifest, and JTest prompt from that exact
feed:

```powershell
.\build\New-ConsumerFeedHandoff.ps1 `
  -ConsumerFeedRoot C:\tmp\orbyss-program-kit-0.1.0-alpha.3 `
  -OutputRoot C:\tmp\orbyss-program-kit-0.1.0-alpha.3-handoff
```

The archive retains `feed/` as its documented local NuGet source and includes
the package manifest, internal checksums, and prompt. The handoff script
rechecks every package byte and fails without output on any mismatch; it does
not publish or modify a release.

The manifest records each project's direct first-party source references.
Ordinary library packages project those references as exact first-party nuspec
dependencies. The self-contained .NET tool and build-integration packages
carry their required implementation closure and must expose no first-party
nuspec dependencies; analyzer and capability-bundle packages have no source
dependency closure. The feed still carries all release-selected public Program
Kit packages as one coordinated set.

### Fresh clone of a consumer repository

A repository built with Program Kit owns whether its AI-provider bindings are
absent, contributor-local, or committed. Its README should state one of the
[`none`, `local-optional`, or `repository-managed` postures](.agent-capabilities/consumer-integration.md)
and pin the exact Program Kit CLI acquisition path.

After a fresh clone:

1. Provide the exact pinned Program Kit packages: install the tool as above,
   or restore the repository-local feed the consumer's `NuGet.Config` maps
   `Orbyss.ProgramKit.*` to.
2. Run `dotnet tool restore` when the repository pins the CLI in a
   `dotnet-tools.json` manifest.
3. For `local-optional`, explicitly run
   `program-kit capabilities initialize --provider <codex|claude>
   --workspace-root .`. For `repository-managed`, verify the committed
   wrappers and lock with `capabilities preflight`; reinitialize only after an
   explicit version change or exact migration. For `none`, do neither.
4. Re-run any materialization the repository records (for example
   `program-kit dotnet materialize-console-inputs <request> --workspace-root .
   --output <directory> --build-consumer`) before regenerating or verifying a
   generated host.

`program-kit capabilities preflight <capability> --workspace-root .` verifies
that the selected repository-managed or local-optional state matches the exact
installed CLI and recorded bytes. Program Kit does not edit `.gitignore`,
stage files, commit files, or silently select a posture.

## Why it exists

Software generation is most useful when the same accepted input produces the
same reviewable output, failures are explicit, and generated code remains
ordinary code that developers can inspect and own. Program Kit provides that
shared foundation:

- typed, versioned contracts instead of loosely interpreted templates;
- deterministic validation and generation with stable diagnostics;
- explicit package, provider, protocol, and tool revisions;
- generated evidence that records what was selected and produced;
- domainless building blocks that other projects can specialize safely;
- development capabilities whose authority remains with the human using them.

Program Kit deliberately separates mechanics from meaning. It can understand
how to compose a .NET host, bind typed configuration, generate an OpenAPI
client, or project an authentication protocol without inventing domain roles,
business policies, deployment intent, or production secrets.

## What is included

The implemented baseline includes:

- artifact, architecture, planning, quality, approval, and development
  contracts;
- modularity, model-first `System.Text.Json` serialization, tasks, in-process
  execution, and scheduling;
- deterministic Workbench operations and a command-line interface;
- .NET API, console, worker, Aspire AppHost, FastEndpoints, Dev Container, and
  OpenAPI client generation;
- typed configuration, Options, secret-reference, telemetry, transport-failure,
  authentication, authorization, and local Keycloak fixture mechanics;
- local package preparation and application publishing;
- a strict repository-owned C# source gate;
- an Observatory Scheduling fixture that proves the domain-neutral baseline.

Some host-tooling extensions are still being completed. Their review artifacts
and tests distinguish implemented, incomplete, and deferred behavior.

## How it works

Program Kit follows a small, predictable pipeline:

1. A caller supplies a typed, versioned definition.
2. Program Kit validates identity, compatibility, completeness, and policy.
3. A selected operation deterministically produces source code, configuration,
   manifests, or another bounded artifact.
4. The operation records diagnostics and integrity evidence.
5. The consumer builds, tests, reviews, and runs the generated result using the
   normal tools for that ecosystem.

Runtime libraries do not load AI instructions, capability prose, repository
state, or ambient provider configuration.

## Get started

Prerequisites:

- Git;
- the exact .NET SDK selected by [`global.json`](global.json);
- Docker only for explicitly selected container-backed integration proofs.

Clone Program Kit directly:

```powershell
git clone https://github.com/orbyss-io/program-kit.git
cd program-kit
dotnet restore ProgramKit.sln --configfile NuGet.Config --locked-mode
dotnet build ProgramKit.sln -c Release --no-restore
dotnet test --solution ProgramKit.sln -c Release --no-build --no-restore --minimum-expected-tests 1
```

`global.json` selects Microsoft Testing Platform. Test commands that name an
input must use `--solution`, `--project`, or `--test-modules`; a positional
path is not the MTP contract. Do not pass the legacy `--maxcpucount` switch to
`dotnet test`: it can build successfully and then discover zero tests. Run a
serialized `dotnet build --maxcpucount:1` separately, followed by
`dotnet test --no-build`, when serialized compilation is required.

When Program Kit is embedded as a submodule, initialize it while cloning:

```powershell
git clone --recurse-submodules <consumer-repository-url>
```

For an existing clone or a checkout created without recursive submodules:

```powershell
git submodule sync --recursive
git submodule update --init --recursive
git -C program-kit rev-parse HEAD
```

The final command prints the exact Program Kit commit pinned by the consumer
repository. Run `git submodule update --init --recursive` again after switching
branches or pulling a parent commit that changes that pin. Do not independently
pull the submodule when reproducibility matters.

## Using the development capabilities

The consumer CLI carries six available provider-neutral capabilities:
`develop-software`, `design-software`, `design-csharp-build-gate`,
`implement-software-plan`, `maintain-software`, and
`publish-dotnet-application-locally`. Codex and Claude wrappers contain only
trigger metadata plus exact `capabilities preflight` and `capabilities read`
commands. Canonical procedures and supporting resources are not copied into
the consumer workspace.

Useful discovery commands are:

```powershell
program-kit capabilities catalog --workspace-root . --format text
program-kit capabilities preflight design-software --workspace-root .
program-kit capabilities read design-software --workspace-root .
program-kit capabilities read-resource software-change-troubleshooting --workspace-root .
program-kit schemas list --format text
program-kit commands describe dotnet.generate-host --format text
program-kit commands describe dotnet.materialize-console-inputs --format text
program-kit diagnostics explain PKCG005 --format text
program-kit csharp-gate describe-definition --format text
```

Reads fail closed on a missing/stale lock, wrong CLI version, incomplete
knowledge closure, modified wrapper, unsupported provider, or Program Kit
authoring marker. Re-run the explicit initializer to refresh owned wrappers;
it preserves another reviewed provider and refuses human-modified or unowned
files without partial writes.

Consumer products choose and document `none`, `local-optional`, or
`repository-managed`; Program Kit does not force setup. Exact removal is also
human-started:

```powershell
program-kit capabilities uninitialize --provider codex --workspace-root .
```

Codex wrappers use `.agents/skills`; `.codex/skills` is exact legacy migration
input only. See
[consumer integration postures](.agent-capabilities/consumer-integration.md)
for selective Git guidance and the complete authority boundary.

### Package-only Console host journey

A Console consumer first retrieves the complete installed guide and its
compiling examples. A schema alone describes document structure; it does not
carry the project topology, handler/validator seam, ownership rules, authority,
or ordered commands:

```powershell
program-kit capabilities read-resource dotnet-console-input-materialization-guide --workspace-root .
program-kit capabilities read-resource dotnet-console-integration-project-example --workspace-root .
program-kit capabilities read-resource dotnet-console-integration-source-example --workspace-root .
program-kit schemas read pkid:schema:program-kit:dotnet-console-input-materialization-request@0.1.0-alpha.1
```

The supported seam is one consumer-owned `net10.0` integration class library,
separate from the generated host. It contains the public request types,
`I<Command>Handler` interfaces, optional validator interfaces and validation
result, public sealed implementations, one public sealed `IShellFeature`, and
the exact unkeyed scoped registrations. A contracts-only/implementation split
is not supported and must return to design.

After restoring that exact project under the consumer repository's package
policy, the installed CLI builds it without restore, evaluates its complete
reference-assembly closure, validates the seam, and transactionally owns the
materialized output:

```powershell
program-kit dotnet materialize-console-inputs console-input-request.json `
  --workspace-root . `
  --output .program-kit/console-inputs `
  --build-consumer
program-kit dotnet generate-host console `
  --shell .program-kit/console-inputs/shell.json `
  --host <EXACT_CONSOLE_HOST_ID> `
  --artifact-manifest .program-kit/console-inputs/artifact-manifest.json `
  --output generated/Example.Console
program-kit dotnet verify-host --root generated/Example.Console
```

Agents may edit the consumer-owned integration source and semantic request
under the active human authority. They must never edit Program Kit-owned
materialized or generated bytes; change the source/request and rerun the
backed operation instead.

Program Kit itself uses repository-frozen contributor guidance, never
CLI-returned consumer capabilities as authoring authority. Runtime packages
never load capability prose or provider configuration.

## Explore the repository

- [Final baseline review](artifacts/final/final-review-report.md)
- [Final topology and closure evidence](artifacts/final/README.md)
- [Self-hosted comparison](artifacts/self-hosted/README.md)
- [Observatory Scheduling fixture](fixtures/observatory-scheduling/README.md)
- [CLI commands](src/Orbyss.ProgramKit.CommandLine/README.md)
- [.NET generation contracts](src/Orbyss.ProgramKit.DotNet/README.md)
- [Dev Container generation](src/Orbyss.ProgramKit.DevContainers/README.md)
- [Capability bundle](src/Orbyss.ProgramKit.CapabilityBundle/README.md)
- [Historical bootstrap authority](bootstrap/README.md)

## License

Program Kit is available under the [MIT License](LICENSE). Vendored schemas,
test vectors, and pinned third-party dependencies retain their own notices and
licenses where applicable.
