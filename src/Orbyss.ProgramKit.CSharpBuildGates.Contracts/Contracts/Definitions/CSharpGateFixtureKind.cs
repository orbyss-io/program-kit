namespace Orbyss.ProgramKit.CSharpBuildGates.Contracts.Definitions;

/// <summary>Finite fixture kinds selected by gate proof.</summary>
public enum CSharpGateFixtureKind
{
    /// <summary>Positive fixture.</summary>
    Positive,
    /// <summary>Negative fixture.</summary>
    Negative,
    /// <summary>Generated-source fixture.</summary>
    GeneratedSource,
    /// <summary>Suppression fixture.</summary>
    Suppression,
    /// <summary>Receipt fixture.</summary>
    Receipt,
    /// <summary>Tamper fixture.</summary>
    Tamper,
    /// <summary>Packaging fixture.</summary>
    Packaging,
    /// <summary>Isolated-consumer fixture.</summary>
    IsolatedConsumer,
    /// <summary>Repeatability fixture.</summary>
    Repeatability,
    /// <summary>Cancellation fixture.</summary>
    Cancellation,
    /// <summary>Performance fixture.</summary>
    Performance,
}
