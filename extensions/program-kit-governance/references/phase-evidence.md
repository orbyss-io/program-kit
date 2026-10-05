# Knowledge and engineering checks

`phase_obligations.py project` prints applicable guidance before planning, tasks and implementation.
The single upstream registry is `phase-obligations.json`. Generated context is disposable.

Keep design choices and required tests in normal plan.md/tasks.md. Implement behavior and
architecture tests in the repository. Run `eng/Invoke-RepositoryVerification.ps1` for ordinary
acceptance; it has no dependency on installed extensions or governance history. Analyzer errors,
architecture violations and failed relevant tests prevent completion. Normal code review assesses
semantic judgments and conditional choices that cannot be proven by static analysis.

No obligation-design/review, semantic-contract, verification-plan/results, architecture-proof
or API-proof attestation is mandatory. Historical evidence can be inspected through
`historical_phase_evidence.py`; it grants no new approval and is not a development prerequisite.
Keep scoped exceptions and their reasons in engineering policy/ADRs and normal review.
Never manufacture passing history or change old hashes to imply current execution.
