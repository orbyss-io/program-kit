namespace Orbyss.ProgramKit.CommandLine.Operations.Diagnostics;

/// <summary>Finite read-only Program Kit diagnostic knowledge.</summary>
public interface IDiagnosticExplanationCatalog
{
    /// <summary>Resolves one registered ID or classifies it as external.</summary>
    DiagnosticExplanation Resolve(string diagnosticId);

    /// <summary>Renders one explanation in the exact requested format.</summary>
    byte[] Render(DiagnosticExplanation explanation, string format);
}
