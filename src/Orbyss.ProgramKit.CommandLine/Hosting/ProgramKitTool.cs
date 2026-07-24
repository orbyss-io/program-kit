using Orbyss.ProgramKit.CommandLine.Composition;

namespace Orbyss.ProgramKit.CommandLine.Hosting;

/// <summary>Process entry point for the <c>program-kit</c> .NET tool.</summary>
public static class ProgramKitTool
{
    /// <summary>Runs one command using only explicit OS tokens and standard streams.</summary>
    public static async Task<int> Main(string[] args)
    {
        var application = CommandLineComposition.CreateDefault();
        var exitCode = await application.RunAsync(
            args,
            CancellationToken.None).ConfigureAwait(false);
        return (int)exitCode;
    }
}
