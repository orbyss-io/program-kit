using System.Collections.Immutable;
using System.Diagnostics;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Verification;
using Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

namespace Orbyss.ProgramKit.CSharpBuildGates.Testing.Operations.Execution;

/// <summary>
/// Executes one of five closed `dotnet` command templates and promotes
/// deterministic evidence only after all exact checks succeed.
/// </summary>
public sealed class PinnedDotNetCSharpGateCompilerHarness :
    ICSharpGateCompilerHarness
{
    private const int AbsoluteMaximumOutputBytes = 1_048_576;

    /// <inheritdoc />
    public async ValueTask<CSharpGateCompilerHarnessResult> VerifyAsync(
        CSharpGateVerificationRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        ValidateRequest(request);
        cancellationToken.ThrowIfCancellationRequested();
        var sdk = await ExecuteAsync(
            request.WorkingDirectory,
            ["--version"],
            request.MaximumCapturedOutputBytes,
            cancellationToken).ConfigureAwait(false);
        if (sdk.ExitCode != 0 ||
            !string.Equals(
                sdk.Output.Trim(),
                request.DotNetSdkVersion.Value,
                StringComparison.Ordinal))
        {
            return Failed(
                sdk,
                CSharpGateEvidenceLayer.Toolchain,
                request.WorkingDirectory);
        }

        var stopwatch = Stopwatch.StartNew();
        var execution = await ExecuteAsync(
            request.WorkingDirectory,
            CommandArguments(request),
            request.MaximumCapturedOutputBytes,
            cancellationToken).ConfigureAwait(false);
        stopwatch.Stop();
        if (execution.ExitCode != 0)
        {
            return Failed(
                execution,
                CSharpGateEvidenceLayer.SourcePolicy,
                request.WorkingDirectory);
        }

        if (stopwatch.ElapsedMilliseconds >
            request.PerformanceBudgetMilliseconds)
        {
            return Failed(
                execution,
                CSharpGateEvidenceLayer.Performance,
                request.WorkingDirectory);
        }

        var participation = DigestExactFiles(
            request.WorkingDirectory,
            request.ParticipationReceiptPaths,
            "participation receipt");
        var exceptions = DigestExactFiles(
            request.WorkingDirectory,
            request.ExceptionUseReceiptPaths,
            "exception-use receipt");
        var packages = ValidatePackages(
            request.WorkingDirectory,
            request.PackagePaths);
        cancellationToken.ThrowIfCancellationRequested();
        var outputDigest = DigestText(NormalizeOutput(
            execution.Output,
            request.WorkingDirectory));
        var result = new CSharpGateCompilerHarnessResult(
            true,
            0,
            null,
            outputDigest,
            participation,
            exceptions,
            packages);
        await CommitEvidenceAsync(
            request,
            result,
            cancellationToken).ConfigureAwait(false);
        return result;
    }

    private static void ValidateRequest(CSharpGateVerificationRequest request)
    {
        var workingDirectory = Path.GetFullPath(request.WorkingDirectory);
        var projectPath = Path.GetFullPath(request.ProjectPath);
        if (!Directory.Exists(workingDirectory) ||
            !File.Exists(projectPath) ||
            !IsUnder(projectPath, workingDirectory))
        {
            throw new InvalidOperationException(
                "Verification requires one exact project below the exact working directory.");
        }

        if (request.DotNetSdkVersion.Value != "10.0.302")
        {
            throw new InvalidOperationException(
                "Only the pinned Program Kit SDK 10.0.302 is supported.");
        }

        if (request.MaximumCapturedOutputBytes is <= 0 or
            > AbsoluteMaximumOutputBytes)
        {
            throw new InvalidOperationException(
                "Captured output must use the finite 1..1048576 byte range.");
        }

        if (request.PerformanceBudgetMilliseconds <= 0)
        {
            throw new InvalidOperationException(
                "A positive finite performance budget is required.");
        }

        ValidateStablePaths(
            request.ParticipationReceiptPaths,
            "participation receipts");
        ValidateStablePaths(
            request.ExceptionUseReceiptPaths,
            "exception-use receipts");
        ValidateStablePaths(request.PackagePaths, "packages");
        var evidence = Path.GetFullPath(request.EvidenceOutputPath);
        if (!IsUnder(evidence, workingDirectory) || File.Exists(evidence))
        {
            throw new InvalidOperationException(
                "Evidence must be a new exact path below the working directory.");
        }
    }

    private static ImmutableArray<string> CommandArguments(
        CSharpGateVerificationRequest request)
    {
        var project = Path.GetFullPath(request.ProjectPath);
        var boundary = Kebab(request.Boundary.ToString());
        var profile = Kebab(request.VerificationProfile.ToString());
        var common = new[]
        {
            project,
            "--no-restore",
            "--nologo",
            "--property:UseSharedCompilation=false",
            string.Concat(
                "--property:ProgramKitCSharpGateImplementationBoundary=",
                boundary),
            string.Concat(
                "--property:ProgramKitCSharpGateVerificationProfile=",
                profile),
        };
        return request.Command switch
        {
            CSharpGateCommand.Build =>
                ImmutableArray.Create("build").AddRange(common),
            CSharpGateCommand.Test =>
                ImmutableArray.Create("test").AddRange(common),
            CSharpGateCommand.Pack =>
                ImmutableArray.Create("pack").AddRange(common),
            CSharpGateCommand.Publish =>
                ImmutableArray.Create("publish").AddRange(common),
            CSharpGateCommand.GeneratedProjectVerify =>
            [
                "msbuild",
                project,
                "/t:ProgramKitVerifyGeneratedProject",
                "/restore:false",
                "/nologo",
                string.Concat(
                    "/p:ProgramKitCSharpGateImplementationBoundary=",
                    boundary),
                string.Concat(
                    "/p:ProgramKitCSharpGateVerificationProfile=",
                    profile),
            ],
            _ => throw new InvalidOperationException(
                "The verification command is not in the finite catalog."),
        };
    }

    private static async ValueTask<FiniteProcessResult> ExecuteAsync(
        string workingDirectory,
        ImmutableArray<string> arguments,
        int maximumBytes,
        CancellationToken cancellationToken)
    {
        ProcessStartInfo startInfo = new("dotnet")
        {
            WorkingDirectory = Path.GetFullPath(workingDirectory),
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
            CreateNoWindow = true,
        };
        foreach (var argument in arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        using var process = Process.Start(startInfo) ??
            throw new InvalidOperationException(
                "The pinned dotnet process could not start.");
        var standardOutput = process.StandardOutput.ReadToEndAsync(
            cancellationToken);
        var standardError = process.StandardError.ReadToEndAsync(
            cancellationToken);
        try
        {
            await process.WaitForExitAsync(cancellationToken)
                .ConfigureAwait(false);
            var output = string.Concat(
                await standardOutput.ConfigureAwait(false),
                Environment.NewLine,
                await standardError.ConfigureAwait(false));
            var bytes = Encoding.UTF8.GetByteCount(output);
            if (bytes > maximumBytes)
            {
                throw new InvalidOperationException(
                    "The finite process output limit was exceeded.");
            }

            return new FiniteProcessResult(process.ExitCode, output);
        }
        catch (OperationCanceledException)
        {
            if (!process.HasExited)
            {
                process.Kill(entireProcessTree: true);
                await process.WaitForExitAsync(CancellationToken.None)
                    .ConfigureAwait(false);
            }

            throw;
        }
    }

    private static ImmutableArray<string> DigestExactFiles(
        string workingDirectory,
        ImmutableArray<string> paths,
        string kind)
    {
        var builder = ImmutableArray.CreateBuilder<string>(paths.Length);
        foreach (var path in paths)
        {
            var exact = ExactContainedPath(workingDirectory, path, kind);
            if (!File.Exists(exact))
            {
                throw new InvalidOperationException(
                    $"The exact {kind} '{path}' does not exist.");
            }

            builder.Add(string.Concat("sha256:", FileDigest(exact)));
        }

        return builder.MoveToImmutable();
    }

    private static ImmutableArray<string> ValidatePackages(
        string workingDirectory,
        ImmutableArray<string> paths)
    {
        var builder = ImmutableArray.CreateBuilder<string>(paths.Length);
        foreach (var path in paths)
        {
            var exact = ExactContainedPath(
                workingDirectory,
                path,
                "package");
            using var archive = ZipFile.OpenRead(exact);
            var forbidden = archive.Entries
                .Select(entry => entry.FullName.Replace('\\', '/'))
                .FirstOrDefault(entry =>
                    entry.StartsWith(
                        "buildTransitive/",
                        StringComparison.OrdinalIgnoreCase) ||
                    entry.StartsWith(
                        "runtime/",
                        StringComparison.OrdinalIgnoreCase) ||
                    entry.StartsWith(
                        "runtimes/",
                        StringComparison.OrdinalIgnoreCase));
            if (forbidden is not null)
            {
                throw new InvalidOperationException(
                    $"Package '{path}' leaks forbidden asset '{forbidden}'.");
            }

            builder.Add(string.Concat("sha256:", FileDigest(exact)));
        }

        return builder.MoveToImmutable();
    }

    private static async ValueTask CommitEvidenceAsync(
        CSharpGateVerificationRequest request,
        CSharpGateCompilerHarnessResult result,
        CancellationToken cancellationToken)
    {
        var output = Path.GetFullPath(request.EvidenceOutputPath);
        var parent = Path.GetDirectoryName(output) ??
            throw new InvalidOperationException(
                "The evidence output has no parent directory.");
        Directory.CreateDirectory(parent);
        var candidate = string.Concat(output, ".", Guid.NewGuid().ToString("N"), ".tmp");
        var evidence = string.Concat(
            "{\"schemaVersion\":\"1.0.0\",\"command\":",
            Json(Kebab(request.Command.ToString())),
            ",\"boundary\":",
            Json(Kebab(request.Boundary.ToString())),
            ",\"verificationProfile\":",
            Json(Kebab(request.VerificationProfile.ToString())),
            ",\"succeeded\":true,\"outputDigest\":",
            Json(string.Concat("sha256:", result.OutputDigest)),
            ",\"participationReceiptDigests\":",
            JsonArray(result.ParticipationReceiptDigests),
            ",\"exceptionUseReceiptDigests\":",
            JsonArray(result.ExceptionUseReceiptDigests),
            ",\"packageDigests\":",
            JsonArray(result.PackageDigests),
            "}\n");
        try
        {
            await File.WriteAllTextAsync(
                candidate,
                evidence,
                new UTF8Encoding(encoderShouldEmitUTF8Identifier: false),
                cancellationToken).ConfigureAwait(false);
            cancellationToken.ThrowIfCancellationRequested();
            File.Move(candidate, output, overwrite: false);
        }
        finally
        {
            if (File.Exists(candidate))
            {
                File.Delete(candidate);
            }
        }
    }

    private static CSharpGateCompilerHarnessResult Failed(
        FiniteProcessResult process,
        CSharpGateEvidenceLayer layer,
        string workingDirectory) =>
        new(
            false,
            process.ExitCode,
            layer,
            DigestText(NormalizeOutput(process.Output, workingDirectory)),
            [],
            [],
            []);

    private static string ExactContainedPath(
        string workingDirectory,
        string path,
        string kind)
    {
        if (string.IsNullOrWhiteSpace(path) ||
            Path.IsPathRooted(path) ||
            path.Split('/', '\\').Any(segment => segment is "." or ".."))
        {
            throw new InvalidOperationException(
                $"Every {kind} path must be exact and working-directory relative.");
        }

        var exact = Path.GetFullPath(Path.Combine(workingDirectory, path));
        if (!IsUnder(exact, workingDirectory))
        {
            throw new InvalidOperationException(
                $"The {kind} path escapes the working directory.");
        }

        return exact;
    }

    private static void ValidateStablePaths(
        ImmutableArray<string> paths,
        string name)
    {
        if (paths.IsDefault ||
            paths.Distinct(StringComparer.Ordinal).Count() != paths.Length ||
            !paths.SequenceEqual(paths.Order(StringComparer.Ordinal)))
        {
            throw new InvalidOperationException(
                $"Exact {name} must be initialized, unique, and ordinally ordered.");
        }
    }

    private static bool IsUnder(string path, string root) =>
        Path.GetFullPath(path).StartsWith(
            string.Concat(
                Path.GetFullPath(root).TrimEnd(
                    Path.DirectorySeparatorChar,
                    Path.AltDirectorySeparatorChar),
                Path.DirectorySeparatorChar),
            StringComparison.OrdinalIgnoreCase);

    private static string FileDigest(string path)
    {
        using var stream = File.OpenRead(path);
        return Convert.ToHexStringLower(SHA256.HashData(stream));
    }

    private static string DigestText(string value) =>
        Convert.ToHexStringLower(
            SHA256.HashData(Encoding.UTF8.GetBytes(value)));

    private static string Redact(string value, string workingDirectory) =>
        value.Replace(
            Path.GetFullPath(workingDirectory),
            "<workspace>",
            StringComparison.OrdinalIgnoreCase);

    private static string NormalizeOutput(
        string value,
        string workingDirectory) =>
        string.Join(
            "\n",
            Redact(value, workingDirectory)
                .Replace('\\', '/')
                .Split('\n')
                .Select(static line => line.TrimEnd('\r', ' '))
                .Where(static line =>
                    !line.TrimStart().StartsWith(
                        "Time Elapsed ",
                        StringComparison.OrdinalIgnoreCase) &&
                    !line.TrimStart().StartsWith(
                        "Build started ",
                        StringComparison.OrdinalIgnoreCase)))
            .Trim();

    private static string Kebab(string value)
    {
        var builder = new StringBuilder(value.Length + 8);
        for (var index = 0; index < value.Length; index++)
        {
            var character = value[index];
            if (index > 0 && char.IsUpper(character))
            {
                builder.Append('-');
            }

            builder.Append(char.ToLowerInvariant(character));
        }

        return builder.ToString();
    }

    private static string Json(string value) =>
        string.Concat(
            "\"",
            value
                .Replace("\\", "\\\\", StringComparison.Ordinal)
                .Replace("\"", "\\\"", StringComparison.Ordinal),
            "\"");

    private static string JsonArray(IEnumerable<string> values) =>
        string.Concat("[", string.Join(",", values.Select(Json)), "]");

}
