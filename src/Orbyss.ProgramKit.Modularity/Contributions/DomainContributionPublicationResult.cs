using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Modularity.Contributions;

/// <summary>Aggregates ordered handler execution observations for one publication.</summary>
/// <param name="Handlers">Handler observations in deterministic execution order.</param>
public sealed record DomainContributionPublicationResult(
    ImmutableArray<DomainContributionHandlerExecution> Handlers)
{
    /// <summary>Gets an empty successful result for zero-handler publication.</summary>
    public static DomainContributionPublicationResult Empty { get; } = new([]);

    /// <summary>Gets whether every selected handler completed successfully.</summary>
    public bool Succeeded =>
        !Handlers.IsDefault &&
        Handlers.All(static handler =>
            handler.Status == DomainContributionHandlerExecutionStatus.Succeeded);
}
