using Orbyss.ProgramKit.DotNet.Generation.Console.Projection;
using Orbyss.ProgramKit.Workbench.Operations.Generation;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Rendering;

internal interface IDotNetConsoleOutputRenderer
{
    ImmutableArray<GeneratedOutput> Render(
        DotNetConsoleHostProjection projection);
}
