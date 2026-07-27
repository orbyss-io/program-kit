namespace Orbyss.ProgramKit.ConformanceTests.Build;

internal sealed record LayeredBuildResult(
    int ExitCode,
    string Output,
    string ProjectDirectory);
