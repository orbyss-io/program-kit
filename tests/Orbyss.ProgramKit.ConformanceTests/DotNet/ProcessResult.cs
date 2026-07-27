namespace Orbyss.ProgramKit.ConformanceTests.DotNet;

internal sealed record ProcessResult(
    int ExitCode,
    string Output);
