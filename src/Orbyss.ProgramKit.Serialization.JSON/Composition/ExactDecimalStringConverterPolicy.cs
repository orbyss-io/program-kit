using System.Text.Json.Serialization;
using Orbyss.ProgramKit.Serialization.Json.Converters;
using Orbyss.ProgramKit.Serialization.Json.Diagnostics;

namespace Orbyss.ProgramKit.Serialization.Json.Composition;

internal static class ExactDecimalStringConverterPolicy
{
    internal static JsonConverter Apply(
        Type targetType,
        JsonConverter converter)
    {
        ArgumentNullException.ThrowIfNull(targetType);
        ArgumentNullException.ThrowIfNull(converter);
        if (targetType != typeof(decimal))
        {
            return converter;
        }

        if (converter is not JsonConverter<decimal> decimalConverter)
        {
            throw ProgramKitJsonException.Create(
                ProgramKitJsonDiagnosticIds.InvalidContribution,
                "A converter selected for decimal must implement JsonConverter<decimal>.",
                "/targetTypeFamilies");
        }

        return converter is ExactDecimalStringJsonConverter
            ? converter
            : new ExactDecimalStringJsonConverter(decimalConverter);
    }
}
