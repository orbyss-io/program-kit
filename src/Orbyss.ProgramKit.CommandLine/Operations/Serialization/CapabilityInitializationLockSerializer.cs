using System.Text.Json;
using Orbyss.ProgramKit.CommandLine.Operations.Capabilities.Initialization;

namespace Orbyss.ProgramKit.CommandLine.Operations.Serialization;

/// <summary>Strict source-generated capability ownership lock serializer.</summary>
public sealed class CapabilityInitializationLockSerializer :
    ICapabilityInitializationLockSerializer
{
    /// <inheritdoc />
    public string ReadVersion(ReadOnlySpan<byte> content)
    {
        StrictJsonObjectValidator.Validate(content);
        Utf8JsonReader reader = new(content);
        if (!reader.Read() || reader.TokenType != JsonTokenType.StartObject)
        {
            throw new JsonException(
                "The capability ownership lock must be a JSON object.");
        }

        while (reader.Read() && reader.TokenType != JsonTokenType.EndObject)
        {
            if (reader.TokenType != JsonTokenType.PropertyName)
            {
                throw new JsonException(
                    "A capability ownership lock property was expected.");
            }

            var name = reader.GetString();
            if (!reader.Read())
            {
                throw new JsonException(
                    "A capability ownership lock value was expected.");
            }

            if (string.Equals(name, "lockVersion", StringComparison.Ordinal))
            {
                if (reader.TokenType != JsonTokenType.String)
                {
                    throw new JsonException(
                        "The capability lockVersion must be a string.");
                }

                return reader.GetString() ??
                    throw new JsonException(
                        "The capability lockVersion cannot be null.");
            }

            reader.Skip();
        }

        throw new JsonException(
            "The capability ownership lock requires lockVersion.");
    }

    /// <inheritdoc />
    public CapabilityInitializationLock Read(ReadOnlySpan<byte> content) =>
        ReadCurrent(content);

    /// <inheritdoc />
    public LegacyCapabilityInitializationLock ReadLegacy(
        ReadOnlySpan<byte> content)
    {
        StrictJsonObjectValidator.Validate(content);
        return JsonSerializer.Deserialize(
            content,
            CapabilityInitializationJsonContext.Default
                .LegacyCapabilityInitializationLock)
            ?? throw new JsonException(
            "The legacy capability ownership lock cannot be JSON null.");
    }

    /// <inheritdoc />
    public byte[] Write(CapabilityInitializationLock value) =>
        JsonSerializer.SerializeToUtf8Bytes(
            value,
            CapabilityInitializationJsonContext.Default
                .CapabilityInitializationLock);

    private static CapabilityInitializationLock ReadCurrent(
        ReadOnlySpan<byte> content)
    {
        StrictJsonObjectValidator.Validate(content);
        return JsonSerializer.Deserialize(
            content,
            CapabilityInitializationJsonContext.Default
                .CapabilityInitializationLock)
            ?? throw new JsonException(
                "The capability ownership lock cannot be JSON null.");
    }
}
