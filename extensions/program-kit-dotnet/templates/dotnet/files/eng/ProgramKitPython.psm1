Set-StrictMode -Version Latest

function Resolve-ProgramKitPython {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Repository)
    try {
        $recordPath = Join-Path $Repository '.specify/python-runtime.json'
        $saved = $null
        if (Test-Path -LiteralPath $recordPath) {
            $saved = Get-Content -LiteralPath $recordPath -Raw | ConvertFrom-Json
            if ($saved.contractVersion -ne 1 -or -not $saved.executable) { throw 'Unsupported core runtime record.' }
        }
        $executable = $env:SPECKIT_PYTHON
        if (-not $executable -and $saved) { $executable = $saved.executable }
        if (-not $executable) {
            $command = Get-Command python -ErrorAction SilentlyContinue
            if ($command) { $executable = $command.Source }
        }
        if (-not $executable -or -not [IO.Path]::IsPathRooted($executable) -or
            -not (Test-Path -LiteralPath $executable -PathType Leaf)) { throw 'Selected interpreter is absent or not an absolute file.' }
        $contract = Join-Path $PSScriptRoot 'python_runtime_contract.py'
        $output = & $executable $contract --repository $Repository --executable $executable --purpose engineering
        if ($LASTEXITCODE -ne 0) { throw 'Applicable Python runtime admission failed.' }
        $actual = $output | ConvertFrom-Json
        return [IO.Path]::GetFullPath($actual.executable)
    }
    catch {
        throw "PKV005 engineering Python is unavailable or stale. Select an installed absolute SPECKIT_PYTHON matching .specify/python-runtime.json, or regenerate core instructions after a reviewed runtime change. Verify the executable and .python-version in your terminal. $($_.Exception.Message)"
    }
}

Export-ModuleMember -Function Resolve-ProgramKitPython
