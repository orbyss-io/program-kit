using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation.Keycloak;

/// <summary>
/// Deterministic generator for the reviewed disposable Keycloak/Aspire fixture.
/// It resolves no secrets and performs no restore, browser, or container action.
/// </summary>
public sealed class KeycloakLocalFixtureGenerator :
    IKeycloakLocalFixtureGenerator
{
    private const string AspireVersion = "13.4.6";
    private const string AspireSourceCommit =
        "87fe259e4fc244c599019a7b1304c85a1488f248";
    private const string DotNetSdkVersion = "10.0.302";
    private const string TargetFramework = "net10.0";
    private const string AdminPasswordParameter = "keycloak-admin-password";
    private const string TestPasswordParameter = "keycloak-test-principal-password";
    private const string ConfidentialSecretParameter =
        "keycloak-confidential-client-secret";
    private const string ServiceSecretParameter = "keycloak-service-client-secret";
    private const string ExchangeSecretParameter =
        "keycloak-token-exchange-client-secret";

    /// <inheritdoc />
    public KeycloakLocalFixtureGenerationResult Generate(
        KeycloakLocalFixtureDefinition definition)
    {
        ArgumentNullException.ThrowIfNull(definition);
        Validate(definition);

        var realm = Output(
            string.Concat(
                "KeycloakFixture/Realm/",
                definition.RealmName,
                "-realm.json"),
            RenderRealm(definition));
        var outputs = ImmutableArray.Create(
                realm,
                Output(
                    "KeycloakFixture/AppHost/AppHost.csproj",
                    RenderProject()),
                Output(
                    "KeycloakFixture/AppHost/Program.cs",
                    RenderProgram(definition)),
                Output(
                    "KeycloakFixture/AppHost/global.json",
                    RenderGlobalJson()),
                Output(
                    "KeycloakFixture/AppHost/Properties/launchSettings.json",
                    RenderLaunchSettings(definition)),
                Output(
                    "KeycloakFixture/keycloak-fixture.lock.json",
                    RenderLock(definition, Hash(realm.Content.Span))),
                Output(
                    "KeycloakFixture/keycloak-fixture.profile.json",
                    RenderProfile(definition)),
                Output(
                    "KeycloakFixture/.gitignore",
                    RenderGitIgnore()),
                Output(
                    "KeycloakFixture/README.md",
                    RenderReadme(definition)))
            .OrderBy(static output => output.RelativePath, StringComparer.Ordinal)
            .ToImmutableArray();
        return new KeycloakLocalFixtureGenerationResult(outputs, HashTree(outputs));
    }

    private static void Validate(KeycloakLocalFixtureDefinition definition)
    {
        if (!ProgramKitIdentifier.Validate(definition.Identity.Value).IsValid ||
            definition.Secrets is null)
        {
            throw Failure(
                DotNetDiagnosticIds.InvalidKeycloakLocalFixture,
                "The fixture requires an exact identity and initialized secret references.",
                "/");
        }

        string[] names =
        [
            definition.RealmName,
            definition.ApiAudience,
            definition.ApiScope,
            definition.PublicClientId,
            definition.ConfidentialClientId,
            definition.ServiceClientId,
            definition.TokenExchangeClientId,
            definition.TestPrincipalName,
        ];
        if (names.Any(static name => !IsStableName(name)) ||
            names.Distinct(StringComparer.Ordinal).Count() != names.Length)
        {
            throw Failure(
                DotNetDiagnosticIds.InvalidKeycloakLocalFixture,
                "Realm, audience, scope, client, and principal names must be unique stable names.",
                "/");
        }

        var authorityPath = string.Concat("/realms/", definition.RealmName);
        if (!IsExactHttps(definition.Authority, authorityPath) ||
            !IsExactHttps(
                definition.MetadataAddress,
                string.Concat(
                    authorityPath,
                    "/.well-known/openid-configuration")) ||
            !SameOrigin(definition.Authority, definition.MetadataAddress) ||
            definition.Authority.Port is < 1 or > 65000)
        {
            throw Failure(
                DotNetDiagnosticIds.UnsupportedKeycloakFixtureProfile,
                "The local provider profile requires one exact HTTPS loopback authority and metadata address.",
                "/authority");
        }

        if (!IsExactHttps(
                definition.PublicRedirectUri,
                "/authentication/login-callback") ||
            !IsExactHttps(
                definition.PublicPostLogoutRedirectUri,
                "/authentication/logout-callback") ||
            !IsExactHttpsOrigin(definition.PublicBrowserOrigin) ||
            !SameOrigin(definition.PublicRedirectUri, definition.PublicBrowserOrigin) ||
            !SameOrigin(
                definition.PublicPostLogoutRedirectUri,
                definition.PublicBrowserOrigin) ||
            !IsExactHttps(definition.ConfidentialRedirectUri, "/signin-oidc"))
        {
            throw Failure(
                DotNetDiagnosticIds.UnsupportedKeycloakFixtureProfile,
                "Public and confidential callbacks must use exact HTTPS origins and reviewed callback paths.",
                "/clients");
        }

        var secrets = new[]
        {
            definition.Secrets.AdminPassword,
            definition.Secrets.TestPrincipalPassword,
            definition.Secrets.ConfidentialClientSecret,
            definition.Secrets.ServiceClientSecret,
            definition.Secrets.TokenExchangeClientSecret,
        };
        if (secrets.Any(static secret => !IsSafeConfigurationSecret(secret)) ||
            secrets.Select(static secret => secret.Identity.Value)
                .Distinct(StringComparer.Ordinal)
                .Count() != secrets.Length)
        {
            throw Failure(
                DotNetDiagnosticIds.UnsafeKeycloakFixtureMaterial,
                "Every runtime value requires one unique classified configuration-text reference.",
                "/secrets");
        }
    }

    private static string RenderRealm(KeycloakLocalFixtureDefinition definition)
    {
        var builder = new StringBuilder();
        builder.AppendLine("{");
        JsonProperty(builder, 1, "realm", definition.RealmName, true);
        builder.AppendLine("  \"enabled\": true,");
        builder.AppendLine("  \"sslRequired\": \"external\",");
        builder.AppendLine("  \"registrationAllowed\": false,");
        builder.AppendLine("  \"resetPasswordAllowed\": false,");
        builder.AppendLine("  \"rememberMe\": false,");
        builder.AppendLine("  \"verifyEmail\": false,");
        builder.AppendLine("  \"loginWithEmailAllowed\": false,");
        builder.AppendLine("  \"duplicateEmailsAllowed\": false,");
        builder.AppendLine("  \"accessTokenLifespan\": 300,");
        builder.AppendLine("  \"ssoSessionIdleTimeout\": 600,");
        builder.AppendLine("  \"ssoSessionMaxLifespan\": 1800,");
        builder.AppendLine("  \"clientScopes\": [");
        builder.AppendLine("    {");
        JsonProperty(builder, 3, "name", definition.ApiScope, true);
        builder.AppendLine("      \"protocol\": \"openid-connect\",");
        builder.AppendLine("      \"attributes\": {");
        builder.AppendLine("        \"include.in.token.scope\": \"true\",");
        builder.AppendLine("        \"display.on.consent.screen\": \"false\"");
        builder.AppendLine("      },");
        builder.AppendLine("      \"protocolMappers\": [");
        builder.AppendLine("        {");
        builder.AppendLine("          \"name\": \"program-kit-api-audience\",");
        builder.AppendLine("          \"protocol\": \"openid-connect\",");
        builder.AppendLine("          \"protocolMapper\": \"oidc-audience-mapper\",");
        builder.AppendLine("          \"consentRequired\": false,");
        builder.AppendLine("          \"config\": {");
        JsonProperty(
            builder,
            6,
            "included.client.audience",
            definition.ApiAudience,
            true);
        builder.AppendLine("            \"id.token.claim\": \"false\",");
        builder.AppendLine("            \"access.token.claim\": \"true\",");
        builder.AppendLine("            \"userinfo.token.claim\": \"false\"");
        builder.AppendLine("          }");
        builder.AppendLine("        }");
        builder.AppendLine("      ]");
        builder.AppendLine("    }");
        builder.AppendLine("  ],");
        builder.AppendLine("  \"clients\": [");
        RenderBrowserClient(builder, definition);
        builder.AppendLine(",");
        RenderConfidentialClient(builder, definition);
        builder.AppendLine(",");
        RenderServiceClient(
            builder,
            definition.ServiceClientId,
            "${PROGRAM_KIT_SERVICE_CLIENT_SECRET}",
            definition.ApiScope,
            false);
        builder.AppendLine(",");
        RenderServiceClient(
            builder,
            definition.TokenExchangeClientId,
            "${PROGRAM_KIT_TOKEN_EXCHANGE_CLIENT_SECRET}",
            definition.ApiScope,
            true);
        builder.AppendLine();
        builder.AppendLine("  ],");
        builder.AppendLine("  \"users\": [");
        builder.AppendLine("    {");
        JsonProperty(builder, 3, "username", definition.TestPrincipalName, true);
        builder.AppendLine("      \"enabled\": true,");
        builder.AppendLine("      \"emailVerified\": false,");
        builder.AppendLine("      \"credentials\": [");
        builder.AppendLine("        {");
        builder.AppendLine("          \"type\": \"password\",");
        builder.AppendLine(
            "          \"value\": \"${PROGRAM_KIT_TEST_PRINCIPAL_PASSWORD}\",");
        builder.AppendLine("          \"temporary\": false");
        builder.AppendLine("        }");
        builder.AppendLine("      ]");
        builder.AppendLine("    }");
        builder.AppendLine("  ]");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static void RenderBrowserClient(
        StringBuilder builder,
        KeycloakLocalFixtureDefinition definition)
    {
        builder.AppendLine("    {");
        JsonProperty(builder, 3, "clientId", definition.PublicClientId, true);
        builder.AppendLine("      \"protocol\": \"openid-connect\",");
        builder.AppendLine("      \"publicClient\": true,");
        builder.AppendLine("      \"standardFlowEnabled\": true,");
        builder.AppendLine("      \"implicitFlowEnabled\": false,");
        builder.AppendLine("      \"directAccessGrantsEnabled\": false,");
        builder.AppendLine("      \"serviceAccountsEnabled\": false,");
        builder.AppendLine("      \"redirectUris\": [");
        JsonArrayValue(builder, 4, definition.PublicRedirectUri.AbsoluteUri, false);
        builder.AppendLine("      ],");
        builder.AppendLine("      \"webOrigins\": [");
        JsonArrayValue(
            builder,
            4,
            definition.PublicBrowserOrigin.GetLeftPart(UriPartial.Authority),
            false);
        builder.AppendLine("      ],");
        builder.AppendLine("      \"defaultClientScopes\": [");
        JsonArrayValue(builder, 4, definition.ApiScope, false);
        builder.AppendLine("      ],");
        builder.AppendLine("      \"attributes\": {");
        builder.AppendLine("        \"pkce.code.challenge.method\": \"S256\",");
        builder.AppendLine("        \"access.token.header.type.rfc9068\": \"true\",");
        JsonProperty(
            builder,
            4,
            "post.logout.redirect.uris",
            string.Concat(definition.PublicPostLogoutRedirectUri.AbsoluteUri, "##"),
            false);
        builder.AppendLine("      }");
        builder.Append("    }");
    }

    private static void RenderConfidentialClient(
        StringBuilder builder,
        KeycloakLocalFixtureDefinition definition)
    {
        builder.AppendLine("    {");
        JsonProperty(
            builder,
            3,
            "clientId",
            definition.ConfidentialClientId,
            true);
        builder.AppendLine("      \"protocol\": \"openid-connect\",");
        builder.AppendLine("      \"publicClient\": false,");
        builder.AppendLine("      \"clientAuthenticatorType\": \"client-secret\",");
        builder.AppendLine(
            "      \"secret\": \"${PROGRAM_KIT_CONFIDENTIAL_CLIENT_SECRET}\",");
        builder.AppendLine("      \"standardFlowEnabled\": true,");
        builder.AppendLine("      \"implicitFlowEnabled\": false,");
        builder.AppendLine("      \"directAccessGrantsEnabled\": false,");
        builder.AppendLine("      \"serviceAccountsEnabled\": false,");
        builder.AppendLine("      \"redirectUris\": [");
        JsonArrayValue(
            builder,
            4,
            definition.ConfidentialRedirectUri.AbsoluteUri,
            false);
        builder.AppendLine("      ],");
        builder.AppendLine("      \"defaultClientScopes\": [");
        JsonArrayValue(builder, 4, definition.ApiScope, false);
        builder.AppendLine("      ],");
        builder.AppendLine("      \"attributes\": {");
        builder.AppendLine("        \"pkce.code.challenge.method\": \"S256\",");
        builder.AppendLine("        \"access.token.header.type.rfc9068\": \"true\"");
        builder.AppendLine("      }");
        builder.Append("    }");
    }

    private static void RenderServiceClient(
        StringBuilder builder,
        string clientId,
        string secretPlaceholder,
        string apiScope,
        bool tokenExchange)
    {
        builder.AppendLine("    {");
        JsonProperty(builder, 3, "clientId", clientId, true);
        builder.AppendLine("      \"protocol\": \"openid-connect\",");
        builder.AppendLine("      \"publicClient\": false,");
        builder.AppendLine("      \"clientAuthenticatorType\": \"client-secret\",");
        JsonProperty(builder, 3, "secret", secretPlaceholder, true);
        builder.AppendLine("      \"standardFlowEnabled\": false,");
        builder.AppendLine("      \"implicitFlowEnabled\": false,");
        builder.AppendLine("      \"directAccessGrantsEnabled\": false,");
        builder.AppendLine("      \"serviceAccountsEnabled\": true,");
        builder.AppendLine("      \"defaultClientScopes\": [");
        JsonArrayValue(builder, 4, apiScope, false);
        builder.AppendLine("      ],");
        builder.AppendLine("      \"attributes\": {");
        builder.AppendLine("        \"access.token.header.type.rfc9068\": \"true\",");
        builder.Append("        \"standard.token.exchange.enabled\": ")
            .AppendLine(tokenExchange ? "\"true\"" : "\"false\"");
        builder.AppendLine("      }");
        builder.Append("    }");
    }

    private static string RenderProject() =>
        string.Concat(
            "<Project Sdk=\"Aspire.AppHost.Sdk/", AspireVersion, "\">\n",
            "  <PropertyGroup>\n",
            "    <OutputType>Exe</OutputType>\n",
            "    <TargetFramework>", TargetFramework, "</TargetFramework>\n",
            "    <Nullable>enable</Nullable>\n",
            "    <ImplicitUsings>enable</ImplicitUsings>\n",
            "    <LangVersion>14.0</LangVersion>\n",
            "    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>\n",
            "    <EnableNETAnalyzers>true</EnableNETAnalyzers>\n",
            "    <AnalysisLevel>latest-all</AnalysisLevel>\n",
            "    <RestorePackagesWithLockFile>true</RestorePackagesWithLockFile>\n",
            "  </PropertyGroup>\n",
            "  <ItemGroup>\n",
            "    <PackageReference Include=\"Aspire.Hosting.AppHost\" Version=\"[",
            AspireVersion,
            "]\" />\n",
            "    <PackageReference Include=\"Aspire.Hosting.Keycloak\" Version=\"[",
            KeycloakLocalFixtureCatalog.AspireKeycloakPackageVersion,
            "]\" />\n",
            "  </ItemGroup>\n",
            "</Project>\n");

    private static string RenderProgram(KeycloakLocalFixtureDefinition definition)
    {
        var builder = new StringBuilder();
        builder.AppendLine("// <auto-generated program-kit>");
        builder.AppendLine("#nullable enable");
        builder.AppendLine();
        builder.AppendLine(
            "var builder = global::Aspire.Hosting.DistributedApplication.CreateBuilder(args);");
        builder.AppendLine(
            "var adminUsername = builder.AddParameter(\"keycloak-admin-username\");");
        SecretParameter(builder, "adminPassword", AdminPasswordParameter);
        SecretParameter(builder, "testPrincipalPassword", TestPasswordParameter);
        SecretParameter(
            builder,
            "confidentialClientSecret",
            ConfidentialSecretParameter);
        SecretParameter(builder, "serviceClientSecret", ServiceSecretParameter);
        SecretParameter(builder, "tokenExchangeClientSecret", ExchangeSecretParameter);
        builder.AppendLine();
        builder.Append("var keycloak = builder.AddKeycloak(\"keycloak\", ")
            .Append(definition.Authority.Port.ToString(CultureInfo.InvariantCulture))
            .AppendLine(", adminUsername, adminPassword)");
        builder.AppendLine(
            "    .WithImage(\"keycloak/keycloak\", \"26.7.0\")");
        builder.Append("    .WithImageSHA256(")
            .Append(DotNetSourceText.CSharpLiteral(
                KeycloakLocalFixtureCatalog.KeycloakImageSha256))
            .AppendLine(")");
        builder.AppendLine("    .WithRealmImport(\"../Realm\")");
        builder.Append("    .WithHttpEndpoint(port: ")
            .Append((definition.Authority.Port + 1).ToString(CultureInfo.InvariantCulture))
            .AppendLine(", targetPort: 9000, name: \"management\")");
        Environment(builder, "KC_HOSTNAME", definition.Authority.GetLeftPart(UriPartial.Authority));
        ParameterEnvironment(
            builder,
            "PROGRAM_KIT_TEST_PRINCIPAL_PASSWORD",
            "testPrincipalPassword");
        ParameterEnvironment(
            builder,
            "PROGRAM_KIT_CONFIDENTIAL_CLIENT_SECRET",
            "confidentialClientSecret");
        ParameterEnvironment(
            builder,
            "PROGRAM_KIT_SERVICE_CLIENT_SECRET",
            "serviceClientSecret");
        ParameterEnvironment(
            builder,
            "PROGRAM_KIT_TOKEN_EXCHANGE_CLIENT_SECRET",
            "tokenExchangeClientSecret");
        builder.AppendLine(
            "    .WithLifetime(global::Aspire.Hosting.ApplicationModel.ContainerLifetime.Session);");
        builder.AppendLine();
        builder.AppendLine("builder.Build().Run();");
        return builder.ToString();
    }

    private static string RenderGlobalJson() =>
        string.Concat(
            "{\n",
            "  \"sdk\": {\n",
            "    \"version\": \"", DotNetSdkVersion, "\",\n",
            "    \"rollForward\": \"disable\",\n",
            "    \"allowPrerelease\": false\n",
            "  }\n",
            "}\n");

    private static string RenderLaunchSettings(
        KeycloakLocalFixtureDefinition definition)
    {
        var dashboardHttps = definition.Authority.Port + 10;
        var dashboardHttp = definition.Authority.Port + 11;
        var dashboardOtlp = definition.Authority.Port + 12;
        var dashboardOtlpHttp = definition.Authority.Port + 13;
        var resourceService = definition.Authority.Port + 14;
        var applicationUrls = string.Concat(
            "https://localhost:",
            dashboardHttps.ToString(CultureInfo.InvariantCulture),
            ";http://localhost:",
            dashboardHttp.ToString(CultureInfo.InvariantCulture));
        return string.Concat(
            "{\n",
            "  \"$schema\": \"https://json.schemastore.org/launchsettings.json\",\n",
            "  \"profiles\": {\n",
            "    \"https\": {\n",
            "      \"commandName\": \"Project\",\n",
            "      \"dotnetRunMessages\": false,\n",
            "      \"launchBrowser\": false,\n",
            "      \"applicationUrl\": \"",
            applicationUrls,
            "\",\n",
            "      \"environmentVariables\": {\n",
            "        \"ASPNETCORE_ENVIRONMENT\": \"Development\",\n",
            "        \"DOTNET_ENVIRONMENT\": \"Development\",\n",
            "        \"ASPNETCORE_URLS\": \"",
            applicationUrls,
            "\",\n",
            "        \"ASPIRE_DASHBOARD_OTLP_ENDPOINT_URL\": \"https://localhost:",
            dashboardOtlp.ToString(CultureInfo.InvariantCulture),
            "\",\n",
            "        \"ASPIRE_DASHBOARD_OTLP_HTTP_ENDPOINT_URL\": \"https://localhost:",
            dashboardOtlpHttp.ToString(CultureInfo.InvariantCulture),
            "\",\n",
            "        \"ASPIRE_RESOURCE_SERVICE_ENDPOINT_URL\": \"https://localhost:",
            resourceService.ToString(CultureInfo.InvariantCulture),
            "\",\n",
            "        \"ASPIRE_DCP_USE_DEVELOPER_CERTIFICATE\": \"true\",\n",
            "        \"ASPIRE_VERSION_CHECK_DISABLED\": \"true\",\n",
            "        \"ASPIRE_DASHBOARD_TELEMETRY_OPTOUT\": \"true\",\n",
            "        \"ASPIRE_DASHBOARD_AI_DISABLED\": \"true\"\n",
            "      }\n",
            "    }\n",
            "  }\n",
            "}\n");
    }

    private static string RenderLock(
        KeycloakLocalFixtureDefinition definition,
        Sha256Digest realmDigest)
    {
        var builder = new StringBuilder();
        builder.AppendLine("{");
        builder.AppendLine("  \"lockKind\": \"program-kit-keycloak-local-fixture\",");
        builder.AppendLine("  \"lockVersion\": \"1.0.0\",");
        JsonProperty(builder, 1, "fixtureIdentity", definition.Identity.Value, true);
        JsonProperty(builder, 1, "fixtureVersion", definition.Version.Value, true);
        JsonProperty(builder, 1, "realmSha256", realmDigest.Value, true);
        builder.AppendLine("  \"aspire\": {");
        builder.AppendLine("    \"version\": \"13.4.6\",");
        JsonProperty(builder, 2, "sourceCommit", AspireSourceCommit, true);
        builder.AppendLine("    \"hostingKeycloak\": {");
        JsonProperty(
            builder,
            3,
            "version",
            KeycloakLocalFixtureCatalog.AspireKeycloakPackageVersion,
            true);
        JsonProperty(
            builder,
            3,
            "packageSha256",
            string.Concat(
                "sha256:",
                KeycloakLocalFixtureCatalog.AspireKeycloakPackageSha256),
            true);
        JsonProperty(
            builder,
            3,
            "assemblySha256",
            string.Concat(
                "sha256:",
                KeycloakLocalFixtureCatalog.AspireKeycloakAssemblySha256),
            false);
        builder.AppendLine("    }");
        builder.AppendLine("  },");
        builder.AppendLine("  \"keycloak\": {");
        JsonProperty(
            builder,
            2,
            "version",
            KeycloakLocalFixtureCatalog.KeycloakVersion,
            true);
        JsonProperty(
            builder,
            2,
            "sourceCommit",
            KeycloakLocalFixtureCatalog.KeycloakSourceCommit,
            true);
        builder.AppendLine(
            "    \"image\": \"quay.io/keycloak/keycloak:26.7.0\",");
        JsonProperty(
            builder,
            2,
            "imageSha256",
            string.Concat(
                "sha256:",
                KeycloakLocalFixtureCatalog.KeycloakImageSha256),
            false);
        builder.AppendLine("  },");
        builder.AppendLine("  \"secretReferenceSha256\": [");
        var digests = SecretReferences(definition)
            .Select(static secret => HashText(secret.Identity.Value).Value)
            .Order(StringComparer.Ordinal)
            .ToArray();
        for (var index = 0; index < digests.Length; index++)
        {
            JsonArrayValue(
                builder,
                2,
                digests[index],
                index < digests.Length - 1);
        }

        builder.AppendLine("  ],");
        builder.AppendLine("  \"executionAuthorized\": false,");
        builder.AppendLine("  \"productionProvisioning\": false,");
        builder.AppendLine("  \"persistentState\": false,");
        builder.AppendLine(
            "  \"platformSpecificRestore\": \"deferred-to-separate-human-started-restore\"");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderProfile(KeycloakLocalFixtureDefinition definition)
    {
        var builder = new StringBuilder();
        builder.AppendLine("{");
        builder.AppendLine("  \"profileKind\": \"keycloak-local-test\",");
        builder.AppendLine("  \"profileVersion\": \"1.0.0\",");
        JsonProperty(
            builder,
            1,
            "authority",
            definition.Authority.AbsoluteUri.TrimEnd('/'),
            true);
        JsonProperty(
            builder,
            1,
            "metadataAddress",
            definition.MetadataAddress.AbsoluteUri,
            true);
        JsonProperty(builder, 1, "audience", definition.ApiAudience, true);
        JsonProperty(builder, 1, "scope", definition.ApiScope, true);
        builder.AppendLine("  \"profiles\": [");
        builder.AppendLine("    \"oidc-public-browser-code-pkce\",");
        builder.AppendLine("    \"oidc-confidential-code-pkce\",");
        builder.AppendLine("    \"rfc9068-jwt-resource-server\",");
        builder.AppendLine("    \"oauth-client-credentials\",");
        builder.AppendLine("    \"rfc8693-token-exchange\"");
        builder.AppendLine("  ],");
        builder.AppendLine("  \"providerConclusions\": false,");
        builder.AppendLine("  \"domainAuthorizationMeaning\": false,");
        builder.AppendLine(
            "  \"runtimeTransport\": \"https-loopback-existing-dotnet-developer-certificate\",");
        builder.AppendLine(
            "  \"executionGate\": \"PROGRAM_KIT_RUN_KEYCLOAK_FIXTURE=1\",");
        builder.AppendLine("  \"evidence\": \"redacted-non-authoritative-outcomes-only\"");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderGitIgnore() =>
        string.Concat(
            "Runtime/\n",
            "AppHost/.aspire/\n",
            "AppHost/logs/\n",
            "AppHost/bin/\n",
            "AppHost/obj/\n",
            "**/playwright/.auth/\n",
            "**/test-results/\n",
            "**/*.har\n",
            "**/*.trace.zip\n",
            "**/*.webm\n");

    private static string RenderReadme(KeycloakLocalFixtureDefinition definition) =>
        string.Concat(
            "# Disposable Keycloak fixture\n\n",
            "This generated fixture is a provider-substitution proof for `",
            definition.RealmName,
            "`. It is not a realm backup, migration, production provisioning ",
            "tool, or identity/authorization model.\n\n",
            "Generation does not restore packages, resolve secrets, create TLS ",
            "material, start Aspire, start Keycloak, or open a browser. The ",
            "separately human-started integration profile must supply all ",
            "parameters. Aspire uses the existing trusted .NET HTTPS developer ",
            "certificate selected by the generated launch profile; generation ",
            "and execution never create, trust, remove, or otherwise mutate ",
            "certificate state. The profile must retain only ",
            "redacted outcome evidence, and remove its owned state.\n");

    private static void SecretParameter(
        StringBuilder builder,
        string variable,
        string name) =>
        builder.Append("var ")
            .Append(variable)
            .Append(" = builder.AddParameter(")
            .Append(DotNetSourceText.CSharpLiteral(name))
            .AppendLine(", secret: true);");

    private static void Environment(
        StringBuilder builder,
        string name,
        string value) =>
        builder.Append("    .WithEnvironment(")
            .Append(DotNetSourceText.CSharpLiteral(name))
            .Append(", ")
            .Append(DotNetSourceText.CSharpLiteral(value))
            .AppendLine(")");

    private static void ParameterEnvironment(
        StringBuilder builder,
        string name,
        string variable) =>
        builder.Append("    .WithEnvironment(")
            .Append(DotNetSourceText.CSharpLiteral(name))
            .Append(", ")
            .Append(variable)
            .AppendLine(")");

    private static void JsonProperty(
        StringBuilder builder,
        int indent,
        string name,
        string value,
        bool comma)
    {
        builder.Append(' ', indent * 2)
            .Append(DotNetSourceText.JsonLiteral(name))
            .Append(": ")
            .Append(DotNetSourceText.JsonLiteral(value));
        builder.AppendLine(comma ? "," : string.Empty);
    }

    private static void JsonArrayValue(
        StringBuilder builder,
        int indent,
        string value,
        bool comma)
    {
        builder.Append(' ', indent * 2)
            .Append(DotNetSourceText.JsonLiteral(value));
        builder.AppendLine(comma ? "," : string.Empty);
    }

    private static bool IsSafeConfigurationSecret(SecretReferenceDescriptor? secret) =>
        secret is not null &&
        ProgramKitIdentifier.Validate(secret.Identity.Value).IsValid &&
        secret.ExpectedResultKind == SecretResultKind.ConfigurationText &&
        secret.Classification != SecretReferenceClassification.Unspecified &&
        secret.LocatorClassification != SecretReferenceClassification.Unspecified;

    private static ImmutableArray<SecretReferenceDescriptor> SecretReferences(
        KeycloakLocalFixtureDefinition definition) =>
        [
            definition.Secrets.AdminPassword,
            definition.Secrets.TestPrincipalPassword,
            definition.Secrets.ConfidentialClientSecret,
            definition.Secrets.ServiceClientSecret,
            definition.Secrets.TokenExchangeClientSecret,
        ];

    private static bool IsStableName(string? value) =>
        value is { Length: >= 1 and <= 128 } &&
        value[0] is >= 'a' and <= 'z' &&
        value.All(static character =>
            character is >= 'a' and <= 'z' or
                >= '0' and <= '9' or '-' or '_' or '.');

    private static bool IsExactHttps(Uri? value, string path) =>
        value is { IsAbsoluteUri: true } &&
        string.Equals(value.Scheme, Uri.UriSchemeHttps, StringComparison.Ordinal) &&
        value.IsLoopback &&
        string.Equals(value.AbsolutePath, path, StringComparison.Ordinal) &&
        value.Query.Length == 0 &&
        value.Fragment.Length == 0 &&
        value.UserInfo.Length == 0;

    private static bool IsExactHttpsOrigin(Uri? value) =>
        IsExactHttps(value, "/");

    private static bool SameOrigin(Uri first, Uri second) =>
        string.Equals(
            first.GetLeftPart(UriPartial.Authority),
            second.GetLeftPart(UriPartial.Authority),
            StringComparison.Ordinal);

    private static GeneratedOutput Output(string path, string text) =>
        new(path, DotNetSourceText.Utf8(text));

    private static Sha256Digest Hash(ReadOnlySpan<byte> bytes) =>
        new(string.Concat(
            "sha256:",
            Convert.ToHexStringLower(SHA256.HashData(bytes))));

    private static Sha256Digest HashText(string value) =>
        Hash(Encoding.UTF8.GetBytes(value));

    private static Sha256Digest HashTree(ImmutableArray<GeneratedOutput> outputs)
    {
        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        foreach (var output in outputs.OrderBy(
                     static output => output.RelativePath,
                     StringComparer.Ordinal))
        {
            hash.AppendData(Encoding.UTF8.GetBytes(output.RelativePath));
            hash.AppendData([0]);
            hash.AppendData(output.Content.Span);
            hash.AppendData([0]);
        }

        return new Sha256Digest(
            string.Concat(
                "sha256:",
                Convert.ToHexStringLower(hash.GetHashAndReset())));
    }

    private static DotNetKitException Failure(
        string diagnosticId,
        string message,
        string path) =>
        DotNetKitException.Create(diagnosticId, message, path);
}
