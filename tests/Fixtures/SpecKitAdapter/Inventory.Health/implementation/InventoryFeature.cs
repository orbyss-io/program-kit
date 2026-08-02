using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace Warehouse.Inventory;

public interface IInventoryProbe
{
    InventoryHealthSnapshot Inspect();
}

public sealed record InventoryHealthSnapshot(string State, int BackorderedItems);

public sealed class InventoryProbe : IInventoryProbe
{
    public InventoryHealthSnapshot Inspect() => new("degraded", 7);
}

[ShellFeature("InventoryHealth", DisplayName = "Inventory Health")]
public sealed class InventoryFeature : IWebShellFeature
{
    public void ConfigureServices(IServiceCollection services) =>
        services.AddScoped<IInventoryProbe, InventoryProbe>();

    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment) =>
        endpoints.MapGet("inventory/health", (IInventoryProbe probe) => Results.Json(probe.Inspect()));
}
