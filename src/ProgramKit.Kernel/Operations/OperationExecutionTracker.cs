using System.Threading;
using Orbyss.ProgramKit.Contracts.Operations;

namespace Orbyss.ProgramKit.Kernel.Operations;

public sealed record OperationExecutionSnapshot(PublicCommand Command, OperationPhase Phase, EffectState Effect);

public static class OperationExecutionTracker
{
    private static readonly AsyncLocal<OperationExecutionSnapshot?> Current = new();

    public static void Start(PublicCommand command) => Current.Value = new OperationExecutionSnapshot(command, OperationPhase.Request, EffectState.None);

    public static void Advance(OperationPhase phase, EffectState effect)
    {
        OperationExecutionSnapshot current = Current.Value ?? new OperationExecutionSnapshot(PublicCommand.Help, OperationPhase.Request, EffectState.None);
        OperationPhase furthest = phase > current.Phase ? phase : current.Phase;
        EffectState proven = Stronger(current.Effect, effect);
        Current.Value = current with { Phase = furthest, Effect = proven };
    }

    public static OperationExecutionSnapshot Snapshot(PublicCommand command) =>
        Current.Value is { } current && current.Command == command
            ? current
            : new OperationExecutionSnapshot(command, OperationPhase.Request, EffectState.None);

    public static void Complete(OperationResult result) => Current.Value = new OperationExecutionSnapshot(result.Command, result.FurthestPhase, result.EffectState);

    private static EffectState Stronger(EffectState current, EffectState next)
    {
        if (current == EffectState.Indeterminate || next == EffectState.Indeterminate)
        {
            return EffectState.Indeterminate;
        }

        return next > current ? next : current;
    }
}
