using System.IO;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Handoff;
using Orbyss.ProgramKit.SpecKitAdapter.Publication;

namespace Orbyss.ProgramKit.SpecKitAdapter.Commands;

public static class HandoffCommand
{
    public static JsonObject Execute(string workspaceRoot, JsonObject request)
    {
        AdapterFeatureContext context = AdapterFeatureContextLoader.Load(workspaceRoot, request, requireReviewedHandoff: false);
        if (!context.Applicability.Active)
            return AdapterResultWriter.NotApplicable(Contracts.AdapterOperation.Handoff, new JsonObject { ["applicability"] = context.Applicability.Applicability.ToString().ToLowerInvariant(), ["blocking"] = context.Applicability.BlocksWorkflow });
        string logicalPath = $"specs/{context.FeatureKey}/program-kit/handoff.yaml";
        string path = LogicalPathPolicy.Resolve(workspaceRoot, logicalPath);
        if (!File.Exists(path))
            return AdapterResultWriter.Success(Contracts.AdapterOperation.Handoff, new JsonObject { ["proposal"] = HandoffProposalBuilder.Propose(context.FeatureKey, $"specs/{context.FeatureKey}"), ["published"] = false });
        BoundHandoff handoff = new HandoffBinder().Bind(Contracts.RestrictedYaml.Parse(File.ReadAllText(path)), requireComplete: false);
        return AdapterResultWriter.Success(Contracts.AdapterOperation.Handoff, new JsonObject { ["handoffDigest"] = handoff.Digest, ["published"] = false });
    }
}
