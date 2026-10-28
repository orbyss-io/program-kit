# Fixture isolation and disposable installation

This review uses unrelated synthetic inputs and maintained Program Kit sources. Private
consumer documents, fixture identities, paths, decisions and diagnostic packets are excluded.

The inspected installed scratch owners matched the contributor source before these repairs.
The native offline regression reproduces ancestor analyzer inheritance and `NU1015` using the
maintained `ProgramKit.Build.props` under a synthetic central-package consumer. A project-body
import flag does not stop the earlier SDK props import. This is a Program Kit defect, independent
of the disposable directory's depth. No product analyzer, SDK, dependency pin or profile changes.

A separate stale executable fixture is a producer/plan-binding problem. Existing preparation
correctly rejects it; the repaired plan gate now checks every contract before any probe can
provision dependencies or invalidate retained eligibility. A synthetic later-contract failure
asserts that no earlier probe runs and original ledger bytes remain unchanged.

| Owner | Result to inspect |
| --- | --- |
| `runtime_fixture.py`, `bootstrap_compatibility.py` | Version 1 managed scratch-root MSBuild props/targets stop ancestor imports for root and nested standalone projects; shared configuration is checked again by supervisor restoration. |
| `fixture_readiness.py` | Conflicting previously authored boundary bytes remain in their original recipe and pickup archive; only the distinct new draft is aligned. |
| `bootstrap_proof_plan.py` | Read-only and executing paths reject stale fixture inputs for the entire plan before provisioning. Existing receipt/closure checks remain in force. |
| `intake_session.py`, `Start-IntakeSession.ps1` | Full release-builder archives replace separate intake packaging and development-directory workflow/bundle inputs. Native catalog installers consume exact verified archive bytes. Supplied same-version assets are supported with `-AssetsDirectory`; `installation-inputs.json` records hashes. |

The earlier trial route used real extension archives and native bundle installation, but its
workflow and bundle inputs came from contributor directories and its governance archive omitted
the release builder's generated guidance. That was an installation-fidelity gap, distinct from
the reproduced scratch defect. The replacement setup serves all six unmodified release archives
through temporary local catalogs and removes their registrations after installation.

Reproduce with the existing prepared interpreter, without installing device tools:

```powershell
./scripts/Test-ProgramKit.ps1 -Python <prepared-python>
<prepared-python> scripts/run_validation.py --suite Affected --changed-from dd20403
<prepared-python> scripts/run_validation.py --suite Affected --check validate_fixture_isolation --check validate_bootstrap_proof_plan --check validate_intake_session --reason "Scratch isolation, complete-plan freshness and release archive inputs"
<prepared-python> scripts/run_validation.py --suite Affected --check validate_intake_install --reason "Actual archive-only native disposable consumer installation"
```

`validate_fixture_isolation` retains both native streams, commands and exit codes under ignored
`artifacts/fixture-isolation/`. It observes expected `NU1015`, successful offline restore/build/run,
exact direct pins, blocked ancestor targets and unchanged application import files.
`validate_intake_install` retains logs under ignored `artifacts/intake-install/`; it checks every
installed extension archive member, exact workflow bytes and native installation coherence.
These tests start no coding agent and use no private product input.

Initial sandbox loopback startup and the first archive-URL bundle attempt failed; their original
validation records remain available. The native bundle CLI requires a catalog ID. The repaired
route registers a temporary bundle catalog and passed actual host-process installation. This
local check does not establish Linux/package CI, provider runtime compatibility or consumer
acceptance. No existing private consumer or saved workflow is restarted or rewritten.
