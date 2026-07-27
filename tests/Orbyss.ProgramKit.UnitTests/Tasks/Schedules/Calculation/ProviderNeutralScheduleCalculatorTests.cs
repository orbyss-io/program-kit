using Orbyss.ProgramKit.Tasks.Core.Execution;
using Orbyss.ProgramKit.Tasks.Core.Schedules;
using Orbyss.ProgramKit.Tasks.Schedules.Calculation;
using Orbyss.ProgramKit.Tasks.Schedules.Descriptors;

namespace Orbyss.ProgramKit.UnitTests.Tasks.Schedules.Calculation;

[TestClass]
public sealed class ProviderNeutralScheduleCalculatorTests
{
    [TestMethod]
    public async Task DelayOnceUsesTheExplicitReferenceInstant()
    {
        DelayOnceOccurrenceCalculator sut =
            new DelayOnceOccurrenceCalculator();
        var reference = TasksCoreTestValues.Instant.AddHours(-1);
        var request = new TaskOccurrenceCalculationRequest<
            DelayOnceScheduleDescriptor>(
            TasksCoreTestValues.Schedule(),
            new DelayOnceScheduleDescriptor(TimeSpan.FromMinutes(30)),
            reference,
            reference,
            TasksCoreTestValues.Instant,
            null,
            10);

        var result = await sut.CalculateAsync(request, CancellationToken.None);

        Assert.ContainsSingle(result.Occurrences);
        Assert.AreEqual(
            reference.AddMinutes(30),
            result.Occurrences[0].ScheduledFor);
    }

    [TestMethod]
    public async Task FixedDelayUsesThePreviousTerminalCompletionInstant()
    {
        FixedDelayOccurrenceCalculator sut =
            new FixedDelayOccurrenceCalculator();
        var completion = TasksCoreTestValues.Instant.AddMinutes(-20);
        var request = new TaskOccurrenceCalculationRequest<
            FixedDelayScheduleDescriptor>(
            TasksCoreTestValues.Schedule(),
            new FixedDelayScheduleDescriptor(TimeSpan.FromMinutes(10)),
            TasksCoreTestValues.Instant.AddHours(-2),
            TasksCoreTestValues.Instant.AddMinutes(-15),
            TasksCoreTestValues.Instant,
            completion,
            10);

        var result = await sut.CalculateAsync(request, CancellationToken.None);

        Assert.ContainsSingle(result.Occurrences);
        Assert.AreEqual(
            completion.AddMinutes(10),
            result.Occurrences[0].ScheduledFor);
    }

    [TestMethod]
    public async Task AnchoredIntervalIsCursorExclusiveAndBounded()
    {
        AnchoredFixedIntervalOccurrenceCalculator sut =
            new AnchoredFixedIntervalOccurrenceCalculator();
        var anchor = TasksCoreTestValues.Instant.AddHours(-1);
        var request = new TaskOccurrenceCalculationRequest<
            AnchoredFixedIntervalScheduleDescriptor>(
            TasksCoreTestValues.Schedule(),
            new AnchoredFixedIntervalScheduleDescriptor(
                anchor,
                TimeSpan.FromMinutes(10)),
            anchor,
            anchor.AddMinutes(20),
            TasksCoreTestValues.Instant,
            null,
            2);

        var result = await sut.CalculateAsync(request, CancellationToken.None);

        Assert.HasCount(2, result.Occurrences);
        Assert.AreEqual(
            anchor.AddMinutes(30),
            result.Occurrences[0].ScheduledFor);
        Assert.AreEqual(
            anchor.AddMinutes(40),
            result.Occurrences[1].ScheduledFor);
    }

    [TestMethod]
    public async Task AnchoredIntervalRejectsCalendarFreeZeroPeriod()
    {
        AnchoredFixedIntervalOccurrenceCalculator sut =
            new AnchoredFixedIntervalOccurrenceCalculator();
        var request = new TaskOccurrenceCalculationRequest<
            AnchoredFixedIntervalScheduleDescriptor>(
            TasksCoreTestValues.Schedule(),
            new AnchoredFixedIntervalScheduleDescriptor(
                TasksCoreTestValues.Instant,
                TimeSpan.Zero),
            TasksCoreTestValues.Instant,
            TasksCoreTestValues.Instant,
            TasksCoreTestValues.Instant,
            null,
            1);

        await Assert.ThrowsExactlyAsync<ArgumentOutOfRangeException>(
            async () =>
                await sut.CalculateAsync(
                    request,
                    CancellationToken.None));
    }
}
