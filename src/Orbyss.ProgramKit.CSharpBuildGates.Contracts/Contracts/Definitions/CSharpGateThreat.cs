using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>A threat and its exact mitigating verification.</summary>
public sealed record CSharpGateThreat(
    ProgramKitIdentifier Identity,
    string Threat,
    string Boundary,
    ImmutableArray<ArtifactReference> Mitigations,
    string ResidualRisk);
