using System.Text.Json;
using Microsoft.Extensions.Options;

namespace ProgramKit.Host.Web;

/// <summary>Refreshes the safe identity readiness signal from discovery and JWKS endpoints.</summary>
internal sealed class IdentityReadinessService(
    IHttpClientFactory clients,
    IOptions<ProgramKitWebOptions> options,
    IdentityReadinessState state,
    ILogger<IdentityReadinessService> logger) : BackgroundService
{
    /// <inheritdoc />
    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        if (options.Value.Profile == ProgramKitWebProfile.None)
        {
            state.SetReady(true);
            return;
        }

        await ProbeAsync(stoppingToken).ConfigureAwait(false);
        using var timer = new PeriodicTimer(TimeSpan.FromSeconds(30));
        while (await timer.WaitForNextTickAsync(stoppingToken).ConfigureAwait(false))
        {
            await ProbeAsync(stoppingToken).ConfigureAwait(false);
        }
    }

    /// <summary>Updates readiness without retaining or exposing provider response details.</summary>
    private async Task ProbeAsync(CancellationToken stoppingToken)
    {
        try
        {
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(stoppingToken);
            timeout.CancelAfter(TimeSpan.FromSeconds(options.Value.DiscoveryTimeoutSeconds));
            var authority = options.Value.Authority.TrimEnd('/');
            var client = clients.CreateClient("program-kit-identity-readiness");
            using var discovery = await client.GetAsync(
                $"{authority}/.well-known/openid-configuration",
                timeout.Token).ConfigureAwait(false);
            discovery.EnsureSuccessStatusCode();
            await using var stream = await discovery.Content.ReadAsStreamAsync(timeout.Token).ConfigureAwait(false);
            using var document = await JsonDocument.ParseAsync(stream, cancellationToken: timeout.Token).ConfigureAwait(false);
            var jwksUri = document.RootElement.GetProperty("jwks_uri").GetString();
            if (string.IsNullOrWhiteSpace(jwksUri))
            {
                throw new InvalidOperationException("OIDC discovery did not supply jwks_uri.");
            }

            using var jwks = await client.GetAsync(jwksUri, timeout.Token).ConfigureAwait(false);
            jwks.EnsureSuccessStatusCode();
            if (state.SetReady(true))
            {
                logger.LogInformation("Identity readiness is available.");
            }
        }
        catch (OperationCanceledException) when (!stoppingToken.IsCancellationRequested)
        {
            if (state.SetReady(false))
            {
                logger.LogWarning("Identity readiness is unavailable because its time budget was exceeded.");
            }
        }
        catch (Exception exception) when (exception is HttpRequestException or JsonException or InvalidOperationException)
        {
            if (state.SetReady(false))
            {
                logger.LogWarning("Identity readiness is unavailable; provider details are intentionally omitted.");
            }
        }
    }
}
