Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-ProgramKitSha256 {
    param([Parameter(Mandatory = $true)][string] $Path)

    return "sha256:$((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant())"
}

function Assert-ProgramKitExactProperties {
    param(
        [Parameter(Mandatory = $true)][psobject] $Value,
        [Parameter(Mandatory = $true)][string[]] $Expected,
        [Parameter(Mandatory = $true)][string] $Path
    )

    $actual = @($Value.PSObject.Properties.Name | Sort-Object)
    $expectedSorted = @($Expected | Sort-Object)
    if (($actual -join "`n") -cne ($expectedSorted -join "`n")) {
        throw "Unexpected properties at ${Path}: $($actual -join ', ')."
    }
}

function Assert-ProgramKitSha256 {
    param(
        [Parameter(Mandatory = $true)][string] $Value,
        [Parameter(Mandatory = $true)][string] $Path
    )

    if ($Value -cnotmatch '^sha256:[0-9a-f]{64}$') {
        throw "Invalid SHA-256 digest at ${Path}: $Value"
    }
}

function Get-ProgramKitCanonicalPackageSet {
    param(
        [Parameter(Mandatory = $true)][string] $CanonicalBuildRoot,
        [Parameter(Mandatory = $true)][string] $RepositoryRoot,
        [Parameter(Mandatory = $true)][bool] $ProvenanceExpected
    )

    $root = [IO.Path]::GetFullPath($CanonicalBuildRoot)
    $repository = [IO.Path]::GetFullPath($RepositoryRoot)
    if (-not (Test-Path -LiteralPath $root -PathType Container)) {
        throw "The canonical-build root is absent: $root"
    }

    $expectedEntries = @(
        'feed',
        'package-manifest.json',
        'SHA256SUMS')
    if ($ProvenanceExpected) {
        $expectedEntries += 'canonical-build-provenance.json'
    }

    $actualEntries = @(
        Get-ChildItem -LiteralPath $root -Force |
            ForEach-Object { $_.Name } |
            Sort-Object)
    $expectedEntries = @($expectedEntries | Sort-Object)
    if (($actualEntries -join "`n") -cne
        ($expectedEntries -join "`n")) {
        throw 'The canonical-build root has missing or unexpected entries.'
    }

    $sourceManifestPath = Join-Path `
        $repository `
        'build/program-kit-release-packages.json'
    $packageManifestPath = Join-Path $root 'package-manifest.json'
    $checksumPath = Join-Path $root 'SHA256SUMS'
    $feedPath = Join-Path $root 'feed'
    if (-not (Test-Path -LiteralPath $sourceManifestPath -PathType Leaf) -or
        -not (Test-Path -LiteralPath $packageManifestPath -PathType Leaf) -or
        -not (Test-Path -LiteralPath $checksumPath -PathType Leaf) -or
        -not (Test-Path -LiteralPath $feedPath -PathType Container)) {
        throw 'The canonical package set is incomplete.'
    }

    $sourceManifest = Get-Content `
        -Raw `
        -LiteralPath $sourceManifestPath |
        ConvertFrom-Json
    Assert-ProgramKitExactProperties `
        -Value $sourceManifest `
        -Expected @('manifestVersion', 'packages', 'productVersion') `
        -Path '/sourcePackageManifest'
    $packageManifest = Get-Content `
        -Raw `
        -LiteralPath $packageManifestPath |
        ConvertFrom-Json
    Assert-ProgramKitExactProperties `
        -Value $packageManifest `
        -Expected @(
            'manifestVersion',
            'packages',
            'productVersion',
            'sourcePackageManifestSha256') `
        -Path '/packageManifest'

    $sourceManifestDigest = Get-ProgramKitSha256 -Path $sourceManifestPath
    if ($sourceManifest.manifestVersion -cne '0.1.0-alpha.1' -or
        $packageManifest.manifestVersion -cne '0.1.0-alpha.1' -or
        $packageManifest.productVersion -cne $sourceManifest.productVersion -or
        $packageManifest.sourcePackageManifestSha256 -cne
            $sourceManifestDigest) {
        throw 'The source and emitted package manifests are incompatible.'
    }

    $selected = @($sourceManifest.packages)
    $packages = @($packageManifest.packages)
    if ($packages.Count -ne $selected.Count -or $packages.Count -eq 0) {
        throw 'The package evidence count differs from the canonical selection.'
    }

    $selectedById = @{}
    foreach ($selection in $selected) {
        Assert-ProgramKitExactProperties `
            -Value $selection `
            -Expected @(
                'coordinatedVersionRequired',
                'firstPartyDependencies',
                'packageId',
                'projectPath',
                'role') `
            -Path "/sourcePackageManifest/packages/$(
                $selection.packageId)"
        $selectionId = [string] $selection.packageId
        if ([string]::IsNullOrWhiteSpace($selectionId) -or
            -not [bool] $selection.coordinatedVersionRequired -or
            $selectedById.ContainsKey($selectionId)) {
            throw 'The canonical package selection is invalid or duplicated.'
        }

        $selectedById[$selectionId] = $selection
    }

    $expectedFiles = @()
    $checksumRows = @()
    foreach ($package in $packages) {
        Assert-ProgramKitExactProperties `
            -Value $package `
            -Expected @(
                'filename',
                'firstPartyDependencies',
                'packageId',
                'role',
                'sha256',
                'size',
                'version') `
            -Path "/packageManifest/packages/$($package.packageId)"
        Assert-ProgramKitSha256 `
            -Value ([string] $package.sha256) `
            -Path "/packageManifest/packages/$($package.packageId)/sha256"
        $packageId = [string] $package.packageId
        if (-not $selectedById.ContainsKey($packageId)) {
            throw "Package selection evidence drifted for $packageId."
        }

        $selection = $selectedById[$packageId]
        if (
            $package.version -cne $sourceManifest.productVersion -or
            $package.role -cne $selection.role) {
            throw "Package selection evidence drifted for $packageId."
        }

        $dependencyEvidence = @($package.firstPartyDependencies)
        foreach ($dependency in $dependencyEvidence) {
            Assert-ProgramKitExactProperties `
                -Value $dependency `
                -Expected @('packageId', 'versionRange') `
                -Path "/packageManifest/packages/$packageId/dependencies"
            $dependencyVersion = [string] $dependency.versionRange
            if ($dependencyVersion -cne $sourceManifest.productVersion -and
                $dependencyVersion -cne "[$(
                    $sourceManifest.productVersion), )" -and
                $dependencyVersion -cne "[$(
                    $sourceManifest.productVersion)]") {
                throw "Dependency version evidence drifted for $packageId."
            }
        }

        $actualDependencies = @(
            $dependencyEvidence |
                ForEach-Object { [string] $_.packageId } |
                Sort-Object)
        $expectedDependencies = if (
            $package.role -ceq 'tool' -or
            $package.role -ceq 'build-integration') {
            @()
        }
        else {
            @(
                $selection.firstPartyDependencies |
                    ForEach-Object { [string] $_ } |
                    Sort-Object)
        }
        if (($actualDependencies -join "`n") -cne
            ($expectedDependencies -join "`n")) {
            throw "Dependency selection evidence drifted for $packageId."
        }

        $expectedFilename = "$(
            $package.packageId).$($package.version).nupkg"
        if ($package.filename -cne $expectedFilename -or
            [IO.Path]::GetFileName([string] $package.filename) -cne
                $package.filename) {
            throw "Package filename evidence drifted for $($package.packageId)."
        }

        $archivePath = Join-Path $feedPath ([string] $package.filename)
        if (-not (Test-Path -LiteralPath $archivePath -PathType Leaf)) {
            throw "Package bytes are absent: $($package.filename)"
        }

        $file = Get-Item -LiteralPath $archivePath
        if ($file.Length -ne [long] $package.size -or
            (Get-ProgramKitSha256 -Path $archivePath) -cne
                $package.sha256) {
            throw "Package evidence does not match exact bytes: $($package.filename)"
        }

        $expectedFiles += [string] $package.filename
        $checksumRows += "$(
            ([string] $package.sha256).Substring(7)
        )  feed/$($package.filename)"
    }

    $actualFiles = @(
        Get-ChildItem -LiteralPath $feedPath -File |
            ForEach-Object { $_.Name } |
            Sort-Object)
    $expectedFiles = @($expectedFiles | Sort-Object)
    if (($actualFiles -join "`n") -cne ($expectedFiles -join "`n")) {
        throw 'The feed has missing or extra package files.'
    }

    $packageManifestDigest = Get-ProgramKitSha256 -Path $packageManifestPath
    $checksumRows += "$(
        $packageManifestDigest.Substring(7)
    )  package-manifest.json"
    $expectedChecksums = "$(
        ($checksumRows | Sort-Object) -join "`n"
    )`n"
    $actualChecksums = [IO.File]::ReadAllText($checksumPath)
    if ($actualChecksums -cne $expectedChecksums) {
        throw 'SHA256SUMS differs from the canonical package evidence.'
    }

    return [pscustomobject]@{
        Root = $root
        ProductVersion = [string] $packageManifest.productVersion
        SourceManifestDigest = $sourceManifestDigest
        PackageManifestDigest = $packageManifestDigest
        ChecksumDigest = Get-ProgramKitSha256 -Path $checksumPath
        Packages = $packages
    }
}

function Write-ProgramKitCanonicalBuildProvenance {
    param(
        [Parameter(Mandatory = $true)][string] $CanonicalBuildRoot,
        [Parameter(Mandatory = $true)][string] $RepositoryRoot,
        [Parameter(Mandatory = $true)][string] $Repository,
        [Parameter(Mandatory = $true)][string] $Event,
        [Parameter(Mandatory = $true)][string] $Branch,
        [Parameter(Mandatory = $true)][string] $SourceCommit,
        [Parameter(Mandatory = $true)][string] $WorkflowIdentity,
        [Parameter(Mandatory = $true)][string] $WorkflowRevision,
        [Parameter(Mandatory = $true)][string] $RunId,
        [Parameter(Mandatory = $true)][string] $ArtifactName,
        [Parameter(Mandatory = $true)][string] $ProfileIdentity,
        [Parameter(Mandatory = $true)][string] $ProfileVersion,
        [Parameter(Mandatory = $true)][string] $ProfileSha256
    )

    Assert-ProgramKitCanonicalMetadata `
        -Repository $Repository `
        -Event $Event `
        -Branch $Branch `
        -SourceCommit $SourceCommit `
        -WorkflowIdentity $WorkflowIdentity `
        -WorkflowRevision $WorkflowRevision `
        -RunId $RunId `
        -ArtifactName $ArtifactName `
        -ProfileIdentity $ProfileIdentity `
        -ProfileVersion $ProfileVersion `
        -ProfileSha256 $ProfileSha256
    $packageSet = Get-ProgramKitCanonicalPackageSet `
        -CanonicalBuildRoot $CanonicalBuildRoot `
        -RepositoryRoot $RepositoryRoot `
        -ProvenanceExpected $false
    $provenancePath = Join-Path `
        $packageSet.Root `
        'canonical-build-provenance.json'
    if (Test-Path -LiteralPath $provenancePath) {
        throw "Canonical-build provenance already exists: $provenancePath"
    }

    $provenance = [ordered]@{
        provenanceVersion = '0.1.0-alpha.1'
        repository = $Repository
        event = $Event
        branch = $Branch
        sourceCommit = $SourceCommit
        workflow = [ordered]@{
            identity = $WorkflowIdentity
            revision = $WorkflowRevision
            runId = $RunId
        }
        integrationProfile = [ordered]@{
            identity = $ProfileIdentity
            version = $ProfileVersion
            digest = $ProfileSha256
        }
        packageSelection = [ordered]@{
            sourceManifestPath = 'build/program-kit-release-packages.json'
            sourceManifestSha256 = $packageSet.SourceManifestDigest
            packageManifestPath = 'package-manifest.json'
            packageManifestSha256 = $packageSet.PackageManifestDigest
            checksumPath = 'SHA256SUMS'
            checksumSha256 = $packageSet.ChecksumDigest
        }
        artifact = [ordered]@{
            name = $ArtifactName
        }
        productVersion = $packageSet.ProductVersion
        packages = @($packageSet.Packages)
    }
    $json = $provenance | ConvertTo-Json -Depth 12
    [IO.File]::WriteAllText(
        $provenancePath,
        "$json`n",
        [Text.UTF8Encoding]::new($false))

    Test-ProgramKitCanonicalBuildProvenance `
        -CanonicalBuildRoot $CanonicalBuildRoot `
        -RepositoryRoot $RepositoryRoot `
        -Repository $Repository `
        -Event $Event `
        -Branch $Branch `
        -SourceCommit $SourceCommit `
        -WorkflowIdentity $WorkflowIdentity `
        -WorkflowRevision $WorkflowRevision `
        -RunId $RunId `
        -ArtifactName $ArtifactName `
        -ProfileIdentity $ProfileIdentity `
        -ProfileVersion $ProfileVersion `
        -ProfileSha256 $ProfileSha256
}

function Test-ProgramKitCanonicalBuildProvenance {
    param(
        [Parameter(Mandatory = $true)][string] $CanonicalBuildRoot,
        [Parameter(Mandatory = $true)][string] $RepositoryRoot,
        [Parameter(Mandatory = $true)][string] $Repository,
        [Parameter(Mandatory = $true)][string] $Event,
        [Parameter(Mandatory = $true)][string] $Branch,
        [Parameter(Mandatory = $true)][string] $SourceCommit,
        [Parameter(Mandatory = $true)][string] $WorkflowIdentity,
        [Parameter(Mandatory = $true)][string] $WorkflowRevision,
        [Parameter(Mandatory = $true)][string] $RunId,
        [Parameter(Mandatory = $true)][string] $ArtifactName,
        [Parameter(Mandatory = $true)][string] $ProfileIdentity,
        [Parameter(Mandatory = $true)][string] $ProfileVersion,
        [Parameter(Mandatory = $true)][string] $ProfileSha256
    )

    Assert-ProgramKitCanonicalMetadata `
        -Repository $Repository `
        -Event $Event `
        -Branch $Branch `
        -SourceCommit $SourceCommit `
        -WorkflowIdentity $WorkflowIdentity `
        -WorkflowRevision $WorkflowRevision `
        -RunId $RunId `
        -ArtifactName $ArtifactName `
        -ProfileIdentity $ProfileIdentity `
        -ProfileVersion $ProfileVersion `
        -ProfileSha256 $ProfileSha256
    $packageSet = Get-ProgramKitCanonicalPackageSet `
        -CanonicalBuildRoot $CanonicalBuildRoot `
        -RepositoryRoot $RepositoryRoot `
        -ProvenanceExpected $true
    $provenancePath = Join-Path `
        $packageSet.Root `
        'canonical-build-provenance.json'
    $provenance = Get-Content `
        -Raw `
        -LiteralPath $provenancePath |
        ConvertFrom-Json
    Assert-ProgramKitExactProperties `
        -Value $provenance `
        -Expected @(
            'artifact',
            'branch',
            'event',
            'integrationProfile',
            'packageSelection',
            'packages',
            'productVersion',
            'provenanceVersion',
            'repository',
            'sourceCommit',
            'workflow') `
        -Path '/provenance'
    Assert-ProgramKitExactProperties `
        -Value $provenance.workflow `
        -Expected @('identity', 'revision', 'runId') `
        -Path '/provenance/workflow'
    Assert-ProgramKitExactProperties `
        -Value $provenance.integrationProfile `
        -Expected @('digest', 'identity', 'version') `
        -Path '/provenance/integrationProfile'
    Assert-ProgramKitExactProperties `
        -Value $provenance.packageSelection `
        -Expected @(
            'checksumPath',
            'checksumSha256',
            'packageManifestPath',
            'packageManifestSha256',
            'sourceManifestPath',
            'sourceManifestSha256') `
        -Path '/provenance/packageSelection'
    Assert-ProgramKitExactProperties `
        -Value $provenance.artifact `
        -Expected @('name') `
        -Path '/provenance/artifact'

    $matches = (
        $provenance.provenanceVersion -ceq '0.1.0-alpha.1' -and
        $provenance.repository -ceq $Repository -and
        $provenance.event -ceq $Event -and
        $provenance.branch -ceq $Branch -and
        $provenance.sourceCommit -ceq $SourceCommit -and
        $provenance.workflow.identity -ceq $WorkflowIdentity -and
        $provenance.workflow.revision -ceq $WorkflowRevision -and
        $provenance.workflow.runId -ceq $RunId -and
        $provenance.integrationProfile.identity -ceq $ProfileIdentity -and
        $provenance.integrationProfile.version -ceq $ProfileVersion -and
        $provenance.integrationProfile.digest -ceq $ProfileSha256 -and
        $provenance.artifact.name -ceq $ArtifactName -and
        $provenance.productVersion -ceq $packageSet.ProductVersion -and
        $provenance.packageSelection.sourceManifestPath -ceq
            'build/program-kit-release-packages.json' -and
        $provenance.packageSelection.sourceManifestSha256 -ceq
            $packageSet.SourceManifestDigest -and
        $provenance.packageSelection.packageManifestPath -ceq
            'package-manifest.json' -and
        $provenance.packageSelection.packageManifestSha256 -ceq
            $packageSet.PackageManifestDigest -and
        $provenance.packageSelection.checksumPath -ceq 'SHA256SUMS' -and
        $provenance.packageSelection.checksumSha256 -ceq
            $packageSet.ChecksumDigest)
    if (-not $matches) {
        throw 'Canonical-build provenance differs from expected execution evidence.'
    }

    $expectedPackages = @(
        $packageSet.Packages | ConvertTo-Json -Depth 8 -Compress)
    $actualPackages = @(
        $provenance.packages | ConvertTo-Json -Depth 8 -Compress)
    if (($actualPackages -join "`n") -cne ($expectedPackages -join "`n")) {
        throw 'Canonical-build provenance package evidence drifted.'
    }

    $result = [ordered]@{
        provenanceSha256 = Get-ProgramKitSha256 -Path $provenancePath
        productVersion = $packageSet.ProductVersion
        packageCount = @($packageSet.Packages).Count
        artifactName = $ArtifactName
        sourceCommit = $SourceCommit
        runId = $RunId
    }
    $result | ConvertTo-Json -Depth 4 -Compress
}

function Assert-ProgramKitCanonicalMetadata {
    param(
        [Parameter(Mandatory = $true)][string] $Repository,
        [Parameter(Mandatory = $true)][string] $Event,
        [Parameter(Mandatory = $true)][string] $Branch,
        [Parameter(Mandatory = $true)][string] $SourceCommit,
        [Parameter(Mandatory = $true)][string] $WorkflowIdentity,
        [Parameter(Mandatory = $true)][string] $WorkflowRevision,
        [Parameter(Mandatory = $true)][string] $RunId,
        [Parameter(Mandatory = $true)][string] $ArtifactName,
        [Parameter(Mandatory = $true)][string] $ProfileIdentity,
        [Parameter(Mandatory = $true)][string] $ProfileVersion,
        [Parameter(Mandatory = $true)][string] $ProfileSha256
    )

    if ($Repository -cnotmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$' -or
        $Event -cne 'push' -or
        $Branch -cne 'refs/heads/main' -or
        $SourceCommit -cnotmatch '^[0-9a-f]{40}$' -or
        $WorkflowRevision -cnotmatch '^[0-9a-f]{40}$' -or
        $RunId -cnotmatch '^[1-9][0-9]*$' -or
        [string]::IsNullOrWhiteSpace($WorkflowIdentity) -or
        [string]::IsNullOrWhiteSpace($ArtifactName) -or
        [string]::IsNullOrWhiteSpace($ProfileIdentity) -or
        [string]::IsNullOrWhiteSpace($ProfileVersion)) {
        throw 'Canonical-build execution metadata is incomplete or ineligible.'
    }

    Assert-ProgramKitSha256 `
        -Value $ProfileSha256 `
        -Path '/integrationProfile/digest'
}

Export-ModuleMember `
    -Function Write-ProgramKitCanonicalBuildProvenance, `
        Test-ProgramKitCanonicalBuildProvenance
