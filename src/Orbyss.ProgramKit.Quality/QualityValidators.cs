using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Quality;

/// <summary>Validates the semantic invariants of a test specification.</summary>
public sealed class TestSpecificationValidator : IProgramKitSemanticValidator<TestSpecification>
{
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
        var diagnostics = QualityEnvelopeValidation.ValidateEnvelope(envelope, this);
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

/// <summary>Validates the semantic invariants of an execution profile.</summary>
public sealed class ExecutionProfileValidator : IProgramKitSemanticValidator<ExecutionProfile>
{
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
        var diagnostics = QualityEnvelopeValidation.ValidateEnvelope(envelope, this);
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

/// <summary>Validates that an exact specification/profile selection satisfies execution requirements.</summary>
public static class TestExecutionSelectionValidator
{
    /// <summary>Validates the selected exact references and the profile's dependency and policy closure.</summary>
    public static ProgramKitValidationResult Validate(
        TestSpecification specification,
        ArtifactReference specificationReference,
        ExecutionProfile profile,
        ProfileReference profileReference,
        TestSpecificationSelection selection)
    {
        ArgumentNullException.ThrowIfNull(specification);
        ArgumentNullException.ThrowIfNull(specificationReference);
        ArgumentNullException.ThrowIfNull(profile);
        ArgumentNullException.ThrowIfNull(profileReference);
        ArgumentNullException.ThrowIfNull(selection);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.AddRange(new TestSpecificationValidator().Validate(specification).Diagnostics);
        diagnostics.AddRange(new ExecutionProfileValidator().Validate(profile).Diagnostics);

        QualityValidation.ValidateTestReference(
            specificationReference,
            "$.specificationReference",
            diagnostics);
        QualityValidation.ValidateProfileReference(
            profileReference,
            "$.profileReference",
            diagnostics);
        QualityValidation.ValidateTestReference(
            selection.Specification,
            "$.selection.specification",
            diagnostics);
        QualityValidation.ValidateProfileReference(
            selection.Profile,
            "$.selection.profile",
            diagnostics);
        if (selection.Specification != specificationReference)
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt201,
                "The selected specification reference must match the validated specification exactly.",
                "$.selection.specification"));
        }

        if (selection.Profile != profileReference)
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt202,
                "The selected profile reference must match the validated profile exactly.",
                "$.selection.profile"));
        }

        var requirements = specification.ExecutionRequirements;
        if (requirements is null)
        {
            return ProgramKitValidationResult.From(diagnostics);
        }

        if (requirements.RunnerClasses.IsDefault
            || !requirements.RunnerClasses.Contains(profile.RunnerClass, StringComparer.Ordinal))
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt203,
                $"Runner class '{profile.RunnerClass}' is not permitted by the specification.",
                "$.profile.runnerClass"));
        }

        if (requirements.Platforms.IsDefault
            || !requirements.Platforms.Contains(profile.Platform, StringComparer.Ordinal))
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt204,
                $"Platform '{profile.Platform}' is not permitted by the specification.",
                "$.profile.platform"));
        }

        if (!requirements.RequiredDependencyClosure.IsDefault)
        {
            foreach (var dependency in requirements.RequiredDependencyClosure)
            {
                if (profile.DependencyClosure.IsDefault
                    || !profile.DependencyClosure.Contains(dependency))
                {
                    diagnostics.Add(QualityValidation.Error(
                        QualityDiagnosticIds.Pkqlt205,
                        $"The execution profile is missing required dependency '{dependency.Identity.Value}'.",
                        "$.profile.dependencyClosure"));
                }
            }
        }

        if (!requirements.EnvironmentAssumptions.IsDefault)
        {
            foreach (var assumption in requirements.EnvironmentAssumptions)
            {
                if (profile.EnvironmentAssumptions.IsDefault
                    || !profile.EnvironmentAssumptions.Contains(assumption, StringComparer.Ordinal))
                {
                    diagnostics.Add(QualityValidation.Error(
                        QualityDiagnosticIds.Pkqlt208,
                        $"The execution profile is missing required environment assumption '{assumption}'.",
                        "$.profile.environmentAssumptions"));
                }
            }
        }

        if (profile.Timeout > requirements.Timeout)
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt206,
                "The execution profile timeout exceeds the specification limit.",
                "$.profile.timeout"));
        }

        if (profile.Retry is not null
            && requirements.Retry is not null
            && profile.Retry.MaximumAttempts > requirements.Retry.MaximumAttempts)
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt207,
                "The execution profile retry count exceeds the specification limit.",
                "$.profile.retry.maximumAttempts"));
        }

        QualityValidation.ValidateAccessDoesNotExceed(
            requirements.Access,
            profile.Access,
            "$.profile.access",
            diagnostics);

        return ProgramKitValidationResult.From(diagnostics);
    }
}

/// <summary>Validates digest-bound test evidence.</summary>
public sealed class TestEvidenceValidator : IProgramKitSemanticValidator<TestEvidence>
{
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
        var diagnostics = QualityEnvelopeValidation.ValidateEnvelope(envelope, this);
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
        diagnostics.AddRange(new TestSpecificationValidator().Validate(specification).Diagnostics);
        diagnostics.AddRange(new ExecutionProfileValidator().Validate(profile).Diagnostics);
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

/// <summary>Validates reviewer independence and exact review-target binding.</summary>
public sealed class IndependentReviewValidator : IProgramKitSemanticValidator<IndependentReview>
{
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
        var diagnostics = QualityEnvelopeValidation.ValidateEnvelope(envelope, this);
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

internal static class QualityEnvelopeValidation
{
    internal static ImmutableArray<ProgramKitDiagnostic>.Builder ValidateEnvelope<TDocument>(
        ArtifactEnvelope<TDocument> envelope,
        IProgramKitSemanticValidator<TDocument> validator)
    {
        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.AddRange(
            new ArtifactEnvelopeValidator<TDocument>(validator)
                .Validate(envelope)
                .Diagnostics);
        return diagnostics;
    }

    internal static bool TryCreateSelfReference<TDocument>(
        ArtifactEnvelope<TDocument>? envelope,
        out ArtifactReference selfReference)
    {
        if (envelope?.Artifact is null || envelope.Integrity is null)
        {
            selfReference = null!;
            return false;
        }

        selfReference = new ArtifactReference(
            envelope.Artifact.Id,
            envelope.Artifact.Version,
            envelope.Integrity.Digest);
        return true;
    }

    internal static void Reject(
        ArtifactReference selfReference,
        ArtifactReference? candidate,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (candidate == selfReference)
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt409,
                "A quality artifact must not embed its own exact identity, version, and digest reference.",
                path));
        }
    }

    internal static void Reject(
        ArtifactReference selfReference,
        ProfileReference? candidate,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (candidate is not null &&
            candidate.Identity == selfReference.Identity &&
            candidate.Version == selfReference.Version &&
            candidate.Digest == selfReference.Digest)
        {
            diagnostics.Add(QualityValidation.Error(
                QualityDiagnosticIds.Pkqlt409,
                "A quality artifact must not embed its own exact identity, version, and digest reference.",
                path));
        }
    }

    internal static void RejectAll(
        ArtifactReference selfReference,
        ImmutableArray<ArtifactReference> candidates,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (candidates.IsDefault)
        {
            return;
        }

        for (var index = 0; index < candidates.Length; index++)
        {
            Reject(
                selfReference,
                candidates[index],
                string.Concat(path, "/", index),
                diagnostics);
        }
    }
}

internal static class QualityValidation
{
    internal static ProgramKitDiagnostic Error(string id, string message, string path) =>
        new(id, ProgramKitDiagnosticSeverity.Error, message, path);

    internal static void RequireText(
        string? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt001, "A non-empty value is required.", path));
        }
    }

    internal static void RequireIdentifier(
        ProgramKitIdentifier value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (string.IsNullOrWhiteSpace(value.Value))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt002, "A Program Kit identifier is required.", path));
        }
    }

    internal static void ValidateReference(
        ArtifactReference? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt003, "An exact artifact reference is required.", path));
            return;
        }

        RequireIdentifier(value.Identity, $"{path}.identity", diagnostics);
        if (string.IsNullOrWhiteSpace(value.Version.Value))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt004, "An exact semantic version is required.", $"{path}.version"));
        }

        if (string.IsNullOrWhiteSpace(value.Digest.Value))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt005, "An exact SHA-256 digest is required.", $"{path}.digest"));
        }
    }

    internal static void ValidateProfileReference(
        ProfileReference? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt006, "An exact profile reference is required.", path));
            return;
        }

        RequireIdentifier(value.Identity, $"{path}.identity", diagnostics);
        if (string.IsNullOrWhiteSpace(value.Version.Value))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt007, "An exact profile version is required.", $"{path}.version"));
        }

        if (string.IsNullOrWhiteSpace(value.Digest.Value))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt008, "An exact profile digest is required.", $"{path}.digest"));
        }

        if (!string.Equals(value.Identity.Kind, "profile", StringComparison.Ordinal))
        {
            diagnostics.Add(Error(
                QualityDiagnosticIds.Pkqlt033,
                "An exact profile reference must have PKID kind 'profile'.",
                $"{path}.identity"));
        }
    }

    internal static void ValidateTestReference(
        ArtifactReference? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        ValidateReference(value, path, diagnostics);
        if (value is not null &&
            !string.Equals(value.Identity.Kind, "test", StringComparison.Ordinal))
        {
            diagnostics.Add(Error(
                QualityDiagnosticIds.Pkqlt032,
                "An exact test specification reference must have PKID kind 'test'.",
                $"{path}.identity"));
        }
    }

    internal static void RequireReferenceKind(
        ArtifactReference? value,
        string expectedKind,
        string path,
        string diagnosticId,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is not null &&
            !string.Equals(value.Identity.Kind, expectedKind, StringComparison.Ordinal))
        {
            diagnostics.Add(Error(
                diagnosticId,
                $"The exact reference must have PKID kind '{expectedKind}'.",
                $"{path}.identity"));
        }
    }

    internal static void ValidateReferences(
        ImmutableArray<ArtifactReference> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt009, "The collection must be initialized.", path));
            return;
        }

        var seen = new HashSet<ArtifactReference>();
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            ValidateReference(value, $"{path}[{index}]", diagnostics);
            if (value is not null && !seen.Add(value))
            {
                diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt010, "Exact artifact references must be unique.", $"{path}[{index}]"));
            }
        }
    }

    internal static void RequireUniqueText(
        ImmutableArray<string> values,
        string path,
        string emptyDiagnosticId,
        string emptyMessage,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefaultOrEmpty)
        {
            diagnostics.Add(Error(emptyDiagnosticId, emptyMessage, path));
            return;
        }

        ValidateTextArray(values, path, diagnostics);
    }

    internal static void ValidateTextArray(
        ImmutableArray<string> values,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt011, "The collection must be initialized.", path));
            return;
        }

        var seen = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < values.Length; index++)
        {
            var value = values[index];
            RequireText(value, $"{path}[{index}]", diagnostics);
            if (!string.IsNullOrWhiteSpace(value) && !seen.Add(value))
            {
                diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt012, $"Value '{value}' occurs more than once.", $"{path}[{index}]"));
            }
        }
    }

    internal static void ValidateRequirements(
        TestExecutionRequirements? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt013, "Execution requirements are required.", path));
            return;
        }

        RequireUniqueText(
            value.RunnerClasses,
            $"{path}.runnerClasses",
            QualityDiagnosticIds.Pkqlt014,
            "At least one runner class is required.",
            diagnostics);
        RequireUniqueText(
            value.Platforms,
            $"{path}.platforms",
            QualityDiagnosticIds.Pkqlt015,
            "At least one platform is required.",
            diagnostics);
        ValidateTextArray(value.EnvironmentAssumptions, $"{path}.environmentAssumptions", diagnostics);
        ValidateReferences(value.RequiredDependencyClosure, $"{path}.requiredDependencyClosure", diagnostics);
        ValidateAccess(value.Access, $"{path}.access", diagnostics);
        ValidateTimeoutAndRetry(value.Timeout, value.Retry, path, diagnostics);
    }

    internal static void ValidateAccess(
        TestExecutionAccessPolicy? value,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (value is null)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt016, "An execution access policy is required.", path));
            return;
        }

        ValidateTextArray(value.AllowedNetworkDestinations, $"{path}.allowedNetworkDestinations", diagnostics);
        ValidateTextArray(value.AllowedWriteRoots, $"{path}.allowedWriteRoots", diagnostics);
        ValidateTextArray(value.AllowedSecretReferences, $"{path}.allowedSecretReferences", diagnostics);
        if (!Enum.IsDefined(value.Network))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt028, "Network access policy must be a defined value.", $"{path}.network"));
        }

        if (!Enum.IsDefined(value.Writes))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt029, "Write access policy must be a defined value.", $"{path}.writes"));
        }

        if (!Enum.IsDefined(value.Restore))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt030, "Restore access policy must be a defined value.", $"{path}.restore"));
        }

        if (!Enum.IsDefined(value.Secrets))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt031, "Secret access policy must be a defined value.", $"{path}.secrets"));
        }

        ValidateAllowList(
            value.Network == NetworkAccessPolicy.ExplicitAllowList,
            value.AllowedNetworkDestinations,
            "network",
            $"{path}.allowedNetworkDestinations",
            diagnostics);
        ValidateAllowList(
            value.Writes == WriteAccessPolicy.ExplicitRoots,
            value.AllowedWriteRoots,
            "write-root",
            $"{path}.allowedWriteRoots",
            diagnostics);
        ValidateAllowList(
            value.Secrets == SecretAccessPolicy.ExplicitReferencesOnly,
            value.AllowedSecretReferences,
            "secret-reference",
            $"{path}.allowedSecretReferences",
            diagnostics);
    }

    internal static void ValidateTimeoutAndRetry(
        TimeSpan timeout,
        TestRetryPolicy? retry,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (timeout <= TimeSpan.Zero)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt017, "Timeout must be positive.", $"{path}.timeout"));
        }

        if (retry is null)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt018, "A retry policy is required.", $"{path}.retry"));
            return;
        }

        if (retry.MaximumAttempts < 1)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt019, "Maximum attempts must be at least one.", $"{path}.retry.maximumAttempts"));
        }

        if (retry.Delay < TimeSpan.Zero)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt020, "Retry delay cannot be negative.", $"{path}.retry.delay"));
        }
    }

    internal static void ValidateAccessDoesNotExceed(
        TestExecutionAccessPolicy? allowed,
        TestExecutionAccessPolicy? selected,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (allowed is null || selected is null)
        {
            return;
        }

        if (!IsNetworkSelectionAllowed(allowed.Network, selected.Network))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt021, "Selected network access exceeds the specification.", $"{path}.network"));
        }

        if (!IsWriteSelectionAllowed(allowed.Writes, selected.Writes))
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt022, "Selected write access exceeds the specification.", $"{path}.writes"));
        }

        if (selected.Restore != RestoreAccessPolicy.Denied
            && selected.Restore != allowed.Restore)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt023, "Selected restore access exceeds the specification.", $"{path}.restore"));
        }

        if (selected.Secrets != SecretAccessPolicy.Denied
            && selected.Secrets != allowed.Secrets)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt024, "Selected secret access exceeds the specification.", $"{path}.secrets"));
        }

        RequireSubset(
            selected.AllowedNetworkDestinations,
            allowed.AllowedNetworkDestinations,
            "network destination",
            $"{path}.allowedNetworkDestinations",
            diagnostics);
        RequireSubset(
            selected.AllowedWriteRoots,
            allowed.AllowedWriteRoots,
            "write root",
            $"{path}.allowedWriteRoots",
            diagnostics);
        RequireSubset(
            selected.AllowedSecretReferences,
            allowed.AllowedSecretReferences,
            "secret reference",
            $"{path}.allowedSecretReferences",
            diagnostics);
    }

    private static void ValidateAllowList(
        bool required,
        ImmutableArray<string> values,
        string kind,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (values.IsDefault)
        {
            return;
        }

        if (required && values.IsEmpty)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt025, $"An explicit {kind} allow-list cannot be empty.", path));
        }
        else if (!required && !values.IsEmpty)
        {
            diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt026, $"{kind} entries require the corresponding explicit policy.", path));
        }
    }

    private static void RequireSubset(
        ImmutableArray<string> selected,
        ImmutableArray<string> allowed,
        string kind,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (selected.IsDefault || allowed.IsDefault)
        {
            return;
        }

        foreach (var value in selected)
        {
            if (!allowed.Contains(value, StringComparer.Ordinal))
            {
                diagnostics.Add(Error(QualityDiagnosticIds.Pkqlt027, $"Selected {kind} '{value}' is not permitted.", path));
            }
        }
    }

    private static bool IsNetworkSelectionAllowed(
        NetworkAccessPolicy allowed,
        NetworkAccessPolicy selected) =>
        selected == NetworkAccessPolicy.Denied ||
        selected == allowed;

    private static bool IsWriteSelectionAllowed(
        WriteAccessPolicy allowed,
        WriteAccessPolicy selected) =>
        selected == WriteAccessPolicy.Denied ||
        selected == allowed;
}
