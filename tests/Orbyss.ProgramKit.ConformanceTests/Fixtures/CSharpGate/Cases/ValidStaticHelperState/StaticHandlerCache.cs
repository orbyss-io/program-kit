namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ValidStaticHelperState;

internal static class StaticHandlerCache
{
    private static readonly string DefaultValue = "default";

    internal static string Resolve() => DefaultValue;
}
