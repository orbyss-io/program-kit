using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Quality.Execution;

namespace Orbyss.ProgramKit.Quality.Validation;

/// <summary>Validates the semantic invariants of an execution profile.</summary>
public sealed class ExecutionProfileValidator :
    IArtifactEnvelopeSemanticValidator<ExecutionProfile>
{
    private readonly IArtifactEnvelopeValidator _envelopeValidator;

    /// <summary>Creates a profile validator with explicit envelope validation.</summary>
    public ExecutionProfileValidator(IArtifactEnvelopeValidator envelopeValidator)
    {
        ArgumentNullException.ThrowIfNull(envelopeValidator);
        _envelopeValidator = envelopeValidator;
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(ExecutionProfile value)
    {
        ArgumentNullException.ThrowIfNull(value);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        QualityValidation.RequireText(value.RunnerClass, "$.runnerClass", diagnostics);
        QualityValidation.RequireText(value.Platform, "$.platform", diagnostics);
        QualityValidation.ValidateTextArray(value.EnvironmentAssumptions, "$.environmentAssumptions", diagnostics);
        QualityValidation.ValidateReferences(value.DependencyClosure, "$.dependencyClosure", diagnostics);
        QualityValidation.ValidateAccess(value.Access, "$.access", diagnostics);
        QualityValidation.ValidateTimeoutAndRetry(value.Timeout, value.Retry, "$", diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <summary>
    /// Validates an enveloped execution profile and rejects a dependency
    /// reference back to the same envelope revision.
    /// </summary>
    public ProgramKitValidationResult Validate(
        ArtifactEnvelope<ExecutionProfile> envelope)
    {
        var diagnostics = QualityEnvelopeValidation.ValidateEnvelope(
            envelope,
            this,
            _envelopeValidator);
        if (QualityEnvelopeValidation.TryCreateSelfReference(
                envelope,
                out var selfReference) &&
            envelope.Document is not null)
        {
            QualityEnvelopeValidation.RejectAll(
                selfReference,
                envelope.Document.DependencyClosure,
                "/document/dependencyClosure",
                diagnostics);
        }

        return ProgramKitValidationResult.From(diagnostics);
    }
}
