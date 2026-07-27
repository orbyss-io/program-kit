namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;

/// <summary>Publishes one validated consumer-owned analyzer scaffold.</summary>
public interface IConsumerAnalyzerScaffoldingService
{
    /// <summary>
    /// Plans, stages, and commits the scaffold or rolls back every staged file.
    /// </summary>
    ValueTask<ConsumerAnalyzerScaffoldPlan> ScaffoldAsync(
        ConsumerAnalyzerScaffoldRequest request,
        string outputRoot,
        CancellationToken cancellationToken);
}
