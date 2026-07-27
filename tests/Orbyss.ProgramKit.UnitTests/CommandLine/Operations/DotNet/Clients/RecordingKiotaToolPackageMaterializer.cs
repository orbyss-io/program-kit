using Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.DotNet.Clients;

internal sealed class RecordingKiotaToolPackageMaterializer :
    IKiotaToolPackageMaterializer
{
    internal List<(string PackagePath, string OutputRoot)> Requests { get; } = [];

    public async ValueTask<string> MaterializeAsync(
        string packagePath,
        string outputRoot,
        CancellationToken cancellationToken)
    {
        Requests.Add((packagePath, outputRoot));
        var entryPath = Path.Combine(
            outputRoot,
            "tools",
            "net10.0",
            "any",
            "kiota.dll");
        Directory.CreateDirectory(Path.GetDirectoryName(entryPath)!);
        await File.WriteAllBytesAsync(
            entryPath,
            [0x4b, 0x69, 0x6f, 0x74, 0x61],
            cancellationToken);
        return entryPath;
    }
}
