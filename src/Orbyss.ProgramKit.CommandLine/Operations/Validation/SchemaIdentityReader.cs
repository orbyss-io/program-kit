using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Contracts.Diagnostics;

namespace Orbyss.ProgramKit.CommandLine.Operations.Validation;

internal static class SchemaIdentityReader
{
    internal static string Read(ReadOnlySpan<byte> utf8Json)
    {
        var reader = new Utf8JsonReader(
            utf8Json,
            new JsonReaderOptions
            {
                AllowTrailingCommas = false,
                CommentHandling = JsonCommentHandling.Disallow,
                MaxDepth = 128,
            });
        if (!reader.Read() || reader.TokenType != JsonTokenType.StartObject)
        {
            throw new CommandInvocationException(
                "A JSON object with a declared '$schema' URI is required.",
                "/$schema");
        }

        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            if (reader.TokenType != JsonTokenType.PropertyName)
            {
                throw new CommandInvocationException(
                    "A JSON property name was expected.",
                    "/");
            }

            var property = reader.GetString();
            if (!reader.Read())
            {
                break;
            }

            if (string.Equals(property, "$schema", StringComparison.Ordinal))
            {
                if (reader.TokenType != JsonTokenType.String)
                {
                    throw new CommandInvocationException(
                        "The '$schema' declaration must be a URI string.",
                        "/$schema");
                }

                return reader.GetString()!;
            }

            reader.Skip();
        }

        throw new CommandInvocationException(
            "The artifact must declare one exact '$schema' URI.",
            "/$schema");
    }
}
