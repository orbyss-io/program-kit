using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;

namespace Orbyss.ProgramKit.UnitTests.Artifacts.Validation.TestSupport;

internal sealed class RecordingScaffoldWorkspace :
    IConsumerAnalyzerScaffoldWorkspace
{
    private readonly IConsumerAnalyzerScaffoldTransaction transaction;

    public RecordingScaffoldWorkspace(
        IConsumerAnalyzerScaffoldTransaction transaction)
    {
        this.transaction = transaction;
    }

    public ValueTask<IConsumerAnalyzerScaffoldTransaction> BeginAsync(
        string outputRoot,
        CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();
        return ValueTask.FromResult<IConsumerAnalyzerScaffoldTransaction>(
            transaction);
    }
}
