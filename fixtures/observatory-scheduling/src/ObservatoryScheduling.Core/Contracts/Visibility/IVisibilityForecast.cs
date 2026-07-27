using ObservatoryScheduling.Core.Contracts.Scheduling;
using ObservatoryScheduling.Core.Contracts.Time;

namespace ObservatoryScheduling.Core.Contracts.Visibility;

/// <summary>Supplies explicitly selected fictional visibility windows.</summary>
public interface IVisibilityForecast
{
    /// <summary>Gets candidate windows for one request.</summary>
    ValueTask<IReadOnlyList<ObservatoryWindow>> GetWindowsAsync(
        ViewingRequest request,
        CancellationToken cancellationToken);
}
