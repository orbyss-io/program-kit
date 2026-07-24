using ObservatoryScheduling.Core.Contracts.Scheduling;
using ObservatoryScheduling.Core.Contracts.Time;

namespace ObservatoryScheduling.Core.Contracts.Constraints;

/// <summary>Applies one ordered additive fictional viewing constraint.</summary>
public interface IViewingConstraint
{
    /// <summary>Gets the explicit deterministic ordering value.</summary>
    int Order { get; }

    /// <summary>Returns whether the candidate is acceptable.</summary>
    ValueTask<bool> AcceptsAsync(
        ViewingRequest request,
        ObservatoryWindow candidate,
        CancellationToken cancellationToken);
}
