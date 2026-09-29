# Preparing Program Kit 0.12.2

This patch candidate fixes governance installation validation when the Python interpreter
running `governance_state.py` has no PyYAML. The supplied configuration starts with
`schema_version: "1.0"`; the dependency-free mapping parser now accepts that scalar.
It continues to reject malformed configuration structure. Consumers do not need to
edit the supplied file or install PyYAML for governance validation.

All Program Kit installable components advance together from published v0.12.1 to
0.12.2. Foundation, Forms, Localization and managed toolchain pins are unchanged.
The initial regression test invokes `validate-installation` using an isolated Python
interpreter without site packages against the actual shipped template, then checks
malformed installed and local configurations.

## Validation and publication handoff

Run targeted checks and the bounded Development suite during preparation. The local
Spec Kit tool was updated to the required 1.0.1 with the user's authorization;
CI and Release pin the same version.

The complete deterministic Release suite must run after the candidate is committed
and the tree is clean, from a normal user-owned PowerShell terminal. On this Windows
host, use Chromium and WebKit locally; CI owns Firefox acceptance:

```powershell
Set-Location 'C:\Users\tech_\Code\program-kit'
.\scripts\Test-ProgramKit.ps1 -Suite Release -Approved -BrowserEngines 'chromium,webkit'
```

Inspect `artifacts/release-validation-0.12.2.log`, the per-check journal, the
generated archives, `SHA256SUMS` and `artifacts/release-receipt-0.12.2.json` before
tagging. The v0.12.1 receipt cannot validate this changed shipped script. The tagged
Release workflow must pass completely before declaring 0.12.2 available to consumers.

For later non-shipping corrections, follow
[Reusing local Release evidence after non-shipping changes](../AGENTS.md#reusing-local-release-evidence-after-non-shipping-changes).
Verify the complete diff against actual packaging inputs, receipt/log validity and
artifact hashes; record both commits, supplementary checks and green CI. Preserve the original receipt unchanged.
The tagged Release workflow still runs in full and produces its own exact-commit evidence.
Failed-tag reuse additionally requires demonstrating a test/assertion or CI-only defect and that
nothing was published from the failed candidate. Exact corrected-commit and same-tag approval is still required.
If any reuse condition is unproven, obtain fresh local Release evidence.
