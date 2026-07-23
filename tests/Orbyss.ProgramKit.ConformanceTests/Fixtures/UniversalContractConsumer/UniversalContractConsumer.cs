using Orbyss.ProgramKit.Architecture;
using Orbyss.ProgramKit.Artifacts;
using Orbyss.ProgramKit.Development;
using Orbyss.ProgramKit.Planning;
using Orbyss.ProgramKit.Quality;

namespace Orbyss.ProgramKit.UniversalContractConsumerFixture;

/// <summary>
/// Proves that a standalone consumer can bind to one public contract from every universal package.
/// </summary>
public static class UniversalContractConsumer
{
    /// <summary>Gets the representative Artifacts contract type.</summary>
    public static Type ArtifactContract => typeof(ArtifactEnvelope<>);

    /// <summary>Gets the representative Architecture contract type.</summary>
    public static Type ArchitectureContract => typeof(ArchitectureDesignDocument);

    /// <summary>Gets the representative Quality contract type.</summary>
    public static Type QualityContract => typeof(TestSpecification);

    /// <summary>Gets the representative Planning contract type.</summary>
    public static Type PlanningContract => typeof(ImplementationPlanDocument);

    /// <summary>Gets the representative Development contract type.</summary>
    public static Type DevelopmentContract => typeof(DevelopmentReceipt);
}
