using CShells;
using CShells.Features;
using CShells.Lifecycle;
using Microsoft.Extensions.DependencyInjection;
using Orbyss.Foundation.PostgreSql;

namespace ProgramKit.Examples.PostgreSql;

/// <summary>Registers the native EF model with Foundation, without registering migration execution.</summary>
[ShellFeature("ProgramKit.NativeEfMigrations")]
public sealed class NativeMigrationFeature(ShellSettings settings) : IShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        services.AddFoundationPostgreSql<NativeMigrationContext>(settings, "fixture", options => new(options));
        services.AddShellInitializer<NativeMigrationAdmission>(LifecyclePhase.Prepare);
    }
}
