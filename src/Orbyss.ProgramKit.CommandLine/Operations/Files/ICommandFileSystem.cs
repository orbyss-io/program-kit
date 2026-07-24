namespace Orbyss.ProgramKit.CommandLine.Operations.Files;

/// <summary>Explicit file boundary used by command operation adapters.</summary>
public interface ICommandFileSystem
{
    /// <summary>Reads exact bytes from one explicitly supplied path.</summary>
    ValueTask<ReadOnlyMemory<byte>> ReadAllBytesAsync(
        string path,
        CancellationToken cancellationToken);

    /// <summary>Writes exact bytes to one explicitly supplied path.</summary>
    ValueTask WriteAllBytesAsync(
        string path,
        ReadOnlyMemory<byte> content,
        CancellationToken cancellationToken);
}
