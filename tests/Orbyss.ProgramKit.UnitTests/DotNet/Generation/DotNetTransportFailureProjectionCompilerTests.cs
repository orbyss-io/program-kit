using Orbyss.ProgramKit.DotNet.Generation;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Generation;

[TestClass]
public sealed class DotNetTransportFailureProjectionCompilerTests
{
    [TestMethod]
    public void ExactProfileGeneratesOrderedSafeDeterministicComposition()
    {
        var host = ApiHost();
        DotNetTransportFailureProjectionCompiler sut = new();

        var first = sut.Compile(host);
        var second = sut.Compile(host);
        var source = string.Join(
            Environment.NewLine,
            first.Select(static output =>
                System.Text.Encoding.UTF8.GetString(output.Content.Span)));
        var registration = sut.RenderRegistration(host);
        var middleware = sut.RenderMiddleware(host);

        Assert.HasCount(6, first);
        Assert.AreSequenceEqual(
            first.Select(static output => output.RelativePath).ToArray(),
            second.Select(static output => output.RelativePath).ToArray());
        foreach (var pair in first.Zip(second))
        {
            Assert.AreSequenceEqual(
                pair.First.Content.ToArray(),
                pair.Second.Content.ToArray());
        }
        Assert.Contains("exception is global::System.InvalidOperationException", source);
        Assert.Contains("exception is OperationCanceledException", source);
        Assert.Contains("context.Response.HasStarted", source);
        Assert.Contains("context.Abort()", source);
        Assert.Contains("environment.IsDevelopment()", source);
        Assert.IsFalse(source.Contains("exception.Message", StringComparison.Ordinal));
        Assert.Contains("AddProblemDetails", registration);
        Assert.IsLessThan(
            registration.IndexOf("ProgramKitMappedTransportFailureHandler", StringComparison.Ordinal),
            registration.IndexOf("ProgramKitClientDisconnectExceptionHandler", StringComparison.Ordinal));
        Assert.IsLessThan(
            registration.IndexOf("ProgramKitFallbackTransportFailureHandler", StringComparison.Ordinal),
            registration.IndexOf("ProgramKitMappedTransportFailureHandler", StringComparison.Ordinal));
        Assert.Contains("SuppressDiagnosticsCallback = static _ => true", middleware);
        Assert.Contains("app.UseStatusCodePages(async statusCodeContext =>", middleware);
        Assert.Contains("problemDetails.TryWriteAsync", middleware);
    }

    private static DotNetHostDefinition ApiHost()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts.Single(static candidate => candidate.Kind == DotNetHostKind.Api);
        return host with
        {
            TransportFailures = DotNetTestContractFactory.TransportFailures(),
        };
    }
}
