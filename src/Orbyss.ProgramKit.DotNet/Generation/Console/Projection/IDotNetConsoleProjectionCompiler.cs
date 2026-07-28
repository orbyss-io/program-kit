using Orbyss.ProgramKit.DotNet.Generation.Console.Binding;
using Orbyss.ProgramKit.OpenConsole.Contracts;

namespace Orbyss.ProgramKit.DotNet.Generation.Console.Projection;

internal interface IDotNetConsoleProjectionCompiler
{
    DotNetConsoleProjectionResult Compile(
        OpenConsoleDocument document,
        DotNetConsoleBindingDocument binding);
}
