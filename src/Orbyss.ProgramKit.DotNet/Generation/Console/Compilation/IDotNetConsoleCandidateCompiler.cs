namespace Orbyss.ProgramKit.DotNet.Generation.Console.Compilation;

/// <summary>Compiles generated candidates against caller-supplied exact references.</summary>
public interface IDotNetConsoleCandidateCompiler
{
    /// <summary>Compiles without MSBuild, assembly loading, or ambient resolution.</summary>
    DotNetConsoleCompilationResult Compile(
        ImmutableArray<DotNetConsoleSourceFile> sources,
        ImmutableArray<DotNetConsoleCompilationReference> references,
        CancellationToken cancellationToken);
}
