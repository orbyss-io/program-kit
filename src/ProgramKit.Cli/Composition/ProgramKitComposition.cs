using Orbyss.ProgramKit.Kernel.Operations;
using Orbyss.ProgramKit.Providers.DotNet;

namespace Orbyss.ProgramKit.Cli.Composition;

public static class ProgramKitComposition
{
    public static ProgramKitKernel CreateKernel() => new(new[] { new DotNetFactoryProvider() });
}
