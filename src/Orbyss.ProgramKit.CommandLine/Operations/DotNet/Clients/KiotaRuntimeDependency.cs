namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Clients;

/// <summary>One exact runtime package required by the generated C# client.</summary>
public sealed record KiotaRuntimeDependency(
    string Package,
    string Version,
    string Kind);
