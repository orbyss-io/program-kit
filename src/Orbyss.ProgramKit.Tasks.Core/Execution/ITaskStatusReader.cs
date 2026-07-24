using Orbyss.ProgramKit.Tasks.Core.Instances;

namespace Orbyss.ProgramKit.Tasks.Core.Execution;

/// <summary>Reads immutable lifecycle status observations.</summary>
public interface ITaskStatusReader
{
    /// <summary>Reads status for an exact accepted instance revision.</summary>
    ValueTask<TaskInstanceStatus?> ReadAsync(
        ArtifactReference instanceRevision,
        CancellationToken cancellationToken);
}
