using System.Globalization;

namespace Orbyss.ProgramKit.UnitTests.Workbench.Operations.Migrations;

[TestClass]
public sealed class MigrationAssessmentEngineTests
{
    private static readonly string[] ExpectedCycleMembers = ["b", "c"];

    [TestMethod]
    public void AssessRetainsAllPathsMakesCyclesAtomicAndOrdersDependencyWaves()
    {
        var fixture = CreateFixture();
        var sut = CreateEngine();

        var result = sut.Assess(fixture);

        Assert.IsTrue(result.IsSuccessful, Format(result.Validation));
        Assert.IsNotNull(result.Value);
        Assert.HasCount(6, result.Value.Impacts);
        var impactC = result.Value.Impacts.Single(static impact =>
            impact.Observed.Identity.Name == "c");
        Assert.HasCount(2, impactC.CausalPaths);
        var cycleCohort = result.Value.Waves
            .SelectMany(static wave => wave.Cohorts)
            .Single(static cohort => cohort.Members.Length == 2);
        Assert.AreSequenceEqual(
            ExpectedCycleMembers,
            cycleCohort.Members.Select(static member => member.Identity.Name).ToArray());
        Assert.AreEqual("a", result.Value.Waves[0].Cohorts[0].Members[0].Identity.Name);
        Assert.AreSequenceEqual(
            Enum.GetValues<MigrationTerminalDisposition>(),
            result.Value.Impacts.Select(static impact => impact.Disposition).ToArray());
        Assert.AreSequenceEqual(
            Enum.GetValues<MigrationRequiredAction>(),
            result.Value.Impacts
                .SelectMany(static impact => impact.RequiredActions)
                .ToArray());
    }

    [TestMethod]
    public void AssessIsCultureInvariantAndRejectsUnknownCompatibility()
    {
        var fixture = CreateFixture();
        var sut = CreateEngine();
        var originalCulture = CultureInfo.CurrentCulture;
        var originalUiCulture = CultureInfo.CurrentUICulture;
        try
        {
            CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("tr-TR");
            CultureInfo.CurrentUICulture = CultureInfo.GetCultureInfo("tr-TR");
            var first = sut.Assess(fixture);
            CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("ar-SA");
            CultureInfo.CurrentUICulture = CultureInfo.GetCultureInfo("ar-SA");
            var second = sut.Assess(fixture);

            Assert.IsTrue(first.IsSuccessful, Format(first.Validation));
            Assert.IsTrue(second.IsSuccessful, Format(second.Validation));
            Assert.IsNotNull(first.Value);
            Assert.IsNotNull(second.Value);
            Assert.AreEqual(Fingerprint(first.Value), Fingerprint(second.Value));
        }
        finally
        {
            CultureInfo.CurrentCulture = originalCulture;
            CultureInfo.CurrentUICulture = originalUiCulture;
        }

        var invalidDecision = fixture.Decisions[0] with
        {
            CompatibilityClaims = fixture.Decisions[0].CompatibilityClaims.SetItem(
                0,
                fixture.Decisions[0].CompatibilityClaims[0] with
                {
                    Classification = CompatibilityClassification.Unknown,
                }),
        };
        var invalid = sut.Assess(fixture with
        {
            Decisions = fixture.Decisions.SetItem(0, invalidDecision),
        });

        Assert.IsFalse(invalid.IsSuccessful);
        Assert.IsTrue(invalid.Validation.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == WorkbenchDiagnosticIds.InvalidMigrationRequest));
    }

    private static MigrationAssessmentEngine CreateEngine()
    {
        IArtifactEnvelopeValidator envelopeValidator =
            new DefaultArtifactEnvelopeValidator();
        IProgramKitSemanticValidator<VersionMapDocument> mapValidator =
            new VersionMapDocumentValidator(envelopeValidator);
        IProgramKitSemanticValidator<VersionSelectionDocument> selectionValidator =
            new VersionSelectionDocumentValidator(envelopeValidator);
        IProgramKitSemanticValidator<MigrationAssessment> assessmentValidator =
            new MigrationAssessmentValidator(envelopeValidator);
        return new MigrationAssessmentEngine(
            mapValidator,
            selectionValidator,
            assessmentValidator);
    }

    private static MigrationAssessmentRequest CreateFixture()
    {
        var observed = new[]
        {
            Reference("a"),
            Reference("b"),
            Reference("c"),
            Reference("d"),
            Reference("e"),
            Reference("f"),
        };
        var nodes = observed
            .Select(static reference => new VersionRevisionNode(
                reference,
                VersionBoundaryKind.Contract,
                ProgramKitIdentifier.Parse("pkid:domain:program-kit:tests"),
                [Evidence("node")]))
            .ToImmutableArray();
        var edges = ImmutableArray.Create(
            Edge("b-a", observed[1], observed[0]),
            Edge("c-a", observed[2], observed[0]),
            Edge("c-b", observed[2], observed[1]),
            Edge("b-c", observed[1], observed[2]),
            Edge("d-c", observed[3], observed[2]),
            Edge("e-d", observed[4], observed[3]),
            Edge("f-e", observed[5], observed[4]));
        var mapReference = TestContractValues.Reference(
            "pkid:version-map:program-kit:test");
        var selectionReference = TestContractValues.Reference(
            "pkid:version-selection:program-kit:test");
        var selections = observed
            .Select((reference, index) => new VersionSelection(
                reference.Identity,
                reference,
                index == 0
                    ? TestContractValues.Reference(reference.Identity.Value, "2.0.0")
                    : reference,
                ProgramKitIdentifier.Parse("pkid:domain:program-kit:tests")))
            .ToImmutableArray();
        var dispositions = Enum.GetValues<MigrationTerminalDisposition>();
        var actions = new[]
        {
            ImmutableArray<MigrationRequiredAction>.Empty,
            [MigrationRequiredAction.Retest],
            [MigrationRequiredAction.Regenerate, MigrationRequiredAction.Recompile],
            [MigrationRequiredAction.RepackageOrRelock, MigrationRequiredAction.MigrateArtifact],
            [MigrationRequiredAction.MigrateConfiguration, MigrationRequiredAction.AddAdapter],
            [MigrationRequiredAction.DrainOrMigratePendingWork],
        };
        var decisions = observed
            .Select((reference, index) => new MigrationBoundaryDecision(
                reference.Identity,
                CompleteCompatibility(),
                dispositions[index],
                actions[index],
                [Evidence(string.Concat("decision-", reference.Identity.Name))],
                string.Concat("Reviewed decision for ", reference.Identity.Value, ".")))
            .ToImmutableArray();
        return new MigrationAssessmentRequest(
            mapReference,
            selectionReference,
            new VersionMapDocument(nodes, edges),
            new VersionSelectionDocument(mapReference, selections),
            decisions,
            MigrationAnalysisLimits.Default);
    }

    private static ImmutableArray<CompatibilityClaim> CompleteCompatibility() =>
        Enum.GetValues<CompatibilityDimension>()
            .Select(static dimension => new CompatibilityClaim(
                dimension,
                CompatibilityClassification.Editorial,
                []))
            .ToImmutableArray();

    private static VersionDependencyEdge Edge(
        string name,
        ArtifactReference source,
        ArtifactReference target) =>
        new(
            ProgramKitIdentifier.Parse(string.Concat("pkid:edge:program-kit:", name)),
            source,
            target.Identity,
            VersionDependencyKind.UsesContract,
            SemanticVersionRange.Parse("[1.0.0]"),
            target,
            DependencyExposure.Private,
            [CompatibilityDimension.SemanticBehavior],
            [Evidence(string.Concat("edge-", name))]);

    private static ArtifactReference Reference(string name) =>
        TestContractValues.Reference(string.Concat("pkid:contract:program-kit:", name));

    private static ArtifactReference Evidence(string name) =>
        TestContractValues.Reference(string.Concat("pkid:evidence:program-kit:", name));

    private static string Fingerprint(MigrationAssessment assessment) =>
        string.Join(
            "|",
            assessment.Waves.SelectMany(static wave => wave.Cohorts)
                .Select(cohort => string.Concat(
                    cohort.Id.Value,
                    ":",
                    string.Join(",", cohort.Members.Select(static member =>
                        member.Identity.Value)))));

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(static diagnostic =>
                string.Concat(diagnostic.Id, " ", diagnostic.Path, " ", diagnostic.Message)));
}
