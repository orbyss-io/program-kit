namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Verification;

/// <summary>The failing assurance layer for typed gate evidence.</summary>
public enum CSharpGateEvidenceLayer
{
    /// <summary>Definition.</summary>
    Definition,
    /// <summary>Mechanics.</summary>
    Mechanics,
    /// <summary>Analyzer build.</summary>
    AnalyzerBuild,
    /// <summary>Attachment.</summary>
    Attachment,
    /// <summary>Inventory.</summary>
    Inventory,
    /// <summary>Source policy.</summary>
    SourcePolicy,
    /// <summary>Suppression.</summary>
    Suppression,
    /// <summary>Configuration or tamper.</summary>
    ConfigurationTamper,
    /// <summary>Evidence.</summary>
    Evidence,
    /// <summary>Performance.</summary>
    Performance,
    /// <summary>Package or runtime closure.</summary>
    PackageRuntime,
    /// <summary>Toolchain.</summary>
    Toolchain,
    /// <summary>Program Kit private-gate regression.</summary>
    InternalRegression,
}
