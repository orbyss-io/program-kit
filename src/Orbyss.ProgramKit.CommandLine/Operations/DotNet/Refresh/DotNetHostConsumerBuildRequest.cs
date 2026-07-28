using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Refresh;

/// <summary>Exact reusable C# build-gate inputs used only with explicit authority.</summary>
public sealed record DotNetHostConsumerBuildRequest(
    string WorkingDirectory,
    string ProjectPath,
    string EvidenceOutputPath,
    ImmutableArray<string> ParticipationReceiptPaths,
    ImmutableArray<string> ExceptionUseReceiptPaths,
    ImmutableArray<string> PackagePaths,
    int MaximumCapturedOutputBytes,
    int PerformanceBudgetMilliseconds);
