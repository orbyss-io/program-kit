using Orbyss.ProgramKit.DotNet.Shells;

namespace ProgramKit.IsolatedConsumers.DotNet;

internal static class Program
{
    private static int Main() =>
        typeof(DotNetShellDocument).Assembly.GetName().Name ==
        "Orbyss.ProgramKit.DotNet"
            ? 0
            : 1;
}
