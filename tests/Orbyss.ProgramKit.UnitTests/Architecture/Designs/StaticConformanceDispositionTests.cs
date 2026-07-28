using System.Collections.Immutable;

namespace Orbyss.ProgramKit.UnitTests.Architecture.Designs;

[TestClass]
public sealed class StaticConformanceDispositionTests
{
    private static readonly ArtifactReference Gate =
        Reference("pkid:gate:consumer:layered-build");
    private static readonly ArtifactReference Matrix =
        Reference("pkid:activation-matrix:consumer:layered-build");
    private static readonly ArtifactReference GateDesign =
        Reference("pkid:design:consumer:layered-build-gate");
    private static readonly ArtifactReference EmptyAcceptance =
        Reference("pkid:decision:consumer:accepted-empty-static-conformance");

    [TestMethod]
    public void EveryExplicitSupportedDispositionHasAValidExactForm()
    {
        StaticConformanceDispositionValidator sut = new();
        var values = new[]
        {
            Create(
                StaticConformanceDispositionKind.ReuseExisting,
                [new StaticConformanceGateSelection(Gate, Matrix)],
                [],
                null,
                []),
            Create(
                StaticConformanceDispositionKind.ExtendExisting,
                [new StaticConformanceGateSelection(Gate, Matrix)],
                [GateDesign],
                null,
                []),
            Create(
                StaticConformanceDispositionKind.CreateNew,
                [],
                [GateDesign],
                null,
                []),
            Create(
                StaticConformanceDispositionKind.NotJustified,
                [],
                [],
                EmptyAcceptance,
                []),
            Create(
                StaticConformanceDispositionKind.BlockedUnavailable,
                [],
                [],
                null,
                ["The required consumer-owned analyzer is unavailable."]),
        };

        foreach (var value in values)
        {
            var result = sut.Validate(value);

            Assert.IsTrue(result.IsValid, Format(result));
        }
    }

    [TestMethod]
    public void MissingImplicitAndUnacceptedEmptyFormsFailClosed()
    {
        StaticConformanceDispositionValidator sut = new();

        var missing = sut.Validate(null!);
        var implicitEmpty = sut.Validate(Create(
            StaticConformanceDispositionKind.ReuseExisting,
            [],
            [],
            null,
            []));
        var unacceptedEmpty = sut.Validate(Create(
            StaticConformanceDispositionKind.NotJustified,
            [],
            [],
            null,
            []));

        Assert.IsFalse(missing.IsValid);
        Assert.IsFalse(implicitEmpty.IsValid);
        Assert.IsFalse(unacceptedEmpty.IsValid);
        Assert.IsTrue(missing.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == ArchitectureDiagnosticIds.Pkarc700));
        Assert.IsTrue(implicitEmpty.Diagnostics.Any(static diagnostic =>
            diagnostic.Path == "/gateSelections"));
        Assert.IsTrue(unacceptedEmpty.Diagnostics.Any(static diagnostic =>
            diagnostic.Path == "/emptySelectionAcceptance"));
    }

    [TestMethod]
    public void BlockedUnavailableCannotMasqueradeAsAcceptedEmpty()
    {
        StaticConformanceDispositionValidator sut = new();
        var invalid = Create(
            StaticConformanceDispositionKind.BlockedUnavailable,
            [],
            [],
            EmptyAcceptance,
            []);

        var result = sut.Validate(invalid);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Path == "/blockers"));
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Path == "/emptySelectionAcceptance"));
    }

    [TestMethod]
    public void V1ToV2MigrationRequiresSuppliedDecisionAndIsRepeatable()
    {
        var source = CreateLegacyDesign();
        var disposition = Reference(
            "pkid:static-conformance-disposition:consumer:software");
        var sourceSnapshot = source with { };
        var first = ArchitectureDesignV1ToV2Migration.Migrate(source, disposition);
        var second = ArchitectureDesignV1ToV2Migration.Migrate(source, disposition);

        Assert.AreEqual(first, second);
        Assert.AreEqual(sourceSnapshot, source);
        Assert.AreEqual(disposition, first.StaticConformanceDisposition);
        Assert.ThrowsExactly<ArgumentNullException>(() =>
            ArchitectureDesignV1ToV2Migration.Migrate(source, null!));
    }

    [TestMethod]
    public void ArchitectureV2RequiresDispositionInstanceRatherThanItsSchema()
    {
        ArchitectureDesignValidator v1Validator = new(
            new ArtifactDecisionValidator(
                new SupportedArtifactKindOwnershipResolver()));
        ArchitectureDesignV2Validator sut = new(v1Validator);
        var exact = ArchitectureDesignV1ToV2Migration.Migrate(
            CreateLegacyDesign(),
            Reference("pkid:static-conformance-disposition:consumer:software"));
        var schema = exact with
        {
            StaticConformanceDisposition = Reference(
                "pkid:schema:program-kit:static-conformance-disposition"),
        };

        var exactResult = sut.Validate(exact);
        var schemaResult = sut.Validate(schema);

        Assert.IsFalse(exactResult.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == ArchitectureDiagnosticIds.Pkarc711));
        Assert.IsTrue(schemaResult.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == ArchitectureDiagnosticIds.Pkarc711));
    }

    [TestMethod]
    public void AlphaMigrationsAreDeterministicAndRequireExactAlphaCounterparts()
    {
        var legacyDisposition = Reference(
            "pkid:static-conformance-disposition:consumer:software");
        var versionTwo = ArchitectureDesignV1ToV2Migration.Migrate(
            CreateLegacyDesign(),
            legacyDisposition);
        var alphaDisposition = Reference(
            "pkid:static-conformance-disposition:consumer:software",
            "0.1.0-alpha.1");
        var firstDesign = ArchitectureDesignV2ToAlpha2Migration.Migrate(
            versionTwo,
            alphaDisposition);
        var secondDesign = ArchitectureDesignV2ToAlpha2Migration.Migrate(
            versionTwo,
            alphaDisposition);
        ArchitectureDesignValidator versionOneValidator = new(
            new ArtifactDecisionValidator(
                new SupportedArtifactKindOwnershipResolver()));
        ArchitectureDesignAlpha2Validator designValidator =
            new(versionOneValidator);

        Assert.AreEqual(firstDesign, secondDesign);
        Assert.AreEqual(alphaDisposition, firstDesign.StaticConformanceDisposition);
        Assert.IsFalse(designValidator.Validate(firstDesign).Diagnostics.Any(
            static diagnostic =>
                diagnostic.Id == ArchitectureDiagnosticIds.Pkarc711));
        Assert.IsTrue(designValidator.Validate(firstDesign with
        {
            StaticConformanceDisposition = legacyDisposition,
        }).Diagnostics.Any(static diagnostic =>
            diagnostic.Id == ArchitectureDiagnosticIds.Pkarc711));

        var sourceDisposition = Create(
            StaticConformanceDispositionKind.NotJustified,
            [],
            [],
            EmptyAcceptance,
            []);
        var alphaDesign = Reference(
            "pkid:design:consumer:software",
            "0.1.0-alpha.2");
        var firstDisposition =
            StaticConformanceDispositionV1ToAlpha1Migration.Migrate(
                sourceDisposition,
                alphaDesign);
        var secondDisposition =
            StaticConformanceDispositionV1ToAlpha1Migration.Migrate(
                sourceDisposition,
                alphaDesign);
        StaticConformanceDispositionAlpha1Validator dispositionValidator =
            new(new StaticConformanceDispositionValidator());

        Assert.AreEqual(firstDisposition, secondDisposition);
        Assert.AreEqual(alphaDesign, firstDisposition.SoftwareDesign);
        Assert.IsTrue(dispositionValidator.Validate(firstDisposition).IsValid);
        Assert.IsFalse(dispositionValidator.Validate(firstDisposition with
        {
            SoftwareDesign = Reference(
                "pkid:design:consumer:software",
                "2.0.0"),
        }).IsValid);
    }

    private static StaticConformanceDisposition Create(
        StaticConformanceDispositionKind kind,
        ImmutableArray<StaticConformanceGateSelection> selections,
        ImmutableArray<ArtifactReference> linkedDesigns,
        ArtifactReference? emptyAcceptance,
        ImmutableArray<string> blockers) =>
        new(
            Reference("pkid:design:consumer:software"),
            [
                new StaticInvariantAllocation(
                    new ProgramKitIdentifier(
                        "pkid:invariant:consumer:no-cross-boundary-reference"),
                    "A consumer boundary is not referenced illegally.",
                    StaticConformanceEnforcementLayer.ArchitectureTest,
                    "The invariant depends on the declared architecture graph."),
            ],
            kind,
            selections,
            linkedDesigns,
            "The exact disposition was selected for this design.",
            ["Runtime behavior remains outside static proof."],
            ["Business correctness is not statically proven."],
            new StaticConformanceDecisionSource(
                Reference("pkid:decision-source:consumer:software-design"),
                "/staticConformanceDisposition"),
            emptyAcceptance,
            blockers);

    private static ArchitectureDesignDocument CreateLegacyDesign() =>
        new(
            "Legacy",
            "Readable v1 migration source.",
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            [],
            null!,
            [],
            []);

    private static ArtifactReference Reference(
        string identity,
        string version = "1.0.0") =>
        new(
            new ProgramKitIdentifier(identity),
            new SemanticVersion(version),
            new Sha256Digest(
                "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"));

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(static diagnostic =>
                $"{diagnostic.Id} {diagnostic.Path}: {diagnostic.Message}"));
}
