using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.Workbench.Composition.Generation;

internal sealed class FileSystemWorkbenchOutputTransaction :
    IWorkbenchOutputTransaction
{
    private readonly string outputRoot;
    private readonly string stagingRoot;
    private bool completed;
    private bool published;

    internal FileSystemWorkbenchOutputTransaction(
        string outputRoot,
        string stagingRoot)
    {
        this.outputRoot = outputRoot;
        this.stagingRoot = stagingRoot;
    }

    public async ValueTask StageAsync(
        GeneratedOutput output,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(output);
        ThrowIfCompleted();
        cancellationToken.ThrowIfCancellationRequested();

        var outputPath = ResolveStagingPath(output.RelativePath);
        var parent = Path.GetDirectoryName(outputPath) ??
            throw new IOException("A staged output path has no parent directory.");
        Directory.CreateDirectory(parent);
        await using var stream = new FileStream(
            outputPath,
            FileMode.CreateNew,
            FileAccess.Write,
            FileShare.None,
            bufferSize: 4096,
            FileOptions.Asynchronous | FileOptions.SequentialScan);
        await stream.WriteAsync(output.Content, cancellationToken).ConfigureAwait(false);
        await stream.FlushAsync(cancellationToken).ConfigureAwait(false);
    }

    public ValueTask CommitAsync(CancellationToken cancellationToken)
    {
        ThrowIfCompleted();
        cancellationToken.ThrowIfCancellationRequested();
        if (Directory.Exists(outputRoot) || File.Exists(outputRoot))
        {
            throw new IOException("The declared output root already exists.");
        }

        Directory.Move(stagingRoot, outputRoot);
        published = true;
        completed = true;
        return ValueTask.CompletedTask;
    }

    public ValueTask RollbackAsync(CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        if (published || completed)
        {
            return ValueTask.CompletedTask;
        }

        if (Directory.Exists(stagingRoot))
        {
            Directory.Delete(stagingRoot, recursive: true);
        }

        completed = true;
        return ValueTask.CompletedTask;
    }

    private string ResolveStagingPath(string relativePath)
    {
        if (string.IsNullOrWhiteSpace(relativePath) ||
            Path.IsPathRooted(relativePath) ||
            relativePath.Contains('\\'))
        {
            throw new IOException("A staged output path is not a normalized relative path.");
        }

        var segments = relativePath.Split('/');
        if (segments.Any(static segment =>
                segment.Length == 0 ||
                segment == "." ||
                segment == ".."))
        {
            throw new IOException("A staged output path is not a normalized relative path.");
        }

        var combined = Path.Combine(
            [stagingRoot, .. segments]);
        var resolved = Path.GetFullPath(combined);
        var prefix = string.Concat(
            stagingRoot.TrimEnd(Path.DirectorySeparatorChar),
            Path.DirectorySeparatorChar);
        var comparison = OperatingSystem.IsWindows()
            ? StringComparison.OrdinalIgnoreCase
            : StringComparison.Ordinal;
        if (!resolved.StartsWith(prefix, comparison))
        {
            throw new IOException("A staged output path escapes its private root.");
        }

        return resolved;
    }

    private void ThrowIfCompleted()
    {
        if (completed)
        {
            throw new InvalidOperationException(
                "The output transaction has already completed.");
        }
    }
}
