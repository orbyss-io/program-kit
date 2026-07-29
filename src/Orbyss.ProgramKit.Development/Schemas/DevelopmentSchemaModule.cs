using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;

namespace Orbyss.ProgramKit.Development.Schemas;

/// <summary>
/// Explicit schema module for every schema owned by Orbyss.ProgramKit.Development.
/// The allow-list is immutable and performs no assembly or directory discovery.
/// </summary>
public sealed class DevelopmentSchemaModule : IProgramKitSchemaModule
{
    private const string ResourcePrefix = "Orbyss.ProgramKit.Development.Schemas.";
    private static readonly SemanticVersion SchemaVersion = new("1.0.0");
    private static readonly SemanticVersion AlphaSchemaVersion =
        new("0.1.0-alpha.1");
    private static readonly SemanticVersion CatalogVersion =
        new("0.1.0-alpha.1");
    private static readonly SemanticVersionRange ExactSchemaVersion = new("[1.0.0]");
    private static readonly ProgramKitIdentifier SchemaOwner =
        new("pkid:package:program-kit:development");
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
            new ProgramKitIdentifier("pkid:project:program-kit:development"),
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
            "development-definitions",
            "definitions-0.1.0-alpha.1.schema.json",
            "https://schemas.orbyss.io/program-kit/development/0.1.0-alpha.1/definitions.schema.json",
            "7d5eecafa74191c2b192e95cd61daf1813be707781eaa4d4505e2484b8a9dd8a",
            AlphaSchemaVersion),
        Create(
            "development-routing-result",
            "development-routing-result-0.1.0-alpha.1.schema.json",
            "https://schemas.orbyss.io/program-kit/development/routing-result/0.1.0-alpha.1/schema.json",
            "535c7c011ef2879f460530f7a1452bd39dc6b8c1afc058fb29504b9eb8f196ea",
            AlphaSchemaVersion),
        Create(
            "capability-availability-snapshot",
            "capability-availability-snapshot.schema.json",
            "https://schemas.orbyss.io/program-kit/development/capability-availability-snapshot/1.0.0/schema.json",
            "b94c6a33763f17dc8ac180e1402cab9a59e120bd58ab7a906cd5a09a128c52bc",
            SchemaVersion),
        Create(
            "development-definitions",
            "definitions.schema.json",
            "https://schemas.orbyss.io/program-kit/development/1.0.0/definitions.schema.json",
            "8557046e873ba1d5f6824dbdbcdf2ec127a104a1c1cf0bf126fd2b57cc0e48d2",
            SchemaVersion),
        Create(
            "development-receipt",
            "development-receipt.schema.json",
            "https://schemas.orbyss.io/program-kit/development/receipt/1.0.0/schema.json",
            "6e252460b830fb655b3e7ca9d5f778f258259ecc933a0962f1d276f90c0291dc",
            SchemaVersion),
        Create(
            "development-routing-result",
            "development-routing-result.schema.json",
            "https://schemas.orbyss.io/program-kit/development/routing-result/1.0.0/schema.json",
            "4f57d0ca35591119a19bc30a639fcfdc0c7ee66dcbdcc528593f38ebb8155c31",
            SchemaVersion),
    ];

    /// <summary>Initializes an explicitly composed schema module.</summary>
    public DevelopmentSchemaModule()
    {
    }

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:development-schemas");

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
                string.Concat("The exact schema reference is not registered: ", exactKey));
        }

        return typeof(DevelopmentSchemaModule).Assembly.GetManifestResourceStream(
                   string.Concat(ResourcePrefix, resource.ResourceName))
               ?? throw new InvalidOperationException(
                   string.Concat("The registered schema resource is unavailable: ", resource.ResourceName));
    }

    private static ProgramKitSchemaResource Create(
        string name,
        string resourceName,
        string canonicalUri,
        string digest,
        SemanticVersion version) =>
        new(
            new ArtifactReference(
                new ProgramKitIdentifier(string.Concat("pkid:schema:program-kit:", name)),
                version,
                new Sha256Digest(string.Concat("sha256:", digest))),
            new Uri(canonicalUri, UriKind.Absolute),
            resourceName,
            "application/schema+json",
            SchemaOwner,
            ArtifactStatus.Implemented,
            SchemaConsumers,
            SchemaProvenance,
            Compatibility(version));

    private static ArtifactCompatibility Compatibility(SemanticVersion version)
    {
        var exact = new SemanticVersionRange(
            string.Concat("[", version.Value, "]"));
        return new ArtifactCompatibility(
            SchemaCompatibility.Policy,
            SchemaCompatibility.Dimensions,
            exact,
            exact,
            []);
    }

    private static string ExactKey(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);
}
