using Orbyss.ProgramKit.DotNet.Generation.Console.Contracts;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Binding;

/// <summary>Inspects exact consumer metadata without loading the assembly.</summary>
public interface IDotNetConsoleMetadataInspector
{
    /// <summary>Verifies the binding against the exact reference-assembly bytes.</summary>
    DotNetConsoleMetadataInspectionResult Inspect(
        DotNetConsoleBindingDocument binding,
        string referenceAssemblyPath);
}
