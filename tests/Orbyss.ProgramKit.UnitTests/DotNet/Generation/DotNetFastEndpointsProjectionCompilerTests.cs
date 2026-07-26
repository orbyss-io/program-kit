using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.DotNet.Generation.FastEndpoints;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.UnitTests.DotNet.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.DotNet.Generation;

[TestClass]
public sealed class DotNetFastEndpointsProjectionCompilerTests
{
    [TestMethod]
    public void ExactProfileGeneratesDeterministicSyntaxAdapterAndParityEvidence()
    {
        var shell = DotNetTestContractFactory.WithFastEndpoints(
            DotNetTestContractFactory.Shell());
        var host = shell.Hosts.Single(static candidate =>
            candidate.Kind == DotNetHostKind.Api);
        var document = DotNetTestContractFactory.ApiDocument(shell);
        DotNetFastEndpointsProjectionCompiler sut = new();

        var first = sut.Compile(host, document);
        var second = sut.Compile(host, document);
        var endpoint = first.Single(static output =>
            IsEndpointOutput(output.RelativePath));
        var endpointSource = Encoding.UTF8.GetString(endpoint.Content.Span);
        var featureSource = Encoding.UTF8.GetString(first.Single(static output =>
            output.RelativePath.EndsWith(
                "ProgramKitFastEndpointsFeature.cs",
                StringComparison.Ordinal)).Content.Span);
        var evidence = first.Single(static output =>
            output.RelativePath.EndsWith(
                "fastendpoints-projection.json",
                StringComparison.Ordinal));
        using var evidenceJson = JsonDocument.Parse(evidence.Content);
        var root = evidenceJson.RootElement;
        var operation = root.GetProperty("operations")[0];

        Assert.HasCount(4, first);
        Assert.AreSequenceEqual(
            first.Select(static output => output.RelativePath).ToArray(),
            second.Select(static output => output.RelativePath).ToArray());
        foreach (var pair in first.Zip(second))
        {
            Assert.AreSequenceEqual(
                pair.First.Content.ToArray(),
                pair.Second.Content.ToArray());
        }

        Assert.Contains("AllowAnonymous();", endpointSource);
        Assert.Contains("DontCatchExceptions();", endpointSource);
        Assert.Contains(
            "IProgramKitFastEndpointOperationDispatcher",
            endpointSource);
        Assert.Contains("HttpContext", endpointSource);
        Assert.Contains(
            "IFastEndpointsShellFeature",
            featureSource);
        Assert.Contains(
            "DependsOn = [\"FastEndpoints\"]",
            featureSource);
        Assert.AreEqual(
            "generated-aspnet-core-operation-authorization-middleware",
            root.GetProperty("securityOwner").GetString());
        Assert.AreEqual(
            "generated-aspnet-core-exception-handler-and-problem-details",
            root.GetProperty("transportFailureOwner").GetString());
        Assert.IsTrue(root.GetProperty("fastEndpointsSecurityNeutralized").GetBoolean());
        Assert.IsTrue(root.GetProperty("fastEndpointsExceptionCatchingDisabled").GetBoolean());
        Assert.IsFalse(root.GetProperty("parallelOpenApiGenerated").GetBoolean());
        Assert.AreEqual("/runs", operation.GetProperty("path").GetString());
        Assert.AreEqual("POST", operation.GetProperty("method").GetString());
        Assert.AreEqual(1, operation.GetProperty("requestContractRevisions").GetArrayLength());
        Assert.AreEqual(1, operation.GetProperty("resultContractRevisions").GetArrayLength());
        Assert.AreEqual(2, operation.GetProperty("problemDetails").GetArrayLength());
        Assert.IsFalse(
            operation.GetProperty("security").GetProperty("anonymous").GetBoolean());
    }

    [TestMethod]
    public void ChangedRouteChangesOnlyTheAffectedEndpointIdentityAndEvidence()
    {
        var shell = DotNetTestContractFactory.WithFastEndpoints(
            DotNetTestContractFactory.Shell());
        var host = shell.Hosts.Single(static candidate =>
            candidate.Kind == DotNetHostKind.Api);
        var original = DotNetTestContractFactory.ApiDocument(shell);
        var changed = original with
        {
            Operations =
            [
                original.Operations[0] with { Path = "/executions" },
            ],
        };
        DotNetFastEndpointsProjectionCompiler sut = new();

        var before = sut.Compile(host, original);
        var after = sut.Compile(host, changed);

        foreach (var stableName in new[]
                 {
                     "IProgramKitFastEndpointOperationDispatcher.cs",
                     "ProgramKitFastEndpointsFeature.cs",
                 })
        {
            var beforeStable = before.Single(output =>
                output.RelativePath.EndsWith(
                    stableName,
                    StringComparison.Ordinal));
            var afterStable = after.Single(output =>
                output.RelativePath.EndsWith(
                    stableName,
                    StringComparison.Ordinal));
            Assert.AreSequenceEqual(
                beforeStable.Content.ToArray(),
                afterStable.Content.ToArray());
        }

        var beforeEndpoint = before.Single(static output =>
            IsEndpointOutput(output.RelativePath));
        var afterEndpoint = after.Single(static output =>
            IsEndpointOutput(output.RelativePath));
        Assert.AreNotEqual(
            beforeEndpoint.RelativePath,
            afterEndpoint.RelativePath);
        var beforeEvidence = before.Single(static output =>
            output.RelativePath.EndsWith(
                "fastendpoints-projection.json",
                StringComparison.Ordinal));
        var afterEvidence = after.Single(static output =>
            output.RelativePath.EndsWith(
                "fastendpoints-projection.json",
                StringComparison.Ordinal));
        Assert.IsFalse(
            beforeEvidence.Content.Span.SequenceEqual(
                afterEvidence.Content.Span));
    }

    [TestMethod]
    public void DisabledProfileGeneratesNoFastEndpointsOutputs()
    {
        var shell = DotNetTestContractFactory.Shell();
        var host = shell.Hosts.Single(static candidate =>
            candidate.Kind == DotNetHostKind.Api);
        DotNetFastEndpointsProjectionCompiler sut = new();

        var outputs = sut.Compile(
            host,
            DotNetTestContractFactory.ApiDocument(shell));

        Assert.IsEmpty(outputs);
    }

    private static bool IsEndpointOutput(string path) =>
        path.StartsWith(
            "ProgramKitGenerated/Hosting/ProgramKitFastEndpoint",
            StringComparison.Ordinal) &&
        !path.EndsWith(
            "ProgramKitFastEndpointsFeature.cs",
            StringComparison.Ordinal);
}
