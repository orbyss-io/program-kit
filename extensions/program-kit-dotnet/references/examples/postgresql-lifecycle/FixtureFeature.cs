using CShells;
using CShells.Features;
using Microsoft.Extensions.DependencyInjection;
using Orbyss.Foundation.PostgreSql;

namespace ProgramKit.Examples.PostgreSql;

/// <summary>Registers the actual shell policy without deploying application tables.</summary>
[ShellFeature("ProgramKit.PostgreSqlLifecycle")]
public sealed class FixtureFeature(ShellSettings settings) : IShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
        => services.AddFoundationPostgreSql<FixtureContext>(settings, "fixture", options => new FixtureContext(options));
}
