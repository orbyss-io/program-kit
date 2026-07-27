using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Schemas;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Generation.Keycloak;
using Orbyss.ProgramKit.DotNet.Schemas;
using Orbyss.ProgramKit.Operations.Contracts.Schemas;
using Orbyss.ProgramKit.Serialization.Json.Canonicalization;
using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.SecretResolution.Contracts.Schemas;
using Orbyss.ProgramKit.Workbench.Operations.Schemas;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Generation.Keycloak;

[TestClass]
public sealed class KeycloakLocalFixtureGeneratorTests
{
    [TestMethod]
    public void SameInputProducesIdenticalBytesAndTreeDigest()
    {
        KeycloakLocalFixtureGenerator generator = new();

        var first = generator.Generate(Definition());
        var second = generator.Generate(Definition());

        Assert.AreEqual(first.OutputTreeSha256, second.OutputTreeSha256);
        Assert.AreSequenceEqual(
            first.Outputs.Select(static output => output.RelativePath).ToArray(),
            second.Outputs.Select(static output => output.RelativePath).ToArray());
        for (var index = 0; index < first.Outputs.Length; index++)
        {
            Assert.AreSequenceEqual(
                first.Outputs[index].Content.ToArray(),
                second.Outputs[index].Content.ToArray());
        }
    }

    [TestMethod]
    public void ChangedCallbackChangesOutputDigest()
    {
        KeycloakLocalFixtureGenerator generator = new();
        var changed = Definition() with
        {
            ConfidentialRedirectUri =
                new Uri("https://localhost:5444/signin-oidc"),
        };

        Assert.AreNotEqual(
            generator.Generate(Definition()).OutputTreeSha256,
            generator.Generate(changed).OutputTreeSha256);
    }

    [TestMethod]
    public void RealmIsMinimalSecretFreeAndProtocolExact()
    {
        KeycloakLocalFixtureGenerator generator = new();
        var result = generator.Generate(Definition());
        var realm = Text(result, "KeycloakFixture/Realm/program-kit-realm.json");
        using var document = JsonDocument.Parse(realm);

        Assert.AreEqual(
            "program-kit",
            document.RootElement.GetProperty("realm").GetString());
        var clients = document.RootElement.GetProperty("clients")
            .EnumerateArray()
            .ToArray();
        Assert.HasCount(5, clients);
        Assert.IsTrue(clients.Single(client =>
            client.GetProperty("clientId").GetString() == "program-kit-api")
            .GetProperty("bearerOnly")
            .GetBoolean());
        Assert.IsTrue(clients.Single(client =>
            client.GetProperty("clientId").GetString() == "program-kit-public")
            .GetProperty("publicClient")
            .GetBoolean());
        Assert.AreEqual(
            "S256",
            clients.Single(client =>
                    client.GetProperty("clientId").GetString() ==
                    "program-kit-public")
                .GetProperty("attributes")
                .GetProperty("pkce.code.challenge.method")
                .GetString());
        Assert.AreEqual(
            "https://localhost:8443/signout-callback-oidc##",
            clients.Single(client =>
                    client.GetProperty("clientId").GetString() ==
                    "program-kit-confidential")
                .GetProperty("attributes")
                .GetProperty("post.logout.redirect.uris")
                .GetString());
        Assert.AreEqual(
            "true",
            clients.Single(client =>
                    client.GetProperty("clientId").GetString() ==
                    "program-kit-exchange")
                .GetProperty("attributes")
                .GetProperty("standard.token.exchange.enabled")
                .GetString());
        Assert.Contains("\"access.token.header.type.rfc9068\": \"true\"", realm);
        Assert.Contains("${PROGRAM_KIT_CONFIDENTIAL_CLIENT_SECRET}", realm);
        Assert.Contains("${PROGRAM_KIT_TEST_PRINCIPAL_PASSWORD}", realm);
        Assert.DoesNotContain("adminPassword", realm);
        Assert.DoesNotContain("\"roles\"", realm);
        Assert.DoesNotContain("\"groups\"", realm);
    }

    [TestMethod]
    public void SecretReferenceIdentitiesAreHashedAndNeverRendered()
    {
        KeycloakLocalFixtureGenerator generator = new();
        var result = generator.Generate(Definition());
        var allText = string.Join(
            Environment.NewLine,
            result.Outputs.Select(output =>
                Encoding.UTF8.GetString(output.Content.Span)));

        Assert.DoesNotContain("pkid:secret-reference:fixture:", allText);
        Assert.Contains("\"secretReferenceSha256\": [", allText);
        Assert.Contains("secret: true", allText);
        Assert.DoesNotContain("fixture-secret-value", allText);
    }

    [TestMethod]
    public void GeneratedSecurityTopologyUsesEveryOrdinaryProjection()
    {
        KeycloakLocalFixtureGenerator generator = new();
        var result = generator.Generate(Definition());
        var host = Text(
            result,
            "KeycloakFixture/GeneratedConsumers/SecurityHost/Program.cs");
        var catalog = Text(
            result,
            "KeycloakFixture/GeneratedConsumers/SecurityHost/ProgramKitGenerated/Hosting/ProgramKitOAuthProfileCatalog.cs");
        var browser = Text(
            result,
            "KeycloakFixture/GeneratedConsumers/PublicBrowser/Program.cs");
        var evidence = Text(
            result,
            "KeycloakFixture/GeneratedConsumers/generated-security-profiles.json");
        var project = Text(
            result,
            "KeycloakFixture/GeneratedConsumers/SecurityHost/SecurityHost.csproj");

        Assert.Contains("AddOpenIdConnect", host);
        Assert.Contains("AddJwtBearer", host);
        Assert.Contains("ProgramKitOAuthTokenEndpointClient", host);
        Assert.Contains("keycloak-service", catalog);
        Assert.Contains("keycloak-exchange-subject", catalog);
        Assert.Contains("keycloak-token-exchange", catalog);
        Assert.Contains("AddOidcAuthentication", browser);
        Assert.Contains("ResponseType = \"code\"", browser);
        Assert.Contains("\"rfc8693-token-exchange\"", evidence);
        Assert.Contains("\"directProtocolReplacementAllowed\": false", evidence);
        Assert.DoesNotContain("Orbyss.ProgramKit", project);
        Assert.IsTrue(result.Outputs.Any(static output =>
            output.RelativePath ==
            "KeycloakFixture/GeneratedConsumers/PublicBrowser/Pages/FixtureProtectedApiProbe.razor"));
    }

    [TestMethod]
    public void AppHostPinsImageIntegrationAndDisposableState()
    {
        KeycloakLocalFixtureGenerator generator = new();
        var result = generator.Generate(Definition());
        var project = Text(result, "KeycloakFixture/AppHost/AppHost.csproj");
        var program = Text(result, "KeycloakFixture/AppHost/Program.cs");
        var tls = Text(
            result,
            "KeycloakFixture/AppHost/ProgramKitFixtureTls.cs");
        var lockText = Text(
            result,
            "KeycloakFixture/keycloak-fixture.lock.json");
        var launchSettings = Text(
            result,
            "KeycloakFixture/AppHost/Properties/launchSettings.json");

        Assert.Contains(
            "Aspire.Hosting.Keycloak\" Version=\"[13.4.6-preview.1.26319.6]\"",
            project);
        Assert.Contains(
            ".WithImageSHA256(\"0f198be292568439d700cdbfb893e69a6009bb43a94a06a945b1d3d506c76b13\")",
            program);
        Assert.Contains(".WithRealmImport(\"../Realm\")", program);
        Assert.Contains(".WithEndpoint(\"http\", endpoint =>", program);
        Assert.Contains("endpoint.UriScheme = \"https\";", program);
        Assert.Contains("endpoint.TargetPort = 8443;", program);
        Assert.Contains("KC_HTTP_ENABLED", program);
        Assert.Contains("\"false\"", program);
        Assert.Contains("KC_HTTPS_CERTIFICATE_FILE", program);
        Assert.Contains("KC_HTTPS_CERTIFICATE_KEY_FILE", program);
        Assert.Contains(
            ".WithBindMount(fixtureTls.ServerCertificatePath",
            program);
        Assert.Contains(
            ".WithBindMount(fixtureTls.ServerPrivateKeyPath",
            program);
        Assert.Contains(
            ".WithHttpEndpoint(port: 5444, targetPort: 9000, name: \"management\")",
            program);
        Assert.Contains(".WithEndpointProxySupport(false)", program);
        Assert.Contains("ContainerLifetime.Session", program);
        Assert.DoesNotContain("UseEphemeralDataProtectionProvider", program);
        Assert.DoesNotContain(string.Concat("WithData", "Volume"), program);
        Assert.DoesNotContain(
            string.Concat("ASPIRE_DCP_USE_", "DEVELOPER_CERTIFICATE"),
            launchSettings);
        Assert.Contains(
            "\"ASPIRE_VERSION_CHECK_DISABLED\": \"true\"",
            launchSettings);
        Assert.Contains(
            "\"ASPIRE_DASHBOARD_TELEMETRY_OPTOUT\": \"true\"",
            launchSettings);
        Assert.Contains(
            "\"ASPIRE_RESOURCE_SERVICE_ENDPOINT_URL\": \"http://localhost:5457\"",
            launchSettings);
        Assert.Contains(
            "X509BasicConstraintsExtension(",
            tls);
        Assert.Contains(
            "X509EnhancedKeyUsageExtension(",
            tls);
        Assert.Contains(
            "SubjectAlternativeNameBuilder",
            tls);
        Assert.Contains(
            "serverKey.ExportSubjectPublicKeyInfo()",
            tls);
        Assert.Contains("chromiumSpkiList", tls);
        Assert.Contains("File.SetUnixFileMode(", tls);
        Assert.DoesNotContain(string.Concat("X509", "Store"), tls);
        Assert.DoesNotContain(string.Concat("Ignore", "HTTPSErrors"), tls);
        Assert.DoesNotContain(string.Concat("Dangerous", "AcceptAny"), tls);
        Assert.DoesNotContain(string.Concat("net", "sh"), tls);
        Assert.Contains("\"lockVersion\": \"2.0.0\"", lockText);
        Assert.Contains("\"providerHttpEnabled\": false", lockText);
        Assert.Contains("\"dotNetTrustMode\": \"dotnet-custom-root-trust\"", lockText);
        Assert.Contains(
            "\"chromiumTrustMode\": \"chromium-server-spki-list\"",
            lockText);
        Assert.Contains("\"executionAuthorized\": false", lockText);
        Assert.Contains("\"productionProvisioning\": false", lockText);
        Assert.Contains("\"persistentState\": false", lockText);
    }

    [TestMethod]
    public void GeneratedRealmAndProfilePassBoundedSchemasAndMutationsFail()
    {
        KeycloakLocalFixtureGenerator generator = new();
        var result = generator.Generate(Definition());
        var realm = result.Outputs.Single(output =>
            output.RelativePath ==
            "KeycloakFixture/Realm/program-kit-realm.json").Content.ToArray();
        var profile = result.Outputs.Single(output =>
            output.RelativePath ==
            "KeycloakFixture/keycloak-fixture.profile.json").Content.ToArray();
        DotNetSchemaModule module = new(
            new OperationsSchemaModule(),
            new SecretResolutionSchemaModule());
        var schema = module.Resources.Single(resource =>
            resource.SchemaReference.Identity.Name ==
            "dotnet-keycloak-local-realm-import");
        var profileSchema = module.Resources.Single(resource =>
            resource.SchemaReference.Identity.Name ==
            "dotnet-keycloak-local-fixture-profile");
        ProgramKitJsonCanonicalizer canonicalizer = new();
        JsonSchemaWorkbenchValidator validator = new(
            canonicalizer,
            new ProgramKitSchemaModuleValidator());
        var limits = DotNetJsonProfiles.ShellBootstrap.MaximumLimits;

        var valid = validator.Validate(
            realm,
            module,
            schema.SchemaReference,
            limits);
        var disclosed = Encoding.UTF8.GetBytes(
            Encoding.UTF8.GetString(realm)
                .Replace(
                    "${PROGRAM_KIT_TEST_PRINCIPAL_PASSWORD}",
                    "fixture-secret-value",
                    StringComparison.Ordinal));
        var invalid = validator.Validate(
            disclosed,
            module,
            schema.SchemaReference,
            limits);
        var validProfile = validator.Validate(
            profile,
            module,
            profileSchema.SchemaReference,
            limits);
        var httpProfile = Encoding.UTF8.GetBytes(
            Encoding.UTF8.GetString(profile)
                .Replace(
                    "https://localhost:5443",
                    "http://localhost:5443",
                    StringComparison.Ordinal));
        var invalidProfile = validator.Validate(
            httpProfile,
            module,
            profileSchema.SchemaReference,
            limits);

        Assert.IsTrue(
            valid.IsValid,
            string.Join(
                Environment.NewLine,
                valid.Diagnostics.Select(static diagnostic => diagnostic.Message)));
        Assert.IsFalse(invalid.IsValid);
        Assert.IsTrue(
            validProfile.IsValid,
            string.Join(
                Environment.NewLine,
                validProfile.Diagnostics.Select(
                    static diagnostic => diagnostic.Message)));
        Assert.IsFalse(invalidProfile.IsValid);
    }

    [TestMethod]
    public void HttpAuthorityFailsWithStableDiagnostic()
    {
        var invalid = Definition() with
        {
            Authority = new Uri("http://localhost:5443/realms/program-kit"),
        };

        KeycloakLocalFixtureGenerator generator = new();
        var exception = Assert.ThrowsExactly<DotNetKitException>(
            () => generator.Generate(invalid));

        Assert.AreEqual(
            DotNetDiagnosticIds.UnsupportedKeycloakFixtureProfile,
            exception.DiagnosticId);
    }

    [TestMethod]
    public void AlternateLoopbackHostnameFailsExactTlsProfile()
    {
        var invalid = Definition() with
        {
            Authority = new Uri(
                "https://127.0.0.1:5443/realms/program-kit"),
            MetadataAddress = new Uri(
                "https://127.0.0.1:5443/realms/program-kit/.well-known/openid-configuration"),
        };

        KeycloakLocalFixtureGenerator generator = new();
        var exception = Assert.ThrowsExactly<DotNetKitException>(
            () => generator.Generate(invalid));

        Assert.AreEqual(
            DotNetDiagnosticIds.UnsupportedKeycloakFixtureProfile,
            exception.DiagnosticId);
    }

    [TestMethod]
    public void NonConfigurationSecretFailsWithStableDiagnostic()
    {
        var definition = Definition();
        var invalid = definition with
        {
            Secrets = definition.Secrets with
            {
                AdminPassword = definition.Secrets.AdminPassword with
                {
                    ExpectedResultKind = SecretResultKind.Certificate,
                },
            },
        };

        KeycloakLocalFixtureGenerator generator = new();
        var exception = Assert.ThrowsExactly<DotNetKitException>(
            () => generator.Generate(invalid));

        Assert.AreEqual(
            DotNetDiagnosticIds.UnsafeKeycloakFixtureMaterial,
            exception.DiagnosticId);
    }

    internal static KeycloakLocalFixtureDefinition Definition() =>
        new(
            new ProgramKitIdentifier("pkid:fixture:program-kit:keycloak-local"),
            new SemanticVersion("1.0.0"),
            "program-kit",
            new Uri("https://localhost:5443/realms/program-kit"),
            new Uri(
                "https://localhost:5443/realms/program-kit/.well-known/openid-configuration"),
            "program-kit-api",
            "program-kit.api",
            "program-kit-public",
            new Uri("https://localhost:7443/authentication/login-callback"),
            new Uri("https://localhost:7443/authentication/logout-callback"),
            new Uri("https://localhost:7443/"),
            "program-kit-confidential",
            new Uri("https://localhost:8443/signin-oidc"),
            "program-kit-service",
            "program-kit-exchange",
            "fixture-principal",
            new KeycloakLocalFixtureSecretReferences(
                Secret("admin-password"),
                Secret("principal-password"),
                Secret("confidential-client-secret"),
                Secret("service-client-secret"),
                Secret("exchange-client-secret")));

    private static SecretReferenceDescriptor Secret(string name) =>
        new(
            new ProgramKitIdentifier(
                string.Concat("pkid:secret-reference:fixture:", name)),
            SecretReferenceClassification.RestrictedMetadata,
            SecretResultKind.ConfigurationText,
            Reference("pkid:capability:fixture:secret-resolver"),
            Reference(string.Concat("pkid:locator:fixture:", name)),
            SecretReferenceClassification.SensitiveMetadata);

    private static ArtifactReference Reference(string identity) =>
        new(
            new ProgramKitIdentifier(identity),
            new SemanticVersion("1.0.0"),
            new Sha256Digest(
                string.Concat("sha256:", new string('b', 64))));

    private static string Text(
        KeycloakLocalFixtureGenerationResult result,
        string path) =>
        Encoding.UTF8.GetString(
            result.Outputs.Single(output => output.RelativePath == path).Content.Span);
}
