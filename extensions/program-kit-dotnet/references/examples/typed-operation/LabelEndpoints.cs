using CShells;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Orbyss.Foundation.Json;
using Orbyss.Foundation.Json.AspNetCore;
using ReadLabel = ProgramKit.Examples.TypedOperation.Operations.ReadLabel.Endpoint;
using WriteLabel = ProgramKit.Examples.TypedOperation.Operations.WriteLabel.Endpoint;

namespace ProgramKit.Examples.TypedOperation;

/// <summary>Composes independent operations and the intentionally shared label representation.</summary>
public static class LabelEndpoints
{
    /// <summary>Registers shared representation/options and operation-owned factories.</summary>
    public static void Configure(IServiceCollection services, ShellSettings settings)
    {
        LabelApiOptions.Configure(services, settings);
        var profile = new JsonProfileKey("sample-label-response");
        var requirement = new JsonProfileRequirement(JsonProfileKeys.TolerantResponse, maximumBytes: 2048);
        services.AddJsonResponseContract<LabelResponse>(profile, requirement);
        ReadLabel.Configure(services);
        WriteLabel.Configure(services);
    }

    /// <summary>Composes mapping without accumulating routes, admission or behavior.</summary>
    public static void Map(IEndpointRouteBuilder endpoints)
    {
        ReadLabel.Map(endpoints);
        WriteLabel.Map(endpoints);
    }
}
