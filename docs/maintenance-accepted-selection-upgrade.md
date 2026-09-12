# Accepted selections before materialization

The published 0.10.2 sequential updater rejects an Accepted building-block selection
without `.program-kit/building-blocks.lock.json` (PKU116). Bootstrap architecture
approval can legitimately produce this state: acceptance records planned placements,
while the later materialization phase owns creation of project dependencies and the
generated lock. The updater also unconditionally applies the selection after installing
components, so removing only its missing-lock check is insufficient.

The corrected updater validates the Accepted selection's catalog, architecture authority,
and resolution before installation. It permits a planned-only state only when every target
has valid planned placement provenance, all targets and managed outputs are absent,
no unfinished materialization transaction exists, and no unmanaged building-block
dependencies are present. It revalidates that state after installation without applying it.

Materialized selections must have a current lock matching installed selection/catalog
authority and current managed outputs. Their provenance is refreshed through the existing
plan/apply transaction. Missing, corrupt, stale, or drifted materialized state fails before
component mutation. Draft selections still require acceptance; catalog resolution changes
still require a reviewed transition. No-selection installations retain their existing path.

## Bounded migration using the published bundle

An affected consumer can use this reviewed updater correction as an external migration
orchestrator while installing the unchanged, verified published 0.10.2 bundle. Run the
updater from the correction's exact checkout, with `--release-root` pointing to the extracted
published bundle and `--target` pointing to the consumer:

```powershell
python C:\path\to\reviewed-correction\scripts\upgrade_program_kit.py `
  --release-root C:\path\to\verified-published-0.10.2 `
  --target C:\path\to\consumer --integration codex
```

Keep `openapi_upgrade_reconciliation.py` alongside the updater in its source checkout;
this helper is unchanged from 0.10.2. Record the correction commit and updater SHA-256 in
the maintenance handoff. The published bundle, tag, receipt, and attestations remain
unchanged. This is an explicitly identified migration correction; the successful 0.10.2
Release receipt does not claim to cover the later updater source change.

Preserve the accepted-run recovery archive before upgrading. After successful coherent
installation, invoke the installed recovery command with its original handoff, following
[accepted-run recovery](maintenance-readiness-recovery.md). The migration does not approve
architecture changes or establish provider compatibility/readiness.

## Validation

`validate_local_upgrade.py` now exercises actual sequential installation for planned-only
and materialized Accepted selections. It verifies immutable selection/ADR/map bytes, no
fabricated lock or target files, refreshed applied provenance, and rejection of changed
catalogs, Draft/missing placement/invalid authority, unmanaged dependencies, pending
transactions, existing output remnants, missing/corrupt/stale locks, and output drift.

`probe_accepted_upgrade_recovery.py` takes an explicit consumer path and run ID, copies its
actual installed tools and authority into a disposable directory, runs the corrected updater
against an explicitly supplied release bundle, and invokes installed recovery preparation
and installation-coherence validation. It verifies preserved original evidence, absent
materialization/completion, and an unchanged source consumer. It starts no coding agent and
does not claim to execute the architecture producer or prove provider compatibility.
