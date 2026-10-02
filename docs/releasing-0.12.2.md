# Preparing Program Kit 0.12.2

This patch candidate establishes explicit `workspace-write` access for Codex bootstrap
workers in every human-owned lifecycle run/resume. The installed Spec Kit adapter's
default `codex exec` can return success after reporting that its filesystem is read-only,
leaving required artifacts absent. The invocation-scoped policy verifies the adapter argv
and native Windows writes before dispatch, rejects conflicting permission overrides and
restores the caller's environment. It leaves persistent config, trust, history and human
review gates intact. Raw Spec Kit resume is not the supported lifecycle entrypoint.
Regression fixtures start no coding agents. A fresh normal-user Windows control verified
that read-only denies writes and workspace-write permits write/readback/cleanup; this does
not claim a new complete model-driven bootstrap acceptance run.

The candidate also fixes governance installation validation when the Python interpreter
running `governance_state.py` has no PyYAML. The supplied configuration starts with
`schema_version: "1.0"`; the dependency-free mapping parser now accepts that scalar.
It continues to reject malformed configuration structure. Consumers do not need to
edit the supplied file or install PyYAML for governance validation.

Roadmap registrations now require current ADR hashes. A stale resolution returns to
architecture with actionable conflict guidance rather than failing at the later due gate.
The historical 0.11.0 placement-contract omission is already fixed in published 0.12.1;
this candidate does not change the current shell or host placement contracts.

The combined candidate also admits the latest matching standalone native
compatibility receipt while preserving Active/Delivered roadmap state. Explicit
post-bootstrap continuation archives completed authority, protects intake,
ratification and Accepted ADRs, renews stale executable proof inputs only in the
matching continuation step, and requires fresh human review and completion.
See [the post-bootstrap handoff](post-bootstrap-release-handoff-2026-10-02.md)
for the exact admission and consumer recovery boundaries.

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

On this host the pinned runtimes are cached under `artifacts/toolchains`; a fresh
terminal otherwise selects the global, incompatible SDK/Node versions. The local
helper `scripts/Invoke-LocalRelease.ps1` selects cached .NET 10.0.202, Node 24.20.0
and npm 11.19.0, uses the native `npm.cmd` executable and Windows system CA trust,
bounds the owned process PATH and restores the caller's environment afterward.
Its `-PrepareOnly` mode verifies setup without running the suite or a coding agent.
The complete mode remains human-owned under AGENTS.md.

Freeze this checkout throughout Release validation. Run other development in a
separate checkout; concurrent source edits invalidate its evidence even when every
check passes. The runner now checks source integrity before and after each check,
preserves the journal and stops with `PROGRAM_KIT_RELEASE_SOURCE_CHANGED` as soon
as it observes a changed commit, working tree or inventory. The receipt's clean
source and exact-commit gates remain mandatory.

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
