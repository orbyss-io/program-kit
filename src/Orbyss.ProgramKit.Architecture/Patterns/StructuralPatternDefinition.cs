using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Patterns;

/// <summary>One structural pattern with both mechanical and human checks.</summary>
public sealed record StructuralPatternDefinition(
    ProgramKitIdentifier Identity,
    string Name,
    string Problem,
    ImmutableArray<string> ApplicabilityCriteria,
    ImmutableArray<string> TradeOffs,
    ImmutableArray<StructuralPatternExample> Examples,
    ImmutableArray<string> MechanicalChecks,
    ImmutableArray<string> HumanChecks);
