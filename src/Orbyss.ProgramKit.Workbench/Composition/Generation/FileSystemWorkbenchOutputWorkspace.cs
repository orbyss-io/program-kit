using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.Workbench.Composition.Generation;

/// <summary>
/// Creates private sibling directories that are published through one
/// same-volume directory rename.
/// </summary>
public sealed class FileSystemWorkbenchOutputWorkspace :
    IWorkbenchOutputWorkspace
{
    /// <inheritdoc />
    public ValueTask<IWorkbenchOutputTransaction> BeginAsync(
        string writeRoot,
        GenerationCollisionPolicy collisionPolicy,
        CancellationToken cancellationToken)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(writeRoot);
        cancellationToken.ThrowIfCancellationRequested();
        if (collisionPolicy != GenerationCollisionPolicy.Fail)
        {
            throw new ArgumentOutOfRangeException(
                nameof(collisionPolicy),
                collisionPolicy,
                "The filesystem workspace supports only fail-on-existing-root publication.");
        }

        var outputRoot = Path.GetFullPath(writeRoot);
        var parent = Directory.GetParent(outputRoot)?.FullName ??
            throw new ArgumentException(
                "The declared output root must have a parent directory.",
                nameof(writeRoot));
        Directory.CreateDirectory(parent);
        var stagingRoot = Path.Combine(
            parent,
            string.Concat(
                ".",
                Path.GetFileName(outputRoot),
                ".program-kit-stage-",
                Guid.NewGuid().ToString("N")));
        Directory.CreateDirectory(stagingRoot);

        IWorkbenchOutputTransaction transaction =
            new FileSystemWorkbenchOutputTransaction(outputRoot, stagingRoot);
        return ValueTask.FromResult(transaction);
    }
}
