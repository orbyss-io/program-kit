using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace Orbyss.ProgramKit.SpecKitAdapter.Invocation;

public sealed record ProgramKitProcessRequest(
    string Executable,
    IReadOnlyList<string> Arguments,
    string WorkingDirectory,
    TimeSpan Timeout,
    int MaximumCapturedCharacters = 1_000_000);

public sealed record ProgramKitProcessResult(int ExitCode, string StandardOutput, string StandardError, bool OutputTruncated);

public interface IProgramKitProcessClient
{
    Task<ProgramKitProcessResult> RunAsync(ProgramKitProcessRequest request, CancellationToken cancellationToken);
}

public sealed class ProgramKitProcessClient : IProgramKitProcessClient
{
    public static ProcessStartInfo CreateStartInfo(ProgramKitProcessRequest request)
    {
        if (request.Timeout <= TimeSpan.Zero || request.MaximumCapturedCharacters < 1)
        {
            throw new ArgumentOutOfRangeException(nameof(request));
        }

        ProcessStartInfo start = new()
        {
            FileName = request.Executable,
            WorkingDirectory = request.WorkingDirectory,
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = true,
        };
        foreach (string argument in request.Arguments) start.ArgumentList.Add(argument);
        return start;
    }

    public async Task<ProgramKitProcessResult> RunAsync(ProgramKitProcessRequest request, CancellationToken cancellationToken)
    {
        using Process process = new() { StartInfo = CreateStartInfo(request) };
        if (!process.Start()) throw new InvalidOperationException("The Program Kit child process did not start.");

        using CancellationTokenSource timeout = new(request.Timeout);
        using CancellationTokenSource linked = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken, timeout.Token);
        Task<(string Text, bool Truncated)> stdout = ReadBoundedAsync(process.StandardOutput, request.MaximumCapturedCharacters);
        Task<(string Text, bool Truncated)> stderr = ReadBoundedAsync(process.StandardError, request.MaximumCapturedCharacters);
        try
        {
            await process.WaitForExitAsync(linked.Token).ConfigureAwait(false);
        }
        catch (OperationCanceledException)
        {
            if (!process.HasExited) process.Kill(entireProcessTree: true);
            await process.WaitForExitAsync(CancellationToken.None).ConfigureAwait(false);
            throw;
        }

        (string output, bool outputTruncated) = await stdout.ConfigureAwait(false);
        (string error, bool errorTruncated) = await stderr.ConfigureAwait(false);
        return new ProgramKitProcessResult(process.ExitCode, output, error, outputTruncated || errorTruncated);
    }

    private static async Task<(string Text, bool Truncated)> ReadBoundedAsync(StreamReader reader, int maximum)
    {
        char[] buffer = new char[4096];
        StringBuilder captured = new(Math.Min(maximum, 4096));
        bool truncated = false;
        int read;
        while ((read = await reader.ReadAsync(buffer).ConfigureAwait(false)) > 0)
        {
            int remaining = maximum - captured.Length;
            if (remaining > 0) captured.Append(buffer, 0, Math.Min(read, remaining));
            if (read > remaining) truncated = true;
        }

        return (captured.ToString(), truncated);
    }
}
