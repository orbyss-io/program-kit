using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts;

/// <summary>Validates exact artifact references.</summary>
public sealed class ArtifactReferenceValidator : IProgramKitSemanticValidator<ArtifactReference>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(ArtifactReference value) =>
        Validate(value, string.Empty);

    internal static ProgramKitValidationResult Validate(
        ArtifactReference? value,
        string path)
    {
        var diagnostics = new ArtifactDiagnosticBuilder();
        if (value is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidArtifactReference,
                "An exact artifact reference is required.",
                path);
            return diagnostics.ToResult();
        }

        diagnostics.Add(ProgramKitIdentifier.Validate(value.Identity.Value, Path(path, "identity")));
        diagnostics.Add(SemanticVersion.Validate(value.Version.Value, Path(path, "version")));
        diagnostics.Add(Sha256Digest.Validate(value.Digest.Value, Path(path, "digest")));
        return diagnostics.ToResult();
    }

    internal static string Key(ArtifactReference reference) =>
        string.Concat(reference.Identity.Value, "@", reference.Version.Value);

    internal static string ExactKey(ArtifactReference reference) =>
        string.Concat(Key(reference), "#", reference.Digest.Value);

    internal static string Path(string parent, string child) =>
        string.IsNullOrEmpty(parent) ? string.Concat("/", child) : string.Concat(parent, "/", child);
}

/// <summary>Validates exact profile references.</summary>
public sealed class ProfileReferenceValidator : IProgramKitSemanticValidator<ProfileReference>
{
    /// <inheritdoc />
    public ProgramKitValidationResult Validate(ProfileReference value) =>
        Validate(value, string.Empty);

    internal static ProgramKitValidationResult Validate(
        ProfileReference? value,
        string path)
    {
        var diagnostics = new ArtifactDiagnosticBuilder();
        if (value is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidProfileReference,
                "An exact profile reference is required.",
                path);
            return diagnostics.ToResult();
        }

        diagnostics.Add(ProgramKitIdentifier.Validate(value.Identity.Value, ArtifactReferenceValidator.Path(path, "identity")));
        diagnostics.Add(SemanticVersion.Validate(value.Version.Value, ArtifactReferenceValidator.Path(path, "version")));
        diagnostics.Add(Sha256Digest.Validate(value.Digest.Value, ArtifactReferenceValidator.Path(path, "digest")));
        if (!string.Equals(value.Identity.Kind, "profile", StringComparison.Ordinal))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidProfileReference,
                "A profile reference identity must have PKID kind 'profile'.",
                ArtifactReferenceValidator.Path(path, "identity"));
        }

        return diagnostics.ToResult();
    }
}

/// <summary>Validates the universal envelope and its cross-field invariants.</summary>
/// <typeparam name="TDocument">The immutable typed document view.</typeparam>
/// <remarks>
/// Self-reference checks compare the supplied envelope identity, version, and
/// integrity digest. Canonical-byte construction and digest recomputation are
/// deliberately deferred to W015.
/// </remarks>
public sealed class ArtifactEnvelopeValidator<TDocument> :
    IProgramKitSemanticValidator<ArtifactEnvelope<TDocument>>
{
    private readonly IProgramKitSemanticValidator<TDocument>? documentValidator;

    /// <summary>Initializes an envelope validator with optional document semantics.</summary>
    public ArtifactEnvelopeValidator(
        IProgramKitSemanticValidator<TDocument>? documentValidator = null)
    {
        this.documentValidator = documentValidator;
    }

    /// <inheritdoc />
    public ProgramKitValidationResult Validate(ArtifactEnvelope<TDocument> value)
    {
        var diagnostics = new ArtifactDiagnosticBuilder();
        if (value is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidArtifactEnvelope,
                "An artifact envelope is required.",
                string.Empty);
            return diagnostics.ToResult();
        }

        ValidateContract(value.Contract, diagnostics);
        ValidateIdentity(value.Artifact, diagnostics);
        ValidateCompatibility(value.Compatibility, diagnostics);
        ValidateProvenance(value.Provenance, diagnostics);
        ValidateRepresentation(value.Representation, diagnostics);
        ValidateIntegrity(value.Integrity, diagnostics);
        ValidateProvenanceDoesNotReferenceEnvelope(value, diagnostics);

        if (value.Document is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidArtifactEnvelope,
                "The envelope document is required.",
                "/document");
        }
        else if (documentValidator is not null)
        {
            diagnostics.Add(documentValidator.Validate(value.Document));
        }

        return diagnostics.ToResult();
    }

    private static void ValidateProvenanceDoesNotReferenceEnvelope(
        ArtifactEnvelope<TDocument> envelope,
        ArtifactDiagnosticBuilder diagnostics)
    {
        if (!ArtifactEnvelopeSelfReference.TryCreate(envelope, out var selfReference) ||
            envelope.Provenance is null ||
            envelope.Provenance.SourceInputs.IsDefault)
        {
            return;
        }

        for (var index = 0; index < envelope.Provenance.SourceInputs.Length; index++)
        {
            ArtifactEnvelopeSelfReference.Reject(
                selfReference,
                envelope.Provenance.SourceInputs[index],
                string.Concat("/provenance/sourceInputs/", index),
                diagnostics);
        }
    }

    private static void ValidateContract(
        ArtifactContract? contract,
        ArtifactDiagnosticBuilder diagnostics)
    {
        if (contract is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidArtifactEnvelope,
                "The envelope contract is required.",
                "/contract");
            return;
        }

        diagnostics.Add(ProgramKitIdentifier.Validate(contract.SchemaId.Value, "/contract/schemaId"));
        diagnostics.Add(SemanticVersion.Validate(contract.SchemaVersion.Value, "/contract/schemaVersion"));
        if (!string.Equals(contract.SchemaId.Kind, "schema", StringComparison.Ordinal))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidArtifactEnvelope,
                "The contract schema identity must have PKID kind 'schema'.",
                "/contract/schemaId");
        }
    }

    private static void ValidateIdentity(
        ArtifactIdentity? artifact,
        ArtifactDiagnosticBuilder diagnostics)
    {
        if (artifact is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidArtifactIdentity,
                "Artifact identity metadata is required.",
                "/artifact");
            return;
        }

        diagnostics.Add(ProgramKitIdentifier.Validate(artifact.Id.Value, "/artifact/id"));
        diagnostics.Add(SemanticVersion.Validate(artifact.Version.Value, "/artifact/version"));
        diagnostics.Add(ProgramKitIdentifier.Validate(artifact.OwnerId.Value, "/artifact/ownerId"));
        if (!ArtifactValidationText.IsKebabCase(artifact.Kind))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidArtifactIdentity,
                "Artifact kind must be a lowercase ASCII kebab-case token.",
                "/artifact/kind");
        }

        if (!Enum.IsDefined(artifact.Status))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidArtifactIdentity,
                "Artifact status is not defined.",
                "/artifact/status");
        }

        ValidateDistinctIdentifiers(
            artifact.Consumers,
            "/artifact/consumers",
            ArtifactDiagnosticIds.InvalidArtifactIdentity,
            diagnostics);
    }

    private static void ValidateCompatibility(
        ArtifactCompatibility? compatibility,
        ArtifactDiagnosticBuilder diagnostics)
    {
        if (compatibility is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidCompatibility,
                "Compatibility metadata is required.",
                "/compatibility");
            return;
        }

        diagnostics.Add(ProgramKitIdentifier.Validate(compatibility.Policy.Value, "/compatibility/policy"));
        diagnostics.Add(SemanticVersionRange.Validate(compatibility.ReaderRange.Value, "/compatibility/readerRange"));
        diagnostics.Add(SemanticVersionRange.Validate(compatibility.WriterRange.Value, "/compatibility/writerRange"));

        if (compatibility.Dimensions.IsDefaultOrEmpty)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidCompatibility,
                "At least one compatibility dimension is required.",
                "/compatibility/dimensions");
        }
        else
        {
            var seenDimensions = new HashSet<CompatibilityDimension>();
            for (var index = 0; index < compatibility.Dimensions.Length; index++)
            {
                var claim = compatibility.Dimensions[index];
                var path = string.Concat("/compatibility/dimensions/", index);
                if (claim is null ||
                    !Enum.IsDefined(claim.Dimension) ||
                    !Enum.IsDefined(claim.Classification))
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidCompatibility,
                        "A compatibility claim must use defined dimension and classification values.",
                        path);
                    continue;
                }

                if (!seenDimensions.Add(claim.Dimension))
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidCompatibility,
                        "A compatibility dimension may be classified only once.",
                        ArtifactReferenceValidator.Path(path, "dimension"));
                }

                if (claim.Classification == CompatibilityClassification.ConditionallyCompatible &&
                    claim.Conditions.IsDefaultOrEmpty)
                {
                    diagnostics.Error(
                        ArtifactDiagnosticIds.InvalidCompatibility,
                        "A conditionally compatible claim requires at least one explicit condition.",
                        ArtifactReferenceValidator.Path(path, "conditions"));
                }

                ValidateNonEmptyStrings(
                    claim.Conditions,
                    ArtifactReferenceValidator.Path(path, "conditions"),
                    ArtifactDiagnosticIds.InvalidCompatibility,
                    diagnostics);
            }
        }

        ValidateReferences(
            compatibility.MigrationReferences,
            "/compatibility/migrationReferences",
            expectedKind: "migration",
            requireAtLeastOne: false,
            ArtifactDiagnosticIds.InvalidCompatibility,
            diagnostics);
    }

    private static void ValidateProvenance(
        ArtifactProvenance? provenance,
        ArtifactDiagnosticBuilder diagnostics)
    {
        if (provenance is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidProvenance,
                "Provenance metadata is required.",
                "/provenance");
            return;
        }

        ValidateReferences(
            provenance.SourceInputs,
            "/provenance/sourceInputs",
            expectedKind: null,
            requireAtLeastOne: true,
            ArtifactDiagnosticIds.InvalidProvenance,
            diagnostics);
        diagnostics.Add(ProgramKitIdentifier.Validate(provenance.Producer.Value, "/provenance/producer"));
        if (string.IsNullOrWhiteSpace(provenance.CorrelationId))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidProvenance,
                "Correlation ID must be supplied explicitly.",
                "/provenance/correlationId");
        }
    }

    private static void ValidateRepresentation(
        ArtifactRepresentation? representation,
        ArtifactDiagnosticBuilder diagnostics)
    {
        if (representation is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidRepresentation,
                "Representation metadata is required.",
                "/representation");
            return;
        }

        diagnostics.Add(ProfileReferenceValidator.Validate(
            representation.SerializationProfileRef,
            "/representation/serializationProfileRef"));
        diagnostics.Add(ProfileReferenceValidator.Validate(
            representation.CanonicalizationProfileRef,
            "/representation/canonicalizationProfileRef"));
        if (string.IsNullOrWhiteSpace(representation.CanonicalMediaType) ||
            representation.CanonicalMediaType.Any(char.IsWhiteSpace))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidRepresentation,
                "Canonical media type must be a non-empty media type without whitespace.",
                "/representation/canonicalMediaType");
        }
    }

    private static void ValidateIntegrity(
        ArtifactIntegrity? integrity,
        ArtifactDiagnosticBuilder diagnostics)
    {
        if (integrity is null)
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidIntegrity,
                "Integrity metadata is required.",
                "/integrity");
            return;
        }

        if (!string.Equals(integrity.Algorithm, "sha256", StringComparison.Ordinal))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.InvalidIntegrity,
                "The only baseline integrity algorithm is 'sha256'.",
                "/integrity/algorithm");
        }

        diagnostics.Add(Sha256Digest.Validate(integrity.Digest.Value, "/integrity/digest"));
    }

    internal static void ValidateReferences(
        ImmutableArray<ArtifactReference> references,
        string path,
        string? expectedKind,
        bool requireAtLeastOne,
        string diagnosticId,
        ArtifactDiagnosticBuilder diagnostics)
    {
        if (references.IsDefault || (requireAtLeastOne && references.IsEmpty))
        {
            diagnostics.Error(
                diagnosticId,
                requireAtLeastOne
                    ? "At least one exact reference is required."
                    : "The reference collection must be initialized.",
                path);
            return;
        }

        var exactKeys = new HashSet<string>(StringComparer.Ordinal);
        var revisionDigests = new Dictionary<string, string>(StringComparer.Ordinal);
        for (var index = 0; index < references.Length; index++)
        {
            var reference = references[index];
            var itemPath = string.Concat(path, "/", index);
            diagnostics.Add(ArtifactReferenceValidator.Validate(reference, itemPath));
            if (reference is null)
            {
                continue;
            }

            if (expectedKind is not null &&
                !string.Equals(reference.Identity.Kind, expectedKind, StringComparison.Ordinal))
            {
                diagnostics.Error(
                    diagnosticId,
                    string.Concat("The reference identity must have PKID kind '", expectedKind, "'."),
                    ArtifactReferenceValidator.Path(itemPath, "identity"));
            }

            var revisionKey = ArtifactReferenceValidator.Key(reference);
            if (revisionDigests.TryGetValue(revisionKey, out var digest) &&
                !string.Equals(digest, reference.Digest.Value, StringComparison.Ordinal))
            {
                diagnostics.Error(
                    ArtifactDiagnosticIds.RevisionDigestConflict,
                    "Equal identity and version values must resolve to equal digests.",
                    itemPath);
            }
            else
            {
                revisionDigests[revisionKey] = reference.Digest.Value;
            }

            if (!exactKeys.Add(ArtifactReferenceValidator.ExactKey(reference)))
            {
                diagnostics.Error(
                    diagnosticId,
                    "Duplicate exact references are not allowed.",
                    itemPath);
            }
        }
    }

    internal static void ValidateDistinctIdentifiers(
        ImmutableArray<ProgramKitIdentifier> identifiers,
        string path,
        string diagnosticId,
        ArtifactDiagnosticBuilder diagnostics)
    {
        if (identifiers.IsDefault)
        {
            diagnostics.Error(diagnosticId, "The identifier collection must be initialized.", path);
            return;
        }

        var seen = new HashSet<string>(StringComparer.Ordinal);
        for (var index = 0; index < identifiers.Length; index++)
        {
            var itemPath = string.Concat(path, "/", index);
            diagnostics.Add(ProgramKitIdentifier.Validate(identifiers[index].Value, itemPath));
            if (!seen.Add(identifiers[index].Value))
            {
                diagnostics.Error(diagnosticId, "Duplicate identifiers are not allowed.", itemPath);
            }
        }
    }

    internal static void ValidateNonEmptyStrings(
        ImmutableArray<string> values,
        string path,
        string diagnosticId,
        ArtifactDiagnosticBuilder diagnostics)
    {
        if (values.IsDefault)
        {
            diagnostics.Error(diagnosticId, "The string collection must be initialized.", path);
            return;
        }

        for (var index = 0; index < values.Length; index++)
        {
            if (string.IsNullOrWhiteSpace(values[index]))
            {
                diagnostics.Error(
                    diagnosticId,
                    "Collection entries must be non-empty.",
                    string.Concat(path, "/", index));
            }
        }
    }
}

internal sealed class ArtifactDiagnosticBuilder
{
    private readonly ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics =
        ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();

    public void Add(ProgramKitValidationResult result)
    {
        diagnostics.AddRange(result.Diagnostics);
    }

    public void Error(string id, string message, string path)
    {
        diagnostics.Add(new ProgramKitDiagnostic(
            id,
            ProgramKitDiagnosticSeverity.Error,
            message,
            path));
    }

    public ProgramKitValidationResult ToResult() =>
        diagnostics.Count == 0
            ? ProgramKitValidationResult.Valid
            : ProgramKitValidationResult.From(diagnostics);
}

internal static class ArtifactValidationText
{
    public static bool IsKebabCase(string? value)
    {
        if (string.IsNullOrEmpty(value) || value[0] == '-' || value[^1] == '-')
        {
            return false;
        }

        var previousHyphen = false;
        foreach (var character in value)
        {
            var hyphen = character == '-';
            if (character is not (>= 'a' and <= 'z') and not (>= '0' and <= '9') && !hyphen)
            {
                return false;
            }

            if (hyphen && previousHyphen)
            {
                return false;
            }

            previousHyphen = hyphen;
        }

        return true;
    }
}

/// <summary>
/// Detects exact-reference cycles from already supplied envelope metadata.
/// It deliberately does not recompute canonical bytes or integrity digests;
/// canonical digest construction and verification belong to W015.
/// </summary>
internal static class ArtifactEnvelopeSelfReference
{
    public static bool TryCreate<TDocument>(
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

    public static void Reject(
        ArtifactReference selfReference,
        ArtifactReference? candidate,
        string path,
        ArtifactDiagnosticBuilder diagnostics)
    {
        if (candidate is not null &&
            string.Equals(
                ArtifactReferenceValidator.ExactKey(selfReference),
                ArtifactReferenceValidator.ExactKey(candidate),
                StringComparison.Ordinal))
        {
            diagnostics.Error(
                ArtifactDiagnosticIds.SelfReferentialArtifact,
                "A durable artifact must not embed its own exact identity, version, and digest reference.",
                path);
        }
    }

    public static void RejectAll(
        ArtifactReference selfReference,
        ImmutableArray<ArtifactReference> candidates,
        string path,
        ArtifactDiagnosticBuilder diagnostics)
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
