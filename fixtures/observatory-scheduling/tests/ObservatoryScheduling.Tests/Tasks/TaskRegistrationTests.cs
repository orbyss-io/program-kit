using Microsoft.Extensions.DependencyInjection;
using Orbyss.ProgramKit.Tasks.Activation;
using Orbyss.ProgramKit.Tasks.Registration;
using Orbyss.ProgramKit.Tasks.Schedules.Cronos.Calculation;
using Orbyss.ProgramKit.Tasks.Schedules.Cronos.Descriptors;
using Orbyss.ProgramKit.Tasks.Core.Schedules;
using ObservatoryScheduling.Core.Tasks;
using ObservatoryScheduling.Scheduling.FirstAvailable.Composition;
using ObservatoryScheduling.Scheduling.FirstAvailable.Features;
using ObservatoryScheduling.Tests.Configuration;

namespace ObservatoryScheduling.Tests.Tasks;

public sealed class TaskRegistrationTests
{
    [Test]
    public void FeatureRegistersTheCompleteTaskAndScheduleClosure()
    {
        IServiceCollection services = new ServiceCollection();
        var feature = new FirstAvailableFeature();

        feature.ConfigureServices(services);

        var catalog = services
            .Single(static descriptor =>
                descriptor.ServiceType == typeof(ITaskRegistrationCatalog))
            .ImplementationInstance as ITaskRegistrationCatalog
            ?? throw new InvalidOperationException(
                "Task registration catalog was not registered.");
        var registrations = catalog.Export();
        FixtureAssert.HasCount(1, registrations.Definitions);
        FixtureAssert.HasCount(1, registrations.Handlers);
        FixtureAssert.HasCount(1, registrations.Bindings);
        FixtureAssert.HasCount(1, registrations.Features);
        FixtureAssert.HasCount(1, registrations.Middleware);
        FixtureAssert.HasCount(1, registrations.Schedules);
        FixtureAssert.HasCount(1, registrations.Calculators);
        FixtureAssert.HasCount(1, registrations.OccurrenceRequestFactories);
        FixtureAssert.HasCount(1, registrations.MisfirePolicies);
        FixtureAssert.HasCount(1, registrations.OverlapPolicies);
    }

    [Test]
    public void HostCompositionRegistersTheActivationScopeResolver()
    {
        IServiceCollection services = new ServiceCollection();
        services.AddFirstAvailableTaskActivation("observatory-worker");

        FixtureAssert.HasCount(
            1,
            services.Where(static descriptor =>
                descriptor.ServiceType ==
                typeof(ITaskActivationScopeResolver)).ToArray());
    }

    [Test]
    public async Task CronosScheduleUsesControlledTimeAndCreatesANormalRequest()
    {
        var calculator = new CronosOccurrenceCalculator();
        var evaluation = new DateTimeOffset(
            2026,
            1,
            1,
            20,
            0,
            0,
            TimeSpan.Zero);
        var request =
            new TaskOccurrenceCalculationRequest<CronosScheduleDescriptor>(
            FirstAvailableTaskContracts.Schedule,
            FirstAvailableTaskContracts.ScheduleDescriptor,
            evaluation.AddDays(-1),
            evaluation.AddMinutes(-1),
            evaluation,
            null,
            1);

        var calculation = await calculator.CalculateAsync(
            request,
            CancellationToken.None);
        FixtureAssert.HasCount(1, calculation.Occurrences);
        var occurrence = calculation.Occurrences[0];
        var factory = new ScheduledViewingRequestFactory();
        var normalRequest = await factory.CreateAsync(
            occurrence,
            CancellationToken.None);

        FixtureAssert.AreEqual(
            FirstAvailableTaskContracts.Definition.Revision,
            normalRequest.DefinitionRevision);
        FixtureAssert.AreEqual(
            occurrence.Revision,
            normalRequest.OccurrenceRevision);
    }
}
