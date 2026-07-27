using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Quality.Diagnostics;
using Orbyss.ProgramKit.Quality.Reviews;

namespace Orbyss.ProgramKit.Quality.Validation;

/// <summary>Validates reviewer independence and exact review-target binding.</summary>
public sealed class IndependentReviewValidator :
    IArtifactEnvelopeSemanticValidator<IndependentReview>
{
    private readonly IArtifactEnvelopeValidator _envelopeValidator;

    /// <summary>Creates a review validator with explicit envelope validation.</summary>
    public IndependentReviewValidator(IArtifactEnvelopeValidator envelopeValidator)
    {
        ArgumentNullException.ThrowIfNull(envelopeValidator);
        _envelopeValidator = envelopeValidator;
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(IndependentReview value)
    {
        ArgumentNullException.ThrowIfNull(value);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        QualityValidation.RequireIdentifier(value.ProducerId, "$.producerId", diagnostics);
        QualityValidation.RequireIdentifier(value.ReviewerId, "$.reviewerId", diagnostics);
        QualityValidation.RequireText(value.Summary, "$.summary", diagnostics);
        QualityValidation.ValidateReferences(value.Evidence, "$.evidence", diagnostics);
        if (!Enum.IsDefined(value.Disposition))
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt407,
                "Independent-review disposition must be a defined value.",
                "$.disposition"));
        }

        if (value.ProducerId == value.ReviewerId)
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt401,
                "The independent reviewer must be different from the artifact producer.",
                "$.reviewerId"));
        }

        if (value.ReviewedAt == default)
        {
            diagnostics.Add(QualityValidation.Error(QualityDiagnosticIds.Pkqlt402, "A supplied review time is required.", "$.reviewedAt"));
        }

        if (value.Target is null)
        {
            diagnostics.Add(QualityValidation.Error(QualityDiagnosticIds.Pkqlt403, "A review target is required.", "$.target"));
        }
        else
        {
            if (!Enum.IsDefined(value.Target.Kind))
            {
                diagnostics.Add(QualityValidation.Error(
                    QualityDiagnosticIds.Pkqlt408,
                    "Independent-review target kind must be a defined value.",
                    "$.target.kind"));
            }

            QualityValidation.ValidateReference(value.Target.Artifact, "$.target.artifact", diagnostics);
            if (value.Target.Kind == IndependentReviewTargetKind.Delta)
            {
                if (value.Target.BaseArtifact is null)
                {
                    diagnostics.Add(QualityValidation.Error(
                        QualityDiagnosticIds.Pkqlt404,
                        "A delta review requires the exact base artifact.",
                        "$.target.baseArtifact"));
                }
                else
                {
                    QualityValidation.ValidateReference(value.Target.BaseArtifact, "$.target.baseArtifact", diagnostics);
                    if (value.Target.BaseArtifact == value.Target.Artifact)
                    {
                        diagnostics.Add(QualityValidation.Error(
                            QualityDiagnosticIds.Pkqlt405,
                            "A delta base and target artifact must differ.",
                            "$.target.baseArtifact"));
                    }
                }
            }
            else if (value.Target.BaseArtifact is not null)
            {
                diagnostics.Add(QualityValidation.Error(
                    QualityDiagnosticIds.Pkqlt406,
                    "An artifact review cannot declare a delta base.",
                    "$.target.baseArtifact"));
            }
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <summary>
    /// Validates an enveloped independent review and rejects exact review
    /// references back to the same envelope revision.
    /// </summary>
    public ProgramKitValidationResult Validate(
        ArtifactEnvelope<IndependentReview> envelope)
    {
        var diagnostics = QualityEnvelopeValidation.ValidateEnvelope(
            envelope,
            this,
            _envelopeValidator);
        if (!QualityEnvelopeValidation.TryCreateSelfReference(
                envelope,
                out var selfReference) ||
            envelope.Document is null)
        {
            return ProgramKitValidationResult.From(diagnostics);
        }

        QualityEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.Target?.Artifact,
            "/document/target/artifact",
            diagnostics);
        QualityEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.Target?.BaseArtifact,
            "/document/target/baseArtifact",
            diagnostics);
        QualityEnvelopeValidation.RejectAll(
            selfReference,
            envelope.Document.Evidence,
            "/document/evidence",
            diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }
}
