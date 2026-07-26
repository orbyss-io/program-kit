namespace Orbyss.ProgramKit.DotNet.Schemas;

/// <summary>Explicit immutable module for DotNet shell and integrator-document schemas.</summary>
public sealed class DotNetSchemaModule : IProgramKitSchemaModule
{
    private readonly IProgramKitSchemaModule operationsSchemas;
    private readonly ImmutableArray<ProgramKitSchemaResource> registered;
    private static readonly SemanticVersion CatalogVersion = new("8.0.0");
    private static readonly SemanticVersion SchemaVersionV1 = new("1.0.0");
    private static readonly SemanticVersion SchemaVersionV2 = new("2.0.0");
    private static readonly SemanticVersion SchemaVersionV3 = new("3.0.0");
    private static readonly SemanticVersion SchemaVersionV4 = new("4.0.0");
    private static readonly SemanticVersion SchemaVersionV5 = new("5.0.0");
    private static readonly SemanticVersion SchemaVersionV6 = new("6.0.0");
    private static readonly SemanticVersion SchemaVersionV7 = new("7.0.0");
    private static readonly SemanticVersion SchemaVersionV8 = new("8.0.0");
    private static readonly ProgramKitIdentifier Owner =
        new("pkid:package:program-kit:dotnet");
    private static readonly ArtifactProvenance Provenance =
        new(
            [
                new ArtifactReference(
                    new ProgramKitIdentifier("pkid:design:program-kit:baseline"),
                    new SemanticVersion("0.3.0"),
                    new Sha256Digest("sha256:dbe65ea112a172761f5725c210add00867b8b9f7a180a8b5ee6f80e42dace1c9")),
                new ArtifactReference(
                    new ProgramKitIdentifier("pkid:plan:program-kit:baseline"),
                    new SemanticVersion("0.3.0"),
                    new Sha256Digest("sha256:6d7396d5eb71e0d064231110e2ccfcae2aea838ca851b1420ff310df127cd951")),
            ],
            new ProgramKitIdentifier("pkid:project:program-kit:dotnet"),
            "pk-w040-approved-review-set-0-3-0");
    private static readonly ArtifactProvenance HostToolingProvenance =
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
            new ProgramKitIdentifier("pkid:project:program-kit:dotnet"),
            "pkht-w010-approved-review-set-1-3-0");
    private static readonly ArtifactProvenance ConfigurationProvenance =
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
            new ProgramKitIdentifier("pkid:project:program-kit:dotnet"),
            "pkht-w020-approved-review-set-1-3-0");
    private static readonly ArtifactProvenance ProviderCatalogProvenance =
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
            new ProgramKitIdentifier("pkid:project:program-kit:dotnet"),
            "pkht-w030-approved-review-set-1-3-0");
    private static readonly ArtifactProvenance TelemetryProvenance =
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
            new ProgramKitIdentifier("pkid:project:program-kit:dotnet"),
            "pkht-w035-approved-review-set-1-3-0");
    private static readonly ArtifactProvenance TransportFailureProvenance =
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
            new ProgramKitIdentifier("pkid:project:program-kit:dotnet"),
            "pkht-w045-approved-review-set-1-3-0");
    private static readonly ArtifactProvenance SecurityProvenance =
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
            new ProgramKitIdentifier("pkid:project:program-kit:dotnet"),
            "pkht-w050-approved-review-set-1-3-0");
    private static readonly ArtifactProvenance PublicBrowserProvenance =
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
            new ProgramKitIdentifier("pkid:project:program-kit:dotnet"),
            "pkht-w052-approved-review-set-1-3-0");
    private static readonly ImmutableArray<ProgramKitSchemaResource> Owned =
    [
        Create(
            "dotnet-artifact-input-manifest",
            "artifact-input-manifest.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/1.0.0/artifact-input-manifest.schema.json",
            "f639632bc7f7770847521ffde74f71b1b787e1b357fdaaadc1e98c598ba27929",
            SchemaVersionV1,
            Provenance),
        Create(
            "dotnet-shell-lock",
            "dotnet-shell-lock.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/1.0.0/dotnet-shell-lock.schema.json",
            "a06c12685454d270bb579ea22f65cfba2d809758c1aa803f2cf6e47433ec4e19",
            SchemaVersionV1,
            Provenance),
        Create(
            "dotnet-shell",
            "dotnet-shell.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/1.0.0/dotnet-shell.schema.json",
            "6d79fb385d2fa623a69fa528b23135c0ffd8ac550023ee3d5b177d3b65b5db04",
            SchemaVersionV1,
            Provenance),
        Create(
            "dotnet-shell",
            "dotnet-shell-2.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/2.0.0/dotnet-shell.schema.json",
            "8f167365be99654e234674f55b95f749f3246aa1371be8a7f5e3294bf9c4d3e9",
            SchemaVersionV2,
            HostToolingProvenance),
        Create(
            "dotnet-shell",
            "dotnet-shell-3.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/3.0.0/dotnet-shell.schema.json",
            "6f3d60cee34c8baf00f27940790a1220676b452f8bf027eeaafdf8c5ab83d60e",
            SchemaVersionV3,
            ConfigurationProvenance),
        Create(
            "dotnet-shell",
            "dotnet-shell-4.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/4.0.0/dotnet-shell.schema.json",
            "689fd7bfec2e545f91a17eeab73f649fc3e09ff2d51af45868ffc9324665a9e0",
            SchemaVersionV4,
            ProviderCatalogProvenance),
        Create(
            "dotnet-configuration-provider-catalog",
            "dotnet-configuration-provider-catalog.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/configuration-provider-catalog/1.0.0/schema.json",
            "c557c6b4057da0fb83c99b0d8b9cf4fc1813139f5692f5b1b86aea770d345215",
            SchemaVersionV1,
            ProviderCatalogProvenance),
        Create(
            "dotnet-shell",
            "dotnet-shell-5.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/5.0.0/dotnet-shell.schema.json",
            "e338de2fb36732180cf3800e63badc3987c2380bc51ceb3db8ecf51fbd577648",
            SchemaVersionV5,
            TelemetryProvenance),
        Create(
            "dotnet-telemetry-composition",
            "dotnet-telemetry-composition.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/telemetry-composition/1.0.0/schema.json",
            "ec2bd8f25443582bc901c46094a006ce6364c1aab8a8f326b7f3ae04c65d3ed4",
            SchemaVersionV1,
            TelemetryProvenance),
        Create(
            "dotnet-shell",
            "dotnet-shell-6.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/6.0.0/dotnet-shell.schema.json",
            "543b7cc734c837fe57a46ecf5e229c436a435cab65a3b67bf55422b000df3221",
            SchemaVersionV6,
            TransportFailureProvenance),
        Create(
            "dotnet-transport-failure-composition",
            "dotnet-transport-failure-composition.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/transport-failure-composition/1.0.0/schema.json",
            "7279ddc217e79620cf0990af230ad1f2e203c12a09f81f259a966b7f892d8490",
            SchemaVersionV1,
            TransportFailureProvenance),
        Create(
            "dotnet-shell",
            "dotnet-shell-7.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/7.0.0/dotnet-shell.schema.json",
            "6a57c35bb1ee533be1667f23a2b0cc763cd2ce727800cb934ee0e8a23f9473f0",
            SchemaVersionV7,
            SecurityProvenance),
        Create(
            "dotnet-security-composition",
            "dotnet-security-composition.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/security-composition/1.0.0/schema.json",
            "a1578edc16e31a942d9c0f3049ec6e467891aadb4b9c39dfb0ea54edabeb721c",
            SchemaVersionV1,
            SecurityProvenance),
        Create(
            "dotnet-shell",
            "dotnet-shell-8.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/8.0.0/dotnet-shell.schema.json",
            "c34541a5f065ee379a76a5f1cd9e6bd9c1a11eb6c09cacdb70a47abc6e19310d",
            SchemaVersionV8,
            PublicBrowserProvenance),
        Create(
            "dotnet-security-composition",
            "dotnet-security-composition-2.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/security-composition/2.0.0/schema.json",
            "a97dadb5a216ffc4efa416e1492df8e6896d9af4e7b9166074f082ca53255f5a",
            SchemaVersionV2,
            PublicBrowserProvenance),
        Create(
            "open-console",
            "open-console.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/1.0.0/open-console.schema.json",
            "eed3583dd81b564dd7137e056f650468a17ad31076bdfe938a2520719a73c8e5",
            SchemaVersionV1,
            Provenance),
        Create(
            "open-worker",
            "open-worker.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/1.0.0/open-worker.schema.json",
            "e1b466d192b2d299e9e367daa0991acf6468c855058c4063974e2306bf7628b3",
            SchemaVersionV1,
            Provenance),
        Create(
            "openapi-3-2-0-informational",
            "openapi-3.2.0-2025-11-23.schema.json",
            "https://spec.openapis.org/oas/3.2/schema/2025-11-23",
            "7d48f01f37eeae4799041b371ad5f533f9f533fd2b0caa1011a8ba27c5b48b70",
            SchemaVersionV1,
            Provenance),
    ];
    /// <summary>
    /// Initializes the DotNet module with the exact Operations dependency
    /// schemas required by the operation projection.
    /// </summary>
    public DotNetSchemaModule(IProgramKitSchemaModule operationsSchemas)
    {
        ArgumentNullException.ThrowIfNull(operationsSchemas);
        this.operationsSchemas = operationsSchemas;
        registered = Owned.AddRange(operationsSchemas.Resources);
    }

    /// <inheritdoc />
    public ProgramKitIdentifier Identity { get; } =
        new("pkid:catalog:program-kit:dotnet-schemas");

    /// <inheritdoc />
    public SemanticVersion Version => CatalogVersion;

    /// <inheritdoc />
    public ImmutableArray<ProgramKitSchemaResource> Resources => registered;

    /// <inheritdoc />
    public Stream OpenRead(ArtifactReference schemaReference)
    {
        ArgumentNullException.ThrowIfNull(schemaReference);
        var key = ExactKey(schemaReference);
        var resource = registered.FirstOrDefault(candidate =>
            string.Equals(ExactKey(candidate.SchemaReference), key, StringComparison.Ordinal));
        if (resource is null)
        {
            throw new KeyNotFoundException(
                string.Concat("The exact DotNet schema is not registered: ", key));
        }

        if (operationsSchemas.Resources.Any(candidate =>
                candidate.SchemaReference == schemaReference))
        {
            return operationsSchemas.OpenRead(schemaReference);
        }

        var assembly = typeof(DotNetSchemaModule).Assembly;
        var resourceName = assembly.GetManifestResourceNames().Single(name =>
            name.EndsWith(resource.ResourceName, StringComparison.Ordinal));
        return assembly.GetManifestResourceStream(resourceName) ??
               throw new InvalidOperationException(
                   string.Concat("The registered DotNet schema is unavailable: ", resource.ResourceName));
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
            Owner,
            ArtifactStatus.Implemented,
            [
                new ProgramKitIdentifier("pkid:project:program-kit:workbench"),
                new ProgramKitIdentifier("pkid:project:program-kit:dotnet"),
                new ProgramKitIdentifier("pkid:test:program-kit:conformance-tests"),
            ],
            provenance,
            Compatibility(version));

    private static ArtifactCompatibility Compatibility(SemanticVersion version) =>
        new(
            new ProgramKitIdentifier("pkid:contract:program-kit:schema-compatibility-policy"),
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
            version switch
            {
                _ when version == SchemaVersionV2 =>
                [
                    new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:migration:program-kit:dotnet-operation-binding-v1-to-v2"),
                        new SemanticVersion("1.0.0"),
                        new Sha256Digest(
                            "sha256:a394d9ff69fe3f1f3d2f0941518ca81c9a79cb0ae092e1ba5579655b016a12b4")),
                ],
                _ when version == SchemaVersionV3 =>
                [
                    new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:migration:program-kit:dotnet-configuration-v2-to-v3"),
                        new SemanticVersion("1.0.0"),
                        new Sha256Digest(
                            "sha256:518c2c4d061a1407e205d6961689574e1e9139be9a68ba8fdab66ddbc9893565")),
                ],
                _ when version == SchemaVersionV4 =>
                [
                    new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:migration:program-kit:dotnet-configuration-v3-to-v4"),
                        new SemanticVersion("1.0.0"),
                        new Sha256Digest(
                            "sha256:052453c42eea7e74533c94d3582cda5e2dec093a9fcae18c04a5f84c13c74ccd")),
                ],
                _ when version == SchemaVersionV5 =>
                [
                    new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:migration:program-kit:dotnet-telemetry-v4-to-v5"),
                        new SemanticVersion("1.0.0"),
                        new Sha256Digest(
                            "sha256:0f3dc06cd571a1b7dc895ead592364d69945740d36330d118ccff8d592dcd765")),
                ],
                _ when version == SchemaVersionV6 =>
                [
                    new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:migration:program-kit:dotnet-transport-failures-v5-to-v6"),
                        new SemanticVersion("1.0.0"),
                        new Sha256Digest(
                            "sha256:b825ecf1b8f88b78609540019c947d82d0adab7a19c2ac83021783bf4ea52f65")),
                ],
                _ when version == SchemaVersionV7 =>
                [
                    new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:migration:program-kit:dotnet-security-v6-to-v7"),
                        new SemanticVersion("1.0.0"),
                        new Sha256Digest(
                            "sha256:0722776dc337a33714fc72d94780b52cad627ff1378d850de05dc8577385572f")),
                ],
                _ when version == SchemaVersionV8 =>
                [
                    new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:migration:program-kit:dotnet-public-browser-v7-to-v8"),
                        new SemanticVersion("1.0.0"),
                        new Sha256Digest(
                            "sha256:a3b5dac3c5ea69e16434b1a393805c5641c88aab0b9f46ca39b1d18fff26f01b")),
                ],
                _ => [],
            });

    private static string ExactKey(ArtifactReference reference) =>
        string.Concat(
            reference.Identity.Value,
            "@",
            reference.Version.Value,
            "#",
            reference.Digest.Value);
}
