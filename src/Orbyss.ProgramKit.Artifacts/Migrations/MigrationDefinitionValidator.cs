namespace Orbyss.ProgramKit.Artifacts.Migrations;

/// <summary>Validates explicit migration definitions.</summary>
public sealed class MigrationDefinitionValidator :
    IArtifactEnvelopeSemanticValidator<MigrationDefinition>
{
    private readonly IArtifactEnvelopeValidator envelopeValidator;

    /// <summary>Initializes the validator with shared envelope validation behavior.</summary>
    public MigrationDefinitionValidator(IArtifactEnvelopeValidator envelopeValidator)
    {
        this.envelopeValidator = envelopeValidator ??
            throw new ArgumentNullException(nameof(envelopeValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(MigrationDefinition value)
    {
        var diagnostics = System.Collections.Immutable.ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidMigrationDefinition,
                "A migration definition is required.",
                string.Empty);
            return diagnostics.ToResult();
        }

        diagnostics.Add(ProgramKitIdentifier.Validate(value.SourceIdentity.Value, "/sourceIdentity"));
        diagnostics.Add(SemanticVersionRange.Validate(value.SourceRange.Value, "/sourceRange"));
        diagnostics.Add(ArtifactReferenceValidator.Validate(value.Target, "/target"));
        diagnostics.Add(ArtifactReferenceValidator.Validate(
            value.ImplementationReference,
            "/implementationReference"));

        if (!Enum.IsDefined(value.Mode) ||
            !Enum.IsDefined(value.LossPolicy) ||
            !Enum.IsDefined(value.FailurePolicy))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidMigrationDefinition,
                "Migration mode, loss policy, and failure policy must be defined.",
                string.Empty);
        }

        if (value.Target is not null && value.Target.Identity != value.SourceIdentity)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidMigrationDefinition,
                "The target identity must equal the source identity; identity replacement is a separate explicit edge.",
                "/target/identity");
        }

        if (value.Mode is MigrationMode.ArtifactTransform or
            MigrationMode.ConfigurationTransform or
            MigrationMode.Regenerate &&
            !value.IsDeterministic)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidMigrationDefinition,
                "Artifact, configuration, and regeneration migrations must be deterministic.",
                "/isDeterministic");
        }

        ValidatePreconditions(value, diagnostics);
        DefaultArtifactEnvelopeValidator.ValidateReferences(
            value.FixtureReferences,
            "/fixtureReferences",
            expectedKind: "fixture",
            requireAtLeastOne: true,
            ArtifactDiagnosticIds.InvalidMigrationDefinition,
            diagnostics);
        return diagnostics.ToResult();
    }

    /// <summary>
    /// Validates the envelope and rejects exact references from the migration
    /// definition back to that same envelope revision.
    /// </summary>
    /// <remarks>
    /// This overload compares supplied exact references only. Canonical-byte
    /// digest recomputation and verification remain W015 work.
    /// </remarks>
    public ProgramKitValidationResult Validate(
        ArtifactEnvelope<MigrationDefinition> envelope)
    {
        var diagnostics = System.Collections.Immutable.ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.Add(envelopeValidator.Validate(envelope, this));
        if (envelope?.Document is null ||
            !ArtifactEnvelopeSelfReference.TryCreate(envelope, out var selfReference))
        {
            return diagnostics.ToResult();
        }

        ArtifactEnvelopeSelfReference.Reject(
            selfReference,
            envelope.Document.Target,
            "/document/target",
            diagnostics);
        ArtifactEnvelopeSelfReference.Reject(
            selfReference,
            envelope.Document.ImplementationReference,
            "/document/implementationReference",
            diagnostics);
        ArtifactEnvelopeSelfReference.RejectAll(
            selfReference,
            envelope.Document.FixtureReferences,
            "/document/fixtureReferences",
            diagnostics);
        for (var index = 0; index < envelope.Document.Preconditions.Length; index++)
        {
            var precondition = envelope.Document.Preconditions[index];
            if (precondition is null)
            {
                continue;
            }

            ArtifactEnvelopeSelfReference.RejectAll(
                selfReference,
                precondition.EvidenceReferences,
                string.Concat("/document/preconditions/", index, "/evidenceReferences"),
                diagnostics);
        }

        return diagnostics.ToResult();
    }

    private static void ValidatePreconditions(
        MigrationDefinition definition,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (definition.Preconditions.IsDefault)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidMigrationDefinition,
                "The precondition collection must be initialized.",
                "/preconditions");
            return;
        }

        if (definition.LossPolicy == MigrationLossPolicy.ExplicitlyLossy &&
            definition.Preconditions.IsEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidMigrationDefinition,
                "An explicitly lossy migration must declare reviewed preconditions.",
                "/preconditions");
        }

        var codes = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < definition.Preconditions.Length; index++)
        {
            var precondition = definition.Preconditions[index];
            var path = string.Concat("/preconditions/", index);
            if (precondition is null)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidMigrationDefinition,
                    "A migration precondition is required.",
                    path);
                continue;
            }

            if (!ArtifactValidationText.IsKebabCase(precondition.Code))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidMigrationDefinition,
                    "Precondition code must be a lowercase ASCII kebab-case token.",
                    ArtifactReferenceValidator.Path(path, "code"));
            }

            if (string.IsNullOrWhiteSpace(precondition.Description))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidMigrationDefinition,
                    "Precondition description is required.",
                    ArtifactReferenceValidator.Path(path, "description"));
            }

            if (!codes.Add(precondition.Code))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidMigrationDefinition,
                    "Precondition codes must be unique.",
                    ArtifactReferenceValidator.Path(path, "code"));
            }

            DefaultArtifactEnvelopeValidator.ValidateReferences(
                precondition.EvidenceReferences,
                ArtifactReferenceValidator.Path(path, "evidenceReferences"),
                expectedKind: null,
                requireAtLeastOne: true,
                ArtifactDiagnosticIds.InvalidMigrationDefinition,
                diagnostics);
        }
    }
}
