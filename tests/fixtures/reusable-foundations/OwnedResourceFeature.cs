using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Orbyss.Foundation.Authentication;
using Orbyss.Foundation.WebDefaults;
using Product.Core;

namespace Application.Api;

/// <summary>Disposable application's product bindings, rather than generic test infrastructure.</summary>
[ShellFeature("Application.Api", DependsOn = ["Orbyss.Foundation.Authentication", "Orbyss.Foundation.WebDefaults", "Application.PostgreSql"])]
public sealed class ApiFeature : IWebShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services) { }
    /// <inheritdoc />
    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment)
    {
        endpoints.MapPut("/resources/{id:guid}", async (Guid id, HttpContext http, IValidatedAccountIdentityReader identities,
            IOwnedResources resources) =>
        {
            if (!identities.TryRead(http.User, out var owner)) return Results.Unauthorized();
            var outcome = await resources.CreateAsync(id, new ResourceOwner(owner.Issuer, owner.Subject), http.RequestAborted);
            return outcome == CreateResourceOutcome.Created ? Results.Created($"/resources/{id}", new { id }) : Results.Conflict();
        }).RequireAuthorization().WithMetadata(new WebResponseMetadata(Private:true));
        endpoints.MapGet("/resources/{id:guid}", async (Guid id, HttpContext http, IValidatedAccountIdentityReader identities,
            IOwnedResources resources) =>
        {
            if (!identities.TryRead(http.User, out var owner)) return Results.Unauthorized();
            var found = await resources.ReadAsync(id, new ResourceOwner(owner.Issuer, owner.Subject), http.RequestAborted);
            return found is { } resource ? Results.Ok(new { id=resource }) : Results.NotFound();
        }).RequireAuthorization().WithMetadata(new WebResponseMetadata(Private:true));
    }
}
