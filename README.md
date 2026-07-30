# Orbyss Program Kit

Orbyss Program Kit is an open-source, domain-neutral toolkit for building
software from explicit, typed definitions. It provides deterministic mechanics
for contracts, validation, code generation, host composition, evidence, and
repeatable development workflows without prescribing what an application's
domain means.

The project currently targets .NET 10 and is in alpha. It can be used on its
own, as a Git submodule, through its .NET packages, or through its command-line
tooling.

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
dotnet test ProgramKit.sln -c Release --no-build --no-restore
```

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

Canonical, provider-neutral capability procedures live in
[`.agent-capabilities/capabilities/`](.agent-capabilities/capabilities/), and
their Program Kit availability is recorded by
[`INDEX.md`](.agent-capabilities/capabilities/INDEX.md). Inert provider-adapter
templates live under
[`.agent-capabilities/provider-adapters/`](.agent-capabilities/provider-adapters/).
Runtime packages never activate these files.

Cloning a repository, initializing a submodule, copying a capability, or
installing the capability bundle does **not** grant authority or start work.
A human explicitly requests each capability-backed task.

Consumer products choose and document one integration posture: `none`,
`local-optional`, or `repository-managed`. Program Kit does not infer that
choice, modify `.gitignore`, stage or commit files, install an AI provider
globally, or grant trust or permissions. See
[consumer integration postures](.agent-capabilities/consumer-integration.md)
for the exact CapabilityBundle `0.1.0-alpha.1` setup and removal commands, reviewed
Codex and Claude Code project roots, multi-provider ownership behavior, and
selective Git guidance.

The complete provider contract and extension checklist remain in
[the provider-adapter guide](.agent-capabilities/provider-adapters/README.md).
An output-folder convention alone is not an adapter.

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
