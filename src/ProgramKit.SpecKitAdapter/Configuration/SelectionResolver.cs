using System;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;

namespace Orbyss.ProgramKit.SpecKitAdapter.Configuration;

public sealed record EffectiveSelection(
    string Alias,
    JsonObject Selection,
    string Source,
    bool Diverged = false,
    string? CurrentAlias = null,
    string? CurrentSource = null);

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

    public static EffectiveSelection ResolvePinned(JsonObject config, string featureKey, JsonObject workspaceLock, JsonObject binding)
    {
        string alias = binding["alias"]?.GetValue<string>() ?? throw new InvalidDataException("A reviewed handoff has no pinned selection alias.");
        string source = binding["source"]?.GetValue<string>() ?? throw new InvalidDataException("A reviewed handoff has no pinned selection source.");
        if (source is not ("feature-override" or "workspace-lock-default"))
            throw new InvalidDataException("A reviewed handoff selection source must be explicit or inherited from the workspace lock.");
        JsonObject pinned = binding["selection"] as JsonObject ?? throw new InvalidDataException("A reviewed handoff has no exact pinned selection.");
        if (!string.Equals(pinned["alias"]?.GetValue<string>(), alias, StringComparison.Ordinal))
            throw new InvalidDataException("The pinned selection alias is internally inconsistent.");
        JsonObject[] matches = workspaceLock["selections"]!.AsArray().OfType<JsonObject>()
            .Where(selection => string.Equals(selection["alias"]?.GetValue<string>(), alias, StringComparison.Ordinal))
            .ToArray();
        if (matches.Length != 1 || !Contracts.CanonicalDocument.Encode(matches[0]).SequenceEqual(Contracts.CanonicalDocument.Encode(pinned)))
            throw new InvalidDataException("The reviewed exact selection is unavailable or changed in the current workspace lock.");

        EffectiveSelection current = Resolve(config, featureKey, workspaceLock);
        bool diverged = !string.Equals(current.Alias, alias, StringComparison.Ordinal)
            || !string.Equals(current.Source, source, StringComparison.Ordinal);
        return new EffectiveSelection(alias, (JsonObject)pinned.DeepClone(), source, diverged, current.Alias, current.Source);
    }
}
