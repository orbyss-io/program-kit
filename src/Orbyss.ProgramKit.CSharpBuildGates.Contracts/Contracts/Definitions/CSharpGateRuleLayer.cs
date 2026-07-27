namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>The static enforcement layer allocated to a rule.</summary>
public enum CSharpGateRuleLayer
{
    /// <summary>Compiler/analyzer proof.</summary>
    Compiler,
    /// <summary>Architecture-test proof outside the analyzer.</summary>
    ArchitectureTest,
    /// <summary>Executable test proof outside the analyzer.</summary>
    ExecutableTest,
    /// <summary>Human review outside the analyzer.</summary>
    HumanReview,
}
