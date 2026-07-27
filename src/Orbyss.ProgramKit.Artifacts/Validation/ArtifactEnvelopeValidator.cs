namespace Orbyss.ProgramKit.Artifacts.Validation;

/// <summary>Adapts the shared envelope validator to a typed semantic validator.</summary>
/// <typeparam name="TDocument">The immutable typed document view.</typeparam>
public sealed class ArtifactEnvelopeValidator<TDocument> :
    IProgramKitSemanticValidator<ArtifactEnvelope<TDocument>>
{
    private readonly IArtifactEnvelopeValidator envelopeValidator;
    private readonly IProgramKitSemanticValidator<TDocument>? documentValidator;

    /// <summary>Initializes the typed adapter with injected validation behavior.</summary>
    public ArtifactEnvelopeValidator(
        IArtifactEnvelopeValidator envelopeValidator,
        IProgramKitSemanticValidator<TDocument>? documentValidator = null)
    {
        this.envelopeValidator = envelopeValidator ??
            throw new ArgumentNullException(nameof(envelopeValidator));
        this.documentValidator = documentValidator;
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(ArtifactEnvelope<TDocument> value) =>
        envelopeValidator.Validate(value, documentValidator);
}
