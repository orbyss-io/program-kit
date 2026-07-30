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
    private static readonly ArtifactReference SchemaReferenceAlpha2 =
        new(
            new ProgramKitIdentifier("pkid:schema:program-kit:open-console"),
            new SemanticVersion("0.1.0-alpha.2"),
            new Sha256Digest(
                "sha256:752af49c54028c23910d034e23fe79affedb42cf4e719a06ff5e884b63fdc2c8"));
    private static readonly ProgramKitSchemaResource SchemaAlpha2 =
        new(
            SchemaReferenceAlpha2,
            new Uri(
                "https://schemas.orbyss.io/program-kit/open-console/0.1.0-alpha.2/schema.json",
                UriKind.Absolute),
            "open-console-0.1.0-alpha.2.schema.json",
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
                            "pkid:design-amendment:program-kit:consumer-contract-surface-hardening"),
                        new SemanticVersion("0.1.0-alpha.1"),
                        new Sha256Digest(
                            "sha256:dc29a4be4fba94801041fc57fb95c4e21780c4db3fcb5376b31b34041ac81f37")),
                    new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:plan-amendment:program-kit:consumer-contract-surface-hardening"),
                        new SemanticVersion("0.1.0-alpha.1"),
                        new Sha256Digest(
                            "sha256:c8b6a2ce5740532204b90202180ebbaa4050b1541da5cbd2401e1f1b89a9c499")),
                ],
                new ProgramKitIdentifier(
                    "pkid:project:program-kit:open-console"),
                "pkcj-w040-approved-review-set-0-1-0-alpha-1"),
            new ArtifactCompatibility(
                new ProgramKitIdentifier(
                    "pkid:contract:program-kit:schema-compatibility-policy"),
                [
                    new CompatibilityClaim(
                        CompatibilityDimension.WireRead,
                        CompatibilityClassification.ConditionallyCompatible,
                        [
                            "The alpha.2 writer requires explicit operation schema sets and distinct positive host exit-code roles.",
                        ]),
                    new CompatibilityClaim(
                        CompatibilityDimension.WireWrite,
                        CompatibilityClassification.CompatibleAdditive,
                        []),
                ],
                new SemanticVersionRange("[0.1.0-alpha.2]"),
                new SemanticVersionRange("[0.1.0-alpha.2]"),
                []));

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:open-console-schemas");

    /// <inheritdoc />
    public SemanticVersion Version { get; } = new("0.1.0-alpha.2");

    /// <inheritdoc />
    public ImmutableArray<ProgramKitSchemaResource> Resources =>
        [Schema, SchemaAlpha2];

    /// <inheritdoc />
    public Stream OpenRead(ArtifactReference schemaReference)
    {
        ArgumentNullException.ThrowIfNull(schemaReference);
        if (schemaReference != SchemaReference &&
            schemaReference != SchemaReferenceAlpha2)
        {
            throw new KeyNotFoundException(
                string.Concat(
                    "The exact Open Console schema is not registered: ",
                    schemaReference.Identity.Value,
                    "@",
                    schemaReference.Version.Value));
        }

        var assembly = typeof(OpenConsoleSchemaModule).Assembly;
        var suffix = schemaReference == SchemaReferenceAlpha2
            ? "open-console-0.1.0-alpha.2.schema.json"
            : "open-console-1.0.0.schema.json";
        var resourceName = assembly.GetManifestResourceNames().Single(name =>
            name.EndsWith(suffix, StringComparison.Ordinal));
        return assembly.GetManifestResourceStream(resourceName) ??
               throw new InvalidOperationException(
                   "The registered Open Console schema is unavailable.");
    }
}
