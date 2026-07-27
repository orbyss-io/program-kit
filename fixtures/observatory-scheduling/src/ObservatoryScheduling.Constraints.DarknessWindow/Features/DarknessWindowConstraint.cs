using ObservatoryScheduling.Core.Contracts.Constraints;
using ObservatoryScheduling.Core.Contracts.Scheduling;
using ObservatoryScheduling.Core.Contracts.Time;

namespace ObservatoryScheduling.Constraints.DarknessWindow.Features;

/// <summary>Accepts only controlled fictional UTC night-time windows.</summary>
public sealed class DarknessWindowConstraint : IViewingConstraint
{
    /// <inheritdoc />
    public int Order => 100;

    /// <inheritdoc />
    public ValueTask<bool> AcceptsAsync(
        ViewingRequest request,
        ObservatoryWindow candidate,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        ArgumentNullException.ThrowIfNull(candidate);
        cancellationToken.ThrowIfCancellationRequested();
        var duration = candidate.EndsAt - candidate.StartsAt;
        var hour = candidate.StartsAt.UtcDateTime.Hour;
        var isDark = hour >= 18 || hour < 6;
        var accepted =
            candidate.StartsAt >= request.EarliestStart &&
            candidate.EndsAt <= request.LatestEnd &&
            duration >= request.RequiredDuration &&
            isDark;
        return ValueTask.FromResult(accepted);
    }
}
