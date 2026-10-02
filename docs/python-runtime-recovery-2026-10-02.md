# Python interpreter and Windows intake output repair

Consumer report: InsurancePolicyEvaluator, Program Kit Governance 0.12.1,
run `26232ea0`. `python` selected Python 3.13.7/PyYAML 6.0.3, while `python3`
selected Python 3.14.5 without PyYAML. Core Spec Kit 1.0.1 generated the constitution
resolver invocation using the latter. Program Kit probed a different interpreter,
and Spec Kit equated Codex exit zero with command completion. The unchanged
constitution was correctly rejected by the subsequent artifact validator.

Program Kit now resolves and validates the product interpreter before dispatch,
checks Python >=3.11 and PyYAML, scopes the same executable to native workflow
steps, and runs the actual constitution resolver on every platform. Its initializers
resolve once and pass that executable into core generation. The CLI supervisor can
still use its isolated Specify environment; schema caches for supervisor and
product Python remain version-specific. No interpreter is removed or modified.

The [coordinated core source patch](../patches/README.md) fixes source ownership:
core generation and hooks bind the recorded executable, the constitution template
requires a blocked/failure report when resolution fails, and worker dispatch
preserves a structured outcome plus both streams. Bootstrap producers have
artifact checks before command-step completion. The constitution check invokes
the existing authoritative Draft validator; unchanged scaffolding remains invalid.
Original process results, diagnostics and successful artifact hashes remain evidence.

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

The reported local constitution recovery is already complete: Draft validation
and review-packet generation passed. Leave that Draft and run history untouched.
Do not regenerate or ratify the recovered document just to test this source fix.
Human constitution review and ratification remain separate decisions.

After the coordinated core and Program Kit updates are actually available, from
a normal user-owned terminal:

1. Preserve uncommitted work, confirmed intake, `.specify/workflows/runs/26232ea0`,
   approval/review evidence and their recorded hashes. Inspect the existing run's
   status without editing its state JSON.
2. Install the released core fix and update Program Kit through its documented
   updater. Regenerate integration instructions through core installation/init
   with `--script py`; review the generated-file diff. Do not hand-patch the skill,
   constitution, confirmed intake, approval ledgers or saved workflow state.
3. Verify the recorded executable and its real resolver:

   ```powershell
   $programKitPython = (Get-Content -Raw .specify/python-runtime.json | ConvertFrom-Json).executable
   & $programKitPython -c 'import sys,yaml; assert sys.version_info >= (3,11); print(sys.executable, yaml.__version__)'
   & $programKitPython .specify/scripts/python/resolve_template.py constitution-template --json
   & $programKitPython .specify/extensions/program-kit-governance/scripts/governance_state.py validate-constitution-draft
   ```

   If PyYAML is missing, install `"PyYAML>=6,<7"` with
   `& $programKitPython -m pip install --disable-pip-version-check "PyYAML>=6,<7"`.
   Do not install into an unrelated interpreter or uninstall another Python.
4. Resume only when the operator intends to continue, through the supported
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

Deterministic regressions cover different/absent `python3`, real missing-PyYAML
environments, supported-version failures, generated consumers, actual resolver
execution, exit-zero blocked workers, absent/invalid artifacts, original diagnostics,
hash retention, Windows ACLs and rollback. No coding-agent session is started.

The bounded Development suite passed. Targeted upstream template/integration
checks passed, and a native Python/PowerShell/Git Bash composition fixture passed.
The upstream parity collection's Bash availability probe skips tests on this host;
the native fixture explicitly selects Git Bash. This does not claim the complete
upstream suite or public package acceptance.

This isolated branch began at prepared 0.12.2 source; it does not select a new
publication version or alter the separately advancing release checkout. The
coordinated core patch is not an upstream release, and this branch's existing CI
pins still name unpatched 1.0.1. Reconcile the changes with the current release
baseline, resolve the core dependency, and update its actual pins before publication.
These are shipping changes, so
earlier local Release receipts cannot be reused. After the user chooses publication,
run the complete local gate in their own terminal from the final clean checkout:

```powershell
.\scripts\Test-ProgramKit.ps1 -Suite Release -Approved -BrowserEngines 'chromium,webkit'
```

Preserve and inspect its log/artifacts; keep Firefox in CI. Publish only after the
complete Release workflow succeeds. No consumer state, approval, ratification,
tag, registry artifact or release receipt is rewritten by this repair.
