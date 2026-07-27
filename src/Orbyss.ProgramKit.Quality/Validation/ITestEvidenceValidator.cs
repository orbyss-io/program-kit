using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Quality.Evidence;
using Orbyss.ProgramKit.Quality.Execution;
using Orbyss.ProgramKit.Quality.Specifications;

namespace Orbyss.ProgramKit.Quality.Validation;

/// <summary>
/// Validates test evidence independently and against the exact specification
/// and execution profile that produced it.
/// </summary>
public interface ITestEvidenceValidator :
    IArtifactEnvelopeSemanticValidator<TestEvidence>
{
    /// <summary>
    /// Validates evidence against its resolved specification and execution
    /// profile contracts.
    /// </summary>
    ProgramKitValidationResult ValidateAgainst(
        TestEvidence evidence,
        TestSpecification specification,
        ArtifactReference specificationReference,
        ExecutionProfile profile,
        ProfileReference profileReference);
}
