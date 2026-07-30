using System.Collections.Immutable;
using System.Security.Cryptography;
using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Capabilities;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;
using Orbyss.ProgramKit.CommandLine.Contracts.Product;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Payload;
using Orbyss.ProgramKit.CommandLine.Operations.Files;
using Orbyss.ProgramKit.CommandLine.Operations.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Readiness;

/// <summary>Exact lock, payload, provider, wrapper, and closure preflight.</summary>
public sealed class CapabilityReadinessService : ICapabilityReadinessService
{
    private const string AuthoringMarker =
        ".agent-capabilities/authoring-workspace.json";
    private const string LockPath = ".program-kit/capabilities.lock.json";
    private const string TransactionPath =
        CapabilityWorkspaceTransaction.TransactionDirectory;
    private const int MaximumLockBytes = 256 * 1024;
    private const int MaximumWrapperBytes = 512 * 1024;
    private readonly ICommandFileSystem fileSystem;
    private readonly IConsumerCapabilityPayload payload;
    private readonly ICapabilityInitializationLockSerializer lockSerializer;

    /// <summary>Initializes the exact read-only readiness boundary.</summary>
    public CapabilityReadinessService(
        ICommandFileSystem fileSystem,
        IConsumerCapabilityPayload payload,
        ICapabilityInitializationLockSerializer lockSerializer)
    {
        this.fileSystem = fileSystem ??
            throw new ArgumentNullException(nameof(fileSystem));
        this.payload = payload ??
            throw new ArgumentNullException(nameof(payload));
        this.lockSerializer = lockSerializer ??
            throw new ArgumentNullException(nameof(lockSerializer));
    }

    /// <inheritdoc />
    public async ValueTask<CapabilityReadinessResult> EvaluateAsync(
        string capabilityId,
        string workspaceRoot,
        CancellationToken cancellationToken)
    {
        var catalog = payload.ResolveCatalogEntry(capabilityId);
        if (!string.Equals(
                catalog.Availability,
                "available",
                StringComparison.Ordinal))
        {
            return new CapabilityReadinessResult(
                catalog.CapabilityId,
                catalog.Role,
                catalog.Availability,
                false,
                false,
                "unavailable",
                catalog.Reason,
                []);
        }

        var workspace = ResolveWorkspace(workspaceRoot);
        var setup = await VerifyWorkspaceAsync(
            workspace,
            cancellationToken).ConfigureAwait(false);
        if (!setup.Ready)
        {
            return new CapabilityReadinessResult(
                catalog.CapabilityId,
                catalog.Role,
                catalog.Availability,
                setup.Providers.Length != 0,
                false,
                "setup-required",
                setup.Reason,
                setup.Providers);
        }

        return new CapabilityReadinessResult(
            catalog.CapabilityId,
            catalog.Role,
            catalog.Availability,
            true,
            true,
            "ready",
            "The installed payload, complete closure, lock, providers, and wrappers match exact recorded bytes.",
            setup.Providers);
    }

    /// <inheritdoc />
    public async ValueTask<ImmutableArray<CapabilityReadinessResult>> CatalogAsync(
        string workspaceRoot,
        CancellationToken cancellationToken)
    {
        var builder = ImmutableArray.CreateBuilder<CapabilityReadinessResult>();
        foreach (var entry in payload.Catalog)
        {
            builder.Add(
                await EvaluateAsync(
                    entry.CapabilityId,
                    workspaceRoot,
                    cancellationToken).ConfigureAwait(false));
        }

        return builder.ToImmutable();
    }

    /// <inheritdoc />
    public async ValueTask<ReadOnlyMemory<byte>> ReadCapabilityAsync(
        string capabilityId,
        string workspaceRoot,
        CancellationToken cancellationToken)
    {
        var readiness = await EvaluateAsync(
            capabilityId,
            workspaceRoot,
            cancellationToken).ConfigureAwait(false);
        RequireReady(readiness);
        return payload.ReadCapability(capabilityId);
    }

    /// <inheritdoc />
    public async ValueTask<ReadOnlyMemory<byte>> ReadResourceAsync(
        string resourceId,
        string workspaceRoot,
        CancellationToken cancellationToken)
    {
        var workspace = ResolveWorkspace(workspaceRoot);
        var setup = await VerifyWorkspaceAsync(
            workspace,
            cancellationToken).ConfigureAwait(false);
        if (!setup.Ready)
        {
            throw SetupRequired(setup.Reason);
        }

        return payload.ReadResource(resourceId);
    }

    private async ValueTask<WorkspaceSetup> VerifyWorkspaceAsync(
        string workspace,
        CancellationToken cancellationToken)
    {
        if (fileSystem.FileExists(ResolveUnder(workspace, AuthoringMarker)))
        {
            return WorkspaceSetup.Blocked(
                "The Program Kit source authoring marker rejects consumer capability retrieval.");
        }

        if (fileSystem.DirectoryExists(
                ResolveUnder(workspace, TransactionPath)))
        {
            return WorkspaceSetup.Blocked(
                "A capability transaction is in progress or interrupted; explicit initialization must close it before use.");
        }

        var lockPath = ResolveUnder(workspace, LockPath);
        if (!fileSystem.FileExists(lockPath))
        {
            return WorkspaceSetup.Blocked(
                "No current workspace capability lock exists. Run capabilities initialize.");
        }

        ReadOnlyMemory<byte> bytes;
        try
        {
            if (fileSystem.GetFileSize(lockPath) > MaximumLockBytes)
            {
                return WorkspaceSetup.Blocked(
                    "The workspace capability lock exceeds its byte limit.");
            }

            bytes = await fileSystem.ReadAllBytesAsync(
                lockPath,
                cancellationToken).ConfigureAwait(false);
        }
        catch (IOException)
        {
            return WorkspaceSetup.Blocked(
                "The workspace capability lock cannot be read.");
        }

        CapabilityInitializationLock value;
        try
        {
            var version = lockSerializer.ReadVersion(bytes.Span);
            if (!string.Equals(
                    version,
                    ProgramKitProductInfo.CapabilityLockVersion,
                    StringComparison.Ordinal))
            {
                return WorkspaceSetup.Blocked(
                    "The workspace has a legacy or unsupported lock. Run explicit capabilities initialize to migrate it.");
            }

            value = lockSerializer.Read(bytes.Span);
        }
        catch (Exception exception)
            when (exception is JsonException or InvalidOperationException or
                KeyNotFoundException)
        {
            return WorkspaceSetup.Blocked(
                "The workspace capability lock is invalid.");
        }

        var providers = value.Providers?
            .Select(static item => item.Provider)
            .Order(StringComparer.Ordinal)
            .ToImmutableArray() ?? [];
        var headerFailure = ValidateHeader(value);
        if (headerFailure is not null)
        {
            return WorkspaceSetup.Blocked(headerFailure, providers);
        }

        var resourceFailure = ValidateResources(value);
        if (resourceFailure is not null)
        {
            return WorkspaceSetup.Blocked(resourceFailure, providers);
        }

        var providerFailure = await ValidateProvidersAsync(
            workspace,
            value,
            cancellationToken).ConfigureAwait(false);
        return providerFailure is null
            ? WorkspaceSetup.Verified(providers)
            : WorkspaceSetup.Blocked(providerFailure, providers);
    }

    private string? ValidateHeader(CapabilityInitializationLock value)
    {
        if (!string.Equals(
                value.LockVersion,
                ProgramKitProductInfo.CapabilityLockVersion,
                StringComparison.Ordinal))
        {
            return "The workspace lock format is unsupported.";
        }

        if (!string.Equals(
                value.CliVersion,
                ProgramKitProductInfo.Version,
                StringComparison.Ordinal))
        {
            return string.Concat(
                "Workspace lock CLI version '",
                value.CliVersion,
                "' differs from installed CLI '",
                ProgramKitProductInfo.Version,
                "'. Run explicit capabilities initialize after selecting the exact version.");
        }

        if (!string.Equals(
                value.BundleVersion,
                payload.Manifest.BundleVersion,
                StringComparison.Ordinal) ||
            !string.Equals(
                value.ManifestVersion,
                payload.Manifest.ManifestVersion,
                StringComparison.Ordinal) ||
            !string.Equals(
                value.ManifestSha256,
                payload.ManifestSha256,
                StringComparison.Ordinal))
        {
            return "The workspace lock payload version or manifest digest is stale.";
        }

        return null;
    }

    private string? ValidateResources(CapabilityInitializationLock value)
    {
        if (value.Resources is null)
        {
            return "The workspace lock has no supporting-resource evidence.";
        }

        var expected = payload.Manifest.SupportingResources
            .OrderBy(static item => item.ResourceId, StringComparer.Ordinal)
            .Select(static item => string.Concat(item.ResourceId, "#", item.Sha256))
            .ToArray();
        var actual = value.Resources
            .OrderBy(static item => item.ResourceId, StringComparer.Ordinal)
            .Select(static item => string.Concat(item.ResourceId, "#", item.Sha256))
            .ToArray();
        return actual.SequenceEqual(expected, StringComparer.Ordinal)
            ? null
            : "The workspace lock supporting-resource closure is stale or incomplete.";
    }

    private async ValueTask<string?> ValidateProvidersAsync(
        string workspace,
        CapabilityInitializationLock value,
        CancellationToken cancellationToken)
    {
        if (value.Providers is null ||
            value.Providers.Length == 0 ||
            value.Providers.GroupBy(
                    static item => item.Provider,
                    StringComparer.Ordinal)
                .Any(static group => group.Count() != 1))
        {
            return "The workspace lock has no unique active provider registrations.";
        }

        foreach (var provider in value.Providers)
        {
            if (!CapabilityProviderContractCatalog.TryGet(
                    provider.Provider,
                    out var contract) ||
                provider.Capabilities is null)
            {
                return "The workspace lock contains an unsupported provider.";
            }

            var root = contract.ProjectSkillRoot;
            var expectedIds = payload.Manifest.Capabilities
                .Select(static item => item.CapabilityId)
                .Order(StringComparer.Ordinal)
                .ToArray();
            var actualIds = provider.Capabilities
                .Select(static item => item.CapabilityId)
                .Order(StringComparer.Ordinal)
                .ToArray();
            if (!actualIds.SequenceEqual(expectedIds, StringComparer.Ordinal))
            {
                return string.Concat(
                    "Provider '",
                    provider.Provider,
                    "' has an incomplete capability registration.");
            }

            foreach (var capability in payload.Manifest.Capabilities)
            {
                var locked = provider.Capabilities.Single(
                    entry => string.Equals(
                        entry.CapabilityId,
                        capability.CapabilityId,
                        StringComparison.Ordinal));
                var adapter = payload.Manifest.OptionalProviderAdapters.Single(
                    item =>
                        string.Equals(
                            item.Provider,
                            provider.Provider,
                            StringComparison.Ordinal) &&
                        string.Equals(
                            item.CapabilityId,
                            capability.CapabilityId,
                            StringComparison.Ordinal));
                var expectedPath = string.Concat(
                    root,
                    capability.CapabilityId,
                    "/SKILL.md");
                var expectedOutput = payload.ReadAdapter(
                    provider.Provider,
                    capability.CapabilityId);
                var expectedOutputDigest = Digest(expectedOutput.Span);
                if (!string.Equals(
                        locked.CanonicalSha256,
                        capability.Sha256,
                        StringComparison.Ordinal) ||
                    !string.Equals(
                        locked.AdapterTemplateSha256,
                        adapter.Sha256,
                        StringComparison.Ordinal) ||
                    !string.Equals(
                        locked.OutputPath,
                        expectedPath,
                        StringComparison.Ordinal) ||
                    !string.Equals(
                        locked.OutputSha256,
                        expectedOutputDigest,
                        StringComparison.Ordinal))
                {
                    return string.Concat(
                        "Provider '",
                        provider.Provider,
                        "' lock evidence is stale for '",
                        capability.CapabilityId,
                        "'.");
                }

                var outputPath = ResolveUnder(workspace, expectedPath);
                if (!fileSystem.FileExists(outputPath) ||
                    fileSystem.GetFileSize(outputPath) > MaximumWrapperBytes)
                {
                    return string.Concat(
                        "Provider wrapper '",
                        expectedPath,
                        "' is missing or exceeds its byte limit.");
                }

                var bytes = await fileSystem.ReadAllBytesAsync(
                    outputPath,
                    cancellationToken).ConfigureAwait(false);
                if (!string.Equals(
                        Digest(bytes.Span),
                        locked.OutputSha256,
                        StringComparison.Ordinal))
                {
                    return string.Concat(
                        "Provider wrapper '",
                        expectedPath,
                        "' was modified after initialization.");
                }
            }
        }

        return null;
    }

    private string ResolveWorkspace(string value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new CommandInvocationException(
                "An explicit workspace root is required.",
                "/workspaceRoot");
        }

        var full = Path.TrimEndingDirectorySeparator(Path.GetFullPath(value));
        if (!fileSystem.DirectoryExists(full))
        {
            throw new CommandInvocationException(
                "The explicit workspace root does not exist.",
                "/workspaceRoot");
        }

        var root = Path.GetPathRoot(full);
        if (root is not null &&
            string.Equals(
                full,
                Path.TrimEndingDirectorySeparator(root),
                PathComparison()))
        {
            throw new CommandInvocationException(
                "A filesystem root cannot be used as a capability workspace.",
                "/workspaceRoot");
        }

        return full;
    }

    private static string ResolveUnder(string root, string relativePath)
    {
        var full = Path.GetFullPath(
            Path.Combine(
                root,
                relativePath.Replace('/', Path.DirectorySeparatorChar)));
        if (!full.StartsWith(
                string.Concat(root, Path.DirectorySeparatorChar),
                PathComparison()))
        {
            throw new CommandInvocationException(
                "A capability path escapes the selected workspace.",
                "/workspaceRoot");
        }

        return full;
    }

    private static void RequireReady(CapabilityReadinessResult result)
    {
        if (string.Equals(result.State, "ready", StringComparison.Ordinal))
        {
            return;
        }

        if (string.Equals(result.State, "unavailable", StringComparison.Ordinal))
        {
            throw new CapabilityOperationException(
                CommandExitCode.UsageOrInputFailure,
                CommandDiagnosticIds.CapabilityUnavailable,
                "/capability",
                result.Reason);
        }

        throw SetupRequired(result.Reason);
    }

    private static CapabilityOperationException SetupRequired(string reason) =>
        new(
            CommandExitCode.ConformanceFailure,
            CommandDiagnosticIds.CapabilitySetupRequired,
            "/workspace",
            reason);

    private static StringComparison PathComparison() =>
        OperatingSystem.IsWindows()
            ? StringComparison.OrdinalIgnoreCase
            : StringComparison.Ordinal;

    private static string Digest(ReadOnlySpan<byte> content) =>
        string.Concat(
            "sha256:",
            Convert.ToHexString(SHA256.HashData(content)).ToLowerInvariant());

}
