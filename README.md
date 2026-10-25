# Program Kit

<!-- latest-published-release:start -->
Latest available release: **[v0.14.3](https://github.com/orbyss-io/program-kit/releases/tag/v0.14.3)**. Before installing, follow the [current installation instructions](#install-in-a-repository), including initializer corrections. [Check the latest release](https://github.com/orbyss-io/program-kit/releases/latest) for the kit version.
<!-- latest-published-release:end -->

Program Kit extends Spec Kit's ordinary **specify -> plan -> tasks -> implement -> test** flow
with applicable architectural knowledge, composition defaults and engineering checks. Plans and
tasks carry substantive choices; compiler/analyzer checks, architecture tests, contract generation
and behavioral tests enforce the software. A resumable product-intake skill establishes the foundation before the first feature.

Implementation keeps focused test-first feedback: run the operation's tests, expand through affected
dependencies when shared contracts or inputs change, and reserve complete application acceptance for
feature/domain closure or formal review handoff. Progress checkpoints do not trigger full acceptance.
One combined implementation preflight supplies concise applicable guidance; detailed references are
available on demand. Publication promotes a complete CI-qualified candidate; see the release procedure.

Application engineering lives in visible `eng/`, native project configuration and deployment
inputs. Builds, tests, contract generation and packaging do not need AI, installed extensions or
governance history. See [the consumer structure and removal classification](docs/consumer-engineering.md).

The executable behavior lives in Spec Kit extensions and focused scripts. `program-kit` is the
versioned distribution layer: it installs the governance, building-blocks and .NET extensions and
the governance template preset. Product founding runs in the current skill session.

Program Kit is the AI extension, not an application platform or a component runtime. The reusable
technical building blocks it understands are independently developed and released from
[`orbyss-io/dotnet-foundation`](https://github.com/orbyss-io/dotnet-foundation) and
[`orbyss-io/forms`](https://github.com/orbyss-io/forms), with localization maintained separately in
[`orbyss-io/localization`](https://github.com/orbyss-io/localization). Orbyss is a software factory
and AI consultancy; the Foundation, Forms, and Localization names describe reusable engineering
assets, not a platform product.

## Install in a repository

Prerequisites:

- Spec Kit `1.1.1` or a compatible newer `1.x` release. The repository's candidate
  qualification workflow records the exact Spec Kit pin used for CI and release validation.
- The coding-agent tooling required by the selected Spec Kit integration; `specify init` validates
  it (for example, `codex` for Codex or `claude` for Claude).
- Git, available as the `git` command.
- Python, available as the `python` command. The Python Spec Kit resolver also requires
  `PyYAML>=6,<7` and Spec Kit's dependency-range parser `packaging>=23` in that exact interpreter.
- Trust in this repository's catalog and release contents. Inspect them before marking the extension catalog install-allowed.

> **Codex execution boundary:** Run every command in this installation section, every Program Kit
> update yourself from a
> normal user-owned PowerShell or WSL terminal. Do not ask a Codex Desktop task or an interactive
> `codex` CLI agent to run them. Agent-run setup can create `.agents` and `.specify` under a sandbox
> identity on Windows. After normal-shell setup, product-intake runs in the existing session.

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
     https://github.com/orbyss-io/program-kit/releases/download/v0.14.3/Initialize-ProgramKit-0.14.3.cmd `
     -OutFile Initialize-ProgramKit.cmd
   ```

2. Execute it from a normal user-owned PowerShell prompt:

   ```powershell
   .\Initialize-ProgramKit.cmd codex
   ```

The command script works in Windows environments that enforce PowerShell `AllSigned` because it is
not a PowerShell script.

The Windows initializer resolves native executable paths automatically, including the persisted
Windows user/machine PATH when CMD cannot find a tool. If a tool is installed in a custom location,
set `$env:PROGRAM_KIT_SPECIFY`, `$env:PROGRAM_KIT_GIT`, or `$env:SPECKIT_PYTHON` to its full executable
path in this terminal before running the initializer. It prints the selected paths and retains the
underlying command errors. Installation failures identify the stage and exit code; preserve that
output and the partial installation for diagnosis.

### Bash on Linux, macOS, or WSL

1. Download the Bash initializer:

   ```bash
   curl -fL \
     https://github.com/orbyss-io/program-kit/releases/download/v0.14.3/Initialize-ProgramKit-0.14.3.sh \
     -o Initialize-ProgramKit.sh
   ```

2. Execute it:

   ```bash
   bash ./Initialize-ProgramKit.sh codex
   ```

The required argument is the Spec Kit integration ID. For example, use `claude` instead of `codex`
for Claude Code. Both launchers initialize the selected integration with Spec Kit's Python runtime, register all
three catalogs and install Program Kit. They do not
require a prewritten design. After installation, describe the intended project naturally to the
installed Program Kit product-intake skill. It establishes connected product intent, constitution,
consequential ADRs, technology choices, domain/C4 map and outcome roadmap, then continues directly
to the selected first feature intake. Do
not bypass or lower execution policy, broadly unblock repository files, or grant unrestricted
execution.

Initialization resolves the advertised release through immutable tag catalogs, then switches all
three registrations to the trusted `main` update channel. Catalog entries continue to pin component
downloads to immutable release tags, while later bundle updates can
discover newer Program Kit releases.

The initializer records actual native generation inputs and interpreter selection
for later ownership checks. Preserve `.specify/program-kit/render-profiles` with
the installation. Historical comparison uses those original inputs independently
of current PATH readiness; an unrecorded historical alias remains unresolved.

Before changing repository-managed files, each launcher verifies that `specify`, `python`, and Git can
execute. Spec Kit validates the coding-agent tooling for the selected integration. The launcher
checks whether that same `python` has `packaging>=23`, reporting its exact-interpreter preparation
command if missing. It checks the loaded PyYAML version against `>=6,<7` and, only when needed,
uses `python -m pip` to install `PyYAML>=6,<7`. If pip is unavailable or the range check still fails, the
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

specify bundle catalog add `
  https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs/bundles.json `
  --id program-kit `
  --policy install-allowed

specify bundle install program-kit --integration codex
```

Replace `codex` with the integration you use in both initialization and bundle installation. The
bundle itself is integration-agnostic.

Keep all four catalogs registered. A locally supplied third-party bundle
archive resolves its extension and preset primitives through their catalogs; the bundle
is the pinned composition record, not a self-contained primitive installer. The standalone ZIP
assets remain useful for inspecting or installing one component deliberately.

### Spec Kit CLI baseline

Program Kit supports the unmodified public Spec Kit 1.1.1 baseline and compatible newer 1.x releases.
The current release qualification pins Spec Kit 1.1.3.
In your own terminal, upgrade an older shared user tool with
`uv tool install specify-cli==1.1.3 --force --no-python-downloads`, then verify
`specify version`. Component manifests require at least 1.1.1; CI and build examples use the exact
tested version.

### Device toolchain readiness

Agents pause dependent work when device tools differ from authoritative pins and provide
officially verified commands for your own terminal. Updates must persist across repositories
and fresh sessions, with supported SDK/runtime versions kept side by side. See the
[device toolchain policy and missing-manager setup](extensions/program-kit-governance/references/device-toolchain-policy.md),
including Windows `winget install Schniz.fnm`, persistent Node defaults and fresh-session
verification. Agents never run device installers or use repository-local tools to mask a mismatch.
The human-owned initializers run this check before repository setup, using their exact release
pins. If setup pauses, complete the printed device steps in your own terminal, refresh the session
and rerun initialization. The check is repeated whenever a later workflow requires different pins.
Contributor validation uses the exact Spec Kit pin already selected by
`.github/workflows/ci.yml`, which can be newer than the consumer compatibility minimum above.

### Upgrade an existing Program Kit installation

Use `speckit.program-kit-governance.upgrade` for a conversational, resumable consumer
upgrade. It assesses cumulative semantic changes against actual code, architecture,
customization and exact dependencies, preserves unchanged intent and saved tasks,
and records bounded scoped migrations. New defaults offer optional adoption.
The maintained [consumer upgrade method](extensions/program-kit-governance/references/consumer-upgrade.md)
prepares a separate worktree with owned ignored setup, delegates installation to the
updater below, and verifies destination activation with original-setup recovery.
Normal feature intake/planning scans relevant migrations without creating a feature
or approval dossier. Application builds remain independent of toolkit coordination.
The local sanitized evidence export sends nothing automatically.

Download and verify the full `program-kit-tooling-<version>.zip` release asset, extract it **outside the
consumer workspace** (for example `C:\ProgramKitReleases`), then run the
release-owned updater from the consuming repository in a normal user-owned terminal:

```powershell
python C:\path\to\program-kit-0.14.3\scripts\upgrade_program_kit.py `
  --release-root C:\path\to\program-kit-0.14.3 `
  --target . `
  --integration codex
```

Replace `codex` with the repository's installed integration. The updater does not use catalogs or
the network. It discovers and probes the installed Spec Kit CLI before importing its ownership
guards; where needed, plain `python` delegates to that CLI's exact interpreter. `PKU119` reports
an unavailable CLI runtime before mutation. It validates that the extracted bundle, extensions, and preset all have the
same release version; takes an exclusive mutation lock; invokes every Spec Kit primitive
sequentially; resynchronizes an existing managed .NET baseline; runs sync check; and then compares
the bundle record, three extension manifests and preset manifest/registry,
and managed-baseline version. It reports success only when every value converges. Do not run
`workflow`, `extension`, `preset`, or `bundle` mutations concurrently with it.

Use `--plan` for an inspectable migration preview. The same upgrade command installs, applies
mechanical migrations and verifies dependencies; `--offline` explicitly leaves network verification
pending. Tooling installation, migration verification, application correctness and release readiness
are reported separately. No bootstrap continuation, architecture worker or renewed fingerprint
approval is required. Current installation state is `.program-kit/installation/migration.json`;
owned attempt logs are ignored `artifacts/program-kit/runs/`. Interrupted retries preserve originals.

Program Kit upgrades preserve the consumer's accepted dependency profile, including its exporter
pin. New .NET projects use the qualified default in the installed building-block extension's
`references/dependency-profiles/index.json`. Scaffolding records that exact profile and the Draft
selection retains it even if a later Program Kit version changes its default. Profile qualification
scope is enforced during validation and acceptance; the historical v0.12.5 profile excludes Assurance
export adoption. The opt-in profile
`foundation-0.2.2-exporter-0.2.4-forms-0.2.0-localization-0.1.1` qualifies public
Exporter 0.2.4 with the retained runtime pins for its listed Authentication, BFF,
Assurance and Web activation closure. Its hashed receipt and profile ship offline
and as immutable release assets. Forms and Localization activation and consumer
Delivery acceptance remain outside that native qualification.

New projects use
`foundation-0.3.6-build-0.3.2-exporter-0.2.7-forms-0.2.1-localization-0.1.2`: Foundation
runtime/analyzer and host 0.3.6, Build 0.3.2, Exporter 0.2.7, Forms 0.2.1, and Localization
0.1.2. Native qualification covers the selected activation closures. Unchanged Forms/Localization
browser evidence retains its explicit historical disposition; no fresh browser qualification is inferred.
Publisher features excluded from OpenAPI composition are checked as metadata;
consumer compatibility and Delivery acceptance remain separate. Installing a
Program Kit upgrade preserves existing accepted and scaffold-captured profiles.
Adopting different dependencies still requires the reviewed dependency transition.

Every upgrade offers an optional software update review: keep current versions, review
qualified dependency profiles, or review all repository software, including packages,
toolchains, CI actions and container images. The conversational upgrade honors your choice;
the standalone updater prints the invitation and includes it in `--plan`. Opting into a
review produces a comparison of current and proposed stable versions, compatibility,
security and migration work. Choose which updates to adopt before changing pins or locks.
Keeping or deferring your current versions does not block the Program Kit installation.

Dependency changes use `dependency_profiles.py list`, then `draft --profile <id> --target .`.
Review the exact profile, preserved originals and proposed producer-contract/planning changes;
record an Accepted decision naming the profile and review SHA-256, then use `accept` with that
decision. Synchronize engineering pins, renew affected proofs and native locks, and verify the
consumer through the existing lifecycle. Completed acceptance retains later analysis and proof
history. These steps are separate from a Program Kit bundle upgrade.

Existing installations can explicitly adopt the repaired exporter while retaining their runtime
profile with `--accept-openapi-producer-pin-reconciliation`. Engineering producer pins change
atomically. Plans, tasks, ADRs, bootstrap history and historical analysis remain unchanged. The next
ordinary contract/build checks execute the changed producer; old results are not relabeled current.
Native lock/restore failures remain real diagnostics and do not reopen bootstrap.

Completed bootstrap stays completed. Uninstalled future providers and unfinished features are
reported separately from tooling migration. Actual provider transitions and registry/sandbox
permissions retain their scoped guards. Fix a reported failure and retry the same verified release
command. The operating-system upgrade lock releases after interruption without a manual terminal
handoff. Local history keeps the latest five completed owned runs, preserving failed/interrupted
runs until explicit cleanup; see the [cleanup preview](docs/consumer-engineering.md).

Retries bind the original installed version, archived inputs and exact target release.
An interrupted component installation can retain its exact archived prior migration receipt;
that receipt stays historical until the maintained updater writes new completion evidence.
Materialization must match the complete original or complete target, with current output and
selection checks. Changed originals, mixed locks, unknown selection changes and unfinished
transactions remain errors; an old attempt does not authorize a different upgrade.

Open the installed integration, invoke `$speckit-program-kit-governance-product-intake`, and
describe what you want to build. A rough idea and a thoroughly designed application are both valid
starting points. The skill extracts existing meaning and decisions, researches consequential
unknowns, uses Program Kit grilling to resolve contradictions, and applies supported defaults
transparently. It preserves supplied detail, provisional assumptions and due questions across
sessions in the existing product artifacts.

Review the connected product intent/journeys, constitution, consequential ADRs, technology radar,
canonical domain/C4 map, outcome roadmap and relevant Foundation capabilities/shell choices.
Intake confirmation establishes an accurate synthesis. Constitutional ratification and acceptance
of the exact named ADR/map scope remain separate explicit human decisions. Future proposals stay
provisional; accepted status or a hash does not prove runtime compatibility.

The skill uses focused installed helpers, including `bootstrap_intake.py`, `architecture_map.py`,
`governance_state.py` and `product_intake.py`. After explicit founding acceptance it continues
directly to `$speckit-program-kit-governance-specification-intake` for the selected first feature.
No assessment/research/backlog/closure dossier, authoring-worker stages, workflow completion or
pre-spec runtime matrix is required. A feasibility experiment belongs before specification only
when its answer changes what should be specified. Ordinary restore, provider/runtime, composition
and implementation checks remain due when their actual actions depend on them.

See [focused founding commands and acceptance](extensions/program-kit-governance/references/product-founding.md).
To inspect the generated diagrams, ask `View the C4 projection` or invoke
`$speckit-program-kit-governance-view-c4`. It validates map/projection freshness and uses pinned
Structurizr Local on localhost. Standalone `$speckit-program-kit-governance-grilling` also supports
stress-testing a plan, decision or idea in the same conversation.

For an explicitly requested fictional draft rehearsal, use
`$speckit-program-kit-governance-proxy-intake`. It preserves simulated answers and stops before
confirmation, founding acceptance and implementation. It supplies no consumer authority or paid
worker acceptance. [Interactive intake](tests/acceptance/intake-grilling.md) remains human-invoked.

The former `$speckit-program-kit-governance-bootstrap` entrypoint is a compatibility alias for
product-intake. The founding workflow and its run/resume/reopen routes are retired. Upgrades remove
owned active registration while preserving saved runs, proof bytes, accepted artifacts and locks.
Incomplete old workflows remain incomplete. Review useful current artifacts with product-intake;
never automatically restart or convert a consumer. Customized owned workflow files require owner
reconciliation before removal. Read-only historical completion inspection remains available.

### Codex Desktop and native Windows

Run initialization and toolkit installation/update from a normal user-owned PowerShell or WSL
terminal. Then use product-intake and ordinary feature skills inside the current Codex session;
founding does not launch an outer workflow or nested coding worker. Existing sandbox-owned path
problems still require ownership repair. See [Windows setup and skill-led founding](docs/codex-desktop-windows.md).

## What it installs

- `program-kit-governance` extension: ships product-intake, grilling, ratification, architecture,
  feature-intake and focused governance/engineering commands.
- `program-kit-building-blocks` extension: supplies qualified capability selection and explicit
  consumer ownership, placement and materialization contracts.
- `program-kit-dotnet` extension: supplies the default .NET runtime baseline and its separately
  invoked, reviewable repository sync command.
- `program-kit-governance-preset`: adds governance traceability to feature and plan templates, and
  replaces task generation and implementation with consistent operation-sized delivery guidance.
- Mandatory hooks before and after `speckit.specify`, after `speckit.plan`, before
  `speckit.implement`, after `speckit.tasks`, and before and after constitution drafting to prevent
  unauthorized specification, regenerate the current ratification packet, and detect architecture drift.

Before every `speckit.specify`, Program Kit checks applicable architecture and automatically runs feature grilling
for the selected feature within its roadmap epic. The interview reuses its preserved seed and settled facts, resolves material questions and
pauses for your confirmation of one concise feature brief before specification setup begins. Small
features can have a short review; uncertain features receive deeper questioning. Saved interviews
resume, and changes reopen affected decisions. The spec uses the confirmed brief and retains its
hash. Product confirmation remains distinct from mechanical workflow state. Applicable knowledge is
routed from scoped adopted targets before planning; canonical conditions and prohibitions survive the brief.
Declared graph checks require responsibility/effect/capability consistency; normal review establishes
semantic ownership. Retained feature-plan decisions resolve inside the reviewed plan without rewriting
approved bootstrap history. Engineering-command success reports its actual scope and is not overall acceptance.

You can prepare a feature ahead of time with `$speckit-program-kit-governance-specification-intake`.
Bootstrap grilling supplies context but does not replace feature confirmation. After upgrading to
0.11.0, active specs need this intake before their next gated step: existing requirements can seed
the draft, but approval is never fabricated during upgrade. See the
[feature-intake contract](extensions/program-kit-governance/references/specification-intake.md).

Bootstrap understands the supplied vision across architectural boundaries and creates roadmap epics
with agreed outcomes and priorities. Each epic can lead to several feature specifications. Detailed
user proposals survive as feature seeds, including boundary rationale, rules, examples and open
questions; sparse ideas can retain sparse seeds. Intended work and exploratory options remain
distinct. A recommended starting outcome does not automatically become the first specification's
complete scope. Feature intake reuses that seed, clarifies its useful delivery boundary and records
an independent feature confirmation, so another feature in the same epic cannot overwrite it.

The preset appends governance to constitution, specification and plan templates. It replaces
`speckit.tasks`, `tasks-template` and `speckit.implement` together so task generation and execution
agree on operation-sized outcomes, exact prerequisites, focused verification and compact resume
checkpoints. New task drafts validate their dependency maps; existing approved plans retain their
IDs, checked states and authority until a reviewed repair. Scoped verification exposes needed,
reusable and unresolved checks without weakening full acceptance or Release gates.
If a consumer needs a durable project-specific template, use the project's
`.specify/templates/overrides/` layer; it has higher precedence and is not managed by Program Kit
updates. Existing saved workflow history remains evidence; the retired founding workflow has no active overlay route.

## Governance model

- The project constitution is the highest governance artifact. It is not a feature specification.
  Drafting revokes stale ratification; only the dedicated human gate and a matching SHA-256 marker
  make it authoritative.
- Explicit intake choices, applicable versioned Program Kit defaults, safe derived defaults, and
  reviewed overrides are presented with the connected foundation. Explicit acceptance promotes only
  the named ADR/map scope. Examples, provisional assumptions and future options remain candidates.
- Project-specific architecture decisions outside that reviewed baseline require a human-approved
  ADR before becoming `Accepted`.
- Generic engineering guardrails apply by default and are revalidated against current primary sources and project context where a consequential founding or feature choice requires them.
- The reusable software language is `Identity + Intent + Context -> Policies -> Decision -> Transition -> Effects -> Admission -> Outcome`.
- Required admission and optional observation are separate contracts. Invisible fire-and-forget behavior and ambiguous empty policy results are forbidden.
- `docs/architecture/specification-roadmap.md` records epic outcomes, completion conditions,
  priorities and linked feature seeds. Domains, epics and specifications have distinct identities.
  An epic is delivered against its agreed outcomes; completing one feature is progress toward it.
  After bootstrap, the user maintains the roadmap; its status does not gate `speckit.specify`.
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

`speckit.program-kit-governance.sync` is an explicit setup tool for project/package/composition
changes. Ordinary planning and coding do not depend on a sync receipt. The maintained upgrader
coordinates routine maintenance directly; actual dependency checks remain required.

For existing applications with misplaced startup responsibilities or an unnecessary composition
library, follow the [scoped lifecycle repair guide](docs/maintenance/application-lifecycle-repair.md).

The reusable BFF/Keycloak composition and its EF/PostgreSQL variant build on these feature-owned
contributions. Declare actual feature projects, package roots and runtime paths in
`eng/foundation-composition.json`; use the existing sync mechanism and maintained
authentication/provider checks. The generated configuration reference and Mermaid diagram,
redacted configured-source view and actual activated-settings inspector distinguish operational
settings from owner-defined protocol behavior. Materialization, platform readiness and product
acceptance have separate outcomes; task guidance places enabling work beside its dependent product
operation. Application ownership, transaction, conflict, replay and recovery tests remain required.
See the [composition reference](extensions/program-kit-dotnet/references/foundation-compositions.md),
[adoption instructions](docs/maintenance/reusable-foundation-adoption.md) and
[0.12.11 migration guide](releases/migration-0.12.11.md). Existing consumer locks, accepted history,
custom configuration and live data remain preserved through toolkit upgrades.

Selecting the .NET profile adopts `Orbyss.Foundation.Host` by default. The coordinator's internal
engineering adapter scaffolds central build/package management, safe managed-file synchronization,
application-bundle staging, and release workflows. Consumers deploy the unchanged, digest-pinned
published Foundation host with a bundle of shells.json, hostsettings.json, nuplane.settings.json,
optional package feeds and a version/hash-bound descriptor. Consumers do not build a host DLL,
Dockerfile or derived image. A write requires reviewed,
source-bound setup choices (or a later Accepted override) and acknowledgement of the independently
pinned packages and NuGet sources; restore/build execution is separately authorized. This .NET adapter is not a
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

During development, run fast integrity checks, then select affected contracts:

```powershell
./scripts/Test-ProgramKit.ps1
python scripts/run_validation.py --suite Affected --changed-from <base-commit>
```

The [validation guide](docs/validation.md) explains the single capability map,
representative fixtures, explicit coverage gaps and runtime budgets. Independent
supported checks run even when another selected check lacks prerequisites. Native,
PostgreSQL, generated-client, browser and Host integrations require an affected risk.
Local records stay ignored; share a concise validation summary in the PR.

PR and explicit candidate CI share one package workflow: fast integrity, one build,
clean installation and installed entrypoints on Windows/Linux, and applicable security
checks. There is no broad duplicate main-push suite. A native GitHub environment
approval identifies the exact candidate and authorizes stable tag creation/publication
of the inspected packages. Sole-maintainer operation is supported. No custom developer
receipt transport or signed readiness form is required. A distinct public initializer and one prior-release upgrade must pass before Release
succeeds. Dependency upgrades remain separate maintenance. See [releasing](docs/releasing.md).

Optional live trials remain separately authorized; deterministic validation never
starts a coding agent. The repository-only release-readiness skill can recommend
relevant trials but grants neither paid-worker nor publication authority. No trial
run means no AI acceptance claim. Confirmed product defects block release; maintainer
review must explicitly address applicable coverage and harness limitations.

## Release assets

- `program-kit-<version>.zip`: small catalog-backed, pinned native composition manifest.
- `program-kit-tooling-<version>.zip`: complete tooling and source-recovery payload, including
  `scripts/upgrade_program_kit.py` for supported sequential offline/local-release upgrades.
  Verify this archive through the same release checksums. Earlier releases carried these inputs
  in their composite bundle; retain those original archives for historical recovery.
- `program-kit-governance-<version>.zip`: standalone governance extension package.
- `program-kit-building-blocks-<version>.zip`: standalone building-block selection extension.
- `program-kit-dotnet-<version>.zip`: standalone .NET capability extension package.
- `program-kit-governance-preset-<version>.zip`: standalone governance template preset.
- `Initialize-ProgramKit-<version>.sh`: copyable Bash initializer for Linux, macOS, and WSL.
- `Initialize-ProgramKit-<version>.cmd`: Windows initializer compatible with PowerShell
  `AllSigned` environments because it is a command script, not a PowerShell script.
- `SHA256SUMS`: exact artifact digests.
- `RELEASE-NOTES-<version>.md`, `MIGRATIONS-<version>.md`, and
  `migration-index-<version>.json`: reviewed release guidance and cumulative
  migration applicability. The same guidance is available offline in the governance extension.
- A separate CI source/package manifest and normal Actions logs bind candidate
  commit, version and exact archive hashes. They remain CI artifacts.

Compare a downloaded artifact's SHA-256 with its release's `SHA256SUMS` and inspected
CI source/package manifest. The maintained publisher does not issue artifact attestations:

```powershell
Get-FileHash program-kit-0.14.3.zip -Algorithm SHA256
```

## UI experience and public discovery

Browser projects can adopt the versioned [UI experience profile](extensions/program-kit-governance/references/ui-experience-v1.md)
through `/speckit.program-kit-governance.ui`. It separates layout, branding (including optional SVG
logos and Lucide/custom icons), semantic tokens, CSS adapters, page intent, public metadata and
consent-gated analytics. Generated native HTML is a reference renderer; accepted frontend frameworks
retain ownership through an initial-render adapter. The optional `Orbyss.Foundation.Web.Discovery` NuGet
feature serves an explicit public projection through CShells, without adding logic to the Host.

The [UI design model](extensions/program-kit-governance/references/ui-design-model.md) makes global/page
layout, brand/theme, components, feedback/recovery, motion, icons and implementation choices explicit.
New inputs use `modern-product-v1`; existing profiles without a presentation selection retain classic
styling. `ui_profile.py explain --target .` exposes choices and override paths without writing.
Complete form patterns and branded login/logout state templates are generated outside public exports;
the inherited Keycloak theme scaffold preserves provider flows and requires actual provider acceptance.

Consumer-owned profile/content inputs generate reproducible, conflict-protected outputs. Core
tests cover contrast, SVG safety, metadata/private-export boundaries, browser accessibility and
keyboard/reflow behavior. [UI experience contract](extensions/program-kit-governance/references/ui-experience-v1.md) distinguish
automated evidence from consumer journey, screen-reader and deployment acceptance.

Forms and localization are supplied by the independently versioned
[`orbyss-io/forms`](https://github.com/orbyss-io/forms) and
[`orbyss-io/localization`](https://github.com/orbyss-io/localization) repositories. Program Kit retains
the knowledge needed to choose their semantic contracts, compiler, runtime, authoring, operations,
storage, MCP, and Angular/React/Vue packages without compiling their source. The consumer still owns
field meaning, business validation, authorization, persistence durability, workflow, and publication
policy. Program Kit compatibility changes therefore update only selection knowledge, templates, and
consumer-facing checks; implementation and release tests remain in the owning component repository.

## Consumer repair feedback (feature source, unreleased)

`speckit.program-kit-governance.repair-request` installs a native consumer skill for
comparable diagnostics, local contributor intake, reviewed GitHub issue/evidence
submissions, follow-up evidence and freshly retrieved status/history. The evaluator
remains repository-only. See the [operating contract](extensions/program-kit-governance/references/repair-feedback/operating.md)
and [indexed unreleased guidance](releases/migration-0.14.0.md).
The [public evidence repository](https://github.com/orbyss-io/program-kit-evidence)
and App-bound guardian were provisioned and tested in three synthetic scenarios;
the maintained operating contract describes its supported boundaries.
Receiving owners use the [maintenance intake procedure](docs/maintenance/repair-feedback.md)
to register a ledger, inspect local/public packets and record request-specific decisions.
The feature remains unreleased source; these infrastructure tests do not qualify a release.

## License

Program Kit is open source under the [MIT License](LICENSE).
