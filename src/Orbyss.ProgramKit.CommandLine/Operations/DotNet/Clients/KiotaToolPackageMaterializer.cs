using System.IO.Compression;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Local;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;

/// <summary>Exact archive verifier and traversal-safe Kiota tool materializer.</summary>
public sealed class KiotaToolPackageMaterializer :
    IKiotaToolPackageMaterializer
{
    private readonly ICommandFileSystem fileSystem;

    /// <summary>Initializes the exact filesystem boundary.</summary>
    public KiotaToolPackageMaterializer(ICommandFileSystem fileSystem)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
    }

    /// <inheritdoc />
    public async ValueTask<string> MaterializeAsync(
        string packagePath,
        string outputRoot,
        CancellationToken cancellationToken)
    {
        var fullPackagePath = Path.GetFullPath(packagePath);
        var fullOutputRoot = Path.GetFullPath(outputRoot);
        if (!fileSystem.FileExists(fullPackagePath))
        {
            throw Failure("The exact Kiota tool package does not exist.");
        }

        var archiveBytes = await fileSystem.ReadAllBytesAsync(
            fullPackagePath,
            cancellationToken).ConfigureAwait(false);
        if (!string.Equals(
                LocalOperationHashes.Sha256(archiveBytes.Span).Value,
                KiotaToolSelection.PackageDigest,
                StringComparison.Ordinal))
        {
            throw Failure(
                "The Kiota tool package bytes differ from the reviewed selection.");
        }

        LocalOperationPaths.EnsureOutputAbsent(fullOutputRoot);
        fileSystem.CreateDirectory(fullOutputRoot);
        using MemoryStream archiveStream = new(archiveBytes.ToArray());
        using ZipArchive archive = new(archiveStream, ZipArchiveMode.Read);
        foreach (var entry in archive.Entries
                     .OrderBy(static entry => entry.FullName, StringComparer.Ordinal))
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (entry.FullName.Length == 0)
            {
                continue;
            }

            var archivePath = entry.FullName.Replace('\\', '/');
            var isDirectory = archivePath.EndsWith('/');
            var relativePath = isDirectory
                ? archivePath.TrimEnd('/')
                : archivePath;
            if (relativePath.Length == 0 ||
                relativePath.StartsWith('/') ||
                relativePath.Split('/').Any(static part =>
                    part is "" or "." or ".."))
            {
                throw Failure(
                    "The exact Kiota package contains an unsafe archive path.");
            }

            var destination = LocalOperationPaths.ResolveBelow(
                fullOutputRoot,
                relativePath,
                "The Kiota package entry");
            if (isDirectory)
            {
                fileSystem.CreateDirectory(destination);
                continue;
            }

            using var source = entry.Open();
            using MemoryStream content = new();
            await source.CopyToAsync(
                content,
                cancellationToken).ConfigureAwait(false);
            await fileSystem.WriteAllBytesAsync(
                destination,
                content.ToArray(),
                cancellationToken).ConfigureAwait(false);
        }

        var entryPath = LocalOperationPaths.ResolveBelow(
            fullOutputRoot,
            KiotaToolSelection.EntryRelativePath,
            "The Kiota entry assembly");
        if (!fileSystem.FileExists(entryPath))
        {
            throw Failure("The exact Kiota package has no reviewed entry assembly.");
        }

        var entryBytes = await fileSystem.ReadAllBytesAsync(
            entryPath,
            cancellationToken).ConfigureAwait(false);
        if (!string.Equals(
                LocalOperationHashes.Sha256(entryBytes.Span).Value,
                KiotaToolSelection.EntryDigest,
                StringComparison.Ordinal))
        {
            throw Failure(
                "The staged Kiota entry assembly differs from the reviewed bytes.");
        }

        return entryPath;
    }

    private static KiotaGenerationException Failure(string message) =>
        new(
            KiotaGenerationDiagnosticIds.InvalidToolPackage,
            message,
            "/toolPackage");
}
