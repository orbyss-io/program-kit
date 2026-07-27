using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Validation;

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
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
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
