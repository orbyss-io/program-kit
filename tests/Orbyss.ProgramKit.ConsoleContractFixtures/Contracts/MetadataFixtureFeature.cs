using CShells.Features;
using Microsoft.Extensions.DependencyInjection;

namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class MetadataFixtureFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        ArgumentNullException.ThrowIfNull(services);
        services.AddScoped<IMetadataFixtureHandler, MetadataFixtureHandler>();
    }
}
