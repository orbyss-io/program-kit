namespace Orbyss.ProgramKit.DotNet.Generation.Console.Compilation;

/// <summary>Deterministic isolated candidate-compilation outcome.</summary>
public sealed record DotNetConsoleCompilationResult(
    bool IsValid,
    ImmutableArray<byte> AssemblyBytes,
    ImmutableArray<ProgramKitDiagnostic> Diagnostics);
