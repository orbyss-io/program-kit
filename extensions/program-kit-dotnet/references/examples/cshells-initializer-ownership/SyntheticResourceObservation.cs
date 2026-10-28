namespace ProgramKit.Examples.CShellsInitializerOwnership;

/// <summary>Finite diagnostic input/output used only by this fictional executable example.</summary>
public sealed class SyntheticResourceObservation
{
    /// <summary>Records independently constructed generation resources.</summary>
    public List<ResourceLifetime> Lifetimes { get; } = [];

    /// <summary>Allows the fixture to observe when initialization actually starts.</summary>
    public TaskCompletionSource AdmissionEntered { get; set; } =
        new(TaskCreationOptions.RunContinuationsAsynchronously);

    /// <summary>Allows the fixture to hold an actual in-progress initializer.</summary>
    public Task AdmissionContinuation { get; set; } = Task.CompletedTask;

    /// <summary>Models rejection after resource acquisition without suppressing the failure.</summary>
    public Exception? Failure { get; set; }
}
