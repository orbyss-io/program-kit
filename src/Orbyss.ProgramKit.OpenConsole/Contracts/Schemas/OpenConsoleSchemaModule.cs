namespace Orbyss.ProgramKit.OpenConsole.Contracts.Schemas;

/// <summary>Exact language-neutral Open Console schema catalog.</summary>
public sealed class OpenConsoleSchemaModule : IProgramKitSchemaModule
{
    private static readonly ProgramKitIdentifier Owner =
        new("pkid:package:program-kit:open-console");
    private static readonly ArtifactReference SchemaReference =
        new(
            new ProgramKitIdentifier("pkid:schema:program-kit:open-console"),
            new SemanticVersion("1.0.0"),
            new Sha256Digest(
                "sha256:72392d78970462ca3e7344b3b1949bb2dadd0bcdcfb33c802755fb943c0afc15"));
    private static readonly ProgramKitSchemaResource Schema =
        new(
            SchemaReference,
            new Uri(
                "https://schemas.orbyss.io/program-kit/open-console/1.0.0/schema.json",
                UriKind.Absolute),
            "open-console-1.0.0.schema.json",
            "application/schema+json",
            Owner,
            ArtifactStatus.Implemented,
            [
                new ProgramKitIdentifier(
                    "pkid:project:program-kit:open-console"),
                new ProgramKitIdentifier(
                    "pkid:project:program-kit:dotnet"),
                new ProgramKitIdentifier(
                    "pkid:test:program-kit:conformance-tests"),
            ],
            new ArtifactProvenance(
                [
                    new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:design:program-kit:typed-console-host-generation"),
                        new SemanticVersion("1.0.0"),
                        new Sha256Digest(
                            "sha256:72bfa056c3e0f19d1765d9feae9aa5eb4ccb546a07896f2682a276294abcd4ca")),
                    new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:plan:program-kit:typed-console-host-generation"),
                        new SemanticVersion("1.0.0"),
                        new Sha256Digest(
                            "sha256:207c47c0150bb91df564937225fdbb44f30dd2b403f21c6468d6abac70fbe273")),
                ],
                new ProgramKitIdentifier(
                    "pkid:project:program-kit:open-console"),
                "pktch-w010-approved-review-set-1-0-0"),
            new ArtifactCompatibility(
                new ProgramKitIdentifier(
                    "pkid:contract:program-kit:schema-compatibility-policy"),
                [
                    new CompatibilityClaim(
                        CompatibilityDimension.WireRead,
                        CompatibilityClassification.Unknown,
                        []),
                    new CompatibilityClaim(
                        CompatibilityDimension.WireWrite,
                        CompatibilityClassification.Unknown,
                        []),
                ],
                new SemanticVersionRange("[1.0.0]"),
                new SemanticVersionRange("[1.0.0]"),
                []));

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:open-console-schemas");

    /// <inheritdoc />
    public SemanticVersion Version { get; } = new("1.0.0");

    /// <inheritdoc />
    public ImmutableArray<ProgramKitSchemaResource> Resources => [Schema];

    /// <inheritdoc />
    public Stream OpenRead(ArtifactReference schemaReference)
    {
        ArgumentNullException.ThrowIfNull(schemaReference);
        if (schemaReference != SchemaReference)
        {
            throw new KeyNotFoundException(
                string.Concat(
                    "The exact Open Console schema is not registered: ",
                    schemaReference.Identity.Value,
                    "@",
                    schemaReference.Version.Value));
        }

        var assembly = typeof(OpenConsoleSchemaModule).Assembly;
        var resourceName = assembly.GetManifestResourceNames().Single(name =>
            name.EndsWith(
                "open-console-1.0.0.schema.json",
                StringComparison.Ordinal));
        return assembly.GetManifestResourceStream(resourceName) ??
               throw new InvalidOperationException(
                   "The registered Open Console schema is unavailable.");
    }
}
