---
description: Turn a product idea into a confirmed Program Kit bootstrap intake using Program Kit grilling for adaptive Q&A, a C4-aligned domain map, and change-aware re-analysis, then provide the safe one-line bootstrap command. Use for new Program Kit projects and for revisiting changed intake artifacts; do not use for ordinary feature specifications.
---

## Purpose

This skill is the Program Kit front door. The user may begin with an incomplete natural-language
description and does not need to create or name an initial-design file. Read
`references/intake-method.md` in full. Read `references/capability-index.json`, then only the
references routed by capabilities relevant to the user's description. Do not enumerate the entire
extension or ask about capability categories that are absent or explicitly excluded.
It conducts adaptive intake before the bootstrap workflow begins.

Before the first interview round, read and follow Program Kit's own
`speckit.program-kit-governance.grilling` skill at
`.specify/extensions/program-kit-governance/commands/speckit.program-kit-governance.grilling.md`
(repository-relative in the initialized consumer). This shipped command is the canonical interview
contract, also exposed as `$speckit-program-kit-governance-grilling`. Use it in this conversation;
the user need not invoke a second skill. Its question ordering, recommendations, answer handling,
and shared-understanding review apply with the intake scope and default policy in
`references/intake-method.md`. Do not substitute an unrelated locally installed `$grilling` skill.
If the shipped command is missing, report the incomplete installation instead of silently using
another interview method.

Keep discovery bounded. Do not enumerate the repository, `.specify`, installed skills, references,
schemas, or implementation scripts. Inspect only an explicitly supplied source artifact and existing
canonical intake paths. Treat the JSON schemas and Python scripts as executable contracts; do not
open them to rediscover shapes or behavior. When the conversation converges, read
`references/intake-artifacts.md` once and author from its compact contract.

## Execution boundary

The skill may create and validate intake artifacts inside the repository. It must never run
`specify init`, Program Kit installation or update commands, or the outer
`specify workflow run program-kit-bootstrap` command. Spec Kit starts separate agent workers for
workflow command steps; an interactive agent starting the outer workflow would nest execution. On
Windows, setup from the sandbox identity can also leave generated paths with unsafe ownership.

Do not request escalation, create an approval rule, wrap the workflow command in another shell, or
start another interactive agent. This skill is guidance-only for the outer-workflow launch.
The human runs the final command from a normal user-owned PowerShell or WSL terminal in the
repository root. Stop. Do not call a shell tool to launch it.

## Entry and re-entry

On every invocation:

1. Treat `$ARGUMENTS` and the current user message as project intent, corrections, or requested
   re-analysis—not as a required path.
2. If `docs/architecture/bootstrap-intake.json` exists, run
   `python .specify/extensions/program-kit-governance/scripts/bootstrap_intake.py changes --json`.
3. If registered artifacts changed, follow the re-analysis procedure in `references/intake-method.md`.
   For a changed `workspace.dsl`, use the registered importer in `scripts/architecture_map.py` and
   write an import candidate outside the canonical paths. Never overwrite the canonical map or
   discard unsupported syntax before the user reviews the impact.
4. If no confirmed intake exists, begin from the user's description. Reflect the understood purpose,
   scope, actors, and first observable outcome before asking questions.

## Adaptive intake

Use Program Kit grilling's decision tree and frontier rounds with the bootstrap-relevant scope in
`references/intake-method.md`. Apply clear Program Kit defaults automatically and summarize them
in the final review. Ask about ambiguous intent, contradictory requirements, and material choices
that the defaults cannot resolve. Keep a compact question/decision record in
`docs/architecture/project-intent.md` so partial answers and changed decisions survive re-entry.

For every detected need separately record mechanism coverage, any Program Kit capability,
consumer domain-semantic ownership and profile, integration ownership, provider selection, and
decision state using `references/intake-artifacts.md`. Never infer that a managed mechanism owns
the consumer's business language or rules. In particular, Program Kit Forms may own rendering,
validation, editor, and schema mechanisms, while consumer form meaning, item references, pricing,
quantification, publication, and workflow semantics remain in consumer-owned modules and bridges.
Explain the consequences of a material deviation when asking about it. Say
"Program Kit has no declared managed capability for this need" for an unmatched need; do not claim
that Program Kit or the project cannot support it.

Keep user intent, Program Kit defaults, derived conclusions, proposals, and unresolved questions
distinct. Do not turn a suggested default into explicit user intent. Candidate vertical slices are
discovery signals only and begin with an actor or trigger and end in an observable outcome.

Before authoring, perform evidence-backed strategic analysis. Classify every subdomain as Core,
Supporting, or Generic. Propose bounded contexts only where model, language, ownership, lifecycle,
or consistency boundaries support them; do not turn pages, nouns, or cross-cutting concerns into
contexts. Record responsibilities, explicit non-responsibilities, language, owned data, invariants,
lifecycle, separation rationale, and split triggers. Challenge suspicious boundaries explicitly.
Preserve every separately named source journey and its observable outcome.

Prepare **founding decision candidates** for the proposed architecture: decision question,
recommended option, genuine alternatives, rationale, consequences, confidence, source evidence,
and affected map identities. Present these alongside the draft map. They are focused prepwork for
the architecture phase, not ADRs and not accepted decisions. Intake confirmation confirms an
accurate provisional synthesis only. The architecture phase must challenge/refine the candidates,
materialize them as Proposed ADRs, and include those exact ADRs in the post-architecture approval.

## Required artifacts

After the questions converge, create or update:

- `docs/architecture/project-intent.md`, including stable Q&A/evidence IDs and a compact coverage and
  disposition summary;
- `docs/architecture/architecture-map.json`, matching
  `references/architecture-map.schema.json` and containing the strategic model plus System Context,
  domain/subdomain landscape, Context Map, context/module decomposition, and one dynamic view per
  source journey;
- `docs/architecture/workspace.dsl`, generated from the canonical map with
  `python .specify/extensions/program-kit-governance/scripts/architecture_map.py export --map docs/architecture/architecture-map.json --format structurizr-dsl --output docs/architecture/workspace.dsl --force`; and
- a draft synthesis of `docs/architecture/bootstrap-intake.json` matching
  `references/bootstrap-intake.schema.json`.

Use `references/intake-artifacts.md` as the authoring contract. Do not read either JSON schema or
either Python implementation before writing. Prefer one focused read batch, one artifact-write
batch, and one export/validation batch; expand only to resolve a concrete validator diagnostic.
Never print whole generated artifacts or repository-wide diffs during verification.

The canonical map owns semantics. The DSL is a reviewable C4 projection and an import source. Mark
inferred bounded contexts, capabilities, ownership, and relationships `proposed` or `unresolved`;
intake does not accept architecture. Preserve the exact hash, byte count, importer ID, and importer
version for every source and bound artifact.

After exporting the DSL and refreshing the draft artifact hashes and byte counts, run:

`python .specify/extensions/program-kit-governance/scripts/bootstrap_intake.py validate-draft --json`

This read-only check validates draft semantics and bound artifacts without confirming the intake.
Repair its diagnostics before the final review; never mark an unreviewed draft confirmed to make
validation pass.

After generating the projection, tell the user: "To open the C4 diagrams safely on localhost, ask
`View the C4 projection` or invoke `$speckit-program-kit-governance-view-c4`. Program Kit validates
freshness and the draft artifact hashes first and does not change the canonical architecture map,
confirm the intake, or accept the architecture."

Present the concise synthesis, subdomain classifications, context challenges, founding decision
candidates and alternatives, map changes, applied defaults with their rationale and consequences,
and assigned/deferred questions with their triggers. This is also grilling's shared-understanding
review; do not ask for a separate approval before preparing the draft artifacts.
Ask for confirmation only after the
semantic gates pass and there are no invisible or unclassified gaps. State explicitly that this
confirmation does not approve architecture or ADRs. Do not mark the intake `confirmed` from silence or inference.
After explicit confirmation, set its status to `confirmed`, refresh every artifact hash and byte
count, and run:

`python .specify/extensions/program-kit-governance/scripts/bootstrap_intake.py validate --json`

Repair validation failures and reconfirm if a repair changes meaning. Do not run bootstrap until the
contract validates.

## Required handoff

After successful validation, tell the user to run the command from a normal user-owned terminal in
the repository root. Always emit exactly one physical, fully substituted command line in its own
fenced block. Use repository-relative forward-slash paths and double-quote each `name=value`
argument. Include no placeholders, line continuations, environment variables, substitutions, shell
operators, or shell-specific syntax:

```text
specify workflow run program-kit-bootstrap --input "bootstrap_intake=docs/architecture/bootstrap-intake.json" --input "integration=auto"
```

If the user explicitly requested automatic approval and ratification, append
`--input "auto_approve_and_ratify=true"` to that same physical line. Never add this input unless the user explicitly requests automatic approval and ratification.

If preflight later reports `PROGRAM_KIT_CONCURRENT_BOOTSTRAP_RUN`, tell the user to verify whether
the listed run still has a live normal-shell workflow process. Never abandon a live run. For a stale
record, display the diagnostic's exact recovery command for the human to run; do not edit workflow
state directly.

After a workflow pause, report the run ID, review packet and named artifacts, and one fully
substituted, single-line resume command. A rejection keeps the run paused for revision and packet
regeneration; never describe rejection as approval failure or encourage approval of stale content.
