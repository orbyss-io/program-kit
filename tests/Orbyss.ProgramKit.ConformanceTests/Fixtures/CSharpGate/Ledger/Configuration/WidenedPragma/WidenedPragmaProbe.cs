namespace Orbyss.ProgramKit.LedgerProbe.Configuration.WidenedPragma;

internal static class WidenedPragmaProbe
{
    internal static void Execute()
    {
#pragma warning disable CS0168
        int unused;

#pragma warning restore CS0168
    }
}
