# Preparing Program Kit 0.12.1

This patch candidate addresses three defects observed in a human-led v0.12.0 consumer trial.
It is based on published tag v0.12.0 (commit b70b94280c68b35ef6827680507fcf3b5321f5d6).
It is not a publication claim. All Program Kit components advance together to 0.12.1;
Foundation 0.2.2, Forms 0.2.0, Localization 0.1.1 and managed toolchain pins stay unchanged.

## Corrections and authority boundaries

- Intake guidance previously requested "draft awaiting review" in project-intent.md but only
  changed the JSON status after confirmation. Author a stable reference to the contract instead.
  Read-only draft validation rejects duplicated current status labels. It does not infer
  approval from prose or replace the human confirmation, and semantic prose review remains needed.
- A generated row-lock test caught only a direct PostgresException. EF's Npgsql execution strategy
  wrapped the expected 55P03 lock timeout in InvalidOperationException. The maintained provider
  recipe now owns this mechanism case, accepts only that direct or directly wrapped SQLSTATE at
  the contended query, tests unrelated-error negatives, and verifies lock release after rollback.
  Full inner exceptions reach retained JUnit and bounded password-redacted diagnostics. This does
  not select a consumer locking policy or prove its household/domain rules.
- An unused raw ADR fixture changed bytes during approval promotion and invalidated a passing
  proof. Preflight now rejects ADR fixtures, including cataloged ADRs outside the conventional
  directory. Canonical source/decision evidence keeps semantic binding; runtime parameters remain
  separate byte-bound fixtures. No hash validator is relaxed and no approval is synthesized.

The original trial also needed a conditional Ready transition restored after native proof
invalidation. The existing proof-plan contract already requires the complete readyWhenProven
transition; it is retained, not replaced by an unconditional Ready assignment.

## Existing consumers and preserved trials

Do not edit a completed trial or reuse its approvals for changed outputs. This candidate does not
modify the preserved v0.12.0 trial or the sibling prepared for an exact same-input v0.12.0 rerun.
Old confirmed inputs remain valid with their historical wording and exact hashes; the contract
remains confirmation authority. New draft validation requires a stable status reference. Do not
rewrite old bound sources for editorial cleanup. Changed intent still needs staged re-analysis.
For old custom proof contracts containing ADR fixtures, preserve the failed attempt, remove the
unused fixture (or bind consumed runtime parameters separately), retain semantic ADR obligations,
and execute a fresh proof. New tooling changes proof provenance; old receipts are not relabeled.
Review changed proof/architecture evidence again at the normal workflow gate.

## Validation and publication handoff

Preparation uses targeted regressions and the bounded Development suite. The PostgreSQL test in
validate_bootstrap_compatibility executes the maintained C# fixture against the exact selected
server image through real renew/locked restore; it starts no coding agent. Original trial logs
are local evidence, not shipped fixtures or claims about this candidate's validation.

Once the candidate is approved to proceed toward publication, commit it and verify a clean tree.
Run the complete deterministic Release suite in a normal user-owned PowerShell terminal:

```powershell
Set-Location 'C:\Code\Orbyss\_ProgramKit\artifacts\worktrees\consumer-bootstrap-fixes-0.12.1'
.\scripts\Test-ProgramKit.ps1 -Suite Release -Approved -BrowserEngines 'chromium,webkit'
```

Inspect artifacts/release-validation-0.12.1.log, the per-check journals, built asset hashes and
artifacts/release-receipt-0.12.1.json before publishing. These are shipped product changes, so the
old v0.12.0 Release receipt cannot validate this candidate. Firefox remains in CI; its local host
limitation is unchanged. The tagged Release workflow must fully pass before consumer availability
is announced. No tag, push, publication or paid live-acceptance run is part of this preparation.

For later non-shipping corrections, follow
[Reusing local Release evidence after non-shipping changes](../AGENTS.md#reusing-local-release-evidence-after-non-shipping-changes).
Verify the complete diff against actual packaging inputs, receipt/log validity and artifact hashes;
record both commits, supplementary checks and green CI. Preserve the original receipt unchanged.
The tagged Release workflow still runs in full and produces its own exact-commit evidence.
Failed-tag reuse additionally requires demonstrating a test/assertion or CI-only defect and that
nothing was published from the failed candidate. Exact corrected-commit and same-tag approval is still required.
If any reuse condition is unproven, obtain fresh local Release evidence.
