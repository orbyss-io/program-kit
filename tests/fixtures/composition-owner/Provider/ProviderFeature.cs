using Application.Core;
using CShells;
using CShells.Features;
using CShells.Lifecycle;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Orbyss.Foundation.PostgreSql;

namespace Application.PostgreSql;

/// <summary>Composes the native context and owned capability; migration deployment remains explicit.</summary>
[ShellFeature("Application.PostgreSql")]
public sealed class ProviderFeature(ShellSettings settings) : IShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        Func<DbContextOptions<PolicyDbContext>, PolicyDbContext> context = options => new(options);
        services.AddFoundationPostgreSql<PolicyDbContext>(
            settings,
            "policies",
            context
        );
        var configuration = settings.GetConfigurationRoot();
        Func<IServiceProvider, OwnedNoteSecret> secret = _ => new OwnedNoteSecret(configuration["Example:HmacSecret"] ?? "");
        services.AddSingleton(secret);
        services.AddScoped<IOwnedNotes, OwnedNotes>();
        services.AddShellInitializer<OwnedNotesAdmission>(LifecyclePhase.Prepare, order: 100);
    }
}
