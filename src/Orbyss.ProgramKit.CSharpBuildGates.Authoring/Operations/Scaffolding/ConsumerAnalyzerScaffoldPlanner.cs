using System.Collections.Immutable;
using System.Globalization;
using System.Text;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Scaffolding;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Selections;
using Orbyss.ProgramKit.CSharpBuildGates.Authoring.Contracts.Validation;

namespace Orbyss.ProgramKit.CSharpBuildGates.Authoring.Operations.Scaffolding;

/// <summary>Plans stable scaffold bytes without writing to a file system.</summary>
public static class ConsumerAnalyzerScaffoldPlanner
{
    /// <summary>Creates one validated, stable-ordered scaffold plan.</summary>
    public static ConsumerAnalyzerScaffoldPlan Plan(ConsumerAnalyzerScaffoldRequest request)
    {
        var errors = ConsumerAnalyzerScaffoldRequestValidator.Validate(request);
        if (!errors.IsEmpty)
        {
            throw new ArgumentException(
                string.Join(Environment.NewLine, errors),
                nameof(request));
        }

        var analyzerClass = string.Concat(
            request.RecipeBinding.DiagnosticId,
            "Analyzer");
        var replacements = new Dictionary<string, string>(StringComparer.Ordinal)
        {
            ["{{ANALYZER_CLASS}}"] = analyzerClass,
            ["{{DIAGNOSTIC_ID}}"] = request.RecipeBinding.DiagnosticId,
            ["{{DIAGNOSTIC_MESSAGE}}"] = EscapeCSharpString(
                request.RecipeBinding.DiagnosticMessage),
            ["{{DIAGNOSTIC_TITLE}}"] = EscapeCSharpString(
                request.RecipeBinding.DiagnosticTitle),
            ["{{FORBIDDEN_SUFFIX}}"] = EscapeCSharpString(
                request.RecipeBinding.Parameters["forbiddenSuffix"]),
            ["{{PROJECT_NAME}}"] = request.ProjectName,
            ["{{RECEIPT_GENERATOR_CLASS}}"] = string.Concat(
                request.ProjectName.Replace(".", string.Empty, StringComparison.Ordinal),
                "ParticipationReceiptGenerator"),
            ["{{ROOT_NAMESPACE}}"] = request.RootNamespace,
        };

        var files = ImmutableArray.CreateBuilder<ConsumerAnalyzerScaffoldFile>();
        files.Add(Source(
            $"Rules/{analyzerClass}.cs",
            RenderTemplate("consumer-analyzer.cs.template", replacements)));
        files.Add(Source(
            $"Generation/{request.ProjectName}ParticipationReceiptGenerator.cs",
            RenderTemplate("participation-receipt-generator.cs.template", replacements)));
        files.Add(Text(
            $"{request.ProjectName}.csproj",
            RenderTemplate("consumer-analyzer.csproj.template", replacements)));
        files.Add(Source(
            $"Tests/{analyzerClass}Tests.cs",
            RenderTemplate("consumer-analyzer-tests.cs.template", replacements)));
        files.Add(Text(
            $"Tests/{request.ProjectName}.Tests.csproj",
            RenderTemplate("consumer-analyzer-tests.csproj.template", replacements)));
        files.Add(Text(
            "gate/ownership-manifest.json",
            RenderOwnershipManifest(request)));
        files.Add(Text(
            "gate/public-analyzer-selections.json",
            RenderPublicSelections(request.PublicAnalyzerSelections)));

        var orderedFiles = files
            .OrderBy(file => file.RelativePath, StringComparer.Ordinal)
            .ToImmutableArray();
        ValidateOutputPaths(orderedFiles);
        return new ConsumerAnalyzerScaffoldPlan(orderedFiles);
    }

    private static ConsumerAnalyzerScaffoldFile Source(string path, string source)
    {
        return Text(path, source);
    }

    private static ConsumerAnalyzerScaffoldFile Text(string path, string text)
    {
        var normalized = string.Concat(
            text.Replace("\r\n", "\n", StringComparison.Ordinal).TrimEnd(),
            "\n");
        return new ConsumerAnalyzerScaffoldFile(
            path,
            Encoding.UTF8.GetBytes(normalized));
    }

    private static string RenderTemplate(
        string templateName,
        IReadOnlyDictionary<string, string> replacements)
    {
        var resourceName = string.Concat(
            "Orbyss.ProgramKit.CSharpBuildGates.Authoring.Templates.",
            templateName);
        using var stream = typeof(ConsumerAnalyzerScaffoldPlanner)
            .Assembly
            .GetManifestResourceStream(resourceName)
            ?? throw new InvalidOperationException(
                $"Missing scaffold template {templateName}.");
        using var reader = new StreamReader(
            stream,
            Encoding.UTF8,
            detectEncodingFromByteOrderMarks: true);
        var rendered = reader.ReadToEnd();
        foreach (var replacement in replacements.OrderBy(
                     replacement => replacement.Key,
                     StringComparer.Ordinal))
        {
            rendered = rendered.Replace(
                replacement.Key,
                replacement.Value,
                StringComparison.Ordinal);
        }

        if (rendered.Contains("{{", StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                $"Template {templateName} contains an unresolved token.");
        }

        return rendered;
    }

    private static string RenderOwnershipManifest(
        ConsumerAnalyzerScaffoldRequest request)
    {
        var binding = request.RecipeBinding;
        var builder = new StringBuilder();
        builder.AppendLine("{");
        AppendProperty(builder, "projectName", request.ProjectName, comma: true, 2);
        AppendProperty(builder, "semanticOwnerId", binding.ConsumerSemanticOwnerId, true, 2);
        AppendProperty(builder, "recipeIdentity", binding.RecipeIdentity, true, 2);
        AppendProperty(builder, "recipeVersion", binding.RecipeVersion, true, 2);
        AppendProperty(builder, "ruleId", binding.RuleId, true, 2);
        AppendProperty(builder, "ruleRevision", binding.RuleRevision, true, 2);
        AppendProperty(builder, "diagnosticId", binding.DiagnosticId, true, 2);
        AppendProperty(builder, "diagnosticRevision", binding.DiagnosticRevision, true, 2);
        builder.AppendLine("  \"parameters\": {");
        var parameters = binding.Parameters.ToArray();
        for (var index = 0; index < parameters.Length; index++)
        {
            AppendProperty(
                builder,
                parameters[index].Key,
                parameters[index].Value,
                index < parameters.Length - 1,
                4);
        }

        builder.AppendLine("  },");
        AppendArray(builder, "applicabilityProfiles", binding.ApplicabilityProfiles, true);
        AppendArray(builder, "fixtureIds", binding.FixtureIds, true);
        AppendArray(builder, "compatibilityClaims", binding.CompatibilityClaims, true);
        AppendProperty(builder, "suppressionPolicy", binding.SuppressionPolicy, false, 2);
        builder.Append('}');
        return builder.ToString();
    }

    private static string RenderPublicSelections(
        ImmutableArray<CSharpPublicAnalyzerSelectionProjection> selections)
    {
        var builder = new StringBuilder();
        builder.AppendLine("{");
        builder.AppendLine("  \"selections\": [");
        var ordered = selections
            .OrderBy(selection => selection.ComponentIdentity, StringComparer.Ordinal)
            .ToArray();
        for (var index = 0; index < ordered.Length; index++)
        {
            var selection = ordered[index];
            builder.AppendLine("    {");
            AppendProperty(builder, "componentIdentity", selection.ComponentIdentity, true, 6);
            AppendProperty(builder, "semanticOwnerId", selection.SemanticOwnerId, true, 6);
            AppendProperty(builder, "packageIdentity", selection.PackageIdentity, true, 6);
            AppendProperty(builder, "packageVersion", selection.PackageVersion, true, 6);
            AppendProperty(builder, "packageSha256", selection.PackageSha256, true, 6);
            AppendProperty(builder, "assemblyPath", selection.AssemblyPath, true, 6);
            AppendProperty(builder, "assemblySha256", selection.AssemblySha256, true, 6);
            AppendProperty(builder, "contractIdentity", selection.ContractIdentity, true, 6);
            AppendProperty(builder, "contractVersion", selection.ContractVersion, true, 6);
            AppendArray(
                builder,
                "diagnosticIds",
                selection.DiagnosticIds,
                comma: false,
                indentation: 6);
            builder.Append("    }");
            builder.AppendLine(index < ordered.Length - 1 ? "," : string.Empty);
        }

        builder.AppendLine("  ]");
        builder.Append('}');
        return builder.ToString();
    }

    private static void AppendArray(
        StringBuilder builder,
        string name,
        IEnumerable<string> values,
        bool comma,
        int indentation = 2)
    {
        var prefix = new string(' ', indentation);
        builder.Append(prefix)
            .Append('"')
            .Append(EscapeJson(name))
            .AppendLine("\": [");
        var ordered = values.Order(StringComparer.Ordinal).ToArray();
        for (var index = 0; index < ordered.Length; index++)
        {
            builder.Append(prefix)
                .Append("  \"")
                .Append(EscapeJson(ordered[index]))
                .Append('"')
                .AppendLine(index < ordered.Length - 1 ? "," : string.Empty);
        }

        builder.Append(prefix).Append(']');
        builder.AppendLine(comma ? "," : string.Empty);
    }

    private static void AppendProperty(
        StringBuilder builder,
        string name,
        string value,
        bool comma,
        int indentation)
    {
        builder.Append(' ', indentation)
            .Append('"')
            .Append(EscapeJson(name))
            .Append("\": \"")
            .Append(EscapeJson(value))
            .Append('"')
            .AppendLine(comma ? "," : string.Empty);
    }

    private static string EscapeJson(string value)
    {
        var builder = new StringBuilder(value.Length);
        foreach (var character in value)
        {
            _ = character switch
            {
                '"' => builder.Append("\\\""),
                '\\' => builder.Append("\\\\"),
                '\b' => builder.Append("\\b"),
                '\f' => builder.Append("\\f"),
                '\n' => builder.Append("\\n"),
                '\r' => builder.Append("\\r"),
                '\t' => builder.Append("\\t"),
                < ' ' => builder.Append("\\u").Append(
                    ((int)character).ToString("x4", CultureInfo.InvariantCulture)),
                _ => builder.Append(character),
            };
        }

        return builder.ToString();
    }

    private static string EscapeCSharpString(string value)
    {
        return value
            .Replace("\\", "\\\\", StringComparison.Ordinal)
            .Replace("\"", "\\\"", StringComparison.Ordinal)
            .Replace("\r", "\\r", StringComparison.Ordinal)
            .Replace("\n", "\\n", StringComparison.Ordinal);
    }

    private static void ValidateOutputPaths(
        ImmutableArray<ConsumerAnalyzerScaffoldFile> files)
    {
        var paths = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var file in files)
        {
            var normalized = file.RelativePath.Replace('\\', '/');
            if (Path.IsPathRooted(file.RelativePath) ||
                normalized.Split('/').Any(segment =>
                    segment.Length == 0 ||
                    string.Equals(segment, ".", StringComparison.Ordinal) ||
                    string.Equals(segment, "..", StringComparison.Ordinal)))
            {
                throw new InvalidOperationException(
                    $"Scaffold path {file.RelativePath} is not a finite relative path.");
            }

            if (!paths.Add(normalized))
            {
                throw new InvalidOperationException(
                    $"Scaffold path {file.RelativePath} collides with another output.");
            }
        }
    }
}
