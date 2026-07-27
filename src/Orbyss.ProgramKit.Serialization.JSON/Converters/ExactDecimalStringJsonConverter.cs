using System.Text.Json;
using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;
using Orbyss.ProgramKit.Serialization.Json.Serialization;

namespace Orbyss.ProgramKit.Serialization.Json.Converters;

internal sealed class ExactDecimalStringJsonConverter : JsonConverter<decimal>
{
    private const int MaximumDecimalWireBytes = 128;
    private readonly JsonConverter<decimal> converter;

    internal ExactDecimalStringJsonConverter(JsonConverter<decimal> converter)
    {
        ArgumentNullException.ThrowIfNull(converter);
        this.converter = converter;
    }

    public override decimal Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        if (reader.TokenType != JsonTokenType.String)
        {
            throw ExactStringFailure();
        }

        return converter.Read(ref reader, typeToConvert, options);
    }

    public override void Write(
        Utf8JsonWriter writer,
        decimal value,
        JsonSerializerOptions options)
    {
        var buffer = new BoundedJsonBufferWriter(MaximumDecimalWireBytes);
        try
        {
            using (var validatingWriter = new Utf8JsonWriter(
                       buffer,
                       new JsonWriterOptions
                       {
                           Encoder = options.Encoder,
                           Indented = false,
                           MaxDepth = 1,
                           SkipValidation = false,
                       }))
            {
                converter.Write(validatingWriter, value, options);
                validatingWriter.Flush();
            }
        }
        catch (JsonByteLimitExceededException exception)
        {
            throw ExactStringFailure(exception);
        }

        var reader = new Utf8JsonReader(
            buffer.WrittenSpan,
            new JsonReaderOptions
            {
                AllowTrailingCommas = false,
                CommentHandling = JsonCommentHandling.Disallow,
                MaxDepth = 1,
            });
        if (!reader.Read() ||
            reader.TokenType != JsonTokenType.String)
        {
            throw ExactStringFailure();
        }

        var text = reader.GetString()
            ?? throw ExactStringFailure();
        if (reader.Read())
        {
            throw ExactStringFailure();
        }

        writer.WriteStringValue(text);
    }

    private static ProgramKitJsonException ExactStringFailure(
        Exception? innerException = null) =>
        ProgramKitJsonException.Create(
            ProgramKitJsonDiagnosticIds.InvalidContribution,
            "Decimal converters must read and write one exact schema-constrained JSON string; numeric decimal tokens are forbidden because canonical binary64 conversion can lose precision.",
            "/targetTypeFamilies",
            innerException);
}
