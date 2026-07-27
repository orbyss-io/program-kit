using Orbyss.ProgramKit.Architecture.Designs;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Development.Receipts;
using Orbyss.ProgramKit.Planning.Plans;
using Orbyss.ProgramKit.Quality.Specifications;

namespace Orbyss.ProgramKit.UniversalContractConsumerFixture.Consumers;

/// <summary>
/// Proves that a standalone consumer can bind to one public contract from every universal package.
/// </summary>
public sealed class UniversalContractConsumer
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
