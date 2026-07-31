param(
    [string] $ExtensionRoot = $PSScriptRoot
)

$ErrorActionPreference = 'Stop'
$markdownPath = Join-Path $ExtensionRoot 'implementation-plan.md'
$designPath = Join-Path $ExtensionRoot 'architecture-design.json'
$outputPath = Join-Path $ExtensionRoot 'implementation-plan.json'
$markdown = [IO.File]::ReadAllText($markdownPath)
$designDigest = (
    Get-FileHash -Algorithm SHA256 -LiteralPath $designPath
).Hash.ToLowerInvariant()

function Normalize-Block([string] $value) {
    return [regex]::Replace($value, '\s+', ' ').Trim()
}

function Read-Block(
    [string] $section,
    [string] $startMarker,
    [string] $endMarker
) {
    $start = $section.IndexOf($startMarker, [StringComparison]::Ordinal)
    if ($start -lt 0) {
        throw "Missing marker '$startMarker'."
    }

    $start += $startMarker.Length
    if ([string]::IsNullOrEmpty($endMarker)) {
        $end = $section.Length
    }
    else {
        $end = $section.IndexOf(
            $endMarker,
            $start,
            [StringComparison]::Ordinal)
        if ($end -lt 0) {
            throw "Missing marker '$endMarker'."
        }
    }

    return Normalize-Block $section.Substring($start, $end - $start)
}

function Expand-RequirementIds([string] $value) {
    $plain = $value.Replace('`', '')
    $ids = [Collections.Generic.HashSet[string]]::new(
        [StringComparer]::Ordinal)
    foreach ($match in [regex]::Matches(
        $plain,
        'R(?<start>\d{3})\s*(?:-|\u2013)\s*R(?<end>\d{3})')) {
        $start = [int]$match.Groups['start'].Value
        $end = [int]$match.Groups['end'].Value
        foreach ($number in $start..$end) {
            [void]$ids.Add(('PKCG-R{0:D3}' -f $number))
        }
    }

    foreach ($match in [regex]::Matches($plain, 'R(?<value>\d{3})')) {
        [void]$ids.Add('PKCG-R' + $match.Groups['value'].Value)
    }

    return @($ids | Sort-Object)
}

$designReference = [ordered]@{
    identity = 'pkid:design:program-kit:reusable-csharp-build-gates'
    version = '1.0.0'
    digest = 'sha256:' + $designDigest
}

$requirementMatches = [regex]::Matches(
    $markdown,
    '(?m)^\|\s*`(?<id>PKCG-R\d{3})`\s*\|\s*(?<outcome>.+?)\s*\|$')
$requirements = [ordered]@{}
foreach ($match in $requirementMatches) {
    $requirements[$match.Groups['id'].Value] =
        $match.Groups['outcome'].Value.Trim()
}
if ($requirements.Count -ne 32) {
    throw "Expected 32 requirements; observed $($requirements.Count)."
}

$traceWorkUnits = @{}
$traceMatches = [regex]::Matches(
    $markdown,
    '(?m)^\|\s*`(?<workUnit>PKCG-W\d{3})`\s*\|\s*(?<requirements>R.+?)\s*\|$')
foreach ($match in $traceMatches) {
    $workUnitId = $match.Groups['workUnit'].Value
    foreach ($requirementId in Expand-RequirementIds(
        $match.Groups['requirements'].Value)) {
        if (-not $traceWorkUnits.ContainsKey($requirementId)) {
            $traceWorkUnits[$requirementId] =
                [Collections.Generic.List[string]]::new()
        }
        $traceWorkUnits[$requirementId].Add($workUnitId)
    }
}

$headingMatches = [regex]::Matches(
    $markdown,
    '(?m)^### `(?<id>PKCG-W\d{3})`[^\r\n]*$')
$workUnits = [Collections.Generic.List[object]]::new()
for ($index = 0; $index -lt $headingMatches.Count; $index++) {
    $heading = $headingMatches[$index]
    $sectionStart = $heading.Index + $heading.Length
    $sectionEnd = if ($index + 1 -lt $headingMatches.Count) {
        $headingMatches[$index + 1].Index
    }
    else {
        $markdown.IndexOf(
            '## 4. Requirement trace',
            $sectionStart,
            [StringComparison]::Ordinal)
    }
    if ($sectionEnd -lt 0) {
        throw 'Could not locate the end of the final work unit.'
    }

    $section = $markdown.Substring(
        $sectionStart,
        $sectionEnd - $sectionStart)
    $workUnitId = $heading.Groups['id'].Value
    $dependsOnText = Read-Block `
        $section `
        '**Depends on:**' `
        '**Allowed edits:**'
    $dependsOn = @(
        [regex]::Matches($dependsOnText, 'PKCG-W\d{3}') |
            ForEach-Object { $_.Value } |
            Sort-Object -Unique
    )
    $requiredOutcome = Read-Block `
        $section `
        '**Required outcomes:**' `
        '**Verification:**'
    $allowedEdits = Read-Block `
        $section `
        '**Allowed edits:**' `
        '**Required outcomes:**'
    $verification = Read-Block `
        $section `
        '**Verification:**' `
        '**Stop conditions:**'
    $stopConditions = Read-Block `
        $section `
        '**Stop conditions:**' `
        ''
    $sequence = [int]$workUnitId.Substring($workUnitId.Length - 3)

    $workUnits.Add([ordered]@{
        workUnitId = $workUnitId
        requiredOutcome = $requiredOutcome
        sequence = $sequence
        parallelGroupId = $null
        dependsOn = $dependsOn
        inputs = @($designReference)
        outputs = @(
            [ordered]@{
                identity = (
                    'pkid:plan-output:program-kit:' +
                    $workUnitId.ToLowerInvariant())
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
if ($workUnits.Count -ne 11) {
    throw "Expected 11 work units; observed $($workUnits.Count)."
}

$trace = [Collections.Generic.List[object]]::new()
foreach ($entry in $requirements.GetEnumerator()) {
    if (-not $traceWorkUnits.ContainsKey($entry.Key)) {
        throw "Requirement '$($entry.Key)' has no work-unit trace."
    }

    $trace.Add([ordered]@{
        requirementId = $entry.Key
        ownerId = 'pkid:domain:program-kit:toolkit'
        contractOrArtifact = $designReference
        workUnitIds = @($traceWorkUnits[$entry.Key] | Sort-Object -Unique)
        implementationOutcome = $entry.Value
        dependencyOrExtensionImpact = @()
        tests = @()
        evidence = @()
        observableAcceptanceOutcome = $entry.Value
    })
}

$plan = [ordered]@{
    design = $designReference
    ownerId = 'pkid:domain:program-kit:toolkit'
    state = 'ready-for-human-decision'
    requirementIds = @($requirements.Keys)
    workUnits = @($workUnits)
    parallelGroups = @()
    trace = @($trace)
    unresolvedDecisions = @()
}

$json = $plan | ConvertTo-Json -Depth 100
$json = $json.Replace("`r`n", "`n") + "`n"
[IO.File]::WriteAllText(
    $outputPath,
    $json,
    [Text.UTF8Encoding]::new($false))
