using System.Collections.Immutable;
using System.Text;
using System.Text.Json;
using Orbyss.ProgramKit.Artifacts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.Diagnostics;

/// <summary>
/// Explicit finite projection of registered Program Kit diagnostics. Unknown
/// identifiers never inherit Program Kit ownership from their spelling.
/// </summary>
public sealed class DiagnosticExplanationCatalog :
    IDiagnosticExplanationCatalog
{
    private static readonly UTF8Encoding Utf8 = new(false);
    private readonly Dictionary<string, DiagnosticExplanation> explanations;

    /// <summary>Builds one duplicate-rejecting explanation catalog.</summary>
    public DiagnosticExplanationCatalog(
        IEnumerable<ProgramKitDiagnosticDefinition> definitions)
    {
        ArgumentNullException.ThrowIfNull(definitions);
        explanations = new Dictionary<string, DiagnosticExplanation>(
            StringComparer.Ordinal);
        foreach (var definition in definitions)
        {
            var explanation = Create(definition);
            if (!explanations.TryAdd(explanation.Id, explanation))
            {
                throw new InvalidDataException(
                    string.Concat(
                        "Diagnostic '",
                        explanation.Id,
                        "' is registered more than once."));
            }
        }
    }

    /// <inheritdoc />
    public DiagnosticExplanation Resolve(string diagnosticId)
    {
        if (string.IsNullOrWhiteSpace(diagnosticId))
        {
            throw new ArgumentException(
                "A diagnostic identifier is required.",
                nameof(diagnosticId));
        }

        return explanations.TryGetValue(diagnosticId, out var explanation)
            ? explanation
            : External(diagnosticId);
    }

    /// <inheritdoc />
    public byte[] Render(
        DiagnosticExplanation explanation,
        string format)
    {
        ArgumentNullException.ThrowIfNull(explanation);
        return format switch
        {
            "json" => RenderJson(explanation),
            "text" => RenderText(explanation),
            _ => throw new ArgumentException(
                "Diagnostic format must be one of: json, text.",
                nameof(format)),
        };
    }

    private static DiagnosticExplanation Create(
        ProgramKitDiagnosticDefinition definition)
    {
        var owner = Owner(definition.Id);
        return new DiagnosticExplanation(
            definition.Id,
            "program-kit-owned",
            owner,
            definition.Title,
            string.Concat(owner, " registered validation contract"),
            "Retain the exact failing command, arguments with secrets redacted, artifact identity, JSON path, and emitted diagnostic envelope.",
            "The supplied artifact, finite option, package evidence, generated output, or repository state does not satisfy the named Program Kit contract.",
            "Describe the failing command, inspect the explicit artifact, read its exact registered schema, then change only consumer-owned input under the active capability and human authority.",
            "Stop when required evidence is absent, the artifact is not consumer-owned, the command or schema is unavailable, or remediation would exceed the active capability's authority.",
            ["artifacts.inspect", "commands.describe", "schemas.read"],
            []);
    }

    private static DiagnosticExplanation External(string id)
    {
        var owner = id.StartsWith("CS", StringComparison.Ordinal)
            ? "C# compiler"
            : id.StartsWith("NU", StringComparison.Ordinal)
                ? "NuGet"
                : id.StartsWith("NETSDK", StringComparison.Ordinal)
                    ? ".NET SDK"
                    : "unregistered external owner";
        return new DiagnosticExplanation(
            id,
            "unregistered-external",
            owner,
            "This identifier is not registered in the installed Program Kit diagnostic catalog.",
            "external or unknown contract",
            "Retain the original tool, command, complete diagnostic text, version, and affected file or package identity.",
            "Program Kit has no registered cause classification for this identifier.",
            "Consult the owning tool's exact documentation or supply the missing external evidence; Program Kit does not invent a repair.",
            "Stop before changing Program Kit-owned or generated files, guessing a meaning, or applying a repair outside the active capability's authority.",
            [],
            []);
    }

    private static string Owner(string id)
    {
        var prefixLength = id.TakeWhile(static character =>
            character is >= 'A' and <= 'Z').Count();
        return prefixLength == 0
            ? "Program Kit"
            : string.Concat("Program Kit ", id[..prefixLength]);
    }

    private static byte[] RenderText(DiagnosticExplanation value)
    {
        StringBuilder output = new();
        output.Append(value.Id)
            .Append(" [")
            .Append(value.Classification)
            .AppendLine("]")
            .Append("Owner: ")
            .AppendLine(value.Owner)
            .Append("Meaning: ")
            .AppendLine(value.Meaning)
            .Append("Affected contract: ")
            .AppendLine(value.AffectedContract)
            .Append("Expected evidence: ")
            .AppendLine(value.ExpectedEvidence)
            .Append("Likely causes: ")
            .AppendLine(value.LikelyCauses)
            .Append("Bounded remediation: ")
            .AppendLine(value.BoundedRemediation)
            .Append("Stop condition: ")
            .AppendLine(value.StopCondition);
        return Utf8.GetBytes(output.ToString());
    }

    private static byte[] RenderJson(DiagnosticExplanation value)
    {
        using MemoryStream output = new();
        using (Utf8JsonWriter writer = new(output))
        {
            writer.WriteStartObject();
            writer.WriteString(
                "affectedContract",
                value.AffectedContract);
            writer.WriteString(
                "boundedRemediation",
                value.BoundedRemediation);
            writer.WriteString("classification", value.Classification);
            writer.WriteString("expectedEvidence", value.ExpectedEvidence);
            writer.WriteString("id", value.Id);
            writer.WriteString("likelyCauses", value.LikelyCauses);
            writer.WriteString("meaning", value.Meaning);
            writer.WriteString("owner", value.Owner);
            writer.WriteStartArray("relatedCommands");
            foreach (var command in value.RelatedCommands)
            {
                writer.WriteStringValue(command);
            }

            writer.WriteEndArray();
            writer.WriteStartArray("relatedSchemas");
            foreach (var schema in value.RelatedSchemas)
            {
                writer.WriteStringValue(schema);
            }

            writer.WriteEndArray();
            writer.WriteString("stopCondition", value.StopCondition);
            writer.WriteEndObject();
        }

        return output.ToArray();
    }
}
