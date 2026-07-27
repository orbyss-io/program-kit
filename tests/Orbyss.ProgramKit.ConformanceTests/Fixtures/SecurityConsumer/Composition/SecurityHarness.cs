using GeneratedHost.Hosting;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.Extensions.DependencyInjection;

namespace GeneratedHost.Composition;

/// <summary>Exercises the isolated generated operation authorization boundary.</summary>
public static class SecurityHarness
{
    /// <summary>Runs one GET request with optional authenticated transport identity.</summary>
    public static async Task<int> RunAsync(
        string path,
        bool authenticated)
    {
        ServiceCollection services = new();
        services.AddLogging();
        services.AddAuthentication("fixture")
            .AddScheme<
                AuthenticationSchemeOptions,
                FixtureAuthenticationHandler>(
                "fixture",
                _ => { });
        services.AddAuthorizationBuilder()
            .AddPolicy(
                "ProgramKit.AuthenticatedTransport",
                policy =>
                {
                    policy.AddAuthenticationSchemes("fixture");
                    policy.RequireAuthenticatedUser();
                })
            .AddPolicy(
                "Fixture.Denied",
                policy =>
                {
                    policy.AddAuthenticationSchemes("fixture");
                    policy.RequireAuthenticatedUser();
                    policy.RequireAssertion(static _ => false);
                });
        await using var provider = services.BuildServiceProvider();
        DefaultHttpContext context = new()
        {
            RequestServices = provider,
        };
        context.Request.Method = HttpMethods.Get;
        context.Request.Path = path;
        if (authenticated)
        {
            context.Request.Headers["x-fixture-user"] = "present";
        }

        var authentication = await context.AuthenticateAsync("fixture");
        if (authentication.Succeeded && authentication.Principal is not null)
        {
            context.User = authentication.Principal;
        }

        ProgramKitOperationAuthorizationMiddleware middleware = new();
        await middleware.InvokeAsync(
            context,
            static next =>
            {
                next.Response.StatusCode = StatusCodes.Status204NoContent;
                return Task.CompletedTask;
            });
        return context.Response.StatusCode;
    }
}
