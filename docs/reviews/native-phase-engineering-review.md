# Native phase engineering: implementation review

Date: 2026-10-26. Checkout: `artifacts/worktrees/bootstrap-intake-analysis`.
Branch/base: `codex/bootstrap-intake-analysis` / `705c8088`. Changes are uncommitted.
The [agreed plan](native-phase-engineering-plan.md) remains the supplied design record.
This index records implementation and review, not consumer approval or publication.

## Changed owners and before/after behavior

| Owner | Before | Delivered behavior |
| --- | --- | --- |
| [Architecture check](../../extensions/program-kit-governance/commands/speckit.program-kit-governance.architecture-check.md) | Hook existed; brief drift/reference guidance | Actual post-plan artifact review: alternatives, exact source facts, semantic/lifecycle/security contracts, selected methods, useful experiments and technical walkthrough; scoped same-conversation decisions and return/resume |
| [Tasks append](../../presets/program-kit-governance-preset/commands/speckit.tasks.md), [plan](../../presets/program-kit-governance-preset/templates/plan-governance.md) / [tasks](../../presets/program-kit-governance-preset/templates/tasks-governance.md) templates | Methods could remain implicit between plan and code | Decisions, reasons, commitments, adaptations and checks reach consuming tasks; first coherent uncertain increment precedes replication |
| [Implement append](../../presets/program-kit-governance-preset/commands/speckit.implement.md), [implementation check](../../extensions/program-kit-governance/commands/speckit.program-kit-governance.implementation-check.md) | Focused checks and human pauses without a complete task-local method | Read behavior/owner/decisions/source; load focused guidance and dependency facts; adapt commitments; code the smallest case; check/review semantics; correct consequential discoveries |
| [Shared feedback](../../extensions/program-kit-governance/references/engineering-feedback.md), [phase evidence](../../extensions/program-kit-governance/references/phase-evidence.md), [phase context](../../extensions/program-kit-governance/commands/speckit.program-kit-governance.phase-context.md), [Analyze append](../../presets/program-kit-governance-preset/commands/speckit.analyze.md) | Finding resolution implicit | Route findings to spec, research/plan/ADR, tasks or implementation; preserve unrelated acceptance/completed tasks; Analyze reports first, with separate authorized correction |
| [Phase helper](../../extensions/program-kit-governance/scripts/phase_obligations.py) | Local context named plan/tasks but omitted feature spec/research/data model | Existing local-guidance index includes those present documents; no semantic verdict, new state or application execution |
| [Native tests](../../tests/validate_native_phases.py), [archive smoke](../../tests/validate_package_smoke.py), [inventory](../../tests/validation-inventory.json) | Native preservation and focused knowledge fixtures | Configured after-plan dispatch/disable/condition/removal, installed guidance/links and actual archived append/reference preservation; narrow phase ownership inputs |

[Consumer engineering](../consumer-engineering.md), [coding context](../coding-context.md),
[coding evaluation](../coding-evaluation.md) and [patterns](../coding-patterns.md) explain the same
method through their current owners. Extension descriptions now describe actual native guidance.

The exact installed upstream native plan was inspected: it already requires hook invocation/wait,
distinguishes `EXECUTE_COMMAND:` from execution, and respects disabled hooks and conditions. No
plan append, second reviewer, lifecycle engine, findings database or bookkeeping gate was added.
After-tasks architecture review still precedes native Analyze. Human decisions remain actual
human decisions; technical review of an uncertain increment does not add an automatic human pause.

The completed EF work in `57ab01de` / `705c8088` remains the mechanism owner: provider-owned native
migrations, snapshots/history, supported extensions, separate deployment and read-only admission.
No EF runtime, profile, version, lock, dependency, Orbyss host, CShells/Nuplane or exporter change.

## Manually authored synthetic walkthrough

Everything in this section is a fictional review example authored for this change. It is not an
observed consumer conversation, coding-agent trial, compiled implementation or human acceptance.
It uses the existing [EF guidance](../../extensions/program-kit-dotnet/references/persistence-profiles.md)
and [qualified native example](../../extensions/program-kit-dotnet/references/examples/postgresql-lifecycle/README.md)
as source owners; it claims no new runtime/platform qualification.

1. **Behavior and alternatives.** A fictional request service must register a request and retain its
   identity; deployment credentials differ from runtime credentials. A draft plan proposes a custom
   migration executable/journal. The post-plan review asks what requirement native EF tooling cannot
   meet. Separate credentials alone do not answer that question. Research points to native EF
   artifacts and the selected project's actual package/lock facts; unavailable exact-version facts
   stay unknown until inspected. The revised approach keeps native migrations and a provider-owned
   context. A justified separate EF migrations assembly or SQL inside a migration remains available.
2. **Decision and method.** Research/plan explains that the request capability promises request
   identity and outcome semantics, application code coordinates registration, and the EF provider
   owns concrete persistence. The plan links source facts and checks rather than copying a manual.
   Private class/file arrangement is an adaptation point. The task for the first registration case
   links that decision and calls for focused build, identity/outcome tests and source review before
   copying the approach to other operations. The actual agreed requester walkthrough stays pending.
3. **One coding increment.** The implementer reads the task/spec/decision and existing registration
   source, then the focused persistence and security references. The proposed small increment uses
   the provider context and one request operation; SDK entities do not leak into the semantic
   capability, and application coordination does not move into the provider. Its checks cover
   identity preservation and the promised failure outcome. This paragraph describes a fictional
   source review, not a successful compiler or application test run.
4. **New technical evidence.** A fictional inspection of a synthetic seed dataset reveals duplicate
   legacy request keys. The planned unique-index migration assumed uniqueness. This invalidates a
   technical assumption, rather than authorizing either a custom migration engine or an invented
   product rule for merging requests. The finding cites the fictional duplicate rows, explains the
   deployment failure, proposes a pre-deployment check/correction and names dependent migration work.
   Product resolution of ambiguous duplicates still needs its actual owner; dependent deployment
   waits. Independent request rendering can continue.
5. **Owning correction, without rewriting history.** After a simulated decision to reject deployment
   with an actionable duplicate report (not merge requests), amend research/plan's migration
   precondition and the dependent tasks. The source review/checks that relied on unique legacy keys
   are due again; unrelated checks remain applicable. An Analyze finding would first be reported
   read-only, followed by this explicit authorized correction step outside Analyze.

Illustrative ordinary task notes before the discovery:

```markdown
- [x] T001 Define request identity/result semantics (plan: Request capability).
- [ ] T002 Author native provider migration (plan: Deployment; assumes unique legacy keys).
- [ ] T003 Exercise migration against synthetic existing rows.
- [ ] T004 Render request detail independently of schema deployment changes.
Review: requester walkthrough pending; pause dependent product expansion.
```

After the simulated correction:

```markdown
- [x] T001 Define request identity/result semantics (plan: Request capability).
- [ ] T002 Author native provider migration after duplicate-key precheck (plan: Deployment).
- [ ] T003 Prove duplicate rejection before DDL, then valid migration and read-only runtime admission.
- [ ] T004 Render request detail independently of schema deployment changes.
Finding: fictional duplicate keys invalidate only the migration's uniqueness assumption.
Simulated decision: report/reject duplicates before deployment; no automatic request merge.
Review: requester walkthrough pending; pause dependent product expansion.
```

This preserves completed `T001`, unrelated `T004`, IDs and the pending human pause. The walkthrough
exercises the meaning of the guidance through authored examples; it does not establish that an
agent would discover or correctly resolve such a finding.

The corresponding fictional plan correction is explicit rather than a silent justification:

```markdown
Before — Deployment: native EF migration may add the unique request-key index; existing keys
are assumed unique. Runtime uses a separate identity with read-only schema admission.

After — Deployment: the synthetic duplicate-key observation invalidated the uniqueness assumption.
Run a duplicate precheck before DDL; reject deployment with an actionable report on duplicates.
Apply the native EF migration only after the precondition holds. Test both rejected and valid rows.
Preserved decision: runtime uses a separate identity with read-only schema admission.
```

## Execution and installed-output review

Use the existing prepared Python
`C:/Users/tech_/AppData/Roaming/uv/tools/specify-cli/Scripts/python.exe` for Spec Kit imports.
The stale `artifacts/tools/validation-uv` environment points to a missing base interpreter; it was
not repaired or used for validation. No device toolchain was installed.

Exact executed commands (`$py` denotes that existing interpreter):

```powershell
./scripts/Test-ProgramKit.ps1 -Python $py
& $py scripts/run_validation.py --suite Affected --changed-from 705c8088 --list
& $py scripts/run_validation.py --suite Affected --changed-from 705c8088
& $py scripts/run_validation.py --check validate_knowledge_inventory --check validate_knowledge_sources --check validate_coding_patterns --check mechanics-installation --reason "reproduce new reference registration, source partition, mutation oracle and actual archived append failures"
& $py scripts/run_validation.py --check validate_device_handoff --reason "reproduce Git Bash parser access denial outside the task sandbox; syntax-only synthetic preparation scripts"
& $py scripts/run_validation.py --check validate_knowledge_inventory --check validate_knowledge_sources --check validate_coding_patterns --check mechanics-installation --reason "verify registered shared feedback, reviewed phase partition and corrected meaningful mutation/archive assertions"
./scripts/Test-ProgramKit.ps1 -Python $py
& $py scripts/run_validation.py --suite Affected --changed-from 705c8088
git diff --check
```

List-only Affected selection was inspected twice and retained at
`artifacts/native-phase-affected-selection.txt`; it had no gaps/deferred checks. The last Affected
run and isolated device-handoff retry used external-process access: the task sandbox prevented
Git Bash from creating its MSYS process object (`0xC0000022`). The existing parser then passed;
no generated preparation script was executed and no assertion/platform was omitted.

| Execution | Outcome / measured elapsed | Local diagnostic record |
| --- | --- | --- |
| Initial Integrity | 7/7 passed; 7.129s | [results](../../artifacts/validation-runs/20261026T133722Z-a36c36aa/results.json) |
| Initial Affected | 30/35 passed; five failing checks; 177.404s | [preserved results/streams](../../artifacts/validation-runs/20261026T133739Z-e9dabbb9/results.json) |
| Focused failure reproduction | Same four supported failures reproduced; archive build passed; 25.232s | [results](../../artifacts/validation-runs/20261026T134101Z-e955c293/results.json) |
| Isolated Bash-access retry | Device-handoff 1/1 passed; 2.379s | [results](../../artifacts/validation-runs/20261026T134105Z-6826357b/results.json) |
| Focused repaired checks | 5/5 passed, including prerequisite archive build; 28.870s | [results](../../artifacts/validation-runs/20261026T134207Z-68b2b894/results.json) |
| Final Integrity | 7/7 passed; 7.048s | [results](../../artifacts/validation-runs/20261026T134258Z-b7edc076/results.json) |
| Final Affected | 35/35 passed; 112.543s; no gaps, deferrals or overruns | [results/commands/streams](../../artifacts/validation-runs/20261026T134348Z-15df51cd/results.json) |

The five initial failures were investigated individually: missing shared-reference registration;
the touched phase-evidence remainder needing review/classification; an existing fingerprint test
whose old wording mutation had become a no-op; a new archive test wrongly assuming Analyze's
fragment had YAML frontmatter; and the Bash sandbox denial. Repairs register the real command
route, classify the actual shared method, mutate a unique canonical marker meaningfully, and
compare complete append content with or without frontmatter. No semantic assertion was weakened.

Every recorded run reports `sourceChangedDuringRun: false`. Final Affected binds commit `705c8088`
and dirty-input digest `9e71e5ff8b94d8ab1d78b7341a3fe4b599fc6152ef346ed710a515966e40acc4`.
Only this review record was completed after that execution; shipped guidance and checks were held
fixed. The final whitespace/diff review covers the completed report too.

Final Affected includes archive build/install, native phases, knowledge routing/source/partition,
composition, authored-work upgrade preservation, pattern/scaffold/seed, device-handoff, preview,
founding/frontier, host and async guidance, plus Integrity regressions. The linked result records
all 35 exact entrypoints and individual costs. It is the maintained Affected selection, not a full
browser/database/native-build matrix. The unchanged EF guidance regression cases ran; the completed
native PostgreSQL runtime qualification was not rerun for this prose/routing repair.

The [retained final installed output](../../artifacts/tests/native-phase-review/ad4fec4622ea4af2a6826f820f570b54/index.md)
contains seven installed command bodies and shared feedback. The source-only phase fixture exercises
native registration/configuration, unchanged upstream plan and scoped custom-stack read-only helpers.
The separate archive smoke installs actual four-component archives via native bundle ownership in a
clean space-path consumer, verifies shared-reference bytes, complete preset appends and rewritten
feedback links, and retains its normal validator accept/reject behavior. This is real installation
execution, not conversational hook execution.

Reviewed installed excerpts:

```text
plan: After emitting the block above you MUST actually invoke the hook and wait for it to finish...
architecture-check: Rendering references does not perform this review.
implement: Identify semantic commitments to preserve and the local adaptation.
analyze: Perform authorized repairs only in a separate explicit correction step outside Analyze...
feedback link: .specify/extensions/program-kit-governance/references/engineering-feedback.md
```

Final source/diff review and a fresh independent sub-agent review of the diff, retained installed
output and subsequent focused repairs found no remaining material defect. Section authors also
reviewed their own work; that is distinct from the independent review. Human acceptance remains due.

## Findings, proof limits and release status

Source review, deterministic installation/assertions, observed agent behavior, human acceptance
and release acceptance are separate claims. Deterministic fixtures run no coding agent and cannot
prove reasoning, source consultation or obedience. The synthetic walkthrough supplies no human
acceptance, provider operation authority, private consumer evidence or runtime qualification.
Local Windows results do not establish Linux acceptance. Firefox remains a known local-host
limitation; this guidance repair does not select a browser scenario or replace CI coverage.

No unresolved implementation finding remains from this work. The Bash restriction remains a task
sandbox limitation with a passing external-process retry; it is not a production workaround. The
original supplied plan remains untracked and unchanged, alongside the new review/reference files.
No other owner's source changes were present at start or overwritten.

The candidate remains unpublished `1.0.0-preview.1`. Local archive installation is development proof;
successful exact-source package CI and native publication approval remain due for a release.
No commit, push, tag or publication is performed. The next action is human diff/output review and
an explicit instruction if commit/push is wanted.
