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
                    "KeycloakFixture/AppHost/ProgramKitFixtureTls.cs",
                    RenderFixtureTls()),
                Output(
                    "KeycloakFixture/AppHost/ProgramKitFixtureTrust.cs",
                    RenderFixtureTrustSource()),
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
            .AddRange(
                KeycloakGeneratedSecurityConsumerGenerator.Generate(definition))
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
            !string.Equals(
                definition.Authority.Host,
                KeycloakLocalFixtureCatalog.TlsProfile.ServerHostName,
                StringComparison.Ordinal) ||
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
        var tls = KeycloakLocalFixtureCatalog.TlsProfile;
        var builder = new StringBuilder();
        builder.AppendLine("// <auto-generated program-kit>");
        builder.AppendLine("#nullable enable");
        builder.AppendLine();
        builder.AppendLine(
            "using var executionCancellation = new global::System.Threading.CancellationTokenSource();");
        builder.AppendLine(
            "global::System.ConsoleCancelEventHandler cancelHandler = (_, eventArgs) =>");
        builder.AppendLine("{");
        builder.AppendLine("    eventArgs.Cancel = true;");
        builder.AppendLine("    executionCancellation.Cancel();");
        builder.AppendLine("};");
        builder.AppendLine("global::System.Console.CancelKeyPress += cancelHandler;");
        builder.AppendLine();
        builder.AppendLine("try");
        builder.AppendLine("{");
        builder.Append("    var runtimeRoot = global::System.Environment.GetEnvironmentVariable(")
            .Append(DotNetSourceText.CSharpLiteral(
                tls.RuntimeRootEnvironmentVariable))
            .AppendLine(") ??");
        builder.AppendLine(
            "        throw new global::System.InvalidOperationException(\"The exact disposable fixture runtime root is required.\");");
        builder.AppendLine(
            "    await using var fixtureTls = await global::ProgramKitFixtureTls.CreateAsync(");
        builder.AppendLine("        runtimeRoot,");
        builder.AppendLine("        executionCancellation.Token);");
        builder.AppendLine();
        builder.AppendLine(
            "    var builder = global::Aspire.Hosting.DistributedApplication.CreateBuilder(args);");
        builder.AppendLine(
            "    var adminUsername = builder.AddParameter(\"keycloak-admin-username\");");
        SecretParameter(builder, "    ", "adminPassword", AdminPasswordParameter);
        SecretParameter(
            builder,
            "    ",
            "testPrincipalPassword",
            TestPasswordParameter);
        SecretParameter(
            builder,
            "    ",
            "confidentialClientSecret",
            ConfidentialSecretParameter);
        SecretParameter(
            builder,
            "    ",
            "serviceClientSecret",
            ServiceSecretParameter);
        SecretParameter(
            builder,
            "    ",
            "tokenExchangeClientSecret",
            ExchangeSecretParameter);
        builder.AppendLine();
        builder.Append("    var keycloak = builder.AddKeycloak(\"keycloak\", ")
            .Append(definition.Authority.Port.ToString(CultureInfo.InvariantCulture))
            .AppendLine(", adminUsername, adminPassword)");
        builder.AppendLine(
            "    .WithImage(\"keycloak/keycloak\", \"26.7.0\")");
        builder.Append("    .WithImageSHA256(")
            .Append(DotNetSourceText.CSharpLiteral(
                KeycloakLocalFixtureCatalog.KeycloakImageSha256))
            .AppendLine(")");
        builder.AppendLine("    .WithRealmImport(\"../Realm\")");
        builder.AppendLine("    .WithEndpoint(\"http\", endpoint =>");
        builder.AppendLine("    {");
        builder.Append("        endpoint.Port = ")
            .Append(definition.Authority.Port.ToString(CultureInfo.InvariantCulture))
            .AppendLine(";");
        builder.Append("        endpoint.TargetPort = ")
            .Append(tls.ProviderHttpsTargetPort.ToString(CultureInfo.InvariantCulture))
            .AppendLine(";");
        builder.AppendLine("        endpoint.UriScheme = \"https\";");
        builder.AppendLine("    })");
        builder.Append("    .WithHttpEndpoint(port: ")
            .Append((definition.Authority.Port + 1).ToString(CultureInfo.InvariantCulture))
            .AppendLine(", targetPort: 9000, name: \"management\")");
        builder.Append("    .WithBindMount(fixtureTls.ServerCertificatePath, ")
            .Append(DotNetSourceText.CSharpLiteral(tls.ContainerCertificatePath))
            .AppendLine(", isReadOnly: true)");
        builder.Append("    .WithBindMount(fixtureTls.ServerPrivateKeyPath, ")
            .Append(DotNetSourceText.CSharpLiteral(tls.ContainerPrivateKeyPath))
            .AppendLine(", isReadOnly: true)");
        Environment(builder, "KC_HOSTNAME", definition.Authority.GetLeftPart(UriPartial.Authority));
        Environment(builder, "KC_HOSTNAME_STRICT", "true");
        Environment(builder, "KC_HTTP_ENABLED", "false");
        Environment(
            builder,
            "KC_HTTPS_PORT",
            tls.ProviderHttpsTargetPort.ToString(CultureInfo.InvariantCulture));
        Environment(
            builder,
            "KC_HTTPS_CERTIFICATE_FILE",
            tls.ContainerCertificatePath);
        Environment(
            builder,
            "KC_HTTPS_CERTIFICATE_KEY_FILE",
            tls.ContainerPrivateKeyPath);
        Environment(builder, "KC_HEALTH_ENABLED", "true");
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
        builder.AppendLine("    await using var application = builder.Build();");
        builder.AppendLine(
            "    await application.RunAsync(executionCancellation.Token);");
        builder.AppendLine("}");
        builder.AppendLine("finally");
        builder.AppendLine("{");
        builder.AppendLine(
            "    global::System.Console.CancelKeyPress -= cancelHandler;");
        builder.AppendLine("}");
        return builder.ToString();
    }

    private static string RenderFixtureTls()
    {
        var tls = KeycloakLocalFixtureCatalog.TlsProfile;
        return $$"""
            // <auto-generated program-kit>
            #nullable enable

            internal sealed class ProgramKitFixtureTls :
                global::System.IAsyncDisposable
            {
                private const string OwnedDirectoryName = "tls";
                private const string AuthorityCertificateFileName = "authority-certificate.pem";
                private const string ServerCertificateFileName = "keycloak-server-certificate.pem";
                private const string ServerPrivateKeyFileName = "keycloak-server-private-key.pem";
                private const string TrustDescriptorFileName = "trust.runtime.json";
                private readonly string ownedDirectory;
                private int disposed;

                private ProgramKitFixtureTls(
                    string ownedDirectory,
                    string authorityCertificatePath,
                    string serverCertificatePath,
                    string serverPrivateKeyPath,
                    string trustDescriptorPath,
                    string chromiumSpkiList)
                {
                    this.ownedDirectory = ownedDirectory;
                    AuthorityCertificatePath = authorityCertificatePath;
                    ServerCertificatePath = serverCertificatePath;
                    ServerPrivateKeyPath = serverPrivateKeyPath;
                    TrustDescriptorPath = trustDescriptorPath;
                    ChromiumSpkiList = chromiumSpkiList;
                }

                internal string AuthorityCertificatePath { get; }

                internal string ServerCertificatePath { get; }

                internal string ServerPrivateKeyPath { get; }

                internal string TrustDescriptorPath { get; }

                internal string ChromiumSpkiList { get; }

                internal static async global::System.Threading.Tasks.ValueTask<ProgramKitFixtureTls> CreateAsync(
                    string runtimeRoot,
                    global::System.Threading.CancellationToken cancellationToken)
                {
                    global::System.ArgumentException.ThrowIfNullOrWhiteSpace(runtimeRoot);
                    cancellationToken.ThrowIfCancellationRequested();
                    var fullRoot = global::System.IO.Path.GetFullPath(runtimeRoot);
                    var filesystemRoot = global::System.IO.Path.GetPathRoot(fullRoot);
                    var leaf = new global::System.IO.DirectoryInfo(fullRoot).Name;
                    if (string.Equals(
                            fullRoot.TrimEnd(
                                global::System.IO.Path.DirectorySeparatorChar,
                                global::System.IO.Path.AltDirectorySeparatorChar),
                            filesystemRoot?.TrimEnd(
                                global::System.IO.Path.DirectorySeparatorChar,
                                global::System.IO.Path.AltDirectorySeparatorChar),
                            global::System.StringComparison.OrdinalIgnoreCase) ||
                        !leaf.StartsWith(
                            "program-kit-keycloak-",
                            global::System.StringComparison.Ordinal) ||
                        leaf.Length == "program-kit-keycloak-".Length)
                    {
                        throw new global::System.InvalidOperationException(
                            "The fixture runtime root must be one exact non-root program-kit-keycloak-* directory.");
                    }

                    var ownedDirectory = global::System.IO.Path.Combine(
                        fullRoot,
                        OwnedDirectoryName);
                    if (global::System.IO.Directory.Exists(ownedDirectory))
                    {
                        throw new global::System.InvalidOperationException(
                            "The fixture TLS directory already exists and cannot be reused.");
                    }

                    global::System.IO.Directory.CreateDirectory(ownedDirectory);
                    var authorityCertificatePath = global::System.IO.Path.Combine(
                        ownedDirectory,
                        AuthorityCertificateFileName);
                    var serverCertificatePath = global::System.IO.Path.Combine(
                        ownedDirectory,
                        ServerCertificateFileName);
                    var serverPrivateKeyPath = global::System.IO.Path.Combine(
                        ownedDirectory,
                        ServerPrivateKeyFileName);
                    var trustDescriptorPath = global::System.IO.Path.Combine(
                        ownedDirectory,
                        TrustDescriptorFileName);

                    try
                    {
                        using var authorityKey = global::System.Security.Cryptography.RSA.Create(
                            {{tls.CertificateAuthorityKeySize.ToString(CultureInfo.InvariantCulture)}});
                        var authorityRequest =
                            new global::System.Security.Cryptography.X509Certificates.CertificateRequest(
                                "CN=Program Kit Keycloak Fixture Authority",
                                authorityKey,
                                global::System.Security.Cryptography.HashAlgorithmName.SHA256,
                                global::System.Security.Cryptography.RSASignaturePadding.Pkcs1);
                        authorityRequest.CertificateExtensions.Add(
                            new global::System.Security.Cryptography.X509Certificates.X509BasicConstraintsExtension(
                                certificateAuthority: true,
                                hasPathLengthConstraint: true,
                                pathLengthConstraint: 0,
                                critical: true));
                        authorityRequest.CertificateExtensions.Add(
                            new global::System.Security.Cryptography.X509Certificates.X509KeyUsageExtension(
                                global::System.Security.Cryptography.X509Certificates.X509KeyUsageFlags.KeyCertSign |
                                global::System.Security.Cryptography.X509Certificates.X509KeyUsageFlags.CrlSign,
                                critical: true));
                        authorityRequest.CertificateExtensions.Add(
                            new global::System.Security.Cryptography.X509Certificates.X509SubjectKeyIdentifierExtension(
                                authorityRequest.PublicKey,
                                critical: false));

                        var notBefore = global::System.DateTimeOffset.UtcNow.AddMinutes(
                            -{{tls.NotBeforeSkewMinutes.ToString(CultureInfo.InvariantCulture)}});
                        using var authorityCertificate =
                            authorityRequest.CreateSelfSigned(
                                notBefore,
                                notBefore.AddHours(
                                    {{tls.CertificateAuthorityValidityHours.ToString(CultureInfo.InvariantCulture)}}));

                        using var serverKey = global::System.Security.Cryptography.RSA.Create(
                            {{tls.ServerKeySize.ToString(CultureInfo.InvariantCulture)}});
                        var serverRequest =
                            new global::System.Security.Cryptography.X509Certificates.CertificateRequest(
                                "CN={{tls.ServerHostName}}",
                                serverKey,
                                global::System.Security.Cryptography.HashAlgorithmName.SHA256,
                                global::System.Security.Cryptography.RSASignaturePadding.Pkcs1);
                        serverRequest.CertificateExtensions.Add(
                            new global::System.Security.Cryptography.X509Certificates.X509BasicConstraintsExtension(
                                certificateAuthority: false,
                                hasPathLengthConstraint: false,
                                pathLengthConstraint: 0,
                                critical: true));
                        serverRequest.CertificateExtensions.Add(
                            new global::System.Security.Cryptography.X509Certificates.X509KeyUsageExtension(
                                global::System.Security.Cryptography.X509Certificates.X509KeyUsageFlags.DigitalSignature |
                                global::System.Security.Cryptography.X509Certificates.X509KeyUsageFlags.KeyEncipherment,
                                critical: true));
                        var usages =
                            new global::System.Security.Cryptography.OidCollection
                            {
                                new global::System.Security.Cryptography.Oid(
                                    "{{tls.ServerExtendedKeyUsageOid}}",
                                    "TLS Web Server Authentication"),
                            };
                        serverRequest.CertificateExtensions.Add(
                            new global::System.Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension(
                                usages,
                                critical: true));
                        var names =
                            new global::System.Security.Cryptography.X509Certificates.SubjectAlternativeNameBuilder();
                        names.AddDnsName("{{tls.ServerHostName}}");
                        names.AddIpAddress(global::System.Net.IPAddress.Loopback);
                        names.AddIpAddress(global::System.Net.IPAddress.IPv6Loopback);
                        serverRequest.CertificateExtensions.Add(names.Build(critical: true));
                        serverRequest.CertificateExtensions.Add(
                            new global::System.Security.Cryptography.X509Certificates.X509SubjectKeyIdentifierExtension(
                                serverRequest.PublicKey,
                                critical: false));

                        var serial = global::System.Security.Cryptography.RandomNumberGenerator.GetBytes(16);
                        serial[0] &= 0x7f;
                        serial[^1] |= 0x01;
                        using var issuedServerCertificate = serverRequest.Create(
                            authorityCertificate,
                            notBefore,
                            notBefore.AddHours(
                                {{tls.ServerCertificateValidityHours.ToString(CultureInfo.InvariantCulture)}}),
                            serial);
                        using var serverCertificate =
                            global::System.Security.Cryptography.X509Certificates.RSACertificateExtensions.CopyWithPrivateKey(
                                issuedServerCertificate,
                                serverKey);
                        var chromiumSpkiList = global::System.Convert.ToBase64String(
                            global::System.Security.Cryptography.SHA256.HashData(
                                serverKey.ExportSubjectPublicKeyInfo()));

                        await global::System.IO.File.WriteAllTextAsync(
                            authorityCertificatePath,
                            authorityCertificate.ExportCertificatePem(),
                            cancellationToken);
                        await global::System.IO.File.WriteAllTextAsync(
                            serverCertificatePath,
                            serverCertificate.ExportCertificatePem(),
                            cancellationToken);
                        await global::System.IO.File.WriteAllTextAsync(
                            serverPrivateKeyPath,
                            serverKey.ExportPkcs8PrivateKeyPem(),
                            cancellationToken);
                        var trustDescriptor = global::System.String.Concat(
                            "{\n",
                            "  \"profile\": \"{{tls.Identity.Value}}@{{tls.Version.Value}}\",\n",
                            "  \"authorityCertificate\": \"tls/authority-certificate.pem\",\n",
                            "  \"dotNetTrust\": \"{{tls.DotNetTrustMode}}\",\n",
                            "  \"chromiumTrust\": \"{{tls.ChromiumTrustMode}}\",\n",
                            "  \"chromiumSpkiList\": \"",
                            chromiumSpkiList,
                            "\"\n",
                            "}\n");
                        await global::System.IO.File.WriteAllTextAsync(
                            trustDescriptorPath,
                            trustDescriptor,
                            cancellationToken);
                        SetOwnedFileModes(
                            authorityCertificatePath,
                            serverCertificatePath,
                            serverPrivateKeyPath,
                            trustDescriptorPath);
                        return new ProgramKitFixtureTls(
                            ownedDirectory,
                            authorityCertificatePath,
                            serverCertificatePath,
                            serverPrivateKeyPath,
                            trustDescriptorPath,
                            chromiumSpkiList);
                    }
                    catch
                    {
                        DeleteOwnedFiles(
                            ownedDirectory,
                            authorityCertificatePath,
                            serverCertificatePath,
                            serverPrivateKeyPath,
                            trustDescriptorPath);
                        throw;
                    }
                }

                public global::System.Threading.Tasks.ValueTask DisposeAsync()
                {
                    if (global::System.Threading.Interlocked.Exchange(ref disposed, 1) == 0)
                    {
                        DeleteOwnedFiles(
                            ownedDirectory,
                            AuthorityCertificatePath,
                            ServerCertificatePath,
                            ServerPrivateKeyPath,
                            TrustDescriptorPath);
                    }

                    return global::System.Threading.Tasks.ValueTask.CompletedTask;
                }

                private static void SetOwnedFileModes(
                    string authorityCertificatePath,
                    string serverCertificatePath,
                    string serverPrivateKeyPath,
                    string trustDescriptorPath)
                {
                    if (global::System.OperatingSystem.IsWindows())
                    {
                        return;
                    }

                    var publicMode =
                        global::System.IO.UnixFileMode.UserRead |
                        global::System.IO.UnixFileMode.UserWrite;
                    global::System.IO.File.SetUnixFileMode(
                        authorityCertificatePath,
                        publicMode);
                    global::System.IO.File.SetUnixFileMode(
                        serverCertificatePath,
                        publicMode);
                    global::System.IO.File.SetUnixFileMode(
                        serverPrivateKeyPath,
                        global::System.IO.UnixFileMode.UserRead |
                        global::System.IO.UnixFileMode.UserWrite);
                    global::System.IO.File.SetUnixFileMode(
                        trustDescriptorPath,
                        publicMode);
                }

                private static void DeleteOwnedFiles(
                    string ownedDirectory,
                    params string[] paths)
                {
                    foreach (var path in paths)
                    {
                        if (global::System.IO.File.Exists(path))
                        {
                            global::System.IO.File.Delete(path);
                        }
                    }

                    if (global::System.IO.Directory.Exists(ownedDirectory) &&
                        !global::System.IO.Directory.EnumerateFileSystemEntries(
                            ownedDirectory).Any())
                    {
                        global::System.IO.Directory.Delete(ownedDirectory);
                    }
                }
            }
            """;
    }

    internal static string RenderFixtureTrustSource()
    {
        var tls = KeycloakLocalFixtureCatalog.TlsProfile;
        return $$"""
            // <auto-generated program-kit>
            #nullable enable

            internal static class ProgramKitFixtureTrust
            {
                internal static global::System.Net.Http.SocketsHttpHandler CreateHttpHandler(
                    string runtimeRoot)
                {
                    var authorityCertificatePath = OwnedPath(
                        runtimeRoot,
                        "authority-certificate.pem");
                    if (!global::System.IO.File.Exists(authorityCertificatePath))
                    {
                        throw new global::System.InvalidOperationException(
                            "The exact fixture authority certificate is unavailable.");
                    }

                    var policy =
                        new global::System.Security.Cryptography.X509Certificates.X509ChainPolicy
                        {
                            TrustMode =
                                global::System.Security.Cryptography.X509Certificates.X509ChainTrustMode.CustomRootTrust,
                            RevocationMode =
                                global::System.Security.Cryptography.X509Certificates.X509RevocationMode.NoCheck,
                            VerificationFlags =
                                global::System.Security.Cryptography.X509Certificates.X509VerificationFlags.NoFlag,
                        };
                    policy.ApplicationPolicy.Add(
                        new global::System.Security.Cryptography.Oid(
                            "{{tls.ServerExtendedKeyUsageOid}}",
                            "TLS Web Server Authentication"));
                    policy.CustomTrustStore.Add(
                        global::System.Security.Cryptography.X509Certificates.X509CertificateLoader.LoadCertificateFromFile(
                            authorityCertificatePath));
                    return new global::System.Net.Http.SocketsHttpHandler
                    {
                        SslOptions =
                            new global::System.Net.Security.SslClientAuthenticationOptions
                            {
                                CertificateChainPolicy = policy,
                            },
                    };
                }

                internal static string ReadChromiumSpkiList(string runtimeRoot)
                {
                    var descriptorPath = OwnedPath(
                        runtimeRoot,
                        "trust.runtime.json");
                    using var descriptor = global::System.Text.Json.JsonDocument.Parse(
                        global::System.IO.File.ReadAllText(descriptorPath));
                    var root = descriptor.RootElement;
                    if (!string.Equals(
                            root.GetProperty("profile").GetString(),
                            "{{tls.Identity.Value}}@{{tls.Version.Value}}",
                            global::System.StringComparison.Ordinal) ||
                        !string.Equals(
                            root.GetProperty("dotNetTrust").GetString(),
                            "{{tls.DotNetTrustMode}}",
                            global::System.StringComparison.Ordinal) ||
                        !string.Equals(
                            root.GetProperty("chromiumTrust").GetString(),
                            "{{tls.ChromiumTrustMode}}",
                            global::System.StringComparison.Ordinal))
                    {
                        throw new global::System.InvalidOperationException(
                            "The fixture trust descriptor does not match the reviewed profile.");
                    }

                    var value = root.GetProperty("chromiumSpkiList").GetString() ??
                        throw new global::System.InvalidOperationException(
                            "The fixture Chromium SPKI list is missing.");
                    if (global::System.Convert.FromBase64String(value).Length != 32)
                    {
                        throw new global::System.InvalidOperationException(
                            "The fixture Chromium SPKI list is not one SHA-256 value.");
                    }

                    return value;
                }

                private static string OwnedPath(
                    string runtimeRoot,
                    string fileName)
                {
                    global::System.ArgumentException.ThrowIfNullOrWhiteSpace(runtimeRoot);
                    var fullRoot = global::System.IO.Path.GetFullPath(runtimeRoot);
                    var leaf = new global::System.IO.DirectoryInfo(fullRoot).Name;
                    if (!leaf.StartsWith(
                            "program-kit-keycloak-",
                            global::System.StringComparison.Ordinal) ||
                        leaf.Length == "program-kit-keycloak-".Length)
                    {
                        throw new global::System.InvalidOperationException(
                            "The fixture trust root is outside the exact owned boundary.");
                    }

                    return global::System.IO.Path.Combine(
                        fullRoot,
                        "tls",
                        fileName);
                }
            }
            """;
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
        var dashboardHttp = definition.Authority.Port + 11;
        var dashboardOtlpHttp = definition.Authority.Port + 13;
        var resourceService = definition.Authority.Port + 14;
        var applicationUrls = string.Concat(
            "http://localhost:",
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
            "        \"ASPIRE_DASHBOARD_OTLP_HTTP_ENDPOINT_URL\": \"http://localhost:",
            dashboardOtlpHttp.ToString(CultureInfo.InvariantCulture),
            "\",\n",
            "        \"ASPIRE_RESOURCE_SERVICE_ENDPOINT_URL\": \"http://localhost:",
            resourceService.ToString(CultureInfo.InvariantCulture),
            "\",\n",
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
        var tls = KeycloakLocalFixtureCatalog.TlsProfile;
        var builder = new StringBuilder();
        builder.AppendLine("{");
        builder.AppendLine("  \"lockKind\": \"program-kit-keycloak-local-fixture\",");
        builder.AppendLine("  \"lockVersion\": \"2.0.0\",");
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
        builder.AppendLine("  \"tls\": {");
        JsonProperty(builder, 2, "profileIdentity", tls.Identity.Value, true);
        JsonProperty(builder, 2, "profileVersion", tls.Version.Value, true);
        JsonProperty(builder, 2, "serverHostName", tls.ServerHostName, true);
        builder.Append("    \"providerHttpsTargetPort\": ")
            .Append(tls.ProviderHttpsTargetPort.ToString(CultureInfo.InvariantCulture))
            .AppendLine(",");
        JsonProperty(
            builder,
            2,
            "certificateAlgorithm",
            tls.CertificateAlgorithm,
            true);
        builder.Append("    \"certificateAuthorityKeySize\": ")
            .Append(tls.CertificateAuthorityKeySize.ToString(
                CultureInfo.InvariantCulture))
            .AppendLine(",");
        builder.Append("    \"serverKeySize\": ")
            .Append(tls.ServerKeySize.ToString(CultureInfo.InvariantCulture))
            .AppendLine(",");
        builder.Append("    \"notBeforeSkewMinutes\": ")
            .Append(tls.NotBeforeSkewMinutes.ToString(CultureInfo.InvariantCulture))
            .AppendLine(",");
        builder.Append("    \"certificateAuthorityValidityHours\": ")
            .Append(tls.CertificateAuthorityValidityHours.ToString(
                CultureInfo.InvariantCulture))
            .AppendLine(",");
        builder.Append("    \"serverCertificateValidityHours\": ")
            .Append(tls.ServerCertificateValidityHours.ToString(
                CultureInfo.InvariantCulture))
            .AppendLine(",");
        JsonProperty(
            builder,
            2,
            "serverExtendedKeyUsageOid",
            tls.ServerExtendedKeyUsageOid,
            true);
        JsonProperty(
            builder,
            2,
            "runtimeRootEnvironmentVariable",
            tls.RuntimeRootEnvironmentVariable,
            true);
        JsonProperty(
            builder,
            2,
            "containerCertificatePath",
            tls.ContainerCertificatePath,
            true);
        JsonProperty(
            builder,
            2,
            "containerPrivateKeyPath",
            tls.ContainerPrivateKeyPath,
            true);
        JsonProperty(builder, 2, "dotNetTrustMode", tls.DotNetTrustMode, true);
        JsonProperty(
            builder,
            2,
            "chromiumTrustMode",
            tls.ChromiumTrustMode,
            true);
        builder.AppendLine("    \"providerHttpEnabled\": false,");
        builder.AppendLine(
            "    \"privateMaterial\": \"runtime-only-owned-tls-directory\",");
        builder.AppendLine(
            "    \"cleanup\": \"known-files-only-bounded-disposal\"");
        builder.AppendLine("  },");
        builder.AppendLine("  \"secretReferenceSha256\": [");
        var digests = SecretReferences(definition)
            .Select(static secret => HashTextValue(secret.Identity.Value).Value)
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
        var tls = KeycloakLocalFixtureCatalog.TlsProfile;
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
        builder.AppendLine("  \"tls\": {");
        JsonProperty(builder, 2, "profileIdentity", tls.Identity.Value, true);
        JsonProperty(builder, 2, "profileVersion", tls.Version.Value, true);
        JsonProperty(builder, 2, "serverHostName", tls.ServerHostName, true);
        builder.Append("    \"providerHttpsTargetPort\": ")
            .Append(tls.ProviderHttpsTargetPort.ToString(CultureInfo.InvariantCulture))
            .AppendLine(",");
        JsonProperty(
            builder,
            2,
            "runtimeRootEnvironmentVariable",
            tls.RuntimeRootEnvironmentVariable,
            true);
        JsonProperty(builder, 2, "dotNetTrustMode", tls.DotNetTrustMode, true);
        JsonProperty(
            builder,
            2,
            "chromiumTrustMode",
            tls.ChromiumTrustMode,
            true);
        builder.AppendLine("    \"providerHttpEnabled\": false,");
        builder.AppendLine(
            "    \"materialLifetime\": \"authorized-execution-only\",");
        builder.AppendLine(
            "    \"trustScope\": \"exact-fixture-processes-only\"");
        builder.AppendLine("  },");
        builder.AppendLine("  \"providerConclusions\": false,");
        builder.AppendLine("  \"domainAuthorizationMeaning\": false,");
        builder.AppendLine(
            "  \"runtimeTransport\": \"https-only-fixture-owned-ephemeral-authority\",");
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
            "parameters and one unique `program-kit-keycloak-*` runtime root. ",
            "At execution time the generated AppHost creates one ephemeral ",
            "authority and one localhost server certificate under the owned ",
            "`tls` directory, mounts only the server certificate and private ",
            "key read-only, and disables the provider HTTP listener. .NET ",
            "clients must use custom-root trust for the generated authority; ",
            "Chromium must use the exact generated server SPKI list. Machine ",
            "and user certificate stores and operating-system network settings ",
            "must not be changed. The profile must retain only ",
            "redacted outcome evidence, and remove its owned state.\n");

    private static void SecretParameter(
        StringBuilder builder,
        string indentation,
        string variable,
        string name) =>
        builder.Append(indentation)
            .Append("var ")
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

    internal static Sha256Digest HashTextValue(string value) =>
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
