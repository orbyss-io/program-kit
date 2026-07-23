namespace Orbyss.ProgramKit.Serialization.Json.Diagnostics;

internal static class JsonExceptionBoundary
{
    internal static bool IsNonFatal(Exception exception) =>
        exception is not OutOfMemoryException and
        not StackOverflowException and
        not AccessViolationException;
}
