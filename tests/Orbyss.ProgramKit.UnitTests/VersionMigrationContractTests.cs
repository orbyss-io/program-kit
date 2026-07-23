using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.UnitTests;

[TestClass]
public sealed class VersionMigrationContractTests
{
    [TestMethod]
    public void VersionMapRequiresAnInRangeExactIdentityVersionAndDigestResolution()
    {
        var source = TestContractValues.Reference(
            "pkid:contract:program-kit:source-contract");
        var target = TestContractValues.Reference(
            "pkid:schema:program-kit:target-schema",
            "2.0.0");
        var map = CreateVersionMap(source, target);

        var valid = new VersionMapDocumentValidator().Validate(map);
        var outsideRange = map with
        {
            Edges =
            [
                map.Edges[0] with
                {
                    AcceptedRange = SemanticVersionRange.Parse("[1.0.0,2.0.0)"),
                },
            ],
        };
        var wrongDigest = map with
        {
            Edges =
            [
                map.Edges[0] with
                {
                    Resolution = target with { Digest = AlternateDigest },
                },
            ],
        };

        var rangeResult = new VersionMapDocumentValidator().Validate(outsideRange);
        var digestResult = new VersionMapDocumentValidator().Validate(wrongDigest);

        Assert.IsTrue(valid.IsValid, Format(valid));
        Assert.IsFalse(rangeResult.IsValid);
        Assert.IsTrue(rangeResult.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ArtifactDiagnosticIds.InvalidVersionMap &&
            diagnostic.Path == "/edges/0/resolution/version"));
        Assert.IsFalse(digestResult.IsValid);
        Assert.IsTrue(digestResult.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ArtifactDiagnosticIds.InvalidVersionMap &&
            diagnostic.Path == "/edges/0/resolution"));
    }

    [TestMethod]
    public void VersionMapRejectsConflictingDigestsForOneSemanticRevision()
    {
        var revision = TestContractValues.Reference(
            "pkid:contract:program-kit:conflicting-contract");
        var conflicting = revision with { Digest = AlternateDigest };
        var map = new VersionMapDocument(
            [
                CreateNode(revision),
                CreateNode(conflicting),
            ],
            []);

        var result = new VersionMapDocumentValidator().Validate(map);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ArtifactDiagnosticIds.RevisionDigestConflict));
    }

    [TestMethod]
    public void VersionSelectionBindsObservedAndTargetToOneExactIdentity()
    {
        var identity = ProgramKitIdentifier.Parse(
            "pkid:contract:program-kit:selected-contract");
        var observed = TestContractValues.Reference(identity.Value, "1.0.0");
        var target = TestContractValues.Reference(identity.Value, "2.0.0");
        var selection = new VersionSelectionDocument(
            TestContractValues.Reference(
                "pkid:version-map:program-kit:baseline"),
            [
                new VersionSelection(
                    identity,
                    observed,
                    target,
                    ProgramKitIdentifier.Parse(
                        "pkid:domain:program-kit:artifacts")),
            ]);

        var valid = new VersionSelectionDocumentValidator().Validate(selection);
        var mismatched = selection with
        {
            Selections =
            [
                selection.Selections[0] with
                {
                    Target = TestContractValues.Reference(
                        "pkid:contract:program-kit:different-contract",
                        "2.0.0"),
                },
            ],
        };

        var invalid = new VersionSelectionDocumentValidator().Validate(mismatched);

        Assert.IsTrue(valid.IsValid, Format(valid));
        Assert.IsFalse(invalid.IsValid);
        Assert.IsTrue(invalid.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ArtifactDiagnosticIds.InvalidVersionSelection &&
            diagnostic.Path == "/selections/0/target/identity"));
    }

    [TestMethod]
    public void MigrationDefinitionEnforcesDeterminismAndReviewedLoss()
    {
        var identity = ProgramKitIdentifier.Parse(
            "pkid:artifact:program-kit:migrated-value");
        var definition = new MigrationDefinition(
            identity,
            SemanticVersionRange.Parse("[1.0.0,2.0.0)"),
            TestContractValues.Reference(identity.Value, "2.0.0"),
            MigrationMode.ArtifactTransform,
            [],
            MigrationLossPolicy.Lossless,
            true,
            true,
            MigrationFailurePolicy.FailBeforeWrite,
            TestContractValues.Reference(
                "pkid:implementation:program-kit:migrated-value"),
            [
                TestContractValues.Reference(
                    "pkid:fixture:program-kit:migrated-value"),
            ]);

        var valid = new MigrationDefinitionValidator().Validate(definition);
        var nondeterministic = new MigrationDefinitionValidator().Validate(
            definition with { IsDeterministic = false });
        var unreviewedLoss = new MigrationDefinitionValidator().Validate(
            definition with
            {
                Mode = MigrationMode.SourceGuidance,
                LossPolicy = MigrationLossPolicy.ExplicitlyLossy,
            });

        Assert.IsTrue(valid.IsValid, Format(valid));
        Assert.IsFalse(nondeterministic.IsValid);
        Assert.IsTrue(nondeterministic.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ArtifactDiagnosticIds.InvalidMigrationDefinition &&
            diagnostic.Path == "/isDeterministic"));
        Assert.IsFalse(unreviewedLoss.IsValid);
        Assert.IsTrue(unreviewedLoss.Diagnostics.Any(diagnostic =>
            diagnostic.Id == ArtifactDiagnosticIds.InvalidMigrationDefinition &&
            diagnostic.Path == "/preconditions"));
    }

    [TestMethod]
    public void DisjointMigrationRootsNeedOnlyTheCausalPathsThatReachEachImpact()
    {
        var assessment = CreateDisjointAssessment();

        var result = new MigrationAssessmentValidator().Validate(assessment);

        Assert.IsTrue(result.IsValid, Format(result));
    }

    [TestMethod]
    public void MigrationDispositionsRequireConsistentActions()
    {
        var assessment = CreateDisjointAssessment();
        var inconsistent = assessment with
        {
            Impacts =
            [
                assessment.Impacts[0] with
                {
                    Disposition = MigrationTerminalDisposition.UnaffectedWithProof,
                    RequiredActions = [MigrationRequiredAction.Retest],
                },
                assessment.Impacts[1] with
                {
                    Disposition = MigrationTerminalDisposition.CompatibleAfterActions,
                    RequiredActions = [],
                },
            ],
        };

        var result = new MigrationAssessmentValidator().Validate(inconsistent);

        Assert.IsFalse(result.IsValid);
        Assert.AreEqual(
            2,
            result.Diagnostics.Count(diagnostic =>
                diagnostic.Id == ArtifactDiagnosticIds.InvalidMigrationDisposition));
    }

    [TestMethod]
    public void DurableVersionAndMigrationPayloadsDoNotRepeatTheirOwnEnvelopeIdentity()
    {
        AssertPublicProperties<VersionMapDocument>("Nodes", "Edges");
        AssertPublicProperties<VersionSelectionDocument>(
            "InputVersionMap",
            "Selections");
        AssertPublicProperties<MigrationDefinition>(
            "SourceIdentity",
            "SourceRange",
            "Target",
            "Mode",
            "Preconditions",
            "LossPolicy",
            "IsDeterministic",
            "IsIdempotent",
            "FailurePolicy",
            "ImplementationReference",
            "FixtureReferences");
        AssertPublicProperties<MigrationAssessment>(
            "VersionMapReference",
            "VersionSelectionReference",
            "ChangedRevisions",
            "Impacts",
            "Waves");
    }

    private static Sha256Digest AlternateDigest =>
        Sha256Digest.Parse($"sha256:{new string('b', 64)}");

    private static VersionMapDocument CreateVersionMap(
        ArtifactReference source,
        ArtifactReference target) =>
        new(
            [
                CreateNode(source),
                CreateNode(target),
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
                    [
                        TestContractValues.Reference(
                            "pkid:evidence:program-kit:source-to-target"),
                    ]),
            ]);

    private static VersionRevisionNode CreateNode(
        ArtifactReference revision) =>
        new(
            revision,
            VersionBoundaryKind.Contract,
            ProgramKitIdentifier.Parse(
                "pkid:domain:program-kit:artifacts"),
            [
                TestContractValues.Reference(
                    "pkid:evidence:program-kit:version-node"),
            ]);

    private static MigrationAssessment CreateDisjointAssessment()
    {
        var firstObserved = TestContractValues.Reference(
            "pkid:contract:program-kit:first-root",
            "1.0.0");
        var firstTarget = TestContractValues.Reference(
            firstObserved.Identity.Value,
            "2.0.0");
        var secondObserved = TestContractValues.Reference(
            "pkid:contract:program-kit:second-root",
            "1.0.0");
        var secondTarget = TestContractValues.Reference(
            secondObserved.Identity.Value,
            "2.0.0");
        var owner = ProgramKitIdentifier.Parse(
            "pkid:domain:program-kit:artifacts");

        return new MigrationAssessment(
            TestContractValues.Reference(
                "pkid:version-map:program-kit:migration-input"),
            TestContractValues.Reference(
                "pkid:version-selection:program-kit:migration-targets"),
            [firstObserved, secondObserved],
            [
                new MigrationImpact(
                    firstObserved,
                    firstTarget,
                    owner,
                    MigrationTerminalDisposition.CompatibleAfterActions,
                    [MigrationRequiredAction.Retest],
                    [
                        TestContractValues.Reference(
                            "pkid:evidence:program-kit:first-impact"),
                    ],
                    [new MigrationCausalPath(firstObserved, [])],
                    "Only the first root reaches this impact."),
                new MigrationImpact(
                    secondObserved,
                    secondTarget,
                    owner,
                    MigrationTerminalDisposition.CompatibleAfterActions,
                    [MigrationRequiredAction.Recompile],
                    [
                        TestContractValues.Reference(
                            "pkid:evidence:program-kit:second-impact"),
                    ],
                    [new MigrationCausalPath(secondObserved, [])],
                    "Only the second root reaches this impact."),
            ],
            [
                new MigrationWave(
                    0,
                    [
                        new MigrationCohort(
                            ProgramKitIdentifier.Parse(
                                "pkid:migration-cohort:program-kit:first-root"),
                            [firstTarget]),
                        new MigrationCohort(
                            ProgramKitIdentifier.Parse(
                                "pkid:migration-cohort:program-kit:second-root"),
                            [secondTarget]),
                    ]),
            ]);
    }

    private static void AssertPublicProperties<T>(params string[] expected)
    {
        var actual = typeof(T)
            .GetProperties()
            .Select(property => property.Name)
            .ToArray();

        CollectionAssert.AreEquivalent(expected, actual);
    }

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(diagnostic =>
                $"{diagnostic.Id} {diagnostic.Path}: {diagnostic.Message}"));
}
