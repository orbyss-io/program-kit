using System;
using System.Collections.Generic;
using System.Linq;
using Orbyss.ProgramKit.Contracts.SessionIntegration;
using Orbyss.ProgramKit.Contracts.Operations;
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

    public IReadOnlyList<SessionProviderManifest> Catalog() => providers.Values.Select(static provider => provider.Manifest).OrderBy(static manifest => manifest.ProviderIdentity.StableKey, StringComparer.Ordinal).ToArray();

    public ISessionProviderAdapter Resolve(string stableKey, string requiredRevision)
    {
        if (!providers.TryGetValue(stableKey, out ISessionProviderAdapter? provider))
            throw new SessionDiagnosticException(SessionDiagnosticCatalog.Id(2), OperationPhase.Resolution, EffectState.None, $"The explicitly selected provider is not registered: {stableKey}");
        if (provider.Manifest.SupportClaim != SessionProviderSupport.Supported)
            throw new SessionDiagnosticException(SessionDiagnosticCatalog.Id(3), OperationPhase.Resolution, EffectState.None, $"The explicitly selected provider is not supported: {stableKey}");
        if (!string.Equals(provider.Manifest.Revision, requiredRevision, StringComparison.Ordinal))
            throw new SessionDiagnosticException(SessionDiagnosticCatalog.Id(3), OperationPhase.Resolution, EffectState.None, $"The provider revision is incompatible. Required {requiredRevision}; registered {provider.Manifest.Revision}.");
        return provider;
    }
}
