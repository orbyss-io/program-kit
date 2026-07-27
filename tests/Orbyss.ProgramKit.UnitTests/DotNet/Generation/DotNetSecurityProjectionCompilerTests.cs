using System.Text;
using Orbyss.ProgramKit.DotNet.Generation;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Generation;

[TestClass]
public sealed class DotNetSecurityProjectionCompilerTests
{
    [TestMethod]
    public void ExactProfilesGenerateHardenedProtocolAndPolicyMechanics()
    {
        var host = ApiHost();
        DotNetSecurityProjectionCompiler sut = new();

        var first = sut.Compile(host);
        var second = sut.Compile(host);
        var source = string.Join(
            Environment.NewLine,
            first.Select(static output =>
                Encoding.UTF8.GetString(output.Content.Span)));
        var registration = sut.RenderRegistration(host);
        var middleware = sut.RenderMiddleware(host);

        Assert.AreSequenceEqual(
            first.Select(static output => output.RelativePath).ToArray(),
            second.Select(static output => output.RelativePath).ToArray());
        foreach (var pair in first.Zip(second))
        {
            Assert.AreSequenceEqual(
                pair.First.Content.ToArray(),
                pair.Second.Content.ToArray());
        }

        Assert.Contains("options.UsePkce = true", registration);
        Assert.Contains("RequireNonce = true", registration);
        Assert.Contains(
            "OpenIdConnectHandler validates protected state and correlation",
            registration);
        Assert.Contains("RequireStateValidation = false", registration);
        Assert.Contains("options.Cookie.Path = \"/\";", registration);
        Assert.Contains("options.CorrelationCookie.Path = \"/\";", registration);
        Assert.Contains("options.NonceCookie.Path = \"/\";", registration);
        Assert.Contains("options.MapInboundClaims = false", registration);
        Assert.Contains("options.SaveTokens = false", registration);
        Assert.Contains(
            "OnRedirectToIdentityProviderForSignOut",
            registration);
        Assert.Contains(
            "context.ProtocolMessage.ClientId = context.Options.ClientId",
            registration);
        Assert.Contains("ValidTypes = [\"at+jwt\"]", registration);
        Assert.Contains("ValidateIssuerSigningKey = true", registration);
        Assert.Contains("RequireAuthenticatedUser", registration);
        Assert.IsFalse(registration.Contains(
            "ClientSecret = \"",
            StringComparison.Ordinal));
        Assert.Contains("TemplateMatcher", source);
        Assert.Contains("AuthorizeAsync", source);
        Assert.Contains("ChallengeAsync", source);
        Assert.Contains("ForbidAsync", source);
        Assert.Contains("Microsoft.NET.Sdk.BlazorWebAssembly", source);
        Assert.Contains("AddOidcAuthentication", source);
        Assert.Contains("ResponseType = \"code\"", source);
        Assert.Contains("<base href=\"/\" />", source);
        Assert.Contains("<RedirectToLogin />", source);
        Assert.Contains(
            "Navigation.NavigateToLogin(\"authentication/login\")",
            source);
        Assert.Contains(
            "Navigation.NavigateToLogout(\"authentication/logout\")",
            source);
        Assert.Contains(
            "@using Microsoft.AspNetCore.Components.Web",
            source);
        Assert.Contains("AuthenticationService.js", source);
        Assert.Contains("window.localStorage.length", source);
        Assert.Contains("RefreshTokenExpected = false", source);
        Assert.Contains("IsSafeAuthorizationResponse", source);
        Assert.Contains("assertProtectedApiAccess", source);
        Assert.Contains("assertAdversarialFailures", source);
        Assert.Contains("\"chromium\" => playwright.Chromium", source);
        Assert.Contains("\"firefox\" => playwright.Firefox", source);
        Assert.Contains("\"webkit\" => playwright.Webkit", source);
        Assert.Contains("policy.DisallowCredentials()", registration);
        Assert.Contains("app.UseCors(\"ProgramKit.PublicBrowser\")", middleware);
        Assert.Contains("grant-type:token-exchange", source);
        Assert.Contains("subject_token_type", source);
        Assert.Contains("actor_token_type", source);
        Assert.Contains("CreateCacheKey", source);
        Assert.Contains("SHA256.HashData", source);
        Assert.Contains("AddHttpClient(\"ProgramKit.OAuth.catalog-service\"", registration);
        var oauthSource = string.Join(
            Environment.NewLine,
            first.Where(static output =>
                    output.RelativePath.Contains("OAuth", StringComparison.Ordinal))
                .Select(static output => Encoding.UTF8.GetString(output.Content.Span)));
        Assert.DoesNotContain("HttpContext", oauthSource);
        Assert.DoesNotContain("GetTokenAsync", oauthSource);
        var browserSource = string.Join(
            Environment.NewLine,
            first.Where(static output =>
                    output.RelativePath.StartsWith("PublicBrowser", StringComparison.Ordinal))
                .Select(static output => Encoding.UTF8.GetString(output.Content.Span)));
        Assert.IsFalse(browserSource.Contains(
            "client_secret",
            StringComparison.OrdinalIgnoreCase));
        Assert.IsFalse(source.Contains("offline_access", StringComparison.OrdinalIgnoreCase));
        Assert.IsTrue(first.Any(static output =>
            output.RelativePath == "PublicBrowser/PublicBrowser.csproj"));
        Assert.IsTrue(first.Any(static output =>
            output.RelativePath ==
            "PublicBrowser/Shared/RedirectToLogin.razor"));
        Assert.IsTrue(first.Any(static output =>
            output.RelativePath ==
            "PublicBrowser/Shared/ProgramKitLogout.razor"));
        Assert.IsTrue(first.Any(static output =>
            output.RelativePath ==
            "PublicBrowserVerification/chromium.runsettings"));
        Assert.IsLessThan(
            middleware.IndexOf(
                "ProgramKitOperationAuthorizationMiddleware",
                StringComparison.Ordinal),
            middleware.IndexOf("UseAuthorization", StringComparison.Ordinal));
    }

    [TestMethod]
    public void PublicBrowserGenerationKeepsAuthenticationMaterialEphemeral()
    {
        var host = ApiHost();
        DotNetSecurityProjectionCompiler sut = new();

        var outputs = sut.Compile(host);
        var combined = string.Join(
            Environment.NewLine,
            outputs.Select(static output =>
                Encoding.UTF8.GetString(output.Content.Span)));

        Assert.DoesNotContain("StorageStateAsync", combined);
        Assert.DoesNotContain("RecordHarPath = \"", combined);
        Assert.DoesNotContain("RecordVideoDir = \"", combined);
        Assert.DoesNotContain("access_token=", combined.Replace(
            "request.Url.Contains(\"access_token=\"",
            string.Empty,
            StringComparison.Ordinal));
        Assert.Contains("playwright/.auth/", combined);
        Assert.Contains("Headless = false", combined);
        Assert.Contains("waitForHumanControlledCallback", combined);
        Assert.Contains("ClearCookiesAsync", combined);
    }

    [TestMethod]
    public void AssertionAuthenticationGeneratesOnlyBoundedConsumerAdapter()
    {
        var host = ApiHost();
        var security = host.Security!;
        var oidc = security.OidcConfidentialInteractive!;
        var assertion = oidc.ClientAuthentication with
        {
            Method = Orbyss.ProgramKit.DotNet.Operations.Security
                .DotNetOidcClientAuthenticationMethod.PrivateKeyJwtAssertion,
            Reference = oidc.ClientAuthentication.Reference with
            {
                ExpectedResultKind = Orbyss.ProgramKit.SecretResolution.Contracts
                    .SecretResultKind.AssertionService,
            },
            ConfigurationKey = null,
        };
        host = host with
        {
            Security = security with
            {
                OidcConfidentialInteractive = oidc with
                {
                    ClientAuthentication = assertion,
                },
            },
        };
        DotNetSecurityProjectionCompiler sut = new();

        var outputs = sut.Compile(host);
        var registration = sut.RenderRegistration(host);

        Assert.IsTrue(outputs.Any(static output =>
            output.RelativePath.EndsWith(
                "IProgramKitOidcClientAssertionProvider.cs",
                StringComparison.Ordinal)));
        Assert.Contains("ClientAssertionType", registration);
        Assert.Contains("assertion.ExpiresAt", registration);
        Assert.IsFalse(registration.Contains(
            "builder.Configuration[",
            StringComparison.Ordinal));
    }

    private static DotNetHostDefinition ApiHost() =>
        DotNetTestContractFactory.Shell().Hosts.Single(static candidate =>
            candidate.Kind == DotNetHostKind.Api);
}
