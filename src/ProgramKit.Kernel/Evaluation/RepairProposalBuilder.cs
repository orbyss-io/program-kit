using System.Text.Json.Nodes;

namespace Orbyss.ProgramKit.Kernel.Evaluation;

public static class RepairProposalBuilder
{
    public static JsonObject Build(JsonObject evaluationRequest)
    {
        JsonObject repair = (JsonObject)evaluationRequest.DeepClone();
        repair["operation"] = "construct";
        repair["constructionMode"] = "repair";
        repair["requestedEffect"] = "committed";
        if (repair["authority"] is JsonObject authority)
        {
            authority["approved"] = false;
        }

        return repair;
    }
}
