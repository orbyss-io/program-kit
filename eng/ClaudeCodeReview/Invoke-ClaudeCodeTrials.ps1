[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string] $ReviewKit,
    [Parameter(Mandatory = $true)] [string] $ConsumerRoot,
    [Parameter(Mandatory = $true)] [string] $ProgramKitPath,
    [string] $ExpectedClaudeCodeVersion = '2.1.220',
    [ValidateRange(10, 10)] [int] $Trials = 10,
    [Parameter(Mandatory = $true)] [string] $ReviewerIdentity,
    [switch] $AuthorizeLiveProviderExecution
)

$ErrorActionPreference = 'Stop'
$pkKit = (Resolve-Path -LiteralPath $ReviewKit).Path
$pkConsumer = (Resolve-Path -LiteralPath $ConsumerRoot).Path
$pkProgramKit = (Resolve-Path -LiteralPath $ProgramKitPath).Path
$pkManifest = Get-Content -Raw -LiteralPath (Join-Path $pkKit 'manifest.json') | ConvertFrom-Json -Depth 20
if (-not $AuthorizeLiveProviderExecution) { throw 'Explicit current human authority for live Claude execution is required.' }
if ($pkManifest.canonicalDependencyStatus -ne 'accepted' -or $pkManifest.supportClaim -ne 'supported') {
    throw 'Live Claude trials are blocked because the sealed kit does not bind an accepted canonical dependency and supported adapter.'
}
$pkReportedVersion = (& claude --version 2>&1 | Out-String).Trim()
if ($pkReportedVersion -notmatch ('^' + [regex]::Escape($ExpectedClaudeCodeVersion) + '(?:\s|$)')) { throw 'PKCLD0001: the observed Claude Code version is not the exact selected release.' }

$pkSchema = '{"type":"object","additionalProperties":false,"required":["caseIdentity","programKitOutcome","effectState","status"],"properties":{"caseIdentity":{"type":"string"},"programKitOutcome":{"enum":["succeeded","needs-input","blocked","cancelled","faulted"]},"effectState":{"enum":["none","candidate-only","committed","indeterminate"]},"status":{"enum":["passed","failed","incompatible","inconclusive"]}}}'
$pkSummaries = [Collections.Generic.List[object]]::new()
for ($pkOrdinal = 1; $pkOrdinal -le $Trials; $pkOrdinal++) {
    $pkCase = 'claude-live-' + $pkOrdinal.ToString('00')
    $pkPrompt = "Use /program-kit for bounded case $pkCase. Treat Program Kit JSON and actual effects as authoritative. Return only the requested bounded classification."
    $pkProviderResult = & claude -p $pkPrompt --output-format json --json-schema $pkSchema --allowedTools $pkProgramKit
    if ($LASTEXITCODE -ne 0) { throw "PKCLD0006: live Claude trial $pkOrdinal did not complete." }
    try { $pkBounded = $pkProviderResult | ConvertFrom-Json -Depth 10 }
    finally { $pkProviderResult = $null }
    if ($pkBounded.caseIdentity -ne $pkCase) { throw "PKCLD0004: trial $pkOrdinal changed the case identity." }
    $pkSummaries.Add([ordered]@{
        ordinal = $pkOrdinal
        caseIdentity = $pkCase
        programKitOutcome = $pkBounded.programKitOutcome
        effectState = $pkBounded.effectState
        status = $pkBounded.status
        reviewerIdentity = $ReviewerIdentity
    })
}
$pkEvidenceRoot = Join-Path $pkConsumer '.program-kit/evidence'
New-Item -ItemType Directory -Path $pkEvidenceRoot -Force | Out-Null
$pkRecord = [ordered]@{ schema = 'program-kit.claude-code-live-trials/v1'; providerVersion = $ExpectedClaudeCodeVersion; reviewerIdentity = $ReviewerIdentity; trials = $pkSummaries }
$pkRecord | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $pkEvidenceRoot 'claude-live-trials.json') -Encoding utf8NoBOM
Write-Output ($pkRecord | ConvertTo-Json -Depth 20 -Compress)
