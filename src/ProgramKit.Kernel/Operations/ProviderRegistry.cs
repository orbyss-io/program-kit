using System;
using System.Collections.Generic;
using System.Linq;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Providers;

namespace Orbyss.ProgramKit.Kernel.Operations;

public sealed class ProviderRegistry
{
    private readonly IReadOnlyDictionary<string, IFactoryProvider> providers;

    public ProviderRegistry(IEnumerable<IFactoryProvider> providers)
    {
        Dictionary<string, IFactoryProvider> exact = new(StringComparer.Ordinal);
        foreach (IFactoryProvider provider in providers)
        {
            ValidateRoleClosure(provider);
            if (!exact.TryAdd(provider.Manifest.Identity.StableKey, provider))
            {
                throw new InvalidOperationException($"Duplicate exact provider identity: {provider.Manifest.Identity.StableKey}");
            }
        }

        this.providers = exact;
    }

    public IReadOnlyList<IFactoryProvider> All => providers.Values
        .OrderBy(static provider => provider.Manifest.Identity.StableKey, StringComparer.Ordinal)
        .ToArray();

    public IFactoryProvider Resolve(string stableKey) => providers.TryGetValue(stableKey, out IFactoryProvider? provider)
        ? provider
        : throw new KeyNotFoundException($"No exact first-party provider is registered for {stableKey}.");

    public TProvider ResolveRole<TProvider>(IReadOnlyList<ExactSelection> selections, ProviderRole role)
        where TProvider : class, IFactoryProvider
    {
        string roleName = Kebab(role);
        ExactSelection[] matches = selections.Where(selection => string.Equals(selection.Role, roleName, StringComparison.Ordinal)).ToArray();
        if (matches.Length != 1)
        {
            throw new KeyNotFoundException($"Exactly one {roleName} provider selection is required; observed {matches.Length}.");
        }

        ExactSelection selection = matches[0];
        IFactoryProvider provider = Resolve(selection.Selected.StableKey);
        if (!string.Equals(provider.Manifest.Identity.Digest, selection.Selected.Digest, StringComparison.Ordinal)
            || !provider.Manifest.Roles.Contains(role)
            || provider is not TProvider typed)
        {
            throw new KeyNotFoundException($"The exact {roleName} provider selection is unavailable or does not implement its advertised role.");
        }

        return typed;
    }

    private static void ValidateRoleClosure(IFactoryProvider provider)
    {
        ProviderRole[] implemented = new[]
        {
            provider is IIntakeMappingProvider ? ProviderRole.IntakeMapping : (ProviderRole?)null,
            provider is IConstructionProvider ? ProviderRole.Construction : (ProviderRole?)null,
            provider is IEvaluationProvider ? ProviderRole.Evaluation : (ProviderRole?)null,
        }.Where(static role => role.HasValue).Select(static role => role!.Value).ToArray();
        ProviderRole[] declared = provider.Manifest.Roles.Distinct().OrderBy(static role => role).ToArray();
        if (!declared.SequenceEqual(implemented.OrderBy(static role => role)))
        {
            throw new InvalidOperationException($"Provider {provider.Manifest.Identity.StableKey} role manifest does not match its callable SPI surfaces.");
        }
    }

    private static string Kebab(ProviderRole role) => role switch
    {
        ProviderRole.IntakeMapping => "intake-mapping",
        ProviderRole.Construction => "construction",
        ProviderRole.Evaluation => "evaluation",
        _ => throw new ArgumentOutOfRangeException(nameof(role)),
    };
}
