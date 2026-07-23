using System.Text.Json;
using System.Text.Json.Serialization;

namespace Orbyss.ProgramKit.UnitTests.Serialization.Json.Serialization;

internal sealed class FailureBoundaryTokenConverter :
    JsonConverter<BoundaryToken>
{
    public override BoundaryToken Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        var value = reader.GetString();
        throw string.Equals(value, "fatal", StringComparison.Ordinal)
            ? new SimulatedFatalJsonException(
                "Intentional process-fatal read probe.")
            : new FormatException("Intentional nonfatal read probe.");
    }

    public override void Write(
        Utf8JsonWriter writer,
        BoundaryToken value,
        JsonSerializerOptions options)
    {
        throw string.Equals(value.Value, "fatal", StringComparison.Ordinal)
            ? new SimulatedFatalJsonException(
                "Intentional process-fatal write probe.")
            : new OverflowException("Intentional nonfatal write probe.");
    }
}
