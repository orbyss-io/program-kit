using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Recipes;

/// <summary>An inert versioned authoring recipe with no consumer authority.</summary>
public sealed record CSharpRuleRecipe(
    string Identity,
    string Version,
    string Title,
    string SemanticSummary,
    ImmutableArray<string> RequiredParameters,
    string AnalyzerTemplateName);
