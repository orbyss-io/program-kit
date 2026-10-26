# Native phase engineering: implementation plan

Date: 2026-10-26.
Status: agreed design, prepared for implementation; no implementation or acceptance claimed.
Baseline: `705c8088` on `codex/bootstrap-intake-analysis`.
Checkout: `C:/Users/tech_/Code/program-kit/artifacts/worktrees/bootstrap-intake-analysis`.

## Outcome and authorization boundary

Make research and technical decisions usable throughout native Spec Kit delivery. Strengthen the
existing post-plan review, carry selected approaches into tasks and coding, and resolve consequential
discoveries in their owning documents before continuing dependent work. Keep the existing native
commands, authored artifacts, human review points and optional engineering helpers.

The user has accepted the design below. The fresh-session execution request can authorize all work
sections together; do not manufacture an approval round between routine implementation sections.
Investigate new material uncertainty before changing agreed product or architectural meaning.
This document is a contributor implementation plan, not a new required consumer artifact.

Do not read, change, quote, package or upload private consumers, their conversations or documents.
Use fictional examples only. Do not start interactive intake, paid coding workers or provider I/O.
Do not install device toolchains. Agents may restore declared project packages using installed tools.
No publication, tags, merge or consumer modification is authorized by this plan. Commit/push follow
the executing session's explicit user authorization; writing this plan does not perform either.

## Reconciled starting point

- `after_plan` already invokes `speckit.program-kit-governance.architecture-check`. This is a gap in
  the depth and visibility of the review, not an absent hook registration.
- `after_tasks` already runs architecture-check followed by native `speckit.analyze`. Preserve the
  explicit invoke/wait/resume behavior and consumer hook configuration established in `6c472846`.
- The phase helper produces relevant reference pages. It does not judge design or implementation,
  invoke a coding method, execute application checks or prove that an agent followed guidance.
- `57ab01de` and `705c8088` added framework-native mechanism guidance, EF migration references and
  qualification work, and corrected obsolete coding documentation. Preserve and extend their owners;
  do not recreate a competing EF repair or infer unrelated runtime qualification from those results.
- Native implementation guidance has focused checks and human pauses, but the connection from
  researched decisions to task-local coding practice remains implicit.

Recheck HEAD, instructions, ownership and dirty changes at execution time. These facts describe the
baseline, not a license to overwrite later work. Local tests and package CI have distinct proof limits.

## Settled design

1. Specify owns user-observable behavior, scope, journeys, rules and outcomes. Planning owns the
   research needed to justify technical choices: authoritative documentation, exact selected-version
   facts, applicable coding patterns, security guidance and Program Kit integration knowledge.
2. Planning fixes responsibilities, contracts, important lifecycle/failure semantics and consequential
   constraints. A proposed private file/class arrangement may evolve during coding without a human
   approval for every refinement. Material architectural or product changes need the relevant decision.
3. Patterns are adapted while preserving their explicit commitments. Exact templates apply when a
   selected generator requires them; catalog qualification is not a prerequisite for a local design.
4. Core capability contracts express semantic promises. Application/process owners coordinate business
   workflow. Providers implement concrete mechanisms and keep SDKs, platform IDs and reconciliation
   state private. Not every infrastructure capability belongs in a catch-all business-domain Core.
5. Review the first coherent increment of a new or uncertain approach before replicating it. This is
   a focused technical review; it does not automatically add a human checkpoint to every task.
6. Implementation continues targeted research when code exposes a missing fact or invalid assumption.
   Consequential findings feed back into spec, research, plan, ADR or tasks as appropriate.
7. Missing bookkeeping files, historical hashes or toolkit statuses do not prevent native delivery.
   Real unanswered decisions, invalid contracts and engineering failures still constrain dependent work.

## Work section 1: substantive post-plan review

Extend the existing architecture-check command's after-plan behavior. Reuse the grilling interview
method for genuine unsettled choices in the same conversation; routine facts are the agent's research
responsibility. Do not launch another coding agent or require every plan to undergo a lengthy interview.

The reviewer must inspect the actual spec, research, plan, contracts/data model and relevant accepted
architecture, not just render the reference index. Review proportionally:

- Fit to required outcomes, authorization, ownership, domain boundaries and failure behavior.
- Alternatives, including the selected framework's native mechanisms and extension points. Explain
  the unmet requirement before introducing equivalent custom infrastructure.
- Applicability and version of consulted sources; distinguish documented facts, local assumptions,
  justified decisions and unknowns requiring an experiment or platform qualification.
- Contract semantics, lifecycle transitions, data ownership, compatibility and security consequences.
- Selected coding approaches, important invariants/adaptation points, and how they will be verified.
- Technical risks and useful early checks; distinguish plan review from compilation/runtime evidence.

Present a concise technical walkthrough with links to decisions, their reasons and meaningful trade-offs.
Resolve material questions before dependent task generation. A supported applicable default need not
be presented as an unanswered question. Do not reopen every previously accepted choice. Preserve actual
human acceptance versus agent recommendations; a Proposed ADR is not a human-approved override.

Make native after-plan dispatch explicit enough that a recommendation or printed command marker is not
reported as execution. If review pauses for a decision, resume the remaining native flow afterward.
Respect disabled/removed hooks and native conditions. Inspect actual installed native plan behavior
before deciding whether a small append to `speckit.plan` is necessary; preserve upstream ownership.
Do not add a second mandatory reviewer/hook when the existing one already owns this activity.

## Work section 2: carry decisions into tasks and coding

In ordinary plan/research/ADR content, make consequential choices easy to trace to their source facts,
constraints, rejected alternatives where useful, and checks. Do not prescribe a mandatory table or a
second architecture model. Avoid copying entire manuals or the complete knowledge catalog into context.

Tasks must preserve the chosen responsibilities, relevant methods/patterns and their checks. A task
can refer to a plan section rather than duplicate it. Group work into coherent outcomes and put a
focused first increment before widespread replication of an unfamiliar approach.

Strengthen the existing native implement command and implementation-check guidance into an actionable
coding method, using the current skill/command packaging. Do not add a new routing hop that merely says
to follow patterns. For the current task or coherent increment:

1. Read its intended behavior, owning responsibility, selected decisions and relevant existing source.
2. Load focused applicable pattern, integration/security guidance and exact dependency facts. Treat
   lexical reference selection as a starting point; correct missed or irrelevant context through review.
3. Identify the commitments to preserve and the local adaptation. Prefer actual framework capabilities
   before introducing wrappers, runners, parsers, extra projects or lifecycle owners.
4. Implement the smallest coherent case. Research an exposed missing fact rather than guessing or
   treating an agent-written task as authority for an unjustified design.
5. Run the appropriate focused compiler/analyzer, architecture, security and behavior checks. Review
   actual source against the intended semantics before replicating the approach where it is uncertain.
6. Resolve material deviations through the owning documents; preserve agreed human review pauses.

Do not mandate a machine-generated file map, coding-unit manifest, exact every-file blueprint or
per-task full-app acceptance. Generators remain optional. Preserve local technology choices and actual
framework contracts. A source review, passing test and human acceptance are separate claims.

## Work section 3: feedback and finding resolution

Define one reusable method in a focused existing reference or a small shared reference, linked from
the phase owners. Do not duplicate long instructions across every command. Use existing documents or
readable review/progress notes; no required database, finding schema, fingerprint or lifecycle state.

| Discovery | Owning correction | Dependent action |
| --- | --- | --- |
| Missing/contradictory product behavior | Spec; clarify with human where needed | Revisit affected design/tasks |
| Invalid technical assumption or contract | Research/plan/ADR | Resolve choice and update affected tasks |
| Missing coverage, dependency or task ordering | Tasks | Correct affected sequence/checks |
| Code violates a valid decision | Implementation | Repair and check the affected behavior |

For a consequential finding, state evidence/source location, consequence, proposed resolution and
affected work. Investigate accessible facts, identify the appropriate decision owner, resolve or
explicitly defer with bounded scope, update affected documents and rerun relevant review/checks.
Continue independent ready work. A missing status note is not itself an engineering failure.

Do not silently amend the plan to justify a consequential coding deviation. Do not use a previous
plan to defend an invalid assumption. Reopen only dependent conclusions, preserve unrelated accepted
decisions and completed tasks/IDs, and reconsider prior checks only where their inputs are invalidated.
Native Analyze stays read-only: report its findings first, then perform authorized corrections openly.
Keep unresolved items visible in the normal final phase report and next-action handoff.

## Source owners to inspect and change proportionally

- `extensions/program-kit-governance/commands/speckit.program-kit-governance.architecture-check.md`
- `extensions/program-kit-governance/commands/speckit.program-kit-governance.implementation-check.md`
- `extensions/program-kit-governance/commands/speckit.program-kit-governance.phase-context.md`
- `extensions/program-kit-governance/references/phase-evidence.md` and relevant programming guidance
- `extensions/program-kit-governance/scripts/phase_obligations.py` and `references/phase-obligations.json`
  only where routing/first-page guidance needs a real change; do not turn them into a semantic engine
- `extensions/program-kit-governance/extension.yml`: align stale descriptions with actual behavior
- `presets/program-kit-governance-preset/templates/plan-governance.md` and `tasks-governance.md`
- `presets/program-kit-governance-preset/commands/speckit.tasks.md` and `speckit.implement.md`;
  add a minimal native plan append only if inspection shows it is needed
- `docs/consumer-engineering.md`, `docs/coding-context.md`, `docs/coding-evaluation.md` and related
  active coding docs; remove contradictory obsolete protocol instructions in the touched route
- Existing native registration/ownership, archives and installed-output mechanisms and their tests
- `tests/validate_native_phases.py`, relevant focused knowledge/package tests, and
  `tests/validation-inventory.json`; use existing owners instead of a parallel validation map

This is a starting map, not an instruction to edit every file. Trace producers and installed output.
Do not broadly delete optional historical helpers or restructure unrelated domains under this repair.
If introducing or substantially reshaping a skill, read the skill-creator instructions first.

## Verification and completion criteria

Read `AGENTS.md`, the development skill and `docs/validation.md`. Use the existing prepared Python
when importing Spec Kit. Start with Integrity, inspect Affected selection, then execute the affected
checks against the implementation baseline. Follow the single inventory's bounds and prerequisites.
No full matrix fallback, device installations or production workaround for a local host limitation.

Cover these cases with proportionate maintained fixtures and source/output review:

1. Native commands survive installation with the intended extensions/appends and one configured
   after-plan architecture review; after-tasks architecture review and Analyze remain ordered.
2. Installed post-plan guidance examines alternatives and real source facts, presents decisions, pauses
   for a material question, and describes resumption without claiming a command marker is execution.
3. A simple independent/custom stack can proceed without toolkit approval files, optional .NET
   tooling or a forced interview about already settled defaults. Respect disabled hook configuration.
4. A synthetic unjustified custom runner is challenged using the framework's native mechanism;
   a justified supported extension remains possible. Preserve the completed EF regression ownership.
5. A selected pattern's semantic commitments and adaptation reach task-local coding guidance, including
   focused source review/checks at the first coherent uncertain increment.
6. A synthetic implementation discovery changes the relevant plan/contract and dependent tasks while
   preserving unrelated decisions, completed IDs/checkmarks and agreed human pauses.
7. Native Analyze is not instructed to mutate files; its findings feed an explicit correction step.
   Missing historical status does not become a gate, and agent proposals cannot become human acceptance.
8. Reference routing remains scoped, standalone governance tolerates absent optional technology
   references, and real archives/installations carry the changed guidance without retired engines.

Do not pretend instruction assertions demonstrate an agent making correct technical decisions.
Deterministic checks establish routing, preservation, installed content and specific executable behavior.
Supplement with a clearly labeled, manually authored synthetic walkthrough from design alternatives
through tasks, one coding increment and a finding fed back to the plan. It may expose gaps but is not
observed agent obedience, independent human acceptance or actual provider/platform qualification.
No coding agent inside deterministic validation. Any further live trial needs its own authorization.

Keep the shipped published Orbyss host, CShells/Nuplane default and managed exporter intact. Do not
change profile pins, consumer locks, supported CI platforms, version or external dependencies for this
guidance repair without a demonstrated separate need and the relevant authorization.

At completion, retain a concise review index with changed owners, before/after behavior, installed
excerpts, synthetic walkthrough, exact executed checks/results/costs, unresolved findings and limits.
Distinguish source implementation, deterministic validation, observed agent behavior, human review
and release status. No local plan correction or green fixture is an upstream publication claim.

## Fresh-session execution request

Use the prompt supplied with this plan. It should direct the implementer to execute all three work
sections, preserve the settled design, validate through existing owners and review the whole diff.
The implementer should report an actual completion or a concrete remaining blocker, rather than stop
after adding another plan. This session only materialized the plan; implementation has not started.
