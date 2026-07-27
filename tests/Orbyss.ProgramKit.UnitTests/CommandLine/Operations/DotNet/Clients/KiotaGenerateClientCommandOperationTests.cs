using Orbyss.ProgramKit.CommandLine.Commands.Parsing;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Descriptors;
using Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.DotNet.Clients;

[TestClass]
public sealed class KiotaGenerateClientCommandOperationTests
{
    [TestMethod]
    public async Task CommandBindsEveryExactLocalInputAndFixedCSharpProfile()
    {
        CommandParser parser = new(CommandDescriptorCatalog.All);
        var invocation = parser.Parse(
        [
            "dotnet",
            "generate-client",
            "--openapi",
            "foreign.openapi.json",
            "--tool-manifest",
            "dotnet-tools.json",
            "--tool-package",
            "kiota.nupkg",
            "--namespace-name",
            "Example.Foreign",
            "--class-name",
            "ForeignClient",
            "--output",
            "generated",
        ]);
        RecordingKiotaForeignClientGenerator generator = new();
        KiotaGenerateClientCommandOperation operation = new(generator);

        var result = await operation.ExecuteAsync(
            invocation,
            CancellationToken.None);

        Assert.AreEqual(CommandExitCode.Success, result.ExitCode);
        Assert.IsNotNull(generator.Request);
        Assert.AreEqual(
            "foreign.openapi.json",
            generator.Request.OpenApiPath);
        Assert.AreEqual(
            "dotnet-tools.json",
            generator.Request.ToolManifestPath);
        Assert.AreEqual("kiota.nupkg", generator.Request.ToolPackagePath);
        Assert.AreEqual("Example.Foreign", generator.Request.NamespaceName);
        Assert.AreEqual("ForeignClient", generator.Request.ClassName);
        Assert.IsEmpty(generator.Request.IncludePatterns);
        Assert.IsEmpty(generator.Request.ExcludePatterns);
    }
}
