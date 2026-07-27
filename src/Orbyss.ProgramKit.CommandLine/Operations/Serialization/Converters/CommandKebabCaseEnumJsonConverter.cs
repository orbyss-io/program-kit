using System.Globalization;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization.Converters;

internal sealed class CommandKebabCaseEnumJsonConverter<TEnum> :
    JsonConverter<TEnum>
    where TEnum : struct, Enum
{
    private static readonly Dictionary<TEnum, string> NamesByValue =
        Enum.GetValues<TEnum>().ToDictionary(
            static value => value,
            static value => ToKebabCase(value.ToString()));

    private static readonly Dictionary<string, TEnum> ValuesByName =
        NamesByValue.ToDictionary(
            static pair => pair.Value,
            static pair => pair.Key,
            StringComparer.Ordinal);

    public override TEnum Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        if (reader.TokenType != JsonTokenType.String)
        {
            throw new JsonException(
                string.Create(
                    CultureInfo.InvariantCulture,
                    $"{typeof(TEnum).Name} must be a JSON string."));
        }

        var name = reader.GetString();
        return name is not null && ValuesByName.TryGetValue(name, out var value)
            ? value
            : throw new JsonException(
                string.Create(
                    CultureInfo.InvariantCulture,
                    $"'{name}' is not a declared {typeof(TEnum).Name} value."));
    }

    public override void Write(
        Utf8JsonWriter writer,
        TEnum value,
        JsonSerializerOptions options)
    {
        if (!NamesByValue.TryGetValue(value, out var name))
        {
            throw new JsonException(
                string.Create(
                    CultureInfo.InvariantCulture,
                    $"'{value}' is not a declared {typeof(TEnum).Name} value."));
        }

        writer.WriteStringValue(name);
    }

    private static string ToKebabCase(string value)
    {
        var builder = new StringBuilder(value.Length + 4);
        for (var index = 0; index < value.Length; index++)
        {
            var character = value[index];
            if (char.IsUpper(character) &&
                index > 0 &&
                (char.IsLower(value[index - 1]) ||
                 (index + 1 < value.Length &&
                  char.IsLower(value[index + 1]))))
            {
                builder.Append('-');
            }

            builder.Append(char.ToLowerInvariant(character));
        }

        return builder.ToString();
    }
}
