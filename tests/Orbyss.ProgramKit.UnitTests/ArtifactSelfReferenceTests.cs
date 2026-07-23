using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.UnitTests;

[TestClass]
public sealed class ArtifactSelfReferenceTests
{
    [TestMethod]
    public void EnvelopeRejectsItsOwnExactReferenceAsAProvenanceInput()
    {
        var envelope = CreateEnvelope(
            "pkid:fixture:program-kit:self-provenance",
            "schema-instance",
            "document");
        var selfReference = CreateSelfReference(envelope);
        var invalid = envelope with
        {
            Provenance = envelope.Provenance with
            {
                SourceInputs = [selfReference],
            },
        };

        var result = new ArtifactEnvelopeValidator<string>().Validate(invalid);

        AssertSelfReference(result, "/provenance/sourceInputs/0");
    }

    [TestMethod]
    public void VersionMapEnvelopeRejectsSelfReferencesAcrossItsGraph()
    {
        var map = CreateVersionMap();
        var baselineEnvelope = CreateEnvelope(
            "pkid:version-map:program-kit:self-map",
            "version-map",
            map);
        var selfReference = CreateSelfReference(baselineEnvelope);
        var cases = new (VersionMapDocument Document, string Path)[]
        {
            (
                map with
                {
                    Nodes = [map.Nodes[0] with { Revision = selfReference }, map.Nodes[1]],
                },
                "/document/nodes/0/revision"),
            (
                map with
                {
                    Nodes =
                    [
                        map.Nodes[0] with { EvidenceReferences = [selfReference] },
                        map.Nodes[1],
                    ],
                },
                "/document/nodes/0/evidenceReferences/0"),
            (
                map with
                {
                    Edges = [map.Edges[0] with { Source = selfReference }],
                },
                "/document/edges/0/source"),
            (
                map with
                {
                    Edges = [map.Edges[0] with { Resolution = selfReference }],
                },
                "/document/edges/0/resolution"),
            (
                map with
                {
                    Edges = [map.Edges[0] with { EvidenceReferences = [selfReference] }],
                },
                "/document/edges/0/evidenceReferences/0"),
        };

        foreach (var testCase in cases)
        {
            var result = new VersionMapDocumentValidator().Validate(
                baselineEnvelope with { Document = testCase.Document });
            AssertSelfReference(result, testCase.Path);
        }
    }

    [TestMethod]
    public void VersionSelectionEnvelopeRejectsItsOwnExactInputReference()
    {
        var selection = new VersionSelectionDocument(
            TestContractValues.Reference(
                "pkid:version-map:program-kit:placeholder-map"),
            [
                new VersionSelection(
                    ProgramKitIdentifier.Parse(
                        "pkid:contract:program-kit:selected-contract"),
                    TestContractValues.Reference(
                        "pkid:contract:program-kit:selected-contract"),
                    TestContractValues.Reference(
                        "pkid:contract:program-kit:selected-contract",
                        "2.0.0"),
                    ProgramKitIdentifier.Parse(
                        "pkid:domain:program-kit:artifacts")),
            ]);
        var envelope = CreateEnvelope(
            "pkid:version-map:program-kit:self-selection",
            "version-selection",
            selection);
        var invalid = envelope with
        {
            Document = selection with
            {
                InputVersionMap = CreateSelfReference(envelope),
            },
        };

        var result = new VersionSelectionDocumentValidator().Validate(invalid);

        AssertSelfReference(result, "/document/inputVersionMap");
    }

    [TestMethod]
    public void MigrationDefinitionEnvelopeRejectsItsOwnImplementationReference()
    {
        var sourceIdentity = ProgramKitIdentifier.Parse(
            "pkid:artifact:program-kit:migrated-value");
        var definition = new MigrationDefinition(
            sourceIdentity,
            SemanticVersionRange.Parse("[1.0.0,2.0.0)"),
            TestContractValues.Reference(sourceIdentity.Value, "2.0.0"),
            MigrationMode.ArtifactTransform,
            [],
            MigrationLossPolicy.Lossless,
            true,
            true,
            MigrationFailurePolicy.FailBeforeWrite,
            TestContractValues.Reference(
                "pkid:implementation:program-kit:placeholder-migrator"),
            [
                TestContractValues.Reference(
                    "pkid:fixture:program-kit:migration-definition"),
            ]);
        var envelope = CreateEnvelope(
            "pkid:implementation:program-kit:self-migrator",
            "migration-definition",
            definition);
        var invalid = envelope with
        {
            Document = definition with
            {
                ImplementationReference = CreateSelfReference(envelope),
            },
        };

        var result = new MigrationDefinitionValidator().Validate(invalid);

        AssertSelfReference(result, "/document/implementationReference");
    }

    [TestMethod]
    public void MigrationAssessmentEnvelopeRejectsItsOwnEvidenceReference()
    {
        var assessment = CreateAssessment();
        var envelope = CreateEnvelope(
            "pkid:evidence:program-kit:self-assessment",
            "migration-assessment",
            assessment);
        var invalidImpact = assessment.Impacts[0] with
        {
            RequiredEvidence = [CreateSelfReference(envelope)],
        };
        var invalid = envelope with
        {
            Document = assessment with { Impacts = [invalidImpact] },
        };

        var result = new MigrationAssessmentValidator().Validate(invalid);

        AssertSelfReference(result, "/document/impacts/0/requiredEvidence/0");
    }

    [TestMethod]
    public void EveryChangedRevisionRequiresItsOwnTerminalImpact()
    {
        var assessment = CreateAssessment();
        var missing = TestContractValues.Reference(
            "pkid:contract:program-kit:unassessed-root");
        var invalid = assessment with
        {
            ChangedRevisions = [assessment.ChangedRevisions[0], missing],
        };

        var result = new MigrationAssessmentValidator().Validate(invalid);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(
            result.Diagnostics.Any(diagnostic =>
                diagnostic.Id == ArtifactDiagnosticIds.InvalidMigrationAssessment &&
                diagnostic.Path == "/changedRevisions/1"),
            Format(result));
    }

    private static ArtifactEnvelope<TDocument> CreateEnvelope<TDocument>(
        string identity,
        string kind,
        TDocument document)
    {
        var version = SemanticVersion.Parse("1.0.0");
        var exactVersion = SemanticVersionRange.Parse("[1.0.0]");
        return new ArtifactEnvelope<TDocument>(
            new ArtifactContract(
                ProgramKitIdentifier.Parse("pkid:schema:program-kit:test-document"),
                version),
            new ArtifactIdentity(
                ProgramKitIdentifier.Parse(identity),
                kind,
                version,
                ProgramKitIdentifier.Parse("pkid:domain:program-kit:artifacts"),
                ArtifactStatus.Implemented,
                [ProgramKitIdentifier.Parse("pkid:test:program-kit:unit-tests")]),
            new ArtifactCompatibility(
                ProgramKitIdentifier.Parse(
                    "pkid:contract:program-kit:compatibility-policy"),
                [
                    new CompatibilityClaim(
                        CompatibilityDimension.WireRead,
                        CompatibilityClassification.CompatibleAdditive,
                        []),
                ],
                exactVersion,
                exactVersion,
                []),
            new ArtifactProvenance(
                [
                    TestContractValues.Reference(
                        "pkid:design:program-kit:test-source"),
                ],
                ProgramKitIdentifier.Parse("pkid:project:program-kit:unit-tests"),
                "self-reference-test"),
            new ArtifactRepresentation(
                TestContractValues.Profile(
                    "pkid:profile:program-kit:json-contracts"),
                TestContractValues.Profile(
                    "pkid:profile:program-kit:canonical-json-rfc8785"),
                "application/json"),
            new ArtifactIntegrity("sha256", TestContractValues.Digest),
            document);
    }

    private static ArtifactReference CreateSelfReference<TDocument>(
        ArtifactEnvelope<TDocument> envelope) =>
        new(
            envelope.Artifact.Id,
            envelope.Artifact.Version,
            envelope.Integrity.Digest);

    private static VersionMapDocument CreateVersionMap()
    {
        var source = TestContractValues.Reference(
            "pkid:contract:program-kit:source-contract");
        var target = TestContractValues.Reference(
            "pkid:schema:program-kit:target-schema",
            "2.0.0");
        var evidence = TestContractValues.Reference(
            "pkid:evidence:program-kit:version-topology");
        var owner = ProgramKitIdentifier.Parse(
            "pkid:domain:program-kit:artifacts");
        return new VersionMapDocument(
            [
                new VersionRevisionNode(
                    source,
                    VersionBoundaryKind.Contract,
                    owner,
                    [evidence]),
                new VersionRevisionNode(
                    target,
                    VersionBoundaryKind.Schema,
                    owner,
                    [evidence]),
            ],
            [
                new VersionDependencyEdge(
                    ProgramKitIdentifier.Parse(
                        "pkid:version-edge:program-kit:source-to-target"),
                    source,
                    target.Identity,
                    VersionDependencyKind.WireSchemaOf,
                    SemanticVersionRange.Parse("[2.0.0]"),
                    target,
                    DependencyExposure.Public,
                    [CompatibilityDimension.WireRead],
                    [evidence]),
            ]);
    }

    private static MigrationAssessment CreateAssessment()
    {
        var observed = TestContractValues.Reference(
            "pkid:contract:program-kit:changed-root");
        var target = TestContractValues.Reference(observed.Identity.Value, "2.0.0");
        return new MigrationAssessment(
            TestContractValues.Reference(
                "pkid:version-map:program-kit:migration-input"),
            TestContractValues.Reference(
                "pkid:version-selection:program-kit:migration-targets"),
            [observed],
            [
                new MigrationImpact(
                    observed,
                    target,
                    ProgramKitIdentifier.Parse(
                        "pkid:domain:program-kit:artifacts"),
                    MigrationTerminalDisposition.CompatibleAfterActions,
                    [MigrationRequiredAction.Retest],
                    [
                        TestContractValues.Reference(
                            "pkid:evidence:program-kit:migration-impact"),
                    ],
                    [new MigrationCausalPath(observed, [])],
                    "The changed root is action-complete."),
            ],
            [
                new MigrationWave(
                    0,
                    [
                        new MigrationCohort(
                            ProgramKitIdentifier.Parse(
                                "pkid:migration-cohort:program-kit:changed-root"),
                            [target]),
                    ]),
            ]);
    }

    private static void AssertSelfReference(
        ProgramKitValidationResult result,
        string expectedPath)
    {
        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(
            result.Diagnostics.Any(diagnostic =>
                diagnostic.Id == ArtifactDiagnosticIds.SelfReferentialArtifact &&
                diagnostic.Path == expectedPath),
            Format(result));
    }

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(diagnostic =>
                $"{diagnostic.Id} {diagnostic.Path}: {diagnostic.Message}"));
}
