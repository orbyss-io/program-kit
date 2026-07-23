namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Validates versioned component manifests.</summary>
public sealed class VersionedComponentManifestValidator :
    IProgramKitSemanticValidator<VersionedComponentManifest>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(VersionedComponentManifest value)
    {
        var diagnostics = System.Collections.Immutable.ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidComponentManifest,
                "A versioned component manifest is required.",
                string.Empty);
            return diagnostics.ToResult();
        }

        diagnostics.Add(ProgramKitIdentifier.Validate(value.Identity.Value, "/identity"));
        diagnostics.Add(ProgramKitIdentifier.Validate(value.OwnerId.Value, "/ownerId"));
        diagnostics.Add(SemanticVersion.Validate(value.Version.Value, "/version"));
        diagnostics.Add(Sha256Digest.Validate(value.Digest.Value, "/digest"));
        if (!Enum.IsDefined(value.Kind))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidComponentManifest,
                "The component boundary kind is not defined.",
                "/kind");
        }

        DefaultArtifactEnvelopeValidator.ValidateReferences(
            value.ProvidedContracts,
            "/providedContracts",
            expectedKind: "contract",
            requireAtLeastOne: false,
            ArtifactDiagnosticIds.InvalidComponentManifest,
            diagnostics);
        ValidateRequirements(value, diagnostics);
        ValidateCompatibilityClaims(value, diagnostics);
        DefaultArtifactEnvelopeValidator.ValidateReferences(
            value.MigrationReferences,
            "/migrationReferences",
            expectedKind: "migration",
            requireAtLeastOne: false,
            ArtifactDiagnosticIds.InvalidComponentManifest,
            diagnostics);
        return diagnostics.ToResult();
    }

    private static void ValidateRequirements(
        VersionedComponentManifest manifest,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (manifest.RequiredContracts.IsDefault)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidComponentManifest,
                "The required-contract collection must be initialized.",
                "/requiredContracts");
            return;
        }

        var seen = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < manifest.RequiredContracts.Length; index++)
        {
            var requirement = manifest.RequiredContracts[index];
            var path = string.Concat("/requiredContracts/", index);
            if (requirement is null)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidComponentManifest,
                    "A version requirement is required.",
                    path);
                continue;
            }

            diagnostics.Add(ProgramKitIdentifier.Validate(
                requirement.Identity.Value,
                ArtifactReferenceValidator.Path(path, "identity")));
            diagnostics.Add(SemanticVersionRange.Validate(
                requirement.AcceptedRange.Value,
                ArtifactReferenceValidator.Path(path, "acceptedRange")));
            diagnostics.Add(ArtifactReferenceValidator.Validate(
                requirement.Resolution,
                ArtifactReferenceValidator.Path(path, "resolution")));
            if (!Enum.IsDefined(requirement.Exposure))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidComponentManifest,
                    "Dependency exposure is not defined.",
                    ArtifactReferenceValidator.Path(path, "exposure"));
            }

            if (requirement.Resolution is not null)
            {
                if (requirement.Identity != requirement.Resolution.Identity)
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidComponentManifest,
                        "The resolution identity must equal the required identity.",
                        ArtifactReferenceValidator.Path(path, "resolution/identity"));
                }

                if (!requirement.AcceptedRange.Contains(requirement.Resolution.Version))
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidComponentManifest,
                        "The exact resolution is outside the accepted range.",
                        ArtifactReferenceValidator.Path(path, "resolution/version"));
                }
            }

            ValidateDimensions(
                requirement.Dimensions,
                ArtifactReferenceValidator.Path(path, "dimensions"),
                ArtifactDiagnosticIds.InvalidComponentManifest,
                diagnostics);
            DefaultArtifactEnvelopeValidator.ValidateReferences(
                requirement.EvidenceReferences,
                ArtifactReferenceValidator.Path(path, "evidenceReferences"),
                expectedKind: null,
                requireAtLeastOne: true,
                ArtifactDiagnosticIds.InvalidComponentManifest,
                diagnostics);
            if (!seen.Add(requirement.Identity.Value))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidComponentManifest,
                    "A manifest may require a contract identity only once.",
                    ArtifactReferenceValidator.Path(path, "identity"));
            }
        }
    }

    private static void ValidateCompatibilityClaims(
        VersionedComponentManifest manifest,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (manifest.CompatibilityClaims.IsDefaultOrEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidComponentManifest,
                "At least one compatibility claim is required.",
                "/compatibilityClaims");
            return;
        }

        var seen = new HashSet<CompatibilityDimension>();
        for (var index = 0; index < manifest.CompatibilityClaims.Length; index++)
        {
            var claim = manifest.CompatibilityClaims[index];
            var path = string.Concat("/compatibilityClaims/", index);
            if (claim is null ||
                !Enum.IsDefined(claim.Dimension) ||
                !Enum.IsDefined(claim.Classification))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidComponentManifest,
                    "A compatibility claim must use defined values.",
                    path);
                continue;
            }

            if (!seen.Add(claim.Dimension))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidComponentManifest,
                    "A compatibility dimension may be claimed only once.",
                    ArtifactReferenceValidator.Path(path, "dimension"));
            }

            if (claim.Classification == CompatibilityClassification.ConditionallyCompatible &&
                claim.Conditions.IsDefaultOrEmpty)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidComponentManifest,
                    "Conditional compatibility requires explicit conditions.",
                    ArtifactReferenceValidator.Path(path, "conditions"));
            }

            DefaultArtifactEnvelopeValidator.ValidateNonEmptyStrings(
                claim.Conditions,
                ArtifactReferenceValidator.Path(path, "conditions"),
                ArtifactDiagnosticIds.InvalidComponentManifest,
                diagnostics);
        }
    }

    internal static void ValidateDimensions(
        System.Collections.Immutable.ImmutableArray<CompatibilityDimension> dimensions,
        string path,
        string diagnosticId,
        System.Collections.Immutable.ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (dimensions.IsDefaultOrEmpty)
        {
            diagnostics.Error(
                diagnosticId,
                "At least one compatibility dimension is required.",
                path);
            return;
        }

        var seen = new HashSet<CompatibilityDimension>();
        for (var index = 0; index < dimensions.Length; index++)
        {
            if (!Enum.IsDefined(dimensions[index]) || !seen.Add(dimensions[index]))
            {
                diagnostics.Error(
                    diagnosticId,
                    "Compatibility dimensions must be defined and unique.",
                    string.Concat(path, "/", index));
            }
        }
    }
}
