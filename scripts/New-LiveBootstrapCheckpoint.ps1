[CmdletBinding()]
param(
    [string]$Authorization = '',
    [string]$Scenario = ''
)

$ErrorActionPreference = 'Stop'
throw 'LIVE_BOOTSTRAP_WORKFLOW_RETIRED: paid bootstrap execution is retired. Use $speckit-program-kit-governance-product-intake, review the project baseline, then continue with specification intake. Existing manifests and checkpoints remain historical evidence; no authorization was consumed.'
