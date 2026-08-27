# Program Kit

Program Kit supplies reusable Spec Kit workflows and governance components for constitution-first,
architecture-governed software delivery. Its first workflow turns an initial design into a ratified
project constitution, modular architecture baseline, ADR system, quality system, and governed roadmap
of vertical feature specifications. Program Kit is maintained independently from the application
repositories that consume it.

The executable behavior lives in a Spec Kit workflow. The bundle is the versioned distribution layer around that workflow and its governance extension.

## Install in a new repository

Prerequisites:

- Spec Kit `1.0.1` or a compatible `1.x` release.
- A supported coding-agent integration.
- Trust in this repository's catalog and release contents. Inspect them before marking the extension catalog install-allowed.

From the root of a new repository, initialize Spec Kit and register the three Program Kit catalogs:

```powershell
specify init . --integration codex --non-interactive

specify extension catalog add `
  https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/extensions.json `
  --name program-kit `
  --install-allowed

specify workflow catalog add `
  https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/workflows.json `
  --name program-kit

specify bundle catalog add `
  https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/bundles.json `
  --id program-kit `
  --policy install-allowed

# Spec Kit 1.0.1 workaround: preinstall the catalog workflow before the bundle.
specify workflow add program-kit-bootstrap
specify bundle install program-kit
```

Replace `codex` with the integration you use. The bundle itself is integration-agnostic.

### Spec Kit 1.0.1 compatibility note

Spec Kit 1.0.1's bundle adapter incorrectly routes a catalog workflow ID through its local-development installer. Preinstalling `program-kit-bootstrap` as shown above is the tested workaround: the bundle then recognizes the pinned workflow and installs the governance extension. Until Spec Kit fixes the adapter, remove the workflow separately with `specify workflow remove program-kit-bootstrap` if you uninstall the bundle.

### Upgrade an existing Program Kit installation

With Spec Kit 1.0.1, the catalog workflow is installed separately from the bundle and must be updated first. Run both commands consecutively from the consuming repository, in this exact order:

```powershell
specify workflow update program-kit-bootstrap
specify bundle update program-kit --integration codex
```

Replace `codex` with the repository's installed integration. Do not run the bootstrap or any Program Kit governance command between these two updates. Program Kit validates the installed workflow registry, workflow manifest, extension manifest, and bundle records before governance work; a mixed-version installation stops with these repair commands before reading the initial design or mutating governance state.

Run the architecture bootstrap with the path to your initial design:

```powershell
specify workflow run program-kit-bootstrap `
  --input initial_design=./initial-design.md `
  --input integration=auto
```

### Codex Desktop on native Windows

Spec Kit 1.0.1 runs every Codex workflow command step by starting a new `codex exec` process. If the outer `specify workflow run` command is first attempted inside Codex Desktop's preferred Windows `elevated` sandbox, that nested CLI cannot use its protected Codex home/state or initialize its app-server client.

Keep the elevated sandbox enabled. Ask Codex to use the installed `speckit-program-kit-governance-bootstrap` skill, or explicitly ask it to run the outer Program Kit command outside the current task sandbox before the first attempt. Approve only this exact prefix:

```text
specify workflow run program-kit-bootstrap
```

You may select **Always allow** for that exact prefix after reviewing it. Do not allow the broader `specify workflow` prefix. Workflow resume is intentionally excluded so assessment, constitution, and bootstrap verdicts remain explicit human decisions.

Program Kit includes a reviewable template at `.specify/extensions/program-kit-governance/templates/codex/program-kit-bootstrap.rules`; it never copies the template into your Codex configuration or enables it. If you manually add a rules file, restart Codex. The ordinary PowerShell fallback is to run the full workflow command above from a terminal in the repository root. WSL, other operating systems, non-Codex integrations, and direct terminal use do not require this exception. See [Codex Desktop on native Windows](docs/codex-desktop-windows.md) for diagnosis, setup, and unsafe non-solutions.

The workflow pauses three times for human review. Continue a paused run after reviewing its generated artifacts:

```powershell
specify workflow status
specify workflow resume <run-id> --input assessment_verdict=approve
specify workflow resume <run-id> --input constitution_verdict=ratify
specify workflow resume <run-id> --input bootstrap_verdict=approve
```

In a new Codex session, you can simply provide this README and your initial design, then ask Codex to install the bundle and run `program-kit-bootstrap`.

## What it installs

- `program-kit-bootstrap` workflow: inventories the design, performs current research, drafts the
  project constitution with the core Spec Kit command, records human ratification as hash-bound
  evidence, creates the architecture baseline and decision backlog, evaluates tooling, creates the
  specification roadmap, and pauses at human review gates.
- `program-kit-governance` extension: supplies reusable bootstrap and validation commands.
- Mandatory hooks before and after `speckit.specify`, after `speckit.plan`, before
  `speckit.implement`, and after implementation to prevent unauthorized specification and detect
  architecture drift.

## Governance model

- The project constitution is the highest governance artifact. It is not a feature specification.
  Drafting revokes stale ratification; only the dedicated human gate and a matching SHA-256 marker
  make it authoritative.
- Project-specific architecture decisions require a human-approved ADR before becoming `Accepted`.
- Technologies discovered in an initial design begin as `Proposed`; mentioning a technology does not accept it.
- Generic engineering guardrails apply by default and are revalidated against current primary sources and project context during every bootstrap.
- The reusable software language is `Identity + Intent + Context -> Policies -> Decision -> Transition -> Effects -> Admission -> Outcome`.
- Required admission and optional observation are separate contracts. Invisible fire-and-forget behavior and ambiguous empty policy results are forbidden.
- `docs/architecture/specification-roadmap.md` is the governed portfolio of candidate feature
  specifications, not application work. At least one entry must be Ready before `speckit.specify`.
- Design tasks resolve architecture gaps and unlock roadmap entries; they do not enter
  `speckit.implement` as feature work.

## Vertical slices and modularity

- Deliver meaningful behavior as an actor, trigger, or intent carried to an observable verified
  outcome rather than as controller/service/repository/frontend phases.
- Bounded contexts and modules own language, contracts, data, and dependency boundaries. Features
  are runtime composition units; shells are runtime isolation contexts; endpoints are transport
  adapters.
- Peer module and feature implementations do not reference one another. Collaboration uses owned
  contracts, ports, events, or query APIs.
- Concrete inheritance is not an automatic feature-reference exception. A genuine feature-family
  extension requires the same owner and release lifecycle, an explicitly designed extension
  contract, an Accepted ADR, and an architecture-test allowlist.

### .NET profile

The .NET profile maps these generic rules to project and assembly boundaries. It evaluates CShells
and CShells.AspNetCore when runtime feature composition, per-shell or per-tenant isolation,
configuration-driven feature sets, or dynamic activation are required. Feature projects reference
the abstraction packages; only the host references the full runtime.

ASP.NET Core Minimal APIs are the default built-in HTTP candidate. Each public operation owns stable
route and operation identity, authorization, wire contracts, validation, status/error schemas,
cancellation behavior, OpenAPI compatibility evidence, and traceability to its vertical slice.
Technology adoption remains Proposed in each consuming repository until its ADR is accepted.

Selecting the .NET profile unlocks the profile-gated `speckit.program-kit-governance.dotnet-sync`
command. It scaffolds central build/package management, safe managed-file synchronization, application-bundle
creation, and release workflows. Program Kit Host runs the resulting immutable ZIP in a digest-pinned layered
container; installing Program Kit alone never creates .NET files. See `docs/dotnet-runtime.md`.

## Development and release

Run the local source checks and disposable install test:

```powershell
./scripts/Test-ProgramKit.ps1
./scripts/Test-LocalInstall.ps1
```

Build all release artifacts:

```powershell
uv run --with "specify-cli==1.0.1" python ./scripts/build_release.py
```

Pushing a SemVer tag matching `VERSION` creates a GitHub release. For the repository, NuGet, and GHCR release checklist, follow `docs/releasing-0.4.1.md`:

```powershell
git tag v0.4.1
git push origin v0.4.1
```

The release workflow validates all manifests and catalog metadata, creates deterministic ZIP files and SHA-256 checksums, generates GitHub build-provenance attestations, and publishes the assets. The CI and release actions are pinned to immutable commits; Dependabot proposes action updates.

## Release assets

- `program-kit-<version>.zip`: installable Program Kit bundle.
- `program-kit-governance-<version>.zip`: standalone governance extension package.
- `program-kit-bootstrap-<version>.zip`: standalone bootstrap workflow package.
- `SHA256SUMS`: exact artifact digests.

Verify a downloaded artifact:

```powershell
gh attestation verify program-kit-0.4.1.zip --repo orbyss-io/program-kit
Get-FileHash program-kit-0.4.1.zip -Algorithm SHA256
```

## License

Program Kit is open source under the [MIT License](LICENSE).
