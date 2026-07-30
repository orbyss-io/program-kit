using System.Collections.Immutable;
using Orbyss.ProgramKit.CommandLine.Operations.Files;

namespace Orbyss.ProgramKit.UnitTests.CommandLine.Operations.DotNet.Materialization;

internal sealed class ThrowingMoveCommandFileSystem : ICommandFileSystem
{
    private readonly ICommandFileSystem inner;

    internal ThrowingMoveCommandFileSystem(ICommandFileSystem inner)
    {
        this.inner = inner;
    }

    public bool FileExists(string path) => inner.FileExists(path);

    public bool DirectoryExists(string path) => inner.DirectoryExists(path);

    public void CreateDirectory(string path) => inner.CreateDirectory(path);

    public void MoveDirectory(string sourcePath, string destinationPath) =>
        inner.MoveDirectory(sourcePath, destinationPath);

    public void MoveFile(
        string sourcePath,
        string destinationPath,
        bool overwrite) =>
        throw new IOException("Simulated interrupted promotion.");

    public void DeleteFile(string path) => inner.DeleteFile(path);

    public void DeleteDirectory(string path) => inner.DeleteDirectory(path);

    public void SetReadOnly(string path, bool isReadOnly) =>
        inner.SetReadOnly(path, isReadOnly);

    public ImmutableArray<string> EnumerateFiles(string path) =>
        inner.EnumerateFiles(path);

    public long GetFileSize(string path) => inner.GetFileSize(path);

    public ValueTask<ReadOnlyMemory<byte>> ReadAllBytesAsync(
        string path,
        CancellationToken cancellationToken) =>
        inner.ReadAllBytesAsync(path, cancellationToken);

    public ValueTask WriteAllBytesAsync(
        string path,
        ReadOnlyMemory<byte> content,
        CancellationToken cancellationToken) =>
        inner.WriteAllBytesAsync(path, content, cancellationToken);
}
