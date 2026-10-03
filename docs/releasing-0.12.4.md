# Preparing Program Kit 0.12.4

This candidate combines Program Kit native-runtime validation, Windows staged-output
permissions, initialized-consumer offline upgrade recovery and Windows workflow
shell preflight and corrective-producer sizing before proofs, on top of published
0.12.3. See [the deferred core proposal](../patches/README.md) and
[upgrade recovery](initialized-upgrade-recovery-2026-10-03.md), plus
[shell-preflight evidence and recovery](windows-workflow-shell-preflight-2026-10-03.md).
The final [producer-sizing correction](recovery-producer-sizing-2026-10-03.md)
preserves the existing limits, proof evidence and separate human review gates.

All installable Program Kit components advance together. Foundation, Forms,
Localization and managed toolchain pins remain unchanged. Published 0.12.3 tags,
archives and evidence must remain unchanged.

## Public Spec Kit compatibility and deferred scope

The user chose on 2026-10-03 to defer the core-dependent Python-command and
structured-worker changes and explicitly rejected a bundled/modified Spec Kit
build. The candidate uses public Spec Kit 1.0.1, with unchanged CI dependency pins.
There is no upstream-release prerequisite, runtime fork, source-patching installer
or generated-consumer repair in this release. The source proposal is retained for
history, excluded from installation and publication acceptance.

Program Kit selects and validates its own native Python interpreter. The installed
core constitution skill retains its upstream invocation, which may use `python3`;
that mismatch is not claimed as fixed. Public core command completion can still
reflect worker process success. Required output and semantics are enforced by
the independent native validators before review, ratification or completion.
Optional command artifact declarations remain in the workflow for compatible
cores, but public 1.0.1 acceptance relies on the native steps, not those fields.
The revised tests exercise the actual unmodified public package and an exit-zero
worker producing no artifact; the native output gate must fail.

The user has authorized publication. Fresh deterministic validation gates remain
required. No stable tag or release was created during the readiness check;
published 0.12.3 remains unchanged.

The revised working candidate passed all 61 bounded Development checks on Windows
on 2026-10-03. Evidence is preserved in
`artifacts/validation-runs/20261003T080233Z-11999036/journal.json`; every recorded
exit code is zero and all 61 log hashes were verified. This includes eight public
core compatibility tests against installed, unmodified Spec Kit 1.0.1. The journal
records the prior HEAD plus the revised working files; it is Development evidence,
not an exact-commit Release receipt. Cached release toolchain preparation also
passed: Node 24.20.0, npm 11.19.0 and .NET SDK 10.0.202.

## Local publication gate

The final combined candidate must remain committed and clean throughout validation.
These shipped changes require fresh local Release evidence. Follow
[AGENTS.md](../AGENTS.md): the complete Windows Release suite runs in a normal
user-owned terminal after the candidate is ready for publication.

```powershell
Set-Location C:\Users\tech_\.codex\worktrees\python-runtime-consistency\program-kit
.\scripts\Invoke-LocalRelease.ps1
```

The helper invokes:

```powershell
.\scripts\Test-ProgramKit.ps1 -Suite Release -Approved -BrowserEngines 'chromium,webkit'
```

Inspect `artifacts/release-validation-0.12.4.log`, per-check journals,
`artifacts/release-receipt-0.12.4.json`, archives and `SHA256SUMS`. Verify source
identity and hashes. Firefox stays in the CI matrix; the known local Windows
launch limitation does not change product acceptance.

Merge the reviewed candidate only after fresh local evidence and green candidate
CI. Confirm the exact corrected commit for `v0.12.4`, then push that stable tag to
invoke the complete tagged Release workflow. Declare availability only after all
deterministic, public install/upgrade and downstream publication gates succeed.
No manual release assets, consumer state edits or automatic approvals substitute.

## Reusing evidence after non-shipping corrections

Follow [Reusing local Release evidence after non-shipping changes](../AGENTS.md#reusing-local-release-evidence-after-non-shipping-changes).
Verify the complete diff against packaging inputs, receipt/log validity and hashes;
record both commits, supplementary checks and green CI.
Preserve the original receipt unchanged.
The tagged Release workflow still runs in full with exact-commit evidence.
Failed-tag reuse also requires a demonstrated test/assertion or CI-only defect and
proof nothing was published from the failed candidate.
Exact corrected-commit and same-tag approval is still required.
If any reuse condition is unproven, obtain fresh local Release evidence.
