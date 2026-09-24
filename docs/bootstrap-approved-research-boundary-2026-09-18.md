# Failed trial 23d94645: approved research edited during closure

Candidate: `4db0e139c78b5af516acd6ec481607f36e4da6cb`, clean source.
Evidence: `artifacts/intake-sessions/53b390f59d574087b5c4c665e9003ab5`.
Consumer: `C:/Users/Joeyb/AppData/Local/Temp/program-kit-intake-cezgungs`.
The original consumer and its approvals remain unchanged by this investigation.

## Observed failure

Native step `validate-bootstrap` failed at 2026-09-18 06:44:51 UTC with
`Bootstrap assessment artifacts changed after human approval`. Of the seven
assessment-bound artifacts, only `docs/architecture/tooling-evaluation.md` differs.
The approved hash is `bd2e1e1a4ba8062af42ae8fbab642fc4824d000fed42fd5b0531b86733a7a728`;
the current hash is `798488f4b785da0a845003645e3f1686b4a0855f61ff9a29b70f754da77c7c21`.

Closure session `01a0b339-9256-7771-ba90-e428765bfaef` issued a write at
06:40:01 UTC that replaced a research sentence requiring actual consumer cases
before closure acceptance with a link to `fd-compatibility-scope.md`, explaining
the split between mechanism proofs and consumer planning/delivery assertions.
That split was appropriate to record in the follow-on ADR; rewriting the approved
research was not. The approval receipt was not renewed by the user.

`validate-closure-output` and compatibility execution both completed after that
edit. The defect was therefore caught too late, after more work had been spent.
This was not an unknown consumer technology or a failure to select a default.

## Contract gap

Closure explicitly preserved the approved register and Accepted ADRs, but did not
make the full assessment-approved file set equally visible. Its broad instruction
to reconcile historical status prose could be read as authorizing edits to research.
The output contract listed primary outputs but did not expose the complete immutable
approval boundary. Stage validation checked output and proof-plan correctness without
checking that the approved assessment inputs were still intact.

Previous deterministic tests covered completion hashing and valid happy paths, but
not a closure author changing approved research while producing otherwise valid
artifacts. The successful prior human run did not exercise that mutation. The
efficiency changes did not cause a hash algorithm regression; they also did not
repair this existing contract gap. Their status-prose guidance remained too broad.

## Repair

- Later producer briefs now project exact approved artifact paths/hashes and the
  approval receipt as read-only inputs. Context creation rejects already changed
  authority before dispatching another producer.
- Their terminal validation checks the captured boundary before output validation,
  synchronization or downstream proof execution. The diagnostic names every changed
  path and directs clarification into a follow-on ADR/ledger. Editing the approval
  receipt to match changed bytes cannot bypass the captured boundary.
- Closure and the existing lifecycle reference explicitly preserve approved research,
  including its historical phase proposals. A successor cites the original without
  adding backlinks or rewriting its text. Substantive baseline replacement retains
  the owning assessment review rather than silently renewing approval.
- Deterministic readiness checks the boundary without duplicating producer guidance
  in its already bounded context.

This does not weaken approval validation, automatically restore consumer files,
invent a user decision or require a new approval for an unchanged original baseline.
The intended agent response to its accidental edit is to preserve the approved
original and keep the clarification in the permitted successor artifacts.

## Verification

The new regression reproduces an approved research edit, verifies rejection before
downstream stage validation, allows a separate successor with unchanged source, and
rejects a rewritten approval receipt. Read-only replay passes for successful trial
c0a74a71 and identifies the exact research file in failed trial 23d94645.

The context and profile fixtures were updated to reflect the early check: a synthetic
profile-selection test now creates its fixture approval after choosing research pins,
and the roadmap check list includes approval preservation before synchronization.
No gate was removed. Logs are retained as `artifacts/approval-boundary-*`.
The nine handoff-quality tests and context regressions passed. The complete bounded
Development suite also passed with exit 0, including profiles, lifecycle, readiness,
compatibility and resumption; see `artifacts/approval-boundary-development.log`.

The efficiency changes are visible in this failed trial: all six later producer
sessions used paged brief reading and none reread the bootstrap intake skill. That
is observed behavior, not evidence of successful bootstrap or overall token savings.
