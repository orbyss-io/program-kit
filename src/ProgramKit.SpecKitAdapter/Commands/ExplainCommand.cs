using System.Text.Json.Nodes;
using Orbyss.ProgramKit.SpecKitAdapter.Contracts;
using Orbyss.ProgramKit.SpecKitAdapter.Invocation;

namespace Orbyss.ProgramKit.SpecKitAdapter.Commands;

public sealed class ExplainCommand
{
    private readonly IPublicProgramKitInvoker invoker;

    public ExplainCommand(IPublicProgramKitInvoker? invoker = null)
    {
        this.invoker = invoker ?? new PublicProgramKitInvoker();
    }

    public JsonObject Execute(string workspaceRoot, JsonObject request)
    {
        AdapterFeatureContext context = AdapterFeatureContextLoader.Load(workspaceRoot, request, requireReviewedHandoff: true);
        if (!context.Applicability.Active)
            return AdapterResultWriter.NotApplicable(AdapterOperation.Explain, new JsonObject { ["blocking"] = context.Applicability.BlocksWorkflow });
        string path = $"specs/{context.FeatureKey}/program-kit/generated/requests/explain.json";
        JsonObject result = invoker.Invoke(workspaceRoot, "explain", path);
        return AdapterResultWriter.Success(AdapterOperation.Explain, new JsonObject { ["request"] = path }, programKitResult: result);
    }
}
