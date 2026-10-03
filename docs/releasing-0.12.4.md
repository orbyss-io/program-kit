# Preparing Program Kit 0.12.4

This candidate combines interpreter/worker artifact consistency, Windows staged-output
permissions, initialized-consumer offline upgrade recovery and Windows workflow
shell preflight and corrective-producer sizing before proofs, on top of published
0.12.3. See [Python source coordination](../patches/README.md) and
[upgrade recovery](initialized-upgrade-recovery-2026-10-03.md), plus
[shell-preflight evidence and recovery](windows-workflow-shell-preflight-2026-10-03.md).
The final [producer-sizing correction](recovery-producer-sizing-2026-10-03.md)
preserves the existing limits, proof evidence and separate human review gates.

All installable Program Kit components advance together. Foundation, Forms,
Localization and managed toolchain pins remain unchanged. Published 0.12.3 tags,
archives and evidence must remain unchanged.

## Coordinated core prerequisite

The maintained core source patch is tested against Spec Kit 1.0.1. It is not a
released dependency. Current pins still select unpatched 1.0.1; worker dispatch
deliberately rejects its incompatible structured-result contract. Land/distribute
the core correction, select its actual released version and update all installation,
build, CI and test pins before publication. Do not publish this candidate while
that prerequisite remains unresolved or invent a public version for it.

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
