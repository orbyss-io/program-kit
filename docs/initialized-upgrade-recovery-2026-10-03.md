# Initialized consumer upgrade convergence and recovery

The InsurancePolicyEvaluator report observed a coherent 0.12.2 installation after
an updater failure. Its immutable bootstrap baseline remains 0.12.1. Run `26232ea0`
is completed, the constitution is Ratified and the building-block selection is
Accepted. Verified 0.12.3 reproduced the same 26 persistence blockers and was not
installed. Neither completed bootstrap nor ratification needs to be repeated.

The shared readiness bug applied feature admission to every proposed data owner
during offline upgrade. No application projects, managed .NET baseline or selected
targets had been materialized. The updater stopped at PKU116 before recording
accepted upgrade authority or assessing consumer phase remediation. This behavior
also existed in 0.12.1; the report does not establish a newly introduced 0.12.2 bug.

## Source correction

`persistence_selection.upgrade_scope` retains global declaration and transition
guards, installed/admitted owners and existing provider/test projects. It defers
only proposed, uninstalled owners whose assigned projects are absent. An unassigned
owner can be deferred only while no application .NET projects exist. Legacy installed
provider intent without valid owner admission remains blocked. Upgrade resolves all
owners regardless of the current feature, so active-feature scoping cannot hide an
installed owner's missing proof.

The release-owned updater checks admission and the currently installed provider's
actual central imports and project assignments before any component installation.
It then refreshes existing baseline files and checks candidate pin convergence.
Future proposals never become installed provider profiles or synthetic admissions.
Their original blockers remain in `deferredPersistenceAdmissions` in readiness and
the separate remediation report. Implementation checks and real-provider proof are
unchanged. Planned targets are not created by upgrade.

CLI discovery now precedes ownership imports. On Windows the probed uv launcher
identifies the exact CLI interpreter; the updater delegates to it if necessary.
The existing validated bridge still supports its documented execution-boundary
fallback. No global Python installation or PATH configuration is changed.

Verified releases must be extracted outside the consumer tree. PKU120 rejects an
in-tree release before CLI actions, rather than suppressing dependency auditing of
arbitrary directories. Actual unmanaged application dependencies remain violations.

Once installation starts, each invocation writes a distinct attempt with installation-input
SHA-256, approved decision SHA-256, initially observed version, original
previous version and status. A matching retry references its failed predecessor;
it preserves the prior file and diagnostic. Accepted upgrade authority is recorded
only after offline convergence and installation validation. Package verification
and consumer phase readiness remain separate. Existing failures without these new
attempts are not rewritten or used to invent prior installation history.
The input digest binds component trees, release-owned scripts, VERSION and bundle;
it is separate from the downloaded archive checksum, which the operator verifies.

## Exact consumer recovery after publication

The following command targets the prepared **0.12.4 candidate**. Do not use it until
the complete tagged Program Kit Release workflow has succeeded. The revised
candidate retains the supported public Spec Kit dependency and defers the core
Python-command proposal. Verify the full
archive's published checksum/attestation, then extract it to the indicated external
directory. Use the existing supported Spec Kit installation. Preserve the constitution
and confirmed intake; do not force reinitialization over consumer artifacts.

From normal user-owned PowerShell:

```powershell
Set-Location C:\Users\tech_\Code\InsurancePolicyEvaluator
$specifyPython = Join-Path ((& uv tool dir).Trim()) 'specify-cli/Scripts/python.exe'
& $specifyPython C:\ProgramKitReleases\program-kit-0.12.4\scripts\upgrade_program_kit.py `
  --release-root C:\ProgramKitReleases\program-kit-0.12.4 `
  --target C:\Users\tech_\Code\InsurancePolicyEvaluator `
  --integration codex
if ($LASTEXITCODE -notin 0,3) { throw 'Upgrade incomplete; preserve its diagnostic and attempt evidence.' }
& $specifyPython .specify/extensions/program-kit-governance/scripts/governance_state.py validate-installation
if ($LASTEXITCODE -ne 0) { throw 'Installation is incoherent.' }
& $specifyPython .specify/extensions/program-kit-governance/scripts/governance_state.py validate-setup-authority
if ($LASTEXITCODE -ne 0) { throw 'Upgrade authority is incomplete.' }
```

If the updater reports SCHEMA_RUNTIME_MISSING, prepare the same runtime before retry:

```powershell
& $specifyPython C:\ProgramKitReleases\program-kit-0.12.4\extensions\program-kit-governance\scripts\schema_runtime.py setup `
  --project-root C:\Users\tech_\Code\InsurancePolicyEvaluator
```

Exit 3 means offline setup converged while explicit package verification remains
pending; follow its exact renewal instructions only for materialized dependencies.
PKU117 describes separate future feature obligations. Neither result grants product
delivery acceptance. The new accepted version record truthfully uses observed
0.12.2 as the previous installation, new 0.12.4 as the installation and original
0.12.1 as the baseline. It does not fabricate a missing 0.12.1-to-0.12.2 success.

Preserve the report's original artifacts and verify these SHA-256 values before
and after recovery:

| Artifact | SHA-256 |
| --- | --- |
| `docs/architecture/bootstrap-decisions.json` | `73f8ec1a0500768a5d8a6d0feb33db988d383f9509387ab0252153619c554b8a` |
| `docs/architecture/bootstrap-intake.json` | `0c0c041d2bcf4e14ff4b7225ac6fef9f5e1df08ada516e7afd686ff6525f54bc` |
| `.specify/memory/constitution.md` | `53da462fd3b40c70037f1c6f7582a1b48907ee955346a25423cdbfff5ad14ad1` |

Keep run history, approval/ratification evidence and all prior failed updater output.
Do not change workflow state, rerun bootstrap, synthesize admission, enable automatic
approvals or perform an implicit rollback. Continue RM-01 through installed feature
intake and its owned phase gates after upgrade authority validates.

## Development evidence

Main through `abfb909` was merged into `codex/python-runtime-consistency` with
the prior interpreter/ACL correction preserved. The bounded Development suite
passed all 60 checks; its journal is
`artifacts/validation-runs/20261002T234940Z-275e2d2f/journal.json`.
The final targeted boundary tests passed 10 cases, and persistence tests passed
21 cases. The sequential local upgrade validator passed using real installers in
disposable consumers: planned and materialized selections, all components installed
before an injected convergence failure, plain-Python discovery, retry provenance,
immutable decisions and deferred admissions. No coding worker or consumer recovery
was launched. This evidence does not substitute for the complete publication gate.
