using GeneratedPublicBrowser.Operations;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Security;

[TestClass]
public sealed class PublicBrowserProtocolConformanceTests
{
    [TestMethod]
    public void PkceUsesTheRfc7636S256GoldenVector()
    {
        const string verifier =
            "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk";

        var challenge =
            PublicBrowserProtocolProbe.CreateS256Challenge(verifier);

        Assert.AreEqual(
            "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM",
            challenge);
    }

    [TestMethod]
    public void RedirectIssuerStateNonceApiTokenAndLogoutBoundariesFailClosed()
    {
        var callback = new Uri(
            "https://browser.example.test/authentication/login-callback");
        var issuer = new Uri("https://identity.example.test/");

        Assert.IsTrue(PublicBrowserProtocolProbe.IsSafeAuthorizationResponse(
            callback,
            issuer,
            "expected-state",
            "expected-state",
            "expected-nonce",
            "expected-nonce"));
        Assert.IsFalse(PublicBrowserProtocolProbe.IsSafeAuthorizationResponse(
            new Uri("https://attacker.example.test/authentication/login-callback"),
            issuer,
            "expected-state",
            "expected-state",
            "expected-nonce",
            "expected-nonce"));
        Assert.IsFalse(PublicBrowserProtocolProbe.IsSafeAuthorizationResponse(
            callback,
            new Uri("https://other-issuer.example.test/"),
            "expected-state",
            "expected-state",
            "expected-nonce",
            "expected-nonce"));
        Assert.IsFalse(PublicBrowserProtocolProbe.IsSafeAuthorizationResponse(
            callback,
            issuer,
            "expected-state",
            "wrong-state",
            "expected-nonce",
            "expected-nonce"));
        Assert.IsFalse(PublicBrowserProtocolProbe.IsSafeAuthorizationResponse(
            callback,
            issuer,
            "expected-state",
            "expected-state",
            "expected-nonce",
            "wrong-nonce"));
        Assert.IsTrue(PublicBrowserProtocolProbe.IsAllowedApiTarget(
            new Uri("https://api.example.test/runs")));
        Assert.IsFalse(PublicBrowserProtocolProbe.IsAllowedApiTarget(
            new Uri("https://attacker.example.test/runs")));
        Assert.IsTrue(PublicBrowserProtocolProbe.IsAccessTokenKind(
            "Bearer",
            "at+jwt"));
        Assert.IsFalse(PublicBrowserProtocolProbe.IsAccessTokenKind(
            "Bearer",
            "JWT"));
        Assert.IsTrue(PublicBrowserProtocolProbe.IsSafeLogoutCallback(
            new Uri(
                "https://browser.example.test/authentication/logout-callback")));
        Assert.IsFalse(PublicBrowserProtocolProbe.IsSafeLogoutCallback(
            new Uri(
                "https://browser.example.test/authentication/logout-callback?token=leak")));
        Assert.IsFalse(PublicBrowserProtocolProbe.RefreshTokenExpected);
    }
}
