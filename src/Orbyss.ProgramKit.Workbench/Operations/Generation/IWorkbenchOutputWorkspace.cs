namespace Orbyss.ProgramKit.Workbench.Operations.Generation;

/// <summary>Creates explicit transactional output scopes.</summary>
public interface IWorkbenchOutputWorkspace
{
    /// <summary>Begins one transaction below the declared write root.</summary>
    ValueTask<IWorkbenchOutputTransaction> BeginAsync(
        string writeRoot,
        GenerationCollisionPolicy collisionPolicy,
        CancellationToken cancellationToken);
}
