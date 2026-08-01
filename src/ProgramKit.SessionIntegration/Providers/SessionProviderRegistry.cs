using System;
using System.Collections.Generic;
using System.Linq;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.SessionIntegration.Diagnostics;

namespace Orbyss.ProgramKit.SessionIntegration.Providers;

public sealed class SessionProviderRegistry
{
    private readonly IReadOnlyDictionary<string, ISessionProviderAdapter> providers;

    public SessionProviderRegistry(IEnumerable<ISessionProviderAdapter> providers)
    {
        Dictionary<string, ISessionProviderAdapter> explicitProviders = new(StringComparer.Ordinal);
        foreach (ISessionProviderAdapter provider in providers)
        {
            string key = provider.Manifest.ProviderIdentity.StableKey;
            if (!explicitProviders.TryAdd(key, provider))
                throw new InvalidOperationException($"Duplicate explicitly registered session provider: {key}");
        }

        this.providers = explicitProviders;
    }

    public IReadOnlyList<SessionProviderManifest> Catalog() =>
        providers.Values.Select(static provider => provider.Manifest).OrderBy(static manifest => manifest.ProviderIdentity.StableKey, StringComparer.Ordinal).ToArray();

    public ISessionProviderAdapter Resolve(GovernedIdentity selected)
    {
        if (!providers.TryGetValue(selected.StableKey, out ISessionProviderAdapter? provider))
            throw new SessionDiagnosticException(SessionDiagnosticCatalog.Id(2), OperationPhase.Resolution, EffectState.None, $"The explicitly selected provider is not registered: {selected.StableKey}");
        if (provider.Manifest.ProviderIdentity != selected)
            throw new SessionDiagnosticException(SessionDiagnosticCatalog.Id(2), OperationPhase.Resolution, EffectState.None, "The explicitly selected provider content identity is unavailable.");
        if (provider.Manifest.SupportClaim != SessionProviderSupport.Supported)
            throw new SessionDiagnosticException(SessionDiagnosticCatalog.Id(3), OperationPhase.Resolution, EffectState.None, $"The explicitly selected provider is not supported: {selected.StableKey}");
        return provider;
    }
}
