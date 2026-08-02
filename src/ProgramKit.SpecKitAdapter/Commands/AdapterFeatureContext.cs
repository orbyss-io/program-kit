using System;
using System.IO;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Configuration;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Handoff;
using Orbyss.ProgramKit.SpecKitAdapter.Publication;

namespace Orbyss.ProgramKit.SpecKitAdapter.Commands;

public sealed record AdapterFeatureContext(
    string FeatureKey,
    ResolvedAdapterConfig Config,
    ApplicabilityResolution Applicability,
    JsonObject WorkspaceLock,
    BoundHandoff? Handoff,
    JsonObject? Review,
    TraceResolution? Trace);

public static class AdapterFeatureContextLoader
{
    public static AdapterFeatureContext Load(string workspaceRoot, JsonObject request, bool requireReviewedHandoff)
    {
        string featureKey = request["feature"]?["key"]?.GetValue<string>() ?? throw new InvalidDataException("A feature key is required.");
        string configPath = request["config"]?["logicalPath"]?.GetValue<string>() ?? throw new InvalidDataException("A config logicalPath is required.");
        ResolvedAdapterConfig config = new AdapterConfigResolver().Resolve(workspaceRoot, configPath);
        ApplicabilityResolution applicability = ApplicabilityResolver.Resolve(config.Document, featureKey);
        string lockLogical = config.Document["programKit"]!["lock"]!.GetValue<string>();
        string lockPath = LogicalPathPolicy.Resolve(workspaceRoot, lockLogical);
        JsonObject workspaceLock = File.Exists(lockPath)
            ? CanonicalDocument.Parse(File.ReadAllBytes(lockPath)).AsObject()
            : new JsonObject();
        if (!requireReviewedHandoff || !applicability.Active)
            return new AdapterFeatureContext(featureKey, config, applicability, workspaceLock, null, null, null);

        string handoffLogical = request["handoff"]?["logicalPath"]?.GetValue<string>() ?? $"specs/{featureKey}/program-kit/handoff.yaml";
        string reviewLogical = request["review"]?["logicalPath"]?.GetValue<string>() ?? $"specs/{featureKey}/program-kit/handoff-review.json";
        string handoffPath = LogicalPathPolicy.Resolve(workspaceRoot, handoffLogical);
        string reviewPath = LogicalPathPolicy.Resolve(workspaceRoot, reviewLogical);
        if (!File.Exists(handoffPath) || !File.Exists(reviewPath)) throw new InvalidDataException("The reviewed feature handoff is incomplete.");
        BoundHandoff handoff = new HandoffBinder().Bind(RestrictedYaml.Parse(File.ReadAllText(handoffPath)), requireComplete: true);
        EffectiveSelection selection = SelectionResolver.Resolve(config.Document, featureKey, workspaceLock);
        if (!string.Equals(handoff.Document["effectiveSelection"]?["alias"]?.GetValue<string>(), selection.Alias, StringComparison.Ordinal))
            throw new InvalidDataException("The reviewed handoff selection differs from the current effective selection.");
        JsonObject review = CanonicalDocument.Parse(File.ReadAllBytes(reviewPath)).AsObject();
        TraceResolution trace = HandoffReviewValidator.Validate(workspaceRoot, handoff, review);
        return new AdapterFeatureContext(featureKey, config, applicability, workspaceLock, handoff, review, trace);
    }
}
