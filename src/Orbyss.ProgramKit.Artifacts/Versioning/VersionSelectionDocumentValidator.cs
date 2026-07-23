namespace Orbyss.ProgramKit.Artifacts.Versioning;

/// <summary>Validates immutable observed-to-target selections.</summary>
public sealed class VersionSelectionDocumentValidator :
    IArtifactEnvelopeSemanticValidator<VersionSelectionDocument>
{
    private readonly IArtifactEnvelopeValidator envelopeValidator;

    /// <summary>Initializes the validator with shared envelope validation behavior.</summary>
    public VersionSelectionDocumentValidator(IArtifactEnvelopeValidator envelopeValidator)
    {
        this.envelopeValidator = envelopeValidator ??
            throw new ArgumentNullException(nameof(envelopeValidator));
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(VersionSelectionDocument value)
    {
        var diagnostics = System.Collections.Immutable.ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        if (value is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidVersionSelection,
                "A version selection document is required.",
                string.Empty);
            return diagnostics.ToResult();
        }

        diagnostics.Add(ArtifactReferenceValidator.Validate(value.InputVersionMap, "/inputVersionMap"));
        if (value.InputVersionMap is not null &&
            !string.Equals(value.InputVersionMap.Identity.Kind, "version-map", StringComparison.Ordinal))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidVersionSelection,
                "The input map reference must have PKID kind 'version-map'.",
                "/inputVersionMap/identity");
        }

        if (value.Selections.IsDefaultOrEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidVersionSelection,
                "At least one exact selection is required.",
                "/selections");
            return diagnostics.ToResult();
        }

        var identities = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < value.Selections.Length; index++)
        {
            var selection = value.Selections[index];
            var path = string.Concat("/selections/", index);
            if (selection is null)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionSelection,
                    "A version selection is required.",
                    path);
                continue;
            }

            diagnostics.Add(ProgramKitIdentifier.Validate(
                selection.Identity.Value,
                ArtifactReferenceValidator.Path(path, "identity")));
            diagnostics.Add(ArtifactReferenceValidator.Validate(
                selection.Observed,
                ArtifactReferenceValidator.Path(path, "observed")));
            diagnostics.Add(ArtifactReferenceValidator.Validate(
                selection.Target,
                ArtifactReferenceValidator.Path(path, "target")));
            diagnostics.Add(ProgramKitIdentifier.Validate(
                selection.OwnerId.Value,
                ArtifactReferenceValidator.Path(path, "ownerId")));

            if (selection.Observed is not null && selection.Observed.Identity != selection.Identity)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionSelection,
                    "The observed reference identity must equal the selected identity.",
                    ArtifactReferenceValidator.Path(path, "observed/identity"));
            }

            if (selection.Target is not null && selection.Target.Identity != selection.Identity)
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionSelection,
                    "The target reference identity must equal the selected identity.",
                    ArtifactReferenceValidator.Path(path, "target/identity"));
            }

            if (!identities.Add(selection.Identity.Value))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.InvalidVersionSelection,
                    "A semantic identity may be selected only once.",
                    ArtifactReferenceValidator.Path(path, "identity"));
            }
        }

        return diagnostics.ToResult();
    }

    /// <summary>
    /// Validates the envelope and rejects exact references from the selection
    /// payload back to that same envelope revision.
    /// </summary>
    /// <remarks>
    /// This overload detects cycles from supplied metadata and does not
    /// recompute canonical bytes or the digest; that remains W015 work.
    /// </remarks>
    public ProgramKitValidationResult Validate(
        ArtifactEnvelope<VersionSelectionDocument> envelope)
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
            envelope.Document.InputVersionMap,
            "/document/inputVersionMap",
            diagnostics);
        for (var index = 0; index < envelope.Document.Selections.Length; index++)
        {
            var selection = envelope.Document.Selections[index];
            if (selection is null)
            {
                continue;
            }

            var path = string.Concat("/document/selections/", index);
            ArtifactEnvelopeSelfReference.Reject(
                selfReference,
                selection.Observed,
                ArtifactReferenceValidator.Path(path, "observed"),
                diagnostics);
            ArtifactEnvelopeSelfReference.Reject(
                selfReference,
                selection.Target,
                ArtifactReferenceValidator.Path(path, "target"),
                diagnostics);
        }

        return diagnostics.ToResult();
    }
}
