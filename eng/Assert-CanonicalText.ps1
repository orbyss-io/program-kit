[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repositoryRoot
try {
    $entries = @(git ls-files --eol)
    if ($LASTEXITCODE -ne 0) { throw 'Unable to inspect tracked file line endings.' }

    $nonCanonical = @($entries | Where-Object {
        $_ -match '(^|\s)i/(crlf|mixed)(\s|$)' -or
        $_ -match '(^|\s)w/(crlf|mixed)(\s|$)'
    })

    if ($nonCanonical.Count -gt 0) {
        $details = $nonCanonical -join [Environment]::NewLine
        throw "Tracked text must use LF in both the Git index and working tree. Configure this clone with 'git config --local core.autocrlf false' and 'git config --local core.eol lf', then normalize the listed files:`n$details"
    }
}
finally {
    Pop-Location
}
