# Preparing Program Kit 0.12.5

This corrective release fixes 0.12.4's classification of bootstrap compatibility
fixture projects as materialized application projects. All Program Kit installable
components advance together. Public Spec Kit 1.0.1, runtime components, managed
toolchains and existing approval/ratification gates stay unchanged. Published
0.12.4 and its evidence remain immutable.

The maintained classifier uses the native recipe/contract validator and current
bootstrap proof-plan registration. It excludes only bound csproj dependency-target
sources inside `docs/architecture/compatibility`, whose recipe and every fixture
source validate. It executes no recipe and grants no persistence admission.
Ordinary documentation projects, invalid/unregistered probes, application sources
bound as fixtures outside this directory, and real materialized projects still
count. Installed/admitted providers and transitions retain their existing guards.

Regression coverage renders the two maintained `managed-dotnet-runtime` and
`relational-mechanism` probe types for proposed unassigned `policy-portfolio` and
`owner-access` owners with planned targets and no managed baseline. It checks
read-only deferral, invalid bindings, arbitrary documentation/application projects
and admitted/installed transition guards. The real sequential updater test also
preserves generated recipe/contract/source bytes and governed version provenance.
The bounded Development suite passed all 61 checks; all 20 targeted upgrade tests
and the real sequential local upgrade validator passed. The classifier is a new
upgrade-only helper, so the existing proof-validation sources remain byte-identical.

A read-only check of InsurancePolicyEvaluator returned zero blockers and both
deferred owners; 111 protected consumer files, including workflow files and probe
registrations, had identical hashes before and after. No consumer upgrade, bootstrap,
worker, approval or state rewrite was run. See
[consumer recovery](probe-fixture-upgrade-recovery-2026-10-03.md).

## Publication gate

The user requested a corrective release and previously explicitly authorized this
task's complete local Release invocation and maintained task opt-in. Freeze clean
committed source, then run:

```powershell
.\scripts\Invoke-LocalRelease.ps1 -AuthorizedCodexTask
```

The normal terminal command remains:

```powershell
.\scripts\Test-ProgramKit.ps1 -Suite Release -Approved -BrowserEngines 'chromium,webkit'
```

Inspect the preserved transcript, per-check journal, exact-source receipt and asset
hashes. Keep Firefox in CI. Merge only with passing local Release and green latest
candidate CI; verify unchanged merge source, then create the new `v0.12.5` tag.
Availability requires successful tagged Release, attestation, publication and
public installation/upgrade validation. Never move published 0.12.4 or replace
consumer history to recover an upgrade.

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
