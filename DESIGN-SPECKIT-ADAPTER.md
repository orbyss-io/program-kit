---
artifact-kind: program-kit-product-design-proposal
product: program-kit-adapter-for-spec-kit
status: accepted-design
approval: approved-human-review
accepted-inputs: workspace-distribution-manifest-lock-and-spec-kit-extension-model
implementation-authority: none
feature-packet: not-created
parent-ledger: DESIGN.md
accepted-decision: DEC-046
governed-by: DEC-010, DEC-015, DEC-016, DEC-024, DEC-029, DEC-031, DEC-032, DEC-034, DEC-037, DEC-041
created: 2026-08-02
last-updated: 2026-08-02
---

# Program Kit Adapter for Spec Kit — Product and Proof Proposal

## 1. Document authority and review state

This document proposes the complete product boundary, user journey, contracts,
packaging, authority model, proof strategy, and delivery sequence for the first
Program Kit adapter for Spec Kit.

It is deliberately written **before** a Spec Kit feature packet exists. It is
not a feature specification, plan, or implementation task list, and it grants
no implementation authority. Its candidate decisions become accepted only
after explicit human review. After acceptance, the normal Program Kit Spec Kit
flow will translate this design into a feature specification, plan, tasks, and
implementation.

The adapter is a consumer product. Program Kit does not install or execute the
adapter in its own repository. This removes the suspected self-hosting loop:
Program Kit may continue to use Spec Kit as its development method while the
adapter is installed only in separate consumer workspaces.

## 2. Executive recommendation

Build a separately versioned **Program Kit Adapter for Spec Kit** with these
boundaries:

1. Program Kit is acquired as an exact workspace-local distribution; global
   installation is not the supported consumer path.
2. V1 executable factory providers are trusted first-party code compiled into
   that selected distribution and explicitly registered in its composition
   root.
3. A consumer-owned Program Kit workspace manifest declares zero or more exact
   requested provider/profile selections and may name one explicit workspace
   default; a generated lock records the exact resolved identities, digests,
   contracts, and evidence. Zero selections is a valid initialized state.
4. Installation, availability, selection, activation, and operation authority
   remain distinct states. One never implies another.
5. A Spec Kit extension supplies guided commands and lifecycle hooks and is
   installed through Spec Kit's supported extension manager.
6. A deterministic adapter executable shipped inside that extension translates
   one reviewed handoff into exact Program Kit public artifacts.
7. The executable invokes only the installed public `program-kit` CLI and never
   references Program Kit kernel or provider implementation assemblies.
8. Spec Kit remains the source of discovery, specification, plan, and tasks.
9. A small, explicit handoff is the reviewed factory projection; it is not a
   second planning model.
10. Program Kit remains the source of resolution, construction, evaluation,
   admission, receipts, and factory diagnostics.
11. Construction is never an automatic hook. It requires a separately issued,
   exact Program Kit authority grant selected by the human.
12. Installation uses Spec Kit's extension mechanism rather than modifying
   manifest-managed Spec Kit templates, scripts, or skills.
13. Adapter participation is resolved per feature from an explicit feature
    override or versioned workspace default. Non-factory work invokes no
    Program Kit factory operation and requires no target profile.
14. Workspace defaults may reduce repetitive selection, but their effective
    values are visible and pinned in each reviewed handoff; changing a default
    never silently rebinds an existing reviewed feature.

The first release should support one exact pair of product versions:

- Spec Kit `0.15.1`; and
- the exact Program Kit release selected by the implementation packet; and
- when a feature requests factory construction, the exact first-party .NET
  provider profile selected by the implementation packet.

Compatibility is fail-closed. Additional patch or minor versions are enumerated
only after executable compatibility proof; installation metadata must not imply
a wider range than the tested matrix.

## 3. Factual baseline

The proposal is based on the current repository and installed product surfaces,
not on an assumed future API.

### 3.1 Accepted Program Kit design

The accepted design already establishes that:

- Spec Kit owns guided discovery, specification, planning, and tasks;
- Program Kit owns independently callable public factory contracts;
- the adapter is separately installed and versioned;
- it is a client of the public factory protocol, not a kernel operation
  provider;
- it cannot create authority, bypass gates, or reinterpret unknown intent; and
- other orchestrators must be able to use the same Program Kit contracts.

These are existing decisions, primarily `DEC-010`, `DEC-015`, `DEC-016`,
`DEC-024`, `DEC-029`, and `DEC-031`. This proposal refines their external product
shape; it does not reopen them.

### 3.2 Current public Program Kit surface

The current factory CLI exposes:

```text
program-kit explain   --workspace <path> --request <path> [--format text|json]
program-kit construct --workspace <path> --request <path> [--format text|json]
program-kit evaluate  --workspace <path> --request <path> [--format text|json]
```

It accepts exact factory requests and software-definition bundles. It does not
contain Spec Kit concepts. This is the correct core boundary.

The reference fixture proves the desired downstream mechanics, but its
`eng/UpdateReferenceFixture.cs` generator is test infrastructure. It directly
uses kernel canonicalization, intake, and closure logic and therefore cannot be
reused by an external adapter.

### 3.3 Current distribution and provider state

`Orbyss.ProgramKit.Cli` is a .NET tool package. The proven consumer path installs
it into the consumer workspace, not as an ambient global tool. The package
currently includes the kernel, the first-party .NET provider, and session
integration assemblies.

The CLI composition root explicitly constructs one `DotNetProvider`; the
kernel does not scan installed assemblies. Its current provider manifest
advertises one exact target profile, `dotnet10-cshells-0.0.28`. The profile is
selected by exact identity in a factory request. Merely having the provider and
profile bytes in the distribution does not select or authorize them.

There is not yet a public Program Kit workspace manifest, exact restore lock,
catalog/list/select lifecycle, or dynamic provider package loader. Those are
required product surfaces for the accepted empty-workspace journey; they must
not be presented as already implemented.

### 3.4 Current public handoff gap

The current public protocol can explain an already exact `explain` request. It
does not yet expose a read-only way to prepare an effect-bearing `construct`
request.

An authorized construct request requires an exact closure digest, current live
state digest, request binding, and authority-grant reference. The fixture
generator obtains those values through kernel internals. The current `explain`
result exposes the explanation and lock digest, but not a public construct
proposal containing the required expected state and request binding. Calling
`construct` with effect `none` is refused by the implementation.

Therefore a real external adapter cannot honestly reproduce the current
fixture's transition from planning to authorization using only public
contracts. This is a product prerequisite, not adapter logic to fake.

### 3.5 Current Spec Kit extension surface

The installed Spec Kit `0.15.1` supports separately installed extensions with:

- versioned `extension.yml` manifests;
- contributed commands;
- project configuration templates;
- lifecycle hooks including `after_plan`, `after_tasks`, `before_implement`,
  and `after_implement`;
- enable, disable, priority, update, and removal operations; and
- local development and catalog installation paths.

It also supports bundles for coordinated installation of multiple extensions,
presets, custom steps, and workflows. The proposed v1 needs one extension, so a
bundle is unnecessary until a second independently managed Spec Kit component
is justified.

## 4. Product objective

Enable a developer to begin with a natural-language software goal, use the
normal Spec Kit workflow to converge intent and implementation work, review a
small explicit factory handoff, and then invoke Program Kit's exact public
factory operations without manually authoring dense factory JSON.

The adapter succeeds when the developer can understand:

- which meaning came from the approved Spec Kit artifacts;
- which values were explicit handoff choices;
- which implementation files remain consumer-owned;
- which files Program Kit proposes to generate;
- which inputs remain unknown or unsupported;
- what authority is required before construction; and
- which product produced every artifact, result, and diagnostic.

## 5. Non-goals

The first adapter does not:

- make Program Kit depend on Spec Kit;
- add planning concepts to Program Kit core;
- parse arbitrary prose and silently treat it as approved meaning;
- generate or approve its own Program Kit authority grant;
- automatically run `construct` from a hook;
- make Spec Kit artifacts Program Kit runtime dependencies;
- replace Program Kit's resolution, construction, evaluation, or diagnostics;
- support every Program Kit provider, vocabulary, or profile;
- install global tools or modify a user's global Spec Kit configuration;
- dynamically load downloaded provider assemblies into the v1 kernel;
- implement a version-range solver, best-match selection, or automatic upgrade;
- modify Spec Kit's manifest-managed core templates, scripts, or skills;
- promise deterministic AI interpretation or custom implementation behavior;
- claim migration support; or
- add the Claude adapter or any other session provider.

## 6. System boundary

```text
Developer intent
    |
    v
Spec Kit: specify -> clarify -> plan -> tasks -> implement custom behavior
    |
    | reviewed handoff + referenced approved artifacts
    v
Program Kit Adapter for Spec Kit
    |  deterministic translation and public CLI orchestration
    v
program-kit prepare/explain -> human authority -> construct -> evaluate
    |
    v
Consumer-owned implementation + Program Kit generated product + evidence
```

Ownership is intentionally one-way:

- Spec Kit does not call Program Kit internals.
- The adapter does not become a Program Kit provider.
- Program Kit does not read Spec Kit artifacts directly.
- The generated product has no runtime dependency on Spec Kit, the adapter, an
  AI agent, or Program Kit.

## 7. Product components

### 7.1 Selected Program Kit distribution

The consumer acquires one exact Program Kit CLI distribution into the
workspace. In v1 that distribution is the executable trust and compatibility
boundary. It contains:

- the public CLI and kernel;
- explicitly registered first-party factory providers;
- the exact provider and target-profile catalog those providers support;
- public contracts, schemas, diagnostic catalogs, and canonicalization
  identities; and
- provider manifests and conformance evidence.

The initial distribution contains the first-party .NET provider and the exact
`.NET 10 + CShells 0.0.28` target profile. Acquiring that distribution makes
them installed and discoverable; it does not select a provider/profile for a
workspace and does not authorize execution.

The supported acquisition is workspace-local. The feature packet must choose
and prove one ordinary .NET mechanism—preferably a local tool manifest, with
the already-proven exact `--tool-path` approach retained as a bounded fallback.
Both must resolve one exact package version without ambient global-tool lookup.

### 7.2 Program Kit workspace manifest and lock

The consumer-owned workspace manifest is the requested factory composition,
analogous to a deliberately stricter `package.json`. It names exact versions,
not ranges, and records explicit human selections.

The Program Kit-generated lock is the accepted exact resolution, analogous to a
content-bound lock file. It records package and distribution identities,
provider/profile identities, digests, operation contracts, schemas, diagnostic
catalogs, dependencies, and conformance evidence.

The manifest never becomes operation authority. The lock proves exact
resolution, not approval to construct.

### 7.3 Spec Kit extension

Proposed extension identity:

```text
orbyss-program-kit-adapter
```

The extension owns:

- command instructions for supported Spec Kit integrations;
- lifecycle hook declarations;
- a project-local configuration template;
- the deterministic adapter executable and its runtime dependencies;
- handoff and adapter-result schemas;
- exact compatibility metadata; and
- install, update, disable, and removal metadata.

### 7.4 Deterministic adapter executable

The extension ships one framework-dependent .NET executable assembly and its
closed dependency set. Spec Kit consumers already need the Program Kit .NET
runtime profile, so this avoids another scripting runtime and provides the same
binary on Windows and Linux.

The executable may depend on separately published **public contract packages**.
It must not reference:

- `ProgramKit.Kernel`;
- a concrete Program Kit provider assembly;
- test fixture generators;
- repository `eng/` scripts; or
- internal Spec Kit Python modules.

It invokes the configured `program-kit` executable as a child process through
its documented CLI grammar. The executable location, release identity, and
supported contract identities are explicit configuration or release-manifest
inputs; `PATH` discovery is not semantic authority.

### 7.5 Program Kit public preparation contract

The adapter requires an orchestrator-neutral, effect-free public operation that
turns an exact desired construction intent into an authorizable proposal.

Proposed public command:

```text
program-kit prepare --workspace <path> --request <path> [--format text|json]
```

`prepare` is not a planning operation and contains no Spec Kit vocabulary. It:

- consumes an exact software-definition bundle, requested construction mode,
  desired effect, selections, evaluation context, and workspace identity;
- resolves the exact prospective construction closure;
- observes the relevant current live-state precondition without mutation;
- emits an exact ungranted construct-request proposal;
- emits the request binding, closure digest, live-state digest, resolution
  explanation, and authority requirements;
- performs no candidate or live publication; and
- never creates an authority grant.

This command must use a newly versioned public request/result contract rather
than silently changing the closed v1 schemas. Existing v1 `explain`,
`construct`, and `evaluate` behavior remains compatible.

The precise schema revision and coexistence rules belong in the later feature
packet, but the capability itself is a design prerequisite. Other orchestrators
receive the same benefit, so it does not create Spec Kit coupling.

### 7.6 Authority provider remains separate

`prepare` returns an authority request/proposal, not authority. A repository
record, human authority service, or another accepted authority provider must
issue the exact grant.

The adapter may:

- display the authority requirements;
- preserve an unprivileged grant proposal as evidence;
- verify that a selected grant reference exists; and
- pass that exact reference into a construct request.

It may not:

- identify itself as the issuer;
- turn a Spec Kit gate result into a Program Kit grant;
- populate a grant with an invented reviewer identity;
- silently select one of several grants; or
- run construction while approval is absent or ambiguous.

Automated tests may use a separately supplied test authority provider to isolate
the construct boundary. A complete consumer release may not rely on that test
fixture as its only issuance path.

### 7.7 Repository authority recording prerequisite

The accepted governance design allows a repository-local human-approval
provider that proves the presence, exact scope, and provenance assertion of a
reviewable record without claiming cryptographic human identity. The current
kernel verifies such grants, but the public CLI does not yet provide a usable
issuance/recording path.

The complete adapter journey therefore also requires an orchestrator-neutral
Program Kit authority-provider command, provisionally:

```text
program-kit authority record --workspace <path> --request <path> [--format text|json]
```

This is not an adapter command. It is an explicit human-invoked interface to
the configured repository authority provider. It consumes the exact output of
`prepare` plus a separately reviewed human decision record, validates their
bindings, and materializes the exact reviewable repository grant and revocation
record. The provider records the human's declared decision; it does not invent
or broaden it.

The exact grammar and contract versioning belong in the feature packet. The
required behavioral boundary is:

- no interactive or ambient semantic defaults;
- no grant without a current exact human decision record;
- no automatic invocation from the adapter or a Spec Kit hook;
- exact request, subject, operation, effect, validity, condition, provenance,
  and revocation bindings;
- structured refusal without partial authority files; and
- seeded-handoff ownership for the created repository records.

If this production authority path is deliberately deferred, the adapter may be
released only as a preparation/explanation preview. It must not be described as
a complete planning-to-construction product.

## 8. Consumer installation and lifecycle

### 8.1 Five distinct states

The installation model must preserve five states that ordinary package-manager
language often conflates:

| State | Meaning | Does not imply |
|---|---|---|
| Installed | Exact package bytes exist in the workspace or package store. | Compatibility, selection, activation, or authority. |
| Available | The selected distribution recognizes the exact manifest and its support evidence. | Human choice or execution. |
| Selected | A human or already approved exact policy chose the provider/profile and the lock records it. | Invocation or widened effects. |
| Activated | One exact request names the selected provider/profile for a supported operation. | Permission for candidate or live writes. |
| Authorized | A separate current grant permits the exact operation, subjects, effect, and preconditions. | Any broader or later action. |

Every command, result, manifest, and diagnostic uses these meanings
consistently. In particular, package installation and a one-item catalog never
become implicit selection.

### 8.2 Accepted empty-workspace journey

The intended consumer journey is:

1. Install and initialize Spec Kit in the empty workspace.
2. Acquire one exact Program Kit CLI distribution workspace-locally.
3. Run an explicit Program Kit initialization command, producing a neutral
   workspace manifest with zero provider/profile selections.
4. Run read-only/acquire `program-kit restore` to produce the exact base lock
   with an empty profile-selection set.
5. Install `orbyss-program-kit-adapter` through Spec Kit's extension manager.
6. Run base adapter `doctor` to verify the Spec Kit/adapter/Program Kit release
   binding without requiring a factory profile.
7. Optionally configure a versioned workspace adapter-activation default. If
   also choosing a default profile for future factory-applicable features,
   inspect the local catalog, add the exact selection, and freshly restore it
   into the lock.
8. Begin the normal Spec Kit discovery, specification, planning, task, and
   implementation workflow. Non-factory features remain outside Program Kit.
9. When a feature first requests Program Kit factory output, inspect the exact
   local distribution catalog, explicitly select or inherit an already
   approved exact profile, and restore the resulting lock.
10. Run feature-readiness `doctor`, review the adapter handoff, then use Program
   Kit preparation, explanation, separately recorded authority, construction,
   and evaluation.

Illustrative command sequence:

```text
specify init ...
dotnet new tool-manifest
dotnet tool install Orbyss.ProgramKit.Cli --version <exact-version>
dotnet tool run program-kit init
dotnet tool run program-kit restore
specify extension add orbyss-program-kit-adapter
speckit.program-kit.doctor

# Only when configuring or activating a factory-applicable feature:
dotnet tool run program-kit catalog list --scope distribution
dotnet tool run program-kit profile select <exact-profile-identity>
dotnet tool run program-kit restore
speckit.program-kit.doctor --feature <feature-key>
```

Only `specify init`, .NET local-tool commands, and Spec Kit extension
installation exist today. The Program Kit `init`, `catalog`, `profile`, and
`restore` grammar is proposed product surface whose exact contracts belong in
the feature packet.

Tool acquisition itself performs no repository mutation beyond the ordinary
local tool manifest/package state. It does not install skills, choose a
profile, or invoke Program Kit. A Program Kit session skill is installed only
through its separate session-capability lifecycle; the Spec Kit adapter is
installed only through Spec Kit's extension lifecycle.

#### 8.2.1 Program Kit initialization boundary

`program-kit init` is a narrowly bounded consumer-workspace bootstrap command,
not a factory operation and not a source of construction authority. It must:

- create only absent Program Kit bootstrap files inside the exact workspace;
- seed a neutral consumer-owned manifest bound to the exact workspace-local
  Program Kit distribution, with zero provider/profile selections;
- perform no network access, package restore, catalog refresh, provider
  activation, profile selection, adapter installation, or factory invocation;
- ignore ambient global Program Kit installations and configuration;
- be idempotent when its exact outputs already exist;
- refuse conflicting, drifted, colliding, or unsafe paths without partial
  writes or silent repair; and
- grant no authority to any later operation.

Initialization cannot require an ordinary construction grant because that
would create a bootstrap cycle before a Program Kit workspace exists. Its
effect class, explicit human-or-authorized-agent invocation evidence, request
and result schemas, atomic publication, and non-overwrite behavior must be
specified and proven in the feature packet. No Spec Kit hook may invoke it.

#### 8.2.2 Local distribution catalog boundary

The v1 catalog command is a read-only, offline inventory of the exact invoked
Program Kit distribution. It lists exact installed provider/profile identities,
support envelopes, contracts, and evidence without downloading, installing,
selecting, restoring, activating, or authorizing anything. A one-item result is
still not an implicit selection.

This local inventory is not the deferred marketplace, remote package registry,
dynamic provider loader, trust store, version solver, or global semantic graph.
Those remain outside v1. The precise grammar may use `catalog list --scope
distribution` or a narrower profile-list form, but the feature packet must keep
the scope explicit and must not silently add remote sources.

### 8.3 Installation ownership and layout

The expected ownership layout is:

```text
consumer-workspace/
├── .config/
│   └── dotnet-tools.json                 # .NET-owned exact CLI acquisition
├── program-kit.yaml                      # consumer-owned requested composition
├── program-kit.lock.json                 # Program Kit-generated exact resolution
├── .program-kit/
│   ├── state/                            # Program Kit receipts and local state
│   └── packages/                         # reserved for exact package content
├── .specify/
│   ├── extensions.yml                    # Spec Kit-owned extension registration
│   └── extensions/
│       └── orbyss-program-kit-adapter/   # Spec Kit-installed adapter release
└── specs/
    └── <feature>/program-kit/            # reviewed handoff and feature evidence
```

Each manager owns its own installation records. The adapter may verify and bind
them into its feature-local manifest, but it must not rewrite the .NET tool
manifest, Program Kit lock, or Spec Kit extension registration behind the
owning tool.

### 8.4 Program Kit workspace manifest

The consumer-owned manifest records requested exact composition and explicit
selection. Illustrative shape:

```yaml
schema: program-kit.workspace/v1
distribution:
  package: Orbyss.ProgramKit.Cli
  version: <exact-version>
factory:
  selections:
    - alias: dotnet-default
      provider:
        identity: orbyss.program-kit.dotnet:factory-provider:dotnet-cshells@1.0.0
      targetProfile:
        identity: orbyss.program-kit.dotnet:target-profile:dotnet10-cshells-0.0.28@1.0.0
  defaultSelection: dotnet-default
```

The actual schema must use the complete governed identities required by the
public contracts. Both `selections: []` with no default and one exact supported
.NET selection are valid v1 states. The collection shape preserves a path to
future multiple named profiles without claiming that v1 can construct through
more than its exact supported profile. V1 accepts exact versions and identities
only. It has no range solver, transitive best-match algorithm, ambient source
discovery, or automatic upgrade.

A default selection is explicit versioned workspace policy, not an ambient
fallback. It applies only after a feature is factory-applicable. Every reviewed
handoff records the effective exact selection and whether it came from a
feature override or workspace-default inheritance. Changing the default does
not silently rebind an existing reviewed handoff.

The manifest may declare expected session capabilities or external adapters for
diagnostic completeness, but their owning products still install and activate
them. Program Kit core does not gain a Spec Kit dependency merely because a
consumer records that external integration.

### 8.5 Exact lock and restore

`program-kit restore` is a read/acquire/verify operation over the manifest. It
does not execute a factory provider. It produces an exact lock containing:

- CLI package and distribution identities and digests;
- exact provider and target-profile identities;
- operation contracts and canonicalization identities;
- schema and diagnostic-catalog identities;
- package sources and exact dependency assets;
- provider support and conformance evidence; and
- unresolved, unavailable, unsupported, or ambiguous items.

Restore succeeds only when the requested composition is uniquely exact and all
required bytes/evidence are available. The human reviews or explicitly accepts
the lock before factory activation. A later changed manifest or selected
distribution invalidates the lock; an unrelated repository edit does not.

A manifest with zero profile selections may restore a base lock containing the
exact distribution and public contract/catalog closure while truthfully
reporting that no factory profile is selected. That state supports base
installation and adapter compatibility checks but cannot activate a factory
feature. Adding or changing a selection requires a fresh exact restore.

### 8.6 Spec Kit extension installation

The versioned Spec Kit extension is installed independently:

```text
specify extension add orbyss-program-kit-adapter
```

A consumer installs an exact catalog release or a validated local extension
directory. Development uses `--dev`; published consumer installation does not.

The installation must:

- write only Spec Kit's extension registration and extension-owned files;
- instantiate project configuration through the supported config mechanism;
- verify a compatible `specify` version;
- verify the explicit workspace-local Program Kit executable, base lock, and
  release identity;
- permit a valid zero-profile workspace and report factory readiness separately;
- fail before partial installation when a required tool or release binding is
  absent or incompatible; and
- leave Spec Kit managed-core manifests and files unchanged.

### 8.7 Adapter project configuration

Adapter configuration records only project-local integration choices, for
example:

```yaml
schema: program-kit.spec-kit-adapter-config/v1
programKit:
  invocation: dotnet-tool-manifest
  workspaceManifest: program-kit.yaml
  workspaceLock: program-kit.lock.json
activation:
  defaultMode: assist
  features: {}
defaultRequestedEffect: none
```

The real schema will use platform-neutral logical paths and exact identities.
It will not accept credentials, authority grants, semantic defaults, ambient
environment substitutions, or an alternative profile that bypasses the Program
Kit lock.

The workspace activation policy supports three explicit modes:

| Mode | Inherited feature behavior |
|---|---|
| `off` | The adapter performs no feature work unless an exact feature override enables it. |
| `assist` | The adapter may perform read-only applicability checks and propose adapter-owned candidates, but it does not block implementation until the feature is explicitly activated. This is the recommended mixed-workspace default. |
| `required` | Every feature must resolve to factory-applicable or explicitly disabled/not-applicable. Unresolved applicability may block the workflow but grants no effect or authority. |

Feature resolution precedence is an exact feature override, then the versioned
workspace default, then `off`; there is no user-machine, environment, path-glob,
or ambient global semantic default. Organization templates may seed workspace
policy, but every repository records and reviews its own exact configuration.

Installation, workspace policy, feature applicability, profile selection, and
operation authority remain separate. An inherited `assist` or `required` mode
does not choose a profile. Applicability is resolved first; only an applicable
feature resolves an explicit feature profile override or the exact locked
workspace default. A missing or incompatible applicable profile returns
structured `needs-input` without fallback.

Once reviewed, a handoff pins its effective activation and profile-selection
source. Later workspace-default changes apply to new or unreviewed candidates;
they do not silently rebind reviewed handoffs. `doctor` reports divergence and
offers an explicit re-handoff rather than mass regeneration or migration.

Base `doctor` verifies installation, exact releases, neutral manifest/base lock,
extension registration, and configuration integrity without requiring a
factory profile. Feature-readiness `doctor` additionally verifies resolved
applicability, the effective exact profile, lock freshness, handoff/review, and
public-contract compatibility for one feature.

### 8.8 Upgrade safety

Program Kit distribution, Program Kit manifest/lock, and Spec Kit adapter have
separate version lifecycles. An upgrade is an explicit requested composition
change followed by a fresh exact restore and compatibility check; installed
newer bytes do not silently replace the selected distribution/profile.

Adapter customization survives Spec Kit upgrades because it is installed as an
extension, not patched into managed core. The release must prove that:

- a manifest-aware Spec Kit upgrade preserves the extension registration;
- an adapter update replaces only adapter-owned installation files;
- project configuration and consumer handoffs remain intact;
- incompatible Spec Kit, Program Kit, lock, provider, or profile versions fail
  closed;
- a failed update leaves the prior working adapter selectable; and
- no `--force` upgrade is required for the supported path.

The adapter release manifest pins the extension, executable, schemas, command
instructions, and compatibility table as one tested release set.

### 8.9 Disable and removal

Disabling the extension removes its commands and hooks from active use without
deleting consumer artifacts or altering the Program Kit profile selection.

Disabling one feature records an exact feature override and stops future
adapter participation for that feature. It never reverses construction,
deletes or edits consumer-owned files, changes workspace defaults, or removes
existing Program Kit products, locks, receipts, snapshots, evidence, handoffs,
or results. Re-enabling first revalidates the preserved state and reports stale
inputs; it does not silently resume an old effect-bearing continuation.

Removing it deletes only unchanged extension-owned installation files and its
registration. It preserves:

- the local Program Kit tool declaration, workspace manifest, and lock;
- Spec Kit specifications, plans, and tasks;
- reviewed handoffs and human review records;
- custom implementation;
- Program Kit products, receipts, and evidence; and
- adapter-generated feature evidence already committed to the repository.

A separate explicit cleanup command may delete regenerable adapter-owned
candidate files only after matching their recorded digests. It never deletes
consumer-owned or Program Kit-owned files.

### 8.10 Future extension-package evolution

The v1 manifest/lock model deliberately prepares for a larger ecosystem without
pretending that arbitrary executable plugins are safe today.

Declarative vocabulary, schema, profile, template, and target-asset packages may
later be acquired as exact content-addressed members under
`.program-kit/packages/`. Executable factory providers remain trusted
first-party code compiled into the selected v1 distribution and explicitly
registered at build time.

Before third-party or independently downloaded executable providers can run,
Program Kit must separately design and prove an out-of-process execution profile
with explicit filesystem, process, environment, network, secret, resource,
input, output, and diagnostic boundaries. Only then may a future exact package
restore make provider executables available for selection. Installation still
will not imply activation or authority.

## 9. Feature-local artifact model

For a feature at `specs/<feature>/`, the proposed layout is:

```text
specs/<feature>/program-kit/
├── handoff.yaml
├── handoff-review.json
└── generated/
    ├── adapter-manifest.json
    ├── definitions/
    │   ├── software-bundle.json
    │   └── <provider-definition>.json
    ├── requests/
    │   ├── prepare.json
    │   ├── explain.json
    │   ├── construct.json          # only after an external grant is selected
    │   └── evaluate.json
    └── results/
        ├── prepare.json
        ├── explain.json
        ├── construct.json
        └── evaluate.json
```

The exact filename set is conditional; a stopped operation does not fabricate
later artifacts.

A feature resolved as disabled or non-factory creates no feature-local Program
Kit directory, handoff, profile binding, request, result, or authority record.
If an earlier adapter-owned candidate exists, disabling preserves it until an
explicit digest-checked cleanup; it never treats absence of current activation
as permission to delete historical or consumer-owned work.

| Artifact | Owner | Meaning |
|---|---|---|
| `handoff.yaml` | seeded-handoff, then consumer-owned | Small reviewed projection from Spec Kit meaning into a supported factory profile. |
| `handoff-review.json` | consumer-owned | Named review of the exact handoff digest; evidence only, never a Program Kit authority grant. |
| `adapter-manifest.json` | adapter-generated-owned | Exact adapter, Spec Kit, Program Kit, schema, input, and output bindings. |
| generated definitions/requests | adapter-generated-owned | Deterministic public Program Kit inputs. |
| captured results | adapter-generated-owned | Exact structured public results returned by the invoked CLI. |
| custom source | consumer-owned | Human/AI-authored implementation referenced by the bundle. |
| Program Kit product/state | Program Kit ownership rules | Generated product, locks, receipts, snapshots, and evidence. |

No file mixes editable and generated regions.

## 10. Handoff contract

### 10.1 Purpose

The handoff exists because free-form Markdown is not a stable machine contract.
It records only information needed to project approved work into one supported
Program Kit definition family.

It does not copy the Spec Kit lifecycle, requirements model, plan model, task
graph, or task state. Those artifacts remain referenced source material.

### 10.2 Required content

The v1 handoff contains:

- exact schema identity;
- feature identity and logical root;
- stable references and exact traced semantic-value digests from `spec.md`,
  `plan.md`, and `tasks.md` where applicable, with whole-source observations
  retained separately as provenance rather than automatic factory identity;
- named intent owner and review state;
- explicit factory applicability and its decision source;
- when factory-applicable, one exact Program Kit target profile and
  provider-family binding plus whether it is explicit or inherited;
- explicit provider-specific definition fields;
- implementation artifact references and ownership;
- field-level trace from each identity-forming value to a Spec Kit artifact or
  explicit human handoff decision;
- unresolved, unsupported, deferred, and excluded items;
- desired Program Kit operation and maximum requested effect; and
- no authority grant.

Illustrative shape:

```yaml
schema: program-kit.spec-kit-handoff/v1
feature:
  key: <feature-key>
  sources:
    spec: specs/<feature-key>/spec.md
    plan: specs/<feature-key>/plan.md
    tasks: specs/<feature-key>/tasks.md
review:
  state: pending
factory:
  applicability: applicable
  definitionFamily: program-kit.provider.dotnet.component-api-definition/v1
  targetProfile: <exact governed identity>
  selectionSource: workspace-default
  desiredOperation: construct
  maximumEffect: committed
definition:
  component: <explicit supported fields>
  application: <explicit supported fields>
implementation:
  records: <logical path, media type, ownership, identity inputs>
trace:
  <factory pointer>: <source artifact and stable section/requirement reference>
unknowns: []
```

This example is explanatory, not the schema. The implementation packet must
define the complete exact schema and canonical projection.

### 10.3 Proposal and review behavior

The AI-facing command may propose `handoff.yaml` after planning. Proposal is not
approval. Before tasks or implementation rely on it, a human reviews:

- factory applicability and any workspace-default inheritance;
- semantic fields;
- target/profile selections;
- generated versus custom ownership;
- unsupported and deferred meaning;
- requested effect ceiling; and
- field-level trace.

The review record binds the exact handoff digest and reviewer identity. Editing
the handoff makes the prior review stale. The adapter may still run a read-only
validation on an unreviewed handoff, but it must not present it as approved or
advance to effect-bearing construction.

### 10.4 No heuristic admission

The deterministic translator consumes the reviewed handoff and referenced
bytes. It does not scrape headings, infer values from prose, execute Markdown,
or ask an LLM to repair missing schema fields.

The AI may help produce a candidate. Missing, conflicting, ambiguous, or
unsupported meaning remains explicit and stops deterministic translation until
the handoff is revised and reviewed.

The adapter does not infer factory applicability from file extensions, project
names, Markdown headings, or the mere presence of a workspace default. A
documentation-only feature with no requested Program Kit output is disabled or
not-applicable and creates no handoff. A change written in documentation that
alters a traced contract, identity, ownership choice, or other semantic factory
input remains factory-relevant even before source code changes exist.

## 11. Adapter commands and Spec Kit hooks

Proposed command names are versioned extension command identities; final naming
is approved in the feature packet.

| Command | Maximum effect | Purpose |
|---|---:|---|
| `speckit.program-kit.doctor` | none | Verify exact Spec Kit, adapter, Program Kit, configuration, and contract compatibility. |
| `speckit.program-kit.activate` | adapter configuration only | Record an exact feature override and optional locked profile reference; it grants no factory authority. |
| `speckit.program-kit.disable` | adapter configuration only | Record an exact feature disable without deleting handoffs, products, locks, receipts, evidence, or consumer work. |
| `speckit.program-kit.handoff` | adapter files only | Propose or refresh a handoff candidate and show unknowns without claiming approval. |
| `speckit.program-kit.validate` | none | Validate reviewed handoff, trace, ownership, paths, and staleness. |
| `speckit.program-kit.prepare` | adapter files only | Deterministically generate factory inputs and invoke public `program-kit prepare`. |
| `speckit.program-kit.explain` | adapter files only | Invoke public `program-kit explain` and preserve its exact structured result. |
| `speckit.program-kit.construct` | bounded Program Kit effect | Invoke public `program-kit construct` only with an explicitly selected exact grant. |
| `speckit.program-kit.evaluate` | adapter files only | Invoke public `program-kit evaluate` and preserve its exact structured result. |

Adapter-file writes are declared local development effects. They are not
Program Kit candidate or live product publication.

### 11.1 Hook policy

Hooks activate only for a feature with an explicit adapter handoff or project
activation policy. Spec Kit may technically invoke an installed hook entry
point for an inactive feature, but the adapter must return `not-applicable`
without launching Program Kit, resolving a profile, writing feature artifacts,
or blocking the workflow. Recommended v1 behavior:

| Hook | Behavior | Blocking? |
|---|---|---:|
| `after_plan` | Resolve the feature override/workspace mode and applicability. In `assist`, optionally propose a handoff; in `required`, require applicable or explicitly disabled/not-applicable state. | Never for inactive/non-applicable work; unresolved `required` state may block its review gate. |
| `after_tasks` | For applicable work, check that tasks respect custom/generated ownership and contain the handoff/review obligations. | Yes only for explicitly activated or `required` applicable work. |
| `before_implement` | Refuse stale or unreviewed handoff inputs and unresolved identity-forming meaning. Inherited `assist` alone never blocks. | Yes only for explicitly activated or `required` applicable work. |
| `after_implement` | For applicable work, refresh relevant implementation digests and offer effect-free `prepare`/`explain`. | No automatic construction; no action for inactive/non-applicable work. |

The hooks do not replace the existing Spec Kit human review gates. They add the
factory-specific information those gates must inspect.

### 11.2 Construction interaction

Construction is always an explicit command after:

1. resolved factory applicability and an exact locked effective profile;
2. reviewed handoff;
3. successful public preparation;
4. successful explanation;
5. human review of the planned artifact set and blockers;
6. explicit selection of one existing exact grant; and
7. a fresh preflight confirming that inputs and live state still match.

If the grant is absent, stale, ambiguous, or mismatched, the adapter returns a
structured request for approval/input and performs no construction.

## 12. Translation rules

The translator is support-bounded and fail-closed.

### 12.1 Spec Kit inputs

Spec Kit files provide referenced intent, requirements, architecture, tasks, and
implementation ownership. Only stable identifiers and reviewed explicit values
cross the handoff. Formatting, prose order, timestamps, and agent transcripts
do not become semantic inputs.

### 12.2 Program Kit outputs

For the initially supported .NET component/API profile, the translator creates:

- one provider-specific semantic definition;
- one software-definition bundle;
- artifact references for consumer-owned custom implementation;
- exact selections and trace;
- one preparation request; and, after public preparation, exact explain,
  construct, and evaluate requests as permitted.

Provider identities, target profiles, media types, and schema identities come
from the adapter release's tested compatibility manifest or the public Program
Kit preparation result. They are not guessed from installed files.

### 12.3 Trace rule

Every identity-forming or output-affecting field must have exactly one of:

- a stable Spec Kit source reference;
- an explicit human handoff decision; or
- a fixed value owned by the exact adapter compatibility profile.

An implementation convenience, filename convention, or LLM inference is not an
authority source.

### 12.4 Change rule

A changed reviewed semantic input creates a new candidate handoff and makes the
old review and generated adapter artifacts stale. A changed implementation file
requires refreshed implementation digests but does not automatically reopen
unrelated semantic choices. A documentation-only change outside the declared
input set does not invalidate factory evidence.

Whole planning-document bytes may be retained in adapter provenance, but
factory invalidation follows the declared field-level trace and exact semantic
values, ownership choices, implementation artifacts, and profile inputs. The
adapter re-resolves stable references after a source-document edit. An unchanged
traced value remains valid; a missing, ambiguous, or changed traced value makes
the affected handoff stale. This prevents a README correction, prose reorder,
or unrelated planning note from causing repository-wide rehashing or factory
reconstruction while still detecting a contract change expressed in Markdown.

## 13. Structured results and diagnostics

The adapter needs an adapter-specific result contract because it performs
translation and Spec Kit lifecycle work outside the public factory CLI.

Proposed envelope:

```text
program-kit.spec-kit-adapter-result/v1
```

It carries:

- exact adapter operation and release identity;
- outcome, furthest stage, effect state, and primary disposition;
- handoff and generated artifact references;
- adapter diagnostics and disclosure decisions;
- compatibility and staleness status; and
- the exact unmodified `program-kit.operation-result/*` document when a factory
  command was invoked.

The adapter does not translate Program Kit diagnostic identities into its own
wording. It may add adapter diagnostics, but the embedded Program Kit result
remains authoritative for factory behavior.

Adapter diagnostics use a separate authority-qualified catalog and include the
same actionable data floor as Program Kit diagnostics. Initial categories must
cover at least:

- incompatible tool or contract version;
- missing or stale handoff review;
- incomplete or conflicting mapping;
- unsupported provider/profile field;
- path escape, collision, or unsafe artifact reference;
- stale referenced bytes;
- missing or ambiguous authority grant; and
- public CLI invocation or result-contract failure.

Rendered prose is never used for automation.

## 14. Determinism and evidence claims

### 14.1 What is deterministic

Given the same:

- reviewed handoff bytes;
- referenced artifact bytes;
- adapter release and compatibility manifest;
- exact Program Kit public contract identities; and
- canonicalization profile,

the deterministic translator must emit byte-identical adapter-owned factory
definition and request artifacts.

Program Kit construction remains governed by its own reproducibility profile.

### 14.2 What is not deterministic

The following are not claimed deterministic:

- natural-language discovery;
- AI-generated spec, plan, task, or handoff proposals;
- human review decisions;
- consumer custom implementation;
- authority issuance;
- terminal presentation, duration, or temporary paths; and
- external tool or runtime behavior outside a named proven profile.

### 14.3 Necessary digest use

Digests are required where they bind semantic input, authority, artifact
ownership, exact release identity, or retained evidence. They are not a general
progress ritual.

The adapter must not regenerate distribution manifests, rehash the repository,
or rerun full proof after an unrelated edit. Each evidence item declares its
invalidation set and is reused while that set is unchanged.

## 15. Security and local-safety model

The adapter is local-first:

- no telemetry, source upload, or network access after package acquisition;
- no credentials in handoffs, results, logs, or governed artifacts;
- no shell evaluation of handoff values;
- no execution of Markdown or generated remediation prose;
- no path outside the declared consumer workspace;
- no symlink/junction escape;
- no ambient global configuration search;
- no automatic construction or grant selection;
- bounded stdout/stderr with disclosure-safe diagnostics; and
- exact child-process argument arrays, never generated shell command strings.

The installed extension is trusted development-time code. It is not described
as sandboxed. Published releases require provenance, dependency inventory, and
the same supply-chain controls as other executable Program Kit packages.

## 16. Compatibility model

Each adapter release declares an exact tested matrix:

| Dimension | V1 policy |
|---|---|
| Spec Kit | Exact `0.15.1` initially; later versions are explicitly enumerated after proof. |
| Program Kit CLI | Exact supported release identity or explicitly enumerated equivalent patch releases. |
| Factory contracts | Exact supported schema and canonicalization identities. |
| Provider/profile | Exact first-party .NET provider and target profile identities. |
| .NET runtime | Exact minimum/runtime family required by both executable products. |
| OS | Windows and Linux paths proven in CI. |
| Spec Kit integration | Integration-neutral commands where possible; Codex proves the first guided journey. |

Installed does not mean compatible. A mismatch produces no generated factory
inputs and no factory invocation.

## 17. Proof design

Proof is claim-driven and tiered. The full Windows/Linux and packaging matrix
runs in authoritative CI once per merge candidate, not after every local edit.

### 17.1 Claim and proof matrix

| Claim | Nearest proof | Authoritative tier | Invalidated by |
|---|---|---|---|
| CLI acquisition is exact and workspace-local with no global fallback | clean consumer package-install assertion | CI, Windows/Linux | tool acquisition, invocation resolver, package metadata |
| Initialization is neutral, idempotent, atomic, and grants no factory authority | empty/existing/conflicting workspace bootstrap matrix | Story + CI | init request/result, bootstrap ownership, publication logic |
| The v1 catalog is exact local distribution inventory, not selection or remote acquisition | offline catalog golden and no-effect tests | Story + CI | catalog grammar, distribution registry, result contract |
| Installed, available, selected, activated, and authorized remain distinct | manifest/lock and operation-state contract matrix | Story + CI | workspace contracts, resolution, invocation, authority logic |
| Zero selected profiles is a valid installed adapter state | neutral manifest/base-lock install and doctor scenario | Story + CI | manifest/lock, extension install, base doctor |
| Workspace defaults reduce repetition without ambient or retroactive selection | activation/profile inheritance and changed-default matrix | Story + CI | adapter config, handoff, selection resolution |
| Non-factory work invokes no Program Kit command and writes no feature artifacts | documentation-only and mixed-workspace black-box scenarios | Story + CI | hook applicability, activation policy, invocation layer |
| Mistaken activation and later disablement are non-destructive | enabled/no-applicable-output/disable/re-enable lifecycle test | Story + CI | hook effects, ownership, cleanup, lifecycle logic |
| Manifest selection produces one exact reviewable lock | restore golden, ambiguity, and staleness tests | Story + CI | manifest/lock schemas, catalog, restore logic, distribution metadata |
| V1 executes only providers compiled into the selected distribution | dependency graph, registry, and unsupported-package tests | Pre-PR + CI | composition root, package graph, provider loading code |
| Extension installs without modifying Spec Kit managed core | clean consumer install assertion | CI, Windows/Linux | extension manifest, install layout, supported Spec Kit line |
| Update/disable/remove preserve consumer work | lifecycle contract test | CI | extension lifecycle code or ownership policy |
| Candidate handoff does not claim approval | schema and command golden tests | Story | handoff schema or proposal command |
| Reviewed handoff translation is byte-repeatable | repeated/permuted-input golden test | Story + CI | translator, schema, canonical profile, compatibility manifest |
| Missing/ambiguous meaning is not guessed | executable negative matrix | Story | mapping rules or diagnostics |
| Adapter uses no kernel/provider internals | project/package reference and binary dependency checks | Pre-PR + CI | project or package graph |
| Public preparation exposes authorizable exact data without effects | public CLI contract/acceptance test | Story + CI | preparation request/result or kernel preparation logic |
| Adapter never creates/selects authority | negative authority and effect tests | Story + CI | command/hook/authority code |
| Repository authority records an exact human decision independently | public authority-provider acceptance and negative tests | Story + CI + Human | authority request/result, repository provider, review schema |
| Exact external grant enables bounded construct | package-only consumer end-to-end | CI | adapter request projection, Program Kit public contracts/provider |
| Result preserves exact Program Kit diagnostics | schema/golden/adversarial tests | Story | adapter result projection or disclosure code |
| Generated product has no development-tool runtime dependency | package/runtime dependency inspection | CI | generated project/package graph |
| Guided journey is understandable | named human review in fresh consumer sessions | Human | commands, prompts, help, handoff layout, authority interaction |

### 17.2 Positive end-to-end scenarios

Two scenarios are required:

1. **Reference Status parity**: reproduce the existing Status component/API
   outcome from a Spec Kit feature without pre-seeded factory definitions or
   requests.
2. **Distinct supported example**: build a different component/API with changed
   names, contract, route, namespace, and custom implementation to prove the
   adapter is not a Status fixture generator.

Both begin with natural-language intent in a clean consumer workspace. The
proof may supply an exact offline package source, cache, and dependency mirror,
but it installs the workspace-local CLI and Spec Kit extension through the
supported consumer commands. It may not pre-seed the Program Kit manifest,
lock, profile selection, adapter registration, handoff, provider definition,
software bundle, factory requests, or Program Kit product files.

The automated construct proof may receive an exact grant from a separately
identified test authority provider so adapter and factory failures stay
diagnosable. At least one package-only consumer acceptance test and the human
journey use the production repository authority recording path. In every case,
the authority provider is outside the adapter and its setup is disclosed.

### 17.2.1 Non-factory and workspace-default scenarios

The proof also requires:

1. an adapter-installed, zero-profile workspace completing a documentation-only
   Spec Kit feature with no Program Kit child process and no feature-local
   Program Kit artifacts;
2. a mixed workspace where one factory feature uses the exact .NET default while
   an unrelated documentation-only feature remains inactive;
3. `assist` inheritance that proposes no effect and does not block an
   unactivated feature;
4. `required` inheritance with an explicit non-factory/disabled exception;
5. an applicable feature inheriting the exact locked workspace profile without
   repeated selection while its handoff records that inheritance;
6. a feature-specific profile override and an incompatible inherited profile
   returning `needs-input` without fallback;
7. a changed workspace default affecting new candidates but not rebinding an
   existing reviewed handoff; and
8. mistaken activation followed by disable/re-enable with no deletion or
   alteration of consumer work, Program Kit products, locks, receipts, or
   evidence.

### 17.3 Negative and adversarial matrix

Executable proof must include:

- missing identity-forming field;
- conflicting Spec Kit trace and handoff value;
- unreviewed and stale-reviewed handoffs;
- edited spec/plan/tasks after review;
- edited custom implementation after preparation;
- zero, multiple, stale, or wrong-subject grants;
- ambient global CLI shadowing the workspace-local release;
- installed but unselected provider/profile and one-item implicit selection;
- zero-profile initialization, repeated initialization, conflicting bootstrap
  state, and attempted hook-driven initialization;
- catalog invocation with network/remote-source attempts and proof that listing
  one candidate does not select it;
- inactive, `assist`, `required`, explicitly disabled, and unresolved feature
  applicability;
- inherited default changes, explicit feature overrides, and attempted silent
  rebind of a reviewed handoff;
- documentation-only work, changed untraced prose, and a traced contract change
  expressed in Markdown;
- disablement or cleanup attempts against consumer-owned, Program Kit-owned,
  drifted, or unproven artifacts;
- version ranges, ambiguous candidates, stale lock, or changed distribution;
- attempted dynamic loading of an unregistered provider package;
- unsupported Spec Kit, Program Kit, schema, provider, and profile versions;
- unknown handoff property;
- duplicate or case-colliding logical paths;
- workspace escape and symlink/junction escape;
- secret-shaped and exception-derived input;
- malformed or prose-contaminated child CLI output;
- interrupted adapter artifact write; and
- attempted hook-driven construction.

Every case asserts outcome, effect, disposition, stable diagnostic identity,
safe expected/observed data, and absence of unauthorized writes.

### 17.4 Install, upgrade, and removal proof

On both Windows and Linux:

1. initialize a clean Spec Kit consumer;
2. acquire the exact Program Kit distribution workspace-locally;
3. initialize a neutral zero-profile Program Kit manifest and base lock;
4. install the exact Spec Kit extension package and pass base `doctor` without
   a factory selection;
5. inspect the offline local catalog, explicitly select the .NET
   provider/profile, restore the exact lock, and pass feature-readiness doctor;
6. reject any global CLI shadow and verify commands, conditional hooks,
   activation defaults/overrides, config, lock binding, and managed-core
   integrity;
7. disable and re-enable one feature and the extension without changing the
   factory selection or deleting preserved work;
8. change workspace defaults without rebinding reviewed handoffs;
9. update from the previous compatible adapter fixture;
10. remove the extension; and
11. prove the local tool declaration, Program Kit manifest/lock, consumer
    handoffs, source, and Program Kit artifacts were preserved.

### 17.5 Human validation

Human validation is qualitative, not a disguised full regression suite.

Run three fresh consumer journeys with no terminal coaching outside the shipped
instructions. Record:

- whether the developer understood what to review;
- whether custom versus generated ownership was clear;
- whether missing input and authority requests were actionable;
- whether the developer could locate the tool declaration, manifest, lock,
  adapter registration, handoff, generated inputs, product files, and evidence;
- whether the developer could distinguish installed, available, selected,
  activated, and authorized state; and
- whether the developer understood workspace defaults, feature overrides,
  non-factory behavior, and why disabling never deletes prior work; and
- whether the developer could explain which product made each decision.

Expand to ten trials only when claiming a numerical reliability rate, when the
three sessions expose instability, or when the human reviewer explicitly asks
for it. A named final human acceptance remains required.

## 18. Efficient verification strategy

| Tier | Run while | Included | Excluded |
|---|---|---|---|
| Edit | changing one translator/command rule | affected build, schema/unit test, focused golden | restore, package install, full Program Kit acceptance |
| Story | completing one user outcome | relevant contract tests and one focused consumer flow | unrelated profiles and cross-platform matrix |
| Pre-PR | candidate locally complete | isolated release build, adapter unit/contract tests, one local-distribution/manifest/restore/extension smoke path, changed-file format | full two-OS conformance and human trials |
| CI | exact merge candidate | full package, Windows/Linux, negative matrix, two end-to-end scenarios, provenance | duplicate local rerun |
| Human | CI candidate green | three fresh guided journeys and design/fitness review | mechanizable checks already proven by CI |

Evidence reuse rules:

- translator evidence depends on translator, schemas, compatibility manifest,
  and fixture input bytes;
- distribution/restore evidence depends on CLI package layout, workspace
  manifest/lock contracts, catalog metadata, selection/restore logic, and the
  supported Program Kit release;
- adapter-install evidence depends on extension layout, extension manifest,
  lifecycle code, and supported Spec Kit version;
- activation/default evidence depends on adapter configuration contracts,
  applicability resolution, inheritance/override logic, hook policy, and
  lifecycle ownership; it does not depend on unrelated consumer documentation;
- Program Kit end-to-end evidence depends on the public preparation/factory
  contracts, supported provider/profile, adapter projection, and consumer
  scenario bytes;
- human evidence depends on user-visible commands, instructions, handoff shape,
  and authority interaction; and
- unrelated documentation, timestamps, branch heads, or regenerated digests do
  not invalidate these claims.

## 19. Delivery sequence after design approval

Only after this proposal is accepted:

1. Allocate the next non-conflicting feature identity after reconciling current
   remote feature branches.
2. Run the normal Spec Kit `specify` flow using this accepted design as input.
3. Clarify any newly exposed product ambiguity.
4. Obtain human approval of the feature specification.
5. Plan the smallest complete sequence across Program Kit workspace
   initialization/manifest/local-catalog/select/restore, adapter activation
   defaults and no-code applicability, public preparation,
   repository-authority recording, and the Spec Kit adapter, with one
   requirement/proof matrix and exact public-contract versioning.
6. Obtain human approval of the plan.
7. Generate tasks, run cross-artifact analysis, and obtain implementation
   approval.
8. Implement vertical slices with edit/story tests only.
9. Run Pre-PR once when locally complete.
10. Let protected Windows/Linux CI own the authoritative full matrix.
11. Run the bounded human validation on the green candidate.
12. Record acceptance and close the packet without a routine convergence audit;
    use convergence only if evidence exposes a real gap.

The adapter itself is not used to implement this repository. It is tested in
temporary/package-only consumer workspaces.

## 20. Risks and mitigations

| Risk | Consequence | Mitigation |
|---|---|---|
| Free-form Markdown becomes hidden machine truth | prompt-dependent and irreproducible mapping | explicit reviewed handoff; deterministic translator consumes no prose heuristics |
| Adapter starts duplicating Spec Kit | competing planning lifecycle | handoff contains only factory projection and references planning artifacts |
| Adapter starts duplicating Program Kit | divergent resolution/authority rules | public `prepare` plus exact CLI invocation; embedded Program Kit result remains authoritative |
| Authority is confused with approval evidence | AI can widen effects | handoff review and Program Kit grant are separate artifacts/providers |
| Global CLI shadows the repository version | different workspaces execute different contracts | workspace-local acquisition, exact invocation binding, and no global fallback |
| Installed package becomes an implicit choice | unreviewed provider/profile gains semantic authority | five-state model, explicit manifest selection, and reviewed exact lock |
| Initialization silently selects the only profile | installation becomes hidden architecture | neutral zero-profile init, separate local catalog/select/restore, and base versus feature doctor |
| Local catalog is mistaken for a marketplace | remote acquisition and trust scope enter v1 accidentally | distribution-only offline inventory with explicit scope and no install/select effects |
| Workspace defaults become ambient or retroactive | different machines or later policy changes silently rebind features | repository-owned exact policy, feature override precedence, and reviewed handoff pinning |
| Adapter runs destructively for non-factory work | documentation changes generate or delete product state | applicability before profile resolution, no-invocation non-factory path, and non-destructive disablement |
| Downloaded DLL is treated as a safe plugin | untrusted code executes inside the kernel process | v1 compiled-in first-party providers; out-of-process isolation before later executable packages |
| Tool managers overwrite one another's state | upgrade/removal corrupts another product's ownership | separate .NET, Program Kit, and Spec Kit records plus cross-product `doctor` verification |
| Spec Kit upgrade removes integration | silent workflow loss | supported extension registration, manifest-aware upgrade proof, managed-core integrity check |
| Compatibility ranges float | different bytes/behavior under same handoff | exact release matrix and fail-closed doctor |
| Proof repeats on every edit | slow delivery and evidence churn | tiered checks and semantic invalidation sets |
| Adapter is only a renamed fixture generator | no reusable product | second distinct scenario and no fixture/test-internal dependencies |
| Packaging ships platform-specific drift | Windows/Linux divergence | one framework-dependent assembly and cross-platform package proof |
| Hooks surprise non-adapter features | workflow friction | explicit activation and conditional hooks |

## 21. Rejected alternatives

### 21.1 Put Spec Kit parsing in Program Kit core

Rejected because it reverses the accepted dependency boundary, makes Program
Kit depend on a planning product, and prevents other orchestrators from using
the same factory contracts.

### 21.2 Implement the adapter only as prompt instructions

Rejected because prompt output cannot own canonical bytes, safe path handling,
schema validation, repeatability, transactional writes, or stable diagnostics.

### 21.3 Reuse the reference fixture generator

Rejected because it depends on kernel internals, embeds the Status example, and
issues fixture authority. It is evidence setup, not a public product.

### 21.4 Modify Spec Kit core templates or skills

Rejected because upgrades can overwrite the changes and because the adapter is
an optional consumer product. Supported extension commands, hooks, and config
provide the correct lifecycle boundary.

### 21.5 Ship a custom Spec Kit workflow in v1

Rejected for now because one extension can integrate through supported hooks
without replacing a consumer's chosen workflow. Revisit only if hooks cannot
express a proven required gate or transition.

### 21.6 Put construction in `after_implement`

Rejected because a hook cannot select or create human authority and should not
cause widened product effects merely because implementation finished.

### 21.7 Treat a Spec Kit approval gate as a Program Kit grant

Rejected because the two products have separate authority contracts and the
adapter may not elevate one workflow event into effect-bearing authority.

### 21.8 Install Program Kit as an ambient global tool

Rejected because a global command can silently change behavior across multiple
workspaces, shadow the repository's tested release, and weaken reproducibility.
The supported path binds one exact workspace-local distribution.

### 21.9 Dynamically load downloaded provider assemblies in v1

Rejected because in-process .NET loading is not isolation, package presence is
not trust, and the accepted v1 distribution already bounds executable providers
to explicitly registered first-party code. External executable providers wait
for a separately designed out-of-process profile.

### 21.10 Let one installer own every product's files

Rejected because .NET tool acquisition, Program Kit factory selection, and Spec
Kit extension activation have different owners and upgrade lifecycles. The
guided journey coordinates them and `doctor` verifies their binding; no manager
silently rewrites another manager's state.

### 21.11 Select the only installed profile during initialization

Rejected because installation count is not semantic authority. Neutral init,
read-only local discovery, explicit workspace policy, and exact restore keep a
one-profile v1 usable without turning availability into selection.

### 21.12 Use machine-global adapter or profile defaults

Rejected because two contributors could resolve the same repository
differently. Defaults are exact versioned workspace policy; organization
templates may seed them, but ambient user or environment configuration has no
semantic authority.

### 21.13 Treat disabling as rollback or cleanup

Rejected because activation state does not own consumer work or previously
admitted Program Kit products. Disablement stops future participation and
preserves history; cleanup is a separate digest-checked operation limited to
unchanged adapter-owned candidates.

## 22. Accepted design decisions

The human approval recorded in section 24 accepts all of the following as one
coherent design:

1. The adapter is a consumer-only product and is not used by Program Kit to
   build itself.
2. The supported CLI path is one exact workspace-local Program Kit
   distribution; global installation and ambient global fallback are excluded.
3. V1 executable factory providers are trusted first-party code compiled into
   the selected distribution and registered explicitly; downloaded provider
   DLLs are not loaded dynamically.
4. A consumer-owned workspace manifest may declare zero or more exact
   provider/profile selections and one explicit workspace default; a Program
   Kit-generated base or factory lock records the exact resolved closure.
5. Installed, available, selected, activated, and authorized are separate
   states; no earlier state implies a later one.
6. The Spec Kit adapter is installed through
   `specify extension add orbyss-program-kit-adapter`, while Program Kit core
   remains independent of Spec Kit.
7. The accepted empty-workspace journey is Spec Kit initialization, local
   Program Kit acquisition, neutral zero-profile Program Kit initialization,
   base restore, Spec Kit adapter installation and base doctor, then profile
   selection and fresh restore only when configuring or activating
   factory-applicable work.
8. The adapter's deterministic executable is shipped inside the extension and
   invokes only public Program Kit CLI contracts.
9. A reviewed explicit handoff, rather than heuristic Markdown parsing, is the
   adapter's semantic input.
10. Program Kit gains an orchestrator-neutral, read-only public preparation
   contract before the adapter claims an end-to-end authorizable flow.
11. Handoff review evidence and Program Kit construction authority remain
   separate; the adapter never issues or chooses a grant.
12. A complete consumer release includes a separately invoked production
   repository-authority recording path; otherwise it is labeled a
   preparation/explanation preview.
13. V1 supports one exact Spec Kit line and one exact Program Kit .NET provider
   profile, then expands only through proof.
14. Extension hooks are conditional, return without Program Kit invocation or
   feature writes for inactive/non-factory work, and never construct
   automatically.
15. The proof uses two clean factory scenarios, explicit no-code and
   mixed-workspace scenarios, Windows/Linux installation and lifecycle proof, a
   full negative matrix, and three qualitative human trials by default.
16. Verification is tiered and evidence is reused according to semantic
   invalidation sets; the full merge matrix runs in CI once.
17. No feature packet or implementation begins until the human explicitly
    accepts this design or records requested revisions here. The recorded
    design approval satisfies the packet prerequisite but grants no
    implementation authority.
18. `program-kit init` is a neutral, idempotent, atomic workspace bootstrap with
    zero selections and no factory authority; exact bootstrap effect and
    invocation evidence are specified in the packet.
19. The v1 Program Kit catalog is read-only offline inventory from the exact
    local distribution. Marketplace, remote acquisition, dynamic loading, and
    version solving remain deferred.
20. Adapter participation resolves per feature from an exact override and then
    a repository-owned workspace mode of `off`, `assist`, or `required`; there
    are no machine-global semantic defaults.
21. Applicability precedes profile resolution. A documentation-only or otherwise
    non-factory feature requires no profile, handoff, Program Kit invocation,
    authority, or feature-local Program Kit artifacts.
22. Workspace profile defaults reduce repeated selection but are pinned with
    their inheritance source in reviewed handoffs. Default changes never
    silently rebind reviewed features, and disable/re-enable never deletes or
    rewrites consumer work or prior Program Kit products/evidence.

## 23. Review checklist

- [x] Product objective and non-goals match the intended adapter.
- [x] The Spec Kit/adapter/Program Kit boundary is understandable.
- [x] The Program Kit distribution is workspace-local, not global.
- [x] Executable providers remain compiled-in first-party providers in v1.
- [x] A consumer manifest plus exact generated lock owns provider/profile
      selection and resolution.
- [x] The Spec Kit adapter is installed through Spec Kit's extension manager.
- [x] The complete empty-workspace journey is the accepted product direction.
- [x] Neutral zero-profile initialization and the local-only catalog boundary
      are accepted.
- [x] Workspace activation defaults, feature overrides, applicability-first
      profile resolution, and non-destructive disablement are accepted.
- [x] Documentation-only and mixed-workspace behavior is explicit and proven.
- [x] The public `prepare` prerequisite is accepted or replaced with another
      public-contract-only solution.
- [x] Handoff content and ownership are acceptable.
- [x] Human review versus construction authority is sufficiently separated.
- [x] The production repository-authority recording prerequisite is accepted,
      revised, or explicitly deferred to a preview-only release.
- [x] Installation, upgrade, disable, and removal behavior is acceptable.
- [x] Command and hook behavior is acceptable.
- [x] Compatibility policy is sufficiently narrow and honest.
- [x] Determinism and security claims are correctly bounded.
- [x] Proof is strong enough without repeating full gates unnecessarily.
- [x] Human validation scope is appropriate.
- [x] Rejected alternatives and tradeoffs are accepted.
- [x] The proposal is approved to become the authority source for a new Spec Kit
      feature packet.

## 24. Review record

**Current decision**: Approved by the human product owner as the authoritative
design input for a new Spec Kit feature packet.

**Requested revision — 2026-08-02**: Harden installation around a
workspace-local Program Kit distribution, compiled-in executable providers for
v1, an explicit consumer manifest and exact lock, Spec Kit-owned adapter
installation, and the complete empty-workspace journey. Incorporated in this
revision.

**Accepted review input — 2026-08-02**: The human product owner explicitly
accepted the workspace-local distribution, compiled-in executable-provider v1
boundary, consumer manifest and exact lock direction, installation of the
adapter through `specify extension add orbyss-program-kit-adapter`, and the full
empty-workspace journey recorded in section 8. This acceptance hardens those
parts of the candidate design but does not approve the complete proposal or
authorize implementation.

**Final refinement and approval — 2026-08-02**: After reviewing the complete
proposal, the human product owner accepted the final recommendations for
neutral zero-profile initialization, a distribution-local read-only catalog,
no-code/non-factory non-invocation, applicability-before-profile resolution,
workspace `off`/`assist`/`required` defaults, exact feature overrides and
profile inheritance, non-retroactive default changes, and non-destructive
disable/re-enable behavior. The human then explicitly stated that, with these
improvements recorded, the complete adapter design was approved.

**Overall acceptance record**: Present. This document is the approved authority
source for creating and reviewing the next Spec Kit feature packet. Approval
does not authorize implementation; specification, plan, tasks, analysis, and
their normal human checkpoints remain required before implementation begins.
