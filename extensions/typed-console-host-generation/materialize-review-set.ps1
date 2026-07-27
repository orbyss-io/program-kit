param(
    [string] $ExtensionRoot = $PSScriptRoot
)

$ErrorActionPreference = 'Stop'
$repositoryRoot = (Resolve-Path (Join-Path $ExtensionRoot '..\..')).Path

function Get-Digest([string] $relativePath) {
    $path = Join-Path $repositoryRoot $relativePath
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required review input does not exist: $relativePath"
    }

    return (
        Get-FileHash -Algorithm SHA256 -LiteralPath $path
    ).Hash.ToLowerInvariant()
}

function New-Reference(
    [string] $identity,
    [string] $version,
    [string] $digest
) {
    return [ordered]@{
        identity = $identity
        version = $version
        digest = 'sha256:' + $digest
    }
}

function Write-Json(
    [string] $relativePath,
    [object] $value
) {
    $path = Join-Path $ExtensionRoot $relativePath
    $json = $value | ConvertTo-Json -Depth 100
    $json = $json.Replace("`r`n", "`n") + "`n"
    [IO.File]::WriteAllText(
        $path,
        $json,
        [Text.UTF8Encoding]::new($false))
}

function New-Boundary(
    [string] $policy,
    [string[]] $guarantees,
    [string[]] $exclusions
) {
    return [ordered]@{
        ownerId = 'pkid:domain:program-kit:toolkit'
        policy = $policy
        guarantees = $guarantees
        exclusions = $exclusions
    }
}

function New-WorkUnit(
    [string] $id,
    [int] $sequence,
    [string[]] $dependsOn,
    [string] $outcome,
    [string] $allowedEdits,
    [string] $observation,
    [string] $stopCondition,
    [string] $kind,
    [object] $designReference,
    [object] $activationMatrix,
    [object] $verificationProfile
) {
    return [ordered]@{
        workUnitId = $id
        requiredOutcome = $outcome
        sequence = $sequence
        parallelGroupId = $null
        dependsOn = $dependsOn
        inputs = @($designReference)
        outputs = @(
            [ordered]@{
                identity = (
                    'pkid:plan-output:program-kit:' +
                    $id.ToLowerInvariant())
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
        stopConditions = @($stopCondition)
        verification = @(
            [ordered]@{
                executable = 'dotnet'
                arguments = @(
                    'test',
                    'ProgramKit.sln',
                    '--no-restore',
                    '--maxcpucount:1',
                    '--property:UseSharedCompilation=false')
                workingDirectory = '.'
                expectedObservation = $observation
            }
        )
        selectedTests = @()
        workUnitKind = $kind
        activationMatrix = $activationMatrix
        verificationProfile = $verificationProfile
    }
}

$sourceCommit = (
    git -C $repositoryRoot `
        -c "safe.directory=$($repositoryRoot.Replace('\', '/'))" `
        rev-parse HEAD
).Trim()
if ($LASTEXITCODE -ne 0 -or $sourceCommit -notmatch '^[0-9a-f]{40}$') {
    throw 'Could not resolve the exact Program Kit source commit.'
}

$intentDigest = Get-Digest `
    'extensions/typed-console-host-generation/design-intent.md'
$architectureMarkdownDigest = Get-Digest `
    'extensions/typed-console-host-generation/architecture-design.md'
$openConsoleSchemaDigest = Get-Digest `
    'schemas/dotnet/open-console.schema.json'
$rendererDigest = Get-Digest `
    'src/Orbyss.ProgramKit.DotNet/Generation/DotNetHostSourceRenderer.cs'
$capabilityBundleDigest = Get-Digest `
    '.agent-capabilities/capability-bundle-manifest.json'
$privateGateDigest = Get-Digest `
    'governance/csharp-source-quality-gate.md'
$activationMatrixDigest = Get-Digest 'Directory.Build.targets'
$verificationProfileDigest = Get-Digest `
    'build/Invoke-CSharpGateTestPlan.ps1'
$gateClosureDigest = Get-Digest `
    'extensions/reusable-csharp-build-gates/implementation-evidence/closure.json'
$gateDesignDigest = Get-Digest `
    'extensions/reusable-csharp-build-gates/architecture-design.json'
$architectureSchemaDigest = Get-Digest `
    'schemas/architecture/architecture-design-2.0.0.schema.json'
$planSchemaDigest = Get-Digest `
    'schemas/planning/implementation-plan-3.0.0.schema.json'
$dispositionSchemaDigest = Get-Digest `
    'schemas/architecture/static-conformance-disposition.schema.json'

$intentReference = New-Reference `
    'pkid:intent:program-kit:typed-console-host-generation' `
    '1.0.0' `
    $intentDigest
$gateDesignReference = New-Reference `
    'pkid:design:program-kit:reusable-csharp-build-gates' `
    '1.0.0' `
    $gateDesignDigest

$designBasis = [ordered]@{
    identity = 'pkid:design:program-kit:typed-console-host-generation-static-basis'
    version = '1.0.0'
    sourceCommit = $sourceCommit
    intent = $intentReference
    humanReadableArchitecture = New-Reference `
        'pkid:ai-artifact:program-kit:typed-console-host-generation-design-markdown' `
        '1.0.0' `
        $architectureMarkdownDigest
    purpose = 'Non-circular exact design basis for the human-selected static-conformance disposition carried by Architecture Design 2.0.'
}
Write-Json 'static-conformance-design-basis.json' $designBasis
$designBasisDigest = Get-Digest `
    'extensions/typed-console-host-generation/static-conformance-design-basis.json'
$designBasisReference = New-Reference `
    $designBasis.identity `
    $designBasis.version `
    $designBasisDigest

$decisionSource = [ordered]@{
    artifactId = 'pkid:decision-source:program-kit:typed-console-host-generation-static-conformance'
    artifactVersion = '1.0.0'
    designBasis = $designBasisReference
    decision = [ordered]@{
        disposition = 'reuse-existing'
        provider = 'codex'
        taskId = '019fa3b9-c0ba-7eb3-816a-12bd68a65c1a'
        statement = 'I approve.'
        conditions = @()
    }
    authorityBoundary = 'The human decision selects the existing private Program Kit C# gate for repository implementation and grants no new gate, analyzer, suppression, activation, publication, or consumer authority.'
}
Write-Json 'static-conformance-decision-source.json' $decisionSource
$decisionSourceDigest = Get-Digest `
    'extensions/typed-console-host-generation/static-conformance-decision-source.json'
$decisionSourceReference = New-Reference `
    $decisionSource.artifactId `
    $decisionSource.artifactVersion `
    $decisionSourceDigest

$privateGateReference = New-Reference `
    'pkid:policy:program-kit:csharp-source-quality-gate' `
    '1.10.0' `
    $privateGateDigest
$activationMatrixReference = New-Reference `
    'pkid:activation-matrix:program-kit:private-csharp-gate-build-spine' `
    '1.0.0' `
    $activationMatrixDigest
$verificationProfileReference = New-Reference `
    'pkid:profile:program-kit:private-csharp-gate-exhaustive' `
    '1.0.0' `
    $verificationProfileDigest
$activationEvidenceReference = New-Reference `
    'pkid:evidence:program-kit:reusable-csharp-build-gates-closure' `
    '1.0.0' `
    $gateClosureDigest

$disposition = [ordered]@{
    softwareDesign = $designBasisReference
    invariantAllocations = @(
        [ordered]@{
            identity = 'pkid:invariant:program-kit:typed-console-repository-source-conformance'
            invariant = 'Program Kit-owned handwritten and generated C# satisfies the private repository source-quality policy.'
            layer = 'roslyn-compiler'
            rationale = 'The existing private PKCS analyzer and build spine already enforce repository source structure and behavioral rules.'
        },
        [ordered]@{
            identity = 'pkid:invariant:program-kit:typed-console-project-package-direction'
            invariant = 'New projects and package references preserve the approved Program Kit dependency direction and exact package pins.'
            layer = 'project-package'
            rationale = 'The existing build spine, explicit solution graph, locked restore, and architecture conformance tests own graph enforcement.'
        },
        [ordered]@{
            identity = 'pkid:invariant:program-kit:typed-console-generated-source-contract'
            invariant = 'Generated consumer-host C# carries the selected public Program Kit generated-source contract without private analyzer leakage.'
            layer = 'roslyn-compiler'
            rationale = 'The existing public generated-source analyzer is selected only in generated consumer hosts; Program Kit implementation remains on the private gate.'
        },
        [ordered]@{
            identity = 'pkid:invariant:program-kit:typed-console-binding-integrity'
            invariant = 'Bindings, reference assemblies, generated trees, capability payloads, and process behavior conform to their exact non-static contracts.'
            layer = 'executable-test'
            rationale = 'Metadata, digest, capability, determinism, and process invariants require dedicated validators and executable conformance rather than a new C# analyzer.'
        }
    )
    disposition = 'reuse-existing'
    gateSelections = @(
        [ordered]@{
            gate = $privateGateReference
            activationMatrix = $activationMatrixReference
        }
    )
    linkedGateDesigns = @()
    rationale = 'The existing private Program Kit C# gate is compatible with this repository implementation. Public generated-host source uses the already-established public generated-source contract only through an explicit consumer-host selection. No new analyzer or gate is justified.'
    residualRisks = @(
        'The private Program Kit gate remains a repository-specific monolith with an MSBuild trust boundary.',
        'Static analysis does not prove binding metadata, generated-tree integrity, capability isolation, runtime process behavior, or human architectural quality.'
    )
    nonStaticClaims = @(
        'Executable binding, validation-order, process-exit, help, completion, determinism, tamper, repair, publication, and capability-installation behavior requires dedicated tests.',
        'Human review remains authoritative for framework fit, semantic ownership, and material design deviation.'
    )
    decisionSource = [ordered]@{
        source = $decisionSourceReference
        jsonPointer = '/decision'
    }
    emptySelectionAcceptance = $null
    blockers = @()
}
Write-Json 'static-conformance-disposition.json' $disposition
$dispositionDigest = Get-Digest `
    'extensions/typed-console-host-generation/static-conformance-disposition.json'
$dispositionReference = New-Reference `
    'pkid:static-conformance-disposition:program-kit:typed-console-host-generation' `
    '1.0.0' `
    $dispositionDigest

$selectionLock = [ordered]@{
    identity = 'pkid:selection-lock:program-kit:typed-console-host-generation-private-gate'
    version = '1.0.0'
    disposition = $dispositionReference
    gateDefinition = $privateGateReference
    activationMatrix = $activationMatrixReference
    verificationProfile = $verificationProfileReference
    activationEvidence = $activationEvidenceReference
    sourceCommit = $sourceCommit
    scope = 'Program Kit-owned implementation source only; never consumer-owned source.'
    state = 'active'
}
Write-Json 'program-kit-private-gate-selection-lock.json' $selectionLock
$selectionLockDigest = Get-Digest `
    'extensions/typed-console-host-generation/program-kit-private-gate-selection-lock.json'
$selectionLockReference = New-Reference `
    $selectionLock.identity `
    $selectionLock.version `
    $selectionLockDigest

$domains = @(
    [ordered]@{
        identity = 'pkid:domain:program-kit:open-console'
        purpose = 'Own the language-neutral Console grammar and caller-visible command contract.'
        vocabulary = @(
            [ordered]@{
                term = 'Open Console document'
                meaning = 'A language-neutral declaration of commands, logical values, cardinality, defaults, constraints, parsing, help, completion, streams, and host exit-code roles.'
                acceptedAliases = @()
            }
        )
    },
    [ordered]@{
        identity = 'pkid:domain:program-kit:dotnet-console-projection'
        purpose = 'Own verified .NET binding and deterministic Spectre Console-host generation without consumer semantics.'
        vocabulary = @(
            [ordered]@{
                term = '.NET Console binding'
                meaning = 'The explicit mapping from Open Console operations to exact CLR requests, handlers, optional validators, feature type, project, assembly, symbols, and defaults.'
                acceptedAliases = @('Console binding document')
            },
            [ordered]@{
                term = '.NET Spectre projection profile'
                meaning = 'The exact support and conformance contract mapping language-neutral Open Console shapes to one pinned Spectre version.'
                acceptedAliases = @('Spectre projection profile')
            }
        )
    },
    [ordered]@{
        identity = 'pkid:domain:program-kit:generated-output-integrity'
        purpose = 'Own host-kind-neutral sealing, verification, atomic replacement, and repair of Program Kit generated trees.'
        vocabulary = @(
            [ordered]@{
                term = 'Generated-output seal'
                meaning = 'The in-tree all-payload digest manifest plus sibling external anchor that together cover one complete generated root.'
                acceptedAliases = @('generated-host integrity seal')
            },
            [ordered]@{
                term = 'Generated-output repair'
                meaning = 'Explicitly authorized quarantine of drift followed by regeneration from authoritative consumer inputs.'
                acceptedAliases = @()
            }
        )
    },
    [ordered]@{
        identity = 'pkid:domain:program-kit:software-maintenance'
        purpose = 'Own human-started bounded incremental maintenance authority and reuse of backed completion profiles.'
        vocabulary = @(
            [ordered]@{
                term = 'Maintenance unit'
                meaning = 'One coherent architecture-compatible application change refreshed, verified, recorded, committed, and pushed as a reversible history event.'
                acceptedAliases = @()
            }
        )
    },
    [ordered]@{
        identity = 'pkid:domain:program-kit:toolkit'
        purpose = 'Own Program Kit command transport, capability packaging, repository integration, and implementation governance.'
        vocabulary = @(
            [ordered]@{
                term = 'Backed operation'
                meaning = 'One exact Program Kit command transport whose implementation is selected from an explicit finite operation set.'
                acceptedAliases = @()
            }
        )
    }
)

$components = @(
    [ordered]@{
        identity = 'pkid:component:program-kit:open-console-contract'
        ownerId = 'pkid:domain:program-kit:open-console'
        kind = 'evaluated-artifact'
        purpose = 'Provide the canonical language-neutral schema, serializer, and semantic validator.'
        providesContractIds = @()
        consumesContractIds = @()
        isActivatable = $false
        compatibilityBoundary = 'Exact schema identity, logical values, parsing, help, completion, streams, constraints, defaults, and host exit-code roles.'
    },
    [ordered]@{
        identity = 'pkid:component:program-kit:dotnet-spectre-console-generator'
        ownerId = 'pkid:domain:program-kit:dotnet-console-projection'
        kind = 'design-time-source'
        purpose = 'Compile Open Console plus an exact .NET binding into one complete deterministic executable Spectre host.'
        providesContractIds = @()
        consumesContractIds = @()
        isActivatable = $false
        compatibilityBoundary = 'Binding schema, projection profile, exact dependencies, generated layout, validation order, composition, help, completion, diagnostics, and managed exit behavior.'
    },
    [ordered]@{
        identity = 'pkid:component:program-kit:generated-output-integrity'
        ownerId = 'pkid:domain:program-kit:generated-output-integrity'
        kind = 'bridge'
        purpose = 'Seal, verify, transact, and explicitly repair generated output across host kinds.'
        providesContractIds = @()
        consumesContractIds = @()
        isActivatable = $false
        compatibilityBoundary = 'Manifest, anchor, path, digest, transaction, diagnostic, build-attestation, and publication-verification revisions.'
    },
    [ordered]@{
        identity = 'pkid:component:program-kit:maintain-software-capability'
        ownerId = 'pkid:domain:program-kit:software-maintenance'
        kind = 'feature'
        purpose = 'Route one human-started bounded compatible change through shared backed completion profiles.'
        providesContractIds = @()
        consumesContractIds = @()
        isActivatable = $true
        compatibilityBoundary = 'Stable capability identity, trigger, maintenance admission, escalation, exact Program Kit upgrade approval, completion profile binding, evidence, and provider-wrapper pointers.'
    },
    [ordered]@{
        identity = 'pkid:component:program-kit:generated-output-integrity-build'
        ownerId = 'pkid:domain:program-kit:generated-output-integrity'
        kind = 'focused-helper'
        purpose = 'Import offline generated-output verification into consumer build and publication boundaries.'
        providesContractIds = @()
        consumesContractIds = @()
        isActivatable = $false
        compatibilityBoundary = 'Build import, attestation, exact verifier package identity, and fail-closed diagnostics.'
    },
    [ordered]@{
        identity = 'pkid:component:program-kit:typed-console-command-transport'
        ownerId = 'pkid:domain:program-kit:toolkit'
        kind = 'host'
        purpose = 'Expose exact generate, refresh, and verify host operations through the frozen Program Kit command grammar.'
        providesContractIds = @()
        consumesContractIds = @()
        isActivatable = $true
        compatibilityBoundary = 'Command paths, arguments, diagnostics, and Program Kit operation exit codes.'
    }
)

$projects = @(
    [ordered]@{
        identity = 'pkid:project:program-kit:open-console'
        ownerId = 'pkid:domain:program-kit:open-console'
        projectPath = 'src/Orbyss.ProgramKit.OpenConsole/Orbyss.ProgramKit.OpenConsole.csproj'
        componentIds = @('pkid:component:program-kit:open-console-contract')
        projectReferenceIds = @()
        packageId = 'pkid:package:program-kit:open-console'
    },
    [ordered]@{
        identity = 'pkid:project:program-kit:dotnet'
        ownerId = 'pkid:domain:program-kit:dotnet-console-projection'
        projectPath = 'src/Orbyss.ProgramKit.DotNet/Orbyss.ProgramKit.DotNet.csproj'
        componentIds = @('pkid:component:program-kit:dotnet-spectre-console-generator')
        projectReferenceIds = @(
            'pkid:project:program-kit:open-console',
            'pkid:project:program-kit:generated-output-integrity')
        packageId = 'pkid:package:program-kit:dotnet'
    },
    [ordered]@{
        identity = 'pkid:project:program-kit:generated-output-integrity'
        ownerId = 'pkid:domain:program-kit:generated-output-integrity'
        projectPath = 'src/Orbyss.ProgramKit.GeneratedOutputIntegrity/Orbyss.ProgramKit.GeneratedOutputIntegrity.csproj'
        componentIds = @('pkid:component:program-kit:generated-output-integrity')
        projectReferenceIds = @()
        packageId = 'pkid:package:program-kit:generated-output-integrity'
    },
    [ordered]@{
        identity = 'pkid:project:program-kit:generated-output-integrity-build'
        ownerId = 'pkid:domain:program-kit:generated-output-integrity'
        projectPath = 'src/Orbyss.ProgramKit.GeneratedOutputIntegrity.Build/Orbyss.ProgramKit.GeneratedOutputIntegrity.Build.csproj'
        componentIds = @('pkid:component:program-kit:generated-output-integrity-build')
        projectReferenceIds = @('pkid:project:program-kit:generated-output-integrity')
        packageId = 'pkid:package:program-kit:generated-output-integrity-build'
    },
    [ordered]@{
        identity = 'pkid:project:program-kit:command-line'
        ownerId = 'pkid:domain:program-kit:toolkit'
        projectPath = 'src/Orbyss.ProgramKit.CommandLine/Orbyss.ProgramKit.CommandLine.csproj'
        componentIds = @('pkid:component:program-kit:typed-console-command-transport')
        projectReferenceIds = @(
            'pkid:project:program-kit:dotnet',
            'pkid:project:program-kit:generated-output-integrity')
        packageId = 'pkid:package:program-kit:command-line'
    },
    [ordered]@{
        identity = 'pkid:project:program-kit:capability-bundle'
        ownerId = 'pkid:domain:program-kit:software-maintenance'
        projectPath = 'src/Orbyss.ProgramKit.CapabilityBundle/Orbyss.ProgramKit.CapabilityBundle.csproj'
        componentIds = @('pkid:component:program-kit:maintain-software-capability')
        projectReferenceIds = @()
        packageId = 'pkid:package:program-kit:capability-bundle'
    }
)

$packages = @(
    [ordered]@{
        identity = 'pkid:package:program-kit:open-console'
        ownerId = 'pkid:domain:program-kit:open-console'
        version = '1.0.0'
        projectIds = @('pkid:project:program-kit:open-console')
        packageDependencyIds = @()
        publicContractIds = @()
        compatibilityBoundary = 'The language-neutral Open Console model, schema, serializer, and validator version together.'
    },
    [ordered]@{
        identity = 'pkid:package:program-kit:dotnet'
        ownerId = 'pkid:domain:program-kit:dotnet-console-projection'
        version = '1.0.0'
        projectIds = @('pkid:project:program-kit:dotnet')
        packageDependencyIds = @(
            'pkid:package:program-kit:open-console',
            'pkid:package:program-kit:generated-output-integrity')
        publicContractIds = @()
        compatibilityBoundary = 'The .NET binding and deterministic Console projection implementation version together.'
    },
    [ordered]@{
        identity = 'pkid:package:program-kit:generated-output-integrity'
        ownerId = 'pkid:domain:program-kit:generated-output-integrity'
        version = '1.0.0'
        projectIds = @('pkid:project:program-kit:generated-output-integrity')
        packageDependencyIds = @()
        publicContractIds = @()
        compatibilityBoundary = 'Generated-output manifest, anchor, verification, transaction, and repair contracts version together.'
    },
    [ordered]@{
        identity = 'pkid:package:program-kit:generated-output-integrity-build'
        ownerId = 'pkid:domain:program-kit:generated-output-integrity'
        version = '1.0.0'
        projectIds = @('pkid:project:program-kit:generated-output-integrity-build')
        packageDependencyIds = @('pkid:package:program-kit:generated-output-integrity')
        publicContractIds = @()
        compatibilityBoundary = 'The consumer build import and compile-time integrity attestation version together.'
    },
    [ordered]@{
        identity = 'pkid:package:program-kit:command-line'
        ownerId = 'pkid:domain:program-kit:toolkit'
        version = '1.0.0'
        projectIds = @('pkid:project:program-kit:command-line')
        packageDependencyIds = @(
            'pkid:package:program-kit:dotnet',
            'pkid:package:program-kit:generated-output-integrity')
        publicContractIds = @()
        compatibilityBoundary = 'The frozen Program Kit host-generation command grammar and operation transport version together.'
    },
    [ordered]@{
        identity = 'pkid:package:program-kit:capability-bundle'
        ownerId = 'pkid:domain:program-kit:software-maintenance'
        version = '1.0.0'
        projectIds = @('pkid:project:program-kit:capability-bundle')
        packageDependencyIds = @()
        publicContractIds = @()
        compatibilityBoundary = 'Exact inert capability payloads, provider adapters, bundle manifest, initialization, and drift verification version together.'
    }
)

$referenceRules = @(
    [ordered]@{
        identity = 'pkid:reference-rule:program-kit:open-console-no-dotnet-vocabulary'
        ownerId = 'pkid:domain:program-kit:open-console'
        disposition = 'forbidden'
        referencingScope = 'Open Console schema, model, validation, examples, and documentation'
        referencedScope = 'CLR, Spectre, CShells, project paths, assemblies, constructors, or dependency injection'
        ownerInput = [ordered]@{
            artifact = $intentReference
            path = 'design-intent.md#binding-authority'
        }
        rationale = 'Open Console must remain implementable by other platforms such as Node.js.'
    },
    [ordered]@{
        identity = 'pkid:reference-rule:program-kit:generated-host-one-way-consumer-reference'
        ownerId = 'pkid:domain:program-kit:dotnet-console-projection'
        disposition = 'allowed'
        referencingScope = 'Generated <Product>.Cli.Host project'
        referencedScope = 'One exact consumer-owned contracts and implementation project'
        ownerInput = [ordered]@{
            artifact = $intentReference
            path = 'design-intent.md#human-started-outcome'
        }
        rationale = 'The generated host adapts typed generated settings to consumer-owned request and behavior contracts.'
    },
    [ordered]@{
        identity = 'pkid:reference-rule:program-kit:no-consumer-generator-runtime'
        ownerId = 'pkid:domain:program-kit:dotnet-console-projection'
        disposition = 'forbidden'
        referencingScope = 'Generated host runtime and consumer project'
        referencedScope = 'Program Kit generation, Workbench, planning, capability, or command-line runtime packages'
        ownerInput = [ordered]@{
            artifact = $intentReference
            path = 'design-intent.md#accepted-dependency-and-framework-decisions'
        }
        rationale = 'Program Kit generation remains design-time only; generated applications carry only their declared host dependencies.'
    },
    [ordered]@{
        identity = 'pkid:reference-rule:program-kit:capability-authoring-inert'
        ownerId = 'pkid:domain:program-kit:software-maintenance'
        disposition = 'forbidden'
        referencingScope = 'Program Kit capability authoring, packing, building, and fixture verification'
        referencedScope = 'Authoring-workspace active provider paths or user-global provider configuration'
        ownerInput = [ordered]@{
            artifact = $intentReference
            path = 'design-intent.md#maintenance-flow'
        }
        rationale = 'Packaging a capability must never activate it in the Program Kit authoring workspace.'
    }
)

$architecture = [ordered]@{
    title = 'Program Kit typed Console host generation'
    intent = 'Generate complete deterministic typed .NET Console hosts from language-neutral Open Console and explicit verified .NET bindings, protect every generated host tree through build and publication integrity, and distribute a safe incremental maintenance flow.'
    scope = @(
        'Language-neutral Open Console ownership and versioning.',
        'Exact .NET binding, metadata inspection, Spectre projection, generated project, CShells composition, validation, help, completion, diagnostics, and exit-code behavior.',
        'Host-kind-neutral generated-output sealing, verification, atomic refresh, explicit repair, build gating, and publication verification.',
        'Shared completion profiles plus an inert installable maintain-software capability and mandatory Program Kit capability-distribution standard.',
        'Unit, schema, build, process, determinism, tamper, repair, capability, and isolated-consumer conformance.'
    )
    nonGoals = @(
        'No Program Kit package publication, release qualification, promotion, deployment, or external consumer modification.',
        'No runtime source-tree integrity check, second executable parser, dynamic completion, reflection scanning, service locator, hook, watcher, autonomous loop, or global provider write.',
        'No consumer-domain semantics, complex document-native object binding, arbitrary converter, or general semantic-validation catalog in this revision.',
        'No new C# analyzer or build gate for this extension.'
    )
    assumptions = @(
        'Spectre.Console 0.55.0, Spectre.Console.Cli 0.55.0, and CShells 0.0.28 remain exactly available to the approved implementation.',
        'The consumer can provide one deterministic compiled reference assembly before generation or explicitly authorize the approved C# build profile.',
        'The generated host root is entirely Program Kit-owned and consumer-owned source remains outside it.',
        'Portable process exit codes are 0 through 255; the managed entry point preserves the exact handler integer while the operating system owns wider-value encoding.',
        'The merged reusable C# build-gate implementation at source commit ' + $sourceCommit + ' is current source truth.'
    )
    unresolvedDecisions = @()
    sourceTruthAuthorities = @(
        [ordered]@{
            identity = 'pkid:source-authority:program-kit:typed-console-intent'
            ownerId = 'pkid:domain:program-kit:toolkit'
            source = $intentReference
            sourcePath = 'extensions/typed-console-host-generation/design-intent.md'
            governs = 'The converged human outcome, boundaries, exact dependencies, integrity behavior, maintenance flow, deferrals, and approval boundary.'
        },
        [ordered]@{
            identity = 'pkid:source-authority:program-kit:current-open-console-schema'
            ownerId = 'pkid:domain:program-kit:open-console'
            source = New-Reference `
                'pkid:schema:program-kit:open-console' `
                '1.0.0' `
                $openConsoleSchemaDigest
            sourcePath = 'schemas/dotnet/open-console.schema.json'
            governs = 'The current grammar and validation source that W010 moves to language-neutral ownership.'
        },
        [ordered]@{
            identity = 'pkid:source-authority:program-kit:current-console-renderer'
            ownerId = 'pkid:domain:program-kit:dotnet-console-projection'
            source = New-Reference `
                'pkid:source:program-kit:dotnet-host-source-renderer' `
                '1.0.0' `
                $rendererDigest
            sourcePath = 'src/Orbyss.ProgramKit.DotNet/Generation/DotNetHostSourceRenderer.cs'
            governs = 'The current generated host layout and Console rendering implementation replaced by the approved compiler structure.'
        },
        [ordered]@{
            identity = 'pkid:source-authority:program-kit:capability-bundle'
            ownerId = 'pkid:domain:program-kit:software-maintenance'
            source = New-Reference `
                'pkid:manifest:program-kit:capability-bundle' `
                '2.1.0' `
                $capabilityBundleDigest
            sourcePath = '.agent-capabilities/capability-bundle-manifest.json'
            governs = 'The existing inert exact-byte capability packaging and explicit initialization foundation extended by W090 and W100.'
        },
        [ordered]@{
            identity = 'pkid:source-authority:program-kit:private-csharp-gate'
            ownerId = 'pkid:domain:program-kit:toolkit'
            source = $privateGateReference
            sourcePath = 'governance/csharp-source-quality-gate.md'
            governs = 'The human-selected existing static conformance policy for Program Kit-owned implementation source.'
        }
    )
    domains = $domains
    contracts = @()
    semanticModels = @(
        [ordered]@{
            identity = 'pkid:model:program-kit:typed-console-binding'
            ownerDomainId = 'pkid:domain:program-kit:dotnet-console-projection'
            meaning = 'The exact reconciliation of language-neutral command sources, structured CLR types, request construction, handlers, optional validators, feature, project, and reference assembly.'
            termContractIds = @()
            invariants = 'Every command maps exactly once; every constructor parameter has an exact CLR descriptor, source, position, name, and default disposition; compiled metadata must match before publication.'
        },
        [ordered]@{
            identity = 'pkid:model:program-kit:typed-console-invocation'
            ownerDomainId = 'pkid:domain:program-kit:dotnet-console-projection'
            meaning = 'The host-owned parse, document validation, request construction, optional consumer validation, handler, cancellation, shutdown, diagnostic, and exit-code lifecycle.'
            termContractIds = @()
            invariants = 'Generated validation precedes consumer code; validator failure prevents handlers; exactly one feature/handler and at most one validator resolve; handler integers remain unchanged at the managed entry point.'
        },
        [ordered]@{
            identity = 'pkid:model:program-kit:generated-output-seal'
            ownerDomainId = 'pkid:domain:program-kit:generated-output-integrity'
            meaning = 'The all-generated-file manifest, external anchor, offline verifier, atomic publication transaction, build attestation, and explicit repair authority.'
            termContractIds = @()
            invariants = 'Every generated payload byte is covered; consumer files are excluded; drift blocks build and publication; repair quarantines rather than adopts edited generated code.'
        },
        [ordered]@{
            identity = 'pkid:model:program-kit:incremental-maintenance'
            ownerDomainId = 'pkid:domain:program-kit:software-maintenance'
            meaning = 'One human-started compatible change routed through shared completion profiles and recorded as coherent application history.'
            termContractIds = @()
            invariants = 'No autonomous start; no guessed semantics; all affected derived artifacts refresh; Program Kit upgrades require exact prior approval; material changes route to design.'
        }
    )
    operations = @()
    components = $components
    projects = $projects
    packages = $packages
    referenceRules = $referenceRules
    extensions = @()
    configuration = @()
    featureActivations = @()
    artifactDecisions = @(
        [ordered]@{
            identity = 'pkid:design:program-kit:typed-console-host-generation'
            ownerId = 'pkid:domain:program-kit:toolkit'
            requestedOutcome = 'Represent the complete typed Console projection, generated-output integrity, and bounded maintenance architecture as one validated canonical design.'
            artifactKind = 'schema-instance'
            executableBehavior = [ordered]@{
                isRequired = $false
                rationale = 'The design grants no runtime execution, generation, repair, maintenance, upgrade, publication, or capability-initialization authority.'
            }
            valueLifecycle = [ordered]@{
                uses = @('validated', 'compared', 'digested')
                rationale = 'The exact canonical bytes are schema-validated, semantically checked, digest-bound by the plan and review manifest, and compared during approved work-unit closure.'
            }
            agentRetrieval = [ordered]@{
                isRequired = $false
                retrievalBoundary = ''
                rationale = 'The review set is explicit repository input; no agent retrieval contract is created.'
            }
            agentProcedure = [ordered]@{
                isRequired = $false
                humanStartBoundary = ''
                procedureBoundary = ''
                rationale = 'This design does not initialize a capability, skill, hook, MCP server, tool binding, provider wrapper, or autonomous procedure.'
            }
            humanCommunication = [ordered]@{
                isRequired = $true
                audience = 'The human Program Kit reviewer and later bounded implementer.'
                decisionAuthorityBoundary = 'Only explicit human approval of this review-set version and exact canonical design and plan SHA-256 values authorizes implementation.'
                rationale = 'The Markdown projection, canonical JSON, validation report, and manifest expose exact identities, boundaries, proof obligations, risks, and deferrals.'
            }
            generatedNavigation = [ordered]@{
                isRequired = $false
                sourceIds = @()
                generationRule = ''
                rationale = 'No generated navigation is required.'
            }
            representation = [ordered]@{
                role = 'canonical'
                canonicalArtifactId = $null
                projectionRule = ''
                lossPolicy = ''
            }
            governance = [ordered]@{
                artifactIdentity = 'pkid:design:program-kit:typed-console-host-generation'
                ownerId = 'pkid:domain:program-kit:toolkit'
                schema = New-Reference `
                    'pkid:schema:program-kit:architecture-design' `
                    '2.0.0' `
                    $architectureSchemaDigest
                provenancePolicy = 'Exact converged human intent and source commit ' + $sourceCommit + ' are named; implementation cannot become design authority.'
                digestPolicy = 'The review manifest and Planning v3 plan bind exact canonical bytes; material change requires revalidation, new digests, and renewed human approval.'
                consumerIds = @(
                    'pkid:component:program-kit:dotnet-spectre-console-generator',
                    'pkid:component:program-kit:generated-output-integrity',
                    'pkid:component:program-kit:maintain-software-capability')
                compatibilityPolicy = 'Open Console, .NET binding, Spectre projection, generated layout, integrity, maintenance, capability, diagnostics, and evidence boundaries version explicitly.'
                migrationPolicy = 'Changed accepted contracts require explicit versioning and migration; the superseded unaccepted dispatcher design has no compatibility or migration path.'
            }
            dataHandling = [ordered]@{
                containsSensitiveData = $false
                redactionPolicy = 'Documents, locks, and evidence include identities, paths, versions, digests, and outcomes only; credentials, secret values, and runtime command values are excluded.'
                externalizationPolicy = 'Canonical artifacts remain Program Kit-owned; generated consumer hosts and initialized inert capability wrappers are exact governed projections.'
                containsEphemeralData = $false
                ephemeralDataPolicy = 'Processes, candidate directories, provider sessions, invocation payloads, and runtime validation observations are not durable design content.'
            }
            rationale = 'A schema-governed canonical design is the review authority while runtime, generator, integrity, maintenance, and capability work remains blocked pending exact approval.'
        }
    )
    representationRelationships = @()
    boundaries = [ordered]@{
        security = New-Boundary `
            'Generation treats documents, metadata, paths, messages, and generated roots as untrusted structured input.' `
            @(
                'No consumer assembly is loaded or executed during core generation.',
                'Paths are contained and reparse traversal is rejected.',
                'Consumer text is rendered as escaped plain text.') `
            @(
                'Consumer handlers and validators are not sandboxed.',
                'External signing against coordinated hostile rewriting is deferred.')
        authority = New-Boundary `
            'Humans start design, implementation, maintenance, upgrade, repair, publication, and capability initialization.' `
            @(
                'Plain refresh cannot erase drift.',
                'Program Kit upgrades name an exact approved version.',
                'Capability packaging does not grant execution authority.') `
            @(
                'No hook, watcher, autonomous loop, silent upgrade, implicit repair, or automatic provider activation.')
        secrets = New-Boundary `
            'Generation and maintenance evidence contains paths, identities, versions, digests, and outcomes but no runtime command values or secrets.' `
            @(
                'Diagnostics and receipts exclude credentials and consumer argument values.') `
            @(
                'Consumer validator access to environment and external systems remains consumer-owned.')
        persistence = New-Boundary `
            'Only authoritative documents, generated output, seals, locks, evidence, capability payloads, and coherent Git history are durable.' `
            @(
                'Generated repair retains a recoverable quarantine.',
                'Each maintenance unit records source and derived artifacts together.') `
            @(
                'Runtime command state, service state, and validation observations are not generation evidence.')
        failure = New-Boundary `
            'Every invalid binding, projection, registration, generated drift, transaction ambiguity, or unsupported shape fails closed before publication or invocation.' `
            @(
                'Program Kit operation exit codes remain 0 success, 1 conformance, 2 usage/input, 3 internal.',
                'Generated command failures use document-declared host exit roles.',
                'Failed generation preserves the prior canonical tree.') `
            @(
                'No failure is converted to generated success or guessed binding.')
        concurrency = New-Boundary `
            'Generation and refresh use one exclusive output transaction; verification observes only sealed states.' `
            @(
                'Concurrent writers cannot interleave generated trees.',
                'Candidate output is isolated until validation completes.') `
            @(
                'Consumer command concurrency remains consumer-owned.')
        cancellation = New-Boundary `
            'Cancellation is propagated through generation, validation, handler execution, host lifecycle, and finite build operations.' `
            @(
                'Cancelled generation publishes no partial candidate.',
                'Cancelled command behavior uses the declared host cancellation exit role.') `
            @(
                'Cancellation does not imply rollback of consumer side effects.')
        observability = New-Boundary `
            'Stable diagnostics and evidence expose exact inputs, phases, output digests, gate participation, tests, commits, and repair authority without retaining consumer data.' `
            @(
                'Actual-process fixtures observe invocation order and exit codes.',
                'Verification reports every drifted path.') `
            @(
                'Telemetry or remote evidence transport is not introduced.')
        compatibility = New-Boundary `
            'Open Console, .NET binding, projection, generated layout, integrity, generation request, capabilities, and evidence version independently and fail closed on mismatch.' `
            @(
                'Exact package pins and reference-assembly digests are recorded.',
                'Open Console remains cross-language.',
                'Installed capabilities remain pinned until an approved Program Kit upgrade.') `
            @(
                'No compatibility layer or migration path is created for unaccepted Console-generation designs.')
    }
    scenarios = @(
        [ordered]@{
            identity = 'pkid:scenario:program-kit:generate-typed-console-host'
            actor = 'Console application engineer'
            intent = 'Generate and execute a complete typed Console host from explicit authoritative contracts.'
            preconditions = @(
                'Open Console, .NET binding, project, reference assembly, projection profile, and generation request conform.',
                'Exactly one consumer Console feature registers all required handlers and optional validators.')
            steps = @(
                'Verify documents, digests, paths, and compiled consumer metadata.',
                'Render and compile the deterministic Spectre candidate.',
                'Seal and atomically publish the generated root.',
                'Build the consumer and generated host through selected gates.',
                'Invoke commands through document validation, optional consumer validation, and handlers.')
            outcomes = @(
                'Typed settings construct typed consumer requests.',
                'Help describes the declared grammar.',
                'Handler integers become managed process results unchanged.',
                'Unchanged inputs regenerate byte-identically.')
            failureOutcomes = @(
                'Wrong types or document constraints exit with invalid invocation before consumer code.',
                'Missing or duplicate registrations fail closed.',
                'Unsupported projection shapes never publish output.')
        },
        [ordered]@{
            identity = 'pkid:scenario:program-kit:repair-generated-host'
            actor = 'Consumer workspace engineer'
            intent = 'Detect and safely reset a tampered generated host.'
            preconditions = @(
                'The generated root differs from its manifest or external anchor.',
                'Authoritative consumer inputs remain available.')
            steps = @(
                'Run verify or refresh and receive all drift diagnostics.',
                'Review the drift and authorize generated-output repair.',
                'Quarantine the drifted tree.',
                'Regenerate, seal, verify, build, test, record, and commit the repaired state.')
            outcomes = @(
                'No generated edit is adopted as source truth.',
                'The canonical host returns to a verified buildable state.',
                'The repair authority and resulting history are recorded.')
            failureOutcomes = @(
                'Without repair authority all bytes remain unchanged.',
                'Ambiguous transaction recovery stops for human review.')
        },
        [ordered]@{
            identity = 'pkid:scenario:program-kit:maintain-consumer-software'
            actor = 'Consumer workspace engineer'
            intent = 'Make one small compatible change without a full architecture cycle.'
            preconditions = @(
                'The human explicitly requests a bounded change.',
                'The change does not introduce a material architecture, schema mechanism, security boundary, or unapproved Program Kit upgrade.')
            steps = @(
                'Classify the request through develop-software.',
                'Change authoritative consumer source.',
                'Refresh every affected derived artifact through backed profiles.',
                'Verify, review, record, commit, and push one coherent unit.')
            outcomes = @(
                'Full and incremental implementation use the same completion mechanics.',
                'Git history remains reversible and interpretable.',
                'Installed capability bytes remain version-locked and drift-verifiable.')
            failureOutcomes = @(
                'Ambiguous semantics or material changes route to design.',
                'Capability activation in the Program Kit authoring workspace is rejected.')
        }
    )
    statusClaims = @(
        [ordered]@{
            subjectId = 'pkid:design:program-kit:typed-console-host-generation'
            status = 'scaffolded'
            evidence = @($intentReference)
            claim = 'The review design exists from explicit converged human intent; no approved implementation behavior is claimed by this artifact.'
        }
    )
    staticConformanceDisposition = $dispositionReference
}
Write-Json 'architecture-design.json' $architecture
$architectureDigest = Get-Digest `
    'extensions/typed-console-host-generation/architecture-design.json'
$designReference = New-Reference `
    'pkid:design:program-kit:typed-console-host-generation' `
    '1.0.0' `
    $architectureDigest

$requirements = [ordered]@{
    'PKTCH-R001' = 'Open Console has language-neutral schema and implementation ownership with no CLR or Spectre vocabulary.'
    'PKTCH-R002' = 'An explicit .NET binding maps every command to verified CLR request, handler, optional validator, feature, and default contracts.'
    'PKTCH-R003' = 'Consumer contracts are verified against exact reference-assembly metadata without loading or executing consumer code.'
    'PKTCH-R004' = 'Console generation emits a complete deterministic executable project using exact Spectre and CShells package versions.'
    'PKTCH-R005' = 'Generated commands enforce document validation, optional consumer validation, and handler invocation in the fixed host-owned order.'
    'PKTCH-R006' = 'Parsing, help, completion, diagnostics, cancellation, and exit codes conform to Open Console through the pinned .NET projection.'
    'PKTCH-R007' = 'Exactly one Console shell feature and exact handler/validator registration cardinality fail closed through explicit DI composition.'
    'PKTCH-R008' = 'Every generated host tree is sealed and offline-verifiable through a host-kind-neutral manifest and external anchor.'
    'PKTCH-R009' = 'Build and publication reject generated drift without adding runtime source-tree verification.'
    'PKTCH-R010' = 'Refresh is deterministic and atomic; explicit repair quarantines drift and regenerates from authoritative inputs.'
    'PKTCH-R011' = 'maintain-software reuses the same backed completion profiles as full implementation and records coherent reversible history.'
    'PKTCH-R012' = 'Program Kit product capabilities are inert, installable, version-locked, drift-verifiable, and forbidden from authoring-workspace activation.'
    'PKTCH-R013' = 'A real isolated consumer proves typed commands, validation, exit codes, determinism, integrity, repair, and capability installation end to end.'
}

$workUnits = @(
    (New-WorkUnit 'PKTCH-W010' 10 @() `
        'Establish neutral Open Console schema and source ownership, including logical values, canonical defaults, parsing, help, completion, streams, and host exit-code roles.' `
        'schemas/open-console; src/Orbyss.ProgramKit.OpenConsole; bounded existing schema registration, Open Console source, fixtures, tests, docs, solution, and lock files.' `
        'Open Console schema, canonical round trips, semantic validation, and language-neutral vocabulary tests pass.' `
        'Stop if neutral ownership narrows Open Console to one framework or leaves an existing schema consumer inconsistent.' `
        'product' $designReference $activationMatrixReference $verificationProfileReference),
    (New-WorkUnit 'PKTCH-W020' 20 @('PKTCH-W010') `
        'Add the versioned .NET binding schema and model with structured CLR types, explicit symbols, defaults, constructor mappings, contracts, project identity, and reference digest.' `
        'schemas/dotnet; src/Orbyss.ProgramKit.DotNet/Generation/Console/Binding and Contracts; serializers, diagnostics, fixtures, tests, and docs.' `
        'Binding round trips and every ambiguous, missing, colliding, mismatched, or non-explicit shape fails deterministically.' `
        'Stop if mappings must be guessed, executable C# enters the binding, or CLR meaning enters Open Console.' `
        'product' $designReference $activationMatrixReference $verificationProfileReference),
    (New-WorkUnit 'PKTCH-W030' 30 @('PKTCH-W020') `
        'Verify exact bindings against digest-checked consumer metadata and compile isolated candidates without loading consumer code or invoking MSBuild.' `
        'src/Orbyss.ProgramKit.DotNet/Generation/Console/Compilation, Binding, Contracts, and Diagnostics; metadata fixtures and focused tests.' `
        'Valid metadata compiles; digest drift, malformed metadata, accessibility, generic, nullability, signature, constructor, and injection failures reject.' `
        'Stop if verification requires Assembly.Load, consumer execution, ambient resolution, arbitrary MSBuild, or relaxed source gates.' `
        'product' $designReference $activationMatrixReference $verificationProfileReference),
    (New-WorkUnit 'PKTCH-W040' 40 @('PKTCH-W030') `
        'Replace Console generation with an immutable Spectre projection and deterministic per-file renderers for a complete executable generated host.' `
        'src/Orbyss.ProgramKit.DotNet/Generation/Console; bounded generation coordinator and writer code; exact package versions; fixtures, tests, docs, solution, and lock files.' `
        'Candidate compilation, exact file layout, public generated-source gate, and repeated byte-identical generation pass without a second parser or runtime generator dependency.' `
        'Stop if the pinned Spectre version cannot faithfully project an accepted shape or if API/Worker behavior changes outside integrity integration.' `
        'product' $designReference $activationMatrixReference $verificationProfileReference),
    (New-WorkUnit 'PKTCH-W050' 50 @('PKTCH-W040') `
        'Compose exactly one Console feature, audit exact service registrations, use one invocation scope, and implement fixed validation and handler lifecycle.' `
        'generated Console composition, command, validation, lifecycle, DI audit, consumer fixture, tests, and documentation.' `
        'Zero, one, duplicate, lifetime, registration-shape, constructor, provider, validation-order, cancellation, and handler-invocation proofs pass.' `
        'Stop if composition requires scanning, a service locator, multiple features, or consumer knowledge of Spectre or generated types.' `
        'product' $designReference $activationMatrixReference $verificationProfileReference),
    (New-WorkUnit 'PKTCH-W060' 60 @('PKTCH-W050') `
        'Freeze parsing, help, static completion, diagnostics, cancellation, exception, and handler exit behavior through the pinned projection profile.' `
        'Console projection profile, settings validation, command configuration, help, completion, outcome handling, process fixtures, goldens, tests, and docs.' `
        'Actual-process grammar, native types, defaults, validation messages, information paths, cancellation, internal failure, and portable exit-code tests pass.' `
        'Stop if fidelity needs a hidden parser, undocumented built-ins, dynamic completion, or non-neutral Open Console changes.' `
        'product' $designReference $activationMatrixReference $verificationProfileReference),
    (New-WorkUnit 'PKTCH-W070' 70 @('PKTCH-W040') `
        'Add host-kind-neutral generated-output schemas, sealing, offline verification, safe transactions, recovery, and dotnet verify-host.' `
        'schemas/generated-output; src/Orbyss.ProgramKit.GeneratedOutputIntegrity; bounded DotNet publication and CommandLine operations; API/Console/Worker fixtures, tests, docs, solution, and locks.' `
        'Immediate verification plus modified, missing, unexpected, unsafe, reparse, malformed, anchor, recovery, determinism, and all-file diagnostics pass.' `
        'Stop if any generated byte is outside coverage, consumer paths are captured, verification regenerates or uses network, or self-hash handling is ambiguous.' `
        'product' $designReference $activationMatrixReference $verificationProfileReference),
    (New-WorkUnit 'PKTCH-W080' 80 @('PKTCH-W060','PKTCH-W070') `
        'Add generation request, refresh, preview, explicit consumer build, authorized repair/quarantine, private integrity build integration, attestation, and publication verification.' `
        'generation request and refresh orchestration; integrity transactions; approved C# build-profile integration; GeneratedOutputIntegrity.Build; generated project; publish-local; CLI grammar/docs; tests, solution, and locks.' `
        'Create, no-change, changed, drift refusal, repair, preview, quarantine, build rejection, publish rejection, no runtime verification, and frozen operation exit codes pass.' `
        'Stop if refresh silently erases or adopts drift, invokes builds without authority, auto-upgrades, or duplicates reusable C# gate mechanics.' `
        'product' $designReference $activationMatrixReference $verificationProfileReference),
    (New-WorkUnit 'PKTCH-W090' 90 @('PKTCH-W080') `
        'Package inert shared completion profiles for source review, refresh, integrity, build/test, optional publication, evidence, diff, coherent commit, and push.' `
        '.agent-capabilities supporting resources; bounded implement-software-plan references; profile manifests; capability bundle verification and isolated fixtures.' `
        'Full and incremental implementation resolve identical profile bytes; profiles remain non-invokable, inert, and authority-free.' `
        'Stop if a profile grants authority, becomes independently invokable, duplicates implementation, or activates in the authoring workspace.' `
        'product' $designReference $activationMatrixReference $verificationProfileReference),
    (New-WorkUnit 'PKTCH-W100' 100 @('PKTCH-W090') `
        'Register and package maintain-software, route bounded changes, enforce the mandatory distributable/inert capability standard, and prove isolated initialization.' `
        '.agent-capabilities canonical definitions, Codex and Claude templates, index, navigation, bundle manifest/package, initializer policy, locks, conformance fixtures, tests, docs, and package locks.' `
        'Capability completeness, thin wrappers, bundle digests, authoring deny, no global writes, isolated initialization, drift checks, upgrade approval, and availability backing pass.' `
        'Stop if the capability can start autonomously, bypass material design, auto-upgrade, activate while authored, or write outside the selected consumer workspace.' `
        'product' $designReference $activationMatrixReference $verificationProfileReference),
    (New-WorkUnit 'PKTCH-W110' 110 @('PKTCH-W080','PKTCH-W100') `
        'Prove and close the complete architecture with an isolated typed Console consumer, exact evidence, full gates, and final reviewed history.' `
        'typed Console conformance fixture; generated expected bytes; unit/conformance harnesses; docs; review-set validation; implementation evidence.' `
        'Locked restore, private/public source gates, full build/unit/conformance suites, child processes, determinism, tamper, repair, build/publish rejection, capability isolation, and changed-file review pass.' `
        'Stop on any required failure, nondeterminism, active authoring capability, incomplete evidence, publication requirement, or material design deviation.' `
        'closure' $designReference $activationMatrixReference $verificationProfileReference)
)

$traceMap = [ordered]@{
    'PKTCH-R001' = @('PKTCH-W010','PKTCH-W060','PKTCH-W110')
    'PKTCH-R002' = @('PKTCH-W020','PKTCH-W030','PKTCH-W110')
    'PKTCH-R003' = @('PKTCH-W030','PKTCH-W110')
    'PKTCH-R004' = @('PKTCH-W040','PKTCH-W110')
    'PKTCH-R005' = @('PKTCH-W050','PKTCH-W060','PKTCH-W110')
    'PKTCH-R006' = @('PKTCH-W060','PKTCH-W110')
    'PKTCH-R007' = @('PKTCH-W050','PKTCH-W110')
    'PKTCH-R008' = @('PKTCH-W070','PKTCH-W080','PKTCH-W110')
    'PKTCH-R009' = @('PKTCH-W080','PKTCH-W110')
    'PKTCH-R010' = @('PKTCH-W070','PKTCH-W080','PKTCH-W110')
    'PKTCH-R011' = @('PKTCH-W090','PKTCH-W100','PKTCH-W110')
    'PKTCH-R012' = @('PKTCH-W100','PKTCH-W110')
    'PKTCH-R013' = @('PKTCH-W110')
}

$trace = @(
    foreach ($entry in $requirements.GetEnumerator()) {
        [ordered]@{
            requirementId = $entry.Key
            ownerId = 'pkid:domain:program-kit:toolkit'
            contractOrArtifact = $designReference
            workUnitIds = $traceMap[$entry.Key]
            implementationOutcome = $entry.Value
            dependencyOrExtensionImpact = @()
            tests = @()
            evidence = @()
            observableAcceptanceOutcome = $entry.Value
        }
    }
)

$plan = [ordered]@{
    design = $designReference
    ownerId = 'pkid:domain:program-kit:toolkit'
    state = 'ready-for-human-decision'
    requirementIds = @($requirements.Keys)
    workUnits = $workUnits
    parallelGroups = @()
    trace = $trace
    unresolvedDecisions = @()
    staticConformanceDisposition = $dispositionReference
    staticConformanceState = 'reuse-existing'
    gateDesign = $gateDesignReference
    gateDefinition = [ordered]@{
        identity = $privateGateReference.identity
        version = $privateGateReference.version
        state = 'materialized'
        integrityDigest = $privateGateReference.digest
    }
    selectionLock = [ordered]@{
        identity = $selectionLockReference.identity
        version = $selectionLockReference.version
        state = 'materialized'
        integrityDigest = $selectionLockReference.digest
    }
    activationEvidence = [ordered]@{
        identity = $activationEvidenceReference.identity
        version = $activationEvidenceReference.version
        state = 'materialized'
        integrityDigest = $activationEvidenceReference.digest
    }
}
Write-Json 'implementation-plan.json' $plan
$planDigest = Get-Digest `
    'extensions/typed-console-host-generation/implementation-plan.json'

$summary = [ordered]@{
    sourceCommit = $sourceCommit
    architectureSchema = New-Reference `
        'pkid:schema:program-kit:architecture-design' `
        '2.0.0' `
        $architectureSchemaDigest
    planSchema = New-Reference `
        'pkid:schema:program-kit:implementation-plan' `
        '3.0.0' `
        $planSchemaDigest
    dispositionSchema = New-Reference `
        'pkid:schema:program-kit:static-conformance-disposition' `
        '1.0.0' `
        $dispositionSchemaDigest
    designBasis = $designBasisReference
    disposition = $dispositionReference
    selectionLock = $selectionLockReference
    design = $designReference
    plan = New-Reference `
        'pkid:plan:program-kit:typed-console-host-generation' `
        '1.0.0' `
        $planDigest
}
Write-Output ($summary | ConvertTo-Json -Depth 20)
