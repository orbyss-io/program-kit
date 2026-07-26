using System.Text.Json;
using GeneratedHost.Composition;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet;

[TestClass]
public sealed class FastEndpointsRuntimeConformanceTests
{
    [TestMethod]
    public async Task AspNetCoreMiddlewareRemainsTheExactSecurityOwner()
    {
        var anonymous = await FastEndpointsHarness.RunAsync(
            "/anonymous",
            authenticated: false);
        var challenged = await FastEndpointsHarness.RunAsync(
            "/protected",
            authenticated: false);
        var accepted = await FastEndpointsHarness.RunAsync(
            "/protected",
            authenticated: true);
        var forbidden = await FastEndpointsHarness.RunAsync(
            "/denied",
            authenticated: true);

        Assert.AreEqual(204, anonymous.StatusCode);
        Assert.AreEqual(401, challenged.StatusCode);
        Assert.AreEqual(204, accepted.StatusCode);
        Assert.AreEqual(403, forbidden.StatusCode);
    }

    [TestMethod]
    public async Task ExceptionsReachTheExactAspNetCoreProblemDetailsOwner()
    {
        var response = await FastEndpointsHarness.RunAsync(
            "/failure",
            authenticated: false);
        using var problem = JsonDocument.Parse(response.Content);
        var root = problem.RootElement;

        Assert.AreEqual(409, response.StatusCode);
        Assert.AreEqual("application/problem+json", response.MediaType);
        Assert.AreEqual(
            "https://errors.orbyss.test/conflict",
            root.GetProperty("type").GetString());
        Assert.AreEqual("Conflict", root.GetProperty("title").GetString());
        Assert.AreEqual(409, root.GetProperty("status").GetInt32());
        Assert.AreEqual(
            "The request conflicts with the current state.",
            root.GetProperty("detail").GetString());
        Assert.DoesNotContain(
            "This message must never enter the response.",
            response.Content,
            StringComparison.Ordinal);
    }
}
