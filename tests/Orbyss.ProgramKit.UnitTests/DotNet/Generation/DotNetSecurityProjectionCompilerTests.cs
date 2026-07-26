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
        Assert.Contains("RequireStateValidation = true", registration);
        Assert.Contains("options.MapInboundClaims = false", registration);
        Assert.Contains("options.SaveTokens = false", registration);
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
        Assert.IsLessThan(
            middleware.IndexOf(
                "ProgramKitOperationAuthorizationMiddleware",
                StringComparison.Ordinal),
            middleware.IndexOf("UseAuthorization", StringComparison.Ordinal));
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
