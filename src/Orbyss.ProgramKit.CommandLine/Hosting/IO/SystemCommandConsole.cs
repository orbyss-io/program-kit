namespace Orbyss.ProgramKit.CommandLine.Hosting.IO;

/// <summary>System console implementation that preserves exact UTF-8 bytes.</summary>
public sealed class SystemCommandConsole : ICommandConsole
{
    /// <inheritdoc />
    public async ValueTask WriteStandardOutputAsync(
        ReadOnlyMemory<byte> content,
        CancellationToken cancellationToken)
    {
        await Console.OpenStandardOutput()
            .WriteAsync(content, cancellationToken)
            .ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async ValueTask WriteStandardErrorAsync(
        ReadOnlyMemory<byte> content,
        CancellationToken cancellationToken)
    {
        await Console.OpenStandardError()
            .WriteAsync(content, cancellationToken)
            .ConfigureAwait(false);
    }
}
