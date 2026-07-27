using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>A finite source/additional/configuration inventory.</summary>
public sealed record CSharpGateInputProfile(
    ProgramKitIdentifier Identity,
    CSharpGateInputKind Kind,
    ImmutableArray<CSharpGateContentItem> Inventory,
    ImmutableArray<ProgramKitIdentifier> ApplicableRuleIds);
