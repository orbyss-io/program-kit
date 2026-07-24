using System.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.Processes;

/// <summary>Default shell-free process boundary with cancellation containment.</summary>
public sealed class CommandProcessRunner : ICommandProcessRunner
{
    /// <inheritdoc />
    public async ValueTask<CommandProcessResult> RunAsync(
        CommandProcessRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        var startInfo = new ProcessStartInfo
        {
            FileName = request.Executable,
            WorkingDirectory = request.WorkingDirectory,
            RedirectStandardError = true,
            RedirectStandardOutput = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        foreach (var argument in request.Arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        foreach (var item in request.Environment)
        {
            startInfo.Environment[item.Key] = item.Value;
        }

        using var process = new Process
        {
            StartInfo = startInfo,
        };
        if (!process.Start())
        {
            throw new IOException(
                string.Concat(
                    "The explicit process could not start: ",
                    request.Executable));
        }

        var standardOutput = process.StandardOutput.ReadToEndAsync(
            cancellationToken);
        var standardError = process.StandardError.ReadToEndAsync(
            cancellationToken);
        try
        {
            await process.WaitForExitAsync(cancellationToken)
                .ConfigureAwait(false);
        }
        catch (OperationCanceledException)
        {
            if (!process.HasExited)
            {
                process.Kill(entireProcessTree: true);
            }

            throw;
        }

        return new CommandProcessResult(
            process.ExitCode,
            await standardOutput.ConfigureAwait(false),
            await standardError.ConfigureAwait(false));
    }
}
