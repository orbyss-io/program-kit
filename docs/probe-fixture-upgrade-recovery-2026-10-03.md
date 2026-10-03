# Registered bootstrap probes: corrective upgrade recovery

InsurancePolicyEvaluator remains coherently installed at 0.12.2 after its earlier
post-install convergence failure. Its immutable accepted baseline is 0.12.1,
bootstrap run `26232ea0` is completed, and no successful upgrade authority was
recorded. The 0.12.4 updater stopped before component mutation with 26 PKP002
blockers because it counted two registered probe sources as application projects.

Program Kit 0.12.5 corrects that classification. It does not manufacture feature
persistence admission, alter provider intent or reinterpret completed bootstrap.
The two proposed owners remain explicit future feature-admission obligations.
Real application projects, invalid probe bindings and installed/admitted provider
transitions still require their existing admission/acceptance checks.

After the full official `v0.12.5` Release workflow succeeds, download its full
archive and verify the published checksum and attestation. Extract it outside the
consumer tree to `C:\ProgramKitReleases\program-kit-0.12.5`. Do not stage it inside
`.program-kit/releases`, reinitialize Spec Kit or rerun bootstrap. In normal
user-owned PowerShell, run the supported updater:

```powershell
Set-Location C:\Users\tech_\Code\InsurancePolicyEvaluator
$specifyPython = Join-Path ((& uv tool dir).Trim()) 'specify-cli/Scripts/python.exe'
& $specifyPython C:\ProgramKitReleases\program-kit-0.12.5\scripts\upgrade_program_kit.py `
  --release-root C:\ProgramKitReleases\program-kit-0.12.5 `
  --target C:\Users\tech_\Code\InsurancePolicyEvaluator `
  --integration codex
if ($LASTEXITCODE -notin 0,3) { throw 'Upgrade incomplete; preserve diagnostics and attempt evidence.' }
& $specifyPython .specify/extensions/program-kit-governance/scripts/governance_state.py validate-installation
if ($LASTEXITCODE -ne 0) { throw 'Installation is incoherent.' }
& $specifyPython .specify/extensions/program-kit-governance/scripts/governance_state.py validate-setup-authority
if ($LASTEXITCODE -ne 0) { throw 'Upgrade authority is incomplete.' }
```

If `SCHEMA_RUNTIME_MISSING` is reported, prepare that same interpreter/runtime,
then retry the supported command:

```powershell
& $specifyPython C:\ProgramKitReleases\program-kit-0.12.5\extensions\program-kit-governance\scripts\schema_runtime.py setup `
  --project-root C:\Users\tech_\Code\InsurancePolicyEvaluator
```

Exit 3 means offline setup converged while explicit package verification remains
pending; follow its exact instructions only for materialized dependencies. The
accepted version record must name baseline 0.12.1, observed previous installation
0.12.2 and new installation 0.12.5. It must never invent successful 0.12.1-to-0.12.2
or 0.12.4 upgrade records. Failed attempts remain preserved and authority is written
only after full convergence. Existing human gates stay separate.

Verify these original SHA-256 values before and after recovery:

| Protected artifact | SHA-256 |
| --- | --- |
| `docs/architecture/bootstrap-decisions.json` | `73f8ec1a0500768a5d8a6d0feb33db988d383f9509387ab0252153619c554b8a` |
| `docs/architecture/bootstrap-intake.json` | `0c0c041d2bcf4e14ff4b7225ac6fef9f5e1df08ada516e7afd686ff6525f54bc` |
| `.specify/memory/constitution.md` | `53da462fd3b40c70037f1c6f7582a1b48907ee955346a25423cdbfff5ad14ad1` |

Also preserve the completed run, proof plan, compatibility recipes, contracts and
source fixtures. The maintenance task checked their hashes read-only and did not
execute this recovery. After tool recovery, RM-01 specification intake keeps its
approved synthetic/redacted enrollment, readable policy upload and cited
supported/excluded/unknown indication scope; owning later phase gates remain.
