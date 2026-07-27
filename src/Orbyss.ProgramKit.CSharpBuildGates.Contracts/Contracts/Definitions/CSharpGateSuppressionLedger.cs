using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>A stable-ordered source-local suppression ledger.</summary>
public sealed record CSharpGateSuppressionLedger(
    ProgramKitIdentifier Identity,
    SemanticVersion Version,
    ImmutableArray<CSharpGateSuppressionEntry> Entries);
