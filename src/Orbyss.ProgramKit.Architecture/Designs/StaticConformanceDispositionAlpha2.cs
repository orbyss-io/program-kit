using System.Collections.Immutable;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>Current static-conformance disposition writer with exact schema identity.</summary>
public sealed record StaticConformanceDispositionAlpha2(
    [property: JsonPropertyName("$schema")] string Schema,
    ArtifactReference SoftwareDesign,
    ImmutableArray<StaticInvariantAllocation> InvariantAllocations,
    StaticConformanceDispositionKind Disposition,
    ImmutableArray<StaticConformanceGateSelection> GateSelections,
    ImmutableArray<ArtifactReference> LinkedGateDesigns,
    string Rationale,
    ImmutableArray<string> ResidualRisks,
    ImmutableArray<string> NonStaticClaims,
    StaticConformanceDecisionSource DecisionSource,
    ArtifactReference? EmptySelectionAcceptance,
    ImmutableArray<string> Blockers)
{
    /// <summary>The only schema URI emitted by this writer.</summary>
    public const string SchemaUri =
        "https://schemas.orbyss.io/program-kit/architecture/0.1.0-alpha.2/static-conformance-disposition.schema.json";
}
