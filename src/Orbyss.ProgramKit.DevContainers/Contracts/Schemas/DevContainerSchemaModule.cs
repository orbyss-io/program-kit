namespace Orbyss.ProgramKit.DevContainers.Contracts.Schemas;

/// <summary>Exact immutable module for the selected official Dev Container base schema.</summary>
public sealed class DevContainerSchemaModule : IProgramKitSchemaModule
{
    private const string ResourceName = "dev-container-base-validation.schema.json";
    private const string ValidationResourceName =
        "Orbyss.ProgramKit.DevContainers.Schemas.dev-container-base-validation.schema.json";
    private const string OfficialResourceName =
        "Orbyss.ProgramKit.DevContainers.Schemas.Vendor.devContainer.base.schema.json";
    private static readonly SemanticVersion SchemaVersion = new("1.0.0");
    private static readonly ArtifactReference SchemaReferenceValue =
        new(
            new ProgramKitIdentifier("pkid:schema:devcontainers:base"),
            SchemaVersion,
            new Sha256Digest(
                "sha256:ad4a53e96281b53a5b4332ebdd8d4cb06d93da152a8c2889f98690874c60716e"));
    private static readonly ProgramKitSchemaResource SchemaResource =
        new(
            SchemaReferenceValue,
            new Uri(
                "https://schemas.orbyss.io/program-kit/dev-containers/1.0.0/dev-container-base-validation.schema.json",
                UriKind.Absolute),
            ResourceName,
            "application/schema+json",
            new ProgramKitIdentifier("pkid:package:program-kit:dev-containers"),
            ArtifactStatus.Implemented,
            [
                new ProgramKitIdentifier("pkid:project:program-kit:dev-containers"),
                new ProgramKitIdentifier("pkid:test:program-kit:conformance-tests"),
            ],
            new ArtifactProvenance(
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
                new ProgramKitIdentifier("pkid:project:program-kit:dev-containers"),
                "pkht-w080-approved-review-set-1-3-0"),
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

    /// <summary>Gets the exact official base-schema reference.</summary>
    public static ArtifactReference BaseSchemaReference => SchemaReferenceValue;

    /// <summary>Opens the unmodified official upstream base-schema bytes.</summary>
    public static Stream OpenOfficialBaseSchema()
    {
        return typeof(DevContainerSchemaModule).Assembly.GetManifestResourceStream(
                   OfficialResourceName)
               ?? throw new InvalidOperationException(
                   "The exact official Dev Container base schema is unavailable.");
    }

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:dev-container-schemas");

    /// <inheritdoc />
    public SemanticVersion Version => SchemaVersion;

    /// <inheritdoc />
    public ImmutableArray<ProgramKitSchemaResource> Resources => [SchemaResource];

    /// <inheritdoc />
    public Stream OpenRead(ArtifactReference schemaReference)
    {
        ArgumentNullException.ThrowIfNull(schemaReference);
        if (schemaReference != SchemaReferenceValue)
        {
            throw new KeyNotFoundException(
                "The exact Dev Container base schema reference is not registered.");
        }

        return typeof(DevContainerSchemaModule).Assembly.GetManifestResourceStream(
                   ValidationResourceName)
               ?? throw new InvalidOperationException(
                   "The exact Dev Container validation schema is unavailable.");
    }
}
