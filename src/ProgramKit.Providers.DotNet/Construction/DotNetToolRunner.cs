using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace Orbyss.ProgramKit.Providers.DotNet.Construction;

public sealed record ToolObservation(string Tool, IReadOnlyList<string> Arguments, int ExitCode, string OutputDigest, bool Succeeded);

public sealed class DotNetToolRunner
{
    private readonly TimeSpan timeout;

    public DotNetToolRunner(TimeSpan? timeout = null)
    {
        this.timeout = timeout ?? TimeSpan.FromMinutes(2);
    }

    public async Task<ToolObservation> RunAsync(
        string workingDirectory,
        IReadOnlyList<string> arguments,
        CancellationToken cancellationToken)
    {
        ProcessStartInfo startInfo = new("dotnet")
        {
            WorkingDirectory = workingDirectory,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        foreach (string argument in arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        startInfo.Environment["DOTNET_CLI_TELEMETRY_OPTOUT"] = "1";
        startInfo.Environment["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1";
        startInfo.Environment["DOTNET_NOLOGO"] = "1";
        startInfo.Environment["DOTNET_CLI_UI_LANGUAGE"] = "en-US";
        startInfo.Environment["NUGET_XMLDOC_MODE"] = "skip";
        startInfo.Environment["NUGET_CREDENTIALPROVIDER_SESSIONTOKENCACHE_ENABLED"] = "false";
        if (!OperatingSystem.IsWindows())
        {
            startInfo.Environment["LANG"] = "C";
            startInfo.Environment["LC_ALL"] = "C";
        }

        using Process process = Process.Start(startInfo)
            ?? throw new InvalidOperationException("Unable to start the exact dotnet tool.");
        using CancellationTokenSource bounded = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        bounded.CancelAfter(timeout);
        try
        {
            Task<string> outputTask = process.StandardOutput.ReadToEndAsync(bounded.Token);
            Task<string> errorTask = process.StandardError.ReadToEndAsync(bounded.Token);
            await process.WaitForExitAsync(bounded.Token).ConfigureAwait(false);
            await outputTask.ConfigureAwait(false);
            await errorTask.ConfigureAwait(false);
            return Observation(workingDirectory, arguments, process.ExitCode, process.ExitCode == 0 ? "completed" : "failed");
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            if (!process.HasExited)
            {
                process.Kill(entireProcessTree: true);
                await process.WaitForExitAsync(CancellationToken.None).ConfigureAwait(false);
            }

            return Observation(workingDirectory, arguments, -1, "timed-out");
        }
    }

    private static ToolObservation Observation(string workingDirectory, IReadOnlyList<string> arguments, int exitCode, string state)
    {
        string candidateRoot = Path.GetFullPath(Path.Combine(workingDirectory, "..", ".."));
        string[] normalizedArguments = arguments.Select(argument => Normalize(argument, workingDirectory, candidateRoot)).ToArray();
        byte[] observationBytes = Encoding.UTF8.GetBytes($"dotnet\n{state}\n{exitCode}\n{string.Join('\n', normalizedArguments)}");
        string digest = $"sha256:{Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(observationBytes)).ToLowerInvariant()}";
        return new ToolObservation("dotnet", normalizedArguments, exitCode, digest, exitCode == 0);
    }

    private static string Normalize(string value, string workingDirectory, string candidateRoot) => value
        .Replace(workingDirectory, "<working-directory>", StringComparison.OrdinalIgnoreCase)
        .Replace(candidateRoot, "<candidate-root>", StringComparison.OrdinalIgnoreCase)
        .Replace('\\', '/');
}
