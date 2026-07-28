using Orbyss.ProgramKit.DotNet.Locks;
using Orbyss.ProgramKit.DotNet.Shells;
using Orbyss.ProgramKit.OpenConsole.Contracts;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Contracts;

/// <summary>Generates one complete deterministic Spectre Console host.</summary>
public interface IDotNetConsoleHostGenerator
{
    /// <summary>Validates, projects, renders, and candidate-compiles one Console host.</summary>
    ImmutableArray<GeneratedOutput> Generate(
        DotNetHostDefinition host,
        DotNetHostLock hostLock,
        OpenConsoleDocument document,
        DotNetConsoleGenerationInput input,
        CancellationToken cancellationToken);
}
