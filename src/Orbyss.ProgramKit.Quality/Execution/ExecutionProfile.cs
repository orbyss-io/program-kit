using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Quality.Execution;

/// <summary>Selects one concrete, reproducible execution environment.</summary>
public sealed record ExecutionProfile(
    string RunnerClass,
    string Platform,
    ImmutableArray<string> EnvironmentAssumptions,
    ImmutableArray<ArtifactReference> DependencyClosure,
    TestExecutionAccessPolicy Access,
    TimeSpan Timeout,
    TestRetryPolicy Retry);
