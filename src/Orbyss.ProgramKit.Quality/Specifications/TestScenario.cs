using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts.References;

namespace Orbyss.ProgramKit.Quality.Specifications;

/// <summary>Defines one durable scenario and its exact machine-contract inputs and fixtures.</summary>
public sealed record TestScenario(
    string ScenarioId,
    TestScenarioKind Kind,
    string Purpose,
    ImmutableArray<ArtifactReference> Inputs,
    ImmutableArray<ArtifactReference> Fixtures,
    string ExpectedResult);
