# Disposable engineering output

New Program Kit engineering baselines reserve the root `eng/` directory for ignored,
deterministically reproducible output. Deleting it loses no authored source, selected
dependency, upgrade provenance, private data or operational evidence.

| Owner | Durable location |
| --- | --- |
| Maintained and application scripts | `scripts/` |
| Helper projects, browser fixtures and application tools | `tools/` |
| Authored composition, architecture, verification, OpenAPI and handoff configuration | `config/program-kit/` |
| Native imported build/package policy | `config/program-kit/build/` |
| Toolkit ownership baseline and exact selected dependency profile/snapshots | `config/program-kit/managed.json`, `config/program-kit/dependency-profile.json`, `config/program-kit/dependency-profiles/` |
| App-wide authored UI inputs and output protection | `config/program-kit/ui/` |
| Native package/tool selections and locks | Existing native project, `.config/`, version and lock files |
| Irreplaceable execution outcomes, failed diagnostics and private runtime data | Their existing evidence/private owners, outside `eng/` |

Run `python scripts/regenerate_eng.py --repository .` with the installed interpreter
matching `.python-version`. `--check` reports missing/stale projections without writing.
Native `dotnet restore`, `dotnet build` and `dotnet test` use this same script before
restore graph collection/build. Durable `Directory.*` imports work at first project
evaluation while `eng/` is absent; required native policy is never conditionally skipped.
PowerShell wrappers remain `scripts/Restore.ps1`, `scripts/Build.ps1` and
`scripts/Invoke-RepositoryVerification.ps1`.

The native extension command `speckit.program-kit-dotnet.regenerate-eng` installs the
agent integration skill that invokes this entrypoint. Normal engineering needs neither
an agent nor `.agents`/`.specify`. The script uses only Python's standard library and
the exact copied toolkit helpers. It installs nothing, selects no newer dependency,
initializes no account and starts no application/service. Missing durable inputs or a
different selected toolkit/runtime fail with a repair diagnostic before output writes.

`engineering.json` records the selected toolkit helper identities and required input
paths. It is a regeneration recipe, not approval or acceptance evidence. Authored input
edits are processed by their ordinary validators; their hashes in `eng/inputs.json`
only describe the current projection. Native policy/dependency changes retain their
normal owners. Concurrent native projects publish identical projections atomically.

Existing consumers are not migrated automatically. Engineering setup refuses a legacy ownership baseline or nonempty unrecognized `eng/` before
writing defaults or ignore rules. Review and relocate actual source/configuration
through an explicitly requested consumer migration first. Native preview toolkit refresh
preserves authored work; it does not perform that engineering migration. Application workers
and their substantive supervisors belong together in `tools/`; thin launcher and maintenance
scripts belong in `scripts/`. Historical
workflow authority and failed operational evidence are never relabeled or regenerated.
