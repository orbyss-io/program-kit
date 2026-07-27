using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;
using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Locks;

namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

/// <summary>Five deterministic C# build-gate operations.</summary>
public interface ICSharpBuildGateOperationService
{
    /// <summary>Validates a definition without loading analyzer code.</summary>
    ProgramKitValidationResult ValidateDefinition(
        CSharpBuildGateDefinitionDocument definition);

    /// <summary>Renders a validated definition deterministically.</summary>
    string RenderDefinition(CSharpBuildGateDefinitionDocument definition);

    /// <summary>Transactionally scaffolds one approved consumer-owned analyzer.</summary>
    ValueTask<ConsumerAnalyzerScaffoldPlan> ScaffoldAsync(
        ConsumerAnalyzerScaffoldRequest request,
        string outputRoot,
        CancellationToken cancellationToken);

    /// <summary>Binds exact local assets without restore, network, or assembly loading.</summary>
    CSharpBuildGateSelectionLockDocument Bind(CSharpGateBindRequest request);

    /// <summary>Runs one finite pinned compiler verification.</summary>
    ValueTask<CSharpGateCompilerHarnessResult> VerifyAsync(
        CSharpGateVerificationRequest request,
        CancellationToken cancellationToken);
}
