using Orbyss.ProgramKit.UnitTests.Tasks.Core.Schedules.TestSupport;

namespace Orbyss.ProgramKit.UnitTests.Tasks.Core.Schedules;

[TestClass]
public sealed class TypedScheduleContractTests
{
    [TestMethod]
    public async Task OccurrenceCalculatorConsumesOnlyTypedControlledTimeInput()
    {
        TestIntervalOccurrenceCalculator sut = new();
        var request =
            new TaskOccurrenceCalculationRequest<TestIntervalDescriptor>(
                TasksCoreTestValues.Schedule(),
                new TestIntervalDescriptor(TimeSpan.FromMinutes(5)),
                TasksCoreTestValues.Instant.AddHours(-1),
                TasksCoreTestValues.Instant.AddMinutes(-10),
                TasksCoreTestValues.Instant,
                null,
                10);

        var result = await sut.CalculateAsync(request, CancellationToken.None);

        Assert.ContainsSingle(result.Occurrences);
        Assert.AreEqual(
            TasksCoreTestValues.Instant.AddMinutes(-5),
            result.Occurrences[0].ScheduledFor);
    }
}
