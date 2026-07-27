using System.Collections.Immutable;
namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Recipes;

/// <summary>The finite catalog of optional, inert Program Kit rule recipes.</summary>
public static class CSharpRuleRecipeCatalog
{
    /// <summary>Gets the suffix-rule recipe.</summary>
    public static CSharpRuleRecipe ForbidTypeNameSuffix { get; } = new(
        "pkid:recipe:program-kit:csharp-forbid-type-name-suffix",
        "1.0.0",
        "Forbid a consumer-selected type-name suffix",
        "Reports a consumer-owned diagnostic when a declared type ends with the exact consumer-selected suffix.",
        ["forbiddenSuffix"],
        "consumer-analyzer.cs.template");

    /// <summary>Gets all recipes in stable identity order.</summary>
    public static ImmutableArray<CSharpRuleRecipe> All { get; } =
        [ForbidTypeNameSuffix];

    /// <summary>Resolves one exact recipe identity and version.</summary>
    public static CSharpRuleRecipe Resolve(string identity, string version)
    {
        return All.SingleOrDefault(recipe =>
                string.Equals(recipe.Identity, identity, StringComparison.Ordinal) &&
                string.Equals(recipe.Version, version, StringComparison.Ordinal))
            ?? throw new ArgumentException(
                $"Unknown C# rule recipe {identity}@{version}.",
                nameof(identity));
    }
}
