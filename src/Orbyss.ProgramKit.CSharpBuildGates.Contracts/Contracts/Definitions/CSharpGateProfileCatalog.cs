using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>All finite profiles selected by one definition.</summary>
public sealed record CSharpGateProfileCatalog(
    ImmutableArray<CSharpGateProjectProfile> Projects,
    ImmutableArray<CSharpGateInputProfile> Inputs,
    ImmutableArray<CSharpGateGeneratedSourceProfile> GeneratedSources);
