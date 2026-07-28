namespace Orbyss.ProgramKit.UnitTests.Workbench.Operations.Versioning;

[TestClass]
public sealed class VersionIntentAndAlphaProgressionTests
{
    [TestMethod]
    public void InventoryAcceptsEveryExplicitIntentWithExactReorderedObservations()
    {
        var inventory = Inventory();
        var observations = inventory.Entries
            .Reverse()
            .Select(static entry => new VersionBearingSourceObservation(
                entry.SourcePath,
                entry.CurrentValue,
                entry.SourceDigest))
            .ToImmutableArray();
        var sut = new VersionIntentInventoryEvaluator(
            new VersionIntentInventoryDocumentValidator());

        var result = sut.Evaluate(
            new VersionIntentInventoryValidationRequest(
                inventory,
                observations,
                observations.Length));

        Assert.IsTrue(result.IsValid, Format(result));
    }

    [TestMethod]
    public void InventoryRejectsContradictoryIntentDisposition()
    {
        var inventory = Inventory();
        var contradictory = inventory with
        {
            Entries =
            [
                inventory.Entries[0] with
                {
                    TransitionDisposition =
                        VersionTransitionDisposition.PreserveExternalSelection,
                },
                .. inventory.Entries[1..],
            ],
        };
        var sut = new VersionIntentInventoryDocumentValidator();

        var result = sut.Validate(contradictory);

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == ArtifactDiagnosticIds.InvalidVersionIntentInventory));
    }

    [TestMethod]
    public void InventoryRejectsIncompleteObservationSet()
    {
        var inventory = Inventory();
        var observations = inventory.Entries
            .Skip(1)
            .Select(static entry => new VersionBearingSourceObservation(
                entry.SourcePath,
                entry.CurrentValue,
                entry.SourceDigest))
            .ToImmutableArray();
        var sut = new VersionIntentInventoryEvaluator(
            new VersionIntentInventoryDocumentValidator());

        var result = sut.Evaluate(
            new VersionIntentInventoryValidationRequest(
                inventory,
                observations,
                inventory.Entries.Length));

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id ==
                WorkbenchDiagnosticIds.InvalidVersionIntentInventoryRequest));
    }

    [TestMethod]
    public void InventoryRejectsDuplicateObservationPath()
    {
        var inventory = Inventory();
        var observations = inventory.Entries
            .Select(static entry => new VersionBearingSourceObservation(
                entry.SourcePath,
                entry.CurrentValue,
                entry.SourceDigest))
            .Append(new VersionBearingSourceObservation(
                inventory.Entries[0].SourcePath,
                inventory.Entries[0].CurrentValue,
                inventory.Entries[0].SourceDigest))
            .ToImmutableArray();
        var sut = new VersionIntentInventoryEvaluator(
            new VersionIntentInventoryDocumentValidator());

        var result = sut.Evaluate(
            new VersionIntentInventoryValidationRequest(
                inventory,
                observations,
                observations.Length));

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id ==
                WorkbenchDiagnosticIds.InvalidVersionIntentInventoryRequest));
    }

    [TestMethod]
    public void ProgressionAcceptsExplicitInitialAlphaRevision()
    {
        var proposal = new AlphaVersionProgressionProposal(
            Id("pkid:schema:program-kit:new-contract"),
            VersionIntent.OwnedArtifactRevision,
            null,
            null,
            null,
            Version("0.1.0-alpha.1"),
            Digest('b'),
            true,
            VersionCompatibilityDisposition.NewIdentity,
            VersionMigrationDisposition.NotRequired,
            [],
            "This is the first owned contract revision.");

        var result = Validator().Validate(
            new AlphaVersionProgressionDocument(Policy(), proposal));

        Assert.IsTrue(result.IsValid, Format(result));
    }

    [TestMethod]
    public void ProgressionAcceptsNextIncompatibleAlphaWithMigration()
    {
        var proposal = ExistingProposal(
            "0.1.0-alpha.2",
            Digest('b'),
            VersionCompatibilityDisposition.Incompatible,
            VersionMigrationDisposition.Required,
            [Reference("pkid:migration:program-kit:test-contract-alpha-2")]);

        var result = Validator().Validate(
            new AlphaVersionProgressionDocument(Policy(), proposal));

        Assert.IsTrue(result.IsValid, Format(result));
    }

    [TestMethod]
    public void ProgressionRejectsSkippedOrdinal()
    {
        var proposal = ExistingProposal(
            "0.1.0-alpha.3",
            Digest('b'),
            VersionCompatibilityDisposition.Compatible,
            VersionMigrationDisposition.NotRequired,
            []);

        var result = Validator().Validate(
            new AlphaVersionProgressionDocument(Policy(), proposal));

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id ==
                WorkbenchDiagnosticIds.InvalidAlphaVersionProgressionProposal));
    }

    [TestMethod]
    public void ProgressionRejectsUnchangedVersionWithChangedDigest()
    {
        var proposal = ExistingProposal(
            "0.1.0-alpha.1",
            Digest('b'),
            VersionCompatibilityDisposition.Unchanged,
            VersionMigrationDisposition.NotRequired,
            []) with
        {
            CanonicalBytesChanged = false,
        };

        var result = Validator().Validate(
            new AlphaVersionProgressionDocument(Policy(), proposal));

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id ==
                WorkbenchDiagnosticIds.InvalidAlphaVersionProgressionProposal));
    }

    [TestMethod]
    public void ProgressionRejectsNonOwnedIntentWithoutSelectingARelease()
    {
        var proposal = ExistingProposal(
            "0.1.0-alpha.2",
            Digest('b'),
            VersionCompatibilityDisposition.Compatible,
            VersionMigrationDisposition.NotRequired,
            []) with
        {
            Intent = VersionIntent.ProductRelease,
        };

        var result = Validator().Validate(
            new AlphaVersionProgressionDocument(Policy(), proposal));

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id ==
                WorkbenchDiagnosticIds.InvalidAlphaVersionProgressionProposal));
    }

    private static VersionIntentInventoryDocument Inventory()
    {
        return new VersionIntentInventoryDocument(
            ".",
            ["src", "schemas", "evidence", "fixtures"],
            [
                Entry(
                    "pkid:release:program-kit:product",
                    "src/Directory.Build.props",
                    "0.1.0-alpha.1",
                    VersionIntent.ProductRelease,
                    true,
                    null,
                    VersionTransitionDisposition.CoordinateProductRelease,
                    'a'),
                Entry(
                    "pkid:schema:program-kit:test-contract",
                    "schemas/test-contract.schema.json",
                    "1.0.0",
                    VersionIntent.OwnedArtifactRevision,
                    true,
                    1,
                    VersionTransitionDisposition.MigrateOwnedRevision,
                    'b'),
                Entry(
                    "pkid:package:external:test-library",
                    "src/ExternalSelection.props",
                    "13.2.1",
                    VersionIntent.ExternalSelection,
                    true,
                    null,
                    VersionTransitionDisposition.PreserveExternalSelection,
                    'c'),
                Entry(
                    "pkid:evidence:program-kit:historic-result",
                    "evidence/historic.json",
                    "3.0.0",
                    VersionIntent.HistoricalEvidenceRevision,
                    false,
                    null,
                    VersionTransitionDisposition.PreserveHistoricalEvidence,
                    'd'),
                Entry(
                    "pkid:fixture:program-kit:legacy-consumer",
                    "fixtures/legacy.json",
                    "4.0.0",
                    VersionIntent.FixtureRevision,
                    false,
                    null,
                    VersionTransitionDisposition.PreserveFixture,
                    'e'),
            ],
            [Reference("pkid:evidence:program-kit:version-inventory-scan")]);
    }

    private static VersionIntentInventoryEntry Entry(
        string identity,
        string path,
        string currentValue,
        VersionIntent intent,
        bool isActive,
        int? ordinal,
        VersionTransitionDisposition disposition,
        char digestMarker) =>
        new(
            Id(identity),
            Id("pkid:domain:program-kit:version-governance"),
            path,
            currentValue,
            Digest(digestMarker),
            intent,
            isActive,
            ordinal,
            disposition);

    private static AlphaVersionProgressionProposal ExistingProposal(
        string proposedVersion,
        Sha256Digest proposedDigest,
        VersionCompatibilityDisposition compatibility,
        VersionMigrationDisposition migration,
        ImmutableArray<ArtifactReference> migrations) =>
        new(
            Id("pkid:schema:program-kit:test-contract"),
            VersionIntent.OwnedArtifactRevision,
            Version("0.1.0-alpha.1"),
            Digest('a'),
            1,
            Version(proposedVersion),
            proposedDigest,
            true,
            compatibility,
            migration,
            migrations,
            "The caller explicitly classified this proposal.");

    private static AlphaVersionProgressionPolicy Policy() =>
        new(
            Reference(
                "pkid:policy:program-kit:alpha-version-progression",
                "0.1.0-alpha.1"),
            Version("0.1.0"),
            "alpha",
            1,
            1,
            Id("pkid:contract:program-kit:version-progression-policy"));

    private static AlphaVersionProgressionValidator Validator() =>
        new(new AlphaVersionProgressionDocumentValidator());

    private static ProgramKitIdentifier Id(string value) =>
        ProgramKitIdentifier.Parse(value);

    private static SemanticVersion Version(string value) =>
        SemanticVersion.Parse(value);

    private static Sha256Digest Digest(char marker) =>
        Sha256Digest.Parse(string.Concat("sha256:", new string(marker, 64)));

    private static ArtifactReference Reference(
        string identity,
        string version = "1.0.0") =>
        new(Id(identity), Version(version), Digest('a'));

    private static string Format(ProgramKitValidationResult result) =>
        string.Join(
            Environment.NewLine,
            result.Diagnostics.Select(static diagnostic =>
                string.Concat(
                    diagnostic.Id,
                    " ",
                    diagnostic.Path,
                    " ",
                    diagnostic.Message)));
}
