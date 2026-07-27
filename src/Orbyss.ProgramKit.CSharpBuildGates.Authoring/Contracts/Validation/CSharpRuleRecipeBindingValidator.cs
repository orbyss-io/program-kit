using System.Collections.Immutable;
using System.Text.RegularExpressions;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Recipes;

namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Validation;

/// <summary>
/// Validates that a recipe adoption supplies all consumer-owned semantics.
/// </summary>
public static partial class CSharpRuleRecipeBindingValidator
{
    private static readonly string[] ReservedDiagnosticPrefixes =
        ["PKCC", "PKCG", "PKCS"];

    /// <summary>Returns stable validation errors for an exact recipe binding.</summary>
    public static ImmutableArray<string> Validate(
        CSharpRuleRecipe recipe,
        CSharpRuleRecipeBinding binding)
    {
        ArgumentNullException.ThrowIfNull(recipe);
        ArgumentNullException.ThrowIfNull(binding);

        var errors = ImmutableArray.CreateBuilder<string>();
        RequireExact(
            errors,
            binding.RecipeIdentity,
            recipe.Identity,
            "recipe identity");
        RequireExact(
            errors,
            binding.RecipeVersion,
            recipe.Version,
            "recipe version");
        RequireValue(errors, binding.ConsumerSemanticOwnerId, "consumer semantic owner");
        RequireValue(errors, binding.RuleId, "consumer rule identity");
        RequireValue(errors, binding.RuleRevision, "consumer rule revision");
        RequireValue(errors, binding.DiagnosticRevision, "consumer diagnostic revision");
        RequireValue(errors, binding.DiagnosticTitle, "consumer diagnostic title");
        RequireValue(errors, binding.DiagnosticMessage, "consumer diagnostic message");
        RequireValue(errors, binding.SuppressionPolicy, "consumer suppression policy");

        if (!DiagnosticIdPattern().IsMatch(binding.DiagnosticId))
        {
            errors.Add(
                "The consumer diagnostic identity must contain uppercase ASCII letters followed by four digits.");
        }

        if (ReservedDiagnosticPrefixes.Any(prefix =>
                binding.DiagnosticId.StartsWith(prefix, StringComparison.Ordinal)))
        {
            errors.Add(
                $"The diagnostic identity {binding.DiagnosticId} uses a Program Kit-reserved prefix.");
        }

        RequireNonEmptyDistinct(errors, binding.ApplicabilityProfiles, "applicability profiles");
        RequireNonEmptyDistinct(errors, binding.FixtureIds, "fixtures");
        RequireNonEmptyDistinct(errors, binding.CompatibilityClaims, "compatibility claims");

        var expectedParameters = recipe.RequiredParameters
            .Order(StringComparer.Ordinal)
            .ToArray();
        var actualParameters = binding.Parameters.Keys
            .Order(StringComparer.Ordinal)
            .ToArray();
        if (!expectedParameters.SequenceEqual(actualParameters, StringComparer.Ordinal))
        {
            errors.Add(
                $"Recipe parameters must be exactly [{string.Join(", ", expectedParameters)}].");
        }

        foreach (var parameter in binding.Parameters)
        {
            RequireValue(errors, parameter.Value, $"recipe parameter {parameter.Key}");
        }

        return errors.ToImmutable();
    }

    private static void RequireExact(
        ImmutableArray<string>.Builder errors,
        string actual,
        string expected,
        string label)
    {
        if (!string.Equals(actual, expected, StringComparison.Ordinal))
        {
            errors.Add($"The {label} must be exactly {expected}.");
        }
    }

    private static void RequireValue(
        ImmutableArray<string>.Builder errors,
        string value,
        string label)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            errors.Add($"The {label} is required.");
        }
    }

    private static void RequireNonEmptyDistinct(
        ImmutableArray<string>.Builder errors,
        ImmutableArray<string> values,
        string label)
    {
        if (values.IsDefaultOrEmpty)
        {
            errors.Add($"One or more {label} are required.");
            return;
        }

        if (values.Any(string.IsNullOrWhiteSpace) ||
            values.Distinct(StringComparer.Ordinal).Count() != values.Length)
        {
            errors.Add($"The {label} must be non-empty and distinct.");
        }
    }

    [GeneratedRegex("^[A-Z]{2,12}[0-9]{4}$", RegexOptions.CultureInvariant)]
    private static partial Regex DiagnosticIdPattern();
}
