using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Artifacts.Versioning;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Local;
using Orbyss.ProgramKit.CommandLine.Operations.Processes;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Packages;

/// <summary>Manifest-only package preparation with staged collision-safe output.</summary>
public sealed class LocalPackagePreparationService :
    ILocalPackagePreparationService
{
    private readonly ICommandFileSystem fileSystem;
    private readonly ICommandProcessRunner processRunner;
    private readonly IPackageArchiveInspector archiveInspector;
    private readonly IProgramKitJsonSerializer serializer;
    private readonly IProgramKitSemanticValidator<VersionMapDocument>
        versionMapValidator;
    private readonly IProgramKitSemanticValidator<VersionSelectionDocument>
        versionSelectionValidator;

    /// <summary>Initializes all package preparation behavior explicitly.</summary>
    public LocalPackagePreparationService(
        ICommandFileSystem fileSystem,
        ICommandProcessRunner processRunner,
        IPackageArchiveInspector archiveInspector,
        IProgramKitJsonSerializer serializer,
        IProgramKitSemanticValidator<VersionMapDocument> versionMapValidator,
        IProgramKitSemanticValidator<VersionSelectionDocument>
        versionSelectionValidator)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
        this.processRunner = processRunner ??
            throw new ArgumentNullException(nameof(processRunner));
        this.archiveInspector = archiveInspector ??
            throw new ArgumentNullException(nameof(archiveInspector));
        this.serializer = serializer ??
            throw new ArgumentNullException(nameof(serializer));
        this.versionMapValidator = versionMapValidator ??
            throw new ArgumentNullException(nameof(versionMapValidator));
        this.versionSelectionValidator = versionSelectionValidator ??
            throw new ArgumentNullException(nameof(versionSelectionValidator));
    }

    /// <inheritdoc />
    public async ValueTask<LocalPackagePreparationResult> PrepareAsync(
        LocalPackagePreparationRequest request,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(request);
        var manifestPath = Path.GetFullPath(request.WorkspaceManifestPath);
        var outputRoot = Path.GetFullPath(request.OutputRoot);
        EnsureOutputAbsent(outputRoot);
        var manifestBytes = await fileSystem.ReadAllBytesAsync(
            manifestPath,
            cancellationToken).ConfigureAwait(false);
        var manifest = serializer.Read<WorkspacePackageManifest>(
            manifestBytes,
            CommandLineJsonProfiles.LocalOperations.Reference,
            CommandLineJsonProfiles.LocalOperations.MaximumLimits);
        var sourceRoot = ValidateManifest(manifestPath, manifest);
        var versionMapBytes = await VerifyArtifactAsync(
            sourceRoot,
            manifest.InputVersionMap,
            cancellationToken).ConfigureAwait(false);
        var versionSelectionBytes = await VerifyArtifactAsync(
            sourceRoot,
            manifest.InputVersionSelection,
            cancellationToken).ConfigureAwait(false);
        ValidateVersioningInputs(
            versionMapBytes,
            versionSelectionBytes,
            manifest);

        var parent = Path.GetDirectoryName(outputRoot) ??
            throw Failure(
                LocalOperationDiagnosticIds.UnsafeOutput,
                "The package output has no parent directory.",
                "/output");
        fileSystem.CreateDirectory(parent);
        var stagingRoot = Path.Combine(
            parent,
            string.Concat(
                ".",
                Path.GetFileName(outputRoot),
                ".staging-",
                Guid.NewGuid().ToString("N")));
        EnsureOutputAbsent(stagingRoot);
        fileSystem.CreateDirectory(stagingRoot);
        try
        {
            var packOutput = Path.Combine(stagingRoot, ".pack");
            fileSystem.CreateDirectory(packOutput);
            await RunPackAsync(
                sourceRoot,
                manifest,
                packOutput,
                cancellationToken).ConfigureAwait(false);
            var packages = await BuildPackageReportsAsync(
                sourceRoot,
                stagingRoot,
                packOutput,
                manifest.Packages,
                cancellationToken).ConfigureAwait(false);
            fileSystem.DeleteDirectory(packOutput);
            var resultManifest = new LocalPackageRootManifest(
                "pkid:schema:program-kit:local-package-root-manifest@1.0.0",
                new SemanticVersion("1.0.0"),
                manifest.SourceRoot,
                manifest.InputVersionMap,
                manifest.InputVersionSelection,
                packages,
                manifest.ExternalPackages
                    .OrderBy(
                        static package => package.PackageRevision.Identity.Value,
                        StringComparer.Ordinal)
                    .ToImmutableArray());
            var resultBytes = serializer.Write(
                resultManifest,
                CommandLineJsonProfiles.LocalOperations.Reference,
                CommandLineJsonProfiles.LocalOperations.MaximumLimits);
            var stagedManifestPath = Path.Combine(
                stagingRoot,
                "local-package-root-manifest.json");
            await fileSystem.WriteAllBytesAsync(
                stagedManifestPath,
                resultBytes.ToArray(),
                cancellationToken).ConfigureAwait(false);
            fileSystem.MoveDirectory(stagingRoot, outputRoot);
            return new LocalPackagePreparationResult(
                resultManifest,
                Path.Combine(outputRoot, "local-package-root-manifest.json"));
        }
        catch
        {
            fileSystem.DeleteDirectory(stagingRoot);
            throw;
        }
    }

    private string ValidateManifest(
        string manifestPath,
        WorkspacePackageManifest manifest)
    {
        if (!string.Equals(
                manifest.Schema,
                "pkid:schema:program-kit:workspace-package-manifest@1.0.0",
                StringComparison.Ordinal) ||
            manifest.Version != new SemanticVersion("1.0.0") ||
            manifest.Packages.IsDefaultOrEmpty ||
            manifest.ExternalPackages.IsDefault)
        {
            throw Failure(
                LocalOperationDiagnosticIds.InvalidWorkspaceManifest,
                "The workspace-package manifest header or finite selections are invalid.",
                "/workspaceManifest");
        }

        var sourceRoot = LocalOperationPaths.ResolveSourceRoot(
            manifestPath,
            manifest.SourceRoot);
        if (!fileSystem.DirectoryExists(sourceRoot))
        {
            throw Failure(
                LocalOperationDiagnosticIds.InvalidWorkspaceManifest,
                "The explicit source root does not exist.",
                "/sourceRoot");
        }

        _ = ResolveRequiredFile(
            sourceRoot,
            manifest.PackProjectPath,
            "/packProjectPath");
        ValidateArtifactLocator(manifest.InputVersionMap, "/inputVersionMap");
        ValidateArtifactLocator(
            manifest.InputVersionSelection,
            "/inputVersionSelection");
        ValidatePackages(sourceRoot, manifest.Packages);
        ValidateExternalPackages(
            manifest.ExternalPackages,
            manifest.Packages
                .Select(static package => package.PackageId)
                .ToHashSet(StringComparer.Ordinal));
        return sourceRoot;
    }

    private void ValidatePackages(
        string sourceRoot,
        ImmutableArray<WorkspacePackageEntry> packages)
    {
        var projects = new HashSet<string>(
            OperatingSystem.IsWindows()
                ? StringComparer.OrdinalIgnoreCase
                : StringComparer.Ordinal);
        var identities = new HashSet<string>(StringComparer.Ordinal);
        var packageIds = new HashSet<string>(StringComparer.Ordinal);
        var outputs = new HashSet<string>(StringComparer.Ordinal);
        foreach (var package in packages)
        {
            LocalOperationPaths.RequireNormalizedRelativePath(
                package.SourceProjectPath,
                "A package source-project path");
            LocalOperationPaths.RequireNormalizedRelativePath(
                package.PackageOutputPath,
                "A package output path");
            if (!string.Equals(
                    package.ExpectedTarget,
                    "net10.0",
                    StringComparison.Ordinal) ||
                string.IsNullOrWhiteSpace(package.PackageRole) ||
                string.IsNullOrWhiteSpace(package.PackageId) ||
                !ProgramKitIdentifier.Validate(
                    package.SourceProjectIdentity.Value).IsValid ||
                !ValidRevision(package.PackageRevision) ||
                !projects.Add(package.SourceProjectPath) ||
                !identities.Add(package.PackageRevision.Identity.Value) ||
                !packageIds.Add(package.PackageId) ||
                !outputs.Add(package.PackageOutputPath))
            {
                throw Failure(
                    LocalOperationDiagnosticIds.InvalidWorkspaceManifest,
                    "Package selections require unique paths/identities, exact revisions, roles, and net10.0 targets.",
                    "/packages");
            }

            _ = ResolveRequiredFile(
                sourceRoot,
                package.SourceProjectPath,
                "/packages/sourceProjectPath");
            var expectedFileName = string.Concat(
                package.PackageId,
                ".",
                package.PackageRevision.Version.Value,
                ".nupkg");
            if (!string.Equals(
                    Path.GetFileName(package.PackageOutputPath),
                    expectedFileName,
                    StringComparison.Ordinal))
            {
                throw Failure(
                    LocalOperationDiagnosticIds.InvalidWorkspaceManifest,
                    "A package output filename must exactly match packageId.version.nupkg.",
                    "/packages/packageOutputPath");
            }
        }
    }

    private static void ValidateExternalPackages(
        ImmutableArray<LockedExternalPackage> packages,
        HashSet<string> localPackageIds)
    {
        var identities = new HashSet<string>(StringComparer.Ordinal);
        var packageIds = new HashSet<string>(StringComparer.Ordinal);
        foreach (var package in packages)
        {
            byte[] hash;
            try
            {
                hash = Convert.FromBase64String(package.ContentHash);
            }
            catch (FormatException)
            {
                throw Failure(
                    LocalOperationDiagnosticIds.InvalidWorkspaceManifest,
                    "An external package content hash is not valid base64.",
                    "/externalPackages/contentHash");
            }

            if (hash.Length != 64 ||
                !ValidRevision(package.PackageRevision) ||
                !identities.Add(package.PackageRevision.Identity.Value) ||
                string.IsNullOrWhiteSpace(package.PackageId) ||
                !packageIds.Add(package.PackageId) ||
                localPackageIds.Contains(package.PackageId) ||
                package.Dependencies.IsDefault)
            {
                throw Failure(
                    LocalOperationDiagnosticIds.InvalidWorkspaceManifest,
                    "External packages require unique exact revisions, SHA-512 content hashes, and initialized dependency lists.",
                    "/externalPackages");
            }
        }

        foreach (var package in packages)
        {
            var dependencyIds = new HashSet<string>(StringComparer.Ordinal);
            if (package.Dependencies.Any(dependency =>
                    string.IsNullOrWhiteSpace(dependency.PackageId) ||
                    string.IsNullOrWhiteSpace(dependency.VersionRange) ||
                    !dependencyIds.Add(dependency.PackageId) ||
                    !packageIds.Contains(dependency.PackageId)))
            {
                throw Failure(
                    LocalOperationDiagnosticIds.InvalidWorkspaceManifest,
                    "External dependency edges must be unique and resolve inside the reviewed external closure.",
                    "/externalPackages/dependencies");
            }
        }
    }

    private static void ValidateArtifactLocator(
        WorkspaceArtifactLocator locator,
        string path)
    {
        ArgumentNullException.ThrowIfNull(locator);
        LocalOperationPaths.RequireNormalizedRelativePath(
            locator.RelativePath,
            "An immutable input locator");
        if (!ValidRevision(locator.Revision))
        {
            throw Failure(
                LocalOperationDiagnosticIds.InvalidWorkspaceManifest,
                "An immutable input locator requires an exact artifact revision.",
                path);
        }
    }

    private async ValueTask<ReadOnlyMemory<byte>> VerifyArtifactAsync(
        string sourceRoot,
        WorkspaceArtifactLocator locator,
        CancellationToken cancellationToken)
    {
        var path = ResolveRequiredFile(
            sourceRoot,
            locator.RelativePath,
            "/immutableInput");
        var bytes = await fileSystem.ReadAllBytesAsync(
            path,
            cancellationToken).ConfigureAwait(false);
        if (LocalOperationHashes.Sha256(bytes.Span) != locator.Revision.Digest)
        {
            throw Failure(
                LocalOperationDiagnosticIds.InvalidWorkspaceManifest,
                "An immutable input locator digest does not match its exact bytes.",
                "/immutableInput/digest");
        }

        return bytes;
    }

    private void ValidateVersioningInputs(
        ReadOnlyMemory<byte> versionMapBytes,
        ReadOnlyMemory<byte> versionSelectionBytes,
        WorkspacePackageManifest manifest)
    {
        var map = serializer.Read<VersionMapDocument>(
            versionMapBytes,
            CommandLineJsonProfiles.LocalOperations.Reference,
            CommandLineJsonProfiles.LocalOperations.MaximumLimits);
        var selection = serializer.Read<VersionSelectionDocument>(
            versionSelectionBytes,
            CommandLineJsonProfiles.LocalOperations.Reference,
            CommandLineJsonProfiles.LocalOperations.MaximumLimits);
        var mapValidation = versionMapValidator.Validate(map);
        var selectionValidation = versionSelectionValidator.Validate(selection);
        if (!mapValidation.IsValid ||
            !selectionValidation.IsValid ||
            selection.InputVersionMap != manifest.InputVersionMap.Revision)
        {
            throw Failure(
                LocalOperationDiagnosticIds.InvalidWorkspaceManifest,
                "The immutable Version Map or Version Selection is invalid or cross-bound to another map revision.",
                "/immutableInput");
        }
    }

    private async ValueTask RunPackAsync(
        string sourceRoot,
        WorkspacePackageManifest manifest,
        string packOutput,
        CancellationToken cancellationToken)
    {
        var projects = manifest.Packages
            .Select(package => LocalOperationPaths.ResolveBelow(
                sourceRoot,
                package.SourceProjectPath,
                "A selected package project"))
            .Order(StringComparer.Ordinal)
            .ToArray();
        var packProject = LocalOperationPaths.ResolveBelow(
            sourceRoot,
            manifest.PackProjectPath,
            "The pack project");
        foreach (var project in projects)
        {
            var result = await processRunner.RunAsync(
                new CommandProcessRequest(
                    "dotnet",
                    sourceRoot,
                    [
                        "msbuild",
                        packProject,
                        "-target:Pack",
                        "-property:Configuration=Release",
                        string.Concat(
                            "-property:PackageOutputPath=",
                            packOutput),
                        string.Concat(
                            "-property:ProgramKitPackageProject=",
                            project),
                        "-property:ProgramKitCommandLineSelfPack=true",
                        "-property:IncludeSymbols=false",
                        "-verbosity:minimal",
                    ],
                    ImmutableDictionary<string, string>.Empty
                        .Add("DOTNET_NOLOGO", "1")
                        .Add("DOTNET_CLI_TELEMETRY_OPTOUT", "1")),
                cancellationToken).ConfigureAwait(false);
            if (result.ExitCode != 0)
            {
                throw Failure(
                    LocalOperationDiagnosticIds.PackagePreparationFailed,
                    ContainedProcessMessage(
                        string.Concat(
                            "Package preparation failed for ",
                            Path.GetFileName(project),
                            "."),
                        result),
                    "/packages");
            }
        }
    }

    private async ValueTask<ImmutableArray<LocalPackageEntry>>
        BuildPackageReportsAsync(
            string sourceRoot,
            string stagingRoot,
            string packOutput,
            ImmutableArray<WorkspacePackageEntry> selections,
            CancellationToken cancellationToken)
    {
        var reports = ImmutableArray.CreateBuilder<LocalPackageEntry>();
        var expectedPackFiles = new HashSet<string>(
            OperatingSystem.IsWindows()
                ? StringComparer.OrdinalIgnoreCase
                : StringComparer.Ordinal);
        foreach (var selection in selections.OrderBy(
                     static package => package.PackageRevision.Identity.Value,
                     StringComparer.Ordinal))
        {
            var packageId = selection.PackageId;
            var fileName = string.Concat(
                packageId,
                ".",
                selection.PackageRevision.Version.Value,
                ".nupkg");
            var packedPath = Path.Combine(packOutput, fileName);
            expectedPackFiles.Add(Path.GetFullPath(packedPath));
            if (!fileSystem.FileExists(packedPath))
            {
                throw Failure(
                    LocalOperationDiagnosticIds.PackageMismatch,
                    string.Concat(
                        "The pack did not produce the exact selected package: ",
                        fileName),
                    "/packages");
            }

            var packageBytes = await fileSystem.ReadAllBytesAsync(
                packedPath,
                cancellationToken).ConfigureAwait(false);
            var archive = archiveInspector.Inspect(
                packageBytes,
                packageId,
                selection.PackageRevision.Version.Value);
            var destination = LocalOperationPaths.ResolveBelow(
                stagingRoot,
                selection.PackageOutputPath,
                "A selected package output");
            await fileSystem.WriteAllBytesAsync(
                destination,
                packageBytes,
                cancellationToken).ConfigureAwait(false);
            reports.Add(
                new LocalPackageEntry(
                    selection.SourceProjectIdentity,
                    selection.SourceProjectPath,
                    selection.PackageRevision,
                    selection.PackageId,
                    selection.PackageRole,
                    selection.ExpectedTarget,
                    selection.PackageOutputPath,
                    packageBytes.Length,
                    LocalOperationHashes.Sha256(packageBytes.Span),
                    LocalOperationHashes.NuGetContentHash(packageBytes.Span),
                    archive.Dependencies,
                    archive.Contents));
        }

        var extras = fileSystem.EnumerateFiles(packOutput)
            .Where(path =>
                path.EndsWith(".nupkg", StringComparison.OrdinalIgnoreCase) &&
                !expectedPackFiles.Contains(Path.GetFullPath(path)))
            .ToArray();
        if (extras.Length != 0)
        {
            throw Failure(
                LocalOperationDiagnosticIds.PackageMismatch,
                "Package preparation produced an unselected nupkg.",
                "/packages");
        }

        return reports.ToImmutable();
    }

    private string ResolveRequiredFile(
        string sourceRoot,
        string relativePath,
        string path)
    {
        var resolved = LocalOperationPaths.ResolveBelow(
            sourceRoot,
            relativePath,
            "An explicit workspace path");
        if (!fileSystem.FileExists(resolved))
        {
            throw Failure(
                LocalOperationDiagnosticIds.InvalidWorkspaceManifest,
                "An explicit workspace file does not exist.",
                path);
        }

        return resolved;
    }

    private static bool ValidRevision(
        Orbyss.ProgramKit.Artifacts.References.ArtifactReference revision) =>
        revision is not null &&
        ProgramKitIdentifier.Validate(revision.Identity.Value).IsValid &&
        SemanticVersion.Validate(revision.Version.Value).IsValid &&
        Sha256Digest.Validate(revision.Digest.Value).IsValid;

    private static void EnsureOutputAbsent(string outputRoot)
    {
        try
        {
            LocalOperationPaths.EnsureOutputAbsent(outputRoot);
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
}
