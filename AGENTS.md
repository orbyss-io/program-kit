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

Ordinary development uses targeted validators plus the bounded default
`./scripts/Test-ProgramKit.ps1` Development suite. Do not run the complete deterministic suite after
each change and do not imply that it was skipped; it is a publication gate, not an edit-loop gate.

Run `./scripts/Test-ProgramKit.ps1 -Suite Release -Approved -BrowserEngines
'chromium,webkit'` only after the user explicitly decides the candidate should proceed toward
publication. On this Windows host, do not start the complete Release suite from a Codex Desktop task;
give the command to the user, let it finish in their user-owned terminal, then inspect the preserved
`artifacts/release-validation-<version>.log` and generated artifacts. CI remains authoritative for
the Firefox leg.

The deterministic Development and Release suites do not invoke a coding agent. Tests whose names
contain `codex` validate integration files, preflight behavior, and guarded harness contracts. Only
an explicitly authorized live-acceptance v2 phase starts automated coding-agent sessions, and it remains
governed by the separate optional-live-acceptance rules below.

`Start-IntakeSession.ps1` is a separate human-owned interactive intake exercise, not an automated
acceptance phase. The user runs it in a normal foreground terminal and answers the installed skill.
Never launch its interactive mode from an agent, CI, a deterministic suite, or an unattended hook.
Its `-PrepareOnly` setup/evidence smoke test starts no coding agent. It never launches bootstrap.

## Optional live acceptance

Paid live acceptance is entirely user-invoked. Do not ask whether to run it during publication, and
do not report it as skipped when it was not requested. Deterministic local and CI-compatible Release
tests remain mandatory.

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
2. Repair the failure and complete the deterministic local release validation.
3. Obtain or confirm the user's approval for the exact corrected commit and same stable tag.
4. Delete the failed tag locally and remotely, recreate it at the approved corrected commit, and push
   the corrected commit and recreated tag. Do not increment the stable version merely because the
   failed candidate tag existed.
5. Do not tell consumers that the version is available, or unblock dependent work, until the recreated
   tag's complete Release workflow succeeds.

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
