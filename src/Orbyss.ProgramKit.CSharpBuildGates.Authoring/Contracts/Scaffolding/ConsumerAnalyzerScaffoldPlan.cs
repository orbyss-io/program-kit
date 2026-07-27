using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;

/// <summary>A stable-ordered, fully validated analyzer scaffold plan.</summary>
public sealed record ConsumerAnalyzerScaffoldPlan(
    ImmutableArray<ConsumerAnalyzerScaffoldFile> Files);
