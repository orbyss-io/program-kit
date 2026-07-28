using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Envelopes;

namespace Orbyss.ProgramKit.Tasks.Core.Schemas;

/// <summary>Explicit immutable module for Tasks.Core-owned schemas.</summary>
public sealed class TasksCoreSchemaModule : IProgramKitSchemaModule
{
    private const string ResourcePrefix = "Orbyss.ProgramKit.Tasks.Core.Schemas.";
    private static readonly SemanticVersion SchemaVersion = new("1.0.0");
    private static readonly SemanticVersion CatalogVersion =
        new("0.1.0-alpha.1");
    private static readonly SemanticVersionRange ExactSchemaVersion =
        new("[1.0.0]");
    private static readonly ProgramKitIdentifier SchemaOwner =
        new("pkid:package:program-kit:tasks-core");
    private static readonly ImmutableArray<ProgramKitIdentifier> SchemaConsumers =
    [
        new("pkid:project:program-kit:workbench"),
        new("pkid:project:program-kit:dotnet"),
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
            new ProgramKitIdentifier("pkid:project:program-kit:tasks-core"),
            "pk-w025-approved-review-set-0-3-0");
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
            "task-definitions",
            "definitions.schema.json",
            "https://schemas.orbyss.io/program-kit/tasks/1.0.0/definitions.schema.json",
            "a0fa72db69105fa1310fc01577430f64d572f530ef7479c6eb56e10fe6e50b2f"),
        Create(
            "task-activation-binding",
            "task-activation-binding.schema.json",
            "https://schemas.orbyss.io/program-kit/tasks/1.0.0/task-activation-binding.schema.json",
            "b2a1b73ed1b6e1ee7b83cc18dc403358a93759672a04c02ae934ffe7e7b56869"),
        Create(
            "task-attempt",
            "task-attempt.schema.json",
            "https://schemas.orbyss.io/program-kit/tasks/1.0.0/task-attempt.schema.json",
            "9a4e438095d82f3f277e227bb8a55f628d7b706afaf1132d59382ac02b7d04da"),
        Create(
            "task-definition",
            "task-definition.schema.json",
            "https://schemas.orbyss.io/program-kit/tasks/1.0.0/task-definition.schema.json",
            "da52f55342c50081ddad4e5520929aa5818a388c91062dce3593d41c0b8bb1dd"),
        Create(
            "task-instance",
            "task-instance.schema.json",
            "https://schemas.orbyss.io/program-kit/tasks/1.0.0/task-instance.schema.json",
            "0e65968c547ecad7c95dd3420d0eaaff0580c13a80ae5e6fe24bbaef87121fe0"),
        Create(
            "task-occurrence",
            "task-occurrence.schema.json",
            "https://schemas.orbyss.io/program-kit/tasks/1.0.0/task-occurrence.schema.json",
            "9e452e6c34a7fcbab319bd7f9ccb403df5e84a8236ba2acdfe7e227cc2827a61"),
        Create(
            "task-request",
            "task-request.schema.json",
            "https://schemas.orbyss.io/program-kit/tasks/1.0.0/task-request.schema.json",
            "6d88c911e4dd2a90d3491a21b2a4b2635f283aa7bcf831a54d53b10e9d22c130"),
        Create(
            "task-schedule-definition",
            "task-schedule-definition.schema.json",
            "https://schemas.orbyss.io/program-kit/tasks/1.0.0/task-schedule-definition.schema.json",
            "5c0d3e94a53b71d1354a5be07c7f84968bf1990fdbd1f1b7f2db5ae919598838"),
    ];

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:tasks-core-schemas");

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
                    "The exact schema reference is not registered: ",
                    exactKey));
        }

        return typeof(TasksCoreSchemaModule).Assembly.GetManifestResourceStream(
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
