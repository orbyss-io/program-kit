using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Compatibility;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Schemas;

/// <summary>
/// Explicit immutable allow-list of C# build-gate contract schemas. No
/// directory or assembly discovery is performed.
/// </summary>
public sealed class CSharpBuildGateSchemaModule : IProgramKitSchemaModule
{
    private const string ResourcePrefix =
        "Orbyss.ProgramKit.CSharpBuildGates.Contracts.Schemas.";
    private static readonly SemanticVersion VersionOne = new("1.0.0");
    private static readonly SemanticVersion VersionAlphaOne =
        new("0.1.0-alpha.1");
    private static readonly SemanticVersion VersionAlphaTwo =
        new("0.1.0-alpha.2");
    private static readonly SemanticVersion CatalogVersion =
        new("0.1.0-alpha.2");
    private static readonly ProgramKitIdentifier Owner =
        new("pkid:package:program-kit:csharp-build-gates-contracts");
    private static readonly ArtifactProvenance Provenance =
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
            new ProgramKitIdentifier(
                "pkid:project:program-kit:csharp-build-gates-contracts"),
            "pkcg-w030-approved-review-set-1-0-0");
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
            new SemanticVersionRange("[1.0.0]"),
            new SemanticVersionRange("[1.0.0]"),
            []);
    private static readonly ArtifactProvenance AmendmentProvenance =
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
            new ProgramKitIdentifier(
                "pkid:project:program-kit:csharp-build-gates-contracts"),
            "pkcj-w050-approved-review-set-0-1-0-alpha-1");

    private static readonly ImmutableArray<ProgramKitSchemaResource>
        SchemaResources =
        [
            Create(
                "csharp-build-gate-definitions",
                "definitions-0.1.0-alpha.1.schema.json",
                "https://schemas.orbyss.io/program-kit/csharp-build-gates/0.1.0-alpha.1/definitions.schema.json",
                "abf7014b586ce9d5d338aa60f9fc13c67dc78ebb2f2c625cbe5e2e5efc84c0b8",
                VersionAlphaOne),
            Create(
                "csharp-build-gate-definition",
                "csharp-build-gate-definition-0.1.0-alpha.1.schema.json",
                "https://schemas.orbyss.io/program-kit/csharp-build-gates/definition/0.1.0-alpha.1/schema.json",
                "35a3662d59b85621ea8d2ab0bba03b23de056001cb4ad9b4385996db76da1638",
                VersionAlphaOne),
            Create(
                "csharp-build-gate-selection-lock",
                "csharp-build-gate-selection-lock-0.1.0-alpha.1.schema.json",
                "https://schemas.orbyss.io/program-kit/csharp-build-gates/selection-lock/0.1.0-alpha.1/schema.json",
                "c0d326108653b9e986df1a2b361611622d269df8072faf421eabec093e165cc5",
                VersionAlphaOne,
                AmendmentProvenance),
            Create(
                "csharp-gate-lock-intent",
                "csharp-gate-lock-intent-0.1.0-alpha.1.schema.json",
                "https://schemas.orbyss.io/program-kit/csharp-build-gates/lock-intent/0.1.0-alpha.1/schema.json",
                "5a8175d515606be5c3ee3ae671d1558a1833ccfda0176d671bc6fd5dbdc7163c",
                VersionAlphaOne,
                AmendmentProvenance),
            Create(
                "csharp-build-gate-definitions",
                "definitions-0.1.0-alpha.2.schema.json",
                "https://schemas.orbyss.io/program-kit/csharp-build-gates/0.1.0-alpha.2/definitions.schema.json",
                "a465dbd23bf6129f6556380d6f845bb1d95fd13b3ce8e3f0bef7ef4755df458f",
                VersionAlphaTwo),
            Create(
                "csharp-build-gate-definition",
                "csharp-build-gate-definition-0.1.0-alpha.2.schema.json",
                "https://schemas.orbyss.io/program-kit/csharp-build-gates/definition/0.1.0-alpha.2/schema.json",
                "d148082c24f9e6176f102d8be1b670d482cf93a93a0585baabd1dd5ab67ae878",
                VersionAlphaTwo),
            Create(
                "csharp-build-gate-definitions",
                "definitions-1.0.0.schema.json",
                "https://schemas.orbyss.io/program-kit/csharp-build-gates/1.0.0/definitions.schema.json",
                "274f99017fc649f442ea39ffdeebef798ddcae599dae8ac716010f93bb15f32e",
                VersionOne),
            Create(
                "csharp-build-gate-definition",
                "csharp-build-gate-definition-1.0.0.schema.json",
                "https://schemas.orbyss.io/program-kit/csharp-build-gates/definition/1.0.0/schema.json",
                "79aa72a795bb1741ea5fb62f7e1571bd17b854cab106b4a7e0435886b0828001",
                VersionOne),
            Create(
                "csharp-build-gate-selection-lock",
                "csharp-build-gate-selection-lock-1.0.0.schema.json",
                "https://schemas.orbyss.io/program-kit/csharp-build-gates/selection-lock/1.0.0/schema.json",
                "efde4229bf3b43901aa97d72935cc6d09ea5ecaa66645fb1b23a1f6c29a2809f",
                VersionOne),
            Create(
                "csharp-build-gate-suppression-ledger",
                "csharp-build-gate-suppression-ledger-1.0.0.schema.json",
                "https://schemas.orbyss.io/program-kit/csharp-build-gates/suppression-ledger/1.0.0/schema.json",
                "a5ef64253b4f70819ca69e11536e248866fe8d30c4bfd537f9d9091fae1efc9a",
                VersionOne),
            Create(
                "csharp-build-gate-participation-receipt",
                "csharp-build-gate-participation-receipt-1.0.0.schema.json",
                "https://schemas.orbyss.io/program-kit/csharp-build-gates/participation-receipt/1.0.0/schema.json",
                "6896ab5449a501eaa161e36e554a6706ca5550e359acf2c7109567f8cae97da7",
                VersionOne),
            Create(
                "csharp-build-gate-verification-evidence",
                "csharp-build-gate-verification-evidence-1.0.0.schema.json",
                "https://schemas.orbyss.io/program-kit/csharp-build-gates/verification-evidence/1.0.0/schema.json",
                "4cabcf61400e55ced9e1dcd2b036b0259b887ece2d026d19b976d0f116397423",
                VersionOne),
        ];

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:csharp-build-gate-schemas");

    /// <inheritdoc />
    public SemanticVersion Version => CatalogVersion;

    /// <inheritdoc />
    public ImmutableArray<ProgramKitSchemaResource> Resources => SchemaResources;

    /// <inheritdoc />
    public Stream OpenRead(ArtifactReference schemaReference)
    {
        ArgumentNullException.ThrowIfNull(schemaReference);
        var exact = ExactKey(schemaReference);
        var resource = SchemaResources.FirstOrDefault(candidate =>
            string.Equals(
                ExactKey(candidate.SchemaReference),
                exact,
                StringComparison.Ordinal));
        if (resource is null)
        {
            throw new KeyNotFoundException(
                string.Concat(
                    "The exact C# build-gate schema is not registered: ",
                    exact));
        }

        return typeof(CSharpBuildGateSchemaModule).Assembly
                   .GetManifestResourceStream(
                       string.Concat(ResourcePrefix, resource.ResourceName))
               ?? throw new InvalidOperationException(
                   string.Concat(
                       "The registered C# build-gate schema is unavailable: ",
                       resource.ResourceName));
    }

    private static ProgramKitSchemaResource Create(
        string name,
        string resourceName,
        string canonicalUri,
        string digest,
        SemanticVersion version,
        ArtifactProvenance? provenance = null) =>
        new(
            new ArtifactReference(
                new ProgramKitIdentifier(
                    string.Concat("pkid:schema:program-kit:", name)),
                version,
                new Sha256Digest(string.Concat("sha256:", digest))),
            new Uri(canonicalUri, UriKind.Absolute),
            resourceName,
            "application/schema+json",
            Owner,
            ArtifactStatus.Implemented,
            [
                new ProgramKitIdentifier(
                    "pkid:test:program-kit:conformance-tests"),
                new ProgramKitIdentifier(
                    "pkid:project:program-kit:csharp-build-gates-operations"),
            ],
            provenance ?? Provenance,
            CompatibilityFor(version));

    private static ArtifactCompatibility CompatibilityFor(
        SemanticVersion version)
    {
        var exact = new SemanticVersionRange(
            string.Concat("[", version.Value, "]"));
        return new ArtifactCompatibility(
            Compatibility.Policy,
            Compatibility.Dimensions,
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
