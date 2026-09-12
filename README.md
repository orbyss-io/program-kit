# Program Kit

Program Kit supplies reusable Spec Kit workflows and governance components for constitution-first,
architecture-governed software delivery. Its conversational front door turns an initial user prompt
into confirmed intent, a reviewable C4-aligned domain map, a ratified project constitution, a modular
architecture baseline, an ADR system, a quality system, and a governed roadmap of vertical feature
specifications. Program Kit is maintained independently from the application repositories that
consume it.

The executable behavior lives in Spec Kit extensions and a workflow. `program-kit` is only the
versioned distribution layer: it installs the governance extension, the .NET extension, the
governance template preset, and the bootstrap workflow as separate components.

Program Kit is the AI extension, not an application platform or a component runtime. The reusable
technical building blocks it understands are independently developed and released from
[`orbyss-io/dotnet-foundation`](https://github.com/orbyss-io/dotnet-foundation) and
[`orbyss-io/forms`](https://github.com/orbyss-io/forms), with localization maintained separately in
[`orbyss-io/localization`](https://github.com/orbyss-io/localization). Orbyss is a software factory
and AI consultancy; the Foundation, Forms, and Localization names describe reusable engineering
assets, not a platform product.

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
     https://github.com/orbyss-io/program-kit/releases/download/v0.11.0/Initialize-ProgramKit-0.11.0.cmd `
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
     https://github.com/orbyss-io/program-kit/releases/download/v0.11.0/Initialize-ProgramKit-0.11.0.sh \
     -o Initialize-ProgramKit.sh
   ```

2. Execute it:

   ```bash
   bash ./Initialize-ProgramKit.sh codex
   ```

The required argument is the Spec Kit integration ID. For example, use `claude` instead of `codex`
for Claude Code. Both launchers initialize the selected integration with Spec Kit's Python runtime, register all
four catalogs, apply the Spec Kit 1.0.1 workflow workaround, and install Program Kit. They do not
require a prewritten design. After installation, describe the intended project naturally to the
installed Program Kit bootstrap skill. It conducts adaptive intake, generates the canonical
C4-aligned domain map and confirmed contract, and provides the final one-line workflow command. Do
not bypass or lower execution policy, broadly unblock repository files, or grant unrestricted
execution.

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

Download and verify the full `program-kit-<version>.zip` release asset, extract it, then run the
release-owned updater from the consuming repository in a normal user-owned terminal:

```powershell
python C:\path\to\program-kit-0.11.0\scripts\upgrade_program_kit.py `
  --release-root C:\path\to\program-kit-0.11.0 `
  --target . `
  --integration codex
```

Replace `codex` with the repository's installed integration. The updater does not use catalogs or
the network. It validates that the extracted bundle, workflow, extensions, and preset all have the
same release version; takes an exclusive mutation lock; invokes every Spec Kit primitive
sequentially; resynchronizes an existing managed .NET baseline; runs sync check; and then compares
the bundle record, workflow manifest/registry, both extension manifests, preset manifest/registry,
and managed-baseline version. It reports success only when every value converges. Do not run
`workflow`, `extension`, `preset`, or `bundle` mutations concurrently with it.

If the target release changes the managed `Orbyss.Foundation.OpenApi.Exporter` pin while registered
consumer contracts still name the older version, the updater stops before mutation with `PKU110`.
It lists every affected contract and specification/planning/research file. Review that list, then
explicitly rerun the same command with:

```powershell
--accept-openapi-producer-pin-reconciliation
```

That opt-in applies the exact producer-pin changes atomically only after component installation
succeeds. It removes stale after-tasks readiness while retaining an invalidation audit and returns
`PKU111`, rather than claiming implementation readiness. Run `$speckit-analyze`, the Program Kit
architecture check, and the Program Kit implementation check for each feature named by the
diagnostic. Never bypass `PKA014` or reuse the prior analysis after planning evidence changes.

For a repository whose approved `bootstrap-decisions.json` names an older Program Kit version, the
updater preserves that immutable file and appends Accepted, SHA-256-bound version authority to
`.specify/governance/program-kit-upgrades.json`. Later governance validates the installed release
against that record; unrecorded version drift remains blocked.

This local-release path replaces the previous pair of remote `workflow update` and `bundle update`
commands. Besides depending on live catalog transport, Spec Kit can advance a bundle record while an
existing component remains old. Program Kit therefore does not treat a successful bundle message as
upgrade evidence.

Open the installed integration in the repository, invoke
`$speckit-program-kit-governance-bootstrap`, and describe what you want to build. Intake uses the
shipped Program Kit grilling skill in the same conversation: numbered questions, recommendations,
and rounds ordered by decision dependencies. Clearly applicable technical defaults are applied
automatically and summarized in the final review; questions focus on ambiguous intent, conflicting
requirements, and material choices. Program Kit will show the C4 System Context and Domain Context Map and bind
the confirmed result in `docs/architecture/bootstrap-intake.json`. It always finishes with this
single physical command line, which can be pasted into PowerShell, Command Prompt, Bash, or another
normal user-owned terminal from the repository root:

```text
specify workflow run program-kit-bootstrap --input "bootstrap_intake=docs/architecture/bootstrap-intake.json" --input "integration=auto"
```

To inspect the generated diagrams before confirming intake or approving a review gate, ask
`View the C4 projection` or invoke `$speckit-program-kit-governance-view-c4`. The installed skill
validates `workspace.dsl` against the canonical JSON map, uses pinned Structurizr Local on an
available localhost port starting at 8081, and keeps viewer-created state outside the repository.

To stress-test a plan, decision, or idea before acting on it, invoke
`$speckit-program-kit-governance-grilling`. The standalone skill works through a dependency-aware
design tree in question rounds and waits for shared understanding before executing the proposed
plan. Bootstrap intake reuses this interview method; the bootstrap workflow and lifecycle hooks do
not start a grilling session. No separately installed personal grilling skill is required.

To evaluate the installed intake interactively from a candidate checkout, use the
[documented interactive launcher command](tests/acceptance/intake-grilling.md)
in a fresh user-owned terminal. It sets up a disposable consumer, asks for your product idea,
and opens Codex for human Q&A. It preserves review evidence before cleanup and never starts
bootstrap. See [interactive intake acceptance](tests/acceptance/intake-grilling.md).

For an uninterrupted development bootstrap, explicitly opt in to automatic approval and
ratification:

```text
specify workflow run program-kit-bootstrap --input "bootstrap_intake=docs/architecture/bootstrap-intake.json" --input "integration=auto" --input "auto_approve_and_ratify=true"
```

This option applies to all three review decisions. The workflow still generates and validates each
hash-bound review packet, then records `approval_mode: automatic` in the assessment, constitution,
and final bootstrap evidence. Review those packets and their listed artifacts after completion. The
default remains `false`; omit the option when you want the workflow to pause at every gate.

If a Program Kit 0.6.8 run reached final approval but failed completion because architecture,
roadmap, and traceability disagree, do not edit approved files or resume that run's persisted old
workflow. Follow the fresh hash-bound recovery procedure in
[`docs/bootstrap-recovery.md`](docs/bootstrap-recovery.md); it updates Program Kit and starts a new
workflow run over the existing repository, so cleaning or reinitializing is unnecessary.

Program Kit prevents concurrent bootstrap runs from mutating the same governance artifacts. If a
hard-terminated process left an older run incorrectly recorded as `running`, the new run stops before
intake and prints the exact `--abandon-run <run-id>` recovery command. First verify that no live
`specify workflow` process still owns that run. The explicit recovery marks only that validated
Program Kit run `aborted`, appends historical evidence, and preserves its files; never edit or delete
workflow state JSON by hand.

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

Unless automatic approval and ratification was explicitly enabled at startup, the workflow pauses
three times for human review. Continue a paused run after reviewing its generated artifacts:

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

- `program-kit-bootstrap` workflow: validates and assesses the confirmed conversational intake and
  C4-aligned domain map, performs current research, drafts the
  project constitution with the core Spec Kit command, records human ratification as hash-bound
  evidence, creates the architecture baseline and decision backlog, evaluates tooling, creates the
  specification roadmap, and pauses at human review gates.
- `program-kit-governance` extension: supplies reusable bootstrap, ratification, and lifecycle-validation commands.
- `program-kit-dotnet` extension: supplies the default .NET runtime baseline and its separately
  invoked, reviewable repository sync command.
- `program-kit-governance-preset`: appends governance traceability to Spec Kit's feature, plan, and task templates.
- Mandatory hooks before and after `speckit.specify`, after `speckit.plan`, before
  `speckit.implement`, after `speckit.tasks`, and before and after constitution drafting to prevent
  unauthorized specification, regenerate the current ratification packet, and detect architecture drift.

Before every `speckit.specify`, Program Kit checks governance and automatically runs feature grilling
for the selected roadmap entry. The interview reuses settled facts, resolves material questions and
pauses for your confirmation of one concise feature brief before specification setup begins. Small
features can have a short review; uncertain features receive deeper questioning. Saved interviews
resume, and changes reopen affected decisions. The spec uses the confirmed brief and retains its
hash; missing or stale evidence blocks later checks and implementation preflight.

You can prepare a feature ahead of time with `$speckit-program-kit-governance-specification-intake`.
Bootstrap grilling supplies context but does not replace feature confirmation. After upgrading to
0.11.0, active specs need this intake before their next gated step: existing requirements can seed
the draft, but approval is never fabricated during upgrade. See the
[feature-intake contract](extensions/program-kit-governance/references/specification-intake.md).

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
the application-neutral `Orbyss.Foundation.Host` and its CShells/Nuplane composition model are adopted
unless intake explicitly opts out. Foundation, Forms, and Localization versions are pinned
independently from the Program Kit version. Approval does not restore packages or contact feeds. Feature projects reference
the smallest required building-block closure; business behavior remains consumer-owned.

ASP.NET Core Minimal APIs are the default built-in HTTP candidate. Each public operation owns stable
route and operation identity, authorization, wire contracts, validation, status/error schemas,
cancellation behavior, OpenAPI compatibility evidence, and traceability to its vertical slice.
Project-specific technology choices outside the approved bootstrap baseline remain Proposed until
their ADR is accepted.

Selecting the .NET profile adopts `Orbyss.Foundation.Host` by default and makes
`speckit.program-kit-dotnet.sync` available. The sync command scaffolds central build/package management,
safe managed-file synchronization, runnable-image staging, and release workflows. The generated application
image layers packages and configuration onto a digest-pinned application-neutral host; the host never parses release
metadata. A write requires the approved,
hash-bound bootstrap baseline (or a later Accepted override) and acknowledgement of the independently
pinned packages and NuGet sources; restore/build execution is separately authorized. This optional sync is not a
prerequisite for technology-neutral governance or proposed quality gates, and installing Program Kit alone
never creates .NET files. See the [building-block selection guide](extensions/program-kit-building-blocks/references/orbyss-building-blocks.md)
and its [machine-readable executable catalog](extensions/program-kit-building-blocks/references/orbyss-building-blocks.json).
The [deterministic selection and materialization contract](docs/building-block-selection.md) documents
the accepted consumer artifact, lock, direct-reference ownership, recovery, and public-availability gates.

Generated Program Kit state and managed engineering tooling share the `.program-kit/` root. The
operational scripts live in `.program-kit/eng/`; consumers should invoke them through the documented
entry points rather than edit them. Sync upgrades authenticated files from the former
`eng/program-kit/` location and removes that retired directory when it becomes empty, while preserving
unrelated consumer-owned content under `eng/`.

Authenticated browser applications adopt `bff-cookie-v1` by default and inherit the versioned
`program-kit-web-threat-model-v1` plus `program-kit-web-security-evidence-v1`. That assurance
baseline maps explicit attackers and threats to controls, classifies standards, drafts, formal
research, platform guidance, and local policy honestly, and identifies configurable defaults and
residual risks that still require project judgement. Governance rejects a browser baseline that
does not inherit those exact IDs.

## Development and release

Prepare the pinned project-local JSON Schema runtime once before validation:

```sh
python extensions/program-kit-governance/scripts/schema_runtime.py setup
```

The PowerShell suite uses uv's Spec Kit interpreter. If that differs from `python`, prepare its
cache too (Windows):

```powershell
& (Join-Path ((& uv tool dir).Trim()) 'specify-cli/Scripts/python.exe') extensions/program-kit-governance/scripts/schema_runtime.py setup
```

The suite only checks/reuses this runtime offline; it prints the exact setup command if missing.

The reusable `json_schema.py validate --schema PATH --input PATH` and `describe --schema PATH
--section '/$defs/record'` tools ship with the governance extension. Consumers use their installed
`.specify/extensions/program-kit-governance/scripts/` copy; this checkout can use its source or
an independently installed copy. See the extension's `references/json-schema-tools.md` for setup,
offline upgrades, reference restrictions, and local-edit protection. No global tool install is needed.

During development, run the bounded source-contract gate. It intentionally excludes browser,
packaging, clean-install, upgrade, and public-registry release gates:

```powershell
./scripts/Test-ProgramKit.ps1
```

When the candidate is explicitly ready to proceed toward publication, run the complete deterministic
suite from a normal user-owned terminal. On this Windows host Firefox remains CI-owned:

```powershell
./scripts/Test-ProgramKit.ps1 -Suite Release -Approved -BrowserEngines 'chromium,webkit'
```

The Release suite records its complete transcript under
`artifacts/release-validation-<version>.log`, so a Codex task can inspect the human-run result without
owning the long-running process.

The deterministic suites do not invoke a coding agent. Tests named for Codex validate integration
contracts and guarded harness behavior only. Paid live acceptance v2 is a separate, completely
optional local diagnostic: publishing must not prompt for it or record it as skipped.

V2 starts from the machine-bound receipt produced by the complete Release suite. A phase-specific,
interactive one-use authorization can run the real bootstrap once and seal a content-addressed
checkpoint. A separately authorized building-block phase copies that checkpoint and uses one Codex
session to adopt the reviewed Internal Forms Workspace selection; the supervisor owns registry
availability, restore, build, and deterministic validation. Repeating that diagnostic does not
repeat bootstrap. The worker never receives registry credentials.

See [`docs/live-bootstrap-acceptance.md`](docs/live-bootstrap-acceptance.md) for the authorization
and execution commands, evidence model, Windows Job Object isolation, and current scope. The legacy
combined `Test-LiveBootstrap.ps1 -Approved` entry point is retired.

Build all release artifacts:

```powershell
uv run --with "specify-cli==1.0.1" python ./scripts/build_release.py
```

Pushing a SemVer tag matching `VERSION` creates a GitHub release. Follow
[`docs/releasing-0.11.0.md`](docs/releasing-0.11.0.md).

```powershell
git tag v0.11.0
git push origin v0.11.0
```

The release workflow validates all manifests and catalog metadata, creates deterministic ZIP files and SHA-256 checksums, generates GitHub build-provenance attestations, and publishes the assets. The CI and release actions are pinned to immutable commits; Dependabot proposes action updates.

## Release assets

- `program-kit-<version>.zip`: Program Kit's catalog-backed, pinned bundle manifest.
  It also contains `scripts/upgrade_program_kit.py`, the supported sequential offline/local-release
  updater for existing installations.
- `program-kit-governance-<version>.zip`: standalone governance extension package.
- `program-kit-dotnet-<version>.zip`: standalone .NET capability extension package.
- `program-kit-governance-preset-<version>.zip`: standalone governance template preset.
- `program-kit-bootstrap-<version>.zip`: standalone bootstrap workflow package.
- `Initialize-ProgramKit-<version>.sh`: copyable Bash initializer for Linux, macOS, and WSL.
- `Initialize-ProgramKit-<version>.cmd`: Windows initializer compatible with PowerShell
  `AllSigned` environments because it is a command script, not a PowerShell script.
- `SHA256SUMS`: exact artifact digests.
- `release-receipt-<version>.json`: clean source, successful deterministic Release steps,
  toolchains, browser matrix, public-availability proof, and exact candidate artifact hashes used by
  optional live acceptance.

Verify a downloaded artifact:

```powershell
gh attestation verify program-kit-0.11.0.zip --repo orbyss-io/program-kit
Get-FileHash program-kit-0.11.0.zip -Algorithm SHA256
```

## UI experience and public discovery

Browser projects can adopt the versioned [UI experience profile](extensions/program-kit-governance/references/ui-experience-v1.md)
through `/speckit.program-kit-governance.ui`. It separates layout, branding (including optional SVG
logos and Lucide/custom icons), semantic tokens, CSS adapters, page intent, public metadata and
consent-gated analytics. Generated native HTML is a reference renderer; accepted frontend frameworks
retain ownership through an initial-render adapter. The optional `Orbyss.Foundation.Web.Discovery` NuGet
feature serves an explicit public projection through CShells, without adding logic to the Host.

Consumer-owned profile/content inputs generate reproducible, conflict-protected outputs. Core
tests cover contrast, SVG safety, metadata/private-export boundaries, browser accessibility and
keyboard/reflow behavior. [Evidence and implementation status](docs/ui-experience-plan.md) distinguish
automated evidence from consumer journey, screen-reader and deployment acceptance.

Forms and localization are supplied by the independently versioned
[`orbyss-io/forms`](https://github.com/orbyss-io/forms) and
[`orbyss-io/localization`](https://github.com/orbyss-io/localization) repositories. Program Kit retains
the knowledge needed to choose their semantic contracts, compiler, runtime, authoring, operations,
storage, MCP, and Angular/React/Vue packages without compiling their source. The consumer still owns
field meaning, business validation, authorization, persistence durability, workflow, and publication
policy. Program Kit compatibility changes therefore update only selection knowledge, templates, and
consumer-facing checks; implementation and release tests remain in the owning component repository.

## License

Program Kit is open source under the [MIT License](LICENSE).
