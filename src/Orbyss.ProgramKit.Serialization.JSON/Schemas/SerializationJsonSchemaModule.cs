using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;

namespace Orbyss.ProgramKit.Serialization.Json.Schemas;

/// <summary>
/// Explicit immutable schema module for Serialization.JSON-owned descriptors.
/// No assembly or directory scanning is performed.
/// </summary>
public sealed class SerializationJsonSchemaModule : IProgramKitSchemaModule
{
    private const string ResourcePrefix =
        "Orbyss.ProgramKit.Serialization.JSON.Schemas.";
    private static readonly SemanticVersion SchemaVersion = new("1.0.0");
    private static readonly SemanticVersion CatalogVersion =
        new("0.1.0-alpha.1");
    private static readonly SemanticVersionRange ExactSchemaVersion =
        new("[1.0.0]");
    private static readonly ProgramKitIdentifier SchemaOwner =
        new("pkid:package:program-kit:serialization-json");
    private static readonly ImmutableArray<ProgramKitIdentifier> SchemaConsumers =
    [
        new("pkid:project:program-kit:serialization-json"),
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
            new ProgramKitIdentifier(
                "pkid:project:program-kit:serialization-json"),
            "pk-w015-approved-review-set-0-3-0");
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
            "serialization-definitions",
            "definitions.schema.json",
            "https://schemas.orbyss.io/program-kit/serialization/1.0.0/definitions.schema.json",
            "010b4cefd64db7508950d6304cc371d17525ae6c53c1f1a5a056b46afa3cc30d"),
        Create(
            "json-contribution-descriptor",
            "json-contribution-descriptor.schema.json",
            "https://schemas.orbyss.io/program-kit/serialization/1.0.0/json-contribution-descriptor.schema.json",
            "d0dc4ed16f1209fdf10cd7a0ac0020b1b9b3d75fa1e4d139247ae039680bf13c"),
        Create(
            "json-profile-selection",
            "json-profile-selection.schema.json",
            "https://schemas.orbyss.io/program-kit/serialization/1.0.0/json-profile-selection.schema.json",
            "506a7c89025166067e5a43fdfd94b06b30690cb3c24ca9dece011dcee8cb3f1c"),
        Create(
            "json-serialization-profile",
            "json-serialization-profile.schema.json",
            "https://schemas.orbyss.io/program-kit/serialization/1.0.0/json-serialization-profile.schema.json",
            "f541567603e359661c2b1051061ceb64a9d6978728f23520764077907b18a7a1"),
        Create(
            "json-profile-source",
            "profile-source.schema.json",
            "https://schemas.orbyss.io/program-kit/serialization/1.0.0/profile-source.schema.json",
            "d8c62250accf7a59e2318546952dda43d645b5164979d8736084453ad755aeb6"),
    ];

    /// <summary>Initializes an explicitly composed schema module.</summary>
    public SerializationJsonSchemaModule()
    {
    }

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:serialization-schemas");

    /// <inheritdoc />
    public SemanticVersion Version => CatalogVersion;

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
                string.Concat(
                    "The exact serialization schema is not registered: ",
                    exactKey));
        }

        return typeof(SerializationJsonSchemaModule).Assembly
                   .GetManifestResourceStream(
                       string.Concat(ResourcePrefix, resource.ResourceName))
               ?? throw new InvalidOperationException(
                   string.Concat(
                       "The registered serialization schema is unavailable: ",
                       resource.ResourceName));
    }

    private static ProgramKitSchemaResource Create(
        string name,
        string resourceName,
        string canonicalUri,
        string digest) =>
        new(
            new ArtifactReference(
                new ProgramKitIdentifier(
                    string.Concat("pkid:schema:program-kit:", name)),
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
