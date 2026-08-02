using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace Reference.Status;

public interface IStatusReader
{
    StatusDocument Read();
}

public sealed record StatusDocument(string State, string ContractRevision);

public sealed class StatusReader : IStatusReader
{
    public StatusDocument Read() => new("operational", "reference.status/v1");
}

[ShellFeature("Status", DisplayName = "Reference Status")]
public sealed class StatusFeature : IWebShellFeature
{
    public void ConfigureServices(IServiceCollection services) =>
        services.AddSingleton<IStatusReader, StatusReader>();

    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment) =>
        endpoints.MapGet("status", (IStatusReader reader) => Results.Json(reader.Read()));
}
