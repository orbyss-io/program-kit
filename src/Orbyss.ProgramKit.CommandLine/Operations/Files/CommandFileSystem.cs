namespace Orbyss.ProgramKit.CommandLine.Operations.Files;

/// <summary>Filesystem implementation with no search or discovery behavior.</summary>
public sealed class CommandFileSystem : ICommandFileSystem
{
    /// <inheritdoc />
    public async ValueTask<ReadOnlyMemory<byte>> ReadAllBytesAsync(
        string path,
        CancellationToken cancellationToken)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        return await File.ReadAllBytesAsync(
            Path.GetFullPath(path),
            cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public async ValueTask WriteAllBytesAsync(
        string path,
        ReadOnlyMemory<byte> content,
        CancellationToken cancellationToken)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        var fullPath = Path.GetFullPath(path);
        var parent = Path.GetDirectoryName(fullPath) ??
            throw new IOException("The explicit output path has no parent directory.");
        Directory.CreateDirectory(parent);
        await File.WriteAllBytesAsync(
            fullPath,
            content.ToArray(),
            cancellationToken).ConfigureAwait(false);
    }
}
