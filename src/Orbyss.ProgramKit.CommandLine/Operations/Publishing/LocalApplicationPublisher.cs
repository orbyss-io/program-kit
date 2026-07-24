using System.Collections.Immutable;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Operations.DotNet;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Local;
using Orbyss.ProgramKit.CommandLine.Operations.Processes;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Publishing;

/// <summary>Isolated exact-host local publish with staged output and complete file hashes.</summary>
public sealed class LocalApplicationPublisher : ILocalApplicationPublisher
{
    private readonly ICommandFileSystem fileSystem;
    private readonly ICommandProcessRunner processRunner;
    private readonly IDotNetHostGenerationCommandService generationService;
    private readonly ILocalPackageRootVerifier packageRootVerifier;
    private readonly INuGetSourceConfigurationWriter sourceWriter;
    private readonly INuGetLockVerifier lockVerifier;
    private readonly IProgramKitJsonSerializer serializer;

    /// <summary>Initializes every generation, restore, verification, and serialization collaborator.</summary>
    public LocalApplicationPublisher(
        ICommandFileSystem fileSystem,
        ICommandProcessRunner processRunner,
        IDotNetHostGenerationCommandService generationService,
        ILocalPackageRootVerifier packageRootVerifier,
        INuGetSourceConfigurationWriter sourceWriter,
        INuGetLockVerifier lockVerifier,
        IProgramKitJsonSerializer serializer)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
        this.processRunner = processRunner ??
            throw new ArgumentNullException(nameof(processRunner));
        this.generationService = generationService ??
            throw new ArgumentNullException(nameof(generationService));
        this.packageRootVerifier = packageRootVerifier ??
            throw new ArgumentNullException(nameof(packageRootVerifier));
        this.sourceWriter = sourceWriter ??
            throw new ArgumentNullException(nameof(sourceWriter));
        this.lockVerifier = lockVerifier ??
            throw new ArgumentNullException(nameof(lockVerifier));
        this.serializer = serializer ??
            throw new ArgumentNullException(nameof(serializer));
    }

    /// <inheritdoc />
    public async ValueTask<LocalApplicationPublishResult> PublishAsync(
        LocalApplicationPublishRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        var outputRoot = Path.GetFullPath(request.OutputRoot);
        try
        {
            LocalOperationPaths.EnsureSafeRoot(outputRoot);
        }
        catch (InvalidDataException exception)
        {
            throw Failure(
                LocalOperationDiagnosticIds.UnsafeOutput,
                exception.Message,
                "/output");
        }

        fileSystem.CreateDirectory(outputRoot);
        var workRoot = Path.Combine(
            outputRoot,
            string.Concat(
                ".program-kit-work-",
                Guid.NewGuid().ToString("N")));
        LocalOperationPaths.EnsureOutputAbsent(workRoot);
        fileSystem.CreateDirectory(workRoot);
        try
        {
            var generatedRoot = Path.Combine(workRoot, "generated");
            var generation = await generationService.GenerateAsync(
                new DotNetHostGenerationCommandRequest(
                    request.ShellPath,
                    request.HostIdentity,
                    request.ArtifactManifestPath,
                    generatedRoot,
                    null),
                cancellationToken).ConfigureAwait(false);
            var packageRoot = await packageRootVerifier.VerifyAsync(
                request.PackageManifestPath,
                generation.Shell.InputVersionMapRevision,
                generation.Shell.InputVersionSelectionRevision,
                cancellationToken).ConfigureAwait(false);
            var configurationPath = Path.Combine(workRoot, "NuGet.Config");
            await fileSystem.WriteAllBytesAsync(
                configurationPath,
                sourceWriter.Write(packageRoot.RootPath, packageRoot.Manifest),
                cancellationToken).ConfigureAwait(false);

            var lockCache = Path.Combine(workRoot, "lock-cache");
            fileSystem.CreateDirectory(lockCache);
            var environment = CreateEnvironment(workRoot, lockCache);
            await RunProcessAsync(
                new CommandProcessRequest(
                    "dotnet",
                    generatedRoot,
                    RestoreArguments(
                        configurationPath,
                        lockCache,
                        lockedMode: false),
                    environment),
                "NuGet lock materialization failed.",
                cancellationToken).ConfigureAwait(false);
            var lockPath = Path.Combine(generatedRoot, "packages.lock.json");
            var lockBytes = await fileSystem.ReadAllBytesAsync(
                lockPath,
                cancellationToken).ConfigureAwait(false);
            try
            {
                lockVerifier.Verify(
                    lockBytes,
                    packageRoot.Manifest,
                    generation.HostLock);
            }
            catch (InvalidDataException exception)
            {
                throw Failure(
                    LocalOperationDiagnosticIds.RestoreClosureMismatch,
                    ContainedExceptionMessage(exception),
                    "/restore");
            }

            fileSystem.DeleteDirectory(lockCache);
            var restoreCache = Path.Combine(workRoot, "restore-cache");
            fileSystem.CreateDirectory(restoreCache);
            environment = CreateEnvironment(workRoot, restoreCache);
            await RunProcessAsync(
                new CommandProcessRequest(
                    "dotnet",
                    generatedRoot,
                    RestoreArguments(
                        configurationPath,
                        restoreCache,
                        lockedMode: true),
                    environment),
                "Locked isolated restore failed.",
                cancellationToken).ConfigureAwait(false);

            var applicationRoot = Path.Combine(workRoot, "application");
            fileSystem.CreateDirectory(applicationRoot);
            await RunProcessAsync(
                new CommandProcessRequest(
                    "dotnet",
                    generatedRoot,
                    [
                        "publish",
                        "GeneratedHost.csproj",
                        "--configuration",
                        "Release",
                        "--no-restore",
                        "--output",
                        applicationRoot,
                        "--verbosity",
                        "minimal",
                    ],
                    environment),
                "Project-level local publish failed.",
                cancellationToken).ConfigureAwait(false);
            var files = await HashPublishedFilesAsync(
                applicationRoot,
                cancellationToken).ConfigureAwait(false);
            var shellLockBytes = await fileSystem.ReadAllBytesAsync(
                Path.Combine(generatedRoot, "shell.lock.json"),
                cancellationToken).ConfigureAwait(false);
            var manifest = LocalPublishManifestFactory.Create(
                generation,
                packageRoot,
                LocalOperationHashes.Sha256(shellLockBytes.Span),
                files,
                serializer);
            var manifestBytes = serializer.Write(
                manifest,
                CommandLineJsonProfiles.LocalOperations.Reference,
                CommandLineJsonProfiles.LocalOperations.MaximumLimits);
            await fileSystem.WriteAllBytesAsync(
                Path.Combine(applicationRoot, "local-publish-manifest.json"),
                manifestBytes.ToArray(),
                cancellationToken).ConfigureAwait(false);

            var leaf = PublishLeaf(outputRoot, generation);
            EnsureLeafAbsent(leaf);
            var leafParent = Path.GetDirectoryName(leaf) ??
                throw Failure(
                    LocalOperationDiagnosticIds.UnsafeOutput,
                    "The local publish leaf has no parent directory.",
                    "/output");
            fileSystem.CreateDirectory(leafParent);
            fileSystem.MoveDirectory(applicationRoot, leaf);
            fileSystem.DeleteDirectory(workRoot);
            return new LocalApplicationPublishResult(
                manifest,
                Path.Combine(leaf, "local-publish-manifest.json"));
        }
        catch
        {
            fileSystem.DeleteDirectory(workRoot);
            throw;
        }
    }

    private static ImmutableArray<string> RestoreArguments(
        string configurationPath,
        string packagesPath,
        bool lockedMode)
    {
        var arguments = ImmutableArray.CreateBuilder<string>();
        arguments.Add("restore");
        arguments.Add("GeneratedHost.csproj");
        arguments.Add("--configfile");
        arguments.Add(configurationPath);
        arguments.Add("--packages");
        arguments.Add(packagesPath);
        arguments.Add("--no-http-cache");
        arguments.Add("--force");
        arguments.Add("--verbosity");
        arguments.Add("minimal");
        arguments.Add("-property:RestoreFallbackFolders=");
        arguments.Add("-property:RestoreIgnoreFailedSources=false");
        if (lockedMode)
        {
            arguments.Add("--locked-mode");
        }
        else
        {
            arguments.Add("--use-lock-file");
            arguments.Add("--force-evaluate");
        }

        return arguments.ToImmutable();
    }

    private static ImmutableDictionary<string, string> CreateEnvironment(
        string workRoot,
        string packagesPath) =>
        ImmutableDictionary<string, string>.Empty
            .Add("APPDATA", Path.Combine(workRoot, "application-data"))
            .Add("DOTNET_NOLOGO", "1")
            .Add("DOTNET_CLI_TELEMETRY_OPTOUT", "1")
            .Add("DOTNET_CLI_HOME", Path.Combine(workRoot, "dotnet-home"))
            .Add("LOCALAPPDATA", Path.Combine(workRoot, "local-application-data"))
            .Add("NUGET_PACKAGES", packagesPath)
            .Add("NUGET_HTTP_CACHE_PATH", Path.Combine(workRoot, "http-cache"))
            .Add("NUGET_FALLBACK_PACKAGES", string.Empty);

    private async ValueTask RunProcessAsync(
        CommandProcessRequest request,
        string message,
        CancellationToken cancellationToken)
    {
        var result = await processRunner.RunAsync(
            request,
            cancellationToken).ConfigureAwait(false);
        if (result.ExitCode != 0)
        {
            throw Failure(
                LocalOperationDiagnosticIds.PublishProcessFailed,
                ContainedProcessMessage(message, result),
                "/publish");
        }
    }

    private async ValueTask<ImmutableArray<PublishedApplicationFile>>
        HashPublishedFilesAsync(
            string applicationRoot,
            CancellationToken cancellationToken)
    {
        var files = ImmutableArray.CreateBuilder<PublishedApplicationFile>();
        foreach (var path in fileSystem.EnumerateFiles(applicationRoot))
        {
            var relativePath = LocalOperationPaths.RelativeTo(
                applicationRoot,
                path);
            if (string.Equals(
                    relativePath,
                    "local-publish-manifest.json",
                    StringComparison.Ordinal))
            {
                throw Failure(
                    LocalOperationDiagnosticIds.UnsafeOutput,
                    "The application publish unexpectedly emitted the reserved manifest path.",
                    "/output");
            }

            var bytes = await fileSystem.ReadAllBytesAsync(
                path,
                cancellationToken).ConfigureAwait(false);
            files.Add(
                new PublishedApplicationFile(
                    relativePath,
                    bytes.Length,
                    LocalOperationHashes.Sha256(bytes.Span)));
        }

        if (files.Count == 0)
        {
            throw Failure(
                LocalOperationDiagnosticIds.PublishProcessFailed,
                "The application publish produced no files.",
                "/publish");
        }

        return files
            .OrderBy(static file => file.RelativePath, StringComparer.Ordinal)
            .ToImmutableArray();
    }

    private static string PublishLeaf(
        string outputRoot,
        DotNetHostGenerationCommandResult generation) =>
        Path.Combine(
            outputRoot,
            "publish",
            LocalOperationPaths.HostSegment(generation.Host.Identity.Value),
            generation.Host.Version.Value,
            string.Concat(
                "Release_",
                generation.HostLock.Target.TargetFramework,
                "_portable_framework-dependent"));

    private static void EnsureLeafAbsent(string leaf)
    {
        try
        {
            LocalOperationPaths.EnsureOutputAbsent(leaf);
        }
        catch (Exception exception)
            when (exception is IOException or InvalidDataException)
        {
            throw Failure(
                LocalOperationDiagnosticIds.UnsafeOutput,
                exception.Message,
                "/output");
        }
    }

    private static LocalOperationException Failure(
        string id,
        string message,
        string path) =>
        new(id, CommandExitCode.ConformanceFailure, message, path);

    private static string ContainedProcessMessage(
        string message,
        CommandProcessResult result)
    {
        var diagnostic = string.IsNullOrWhiteSpace(result.StandardError)
            ? result.StandardOutput
            : result.StandardError;
        diagnostic = diagnostic.Trim();
        if (diagnostic.Length > 4096)
        {
            diagnostic = diagnostic[^4096..];
        }

        return string.IsNullOrWhiteSpace(diagnostic)
            ? message
            : string.Concat(message, " ", diagnostic);
    }

    private static string ContainedExceptionMessage(Exception exception)
    {
        var messages = new List<string>();
        for (var current = exception;
             current is not null && messages.Count < 4;
             current = current.InnerException)
        {
            if (!string.IsNullOrWhiteSpace(current.Message))
            {
                messages.Add(current.Message);
            }
        }

        var message = string.Join(" ", messages);
        return message.Length <= 4096
            ? message
            : message[..4096];
    }
}
