# Program Kit contributor instructions

## Local Firefox limitation

Firefox is not runnable on the current local Windows host. Playwright reaches
`browserType.launch: spawn UNKNOWN` when it tries to start the installed Firefox binary. Do not
retry Firefox repeatedly, diagnose that host error as a product regression, or change production
code to accommodate it. Where a validator exposes `--engines`, use the non-Firefox engines locally
(for example, `--engines=chromium,webkit`), continue the remaining deterministic validators, and
report the known local-host limitation. Keep Firefox in the CI browser matrix; CI remains the
authority for Firefox acceptance.

## Development and release validation

Before selecting a release candidate, run the [dependency update workflow](docs/maintenance/dependency-review.md).
Upgrade active external pins and lockfiles, run the deterministic tests, and regenerate the
qualified default profile and versioned knowledge together. Add newly introduced dependencies
to `maintenance-policy.json`. Preserve historical profiles/evidence and existing consumer locks.
Keep update work out of ordinary Spec Kit hooks and implementation loops. Test, lookup and
security failures block the update and identify the repair; they are never treated as success.

Ordinary development uses targeted validators plus the bounded default
`./scripts/Test-ProgramKit.ps1` Development suite. Main pushes run Development plus
checks affected by the whole push range and prerequisite closure. Unknown selection
inputs select the full deterministic inventory. PR coverage remains enabled.

CI owns complete deterministic release qualification. Use the untagged
`qualify-candidate.yml` workflow with the exact expected main commit. It builds one
publication payload, runs complete Linux acceptance with Chromium/Firefox/WebKit,
focused Windows compatibility and security checks. Reuse a complete matching
successful qualification; partial CI runs cannot be merged into qualification.
No mandatory local Release suite repeats CI-capable checks. A candidate may need no
local acceptance execution. Retired local Release entry points provide migration
guidance and cannot mint new legacy receipts. Historical receipts remain read-only.

Tagged Release verifies exact source, trusted producer/job/coverage provenance and
all payload hashes, a reviewed readiness disposition and fresh security evidence.
It promotes the qualified CI artifacts without rebuilding or rerunning deterministic
acceptance. Missing/expired/incomplete/untrusted evidence blocks publication and
identifies the pre-tag CI recovery command. Security defaults to 24 hours; refresh
only the scan against the unchanged candidate with `refresh-candidate-security.yml`.
Artifact retention defaults to 14 days and is independent of scan freshness.
Policy and required variants are enforced in `release-policy.json` and
`scripts/release_candidate.py`; see [releasing](docs/releasing.md).

Deterministic validation never invokes a coding agent. Only an explicitly authorized
live-acceptance v2 phase starts automated coding-agent sessions. The repository-only
`.agents/skills/program-kit-release-readiness/SKILL.md` recommends optional trials
from actual changes; it grants no paid-worker or publication authority. Confirmed
product defects block readiness until repaired; harness failures/inconclusive trials
need explicit disposition. No trial run means no AI acceptance claim.

`Start-IntakeSession.ps1` is a separate human-owned interactive intake exercise.
Never launch its interactive mode from an agent, CI, a deterministic suite, or an unattended hook.
Its `-PrepareOnly` setup/evidence smoke test starts no coding agent and never launches bootstrap.

Release-oriented optional trials use `release_candidate.py prepare-trial` to verify
CI packages, check actual local prerequisites and install a disposable consumer.
The separate local preparation record binds the actual host/toolchains, original
CI qualification digest and exact packages. It is preparation, not local execution
of Linux qualification. Historical local-evidence reuse cannot authorize borrowing
qualification from another commit or rewriting a receipt.

## Consumer repair intake

For explicitly scoped incoming consumer repair observations, use the repository-only
`program-kit-repair-evaluator` skill and [maintenance intake procedure](docs/maintenance/repair-feedback.md).
The receiving owner explicitly registers an existing ledger, then uses bounded `inbox`
and exact `inspect` operations. Do not infer a destination from an active chat or edit
another maintenance campaign. Intake remains on demand; ordinary Spec Kit hooks and
deterministic validation do not start agents, poll chats or contact consumers.

## Optional live acceptance

The optional OCR-only provider operation path is separate from coding-worker
acceptance. Its account initialization and `provider_operation_authority.py`
interactive issuance are human-terminal-owned: never launch either from an agent,
CI or unattended hook. Deterministic validators may issue fictional recording-mode
manifests and run offline transports; those cannot authorize provider I/O. Preserve
original account authority, reservations and uncertain outcomes across sessions.

### Optional non-authorizing proxy intake

An explicit user request for a proxy intake/rehearsal authorizes the current session to simulate
fictional consumer answers and create draft artifacts in a disposable consumer. Use the shipped
`speckit.program-kit-governance.proxy-intake` command. This is a separate optional tool: default to
one question round for a quick scan, or perform full draft intake when requested. Setup uses
`Start-IntakeSession.ps1 -PrepareOnly`; never launch its interactive mode for the proxy.
Disclose simulated answers, preserve the proxy marker, and stop before confirmation/bootstrap.
This supplies no paid-worker, live-acceptance, implementation, architecture or release authority.
The following live-acceptance requirements remain unchanged for actual automated workers.

An explicit later request can extend the same-session rehearsal through bootstrap using
`speckit.program-kit-governance.proxy-bootstrap`. Its dedicated adapter pauses native command steps
for the current session, labels review decisions simulated, retains the draft intake and runs real
validators. This is a separate exception for an adapter that cannot dispatch a coding agent; never
use ordinary outer Codex bootstrap for a proxy or promote its results to consumer authority.
Stop before feature implementation. The paid-worker manifest rules still apply to actual workers.

Paid live acceptance is entirely user-invoked. Do not ask whether to run it during publication, and
do not report it as skipped when it was not requested. Complete deterministic CI qualification remains mandatory before publication.

When the user requests paid learning trials before release preparation, use an explicitly selected
development-trial receipt from `tests/live/v2/trial_candidate.py`. It binds clean source, platform,
toolchains, locally built and installation-tested archives, and the actual preparation logs. It
does not require the complete Release suite or claim public-package/browser/Release acceptance.
Select it with `New-LiveAcceptanceAuthorization.ps1 -TrialReceipt`; the exact one-use phase,
checkpoint, model, worker sandbox and human confirmation rules below still apply. Development-trial
evidence can inform fixes but never satisfies or substitutes for the publication Release gate.

- A user request authorizes only issuance of the exact phase-specific manifest they confirm through
  `New-LiveAcceptanceAuthorization.ps1`; it is not a reusable preference or authorization for a
  different phase.
- Run `New-LiveBootstrapCheckpoint.ps1` or `Test-LiveBuildingBlockConsumer.ps1` only with the matching
  unexpired, unconsumed manifest. Building-block authorization must bind the exact parent checkpoint.
- Wait for completion, inspect the generated manifest and redacted streams, repair in-scope defects,
  and obtain a new one-use authorization before any rerun.
- Never add a paid phase to CI or an unattended hook. Never recreate a boolean `-Approved` path.
- `Test-LiveBootstrap.ps1` and the old Python entry point are retired; historical v1 evidence is
  read-only and must not be upconverted.

The live harness is the sole exception to the normal rule against agent-started outer Codex
bootstrap orchestration. It may exercise that exception only for its generated disposable test
repository and preserves evidence under `artifacts/live-acceptance/v2/`. Do not copy its environment
sanitization into consumer setup, bootstrap guidance, or another script.

## Failed stable-release recovery

A pushed stable tag is a release candidate until the complete Release workflow succeeds. NuGet and
host-image publication must remain downstream reusable jobs of that workflow, after all deterministic
validation and public component-release gates. Never restore independent stable-tag triggers for
those irreversible publication workflows.

If the Release workflow fails for a stable tag:

1. Preserve and inspect the failed run evidence.
2. Repair the failure and obtain valid complete CI qualification for the exact corrected
   commit, then verify promotion without publication. Preserve failed-run evidence,
   confirm whether publication steps ran and inspect public assets/immutable registries.
   Never conceal partial publication, rewrite old evidence or reuse another source's
   qualification. A different candidate requires its own complete qualification.
3. Obtain or confirm the user's approval for the exact corrected commit and same stable tag.
4. Delete the failed tag locally and remotely, recreate it at the approved corrected commit, and push
   the corrected commit and recreated tag. Do not increment the stable version merely because the
   failed candidate tag existed.
5. Do not tell consumers that the version is available, or unblock dependent work, until the recreated
   tag's promotion and public installation/upgrade workflow succeeds.

Before repointing, verify whether any immutable registry artifact escaped the gate. Disclose any
partial publication explicitly; a tag correction must never conceal that an artifact was produced
from a different source state.

## Windows live-worker execution

The live harness launches disposable Codex workers with `--sandbox workspace-write`. On Windows,
the worker sandbox can use a different SID from the process that created the disposable Git
repository. A workflow-process `GIT_CONFIG_*` safe-directory injection is only a best-effort aid:
the sandbox may filter it before the worker starts.

The harness therefore writes an `AGENTS.md` inside the disposable consumer. Workers must run every
Git operation as `git -c safe.directory=<absolute-disposable-project> -c core.excludesFile=
<command>` on Windows, or use `/dev/null` as the excludes value on POSIX. Windows Git rejects `NUL`
as an excludes file. The second override prevents a harmless warning
when the sandbox cannot read the user's global Git ignore file. Never use `git config --global`,
never persist a safe-directory exception, and never disable or bypass the sandbox. Keep Python
output UTF-8 (`PYTHONUTF8=1`); the harness and workflow establish this for their owned process trees.

Start each Windows worker suspended, assign it to the harness Job Object, and resume it only after
assignment. Determine liveness from process handles and Job accounting. Never use `os.kill(pid, 0)`,
`CTRL_C_EVENT`, or another signalling probe: a previous POSIX-style liveness check could close the
Windows terminal host. Record cancellation only from observed operator interruption; exit code 130
without that provenance is inconclusive. Terminate descendants, drain both streams, and record both
outcomes before sealing evidence.

The full worker output is redacted evidence, not console progress. Preserve both streams and their
raw-stream hashes, redaction counts, cleanup, and drain results. Registry credentials belong only to
the supervisor's exact availability/restore child processes and must never enter a worker environment
or evidence payload.

When the harness itself is started from a sandboxed Codex Desktop task, the outer task sandbox may
hide the user-owned Codex home and produce `Error finding codex home: Could not find home directory`
before an agent session starts. Retry the explicitly approved harness with external-process access
to the installed Codex CLI. This only relaxes the outer harness launch; it must not remove the
inner disposable workers' `workspace-write` sandbox or broaden their filesystem permissions.
