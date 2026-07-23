using System.Collections.Immutable;
using Orbyss.ProgramKit.Architecture;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.UnitTests;

[TestClass]
public sealed class ArchitectureDesignContractTests
{
    [TestMethod]
    public void FullSyntheticDesignClosesItsDeclaredCrossReferences()
    {
        var design = CreateDesign();

        var result = new ArchitectureDesignValidator().Validate(design);

        Assert.IsTrue(result.IsValid, Format(result));
        Assert.AreEqual(1, design.UnresolvedDecisions.Length);
        Assert.AreEqual(1, design.SemanticModels.Length);
        Assert.AreEqual(1, design.Operations.Length);
        Assert.AreEqual(5, design.Extensions.Length);
        Assert.AreEqual(1, design.Configuration.Length);
        Assert.AreEqual(1, design.FeatureActivations.Length);
        Assert.AreEqual(1, design.RepresentationRelationships.Length);
        CollectionAssert.AreEquivalent(
            Enum.GetValues<ExtensionKind>(),
            design.Extensions.Select(static extension => extension.Kind).ToArray());

        var operation = design.Operations[0];
        Assert.IsNotNull(operation.Input);
        Assert.IsNotNull(operation.Output);
        Assert.IsNotNull(operation.SideEffects);
        Assert.IsNotNull(operation.Authority);
        Assert.IsNotNull(operation.Failures);
        Assert.IsNotNull(operation.Cancellation);
        Assert.IsNotNull(operation.Idempotency);
        Assert.IsNotNull(operation.Compatibility);
        Assert.IsNotNull(operation.Observability);
        Assert.IsNotNull(operation.ResourceOwnership);
    }

    [TestMethod]
    public void GovernedArtifactAndItsSingleDecisionMayShareAnIdentity()
    {
        var design = CreateDesign();

        var result = new ArchitectureDesignValidator().Validate(design);

        Assert.IsFalse(result.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ArchitectureDiagnosticIds.Pkarc601 &&
            diagnostic.Path.StartsWith(
                "/artifactDecisions/",
                StringComparison.Ordinal)));
    }

    [TestMethod]
    public void DuplicateArtifactDecisionsForOneArtifactFailClosed()
    {
        var design = CreateDesign();
        var duplicate = design with
        {
            ArtifactDecisions =
            [
                design.ArtifactDecisions[0],
                design.ArtifactDecisions[0],
            ],
        };

        var result = new ArchitectureDesignValidator().Validate(duplicate);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ArchitectureDiagnosticIds.Pkarc601 &&
            diagnostic.Path == "/artifactDecisions/1/identity"));
    }

    [TestMethod]
    public void UndeclaredProjectComponentAndPackageProjectAreRejected()
    {
        var design = CreateDesign();
        var missingComponent = ProgramKitIdentifier.Parse(
            "pkid:component:program-kit:missing-component");
        var missingProject = ProgramKitIdentifier.Parse(
            "pkid:project:program-kit:missing-project");
        var invalid = design with
        {
            Projects =
            [
                design.Projects[0] with
                {
                    ComponentIds = [missingComponent],
                },
            ],
            Packages =
            [
                design.Packages[0] with
                {
                    ProjectIds = [missingProject],
                },
            ],
        };

        var result = new ArchitectureDesignValidator().Validate(invalid);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ArchitectureDiagnosticIds.Pkarc634 &&
            diagnostic.Path == "/projects/0/componentIds/0"));
        Assert.IsTrue(result.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ArchitectureDiagnosticIds.Pkarc634 &&
            diagnostic.Path == "/packages/0/projectIds/0"));
    }

    [TestMethod]
    public void UndefinedEnumValuesFailClosedAcrossTheArchitectureContract()
    {
        var design = CreateDesign();
        var invalid = design with
        {
            Contracts = design.Contracts.SetItem(
                0,
                design.Contracts[0] with { Kind = (ContractKind)999 }),
            Components = design.Components.SetItem(
                0,
                design.Components[0] with { Kind = (ComponentKind)999 }),
            ReferenceRules = design.ReferenceRules.SetItem(
                0,
                design.ReferenceRules[0] with
                {
                    Disposition = (ReferenceRuleDisposition)999,
                }),
            Operations = design.Operations.SetItem(
                0,
                design.Operations[0] with
                {
                    Idempotency = design.Operations[0].Idempotency with
                    {
                        Kind = (OperationIdempotencyKind)999,
                    },
                }),
            Extensions = design.Extensions.SetItem(
                0,
                design.Extensions[0] with
                {
                    Semantics = design.Extensions[0].Semantics with
                    {
                        Replacement = design.Extensions[0].Semantics.Replacement! with
                        {
                            Cardinality = (ReplacementCardinality)999,
                        },
                    },
                }),
            ArtifactDecisions = design.ArtifactDecisions.SetItem(
                0,
                design.ArtifactDecisions[0] with
                {
                    ValueLifecycle = design.ArtifactDecisions[0].ValueLifecycle with
                    {
                        Uses = [(ValueLifecycleUse)999],
                    },
                }),
            StatusClaims = design.StatusClaims.SetItem(
                0,
                design.StatusClaims[0] with { Status = (ArtifactStatus)999 }),
        };

        var result = new ArchitectureDesignValidator().Validate(invalid);
        var diagnosticIds = result.Diagnostics
            .Select(static diagnostic => diagnostic.Id)
            .ToHashSet(StringComparer.Ordinal);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(diagnosticIds.Contains(ArchitectureDiagnosticIds.Pkarc124));
        Assert.IsTrue(diagnosticIds.Contains(ArchitectureDiagnosticIds.Pkarc212));
        Assert.IsTrue(diagnosticIds.Contains(ArchitectureDiagnosticIds.Pkarc331));
        Assert.IsTrue(diagnosticIds.Contains(ArchitectureDiagnosticIds.Pkarc637));
        Assert.IsTrue(diagnosticIds.Contains(ArchitectureDiagnosticIds.Pkarc638));
        Assert.IsTrue(diagnosticIds.Contains(ArchitectureDiagnosticIds.Pkarc639));
        Assert.IsTrue(diagnosticIds.Contains(ArchitectureDiagnosticIds.Pkarc640));
    }

    private static ArchitectureDesignDocument CreateDesign()
    {
        var owner = ProgramKitIdentifier.Parse(
            "pkid:domain:program-kit:architecture-test");
        var contract = ProgramKitIdentifier.Parse(
            "pkid:contract:program-kit:architecture-test");
        var semanticModel = ProgramKitIdentifier.Parse(
            "pkid:model:program-kit:architecture-test");
        var operation = ProgramKitIdentifier.Parse(
            "pkid:operation:program-kit:architecture-test");
        var coreComponent = ProgramKitIdentifier.Parse(
            "pkid:component:program-kit:architecture-test");
        var featureComponent = ProgramKitIdentifier.Parse(
            "pkid:feature:program-kit:architecture-test");
        var providerComponent = ProgramKitIdentifier.Parse(
            "pkid:provider:program-kit:architecture-test");
        var project = ProgramKitIdentifier.Parse(
            "pkid:project:program-kit:architecture-test");
        var package = ProgramKitIdentifier.Parse(
            "pkid:package:program-kit:architecture-test");
        var configuration = ProgramKitIdentifier.Parse(
            "pkid:configuration:program-kit:architecture-test");
        var projection = ProgramKitIdentifier.Parse(
            "pkid:catalog:program-kit:architecture-test-index");
        var source = TestContractValues.Reference(
            "pkid:design-source:program-kit:architecture-test");
        var contractReference = TestContractValues.Reference(contract.Value);

        return new ArchitectureDesignDocument(
            "Synthetic architecture",
            "Exercise a fully connected architecture contract.",
            ["Every universal architecture semantic category."],
            ["Runtime implementation is outside this test."],
            ["All artifact and contract references are exact revisions."],
            [
                new UnresolvedDecision(
                    ProgramKitIdentifier.Parse(
                        "pkid:design:program-kit:unresolved-provider-choice"),
                    owner,
                    "Which production provider should be selected?",
                    "Before production composition.",
                    "Production composition remains blocked."),
            ],
            [
                new SourceTruthAuthority(
                    ProgramKitIdentifier.Parse(
                        "pkid:source-authority:program-kit:architecture-test"),
                    owner,
                    source,
                    "/architecture",
                    "The synthetic architecture."),
            ],
            [
                new DomainDefinition(
                    owner,
                    "Own the synthetic architecture vocabulary.",
                    [
                        new VocabularyTermDefinition(
                            "Synthetic contract",
                            "A contract used to test architecture consistency.",
                            []),
                    ]),
            ],
            [
                new ContractDefinition(
                    contract,
                    owner,
                    ContractKind.Value,
                    SemanticVersion.Parse("1.0.0"),
                    TestContractValues.Reference(
                        "pkid:schema:program-kit:architecture-test"),
                    "Carries the synthetic value.",
                    "Major versions carry breaking changes."),
            ],
            [
                new SemanticModelDefinition(
                    semanticModel,
                    owner,
                    "Models one validated synthetic value.",
                    [contract],
                    "The value is non-empty and schema-valid."),
            ],
            [
                new OperationDefinition(
                    operation,
                    owner,
                    "Exchange one synthetic value.",
                    new OperationInputDefinition(
                        [contractReference],
                        false,
                        "Validate against the exact input contract."),
                    new OperationOutputDefinition(
                        [contractReference],
                        false,
                        false,
                        "Return one value after successful completion."),
                    new OperationSideEffectDefinition(true, []),
                    new OperationAuthorityDefinition(
                        false,
                        [],
                        "Before handler invocation.",
                        "No authority is required for this synthetic operation."),
                    new OperationFailureSet(
                        [
                            new OperationFailureDefinition(
                                ProgramKitIdentifier.Parse(
                                    "pkid:contract:program-kit:architecture-test-failure"),
                                "invalid-value",
                                "The supplied value is invalid.",
                                false,
                                null),
                        ],
                        "Unexpected failures become a stable internal failure."),
                    new OperationCancellationDefinition(
                        true,
                        "Cancellation is accepted until completion commits.",
                        "Cancellation propagates to the handler.",
                        "A committed completion wins the cancellation race."),
                    new OperationIdempotencyDefinition(
                        OperationIdempotencyKind.NaturallyIdempotent,
                        "Canonical input identity is the semantic key.",
                        "A duplicate returns the same semantic result."),
                    new OperationCompatibilityDefinition(
                        [
                            CompatibilityDimension.SemanticBehavior,
                            CompatibilityDimension.WireRead,
                            CompatibilityDimension.WireWrite,
                        ],
                        "Breaking contract changes require a migration.",
                        []),
                    new OperationObservabilityDefinition(
                        ["trace", "diagnostic"],
                        "The supplied correlation identity is preserved.",
                        "Contract values are redacted."),
                    new OperationResourceOwnershipDefinition(
                        [],
                        "The operation acquires no owned resources.")),
            ],
            [
                new ComponentDefinition(
                    coreComponent,
                    owner,
                    ComponentKind.DomainCore,
                    "Own the synthetic contract.",
                    [contract],
                    [],
                    false,
                    "The public contract is the compatibility boundary."),
                new ComponentDefinition(
                    featureComponent,
                    owner,
                    ComponentKind.Feature,
                    "Expose the synthetic operation.",
                    [contract],
                    [contract],
                    true,
                    "The feature activation identity is the compatibility boundary."),
                new ComponentDefinition(
                    providerComponent,
                    owner,
                    ComponentKind.Provider,
                    "Provide a replaceable synthetic implementation.",
                    [contract],
                    [contract],
                    false,
                    "The provider contract is the compatibility boundary."),
            ],
            [
                new ProjectDefinition(
                    project,
                    owner,
                    "src/ArchitectureTest/ArchitectureTest.csproj",
                    [coreComponent, featureComponent, providerComponent],
                    [],
                    package),
            ],
            [
                new PackageDefinition(
                    package,
                    owner,
                    SemanticVersion.Parse("1.0.0"),
                    [project],
                    [],
                    [contract],
                    "The package version governs the public contract."),
            ],
            [
                new ReferenceRuleDefinition(
                    ProgramKitIdentifier.Parse(
                        "pkid:reference-rule:program-kit:architecture-test"),
                    owner,
                    ReferenceRuleDisposition.Allowed,
                    project.Value,
                    contract.Value,
                    new SourceTrace(source, "/referenceRules/0"),
                    "The owning project may expose its contract."),
            ],
            CreateExtensions(owner, project, providerComponent, contractReference),
            [
                new ConfigurationDefinition(
                    configuration,
                    owner,
                    TestContractValues.Reference(
                        "pkid:schema:program-kit:architecture-test-configuration"),
                    "Synthetic feature activation.",
                    "No secrets are accepted.",
                    "Breaking configuration changes require migration."),
            ],
            [
                new FeatureActivationDefinition(
                    ProgramKitIdentifier.Parse(
                        "pkid:extension-point:program-kit:architecture-test-activation"),
                    featureComponent,
                    owner,
                    configuration,
                    "Select the feature explicitly by activation identity.",
                    "Missing or duplicate activation fails startup."),
            ],
            [
                CreateArtifactDecision(contract, owner, project),
                CreateProjectionDecision(projection, contract, project),
            ],
            [
                new CanonicalProjectionRelationship(
                    projection,
                    contract,
                    "Generate navigation from the validated contract decision.",
                    "The projection contains navigation only.",
                    true),
            ],
            CreateBoundaries(owner),
            [
                new CallerVisibleScenario(
                    ProgramKitIdentifier.Parse(
                        "pkid:scenario:program-kit:architecture-test"),
                    "Consumer",
                    "Use the synthetic contract.",
                    [],
                    ["Reference the package.", "Exchange the contract."],
                    ["The contract is exchanged."],
                    ["An invalid value is rejected."]),
            ],
            [
                new ArchitectureStatusClaim(
                    coreComponent,
                    ArtifactStatus.Deferred,
                    [],
                    "The synthetic runtime component is deliberately not implemented."),
            ]);
    }

    private static ImmutableArray<ExtensionDefinition> CreateExtensions(
        ProgramKitIdentifier owner,
        ProgramKitIdentifier project,
        ProgramKitIdentifier provider,
        ArtifactReference contract) =>
    [
        new ExtensionDefinition(
            ProgramKitIdentifier.Parse(
                "pkid:extension-point:program-kit:architecture-test-replacement"),
            owner,
            ExtensionKind.Replacement,
            contract,
            new ExtensionSemantics(
                new ReplacementSemantics(
                    ReplacementCardinality.ExactlyOne,
                    "Select the exact configured identity.",
                    "No implicit fallback is allowed.",
                    "A missing or duplicate selection fails."),
                null,
                null,
                null,
                null)),
        new ExtensionDefinition(
            ProgramKitIdentifier.Parse(
                "pkid:extension-point:program-kit:architecture-test-additive"),
            owner,
            ExtensionKind.AdditiveContribution,
            contract,
            new ExtensionSemantics(
                null,
                new AdditiveContributionSemantics(
                    "Zero or more contributions.",
                    "Order by explicit stable identity.",
                    "Aggregate all successful values.",
                    "Fail fast on the first invalid contribution."),
                null,
                null,
                null)),
        new ExtensionDefinition(
            ProgramKitIdentifier.Parse(
                "pkid:extension-point:program-kit:architecture-test-event"),
            owner,
            ExtensionKind.EventSubscription,
            contract,
            new ExtensionSemantics(
                null,
                null,
                new EventSubscriptionSemantics(
                    "At-most-once in-process delivery.",
                    "Stable handler order within one publication.",
                    "No retry.",
                    "No duplicate delivery is introduced.",
                    "The first handler failure stops publication."),
                null,
                null)),
        new ExtensionDefinition(
            ProgramKitIdentifier.Parse(
                "pkid:extension-point:program-kit:architecture-test-provider"),
            owner,
            ExtensionKind.ProviderSpecialization,
            contract,
            new ExtensionSemantics(
                null,
                null,
                null,
                new ProviderSpecializationSemantics(
                    provider,
                    [contract],
                    "The specialization remains compatible with the base contract.",
                    "Fall back only to the explicitly selected base provider."),
                null)),
        new ExtensionDefinition(
            ProgramKitIdentifier.Parse(
                "pkid:extension-point:program-kit:architecture-test-adapter"),
            owner,
            ExtensionKind.AdapterBridge,
            contract,
            new ExtensionSemantics(
                null,
                null,
                null,
                null,
                new AdapterBridgeSemantics(
                    owner,
                    project,
                    "Translate the exact contract without implicit discovery.",
                    "Reject values that cannot be translated losslessly.",
                    "The invoking principal authority is preserved.",
                    "Translation failures are caller-visible.",
                    "Correlation and translation diagnostics are emitted."))),
    ];

    private static ArtifactDecision CreateArtifactDecision(
        ProgramKitIdentifier identity,
        ProgramKitIdentifier owner,
        ProgramKitIdentifier consumer) =>
        new(
            identity,
            owner,
            "Exchange the synthetic typed contract.",
            SupportedArtifactKind.SchemaInstance,
            new ExecutableBehaviorAnswer(
                false,
                "The contract contains no executable behavior."),
            new ValueLifecycleAnswer(
                [ValueLifecycleUse.Validated, ValueLifecycleUse.Exchanged],
                "The value is validated before exchange."),
            new AgentRetrievalAnswer(
                false,
                string.Empty,
                "No agent retrieval is required."),
            new AgentProcedureAnswer(
                false,
                string.Empty,
                string.Empty,
                "No agent procedure is required."),
            new HumanCommunicationAnswer(
                false,
                string.Empty,
                string.Empty,
                "The artifact is machine-readable."),
            new GeneratedNavigationAnswer(
                false,
                [],
                string.Empty,
                "No navigation projection is required."),
            new RepresentationAnswer(
                ArtifactRepresentationRole.Canonical,
                null,
                string.Empty,
                string.Empty),
            new GovernanceAnswer(
                identity,
                owner,
                TestContractValues.Reference(
                    "pkid:schema:program-kit:architecture-test"),
                "The design is the source.",
                "The canonical envelope is digested.",
                [consumer],
                "Major versions carry breaking changes.",
                "Migrations produce a new exact artifact."),
            new DataHandlingAnswer(
                false,
                "No sensitive values are present.",
                "No values are externalized.",
                false,
                "Canonical values contain no ephemeral state."),
            "The contract is a canonical, schema-governed instance.");

    private static ArtifactDecision CreateProjectionDecision(
        ProgramKitIdentifier identity,
        ProgramKitIdentifier canonicalIdentity,
        ProgramKitIdentifier owner) =>
        new(
            identity,
            owner,
            "Navigate the synthetic architecture.",
            SupportedArtifactKind.GeneratedIndex,
            new ExecutableBehaviorAnswer(
                false,
                "The generated index contains no executable behavior."),
            new ValueLifecycleAnswer(
                [ValueLifecycleUse.Compared, ValueLifecycleUse.Digested],
                "The generated projection is compared and digested."),
            new AgentRetrievalAnswer(
                false,
                string.Empty,
                "No agent retrieval is required."),
            new AgentProcedureAnswer(
                false,
                string.Empty,
                string.Empty,
                "No agent procedure is required."),
            new HumanCommunicationAnswer(
                false,
                string.Empty,
                string.Empty,
                "The index is machine-readable navigation."),
            new GeneratedNavigationAnswer(
                true,
                [canonicalIdentity],
                "Project stable navigation from the canonical contract.",
                "Navigation is generated from the canonical artifact."),
            new RepresentationAnswer(
                ArtifactRepresentationRole.Projection,
                canonicalIdentity,
                "Project stable navigation from the canonical contract.",
                "The projection omits contract implementation detail."),
            new GovernanceAnswer(
                identity,
                owner,
                TestContractValues.Reference(
                    "pkid:schema:program-kit:architecture-test-index"),
                "The canonical contract is the exact source.",
                "The generated index envelope is digested.",
                [owner],
                "Regenerate when its canonical source changes.",
                "Regenerate rather than transform the projection."),
            new DataHandlingAnswer(
                false,
                "No sensitive values are present.",
                "No values are externalized.",
                false,
                "The projection contains no ephemeral state."),
            "A generated index is a projection of the canonical contract.");

    private static ArchitectureBoundarySet CreateBoundaries(
        ProgramKitIdentifier owner) =>
        new(
            CreateBoundary(owner, "Security"),
            CreateBoundary(owner, "Authority"),
            CreateBoundary(owner, "Secrets"),
            CreateBoundary(owner, "Persistence"),
            CreateBoundary(owner, "Failure"),
            CreateBoundary(owner, "Concurrency"),
            CreateBoundary(owner, "Cancellation"),
            CreateBoundary(owner, "Observability"),
            CreateBoundary(owner, "Compatibility"));

    private static BoundaryDefinition CreateBoundary(
        ProgramKitIdentifier owner,
        string name) =>
        new(
            owner,
            $"{name} is explicitly bounded.",
            [$"{name} behavior is deterministic."],
            [$"{name} behavior outside the contract is excluded."]);

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(diagnostic =>
                $"{diagnostic.Id} {diagnostic.Path}: {diagnostic.Message}"));
}
