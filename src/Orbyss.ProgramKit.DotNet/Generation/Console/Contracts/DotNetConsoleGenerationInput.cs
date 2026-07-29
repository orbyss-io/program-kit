using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.DotNet.Generation.Console.Compilation;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Contracts;

/// <summary>Exact ephemeral inputs required to generate and compile one Console host.</summary>
public sealed record DotNetConsoleGenerationInput(
    DotNetConsoleBindingDocument Binding,
    string ConsumerReferenceAssemblyPath,
    ImmutableArray<DotNetConsoleCompilationReference> CompilationReferences,
    string? ConsumerProjectReferencePath = null);
