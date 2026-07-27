using FastEndpoints;
using GeneratedHost.Hosting;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.TestHost;
using Microsoft.Extensions.DependencyInjection;

namespace GeneratedHost.Composition;

/// <summary>
/// Runs the isolated FastEndpoints syntax adapter with the generated ASP.NET
/// Core security and transport-failure owners.
/// </summary>
public static class FastEndpointsHarness
{
    /// <summary>Invokes one exact fixture path.</summary>
    public static async Task<FastEndpointsFixtureResponse> RunAsync(
        string path,
        bool authenticated)
    {
        var builder = WebApplication.CreateBuilder();
        builder.WebHost.UseTestServer();
        builder.Services.AddAuthentication("fixture")
            .AddScheme<
                AuthenticationSchemeOptions,
                FixtureAuthenticationHandler>(
                "fixture",
                static _ => { });
        builder.Services.AddAuthorizationBuilder()
            .AddPolicy(
                "ProgramKit.AuthenticatedTransport",
                static policy =>
                {
                    policy.AddAuthenticationSchemes("fixture");
                    policy.RequireAuthenticatedUser();
                })
            .AddPolicy(
                "Fixture.Denied",
                static policy =>
                {
                    policy.AddAuthenticationSchemes("fixture");
                    policy.RequireAuthenticatedUser();
                    policy.RequireAssertion(static _ => false);
                });
        builder.Services.AddTransient<ProgramKitOperationAuthorizationMiddleware>();
        builder.Services.AddProblemDetails();
        builder.Services.AddExceptionHandler<ProgramKitMappedTransportFailureHandler>();
        builder.Services.AddSingleton<
            IProgramKitFastEndpointOperationDispatcher,
            FixtureOperationDispatcher>();
        builder.Services.AddFastEndpoints(options =>
        {
            options.Assemblies =
                [typeof(ProgramKitFastEndpointAnonymous).Assembly];
        });

        await using var app = builder.Build();
        app.UseExceptionHandler(new ExceptionHandlerOptions
        {
            SuppressDiagnosticsCallback = static _ => true,
        });
        app.UseAuthentication();
        app.UseAuthorization();
        app.UseMiddleware<ProgramKitOperationAuthorizationMiddleware>();
        app.UseFastEndpoints();
        await app.StartAsync();

        using var client = app.GetTestClient();
        if (authenticated)
        {
            client.DefaultRequestHeaders.Add("x-fixture-user", "present");
        }

        using var response = await client.GetAsync(
            path,
            CancellationToken.None);
        var content = await response.Content.ReadAsStringAsync(
            CancellationToken.None);
        return new FastEndpointsFixtureResponse(
            (int)response.StatusCode,
            response.Content.Headers.ContentType?.MediaType,
            content);
    }
}
