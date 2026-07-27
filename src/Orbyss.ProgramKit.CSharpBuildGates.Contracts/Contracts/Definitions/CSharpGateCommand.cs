namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>Commands on which analyzers may be activated.</summary>
public enum CSharpGateCommand
{
    /// <summary>Build.</summary>
    Build,
    /// <summary>Test.</summary>
    Test,
    /// <summary>Pack.</summary>
    Pack,
    /// <summary>Publish.</summary>
    Publish,
    /// <summary>Verification of a generated project.</summary>
    GeneratedProjectVerify,
}
