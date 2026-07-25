namespace Orbyss.ProgramKit.Operations.Contracts.Schemas;

/// <summary>
/// Explicit finite schema module owned by Orbyss.ProgramKit.Operations.
/// </summary>
public sealed class OperationsSchemaModule : IProgramKitSchemaModule
{
    private const string ResourcePrefix = "Orbyss.ProgramKit.Operations.Schemas.";
    private static readonly SemanticVersion SchemaVersion = new("1.0.0");
    private static readonly ProgramKitIdentifier SchemaOwner =
        new("pkid:package:program-kit:operations");
    private static readonly ImmutableArray<ProgramKitIdentifier> SchemaConsumers =
    [
        new("pkid:project:program-kit:dotnet"),
        new("pkid:project:program-kit:workbench"),
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
            new ProgramKitIdentifier("pkid:project:program-kit:operations"),
            "pkht-w010-approved-review-set-1-3-0");
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
            "operations-definitions",
            "definitions.schema.json",
            "https://schemas.orbyss.io/program-kit/operations/1.0.0/definitions.schema.json",
            "67f4cc39a30ba27ccfbf439a5b74015b9a552b91dd0837636e9f1554bd66ad3e"),
        Create(
            "operation-contract-catalog",
            "operation-contract-catalog.schema.json",
            "https://schemas.orbyss.io/program-kit/operations/operation-contract-catalog/1.0.0/schema.json",
            "e865f2daa9c94bbd6dce3a1bffca96060c01dd68d2ee3cd79e0a620fb366edbd"),
        Create(
            "operation-contract-descriptor",
            "operation-contract-descriptor.schema.json",
            "https://schemas.orbyss.io/program-kit/operations/operation-contract-descriptor/1.0.0/schema.json",
            "033977338937a007abc2dce36ede6b2037c92f947d315b8155f1e6c1bc613d94"),
        Create(
            "operation-invocation",
            "operation-invocation.schema.json",
            "https://schemas.orbyss.io/program-kit/operations/operation-invocation/1.0.0/schema.json",
            "9c72a42935af296d2e0673ee8776642205254981dc35bf83a69402ba79d0dcf2"),
        Create(
            "operation-progress",
            "operation-progress.schema.json",
            "https://schemas.orbyss.io/program-kit/operations/operation-progress/1.0.0/schema.json",
            "193b765fd6651d3871620ee52b460cfc3d66c6ffe3857a145b8350e89fe8eed0"),
        Create(
            "operation-result",
            "operation-result.schema.json",
            "https://schemas.orbyss.io/program-kit/operations/operation-result/1.0.0/schema.json",
            "16597c530c191945bc3999050d7491b21ced8ead9659b7f5d17fb8cb095f0517"),
        Create(
            "transport-failure-profile",
            "transport-failure-profile.schema.json",
            "https://schemas.orbyss.io/program-kit/operations/transport-failure-profile/1.0.0/schema.json",
            "31d131cf1677327f7b8ba0a8546224eaae31cb954ce13310053cfe8b87631269"),
    ];

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:operations-schemas");

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

        return typeof(OperationsSchemaModule).Assembly.GetManifestResourceStream(
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
