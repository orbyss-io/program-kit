namespace ProgramKit.Examples.CShellsInitializerOwnership;

/// <summary>A fictional memory resource for the executable example, not a product storage provider.</summary>
public sealed class SyntheticResourceOwner : IAsyncDisposable
{
    /// <summary>Coordinates only the finite synthetic admission experiment.</summary>
    private readonly SyntheticResourceObservation observation;
    /// <summary>Retains the resource whose usability and teardown are independently exercised.</summary>
    private readonly MemoryStream resource;
    /// <summary>Records completion of admission before resource use becomes available.</summary>
    private bool admitted;

    /// <summary>Acquires an owned resource and reports its lifetime to the synthetic fixture.</summary>
    public SyntheticResourceOwner(SyntheticResourceObservation observation)
    {
        this.observation = observation;
        byte[] contents = [42];
        resource = new MemoryStream(contents, writable: false);
        Lifetime = new ResourceLifetime();
        observation.Lifetimes.Add(Lifetime);
    }

    /// <summary>Exposes synthetic instrumentation; product owners retain their real resource contract.</summary>
    public ResourceLifetime Lifetime { get; }

    /// <summary>Exercises awaited admission, original cancellation and partial-startup failure.</summary>
    public async Task AdmitAsync(CancellationToken cancellationToken)
    {
        Lifetime.ObserveInitialization();
        observation.AdmissionEntered.TrySetResult();
        await observation.AdmissionContinuation.WaitAsync(cancellationToken);
        cancellationToken.ThrowIfCancellationRequested();
        if (observation.Failure is { } failure)
            throw failure;
        admitted = true;
    }

    /// <summary>Proves a real resource remains usable only after admission and before disposal.</summary>
    public int Use()
    {
        ObjectDisposedException.ThrowIf(!resource.CanRead, this);
        if (!admitted)
            throw new InvalidOperationException("Resource admission has not succeeded.");
        return resource.ToArray()[0];
    }

    /// <inheritdoc />
    public ValueTask DisposeAsync()
    {
        Lifetime.ObserveDisposal();
        return resource.DisposeAsync();
    }
}
