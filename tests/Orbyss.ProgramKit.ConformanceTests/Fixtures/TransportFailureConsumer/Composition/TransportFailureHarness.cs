using System.Diagnostics.Metrics;
using System.Text;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Http.Features;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Hosting.Internal;
using Microsoft.Extensions.Logging;
using GeneratedHost.Hosting;

namespace GeneratedHost.Composition;

/// <summary>Executes generated exception handlers against an in-memory HTTP context.</summary>
public static class TransportFailureHarness
{
    /// <summary>Runs one exception through the exact generated handler order.</summary>
    public static async Task<TransportFailureResult> RunAsync(
        Exception exception,
        bool development = false,
        string accept = "application/problem+json",
        bool responseStarted = false,
        bool clientAborted = false)
    {
        CaptureLoggerProvider logs = new();
        ServiceCollection services = new();
        _ = services.AddLogging(builder => builder.AddProvider(logs));
        _ = services.AddProblemDetails();
        await using var provider = services.BuildServiceProvider();
        var context = new DefaultHttpContext
        {
            RequestServices = provider,
        };
        context.Request.Path = "/fixture";
        context.Request.Headers.Accept = accept;
        MemoryStream body = new();
        context.Response.Body = body;
        if (responseStarted)
        {
            context.Features.Set<IHttpResponseFeature>(
                new StartedResponseFeature());
        }

        using CancellationTokenSource requestAbort = new();
        if (clientAborted)
        {
            requestAbort.Cancel();
            context.RequestAborted = requestAbort.Token;
        }

        var environment = new HostingEnvironment
        {
            EnvironmentName = development
                ? Environments.Development
                : Environments.Production,
        };
        var problemDetails = provider.GetRequiredService<IProblemDetailsService>();
        IExceptionHandler[] handlers =
        [
            new ProgramKitClientDisconnectExceptionHandler(
                provider.GetRequiredService<ILogger<ProgramKitTransportFailureCategory>>()),
            new ProgramKitMappedTransportFailureHandler(
                problemDetails,
                environment,
                provider.GetRequiredService<ILogger<ProgramKitTransportFailureCategory>>()),
            new ProgramKitFallbackTransportFailureHandler(
                problemDetails,
                environment,
                provider.GetRequiredService<ILogger<ProgramKitTransportFailureCategory>>()),
        ];
        var measurements = 0;
        using MeterListener listener = new();
        listener.InstrumentPublished = (instrument, current) =>
        {
            if (instrument.Meter.Name ==
                ProgramKitTransportFailureDiagnostics.MeterName)
            {
                current.EnableMeasurementEvents(instrument);
            }
        };
        listener.SetMeasurementEventCallback<long>(
            (_, _, _, _) => Interlocked.Increment(ref measurements));
        listener.Start();

        var handled = false;
        foreach (var handler in handlers)
        {
            if (await handler.TryHandleAsync(
                    context,
                    exception,
                    CancellationToken.None))
            {
                handled = true;
                break;
            }
        }

        await context.Response.CompleteAsync();
        var text = Encoding.UTF8.GetString(body.ToArray());
        return new TransportFailureResult(
            handled,
            context.Response.StatusCode,
            text,
            logs.Messages.Count,
            string.Join(Environment.NewLine, logs.Messages),
            measurements);
    }

    /// <summary>Runs the selected framework status-code-page middleware.</summary>
    public static async Task<(int StatusCode, string Body)> RunStatusCodePageAsync(
        string accept = "application/problem+json")
    {
        ServiceCollection services = new();
        _ = services.AddLogging();
        _ = services.AddProblemDetails();
        await using var provider = services.BuildServiceProvider();
        ApplicationBuilder application = new(provider);
        _ = application.UseStatusCodePages(async statusCodeContext =>
        {
            var problemDetails = statusCodeContext.HttpContext.RequestServices
                .GetRequiredService<IProblemDetailsService>();
            _ = await problemDetails.TryWriteAsync(new ProblemDetailsContext
            {
                HttpContext = statusCodeContext.HttpContext,
            });
        });
        application.Run(static context =>
        {
            context.Response.StatusCode = StatusCodes.Status404NotFound;
            return Task.CompletedTask;
        });
        var pipeline = application.Build();
        var context = new DefaultHttpContext
        {
            RequestServices = provider,
        };
        context.Request.Headers.Accept = accept;
        MemoryStream body = new();
        context.Response.Body = body;

        await pipeline(context);

        return (
            context.Response.StatusCode,
            Encoding.UTF8.GetString(body.ToArray()));
    }
}
