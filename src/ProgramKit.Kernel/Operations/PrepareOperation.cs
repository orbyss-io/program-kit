using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Kernel.Preparation;

namespace Orbyss.ProgramKit.Kernel.Operations;

public sealed class PrepareOperation
{
    private readonly PreparationService preparation;

    public PrepareOperation(PreparationService preparation)
    {
        this.preparation = preparation;
    }

    public OperationResult Execute(string workspaceRoot, JsonObject request)
    {
        JsonObject proposal = preparation.Prepare(workspaceRoot, request);
        return OperationResultFactory.Success(
            PublicCommand.Prepare,
            OperationPhase.Completion,
            EffectState.None,
            payload: new JsonObject { ["proposal"] = proposal });
    }
}
