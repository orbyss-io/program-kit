namespace Orbyss.ProgramKit.UnitTests.TestSupport.Fixtures;

internal static class TestContractValues
{
    public static Sha256Digest Digest { get; } =
        Sha256Digest.Parse($"sha256:{new string('a', 64)}");

    public static ArtifactReference Reference(
        string identity,
        string version = "1.0.0") =>
        new(
            ProgramKitIdentifier.Parse(identity),
            SemanticVersion.Parse(version),
            Digest);

    public static ProfileReference Profile(
        string identity,
        string version = "1.0.0") =>
        new(
            ProgramKitIdentifier.Parse(identity),
            SemanticVersion.Parse(version),
            Digest);

    public static ArtifactEnvelope<TDocument> Envelope<TDocument>(
        string identity,
        string kind,
        TDocument document)
    {
        var exactVersion = SemanticVersion.Parse("1.0.0");
        return new ArtifactEnvelope<TDocument>(
            new ArtifactContract(
                ProgramKitIdentifier.Parse(
                    "pkid:schema:program-kit:test-artifact-envelope"),
                exactVersion),
            new ArtifactIdentity(
                ProgramKitIdentifier.Parse(identity),
                kind,
                exactVersion,
                ProgramKitIdentifier.Parse("pkid:domain:program-kit:tests"),
                ArtifactStatus.Implemented,
                [ProgramKitIdentifier.Parse("pkid:test:program-kit:unit-tests")]),
            new ArtifactCompatibility(
                ProgramKitIdentifier.Parse(
                    "pkid:contract:program-kit:test-compatibility-policy"),
                [
                    new CompatibilityClaim(
                        CompatibilityDimension.SemanticBehavior,
                        CompatibilityClassification.Unknown,
                        []),
                ],
                SemanticVersionRange.Parse("[1.0.0]"),
                SemanticVersionRange.Parse("[1.0.0]"),
                []),
            new ArtifactProvenance(
                [
                    Reference(
                        "pkid:design:program-kit:test-envelope-source"),
                ],
                ProgramKitIdentifier.Parse(
                    "pkid:producer:program-kit:unit-tests"),
                "test-envelope"),
            new ArtifactRepresentation(
                Profile(
                    "pkid:profile:program-kit:test-json-serialization"),
                Profile(
                    "pkid:profile:program-kit:test-json-canonicalization"),
                "application/json"),
            new ArtifactIntegrity("sha256", Digest),
            document);
    }
}
