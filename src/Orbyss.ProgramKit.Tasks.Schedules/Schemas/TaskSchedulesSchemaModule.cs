using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;

namespace Orbyss.ProgramKit.Tasks.Schedules.Schemas;

/// <summary>Explicit immutable module for provider-neutral schedule schemas.</summary>
public sealed class TaskSchedulesSchemaModule : IProgramKitSchemaModule
{
    private const string ResourcePrefix =
        "Orbyss.ProgramKit.Tasks.Schedules.Schemas.";
    private static readonly SemanticVersion SchemaVersion = new("1.0.0");
    private static readonly SemanticVersionRange ExactSchemaVersion =
        new("[1.0.0]");
    private static readonly ProgramKitIdentifier SchemaOwner =
        new("pkid:package:program-kit:tasks-schedules");
    private static readonly ArtifactProvenance Provenance =
        new(
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
                "pkid:project:program-kit:tasks-schedules"),
            "pk-w030-approved-review-set-0-3-0");
    private static readonly ArtifactCompatibility Compatibility =
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
    private static readonly ImmutableArray<ProgramKitSchemaResource> Registered =
    [
        Create(
            "anchored-fixed-interval-schedule-descriptor",
            "anchored-fixed-interval.schema.json",
            "https://schemas.orbyss.io/program-kit/task-schedules/1.0.0/anchored-fixed-interval.schema.json",
            "29e6902d13c9b9dbe15eb472a1abc841d2df79c0369bb3b03515243c5bde737b"),
        Create(
            "delay-once-schedule-descriptor",
            "delay-once.schema.json",
            "https://schemas.orbyss.io/program-kit/task-schedules/1.0.0/delay-once.schema.json",
            "1fbafbdcec7f8386d249115925d9b0b95f8183a866b442f26814ad8e10c20c38"),
        Create(
            "fixed-delay-schedule-descriptor",
            "fixed-delay.schema.json",
            "https://schemas.orbyss.io/program-kit/task-schedules/1.0.0/fixed-delay.schema.json",
            "2a531f4bd657e8cb799db87f1d0768fd99f63924efeb6487d3ff0470065a7caa"),
    ];

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:task-schedule-schemas");

    /// <inheritdoc />
    public SemanticVersion Version => SchemaVersion;

    /// <inheritdoc />
    public ImmutableArray<ProgramKitSchemaResource> Resources => Registered;

    /// <inheritdoc />
    public Stream OpenRead(ArtifactReference schemaReference)
    {
        ArgumentNullException.ThrowIfNull(schemaReference);
        var exactKey = ExactKey(schemaReference);
        var resource = Registered.FirstOrDefault(candidate =>
            string.Equals(
                ExactKey(candidate.SchemaReference),
                exactKey,
                StringComparison.Ordinal));
        if (resource is null)
        {
            throw new KeyNotFoundException(
                string.Concat(
                    "The exact schedule schema is not registered: ",
                    exactKey));
        }

        return typeof(TaskSchedulesSchemaModule).Assembly
                   .GetManifestResourceStream(
                       string.Concat(
                           ResourcePrefix,
                           resource.ResourceName))
               ?? throw new InvalidOperationException(
                   string.Concat(
                       "The registered schedule schema is unavailable: ",
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
            [
                new ProgramKitIdentifier(
                    "pkid:project:program-kit:workbench"),
                new ProgramKitIdentifier(
                    "pkid:project:program-kit:dotnet"),
                new ProgramKitIdentifier(
                    "pkid:test:program-kit:conformance-tests"),
            ],
            Provenance,
            Compatibility);

    private static string ExactKey(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);
}
