# Equipment Lending bootstrap failure cd738af9

The real human-owned native workflow passed intake validation, assessment review
and constitution ratification, then stopped at `validate-architecture-output`.
The architecture producer reported `PKB303` and left Proposed ADRs and a Draft
selection. Its zero process exit did not mean architecture completion; the native
gate correctly failed. This run is preserved as native workflow evidence, not
relabelled as an authorized live-harness checkpoint.

## Diagnosis and corrections

The architecture brief prohibited validator/code discovery but omitted rules
enforced by `building_blocks.py`: `cshell-shell` requires a `shells.json` path and
the runtime `shell` identity, while `host-image` requires a Dockerfile. The producer
tried `shells/lending-local.json`, then `LendingShell.cs`; its host target was a
compiled DLL. These were preventable attempts caused by an incomplete contract.

The selection schema now owns executable path/identity rules for all six target
kinds. Both the resolver and the research/architecture projection consume those
same rules. The projection includes meanings, legal examples and required fields
before drafting. Examples do not prescribe directory layout. Diagnostics name
the expected artifact instead of requiring another guessing cycle.

Offline recovery also reproduced a second failure: a valid evolved architecture
map no longer matches the original intake byte hash, and structural failure can
leave the derived DSL stale. Recovery now validates current map structure and its
alignment with immutable intake semantics, preserves the original artifacts,
refreshes only the derived DSL/context and validates the full evolved handoff.
It never rewrites intake hashes, the canonical map, approved assessment,
constitution or workflow state. Invalid input is still rejected; a rejected
context rebuild restores the preceding DSL bytes.

## Evidence

- `artifacts/bootstrap-failure-cd738af9/snapshot.json` binds the preserved failure.
- `placement-replay.json` in that directory reproduces the actual invalid paths
  and demonstrates valid placement/resolution after correction in a copy only.
- `recovery-replay.json` records native recovery on the real failed map, preserving
  nine authority/state artifacts byte-for-byte.
- `tool-repair/receipt.json` records a real local Spec Kit extension reinstall,
  version-coherence validation and installed recovery in a disposable copy. Initial
  incomplete diagnostic copies and their failures remain separate evidence.
- `artifacts/placement-contract-tests.log` covers all six producer-visible kinds,
  the actual failed shell/DLL paths, required shell identity, case preservation,
  missing pre-dispatch contracts and legacy selection readability.
- `artifacts/placement-recovery-tests.log` covers evolved-map/stale-DSL recovery,
  unchanged authority and rejection of altered confirmed domain/intent semantics.
- `artifacts/placement-recovery-development.log` is the final bounded Development
  pass. `placement-recovery-context.log` records targeted context/freshness checks.
- `artifacts/placement-recovery-build.log` and `placement-recovery-install.log`
  record the successful final candidate build and packaged component/bundle install.

The pasted architecture output reports 104,364 tokens. That is a stage-local
observation, not a complete intake/bootstrap total or a measured avoidable-token
amount. Preserve the terminal/conversation evidence for later attributed analysis.

## Continue the existing consumer

No new paid worker was launched during diagnosis. The original consumer has not
been modified by these repairs. Keep its directory and failed run.

For this **same-version candidate tooling correction**, reinstall the two changed
extensions through Spec Kit so their generated skills and installation metadata
stay coherent. The catalog, package versions and workflow definition are unchanged.
This is not the application upgrade flow: that flow correctly requires Accepted
selection authority, which this failed architecture does not yet have.

From the original consumer in a normal user-owned terminal:

```powershell
$candidateRoot = 'C:\Code\Orbyss\_ProgramKit\artifacts\repository-sync-coordinator'
Set-Location 'C:\Users\Joeyb\AppData\Local\Temp\program-kit-intake-v10enu5e'
specify extension add "$candidateRoot/extensions/program-kit-building-blocks" --dev --force
if ($LASTEXITCODE -ne 0) { throw 'Building-block tooling repair failed.' }
specify extension add "$candidateRoot/extensions/program-kit-governance" --dev --force
if ($LASTEXITCODE -ne 0) { throw 'Governance tooling repair failed.' }
python .specify/extensions/program-kit-governance/scripts/governance_state.py validate-installation
if ($LASTEXITCODE -ne 0) { throw 'Installation coherence check failed.' }
python .specify/extensions/program-kit-governance/scripts/bootstrap_context.py prepare-architecture-recovery --run-id cd738af9 --json
if ($LASTEXITCODE -ne 0) { throw 'Recovery preparation failed; preserve its evidence.' }
```

These commands install tools and prepare the handoff; they do not launch a model.
Return the resulting recovery manifest for review before another paid attempt.
The next human-owned architecture invocation uses the helper's exact
`architecture_skill_input`. It must reconcile Proposed ADR paths with the Draft,
complete narrative output and pass the full architecture validator. Only then
does `specify workflow resume cd738af9` continue the same workflow. Resume alone
retries the failed validator and cannot regenerate the missing architecture.

No new intake, new bootstrap run, fabricated approval or publication follows from
these repairs. The first vertical slice and full independent acceptance remain
outstanding. Source changes invalidate the older exact candidate trial receipt;
any later automated harness phase needs fresh preparation and matching one-use
authorization.
