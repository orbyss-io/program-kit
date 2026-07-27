using Orbyss.ProgramKit.Artifacts.Diagnostics;

namespace Orbyss.ProgramKit.Modularity.Diagnostics;

/// <summary>Reports deterministic middleware-contract misuse.</summary>
public sealed class ModularityPipelineException : InvalidOperationException
{
    /// <summary>Initializes an exception from one stable diagnostic.</summary>
    /// <param name="diagnostic">The middleware-contract diagnostic.</param>
    public ModularityPipelineException(ProgramKitDiagnostic diagnostic)
        : base(diagnostic?.Message)
    {
        ArgumentNullException.ThrowIfNull(diagnostic);
        Diagnostic = diagnostic;
    }

    /// <summary>Gets the stable middleware-contract diagnostic.</summary>
    public ProgramKitDiagnostic Diagnostic { get; }
}
