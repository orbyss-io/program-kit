using System.Collections.Immutable;

namespace Orbyss.ProgramKit.Artifacts.Envelopes;

/// <summary>Records supplied provenance without inventing ambient values.</summary>
/// <param name="SourceInputs">Exact source revisions in stable order.</param>
/// <param name="Producer">The producer identity.</param>
/// <param name="CorrelationId">A caller-supplied correlation identifier.</param>
public sealed record ArtifactProvenance(
    ImmutableArray<ArtifactReference> SourceInputs,
    ProgramKitIdentifier Producer,
    string CorrelationId);
