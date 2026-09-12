# RM-01 runtime staging: central package pins

## Adoption status

This is an unpublished maintenance candidate on `codex/runnable-host-central-pins`,
based on main `0f5aa7a55a2502af9e8b938290b128165ef58b00`. No fixed supported release
is available from this work. The local archives retain the development version
0.11.0; their existence is not publication or authorization to install them.
PriceCalculator must remain blocked at T023 until a containing release passes its
publication gates and the user authorizes adoption. Merge, release, tag and paid
test execution have not been authorized for this maintenance request.

## Diagnosis and repair

The old `managed_package_versions` reader inspected only
`.program-kit/eng/ProgramKit.Packages.props`. The supported root central file imports
that baseline, optionally imports selected building-block pins, and permits consumer
declarations afterward. The three public web features were correctly pinned to
0.1.0 in that consumer section, so baseline synchronization could be clean while
stage failed with PKR019. Applying unrelated building-block selections is unnecessary.

The repaired `central_package_versions` follows that supported literal import graph.
It rejects missing pins, case-insensitive duplicates/conflicts, imports outside the
repository, cycles, ranges/floating pins and unsupported MSBuild evaluation. It does
not approximate conditional items, property-based versions or Update/Remove.
The exact supported subset is documented in the shipped
[runtime reference](../extensions/program-kit-dotnet/references/dotnet-runtime-and-application-bundles.md).

Stage also checks packed/restored built-in versions against those central pins,
rejects a transitive dependency that would replace a pin, and verifies the actual
downloaded built-in identities/versions before writing successful closure evidence.
Existing feature/dependency/route/dormancy and run-scoped package/configuration hash
validation remains in place. Failed retries invalidate success evidence and preserve
previous staged output until a complete new stage passes.

The supported import path semantics follow the
[MSBuild Import contract](https://learn.microsoft.com/en-us/visualstudio/msbuild/import-element-msbuild)
and the root/imported declarations described by
[NuGet central package management](https://learn.microsoft.com/en-us/nuget/consume-packages/central-package-management).
Staging intentionally accepts a smaller, unambiguous literal subset.

## Regression evidence

- The unmodified main source reproduces the exact OpenApi PKR019 failure against the
  retained synthetic fixture at `tests/fixtures/runnable-host/central-package-pins/`.
- `python tests/validate_runnable_host_pins.py` passes all 11 tests: real imported/consumer
  layout, the actual building-block props generator, optional and nested imports,
  18 unsupported/missing/conflict cases, unimported
  managed pins, imported conflicts, retained prior output, stale success invalidation,
  packed/restored conflicts, transitive pin replacement and incorrect downloads.
- `python tests/validate_lifecycle_profiles.py` passes, including the existing full
  stage and closure checks with a real central import added to its fixture.
- The bounded Development suite passes. The new fast regression is registered in
  Development, CI and the future Release workflow.
- `python tests/validate_dotnet_scaffold.py` passes managed baseline lifecycle and
  consumer-file preservation checks. Local candidate packaging succeeds; the archived
  staging script is checked against the exact source SHA256.
- Read-only resolution against the actual consumer resolves WebDefaults,
  Web.ProblemDetails and Web.OpenApi to 0.1.0. No consumer staging or mutation ran.

CI and publication validation are pending. These deterministic packages/downloads
are synthetic; they do not claim a real endpoint export or deployed RM-01 outcome.

## Supported continuation after a containing release is approved

Do not execute this procedure against the development checkout or overlay one script.
First obtain the complete published release archive, verify its SHA256SUMS and exact
release source/CI evidence, and extract it outside the consumer repository. Confirm
that release contains this repair and review all intervening compatibility changes.
Before mutation, stop concurrent lifecycle/upgrade operations and preserve a complete
restorable snapshot of the consumer, including its uncommitted work, ignored managed
state and genuine evidence. Keep credentials in their existing protected storage.

Use the release-owned sequential updater from a normal user-owned terminal. Replace
only the release-root placeholder with the verified containing release directory:

```powershell
Set-Location C:\Code\Orbyss\PriceCalculator
$releaseRoot = 'C:\path\to\verified-containing-release'
python "$releaseRoot\extensions\program-kit-governance\scripts\schema_runtime.py" setup --project-root .
if ($LASTEXITCODE -ne 0) { throw 'Target schema runtime preparation failed.' }
python "$releaseRoot\scripts\upgrade_program_kit.py" --release-root $releaseRoot --target . --integration codex
if ($LASTEXITCODE -ne 0) { throw 'Preserve the upgrade diagnostic and resolve its named continuation before proceeding.' }
python .specify/extensions/program-kit-governance/scripts/governance_state.py validate-installation
if ($LASTEXITCODE -ne 0) { throw 'Installed components are not coherent.' }
python .specify/extensions/program-kit-dotnet/scripts/dotnet_sync.py --target . --profile-selected --check
if ($LASTEXITCODE -ne 0) { throw 'Managed baseline has not converged.' }
```

The updater performs the write and check synchronization with the already recorded
web/persistence profiles. Retain bff-cookie and persistence-none; the feature's
approved PostgreSQL provider does not justify changing that baseline. Consumer-owned
central pins, public features, accepted shared architecture and host remain unchanged.
The updater preserves bootstrap decisions and records governed upgrade authority.

Managed-file conflicts stop the operation; preserve both versions and resolve through
the baseline's supported conflict procedure. Do not force an overwrite, patch the
installed module or fabricate installed hashes. A sequential upgrade can stop after
some components advance: retain its log, fix the reported cause and rerun the same
verified updater to convergence. If abandoning the upgrade, use an explicitly
authorized full pre-upgrade snapshot restoration; do not downgrade individual files
or edit registry/workflow state. Locks require the reported supported recovery and
confirmation that their owning operation ended.

PKU110 means producer-pin reconciliation requires separate review before mutation.
Do not add its acceptance flag merely to make this staging fix install. PKU111/exit 3
requires renewed analysis for each named feature. PKU113 requires the exact recorded
lock-renewal commands, followed by locked restore and updater convergence. This repair
itself does not change public runtime or exporter pins. PKU116 must be resolved within
the accepted selection's scope; do not apply future admin/authoring selections.

## Governance and feature readiness renewal

The staging repair alone changes neither architecture decisions nor spec/plan/task
bytes. A containing release based on current 0.11.0 development also introduces the
feature-intake gate: an existing Active feature must satisfy that gate at its next
gated operation. Reuse genuine feature evidence if already valid. Otherwise invoke
the installed `$speckit-program-kit-governance-specification-intake` for the existing
RM-01 feature, preserve approved facts, present its exact review and obtain real user
confirmation. Bootstrap approval is not feature-intake confirmation. Use the supported
existing-feature context; never manufacture the receipt or change roadmap eligibility.

Adding the confirmed brief/hash to spec traceability changes the spec's bytes and
requires `$speckit-analyze`, followed by the installed Program Kit architecture and
implementation checks. The same renewal applies to reconciled producer pins, stale
analysis or genuine plan/task changes. Do not invoke lifecycle completion alone to
create evidence for analysis that did not execute.

Preserve constitution ratification and unchanged accepted decisions. A changed
architecture decision needs its own genuine approval; this repair does not authorize
one. Historical bootstrap bd6be6ca stays aborted. Do not rerun bootstrap, use its
recovery commands or relabel the run to address T023.

Before repeating T023, run the installed checks and require zero exit status:

```powershell
python .specify/extensions/program-kit-governance/scripts/governance_state.py validate --require-roadmap
if ($LASTEXITCODE -ne 0) { throw 'Governance is blocked.' }
python .specify/extensions/program-kit-governance/scripts/implementation_preflight.py --repository . --feature-dir specs/001-assisted-renovation
if ($LASTEXITCODE -ne 0) { throw 'Implementation admission is blocked.' }
pwsh -NoProfile -File .program-kit/eng/Restore.ps1 -LockedMode
if ($LASTEXITCODE -ne 0) { throw 'Locked restore failed.' }
```

Then resume `$speckit-implement` at T023 with the retained task state and all required
hooks. Rebuild/repack the approved six-package graph if inputs changed; preserve and
rerun applicable component evidence. Execute the original supported stage command:

```powershell
python .program-kit/eng/runnable_host.py stage --repository . --packages artifacts/packages/0.1.0 --output artifacts/runnable-host
if ($LASTEXITCODE -ne 0) { throw 'T023 runtime staging is still blocked.' }
```

Require new `.program-kit/evidence/runtime-closure.json` with `satisfied=true`, the
current installed Program Kit version, the correct stagedRoot and actual package and
configuration hashes. The public feature packages must still be exactly 0.1.0.
An old preserved output directory alone is not success. Continue T023's registered
OpenAPI pipeline with the real managed exporter, reviewed initial baseline, pinned
oasdiff, isolated generator and consuming application compile. Initialize a baseline
only under its existing review/approval procedure; never overwrite one to hide drift.
Retain successful `.program-kit/evidence/openapi/pipeline.json` and its contract evidence.

Only then complete T023 and continue its dependents. PKUI001 remains separate unfinished
UI work. The earlier 18 component passes do not waive full managed build/tests,
deployed browser/manual acceptance, accessibility, performance, recovery or roadmap
delivery requirements. Until supported adoption and these checks pass, remain blocked.
