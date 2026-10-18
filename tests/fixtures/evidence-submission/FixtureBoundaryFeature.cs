using System.Security.Claims;
using System.Text.Encodings.Web;
using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Authentication;
using Microsoft.Extensions.Options;

namespace Evidence.Probe;

/// <summary>Fictional local identity adapter. Never shipped as authentication or provider-login guidance.</summary>
[ShellFeature("Fixture.Identity")]
public sealed class FixtureBoundaryFeature : IMiddlewareShellFeature
{
    public int Order => -700;

    public void ConfigureServices(IServiceCollection services)
    {
        var authentication = services.AddAuthentication("fixture");
        authentication
            .AddScheme<AuthenticationSchemeOptions, FixtureIdentity>("fixture", null);
        services.AddAuthorization();
    }

    public void UseMiddleware(IApplicationBuilder app, IHostEnvironment? environment)
    {
        app.UseAuthentication();
        app.UseAuthorization();
    }
}
