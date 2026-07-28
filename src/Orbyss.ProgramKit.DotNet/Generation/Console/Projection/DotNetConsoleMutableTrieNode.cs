namespace Orbyss.ProgramKit.DotNet.Generation.Console.Projection;

internal sealed class DotNetConsoleMutableTrieNode(string token)
{
    internal string Token { get; } = token;

    internal DotNetConsoleCommandProjection? Command { get; set; }

    internal Dictionary<string, DotNetConsoleMutableTrieNode> Children { get; } =
        new(StringComparer.Ordinal);
}
