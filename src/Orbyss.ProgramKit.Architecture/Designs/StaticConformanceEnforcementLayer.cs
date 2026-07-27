namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>The narrowest reliable enforcement layer for a static invariant.</summary>
public enum StaticConformanceEnforcementLayer
{
    /// <summary>C# language or type-system enforcement.</summary>
    LanguageTypeSystem,
    /// <summary>Project or package graph enforcement.</summary>
    ProjectPackage,
    /// <summary>Roslyn compiler/analyzer enforcement.</summary>
    RoslynCompiler,
    /// <summary>MSBuild enforcement.</summary>
    MsBuild,
    /// <summary>Architecture-test enforcement.</summary>
    ArchitectureTest,
    /// <summary>Executable-test enforcement.</summary>
    ExecutableTest,
    /// <summary>Human review because static enforcement is unsuitable.</summary>
    HumanReview,
}
