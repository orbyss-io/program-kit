using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;

namespace Orbyss.ProgramKit.SpecKitAdapter.Configuration;

public sealed record EffectiveSelection(string Alias, JsonObject Selection, string Source);

public static class SelectionResolver
{
    public static EffectiveSelection Resolve(JsonObject config, string featureKey, JsonObject workspaceLock)
    {
        JsonObject? feature = config["activation"]!["features"]?[featureKey] as JsonObject;
        string? explicitAlias = feature?["selection"]?.GetValue<string>();
        string? inheritedAlias = workspaceLock["defaultSelection"]?.GetValue<string>();
        string alias = explicitAlias ?? inheritedAlias ?? throw new InvalidDataException("An applicable feature requires an explicit or locked default selection.");
        JsonObject[] matches = workspaceLock["selections"]!.AsArray().OfType<JsonObject>()
            .Where(selection => string.Equals(selection["alias"]?.GetValue<string>(), alias, StringComparison.Ordinal))
            .ToArray();
        if (matches.Length != 1) throw new InvalidDataException("The effective selection alias must resolve exactly once in the current lock.");
        return new EffectiveSelection(alias, (JsonObject)matches[0].DeepClone(), explicitAlias is null ? "workspace-lock-default" : "feature-override");
    }
}
