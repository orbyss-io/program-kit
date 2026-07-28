using CShells.Features;
using Microsoft.Extensions.DependencyInjection;

namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class JTestFixtureFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        ArgumentNullException.ThrowIfNull(services);
        services.AddScoped<IJTestRunHandler, JTestRunHandler>();
        services.AddScoped<IJTestValidateHandler, JTestValidateHandler>();
        services.AddScoped<IJTestDescribeHandler, JTestDescribeHandler>();
        services.AddScoped<IJTestRunValidator, JTestRunValidator>();
    }
}
