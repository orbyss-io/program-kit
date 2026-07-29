using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Operations.Processes;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.DotNet.Materialization;

internal sealed class RecordingConsoleMaterializationRunner(
    string targetReferencePath,
    int buildExitCode = 0,
    IReadOnlyList<string>? compilationReferencePaths = null) :
    ICommandProcessRunner
{
    private string? targetAssemblyPath;

    internal List<CommandProcessRequest> Requests { get; } = [];

    public ValueTask<CommandProcessResult> RunAsync(
        CommandProcessRequest request,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        Requests.Add(request);
        if (request.Arguments[0] == "build")
        {
            if (buildExitCode == 0)
            {
                targetAssemblyPath = Path.Combine(
                    request.WorkingDirectory,
                    "src",
                    "JTest.Console.Integration",
                    "bin",
                    "Release",
                    "net10.0",
                    "JTest.Console.Integration.dll");
                Directory.CreateDirectory(
                    Path.GetDirectoryName(targetAssemblyPath) ??
                    throw new InvalidOperationException());
                File.Copy(
                    targetReferencePath,
                    targetAssemblyPath,
                    overwrite: true);
            }

            return ValueTask.FromResult(
                new CommandProcessResult(
                    buildExitCode,
                    string.Empty,
                    buildExitCode == 0 ? string.Empty : "fixture build failed"));
        }

        Assert.AreEqual("msbuild", request.Arguments[0]);
        var references = (compilationReferencePaths ??
                [targetReferencePath])
            .Select(path => new
            {
                Identity = path,
                FullPath = path,
            })
            .ToArray();
        var output = JsonSerializer.Serialize(
            new
            {
                Properties = new
                {
                    TargetPath = targetAssemblyPath ??
                        throw new InvalidOperationException(
                            "The fixture build did not produce a target assembly."),
                    TargetRefPath = targetReferencePath,
                },
                Items = new
                {
                    ReferencePathWithRefAssemblies = references,
                },
            });
        return ValueTask.FromResult(
            new CommandProcessResult(0, output, string.Empty));
    }
}
