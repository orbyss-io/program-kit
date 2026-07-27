namespace Orbyss.ProgramKit.Artifacts.Migrations;

/// <summary>Validates action-complete migration impact assessments.</summary>
public sealed class MigrationAssessmentValidator :
    IArtifactEnvelopeSemanticValidator<MigrationAssessment>
{
    private readonly IArtifactEnvelopeValidator envelopeValidator;

    /// <summary>Initializes the validator with shared envelope validation behavior.</summary>
    public MigrationAssessmentValidator(IArtifactEnvelopeValidator envelopeValidator)
    {
        this.envelopeValidator = envelopeValidator ??
            throw new ArgumentNullException(nameof(envelopeValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(MigrationAssessment value)
    {
        var diagnostics = System.Collections.Immutable.ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidMigrationAssessment,
                "A migration assessment is required.",
                string.Empty);
            return diagnostics.ToResult();
        }

        diagnostics.Add(ArtifactReferenceValidator.Validate(
            value.VersionMapReference,
            "/versionMapReference"));
        diagnostics.Add(ArtifactReferenceValidator.Validate(
            value.VersionSelectionReference,
            "/versionSelectionReference"));
        ValidateReferenceKinds(value, diagnostics);

        DefaultArtifactEnvelopeValidator.ValidateReferences(
            value.ChangedRevisions,
            "/changedRevisions",
            expectedKind: null,
            requireAtLeastOne: true,
            ArtifactDiagnosticIds.InvalidMigrationAssessment,
            diagnostics);

        var targetKeys = ValidateImpacts(value, diagnostics);
        ValidateWaves(value, targetKeys, diagnostics);
        return diagnostics.ToResult();
    }

    /// <summary>
    /// Validates the envelope and rejects exact references from the migration
    /// assessment back to that same envelope revision.
    /// </summary>
    /// <remarks>
    /// This overload detects supplied-reference cycles only. Canonical-byte
    /// digest recomputation and verification remain W015 work.
    /// </remarks>
    public ProgramKitValidationResult Validate(
        ArtifactEnvelope<MigrationAssessment> envelope)
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
            envelope.Document.VersionMapReference,
            "/document/versionMapReference",
            diagnostics);
        ArtifactEnvelopeSelfReference.Reject(
            selfReference,
            envelope.Document.VersionSelectionReference,
            "/document/versionSelectionReference",
            diagnostics);
        ArtifactEnvelopeSelfReference.RejectAll(
            selfReference,
            envelope.Document.ChangedRevisions,
            "/document/changedRevisions",
            diagnostics);

        for (var impactIndex = 0; impactIndex < envelope.Document.Impacts.Length; impactIndex++)
        {
            var impact = envelope.Document.Impacts[impactIndex];
            if (impact is null)
            {
                continue;
            }

            var impactPath = string.Concat("/document/impacts/", impactIndex);
            ArtifactEnvelopeSelfReference.Reject(
                selfReference,
                impact.Observed,
                ArtifactReferenceValidator.Path(impactPath, "observed"),
                diagnostics);
            ArtifactEnvelopeSelfReference.Reject(
                selfReference,
                impact.Target,
                ArtifactReferenceValidator.Path(impactPath, "target"),
                diagnostics);
            ArtifactEnvelopeSelfReference.RejectAll(
                selfReference,
                impact.RequiredEvidence,
                ArtifactReferenceValidator.Path(impactPath, "requiredEvidence"),
                diagnostics);
            for (var pathIndex = 0; pathIndex < impact.CausalPaths.Length; pathIndex++)
            {
                var causalPath = impact.CausalPaths[pathIndex];
                if (causalPath is null)
                {
                    continue;
                }

                ArtifactEnvelopeSelfReference.Reject(
                    selfReference,
                    causalPath.ChangedRoot,
                    string.Concat(impactPath, "/causalPaths/", pathIndex, "/changedRoot"),
                    diagnostics);
            }
        }

        for (var waveIndex = 0; waveIndex < envelope.Document.Waves.Length; waveIndex++)
        {
            var wave = envelope.Document.Waves[waveIndex];
            if (wave is null)
            {
                continue;
            }

            for (var cohortIndex = 0; cohortIndex < wave.Cohorts.Length; cohortIndex++)
            {
                var cohort = wave.Cohorts[cohortIndex];
                if (cohort is null)
                {
                    continue;
                }

                ArtifactEnvelopeSelfReference.RejectAll(
                    selfReference,
                    cohort.Members,
                    string.Concat(
                        "/document/waves/",
                        waveIndex,
                        "/cohorts/",
                        cohortIndex,
                        "/members"),
                    diagnostics);
            }
        }

        return diagnostics.ToResult();
    }

    private static void ValidateReferenceKinds(
        MigrationAssessment assessment,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (assessment.VersionMapReference is not null &&
            !string.Equals(
                assessment.VersionMapReference.Identity.Kind,
                "version-map",
                StringComparison.Ordinal))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidMigrationAssessment,
                "The version map reference must have PKID kind 'version-map'.",
                "/versionMapReference/identity");
        }

        if (assessment.VersionSelectionReference is not null &&
            !string.Equals(
                assessment.VersionSelectionReference.Identity.Kind,
                "version-selection",
                StringComparison.Ordinal))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidMigrationAssessment,
                "The version selection reference must have PKID kind 'version-selection'.",
                "/versionSelectionReference/identity");
        }
    }

    private static HashSet<string> ValidateImpacts(
        MigrationAssessment assessment,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var targetKeys = new HashSet<string>(StringComparer.Ordinal);
        if (assessment.Impacts.IsDefaultOrEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidMigrationAssessment,
                "At least one reached revision must have a terminal impact.",
                "/impacts");
            return targetKeys;
        }

        var observedKeys = new HashSet<string>(StringComparer.Ordinal);
        var changedRoots = assessment.ChangedRevisions.IsDefault
            ? new HashSet<string>(StringComparer.Ordinal)
            : assessment.ChangedRevisions
                .Where(static reference => reference is not null)
                .Select(ArtifactReferenceValidator.ExactKey)
                .ToHashSet(StringComparer.Ordinal);

        for (var index = 0; index < assessment.Impacts.Length; index++)
        {
            var impact = assessment.Impacts[index];
            var path = string.Concat("/impacts/", index);
            if (impact is null)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidMigrationAssessment,
                    "A migration impact is required.",
                    path);
                continue;
            }

            diagnostics.Add(ArtifactReferenceValidator.Validate(
                impact.Observed,
                ArtifactReferenceValidator.Path(path, "observed")));
            diagnostics.Add(ArtifactReferenceValidator.Validate(
                impact.Target,
                ArtifactReferenceValidator.Path(path, "target")));
            diagnostics.Add(ProgramKitIdentifier.Validate(
                impact.OwnerId.Value,
                ArtifactReferenceValidator.Path(path, "ownerId")));
            if (!Enum.IsDefined(impact.Disposition))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidMigrationDisposition,
                    "The terminal disposition is not defined.",
                    ArtifactReferenceValidator.Path(path, "disposition"));
            }

            if (impact.Observed is not null && impact.Target is not null &&
                impact.Observed.Identity != impact.Target.Identity)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidMigrationAssessment,
                    "Observed and target revisions must describe the same semantic identity.",
                    ArtifactReferenceValidator.Path(path, "target/identity"));
            }

            if (impact.Observed is not null &&
                !observedKeys.Add(ArtifactReferenceValidator.ExactKey(impact.Observed)))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidMigrationAssessment,
                    "Each reached exact revision may have only one terminal impact.",
                    ArtifactReferenceValidator.Path(path, "observed"));
            }

            if (impact.Target is not null)
            {
                targetKeys.Add(ArtifactReferenceValidator.ExactKey(impact.Target));
            }

            ValidateActions(impact, path, diagnostics);
            DefaultArtifactEnvelopeValidator.ValidateReferences(
                impact.RequiredEvidence,
                ArtifactReferenceValidator.Path(path, "requiredEvidence"),
                expectedKind: null,
                requireAtLeastOne: true,
                ArtifactDiagnosticIds.InvalidMigrationAssessment,
                diagnostics);
            ValidateCausalPaths(impact, path, changedRoots, diagnostics);
            if (string.IsNullOrWhiteSpace(impact.Rationale))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidMigrationAssessment,
                    "A terminal impact requires an explicit rationale.",
                    ArtifactReferenceValidator.Path(path, "rationale"));
            }
        }

        if (!assessment.ChangedRevisions.IsDefault)
        {
            for (var index = 0; index < assessment.ChangedRevisions.Length; index++)
            {
                var changedRevision = assessment.ChangedRevisions[index];
                if (changedRevision is not null &&
                    !observedKeys.Contains(ArtifactReferenceValidator.ExactKey(changedRevision)))
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidMigrationAssessment,
                        "Every changed revision must have its own terminal impact.",
                        string.Concat("/changedRevisions/", index));
                }
            }
        }

        return targetKeys;
    }

    private static void ValidateActions(
        MigrationImpact impact,
        string path,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var actionPath = ArtifactReferenceValidator.Path(path, "requiredActions");
        if (impact.RequiredActions.IsDefault)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidMigrationDisposition,
                "The required-action collection must be initialized.",
                actionPath);
            return;
        }

        if (impact.Disposition == MigrationTerminalDisposition.UnaffectedWithProof &&
            !impact.RequiredActions.IsEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidMigrationDisposition,
                "An unaffected-with-proof disposition requires an empty action list.",
                actionPath);
        }

        if (impact.Disposition == MigrationTerminalDisposition.CompatibleAfterActions &&
            impact.RequiredActions.IsEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidMigrationDisposition,
                "A compatible-after-actions disposition requires at least one action.",
                actionPath);
        }

        var actions = new HashSet<MigrationRequiredAction>();
        for (var index = 0; index < impact.RequiredActions.Length; index++)
        {
            if (!Enum.IsDefined(impact.RequiredActions[index]) ||
                !actions.Add(impact.RequiredActions[index]))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidMigrationDisposition,
                    "Required actions must be defined and may occur only once.",
                    string.Concat(actionPath, "/", index));
            }
        }
    }

    private static void ValidateCausalPaths(
        MigrationImpact impact,
        string path,
        HashSet<string> changedRoots,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        var causalPath = ArtifactReferenceValidator.Path(path, "causalPaths");
        if (impact.CausalPaths.IsDefaultOrEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidMigrationAssessment,
                "Every reached revision must retain at least one causal path.",
                causalPath);
            return;
        }

        for (var index = 0; index < impact.CausalPaths.Length; index++)
        {
            var causal = impact.CausalPaths[index];
            var itemPath = string.Concat(causalPath, "/", index);
            if (causal is null)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidMigrationAssessment,
                    "A causal path is required.",
                    itemPath);
                continue;
            }

            diagnostics.Add(ArtifactReferenceValidator.Validate(
                causal.ChangedRoot,
                ArtifactReferenceValidator.Path(itemPath, "changedRoot")));
            if (causal.ChangedRoot is not null)
            {
                var rootKey = ArtifactReferenceValidator.ExactKey(causal.ChangedRoot);
                if (!changedRoots.Contains(rootKey))
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidMigrationAssessment,
                        "A causal path root must be listed in changedRevisions.",
                        ArtifactReferenceValidator.Path(itemPath, "changedRoot"));
                }

            }

            DefaultArtifactEnvelopeValidator.ValidateDistinctIdentifiers(
                causal.EdgeIds,
                ArtifactReferenceValidator.Path(itemPath, "edgeIds"),
                ArtifactDiagnosticIds.InvalidMigrationAssessment,
                diagnostics);
        }

    }

    private static void ValidateWaves(
        MigrationAssessment assessment,
        HashSet<string> expectedTargets,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (assessment.Waves.IsDefaultOrEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidMigrationAssessment,
                "At least one dependency-safe migration wave is required.",
                "/waves");
            return;
        }

        var scheduledTargets = new HashSet<string>(StringComparer.Ordinal);
        var cohortIds = new HashSet<string>(StringComparer.Ordinal);
        for (var waveIndex = 0; waveIndex < assessment.Waves.Length; waveIndex++)
        {
            var wave = assessment.Waves[waveIndex];
            var wavePath = string.Concat("/waves/", waveIndex);
            if (wave is null)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidMigrationAssessment,
                    "A migration wave is required.",
                    wavePath);
                continue;
            }

            if (wave.Ordinal != waveIndex)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidMigrationAssessment,
                    "Migration wave ordinals must be contiguous and zero-based.",
                    ArtifactReferenceValidator.Path(wavePath, "ordinal"));
            }

            if (wave.Cohorts.IsDefaultOrEmpty)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidMigrationAssessment,
                    "A migration wave must contain at least one atomic cohort.",
                    ArtifactReferenceValidator.Path(wavePath, "cohorts"));
                continue;
            }

            for (var cohortIndex = 0; cohortIndex < wave.Cohorts.Length; cohortIndex++)
            {
                var cohort = wave.Cohorts[cohortIndex];
                var cohortPath = string.Concat(wavePath, "/cohorts/", cohortIndex);
                if (cohort is null)
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidMigrationAssessment,
                        "A migration cohort is required.",
                        cohortPath);
                    continue;
                }

                diagnostics.Add(ProgramKitIdentifier.Validate(
                    cohort.Id.Value,
                    ArtifactReferenceValidator.Path(cohortPath, "id")));
                if (!cohortIds.Add(cohort.Id.Value))
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidMigrationAssessment,
                        "Migration cohort identities must be unique.",
                        ArtifactReferenceValidator.Path(cohortPath, "id"));
                }

                DefaultArtifactEnvelopeValidator.ValidateReferences(
                    cohort.Members,
                    ArtifactReferenceValidator.Path(cohortPath, "members"),
                    expectedKind: null,
                    requireAtLeastOne: true,
                    ArtifactDiagnosticIds.InvalidMigrationAssessment,
                    diagnostics);
                if (cohort.Members.IsDefault)
                {
                    continue;
                }

                foreach (var member in cohort.Members)
                {
                    if (member is null)
                    {
                        continue;
                    }

                    var key = ArtifactReferenceValidator.ExactKey(member);
                    if (!expectedTargets.Contains(key))
                    {
                        diagnostics.Error(
                            ArtifactDiagnosticIds.InvalidMigrationAssessment,
                            "A wave member must be the exact target of an assessed impact.",
                            ArtifactReferenceValidator.Path(cohortPath, "members"));
                    }

                    if (!scheduledTargets.Add(key))
                    {
                        diagnostics.Error(
                            ArtifactDiagnosticIds.InvalidMigrationAssessment,
                            "Every assessed target must appear in exactly one migration cohort.",
                            ArtifactReferenceValidator.Path(cohortPath, "members"));
                    }
                }
            }
        }

        if (!scheduledTargets.SetEquals(expectedTargets))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidMigrationAssessment,
                "Migration waves must contain every assessed target exactly once.",
                "/waves");
        }
    }
}
