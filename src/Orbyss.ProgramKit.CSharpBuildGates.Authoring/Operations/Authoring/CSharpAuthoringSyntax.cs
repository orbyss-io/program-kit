using System.Globalization;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Recipes;

namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Operations.Authoring;

/// <summary>
/// Deterministic Roslyn helpers that register no analyzer or source generator.
/// </summary>
public static class CSharpAuthoringSyntax
{
    /// <summary>Parses and normalizes valid C# source using the pinned language.</summary>
    public static string NormalizeSource(string source)
    {
        ArgumentNullException.ThrowIfNull(source);

        var tree = CSharpSyntaxTree.ParseText(
            source,
            CSharpParseOptions.Default.WithLanguageVersion(LanguageVersion.CSharp14));
        var syntaxErrors = tree.GetDiagnostics()
            .Where(diagnostic => diagnostic.Severity == DiagnosticSeverity.Error)
            .OrderBy(diagnostic => diagnostic.Location.SourceSpan.Start)
            .ToArray();
        if (syntaxErrors.Length > 0)
        {
            throw new ArgumentException(
                $"The source contains invalid C# syntax: {syntaxErrors[0].GetMessage(CultureInfo.InvariantCulture)}",
                nameof(source));
        }

        return string.Concat(
            tree.GetRoot()
                .NormalizeWhitespace(
                    indentation: "    ",
                    eol: "\n",
                    elasticTrivia: false)
                .ToFullString()
                .TrimEnd(),
            "\n");
    }

    /// <summary>Creates a descriptor from an explicit consumer-owned binding.</summary>
    public static DiagnosticDescriptor CreateDescriptor(
        CSharpRuleRecipeBinding binding,
        string category,
        DiagnosticSeverity defaultSeverity,
        bool enabledByDefault)
    {
        ArgumentNullException.ThrowIfNull(binding);
        ArgumentException.ThrowIfNullOrWhiteSpace(category);

        return new DiagnosticDescriptor(
            binding.DiagnosticId,
            binding.DiagnosticTitle,
            binding.DiagnosticMessage,
            category,
            defaultSeverity,
            enabledByDefault,
            description: null,
            helpLinkUri: null,
            customTags: []);
    }
}
