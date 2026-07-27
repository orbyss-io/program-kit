using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Quality.Execution;
using Orbyss.ProgramKit.Quality.Specifications;

namespace Orbyss.ProgramKit.Quality.Validation;

/// <summary>
/// Validates whether an exact specification and execution-profile selection
/// satisfies the specification's execution requirements.
/// </summary>
public interface ITestExecutionSelectionValidator
{
    /// <summary>
    /// Validates the selected exact references and the profile's dependency
    /// and policy closure.
    /// </summary>
    ProgramKitValidationResult Validate(
        TestSpecification specification,
        ArtifactReference specificationReference,
        ExecutionProfile profile,
        ProfileReference profileReference,
        TestSpecificationSelection selection);
}
