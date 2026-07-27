using ObservatoryScheduling.Core.Contracts.Scheduling;
using ObservatoryScheduling.Core.Contracts.Time;
using ObservatoryScheduling.Core.Contracts.Visibility;

namespace ObservatoryScheduling.Visibility.Fixed.Features;

/// <summary>Controlled deterministic visibility data for the fictional proof.</summary>
public sealed class StaticVisibilityForecast : IVisibilityForecast
{
    /// <inheritdoc />
    public ValueTask<IReadOnlyList<ObservatoryWindow>> GetWindowsAsync(
        ViewingRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        cancellationToken.ThrowIfCancellationRequested();
        IReadOnlyList<ObservatoryWindow> windows =
        [
            new(
                request.EarliestStart,
                request.EarliestStart.AddHours(1)),
            new(
                request.EarliestStart.AddHours(2),
                request.EarliestStart.AddHours(4)),
        ];
        return ValueTask.FromResult(windows);
    }
}
