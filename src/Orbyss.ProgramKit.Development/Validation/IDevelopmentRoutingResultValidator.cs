using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Development.Capabilities;
using Orbyss.ProgramKit.Development.Routing;

namespace Orbyss.ProgramKit.Development.Validation;

/// <summary>
/// Validates a routing result independently and against its resolved
/// availability snapshot.
/// </summary>
public interface IDevelopmentRoutingResultValidator :
    IArtifactEnvelopeSemanticValidator<DevelopmentRoutingResult>
{
    /// <summary>
    /// Validates that the routing result agrees with the supplied snapshot and
    /// its exact reference.
    /// </summary>
    ProgramKitValidationResult ValidateAgainst(
        DevelopmentRoutingResult result,
        CapabilityAvailabilitySnapshot snapshot,
        ArtifactReference snapshotReference);
}
