using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Schemas;

/// <summary>
/// Explicit schema module for every schema owned by
/// Orbyss.ProgramKit.Architecture. The allow-list is immutable and performs no
/// assembly, directory, or resource-name discovery.
/// </summary>
public sealed class ArchitectureSchemaModule : IProgramKitSchemaModule
{
    private const string ResourcePrefix = "Orbyss.ProgramKit.Architecture.Schemas.";
    private static readonly SemanticVersion SchemaVersion = new("1.0.0");
    private static readonly SemanticVersionRange ExactSchemaVersion =
        new("[1.0.0]");
    private static readonly ProgramKitIdentifier SchemaOwner =
        new("pkid:package:program-kit:architecture");
    private static readonly ImmutableArray<ProgramKitIdentifier> SchemaConsumers =
    [
        new("pkid:project:program-kit:workbench"),
        new("pkid:test:program-kit:conformance-tests"),
    ];
    private static readonly ArtifactProvenance SchemaProvenance =
        new(
            [
                new ArtifactReference(
                    new ProgramKitIdentifier("pkid:design:program-kit:baseline"),
                    new SemanticVersion("0.3.0"),
                    new Sha256Digest(
                        "sha256:dbe65ea112a172761f5725c210add00867b8b9f7a180a8b5ee6f80e42dace1c9")),
                new ArtifactReference(
                    new ProgramKitIdentifier("pkid:plan:program-kit:baseline"),
                    new SemanticVersion("0.3.0"),
                    new Sha256Digest(
                        "sha256:6d7396d5eb71e0d064231110e2ccfcae2aea838ca851b1420ff310df127cd951")),
            ],
            new ProgramKitIdentifier("pkid:project:program-kit:architecture"),
            "pk-w010-approved-review-set-0-3-0");
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
            ExactSchemaVersion,
            ExactSchemaVersion,
            []);

    private static readonly ImmutableArray<ProgramKitSchemaResource> SchemaResources =
    [
        Create(
            "architecture-design",
            "architecture-design.schema.json",
            "https://schemas.orbyss.io/program-kit/architecture/1.0.0/architecture-design.schema.json",
            "19606f994af588d3d48284391af3880e1ade0315980189ad681026d7e43976e2"),
        Create(
            "artifact-decision",
            "artifact-decision.schema.json",
            "https://schemas.orbyss.io/program-kit/architecture/1.0.0/artifact-decision.schema.json",
            "e07d865c896aa23d63c0294b0832c4f1820c4863737d181cb6723f2e4d813025"),
        Create(
            "dotnet-target-profile",
            "dotnet-target-profile.schema.json",
            "https://schemas.orbyss.io/program-kit/architecture/1.0.0/dotnet-target-profile.schema.json",
            "ded80622b97322feaf7a67b5cb738870249c55588fc9b7ae22a0997261f87f18"),
        Create(
            "structural-pattern-catalog",
            "structural-pattern-catalog.schema.json",
            "https://schemas.orbyss.io/program-kit/architecture/1.0.0/structural-pattern-catalog.schema.json",
            "ebfeebc5d37bb37f9ccecbb8f68c444e1dbbb217cf5ab111f2b8bf09f8632c7d"),
    ];

    /// <summary>Initializes an explicitly composed schema module.</summary>
    public ArchitectureSchemaModule()
    {
    }

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:architecture-schemas");

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

        return typeof(ArchitectureSchemaModule).Assembly.GetManifestResourceStream(
                   string.Concat(ResourcePrefix, resource.ResourceName))
               ?? throw new InvalidOperationException(
                   string.Concat("The registered schema resource is unavailable: ", resource.ResourceName));
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
