namespace Orbyss.ProgramKit.SecretResolution.Contracts.Schemas;

/// <summary>Explicit finite schema module owned by SecretResolution.</summary>
public sealed class SecretResolutionSchemaModule : IProgramKitSchemaModule
{
    private const string ResourcePrefix =
        "Orbyss.ProgramKit.SecretResolution.Schemas.v1_0_0.";
    private static readonly SemanticVersion SchemaVersion = new("1.0.0");
    private static readonly ProgramKitIdentifier SchemaOwner =
        new("pkid:package:program-kit:secret-resolution");
    private static readonly ImmutableArray<ProgramKitIdentifier> SchemaConsumers =
    [
        new("pkid:project:program-kit:dotnet"),
        new("pkid:test:program-kit:conformance-tests"),
    ];
    private static readonly ArtifactProvenance SchemaProvenance =
        new(
            [
                new ArtifactReference(
                    new ProgramKitIdentifier("pkid:design:program-kit:host-tooling"),
                    new SemanticVersion("1.3.0"),
                    new Sha256Digest(
                        "sha256:a9ad015470f3996ea09811d57007ec4ab90e3b2cbff91245e625bfdd82ad0d57")),
                new ArtifactReference(
                    new ProgramKitIdentifier("pkid:plan:program-kit:host-tooling"),
                    new SemanticVersion("1.3.0"),
                    new Sha256Digest(
                        "sha256:8144a67d5d919211f87a2d30a4d7a870f299c126e138986c6f079e133734f9a5")),
            ],
            new ProgramKitIdentifier("pkid:project:program-kit:secret-resolution"),
            "pkht-w025-approved-review-set-1-3-0");
    private static readonly ArtifactCompatibility SchemaCompatibility =
        new(
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
            []);
    private static readonly ImmutableArray<ProgramKitSchemaResource> SchemaResources =
    [
        Create(
            "secret-resolution-contract",
            "secret-resolution-contract.schema.json",
            "https://schemas.orbyss.io/program-kit/secret-resolution/secret-resolution-contract/1.0.0/schema.json",
            "0dc33c7a414fcd63da9f10d7fd80830c7d9d01096f44cf6e25e247950c503a85"),
        Create(
            "secret-change-signal",
            "secret-change-signal.schema.json",
            "https://schemas.orbyss.io/program-kit/secret-resolution/secret-change-signal/1.0.0/schema.json",
            "fa61593b3bb5c3c69d1476c575d891d64141bafba217b066a2b31b7097bbef43"),
        Create(
            "secret-reaction-result",
            "secret-reaction-result.schema.json",
            "https://schemas.orbyss.io/program-kit/secret-resolution/secret-reaction-result/1.0.0/schema.json",
            "b5a47f6ba3deb6de1df8fe6ed318945bf03a7ace2d59e735b389caa7fd37eb5c"),
    ];

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:secret-resolution-schemas");

    /// <inheritdoc />
    public SemanticVersion Version => SchemaVersion;

    /// <inheritdoc />
    public ImmutableArray<ProgramKitSchemaResource> Resources => SchemaResources;

    /// <inheritdoc />
    public Stream OpenRead(ArtifactReference schemaReference)
    {
        ArgumentNullException.ThrowIfNull(schemaReference);
        var exactKey = ExactKey(schemaReference);
        var resource = SchemaResources.FirstOrDefault(candidate =>
            string.Equals(
                ExactKey(candidate.SchemaReference),
                exactKey,
                StringComparison.Ordinal));
        if (resource is null)
        {
            throw new KeyNotFoundException(
                string.Concat("The exact schema reference is not registered: ", exactKey));
        }

        return typeof(SecretResolutionSchemaModule).Assembly.GetManifestResourceStream(
                   string.Concat(ResourcePrefix, resource.ResourceName))
               ?? throw new InvalidOperationException(
                   string.Concat(
                       "The registered schema resource is unavailable: ",
                       resource.ResourceName));
    }

    private static ProgramKitSchemaResource Create(
        string name,
        string resourceName,
        string canonicalUri,
        string digest) =>
        new(
            new ArtifactReference(
                new ProgramKitIdentifier(string.Concat("pkid:schema:program-kit:", name)),
                SchemaVersion,
                new Sha256Digest(string.Concat("sha256:", digest))),
            new Uri(canonicalUri, UriKind.Absolute),
            resourceName,
            "application/schema+json",
            SchemaOwner,
            ArtifactStatus.Implemented,
            SchemaConsumers,
            SchemaProvenance,
            SchemaCompatibility);

    private static string ExactKey(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);
}
