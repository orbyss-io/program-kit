[CmdletBinding()]
param(
    [Parameter()]
    [ValidateSet('Status', 'Upgrade')]
    [string]$Mode = 'Status',

    [Parameter()]
    [string]$Integration = 'codex',

    [Parameter()]
    [AllowEmptyString()]
    [string]$Workflow = 'speckit',

    [Parameter()]
    [string]$RepositoryRoot,

    [Parameter()]
    [string]$SpecifyCommand = 'specify',

    [Parameter()]
    [string]$IntegrityScript
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = if ($RepositoryRoot) {
    [IO.Path]::GetFullPath($RepositoryRoot)
}
else {
    Split-Path -Parent $PSScriptRoot
}
$integrityScriptPath = if ($IntegrityScript) {
    [IO.Path]::GetFullPath($IntegrityScript)
}
else {
    Join-Path $PSScriptRoot 'Assert-SpecKitIntegrity.ps1'
}

function Invoke-Specify {
    param([Parameter(Mandatory)][string[]]$Arguments)

    & $SpecifyCommand @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Spec Kit command failed: specify $($Arguments -join ' ')"
    }
}

Push-Location $repositoryRoot
try {
    & $integrityScriptPath
    if ($LASTEXITCODE -ne 0) {
        throw 'Refusing Spec Kit maintenance while project integrity is already failing.'
    }

    Invoke-Specify @('integration', 'status', '--json')
    if ($Mode -eq 'Status') {
        Write-Host 'Status is read-only. Use -Mode Upgrade on a clean branch to perform a manifest-aware upgrade.'
        return
    }

    $worktreeChanges = & git status --porcelain
    if ($LASTEXITCODE -ne 0) {
        throw 'Could not inspect the Git worktree before upgrade.'
    }
    if ($worktreeChanges) {
        throw 'Spec Kit upgrades require a clean worktree so every upstream change remains reviewable and recoverable.'
    }

    # Deliberately omit --force. Manifest-aware upgrade must stop on any
    # unexpected local edit to a managed integration or shared core file.
    Invoke-Specify @('integration', 'upgrade', $Integration)
    # Installed workflows have their own lifecycle. The project overlay lives
    # outside the installed workflow directory and is preserved by this update.
    if ($Workflow) {
        Invoke-Specify @('workflow', 'update', $Workflow)
    }

    $extensionsFile = Join-Path $repositoryRoot '.specify/extensions.yml'
    if (Test-Path -LiteralPath $extensionsFile -PathType Leaf) {
        Invoke-Specify @('extension', 'update')
    }

    & $integrityScriptPath
    if ($LASTEXITCODE -ne 0) {
        throw 'The upgraded Spec Kit core is incompatible with the Program Kit project layer. Do not force or commit the upgrade; reconcile the reported boundary explicitly.'
    }

    Write-Host 'Manifest-aware upgrade completed. Review the Git diff and run PrePr verification before opening a pull request.'
}
finally {
    Pop-Location
}
