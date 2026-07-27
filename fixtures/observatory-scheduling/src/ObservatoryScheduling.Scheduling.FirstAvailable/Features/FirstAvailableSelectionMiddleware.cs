using Orbyss.ProgramKit.Modularity.Middleware;
using ObservatoryScheduling.Core.Contracts.Scheduling;

namespace ObservatoryScheduling.Scheduling.FirstAvailable.Features;

/// <summary>Validates the explicit scheduling interval before selection behavior runs.</summary>
public sealed class FirstAvailableSelectionMiddleware :
    IProgramKitMiddleware<ViewingRequest, ViewingSession?>
{
    /// <inheritdoc />
    public ValueTask<ViewingSession?> InvokeAsync(
        ViewingRequest context,
        ProgramKitMiddlewareNext<ViewingRequest, ViewingSession?> continuation,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(context);
        ArgumentNullException.ThrowIfNull(continuation);
        cancellationToken.ThrowIfCancellationRequested();
        if (string.IsNullOrWhiteSpace(context.Target) ||
            context.EarliestStart >= context.LatestEnd ||
            context.RequiredDuration <= TimeSpan.Zero)
        {
            throw new ArgumentException(
                "A viewing request requires a target, ordered interval, and positive duration.",
                nameof(context));
        }

        return continuation(context);
    }
}
