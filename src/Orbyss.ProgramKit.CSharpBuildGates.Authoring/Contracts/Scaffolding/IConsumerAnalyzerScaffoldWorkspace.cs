namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;

/// <summary>Creates isolated scaffold publication transactions.</summary>
public interface IConsumerAnalyzerScaffoldWorkspace
{
    /// <summary>Begins a transaction for an output root that must not exist.</summary>
    ValueTask<IConsumerAnalyzerScaffoldTransaction> BeginAsync(
        string outputRoot,
        CancellationToken cancellationToken);
}
