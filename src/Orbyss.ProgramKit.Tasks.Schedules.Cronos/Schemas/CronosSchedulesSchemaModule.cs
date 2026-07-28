using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;

namespace Orbyss.ProgramKit.Tasks.Schedules.Cronos.Schemas;

/// <summary>Immutable schema module for the selected cronos/0.13 descriptor.</summary>
public sealed class CronosSchedulesSchemaModule : IProgramKitSchemaModule
{
    private const string ResourceName =
        "cronos-schedule-descriptor.schema.json";
    private static readonly SemanticVersion SchemaVersion = new("1.0.0");
    private static readonly SemanticVersion CatalogVersion =
        new("0.1.0-alpha.1");
    private static readonly SemanticVersionRange ExactSchemaVersion =
        new("[1.0.0]");
    private static readonly ArtifactReference DescriptorSchema =
        new(
            new ProgramKitIdentifier(
                "pkid:schema:program-kit:cronos-schedule-descriptor"),
            SchemaVersion,
            new Sha256Digest(
                "sha256:cbb5ce4ae60b1910bfbc57f8f8b89b63d5822af3861a14cebc0064fe9e21ce82"));
    private static readonly ImmutableArray<ProgramKitSchemaResource> Registered =
    [
        new ProgramKitSchemaResource(
            DescriptorSchema,
            new Uri(
                "https://schemas.orbyss.io/program-kit/task-schedules-cronos/1.0.0/cronos-schedule-descriptor.schema.json",
                UriKind.Absolute),
            ResourceName,
            "application/schema+json",
            new ProgramKitIdentifier(
                "pkid:package:program-kit:tasks-schedules-cronos"),
            ArtifactStatus.Implemented,
            [
                new ProgramKitIdentifier(
                    "pkid:project:program-kit:dotnet"),
                new ProgramKitIdentifier(
                    "pkid:test:program-kit:conformance-tests"),
            ],
            new ArtifactProvenance(
                [
                    new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:design:program-kit:baseline"),
                        new SemanticVersion("0.3.0"),
                        new Sha256Digest(
                            "sha256:dbe65ea112a172761f5725c210add00867b8b9f7a180a8b5ee6f80e42dace1c9")),
                    new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:plan:program-kit:baseline"),
                        new SemanticVersion("0.3.0"),
                        new Sha256Digest(
                            "sha256:6d7396d5eb71e0d064231110e2ccfcae2aea838ca851b1420ff310df127cd951")),
                ],
                new ProgramKitIdentifier(
                    "pkid:project:program-kit:tasks-schedules-cronos"),
                "pk-w030-approved-review-set-0-3-0"),
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
                ExactSchemaVersion,
                ExactSchemaVersion,
                [])),
    ];

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:cronos-schedule-schemas");

    /// <inheritdoc />
    public SemanticVersion Version => CatalogVersion;

    /// <inheritdoc />
    public ImmutableArray<ProgramKitSchemaResource> Resources => Registered;

    /// <inheritdoc />
    public Stream OpenRead(ArtifactReference schemaReference)
    {
        ArgumentNullException.ThrowIfNull(schemaReference);
        if (schemaReference != DescriptorSchema)
        {
            throw new KeyNotFoundException(
                "The exact Cronos schedule schema is not registered.");
        }

        return typeof(CronosSchedulesSchemaModule).Assembly
                   .GetManifestResourceStream(
                       string.Concat(
                           "Orbyss.ProgramKit.Tasks.Schedules.Cronos.Schemas.",
                           ResourceName))
               ?? throw new InvalidOperationException(
                   "The registered Cronos schedule schema is unavailable.");
    }
}
