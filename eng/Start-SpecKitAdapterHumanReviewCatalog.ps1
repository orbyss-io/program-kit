[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $ReviewRoot
)

if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw 'Spec Kit adapter human review requires PowerShell 7 or later.'
}

$ErrorActionPreference = 'Stop'
$review = (Resolve-Path -LiteralPath $ReviewRoot).Path
$environment = Get-Content -LiteralPath (Join-Path $review 'review-environment.json') -Raw |
    ConvertFrom-Json -Depth 20
$comparison = if ($IsWindows) { [StringComparison]::OrdinalIgnoreCase } else { [StringComparison]::Ordinal }
if ($environment.schema -cne 'program-kit.spec-kit-adapter-human-review-seed/v1' -or
    $environment.status -cne 'ready' -or
    -not ([IO.Path]::GetFullPath([string]$environment.reviewRoot).Equals($review, $comparison))) {
    throw 'The selected directory is not the exact prepared human-review seed.'
}

$cliPath = Join-Path $review ([string]$environment.cli.package)
$archivePath = Join-Path $review ([string]$environment.adapter.archive)
$catalogRoot = Join-Path $review 'catalog'
if (-not (Test-Path -LiteralPath (Join-Path $catalogRoot 'catalog.json') -PathType Leaf) -or
    -not (Test-Path -LiteralPath $cliPath -PathType Leaf) -or
    -not (Test-Path -LiteralPath $archivePath -PathType Leaf)) {
    throw 'The prepared local package or catalog is missing.'
}
$cliDigest = 'sha256:' + (Get-FileHash -LiteralPath $cliPath -Algorithm SHA256).Hash.ToLowerInvariant()
$archiveDigest = 'sha256:' + (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($cliDigest -cne [string]$environment.cli.digest -or $archiveDigest -cne [string]$environment.adapter.digest) {
    throw 'The prepared CLI or adapter archive has changed.'
}
foreach ($consumerName in @($environment.consumers)) {
    $consumer = Join-Path $review ([string]$consumerName)
    if (-not (Test-Path -LiteralPath $consumer -PathType Container) -or
        @(Get-ChildItem -LiteralPath $consumer -Force).Count -ne 0) {
        throw "Consumer workspace '$consumerName' is missing or no longer empty."
    }
}

$port = [int]$environment.catalog.port
$probe = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $port)
try { $probe.Start() }
catch { throw "Catalog port $port is in use. Prepare a new seed with -CatalogPort set to a free port." }
finally { $probe.Stop() }

$python = $null
try {
    $uv = @(Get-Command uv -CommandType Application -All -ErrorAction Stop)[0]
    $uvOutput = @(& $uv.Source python find 2>$null)
    if ($LASTEXITCODE -eq 0 -and $uvOutput.Count -gt 0 -and
        (Test-Path -LiteralPath ([string]$uvOutput[-1]) -PathType Leaf)) {
        $python = (Resolve-Path -LiteralPath ([string]$uvOutput[-1])).Path
    }
}
catch {
    $python = $null
}
if (-not $python) {
    foreach ($commandName in @('python', 'python3')) {
        try {
            $candidate = @(Get-Command $commandName -CommandType Application -All -ErrorAction Stop)[0]
            if ($candidate) {
                $python = $candidate.Source
                break
            }
        }
        catch {
            continue
        }
    }
}
if (-not $python) {
    throw 'No Python interpreter is available. Install Spec Kit with uv or place python/python3 on PATH.'
}

Write-Host "Serving the exact local extension catalog at $($environment.catalog.catalogUrl)"
Write-Host 'Keep this terminal open during all three review journeys. Press Ctrl+C after the final journey.'
& $python -m http.server $port --bind 127.0.0.1 --directory $catalogRoot
if ($LASTEXITCODE -ne 0) { throw 'The local extension catalog server stopped unexpectedly.' }
