namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>The finite ownership class of a selected analyzer component.</summary>
public enum CSharpAnalyzerComponentKind
{
    /// <summary>Compiler and SDK diagnostics selected as a standard baseline.</summary>
    CompilerBaseline,
    /// <summary>A Program Kit analyzer owned by an exact public contract.</summary>
    ProgramKitPublicContract,
    /// <summary>An analyzer whose policy and diagnostics are consumer-owned.</summary>
    ConsumerOwned,
}
