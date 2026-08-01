using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;

namespace Orbyss.ProgramKit.Providers.DotNet.Construction;

public sealed record ToolObservation(
    string Tool,
    IReadOnlyList<string> Arguments,
    int ExitCode,
    string OutputDigest,
    IReadOnlyList<string> DiagnosticCodes,
    bool Succeeded);

public sealed partial class DotNetToolRunner
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
        string candidateRoot = Path.GetFullPath(Path.Combine(workingDirectory, "..", ".."));
        string toolHome = Path.Combine(candidateRoot, ".packages", ".tool-home");
        Directory.CreateDirectory(toolHome);

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
        startInfo.Environment["DOTNET_CLI_HOME"] = toolHome;
        startInfo.Environment["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "1";
        startInfo.Environment["DOTNET_NOLOGO"] = "1";
        startInfo.Environment["DOTNET_CLI_UI_LANGUAGE"] = "en-US";
        startInfo.Environment["NUGET_XMLDOC_MODE"] = "skip";
        startInfo.Environment["NUGET_CREDENTIALPROVIDER_SESSIONTOKENCACHE_ENABLED"] = "false";
        if (OperatingSystem.IsWindows())
        {
            startInfo.Environment["APPDATA"] = toolHome;
        }
        else
        {
            startInfo.Environment["LANG"] = "C";
            startInfo.Environment["LC_ALL"] = "C";
            startInfo.Environment["XDG_CONFIG_HOME"] = toolHome;
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
            string output = await outputTask.ConfigureAwait(false);
            string error = await errorTask.ConfigureAwait(false);
            return Observation(
                workingDirectory,
                arguments,
                process.ExitCode,
                process.ExitCode == 0 ? "completed" : "failed",
                $"{output}\n{error}");
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            if (!process.HasExited)
            {
                process.Kill(entireProcessTree: true);
                await process.WaitForExitAsync(CancellationToken.None).ConfigureAwait(false);
            }

            return Observation(workingDirectory, arguments, -1, "timed-out", string.Empty);
        }
    }

    private static ToolObservation Observation(
        string workingDirectory,
        IReadOnlyList<string> arguments,
        int exitCode,
        string state,
        string output)
    {
        string candidateRoot = Path.GetFullPath(Path.Combine(workingDirectory, "..", ".."));
        string[] normalizedArguments = arguments
            .Select(argument => Normalize(argument, workingDirectory, candidateRoot))
            .ToArray();
        byte[] observationBytes = Encoding.UTF8.GetBytes(
            $"dotnet\n{state}\n{exitCode}\n{string.Join('\n', normalizedArguments)}");
        string digest = $"sha256:{Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(observationBytes)).ToLowerInvariant()}";
        string[] diagnosticCodes = DiagnosticCode().Matches(output)
            .Select(static match => match.Value)
            .Distinct(StringComparer.Ordinal)
            .OrderBy(static value => value, StringComparer.Ordinal)
            .ToArray();
        return new ToolObservation("dotnet", normalizedArguments, exitCode, digest, diagnosticCodes, exitCode == 0);
    }

    private static string Normalize(string value, string workingDirectory, string candidateRoot) => value
        .Replace(workingDirectory, "<working-directory>", StringComparison.OrdinalIgnoreCase)
        .Replace(candidateRoot, "<candidate-root>", StringComparison.OrdinalIgnoreCase)
        .Replace('\\', '/');

    [GeneratedRegex(@"\b(?:NU|MSB|CS)\d{4}\b", RegexOptions.CultureInvariant)]
    private static partial Regex DiagnosticCode();
}
