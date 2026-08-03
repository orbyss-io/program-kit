[CmdletBinding()]
param(
    [switch]$RepositoryOnly
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$failures = [System.Collections.Generic.List[string]]::new()
$trackedPaths = $null

if ($RepositoryOnly) {
    $trackedPaths = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::Ordinal
    )
    $trackedOutput = & git -C $repositoryRoot ls-files
    if ($LASTEXITCODE -ne 0) {
        Write-Error 'Unable to enumerate repository-tracked files for the Spec Kit integrity check.'
        exit 1
    }

    foreach ($trackedPath in $trackedOutput) {
        [void]$trackedPaths.Add($trackedPath.Replace('\', '/'))
    }
}

function Add-IntegrityFailure {
    param([Parameter(Mandatory)][string]$Message)

    $failures.Add($Message)
}

function Assert-RequiredFile {
    param([Parameter(Mandatory)][string]$RelativePath)

    $path = Join-Path $repositoryRoot $RelativePath
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        Add-IntegrityFailure "Required project-owned Spec Kit file is missing: $RelativePath"
    }
}

function Assert-ContainsLiteral {
    param(
        [Parameter(Mandatory)][string]$RelativePath,
        [Parameter(Mandatory)][string]$Expected
    )

    $path = Join-Path $repositoryRoot $RelativePath
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        return
    }

    $content = [System.IO.File]::ReadAllText($path)
    if (-not $content.Contains($Expected, [System.StringComparison]::Ordinal)) {
        Add-IntegrityFailure "Required content '$Expected' is missing from $RelativePath"
    }
}

$manifestDirectory = Join-Path $repositoryRoot '.specify/integrations'
foreach ($manifestPath in Get-ChildItem -LiteralPath $manifestDirectory -Filter '*.manifest.json') {
    $manifest = Get-Content -LiteralPath $manifestPath.FullName -Raw | ConvertFrom-Json
    foreach ($entry in $manifest.files.PSObject.Properties) {
        $managedRelativePath = $entry.Name.Replace('\', '/')
        if ($RepositoryOnly -and -not $trackedPaths.Contains($managedRelativePath)) {
            continue
        }

        $managedPath = Join-Path $repositoryRoot $entry.Name
        if (-not (Test-Path -LiteralPath $managedPath -PathType Leaf)) {
            Add-IntegrityFailure "Spec Kit managed file is missing: $($entry.Name)"
            continue
        }

        $actualHash = (Get-FileHash -LiteralPath $managedPath -Algorithm SHA256).Hash.ToLowerInvariant()
        $expectedHash = ([string]$entry.Value).ToLowerInvariant()
        if ($actualHash -ne $expectedHash) {
            Add-IntegrityFailure "Spec Kit managed file was edited in place: $($entry.Name). Put project policy in an override, preset, extension, or workflow overlay instead."
        }
    }
}

$requiredFiles = @(
    '.specify/templates/overrides/spec-template.md',
    '.specify/templates/overrides/plan-template.md',
    '.specify/templates/overrides/tasks-template.md',
    '.specify/workflows/overlays/speckit/program-kit-delivery.yml',
    '.specify/memory/constitution.md',
    'eng/Invoke-Verification.ps1',
    'eng/Invoke-SpecKitUpgrade.ps1',
    'eng/SPECKIT.md'
)
foreach ($requiredFile in $requiredFiles) {
    Assert-RequiredFile $requiredFile
}

$commonScript = Join-Path $repositoryRoot '.specify/scripts/powershell/common.ps1'
if (Test-Path -LiteralPath $commonScript -PathType Leaf) {
    . $commonScript
    foreach ($templateName in @('spec-template', 'plan-template', 'tasks-template')) {
        $resolved = Resolve-Template -TemplateName $templateName -RepoRoot $repositoryRoot
        $expected = (Resolve-Path -LiteralPath (Join-Path $repositoryRoot ".specify/templates/overrides/$templateName.md")).Path
        if (-not $resolved -or (Resolve-Path -LiteralPath $resolved).Path -ne $expected) {
            Add-IntegrityFailure "Template resolution no longer selects the project override for $templateName."
        }
    }
}

$baseWorkflow = '.specify/workflows/speckit/workflow.yml'
foreach ($anchor in @('specify', 'review-spec', 'plan', 'review-plan', 'tasks', 'implement')) {
    Assert-ContainsLiteral $baseWorkflow "- id: $anchor"
}

$overlay = '.specify/workflows/overlays/speckit/program-kit-delivery.yml'
foreach ($requiredText in @(
    'extends: "speckit"',
    'insert_after: specify',
    'command: speckit.clarify',
    'replace: review-spec',
    'replace: review-plan',
    'insert_before: implement',
    'command: speckit.analyze',
    'id: review-tasks'
)) {
    Assert-ContainsLiteral $overlay $requiredText
}

$taskTemplate = Join-Path $repositoryRoot '.specify/templates/overrides/tasks-template.md'
if (Test-Path -LiteralPath $taskTemplate -PathType Leaf) {
    $taskTemplateContent = [System.IO.File]::ReadAllText($taskTemplate)
    if ($taskTemplateContent.Contains('Tests are OPTIONAL', [System.StringComparison]::OrdinalIgnoreCase)) {
        Add-IntegrityFailure 'The project tasks override has regressed to optional proof for governed requirements.'
    }
}

Assert-ContainsLiteral '.specify/templates/overrides/spec-template.md' '## Intent, Authority, and Scope *(mandatory)*'
Assert-ContainsLiteral '.specify/templates/overrides/spec-template.md' '### Requirement Classification'
Assert-ContainsLiteral '.specify/templates/overrides/plan-template.md' '## Requirement and Proof Matrix *(mandatory)*'
Assert-ContainsLiteral '.specify/templates/overrides/plan-template.md' '## Verification Strategy *(mandatory)*'
Assert-ContainsLiteral '.specify/templates/overrides/tasks-template.md' '**Proof rule**:'
Assert-ContainsLiteral '.specify/memory/constitution.md' 'Equivalent evidence MUST be reused while its declared input and invalidation set'
Assert-ContainsLiteral 'eng/Invoke-Verification.ps1' "ValidateSet('Edit', 'Story', 'PrePr', 'Ci', 'Human', 'Fast', 'Contract')"
Assert-ContainsLiteral '.github/workflows/vertical-slice.yml' './eng/Assert-SpecKitIntegrity.ps1 -RepositoryOnly'
Assert-ContainsLiteral '.github/workflows/vertical-slice.yml' 'cancel-in-progress:'

if ($failures.Count -gt 0) {
    Write-Error ("Spec Kit project integrity failed:`n - " + ($failures -join "`n - "))
    exit 1
}

$scope = if ($RepositoryOnly) { 'repository-tracked managed core' } else { 'installed managed core' }
Write-Host "Spec Kit project integrity passed: $scope is pristine and project overlays remain active."
$global:LASTEXITCODE = 0
