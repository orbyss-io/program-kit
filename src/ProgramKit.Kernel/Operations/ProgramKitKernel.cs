using System.Collections.Generic;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Kernel.Resolution;

namespace Orbyss.ProgramKit.Kernel.Operations;

public sealed class ProgramKitKernel
{
    private readonly ExplainOperation explain;
    private readonly ConstructOperation construct;
    private readonly EvaluateOperation evaluate;

    public ProgramKitKernel(IEnumerable<IFactoryProvider> providers)
    {
        ProviderRegistry registry = new(providers);
        IntakePipeline intake = new(registry);
        ResolutionEngine resolution = new(registry);
        explain = new ExplainOperation(intake, resolution);
        construct = new ConstructOperation(intake, resolution);
        evaluate = new EvaluateOperation(intake, resolution);
    }

    public OperationResult Explain(string workspaceRoot, string requestPath) => explain.Execute(workspaceRoot, requestPath);

    public OperationResult Construct(string workspaceRoot, string requestPath) => construct.Execute(workspaceRoot, requestPath);

    public OperationResult Evaluate(string workspaceRoot, string requestPath) => evaluate.Execute(workspaceRoot, requestPath);

    public static OperationResult Help() => OperationResultFactory.Success(
        PublicCommand.Help,
        OperationPhase.Completion,
        EffectState.None,
        utility: new JsonObject
        {
            ["kind"] = "help",
            ["commands"] = new JsonArray("explain", "construct", "evaluate", "help", "version"),
            ["contractResources"] = new JsonArray("cli", "operation-result", "diagnostics"),
        });

    public static OperationResult Version() => OperationResultFactory.Success(
        PublicCommand.Version,
        OperationPhase.Completion,
        EffectState.None,
        utility: new JsonObject
        {
            ["kind"] = "version",
            ["cli"] = "1.0.0-alpha.1",
            ["kernelProtocol"] = "1.0.0",
            ["canonicalProfile"] = "program-kit.canonical-json/v1",
            ["diagnosticCatalog"] = "1.0.0",
            ["distribution"] = "dotnet10-cshells-0.0.28",
        });
}
