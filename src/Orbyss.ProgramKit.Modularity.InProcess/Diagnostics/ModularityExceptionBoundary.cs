namespace Orbyss.ProgramKit.Modularity.InProcess.Diagnostics;

internal static class ModularityExceptionBoundary
{
    internal static bool IsNonFatal(Exception exception) =>
        exception is not OutOfMemoryException and
        not StackOverflowException and
        not AccessViolationException;
}
