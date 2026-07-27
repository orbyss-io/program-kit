using Orbyss.ProgramKit.Modularity.Contributions;
using Orbyss.ProgramKit.Modularity.Middleware;
using ObservatoryScheduling.Core.Contracts.Contributions;
using ObservatoryScheduling.Core.Contracts.Constraints;
using ObservatoryScheduling.Core.Contracts.Scheduling;
using ObservatoryScheduling.Core.Contracts.Visibility;

namespace ObservatoryScheduling.Scheduling.FirstAvailable.Features;

/// <summary>Selects the first acceptable window through injected domain services.</summary>
public sealed class FirstAvailableScheduler : IFirstAvailableScheduler
{
    private readonly IVisibilityForecast visibility;
    private readonly IEnumerable<IViewingConstraint> constraints;
    private readonly IProgramKitMiddlewarePipeline<ViewingRequest, ViewingSession?> pipeline;
    private readonly IDomainContributionPublisher publisher;

    /// <summary>Initializes scheduling behavior from explicit injected contracts.</summary>
    public FirstAvailableScheduler(
        IVisibilityForecast visibility,
        IEnumerable<IViewingConstraint> constraints,
        IProgramKitMiddlewarePipeline<ViewingRequest, ViewingSession?> pipeline,
        IDomainContributionPublisher publisher)
    {
        this.visibility = visibility ??
            throw new ArgumentNullException(nameof(visibility));
        ArgumentNullException.ThrowIfNull(constraints);
        this.constraints = constraints;
        this.pipeline = pipeline ??
            throw new ArgumentNullException(nameof(pipeline));
        this.publisher = publisher ??
            throw new ArgumentNullException(nameof(publisher));
    }

    /// <inheritdoc />
    public ValueTask<ViewingSession?> ScheduleAsync(
        ViewingRequest request,
        CancellationToken cancellationToken) =>
        pipeline.ExecuteAsync(
            request,
            SelectAsync,
            cancellationToken);

    private async ValueTask<ViewingSession?> SelectAsync(
        ViewingRequest request,
        CancellationToken cancellationToken)
    {
        var windows = await visibility.GetWindowsAsync(
            request,
            cancellationToken).ConfigureAwait(false);
        foreach (var window in windows.OrderBy(static window => window.StartsAt))
        {
            var accepted = true;
            foreach (var constraint in constraints.OrderBy(
                         static constraint => constraint.Order))
            {
                if (!await constraint.AcceptsAsync(
                        request,
                        window,
                        cancellationToken).ConfigureAwait(false))
                {
                    accepted = false;
                    break;
                }
            }

            if (!accepted)
            {
                continue;
            }

            var session = new ViewingSession(request.Target, window);
            _ = await publisher.PublishAsync(
                new ViewingScheduled(session),
                DomainContributionPublicationPolicy.FailFast,
                cancellationToken).ConfigureAwait(false);
            return session;
        }

        return null;
    }
}
