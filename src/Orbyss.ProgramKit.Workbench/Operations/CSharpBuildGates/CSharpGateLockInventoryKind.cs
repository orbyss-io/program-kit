namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

/// <summary>Finite selection-lock inventory destinations for explicit assets.</summary>
public enum CSharpGateLockInventoryKind
{
    /// <summary>Project input.</summary>
    Project,
    /// <summary>Physical consumer-authored source.</summary>
    PhysicalSource,
    /// <summary>Generated source.</summary>
    GeneratedSource,
    /// <summary>Reference or analyzer assembly.</summary>
    Reference,
    /// <summary>Analyzer additional file.</summary>
    AdditionalFile,
    /// <summary>Analyzer configuration file.</summary>
    AnalyzerConfiguration,
}
