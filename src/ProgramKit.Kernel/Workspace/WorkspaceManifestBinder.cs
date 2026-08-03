using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Identity;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Kernel.Distribution;
using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.Kernel.Validation;

namespace Orbyss.ProgramKit.Kernel.Workspace;

public sealed record BoundWorkspaceSelection(string Alias, IFactoryProvider Provider, GovernedIdentity Profile, GovernedIdentity Authority, JsonObject Document);
public sealed record BoundWorkspaceManifest(JsonObject Document, JsonObject Distribution, IReadOnlyList<BoundWorkspaceSelection> Selections, string? DefaultSelection);

public sealed class WorkspaceManifestBinder
{
    private readonly ProviderRegistry providers;

    public WorkspaceManifestBinder(ProviderRegistry providers)
    {
        this.providers = providers;
    }

    public BoundWorkspaceManifest Bind(JsonObject manifest)
    {
        Validate(ContractSchemaResources.WorkspaceManifestId, manifest);
        JsonObject distribution = DistributionDescriptor.ValidateBinding(manifest["distribution"]!.AsObject());
        JsonObject factory = manifest["factory"]!.AsObject();
        JsonArray selections = factory["selections"]!.AsArray();
        HashSet<string> aliases = new(StringComparer.OrdinalIgnoreCase);
        List<BoundWorkspaceSelection> bound = new();
        TypedContractBinder binder = new();
        foreach (JsonNode? node in selections)
        {
            JsonObject selection = node?.AsObject() ?? throw new InvalidDataException("Workspace selections must be objects.");
            string alias = selection["alias"]!.GetValue<string>();
            if (!aliases.Add(alias)) throw new InvalidDataException("Workspace selection aliases must be unique without case collisions.");
            GovernedIdentity providerIdentity = binder.BindIdentity(selection["provider"]!.AsObject());
            IFactoryProvider provider = providers.Resolve(providerIdentity.StableKey);
            if (!string.Equals(provider.Manifest.Identity.Digest, providerIdentity.Digest, StringComparison.Ordinal))
                throw new InvalidDataException("The selected provider digest is not exact.");
            GovernedIdentity profile = binder.BindIdentity(selection["targetProfile"]!.AsObject());
            GovernedIdentity expectedProfile = provider.Manifest.Profiles.Select(value => DistributionCatalogService.Profile(provider, value))
                .SingleOrDefault(value => string.Equals(value.StableKey, profile.StableKey, StringComparison.Ordinal))
                ?? throw new KeyNotFoundException("The exact selected target profile is unavailable.");
            if (!string.Equals(expectedProfile.Digest, profile.Digest, StringComparison.Ordinal))
                throw new InvalidDataException("The selected target profile digest is not exact.");
            GovernedIdentity authority = binder.BindIdentity(selection["selectionAuthority"]!.AsObject());
            bound.Add(new BoundWorkspaceSelection(alias, provider, profile, authority, (JsonObject)selection.DeepClone()));
        }

        string? defaultSelection = factory["defaultSelection"]?.GetValue<string>();
        if (defaultSelection is not null && !aliases.Contains(defaultSelection))
            throw new InvalidDataException("The workspace default selection must name exactly one declared selection.");
        return new BoundWorkspaceManifest((JsonObject)manifest.DeepClone(), distribution, bound.OrderBy(static item => item.Alias, StringComparer.Ordinal).ToArray(), defaultSelection);
    }

    private static void Validate(string schema, JsonObject document)
    {
        var failures = new StructuralSchemaValidator(new SchemaRegistry()).Validate(schema, document);
        if (failures.Count > 0) throw new InvalidDataException(string.Join(" | ", failures));
    }
}
