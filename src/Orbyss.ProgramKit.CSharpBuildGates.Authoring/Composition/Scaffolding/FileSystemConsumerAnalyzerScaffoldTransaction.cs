using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;

namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Composition.Scaffolding;

internal sealed class FileSystemConsumerAnalyzerScaffoldTransaction(
    string outputRoot,
    string stagingRoot) : IConsumerAnalyzerScaffoldTransaction
{
    private bool committed;
    private bool rolledBack;

    public async ValueTask WriteAsync(
        string relativePath,
        ReadOnlyMemory<byte> content,
        CancellationToken cancellationToken)
    {
        EnsureActive();
        var normalized = relativePath.Replace('\\', '/');
        if (Path.IsPathRooted(relativePath) ||
            normalized.Split('/').Any(segment =>
                segment.Length == 0 ||
                string.Equals(segment, ".", StringComparison.Ordinal) ||
                string.Equals(segment, "..", StringComparison.Ordinal)))
        {
            throw new IOException(
                $"Refusing scaffold path outside the transaction: {relativePath}");
        }

        var target = Path.GetFullPath(Path.Combine(stagingRoot, relativePath));
        var boundary = string.Concat(
            Path.GetFullPath(stagingRoot).TrimEnd(Path.DirectorySeparatorChar),
            Path.DirectorySeparatorChar);
        if (!target.StartsWith(
                boundary,
                StringComparison.OrdinalIgnoreCase))
        {
            throw new IOException(
                $"Refusing scaffold path outside the transaction: {relativePath}");
        }

        if (File.Exists(target) || Directory.Exists(target))
        {
            throw new IOException(
                $"Scaffold output collides with an existing staged path: {relativePath}");
        }

        var directory = Path.GetDirectoryName(target)
            ?? throw new IOException(
                $"Could not resolve the scaffold directory for {relativePath}.");
        Directory.CreateDirectory(directory);
        await File.WriteAllBytesAsync(
                target,
                content.ToArray(),
                cancellationToken)
            .ConfigureAwait(false);
    }

    public ValueTask CommitAsync(CancellationToken cancellationToken)
    {
        EnsureActive();
        cancellationToken.ThrowIfCancellationRequested();
        if (Directory.Exists(outputRoot) || File.Exists(outputRoot))
        {
            throw new IOException(
                $"Scaffold output appeared during the transaction and will not be overwritten: {outputRoot}");
        }

        Directory.Move(stagingRoot, outputRoot);
        committed = true;
        return ValueTask.CompletedTask;
    }

    public ValueTask RollbackAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (committed || rolledBack)
        {
            return ValueTask.CompletedTask;
        }

        if (Directory.Exists(stagingRoot))
        {
            Directory.Delete(stagingRoot, recursive: true);
        }

        rolledBack = true;
        return ValueTask.CompletedTask;
    }

    public async ValueTask DisposeAsync()
    {
        if (!committed && !rolledBack)
        {
            await RollbackAsync(CancellationToken.None).ConfigureAwait(false);
        }
    }

    private void EnsureActive()
    {
        if (committed || rolledBack)
        {
            throw new InvalidOperationException(
                "The scaffold transaction is no longer active.");
        }
    }
}
