namespace Orbyss.ProgramKit.CommandLine.Hosting.IO;

/// <summary>Explicit standard-stream boundary for scriptable command execution.</summary>
public interface ICommandConsole
{
    /// <summary>Writes exact bytes to standard output.</summary>
    ValueTask WriteStandardOutputAsync(
        ReadOnlyMemory<byte> content,
        CancellationToken cancellationToken);

    /// <summary>Writes exact bytes to standard error.</summary>
    ValueTask WriteStandardErrorAsync(
        ReadOnlyMemory<byte> content,
        CancellationToken cancellationToken);
}
