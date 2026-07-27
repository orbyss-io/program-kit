using System.Collections.Immutable;
using System.Security.Cryptography;
using System.Text.Json;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.Artifacts.Versioning;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Diagnostics;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Schemas;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Validation;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Verification;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Profiles;
using Orbyss.ProgramKit.Workbench.Operations.Schemas;

namespace Orbyss.ProgramKit.UnitTests.Artifacts.Validation;

[TestClass]
public sealed class CSharpBuildGateContractTests
{
    private static readonly Sha256Digest DigestA = Digest('a');
    private static readonly Sha256Digest DigestB = Digest('b');

    [TestMethod]
    public void ExactFiniteConsumerOwnedDefinitionIsValid()
    {
        var definition = Definition();
        CSharpBuildGateDefinitionValidator sut = new();

        var first = sut.Validate(definition);
        var second = sut.Validate(definition);

        Assert.IsTrue(first.IsValid, Format(first));
        Assert.AreSequenceEqual(first.Diagnostics, second.Diagnostics);
        Assert.AreSequenceEqual(
            Enumerable.Range(1, 13)
                .Select(static number => $"PKCG{number:000}")
                .ToArray(),
            CSharpBuildGateDiagnosticIds.All);
    }

    [TestMethod]
    public void PrivateMechanicsAndCopiedOwnershipDiagnosticsAreRejected()
    {
        var definition = Definition();
        var privateDiagnostic = definition with
        {
            RuleCatalog = definition.RuleCatalog with
            {
                Rules =
                [
                    definition.RuleCatalog.Rules[0] with
                    {
                        DiagnosticId = "PKCS001",
                    },
                ],
                Diagnostics =
                [
                    definition.RuleCatalog.Diagnostics[0] with
                    {
                        DiagnosticId = "PKCS001",
                    },
                ],
            },
        };
        var copiedPublicOwnership = definition with
        {
            RuleCatalog = definition.RuleCatalog with
            {
                Rules =
                [
                    definition.RuleCatalog.Rules[0] with
                    {
                        Kind =
                            CSharpGateRuleKind.ProgramKitPublicContract,
                        DiagnosticId = "PKCC0001",
                    },
                ],
                Diagnostics =
                [
                    definition.RuleCatalog.Diagnostics[0] with
                    {
                        DiagnosticId = "PKCC0001",
                    },
                ],
            },
        };
        CSharpBuildGateDefinitionValidator sut = new();

        var privateResult = sut.Validate(privateDiagnostic);
        var copiedResult = sut.Validate(copiedPublicOwnership);

        Assert.IsFalse(privateResult.IsValid);
        Assert.IsTrue(privateResult.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == CSharpBuildGateDiagnosticIds.Pkcg004));
        Assert.IsFalse(copiedResult.IsValid);
        Assert.IsTrue(copiedResult.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == CSharpBuildGateDiagnosticIds.Pkcg003));
    }

    [TestMethod]
    public void GlobsAndGeneratedSourceForgeryAreRejected()
    {
        var definition = Definition();
        var glob = definition with
        {
            Profiles = definition.Profiles with
            {
                Projects =
                [
                    definition.Profiles.Projects[0] with
                    {
                        RepositoryRelativeProjectPath = "src/**/*.csproj",
                    },
                ],
            },
        };
        var forged = definition with
        {
            Profiles = definition.Profiles with
            {
                GeneratedSources =
                [
                    new CSharpGateGeneratedSourceProfile(
                        Id("profile", "generated"),
                        Ref("generator", "consumer-source"),
                        definition.OwnerId,
                        "// consumer-generated",
                        ["Consumer.g.cs"],
                        Ref("manifest", "generated-source"),
                        [
                            new CSharpGateContentItem(
                                "src/Consumer/Service.cs",
                                DigestA),
                        ],
                        [Id("rule", "boundary")]),
                ],
            },
        };
        CSharpBuildGateDefinitionValidator sut = new();

        var globResult = sut.Validate(glob);
        var forgedResult = sut.Validate(forged);

        Assert.IsFalse(globResult.IsValid);
        Assert.IsFalse(forgedResult.IsValid);
        Assert.IsTrue(globResult.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == CSharpBuildGateDiagnosticIds.Pkcg006));
        Assert.IsTrue(forgedResult.Diagnostics.Any(static diagnostic =>
            diagnostic.Message.Contains(
                "relabel",
                StringComparison.Ordinal)));
    }

    [TestMethod]
    public void TemporaryExceptionsAreTypedScopedAndBounded()
    {
        var definition = Definition();
        var activatedAt =
            new DateTimeOffset(2026, 7, 27, 10, 0, 0, TimeSpan.Zero);
        var invalid = definition with
        {
            TemporaryExceptions =
            [
                new CSharpGateTemporaryActivationExceptionRecord(
                    Id("exception", "bootstrap"),
                    Ref("gate", "consumer"),
                    Id("rule", "boundary"),
                    Id("profile", "project"),
                    Id("profile", "physical"),
                    CSharpGateCommand.Build,
                    CSharpGateImplementationBoundary.WorkUnit,
                    CSharpGateVerificationProfileKind.WorkUnit,
                    CSharpGateTemporaryExceptionConditionKind
                        .ExactToolchainIncompatibility,
                    [],
                    definition.OwnerId,
                    Ref("decision", "temporary-exception"),
                    "The pinned compiler cannot load.",
                    "This compilation is temporarily ungated.",
                    [Ref("evidence", "compensating-test")],
                    [Ref("evidence", "toolchain-state")],
                    activatedAt,
                    activatedAt.AddMinutes(-1),
                    null,
                    0,
                    Id("work-unit", "remove-exception")),
            ],
        };

        CSharpBuildGateDefinitionValidator sut = new();

        var result = sut.Validate(invalid);

        Assert.IsFalse(result.IsValid);
        Assert.IsGreaterThanOrEqualTo(
            3,
            result.Diagnostics.Count(static diagnostic =>
                diagnostic.Id == CSharpBuildGateDiagnosticIds.Pkcg009));
    }

    [TestMethod]
    public void BoundedExceptionMaySelectOneRuleFromMultiComponentActivation()
    {
        var definition = Definition();
        var secondComponent = definition.AnalyzerComponents[0] with
        {
            Identity = Id("analyzer", "second"),
            RuleIds = [Id("rule", "second")],
        };
        var secondRule = definition.RuleCatalog.Rules[0] with
        {
            Identity = Id("rule", "second"),
            DiagnosticId = "DSE0002",
        };
        var secondDiagnostic = definition.RuleCatalog.Diagnostics[0] with
        {
            DiagnosticId = "DSE0002",
            RuleId = secondRule.Identity,
        };
        var activation = definition.ActivationMatrix.Activations[0];
        var activatedAt =
            new DateTimeOffset(2026, 7, 27, 10, 0, 0, TimeSpan.Zero);
        var exception = new CSharpGateTemporaryActivationExceptionRecord(
            Id("exception", "toolchain"),
            Ref("gate", "consumer"),
            Id("rule", "boundary"),
            activation.ProjectProfileId,
            activation.SourceProfileId,
            activation.Command,
            activation.Boundary,
            activation.VerificationProfile,
            CSharpGateTemporaryExceptionConditionKind
                .ExactToolchainIncompatibility,
            [
                new CSharpGateConditionParameter(
                    "sdk-version",
                    "10.0.100",
                    DigestA),
            ],
            definition.OwnerId,
            Ref("decision", "temporary-exception"),
            "The exact pinned SDK cannot load this analyzer revision.",
            "The affected rule does not execute in this one activation cell.",
            [Ref("evidence", "compensating-test")],
            [Ref("evidence", "toolchain-state")],
            activatedAt,
            activatedAt.AddHours(1),
            "Remove when the pinned analyzer revision supports SDK 10.0.100.",
            1,
            Id("work-unit", "remove-exception"));
        var withException = definition with
        {
            AnalyzerComponents =
            [
                definition.AnalyzerComponents[0],
                secondComponent,
            ],
            RuleCatalog = definition.RuleCatalog with
            {
                Rules =
                [
                    definition.RuleCatalog.Rules[0],
                    secondRule,
                ],
                Diagnostics =
                [
                    definition.RuleCatalog.Diagnostics[0],
                    secondDiagnostic,
                ],
            },
            ActivationMatrix = definition.ActivationMatrix with
            {
                Activations =
                [
                    activation with
                    {
                        AnalyzerComponentIds =
                        [
                            definition.AnalyzerComponents[0].Identity,
                            secondComponent.Identity,
                        ],
                    },
                ],
            },
            TemporaryExceptions = [exception],
        };
        CSharpBuildGateDefinitionValidator sut = new();

        var result = sut.Validate(withException);

        Assert.IsTrue(result.IsValid, Format(result));
    }

    [TestMethod]
    public void SuppressionReconciliationFailsClosed()
    {
        var approvedAt =
            new DateTimeOffset(2026, 7, 27, 10, 0, 0, TimeSpan.Zero);
        var entry = new CSharpGateSuppressionEntry(
            Id("suppression", "one"),
            Id("domain", "software"),
            "DSE0001",
            Id("rule", "boundary"),
            Version(),
            Id("profile", "project"),
            "src/Consumer/Service.cs",
            CSharpGateSuppressionTargetKind.Line,
            "12",
            CSharpGateSuppressionMechanism.SourcePragma,
            Ref("decision", "suppression"),
            "A bounded compatibility suppression.",
            approvedAt,
            approvedAt.AddHours(1),
            null,
            DigestA,
            DigestA,
            DigestA,
            "Remove after dependency migration.");
        var ledger = new CSharpGateSuppressionLedger(
            Id("ledger", "consumer"),
            Version(),
            [entry]);

        var missing =
            CSharpGateSuppressionReconciliationValidation.Validate(
                ledger,
                new CSharpGateSuppressionReconciliation(
                    [],
                    approvedAt.AddMinutes(1)));
        var expired =
            CSharpGateSuppressionReconciliationValidation.Validate(
                ledger,
                new CSharpGateSuppressionReconciliation(
                    [entry.Identity],
                    approvedAt.AddHours(2)));
        var exact =
            CSharpGateSuppressionReconciliationValidation.Validate(
                ledger,
                new CSharpGateSuppressionReconciliation(
                    [entry.Identity],
                    approvedAt.AddMinutes(1)));

        Assert.IsFalse(missing.IsValid);
        Assert.IsFalse(expired.IsValid);
        Assert.IsTrue(exact.IsValid, Format(exact));
    }

    [TestMethod]
    public void SelectionLockRequiresExactPathsDigestsAndReceiptCardinality()
    {
        var definition = Definition();
        var definitionReference = new ArtifactReference(
            definition.Identity,
            definition.Version,
            definition.RevisionDigest);
        var exact = SelectionLock(definitionReference);
        var glob = exact with
        {
            PhysicalSourceInventory =
            [
                new CSharpGateLockedContent("src/**/*.cs", DigestA),
            ],
        };
        var stale = exact with
        {
            GateDefinition = definitionReference with
            {
                Digest = DigestB,
            },
        };
        var noReceipt = exact with
        {
            ExpectedReceipts = [],
        };
        CSharpBuildGateSelectionLockValidator lockValidator = new();

        Assert.IsTrue(lockValidator.Validate(exact).IsValid);
        Assert.IsFalse(lockValidator.Validate(glob).IsValid);
        Assert.IsTrue(
            CSharpBuildGateDefinitionLockValidation.Validate(
                definition,
                definitionReference,
                exact).IsValid);
        Assert.IsFalse(
            CSharpBuildGateDefinitionLockValidation.Validate(
                definition,
                definitionReference,
                stale).IsValid);
        Assert.IsFalse(
            CSharpBuildGateDefinitionLockValidation.Validate(
                definition,
                definitionReference,
                noReceipt).IsValid);
    }

    [TestMethod]
    public void ParticipationAndEvidenceContractsRejectMismatches()
    {
        var lockReference = Ref("selection-lock", "consumer");
        var receipt = new CSharpGateParticipationReceiptDocument(
            Id("receipt", "consumer-analyzer"),
            Version(),
            lockReference,
            Id("profile", "project"),
            Id("analyzer", "consumer"),
            CSharpGateVerificationProfileKind.WorkUnit,
            "nonce-1",
            DigestA,
            DigestA,
            DigestA,
            DigestB);
        var mismatched = receipt with
        {
            ExecutedCompilerInputDigest = DigestB,
        };
        var evidence = new CSharpBuildGateVerificationEvidenceDocument(
            Id("evidence", "consumer"),
            Version(),
            lockReference,
            CSharpGateVerificationProfileKind.WorkUnit,
            true,
            null,
            [Ref("receipt", "consumer-analyzer")],
            [],
            [],
            DigestA,
            DigestB);
        var contradictory = evidence with
        {
            FailureLayer = CSharpGateEvidenceLayer.Attachment,
        };

        CSharpGateParticipationReceiptValidator receiptValidator = new();
        CSharpBuildGateVerificationEvidenceValidator evidenceValidator = new();

        Assert.IsTrue(receiptValidator.Validate(receipt).IsValid);
        Assert.IsFalse(receiptValidator.Validate(mismatched).IsValid);
        Assert.IsTrue(evidenceValidator.Validate(evidence).IsValid);
        Assert.IsFalse(evidenceValidator.Validate(contradictory).IsValid);
    }

    [TestMethod]
    public void SchemaModuleIsExactFiniteAndDigestLocked()
    {
        CSharpBuildGateSchemaModule module = new();
        ProgramKitSchemaModuleValidator validator = new();

        var validation = validator.Validate(module);

        Assert.IsTrue(validation.IsValid, Format(validation));
        Assert.HasCount(6, module.Resources);
        foreach (var resource in module.Resources)
        {
            using var stream = module.OpenRead(resource.SchemaReference);
            var actual = string.Concat(
                "sha256:",
                Convert.ToHexStringLower(SHA256.HashData(stream)));
            Assert.AreEqual(resource.SchemaReference.Digest.Value, actual);
        }
    }

    [TestMethod]
    public void ConsumerOwnedDefinitionFixtureConformsAndCanonicalizesDeterministically()
    {
        var bytes = File.ReadAllBytes(Path.Combine(
            FindProgramKitRoot().FullName,
            "extensions",
            "reusable-csharp-build-gates",
            "fixtures",
            "consumer-owned-build-gate-definition.json"));
        CSharpBuildGateSchemaModule csharpModule = new();
        CSharpBuildGateCompositeSchemaModule module = new(
        [
            new ArtifactsSchemaModule(),
            csharpModule,
        ]);
        var schema = csharpModule.Resources.Single(static resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:csharp-build-gate-definition");
        ProgramKitJsonCanonicalizer canonicalizer = new();
        JsonSchemaWorkbenchValidator validator = new(
            canonicalizer,
            new ProgramKitSchemaModuleValidator());

        var validation = validator.Validate(
            bytes,
            module,
            schema.SchemaReference,
            JsonSerializationLimits.Default);
        var overLimit = Assert.ThrowsExactly<ProgramKitJsonException>(() =>
            validator.Validate(
                bytes,
                module,
                schema.SchemaReference,
                new JsonSerializationLimits(
                    MaxUtf8Bytes: 1,
                    MaxDepth: 64,
                    MaxTokens: 100_000,
                    MaxObjectMembers: 100_000,
                    MaxBufferedObjectBytes: 1)));
        var first = canonicalizer.Canonicalize(
            bytes,
            JsonSerializationLimits.Default);
        var second = canonicalizer.Canonicalize(
            bytes,
            JsonSerializationLimits.Default);

        Assert.IsTrue(validation.IsValid, Format(validation));
        Assert.Contains("byte limit", overLimit.Message);
        Assert.AreEqual(first.Digest, second.Digest);
        Assert.AreSequenceEqual(first.ToArray(), second.ToArray());
    }

    [TestMethod]
    public void ContractAssemblyHasNoRuntimeRoslynOrMsBuildClosure()
    {
        var references = typeof(CSharpBuildGateDefinitionDocument)
            .Assembly
            .GetReferencedAssemblies()
            .Select(static reference => reference.Name!)
            .Order(StringComparer.Ordinal)
            .ToArray();

        Assert.Contains("Orbyss.ProgramKit.Artifacts", references);
        Assert.DoesNotContain(static reference =>
            reference.StartsWith(
                "Microsoft.CodeAnalysis",
                StringComparison.Ordinal) ||
            reference.StartsWith(
                "Microsoft.Build",
                StringComparison.Ordinal) ||
            reference.StartsWith(
                "Microsoft.Extensions.Hosting",
                StringComparison.Ordinal),
            references);
    }

    [TestMethod]
    public void ContractVersionMapIsSchemaAndModelValid()
    {
        var bytes = File.ReadAllBytes(Path.Combine(
            FindProgramKitRoot().FullName,
            "extensions",
            "reusable-csharp-build-gates",
            "csharp-build-gate-contracts-version-map.json"));
        ArtifactsSchemaModule module = new();
        var schema = module.Resources.Single(static resource =>
            resource.SchemaReference.Identity.Value ==
                "pkid:schema:program-kit:version-map");
        JsonSchemaWorkbenchValidator schemaValidator = new(
            new ProgramKitJsonCanonicalizer(),
            new ProgramKitSchemaModuleValidator());
        using var json = JsonDocument.Parse(bytes);
        var map = ReadVersionMap(json.RootElement);
        VersionMapDocumentValidator modelValidator = new(
            new DefaultArtifactEnvelopeValidator());

        var schemaValidation = schemaValidator.Validate(
            bytes,
            module,
            schema.SchemaReference,
            JsonSerializationLimits.Default);
        var modelValidation = modelValidator.Validate(map);

        Assert.IsTrue(schemaValidation.IsValid, Format(schemaValidation));
        Assert.IsTrue(modelValidation.IsValid, Format(modelValidation));
        Assert.HasCount(6, map.Nodes);
        Assert.HasCount(6, map.Edges);
    }

    private static CSharpBuildGateDefinitionDocument Definition()
    {
        var ownerId = Id("domain", "software");
        var ruleId = Id("rule", "boundary");
        var projectProfileId = Id("profile", "project");
        var sourceProfileId = Id("profile", "physical");
        var componentId = Id("analyzer", "consumer");
        var sourceContract = Ref("contract", "consumer-boundary");
        var rule = new CSharpGateRuleDefinition(
            ruleId,
            Version(),
            CSharpGateRuleKind.ConsumerOwned,
            ownerId,
            sourceContract,
            "DSE0001",
            "Consumer boundary",
            "Architecture",
            CSharpGateDiagnosticSeverity.Error,
            "The approved boundary must remain explicit.",
            "Move the reference behind the approved contract.",
            "A forbidden namespace reference is present in the compilation.",
            CSharpGateRuleLayer.Compiler,
            ["Runtime behavior is outside this rule."],
            [projectProfileId],
            [sourceProfileId],
            CSharpGateSuppressionDisposition.SourceLocalLedger,
            Ref("fixture", "positive"),
            Ref("fixture", "negative"),
            Ref("compatibility", "rule"),
            Ref("migration", "rule"),
            null,
            null,
            null,
            "Report the forbidden syntax location.",
            "Use a deterministic invariant message.",
            100,
            1000);
        return new CSharpBuildGateDefinitionDocument(
            Id("gate", "consumer"),
            Version(),
            DigestA,
            ownerId,
            Id("policy", "software"),
            Ref("static-conformance-disposition", "software"),
            Ref("compatibility-policy", "software"),
            [
                new CSharpSemanticOwner(
                    ownerId,
                    CSharpAnalyzerComponentKind.ConsumerOwned,
                    sourceContract,
                    "DSE"),
            ],
            [
                new CSharpAnalyzerComponent(
                    componentId,
                    CSharpAnalyzerComponentKind.ConsumerOwned,
                    ownerId,
                    new CSharpAnalyzerArtifactSelection(
                        CSharpAnalyzerArtifactKind.LocalNonPackableProject,
                        "analyzers/Consumer.Analyzers/Consumer.Analyzers.csproj",
                        null,
                        "Consumer.Analyzers.dll",
                        DigestA,
                        false,
                        false,
                        false),
                    [ruleId],
                    [Ref("receipt-generator", "consumer-analyzer")],
                    Range(),
                    Range(),
                    Range(),
                    Range(),
                    Range()),
            ],
            new CSharpGateRuleCatalog(
                Id("catalog", "rules"),
                Version(),
                [rule],
                [
                    new CSharpGateDiagnosticDefinition(
                        "DSE0001",
                        ownerId,
                        ruleId,
                        Version(),
                        rule.Title,
                        rule.Category,
                        rule.DefaultSeverity,
                        "Consumer boundary violation."),
                ]),
            new CSharpGateProfileCatalog(
                [
                    new CSharpGateProjectProfile(
                        projectProfileId,
                        Id("project", "consumer"),
                        "src/Consumer/Consumer.csproj",
                        ["net10.0"],
                        [],
                        []),
                ],
                [
                    new CSharpGateInputProfile(
                        sourceProfileId,
                        CSharpGateInputKind.PhysicalSource,
                        [
                            new CSharpGateContentItem(
                                "src/Consumer/Service.cs",
                                DigestA),
                        ],
                        [ruleId]),
                ],
                []),
            new CSharpGateActivationMatrix(
                Id("activation-matrix", "consumer"),
                Version(),
                [
                    new CSharpGateActivation(
                        projectProfileId,
                        sourceProfileId,
                        CSharpGateCommand.Build,
                        CSharpGateImplementationBoundary.WorkUnit,
                        CSharpGateVerificationProfileKind.WorkUnit,
                        [componentId]),
                ]),
            [],
            new CSharpGateSuppressionLedger(
                Id("ledger", "consumer"),
                Version(),
                []),
            new CSharpGateAssurance(
                new CSharpGateCompatibility(
                    Range(),
                    Range(),
                    Range(),
                    Range(),
                    Range()),
                [],
                [
                    new CSharpGateThreat(
                        Id("threat", "analyzer-removal"),
                        "The selected analyzer is removed.",
                        "Compiler attachment",
                        [Ref("fixture", "tamper")],
                        "Compiler defects remain outside this proof."),
                ],
                [
                    new CSharpGateFixture(
                        Id("fixture", "positive"),
                        CSharpGateFixtureKind.Positive,
                        Ref("fixture-input", "positive"),
                        DigestA,
                        DigestB),
                ],
                new CSharpGatePerformanceBudget(100, 1000, 256)));
    }

    private static CSharpBuildGateSelectionLockDocument SelectionLock(
        ArtifactReference definitionReference) =>
        new(
            Id("selection-lock", "consumer"),
            Version(),
            Ref("static-conformance-disposition", "software"),
            definitionReference,
            [Ref("analyzer", "consumer")],
            Ref("catalog", "rules"),
            [],
            Ref("activation-matrix", "consumer"),
            Ref("ledger", "consumer"),
            [Ref("operation", "verify")],
            [
                new CSharpGateLockedContent(
                    "src/Consumer/Consumer.csproj",
                    DigestA),
            ],
            [
                new CSharpGateLockedContent(
                    "src/Consumer/Service.cs",
                    DigestA),
            ],
            [],
            [
                new CSharpGateLockedContent(
                    "analyzers/Consumer.Analyzers.dll",
                    DigestA),
            ],
            [],
            [],
            Version(),
            Version(),
            Version(),
            "net10.0",
            [
                new CSharpGateExpectedReceipt(
                    Id("profile", "project"),
                    Id("analyzer", "consumer"),
                    CSharpGateVerificationProfileKind.WorkUnit,
                    Id("receipt", "consumer-analyzer")),
            ],
            DigestA,
            DigestB);

    private static ProgramKitIdentifier Id(string kind, string name) =>
        new($"pkid:{kind}:consumer:{name}");

    private static ArtifactReference Ref(string kind, string name) =>
        new(Id(kind, name), Version(), DigestA);

    private static SemanticVersion Version() => new("1.0.0");

    private static SemanticVersionRange Range() => new("[1.0.0]");

    private static Sha256Digest Digest(char value) =>
        new($"sha256:{new string(value, 64)}");

    private static VersionMapDocument ReadVersionMap(JsonElement root) =>
        new(
            root.GetProperty("nodes")
                .EnumerateArray()
                .Select(ReadVersionNode)
                .ToImmutableArray(),
            root.GetProperty("edges")
                .EnumerateArray()
                .Select(ReadVersionEdge)
                .ToImmutableArray());

    private static VersionRevisionNode ReadVersionNode(JsonElement value) =>
        new(
            ReadReference(value.GetProperty("revision")),
            VersionBoundaryKind.Schema,
            new ProgramKitIdentifier(value.GetProperty("ownerId").GetString()!),
            value.GetProperty("evidenceReferences")
                .EnumerateArray()
                .Select(ReadReference)
                .ToImmutableArray());

    private static VersionDependencyEdge ReadVersionEdge(JsonElement value) =>
        new(
            new ProgramKitIdentifier(value.GetProperty("id").GetString()!),
            ReadReference(value.GetProperty("source")),
            new ProgramKitIdentifier(
                value.GetProperty("targetIdentity").GetString()!),
            VersionDependencyKind.UsesContract,
            new SemanticVersionRange(
                value.GetProperty("acceptedRange").GetString()!),
            ReadReference(value.GetProperty("resolution")),
            DependencyExposure.Public,
            value.GetProperty("compatibilityDimensions")
                .EnumerateArray()
                .Select(static item => item.GetString() switch
                {
                    "wire-read" => CompatibilityDimension.WireRead,
                    "wire-write" => CompatibilityDimension.WireWrite,
                    _ => throw new InvalidDataException(
                        "Unexpected compatibility dimension."),
                })
                .ToImmutableArray(),
            value.GetProperty("evidenceReferences")
                .EnumerateArray()
                .Select(ReadReference)
                .ToImmutableArray());

    private static ArtifactReference ReadReference(JsonElement value) =>
        new(
            new ProgramKitIdentifier(value.GetProperty("identity").GetString()!),
            new SemanticVersion(value.GetProperty("version").GetString()!),
            new Sha256Digest(value.GetProperty("digest").GetString()!));

    private static DirectoryInfo FindProgramKitRoot()
    {
        DirectoryInfo? current = new(AppContext.BaseDirectory);
        while (current is not null)
        {
            if (File.Exists(Path.Combine(current.FullName, "ProgramKit.sln")))
            {
                return current;
            }

            current = current.Parent;
        }

        throw new DirectoryNotFoundException(
            "Unable to locate the Program Kit repository root.");
    }

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(static diagnostic =>
                $"{diagnostic.Id} {diagnostic.Path}: {diagnostic.Message}"));
}
