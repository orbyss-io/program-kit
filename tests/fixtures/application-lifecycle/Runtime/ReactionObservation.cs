namespace ProgramKit.Examples.Events;
/// <summary>Fixture-owned outcome observation, not a production audit or durable reaction.</summary>
public sealed class ReactionObservation
{
    public List<string> Events { get; } = [];
    public TaskCompletionSource HandlerEntered { get; } = new(TaskCreationOptions.RunContinuationsAsynchronously);
}
