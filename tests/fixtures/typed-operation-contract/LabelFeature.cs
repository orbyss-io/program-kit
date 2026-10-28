using CShells;
using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using ProgramKit.Examples.TypedOperation;

namespace Label.Contract.Api;

/// <summary>Fictional native composition wrapper over the actual shipped operation sources; no runtime provider.</summary>
[ShellFeature("Label.Contract", DependsOn = ["Orbyss.Foundation.Json.AspNetCore", "Orbyss.Foundation.Web.OpenApi"])]
public sealed class LabelFeature(ShellSettings settings) : IWebShellFeature
{
    /// <summary>Registers the actual deferred endpoint factories and native JSON contracts.</summary>
    public void ConfigureServices(IServiceCollection services) => LabelEndpoints.Configure(services, settings);

    /// <summary>Maps the actual stable label routes without resolving an application or store capability.</summary>
    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment) => LabelEndpoints.Map(endpoints);
}
