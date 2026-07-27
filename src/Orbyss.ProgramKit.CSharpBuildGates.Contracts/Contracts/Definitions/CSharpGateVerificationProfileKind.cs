namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>Finite verification profiles.</summary>
public enum CSharpGateVerificationProfileKind
{
    /// <summary>Bootstrap.</summary>
    Bootstrap,
    /// <summary>Focused verification.</summary>
    Focused,
    /// <summary>Work-unit verification.</summary>
    WorkUnit,
    /// <summary>Generated-output verification.</summary>
    GeneratedOutput,
    /// <summary>Tamper verification.</summary>
    Tamper,
    /// <summary>Performance verification.</summary>
    Performance,
    /// <summary>Final closure verification.</summary>
    FinalClosure,
}
