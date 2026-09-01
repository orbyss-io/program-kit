# Recovering a hash-approved bootstrap after roadmap drift

Program Kit 0.6.9 supports recovery without cleaning or reinitializing the consumer repository.
The failed run itself must not be resumed: Spec Kit persists the workflow definition with each run,
so resuming a 0.6.8 run would retry its old final step without the new synchronization and
cross-artifact validation steps.

Do not edit `architecture.md`, `traceability.md`, the bootstrap review packet, or approval JSON by
hand. Those artifacts are hash-bound. Recovery uses a new 0.6.9 workflow run over the existing
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
