using System.Text.Json;
using CShells;
using CShells.AspNetCore.Features;
using CShells.Features;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Routing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Options;
using Orbyss.Foundation.Authentication;
using ProgramKit.Foundation.TestSupport;

namespace ProgramKit.Qualification;

/// <summary>Maintained test-only observer activated in a disposable copy of the bundle.</summary>
[ShellFeature("ProgramKit.Qualification.Probe", DependsOn = [__DEPENDENCIES__])]
public sealed class QualificationFeature(ShellSettings settings) : IWebShellFeature
{
    /// <inheritdoc />
    public void ConfigureServices(IServiceCollection services) { }
    /// <inheritdoc />
    public void MapEndpoints(IEndpointRouteBuilder endpoints, IHostEnvironment? environment)
    {
        endpoints.MapGet("/", () => Results.Text("Disposable qualification fixture")).AllowAnonymous();
        endpoints.MapGet("/api/permission-probe", () => Results.NoContent()).RequireAuthorization("permission:foundation.probe");
        endpoints.MapGet("/__foundation/settings", (HttpContext http) =>
        {
            var phase="native configuration root";
            try
            {
            var location = Path.Combine(Path.GetDirectoryName(typeof(QualificationFeature).Assembly.Location)!, "settings.json");
            using var metadata = JsonDocument.Parse(File.ReadAllText(location));
            var configuration = settings.GetConfigurationRoot() as IConfigurationRoot
                ?? throw new InvalidOperationException("Activated shell configuration does not expose its native provider root.");
            using var scopes=JsonDocument.Parse(File.ReadAllText(Path.Combine(Path.GetDirectoryName(location)!,"scopes.json")));
            phase="actual authentication options";
            var authentication=RuntimeOptionsObservation.CaptureAuthentication(http.RequestServices,configuration,metadata.RootElement.EnumerateArray());
            phase="additional activated owner options";
            var owners=RuntimeOptionsObservation.Capture(http.RequestServices,configuration,scopes.RootElement);
            return Results.Json(new
            {
                optionsInstance = "activated IOptions<FoundationWebOptions>.Value",
                settings=authentication.Settings,
                authenticationAssembly=authentication.Assembly,
                profileAssembly=authentication.ProfileAssembly,
                owners
            });
            }
            catch (Exception error)
            {
                // Safe test-only diagnostics reveal phase/type identities, never
                // exception details, configured values, requests or credentials.
                var diagnostic=error.Message is "Sequence contains no matching element" or "Sequence contains more than one matching element"
                    or "Selected options metadata produced no runtime observations." or "Ambiguous actual registered owner catalogs."
                    or "Actual configured authentication owner is absent or ambiguous." ? error.Message :
                    error.Message.StartsWith("Declared setting has no actual bound property:",StringComparison.Ordinal) ||
                    error.Message.StartsWith("Duplicate runtime setting metadata path:",StringComparison.Ordinal) ? error.Message : null;
                return Results.Json(new {status="observer-failed",phase,
                    configurationType=settings.GetConfigurationRoot().GetType().FullName,errorType=error.GetType().FullName,
                    owner=error.Data["ProgramKitObservationOwner"],diagnostic},statusCode:500);
            }
        }).AllowAnonymous();
    }
}
