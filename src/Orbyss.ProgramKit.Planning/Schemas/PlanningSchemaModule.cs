using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;

namespace Orbyss.ProgramKit.Planning.Schemas;

/// <summary>
/// Explicit schema module for every schema owned by Orbyss.ProgramKit.Planning.
/// The allow-list is immutable and performs no assembly or directory discovery.
/// </summary>
public sealed class PlanningSchemaModule : IProgramKitSchemaModule
{
    private const string ResourcePrefix = "Orbyss.ProgramKit.Planning.Schemas.";
    private static readonly SemanticVersion CatalogVersion =
        new("0.1.0-alpha.4");
    private static readonly SemanticVersion SchemaVersionV1 = new("1.0.0");
    private static readonly SemanticVersion SchemaVersionV2 = new("2.0.0");
    private static readonly SemanticVersion SchemaVersionV3 = new("3.0.0");
    private static readonly SemanticVersion SchemaVersionAlpha3 =
        new("0.1.0-alpha.3");
    private static readonly SemanticVersion SchemaVersionAlpha4 =
        new("0.1.0-alpha.4");
    private static readonly ProgramKitIdentifier SchemaOwner =
        new("pkid:package:program-kit:planning");
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
            new ProgramKitIdentifier("pkid:project:program-kit:planning"),
            "pk-w010-approved-review-set-0-3-0");
    private static readonly ArtifactProvenance HostToolingSchemaProvenance =
        new(
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
            new ProgramKitIdentifier("pkid:project:program-kit:planning"),
            "pkht-w010-approved-review-set-1-3-0");
    private static readonly ArtifactProvenance BuildGateSchemaProvenance =
        new(
            [
                new ArtifactReference(
                    new ProgramKitIdentifier(
                        "pkid:design:program-kit:reusable-csharp-build-gates"),
                    new SemanticVersion("1.0.0"),
                    new Sha256Digest(
                        "sha256:be89504de69b0aaf7adc520a0aa76528e519fc57f56e72b7d4a6c595419929da")),
                new ArtifactReference(
                    new ProgramKitIdentifier(
                        "pkid:plan:program-kit:reusable-csharp-build-gates"),
                    new SemanticVersion("1.0.0"),
                    new Sha256Digest(
                        "sha256:307bf4097b469e6d1aa307e79653f8f3568e0385409433ff5f5ca13a0056e1d4")),
            ],
            new ProgramKitIdentifier("pkid:project:program-kit:planning"),
            "pkcg-w020-approved-review-set-1-0-0");
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
            new ProgramKitIdentifier("pkid:project:program-kit:planning"),
            "pkav-w020-approved-review-set-0-1-0-alpha-1");
    private static readonly ArtifactProvenance ConsumerContractProvenance =
        new(
            [
                new ArtifactReference(
                    new ProgramKitIdentifier(
                        "pkid:design-amendment:program-kit:consumer-contract-surface-hardening"),
                    new SemanticVersion("0.1.0-alpha.1"),
                    new Sha256Digest(
                        "sha256:dc29a4be4fba94801041fc57fb95c4e21780c4db3fcb5376b31b34041ac81f37")),
                new ArtifactReference(
                    new ProgramKitIdentifier(
                        "pkid:plan-amendment:program-kit:consumer-contract-surface-hardening"),
                    new SemanticVersion("0.1.0-alpha.1"),
                    new Sha256Digest(
                        "sha256:c8b6a2ce5740532204b90202180ebbaa4050b1541da5cbd2401e1f1b89a9c499")),
            ],
            new ProgramKitIdentifier("pkid:project:program-kit:planning"),
            "PKCJ-W030");

    private static readonly ImmutableArray<ProgramKitSchemaResource> SchemaResources =
    [
        Create(
            "planning-definitions",
            "definitions.schema.json",
            "https://schemas.orbyss.io/program-kit/planning/1.0.0/definitions.schema.json",
            "14398b35cb4eda7f59ba04c8c91056d0e84dc6895c31f22a4446bc370bfb00f9",
            SchemaVersionV1,
            SchemaProvenance),
        Create(
            "design-plan-approval",
            "design-plan-approval.schema.json",
            "https://schemas.orbyss.io/program-kit/planning/design-plan-approval/1.0.0/schema.json",
            "58adfa2eff4a8276c9ca1687db8fb44beb899819fa356468d37c05bd664f2014",
            SchemaVersionV1,
            SchemaProvenance),
        Create(
            "implementation-plan",
            "implementation-plan.schema.json",
            "https://schemas.orbyss.io/program-kit/planning/implementation-plan/1.0.0/schema.json",
            "b0d87ae0dca8ba075f79deb22e11ada54c0b74483b89dc19ac021a9d30f64423",
            SchemaVersionV1,
            SchemaProvenance),
        Create(
            "planning-definitions",
            "definitions-2.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/planning/2.0.0/definitions.schema.json",
            "32e505c59c5adff33bdd34e4e53084111a042d200b0c0dbfc09c9c696633f8cd",
            SchemaVersionV2,
            HostToolingSchemaProvenance),
        Create(
            "implementation-plan",
            "implementation-plan-2.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/planning/implementation-plan/2.0.0/schema.json",
            "119bc1a17ed4f1c2eef193e5c0c75df0c7c4ea9b33b55d206b871bca4614c32d",
            SchemaVersionV2,
            HostToolingSchemaProvenance),
        Create(
            "planning-definitions",
            "definitions-3.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/planning/3.0.0/definitions.schema.json",
            "70b3a0291cfa163da5b6144394fb4cc44fe00d44e4a8d2953dab5ec28e78ddc7",
            SchemaVersionV3,
            BuildGateSchemaProvenance),
        Create(
            "implementation-plan",
            "implementation-plan-3.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/planning/implementation-plan/3.0.0/schema.json",
            "0f3b8f524b29ec7b5871ce411f06852e1b06326a5e1da616184627df0b5ea1b6",
            SchemaVersionV3,
            BuildGateSchemaProvenance),
        Create(
            "implementation-plan",
            "implementation-plan-0.1.0-alpha.3.schema.json",
            "https://schemas.orbyss.io/program-kit/planning/implementation-plan/0.1.0-alpha.3/schema.json",
            "774c6b945ac2b63c2e4beca0afab9c282669274f0c7d4eb4b9e936ba38460c7c",
            SchemaVersionAlpha3,
            AlphaTransitionProvenance),
        Create(
            "planning-definitions",
            "definitions-0.1.0-alpha.4.schema.json",
            "https://schemas.orbyss.io/program-kit/planning/0.1.0-alpha.4/definitions.schema.json",
            "78228cf3d0ab5b7d72c2dd8481496dc9f60eeb44f408effb545cdbc80eb0a256",
            SchemaVersionAlpha4,
            ConsumerContractProvenance),
        Create(
            "implementation-plan",
            "implementation-plan-0.1.0-alpha.4.schema.json",
            "https://schemas.orbyss.io/program-kit/planning/implementation-plan/0.1.0-alpha.4/schema.json",
            "78f666674061f748078f39b79f6504f3ad01570e15af9380da68c9688d50a4ca",
            SchemaVersionAlpha4,
            ConsumerContractProvenance),
    ];

    /// <summary>Initializes an explicitly composed schema module.</summary>
    public PlanningSchemaModule()
    {
    }

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:planning-schemas");

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

        return typeof(PlanningSchemaModule).Assembly.GetManifestResourceStream(
                   string.Concat(ResourcePrefix, resource.ResourceName))
               ?? throw new InvalidOperationException(
                   string.Concat("The registered schema resource is unavailable: ", resource.ResourceName));
    }

    private static ProgramKitSchemaResource Create(
        string name,
        string resourceName,
        string canonicalUri,
        string digest,
        SemanticVersion version,
        ArtifactProvenance provenance) =>
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
            provenance,
            Compatibility(version));

    private static ArtifactCompatibility Compatibility(SemanticVersion version) =>
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
            new SemanticVersionRange(string.Concat("[", version.Value, "]")),
            new SemanticVersionRange(string.Concat("[", version.Value, "]")),
            []);

    private static string ExactKey(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);
}
