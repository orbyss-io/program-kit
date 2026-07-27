namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>The finite source/input classes understood by gate mechanics.</summary>
public enum CSharpGateInputKind
{
    /// <summary>Physical consumer-authored C#.</summary>
    PhysicalSource,
    /// <summary>Consumer-owned generated C#.</summary>
    ConsumerGeneratedSource,
    /// <summary>Compiler, SDK, or third-party generated C#.</summary>
    ExternalGeneratedSource,
    /// <summary>An analyzer AdditionalFile.</summary>
    AdditionalFile,
    /// <summary>An analyzer configuration file.</summary>
    AnalyzerConfiguration,
}
