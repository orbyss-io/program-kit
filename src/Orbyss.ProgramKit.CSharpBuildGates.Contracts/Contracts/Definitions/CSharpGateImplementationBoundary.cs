namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>Implementation boundaries used by the finite activation matrix.</summary>
public enum CSharpGateImplementationBoundary
{
    /// <summary>Gate establishment.</summary>
    GateEstablishment,
    /// <summary>Implementation preflight.</summary>
    Preflight,
    /// <summary>Product work unit.</summary>
    WorkUnit,
    /// <summary>Generated output verification.</summary>
    GeneratedOutput,
    /// <summary>Final closure.</summary>
    FinalClosure,
}
