using System.Text.Json.Nodes;

namespace Orbyss.ProgramKit.Kernel.Evaluation;

public static class RepairProposalBuilder
{
    private const string EmptyDigest = "sha256:0000000000000000000000000000000000000000000000000000000000000000";

    public static JsonObject Build(JsonObject evaluationRequest, string closureDigest, string liveStateDigest)
    {
        JsonObject repair = (JsonObject)evaluationRequest.DeepClone();
        repair["operation"] = "construct";
        repair["constructionMode"] = "repair";
        repair["requestedEffect"] = "committed";
        repair.Remove("continuation");
        repair["authorityGrant"] = new JsonObject
        {
            ["identity"] = new JsonObject
            {
                ["authority"] = "pending.human",
                ["kind"] = "authority-grant",
                ["name"] = "pending-repair-grant",
                ["revision"] = "1",
                ["digest"] = EmptyDigest,
            },
            ["mediaType"] = "application/vnd.program-kit.authority-grant+json",
            ["logicalPath"] = "authority/pending-repair-grant.json",
            ["digest"] = EmptyDigest,
            ["ownership"] = "consumer-owned",
        };
        repair["expectedState"] = new JsonObject
        {
            ["closureDigest"] = closureDigest,
            ["liveStateDigest"] = liveStateDigest,
        };
        return repair;
    }
}
