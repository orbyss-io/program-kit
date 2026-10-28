using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Orbyss.Foundation.Authentication;

namespace Application.Api;

/// <summary>Owns the synthetic note transport while the selected Foundation owns authentication and canonical permissions.</summary>
[ShellFeature("Application.Api", DependsOn = ["Orbyss.Foundation.Authentication", "Orbyss.Foundation.DomainEvents"])]
public sealed class ApiFeature : IWebShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services)
    {
        Func<IServiceProvider, OwnedNotesEndpoints> create = provider => ActivatorUtilities.CreateInstance<OwnedNotesEndpoints>(provider);
        services.AddScoped(create);
    }
    /// <inheritdoc />
    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment)
    {
        Func<HttpContext, OwnedNotesEndpoints, Task<IResult>> create = (HttpContext context, [FromServices] OwnedNotesEndpoints notes) => notes.CreateAsync(context);
        Func<HttpContext, Guid, OwnedNotesEndpoints, Task<IResult>> read = (
            HttpContext context,
            Guid id,
            [FromServices] OwnedNotesEndpoints notes
        ) => notes.ReadAsync(context, id);
        var writePermission = PermissionPolicyNames.ForPermission("notes.write");
        var readPermission = PermissionPolicyNames.ForPermission("notes.read");
        endpoints
            .MapPost("/api/owned-notes", create)
            .RequireAuthorization(writePermission)
            .ExcludeFromDescription();
        endpoints
            .MapGet("/api/owned-notes/{id:guid}", read)
            .RequireAuthorization(readPermission)
            .ExcludeFromDescription();
    }
}
