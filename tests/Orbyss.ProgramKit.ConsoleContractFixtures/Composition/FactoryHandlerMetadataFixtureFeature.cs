using CShells.Features;
using Microsoft.Extensions.DependencyInjection;
using Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

namespace Orbyss.ProgramKit.ConsoleContractFixtures.Composition;

public sealed class FactoryHandlerMetadataFixtureFeature : IShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        ArgumentNullException.ThrowIfNull(services);
        services.AddScoped<IMetadataFixtureHandler>(
            static _ => new MetadataFixtureHandler());
    }
}
