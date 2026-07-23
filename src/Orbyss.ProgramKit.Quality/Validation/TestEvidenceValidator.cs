using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Quality.Diagnostics;
using Orbyss.ProgramKit.Quality.Execution;
using Orbyss.ProgramKit.Quality.Evidence;
using Orbyss.ProgramKit.Quality.Specifications;

namespace Orbyss.ProgramKit.Quality.Validation;

/// <summary>Validates digest-bound test evidence.</summary>
public sealed class TestEvidenceValidator : ITestEvidenceValidator
{
    private readonly IProgramKitSemanticValidator<TestSpecification> _specificationValidator;
    private readonly IProgramKitSemanticValidator<ExecutionProfile> _profileValidator;
    private readonly IArtifactEnvelopeValidator _envelopeValidator;

    /// <summary>Creates an evidence validator with explicit semantic dependencies.</summary>
    public TestEvidenceValidator(
        IProgramKitSemanticValidator<TestSpecification> specificationValidator,
        IProgramKitSemanticValidator<ExecutionProfile> profileValidator,
        IArtifactEnvelopeValidator envelopeValidator)
    {
        ArgumentNullException.ThrowIfNull(specificationValidator);
        ArgumentNullException.ThrowIfNull(profileValidator);
        ArgumentNullException.ThrowIfNull(envelopeValidator);

        _specificationValidator = specificationValidator;
        _profileValidator = profileValidator;
        _envelopeValidator = envelopeValidator;
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(TestEvidence value)
    {
        ArgumentNullException.ThrowIfNull(value);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        QualityValidation.ValidateTestReference(value.Specification, "$.specification", diagnostics);
        QualityValidation.ValidateProfileReference(value.Profile, "$.profile", diagnostics);
        QualityValidation.ValidateReference(value.Subject, "$.subject", diagnostics);
        QualityValidation.RequireIdentifier(value.ProducerId, "$.producerId", diagnostics);
        QualityValidation.RequireText(value.CorrelationId, "$.correlationId", diagnostics);
        if (!Enum.IsDefined(value.Outcome))
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt309,
                "Evidence outcome must be a defined value.",
                "$.outcome"));
        }

        if (value.ObservedAt == default)
        {
            diagnostics.Add(QualityValidation.Error(QualityDiagnosticIds.Pkqlt301, "A supplied observation time is required.", "$.observedAt"));
        }

        if (value.Observations.IsDefaultOrEmpty)
        {
            diagnostics.Add(QualityValidation.Error(QualityDiagnosticIds.Pkqlt302, "At least one observation is required.", "$.observations"));
        }
        else
        {
            var names = new HashSet<string>(StringComparer.Ordinal);
            for (var index = 0; index < value.Observations.Length; index++)
            {
                var observation = value.Observations[index];
                var path = $"$.observations[{index}]";
                if (observation is null)
                {
                    diagnostics.Add(QualityValidation.Error(QualityDiagnosticIds.Pkqlt303, "An observation cannot be null.", path));
                    continue;
                }

                QualityValidation.RequireText(observation.Name, $"{path}.name", diagnostics);
                QualityValidation.RequireText(observation.Value, $"{path}.value", diagnostics);
                if (observation.Attachment is not null)
                {
                    QualityValidation.ValidateReference(observation.Attachment, $"{path}.attachment", diagnostics);
                }

                if (!string.IsNullOrWhiteSpace(observation.Name) && !names.Add(observation.Name))
                {
                    diagnostics.Add(QualityValidation.Error(
                        QualityDiagnosticIds.Pkqlt304,
                        $"Observation '{observation.Name}' occurs more than once.",
                        $"{path}.name"));
                }
            }
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <summary>
    /// Validates enveloped evidence and rejects exact evidence references back
    /// to the same envelope revision.
    /// </summary>
    public ProgramKitValidationResult Validate(
        ArtifactEnvelope<TestEvidence> envelope)
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
            envelope.Document.Specification,
            "/document/specification",
            diagnostics);
        QualityEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.Profile,
            "/document/profile",
            diagnostics);
        QualityEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.Subject,
            "/document/subject",
            diagnostics);
        for (var index = 0; index < envelope.Document.Observations.Length; index++)
        {
            QualityEnvelopeValidation.Reject(
                selfReference,
                envelope.Document.Observations[index]?.Attachment,
                $"/document/observations/{index}/attachment",
                diagnostics);
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <summary>Validates evidence against the exact selected specification/profile and evidence shape.</summary>
    public ProgramKitValidationResult ValidateAgainst(
        TestEvidence evidence,
        TestSpecification specification,
        ArtifactReference specificationReference,
        ExecutionProfile profile,
        ProfileReference profileReference)
    {
        ArgumentNullException.ThrowIfNull(evidence);
        ArgumentNullException.ThrowIfNull(specification);
        ArgumentNullException.ThrowIfNull(specificationReference);
        ArgumentNullException.ThrowIfNull(profile);
        ArgumentNullException.ThrowIfNull(profileReference);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.AddRange(Validate(evidence).Diagnostics);
        diagnostics.AddRange(_specificationValidator.Validate(specification).Diagnostics);
        diagnostics.AddRange(_profileValidator.Validate(profile).Diagnostics);
        QualityValidation.ValidateTestReference(
            specificationReference,
            "$.specificationReference",
            diagnostics);
        QualityValidation.ValidateProfileReference(
            profileReference,
            "$.profileReference",
            diagnostics);
        if (evidence.Specification != specificationReference)
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt305,
                "Evidence must bind the exact executed specification.",
                "$.specification"));
        }

        if (evidence.Profile != profileReference)
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt306,
                "Evidence must bind the exact executed profile.",
                "$.profile"));
        }

        var observations = evidence.Observations.IsDefault
            ? ImmutableArray<TestObservation>.Empty
            : evidence.Observations;
        if (specification.EvidenceShape is null)
        {
            return ProgramKitValidationResult.From(diagnostics);
        }

        if (!specification.EvidenceShape.RequiredObservations.IsDefault)
        {
            foreach (var required in specification.EvidenceShape.RequiredObservations)
            {
                if (!observations.Any(observation =>
                        string.Equals(observation?.Name, required, StringComparison.Ordinal)))
                {
                    diagnostics.Add(QualityValidation.Error(
                        QualityDiagnosticIds.Pkqlt307,
                        $"Required observation '{required}' is missing.",
                        "$.observations"));
                }
            }
        }

        if (!specification.EvidenceShape.AllowsAttachments
            && observations.Any(observation => observation?.Attachment is not null))
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt308,
                "The specification's evidence shape does not permit attachments.",
                "$.observations"));
        }

        return ProgramKitValidationResult.From(diagnostics);
    }
}
