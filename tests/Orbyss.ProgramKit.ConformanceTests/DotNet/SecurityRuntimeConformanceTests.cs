using GeneratedHost.Composition;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet;

[TestClass]
public sealed class SecurityRuntimeConformanceTests
{
    [TestMethod]
    public async Task AnonymousAndProtectedOperationsHaveExactDisposition()
    {
        var anonymous = await SecurityHarness.RunAsync(
            "/anonymous",
            authenticated: false);
        var challenged = await SecurityHarness.RunAsync(
            "/protected",
            authenticated: false);
        var accepted = await SecurityHarness.RunAsync(
            "/protected",
            authenticated: true);

        Assert.AreEqual(204, anonymous);
        Assert.AreEqual(401, challenged);
        Assert.AreEqual(204, accepted);
    }

    [TestMethod]
    public async Task AuthenticatedPolicyFailureForbids()
    {
        var forbidden = await SecurityHarness.RunAsync(
            "/denied",
            authenticated: true);

        Assert.AreEqual(403, forbidden);
    }

    [TestMethod]
    public async Task JwtResourceServerAcceptsOnlyExactAccessTokenVectors()
    {
        Assert.IsTrue(await JwtVectorHarness.ValidateAsync("valid"));
        Assert.IsFalse(await JwtVectorHarness.ValidateAsync("wrong-issuer"));
        Assert.IsFalse(await JwtVectorHarness.ValidateAsync("wrong-audience"));
        Assert.IsFalse(await JwtVectorHarness.ValidateAsync("expired"));
        Assert.IsFalse(await JwtVectorHarness.ValidateAsync("unsigned"));
        Assert.IsFalse(await JwtVectorHarness.ValidateAsync("id-token-type"));
    }
}
