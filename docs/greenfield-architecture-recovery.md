# Greenfield architecture placement and recovery of bd6be6ca

The PriceCalculator failure was an impossible architecture handoff, not a missed intake filename
question. The saved inventory contained only an absent `Directory.Build.props` convention. Seven
slot occurrences across browser BFF, Forms and Localization required .NET, npm or CShell targets.
The handoff allowed only inventory paths and prohibited scaffolding. Its draft command produced
empty scopes, targets and instances. The offline diagnostic reproduced this exactly and showed
that explicit future paths already resolve provisionally without creating consumer manifests.

## Source correction

Architecture now owns an explicit placement declaration in each Draft selection target. Observed
inventory remains filesystem evidence; the repository sentinel is marked `origin: convention`
when absent. The brief authorizes architecture to derive future paths from semantic ownership,
deployment boundaries, conventions and supplied preferences. Intake must not ask product users
for project/package/shell filenames or target IDs.

Each declaration has `state` (`observed` or `planned`), canonical element `owner`, `decisionIds`
and `rationale`, in addition to the existing target kind, path, role, scope and shell. Owner-linked
Proposed or Accepted ADRs must appear in selection authority and the canonical map with current
source hashes. Draft provenance validation checks missing/stale ownership and decision evidence,
path containment and cross-platform hazards, case collisions, consumer-file kinds, slot roles and
scope compatibility. New bootstrap Drafts require every target's declaration and nonempty
composition instances. Legacy selections without this added metadata remain readable; once a
declaration is present its provenance is checked by resolution and acceptance too.

The existing approval transition still promotes reviewed founding ADRs and the Draft together.
Planned origin persists after an approved scaffold. Architecture does not restore packages or
materialize files. Apply continues to reject absent consumer-owned .NET/npm manifests.

Research now receives the same managed option projection as architecture. Forms' renderer group
currently lists Angular, React and Vue. The saved Blazor research proposal remains unresolved;
these changes do not select React for PriceCalculator or assert that a custom Blazor adapter is
impossible. Architecture must reconcile the proposal with supported options or a reviewed adapter/
override, preserving approved product semantics. All generated validation commands carry the
actual run ID.

An architecture worker that cannot proceed records a structured reason, owner and resolution via
`record-architecture-blocked`. Both the legacy output gate and the full validation batch report
that prerequisite before missing-output errors. A deliberate context rebuild archives the report
under the run's `program-kit-context` directory. New workflows name the process step
`architecture-dispatch`; its completion means only process exit, and `validate-architecture-output`
runs the full architecture batch. Spec Kit's command executor still reports zero-exit processes as
completed. Historical state and unavailable worker streams are not rewritten or reconstructed.

## Recovery procedure for the existing run

The corrected source must first be delivered through a coherent Program Kit installation,
including regenerated integration skills. The correction is part of the `0.10.1` candidate. Once its complete Release workflow succeeds
and the verified full release is available, use its documented sequential
`scripts/upgrade_program_kit.py --release-root ... --target . --integration codex` procedure from a
normal user-owned terminal. Do not patch only generated context or only an installed Python file;
the schema, resolver, command/skill and context contracts must agree. Verify installation versions
and retain the updater's evidence before continuing.

From `C:/Code/Orbyss/PriceCalculator`, run:

```powershell
python .specify/extensions/program-kit-governance/scripts/bootstrap_context.py prepare-architecture-recovery --run-id bd6be6ca --json
```

This helper accepts a failed `program-kit-bootstrap` run whose current step is
`validate-architecture-output` and refuses an already approved bootstrap. It validates the intake
handoff, preserves content-addressed copies of the failed context, workflow snapshot, event log, state, inputs
and authority artifacts, and rebuilds the architecture brief with the installed corrected source.
Its recovery manifest records original paths and hashes. It does not edit workflow state, inputs,
confirmed intake, the approved assessment or constitution. It does not dispatch a worker or start
another bootstrap. The architecture skill still performs its normal governance validation before
writing; the helper does not replace those approval/freshness checks.

Invoke the installed architecture skill in the consumer's user-owned Codex session with exactly
the helper's `architecture_skill_input` value:

```text
$speckit-program-kit-governance-architecture docs/architecture/bootstrap-intake.json; bootstrap context: .specify/workflows/runs/bd6be6ca/program-kit-context/architecture.json
```

This regenerates the missing architecture for the existing run. It must preserve confirmed intake
and approved assessment choices, reconcile renderer/provider compatibility, author placement with
Proposed founding decision provenance, and complete its structural and final validation. Review
the new proposals through the existing bootstrap approval gate; do not auto-accept them. If an
actual semantic change to approved choices is necessary, stop for the applicable assessment review
instead of changing its hashes or treating the context refresh as approval.

After the skill reports successful validation, run:

```powershell
python .specify/extensions/program-kit-governance/scripts/bootstrap_context.py validate-stage --stage architecture --run-id bd6be6ca --json
specify workflow resume bd6be6ca
```

Run the resume command only when validation passes. The installed Spec Kit CLI has no rewind or
`--from-step` option. Its supported resume command begins at the failed validator, so resume alone
cannot generate the missing architecture. Direct invocation of the installed skill above is the
supported generation path; the existing workflow then continues from its saved position and keeps
its original approval gates. Do not launch `workflow run` or bootstrap again over this run.

## Validation evidence and limits

- The supplied installed-consumer diagnostic reproduced the absent sentinel, seven unfillable
  slots, empty generated Draft and successful synthetic unmaterialized Forms resolution.
- `tests/validate_architecture_placement.py` covers a complete browser/forms/localization Draft,
  mixed observed/planned targets, missing provenance and bindings, wrong kinds/roles/scopes,
  traversal and case collisions, stale ADR hashes, unsupported Blazor option rejection, the
  existing acceptance transition and refusal to apply absent .NET/npm manifests.
- The same validator exercises the real Spec Kit workflow engine with mocked command dispatch
  (no agent process), proving that a zero-exit blocked worker fails the full gate with its primary
  reason and that resume retries that gate without redispatching the worker. Recovery tests verify
  archived diagnostics, source hashes and unchanged approval/input/state bytes.
- Recovery preparation was also run against a temporary copy of the actual `bd6be6ca` evidence
  with the corrected source installed in that copy: 17 source artifacts were preserved, all three
  absent target kinds had an authorized planning path, and commands used `bd6be6ca`. The actual
  consumer state, intake, decision register, assessment approval and ratification hashes remained
  unchanged.
- The bounded Development suite, bootstrap-context, governance-state and Codex bootstrap validators pass.
  Development required explicit setup of the pinned project-local schema runtime. The extra Windows
  initializer check required a short process-local PATH: the inherited 11,070-character PATH
  prevented cmd.exe from finding where.exe. No persistent environment or initializer change was made. Its offline
  bundle validation reports well-formed structure; it does not verify remote catalog availability.

This is deterministic evidence for the correction and recovery mechanics, not a claim that a live
architecture retry, package restore or deployment has succeeded. Remaining prerequisites are a
coherent corrected installation, architecture's compatible stack/provider and placement decisions,
successful artifact validation, and the existing human approval gates. Firefox cannot launch on
this local Windows host; CI retains authority for Firefox acceptance. Publication uses the separate
user-owned Release validation process described in `AGENTS.md`.
