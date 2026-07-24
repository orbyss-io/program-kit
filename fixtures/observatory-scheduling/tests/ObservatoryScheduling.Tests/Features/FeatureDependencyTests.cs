using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.Extensions.DependencyInjection;
using Orbyss.ProgramKit.Tasks.Registration;
using ObservatoryScheduling.Constraints.DarknessWindow.Features;
using ObservatoryScheduling.Core.Contracts.Scheduling;
using ObservatoryScheduling.Scheduling.Api.Features;
using ObservatoryScheduling.Scheduling.FirstAvailable.Features;
using ObservatoryScheduling.Tests.Configuration;
using ObservatoryScheduling.Visibility.Fixed.Features;

namespace ObservatoryScheduling.Tests.Features;

public sealed class FeatureDependencyTests
{
    [Test]
    public void ConcreteFeaturesImplementTheDirectCshellsContracts()
    {
        FixtureAssert.IsType<IShellFeature>(new StaticVisibilityFeature());
        FixtureAssert.IsType<IShellFeature>(new DarknessWindowFeature());
        FixtureAssert.IsType<IShellFeature>(new FirstAvailableFeature());
        FixtureAssert.IsType<IWebShellFeature>(new SchedulingApiFeature());
    }

    [Test]
    public void ApiFeatureContributesNoTaskRegistrations()
    {
        IServiceCollection services = new ServiceCollection();
        var feature = new SchedulingApiFeature();

        feature.ConfigureServices(services);

        FixtureAssert.IsFalse(services.Any(static descriptor =>
            descriptor.ServiceType == typeof(ITaskRegistrationCatalog)));
    }

    [Test]
    public void CoreRemainsCshellsFreeAndApiRemainsTasksFree()
    {
        var coreReferences = typeof(ViewingRequest)
            .Assembly
            .GetReferencedAssemblies()
            .Select(static reference => reference.Name)
            .ToHashSet(StringComparer.Ordinal);
        var apiReferences = typeof(SchedulingApiFeature)
            .Assembly
            .GetReferencedAssemblies()
            .Select(static reference => reference.Name)
            .ToHashSet(StringComparer.Ordinal);

        FixtureAssert.IsFalse(coreReferences.Any(static name =>
            name?.StartsWith("CShells", StringComparison.Ordinal) == true));
        FixtureAssert.IsFalse(apiReferences.Any(static name =>
            name?.StartsWith(
                "Orbyss.ProgramKit.Tasks",
                StringComparison.Ordinal) == true));
    }
}
