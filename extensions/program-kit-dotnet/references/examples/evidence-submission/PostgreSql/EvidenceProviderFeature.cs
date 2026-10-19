using CShells;
using CShells.Features;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

namespace ProgramKit.Examples.Evidence;

/// <summary>Owning provider registration. The connection is a supervisor-owned secret reference, never evidence.</summary>
[ShellFeature("Evidence.PostgreSql")]
public sealed class EvidenceProviderFeature(ShellSettings settings) : IShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        var configuration = settings.GetConfigurationRoot();
        var connection = configuration["Evidence:Connection"];
        if (string.IsNullOrWhiteSpace(connection))
            throw new InvalidOperationException("Evidence provider connection is unavailable.");
        Action<DbContextOptionsBuilder> configure = options => options.UseNpgsql(connection);
        services.AddDbContext<EvidenceDbContext>(configure);
        services.AddScoped<IEvidenceJournal, PostgreSqlEvidenceJournal>();
    }
}
