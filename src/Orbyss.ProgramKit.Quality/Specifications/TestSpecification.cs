using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.Primitives;

namespace Orbyss.ProgramKit.Quality.Specifications;

/// <summary>
/// Describes durable test meaning independently from the environment used to execute it.
/// </summary>
public sealed record TestSpecification(
    ProgramKitIdentifier OwnerId,
    string Purpose,
    ImmutableArray<string> RequirementIds,
    ImmutableArray<TestCategory> Categories,
    ImmutableArray<TestScenario> Scenarios,
    TestExecutionRequirements ExecutionRequirements,
    TestExpectedResult ExpectedResult,
    TestEvidenceShape EvidenceShape);
