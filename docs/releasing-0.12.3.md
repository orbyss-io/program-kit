# Preparing Program Kit 0.12.3

This patch fixes completed-bootstrap continuation after a legitimate constitution
amendment and regenerated readiness report. Current ratified authority is validated
separately from exact historical completion bindings; original approval/completion
evidence, native proof admission, fresh human review and engine completion remain
required. See [the correction evidence](post-bootstrap-authority-evolution-repair-2026-10-02.md).

All Program Kit installable components advance from 0.12.2 to 0.12.3 together.
Foundation, Forms, Localization, Spec Kit and managed toolchain pins are unchanged.
Version 0.12.2 is already published; preserve its tag and release assets.

## Local publication gate

The final candidate must remain committed and clean throughout validation. These
are shipped changes and require fresh local Release evidence. Follow
[AGENTS.md](../AGENTS.md): run the complete Windows Release suite in a normal
user-owned terminal. The cached toolchain helper verifies Node 24.20.0, npm 11.19.0
and .NET SDK 10.0.202, bounds PATH, and supplies the package token only to the
validation process tree. It restores the caller's environment afterward.

```powershell
Set-Location C:\Users\tech_\Code\program-kit
.\scripts\Invoke-LocalRelease.ps1
```

The helper invokes the required command:

```powershell
.\scripts\Test-ProgramKit.ps1 -Suite Release -Approved -BrowserEngines 'chromium,webkit'
```

Inspect `artifacts/release-validation-0.12.3.log`, the per-check journal,
`artifacts/release-receipt-0.12.3.json`, the archives and `SHA256SUMS`. Verify the
receipt source and artifact hashes before publication. Firefox remains required in
CI, despite the documented local Windows launch limitation.

Merge the reviewed patch after local evidence and candidate CI pass. Push the new
`v0.12.3` tag matching VERSION to invoke the complete tagged Release workflow.
Declare the version available only after that workflow and its public install and
upgrade checks finish successfully. Do not create release assets manually to bypass
the tagged workflow, or move the published 0.12.2 tag.

## Reusing evidence after non-shipping corrections

Follow [Reusing local Release evidence after non-shipping changes](../AGENTS.md#reusing-local-release-evidence-after-non-shipping-changes).
Verify the complete diff against actual packaging inputs, receipt/log validity and
artifact hashes; record both commits, supplementary checks and green CI.
Preserve the original receipt unchanged.
The tagged Release workflow still runs in full and produces its own exact-commit evidence.
Failed-tag reuse additionally requires demonstrating a test/assertion or CI-only defect and that
nothing was published from the failed candidate. Exact corrected-commit and same-tag approval is still required.
If any reuse condition is unproven, obtain fresh local Release evidence.
