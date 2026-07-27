using Orbyss.ProgramKit.Artifacts.Envelopes;

namespace Orbyss.ProgramKit.Artifacts.Validation;

/// <summary>
/// Validates both a contract payload and that payload inside its artifact
/// envelope.
/// </summary>
/// <typeparam name="T">The immutable Program Kit contract type.</typeparam>
public interface IArtifactEnvelopeSemanticValidator<T> :
    IProgramKitSemanticValidator<T>
{
    /// <summary>
    /// Validates the supplied envelope, including payload self-reference
    /// constraints.
    /// </summary>
    ProgramKitValidationResult Validate(ArtifactEnvelope<T> envelope);
}
