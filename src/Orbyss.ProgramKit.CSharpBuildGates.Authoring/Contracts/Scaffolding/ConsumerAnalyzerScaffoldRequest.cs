using System.Collections.Immutable;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Recipes;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Selections;

namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;

/// <summary>
/// The consumer-approved inputs required to plan one consumer-owned analyzer
/// scaffold.
/// </summary>
public sealed record ConsumerAnalyzerScaffoldRequest(
    string ProjectName,
    string RootNamespace,
    CSharpRuleRecipeBinding RecipeBinding,
    ImmutableArray<CSharpPublicAnalyzerSelectionProjection> PublicAnalyzerSelections);
