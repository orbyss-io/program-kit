using System.Text;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.DotNet.Composition;
using Orbyss.ProgramKit.DotNet.Operations.Security;
using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation.Keycloak;

/// <summary>
/// Composes the ordinary Program Kit security compiler into the disposable
/// Keycloak fixture. Provider-specific code supplies only fixture hosting,
/// exact trust, and consumer adapters.
/// </summary>
internal static class KeycloakGeneratedSecurityConsumerGenerator
{
    private const string HostRoot =
        "KeycloakFixture/GeneratedConsumers/SecurityHost/";
    private const string ConsumerRoot =
        "KeycloakFixture/GeneratedConsumers/";
    private const string JwtScheme = "ProgramKit.Jwt";
    private const string OidcScheme = "ProgramKit.Oidc";
    private const string CookieScheme = "ProgramKit.Cookie";
    private const string PolicyName = "ProgramKit.AuthenticatedTransport";
    private const string ServiceClientName = "keycloak-service";
    private const string RolloverServiceClientName =
        "keycloak-service-after-rollover";
    private const string ExchangeSubjectClientName =
        "keycloak-exchange-subject";
    private const string ExchangeClientName = "keycloak-token-exchange";

    internal static ImmutableArray<GeneratedOutput> Generate(
        KeycloakLocalFixtureDefinition definition)
    {
        var security = Security(definition);
        var compiler = DotNetSecurityProjectionComposition.Create();
        var outputs = ImmutableArray.CreateBuilder<GeneratedOutput>();
        foreach (var output in compiler.Compile(security))
        {
            var root = output.RelativePath.StartsWith(
                "PublicBrowser",
                StringComparison.Ordinal)
                ? ConsumerRoot
                : HostRoot;
            outputs.Add(new GeneratedOutput(
                string.Concat(root, output.RelativePath),
                output.Content));
        }

        outputs.Add(Output(
            string.Concat(HostRoot, "SecurityHost.csproj"),
            RenderHostProject()));
        outputs.Add(Output(
            string.Concat(HostRoot, "Program.cs"),
            RenderHostProgram(
                compiler.RenderRegistration(security),
                compiler.RenderMiddleware(security))));
        outputs.Add(Output(
            string.Concat(HostRoot, "FixtureSecurityAdapters.cs"),
            RenderHostAdapters(definition)));
        outputs.Add(Output(
            string.Concat(HostRoot, "ProgramKitFixtureTrust.cs"),
            KeycloakLocalFixtureGenerator.RenderFixtureTrustSource()));
        outputs.Add(Output(
            string.Concat(
                ConsumerRoot,
                "PublicBrowser/Pages/FixtureProtectedApiProbe.razor"),
            RenderPublicBrowserProbe()));
        outputs.Add(Output(
            string.Concat(ConsumerRoot, "generated-security-profiles.json"),
            RenderEvidence()));
        return outputs.ToImmutable();
    }

    private static DotNetSecurityConfiguration Security(
        KeycloakLocalFixtureDefinition definition)
    {
        var policy = Reference("policy", "authenticated-transport");
        var tokenEndpoint = new Uri(
            string.Concat(
                definition.Authority.AbsoluteUri.TrimEnd('/'),
                "/protocol/openid-connect/token"));
        var resource = new Uri(
            definition.ConfidentialRedirectUri.GetLeftPart(
                UriPartial.Authority));
        var oidcSecret = new DotNetOidcClientAuthentication(
            DotNetOidcClientAuthenticationMethod.ClientSecretPost,
            definition.Secrets.ConfidentialClientSecret,
            "Authentication:Oidc:ClientSecret");
        var serviceAuthentication = OAuthAuthentication(
            FixtureSecret(
                definition.Secrets.ServiceClientSecret,
                "keycloak-service-client"));
        var exchangeAuthentication = OAuthAuthentication(
            FixtureSecret(
                definition.Secrets.TokenExchangeClientSecret,
                "keycloak-token-exchange-client"));
        var subjectSource = new DotNetOAuthTokenSource(
            new ProgramKitIdentifier(
                "pkid:token-source:program-kit:keycloak-exchange-subject"),
            Reference("provenance", "generated-exchange-subject"),
            DotNetOAuthTokenType.AccessToken);
        return new DotNetSecurityConfiguration(
            Reference("profile", "keycloak-generated-security"),
            new DotNetAuthenticationDefaults(
                JwtScheme,
                OidcScheme,
                JwtScheme,
                CookieScheme,
                OidcScheme),
            new DotNetOidcConfidentialInteractiveProfile(
                Reference("profile", "keycloak-confidential-code-pkce"),
                OidcScheme,
                CookieScheme,
                definition.Authority,
                definition.MetadataAddress,
                definition.ConfidentialClientId,
                oidcSecret,
                definition.ConfidentialRedirectUri.AbsolutePath,
                "/signout-callback-oidc",
                "/signout-oidc",
                ["openid", "profile", definition.ApiScope],
                ["RS256"],
                DotNetOidcPushedAuthorizationBehavior.UseIfAvailable,
                DotNetTransportClaimMapping.PreserveProviderClaimNames,
                Cookie("__Host-program-kit-session", DotNetCookieSameSite.Lax, 60),
                Cookie(
                    "__Host-program-kit-correlation",
                    DotNetCookieSameSite.None,
                    15),
                Cookie("__Host-program-kit-nonce", DotNetCookieSameSite.None, 15),
                300,
                true,
                true,
                true,
                true,
                false,
                false),
            new DotNetOidcPublicBrowserProfile(
                Reference("profile", "keycloak-public-browser-code-pkce"),
                DotNetPublicBrowserTargetAdapterCatalog.BlazorWebAssemblyOidc,
                definition.Authority,
                definition.MetadataAddress,
                definition.PublicClientId,
                definition.PublicRedirectUri,
                definition.PublicPostLogoutRedirectUri,
                definition.PublicBrowserOrigin,
                resource,
                "ProgramKit.PublicBrowser",
                [definition.PublicBrowserOrigin],
                ["GET"],
                ["openid", "profile", definition.ApiScope],
                DotNetPublicBrowserTokenStorage.BrowserSession,
                DotNetPublicBrowserRefreshDisposition.Absent,
                Reference("acceptance", "keycloak-public-browser-threat-model"),
                true,
                true,
                true,
                true,
                true,
                true,
                true,
                true,
                new DotNetPublicBrowserVerification(
                    Reference("profile", "keycloak-public-browser-verification"),
                    DotNetPublicBrowserTargetAdapterCatalog.Playwright,
                    [DotNetBrowserEngine.Chromium],
                    true,
                    false,
                    false,
                    false,
                    false,
                    true)),
            new DotNetJwtResourceServerProfile(
                Reference("profile", "keycloak-rfc9068-resource-server"),
                JwtScheme,
                definition.Authority,
                definition.MetadataAddress,
                definition.Authority.AbsoluteUri.TrimEnd('/'),
                definition.ApiAudience,
                ["RS256"],
                DotNetJwtAccessTokenProfile.Rfc9068AtJwt,
                DotNetTransportClaimMapping.PreserveProviderClaimNames,
                30,
                true,
                false),
            [
                ClientCredentials(
                    "service",
                    ServiceClientName,
                    tokenEndpoint,
                    definition.ServiceClientId,
                    serviceAuthentication,
                    resource,
                    definition),
                ClientCredentials(
                    "exchange-subject",
                    ExchangeSubjectClientName,
                    tokenEndpoint,
                    definition.TokenExchangeClientId,
                    exchangeAuthentication,
                    resource,
                    definition),
                ClientCredentials(
                    "service-after-rollover",
                    RolloverServiceClientName,
                    tokenEndpoint,
                    definition.ServiceClientId,
                    serviceAuthentication,
                    resource,
                    definition),
            ],
            [
                new DotNetOAuthTokenExchangeProfile(
                    Reference("profile", "keycloak-rfc8693-token-exchange"),
                    ExchangeClientName,
                    definition.MetadataAddress,
                    tokenEndpoint,
                    definition.TokenExchangeClientId,
                    exchangeAuthentication,
                    subjectSource,
                    null,
                    DotNetOAuthExchangeMode.Impersonation,
                    DotNetOAuthTokenType.AccessToken,
                    DotNetOAuthTokenType.AccessToken,
                    resource,
                    definition.ApiAudience,
                    [definition.ApiScope],
                    300,
                    30,
                    new DotNetOAuthCachePolicy(true, 30, 300),
                    true,
                    true,
                    true,
                    false,
                    false),
            ],
            [
                new DotNetNamedHostPolicyReference(
                    policy,
                    PolicyName,
                    [JwtScheme],
                    DotNetPolicyRegistrationOwnership
                        .ProgramKitAuthenticatedTransport),
            ],
            [
                new DotNetOperationSecurityBinding(
                    Reference("operation", "keycloak-protected-probe"),
                    "GET",
                    "/protected",
                    DotNetOperationSecurityDisposition.NamedPolicy,
                    policy.Identity),
            ]);
    }

    private static DotNetOAuthClientCredentialsProfile ClientCredentials(
        string profileName,
        string clientName,
        Uri tokenEndpoint,
        string clientId,
        DotNetOAuthClientAuthentication authentication,
        Uri resource,
        KeycloakLocalFixtureDefinition definition) =>
        new(
            Reference("profile", string.Concat("keycloak-", profileName)),
            clientName,
            definition.MetadataAddress,
            tokenEndpoint,
            clientId,
            authentication,
            resource,
            definition.ApiAudience,
            [definition.ApiScope],
            DotNetOAuthTokenType.AccessToken,
            300,
            30,
            new DotNetOAuthCachePolicy(true, 30, 300),
            true,
            true,
            true,
            false,
            false);

    private static DotNetOAuthClientAuthentication OAuthAuthentication(
        SecretReferenceDescriptor reference) =>
        new(
            DotNetOAuthClientAuthenticationMethod.ClientSecretBasic,
            reference,
            null);

    private static SecretReferenceDescriptor FixtureSecret(
        SecretReferenceDescriptor source,
        string name) =>
        source with
        {
            Identity = new ProgramKitIdentifier(
                string.Concat(
                    "pkid:secret-reference:program-kit:",
                    name)),
        };

    private static DotNetCookieSecurityProfile Cookie(
        string name,
        DotNetCookieSameSite sameSite,
        int lifetimeMinutes) =>
        new(name, sameSite, true, true, false, lifetimeMinutes);

    private static ArtifactReference Reference(string kind, string name)
    {
        var identity = new ProgramKitIdentifier(
            string.Concat("pkid:", kind, ":program-kit:", name));
        return new ArtifactReference(
            identity,
            new SemanticVersion("1.0.0"),
            KeycloakLocalFixtureGenerator.HashTextValue(identity.Value));
    }

    private static string RenderHostProject() =>
        """
        <Project Sdk="Microsoft.NET.Sdk.Web">
          <PropertyGroup>
            <TargetFramework>net10.0</TargetFramework>
            <LangVersion>14.0</LangVersion>
            <Nullable>enable</Nullable>
            <ImplicitUsings>enable</ImplicitUsings>
            <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
            <RootNamespace>GeneratedHost</RootNamespace>
          </PropertyGroup>
          <ItemGroup>
            <PackageReference Include="Microsoft.AspNetCore.Authentication.JwtBearer" Version="[10.0.10]" />
            <PackageReference Include="Microsoft.AspNetCore.Authentication.OpenIdConnect" Version="[10.0.10]" />
          </ItemGroup>
        </Project>
        """;

    private static string RenderHostProgram(
        string registration,
        string middleware) =>
        string.Concat(
            """
            // <auto-generated program-kit>
            using GeneratedHost.Hosting;
            using Microsoft.AspNetCore.Authentication;
            using Microsoft.AspNetCore.Authentication.JwtBearer;
            using Microsoft.AspNetCore.Authentication.OpenIdConnect;

            var builder = WebApplication.CreateBuilder(args);
            """,
            registration,
            """
            builder.Services.AddSingleton<FixtureOAuthMaterial>();
            builder.Services.AddSingleton<IProgramKitOAuthClientCredentialProvider>(
                static provider => provider.GetRequiredService<FixtureOAuthMaterial>());
            builder.Services.AddSingleton<IProgramKitOAuthTokenSource>(
                static provider => provider.GetRequiredService<FixtureOAuthMaterial>());
            builder.Services.AddSingleton<IProgramKitOAuthClientAssertionProvider,
                RejectingFixtureAssertionProvider>();
            var runtimeRoot = Environment.GetEnvironmentVariable(
                "PROGRAM_KIT_KEYCLOAK_RUNTIME_ROOT")
                ?? throw new InvalidOperationException("The owned fixture runtime root is unavailable.");
            builder.Services.PostConfigure<OpenIdConnectOptions>("ProgramKit.Oidc", options =>
                options.BackchannelHttpHandler =
                    ProgramKitFixtureTrust.CreateHttpHandler(runtimeRoot));
            builder.Services.PostConfigure<JwtBearerOptions>("ProgramKit.Jwt", options =>
                options.BackchannelHttpHandler =
                    ProgramKitFixtureTrust.CreateHttpHandler(runtimeRoot));
            foreach (var clientName in new[]
                     {
                         "keycloak-service",
                         "keycloak-service-after-rollover",
                         "keycloak-exchange-subject",
                         "keycloak-token-exchange",
                     })
            {
                builder.Services.AddHttpClient(
                        string.Concat("ProgramKit.OAuth.", clientName))
                    .ConfigurePrimaryHttpMessageHandler(
                        () => ProgramKitFixtureTrust.CreateHttpHandler(runtimeRoot));
            }

            var app = builder.Build();
            """,
            middleware,
            """
            app.MapGet("/", () => Results.Ok(new { profile = "generated-security-host" }));
            app.MapGet("/protected", () => Results.Ok(new { outcome = "accepted" }));
            app.MapGet("/confidential/login", () =>
                Results.Challenge(
                    new AuthenticationProperties { RedirectUri = "/confidential/session" },
                    ["ProgramKit.Oidc"]));
            app.MapGet("/confidential/session", (HttpContext context) =>
                Results.Ok(new
                {
                    authenticated = context.User.Identity?.IsAuthenticated == true,
                })).RequireAuthorization(
                    new Microsoft.AspNetCore.Authorization.AuthorizeAttribute
                    {
                        AuthenticationSchemes = "ProgramKit.Cookie",
                    });
            app.MapGet("/confidential/logout", () =>
                Results.SignOut(
                    new AuthenticationProperties { RedirectUri = "/" },
                    ["ProgramKit.Oidc", "ProgramKit.Cookie"]));
            app.MapPost("/oauth/client-credentials", async (
                ProgramKitOAuthTokenEndpointClient tokens,
                CancellationToken cancellationToken) =>
            {
                _ = await tokens.GetAsync("keycloak-service", cancellationToken);
                return Results.Ok(new { outcome = "accepted" });
            });
            app.MapPost("/oauth/token-exchange", async (
                ProgramKitOAuthTokenEndpointClient tokens,
                FixtureOAuthMaterial material,
                CancellationToken cancellationToken) =>
            {
                var subject = await tokens.GetAsync(
                    "keycloak-exchange-subject",
                    cancellationToken);
                material.SetSubject(subject);
                try
                {
                    _ = await tokens.GetAsync(
                        "keycloak-token-exchange",
                        cancellationToken);
                }
                finally
                {
                    material.ClearSubject();
                }
                return Results.Ok(new { outcome = "accepted" });
            });
            app.MapPost("/oauth/protected-roundtrip", async (
                ProgramKitOAuthTokenEndpointClient tokens,
                CancellationToken cancellationToken) =>
            {
                var token = await tokens.GetAsync(
                    "keycloak-service",
                    cancellationToken);
                using var handler =
                    ProgramKitFixtureTrust.CreateHttpHandler(runtimeRoot);
                using var client = new HttpClient(handler);
                using var request = new HttpRequestMessage(
                    HttpMethod.Get,
                    "https://localhost:8443/protected");
                request.Headers.Authorization =
                    new System.Net.Http.Headers.AuthenticationHeaderValue(
                        "Bearer",
                        token.Value);
                using var response = await client.SendAsync(
                    request,
                    cancellationToken);
                return response.IsSuccessStatusCode
                    ? Results.Ok(new { outcome = "accepted" })
                    : Results.StatusCode((int)response.StatusCode);
            });
            app.MapPost("/oauth/protected-roundtrip-after-rollover", async (
                ProgramKitOAuthTokenEndpointClient tokens,
                CancellationToken cancellationToken) =>
            {
                var token = await tokens.GetAsync(
                    "keycloak-service-after-rollover",
                    cancellationToken);
                using var handler =
                    ProgramKitFixtureTrust.CreateHttpHandler(runtimeRoot);
                using var client = new HttpClient(handler);
                using var request = new HttpRequestMessage(
                    HttpMethod.Get,
                    "https://localhost:8443/protected");
                request.Headers.Authorization =
                    new System.Net.Http.Headers.AuthenticationHeaderValue(
                        "Bearer",
                        token.Value);
                using var response = await client.SendAsync(
                    request,
                    cancellationToken);
                return response.IsSuccessStatusCode
                    ? Results.Ok(new { outcome = "accepted" })
                    : Results.StatusCode((int)response.StatusCode);
            });
            app.Run();
            """);

    private static string RenderHostAdapters(
        KeycloakLocalFixtureDefinition definition) =>
        string.Concat(
            """
            // <auto-generated program-kit>
            #nullable enable

            namespace GeneratedHost.Hosting;

            internal sealed class FixtureOAuthMaterial :
                IProgramKitOAuthClientCredentialProvider,
                IProgramKitOAuthTokenSource
            {
                private readonly AsyncLocal<ProgramKitOAuthAccessToken?> subject =
                    new();

                public ValueTask<string> GetAsync(
                    string referenceIdentity,
                    CancellationToken cancellationToken)
                {
                    cancellationToken.ThrowIfCancellationRequested();
                    var environmentName = referenceIdentity switch
                    {
            """,
            "            ",
            DotNetSourceText.CSharpLiteral(
                "pkid:secret-reference:program-kit:keycloak-service-client"),
            " => \"PROGRAM_KIT_SERVICE_CLIENT_SECRET\",\n",
            "            ",
            DotNetSourceText.CSharpLiteral(
                "pkid:secret-reference:program-kit:keycloak-token-exchange-client"),
            " => \"PROGRAM_KIT_TOKEN_EXCHANGE_CLIENT_SECRET\",\n",
            """
                        _ => throw new InvalidOperationException(
                            "The generated OAuth credential reference is not bound."),
                    };
                    return ValueTask.FromResult(
                        Environment.GetEnvironmentVariable(environmentName)
                        ?? throw new InvalidOperationException(
                            "The generated OAuth credential did not resolve."));
                }

                ValueTask<ProgramKitOAuthTokenSourceValue>
                    IProgramKitOAuthTokenSource.GetAsync(
                        string sourceIdentity,
                        CancellationToken cancellationToken)
                {
                    cancellationToken.ThrowIfCancellationRequested();
                    var value = subject.Value ??
                        throw new InvalidOperationException(
                            "The explicit generated exchange subject is unavailable.");
                    return ValueTask.FromResult(new ProgramKitOAuthTokenSourceValue(
                        value.Value,
                        value.TokenKind,
                        "pkid:provenance:program-kit:generated-exchange-subject"));
                }

                internal void SetSubject(ProgramKitOAuthAccessToken value) =>
                    subject.Value = value;

                internal void ClearSubject() => subject.Value = null;
            }

            internal sealed class RejectingFixtureAssertionProvider :
                IProgramKitOAuthClientAssertionProvider
            {
                public ValueTask<string> CreateAsync(
                    string referenceIdentity,
                    Uri tokenEndpoint,
                    CancellationToken cancellationToken) =>
                    throw new NotSupportedException(
                        "The exact fixture profiles do not select private_key_jwt.");
            }
            """);

    private static string RenderPublicBrowserProbe() =>
        """
        @* <auto-generated program-kit fixture composition> *@
        @page "/fixture/protected-api"
        @using Microsoft.AspNetCore.Authorization
        @attribute [Authorize]
        @inject HttpClient Client

        <button id="call-protected-api" @onclick="CallAsync">Call protected API</button>
        <output id="protected-api-outcome">@outcome</output>

        @code {
            private string outcome = "not-run";

            private async Task CallAsync()
            {
                using var response = await Client.GetAsync("protected");
                outcome = response.IsSuccessStatusCode ? "accepted" : "rejected";
            }
        }
        """;

    private static string RenderEvidence() =>
        """
        {
          "profileVersion": "1.0.0",
          "compiler": "Orbyss.ProgramKit.DotNet.Generation.DotNetSecurityProjectionCompiler",
          "roles": [
            "oidc-confidential-code-pkce",
            "oidc-public-browser-code-pkce",
            "rfc9068-jwt-resource-server",
            "oauth-client-credentials",
            "rfc8693-token-exchange"
          ],
          "directProtocolReplacementAllowed": false,
          "programKitRuntimeDependency": false,
          "executionAuthorized": false
        }
        """;

    private static GeneratedOutput Output(string path, string text) =>
        new(path, DotNetSourceText.Utf8(text));
}
