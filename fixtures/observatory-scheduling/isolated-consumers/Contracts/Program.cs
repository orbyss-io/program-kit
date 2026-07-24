using Orbyss.ProgramKit.Tasks.Core.Definitions;

namespace ProgramKit.IsolatedConsumers.Contracts;

internal static class Program
{
    private static int Main() =>
        typeof(TaskDefinition).Assembly.GetName().Name ==
        "Orbyss.ProgramKit.Tasks.Core"
            ? 0
            : 1;
}
