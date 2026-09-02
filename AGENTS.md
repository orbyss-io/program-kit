# Program Kit contributor instructions

## Publishing

Before creating or pushing a release tag, publishing release assets, or otherwise making a Program
Kit version public, ask the user this explicit question and wait for the answer:

> Do you want me to run the paid live bootstrap acceptance suite before publishing this version?

Do not infer approval from a request to publish, from earlier test approval, or from a previously
successful run.

- If the user gives an explicit yes, run `./scripts/Test-LiveBootstrap.ps1 -Integration codex -Approved`
  (or the explicitly requested installed integration), wait for completion, inspect the generated
  report and output streams, and block publication if it fails.
- If the user answers no, state clearly in the release handoff that the live suite was explicitly
  skipped. The deterministic local and CI-compatible tests remain mandatory.
- Never add the paid live suite to CI or run it from an unattended hook.
- Never pass `-Approved` unless the current publishing conversation contains the user's explicit
  approval.

The live harness is the sole exception to the normal rule against agent-started outer Codex
bootstrap orchestration. It may exercise that exception only for its generated disposable test
repository and preserves evidence under `artifacts/live-acceptance/`. Do not copy its environment
sanitization into consumer setup, bootstrap guidance, or another script.

## Windows live-worker execution

The live harness launches disposable Codex workers with `--sandbox workspace-write`. On Windows,
the worker sandbox can use a different SID from the process that created the disposable Git
repository. A workflow-process `GIT_CONFIG_*` safe-directory injection is only a best-effort aid:
the sandbox may filter it before the worker starts.

The harness therefore writes an `AGENTS.md` inside the disposable consumer. Workers must run every
Git operation as `git -c safe.directory=<absolute-disposable-project> -c
core.excludesFile=<platform-null-device> <command>`. The second override prevents a harmless warning
when the sandbox cannot read the user's global Git ignore file. Never use `git config --global`,
never persist a safe-directory exception, and never disable or bypass the sandbox. Keep Python
output UTF-8 (`PYTHONUTF8=1`); the harness and workflow establish this for their owned process trees.

The full worker output is evidence, not console progress. Preserve it in `workflow.stderr.log` and
show concise workflow step transitions in the terminal. Treat token, stream-size, duration, and
stage-brief budgets as advisory performance signals; functional completion and governance
validation remain the pass/fail contract.

When the harness itself is started from a sandboxed Codex Desktop task, the outer task sandbox may
hide the user-owned Codex home and produce `Error finding codex home: Could not find home directory`
before an agent session starts. Retry the explicitly approved harness with external-process access
to the installed Codex CLI. This only relaxes the outer harness launch; it must not remove the
inner disposable workers' `workspace-write` sandbox or broaden their filesystem permissions.
