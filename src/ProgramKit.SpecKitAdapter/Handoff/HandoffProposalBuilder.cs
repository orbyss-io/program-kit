using System.Text.Json.Nodes;

namespace Orbyss.ProgramKit.SpecKitAdapter.Handoff;

public static class HandoffProposalBuilder
{
    public static JsonObject Propose(string featureKey, string featureRoot) => new()
    {
        ["schema"] = "program-kit.spec-kit-handoff-proposal/v1",
        ["feature"] = new JsonObject { ["key"] = featureKey, ["root"] = featureRoot },
        ["authority"] = "none",
        ["admitted"] = false,
        ["requiredHumanDecisions"] = new JsonArray("applicability", "effective-selection", "definition-fields", "implementation-ownership", "trace", "maximum-effect"),
        ["heuristicSourcesAdmitted"] = false,
    };
}
