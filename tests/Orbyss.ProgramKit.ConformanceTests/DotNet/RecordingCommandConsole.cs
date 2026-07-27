using Orbyss.ProgramKit.CommandLine.Hosting.IO;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet;

internal sealed class RecordingCommandConsole :
    ICommandConsole
{
    private readonly List<byte> standardOutput = [];
    private readonly List<byte> standardError = [];

    internal byte[] StandardOutput => [.. standardOutput];

    internal byte[] StandardError => [.. standardError];

    public ValueTask WriteStandardOutputAsync(
        ReadOnlyMemory<byte> content,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        standardOutput.AddRange(content.ToArray());
        return ValueTask.CompletedTask;
    }

    public ValueTask WriteStandardErrorAsync(
        ReadOnlyMemory<byte> content,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        standardError.AddRange(content.ToArray());
        return ValueTask.CompletedTask;
    }
}
