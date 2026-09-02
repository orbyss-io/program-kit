namespace ProgramKit.Host.Shells;

/// <summary>Tracks whether the startup eager-activation pass has completed.</summary>
internal sealed class EagerShellActivationState
{
    /// <summary>The completion flag written after every configured shell has been activated.</summary>
    private volatile bool _complete;

    /// <summary>Gets whether startup eager activation has completed.</summary>
    public bool IsComplete => _complete;

    /// <summary>Marks the startup eager-activation pass complete.</summary>
    public void Complete() => _complete = true;
}
