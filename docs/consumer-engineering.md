# Consumer engineering without lifecycle duplication

Program Kit supplies focused knowledge before Spec Kit planning, tasks and implementation.
Compiler/analyzer checks, compiled dependency policy, real tests, contract checks and normal code
review enforce the software. Initial bootstrap is setup history, never a routine gate.
This upstream change leaves dezaaglijst untouched. Its migration and specification restart remain
separate follow-up work.

The native constitution template carries explicit test-first, architecture and independent-engineering
principles. Existing project constitutions remain unchanged by installation. Substantive amendments
are reviewed against the constitution itself without bootstrap/installation history. Specifications
retain native prioritized stories and acceptance scenarios and explicitly request automated tests;
tasks map those tests to the stories before implementation. Scoped exceptions stay in plans/ADRs.
Clarify runs after specify, and analyze after tasks; neither introduces an extra approval dossier.

| Classification | Concrete consumer examples | Reason |
| --- | --- | --- |
| Keep | constitution, spec.md, intake brief, plan.md, tasks.md, designs, accepted ADRs, architecture-map.json, user-owned specification-roadmap.md | Actionable intent and decisions. Builds can run if these authoring inputs are removed. |
| Keep | src/, tests/, native project/package files and locks, .editorconfig, eng/, contract baselines, shells.json, hostsettings.json, nuplane.settings.json, deploy/, CI | Actual software, enforcement and reproducible composition; visible and runnable by humans. |
| Consolidate | knowledge-inventory.json and phase requirement registry | One upstream phase-obligations.json authority records conditions, examples, enforcement and coverage scope. No consumer copies to maintain. |
| Consolidate | artifact-ownership runtimeComposition, API proof operation lists, persistence package assignments | Project roles belong in eng/architecture.json; project/package files, contract registry and tests supply the remaining facts. Plans carry unique choices. |
| Generate | C4 views from the architecture model, focused guidance, installation metadata, test output | Regenerable output, never new approval authority. Guidance is printed, not required as a feature file. |
| Archive | existing .program-kit/evidence/, .specify/governance/recovery/, old receipts, published-host runtime-feed diagnostics | History remains readable and unchanged. Counts alone cannot establish safe deletion or toolkit ownership. |
| Remove from routine lifecycle | obligation-design/review, phase projections, semantic-contract, verification-plan/results wrappers, architecture-proof/api-proof attestations, ratification/roadmap/analysis hash checks | Plans, engineering configuration, actual execution and review provide the useful facts. History cannot block drafting/coding. |
| Tool installation | .specify/extensions/, installed workflows and integration skills | Versioned toolkit internals, restored through installation; no application build or deployment dependency. |

The supplied consumer inventory includes agent troubleshooting artifacts. This change removes
required maintenance of duplicate state. It does not indiscriminately delete files or claim that
every historical item was a mandatory toolkit output.

A minimal active structure is:

```text
src/                            application code
tests/                          executable behavior/architecture/security tests
eng/                            documented verification, contracts, project-role policy
contracts/                      checked contract baselines
deploy/                         composition and deployment inputs
Directory.Build.*               ordinary build policy
Directory.Packages.props         central dependencies
global.json, locks, .editorconfig
.github/workflows/               ordinary engineering CI/release
specs/<feature>/                 spec, intake reference, plan, tasks, useful design
docs/architecture/              architecture model, ADRs, optional user roadmap
.specify/memory/constitution.md   authoring authority
artifacts/                       ignored generated output
```

No workflow ledger, recovery dossier, generated phase declaration or approval fingerprint is an
application prerequisite. Preserve scoped exceptions and unique test requirements when consolidating
old inputs. Qualified compositions reduce repetitive integration work; custom application behavior
still needs meaningful tests.

The supported maintenance command is the release-owned updater:

```powershell
python <verified-release>/scripts/upgrade_program_kit.py --release-root <verified-release> --target . --plan
python <verified-release>/scripts/upgrade_program_kit.py --release-root <verified-release> --target .
```

It installs sequentially, synchronizes transactionally, verifies native dependencies and reports
installation, migration, application and release states separately. Use --offline explicitly for
installation without network restore. Inspect diagnostics and retry the same command after failure;
originals and completed bootstrap history remain intact. Substantive profile/provider changes and
genuine registry/sandbox permissions retain their scoped checks. No worker is launched.

Cleanup previews only marked toolkit-owned local execution runs:

```powershell
python .specify/extensions/program-kit-governance/scripts/execution_history.py --repository . --plan
python .specify/extensions/program-kit-governance/scripts/execution_history.py --repository . --apply
```

Automatic retention keeps the latest five completed runs. Failed and interrupted runs are protected;
--include-failed explicitly includes failed diagnostics. Interrupted/unowned/linked paths and arbitrary
old recovery/evidence files are never deleted. Consumer historical cleanup requires its later
inspectable migration assessment, not a blanket recursive removal.

Measured disposable acceptance across local Development runs: four guidance phases plus
implementation preflight took 0.005–0.007 seconds, created zero maintained artifacts and required zero
approval records. Legacy engineering relocation, preview and retry took 0.562–0.583 seconds. After deleting
governance, toolkit state and extensions, native restore took 0.803–0.826 seconds and real build/test/
architecture/package verification took 7.866–22.043 seconds. Incorrect behavior was rejected in 4.161–11.868
seconds. Logs are under artifacts/standalone-engineering/ and validation-runs/.

Real installed-Specify offline upgrade fixtures completed installation coherence in 6.0–7.0
seconds; inspectable preview took 0.38 seconds. These fixtures include preserved active features,
interruption and retry. Offline runs with changed dependency inputs correctly returned pending
verification (exit 3); these timings do not claim network restore or application/release acceptance.
The recorded measurements are in artifacts/maintenance-flow/local-upgrade-timings.json.

The previous domain-slice lifecycle required phase-obligations.json, phase-context.md,
obligation-design.json, obligation-review.json, semantic-contract.json, verification-plan.json and
verification-results.json in addition to normal plans/tasks; .NET/API added further attestations.
The equivalent new guidance fixture maintains none of those seven files. The old receipt-dependent
fixture could not proceed without constructing/renewing that state, so no comparable old complete
runtime is claimed. These are local fixture measurements, not a universal upgrade SLA; network,
actual builds and tests account for the remaining engineering time.

Consumer upgrades use `speckit.program-kit-governance.upgrade` and the maintained
[upgrade method](../extensions/program-kit-governance/references/consumer-upgrade.md).
The isolated attempt reproduces owned ignored installation assets and preserves source
setup/customization; destination activation uses the existing updater and tested recovery.
The single coordination record holds scoped findings and bounded migration briefs.
Ordinary pre-spec intake and planning refine matching owner/contract scope; dependencies
stay in existing plans/tasks. Valid requirements, confirmed intent, task IDs and completed
work survive selective repair. A new toolkit default offers supported retention or explicit
reviewed adoption. Shared incompatibilities due for upgrade must be resolved before
activation; credible future implementation migrations can remain deferred.

Scans and reports are regenerable views. They are never native application build/runtime
inputs. Toolkit convergence, current affected tests, substantive review and destination
activation remain separate outcomes. External rollout cannot be undone by worktree recovery.
Maintenance evidence export is bounded, sanitized and local; sharing is a consumer action.
