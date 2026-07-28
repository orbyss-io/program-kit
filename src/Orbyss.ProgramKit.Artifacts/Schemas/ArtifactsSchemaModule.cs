using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Schemas;

/// <summary>Explicit schema module for schemas owned by Orbyss.ProgramKit.Artifacts.</summary>
public sealed class ArtifactsSchemaModule : IProgramKitSchemaModule
{
    private const string ResourcePrefix = "Orbyss.ProgramKit.Artifacts.Schemas.";
    private static readonly SemanticVersion CatalogVersion =
        new("0.1.0-alpha.1");
    private static readonly ProgramKitIdentifier SchemaOwner =
        new("pkid:package:program-kit:artifacts");
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
            new ProgramKitIdentifier("pkid:project:program-kit:artifacts"),
            "pk-w010-approved-review-set-0-3-0");
    private static readonly ArtifactProvenance TransitionSchemaProvenance =
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
            new ProgramKitIdentifier("pkid:project:program-kit:artifacts"),
            "PKAV-W010");

    private static readonly ImmutableArray<ProgramKitSchemaResource> SchemaResources =
    [
        Create(
            "artifact-definitions",
            "1.0.0",
            "definitions.schema.json",
            "https://schemas.orbyss.io/program-kit/artifacts/1.0.0/definitions.schema.json",
            "009a1360b1afcb1d91874d694f18318a91800d38626ca0c7696ce931856598ff"),
        Create(
            "artifact-envelope",
            "1.0.0",
            "artifact-envelope.schema.json",
            "https://schemas.orbyss.io/program-kit/artifacts/1.0.0/artifact-envelope.schema.json",
            "c2389234562fb5a5e32d8bdc966c9f796ea4da0eeac1a0eb324956ef3f1e8f14"),
        Create(
            "versioned-component-manifest",
            "1.0.0",
            "versioned-component-manifest.schema.json",
            "https://schemas.orbyss.io/program-kit/artifacts/1.0.0/versioned-component-manifest.schema.json",
            "6962cc487413df4361b873709b88acd6fe18608bd17a470a1b1aa56147197c08"),
        Create(
            "version-map",
            "1.0.0",
            "version-map.schema.json",
            "https://schemas.orbyss.io/program-kit/artifacts/1.0.0/version-map.schema.json",
            "c2a5145d3142ea9d1b10e313581a210538628861cc08893de76c754164d2f859"),
        Create(
            "version-selection",
            "1.0.0",
            "version-selection.schema.json",
            "https://schemas.orbyss.io/program-kit/artifacts/1.0.0/version-selection.schema.json",
            "029ea80c946a42218e40b6c4269d3ea08ab165f78de60dc6a0488fba7518faad"),
        Create(
            "migration-definition",
            "1.0.0",
            "migration-definition.schema.json",
            "https://schemas.orbyss.io/program-kit/artifacts/1.0.0/migration-definition.schema.json",
            "bf7dad73cf4135640b7ac98d7e3fae8236dcd955c7c48e9fdc08a1ae088a3294"),
        Create(
            "migration-assessment",
            "1.0.0",
            "migration-assessment.schema.json",
            "https://schemas.orbyss.io/program-kit/artifacts/1.0.0/migration-assessment.schema.json",
            "dd72e65ace420da64bd03903bcf0e7bffca53b7a470c20d5beae6f54c0aad2a9"),
        Create(
            "rfc8785-vector-set",
            "1.0.0",
            "rfc8785-vector-set.schema.json",
            "https://schemas.orbyss.io/program-kit/artifacts/1.0.0/rfc8785-vector-set.schema.json",
            "40b14e5459501ca6256c8e30099fea425fc979e97dbdfc85f121620ff9b9a4af"),
        Create(
            "version-intent-inventory",
            "0.1.0-alpha.1",
            "version-intent-inventory-0.1.0-alpha.1.schema.json",
            "https://schemas.orbyss.io/program-kit/versioning/0.1.0-alpha.1/version-intent-inventory.schema.json",
            "1212989f6406610b3ed304063a410baa683985b42b7c9c2c43bf6bee3dd1249c",
            TransitionSchemaProvenance),
        Create(
            "version-intent-inventory",
            "0.1.0-alpha.2",
            "version-intent-inventory-0.1.0-alpha.2.schema.json",
            "https://schemas.orbyss.io/program-kit/versioning/0.1.0-alpha.2/version-intent-inventory.schema.json",
            "935ed5616a14fb3b8be4726db6c52c0b14c2a8608ad419826f5f9d4549d33702",
            TransitionSchemaProvenance),
        Create(
            "alpha-version-progression",
            "0.1.0-alpha.1",
            "alpha-version-progression-0.1.0-alpha.1.schema.json",
            "https://schemas.orbyss.io/program-kit/versioning/0.1.0-alpha.1/alpha-version-progression.schema.json",
            "88003afb62af21937103f9fc2cd21a6255c7120115ba11ba38ff8eee2f10cb75",
            TransitionSchemaProvenance),
    ];

    /// <summary>Initializes an explicitly composed schema module.</summary>
    public ArtifactsSchemaModule()
    {
    }

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:artifact-schemas");

    /// <inheritdoc />
    public SemanticVersion Version => CatalogVersion;

    /// <inheritdoc />
    public ImmutableArray<ProgramKitSchemaResource> Resources => SchemaResources;

    /// <inheritdoc />
    public Stream OpenRead(ArtifactReference schemaReference)
    {
        ArgumentNullException.ThrowIfNull(schemaReference);
        var exactKey = ArtifactReferenceValidator.ExactKey(schemaReference);
        var resource = SchemaResources.FirstOrDefault(candidate =>
            string.Equals(
                ArtifactReferenceValidator.ExactKey(candidate.SchemaReference),
                exactKey,
                StringComparison.Ordinal));
        if (resource is null)
        {
            throw new KeyNotFoundException(
                string.Concat("The exact schema reference is not registered: ", exactKey));
        }

        return typeof(ArtifactsSchemaModule).Assembly.GetManifestResourceStream(
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
        return new ProgramKitSchemaResource(
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
            Compatibility(schemaVersion));
    }

    private static ArtifactCompatibility Compatibility(
        SemanticVersion version)
    {
        var exactVersion = new SemanticVersionRange(
            string.Concat("[", version.Value, "]"));
        return new ArtifactCompatibility(
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
            exactVersion,
            exactVersion,
            []);
    }
}
