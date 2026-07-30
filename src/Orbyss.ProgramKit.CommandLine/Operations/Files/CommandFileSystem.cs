using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.Files;

/// <summary>Filesystem implementation with no search or discovery behavior.</summary>
public sealed class CommandFileSystem : ICommandFileSystem
{
    /// <inheritdoc />
    public bool FileExists(string path)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        return File.Exists(Path.GetFullPath(path));
    }

    /// <inheritdoc />
    public bool DirectoryExists(string path)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        return Directory.Exists(Path.GetFullPath(path));
    }

    /// <inheritdoc />
    public void CreateDirectory(string path)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        Directory.CreateDirectory(Path.GetFullPath(path));
    }

    /// <inheritdoc />
    public void MoveDirectory(string sourcePath, string destinationPath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sourcePath);
        ArgumentException.ThrowIfNullOrWhiteSpace(destinationPath);
        Directory.Move(
            Path.GetFullPath(sourcePath),
            Path.GetFullPath(destinationPath));
    }

    /// <inheritdoc />
    public void DeleteDirectory(string path)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        var fullPath = Path.GetFullPath(path);
        if (Directory.Exists(fullPath))
        {
            Directory.Delete(fullPath, recursive: true);
        }
    }

    /// <inheritdoc />
    public ImmutableArray<string> EnumerateFiles(string path)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        return Directory
            .EnumerateFiles(
                Path.GetFullPath(path),
                "*",
                SearchOption.AllDirectories)
            .Order(StringComparer.Ordinal)
            .ToImmutableArray();
    }

    /// <inheritdoc />
    public long GetFileSize(string path)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        return new FileInfo(Path.GetFullPath(path)).Length;
    }

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

    /// <inheritdoc />
    public void DeleteFile(string path)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        var fullPath = Path.GetFullPath(path);
        if (File.Exists(fullPath))
        {
            File.Delete(fullPath);
        }
    }
}
