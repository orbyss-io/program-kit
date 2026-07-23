using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.References;
using Orbyss.ProgramKit.Quality.Execution;

namespace Orbyss.ProgramKit.Quality.Specifications;

/// <summary>Defines execution constraints without selecting a concrete runner environment.</summary>
public sealed record TestExecutionRequirements(
    ImmutableArray<string> RunnerClasses,
    ImmutableArray<string> Platforms,
    ImmutableArray<string> EnvironmentAssumptions,
    ImmutableArray<ArtifactReference> RequiredDependencyClosure,
    TestExecutionAccessPolicy Access,
    TimeSpan Timeout,
    TestRetryPolicy Retry);
