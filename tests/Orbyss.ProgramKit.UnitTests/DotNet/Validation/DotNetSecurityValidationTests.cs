using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.DotNet.Diagnostics;
using Orbyss.ProgramKit.DotNet.Operations.Security;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.DotNet.Validation;
using Orbyss.ProgramKit.Operations.Contracts.Validation;
using Orbyss.ProgramKit.SecretResolution.Contracts;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Validation;

[TestClass]
public sealed class DotNetSecurityValidationTests
{
    [TestMethod]
    public void ExactOidcJwtAndOperationPolicyCompositionIsValid()
    {
        var result = Validator().Validate(DotNetTestContractFactory.Shell());

        Assert.IsTrue(
            result.IsValid,
            string.Join(Environment.NewLine, result.Diagnostics));
    }

    [TestMethod]
    public void IdTokenShapedJwtAndMissingOperationCoverageFailClosed()
    {
        var shell = DotNetTestContractFactory.Shell();
        var api = shell.Hosts.Single(static host =>
            host.Kind == DotNetHostKind.Api);
        var security = api.Security!;
        var invalid = security with
        {
            JwtResourceServer = security.JwtResourceServer! with
            {
                AccessTokenProfile = (DotNetJwtAccessTokenProfile)999,
            },
            OperationBindings = [],
        };

        var result = Validator().Validate(ReplaceSecurity(shell, api, invalid));

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == DotNetDiagnosticIds.InvalidSecurityConfiguration));
    }

    [TestMethod]
    public void SecretValueShapeCannotReplaceClassifiedReference()
    {
        var shell = DotNetTestContractFactory.Shell();
        var api = shell.Hosts.Single(static host =>
            host.Kind == DotNetHostKind.Api);
        var security = api.Security!;
        var oidc = security.OidcConfidentialInteractive!;
        var authentication = oidc.ClientAuthentication;
        var invalidReference = authentication.Reference with
        {
            Classification = SecretReferenceClassification.Unspecified,
            ExpectedResultKind = SecretResultKind.Certificate,
        };
        var invalid = security with
        {
            OidcConfidentialInteractive = oidc with
            {
                ClientAuthentication = authentication with
                {
                    Reference = invalidReference,
                    ConfigurationKey = null,
                },
            },
        };

        var result = Validator().Validate(ReplaceSecurity(shell, api, invalid));

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == DotNetDiagnosticIds.UnsafeSecurityMaterial));
    }

    [TestMethod]
    public void PublicBrowserRequiresNoSecretNoRefreshAndHumanThreatAcceptance()
    {
        var shell = DotNetTestContractFactory.Shell();
        var api = shell.Hosts.Single(static host =>
            host.Kind == DotNetHostKind.Api);
        var security = api.Security!;
        var browser = security.OidcPublicBrowser!;
        var invalid = security with
        {
            OidcPublicBrowser = browser with
            {
                ClientSecretAbsent = false,
                RefreshDisposition =
                    DotNetPublicBrowserRefreshDisposition.RotatingBrowserSession,
                HumanAcceptedBrowserHeldTokens = false,
                Scopes = browser.Scopes.Add("offline_access"),
            },
        };

        var result = Validator().Validate(ReplaceSecurity(shell, api, invalid));

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == DotNetDiagnosticIds.InvalidSecurityConfiguration &&
            diagnostic.Path.StartsWith(
                "/hosts/security/oidcPublicBrowser",
                StringComparison.Ordinal)));
    }

    [TestMethod]
    public void PublicBrowserRejectsOriginDriftAndDurableVerificationState()
    {
        var shell = DotNetTestContractFactory.Shell();
        var api = shell.Hosts.Single(static host =>
            host.Kind == DotNetHostKind.Api);
        var security = api.Security!;
        var browser = security.OidcPublicBrowser!;
        var invalid = security with
        {
            OidcPublicBrowser = browser with
            {
                RedirectUri = new Uri(
                    "https://attacker.example.test/authentication/login-callback"),
                CorsAllowedOrigins =
                    [new Uri("https://attacker.example.test/")],
                Verification = browser.Verification with
                {
                    PersistAuthenticationState = true,
                    PersistTrace = true,
                },
            },
        };

        var result = Validator().Validate(ReplaceSecurity(shell, api, invalid));

        Assert.IsFalse(result.IsValid);
        Assert.IsGreaterThanOrEqualTo(
            2,
            result.Diagnostics.Count(static diagnostic =>
                diagnostic.Id ==
                DotNetDiagnosticIds.InvalidSecurityConfiguration));
    }

    [TestMethod]
    public void OAuthServiceClientsRejectAmbientTokensRetriesAndIncompleteCacheIsolation()
    {
        var shell = DotNetTestContractFactory.Shell();
        var api = shell.Hosts.Single(static host => host.Kind == DotNetHostKind.Api);
        var security = api.Security!;
        var client = security.OAuthClientCredentials.Single();
        var invalid = security with
        {
            OAuthClientCredentials =
            [
                client with
                {
                    RetrieveAmbientCurrentUserToken = true,
                    AutomaticRetry = true,
                    Cache = client.Cache with
                    {
                        ExpirySkewSeconds = client.Cache.MaximumLifetimeSeconds,
                    },
                },
            ],
        };

        var result = Validator().Validate(ReplaceSecurity(shell, api, invalid));

        Assert.IsFalse(result.IsValid);
        Assert.IsTrue(result.Diagnostics.Any(static diagnostic =>
            diagnostic.Id == DotNetDiagnosticIds.InvalidSecurityConfiguration &&
            diagnostic.Path.StartsWith(
                "/hosts/security/oauthClientCredentials",
                StringComparison.Ordinal)));
    }

    [TestMethod]
    public void TokenExchangeKeepsSubjectActorAndModeExplicit()
    {
        var shell = DotNetTestContractFactory.Shell();
        var api = shell.Hosts.Single(static host => host.Kind == DotNetHostKind.Api);
        var security = api.Security!;
        var exchange = security.OAuthTokenExchanges.Single();
        var invalid = security with
        {
            OAuthTokenExchanges =
            [
                exchange with
                {
                    ExchangeMode = DotNetOAuthExchangeMode.Impersonation,
                    ActorToken = exchange.SubjectToken,
                },
            ],
        };

        var result = Validator().Validate(ReplaceSecurity(shell, api, invalid));

        Assert.IsFalse(result.IsValid);
        Assert.IsGreaterThanOrEqualTo(
            1,
            result.Diagnostics.Count(static diagnostic =>
                diagnostic.Id == DotNetDiagnosticIds.InvalidSecurityConfiguration &&
                diagnostic.Path.StartsWith(
                    "/hosts/security/oauthTokenExchanges",
                    StringComparison.Ordinal)));
    }

    private static DotNetShellDocument ReplaceSecurity(
        DotNetShellDocument shell,
        DotNetHostDefinition api,
        DotNetSecurityConfiguration security) =>
        shell with
        {
            Hosts = shell.Hosts.Select(host =>
                    host.Identity == api.Identity
                        ? host with { Security = security }
                        : host)
                .ToImmutableArray(),
        };

    private static DotNetShellValidator Validator() =>
        new(
            new ArtifactReferenceValidator(),
            new OperationContractDescriptorValidator(),
            new TransportFailureProfileValidator(),
            new Orbyss.ProgramKit.SecretResolution.Contracts.Validation.SecretResolutionContractValidator(),
            DotNetTestContractFactory.ProviderCatalog());
}
