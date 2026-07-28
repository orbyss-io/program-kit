namespace Orbyss.ProgramKit.DotNet.Generation.Console.Compilation;

/// <summary>One exact metadata reference accepted by candidate compilation.</summary>
public sealed record DotNetConsoleCompilationReference(
    string Path,
    Sha256Digest Digest);
