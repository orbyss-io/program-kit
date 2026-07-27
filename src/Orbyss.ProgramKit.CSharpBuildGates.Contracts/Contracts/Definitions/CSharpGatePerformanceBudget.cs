namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>Finite focused/full performance budgets.</summary>
public sealed record CSharpGatePerformanceBudget(
    int FocusedMilliseconds,
    int FullClosureMilliseconds,
    int MaximumAllocatedMegabytes);
