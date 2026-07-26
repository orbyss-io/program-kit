using System.Net;
using System.Security.Cryptography;
using System.Text;
using GeneratedOAuthServiceClients.Operations;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Security;

[TestClass]
public sealed class OAuthServiceClientConformanceTests
{
    private const string AccessTokenType =
        "urn:ietf:params:oauth:token-type:access_token";

    [TestMethod]
    public async Task ExactClientCredentialsAndExchangeRequestsAreAcceptedAndCached()
    {
        var handler = new AuthorizationServerHandler();
        OAuthServiceClientProbe sut = new(new HttpClient(handler));
        var profile = Profile();
        var secret = Ephemeral();
        var subject = new OAuthSourceToken(Ephemeral(), AccessTokenType, "explicit-subject");
        var actor = new OAuthSourceToken(
            Ephemeral(),
            "urn:ietf:params:oauth:token-type:jwt",
            "explicit-actor");

        var client = await sut.ClientCredentialsAsync(profile, secret, default);
        var exchange = await sut.ExchangeAsync(
            profile,
            secret,
            subject,
            actor,
            true,
            default);
        var cached = await sut.ExchangeAsync(
            profile,
            secret,
            subject,
            actor,
            true,
            default);

        Assert.AreEqual("accepted", client.Evidence.Outcome);
        Assert.AreEqual("accepted", exchange.Evidence.Outcome);
        Assert.AreEqual("cache-hit", cached.Evidence.Outcome);
        Assert.AreEqual(2, handler.RequestCount);
        Assert.IsTrue(handler.SawClientCredentials);
        Assert.IsTrue(handler.SawExactExchange);
        Assert.DoesNotContain(client.Token.Value, client.Evidence.ToString());
        Assert.DoesNotContain(exchange.Token.Value, exchange.Evidence.ToString());
    }

    [TestMethod]
    public void CacheKeysIsolateEverySecurityDimensionAndNeverContainTokens()
    {
        var profile = Profile();
        var first = new OAuthSourceToken(Ephemeral(), AccessTokenType, "subject-a");
        var second = first with { ProvenanceIdentity = "subject-b" };
        var keyOne = OAuthServiceClientProbe.CreateCacheKey(profile, first, null);
        var keyTwo = OAuthServiceClientProbe.CreateCacheKey(profile, second, null);
        var keyThree = OAuthServiceClientProbe.CreateCacheKey(
            profile with { Audience = "other-api" },
            first,
            null);

        Assert.AreNotEqual(keyOne, keyTwo);
        Assert.AreNotEqual(keyOne, keyThree);
        Assert.DoesNotContain(first.Value, keyOne);
    }

    [TestMethod]
    public async Task ConfusedModeWrongResponseOutageAndCancellationFailClosedWithoutRetry()
    {
        OAuthServiceClientProbe confused = new(
            new HttpClient(new AuthorizationServerHandler()));
        var subject = new OAuthSourceToken(Ephemeral(), AccessTokenType, "subject");
        var actor = new OAuthSourceToken(Ephemeral(), AccessTokenType, "actor");
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await confused.ExchangeAsync(
                Profile(),
                Ephemeral(),
                subject,
                actor,
                false,
                default));

        var rejectedHandler = new AuthorizationServerHandler
        {
            StatusCode = HttpStatusCode.ServiceUnavailable,
        };
        OAuthServiceClientProbe rejected = new(new HttpClient(rejectedHandler));
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await rejected.ClientCredentialsAsync(Profile(), Ephemeral(), default));
        Assert.AreEqual(1, rejectedHandler.RequestCount);

        var wrongTypeHandler = new AuthorizationServerHandler
        {
            IssuedTokenType = "urn:ietf:params:oauth:token-type:jwt",
        };
        OAuthServiceClientProbe wrongType = new(new HttpClient(wrongTypeHandler));
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await wrongType.ClientCredentialsAsync(Profile(), Ephemeral(), default));

        using CancellationTokenSource cancellation = new();
        cancellation.Cancel();
        await Assert.ThrowsAsync<OperationCanceledException>(async () =>
            await confused.ClientCredentialsAsync(
                Profile(),
                Ephemeral(),
                cancellation.Token));
    }

    private static OAuthProfile Profile() =>
        new(
            "catalog-service",
            new Uri("https://identity.example.test/connect/token"),
            "catalog-client",
            new Uri("https://catalog.example.test/"),
            "catalog-api",
            "catalog.read",
            AccessTokenType,
            AccessTokenType,
            300,
            30);

    private static string Ephemeral() =>
        Convert.ToBase64String(RandomNumberGenerator.GetBytes(32));

}
