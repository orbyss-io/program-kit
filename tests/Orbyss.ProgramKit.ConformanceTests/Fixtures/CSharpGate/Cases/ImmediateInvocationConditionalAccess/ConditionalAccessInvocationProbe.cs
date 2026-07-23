namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ImmediateInvocationConditionalAccess;

internal static class ConditionalAccessInvocationProbe
{
    internal static string? Execute() => new object()?.ToString();
}
