using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace Orbyss.ProgramKit.Providers.DotNet.Construction;

public sealed record ToolObservation(string Tool, IReadOnlyList<string> Arguments, int ExitCode, string OutputDigest, bool Succeeded);

public sealed class DotNetToolRunner
{
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
        startInfo.Environment["DOTNET_NOLOGO"] = "1";
        startInfo.Environment["NUGET_XMLDOC_MODE"] = "skip";

        using Process process = Process.Start(startInfo)
            ?? throw new InvalidOperationException("Unable to start the exact dotnet tool.");
        Task<string> outputTask = process.StandardOutput.ReadToEndAsync(cancellationToken);
        Task<string> errorTask = process.StandardError.ReadToEndAsync(cancellationToken);
        await process.WaitForExitAsync(cancellationToken).ConfigureAwait(false);
        string output = await outputTask.ConfigureAwait(false);
        string error = await errorTask.ConfigureAwait(false);
        byte[] observationBytes = Encoding.UTF8.GetBytes($"{process.ExitCode}\n{output}\n{error}");
        string digest = $"sha256:{Convert.ToHexString(System.Security.Cryptography.SHA256.HashData(observationBytes)).ToLowerInvariant()}";
        return new ToolObservation("dotnet", arguments, process.ExitCode, digest, process.ExitCode == 0);
    }
}
