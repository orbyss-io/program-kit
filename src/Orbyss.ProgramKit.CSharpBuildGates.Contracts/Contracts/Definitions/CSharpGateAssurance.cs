using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>All assurance contracts carried by one definition.</summary>
public sealed record CSharpGateAssurance(
    CSharpGateCompatibility Compatibility,
    ImmutableArray<CSharpGateMigrationRequirement> Migrations,
    ImmutableArray<CSharpGateThreat> Threats,
    ImmutableArray<CSharpGateFixture> Fixtures,
    CSharpGatePerformanceBudget Performance);
