using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>One exact conjunctive activation cell.</summary>
public sealed record CSharpGateActivation(
    ProgramKitIdentifier ProjectProfileId,
    ProgramKitIdentifier SourceProfileId,
    CSharpGateCommand Command,
    CSharpGateImplementationBoundary Boundary,
    CSharpGateVerificationProfileKind VerificationProfile,
    ImmutableArray<ProgramKitIdentifier> AnalyzerComponentIds);
