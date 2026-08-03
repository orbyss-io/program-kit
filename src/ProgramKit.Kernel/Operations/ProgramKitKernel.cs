using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json.Nodes;
using Orbyss.ProgramKit.Contracts.Operations;
using Orbyss.ProgramKit.Contracts.Providers;
using Orbyss.ProgramKit.Contracts.Schemas;
using Orbyss.ProgramKit.Kernel.Authority;
using Orbyss.ProgramKit.Kernel.Canonicalization;
using Orbyss.ProgramKit.Kernel.Distribution;
using Orbyss.ProgramKit.Kernel.Intake;
using Orbyss.ProgramKit.Kernel.Preparation;
using Orbyss.ProgramKit.Kernel.Resolution;
using Orbyss.ProgramKit.Kernel.Validation;
using Orbyss.ProgramKit.Kernel.Workspace;

namespace Orbyss.ProgramKit.Kernel.Operations;

public sealed class ProgramKitKernel
{
    private readonly ExplainOperation explain;
    private readonly ConstructOperation construct;
    private readonly EvaluateOperation evaluate;
    private readonly DistributionCatalogService catalog;
    private readonly WorkspaceRestoreService restore;
    private readonly WorkspaceInitializationService initialize = new();
    private readonly PrepareOperation prepare;
    private readonly RepositoryAuthorityRecordOperation authorityRecord;

    public ProgramKitKernel(IEnumerable<IFactoryProvider> providers)
    {
        ProviderRegistry registry = new(providers);
        IntakePipeline intake = new(registry);
        ResolutionEngine resolution = new(registry);
        explain = new ExplainOperation(intake, resolution);
        construct = new ConstructOperation(intake, resolution);
        evaluate = new EvaluateOperation(intake, resolution);
        catalog = new DistributionCatalogService(registry);
        restore = new WorkspaceRestoreService(registry);
        prepare = new PrepareOperation(new PreparationService(registry));
        authorityRecord = new RepositoryAuthorityRecordOperation(registry);
    }

    public OperationResult Explain(string workspaceRoot, string requestPath) => explain.Execute(workspaceRoot, requestPath);

    public OperationResult Construct(string workspaceRoot, string requestPath) => construct.Execute(workspaceRoot, requestPath);

    public OperationResult Evaluate(string workspaceRoot, string requestPath) => evaluate.Execute(workspaceRoot, requestPath);

    public OperationResult InitializeWorkspace(string workspaceRoot, string requestPath)
    {
        JsonObject request = ReadRequest(requestPath, ContractSchemaResources.WorkspaceInitializationRequestId);
        var result = initialize.Initialize(workspaceRoot, request);
        EffectState effect = result.Publication.Changes.All(static change => change.Kind == "unchanged") ? EffectState.None : EffectState.Committed;
        return OperationResultFactory.Success(PublicCommand.Init, OperationPhase.Completion, effect, changes: result.Publication.Changes, payload: result.Payload);
    }

    public OperationResult ListCatalog(string requestPath)
    {
        JsonObject request = ReadRequest(requestPath, ContractSchemaResources.CatalogRequestId);
        JsonObject payload = new() { ["catalog"] = catalog.Create(request["distributionBinding"]!.AsObject()) };
        return OperationResultFactory.Success(PublicCommand.CatalogList, OperationPhase.Completion, EffectState.None, payload: payload);
    }

    public OperationResult RestoreWorkspace(string workspaceRoot, string requestPath)
    {
        JsonObject request = ReadRequest(requestPath, ContractSchemaResources.WorkspaceRestoreRequestId);
        var result = restore.Restore(workspaceRoot, request);
        EffectState effect = result.Publication.Changes.All(static change => change.Kind == "unchanged") ? EffectState.None : EffectState.Committed;
        return OperationResultFactory.Success(PublicCommand.Restore, OperationPhase.Completion, effect, changes: result.Publication.Changes, payload: result.Payload);
    }

    public OperationResult Prepare(string workspaceRoot, string requestPath) =>
        prepare.Execute(workspaceRoot, ReadRequest(requestPath, ContractSchemaResources.PreparationRequestId));

    public OperationResult RecordAuthority(string workspaceRoot, string requestPath) =>
        authorityRecord.Execute(workspaceRoot, ReadRequest(requestPath, ContractSchemaResources.AuthorityRecordRequestId));

    private static JsonObject ReadRequest(string requestPath, string schemaId)
    {
        JsonObject request = CanonicalJson.Parse(File.ReadAllBytes(requestPath)).AsObject();
        var failures = new StructuralSchemaValidator(new SchemaRegistry()).Validate(schemaId, request);
        if (failures.Count > 0) throw new InvalidDataException(string.Join(" | ", failures));
        return request;
    }

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
            ["cli"] = "1.0.0-alpha.2",
            ["kernelProtocol"] = "1.0.0",
            ["canonicalProfile"] = "program-kit.canonical-json/v1",
            ["diagnosticCatalog"] = "1.0.0",
            ["distribution"] = "dotnet10-cshells-0.0.28",
        });
}
