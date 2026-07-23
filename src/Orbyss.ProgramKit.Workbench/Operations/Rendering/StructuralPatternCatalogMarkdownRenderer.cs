using System.Text;
using Orbyss.ProgramKit.Architecture.Patterns;

namespace Orbyss.ProgramKit.Workbench.Operations.Rendering;

/// <summary>
/// Renders validated structural guidance without turning it into implementation
/// authority.
/// </summary>
public sealed class StructuralPatternCatalogMarkdownRenderer :
    IWorkbenchRenderer<StructuralPatternCatalog>
{
    private readonly IProgramKitSemanticValidator<StructuralPatternCatalog> validator;

    /// <summary>Initializes the renderer with the catalog semantic validator.</summary>
    public StructuralPatternCatalogMarkdownRenderer(
        IProgramKitSemanticValidator<StructuralPatternCatalog> validator)
    {
        this.validator = validator ??
            throw new ArgumentNullException(nameof(validator));
    }

    /// <inheritdoc />
    public string RenderMarkdown(StructuralPatternCatalog value)
    {
        ArgumentNullException.ThrowIfNull(value);
        var validation = validator.Validate(value);
        if (!validation.IsValid)
        {
            var diagnosticIds = validation.Diagnostics
                .Select(static diagnostic => diagnostic.Id)
                .Distinct(StringComparer.Ordinal)
                .Order(StringComparer.Ordinal);
            throw new ArgumentException(
                string.Concat(
                    "The structural-pattern catalog is invalid: ",
                    string.Join(", ", diagnosticIds),
                    "."),
                nameof(value));
        }

        var builder = new StringBuilder();
        AppendLine(builder, string.Concat("# ", Escape(value.Purpose)));
        AppendLine(builder, string.Empty);
        AppendLine(builder, string.Concat("- Identity: `", value.Identity.Value, "`"));
        AppendLine(builder, string.Concat("- Version: `", value.Version.Value, "`"));
        foreach (var pattern in value.Patterns)
        {
            AppendLine(builder, string.Empty);
            AppendLine(builder, string.Concat("## ", Escape(pattern.Name)));
            AppendLine(builder, string.Empty);
            AppendLine(builder, string.Concat("Identity: `", pattern.Identity.Value, "`"));
            AppendLine(builder, string.Empty);
            AppendLine(builder, Escape(pattern.Problem));
            AppendList(builder, "Applicability", pattern.ApplicabilityCriteria);
            AppendList(builder, "Trade-offs", pattern.TradeOffs);
            AppendLine(builder, string.Empty);
            AppendLine(builder, "### Examples");
            foreach (var example in pattern.Examples)
            {
                AppendLine(builder, string.Empty);
                AppendLine(builder, string.Concat("#### ", Escape(example.Name)));
                AppendLine(builder, string.Empty);
                AppendLine(builder, string.Concat("- Context: ", Escape(example.Context)));
                AppendLine(
                    builder,
                    string.Concat("- Application: ", Escape(example.Application)));
                AppendLine(
                    builder,
                    string.Concat("- Consequence: ", Escape(example.Consequence)));
            }

            AppendList(builder, "Mechanical checks", pattern.MechanicalChecks);
            AppendList(builder, "Human checks", pattern.HumanChecks);
        }

        return builder.ToString();
    }

    private static void AppendList(
        StringBuilder builder,
        string heading,
        ImmutableArray<string> values)
    {
        AppendLine(builder, string.Empty);
        AppendLine(builder, string.Concat("### ", heading));
        AppendLine(builder, string.Empty);
        foreach (var value in values)
        {
            AppendLine(builder, string.Concat("- ", Escape(value)));
        }
    }

    private static void AppendLine(StringBuilder builder, string value)
    {
        builder.Append(value);
        builder.Append('\n');
    }

    private static string Escape(string value) =>
        value
            .Replace("\r\n", " ", StringComparison.Ordinal)
            .Replace('\r', ' ')
            .Replace('\n', ' ')
            .Replace("\\", "\\\\", StringComparison.Ordinal)
            .Replace("*", "\\*", StringComparison.Ordinal)
            .Replace("_", "\\_", StringComparison.Ordinal)
            .Replace("#", "\\#", StringComparison.Ordinal)
            .Replace("[", "\\[", StringComparison.Ordinal)
            .Replace("]", "\\]", StringComparison.Ordinal)
            .Replace("<", "\\<", StringComparison.Ordinal)
            .Replace(">", "\\>", StringComparison.Ordinal);
}
