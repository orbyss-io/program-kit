namespace Orbyss.ProgramKit.CSharpGateProbe.Cases.ImmediateInvocationPropertyChain;

internal sealed class PropertyInvocationProbe
{
    internal string Run() =>
        new UriBuilder().Uri.ToString();
}
