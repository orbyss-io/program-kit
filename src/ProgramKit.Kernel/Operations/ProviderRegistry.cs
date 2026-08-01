using System;
using System.Collections.Generic;
using System.Linq;
using Orbyss.ProgramKit.Contracts.Providers;

namespace Orbyss.ProgramKit.Kernel.Operations;

public sealed class ProviderRegistry
{
    private readonly IReadOnlyDictionary<string, IFactoryProvider> providers;

    public ProviderRegistry(IEnumerable<IFactoryProvider> providers)
    {
        this.providers = providers.ToDictionary(static provider => provider.Manifest.Identity.StableKey, StringComparer.Ordinal);
    }

    public IReadOnlyList<IFactoryProvider> All => providers.Values.OrderBy(static provider => provider.Manifest.Identity.StableKey, StringComparer.Ordinal).ToArray();

    public IFactoryProvider Resolve(string stableKey) => providers.TryGetValue(stableKey, out IFactoryProvider? provider)
        ? provider
        : throw new KeyNotFoundException($"No exact first-party provider is registered for {stableKey}.");
}
