using System.Collections.Immutable;
using System.Text;
using System.Text.Json;

namespace Orbyss.ProgramKit.CommandLine.Operations.DotNet.Materialization;

/// <summary>Streaming parser for the documented MSBuild get-property/item JSON.</summary>
public static class MsBuildReferenceQueryParser
{
    /// <summary>Parses one exact query result without a mutable JSON DOM.</summary>
    public static MsBuildReferenceQueryResult Parse(string value)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(value);
        var trimmed = value.Trim();
        if (!trimmed.StartsWith('{') || !trimmed.EndsWith('}'))
        {
            throw Failure(
                "MSBuild reference evaluation emitted non-JSON output.");
        }

        var reader = new Utf8JsonReader(
            Encoding.UTF8.GetBytes(trimmed),
            new JsonReaderOptions
            {
                AllowTrailingCommas = false,
                CommentHandling = JsonCommentHandling.Disallow,
                MaxDepth = 32,
            });
        string? targetAssembly = null;
        string? targetReference = null;
        ImmutableArray<string>? references = null;
        while (reader.Read())
        {
            if (reader.TokenType != JsonTokenType.PropertyName)
            {
                continue;
            }

            var name = reader.GetString();
            if (string.Equals(
                    name,
                    "TargetPath",
                    StringComparison.Ordinal))
            {
                if (targetAssembly is not null ||
                    !reader.Read() ||
                    reader.TokenType != JsonTokenType.String)
                {
                    throw Failure(
                        "MSBuild returned an invalid or duplicate TargetPath.");
                }

                targetAssembly = reader.GetString();
            }
            else if (string.Equals(
                    name,
                    "TargetRefPath",
                    StringComparison.Ordinal))
            {
                if (targetReference is not null ||
                    !reader.Read() ||
                    reader.TokenType != JsonTokenType.String)
                {
                    throw Failure(
                        "MSBuild returned an invalid or duplicate TargetRefPath.");
                }

                targetReference = reader.GetString();
            }
            else if (string.Equals(
                         name,
                         "ReferencePathWithRefAssemblies",
                         StringComparison.Ordinal))
            {
                if (references is not null || !reader.Read())
                {
                    throw Failure(
                        "MSBuild returned duplicate reference items.");
                }

                references = ParseReferenceArray(ref reader);
            }
        }

        if (string.IsNullOrWhiteSpace(targetAssembly) ||
            string.IsNullOrWhiteSpace(targetReference) ||
            references is null ||
            references.Value.IsDefaultOrEmpty)
        {
            throw Failure(
                "MSBuild did not return one TargetPath, one TargetRefPath, and a non-empty ReferencePathWithRefAssemblies collection.");
        }

        return new MsBuildReferenceQueryResult(
            targetAssembly,
            targetReference,
            references.Value);
    }

    private static ImmutableArray<string> ParseReferenceArray(
        ref Utf8JsonReader reader)
    {
        if (reader.TokenType != JsonTokenType.StartArray)
        {
            throw Failure(
                "ReferencePathWithRefAssemblies must be a JSON array.");
        }

        var references = ImmutableArray.CreateBuilder<string>();
        while (reader.Read() && reader.TokenType != JsonTokenType.EndArray)
        {
            if (reader.TokenType != JsonTokenType.StartObject)
            {
                throw Failure(
                    "Every evaluated reference item must be a JSON object.");
            }

            references.Add(ParseReferenceItem(ref reader));
        }

        return references.ToImmutable();
    }

    private static string ParseReferenceItem(ref Utf8JsonReader reader)
    {
        string? identity = null;
        string? fullPath = null;
        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            if (reader.TokenType != JsonTokenType.PropertyName)
            {
                throw Failure(
                    "An evaluated reference item contains malformed JSON.");
            }

            var name = reader.GetString();
            if (!reader.Read())
            {
                throw Failure(
                    "An evaluated reference item ended unexpectedly.");
            }

            if (string.Equals(name, "Identity", StringComparison.Ordinal))
            {
                if (identity is not null ||
                    reader.TokenType != JsonTokenType.String)
                {
                    throw Failure(
                        "An evaluated reference item has an invalid Identity.");
                }

                identity = reader.GetString();
            }
            else if (string.Equals(name, "FullPath", StringComparison.Ordinal))
            {
                if (fullPath is not null ||
                    reader.TokenType != JsonTokenType.String)
                {
                    throw Failure(
                        "An evaluated reference item has an invalid FullPath.");
                }

                fullPath = reader.GetString();
            }
            else if (reader.TokenType is
                     JsonTokenType.StartArray or JsonTokenType.StartObject)
            {
                reader.Skip();
            }
        }

        var result = string.IsNullOrWhiteSpace(fullPath)
            ? identity
            : fullPath;
        return string.IsNullOrWhiteSpace(result)
            ? throw Failure(
                "An evaluated reference item has no exact path.")
            : result;
    }

    private static ConsoleInputMaterializationException Failure(
        string message) =>
        new(
            ConsoleInputMaterializationDiagnosticIds.ReferenceQueryFailed,
            message,
            "/referenceQuery");
}
