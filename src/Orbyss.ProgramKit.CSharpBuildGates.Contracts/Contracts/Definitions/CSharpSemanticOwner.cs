using Orbyss.ProgramKit.Artifacts.Primitives;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>An exact semantic owner and its governing authority.</summary>
public sealed record CSharpSemanticOwner(
    ProgramKitIdentifier Identity,
    CSharpAnalyzerComponentKind Kind,
    ArtifactReference GoverningContract,
    string DiagnosticPrefix);
