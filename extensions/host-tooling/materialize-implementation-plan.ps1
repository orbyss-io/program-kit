[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$extensionRoot = $PSScriptRoot
$markdownPath = Join-Path $extensionRoot 'implementation-plan.md'
$outputPath = Join-Path $extensionRoot 'implementation-plan.json'
$approvedMarkdownDigest = '8144a67d5d919211f87a2d30a4d7a870f299c126e138986c6f079e133734f9a5'
$actualMarkdownDigest = (Get-FileHash -Algorithm SHA256 -LiteralPath $markdownPath).Hash.ToLowerInvariant()
if ($actualMarkdownDigest -ne $approvedMarkdownDigest) {
    throw "The approved Markdown plan digest changed: $actualMarkdownDigest"
}

$design = [ordered]@{
    identity = 'pkid:design:program-kit:host-tooling'
    version = '1.3.0'
    digest = 'sha256:a9ad015470f3996ea09811d57007ec4ab90e3b2cbff91245e625bfdd82ad0d57'
}
$ownerId = 'pkid:domain:program-kit:toolkit'
$lines = [IO.File]::ReadAllLines($markdownPath)

function Normalize-Lines {
    param([string[]]$Value)

    return (($Value | ForEach-Object { $_.Trim() }) -join ' ' -replace '\s+', ' ').Trim()
}

function Get-BlockValue {
    param(
        [string[]]$Section,
        [string]$StartMarker,
        [string[]]$EndMarkers
    )

    $start = -1
    for ($index = 0; $index -lt $Section.Length; $index++) {
        if ($Section[$index].StartsWith($StartMarker, [StringComparison]::Ordinal)) {
            $start = $index
            break
        }
    }
    if ($start -lt 0) {
        return ''
    }

    $values = [Collections.Generic.List[string]]::new()
    $values.Add($Section[$start].Substring($StartMarker.Length))
    for ($index = $start + 1; $index -lt $Section.Length; $index++) {
        $line = $Section[$index]
        if ($EndMarkers | Where-Object { $line.StartsWith($_, [StringComparison]::Ordinal) }) {
            break
        }
        $values.Add($line)
    }

    return Normalize-Lines $values.ToArray()
}

function Expand-Identifiers {
    param(
        [string]$Text,
        [string]$Kind
    )

    $plain = $Text.Replace('`', '')
    $values = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($range in [regex]::Matches($plain, "$Kind(?<start>\d{3})\s*[–-]\s*$Kind(?<end>\d{3})")) {
        $start = [int]$range.Groups['start'].Value
        $end = [int]$range.Groups['end'].Value
        foreach ($number in $start..$end) {
            $null = $values.Add(('PKHT-{0}{1:D3}' -f $Kind, $number))
        }
    }
    foreach ($match in [regex]::Matches($plain, "$Kind(?<value>\d{3})")) {
        $null = $values.Add(('PKHT-{0}{1}' -f $Kind, $match.Groups['value'].Value))
    }

    return @($values | Sort-Object)
}

$requirementOutcomes = [ordered]@{}
foreach ($line in $lines) {
    if ($line -match '^\|\s*`(?<id>PKHT-R\d{3})`\s*\|\s*(?<outcome>.+?)\s*\|$') {
        $requirementOutcomes[$Matches.id] = $Matches.outcome
    }
}
if ($requirementOutcomes.Count -ne 29) {
    throw "Expected 29 approved requirements, found $($requirementOutcomes.Count)."
}

$headings = [Collections.Generic.List[object]]::new()
for ($index = 0; $index -lt $lines.Length; $index++) {
    if ($lines[$index] -match '^### `(?<id>PKHT-W\d{3})`') {
        $headings.Add([pscustomobject]@{ Id = $Matches.id; Index = $index })
    }
}
if ($headings.Count -ne 16) {
    throw "Expected 16 approved work units, found $($headings.Count)."
}

$workUnits = [Collections.Generic.List[object]]::new()
$requirementWorkUnits = @{}
for ($headingIndex = 0; $headingIndex -lt $headings.Count; $headingIndex++) {
    $heading = $headings[$headingIndex]
    $end = if ($headingIndex + 1 -lt $headings.Count) {
        $headings[$headingIndex + 1].Index
    } else {
        $lines.Length
    }
    $section = @($lines[($heading.Index + 1)..($end - 1)])
    $requirementText = Get-BlockValue $section '**Requirements:**' @('**Depends on:**', '**Allowed edits:**')
    $requirements = @(Expand-Identifiers $requirementText 'R')
    $dependencyText = Get-BlockValue $section '**Depends on:**' @('**Allowed edits:**')
    $dependsOn = @(Expand-Identifiers $dependencyText 'W')
    $allowedEdits = Get-BlockValue $section '**Allowed edits:**' @('**Required outcomes:**')
    $requiredOutcome = Get-BlockValue $section '**Required outcomes:**' @('**Verification:**')
    $verification = Get-BlockValue $section '**Verification:**' @('**Stop conditions:**')
    $stopConditions = Get-BlockValue $section '**Stop conditions:**' @()
    if ([string]::IsNullOrWhiteSpace($requiredOutcome) -or
        [string]::IsNullOrWhiteSpace($allowedEdits) -or
        [string]::IsNullOrWhiteSpace($verification) -or
        [string]::IsNullOrWhiteSpace($stopConditions)) {
        throw "Work unit $($heading.Id) has an incomplete approved projection."
    }

    foreach ($requirement in $requirements) {
        if (-not $requirementWorkUnits.ContainsKey($requirement)) {
            $requirementWorkUnits[$requirement] = [Collections.Generic.List[string]]::new()
        }
        $requirementWorkUnits[$requirement].Add($heading.Id)
    }

    $sequence = [int]$heading.Id.Substring($heading.Id.Length - 3)
    $workUnits.Add([ordered]@{
        workUnitId = $heading.Id
        requiredOutcome = $requiredOutcome
        sequence = $sequence
        parallelGroupId = $null
        dependsOn = @($dependsOn)
        inputs = @($design)
        outputs = @(
            [ordered]@{
                identity = "pkid:plan-output:program-kit:$($heading.Id.ToLowerInvariant())"
                version = '1.0.0'
                state = 'prospective'
                integrityDigest = $null
            }
        )
        allowedEdits = @($allowedEdits)
        sourceDependencies = @()
        externalDependencies = @()
        migrations = @()
        compatibility = @()
        stopConditions = @($stopConditions)
        verification = @(
            [ordered]@{
                executable = 'dotnet'
                arguments = @('test', 'ProgramKit.sln', '--no-restore')
                workingDirectory = 'program-kit'
                expectedObservation = $verification
            }
        )
        selectedTests = @()
    })
}

$trace = [Collections.Generic.List[object]]::new()
foreach ($requirement in $requirementOutcomes.Keys) {
    if (-not $requirementWorkUnits.ContainsKey($requirement)) {
        throw "Approved requirement $requirement is not assigned to a work unit."
    }
    $outcome = $requirementOutcomes[$requirement]
    $trace.Add([ordered]@{
        requirementId = $requirement
        ownerId = $ownerId
        contractOrArtifact = $design
        workUnitIds = @($requirementWorkUnits[$requirement] | Sort-Object -Unique)
        implementationOutcome = $outcome
        dependencyOrExtensionImpact = @()
        tests = @()
        evidence = @()
        observableAcceptanceOutcome = $outcome
    })
}

$plan = [ordered]@{
    design = $design
    ownerId = $ownerId
    state = 'ready-for-human-decision'
    requirementIds = @($requirementOutcomes.Keys)
    workUnits = @($workUnits)
    parallelGroups = @()
    trace = @($trace)
    unresolvedDecisions = @()
}

$json = $plan | ConvertTo-Json -Depth 20
$json = $json.Replace("`r`n", "`n")
[IO.File]::WriteAllText(
    $outputPath,
    [string]::Concat($json, "`n"),
    [Text.UTF8Encoding]::new($false))
