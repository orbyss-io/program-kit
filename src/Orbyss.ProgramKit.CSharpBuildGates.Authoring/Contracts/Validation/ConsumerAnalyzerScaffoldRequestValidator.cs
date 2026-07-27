using System.Collections.Immutable;
using System.Text.RegularExpressions;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Recipes;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;

namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Validation;

/// <summary>Validates finite consumer analyzer scaffold inputs.</summary>
public static partial class ConsumerAnalyzerScaffoldRequestValidator
{
    /// <summary>Returns stable errors without reading files or loading analyzers.</summary>
    public static ImmutableArray<string> Validate(ConsumerAnalyzerScaffoldRequest request)
    {
        ArgumentNullException.ThrowIfNull(request);

        var errors = ImmutableArray.CreateBuilder<string>();
        if (!IdentifierPattern().IsMatch(request.ProjectName))
        {
            errors.Add("The project name must be a dotted C# identifier.");
        }

        if (!NamespacePattern().IsMatch(request.RootNamespace))
        {
            errors.Add("The root namespace must be a dotted C# namespace.");
        }

        CSharpRuleRecipe? recipe = null;
        try
        {
            recipe = CSharpRuleRecipeCatalog.Resolve(
                request.RecipeBinding.RecipeIdentity,
                request.RecipeBinding.RecipeVersion);
        }
        catch (ArgumentException exception)
        {
            errors.Add(exception.Message);
        }

        if (recipe is not null)
        {
            errors.AddRange(CSharpRuleRecipeBindingValidator.Validate(
                recipe,
                request.RecipeBinding));
        }

        var publicDiagnostics = new HashSet<string>(StringComparer.Ordinal);
        foreach (var selection in request.PublicAnalyzerSelections)
        {
            RequireValue(errors, selection.ComponentIdentity, "public analyzer component identity");
            RequireValue(errors, selection.SemanticOwnerId, "public analyzer semantic owner");
            RequireValue(errors, selection.PackageIdentity, "public analyzer package identity");
            RequireValue(errors, selection.PackageVersion, "public analyzer package version");
            RequireSha256(errors, selection.PackageSha256, "public analyzer package");
            RequireValue(errors, selection.AssemblyPath, "public analyzer assembly path");
            RequireSha256(errors, selection.AssemblySha256, "public analyzer assembly");
            RequireValue(errors, selection.ContractIdentity, "public contract identity");
            RequireValue(errors, selection.ContractVersion, "public contract version");

            if (selection.DiagnosticIds.IsDefaultOrEmpty)
            {
                errors.Add("A public analyzer selection requires one or more diagnostics.");
            }

            foreach (var diagnosticId in selection.DiagnosticIds)
            {
                if (!diagnosticId.StartsWith("PKCC", StringComparison.Ordinal))
                {
                    errors.Add(
                        $"Public analyzer diagnostic {diagnosticId} is not a PKCC identity.");
                }

                if (!publicDiagnostics.Add(diagnosticId))
                {
                    errors.Add(
                        $"Public analyzer diagnostic {diagnosticId} is selected more than once.");
                }

                if (string.Equals(
                        diagnosticId,
                        request.RecipeBinding.DiagnosticId,
                        StringComparison.Ordinal))
                {
                    errors.Add(
                        $"Consumer diagnostic {diagnosticId} collides with a public analyzer diagnostic.");
                }
            }
        }

        return errors.ToImmutable();
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

    private static void RequireSha256(
        ImmutableArray<string>.Builder errors,
        string value,
        string label)
    {
        if (!Sha256Pattern().IsMatch(value))
        {
            errors.Add($"The {label} digest must be lowercase SHA-256.");
        }
    }

    [GeneratedRegex(
        "^[A-Za-z_][A-Za-z0-9_]*(\\.[A-Za-z_][A-Za-z0-9_]*)*$",
        RegexOptions.CultureInvariant)]
    private static partial Regex IdentifierPattern();

    [GeneratedRegex(
        "^[A-Za-z_][A-Za-z0-9_]*(\\.[A-Za-z_][A-Za-z0-9_]*)*$",
        RegexOptions.CultureInvariant)]
    private static partial Regex NamespacePattern();

    [GeneratedRegex("^[0-9a-f]{64}$", RegexOptions.CultureInvariant)]
    private static partial Regex Sha256Pattern();
}
