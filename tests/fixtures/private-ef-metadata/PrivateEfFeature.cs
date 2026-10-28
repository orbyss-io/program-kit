using CShells;
using CShells.AspNetCore.Features;
using CShells.Features;
using CShells.Lifecycle;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Routing;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Newtonsoft.Json;
using Orbyss.Foundation.PostgreSql;

namespace ProgramKit.Examples.PostgreSql;

/// <summary>Exercises a packed EF feature and a genuine private runtime dependency on the public Host.</summary>
[ShellFeature("ProgramKit.PrivateEfMetadata")]
public sealed class PrivateEfFeature(ShellSettings settings) : IWebShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        Func<DbContextOptions<NativeMigrationContext>, NativeMigrationContext> createContext = options => new(options);
        services.AddFoundationPostgreSql<NativeMigrationContext>(
            settings,
            "fixture",
            createContext
        );
        services.AddShellInitializer<NativeMigrationAdmission>(LifecyclePhase.Prepare, order: 100);
    }

    /// <inheritdoc />
    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment)
    {
        endpoints
            .MapGet("/api/private-ef", ReadAsync)
            .AllowAnonymous();
        endpoints
            .MapPost("/api/private-ef", WriteAsync)
            .AllowAnonymous();
    }

    /// <summary>Reads through the registered Foundation unit and serializes with the private runtime package.</summary>
    private static async Task<IResult> ReadAsync(
        [FromServices] IPostgreSqlUnitLeaseFactory<NativeMigrationContext> units,
        CancellationToken cancellationToken
    )
    {
        await using var unit = await units.BeginUnitAsync(cancellationToken);
        await using var context = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
        var entries = context.Set<NativeMigrationEntry>();
        var count = await entries.CountAsync(unit.Deadline.Token);
        var response = new { count, privateRuntime = "Newtonsoft.Json" };
        var json = JsonConvert.SerializeObject(response);
        return Results.Text(json, "application/json");
    }

    /// <summary>Persists one synthetic value using only the Host's runtime database identity.</summary>
    private static async Task<IResult> WriteAsync(
        [FromServices] IPostgreSqlUnitLeaseFactory<NativeMigrationContext> units,
        CancellationToken cancellationToken
    )
    {
        await using var unit = await units.BeginUnitAsync(cancellationToken);
        await using var context = await unit.Factory.CreateDbContextAsync(unit.Deadline.Token);
        var entry = new NativeMigrationEntry { Value = "published-host-entry" };
        context.Add(entry);
        await context.SaveChangesAsync(unit.Deadline.Token);
        return Results.Text("written", "text/plain");
    }
}
