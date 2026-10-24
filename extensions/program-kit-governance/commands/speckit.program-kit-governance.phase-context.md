---
description: Supply applicable architecture and coding guidance before work.
scripts:
  py: scripts/phase_obligations.py
---
Locate the current Spec Kit feature. Run `{SCRIPT} project --feature-dir <feature> --phase planning`
before planning. Run `{SCRIPT} project --feature-dir <feature> --phase tasks` before tasks.
The after-plan hook already checked the planned graph; task drafting carries those choices without
immediately repeating that check. The after-tasks and combined implementation-check hooks validate
the current graph before affected coding. Do not invoke phase-context again before implementation.
Use the returned phase actions and canonical decision constraints before choosing patterns.
Text output is paged to fit tool transport. A first page is not the complete guidance: use the
reported --page continuation or --only <id> at the affected decision. Keep reads bounded instead
of requesting full JSON inventories or combining whole references. Before proposing .NET physical
projects, use --only dotnet-boundaries and the Modular DDD topology section of the technology profile.
Map accepted contexts/modules to projects, packages, namespaces and dependencies in the normal plan;
semantic example names in ADRs do not supersede the physical topology.
Their conditions, prohibitions and exceptions are binding guidance, not optional explanation.
Scoped accepted targets and feature ownership inform routing before a plan or project exists.
Resolve reported associations/conflicts; repository-wide adoption does not select every owner's mechanisms.
Repeated applicability is labelled with `scope-N`; each label applies only to the canonical rules marked with it.
The assembled text brief has a maintained UTF-8 byte budget, including observed context and wrappers.
`PKC026` reports overflow without truncating duties: narrow the actual operation/owner paths, or inspect
a concrete responsibility with `--only`. JSON is an explicit diagnostic/deep lookup view; do not append
the whole JSON view to an ordinary brief or concatenate every focused section.
Use focused section lookup for a concrete unresolved choice, not a checklist to reread every source. Use `--only <id>`
for a focused follow-up. Apply their conditions to concrete design/code choices;
record decisions, exceptions and actual required tests in the existing plan and tasks.
Use the plan template's `Operation implementation map` for actual ownership/results and applicable
cancellation/deadline, cleanup/uncertainty, transaction/replay, admission/bounds, concurrency,
configuration/time and activation/drain decisions. State ownership from the first acquisition or
external identity through every following failure edge. Task drafting carries compatible selected
patterns/examples or supported manual alternatives, first adverse cases/test owners and the first
coherent compiler/analyzer/focused checks before expansion. Missing consequential choices block only
dependent source work. Investigate accessible facts locally; ask humans only for missing material
intent, architecture, risk or authority. Update the actual spec/ADR/plan/tasks where affected and
retry scoped analysis/preparation then fresh preflight. Toolkit representation and environment gaps
need their owning repair/preparation route; a rule list or reading receipt cannot unblock them.
For attributable source ownership and evaluation routes, use the single discovery entry point:
`python .specify/extensions/program-kit-governance/scripts/knowledge_discovery.py catalog --requirement <id>`.
Add `--resolve` for actual canonical declarations. This lookup is regenerable output, not another
consumer catalog or acceptance record; source availability and declared routing do not prove application.
When a selected foundation composition affects configuration, link its existing
`docs/architecture/foundation-configuration.md` ownership/flow reference and the redacted
`eng/foundation_composition.py --repository . --effective` view. State whether the view
projects configured sources or observes activated options. Report relevant overrides,
their owner and change procedure; distinguish tunable operational values from protocol
constants, fixed admission constraints and compatibility-sensitive product policies.
Regenerate managed views through normal sync when their source contracts/composition change.
Never put secret values into responses, design documents, diagrams or browser exports.
Use the project's analyzers and targeted tests during implementation. Do not create phase-context,
obligation-design/review, semantic-contract or proof-attestation files. No renewed human approval
is needed for generated context, changed toolkit bytes or test execution.

## Retained feature planning decisions

The projection names open feature-plan prerequisite IDs, owners and tasks from retained history.
Draft their resolutions in the normal plan/contracts; pending review does not forbid that drafting.
After the actual normal design review, record each exact resolution with:
`python .specify/extensions/program-kit-governance/scripts/feature_plan_decisions.py record --feature-dir <feature> --prerequisite <id> --evidence "<feature>/plan.md#Exact heading" --reviewer "<actual reviewer>" --provenance "<actual review context>"`.
This preserves a small inline plan record and binds its reviewed section and existing intent/condition.
It creates no separate receipt or new human gate. Never invent human approval or substitute an agent's
review for a required ADR acceptance. Changed evidence reopens only its dependent decision.
Readiness and implementation consume this same resolution without changing the approved bootstrap ledger,
confirmed intake, constitution, ADR history or original approval hashes. A plan cannot close compatibility,
delivery, rights or production evidence. Missing legacy annotations are diagnosed for the affected decision;
do not automatically rewrite an existing approved plan.

## Task drafting and resume (before_tasks)

For tasks, use `--phase tasks` even when resuming. Inspect existing tasks.md first.
Run the ordinary setup_tasks script once to resolve the feature and composed tasks template;
reuse its result in the same turn. For a new draft, read spec.md, plan.md and the constitution,
then immediately persist a draft before optional
documents, detailed reference lookup or whole-plan validation. Use the installed
`python .specify/extensions/program-kit-governance/scripts/task_draft.py prepare --feature-dir <feature> --phases US1_create US1_list US2_process ... closure dependencies`
with actual operation group identifiers derived from the specification. A retained legacy draft keeps
its existing phase identifiers. Minimal enabling tasks belong to their first proving operation;
there is no all-story foundation barrier. All progress stays in tasks.md;
the inline checkpoint records drafting progress, not acceptance, approval or test evidence.
`prepare` also reports configured document ownership. If original preservation records are
declared in `eng/retained-inputs.json`, inspect the exact target with
`python eng/retained_inputs.py inspect --repository . --path <document>`.
Keep frozen evidence byte-identical. Declare a referenced frozen file as `read` in a
`## Document outputs` table (`Task | Path | Mode`); put current changes in a distinct
active index/versioned proposal linked to the preserved evidence. Draft saving, finalization
and delivery preflight reject frozen write targets. `acknowledge-inputs` cannot remove or
replace a previously bound frozen record. Do not regenerate a failing original hash.
For a materialized foundation selection, inspect
`python eng/foundation_setup.py --repository . --status` once. This read-only view
names the latest real setup results, changed-input state and required live service checks.
Carry existing maintained infrastructure into the operation plan instead of authoring it again.
An unchanged recorded check is component/integration evidence; a removed or changed service still
needs its applicable setup check before the dependent operation. A newer failed/incomplete result
remains unresolved. Drafting never invokes `--execute`, restores packages or starts services.

On resume, run `prepare` before repeating design preparation. It returns completed/remaining phases and changedInputs without replacing
the draft. Reuse saved phases and preparation when inputs are unchanged; do not reload every
optional document or repeat broad reference preparation. Preserve IDs, checked boxes and edits.
For changed inputs, review only affected phases and their dependencies, edit those tasks in place,
then use `acknowledge-inputs` after that review. An unmarked existing tasks.md is preserved:
inspect and fill only gaps directly rather than starting over.

Write each completed phase to an ignored temporary content file, then persist it with
`task_draft.py save-phase --feature-dir <feature> --phase <id> --content-file <file>`.
Continue unique task IDs from the saved draft. Save each operation group as soon
as it is ready; dependencies/parallel examples and the final coverage pass come last.
This incremental persistence replaces any instruction to hold all phases in memory before
writing tasks.md. Include constitution-required tests with risk-selected sequencing,
security, ownership and real-provider checks. Missing compatibility inputs/admission work
become owned prerequisite tasks with explicit dependencies; do not run probes, provision
services, restart bootstrap, alter approvals or change accepted pins while drafting.

After every planned phase and the final coverage/format review are saved, run
`task_draft.py finalize --feature-dir <feature>` for a marked draft. For an unmarked existing
document, finish that same review directly without requiring helper metadata. Then dispatch mandatory after_tasks hooks,
including read-only speckit.analyze. Do not invoke analyze on an incomplete draft or after
each phase write, and do not claim task generation completed while a draft remains.

Use the resolved Story delivery map and story sizing criteria. Keep review per runnable story;
earlier checkpoints need explicit agreement. Persist delivery/roles/decisions/effort in the same
current tasks checkpoint using `task_draft.py delivery` and `references/phase-evidence.md`.
Fresh-feature adoption requires archived abandonment and constitution amendment/ratification,
then every Spec Kit phase from fresh spec; old implementation checkmarks grant no new authority.
