namespace Orbyss.ProgramKit.DotNet.Generation.Console.Projection;

internal sealed record DotNetConsoleCommandTrieNode(
    string Token,
    DotNetConsoleCommandProjection? Command,
    ImmutableArray<DotNetConsoleCommandTrieNode> Children);
