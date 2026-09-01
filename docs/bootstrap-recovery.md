# Recovering a hash-approved bootstrap after roadmap drift

Program Kit 0.6.10 supports recovery without cleaning or reinitializing the consumer repository.
The failed run itself must not be resumed: Spec Kit persists the workflow definition with each run,
so resuming a 0.6.8 run would retry its old final step without the new synchronization and
cross-artifact validation steps.

Do not edit `architecture.md`, `traceability.md`, the bootstrap review packet, or approval JSON by
hand. Those artifacts are hash-bound. Recovery uses a new 0.6.10 workflow run over the existing
repository. It regenerates architecture and roadmap artifacts, synchronizes the derived roadmap
views, validates them before review, regenerates the final review packet, requires fresh human
approval, replaces `bootstrap-approval.json` with hashes for the newly approved content, reruns
readiness, and only then completes bootstrap.

From a normal user-owned PowerShell prompt in the affected repository, run:

```powershell
Set-Location C:\path\to\PriceCalculator

$failedRunId = 'bf551b86'
$failedInputsPath = ".specify\workflows\runs\$failedRunId\inputs.json"
$failedInputs = Get-Content -Raw -LiteralPath $failedInputsPath | ConvertFrom-Json
$initialDesign = [string]$failedInputs.inputs.initial_design
$integrationState = Get-Content -Raw -LiteralPath '.specify\integration.json' | ConvertFrom-Json
$integration = [string]$integrationState.default_integration
if ([string]::IsNullOrWhiteSpace($integration)) {
    $integration = [string]$integrationState.integration
}

# Program Kit 0.6.9 and earlier registered immutable release catalogs. Replace
# those registrations with the update channel before asking Spec Kit to update.
$catalogRoot = 'https://raw.githubusercontent.com/orbyss-io/program-kit/main/catalogs'
specify extension catalog remove program-kit
if ($LASTEXITCODE -ne 0) { throw 'Could not remove the pinned extension catalog.' }
specify preset catalog remove program-kit
if ($LASTEXITCODE -ne 0) { throw 'Could not remove the pinned preset catalog.' }
specify workflow catalog remove 0
if ($LASTEXITCODE -ne 0) { throw 'Could not remove the pinned workflow catalog.' }
specify bundle catalog remove program-kit
if ($LASTEXITCODE -ne 0) { throw 'Could not remove the pinned bundle catalog.' }

specify extension catalog add "$catalogRoot/extensions.json" --name program-kit --install-allowed
if ($LASTEXITCODE -ne 0) { throw 'Could not register the extension update catalog.' }
specify preset catalog add "$catalogRoot/presets.json" --name program-kit --install-allowed
if ($LASTEXITCODE -ne 0) { throw 'Could not register the preset update catalog.' }
specify workflow catalog add "$catalogRoot/workflows.json" --name program-kit
if ($LASTEXITCODE -ne 0) { throw 'Could not register the workflow update catalog.' }
specify bundle catalog add "$catalogRoot/bundles.json" --id program-kit --policy install-allowed
if ($LASTEXITCODE -ne 0) { throw 'Could not register the bundle update catalog.' }

specify workflow update program-kit-bootstrap
if ($LASTEXITCODE -ne 0) { throw 'Program Kit workflow update failed.' }

specify bundle update program-kit --integration $integration
if ($LASTEXITCODE -ne 0) { throw 'Program Kit bundle update failed.' }

python .specify/extensions/program-kit-governance/scripts/governance_state.py validate-installation
if ($LASTEXITCODE -ne 0) { throw 'Program Kit installation is not version-coherent.' }

specify workflow run program-kit-bootstrap `
  --input "initial_design=$initialDesign" `
  --input "integration=$integration"
if ($LASTEXITCODE -ne 0) { throw 'Recovered bootstrap did not complete.' }

python .specify/extensions/program-kit-governance/scripts/governance_state.py validate-completion
if ($LASTEXITCODE -ne 0) { throw 'Bootstrap completion hashes are invalid.' }
```

Review and decide every displayed gate in the new run. In particular, the final bootstrap gate must
show the regenerated packet before approval. Do not run `specify workflow resume bf551b86`; retain
that failed run as historical evidence.

## Recovering an abandoned run still marked running

Program Kit 0.6.11 adds explicit recovery for this condition.

Spec Kit records a normal interruption as a terminal workflow state, but a hard process termination
can leave its last persisted state as `running`. Program Kit blocks a replacement bootstrap before
intake when it finds such a record because concurrent bootstrap runs would mutate the same governed
artifacts.

First verify that the listed run has no live `specify workflow` process. Then use the exact command
printed by the preflight diagnostic, from the same normal user-owned shell:

```powershell
python .specify/extensions/program-kit-governance/scripts/codex_bootstrap_preflight.py `
  --abandon-run <run-id>
```

The command accepts only a validated `program-kit-bootstrap` run whose current status is `running`.
It atomically changes that run to `aborted`, records the explicit operator action in `log.jsonl`, and
leaves the workflow snapshot, inputs, step results, and prior log evidence intact. It refuses other
workflow types and already-terminal runs. Start a new bootstrap afterward; do not edit or delete the
run directory by hand.
