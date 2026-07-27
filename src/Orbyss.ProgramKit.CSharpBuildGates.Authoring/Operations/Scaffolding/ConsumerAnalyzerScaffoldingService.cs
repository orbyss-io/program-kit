using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;

namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Operations.Scaffolding;

/// <summary>Transactional implementation of consumer analyzer scaffolding.</summary>
public sealed class ConsumerAnalyzerScaffoldingService(
    IConsumerAnalyzerScaffoldWorkspace workspace) :
    IConsumerAnalyzerScaffoldingService
{
    /// <inheritdoc />
    public async ValueTask<ConsumerAnalyzerScaffoldPlan> ScaffoldAsync(
        ConsumerAnalyzerScaffoldRequest request,
        string outputRoot,
        CancellationToken cancellationToken)
    {
        var plan = ConsumerAnalyzerScaffoldPlanner.Plan(request);
        await using var transaction = await workspace
            .BeginAsync(outputRoot, cancellationToken)
            .ConfigureAwait(false);
        try
        {
            foreach (var file in plan.Files)
            {
                cancellationToken.ThrowIfCancellationRequested();
                await transaction
                    .WriteAsync(file.RelativePath, file.Content, cancellationToken)
                    .ConfigureAwait(false);
            }

            cancellationToken.ThrowIfCancellationRequested();
            await transaction
                .CommitAsync(cancellationToken)
                .ConfigureAwait(false);
            return plan;
        }
        catch
        {
            await transaction
                .RollbackAsync(CancellationToken.None)
                .ConfigureAwait(false);
            throw;
        }
    }
}
