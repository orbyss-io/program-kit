using System.IO;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Configuration;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Diagnostics;
using Orbyss.ProgramKit.SpecKitAdapter.Handoff;
using Orbyss.ProgramKit.SpecKitAdapter.Publication;

namespace Orbyss.ProgramKit.SpecKitAdapter.Commands;

public sealed record AdapterFeatureContext(
    string FeatureKey,
    ResolvedAdapterConfig Config,
    ApplicabilityResolution Applicability,
    JsonObject WorkspaceLock,
    EffectiveSelection? Selection,
    BoundHandoff? Handoff,
    JsonObject? Review,
    TraceResolution? Trace);

public static class AdapterFeatureContextLoader
{
    public static AdapterFeatureContext Load(string workspaceRoot, JsonObject request, bool requireReviewedHandoff)
    {
        string featureKey = request["feature"]?["key"]?.GetValue<string>() ?? throw new InvalidDataException("A feature key is required.");
        string configPath = request["config"]?["logicalPath"]?.GetValue<string>() ?? throw new InvalidDataException("A config logicalPath is required.");
        ResolvedAdapterConfig config;
        try
        {
            config = new AdapterConfigResolver().Resolve(workspaceRoot, configPath);
        }
        catch (InvalidDataException exception)
        {
            throw new AdapterBoundaryException(AdapterFailureKind.InvalidConfiguration, "The adapter configuration is invalid.", innerException: exception);
        }
        ApplicabilityResolution applicability = ApplicabilityResolver.Resolve(config.Document, featureKey);
        if (!applicability.Active)
            return new AdapterFeatureContext(featureKey, config, applicability, new JsonObject(), null, null, null, null);
        string lockLogical = config.Document["programKit"]!["lock"]!.GetValue<string>();
        string lockPath = LogicalPathPolicy.Resolve(workspaceRoot, lockLogical);
        JsonObject workspaceLock = File.Exists(lockPath)
            ? CanonicalDocument.Parse(File.ReadAllBytes(lockPath)).AsObject()
            : new JsonObject();
        if (!requireReviewedHandoff)
            return new AdapterFeatureContext(featureKey, config, applicability, workspaceLock, null, null, null, null);

        string handoffLogical = request["handoff"]?["logicalPath"]?.GetValue<string>() ?? $"specs/{featureKey}/program-kit/handoff.yaml";
        string reviewLogical = request["review"]?["logicalPath"]?.GetValue<string>() ?? $"specs/{featureKey}/program-kit/handoff-review.json";
        string handoffPath = LogicalPathPolicy.Resolve(workspaceRoot, handoffLogical);
        string reviewPath = LogicalPathPolicy.Resolve(workspaceRoot, reviewLogical);
        if (!File.Exists(handoffPath) || !File.Exists(reviewPath))
            throw new AdapterBoundaryException(AdapterFailureKind.InvalidHandoff, "The reviewed feature handoff is incomplete.");
        BoundHandoff handoff;
        try
        {
            handoff = new HandoffBinder().Bind(RestrictedYaml.Parse(File.ReadAllText(handoffPath)), requireComplete: true);
        }
        catch (InvalidDataException exception)
        {
            throw new AdapterBoundaryException(AdapterFailureKind.InvalidHandoff, "The feature handoff is invalid.", innerException: exception);
        }

        EffectiveSelection selection;
        try
        {
            selection = SelectionResolver.ResolvePinned(config.Document, featureKey, workspaceLock, handoff.Document["effectiveSelection"]!.AsObject());
        }
        catch (InvalidDataException exception)
        {
            throw new AdapterBoundaryException(AdapterFailureKind.InvalidSelection, "The reviewed selection is invalid.", "needs-input", exception);
        }

        JsonObject review;
        TraceResolution trace;
        try
        {
            review = CanonicalDocument.Parse(File.ReadAllBytes(reviewPath)).AsObject();
            trace = HandoffReviewValidator.Validate(workspaceRoot, handoff, review);
        }
        catch (AdapterBoundaryException)
        {
            throw;
        }
        catch (InvalidDataException exception)
        {
            throw new AdapterBoundaryException(AdapterFailureKind.InvalidReview, "The handoff review is invalid.", "needs-input", exception);
        }
        return new AdapterFeatureContext(featureKey, config, applicability, workspaceLock, selection, handoff, review, trace);
    }
}
