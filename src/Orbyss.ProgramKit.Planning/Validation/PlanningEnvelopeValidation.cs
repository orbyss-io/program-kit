using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Diagnostics;
using Orbyss.ProgramKit.Artifacts.Envelopes;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Artifacts.Validation;
using Orbyss.ProgramKit.Planning.Diagnostics;
using Orbyss.ProgramKit.Planning.Plans;
using Orbyss.ProgramKit.Quality.Execution;

namespace Orbyss.ProgramKit.Planning.Validation;

internal static class PlanningEnvelopeValidation
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
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln219,
                "A planning artifact must not embed its own exact identity, version, and digest reference.",
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
            diagnostics.Add(PlanningValidation.Error(
                PlanningDiagnosticIds.Pkpln219,
                "A planning artifact must not embed its own exact identity, version, and digest reference.",
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

    internal static void RejectDependencies(
        ArtifactReference selfReference,
        ImmutableArray<PlanDependency> dependencies,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (dependencies.IsDefault)
        {
            return;
        }

        for (var index = 0; index < dependencies.Length; index++)
        {
            Reject(
                selfReference,
                dependencies[index]?.Artifact,
                string.Concat(path, "/", index, "/artifact"),
                diagnostics);
        }
    }

    internal static void RejectSelections(
        ArtifactReference selfReference,
        ImmutableArray<TestSpecificationSelection> selections,
        string path,
        ImmutableArray<ProgramKitDiagnostic>.Builder diagnostics)
    {
        if (selections.IsDefault)
        {
            return;
        }

        for (var index = 0; index < selections.Length; index++)
        {
            var selection = selections[index];
            Reject(
                selfReference,
                selection?.Specification,
                string.Concat(path, "/", index, "/specification"),
                diagnostics);
            Reject(
                selfReference,
                selection?.Profile,
                string.Concat(path, "/", index, "/profile"),
                diagnostics);
        }
    }
}
