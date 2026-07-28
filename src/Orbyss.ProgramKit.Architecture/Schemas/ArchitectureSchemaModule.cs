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
    private static readonly ArtifactProvenance AlphaTransitionProvenance =
        new(
            [
                new ArtifactReference(
                    new ProgramKitIdentifier(
                        "pkid:design:program-kit:alpha-version-transition"),
                    new SemanticVersion("0.1.0-alpha.1"),
                    new Sha256Digest(
                        "sha256:2b8027d505dfcef7f1b28bc3aecf3333b575e59928dabb7121d24f28be2811ba")),
                new ArtifactReference(
                    new ProgramKitIdentifier(
                        "pkid:plan:program-kit:alpha-version-transition"),
                    new SemanticVersion("0.1.0-alpha.1"),
                    new Sha256Digest(
                        "sha256:66e37776c11cda3ee17747b6dd3165286e4a2901e17dca41464a243f1f2e750f")),
            ],
            new ProgramKitIdentifier("pkid:project:program-kit:architecture"),
            "pkav-w020-approved-review-set-0-1-0-alpha-1");
    private static readonly ImmutableArray<ProgramKitSchemaResource> SchemaResources =
    [
        Create(
            "architecture-design",
            "1.0.0",
            "architecture-design.schema.json",
            "https://schemas.orbyss.io/program-kit/architecture/1.0.0/architecture-design.schema.json",
            "19606f994af588d3d48284391af3880e1ade0315980189ad681026d7e43976e2"),
        Create(
            "artifact-decision",
            "1.0.0",
            "artifact-decision.schema.json",
            "https://schemas.orbyss.io/program-kit/architecture/1.0.0/artifact-decision.schema.json",
            "e07d865c896aa23d63c0294b0832c4f1820c4863737d181cb6723f2e4d813025"),
        Create(
            "dotnet-target-profile",
            "1.0.0",
            "dotnet-target-profile.schema.json",
            "https://schemas.orbyss.io/program-kit/architecture/1.0.0/dotnet-target-profile.schema.json",
            "ded80622b97322feaf7a67b5cb738870249c55588fc9b7ae22a0997261f87f18"),
        Create(
            "structural-pattern-catalog",
            "1.0.0",
            "structural-pattern-catalog.schema.json",
            "https://schemas.orbyss.io/program-kit/architecture/1.0.0/structural-pattern-catalog.schema.json",
            "ebfeebc5d37bb37f9ccecbb8f68c444e1dbbb217cf5ab111f2b8bf09f8632c7d"),
        Create(
            "architecture-design",
            "2.0.0",
            "architecture-design-2.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/architecture/2.0.0/architecture-design.schema.json",
            "2698ce65a29cb0d5007b2ab1773d7e387385df7c8b72495804b292b6af696198"),
        Create(
            "architecture-design",
            "0.1.0-alpha.2",
            "architecture-design-0.1.0-alpha.2.schema.json",
            "https://schemas.orbyss.io/program-kit/architecture/0.1.0-alpha.2/architecture-design.schema.json",
            "e94b5e1dab8292066669ccee5069f27a6e220962906051931fc1f1607fe2dbf7",
            AlphaTransitionProvenance),
        Create(
            "static-conformance-disposition",
            "1.0.0",
            "static-conformance-disposition.schema.json",
            "https://schemas.orbyss.io/program-kit/architecture/1.0.0/static-conformance-disposition.schema.json",
            "834902de4706a7c6859390bd7ee5e4fd6a3e7e455486348c02a1cb84604d15bd"),
        Create(
            "static-conformance-disposition",
            "0.1.0-alpha.1",
            "static-conformance-disposition-0.1.0-alpha.1.schema.json",
            "https://schemas.orbyss.io/program-kit/architecture/0.1.0-alpha.1/static-conformance-disposition.schema.json",
            "9de8f2dfcc52bb629ef802db26bd67ffc38687d73d08084292127f6eeda29811",
            AlphaTransitionProvenance),
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
        string version,
        string resourceName,
        string canonicalUri,
        string digest,
        ArtifactProvenance? provenance = null)
    {
        var schemaVersion = new SemanticVersion(version);
        var exactSchemaVersion = new SemanticVersionRange(
            string.Concat("[", version, "]"));
        var compatibility = new ArtifactCompatibility(
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
            exactSchemaVersion,
            exactSchemaVersion,
            []);
        return
        new(
            new ArtifactReference(
                new ProgramKitIdentifier(string.Concat("pkid:schema:program-kit:", name)),
                schemaVersion,
                new Sha256Digest(string.Concat("sha256:", digest))),
            new Uri(canonicalUri, UriKind.Absolute),
            resourceName,
            "application/schema+json",
            SchemaOwner,
            ArtifactStatus.Implemented,
            SchemaConsumers,
            provenance ?? SchemaProvenance,
            compatibility);
    }

    private static string ExactKey(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);
}
