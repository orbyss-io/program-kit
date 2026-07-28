namespace Orbyss.ProgramKit.DotNet.Schemas;

/// <summary>Explicit immutable module for DotNet shell and integrator-document schemas.</summary>
public sealed class DotNetSchemaModule : IProgramKitSchemaModule
{
    private readonly IProgramKitSchemaModule operationsSchemas;
    private readonly IProgramKitSchemaModule secretResolutionSchemas;
    private readonly ImmutableArray<ProgramKitSchemaResource> registered;
    private static readonly SemanticVersion CatalogVersion = new("11.5.0");
    private static readonly SemanticVersion SchemaVersionAlpha1 =
        new("0.1.0-alpha.1");
    private static readonly SemanticVersion SchemaVersionV1 = new("1.0.0");
    private static readonly SemanticVersion SchemaVersionV2 = new("2.0.0");
    private static readonly SemanticVersion SchemaVersionV3 = new("3.0.0");
    private static readonly SemanticVersion SchemaVersionV4 = new("4.0.0");
    private static readonly SemanticVersion SchemaVersionV5 = new("5.0.0");
    private static readonly SemanticVersion SchemaVersionV6 = new("6.0.0");
    private static readonly SemanticVersion SchemaVersionV7 = new("7.0.0");
    private static readonly SemanticVersion SchemaVersionV8 = new("8.0.0");
    private static readonly SemanticVersion SchemaVersionV9 = new("9.0.0");
    private static readonly SemanticVersion SchemaVersionV10 = new("10.0.0");
    private static readonly SemanticVersion SchemaVersionV11 = new("11.0.0");
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
    private static readonly ArtifactProvenance OAuthServiceClientProvenance =
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
            "pkht-w055-approved-review-set-1-3-0");
    private static readonly ArtifactProvenance AzureKeyVaultProvenance =
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
            "pkht-w040-human-approved-key-vault-only-adjustment");
    private static readonly ArtifactProvenance FastEndpointsProvenance =
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
            "pkht-w090-approved-review-set-1-3-0");
    private static readonly ArtifactProvenance KeycloakFixtureProvenance =
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
                new ArtifactReference(
                    new ProgramKitIdentifier(
                        "pkid:design:program-kit:host-tooling-keycloak-tls-proof"),
                    new SemanticVersion("1.0.0"),
                    new Sha256Digest(
                        "sha256:094459fa8813d04f3ab0f97764770d80564657d27be04762c78e6a726d9d6a11")),
                new ArtifactReference(
                    new ProgramKitIdentifier(
                        "pkid:plan:program-kit:host-tooling-keycloak-tls-proof"),
                    new SemanticVersion("1.0.0"),
                    new Sha256Digest(
                        "sha256:a7aae926ae5916f2ccdbda28a2dc70dfc008e43236718c3a5ed1ee644831c39a")),
            ],
            new ProgramKitIdentifier("pkid:project:program-kit:dotnet"),
            "pkkc-w010-approved-correction-1-0-0");
    private static readonly ArtifactProvenance TypedConsoleProvenance =
        new(
            [
                new ArtifactReference(
                    new ProgramKitIdentifier(
                        "pkid:design:program-kit:typed-console-host-generation"),
                    new SemanticVersion("1.0.0"),
                    new Sha256Digest(
                        "sha256:72bfa056c3e0f19d1765d9feae9aa5eb4ccb546a07896f2682a276294abcd4ca")),
                new ArtifactReference(
                    new ProgramKitIdentifier(
                        "pkid:plan:program-kit:typed-console-host-generation"),
                    new SemanticVersion("1.0.0"),
                    new Sha256Digest(
                        "sha256:207c47c0150bb91df564937225fdbb44f30dd2b403f21c6468d6abac70fbe273")),
            ],
            new ProgramKitIdentifier("pkid:project:program-kit:dotnet"),
            "pktch-w020-approved-review-set-1-0-0");
    private static readonly ArtifactProvenance
        ConsoleCliReachabilityProvenance =
            new(
                [
                    new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:design:program-kit:console-generation-cli-reachability"),
                        new SemanticVersion("0.1.0-alpha.1"),
                        new Sha256Digest(
                            "sha256:0a2479ab1c0d746418fea77b85fc09a694a39c7183d6ea10e53ada054e44157e")),
                    new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:plan:program-kit:console-generation-cli-reachability"),
                        new SemanticVersion("0.1.0-alpha.1"),
                        new Sha256Digest(
                            "sha256:90606b64907b16b677aba485b50bb21b5b0953b271b9bae6b7b5236048631289")),
                ],
                new ProgramKitIdentifier("pkid:project:program-kit:dotnet"),
                "pkcg-w010-approved-review-set-0-1-0-alpha-1");
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
            "dotnet-artifact-input-manifest",
            "artifact-input-manifest-0.1.0-alpha.1.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/0.1.0-alpha.1/artifact-input-manifest.schema.json",
            "db2fdb4bc96a2e4e9b625e6b232681ec1a7526f5ba46593ae3ce610e8a5b4534",
            SchemaVersionAlpha1,
            ConsoleCliReachabilityProvenance),
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
            "dotnet-shell",
            "dotnet-shell-9.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/9.0.0/dotnet-shell.schema.json",
            "f25df5b350c36a4189a4007f2dad7908f72b40df50e705933913315d53c11d7b",
            SchemaVersionV9,
            OAuthServiceClientProvenance),
        Create(
            "dotnet-security-composition",
            "dotnet-security-composition-3.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/security-composition/3.0.0/schema.json",
            "6064358be2a5636ef459b01d4503e112da63e4512d816741bbb13f74879a0343",
            SchemaVersionV3,
            OAuthServiceClientProvenance),
        Create(
            "dotnet-shell",
            "dotnet-shell-10.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/10.0.0/dotnet-shell.schema.json",
            "0bc42230ee4c1d03aa07235fcde2abcd483f5817e7008f23c5bc29d8e209f08a",
            SchemaVersionV10,
            AzureKeyVaultProvenance),
        Create(
            "dotnet-shell",
            "dotnet-shell-11.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/11.0.0/dotnet-shell.schema.json",
            "17d9ce99d9d717c874f4e398081b056232a1533ef038a4c5c35e3b7896e0caec",
            SchemaVersionV11,
            FastEndpointsProvenance),
        Create(
            "dotnet-azure-key-vault-composition",
            "dotnet-azure-key-vault-composition.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/azure-key-vault-composition/1.0.0/schema.json",
            "873f1d6f1f98b7bee34a4f562b5a3919793dd0146d6f432f965afa2189799eea",
            SchemaVersionV1,
            AzureKeyVaultProvenance),
        Create(
            "dotnet-keycloak-local-realm-import",
            "keycloak-local-realm-import-1.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/keycloak-local-realm-import/1.0.0/schema.json",
            "e07e6a18cca49f4449bc82346a1a089a53573ac3b58390fdeeed86a77042ba3c",
            SchemaVersionV1,
            KeycloakFixtureProvenance),
        Create(
            "dotnet-keycloak-local-fixture-profile",
            "keycloak-local-fixture-profile-1.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/keycloak-local-fixture-profile/1.0.0/schema.json",
            "15d77ff5f65b33e313f150e8acb000be88079e6774e97928b745bb3cab70c35d",
            SchemaVersionV1,
            KeycloakFixtureProvenance),
        Create(
            "dotnet-configuration-provider-catalog",
            "dotnet-configuration-provider-catalog-2.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/configuration-provider-catalog/2.0.0/schema.json",
            "6662822e3707c822b692753ae244316e861f6b17e0a8114db4f7dc4b91e6d85a",
            SchemaVersionV2,
            AzureKeyVaultProvenance),
        Create(
            "dotnet-console-binding",
            "dotnet-console-binding-1.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/console-binding/1.0.0/schema.json",
            "d5db01326609f83b39dbc1275afbde67b43ac9664d3915a2cdbc300b06da47e9",
            SchemaVersionV1,
            TypedConsoleProvenance),
        Create(
            "dotnet-host-generation-request",
            "dotnet-host-generation-request-1.0.0.schema.json",
            "https://schemas.orbyss.io/program-kit/dotnet/host-generation-request/1.0.0/schema.json",
            "5736c320bb96148aa6c6f770d4316232728fd87c69948713ab4c1420cd853a26",
            SchemaVersionV1,
            TypedConsoleProvenance),
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
    /// Initializes the DotNet module with exact Operations and secret-resolution
    /// dependency schemas required by its projections.
    /// </summary>
    public DotNetSchemaModule(
        IProgramKitSchemaModule operationsSchemas,
        IProgramKitSchemaModule secretResolutionSchemas)
    {
        ArgumentNullException.ThrowIfNull(operationsSchemas);
        ArgumentNullException.ThrowIfNull(secretResolutionSchemas);
        this.operationsSchemas = operationsSchemas;
        this.secretResolutionSchemas = secretResolutionSchemas;
        registered = Owned
            .AddRange(operationsSchemas.Resources)
            .AddRange(secretResolutionSchemas.Resources);
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

        if (secretResolutionSchemas.Resources.Any(candidate =>
                candidate.SchemaReference == schemaReference))
        {
            return secretResolutionSchemas.OpenRead(schemaReference);
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
            Compatibility(name, version));

    private static ArtifactCompatibility Compatibility(
        string name,
        SemanticVersion version) =>
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
            name == "dotnet-configuration-provider-catalog" &&
            version == SchemaVersionV2
                ?
                [
                    new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:migration:program-kit:dotnet-configuration-provider-catalog-v1-to-v2"),
                        new SemanticVersion("1.0.0"),
                        new Sha256Digest(
                            "sha256:76ed434b6c743180926caadc0d4ce9e1adf74a30e39f432507a53771b3e7d5c6")),
                ]
                : version switch
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
                    _ when version == SchemaVersionV9 =>
                    [
                        new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:migration:program-kit:dotnet-oauth-service-clients-v8-to-v9"),
                        new SemanticVersion("1.0.0"),
                        new Sha256Digest(
                            "sha256:d7842fbef99eda9ca69d3e8beccd88af54f470bdac7e93b0afa0d796babfa179")),
                ],
                    _ when version == SchemaVersionV10 =>
                    [
                        new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:migration:program-kit:dotnet-azure-key-vault-v9-to-v10"),
                        new SemanticVersion("1.0.0"),
                        new Sha256Digest(
                            "sha256:1cee0a9842dfcd73f675a943b1cde203dd7879334f9994764583871506c1b3ad")),
                ],
                    _ when version == SchemaVersionV11 =>
                    [
                        new ArtifactReference(
                        new ProgramKitIdentifier(
                            "pkid:migration:program-kit:dotnet-fastendpoints-v10-to-v11"),
                        new SemanticVersion("1.0.0"),
                        new Sha256Digest(
                            "sha256:c909e8d4be626a8a075da56489eb48f54697fd8cbfc89ae460cda9548b380527")),
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
