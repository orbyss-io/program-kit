using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Materialization;

/// <summary>
/// Verifies implementation ownership in the exact selected Console integration
/// assembly without loading consumer code.
/// </summary>
public interface IDotNetConsoleIntegrationAssemblyInspector
{
    /// <summary>Inspects the complete selected integration assembly seam.</summary>
    ProgramKitValidationResult Inspect(
        DotNetConsoleBindingDocument binding,
        string referenceAssemblyPath);
}
