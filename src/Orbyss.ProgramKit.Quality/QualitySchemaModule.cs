using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Quality;

/// <summary>
/// Explicit schema module for every schema owned by Orbyss.ProgramKit.Quality.
/// The allow-list is immutable and performs no assembly or directory discovery.
/// </summary>
public sealed class QualitySchemaModule : IProgramKitSchemaModule
{
    private const string ResourcePrefix = "Orbyss.ProgramKit.Quality.Schemas.";
    private static readonly SemanticVersion SchemaVersion = new("1.0.0");
    private static readonly SemanticVersionRange ExactSchemaVersion = new("[1.0.0]");
    private static readonly ProgramKitIdentifier SchemaOwner =
        new("pkid:package:program-kit:quality");
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
            new ProgramKitIdentifier("pkid:project:program-kit:quality"),
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
            "quality-definitions",
            "definitions.schema.json",
            "https://schemas.orbyss.io/program-kit/quality/1.0.0/definitions.schema.json",
            "391303aa21e18d816273f936510d392b733e8aefb70ae27a422dd51ee703c312"),
        Create(
            "execution-profile",
            "execution-profile.schema.json",
            "https://schemas.orbyss.io/program-kit/quality/execution-profile/1.0.0/schema.json",
            "75e29c235def43be23f82e6102b4a8d227169740d01bafb9a9daacdff87763f6"),
        Create(
            "independent-review",
            "independent-review.schema.json",
            "https://schemas.orbyss.io/program-kit/quality/independent-review/1.0.0/schema.json",
            "7697b8fa1ee3925397de31f0ba728987aec653e416369fad3496c781836251aa"),
        Create(
            "test-evidence",
            "test-evidence.schema.json",
            "https://schemas.orbyss.io/program-kit/quality/test-evidence/1.0.0/schema.json",
            "f822b40dea6510570bc6f911e1ccc817de98129efab081f707b5c65e6b85203b"),
        Create(
            "test-specification",
            "test-specification.schema.json",
            "https://schemas.orbyss.io/program-kit/quality/test-specification/1.0.0/schema.json",
            "90b664d00816c8386f81218d179546b3b5a31911149d0e37fd3df319de2075b1"),
    ];

    private QualitySchemaModule()
    {
    }

    /// <summary>Gets the singleton stateless schema module.</summary>
    public static QualitySchemaModule Instance { get; } = new();

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:quality-schemas");

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

        return typeof(QualitySchemaModule).Assembly.GetManifestResourceStream(
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
