using Microsoft.Extensions.DependencyInjection;

namespace Orbyss.ProgramKit.ConsoleContractFixtures.Contracts;

public sealed class ThrowingMetadataFixtureFeature : CShells.Features.IShellFeature
{
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddScoped<
            IMetadataFixtureHandler,
            ThrowingMetadataFixtureHandler>();
    }
}
