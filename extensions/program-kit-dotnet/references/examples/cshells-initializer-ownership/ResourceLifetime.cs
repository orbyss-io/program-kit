namespace ProgramKit.Examples.CShellsInitializerOwnership;

/// <summary>Counts calls before resource idempotency could conceal duplicate disposal.</summary>
public sealed class ResourceLifetime
{
    /// <summary>Counts actual initializer invocations across asynchronous observations.</summary>
    private int initializations;
    /// <summary>Counts disposal requests even when the underlying resource is idempotent.</summary>
    private int disposals;

    /// <summary>Gets actual initialization invocations.</summary>
    public int Initializations => Volatile.Read(ref initializations);

    /// <summary>Gets actual disposal invocations.</summary>
    public int Disposals => Volatile.Read(ref disposals);

    /// <summary>Records an actual initializer invocation.</summary>
    internal void ObserveInitialization() => Interlocked.Increment(ref initializations);

    /// <summary>Records an actual resource disposal invocation.</summary>
    internal void ObserveDisposal() => Interlocked.Increment(ref disposals);
}
