namespace Orbyss.ProgramKit.Artifacts.Validation;

/// <summary>Validates universal artifact envelopes with optional document semantics.</summary>
public interface IArtifactEnvelopeValidator
{
    /// <summary>Validates an envelope and its typed document.</summary>
    /// <typeparam name="TDocument">The immutable typed document view.</typeparam>
    /// <param name="value">The envelope to validate.</param>
    /// <param name="documentValidator">Optional document-specific semantics.</param>
    /// <returns>The complete immutable validation result.</returns>
    ProgramKitValidationResult Validate<TDocument>(
        ArtifactEnvelope<TDocument> value,
        IProgramKitSemanticValidator<TDocument>? documentValidator = null);
}
