using System.Diagnostics;
using System.Net;
namespace ObservatoryScheduling.Tests.Configuration;

public sealed class HostRuntimeTests
{
    [Test]
    public async Task HostsStartAndExposeTheirDeclaredHealthContracts()
    {
        await VerifyConsoleHelpAsync();
        await VerifyHostAsync(
            "ObservatoryScheduling.Api.exe",
            43101,
            ["/health/ready", "/health/live"]);
        await VerifyHostAsync(
            "ObservatoryScheduling.Console.exe",
            43102,
            ["/health/ready"]);
        await VerifyHostAsync(
            "ObservatoryScheduling.Worker.exe",
            43103,
            ["/health/ready"]);
    }

    private static async Task VerifyConsoleHelpAsync()
    {
        var startInfo = CreateStartInfo(
            "ObservatoryScheduling.Console.exe");
        startInfo.ArgumentList.Add("--help");
        using var process = Process.Start(startInfo) ??
            throw new InvalidOperationException(
                "The Observatory Console host did not start.");
        var output = await process.StandardOutput.ReadToEndAsync();
        var error = await process.StandardError.ReadToEndAsync();
        await process.WaitForExitAsync();

        FixtureAssert.AreEqual(0, process.ExitCode);
        FixtureAssert.IsTrue(output.StartsWith(
            "schedule --target",
            StringComparison.Ordinal));
        FixtureAssert.AreEqual(string.Empty, error);
    }

    private static async Task VerifyHostAsync(
        string executableName,
        int port,
        IReadOnlyList<string> paths)
    {
        var startInfo = CreateStartInfo(executableName);
        using var process = Process.Start(startInfo) ??
            throw new InvalidOperationException(
                $"{executableName} did not start.");
        try
        {
            using var client = new HttpClient
            {
                Timeout = TimeSpan.FromSeconds(1),
            };
            foreach (var path in paths)
            {
                using var response = await WaitForHealthAsync(
                    process,
                    client,
                    new Uri(
                        $"http://127.0.0.1:{port}{path}",
                        UriKind.Absolute));
                FixtureAssert.AreEqual(
                    HttpStatusCode.OK,
                    response.StatusCode);
            }
        }
        finally
        {
            if (!process.HasExited)
            {
                process.Kill(entireProcessTree: true);
                await process.WaitForExitAsync();
            }
        }
    }

    private static async Task<HttpResponseMessage> WaitForHealthAsync(
        Process process,
        HttpClient client,
        Uri endpoint)
    {
        for (var attempt = 0; attempt < 40; attempt++)
        {
            if (process.HasExited)
            {
                var output = await process.StandardOutput.ReadToEndAsync();
                var error = await process.StandardError.ReadToEndAsync();
                throw new InvalidOperationException(
                    $"Host exited before {endpoint} became ready.{Environment.NewLine}{output}{Environment.NewLine}{error}");
            }

            try
            {
                return await client.GetAsync(endpoint);
            }
            catch (HttpRequestException) when (attempt < 39)
            {
                await Task.Delay(TimeSpan.FromMilliseconds(250));
            }
            catch (TaskCanceledException) when (attempt < 39)
            {
                await Task.Delay(TimeSpan.FromMilliseconds(250));
            }
        }

        throw new InvalidOperationException(
            $"{endpoint} did not become ready.");
    }

    private static ProcessStartInfo CreateStartInfo(string executableName)
    {
        var executable = Path.Combine(
            AppContext.BaseDirectory,
            executableName);
        return new ProcessStartInfo(executable)
        {
            CreateNoWindow = true,
            RedirectStandardError = true,
            RedirectStandardOutput = true,
            UseShellExecute = false,
            WorkingDirectory = AppContext.BaseDirectory,
        };
    }
}
