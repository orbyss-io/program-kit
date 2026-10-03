# Python diagnostic and Windows intake output repair

**Revised release scope, 2026-10-03:** the user chose to defer the core `python3`
and structured-worker proposal after successful local consumer recovery, and
rejected a bundled or modified Spec Kit build. Program Kit 0.12.4 retains public
Spec Kit and its generated instructions. The independent Windows ACL fix and
native runtime/semantic validators remain in the candidate. No upstream release
or private core contract is required. The original source proposal remains
historical evidence and is excluded from release acceptance.

Consumer report: InsurancePolicyEvaluator, Program Kit Governance 0.12.1,
run `26232ea0`. `python` selected Python 3.13.7/PyYAML 6.0.3, while `python3`
selected Python 3.14.5 without PyYAML. Core Spec Kit 1.0.1 generated the constitution
resolver invocation using the latter. Program Kit probed a different interpreter,
and Spec Kit equated Codex exit zero with command completion. The unchanged
constitution was correctly rejected by the subsequent artifact validator.

Program Kit now resolves and validates its native interpreter before dispatch,
checks Python >=3.11 and PyYAML, scopes the same executable to native workflow
steps, and probes the resolver script on every platform. This does not verify or
rewrite the core-generated `python3` invocation. Its initializers resolve the native
interpreter once; the stock core retains its generation behavior. The CLI supervisor can
still use its isolated Specify environment; schema caches for supervisor and
product Python remain version-specific. No interpreter is removed or modified.

The [deferred core source proposal](../patches/README.md) describes generation and
structured-worker changes; those are not installed or claimed as fixed in this
release. Public core can still mark an exit-zero command completed. Program Kit's
following native artifact and semantic validators remain authoritative, including
the Draft constitution validator that rejects unchanged scaffolding. Existing run
results and artifact hashes remain evidence; no state is rewritten to correct a
historical command-step status.

The intake authoring defect came from moving validated files out of a private
temporary staging directory. On Windows, those files can retain the staging DACL,
including Python 3.13's protected owner-only temporary-directory permissions.
Publication now creates ordinary siblings in the destination directory. New files
inherit destination permissions; existing files use Windows ReplaceFile to retain
their DACL. Only the three canonical authoring outputs receive an explicit
read/write grant to the workspace-root owner's SID, so a different sandbox owner
does not make them unreadable. No directory ACL, unrelated file, broad group or
execution policy is changed. Rollback preserves bytes and permissions; confirmed
intake still cannot be replaced by draft authoring.

## Consumer recovery

At the original report, local Draft validation and review-packet generation had
passed. The later 2026-10-03 report supersedes that status: this consumer's bootstrap
is completed and its constitution is Ratified. Follow the
[upgrade-only recovery](initialized-upgrade-recovery-2026-10-03.md); preserve the
Ratified document and completed run. Do not resume bootstrap for this consumer.
Human constitution review and ratification remain separate decisions.

The steps below apply to an unfinished run. This consumer now uses the linked
upgrade-only recovery instead. After Program Kit 0.12.4 is actually published,
from a normal user-owned terminal:

1. Preserve uncommitted work, confirmed intake, `.specify/workflows/runs/26232ea0`,
   approval/review evidence and their recorded hashes. Inspect the existing run's
   status without editing its state JSON.
2. Update Program Kit through its documented updater with the existing supported
   public Spec Kit installation. Do not hand-patch the skill,
   constitution, confirmed intake, approval ledgers or saved workflow state.
3. For a native-runtime problem, verify the selected executable and resolver:

   ```powershell
   $programKitPython = (python -c 'import sys; print(sys.executable)').Trim()
   & $programKitPython -c 'import sys,yaml; assert sys.version_info >= (3,11); print(sys.executable, yaml.__version__)'
   & $programKitPython .specify/scripts/python/resolve_template.py constitution-template --json
   & $programKitPython .specify/extensions/program-kit-governance/scripts/governance_state.py validate-constitution-draft
   ```

   If PyYAML is missing, install `"PyYAML>=6,<7"` with
   `& $programKitPython -m pip install --disable-pip-version-check "PyYAML>=6,<7"`.
   Do not install into an unrelated interpreter or uninstall another Python.
4. For an unfinished run only, resume when the operator intends to continue through the supported
   lifecycle entry point:

   ```powershell
   & $programKitPython .specify/extensions/program-kit-governance/scripts/workflow_lifecycle.py resume --run-id 26232ea0
   ```

   This is human-owned outer orchestration. Review the retained Draft packet at
   the human gate; no automatic approval input is needed. Do not start a replacement
   run merely to conceal the failed step or manually mark it completed.

For existing unreadable intake/map/DSL files, an owner or administrator should
inspect only those exact paths and restore the workspace owner's intended access,
preserving all other ACEs and recorded content hashes. The new builder prevents
staging ACL transfer; an update alone does not repair old files. Do not rerun draft
authoring against confirmed intake and do not recursively reset repository ACLs.

## Validation and release dependency

Current deterministic regressions exercise the unmodified public package and its
unchanged generated skill, Program Kit native selection with different/absent
`python3`, missing native dependencies, supported-version failures, exit-zero
workers without artifacts, Windows ACLs and rollback. Native validators reject
missing output. The separate deferred proposal tests do not supply release
acceptance. No coding-agent session is started.

Earlier Development and upstream-proposal logs are historical. The revised
candidate requires fresh targeted/Development checks with public Spec Kit, then
the final publication Release gate. Proposal fixtures are not a released package.

This isolated branch began at prepared 0.12.2 source, merged published 0.12.3 main,
and now prepares the combined 0.12.4 candidate without changing the main checkout. The
core-dependent proposal is deferred. CI retains public Spec Kit 1.0.1 and no
patched runtime is built or installed. Reconcile the revised scope with the
current release baseline before publication.
These are shipping changes, so
earlier local Release receipts cannot be reused. After the user chooses publication,
run the complete local gate in their own terminal from the final clean checkout:

```powershell
.\scripts\Test-ProgramKit.ps1 -Suite Release -Approved -BrowserEngines 'chromium,webkit'
```

Preserve and inspect its log/artifacts; keep Firefox in CI. Publish only after the
complete Release workflow succeeds. No consumer state, approval, ratification,
tag, registry artifact or release receipt is rewritten by this repair.
