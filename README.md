# Program Kit

Program Kit supplies reusable Spec Kit workflows and governance components for constitution-first,
architecture-governed software delivery. Its first workflow turns an initial design into a ratified
project constitution, modular architecture baseline, ADR system, quality system, and governed roadmap
of vertical feature specifications. Program Kit is maintained independently from the application
repositories that consume it.

The executable behavior lives in Spec Kit extensions and a workflow. `program-kit` is only the
versioned distribution layer: it installs the governance extension, the .NET extension, the
governance template preset, and the bootstrap workflow as separate components.

## Install in a repository

Prerequisites:

- Spec Kit `1.0.1` or a compatible `1.x` release.
- The coding-agent tooling required by the selected Spec Kit integration; `specify init` validates
  it (for example, `codex` for Codex or `claude` for Claude).
- Git, available as the `git` command.
- Python, available as the `python` command. The Python Spec Kit resolver also requires
  `PyYAML>=6,<7` in that exact interpreter.
- Trust in this repository's catalog and release contents. Inspect them before marking the extension catalog install-allowed.

> **Codex execution boundary:** Run every command in this installation section, every Program Kit
> update, and the outer `specify workflow run program-kit-bootstrap ...` command yourself from a
> normal user-owned PowerShell or WSL terminal. Do not ask a Codex Desktop task or an interactive
> `codex` CLI agent to run them. Agent-run setup can create `.agents` and `.specify` under a sandbox
> identity on Windows, and the outer workflow would also cause nested `codex exec` execution.

The repository does not need to be empty. Existing source, documentation, an initial design, and an
existing Spec Kit initialization are allowed. The initializer refreshes Spec Kit's Codex integration
with the Python script flavor but does not delete unrelated project files. The directory must
already be inside an initialized Git work tree. Otherwise, the initializer stops before dependency
installation or repository setup and prints `git init` and `git status` for the user to run. Spec Kit may refresh files that it owns or scaffolds. If the initializer detects an existing or partial Program Kit
installation, it stops before running `specify`; use the update commands instead.

Run these steps from the repository root.

### Windows

1. Download the Windows command initializer:

   ```powershell
   Invoke-WebRequest `
     https://github.com/orbyss-io/program-kit/releases/download/v0.6.10/Initialize-ProgramKit-0.6.10.cmd `
     -OutFile Initialize-ProgramKit.cmd
   ```

2. Execute it from a normal user-owned PowerShell prompt:

   ```powershell
   .\Initialize-ProgramKit.cmd codex
   ```

The command script works in Windows environments that enforce PowerShell `AllSigned` because it is
not a PowerShell script.

### Bash on Linux, macOS, or WSL

1. Download the Bash initializer:

   ```bash
   curl -fL \
     https://github.com/orbyss-io/program-kit/releases/download/v0.6.10/Initialize-ProgramKit-0.6.10.sh \
     -o Initialize-ProgramKit.sh
   ```

2. Execute it:

   ```bash
   bash ./Initialize-ProgramKit.sh codex
   ```

The required argument is the Spec Kit integration ID. For example, use `claude` instead of `codex`
for Claude Code. Both launchers initialize the selected integration with Spec Kit's Python runtime, register all
four catalogs, apply the Spec Kit 1.0.1 workflow workaround, and install Program Kit. They do not
require, create, locate, or assume a filename for the initial design. When starting the bootstrap,
pass the user-chosen design path through `--input initial_design=...`. Do not bypass or lower
execution policy, broadly unblock repository files, or grant unrestricted execution.

Initialization resolves the advertised release through immutable tag catalogs, then switches all
four registrations to the trusted `main` update channel. Catalog entries continue to pin component
downloads to immutable release tags, while later `workflow update` and `bundle update` commands can
discover newer Program Kit releases.

Before changing repository-managed files, each launcher verifies that `specify`, `python`, and Git can
execute. Spec Kit validates the coding-agent tooling for the selected integration. The launcher
checks whether that same `python` can import PyYAML and, only when needed,
uses `python -m pip` to install `PyYAML>=6,<7`. If pip is unavailable or the import still fails, the
initializer stops with a dependency-specific error.

Codex workers require a Git work tree. Program Kit intentionally fails early when Git is not
initialized instead of changing repository history implicitly or passing `--skip-git-repo-check`
to Codex.

The equivalent manual sequence is:

```powershell
specify init . --force --non-interactive --integration codex --script py

specify extension catalog add `
  https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/extensions.json `
  --name program-kit `
  --install-allowed

specify preset catalog add `
  https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/presets.json `
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
specify bundle install program-kit --integration codex
```

Replace `codex` with the integration you use in both initialization and bundle installation. The
bundle itself is integration-agnostic.

Keep all four catalogs registered. In Spec Kit 1.0.1, even a locally supplied third-party bundle
archive resolves its extension, preset, and workflow primitives through their catalogs; the bundle
is the pinned composition record, not a self-contained primitive installer. The standalone ZIP
assets remain useful for inspecting or installing one component deliberately.

### Spec Kit 1.0.1 compatibility note

Spec Kit 1.0.1's bundle adapter incorrectly routes a catalog workflow ID through its local-development installer. Preinstalling `program-kit-bootstrap` as shown above is the tested workaround: the bundle then recognizes the pinned workflow and installs the governance extension. Until Spec Kit fixes the adapter, remove the workflow separately with `specify workflow remove program-kit-bootstrap` if you uninstall the bundle.

### Upgrade an existing Program Kit installation

With Spec Kit 1.0.1, the catalog workflow is installed separately from the bundle and must be updated first. Run both commands consecutively from the consuming repository, in this exact order:

```powershell
specify workflow update program-kit-bootstrap
specify bundle update program-kit --integration codex
```

Installations created by Program Kit 0.6.9 or earlier used immutable release-tag catalog
registrations. Before their first upgrade, replace those four registrations once:

```powershell
$catalogRoot = 'https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs'
specify extension catalog remove program-kit
specify preset catalog remove program-kit
specify workflow catalog remove 0
specify bundle catalog remove program-kit
specify extension catalog add "$catalogRoot/extensions.json" --name program-kit --install-allowed
specify preset catalog add "$catalogRoot/presets.json" --name program-kit --install-allowed
specify workflow catalog add "$catalogRoot/workflows.json" --name program-kit
specify bundle catalog add "$catalogRoot/bundles.json" --id program-kit --policy install-allowed
```

Replace `codex` with the repository's installed integration. Do not run the bootstrap or any Program Kit governance command between these two updates. Program Kit validates the installed workflow registry, workflow manifest, extension manifest, and bundle records before governance work; a mixed-version installation stops with these repair commands before reading the initial design or mutating governance state.

Run the architecture bootstrap with the path to your initial design:

```powershell
specify workflow run program-kit-bootstrap `
  --input initial_design=./path/to/your-design.md `
  --input integration=auto
```

If a Program Kit 0.6.8 run reached final approval but failed completion because architecture,
roadmap, and traceability disagree, do not edit approved files or resume that run's persisted old
workflow. Follow the fresh hash-bound recovery procedure in
[`docs/bootstrap-recovery.md`](docs/bootstrap-recovery.md); it updates Program Kit and starts a new
workflow run over the existing repository, so cleaning or reinitializing is unnecessary.

### Codex Desktop, CLI agents, and native Windows

The outer lifecycle belongs to the human's normal shell. Spec Kit starts a new `codex exec` process
for each Codex workflow command step; those workers remain sandboxed. Starting the outer workflow
from an existing Desktop or interactive CLI agent instead nests Codex execution.

On native Windows, there is an additional ownership risk. OpenAI documents that the preferred
elevated sandbox uses dedicated lower-privilege users and filesystem permission boundaries. If that
identity performs initialization or installation, it can own generated `.agents`, `.specify`, and
related paths. A later sandbox refresh may then fail to apply its protective ACL boundary, including
with `SetNamedSecurityInfoW ... error 5`. Rerunning init alone does not repair existing ownership.

The installed `speckit-program-kit-governance-bootstrap` skill is guidance-only: it displays the
complete command for the user to copy into normal PowerShell or WSL, then stops. It never runs the
outer workflow, requests an agent exception, or installs an approval rule. See
[Program Kit bootstrap from Windows and Codex](docs/codex-desktop-windows.md) for official OpenAI
background, the supported sequence, and a conservative clean start that preserves `.git` unless the
human explicitly chooses a new repository.

The workflow pauses three times for human review. Continue a paused run after reviewing its generated artifacts:

- Gate 1/3: assessment approval (`approve`)
- Gate 2/3: constitution ratification (`ratify`)
- Gate 3/3: final bootstrap approval (`approve`)

```powershell
specify workflow status
specify workflow resume <run-id> --input assessment_verdict=approve
specify workflow resume <run-id> --input constitution_verdict=ratify
specify workflow resume <run-id> --input bootstrap_verdict=approve
```

After normal-shell installation, Codex Desktop can use the installed skills for ordinary repository
work. If asked about bootstrap, it should display the command for the human to run rather than
orchestrating setup itself.

## What it installs

- `program-kit-bootstrap` workflow: inventories the design, performs current research, drafts the
  project constitution with the core Spec Kit command, records human ratification as hash-bound
  evidence, creates the architecture baseline and decision backlog, evaluates tooling, creates the
  specification roadmap, and pauses at human review gates.
- `program-kit-governance` extension: supplies reusable bootstrap, ratification, and lifecycle-validation commands.
- `program-kit-dotnet` extension: supplies the default .NET runtime baseline and its separately
  invoked, reviewable repository sync command.
- `program-kit-governance-preset`: appends governance traceability to Spec Kit's feature, plan, and task templates.
- Mandatory hooks before and after `speckit.specify`, after `speckit.plan`, before
  `speckit.implement`, after `speckit.tasks`, and before constitution drafting to prevent unauthorized
  specification and detect architecture drift.

The preset deliberately uses the Spec Kit `append` strategy, so it augments rather than replaces
the core templates. If a consumer needs a durable project-specific template, use the project's
`.specify/templates/overrides/` layer; it has higher precedence and is not managed by Program Kit
updates. Workflow overlays remain the appropriate mechanism for changing a workflow's steps locally.

## Governance model

- The project constitution is the highest governance artifact. It is not a feature specification.
  Drafting revokes stale ratification; only the dedicated human gate and a matching SHA-256 marker
  make it authoritative.
- Explicit intake choices, applicable versioned Program Kit defaults, safe derived defaults, and
  reviewed overrides are adopted together by the hash-bound assessment gate and recorded in one
  Accepted bootstrap-baseline decision. Examples and future options remain candidates.
- Project-specific architecture decisions outside that reviewed baseline require a human-approved
  ADR before becoming `Accepted`.
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

The .NET profile maps these generic rules to project and assembly boundaries. When .NET is selected,
`ProgramKit.Host` and its application-bundle/CShells composition model are adopted automatically
unless intake explicitly opts out. The assessment packet prominently discloses its pinned preview
packages and preview sources; approval does not restore packages or contact feeds. Feature projects
reference abstraction packages; only the host references the full runtime.

ASP.NET Core Minimal APIs are the default built-in HTTP candidate. Each public operation owns stable
route and operation identity, authorization, wire contracts, validation, status/error schemas,
cancellation behavior, OpenAPI compatibility evidence, and traceability to its vertical slice.
Project-specific technology choices outside the approved bootstrap baseline remain Proposed until
their ADR is accepted.

Selecting the .NET profile adopts `ProgramKit.Host` by default and makes
`speckit.program-kit-dotnet.sync` available. The sync command scaffolds central build/package management,
safe managed-file synchronization, application-bundle creation, and release workflows. Program Kit Host
runs the resulting immutable ZIP in a digest-pinned layered container. A write requires the approved,
hash-bound bootstrap baseline (or a later Accepted override) and acknowledgement of its pinned preview
packages and NuGet sources; restore/build execution is separately authorized. This optional sync is not a
prerequisite for technology-neutral governance or proposed quality gates, and installing Program Kit alone
never creates .NET files. See `docs/dotnet-runtime.md`.

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

Pushing a SemVer tag matching `VERSION` creates a GitHub release. Follow
[`docs/releasing-0.6.10.md`](docs/releasing-0.6.10.md).

```powershell
git tag v0.6.10
git push origin v0.6.10
```

The release workflow validates all manifests and catalog metadata, creates deterministic ZIP files and SHA-256 checksums, generates GitHub build-provenance attestations, and publishes the assets. The CI and release actions are pinned to immutable commits; Dependabot proposes action updates.

## Release assets

- `program-kit-<version>.zip`: Program Kit's catalog-backed, pinned bundle manifest.
- `program-kit-governance-<version>.zip`: standalone governance extension package.
- `program-kit-dotnet-<version>.zip`: standalone .NET capability extension package.
- `program-kit-governance-preset-<version>.zip`: standalone governance template preset.
- `program-kit-bootstrap-<version>.zip`: standalone bootstrap workflow package.
- `Initialize-ProgramKit-<version>.sh`: copyable Bash initializer for Linux, macOS, and WSL.
- `Initialize-ProgramKit-<version>.cmd`: Windows initializer compatible with PowerShell
  `AllSigned` environments because it is a command script, not a PowerShell script.
- `SHA256SUMS`: exact artifact digests.

Verify a downloaded artifact:

```powershell
gh attestation verify program-kit-0.6.10.zip --repo orbyss-io/program-kit
Get-FileHash program-kit-0.6.10.zip -Algorithm SHA256
```

## License

Program Kit is open source under the [MIT License](LICENSE).
