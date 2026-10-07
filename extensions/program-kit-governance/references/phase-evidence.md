# Knowledge and engineering checks

`phase_obligations.py project` prints concise guidance before planning and tasks. The single
implementation preflight prints implementation guidance while validating planned architecture.
The single upstream registry is `phase-obligations.json`. Generated context is disposable.

`phase_obligations.py check` validates the declared `eng/architecture.json` graph after-plan,
after-tasks and before implementation. Before tasks, project `--phase tasks` rather than repeating
the after-plan check. The implementation preflight is the sole before-implement hook.
Roles, edges and capability owners must satisfy the adopted compilation boundaries before a build.
An empty initial graph or pure Core utility remains legitimate; it does not certify later runtime
bindings. Compiled inventory and actual activation/resolution/lifetime tests establish those checks.

Keep design choices and required tests in normal plan.md/tasks.md. Implement behavior and
architecture tests in the repository. Use `eng/Invoke-RepositoryVerification.ps1 -Scope Focused`
or `-Scope Affected` while coding. Retain the complete implementation baseline and inspect selection
with `-Plan`; do not select by the last edited file alone. Progress saves and resumes earn only
checks invalidated by changes. `phase_obligations.py finish` returns progress for open tasks/drafts;
closed features or an explicit `--handoff` run complete acceptance once.
Run `eng/Invoke-RepositoryVerification.ps1` for complete acceptance; it has no dependency on
installed extensions or governance history. Analyzer errors,
architecture violations and failed relevant tests prevent completion. Normal code review assesses
semantic judgments and conditional choices that cannot be proven by static analysis.

No obligation-design/review, semantic-contract, verification-plan/results, architecture-proof
or API-proof attestation is mandatory. Historical evidence can be inspected through
`historical_phase_evidence.py`; it grants no new approval and is not a development prerequisite.
Keep scoped exceptions and their reasons in engineering policy/ADRs and normal review.
Never manufacture passing history or change old hashes to imply current execution.
