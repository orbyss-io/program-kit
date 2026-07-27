namespace Orbyss.ProgramKit.Tasks.Activation;

/// <summary>Fresh exact service scope for one task attempt.</summary>
public interface ITaskActivationScope : IAsyncDisposable
{
    /// <summary>Gets the exact scoped service provider.</summary>
    IServiceProvider Services { get; }
}
