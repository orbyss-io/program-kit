using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Development.Diagnostics;
using Orbyss.ProgramKit.Development.Routing;

namespace Orbyss.ProgramKit.Development.Validation;

internal static class DevelopmentEnvelopeValidation
{
    internal static ImmutableArray<ProgramKitDiagnostic>.Builder ValidateEnvelope<TDocument>(
        ArtifactEnvelope<TDocument> envelope,
        IProgramKitSemanticValidator<TDocument> validator,
        IArtifactEnvelopeValidator envelopeValidator)
    {
        ArgumentNullException.ThrowIfNull(envelopeValidator);

        var diagnostics = ImmutableArray.CreateBuilder<ProgramKitDiagnostic>();
        diagnostics.AddRange(
            envelopeValidator
                .Validate(envelope, validator)
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
            diagnostics.Add(DevelopmentValidation.Error(
                DevelopmentDiagnosticIds.Pkdev307,
                "A development artifact must not embed its own exact identity, version, and digest reference.",
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

    internal static void RejectRouting(
        ArtifactReference selfReference,
        DevelopmentRoutingOutcome? routing,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (routing is null)
        {
            return;
        }

        RejectAll(
            selfReference,
            routing.NextCapabilities,
            string.Concat(path, "/nextCapabilities"),
            diagnostics);
    }
}
