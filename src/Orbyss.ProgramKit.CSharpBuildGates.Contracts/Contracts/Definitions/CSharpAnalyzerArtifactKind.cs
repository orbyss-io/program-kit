namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>How exact analyzer bytes are selected without ambient discovery.</summary>
public enum CSharpAnalyzerArtifactKind
{
    /// <summary>A repository-local project that is explicitly non-packable.</summary>
    LocalNonPackableProject,
    /// <summary>An exact analyzer-only package and assembly selection.</summary>
    AnalyzerPackage,
}
