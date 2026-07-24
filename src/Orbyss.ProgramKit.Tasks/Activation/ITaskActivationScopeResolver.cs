namespace Orbyss.ProgramKit.Tasks.Activation;

/// <summary>
/// Resolves opaque feature/shell activation identities without exposing a
/// provider ABI.
/// </summary>
public interface ITaskActivationScopeResolver
{
    /// <summary>Creates one fresh activation scope for one handler attempt.</summary>
    ValueTask<ITaskActivationScope> CreateScopeAsync(
        TaskActivationRequest request,
        CancellationToken cancellationToken);
}
