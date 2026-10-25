# Program Kit contributor instructions

## Local Firefox limitation

Firefox is not runnable on the current local Windows host. Playwright reaches
`browserType.launch: spawn UNKNOWN` when it tries to start the installed Firefox binary. Do not
retry Firefox repeatedly, diagnose that host error as a product regression, or change production
code to accommodate it. Where a validator exposes `--engines`, use the non-Firefox engines locally
(for example, `--engines=chromium,webkit`), continue the remaining deterministic validators, and
report the known local-host limitation. Retain Firefox in affected browser scenarios where browser coverage is required; the relevant
CI scenario remains the authority for Firefox acceptance. Do not restore an automatic full browser matrix.

## Development and release validation

Ordinary development runs `./scripts/Test-ProgramKit.ps1` (Integrity), then affected
contracts with `python scripts/run_validation.py --suite Affected --changed-from <base>`.
The single maintained definition is `tests/validation-inventory.json`; see
[validation](docs/validation.md) for capability edges, fixture scope and runtime budgets.
Unknown paths or history are explicit coverage gaps, never an instruction to run the
full inventory. Run independent supported checks; missing prerequisites, failed tests,
timeouts and overruns are not success. Every check owns only the prerequisites it uses.
Do not install device toolchains from an agent or substitute local runtime copies.

The six representative mechanical families establish an initial baseline with
`--suite Baseline`. They cover installation, phases, knowledge, founding intake, upgrade and
scaffolding, with explicit limits. Expensive native, database, browser and Host checks
need a concrete affected contract; broad scenario investigations require `--check` and
`--reason`. Do not rerun broad matrices simply because composition or a shared SDK changed.
Use representative mechanisms and expand coverage when an observed regression warrants it.
Local diagnostic records under ignored `artifacts/validation-runs/` bind actual working
contents, including uncommitted edits. They are neither attestations nor publication
authority. Report validation and gaps concisely in the PR; the maintainer accepts those
claims through native GitHub review/publication approval. No custom remote receipt handoff.

PRs and explicit exact-source candidates share package CI: fast integrity, one archive
build, clean Windows/Linux installation and installed entrypoint smoke, and applicable
security checks. Logs and package/source hash manifests stay in Actions artifacts. There
is no duplicate broad main-push or tagged acceptance suite. Publication uses the exact
inspected artifacts, with native `publication` environment approval before tag creation
or publication. Do not dispatch publication, create tags or publish without user authority.
See [releasing](docs/releasing.md). Sole-maintainer approval is supported explicitly.

Dependency discovery, pin upgrades, lock refresh and profile qualification are separate
[maintenance](docs/maintenance/dependency-review.md), not mandatory release preparation.
Retain qualified product profiles, versioned knowledge, native ownership baselines and
existing consumer locks. New external inputs belong in `maintenance-policy.json`.
Failed lookups, security findings or tests remain failures with actionable repairs.
Known applicable product defects block release; missing coverage/harness limitations
require a concrete maintainer disposition, never an implicit green result.

Deterministic validation never invokes a coding agent. Optional live trials remain
individually user-authorized; the release-readiness skill grants no paid-worker or
publication authority. No trial run means no AI acceptance claim. Installation, interactive
launcher startup and provider account/authority initialization remain human-terminal-owned.
The installed product-intake skill authors and reviews the baseline in the consumer conversation.
`Start-IntakeSession.ps1 -PrepareOnly` starts no coding agent or workflow. Release
trial preparation verifies candidate packages and actual local prerequisites in a
disposable consumer; it does not create additional release qualification.

## Consumer repair intake

For explicitly scoped incoming consumer repair observations, use the repository-only
`program-kit-repair-evaluator` skill and [maintenance intake procedure](docs/maintenance/repair-feedback.md).
The receiving owner explicitly registers an existing ledger, then uses bounded `inbox`
and exact `inspect` operations. Do not infer a destination from an active chat or edit
another maintenance campaign. Intake remains on demand; ordinary Spec Kit hooks and
deterministic validation do not start agents, poll chats or contact consumers.

## Repairing failed validation before retrying CI

Preserve the original failed run and inspect every independent failure. Reproduce each
supported failure through its focused entrypoint, fix the cause and run meaningful
affected regressions before retrying CI. Inspect the whole changed upstream contract;
do not discover adjacent broken arguments by repeatedly running broad suites.
Missing Linux, Docker, Firefox or toolchains remain explicit local limitations. Do not
install prohibited runtimes, weaken assertions, omit supported CI platforms or call a
different environment an exact reproduction. Add targeted diagnostics when needed.
Only a successful exact-source package run can supply publication bytes; targeted
local results do not substitute for that run.

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
Disclose simulated answers, preserve the proxy marker, and stop before confirmation or acceptance.
This supplies no paid-worker, live-acceptance, implementation, architecture or release authority.
The following live-acceptance requirements remain unchanged for actual automated workers.

The bootstrap workflow, proxy-bootstrap adapter and paid bootstrap/workflow phases are retired.
Use `speckit.program-kit-governance.product-intake` for the founding baseline, then
`speckit.program-kit-governance.specification-intake` for the selected feature. A simulated
rehearsal supplies no consumer acceptance, constitution ratification or executed compatibility
claim. Existing workflow runs, checkpoints and receipts remain read-only history; do not resume,
recreate or relabel them as a new successful workflow. No replacement paid founding trial is supplied.

Paid live acceptance is entirely user-invoked. Do not ask whether to run it during publication, and
do not report it as skipped when it was not requested. Successful exact-source package CI remains mandatory before publication.

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
- Run supported building-block, feature or upgrade phases only with the matching unexpired,
  unconsumed manifest. Each authorization must bind its exact supported parent checkpoint.
  Retirement does not authorize a fabricated parent or a substitute bootstrap run.
- Wait for completion, inspect the generated manifest and redacted streams, repair in-scope defects,
  and obtain a new one-use authorization before any rerun.
- Never add a paid phase to CI or an unattended hook. Never recreate a boolean `-Approved` path.
- `New-LiveBootstrapCheckpoint.ps1`, the bootstrap/workflow issuer and runner phases,
  `Test-LiveBootstrap.ps1` and the old Python entry point cannot start paid bootstrap execution.
  Historical evidence is read-only and must not be upconverted.

Independent user-authorized feature and upgrade trials preserve evidence under
`artifacts/live-acceptance/v2/`. Their process supervision, sandbox, credential isolation and
one-use authority rules remain in force. Do not copy harness environment sanitization into
consumer setup or guidance, and never launch an outer bootstrap workflow from an agent.

## Failed stable-release recovery

A pushed stable tag is a release candidate until the approved publication workflow succeeds. NuGet and
host-image publication must remain downstream reusable jobs of that workflow, after exact package verification and applicable public component gates. Never restore independent stable-tag triggers for
those irreversible publication workflows.

If the Release workflow fails for a stable tag:

1. Preserve and inspect the failed run evidence.
2. Repair the failure and obtain a successful exact-source package CI run for the corrected
   commit, then verify promotion without publication. Preserve failed-run evidence,
   confirm whether publication steps ran and inspect public assets/immutable registries.
   Never conceal partial publication, rewrite old evidence or reuse another source's
   package run. A different source requires its own package run.
3. Obtain or confirm the user's approval for the exact corrected commit and same stable tag.
4. Delete the failed tag locally and remotely, recreate it at the approved corrected commit, and push
   the corrected commit and recreated tag. Do not increment the stable version merely because the
   failed candidate tag existed.
5. Do not tell consumers that the version is available, or unblock dependent work, until the recreated
   tag's promotion and actual public installation/upgrade verification succeeds.

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
