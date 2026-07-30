using Orbyss.ProgramKit.CommandLine.Contracts;
using Orbyss.ProgramKit.CommandLine.Contracts.Capabilities;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

/// <summary>Fail-closed semantic validation for capability ownership locks.</summary>
public static class CapabilityInitializationLockVerifier
{
    private static readonly string[] DistributedCapabilityIds =
    [
        "design-csharp-build-gate",
        "design-software",
        "develop-software",
        "implement-software-plan",
        "maintain-software",
    ];

    /// <summary>Validates the complete exact ownership set.</summary>
    public static void Verify(CapabilityInitializationLock value)
    {
        ArgumentNullException.ThrowIfNull(value);
        if (value.LockVersion is not ("1.0.0" or "2.0.0") ||
            value.Providers is null ||
            value.Providers.Length is < 1 or > 2 ||
            value.Providers.Any(static provider => provider is null) ||
            value.LockVersion == "1.0.0" && value.Providers.Length != 1)
        {
            throw InvalidLock();
        }

        var providerIds = value.Providers
            .Select(static provider => provider.Provider)
            .ToArray();
        var sortedProviderIds = providerIds
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (!sortedProviderIds.SequenceEqual(
                sortedProviderIds.Distinct(StringComparer.Ordinal),
                StringComparer.Ordinal) ||
            value.LockVersion == "2.0.0" &&
            !providerIds.SequenceEqual(
                sortedProviderIds,
                StringComparer.Ordinal))
        {
            throw InvalidLock();
        }

        var outputPaths = new HashSet<string>(StringComparer.Ordinal);
        foreach (var provider in value.Providers)
        {
            VerifyProvider(provider, value.LockVersion, outputPaths);
        }
    }

    private static void VerifyProvider(
        CapabilityProviderInitializationLock provider,
        string lockVersion,
        HashSet<string> outputPaths)
    {
        if (!CapabilityProviderContractCatalog.TryGet(
                provider.Provider,
                out var contract) ||
            !IsSupportedBundleVersion(provider.BundleVersion) ||
            !IsDigest(provider.ManifestSha256) ||
            !IsSafeStoredRelativePath(
                provider.ProgramKitRoot,
                allowCurrentDirectory: true))
        {
            throw InvalidLock();
        }

        var expectedCapabilityIds = ExpectedCapabilityIds(
            provider.BundleVersion);
        if (provider.Capabilities is null ||
            provider.Capabilities.Length != expectedCapabilityIds.Length)
        {
            throw InvalidLock();
        }

        var actualIds = provider.Capabilities
            .Select(static entry => entry?.CapabilityId)
            .ToArray();
        if (lockVersion == "2.0.0" &&
            !actualIds.SequenceEqual(
                expectedCapabilityIds,
                StringComparer.Ordinal) ||
            lockVersion == "1.0.0" &&
            !actualIds
                .Order(StringComparer.Ordinal)
                .SequenceEqual(
                    expectedCapabilityIds,
                    StringComparer.Ordinal))
        {
            throw InvalidLock();
        }

        var root = SelectOutputRoot(provider, contract);
        foreach (var entry in provider.Capabilities)
        {
            if (entry is null ||
                !string.Equals(
                    entry.OutputPath,
                    string.Concat(
                        root,
                        entry.CapabilityId,
                        "/SKILL.md"),
                    StringComparison.Ordinal) ||
                !outputPaths.Add(entry.OutputPath) ||
                !IsSafeStoredRelativePath(
                    entry.CanonicalPath,
                    allowCurrentDirectory: false) ||
                !IsDigest(entry.CanonicalSha256) ||
                !IsDigest(entry.AdapterTemplateSha256) ||
                !IsDigest(entry.OutputSha256))
            {
                throw InvalidLock();
            }
        }
    }

    private static string SelectOutputRoot(
        CapabilityProviderInitializationLock provider,
        CapabilityProviderContract contract)
    {
        if (provider.Capabilities.All(
                entry =>
                    entry.OutputPath.StartsWith(
                        contract.ProjectSkillRoot,
                        StringComparison.Ordinal)))
        {
            return contract.ProjectSkillRoot;
        }

        if (contract.LegacyProjectSkillRoot is not null &&
            provider.Capabilities.All(
                entry =>
                    entry.OutputPath.StartsWith(
                        contract.LegacyProjectSkillRoot,
                        StringComparison.Ordinal)))
        {
            return contract.LegacyProjectSkillRoot;
        }

        throw InvalidLock();
    }

    private static string[] ExpectedCapabilityIds(string bundleVersion) =>
        bundleVersion switch
        {
            "2.0.0" =>
            [
                "design-software",
                "develop-software",
                "implement-software-plan",
            ],
            "2.1.0" or "2.2.0" =>
            [
                "design-csharp-build-gate",
                "design-software",
                "develop-software",
                "implement-software-plan",
            ],
            "3.0.0" or "4.0.0" => DistributedCapabilityIds,
            _ => [],
        };

    private static bool IsSupportedBundleVersion(string value) =>
        value is "2.0.0" or "2.1.0" or "2.2.0" or "3.0.0" or "4.0.0";

    private static bool IsDigest(string value)
    {
        if (value is null ||
            value.Length != 71 ||
            !value.StartsWith("sha256:", StringComparison.Ordinal))
        {
            return false;
        }

        foreach (var character in value.AsSpan(7))
        {
            if (character is not (>= '0' and <= '9') and
                not (>= 'a' and <= 'f'))
            {
                return false;
            }
        }

        return true;
    }

    private static bool IsSafeStoredRelativePath(
        string value,
        bool allowCurrentDirectory)
    {
        if (allowCurrentDirectory &&
            string.Equals(value, ".", StringComparison.Ordinal))
        {
            return true;
        }

        return !string.IsNullOrWhiteSpace(value) &&
            !Path.IsPathRooted(value) &&
            !value.Contains('\\') &&
            !value.Any(char.IsControl) &&
            value.Split('/').All(
                static segment =>
                    !string.IsNullOrWhiteSpace(segment) &&
                    segment is not "." and not "..");
    }

    private static CapabilityOperationException InvalidLock() =>
        new(
            CommandExitCode.ConformanceFailure,
            CommandDiagnosticIds.InvalidCapabilityInitialization,
            "/lock",
            "The existing Program Kit capability ownership lock is unsupported.");
}
