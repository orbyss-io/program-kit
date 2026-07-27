using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Quality.Diagnostics;
using Orbyss.ProgramKit.Quality.Specifications;

namespace Orbyss.ProgramKit.Quality.Validation;

/// <summary>Validates the semantic invariants of a test specification.</summary>
public sealed class TestSpecificationValidator :
    IArtifactEnvelopeSemanticValidator<TestSpecification>
{
    private readonly IArtifactEnvelopeValidator _envelopeValidator;

    /// <summary>Creates a specification validator with explicit envelope validation.</summary>
    public TestSpecificationValidator(IArtifactEnvelopeValidator envelopeValidator)
    {
        ArgumentNullException.ThrowIfNull(envelopeValidator);
        _envelopeValidator = envelopeValidator;
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(TestSpecification value)
    {
        ArgumentNullException.ThrowIfNull(value);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        QualityValidation.RequireIdentifier(value.OwnerId, "$.ownerId", diagnostics);
        QualityValidation.RequireText(value.Purpose, "$.purpose", diagnostics);
        QualityValidation.RequireUniqueText(
            value.RequirementIds,
            "$.requirementIds",
            QualityDiagnosticIds.Pkqlt101,
            "At least one requirement ID is required.",
            diagnostics);

        if (value.Categories.IsDefaultOrEmpty)
        {
            diagnostics.Add(QualityValidation.Error(QualityDiagnosticIds.Pkqlt102, "At least one test category is required.", "$.categories"));
        }
        else
        {
            if (value.Categories.Distinct().Count() != value.Categories.Length)
            {
                diagnostics.Add(QualityValidation.Error(QualityDiagnosticIds.Pkqlt103, "Test categories must be unique.", "$.categories"));
            }

            for (var index = 0; index < value.Categories.Length; index++)
            {
                if (!Enum.IsDefined(value.Categories[index]))
                {
                    diagnostics.Add(QualityValidation.Error(
                        QualityDiagnosticIds.Pkqlt110,
                        "Test category must be a defined value.",
                        $"$.categories[{index}]"));
                }
            }
        }

        if (value.Scenarios.IsDefaultOrEmpty)
        {
            diagnostics.Add(QualityValidation.Error(QualityDiagnosticIds.Pkqlt104, "At least one scenario is required.", "$.scenarios"));
        }
        else
        {
            var scenarioIds = new HashSet<string>(StringComparer.Ordinal);
            for (var index = 0; index < value.Scenarios.Length; index++)
            {
                var path = $"$.scenarios[{index}]";
                var scenario = value.Scenarios[index];
                if (scenario is null)
                {
                    diagnostics.Add(QualityValidation.Error(QualityDiagnosticIds.Pkqlt105, "A scenario cannot be null.", path));
                    continue;
                }

                QualityValidation.RequireText(scenario.ScenarioId, $"{path}.scenarioId", diagnostics);
                QualityValidation.RequireText(scenario.Purpose, $"{path}.purpose", diagnostics);
                QualityValidation.RequireText(scenario.ExpectedResult, $"{path}.expectedResult", diagnostics);
                if (!Enum.IsDefined(scenario.Kind))
                {
                    diagnostics.Add(QualityValidation.Error(
                        QualityDiagnosticIds.Pkqlt111,
                        "Scenario kind must be a defined value.",
                        $"{path}.kind"));
                }

                QualityValidation.ValidateReferences(scenario.Inputs, $"{path}.inputs", diagnostics);
                QualityValidation.ValidateReferences(scenario.Fixtures, $"{path}.fixtures", diagnostics);
                if (!string.IsNullOrWhiteSpace(scenario.ScenarioId)
                    && !scenarioIds.Add(scenario.ScenarioId))
                {
                    diagnostics.Add(QualityValidation.Error(
                        QualityDiagnosticIds.Pkqlt106,
                        $"Scenario ID '{scenario.ScenarioId}' occurs more than once.",
                        $"{path}.scenarioId"));
                }
            }
        }

        QualityValidation.ValidateRequirements(value.ExecutionRequirements, "$.executionRequirements", diagnostics);

        if (value.ExpectedResult is null)
        {
            diagnostics.Add(QualityValidation.Error(QualityDiagnosticIds.Pkqlt107, "Expected result is required.", "$.expectedResult"));
        }
        else
        {
            QualityValidation.RequireText(value.ExpectedResult.OutcomeCode, "$.expectedResult.outcomeCode", diagnostics);
            QualityValidation.RequireText(value.ExpectedResult.Description, "$.expectedResult.description", diagnostics);
        }

        if (value.EvidenceShape is null)
        {
            diagnostics.Add(QualityValidation.Error(QualityDiagnosticIds.Pkqlt108, "Evidence shape is required.", "$.evidenceShape"));
        }
        else
        {
            QualityValidation.ValidateReference(value.EvidenceShape.Schema, "$.evidenceShape.schema", diagnostics);
            QualityValidation.RequireReferenceKind(
                value.EvidenceShape.Schema,
                "schema",
                "$.evidenceShape.schema",
                QualityDiagnosticIds.Pkqlt034,
                diagnostics);
            QualityValidation.RequireUniqueText(
                value.EvidenceShape.RequiredObservations,
                "$.evidenceShape.requiredObservations",
                QualityDiagnosticIds.Pkqlt109,
                "At least one required observation is required.",
                diagnostics);
        }

        return ProgramKitValidationResult.From(diagnostics);
    }

    /// <summary>
    /// Validates an enveloped specification and rejects exact payload references
    /// back to the same envelope revision.
    /// </summary>
    public ProgramKitValidationResult Validate(
        ArtifactEnvelope<TestSpecification> envelope)
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

        for (var index = 0; index < envelope.Document.Scenarios.Length; index++)
        {
            var scenario = envelope.Document.Scenarios[index];
            if (scenario is null)
            {
                continue;
            }

            QualityEnvelopeValidation.RejectAll(
                selfReference,
                scenario.Inputs,
                $"/document/scenarios/{index}/inputs",
                diagnostics);
            QualityEnvelopeValidation.RejectAll(
                selfReference,
                scenario.Fixtures,
                $"/document/scenarios/{index}/fixtures",
                diagnostics);
        }

        if (envelope.Document.ExecutionRequirements is { } requirements)
        {
            QualityEnvelopeValidation.RejectAll(
                selfReference,
                requirements.RequiredDependencyClosure,
                "/document/executionRequirements/requiredDependencyClosure",
                diagnostics);
        }

        QualityEnvelopeValidation.Reject(
            selfReference,
            envelope.Document.EvidenceShape?.Schema,
            "/document/evidenceShape/schema",
            diagnostics);
        return ProgramKitValidationResult.From(diagnostics);
    }
}
