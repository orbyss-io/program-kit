namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>Finite suppression mechanisms that keep the analyzer executing.</summary>
public enum CSharpGateSuppressionMechanism
{
    /// <summary>A source-local pragma.</summary>
    SourcePragma,
    /// <summary>A source-local SuppressMessage attribute.</summary>
    SourceAttribute,
}
