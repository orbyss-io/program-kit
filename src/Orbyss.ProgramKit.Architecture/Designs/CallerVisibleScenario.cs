using System.Collections.Immutable;
using Orbyss.ProgramKit.Artifacts;

namespace Orbyss.ProgramKit.Architecture.Designs;

/// <summary>A caller-visible scenario used to inspect the architecture as behavior.</summary>
public sealed record CallerVisibleScenario(
    ProgramKitIdentifier Identity,
    string Actor,
    string Intent,
    ImmutableArray<string> Preconditions,
    ImmutableArray<string> Steps,
    ImmutableArray<string> Outcomes,
    ImmutableArray<string> FailureOutcomes);
