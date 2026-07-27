using Orbyss.ProgramKit.Modularity.Contributions;
using Orbyss.ProgramKit.Modularity.Middleware;
using ObservatoryScheduling.Constraints.DarknessWindow.Features;
using ObservatoryScheduling.Core.Contracts.Constraints;
using ObservatoryScheduling.Core.Contracts.Scheduling;
using ObservatoryScheduling.Core.Contracts.Visibility;
using ObservatoryScheduling.Scheduling.FirstAvailable.Features;
using ObservatoryScheduling.Tests.Configuration;
using ObservatoryScheduling.Visibility.Fixed.Features;

namespace ObservatoryScheduling.Tests.Features;

public sealed class SchedulingBehaviorTests
{
    [Test]
    public async Task ImmediateSchedulingUsesMiddlewareConstraintAndContribution()
    {
        IVisibilityForecast visibility = new StaticVisibilityForecast();
        IViewingConstraint constraint = new DarknessWindowConstraint();
        IProgramKitMiddlewarePipeline<ViewingRequest, ViewingSession?> pipeline =
            ObservatoryTestComposition.CreatePipeline();
        var recorder = new ViewingScheduledRecorder();
        IDomainContributionPublisher publisher =
            ObservatoryTestComposition.CreatePublisher(recorder);
        var scheduler = new FirstAvailableScheduler(
            visibility,
            [constraint],
            pipeline,
            publisher);
        var request = new ViewingRequest(
            "M42",
            new DateTimeOffset(2026, 1, 1, 20, 0, 0, TimeSpan.Zero),
            new DateTimeOffset(2026, 1, 2, 4, 0, 0, TimeSpan.Zero),
            TimeSpan.FromMinutes(45));

        var session = await scheduler.ScheduleAsync(
            request,
            CancellationToken.None);

        var scheduledSession = session ??
            throw new InvalidOperationException(
                "The valid fixture request was not scheduled.");
        FixtureAssert.AreEqual("M42", scheduledSession.Target);
        FixtureAssert.AreEqual(scheduledSession, recorder.Last?.Session);
    }

    [Test]
    public async Task MiddlewareRejectsAnInvalidImmediateRequest()
    {
        IVisibilityForecast visibility = new StaticVisibilityForecast();
        IViewingConstraint constraint = new DarknessWindowConstraint();
        var recorder = new ViewingScheduledRecorder();
        var scheduler = new FirstAvailableScheduler(
            visibility,
            [constraint],
            ObservatoryTestComposition.CreatePipeline(),
            ObservatoryTestComposition.CreatePublisher(recorder));
        var invalid = new ViewingRequest(
            "",
            DateTimeOffset.UnixEpoch,
            DateTimeOffset.UnixEpoch,
            TimeSpan.Zero);

        await FixtureAssert.ThrowsExactlyAsync<ArgumentException>(
            async () =>
                _ = await scheduler.ScheduleAsync(
                    invalid,
                    CancellationToken.None));
    }
}
