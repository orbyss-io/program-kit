namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>The only temporary non-execution conditions supported initially.</summary>
public enum CSharpGateTemporaryExceptionConditionKind
{
    /// <summary>An exact toolchain incompatibility.</summary>
    ExactToolchainIncompatibility,
    /// <summary>An exact target-framework incompatibility.</summary>
    ExactTargetFrameworkIncompatibility,
    /// <summary>Generated input is unavailable with separately proven producer state.</summary>
    UnavailableGeneratedInput,
    /// <summary>The exact gate-establishment boundary.</summary>
    GateEstablishmentBoundary,
}
