using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>A stable-ordered finite activation matrix.</summary>
public sealed record CSharpGateActivationMatrix(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    ImmutableArray<CSharpGateActivation> Activations);
