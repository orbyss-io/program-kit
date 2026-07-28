namespace Orbyss.ProgramKit.DotNet.Generation.Console.Compilation;

/// <summary>One deterministic generated source candidate.</summary>
public sealed record DotNetConsoleSourceFile(
    string RelativePath,
    string Content);
