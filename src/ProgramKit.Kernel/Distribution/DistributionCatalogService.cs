using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.Kernel.Distribution;

public sealed class DistributionCatalogService
{
    private readonly ProviderRegistry providers;

    public DistributionCatalogService(ProviderRegistry providers)
    {
        this.providers = providers;
    }

    public JsonObject Create(JsonObject distributionBinding)
    {
        JsonObject binding = DistributionDescriptor.ValidateBinding(distributionBinding);
        JsonArray providerEntries = new(providers.All.Select(ProviderEntry).ToArray());
        SchemaRegistry schemas = new();
        JsonObject schemaDigests = new(schemas.Digests.OrderBy(static item => item.Key, StringComparer.Ordinal)
            .Select(static item => KeyValuePair.Create<string, JsonNode?>(item.Key, item.Value)));
        JsonObject diagnostics = new();
        foreach (IFactoryProvider provider in providers.All)
            diagnostics[provider.Manifest.DiagnosticCatalog.Identity.StableKey] = provider.Manifest.DiagnosticCatalog.Digest;
        JsonObject canonicalProfiles = new()
        {
            [CanonicalJson.Profile] = Digests.Sha256(System.Text.Encoding.UTF8.GetBytes(CanonicalJson.Profile)),
        };
        JsonObject catalog = new()
        {
            ["schema"] = "program-kit.distribution-catalog/v1",
            ["canonicalProfile"] = CanonicalJson.Profile,
            ["distributionBinding"] = binding,
            ["providers"] = providerEntries,
            ["schemas"] = schemaDigests,
            ["diagnosticCatalogs"] = diagnostics,
            ["canonicalProfiles"] = canonicalProfiles,
            ["evidence"] = new JsonArray(providers.All.SelectMany(static provider => provider.Manifest.ConformanceEvidence).Select(ContractJson.Evidence).ToArray()),
        };
        catalog["digest"] = CanonicalJson.Digest(catalog);
        return catalog;
    }

    private static JsonObject ProviderEntry(IFactoryProvider provider) => new()
    {
        ["provider"] = ContractJson.Identity(provider.Manifest.Identity),
        ["distribution"] = ContractJson.Identity(provider.Manifest.Distribution),
        ["profiles"] = new JsonArray(provider.Manifest.Profiles.OrderBy(static value => value, StringComparer.Ordinal).Select(value => ContractJson.Identity(Profile(provider, value))).ToArray()),
        ["roles"] = new JsonArray(provider.Manifest.Roles.OrderBy(static value => value).Select(static value => JsonValue.Create(ContractJson.Kebab(value))).ToArray()),
        ["inputKinds"] = new JsonArray(provider.Manifest.InputKinds.OrderBy(static value => value, StringComparer.Ordinal).Select(static value => JsonValue.Create(value)).ToArray()),
        ["outputKinds"] = new JsonArray(provider.Manifest.OutputKinds.OrderBy(static value => value, StringComparer.Ordinal).Select(static value => JsonValue.Create(value)).ToArray()),
        ["effects"] = new JsonArray(provider.Manifest.FilesystemEffects.OrderBy(static value => value, StringComparer.Ordinal).Select(static value => JsonValue.Create(value)).ToArray()),
        ["processes"] = new JsonArray(provider.Manifest.Processes.OrderBy(static value => value, StringComparer.Ordinal).Select(static value => JsonValue.Create(value)).ToArray()),
        ["supportStatus"] = "supported",
        ["evidence"] = new JsonArray(provider.Manifest.ConformanceEvidence.Select(ContractJson.Evidence).ToArray()),
    };

    public static Orbyss.ProgramKit.Contracts.Identity.GovernedIdentity Profile(IFactoryProvider provider, string name) =>
        ContractJson.StableIdentity(provider.Manifest.Identity.Authority, "target-profile", name, "1.0.0", name);
}
