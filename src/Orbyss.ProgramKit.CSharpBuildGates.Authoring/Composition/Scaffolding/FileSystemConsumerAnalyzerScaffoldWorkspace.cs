using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;

namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Composition.Scaffolding;

/// <summary>
/// Creates same-volume file-system transactions without overwriting an output.
/// </summary>
public sealed class FileSystemConsumerAnalyzerScaffoldWorkspace :
    IConsumerAnalyzerScaffoldWorkspace
{
    /// <inheritdoc />
    public ValueTask<IConsumerAnalyzerScaffoldTransaction> BeginAsync(
        string outputRoot,
        CancellationToken cancellationToken)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(outputRoot);
        cancellationToken.ThrowIfCancellationRequested();

        var resolvedOutput = Path.GetFullPath(outputRoot);
        if (Directory.Exists(resolvedOutput) || File.Exists(resolvedOutput))
        {
            throw new IOException(
                $"Scaffold output already exists and will not be overwritten: {resolvedOutput}");
        }

        var parent = Path.GetDirectoryName(resolvedOutput)
            ?? throw new ArgumentException(
                "The scaffold output must have a parent directory.",
                nameof(outputRoot));
        Directory.CreateDirectory(parent);
        var staging = Path.Combine(
            parent,
            string.Concat(
                ".pkcg-scaffold-",
                Path.GetFileName(resolvedOutput),
                "-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(staging);

        return ValueTask.FromResult<IConsumerAnalyzerScaffoldTransaction>(
            new FileSystemConsumerAnalyzerScaffoldTransaction(
                resolvedOutput,
                staging));
    }
}
