using Orbyss.ProgramKit.CSharpBuildGates.Contracts.Verification;

namespace Orbyss.ProgramKit.Workbench.Operations.CSharpBuildGates;

/// <summary>A failure owned by one exact C# build-gate evidence layer.</summary>
public sealed class CSharpBuildGateOperationException : Exception
{
    /// <summary>Initializes a typed operation failure.</summary>
    public CSharpBuildGateOperationException(
        CSharpGateEvidenceLayer layer,
        string message)
        : base(message)
    {
        Layer = layer;
    }

    /// <summary>Gets the exact failure layer.</summary>
    public CSharpGateEvidenceLayer Layer { get; }
}
