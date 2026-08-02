[CmdletBinding()]
param(
    [Parameter()]
    [ValidateSet('Status', 'Upgrade')]
    [string]$Mode = 'Status',

    [Parameter()]
    [string]$Integration = 'codex'
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot

function Invoke-Specify {
    param([Parameter(Mandatory)][string[]]$Arguments)

    & specify @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Spec Kit command failed: specify $($Arguments -join ' ')"
    }
}

Push-Location $repositoryRoot
try {
    & (Join-Path $PSScriptRoot 'Assert-SpecKitIntegrity.ps1')
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
    Invoke-Specify @('workflow', 'update', 'speckit')

    $extensionsFile = Join-Path $repositoryRoot '.specify/extensions.yml'
    if (Test-Path -LiteralPath $extensionsFile -PathType Leaf) {
        Invoke-Specify @('extension', 'update')
    }

    & (Join-Path $PSScriptRoot 'Assert-SpecKitIntegrity.ps1')
    if ($LASTEXITCODE -ne 0) {
        throw 'The upgraded Spec Kit core is incompatible with the Program Kit project layer. Do not force or commit the upgrade; reconcile the reported boundary explicitly.'
    }

    Write-Host 'Manifest-aware upgrade completed. Review the Git diff and run PrePr verification before opening a pull request.'
}
finally {
    Pop-Location
}
