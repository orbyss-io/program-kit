using System.Collections.Immutable;

namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Recipes;

/// <summary>A complete consumer-owned adoption of one inert rule recipe.</summary>
public sealed record CSharpRuleRecipeBinding(
    string RecipeIdentity,
    string RecipeVersion,
    string ConsumerSemanticOwnerId,
    string RuleId,
    string RuleRevision,
    string DiagnosticId,
    string DiagnosticRevision,
    string DiagnosticTitle,
    string DiagnosticMessage,
    ImmutableSortedDictionary<string, string> Parameters,
    ImmutableArray<string> ApplicabilityProfiles,
    ImmutableArray<string> FixtureIds,
    ImmutableArray<string> CompatibilityClaims,
    string SuppressionPolicy);
