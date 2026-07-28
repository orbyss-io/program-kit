using CShells.Features;
using Microsoft.Extensions.DependencyInjection;

namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class DuplicateHandlerMetadataFixtureFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        ArgumentNullException.ThrowIfNull(services);
        services.AddScoped<IMetadataFixtureHandler, MetadataFixtureHandler>();
        services.AddScoped<IMetadataFixtureHandler, MetadataFixtureHandler>();
    }
}
