namespace Orbyss.ProgramKit.ConformanceTests.Build;

internal sealed record PublicAnalyzerBuildResult(
    int ExitCode,
    string Output,
    long ElapsedMilliseconds,
    string ProjectDirectory);
