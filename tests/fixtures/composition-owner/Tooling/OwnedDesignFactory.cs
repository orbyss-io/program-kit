using Application.PostgreSql;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;

namespace Application.Deployment;

/// <summary>Supports native EF from an unpacked startup project without admitting Design into the runtime provider.</summary>
public sealed class OwnedDesignFactory : IDesignTimeDbContextFactory<PolicyDbContext>
{
    /// <inheritdoc />
    public PolicyDbContext CreateDbContext(string[] args)
    {
        var builder = new DbContextOptionsBuilder<PolicyDbContext>();
        builder.UseNpgsql("Host=127.0.0.1;Port=1;Database=design_only;Username=design_only;Timeout=1");
        return new PolicyDbContext(builder.Options);
    }
}
