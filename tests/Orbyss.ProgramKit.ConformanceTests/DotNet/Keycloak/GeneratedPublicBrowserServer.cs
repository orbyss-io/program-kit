using System.Security.Cryptography.X509Certificates;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.StaticFiles;
using Microsoft.Extensions.Logging;

namespace Orbyss.ProgramKit.ConformanceTests.DotNet.Keycloak;

internal sealed class GeneratedPublicBrowserServer : IAsyncDisposable
{
    private readonly WebApplication application;
    private readonly X509Certificate2 certificate;

    private GeneratedPublicBrowserServer(
        WebApplication application,
        X509Certificate2 certificate)
    {
        this.application = application;
        this.certificate = certificate;
    }

    internal static async Task<GeneratedPublicBrowserServer> StartAsync(
        string staticRoot,
        string certificatePath,
        string privateKeyPath,
        int port,
        CancellationToken cancellationToken)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(staticRoot);
        ArgumentException.ThrowIfNullOrWhiteSpace(certificatePath);
        ArgumentException.ThrowIfNullOrWhiteSpace(privateKeyPath);
        ArgumentOutOfRangeException.ThrowIfLessThan(port, 1);
        ArgumentOutOfRangeException.ThrowIfGreaterThan(port, 65535);
        if (!Directory.Exists(staticRoot))
        {
            throw new DirectoryNotFoundException(
                "The generated public-browser static output is unavailable.");
        }
        if (!File.Exists(Path.Combine(staticRoot, "index.html")))
        {
            throw new FileNotFoundException(
                "The generated public-browser entry document is unavailable.");
        }

        var certificate = X509Certificate2.CreateFromPemFile(
            certificatePath,
            privateKeyPath);
        try
        {
            var builder = WebApplication.CreateSlimBuilder(
                new WebApplicationOptions
                {
                    ContentRootPath = staticRoot,
                    WebRootPath = staticRoot,
                });
            builder.Logging.ClearProviders();
            builder.WebHost.ConfigureKestrel(options =>
                options.ListenLocalhost(
                    port,
                    endpoint => endpoint.UseHttps(certificate)));
            var application = builder.Build();
            FileExtensionContentTypeProvider contentTypes = new();
            contentTypes.Mappings[".dat"] = "application/octet-stream";
            application.UseDefaultFiles();
            application.UseStaticFiles(
                new StaticFileOptions
                {
                    ContentTypeProvider = contentTypes,
                });
            application.MapFallbackToFile("index.html");
            await application.StartAsync(cancellationToken);
            return new GeneratedPublicBrowserServer(application, certificate);
        }
        catch
        {
            certificate.Dispose();
            throw;
        }
    }

    public async ValueTask DisposeAsync()
    {
        using var cancellation = new CancellationTokenSource(
            TimeSpan.FromSeconds(10));
        try
        {
            await application.StopAsync(cancellation.Token);
        }
        finally
        {
            await application.DisposeAsync();
            certificate.Dispose();
        }
    }
}
