using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.Files;

/// <summary>Explicit file boundary used by command operation adapters.</summary>
public interface ICommandFileSystem
{
    /// <summary>Returns whether one exact file exists.</summary>
    bool FileExists(string path);

    /// <summary>Returns whether one exact directory exists.</summary>
    bool DirectoryExists(string path);

    /// <summary>Creates one exact directory and its parents.</summary>
    void CreateDirectory(string path);

    /// <summary>Moves one exact directory without overwrite semantics.</summary>
    void MoveDirectory(string sourcePath, string destinationPath);

    /// <summary>Deletes one exact operation-owned directory.</summary>
    void DeleteDirectory(string path);

    /// <summary>Enumerates exact files below one supplied directory.</summary>
    ImmutableArray<string> EnumerateFiles(string path);

    /// <summary>Gets the exact size of one supplied file.</summary>
    long GetFileSize(string path);

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
