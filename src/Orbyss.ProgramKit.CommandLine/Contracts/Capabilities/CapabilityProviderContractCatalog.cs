using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Contracts.Capabilities;

/// <summary>
/// Exact provider contracts supported by project-scoped capability operations.
/// </summary>
public static class CapabilityProviderContractCatalog
{
    /// <summary>Gets the finite contracts in provider identifier order.</summary>
    public static ImmutableArray<CapabilityProviderContract> All { get; } =
    [
        new("claude", ".claude/skills/", null),
        new("codex", ".agents/skills/", ".codex/skills/"),
    ];

    /// <summary>Gets the exact finite provider identifiers.</summary>
    public static IReadOnlySet<string> ProviderIds { get; } =
        All.Select(static contract => contract.ProviderId)
            .ToImmutableHashSet(StringComparer.Ordinal);

    /// <summary>Finds one exact reviewed provider contract.</summary>
    public static bool TryGet(
        string? providerId,
        out CapabilityProviderContract contract)
    {
        contract = All.FirstOrDefault(
            candidate =>
                string.Equals(
                    candidate.ProviderId,
                    providerId,
                    StringComparison.Ordinal))!;
        return contract is not null;
    }
}
